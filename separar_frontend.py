import os
import shutil
import subprocess

# 1. Caminhos
diretorio_atual = os.getcwd()
desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
novo_frontend_path = os.path.join(desktop_path, "PROJETO_FRONTEND_NOVO")
pasta_frontend_local = os.path.join(diretorio_atual, "frontend")

print("🚀 Iniciando a separação e organização do Frontend...")

# 2. Cria a nova pasta limpa na Área de Trabalho
if os.path.exists(novo_frontend_path):
    shutil.rmtree(novo_frontend_path)
os.makedirs(novo_frontend_path, exist_ok=True)

# 3. Lista de itens para copiar do frontend antigo
itens_para_copiar = [
    ".streamlit",
    "pages",
    "utils.py",
    "requirements.txt",
    "README.md",
    "styles.css"
]

# Copia pastas e arquivos utilitários
for item in itens_para_copiar:
    origem = os.path.join(pasta_frontend_local, item)
    destino = os.path.join(novo_frontend_path, item)
    
    if os.path.exists(origem):
        if os.path.isdir(origem):
            shutil.copytree(origem, destino)
            print(f"✅ Pasta copiada: {item}")
        else:
            shutil.copy2(origem, destino)
            print(f"✅ Arquivo copiado: {item}")

# 4. Copia o sidebar.py já renomeando para app.py na raiz do novo projeto
origem_sidebar = os.path.join(pasta_frontend_local, "sidebar.py")
destino_app = os.path.join(novo_frontend_path, "app.py")

if os.path.exists(origem_sidebar):
    shutil.copy2(origem_sidebar, destino_app)
    print("✅ 'sidebar.py' copiado e renomeado para 'app.py' com sucesso!")

# 5. Remove o rastreamento da pasta frontend antiga e apaga ela do backend
print("\n🧹 Limpando o projeto backend...")
try:
    subprocess.run(["git", "rm", "-r", "--cached", "frontend"], capture_output=True)
except Exception as e:
    pass

if os.path.exists(pasta_frontend_local):
    shutil.rmtree(pasta_frontend_local)
    print("✅ Pasta 'frontend' antiga removida do projeto backend.")

print("\n🎉 PRONTO! Seu frontend novinho e organizado tá na Área de Trabalho:")
print(f"👉 {novo_frontend_path}")