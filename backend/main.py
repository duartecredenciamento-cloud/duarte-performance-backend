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
    version="2.5"
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
# JWT
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
            algorithms=[
                auth.ALGORITHM
            ]
        )


        username = payload.get(
            "sub"
        )


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
        .filter(
            models.Usuario.username == username
        )
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

        "sistema":
        "Duarte Performance API",

        "versao":"2.5"

    }



# =====================================================
# LOGIN
# =====================================================


@app.post("/token")
def login(

    form_data:
    OAuth2PasswordRequestForm = Depends(),

    db:
    Session = Depends(get_db)

):


    usuario = (

        db.query(models.Usuario)

        .filter(
            models.Usuario.username
            ==
            form_data.username
        )

        .first()

    )



    if not usuario:

        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha inválidos"
        )



    if not auth.verificar_senha(

        form_data.password,

        usuario.password_hash

    ):

        raise HTTPException(
            status_code=401,
            detail="Usuário ou senha inválidos"
        )



    token = auth.criar_token_acesso(

        {

            "sub":
            usuario.username,


            "nome":
            usuario.nome,


            "role":
            usuario.role,


            "id":
            usuario.id

        }

    )


    return {


        "access_token":
        token,


        "token_type":
        "bearer",


        "username":
        usuario.username,


        "nome":
        usuario.nome,


        "role":
        usuario.role

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
# PERFIL DO USUÁRIO
# =====================================================


@app.get("/usuarios/me")
def meu_usuario(

    usuario:
    models.Usuario = Depends(usuario_logado)

):

    return {

        "id":
        usuario.id,

        "username":
        usuario.username,

        "nome":
        usuario.nome,

        "email":
        usuario.email,

        "role":
        usuario.role,

        "perfil_completo":
        usuario.perfil_completo

    }





# =====================================================
# REGISTROS OPERACIONAIS
# =====================================================


@app.post(
    "/registros/",
    response_model=schemas.RegistroOut
)
def criar_registro(

    registro:
    schemas.RegistroCreate,

    db:
    Session = Depends(get_db),

    usuario:
    models.Usuario = Depends(usuario_logado)

):


    novo = models.RegistroModel(

        operador_nome=
        usuario.nome,


        cliente_nome=
        registro.cliente_nome,


        status=
        registro.status,


        justificativa=
        registro.justificativa

    )


    db.add(novo)

    db.commit()

    db.refresh(novo)


    return novo





@app.get(
    "/registros/",
    response_model=list[schemas.RegistroOut]
)
def listar_registros(

    db:
    Session = Depends(get_db),

    usuario:
    models.Usuario = Depends(usuario_logado)

):


    registros = (

        db.query(
            models.RegistroModel
        )

        .order_by(
            models.RegistroModel.data_registro.desc()
        )

        .all()

    )


    return registros





@app.put(
    "/registros/{registro_id}"
)
def atualizar_registro(

    registro_id:int,

    dados:
    schemas.RegistroUpdate,

    db:
    Session = Depends(get_db),

    usuario:
    models.Usuario = Depends(usuario_logado)

):


    registro = (

        db.query(
            models.RegistroModel
        )

        .filter(
            models.RegistroModel.id
            ==
            registro_id
        )

        .first()

    )


    if not registro:

        raise HTTPException(
            404,
            "Registro não encontrado"
        )


    for campo, valor in dados.dict(
        exclude_unset=True
    ).items():

        setattr(
            registro,
            campo,
            valor
        )


    db.commit()


    return {

        "status":
        "Atualizado"

    }





@app.delete(
    "/registros/{registro_id}"
)
def deletar_registro(

    registro_id:int,

    db:
    Session = Depends(get_db),

    usuario:
    models.Usuario = Depends(usuario_logado)

):


    registro = (

        db.query(
            models.RegistroModel
        )

        .filter(
            models.RegistroModel.id
            ==
            registro_id
        )

        .first()

    )


    if not registro:

        raise HTTPException(
            404,
            "Registro não encontrado"
        )


    db.delete(registro)

    db.commit()


    return {

        "status":
        "Excluído"

    }





# =====================================================
# CRONOGRAMA
# =====================================================


@app.get(
    "/cronograma/"
)
def listar_cronograma(

    db:
    Session = Depends(get_db),

    usuario:
    models.Usuario = Depends(usuario_logado)

):


    dados = (

        db.query(
            models.CronogramaModel
        )

        .all()

    )


    return dados