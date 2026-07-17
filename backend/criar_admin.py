from database import SessionLocal
import models
import auth

db = SessionLocal()

# CPF e Senha do Admin Master
cpf_admin = "00000000000"   # Altere se quiser
senha = "Duarte123#"        # Senha que você vai usar para logar

# Verifica se já existe
if not db.query(models.UserModel).filter(models.UserModel.cpf == cpf_admin).first():
    usuario = models.UserModel(
        cpf=cpf_admin,
        nome="Administrador Geral",
        password_hash=auth.obter_hash_senha(senha),
        role="Admin Master"
    )
    db.add(usuario)
    db.commit()
    print(f"✅ Admin criado com sucesso!\nCPF: {cpf_admin}\nSenha: {senha}")
else:
    print("Usuário admin já existe.")