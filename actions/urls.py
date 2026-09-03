from django.urls import path
from . import views

urlpatterns = [
<<<<<<< Updated upstream
    path('', views.acao_list_view, name='acao_list'),
=======
    path('', views.kanban_view, name='kanban'),
>>>>>>> Stashed changes
    path('actions/<int:acao_id>/atualizar_status/', views.atualizar_status_acao, name='atualizar_status_acao'),
]

