from django.db.models import Count
from django.shortcuts import get_object_or_404

from ..models import AcaoCatalogo


class CatalogoRepositorio:
    @staticmethod
    def buscar_ou_404(modelo_id):
        return get_object_or_404(AcaoCatalogo, pk=modelo_id)

    @staticmethod
    def buscar_por_id(modelo_id):
        if not str(modelo_id or '').isdigit():
            return None
        return AcaoCatalogo.objects.select_related('eixo').filter(pk=modelo_id).first()

    @staticmethod
    def listar_todos():
        return AcaoCatalogo.objects.select_related('eixo')

    @staticmethod
    def listar_filtrado(nome_filtro='', eixo_filtro=''):
        qs = (
            AcaoCatalogo.objects.select_related('eixo', 'eixo__pai')
            .annotate(total_acoes=Count('instancias'))
            .order_by('eixo__nome', 'nome')
        )
        if nome_filtro:
            qs = qs.filter(nome__icontains=nome_filtro)
        if eixo_filtro.isdigit():
            qs = qs.filter(eixo_id=eixo_filtro)
        return qs

    @staticmethod
    def nome_existe(nome, excluir_pk=None):
        return AcaoCatalogo.objects.filter(nome__iexact=nome).exclude(pk=excluir_pk).exists()

    @staticmethod
    def excluir(modelo):
        modelo.delete()