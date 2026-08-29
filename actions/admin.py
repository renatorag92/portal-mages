from django.contrib import admin
from .models import Acao, Etapa

admin.site.register(Acao)

class AcaoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'eixo', 'prioridade', 'responsavel', 'data_inicio', 'data_fim', 'status', 'custo')
    # Campo de pesquisa 
    search_fields = ('codigo', 'nome', 'eixo', 'responsavel')
    # Filtro
    list_filter = ('eixo','prioridade', 'status')

admin.site.register(Etapa)

class EtapaAdmin(admin.ModelAdmin):
    list_display = ('acao', 'etapa', 'responsavel', 'data_inicio', 'data_fim', 'status', 'prioridade')
    search_fields = ('acao__nome', 'etapa', 'responsavel')
    list_filter = ('status', 'prioridade')

