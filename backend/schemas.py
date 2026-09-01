from pydantic import BaseModel, Field, ConfigDict
from datetime import datetime
from typing import Optional

class UsuarioCreate(BaseModel):
    username: str
    nome: str
    senha: str
    email: Optional[str] = None
    role: Optional[str] = "Operador"

class RegistroCreate(BaseModel):
    cliente_nome: Optional[str] = None
    cliente: Optional[str] = None
    status: str
    justificativa: Optional[str] = ""
    operador_nome: Optional[str] = None
    data_registro: Optional[str] = None

class RegistroUpdate(BaseModel):
    cliente_nome: Optional[str] = None
    status: Optional[str] = None
    justificativa: Optional[str] = None
    operador_nome: Optional[str] = None
    data_registro: Optional[str] = None

class RegistroOut(BaseModel):
    id: int
    operador_nome: str
    cliente_nome: str
    status: str
    justificativa: Optional[str] = None
    data_registro: datetime

    model_config = ConfigDict(from_attributes=True)

class SolicitacaoSenhaCreate(BaseModel):
    username: str
    email: Optional[str] = None
    telefone: Optional[str] = None

class RedefinirSenhaAutorizada(BaseModel):
    username: str
    nova_senha: str