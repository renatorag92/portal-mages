import json
import logging
import re
from datetime import timedelta
from decimal import Decimal, InvalidOperation

import webcolors
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.core.exceptions import ValidationError
from django.core.files.storage import default_storage
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse_lazy
from django.utils.dateparse import parse_date
from django.utils import timezone
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from collections import Counter
from datetime import date, timedelta

from .forms import (
    ConsultoriaForm, FuncionarioForm, LoginCPFForm, MinhaContaForm,
    PrefeituraForm, gerar_senha_provisoria, preparar_senha,
)
from .models import (
    Acao, AcaoCatalogo, Consultoria, Eixo, Etapa, Funcionario,
    NotificacaoLida, Prefeitura, Status,
)

logger = logging.getLogger(__name__)

PT_EN = dict(zip(
    'azul vermelho verde amarelo laranja roxo rosa preto branco cinza marrom ciano dourado prata turquesa bege lilás violeta magenta índigo salmão coral vinho lima'.split(),
    'blue red green yellow orange purple pink black white gray brown cyan gold silver turquoise beige lavender violet magenta indigo salmon coral maroon lime'.split(),
))
MAX_STATUS_COLUMNS = 7
EN_PT = {ingles: portugues for portugues, ingles in PT_EN.items()}


# =========================================================
# UTILITÁRIOS GERAIS
# =========================================================

def _cor_para_edicao(status):
    if status.cor_nome:
        return status.cor_nome
    try:
        nome_cor = webcolors.hex_to_name(status.cor)
    except ValueError:
        return status.cor
    return EN_PT.get(nome_cor, nome_cor)


def _formatar_cnpj(cnpj):
    digitos = re.sub(r'\D', '', cnpj or '')
    if len(digitos) == 14:
        return f'{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}'
    return digitos


def _carregar_json(request):
    try:
        dados = json.loads(request.body or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return dados if isinstance(dados, dict) else None


def _erros_formulario(form):
    return {
        campo: [erro['message'] for erro in erros]
        for campo, erros in form.errors.get_json_data().items()
    }


def _erro(mensagem, status=400):
    return JsonResponse({'success': False, 'error': mensagem}, status=status)


def _por_pk(queryset, valor):
    # Evita erro de conversão quando o valor não é um número
    if not str(valor or '').isdigit():
        return None
    return queryset.filter(pk=valor).first()


def _converter_data(valor):
    try:
        return parse_date(valor or '')
    except ValueError:
        return None


def _datas_etapa_dentro_periodo(data_inicio, data_fim, inicio_acao, fim_acao):
    return data_inicio >= inicio_acao and data_fim <= fim_acao


def _iso(data):
    return data.isoformat() if hasattr(data, 'isoformat') else (data or '')


def _usuario_configuracoes(user):
    # Só consultor (ou superusuário) acessa cadastro e configuração
    return user.is_authenticated and (user.is_superuser or user.e_consultor)


def _prefeitura_ativa(request):
    """
    Prefeitura que o usuário está operando agora.
    - Usuário da prefeitura: sempre a sua.
    - Consultor: a que ele escolheu (guardada na sessão), entre todas da consultoria.
    """
    usuario = request.user
    if not usuario.is_authenticated:
        return None

    permitidas = usuario.prefeituras_permitidas()
    escolhida = _por_pk(permitidas, request.session.get('prefeitura_id'))
    if escolhida:
        return escolhida

    opcoes = list(permitidas[:2])
    if len(opcoes) == 1:
        request.session['prefeitura_id'] = opcoes[0].pk
        return opcoes[0]
    return None


# =========================================================
# CADASTRO DE PREFEITURA E CONSULTORIA (1:1)
# =========================================================

def _serializar_cadastro(registro, consultoria=False):
    dados = {
        'id': registro.pk,
        'cnpj': registro.cnpj,
        'cnpj_formatado': _formatar_cnpj(registro.cnpj),
        'nome_fantasia': registro.nome_fantasia,
        'nome_juridico': registro.nome_juridico,
        'endereco': registro.endereco,
    }
    if consultoria:
        prefeitura = Prefeitura.objects.filter(consultoria=registro).first()
        dados['prefeitura_id'] = prefeitura.pk if prefeitura else None
        dados['prefeitura_nome'] = prefeitura.nome_fantasia if prefeitura else ''
    return dados


@login_required
@user_passes_test(_usuario_configuracoes)
def gerenciar_prefeitura_view(request):
    registro = Prefeitura.objects.order_by('pk').first()
    return render(request, 'actions/cadastro-entidade.html', {
        'tipo_entidade': 'prefeitura',
        'titulo_entidade': 'Prefeitura',
        'registro': registro,
        'cnpj_formatado': _formatar_cnpj(registro.cnpj) if registro else '',
        'form': PrefeituraForm(instance=registro),
    })


@login_required
@user_passes_test(_usuario_configuracoes)
@require_POST
def salvar_prefeitura_view(request):
    dados = _carregar_json(request)
    if dados is None:
        return JsonResponse({'success': False, 'errors': {'__all__': ['Requisição inválida.']}}, status=400)

    registro = Prefeitura.objects.order_by('pk').first()
    registro_id = dados.get('id')
    if registro and str(registro.pk) != str(registro_id):
        return JsonResponse({
            'success': False,
            'errors': {'__all__': ['Já existe uma prefeitura cadastrada. Edite o registro atual.']},
        }, status=409)
    if registro is None and registro_id:
        return JsonResponse({'success': False, 'errors': {'__all__': ['Prefeitura não encontrada.']}}, status=404)

    form = PrefeituraForm(dados, instance=registro)
    if not form.is_valid():
        return JsonResponse({'success': False, 'errors': _erros_formulario(form)}, status=400)

    try:
        with transaction.atomic():
            if registro is None and Prefeitura.objects.exists():
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': ['Já existe uma prefeitura cadastrada.']},
                }, status=409)
            registro = registro or Prefeitura()
            for campo in ('cnpj', 'nome_fantasia', 'nome_juridico', 'endereco'):
                setattr(registro, campo, form.cleaned_data[campo])
            registro.save()
    except IntegrityError:
        return JsonResponse({
            'success': False,
            'errors': {'cnpj': ['CNPJ já cadastrado.']},
        }, status=409)

    return JsonResponse({'success': True, 'registro': _serializar_cadastro(registro)})


@login_required
@user_passes_test(_usuario_configuracoes)
def gerenciar_consultoria_view(request):
    registro = Consultoria.objects.order_by('pk').first()
    sem_prefeituras = not Prefeitura.objects.exists()
    return render(request, 'actions/cadastro-entidade.html', {
        'tipo_entidade': 'consultoria',
        'titulo_entidade': 'Consultoria',
        'registro': registro,
        'cnpj_formatado': _formatar_cnpj(registro.cnpj) if registro else '',
        'form': ConsultoriaForm(instance=registro) if not sem_prefeituras else None,
        'sem_prefeituras': sem_prefeituras,
    })


@login_required
@user_passes_test(_usuario_configuracoes)
@require_POST
def salvar_consultoria_view(request):
    dados = _carregar_json(request)
    if dados is None:
        return JsonResponse({'success': False, 'errors': {'__all__': ['Requisição inválida.']}}, status=400)

    registro_atual = Consultoria.objects.order_by('pk').first()
    registro_id = dados.get('id')
    if registro_atual and str(registro_atual.pk) != str(registro_id):
        return JsonResponse({
            'success': False,
            'errors': {'__all__': ['Já existe uma consultoria cadastrada. Edite o registro atual.']},
        }, status=409)
    if registro_atual is None and registro_id:
        return JsonResponse({'success': False, 'errors': {'__all__': ['Consultoria não encontrada.']}}, status=404)

    form = ConsultoriaForm(dados, instance=registro_atual)
    if not form.is_valid():
        return JsonResponse({'success': False, 'errors': _erros_formulario(form)}, status=400)

    try:
        # O formulário grava a consultoria e o vínculo 1:1 com a prefeitura
        registro = form.salvar()
    except IntegrityError:
        cnpj_duplicado = Consultoria.objects.filter(
            cnpj=form.cleaned_data['cnpj'],
        ).exclude(pk=registro_atual.pk if registro_atual else None).exists()
        if cnpj_duplicado:
            return JsonResponse({'success': False, 'errors': {'cnpj': ['CNPJ já cadastrado.']}}, status=409)
        return JsonResponse({
            'success': False,
            'errors': {'__all__': ['Não foi possível salvar a consultoria. Tente novamente.']},
        }, status=409)

    return JsonResponse({'success': True, 'registro': _serializar_cadastro(registro, consultoria=True)})


# =========================================================
# STATUS E EIXOS (configuração)
# =========================================================

class StatusForm(forms.ModelForm):
    cor = forms.CharField(max_length=45)

    class Meta:
        model = Status
        fields = ('nome', 'cor')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and not self.is_bound:
            self.initial['cor'] = _cor_para_edicao(self.instance)

    def clean_cor(self):
        cor_informada = self.cleaned_data['cor'].strip()
        self.cor_informada = cor_informada
        cor = cor_informada.lower()
        cor = PT_EN.get(cor, cor)
        try:
            cor = webcolors.name_to_hex(cor)
        except ValueError:
            try:
                cor = webcolors.normalize_hex(cor)
            except ValueError:
                raise ValidationError(
                    'Cor inválida. Use um nome (ex.: amarelo) ou hexadecimal (ex.: #ffff00).'
                )
        return cor

    def clean(self):
        cleaned_data = super().clean()
        if not self.instance.pk and Status.objects.count() >= MAX_STATUS_COLUMNS:
            self.add_error(
                None,
                f'O limite de {MAX_STATUS_COLUMNS} status foi atingido. Exclua um status para cadastrar outro.',
            )
        if 'nome' in cleaned_data:
            cleaned_data['nome'] = cleaned_data['nome'].strip()
        mensagens = {
            'nome': 'Já existe um status com esse nome.',
            'cor': 'Essa cor já está cadastrada em outro status.',
        }
        for campo, msg in mensagens.items():
            valor = cleaned_data.get(campo)
            if valor and Status.objects.filter(
                **{f'{campo}__iexact': valor}
            ).exclude(pk=self.instance.pk).exists():
                self.add_error(campo, msg)
        return cleaned_data

    def save(self, commit=True):
        status = super().save(commit=False)
        status.cor_nome = getattr(self, 'cor_informada', status.cor_nome)
        if commit:
            status.save()
            self.save_m2m()
        return status

class EixoForm(forms.ModelForm):
    pai = forms.ModelChoiceField(
        queryset=Eixo.objects.none(),
        required=False,
        label='Eixo pai',
        empty_label='Nenhum (eixo principal)',
    )

    class Meta:
        model = Eixo
        fields = ('nome', 'pai')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        qs = Eixo.objects.filter(pai__isnull=True)
        if self.instance.pk:
            qs = qs.exclude(pk=self.instance.pk)
        self.fields['pai'].queryset = qs

    def clean_nome(self):
        nome = (self.cleaned_data.get('nome') or '').strip()
        if not nome:
            raise ValidationError('Informe o nome do eixo.')
        if Eixo.objects.filter(nome__iexact=nome).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Já existe um eixo com esse nome.')
        return nome

@login_required
@user_passes_test(_usuario_configuracoes)
def gerenciar_eixo_view(request, eixo_id=None):
    eixo = get_object_or_404(Eixo, pk=eixo_id) if eixo_id else None

    if request.method == 'POST':
        form = EixoForm(request.POST, instance=eixo)
        if form.is_valid():
            form.save()
            if eixo:
                messages.success(request, 'Eixo atualizado com sucesso.', extra_tags='eixo-updated')
            else:
                messages.success(request, 'Eixo cadastrado com sucesso.', extra_tags='eixo-created')
            return redirect('gerenciar_eixo')
    else:
        form = EixoForm(instance=eixo)

    eixo_lista = Eixo.objects.annotate(total_vinculos=Count('acoes')).order_by('nome')
    return render(request, 'actions/gerenciar-eixo.html', {
        'form': form,
        'eixo_lista': eixo_lista,
        'eixo_edicao': eixo,
    })


@login_required
@user_passes_test(_usuario_configuracoes)
@require_POST
def excluir_eixo_view(request, eixo_id):
    eixo = get_object_or_404(Eixo, pk=eixo_id)

    try:
        eixo.delete()
        messages.success(request, 'Eixo excluído com sucesso.', extra_tags='eixo-deleted')
    except ProtectedError:
        messages.error(
            request,
            'Este eixo não pode ser excluído porque está vinculado a um ou mais itens do catálogo.',
            extra_tags='eixo-delete-blocked',
        )
    return redirect('gerenciar_eixo')

class AcaoCatalogoForm(forms.ModelForm):
    class Meta:
        model = AcaoCatalogo
        fields = ('nome', 'eixo', 'ativa')
        labels = {'ativa': 'Disponível para escolha'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ação só pode ficar em eixo "folha": subeixo, ou eixo sem subeixos
        self.fields['eixo'].queryset = (
            Eixo.objects.filter(subeixos__isnull=True).select_related('pai').order_by('nome'))
        self.fields['eixo'].label_from_instance = lambda e: (
            f'{e.pai.nome} › {e.nome}' if e.pai_id else e.nome)

    def clean_nome(self):
        nome = (self.cleaned_data.get('nome') or '').strip()
        if not nome:
            raise ValidationError('Informe o nome da ação.')
        if AcaoCatalogo.objects.filter(nome__iexact=nome).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Já existe uma ação com esse nome no catálogo.')
        return nome

@login_required
@user_passes_test(_usuario_configuracoes)
def gerenciar_funcionario_view(request, funcionario_id=None):
    funcionario = get_object_or_404(Funcionario, pk=funcionario_id) if funcionario_id else None

    if request.method == 'POST':
        form = FuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            registro = form.save(commit=False)
            senha = preparar_senha(registro)
            registro.save()
            if senha:
                messages.warning(
                    request,
                    f'Senha provisória de {registro.nome} (CPF {registro.username}): {senha}. '
                    'Informe agora; ela não será exibida novamente.',
                    extra_tags='funcionario-senha',
                )
            messages.success(
                request,
                'Funcionário atualizado com sucesso.' if funcionario else 'Funcionário cadastrado com sucesso.',
                extra_tags='funcionario-updated' if funcionario else 'funcionario-created',
            )
            return redirect('gerenciar_funcionario')
    else:
        form = FuncionarioForm(instance=funcionario)

    funcionario_lista = Funcionario.objects.select_related('prefeitura', 'consultoria').order_by('nome')
    return render(request, 'actions/gerenciar-funcionario.html', {
        'form': form,
        'funcionario_lista': funcionario_lista,
        'funcionario_edicao': funcionario,
    })

@login_required
@user_passes_test(_usuario_configuracoes)
@require_POST
def excluir_funcionario_view(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, pk=funcionario_id)

    if funcionario.pk == request.user.pk:
        messages.error(request, 'Você não pode excluir o seu próprio cadastro.',
                       extra_tags='funcionario-delete-blocked')
    else:
        try:
            funcionario.delete()
            messages.success(request, 'Funcionário excluído com sucesso.', extra_tags='funcionario-deleted')
        except ProtectedError:
            messages.error(
                request,
                'Este funcionário não pode ser excluído porque está vinculado a ações ou etapas.',
                extra_tags='funcionario-delete-blocked',
            )
    return redirect('gerenciar_funcionario')

@login_required
@user_passes_test(_usuario_configuracoes)
def gerenciar_catalogo_view(request, modelo_id=None):
    modelo = get_object_or_404(AcaoCatalogo, pk=modelo_id) if modelo_id else None

    if request.method == 'POST':
        form = AcaoCatalogoForm(request.POST, instance=modelo)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Ação do catálogo atualizada com sucesso.' if modelo else 'Ação do catálogo cadastrada com sucesso.',
                extra_tags='catalogo-updated' if modelo else 'catalogo-created',
            )
            return redirect('gerenciar_catalogo')
    else:
        form = AcaoCatalogoForm(instance=modelo)

    catalogo_lista = (
        AcaoCatalogo.objects.select_related('eixo', 'eixo__pai')
        .annotate(total_acoes=Count('instancias'))
        .order_by('eixo__nome', 'nome')
    )
    return render(request, 'actions/gerenciar-catalogo.html', {
        'form': form,
        'catalogo_lista': catalogo_lista,
        'catalogo_edicao': modelo,
    })


@login_required
@user_passes_test(_usuario_configuracoes)
@require_POST
def excluir_catalogo_view(request, modelo_id):
    modelo = get_object_or_404(AcaoCatalogo, pk=modelo_id)
    # As ações já criadas guardam o nome copiado, então continuam existindo (on_delete=SET_NULL)
    modelo.delete()
    messages.success(request, 'Ação do catálogo excluída com sucesso.', extra_tags='catalogo-deleted')
    return redirect('gerenciar_catalogo')

@login_required
@user_passes_test(_usuario_configuracoes)
def gerenciar_status_view(request, status_id=None):
    status = get_object_or_404(Status, pk=status_id) if status_id else None

    if request.method == 'POST':
        form = StatusForm(request.POST, instance=status)
        if form.is_valid():
            form.save()
            if status:
                messages.success(request, 'Status atualizado com sucesso.', extra_tags='status-updated')
            else:
                messages.success(request, 'Status cadastrado com sucesso.', extra_tags='status-created')
            return redirect('gerenciar_status')
    else:
        form = StatusForm(instance=status)

    status_lista = Status.objects.annotate(total_acoes=Count('acoes')).order_by('ordem', 'id')
    status_limite_atingido = status_lista.count() >= MAX_STATUS_COLUMNS
    return render(request, 'actions/gerenciar-status.html', {
        'form': form,
        'status_lista': status_lista,
        'status_edicao': status,
        'status_limite_atingido': status_limite_atingido,
        'max_status_columns': MAX_STATUS_COLUMNS,
    })


@login_required
@user_passes_test(_usuario_configuracoes)
@require_POST
def editar_status_kanban_view(request, status_id):
    status = get_object_or_404(Status, pk=status_id)
    form = StatusForm(request.POST, instance=status)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': {
                field: [str(error) for error in errors]
                for field, errors in form.errors.items()
            },
        }, status=400)
    status = form.save()
    request.session['kanban_toast'] = {
        'mensagem': f'Status "{status.nome}" atualizado com sucesso.',
        'tipo': 'status-updated',
    }
    return JsonResponse({
        'success': True,
        'status': {'id': status.id, 'nome': status.nome, 'cor': status.cor},
    })


@login_required
@user_passes_test(_usuario_configuracoes)
@require_POST
def excluir_status_view(request, status_id):
    status = get_object_or_404(Status, pk=status_id)

    try:
        status.delete()
        messages.success(request, 'Status excluído com sucesso.', extra_tags='status-deleted')
    except ProtectedError:
        # Ações usam on_delete=PROTECT: status com ações vinculadas não pode ser excluído
        messages.error(
            request,
            'Este status não pode ser excluído porque está vinculado a uma ou mais ações.',
            extra_tags='status-delete-blocked',
        )
    return redirect('gerenciar_status')

@login_required
@user_passes_test(_usuario_configuracoes)
@require_POST
def gerar_senha_funcionario_view(request, funcionario_id):
    funcionario = get_object_or_404(Funcionario, pk=funcionario_id)

    if not funcionario.tem_acesso:
        messages.error(request, 'Este funcionário não tem acesso ao sistema.',
                       extra_tags='funcionario-senha-erro')
        return redirect('gerenciar_funcionario')

    senha = gerar_senha_provisoria()
    funcionario.set_password(senha)
    funcionario.primeiro_acesso = True
    funcionario.save()

    messages.warning(
        request,
        f'Nova senha provisória de {funcionario.nome} (CPF {funcionario.username}): {senha}. '
        'A senha anterior deixou de valer. Informe agora; ela não será exibida novamente.',
        extra_tags='funcionario-senha',
    )
    return redirect('gerenciar_funcionario')

# =========================================================
# LOGIN, PRIMEIRO ACESSO E PREFEITURA ATIVA
# =========================================================

class CustomLoginView(LoginView):
    template_name = 'actions/login.html'
    authentication_form = LoginCPFForm
    redirect_authenticated_user = True

    def get_form_kwargs(self):
        # O HTML envia "contrato" e "senha"; o Django espera "username" e "password".
        kwargs = super().get_form_kwargs()
        if 'data' in kwargs:
            data = kwargs['data'].copy()
            data['username'] = data.get('contrato', '')
            data['password'] = data.get('senha', '')
            kwargs['data'] = data
        return kwargs

    def form_invalid(self, form):
        # Guarda o erro e o contrato digitado, e volta para a tela de login.
        # Assim, ao recarregar (F5), o erro não reaparece.
        self.request.session['login_erro'] = True
        self.request.session['login_contrato'] = self.request.POST.get('contrato', '')
        return redirect('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # pop() lê e apaga, então o erro aparece uma vez só
        context['erro_login'] = self.request.session.pop('login_erro', False)
        context['contrato_digitado'] = self.request.session.pop('login_contrato', '')
        return context

    def get_success_url(self):
        if self.request.user.primeiro_acesso:
            return reverse_lazy('redefinir-senha')
        return reverse_lazy('kanban')


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'actions/redefinir-senha.html'
    success_url = reverse_lazy('kanban')

    def form_valid(self, form):
        response = super().form_valid(form)
        usuario = self.request.user
        usuario.primeiro_acesso = False
        usuario.save(update_fields=['primeiro_acesso'])
        return response


@login_required
def minha_conta_view(request):
    if request.method == 'POST':
        form = MinhaContaForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            foto_anterior = Funcionario.objects.values_list('foto', flat=True).get(
                pk=request.user.pk,
            )
            usuario = form.save()
            foto_substituida = bool(request.FILES.get('foto')) or 'foto-clear' in request.POST
            if foto_anterior and foto_substituida:
                default_storage.delete(foto_anterior)
            messages.success(request, 'Seus dados foram atualizados com sucesso.')
            return redirect('minha_conta')
    else:
        form = MinhaContaForm(instance=request.user)

    return render(request, 'actions/minha-conta.html', {'form': form})


@login_required
def escolher_prefeitura_view(request):
    # Consultor escolhe em qual prefeitura vai trabalhar
    prefeituras = request.user.prefeituras_permitidas().order_by('nome_fantasia')
    if request.method == 'POST':
        escolhida = _por_pk(prefeituras, request.POST.get('prefeitura'))
        if escolhida:
            request.session['prefeitura_id'] = escolhida.pk
            return redirect('kanban')
        messages.error(request, 'Selecione uma prefeitura da lista.')
    return render(request, 'actions/escolher-prefeitura.html', {'prefeituras': prefeituras})


@login_required
@require_POST
def marcar_notificacao_lida_view(request, tipo, item_id):
    prefeitura = _prefeitura_ativa(request)
    if prefeitura is None:
        return redirect('escolher_prefeitura')

    if tipo == 'acao':
        acao = get_object_or_404(Acao, pk=item_id, prefeitura=prefeitura)
        NotificacaoLida.objects.get_or_create(
            usuario=request.user,
            acao=acao,
            etapa=None,
        )
    elif tipo == 'etapa':
        etapa = get_object_or_404(Etapa, pk=item_id, acao__prefeitura=prefeitura)
        NotificacaoLida.objects.get_or_create(
            usuario=request.user,
            acao=None,
            etapa=etapa,
        )
    else:
        return redirect('kanban')

    return redirect('kanban')


@login_required
@require_POST
def remover_notificacao_view(request, tipo, item_id):
    prefeitura = _prefeitura_ativa(request)
    if prefeitura is None:
        return JsonResponse({'success': False}, status=400)

    limite = timezone.localdate() + timedelta(days=7)
    status_encerrados = ('Concluído', 'Cancelado')
    if tipo == 'acao':
        alvo = get_object_or_404(
            Acao.objects.filter(
                prefeitura=prefeitura,
                data_fim__lte=limite,
            ).exclude(status__nome__in=status_encerrados),
            pk=item_id,
        )
        notificacao, _ = NotificacaoLida.objects.get_or_create(
            usuario=request.user,
            acao=alvo,
            etapa=None,
        )
    elif tipo == 'etapa':
        alvo = get_object_or_404(
            Etapa.objects.filter(
                acao__prefeitura=prefeitura,
                concluida=False,
                data_fim__lte=limite,
            ).exclude(acao__status__nome__in=status_encerrados),
            pk=item_id,
        )
        notificacao, _ = NotificacaoLida.objects.get_or_create(
            usuario=request.user,
            acao=None,
            etapa=alvo,
        )
    else:
        return JsonResponse({'success': False}, status=404)

    if not notificacao.removida:
        notificacao.removida = True
        notificacao.save(update_fields=['removida'])

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('kanban')


# =========================================================
# KANBAN
# =========================================================

@login_required
def kanban_view(request):
    prefeitura = _prefeitura_ativa(request)
    if prefeitura is None:
        return redirect('escolher_prefeitura')

    # Contagem só das ações desta prefeitura
    todos_status = Status.objects.annotate(
        total_acoes=Count('acoes', filter=Q(acoes__prefeitura=prefeitura)),
    ).order_by('ordem', 'id')

    acoes = Acao.objects.filter(prefeitura=prefeitura).select_related(
        'modelo', 'eixo', 'status', 'responsavel',
    ).annotate(
        total_etapas=Count('etapas'),
        etapas_concluidas=Count('etapas', filter=Q(etapas__concluida=True)),
    )

    for st in todos_status:
        st.acoes_lista = [a for a in acoes if a.status_id == st.id]
        st.cor_para_edicao = _cor_para_edicao(st)

    eixos_raiz = Eixo.objects.filter(pai__isnull=True).prefetch_related('subeixos')
    acoes_catalogo = AcaoCatalogo.objects.filter(ativa=True).select_related('eixo')
    acoes_catalogo_list = [{'id': a.id, 'nome': a.nome, 'eixo_id': a.eixo_id} for a in acoes_catalogo]

    # Dicionário de eixos, incluindo subeixos, para exibir no filtro do kanban
    context = {
        'prefeitura': prefeitura,
        'kanban': todos_status,
        'eixos_raiz': eixos_raiz,
        'acoes_catalogo_list': acoes_catalogo_list,
        'prioridades': Acao.Status_Prioridade.choices,
        'toast': request.session.pop('kanban_toast', None),
    }
    return render(request, 'actions/kanban-governanca.html', context)


# =========================================================
# AÇÕES E ETAPAS (operação)
# =========================================================

def _funcionario_por_cpf(cpf, prefeitura):
    # Aceita o CPF com ou sem máscara; o CPF é salvo só com dígitos
    digitos = re.sub(r'\D', '', cpf or '')
    if prefeitura is None or len(digitos) != 11:
        return None
    return Funcionario.objects.filter(prefeitura=prefeitura, username=digitos).first()


def _acao_da_prefeitura(request, acao_id):
    prefeitura = _prefeitura_ativa(request)
    if prefeitura is None or not str(acao_id).isdigit():
        return None
    return (
        Acao.objects
        .select_related('modelo', 'eixo', 'status', 'responsavel')
        .filter(prefeitura=prefeitura, pk=int(acao_id))
        .first()
    )


def _etapa_da_prefeitura(request, etapa_id):
    prefeitura = _prefeitura_ativa(request)
    if prefeitura is None:
        return None
    return (
        Etapa.objects
        .select_related('acao__status', 'acao__eixo', 'acao__responsavel', 'responsavel')
        .filter(pk=etapa_id, acao__prefeitura=prefeitura)
        .first()
    )


def _acao_cancelada(acao):
    # Ação cancelada é definitiva: não pode mais ser alterada
    return slugify(acao.status.nome) == 'cancelado'


def _serializar_acao(acao):
    return {
        'id': acao.id,
        'codigo': acao.codigo,
        'nome': acao.nome,
        'eixo': acao.eixo.nome,
        'prioridade': acao.prioridade,
        'custo': acao.custo,
        'data_inicio': _iso(acao.data_inicio),
        'data_fim': _iso(acao.data_fim),
        'observacoes': acao.observacoes or '',
        'responsavel': acao.responsavel.nome,
        'status': {'id': acao.status.id, 'nome': acao.status.nome, 'cor': acao.status.cor},
        'somente_leitura': _acao_cancelada(acao),
    }


def _serializar_etapa(etapa):
    return {
        'id': etapa.id,
        'nome': etapa.nome,
        'cpf': etapa.responsavel.cpf,
        'responsavel': etapa.responsavel.nome,
        'prioridade': etapa.prioridade,
        'data_inicio': _iso(etapa.data_inicio),
        'data_fim': _iso(etapa.data_fim),
        'observacoes': etapa.observacoes or '',
        'concluida': etapa.concluida,
    }


@login_required
@require_POST
def atualizar_status_acao(request, acao_id):
    # Só encontra a ação se ela for da prefeitura ativa
    acao = _acao_da_prefeitura(request, acao_id)

    # Ação inexistente, de outra prefeitura ou cancelada (definitiva): não muda nada
    if acao is None or _acao_cancelada(acao):
        return redirect('kanban')

    novo_status = request.POST.get('status')
    status_destino_id = None

    # Só salva (e avisa) se o status realmente mudou
    if novo_status and novo_status.isdigit() and str(acao.status_id) != novo_status:
        status_destino = get_object_or_404(Status, pk=novo_status)
        acao.status = status_destino
        acao.atualizado_por = request.user
        acao.save()
        status_destino_id = status_destino.pk
        request.session['kanban_toast'] = {
            'mensagem': f'Ação {acao.codigo} movida para "{status_destino.nome}".'
        }

    if status_destino_id is not None:
        return redirect(f'{reverse_lazy("kanban")}?status_destino={status_destino_id}')

    return redirect('kanban')


@login_required
@require_POST
def criar_acao_kanban_view(request):
    prefeitura = _prefeitura_ativa(request)
    if prefeitura is None:
        return _erro('Selecione uma prefeitura antes de criar ações.', 403)

    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST
    except (ValueError, TypeError):
        return _erro('Dados inválidos.')

    eixo_id = data.get('eixo')
    acao_catalogo_id = data.get('acao')
    acao_texto_custom = (data.get('novaAcao') or '').strip()
    status_id = data.get('status')
    prioridade = data.get('prioridade')

    if prioridade not in Acao.Status_Prioridade.values:
        return _erro('Prioridade inválida.')

    # O pop-up manda o custo com ponto decimal ("2121.22"); o formulário comum manda "2.121,22"
    custo_raw = str(data.get('custo', '0')).strip()
    if request.content_type != 'application/json':
        custo_raw = custo_raw.replace('.', '').replace(',', '.')
    try:
        custo = Decimal(custo_raw)
    except InvalidOperation:
        custo = 0.0

    data_inicio = _converter_data(data.get('dataInicio') or data.get('data_inicio'))
    data_fim = _converter_data(data.get('dataFim') or data.get('data_fim'))
    if not data_inicio or not data_fim:
        return _erro('Informe datas válidas.')
    if data_fim < data_inicio:
        return _erro('A data de fim não pode ser anterior à data de início.')

    observacoes = (data.get('observacoes') or '').strip() or None

    # Nome e eixo: do catálogo, ou digitados pelo usuário (sem criar nada no catálogo)
    if acao_catalogo_id and acao_catalogo_id != 'outra':
        modelo = AcaoCatalogo.objects.select_related('eixo').filter(
            pk=acao_catalogo_id, ativa=True).first() if str(acao_catalogo_id).isdigit() else None
        if modelo is None:
            return _erro('Ação do catálogo não encontrada.')
        nome_acao, eixo_obj = modelo.nome, modelo.eixo
    else:
        if not acao_texto_custom:
            return _erro('Informe o nome da ação.')
        modelo = None
        eixo_obj = _por_pk(Eixo.objects.all(), eixo_id)
        if eixo_obj is None:
            return _erro('Eixo não encontrado.')
        nome_acao = acao_texto_custom

    status_obj = _por_pk(Status.objects.all(), status_id) if status_id else Status.objects.first()
    if status_obj is None:
        return _erro('Status não encontrado.')

    # Responsável: CPF enviado pelo formulário, ou o próprio usuário se ele for da prefeitura
    cpf_responsavel = data.get('responsavel')
    if cpf_responsavel:
        responsavel = _funcionario_por_cpf(cpf_responsavel, prefeitura)
    elif request.user.prefeitura_id == prefeitura.pk:
        responsavel = request.user
    else:
        responsavel = None
    if responsavel is None:
        return _erro('Informe o responsável pela ação entre os funcionários da prefeitura.')

    # Valida o CPF de cada etapa ANTES de criar qualquer coisa
    etapas_validadas = []
    if request.content_type == 'application/json':
        for item in data.get('etapas', []):
            nome_etapa = item.get('nome') or item.get('etapaNome')
            if not nome_etapa:
                continue
            resp_etapa = _funcionario_por_cpf(item.get('cpf'), prefeitura)
            if resp_etapa is None:
                return _erro(
                    f'O CPF informado na etapa "{nome_etapa}" não foi encontrado '
                    'entre os funcionários da sua prefeitura.'
                )
            e_inicio = _converter_data(
                item.get('inicio') or item.get('data_inicio') or item.get('dataInicio')
                or item.get('etapaInicio')) or data_inicio
            e_fim = _converter_data(
                item.get('fim') or item.get('data_fim') or item.get('dataFim')
                or item.get('etapaFim')) or data_fim
            if e_fim < e_inicio:
                return _erro('A data de fim da etapa não pode ser anterior à data de início.')
            if not _datas_etapa_dentro_periodo(e_inicio, e_fim, data_inicio, data_fim):
                return _erro('As datas da etapa devem estar dentro do período da ação.')
            etapas_validadas.append((item, nome_etapa, resp_etapa, e_inicio, e_fim))
    else:
        nomes = request.POST.getlist('etapaNome[]')
        inicios = request.POST.getlist('etapaInicio[]')
        fims = request.POST.getlist('etapaFim[]')
        prioridades = request.POST.getlist('etapaPrioridade[]')
        obs_list = request.POST.getlist('etapaObservacoes[]')

        for i, nome in enumerate(nomes):
            if not nome.strip():
                continue
            e_inicio = _converter_data(inicios[i]) if i < len(inicios) else None
            e_fim = _converter_data(fims[i]) if i < len(fims) else None
            e_inicio = e_inicio or data_inicio
            e_fim = e_fim or data_fim
            if e_fim < e_inicio:
                return _erro('A data de fim da etapa não pode ser anterior à data de início.')
            if not _datas_etapa_dentro_periodo(e_inicio, e_fim, data_inicio, data_fim):
                return _erro('As datas da etapa devem estar dentro do período da ação.')
            etapas_validadas.append((
                {
                    'prioridade': prioridades[i] if i < len(prioridades) else '',
                    'observacoes': obs_list[i] if i < len(obs_list) else '',
                },
                nome.strip(),
                responsavel,
                e_inicio,
                e_fim,
            ))

    try:
        with transaction.atomic():
            nova_acao = Acao.objects.create(
                prefeitura=prefeitura,
                nome=nome_acao,
                eixo=eixo_obj,
                modelo=modelo,
                responsavel=responsavel,
                status=status_obj,
                prioridade=prioridade,
                custo=custo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                observacoes=observacoes,
                criado_por=request.user,
                atualizado_por=request.user,
            )

            if request.content_type == 'application/json':
                for item, nome_etapa, resp_etapa, e_inicio, e_fim in etapas_validadas:
                    Etapa.objects.create(
                        acao=nova_acao,
                        nome=nome_etapa,
                        responsavel=resp_etapa,
                        data_inicio=e_inicio,
                        data_fim=e_fim,
                        prioridade=item.get('prioridade') or '',
                        observacoes=item.get('observacoes', ''),
                        criado_por=request.user,
                        atualizado_por=request.user,
                    )
            else:
                for item, nome, resp_etapa, e_inicio, e_fim in etapas_validadas:
                    Etapa.objects.create(
                        acao=nova_acao,
                        nome=nome,
                        responsavel=resp_etapa,
                        data_inicio=e_inicio,
                        data_fim=e_fim,
                        prioridade=item['prioridade'],
                        observacoes=item['observacoes'],
                        criado_por=request.user,
                        atualizado_por=request.user,
                    )
    except IntegrityError:
        # Dois cadastros simultâneos podem gerar o mesmo código da ação
        logger.exception('Conflito ao criar ação na prefeitura %s', prefeitura.pk)
        return _erro('Não foi possível salvar a ação. Tente novamente.', 409)
    except Exception:
        logger.exception('Erro inesperado ao criar ação na prefeitura %s', prefeitura.pk)
        return _erro('Erro interno ao criar a ação.', 500)

    return JsonResponse({'success': True, 'message': 'Ação criada com sucesso!'}, status=201)


@login_required
def obter_detalhes_acao_view(request, acao_id):
    acao = _acao_da_prefeitura(request, acao_id)
    if acao is None:
        return _erro('Ação não encontrada.', 404)

    etapas = acao.etapas.select_related('responsavel').order_by('id')
    return JsonResponse({
        'success': True,
        'acao': _serializar_acao(acao),
        'etapas': [_serializar_etapa(e) for e in etapas],
        'prioridades': list(Acao.Status_Prioridade.values),
    })


@login_required
@require_POST
def editar_acao_view(request, acao_id):
    acao = _acao_da_prefeitura(request, acao_id)
    if acao is None:
        return _erro('Ação não encontrada.', 404)
    if _acao_cancelada(acao):
        return _erro('Uma ação cancelada não pode ser editada.', 403)

    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        return _erro('Dados inválidos.')

    prioridade = data.get('prioridade')
    if prioridade not in Acao.Status_Prioridade.values:
        return _erro('Prioridade inválida.')

    try:
        custo = Decimal(str(data.get('custo', '')).strip())
    except InvalidOperation:
        return _erro('Custo inválido.')
    if not custo.is_finite() or custo < 0:
        return _erro('Custo inválido.')

    data_inicio = _converter_data(data.get('data_inicio'))
    data_fim = _converter_data(data.get('data_fim'))
    if not data_inicio or not data_fim:
        return _erro('Informe datas válidas.')
    if data_fim < data_inicio:
        return _erro('A data de fim não pode ser anterior à data de início.')
    if acao.etapas.filter(
        Q(data_inicio__lt=data_inicio) | Q(data_fim__gt=data_fim)
    ).exists():
        return _erro('O período da ação não pode excluir datas de uma etapa existente.')

    acao.prioridade = prioridade
    acao.custo = custo
    acao.data_inicio = data_inicio
    acao.data_fim = data_fim
    acao.observacoes = (data.get('observacoes') or '').strip() or None
    acao.atualizado_por = request.user
    acao.save()

    return JsonResponse({'success': True, 'acao': _serializar_acao(acao)})


def _dados_etapa(request, acao):
    # Lê e valida o JSON de uma etapa. Retorna (dados, None) ou (None, resposta_de_erro).
    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        return None, _erro('Dados inválidos.')
    if not isinstance(data, dict):
        return None, _erro('Dados inválidos.')

    nome = (data.get('nome') or '').strip()
    if not nome or len(nome) > 45:
        return None, _erro('Informe um nome para a etapa com até 45 caracteres.')

    prioridade = data.get('prioridade')
    if prioridade not in Acao.Status_Prioridade.values:
        return None, _erro('Prioridade inválida.')

    data_inicio = _converter_data(data.get('data_inicio'))
    data_fim = _converter_data(data.get('data_fim'))
    if not data_inicio or not data_fim:
        return None, _erro('Informe datas válidas.')
    if data_fim < data_inicio:
        return None, _erro('A data de fim não pode ser anterior à data de início.')
    if not _datas_etapa_dentro_periodo(
        data_inicio, data_fim, acao.data_inicio, acao.data_fim
    ):
        return None, _erro('As datas da etapa devem estar dentro do período da ação.')

    responsavel = _funcionario_por_cpf(data.get('cpf'), _prefeitura_ativa(request))
    if responsavel is None:
        return None, _erro('CPF do responsável não encontrado entre os funcionários da sua prefeitura.')

    return {
        'nome': nome,
        'responsavel': responsavel,
        'prioridade': prioridade,
        'data_inicio': data_inicio,
        'data_fim': data_fim,
        'observacoes': (data.get('observacoes') or '').strip() or None,
    }, None


@login_required
@require_POST
def adicionar_etapa_view(request, acao_id):
    acao = _acao_da_prefeitura(request, acao_id)
    if acao is None:
        return _erro('Ação não encontrada.', 404)
    if _acao_cancelada(acao):
        return _erro('Uma ação cancelada não pode ser editada.', 403)

    dados, erro = _dados_etapa(request, acao)
    if erro:
        return erro

    etapa = Etapa.objects.create(
        acao=acao, criado_por=request.user, atualizado_por=request.user, **dados)
    return JsonResponse({'success': True, 'etapa': _serializar_etapa(etapa)}, status=201)


@login_required
@require_POST
def editar_etapa_view(request, etapa_id):
    etapa = _etapa_da_prefeitura(request, etapa_id)
    if etapa is None:
        return _erro('Etapa não encontrada.', 404)
    if _acao_cancelada(etapa.acao):
        return _erro('Uma ação cancelada não pode ser editada.', 403)

    dados, erro = _dados_etapa(request, etapa.acao)
    if erro:
        return erro

    for campo, valor in dados.items():
        setattr(etapa, campo, valor)
    etapa.atualizado_por = request.user
    etapa.save()

    return JsonResponse({'success': True, 'etapa': _serializar_etapa(etapa)})


@login_required
@require_POST
def alterar_etapa_view(request, etapa_id):
    # Marca ou desmarca a etapa como concluída
    etapa = _etapa_da_prefeitura(request, etapa_id)
    if etapa is None:
        return _erro('Etapa não encontrada.', 404)
    if _acao_cancelada(etapa.acao):
        return _erro('Uma ação cancelada não pode ser editada.', 403)

    etapa.concluida = not etapa.concluida
    etapa.atualizado_por = request.user
    etapa.save(update_fields=['concluida', 'atualizado_por', 'atualizado_em'])
    return JsonResponse({'success': True, 'concluida': etapa.concluida})


@login_required
@require_POST
def excluir_etapa_view(request, etapa_id):
    etapa = _etapa_da_prefeitura(request, etapa_id)
    if etapa is None:
        return _erro('Etapa não encontrada.', 404)
    if _acao_cancelada(etapa.acao):
        return _erro('Uma ação cancelada não pode ser editada.', 403)

    etapa.delete()
    return JsonResponse({'success': True, 'message': 'Etapa excluída com sucesso!'})


@login_required
@require_POST
def excluir_acao_view(request, acao_id):
    acao = _acao_da_prefeitura(request, acao_id)
    if acao is None:
        return _erro('Ação não encontrada.', 404)
    if _acao_cancelada(acao):
        return _erro('Uma ação cancelada não pode ser excluída.', 403)

    try:
        with transaction.atomic():
            # As etapas usam on_delete=PROTECT, então são apagadas antes da ação
            acao.etapas.all().delete()
            acao.delete()
    except ProtectedError:
        return _erro('Não foi possível excluir a ação porque ela está vinculada a outros registros.', 409)

    return JsonResponse({'success': True, 'message': 'Ação excluída com sucesso!'})

# =========================================================
# DASHBOARD
# =========================================================

PALETA_EIXOS = ['#3e4a89', '#2e8b57', '#b5b94a', '#7b3f9e', '#d98a1f', '#c0392b', '#2aa198', '#8a8f99']
SLUGS_EM_EXECUCAO = ('em-execucao', 'execucao')
DIAS_PROXIMO = 15   # etapas que vencem nesse prazo entram na tabela e no gráfico de prazos
DIAS_URGENTE = 7    # etapa que vence em até esse prazo aparece em amarelo na tabela


def _moeda(valor):
    texto = f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
    return f'R$ {texto}'



def _gradiente(fatias):
    # fatias: lista de (cor, valor). Monta o conic-gradient que desenha a rosca
    total = sum(valor for _, valor in fatias)
    if not total:
        return 'conic-gradient(#e5e2d9 0 100%)'
    partes, inicio = [], 0.0
    for cor, valor in fatias:
        if not valor:
            continue
        fim = inicio + float(valor) / float(total) * 100
        partes.append(f'{cor} {inicio:.2f}% {fim:.2f}%')
        inicio = fim
    return 'conic-gradient(' + ', '.join(partes) + ')'


def _distribuicao(itens):
    # itens: lista de (nome, cor, valor, texto). Devolve tudo que a rosca e a legenda precisam
    total = sum(valor for _, _, valor, _ in itens)
    legenda = [
        {
            'nome': nome,
            'cor': cor,
            'pct': round(valor / total * 100) if total else 0,
            'texto': texto,
        }
        for nome, cor, valor, texto in itens
    ]
    return {
        'gradiente': _gradiente([(cor, valor) for _, cor, valor, _ in itens]),
        'legenda': legenda,
        'vazio': total == 0,
    }


@login_required
def dashboard_view(request):
    prefeitura = _prefeitura_ativa(request)
    if prefeitura is None:
        return redirect('escolher_prefeitura')

    hoje = date.today()
    limite_proximas = hoje + timedelta(days=DIAS_PROXIMO)

    acoes = list(
        Acao.objects.filter(prefeitura=prefeitura)
        .select_related('status', 'eixo')
    )
    # Ativas: não estão canceladas nem concluídas
    ativas = [a for a in acoes if not _acao_cancelada(a) and slugify(a.status.nome) != 'concluido']

    # Cards do topo
    total_ativas = len(ativas)
    total_execucao = sum(1 for a in ativas if slugify(a.status.nome) in SLUGS_EM_EXECUCAO)
    total_atrasadas = sum(1 for a in ativas if a.data_fim < hoje)
    impacto = sum(a.custo for a in ativas)

    # Barras: quantas ações (de todas) há em cada status
    contagem_status = Counter(a.status_id for a in acoes)
    maior = max(contagem_status.values(), default=0)
    barras = []
    for status in Status.objects.order_by('ordem', 'id'):
        total = contagem_status.get(status.id, 0)
        barras.append({
            'nome': status.nome,
            'cor': status.cor,
            'total': total,
            'pct': round(total / maior * 100) if maior else 0,
        })

    # Rosca por eixo, com quantidade e custo das ações ativas
    por_eixo = {}
    for a in ativas:
        nome = a.eixo.nome if a.eixo_id else 'Sem eixo'
        qtd, custo = por_eixo.get(nome, (0, Decimal('0')))
        por_eixo[nome] = (qtd + 1, custo + a.custo)

    eixos = sorted(por_eixo.items(), key=lambda item: item[1][0], reverse=True)
    cores = [PALETA_EIXOS[i % len(PALETA_EIXOS)] for i in range(len(eixos))]
    fatias_qtd = [(nome, cor, qtd, str(qtd)) for (nome, (qtd, _)), cor in zip(eixos, cores)]
    fatias_custo = [(nome, cor, custo, _moeda(custo)) for (nome, (_, custo)), cor in zip(eixos, cores)]

    # Rosca por prazo, com as ações ativas
    vence_logo = sum(1 for a in ativas if hoje <= a.data_fim <= limite_proximas)
    no_prazo = total_ativas - total_atrasadas - vence_logo
    fatias_prazo = [
        ('Atrasadas', '#c0392b', total_atrasadas, str(total_atrasadas)),
        (f'Vence em até {DIAS_PROXIMO} dias', '#e0b400', vence_logo, str(vence_logo)),
        ('No prazo', '#2e8b57', no_prazo, str(no_prazo)),
    ]

    # Tabela: etapas não concluídas de ações ativas que vencem no período
    etapas = (
        Etapa.objects.filter(
            acao__in=ativas,
            concluida=False,
            data_fim__lte=limite_proximas,
        )
        .select_related('acao__eixo', 'acao__status', 'responsavel')
        .order_by('data_fim', 'id')[:10]
    )

    proximas = []
    for e in etapas:
        acao = e.acao
        dias = (e.data_fim - hoje).days
        nivel = 'vermelho' if dias < 0 else ('amarelo' if dias <= DIAS_URGENTE else 'verde')
        prioridade = e.prioridade or acao.prioridade
        proximas.append({
            'eixo': acao.eixo.nome if acao.eixo_id else '—',
            'nome_acao': acao.nome,
            'etapa': e.nome,
            'responsavel': e.responsavel.nome,
            'data': e.data_fim,
            'nivel': nivel,
            'status': acao.status.nome,
            'prioridade': prioridade or '—',
            'prioridade_classe': slugify(prioridade),
        })

    context = {
        'total_ativas': total_ativas,
        'total_execucao': total_execucao,
        'total_atrasadas': total_atrasadas,
        'impacto': _moeda(impacto),
        'barras': barras,
        'distribuicoes': [
            {'chave': 'visao_geral', 'dados': _distribuicao(fatias_qtd)},
            {'chave': 'por_eixo', 'dados': _distribuicao(fatias_custo)},
            {'chave': 'por_prazo', 'dados': _distribuicao(fatias_prazo)},
        ],
        'proximas_etapas': proximas,
        'dias_proximo': DIAS_PROXIMO,
    }
    return render(request, 'actions/dashboard.html', context)