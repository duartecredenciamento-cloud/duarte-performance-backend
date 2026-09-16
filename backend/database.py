"""
Configuração da Conexão com o Banco de Dados (PostgreSQL Railway / SQLite Local).
"""
import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Tenta obter a URL do banco do Railway (Postgres)
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL")

# Se não encontrar a variável do Railway, utiliza o SQLite localmente
if not SQLALCHEMY_DATABASE_URL:
    SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"

# Correção para compatibilidade de protocolo no SQLAlchemy (postgres:// -> postgresql://)
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Ajuste de argumentos de conexão conforme o banco de dados
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    engine = create_engine(
        SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
    )
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    """Injeta a sessão do banco de dados nas rotas do FastAPI e garante o fechamento."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()