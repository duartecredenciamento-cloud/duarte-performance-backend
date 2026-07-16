import os
from jose import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext

# IMPORTANTE: a chave antiga estava fixa no código e já foi parar no GitHub —
# considere ela comprometida. Gere uma nova e configure só como variável de
# ambiente (nunca commitar de novo). Em desenvolvimento local, cai numa chave
# de fallback só pra não quebrar o `uvicorn --reload` na sua máquina.
SECRET_KEY = os.environ.get("SECRET_KEY", "apenas-para-desenvolvimento-local-troque-em-producao")
ALGORITHM = "HS256"

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verificar_senha(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def obter_hash_senha(password: str) -> str:
    return pwd_context.hash(password)

def criar_token_acesso(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=480)  # 8 horas de expediente
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt