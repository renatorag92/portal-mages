from django.db import models


class Consultoria(models.Model):
    cnpj = models.CharField(max_length=14, unique=True)
    nome_juridico = models.CharField(max_length=100)
    nome_fantasia = models.CharField(max_length=100)
    endereco = models.CharField(max_length=150)

    class Meta:
        verbose_name = 'Consultoria'
        verbose_name_plural = 'Consultoria'

    def __str__(self):
        return self.nome_fantasia