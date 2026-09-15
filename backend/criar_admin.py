"""
Script de inicialização: cria/atualiza o Admin Master padrão.
Garante que o administrador exista no banco de dados com os atributos corretos.
"""
import database
import models
import auth

db = next(database.get_db())

ADMIN_USERNAME = "admin@duarte.com"
ADMIN_SENHA = "123456"

try:
    admin_existente = (
        db.query(models.Usuario)
        .filter(models.Usuario.username == ADMIN_USERNAME)
        .first()
    )

    if admin_existente:
        print("Admin Master já existe. Atualizando credenciais...")
        admin_existente.password_hash = auth.obter_hash_senha(ADMIN_SENHA)
        admin_existente.role = "Admin"
    else:
        print("Criando o Admin Master inicial...")
        novo_admin = models.Usuario(
            username=ADMIN_USERNAME,
            password_hash=auth.obter_hash_senha(ADMIN_SENHA),
            role="Admin",
            nome="Admin Master",
            email="admin@duarte.com"
        )
        db.add(novo_admin)

    db.commit()
    print("=" * 50)
    print("  ADMIN MASTER PRONTO!")
    print(f"  usuário: {ADMIN_USERNAME} | senha: {ADMIN_SENHA}")
    print("=" * 50)

except Exception as e:
    db.rollback()
    print(f"❌ Erro ao criar/atualizar o Admin Master: {e}")

finally:
    db.close()