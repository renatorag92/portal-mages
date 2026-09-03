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
<<<<<<< Updated upstream
    return render(request, 'actions/acao_list.html', {'kanban': acoes_por_status})
=======
    return render(request, 'actions/kanban-governanca.html', {'kanban': acoes_por_status})
# 
# def acao_list_view(request):
    
#     acoes_por_status = {
#         'planejado': Acao.objects.filter(status=Status_status.PLANEJADO),
#         'em_preparacao': Acao.objects.filter(status=Status_status.EM_PREPARACAO),
#         'em_execucao': Acao.objects.filter(status=Status_status.EM_EXECUCAO),
#         'em_validacao': Acao.objects.filter(status=Status_status.EM_VALIDACAO),
#         'concluido': Acao.objects.filter(status=Status_status.CONCLUIDO),
#         'cancelado': Acao.objects.filter(status=Status_status.CANCELADO)
#     }
#     return render(request, 'actions/kanban.html', {'kanban': acoes_por_status})
>>>>>>> Stashed changes

def atualizar_status_acao(request, acao_id):
    if request.method == 'POST':
        acao = get_object_or_404(Acao, id=acao_id)
        novo_status = request.POST.get('status')
        
        if novo_status:
            acao.status = novo_status
            acao.save()
            
    return redirect('acao_list')  # Redireciona para a lista de ações após a atualização