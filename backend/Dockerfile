FROM python:3.12-slim

WORKDIR /app

# Copia e instala as dependências primeiro para aproveitar o cache do Docker
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia o restante do código do backend
COPY . .

# Comando para rodar a aplicação usando a porta dinâmica do Render
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT:-10000}"]