# Duarte Performance 2.0 — base de modernização e homologação

Esta entrega contém uma nova interface HTML/CSS/JavaScript servida pela aplicação FastAPI mantida, mais o backend legado copiado para uma área de homologação. **Não é uma migração de produção concluída.** Não foi fornecido acesso ao Railway/banco produtivo nem evidência de que os bancos SQLite anexados sejam a fonte de produção. Não aponte esta versão à produção até concluir as salvaguardas deste documento.

## O que foi analisado

Os dois ZIPs foram descompactados e os arquivos-fonte foram inspecionados. O Duarte Performance contém Streamlit, Python 3.12, FastAPI, SQLAlchemy, JWT/bcrypt e arquivos SQLite diversos; a configuração aponta para Railway por `BACKEND_URL` e recebe `DATABASE_URL`, mas não veio configuração verificável do projeto hospedado. A referência Duarte Repay usa servidor Python próprio, HTML/CSS/JS e SQLite com diretório configurável, cookie de sessão HttpOnly, dashboard, menu responsivo e componentes premium. Foram adaptados princípios de navegação, hierarquia tipográfica, dark navy, acentos quentes/azuis, responsividade, feedback e redução de movimento — não foram copiados seus fluxos de reembolso.

## Inventário relevante e riscos conhecidos

- API original: `/token`, `/usuarios/`, `/usuarios/me`, `/usuarios/{id}/role`, `/registros/`, `/cronograma/`, `/recuperar-senha/`, `/admin/solicitacoes-senha/`, health e diagnóstico. O backend não implementa várias rotas referidas pela UI antiga (entre elas editar/excluir apontamentos e editar/excluir linhas de escala), embora a UI as tente chamar.
- Frontend Streamlit: login/cadastro/recuperação, dashboard com filtros, KPIs, insights e gráficos; escala semanal; lançamento diário; relatórios semanais/mensais/personalizados e exportação; editor de apontamentos; painel administrativo. Há discrepâncias entre as operações existentes na API e a interface.
- Dados anexados: `backend/duarte_performance.db` tem 122.880 bytes, tabelas `users` (1 linha), `usuarios` (1), `departamentos` (1), `registros`, `cronogramas`, logs e clientes vazios; `duarte_gestao.db` tem usuários legados (3), mas tabelas de reembolso/log/notificações vazias; outro `duarte_performance.db` tem zero bytes. Resumo com SHA-256 e contagens está em `docs/inventario-bancos.json`. Não são prova do estado do banco de produção.
- Esquema FastAPI `users`/`registros` não coincide necessariamente com os esquemas SQLite legados `usuarios`/`cronogramas` e o banco separado `duarte_gestao.db`. O backend executava `create_all` no import; isso pode criar tabelas em banco vazio sem migrar dados. Um `reset_db.bat` apaga SQLite e `init_db.py` insere credenciais padrão em texto claro; não execute esses scripts em produção.
- Segredo JWT hard-coded aparece num módulo de configuração legado, mas o FastAPI exige `SECRET_KEY` com 32+ caracteres. CORS antigo aceitava `*` com credenciais; nesta base foi restrito e só habilitado quando origens explicitamente configuradas. Cadastro público antigo recebeu proteção de admin. Algumas rotas de registros e cronograma eram acessíveis sem autenticação; foram protegidas.
- Evidências: modelo atual contém campo `caminho_evidencia`, mas o FastAPI revisado no anexo não expõe upload/download desse campo. Necessário localizar o armazenamento real e migrar/cotejar uploads antes da troca. O banco/anexos mostram nenhuma pasta de evidência, sem provar que produção não tenha uploads.
- Deploy conhecido apenas parcialmente: Dockerfile FastAPI usa Uvicorn e `PORT`; composição local PostgreSQL inclui credenciais fixas de exemplo e volume Docker. Arquivos indicam Railway, mas não há painel, volume, variáveis, URL de produção do banco, política de backup, domínio ou logs. Não há prova de que Railway use esse PostgreSQL/SQLite.

## Funcionalidade nesta base

- Login `/token` e perfil `/usuarios/me` usando JWT; token guardado em `sessionStorage` no navegador (aceita risco de XSS maior do que cookie HttpOnly; reduzir superfícies e CSP é obrigatório). Não usar em domínio hostil.
- Painel com KPIs, status, atividade recente, página de registros com busca/status/data, dashboard filtrável e CSV; dados vêm da API atual (máximo 500 registros por consulta; totais podem ser incompletos para histórico maior).
- Lançamento, justificativa obrigatória e registro de quem lançou, data e período; operação é conferida também na API.
- Escala consultada da API; perfil de gestão pode adicionar e, no backend, editar/excluir linhas. Editor de apontamentos para gestão foi implementado no backend, mas ainda não há controles de edição/exclusão nessa UI.
- Consulta de equipe só para Admin. Não foram inventados fluxos de recuperação de senha, solicitações de senha, logs administrativos completos, anexos ou administrador de usuário para os quais o backend não tem contrato confiável.
- Não foi incluída a escala estática embutida no app Streamlit como dado real, pois não pode substituir a fonte dinâmica do backend.

## Rodar localmente (Windows / VS Code)

1. Instale Python 3.12 e abra a pasta `backend` no VS Code.
2. No PowerShell:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

3. Edite `.env` com segredo local aleatório e banco local descartável:

```text
APP_ENV=development
LOCAL_DB_PATH=./data/duarte_performance_dev.sqlite3
ALLOW_SCHEMA_CREATE=true
SECRET_KEY=coloque-um-segredo-aleatorio-local-com-mais-de-32-caracteres
```

4. Carregue valores sem commitar `.env` e rode:

```powershell
Get-Content .env | Where-Object { $_ -match '^\s*[^#].*=' } | ForEach-Object { $n,$v=$_.Split('=',2); Set-Item -Path "Env:$n" -Value $v }
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

Abra `http://127.0.0.1:8000`. Em banco local recém-criado não há usuário por padrão. Cadastre/provisione um usuário em ambiente de desenvolvimento seguindo o processo controlado da organização; não coloque dados ou senhas reais no SQLite de teste.

## Deploy — apenas preparação, não executar contra produção ainda

O backend deve servir a interface e API pela mesma origem. Use o Dockerfile e defina `PORT` fornecida pelo serviço, `APP_ENV=production`, `DATABASE_URL` apontando ao banco persistente correto e `SECRET_KEY` longo, único e guardado no gerenciador de segredos. Se frontend estiver em origem externa, configure só os domínios HTTPS reais em `CORS_ORIGINS`. Não ative `ALLOW_SCHEMA_CREATE` em produção.

**Não faça deploy dessa cópia antes de: identificar e documentar serviço e banco de produção; backup completo do banco e arquivos de evidência; restauração ensaiada em homologação; contagens e checksums; mapa aprovado de tabelas/colunas/IDs; migrações Alembic validadas em clone; comparação dos mesmos indicadores no antigo e novo; compatibilidade de hashes de senha; verificar usuários, cronogramas, registros, justificativas, auditoria e anexos; política de rollback.** O arquivo Alembic incluído é baseline vazia, não transforma tabelas. A ferramenta `migrar-legado.py` apenas faz cópia auditável de um SQLite não vazio para destino novo e recusa sobrescrever; não é migrador de esquema, nem copia produção.

Procedimento recomendado: congelar gravações por janela aprovada; fazer backup pelo provedor e cópia dos arquivos anexados; baixar cópia de homologação; rodar inventário e hashes; testar restauração; construir migrações específicas após analisar o schema real; executar em clone; cotejar contagens, chaves e relatórios; fazer cutover com plano de retorno; manter aplicação e banco antigos sem mutação destrutiva até aceitação.

## Testes incluídos e limitações

```powershell
python -m unittest discover -s tests -v
node --check static\app.js
```

Há testes unitários de regras e smoke de interface/health/API. Não foi possível executá-los neste ambiente, pois dependências do backend (FastAPI, SQLAlchemy, JWT, Passlib, Uvicorn e pytest) não estão instaladas e a instalação de pacotes não foi tentada. A validação de sintaxe JS passou. O frontend foi implementado, mas não foi carregado num browser; responsividade/accessibilidade visual ainda precisa de QA manual. Sem credenciais ou serviço de produção, não se testou integração com o backend ativo, reinício contra banco real, restauração, anexos nem regressão operacional completa.

## Segurança e dados pessoais

CPF e informações operacionais são dados pessoais/empresariais. Restringir acesso, usar TLS, rotacionar segredos legados, revisar logs, limitar tentativas, formalizar retenção e base legal LGPD, revisar sessionStorage frente ao XSS, rate-limit login, verificar `Origin`/CSRF se migrar para cookies, validar anexos por conteúdo/tipo/tamanho e implantar storage privado durável. Não enviar senhas, JWT, CPF ou evidências em logs públicos.

## Variáveis

`APP_ENV`, `PORT`, `DATABASE_URL`, `LOCAL_DB_PATH` (somente desenvolvimento), `SECRET_KEY`, `CORS_ORIGINS`, `ALLOW_SCHEMA_CREATE` (somente desenvolvimento), `ADMIN_BOOTSTRAP_USERNAME`, `ADMIN_BOOTSTRAP_PASSWORD`, `ADMIN_BOOTSTRAP_RESET_EXISTING`. O bootstrap só cria se conta não existe; não configurar reset na rotina normal.

## Conteúdo do pacote

`backend/` — FastAPI atual protegido, frontend estático, Dockerfile, dependências, Alembic baseline e testes. `docs/inventario-bancos.json` — resumo verificável de arquivos SQLite fornecidos. A interface Streamlit original permanece preservada no ZIP original anexado; esta entrega não a apaga nem troca o sistema publicado.
