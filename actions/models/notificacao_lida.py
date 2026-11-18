from django.db import models
from django.db.models import Q


class NotificacaoLida(models.Model):
    usuario = models.ForeignKey(
        'actions.Funcionario', on_delete=models.CASCADE, related_name='notificacoes_lidas',
    )
    acao = models.ForeignKey(
        'actions.Acao', on_delete=models.CASCADE, null=True, blank=True,
        related_name='leituras_notificacao',
    )
    etapa = models.ForeignKey(
        'actions.Etapa', on_delete=models.CASCADE, null=True, blank=True,
        related_name='leituras_notificacao',
    )
    lida_em = models.DateTimeField(auto_now_add=True)
    removida = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.CheckConstraint(
                condition=(
                    Q(acao__isnull=False, etapa__isnull=True)
                    | Q(acao__isnull=True, etapa__isnull=False)
                ),
                name='notificacao_lida_acao_ou_etapa',
            ),
            models.UniqueConstraint(
                fields=['usuario', 'acao'],
                condition=Q(acao__isnull=False),
                name='notificacao_lida_usuario_acao_unica',
            ),
            models.UniqueConstraint(
                fields=['usuario', 'etapa'],
                condition=Q(etapa__isnull=False),
                name='notificacao_lida_usuario_etapa_unica',
            ),
        ]