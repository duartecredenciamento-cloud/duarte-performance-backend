import os
import inspect
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
st.set_page_config(
    page_title="Duarte Performance | Gestão Operacional",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="expanded"
)

FUSO_BR = ZoneInfo("America/Sao_Paulo")
API_URL = os.getenv("BACKEND_URL", "https://duarte-performance-backend.onrender.com")
PAPEIS_GESTAO = ["Admin Master", "Gestor", "Admin", "Coordenador"]

# CSS
css_path = os.path.join(os.path.dirname(__file__), "styles.css")
try:
    with open(css_path, "r", encoding="utf-8") as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
except Exception as e:
    st.warning(f"⚠️ CSS não carregado: {e}")

# ===================== SESSION STATE =====================
for key, val in {
    "token": None,
    "username": None,
    "nome": None,
    "user_nome": None,
    "role": "Operador",
    "user_role": "Operador",
    "perfil_completo": True
}.items():
    if key not in st.session_state:
        st.session_state[key] = val

# ===================== HELPERS API =====================
def get_headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}

def api_get(endpoint):
    try:
        return requests.get(f"{API_URL}{endpoint}", headers=get_headers(), timeout=15)
    except Exception as e:
        st.error(f"Erro ao buscar dados: {e}")
        return None

def api_post_json(endpoint, payload):
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        return requests.post(f"{API_URL}{endpoint}", json=payload, headers=headers, timeout=20)
    except Exception as e:
        st.error(f"Erro ao enviar: {e}")
        return None

def api_post_form(endpoint, data=None, files=None):
    try:
        return requests.post(f"{API_URL}{endpoint}", data=data, files=files, headers=get_headers(), timeout=20)
    except Exception as e:
        st.error(f"Erro ao enviar formulário: {e}")
        return None

def api_put_json(endpoint, payload):
    try:
        headers = get_headers()
        headers["Content-Type"] = "application/json"
        return requests.put(f"{API_URL}{endpoint}", json=payload, headers=headers, timeout=20)
    except Exception as e:
        st.error(f"Erro ao atualizar: {e}")
        return None

def api_delete(endpoint):
    try:
        return requests.delete(f"{API_URL}{endpoint}", headers=get_headers(), timeout=20)
    except Exception as e:
        st.error(f"Erro ao excluir: {e}")
        return None

@st.cache_data(ttl=30, show_spinner=False)
def carregar_cronograma_cache(_token):
    try:
        resp = requests.get(f"{API_URL}/cronograma/", headers={"Authorization": f"Bearer {_token}"}, timeout=15)
        if resp.status_code == 200:
            return pd.DataFrame(resp.json())
    except:
        pass
    return pd.DataFrame()

def carregar_cronograma():
    return carregar_cronograma_cache(st.session_state.get("token"))

# ===================== LOGIN =====================
if not st.session_state.get("token"):
    render_login()
    st.stop()

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

if st.sidebar.button("🚪 Sair do Sistema", use_container_width=True):
    st.session_state.clear()
    st.rerun()

# ===================== ROTEAMENTO =====================
if menu == "📊 Dashboard Gerencial":
    render_dashboard(api_get)
elif menu == "🗓️ Escala Semanal":
    render_escala(carregar_cronograma)
elif menu == "📑 Relatórios Operacionais":
    render_relatorios(api_get)
elif menu == "📝 Lançar Execução Diária":
    render_lancamento(api_post_json)
elif menu == "✏️ Editor de Apontamentos":
    render_editor(api_get, api_put_json, api_delete)