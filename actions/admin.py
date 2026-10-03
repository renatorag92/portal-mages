from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import (
    Prefeitura, Consultoria, Funcionario, Secretario, 
    Eixo, Status, Acao, Etapa, PerfilUsuario, AcaoCatalogo
)

# --- Configuração de Inline para Unificar Usuário e PerfilUsuario ---

class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name = 'Perfil do Usuário'
    verbose_name_plural = 'Perfil do Usuário'
    fk_name = 'usuario'

class UserAdmin(BaseUserAdmin):
    inlines = (PerfilUsuarioInline,)

# Re-registra o modelo User do Django
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# --- Demais Modelos do Sistema ---

@admin.register(Prefeitura)
class PrefeituraAdmin(admin.ModelAdmin):
    list_display = ('nome_fantasia', 'cnpj', 'nome_juridico', 'endereco')
    sortable_by = ()  # Desativa a ordenação nos cabeçalhos das colunas     
    save_as_continue = False

    def has_add_permission(self, request):
        if Prefeitura.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(Consultoria)
class ConsultoriaAdmin(admin.ModelAdmin):
    list_display = ('nome_fantasia', 'nome_juridico', 'cnpj', 'endereco', 'prefeitura')
    sortable_by = ()  # Desativa a ordenação nos cabeçalhos das colunas
    save_as_continue = False

    def has_add_permission(self, request):
        if Consultoria.objects.exists():
            return False
        return super().has_add_permission(request)

    def has_delete_permission(self, request, obj=None):
        return False

    def changeform_view(self, request, object_id=None, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['show_save_and_continue'] = False
        return super().changeform_view(request, object_id, form_url, extra_context)


@admin.register(Funcionario)
class FuncionarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'email', 'cargo')
    search_fields = ('nome', 'cpf')


@admin.register(Secretario)
class SecretarioAdmin(admin.ModelAdmin):
    list_display = ('nome', 'cpf', 'email')


@admin.register(Eixo)
class EixoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'descricao')


@admin.register(Status)
class StatusAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'cor')


@admin.register(AcaoCatalogo)
class AcaoCatalogoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'eixo')
    search_fields = ('eixo',)
    list_filter = ('nome',)


@admin.register(Acao)
class AcaoAdmin(admin.ModelAdmin):
    list_display = (
        'codigo', 'get_nome_acao', 'prioridade',
        'data_inicio', 'data_fim'
    )
    list_filter = ('prioridade', 'status')
    search_fields = ('codigo', 'acao_catalogo__nome', 'nova_acao_texto')

    @admin.display(description='Ação')
    def get_nome_acao(self, obj):
        if obj.acao_catalogo:
            return obj.acao_catalogo.nome
        return obj.nova_acao_texto or 'Sem nome'


@admin.register(Etapa)
class EtapaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'acao', 'responsavel')
    list_filter = ('nome',)