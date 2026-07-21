import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# -----------------------------------------------------------------------------
# Configuração da URL de Conexão com o Banco de Dados
# -----------------------------------------------------------------------------
# Busca a variável DATABASE_URL definida no Render.
# Se estiver rodando localmente sem variável, cai no fallback do SQLite.
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./duarte_performance.db")

# AJUSTE CRÍTICO PARA O RENDER:
# O Render fornece conexões PostgreSQL no formato antigo 'postgres://',
# porém o SQLAlchemy moderno exige estritamente o formato 'postgresql://'.
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# -----------------------------------------------------------------------------
# Inicialização do Engine do SQLAlchemy
# -----------------------------------------------------------------------------
connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args=connect_args
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# -----------------------------------------------------------------------------
# Injeção de Dependência da Sessão (Usado no main.py)
# -----------------------------------------------------------------------------
def get_db():
    """
    Gera uma sessão do banco para cada requisição da API e fecha ao finalizar.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()