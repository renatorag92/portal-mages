from django.db import models

STATUS_CHOICES = [
    ('planejado', 'Planejado'),
    ('em_preparacao', 'Em preparação'),
    ('em_execucao', 'Em execução'),
    ('em_validacao', 'Em validação'),
    ('concluido', 'Concluído'),
    ('cancelado', 'Cancelado'),
    ('alta', 'Alta'),
    ('media', 'Média'),
    ('baixa', 'Baixa'),]

class Acao(models.Model):
    codigo = models.CharField(max_length=10)
    nome = models.CharField(max_length=100)
    eixo = models.CharField(max_length=100)
    prioridade = models.CharField(max_length=20, choices=STATUS_CHOICES,)
    responsavel = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planejado')            
    custo = models.DecimalField(max_digits=10, decimal_places=2)
    observacao = models.TextField(blank=True, null=True)

class Etapa(models.Model):
    acao = models.ForeignKey(Acao, on_delete=models.CASCADE, related_name='etapas')
    etapa = models.CharField(max_length=100)
    responsavel = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='planejado')
    prioridade = models.IntegerField()
    observacao = models.TextField(blank=True, null=True)

# Retorna o nome da ação quando for chamado o objeto
def __str__(self):
    return self.nome
# Retorna o nome da etapa quando for chamado o objeto
def __str__(self):
    return self.etapa


