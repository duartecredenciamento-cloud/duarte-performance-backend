from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

# =====================================================
# SCHEMAS DE USUÁRIO
# =====================================================

class UsuarioCreate(BaseModel):
    username: str
    senha: Optional[str] = "123456"
    nome: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = "Operador"


class UsuarioUpdate(BaseModel):
    username: Optional[str] = None
    senha: Optional[str] = None
    nome: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    ativo: Optional[bool] = None


class UsuarioOut(BaseModel):
    id: int
    username: str
    nome: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = "Operador"
    ativo: Optional[bool] = True
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# SCHEMAS DE REGISTRO / PERFORMANCE
# =====================================================

class RegistroCreate(BaseModel):
    cliente_nome: Optional[str] = None
    cliente: Optional[str] = None
    status: str
    justificativa: Optional[str] = ""
    operador_nome: Optional[str] = None
    data_registro: Optional[str] = None
    periodo: Optional[str] = "MANHA"


class RegistroUpdate(BaseModel):
    cliente_nome: Optional[str] = None
    status: Optional[str] = None
    justificativa: Optional[str] = None
    operador_nome: Optional[str] = None
    data_registro: Optional[str] = None
    periodo: Optional[str] = None


class RegistroOut(BaseModel):
    id: int
    operador_nome: str
    cliente_nome: str
    status: str
    justificativa: Optional[str] = None
    data_registro: datetime
    periodo: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# SCHEMAS DE ESCALA / CRONOGRAMA
# =====================================================

class EscalaCreate(BaseModel):
    operador: str
    periodo: str
    dia_semana: str
    cliente: str


class EscalaOut(BaseModel):
    id: int
    operador: str
    periodo: str
    dia_semana: str
    cliente: str

    model_config = ConfigDict(from_attributes=True)


# =====================================================
# SCHEMAS DE RECUPERAÇÃO / REDEFINIÇÃO DE SENHA
# =====================================================

class SolicitacaoSenhaCreate(BaseModel):
    username: str
    email: Optional[str] = None
    telefone: Optional[str] = None


class RedefinirSenhaAutorizada(BaseModel):
    username: str
    nova_senha: str