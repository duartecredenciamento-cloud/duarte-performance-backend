from sqlalchemy import Column, Integer, String, Boolean
from database import Base

class Usuario(Base):
    __tablename__ = "usuarios"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String, nullable=False)  # <-- Corrigido para bater com o pgAdmin
    nome = Column(String(150), nullable=True)
    email = Column(String(150), nullable=True)
    telefone = Column(String(20), nullable=True)
    perfil_completo = Column(Boolean, default=False)
    role = Column(String(50), default="operador")
    departamento_id = Column(Integer, nullable=True)