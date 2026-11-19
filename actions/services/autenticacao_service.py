import re

from ..forms import gerar_senha_provisoria
from ..repositories.funcionario_repositorio import FuncionarioRepositorio
from ..repositories.solicitacao_senha_repositorio import SolicitacaoSenhaRepositorio
from .excecoes import ErroRegraNegocio


class AutenticacaoService:
    @staticmethod
    def gerar_nova_senha_provisoria(funcionario_id):
        funcionario = FuncionarioRepositorio.buscar_ou_404(funcionario_id)
        solicitacao = SolicitacaoSenhaRepositorio.buscar_pendente(funcionario)

        if not funcionario.tem_acesso:
            raise ErroRegraNegocio('Este funcionário não tem acesso ao sistema.')
        if not funcionario.primeiro_acesso and solicitacao is None:
            raise ErroRegraNegocio(
                'Não há solicitação de troca de senha pendente para este funcionário.'
            )

        senha = gerar_senha_provisoria()
        funcionario.set_password(senha)
        funcionario.primeiro_acesso = True
        FuncionarioRepositorio.salvar(funcionario)
        if solicitacao is not None:
            SolicitacaoSenhaRepositorio.marcar_resolvida(solicitacao)
        return funcionario, senha

    @staticmethod
    def registrar_solicitacao_redefinicao(cpf_bruto):
        cpf = re.sub(r'\D', '', cpf_bruto or '')
        if len(cpf) == 11:
            funcionario = FuncionarioRepositorio.buscar_ativo_com_acesso_por_cpf(cpf)
            if funcionario is not None:
                SolicitacaoSenhaRepositorio.criar_se_nao_existir(funcionario)

    @staticmethod
    def concluir_primeiro_acesso(usuario):
        usuario.primeiro_acesso = False
        FuncionarioRepositorio.salvar(usuario, update_fields=['primeiro_acesso'])

    @staticmethod
    def listar_prefeituras_permitidas(usuario):
        return usuario.prefeituras_permitidas().order_by('nome_fantasia')

    @staticmethod
    def selecionar_prefeitura_sessao(usuario, session, prefeitura_id):
        permitidas = usuario.prefeituras_permitidas()
        if not str(prefeitura_id or '').isdigit():
            return None
        escolhida = permitidas.filter(pk=prefeitura_id).first()
        if escolhida:
            session['prefeitura_id'] = escolhida.pk
        return escolhida

    @staticmethod
    def resolver_prefeitura_ativa(usuario, session):
        if not usuario.is_authenticated:
            return None
        permitidas = usuario.prefeituras_permitidas()
        prefeitura_id = session.get('prefeitura_id')
        if str(prefeitura_id or '').isdigit():
            escolhida = permitidas.filter(pk=prefeitura_id).first()
            if escolhida:
                return escolhida

        opcoes = list(permitidas[:2])
        if len(opcoes) == 1:
            session['prefeitura_id'] = opcoes[0].pk
            return opcoes[0]
        return None