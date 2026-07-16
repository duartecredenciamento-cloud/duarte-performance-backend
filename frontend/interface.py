import streamlit as st
import requests
import pandas as pd
import io
import time
from datetime import datetime
import os

st.set_page_config(page_title="Duarte Performance", page_icon="🟠", layout="wide", initial_sidebar_state="expanded")

API_URL = "https://duarte-performance-backend.onrender.com"

if "token" not in st.session_state: st.session_state.token = None
if "username" not in st.session_state: st.session_state.username = None
if "role" not in st.session_state: st.session_state.role = None

# CSS Premium
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%); }
    .kpi-card { background: white; padding: 28px; border-radius: 20px; box-shadow: 0 10px 30px rgba(15,23,42,0.08); border-left: 7px solid #F39200; }
    .login-card { background: white; padding: 48px; border-radius: 28px; box-shadow: 0 25px 60px rgba(0,0,0,0.1); }
    .stButton>button { border-radius: 12px; font-weight: 700; }
    .stButton>button[kind="primary"] { background: linear-gradient(90deg, #0F172A, #1E293B); }
    .stButton>button:hover { background: linear-gradient(90deg, #F39200, #E07A00) !important; }
</style>
""", unsafe_allow_html=True)

def api_get(endpoint):
    if not st.session_state.token: return type('obj', (), {'status_code': 401, 'json': lambda: {}})()
    try:
        return requests.get(f"{API_URL}{endpoint}", headers={"Authorization": f"Bearer {st.session_state.token}"}, timeout=12)
    except:
        return type('obj', (), {'status_code': 500, 'json': lambda: {}})()

def api_post(endpoint, data=None, files=None):
    if not st.session_state.token: return type('obj', (), {'status_code': 401, 'json': lambda: {}})()
    try:
        return requests.post(f"{API_URL}{endpoint}", data=data, files=files, headers={"Authorization": f"Bearer {st.session_state.token}"}, timeout=15)
    except:
        return type('obj', (), {'status_code': 500, 'json': lambda: {}})()

# LOGIN
if not st.session_state.token:
    st.markdown("<div style='display:flex;justify-content:center;align-items:center;min-height:90vh'>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='login-card' style='max-width:480px;margin:auto;'>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;color:#0F172A;'>Duarte Performance</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#64748B;'>Gestão de Rede de Prestadores</p>", unsafe_allow_html=True)
        
        cpf = st.text_input("CPF Corporativo", placeholder="00000000000")
        senha = st.text_input("Senha", type="password")
        
        if st.button("🔑 AUTENTICAR", type="primary", use_container_width=True):
            try:
                resp = requests.post(f"{API_URL}/token", data={"username": cpf, "password": senha})
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.username = data.get("nome", "Usuário")
                    st.success("✅ Login realizado!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ CPF ou senha inválidos")
            except:
                st.error("❌ Erro de conexão")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# Sidebar
st.sidebar.success(f"👤 {st.session_state.username}")
st.sidebar.caption(st.session_state.role)

menu = st.sidebar.radio("Navegação", ["🏠 Dashboard", "📝 Lançar Atividade", "🗓️ Escala Semanal"])

if menu == "🏠 Dashboard":
    st.title("Dashboard Executivo")
    resp = api_get("/registros/")
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Sistema conectado. Nenhum registro ainda.")

elif menu == "📝 Lançar Atividade":
    st.title("Lançamento de Atividade")
    with st.form("form"):
        cliente = st.selectbox("Cliente", ["FR FISIO", "EV-CITI", "REGULAÇÃO"])
        status = st.selectbox("Status", ["Realizado Total", "Realizado Parcial", "Não Realizado"])
        obs = st.text_area("Observações", height=150)
        if st.form_submit_button("Registrar", type="primary"):
            st.success("Registrado com sucesso!")

elif menu == "🗓️ Escala Semanal":
    st.title("Escala Semanal")
    resp = api_get("/cronograma/")
    if resp.status_code == 200:
        st.dataframe(pd.DataFrame(resp.json()), use_container_width=True)
    else:
        st.info("Carregando...")

st.sidebar.button("Sair", on_click=lambda: st.session_state.clear() or st.rerun())