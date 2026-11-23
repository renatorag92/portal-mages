from django.core.exceptions import ValidationError
from django.db import models


class Eixo(models.Model):
    id = models.AutoField(primary_key=True)
    nome = models.CharField(max_length=45, unique=True)
    principal = models.ForeignKey(
        'self', on_delete=models.PROTECT, null=True, blank=True,
        related_name='subeixos')

    def __str__(self):
        return self.nome

    def clean(self):
        super().clean()
        if self.principal_id is None:
            return
        if self.principal_id == self.pk:
            raise ValidationError({'principal': 'Um eixo não pode ser subeixo de si mesmo.'})
        if self.principal.principal_id is not None:
            raise ValidationError({'principal': 'Só é permitido um nível de subeixo.'})
        if self.pk and self.subeixos.exists():
            raise ValidationError({'principal': 'Este eixo tem subeixos, então não pode ser subeixo.'})