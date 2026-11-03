from django.contrib import admin, messages
from .forms import FuncionarioForm, preparar_senha

from .forms import FuncionarioForm
from .models import (
    Prefeitura, Consultoria, Funcionario, Eixo, Status, AcaoCatalogo, Acao, Etapa,
)


# ---------------------------------------------------------------------------
# Base: somente consultores (e superusuário) acessam as telas de configuração
# ---------------------------------------------------------------------------
class SomenteConsultorAdmin(admin.ModelAdmin):
    def _pode(self, request):
        usuario = request.user
        return usuario.is_authenticated and (usuario.is_superuser or usuario.e_consultor)

    def has_module_permission(self, request):
        return self._pode(request)

    def has_view_permission(self, request, obj=None):
        return self._pode(request)

    def has_add_permission(self, request):
        return self._pode(request)

    def has_change_permission(self, request, obj=None):
        return self._pode(request)

    def has_delete_permission(self, request, obj=None):
        return self._pode(request)


class RegistroUnicoAdmin(SomenteConsultorAdmin):
    """Prefeitura e Consultoria: só um registro (sistema atende um município)."""
    sortable_by = ()
    save_as_continue = False

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(Prefeitura)
class PrefeituraAdmin(RegistroUnicoAdmin):
    list_display = ('nome_fantasia', 'cnpj', 'nome_juridico', 'endereco', 'consultoria')


@admin.register(Consultoria)
class ConsultoriaAdmin(RegistroUnicoAdmin):
    list_display = ('nome_fantasia', 'nome_juridico', 'cnpj', 'endereco', 'get_prefeitura')

    @admin.display(description='Prefeitura')
    def get_prefeitura(self, obj):
        # Relação 1:1 reversa: pode não existir ainda
        prefeitura = getattr(obj, 'prefeitura', None)
        return prefeitura.nome_fantasia if prefeitura else '—'


# ---------------------------------------------------------------------------
# Funcionário: único cadastro de pessoas (com ou sem login)
# ---------------------------------------------------------------------------
@admin.register(Funcionario)
class FuncionarioAdmin(SomenteConsultorAdmin):
    form = FuncionarioForm
    list_display = ('nome', 'username', 'cargo', 'prefeitura', 'consultoria', 'tem_acesso')
    list_filter = ('prefeitura', 'consultoria', 'tem_acesso')
    search_fields = ('nome', 'username', 'email')
    fieldsets = (
    ('Dados pessoais', {'fields': ('nome', 'username', 'email', 'telefone', 'endereco')}),
    ('Vínculo', {'fields': ('cargo', 'vinculo')}),
    ('Acesso ao sistema', {'fields': ('tem_acesso',)}),
)

class FuncionarioAdmin(SomenteConsultorAdmin):
    # ... restante igual

    def save_model(self, request, obj, form, change):
        senha = preparar_senha(obj)
        super().save_model(request, obj, form, change)
        if senha:
            messages.warning(
                request,
                f'Senha provisória de {obj.nome} (CPF {obj.username}): {senha}. '
                'Copie e informe ao usuário; ela não será exibida novamente.',
            )

# ---------------------------------------------------------------------------
# Tabelas de apoio (configuração)
# ---------------------------------------------------------------------------
@admin.register(Eixo)
class EixoAdmin(SomenteConsultorAdmin):
    list_display = ('id', 'nome')


@admin.register(Status)
class StatusAdmin(SomenteConsultorAdmin):
    list_display = ('id', 'nome', 'cor', 'ordem')


@admin.register(AcaoCatalogo)
class AcaoCatalogoAdmin(SomenteConsultorAdmin):
    list_display = ('nome', 'eixo', 'ativa')
    list_filter = ('eixo', 'ativa')
    search_fields = ('nome', 'eixo__nome')


# ---------------------------------------------------------------------------
# Operação: Ações e Etapas, com auditoria automática
# ---------------------------------------------------------------------------
class AuditoriaAdminMixin:
    """Preenche criado_por e atualizado_por com o usuário logado."""

    def save_model(self, request, obj, form, change):
        if not change:
            obj.criado_por = request.user
        obj.atualizado_por = request.user
        super().save_model(request, obj, form, change)


@admin.register(Acao)
class AcaoAdmin(AuditoriaAdminMixin, SomenteConsultorAdmin):
    list_display = ('codigo', 'nome', 'prefeitura', 'prioridade', 'data_inicio', 'data_fim')
    list_filter = ('prefeitura', 'prioridade', 'status')
    search_fields = ('nome', 'modelo__nome')
    readonly_fields = ('codigo', 'criado_em', 'atualizado_em', 'criado_por', 'atualizado_por')


@admin.register(Etapa)
class EtapaAdmin(AuditoriaAdminMixin, SomenteConsultorAdmin):
    list_display = ('id', 'nome', 'acao', 'responsavel', 'concluida')
    list_filter = ('concluida', 'acao__prefeitura')
    search_fields = ('nome',)
    readonly_fields = ('criado_em', 'atualizado_em', 'criado_por', 'atualizado_por')