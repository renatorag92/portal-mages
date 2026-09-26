from django.db import models
from django.contrib.auth.models import User
from .choices import Status_status, Status_prioridade, Status_eixo

class Acao(models.Model):
    codigo = models.CharField(max_length=10, unique=True, blank=True, null=True)
    nome = models.CharField(max_length=100)
    acao = models.CharField(max_length=100, blank=True, null=True)
    nova_acao_texto = models.CharField(max_length=255, blank=True, null=True)
    eixo = models.CharField(max_length=100, choices=Status_eixo)
    prioridade = models.CharField(max_length=20, choices=Status_prioridade)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20, choices=Status_status, default='planejado')            
    custo = models.DecimalField(max_digits=10, decimal_places=2)
    observacoes = models.TextField(blank=True, null=True)
    prefeitura = models.ForeignKey('Prefeitura', on_delete=models.CASCADE, related_name='acoes')
    
    class Meta:
        verbose_name_plural = 'Ações'

    def save(self, *args, **kwargs):
        if not self.codigo:
            ultima_acao = Acao.objects.all().order_by('id').last()
            if ultima_acao and ultima_acao.codigo and ultima_acao.codigo.isdigit():
                self.codigo = str(int(ultima_acao.codigo) + 1)
            else:
                self.codigo = "1"
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.codigo} - {self.nome}"

class Etapa(models.Model):
    acao = models.ForeignKey(Acao, on_delete=models.CASCADE, related_name='etapas')
    etapa = models.CharField(max_length=100)
    responsavel_cpf = models.CharField(max_length=14, blank=True, null=True)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20, choices=Status_status, default='planejado')
    prioridade = models.CharField(max_length=20, choices=Status_prioridade)
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Etapas'

    def __str__(self):
        return self.etapa
    
class Prefeitura(models.Model):
    nome = models.CharField(max_length=100)
    sigla = models.CharField(max_length=10, blank=True, null=True)
    cidade = models.CharField(max_length=100)
        
    def __str__(self):
        return self.nome
        
class PerfilUsuario(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    primeiro_acesso = models.BooleanField(default=True)
    prefeitura = models.ForeignKey(Prefeitura, on_delete=models.CASCADE, related_name='usuarios', default=None, null=True, blank=True)
    cargo = models.CharField(max_length=100)
    
    def __str__(self):
        return f"{self.usuario.username} - {self.cargo}"