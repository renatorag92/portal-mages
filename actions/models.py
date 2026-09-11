from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.contrib.auth.views import PasswordChangeView
from django.urls import reverse_lazy # Importa o modelo de usuário do Django
from django.dispatch import receiver # Importa o sinal para criar o perfil do usuário automaticamente
from .choices import Status_status, Status_prioridade, Status_eixo

class Acao(models.Model):

    codigo = models.CharField(max_length=10, unique=True) # ex.: A001, A002, etc.
    nome = models.CharField(max_length=100)
    eixo = models.CharField(max_length=100, choices=Status_eixo)
    prioridade = models.CharField(max_length=20, choices=Status_prioridade)
    responsavel = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20, choices=Status_status, default='planejado')            
    custo = models.DecimalField(max_digits=10, decimal_places=2)
    observacao = models.TextField(blank=True, null=True)
    prefeitura = models.ForeignKey('Prefeitura', on_delete=models.CASCADE, related_name='acoes')
    
    class Meta:
        verbose_name_plural = 'Ações'
        
    # Retorna o nome da etapa quando for chamado o objeto
    def __str__(self):
        return f"{self.codigo} - {self.nome}" 

class Etapa(models.Model):
    
    acao = models.ForeignKey(Acao, on_delete=models.CASCADE, related_name='etapas')
    etapa = models.CharField(max_length=100)
    responsavel = models.CharField(max_length=100)
    data_inicio = models.DateField()
    data_fim = models.DateField()
    status = models.CharField(max_length=20, choices=Status_status, default='planejado')
    prioridade = models.CharField(max_length=20, choices=Status_prioridade)
    observacao = models.TextField(blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Etapas'

    # Retorna o codigo e o nome da ação quando for chamado o objetodef __str__(self):
    def __str__(self):
        return self.etapa
    
class Prefeitura(models.Model):
    nome = models.CharField(max_length=100) # ex.: Prefeitura Municipal de Nova Cruz
    sigla = models.CharField(max_length=10, blank=True, null=True) # Se tiver
    cidade = models.CharField(max_length=100) # ex.: Nova Cruz/RN
        
    def __str__(self):
        return self.nome
        
class PerfilUsuario(models.Model):
    # Conecta o modelo PerfilUsuario com o modelo User do Django
    # OneToOneField garante que cada usuário tenha apenas um perfil
    usuario = models.OneToOneField(User, on_delete=models.CASCADE, related_name='perfil')
    primeiro_acesso = models.BooleanField(default=True) # Indica se é o primeiro acesso do usuário 
    prefeitura = models.ForeignKey(Prefeitura, on_delete=models.CASCADE, related_name='usuarios', default=None, null=True, blank=True)
    cargo = models.CharField(max_length=100) # ex.: Gestor, Secretário, etc.
    
    def __str__(self):
        return f"{self.usuario.username} - {self.cargo}"
        
class CustomPasswordChangeView(PasswordChangeView):
    template_name = 'actions/password-change.html'
    success_url = reverse_lazy('kanban') # Redireciona para a página do Kanban após a alteração da senha
    def form_valid(self, form):
        response = super().form_valid(form) # Chama o método form_valid da classe pai para processar a alteração da senha
       
        # Atualiza o campo primeiro_acesso para False após a alteração da senha
        self.request.user.perfil.primeiro_acesso = False
        self.request.user.perfil.save()
        
        return response
    

# @receiver(post_save, sender=User)
# def criar_ou_atualizar_perfil_usuario(sender, instance, created, **_kwargs):
#     if created:
#         PerfilUsuario.objects.get_or_create(usuario=instance)
#     else:
#         if hasattr(instance, 'perfilusuario'):
#             instance.perfilusuario.save()
        

        
        
        
        



