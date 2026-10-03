from django.contrib import admin
from .models import Prefeitura, Consultoria, Funcionario, Secretario, Eixo, Status, Acao, Etapa, PerfilUsuario, AcaoCatalogo

@admin.register(Prefeitura)
class PrefeituraAdmin(admin.ModelAdmin):
    list_display = ('nome_fantasia', 'cnpj', 'nome_juridico')
    search_fields = ('nome_fantasia', 'cnpj')

@admin.register(Consultoria)
class ConsultoriaAdmin(admin.ModelAdmin):
    list_display = ('nome_fantasia', 'cnpj', 'prefeitura')

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
        'codigo', 'acao_catalogo', 'nova_acao_texto', 'prioridade',
        'data_inicio', 'data_fim')
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

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'prefeitura', 'cargo', 'primeiro_acesso')
