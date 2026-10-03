from django.shortcuts import redirect
from django.urls import reverse


class PrimeiroAcessoMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1. Verifica se o usuário está autenticado
        if request.user.is_authenticated:
            # 2. Verifica se ele possui o perfil cadastrado
            if hasattr(request.user, 'perfil'):
                # 3. Se for o primeiro acesso...
                if request.user.perfil.primeiro_acesso:
                    # Rotas liberadas para não criar um loop infinito
                    rota_redefinir_senha = reverse('redefinir-senha')
                    rotas_liberadas = {
                        rota_redefinir_senha,
                        reverse('logout'),        # logout do sistema
                        reverse('admin:logout'),  # logout do admin
                    }

                    # Qualquer outra página redireciona para a troca de senha
                    if request.path not in rotas_liberadas:
                        return redirect(rota_redefinir_senha)

        response = self.get_response(request)
        return response