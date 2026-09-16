"""
Aplicação Principal FastAPI com Autenticação JWT, Suporte CORS e Rotas Operacionais.
"""
import datetime
from datetime import timedelta
from typing import List, Optional
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
from sqlalchemy.orm import Session
from jose import JWTError, jwt
from passlib.context import CryptContext

import models
from database import engine, get_db

# Cria automaticamente todas as tabelas registradas no models.py
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="Sistema de Gestão Operacional", version="2.0.0")

# ==============================================================================
# CONFIGURAÇÃO DE CORS (Essencial para comunicação Frontend <-> Backend)
# ==============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite requisições de qualquer origem
    allow_credentials=True,
    allow_methods=["*"],  # Permite todos os métodos (GET, POST, OPTIONS, etc.)
    allow_headers=["*"],
)

# Configurações do JWT e Criptografia
SECRET_KEY = "SUA_CHAVE_SECRETA_SUPER_SEGURA_AQUI"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas de sessão

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ==============================================================================
# SEGURANÇA E AUXILIARES DE AUTENTICAÇÃO
# ==============================================================================

def verificar_senha(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def gerar_hash_senha(password: str) -> str:
    return pwd_context.hash(password)

def criar_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.datetime.utcnow() + (expires_delta or timedelta(minutes=15))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def obter_usuario_atual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Não foi possível validar as credenciais",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception
        
    usuario = db.query(models.Usuario).filter(models.Usuario.username == username).first()
    if usuario is None:
        raise credentials_exception
    return usuario


# ==============================================================================
# SCHEMAS PYDANTIC (Validação de Dados)
# ==============================================================================

class Token(BaseModel):
    access_token: str
    token_type: str

class UsuarioBase(BaseModel):
    username: str
    nome: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = "ADMIN"

class UsuarioCreate(UsuarioBase):
    password: str

class UsuarioResponse(UsuarioBase):
    id: int

    class Config:
        from_attributes = True


class RegistroBase(BaseModel):
    operador_nome: str
    cliente_nome: str
    status: str
    justificativa: Optional[str] = ""
    periodo: Optional[str] = None

class RegistroCreate(RegistroBase):
    pass

class RegistroResponse(RegistroBase):
    id: int
    data_registro: datetime.datetime

    class Config:
        from_attributes = True


class CronogramaBase(BaseModel):
    operador: str
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
    username: str
    email: Optional[str] = None
    telefone: Optional[str] = None
    status: str
    solicitado_em: datetime.datetime

    class Config:
        from_attributes = True


# ==============================================================================
# FUNÇÃO AUXILIAR DE LOG
# ==============================================================================

def registrar_log(db: Session, usuario: str, acao: str, detalhes: str = None):
    log = models.LogAtividade(
        usuario=usuario,
        acao=acao,
        detalhes=detalhes,
        data_hora=datetime.datetime.utcnow()
    )
    db.add(log)
    db.commit()


# ==============================================================================
# ROTAS DE AUTENTICAÇÃO E USUÁRIOS
# ==============================================================================

@app.post("/token", response_model=Token)
def login_para_obter_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    usuario = db.query(models.Usuario).filter(models.Usuario.username == form_data.username).first()
    if not usuario or not verificar_senha(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = criar_access_token(
        data={"sub": usuario.username, "role": usuario.role}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/usuarios/me", response_model=UsuarioResponse)
def ler_usuario_logado(current_user: models.Usuario = Depends(obter_usuario_atual)):
    return current_user

@app.post("/usuarios/", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED)
def cadastrar_usuario(usuario: UsuarioCreate, db: Session = Depends(get_db)):
    db_user = db.query(models.Usuario).filter(models.Usuario.username == usuario.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Nome de usuário já cadastrado.")
    
    novo_usuario = models.Usuario(
        username=usuario.username,
        password_hash=gerar_hash_senha(usuario.password),
        nome=usuario.nome,
        email=usuario.email,
        role=usuario.role
    )
    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario


# ==============================================================================
# SETUP INICIAL DO ADMINISTRADOR E CARGA DE DADOS
# ==============================================================================

@app.get("/setup-admin")
def setup_admin_manual(db: Session = Depends(get_db)):
    # 1. Garante que o usuário erick exista e tenha permissão de ADMIN
    usuario = db.query(models.Usuario).filter(models.Usuario.username == "erick").first()
    if usuario:
        usuario.role = "ADMIN"
    else:
        usuario = models.Usuario(
            username="erick",
            password_hash=gerar_hash_senha("admin123"),
            nome="Erick",
            email="admin@duartegestao.com.br",
            role="ADMIN"
        )
        db.add(usuario)
    db.commit()

    # 2. Popula o banco com clientes padrão no cronograma se estiver vazio
    total_cronograma = db.query(models.CronogramaModel).count()
    if total_cronograma == 0:
        clientes_padrao = [
            "Suporte", "Suporte Operacional", "Antecipação", "Amil", 
            "Qualicorp", "Porto Seguro", "Bradesco", "Convenios"
        ]
        for cliente in clientes_padrao:
            novo_item = models.CronogramaModel(
                operador="GERAL",
                periodo="MANHÃ",
                segunda=cliente,
                terca=cliente,
                quarta=cliente,
                quinta=cliente,
                sexta=cliente
            )
            db.add(novo_item)
        db.commit()

    return {"status": "success", "message": "Admin configurado como ADMIN e carga inicial de clientes concluída!"}


# ==============================================================================
# ROTAS DE REGISTROS
# ==============================================================================

@app.post("/registros/", response_model=RegistroResponse, status_code=status.HTTP_201_CREATED)
def criar_registro(registro: RegistroCreate, db: Session = Depends(get_db)):
    db_registro = models.RegistroModel(**registro.model_dump())
    db.add(db_registro)
    db.commit()
    db.refresh(db_registro)
    
    registrar_log(db, usuario=registro.operador_nome, acao="Criou Registro", detalhes=f"Cliente: {registro.cliente_nome}")
    return db_registro

@app.get("/registros/", response_model=List[RegistroResponse])
def listar_registros(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(models.RegistroModel).offset(skip).limit(limit).all()


# ==============================================================================
# ROTAS DE CRONOGRAMA
# ==============================================================================

@app.get("/cronograma/", response_model=List[CronogramaResponse])
def listar_cronograma(db: Session = Depends(get_db)):
    return db.query(models.CronogramaModel).all()

@app.post("/cronograma/", response_model=CronogramaResponse, status_code=status.HTTP_201_CREATED)
def criar_cronograma(cronograma: CronogramaCreate, db: Session = Depends(get_db)):
    db_cronograma = models.CronogramaModel(**cronograma.model_dump())
    db.add(db_cronograma)
    db.commit()
    db.refresh(db_cronograma)
    return db_cronograma


# ==============================================================================
# ROTAS DE RECUPERAÇÃO DE SENHA
# ==============================================================================

@app.post("/recuperar-senha/", response_model=SolicitacaoSenhaResponse, status_code=status.HTTP_201_CREATED)
def solicitar_recuperacao_senha(solicitacao: SolicitacaoSenhaCreate, db: Session = Depends(get_db)):
    db_solicitacao = models.SolicitacaoSenhaModel(**solicitacao.model_dump())
    db.add(db_solicitacao)
    db.commit()
    db.refresh(db_solicitacao)
    
    registrar_log(db, usuario=solicitacao.username, acao="Solicitação de Senha", detalhes="Usuário pediu redefinição de senha.")
    return db_solicitacao

@app.get("/admin/solicitacoes-senha/", response_model=List[SolicitacaoSenhaResponse])
def listar_solicitacoes_senha(db: Session = Depends(get_db)):
    return db.query(models.SolicitacaoSenhaModel).all()


# ==============================================================================
# ROTA DE DIAGNÓSTICO E SAÚDE
# ==============================================================================

@app.get("/")
def health_check():
    return {"status": "online", "message": "API rodando perfeitamente!"}

@app.get("/admin/diagnostico-cronograma")
def diagnostico_cronograma(db: Session = Depends(get_db)):
    total = db.query(models.CronogramaModel).count()
    return {"status": "ok", "total_registros_cronograma": total}