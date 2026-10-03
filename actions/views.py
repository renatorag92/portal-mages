import json
import webcolors
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count
from django.db.models.deletion import ProtectedError
from django.http import JsonResponse
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.urls import reverse_lazy
from .models import AcaoCatalogo, Acao, Etapa, Eixo, Status

PT_EN = dict(zip(
    'azul vermelho verde amarelo laranja roxo rosa preto branco cinza marrom ciano dourado prata turquesa bege lilás violeta magenta índigo salmão coral vinho lima'.split(),
    'blue red green yellow orange purple pink black white gray brown cyan gold silver turquoise beige lavender violet magenta indigo salmon coral maroon lime'.split(),
))


class StatusForm(forms.ModelForm):
    cor = forms.CharField(
        max_length=45,
    )

    class Meta:
        model = Status
        fields = ('nome', 'cor')

    def clean_cor(self):
        cor = self.cleaned_data['cor'].strip().lower()
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


class CustomLoginView(LoginView):
    template_name = 'actions/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        # Corrigido para user.perfil
        if hasattr(user, 'perfil') and user.perfil.primeiro_acesso:
            return reverse_lazy('password-change')
        return reverse_lazy('kanban')


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'actions/password-change.html'
    success_url = reverse_lazy('kanban')

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.perfil.primeiro_acesso = False
        self.request.user.perfil.save()
        return response


@login_required
def cadastro_acoes_view(request):
    eixos = Eixo.objects.all()
    acoes_catalogo = AcaoCatalogo.objects.select_related('eixo').all()
    status_lista = Status.objects.order_by('ordem', 'id')

    # Passa a lista pura de dicionários Python (o template tratará com json_script)
    acoes_catalogo_list = [{'id': a.id, 'nome': a.nome, 'eixo_id': a.eixo.id} for a in acoes_catalogo]
    
    context = {
        'eixos': [(e.id, e.nome) for e in eixos],
        'acoes_catalogo_objetos': acoes_catalogo, 
        'acoes_catalogo_list': acoes_catalogo_list,
        'status_lista': status_lista,
        'prioridades': Acao.Status_Prioridade.choices, 
    }
    return render(request, 'actions/cadastro-de-acoes.html', context)


@login_required
def kanban_view(request):
    prefeitura_logada = request.user.perfil.prefeitura
    todos_status = Status.objects.order_by('ordem', 'id')

    acoes = Acao.objects.filter(
        secretario__prefeitura=prefeitura_logada
    ).select_related('acao_catalogo__eixo', 'acao_catalogo', 'status', 'secretario')

    for st in todos_status:
        st.acoes_lista = [a for a in acoes if a.status_id == st.id]

    return render(request, 'actions/kanban-governanca.html', {'kanban': todos_status})


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
    return render(request, 'actions/gerenciar-status.html', {
        'form': form,
        'status_lista': status_lista,
        'status_edicao': status,
    })


@login_required
@require_POST
def excluir_status_view(request, status_id):
    status = get_object_or_404(Status, pk=status_id)
    if status.acoes.exists():
        messages.error(
            request,
            'Este status não pode ser excluído porque está vinculado a uma ou mais ações.',
            extra_tags='status-delete-blocked',
        )
        return redirect('gerenciar_status')

    try:
        status.delete()
        messages.success(request, 'Status excluído com sucesso.', extra_tags='status-deleted')
    except ProtectedError:
        messages.error(
            request,
            'Este status não pode ser excluído porque está vinculado a uma ou mais ações.',
            extra_tags='status-delete-blocked',
        )
    return redirect('gerenciar_status')


def atualizar_status_acao(request, acao_id):
    if request.method == 'POST':
        acao = get_object_or_404(Acao, id=acao_id)
        novo_status = request.POST.get('status')
        
        if novo_status:
            acao.status_id = novo_status # Atribuição via status_id
            acao.save()
            
    return redirect('kanban') 


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
        custo = data.get('custo')
        data_inicio = data.get('dataInicio')
        data_fim = data.get('dataFim')
        observacoes = data.get('observacoes')

        secretario = request.user.perfil.secretario

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
                custo=custo or 0,
                data_inicio=data_inicio,
                data_fim=data_fim,
                observacoes=observacoes,
            )

            # Grava etapas iniciais caso tenham sido informadas na criação
            if request.content_type == 'application/json':
                etapas_data = data.get('etapas', [])
                for item in etapas_data:
                    if item.get('nome'):
                        Etapa.objects.create(acao=nova_acao, nome=item.get('nome'))
            else:
                nomes = request.POST.getlist('etapaNome[]')
                for nome in nomes:
                    if nome.strip():
                        Etapa.objects.create(acao=nova_acao, nome=nome.strip())

        return JsonResponse({
            'success': True,
            'message': 'Ação criada com sucesso!',
            'card': { 
                'id': nova_acao.id,
                'nome': nova_acao.acao_catalogo.nome,
                'eixo': nova_acao.acao_catalogo.eixo.nome,
                'prioridade': nova_acao.get_prioridade_display() if hasattr(nova_acao, 'get_prioridade_display') else nova_acao.prioridade,
                'status_id': nova_acao.status.id,
                'status_nome': nova_acao.status.nome,
                'secretario': getattr(nova_acao.secretario, 'nome', str(nova_acao.secretario)),
                'custo': str(nova_acao.custo),
            },
        }, status=201)
             
    except Eixo.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Eixo não encontrado.'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


def obter_detalhes_acao_view(request, acao_id):
    try:
        acao = Acao.objects.select_related('acao_catalogo', 'secretario').get(id=acao_id)
        etapas = list(acao.etapas.values('id', 'nome', 'concluida'))

        return JsonResponse({
            'success': True,
            'acao': {
                'id': acao.id,
                'nome': acao.acao_catalogo.nome,
                'custo': acao.custo,
                'prioridade': acao.prioridade,
                'data_inicio': acao.data_inicio,
                'data_fim': acao.data_fim,
                'observacoes': acao.observacoes,
            },
            'etapas': etapas,
        })
    except Acao.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ação não encontrada.'}, status=404)


@require_POST
def alterar_etapa_view(request, etapa_id):
    try:
        etapa = Etapa.objects.get(id=etapa_id)
        etapa.concluida = not etapa.concluida
        etapa.save()
        return JsonResponse({'success': True, 'concluida': etapa.concluida})
    except Etapa.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Etapa não encontrada.'}, status=404)


@require_POST
def editar_acao_view(request, acao_id):
    # Edita os dados da Ação e realiza a sincronização em bloco
    try:
        acao = Acao.objects.get(id=acao_id)
        data = (
            json.loads(request.body)
            if request.content_type == 'application/json'
            else request.POST
        )

        with transaction.atomic():
            # 1. Atualiza dados principais
            acao.prioridade = data.get('prioridade', acao.prioridade)
            acao.custo = data.get('custo', acao.custo)
            acao.data_inicio = data.get('data_inicio', acao.data_inicio)
            acao.data_fim = data.get('data_fim', acao.data_fim)
            acao.observacoes = data.get('observacoes', acao.observacoes)
            acao.save()

            # 2. Sincroniza a lista de etapas
            etapas_data = data.get('etapas')
            if etapas_data is not None:
                ids_manter = []

                for item in etapas_data:
                    etapa_id = item.get('id')
                    nome = item.get('nome', '').strip()

                    if not nome:
                        continue  # Descarta entradas vazias

                    if etapa_id:
                        # Atualiza etapa existente
                        Etapa.objects.filter(id=etapa_id, acao=acao).update(
                            nome=nome,
                            concluida=item.get('concluida', False)
                        )
                        ids_manter.append(etapa_id)
                    else:
                        # Cria nova etapa vinculada à Ação
                        nova_etapa = Etapa.objects.create(
                            acao=acao,
                            nome=nome,
                            concluida=item.get('concluida', False)
                        )
                        ids_manter.append(nova_etapa.id)

                # Remove do banco as etapas que o usuário apagou na interface
                acao.etapas.exclude(id__in=ids_manter).delete()

        return JsonResponse({'success': True, 'message': 'Ação e etapas atualizadas com sucesso!'})

    except Acao.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ação não encontrada.'}, status=404)
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)


@require_POST
def excluir_acao_view(request, acao_id):
    try:
        acao = Acao.objects.get(id=acao_id)
        acao.delete()
        return JsonResponse({'success': True, 'message': 'Ação excluída com sucesso!'})
    except Acao.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Ação não encontrada.'}, status=404)