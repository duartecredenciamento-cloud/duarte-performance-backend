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

app = FastAPI(title="Sistema de Gestão Operacional", version="2.1.0")

# ==============================================================================
# CONFIGURAÇÃO DE CORS
# ==============================================================================
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configurações do JWT e Criptografia
SECRET_KEY = "SUA_CHAVE_SECRETA_SUPER_SEGURA_AQUI"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 480  # 8 horas de sessão

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")


# ==============================================================================
# SCHEMAS PYDANTIC (Flexibilizados para evitar erros 500 com campos nulos/ausentes)
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

def registrar_log(db: Session, usuario: str, acao: str, detalhes: str = None):
    try:
        log = models.LogAtividade(
            usuario=usuario,
            acao=acao,
            detalhes=detalhes,
            data_hora=datetime.datetime.utcnow()
        )
        db.add(log)
        db.commit()
    except Exception:
        db.rollback()


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
    
    user_role = "admin" if usuario.username.lower() == "erick" else (usuario.role or "operador").lower()

    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = criar_access_token(
        data={"sub": usuario.username, "role": user_role}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token, 
        "token_type": "bearer",
        "role": user_role,
        "username": usuario.username
    }

@app.get("/usuarios/", response_model=List[UsuarioResponse])
def listar_todos_usuarios(db: Session = Depends(get_db)):
    """Rota para o Painel Admin carregar a lista de usuários da equipe"""
    try:
        return db.query(models.Usuario).all()
    except Exception:
        return []

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
# SETUP INICIAL DO ADMINISTRADOR
# ==============================================================================

@app.get("/setup-admin")
def setup_admin_manual(db: Session = Depends(get_db)):
    try:
        usuarios = db.query(models.Usuario).filter(models.Usuario.username.ilike("erick")).all()
        
        if usuarios:
            for u in usuarios:
                u.role = "admin"
                u.password_hash = gerar_hash_senha("admin123")
            db.commit()
            return {"status": "success", "message": "Role do Erick alterada para admin e senha definida como admin123!"}
        
        novo_admin = models.Usuario(
            username="erick",
            password_hash=gerar_hash_senha("admin123"),
            nome="Erick",
            email="admin@duartegestao.com.br",
            role="admin"
        )
        db.add(novo_admin)
        db.commit()
        return {"status": "success", "message": "Usuário erick criado com role admin!"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Erro ao configurar admin: {str(e)}")


# ==============================================================================
# ROTAS DE REGISTROS (DASHBOARD, RELATÓRIOS E EDITOR)
# ==============================================================================

@app.post("/registros/", response_model=RegistroResponse, status_code=status.HTTP_201_CREATED)
def criar_registro(registro: RegistroCreate, db: Session = Depends(get_db)):
    try:
        dados = registro.model_dump(exclude_unset=True)
        
        db_registro = models.RegistroModel(
            operador_nome=dados.get("operador_nome") or "Operador",
            cliente_nome=dados.get("cliente_nome") or "Atendimento Geral",
            status=dados.get("status") or "Concluído",
            justificativa=dados.get("justificativa") or "",
            periodo=dados.get("periodo") or "Geral"
        )
        
        db.add(db_registro)
        db.commit()
        db.refresh(db_registro)
        
        registrar_log(
            db, 
            usuario=db_registro.operador_nome, 
            acao="Criou Registro", 
            detalhes=f"Cliente: {db_registro.cliente_nome}"
        )
        return db_registro
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Erro ao salvar registro: {str(e)}"
        )

@app.get("/registros/", response_model=List[RegistroResponse])
def listar_registros(skip: int = 0, limit: int = 500, db: Session = Depends(get_db)):
    """Carrega as tabelas e gráficos do frontend"""
    try:
        return db.query(models.RegistroModel).offset(skip).limit(limit).all()
    except Exception:
        return []


# ==============================================================================
# ROTAS DE CRONOGRAMA
# ==============================================================================

@app.get("/cronograma/", response_model=List[CronogramaResponse])
def listar_cronograma(db: Session = Depends(get_db)):
    try:
        return db.query(models.CronogramaModel).all()
    except Exception:
        return []

@app.post("/cronograma/", response_model=CronogramaResponse, status_code=status.HTTP_201_CREATED)
def criar_cronograma(cronograma: CronogramaCreate, db: Session = Depends(get_db)):
    db_cronograma = models.CronogramaModel(**cronograma.model_dump(exclude_unset=True))
    db.add(db_cronograma)
    db.commit()
    db.refresh(db_cronograma)
    return db_cronograma


# ==============================================================================
# ROTAS DE RECUPERAÇÃO DE SENHA E ADMIN
# ==============================================================================

@app.post("/recuperar-senha/", response_model=SolicitacaoSenhaResponse, status_code=status.HTTP_201_CREATED)
def solicitar_recuperacao_senha(solicitacao: SolicitacaoSenhaCreate, db: Session = Depends(get_db)):
    db_solicitacao = models.SolicitacaoSenhaModel(**solicitacao.model_dump(exclude_unset=True))
    db.add(db_solicitacao)
    db.commit()
    db.refresh(db_solicitacao)
    
    registrar_log(db, usuario=solicitacao.username, acao="Solicitação de Senha", detalhes="Usuário pediu redefinição de senha.")
    return db_solicitacao

@app.get("/admin/solicitacoes-senha/", response_model=List[SolicitacaoSenhaResponse])
def listar_solicitacoes_senha(db: Session = Depends(get_db)):
    try:
        return db.query(models.SolicitacaoSenhaModel).all()
    except Exception:
        return []


# ==============================================================================
# DIAGNÓSTICO E SAÚDE
# ==============================================================================

@app.get("/")
def health_check():
    return {"status": "online", "message": "API Duarte Gestão 100% Ativa"}

@app.get("/admin/diagnostico-cronograma")
def diagnostico_cronograma(db: Session = Depends(get_db)):
    try:
        total = db.query(models.CronogramaModel).count()
        return {"status": "ok", "total_registros_cronograma": total}
    except Exception as e:
        return {"status": "erro", "detalhes": str(e)}