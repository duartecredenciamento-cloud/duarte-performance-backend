from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import os

app = FastAPI(title="Duarte Performance Backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def root():
    return {"status": "online", "message": "Backend Duarte Performance rodando"}

@app.get("/token")
def fake_token():
    return {"access_token": "fake-jwt-token", "token_type": "bearer", "nome": "Admin", "role": "Admin Master"}

@app.get("/registros/")
def registros():
    return [{"id": 1, "operador_nome": "Teste", "cliente_nome": "FR FISIO", "status": "Realizado Total"}]

@app.get("/cronograma/")
def cronograma():
    return [{"id": 1, "operador": "Karine", "dia_semana": "Segunda", "cliente": "FR FISIO"}]

if __name__ == "__main__":
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)