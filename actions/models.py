import re

from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.validators import RegexValidator
from django.db import models
from django.db.models import F, Max, Q

# ---------------------------------------------------------------------------
# Entidades base (Consultoria e Prefeitura)
# ---------------------------------------------------------------------------
class Consultoria(models.Model):
    cnpj = models.CharField(max_length=14, unique=True)
    nome_juridico = models.CharField(max_length=100)
    nome_fantasia = models.CharField(max_length=100)
    endereco = models.CharField(max_length=150)

    class Meta:
        verbose_name = 'Consultoria'
        verbose_name_plural = 'Consultoria'

    def __str__(self):
        return self.nome_fantasia


class Prefeitura(models.Model):
    cnpj = models.CharField(max_length=14, unique=True)
    nome_juridico = models.CharField(max_length=100)   # ex.: Prefeitura Municipal de Nova Cruz
    nome_fantasia = models.CharField(max_length=100)
    endereco = models.CharField(max_length=150)

    # Relação 1:1 com a Consultoria (anulável: a prefeitura pode existir antes do vínculo)
    consultoria = models.OneToOneField(
        Consultoria, on_delete=models.PROTECT, related_name='prefeitura',
        null=True, blank=True)

    class Meta:
        verbose_name = 'Prefeitura'
        verbose_name_plural = 'Prefeitura'  # mantém "Prefeitura" no singular no admin

    def __str__(self):
        return self.nome_fantasia


# ---------------------------------------------------------------------------
# Funcionário (único modelo de usuário do sistema)
# ---------------------------------------------------------------------------
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
    username = models.CharField(
        'CPF', max_length=11, unique=True, db_column='cpf',
        error_messages={'unique': 'Já existe um funcionário com este CPF.'})

    # Usamos `nome` no lugar de first_name/last_name
    first_name = None
    last_name = None

    nome = models.CharField(max_length=100)
    telefone = models.CharField(max_length=20, blank=True)
    endereco = models.CharField(max_length=150, blank=True)
    cargo = models.CharField(max_length=60, blank=True)  # texto livre (formulário sugere os já usados)
    foto = models.ImageField(upload_to='profile_photos/', blank=True)

    # Pertence a UMA entidade: prefeitura OU consultoria
    prefeitura = models.ForeignKey(
        Prefeitura, on_delete=models.PROTECT, related_name='funcionarios',
        null=True, blank=True)
    consultoria = models.ForeignKey(
        Consultoria, on_delete=models.PROTECT, related_name='funcionarios',
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


# ---------------------------------------------------------------------------
# Tabelas de apoio (globais, cadastradas pela consultoria)
# ---------------------------------------------------------------------------
class Eixo(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=45, unique=True)
    pai = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True,
        related_name='subeixos')

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()
        if self.pai_id is None:
            return
        if self.pai_id == self.pk:
            raise ValidationError({'pai': 'Um eixo não pode ser subeixo de si mesmo.'})
        if self.pai.pai_id is not None:
            raise ValidationError({'pai': 'Só é permitido um nível de subeixo.'})
        if self.pk and self.subeixos.exists():
            raise ValidationError({'pai': 'Este eixo tem subeixos, então não pode ser subeixo.'})

class Status(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=45)
    cor = models.CharField(
        max_length=7,
        default='#3b3b8c',
        validators=[RegexValidator(
            r'^#[0-9A-Fa-f]{6}$', 'Informe uma cor hexadecimal no formato #RRGGBB.')],
    )
    cor_nome = models.CharField(max_length=45, blank=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Status'
        verbose_name_plural = 'Status'
        ordering = ['ordem']

    def __str__(self):
        return self.nome


class AcaoCatalogo(models.Model):
    """Banco de Ações Estratégicas: modelos globais que o município pode escolher."""
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255, unique=True)
    eixo = models.ForeignKey(Eixo, on_delete=models.PROTECT, related_name='modelos')
    ativa = models.BooleanField(default=True)   # esconde da lista sem apagar

    class Meta:
        verbose_name = 'Ação do Catálogo'
        verbose_name_plural = 'Catálogo de Ações'
        ordering = ['eixo', 'nome']

    def __str__(self):
        return f"{self.eixo.nome} - {self.nome}"


# ---------------------------------------------------------------------------
# Núcleo do sistema (Ações e Etapas)
# ---------------------------------------------------------------------------
class Acao(models.Model):
    class Status_Prioridade(models.TextChoices):
        alta = 'Alta'
        media = 'Média'
        baixa = 'Baixa'

    # Isolamento por município
    prefeitura = models.ForeignKey(Prefeitura, on_delete=models.PROTECT, related_name='acoes')

    # Número sequencial dentro da prefeitura (1, 2, 3...), gerado automaticamente
    codigo = models.PositiveIntegerField(editable=False)

    # Sempre preenchidos: se escolheu do catálogo, são copiados do modelo
    nome = models.CharField(max_length=255)
    eixo = models.ForeignKey(Eixo, on_delete=models.PROTECT, related_name='acoes')
    modelo = models.ForeignKey(
        AcaoCatalogo, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='instancias')   # origem: catálogo (None = criada pelo município)

    prioridade = models.CharField(
        max_length=20, choices=Status_Prioridade.choices, default='')
    data_inicio = models.DateField()
    data_fim = models.DateField()
    custo = models.FloatField()
    observacoes = models.TextField(blank=True, null=True)

    status = models.ForeignKey(Status, on_delete=models.PROTECT, related_name='acoes')

    # Funcionário da prefeitura responsável pela ação
    responsavel = models.ForeignKey(
        Funcionario, on_delete=models.PROTECT, related_name='acoes')

    # Auditoria (consultor e usuário da prefeitura editam os mesmos dados)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(
        Funcionario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', editable=False)
    atualizado_por = models.ForeignKey(
        Funcionario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', editable=False)

    class Meta:
        verbose_name = 'Ação'
        verbose_name_plural = 'Ações'
        ordering = ['prefeitura', 'codigo']
        constraints = [
            models.UniqueConstraint(
                fields=['prefeitura', 'codigo'], name='acao_codigo_unico_por_prefeitura'),
            models.CheckConstraint(
                condition=Q(data_fim__gte=F('data_inicio')),
                name='acao_data_fim_apos_inicio',
                violation_error_message='A data de fim deve ser igual ou posterior à de início.'),
        ]

    def _aplicar_modelo(self):
        """Copia nome e eixo do catálogo quando a ação vem de um modelo."""
        if self.modelo_id:
            if not self.nome:
                self.nome = self.modelo.nome
            if not self.eixo_id:
                self.eixo_id = self.modelo.eixo_id

    def clean(self):
        super().clean()
        self._aplicar_modelo()
        if (self.responsavel_id and self.prefeitura_id
                and self.responsavel.prefeitura_id != self.prefeitura_id):
            raise ValidationError(
                {'responsavel': 'O responsável deve ser funcionário da mesma prefeitura da ação.'})

    def save(self, *args, **kwargs):
        self._aplicar_modelo()
        if not self.codigo:
            ultimo = Acao.objects.filter(prefeitura_id=self.prefeitura_id) \
                .aggregate(m=Max('codigo'))['m']
            self.codigo = (ultimo or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nome}"


class Etapa(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=45)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    observacoes = models.TextField(blank=True, null=True)
    prioridade = models.CharField(
        max_length=20, choices=Acao.Status_Prioridade.choices, blank=True, default='')
    concluida = models.BooleanField(default=False)

    acao = models.ForeignKey(Acao, on_delete=models.PROTECT, related_name='etapas')

    # Funcionário responsável pela execução da etapa
    responsavel = models.ForeignKey(
        Funcionario, on_delete=models.PROTECT, related_name='etapas_responsaveis')

    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(
        Funcionario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', editable=False)
    atualizado_por = models.ForeignKey(
        Funcionario, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', editable=False)

    class Meta:
        verbose_name = 'Etapa'
        verbose_name_plural = 'Etapas'
        ordering = ['data_inicio']
        constraints = [
            models.CheckConstraint(
                condition=Q(data_fim__gte=F('data_inicio')),
                name='etapa_data_fim_apos_inicio',
                violation_error_message='A data de fim deve ser igual ou posterior à de início.'),
        ]

    def clean(self):
        super().clean()
        if (self.responsavel_id and self.acao_id
                and self.responsavel.prefeitura_id != self.acao.prefeitura_id):
            raise ValidationError(
                {'responsavel': 'O responsável deve ser funcionário da mesma prefeitura da ação.'})

    def __str__(self):
        return f"{self.id} - {self.nome}"


class NotificacaoLida(models.Model):
    usuario = models.ForeignKey(
        Funcionario, on_delete=models.CASCADE, related_name='notificacoes_lidas',
    )
    acao = models.ForeignKey(
        Acao, on_delete=models.CASCADE, null=True, blank=True,
        related_name='leituras_notificacao',
    )
    etapa = models.ForeignKey(
        Etapa, on_delete=models.CASCADE, null=True, blank=True,
        related_name='leituras_notificacao',
    )
    lida_em = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(acao__isnull=False, etapa__isnull=True)
                    | Q(acao__isnull=True, etapa__isnull=False)
                ),
                name='notificacao_lida_acao_ou_etapa',
            ),
            models.UniqueConstraint(
                fields=['usuario', 'acao'],
                condition=Q(acao__isnull=False),
                name='notificacao_lida_usuario_acao_unica',
            ),
            models.UniqueConstraint(
                fields=['usuario', 'etapa'],
                condition=Q(etapa__isnull=False),
                name='notificacao_lida_usuario_etapa_unica',
            ),
        ]