import streamlit as st
import pandas as pd
from datetime import datetime
import requests

# ===================== CONFIGURAÇÃO =====================
st.set_page_config(page_title="Duarte Performance", page_icon="🟠", layout="wide", initial_sidebar_state="expanded")

# ===================== SESSION STATE =====================
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'user' not in st.session_state:
    st.session_state.user = ""
if 'role' not in st.session_state:
    st.session_state.role = ""
if 'equipe' not in st.session_state:
    st.session_state.equipe = ["Abraão da Silva Santos", "Cristiane Aparecida Duarte", "Bethania Duarte"]
if 'df_escala' not in st.session_state:
    st.session_state.df_escala = pd.DataFrame(columns=['DATA', 'OPERADOR', 'CLIENTE', 'TURNO'])
if 'df_apontamentos' not in st.session_state:
    st.session_state.df_apontamentos = pd.DataFrame(columns=['ID', 'DATA', 'OPERADOR', 'CLIENTE', 'STATUS', 'OBSERVACAO'])
if 'menu' not in st.session_state:
    st.session_state.menu = "Dashboard"

# ===================== CSS PREMIUM =====================
st.markdown("""
<style>
    .stApp { background: linear-gradient(135deg, #F8FAFC 0%, #EEF2F6 100%); }
    [data-testid="stSidebar"] { background: linear-gradient(180deg, #0A1128 0%, #02040A 100%); border-right: 5px solid #F26419; }
    .stButton>button[kind="primary"] { background: linear-gradient(90deg, #0F172A, #1E293B); }
    .stButton>button:hover { background: linear-gradient(90deg, #F26419, #d95615) !important; }
</style>
""", unsafe_allow_html=True)

# ===================== FUNÇÕES DE PÁGINAS =====================
def aba_dashboard():
    st.header("📈 Dashboard Gerencial")
    df = st.session_state.df_apontamentos
    if df.empty:
        st.warning("Sem dados ainda.")
        return
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total", len(df))
    c2.metric("Realizado Total", (df['STATUS'] == 'Realizado Total').sum())
    c3.metric("Realizado Parcial", (df['STATUS'] == 'Realizado Parcial').sum())
    c4.metric("Não Realizado", (df['STATUS'] == 'Não Realizado').sum())
    st.bar_chart(df['STATUS'].value_counts())

def aba_escala():
    st.header("🗓️ Escala Semanal")
    if st.session_state.df_escala.empty:
        st.info("Nenhuma escala importada.")
    else:
        st.dataframe(st.session_state.df_escala, use_container_width=True)

def aba_relatorios():
    st.header("📊 Relatórios")
    df = st.session_state.df_apontamentos
    if df.empty:
        st.warning("Sem dados.")
        return
    st.dataframe(df, use_container_width=True)

def aba_lancar():
    st.header("📝 Lançar Execução Diária")
    st.info("Funcionalidade em desenvolvimento")

def aba_editor():
    st.header("✏️ Editor de Apontamentos")
    st.info("Funcionalidade em desenvolvimento")

# ===================== LOGIN =====================
if not st.session_state.logged_in:
    st.title("Duarte Performance")
    username = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")
    if st.button("Entrar", type="primary"):
        try:
            resp = requests.post("https://duarte-performance-backend.onrender.com/token", data={"username": username, "password": senha})
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.logged_in = True
                st.session_state.user = data.get("nome", username)
                st.session_state.role = data.get("role", "Operador")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
        except:
            st.error("Erro de conexão")
    st.stop()

# ===================== SIDEBAR =====================
with st.sidebar:
    st.markdown("### Duarte Performance")
    nome = st.session_state.user
    partes = nome.split()
    iniciais = (partes[0][0] + partes[-1][0]).upper() if len(partes) >= 2 else nome[:2].upper()
    
    st.markdown(f"""
    <div style="text-align:center; margin:20px 0;">
        <div style="background: linear-gradient(#F26419,#d95615); color:white; width:70px;height:70px;border-radius:50%; 
                    display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:900;margin:auto;">
            {iniciais}
        </div>
        <strong>{nome}</strong><br>
        <small>{st.session_state.role}</small>
    </div>
    """, unsafe_allow_html=True)
    
    menu = st.radio("Menu", ["Dashboard", "Escala Semanal", "Relatórios", "Lançar Atividade", "Editor"])
    st.session_state.menu = menu

    if st.button("Sair"):
        st.session_state.logged_in = False
        st.rerun()

# ===================== ROTEAMENTO =====================
if st.session_state.menu == "Dashboard":
    aba_dashboard()
elif st.session_state.menu == "Escala Semanal":
    aba_escala()
elif st.session_state.menu == "Relatórios":
    aba_relatorios()
elif st.session_state.menu == "Lançar Atividade":
    aba_lancar()
elif st.session_state.menu == "Editor":
    aba_editor()