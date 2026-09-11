from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth import authenticate, login
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.urls import reverse_lazy
from django.contrib import messages
from .models import Acao
# Importando explicitamente as classes do seu choices.py
from .choices import Status_status, Status_eixo, Status_prioridade

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

@login_required
def cadastro_acoes_view(request):
    context = {
        # Chamando .choices diretamente da classe TextChoices
        'eixos': Status_eixo.choices,
        'prioridades': Status_prioridade.choices,
    }
    return render(request, 'actions/cadastro-de-acoes.html', context)

def atualizar_status_acao(request, acao_id):
    if request.method == 'POST':
        acao = get_object_or_404(Acao, id=acao_id)
        novo_status = request.POST.get('status')
        
        if novo_status:
            acao.status = novo_status
            acao.save()
            
    return redirect('kanban')

class CustomLoginView(LoginView):
    template_name = 'actions/login.html'
    redirect_authenticated_user = True
    
    def get_success_url(self):
        user = self.request.user
        if hasattr(user, 'perfilusuario') and user.perfilusuario.primeiro_acesso:
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