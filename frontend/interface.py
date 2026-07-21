import streamlit as st
import pandas as pd
from datetime import datetime
import requests

st.set_page_config(page_title="Duarte Performance", page_icon="🟠", layout="wide")

# ===================== SESSION STATE =====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = ""
if 'role' not in st.session_state:
    st.session_state.role = ""
if 'df_escala' not in st.session_state:
    st.session_state.df_escala = pd.DataFrame(columns=['DATA', 'OPERADOR', 'CLIENTE', 'TURNO'])
if 'df_apontamentos' not in st.session_state:
    st.session_state.df_apontamentos = pd.DataFrame(columns=['ID', 'DATA', 'OPERADOR', 'CLIENTE', 'STATUS', 'OBSERVACAO'])

# ===================== CSS =====================
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #F8FAFC 0%, #EEF2F6 100%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0A1128 0%, #02040A 100%); }
</style>
""", unsafe_allow_html=True)

# ===================== LOGIN =====================
if not st.session_state.logged_in:
    st.title("Duarte Performance")
    st.markdown("### Login do Sistema")
    
    username = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    
    if st.button("Entrar", type="primary"):
        try:
            resp = requests.post(
                "https://duarte-performance-backend.onrender.com/token",
                data={"username": username, "password": senha},
                timeout=10
            )
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.logged_in = True
                st.session_state.user = data.get("nome", username)
                st.session_state.role = data.get("role", "Operador")
                st.success("Login realizado!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
        except:
            st.error("Erro de conexão com o backend. Verifique se o backend está online.")
    st.stop()

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("### Duarte Performance")
    nome = st.session_state.user
    st.markdown(f"**👤 {nome}**")
    st.markdown(f"**💼 {st.session_state.role}**")
    st.divider()
    
    menu = st.radio("Menu", ["Dashboard", "Escala Semanal", "Relatórios", "Lançar Atividade", "Editor"])
    st.session_state.menu = menu

    if st.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

# ===================== ROTEAMENTO =====================
if st.session_state.menu == "Dashboard":
    st.header("📈 Dashboard Gerencial")
    st.info("Dashboard em desenvolvimento")
elif st.session_state.menu == "Escala Semanal":
    st.header("🗓️ Escala Semanal")
    st.info("Escala em desenvolvimento")
elif st.session_state.menu == "Relatórios":
    st.header("📊 Relatórios")
    st.info("Relatórios em desenvolvimento")
elif st.session_state.menu == "Lançar Atividade":
    st.header("📝 Lançar Atividade")
    st.info("Lançamento em desenvolvimento")
elif st.session_state.menu == "Editor":
    st.header("✏️ Editor")
    st.info("Editor em desenvolvimento")