from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator

# Entidades base (Prefeitura e Consultoria)
class Prefeitura(models.Model):
    cnpj = models.CharField(max_length=14, unique=True)
    nome_juridico = models.CharField(max_length=45) # ex.: Prefeitura Municipal de Nova Cruz
    nome_fantasia = models.CharField(max_length=45)
    endereco = models.CharField(max_length=45)

    class Meta:
        verbose_name = "Prefeitura"
        verbose_name_plural = "Prefeitura"  # Deixa o nome "prefeitura" no singular

    def __str__(self):
        return self.nome_fantasia

class Consultoria(models.Model):
    cnpj = models.CharField(max_length=14, unique=True) 
    nome_juridico = models.CharField(max_length=45)
    nome_fantasia = models.CharField(max_length=45)
    endereco = models.CharField(max_length=45)

    # Relação 1:1 com a Prefeitura
    prefeitura = models.OneToOneField(Prefeitura, on_delete=models.CASCADE, related_name='consultoria')

    class Meta:
        verbose_name = 'Consultoria'
        verbose_name_plural = 'Consultoria'

    def __str__(self): 
        return self.nome_fantasia

class Funcionario(models.Model):
    prefeitura = models.ForeignKey(Prefeitura, on_delete=models.PROTECT, related_name='secretarios', default=None, null=True, blank=True)
    cpf = models.CharField(max_length=14, unique=True)
    nome = models.CharField(max_length=45)
    email = models.EmailField(max_length=45)
    telefone = models.CharField(max_length=45)
    endereco = models.CharField(max_length=45)
    cargo = models.CharField(max_length=45)

    class Meta:
        verbose_name = 'Funcionário'
        verbose_name_plural = 'Funcionários'
    
    def __str__(self):
        return self.nome

class Secretario(Funcionario):
    senha = models.CharField(max_length=128, blank=True, null=False)

    class Meta:
        verbose_name = 'Secretário'
        verbose_name_plural = 'Secretários'

    def __str__(self):
        return self.nome

class Eixo(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=45)
    descricao = models.CharField(max_length=45, blank=True, null=True)

    def __str__(self):
        return self.nome

class Status(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=45)
    cor = models.CharField(
        max_length=7,
        default='#3b3b8c',
        validators=[RegexValidator(r'^#[0-9A-Fa-f]{6}$', 'Informe uma cor hexadecimal no formato #RRGGBB.')],
    )
    cor_nome = models.CharField(max_length=45, blank=True)
    ordem = models.IntegerField(default=0)

    class Meta:
        verbose_name = 'Status'
        verbose_name_plural = 'Status'

    def __str__(self):
        return self.nome

# Tabela de Catálogo de Ações padronizada
class AcaoCatalogo(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=100)
    eixo = models.ForeignKey(Eixo, on_delete=models.PROTECT, related_name='acoes')

    class Meta:
        verbose_name = 'Ação do Catálogo'
        verbose_name_plural = 'Catálogo de Ações'

        def __str__(self):
            return f"{self.eixo.nome} - {self.nome}"

# Núcleo do sistema (Açõe e Etapas)
class Acao(models.Model):
    class Status_Prioridade(models.TextChoices):
        alta = 'Alta'
        media = 'Média'
        baixa = 'Baixa'

    codigo = models.CharField(primary_key=True)

    # Ação selecionada do Catálogo
    acao_catalogo = models.ForeignKey(
        AcaoCatalogo,
        on_delete=models.PROTECT,
        related_name='instancias', null=True, blank=True)

    # Ação digitada pelo usuário
    nova_acao_texto = models.CharField(max_length=45, blank=True, null=True)
    
    prioridade = models.CharField(max_length=20, choices=Status_Prioridade, default='')
    data_inicio = models.DateField()
    data_fim = models.DateField()
    custo = models.FloatField()
    observacoes = models.CharField(blank=True, null=True)

    # Chaves estrangeiras do DER
    status = models.ForeignKey(Status, on_delete=models.PROTECT, related_name='acoes')

    # Secretário Responsavel (FK apontando para Funcionario)
    secretario = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        related_name='acoes',
        db_column='Funcionario_Secretario_CPF'
        )
    
    class Meta:
        verbose_name_plural = 'Ações'

    def save(self, *args, **kwargs):
        if not self.codigo:
            codigos = [int(c) for c in Acao.objects.values_list('codigo', flat=True) if str(c).isdigit()]
            self.codigo = str(max(codigos) + 1) if codigos else "1"
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.codigo} - {self.acao_catalogo.nome}"

class Etapa(models.Model):   
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=45)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    observacoes = models.TextField(blank=True, null=True)
    prioridade = models.CharField(max_length=20, choices=Acao.Status_Prioridade.choices, blank=True, default='')
    concluida = models.BooleanField(default=False)

    # Chaves estrangeiras
    acao = models.ForeignKey(
        Acao,
        on_delete=models.PROTECT,
        related_name='etapas',
        db_column='Acao_Codigo'
        )

    # Funcionário Responsável pela execução da etapa
    responsavel = models.ForeignKey(
        Funcionario,
        on_delete=models.PROTECT,
        related_name='etapas_responsaveis',
        db_column='Funcionario_Responsavel_CPF')

    class Meta:
        verbose_name_plural = 'Etapas'
        
    def __str__(self):
        return f"{self.id} - {self.nome}"
    
class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    primeiro_acesso = models.BooleanField(default=True)
    prefeitura = models.ForeignKey(Prefeitura, on_delete=models.CASCADE, related_name='usuarios', default=None, null=True, blank=True)
    cargo = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.cargo}"