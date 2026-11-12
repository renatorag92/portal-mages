# Portal MAGES
Sistema web de Gestão Estratégica e Kanban.

### Como rodar o projeto localmente

- Clonar o repositório e ativar o ambiente virtual (.venv).

- Instalar as dependências (pip install -r requirements.txt).

- Instalar o Node.js e gerar os estilos responsivos do Tailwind:
  - `npm install`
  - `npm run build:css`
  - Durante o desenvolvimento, use `npm run watch:css` para atualizar os estilos automaticamente.

- Rodar as migrações do banco (python manage.py migrate).

- Carregar dados iniciais (Eixos e Catálogo de ações) -> (python manage.py carregar_dados_iniciais) 

- Executar o comando do usuário padrão (python manage.py criar_usuario_padrao)
     - Após criar o usuario padrão os Logins são: CPF 12345678909 (consultor) e CPF 98765432100 (secretário). Senha: senha123 (para ambos)

- Iniciar o servidor (python manage.py runserver)

### Solicitação de troca de senha

Na tela de login, o funcionário pode selecionar **Esqueci minha senha** e informar o CPF
já preenchido. Os consultores recebem uma notificação com o nome do solicitante. Na tela
de funcionários, o consultor gera a senha provisória; no próximo acesso, o funcionário
deve definir uma nova senha. O consultor também pode marcar a solicitação como lida sem
gerar a senha imediatamente. As notificações são atualizadas automaticamente a cada
10 segundos enquanto a página está aberta. Nos alertas de prazo, tarefas que vencem
amanhã ficam em vermelho e prazos já vencidos recebem um destaque próprio com a indicação
de atraso.