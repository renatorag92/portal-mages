from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LoginView, PasswordChangeView
from django.shortcuts import redirect, render
from django.urls import reverse_lazy
from django.views.decorators.http import require_POST

from ..forms import LoginCPFForm
from ..services.autenticacao_service import AutenticacaoService


class CustomLoginView(LoginView):
    template_name = 'actions/login.html'
    authentication_form = LoginCPFForm
    redirect_authenticated_user = True

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if 'data' in kwargs:
            data = kwargs['data'].copy()
            data['username'] = data.get('contrato', '')
            data['password'] = data.get('senha', '')
            kwargs['data'] = data
        return kwargs

    def form_invalid(self, form):
        self.request.session['login_erro'] = True
        self.request.session['login_contrato'] = self.request.POST.get('contrato', '')
        return redirect('login')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['erro_login'] = self.request.session.pop('login_erro', False)
        context['contrato_digitado'] = self.request.session.pop('login_contrato', '')
        context['solicitacao_senha_enviada'] = self.request.session.pop('solicitacao_senha_enviada', False)
        return context

    def get_success_url(self):
        if self.request.user.primeiro_acesso:
            return reverse_lazy('redefinir-senha')
        return reverse_lazy('kanban')


class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'actions/redefinir-senha.html'
    success_url = reverse_lazy('kanban')

    def form_valid(self, form):
        response = super().form_valid(form)
        AutenticacaoService.concluir_primeiro_acesso(self.request.user)
        return response


@login_required
def escolher_prefeitura_view(request):
    prefeituras = AutenticacaoService.listar_prefeituras_permitidas(request.user)
    if request.method == 'POST':
        escolhida = AutenticacaoService.selecionar_prefeitura_sessao(
            request.user, request.session, request.POST.get('prefeitura')
        )
        if escolhida:
            return redirect('kanban')
        messages.error(request, 'Selecione uma prefeitura da lista.')
    return render(request, 'actions/escolher-prefeitura.html', {'prefeituras': prefeituras})


@require_POST
def solicitar_redefinicao_senha_view(request):
    AutenticacaoService.registrar_solicitacao_redefinicao(request.POST.get('cpf', ''))
    request.session['solicitacao_senha_enviada'] = True
    return redirect('login')