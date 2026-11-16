from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from .models import (
    Acao, NotificacaoLida, SolicitacaoRedefinicaoSenha,
)

STATUS_SEM_NOTIFICACAO = ('Concluído', 'Suspenso', 'Cancelado')


def _mensagem_prazo(dias):
    if dias < 0:
        return f'Prazo atrasado há {abs(dias)} dia(s).', 'overdue'
    if dias == 0:
        return 'O prazo termina hoje.', 'warning'
    if dias == 1:
        return 'O prazo termina amanhã.', 'danger'
    return f'O prazo termina em {dias} dia(s).', 'warning'


def notifications(request):
    solicitacoes_senha = []
    if request.user.is_authenticated and request.user.e_consultor:
        solicitacoes_senha = list(
            SolicitacaoRedefinicaoSenha.objects.filter(pendente=True)
            .select_related('funcionario')
        )
    notificacoes_senha = [
        {
            'id': f'solicitacao_senha-{solicitacao.pk}',
            'titulo': 'Solicitação de troca de senha',
            'mensagem': f'{solicitacao.funcionario.nome} deseja alterar a senha.',
            'nome': solicitacao.funcionario.nome,
            'tipo': 'warning',
            'urgencia': 'seguranca',
            'alvo_tipo': 'solicitacao_senha',
            'alvo_id': solicitacao.pk,
            'lida': False,
            'url': None,
            'url_nao_lida': None,
            'destino_url': reverse('gerenciar_funcionario'),
            'solicitada_em': solicitacao.solicitada_em,
            'data': solicitacao.solicitada_em,
            'data_iso': solicitacao.solicitada_em,
            'prazo': None,
        }
        for solicitacao in solicitacoes_senha
    ]

    if not request.user.is_authenticated:
        return {
            'notifications': [],
            'notification_count': 0,
            'notification_total_count': 0,
            'password_reset_notifications': [],
            'password_reset_notification_count': 0,
            'password_reset_unread_count': 0,
            'notification_feed': [],
            'notification_display_total_count': 0,
            'notification_display_visible_count': 0,
            'notification_display_unread_count': 0,
        }

    solicitacoes_senha = []
    if request.user.e_consultor:
        solicitacoes_senha = list(
            SolicitacaoRedefinicaoSenha.objects.filter(pendente=True)
            .select_related('funcionario')
        )

    notificacoes_senha = [
    {
        'id': f'solicitacao_senha-{s.pk}',
        'titulo': 'Solicitação de troca de senha',
        'mensagem': f'{s.funcionario.nome} deseja alterar a senha.',
        'nome': s.funcionario.nome,
        'tipo': 'warning',
        'urgencia': 'seguranca',
        'alvo_tipo': 'solicitacao_senha',
        'alvo_id': s.pk,
        'lida': False,                       # pedido pendente: sempre aparece como não lido
        'url': reverse('gerenciar_funcionario'),
        'url_nao_lida': reverse('gerenciar_funcionario'),
        'destino_url': reverse('gerenciar_funcionario'),
        'remover_url': None,                 # não se remove pedido de senha pelo sino
        'solicitada_em': s.solicitada_em,
        'criado_em': s.solicitada_em,
        'data': None,
        'data_iso': None,                    # era datetime: a view precisa de texto ou None
        'prazo': None,
    }
    for s in solicitacoes_senha
]

    prefeituras = list(request.user.prefeituras_permitidas()[:2])
    prefeitura_id = request.session.get('prefeitura_id')
    prefeitura = next(
        (item for item in prefeituras if str(item.pk) == str(prefeitura_id)),
        None,
    )
    if prefeitura is None and len(prefeituras) == 1:
        prefeitura = prefeituras[0]
    if prefeitura is None:
        return {
            'notifications': [],
            'notification_count': 0,
            'notification_total_count': 0,
            'password_reset_notifications': notificacoes_senha,
            'password_reset_notification_count': len(notificacoes_senha),
            'password_reset_unread_count': sum(
                len(notificacoes_senha)
            ),
            'notification_display_total_count': len(notificacoes_senha),
            'notification_display_visible_count': len(notificacoes_senha),
            'notification_feed': notificacoes_senha,
        }

    hoje = timezone.localdate()
    limite = hoje + timedelta(days=7)
    avisos = []

    acoes = Acao.objects.filter(
        prefeitura=prefeitura,
        data_fim__lte=limite,
    ).exclude(
        status__nome__in=STATUS_SEM_NOTIFICACAO,
    ).select_related('status')
    acoes_lidas = set(
        NotificacaoLida.objects.filter(
            usuario=request.user,
            acao__prefeitura=prefeitura,
            removida=False,
        ).values_list('acao_id', flat=True)
    )
    for acao in acoes:
        dias = (acao.data_fim - hoje).days
        mensagem, tipo = _mensagem_prazo(dias)
        avisos.append({
            'titulo': f'Ação: {acao.nome}',
            'mensagem': mensagem,
            'data': acao.data_fim,
            'criado_em': acao.criado_em,
            'tipo': tipo,
            'urgencia': {
                'overdue': 'atrasado',
                'danger': 'breve',
                'warning': 'info',
            }[tipo],
            'alvo_tipo': 'acao',
            'alvo_id': acao.pk,
            'lida': acao.pk in acoes_lidas,
        })

    acoes_removidas = set(
        NotificacaoLida.objects.filter(
            usuario=request.user,
            acao__prefeitura=prefeitura,
            removida=True,
        ).values_list('acao_id', flat=True)
    )
    avisos = [
        aviso for aviso in avisos
        if aviso['alvo_id'] not in acoes_removidas
    ]
    avisos.sort(key=lambda aviso: aviso['criado_em'], reverse=True)
    notificacoes = [
        {
            **aviso,
            'id': f"{aviso['alvo_tipo']}-{aviso['alvo_id']}",
            'data_iso': aviso['criado_em'],
            'url': reverse(
                'marcar_notificacao_lida',
                args=[aviso['alvo_tipo'], aviso['alvo_id']],
            ),
            'url_nao_lida': reverse(
                'marcar_notificacao_nao_lida',
                args=[aviso['alvo_tipo'], aviso['alvo_id']],
            ),
            'remover_url': reverse(
                'remover_notificacao',
                args=[aviso['alvo_tipo'], aviso['alvo_id']],
            ),
        }
        for aviso in avisos
    ]
    notification_feed = sorted(
        [*notificacoes, *notificacoes_senha],
        key=lambda aviso: (
            aviso['solicitada_em']
            if aviso['alvo_tipo'] == 'solicitacao_senha'
            else aviso['criado_em']
        ),
        reverse=True,
    )
    return {
        'notifications': notificacoes,
        'notification_count': sum(not notification['lida'] for notification in avisos),
        'notification_total_count': len(avisos),
        'password_reset_notifications': notificacoes_senha,
        'password_reset_notification_count': len(notificacoes_senha),
        'password_reset_unread_count': len(notificacoes_senha),
        'notification_feed': notification_feed,
        'notification_display_total_count': len(avisos) + len(notificacoes_senha),
        'notification_display_visible_count': len(notification_feed),
        'notification_display_unread_count': (
            sum(not notification['lida'] for notification in avisos)
            + len(notificacoes_senha)
        ),
        'password_reset_unread_count': len(notificacoes_senha),
    }
