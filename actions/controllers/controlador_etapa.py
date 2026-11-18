import json

from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_POST

from ..services.autenticacao_service import AutenticacaoService
from ..services.etapa_service import EtapaService
from ..services.excecoes import ErroRegraNegocio
from ._base import erro_json


@login_required
@require_POST
def adicionar_etapa_view(request, acao_id):
    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            return erro_json('Dados inválidos.')
    except (ValueError, TypeError):
        return erro_json('Dados inválidos.')

    try:
        etapa_serializada = EtapaService.adicionar(prefeitura, acao_id, data, request.user)
    except ErroRegraNegocio as e:
        return erro_json(e.mensagem, e.status)

    return JsonResponse({'success': True, 'etapa': etapa_serializada}, status=201)


@login_required
@require_POST
def editar_etapa_view(request, etapa_id):
    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            return erro_json('Dados inválidos.')
    except (ValueError, TypeError):
        return erro_json('Dados inválidos.')

    try:
        etapa_serializada = EtapaService.editar(prefeitura, etapa_id, data, request.user)
    except ErroRegraNegocio as e:
        return erro_json(e.mensagem, e.status)

    return JsonResponse({'success': True, 'etapa': etapa_serializada})


@login_required
@require_POST
def alterar_etapa_view(request, etapa_id):
    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    try:
        concluida = EtapaService.alternar_conclusao(prefeitura, etapa_id, request.user)
    except ErroRegraNegocio as e:
        return erro_json(e.mensagem, e.status)

    return JsonResponse({'success': True, 'concluida': concluida})


@login_required
@require_POST
def excluir_etapa_view(request, etapa_id):
    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    try:
        EtapaService.excluir(prefeitura, etapa_id)
    except ErroRegraNegocio as e:
        return erro_json(e.mensagem, e.status)

    return JsonResponse({'success': True, 'message': 'Etapa excluída com sucesso!'})