from django.urls import path
from . import views

urlpatterns = [
    path('', views.acao_list_view, name='acao_list'),
]

