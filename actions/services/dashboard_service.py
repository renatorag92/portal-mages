from collections import Counter
from datetime import date, timedelta
from decimal import Decimal
from django.utils.text import slugify

from ..models import Status
from ..repositories.acao_repositorio import AcaoRepositorio
from ..repositories.catalogo_repositorio import CatalogoRepositorio
from ..repositories.eixo_repositorio import EixoRepositorio
from ..repositories.status_repositorio import StatusRepositorio
from .status_service import StatusService

PALETA_EIXOS = ['#3e4a89', '#2e8b57', '#b5b94a', '#7b3f9e', '#d98a1f', '#c0392b', '#2aa198', '#8a8f99']
DIAS_PROXIMO = 15
DIAS_URGENTE = 7


class DashboardService:
    @staticmethod
    def montar_quadro_kanban(prefeitura):
        todos_status = StatusRepositorio.listar_para_kanban(prefeitura)
        acoes = list(AcaoRepositorio.listar_para_kanban(prefeitura))

        for st in todos_status:
            st.acoes_lista = [a for a in acoes if a.status_id == st.id]
            st.cor_para_edicao = StatusService.cor_para_edicao(st)

        eixos_raiz = EixoRepositorio.listar_raiz_com_subeixos()
        acoes_catalogo_list = [
            {'id': a.id, 'nome': a.nome, 'eixo_id': a.eixo_id}
            for a in CatalogoRepositorio.listar_todos()
        ]
        return {
            'prefeitura': prefeitura,
            'kanban': todos_status,
            'eixos_raiz': eixos_raiz,
            'acoes_catalogo_list': acoes_catalogo_list,
        }

    @staticmethod
    def _moeda(valor):
        texto = f'{valor:,.2f}'.replace(',', 'X').replace('.', ',').replace('X', '.')
        return f'R$ {texto}'

    @staticmethod
    def _gradiente(fatias):
        total = sum(valor for _, valor in fatias)
        if not total:
            return 'conic-gradient(#e5e2d9 0 100%)'
        partes, inicio = [], 0.0
        for cor, valor in fatias:
            if not valor:
                continue
            fim = inicio + float(valor) / float(total) * 100
            partes.append(f'{cor} {inicio:.2f}% {fim:.2f}%')
            inicio = fim
        return 'conic-gradient(' + ', '.join(partes) + ')'

    @classmethod
    def _distribuicao(cls, itens):
        total = sum(valor for _, _, valor, _ in itens)
        legenda = [
            {
                'nome': nome,
                'cor': cor,
                'pct': round(valor / total * 100) if total else 0,
                'texto': texto,
            }
            for nome, cor, valor, texto in itens
        ]
        return {
            'gradiente': cls._gradiente([(cor, valor) for _, cor, valor, _ in itens]),
            'legenda': legenda,
            'vazio': total == 0,
        }

    @classmethod
    def gerar_metricas(cls, prefeitura):
        hoje = date.today()
        limite_proximas = hoje + timedelta(days=DIAS_PROXIMO)

        acoes = list(AcaoRepositorio.listar_para_dashboard(prefeitura))
        ativas = [
            a for a in acoes
            if a.status.chave != Status.Chave.CANCELADO and a.status.chave in Status.ATIVAS
        ]

        total_ativas = len(ativas)
        total_atrasadas = sum(1 for a in ativas if a.data_fim < hoje)
        total_execucao = sum(1 for a in ativas if a.status.chave == Status.Chave.EM_EXECUCAO)
        arrecadacao_estimada_total = sum(a.arrecadacao_estimada for a in ativas)

        contagem_status = Counter(a.status_id for a in acoes)
        maior = max(contagem_status.values(), default=0)
        barras = []
        for status in StatusRepositorio.listar_ordenados():
            total = contagem_status.get(status.id, 0)
            barras.append({
                'nome': status.nome,
                'cor': status.cor,
                'total': total,
                'pct': round(total / maior * 100) if maior else 0,
            })

        por_eixo = {}
        for a in ativas:
            nome = a.eixo.nome if a.eixo_id else 'Sem eixo'
            qtd, arrecadacao_estimada = por_eixo.get(nome, (0, Decimal('0')))
            por_eixo[nome] = (qtd + 1, arrecadacao_estimada + a.arrecadacao_estimada)

        eixos = sorted(por_eixo.items(), key=lambda item: item[1][0], reverse=True)
        cores = [PALETA_EIXOS[i % len(PALETA_EIXOS)] for i in range(len(eixos))]
        fatias_qtd = [(nome, cor, qtd, str(qtd)) for (nome, (qtd, _)), cor in zip(eixos, cores)]
        fatias_arrecadacao_estimada = [
            (nome, cor, arrecadacao_estimada, cls._moeda(arrecadacao_estimada))
            for (nome, (_, arrecadacao_estimada)), cor in zip(eixos, cores)
        ]

        vence_logo = sum(1 for a in ativas if hoje <= a.data_fim <= limite_proximas)
        no_prazo = total_ativas - total_atrasadas - vence_logo
        fatias_prazo = [
            ('Atrasadas', '#c0392b', total_atrasadas, str(total_atrasadas)),
            (f'Vence em até {DIAS_PROXIMO} dias', '#e0b400', vence_logo, str(vence_logo)),
            ('No prazo', '#2e8b57', no_prazo, str(no_prazo)),
        ]

        proximas_acoes = sorted(
            (a for a in ativas if hoje <= a.data_fim <= limite_proximas),
            key=lambda a: (a.data_fim, a.pk),
        )
        atrasadas_acoes = sorted(
            (a for a in ativas if a.data_fim < hoje),
            key=lambda a: (a.data_fim, a.pk),
        )

        def preparar_acao(a, nivel):
            return {
                'id': a.id,
                'eixo': a.eixo.nome if a.eixo_id else '—',
                'nome_acao': a.nome,
                'responsavel': a.responsavel.nome,
                'data': a.data_fim,
                'nivel': nivel,
                'status': a.status.nome,
                'prioridade': a.prioridade or '—',
                'prioridade_classe': slugify(a.prioridade),
            }

        proximas = []
        for a in proximas_acoes:
            dias = (a.data_fim - hoje).days
            nivel = (
                'vermelho' if dias <= 1
                else 'amarelo' if dias <= DIAS_URGENTE
                else 'verde'
            )
            proximas.append(preparar_acao(a, nivel))

        atrasadas = [preparar_acao(a, 'vermelho') for a in atrasadas_acoes]

        return {
            'total_ativas': total_ativas,
            'total_execucao': total_execucao,
            'total_atrasadas': total_atrasadas,
            'arrecadacao_estimada_total': cls._moeda(arrecadacao_estimada_total),
            'barras': barras,
            'distribuicoes': [
                {'chave': 'visao_geral', 'dados': cls._distribuicao(fatias_qtd)},
                {'chave': 'por_eixo', 'dados': cls._distribuicao(fatias_arrecadacao_estimada)},
                {'chave': 'por_prazo', 'dados': cls._distribuicao(fatias_prazo)},
            ],
            'proximas_acoes': proximas,
            'atrasadas_acoes': atrasadas,
            'dias_proximo': DIAS_PROXIMO,
        }