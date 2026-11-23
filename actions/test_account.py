import tempfile

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse

from actions.models import Prefeitura


class MinhaContaTests(TestCase):
    def setUp(self):
        prefeitura = Prefeitura.objects.create(
            cnpj='12345678000195',
            nome_juridico='Prefeitura Central',
            nome_fantasia='Prefeitura Central',
            endereco='Rua Central, 1',
        )
        self.user = get_user_model().objects.create_user(
            username='12345678901',
            password='test-password',
            nome='Nome Original',
            email='original@example.com',
            telefone='11999990000',
            endereco='Rua Original, 1',
            cargo='Analista',
            prefeitura=prefeitura,
            tem_acesso=True,
            primeiro_acesso=False,
        )
        self.client.force_login(self.user)
        self.url = reverse('minha_conta')
        self.media_dir = tempfile.TemporaryDirectory()
        self.media_settings = override_settings(MEDIA_ROOT=self.media_dir.name)
        self.media_settings.enable()
        self.addCleanup(self.media_settings.disable)
        self.addCleanup(self.media_dir.cleanup)


    def test_account_page_is_linked_from_the_user_menu(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nome Original')
        self.assertContains(response, 'user-menu-role">(Analista)</span>')
        self.assertNotContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, reverse('minha_conta'))
        self.assertNotContains(response, 'Foto de perfil')
        self.assertNotContains(response, 'id="profilePhotoDialog"')
        self.assertNotContains(response, 'id="chooseProfilePhoto"')
        self.assertNotContains(response, 'id="removeProfilePhoto"')
        self.assertNotContains(response, 'id="saveProfilePhoto"')
        self.assertNotContains(response, 'JPG, PNG ou WEBP, até 5 MB.')
        self.assertNotContains(response, 'Adicionar foto')
        self.assertNotContains(response, 'name="username"')

    def test_user_can_update_personal_data(self):
        response = self.client.post(
            self.url,
            {
                'nome': 'Nome Atualizado',
                'email': 'atualizado@example.com',
                'telefone': '11988887777',
                'endereco': 'Rua Nova, 20',
            },
        )

        if response.status_code != 302:
            self.fail(str(response.context['form'].errors))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.url)
        self.user.refresh_from_db()
        self.assertEqual(self.user.nome, 'Nome Atualizado')
        self.assertEqual(self.user.email, 'atualizado@example.com')
        self.assertEqual(self.user.telefone, '11988887777')
        self.assertEqual(self.user.endereco, 'Rua Nova, 20')
        self.assertEqual(self.user.cpf, '12345678901')
        self.assertEqual(self.user.cargo, 'Analista')
        page = self.client.get(self.url)
        self.assertContains(page, 'Seus dados foram atualizados com sucesso.')
