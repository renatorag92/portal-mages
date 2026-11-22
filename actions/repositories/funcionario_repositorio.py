import re
from django.db.models import Exists, OuterRef
from django.shortcuts import get_object_or_404

from ..models import Funcionario, SolicitacaoRedefinicaoSenha


class FuncionarioRepositorio:
    @staticmethod
    def buscar_ou_404(funcionario_id):
        return get_object_or_404(Funcionario, pk=funcionario_id)

    @staticmethod
    def buscar_por_cpf_e_prefeitura(cpf, prefeitura):
        digitos = re.sub(r'\D', '', cpf or '')
        if prefeitura is None or len(digitos) != 11:
            return None
        return Funcionario.objects.filter(prefeitura=prefeitura, username=digitos).first()

    @staticmethod
    def buscar_ativo_com_acesso_por_cpf(cpf):
        return Funcionario.objects.filter(
            username=cpf, tem_acesso=True, is_active=True
        ).first()

    @staticmethod
    def listar_com_solicitacao_pendente():
        solicitacoes_pendentes = SolicitacaoRedefinicaoSenha.objects.filter(
            funcionario_id=OuterRef('pk'), pendente=True
        )
        return (
            Funcionario.objects.select_related('prefeitura', 'consultoria')
            .annotate(senha_solicitada=Exists(solicitacoes_pendentes))
            .order_by('nome')
        )

    @staticmethod
    def contar_consultores():
        return Funcionario.objects.filter(
            tem_acesso=True,
            consultoria__isnull=False,
        ).count()

    @staticmethod
    def obter_caminho_foto(funcionario_id):
        return Funcionario.objects.values_list('foto', flat=True).get(pk=funcionario_id)

    @staticmethod
    def salvar(funcionario, update_fields=None):
        funcionario.save(update_fields=update_fields)
        return funcionario

    @staticmethod
    def excluir(funcionario):
        funcionario.delete()