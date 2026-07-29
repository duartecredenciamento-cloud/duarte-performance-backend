import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import requests
import streamlit as st

# Importação das Views
from views.login import render_login
from views.dashboard import render_dashboard
from views.escala import render_escala
from views.relatorios import render_relatorios
from views.lancamento import render_lancamento
from views.editor import render_editor

# ===================== CONFIGURAÇÃO =====================
# ⚠️ st.set_page_config precisa ser SEMPRE a primeira instrução Streamlit do arquivo.
st.set_page_config(
    page_title="Duarte Performance | Gestão Operacional",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="expanded"
)

FUSO_BR = ZoneInfo("America/Sao_Paulo")
API_URL = os.getenv("BACKEND_URL", "https://duarte-performance-backend-production.up.railway.app")  # URL do backend (padrão localhost para dev local)
PAPEIS_GESTAO = ["Admin Master", "Gestor", "Admin", "Coordenador"]

# CSS
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
try:
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception as e:
    st.warning(f"⚠️ CSS não carregado: {e}")

# Depois do st.set_page_config e carregamento do CSS

# ===================== TELA DE CARREGAMENTO =====================
if "carregando" not in st.session_state:
    st.session_state["carregando"] = True

if st.session_state["carregando"]:
    st.markdown("""
    <div style="
        display:flex;
        flex-direction:column;
        align-items:center;
        justify-content:center;
        height:80vh;
        text-align:center;
    ">
        <h1 style="color:#001E57; font-size:2.5rem;">Duarte Performance</h1>
        <p style="color:#64748B;">Carregando sistema...</p>
    </div>
    """, unsafe_allow_html=True)
    
    time.sleep(1.5)  # tempo de carregamento
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


# ===================== HELPERS DE API (camada completa de comunicação) =====================
def get_headers() -> dict:
    """Monta o cabeçalho de autenticação com o token JWT salvo na sessão."""
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _tratar_sessao_expirada(resp: requests.Response) -> None:
    """Se o backend disser que o token expirou (401), derruba a sessão local
    pra forçar um novo login limpo na próxima interação, em vez de deixar a
    pessoa presa numa tela autenticada que na verdade não funciona mais."""
    if resp is not None and resp.status_code == 401:
        st.session_state.clear()
        st.warning("🔒 Sua sessão expirou. Faça login novamente.")
        time.sleep(1.2)
        st.rerun()


def api_get(endpoint: str):
    """GET autenticado no backend. Retorna a Response ou None em caso de falha de rede."""
    try:
        resp = requests.get(f"{API_URL}{endpoint}", headers=get_headers(), timeout=30)
        _tratar_sessao_expirada(resp)
        return resp
    except requests.exceptions.Timeout:
        st.error("⏳ O servidor demorou para responder. O Render pode estar acordando — tente novamente em instantes.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend. Verifique se o serviço no Render está no ar.")
        return None
    except Exception as e:
        st.error(f"⚠️ Erro ao buscar dados: {e}")
        return None


def api_post_form(endpoint: str, data: dict = None, files: dict = None):
    """POST autenticado enviando dados como formulário (form-urlencoded/multipart)."""
    try:
        resp = requests.post(f"{API_URL}{endpoint}", data=data, files=files, headers=get_headers(), timeout=30)
        _tratar_sessao_expirada(resp)
        return resp
    except requests.exceptions.Timeout:
        st.error("⏳ O servidor demorou para responder. O Render pode estar acordando — tente novamente em instantes.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend. Verifique se o serviço no Render está no ar.")
        return None
    except Exception as e:
        st.error(f"⚠️ Erro ao enviar formulário: {e}")
        return None


def api_post_json(endpoint: str, payload: dict):
    """POST autenticado enviando um corpo JSON."""
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        resp = requests.post(f"{API_URL}{endpoint}", json=payload, headers=headers, timeout=30)
        _tratar_sessao_expirada(resp)
        return resp
    except requests.exceptions.Timeout:
        st.error("⏳ O servidor demorou para responder. O Render pode estar acordando — tente novamente em instantes.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend. Verifique se o serviço no Render está no ar.")
        return None
    except Exception as e:
        st.error(f"⚠️ Erro ao enviar requisição: {e}")
        return None


def api_put_json(endpoint: str, payload: dict):
    """PUT autenticado enviando um corpo JSON (usado para editar registros/cronograma)."""
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        resp = requests.put(f"{API_URL}{endpoint}", json=payload, headers=headers, timeout=30)
        _tratar_sessao_expirada(resp)
        return resp
    except requests.exceptions.Timeout:
        st.error("⏳ O servidor demorou para responder. O Render pode estar acordando — tente novamente em instantes.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend. Verifique se o serviço no Render está no ar.")
        return None
    except Exception as e:
        st.error(f"⚠️ Erro ao atualizar registro: {e}")
        return None


def api_delete(endpoint: str):
    """DELETE autenticado."""
    try:
        resp = requests.delete(f"{API_URL}{endpoint}", headers=get_headers(), timeout=30)
        _tratar_sessao_expirada(resp)
        return resp
    except requests.exceptions.Timeout:
        st.error("⏳ O servidor demorou para responder. O Render pode estar acordando — tente novamente em instantes.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("❌ Não foi possível conectar ao backend. Verifique se o serviço no Render está no ar.")
        return None
    except Exception as e:
        st.error(f"⚠️ Erro ao excluir registro: {e}")
        return None


@st.cache_data(ttl=30, show_spinner=False)
def carregar_cronograma_cache(_token):
    try:
        resp = requests.get(f"{API_URL}/cronograma/", headers={"Authorization": f"Bearer {_token}"}, timeout=30)
        if resp.status_code == 200:
            return pd.DataFrame(resp.json())
    except Exception:
        pass
    return pd.DataFrame()


def carregar_cronograma():
    return carregar_cronograma_cache(st.session_state.get("token"))


# ===================== LOGIN =====================
# Nunca carrega nada do dashboard sem autenticação — a checagem do token
# tem que vir antes de qualquer outra coisa na tela.
if not st.session_state.get("token"):
    render_login()
    st.stop()

# Mantém as variáveis "espelho" (user_nome/user_role) sincronizadas, já que
# algumas views mais antigas ainda podem consultar esses nomes alternativos.
if st.session_state.get("nome") and not st.session_state.get("user_nome"):
    st.session_state["user_nome"] = st.session_state["nome"]
if st.session_state.get("role") and not st.session_state.get("user_role"):
    st.session_state["user_role"] = st.session_state["role"]

# ===================== SIDEBAR =====================
nome_raw = st.session_state.get("nome") or st.session_state.get("username") or "Usuário"
nome_usuario = nome_raw.strip().title()
iniciais = "".join([p[0] for p in nome_usuario.split()[:2]]).upper() if nome_usuario else "U"
role = st.session_state.get("role", "Operador")

st.sidebar.markdown(f'''
<div style='text-align:center;padding:15px;background:rgba(255,255,255,0.05);border-radius:16px;margin-bottom:20px;'>
    <div style='background:linear-gradient(135deg,#FF9200,#E07A00);color:white;width:60px;height:60px;border-radius:50%;margin:0 auto 10px;display:flex;align-items:center;justify-content:center;font-size:1.5rem;font-weight:900;'>{iniciais}</div>
    <div style='font-weight:800;color:#F8FAFC;'>{nome_usuario}</div>
    <div style='color:#FF9200;font-size:0.85rem;'>{role}</div>
</div>
''', unsafe_allow_html=True)

menus = ["📊 Dashboard Gerencial", "🗓️ Escala Semanal", "📑 Relatórios Operacionais", "📝 Lançar Execução Diária"]
if role in PAPEIS_GESTAO:
    menus.append("✏️ Editor de Apontamentos")

menu = st.sidebar.radio("Navegação", menus, label_visibility="collapsed")

# ===================== BOTÃO SAIR =====================
st.sidebar.markdown("""
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
""", unsafe_allow_html=True)

if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True, key="btn_logout"):
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