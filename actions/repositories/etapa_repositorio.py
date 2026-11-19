from django.db.models import Q

from ..context_processors import STATUS_SEM_NOTIFICACAO
from ..models import Etapa


class EtapaRepositorio:
    @staticmethod
    def buscar_por_prefeitura(prefeitura, etapa_id):
        if prefeitura is None:
            return None
        return (
            Etapa.objects.select_related('acao__status', 'acao__eixo', 'acao__responsavel', 'responsavel')
            .filter(pk=etapa_id, acao__prefeitura=prefeitura)
            .first()
        )

    @staticmethod
    def buscar_elegivel_notificacao(prefeitura, etapa_id, limite):
        return Etapa.objects.filter(
            acao__prefeitura=prefeitura,
            concluida=False,
            data_fim__lte=limite,
            pk=etapa_id,
        ).exclude(acao__status__nome__in=STATUS_SEM_NOTIFICACAO).first()

    @staticmethod
    def listar_por_acao(acao):
        return acao.etapas.select_related('responsavel').order_by('id')

    @staticmethod
    def existe_fora_periodo(acao, data_inicio, data_fim):
        return acao.etapas.filter(Q(data_inicio__lt=data_inicio) | Q(data_fim__gt=data_fim)).exists()

    @staticmethod
    def criar(**kwargs):
        return Etapa.objects.create(**kwargs)

    @staticmethod
    def salvar(etapa, update_fields=None):
        etapa.save(update_fields=update_fields)
        return etapa

    @staticmethod
    def excluir(etapa):
        etapa.delete()

    @staticmethod
    def excluir_todas_da_acao(acao):
        acao.etapas.all().delete()