import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import io
import time
from datetime import datetime
import os

st.set_page_config(page_title="Duarte Performance", page_icon="🟠", layout="wide", initial_sidebar_state="expanded")

# ===================== CONFIGURAÇÃO RENDER =====================
API_URL = "https://duarte-performance-backend.onrender.com"

# ===================== ESTADO =====================
if "token" not in st.session_state: st.session_state.token = None
if "username" not in st.session_state: st.session_state.username = None
if "role" not in st.session_state: st.session_state.role = None

# ===================== CSS PREMIUM =====================
st.markdown("""
<style>
    .stApp { background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%); }
    .kpi-card { background: white; padding: 28px; border-radius: 20px; box-shadow: 0 10px 30px rgba(15,23,42,0.08); border-left: 7px solid #F39200; }
    .login-card { background: white; padding: 50px; border-radius: 24px; box-shadow: 0 20px 60px rgba(0,0,0,0.1); }
    div[data-baseweb="input"], div[data-baseweb="select"] { background: white !important; }
    .stButton>button { background: linear-gradient(90deg, #0F172A, #1E293B); color: white; border-radius: 12px; }
    .stButton>button:hover { background: linear-gradient(90deg, #F39200, #E07A00) !important; }
</style>
""", unsafe_allow_html=True)

# ===================== API =====================
def api_get(endpoint):
    if not st.session_state.token: return type('obj', (), {'status_code': 401, 'json': lambda: {}})()
    try:
        return requests.get(f"{API_URL}{endpoint}", headers={"Authorization": f"Bearer {st.session_state.token}"}, timeout=15)
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
        st.markdown("<div class='login-card' style='max-width:450px;'>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;color:#0F172A;font-size:42px;'>Duarte Performance</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#64748B;'>Gestão de Rede de Prestadores</p>", unsafe_allow_html=True)
        
        cpf = st.text_input("CPF Corporativo", placeholder="00000000000")
        senha = st.text_input("Senha", type="password")
        
        if st.button("🔑 ENTRAR", type="primary", use_container_width=True):
            try:
                resp = requests.post(f"{API_URL}/token", data={"username": cpf, "password": senha})
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.token = data["access_token"]
                    st.session_state.username = data.get("nome", "Usuário")
                    st.session_state.role = data.get("role", "Operador")
                    st.success("✅ Login realizado com sucesso!")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("❌ CPF ou senha incorretos")
            except:
                st.error("❌ Erro de conexão com servidor")
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ===================== SIDEBAR =====================
st.sidebar.image("https://via.placeholder.com/200x60/0F172A/F39200?text=DUARTE", use_container_width=True)
st.sidebar.success(f"👤 {st.session_state.username}")
st.sidebar.caption(st.session_state.role)

menu = st.sidebar.radio("Navegação", [
    "🏠 Dashboard Executivo",
    "📝 Lançar Atividade",
    "📅 Prazos & SLA",
    "🗓️ Conograma",
    "🔍 Auditoria/Logs"
])

# ===================== TELAS =====================
if menu == "🏠 Dashboard Executivo":
    st.title("Dashboard Executivo")
    st.markdown("**Visão consolidada da performance da Rede**")
    
    resp = api_get("/registros/")
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        if not df.empty:
            c1,c2,c3,c4 = st.columns(4)
            c1.metric("Total Atividades", len(df))
            c2.metric("Taxa Sucesso", f"{int(len(df[df['status'].str.contains('Realizado', na=False)])/len(df)*100) if len(df)>0 else 0}%")
            c3.metric("Pendências", len(df[~df['status'].str.contains('Realizado', na=False)]))
            st.plotly_chart(px.pie(df, names='status'), use_container_width=True)
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhum registro ainda.")
    else:
        st.warning("Aguardando dados do backend...")

elif menu == "📝 Lançar Atividade":
    st.title("Lançamento de Atividade")
    with st.form("form_lanc"):
        col1, col2 = st.columns(2)
        cliente = col1.selectbox("Cliente", ["FR FISIO", "EV-CITI", "REGULAÇÃO"])
        status = col2.selectbox("Status", ["Realizado Total", "Realizado Parcial", "Não Realizado"])
        obs = st.text_area("Justificativa / Observações", height=150)
        evidencia = st.file_uploader("Evidência", type=["pdf","png","jpg","xlsx"])
        
        if st.form_submit_button("💾 REGISTRAR ATIVIDADE", type="primary"):
            files = {"evidencia": (evidencia.name, evidencia.getvalue(), evidencia.type)} if evidencia else None
            payload = {"operador_nome": st.session_state.username, "cliente_nome": cliente, "status": status, "justificativa": obs}
            resp = api_post("/registros/", data=payload, files=files)
            if resp.status_code == 200:
                st.success("✅ Atividade registrada com sucesso!")
                st.balloons()
            else:
                st.error("Erro ao registrar")

elif menu == "🗓️ Conograma":
    st.title("Conograma")
    resp = api_get("/cronograma/")
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        st.dataframe(df, use_container_width=True)
    else:
        st.info("Carregando escala...")

elif menu == "🔍 Auditoria/Logs":
    if st.session_state.role == "Admin Master":
        st.title("Auditoria do Sistema")
        resp = api_get("/auditoria/")
        if resp.status_code == 200:
            st.dataframe(pd.DataFrame(resp.json()), use_container_width=True)
        else:
            st.info("Nenhum log encontrado")
    else:
        st.error("Acesso restrito")

st.sidebar.button("🚪 Sair", on_click=lambda: st.session_state.clear() or st.rerun())