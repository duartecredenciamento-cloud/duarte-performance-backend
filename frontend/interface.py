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
# ESTADO DE SESSÃO (MOCK DE LOGIN E DADOS REAIS)
# -----------------------------------------------------------------------------
if 'logged_in' not in st.session_state:
    st.session_state.logged_in = True
    st.session_state.user = "Abraão da Silva Santos"           # Gestor Operacional
    st.session_state.role = "Gestor Operacional"               # Pode mudar para "Operador" ou "Admin"
    st.session_state.equipe = [
        "Abraão da Silva Santos",
        "Cristiane Aparecida Duarte",   # CEO
        "Bethania Duarte",              # Gerente de Novos Negócios
        "Equipe Rede"
    ]

if 'df_escala' not in st.session_state:
    # Mock inicial da escala (pode ser substituído por dados reais do backend)
    st.session_state.df_escala = pd.DataFrame({
        'DATA': ['2026-07-21', '2026-07-22', '2026-07-23'],
        'OPERADOR': ['Abraão da Silva Santos', 'Bethania Duarte', 'Cristiane Aparecida Duarte'],
        'CLIENTE': ['FR FISIO', 'EV-CITI', 'REGULAÇÃO'],
        'TURNO': ['Manhã', 'Integral', 'Tarde']
    })

if 'df_apontamentos' not in st.session_state:
    # Mock de apontamentos
    st.session_state.df_apontamentos = pd.DataFrame({
        'ID': [1, 2, 3],
        'DATA': ['2026-07-21', '2026-07-21', '2026-07-20'],
        'OPERADOR': ['Abraão da Silva Santos', 'Bethania Duarte', 'Abraão da Silva Santos'],
        'CLIENTE': ['FR FISIO', 'EV-CITI', 'REGULAÇÃO'],
        'STATUS': ['Realizado Total', 'Realizado Parcial', 'Não Realizado'],
        'OBSERVACAO': [
            'Credenciamento concluído com sucesso',
            'Aguardando aprovação do cliente',
            'Cliente não atendeu'
        ]
    })

def aba_escala_semanal():
    st.header("📅 Escala Semanal (Cronograma Operacional)")
    st.markdown("**Gestão de alocação de operadores por cliente e dia da semana**")

    # === IMPORTAÇÃO DE PLANILHA ===
    st.subheader("1. Importar Base de Escala")
    arquivo_escala = st.file_uploader(
        "Anexe a planilha da escala (.xlsx ou .csv)", 
        type=['xlsx', 'csv'],
        help="Colunas esperadas: DATA, OPERADOR, CLIENTE, TURNO"
    )
    
    if arquivo_escala:
        try:
            if arquivo_escala.name.endswith('.csv'):
                df_temp = pd.read_csv(arquivo_escala)
            else:
                df_temp = pd.read_excel(arquivo_escala)
            
            sucesso, mensagem = utils.validar_escala(df_temp)
            if sucesso:
                st.success(mensagem)
                st.session_state.df_escala = df_temp
                st.rerun()
            else:
                st.error("Falha na validação:")
                for erro in (mensagem if isinstance(mensagem, list) else [mensagem]):
                    st.warning(erro)
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {str(e)}")

    st.divider()

    # === VISUALIZAÇÃO DA ESCALA ATUAL ===
    st.subheader("2. Escala Atual")
    if st.session_state.df_escala.empty:
        st.info("Nenhuma escala importada ainda. Importe uma planilha acima.")
    else:
        df_view = st.session_state.df_escala.copy()
        
        # Filtros
        col1, col2 = st.columns(2)
        with col1:
            operador_filtro = st.selectbox(
                "Filtrar por Operador", 
                ["Todos"] + sorted(df_view["OPERADOR"].unique().tolist())
            )
        with col2:
            dia_filtro = st.selectbox(
                "Filtrar por Dia", 
                ["Todos"] + sorted(df_view["DATA"].unique().tolist())
            )
        
        # Aplicar filtros
        if operador_filtro != "Todos":
            df_view = df_view[df_view["OPERADOR"] == operador_filtro]
        if dia_filtro != "Todos":
            df_view = df_view[df_view["DATA"] == dia_filtro]
        
        st.dataframe(df_view, use_container_width=True, hide_index=True)

    st.divider()

    # === LANÇAMENTO MANUAL (opcional) ===
    st.subheader("3. Adicionar Item Manualmente")
    with st.form("form_add_escala"):
        col1, col2, col3 = st.columns(3)
        data_nova = col1.date_input("Data", value=datetime.now())
        operador_novo = col2.selectbox("Operador", st.session_state.equipe)
        cliente_novo = col3.text_input("Cliente")
        
        turno_novo = st.selectbox("Turno", ["Manhã", "Tarde", "Integral"])
        
        if st.form_submit_button("➕ Adicionar à Escala", type="primary"):
            if cliente_novo:
                novo_item = {
                    'DATA': data_nova.strftime('%Y-%m-%d'),
                    'OPERADOR': operador_novo,
                    'CLIENTE': cliente_novo,
                    'TURNO': turno_novo
                }
                st.session_state.df_escala = pd.concat([
                    st.session_state.df_escala, 
                    pd.DataFrame([novo_item])
                ], ignore_index=True)
                st.success(f"Item adicionado para {operador_novo}!")
                st.rerun()
            else:
                st.warning("Informe o cliente.")
    
    # CRUD Completo e Interativo nativo do Streamlit
    st.subheader("2. Gerenciar Escala (Adicionar/Remover/Mover)")
    st.caption("Edite os dados diretamente na tabela abaixo. Adicione ou exclua linhas.")
    
    # O st.data_editor é a forma definitiva de fazer CRUD em DataFrames no Streamlit
    df_editado = st.data_editor(
        st.session_state.df_escala,
        num_rows="dynamic",
        use_container_width=True,
        key="editor_escala"
    )
    
    if st.button("Salvar Alterações na Escala"):
        st.session_state.df_escala = df_editado
        utils.registrar_auditoria("EDICAO_ESCALA", st.session_state.user, "Atualizou a escala semanal via CRUD.")
        st.success("Escala atualizada no sistema!")


def aba_relatorios():
    st.header("📊 Relatórios Operacionais")
    df = st.session_state.df_apontamentos
    
    if df.empty:
        st.warning("Nenhum apontamento registrado ainda.")
        return

    # LÓGICA DE FILTRAGEM CUMULATIVA E REATIVA CORRETA
    with st.expander("Filtros de Pesquisa", expanded=True):
        col1, col2, col3 = st.columns(3)
        with col1:
            filtro_data = st.date_input("Data", [])
        with col2:
            opcoes_operador = ["Todos"] + df['OPERADOR'].unique().tolist()
            filtro_operador = st.selectbox("Operador", opcoes_operador)
        with col3:
            opcoes_status = ["Todos"] + df['STATUS'].unique().tolist()
            filtro_status = st.selectbox("Status (SLA)", opcoes_status)

    # Aplicação sequencial dos filtros no DataFrame
    df_filtrado = df.copy()
    
    if filtro_data and len(filtro_data) == 2:
        start_date, end_date = filtro_data
        df_filtrado = df_filtrado[
            (pd.to_datetime(df_filtrado['DATA']).dt.date >= start_date) & 
            (pd.to_datetime(df_filtrado['DATA']).dt.date <= end_date)
        ]
    elif filtro_data and len(filtro_data) == 1:
         df_filtrado = df_filtrado[pd.to_datetime(df_filtrado['DATA']).dt.date == filtro_data[0]]
         
    if filtro_operador != "Todos":
        df_filtrado = df_filtrado[df_filtrado['OPERADOR'] == filtro_operador]
        
    if filtro_status != "Todos":
        df_filtrado = df_filtrado[df_filtrado['STATUS'] == filtro_status]

    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)


def aba_editor_apontamentos():
    st.header("⚙️ Editor de Apontamentos")
    
    # REGRA DE SEGURANÇA: Restrição Estrita de Acesso
    if st.session_state.role not in ["Gestor", "Admin"]:
        st.error("Acesso Negado: Apenas Gestores ou Administradores podem acessar a edição de apontamentos e observações retroativas.")
        return
        
    st.info("Selecione o registro incorreto abaixo para alterar o Status, Cliente ou Observação.")
    df = st.session_state.df_apontamentos
    
    if df.empty:
        st.warning("Nenhum dado para editar.")
        return
        
    id_selecionado = st.selectbox("Selecione o ID do Apontamento", df['ID'].tolist())
    
    if id_selecionado:
        # Pega a linha atual
        registro_atual = df[df['ID'] == id_selecionado].iloc[0]
        
        with st.form("form_edicao"):
            novo_cliente = st.text_input("Cliente", value=registro_atual['CLIENTE'])
            novo_status = st.selectbox("Status", ["Concluído", "Pendente", "Impedido", "Em Andamento", "Não Informado"], index=["Concluído", "Pendente", "Impedido", "Em Andamento", "Não Informado"].index(registro_atual['STATUS']) if registro_atual['STATUS'] in ["Concluído", "Pendente", "Impedido", "Em Andamento", "Não Informado"] else 0)
            nova_obs = st.text_area("Observação / Justificativa", value=registro_atual['OBSERVACAO'])
            
            if st.form_submit_button("Salvar Correção"):
                # Atualiza o DataFrame no estado
                st.session_state.df_apontamentos.loc[st.session_state.df_apontamentos['ID'] == id_selecionado, 'CLIENTE'] = novo_cliente
                st.session_state.df_apontamentos.loc[st.session_state.df_apontamentos['ID'] == id_selecionado, 'STATUS'] = novo_status
                st.session_state.df_apontamentos.loc[st.session_state.df_apontamentos['ID'] == id_selecionado, 'OBSERVACAO'] = nova_obs
                
                utils.registrar_auditoria("EDICAO_APONTAMENTO", st.session_state.user, f"Editou o ID {id_selecionado}")
                st.success("Registro atualizado com sucesso!")
                st.rerun()

def aba_dashboard():
    st.header("📈 Dashboard Gerencial")
    df = st.session_state.df_apontamentos
    
    if df.empty:
        st.warning("Sem dados para exibir no Dashboard.")
        return
        
    col1, col2 = st.columns(2)
    with col1:
        filtro_dash_op = st.selectbox("Filtrar por Operador", ["Geral"] + df['OPERADOR'].unique().tolist(), key="dash_op")
    with col2:
         filtro_dash_cli = st.selectbox("Filtrar por Cliente", ["Geral"] + df['CLIENTE'].unique().tolist(), key="dash_cli")
         
    df_dash = df.copy()
    if filtro_dash_op != "Geral": df_dash = df_dash[df_dash['OPERADOR'] == filtro_dash_op]
    if filtro_dash_cli != "Geral": df_dash = df_dash[df_dash['CLIENTE'] == filtro_dash_cli]
    
    st.subheader("Produtividade por Status")
    status_count = df_dash['STATUS'].value_counts()
    st.bar_chart(status_count, color="#F26419")

# -----------------------------------------------------------------------------
# MENU LATERAL PREMIUM COM AVATAR DE INICIAIS
# -----------------------------------------------------------------------------
with st.sidebar:
    # Logo
    st.markdown("""
    <div style="text-align:center; padding: 20px 0 15px 0;">
        <h2 style="color:#F26419; margin:0; font-weight:900; letter-spacing:-1px;">DUARTE</h2>
        <p style="color:#94A3B8; margin:0; font-size:13px; letter-spacing:2px;">PERFORMANCE</p>
    </div>
    """, unsafe_allow_html=True)

    # Avatar com Iniciais
    nome = st.session_state.user
    partes = nome.strip().split()
    iniciais = (partes[0][0] + partes[-1][0]).upper() if len(partes) > 1 else nome[:2].upper()

    st.markdown(f"""
    <div style="display: flex; justify-content: center; margin: 15px 0 25px 0;">
        <div style="
            background: linear-gradient(135deg, #F26419, #d95615);
            color: white;
            width: 72px;
            height: 72px;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            font-weight: 900;
            box-shadow: 0 8px 25px rgba(242, 100, 25, 0.4);
            border: 4px solid rgba(255,255,255,0.2);
        ">{iniciais}</div>
    </div>
    """, unsafe_allow_html=True)

    # Nome e Perfil
    st.markdown(f"""
    <div style="text-align:center; margin-bottom: 30px;">
        <strong style="color:#F1F5F9; font-size:17px;">{nome}</strong><br>
        <span style="color:#F26419; font-size:13px; font-weight:700;">{st.session_state.role}</span>
    </div>
    """, unsafe_allow_html=True)

    st.divider()

    # Menu
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

    st.caption("📍 Status da Operação")
    st.success("🟢 Todos os sistemas operando normalmente")
    
    if st.button("🚪 Encerrar Sessão", use_container_width=True, type="secondary"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()