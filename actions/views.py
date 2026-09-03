from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from .models import Acao
from .choices import Status_status

@login_required
def kanban_view(request):
    prefeitura_do_usuario = request.user.perfil.prefeitura
    
    acoes_por_status = {
        'planejado': Acao.objects.filter(status=Status_status.PLANEJADO, prefeitura=prefeitura_do_usuario),
        'preparacao': Acao.objects.filter(status=Status_status.EM_PREPARACAO, prefeitura=prefeitura_do_usuario),
        'execucao': Acao.objects.filter(status=Status_status.EM_EXECUCAO, prefeitura=prefeitura_do_usuario),
        'validacao': Acao.objects.filter(status=Status_status.EM_VALIDACAO, prefeitura=prefeitura_do_usuario),
        'concluido': Acao.objects.filter(status=Status_status.CONCLUIDO, prefeitura=prefeitura_do_usuario),
        'cancelado': Acao.objects.filter(status=Status_status.CANCELADO, prefeitura=prefeitura_do_usuario)
    }
    return render(request, 'actions/kanban-governanca.html', {'kanban': acoes_por_status})

def atualizar_status_acao(request, acao_id):
    if request.method == 'POST':
        acao = get_object_or_404(Acao, id=acao_id)
        novo_status = request.POST.get('status')
        
        if novo_status:
            acao.status = novo_status
            acao.save()
            
    return redirect('kanban')  # Redireciona para a lista de ações após a atualização