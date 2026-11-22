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
    def test_id_e_sequencial_por_prefeitura(self):
        segunda = Acao.objects.create(
            prefeitura=self.prefeitura, nome='Segunda', eixo=self.eixo,
            status=self.status_planejado, responsavel=self.responsavel,
            prioridade='Média', data_inicio=date(2026, 1, 1), data_fim=date(2026, 2, 1),
            arrecadacao_estimada=Decimal('0'))
        self.assertEqual(self.acao.id, 1)
        self.assertEqual(segunda.id, 2)

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


class GerenciarCatalogoTests(BaseCenario):
    def setUp(self):
        super().setUp()
        self.item_catalogo = AcaoCatalogo.objects.create(
            nome='Ação pré-cadastrada', eixo=self.eixo)
        self.consultor = Funcionario.objects.create(
            username='12345678906', nome='Consultor',
            consultoria=self.consultoria, tem_acesso=True)
        self.usuario_prefeitura = Funcionario.objects.create(
            username='12345678907', nome='Usuário da prefeitura',
            prefeitura=self.prefeitura, tem_acesso=True)

    def test_consultor_acessa_gerenciamento_de_acoes(self):
        self.client.force_login(self.consultor)

        resposta = self.client.get(reverse('gerenciar_catalogo'))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'Gerenciar Ações')
        self.assertContains(resposta, 'Ação pré-cadastrada')

    def test_consultor_edita_acao_pre_cadastrada(self):
        self.client.force_login(self.consultor)

        resposta = self.client.post(
            reverse('editar_catalogo', args=[self.item_catalogo.pk]),
            {'nome': 'Ação atualizada', 'eixo': self.eixo.pk},
        )

        self.assertRedirects(resposta, reverse('gerenciar_catalogo'))
        self.item_catalogo.refresh_from_db()
        self.assertEqual(self.item_catalogo.nome, 'Ação atualizada')

    def test_consultor_altera_eixo_da_acao(self):
        outro_eixo = Eixo.objects.create(nome='Saúde')
        self.client.force_login(self.consultor)

        resposta = self.client.post(
            reverse('editar_catalogo', args=[self.item_catalogo.pk]),
            {'nome': self.item_catalogo.nome, 'eixo': outro_eixo.pk},
        )

        self.assertRedirects(resposta, reverse('gerenciar_catalogo'))
        self.item_catalogo.refresh_from_db()
        self.assertEqual(self.item_catalogo.eixo_id, outro_eixo.pk)

    def test_lapis_abre_edicao_na_linha_da_acao(self):
        self.client.force_login(self.consultor)

        resposta = self.client.get(reverse('editar_catalogo', args=[self.item_catalogo.pk]))

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, 'name="nome"')
        self.assertContains(resposta, 'name="eixo"')
        self.assertContains(resposta, 'Cadastrar ação no catálogo')

    def test_acao_em_uso_nao_pode_ser_excluida(self):
        self.acao.modelo = self.item_catalogo
        self.acao.save()
        self.client.force_login(self.consultor)

        resposta = self.client.post(reverse('excluir_catalogo', args=[self.item_catalogo.pk]))

        self.assertRedirects(resposta, reverse('gerenciar_catalogo'))
        self.assertTrue(AcaoCatalogo.objects.filter(pk=self.item_catalogo.pk).exists())
        self.acao.refresh_from_db()
        self.assertEqual(self.acao.modelo_id, self.item_catalogo.pk)

    def test_exclusao_de_acao_em_uso_fica_desabilitada_na_lista(self):
        self.acao.modelo = self.item_catalogo
        self.acao.save()
        self.client.force_login(self.consultor)

        resposta = self.client.get(reverse('gerenciar_catalogo'))

        self.assertContains(resposta, 'ação em uso')
        self.assertContains(resposta, 'disabled')

    def test_consultor_filtra_catalogo_por_nome_e_eixo(self):
        outro_eixo = Eixo.objects.create(nome='Saúde')
        outra_acao = AcaoCatalogo.objects.create(nome='Ação de saúde', eixo=outro_eixo)
        self.client.force_login(self.consultor)

        resposta = self.client.get(
            reverse('gerenciar_catalogo'),
            {'nome': 'saúde', 'eixo': outro_eixo.pk},
        )

        self.assertEqual(resposta.status_code, 200)
        self.assertContains(resposta, outra_acao.nome)
        self.assertNotContains(resposta, self.item_catalogo.nome)

    def test_usuario_da_prefeitura_nao_acessa_gerenciamento_de_acoes(self):
        self.client.force_login(self.usuario_prefeitura)

        resposta = self.client.get(reverse('gerenciar_catalogo'))

        self.assertEqual(resposta.status_code, 302)


class ExclusaoConsultorTests(BaseCenario):
    def criar_consultor(self, cpf, nome):
        return Funcionario.objects.create(
            username=cpf,
            nome=nome,
            consultoria=self.consultoria,
            tem_acesso=True,
        )

    def test_nunca_exclui_um_consultor_quando_somente_existirem_dois(self):
        consultor_1 = self.criar_consultor('12345678908', 'Consultor 1')
        consultor_2 = self.criar_consultor('12345678909', 'Consultor 2')
        self.client.force_login(consultor_1)

        resposta = self.client.post(
            reverse('excluir_funcionario', args=[consultor_2.pk])
        )

        self.assertRedirects(resposta, reverse('gerenciar_funcionario'))
        self.assertTrue(Funcionario.objects.filter(pk=consultor_2.pk).exists())

    def test_com_tres_consultores_permite_excluir_um(self):
        consultor_1 = self.criar_consultor('12345678910', 'Consultor 1')
        consultor_2 = self.criar_consultor('12345678911', 'Consultor 2')
        consultor_3 = self.criar_consultor('12345678912', 'Consultor 3')
        self.client.force_login(consultor_3)

        resposta = self.client.post(
            reverse('excluir_funcionario', args=[consultor_1.pk])
        )

        self.assertRedirects(resposta, reverse('gerenciar_funcionario'))
        self.assertFalse(Funcionario.objects.filter(pk=consultor_1.pk).exists())
        self.assertTrue(Funcionario.objects.filter(pk=consultor_2.pk).exists())

    def test_com_tres_consultores_a_interface_esconde_a_exclusao_apos_reduzir_a_dois(self):
        consultor_1 = self.criar_consultor('12345678913', 'Consultor 1')
        consultor_2 = self.criar_consultor('12345678914', 'Consultor 2')
        consultor_3 = self.criar_consultor('12345678915', 'Consultor 3')
        consultor_1.delete()
        self.client.force_login(consultor_2)

        resposta = self.client.get(reverse('gerenciar_funcionario'))

        self.assertContains(resposta, consultor_3.nome)
        self.assertNotContains(
            resposta,
            reverse('excluir_funcionario', args=[consultor_3.pk]),
        )


class CancelamentoTests(BaseCenario):
    def test_acao_cancelada_e_somente_leitura(self):
        self.acao.status = self.status_cancelado
        self.acao.save()
        from actions.views import _acao_cancelada
        self.assertTrue(_acao_cancelada(self.acao))