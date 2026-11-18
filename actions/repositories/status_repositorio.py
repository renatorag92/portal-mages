from django.db.models import Count, Q
from django.shortcuts import get_object_or_404

from ..models import Status


class StatusRepositorio:
    @staticmethod
    def buscar_ou_404(status_id):
        return get_object_or_404(Status, pk=status_id)

    @staticmethod
    def buscar_por_id(status_id):
        if not str(status_id or '').isdigit():
            return None
        return Status.objects.filter(pk=status_id).first()

    @staticmethod
    def obter_primeiro():
        return Status.objects.first()

    @staticmethod
    def cor_existe(cor, excluir_pk=None):
        return Status.objects.filter(cor__iexact=cor).exclude(pk=excluir_pk).exists()

    @staticmethod
    def listar_ordenados():
        return Status.objects.order_by('ordem', 'id')

    @staticmethod
    def listar_com_contagem():
        return Status.objects.annotate(total_acoes=Count('acoes')).order_by('ordem', 'id')

    @staticmethod
    def listar_para_kanban(prefeitura):
        return Status.objects.annotate(
            total_acoes=Count('acoes', filter=Q(acoes__prefeitura=prefeitura)),
        ).order_by('ordem', 'id')