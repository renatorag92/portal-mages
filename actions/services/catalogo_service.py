from django.db.models.deletion import ProtectedError

from ..repositories.catalogo_repositorio import CatalogoRepositorio
from .excecoes import ErroRegraNegocio


class CatalogoService:
    @staticmethod
    def buscar_ou_404(modelo_id):
        return CatalogoRepositorio.buscar_ou_404(modelo_id)

    @staticmethod
    def listar_filtrado(nome_filtro='', eixo_filtro=''):
        return CatalogoRepositorio.listar_filtrado(nome_filtro, eixo_filtro)

    @staticmethod
    def nome_existe(nome, excluir_pk=None):
        return CatalogoRepositorio.nome_existe(nome, excluir_pk)

    @staticmethod
    def excluir(modelo_id):
        modelo = CatalogoRepositorio.buscar_ou_404(modelo_id)
        try:
            CatalogoRepositorio.excluir(modelo)
        except ProtectedError:
            raise ErroRegraNegocio(
                'Esta ação não pode ser excluída porque está sendo usada em uma ou mais ações.'
            )