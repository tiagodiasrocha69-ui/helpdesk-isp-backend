
# HelpDesk ISP — Backend

## Projeto Integrador II

Universidade Estadual do Piauí — UESPI  
Universidade Aberta do Piauí — UAPI  
Curso: Tecnologia em Sistemas para Internet

Versão: 1.0.0

## Sobre o projeto

O HelpDesk ISP é um sistema web desenvolvido para
gerenciar chamados técnicos de provedores de internet.

O sistema centraliza informações sobre clientes,
técnicos, usuários e atendimentos, permitindo acompanhar
todo o ciclo de vida de um chamado técnico.

Este repositório contém o backend da aplicação,
responsável pelas regras de negócio, autenticação,
controle de acesso e persistência dos dados.

## Objetivos

- Centralizar o gerenciamento de chamados técnicos.
- Organizar o cadastro de clientes e técnicos.
- Controlar a distribuição dos atendimentos.
- Acompanhar o andamento dos chamados.
- Registrar o histórico das movimentações.
- Auxiliar a tomada de decisões por meio de indicadores
  e relatórios.

## Tecnologias utilizadas

- Python
- Flask
- Flask-CORS
- SQLite
- Werkzeug
- API REST
- JSON
- Git e GitHub

## Funcionalidades

### Autenticação e segurança

- Login e logout.
- Autenticação baseada em sessão.
- Controle de acesso por perfil.
- Armazenamento de senhas com hash.
- Validação de usuários ativos.
- Redefinição de senhas.
- Invalidação de sessões após alteração de senha.
- Configuração de chave secreta por variável de ambiente.

### Clientes

- Cadastro de clientes.
- Consulta de clientes.
- Atualização de dados.
- Exclusão de registros sem chamados vinculados.

### Técnicos

- Cadastro de técnicos.
- Criação de contas de acesso.
- Atualização de informações.
- Controle de disponibilidade.
- Gerenciamento de vínculos com chamados.

### Chamados técnicos

- Abertura de chamados.
- Definição de prioridade.
- Consulta e filtragem.
- Atribuição manual de técnicos.
- Início do atendimento.
- Encerramento do chamado.
- Registro da solução.
- Histórico de movimentações.

### Dashboard

- Total de chamados.
- Chamados abertos.
- Chamados em andamento.
- Chamados concluídos.
- Total de clientes.
- Total de técnicos.
- Técnicos disponíveis.
- Taxa de resolução.
- Distribuição por prioridade.
- Chamados recentes.

### Gerenciamento de usuários

- Cadastro de usuários.
- Consulta de usuários.
- Atualização de informações.
- Alteração de perfis.
- Ativação e desativação de contas.
- Redefinição de senhas.
- Proteção da própria conta administrativa.

### Relatórios

- Filtro por período.
- Filtro por técnico.
- Filtro por status.
- Filtro por prioridade.
- Taxa de resolução.
- Tempo médio de resolução.
- Desempenho dos técnicos.
- Listagem detalhada de atendimentos.

A exportação CSV e PDF é realizada pelo frontend.

## Perfis de acesso

| Perfil | Responsabilidade |
|---|---|
| Administrador | Gerenciamento geral do sistema |
| Atendente | Cadastro de clientes e abertura de chamados |
| Técnico | Atendimento dos chamados atribuídos |
| Gerente | Consulta de indicadores e relatórios |

## Estrutura do projeto

```text
helpdesk-isp-backend/
├── app.py
├── auth.py
├── database.py
├── clientes.py
├── tecnicos.py
├── chamados.py
├── dashboard.py
├── usuarios.py
├── relatorios.py
├── requirements.txt
├── .gitignore
└── README.md
```

## Banco de dados

O sistema utiliza SQLite para armazenamento
persistente das informações.

Principais tabelas:

- usuarios
- clientes
- tecnicos
- chamados
- historico_chamados

O banco de dados é criado automaticamente durante
a inicialização da aplicação.

## Instalação e execução

### 1. Clonar o repositório

```bash
git clone https://github.com/tiagodiasrocha69-ui/helpdesk-isp-backend.git
cd helpdesk-isp-backend
```

### 2. Criar o ambiente virtual

```powershell
python -m venv venv
```

### 3. Ativar o ambiente virtual no Windows

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
.\venv\Scripts\Activate.ps1
```

### 4. Instalar as dependências

```powershell
python -m pip install -r requirements.txt
```

### 5. Configurar a chave secreta

```powershell
$env:SECRET_KEY = (python -c "import secrets; print(secrets.token_hex(32))")
```

### 6. Configurar a senha inicial do administrador

Na primeira execução, defina ADMIN_PASSWORD com
uma senha de pelo menos 12 caracteres.

```powershell
$env:ADMIN_PASSWORD = Read-Host "Senha inicial do administrador"
```

Essa configuração é necessária para a criação inicial
da conta administrativa.

O login inicial do administrador é admin.

### 7. Iniciar a aplicação

```powershell
python app.py
```

A API estará disponível em:

http://127.0.0.1:5000

### 8. Verificar o funcionamento da API

Acesse:

http://127.0.0.1:5000/api/health

## Principais endpoints

| Método | Endpoint | Descrição |
|---|---|---|
| GET | /api/health | Verificar disponibilidade |
| POST | /api/login | Autenticar usuário |
| POST | /api/logout | Encerrar sessão |
| GET | /api/me | Consultar usuário autenticado |
| GET | /api/clientes | Listar clientes |
| POST | /api/clientes | Cadastrar cliente |
| GET | /api/tecnicos | Listar técnicos |
| POST | /api/tecnicos | Cadastrar técnico |
| GET | /api/chamados | Listar chamados |
| POST | /api/chamados | Abrir chamado |
| GET | /api/chamados/{id} | Consultar chamado |
| PUT | /api/chamados/{id}/atribuir | Atribuir técnico |
| PUT | /api/chamados/{id}/status | Atualizar status |
| GET | /api/chamados/{id}/historico | Consultar histórico |
| GET | /api/dashboard | Consultar indicadores |
| GET | /api/usuarios | Listar usuários |
| POST | /api/usuarios | Cadastrar usuário |
| PUT | /api/usuarios/{id} | Atualizar usuário |
| PUT | /api/usuarios/{id}/status | Alterar situação |
| PUT | /api/usuarios/{id}/senha | Redefinir senha |
| GET | /api/relatorios | Gerar relatório |

## Fluxo de atendimento

1. Cadastro do cliente.
2. Abertura do chamado técnico.
3. Definição da prioridade.
4. Atribuição de um técnico.
5. Início do atendimento.
6. Registro da solução.
7. Encerramento do chamado.
8. Consulta do histórico e dos relatórios.

## Integração com o frontend

O backend disponibiliza uma API REST consumida
pelo frontend desenvolvido em React.

Repositório do frontend:

https://github.com/tiagodiasrocha69-ui/HelpDesk-ISP

O frontend deve ser executado localmente na porta 5173.

## Testes e qualidade

Foram realizadas verificações de:

- Autenticação e controle de acesso.
- Operações de cadastro.
- Integração entre frontend e backend.
- Persistência de dados.
- Fluxo de atendimento técnico.
- Geração de indicadores.
- Relatórios e filtros.
- Sintaxe dos arquivos Python.
- Compatibilidade das dependências.

## Segurança

O projeto utiliza:

- Senhas protegidas por hash.
- Consultas SQL parametrizadas na autenticação.
- Controle de acesso por perfil.
- Cookies HttpOnly e SameSite.
- Chave secreta por variável de ambiente.
- CORS restrito ao ambiente local.
- Modo debug desativado.
- Arquivos sensíveis ignorados pelo Git.

A configuração atual destina-se ao ambiente acadêmico
e de desenvolvimento local.

Uma implantação pública exige configurações adicionais,
incluindo HTTPS, proteção CSRF, limitação de tentativas
de autenticação e servidor apropriado para produção.

## Metodologia de desenvolvimento

O desenvolvimento foi organizado em etapas
incrementais, com versionamento pelo GitHub
e planejamento de atividades pelo Trello.

## Status do projeto

Versão funcional desenvolvida para a disciplina
Projeto Integrador II.

## Finalidade acadêmica

Projeto desenvolvido para fins acadêmicos no curso
de Tecnologia em Sistemas para Internet da UESPI/UAPI.
