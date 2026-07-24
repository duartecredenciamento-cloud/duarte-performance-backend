from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

# Importações internas do seu projeto
import models
import auth
from database import get_db, engine

# Cria automaticamente as tabelas no PostgreSQL caso não existam
models.Base.metadata.create_all(bind=engine)

app = FastAPI(
    title="Duarte Performance API",
    description="Backend de Inteligência Operacional & Credenciamento de Saúde",
    version="2.4"
)

# Configuração de CORS (Libera o frontend no Streamlit para fazer requisições)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# =====================================================
# INICIALIZAÇÃO AUTOMÁTICA (Startup)
# =====================================================
@app.on_event("startup")
def inicializar_admin_padrao():
    """Garante que o usuário admin master exista e esteja com a senha correta ao subir a aplicação."""
    try:
        db: Session = next(get_db())
        username_admin = "admin"
        admin = db.query(models.Usuario).filter(models.Usuario.username == username_admin).first()
        
        if not admin:
            novo_admin = models.Usuario(
                username=username_admin,
                password_hash=auth.obter_hash_senha("Duarte1234#"),
                nome="Administrador Duarte",
                email="admin@duartegestao.com.br",
                role="Admin Master",
                perfil_completo=True
            )
            db.add(novo_admin)
            db.commit()
            print("✅ Usuário 'admin' padrão criado com sucesso no banco!")
        else:
            admin.password_hash = auth.obter_hash_senha("Duarte1234#")
            admin.role = "Admin Master"
            db.commit()
            print("✅ Senha do usuário 'admin' redefinida para 'Duarte1234#' com sucesso!")
        db.close()
    except Exception as e:
        print(f"⚠️ Aviso na inicialização do admin: {e}")


# =====================================================
# ROTAS DE DIAGNÓSTICO E EMERGÊNCIA
# =====================================================
@app.get("/")
def health_check():
    return {"status": "online", "sistema": "Duarte Performance Backend", "versao": "2.4"}


@app.get("/criar-admin-agora")
def criar_admin_emergencia(db: Session = Depends(get_db)):
    """
    Rota de emergência acessível pelo navegador para forçar a criação/reset do admin.
    URL: https://duarte-performance-backend.onrender.com/criar-admin-agora
    """
    try:
        admin = db.query(models.Usuario).filter(models.Usuario.username == "admin").first()
        if not admin:
            admin = models.Usuario(
                username="admin",
                password_hash=auth.obter_hash_senha("Duarte1234#"),
                nome="Administrador Duarte",
                email="admin@duartegestao.com.br",
                role="Admin Master",
                perfil_completo=True
            )
            db.add(admin)
        else:
            admin.password_hash = auth.obter_hash_senha("Duarte1234#")
            admin.role = "Admin Master"
        
        db.commit()
        return {
            "status": "SUCESSO", 
            "mensagem": "Usuário 'admin' registrado no PostgreSQL com a senha 'Duarte1234#'!"
        }
    except Exception as e:
        return {"status": "ERRO", "detalhe": str(e)}


# =====================================================
# ROTA DE AUTENTICAÇÃO (LOGIN JWT)
# =====================================================
@app.post("/token")
def login_para_acesso_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    """Endpoint oficial de login exigido pelo Streamlit."""
    username_limpo = form_data.username.strip()
    password_limpa = form_data.password.strip()

    user = db.query(models.Usuario).filter(models.Usuario.username == username_limpo).first()
    
    if not user or not auth.verificar_senha(password_limpa, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário ou senha incorretos",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = auth.criar_token_acesso(data={"sub": user.username, "role": user.role})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user.username,
        "nome": user.nome or user.username,
        "role": user.role
    }