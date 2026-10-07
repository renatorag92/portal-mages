from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse

from .models import PerfilUsuario, Status
from .views import MAX_STATUS_COLUMNS, StatusForm


class StatusFormLimitTests(TestCase):
    def setUp(self):
        for index in range(MAX_STATUS_COLUMNS):
            Status.objects.create(
                nome=f'Status {index + 1}',
                cor=f'#{index + 1:06x}',
                ordem=index,
            )

    def test_rejects_new_status_when_limit_is_reached(self):
        form = StatusForm({'nome': 'Novo status', 'cor': '#ffffff'})

        self.assertFalse(form.is_valid())
        self.assertIn(
            f'O limite de {MAX_STATUS_COLUMNS} status foi atingido.',
            form.non_field_errors()[0],
        )

    def test_allows_new_status_below_limit(self):
        Status.objects.order_by('ordem').last().delete()
        form = StatusForm({'nome': 'Novo status', 'cor': '#ffffff'})

        self.assertTrue(form.is_valid(), form.errors)

    def test_allows_editing_status_when_limit_is_reached(self):
        status = Status.objects.order_by('ordem').first()
        form = StatusForm(
            {'nome': 'Status editado', 'cor': '#ffffff'},
            instance=status,
        )

        self.assertTrue(form.is_valid(), form.errors)


class KanbanStatusEditTests(TestCase):
    def setUp(self):
        user = User.objects.create_user(username='status-editor', password='test-password')
        PerfilUsuario.objects.create(
            usuario=user,
            cargo='Administrador',
            primeiro_acesso=False,
        )
        self.client.force_login(user)
        self.status = Status.objects.create(nome='Em andamento', cor='#123456')
        self.url = reverse('editar_status_kanban', args=[self.status.pk])

    def test_updates_status_from_kanban_modal_endpoint(self):
        response = self.client.post(
            self.url,
            {'nome': 'Em análise', 'cor': '#ffffff'},
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertIn('atualizado com sucesso', self.client.session['kanban_toast']['mensagem'])
        self.status.refresh_from_db()
        self.assertEqual(self.status.nome, 'Em análise')
        self.assertEqual(self.status.cor, '#ffffff')
        self.assertEqual(self.status.cor_nome, '#ffffff')

    def test_preserves_named_color_for_status_editing(self):
        response = self.client.post(
            self.url,
            {'nome': 'Em análise', 'cor': 'Lilás'},
        )

        self.assertEqual(response.status_code, 200)
        self.status.refresh_from_db()
        self.assertEqual(self.status.cor, '#e6e6fa')
        self.assertEqual(self.status.cor_nome, 'Lilás')

    def test_status_form_uses_saved_color_input_when_editing(self):
        self.client.post(
            self.url,
            {'nome': 'Em análise', 'cor': 'Lilás'},
        )

        self.status.refresh_from_db()
        form = StatusForm(instance=self.status)
        self.assertEqual(form['cor'].value(), 'Lilás')

    def test_legacy_named_hex_color_has_readable_edit_value(self):
        self.status.cor = '#e6e6fa'
        self.status.save()

        form = StatusForm(instance=self.status)

        self.assertEqual(form['cor'].value(), 'lilás')

    def test_returns_validation_errors_without_updating_status(self):
        response = self.client.post(
            self.url,
            {'nome': 'Em andamento', 'cor': 'cor-invalida'},
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('cor', response.json()['errors'])
        self.status.refresh_from_db()
        self.assertEqual(self.status.cor, '#123456')

    def test_kanban_has_no_status_delete_action(self):
        response = self.client.get(reverse('kanban'))

        self.assertEqual(response.status_code, 200)
        self.assertRegex(
            response.content.decode(),
            r'<h1>\s*Kanban de Governança\s*</h1>',
        )
        self.assertContains(response, 'Editar status Em andamento')
        self.assertNotContains(response, 'Excluir status Em andamento')
