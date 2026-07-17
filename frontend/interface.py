import streamlit as st
import requests
import pandas as pd
import time
import os
from datetime import datetime

st.set_page_config(page_title="Duarte Performance", page_icon="🟠", layout="wide", initial_sidebar_state="expanded")

API_URL = "https://duarte-performance-backend.onrender.com"


# Sessão
if "token" not in st.session_state: st.session_state.token = None
if "username" not in st.session_state: st.session_state.username = None
if "role" not in st.session_state: st.session_state.role = None

# ===================== CSS EXECUTIVO =====================
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%); font-family: 'Segoe UI', sans-serif; }
    .login-card { background: white; padding: 60px 50px; border-radius: 28px; box-shadow: 0 25px 70px rgba(15,23,42,0.15); max-width: 460px; margin: auto; }
    .kpi-card { background: white; padding: 30px; border-radius: 20px; box-shadow: 0 10px 30px rgba(15,23,42,0.08); border-left: 8px solid #F39200; }
    div[data-baseweb="input"], div[data-baseweb="select"] { background: white !important; border-radius: 12px !important; }
    .stButton>button { border-radius: 12px; font-weight: 700; padding: 12px 24px; }
    .stButton>button[kind="primary"] { background: linear-gradient(90deg, #0F172A, #1E293B); }
    .stButton>button:hover { background: linear-gradient(90deg, #F39200, #E07A00) !important; transform: translateY(-2px); }
</style>
""", unsafe_allow_html=True)

def api_get(endpoint):
    if not st.session_state.token: return type('obj', (), {'status_code': 401, 'json': lambda: {}})()
    try:
        return requests.get(f"{API_URL}{endpoint}", headers={"Authorization": f"Bearer {st.session_state.token}"}, timeout=10)
    except:
        return type('obj', (), {'status_code': 500, 'json': lambda: {}})()

def api_post(endpoint, data=None, files=None):
    if not st.session_state.token: return type('obj', (), {'status_code': 401, 'json': lambda: {}})()
    try:
        return requests.post(f"{API_URL}{endpoint}", data=data, files=files, headers={"Authorization": f"Bearer {st.session_state.token}"}, timeout=15)
    except:
        return type('obj', (), {'status_code': 500, 'json': lambda: {}})()

# ===================== LOGIN =====================
if not st.session_state.token:
    st.markdown("<div style='display:flex;justify-content:center;align-items:center;min-height:90vh'>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;color:#0F172A;font-size:42px;margin-bottom:8px;'>Duarte Performance</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#64748B;font-size:18px;'>Gestão de Rede de Prestadores</p>", unsafe_allow_html=True)
        
        cpf = st.text_input("CPF Corporativo", placeholder="00000000000", key="cpf")
        senha = st.text_input("Senha", type="password", key="senha")
        
        if st.button("🔑 AUTENTICAR", type="primary", use_container_width=True):
            try:
                resp = requests.post(f"{API_URL}/token", data={"username": cpf, "password": senha})
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.username = data.get("nome", "Usuário")
                    st.success("✅ Login realizado com sucesso!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ CPF ou senha inválidos")
            except:
                st.error("❌ Erro de conexão com o backend")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ===================== INTERFACE PRINCIPAL =====================
st.sidebar.success(f"👤 {st.session_state.username.upper()}")
st.sidebar.caption(st.session_state.role)

menu = st.sidebar.radio("Navegação", [
    "🏠 Dashboard Executivo",
    "📝 Lançar Atividade",
    "🗓️ Escala Semanal"
])

if menu == "🏠 Dashboard Executivo":
    st.title("Dashboard Executivo")
    st.markdown("**Visão consolidada da performance operacional**")
    
    resp = api_get("/registros/")
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        if not df.empty:
            c1, c2, c3 = st.columns(3)
            c1.metric("Total Atividades", len(df))
            c2.metric("Pendências", len([x for x in df['status'] if 'Não' in str(x) or 'Parcial' in str(x)]))
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhum registro encontrado ainda.")
    else:
        st.warning("Backend conectado ✓ Aguardando registros...")

elif menu == "📝 Lançar Atividade":
    st.title("Lançamento de Atividade")
    with st.form("lancamento"):
        col1, col2 = st.columns(2)
        cliente = col1.selectbox("Cliente", ["FR FISIO", "EV-CITI", "REGULAÇÃO"])
        status = col2.selectbox("Status", ["Realizado Total", "Realizado Parcial", "Não Realizado"])
        obs = st.text_area("Justificativa / Observações", height=160)
        
        if st.form_submit_button("💾 REGISTRAR ATIVIDADE", type="primary"):
            payload = {"operador_nome": st.session_state.username, "cliente_nome": cliente, "status": status, "justificativa": obs}
            resp = api_post("/registros/", data=payload)
            if resp.status_code in [200, 201]:
                st.success("✅ Atividade registrada com sucesso!")
                st.balloons()
            else:
                st.error("Erro ao registrar atividade")

elif menu == "🗓️ Escala Semanal":
    st.title("Escala de Trabalho Semanal")
    resp = api_get("/cronograma/")
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Carregando escala...")

st.sidebar.button("🚪 Encerrar Sessão", on_click=lambda: st.session_state.clear() or st.rerun())