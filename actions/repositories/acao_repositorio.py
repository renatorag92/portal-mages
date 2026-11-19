from django.db.models import Count, Q

from ..context_processors import STATUS_SEM_NOTIFICACAO
from ..models import Acao


class AcaoRepositorio:
    @staticmethod
    def buscar_por_prefeitura(prefeitura, acao_id):
        if prefeitura is None or not str(acao_id).isdigit():
            return None
        return (
            Acao.objects.select_related('modelo', 'eixo', 'status', 'responsavel')
            .filter(prefeitura=prefeitura, pk=int(acao_id))
            .first()
        )

    @staticmethod
    def buscar_elegivel_notificacao(prefeitura, acao_id, limite):
        return Acao.objects.filter(
            prefeitura=prefeitura,
            data_fim__lte=limite,
            pk=acao_id,
        ).exclude(status__nome__in=STATUS_SEM_NOTIFICACAO).first()

    @staticmethod
    def listar_para_kanban(prefeitura):
        return Acao.objects.filter(prefeitura=prefeitura).select_related(
            'modelo', 'eixo', 'status', 'responsavel',
        ).annotate(
            total_etapas=Count('etapas'),
            etapas_concluidas=Count('etapas', filter=Q(etapas__concluida=True)),
        )

    @staticmethod
    def listar_para_dashboard(prefeitura):
        return Acao.objects.filter(prefeitura=prefeitura).select_related(
            'status', 'eixo', 'responsavel'
        )

    @staticmethod
    def criar(**kwargs):
        return Acao.objects.create(**kwargs)

    @staticmethod
    def salvar(acao):
        acao.save()
        return acao

    @staticmethod
    def excluir(acao):
        acao.delete()