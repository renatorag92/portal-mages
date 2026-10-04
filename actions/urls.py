from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.kanban_view, name='kanban'),  # Rota para a página do Kanban
    path('kanban/status/', views.gerenciar_status_view, name='gerenciar_status'),
    path('kanban/status/<int:status_id>/editar/', views.gerenciar_status_view, name='editar_status'),
    path('kanban/status/<int:status_id>/excluir/', views.excluir_status_view, name='excluir_status'),
    path('kanban/criar-acao/', views.criar_acao_kanban_view, name='criar_acao_kanban'),  # Rota para criar uma ação
    path('kanban/acao/<int:acao_id>/', views.obter_detalhes_acao_view, name='obter_detalhes_acao'),  # Dados da ação e das etapas (pop-up de detalhes)
    path('kanban/acao/<int:acao_id>/editar/', views.editar_acao_view, name='editar_acao'),  # Rota para alterar dados de uma ação
    path('kanban/acao/<int:acao_id>/excluir/', views.excluir_acao_view, name='excluir_acao'),  # Rota para excluir uma ação
    path('kanban/etapa/<int:etapa_id>/editar/', views.editar_etapa_view, name='editar_etapa'),  # Rota para alterar dados de uma etapa
    path('kanban/etapa/<int:etapa_id>/concluir/', views.alterar_etapa_view, name='alterar_etapa'),  # Rota para marcar/desmarcar etapa como concluída
    path('login/', views.CustomLoginView.as_view(), name='login'),  # Rota do login
    path('cadastrar-acoes/', views.cadastro_acoes_view, name='cadastro_acoes'), # Antiga rota de cadastro (redireciona para o Kanban)
    path('redefinir-senha/', views.CustomPasswordChangeView.as_view(), name='redefinir-senha'),  # Rota para alterar a senha
    path('actions/<int:acao_id>/atualizar_status/', views.atualizar_status_acao, name='atualizar_status_acao'),  # Rota para atualizar o status da ação
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),  # Rota de logout
]