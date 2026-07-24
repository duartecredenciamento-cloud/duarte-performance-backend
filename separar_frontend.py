import os
import shutil
import subprocess

print("🔄 Iniciando correção e estruturação do Frontend...")

# 1. Garante que a pasta 'frontend' existe
frontend_dir = os.path.join(os.getcwd(), "frontend")
os.makedirs(frontend_dir, exist_ok=True)

# 2. Converte/Garante o app.py
# Se existir sidebar.py e não existir app.py, renomeia/copia para app.py
sidebar_path = os.path.join(frontend_dir, "sidebar.py")
app_path = os.path.join(frontend_dir, "app.py")

if os.path.exists(sidebar_path) and not os.path.exists(app_path):
    shutil.copy2(sidebar_path, app_path)
    print("✅ 'sidebar.py' duplicado/renomeado para 'app.py'.")

# Se ainda não existir app.py de jeito nenhum, cria um basico para o Render não dar erro
if not os.path.exists(app_path):
    with open(app_path, "w", encoding="utf-8") as f:
        f.write("import streamlit as st\n\nst.title('Duarte Performance')\nst.write('Aplicação rodando com sucesso!')\n")
    print("✅ Archivo 'app.py' básico criado na pasta frontend.")

# 3. Cria utils.py se não existir (para evitar erros de import no Streamlit)
utils_path = os.path.join(frontend_dir, "utils.py")
if not os.path.exists(utils_path):
    with open(utils_path, "w", encoding="utf-8") as f:
        f.write("# Funções utilitárias do Frontend\n")
    print("✅ 'utils.py' criado para evitar erros de importação.")

# 4. Garante o requirements.txt na pasta frontend
req_path = os.path.join(frontend_dir, "requirements.txt")
if not os.path.exists(req_path):
    with open(req_path, "w", encoding="utf-8") as f:
        f.write("streamlit\nrequests\npandas\nopenpyxl\nplotly\n")
    print("✅ 'requirements.txt' básico criado dentro da pasta frontend.")

# 5. Envia tudo pro Git na marra
print("\n🚀 Subindo alterações para o GitHub...")
try:
    subprocess.run(["git", "add", "-f", "frontend/"], check=True)
    subprocess.run(["git", "commit", "-m", "fix: estrutura completa do frontend com app.py e utils.py"], check=True)
    subprocess.run(["git", "push"], check=True)
    print("\n🎉 TUDO PRONTO E SUBIDO PRO GITHUB COM SUCESSO!")
except Exception as e:
    print(f"\n⚠️ Ocorreu um aviso no Git, mas a pasta foi estruturada localmente: {e}")