from django.db import models


class AcaoCatalogo(models.Model):
    """Banco de Ações Estratégicas: modelos globais que o município pode escolher."""
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=255, unique=True)
    eixo = models.ForeignKey('actions.Eixo', on_delete=models.PROTECT, related_name='modelos')

    class Meta:
        verbose_name = 'Ação do Catálogo'
        verbose_name_plural = 'Catálogo de Ações'
        ordering = ['eixo', 'nome']

    def __str__(self):
        return f"{self.eixo.nome} - {self.nome}"