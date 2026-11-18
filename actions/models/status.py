from django.core.validators import RegexValidator
from django.db import models


class Status(models.Model):

    class Chave(models.TextChoices):
        PLANEJADO = 'PLANEJADO', 'Planejado'
        PREPARACAO = 'PREPARACAO', 'Preparação'
        EM_EXECUCAO = 'EM_EXECUCAO', 'Em execução'
        EM_VALIDACAO = 'EM_VALIDACAO', 'Em validação'
        CONCLUIDO = 'CONCLUIDO', 'Concluído'
        SUSPENSO = 'SUSPENSO', 'Suspenso'
        CANCELADO = 'CANCELADO', 'Cancelado'

    # Grupos de regra, definidos junto da chave
    ATIVAS = (Chave.PLANEJADO, Chave.PREPARACAO, Chave.EM_EXECUCAO, Chave.EM_VALIDACAO)
    ENCERRADAS = (Chave.CONCLUIDO, Chave.CANCELADO)

    id = models.AutoField(primary_key=True)
    chave = models.CharField(max_length=20, unique=True, editable=False)
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