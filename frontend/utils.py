# Funções utilitárias do Frontend
import os
import requests
import pandas as pd
import streamlit as st

# URL Base do Backend no Render (Ajuste se o endpoint do backend for outro)
BACKEND_URL = os.getenv("BACKEND_URL", "https://duarte-performance-backend.onrender.com")

def check_backend_status():
    """Verifica se a API do Backend está online."""
    try:
        response = requests.get(f"{BACKEND_URL}/docs", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def fetch_data(endpoint: str, params: dict = None):
    """
    Faz requisição GET para o backend e retorna os dados em JSON ou None se falhar.
    """
    url = f"{BACKEND_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.get(url, params=params, timeout=10)
        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"Erro ao buscar dados ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro de conexão com o backend: {e}")
        return None

def post_data(endpoint: str, data: dict = None, files: dict = None):
    """
    Faz requisição POST para o backend.
    """
    url = f"{BACKEND_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.post(url, json=data, files=files, timeout=15)
        if response.status_code in [200, 201]:
            return response.json()
        else:
            st.error(f"Erro ao enviar dados ({response.status_code}): {response.text}")
            return None
    except Exception as e:
        st.error(f"Erro de conexão com o backend: {e}")
        return None

def format_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Limpa e formata DataFrames para exibição visual no Streamlit.
    """
    if df.empty:
        return df
    # Remove colunas desnecessárias se existirem
    columns_to_drop = [col for col in ['id', 'created_at'] if col in df.columns]
    return df.drop(columns=columns_to_drop)