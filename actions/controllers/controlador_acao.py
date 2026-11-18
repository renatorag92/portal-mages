import json
import logging

from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from ..models import Acao
from ..services.acao_service import AcaoService
from ..services.autenticacao_service import AutenticacaoService
from ..services.excecoes import ErroRegraNegocio
from ._base import erro_json

logger = logging.getLogger(__name__)


@login_required
@require_POST
def atualizar_status_acao(request, acao_id):
    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    resultado = AcaoService.mover_status(prefeitura, acao_id, request.POST.get('status'), request.user)
    if resultado is False:
        raise Http404()
    if resultado is not None:
        acao, status_destino = resultado
        request.session['kanban_toast'] = {
            'mensagem': f'Ação {acao.codigo} movida para "{status_destino.nome}".'
        }
        return redirect(f'{reverse_lazy("kanban")}?status_destino={status_destino.pk}')
    return redirect('kanban')


@login_required
@require_POST
def criar_acao_kanban_view(request):
    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    if prefeitura is None:
        return erro_json('Selecione uma prefeitura antes de criar ações.', 403)

    is_json = request.content_type == 'application/json'
    try:
        data = json.loads(request.body) if is_json else request.POST
    except (ValueError, TypeError):
        return erro_json('Dados inválidos.')

    post_lists = None if is_json else {
        'nomes': request.POST.getlist('etapaNome[]'),
        'inicios': request.POST.getlist('etapaInicio[]'),
        'fims': request.POST.getlist('etapaFim[]'),
        'prioridades': request.POST.getlist('etapaPrioridade[]'),
        'obs_list': request.POST.getlist('etapaObservacoes[]'),
    }

    try:
        nova_acao = AcaoService.criar_com_etapas(
            prefeitura, request.user, data, is_json=is_json, post_lists=post_lists
        )
    except ErroRegraNegocio as e:
        return erro_json(e.mensagem, e.status)
    except Exception:
        logger.exception('Erro inesperado ao criar ação na prefeitura %s', prefeitura.pk)
        return erro_json('Erro interno ao criar a ação.', 500)

    return JsonResponse({
        'success': True,
        'message': 'Ação criada com sucesso!',
        'codigo': nova_acao.codigo,
    }, status=201)


@login_required
def obter_detalhes_acao_view(request, acao_id):
    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    try:
        detalhes = AcaoService.obter_detalhes(prefeitura, acao_id)
    except ErroRegraNegocio as e:
        return erro_json(e.mensagem, e.status)

    detalhes['prioridades'] = list(Acao.Status_Prioridade.values)
    return JsonResponse({'success': True, **detalhes})


@login_required
@require_POST
def editar_acao_view(request, acao_id):
    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    try:
        data = json.loads(request.body)
    except (ValueError, TypeError):
        return erro_json('Dados inválidos.')

    try:
        acao_serializada = AcaoService.editar(prefeitura, acao_id, data, request.user)
    except ErroRegraNegocio as e:
        return erro_json(e.mensagem, e.status)

    return JsonResponse({'success': True, 'acao': acao_serializada})


@login_required
@require_POST
def excluir_acao_view(request, acao_id):
    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    try:
        AcaoService.excluir(prefeitura, acao_id)
    except ErroRegraNegocio as e:
        return erro_json(e.mensagem, e.status)

    return JsonResponse({'success': True, 'message': 'Ação excluída com sucesso!'})