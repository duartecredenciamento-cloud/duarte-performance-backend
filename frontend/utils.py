import pandas as pd
from datetime import datetime
import streamlit as st

# --- LÓGICA DE ESCALA E VALIDAÇÃO ---

def validar_escala(df_escala):
    """
    Analisa a planilha de escala importada buscando duplicidades e conflitos.
    Espera colunas: 'Data', 'Operador', 'Cliente'.
    """
    erros = []
    
    # Padroniza nomes das colunas para evitar erros de case (maiúscula/minúscula)
    df_escala.columns = [col.strip().upper() for col in df_escala.columns]
    colunas_obrigatorias = ['DATA', 'OPERADOR', 'CLIENTE']
    
    for col in colunas_obrigatorias:
        if col not in df_escala.columns:
            return False, f"Erro: A coluna obrigatória '{col}' não foi encontrada na planilha."

    # Verifica duplicidades: Mesmo operador, mesmo cliente, mesma data
    duplicadas = df_escala[df_escala.duplicated(subset=['DATA', 'OPERADOR', 'CLIENTE'], keep=False)]
    if not duplicadas.empty:
        erros.append("Foram encontradas alocações duplicadas para o mesmo Operador/Cliente no mesmo dia.")
        
    # Verifica limite operacional (Exemplo: Operador com mais de 10 clientes no dia)
    contagem_diaria = df_escala.groupby(['DATA', 'OPERADOR']).size()
    conflitos_sobrecarga = contagem_diaria[contagem_diaria > 10]
    if not conflitos_sobrecarga.empty:
        erros.append("Aviso: Existem operadores alocados em mais de 10 clientes no mesmo dia.")

    if erros:
        return False, erros
    
    return True, "Escala validada com sucesso! Sem conflitos."

def obter_clientes_do_dia(df_escala, operador, data_atual):
    """
    Filtra os clientes de um operador específico para a data atual.
    """
    if df_escala.empty:
        return []
    
    # Lógica de filtro reativa e segura
    mascara = (
        (df_escala['OPERADOR'].str.lower() == operador.lower()) & 
        (pd.to_datetime(df_escala['DATA']).dt.date == pd.to_datetime(data_atual).date())
    )
    clientes_alocados = df_escala[mascara]['CLIENTE'].unique().tolist()
    return clientes_alocados

# --- LÓGICA DE AUDITORIA E STATUS ---

def registrar_auditoria(acao, usuario, detalhes):
    """
    Simula o registro de logs no banco de dados (Auditoria).
    """
    log = {
        "Data_Hora": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "Usuario": usuario,
        "Acao": acao,
        "Detalhes": detalhes
    }
    # Em produção, aqui vai o insert no banco (SQLAlchemy/PostgreSQL)
    if 'auditoria_logs' not in st.session_state:
        st.session_state['auditoria_logs'] = []
    st.session_state['auditoria_logs'].append(log)

def processar_fechamento_diario(df_escala, df_apontamentos, data_alvo):
    """
    Rotina (Auto-Status): Verifica na escala quem não lançou tarefa e gera 'Não Informado'.
    """
    # Lógica simplificada de batimento
    # Se o par (Data, Cliente, Operador) está na escala mas não nos apontamentos -> 'Não Informado'
    pass # Implementar batimento em DF aqui quando o DB estiver conectado