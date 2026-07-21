import bcrypt

def obter_hash_senha(senha: str) -> str:
    # Converte a senha para bytes e gera o hash com bcrypt nativo
    senha_bytes = senha.encode('utf-8')
    salt = bcrypt.gensalt()
    hash_bytes = bcrypt.hashpw(senha_bytes, salt)
    return hash_bytes.decode('utf-8')

def verificar_senha(senha_plana: str, senha_hash: str) -> bool:
    # Compara a senha digitada com a hash do banco
    senha_bytes = senha_plana.encode('utf-8')
    hash_bytes = senha_hash.encode('utf-8')
    return bcrypt.checkpw(senha_bytes, hash_bytes)