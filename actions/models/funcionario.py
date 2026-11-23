import re

from django.apps import apps
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q


class Funcionario(AbstractUser):
    """
    Qualquer funcionário, da prefeitura ou da consultoria.
    - tem_acesso=False -> só existe para ser vinculado a ações/etapas (sem login).
    - tem_acesso=True + consultoria  -> consultor (opera todas as prefeituras da
      consultoria e acessa configuração/cadastro).
    - tem_acesso=True + prefeitura   -> usuário da prefeitura (opera só a sua).
    """
    # O login é o CPF: reaproveita o campo `username` do Django (coluna `cpf` no banco,
    # armazenado só com dígitos). Em código, acesse também por `funcionario.cpf`.
    cpf = models.CharField(
        'CPF', max_length=11, unique=True, db_column='cpf',
        error_messages={'unique': 'Já existe um funcionário com este CPF.'})

    # Usamos `nome` no lugar de first_name/last_name
    first_name = None
    last_name = None

    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, blank=True)
    endereco = models.CharField(max_length=150, blank=True)
    cargo = models.CharField(max_length=60, blank=True)  # texto livre (formulário sugere os já usados)

    # Pertence a UMA entidade: prefeitura OU consultoria
    prefeitura = models.ForeignKey(
        'actions.Prefeitura', on_delete=models.PROTECT, related_name='funcionarios',
        null=True, blank=True)
    consultoria = models.ForeignKey(
        'actions.Consultoria', on_delete=models.PROTECT, related_name='funcionarios',
        null=True, blank=True)

    tem_acesso = models.BooleanField(default=False)
    primeiro_acesso = models.BooleanField(default=True)

    REQUIRED_FIELDS = ['nome']          # pedido pelo createsuperuser (além do CPF)

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
        ordering = ['nome']
        constraints = [
            # No máximo uma entidade (o superusuário pode não ter nenhuma)
            models.CheckConstraint(
                condition=~Q(prefeitura__isnull=False, consultoria__isnull=False),
                name='funcionario_uma_entidade',
                violation_error_message='Informe a prefeitura OU a consultoria, não as duas.'),
        ]

    def __str__(self):
        return self.nome

    def get_full_name(self):
        return self.nome

    def get_short_name(self):
        return self.nome.split()[0] if self.nome else self.username

    @property
    def cpf(self):
        return self.username

    # --- papéis derivados (não há campo "perfil") ---------------------------
    @property
    def e_consultor(self):
        return self.tem_acesso and self.consultoria_id is not None

    def prefeituras_permitidas(self):
        """Prefeituras que este usuário pode operar."""
        Prefeitura = apps.get_model('actions', 'Prefeitura')
        if self.e_consultor:
            return Prefeitura.objects.filter(consultoria_id=self.consultoria_id)
        if self.tem_acesso and self.prefeitura_id:
            return Prefeitura.objects.filter(pk=self.prefeitura_id)
        return Prefeitura.objects.none()

    # --- validação e persistência ------------------------------------------
    def clean(self):
        super().clean()
        self.username = re.sub(r'\D', '', self.username or '')
        if len(self.username) != 11:
            raise ValidationError({'username': 'Informe um CPF com 11 dígitos.'})
        if self.prefeitura_id and self.consultoria_id:
            raise ValidationError('Informe a prefeitura OU a consultoria, não as duas.')
        if not (self.prefeitura_id or self.consultoria_id) and not self.is_superuser:
            raise ValidationError('Informe a prefeitura ou a consultoria do funcionário.')

    def save(self, *args, **kwargs):
        self.username = re.sub(r'\D', '', self.username or '')
        if self.is_superuser:
            self.tem_acesso = True                # superusuário sempre pode logar
        self.is_staff = self.is_superuser or self.e_consultor   # só consultor entra no /admin
        if not self.tem_acesso:
            self.set_unusable_password()          # sem acesso = sem senha utilizável
        super().save(*args, **kwargs)