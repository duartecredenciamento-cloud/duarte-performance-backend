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


# Matriz padrão AGOSTO II (Gestão Comercial)
MATRIZ_AGOSTO_II = [
    {"operador": "LARISSA", "periodo": "MANHÃ", "segunda": "EV-CITI", "terca": "CONVACARE", "quarta": "IMC", "quinta": "MEDLIGTH", "sexta": "PRÉ ALINHAMENTO"},
    {"operador": "LARISSA", "periodo": "TARDE", "segunda": "-", "terca": "-", "quarta": "-", "quinta": "-", "sexta": "RESCINDIDOS - UNICLIN/MAR/SILMARO e ETC"},
    {"operador": "KARINE", "periodo": "MANHÃ", "segunda": "ALPHA LABs", "terca": "CLINICA TOPÁZIO", "quarta": "RALG 1° e 3° SEMANA", "quinta": "ATIVAMENTE", "sexta": "MVS"},
    {"operador": "KARINE", "periodo": "TARDE", "segunda": "-", "terca": "-", "quarta": "PRIME 2° SEMANA", "quinta": "-", "sexta": "DIOGO PARAUAPEBAS"},
    {"operador": "NEIA", "periodo": "MANHÃ", "segunda": "CLINICA VIVENCY", "terca": "RBL 1° e 3° SEMANA", "quarta": "CLINICA AMINO", "quinta": "CLINICA FARFALLA", "sexta": "INST. VER"},
    {"operador": "NEIA", "periodo": "TARDE", "segunda": "-", "terca": "-", "quarta": "-", "quinta": "-", "sexta": "-"},
    {"operador": "SILVANA", "periodo": "MANHÃ", "segunda": "PRO-EXAME", "terca": "CLIN COFFI", "quarta": "HOSP. AMATO", "quinta": "TRIDES", "sexta": "HARMONY"},
    {"operador": "SILVANA", "periodo": "TARDE", "segunda": "-", "terca": "-", "quarta": "LAB. BRUNO", "quinta": "-", "sexta": "-"},
    {"operador": "JULIA", "periodo": "MANHÃ", "segunda": "FR FISIO", "terca": "CANTAREIRA", "quarta": "CIE FISIO - SJC", "quinta": "CLINICA ROSANA", "sexta": "VIVA - TEA"},
    {"operador": "JULIA", "periodo": "TARDE", "segunda": "-", "terca": "-", "quarta": "-", "quinta": "-", "sexta": "-"},
    {"operador": "EDVÂNIA", "periodo": "MANHÃ", "segunda": "REGULAÇÃO", "terca": "EDITAIS", "quarta": "EDITAIS", "quinta": "FISO LIFE", "sexta": "EMS-BETESDA 1º e 3º SEMANA"},
    {"operador": "EDVÂNIA", "periodo": "TARDE", "segunda": "-", "terca": "-", "quarta": "-", "quinta": "-", "sexta": "MULHER MODERNA 2° SEMANA"},
]


def criar_admin_inicial():
    """Cria o admin padrão se não existir."""
    db = SessionLocal()
    try:
        admin_existente = (
            db.query(models.Usuario)
            .filter(models.Usuario.username == "admin@duarte.com")
            .first()
        )

        if not admin_existente:
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
        db.rollback()
        print("⚠️ Usuário admin já foi registrado por outro processo.")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao criar usuário administrador inicial: {e}")
    finally:
        db.close()


def popular_cronograma_se_vazio():
    """Se a tabela de cronograma estiver vazia, carrega a matriz AGOSTO II."""
    db = SessionLocal()
    try:
        total = db.query(models.CronogramaModel).count()
        if total == 0:
            for item in MATRIZ_AGOSTO_II:
                db.add(
                    models.CronogramaModel(
                        operador=item["operador"],
                        periodo=item["periodo"],
                        segunda=item["segunda"],
                        terca=item["terca"],
                        quarta=item["quarta"],
                        quinta=item["quinta"],
                        sexta=item["sexta"],
                    )
                )
            db.commit()
            print("✅ Cronograma AGOSTO II carregado no banco.")
        else:
            print(f"ℹ️ Cronograma já possui {total} registro(s).")
    except Exception as e:
        db.rollback()
        print(f"❌ Erro ao popular cronograma: {e}")
    finally:
        db.close()


# =====================================================
# CONFIGURAÇÃO API
# =====================================================

app = FastAPI(
    title="Duarte Performance API",
    description="Gestão Operacional Duarte Gestão",
    version="2.6"
)


@app.on_event("startup")
def startup_event():
    criar_admin_inicial()
    popular_cronograma_se_vazio()


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
        "status": "online",
        "sistema": "Duarte Performance API",
        "versao": "2.6"
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
    if usuario.role not in ("Admin", "Gestor"):
        raise HTTPException(
            status_code=403,
            detail="Acesso restrito a usuários Admin ou Gestor.",
        )
    return usuario


def exigir_admin(
    usuario: models.Usuario = Depends(usuario_logado),
) -> models.Usuario:
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
    """Busca toda a escala cadastrada no banco (colunas sempre padronizadas)."""
    dados = db.query(models.CronogramaModel).all()

    # Se vazio, tenta popular na hora
    if not dados:
        popular_cronograma_se_vazio()
        dados = db.query(models.CronogramaModel).all()

    return [
        {
            "id": c.id,
            "Operador": c.operador or "-",
            "Periodo": c.periodo or "-",
            "Segunda": c.segunda or "-",
            "Terça": c.terca or "-",
            "Quarta": c.quarta or "-",
            "Quinta": c.quinta or "-",
            "Sexta": c.sexta or "-",
        }
        for c in dados
    ]


@app.post("/cronograma/")
def criar_ou_atualizar_item_escala(
    payload: dict,
    db: Session = Depends(get_db),
    usuario: models.Usuario = Depends(usuario_logado),
):
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