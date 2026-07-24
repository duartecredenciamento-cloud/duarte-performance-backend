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

from jose import JWTError, jwt

import models
import schemas
import auth

from database import (
    get_db,
    engine
)


# =====================================================
# CRIAÇÃO DAS TABELAS
# =====================================================

models.Base.metadata.create_all(
    bind=engine
)


# =====================================================
# CONFIGURAÇÃO API
# =====================================================

app = FastAPI(
    title="Duarte Performance API",
    description="Gestão Operacional Duarte Gestão",
    version="2.5"
)


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