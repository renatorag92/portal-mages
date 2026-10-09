import re

from django import forms
from django.core.exceptions import ValidationError
from django.db.models import Q

from .models import Consultoria, Prefeitura


class CadastroEntidadeForm(forms.Form):
    cnpj = forms.CharField(
        label='CNPJ',
        error_messages={'required': 'O campo CNPJ é obrigatório.'},
    )
    nome_fantasia = forms.CharField(
        max_length=45,
        label='Nome fantasia',
        error_messages={
            'required': 'O campo Nome fantasia é obrigatório.',
            'max_length': 'Nome fantasia deve ter no máximo 45 caracteres.',
        },
    )
    nome_juridico = forms.CharField(
        max_length=45,
        label='Nome jurídico',
        error_messages={
            'required': 'O campo Nome jurídico é obrigatório.',
            'max_length': 'Nome jurídico deve ter no máximo 45 caracteres.',
        },
    )
    endereco = forms.CharField(
        max_length=45,
        label='Endereço',
        error_messages={
            'required': 'O campo Endereço é obrigatório.',
            'max_length': 'Endereço deve ter no máximo 45 caracteres.',
        },
    )

    modelo = None

    def __init__(self, *args, instance=None, **kwargs):
        self.instance = instance
        initial = dict(kwargs.pop('initial', {}))
        if instance:
            for campo in ('cnpj', 'nome_fantasia', 'nome_juridico', 'endereco'):
                initial.setdefault(campo, getattr(instance, campo))
            if hasattr(instance, 'prefeitura_id'):
                initial.setdefault('prefeitura', instance.prefeitura_id)
        kwargs['initial'] = initial
        super().__init__(*args, **kwargs)

    def clean_cnpj(self):
        informado = self.cleaned_data['cnpj'].strip()
        if not re.fullmatch(r'\d{14}|\d{2}\.\d{3}\.\d{3}/\d{4}-\d{2}', informado):
            raise ValidationError('CNPJ incompleto. Informe os 14 dígitos.')

        cnpj = re.sub(r'\D', '', informado)
        consulta = self.modelo.objects.filter(cnpj=cnpj)
        if self.instance:
            consulta = consulta.exclude(pk=self.instance.pk)
        if consulta.exists():
            raise ValidationError('CNPJ já cadastrado.')
        return cnpj


class PrefeituraForm(CadastroEntidadeForm):
    modelo = Prefeitura


class ConsultoriaForm(CadastroEntidadeForm):
    modelo = Consultoria
    prefeitura = forms.ModelChoiceField(
        queryset=Prefeitura.objects.none(),
        label='Prefeitura',
        empty_label='Selecione uma prefeitura',
        error_messages={
            'required': 'O campo Prefeitura é obrigatório.',
            'invalid_choice': 'Selecione uma prefeitura válida e disponível.',
        },
    )

    def __init__(self, *args, instance=None, **kwargs):
        super().__init__(*args, instance=instance, **kwargs)
        prefeituras = Prefeitura.objects.filter(consultoria__isnull=True)
        if instance:
            prefeituras = Prefeitura.objects.filter(
                Q(consultoria__isnull=True) | Q(pk=instance.prefeitura_id)
            )
        self.fields['prefeitura'].queryset = prefeituras.order_by('nome_fantasia')