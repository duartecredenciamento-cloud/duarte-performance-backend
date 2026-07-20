from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List

# =====================================================
# ESQUEMAS DE USUÁRIO (Autenticação Segura)
# =====================================================
class UserBase(BaseModel):
    cpf: str
    nome: str
    role: str
    departamento_id: Optional[int] = None

    @field_validator("cpf")
    @classmethod
    def validar_e_sanitizar_cpf(cls, v: str) -> str:
        v_clean = "".join(filter(str.isdigit, v))
        if len(v_clean) != 11:
            raise ValueError("O CPF deve conter exatamente 11 dígitos numéricos.")
        return v_clean

class UserCreate(UserBase):
    password: str

class UserOut(UserBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# =====================================================
# ESQUEMAS DO CRONOGRAMA (Escala Semanal e SLA)
# =====================================================
class CronogramaBase(BaseModel):
    operador: str
    dia_semana: str
    atividade: str
    cliente: str
    periodo: Optional[str] = None
    data_limite: Optional[str] = None
    status_prazo: Optional[str] = "Pendente"

class CronogramaCreate(CronogramaBase):
    pass

class CronogramaUpdate(BaseModel):
    """Todos os campos são opcionais — usado tanto para corrigir um campo
    quanto para 'mover' o item (trocando operador e/ou dia_semana)."""
    operador: Optional[str] = None
    dia_semana: Optional[str] = None
    atividade: Optional[str] = None
    cliente: Optional[str] = None
    periodo: Optional[str] = None
    data_limite: Optional[str] = None
    status_prazo: Optional[str] = None

class CronogramaOut(CronogramaBase):
    id: int
    model_config = ConfigDict(from_attributes=True)


# =====================================================
# ESQUEMAS DOS REGISTROS OPERACIONAIS (Entregas Diárias)
# =====================================================
class RegistroBase(BaseModel):
    operador_nome: str
    cliente_nome: str
    status: str
    justificativa: Optional[str] = None

class RegistroCreate(RegistroBase):
    pass

class RegistroUpdate(BaseModel):
    """Usado pelo Editor de Apontamentos para corrigir um lançamento enviado errado."""
    cliente_nome: Optional[str] = None
    status: Optional[str] = None
    justificativa: Optional[str] = None

class RegistroOut(RegistroBase):
    id: int
    data_registro: datetime
    caminho_evidencia: Optional[str] = None
    aprovado_gestor: Optional[str] = "Pendente"
    model_config = ConfigDict(from_attributes=True)


# =====================================================
# ESQUEMA DE AUDITORIA (Compliance & LGPD)
# =====================================================
class AuditoriaOut(BaseModel):
    id: int
    timestamp: datetime
    usuario_cpf: Optional[str] = None
    usuario_nome: Optional[str] = None
    ip_origem: Optional[str] = None
    acao: str
    detalhes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)