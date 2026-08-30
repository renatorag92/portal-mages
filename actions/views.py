from django.shortcuts import render
from .models import Acao
from .choices import Status_status

def acao_list_view(request):
    
    acoes_por_status = {
        'planejado': Acao.objects.filter(status=Status_status.PLANEJADO),
        'em_preparacao': Acao.objects.filter(status=Status_status.EM_PREPARACAO),
        'em_execucao': Acao.objects.filter(status=Status_status.EM_EXECUCAO),
        'em_validacao': Acao.objects.filter(status=Status_status.EM_VALIDACAO),
        'concluido': Acao.objects.filter(status=Status_status.CONCLUIDO),
        'cancelado': Acao.objects.filter(status=Status_status.CANCELADO)
    }
    return render(request, 'actions/acao_list.html', {'kanban': acoes_por_status})
