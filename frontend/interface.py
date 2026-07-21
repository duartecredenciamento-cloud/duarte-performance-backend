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

# -----------------------------------------------------------------------------
# MÓDULOS DA INTERFACE (FUNÇÕES SEPARADAS POR ABA)
# -----------------------------------------------------------------------------

def aba_lancar_execucao():
    st.header("📝 Lançar Execução Diária")
    
    hoje = datetime.now()
    st.markdown(f"**Registro Auditado:** {hoje.strftime('%d/%m/%Y')} | **Operador:** {st.session_state.user}")
    
    # 1. Busca os clientes da escala do dia para este operador
    clientes_hoje = utils.obter_clientes_do_dia(st.session_state.df_escala, st.session_state.user, hoje)
    
    # 2. Lógica Dinâmica do Dropdown baseada na imagem enviada
    if not clientes_hoje:
        st.info("ℹ️ Não encontramos nenhum cliente atribuído a você na escala de hoje. Selecione 'Suporte' ou 'Outro'.")
        opcoes_cliente = ["Suporte", "Outro"]
    else:
        opcoes_cliente = clientes_hoje + ["Suporte", "Outro"]
        
    col1, col2 = st.columns(2)
    with col1:
        cliente_selecionado = st.selectbox("Selecione o Cliente Trabalhado", opcoes_cliente)
        
        # Sub-filtro condicional exigido
        if cliente_selecionado == "Suporte":
            todos_clientes = ["Cliente A", "Cliente B", "Cliente C"] # Substituir por query no banco
            cliente_destino = st.selectbox("Selecione o Cliente de Destino", todos_clientes)
            cliente_final = f"Suporte - {cliente_destino}"
        else:
            cliente_final = cliente_selecionado

    with col2:
        status_trabalho = st.selectbox("Status Final do Trabalho", ["Concluído", "Pendente", "Impedido", "Em Andamento"])
    
    # UX Text atualizado
    observacao = st.text_area(
        "Justificativa / Observações", 
        placeholder="Devido a reunião não foi possível realizar totalmente as tarefas do cliente"
    )
    
    st.file_uploader("📎 Comprovações e Evidências", accept_multiple_files=False)
    
    if st.button("🚀 ENVIAR APONTAMENTO DIÁRIO"):
        # Lógica de gravação
        novo_id = len(st.session_state.df_apontamentos) + 1
        novo_apontamento = {
            'ID': novo_id,
            'DATA': hoje.strftime('%Y-%m-%d'),
            'OPERADOR': st.session_state.user,
            'CLIENTE': cliente_final,
            'STATUS': status_trabalho,
            'OBSERVACAO': observacao
        }
        st.session_state.df_apontamentos = pd.concat([st.session_state.df_apontamentos, pd.DataFrame([novo_apontamento])], ignore_index=True)
        utils.registrar_auditoria("INSERCAO", st.session_state.user, f"Lançou {status_trabalho} para {cliente_final}")
        st.success("Apontamento registrado com sucesso!")


def aba_escala_semanal():
    st.header("📅 Escala Semanal (Cronograma)")
    
    # Upload e Validação
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
                st.success(mensagem)
                st.session_state.df_escala = df_temp
            else:
                st.error("Falha na validação do arquivo:")
                for erro in (mensagem if isinstance(mensagem, list) else [mensagem]):
                    st.warning(erro)
        except Exception as e:
            st.error(f"Erro ao processar arquivo: {e}")

    st.divider()
    
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
# MENU LATERAL E NAVEGAÇÃO PRINCIPAL
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://via.placeholder.com/150x50?text=Duarte+Performance", use_column_width=True) # Substitua pelo logo real
    st.markdown(f"**🟢 Online:** {st.session_state.user}")
    st.markdown(f"**💼 Perfil:** {st.session_state.role}")
    st.divider()
    
    menu = st.radio(
        "Navegação Principal",
        ["Dashboard Gerencial", "Escala Semanal", "Relatórios Operacionais", "Lançar Execução Diária", "Editor de Apontamentos (Gestor)"]
    )

# Controle de roteamento das abas
if menu == "Lançar Execução Diária":
    aba_lancar_execucao()
elif menu == "Escala Semanal":
    aba_escala_semanal()
elif menu == "Relatórios Operacionais":
    aba_relatorios()
elif menu == "Dashboard Gerencial":
    aba_dashboard()
elif menu == "Editor de Apontamentos (Gestor)":
    aba_editor_apontamentos()