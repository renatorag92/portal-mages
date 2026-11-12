from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Consultoria, Prefeitura, SolicitacaoRedefinicaoSenha


class PasswordResetRequestTests(TestCase):
    def setUp(self):
        self.prefeitura = Prefeitura.objects.create(
            cnpj='12345678000195',
            nome_juridico='Prefeitura Central',
            nome_fantasia='Prefeitura Central',
            endereco='Rua Central, 1',
        )
        self.consultoria = Consultoria.objects.create(
            cnpj='98765432000110',
            nome_juridico='Consultoria Central',
            nome_fantasia='Consultoria Central',
            endereco='Rua Consultoria, 2',
        )
        self.prefeitura.consultoria = self.consultoria
        self.prefeitura.save(update_fields=['consultoria'])

        funcionario_model = get_user_model()
        self.consultor = funcionario_model.objects.create_user(
            username='11111111111',
            password='test-password',
            nome='Consultor Responsável',
            consultoria=self.consultoria,
            tem_acesso=True,
            primeiro_acesso=False,
        )
        self.funcionario = funcionario_model.objects.create_user(
            username='22222222222',
            password='old-password',
            nome='Pessoa Solicitante',
            prefeitura=self.prefeitura,
            tem_acesso=True,
            primeiro_acesso=False,
        )
        self.request_url = reverse('solicitar_redefinicao_senha')

    def test_login_forgot_password_creates_request_and_notifies_consultor_by_name(self):
        login_page = self.client.get(reverse('login'))
        self.assertContains(login_page, 'Esqueci minha senha')
        self.assertContains(login_page, 'forgotPasswordForm')

        response = self.client.post(self.request_url, {'cpf': '222.222.222-22'})

        self.assertRedirects(response, reverse('login'))
        self.assertTrue(
            SolicitacaoRedefinicaoSenha.objects.filter(
                funcionario=self.funcionario,
                pendente=True,
            ).exists()
        )
        self.client.force_login(self.consultor)
        page = self.client.get(reverse('gerenciar_funcionario'))

        self.assertContains(page, 'Pessoa Solicitante deseja alterar a senha.')
        self.assertContains(page, 'Pessoa Solicitante')
        self.assertContains(page, 'Solicitada')
        self.assertContains(
            page,
            reverse('gerar_senha_funcionario', args=[self.funcionario.pk]),
        )

    def test_repeated_requests_keep_one_pending_notification(self):
        for _ in range(2):
            self.client.post(self.request_url, {'cpf': self.funcionario.username})

        self.assertEqual(
            SolicitacaoRedefinicaoSenha.objects.filter(
                funcionario=self.funcionario,
                pendente=True,
            ).count(),
            1,
        )

    def test_password_request_can_be_marked_read_per_consultor(self):
        self.client.post(self.request_url, {'cpf': self.funcionario.username})
        solicitacao = SolicitacaoRedefinicaoSenha.objects.get(
            funcionario=self.funcionario,
            pendente=True,
        )
        self.client.force_login(self.consultor)
        refresh_url = reverse('atualizar_notificacoes')

        unread = self.client.get(refresh_url).json()
        item = next(
            item for item in unread['notifications']
            if item['alvo_tipo'] == 'solicitacao_senha'
        )
        self.assertFalse(item['lida'])
        self.assertEqual(unread['unread_count'], 1)
        self.assertEqual(
            item['destino_url'],
            reverse('gerenciar_funcionario'),
        )

        response = self.client.post(
            reverse('marcar_solicitacao_senha_lida', args=[solicitacao.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200, response.get('Location'))
        self.assertEqual(response.json(), {'success': True})
        read = self.client.get(refresh_url).json()
        item = next(
            item for item in read['notifications']
            if item['alvo_tipo'] == 'solicitacao_senha'
        )
        self.assertTrue(item['lida'])
        self.assertEqual(read['unread_count'], 0)
        self.assertNotContains(
            self.client.get(reverse('gerenciar_funcionario')),
            'notification-mark-read-button',
        )

    def test_only_the_consultor_who_reads_the_request_clears_its_unread_badge(self):
        self.client.post(self.request_url, {'cpf': self.funcionario.username})
        outro_consultor = get_user_model().objects.create_user(
            username='33333333333',
            password='test-password',
            nome='Outro Consultor',
            consultoria=self.consultoria,
            tem_acesso=True,
            primeiro_acesso=False,
        )
        self.client.force_login(self.consultor)
        solicitacao = SolicitacaoRedefinicaoSenha.objects.get(
            funcionario=self.funcionario,
            pendente=True,
        )
        self.client.post(
            reverse('marcar_solicitacao_senha_lida', args=[solicitacao.pk]),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.client.force_login(outro_consultor)
        response = self.client.get(reverse('atualizar_notificacoes'))

        self.assertEqual(response.json()['unread_count'], 1)

    def test_generated_password_resolves_request_and_requires_first_login_change(self):
        self.client.post(self.request_url, {'cpf': self.funcionario.username})
        self.client.force_login(self.consultor)

        response = self.client.post(
            reverse('gerar_senha_funcionario', args=[self.funcionario.pk]),
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.funcionario.refresh_from_db()
        self.assertTrue(self.funcionario.primeiro_acesso)
        self.assertTrue(self.funcionario.has_usable_password())
        self.assertFalse(
            SolicitacaoRedefinicaoSenha.objects.filter(
                funcionario=self.funcionario,
                pendente=True,
            ).exists()
        )
        self.assertContains(response, 'Provisória')
        self.assertContains(response, 'Nova senha provisória')

    def test_unknown_or_ineligible_cpf_gets_generic_response_without_request(self):
        response = self.client.post(self.request_url, {'cpf': '99999999999'})

        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], reverse('login'))
        self.assertContains(
            self.client.get(reverse('login')),
            'Se o CPF informado estiver cadastrado com acesso, os consultores serão notificados.',
        )
        self.assertFalse(SolicitacaoRedefinicaoSenha.objects.exists())
