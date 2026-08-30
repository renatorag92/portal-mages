from django.db import models
from .choices import Status_status, Status_prioridade, Status_eixo

class Acao(models.Model):

    codigo = models.CharField(max_length=10)
    nome = models.CharField(max_length=100)
    eixo = models.CharField(max_length=100, choices=Status_eixo)
    prioridade = models.CharField(max_length=20, choices=Status_prioridade)
    responsavel = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20, choices=Status_status, default='planejado')            
    custo = models.DecimalField(max_digits=10, decimal_places=2)
    observacao = models.TextField(blank=True, null=True)
    
    class Meta:
        verbose_name_plural = 'Ações'
        
    # Retorna o nome da etapa quando for chamado o objeto
    def __str__(self):
        return f"{self.codigo} - {self.nome}" 

class Etapa(models.Model):
    
    acao = models.ForeignKey(Acao, on_delete=models.CASCADE, related_name='etapas')
    etapa = models.CharField(max_length=100)
    responsavel = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20, choices=Status_status, default='planejado')
    prioridade = models.CharField(max_length=20, choices=Status_prioridade)
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Etapas'

    # Retorna o codigo e o nome da ação quando for chamado o objetodef __str__(self):
    def __str__(self):
        return self.etapa



