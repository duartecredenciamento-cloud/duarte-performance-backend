import os
import shutil

def organizar_projeto():
    # Caminho raiz onde o script está rodando
    raiz = os.getcwd()
    
    print("🚀 Iniciando organização das pastas e arquivos...\n")

    # 1. Mapeamento de onde cada arquivo/extensão deve ficar
    # (Origem na raiz -> Destino)
    regras_arquivos = {
        # Arquivos do Frontend que estavam soltos na raiz
        "app.py": "frontend",
        "style.css": "frontend",
        "sidebar.py": "frontend",
        "utils.py": "frontend",
        
        # Arquivos do Backend
        "main.py": "backend",
        "database.py": "backend",
        
        # Logs e documentações soltas
        "duarte_performance.log": "logs",
    }

    # 2. Garantir que as pastas principais existam
    pastas_necessarias = ["frontend", "backend", "logs"]
    for pasta in pastas_necessarias:
        caminho_pasta = os.path.join(raiz, pasta)
        if not os.path.exists(caminho_pasta):
            os.makedirs(caminho_pasta)
            print(f"📁 Pasta criada: {pasta}/")

    # 3. Mover arquivos mapeados
    for arquivo, pasta_destino in regras_arquivos.items():
        caminho_origem = os.path.join(raiz, arquivo)
        caminho_destino = os.path.join(raiz, pasta_destino, arquivo)

        if os.path.exists(caminho_origem):
            shutil.move(caminho_origem, caminho_destino)
            print(f"🚚 Movido: {arquivo}  ➡️  {pasta_destino}/{arquivo}")

    # 4. Mover arquivos .txt soltos na raiz para a pasta logs/docs (opcional)
    for item in os.listdir(raiz):
        caminho_item = os.path.join(raiz, item)
        if os.path.isfile(caminho_item) and item.endswith('.txt'):
            destino_txt = os.path.join(raiz, "logs", item)
            shutil.move(caminho_item, destino_txt)
            print(f"📄 Movido texto: {item}  ➡️  logs/{item}")

    # 5. Mover a pasta 'pages' para dentro de 'frontend' caso esteja solta na raiz
    pasta_pages_raiz = os.path.join(raiz, "pages")
    pasta_pages_destino = os.path.join(raiz, "frontend", "pages")
    if os.path.exists(pasta_pages_raiz) and not os.path.exists(pasta_pages_destino):
        shutil.move(pasta_pages_raiz, pasta_pages_destino)
        print("📁 Movida pasta: pages/  ➡️  frontend/pages/")

    print("\n✅ Estrutura organizada com sucesso!")

if __name__ == "__main__":
    organizar_projeto()