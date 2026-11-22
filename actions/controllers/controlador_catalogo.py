from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.exceptions import ValidationError
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..models import AcaoCatalogo
from ..services.catalogo_service import CatalogoService
from ..services.eixo_service import EixoService
from ..services.excecoes import ErroRegraNegocio
from ._base import usuario_configuracoes


class AcaoCatalogoForm(forms.ModelForm):
    class Meta:
        model = AcaoCatalogo
        fields = ('nome', 'eixo')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['eixo'].queryset = EixoService.listar_folha()
        self.fields['eixo'].label_from_instance = lambda e: (
            f'{e.principal.nome} › {e.nome}' if e.principal_id else e.nome
        )

    def clean_nome(self):
        nome = (self.cleaned_data.get('nome') or '').strip()
        if not nome:
            raise ValidationError('Informe o nome da ação.')
        if CatalogoService.nome_existe(nome, self.instance.pk):
            raise ValidationError('Já existe uma ação com esse nome no catálogo.')
        return nome


@login_required
@user_passes_test(usuario_configuracoes)
def gerenciar_catalogo_view(request, modelo_id=None):
    modelo = CatalogoService.buscar_ou_404(modelo_id) if modelo_id else None
    form = AcaoCatalogoForm()
    catalogo_edicao_form = AcaoCatalogoForm(instance=modelo) if modelo else None

    if request.method == 'POST':
        form_enviado = AcaoCatalogoForm(request.POST, instance=modelo)
        if form_enviado.is_valid():
            form_enviado.save()
            messages.success(
                request,
                'Ação do catálogo atualizada com sucesso.' if modelo else 'Ação do catálogo cadastrada com sucesso.',
                extra_tags='catalogo-updated' if modelo else 'catalogo-created',
            )
            return redirect('gerenciar_catalogo')
        if modelo:
            catalogo_edicao_form = form_enviado
        else:
            form = form_enviado
    else:
        form = AcaoCatalogoForm(instance=modelo)

    nome_filtro = (request.GET.get('nome') or '').strip()
    eixo_filtro = (request.GET.get('eixo') or '').strip()

    return render(request, 'actions/gerenciar-catalogo.html', {
        'form': form,
        'catalogo_edicao_form': catalogo_edicao_form,
        'catalogo_lista': CatalogoService.listar_filtrado(nome_filtro, eixo_filtro),
        'catalogo_edicao': modelo,
        'nome_filtro': nome_filtro,
        'eixo_filtro': eixo_filtro,
        'eixos_lista': EixoService.listar_folha(),
    })


@login_required
@user_passes_test(usuario_configuracoes)
@require_POST
def excluir_catalogo_view(request, modelo_id):
    try:
        CatalogoService.excluir(modelo_id)
        messages.success(request, 'Ação do catálogo excluída com sucesso.', extra_tags='catalogo-deleted')
    except ErroRegraNegocio as e:
        messages.error(request, e.mensagem, extra_tags='catalogo-delete-blocked')
    return redirect('gerenciar_catalogo')