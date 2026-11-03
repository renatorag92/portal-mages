# actions/management/commands/criar_usuario_padrao.py
from django.core.management.base import BaseCommand

from actions.models import Consultoria, Funcionario, Prefeitura

SENHA_TESTE = 'senha123'


class Command(BaseCommand):
    help = 'Cria consultoria, prefeitura, um consultor e um secretário para testes.'

    def handle(self, *args, **options):
        consultoria, _ = Consultoria.objects.get_or_create(
            cnpj='00000000000100',
            defaults={
                'nome_juridico': 'Consultoria Teste LTDA',
                'nome_fantasia': 'Consultoria Teste',
                'endereco': 'Rua Teste, 100',
            },
        )

        prefeitura, _ = Prefeitura.objects.get_or_create(
            cnpj='00000000000191',
            defaults={
                'nome_juridico': 'Prefeitura Municipal de Teste',
                'nome_fantasia': 'Prefeitura Teste',
                'endereco': 'Praça Central, 1',
                'consultoria': consultoria,
            },
        )

        consultor, criado = Funcionario.objects.get_or_create(
            username='12345678909',
            defaults={
                'nome': 'Consultor Teste',
                'consultoria': consultoria,
                'tem_acesso': True,
                'primeiro_acesso': False,
            },
        )
        if criado:
            consultor.set_password(SENHA_TESTE)
            consultor.save()

        secretario, criado = Funcionario.objects.get_or_create(
            username='98765432100',
            defaults={
                'nome': 'Secretário Teste',
                'prefeitura': prefeitura,
                'cargo': 'Secretário',
                'tem_acesso': True,
                'primeiro_acesso': False,
            },
        )
        if criado:
            secretario.set_password(SENHA_TESTE)
            secretario.save()

        self.stdout.write(self.style.SUCCESS(
            f'Pronto. Logins: CPF 12345678909 (consultor) e CPF 98765432100 (secretário). '
            f'Senha: {SENHA_TESTE}'
        ))