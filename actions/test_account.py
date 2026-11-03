import io
import tempfile

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from .models import Prefeitura


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

    def criar_imagem(self, nome='foto.png', formato='PNG'):
        conteudo = io.BytesIO()
        Image.new('RGB', (2, 2), color='red').save(conteudo, format=formato)
        return SimpleUploadedFile(
            nome,
            conteudo.getvalue(),
            content_type=f'image/{formato.lower()}',
        )

    def test_account_page_is_linked_from_the_user_menu(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Nome Original')
        self.assertContains(response, 'user-menu-role">(Analista)</span>')
        self.assertContains(response, 'enctype="multipart/form-data"')
        self.assertContains(response, reverse('minha_conta'))
        self.assertContains(response, 'Foto de perfil')
        self.assertContains(response, 'id="profilePhotoDialog"')
        self.assertContains(response, 'id="chooseProfilePhoto"')
        self.assertNotContains(response, 'id="removeProfilePhoto"')
        self.assertContains(response, 'id="saveProfilePhoto"')
        self.assertNotContains(response, 'JPG, PNG ou WEBP, até 5 MB.')
        self.assertNotContains(response, 'Adicionar foto')
        self.assertNotContains(response, 'name="username"')

    def test_user_can_update_personal_data_and_upload_profile_photo(self):
        response = self.client.post(
            self.url,
            {
                'nome': 'Nome Atualizado',
                'email': 'atualizado@example.com',
                'telefone': '11988887777',
                'endereco': 'Rua Nova, 20',
                'foto': self.criar_imagem('../foto.png'),
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
        self.assertTrue(self.user.foto.name.startswith('profile_photos/'))
        self.assertTrue(self.user.foto.storage.exists(self.user.foto.name))
        page = self.client.get(self.url)
        self.assertContains(page, 'Seus dados foram atualizados com sucesso.')
        self.assertContains(page, self.user.foto.url)
        self.assertContains(page, 'id="removeProfilePhoto"')

    def test_rejects_non_image_upload_without_updating_account(self):
        response = self.client.post(
            self.url,
            {
                'nome': 'Nome Inválido',
                'email': 'original@example.com',
                'telefone': '11999990000',
                'endereco': 'Rua Original, 1',
                'foto': SimpleUploadedFile(
                    'foto.png',
                    b'isso nao e uma imagem',
                    content_type='image/png',
                ),
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.context['form'].errors['foto'][0],
            'Envie uma imagem JPG, PNG ou WEBP.',
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.nome, 'Nome Original')

    def test_user_can_remove_existing_profile_photo(self):
        upload = self.criar_imagem()
        self.user.foto.save(upload.name, upload, save=True)
        nome_foto = self.user.foto.name
        self.user.refresh_from_db()
        self.assertEqual(self.user.foto.name, nome_foto)

        response = self.client.post(
            self.url,
            {
                'nome': self.user.nome,
                'email': self.user.email,
                'telefone': self.user.telefone,
                'endereco': self.user.endereco,
                'foto-clear': 'on',
            },
        )

        if response.status_code != 302:
            self.fail(str(response.context['form'].errors))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response['Location'], self.url)
        self.user.refresh_from_db()
        self.assertFalse(self.user.foto)
        self.assertFalse(self.user.foto.storage.exists(nome_foto))
