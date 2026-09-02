import os
from datetime import datetime, timedelta, timezone
import bcrypt
from jose import jwt, JWTError

# =====================================================
# CONFIGURAÇÕES JWT
# =====================================================

SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    SECRET_KEY = "DUARTE_PERFORMANCE_DEV_KEY_ALTERAR_EM_PRODUCAO"

ALGORITHM = "HS256"

try:
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("JWT_EXPIRE_MINUTES", "1440"))
except ValueError:
    ACCESS_TOKEN_EXPIRE_MINUTES = 1440


# =====================================================
# HASH DE SENHAS (BCRYPT)
# =====================================================

def obter_hash_senha(senha: str) -> str:
    """
    Cria um hash seguro utilizando bcrypt.
    Garante limite de 72 bytes do bcrypt para evitar exceções.
    """
    if not senha:
        raise ValueError("Senha obrigatória.")

    senha_bytes = senha.encode("utf-8")[:72]
    salt = bcrypt.gensalt()
    hash_senha = bcrypt.hashpw(senha_bytes, salt)

    return hash_senha.decode("utf-8")


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """
    Compara a senha digitada com o hash armazenado no banco.
    Trata espaços em branco soltos, converte o prefixo $2y$ (comum em geradores
    legados/passlib) para $2b$ e evita falhas silenciosas ou crashes do bcrypt.
    """
    if not senha_plana or not senha_hash:
        return False

    try:
        hash_limpo = str(senha_hash).strip()

        # Converte prefixo $2y$ para $2b$ se necessário
        if hash_limpo.startswith("$2y$"):
            hash_limpo = "$2b$" + hash_limpo[4:]

        senha_bytes = senha_plana.encode("utf-8")[:72]
        hash_bytes = hash_limpo.encode("utf-8")

        return bcrypt.checkpw(senha_bytes, hash_bytes)
    except Exception:
        return False


# =====================================================
# CRIAÇÃO DO TOKEN JWT
# =====================================================

def criar_token_acesso(dados_usuario: dict) -> str:
    """
    Cria token JWT de acesso com data de expiração calculada.
    """
    payload = dados_usuario.copy()

    expiracao = datetime.now(timezone.utc) + timedelta(
        minutes=ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload.update({"exp": expiracao})

    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token


# =====================================================
# DECODIFICAÇÃO E VALIDAÇÃO DO TOKEN
# =====================================================

def validar_token(token: str):
    """
    Valida e retorna os dados contidos no JWT.
    Retorna None em caso de token inválido ou expirado.
    """
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload
    except JWTError:
        return None