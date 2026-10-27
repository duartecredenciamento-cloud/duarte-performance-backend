DUARTE PERFORMANCE — RECUPERAÇÃO ADMINISTRATIVA DE ACESSO

Arquivos deste pacote (substituir no serviço backend):
- backend/main.py
- backend/static/app.js
- backend/static/index.html
- backend/static/app.css

O que muda:
Na seção Equipe e acessos, somente o perfil Admin/Admin Master terá a ação 🔑 para definir uma nova senha para o funcionário. A senha não é consultável. A senha nova deve ter pelo menos 12 caracteres e será gravada como hash. A ação exige autenticação administrativa e fica registrada na auditoria.

Como usar após publicação:
1. Entre com uma conta Admin.
2. Abra Equipe e acessos e atualize a lista.
3. Na linha do funcionário, clique no ícone de chave.
4. Defina uma senha temporária forte (12+ caracteres), confirme e compartilhe diretamente com o funcionário por canal privado.
5. Oriente a pessoa a entrar e depois trocar a senha, se o sistema oferecer essa opção. A senha temporária não expira automaticamente nesta versão; por isso, peça que ela faça login e altere para uma senha própria assim que possível.

Importante:
- Não altera tabelas, migrations, banco, volume ou configuração Railway.
- Não publica automaticamente; você precisa aplicar os quatro arquivos no projeto e publicar o backend.
- Este pacote foi montado a partir do projeto enviado. A integração com o Railway e com o banco de produção não foi testada.
- Não apague o serviço frontend nem mude o domínio por causa desta correção.
- Faça a substituição dos arquivos com backup do código atual; não substitua arquivos do projeto que não estão listados.
