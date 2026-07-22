from sqlalchemy import Column, Integer, String, Boolean, DateTime
from datetime import datetime
from backend.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    nome = Column(String, nullable=True)
    email = Column(String, nullable=True)
    telefone = Column(String, nullable=True)
    role = Column(String, default="operador")
    perfil_completo = Column(Boolean, default=False)
    criado_em = Column(DateTime, default=datetime.utcnow)