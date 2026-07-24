import os
import requests
import pandas as pd
import streamlit as st

# URL Base do Backend no Render
BACKEND_URL = os.getenv("BACKEND_URL", "https://duarte-performance-backend.onrender.com")

def get_auth_headers() -> dict:
    """
    Recupera o Token JWT salvo no session_state e monta o cabeçalho de autenticação.
    """
    token = st.session_state.get("token")
    if token:
        return {"Authorization": f"Bearer {token}"}
    return {}

def check_backend_status() -> bool:
    """Verifica se a API do Backend está online."""
    try:
        response = requests.get(f"{BACKEND_URL}/", timeout=5)
        return response.status_code == 200
    except Exception:
        return False

def fetch_data(endpoint: str, params: dict = None):
    """
    Faz requisição GET autenticada para o backend e retorna o JSON.
    """
    url = f"{BACKEND_URL}/{endpoint.lstrip('/')}"
    try:
        response = requests.get(url, params=params, headers=get_auth_headers(), timeout=10)
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
    Faz requisição POST autenticada para o backend.
    """
    url = f"{BACKEND_URL}/{endpoint.lstrip('/')}"
    headers = get_auth_headers()
    try:
        if files:
            # Para upload de arquivos (multipart/form-data), o requests define o Content-Type automaticamente
            response = requests.post(url, data=data, files=files, headers=headers, timeout=15)
        else:
            response = requests.post(url, json=data, headers=headers, timeout=15)

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
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Remove colunas de controle interno
    columns_to_drop = [col for col in ['id', 'created_at'] if col in df.columns]
    return df.drop(columns=columns_to_drop)