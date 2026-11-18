from django.db import IntegrityError

from ..repositories.consultoria_repositorio import ConsultoriaRepositorio
from ..repositories.prefeitura_repositorio import PrefeituraRepositorio
from .excecoes import ErroRegraNegocio
from .prefeitura_service import formatar_cnpj


class ConsultoriaService:
    @staticmethod
    def serializar(registro):
        prefeitura = PrefeituraRepositorio.buscar_por_consultoria(registro)
        return {
            'id': registro.pk,
            'cnpj': registro.cnpj,
            'cnpj_formatado': formatar_cnpj(registro.cnpj),
            'nome_fantasia': registro.nome_fantasia,
            'nome_juridico': registro.nome_juridico,
            'endereco': registro.endereco,
            'prefeitura_id': prefeitura.pk if prefeitura else None,
            'prefeitura_nome': prefeitura.nome_fantasia if prefeitura else '',
        }

    @staticmethod
    def preparar_tela(form_class):
        registro = ConsultoriaRepositorio.obter_primeira()
        sem_prefeituras = not PrefeituraRepositorio.existe_alguma()
        return {
            'tipo_entidade': 'consultoria',
            'titulo_entidade': 'Consultoria',
            'registro': registro,
            'cnpj_formatado': formatar_cnpj(registro.cnpj) if registro else '',
            'form': form_class(instance=registro) if not sem_prefeituras else None,
            'sem_prefeituras': sem_prefeituras,
        }

    @staticmethod
    def obter_para_edicao(registro_id):
        registro_atual = ConsultoriaRepositorio.obter_primeira()
        if registro_atual and str(registro_atual.pk) != str(registro_id):
            raise ErroRegraNegocio(
                'Já existe uma consultoria cadastrada.',
                status=409,
                errors={'__all__': ['Já existe uma consultoria cadastrada. Edite o registro atual.']},
            )
        if registro_atual is None and registro_id:
            raise ErroRegraNegocio(
                'Consultoria não encontrada.',
                status=404,
                errors={'__all__': ['Consultoria não encontrada.']},
            )
        return registro_atual

    @staticmethod
    def salvar(form, registro_atual):
        try:
            return form.salvar()
        except IntegrityError:
            if ConsultoriaRepositorio.cnpj_existe(
                form.cleaned_data['cnpj'],
                excluir_pk=registro_atual.pk if registro_atual else None,
            ):
                raise ErroRegraNegocio(
                    'CNPJ já cadastrado.',
                    status=409,
                    errors={'cnpj': ['CNPJ já cadastrado.']},
                )
            raise ErroRegraNegocio(
                'Não foi possível salvar a consultoria. Tente novamente.',
                status=409,
                errors={'__all__': ['Não foi possível salvar a consultoria. Tente novamente.']},
            )