"""
Script de inicialização: cria/atualiza o Admin Master padrão.
Roda automaticamente antes do uvicorn subir (veja o Start Command no Render:
"python criar_admin.py && uvicorn main:app ..."), então toda vez que o backend
reinicia, esse script garante que o admin existe com a senha certa.
"""
import database
import models
import auth

db = next(database.get_db())

# Departamento base
depto_cred = db.query(models.DepartamentoModel).filter(models.DepartamentoModel.nome == "Credenciamento").first()
if not depto_cred:
    depto_cred = models.DepartamentoModel(nome="Credenciamento")
    db.add(depto_cred)
    db.commit()
    db.refresh(depto_cred)

ADMIN_USERNAME = "admin"
ADMIN_SENHA = "Duarte1234#"

try:
    admin_existente = db.query(models.Usuario).filter(models.Usuario.username == ADMIN_USERNAME).first()

    if admin_existente:
        print("Admin Master já existe. Atualizando a senha por garantia...")
        admin_existente.password_hash = auth.obter_hash_senha(ADMIN_SENHA)
        admin_existente.role = "Admin Master"
        admin_existente.perfil_completo = True
    else:
        print("Criando o Admin Master inicial...")
        novo_admin = models.Usuario(
            username=ADMIN_USERNAME,
            password_hash=auth.obter_hash_senha(ADMIN_SENHA),
            nome="Admin Master",
            role="Admin Master",
            perfil_completo=True,
            departamento_id=depto_cred.id
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