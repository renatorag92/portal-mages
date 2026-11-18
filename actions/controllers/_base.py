import json
from django.http import JsonResponse


def carregar_json(request):
    try:
        dados = json.loads(request.body or '{}')
    except (json.JSONDecodeError, UnicodeDecodeError):
        return None
    return dados if isinstance(dados, dict) else None


def erros_formulario(form):
    return {
        campo: [erro['message'] for erro in erros]
        for campo, erros in form.errors.get_json_data().items()
    }


def erro_json(mensagem, status=400):
    return JsonResponse({'success': False, 'error': mensagem}, status=status)


def usuario_configuracoes(user):
    return user.is_authenticated and (user.is_superuser or user.e_consultor)