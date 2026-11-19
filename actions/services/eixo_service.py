from django.db.models.deletion import ProtectedError

from ..repositories.eixo_repositorio import EixoRepositorio
from .excecoes import ErroRegraNegocio


class EixoService:
    @staticmethod
    def buscar_ou_404(eixo_id):
        return EixoRepositorio.buscar_ou_404(eixo_id)

    @staticmethod
    def listar_todos():
        return EixoRepositorio.listar_com_vinculos()

    @staticmethod
    def listar_principais(excluir_pk=None):
        return EixoRepositorio.listar_principais(excluir_pk)

    @staticmethod
    def listar_folha():
        return EixoRepositorio.listar_folha()

    @staticmethod
    def nome_existe(nome, excluir_pk=None):
        return EixoRepositorio.nome_existe(nome, excluir_pk)

    @staticmethod
    def excluir(eixo_id):
        eixo = EixoRepositorio.buscar_ou_404(eixo_id)
        try:
            EixoRepositorio.excluir(eixo)
        except ProtectedError:
            raise ErroRegraNegocio(
                'Este eixo não pode ser excluído porque está vinculado a um ou mais itens do catálogo.'
            )