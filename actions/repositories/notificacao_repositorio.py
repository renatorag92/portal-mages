from ..models import NotificacaoLida


class NotificacaoRepositorio:
    @staticmethod
    def registrar_leitura_acao(usuario, acao):
        obj, _ = NotificacaoLida.objects.get_or_create(usuario=usuario, acao=acao, etapa=None)
        return obj

    @staticmethod
    def registrar_leitura_etapa(usuario, etapa):
        obj, _ = NotificacaoLida.objects.get_or_create(usuario=usuario, acao=None, etapa=etapa)
        return obj

    @staticmethod
    def remover_leitura_acao(usuario, acao):
        NotificacaoLida.objects.filter(usuario=usuario, acao=acao, removida=False).delete()

    @staticmethod
    def remover_leitura_etapa(usuario, etapa):
        NotificacaoLida.objects.filter(usuario=usuario, etapa=etapa, removida=False).delete()

    @staticmethod
    def marcar_removida(notificacao):
        notificacao.removida = True
        notificacao.save(update_fields=['removida'])