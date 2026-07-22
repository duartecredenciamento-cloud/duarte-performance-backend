import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import io
from datetime import datetime

import utils

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
    :root {
        --primary-dark: #0F172A;
        --primary-light: #1E293B;
        --accent-orange: #F39200;
        --accent-hover: #E07A00;
        --bg-body: #F8FAFC;
        --bg-card: #FFFFFF;
        --text-muted: #64748B;
        --border-color: #E2E8F0;
    }
    .stApp {
        background-color: var(--bg-body);
        background-image: radial-gradient(circle at 50% 0%, rgba(243, 146, 0, 0.04) 0%, transparent 60%);
        font-family: 'Segoe UI', system-ui, sans-serif;
    }
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--primary-dark) 0%, #020617 100%);
        border-right: 1px solid rgba(255, 255, 255, 0.05);
    }
    [data-testid="stSidebar"] * { color: #F8FAFC !important; }
    .login-card {
        background: var(--bg-card); padding: 50px; border-radius: 24px;
        box-shadow: 0 10px 40px -10px rgba(15,23,42,0.1); max-width: 480px;
        margin: auto; border: 1px solid var(--border-color);
    }
    div[data-baseweb="input"], div[data-baseweb="base-input"], div[data-baseweb="textarea"] {
        background-color: #FFFFFF !important; border-radius: 10px !important; border: 1.5px solid #CBD5E1 !important;
    }
    .stTextInput input, .stTextArea textarea, input[type="text"], input[type="password"] {
        background-color: #FFFFFF !important; color: #0F172A !important;
        -webkit-text-fill-color: #0F172A !important; font-weight: 600 !important; font-size: 16px !important;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="textarea"]:focus-within {
        border-color: var(--accent-orange) !important; box-shadow: 0 0 0 3px rgba(243, 146, 0, 0.15) !important;
    }
    .kpi-card {
        background: var(--bg-card); padding: 24px; border-radius: 16px; border-left: 5px solid var(--accent-orange);
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.03); transition: transform 0.2s ease;
    }
    .kpi-card:hover { transform: translateY(-3px); }
    .stButton>button[kind="primary"] {
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-light) 100%);
        color: white !important; border-radius: 10px; font-weight: 700; padding: 12px 24px; transition: all 0.2s ease;
    }
    .stButton>button[kind="primary"]:hover {
        background: linear-gradient(135deg, var(--accent-orange) 0%, var(--accent-hover) 100%) !important;
        transform: translateY(-1px);
    }
    div[role="radiogroup"] > label {
        padding: 12px 15px !important; border-radius: 12px !important; margin-bottom: 4px !important; transition: all 0.2s ease !important;
    }
    div[role="radiogroup"] > label:hover { background: rgba(255, 255, 255, 0.05) !important; transform: translateX(5px); }
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
if not st.session_state.token:
    st.markdown("<div style='padding-top: 8vh;'>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;color:#0F172A;font-weight:900;margin:0;'>Duarte Performance</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#64748B;font-size:14px;margin-bottom:20px;'>Departamento de Credenciamento</p>", unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["🔑 Entrar", "🆕 Criar Conta"])

        with tab_login:
            username_input = st.text_input("Usuário", placeholder="ex: erick_duarte", key="login_username")
            senha_input = st.text_input("Senha de Acesso", type="password", placeholder="Digite sua senha", key="login_senha")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("🔑 ACESSAR PLATAFORMA", type="primary", use_container_width=True):
                if not username_input or not senha_input:
                    st.warning("Por favor, preencha usuário e senha.")
                else:
                    try:
                        resp = requests.post(f"{API_URL}/token", data={"username": username_input, "password": senha_input}, timeout=10)
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.update({
                                "token": data["access_token"],
                                "username": data.get("username"),
                                "nome": data.get("nome"),
                                "role": data.get("role", "Operador"),
                                "perfil_completo": data.get("perfil_completo", True)
                            })
                            st.success("Autenticação realizada com sucesso!")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("Usuário ou senha incorretos.")
                    except Exception:
                        # NUNCA logar por fallback local. Se a API estiver fora do ar, o
                        # usuário precisa saber disso, não ser jogado dentro do sistema
                        # como Admin Master fingindo que deu certo.
                        st.error("⚠️ Não foi possível conectar ao servidor. Tente novamente em instantes.")

        with tab_signup:
            st.caption("Crie sua conta pra acessar a plataforma. Você entra automaticamente como Operador.")
            nome_signup = st.text_input("Nome Completo", key="signup_nome")
            username_signup = st.text_input("Usuário (será seu login)", placeholder="ex: erick_duarte", key="signup_username")
            email_signup = st.text_input("E-mail", placeholder="seuemail@exemplo.com", key="signup_email")
            telefone_signup = st.text_input("WhatsApp", placeholder="(00) 00000-0000", key="signup_telefone")
            senha_signup = st.text_input("Crie uma senha", type="password", key="signup_senha")
            senha_confirma = st.text_input("Confirme a senha", type="password", key="signup_senha2")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button("✅ CRIAR MINHA CONTA", type="primary", use_container_width=True):
                if not all([nome_signup, username_signup, senha_signup, senha_confirma]):
                    st.warning("Nome, usuário e senha são obrigatórios.")
                elif senha_signup != senha_confirma:
                    st.error("As senhas não conferem.")
                else:
                    payload = {
                        "username": username_signup, "password": senha_signup, "nome": nome_signup,
                        "email": email_signup or None, "telefone": telefone_signup or None
                    }
                    try:
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
                            st.success("Conta criada! Entrando...")
                            time.sleep(0.5)
                            st.rerun()
                        elif resp.status_code == 400:
                            st.error(resp.json().get("detail", "Este usuário já existe."))
                        else:
                            st.error(f"Erro ao criar conta: {resp.text}")
                    except Exception:
                        st.error("⚠️ Não foi possível conectar ao servidor. Tente novamente em instantes.")

        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# ===================== 2.1. COMPLETAR PERFIL (primeiro acesso de conta criada pelo Admin) =====================
if not st.session_state.perfil_completo:
    st.markdown("<div style='padding-top: 8vh;'>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align:center;color:#0F172A;font-weight:900;'>Complete seu Perfil</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#64748B;font-size:14px;margin-bottom:20px;'>Sua conta foi criada pelo Admin. Antes de continuar, confirme seus dados.</p>", unsafe_allow_html=True)

        nome_completar = st.text_input("Nome Completo", key="completar_nome")
        email_completar = st.text_input("E-mail", placeholder="seuemail@exemplo.com", key="completar_email")
        telefone_completar = st.text_input("WhatsApp", placeholder="(00) 00000-0000", key="completar_telefone")

        if st.button("✅ Salvar e Continuar", type="primary", use_container_width=True):
            if not nome_completar:
                st.warning("O nome completo é obrigatório.")
            else:
                payload = {"nome": nome_completar, "email": email_completar or None, "telefone": telefone_completar or None}
                resp = api_put_json("/usuarios/me", payload)
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.nome = data.get("nome")
                    st.session_state.perfil_completo = True
                    st.success("Perfil atualizado!")
                    time.sleep(0.5)
                    st.rerun()
                else:
                    st.error(f"Erro ao salvar perfil: {resp.text}")
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()




# ===================== 3. CONTEXTO DO PERFIL (SIDEBAR) =====================
nome_usuario = (st.session_state.nome or st.session_state.username or "").upper()
partes_nome = nome_usuario.split()
iniciais = "".join([n[0] for n in partes_nome[:2]]) if len(partes_nome) > 1 else nome_usuario[0:2]
role = st.session_state.role

st.sidebar.markdown(f"""
<div style='background: rgba(255,255,255,0.03); border: 1px solid rgba(255,255,255,0.05); border-radius: 16px; padding: 20px 10px; text-align: center; margin-bottom: 25px;'>
    <div style='background: linear-gradient(135deg, #F39200 0%, #E07A00 100%); color: #0F172A; width: 55px; height: 55px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 20px; font-weight: 900; margin: 0 auto 10px auto;'>{iniciais}</div>
    <p style='color: #F8FAFC; font-size: 16px; font-weight: 700; margin: 0 0 5px 0;'>{nome_usuario}</p>
    <span style='padding: 4px 12px; border-radius: 20px; font-size: 10px; font-weight: 800; text-transform: uppercase; color: #0F172A; background: #F39200;'>{role}</span>
</div>
""", unsafe_allow_html=True)

# Menu dinâmico: Editor de Apontamentos, Gestão de Equipe e Auditoria só aparecem pra quem tem permissão
menus_disponiveis = ["📊 Dashboard Gerencial", "🗓️ Escala Semanal", "📑 Relatórios Operacionais", "📝 Lançar Execução Diária"]
if role in PAPEIS_GESTAO:
    menus_disponiveis.append("✏️ Editor de Apontamentos")
if role == "Admin Master":
    menus_disponiveis.append("👥 Gestão de Equipe")
    menus_disponiveis.append("🔐 Auditoria e Acessos")

st.sidebar.markdown("<p style='color: #64748B; font-size: 11px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 10px; margin-left: 5px;'>Navegação Principal</p>", unsafe_allow_html=True)
menu = st.sidebar.radio("Navegação do Sistema", menus_disponiveis, label_visibility="collapsed")

st.sidebar.markdown("<br>" * 3, unsafe_allow_html=True)
if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True, type="secondary"):
    st.session_state.clear()
    st.rerun()


# ===================== 4. DIRECIONAMENTO DAS ABAS =====================

# --- ABA 1: DASHBOARD GERENCIAL ---
if menu == "📊 Dashboard Gerencial":
    st.markdown("<h1 style='color: #0F172A; font-weight: 800;'>Dashboard Gerencial de Performance</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B;'>Métricas consolidadas de produtividade do Credenciamento.</p>", unsafe_allow_html=True)

    resp_reg = api_get("/registros/")
    if resp_reg.status_code != 200:
        st.error("Não foi possível carregar os registros do servidor.")
        st.stop()

    dados_reg = resp_reg.json()
    if not dados_reg:
        st.info("📭 Ainda não há nenhum apontamento lançado no sistema.")
        st.stop()

    df_reg = pd.DataFrame(dados_reg)

    # --- Filtros Avançados por Cliente e Operador ---
    fcol1, fcol2 = st.columns(2)
    with fcol1:
        filtro_operador = st.multiselect("Filtrar por Operador", sorted(df_reg["operador_nome"].dropna().unique()))
    with fcol2:
        filtro_cliente = st.multiselect("Filtrar por Cliente", sorted(df_reg["cliente_nome"].dropna().unique()))

    df_view = df_reg.copy()
    if filtro_operador:
        df_view = df_view[df_view["operador_nome"].isin(filtro_operador)]
    if filtro_cliente:
        df_view = df_view[df_view["cliente_nome"].isin(filtro_cliente)]

    total = len(df_view)
    realizado_total = int((df_view["status"] == "Realizado Total").sum())
    realizado_parcial = int((df_view["status"] == "Realizado Parcial").sum())
    nao_realizado = int((df_view["status"] == "Não Realizado").sum())
    nao_informado = int((df_view["status"] == "Não Informado").sum())

    c1, c2, c3, c4 = st.columns(4)
    c1.markdown(f"<div class='kpi-card'><b>Total de Apontamentos</b><h2>{total}</h2></div>", unsafe_allow_html=True)
    c2.markdown(f"<div class='kpi-card' style='border-left-color:#10B981'><b style='color:#10B981'>Realizado Total</b><h2>{realizado_total}</h2></div>", unsafe_allow_html=True)
    c3.markdown(f"<div class='kpi-card' style='border-left-color:#F59E0B'><b style='color:#F59E0B'>Realizado Parcial</b><h2>{realizado_parcial}</h2></div>", unsafe_allow_html=True)
    c4.markdown(f"<div class='kpi-card' style='border-left-color:#EF4444'><b style='color:#EF4444'>Não Realizado / Não Informado</b><h2>{nao_realizado + nao_informado}</h2></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    g1, g2 = st.columns(2)
    with g1:
        if total > 0:
            fig_pie = px.pie(df_view, names="status", title="Pipeline Operacional (SLA)", hole=0.4,
                              color_discrete_map={"Realizado Total": "#10B981", "Realizado Parcial": "#F39200", "Não Realizado": "#EF4444", "Não Informado": "#94A3B8"})
            st.plotly_chart(fig_pie, use_container_width=True)
    with g2:
        if total > 0:
            fig_bar = px.bar(df_view, x="operador_nome", color="status", title="Produtividade por Operador",
                              color_discrete_map={"Realizado Total": "#10B981", "Realizado Parcial": "#F39200", "Não Realizado": "#EF4444", "Não Informado": "#94A3B8"})
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("### Volumetria por Cliente")
    if total > 0:
        fig_cliente = px.bar(df_view["cliente_nome"].value_counts().reset_index(), x="cliente_nome", y="count",
                              title="Apontamentos por Cliente", color_discrete_sequence=["#0F172A"])
        st.plotly_chart(fig_cliente, use_container_width=True)


# --- ABA 2: ESCALA SEMANAL (CRUD completo + importação de planilha) ---
elif menu == "🗓️ Escala Semanal":
    st.markdown("<h1 style='color: #0F172A; font-weight: 800;'>Cronograma e Agenda Semanal</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B;'>Matriz operacional de alocação de contas e turnos da Gestão Comercial.</p>", unsafe_allow_html=True)

    df_crono = carregar_cronograma()

    if df_crono.empty:
        st.info("📭 Nenhum item cadastrado no cronograma ainda.")
    else:
        df_crono = df_crono.fillna("")
        qtd_duplicados = int(df_crono["duplicado"].sum()) if "duplicado" in df_crono.columns else 0
        if qtd_duplicados > 0:
            duplicados_texto = df_crono[df_crono["duplicado"] == True][["operador", "cliente"]].drop_duplicates()
            linhas_aviso = "\n".join(f"- **{r['operador']}** com alocação repetida em **{r['cliente']}**" for _, r in duplicados_texto.iterrows())
            st.warning(f"⚠ **Sinalização de Duplicidade Semanal:**\n\n{linhas_aviso}")

        dias_padrao = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
        dias_presentes = [d for d in dias_padrao if d in set(df_crono["dia_semana"].unique())]

        def estilo_celula(val):
            v = str(val).strip().upper()
            if v == "FÉRIAS":
                return 'background-color: #E0F2FE; color: #0369A1; font-weight: bold; text-align: center;'
            elif "SUPORTE" in v:
                return 'color: #475569; background-color: #F1F5F9; font-style: italic;'
            elif v in ("", "X"):
                return 'color: #94A3B8; text-align: center;'
            return 'color: #1E293B;'

        pivot_linhas = []
        for op in sorted(o for o in df_crono["operador"].unique() if o):
            linha = {"Operador": op}
            sub = df_crono[df_crono["operador"] == op]
            for d in dias_presentes:
                itens_dia = sub[sub["dia_semana"] == d]
                linha[d] = " / ".join(itens_dia["cliente"].tolist()) if not itens_dia.empty else ""
            pivot_linhas.append(linha)
        df_pivot = pd.DataFrame(pivot_linhas)
        st.dataframe(df_pivot.style.map(estilo_celula), use_container_width=True, hide_index=True)

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


# --- ABA 3: RELATÓRIOS OPERACIONAIS (filtros de verdade, sem dado fixo) ---
elif menu == "📑 Relatórios Operacionais":
    st.markdown("<h1 style='color: #0F172A; font-weight: 800; letter-spacing:-0.5px;'>Relatório Principal de Produtividade</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B;'>Filtros avançados e extração de dados auditáveis das rotinas operacionais.</p>", unsafe_allow_html=True)

    resp_reg = api_get("/registros/")
    if resp_reg.status_code != 200:
        st.error("Não foi possível carregar os registros do servidor.")
        st.stop()

    dados_reg = resp_reg.json()
    if not dados_reg:
        st.info("📭 Ainda não há nenhum apontamento lançado no sistema.")
        st.stop()

    df_principal = pd.DataFrame(dados_reg)
    df_principal["data_registro"] = pd.to_datetime(df_principal["data_registro"])
    df_principal["Data"] = df_principal["data_registro"].dt.strftime("%d/%m/%Y")
    dias_pt_map = {0: "Segunda", 1: "Terça", 2: "Quarta", 3: "Quinta", 4: "Sexta", 5: "Sábado", 6: "Domingo"}
    df_principal["Dia"] = df_principal["data_registro"].dt.weekday.map(dias_pt_map)
    df_principal = df_principal.rename(columns={
        "cliente_nome": "Cliente", "operador_nome": "Operador", "status": "Status", "justificativa": "Observação"
    })

    # --- Filtros que realmente filtram o DataFrame (reativos via widgets nativos) ---
    f1, f2, f3 = st.columns(3)
    with f1:
        periodo_sel = f1.date_input("Período", value=(), format="DD/MM/YYYY")
    with f2:
        operador_sel = f2.multiselect("Filtrar por Operador", sorted(df_principal["Operador"].unique()))
    with f3:
        status_sel = f3.multiselect("Status de SLA", sorted(df_principal["Status"].unique()))

    df_view = df_principal.copy()
    if isinstance(periodo_sel, tuple) and len(periodo_sel) == 2:
        ini, fim = periodo_sel
        df_view = df_view[(df_view["data_registro"].dt.date >= ini) & (df_view["data_registro"].dt.date <= fim)]
    if operador_sel:
        df_view = df_view[df_view["Operador"].isin(operador_sel)]
    if status_sel:
        df_view = df_view[df_view["Status"].isin(status_sel)]

    st.caption(f"{len(df_view)} registro(s) encontrado(s) com os filtros atuais.")

    def colorir_relatorio(row):
        styles = [''] * len(row)
        status = str(row['Status']).strip()
        if status == "Realizado Total":
            bg_color = "background-color: #ECFDF5; color: #065F46; font-weight: 500;"
        elif status == "Realizado Parcial":
            bg_color = "background-color: #FFFBEB; color: #92400E; font-weight: 500;"
        elif status == "Não Realizado":
            bg_color = "background-color: #FEF2F2; color: #991B1B; font-weight: bold;"
        elif status == "Não Informado":
            bg_color = "background-color: #F1F5F9; color: #475569; font-style: italic;"
        else:
            bg_color = ""
        styles[row.index.get_loc('Status')] = bg_color
        styles[row.index.get_loc('Operador')] = 'font-weight: 600; color: #1E293B;'
        return styles

    colunas_exibir = ["Data", "Dia", "Cliente", "Operador", "Status", "Observação"]
    df_exibir = df_view[colunas_exibir]
    st.dataframe(df_exibir.style.apply(colorir_relatorio, axis=1), use_container_width=True, hide_index=True)

    towrite = io.BytesIO()
    with pd.ExcelWriter(towrite, engine='xlsxwriter') as writer:
        df_exibir.to_excel(writer, sheet_name='Performance_Duarte', index=False)

    st.markdown("<br>", unsafe_allow_html=True)
    st.download_button(
        label="📥 EXPORTAR PLANILHA CONSOLIDADA (.XLSX)",
        data=towrite.getvalue(),
        file_name=f"Duarte_Performance_{datetime.now().strftime('%d%m%Y')}.xlsx",
        mime="application/vnd.ms-excel",
        type="primary",
        use_container_width=True
    )


# --- ABA 4: LANÇAR EXECUÇÃO DIÁRIA (cliente filtrado pela escala real do dia) ---
elif menu == "📝 Lançar Execução Diária":
    st.markdown("<h1 style='color: #0F172A; font-weight: 800; letter-spacing:-0.5px;'>Apontamento de Execução Diária</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B;'>Registre suas atividades operacionais com validação dinâmica e anexo de evidências.</p>", unsafe_allow_html=True)

    dia_hoje = utils.dia_semana_atual()
    st.markdown(f"""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; padding: 12px 16px; border-radius: 8px; margin-bottom: 20px;">
            <span style="color: #64748B; font-size: 14px;">🕒 <b>Registro Auditado:</b> {datetime.now().strftime('%d/%m/%Y')} ({dia_hoje})</span>
            <span style="color: #E2E8F0; margin: 0 10px;">|</span>
            <span style="color: #64748B; font-size: 14px;">👤 <b>Operador:</b> {(st.session_state.nome or "").upper()}</span>
        </div>
    """, unsafe_allow_html=True)

    df_crono = carregar_cronograma()
    clientes_do_dia = utils.clientes_do_operador_no_dia(df_crono, st.session_state.nome or "", dia_hoje)

    lista_clientes = ["Selecione..."] + clientes_do_dia + ["Suporte", "Outro (não está na escala de hoje)"]
    if not clientes_do_dia:
        st.info("ℹ️ Não encontramos nenhum cliente atribuído a você na escala de hoje. Selecione 'Suporte' ou 'Outro'.")

    c_alt1, c_alt2 = st.columns(2)
    cliente_sel = c_alt1.selectbox("Selecione o Cliente Trabalhado", lista_clientes, key="cliente_diario")

    # Sub-filtro condicional: quando escolhe Suporte, abre um segundo campo pra dizer qual cliente
    cliente_final = cliente_sel
    if cliente_sel == "Suporte":
        cliente_suporte_destino = c_alt1.selectbox("Suporte para qual cliente?", ["Selecione..."] + sorted(set(clientes_do_dia)) if clientes_do_dia else ["Selecione..."], key="cliente_suporte_destino")
        if cliente_suporte_destino != "Selecione...":
            cliente_final = utils.formatar_cliente_suporte(cliente_suporte_destino)
    elif cliente_sel == "Outro (não está na escala de hoje)":
        cliente_final = c_alt1.text_input("Digite o nome do cliente", key="cliente_outro")

    status_sel = c_alt2.selectbox("Status Final do Trabalho", ["Selecione...", "Realizado Total", "Realizado Parcial", "Não Realizado"], key="status_diario")

    obs_texto = ""
    if status_sel in ["Realizado Parcial", "Não Realizado"]:
        st.markdown(f"""
            <div style="background: #FFFBEB; border-left: 4px solid #F59E0B; padding: 12px; border-radius: 4px; margin: 15px 0 5px 0;">
                <strong style="color: #B45309;">⚠ Justificativa Obrigatória</strong><br>
                <span style="color: #78350F; font-size: 13px;">Explique detalhadamente o motivo do status ser <b>{status_sel}</b>.</span>
            </div>
        """, unsafe_allow_html=True)
        obs_texto = st.text_area(
            "Detalhamento Operacional da Ocorrência", height=120,
            placeholder="Devido a reunião não foi possível realizar totalmente as tarefas do cliente",
            key="justificativa_diaria"
        )

    st.markdown("#### 📎 Comprovações e Evidências")
    arquivo_evidencia = st.file_uploader("Arraste ou selecione o print da sua tela/sistema", type=["png", "jpg", "jpeg", "pdf", "xlsx"], key="evidencia_diaria")

    if arquivo_evidencia is not None and arquivo_evidencia.type in ["image/png", "image/jpeg"]:
        with st.expander("👁️ Visualizar Print Carregado", expanded=True):
            st.image(arquivo_evidencia, caption="Evidência Capturada", use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if st.button("🚀 ENVIAR APONTAMENTO DIÁRIO", type="primary", use_container_width=True):
        if cliente_sel == "Selecione..." or status_sel == "Selecione..." or not cliente_final or cliente_final == "Selecione...":
            st.error("Por favor, selecione o cliente e o status antes de salvar.")
        elif status_sel in ["Realizado Parcial", "Não Realizado"] and not obs_texto.strip():
            st.error("A justificativa detalhada é estritamente obrigatória para auditoria interna.")
        else:
            payload = {
                "operador_nome": st.session_state.nome,
                "cliente_nome": cliente_final,
                "status": status_sel,
                "justificativa": obs_texto or ""
            }
            files = {"evidencia": (arquivo_evidencia.name, arquivo_evidencia.getvalue(), arquivo_evidencia.type)} if arquivo_evidencia else None
            resp = api_post_form("/registros/", data=payload, files=files)
            if resp.status_code == 200:
                st.success("Perfeito! Apontamento gravado com sucesso no ecossistema de dados.")
                st.balloons()
            else:
                st.error(f"Erro ao gravar o apontamento: {resp.text}")


# --- ABA 5: EDITOR DE APONTAMENTOS (Gestor / Admin Master) ---
elif menu == "✏️ Editor de Apontamentos":
    st.markdown("<h1 style='color: #0F172A; font-weight: 800;'>Editor de Apontamentos</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B;'>Corrija um apontamento enviado incorretamente. Toda edição fica registrada na Auditoria automaticamente.</p>", unsafe_allow_html=True)

    if role not in PAPEIS_GESTAO:
        st.error("🔒 Acesso restrito a Gestores e Administradores.")
        st.stop()

    resp_reg = api_get("/registros/")
    if resp_reg.status_code != 200:
        st.error("Não foi possível carregar os registros do servidor.")
        st.stop()

    dados_reg = resp_reg.json()
    if not dados_reg:
        st.info("📭 Nenhum apontamento lançado ainda.")
        st.stop()

    df_reg = pd.DataFrame(dados_reg)
    df_reg["data_registro"] = pd.to_datetime(df_reg["data_registro"]).dt.strftime("%d/%m/%Y %H:%M")

    opcoes = {
        f"#{r['id']} — {r['operador_nome']} — {r['cliente_nome']} — {r['status']} ({r['data_registro']})": r
        for _, r in df_reg.iterrows()
    }
    escolha = st.selectbox("Selecione o apontamento para editar", list(opcoes.keys()))
    item_sel = opcoes[escolha]

    with st.form("form_editar_apontamento"):
        cliente_edit = st.text_input("Cliente", value=item_sel["cliente_nome"])
        status_edit = st.selectbox(
            "Status", ["Realizado Total", "Realizado Parcial", "Não Realizado", "Não Informado"],
            index=["Realizado Total", "Realizado Parcial", "Não Realizado", "Não Informado"].index(item_sel["status"])
            if item_sel["status"] in ["Realizado Total", "Realizado Parcial", "Não Realizado", "Não Informado"] else 0
        )
        obs_edit = st.text_area("Observação / Justificativa", value=item_sel.get("justificativa") or "")

        if st.form_submit_button("💾 Salvar Correção", type="primary"):
            payload = {"cliente_nome": cliente_edit, "status": status_edit, "justificativa": obs_edit}
            resp = api_put_json(f"/registros/{int(item_sel['id'])}", payload)
            if resp.status_code == 200:
                st.success("Apontamento corrigido! A alteração já está registrada na Auditoria.")
                st.rerun()
            else:
                st.error(f"Erro ao editar: {resp.text}")

    st.markdown("---")
    st.markdown("### 🔄 Verificação de Pendências do Dia")
    st.caption(
        "Marca automaticamente como 'Não Informado' qualquer atividade da escala de hoje que ainda não "
        "tenha sido lançada. Ideal rodar isso 1x ao fim do expediente (ou configurar um Render Cron Job "
        "chamando esse mesmo endpoint diariamente, em vez de depender de alguém clicar aqui)."
    )
    if st.button("Verificar Pendências de Hoje"):
        resp = api_post_json("/registros/marcar-pendentes/", {})
        if resp.status_code == 200:
            qtd = resp.json().get("marcados_como_nao_informado", 0)
            st.success(f"{qtd} apontamento(s) pendente(s) marcado(s) como 'Não Informado'.")
        else:
            st.error(f"Erro ao verificar pendências: {resp.text}")


# --- ABA GESTÃO DE EQUIPE (Admin Master cria contas: username, senha provisória, papel, departamento) ---
elif menu == "👥 Gestão de Equipe":
    st.markdown("<h1 style='color: #0F172A; font-weight: 800;'>Gestão de Equipe</h1>", unsafe_allow_html=True)
    if role != "Admin Master":
        st.error("🔒 Acesso restrito ao Admin Master.")
        st.stop()

    tab_add, tab_list = st.tabs(["➕ Adicionar Membro", "📋 Lista de Equipe"])

    with tab_add:
        st.caption(
            "Você pode cadastrar só o essencial (usuário, senha provisória, papel) e deixar "
            "Nome/E-mail/WhatsApp em branco — a pessoa completa isso sozinha no primeiro login dela."
        )
        resp_deptos = api_get("/departamentos/")
        deptos = resp_deptos.json() if resp_deptos.status_code == 200 else []
        opcoes_depto = {d["nome"]: d["id"] for d in deptos} if deptos else {}

        with st.form("form_add_membro"):
            c1, c2 = st.columns(2)
            username_novo = c1.text_input("Usuário (login)", placeholder="ex: erick_duarte")
            senha_provisoria = c2.text_input("Senha Provisória", type="password")
            c3, c4 = st.columns(2)
            role_novo = c3.selectbox("Cargo", ["Operador", "Gestor", "Admin Master"])
            depto_novo = c4.selectbox("Departamento", ["(Nenhum)"] + list(opcoes_depto.keys()))
            st.markdown("###### Opcional — pode deixar em branco pra pessoa completar depois")
            c5, c6, c7 = st.columns(3)
            nome_novo = c5.text_input("Nome Completo (opcional)")
            email_novo = c6.text_input("E-mail (opcional)")
            telefone_novo = c7.text_input("WhatsApp (opcional)")

            if st.form_submit_button("Adicionar à Equipe", type="primary"):
                if not username_novo or not senha_provisoria:
                    st.warning("Usuário e senha provisória são obrigatórios.")
                else:
                    payload = {
                        "username": username_novo, "password": senha_provisoria, "role": role_novo,
                        "departamento_id": opcoes_depto.get(depto_novo),
                        "nome": nome_novo or None, "email": email_novo or None, "telefone": telefone_novo or None
                    }
                    resp = api_post_json("/usuarios/", payload)
                    if resp.status_code == 200:
                        st.success(f"Colaborador '{username_novo}' adicionado com sucesso!")
                        st.rerun()
                    elif resp.status_code == 400:
                        st.error(resp.json().get("detail", "Este usuário já existe."))
                    else:
                        st.error(f"Erro ao cadastrar: {resp.text}")

    with tab_list:
        resp_usuarios = api_get("/usuarios/")
        if resp_usuarios.status_code == 200 and resp_usuarios.json():
            df_equipe = pd.DataFrame(resp_usuarios.json())
            df_equipe["perfil_completo"] = df_equipe["perfil_completo"].map({True: "✅ Completo", False: "⏳ Pendente"})
            df_equipe = df_equipe.rename(columns={
                "username": "Usuário", "nome": "Nome", "email": "E-mail", "telefone": "WhatsApp",
                "role": "Cargo", "perfil_completo": "Perfil"
            })[["Usuário", "Nome", "E-mail", "WhatsApp", "Cargo", "Perfil"]]
            st.dataframe(df_equipe, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum colaborador cadastrado ainda.")


# --- ABA 6: AUDITORIA E ACESSOS (Admin Master, dados reais do backend) ---
elif menu == "🔐 Auditoria e Acessos":
    st.markdown("<h1 style='color: #0F172A; font-weight: 800; letter-spacing:-0.5px;'>Módulo de Auditoria e Segurança (LGPD)</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: #64748B;'>Rastreamento completo e imutável de transações, edições de cronograma e justificativas.</p>", unsafe_allow_html=True)

    if role != "Admin Master":
        st.error("🔒 Acesso restrito ao Admin Master.")
        st.stop()

    resp_audit = api_get("/auditoria/")
    if resp_audit.status_code != 200:
        st.error("Não foi possível carregar os logs de auditoria.")
        st.stop()

    dados_audit = resp_audit.json()
    if not dados_audit:
        st.info("Nenhum evento de auditoria registrado ainda.")
        st.stop()

    df_audit = pd.DataFrame(dados_audit)
    df_audit["timestamp"] = pd.to_datetime(df_audit["timestamp"]).dt.strftime("%d/%m/%Y %H:%M:%S")

    total_eventos = len(df_audit)
    falhas_login = int(df_audit["acao"].str.contains("LOGIN_FAILED").sum())
    alteracoes_cronograma = int(df_audit["acao"].str.contains("CRONOGRAMA").sum())

    c_sec1, c_sec2, c_sec3 = st.columns(3)
    c_sec1.markdown(f"<div class='kpi-card' style='border-left-color: #10B981;'><b>Eventos Registrados</b><h3 style='color:#10B981; margin:5px 0 0 0;'>{total_eventos}</h3></div>", unsafe_allow_html=True)
    c_sec2.markdown(f"<div class='kpi-card' style='border-left-color: #EF4444;'><b>Tentativas de Login Falhas</b><h3 style='color:#EF4444; margin:5px 0 0 0;'>{falhas_login}</h3></div>", unsafe_allow_html=True)
    c_sec3.markdown(f"<div class='kpi-card' style='border-left-color: #F59E0B;'><b>Alterações de Escala</b><h3 style='color:#F59E0B; margin:5px 0 0 0;'>{alteracoes_cronograma}</h3></div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 🔍 Histórico de Operações")

    df_audit_exibir = df_audit.rename(columns={
        "timestamp": "Data/Hora", "usuario_nome": "Nome", "usuario_login": "Usuário",
        "ip_origem": "IP de Origem", "acao": "Ação", "detalhes": "Detalhes"
    })[["Data/Hora", "Nome", "Usuário", "Ação", "Detalhes", "IP de Origem"]]

    col1, col2 = st.columns(2)
    with col1:
        filtro_acao = st.multiselect("Filtrar por Ação", sorted(df_audit_exibir["Ação"].unique()))
    with col2:
        filtro_usuario = st.multiselect("Filtrar por Usuário", sorted(u for u in df_audit_exibir["Usuário"].unique() if u))

    df_audit_view = df_audit_exibir.copy()
    if filtro_acao:
        df_audit_view = df_audit_view[df_audit_view["Ação"].isin(filtro_acao)]
    if filtro_usuario:
        df_audit_view = df_audit_view[df_audit_view["Usuário"].isin(filtro_usuario)]

    st.dataframe(df_audit_view, use_container_width=True, hide_index=True)
    st.caption("🔒 Os logs gerados nesta plataforma são imutáveis e não podem ser apagados ou editados por nenhum perfil, incluindo Admin Master.")