from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator
from django.db.models.signals import post_save
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy # Importa o modelo de usuário do Django
from django.dispatch import receiver # Importa o sinal para criar o perfil do usuário automaticamente
from django.db import models

# Entidades base (Prefeitura e Consultoria)
class Prefeitura(models.Model):
    cnpj = models.CharField(max_length=14, unique=True)
    nome_juridico = models.CharField(max_length=45) # ex.: Prefeitura Municipal de Nova Cruz
    nome_fantasia = models.CharField(max_length=45)
    endereco = models.CharField(max_length=45)
        
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
        verbose_name_plural = 'Consultorias'

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
            ultima_acao = Acao.objects.all().order_by('codigo').last()
            if ultima_acao and ultima_acao.codigo and ultima_acao.codigo.isdigit():
                self.codigo = str(int(ultima_acao.codigo) + 1)
            else:
                self.codigo = "1"
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.codigo} - {self.acao_catalogo.nome}"

class Etapa(models.Model):   
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=45)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    observacoes = models.TextField(blank=True, null=True)

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
        
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'actions/password-change.html'
    success_url = reverse_lazy('kanban') # Redireciona para a página do Kanban após a alteração da senha
    def form_valid(self, form):
        response = super().form_valid(form) # Chama o método form_valid da classe pai para processar a alteração da senha
       
        # Atualiza o campo primeiro_acesso para False após a alteração da senha
        self.request.user.perfil.primeiro_acesso = False
        self.request.user.perfil.save()
        
        return response

        
        
        


