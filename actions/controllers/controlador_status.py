from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from ..models import Status
from ..services.status_service import StatusService
from ._base import usuario_configuracoes


class StatusForm(forms.ModelForm):
    cor = forms.CharField(max_length=45)

    class Meta:
        model = Status
        fields = ('cor',)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk and not self.is_bound:
            self.initial['cor'] = StatusService.cor_para_edicao(self.instance)

    def clean_cor(self):
        cor_informada = self.cleaned_data['cor'].strip()
        self.cor_informada = cor_informada
        return StatusService.normalizar_cor(cor_informada)

    def clean(self):
        cleaned_data = super().clean()
        cor = cleaned_data.get('cor')
        if cor and StatusService.cor_em_uso(cor, self.instance.pk):
            self.add_error('cor', 'Essa cor já está cadastrada em outro status.')
        return cleaned_data

    def save(self, commit=True):
        status = super().save(commit=False)
        status.cor_nome = getattr(self, 'cor_informada', status.cor_nome)
        if commit:
            status.save()
        return status


@login_required
@user_passes_test(usuario_configuracoes)
def gerenciar_status_view(request, status_id=None):
    status = StatusService.buscar_ou_404(status_id) if status_id else None
    form = None

    if status:
        if request.method == 'POST':
            form = StatusForm(request.POST, instance=status)
            if form.is_valid():
                form.save()
                messages.success(request, 'Cor do status atualizada com sucesso.', extra_tags='status-updated')
                return redirect('gerenciar_status')
        else:
            form = StatusForm(instance=status)

    return render(request, 'actions/gerenciar-status.html', {
        'form': form,
        'status_lista': StatusService.listar_todos(),
        'status_edicao': status,
    })


@login_required
@user_passes_test(usuario_configuracoes)
@require_POST
def editar_status_kanban_view(request, status_id):
    status = StatusService.buscar_ou_404(status_id)
    form = StatusForm(request.POST, instance=status)
    if not form.is_valid():
        return JsonResponse({
            'success': False,
            'errors': {
                field: [str(error) for error in errors]
                for field, errors in form.errors.items()
            },
        }, status=400)
    status = form.save()
    request.session['kanban_toast'] = {
        'mensagem': f'Status "{status.nome}" atualizado com sucesso.',
        'tipo': 'status-updated',
    }
    return JsonResponse({
        'success': True,
        'status': {'id': status.id, 'nome': status.nome, 'cor': status.cor},
    })