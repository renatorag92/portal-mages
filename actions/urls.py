from django.urls import path
from . import views
from django.contrib.auth.views import LogoutView

urlpatterns = [
    path('', views.kanban_view, name='kanban'),  # Rota para a página do Kanban
    path('login/', views.CustomLoginView.as_view(), name='login'),  # Rota do login
    path('alterar_senha/', views.CustomPasswordChangeView.as_view(), name='password-change'),  # Rota para alterar a senha
    path('actions/<int:acao_id>/atualizar_status/', views.atualizar_status_acao, name='atualizar_status_acao'),  # Rota para atualizar o status da ação
    path('logout/', LogoutView.as_view(next_page='/login/'), name='logout'),  # Rota de logout
]