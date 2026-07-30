from fastapi import (
    FastAPI,
    Depends,
    HTTPException,
    status
)

from fastapi.security import (
    OAuth2PasswordRequestForm,
    OAuth2PasswordBearer
)

from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from jose import JWTError, jwt

from pydantic import BaseModel

import models
import schemas
import auth

from database import (
    get_db,
    engine,
    SessionLocal
)


# =====================================================
# CRIAÇÃO DAS TABELAS E DADOS INICIAIS
# =====================================================

models.Base.metadata.create_all(
    bind=engine
)


def criar_admin_inicial():
    """
    Verifica se o usuário administrador padrão existe.
    Caso não exista, cria automaticamente utilizando os campos
    exatos do models.Usuario, com tratamento de erros para deploy.
    """
    db = SessionLocal()
    try:
        # Verifica se o admin já existe pelo username
        admin_existente = (
            db.query(models.Usuario)
            .filter(models.Usuario.username == "admin@duarte.com")
            .first()
        )

        if not admin_existente:
            # Nunca salva a senha em texto puro, utiliza o bcrypt do auth.py
            senha_criptografada = auth.obter_hash_senha("123456")
            
            novo_admin = models.Usuario(
                username="admin@duarte.com",
                email="admin@duarte.com",
                nome="Administrador",
                password_hash=senha_criptografada,
                role="Admin",
                perfil_completo=True
            )
            
            db.add(novo_admin)
            db.commit()
            print("✅ Usuário administrador criado com sucesso no banco de dados.")
            
    except IntegrityError:
        # Evita erro fatal se múltiplos workers da Railway tentarem criar o admin ao mesmo tempo
        db.rollback()
        print("⚠️ Usuário admin já foi registrado por outro processo (IntegrityError evitado).")
    except Exception as e:
        # Garante que qualquer outro erro não trave o banco (database is locked)
        db.rollback()
        print(f"❌ Erro ao criar usuário administrador inicial: {e}")
    finally:
        # Garante que a sessão será fechada corretamente, liberando o banco
        db.close()


# =====================================================
# CONFIGURAÇÃO API
# =====================================================

app = FastAPI(
    title="Duarte Performance API",
    description="Gestão Operacional Duarte Gestão",
    version="2.6"
)

# Aciona a função de criação do admin na inicialização da API
@app.on_event("startup")
def startup_event():
    criar_admin_inicial()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# =====================================================
# JWT & AUTENTICAÇÃO
# =====================================================

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl="/token"
)

def usuario_logado(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    try:
        payload = jwt.decode(
            token,
            auth.SECRET_KEY,
            algorithms=[auth.ALGORITHM]
        )
        username = payload.get("sub")
        if not username:
            raise HTTPException(
                status_code=401,
                detail="Token inválido"
            )
    except JWTError:
        raise HTTPException(
            status_code=401,
            detail="Token expirado ou inválido"
        )

    usuario = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == username)
        .first()
    )

    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuário não encontrado"
        )
    return usuario



# =====================================================
# HEALTH CHECK
# =====================================================

@app.get("/")
def home():
    return {
        "status":"online",
        "sistema":"Duarte Performance API",
        "versao":"2.6"
    }


# =====================================================
# ROTA DE RESGATE DO ADMIN (SETUP RÁPIDO)
# =====================================================

@app.get("/setup-admin")
def setup_admin_manual(db: Session = Depends(get_db)):
    """Acesse essa URL no navegador para criar/resetar o admin instantaneamente."""
    admin = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == "admin@duarte.com")
        .first()
    )

    senha_hash = auth.obter_hash_senha("123456")

    if not admin:
        admin = models.Usuario(
            username="admin@duarte.com",
            email="admin@duarte.com",
            nome="Administrador",
            password_hash=senha_hash,
            role="Admin",
            perfil_completo=True,
        )
        db.add(admin)
        db.commit()
        return {
            "status": "sucesso",
            "mensagem": "✅ Usuário admin@duarte.com criado do zero com a senha 123456!"
        }
    else:
        admin.password_hash = senha_hash
        db.commit()
        return {
            "status": "sucesso",
            "mensagem": "✅ Senha do usuário admin@duarte.com redefinida para 123456!"
        }


# =====================================================
# LOGIN
# =====================================================

@app.post("/token")
def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    usuario = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == form_data.username)
        .first()
    )

    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha inválidos"
        )

    if not auth.verificar_senha(form_data.password, usuario.password_hash):
        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha inválidos"
        )

    token = auth.criar_token_acesso(
        {
            "sub": usuario.username,
            "nome": usuario.nome,
            "role": usuario.role,
            "id": usuario.id
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "username": usuario.username,
        "nome": usuario.nome,
        "role": usuario.role
    }


# =====================================================
# GESTÃO DE USUÁRIOS (CADASTRO)
# =====================================================

@app.post("/usuarios/", status_code=201)
def criar_usuario(
    dados: schemas.UsuarioCreate, 
    db: Session = Depends(get_db)
):
    """
    Cria um novo usuário no sistema garantindo hash da senha
    e checagem de duplicidade.
    """
    
    usuario_existente = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == dados.username)
        .first()
    )

    if usuario_existente:
        raise HTTPException(
            status_code=400, 
            detail="Este nome de usuário/e-mail já existe."
        )

    senha_hash = auth.obter_hash_senha(dados.senha)

    novo_usuario = models.Usuario(
        username=dados.username,
        email=dados.email if hasattr(dados, "email") and dados.email else dados.username,
        nome=dados.nome,
        password_hash=senha_hash,
        role=dados.role if hasattr(dados, "role") and dados.role else "Operador",
        perfil_completo=True,
    )

    db.add(novo_usuario)
    db.commit()
    db.refresh(novo_usuario)

    return {
        "status": "sucesso",
        "mensagem": f"Usuário {novo_usuario.nome} criado com sucesso!",
        "id": novo_usuario.id,
    }


# =====================================================
# GESTÃO DE PERMISSÕES / FUNÇÕES (ROLES)
# =====================================================

ROLES_VALIDAS = ["Operador", "Visualizador", "Gestor", "Admin"]


class RoleUpdate(BaseModel):
    role: str


def exigir_admin_ou_gestor(
    usuario: models.Usuario = Depends(usuario_logado),
) -> models.Usuario:
    """Libera o acesso apenas para Admin ou Gestor."""
    if usuario.role not in ("Admin", "Gestor"):
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito a usuários Admin ou Gestor.",
        )
    return usuario


def exigir_admin(
    usuario: models.Usuario = Depends(usuario_logado),
) -> models.Usuario:
    """Libera o acesso apenas para Admin."""
    if usuario.role != "Admin":
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito ao perfil Admin.",
        )
    return usuario


@app.get("/usuarios/todos")
def listar_todos_usuarios(
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin_ou_gestor),
):
    """Retorna id, nome, username, email e role de todos os usuários."""
    usuarios = db.query(models.Usuario).order_by(models.Usuario.nome).all()
    return [
        {
            "id": u.id,
            "nome": u.nome,
            "username": u.username,
            "email": u.email,
            "role": u.role,
        }
        for u in usuarios
    ]


@app.put("/usuarios/{usuario_id}/role")
def atualizar_role_usuario(
    usuario_id: int,
    dados: RoleUpdate,
    db: Session = Depends(get_db),
    _: models.Usuario = Depends(exigir_admin),
):
    """Atualiza a função (role) de um usuário. Somente Admin pode chamar."""
    if dados.role not in ROLES_VALIDAS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Função inválida. Use uma das opções: "
                + ", ".join(ROLES_VALIDAS)
            ),
        )

    usuario_alvo = (
        db.query(models.Usuario)
        .filter(models.Usuario.id == usuario_id)
        .first()
    )

    if not usuario_alvo:
        raise HTTPException(
            status_code=404, detail="Usuário não encontrado."
        )

    usuario_alvo.role = dados.role
    db.commit()
    db.refresh(usuario_alvo)

    return {
        "status": "sucesso",
        "mensagem": (
            f"Função de {usuario_alvo.nome} atualizada para"
            f" {usuario_alvo.role}."
        ),
        "id": usuario_alvo.id,
        "role": usuario_alvo.role,
    }


# =====================================================
# PERFIL DO USUÁRIO
# =====================================================

@app.get("/usuarios/me")
def meu_usuario(usuario: models.Usuario = Depends(usuario_logado)):
    return {
        "id": usuario.id,
        "username": usuario.username,
        "nome": usuario.nome,
        "email": usuario.email,
        "role": usuario.role,
        "perfil_completo": usuario.perfil_completo
    }


# =====================================================
# REGISTROS OPERACIONAIS
# =====================================================

@app.post("/registros/", response_model=schemas.RegistroOut)
def criar_registro(
    registro: schemas.RegistroCreate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado)
):
    novo = models.RegistroModel(
        operador_nome=usuario.nome,
        cliente_nome=registro.cliente_nome,
        status=registro.status,
        justificativa=registro.justificativa
    )
    db.add(novo)
    db.commit()
    db.refresh(novo)
    return novo


@app.get("/registros/", response_model=list[schemas.RegistroOut])
def listar_registros(
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado)
):
    registros = (
        db.query(models.RegistroModel)
        .order_by(models.RegistroModel.data_registro.desc())
        .all()
    )
    return registros


@app.put("/registros/{registro_id}")
def atualizar_registro(
    registro_id: int,
    dados: schemas.RegistroUpdate,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado)
):
    registro = (
        db.query(models.RegistroModel)
        .filter(models.RegistroModel.id == registro_id)
        .first()
    )

    if not registro:
        raise HTTPException(404, "Registro não encontrado")

    for campo, valor in dados.dict(exclude_unset=True).items():
        setattr(registro, campo, valor)

    db.commit()
    return {"status": "Atualizado"}


@app.delete("/registros/{registro_id}")
def deletar_registro(
    registro_id: int,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado)
):
    registro = (
        db.query(models.RegistroModel)
        .filter(models.RegistroModel.id == registro_id)
        .first()
    )

    if not registro:
        raise HTTPException(404, "Registro não encontrado")

    db.delete(registro)
    db.commit()
    return {"status": "Excluído"}


# =====================================================
# CRONOGRAMA DINÂMICO
# =====================================================

@app.get("/cronograma/")
def listar_cronograma(
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado)
):
    """Busca toda a escala cadastrada no banco de dados."""
    dados = db.query(models.CronogramaModel).all()
    return [
        {
            "id": c.id,
            "Operador": c.operador,
            "Periodo": c.periodo,
            "Segunda": c.segunda,
            "Terça": c.terca,
            "Quarta": c.quarta,
            "Quinta": c.quinta,
            "Sexta": c.sexta,
        }
        for c in dados
    ]


@app.post("/cronograma/")
def criar_ou_atualizar_item_escala(
    payload: dict,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado),
):
    """Adiciona um novo operador/escala ou atualiza um existente."""
    if usuario.role.lower() not in ["admin", "gestor"]:
        raise HTTPException(
            status_code=403, detail="Apenas Admin/Gestor pode alterar a escala."
        )

    novo_item = models.CronogramaModel(
        operador=payload.get("Operador", "").upper(),
        periodo=payload.get("Periodo", "MANHÃ").upper(),
        segunda=payload.get("Segunda", "-"),
        terca=payload.get("Terça", "-"),
        quarta=payload.get("Quarta", "-"),
        quinta=payload.get("Quinta", "-"),
        sexta=payload.get("Sexta", "-"),
    )
    db.add(novo_item)
    db.commit()
    db.refresh(novo_item)

    return {"status": "sucesso", "mensagem": "Escala atualizada com sucesso!"}


@app.delete("/cronograma/{item_id}")
def deletar_item_escala(
    item_id: int,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado),
):
    """Exclui uma linha da escala (Remover operador ou turno)."""
    if usuario.role.lower() not in ["admin", "gestor"]:
        raise HTTPException(
            status_code=403, detail="Apenas Admin/Gestor pode excluir itens."
        )

    item = (
        db.query(models.CronogramaModel)
        .filter(models.CronogramaModel.id == item_id)
        .first()
    )
    if not item:
        raise HTTPException(status_code=404, detail="Item não encontrado.")

    db.delete(item)
    db.commit()
    return {"status": "sucesso", "mensagem": "Item removido da escala!"}