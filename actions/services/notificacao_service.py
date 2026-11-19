from datetime import timedelta
from django.utils import timezone

from ..repositories.acao_repositorio import AcaoRepositorio
from ..repositories.etapa_repositorio import EtapaRepositorio
from ..repositories.notificacao_repositorio import NotificacaoRepositorio


class NotificacaoService:
    @staticmethod
    def marcar_lida(usuario, prefeitura, tipo, item_id):
        if tipo == 'acao':
            acao = AcaoRepositorio.buscar_por_prefeitura(prefeitura, item_id)
            if acao is None:
                return False
            NotificacaoRepositorio.registrar_leitura_acao(usuario, acao)
        elif tipo == 'etapa':
            etapa = EtapaRepositorio.buscar_por_prefeitura(prefeitura, item_id)
            if etapa is None:
                return False
            NotificacaoRepositorio.registrar_leitura_etapa(usuario, etapa)
        return True

    @staticmethod
    def marcar_nao_lida(usuario, prefeitura, tipo, item_id):
        if tipo == 'acao':
            acao = AcaoRepositorio.buscar_por_prefeitura(prefeitura, item_id)
            if acao is None:
                return False
            NotificacaoRepositorio.remover_leitura_acao(usuario, acao)
            return True
        if tipo == 'etapa':
            etapa = EtapaRepositorio.buscar_por_prefeitura(prefeitura, item_id)
            if etapa is None:
                return False
            NotificacaoRepositorio.remover_leitura_etapa(usuario, etapa)
            return True
        return None

    @staticmethod
    def remover(usuario, prefeitura, tipo, item_id):
        limite = timezone.localdate() + timedelta(days=7)
        if tipo == 'acao':
            alvo = AcaoRepositorio.buscar_elegivel_notificacao(prefeitura, item_id, limite)
            if alvo is None:
                return False
            notificacao = NotificacaoRepositorio.registrar_leitura_acao(usuario, alvo)
        elif tipo == 'etapa':
            alvo = EtapaRepositorio.buscar_elegivel_notificacao(prefeitura, item_id, limite)
            if alvo is None:
                return False
            notificacao = NotificacaoRepositorio.registrar_leitura_etapa(usuario, alvo)
        else:
            return None

        if not notificacao.removida:
            NotificacaoRepositorio.marcar_removida(notificacao)
        return True

    @staticmethod
    def serializar_feed(feed):
        notificacoes = []
        for item in feed:
            solicitacao_senha = item['alvo_tipo'] == 'solicitacao_senha'
            data_str = item['data'].isoformat() if hasattr(item['data'], 'isoformat') else (item['data'] or '')
            notificacoes.append({
                'id': item.get('id', f"{item['alvo_tipo']}-{item['alvo_id']}"),
                'alvo_tipo': item['alvo_tipo'],
                'titulo': item['titulo'],
                'mensagem': item['mensagem'],
                'tipo': item['tipo'],
                'urgencia': item['urgencia'],
                'lida': item.get('lida', False),
                'data': data_str,
                'prazo': data_str if item['alvo_tipo'] in {'acao', 'etapa'} else None,
                'criado_em': (item['solicitada_em'] if solicitacao_senha else item['criado_em']).isoformat(),
                'url': item['url'],
                'url_nao_lida': item['url_nao_lida'],
                'destino_url': item.get('destino_url'),
                'remover_url': item.get('remover_url'),
            })
        return notificacoes