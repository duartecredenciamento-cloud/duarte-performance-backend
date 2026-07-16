from database import engine

try:
    connection = engine.connect()
    print("Sucesso! Conexão com o banco 'duarte_performance' estabelecida.")
    connection.close()
except Exception as e:
    print(f"Erro ao conectar: {e}")