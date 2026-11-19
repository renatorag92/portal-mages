from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Q

from .acao import Acao


class Etapa(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=45)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    observacoes = models.TextField(blank=True, null=True)
    prioridade = models.CharField(
        max_length=20, choices=Acao.Status_Prioridade.choices, blank=True, default='')
    concluida = models.BooleanField(default=False)

    acao = models.ForeignKey('actions.Acao', on_delete=models.PROTECT, related_name='etapas')

    # Funcionário responsável pela execução da etapa
    responsavel = models.ForeignKey(
        'actions.Funcionario', on_delete=models.PROTECT, related_name='etapas_responsaveis')

    # Auditoria
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(
        'actions.Funcionario', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', editable=False)
    atualizado_por = models.ForeignKey(
        'actions.Funcionario', on_delete=models.SET_NULL, null=True, blank=True,
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