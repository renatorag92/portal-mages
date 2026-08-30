from django.shortcuts import render, get_object_or_404, redirect
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

def atualizar_status_acao(request, acao_id):
    if request.method == 'POST':
        acao = get_object_or_404(Acao, id=acao_id)
        novo_status = request.POST.get('status')
        
        if novo_status:
            acao.status = novo_status
            acao.save()
            
    return redirect('acao_list')  # Redireciona para a lista de ações após a atualização