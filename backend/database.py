import os
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# Em produção (Render), a URL vem da variável de ambiente DATABASE_URL.
# Em desenvolvimento local, cai no seu Postgres da máquina.
SQLALCHEMY_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:Duarte1234#@localhost:5432/duarte_performance"
)

# O Render (e alguns provedores no estilo Heroku) às vezes entrega a URL
# começando com "postgres://", que o SQLAlchemy moderno não aceita mais.
# Isso corrige sem quebrar o funcionamento local.
if SQLALCHEMY_DATABASE_URL.startswith("postgres://"):
    SQLALCHEMY_DATABASE_URL = SQLALCHEMY_DATABASE_URL.replace("postgres://", "postgresql://", 1)

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()