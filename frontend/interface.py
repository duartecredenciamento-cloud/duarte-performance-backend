import streamlit as st
import requests
import pandas as pd
import io
import time
from datetime import datetime
import os

st.set_page_config(page_title="Duarte Performance", page_icon="🟠", layout="wide")

# ================== CONFIGURAÇÃO RENDER ==================
API_URL = os.getenv("API_URL", "https://duarte-performance-backend.onrender.com")

# Estado
if "token" not in st.session_state:
    st.session_state.token = None
if "username" not in st.session_state:
    st.session_state.username = None
if "role" not in st.session_state:
    st.session_state.role = None

# CSS Simples
st.markdown("""
<style>
    .stApp { background: #F8FAFC; }
    .kpi-card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); }
</style>
""", unsafe_allow_html=True)

# API Helpers
def api_get(endpoint):
    if not st.session_state.token:
        return type('obj', (), {'status_code': 401, 'json': lambda: {}})()
    try:
        return requests.get(f"{API_URL}{endpoint}", 
                          headers={"Authorization": f"Bearer {st.session_state.token}"}, timeout=10)
    except:
        return type('obj', (), {'status_code': 500, 'json': lambda: {}})()

# LOGIN
if not st.session_state.token:
    st.title("Duarte Performance")
    cpf = st.text_input("CPF")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar", type="primary"):
        try:
            resp = requests.post(f"{API_URL}/token", 
                               data={"username": cpf, "password": senha})
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.token = data["access_token"]
                st.session_state.username = data.get("nome", "Usuário")
                st.success("Login OK!")
                st.rerun()
            else:
                st.error("Credenciais inválidas")
        except:
            st.error("Erro de conexão com backend")
    st.stop()

# Sidebar
st.sidebar.success(f"👤 {st.session_state.username}")
menu = st.sidebar.radio("Menu", ["Dashboard", "Lançar Atividade", "Escala Semanal"])

if menu == "Dashboard":
    st.title("Dashboard Executivo")
    resp = api_get("/registros/")
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        st.dataframe(df, use_container_width=True)
    else:
        st.warning("Backend não respondeu ainda. Aguarde o deploy finalizar.")

elif menu == "Lançar Atividade":
    st.title("Lançar Atividade")
    st.info("Funcionalidade em construção - backend em integração")

else:
    st.title("Escala Semanal")
    st.info("Em desenvolvimento")

st.sidebar.button("Sair", on_click=lambda: st.session_state.clear() or st.rerun())