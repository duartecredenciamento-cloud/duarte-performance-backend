ATUALIZAÇÃO — APROVAÇÃO DE REDEFINIÇÃO DE SENHA

Arquivos deste pacote (substituir no serviço backend, mantendo as pastas):
- backend/main.py
- backend/static/index.html
- backend/static/app.js
- backend/static/app.css

O que muda:
- A área Equipe e acessos passa a ser exclusiva para Admin/Admin Master, conforme as permissões já impostas pela API.
- A fila administrativa lista solicitações, permite autorizar (validade de 10 minutos) ou rejeitar e mostra status/expiração.
- A interface apresenta erro explícito se o endpoint não conseguir consultar a tabela; não mostra uma fila vazia como se a consulta tivesse funcionado.
- A fila continua protegida pela autenticação e validação de administrador no backend.

Publicação segura:
1. Salve uma cópia dos quatro arquivos atuais.
2. Substitua somente estes quatro arquivos no projeto backend e publique o serviço backend. Não altere banco, volume, migrations, variáveis ou serviço frontend por causa desta atualização.
3. Entre com um usuário Admin/Admin Master, abra Equipe e acessos e use Atualizar na seção de solicitações.
4. Teste primeiro com uma conta de homologação: solicite redefinição com usuário/e-mail cadastrados, confirme que apareceu na fila, autorize e redefina em até 10 minutos; depois teste rejeição.

IMPORTANTE SOBRE O BANCO:
O código já possui o modelo e as rotas para a tabela `solicitacoes_senha`, mas esta entrega não confirma que essa tabela exista no banco de produção. Nenhuma migration nem alteração de banco foi incluída. Se a fila retornar erro informando ausência da tabela, pare e não habilite `ALLOW_SCHEMA_CREATE` em produção; é necessária uma migration específica após backup e confirmação do schema.

FRONTEND NO RAILWAY:
A base backend deste projeto serve a interface a partir de `backend/static` (raiz e `/app`). O serviço frontend separado é uma cópia Nginx da interface e encaminha chamadas à API. A existência de uma tela no domínio do backend não prova que o serviço separado deixou de ser usado. Não exclua o serviço ainda: confirme que o domínio público usado por todos é o do backend, que login e fluxos críticos funcionam numa janela anônima e que nenhum domínio/configuração externa ainda aponta para o frontend. Não altere nem remova o serviço de banco.

Validações deste pacote: sintaxe JavaScript e Python e integridade do ZIP. Não houve acesso ao Railway ou teste integrado com o banco/produção.
