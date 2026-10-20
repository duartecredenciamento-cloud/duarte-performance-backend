import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Lê a URL do PostgreSQL das variáveis do Railway; se não achar, usa SQLite local
SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
if not SQLALCHEMY_DATABASE_URL:
    if os.getenv("APP_ENV", "development").lower() == "production":
        raise RuntimeError("DATABASE_URL persistente é obrigatória em produção.")
    local_db = Path(os.getenv("LOCAL_DB_PATH", "./data/duarte_performance_dev.sqlite3")).resolve()
    local_db.parent.mkdir(parents=True, exist_ok=True)
    SQLALCHEMY_DATABASE_URL = "sqlite:///" + local_db.as_posix()

# Correção de protocolo para compatibilidade com SQLAlchemy 2.0+
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

# Configurações de engine para PostgreSQL / SQLite
if "sqlite" in SQLALCHEMY_DATABASE_URL:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
else:
    engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_pre_ping=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()