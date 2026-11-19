from ..models import Consultoria


class ConsultoriaRepositorio:
    @staticmethod
    def obter_primeira():
        return Consultoria.objects.order_by('pk').first()

    @staticmethod
    def cnpj_existe(cnpj, excluir_pk=None):
        qs = Consultoria.objects.filter(cnpj=cnpj)
        if excluir_pk is not None:
            qs = qs.exclude(pk=excluir_pk)
        return qs.exists()