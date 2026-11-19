from .controllers.controlador_login import (
    CustomLoginView,
    CustomPasswordChangeView,
    escolher_prefeitura_view,
    solicitar_redefinicao_senha_view,
)
from .controllers.controlador_prefeitura import (
    gerenciar_prefeitura_view,
    salvar_prefeitura_view,
)
from .controllers.controlador_consultoria import (
    gerenciar_consultoria_view,
    salvar_consultoria_view,
)
from .controllers.controlador_funcionario import (
    excluir_funcionario_view,
    gerar_senha_funcionario_view,
    gerenciar_funcionario_view,
    minha_conta_view,
)
from .controllers.controlador_eixo import (
    excluir_eixo_view,
    gerenciar_eixo_view,
)
from .controllers.controlador_catalogo import (
    excluir_catalogo_view,
    gerenciar_catalogo_view,
)
from .controllers.controlador_status import (
    editar_status_kanban_view,
    gerenciar_status_view,
)
from .controllers.controlador_kanban_dashboard import (
    dashboard_view,
    kanban_view,
)
from .controllers.controlador_acao import (
    atualizar_status_acao,
    criar_acao_kanban_view,
    editar_acao_view,
    excluir_acao_view,
    obter_detalhes_acao_view,
)
from .controllers.controlador_etapa import (
    adicionar_etapa_view,
    alterar_etapa_view,
    editar_etapa_view,
    excluir_etapa_view,
)
from .controllers.controlador_notificacao import (
    atualizar_notificacoes_view,
    marcar_notificacao_lida_view,
    marcar_notificacao_nao_lida_view,
    marcar_solicitacao_senha_lida_view,
    remover_notificacao_view,
)
