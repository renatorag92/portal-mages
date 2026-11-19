from django.contrib.auth.views import LogoutView
from django.urls import path
from .controllers import (
    controlador_acao,
    controlador_catalogo,
    controlador_consultoria,
    controlador_eixo,
    controlador_etapa,
    controlador_funcionario,
    controlador_kanban_dashboard,
    controlador_login,
    controlador_notificacao,
    controlador_prefeitura,
    controlador_status,
)

urlpatterns = [
    # Login, Logout e Sessão
    path('login/', controlador_login.CustomLoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(next_page='login'), name='logout'),
    path('redefinir-senha/', controlador_login.CustomPasswordChangeView.as_view(), name='redefinir-senha'),
    path('escolher-prefeitura/', controlador_login.escolher_prefeitura_view, name='escolher_prefeitura'),
    path('solicitar-redefinicao-senha/', controlador_login.solicitar_redefinicao_senha_view, name='solicitar_redefinicao_senha'),

    # Prefeitura
    path('cadastros/prefeitura/', controlador_prefeitura.gerenciar_prefeitura_view, name='gerenciar_prefeitura'),
    path('cadastros/prefeitura/salvar/', controlador_prefeitura.salvar_prefeitura_view, name='salvar_prefeitura'),

    # Consultoria
    path('cadastros/consultoria/', controlador_consultoria.gerenciar_consultoria_view, name='gerenciar_consultoria'),
    path('cadastros/consultoria/salvar/', controlador_consultoria.salvar_consultoria_view, name='salvar_consultoria'),

    # Funcionário e Conta
    path('minha-conta/', controlador_funcionario.minha_conta_view, name='minha_conta'),
    path('cadastros/funcionarios/', controlador_funcionario.gerenciar_funcionario_view, name='gerenciar_funcionario'),
    path('cadastros/funcionarios/<int:funcionario_id>/', controlador_funcionario.gerenciar_funcionario_view, name='editar_funcionario'),
    path('cadastros/funcionarios/<int:funcionario_id>/excluir/', controlador_funcionario.excluir_funcionario_view, name='excluir_funcionario'),
    path('cadastros/funcionarios/<int:funcionario_id>/gerar-senha/', controlador_funcionario.gerar_senha_funcionario_view, name='gerar_senha_funcionario'),

    # Eixo
    path('config/eixos/', controlador_eixo.gerenciar_eixo_view, name='gerenciar_eixo'),
    path('config/eixos/<int:eixo_id>/', controlador_eixo.gerenciar_eixo_view, name='editar_eixo'),
    path('config/eixos/<int:eixo_id>/excluir/', controlador_eixo.excluir_eixo_view, name='excluir_eixo'),

    # Catálogo de Ações
    path('config/catalogo/', controlador_catalogo.gerenciar_catalogo_view, name='gerenciar_catalogo'),
    path('config/catalogo/<int:modelo_id>/', controlador_catalogo.gerenciar_catalogo_view, name='editar_catalogo'),
    path('config/catalogo/<int:modelo_id>/excluir/', controlador_catalogo.excluir_catalogo_view, name='excluir_catalogo'),

    # Status
    path('config/status/', controlador_status.gerenciar_status_view, name='gerenciar_status'),
    path('config/status/<int:status_id>/', controlador_status.gerenciar_status_view, name='editar_status'),
    path('kanban/status/<int:status_id>/editar/', controlador_status.editar_status_kanban_view, name='editar_status_kanban'),

    # Kanban e Dashboard
    path('', controlador_kanban_dashboard.kanban_view, name='kanban'),
    path('dashboard/', controlador_kanban_dashboard.dashboard_view, name='dashboard'),

    # Ação
    path('acoes/criar/', controlador_acao.criar_acao_kanban_view, name='criar_acao_kanban'),
    path('acoes/<int:acao_id>/', controlador_acao.obter_detalhes_acao_view, name='obter_detalhes_acao'),
    path('acoes/<int:acao_id>/editar/', controlador_acao.editar_acao_view, name='editar_acao'),
    path('acoes/<int:acao_id>/excluir/', controlador_acao.excluir_acao_view, name='excluir_acao'),
    path('acoes/<int:acao_id>/status/', controlador_acao.atualizar_status_acao, name='atualizar_status_acao'),

    # Etapa
    path('acoes/<int:acao_id>/etapas/adicionar/', controlador_etapa.adicionar_etapa_view, name='adicionar_etapa'),
    path('etapas/<int:etapa_id>/editar/', controlador_etapa.editar_etapa_view, name='editar_etapa'),
    path('etapas/<int:etapa_id>/alterar/', controlador_etapa.alterar_etapa_view, name='alterar_etapa'),
    path('etapas/<int:etapa_id>/excluir/', controlador_etapa.excluir_etapa_view, name='excluir_etapa'),

    # Notificações
    path('notificacoes/atualizar/', controlador_notificacao.atualizar_notificacoes_view, name='atualizar_notificacoes'),
    path('notificacoes/<str:tipo>/<int:item_id>/lida/', controlador_notificacao.marcar_notificacao_lida_view, name='marcar_notificacao_lida'),
    path('notificacoes/<str:tipo>/<int:item_id>/nao-lida/', controlador_notificacao.marcar_notificacao_nao_lida_view, name='marcar_notificacao_nao_lida'),
    path('notificacoes/<str:tipo>/<int:item_id>/remover/', controlador_notificacao.remover_notificacao_view, name='remover_notificacao'),
    path('notificacoes/solicitacao-senha/<int:solicitacao_id>/lida/', controlador_notificacao.marcar_solicitacao_senha_lida_view, name='marcar_solicitacao_senha_lida'),
]