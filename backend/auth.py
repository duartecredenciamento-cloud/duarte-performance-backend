import os
from datetime import datetime, timedelta
import bcrypt
from jose import jwt

# -----------------------------------------------------------------------------
# Configurações de Segurança e JWT
# -----------------------------------------------------------------------------
# Busca a chave nas variáveis do Render; se não encontrar, usa a chave de backup.
SECRET_KEY = os.getenv("SECRET_KEY", "duarte_chave_secreta_2026_super_segura")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # Expira em 24 horas

# -----------------------------------------------------------------------------
# Funções de Criptografia de Senha (bcrypt nativo)
# -----------------------------------------------------------------------------
def obter_hash_senha(senha: str) -> str:
    """
    Gera o hash da senha utilizando bcrypt.
    Trunca a senha em 72 bytes para prevenir erros de limitação do bcrypt.
    """
    if not senha:
        raise ValueError("A senha não pode estar vazia.")
    
    senha_bytes = senha.encode('utf-8')[:72]
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(senha_bytes, salt).decode('utf-8')


def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    """
    Verifica se a senha digitada corresponde ao hash gravado no banco de dados.
    """
    if not senha_plana or not senha_hash:
        return False
    try:
        senha_bytes = senha_plana.encode('utf-8')[:72]
        hash_bytes = senha_hash.encode('utf-8')
        return bcrypt.checkpw(senha_bytes, hash_bytes)
    except Exception:
        return False

# -----------------------------------------------------------------------------
# Geração de Tokens JWT
# -----------------------------------------------------------------------------
def criar_token_acesso(data: dict) -> str:
    """
    Gera o token JWT assinado para autenticação nas rotas protegidas.
    """
    to_encode = data.copy()
    expiracao = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expiracao})
    
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)