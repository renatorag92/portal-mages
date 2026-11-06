from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

from .models import Acao, Etapa, NotificacaoLida


def notifications(request):
    if not request.user.is_authenticated:
        return {
            'notifications': [],
            'notification_count': 0,
            'notification_total_count': 0,
        }

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
        }

    hoje = timezone.localdate()
    limite = hoje + timedelta(days=7)
    status_encerrados = ('Concluído', 'Cancelado')
    avisos = []

    acoes = Acao.objects.filter(
        prefeitura=prefeitura,
        data_fim__lte=limite,
    ).exclude(
        status__nome__in=status_encerrados,
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
        if dias < 0:
            mensagem = f'O prazo venceu há {abs(dias)} dia(s).'
            tipo = 'danger'
        elif dias == 0:
            mensagem = 'O prazo termina hoje.'
            tipo = 'warning'
        else:
            mensagem = f'O prazo termina em {dias} dia(s).'
            tipo = 'warning'
        avisos.append({
            'titulo': f'Ação: {acao.nome}',
            'mensagem': mensagem,
            'data': acao.data_fim,
            'criado_em': acao.criado_em,
            'tipo': tipo,
            'alvo_tipo': 'acao',
            'alvo_id': acao.pk,
            'lida': acao.pk in acoes_lidas,
        })

    etapas = Etapa.objects.filter(
        acao__prefeitura=prefeitura,
        concluida=False,
        data_fim__lte=limite,
    ).exclude(
        acao__status__nome__in=status_encerrados,
    ).select_related('acao')
    etapas_lidas = set(
        NotificacaoLida.objects.filter(
            usuario=request.user,
            etapa__acao__prefeitura=prefeitura,
            removida=False,
        ).values_list('etapa_id', flat=True)
    )
    for etapa in etapas:
        dias = (etapa.data_fim - hoje).days
        if dias < 0:
            mensagem = f'O prazo venceu há {abs(dias)} dia(s).'
            tipo = 'danger'
        elif dias == 0:
            mensagem = 'O prazo termina hoje.'
            tipo = 'warning'
        else:
            mensagem = f'O prazo termina em {dias} dia(s).'
            tipo = 'warning'
        avisos.append({
            'titulo': f'Etapa: {etapa.nome}',
            'mensagem': f'{mensagem} Ação: {etapa.acao.nome}.',
            'data': etapa.data_fim,
            'criado_em': etapa.criado_em,
            'tipo': tipo,
            'alvo_tipo': 'etapa',
            'alvo_id': etapa.pk,
            'lida': etapa.pk in etapas_lidas,
        })

    acoes_removidas = set(
        NotificacaoLida.objects.filter(
            usuario=request.user,
            acao__prefeitura=prefeitura,
            removida=True,
        ).values_list('acao_id', flat=True)
    )
    etapas_removidas = set(
        NotificacaoLida.objects.filter(
            usuario=request.user,
            etapa__acao__prefeitura=prefeitura,
            removida=True,
        ).values_list('etapa_id', flat=True)
    )
    avisos = [
        aviso for aviso in avisos
        if not (
            aviso['alvo_tipo'] == 'acao' and aviso['alvo_id'] in acoes_removidas
            or aviso['alvo_tipo'] == 'etapa' and aviso['alvo_id'] in etapas_removidas
        )
    ]
    avisos.sort(key=lambda aviso: aviso['criado_em'], reverse=True)
    avisos.sort(key=lambda aviso: aviso['lida'])
    notificacoes = [
        {
            **aviso,
            'url': reverse(
                'marcar_notificacao_lida',
                args=[aviso['alvo_tipo'], aviso['alvo_id']],
            ),
            'remover_url': reverse(
                'remover_notificacao',
                args=[aviso['alvo_tipo'], aviso['alvo_id']],
            ),
        }
        for aviso in avisos[:8]
    ]
    return {
        'notifications': notificacoes,
        'notification_count': sum(not notification['lida'] for notification in avisos),
        'notification_total_count': len(avisos),
    }
