from ..models import SolicitacaoRedefinicaoSenha


class SolicitacaoSenhaRepositorio:
    @staticmethod
    def buscar_pendente(funcionario):
        return SolicitacaoRedefinicaoSenha.objects.filter(
            funcionario=funcionario, pendente=True
        ).first()

    @staticmethod
    def criar_se_nao_existir(funcionario):
        return SolicitacaoRedefinicaoSenha.objects.get_or_create(
            funcionario=funcionario, pendente=True
        )

    @staticmethod
    def marcar_resolvida(solicitacao):
        solicitacao.pendente = False
        solicitacao.save(update_fields=['pendente'])