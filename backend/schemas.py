from pydantic import BaseModel, ConfigDict, field_validator
from datetime import datetime
from typing import Optional, List


def _sanitizar_username(v: str) -> str:
    v = (v or "").strip().lower().replace(" ", "_")
    v = "".join(c for c in v if c.isalnum() or c == "_")
    return v


def _validar_email_simples(v: Optional[str]) -> Optional[str]:
    """Validação leve (sem depender do pacote email-validator): só confere
    que tem um '@' com algo antes e um '.' depois, sem julgar mais que isso."""
    if not v:
        return v
    v = v.strip()
    if "@" not in v or "." not in v.split("@")[-1]:
        raise ValueError("E-mail em formato inválido.")
    return v


# =====================================================
# ESQUEMAS DE USUÁRIO
# =====================================================
class UserSignupPublic(BaseModel):
    """Cadastro público (a própria pessoa cria a conta)."""
    username: str
    password: str
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None

    @field_validator("username")
    @classmethod
    def sanitizar_username(cls, v):
        v_limpo = _sanitizar_username(v)
        if len(v_limpo) < 3:
            raise ValueError("O usuário precisa ter ao menos 3 caracteres (letras, números ou _).")
        return v_limpo

    @field_validator("email")
    @classmethod
    def validar_email(cls, v):
        return _validar_email_simples(v)


class UserAdminCreate(BaseModel):
    """Criação pelo Admin Master. Nome/e-mail/telefone são opcionais aqui —
    se ficarem em branco, a pessoa completa no primeiro login dela."""
    username: str
    password: str
    role: str
    departamento_id: Optional[int] = None
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None

    @field_validator("username")
    @classmethod
    def sanitizar_username(cls, v):
        v_limpo = _sanitizar_username(v)
        if len(v_limpo) < 3:
            raise ValueError("O usuário precisa ter ao menos 3 caracteres (letras, números ou _).")
        return v_limpo

    @field_validator("email")
    @classmethod
    def validar_email(cls, v):
        return _validar_email_simples(v)


class UserProfileComplete(BaseModel):
    """Usado na tela de 'Complete seu Perfil' no primeiro acesso."""
    nome: str
    email: Optional[str] = None
    telefone: Optional[str] = None

    @field_validator("email")
    @classmethod
    def validar_email(cls, v):
        return _validar_email_simples(v)


class UserOut(BaseModel):
    id: int
    username: str
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    role: str
    departamento_id: Optional[int] = None
    perfil_completo: bool
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
    usuario_login: Optional[str] = None
    usuario_nome: Optional[str] = None
    ip_origem: Optional[str] = None
    acao: str
    detalhes: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)