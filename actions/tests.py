from datetime import date
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse

from actions.models import Acao, AcaoCatalogo, Consultoria, Eixo, Funcionario, Prefeitura, Status


class BaseCenario(TestCase):
    def setUp(self):
        self.consultoria = Consultoria.objects.create(
            cnpj='00000000000100', nome_juridico='Consultoria LTDA',
            nome_fantasia='Consultoria', endereco='Rua A, 1')
        self.prefeitura = Prefeitura.objects.create(
            cnpj='00000000000191', nome_juridico='Prefeitura Municipal',
            nome_fantasia='Prefeitura', endereco='Praça, 1',
            consultoria=self.consultoria)
        self.outra = Prefeitura.objects.create(
            cnpj='00000000000272', nome_juridico='Outra Prefeitura',
            nome_fantasia='Outra', endereco='Rua B, 2')

        self.eixo = Eixo.objects.create(nome='Governança e Legislação')
        self.status_planejado = Status.objects.create(
            chave='PLANEJADO', nome='Planejado', cor='#0000ff', ordem=1)
        self.status_cancelado = Status.objects.create(
            chave='CANCELADO', nome='Cancelado', cor='#ff0000', ordem=7)

        self.responsavel = Funcionario.objects.create(
            username='12345678901', nome='Responsável', prefeitura=self.prefeitura)

        self.acao = Acao.objects.create(
            prefeitura=self.prefeitura, nome='Ação teste', eixo=self.eixo,
            status=self.status_planejado, responsavel=self.responsavel,
            prioridade='Alta', data_inicio=date(2026, 1, 1), data_fim=date(2026, 12, 31),
            arrecadacao_estimada=Decimal('1500.75'))


class RegrasDeNegocioTests(BaseCenario):
    def test_codigo_e_sequencial_por_prefeitura(self):
        segunda = Acao.objects.create(
            prefeitura=self.prefeitura, nome='Segunda', eixo=self.eixo,
            status=self.status_planejado, responsavel=self.responsavel,
            prioridade='Média', data_inicio=date(2026, 1, 1), data_fim=date(2026, 2, 1),
            arrecadacao_estimada=Decimal('0'))
        self.assertEqual(self.acao.codigo, 1)
        self.assertEqual(segunda.codigo, 2)

    def test_fim_antes_do_inicio_e_recusado_pelo_banco(self):
        from django.db import IntegrityError, transaction
        with self.assertRaises(IntegrityError), transaction.atomic():
            Acao.objects.create(
                prefeitura=self.prefeitura, nome='Inválida', eixo=self.eixo,
                status=self.status_planejado, responsavel=self.responsavel,
                prioridade='Baixa', data_inicio=date(2026, 5, 1), data_fim=date(2026, 4, 1),
                arrecadacao_estimada=Decimal('0'))

    def test_arrecadacao_e_gravada_como_decimal(self):
        self.acao.refresh_from_db()
        self.assertEqual(self.acao.arrecadacao_estimada, Decimal('1500.75'))

    def test_cpf_e_normalizado_ao_salvar(self):
        f = Funcionario(username='123.456.789-02', nome='Com máscara', prefeitura=self.prefeitura)
        f.save()
        self.assertEqual(f.username, '12345678902')

    def test_responsavel_precisa_ser_da_mesma_prefeitura(self):
        from django.core.exceptions import ValidationError
        estranho = Funcionario.objects.create(
            username='12345678903', nome='De outra', prefeitura=self.outra)
        self.acao.responsavel = estranho
        with self.assertRaises(ValidationError):
            self.acao.full_clean()

class IsolamentoTests(BaseCenario):
    def setUp(self):
        super().setUp()
        self.secretario_outra = Funcionario.objects.create(
            username='12345678904', nome='Secretário da outra',
            prefeitura=self.outra, tem_acesso=True)
        self.secretario_outra.set_password('senha-teste-123')
        self.secretario_outra.save()

        self.secretario_dona = Funcionario.objects.create(
            username='12345678905', nome='Secretário da dona',
            prefeitura=self.prefeitura, tem_acesso=True)
        self.secretario_dona.set_password('senha-teste-123')
        self.secretario_dona.save()

    def test_usuario_de_outra_prefeitura_nao_acessa_acao(self):
        self.client.login(username='12345678904', password='senha-teste-123')
        resposta = self.client.get(reverse('obter_detalhes_acao', args=[self.acao.id]))
        self.assertEqual(resposta.status_code, 404)

    def test_usuario_da_prefeitura_acessa_propria_acao(self):
        self.client.login(username='12345678905', password='senha-teste-123')
        resposta = self.client.get(reverse('obter_detalhes_acao', args=[self.acao.id]))
        self.assertEqual(resposta.status_code, 200)

class CancelamentoTests(BaseCenario):
    def test_acao_cancelada_e_somente_leitura(self):
        self.acao.status = self.status_cancelado
        self.acao.save()
        from actions.views import _acao_cancelada
        self.assertTrue(_acao_cancelada(self.acao))