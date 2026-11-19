from django.db import models
from django.db.models import Q


class SolicitacaoRedefinicaoSenha(models.Model):
    funcionario = models.ForeignKey(
        'actions.Funcionario', on_delete=models.CASCADE, related_name='solicitacoes_redefinicao_senha',
    )
    solicitada_em = models.DateTimeField(auto_now_add=True)
    pendente = models.BooleanField(default=True)

    class Meta:
        ordering = ['-solicitada_em']
        constraints = [
            models.UniqueConstraint(
                fields=['funcionario'],
                condition=Q(pendente=True),
                name='solicitacao_senha_pendente_unica',
            ),
        ]