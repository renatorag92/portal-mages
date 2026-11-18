from django.contrib.auth.decorators import login_required
from django.http import Http404, JsonResponse
from django.shortcuts import redirect
from django.views.decorators.http import require_POST

from ..context_processors import notifications as carregar_notificacoes
from ..services.autenticacao_service import AutenticacaoService
from ..services.notificacao_service import NotificacaoService


@login_required
@require_POST
def marcar_notificacao_lida_view(request, tipo, item_id):
    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    if prefeitura is None:
        return redirect('escolher_prefeitura')

    if tipo in {'acao', 'etapa'}:
        if not NotificacaoService.marcar_lida(request.user, prefeitura, tipo, item_id):
            raise Http404()
    return redirect('kanban')


@login_required
@require_POST
def marcar_solicitacao_senha_lida_view(request, solicitacao_id):
    if not request.user.e_consultor:
        return JsonResponse({'success': False}, status=403)
    return JsonResponse({
        'success': False,
        'error': 'A solicitação só é resolvida ao gerar uma nova senha.',
    }, status=409)


@login_required
@require_POST
def marcar_notificacao_nao_lida_view(request, tipo, item_id):
    if tipo == 'solicitacao_senha':
        if not request.user.e_consultor:
            return JsonResponse({'success': False}, status=403)
        return JsonResponse({
            'success': False,
            'error': 'A solicitação não pode ser marcada como não lida.',
        }, status=409)

    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    if prefeitura is None:
        return JsonResponse({'success': False}, status=400)

    resultado = NotificacaoService.marcar_nao_lida(request.user, prefeitura, tipo, item_id)
    if resultado is None:
        return JsonResponse({'success': False}, status=404)
    if resultado is False:
        raise Http404()
    return JsonResponse({'success': True})


@login_required
def atualizar_notificacoes_view(request):
    contexto = carregar_notificacoes(request)
    notificacoes = NotificacaoService.serializar_feed(contexto['notification_feed'])
    return JsonResponse({
        'notifications': notificacoes,
        'unread_count': contexto['notification_display_unread_count'],
        'total_count': contexto['notification_display_total_count'],
    })


@login_required
@require_POST
def remover_notificacao_view(request, tipo, item_id):
    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    if prefeitura is None:
        return JsonResponse({'success': False}, status=400)

    resultado = NotificacaoService.remover(request.user, prefeitura, tipo, item_id)
    if resultado is None:
        return JsonResponse({'success': False}, status=404)
    if resultado is False:
        raise Http404()

    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    return redirect('kanban')