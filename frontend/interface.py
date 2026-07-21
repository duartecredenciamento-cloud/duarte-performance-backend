import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
import os

# Importa as funções pesadas do módulo utils (se existir)
try:
    import utils
except ImportError:
    utils = None

# -----------------------------------------------------------------------------
# 1. CONFIGURAÇÃO DA PÁGINA E CSS GLOBAL
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Duarte Performance - Gestão Operacional",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed" # Começa fechado por padrão
)

# ESTILIZAÇÃO GLOBAL E REMOÇÃO DO MENU AUTOMÁTICO
st.markdown("""
    <style>
        /* 1. MATA O MENU NATIVO DE ARQUIVOS DO STREAMLIT PARA SEMPRE */
        [data-testid="stSidebarNav"] { display: none !important; }
        
        /* 2. Cores da Duarte Gestão */
        .stApp { background-color: #F4F6F9; }
        [data-testid="stSidebar"] { background-color: #0A1128 !important; }
        [data-testid="stSidebar"] * { color: #FFFFFF !important; }
        
        /* 3. Botões em Destaque */
        div.stButton > button:first-child {
            background-color: #F26419; 
            color: #FFFFFF; 
            border: none; 
            border-radius: 6px;
            font-weight: bold;
            transition: all 0.3s ease;
        }
        div.stButton > button:hover {
            background-color: #D95615; 
            color: #FFFFFF;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. CONTROLE DE SESSÃO E OCULTAÇÃO DA SIDEBAR NO LOGIN
# -----------------------------------------------------------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "https://duarte-performance-backend.onrender.com")

if 'logged_in' not in st.session_state:
    st.session_state.logged_in = False
if 'token' not in st.session_state:
    st.session_state.token = None
if 'user' not in st.session_state:
    st.session_state.user = None
if 'role' not in st.session_state:
    st.session_state.role = "operador"

if 'df_escala' not in st.session_state:
    st.session_state.df_escala = pd.DataFrame(columns=['DATA', 'OPERADOR', 'CLIENTE'])

if 'df_apontamentos' not in st.session_state:
    st.session_state.df_apontamentos = pd.DataFrame(columns=[
        'ID', 'DATA', 'OPERADOR', 'CLIENTE', 'STATUS', 'OBSERVACAO'
    ])

# 🚨 TRAVA DE SEGURANÇA: SE NÃO ESTIVER LOGADO, ESCONDE A SIDEBAR INTEIRA 🚨
if not st.session_state.logged_in:
    st.markdown("""
        <style>
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="collapsedControl"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 3. TELA DE LOGIN (COM SUPORTE A COLD START DO RENDER)
# -----------------------------------------------------------------------------
def tela_login():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<h2 style='text-align: center; color: #0A1128;'>Duarte Performance</h2>", unsafe_allow_html=True)
        st.markdown("<h4 style='text-align: center; color: #6C757D;'>Login do Sistema</h4>", unsafe_allow_html=True)
        st.divider()

        with st.form("form_login"):
            usuario = st.text_input("Usuário", placeholder="Digite seu usuário")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha")
            btn_entrar = st.form_submit_button("Entrar", use_container_width=True)

            if btn_entrar:
                if not usuario or not senha:
                    st.warning("Preencha todos os campos!")
                    return

                try:
                    # TIMEOUT AUMENTADO PARA 60s (Suporta o boot do backend no Render)
                    response = requests.post(
                        f"{BACKEND_URL}/token",
                        data={"username": usuario, "password": senha},
                        timeout=60 
                    )

                    if response.status_code == 200:
                        data = response.json()
                        st.session_state.logged_in = True
                        st.session_state.token = data.get("access_token")
                        st.session_state.user = usuario
                        
                        if usuario.lower() in ["admin", "abraao", "gestor"]:
                            st.session_state.role = "Gestor"
                        else:
                            st.session_state.role = "Operador"

                        st.success("Login realizado!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
                        
                except requests.exceptions.Timeout:
                    st.error("O servidor está iniciando. Aguarde 30 segundos e clique em Entrar novamente.")
                except Exception as e:
                    st.error("Erro de conexão com o backend. Verifique se a API está online.")

# -----------------------------------------------------------------------------
# 4. MÓDULOS DE INTERFACE DO SISTEMA
# -----------------------------------------------------------------------------

def aba_dashboard():
    st.header("📈 Dashboard Gerencial")
    df = st.session_state.df_apontamentos

    if df.empty:
        st.info("Nenhum dado de execução registrado até o momento.")
        return

    col1, col2 = st.columns(2)
    with col1:
        ops = ["Todos"] + list(df['OPERADOR'].dropna().unique())
        filtro_op = st.selectbox("Filtrar por Operador", ops, key="dash_op")
    with col2:
        clis = ["Todos"] + list(df['CLIENTE'].dropna().unique())
        filtro_cli = st.selectbox("Filtrar por Cliente", clis, key="dash_cli")

    df_dash = df.copy()
    if filtro_op != "Todos":
        df_dash = df_dash[df_dash['OPERADOR'] == filtro_op]
    if filtro_cli != "Todos":
        df_dash = df_dash[df_dash['CLIENTE'] == filtro_cli]

    kpi1, kpi2, kpi3 = st.columns(3)
    kpi1.metric("Total Apontamentos", len(df_dash))
    kpi2.metric("Concluídos", len(df_dash[df_dash['STATUS'] == 'Concluído']))
    kpi3.metric("Pendentes", len(df_dash[df_dash['STATUS'].isin(['Pendente', 'Impedido'])]))


def aba_escala_semanal():
    st.header("📅 Escala Semanal")
    arquivo = st.file_uploader("Selecione o arquivo de escala", type=['xlsx', 'csv'])

    if arquivo:
        try:
            df_temp = pd.read_csv(arquivo) if arquivo.name.endswith('.csv') else pd.read_excel(arquivo)
            st.session_state.df_escala = df_temp
            st.success("Escala carregada!")
        except Exception as e:
            st.error(f"Erro: {e}")

    df_editado = st.data_editor(st.session_state.df_escala, num_rows="dynamic", use_container_width=True)

    if st.button("💾 Salvar Alterações"):
        st.session_state.df_escala = df_editado
        st.success("Escala atualizada!")


def aba_relatorios():
    st.header("📊 Relatórios Operacionais")
    df = st.session_state.df_apontamentos

    if df.empty:
        st.warning("Sem dados para gerar relatórios.")
        return

    st.dataframe(df, use_container_width=True, hide_index=True)


def aba_lancar_execucao():
    st.header("📝 Lançar Execução Diária")
    hoje = date.today()

    col1, col2 = st.columns(2)
    with col1:
        cliente_sel = st.selectbox("Cliente", ["Qualicorp", "Amil", "Bradesco", "Suporte", "Outro"])
    with col2:
        status_trabalho = st.selectbox("Status", ["Concluído", "Pendente", "Impedido", "Em Andamento"])

    obs = st.text_area("Observações")

    if st.button("🚀 ENVIAR APONTAMENTO", use_container_width=True):
        novo_registro = {
            'ID': len(st.session_state.df_apontamentos) + 1,
            'DATA': hoje.strftime('%Y-%m-%d'),
            'OPERADOR': st.session_state.user,
            'CLIENTE': cliente_sel,
            'STATUS': status_trabalho,
            'OBSERVACAO': obs
        }
        st.session_state.df_apontamentos = pd.concat(
            [st.session_state.df_apontamentos, pd.DataFrame([novo_registro])],
            ignore_index=True
        )
        st.success("Apontamento registrado com sucesso!")


def aba_editor_apontamentos():
    st.header("⚙️ Editor de Apontamentos")

    if st.session_state.role not in ["Gestor", "Admin"]:
        st.error("🚫 Acesso Negado: Apenas Gestores podem editar apontamentos.")
        return

    df = st.session_state.df_apontamentos
    if df.empty:
        st.warning("Não há registros.")
        return

    id_selecionado = st.selectbox("ID do Apontamento", df['ID'].tolist())
    if id_selecionado:
        registro_atual = df[df['ID'] == id_selecionado].iloc[0]
        
        with st.form("form_edicao"):
            novo_status = st.selectbox("Status", ["Concluído", "Pendente", "Impedido"])
            if st.form_submit_button("Salvar"):
                st.session_state.df_apontamentos.loc[df['ID'] == id_selecionado, 'STATUS'] = novo_status
                st.success("Atualizado!")
                st.rerun()

# -----------------------------------------------------------------------------
# 5. ESTRUTURA E NAVEGAÇÃO PRINCIPAL
# -----------------------------------------------------------------------------
if not st.session_state.logged_in:
    tela_login()
else:
    # Mostra a sidebar manual apenas após o login
    with st.sidebar:
        st.markdown("<h3 style='text-align: center;'>Duarte Gestão</h3>", unsafe_allow_html=True)
        st.markdown(f"**👤 Usuário:** {st.session_state.user}")
        st.markdown(f"**🛡️ Perfil:** {st.session_state.role}")
        st.divider()

        menu = st.radio(
            "Menu de Navegação",
            [
                "Dashboard Gerencial",
                "Escala Semanal",
                "Relatórios Operacionais",
                "Lançar Execução Diária",
                "Editor de Apontamentos"
            ]
        )

        st.divider()
        if st.button("🚪 Sair", use_container_width=True):
            st.session_state.logged_in = False
            st.session_state.token = None
            st.session_state.user = None
            st.rerun()

    if menu == "Dashboard Gerencial":
        aba_dashboard()
    elif menu == "Escala Semanal":
        aba_escala_semanal()
    elif menu == "Relatórios Operacionais":
        aba_relatorios()
    elif menu == "Lançar Execução Diária":
        aba_lancar_execucao()
    elif menu == "Editor de Apontamentos":
        aba_editor_apontamentos()