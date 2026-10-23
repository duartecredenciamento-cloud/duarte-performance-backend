"""
Aplicação principal FastAPI — Duarte Performance.

Autenticação JWT, usuários, registros operacionais, cronograma
e provisionamento administrativo controlado por variáveis de ambiente.
"""

import datetime
import logging
import os
from datetime import timedelta
from typing import List, Optional

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.middleware.base import BaseHTTPMiddleware
from pathlib import Path
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
from database import SessionLocal, engine, get_db


# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

SECRET_KEY = os.getenv("SECRET_KEY", "").strip()

if len(SECRET_KEY) < 32:
    raise RuntimeError(
        "Configure SECRET_KEY no serviço backend com uma chave "
        "aleatória de pelo menos 32 caracteres antes de iniciar a API."
    )

pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# Criação de schema é explícita apenas em desenvolvimento, nunca no deploy.
if os.getenv("ALLOW_SCHEMA_CREATE", "").strip().lower() in {"1", "true", "yes"}:
    if os.getenv("APP_ENV", "development").lower() == "production":
        raise RuntimeError("ALLOW_SCHEMA_CREATE não pode ser usado em produção.")
    models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Duarte Performance 2.0",
    version="2.0.0",
)

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com data:; img-src 'self' data:; connect-src 'self'; "
            "object-src 'none'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'"
        )
        return response


app.add_middleware(SecurityHeadersMiddleware)

_cors_origins = [x.strip() for x in os.getenv("CORS_ORIGINS", "").split(",") if x.strip()]
if _cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=_cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type"],
    )


# ==============================================================================
# SCHEMAS PYDANTIC
# ==============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str
    role: Optional[str] = None
    username: Optional[str] = None


class UsuarioBase(BaseModel):
    username: str
    nome: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = "operador"


class UsuarioCreate(UsuarioBase):
    password: str


class UsuarioRoleUpdate(BaseModel):
    role: str


class UsuarioResponse(UsuarioBase):
    id: int

    # Valor de resposta para compatibilidade com o frontend.
    # Não é uma coluna do models.Usuario atual.
    ativo: Optional[bool] = True

    class Config:
        from_attributes = True


class RegistroBase(BaseModel):
    operador_nome: Optional[str] = None
    cliente_nome: Optional[str] = None
    status: Optional[str] = None
    justificativa: Optional[str] = ""
    periodo: Optional[str] = None
    data_registro: Optional[datetime.datetime] = None


class RegistroUpdate(BaseModel):
    cliente_nome: Optional[str] = None
    status: Optional[str] = None
    justificativa: Optional[str] = None
    data_registro: Optional[datetime.datetime] = None
    periodo: Optional[str] = None


class RegistroCreate(RegistroBase):
    pass


class RegistroResponse(BaseModel):
    id: int
    operador_nome: Optional[str] = None
    cliente_nome: Optional[str] = None
    status: Optional[str] = None
    justificativa: Optional[str] = ""
    periodo: Optional[str] = None
    data_registro: Optional[datetime.datetime] = None

    class Config:
        from_attributes = True


class CronogramaBase(BaseModel):
    operador: Optional[str] = None
    periodo: Optional[str] = "MANHÃ"
    segunda: Optional[str] = "-"
    terca: Optional[str] = "-"
    quarta: Optional[str] = "-"
    quinta: Optional[str] = "-"
    sexta: Optional[str] = "-"


class CronogramaCreate(CronogramaBase):
    pass


class CronogramaResponse(CronogramaBase):
    id: int

    class Config:
        from_attributes = True


class SolicitacaoSenhaCreate(BaseModel):
    username: str
    email: Optional[str] = None
    telefone: Optional[str] = None


class SolicitacaoSenhaResponse(BaseModel):
    id: int
    username: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    status: Optional[str] = "pendente"
    solicitado_em: Optional[datetime.datetime] = None
    autorizado_em: Optional[datetime.datetime] = None
    expira_em: Optional[datetime.datetime] = None
    autorizado_por: Optional[str] = None

    class Config:
        from_attributes = True


class SenhaUpdate(BaseModel):
    username: str
    nova_senha: str
    confirmar_senha: str


class SenhaAdminReset(BaseModel):
    nova_senha: str


# ==============================================================================
# SENHAS E JWT
# ==============================================================================

def verificar_senha(
    plain_password: str,
    hashed_password: str,
) -> bool:
    if not plain_password or not hashed_password:
        return False

    try:
        return pwd_context.verify(
            plain_password,
            hashed_password,
        )
    except (TypeError, ValueError):
        logger.warning(
            "Foi encontrado um hash de senha inválido "
            "durante uma tentativa de login."
        )
        return False


def gerar_hash_senha(password: str) -> str:
    if not password:
        raise ValueError("Senha obrigatória.")

    return pwd_context.hash(password)


def criar_access_token(
    data: dict,
    expires_delta: Optional[timedelta] = None,
) -> str:
    to_encode = data.copy()

    expire = datetime.datetime.now(
        datetime.timezone.utc
    ) + (
        expires_delta
        or timedelta(minutes=15)
    )

    to_encode.update({"exp": expire})

    return jwt.encode(
        to_encode,
        SECRET_KEY,
        algorithm=ALGORITHM,
    )


def obter_usuario_atual(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[ALGORITHM],
        )

        username = payload.get("sub")

        if not isinstance(username, str) or not username.strip():
            raise credentials_exception

    except JWTError:
        raise credentials_exception

    usuario = (
        db.query(models.Usuario)
        .filter(
            func.lower(models.Usuario.username)
            == username.strip().lower()
        )
        .first()
    )

    if usuario is None:
        raise credentials_exception

    return usuario


def exigir_administrador(usuario: models.Usuario) -> None:
    """Permite ações administrativas somente ao administrador atual."""
    role = (usuario.role or "").strip().casefold().replace("_", " ")
    if role not in {"admin", "admin master"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem realizar esta ação.",
        )


def _role_normalizada(usuario: models.Usuario) -> str:
    return (usuario.role or "operador").strip().casefold().replace("_", " ")


def _pode_gerir_operacao(usuario: models.Usuario) -> bool:
    return _role_normalizada(usuario) in {
        "admin", "admin master", "gestor", "coordenador"
    }


def registrar_log(
    db: Session,
    usuario: str,
    acao: str,
    detalhes: Optional[str] = None,
):
    try:
        log = models.LogAtividade(
            usuario=usuario,
            acao=acao,
            detalhes=detalhes,
            data_hora=datetime.datetime.utcnow(),
        )

        db.add(log)
        db.commit()

    except Exception:
        db.rollback()
        logger.exception(
            "Falha ao registrar ação de auditoria."
        )


# ==============================================================================
# PROVISIONAMENTO ADMINISTRATIVO
# ==============================================================================

def _variavel_verdadeira(nome: str) -> bool:
    return os.getenv(nome, "").strip().lower() in {
        "1",
        "true",
        "yes",
        "sim",
    }


def _provisionar_admin_ambiente() -> None:
    """
    Provisiona uma conta administrativa no início do backend.

    Variáveis:
        ADMIN_BOOTSTRAP_USERNAME
        ADMIN_BOOTSTRAP_PASSWORD
        ADMIN_BOOTSTRAP_RESET_EXISTING

    Se a conta já existir, a senha só é redefinida quando
    ADMIN_BOOTSTRAP_RESET_EXISTING=true.
    """
    username = os.getenv(
        "ADMIN_BOOTSTRAP_USERNAME",
        "",
    ).strip()

    password = os.getenv(
        "ADMIN_BOOTSTRAP_PASSWORD",
        "",
    )

    if not username and not password:
        return

    if not username or not password:
        raise RuntimeError(
            "Configure ADMIN_BOOTSTRAP_USERNAME e "
            "ADMIN_BOOTSTRAP_PASSWORD em conjunto."
        )

    if len(password) < 12:
        raise RuntimeError(
            "ADMIN_BOOTSTRAP_PASSWORD precisa ter "
            "pelo menos 12 caracteres."
        )

    if len(password.encode("utf-8")) > 72:
        raise RuntimeError(
            "ADMIN_BOOTSTRAP_PASSWORD deve ter no máximo "
            "72 bytes em UTF-8."
        )

    reset_existing = _variavel_verdadeira(
        "ADMIN_BOOTSTRAP_RESET_EXISTING"
    )

    db = SessionLocal()

    try:
        usuario = (
            db.query(models.Usuario)
            .filter(
                func.lower(models.Usuario.username)
                == username.lower()
            )
            .first()
        )

        if usuario is None:
            usuario = models.Usuario(
                username=username,
                password_hash=gerar_hash_senha(password),
                nome=(
                    "Abraão"
                    if username.lower() == "abraao"
                    else username
                ),
                role="admin",
            )

            db.add(usuario)
            db.commit()

            logger.warning(
                "Conta administrativa %s criada "
                "por provisionamento de ambiente.",
                username,
            )
            return

        if not reset_existing:
            logger.warning(
                "A conta %s já existe. Nenhuma senha foi "
                "alterada. Para redefini-la, configure "
                "ADMIN_BOOTSTRAP_RESET_EXISTING=true.",
                username,
            )
            return

        usuario.password_hash = gerar_hash_senha(password)
        usuario.role = "admin"

        db.commit()

        logger.warning(
            "Conta administrativa %s redefinida "
            "por provisionamento de ambiente.",
            username,
        )

    except Exception:
        db.rollback()
        logger.exception(
            "Falha no provisionamento da conta administrativa."
        )
        raise

    finally:
        db.close()


@app.on_event("startup")
def inicializar_aplicacao():
    _provisionar_admin_ambiente()
    if os.getenv("APP_ENV", "development").lower() == "production":
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")


# ==============================================================================
# AUTENTICAÇÃO E USUÁRIOS
# ==============================================================================

@app.post(
    "/token",
    response_model=Token,
)
def login_para_obter_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    username = form_data.username.strip()

    usuario = (
        db.query(models.Usuario)
        .filter(
            func.lower(models.Usuario.username)
            == username.lower()
        )
        .first()
    )

    if (
        usuario is None
        or not verificar_senha(
            form_data.password,
            usuario.password_hash,
        )
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_role = (
        (usuario.role or "operador")
        .strip()
        .lower()
    )

    access_token = criar_access_token(
        data={
            "sub": usuario.username,
            "role": user_role,
        },
        expires_delta=timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        ),
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "role": user_role,
        "username": usuario.username,
        "nome": usuario.nome or usuario.username,
    }


@app.get(
    "/usuarios/",
    response_model=List[UsuarioResponse],
)
def listar_todos_usuarios(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    exigir_administrador(current_user)
    try:
        return db.query(models.Usuario).all()

    except Exception:
        logger.exception(
            "Erro ao listar usuários."
        )
        return []


@app.get(
    "/usuarios/me",
    response_model=UsuarioResponse,
)
def ler_usuario_logado(
    current_user: models.Usuario = Depends(
        obter_usuario_atual
    ),
):
    return current_user


@app.post(
    "/usuarios/",
    response_model=UsuarioResponse,
    status_code=status.HTTP_201_CREATED,
)
def cadastrar_usuario(
    usuario: UsuarioCreate,
    db: Session = Depends(get_db),
):
    username = usuario.username.strip()

    if not username:
        raise HTTPException(
            status_code=400,
            detail="Informe o nome de usuário.",
        )

    existente = (
        db.query(models.Usuario)
        .filter(
            func.lower(models.Usuario.username)
            == username.lower()
        )
        .first()
    )

    if existente:
        raise HTTPException(
            status_code=400,
            detail="Nome de usuário já cadastrado.",
        )

    if not usuario.password:
        raise HTTPException(
            status_code=400,
            detail="Informe uma senha.",
        )

    # Rota pública: não aceita role=admin enviada pelo cliente.
    if len(usuario.password) < 10 or len(usuario.password.encode("utf-8")) > 72:
        raise HTTPException(status_code=422, detail="A senha deve ter de 10 a 72 bytes.")
    novo_usuario = models.Usuario(
        username=username,
        password_hash=gerar_hash_senha(usuario.password),
        nome=usuario.nome,
        email=usuario.email,
        role="operador",
    )

    try:
        db.add(novo_usuario)
        db.commit()
        db.refresh(novo_usuario)

    except Exception:
        db.rollback()
        logger.exception(
            "Erro ao cadastrar usuário."
        )
        raise HTTPException(
            status_code=500,
            detail="Erro ao cadastrar usuário.",
        )

    return novo_usuario


@app.put(
    "/usuarios/{usuario_id}/role",
    response_model=UsuarioResponse,
)
def atualizar_funcao_usuario(
    usuario_id: int,
    atualizacao: UsuarioRoleUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    """Altera a função de uma conta; exige administrador autenticado."""
    exigir_administrador(current_user)

    roles_permitidas = {
        "operador": "operador",
        "visualizador": "visualizador",
        "gestor": "gestor",
        "admin": "admin",
    }
    role_solicitada = atualizacao.role.strip().casefold()
    nova_role = roles_permitidas.get(role_solicitada)

    if nova_role is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Função inválida. Escolha Operador, Visualizador, "
                "Gestor ou Admin."
            ),
        )

    usuario = db.query(models.Usuario).filter(
        models.Usuario.id == usuario_id
    ).first()
    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    role_atual = (usuario.role or "operador").strip().casefold()
    if usuario.id == current_user.id and nova_role != "admin":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Não é permitido remover sua própria função de administrador.",
        )

    if role_atual in {"admin", "admin master"} and nova_role != "admin":
        total_admins = db.query(models.Usuario).filter(
            func.lower(func.trim(models.Usuario.role)).in_(
                ["admin", "admin master"]
            )
        ).count()
        if total_admins <= 1:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Não é possível remover o último administrador.",
            )

    usuario.role = nova_role
    try:
        db.commit()
        db.refresh(usuario)
    except Exception:
        db.rollback()
        logger.exception("Erro ao atualizar função do usuário.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Erro ao atualizar a função do usuário.",
        )

    registrar_log(
        db,
        usuario=current_user.username,
        acao="Alterou função de usuário",
        detalhes=f"Usuário ID {usuario.id}: {role_atual} -> {nova_role}",
    )
    return usuario


# ==============================================================================
# ENDPOINTS ANTIGOS DE SETUP: DESATIVADOS
# ==============================================================================

@app.get("/setup-admin")
def setup_admin_manual():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "Endpoint de redefinição pública desativado. "
            "Utilize o provisionamento administrativo "
            "por variáveis de ambiente."
        ),
    )


@app.get("/setup-abraao")
def setup_abraao_manual():
    raise HTTPException(
        status_code=status.HTTP_410_GONE,
        detail=(
            "Endpoint de redefinição pública desativado. "
            "Utilize o provisionamento administrativo "
            "por variáveis de ambiente."
        ),
    )


# ==============================================================================
# REGISTROS
# ==============================================================================

@app.post(
    "/registros/",
    response_model=RegistroResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_registro(
    registro: RegistroCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    try:
        permitidos = {"Realizado Total", "Realizado Parcial", "Não Realizado", "Não Se Aplica"}
        if _pode_gerir_operacao(current_user):
            permitidos.add("Não Informado")
        if registro.status not in permitidos:
            raise HTTPException(status_code=422, detail="Status de execução inválido para este perfil.")
        if registro.status in {"Realizado Parcial", "Não Realizado", "Não Se Aplica", "Não Informado"} and not (registro.justificativa or "").strip():
            raise HTTPException(status_code=422, detail="Justificativa obrigatória para o status informado.")
        nome_autenticado = (current_user.nome or current_user.username).strip()
        if not _pode_gerir_operacao(current_user) and registro.operador_nome and registro.operador_nome.strip().casefold() not in {nome_autenticado.casefold(), current_user.username.casefold()}:
            raise HTTPException(status_code=403, detail="Não é permitido lançar em nome de outro operador.")
        dados = registro.model_dump(
            exclude_unset=True
        )

        db_registro = models.RegistroModel(
            operador_nome=(
                (dados.get("operador_nome") or nome_autenticado).strip()
                if _pode_gerir_operacao(current_user)
                else nome_autenticado
            ),
            cliente_nome=(dados.get("cliente_nome") or "Atendimento Geral").strip(),
            status=dados["status"],
            justificativa=(dados.get("justificativa") or "").strip(),
            periodo=(dados.get("periodo") or "Geral").strip(),
            data_registro=dados.get("data_registro") or datetime.datetime.utcnow(),
        )

        db.add(db_registro)
        db.commit()
        db.refresh(db_registro)

        registrar_log(
            db,
            usuario=db_registro.operador_nome,
            acao="Criou Registro",
            detalhes=(
                f"Cliente: {db_registro.cliente_nome}"
            ),
        )

        return db_registro

    except HTTPException:
        db.rollback()
        raise
    except Exception:
        db.rollback()
        logger.exception("Erro ao salvar registro.")
        raise HTTPException(
            status_code=500,
            detail="Erro ao salvar registro.",
        )


@app.get(
    "/registros/",
    response_model=List[RegistroResponse],
)
def listar_registros(
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    try:
        query = db.query(models.RegistroModel)
        if not (_pode_gerir_operacao(current_user) or _role_normalizada(current_user) == "visualizador"):
            nome = (current_user.nome or current_user.username).strip()
            query = query.filter(func.lower(models.RegistroModel.operador_nome) == nome.casefold())
        return query.order_by(models.RegistroModel.data_registro.desc()).offset(max(skip, 0)).limit(min(max(limit, 1), 500)).all()

    except Exception:
        logger.exception(
            "Erro ao listar registros."
        )
        return []


# ==============================================================================
# CRONOGRAMA
# ==============================================================================

@app.get(
    "/cronograma/",
    response_model=List[CronogramaResponse],
)
def listar_cronograma(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    try:
        query = db.query(models.CronogramaModel)
        if not (_pode_gerir_operacao(current_user) or _role_normalizada(current_user) == "visualizador"):
            nome = (current_user.nome or current_user.username).strip()
            query = query.filter(func.lower(models.CronogramaModel.operador) == nome.casefold())
        return query.all()

    except Exception:
        logger.exception(
            "Erro ao listar cronograma."
        )
        return []


@app.put(
    "/registros/{registro_id}",
    response_model=RegistroResponse,
)
def atualizar_registro(
    registro_id: int,
    atualizacao: RegistroUpdate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    if not _pode_gerir_operacao(current_user):
        raise HTTPException(status_code=403, detail="Apenas gestão pode editar apontamentos.")
    registro = db.query(models.RegistroModel).filter(models.RegistroModel.id == registro_id).first()
    if registro is None:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")
    changes = atualizacao.model_dump(exclude_unset=True)
    status_novo = changes.get("status", registro.status)
    justificativa = changes.get("justificativa", registro.justificativa or "")
    if status_novo not in {"Realizado Total", "Realizado Parcial", "Não Realizado", "Não Se Aplica", "Não Informado"}:
        raise HTTPException(status_code=422, detail="Status de execução inválido.")
    if status_novo in {"Realizado Parcial", "Não Realizado", "Não Se Aplica", "Não Informado"} and not (justificativa or "").strip():
        raise HTTPException(status_code=422, detail="Justificativa obrigatória para o status informado.")
    for key, value in changes.items():
        setattr(registro, key, value)
    try:
        db.commit()
        db.refresh(registro)
    except Exception:
        db.rollback()
        logger.exception("Erro ao editar apontamento.")
        raise HTTPException(status_code=500, detail="Não foi possível atualizar o registro.")
    registrar_log(db, current_user.username, "Editou apontamento", f"Registro ID {registro_id}")
    return registro


@app.delete("/registros/{registro_id}")
def excluir_registro(
    registro_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    if not _pode_gerir_operacao(current_user):
        raise HTTPException(status_code=403, detail="Apenas gestão pode excluir apontamentos.")
    registro = db.query(models.RegistroModel).filter(models.RegistroModel.id == registro_id).first()
    if registro is None:
        raise HTTPException(status_code=404, detail="Registro não encontrado.")
    db.delete(registro)
    db.commit()
    registrar_log(db, current_user.username, "Excluiu apontamento", f"Registro ID {registro_id}")
    return {"ok": True}


@app.put("/cronograma/{cronograma_id}", response_model=CronogramaResponse)
def atualizar_cronograma(
    cronograma_id: int,
    atualizacao: CronogramaBase,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    if not _pode_gerir_operacao(current_user):
        raise HTTPException(status_code=403, detail="Apenas gestão pode alterar o cronograma.")
    item = db.query(models.CronogramaModel).filter(models.CronogramaModel.id == cronograma_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Linha da escala não encontrada.")
    for key, value in atualizacao.model_dump(exclude_unset=True).items():
        setattr(item, key, value)
    db.commit()
    db.refresh(item)
    registrar_log(db, current_user.username, "Atualizou cronograma", f"Linha ID {cronograma_id}")
    return item


@app.delete("/cronograma/{cronograma_id}")
def excluir_cronograma(
    cronograma_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    if not _pode_gerir_operacao(current_user):
        raise HTTPException(status_code=403, detail="Apenas gestão pode alterar o cronograma.")
    item = db.query(models.CronogramaModel).filter(models.CronogramaModel.id == cronograma_id).first()
    if item is None:
        raise HTTPException(status_code=404, detail="Linha da escala não encontrada.")
    db.delete(item)
    db.commit()
    registrar_log(db, current_user.username, "Excluiu cronograma", f"Linha ID {cronograma_id}")
    return {"ok": True}


@app.post(
    "/cronograma/",
    response_model=CronogramaResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_cronograma(
    cronograma: CronogramaCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    if not _pode_gerir_operacao(current_user):
        raise HTTPException(status_code=403, detail="Apenas gestão pode alterar o cronograma.")
    db_cronograma = models.CronogramaModel(
        **cronograma.model_dump(
            exclude_unset=True
        )
    )

    db.add(db_cronograma)
    db.commit()
    db.refresh(db_cronograma)

    return db_cronograma


# ==============================================================================
# RECUPERAÇÃO DE SENHA E ADMIN
# ==============================================================================

@app.post(
    "/recuperar-senha/",
    response_model=SolicitacaoSenhaResponse,
    status_code=status.HTTP_201_CREATED,
)
def solicitar_recuperacao_senha(
    solicitacao: SolicitacaoSenhaCreate,
    db: Session = Depends(get_db),
):
    username = solicitacao.username.strip()
    usuario = db.query(models.Usuario).filter(func.lower(models.Usuario.username) == username.casefold()).first()
    if usuario and solicitacao.email and usuario.email and usuario.email.casefold() == solicitacao.email.strip().casefold():
        db_solicitacao = models.SolicitacaoSenhaModel(
            username=usuario.username,
            email=usuario.email,
            telefone=solicitacao.telefone,
            status="pendente",
        )
        db.add(db_solicitacao)
        db.commit()
        registrar_log(db, usuario=usuario.username, acao="Solicitação de senha", detalhes="Solicitação recebida para análise administrativa.")
    # Resposta indistinguível para evitar enumeração de contas.
    return {"id": 0, "username": username, "email": None, "telefone": None, "status": "pendente", "solicitado_em": datetime.datetime.utcnow(), "message": "Se os dados coincidirem, a solicitação será encaminhada para análise."}


@app.post("/admin/solicitacoes-senha/{solicitacao_id}/autorizar")
def autorizar_recuperacao(
    solicitacao_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    exigir_administrador(current_user)
    item = db.query(models.SolicitacaoSenhaModel).filter(models.SolicitacaoSenhaModel.id == solicitacao_id).first()
    if item is None or item.status != "pendente":
        raise HTTPException(status_code=404, detail="Solicitação pendente não encontrada.")
    agora = datetime.datetime.utcnow()
    item.status = "autorizado"
    item.autorizado_em = agora
    item.expira_em = agora + timedelta(minutes=10)
    item.autorizado_por = current_user.username
    db.commit()
    registrar_log(db, current_user.username, "Autorizou recuperação de senha", f"Solicitação ID {solicitacao_id}")
    return {"ok": True, "expira_em": item.expira_em}


@app.post("/admin/solicitacoes-senha/{solicitacao_id}/rejeitar")
def rejeitar_recuperacao(
    solicitacao_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    exigir_administrador(current_user)
    item = db.query(models.SolicitacaoSenhaModel).filter(models.SolicitacaoSenhaModel.id == solicitacao_id).first()
    if item is None or item.status != "pendente":
        raise HTTPException(status_code=404, detail="Solicitação pendente não encontrada.")
    item.status = "rejeitado"
    item.autorizado_por = current_user.username
    db.commit()
    registrar_log(db, current_user.username, "Rejeitou recuperação de senha", f"Solicitação ID {solicitacao_id}")
    return {"ok": True}


@app.post("/redefinir-senha-autorizada/")
def redefinir_senha_autorizada(
    dados: SenhaUpdate,
    db: Session = Depends(get_db),
):
    username = dados.username.strip()
    if dados.nova_senha != dados.confirmar_senha or len(dados.nova_senha) < 10 or len(dados.nova_senha.encode("utf-8")) > 72:
        raise HTTPException(status_code=422, detail="Confirmação inválida ou senha fora do limite permitido.")
    item = db.query(models.SolicitacaoSenhaModel).filter(
        func.lower(models.SolicitacaoSenhaModel.username) == username.casefold(),
        models.SolicitacaoSenhaModel.status == "autorizado",
        models.SolicitacaoSenhaModel.expira_em >= datetime.datetime.utcnow(),
    ).order_by(models.SolicitacaoSenhaModel.id.desc()).first()
    if item is None:
        raise HTTPException(status_code=403, detail="Não há autorização válida para redefinir a senha.")
    usuario = db.query(models.Usuario).filter(func.lower(models.Usuario.username) == username.casefold()).first()
    if usuario is None:
        raise HTTPException(status_code=404, detail="Conta não encontrada.")
    usuario.password_hash = gerar_hash_senha(dados.nova_senha)
    item.status = "usado"
    db.commit()
    registrar_log(db, usuario.username, "Redefiniu senha autorizada", f"Solicitação ID {item.id}")
    return {"ok": True, "message": "Senha redefinida. Entre novamente."}


@app.get(
    "/admin/solicitacoes-senha/",
    response_model=List[SolicitacaoSenhaResponse],
)
def listar_solicitacoes_senha(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    exigir_administrador(current_user)
    try:
        return db.query(
            models.SolicitacaoSenhaModel
        ).order_by(models.SolicitacaoSenhaModel.id.desc()).all()
    except Exception as exc:
        logger.exception("Erro ao listar solicitações de senha.")
        raise HTTPException(
            status_code=500,
            detail="Não foi possível consultar a fila de redefinição. Verifique se a tabela solicitacoes_senha existe no banco.",
        ) from exc


# ==============================================================================
# DIAGNÓSTICO E SAÚDE
# ==============================================================================

@app.get("/", include_in_schema=False)
def frontend_home():
    index = Path(__file__).resolve().parent / "static" / "index.html"
    if index.is_file():
        return FileResponse(index)
    return {"status": "online", "message": "API Duarte Performance 2.0"}


@app.get("/healthz")
def health_check():
    try:
        with engine.connect() as connection:
            connection.exec_driver_sql("SELECT 1")
        return {"status": "online", "database": "connected"}
    except Exception:
        logger.exception("Falha no health check do banco.")
        raise HTTPException(status_code=503, detail="Banco de dados indisponível.")


@app.get("/admin/diagnostico-cronograma")
def diagnostico_cronograma(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(obter_usuario_atual),
):
    exigir_administrador(current_user)
    try:
        total = db.query(
            models.CronogramaModel
        ).count()

        return {
            "status": "ok",
            "total_registros_cronograma": total,
        }

    except Exception:
        logger.exception(
            "Erro no diagnóstico do cronograma."
        )
        return {
            "status": "erro",
            "detalhes": (
                "Não foi possível consultar o cronograma."
            ),
        }

# Interface web servida pela mesma origem da API para evitar CORS permissivo.
_static_dir = Path(__file__).resolve().parent / "static"
if _static_dir.is_dir():
    app.mount("/app", StaticFiles(directory=str(_static_dir), html=True), name="frontend")
    @app.get("/{path:path}", include_in_schema=False)
    def frontend_spa_fallback(path: str):
        asset = (_static_dir / path).resolve()
        if asset.is_relative_to(_static_dir.resolve()) and asset.is_file():
            return FileResponse(asset)
        return FileResponse(_static_dir / "index.html")
