from django.db import models

class Acao(models.Model):

    class Status(models.TextChoices):
        PLANEJADO = 'planejado', 'Planejado'
        EM_PREPARACAO = 'em_preparacao', 'Em preparação'
        EM_EXECUCAO = 'em_execucao', 'Em execução'
        EM_VALIDACAO = 'em_validacao', 'Em validação'
        CONCLUIDO = 'concluido', 'Concluído'
        CANCELADO = 'cancelado', 'Cancelado'

    codigo = models.CharField(max_length=10)
    nome = models.CharField(max_length=100)
    eixo = models.CharField(max_length=100)
    prioridade = models.CharField(max_length=20, choices=Status,)
    responsavel = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20, choices=Status, default='planejado')            
    custo = models.DecimalField(max_digits=10, decimal_places=2)
    observacao = models.TextField(blank=True, null=True)

class Etapa(models.Model):

    class Status(models.TextChoices):
        BAIXA = 'baixa', 'Baixa'
        MEDIA = 'media', 'Média'
        ALTA = 'alta', 'Alta'

    acao = models.ForeignKey(Acao, on_delete=models.CASCADE, related_name='etapas')
    etapa = models.CharField(max_length=100)
    responsavel = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20, choices=Status, default='planejado')
    prioridade = models.CharField(max_length=20, choices=Status, default='')
    observacao = models.TextField(blank=True, null=True)

# Retorna o codigo e o nome da ação quando for chamado o objeto
def __str__(self):
    return self.codigo + ' - ' + self.nome
# Retorna o nome da etapa quando for chamado o objeto
def __str__(self):
    return self.etapa


