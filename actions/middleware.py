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
                    # Define a rota de alteração de senha e de logout para não criar um loop infinito
                    rota_mudanca_senha = reverse('password-change') # Ajuste aqui!
                    rota_logout = reverse('admin:logout') # Ou a sua rota de logout personalizada

                    # Se ele tentar ir para qualquer outra página que não seja a de trocar senha ou deslogar, bloqueia!
                    if request.path != rota_mudanca_senha and request.path != rota_logout:
                        return redirect(rota_mudanca_senha)

        response = self.get_response(request)
        return response
