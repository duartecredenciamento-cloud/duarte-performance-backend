from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from models import Base, Usuario
from auth import verificar_senha, criar_token_acesso, obter_hash_senha
from backend.database import engine, get_db

# -----------------------------------------------------------------------------
# Inicialização e Criação das Tabelas
# -----------------------------------------------------------------------------
Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Duarte Performance API",
    description="API de controle operacional com trilhas de auditoria",
    version="1.0.0"
)

# -----------------------------------------------------------------------------
# Configuração de CORS (Essencial para comunicação Frontend <-> Backend no Render)
# -----------------------------------------------------------------------------
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Libera requisições de qualquer origem
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# -----------------------------------------------------------------------------
# Schemas (Pydantic Models)
# -----------------------------------------------------------------------------
class UsuarioCreate(BaseModel):
    username: str
    password: str
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None

class UsuarioUpdate(BaseModel):
    nome: Optional[str] = None
    email: Optional[str] = None
    telefone: Optional[str] = None
    perfil_completo: Optional[bool] = True

class UsuarioResponse(BaseModel):
    id: int
    username: str
    nome: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = "operador"
    perfil_completo: Optional[bool] = False

    class Config:
        from_attributes = True

class TokenResponse(BaseModel):
    access_token: str
    token_type: str

# -----------------------------------------------------------------------------
# Rotas Principais
# -----------------------------------------------------------------------------

@app.get("/")
def root():
    return {"status": "ok", "mensagem": "Duarte Performance API rodando perfeitamente!"}


@app.post("/token", response_model=TokenResponse, summary="Login / Geração de Token JWT")
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Autentica o usuário comparando a senha digitada com a coluna password_hash do PostgreSQL.
    """
    usuario = db.query(Usuario).filter(Usuario.username == form_data.username).first()

    # Validação do Usuário e Senha no Hash
    if not usuario or not verificar_senha(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Gera Token JWT
    access_token = criar_token_acesso(data={"sub": usuario.username, "role": usuario.role})
    return {"access_token": access_token, "token_type": "bearer"}


@app.post("/cadastro", response_model=UsuarioResponse, status_code=status.HTTP_201_CREATED, summary="Cadastro Público de Usuário")
def cadastrar_usuario(user_in: UsuarioCreate, db: Session = Depends(get_db)):
    """
    Cadastra um novo usuário criptografando a senha diretamente na coluna password_hash.
    """
    usuario_existente = db.query(Usuario).filter(Usuario.username == user_in.username).first()
    if usuario_existente:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Nome de usuário já cadastrado no sistema."
        )

    hash_senha = obter_hash_senha(user_in.password)
    
    novo_usuario = Usuario(
        username=user_in.username,
        password_hash=hash_senha,  # Bate com o nome exato da coluna no PostgreSQL
        nome=user_in.nome,
        email=user_in.email,
        telefone=user_in.telefone,
        role="operador",
        perfil_completo=False
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)
    return novo_usuario


@app.get("/usuarios/me", response_model=UsuarioResponse, summary="Obter dados do usuário logado")
def obter_perfil_atual(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    # Rota mock/suporte para perfil atual
    from jose import jwt, JWTError
    from auth import SECRET_KEY, ALGORITHM

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Token inválido")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido ou expirado")

    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")
    
    return usuario


@app.put("/usuarios/me", summary="Completar / Atualizar Perfil")
def atualizar_perfil(dados: UsuarioUpdate, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    from jose import jwt, JWTError
    from auth import SECRET_KEY, ALGORITHM

    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=401, detail="Token inválido")

    usuario = db.query(Usuario).filter(Usuario.username == username).first()
    if not usuario:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    if dados.nome: usuario.nome = dados.nome
    if dados.email: usuario.email = dados.email
    if dados.telefone: usuario.telefone = dados.telefone
    usuario.perfil_completo = True

    db.commit()
    return {"msg": "Perfil atualizado com sucesso"}


@app.get("/cronograma/", summary="Listar Cronograma Operacional")
def listar_cronograma(token: str = Depends(oauth2_scheme)):
    # Rota base para sincronização do cronograma
    return {"msg": "Rota de cronograma operacional ativa", "dados": []}