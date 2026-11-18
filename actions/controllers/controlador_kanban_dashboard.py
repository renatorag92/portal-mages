from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render

from ..models import Acao
from ..services.autenticacao_service import AutenticacaoService
from ..services.dashboard_service import DashboardService


@login_required
def kanban_view(request):
    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    if prefeitura is None:
        return redirect('escolher_prefeitura')

    context = DashboardService.montar_quadro_kanban(prefeitura)
    context['prioridades'] = Acao.Status_Prioridade.choices
    context['toast'] = request.session.pop('kanban_toast', None)
    return render(request, 'actions/kanban-governanca.html', context)


@login_required
def dashboard_view(request):
    prefeitura = AutenticacaoService.resolver_prefeitura_ativa(request.user, request.session)
    if prefeitura is None:
        return redirect('escolher_prefeitura')

    context = DashboardService.gerar_metricas(prefeitura)
    return render(request, 'actions/dashboard.html', context)