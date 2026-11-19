from ..models import Prefeitura


class PrefeituraRepositorio:
    @staticmethod
    def obter_primeira():
        return Prefeitura.objects.order_by('pk').first()

    @staticmethod
    def existe_alguma():
        return Prefeitura.objects.exists()

    @staticmethod
    def buscar_por_consultoria(consultoria):
        return Prefeitura.objects.filter(consultoria=consultoria).first()

    @staticmethod
    def salvar(registro, dados):
        registro = registro or Prefeitura()
        for campo in ('cnpj', 'nome_fantasia', 'nome_juridico', 'endereco'):
            setattr(registro, campo, dados[campo])
        registro.save()
        return registro