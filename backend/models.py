"""
Definições dos Modelos SQLAlchemy do Banco de Dados.
"""
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from database import Base
import datetime

class Usuario(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(120), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="Operador")
    nome = Column(String(120), nullable=True)
    email = Column(String(120), nullable=True)

class LogAtividade(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(120), nullable=False)
    acao = Column(String(255), nullable=False)
    detalhes = Column(Text, nullable=True)
    data_hora = Column(DateTime, default=datetime.datetime.utcnow)