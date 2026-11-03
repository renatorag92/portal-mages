from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from .models import Acao, Eixo, Etapa, NotificacaoLida, Prefeitura, Status


class NotificationCenterTests(TestCase):
    def setUp(self):
        self.prefeitura = Prefeitura.objects.create(
            cnpj='12345678000195',
            nome_juridico='Prefeitura Central',
            nome_fantasia='Prefeitura Central',
            endereco='Rua Central, 1',
        )
        self.user = get_user_model().objects.create_user(
            username='12345678901',
            password='test-password',
            nome='Responsável',
            prefeitura=self.prefeitura,
            tem_acesso=True,
            primeiro_acesso=False,
        )
        self.client.force_login(self.user)
        self.eixo = Eixo.objects.create(nome='Mobilidade')
        self.status = Status.objects.create(nome='Em execução')
        self.hoje = timezone.localdate()

    def criar_acao(self, nome, data_fim, status=None, prefeitura=None):
        return Acao.objects.create(
            prefeitura=prefeitura or self.prefeitura,
            nome=nome,
            eixo=self.eixo,
            prioridade='Média',
            data_inicio=min(self.hoje, data_fim),
            data_fim=data_fim,
            custo=0,
            status=status or self.status,
            responsavel=self.user,
        )

    def test_lists_overdue_and_approaching_actions_but_not_closed_or_distant_ones(self):
        self.criar_acao('Ação atrasada', self.hoje - timedelta(days=2))
        self.criar_acao('Ação próxima', self.hoje + timedelta(days=4))
        self.criar_acao('Ação distante', self.hoje + timedelta(days=8))
        concluido = Status.objects.create(nome='Concluído')
        self.criar_acao('Ação concluída', self.hoje + timedelta(days=2), concluido)

        outra_prefeitura = Prefeitura.objects.create(
            cnpj='98765432000110',
            nome_juridico='Outra Prefeitura',
            nome_fantasia='Outra Prefeitura',
            endereco='Rua Secundária, 2',
        )
        self.criar_acao(
            'Ação de outra prefeitura',
            self.hoje + timedelta(days=1),
            prefeitura=outra_prefeitura,
        )

        response = self.client.get(reverse('kanban'))

        self.assertEqual(response.status_code, 200)
        notificacoes = response.context['notifications']
        self.assertEqual(response.context['notification_count'], 2)
        self.assertEqual(
            {item['titulo'] for item in notificacoes},
            {'Ação: Ação atrasada', 'Ação: Ação próxima'},
        )
        self.assertEqual(response.context['notification_count'], 2)
        self.assertContains(response, 'id="notificationToggle"')
        self.assertNotContains(response, 'id="notificationTrash"')
        self.assertNotContains(response, 'data-notification-drag')
        self.assertContains(response, 'class="notification-delete-button"')
        self.assertContains(response, 'id="notificationHeaderCount">2</span>')
        self.assertContains(response, 'Ação atrasada')

    def test_clicking_action_notification_marks_it_read_and_redirects(self):
        acao = self.criar_acao('Ação próxima', self.hoje + timedelta(days=2))
        url = reverse('marcar_notificacao_lida', args=['acao', acao.pk])

        response = self.client.post(url)

        self.assertRedirects(response, reverse('kanban'))
        self.assertTrue(
            NotificacaoLida.objects.filter(usuario=self.user, acao=acao).exists()
        )
        page = self.client.get(reverse('kanban'))
        self.assertEqual(page.context['notification_count'], 0)
        self.assertTrue(page.context['notifications'][0]['lida'])
        self.assertContains(page, 'notification-read-icon-read')
        self.assertContains(page, 'bi-envelope-open')

    def test_user_cannot_mark_another_municipality_notification_as_read(self):
        outra_prefeitura = Prefeitura.objects.create(
            cnpj='98765432000110',
            nome_juridico='Outra Prefeitura',
            nome_fantasia='Outra Prefeitura',
            endereco='Rua Secundária, 2',
        )
        acao = self.criar_acao(
            'Ação de outra prefeitura',
            self.hoje + timedelta(days=2),
            prefeitura=outra_prefeitura,
        )

        response = self.client.post(
            reverse('marcar_notificacao_lida', args=['acao', acao.pk])
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(NotificacaoLida.objects.filter(acao=acao).exists())

    def test_removing_notification_hides_it_and_updates_counts(self):
        acao_removida = self.criar_acao('Ação removida', self.hoje + timedelta(days=1))
        acao_restante = self.criar_acao('Ação restante', self.hoje + timedelta(days=3))
        url = reverse('remover_notificacao', args=['acao', acao_removida.pk])

        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})
        registro = NotificacaoLida.objects.get(usuario=self.user, acao=acao_removida)
        self.assertTrue(registro.removida)

        page = self.client.get(reverse('kanban'))
        self.assertEqual(page.context['notification_count'], 1)
        self.assertEqual(page.context['notification_total_count'], 1)
        self.assertEqual(
            [item['titulo'] for item in page.context['notifications']],
            [f'Ação: {acao_restante.nome}'],
        )

    def test_user_cannot_remove_notification_from_another_municipality(self):
        outra_prefeitura = Prefeitura.objects.create(
            cnpj='98765432000110',
            nome_juridico='Outra Prefeitura',
            nome_fantasia='Outra Prefeitura',
            endereco='Rua Secundária, 2',
        )
        acao = self.criar_acao(
            'Ação de outra prefeitura',
            self.hoje + timedelta(days=2),
            prefeitura=outra_prefeitura,
        )
        url = reverse('remover_notificacao', args=['acao', acao.pk])

        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 404)
        self.assertFalse(NotificacaoLida.objects.filter(acao=acao).exists())

    def test_removing_stage_notification_hides_it(self):
        acao = self.criar_acao('Ação em andamento', self.hoje + timedelta(days=14))
        etapa = Etapa.objects.create(
            nome='Etapa removida',
            data_inicio=self.hoje,
            data_fim=self.hoje + timedelta(days=2),
            acao=acao,
            responsavel=self.user,
        )
        url = reverse('remover_notificacao', args=['etapa', etapa.pk])

        response = self.client.post(
            url,
            HTTP_X_REQUESTED_WITH='XMLHttpRequest',
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True})
        self.assertTrue(
            NotificacaoLida.objects.get(usuario=self.user, etapa=etapa).removida
        )
        page = self.client.get(reverse('kanban'))
        self.assertEqual(page.context['notification_total_count'], 0)

    def test_clicking_stage_notification_marks_it_read_and_redirects(self):
        acao = self.criar_acao('Ação em andamento', self.hoje + timedelta(days=14))
        etapa = Etapa.objects.create(
            nome='Etapa urgente',
            data_inicio=self.hoje,
            data_fim=self.hoje + timedelta(days=2),
            acao=acao,
            responsavel=self.user,
        )

        response = self.client.post(
            reverse('marcar_notificacao_lida', args=['etapa', etapa.pk])
        )

        self.assertRedirects(response, reverse('kanban'))
        self.assertTrue(
            NotificacaoLida.objects.filter(usuario=self.user, etapa=etapa).exists()
        )

    def test_lists_due_incomplete_stages_and_omits_completed_stages(self):
        acao = self.criar_acao('Ação em andamento', self.hoje + timedelta(days=14))
        etapa = Etapa.objects.create(
            nome='Etapa urgente',
            data_inicio=self.hoje - timedelta(days=1),
            data_fim=self.hoje + timedelta(days=2),
            acao=acao,
            responsavel=self.user,
        )
        Etapa.objects.create(
            nome='Etapa concluída',
            data_inicio=self.hoje,
            data_fim=self.hoje + timedelta(days=1),
            acao=acao,
            responsavel=self.user,
            concluida=True,
        )

        response = self.client.get(reverse('kanban'))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['notification_count'], 1)
        self.assertEqual(response.context['notifications'][0]['titulo'], f'Etapa: {etapa.nome}')
