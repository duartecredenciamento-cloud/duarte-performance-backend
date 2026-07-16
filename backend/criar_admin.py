import database
import models
import auth

# Conecta ao banco real PostgreSQL
db = next(database.get_db())

# Criação automática de Departamentos base para a Duarte Gestão
depto_cred = db.query(models.DepartamentoModel).filter(models.DepartamentoModel.nome == "Credenciamento").first()
if not depto_cred:
    depto_cred = models.DepartamentoModel(nome="Credenciamento")
    db.add(depto_cred)
    db.commit()
    db.refresh(depto_cred)

# Cadastrando os Clientes Corporativos do documento de requisitos
clientes_base = ["EV-CITI", "CONVACARE", "IMC", "Hospital Amato", "Clin Coffi", "Trides", "Lab Bruno", "Pro-Exame"]
for c_nome in clientes_base:
    exists = db.query(models.ClienteModel).filter(models.ClienteModel.nome == c_nome).first()
    if not exists:
        db.add(models.ClienteModel(nome=c_nome))
db.commit()

# Verifica se o administrador pelo CPF já existe (Usaremos um CPF fictício para o teste admin)
admin_cpf = "00000000000"
user_admin = db.query(models.UserModel).filter(models.UserModel.cpf == admin_cpf).first()

senha_hasheada = auth.obter_hash_senha("Duarte1234#")

if user_admin:
    print("Administrador encontrado. Atualizando credenciais...")
    user_admin.password_hash = senha_hasheada
    user_admin.role = "Admin Master"
else:
    print("Instanciando Admin Master inicial...")
    novo_admin = models.UserModel(
        cpf=admin_cpf,
        nome="Administrador Geral",
        password_hash=senha_hasheada,
        role="Admin Master",
        departamento_id=depto_cred.id
    )
    db.add(novo_admin)

# Cadastra o operador inicial para testes de login
operador_cpf = "11111111111"
user_op = db.query(models.UserModel).filter(models.UserModel.cpf == operador_cpf).first()
if not user_op:
    novo_op = models.UserModel(
        cpf=operador_cpf,
        nome="Aline",
        password_hash=auth.obter_hash_senha("Duarte123"),
        role="Operador",
        departamento_id=depto_cred.id
    )
    db.add(novo_op)

db.commit()
print("\n" + "="*50)
print("  BANCO DE DADOS POPULADO COM SUCESSO!")
print("="*50)
print(f"  ADMIN MASTER: CPF: 000.000.000-00 | Senha: Duarte1234#")
print(f"  OPERADOR:     CPF: 111.111.111-11 | Senha: Duarte123")
print("="*50)