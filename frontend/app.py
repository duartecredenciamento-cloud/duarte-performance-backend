import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime
from zoneinfo import ZoneInfo

# Importação dos módulos das telas
from views.login import render_login
from views.dashboard import render_dashboard
from views.escala import render_escala
from views.relatorios import render_relatorios
from views.lancamento import render_lancamento
from views.editor import render_editor

# ===================== 1. CONFIGURAÇÃO E FUSO HORÁRIO =====================
FUSO_BR = ZoneInfo("America/Sao_Paulo")
API_URL = "https://duarte-performance-backend.onrender.com"
PAPEIS_GESTAO = ["Admin Master", "Gestor"]

st.set_page_config(
    page_title="Duarte Performance | Gestão Operacional",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Carregamento seguro do CSS com codificação UTF-8
try:
    with open("styles.css", "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception as e:
    st.warning("⚠️ Não foi possível aplicar o stylesheet customizado. Usando padrão.")

# ===================== 2. GERENCIAMENTO DE ESTADO (SESSION STATE) =====================
ESTADOS_INICIAIS = {
    "token": None,
    "username": None,
    "nome": None,
    "role": "Operador",
    "perfil_completo": True
}

for key, val in ESTADOS_INICIAIS.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ===================== 3. HELPERS DE API CENTRALIZADOS =====================
def get_headers():
    return {"Authorization": f"Bearer {st.session_state.token}"}

def api_get(endpoint):
    try:
        return requests.get(f"{API_URL}{endpoint}", headers=get_headers(), timeout=15)
    except Exception as e:
        st.error(f"⚠️ Erro ao conectar com o servidor: {e}")
        return None

def api_post_form(endpoint, data=None, files=None):
    try:
        return requests.post(f"{API_URL}{endpoint}", data=data, files=files, headers=get_headers(), timeout=20)
    except Exception as e:
        st.error(f"⚠️ Erro ao enviar dados: {e}")
        return None

def api_post_json(endpoint, payload):
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        return requests.post(f"{API_URL}{endpoint}", json=payload, headers=headers, timeout=20)
    except Exception as e:
        st.error(f"⚠️ Erro ao enviar requisição: {e}")
        return None

@st.cache_data(ttl=30, show_spinner=False)
def carregar_cronograma_cache(_token):
    try:
        resp = requests.get(f"{API_URL}/cronograma/", headers={"Authorization": f"Bearer {_token}"}, timeout=15)
        if resp.status_code == 200 and resp.json():
            return pd.DataFrame(resp.json())
    except Exception:
        pass
    return pd.DataFrame()

def carregar_cronograma():
    return carregar_cronograma_cache(st.session_state.token)

# ===================== 4. GUILD E SEGURANÇA (AUTENTICAÇÃO) =====================
if not st.session_state.get("token"):
    render_login()
    st.stop()

# ===================== 5. SIDEBAR EXECUTIVA =====================
nome_raw = st.session_state.get("nome") or st.session_state.get("username") or "Usuário"
nome_usuario = nome_raw.strip().title()
partes_nome = nome_usuario.split()
iniciais = "".join([n[0] for n in partes_nome[:2]]).upper() if len(partes_nome) > 1 else nome_usuario[:2].upper()
role = st.session_state.get("role", "Operador")

# Perfil do Usuário Estilizado
st.sidebar.markdown(f'''
<div style='text-align: center; padding: 15px 10px; background: rgba(255,255,255,0.04); border-radius: 16px; margin-bottom: 20px; border: 1px solid rgba(255,255,255,0.08);'>
    <div style='background: linear-gradient(135deg, #FF9200 0%, #E07A00 100%); color: #FFF; width: 54px; height: 54px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-weight: 900; font-size: 1.2rem; margin: 0 auto 10px auto; box-shadow: 0 4px 15px rgba(255,146,0,0.3);'>
        {iniciais}
    </div>
    <div style='color: #F8FAFC; font-weight: 800; font-size: 16px; letter-spacing: 0.3px;'>{nome_usuario}</div>
    <div style='color: #FF9200; font-size: 11px; font-weight: 700; text-transform: uppercase; letter-spacing: 1px; margin-top: 2px;'>{role}</div>
</div>
''', unsafe_allow_html=True)

# Construção do Menu Dinâmico
menus_disponiveis = [
    "📊 Dashboard Gerencial", 
    "🗓️ Escala Semanal", 
    "📑 Relatórios Operacionais", 
    "📝 Lançar Execução Diária"
]

if role in PAPEIS_GESTAO:
    menus_disponiveis.append("✏️ Editor de Apontamentos")

menu = st.sidebar.radio("Navegação Principal", menus_disponiveis, label_visibility="collapsed")

st.sidebar.markdown("---")

# Botão de Logout com limpeza completa de estado
if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True):
    st.session_state.clear()
    st.cache_data.clear()
    st.rerun()

# Badge de versão/status na base da sidebar
st.sidebar.markdown("""
<div style="text-align: center; font-size: 11px; color: #64748B; margin-top: 15px;">
    Duarte Performance v2.4 • Active Session
</div>
""", unsafe_allow_html=True)

# ===================== 6. ROTEAMENTO DAS VISÕES (VIEWS) =====================
if menu == "📊 Dashboard Gerencial":
    render_dashboard(api_get)
elif menu == "🗓️ Escala Semanal":
    render_escala(carregar_cronograma)
elif menu == "📑 Relatórios Operacionais":
    render_relatorios(api_get)
elif menu == "📝 Lançar Execução Diária":
    render_lancamento(api_post_form)
elif menu == "✏️ Editor de Apontamentos":
    render_editor(api_get)
