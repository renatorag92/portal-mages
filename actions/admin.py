from django.contrib import admin
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
    
@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'prefeitura', 'cargo')
    search_fields = ('usuario__username', 'prefeitura__nome', 'cargo')
    search_fields = ('usuario__username', 'prefeitura__nome', 'cargo')
    