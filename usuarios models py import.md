# usuarios/models.py
import string
import random
from django.contrib.auth.models import AbstractUser
from django.db import models

class Funcionario(AbstractUser):
    """
    TABELA ÚNICA NO BANCO DE DADOS.
    Ela substitui as antigas tabelas Usuario, Funcionario e Secretario.
    Herda os poderes de login do AbstractUser, mas mantém a identidade de Funcionário.
    """
    # Atributos de negócio que você já usava:
    prefeitura = models.ForeignKey('Prefeitura', on_delete=models.CASCADE, related_name='funcionarios')
    cpf = models.CharField(max_length=14, unique=True)
    telefone = models.CharField(max_length=45, blank=True)
    endereco = models.CharField(max_length=45, blank=True)
    cargo = models.CharField(max_length=100) # Ex: Secretário de Saúde, Operador, Motorista
    
    # Controle de segurança para redefinição de senha:
    primeiro_acesso = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'

    def __str__(self):
        # get_full_name() junta o first_name e last_name que vêm do AbstractUser
        return f"{self.get_full_name() or self.username} ({self.cargo}) - {self.prefeitura.nome_fantasia}"

    def save(self, *args, **kwargs):
        """Gera senha automática para quem tem acesso e desativa quem não tem."""
        is_new = self._state.adding

        if is_new:
            # Se o funcionário foi marcado para ter acesso (is_active=True) e está sem senha
            if self.is_active and not self.password:
                caracteres = string.ascii_letters + string.digits + "!@#$%*"
                senha_temporaria = ''.join(random.choice(caracteres) for _ in range(12))
                self.set_password(senha_temporaria)
                self.primeiro_acesso = True
                # Guarda temporariamente para exibir no painel admin
                self._senha_temporaria = senha_temporaria
                
            # Se for cadastrado SEM acesso ao sistema (is_active=False)
            elif not self.is_active:
                self.set_unusable_password() # Define uma senha inválida por segurança
                self.primeiro_acesso = False

        super().save(*args, **kwargs)

