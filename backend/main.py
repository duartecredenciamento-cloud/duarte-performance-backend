from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os
from database import SessionLocal
import models
import auth

app = FastAPI(title="Duarte Performance Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ===================== CRIA ADMIN AUTOMATICAMENTE =====================
def criar_admin_padrao():
    db = SessionLocal()
    cpf = "00000000000"
    senha = "Duarte123#"
    
    if not db.query(models.UserModel).filter(models.UserModel.cpf == cpf).first():
        user = models.UserModel(
            cpf=cpf,
            nome="Administrador Geral",
            password_hash=auth.obter_hash_senha(senha),
            role="Admin Master"
        )
        db.add(user)
        db.commit()
        print("✅ ADMIN MASTER CRIADO AUTOMATICAMENTE!")
    else:
        print("✅ Admin já existe.")
    db.close()

# Executa na inicialização
criar_admin_padrao()

@app.get("/")
def root():
    return {"status": "online", "admin": "00000000000 / Duarte123#"}

@app.get("/token")
def fake_token():
    return {"access_token": "fake-token-para-teste", "token_type": "bearer", "nome": "Administrador Geral", "role": "Admin Master"}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)