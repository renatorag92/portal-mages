import re
from django.db import IntegrityError, transaction

from ..repositories.prefeitura_repositorio import PrefeituraRepositorio
from .excecoes import ErroRegraNegocio


def formatar_cnpj(cnpj):
    digitos = re.sub(r'\D', '', cnpj or '')
    if len(digitos) == 14:
        return f'{digitos[:2]}.{digitos[2:5]}.{digitos[5:8]}/{digitos[8:12]}-{digitos[12:]}'
    return digitos


class PrefeituraService:
    @staticmethod
    def serializar(registro):
        return {
            'id': registro.pk,
            'cnpj': registro.cnpj,
            'cnpj_formatado': formatar_cnpj(registro.cnpj),
            'nome_fantasia': registro.nome_fantasia,
            'nome_juridico': registro.nome_juridico,
            'endereco': registro.endereco,
        }

    @staticmethod
    def preparar_tela(form_class):
        registro = PrefeituraRepositorio.obter_primeira()
        return {
            'tipo_entidade': 'prefeitura',
            'titulo_entidade': 'Prefeitura',
            'registro': registro,
            'cnpj_formatado': formatar_cnpj(registro.cnpj) if registro else '',
            'form': form_class(instance=registro),
        }

    @staticmethod
    def obter_para_edicao(registro_id):
        registro = PrefeituraRepositorio.obter_primeira()
        if registro and str(registro.pk) != str(registro_id):
            raise ErroRegraNegocio(
                'Já existe uma prefeitura cadastrada.',
                status=409,
                errors={'__all__': ['Já existe uma prefeitura cadastrada. Edite o registro atual.']},
            )
        if registro is None and registro_id:
            raise ErroRegraNegocio(
                'Prefeitura não encontrada.',
                status=404,
                errors={'__all__': ['Prefeitura não encontrada.']},
            )
        return registro

    @staticmethod
    def salvar(registro, cleaned_data):
        try:
            with transaction.atomic():
                if registro is None and PrefeituraRepositorio.existe_alguma():
                    raise ErroRegraNegocio(
                        'Já existe uma prefeitura cadastrada.',
                        status=409,
                        errors={'__all__': ['Já existe uma prefeitura cadastrada.']},
                    )
                return PrefeituraRepositorio.salvar(registro, cleaned_data)
        except IntegrityError:
            raise ErroRegraNegocio(
                'CNPJ já cadastrado.',
                status=409,
                errors={'cnpj': ['CNPJ já cadastrado.']},
            )