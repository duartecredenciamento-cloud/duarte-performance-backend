from fastapi import FastAPI, Depends, HTTPException, status, Form, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="Duarte Performance Backend")

# 🌍 LIBERAÇÃO DE CORS (Essencial para o Frontend acessar o Backend no Render)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 👥 BANCO DE DADOS EM MEMÓRIA (Substitua pelos seus dados de produção)
# Configurei seu CPF de teste para você logar de primeira com a senha 123
USUARIOS_DB = {
    "12345678901": {"nome": "Erick Admin", "senha": "123", "role": "Admin Master", "cpf": "12345678901"}
}

CRONOGRAMA_DB = [
    {"id": 1, "operador": "Felipe", "dia_semana": "Segunda", "atividade": "Monitoramento de Rede", "cliente": "FR FISIO", "periodo": "Integral", "data_limite": "20/07/2026", "status_prazo": "No Prazo", "duplicado": False},
    {"id": 2, "operador": "Julia", "dia_semana": "Terça", "atividade": "Alocação de Prestadores", "cliente": "EV-CITI", "periodo": "Integral", "data_limite": "21/07/2026", "status_prazo": "No Prazo", "duplicado": False},
    {"id": 3, "operador": "Lucas", "dia_semana": "Quarta", "atividade": "Alinhamento Operacional", "cliente": "REGULAÇÃO", "periodo": "Integral", "data_limite": "22/07/2026", "status_prazo": "No Prazo", "duplicado": False}
]

REGISTROS_DB = []
AUDITORIA_DB = []

# 🔑 ROTA DE LOGIN FORM-DATA (Bate certinho com o seu Streamlit)
@app.post("/token")
def login(username: str = Form(...), password: str = Form(...)):
    user = USUARIOS_DB.get(username)
    if not user or user["senha"] != password:
        AUDITORIA_DB.append({
            "timestamp": datetime.utcnow().isoformat(),
            "usuario_nome": "Desconhecido",
            "usuario_cpf": username,
            "ip_origem": "Render-Gateway",
            "acao": "LOGIN_FAILED",
            "detalhes": "Tentativa de login inválida"
        })
        raise HTTPException(status_code=401, detail="CPF ou senha incorretos")
    
    AUDITORIA_DB.append({
        "timestamp": datetime.utcnow().isoformat(),
        "usuario_nome": user["nome"],
        "usuario_cpf": user["cpf"],
        "ip_origem": "Render-Gateway",
        "acao": "LOGIN_SUCCESS",
        "detalhes": f"Usuário {user['nome']} logou com sucesso"
    })
    
    return {
        "access_token": "token_sessao_duarte_sucesso",
        "token_type": "bearer",
        "role": user["role"],
        "nome": user["nome"],
        "cpf": user["cpf"]
    }

@app.get("/cronograma/")
def get_cronograma():
    return CRONOGRAMA_DB

@app.get("/registros/")
def get_registros():
    return REGISTROS_DB

@app.post("/registros/")
def create_registro(
    operador_nome: str = Form(...),
    cliente_nome: str = Form(...),
    status: str = Form(...),
    justificativa: str = Form(...),
    evidencia: Optional[UploadFile] = File(None)
):
    novo_reg = {
        "id": len(REGISTROS_DB) + 1,
        "operador_nome": operador_nome,
        "cliente_nome": cliente_nome,
        "status": status,
        "justificativa": justificativa,
        "evidencia_nome": evidencia.filename if evidencia else None
    }
    REGISTROS_DB.append(novo_reg)
    return {"status": "success", "data": novo_reg}

@app.get("/usuarios/")
def get_usuarios():
    return list(USUARIOS_DB.values())

@app.get("/auditoria/")
def get_auditoria():
    return AUDITORIA_DB