import sqlite3
from datetime import datetime
import os

# --- CONFIGURAÇÕES ---
DB_PATH = "duarte_gestao.db"
DB_TIMEOUT = 20

# --- ESTRUTURA DO BANCO DE DADOS (SQLITE) ---
def inicializar_banco():
    # Conecta ao banco (cria o arquivo se não existir)
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    cursor = conn.cursor()
    
    # Criação das Tabelas
    cursor.execute("""CREATE TABLE IF NOT EXISTS usuarios 
                      (usuario TEXT PRIMARY KEY, senha TEXT, email TEXT, nivel TEXT, 
                       nome_completo TEXT, cpf TEXT, telefone TEXT)""")
                       
    cursor.execute("""CREATE TABLE IF NOT EXISTS reembolsos 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, despesa TEXT, 
                       categoria TEXT, c_custo TEXT, valor REAL, status TEXT, data DATE, caminho_arquivo TEXT)""")
                       
    cursor.execute("""CREATE TABLE IF NOT EXISTS logs 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario_acao TEXT, acao TEXT, data_hora DATETIME)""")
                     
    cursor.execute("""CREATE TABLE IF NOT EXISTS notificacoes 
                      (id INTEGER PRIMARY KEY AUTOINCREMENT, usuario TEXT, mensagem TEXT, 
                       lida INTEGER, data_hora TEXT)""")
    
    # Inserção de Usuários Padrão
    adms = [
        ('admin', 'Duarte1234#', 'financeiro.duartegestao@gmail.com', 'admin', 'ADMINISTRADOR PRINCIPAL', '000.000.000-00', '(00) 00000-0000'),
        ('operacional', 'Duarte1234#', 'financeiro.duartegestao@gmail.com', 'admin', 'OPERACIONAL ADMINISTRATIVO', '000.000.000-00', '(00) 00000-0000'),
        ('financeiro', 'Duarte1234#', 'financeiro.duartegestao@gmail.com', 'admin', 'FINANCEIRO DIRETORIA', '000.000.000-00', '(00) 00000-0000')
    ]
    
    for u in adms: 
        cursor.execute("INSERT OR REPLACE INTO usuarios VALUES (?,?,?,?,?,?,?)", u)
    
    conn.commit()
    conn.close()
    print("✅ Banco inicializado com sucesso!")

# --- FUNÇÃO DE LOG ---
def registrar_log(user, acao):
    conn = sqlite3.connect(DB_PATH, timeout=DB_TIMEOUT)
    cursor = conn.cursor()
    cursor.execute("INSERT INTO logs (usuario_acao, acao, data_hora) VALUES (?,?,?)", 
                   (user, acao, datetime.now()))
    conn.commit()
    conn.close()

# Executa ao rodar o arquivo
if __name__ == "__main__":
    inicializar_banco()