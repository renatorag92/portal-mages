# Portal MAGES
Sistema web de Gestão Estratégica e Kanban.

## Requisitos

- Python 3.12 ou 3.13
- PostgreSQL 16
- Node.js (para os estilos Tailwind)
- Git

## Como rodar o projeto localmente

### 1. Clonar o repositório

```bash
git clone <url-do-repositorio>
cd portal-mages
```

### 2. Instalar o PostgreSQL

**Fedora:**

```bash
sudo dnf install postgresql-server postgresql
sudo postgresql-setup --initdb
sudo systemctl enable --now postgresql
```

**Ubuntu:**

```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl enable --now postgresql
```

### 3. Criar o usuário e o banco

```bash
sudo -u postgres psql
```

Dentro do `psql`:

```sql
CREATE USER mages WITH PASSWORD 'troque-esta-senha' CREATEDB;
CREATE DATABASE mages OWNER mages;
\q
```

### 4. Permitir login por senha (apenas Fedora)

No Fedora, o PostgreSQL vem com autenticação `ident` nas conexões por TCP, o que impede o login com usuário e senha usado pelo Django. Edite:

```bash
sudo nano /var/lib/pgsql/data/pg_hba.conf
```

Nas linhas `host` do fim do arquivo, troque `ident` por `scram-sha-256`:

```
host    all    all    127.0.0.1/32    scram-sha-256
host    all    all    ::1/128         scram-sha-256
```

Reinicie o serviço:

```bash
sudo systemctl restart postgresql
```

No Ubuntu, normalmente esse passo não é necessário.

### 5. Configurar as variáveis de ambiente

```bash
cp .env.example .env
```

Abra o `.env` e defina `POSTGRES_PASSWORD` com a mesma senha do passo 3. O arquivo `.env` não vai para o repositório.

Para testar a conexão antes de seguir:

```bash
psql -h localhost -U mages -d mages
```

Se pedir a senha e entrar, siga em frente.

### 6. Ativar o ambiente virtual e instalar as dependências Python

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 7. Instalar o Node.js e gerar os estilos

```bash
npm install
npm run build:css
```

Durante o desenvolvimento, use `npm run watch:css` para atualizar os estilos automaticamente. Deixe esse comando rodando em outro terminal.

### 8. Criar as tabelas e carregar os dados

```bash
python manage.py migrate
python manage.py carregar_dados_iniciais
python manage.py criar_usuario_padrao
```

- `carregar_dados_iniciais` cria eixos, status e o catálogo de ações. Pode ser executado várias vezes sem duplicar registros.
- `criar_usuario_padrao` cria uma consultoria, uma prefeitura, um consultor e um secretário para testes. Só funciona com `DEBUG` ligado.

### 9. Iniciar o servidor

```bash
python manage.py runserver
```

Acesse http://127.0.0.1:8000 e entre com:

| Perfil | CPF | Senha |
|---|---|---|
| Consultor | 12345678901 | senha123 |
| Secretário |98765432102 | senha123 |