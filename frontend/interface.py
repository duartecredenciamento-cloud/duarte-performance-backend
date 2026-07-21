import streamlit as st
import pandas as pd
from datetime import datetime
import utils  # Importa a lógica pesada que criamos separadamente

st.markdown("""
<style>
    /* ===================== CORES DUARTE ===================== */
    :root {
        --duarte-dark: #0A1128;
        --duarte-blue: #0F172A;
        --duarte-orange: #F26419;
        --duarte-orange-hover: #d95615;
        --bg-light: #F8FAFC;
        --card-bg: #FFFFFF;
        --text-primary: #0F172A;
        --text-muted: #64748B;
    }

    /* Background suave com gradiente sutil */
    .stApp {
        background: linear-gradient(135deg, #F8FAFC 0%, #EEF2F6 100%);
        font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
    }

    /* Sidebar com animação de entrada */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, var(--duarte-dark) 0%, #02040A 100%);
        border-right: 5px solid var(--duarte-orange);
        animation: slideInLeft 0.6s ease-out;
    }

    @keyframes slideInLeft {
        from { transform: translateX(-30px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }

    /* Menu items com hover premium */
    [data-testid="stSidebar"] [data-testid="stRadio"] label {
        border-radius: 14px;
        padding: 16px 20px;
        margin-bottom: 6px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        border: 1px solid rgba(255,255,255,0.08);
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label:hover {
        background: rgba(242, 100, 25, 0.18) !important;
        transform: translateX(12px) scale(1.02);
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    [data-testid="stSidebar"] [data-testid="stRadio"] label[data-checked="true"] {
        background: linear-gradient(90deg, var(--duarte-orange), #e05a12) !important;
        color: white !important;
        font-weight: 700;
        box-shadow: 0 6px 18px rgba(242,100,25,0.45);
    }

    /* Cards com animação de entrada e hover */
    .kpi-card {
        background: var(--card-bg);
        padding: 32px 26px;
        border-radius: 22px;
        box-shadow: 0 12px 35px rgba(15,23,42,0.08);
        border-left: 8px solid var(--duarte-orange);
        transition: all 0.5s cubic-bezier(0.34, 1.56, 0.64, 1);
        animation: fadeInUp 0.7s ease forwards;
    }
    .kpi-card:hover {
        transform: translateY(-12px) scale(1.02);
        box-shadow: 0 25px 50px rgba(15,23,42,0.18);
    }

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(30px); }
        to { opacity: 1; transform: translateY(0); }
    }

    /* Botões com efeito ripple premium */
    div.stButton > button {
        border-radius: 14px;
        font-weight: 700;
        padding: 14px 36px;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        position: relative;
        overflow: hidden;
    }
    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, var(--duarte-blue), var(--duarte-dark));
        color: white;
    }
    div.stButton > button:hover {
        background: linear-gradient(135deg, var(--duarte-orange), var(--duarte-orange-hover)) !important;
        transform: translateY(-4px);
        box-shadow: 0 15px 30px rgba(242,100,25,0.4);
    }

    /* Inputs com focus animation */
    div[data-baseweb="input"], div[data-baseweb="select"], div[data-baseweb="textarea"] {
        background: #FFFFFF !important;
        border-radius: 14px !important;
        border: 2px solid #E2E8F0 !important;
        transition: all 0.3s ease;
    }
    div[data-baseweb="input"]:focus-within, div[data-baseweb="select"]:focus-within {
        border-color: var(--duarte-orange) !important;
        box-shadow: 0 0 0 4px rgba(242,100,25,0.2) !important;
        transform: scale(1.02);
    }

    /* Tabelas com zebra e hover */
    .stDataFrame tbody tr:hover {
        background-color: rgba(242,100,25,0.08) !important;
        transition: background-color 0.3s ease;
    }

    /* Loading spinner customizado */
    .stSpinner > div > div {
        border-color: var(--duarte-orange) !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# ABA: ESCALA SEMANAL (Melhorada)
# -----------------------------------------------------------------------------
def aba_escala_semanal():
    st.header("📅 Escala Semanal (Cronograma Operacional)")
    st.markdown("**Gestão inteligente de alocação de operadores por cliente e dia da semana**")

    # Importação
    st.subheader("1. Importar Base de Escala")
    arquivo_escala = st.file_uploader("Anexe a planilha (.xlsx ou .csv)", type=['xlsx', 'csv'])
    
    if arquivo_escala:
        try:
            if arquivo_escala.name.endswith('.csv'):
                df_temp = pd.read_csv(arquivo_escala)
            else:
                df_temp = pd.read_excel(arquivo_escala)
            
            sucesso, mensagem = utils.validar_escala(df_temp)
            if sucesso:
                st.session_state.df_escala = df_temp
                st.success("✅ Escala importada com sucesso!")
                st.rerun()
            else:
                st.error(mensagem)
        except Exception as e:
            st.error(f"Erro: {e}")

    st.divider()

    # Visualização
    st.subheader("2. Escala Atual")
    if st.session_state.df_escala.empty:
        st.info("Nenhuma escala importada ainda.")
    else:
        df_view = st.session_state.df_escala.copy()
        
        col1, col2 = st.columns(2)
        with col1:
            operador_filtro = st.selectbox("Filtrar por Operador", ["Todos"] + sorted(df_view["OPERADOR"].unique().tolist()))
        with col2:
            dia_filtro = st.selectbox("Filtrar por Data", ["Todos"] + sorted(df_view["DATA"].unique().tolist()))
        
        if operador_filtro != "Todos":
            df_view = df_view[df_view["OPERADOR"] == operador_filtro]
        if dia_filtro != "Todos":
            df_view = df_view[df_view["DATA"] == dia_filtro]
        
        st.dataframe(df_view, use_container_width=True, hide_index=True)

        # Botão de exportação
        csv = df_view.to_csv(index=False).encode()
        st.download_button("📥 Exportar CSV", csv, "escala_atual.csv", "text/csv")

    st.divider()

    # Adição Manual + Editor
    st.subheader("3. Gerenciar Escala")
    with st.form("add_item"):
        col1, col2, col3 = st.columns(3)
        data_nova = col1.date_input("Data", value=datetime.now())
        operador_novo = col2.selectbox("Operador", st.session_state.equipe)
        cliente_novo = col3.text_input("Cliente")
        turno_novo = st.selectbox("Turno", ["Manhã", "Tarde", "Integral"])
        
        if st.form_submit_button("➕ Adicionar", type="primary"):
            if cliente_novo:
                novo = {'DATA': data_nova.strftime('%Y-%m-%d'), 'OPERADOR': operador_novo, 'CLIENTE': cliente_novo, 'TURNO': turno_novo}
                st.session_state.df_escala = pd.concat([st.session_state.df_escala, pd.DataFrame([novo])], ignore_index=True)
                st.success("Item adicionado!")
                st.rerun()

    # Editor Interativo
    st.subheader("Editor Interativo")
    df_editado = st.data_editor(st.session_state.df_escala, num_rows="dynamic", use_container_width=True)
    if st.button("💾 Salvar Alterações"):
        st.session_state.df_escala = df_editado
        st.success("Escala salva com sucesso!")


# -----------------------------------------------------------------------------
# ABA: RELATÓRIOS
# -----------------------------------------------------------------------------
def aba_relatorios():
    st.header("📊 Relatórios Operacionais")
    df = st.session_state.df_apontamentos
    
    if df.empty:
        st.warning("Nenhum apontamento registrado.")
        return

    # Filtros
    with st.expander("🔎 Filtros Avançados", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_data = st.date_input("Período", [])
        with col2:
            filtro_operador = st.selectbox("Operador", ["Todos"] + df['OPERADOR'].unique().tolist())
        with col3:
            filtro_status = st.selectbox("Status", ["Todos"] + df['STATUS'].unique().tolist())

    df_filtrado = df.copy()
    if filtro_data and len(filtro_data) == 2:
        df_filtrado = df_filtrado[(pd.to_datetime(df_filtrado['DATA']) >= pd.to_datetime(filtro_data[0])) & 
                                  (pd.to_datetime(df_filtrado['DATA']) <= pd.to_datetime(filtro_data[1]))]
    if filtro_operador != "Todos":
        df_filtrado = df_filtrado[df_filtrado['OPERADOR'] == filtro_operador]
    if filtro_status != "Todos":
        df_filtrado = df_filtrado[df_filtrado['STATUS'] == filtro_status]

    st.dataframe(df_filtrado, use_container_width=True)

    # Exportação
    csv = df_filtrado.to_csv(index=False).encode()
    st.download_button("📥 Exportar Relatório (CSV)", csv, "relatorio.csv", "text/csv", type="primary")


# -----------------------------------------------------------------------------
# ABA: EDITOR DE APONTAMENTOS
# -----------------------------------------------------------------------------
def aba_editor_apontamentos():
    st.header("✏️ Editor de Apontamentos")
    if st.session_state.role not in ["Gestor", "Gestor Operacional", "Admin"]:
        st.error("Acesso restrito.")
        return

    df = st.session_state.df_apontamentos
    if df.empty:
        st.warning("Nenhum registro para editar.")
        return

    id_sel = st.selectbox("Selecione o registro", df['ID'].tolist())
    registro = df[df['ID'] == id_sel].iloc[0]

    with st.form("edit_form"):
        novo_cliente = st.text_input("Cliente", registro['CLIENTE'])
        novo_status = st.selectbox("Status", ["Realizado Total", "Realizado Parcial", "Não Realizado"], index=0)
        nova_obs = st.text_area("Observação", registro['OBSERVACAO'])
        
        if st.form_submit_button("Salvar Alterações", type="primary"):
            df.loc[df['ID'] == id_sel, ['CLIENTE', 'STATUS', 'OBSERVACAO']] = [novo_cliente, novo_status, nova_obs]
            st.success("Registro atualizado!")
            st.rerun()


# -----------------------------------------------------------------------------
# ABA: DASHBOARD
# -----------------------------------------------------------------------------
def aba_dashboard():
    st.header("📈 Dashboard Gerencial")
    df = st.session_state.df_apontamentos
    
    if df.empty:
        st.warning("Sem dados para exibir.")
        return

    col1, col2 = st.columns(2)
    with col1:
        filtro_op = st.selectbox("Operador", ["Geral"] + df['OPERADOR'].unique().tolist())
    with col2:
        filtro_cli = st.selectbox("Cliente", ["Geral"] + df['CLIENTE'].unique().tolist())

    df_dash = df.copy()
    if filtro_op != "Geral": df_dash = df_dash[df_dash['OPERADOR'] == filtro_op]
    if filtro_cli != "Geral": df_dash = df_dash[df_dash['CLIENTE'] == filtro_cli]

    # Métricas
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Apontamentos", len(df_dash))
    c2.metric("Realizado Total", (df_dash['STATUS'] == 'Realizado Total').sum())
    c3.metric("Realizado Parcial", (df_dash['STATUS'] == 'Realizado Parcial').sum())
    c4.metric("Não Realizado", (df_dash['STATUS'] == 'Não Realizado').sum())

    # Gráficos
    st.subheader("Distribuição por Status")
    st.bar_chart(df_dash['STATUS'].value_counts())

    st.subheader("Por Operador")
    st.bar_chart(df_dash.groupby('OPERADOR').size())

# -----------------------------------------------------------------------------
# MENU LATERAL PREMIUM + NOTIFICAÇÕES + INICIAIS INTELIGENTES
# -----------------------------------------------------------------------------
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 15px 0;">
        <h2 style="color:#F26419; margin:0; font-weight:900; letter-spacing:-1px;">DUARTE</h2>
        <p style="color:#94A3B8; margin:0; font-size:13px; letter-spacing:2px;">PERFORMANCE</p>
    </div>
    """, unsafe_allow_html=True)

    # LÓGICA INTELIGENTE DE INICIAIS
    nome_completo = st.session_state.user.strip()
    partes = [p for p in nome_completo.split() if len(p) > 1]
    if len(partes) >= 2:
        iniciais = (partes[0][0] + partes[-1][0]).upper()
    else:
        iniciais = nome_completo[:2].upper()

    # Avatar com Iniciais
    st.markdown(f"""
    <div style="display: flex; justify-content: center; margin: 15px 0 20px 0;">
        <div style="background: linear-gradient(135deg, #F26419, #d95615); color: white; 
                    width: 78px; height: 78px; border-radius: 50%; display: flex; 
                    align-items: center; justify-content: center; font-size: 32px; 
                    font-weight: 900; box-shadow: 0 10px 30px rgba(242,100,25,0.45);
                    border: 5px solid rgba(255,255,255,0.25);">
            {iniciais}
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Nome e Perfil
    st.markdown(f"""
    <div style="text-align:center; margin-bottom: 25px;">
        <strong style="color:#F1F5F9; font-size:17px;">{nome_completo}</strong><br>
        <span style="color:#F26419; font-size:13px; font-weight:700;">{st.session_state.role}</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # ÍCONE DE NOTIFICAÇÃO
    col_notif, col_menu = st.columns([1, 5])
    with col_notif:
        if st.button("🛎️", key="notif_btn"):
            st.session_state.show_notifications = not st.session_state.get("show_notifications", False)
    
    # Menu Principal
    menu = st.radio(
        "Navegação Principal",
        [
            "🏠 Dashboard Gerencial",
            "🗓️ Escala Semanal",
            "📊 Relatórios Operacionais",
            "📝 Lançar Execução Diária",
            "✏️ Editor de Apontamentos (Gestor)"
        ],
        label_visibility="collapsed"
    )

    st.divider()

    # Validação de Nome Único (exemplo)
    if st.button("🔍 Verificar Nome Único"):
        nome_teste = st.text_input("Digite um nome para validar", key="nome_valida")
        if nome_teste:
            # Simulação de validação
            if nome_teste.lower() in [n.lower() for n in st.session_state.equipe]:
                st.error("❌ Nome já existe")
            else:
                st.success("✅ Nome disponível")

    st.caption("📍 Status da Operação")
    st.success("🟢 Todos os sistemas operando normalmente")

    if st.button("🚪 Encerrar Sessão", use_container_width=True, type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()