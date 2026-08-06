from datetime import datetime
import os
import time
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import streamlit as st

from views.admin import render_painel_admin
from views.dashboard import render_dashboard
from views.editor import render_editor
from views.escala import render_escala
from views.lancamento import render_lancamento
from views.login import render_login
from views.relatorios import render_relatorios

# ===================== CONFIGURAÇÃO =====================
st.set_page_config(
    page_title="Duarte Performance | Gestão Operacional",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="expanded",
)

FUSO_BR = ZoneInfo("America/Sao_Paulo")
API_URL = os.getenv(
    "BACKEND_URL",
    "https://duarte-performance-backend-production.up.railway.app",
)

PAPEIS_GESTAO = ["Admin Master", "Gestor", "Admin", "Coordenador"]
PAPEIS_LANCAMENTO = [
    "Operador",
    "Visualizador",
    "Admin Master",
    "Gestor",
    "Admin",
    "Coordenador",
]

css_path = os.path.join(os.path.dirname(__file__), "styles.css")
try:
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception as e:
    st.warning(f"⚠️ CSS não carregado: {e}")

# ===================== TELA DE CARREGAMENTO =====================
if "carregando" not in st.session_state:
    st.session_state["carregando"] = True

if st.session_state["carregando"]:
    st.markdown(
        """
    <style>
        [data-testid="stSidebar"],
        [data-testid="stHeader"],
        [data-testid="stToolbar"],
        footer { display: none !important; }
        .stApp {
            background: linear-gradient(145deg, #030A1A 0%, #001E57 45%, #0B296B 100%) !important;
        }
        @keyframes spinRing {
            0%   { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @keyframes pulseDot {
            0%, 100% { opacity: 0.35; transform: scale(0.85); }
            50%      { opacity: 1;    transform: scale(1.1); }
        }
        @keyframes fadeUp {
            from { opacity: 0; transform: translateY(18px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes barShine {
            0%   { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }
        .dp-loader-wrap {
            min-height: 88vh;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            text-align: center;
            animation: fadeUp 0.6s ease-out;
            font-family: 'Inter', system-ui, -apple-system, sans-serif;
        }
        .dp-logo-mark {
            width: 72px; height: 72px; border-radius: 18px;
            background: linear-gradient(135deg, #FF9200 0%, #E07A00 100%);
            display: flex; align-items: center; justify-content: center;
            color: #fff; font-size: 1.75rem; font-weight: 900;
            box-shadow: 0 12px 40px rgba(255, 146, 0, 0.35);
            margin-bottom: 28px;
        }
        .dp-title {
            color: #FFFFFF; font-size: 2rem; font-weight: 800;
            margin: 0 0 6px 0;
        }
        .dp-title span { color: #FF9200; }
        .dp-sub {
            color: #94A3B8; font-size: 0.95rem; margin: 0 0 36px 0;
        }
        .dp-ring {
            width: 48px; height: 48px; border-radius: 50%;
            border: 3px solid rgba(255, 255, 255, 0.12);
            border-top-color: #FF9200;
            animation: spinRing 0.85s linear infinite;
            margin-bottom: 22px;
        }
        .dp-bar {
            width: 200px; height: 4px; border-radius: 99px;
            background: rgba(255, 255, 255, 0.1);
            overflow: hidden; margin-bottom: 18px;
        }
        .dp-bar-inner {
            height: 100%; width: 45%; border-radius: 99px;
            background: linear-gradient(90deg, #FF9200, #FFB84D, #FF9200);
            background-size: 200% 100%;
            animation: barShine 1.4s ease-in-out infinite;
        }
        .dp-status {
            color: #CBD5E1; font-size: 0.8rem; font-weight: 600;
        }
        .dp-dots span {
            display: inline-block; width: 5px; height: 5px;
            margin: 0 3px; border-radius: 50%; background: #FF9200;
            animation: pulseDot 1.2s ease-in-out infinite;
        }
        .dp-dots span:nth-child(2) { animation-delay: 0.2s; }
        .dp-dots span:nth-child(3) { animation-delay: 0.4s; }
        .dp-footer {
            margin-top: 48px; color: #64748B; font-size: 0.72rem;
        }
    </style>
    <div class="dp-loader-wrap">
        <div class="dp-logo-mark">DP</div>
        <h1 class="dp-title">Duarte <span>Performance</span></h1>
        <p class="dp-sub">Gestão Operacional Inteligente</p>
        <div class="dp-ring"></div>
        <div class="dp-bar"><div class="dp-bar-inner"></div></div>
        <p class="dp-status">
            Preparando o ambiente
            <span class="dp-dots"><span></span><span></span><span></span></span>
        </p>
        <p class="dp-footer">Duarte Gestão · Acesso seguro</p>
    </div>
    """,
        unsafe_allow_html=True,
    )
    time.sleep(1.9)
    st.session_state["carregando"] = False
    st.rerun()

# ===================== SESSION STATE =====================
for key, val in {
    "token": None,
    "username": None,
    "nome": None,
    "user_nome": None,
    "role": "Operador",
    "user_role": "Operador",
    "perfil_completo": True,
}.items():
    if key not in st.session_state:
        st.session_state[key] = val


# ===================== HELPERS DE API =====================
def get_headers() -> dict:
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _tratar_sessao_expirada(resp: requests.Response) -> None:
    if resp is not None and resp.status_code == 401:
        st.session_state.clear()
        st.warning("🔒 Sua sessão expirou. Faça login novamente.")
        time.sleep(1.2)
        st.rerun()


def api_get(endpoint: str):
    try:
        resp = requests.get(
            f"{API_URL}{endpoint}", headers=get_headers(), timeout=30
        )
        _tratar_sessao_expirada(resp)
        return resp
    except requests.exceptions.Timeout:
        st.error("⏳ O servidor demorou para responder. Tente novamente.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend.")
        return None
    except Exception as e:
        st.error(f"⚠️ Erro ao buscar dados: {e}")
        return None


def api_post_form(endpoint: str, data: dict = None, files: dict = None):
    try:
        resp = requests.post(
            f"{API_URL}{endpoint}",
            data=data,
            files=files,
            headers=get_headers(),
            timeout=30,
        )
        _tratar_sessao_expirada(resp)
        return resp
    except requests.exceptions.Timeout:
        st.error("⏳ O servidor demorou para responder.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend.")
        return None
    except Exception as e:
        st.error(f"⚠️ Erro ao enviar formulário: {e}")
        return None


def api_post_json(endpoint: str, payload: dict):
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        resp = requests.post(
            f"{API_URL}{endpoint}", json=payload, headers=headers, timeout=30
        )
        _tratar_sessao_expirada(resp)
        return resp
    except requests.exceptions.Timeout:
        st.error("⏳ O servidor demorou para responder.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend.")
        return None
    except Exception as e:
        st.error(f"⚠️ Erro ao enviar requisição: {e}")
        return None


def api_put_json(endpoint: str, payload: dict):
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        resp = requests.put(
            f"{API_URL}{endpoint}", json=payload, headers=headers, timeout=30
        )
        _tratar_sessao_expirada(resp)
        return resp
    except requests.exceptions.Timeout:
        st.error("⏳ O servidor demorou para responder.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend.")
        return None
    except Exception as e:
        st.error(f"⚠️ Erro ao atualizar registro: {e}")
        return None


def api_delete(endpoint: str):
    try:
        resp = requests.delete(
            f"{API_URL}{endpoint}", headers=get_headers(), timeout=30
        )
        _tratar_sessao_expirada(resp)
        return resp
    except requests.exceptions.Timeout:
        st.error("⏳ O servidor demorou para responder.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend.")
        return None
    except Exception as e:
        st.error(f"⚠️ Erro ao excluir registro: {e}")
        return None


@st.cache_data(ttl=30, show_spinner=False)
def carregar_cronograma_cache(_token: str):
    if not _token:
        return None
    try:
        resp = requests.get(
            f"{API_URL}/cronograma/",
            headers={"Authorization": f"Bearer {_token}"},
            timeout=30,
        )
        if resp.status_code == 200:
            dados = resp.json()
            if dados:
                return pd.DataFrame(dados)
    except Exception:
        pass
    return None


def carregar_cronograma():
    return carregar_cronograma_cache(st.session_state.get("token") or "")


# ===================== LOGIN =====================
if not st.session_state.get("token"):
    render_login()
    st.stop()

if st.session_state.get("nome") and not st.session_state.get("user_nome"):
    st.session_state["user_nome"] = st.session_state["nome"]
if st.session_state.get("role") and not st.session_state.get("user_role"):
    st.session_state["user_role"] = st.session_state["role"]

# ===================== SIDEBAR =====================
nome_raw = (
    st.session_state.get("nome")
    or st.session_state.get("username")
    or "Usuário"
)
nome_usuario = nome_raw.strip().title()
iniciais = (
    "".join([p[0] for p in nome_usuario.split()[:2]]).upper()
    if nome_usuario
    else "U"
)
role = st.session_state.get("role", "Operador")
role_norm = str(role).strip().lower()

PAPEIS_GESTAO_NORM = ["admin master", "gestor", "admin", "coordenador"]
PAPEIS_COM_DASH_RELATORIO = [
    "admin master",
    "gestor",
    "admin",
    "coordenador",
    "visualizador",
]

st.sidebar.markdown(
    f"""
<div style='text-align:center;padding:15px;background:rgba(255,255,255,0.05);border-radius:16px;margin-bottom:20px;'>
    <div style='background:linear-gradient(135deg,#FF9200,#E07A00);color:white;width:60px;height:60px;border-radius:50%;margin:0 auto 10px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;font-weight:900;'>{iniciais}</div>
    <div style='font-weight:800;color:#F8FAFC;'>{nome_usuario}</div>
    <div style='color:#FF9200;font-size:0.85rem;'>{role}</div>
</div>
""",
    unsafe_allow_html=True,
)

if role_norm == "operador":
    menus = [
        "🗓️ Escala Semanal",
        "📝 Lançar Execução Diária",
    ]
else:
    menus = []
    if role_norm in PAPEIS_COM_DASH_RELATORIO:
        menus.append("📊 Dashboard Gerencial")
    menus.append("🗓️ Escala Semanal")
    if role_norm in PAPEIS_COM_DASH_RELATORIO:
        menus.append("📑 Relatórios Operacionais")
    menus.append("📝 Lançar Execução Diária")
    if role_norm in PAPEIS_GESTAO_NORM:
        menus.append("✏️ Editor de Apontamentos")
        menus.append("🛡️ Painel Admin")

menu = st.sidebar.radio("Navegação", menus, label_visibility="collapsed")

st.sidebar.markdown(
    """
<style>
    section[data-testid="stSidebar"] button {
        background: linear-gradient(135deg, #FF9200 0%, #E07A00 100%) !important;
        color: white !important;
        font-weight: 700 !important;
        border: none !important;
        border-radius: 12px !important;
        height: 48px !important;
        box-shadow: 0 4px 12px rgba(255, 146, 0, 0.35) !important;
    }
    section[data-testid="stSidebar"] button:hover {
        background: linear-gradient(135deg, #FFA733 0%, #FF9200 100%) !important;
        transform: translateY(-2px) !important;
    }
</style>
""",
    unsafe_allow_html=True,
)

if st.sidebar.button(
    "🚪 Sair do Sistema", use_container_width=True, key="btn_logout"
):
    st.session_state.clear()
    st.rerun()

# ===================== ROTEAMENTO =====================
if menu == "📊 Dashboard Gerencial":
    render_dashboard(api_get)
elif menu == "🗓️ Escala Semanal":
    render_escala(carregar_cronograma)
elif menu == "📑 Relatórios Operacionais":
    render_relatorios()
elif menu == "📝 Lançar Execução Diária":
    render_lancamento(api_post_json, carregar_cronograma)
elif menu == "✏️ Editor de Apontamentos":
    render_editor(api_get, api_put_json, api_delete)
elif menu == "🛡️ Painel Admin":
    render_painel_admin()