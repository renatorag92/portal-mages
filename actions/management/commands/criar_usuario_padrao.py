from django.core.management import BaseCommand
from django.contrib.auth.models import User
from actions.models import PerfilUsuario

class Command(BaseCommand):
    help = 'Crea un perfil de usuario para cada usuario existente'

    def handle(self, *args, **options): 
        username_padrao = '11111' # Numero do contrato padrão
        senha_padrao = '12345678' # Senha padrão para os desenvolvedores
        
        # Cria ou pega o usuário se ele já existir
        user, created = User.objects.get_or_create(username=username_padrao, defaults={'is_staff': True, 'is_superuser': True}) # Permite acesso ao admin também
        
        if created:
            user.set_password(senha_padrao)
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Usuário "{username_padrao}" criado com sucesso.'))
            
        else:
            self.stdout.write(self.style.WARNING(f'Usuário "{username_padrao}" já existe.'))
            
        # Garante que o perfil do usuário seja criado e defina a flag primeiro_acesso como False
        perfil, _ = PerfilUsuario.objects.get_or_create(usuario=user)
        perfil.primeiro_acesso = False
        perfil.save()
        
        self.stdout.write(self.style.SUCCESS('Flag definida como False com sucesso'))
        
        