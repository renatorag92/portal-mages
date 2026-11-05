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