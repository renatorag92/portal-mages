from django.core.management.base import BaseCommand
from django.db import transaction

from actions.models import AcaoCatalogo, Eixo, Status

# (nome, pai). O pai precisa vir antes do filho na lista.
EIXOS = [
    ('Cadastro Tributário', None),
    ('Cadastro Imobiliário', 'Cadastro Tributário'),
    ('Cadastro Mobiliário', 'Cadastro Tributário'),
    ('Fiscalização Tributária', None),
    ('Arrecadação e Cobrança', None),
    ('Modernização e Tecnologia', None),
    ('Governança e Legislação', None),
]

# (nome, cor hex, nome da cor exibido na edição, ordem da coluna)
STATUS = [
    ('Planejado', '#0000ff', 'azul', 1),
    ('Preparação', '#00ffff', 'ciano', 2),
    ('Em execução', '#ffff00', 'amarelo', 3),
    ('Em validação', '#800080', 'roxo', 4),
    ('Concluído', '#008000', 'verde', 5),
    ('Suspenso', '#808080', 'cinza', 6),
    ('Cancelado', '#ff0000', 'vermelho', 7),
]

CATALOGO = {
    'Cadastro Imobiliário': [
        'Atualizar cadastro imobiliário urbano (georreferenciamento e pesquisa cadastral)',
        'Integrar-se com o SINTER',
        'Identificar imóveis não cadastrados (mesmo que individualmente)',
        'Revisar áreas construídas dos imóveis (no mínimo os maiores)',
        'Identificar imóveis com construção não declarada (no mínimo os maiores)',
        'Identificar novos loteamentos urbanos',
        'Atualizar cadastro de contribuintes do IPTU',
        'Criar rotina anual de atualização cadastral',
        'Integrar cadastro com dados de outras secretarias',
        'Utilizar dados do cartório',
        'Identificar imóveis isentos ou imunes incorretamente',
        'Implantar cadastro territorial multifinalitário',
        'Criar política de incentivo à atualização do cadastro',
        'Fazer varredura dos imóveis com cadastro sem CPF/CNPJ do responsável',
        'Conferir os imóveis com endereço incompleto ou sem numeração',
        'Revisar os imóveis com isenção ativa há mais de 3 anos sem recadastramento documental',
        'Implantar rotina mensal de recebimento, da Secretaria de Obras, de informações sobre alvarás, habite-se, demolições e reformas',
        'Mapear loteamentos recentes ainda não refletidos integralmente no cadastro',
    ],
    'Cadastro Mobiliário': [
        'Atualizar cadastro de empresas',
        'Revisar CNAE das empresas cadastradas',
        'Identificar empresas ativas na Receita Federal não cadastradas',
        'Criar rotina de revisão cadastral de MEI',
        'Rever dimensões dos imóveis (principalmente os maiores contribuintes)',
        'Criar cadastro separado dos 30 maiores contribuintes do ISS',
        'Criar cadastro separado dos 50 maiores contribuintes do TLF',
        'Levantar contribuintes com inscrição ativa, mas sem emissão de nota e sem recolhimento por longo período',
        'Revisar cadastro de contribuintes autônomos e sociedades de profissionais para verificar se mantêm os requisitos do enquadramento',
    ],
    'Fiscalização Tributária': [
        'Cruzar NFS-e com PGDAS',
        'Cruzar NFS-e com retenções de ISS',
        'Fiscalizar empresas de construção civil',
        'Fiscalizar serviços médicos',
        'Fiscalizar laboratórios e clínicas',
        'Fiscalizar instituições financeiras',
        'Fiscalizar cartórios',
        'Fiscalizar cooperativas de crédito',
        'Fiscalizar serviços de telecomunicações',
        'Fiscalizar empresas de energia (ex.: cessão de uso de postes)',
        'Fiscalizar serviços de engenharia',
        'Fiscalizar prestadores de serviços ao município',
        'Fiscalizar o ISS retido pelo município',
        'Fiscalizar o IRRF retido pelo município',
        'Fiscalizar prestadores de serviços de tecnologia',
        'Fiscalizar empresas de transporte',
        'Fiscalizar empresas de limpeza urbana',
        'Fiscalizar academias e escolas particulares',
        'Criar monitoramento de grandes contribuintes',
        'Criar rotina de fiscalização periódica',
        'Implantar plano anual de fiscalização',
        'Criar rotina de verificação de notas canceladas e substituídas em excesso',
        'Listar contribuintes com queda brusca de emissão de NFS-e e analisar caso a caso',
        'Criar operação específica "tomadores relevantes": prefeitura, câmara, fundo de saúde, fundo de assistência, grandes obras, cooperativas e bancos',
        'Criar malha básica: empresa com nota emitida e sem recolhimento, empresa com recolhimento sem nota, empresa com retenção incompatível',
    ],
    'Arrecadação e Cobrança': [
        'Atualizar base da dívida ativa',
        'Identificar maiores devedores',
        'Implantar cobrança administrativa',
        'Criar rotina de notificação de débitos',
        'Revisar parcelamentos ativos',
        'Monitorar inadimplência tributária (principalmente dos grandes contribuintes)',
        'Implantar serviço de proteção ao crédito da dívida ativa',
        'Implantar cobrança eletrônica',
        'Criar política de cobrança de grandes devedores',
        'Implantar programa de regularização fiscal',
        'Monitorar arrecadação mensal',
        'Revisar débitos prescritos',
        'Priorizar execução fiscal de grandes devedores',
        'Criar rotina de cobrança preventiva',
        'Implantar acompanhamento de parcelamentos',
        'Criar sistema de controle da dívida ativa',
        'Revisar cadastro de devedores',
        'Criar ranking de arrecadação tributária (por contribuinte)',
        'Separar a dívida ativa em 4 grupos: até R$ 500, de R$ 500 a R$ 5 mil, de R$ 5 mil a R$ 20 mil e acima disso',
        'Criar lista dos 100 maiores devedores',
        'Criar rotina mensal de envio de aviso de débito antes da inscrição ou cobrança mais dura',
        'Relacionar débitos de empresas que contratam com o poder público',
        'Criar rotina de cobrança preventiva para tributos de vencimento periódico',
        'Atualizar cadastro de telefone, e-mail e endereço dos maiores devedores',
    ],
    'Modernização e Tecnologia': [
        'Implantar painel simples de acompanhamento da arrecadação mensal por tributo',
        'Treinar equipe para uso da NFS-e nacional',
        'Criar banco de dados fiscal',
        'Implantar BI tributário',
        'Criar cruzamento automatizado de dados',
        'Implantar sistema de inteligência fiscal (malhas fiscais com dados da NFS-e, arrecadação e outros dados)',
        'Implantar processo administrativo digital',
        'Disponibilizar serviços on-line',
        'Criar sistema de monitoramento da arrecadação',
        'Integrar sistemas municipais',
        'Criar dashboard de fiscalização',
        'Implantar sistema de acompanhamento de metas',
        'Implantar base de dados geográficos',
        'Integrar base tributária com planejamento urbano',
        'Implantar sistema de análise fiscal',
        'Criar rotina de exportação mensal dos dados do sistema tributário para análise externa',
        'Implantar sistema de comunicação virtual por WhatsApp oficial para avisos e interação com o contribuinte',
    ],
    'Governança e Legislação': [
        'Revisar Código Tributário Municipal',
        'Revisar procedimentos de lançamento tributário',
        'Criar norma de rotina de fiscalização tributária',
        'Criar normas de rotina de arrecadação tributária',
        'Implantar planejamento anual da tributação',
        'Criar indicadores de desempenho do setor',
        'Criar rotina de reuniões de gestão tributária',
        'Atualizar Planta Genérica de Valores',
        'Regulamentar procedimentos tributários',
        'Criar política de gestão tributária',
        'Adequar legislação à reforma tributária',
        'Criar programa de capacitação em legislação da equipe',
        'Adequar a estrutura organizacional',
        'Revisar a lei de estruturação da carreira',
    ],
}


class Command(BaseCommand):
    help = 'Carrega eixos, status e catálogo de ações. Pode ser executado quantas vezes quiser.'

    @transaction.atomic
    def handle(self, *args, **options):
        novos = {'eixos': 0, 'status': 0, 'catalogo': 0}

        eixos = {}
        for nome, pai in EIXOS:
            eixo, criado = Eixo.objects.get_or_create(
                nome=nome,
                defaults={'pai': eixos[pai] if pai else None},
            )
            eixos[nome] = eixo
            novos['eixos'] += criado

        for nome, cor, cor_nome, ordem in STATUS:
            _, criado = Status.objects.get_or_create(
                nome=nome,
                defaults={'cor': cor, 'cor_nome': cor_nome, 'ordem': ordem},
            )
            novos['status'] += criado

        for eixo_nome, acoes in CATALOGO.items():
            for nome in acoes:
                _, criado = AcaoCatalogo.objects.get_or_create(
                    nome=nome,
                    defaults={'eixo': eixos[eixo_nome], 'ativa': True},
                )
                novos['catalogo'] += criado

        self.stdout.write(self.style.SUCCESS(
            f"Dados iniciais carregados. Criados agora: "
            f"{novos['eixos']} eixos, {novos['status']} status, {novos['catalogo']} ações do catálogo."
        ))