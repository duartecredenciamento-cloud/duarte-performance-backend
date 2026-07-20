FROM python:3.12-slim

WORKDIR /app

# Copia as dependências de dentro da pasta backend
COPY backend/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o código da pasta backend para o contêiner
COPY backend/ .

# Comando de inicialização
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]