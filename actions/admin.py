from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Acao, Etapa, PerfilUsuario, Prefeitura

@admin.register(Acao) # Registra o modelo Acao no admin do Django
class AcaoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'eixo', 'prioridade', 'responsavel', 'data_inicio', 'data_fim', 'status', 'custo')
    # Campo de pesquisa 
    search_fields = ('codigo', 'nome', 'eixo', 'responsavel')
    # Filtro
    list_filter = ('eixo','prioridade', 'status')

@admin.register(Etapa)
class EtapaAdmin(admin.ModelAdmin):
    list_display = ('acao', 'etapa', 'responsavel', 'data_inicio', 'data_fim', 'status', 'prioridade')
    search_fields = ('acao__nome', 'etapa', 'responsavel')
    list_filter = ('status', 'prioridade')
    
@admin.register(Prefeitura)
class PrefeituraAdmin(admin.ModelAdmin):
    list_display = ('nome', 'sigla', 'cidade')
    search_fields = ('nome', 'sigla', 'cidade')
    
# 1. Inline que insere o PerfilUsuario dentro do formulário do User
class PerfilUsuarioInline(admin.StackedInline):
    model = PerfilUsuario
    can_delete = False
    verbose_name_plural = 'Persil Usuário'
    fields = ('prefeitura', 'cargo', 'primeiro_acesso')
    
    # Adicionamos o Inline na Admnistração do User
class UserAdmin(BaseUserAdmin):
        inlines = (PerfilUsuarioInline,)  
        
# Substituímos a administração padrão do Django pela nossa versão unificada
admin.site.unregister(User)
admin.site.register(User, UserAdmin)   
    