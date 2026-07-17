import streamlit as st
import requests
import pandas as pd
import time
import os
from datetime import datetime

# --- CONFIGURAÇÃO PREMIUM DA PÁGINA ---
st.set_page_config(
    page_title="Duarte Performance", 
    page_icon="🟠", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

API_URL = "https://duarte-performance-backend.onrender.com"

# --- CONTROLE DA TELA DE CARREGAMENTO (LOADING SCREEN) ---
if "app_loaded" not in st.session_state:
    st.session_state.app_loaded = False

# CSS da Tela de Carregamento Dinâmica
st.markdown("""
<style>
.loader-container {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 80vh;
    font-family: 'Segoe UI', system-ui, sans-serif;
}
.spinner {
    border: 5px solid #E2E8F0;
    border-top: 5px solid #0F172A;
    border-right: 5px solid #F39200;
    border-radius: 50%;
    width: 60px;
    height: 60px;
    animation: spin 1s linear infinite;
    margin-bottom: 25px;
}
@keyframes spin {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}
</style>
""", unsafe_allow_html=True)

if not st.session_state.app_loaded:
    placeholder = st.empty()
    with placeholder.container():
        st.markdown("""
        <div class="loader-container">
            <div class="spinner"></div>
            <h2 style="color: #0F172A; font-weight: 800; margin: 0;">DUARTE PERFORMANCE</h2>
            <p style="color: #64748B; font-size: 14px; margin-top: 5px;">Carregando ambiente seguro de Gestão de Rede...</p>
        </div>
        """, unsafe_allow_html=True)
    time.sleep(1.2)
    st.session_state.app_loaded = True
    placeholder.empty()
    st.rerun()

# --- ESTADOS DE SESSÃO ---
if "token" not in st.session_state: st.session_state.token = None
if "username" not in st.session_state: st.session_state.username = None
if "role" not in st.session_state: st.session_state.role = None
if "cpf" not in st.session_state: st.session_state.cpf = None

# ===================== 🎨 DESIGN EXECUTIVO CLEAN ORIGINAL =====================
st.markdown("""
<style>
    .stApp { 
        background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%); 
        font-family: 'Segoe UI', sans-serif; 
    }
    #MainMenu, header, footer, [data-testid="stHeader"] { visibility: hidden !important; display: none !important; }
    
    /* Login Card */
    .login-card { 
        background: white; 
        padding: 50px 40px; 
        border-radius: 24px; 
        box-shadow: 0 20px 50px rgba(15,23,42,0.08); 
        max-width: 450px; 
        margin: auto; 
        border: 1px solid #E2E8F0;
    }
    
    /* KPIs Executivos */
    .kpi-card { 
        background: white; 
        padding: 25px; 
        border-radius: 16px; 
        box-shadow: 0 8px 25px rgba(15,23,42,0.05); 
        border-left: 6px solid #F39200; 
    }
    
    /* Custom Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0F172A 0%, #1E2937 100%);
        border-right: 4px solid #F39200;
    }
    [data-testid="stSidebar"] * { color: #F1F5F9 !important; }
    
    /* Botões Customizados */
    .stButton>button { 
        border-radius: 10px; 
        font-weight: 700; 
        padding: 10px 22px; 
        transition: all 0.3s ease;
    }
    .stButton>button[kind="primary"] { 
        background: linear-gradient(90deg, #0F172A, #1E293B); 
        color: white !important;
    }
    .stButton>button:hover { 
        background: linear-gradient(90deg, #F39200, #E07A00) !important; 
        color: white !important;
        transform: translateY(-2px); 
        box-shadow: 0 8px 20px rgba(243,146,0,0.3);
    }
    
    /* INPUTS BLINDADOS COM ALTO CONTRASTE (Fundo branco, texto escuro) */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="textarea"] {
        background-color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1.5px solid #CBD5E1 !important;
    }
    .stTextInput input, .stTextArea textarea, input[type="text"], input[type="password"] {
        background-color: #FFFFFF !important;
        color: #1E293B !important;
        -webkit-text-fill-color: #1E293B !important;
        font-weight: 600 !important;
    }
    div[data-baseweb="input"]:focus-within {
        border: 1.5px solid #F39200 !important;
    }
</style>
""", unsafe_allow_html=True)

# ===================== FUNÇÕES DE CONEXÃO REQUISIÇÕES =====================
def api_get(endpoint):
    if not st.session_state.token: 
        return type('obj', (), {'status_code': 401, 'json': lambda: {}})()
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        return requests.get(f"{API_URL}{endpoint}", headers=headers, timeout=10)
    except requests.exceptions.RequestException:
        return type('obj', (), {'status_code': 500, 'json': lambda: {}})()

def api_post(endpoint, data=None, files=None):
    if not st.session_state.token: 
        return type('obj', (), {'status_code': 401, 'json': lambda: {}})()
    try:
        headers = {"Authorization": f"Bearer {st.session_state.token}"}
        return requests.post(f"{API_URL}{endpoint}", data=data, files=files, headers=headers, timeout=15)
    except requests.exceptions.RequestException:
        return type('obj', (), {'status_code': 500, 'json': lambda: {}})()

# ===================== TELA DE AUTENTICAÇÃO =====================
if not st.session_state.token:
    st.markdown("<div style='padding-top: 12vh;'>", unsafe_allow_html=True)
    
    # Flags de controle de fluxo de login para evitar misturar elementos visuais
    login_sucesso = False
    erro_credenciais = False
    erro_conexao = False
    
    with st.container():
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;color:#0F172A;font-size:36px;margin:0;font-weight:800;'>Duarte Performance</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#64748B;font-size:16px;margin-bottom:30px;'>Gestão de Rede de Prestadores</p>", unsafe_allow_html=True)
        
        cpf_input = st.text_input("CPF Corporativo", placeholder="Digite apenas números", key="cpf_input")
        senha_input = st.text_input("Senha", type="password", placeholder="••••••••", key="senha_input")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🔑 AUTENTICAR", type="primary", use_container_width=True):
            cpf_limpo = ''.join(filter(str.isdigit, cpf_input))
            if not cpf_limpo or not senha_input:
                st.warning("⚠️ Preencha os campos de CPF e senha.")
            else:
                try:
                    resp = requests.post(f"{API_URL}/token", data={"username": cpf_limpo, "password": senha_input}, timeout=10)
                    if resp.status_code == 200:
                        data = resp.json()
                        st.session_state.token = data["access_token"]
                        st.session_state.username = data.get("nome", "Usuário")
                        st.session_state.role = data.get("role", "Operador")
                        st.session_state.cpf = data.get("cpf", cpf_limpo)
                        login_sucesso = True
                    else:
                        erro_credenciais = True
                except requests.exceptions.RequestException:
                    erro_conexao = True

        # Renderização dos feedbacks fora do escopo do try/except para não quebrar o Streamlit
        if login_sucesso:
            st.success("✅ Login realizado com sucesso!")
            time.sleep(1)
            st.rerun()
        elif erro_credenciais:
            st.error("❌ CPF ou senha inválidos")
        elif erro_conexao:
            st.error("❌ Erro de conexão com o backend no Render")
            
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ===================== INTERFACE PRINCIPAL GESTÃO DE REDE =====================
st.sidebar.markdown(f"""
    <div style='background: rgba(255,255,255,0.08); border-radius:12px; padding:15px; text-align:center; margin-bottom:20px;'>
        <p style='margin:0; opacity:0.7; font-size:11px;'>ANALISTA AUTENTICADO</p>
        <p style='margin:5px 0; font-size:16px; font-weight:700; color:#F39200;'>{st.session_state.username.upper()}</p>
        <span style='background:#F39200; color:#0F172A; padding:2px 12px; border-radius:20px; font-size:11px; font-weight:700;'>{st.session_state.role}</span>
    </div>
""", unsafe_allow_html=True)

menu = st.sidebar.radio("Menu Operacional", [
    "🏠 Dashboard Executivo",
    "📝 Lançar Atividade",
    "🗓️ Escala Semanal"
], label_visibility="collapsed")

st.sidebar.markdown("<br>"*5, unsafe_allow_html=True)
if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True, type="secondary"):
    st.session_state.token = None
    st.session_state.clear()
    st.rerun()

# ----------------- TELA: DASHBOARD -----------------
if menu == "🏠 Dashboard Executivo":
    st.markdown("<h1 style='color: #0F172A; font-weight: 800;'>Dashboard Executivo</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>Visão em tempo real da performance operacional da Rede.</p>", unsafe_allow_html=True)
    
    resp = api_get("/registros/")
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        if not df.empty:
            c1, c2 = st.columns(2)
            with c1:
                st.markdown(f"<div class='kpi-card'><div style='color:#64748B; font-weight:600; font-size:13px;'>TOTAL ATIVIDADES</div><div style='font-size:36px; font-weight:800; color:#0F172A;'>{len(df)}</div></div>", unsafe_allow_html=True)
            with c2:
                pendentes = len([x for x in df['status'] if 'Não' in str(x) or 'Parcial' in str(x)])
                st.markdown(f"<div class='kpi-card' style='border-left-color:#F59E0B;'><div style='color:#64748B; font-weight:600; font-size:13px;'>PENDÊNCIAS</div><div style='font-size:36px; font-weight:800; color:#F59E0B;'>{pendentes}</div></div>", unsafe_allow_html=True)
            
            st.markdown("<br>", unsafe_allow_html=True)
            st.subheader("📋 Histórico Recente de Lançamentos")
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("💡 Conexão efetuada. Nenhum registro lançado hoje.")
    else:
        st.warning("Backend conectado ✓ Aguardando primeiros registros...")

# ----------------- TELA: LANÇAR ATIVIDADE -----------------
elif menu == "📝 Lançar Atividade":
    st.markdown("<h1 style='color: #0F172A; font-weight: 800;'>Lançamento de Atividade</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>Insira as informações operacionais das contas de Rede.</p>", unsafe_allow_html=True)
    
    with st.form("lancamento_rede"):
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.selectbox("Conta de Rede / Cliente", ["FR FISIO", "EV-CITI", "REGULAÇÃO"])
        with col2:
            status = st.selectbox("Status Operacional", ["Realizado Total", "Realizado Parcial", "Não Realizado"])
        
        obs = st.text_area("Justificativa / Observações Detalhadas", height=150, placeholder="Descreva os contatos, status de prestadores, etc...")
        
        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("💾 REGISTRAR ATIVIDADE ATIVA", type="primary", use_container_width=True):
            payload = {
                "operador_nome": st.session_state.username, 
                "cliente_nome": cliente, 
                "status": status, 
                "justificativa": obs or ""
            }
            resp = api_post("/registros/", data=payload)
            if resp.status_code in [200, 201]:
                st.success("✅ Atividade de Rede registrada com sucesso!")
                st.balloons()
            else:
                st.error("❌ Falha interna ao salvar registro no servidor.")

# ----------------- TELA: ESCALA SEMANAL -----------------
elif menu == "🗓️ Escala Semanal":
    st.markdown("<h1 style='color: #0F172A; font-weight: 800;'>Escala de Trabalho Semanal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B;'>Acompanhamento das agendas e turnos dos Analistas de Rede.</p>", unsafe_allow_html=True)
    
    resp = api_get("/cronograma/")
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        if not df.empty:
            # Filtro de segurança contra projetos antigos remanescentes
            df = df[~df["cliente"].str.upper().isin(["DNA CARE", "VIVEST"])]
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("📅 Nenhuma escala configurada no backend para esta semana.")
    else:
        st.info("⏳ Sincronizando escala de trabalho...")