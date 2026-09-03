from django.db import models

class Status_eixo(models.TextChoices):
    CADASTRO_TRIBUTARIO = 'cadastro_tributario', 'Cadastro Tributário'
    FISCALIZACAO_TRIBUTARIA = 'fiscalizacao_tributaria', 'Fiscalização Tributária'
    ARRECADACAO_E_COBRANCA = 'arrecadacao_e_cobranca', 'Arrecadação e Cobrança'
    MODERNIZACAO_E_TECNOLOGIA = 'modernizacao_e_tecnologia', 'Modernização e Tecnologia'
    GOVERNANCA_E_LEGISLACAO = 'governanca_e_legislacao', 'Governança e Legislação'       

class Status_status(models.TextChoices):
        PLANEJADO = 'planejado', 'Planejado'
        EM_PREPARACAO = 'preparacao', 'Em preparação'
        EM_EXECUCAO = 'execucao', 'Em execução'
        EM_VALIDACAO = 'validacao', 'Em validação'
        CONCLUIDO = 'concluido', 'Concluído'
        CANCELADO = 'cancelado', 'Cancelado'

class Status_prioridade(models.TextChoices):
        BAIXA = 'baixa', 'Baixa'
        MEDIA = 'media', 'Média'
        ALTA = 'alta', 'Alta'