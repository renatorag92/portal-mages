from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST

from ..forms import ConsultoriaForm
from ..services.consultoria_service import ConsultoriaService
from ..services.excecoes import ErroRegraNegocio
from ._base import carregar_json, erros_formulario, usuario_configuracoes


@login_required
@user_passes_test(usuario_configuracoes)
def gerenciar_consultoria_view(request):
    contexto = ConsultoriaService.preparar_tela(ConsultoriaForm)
    return render(request, 'actions/cadastro-entidade.html', contexto)


@login_required
@user_passes_test(usuario_configuracoes)
@require_POST
def salvar_consultoria_view(request):
    dados = carregar_json(request)
    if dados is None:
        return JsonResponse({'success': False, 'errors': {'__all__': ['Requisição inválida.']}}, status=400)

    try:
        registro_atual = ConsultoriaService.obter_para_edicao(dados.get('id'))
    except ErroRegraNegocio as e:
        return JsonResponse({'success': False, 'errors': e.errors}, status=e.status)

    form = ConsultoriaForm(dados, instance=registro_atual)
    if not form.is_valid():
        return JsonResponse({'success': False, 'errors': erros_formulario(form)}, status=400)

    try:
        registro = ConsultoriaService.salvar(form, registro_atual)
    except ErroRegraNegocio as e:
        return JsonResponse({'success': False, 'errors': e.errors}, status=e.status)

    return JsonResponse({'success': True, 'registro': ConsultoriaService.serializar(registro)})