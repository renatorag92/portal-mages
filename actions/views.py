import json
import re
import webcolors
from decimal import Decimal, InvalidOperation
from django import forms
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.db.models import Count, Q
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.contrib import messages
from django.utils.dateparse import parse_date
from django.utils.text import slugify
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.urls import reverse_lazy
from .forms import ConsultoriaForm, PrefeituraForm
from .models import AcaoCatalogo, Acao, Etapa, Eixo, Status, Funcionario, Prefeitura, Consultoria

PT_EN = dict(zip(
    'azul vermelho verde amarelo laranja roxo rosa preto branco cinza marrom ciano dourado prata turquesa bege lilás violeta magenta índigo salmão coral vinho lima'.split(),
    'blue red green yellow orange purple pink black white gray brown cyan gold silver turquoise beige lavender violet magenta indigo salmon coral maroon lime'.split(),
))
MAX_STATUS_COLUMNS = 7
EN_PT = {ingles: portugues for portugues, ingles in PT_EN.items()}


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
        dados['prefeitura_id'] = registro.prefeitura_id
        dados['prefeitura_nome'] = registro.prefeitura.nome_fantasia
    return dados


def _usuario_configuracoes(user):
    return user.is_staff or user.is_superuser


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
    registro = Consultoria.objects.select_related('prefeitura').order_by('pk').first()
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
        with transaction.atomic():
            if registro_atual is None and Consultoria.objects.exists():
                return JsonResponse({
                    'success': False,
                    'errors': {'__all__': ['Já existe uma consultoria cadastrada.']},
                }, status=409)
            registro = registro_atual or Consultoria()
            for campo in ('cnpj', 'nome_fantasia', 'nome_juridico', 'endereco', 'prefeitura'):
                setattr(registro, campo, form.cleaned_data[campo])
            registro.save()
    except IntegrityError:
        cnpj_duplicado = Consultoria.objects.filter(
            cnpj=form.cleaned_data['cnpj'],
        ).exclude(pk=registro_atual.pk if registro_atual else None).exists()
        campo = 'cnpj' if cnpj_duplicado else 'prefeitura'
        mensagem = 'CNPJ já cadastrado.' if cnpj_duplicado else 'Esta prefeitura já possui uma consultoria vinculada.'
        return JsonResponse({'success': False, 'errors': {campo: [mensagem]}}, status=409)

    return JsonResponse({'success': True, 'registro': _serializar_cadastro(registro, consultoria=True)})


class StatusForm(forms.ModelForm):
    cor = forms.CharField(
        max_length=45,
    )

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
    class Meta:
        model = Eixo
        fields = ('nome', 'descricao')

    def clean_nome(self):
        nome = (self.cleaned_data.get('nome') or '').strip()
        if not nome:
            raise ValidationError('Informe o nome do eixo.')
        if Eixo.objects.filter(nome__iexact=nome).exclude(pk=self.instance.pk).exists():
            raise ValidationError('Já existe um eixo com esse nome.')
        return nome

    def clean_descricao(self):
        descricao = (self.cleaned_data.get('descricao') or '').strip()
        return descricao


class CustomLoginView(LoginView):
    template_name = 'actions/login.html'
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
        user = self.request.user
        # Corrigido para user.perfil
        if hasattr(user, 'perfil') and user.perfil.primeiro_acesso:
            return reverse_lazy('redefinir-senha')
        return reverse_lazy('kanban')


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'actions/redefinir-senha.html'
    success_url = reverse_lazy('kanban')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.perfil.primeiro_acesso = False
        self.request.user.perfil.save()
        return response

@login_required
def kanban_view(request):
    prefeitura_logada = request.user.perfil.prefeitura
    todos_status = Status.objects.annotate(total_acoes=Count('acoes')).order_by('ordem', 'id')

    acoes = Acao.objects.filter(
        secretario__prefeitura=prefeitura_logada
    ).select_related(
        'acao_catalogo__eixo', 'status', 'secretario'
    ).annotate(
        total_etapas=Count('etapas'),
        etapas_concluidas=Count('etapas', filter=Q(etapas__concluida=True)),
    )

    for st in todos_status:
        st.acoes_lista = [a for a in acoes if a.status_id == st.id]
        st.cor_para_edicao = _cor_para_edicao(st)

    # Dados adicionais necessários para popular o modal de cadastro de ação
    eixos = Eixo.objects.all()
    acoes_catalogo = AcaoCatalogo.objects.select_related('eixo').all()
    acoes_catalogo_list = [{'id': a.id, 'nome': a.nome, 'eixo_id': a.eixo.id} for a in acoes_catalogo]

    context = {
        'kanban': todos_status,
        'eixos': eixos,
        'acoes_catalogo_list': acoes_catalogo_list,
        'prioridades': Acao.Status_Prioridade.choices,
        'toast': request.session.pop('kanban_toast', None),
    }

    return render(request, 'actions/kanban-governanca.html', context)


@login_required
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

    eixo_lista = Eixo.objects.annotate(total_acoes=Count('acoes')).order_by('nome')
    return render(request, 'actions/gerenciar-eixo.html', {
        'form': form,
        'eixo_lista': eixo_lista,
        'eixo_edicao': eixo,
    })


@login_required
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


@login_required
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
        'status': {
            'id': status.id,
            'nome': status.nome,
            'cor': status.cor,
        },
    })


@login_required
@require_POST
def excluir_status_view(request, status_id):
    status = get_object_or_404(Status, pk=status_id)

    try:
        status.delete()
        messages.success(request, 'Status excluído com sucesso.', extra_tags='status-deleted')
    except ProtectedError:
        # As ações usam on_delete=PROTECT: status com ações vinculadas não pode ser excluído
        messages.error(
            request,
            'Este status não pode ser excluído porque está vinculado a uma ou mais ações.',
            extra_tags='status-delete-blocked',
        )
    return redirect('gerenciar_status')


@login_required
@require_POST
def atualizar_status_acao(request, acao_id):
    # Só encontra a ação se ela for da prefeitura do usuário logado
    acao = _acao_da_prefeitura(request, acao_id)

    # Ação inexistente, de outra prefeitura ou cancelada (definitiva): não muda nada
    if acao is None or _acao_cancelada(acao):
        return redirect('kanban')

    novo_status = request.POST.get('status')

    # Só salva (e avisa) se o status realmente mudou
    if novo_status and novo_status.isdigit() and str(acao.status_id) != novo_status:
        status_destino = get_object_or_404(Status, pk=novo_status)
        acao.status = status_destino
        acao.save()
        request.session['kanban_toast'] = {
            'mensagem': f'Ação {acao.codigo} movida para "{status_destino.nome}".'
        }

    return redirect('kanban')


# =========================================================
# APOIO (ações e etapas)
# =========================================================

def _erro(mensagem, status=400):
    return JsonResponse({'success': False, 'error': mensagem}, status=status)


def _prefeitura_do_usuario(request):
    perfil = getattr(request.user, 'perfil', None)
    return perfil.prefeitura if perfil else None


def _converter_data(valor):
    try:
        return parse_date(valor or '')
    except ValueError:
        return None


def _funcionario_por_cpf(cpf, prefeitura):
    # Aceita o CPF com ou sem máscara, e só procura entre os funcionários da prefeitura
    digitos = re.sub(r'\D', '', cpf or '')
    if len(digitos) != 11:
        return None
    mascarado = f'{digitos[:3]}.{digitos[3:6]}.{digitos[6:9]}-{digitos[9:]}'
    return (
        Funcionario.objects
        .filter(prefeitura=prefeitura)
        .filter(Q(cpf=digitos) | Q(cpf=mascarado))
        .first()
    )


def _acao_da_prefeitura(request, acao_id):
    prefeitura = _prefeitura_do_usuario(request)
    if prefeitura is None:
        return None
    return (
        Acao.objects
        .select_related('acao_catalogo__eixo', 'status', 'secretario')
        .filter(codigo=str(acao_id), secretario__prefeitura=prefeitura)
        .first()
    )


def _etapa_da_prefeitura(request, etapa_id):
    prefeitura = _prefeitura_do_usuario(request)
    if prefeitura is None:
        return None
    return (
        Etapa.objects
        .select_related('acao__status', 'acao__secretario', 'responsavel')
        .filter(pk=etapa_id, acao__secretario__prefeitura=prefeitura)
        .first()
    )


def _acao_cancelada(acao):
    # Ação cancelada é definitiva: não pode mais ser alterada
    return slugify(acao.status.nome) == 'cancelado'


def _iso(data):
    return data.isoformat() if hasattr(data, 'isoformat') else (data or '')


def _serializar_acao(acao):
    catalogo = acao.acao_catalogo
    return {
        'codigo': acao.codigo,
        'nome': catalogo.nome if catalogo else (acao.nova_acao_texto or ''),
        'eixo': catalogo.eixo.nome if catalogo else '',
        'prioridade': acao.prioridade,
        'custo': acao.custo,
        'data_inicio': _iso(acao.data_inicio),
        'data_fim': _iso(acao.data_fim),
        'observacoes': acao.observacoes or '',
        'responsavel': acao.secretario.nome,
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


# =========================================================
# CADASTRO DE AÇÃO (pop-up do Kanban)
# =========================================================

@require_POST
def criar_acao_kanban_view(request):
    try:
        if request.content_type == 'application/json':
            data = json.loads(request.body)
        else:
            data = request.POST

        eixo_id = data.get('eixo')
        acao_catalogo_id = data.get('acao')
        acao_texto_custom = data.get('novaAcao', '').strip()

        status_id = data.get('status')
        prioridade = data.get('prioridade')

        # Tratamento do custo.
        # O pop-up já manda o valor como "2121.22" (ponto decimal). Só um formulário comum
        # manda no formato brasileiro ("2.121,22"), que precisa ser convertido.
        custo_raw = str(data.get('custo', '0')).strip()
        if request.content_type != 'application/json':
            custo_raw = custo_raw.replace('.', '').replace(',', '.')
        try:
            custo = float(custo_raw)
        except ValueError:
            custo = 0.0

        data_inicio = data.get('dataInicio') or data.get('data_inicio')
        data_fim = data.get('dataFim') or data.get('data_fim')
        observacoes = data.get('observacoes')

        # Obtém o funcionário/secretário padrão da prefeitura do usuário logado
        prefeitura_logada = request.user.perfil.prefeitura
        secretario = Funcionario.objects.filter(prefeitura=prefeitura_logada).first()

        if not secretario:
            return JsonResponse({
                'success': False,
                'error': 'Cadastre pelo menos um Secretário/Funcionário no Admin antes de criar ações.'
            }, status=400)

        # Valida o CPF de cada etapa ANTES de criar qualquer coisa
        etapas_validadas = []
        if request.content_type == 'application/json':
            for item in data.get('etapas', []):
                nome_etapa = item.get('nome') or item.get('etapaNome')
                if not nome_etapa:
                    continue

                responsavel = _funcionario_por_cpf(item.get('cpf'), prefeitura_logada)
                if responsavel is None:
                    return JsonResponse({
                        'success': False,
                        'error': f'O CPF informado na etapa "{nome_etapa}" não foi encontrado entre os funcionários da sua prefeitura.'
                    }, status=400)

                etapas_validadas.append((item, nome_etapa, responsavel))

        with transaction.atomic():
            eixo_obj = Eixo.objects.get(id=eixo_id)

            if acao_catalogo_id and acao_catalogo_id != 'outra':
                acao_catalogo_obj = AcaoCatalogo.objects.get(id=acao_catalogo_id)
            else:
                acao_catalogo_obj = AcaoCatalogo.objects.create(nome=acao_texto_custom, eixo=eixo_obj)

            status_obj = Status.objects.get(id=status_id) if status_id else Status.objects.first()

            nova_acao = Acao.objects.create(
                acao_catalogo=acao_catalogo_obj,
                secretario=secretario,
                status=status_obj,
                prioridade=prioridade,
                custo=custo,
                data_inicio=data_inicio,
                data_fim=data_fim,
                observacoes=observacoes,
            )

            # --- CRIAÇÃO DAS ETAPAS ---
            if request.content_type == 'application/json':
                for item, nome_etapa, responsavel in etapas_validadas:
                    # O pop-up manda "inicio" e "fim"
                    e_inicio = item.get('inicio') or item.get('data_inicio') or item.get('dataInicio') or item.get('etapaInicio') or data_inicio
                    e_fim = item.get('fim') or item.get('data_fim') or item.get('dataFim') or item.get('etapaFim') or data_fim

                    Etapa.objects.create(
                        acao=nova_acao,
                        nome=nome_etapa,
                        responsavel=responsavel,
                        data_inicio=e_inicio,
                        data_fim=e_fim,
                        prioridade=item.get('prioridade') or '',
                        observacoes=item.get('observacoes', '')
                    )
            else:
                nomes = request.POST.getlist('etapaNome[]')
                inicios = request.POST.getlist('etapaInicio[]')
                fims = request.POST.getlist('etapaFim[]')
                prioridades = request.POST.getlist('etapaPrioridade[]')
                obs_list = request.POST.getlist('etapaObservacoes[]')

                for i, nome in enumerate(nomes):
                    if nome.strip():
                        d_inicio = inicios[i] if (i < len(inicios) and inicios[i]) else data_inicio
                        d_fim = fims[i] if (i < len(fims) and fims[i]) else data_fim
                        prio = prioridades[i] if i < len(prioridades) else ''
                        obs = obs_list[i] if i < len(obs_list) else ''

                        Etapa.objects.create(
                            acao=nova_acao,
                            nome=nome.strip(),
                            responsavel=secretario,
                            data_inicio=d_inicio,
                            data_fim=d_fim,
                            prioridade=prio,
                            observacoes=obs
                        )

        return JsonResponse({'success': True, 'message': 'Ação criada com sucesso!'}, status=201)

    except Eixo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Eixo não encontrado.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


# =========================================================
# DETALHES, EDIÇÃO E ETAPAS (pop-up de detalhes)
# =========================================================

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

    acao.prioridade = prioridade
    acao.custo = float(custo)
    acao.data_inicio = data_inicio
    acao.data_fim = data_fim
    acao.observacoes = (data.get('observacoes') or '').strip() or None
    acao.save()

    return JsonResponse({'success': True, 'acao': _serializar_acao(acao)})


def _dados_etapa(request):
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

    responsavel = _funcionario_por_cpf(data.get('cpf'), _prefeitura_do_usuario(request))
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

    dados, erro = _dados_etapa(request)
    if erro:
        return erro

    etapa = Etapa.objects.create(acao=acao, **dados)
    return JsonResponse({'success': True, 'etapa': _serializar_etapa(etapa)}, status=201)


@login_required
@require_POST
def editar_etapa_view(request, etapa_id):
    etapa = _etapa_da_prefeitura(request, etapa_id)
    if etapa is None:
        return _erro('Etapa não encontrada.', 404)
    if _acao_cancelada(etapa.acao):
        return _erro('Uma ação cancelada não pode ser editada.', 403)

    dados, erro = _dados_etapa(request)
    if erro:
        return erro

    for campo, valor in dados.items():
        setattr(etapa, campo, valor)
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
    etapa.save(update_fields=['concluida'])
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