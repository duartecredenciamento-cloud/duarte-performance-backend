import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import io
from datetime import datetime, timedelta
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.units import cm

# --- Configuração Premium da Página ---
st.set_page_config(
    page_title="Duarte Performance | Premium",
    page_icon="🟠",
    layout="wide",
    initial_sidebar_state="expanded"
)

API_URL = "http://127.0.0.1:8000"

# --- DIAS DA SEMANA PADRÃO PARA A VISÃO DE AGENDA ---
DIAS_SEMANA_PADRAO = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]

# --- FUNÇÕES DE INTELIGÊNCIA (agora lendo o cronograma real via API, não mais um dicionário fixo) ---
def carregar_cronograma_df():
    """Busca o cronograma real no backend (GET /cronograma/) e devolve sempre um DataFrame,
    mesmo que a API falhe ou não haja nenhum registro ainda."""
    colunas = ["id", "operador", "dia_semana", "atividade", "cliente", "periodo", "data_limite", "status_prazo", "duplicado"]
    try:
        resp = api_get("/cronograma/")
        if resp.status_code == 200:
            dados = resp.json()
            if dados:
                return pd.DataFrame(dados)
    except Exception:
        pass
    return pd.DataFrame(columns=colunas)

def obter_todos_clientes():
    df = carregar_cronograma_df()
    if df.empty or "cliente" not in df.columns:
        return []
    clientes = sorted({c.strip() for c in df["cliente"].dropna() if c.strip()})
    return clientes

def obter_clientes_por_operador(username):
    df = carregar_cronograma_df()
    if df.empty or "operador" not in df.columns:
        return []
    df_op = df[df["operador"].str.lower() == username.lower()]
    if df_op.empty:
        # Sem alocação própria ainda cadastrada: cai para a lista geral, pra não travar o lançamento
        return obter_todos_clientes()
    return sorted({c.strip() for c in df_op["cliente"].dropna() if c.strip()})

# --- 🎨 CSS PREMIUM INJETADO (DESIGN EXECUTIVO) ---
st.markdown("""
<style>
@keyframes fadeIn {
    from { opacity: 0; transform: translateY(20px); }
    to { opacity: 1; transform: translateY(0); }
}
@keyframes pulse {
    0% { transform: scale(1); }
    50% { transform: scale(1.05); }
    100% { transform: scale(1); }
}
.stApp {
    background: linear-gradient(180deg, #F8FAFC 0%, #F1F5F9 100%);
    font-family: 'Inter', system-ui, sans-serif;
}
#MainMenu, header, footer, [data-testid="stHeader"] {visibility: hidden !important; display: none !important;}

/* Sidebar Premium */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #0F172A 0%, #1E2937 100%);
    border-right: 4px solid #F39200;
    box-shadow: 4px 0 20px rgba(0,0,0,0.1);
}
[data-testid="stSidebar"] * { color: #F1F5F9 !important; }

/* Nav Items */
[data-testid="stSidebar"] [data-testid="stRadio"] label {
    border-radius: 12px;
    padding: 14px 18px;
    margin-bottom: 8px;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border: 1px solid rgba(255,255,255,0.1);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
    background: rgba(243, 146, 0, 0.15) !important;
    transform: translateX(8px);
}
[data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {
    background: #F39200 !important;
    color: #0F172A !important;
    font-weight: 700;
    box-shadow: 0 4px 12px rgba(243,146,0,0.3);
}

/* Cards & KPIs */
.kpi-card {
    background: white;
    padding: 28px 24px;
    border-radius: 20px;
    box-shadow: 0 10px 30px rgba(15,23,42,0.08);
    border-left: 7px solid #F39200;
    transition: all 0.4s cubic-bezier(0.4, 0.0, 0.2, 1);
    animation: fadeIn 0.6s ease-out;
}
.kpi-card:hover {
    transform: translateY(-8px);
    box-shadow: 0 20px 40px rgba(15,23,42,0.12);
}
.kpi-title {
    color: #64748B;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}
.kpi-value {
    font-size: 42px;
    font-weight: 900;
    color: #0F172A;
    margin-top: 8px;
    line-height: 1;
}

/* Modern Tables */
.custom-table-container {
    background: white;
    border-radius: 20px;
    overflow: hidden;
    box-shadow: 0 10px 30px rgba(0,0,0,0.06);
    border: 1px solid #E2E8F0;
}
.custom-table {
    width: 100%;
    border-collapse: collapse;
}
.custom-table th {
    background: #0F172A;
    color: white;
    padding: 18px 16px;
    text-align: left;
    font-weight: 700;
    font-size: 13px;
    letter-spacing: 0.6px;
}
.custom-table td {
    padding: 18px 16px;
    border-bottom: 1px solid #F1F5F9;
    color: #334155;
}
.custom-table tr:hover {
    background: #F8FAFC;
}

/* Buttons */
div.stButton > button {
    border-radius: 12px;
    font-weight: 700;
    padding: 12px 28px;
    transition: all 0.3s ease;
}
div.stButton > button[kind="primary"] {
    background: linear-gradient(90deg, #F39200, #E07A00);
    color: white;
    box-shadow: 0 6px 15px rgba(243,146,0,0.25);
}
div.stButton > button:hover {
    transform: translateY(-3px);
    box-shadow: 0 10px 25px rgba(243,146,0,0.35);
}

/* Login */
.login-card {
    background: white;
    padding: 48px 40px;
    border-radius: 28px;
    box-shadow: 0 25px 60px rgba(15,23,42,0.1);
    border: 1px solid #E2E8F0;
    animation: fadeIn 0.8s ease-out;
}

/* =======================================================
   FIX INPUTS (impede fundo azul-escuro no foco / autofill)
   O tema do Streamlit (secondaryBackgroundColor) e o estilo
   nativo de foco do navegador tentam pintar o input de escuro.
   As regras abaixo forçam SEMPRE fundo branco + texto escuro,
   com borda laranja Duarte só quando o campo está focado.
======================================================= */

/* Wrapper do widget (o Streamlit usa BaseWeb, que herda a cor
   secundária do tema para o container do input) */
div[data-baseweb="input"],
div[data-baseweb="base-input"],
div[data-baseweb="textarea"] {
    background-color: #FFFFFF !important;
    border-radius: 10px !important;
    border: 1.5px solid #CBD5E1 !important;
    transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
}

/* Input/textarea propriamente ditos */
.stTextInput input,
.stNumberInput input,
.stTextArea textarea,
input[type="text"],
input[type="password"],
input[type="number"] {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
    -webkit-text-fill-color: #1E293B !important;
    caret-color: #1E293B !important;
    font-weight: 600 !important;
    box-shadow: none !important;
}

/* Foco: SÓ a borda muda, nunca o fundo */
div[data-baseweb="input"]:focus-within,
div[data-baseweb="base-input"]:focus-within,
div[data-baseweb="textarea"]:focus-within {
    background-color: #FFFFFF !important;
    border: 1.5px solid #F39200 !important;
    box-shadow: 0 0 0 3px rgba(243, 146, 0, 0.15) !important;
}
.stTextInput input:focus,
.stNumberInput input:focus,
.stTextArea textarea:focus {
    background-color: #FFFFFF !important;
    color: #1E293B !important;
    outline: none !important;
}

/* Autofill do Chrome/Edge (senha/CPF salvos) — o navegador tenta
   pintar de azul/amarelo por padrão; o truque do box-shadow
   "inset" gigante sobrescreve isso sem quebrar o texto digitado */
input:-webkit-autofill,
input:-webkit-autofill:hover,
input:-webkit-autofill:focus,
input:-webkit-autofill:active {
    -webkit-box-shadow: 0 0 0 100px #FFFFFF inset !important;
    box-shadow: 0 0 0 100px #FFFFFF inset !important;
    -webkit-text-fill-color: #1E293B !important;
    caret-color: #1E293B !important;
    border: 1.5px solid #F39200 !important;
    transition: background-color 9999s ease-in-out 0s !important;
}
</style>
""", unsafe_allow_html=True)

# --- Inicialização de Estado ---
if "token" not in st.session_state: st.session_state.token = None
if "username" not in st.session_state: st.session_state.username = None
if "cpf" not in st.session_state: st.session_state.cpf = None
if "role" not in st.session_state: st.session_state.role = None

def api_get(endpoint):
    if not st.session_state.token:
        return type('obj', (object,), {'status_code': 401, 'json': lambda: {}})()
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        return requests.get(f"{API_URL}{endpoint}", headers=headers, timeout=10)
    except:
        return type('obj', (object,), {'status_code': 500, 'json': lambda: {}})()

def api_post(endpoint, data=None, files=None):
    if not st.session_state.token:
        return type('obj', (object,), {'status_code': 401, 'json': lambda: {}})()
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        return requests.post(f"{API_URL}{endpoint}", data=data, files=files, headers=headers, timeout=10)
    except:
        return type('obj', (object,), {'status_code': 500, 'json': lambda: {}})()

def api_post_json(endpoint, payload):
    """POST com corpo JSON — necessário para endpoints como /usuarios/ e /cronograma/,
    que no FastAPI esperam um Pydantic model no corpo (json=), não form-data (data=)."""
    if not st.session_state.token:
        return type('obj', (object,), {'status_code': 401, 'json': lambda: {}})()
    headers = {"Authorization": f"Bearer {st.session_state.token}"}
    try:
        return requests.post(f"{API_URL}{endpoint}", json=payload, headers=headers, timeout=10)
    except Exception:
        return type('obj', (object,), {'status_code': 500, 'json': lambda: {"detail": "Erro de conexão com o servidor."}})()


def render_html_seguro(html: str):
    st.markdown(" ".join(html.split()), unsafe_allow_html=True)

def gerar_pdf_tabela(df: pd.DataFrame, titulo: str) -> bytes:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=landscape(A4), topMargin=1.5*cm, bottomMargin=1.5*cm, leftMargin=1.5*cm, rightMargin=1.5*cm)
    estilos = getSampleStyleSheet()
    elementos = [Paragraph(f"<b>{titulo}</b>", estilos["Title"]), Spacer(1, 0.5*cm)]
    dados_tabela = [list(df.columns)] + df.astype(str).values.tolist()
    tabela = Table(dados_tabela, repeatRows=1)
    tabela.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0F172A")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F8FAFC")]),
        ("GRID", (0, 0), (-1, -1), 0.6, colors.HexColor("#CBD5E1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("PADDING", (0, 0), (-1, -1), 8),
    ]))
    elementos.append(tabela)
    doc.build(elementos)
    buffer.seek(0)
    return buffer.getvalue()

def botoes_exportacao(df_export: pd.DataFrame, titulo: str, nome_arquivo: str):
    col1, col2 = st.columns(2)
    with col1:
        buffer_xlsx = io.BytesIO()
        with pd.ExcelWriter(buffer_xlsx, engine="openpyxl") as writer:
            df_export.to_excel(writer, index=False, sheet_name=titulo[:30])
        st.download_button("📊 Exportar Excel", data=buffer_xlsx.getvalue(), file_name=f"{nome_arquivo}_{datetime.today().strftime('%d%m%Y')}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", use_container_width=True, type="secondary")
    with col2:
        pdf_bytes = gerar_pdf_tabela(df_export, titulo)
        st.download_button("🧾 Exportar PDF", data=pdf_bytes, file_name=f"{nome_arquivo}_{datetime.today().strftime('%d%m%Y')}.pdf", mime="application/pdf", use_container_width=True, type="primary")

# --- FLUXO DE LOGIN COM CPF ---
if not st.session_state.token:
    st.markdown("<div style='display:flex; justify-content:center; align-items:center; min-height:100vh;'>", unsafe_allow_html=True)
    _, col_central, _ = st.columns([1, 1.1, 1])
    with col_central:
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        
        col_logo1, col_logo2, col_logo3 = st.columns([1, 2, 1])
        with col_logo2:
            if os.path.exists("Logotipo_RGB-03.png"):
                st.image("Logotipo_RGB-03.png", use_container_width=True)
        
        st.markdown("""
            <div style='text-align:center; margin: 30px 0 40px 0;'>
                <h1 style='color:#0F172A; font-size:32px; font-weight:800; margin:0;'>Duarte Performance</h1>
                <p style='color:#64748B; font-size:16px;'>Gestão Inteligente de Operações</p>
            </div>
        """, unsafe_allow_html=True)

        cpf_input = st.text_input("CPF Corporativo", placeholder="000.000.000-00", max_chars=14)
        senha = st.text_input("Senha de Acesso", type="password", placeholder="••••••••")
        
        col_btn1, col_btn2 = st.columns([1,1])
        with col_btn1:
            if st.button("🔑 AUTENTICAR", type="primary", use_container_width=True):
                if not cpf_input or not senha:
                    st.error("❌ CPF e senha são obrigatórios.")
                else:
                    # Sanitização: mantém apenas os dígitos do CPF digitado
                    # (aceita "000.000.000-00", "000 000 000 00", etc.)
                    cpf_limpo = ''.join(filter(str.isdigit, cpf_input))
                    if len(cpf_limpo) != 11:
                        st.error("❌ CPF inválido. Digite os 11 números do CPF.")
                    else:
                        try:
                            resp = requests.post(f"{API_URL}/token", data={"username": cpf_limpo, "password": senha}, timeout=8)
                            if resp.status_code == 200:
                                dados = resp.json()
                                st.session_state.token = dados["access_token"]
                                st.session_state.cpf = cpf_limpo
                                st.session_state.username = dados.get("nome", cpf_limpo)
                                st.session_state.role = dados.get("role", "Operador")
                                st.success("✅ Autenticação bem-sucedida!")
                                st.rerun()
                            else:
                                st.error("❌ CPF ou senha inválidos.")
                        except Exception:
                            st.error("⚠️ Erro de conexão com servidor.")
        with col_btn2:
            st.button("Esqueci senha", use_container_width=True, disabled=True)
        
        st.markdown("</div>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# --- SIDEBAR PREMIUM ---
col_sb1, col_sb2, col_sb3 = st.sidebar.columns([0.1, 2.8, 0.1])
with col_sb2:
    if os.path.exists("Logotipo_RGB-03.png"):
        st.image("Logotipo_RGB-03.png", use_container_width=True)

st.sidebar.markdown(f"""
    <div style='background: rgba(255,255,255,0.08); border-radius:16px; padding:20px; text-align:center; margin:20px 0;'>
        <p style='margin:0; opacity:0.8; font-size:13px;'>LOGADO COMO</p>
        <p style='margin:8px 0 0 0; font-size:19px; font-weight:800; color:#F39200;'>{st.session_state.username.upper()}</p>
        <span style='background:#F39200; color:#0F172A; padding:4px 16px; border-radius:30px; font-size:11px; font-weight:700;'>{st.session_state.role}</span>
    </div>
""", unsafe_allow_html=True)

menu_options = ["🏠 Dashboard Executivo", "📝 Lançar Atividade", "📅 Gestão de Prazos", "🗓️ Escala Comercial"]

# Telas restritas a quem tem permissão de gestão de equipe/segurança,
# conforme os perfis definidos no prompt do sistema:
# Admin Master -> acesso total | Gestor -> operação, sem config. global | Operador -> só o essencial
if st.session_state.role == "Admin Master":
    menu_options += ["👥 Gestão de Equipe", "🔍 Auditoria"]

menu = st.sidebar.radio("Navegação", menu_options, label_visibility="collapsed")

st.sidebar.markdown("<br>"*3, unsafe_allow_html=True)
if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True, type="secondary"):
    st.session_state.token = None
    st.session_state.clear()
    st.rerun()

# NOTA: o registro de auditoria acontece no backend (função registrar_log em main.py),
# de forma automática em ações críticas (login, criação de cronograma, registros, cadastro
# de usuário). Não existe mais uma função local aqui pra evitar um log "fantasma" que
# some ao atualizar a página — a versão real e imutável é a exibida na tela de Auditoria.

# --- TELAS ---
st.markdown("<div style='padding: 0 24px;'>", unsafe_allow_html=True)

if menu == "🏠 Dashboard Executivo":
    st.markdown("<h1 style='color: #0F172A; font-size: 38px; font-weight: 800;'>Dashboard Executivo</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color:#64748B; font-size:16px;'>Visão consolidada da performance operacional.</p>", unsafe_allow_html=True)
    
    resp = api_get("/registros/")
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        if len(df) > 0:
            col_kpi1, col_kpi2, col_kpi3, col_kpi4 = st.columns(4)
            with col_kpi1:
                st.markdown(f"<div class='kpi-card'><div class='kpi-title'>TOTAL ATIVIDADES</div><div class='kpi-value'>{len(df)}</div></div>", unsafe_allow_html=True)
            with col_kpi2:
                sucessos = len(df[df['status'].str.contains("Realizado", na=False)])
                st.markdown(f"<div class='kpi-card' style='border-left-color:#10B981;'><div class='kpi-title'>TAXA DE SUCESSO</div><div class='kpi-value' style='color:#10B981;'>{int(sucessos/len(df)*100) if len(df)>0 else 0}%</div></div>", unsafe_allow_html=True)
            with col_kpi3:
                st.markdown(f"<div class='kpi-card' style='border-left-color:#F59E0B;'><div class='kpi-title'>PENDÊNCIAS</div><div class='kpi-value' style='color:#F59E0B;'>{len(df[df['status'].str.contains('Parcial|Não', na=False)])}</div></div>", unsafe_allow_html=True)
            with col_kpi4:
                st.markdown(f"<div class='kpi-card' style='border-left-color:#3B82F6;'><div class='kpi-title'>OPERADORES ATIVOS</div><div class='kpi-value' style='color:#3B82F6;'>9</div></div>", unsafe_allow_html=True)
            
            tab1, tab2 = st.tabs(["📊 Análise por Status", "👥 Por Operador"])
            with tab1:
                fig = px.pie(df, names='status', title="Distribuição de Status", color_discrete_sequence=px.colors.sequential.Blues)
                st.plotly_chart(fig, use_container_width=True)
            with tab2:
                fig2 = px.bar(df.groupby('operador_nome').size().reset_index(name='Total'), x='operador_nome', y='Total', color='operador_nome')
                st.plotly_chart(fig2, use_container_width=True)
            
            st.subheader("📋 Últimas Atividades")
            st.dataframe(df.tail(10), use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum registro encontrado.")
    else:
        st.warning("Não foi possível carregar dados do dashboard.")

elif menu == "📝 Lançar Atividade":
    st.markdown("<h1 style='color: #0F172A; font-size: 38px; font-weight: 800;'>Lançamento de Atividade</h1>", unsafe_allow_html=True)
    lista_clientes = obter_todos_clientes() if st.session_state.role in ("Admin Master", "Gestor") else obter_clientes_por_operador(st.session_state.username)
    
    with st.form("form_lancamento"):
        col1, col2 = st.columns(2)
        with col1:
            cliente = st.selectbox("Cliente / Conta", lista_clientes)
        with col2:
            status = st.selectbox("Status", ["Realizado Total", "Realizado Parcial", "Não Realizado"])
        
        justificativa = st.text_area("Justificativa / Observações", height=140, placeholder="Descreva detalhes técnicos ou evidências...")
        evidencia = st.file_uploader("Evidência (PDF, Imagem, Planilha)", type=["pdf","png","jpg","xlsx"])
        
        submitted = st.form_submit_button("💾 REGISTRAR ATIVIDADE", type="primary", use_container_width=True)
        if submitted:
            payload = {
                "operador_nome": st.session_state.username,
                "cliente_nome": cliente,
                "status": status,
                "justificativa": justificativa or ""
            }
            files = {"evidencia": (evidencia.name, evidencia.getvalue(), evidencia.type)} if evidencia else None
            resp = api_post("/registros/", data=payload, files=files)
            if resp.status_code == 200:
                st.success("✅ Atividade registrada com sucesso!")
                st.balloons()
            else:
                st.error("Erro ao registrar atividade.")

elif menu == "📅 Gestão de Prazos":
    st.markdown("<h1 style='color: #0F172A; font-size: 38px; font-weight: 800;'>Gestão de Prazos & SLA</h1>", unsafe_allow_html=True)
    resp = api_get("/cronograma/")
    if resp.status_code == 200:
        df = pd.DataFrame(resp.json())
        if len(df) > 0:
            def farol_sla(row):
                try:
                    dl = datetime.strptime(row.get("data_limite", ""), "%d/%m/%Y")
                    dias = (dl - datetime.now()).days
                    if dias < 0: return "🔴 ATRASADO"
                    elif dias <= 3: return "🟡 ALERTA"
                    return "🟢 NO PRAZO"
                except:
                    return "⚪ SEM DATA"
            
            df["SLA"] = df.apply(farol_sla, axis=1)
            
            k1, k2, k3 = st.columns(3)
            with k1: st.metric("Atrasados", len(df[df["SLA"].str.contains("ATRASADO")]))
            with k2: st.metric("Em Alerta", len(df[df["SLA"].str.contains("ALERTA")]))
            with k3: st.metric("No Prazo", len(df[df["SLA"].str.contains("NO PRAZO")]))
            
            botoes_exportacao(df, "Relatório SLA", "SLA_Duarte")
            st.dataframe(df, use_container_width=True)
        else:
            st.info("Nenhum prazo cadastrado.")
    else:
        st.error("Falha ao carregar cronograma.")

elif menu == "🗓️ Escala Comercial":
    st.markdown("<h1 style='color: #0F172A; font-size: 38px; font-weight: 800;'>Escala Comercial Semanal</h1>", unsafe_allow_html=True)

    df_crono = carregar_cronograma_df()

    if df_crono.empty:
        st.info("📭 Nenhum cronograma cadastrado ainda. Assim que o Gestor montar a escala da semana, ela aparece aqui automaticamente.")
    else:
        df_crono = df_crono.fillna("")
        operadores_todos = sorted(o for o in df_crono["operador"].unique() if o)
        dias_presentes = [d for d in DIAS_SEMANA_PADRAO if d in set(df_crono["dia_semana"].unique())]
        dias_extra = sorted(set(df_crono["dia_semana"].unique()) - set(DIAS_SEMANA_PADRAO) - {""})
        dias_exibir = dias_presentes + dias_extra  # não perde dado se alguém cadastrar um dia fora do padrão

        st.markdown("### Visão Geral da Equipe")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Colaboradores", len(operadores_todos))
        with col2:
            mask_ferias = df_crono["cliente"].str.contains("FÉRIAS", case=False) | df_crono["atividade"].str.contains("FÉRIAS", case=False)
            st.metric("Em Férias", df_crono[mask_ferias]["operador"].nunique())
        with col3:
            mask_integral = df_crono["periodo"].str.contains("Integral", case=False)
            st.metric("Turno Integral", df_crono[mask_integral]["operador"].nunique())
        with col4:
            qtd_duplicados = int(df_crono["duplicado"].sum()) if "duplicado" in df_crono.columns else 0
            st.metric("⚠️ Duplicidades", qtd_duplicados)

        if qtd_duplicados > 0:
            st.warning("⚠️ Existe(m) cliente(s) repetido(s) para o mesmo operador em mais de um dia da semana. Não bloqueia o cadastro, apenas revise se é intencional.")

        filtro = st.multiselect("Filtrar Colaboradores", operadores_todos)
        df_view = df_crono[df_crono["operador"].isin(filtro)] if filtro else df_crono

        botoes_exportacao(df_view.drop(columns=["duplicado"], errors="ignore"), "Escala Comercial", "Escala_Duarte")

        # Cada célula pode ter mais de um item no mesmo dia (ex: dois clientes na mesma manhã)
        def celula_escala(sub_df):
            if sub_df.empty:
                return "—"
            partes = []
            for _, item in sub_df.iterrows():
                texto = item["cliente"] or item["atividade"] or "—"
                aviso = " ⚠️" if item.get("duplicado") else ""
                if "FÉRIAS" in texto.upper():
                    partes.append(f"<span style='background:#DBEAFE;color:#1E40AF;padding:4px 12px;border-radius:9999px;'>🌴 {texto}</span>")
                elif "SUPORTE" in texto.upper():
                    partes.append(f"<span style='background:#F1F5F9;color:#475569;padding:4px 12px;border-radius:9999px;'>🛠️ {texto}</span>")
                else:
                    partes.append(f"<span style='font-weight:600;'>{texto}{aviso}</span>")
            return "<br>".join(partes)

        html_rows = []
        for op in sorted(o for o in df_view["operador"].unique() if o):
            sub_op = df_view[df_view["operador"] == op]
            periodos_op = sub_op["periodo"].replace("", pd.NA).dropna()
            turno = periodos_op.mode().iloc[0] if not periodos_op.empty else "—"
            cells = "".join(f"<td>{celula_escala(sub_op[sub_op['dia_semana'] == d])}</td>" for d in dias_exibir)
            html_rows.append(f"<tr><td><b>{op}</b></td><td>{turno}</td>{cells}</tr>")

        cabecalho_dias = "".join(f"<th>{d}</th>" for d in dias_exibir)
        tabela = (
            "<div class='custom-table-container'>"
            "<table class='custom-table'>"
            f"<thead><tr><th>Colaborador</th><th>Turno</th>{cabecalho_dias}</tr></thead>"
            f"<tbody>{''.join(html_rows)}</tbody>"
            "</table>"
            "</div>"
        )
        st.markdown(tabela, unsafe_allow_html=True)

elif menu == "👥 Gestão de Equipe":
    st.markdown("<h1 style='color: #0F172A; font-size: 38px; font-weight: 800;'>Gestão de Equipe</h1>", unsafe_allow_html=True)
    if st.session_state.role != "Admin Master":
        st.error("🔒 Acesso restrito ao Admin Master.")
        st.stop()
    st.info("🔧 Módulo de Gestão de Equipe - Cadastro e Acompanhamento de Operadores")

    # Departamentos reais cadastrados no banco (via criar_admin.py ou futuro CRUD)
    resp_deptos = api_get("/departamentos/")
    deptos = resp_deptos.json() if resp_deptos.status_code == 200 else []
    mapa_deptos = {d["nome"]: d["id"] for d in deptos}

    tab_gestao1, tab_gestao2 = st.tabs(["👤 Adicionar Membro", "📋 Lista de Equipe"])
    with tab_gestao1:
        if not mapa_deptos:
            st.warning("⚠️ Nenhum departamento cadastrado ainda. Rode o `criar_admin.py` ou cadastre um departamento antes de adicionar colaboradores.")
        with st.form("add_member"):
            nome = st.text_input("Nome Completo")
            cpf = st.text_input("CPF", placeholder="000.000.000-00")
            senha_provisoria = st.text_input("Senha Provisória", type="password", help="O colaborador poderá trocar depois do primeiro acesso.")
            role = st.selectbox("Cargo", ["Operador", "Gestor", "Admin Master"])
            departamento_nome = st.selectbox("Departamento", list(mapa_deptos.keys())) if mapa_deptos else None

            if st.form_submit_button("Adicionar à Equipe", type="primary", use_container_width=True):
                cpf_limpo = ''.join(filter(str.isdigit, cpf))
                if not nome or not cpf_limpo or not senha_provisoria:
                    st.error("❌ Nome, CPF e senha provisória são obrigatórios.")
                elif len(cpf_limpo) != 11:
                    st.error("❌ CPF inválido. Digite os 11 números do CPF.")
                elif not mapa_deptos:
                    st.error("❌ Cadastre um departamento antes de adicionar colaboradores.")
                else:
                    payload = {
                        "cpf": cpf_limpo,
                        "nome": nome,
                        "role": role,
                        "departamento_id": mapa_deptos[departamento_nome],
                        "password": senha_provisoria
                    }
                    resp_novo = api_post_json("/usuarios/", payload)
                    if resp_novo.status_code == 200:
                        st.success(f"✅ {nome} adicionado(a) com sucesso! O log de auditoria já foi gravado automaticamente pelo backend.")
                        st.balloons()
                    elif resp_novo.status_code == 400:
                        st.error(f"❌ {resp_novo.json().get('detail', 'CPF já cadastrado.')}")
                    elif resp_novo.status_code == 403:
                        st.error("🔒 Sua sessão não tem permissão de Admin Master no backend.")
                    else:
                        st.error(f"⚠️ Erro ao cadastrar (status {resp_novo.status_code}). Verifique se o backend está rodando.")

    with tab_gestao2:
        resp_usuarios = api_get("/usuarios/")
        if resp_usuarios.status_code == 200 and resp_usuarios.json():
            mapa_deptos_inverso = {d["id"]: d["nome"] for d in deptos}
            equipe_df = pd.DataFrame(resp_usuarios.json())[["nome", "cpf", "role", "departamento_id"]]
            equipe_df["departamento_id"] = equipe_df["departamento_id"].map(mapa_deptos_inverso).fillna("—")
            equipe_df.columns = ["Nome", "CPF", "Cargo", "Departamento"]
            st.dataframe(equipe_df, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum colaborador cadastrado ainda (ou sem permissão para consultar).")

elif menu == "🔍 Auditoria":
    st.markdown("<h1 style='color: #0F172A; font-size: 38px; font-weight: 800;'>Auditoria do Sistema</h1>", unsafe_allow_html=True)
    if st.session_state.role != "Admin Master":
        st.error("🔒 Acesso restrito ao Admin Master.")
        st.stop()
    st.subheader("Histórico de Ações (registro imutável, direto do banco)")

    resp_audit = api_get("/auditoria/")
    if resp_audit.status_code == 200:
        dados_audit = resp_audit.json()
        if dados_audit:
            audit_df = pd.DataFrame(dados_audit)
            audit_df["timestamp"] = pd.to_datetime(audit_df["timestamp"]).dt.strftime("%d/%m/%Y %H:%M:%S")
            audit_df = audit_df.rename(columns={
                "timestamp": "Data/Hora", "usuario_nome": "Usuário", "usuario_cpf": "CPF",
                "ip_origem": "IP de Origem", "acao": "Ação", "detalhes": "Detalhes"
            })[["Data/Hora", "Usuário", "CPF", "Ação", "Detalhes", "IP de Origem"]]

            falhas_login = int(audit_df["Ação"].str.contains("LOGIN_FAILED").sum())
            if falhas_login > 0:
                st.warning(f"⚠️ {falhas_login} tentativa(s) de login falha registrada(s) no log — vale checar se não é força bruta.")

            col1, col2 = st.columns(2)
            with col1:
                filtro_acao = st.multiselect("Filtrar por Ação", sorted(audit_df["Ação"].unique()))
            with col2:
                filtro_usuario = st.multiselect("Filtrar por Usuário", sorted(u for u in audit_df["Usuário"].unique() if u))

            audit_view = audit_df.copy()
            if filtro_acao: audit_view = audit_view[audit_view["Ação"].isin(filtro_acao)]
            if filtro_usuario: audit_view = audit_view[audit_view["Usuário"].isin(filtro_usuario)]

            botoes_exportacao(audit_view, "Auditoria", "Auditoria_Duarte")
            st.dataframe(audit_view, use_container_width=True, hide_index=True)
        else:
            st.info("Nenhum evento de auditoria registrado ainda.")
    else:
        st.error("Não foi possível carregar os logs de auditoria no momento.")

st.markdown("</div>", unsafe_allow_html=True)