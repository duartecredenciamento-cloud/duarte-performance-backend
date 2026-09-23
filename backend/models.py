"""
Modelos SQLAlchemy — Duarte Performance.

Atenção: não adicionar colunas a tabelas existentes apenas neste
arquivo. Alterações de estrutura do PostgreSQL exigem migração.
"""

import datetime

from sqlalchemy import Column, DateTime, Integer, String, Text

from database import Base


class Usuario(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(
        String(120),
        unique=True,
        nullable=False,
        index=True,
    )
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), default="Operador")
    nome = Column(String(120), nullable=True)
    email = Column(String(120), nullable=True)


class RegistroModel(Base):
    __tablename__ = "registros"

    id = Column(Integer, primary_key=True, index=True)
    operador_nome = Column(String(120), nullable=True)
    cliente_nome = Column(String(120), nullable=True)
    status = Column(String(120), nullable=True)
    justificativa = Column(Text, nullable=True)
    periodo = Column(String(50), nullable=True)
    data_registro = Column(
        DateTime,
        default=datetime.datetime.utcnow,
    )


class CronogramaModel(Base):
    __tablename__ = "cronograma"

    id = Column(Integer, primary_key=True, index=True)
    operador = Column(String(120), nullable=True)
    periodo = Column(String(50), nullable=True)
    segunda = Column(String(120), nullable=True)
    terca = Column(String(120), nullable=True)
    quarta = Column(String(120), nullable=True)
    quinta = Column(String(120), nullable=True)
    sexta = Column(String(120), nullable=True)


class SolicitacaoSenhaModel(Base):
    __tablename__ = "solicitacoes_senha"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(120), nullable=True)
    email = Column(String(120), nullable=True)
    telefone = Column(String(50), nullable=True)
    status = Column(String(50), default="pendente")
    solicitado_em = Column(
        DateTime,
        default=datetime.datetime.utcnow,
    )


class LogAtividade(Base):
    __tablename__ = "logs"

    id = Column(Integer, primary_key=True, index=True)
    usuario = Column(String(120), nullable=False)
    acao = Column(String(255), nullable=False)
    detalhes = Column(Text, nullable=True)
    data_hora = Column(
        DateTime,
        default=datetime.datetime.utcnow,
    )