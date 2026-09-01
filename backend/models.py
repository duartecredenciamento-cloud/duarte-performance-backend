from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Index
from sqlalchemy.sql import func
from database import Base

class Usuario(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(120), unique=True, index=True, nullable=False)
    email = Column(String(120), nullable=True)
    nome = Column(String(150), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="Operador", nullable=False)
    perfil_completo = Column(Boolean, default=True)
    telefone = Column(String(30), nullable=True)
    criado_em = Column(DateTime(timezone=True), server_default=func.now())

class RegistroModel(Base):
    __tablename__ = "registros"

    id = Column(Integer, primary_key=True, index=True)
    operador_nome = Column(String(150), index=True, nullable=False)
    cliente_nome = Column(String(150), index=True, nullable=False)
    status = Column(String(50), index=True, nullable=False)
    justificativa = Column(Text, nullable=True)
    data_registro = Column(DateTime, default=func.now(), index=True, nullable=False)

    __table_args__ = (
        Index("idx_operador_data", "operador_nome", "data_registro"),
    )

class CronogramaModel(Base):
    __tablename__ = "cronograma"

    id = Column(Integer, primary_key=True, index=True)
    operador = Column(String(150), index=True, nullable=False)
    periodo = Column(String(50), default="MANHÃ", nullable=False)
    segunda = Column(String(150), default="-")
    terca = Column(String(150), default="-")
    quarta = Column(String(150), default="-")
    quinta = Column(String(150), default="-")
    sexta = Column(String(150), default="-")

class SolicitacaoSenhaModel(Base):
    __tablename__ = "solicitacoes_senha"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(120), index=True, nullable=False)
    email = Column(String(120), nullable=True)
    telefone = Column(String(30), nullable=True)
    status = Column(String(30), default="pendente", index=True) # pendente, autorizado, rejeitado, usado, expirado
    solicitado_em = Column(DateTime, default=func.now())
    autorizado_em = Column(DateTime, nullable=True)
    expira_em = Column(DateTime, nullable=True)
    usado_em = Column(DateTime, nullable=True)
    autorizado_por = Column(String(120), nullable=True)