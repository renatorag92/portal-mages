from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..models import Eixo
from ..services.eixo_service import EixoService
from ..services.excecoes import ErroRegraNegocio
from ._base import usuario_configuracoes


class EixoForm(forms.ModelForm):
    principal = forms.ModelChoiceField(
        queryset=Eixo.objects.none(),
        required=False,
        label='Eixo principal',
        empty_label='Nenhum (eixo principal)',
    )

    class Meta:
        model = Eixo
        fields = ('nome', 'principal')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['principal'].queryset = EixoService.listar_principais(self.instance.pk)

    def clean_nome(self):
        nome = (self.cleaned_data.get('nome') or '').strip()
        if not nome:
            raise ValidationError('Informe o nome do eixo.')
        if EixoService.nome_existe(nome, self.instance.pk):
            raise ValidationError('Já existe um eixo com esse nome.')
        return nome


@login_required
@user_passes_test(usuario_configuracoes)
def gerenciar_eixo_view(request, eixo_id=None):
    eixo = EixoService.buscar_ou_404(eixo_id) if eixo_id else None

    if request.method == 'POST':
        form = EixoForm(request.POST, instance=eixo)
        if form.is_valid():
            form.save()
            messages.success(
                request,
                'Eixo atualizado com sucesso.' if eixo else 'Eixo cadastrado com sucesso.',
                extra_tags='eixo-updated' if eixo else 'eixo-created',
            )
            return redirect('gerenciar_eixo')
    else:
        form = EixoForm(instance=eixo)

    return render(request, 'actions/gerenciar-eixo.html', {
        'form': form,
        'eixo_lista': EixoService.listar_todos(),
        'eixo_edicao': eixo,
    })


@login_required
@user_passes_test(usuario_configuracoes)
@require_POST
def excluir_eixo_view(request, eixo_id):
    try:
        EixoService.excluir(eixo_id)
        messages.success(request, 'Eixo excluído com sucesso.', extra_tags='eixo-deleted')
    except ErroRegraNegocio as e:
        messages.error(request, e.mensagem, extra_tags='eixo-delete-blocked')
    return redirect('gerenciar_eixo')