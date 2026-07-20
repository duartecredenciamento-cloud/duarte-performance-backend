"""
Script de inicialização: cria o Admin Master padrão (se ainda não existir).
Rode isso 1x, apontando DATABASE_URL pro banco de produção (Render), depois
que o backend já tiver subido pelo menos uma vez (pra tabela já existir).
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

# Clientes base (do documento de requisitos)
clientes_base = ["EV-CITI", "CONVACARE", "IMC", "Hospital Amato", "Clin Coffi", "Trides", "Lab Bruno", "Pro-Exame"]
for c_nome in clientes_base:
    if not db.query(models.ClienteModel).filter(models.ClienteModel.nome == c_nome).first():
        db.add(models.ClienteModel(nome=c_nome))
db.commit()

# --- Admin Master padrão ---
ADMIN_USERNAME = "admin"
ADMIN_SENHA = "Duarte1234#"

admin_existente = db.query(models.UserModel).filter(models.UserModel.username == ADMIN_USERNAME).first()
if admin_existente:
    print("Admin Master já existe. Atualizando a senha só por garantia...")
    admin_existente.password_hash = auth.obter_hash_senha(ADMIN_SENHA)
    admin_existente.role = "Admin Master"
else:
    print("Criando o Admin Master inicial...")
    novo_admin = models.UserModel(
        username=ADMIN_USERNAME,
        nome="Administrador Geral",
        password_hash=auth.obter_hash_senha(ADMIN_SENHA),
        role="Admin Master",
        departamento_id=depto_cred.id,
        perfil_completo=True
    )
    db.add(novo_admin)

# --- Operador de teste ---
OPERADOR_USERNAME = "operador_teste"
OPERADOR_SENHA = "Duarte123"

op_existente = db.query(models.UserModel).filter(models.UserModel.username == OPERADOR_USERNAME).first()
if not op_existente:
    novo_op = models.UserModel(
        username=OPERADOR_USERNAME,
        nome="Aline",
        password_hash=auth.obter_hash_senha(OPERADOR_SENHA),
        role="Operador",
        departamento_id=depto_cred.id,
        perfil_completo=True
    )
    db.add(novo_op)

db.commit()
print("\n" + "=" * 50)
print("  BANCO DE DADOS POPULADO COM SUCESSO!")
print("=" * 50)
print(f"  ADMIN MASTER: usuário: {ADMIN_USERNAME} | senha: {ADMIN_SENHA}")
print(f"  OPERADOR:     usuário: {OPERADOR_USERNAME} | senha: {OPERADOR_SENHA}")
print("=" * 50)