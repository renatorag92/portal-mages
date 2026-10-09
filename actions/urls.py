from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.kanban_view, name='kanban'),  # Rota para a página do Kanban
    path('kanban/eixos/', views.gerenciar_eixo_view, name='gerenciar_eixo'),
    path('kanban/eixos/<int:eixo_id>/editar/', views.gerenciar_eixo_view, name='editar_eixo'),
    path('kanban/eixos/<int:eixo_id>/excluir/', views.excluir_eixo_view, name='excluir_eixo'),
    path('kanban/status/', views.gerenciar_status_view, name='gerenciar_status'),
    path('configuracoes/prefeitura/', views.gerenciar_prefeitura_view, name='gerenciar_prefeitura'),
    path('configuracoes/prefeitura/salvar/', views.salvar_prefeitura_view, name='salvar_prefeitura'),
    path('configuracoes/consultoria/', views.gerenciar_consultoria_view, name='gerenciar_consultoria'),
    path('configuracoes/consultoria/salvar/', views.salvar_consultoria_view, name='salvar_consultoria'),
    path('kanban/status/<int:status_id>/editar/', views.gerenciar_status_view, name='editar_status'), # Rota para alterar dados de um status
    path('kanban/status/<int:status_id>/editar-no-kanban/', views.editar_status_kanban_view, name='editar_status_kanban'),
    path('kanban/status/<int:status_id>/excluir/', views.excluir_status_view, name='excluir_status'), # Rota para excluir um status
    path('kanban/criar-acao/', views.criar_acao_kanban_view, name='criar_acao_kanban'),  # Rota para criar uma ação
    path('kanban/acao/<int:acao_id>/', views.obter_detalhes_acao_view, name='obter_detalhes_acao'),  # Dados da ação e das etapas (pop-up de detalhes)
    path('kanban/acao/<int:acao_id>/editar/', views.editar_acao_view, name='editar_acao'),  # Rota para alterar dados de uma ação
    path('kanban/acao/<int:acao_id>/excluir/', views.excluir_acao_view, name='excluir_acao'),  # Rota para excluir uma ação
    path('kanban/etapa/<int:etapa_id>/editar/', views.editar_etapa_view, name='editar_etapa'),  # Rota para alterar dados de uma etapa
    path('kanban/acao/<int:acao_id>/etapas/nova/', views.adicionar_etapa_view, name='adicionar_etapa'),  # Rota para adicionar uma etapa
    path('kanban/etapa/<int:etapa_id>/concluir/', views.alterar_etapa_view, name='alterar_etapa'),  # Rota para marcar/desmarcar etapa como concluída
    path('kanban/etapa/<int:etapa_id>/excluir/', views.excluir_etapa_view, name='excluir_etapa'),  # Rota para excluir uma etapa
    path('login/', views.CustomLoginView.as_view(), name='login'),  # Rota do login
    path('redefinir-senha/', views.CustomPasswordChangeView.as_view(), name='redefinir-senha'),  # Rota para alterar a senha
    path('actions/<int:acao_id>/atualizar_status/', views.atualizar_status_acao, name='atualizar_status_acao'),  # Rota para atualizar o status da ação
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),  # Rota de logout
]