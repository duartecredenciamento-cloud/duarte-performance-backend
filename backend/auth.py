import os

from datetime import datetime, timedelta, timezone

import bcrypt

from jose import jwt, JWTError



# =====================================================
# CONFIGURAÇÕES JWT
# =====================================================

SECRET_KEY = os.getenv(
    "SECRET_KEY"
)


if not SECRET_KEY:
    SECRET_KEY = (
        "DUARTE_PERFORMANCE_DEV_KEY_"
        "ALTERAR_EM_PRODUCAO"
    )



ALGORITHM = "HS256"


ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.getenv(
        "JWT_EXPIRE_MINUTES",
        "1440"
    )
)



# =====================================================
# HASH DE SENHAS
# =====================================================


def obter_hash_senha(
    senha: str
) -> str:

    """
    Cria hash seguro utilizando bcrypt.
    """

    if not senha:

        raise ValueError(
            "Senha obrigatória."
        )


    senha_bytes = (
        senha
        .encode("utf-8")
        [:72]
    )


    salt = bcrypt.gensalt()


    hash_senha = bcrypt.hashpw(
        senha_bytes,
        salt
    )


    return hash_senha.decode(
        "utf-8"
    )



def verificar_senha(
    senha_plana: str,
    senha_hash: str
) -> bool:

    """
    Compara senha digitada
    com hash armazenado.
    """

    if not senha_plana or not senha_hash:

        return False


    try:

        senha_bytes = (
            senha_plana
            .encode("utf-8")
            [:72]
        )


        hash_bytes = (
            senha_hash
            .encode("utf-8")
        )


        return bcrypt.checkpw(
            senha_bytes,
            hash_bytes
        )


    except Exception:

        return False



# =====================================================
# CRIAÇÃO DO TOKEN JWT
# =====================================================


def criar_token_acesso(
    dados_usuario: dict
) -> str:

    """
    Cria token JWT.

    Campos recomendados:
    
    sub   -> login do usuário
    nome  -> nome exibido
    role  -> permissão
    """

    payload = dados_usuario.copy()


    expiracao = (
        datetime.now(timezone.utc)
        +
        timedelta(
            minutes=
            ACCESS_TOKEN_EXPIRE_MINUTES
        )
    )


    payload.update(
        {
            "exp": expiracao
        }
    )


    token = jwt.encode(
        payload,
        SECRET_KEY,
        algorithm=ALGORITHM
    )


    return token



# =====================================================
# DECODIFICAÇÃO DO TOKEN
# =====================================================


def validar_token(
    token: str
):

    """
    Valida e retorna dados
    existentes no JWT.
    """

    try:

        payload = jwt.decode(
            token,
            SECRET_KEY,
            algorithms=[
                ALGORITHM
            ]
        )


        return payload


    except JWTError:

        return None