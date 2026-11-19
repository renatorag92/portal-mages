from django.core.exceptions import ValidationError
from django.db import models


class Eixo(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=45, unique=True)
    pai = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True,
        related_name='subeixos')

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()
        if self.pai_id is None:
            return
        if self.pai_id == self.pk:
            raise ValidationError({'pai': 'Um eixo não pode ser subeixo de si mesmo.'})
        if self.pai.pai_id is not None:
            raise ValidationError({'pai': 'Só é permitido um nível de subeixo.'})
        if self.pk and self.subeixos.exists():
            raise ValidationError({'pai': 'Este eixo tem subeixos, então não pode ser subeixo.'})