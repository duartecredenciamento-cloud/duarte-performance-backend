import os

# Configurações do Banco de Dados
DB_NAME = "duarte_gestao.db"
DB_PATH = os.path.join(os.path.dirname(__file__), DB_NAME)
DB_TIMEOUT = 20

# Configurações de Segurança (JWT)
SECRET_KEY = "super-duarte-secret-key-2026"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30