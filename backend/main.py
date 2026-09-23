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
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from passlib.context import CryptContext
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session

import models
from database import engine, get_db


# ==============================================================================
# CONFIGURAÇÕES
# ==============================================================================

logger = logging.getLogger(__name__)

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480

# Obrigatória: não manter uma chave JWT fixa no código-fonte.
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

# Preserva o comportamento de criação de tabelas do projeto.
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Sistema de Gestão Operacional",
    version="2.2.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
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


class UsuarioResponse(UsuarioBase):
    id: int
    ativo: Optional[bool] = True

    class Config:
        from_attributes = True


class RegistroBase(BaseModel):
    operador_nome: Optional[str] = None
    cliente_nome: Optional[str] = None
    status: Optional[str] = None
    justificativa: Optional[str] = ""
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

    class Config:
        from_attributes = True


# ==============================================================================
# SENHAS E JWT
# ==============================================================================

def verificar_senha(
    plain_password: str,
    hashed_password: str,
) -> bool:
    if not hashed_password:
        return False

    try:
        return pwd_context.verify(
            plain_password,
            hashed_password,
        )
    except (TypeError, ValueError):
        # Um hash inválido não deve provocar erro 500 no login.
        logger.warning(
            "Foi encontrado um hash de senha inválido "
            "durante uma tentativa de login."
        )
        return False


def gerar_hash_senha(password: str) -> str:
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

    if usuario is None or usuario.ativo is False:
        raise credentials_exception

    return usuario


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
# PROVISIONAMENTO ADMINISTRATIVO SEGURO
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

    Regras:
    - Sem username/senha configurados, não faz nada.
    - Se o usuário não existe, cria como admin.
    - Se existe, só redefine a senha quando
      ADMIN_BOOTSTRAP_RESET_EXISTING=true.
    - Nunca imprime a senha nos logs.
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

    # bcrypt considera no máximo os primeiros 72 bytes da senha.
    if len(password.encode("utf-8")) > 72:
        raise RuntimeError(
            "ADMIN_BOOTSTRAP_PASSWORD deve ter no máximo "
            "72 bytes em UTF-8."
        )

    reset_existing = _variavel_verdadeira(
        "ADMIN_BOOTSTRAP_RESET_EXISTING"
    )

    db = next(get_db())

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
                nome="Abraão"
                if username.lower() == "abraao"
                else username,
                role="admin",
                ativo=True,
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
        usuario.ativo = True

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
        or usuario.ativo is False
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

    # A permissão vem do banco; não existe bypass por username.
    # O provisionamento acima define a role admin de Abraão.
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
    }


@app.get(
    "/usuarios/",
    response_model=List[UsuarioResponse],
)
def listar_todos_usuarios(
    db: Session = Depends(get_db),
):
    """Mantida para compatibilidade com o painel atual."""
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

    # Rota pública: nunca aceitar role=admin enviada pelo cliente.
    novo_usuario = models.Usuario(
        username=username,
        password_hash=gerar_hash_senha(usuario.password),
        nome=usuario.nome,
        email=usuario.email,
        role="operador",
        ativo=True,
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
):
    try:
        dados = registro.model_dump(
            exclude_unset=True
        )

        db_registro = models.RegistroModel(
            operador_nome=(
                dados.get("operador_nome")
                or "Operador"
            ),
            cliente_nome=(
                dados.get("cliente_nome")
                or "Atendimento Geral"
            ),
            status=(
                dados.get("status")
                or "Concluído"
            ),
            justificativa=(
                dados.get("justificativa")
                or ""
            ),
            periodo=(
                dados.get("periodo")
                or "Geral"
            ),
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

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail=(
                f"Erro ao salvar registro: {exc}"
            ),
        )


@app.get(
    "/registros/",
    response_model=List[RegistroResponse],
)
def listar_registros(
    skip: int = 0,
    limit: int = 500,
    db: Session = Depends(get_db),
):
    try:
        return (
            db.query(models.RegistroModel)
            .offset(skip)
            .limit(limit)
            .all()
        )

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
):
    try:
        return db.query(
            models.CronogramaModel
        ).all()

    except Exception:
        logger.exception(
            "Erro ao listar cronograma."
        )
        return []


@app.post(
    "/cronograma/",
    response_model=CronogramaResponse,
    status_code=status.HTTP_201_CREATED,
)
def criar_cronograma(
    cronograma: CronogramaCreate,
    db: Session = Depends(get_db),
):
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
    db_solicitacao = models.SolicitacaoSenhaModel(
        **solicitacao.model_dump(
            exclude_unset=True
        )
    )

    db.add(db_solicitacao)
    db.commit()
    db.refresh(db_solicitacao)

    registrar_log(
        db,
        usuario=solicitacao.username,
        acao="Solicitação de Senha",
        detalhes=(
            "Usuário pediu redefinição de senha."
        ),
    )

    return db_solicitacao


@app.get(
    "/admin/solicitacoes-senha/",
    response_model=List[SolicitacaoSenhaResponse],
)
def listar_solicitacoes_senha(
    db: Session = Depends(get_db),
):
    try:
        return db.query(
            models.SolicitacaoSenhaModel
        ).all()

    except Exception:
        logger.exception(
            "Erro ao listar solicitações de senha."
        )
        return []


# ==============================================================================
# DIAGNÓSTICO E SAÚDE
# ==============================================================================

@app.get("/")
def health_check():
    return {
        "status": "online",
        "message": (
            "API Duarte Gestão 100% Ativa"
        ),
    }


@app.get("/admin/diagnostico-cronograma")
def diagnostico_cronograma(
    db: Session = Depends(get_db),
):
    try:
        total = db.query(
            models.CronogramaModel
        ).count()

        return {
            "status": "ok",
            "total_registros_cronograma": total,
        }

    except Exception as exc:
        return {
            "status": "erro",
            "detalhes": str(exc),
        }