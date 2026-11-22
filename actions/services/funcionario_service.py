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
    def contar_consultores():
        return FuncionarioRepositorio.contar_consultores()

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
        if funcionario.e_consultor:
            total_consultores = FuncionarioRepositorio.contar_consultores()
            if total_consultores <= 2:
                raise ErroRegraNegocio(
                    'Não é possível excluir consultores quando restarem menos de três no sistema.'
                )
        try:
            FuncionarioRepositorio.excluir(funcionario)
        except ProtectedError:
            raise ErroRegraNegocio(
                'Este funcionário não pode ser excluído porque está vinculado a ações ou etapas.'
            )

    @staticmethod
    def atualizar_perfil(form):
        return form.save()