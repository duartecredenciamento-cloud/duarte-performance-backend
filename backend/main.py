from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel

from database import engine, get_db
from models import Base, Usuario
from auth import verificar_senha, criar_token_acesso, obter_hash_senha

# Cria as tabelas no banco caso não existam
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Duarte Performance API")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# --- SCHEMA PARA CADASTRO ---
class UsuarioCreate(BaseModel):
    username: str
    password: str
    nome: str = None
    email: str = None

# --- ROTA DE LOGIN (Para o Swagger e Frontend) ---
@app.post("/token")
def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Busca usuário no banco
    usuario = db.query(Usuario).filter(Usuario.username == form_data.username).first()
    
    # Verifica se o usuário existe e se a senha digitada bate com o password_hash do banco
    if not usuario or not verificar_senha(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Gera o Token
    access_token = criar_token_acesso(data={"sub": usuario.username})
    return {"access_token": access_token, "token_type": "bearer"}

# --- ROTA DE CADASTRO PÚBLICO ---
@app.post("/cadastro", status_code=status.HTTP_201_CREATED)
def criar_usuario(user_in: UsuarioCreate, db: Session = Depends(get_db)):
    # Verifica se username já existe
    if db.query(Usuario).filter(Usuario.username == user_in.username).first():
        raise HTTPException(status_code=400, detail="Username já cadastrado")
    
    # Cria o hash e salva na coluna password_hash
    hash_senha = obter_hash_senha(user_in.password)
    novo_usuario = Usuario(
        username=user_in.username,
        password_hash=hash_senha,  # <-- Coluna correta
        nome=user_in.nome,
        email=user_in.email
    )
    
    db.add(novo_usuario)
    db.commit()
    return {"msg": "Usuário criado com sucesso"}