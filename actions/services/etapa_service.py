from django.utils.dateparse import parse_date

from ..models import Acao, Status
from ..repositories.acao_repositorio import AcaoRepositorio
from ..repositories.etapa_repositorio import EtapaRepositorio
from ..repositories.funcionario_repositorio import FuncionarioRepositorio
from .excecoes import ErroRegraNegocio


def _converter_data(valor):
    try:
        return parse_date(valor or '')
    except ValueError:
        return None


def _iso(data):
    return data.isoformat() if hasattr(data, 'isoformat') else (data or '')


class EtapaService:
    @staticmethod
    def serializar(etapa):
        return {
            'id': etapa.id,
            'nome': etapa.nome,
            'cpf': etapa.responsavel.cpf,
            'responsavel': etapa.responsavel.nome,
            'prioridade': etapa.prioridade,
            'data_inicio': _iso(etapa.data_inicio),
            'data_fim': _iso(etapa.data_fim),
            'observacoes': etapa.observacoes or '',
            'concluida': etapa.concluida,
        }

    @staticmethod
    def _validar_dados(data, acao, prefeitura):
        nome = (data.get('nome') or '').strip()
        if not nome or len(nome) > 45:
            raise ErroRegraNegocio('Informe um nome para a etapa com até 45 caracteres.')

        prioridade = data.get('prioridade')
        if prioridade not in Acao.Status_Prioridade.values:
            raise ErroRegraNegocio('Prioridade inválida.')

        data_inicio = _converter_data(data.get('data_inicio'))
        data_fim = _converter_data(data.get('data_fim'))
        if not data_inicio or not data_fim:
            raise ErroRegraNegocio('Informe datas válidas.')
        if data_fim < data_inicio:
            raise ErroRegraNegocio('A data de fim não pode ser anterior à data de início.')
        if not (data_inicio >= acao.data_inicio and data_fim <= acao.data_fim):
            raise ErroRegraNegocio('As datas da etapa devem estar dentro do período da ação.')

        responsavel = FuncionarioRepositorio.buscar_por_cpf_e_prefeitura(data.get('cpf'), prefeitura)
        if responsavel is None:
            raise ErroRegraNegocio('CPF do responsável não encontrado entre os funcionários da sua prefeitura.')

        return {
            'nome': nome,
            'responsavel': responsavel,
            'prioridade': prioridade,
            'data_inicio': data_inicio,
            'data_fim': data_fim,
            'observacoes': (data.get('observacoes') or '').strip() or None,
        }

    @classmethod
    def adicionar(cls, prefeitura, acao_id, data, usuario):
        acao = AcaoRepositorio.buscar_por_prefeitura(prefeitura, acao_id)
        if acao is None:
            raise ErroRegraNegocio('Ação não encontrada.', status=404)
        if acao.status.chave == Status.Chave.CANCELADO:
            raise ErroRegraNegocio('Uma ação cancelada não pode ser editada.', status=403)

        dados = cls._validar_dados(data, acao, prefeitura)
        etapa = EtapaRepositorio.criar(acao=acao, criado_por=usuario, atualizado_por=usuario, **dados)
        return cls.serializar(etapa)

    @classmethod
    def editar(cls, prefeitura, etapa_id, data, usuario):
        etapa = EtapaRepositorio.buscar_por_prefeitura(prefeitura, etapa_id)
        if etapa is None:
            raise ErroRegraNegocio('Etapa não encontrada.', status=404)
        if etapa.acao.status.chave == Status.Chave.CANCELADO:
            raise ErroRegraNegocio('Uma ação cancelada não pode ser editada.', status=403)

        dados = cls._validar_dados(data, etapa.acao, prefeitura)
        for campo, valor in dados.items():
            setattr(etapa, campo, valor)
        etapa.atualizado_por = usuario
        EtapaRepositorio.salvar(etapa)
        return cls.serializar(etapa)

    @staticmethod
    def alternar_conclusao(prefeitura, etapa_id, usuario):
        etapa = EtapaRepositorio.buscar_por_prefeitura(prefeitura, etapa_id)
        if etapa is None:
            raise ErroRegraNegocio('Etapa não encontrada.', status=404)
        if etapa.acao.status.chave == Status.Chave.CANCELADO:
            raise ErroRegraNegocio('Uma ação cancelada não pode ser editada.', status=403)

        etapa.concluida = not etapa.concluida
        etapa.atualizado_por = usuario
        EtapaRepositorio.salvar(etapa, update_fields=['concluida', 'atualizado_por', 'atualizado_em'])
        return etapa.concluida

    @staticmethod
    def excluir(prefeitura, etapa_id):
        etapa = EtapaRepositorio.buscar_por_prefeitura(prefeitura, etapa_id)
        if etapa is None:
            raise ErroRegraNegocio('Etapa não encontrada.', status=404)
        if etapa.acao.status.chave == Status.Chave.CANCELADO:
            raise ErroRegraNegocio('Uma ação cancelada não pode ser editada.', status=403)
        EtapaRepositorio.excluir(etapa)