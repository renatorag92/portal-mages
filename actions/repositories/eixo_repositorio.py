from django.db.models import Count
from django.shortcuts import get_object_or_404

from ..models import Eixo


class EixoRepositorio:
    @staticmethod
    def buscar_ou_404(eixo_id):
        return get_object_or_404(Eixo, pk=eixo_id)

    @staticmethod
    def buscar_por_id(eixo_id):
        if not str(eixo_id or '').isdigit():
            return None
        return Eixo.objects.filter(pk=eixo_id).first()

    @staticmethod
    def listar_com_vinculos():
        return Eixo.objects.annotate(total_vinculos=Count('acoes')).order_by('nome')

    @staticmethod
    def listar_principais(excluir_pk=None):
        qs = Eixo.objects.filter(principal__isnull=True)
        if excluir_pk:
            qs = qs.exclude(pk=excluir_pk)
        return qs

    @staticmethod
    def listar_folha():
        return Eixo.objects.filter(subeixos__isnull=True).select_related('principal').order_by('nome')

    @staticmethod
    def listar_raiz_com_subeixos():
        return Eixo.objects.filter(principal__isnull=True).prefetch_related('subeixos')

    @staticmethod
    def nome_existe(nome, excluir_pk=None):
        return Eixo.objects.filter(nome__iexact=nome).exclude(pk=excluir_pk).exists()

    @staticmethod
    def excluir(eixo):
        eixo.delete()