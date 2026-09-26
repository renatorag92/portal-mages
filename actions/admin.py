from django.contrib import admin
from .models import Prefeitura, Consultoria, Funcionario, Secretario, Eixo, Status, Acao, Etapa, PerfilUsuario

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
    list_display = ('id', 'nome')

@admin.register(Acao)
class AcaoAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'nome', 'eixo', 'status', 'secretario', 'prioridade')
    list_filter = ('status', 'eixo', 'prioridade')
    search_fields = ('codigo', 'nome')

@admin.register(Etapa)
class EtapaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nome', 'acao', 'status', 'responsavel')
    list_filter = ('status',)

@admin.register(PerfilUsuario)
class PerfilUsuarioAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'prefeitura', 'cargo', 'primeiro_acesso')