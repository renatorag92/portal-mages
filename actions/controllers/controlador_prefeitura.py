from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from ..forms import PrefeituraForm
from ..services.excecoes import ErroRegraNegocio
from ..services.prefeitura_service import PrefeituraService
from ._base import carregar_json, erros_formulario, usuario_configuracoes


@login_required
@user_passes_test(usuario_configuracoes)
def gerenciar_prefeitura_view(request):
    contexto = PrefeituraService.preparar_tela(PrefeituraForm)
    return render(request, 'actions/cadastro-entidade.html', contexto)


@login_required
@user_passes_test(usuario_configuracoes)
@require_POST
def salvar_prefeitura_view(request):
    dados = carregar_json(request)
    if dados is None:
        return JsonResponse({'success': False, 'errors': {'__all__': ['Requisição inválida.']}}, status=400)

    try:
        registro = PrefeituraService.obter_para_edicao(dados.get('id'))
    except ErroRegraNegocio as e:
        return JsonResponse({'success': False, 'errors': e.errors}, status=e.status)

    form = PrefeituraForm(dados, instance=registro)
    if not form.is_valid():
        return JsonResponse({'success': False, 'errors': erros_formulario(form)}, status=400)

    try:
        registro = PrefeituraService.salvar(registro, form.cleaned_data)
    except ErroRegraNegocio as e:
        return JsonResponse({'success': False, 'errors': e.errors}, status=e.status)

    return JsonResponse({'success': True, 'registro': PrefeituraService.serializar(registro)})