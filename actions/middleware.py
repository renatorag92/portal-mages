from django.shortcuts import redirect
from django.urls import reverse


class PrimeiroAcessoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if request.user.is_authenticated and request.user.primeiro_acesso:
            rota_redefinir_senha = reverse('redefinir-senha')
            rotas_liberadas = {
                rota_redefinir_senha,
                reverse('logout'),
                reverse('admin:logout'),
            }
            if request.path not in rotas_liberadas:
                return redirect(rota_redefinir_senha)

        response = self.get_response(request)
        return response