from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import F, Max, Q


class Acao(models.Model):
    class Status_Prioridade(models.TextChoices):
        alta = 'Alta'
        media = 'Média'
        baixa = 'Baixa'

    # Isolamento por município
    prefeitura = models.ForeignKey('actions.Prefeitura', on_delete=models.PROTECT, related_name='acoes')

    # Número sequencial dentro da prefeitura (1, 2, 3...), gerado automaticamente
    id = models.AutoField(primary_key=True)
    # Sempre preenchidos: se escolheu do catálogo, são copiados do modelo
    nome = models.CharField(max_length=255)
    eixo = models.ForeignKey('actions.Eixo', on_delete=models.PROTECT, related_name='acoes')
    modelo = models.ForeignKey(
        'actions.AcaoCatalogo', on_delete=models.PROTECT, null=True, blank=True,
        related_name='instancias')   # origem: catálogo (None = criada pelo município)

    prioridade = models.CharField(
        max_length=20, choices=Status_Prioridade.choices, default='')
    data_inicio = models.DateField()
    data_fim = models.DateField()
    arrecadacao_estimada = models.DecimalField(max_digits=14, decimal_places=2)
    observacoes = models.TextField(blank=True, null=True)

    status = models.ForeignKey('actions.Status', on_delete=models.PROTECT, related_name='acoes')

    # Funcionário da prefeitura responsável pela ação
    responsavel = models.ForeignKey(
        'actions.Funcionario', on_delete=models.PROTECT, related_name='acoes')

    # Auditoria (consultor e usuário da prefeitura editam os mesmos dados)
    criado_em = models.DateTimeField(auto_now_add=True)
    atualizado_em = models.DateTimeField(auto_now=True)
    criado_por = models.ForeignKey(
        'actions.Funcionario', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', editable=False)
    atualizado_por = models.ForeignKey(
        'actions.Funcionario', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='+', editable=False)

    class Meta:
        verbose_name = 'Ação'
        verbose_name_plural = 'Ações'
        ordering = ['prefeitura', 'id']
        constraints = [
            models.UniqueConstraint(
                fields=['prefeitura', 'id'], name='acao_id_unico_por_prefeitura'),
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
        if not self.id:
            ultimo = Acao.objects.filter(prefeitura_id=self.prefeitura_id) \
                .aggregate(m=Max('id'))['m']
            self.id = (ultimo or 0) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.id} - {self.nome}"