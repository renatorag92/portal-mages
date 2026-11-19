from django.db import models


class Prefeitura(models.Model):
    cnpj = models.CharField(max_length=14, unique=True)
    nome_juridico = models.CharField(max_length=100)   # ex.: Prefeitura Municipal de Nova Cruz
    nome_fantasia = models.CharField(max_length=100)
    endereco = models.CharField(max_length=150)

    # Relação 1:1 com a Consultoria (anulável: a prefeitura pode existir antes do vínculo)
    consultoria = models.OneToOneField(
        'actions.Consultoria', on_delete=models.PROTECT, related_name='prefeitura',
        null=True, blank=True)

    class Meta:
        verbose_name = 'Prefeitura'
        verbose_name_plural = 'Prefeitura'  # mantém "Prefeitura" no singular no admin

    def __str__(self):
        return self.nome_fantasia