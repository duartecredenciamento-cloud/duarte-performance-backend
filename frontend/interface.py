import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import io
from datetime import datetime

import utils

# --- FUNÇÕES DE REQUISIÇÃO AUXILIARES (Para corrigir o Pylance) ---
def api_post(endpoint, json_data):
    headers = {}
    if "token" in st.session_state and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return requests.post(f"{API_URL}{endpoint}", json=json_data, headers=headers, timeout=10)

def api_post_file(endpoint, files):
    headers = {}
    if "token" in st.session_state and st.session_state.token:
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    return requests.post(f"{API_URL}{endpoint}", files=files, headers=headers, timeout=10)

# ===================== 1. CONFIGURACOES GLOBAIS E UI =====================
st.set_page_config(
    page_title="Duarte Performance | Gestao Operacional",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "https://duarte-performance-backend.onrender.com"

st.markdown("""
<style>
    /* =========================================================
       SYSTEM PALETTE & TOKENS (DUARTE PREMIUM DESIGN SYSTEM)
       ========================================================= */
    :root {
        --primary-navy: #001E57;
        --secondary-navy: #0B296B;
        --dark-abyss: #030A1A;
        --accent-orange: #FF9200;
        --accent-hover: #E07A00;
        --accent-glow: rgba(255, 146, 0, 0.35);
        --bg-body: #F4F6F9;
        --bg-card: #FFFFFF;
        --text-primary: #0F172A;
        --text-muted: #64748B;
        --border-color: #E2E8F0;
    }

    /* =========================================================
       ANIMATIONS KEYFRAMES
       ========================================================= */
    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(15px); }
        to { opacity: 1; transform: translateY(0); }
    }

    @keyframes pulseGlow {
        0% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.4); }
        70% { box-shadow: 0 0 0 12px rgba(255, 146, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
    }

    @keyframes shimmer {
        0% { background-position: -200% 0; }
        100% { background-position: 200% 0; }
    }

    /* =========================================================
       GLOBAL APP & CONTAINER STYLING
       ========================================================= */
    .stApp {
        background-color: var(--bg-body);
        background-image: 
            radial-gradient(circle at 80% 0%, rgba(255, 146, 0, 0.06) 0%, transparent 50%),
            radial-gradient(circle at 20% 100%, rgba(0, 30, 87, 0.04) 0%, transparent 60%);
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif;
    }

    /* Animação suave para as seções carregarem */
    .block-container {
        animation: fadeInUp 0.4s ease-out forwards;
    }

    /* =========================================================
       SIDEBAR GLASSMORPHISM & NAV
       ========================================================= */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--primary-navy) 0%, var(--dark-abyss) 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08) !important;
        box-shadow: 4px 0 25px rgba(0, 0, 0, 0.15);
    }

    [data-testid="stSidebar"] * {
        color: #F8FAFC !important;
    }

    /* Radios / Menu Lateral customizado */
    div[role="radiogroup"] > label {
        padding: 12px 18px !important;
        border-radius: 12px !important;
        margin-bottom: 6px !important;
        background: rgba(255, 255, 255, 0.02) !important;
        border: 1px solid rgba(255, 255, 255, 0.05) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    }

    div[role="radiogroup"] > label:hover {
        background: rgba(255, 146, 0, 0.12) !important;
        border-color: rgba(255, 146, 0, 0.4) !important;
        transform: translateX(6px) scale(1.01);
    }

    div[role="radiogroup"] > label[data-checked="true"] {
        background: linear-gradient(90deg, rgba(255, 146, 0, 0.25) 0%, rgba(255, 146, 0, 0.05) 100%) !important;
        border-left: 4px solid var(--accent-orange) !important;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
    }

    /* =========================================================
       KPI CARDS ULTRA MODERN
       ========================================================= */
    .kpi-card {
        background: var(--bg-card);
        padding: 24px;
        border-radius: 20px;
        border: 1px solid var(--border-color);
        border-left: 6px solid var(--accent-orange);
        box-shadow: 0 10px 25px -5px rgba(0, 30, 87, 0.05);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }

    .kpi-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 20px 35px -10px rgba(0, 30, 87, 0.12);
        border-color: rgba(255, 146, 0, 0.3);
    }

    .kpi-card h2, .kpi-card h3 {
        color: var(--primary-navy);
        font-weight: 800;
        letter-spacing: -0.5px;
    }

    /* =========================================================
       FORM INPUTS & BUTTONS
       ========================================================= */
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="textarea"] {
        background-color: #FFFFFF !important;
        border-radius: 12px !important;
        border: 1.5px solid #CBD5E1 !important;
        transition: all 0.2s ease !important;
    }

    .stTextInput input, .stTextArea textarea, input[type="text"], input[type="password"] {
        background-color: #FFFFFF !important;
        color: var(--text-primary) !important;
        -webkit-text-fill-color: var(--text-primary) !important;
        font-weight: 600 !important;
        font-size: 15px !important;
    }

    div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within {
        border-color: var(--accent-orange) !important;
        box-shadow: 0 0 0 4px rgba(255, 146, 0, 0.18) !important;
    }

    /* Botão Principal */
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary-navy) 0%, var(--secondary-navy) 100%) !important;
        color: #FFFFFF !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        letter-spacing: 0.5px !important;
        padding: 14px 28px !important;
        box-shadow: 0 4px 15px rgba(0, 30, 87, 0.2) !important;
        transition: all 0.3s ease !important;
    }

    .stButton>button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--accent-orange) 0%, var(--accent-hover) 100%) !important;
        box-shadow: 0 8px 25px var(--accent-glow) !important;
        transform: translateY(-2px);
    }

    /* =========================================================
       LOGIN CARD GLASS EFFECTS
       ========================================================= */
    .login-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        padding: 48px;
        border-radius: 28px;
        box-shadow: 0 20px 50px -10px rgba(0, 30, 87, 0.15);
        max-width: 460px;
        margin: auto;
        border: 1px solid rgba(255, 255, 255, 0.8);
        animation: fadeInUp 0.5s ease-out forwards;
    }

    /* Ajuste de Abas */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background-color: #F1F5F9;
        padding: 6px;
        border-radius: 14px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 42px;
        border-radius: 10px;
        font-weight: 700;
        color: var(--text-muted);
    }

    .stTabs [aria-selected="true"] {
        background-color: #FFFFFF !important;
        color: var(--primary-navy) !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
    }
</style>
""", unsafe_allow_html=True)

# Papeis que tem permissao de gestao (editar cronograma, editar apontamento, ver auditoria)
PAPEIS_GESTAO = ["Admin Master", "Gestor"]

for key in ["token", "username", "nome", "role", "perfil_completo"]:
    if key not in st.session_state:
        st.session_state[key] = None


# ===================== HELPERS DE API (nada de dado mockado a partir daqui) =====================
def api_get(endpoint):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    return requests.get(f"{API_URL}{endpoint}", headers=headers, timeout=15)

def api_post_form(endpoint, data=None, files=None):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    return requests.post(f"{API_URL}{endpoint}", data=data, files=files, headers=headers, timeout=20)

def api_post_json(endpoint, payload):
    headers = {"Authorization": f"Bearer {st.session_state.token}", "Content-Type": "application/json"}
    return requests.post(f"{API_URL}{endpoint}", json=payload, headers=headers, timeout=20)

def api_put_json(endpoint, payload):
    headers = {"Authorization": f"Bearer {st.session_state.token}", "Content-Type": "application/json"}
    return requests.put(f"{API_URL}{endpoint}", json=payload, headers=headers, timeout=20)

def api_delete(endpoint):
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    return requests.delete(f"{API_URL}{endpoint}", headers=headers, timeout=15)

@st.cache_data(ttl=30, show_spinner=False)
def carregar_cronograma_cache(_token):
    resp = requests.get(f"{API_URL}/cronograma/", headers={"Authorization": f"Bearer {_token}"}, timeout=15)
    if resp.status_code == 200 and resp.json():
        return pd.DataFrame(resp.json())
    return pd.DataFrame(columns=["id", "operador", "dia_semana", "atividade", "cliente", "periodo", "data_limite", "status_prazo", "duplicado"])

def carregar_cronograma():
    return carregar_cronograma_cache(st.session_state.token)

def limpar_cache_cronograma():
    carregar_cronograma_cache.clear()


# ===================== 2. TELA DE LOGIN / CADASTRO =====================
if not st.session_state.get("token"):
    
    # 1. ESTILIZAÇÃO CSS AVANÇADA (GLASSMORPHISM, BADGES & EFEITOS NEON)
    st.markdown(
        """
        <style>
            /* Animação Smooth de Entrada */
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(24px); }
                to { opacity: 1; transform: translateY(0); }
            }
            @keyframes pulseGlow {
                0% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.4); }
                70% { box-shadow: 0 0 0 12px rgba(255, 146, 0, 0); }
                100% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
            }

            .login-wrapper {
                animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                padding-top: 3vh;
            }

            /* Badge Superior de Tecnologia */
            .brand-badge {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: rgba(0, 30, 87, 0.06);
                border: 1px solid rgba(0, 30, 87, 0.15);
                color: #001E57;
                padding: 6px 16px;
                border-radius: 30px;
                font-size: 13px;
                font-weight: 700;
                margin-bottom: 20px;
            }
            .badge-dot {
                width: 8px;
                height: 8px;
                background-color: #FF9200;
                border-radius: 50%;
                animation: pulseGlow 2s infinite;
            }

            /* Card Glassmorphism do Formulário */
            .login-card-glass {
                background: rgba(255, 255, 255, 0.85);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid rgba(226, 232, 240, 0.8);
                border-radius: 24px;
                padding: 36px 32px;
                box-shadow: 0 20px 40px -15px rgba(0, 30, 87, 0.08), 0 0 15px rgba(0, 0, 0, 0.02);
                transition: all 0.3s ease;
            }

            /* Recursos em Destaque no Lado Esquerdo */
            .feature-pill {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-top: 16px;
                background: rgba(255, 255, 255, 0.6);
                border: 1px solid rgba(226, 232, 240, 0.6);
                padding: 12px 18px;
                border-radius: 14px;
                max-width: 420px;
            }
            .feature-icon {
                font-size: 20px;
                background: rgba(0, 30, 87, 0.08);
                width: 38px;
                height: 38px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 10px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div class='login-wrapper'>", unsafe_allow_html=True)

    # Layout Dividido: Coluna de Branding (Esquerda) vs Formulário (Direita)
    col_brand, col_form = st.columns([1.2, 1], gap="large")

    # --- LADO ESQUERDO: BRANDING & EXPERIÊNCIA DE IMPACTO ---
    with col_brand:
        st.markdown(
            """
            <div style="padding-top: 4vh; padding-right: 15px;">
                <div class='brand-badge'>
                    <span class='badge-dot'></span> Ecossistema Inteligente v2.4
                </div>
                
                <h1 style="font-size: 3.8rem; font-weight: 900; line-height: 1.05; color: #001E57; margin-bottom: 12px; letter-spacing: -1.5px;">
                    Duarte<br><span style="color: #FF9200;">Performance</span>
                </h1>
                
                <h3 style="font-weight: 700; color: #475569; font-size: 1.35rem; margin-bottom: 20px; letter-spacing: -0.3px;">
                    Departamento de Credenciamento & Operações
                </h3>
                
                <p style="font-size: 1.05rem; color: #64748B; line-height: 1.6; max-width: 440px; margin-bottom: 30px;">
                    Gerencie cadastros, acompanhe relatórios de auditabilidade e otimize a produtividade da equipe em uma única central automatizada.
                </p>

                <!-- Destaques Rápidos -->
                <div class='feature-pill'>
                    <div class='feature-icon'>⚡</div>
                    <div>
                        <div style='font-weight: 700; color: #0F172A; font-size: 14px;'>Alta Performance</div>
                        <div style='color: #64748B; font-size: 12px;'>Fluxos simplificados para validação diária</div>
                    </div>
                </div>

                <div class='feature-pill'>
                    <div class='feature-icon'>🛡️</div>
                    <div>
                        <div style='font-weight: 700; color: #0F172A; font-size: 14px;'>Rastreabilidade & LGPD</div>
                        <div style='color: #64748B; font-size: 12px;'>Logs completos e segurança de acesso por nível</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- LADO DIREITO: CARD DE LOGIN / CADASTRO ---
    with col_form:
        st.markdown("<div class='login-card-glass'>", unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["🔑 Acessar Plataforma", "🆕 Solicitar Acesso"])

        # TAB 1: LOGIN
        with tab_login:
            st.markdown("<p style='color: #64748B; font-size: 13px; margin-top: 8px;'>Informe suas credenciais corporativas para entrar.</p>", unsafe_allow_html=True)
            
            username_input = st.text_input("Usuário", placeholder="ex: erick.duarte", key="login_username")
            senha_input = st.text_input("Senha de Acesso", type="password", placeholder="••••••••", key="login_senha")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🚀 ENTRAR NO SISTEMA", type="primary", use_container_width=True):
                if not username_input or not senha_input:
                    st.warning("⚠️ Por favor, informe seu usuário e senha.")
                else:
                    try:
                        with st.spinner("Autenticando credenciais..."):
                            resp = requests.post(
                                f"{API_URL}/token", 
                                data={"username": username_input.strip(), "password": senha_input}, 
                                timeout=10
                            )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.update({
                                "token": data["access_token"],
                                "username": data.get("username"),
                                "nome": data.get("nome"),
                                "role": data.get("role", "Operador"),
                                "perfil_completo": data.get("perfil_completo", True)
                            })
                            st.success("✨ Autenticação realizada! Redirecionando...")
                            time.sleep(0.4)
                            st.rerun()
                        else:
                            st.error("❌ Usuário ou senha incorretos.")
                    except Exception:
                        st.error("⚠️ Não foi possível conectar ao servidor backend. Verifique sua conexão.")

        # TAB 2: CRIAR CONTA
        with tab_signup:
            st.markdown("<p style='color: #64748B; font-size: 13px; margin-top: 8px;'>Cadastre-se para obter acesso inicial como Operador.</p>", unsafe_allow_html=True)
            
            nome_signup = st.text_input("Nome Completo", placeholder="ex: Erick Duarte", key="signup_nome")
            username_signup = st.text_input("Usuário (Login)", placeholder="ex: erick.duarte", key="signup_username")
            
            c_email, c_whats = st.columns(2)
            email_signup = c_email.text_input("E-mail", placeholder="seu@email.com", key="signup_email")
            telefone_signup = c_whats.text_input("WhatsApp", placeholder="(11) 99999-9999", key="signup_telefone")
            
            c_s1, c_s2 = st.columns(2)
            senha_signup = c_s1.text_input("Crie uma Senha", type="password", placeholder="••••••••", key="signup_senha")
            senha_confirma = c_s2.text_input("Confirme a Senha", type="password", placeholder="••••••••", key="signup_senha2")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ CONCLUIR CADASTRO", type="primary", use_container_width=True):
                if not all([nome_signup, username_signup, senha_signup, senha_confirma]):
                    st.warning("⚠️ Nome, usuário e senha são preenchimentos obrigatórios.")
                elif senha_signup != senha_confirma:
                    st.error("⚠️ As senhas digitadas não conferem.")
                else:
                    payload = {
                        "username": username_signup.strip().lower(), 
                        "password": senha_signup, 
                        "nome": nome_signup.strip(),
                        "email": email_signup.strip() if email_signup else None, 
                        "telefone": telefone_signup.strip() if telefone_signup else None
                    }
                    try:
                        with st.spinner("Criando credenciais..."):
                            resp = requests.post(f"{API_URL}/cadastro/", json=payload, timeout=10)
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.update({
                                "token": data["access_token"],
                                "username": data.get("username"),
                                "nome": data.get("nome"),
                                "role": data.get("role", "Operador"),
                                "perfil_completo": data.get("perfil_completo", True)
                            })
                            st.success("🎉 Conta criada com sucesso! Entrando no sistema...")
                            time.sleep(0.4)
                            st.rerun()
                        elif resp.status_code == 400:
                            st.error(resp.json().get("detail", "⚠️ Este nome de usuário já está cadastrado."))
                        else:
                            st.error(f"❌ Erro ao criar conta: {resp.text}")
                    except Exception:
                        st.error("⚠️ Não foi possível conectar ao servidor backend. Tente novamente.")

        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ===================== 2.1. COMPLETAR PERFIL (Primeiro acesso de conta criada pelo Admin) =====================
if not st.session_state.get("perfil_completo"):
    
    # 1. ESTILIZAÇÃO CSS AVANÇADA (Glassmorphism, Step Badges e Animações)
    st.markdown(
        """
        <style>
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(24px); }
                to { opacity: 1; transform: translateY(0); }
            }
            @keyframes pulseGlow {
                0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); }
                70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); }
                100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); }
            }

            .onboarding-wrapper {
                animation: fadeInUp 0.55s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                padding-top: 3vh;
            }

            /* Badge de Onboarding / Etapas */
            .step-badge {
                display: inline-flex;
                align-items: center;
                gap: 8px;
                background: rgba(255, 146, 0, 0.1);
                border: 1px solid rgba(255, 146, 0, 0.3);
                color: #FF9200;
                padding: 6px 16px;
                border-radius: 30px;
                font-size: 13px;
                font-weight: 700;
                margin-bottom: 20px;
            }
            .step-dot {
                width: 8px;
                height: 8px;
                background-color: #10B981;
                border-radius: 50%;
                animation: pulseGlow 2s infinite;
            }

            /* Card Glassmorphism do Formulário */
            .onboarding-card-glass {
                background: rgba(255, 255, 255, 0.88);
                backdrop-filter: blur(16px);
                -webkit-backdrop-filter: blur(16px);
                border: 1px solid rgba(226, 232, 240, 0.8);
                border-radius: 24px;
                padding: 36px 32px;
                box-shadow: 0 20px 40px -15px rgba(0, 30, 87, 0.08), 0 0 15px rgba(0, 0, 0, 0.02);
            }

            /* Cards Informativos de Segurança */
            .security-pill {
                display: flex;
                align-items: center;
                gap: 12px;
                margin-top: 16px;
                background: rgba(255, 255, 255, 0.65);
                border: 1px solid rgba(226, 232, 240, 0.7);
                padding: 12px 18px;
                border-radius: 14px;
                max-width: 440px;
            }
            .security-icon {
                font-size: 18px;
                background: rgba(0, 30, 87, 0.08);
                width: 36px;
                height: 36px;
                display: flex;
                align-items: center;
                justify-content: center;
                border-radius: 10px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    st.markdown("<div class='onboarding-wrapper'>", unsafe_allow_html=True)

    # Layout Dividido: Coluna de Branding / Welcoming (Esquerda) vs Formulário (Direita)
    col_brand, col_form = st.columns([1.2, 1], gap="large")

    # --- LADO ESQUERDO: MENSAGEM DE BOAS-VINDAS E ORIENTAÇÕES ---
    with col_brand:
        usr_atual = st.session_state.get("username", "Colaborador")
        st.markdown(
            f"""
            <div style="padding-top: 4vh; padding-right: 15px;">
                <div class='step-badge'>
                    <span class='step-dot'></span> Etapa Final • Ativação de Acesso
                </div>
                
                <h1 style="font-size: 3.5rem; font-weight: 900; line-height: 1.08; color: #001E57; margin-bottom: 12px; letter-spacing: -1.5px;">
                    Seja bem-vindo,<br><span style="color: #FF9200;">{usr_atual}!</span>
                </h1>
                
                <h3 style="font-weight: 700; color: #475569; font-size: 1.3rem; margin-bottom: 20px; letter-spacing: -0.3px;">
                    Configuração do Perfil Corporativo
                </h3>
                
                <p style="font-size: 1.05rem; color: #64748B; line-height: 1.6; max-width: 440px; margin-bottom: 28px;">
                    Sua conta pré-cadastrada pela administração já está pronta! Valide seus dados corporativos abaixo para liberar seu Workspace na plataforma.
                </p>

                <!-- Garantias de Segurança -->
                <div class='security-pill'>
                    <div class='security-icon'>🛡️</div>
                    <div>
                        <div style='font-weight: 700; color: #0F172A; font-size: 13px;'>Proteção de Dados & LGPD</div>
                        <div style='color: #64748B; font-size: 12px;'>Seus dados são de uso exclusivo da Duarte Gestão</div>
                    </div>
                </div>

                <div class='security-pill'>
                    <div class='security-icon'>⚡</div>
                    <div>
                        <div style='font-weight: 700; color: #0F172A; font-size: 13px;'>Acesso Imediato</div>
                        <div style='color: #64748B; font-size: 12px;'>Sua esteira de trabalho será liberada após salvar</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # --- LADO DIREITO: FORMULÁRIO DE COMPLEMENTAÇÃO ---
    with col_form:
        st.markdown("<div class='onboarding-card-glass'>", unsafe_allow_html=True)
        
        st.markdown(
            """
            <div style='text-align: center; margin-bottom: 20px;'>
                <div style='font-size: 28px; margin-bottom: 4px;'>👤</div>
                <h3 style='color: #001E57; font-weight: 800; margin: 0; font-size: 22px;'>Complete seu Perfil</h3>
                <p style='color: #64748B; font-size: 13px; margin-top: 4px;'>Confirme os dados para personalização do seu perfil.</p>
            </div>
            """,
            unsafe_allow_html=True
        )

        nome_completar = st.text_input("Nome Completo (Obrigatório)", value=st.session_state.get("nome") or "", placeholder="ex: Erick Duarte", key="completar_nome")
        email_completar = st.text_input("E-mail Corporativo", placeholder="seuemail@duartegestao.com.br", key="completar_email")
        telefone_completar = st.text_input("WhatsApp / Telefone Direct", placeholder="(11) 99999-9999", key="completar_telefone")

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚀 SALVAR E ACESSAR PLATAFORMA", type="primary", use_container_width=True):
            if not nome_completar.strip():
                st.warning("⚠️ Por favor, preencha o seu nome completo para prosseguir.")
            else:
                payload = {
                    "nome": nome_completar.strip(),
                    "email": email_completar.strip() if email_completar else None,
                    "telefone": telefone_completar.strip() if telefone_completar else None
                }
                
                with st.spinner("Atualizando cadastro e configurando área de trabalho..."):
                    resp = api_put_json("/usuarios/me", payload)
                    
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.nome = data.get("nome")
                    st.session_state.perfil_completo = True
                    st.success("✨ Perfil configurado com sucesso! Redirecionando...")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"❌ Erro ao atualizar perfil: {resp.text}")

        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ===================== 3. CONTEXTO DO PERFIL (SIDEBAR) =====================

# 1. Tratamento Defensivo do Nome e Iniciais
nome_raw = st.session_state.get("nome") or st.session_state.get("username") or "Usuário"
nome_usuario = nome_raw.strip().title()
partes_nome = nome_usuario.split()
iniciais = "".join([n[0] for n in partes_nome[:2]]).upper() if len(partes_nome) > 1 else nome_usuario[:2].upper()
role = st.session_state.get("role", "Operador")

# 2. Definição Visual da Badge por Permissão (Role Color Mapping)
role_styles = {
    "Admin Master": "background: rgba(239, 68, 68, 0.15); color: #FCA5A5; border: 1px solid rgba(239, 68, 68, 0.3);",
    "Gestão": "background: rgba(255, 146, 0, 0.15); color: #FFB84D; border: 1px solid rgba(255, 146, 0, 0.3);",
    "Operador": "background: rgba(16, 185, 129, 0.15); color: #6EE7B7; border: 1px solid rgba(16, 185, 129, 0.3);"
}
style_role = role_styles.get(role, "background: rgba(255, 255, 255, 0.1); color: #E2E8F0; border: 1px solid rgba(255, 255, 255, 0.2);")

# 3. CSS Exclusivo da Sidebar
st.sidebar.markdown("""
<style>
    /* Estilização da Sidebar Glassmorphism */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #001E57 0%, #000F2D 100%) !important;
        border-right: 1px solid rgba(255, 255, 255, 0.08);
    }

    /* Card de Perfil */
    .profile-card {
        background: rgba(255, 255, 255, 0.05);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        border-radius: 20px;
        padding: 22px 16px;
        text-align: center;
        margin-bottom: 24px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.25);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .profile-card:hover {
        border-color: rgba(255, 146, 0, 0.4);
        box-shadow: 0 12px 35px rgba(255, 146, 0, 0.15);
    }

    /* Container do Avatar com Indicador Online */
    .avatar-wrapper {
        position: relative;
        width: 68px;
        height: 68px;
        margin: 0 auto 12px auto;
    }
    .avatar-circle {
        background: linear-gradient(135deg, #FF9200 0%, #CC7500 100%);
        color: #FFFFFF;
        width: 100%;
        height: 100%;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 22px;
        font-weight: 900;
        letter-spacing: 1px;
        box-shadow: 0 6px 20px rgba(255, 146, 0, 0.4);
        border: 2px solid rgba(255, 255, 255, 0.2);
    }
    .status-indicator {
        position: absolute;
        bottom: 2px;
        right: 2px;
        width: 14px;
        height: 14px;
        background-color: #10B981;
        border: 2.5px solid #001E57;
        border-radius: 50%;
    }

    /* Botão de Logout Customizado */
    .logout-btn-wrapper button {
        background: rgba(239, 68, 68, 0.1) !important;
        color: #FCA5A5 !important;
        border: 1px solid rgba(239, 68, 68, 0.25) !important;
        border-radius: 12px !important;
        font-weight: 700 !important;
        transition: all 0.25s ease !important;
    }
    .logout-btn-wrapper button:hover {
        background: rgba(239, 68, 68, 0.25) !important;
        border-color: #EF4444 !important;
        color: #FFFFFF !important;
        box-shadow: 0 4px 15px rgba(239, 68, 68, 0.3) !important;
    }
</style>
""", unsafe_allow_html=True)

# 4. Header de Marca na Sidebar
st.sidebar.markdown("""
<div style='display: flex; align-items: center; gap: 10px; padding: 10px 5px 20px 5px;'>
    <div style='background: #FF9200; width: 8px; height: 24px; border-radius: 4px;'></div>
    <div>
        <div style='color: #FFFFFF; font-weight: 900; font-size: 16px; letter-spacing: -0.5px;'>DUARTE PERFORMANCE</div>
        <div style='color: rgba(255, 255, 255, 0.5); font-size: 10px; font-weight: 700; text-transform: uppercase;'>Credenciamento v2.4</div>
    </div>
</div>
""", unsafe_allow_html=True)

# 5. Cartão de Perfil do Usuário
st.sidebar.markdown(f"""
<div class='profile-card'>
    <div class='avatar-wrapper'>
        <div class='avatar-circle'>{iniciais}</div>
        <div class='status-indicator' title='Sessão Ativa'></div>
    </div>
    <div style='color: #F8FAFC; font-size: 16px; font-weight: 800; margin-bottom: 6px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;'>
        {nome_usuario}
    </div>
    <span style='
        padding: 4px 14px; 
        border-radius: 20px; 
        font-size: 10px; 
        font-weight: 800; 
        text-transform: uppercase; 
        letter-spacing: 0.6px;
        {style_role}
    '>{role}</span>
</div>
""", unsafe_allow_html=True)

# 6. Construção Dinâmica do Menu de Navegação
menus_disponiveis = [
    "📊 Dashboard Gerencial", 
    "🗓️ Escala Semanal", 
    "📑 Relatórios Operacionais", 
    "📝 Lançar Execução Diária"
]

if role in PAPEIS_GESTAO:
    menus_disponiveis.append("✏️ Editor de Apontamentos")

if role == "Admin Master":
    menus_disponiveis.append("👥 Gestão de Equipe")
    menus_disponiveis.append("🔐 Auditoria e Acessos")

# Título da Seção de Navegação
st.sidebar.markdown(
    "<p style='color: rgba(255,255,255,0.4); font-size: 10px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; margin: 15px 0 10px 5px;'>Navegação Principal</p>", 
    unsafe_allow_html=True
)

# Renderização do Menu Radio
menu = st.sidebar.radio("Navegação do Sistema", menus_disponiveis, label_visibility="collapsed")

# 7. Separador e Botão de Logout Estilizado
st.sidebar.markdown("<hr style='border: none; border-top: 1px solid rgba(255,255,255,0.08); margin: 25px 0 15px 0;'>", unsafe_allow_html=True)

st.sidebar.markdown("<div class='logout-btn-wrapper'>", unsafe_allow_html=True)
if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True):
    st.session_state.clear()
    st.rerun()
st.sidebar.markdown("</div>", unsafe_allow_html=True)


# --- ABA 1: DASHBOARD GERENCIAL ---
if menu == "📊 Dashboard Gerencial":
    st.markdown("""
    <div style="margin-bottom: 25px;">
        <h1 style="color: #0F172A; font-weight: 900; font-size: 2.2rem; margin-bottom: 4px;">
            📊 Dashboard Gerencial de Performance
        </h1>
        <p style="color: #64748B; font-size: 1rem; margin: 0;">
            Métricas consolidadas de produtividade e acompanhamento de SLA da operação de Credenciamento.
        </p>
    </div>
    """, unsafe_allow_html=True)

    resp_reg = api_get("/registros/")
    if resp_reg.status_code != 200:
        st.error("⚠️ Não foi possível carregar os registros do servidor. Verifique a conexão com o backend.")
        st.stop()

    dados_reg = resp_reg.json()
    if not dados_reg:
        st.info("📭 Ainda não há nenhum apontamento lançado no sistema.")
        st.stop()

    df_reg = pd.DataFrame(dados_reg)

    # Tratamento defensivo de dados
    cols_esperadas = ["operador_nome", "cliente_nome", "status"]
    for col in cols_esperadas:
        if col not in df_reg.columns:
            df_reg[col] = "Não Informado"

    df_reg["operador_nome"] = df_reg["operador_nome"].fillna("Não Atribuído")
    df_reg["cliente_nome"] = df_reg["cliente_nome"].fillna("Cliente Não Informado")
    df_reg["status"] = df_reg["status"].fillna("Não Informado")

    # --- Painel de Filtros estilo Card ---
    with st.expander("🔍 Painel de Filtros Avançados", expanded=True):
        fcol1, fcol2 = st.columns(2)
        with fcol1:
            filtro_operador = st.multiselect(
                "Filtrar por Operador", 
                options=sorted(df_reg["operador_nome"].unique()),
                placeholder="Todos os operadores"
            )
        with fcol2:
            filtro_cliente = st.multiselect(
                "Filtrar por Cliente", 
                options=sorted(df_reg["cliente_nome"].unique()),
                placeholder="Todos os clientes"
            )

    df_view = df_reg.copy()
    if filtro_operador:
        df_view = df_view[df_view["operador_nome"].isin(filtro_operador)]
    if filtro_cliente:
        df_view = df_view[df_view["cliente_nome"].isin(filtro_cliente)]

    # Métrica de Consolidação
    total = len(df_view)
    realizado_total = int((df_view["status"] == "Realizado Total").sum())
    realizado_parcial = int((df_view["status"] == "Realizado Parcial").sum())
    nao_realizado = int((df_view["status"] == "Não Realizado").sum())
    nao_informado = int((df_view["status"] == "Não Informado").sum())

    taxa_eficiencia = round((realizado_total / total * 100), 1) if total > 0 else 0.0

    # KPI Cards Elevados
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"""
    <div style='background: #FFFFFF; padding: 20px 15px; border-radius: 14px; border-top: 5px solid #001E57; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center;'>
        <span style='color: #64748B; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;'>Total de Apontamentos</span>
        <h2 style='color: #001E57; font-size: 32px; font-weight: 900; margin: 6px 0 2px 0;'>{total}</h2>
        <span style='font-size: 11px; color: #001E57; font-weight: 700;'>Eficiência SLA: {taxa_eficiencia}%</span>
    </div>
    """, unsafe_allow_html=True)

    c2.markdown(f"""
    <div style='background: #FFFFFF; padding: 20px 15px; border-radius: 14px; border-top: 5px solid #10B981; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center;'>
        <span style='color: #10B981; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;'>Realizado Total</span>
        <h2 style='color: #10B981; font-size: 32px; font-weight: 900; margin: 6px 0 2px 0;'>{realizado_total}</h2>
        <span style='font-size: 11px; color: #64748B;'>Dentro da Meta</span>
    </div>
    """, unsafe_allow_html=True)

    c3.markdown(f"""
    <div style='background: #FFFFFF; padding: 20px 15px; border-radius: 14px; border-top: 5px solid #FF9200; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center;'>
        <span style='color: #FF9200; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;'>Realizado Parcial</span>
        <h2 style='color: #FF9200; font-size: 32px; font-weight: 900; margin: 6px 0 2px 0;'>{realizado_parcial}</h2>
        <span style='font-size: 11px; color: #64748B;'>Acompanhamento Requerido</span>
    </div>
    """, unsafe_allow_html=True)

    c4.markdown(f"""
    <div style='background: #FFFFFF; padding: 20px 15px; border-radius: 14px; border-top: 5px solid #EF4444; box-shadow: 0 4px 15px rgba(0,0,0,0.05); text-align: center;'>
        <span style='color: #EF4444; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;'>Pendente / Não Realizado</span>
        <h2 style='color: #EF4444; font-size: 32px; font-weight: 900; margin: 6px 0 2px 0;'>{nao_realizado + nao_informado}</h2>
        <span style='font-size: 11px; color: #64748B;'>Gargalo / Atenção</span>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Mapeamento oficial de cores do sistema
    color_map = {
        "Realizado Total": "#10B981",
        "Realizado Parcial": "#FF9200",
        "Não Realizado": "#EF4444",
        "Não Informado": "#94A3B8"
    }

    g1, g2 = st.columns(2)
    with g1:
        if total > 0:
            fig_pie = px.pie(
                df_view, 
                names="status", 
                title="<b>Pipeline Operacional (SLA)</b>", 
                hole=0.55,
                color="status",
                color_discrete_map=color_map
            )
            fig_pie.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                marker=dict(line=dict(color='#FFFFFF', width=2))
            )
            fig_pie.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#0F172A"),
                legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
                margin=dict(t=50, b=50, l=10, r=10)
            )
            st.plotly_chart(fig_pie, use_container_width=True)

    with g2:
        if total > 0:
            fig_bar = px.bar(
                df_view, 
                x="operador_nome", 
                color="status", 
                title="<b>Produtividade por Operador</b>",
                color_discrete_map=color_map,
                barmode="stack"
            )
            fig_bar.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", color="#0F172A"),
                xaxis_title="Operador",
                yaxis_title="Qtd. Apontamentos",
                legend=dict(orientation="h", yanchor="bottom", y=-0.3, xanchor="center", x=0.5),
                margin=dict(t=50, b=50, l=10, r=10)
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("<hr style='border: none; border-top: 1px solid #E2E8F0; margin: 30px 0 20px 0;'>", unsafe_allow_html=True)
    st.markdown("### 🏢 Volumetria por Carteira de Cliente")
    
    if total > 0:
        df_cliente = df_view["cliente_nome"].value_counts().reset_index()
        df_cliente.columns = ["cliente_nome", "count"]
        
        fig_cliente = px.bar(
            df_cliente, 
            x="cliente_nome", 
            y="count",
            text="count",
            title="<b>Volume Total de Apontamentos por Cliente</b>", 
            color_discrete_sequence=["#001E57"]
        )
        fig_cliente.update_traces(
            textposition='outside',
            marker_line_color='#FF9200',
            marker_line_width=1.5
        )
        fig_cliente.update_layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#0F172A"),
            xaxis_title="Cliente / Operadora",
            yaxis_title="Volume de Demandas",
            margin=dict(t=50, b=40, l=10, r=10)
        )
        st.plotly_chart(fig_cliente, use_container_width=True)


# --- ABA 2: ESCALA SEMANAL (UNIFICADA E CORRIGIDA) ---
elif menu == "🗓️ Escala Semanal":
    st.markdown("""
    <div style="margin-bottom: 25px;">
        <h1 style="color: #0F172A; font-weight: 900; font-size: 2.2rem; margin-bottom: 4px;">
            🗓️ Escala Semanal - Gestão Comercial
        </h1>
        <p style="color: #64748B; font-size: 1rem; margin: 0;">
            Matriz oficial de distribuição de carteiras e horários da equipe de Credenciamento.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Dados fiéis à foto enviada
    ESCALA_IMAGEM_OFICIAL = [
        # LARISSA
        {"operador": "LARISSA", "periodo": "MANHA", "dia_semana": "Segunda", "cliente": "EV-CITI"},
        {"operador": "LARISSA", "periodo": "MANHA", "dia_semana": "Terça", "cliente": "CONVACARE"},
        {"operador": "LARISSA", "periodo": "MANHA", "dia_semana": "Quarta", "cliente": "IMC"},
        {"operador": "LARISSA", "periodo": "MANHA", "dia_semana": "Quinta", "cliente": "PRIME"},
        {"operador": "LARISSA", "periodo": "MANHA", "dia_semana": "Sexta", "cliente": "PRÉ ALINHAMENTO"},
        {"operador": "LARISSA", "periodo": "TARDE", "dia_semana": "Sexta", "cliente": "RESCINDIDOS - UNICLIN/MAR/SILMARO e ETC"},
        
        # KARINE
        {"operador": "KARINE", "periodo": "MANHA", "dia_semana": "Segunda", "cliente": "ALPHA LABs"},
        {"operador": "KARINE", "periodo": "MANHA", "dia_semana": "Terça", "cliente": "CLINICA TOPÁZIO"},
        {"operador": "KARINE", "periodo": "MANHA", "dia_semana": "Quarta", "cliente": "RALG"},
        {"operador": "KARINE", "periodo": "MANHA", "dia_semana": "Quinta", "cliente": "ATIVAMENTE"},
        {"operador": "KARINE", "periodo": "MANHA", "dia_semana": "Sexta", "cliente": "MVS"},
        {"operador": "KARINE", "periodo": "TARDE", "dia_semana": "Quinta", "cliente": "MULHER MODERNA"},
        {"operador": "KARINE", "periodo": "TARDE", "dia_semana": "Sexta", "cliente": "DIOGO PARAUAPEBAS"},

        # NEIA
        {"operador": "NEIA", "periodo": "MANHA", "dia_semana": "Segunda", "cliente": "CLINICA VIVENCY"},
        {"operador": "NEIA", "periodo": "MANHA", "dia_semana": "Terça", "cliente": "LAB. BRUNO"},
        {"operador": "NEIA", "periodo": "MANHA", "dia_semana": "Quarta", "cliente": "CLINICA AMINO"},
        {"operador": "NEIA", "periodo": "MANHA", "dia_semana": "Quinta", "cliente": "CLINICA FARFALLA"},
        {"operador": "NEIA", "periodo": "MANHA", "dia_semana": "Sexta", "cliente": "PRO-EXAME"},

        # VITÓRIA - I
        {"operador": "VITÓRIA - I", "periodo": "MANHA", "dia_semana": "Segunda", "cliente": "CLINICA ROSANA"},
        {"operador": "VITÓRIA - I", "periodo": "MANHA", "dia_semana": "Terça", "cliente": "MEDLIGTH"},
        {"operador": "VITÓRIA - I", "periodo": "MANHA", "dia_semana": "Quarta", "cliente": "INST. VER"},
        {"operador": "VITÓRIA - I", "periodo": "MANHA", "dia_semana": "Quinta", "cliente": "CANTAREIRA"},
        {"operador": "VITÓRIA - I", "periodo": "MANHA", "dia_semana": "Sexta", "cliente": "SUPORTE"},

        # SILVANA
        {"operador": "SILVANA", "periodo": "MANHA", "dia_semana": "Segunda", "cliente": "HOSP. AMATO"},
        {"operador": "SILVANA", "periodo": "MANHA", "dia_semana": "Terça", "cliente": "CLIN COFFI"},
        {"operador": "SILVANA", "periodo": "MANHA", "dia_semana": "Quarta", "cliente": "RBL"},
        {"operador": "SILVANA", "periodo": "MANHA", "dia_semana": "Quinta", "cliente": "TRIDES"},
        {"operador": "SILVANA", "periodo": "MANHA", "dia_semana": "Sexta", "cliente": "HARMONY"},

        # JULIA
        {"operador": "JULIA", "periodo": "MANHA", "dia_semana": "Segunda", "cliente": "FR FISIO"},
        {"operador": "JULIA", "periodo": "MANHA", "dia_semana": "Terça", "cliente": "FISIO LIFE"},
        {"operador": "JULIA", "periodo": "MANHA", "dia_semana": "Quarta", "cliente": "CIE FISIO - SJC"},
        {"operador": "JULIA", "periodo": "MANHA", "dia_semana": "Quinta", "cliente": "EMS-BETESDA"},
        {"operador": "JULIA", "periodo": "MANHA", "dia_semana": "Sexta", "cliente": "VIVA - TEA"},
    ]

    # Carrega os dados salvos no banco
    df_crono = carregar_cronograma()

    # ÚNICO CONJUNTO DE ABAS PARA A TELA
    tab_matriz, tab_crud, tab_import = st.tabs([
        "📊 Matriz de Distribuição", 
        "✏️ Alocação Manual / CRUD", 
        "📥 Importar Planilha Excel"
    ])

    # Estilização visual para células destacadas
    def estilizar_matriz(val):
        v = str(val).strip().upper()
        if v in ["HOSP. AMATO", "INST. VER", "PRIME"]:
            return 'color: #DC2626; font-weight: 800; background-color: #FEF2F2;'
        elif v == "MANHA":
            return 'color: #0284C7; font-weight: 700; font-style: italic;'
        elif v == "TARDE":
            return 'color: #D97706; font-weight: 700; font-style: italic;'
        elif "FÉRIAS" in v or "FERIAS" in v:
            return 'background-color: #E0F2FE; color: #0369A1; font-weight: bold;'
        elif "SUPORTE" in v:
            return 'background-color: #FEF3C7; color: #B45309; font-style: italic;'
        elif v != "":
            return 'color: #0F172A; font-weight: 600;'
        return ''

   # ==================== ABA 1: MATRIZ VISUAL ====================
    with tab_matriz:
        if df_crono.empty:
            st.info("📭 Nenhum item cadastrado no cronograma semanal ainda. Utilize as abas ao lado para adicionar.")
        else:
            df_crono = df_crono.fillna("")
        
        # Métricas da Escala
        total_ops = df_crono["operador"].nunique()
        total_alocacoes = len(df_crono[~df_crono["cliente"].isin(["", "X", "FOLGA"])])
        qtd_duplicados = int(df_crono["duplicado"].sum()) if "duplicado" in df_crono.columns else 0

        # Injeção de Estilos CSS para Efeitos, Gradientes e Animações
        st.markdown("""
        <style>
            @keyframes pulse-subtle {
                0% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.3); }
                70% { box-shadow: 0 0 0 10px rgba(239, 68, 68, 0); }
                100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0); }
            }
            .kpi-card {
                background: #FFFFFF;
                border-radius: 16px;
                padding: 20px 24px;
                border: 1px solid rgba(226, 232, 240, 0.8);
                box-shadow: 0 10px 25px -5px rgba(0, 0, 0, 0.03), 0 8px 10px -6px rgba(0, 0, 0, 0.01);
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                position: relative;
                overflow: hidden;
            }
            .kpi-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 20px 30px -10px rgba(0, 0, 0, 0.08);
            }
            .kpi-card-border {
                position: absolute;
                top: 0; left: 0;
                width: 6px; height: 100%;
            }
            .alert-container {
                background: linear-gradient(135deg, #FEF2F2 0%, #FFF5F5 100%);
                border: 1px solid #FCA5A5;
                border-left: 6px solid #EF4444;
                border-radius: 16px;
                padding: 20px 24px;
                margin-bottom: 25px;
                animation: pulse-subtle 2.5s infinite;
                transition: all 0.3s ease;
            }
            .alert-item {
                display: flex;
                align-items: center;
                gap: 8px;
                padding: 6px 0;
                border-bottom: 1px dashed #FECACA;
            }
            .alert-item:last-child {
                border-bottom: none;
            }
        </style>
        """, unsafe_allow_html=True)

        # Cards de Indicadores Rápidos (Com Efeito Hover e Design Moderno)
        k1, k2, k3 = st.columns(3)
        
        with k1:
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-card-border' style='background: linear-gradient(180deg, #001E57 0%, #0B3C91 100%);'></div>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='color: #64748B; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;'>Operadores Escalados</span>
                    <span style='background: #F1F5F9; padding: 4px 8px; border-radius: 8px; font-size: 14px;'>👥</span>
                </div>
                <h3 style='color: #001E57; font-size: 32px; font-weight: 900; margin: 8px 0 0 0; letter-spacing: -0.5px;'>{total_ops}</h3>
            </div>
            """, unsafe_allow_html=True)

        with k2:
            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-card-border' style='background: linear-gradient(180deg, #FF9200 0%, #D97706 100%);'></div>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='color: #64748B; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;'>Atribuições Ativas</span>
                    <span style='background: #FFFBEB; padding: 4px 8px; border-radius: 8px; font-size: 14px;'>📌</span>
                </div>
                <h3 style='color: #FF9200; font-size: 32px; font-weight: 900; margin: 8px 0 0 0; letter-spacing: -0.5px;'>{total_alocacoes}</h3>
            </div>
            """, unsafe_allow_html=True)

        with k3:
            cor_status = "#EF4444" if qtd_duplicados > 0 else "#10B981"
            grad_status = "linear-gradient(180deg, #EF4444 0%, #DC2626 100%)" if qtd_duplicados > 0 else "linear-gradient(180deg, #10B981 0%, #059669 100%)"
            bg_icon = "#FEF2F2" if qtd_duplicados > 0 else "#ECFDF5"
            icon_status = "⚠️" if qtd_duplicados > 0 else "✅"

            st.markdown(f"""
            <div class='kpi-card'>
                <div class='kpi-card-border' style='background: {grad_status};'></div>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='color: #64748B; font-size: 11px; font-weight: 800; text-transform: uppercase; letter-spacing: 0.5px;'>Sinalizações de Conflito</span>
                    <span style='background: {bg_icon}; padding: 4px 8px; border-radius: 8px; font-size: 14px;'>{icon_status}</span>
                </div>
                <h3 style='color: {cor_status}; font-size: 32px; font-weight: 900; margin: 8px 0 0 0; letter-spacing: -0.5px;'>{qtd_duplicados}</h3>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Card de Alerta de Duplicidades (Pulsante e Dinâmico)
        if qtd_duplicados > 0:
            duplicados_texto = df_crono[df_crono["duplicado"] == True][["operador", "cliente"]].drop_duplicates()
            
            itens_html = "".join([
                f"""
                <div class='alert-item'>
                    <span style='color: #EF4444; font-size: 12px;'>🚨</span>
                    <span style='color: #7F1D1D; font-size: 13px;'>
                        <b>{r['operador']}</b> alocado em duplicidade na carteira <u>{r['cliente']}</u>
                    </span>
                </div>
                """ for _, r in duplicados_texto.iterrows()
            ])

            st.markdown(f"""
            <div class='alert-container'>
                <div style='display: flex; align-items: center; gap: 10px; margin-bottom: 12px;'>
                    <div style='background: #EF4444; color: white; padding: 4px 8px; border-radius: 6px; font-size: 12px; font-weight: 800;'>
                        ATENÇÃO
                    </div>
                    <h4 style='color: #991B1B; margin: 0; font-size: 16px; font-weight: 800;'>
                        Conflitos de Alocação Detectados na Escala
                    </h4>
                </div>
                <div style='display: flex; flex-direction: column; gap: 2px;'>
                    {itens_html}
                </div>
            </div>
            """, unsafe_allow_html=True)

            # Tratamento da Pivot
            dias_padrao = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
            dias_presentes = [d for d in dias_padrao if d in set(df_crono["dia_semana"].unique())]

            # Estilização das Células da Tabela
            def estilo_celula(val):
                v = str(val).strip().upper()
                if "FÉRIAS" in v or "FERIAS" in v:
                    return 'background-color: #E0F2FE; color: #0369A1; font-weight: bold; text-align: center;'
                elif "SUPORTE" in v:
                    return 'background-color: #FEF3C7; color: #B45309; font-style: italic; font-weight: 600;'
                elif "FOLGA" in v:
                    return 'background-color: #F1F5F9; color: #94A3B8; text-align: center;'
                elif v in ("", "X", "-"):
                    return 'color: #CBD5E1; text-align: center;'
                return 'color: #0F172A; font-weight: 600;'

            pivot_linhas = []
            for op in sorted(o for o in df_crono["operador"].unique() if o):
                linha = {"Operador": op}
                sub = df_crono[df_crono["operador"] == op]
                for d in dias_presentes:
                    itens_dia = sub[sub["dia_semana"] == d]
                    linha[d] = " / ".join(itens_dia["cliente"].tolist()) if not itens_dia.empty else ""
                pivot_linhas.append(linha)

            df_pivot = pd.DataFrame(pivot_linhas)

            st.markdown("### 📋 Grade Semanal de Atribuições")
            st.dataframe(
                df_pivot.style.map(estilo_celula), 
                use_container_width=True, 
                hide_index=True,
                height=450
            )

    # ==================== ABA 2: ALOCAÇÃO MANUAL (CRUD) ====================
    with tab_crud:
        st.markdown("### ➕ Nova Alocação / Ajuste de Turno")
        st.caption("Preencha o formulário abaixo para registrar ou atualizar a alocação de um operador.")

        with st.form("form_alocacao_manual"):
            c_op, c_dia, c_cli = st.columns(3)
            with c_op:
                op_nome = st.text_input("Nome do Operador", placeholder="ex: Lucas / Aline")
            with c_dia:
                dia_sel = st.selectbox("Dia da Semana", ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"])
            with c_cli:
                cli_nome = st.text_input("Cliente / Carteira / Status", placeholder="ex: VIVEST, FÉRIAS, SUPORTE")

            st.markdown("<br>", unsafe_allow_html=True)
            btn_salvar_alocacao = st.form_submit_button("💾 Salvar Alocação na Escala", type="primary", use_container_width=True)

            if btn_salvar_alocacao:
                if not op_nome or not cli_nome:
                    st.warning("Preencha o operador e o cliente/status para salvar.")
                else:
                    payload = {"operador": op_nome, "dia_semana": dia_sel, "cliente": cli_nome}
                    resp = api_post("/cronograma/", payload)
                    if resp.status_code in [200, 201]:
                        st.success(f"Alocação de **{op_nome}** para **{dia_sel}** salva com sucesso!")
                        time.sleep(0.5)
                        st.rerun()
                    else:
                        st.error(f"Erro ao salvar alocação: {resp.text}")

    # ==================== ABA 3: IMPORTAÇÃO DE PLANILHA ====================
    with tab_import:
        st.markdown("### 📥 Carga Massiva via Planilha Excel")
        st.caption("Envie o arquivo `.xlsx` da escala para importar os dados de uma só vez.")

        arquivo_escala = st.file_uploader("Selecione o arquivo da Escala Semanal (.xlsx, .xls)", type=["xlsx", "xls"])
        
        if arquivo_escala is not None:
            try:
                df_upload = pd.read_excel(arquivo_escala)
                st.markdown("#### Pré-visualização dos Dados Detectados:")
                st.dataframe(df_upload.head(10), use_container_width=True)

                if st.button("🚀 Confirmar Importação da Planilha", type="primary"):
                    with st.spinner("Processando e sincronizando escala..."):
                        # Envia a planilha em bytes/json para a API
                        files = {"file": (arquivo_escala.name, arquivo_escala.getvalue(), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
                        resp = api_post_file("/cronograma/importar", files)
                        if resp.status_code in [200, 201]:
                            st.success("Planilha importada e sincronizada com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"Erro ao importar planilha: {resp.text}")
            except Exception as e:
                st.error(f"Erro ao ler o arquivo Excel: {e}")

    # --- CRUD (só Gestor/Admin Master) ---
    if role in PAPEIS_GESTAO:
        st.markdown("### ⚙️ Painel de Distribuição de Contas")
        tab_add, tab_edit, tab_del, tab_import = st.tabs(["➕ Adicionar", "✏️ Editar / Mover", "🗑️ Remover", "📥 Importar Planilha"])

        with tab_add:
            with st.form("form_add_cronograma"):
                c1, c2 = st.columns(2)
                operador_novo = c1.text_input("Operador")
                dia_novo = c2.selectbox("Dia da Semana", ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"])
                c3, c4 = st.columns(2)
                cliente_novo = c3.text_input("Cliente / Atividade")
                periodo_novo = c4.selectbox("Período", ["Manhã", "Tarde", "Integral"])
                atividade_nova = st.text_input("Descrição da Atividade", value="Credenciamento")
                if st.form_submit_button("Adicionar à Escala", type="primary"):
                    if not operador_novo or not cliente_novo:
                        st.warning("Preencha Operador e Cliente.")
                    else:
                        payload = {
                            "operador": operador_novo, "dia_semana": dia_novo, "atividade": atividade_nova,
                            "cliente": cliente_novo, "periodo": periodo_novo, "data_limite": None, "status_prazo": "Pendente"
                        }
                        resp = api_post_json("/cronograma/", payload)
                        if resp.status_code == 200:
                            st.success("Item adicionado à escala!")
                            if resp.json().get("alerta_duplicidade"):
                                st.warning("⚠️ Esse cliente já estava alocado pra esse operador em outro dia.")
                            limpar_cache_cronograma()
                            st.rerun()
                        else:
                            st.error(f"Erro ao adicionar: {resp.text}")

        with tab_edit:
            if df_crono.empty:
                st.info("Nada pra editar ainda.")
            else:
                opcoes = {f"#{r['id']} — {r['operador']} — {r['cliente']} ({r['dia_semana']})": r for _, r in df_crono.iterrows()}
                escolha = st.selectbox("Selecione o item", list(opcoes.keys()))
                item_sel = opcoes[escolha]
                with st.form("form_edit_cronograma"):
                    c1, c2 = st.columns(2)
                    operador_edit = c1.text_input("Operador", value=item_sel["operador"])
                    dia_edit = c2.selectbox("Dia da Semana (mover)", ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"],
                                             index=["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"].index(item_sel["dia_semana"]) if item_sel["dia_semana"] in ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"] else 0)
                    c3, c4 = st.columns(2)
                    cliente_edit = c3.text_input("Cliente / Atividade", value=item_sel["cliente"])
                    periodo_edit = c4.text_input("Período", value=item_sel["periodo"])
                    if st.form_submit_button("Salvar Alterações", type="primary"):
                        payload = {"operador": operador_edit, "dia_semana": dia_edit, "cliente": cliente_edit, "periodo": periodo_edit}
                        resp = api_put_json(f"/cronograma/{int(item_sel['id'])}", payload)
                        if resp.status_code == 200:
                            st.success("Item atualizado/movido com sucesso!")
                            limpar_cache_cronograma()
                            st.rerun()
                        else:
                            st.error(f"Erro ao editar: {resp.text}")

        with tab_del:
            if df_crono.empty:
                st.info("Nada pra remover ainda.")
            else:
                opcoes_del = {f"#{r['id']} — {r['operador']} — {r['cliente']} ({r['dia_semana']})": int(r['id']) for _, r in df_crono.iterrows()}
                escolha_del = st.selectbox("Selecione o item pra remover", list(opcoes_del.keys()), key="del_select")
                if st.button("🗑️ Remover Item Selecionado", type="secondary"):
                    resp = api_delete(f"/cronograma/{opcoes_del[escolha_del]}")
                    if resp.status_code == 200:
                        st.success("Item removido da escala.")
                        limpar_cache_cronograma()
                        st.rerun()
                    else:
                        st.error(f"Erro ao remover: {resp.text}")

        with tab_import:
            st.caption("Aceita .xlsx ou .csv com colunas parecidas com: Operador, Dia da Semana, Cliente, Período.")
            arquivo_escala = st.file_uploader("Planilha de Escala", type=["xlsx", "csv"], key="upload_escala")
            if arquivo_escala is not None:
                df_importado, avisos = utils.parsear_planilha_escala(arquivo_escala)
                if avisos:
                    for a in avisos:
                        st.error(a)
                elif df_importado.empty:
                    st.warning("A planilha não trouxe nenhuma linha válida.")
                else:
                    df_com_dup = utils.detectar_duplicidade_escala(df_importado)
                    qtd_dup = int(df_com_dup["duplicado_local"].sum())
                    if qtd_dup > 0:
                        st.warning(f"⚠️ {qtd_dup} linha(s) com cliente repetido pro mesmo operador — revise antes de importar.")
                    st.dataframe(df_com_dup, use_container_width=True, hide_index=True)
                    if st.button("✅ Confirmar Importação", type="primary"):
                        sucesso, falha = 0, 0
                        for _, linha in df_importado.iterrows():
                            payload = {
                                "operador": linha["operador"], "dia_semana": linha.get("dia_semana", "Segunda"),
                                "atividade": "Credenciamento", "cliente": linha["cliente"],
                                "periodo": linha.get("periodo", ""), "data_limite": None, "status_prazo": "Pendente"
                            }
                            resp = api_post_json("/cronograma/", payload)
                            sucesso += 1 if resp.status_code == 200 else 0
                            falha += 1 if resp.status_code != 200 else 0
                        st.success(f"Importação concluída: {sucesso} linha(s) adicionada(s), {falha} falha(s).")
                        limpar_cache_cronograma()
                        st.rerun()


# --- ABA 3: RELATÓRIOS OPERACIONAIS (Filtros Avançados & Métricas Reativas) ---
elif menu == "📑 Relatórios Operacionais":

    # 1. INJEÇÃO DE CSS AVANÇADO (Animações, Cards, Efeitos Glassmorphism e Hover)
    st.markdown(
        """
        <style>
            /* Animação Smooth Fade-In + Slide UP */
            @keyframes fadeInUp {
                from { 
                    opacity: 0; 
                    transform: translateY(12px); 
                }
                to { 
                    opacity: 1; 
                    transform: translateY(0); 
                }
            }

            .report-container {
                animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }

            /* Container dos Filtros */
            .filter-card {
                background: #FFFFFF;
                border: 1px solid #E2E8F0;
                border-radius: 16px;
                padding: 24px 24px 12px 24px;
                box-shadow: 0 4px 20px -2px rgba(0, 30, 87, 0.04);
                margin-bottom: 24px;
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }
            .filter-card:hover {
                box-shadow: 0 12px 28px -6px rgba(0, 30, 87, 0.08);
                border-color: #CBD5E1;
            }

            /* Mini Cards de Métricas KPi */
            .metric-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
                animation: fadeInUp 0.7s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }
            .metric-mini-card {
                background: #FFFFFF;
                border-radius: 14px;
                padding: 18px 20px;
                border: 1px solid #E2E8F0;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.02);
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
                position: relative;
                overflow: hidden;
            }
            .metric-mini-card:hover {
                transform: translateY(-4px);
                box-shadow: 0 12px 24px -6px rgba(0, 30, 87, 0.12);
            }
            .metric-title {
                color: #64748B;
                font-size: 11px;
                font-weight: 800;
                text-transform: uppercase;
                letter-spacing: 0.5px;
            }
            .metric-value {
                font-size: 28px;
                font-weight: 900;
                margin: 6px 0 0 0;
                line-height: 1;
            }

            /* Banner da Seção de Exportação */
            .export-card {
                background: linear-gradient(135deg, #001E57 0%, #0F172A 100%);
                border-radius: 16px;
                padding: 24px 28px;
                color: #FFFFFF;
                margin-top: 28px;
                box-shadow: 0 12px 28px -6px rgba(0, 30, 87, 0.25);
                display: flex;
                align-items: center;
                justify-content: space-between;
                animation: fadeInUp 0.8s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }
            
            /* Suavização de Inputs Streamlit */
            .stSelectbox label, .stMultiSelect label, .stDateInput label {
                font-weight: 700 !important;
                color: #334155 !important;
                font-size: 0.85rem !important;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )

    # 2. HEADER DA PÁGINA
    st.markdown(
        """
        <div class='report-container'>
            <h1 style='color: #0F172A; font-weight: 900; font-size: 2.2rem; letter-spacing: -0.5px; margin-bottom: 4px;'>
                📑 Relatório Principal de Produtividade
            </h1>
            <p style='color: #64748B; font-size: 0.98rem; margin: 0 0 20px 0;'>
                Filtros avançados, indicadores operacionais reativos e extração de dados auditáveis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. REQUISIÇÃO E TRATAMENTO DOS DADOS
    resp_reg = api_get("/registros/") if "api_get" in globals() else None

    if resp_reg is None or resp_reg.status_code != 200:
        st.error(
            "⚠️ Não foi possível carregar os registros do servidor. Verifique a"
            " conexão com a API."
        )
        st.stop()

    dados_reg = resp_reg.json()
    if not dados_reg:
        st.info("📭 Ainda não há nenhum apontamento lançado no sistema.")
        st.stop()

    df_principal = pd.DataFrame(dados_reg)

    # Conversão Tratada de Datas
    df_principal["data_registro"] = pd.to_datetime(df_principal["data_registro"])
    df_principal["Data"] = df_principal["data_registro"].dt.strftime("%d/%m/%Y")

    dias_pt_map = {
        0: "Segunda-feira",
        1: "Terça-feira",
        2: "Quarta-feira",
        3: "Quinta-feira",
        4: "Sexta-feira",
        5: "Sábado",
        6: "Domingo",
    }
    df_principal["Dia"] = df_principal["data_registro"].dt.weekday.map(
        dias_pt_map
    )

    # Renomeação e Higienização de Colunas
    df_principal = df_principal.rename(
        columns={
            "cliente_nome": "Cliente",
            "operador_nome": "Operador",
            "status": "Status",
            "justificativa": "Observação",
        }
    )

    # 4. PAINEL DE FILTROS AVANÇADOS
    st.markdown("<div class='filter-card'>", unsafe_allow_html=True)
    st.markdown(
        "<h4 style='color: #001E57; margin: 0 0 16px 0; font-weight: 800; font-size:"
        " 16px; display: flex; align-items: center; gap: 8px;'>"
        "🔍 Painel de Filtros Auditáveis</h4>",
        unsafe_allow_html=True,
    )

    f1, f2, f3 = st.columns([1.2, 1.4, 1.4])
    with f1:
        periodo_sel = st.date_input("📆 Período", value=(), format="DD/MM/YYYY")
    with f2:
        operadores_unicos = sorted(
            df_principal["Operador"].dropna().unique().tolist()
        )
        operador_sel = st.multiselect(
            "👤 Filtrar por Operador",
            operadores_unicos,
            placeholder="Todos os Operadores",
        )
    with f3:
        status_unicos = sorted(
            df_principal["Status"].dropna().unique().tolist()
        )
        status_sel = st.multiselect(
            "🎯 Status de SLA",
            status_unicos,
            placeholder="Todos os Status",
        )

    st.markdown("</div>", unsafe_allow_html=True)

    # 5. APLICAÇÃO REATIVA DOS FILTROS
    df_view = df_principal.copy()

    if isinstance(periodo_sel, tuple) and len(periodo_sel) == 2:
        ini, fim = periodo_sel
        df_view = df_view[
            (df_view["data_registro"].dt.date >= ini)
            & (df_view["data_registro"].dt.date <= fim)
        ]
    if operador_sel:
        df_view = df_view[df_view["Operador"].isin(operador_sel)]
    if status_sel:
        df_view = df_view[df_view["Status"].isin(status_sel)]

    # 6. RESUMO DE MÉTRICAS DINÂMICAS (KPIs)
    total_filtrado = len(df_view)
    total_realizado = len(
        df_view[
            df_view["Status"].str.contains("Realizado", case=False, na=False)
        ]
    )
    nao_realizado = len(
        df_view[
            df_view["Status"].str.contains("Não Realizado", case=False, na=False)
        ]
    )
    taxa_sla = (
        (total_realizado / total_filtrado * 100) if total_filtrado > 0 else 0.0
    )

    m1, m2, m3, m4 = st.columns(4)
    with m1:
        st.markdown(
            f"""
            <div class='metric-mini-card' style='border-left: 5px solid #001E57;'>
                <div class='metric-title'>Registros Filtrados</div>
                <div class='metric-value' style='color: #001E57;'>{total_filtrado:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m2:
        st.markdown(
            f"""
            <div class='metric-mini-card' style='border-left: 5px solid #10B981;'>
                <div class='metric-title'>Concluídos / Parciais</div>
                <div class='metric-value' style='color: #10B981;'>{total_realizado:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m3:
        st.markdown(
            f"""
            <div class='metric-mini-card' style='border-left: 5px solid #EF4444;'>
                <div class='metric-title'>Não Realizados</div>
                <div class='metric-value' style='color: #EF4444;'>{nao_realizado:,}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    with m4:
        st.markdown(
            f"""
            <div class='metric-mini-card' style='border-left: 5px solid #FF9200;'>
                <div class='metric-title'>Taxa de Atendimento</div>
                <div class='metric-value' style='color: #FF9200;'>{taxa_sla:.1f}%</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # 7. VISUALIZAÇÃO INTERATIVA DA TABELA DE DADOS
    st.subheader("📋 Visualização Detalhada dos Registros")

    # Seleção de colunas estratégicas para exibição limpa
    colunas_exibir = [
        col
        for col in [
            "Data",
            "Dia",
            "Cliente",
            "Operador",
            "Status",
            "Observação",
        ]
        if col in df_view.columns
    ]

    st.dataframe(
        df_view[colunas_exibir],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Data": st.column_config.TextColumn("📅 Data", width="small"),
            "Dia": st.column_config.TextColumn("📆 Dia", width="small"),
            "Cliente": st.column_config.TextColumn(
                "🏢 Cliente / Prestador", width="medium"
            ),
            "Operador": st.column_config.TextColumn(
                "👤 Operador", width="medium"
            ),
            "Status": st.column_config.CategoricalColumn(
                "🎯 Status SLA",
                width="medium",
            ),
            "Observação": st.column_config.TextColumn(
                "💬 Observação", width="large"
            ),
        },
    )

    # 8. ÁREA DE EXPORTAÇÃO DOS DADOS
    st.markdown(
        """
        <div class='export-card'>
            <div>
                <h3 style='margin: 0 0 6px 0; font-size: 18px; font-weight: 800; color: #FFFFFF;'>📥 Exportar Dados Filtrados</h3>
                <p style='margin: 0; font-size: 13px; color: #94A3B8;'>Baixe a visualização atual em formato Excel para auditoria externa.</p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Gerador de Excel em memória
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
        df_view.to_excel(writer, sheet_name="Relatório Operacional", index=False)

    st.download_button(
        label="📊 Baixar Relatório (.xlsx)",
        data=buffer.getvalue(),
        file_name="relatorio_operacional_produtividade.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=False,
    )


    # --- FORMATAÇÃO VISUAL DA TABELA ---
    def colorir_relatorio(row):
        styles = [""] * len(row)
        status = str(row["Status"]).strip()

        if status == "Realizado Total":
            bg_color = (
                "background-color: #ECFDF5; color: #065F46; font-weight: 700;"
                " border-radius: 6px;"
            )
        elif status == "Realizado Parcial":
            bg_color = (
                "background-color: #FFFBEB; color: #92400E; font-weight: 700;"
                " border-radius: 6px;"
            )
        elif status == "Não Realizado":
            bg_color = (
                "background-color: #FEF2F2; color: #991B1B; font-weight: 800;"
                " border-radius: 6px;"
            )
        elif status == "Não Informado":
            bg_color = (
                "background-color: #F1F5F9; color: #475569; font-style: italic;"
            )
        else:
            bg_color = ""

        styles[row.index.get_loc("Status")] = bg_color
        styles[row.index.get_loc("Operador")] = (
            "font-weight: 700; color: #0F172A;"
        )
        styles[row.index.get_loc("Cliente")] = "font-weight: 600; color: #334155;"
        return styles


    colunas_exibir = ["Data", "Dia", "Cliente", "Operador", "Status", "Observação"]
    colunas_presentes = [c for c in colunas_exibir if c in df_view.columns]
    df_exibir = df_view[colunas_presentes]

    if df_exibir.empty:
        st.warning(
            "⚠️ Nenhum registro atende aos critérios dos filtros selecionados."
        )
    else:
        st.dataframe(
            df_exibir.style.apply(colorir_relatorio, axis=1),
            use_container_width=True,
            hide_index=True,
            height=420,
        )

    # --- GERADOR DE PLANILHA EXCEL EM MEMÓRIA ---
    towrite = io.BytesIO()
    with pd.ExcelWriter(towrite, engine="xlsxwriter") as writer:
        df_exibir.to_excel(writer, sheet_name="Performance_Duarte", index=False)

        workbook = writer.book
        worksheet = writer.sheets["Performance_Duarte"]
        format_header = workbook.add_format(
            {"bold": True, "bg_color": "#001E57", "font_color": "#FFFFFF"}
        )

        for col_num, value in enumerate(df_exibir.columns.values):
            worksheet.write(0, col_num, value, format_header)
            max_len = (
                max(df_exibir[value].astype(str).map(len).max(), len(value)) + 3
            )
            worksheet.set_column(col_num, col_num, max_len)

    # --- CARD DE EXPORTAÇÃO EXECUTIVA ---
    st.markdown(
        """
        <div style='background: linear-gradient(135deg, #001E57 0%, #0F172A 100%); border-radius: 16px; padding: 20px 24px; margin-top: 20px; box-shadow: 0 10px 25px rgba(0,30,87,0.15);'>
            <div style='display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 15px;'>
                <div>
                    <h4 style='color: #FFFFFF; margin: 0 0 4px 0; font-size: 16px; font-weight: 800;'>📊 Exportação de Dados Consolidados</h4>
                    <p style='color: #94A3B8; margin: 0; font-size: 13px;'>Baixe a base formatada com as colunas e filtros aplicados na tela atual.</p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    st.download_button(
        label="📥 DOWNLOAD DA PLANILHA EXCEL (.XLSX)",
        data=towrite.getvalue(),
        file_name=(
            f"Duarte_Performance_{datetime.now().strftime('%d%m%Y_%H%M')}.xlsx"
        ),
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        type="primary",
        use_container_width=True,
    )

    # --- ABA 4: LANÇAR EXECUÇÃO DIÁRIA ---
elif menu == "📝 Lançar Execução Diária":

    # 1. INJEÇÃO DE CSS AVANÇADO (Design Glassmorphism, Animações e Cards Modernos)
    st.markdown(
        """
        <style>
            /* Animação Smooth Fade-In + Slide Up */
            @keyframes fadeInUp {
                from { 
                    opacity: 0; 
                    transform: translateY(12px); 
                }
                to { 
                    opacity: 1; 
                    transform: translateY(0); 
                }
            }

            .form-container { 
                animation: fadeInUp 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards; 
            }

            /* Card Header Auditado (Gradient Corporativo) */
            .header-audit-card {
                background: linear-gradient(135deg, #001E57 0%, #0F172A 100%);
                border-radius: 16px; 
                padding: 20px 24px; 
                color: #FFFFFF;
                box-shadow: 0 10px 25px -5px rgba(0, 30, 87, 0.25);
                margin-bottom: 24px; 
                display: flex; 
                align-items: center;
                justify-content: space-between; 
                flex-wrap: wrap; 
                gap: 12px;
                animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards;
            }

            .header-audit-badge {
                background: rgba(255, 255, 255, 0.12); 
                backdrop-filter: blur(8px);
                -webkit-backdrop-filter: blur(8px);
                border: 1px solid rgba(255, 255, 255, 0.18); 
                padding: 8px 16px;
                border-radius: 12px; 
                font-size: 13px; 
                font-weight: 700; 
                letter-spacing: 0.3px;
                color: #FFFFFF;
            }

            /* Card Principal do Formulário */
            .form-card {
                background: #FFFFFF; 
                border: 1px solid #E2E8F0;
                border-radius: 18px; 
                padding: 28px;
                box-shadow: 0 10px 30px -5px rgba(0, 30, 87, 0.04); 
                margin-bottom: 24px;
                animation: fadeInUp 0.6s cubic-bezier(0.16, 1, 0.3, 1) forwards;
                transition: all 0.3s ease;
            }
            .form-card:hover {
                border-color: #CBD5E1;
                box-shadow: 0 14px 35px -8px rgba(0, 30, 87, 0.08);
            }

            /* Banner de Alerta para Justificativa */
            .alert-justificativa {
                background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
                border: 1px solid #FCD34D; 
                border-left: 6px solid #FF9200;
                border-radius: 14px; 
                padding: 16px 20px; 
                margin: 20px 0 16px 0;
                animation: fadeInUp 0.3s ease-out forwards;
            }

            .upload-section-title {
                color: #0F172A; 
                font-weight: 800; 
                font-size: 15px;
                margin-top: 24px; 
                margin-bottom: 12px; 
                display: flex; 
                align-items: center; 
                gap: 8px;
            }

            /* Estilização Customizada de Labels de Input */
            .stSelectbox label, .stTextInput label, .stTextArea label, .stFileUploader label {
                font-weight: 700 !important;
                color: #334155 !important;
                font-size: 0.88rem !important;
            }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # 2. CABEÇALHO DA PÁGINA
    st.markdown(
        """
        <div class='form-container'>
            <h1 style='color: #0F172A; font-weight: 900; font-size: 2.2rem; letter-spacing: -0.5px; margin-bottom: 4px;'>
                📝 Apontamento de Execução Diária
            </h1>
            <p style='color: #64748B; font-size: 0.98rem; margin-bottom: 22px;'>
                Registre suas atividades operacionais com validação dinâmica e anexo de evidências auditáveis.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 3. DADOS DE SESSÃO E AUDITORIA
    dia_hoje = utils.dia_semana_atual() if "utils" in globals() else "Dia Atual"
    nome_operador = (
        st.session_state.get("nome") or "Operador Não Identificado"
    ).upper()
    data_formatada = datetime.now().strftime("%d/%m/%Y")

    st.markdown(
        f"""
        <div class='header-audit-card'>
            <div style='display: flex; align-items: center; gap: 12px;'>
                <span style='font-size: 22px;'>🛡️</span>
                <div>
                    <span style='color: #94A3B8; font-size: 11px; text-transform: uppercase; font-weight: 800; letter-spacing: 0.5px; display: block;'>Sessão Auditada</span>
                    <span style='color: #FFFFFF; font-weight: 800; font-size: 16px;'>{nome_operador}</span>
                </div>
            </div>
            <div style='display: flex; gap: 10px; align-items: center;'>
                <div class='header-audit-badge'>
                    📅 {data_formatada} <span style='opacity: 0.7; font-weight: 400;'>|</span> {dia_hoje}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # 4. CARREGAMENTO DOS CLIENTES E ESCALA
    df_crono = (
        carregar_cronograma()
        if "carregar_cronograma" in globals()
        else pd.DataFrame()
    )
    clientes_do_dia = (
        utils.clientes_do_operador_no_dia(
            df_crono, st.session_state.get("nome", ""), dia_hoje
        )
        if "utils" in globals()
        else []
    )
    lista_clientes = (
        ["Selecione..."]
        + clientes_do_dia
        + ["Suporte", "Outro (não está na escala de hoje)"]
    )

    if not clientes_do_dia:
        st.info(
            "ℹ️ Não encontramos nenhum cliente atribuído a você na escala de"
            " hoje. Selecione **'Suporte'** ou **'Outro'** para prosseguir."
        )

    # 5. FORMULÁRIO DE DETALHES OPERACIONAIS
    st.markdown("<div class='form-card'>", unsafe_allow_html=True)
    st.markdown(
        "<h4 style='color: #001E57; margin: 0 0 18px 0; font-weight: 800;"
        " font-size: 16px; display: flex; align-items: center; gap: 8px;'>"
        "📋 Detalhes da Operação</h4>",
        unsafe_allow_html=True,
    )

    c_alt1, c_alt2 = st.columns(2)

    with c_alt1:
        cliente_sel = st.selectbox(
            "Selecione o Cliente Trabalhado",
            lista_clientes,
            key="cliente_diario",
        )

        cliente_final = cliente_sel

        # Lógica condicional para seleção secundária de cliente
        if cliente_sel == "Suporte":
            opcoes_suporte = (
                ["Selecione..."] + sorted(list(set(clientes_do_dia)))
                if clientes_do_dia
                else ["Selecione..."]
            )
            cliente_suporte_destino = st.selectbox(
                "Suporte para qual cliente?",
                opcoes_suporte,
                key="cliente_suporte_destino",
            )
            if cliente_suporte_destino != "Selecione...":
                cliente_final = (
                    utils.formatar_cliente_suporte(cliente_suporte_destino)
                    if "utils" in globals()
                    else f"Suporte - {cliente_suporte_destino}"
                )

        elif cliente_sel == "Outro (não está na escala de hoje)":
            cliente_final = st.text_input(
                "Digite o nome do cliente",
                placeholder="Ex: Cliente Especial / Projeto Exceção",
                key="cliente_outro",
            )

    with c_alt2:
        status_sel = st.selectbox(
            "Status Final do Trabalho",
            [
                "Selecione...",
                "Realizado Total",
                "Realizado Parcial",
                "Não Realizado",
            ],
            key="status_diario",
        )

    # 6. JUSTIFICATIVA E MOTIVAÇÃO
    obs_texto = ""
    if status_sel in ["Realizado Parcial", "Não Realizado"]:
        st.markdown(
            f"""
            <div class='alert-justificativa'>
                <div style='display: flex; align-items: center; gap: 8px; margin-bottom: 4px;'>
                    <span style='font-size: 16px;'>⚠️</span>
                    <strong style='color: #B45309; font-size: 14px;'>Justificativa Obrigatória para Auditoria</strong>
                </div>
                <span style='color: #78350F; font-size: 13px;'>Explique detalhadamente o motivo pelo qual o status da atividade foi marcado como <b>{status_sel}</b>.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        obs_texto = st.text_area(
            "Detalhamento Operacional da Ocorrência",
            height=110,
            placeholder=(
                "Ex: Devido a alinhamento de urgência com a gestão, não foi"
                " possível concluir a totalidade das tarefas planejadas para"
                " este cliente."
            ),
            key="justificativa_diaria",
        )

    # 7. UPLOAD DE EVIDÊNCIAS E ANEXOS
    st.markdown(
        "<div class='upload-section-title'>📎 Comprovações e Evidências das"
        " Atividades</div>",
        unsafe_allow_html=True,
    )
    arquivo_evidencia = st.file_uploader(
        "Arraste ou selecione a comprovação do sistema (PNG, JPG, PDF, XLSX)",
        type=["png", "jpg", "jpeg", "pdf", "xlsx"],
        key="evidencia_diaria",
    )

    if arquivo_evidencia is not None and arquivo_evidencia.type in [
        "image/png",
        "image/jpeg",
    ]:
        with st.expander(
            "👁️ Visualizar Prévia da Imagem Anexada", expanded=False
        ):
            st.image(
                arquivo_evidencia,
                caption=f"Evidência Anexada: {arquivo_evidencia.name}",
                use_container_width=True,
            )

    st.markdown("</div>", unsafe_allow_html=True)  # Fechamento do form-card

    st.markdown("<div style='margin-top: 20px;'></div>", unsafe_allow_html=True)

# 8. SUBMISSÃO DO FORMULÁRIO COM VALIDAÇÕES
    if st.button("🚀 ENVIAR APONTAMENTO DIÁRIO", type="primary", use_container_width=True):
        if (
            cliente_sel == "Selecione..."
            or status_sel == "Selecione..."
            or not cliente_final
            or cliente_final == "Selecione..."
        ):
            st.error("⚠️ Por favor, selecione o cliente e o status antes de salvar o formulário.")
        elif status_sel in ["Realizado Parcial", "Não Realizado"] and not obs_texto.strip():
            st.error("⚠️ A justificativa detalhada é estritamente obrigatória para status parciais ou não realizados.")
        else:
            payload = {
                "operador_nome": st.session_state.get("nome", ""),
                "cliente_nome": cliente_final,
                "status": status_sel,
                "justificativa": obs_texto.strip() if obs_texto else "",
            }

            files = (
                {
                    "evidencia": (
                        arquivo_evidencia.name,
                        arquivo_evidencia.getvalue(),
                        arquivo_evidencia.type,
                    )
                }
                if arquivo_evidencia
                else None
            )

            with st.spinner("✨ Gravando apontamento no ecossistema de dados..."):
                resp = (
                    api_post_form("/registros/", data=payload, files=files)
                    if "api_post_form" in globals()
                    else None
                )

            if resp and resp.status_code in [200, 201]:
                st.success("✨ Perfeito! Apontamento gravado com sucesso no ecossistema de dados.")
                st.balloons()
            else:
                detalhe_erro = (
                    resp.text
                    if resp
                    else "Sem resposta ou erro de conexão com o servidor."
                )
                st.error(f"❌ Erro ao gravar o apontamento: {detalhe_erro}")


# --- ABA 5: EDITOR DE APONTAMENTOS ---
elif menu == "✏️ Editor de Apontamentos":

    # 1. ESTILIZAÇÃO CSS E ANIMAÇÕES FLUIDAS
    st.markdown(
        """
        <style>
            @keyframes fadeInUp { 
                from { opacity: 0; transform: translateY(16px); } 
                to { opacity: 1; transform: translateY(0); } 
            }
            .editor-container { 
                animation: fadeInUp 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards; 
            }
            .editor-header-banner {
                background: linear-gradient(135deg, #001E57 0%, #0F172A 100%);
                border-radius: 18px; 
                padding: 24px 30px; 
                color: #FFFFFF;
                box-shadow: 0 12px 28px -5px rgba(0, 30, 87, 0.25); 
                margin-bottom: 24px;
            }
            .preview-card {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(10px);
                border-radius: 14px;
                padding: 18px 22px;
                border: 1px solid rgba(226, 232, 240, 0.2);
                margin-bottom: 20px;
                transition: all 0.3s ease;
            }
            .action-box {
                background: rgba(0, 30, 87, 0.03);
                border: 1px dashed rgba(0, 30, 87, 0.2);
                border-radius: 16px;
                padding: 22px;
                margin-top: 30px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 2. CABEÇALHO DA ABA
    st.markdown(
        """
        <div class='editor-container'>
            <div class='editor-header-banner'>
                <h2 style='margin: 0 0 6px 0; font-weight: 800; font-size: 26px; letter-spacing: -0.5px; color: #FFFFFF;'>
                    ✏️ Editor de Apontamentos & Ajustes
                </h2>
                <p style='margin: 0; color: #94A3B8; font-size: 14px;'>
                    Corrija lançamentos incorretos com rastreabilidade garantida. Toda edição gera um log automático na Auditoria.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if role not in PAPEIS_GESTAO:
        st.error("🔒 Acesso restrito a Gestores e Administradores.")
        st.stop()

    with st.spinner("🔍 Carregando registros de lançamentos..."):
        resp_reg = api_get("/registros/")

    if resp_reg.status_code != 200:
        st.error("⚠️ Não foi possível carregar os registros do servidor.")
        st.stop()

    dados_reg = resp_reg.json()
    if not dados_reg:
        st.info("📭 Nenhum apontamento lançado até o momento.")
        st.stop()

    df_reg = pd.DataFrame(dados_reg)
    df_reg["data_registro"] = pd.to_datetime(df_reg["data_registro"]).dt.strftime("%d/%m/%Y %H:%M")

    # Mapeamento para o Selectbox
    opcoes = {
        f"#{r['id']} — {r['operador_nome']} | {r['cliente_nome']} — {r['status']} ({r['data_registro']})": r
        for _, r in df_reg.iterrows()
    }

    st.markdown("##### 📌 Seleção do Lançamento")
    escolha = st.selectbox("Busque ou escolha o registro para edição:", list(opcoes.keys()))
    item_sel = opcoes[escolha]

    # CARD DE PRÉ-VISUALIZAÇÃO DO REGISTRO SELECIONADO
    status_color = {
        "Realizado Total": "#10B981",
        "Realizado Parcial": "#FF9200",
        "Não Realizado": "#EF4444",
        "Não Informado": "#64748B"
    }.get(item_sel.get("status"), "#001E57")

    st.markdown(
        f"""
        <div class='preview-card'>
            <div style='display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;'>
                <div>
                    <span style='font-size: 12px; color: #64748B; font-weight: 700;'>REGISTRO SELECIONADO #{item_sel.get('id')}</span>
                    <h4 style='margin: 2px 0 0 0; font-size: 18px; color: #0F172A;'>{item_sel.get('cliente_nome')}</h4>
                    <p style='margin: 0; font-size: 13px; color: #64748B;'>Operador: <b>{item_sel.get('operador_nome')}</b> | Data: {item_sel.get('data_registro')}</p>
                </div>
                <div style='background: {status_color}15; border: 1px solid {status_color}40; color: {status_color}; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 13px;'>
                    ● {item_sel.get('status')}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # FORMULÁRIO DE EDIÇÃO ESTRUTURADO
    with st.form("form_editar_apontamento", clear_on_submit=False):
        st.markdown("##### ✏️ Alterar Informações")
        
        c1, c2 = st.columns(2)
        cliente_edit = c1.text_input("Cliente / Prestador", value=item_sel["cliente_nome"])
        
        lista_status = ["Realizado Total", "Realizado Parcial", "Não Realizado", "Não Informado"]
        idx_status = lista_status.index(item_sel["status"]) if item_sel["status"] in lista_status else 0
        status_edit = c2.selectbox("Novo Status", lista_status, index=idx_status)

        obs_edit = st.text_area(
            "Observação / Justificativa da Alteração", 
            value=item_sel.get("justificativa") or "",
            placeholder="Informe o motivo da correção do apontamento..."
        )

        st.markdown("<br>", unsafe_allow_html=True)
        if st.form_submit_button("💾 Salvar Correção do Apontamento", type="primary", use_container_width=True):
            payload = {
                "cliente_nome": cliente_edit,
                "status": status_edit,
                "justificativa": obs_edit,
            }
            with st.spinner("Atualizando apontamento e gerando log de auditoria..."):
                resp = api_put_json(f"/registros/{int(item_sel['id'])}", payload)
                
            if resp.status_code == 200:
                st.success("✅ Apontamento corrigido com sucesso! A alteração foi gravada na Auditoria.")
                st.rerun()
            else:
                st.error(f"❌ Erro ao editar registro: {resp.text}")

    # ÁREA DE PENDÊNCIAS DO DIA (ACTION CARD)
    st.markdown(
        """
        <div class='action-box'>
            <h4 style='margin: 0 0 4px 0; color: #001E57; font-weight: 800;'>🔄 Rotina Automatizada: Pendências do Dia</h4>
            <p style='margin: 0 0 16px 0; color: #64748B; font-size: 13px;'>
                Verifica automaticamente a escala de hoje e marca como <b>"Não Informado"</b> qualquer atividade pendente que não tenha recebido lançamento até o momento.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    if st.button("⚡ Executar Verificação de Pendências do Dia", use_container_width=True):
        with st.spinner("Verificando escala e apontamentos pendentes..."):
            resp = api_post_json("/registros/marcar-pendentes/", {})
        if resp.status_code == 200:
            qtd = resp.json().get("marcados_como_nao_informado", 0)
            st.success(f"🎯 Concluído! **{qtd}** apontamento(s) pendente(s) identificado(s) e marcado(s) como 'Não Informado'.")
        else:
            st.error(f"❌ Erro ao verificar pendências: {resp.text}")

# --- ABA 6: GESTÃO DE EQUIPE ---
elif menu == "👥 Gestão de Equipe":

    # 1. ESTILIZAÇÃO E ANIMAÇÕES CSS
    st.markdown(
        """
        <style>
            @keyframes fadeInUp { 
                from { opacity: 0; transform: translateY(16px); } 
                to { opacity: 1; transform: translateY(0); } 
            }
            .team-container { 
                animation: fadeInUp 0.45s cubic-bezier(0.16, 1, 0.3, 1) forwards; 
            }
            .team-header-banner {
                background: linear-gradient(135deg, #001E57 0%, #0F172A 100%);
                border-radius: 18px; 
                padding: 24px 30px; 
                color: #FFFFFF;
                box-shadow: 0 12px 28px -5px rgba(0, 30, 87, 0.25); 
                margin-bottom: 24px;
                display: flex; 
                align-items: center; 
                justify-content: space-between; 
                flex-wrap: wrap; 
                gap: 12px;
            }
            .kpi-grid-team {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 16px;
                margin-bottom: 24px;
            }
            .kpi-team-card {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(8px);
                border-radius: 14px;
                padding: 16px 20px;
                border: 1px solid rgba(226, 232, 240, 0.15);
                transition: all 0.3s ease;
            }
            .kpi-team-card:hover {
                transform: translateY(-3px);
                border-color: rgba(0, 30, 87, 0.4);
            }
            .kpi-team-title {
                font-size: 11px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                color: #94A3B8;
                font-weight: 600;
            }
            .kpi-team-value {
                font-size: 24px;
                font-weight: 800;
                color: #001E57;
                margin-top: 4px;
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 2. BANNER DE CABEÇALHO
    st.markdown(
        """
        <div class='team-container'>
            <div class='team-header-banner'>
                <div>
                    <h2 style='margin: 0 0 6px 0; font-weight: 800; font-size: 26px; letter-spacing: -0.5px;'>
                        👥 Gestão de Equipe & Controle de Acessos
                    </h2>
                    <p style='margin: 0; color: #94A3B8; font-size: 14px;'>
                        Cadastre novos colaboradores, gerencie permissões por perfil e acompanhe a integridade dos cadastros.
                    </p>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if role != "Admin Master":
        st.error("🔒 Acesso restrito. Apenas Administradores Masters possuem permissão para gerenciar a equipe.")
        st.stop()

    # BUSCA INICIAL DE USUÁRIOS E DEPARTAMENTOS PARA MÉTRICAS E FORM
    resp_deptos = api_get("/departamentos/")
    deptos = resp_deptos.json() if resp_deptos.status_code == 200 else []
    opcoes_depto = {d["nome"]: d["id"] for d in deptos} if deptos else {}

    resp_usuarios = api_get("/usuarios/")
    lista_usuarios = resp_usuarios.json() if (resp_usuarios.status_code == 200 and resp_usuarios.json()) else []

    # KPI CARDS SUPERIORES
    total_membros = len(lista_usuarios)
    perfis_completos = sum(1 for u in lista_usuarios if u.get("perfil_completo"))
    admins_count = sum(1 for u in lista_usuarios if u.get("role") == "Admin Master")

    st.markdown(
        f"""
        <div class='kpi-grid-team'>
            <div class='kpi-team-card'>
                <div class='kpi-team-title'>Total de Colaboradores</div>
                <div class='kpi-team-value'>{total_membros}</div>
            </div>
            <div class='kpi-team-card'>
                <div class='kpi-team-title'>Cadastros Completos</div>
                <div class='kpi-team-value' style='color: #10B981;'>{perfis_completos} / {total_membros}</div>
            </div>
            <div class='kpi-team-card'>
                <div class='kpi-team-title'>Administradores</div>
                <div class='kpi-team-value' style='color: #FF9200;'>{admins_count}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

    # NAVEGAÇÃO DE ABAS
    tab_list, tab_add = st.tabs(["📋 Lista de Equipe", "➕ Novo Colaborador"])

    # --- ABA 1: LISTA DA EQUIPE ---
    with tab_list:
        if lista_usuarios:
            df_equipe = pd.DataFrame(lista_usuarios)
            
            # Formatação visual dos status
            if "perfil_completo" in df_equipe.columns:
                df_equipe["perfil_completo"] = df_equipe["perfil_completo"].map(
                    {True: "🟢 Completo", False: "🟡 Pendente"}
                )

            # Mapeamento e Renomeação de Colunas
            colunas_map = {
                "username": "Usuário",
                "nome": "Nome Completo",
                "email": "E-mail",
                "telefone": "WhatsApp",
                "role": "Cargo / Função",
                "perfil_completo": "Status do Perfil"
            }
            
            # Filtro reativo para a tabela
            col_busca, col_filtro_role = st.columns([2, 1])
            with col_busca:
                termo_busca = st.text_input("🔍 Buscar membro", placeholder="Digite nome, usuário ou e-mail...")
            with col_filtro_role:
                filtro_cargo = st.selectbox("Filtrar por Cargo", ["Todos", "Operador", "Gestor", "Admin Master"])

            # Aplicação de Filtros
            if termo_busca:
                mask = df_equipe.apply(lambda row: row.astype(str).str.contains(termo_busca, case=False).any(), axis=1)
                df_equipe = df_equipe[mask]

            if filtro_cargo != "Todos":
                df_equipe = df_equipe[df_equipe["role"] == filtro_cargo]

            # Seleciona apenas as colunas desejadas que existem no DataFrame
            cols_exibicao = [c for c in colunas_map.keys() if c in df_equipe.columns]
            df_exibir = df_equipe[cols_exibicao].rename(columns=colunas_map)

            st.dataframe(
                df_exibir,
                use_container_width=True,
                hide_index=True,
                height=380
            )
        else:
            st.info("📭 Nenhum colaborador cadastrado na base até o momento.")

    # --- ABA 2: ADICIONAR COLABORADOR ---
    with tab_add:
        st.markdown("#### 👤 Dados do Novo Membro")
        st.caption("Preencha as credenciais iniciais. O novo usuário poderá complementar as demais informações no primeiro acesso.")

        with st.form("form_add_membro", clear_on_submit=True):
            st.markdown("##### 🔑 Credenciais de Acesso (Obrigatório)")
            c1, c2 = st.columns(2)
            username_novo = c1.text_input("Usuário (Login)", placeholder="ex: erick.duarte")
            senha_provisoria = c2.text_input("Senha Provisória", type="password", placeholder="••••••••")

            c3, c4 = st.columns(2)
            role_novo = c3.selectbox("Nível de Permissão (Cargo)", ["Operador", "Gestor", "Admin Master"])
            depto_novo = c4.selectbox("Departamento de Atuação", ["(Nenhum)"] + list(opcoes_depto.keys()))

            st.markdown("---")
            st.markdown("##### 📝 Dados Complementares (Opcional)")
            c5, c6, c7 = st.columns(3)
            nome_novo = c5.text_input("Nome Completo", placeholder="ex: Erick Duarte")
            email_novo = c6.text_input("E-mail Corporativo", placeholder="ex: erick@duartegestao.com.br")
            telefone_novo = c7.text_input("WhatsApp / Telefone", placeholder="ex: (11) 99999-9999")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.form_submit_button("🚀 Cadastrar Colaborador", type="primary", use_container_width=True):
                if not username_novo or not senha_provisoria:
                    st.warning("⚠️ Usuário e senha provisória são campos obrigatórios.")
                else:
                    payload = {
                        "username": username_novo.strip().lower(),
                        "password": senha_provisoria,
                        "role": role_novo,
                        "departamento_id": opcoes_depto.get(depto_novo),
                        "nome": nome_novo.strip() if nome_novo else None,
                        "email": email_novo.strip() if email_novo else None,
                        "telefone": telefone_novo.strip() if telefone_novo else None,
                    }
                    resp = api_post_json("/usuarios/", payload)
                    if resp.status_code == 200:
                        st.success(f"✅ Colaborador **{username_novo}** cadastrado com sucesso!")
                        st.rerun()
                    elif resp.status_code == 400:
                        st.error(resp.json().get("detail", "⚠️ Este nome de usuário já está em uso."))
                    else:
                        st.error(f"❌ Erro ao realizar cadastro: {resp.text}")

# --- ABA 7: AUDITORIA E ACESSOS ---
elif menu == "🔐 Auditoria e Acessos":

    # 1. INJEÇÃO DE CSS AVANÇADO (Glassmorphism, Animações e Cards Neomórficos)
    st.markdown(
        """
        <style>
            /* Animações de Entrada e Efeitos */
            @keyframes fadeInUp { 
                from { opacity: 0; transform: translateY(18px); } 
                to { opacity: 1; transform: translateY(0); } 
            }
            @keyframes pulseGlow { 
                0% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0.4); } 
                70% { box-shadow: 0 0 0 10px rgba(16, 185, 129, 0); } 
                100% { box-shadow: 0 0 0 0 rgba(16, 185, 129, 0); } 
            }

            .audit-container { 
                animation: fadeInUp 0.5s cubic-bezier(0.16, 1, 0.3, 1) forwards; 
            }

            /* Header Principal com Glassmorphism */
            .audit-header-banner {
                background: linear-gradient(135deg, rgba(0, 30, 87, 0.95) 0%, rgba(15, 23, 42, 0.98) 100%);
                backdrop-filter: blur(12px);
                -webkit-backdrop-filter: blur(12px);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 20px; 
                padding: 26px 32px; 
                color: #FFFFFF;
                box-shadow: 0 15px 35px -5px rgba(0, 30, 87, 0.3); 
                margin-bottom: 28px;
                display: flex; 
                align-items: center; 
                justify-content: space-between; 
                flex-wrap: wrap; 
                gap: 16px;
            }

            /* Badge LGPD com Pulso Ativo */
            .lgpd-badge {
                background: rgba(16, 185, 129, 0.12); 
                border: 1px solid rgba(16, 185, 129, 0.4);
                color: #34D399; 
                padding: 8px 18px; 
                border-radius: 30px; 
                font-size: 13px; 
                font-weight: 700;
                letter-spacing: 0.3px;
                display: inline-flex; 
                align-items: center; 
                gap: 8px;
                animation: pulseGlow 2.5s infinite;
            }

            /* Cards de Métricas em Destaque (KPIs) */
            .kpi-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 18px;
                margin-bottom: 28px;
            }
            .kpi-card {
                background: rgba(255, 255, 255, 0.05);
                backdrop-filter: blur(8px);
                border-radius: 16px;
                padding: 20px 22px;
                border: 1px solid rgba(226, 232, 240, 0.15);
                box-shadow: 0 4px 20px rgba(0, 0, 0, 0.03);
                transition: all 0.3s cubic-bezier(0.16, 1, 0.3, 1);
            }
            .kpi-card:hover {
                transform: translateY(-4px);
                border-color: rgba(0, 30, 87, 0.4);
                box-shadow: 0 12px 30px rgba(0, 30, 87, 0.12);
            }
            .kpi-title {
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 0.8px;
                color: #94A3B8;
                font-weight: 600;
                margin-bottom: 6px;
            }
            .kpi-value {
                font-size: 26px;
                font-weight: 800;
                color: #001E57;
            }

            /* Customização de Tabela e Scrollbar */
            ::-webkit-scrollbar {
                width: 8px;
                height: 8px;
            }
            ::-webkit-scrollbar-track {
                background: rgba(0, 0, 0, 0.02);
            }
            ::-webkit-scrollbar-thumb {
                background: rgba(0, 30, 87, 0.2);
                border-radius: 10px;
            }
            ::-webkit-scrollbar-thumb:hover {
                background: rgba(0, 30, 87, 0.5);
            }
        </style>
        """,
        unsafe_allow_html=True
    )

    # 2. CABEÇALHO DA AUDITORIA
    st.markdown(
        """
        <div class='audit-container'>
            <div class='audit-header-banner'>
                <div>
                    <h2 style='margin: 0 0 6px 0; font-weight: 800; font-size: 26px; letter-spacing: -0.5px;'>
                        🔐 Control Tower & Trilha de Auditoria
                    </h2>
                    <p style='margin: 0; color: #94A3B8; font-size: 14px;'>
                        Rastreabilidade em tempo real de operações, alterações e acessos na plataforma.
                    </p>
                </div>
                <div class='lgpd-badge'>
                    <span>🛡️</span> Compliance LGPD Ativo
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    if role != "Admin Master":
        st.warning("🔒 Acesso restrito. Apenas administradores possuem permissão para visualizar logs de auditoria.")
        st.stop()

    # 3. REQUISIÇÃO E EXIBIÇÃO DE DADOS
    with st.spinner("⚡ Sincronizando registros de segurança..."):
        resp_audit = api_get("/auditoria/")
        
    if resp_audit.status_code == 200:
        dados_audit = resp_audit.json()
        if not dados_audit:
            st.info("📭 Nenhum log de auditoria registrado no sistema no momento.")
        else:
            df_audit = pd.DataFrame(dados_audit)
            
            # Formatação estrutural de datas
            if "data_hora" in df_audit.columns:
                df_audit["data_hora"] = pd.to_datetime(df_audit["data_hora"]).dt.strftime("%d/%m/%Y %H:%M:%S")
            
            # --- CARDS DE MÉTRICAS (KPIs RÁPIDOS) ---
            total_logs = len(df_audit)
            usuarios_unicos = df_audit["usuario"].nunique() if "usuario" in df_audit.columns else "N/A"
            acoes_hoje = len(df_audit) # Pode filtrar por data atual se necessário

            st.markdown(
                f"""
                <div class='kpi-grid'>
                    <div class='kpi-card'>
                        <div class='kpi-title'>Total de Eventos</div>
                        <div class='kpi-value'>{total_logs}</div>
                    </div>
                    <div class='kpi-card'>
                        <div class='kpi-title'>Usuários Ativos</div>
                        <div class='kpi-value'>{usuarios_unicos}</div>
                    </div>
                    <div class='kpi-card'>
                        <div class='kpi-title'>Status do Sistema</div>
                        <div class='kpi-value' style='color: #10B981; font-size: 20px; font-weight: 700;'>🟢 Monitorado</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

            st.markdown("### 📜 Registros de Atividade")
            
            # Filtro Interativo
            col_busca, col_espaco = st.columns([1.5, 1.5])
            with col_busca:
                termo_busca = st.text_input("🔍 Filtrar logs em tempo real", placeholder="Digite um nome, ação, ID ou data...")
                
            if termo_busca:
                mask = df_audit.apply(lambda row: row.astype(str).str.contains(termo_busca, case=False).any(), axis=1)
                df_audit = df_audit[mask]

            # Exibição do Dataframe com Altura Fixa
            st.dataframe(
                df_audit,
                use_container_width=True,
                hide_index=True,
                height=420
            )
            
            # --- ÁREA DE EXPORTAÇÃO ---
            buffer_audit = io.BytesIO()
            with pd.ExcelWriter(buffer_audit, engine="xlsxwriter") as writer:
                df_audit.to_excel(writer, sheet_name="Auditoria_Segurança", index=False)
                
            st.markdown("<br>", unsafe_allow_html=True)
            st.download_button(
                label="📥 Exportar Relatório de Auditoria (.xlsx)",
                data=buffer_audit.getvalue(),
                file_name=f"Auditoria_Duarte_Gestao_{datetime.now().strftime('%d%m%Y_%H%M')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary"
            )
    else:
        st.error(f"⚠️ Erro ao carregar as trilhas de auditoria: {resp_audit.text}")