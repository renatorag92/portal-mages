import re
import secrets

from django import forms
from django.core.exceptions import ValidationError
from django.contrib.auth.forms import AuthenticationForm
from django.db import transaction
from django.db.models import Q

from .models import Consultoria, Funcionario, Prefeitura

CAMPOS_ENTIDADE = ('cnpj', 'nome_fantasia', 'nome_juridico', 'endereco')

class LoginCPFForm(AuthenticationForm):
    def clean_username(self):
        return re.sub(r'\D', '', self.cleaned_data.get('username') or '')

# ---------------------------------------------------------------------------
# Cadastro de Prefeitura e Consultoria (recebidos como JSON pelas views)
# ---------------------------------------------------------------------------
class CadastroEntidadeForm(forms.Form):
    cnpj = forms.CharField(
        label='CNPJ',
        error_messages={'required': 'O campo CNPJ é obrigatório.'},
    )
    nome_fantasia = forms.CharField(
        max_length=100,
        label='Nome fantasia',
        error_messages={
            'required': 'O campo Nome fantasia é obrigatório.',
            'max_length': 'Nome fantasia deve ter no máximo 100 caracteres.',
        },
    )
    nome_juridico = forms.CharField(
        max_length=100,
        label='Nome jurídico',
        error_messages={
            'required': 'O campo Nome jurídico é obrigatório.',
            'max_length': 'Nome jurídico deve ter no máximo 100 caracteres.',
        },
    )
    endereco = forms.CharField(
        max_length=150,
        label='Endereço',
        error_messages={
            'required': 'O campo Endereço é obrigatório.',
            'max_length': 'Endereço deve ter no máximo 150 caracteres.',
        },
    )

    entidade_model = None  # definido em cada subclasse

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        initial = dict(kwargs.pop('initial', None) or {})
        if instance is not None:
            for campo in CAMPOS_ENTIDADE:
                initial.setdefault(campo, getattr(instance, campo))
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def clean_cnpj(self):
        informado = self.cleaned_data['cnpj'].strip()
        if not re.fullmatch(r'\d{14}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', informado):
            raise ValidationError('CNPJ incompleto. Informe os 14 dígitos.')

        cnpj = re.sub(r'\D', '', informado)
        consulta = self.entidade_model.objects.filter(cnpj=cnpj)
        if self.instance is not None:
            consulta = consulta.exclude(pk=self.instance.pk)
        if consulta.exists():
            raise ValidationError('CNPJ já cadastrado.')
        return cnpj


class PrefeituraForm(CadastroEntidadeForm):
    entidade_model = Prefeitura


class ConsultoriaForm(CadastroEntidadeForm):
    entidade_model = Consultoria

    def salvar(self):
        dados = self.cleaned_data

        with transaction.atomic():
            consultoria = self.instance if self.instance is not None else Consultoria()
            for campo in CAMPOS_ENTIDADE:
                setattr(consultoria, campo, dados[campo])
            consultoria.save()

        return consultoria


# ---------------------------------------------------------------------------
# Cadastro de Funcionário (usado pelo admin, feito por consultores)
# ---------------------------------------------------------------------------
class FuncionarioForm(forms.ModelForm):
    vinculo = forms.ChoiceField(
        choices=[('prefeitura', 'Prefeitura'), ('consultoria', 'Consultoria')],
        widget=forms.RadioSelect,
        label='Vínculo',
        error_messages={
            'required': 'Escolha se o funcionário é da prefeitura ou da consultoria.',
            'invalid_choice': 'Escolha uma das opções de vínculo.',
        },
    )

    class Meta:
        model = Funcionario
        fields = ['nome', 'username', 'email', 'telefone', 'endereco', 'cargo', 'tem_acesso']
        labels = {'username': 'CPF'}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            if self.instance.prefeitura_id:
                self.initial.setdefault('vinculo', 'prefeitura')
            elif self.instance.consultoria_id:
                self.initial.setdefault('vinculo', 'consultoria')
            self.fields['username'].disabled = True

    def clean_username(self):
        digitos = re.sub(r'\D', '', self.cleaned_data.get('username') or '')
        if len(digitos) != 11:
            raise ValidationError('Informe um CPF com 11 dígitos.')

        consulta = Funcionario.objects.filter(username=digitos)
        if self.instance.pk:
            consulta = consulta.exclude(pk=self.instance.pk)
        if consulta.exists():
            raise ValidationError('Já existe um funcionário com este CPF.')
        return digitos

    def clean(self):
        dados = super().clean()
        vinculo = dados.get('vinculo')
        if not vinculo:
            return dados  # o erro já aparece no campo vínculo

        if vinculo == 'prefeitura':
            entidade = Prefeitura.objects.order_by('pk').first()
            if entidade is None:
                raise ValidationError('Cadastre a prefeitura antes de vincular funcionários a ela.')
            self.instance.prefeitura = entidade
            self.instance.consultoria = None
        else:
            entidade = Consultoria.objects.order_by('pk').first()
            if entidade is None:
                raise ValidationError('Cadastre a consultoria antes de vincular funcionários a ela.')
            self.instance.consultoria = entidade
            self.instance.prefeitura = None

        return dados

class MinhaContaForm(forms.ModelForm):
    class Meta:
        model = Funcionario
        fields = ['nome', 'email', 'telefone', 'endereco']
        labels = {
            'nome': 'Nome completo',
            'email': 'E-mail',
            'telefone': 'Telefone',
            'endereco': 'Endereço',
        }


ALFABETO_SENHA = 'abcdefghijkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'

def gerar_senha_provisoria(tamanho=10):
    return ''.join(secrets.choice(ALFABETO_SENHA) for _ in range(tamanho))

def preparar_senha(funcionario):
    """Gera senha provisória se o funcionário tem acesso e ainda não tem uma senha.
    Devolve a senha em texto puro (para mostrar uma vez) ou None."""
    if not funcionario.tem_acesso:
        return None
    if funcionario.password and funcionario.has_usable_password():
        return None
    senha = gerar_senha_provisoria()
    funcionario.set_password(senha)
    funcionario.primeiro_acesso = True
    return senha