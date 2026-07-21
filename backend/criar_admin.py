from database import SessionLocal, engine
from models import Base, Usuario
from auth import obter_hash_senha

def resetar_ou_criar_admin():
    # Garante que as tabelas existem
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    
    try:
        # Gera o hash da senha usando bcrypt nativo
        nova_hash = obter_hash_senha("Duarte1234#")
        
        # Busca o admin pelo username
        admin = db.query(Usuario).filter(Usuario.username == "admin").first()

        if admin:
            print(">>> Usuário 'admin' encontrado! Atualizando hash da senha no banco...")
            admin.password_hash = nova_hash  # <-- Atualiza na coluna correta
            db.commit()
            print(">>> SENHA DO ADMIN ATUALIZADA COM SUCESSO PARA 'Duarte1234#'!")
        else:
            print(">>> Admin não encontrado. Criando novo usuário 'admin'...")
            novo_admin = Usuario(
                username="admin",
                password_hash=nova_hash,  # <-- Salva na coluna correta
                nome="Admin Master",
                role="admin",
                perfil_completo=True
            )
            db.add(novo_admin)
            db.commit()
            print(">>> ADMIN CRIADO COM SUCESSO!")

    except Exception as e:
        print(f"❌ Erro ao atualizar admin: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    resetar_ou_criar_admin()