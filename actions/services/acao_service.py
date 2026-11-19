from decimal import Decimal, InvalidOperation

from django.db import IntegrityError, transaction
from django.db.models.deletion import ProtectedError

from ..models import Acao, Status
from ..repositories.acao_repositorio import AcaoRepositorio
from ..repositories.catalogo_repositorio import CatalogoRepositorio
from ..repositories.eixo_repositorio import EixoRepositorio
from ..repositories.etapa_repositorio import EtapaRepositorio
from ..repositories.funcionario_repositorio import FuncionarioRepositorio
from ..repositories.status_repositorio import StatusRepositorio
from .etapa_service import EtapaService, _converter_data, _iso
from .excecoes import ErroRegraNegocio


def _acao_cancelada(acao):
    return acao.status.chave == Status.Chave.CANCELADO


class AcaoService:
    @staticmethod
    def serializar(acao):
        return {
            'id': acao.id,
            'codigo': acao.codigo,
            'nome': acao.nome,
            'eixo': acao.eixo.nome,
            'prioridade': acao.prioridade,
            'arrecadacao_estimada': acao.arrecadacao_estimada,
            'data_inicio': _iso(acao.data_inicio),
            'data_fim': _iso(acao.data_fim),
            'observacoes': acao.observacoes or '',
            'responsavel': acao.responsavel.nome,
            'status': {'id': acao.status.id, 'nome': acao.status.nome, 'cor': acao.status.cor},
            'somente_leitura': _acao_cancelada(acao),
        }

    @staticmethod
    def mover_status(prefeitura, acao_id, novo_status_id, usuario):
        acao = AcaoRepositorio.buscar_por_prefeitura(prefeitura, acao_id)
        if acao is None or _acao_cancelada(acao):
            return None
        if novo_status_id and str(novo_status_id).isdigit() and str(acao.status_id) != str(novo_status_id):
            status_destino = StatusRepositorio.buscar_por_id(novo_status_id)
            if status_destino is None:
                return False
            acao.status = status_destino
            acao.atualizado_por = usuario
            AcaoRepositorio.salvar(acao)
            return acao, status_destino
        return None

    @staticmethod
    def criar_com_etapas(prefeitura, usuario, data, is_json=True, post_lists=None):
        eixo_id = data.get('eixo')
        acao_catalogo_id = data.get('acao')
        acao_texto_custom = (data.get('novaAcao') or '').strip()
        status_id = data.get('status')
        prioridade = data.get('prioridade')

        if prioridade not in Acao.Status_Prioridade.values:
            raise ErroRegraNegocio('Prioridade inválida.')

        arrecadacao_estimada_raw = str(data.get('arrecadacao_estimada', '0')).strip()
        if not is_json:
            arrecadacao_estimada_raw = arrecadacao_estimada_raw.replace('.', '').replace(',', '.')
        try:
            arrecadacao_estimada = Decimal(arrecadacao_estimada_raw)
        except InvalidOperation:
            arrecadacao_estimada = 0.0

        data_inicio = _converter_data(data.get('dataInicio') or data.get('data_inicio'))
        data_fim = _converter_data(data.get('dataFim') or data.get('data_fim'))
        if not data_inicio or not data_fim:
            raise ErroRegraNegocio('Informe datas válidas.')
        if data_fim < data_inicio:
            raise ErroRegraNegocio('A data de fim não pode ser anterior à data de início.')

        observacoes = (data.get('observacoes') or '').strip() or None

        if acao_catalogo_id and acao_catalogo_id != 'outra':
            modelo = CatalogoRepositorio.buscar_por_id(acao_catalogo_id)
            if modelo is None:
                raise ErroRegraNegocio('Ação do catálogo não encontrada.')
            nome_acao, eixo_obj = modelo.nome, modelo.eixo
        else:
            if not acao_texto_custom:
                raise ErroRegraNegocio('Informe o nome da ação.')
            modelo = None
            eixo_obj = EixoRepositorio.buscar_por_id(eixo_id)
            if eixo_obj is None:
                raise ErroRegraNegocio('Eixo não encontrado.')
            nome_acao = acao_texto_custom

        status_obj = (
            StatusRepositorio.buscar_por_id(status_id)
            if status_id else StatusRepositorio.obter_primeiro()
        )
        if status_obj is None:
            raise ErroRegraNegocio('Status não encontrado.')

        cpf_responsavel = data.get('responsavel')
        if cpf_responsavel:
            responsavel = FuncionarioRepositorio.buscar_por_cpf_e_prefeitura(cpf_responsavel, prefeitura)
        elif usuario.prefeitura_id == prefeitura.pk:
            responsavel = usuario
        else:
            responsavel = None
        if responsavel is None:
            raise ErroRegraNegocio('Informe o responsável pela ação entre os funcionários da prefeitura.')

        etapas_validadas = []
        if is_json:
            for item in data.get('etapas', []):
                nome_etapa = item.get('nome') or item.get('etapaNome')
                if not nome_etapa:
                    continue
                resp_etapa = FuncionarioRepositorio.buscar_por_cpf_e_prefeitura(item.get('cpf'), prefeitura)
                if resp_etapa is None:
                    raise ErroRegraNegocio(
                        f'O CPF informado na etapa "{nome_etapa}" não foi encontrado '
                        'entre os funcionários da sua prefeitura.'
                    )
                e_inicio = _converter_data(
                    item.get('inicio') or item.get('data_inicio') or item.get('dataInicio')
                    or item.get('etapaInicio')) or data_inicio
                e_fim = _converter_data(
                    item.get('fim') or item.get('data_fim') or item.get('dataFim')
                    or item.get('etapaFim')) or data_fim
                if e_fim < e_inicio:
                    raise ErroRegraNegocio('A data de fim da etapa não pode ser anterior à data de início.')
                if not (e_inicio >= data_inicio and e_fim <= data_fim):
                    raise ErroRegraNegocio('As datas da etapa devem estar dentro do período da ação.')
                etapas_validadas.append({
                    'nome': nome_etapa,
                    'responsavel': resp_etapa,
                    'data_inicio': e_inicio,
                    'data_fim': e_fim,
                    'prioridade': item.get('prioridade') or '',
                    'observacoes': item.get('observacoes', ''),
                })
        else:
            post_lists = post_lists or {}
            nomes = post_lists.get('nomes', [])
            inicios = post_lists.get('inicios', [])
            fims = post_lists.get('fims', [])
            prioridades = post_lists.get('prioridades', [])
            obs_list = post_lists.get('obs_list', [])

            for i, nome in enumerate(nomes):
                if not nome.strip():
                    continue
                e_inicio = (_converter_data(inicios[i]) if i < len(inicios) else None) or data_inicio
                e_fim = (_converter_data(fims[i]) if i < len(fims) else None) or data_fim
                if e_fim < e_inicio:
                    raise ErroRegraNegocio('A data de fim da etapa não pode ser anterior à data de início.')
                if not (e_inicio >= data_inicio and e_fim <= data_fim):
                    raise ErroRegraNegocio('As datas da etapa devem estar dentro do período da ação.')
                etapas_validadas.append({
                    'nome': nome.strip(),
                    'responsavel': responsavel,
                    'data_inicio': e_inicio,
                    'data_fim': e_fim,
                    'prioridade': prioridades[i] if i < len(prioridades) else '',
                    'observacoes': obs_list[i] if i < len(obs_list) else '',
                })

        try:
            with transaction.atomic():
                nova_acao = AcaoRepositorio.criar(
                    prefeitura=prefeitura,
                    nome=nome_acao,
                    eixo=eixo_obj,
                    modelo=modelo,
                    responsavel=responsavel,
                    status=status_obj,
                    prioridade=prioridade,
                    arrecadacao_estimada=arrecadacao_estimada,
                    data_inicio=data_inicio,
                    data_fim=data_fim,
                    observacoes=observacoes,
                    criado_por=usuario,
                    atualizado_por=usuario,
                )
                for dados_etapa in etapas_validadas:
                    EtapaRepositorio.criar(
                        acao=nova_acao,
                        criado_por=usuario,
                        atualizado_por=usuario,
                        **dados_etapa,
                    )
                return nova_acao
        except IntegrityError:
            raise ErroRegraNegocio('Não foi possível salvar a ação. Tente novamente.', status=409)

    @classmethod
    def obter_detalhes(cls, prefeitura, acao_id):
        acao = AcaoRepositorio.buscar_por_prefeitura(prefeitura, acao_id)
        if acao is None:
            raise ErroRegraNegocio('Ação não encontrada.', status=404)
        etapas = EtapaRepositorio.listar_por_acao(acao)
        return {
            'acao': cls.serializar(acao),
            'etapas': [EtapaService.serializar(e) for e in etapas],
        }

    @classmethod
    def editar(cls, prefeitura, acao_id, data, usuario):
        acao = AcaoRepositorio.buscar_por_prefeitura(prefeitura, acao_id)
        if acao is None:
            raise ErroRegraNegocio('Ação não encontrada.', status=404)
        if _acao_cancelada(acao):
            raise ErroRegraNegocio('Uma ação cancelada não pode ser editada.', status=403)

        prioridade = data.get('prioridade')
        if prioridade not in Acao.Status_Prioridade.values:
            raise ErroRegraNegocio('Prioridade inválida.')

        try:
            arrecadacao_estimada = Decimal(str(data.get('arrecadacao_estimada', '')).strip())
        except InvalidOperation:
            raise ErroRegraNegocio('Arrecadação estimada inválida.')
        if not arrecadacao_estimada.is_finite() or arrecadacao_estimada < 0:
            raise ErroRegraNegocio('Arrecadação estimada inválida.')

        data_inicio = _converter_data(data.get('data_inicio'))
        data_fim = _converter_data(data.get('data_fim'))
        if not data_inicio or not data_fim:
            raise ErroRegraNegocio('Informe datas válidas.')
        if data_fim < data_inicio:
            raise ErroRegraNegocio('A data de fim não pode ser anterior à data de início.')
        if EtapaRepositorio.existe_fora_periodo(acao, data_inicio, data_fim):
            raise ErroRegraNegocio('O período da ação não pode excluir datas de uma etapa existente.')

        acao.prioridade = prioridade
        acao.arrecadacao_estimada = arrecadacao_estimada
        acao.data_inicio = data_inicio
        acao.data_fim = data_fim
        acao.observacoes = (data.get('observacoes') or '').strip() or None
        acao.atualizado_por = usuario
        AcaoRepositorio.salvar(acao)
        return cls.serializar(acao)

    @staticmethod
    def excluir(prefeitura, acao_id):
        acao = AcaoRepositorio.buscar_por_prefeitura(prefeitura, acao_id)
        if acao is None:
            raise ErroRegraNegocio('Ação não encontrada.', status=404)
        if _acao_cancelada(acao):
            raise ErroRegraNegocio('Uma ação cancelada não pode ser excluída.', status=403)

        try:
            with transaction.atomic():
                EtapaRepositorio.excluir_todas_da_acao(acao)
                AcaoRepositorio.excluir(acao)
        except ProtectedError:
            raise ErroRegraNegocio(
                'Não foi possível excluir a ação porque ela está vinculada a outros registros.',
                status=409,
            )