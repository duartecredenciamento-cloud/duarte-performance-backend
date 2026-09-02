import traceback
from datetime import date, datetime, time, timedelta
from typing import Optional
from zoneinfo import ZoneInfo

from fastapi import Depends, FastAPI, HTTPException, Query, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from sqlalchemy import Index, text, func
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

import auth
import models
import schemas
from database import SessionLocal, engine, get_db

# Criação das tabelas caso não existam
models.Base.metadata.create_all(bind=engine)


def _garantir_autoincremento_users():
    """Garante a sequence e default de id na tabela users no PostgreSQL."""
    try:
        with engine.begin() as conn:
            if conn.dialect.name == "postgresql":
                conn.execute(
                    text("""
                    DO $$
                    BEGIN
                        IF NOT EXISTS (
                            SELECT 1 FROM pg_class c
                            JOIN pg_namespace n ON n.oid = c.relnamespace
                            WHERE c.relname = 'users_id_seq'
                        ) THEN
                            CREATE SEQUENCE users_id_seq;
                        END IF;

                        PERFORM setval(
                            'users_id_seq',
                            COALESCE((SELECT MAX(id) FROM users), 0) + 1,
                            false
                        );

                        ALTER TABLE users ALTER COLUMN id SET DEFAULT nextval('users_id_seq');
                    END $$;
                """)
                )
        print("✅ Autoincremento da coluna id (users) validado no PostgreSQL.")
    except Exception as e:
        print(f"⚠️ Aviso ao verificar autoincremento de users.id: {e}")


app = FastAPI(
    title="Duarte Performance API",
    version="2.9.4",
    description="API de Gestão Operacional e Autenticação",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup_event():
    _garantir_autoincremento_users()


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/token")

# =====================================================
# DEPENDÊNCIA DE AUTENTICAÇÃO
# =====================================================


def usuario_logado(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
):
    try:
        payload = jwt.decode(
            token, auth.SECRET_KEY, algorithms=[auth.ALGORITHM]
        )
        username: str = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token expirado ou inválido",
        )

    usuario = (
        db.query(models.Usuario)
        .filter(
            func.lower(models.Usuario.username) == username.strip().lower()
        )
        .first()
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado",
        )
    return usuario


# =====================================================
# ROTAS DE AUTENTICAÇÃO E SETUP
# =====================================================


@app.get("/")
def home():
    return {
        "status": "online",
        "sistema": "Duarte Performance API",
        "versao": "2.9.4",
    }


@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db),
):
    login_input = form_data.username.strip().lower()

    # Busca no banco de forma insensível a maiúsculas
    usuario = (
        db.query(models.Usuario)
        .filter(func.lower(models.Usuario.username) == login_input)
        .first()
    )

    if not usuario or not auth.verificar_senha(
        form_data.password, usuario.password_hash
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos.",
        )

    token = auth.criar_token_acesso(
        {
            "sub": usuario.username,
            "nome": usuario.username,
            "role": usuario.role,
            "id": usuario.id,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": usuario.username,
        "nome": usuario.username,
        "role": usuario.role,
    }


@app.get("/setup-admin")
def setup_admin_manual(db: Session = Depends(get_db)):
    try:
        admin = (
            db.query(models.Usuario)
            .filter(
                (func.lower(models.Usuario.username) == "admin@duarte.com")
                | (func.lower(models.Usuario.username) == "admin")
            )
            .first()
        )

        senha_hash = auth.obter_hash_senha("123456")

        if not admin:
            admin = models.Usuario(
                username="admin@duarte.com",
                password_hash=senha_hash,
                role="Admin",
            )
            db.add(admin)
            db.commit()
            db.refresh(admin)
            return {
                "status": "sucesso",
                "mensagem": "Usuário admin criado com sucesso. Senha: 123456",
            }

        admin.password_hash = senha_hash
        db.commit()
        return {
            "status": "sucesso",
            "mensagem": f"Senha do usuário '{admin.username}' redefinida para 123456",
        }

    except SQLAlchemyError as e:
        db.rollback()
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro de banco de dados no setup admin: {str(e.__cause__ or e)}",
        )


@app.get("/me")
def obter_perfil_atual(usuario: models.Usuario = Depends(usuario_logado)):
    return {
        "id": usuario.id,
        "username": usuario.username,
        "role": usuario.role,
        "departamento": usuario.departamento,
    }


# =====================================================
# GESTÃO DE USUÁRIOS
# =====================================================


@app.get("/usuarios")
def listar_usuarios(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(usuario_logado),
):
    usuarios = db.query(models.Usuario).all()
    return [
        {
            "id": u.id,
            "username": u.username,
            "role": u.role,
            "departamento": u.departamento,
        }
        for u in usuarios
    ]


@app.post("/usuarios")
def criar_usuario(
    dados: schemas.UsuarioCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(usuario_logado),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem criar usuários.",
        )

    existente = (
        db.query(models.Usuario)
        .filter(
            func.lower(models.Usuario.username) == dados.username.strip().lower()
        )
        .first()
    )
    if existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário já cadastrado.",
        )

    novo_usuario = models.Usuario(
        username=dados.username.strip(),
        password_hash=auth.obter_hash_senha(dados.senha),
        role=dados.role or "Operador",
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {
        "status": "sucesso",
        "id": novo_usuario.id,
        "username": novo_usuario.username,
    }


@app.delete("/usuarios/{usuario_id}")
def deletar_usuario(
    usuario_id: int,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(usuario_logado),
):
    if current_user.role != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Apenas administradores podem excluir usuários.",
        )

    usuario = (
        db.query(models.Usuario).filter(models.Usuario.id == usuario_id).first()
    )
    if not usuario:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Usuário não encontrado.",
        )

    db.delete(usuario)
    db.commit()
    return {"status": "sucesso", "mensagem": "Usuário removido."}


# =====================================================
# REGISTROS E APONTAMENTOS
# =====================================================


@app.get("/registros")
def listar_registros(
    data: Optional[str] = None,
    operador: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(usuario_logado),
):
    query = db.query(models.RegistroModel)

    if operador:
        query = query.filter(
            func.lower(models.RegistroModel.operador_nome)
            == operador.strip().lower()
        )

    if data:
        try:
            data_dt = datetime.strptime(data, "%Y-%m-%d").date()
            query = query.filter(
                func.date(models.RegistroModel.data_registro) == data_dt
            )
        except ValueError:
            pass

    registros = query.order_by(models.RegistroModel.data_registro.desc()).all()
    return registros


@app.post("/registros")
def criar_registro(
    registro: schemas.RegistroCreate,
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(usuario_logado),
):
    cliente_final = registro.cliente_nome or registro.cliente
    operador_final = registro.operador_nome or current_user.username

    novo_registro = models.RegistroModel(
        operador_nome=operador_final,
        cliente_nome=cliente_final or "N/A",
        status=registro.status,
        justificativa=registro.justificativa or "",
    )

    db.add(novo_registro)
    db.commit()
    db.refresh(novo_registro)
    return novo_registro


# =====================================================
# CRONOGRAMA DE ESCALAS
# =====================================================


@app.get("/cronograma")
def obter_cronograma(
    db: Session = Depends(get_db),
    current_user: models.Usuario = Depends(usuario_logado),
):
    return db.query(models.CronogramaModel).all()