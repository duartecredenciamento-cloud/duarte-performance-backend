from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

# ===================== DEPARTAMENTOS =====================
class DepartamentoModel(Base):
    __tablename__ = "departamentos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(100), unique=True, nullable=False, index=True)
    usuarios = relationship("UserModel", back_populates="departamento", cascade="all, delete-orphan")

# ===================== USUÁRIOS =====================
class UserModel(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True, index=True)
    cpf = Column(String(11), unique=True, nullable=False, index=True)
    nome = Column(String(150), nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)  # Admin Master, Gestor, Operador
    departamento_id = Column(Integer, ForeignKey("departamentos.id", ondelete="SET NULL"), nullable=True)
    departamento = relationship("DepartamentoModel", back_populates="usuarios")

# ===================== CLIENTES =====================
class ClienteModel(Base):
    __tablename__ = "clientes"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String(150), unique=True, nullable=False, index=True)

# ===================== CRONOGRAMA =====================
class CronogramaModel(Base):
    __tablename__ = "cronogramas"
    id = Column(Integer, primary_key=True, index=True)
    operador = Column(String(100), nullable=False, index=True)
    dia_semana = Column(String(20), nullable=False)
    atividade = Column(String(255), nullable=False)
    cliente = Column(String(150), nullable=False, index=True)
    periodo = Column(String(50), nullable=True)
    data_limite = Column(String(20), nullable=True)
    status_prazo = Column(String(50), default="Pendente")

# ===================== REGISTROS =====================
class RegistroModel(Base):
    __tablename__ = "registros"
    id = Column(Integer, primary_key=True, index=True)
    data_registro = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    operador_nome = Column(String(100), nullable=False, index=True)
    cliente_nome = Column(String(150), nullable=False, index=True)
    status = Column(String(50), nullable=False)
    justificativa = Column(Text, nullable=True)
    caminho_evidencia = Column(String(255), nullable=True)
    aprovado_gestor = Column(String(20), default="Pendente")

# ===================== AUDITORIA =====================
class AuditoriaModel(Base):
    __tablename__ = "auditoria_logs"
    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    usuario_cpf = Column(String(11), nullable=True, index=True)
    usuario_nome = Column(String(150), nullable=True)
    ip_origem = Column(String(45), nullable=True)
    acao = Column(String(100), nullable=False)
    detalhes = Column(Text, nullable=True)