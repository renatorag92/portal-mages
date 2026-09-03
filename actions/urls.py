from django.urls import path
from . import views

urlpatterns = [
    path('', views.kanban_view, name='kanban'),  
    path('login/', views.login_view, name='login'), # Rota do login
    path('actions/<int:acao_id>/atualizar_status/', views.atualizar_status_acao, name='atualizar_status_acao'),
]

