from django.core.files.storage import default_storage
from django.db.models.deletion import ProtectedError

from ..forms import preparar_senha
from ..repositories.funcionario_repositorio import FuncionarioRepositorio
from .excecoes import ErroRegraNegocio


class FuncionarioService:
    @staticmethod
    def buscar_ou_404(funcionario_id):
        return FuncionarioRepositorio.buscar_ou_404(funcionario_id)

    @staticmethod
    def listar_todos():
        return FuncionarioRepositorio.listar_com_solicitacao_pendente()

    @staticmethod
    def salvar(form):
        registro = form.save(commit=False)
        senha = preparar_senha(registro)
        FuncionarioRepositorio.salvar(registro)
        return registro, senha

    @staticmethod
    def excluir(funcionario_id, usuario_logado):
        funcionario = FuncionarioRepositorio.buscar_ou_404(funcionario_id)
        if funcionario.pk == usuario_logado.pk:
            raise ErroRegraNegocio('Você não pode excluir o seu próprio cadastro.')
        try:
            FuncionarioRepositorio.excluir(funcionario)
        except ProtectedError:
            raise ErroRegraNegocio(
                'Este funcionário não pode ser excluído porque está vinculado a ações ou etapas.'
            )

    @staticmethod
    def atualizar_perfil(form, usuario, nova_foto_enviada, limpar_foto):
        foto_anterior = FuncionarioRepositorio.obter_caminho_foto(usuario.pk)
        usuario_atualizado = form.save()
        if foto_anterior and (nova_foto_enviada or limpar_foto):
            default_storage.delete(foto_anterior)
        return usuario_atualizado