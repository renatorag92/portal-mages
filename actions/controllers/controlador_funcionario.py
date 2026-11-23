from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..forms import FuncionarioForm, MinhaContaForm
from ..services.autenticacao_service import AutenticacaoService
from ..services.excecoes import ErroRegraNegocio
from ..services.funcionario_service import FuncionarioService
from ._base import usuario_configuracoes


@login_required
def minha_conta_view(request):
    if request.method == 'POST':
        form = MinhaContaForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            FuncionarioService.atualizar_perfil(form)
            messages.success(request, 'Seus dados foram atualizados com sucesso.')
            return redirect('minha_conta')
    else:
        form = MinhaContaForm(instance=request.user)

    return render(request, 'actions/minha-conta.html', {'form': form})


@login_required
@user_passes_test(usuario_configuracoes)
def gerenciar_funcionario_view(request, funcionario_id=None):
    funcionario = FuncionarioService.buscar_ou_404(funcionario_id) if funcionario_id else None

    if request.method == 'POST':
        form = FuncionarioForm(request.POST, instance=funcionario)
        if form.is_valid():
            registro, senha = FuncionarioService.salvar(form)
            if senha:
                messages.warning(
                    request,
                    f'Senha provisória de {registro.nome} (CPF {registro.username}): {senha}. '
                    'Informe agora; ela não será exibida novamente.',
                    extra_tags='funcionario-senha',
                )
            messages.success(
                request,
                'Funcionário atualizado com sucesso.' if funcionario else 'Funcionário cadastrado com sucesso.',
                extra_tags='funcionario-updated' if funcionario else 'funcionario-created',
            )
            return redirect('gerenciar_funcionario')
    else:
        form = FuncionarioForm(instance=funcionario)

    return render(request, 'actions/gerenciar-funcionario.html', {
        'form': form,
        'funcionario_lista': FuncionarioService.listar_todos(),
        'funcionario_edicao': funcionario,
        'total_consultores': FuncionarioService.contar_consultores(),
    })


@login_required
@user_passes_test(usuario_configuracoes)
@require_POST
def excluir_funcionario_view(request, funcionario_id):
    try:
        FuncionarioService.excluir(funcionario_id, request.user)
        messages.success(request, 'Funcionário excluído com sucesso.', extra_tags='funcionario-deleted')
    except ErroRegraNegocio as e:
        messages.error(request, e.mensagem, extra_tags='funcionario-delete-blocked')
    return redirect('gerenciar_funcionario')


@login_required
@user_passes_test(usuario_configuracoes)
@require_POST
def gerar_senha_funcionario_view(request, funcionario_id):
    try:
        funcionario, senha = AutenticacaoService.gerar_nova_senha_provisoria(funcionario_id)
        messages.warning(
            request,
            f'Nova senha provisória de {funcionario.nome} (CPF {funcionario.username}): {senha}. '
            'A senha anterior deixou de valer. Informe agora; ela não será exibida novamente.',
            extra_tags='funcionario-senha',
        )
    except ErroRegraNegocio as e:
        messages.error(request, e.mensagem, extra_tags='funcionario-senha-erro')
    return redirect('gerenciar_funcionario')