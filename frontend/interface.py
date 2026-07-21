import streamlit as st
import pandas as pd
import requests
from datetime import datetime, date
import os
from datetime import datetime, timedelta, timezone

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA E CSS GLOBAL (PREMIUM DESIGN)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Duarte Performance - Gestão Operacional",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
    <style>
        /* 1. Ocultar Elementos Padrão do Streamlit */
        [data-testid="stSidebarNav"] { display: none !important; }
        #MainMenu { visibility: hidden; }
        footer { visibility: hidden; }
        header { visibility: hidden; }

        /* 2. Fundo Geral da Aplicação */
        .stApp { 
            background-color: #F4F6F9; 
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* 3. Estilização da Sidebar (Azul Marinho Duarte) */
        [data-testid="stSidebar"] {
            background-color: #0A1128 !important;
            border-right: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 4px 0px 15px rgba(0, 0, 0, 0.1);
        }
        [data-testid="stSidebar"] * { 
            color: #FFFFFF !important; 
        }

        /* 4. Estilização de Cards de Métricas (st.metric) */
        [data-testid="stMetric"] {
            background: #FFFFFF;
            padding: 18px 22px;
            border-radius: 12px;
            box-shadow: 0px 4px 12px rgba(10, 17, 40, 0.05);
            border: 1px solid #E2E8F0;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            box-shadow: 0px 6px 16px rgba(10, 17, 40, 0.1);
        }
        [data-testid="stMetricLabel"] {
            font-weight: 600 !important;
            color: #6C757D !important;
            font-size: 0.88rem !important;
        }
        [data-testid="stMetricValue"] {
            font-weight: 700 !important;
            color: #0A1128 !important;
        }

        /* 5. Inputs, Selectbox e TextAreas (Glassmorphism & Clean) */
        .stTextInput > div > div > input,
        .stSelectbox > div > div > div,
        .stTextArea > div > div > textarea {
            background-color: #FFFFFF !important;
            border-radius: 8px !important;
            border: 1px solid #CED4DA !important;
            color: #0A1128 !important;
            box-shadow: 0px 2px 4px rgba(0, 0, 0, 0.02);
            transition: all 0.2s ease-in-out;
        }
        .stTextInput > div > div > input:focus,
        .stSelectbox > div > div > div:focus,
        .stTextArea > div > div > textarea:focus {
            border-color: #F26419 !important;
            box-shadow: 0 0 0 3px rgba(242, 100, 25, 0.15) !important;
        }

        /* 6. Botões (Laranja Duarte com Efeito Elevação) */
        div.stButton > button:first-child {
            background-color: #F26419; 
            color: #FFFFFF !important; 
            border: none; 
            border-radius: 8px;
            padding: 0.6rem 1.2rem;
            font-weight: 600;
            letter-spacing: 0.3px;
            box-shadow: 0px 4px 10px rgba(242, 100, 25, 0.25);
            transition: all 0.25s ease-in-out;
        }
        div.stButton > button:hover {
            background-color: #D95615 !important; 
            color: #FFFFFF !important;
            box-shadow: 0px 6px 14px rgba(242, 100, 25, 0.35);
            transform: translateY(-1px);
        }
        div.stButton > button:active {
            transform: translateY(1px);
            box-shadow: 0px 2px 6px rgba(242, 100, 25, 0.2);
        }

        /* 7. Formulários e Containers */
        [data-testid="stForm"] {
            background: #FFFFFF;
            padding: 24px;
            border-radius: 12px;
            border: 1px solid #E2E8F0;
            box-shadow: 0px 4px 16px rgba(0, 0, 0, 0.03);
        }

        /* 8. Tabelas e Dataframes (Bordas Arredondadas) */
        [data-testid="stDataFrame"] {
            background: #FFFFFF;
            border-radius: 10px;
            padding: 6px;
            border: 1px solid #E2E8F0;
            box-shadow: 0px 2px 8px rgba(0, 0, 0, 0.02);
        }

        /* 9. Scrollbar Customizada (Fina e Minimalista) */
        ::-webkit-scrollbar {
            width: 6px;
            height: 6px;
        }
        ::-webkit-scrollbar-track {
            background: #F4F6F9;
        }
        ::-webkit-scrollbar-thumb {
            background: #CBD5E1;
            border-radius: 4px;
        }
        ::-webkit-scrollbar-thumb:hover {
            background: #94A3B8;
        }
    </style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# MÓDULO DE REGRAS DE NEGÓCIO E DADOS (NÚCLEO LÓGICO / UTILS)
# -----------------------------------------------------------------------------
BACKEND_URL = os.getenv("BACKEND_URL", "https://duarte-performance-backend.onrender.com")

# Fuso horário do Brasil (Garante que o servidor no Render não puxe o dia errado)
FUSO_BR = timezone(timedelta(hours=-3))

def inicializar_estados():
    """Garante que as tabelas base e variáveis de sessão existam de forma segura."""
    
    # Variáveis Simples
    estados_padrao = {
        'logged_in': False,
        'token': None,
        'user': None,
        'role': "Operador"
    }
    for chave, valor in estados_padrao.items():
        if chave not in st.session_state:
            st.session_state[chave] = valor
            
    # Tabela de Escala Semanal
    if 'df_escala' not in st.session_state:
        st.session_state.df_escala = pd.DataFrame(columns=[
            'ID', 'DIA_SEMANA', 'OPERADOR', 'CLIENTE'
        ])
    
    # Tabela de Apontamentos com Auditoria
    if 'df_apontamentos' not in st.session_state:
        st.session_state.df_apontamentos = pd.DataFrame(columns=[
            'ID', 'DATA_REGISTRO', 'DIA_SEMANA', 'OPERADOR', 'CLIENTE', 'STATUS', 'OBSERVACAO', 'LOG_AUDITORIA'
        ])

def verificar_duplicidades(df_escala):
    """Verifica se um cliente foi alocado para o mesmo operador mais de uma vez na semana."""
    if df_escala.empty: 
        return []
        
    duplicados = df_escala.groupby(['OPERADOR', 'CLIENTE']).size().reset_index(name='contagem')
    alertas = duplicados[duplicados['contagem'] > 1]
    return alertas.to_dict('records')

def obter_dia_semana_pt(data_obj):
    """Converte a data para o nome do dia em português de forma segura."""
    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    return dias[data_obj.weekday()]

def consolidar_nao_informados():
    """
    Gera apontamentos automáticos de 'Não Informado' para tarefas da escala não lançadas.
    Otimizado para não sobrecarregar a memória com múltiplos pd.concat em loop.
    """
    hoje_br = datetime.now(FUSO_BR).date()
    dia_atual = obter_dia_semana_pt(hoje_br)
    data_str = hoje_br.strftime('%Y-%m-%d')
    
    escala = st.session_state.df_escala
    apontamentos = st.session_state.df_apontamentos
    
    # Pega tudo que deveria ser feito hoje
    tarefas_hoje = escala[escala['DIA_SEMANA'] == dia_atual]
    novos_registros = []
    
    for _, tarefa in tarefas_hoje.iterrows():
        # Verifica se já foi lançado
        ja_lancado = apontamentos[
            (apontamentos['DATA_REGISTRO'] == data_str) & 
            (apontamentos['OPERADOR'] == tarefa['OPERADOR']) &
            (apontamentos['CLIENTE'] == tarefa['CLIENTE'])
        ]
        
        if ja_lancado.empty:
            novo_id = len(apontamentos) + len(novos_registros) + 1
            log_hora = datetime.now(FUSO_BR).strftime("%Y-%m-%d %H:%M:%S")
            
            novos_registros.append({
                'ID': novo_id,
                'DATA_REGISTRO': data_str,
                'DIA_SEMANA': dia_atual,
                'OPERADOR': tarefa['OPERADOR'],
                'CLIENTE': tarefa['CLIENTE'],
                'STATUS': 'Não Informado',
                'OBSERVACAO': 'Gerado automaticamente pelo sistema.',
                'LOG_AUDITORIA': f'[{log_hora}] Registro automático.'
            })
            
    # Executa a concatenação apenas UMA VEZ no final (muito mais rápido e seguro)
    if novos_registros:
        df_novos = pd.DataFrame(novos_registros)
        st.session_state.df_apontamentos = pd.concat(
            [st.session_state.df_apontamentos, df_novos], 
            ignore_index=True
        )

# Chama inicialização
inicializar_estados()

# Trava de Segurança Visual: Esconde o menu se não estiver logado
if not st.session_state.logged_in:
    st.markdown("""
        <style>
            /* Esconde a barra lateral nativa antes do login */
            [data-testid="stSidebar"] { display: none !important; }
            [data-testid="collapsedControl"] { display: none !important; }
        </style>
    """, unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# INTERFACE DE LOGIN
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
                        st.session_state.role = "Gestor" if usuario.lower() in ["admin", "gestor", "abraao"] else "Operador"
                        st.success("Login realizado!")
                        st.rerun()
                    else:
                        st.error("Usuário ou senha incorretos.")
                except Exception as e:
                    st.error("O servidor está iniciando ou indisponível (Cold Start). Aguarde alguns segundos.")

# -----------------------------------------------------------------------------
# MÓDULOS DA APLICAÇÃO (LAYOUT E UX)
# -----------------------------------------------------------------------------
def aba_dashboard():
    st.header("📈 Dashboard Gerencial")
    df = st.session_state.df_apontamentos

    if df.empty:
        st.info("Nenhum dado de execução registrado até o momento.")
        return

    # Filtros Avançados
    col1, col2, col3 = st.columns(3)
    ops = ["Todos"] + list(df['OPERADOR'].dropna().unique())
    clis = ["Todos"] + list(df['CLIENTE'].dropna().unique())
    status_list = ["Todos"] + list(df['STATUS'].dropna().unique())

    filtro_op = col1.selectbox("Filtrar por Operador", ops)
    filtro_cli = col2.selectbox("Filtrar por Cliente", clis)
    filtro_status = col3.selectbox("Filtrar por Status", status_list)

    # Aplicação de Filtros Reativos
    df_dash = df.copy()
    if filtro_op != "Todos": df_dash = df_dash[df_dash['OPERADOR'] == filtro_op]
    if filtro_cli != "Todos": df_dash = df_dash[df_dash['CLIENTE'] == filtro_cli]
    if filtro_status != "Todos": df_dash = df_dash[df_dash['STATUS'] == filtro_status]

    # Indicadores
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Total de Atividades", len(df_dash))
    kpi2.metric("Realizado Total", len(df_dash[df_dash['STATUS'] == 'Realizado Total']))
    kpi3.metric("Não Realizadas", len(df_dash[df_dash['STATUS'] == 'Não Realizado']))
    kpi4.metric("Não Informadas", len(df_dash[df_dash['STATUS'] == 'Não Informado']))

    if not df_dash.empty:
        st.bar_chart(df_dash['STATUS'].value_counts())

def aba_escala_semanal():
    st.header("📅 Escala Semanal e Cronograma")
    
    if st.session_state.role not in ["Gestor", "Admin"]:
        st.error("Apenas gestores podem alterar o cronograma.")
        st.dataframe(st.session_state.df_escala, use_container_width=True, hide_index=True)
        return

    arquivo = st.file_uploader("Importar planilha de escala (.xlsx ou .csv)", type=['xlsx', 'csv'])

    if arquivo:
        try:
            df_temp = pd.read_csv(arquivo) if arquivo.name.endswith('.csv') else pd.read_excel(arquivo)
            # Padroniza nomes das colunas
            df_temp.columns = df_temp.columns.str.upper()
            st.session_state.df_escala = df_temp
            st.success("Escala carregada!")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

    # Alerta de Duplicidade
    alertas = verificar_duplicidades(st.session_state.df_escala)
    if alertas:
        st.warning("⚠️ Atenção: Detectamos alocações duplicadas na semana:")
        for a in alertas:
            st.write(f"- Operador **{a['OPERADOR']}** está com o cliente **{a['CLIENTE']}** repetido ({a['contagem']} vezes).")

    st.write("### Editor de Escala (CRUD Integrado)")
    st.info("Você pode adicionar, excluir ou alterar as células diretamente na tabela abaixo.")
    
    # CRUD completo via data_editor do Streamlit
    df_editado = st.data_editor(
        st.session_state.df_escala, 
        num_rows="dynamic", 
        use_container_width=True,
        key="editor_escala"
    )

    if st.button("💾 Salvar Alterações do Cronograma"):
        st.session_state.df_escala = df_editado
        st.success("Cronograma salvo e validado com sucesso!")

def aba_relatorios():
    st.header("📊 Relatórios Operacionais")
    df = st.session_state.df_apontamentos

    if df.empty:
        st.warning("Sem dados para gerar relatórios.")
        return

    # Lógica de Filtros corrigida via st.session_state (reativos)
    col1, col2, col3 = st.columns(3)
    ops = ["Todos"] + list(df['OPERADOR'].dropna().unique())
    clis = ["Todos"] + list(df['CLIENTE'].dropna().unique())
    
    f_op = col1.selectbox("Operador", ops, key="rel_op")
    f_cli = col2.selectbox("Cliente", clis, key="rel_cli")
    f_data = col3.date_input("Data do Registro", value=None)

    df_filtrado = df.copy()
    if f_op != "Todos": df_filtrado = df_filtrado[df_filtrado['OPERADOR'] == f_op]
    if f_cli != "Todos": df_filtrado = df_filtrado[df_filtrado['CLIENTE'] == f_cli]
    if f_data: df_filtrado = df_filtrado[df_filtrado['DATA_REGISTRO'] == f_data.strftime('%Y-%m-%d')]

    st.dataframe(df_filtrado, use_container_width=True, hide_index=True)

def aba_lancar_execucao():
    st.header("📝 Lançar Execução Diária")
    hoje = date.today()
    dia_pt = obter_dia_semana_pt(hoje)
    
    st.write(f"**Data:** {hoje.strftime('%d/%m/%Y')} | **Dia:** {dia_pt}")
    
    # Filtro Dinâmico: Busca clientes apenas daquele dia para o operador logado
    escala = st.session_state.df_escala
    clientes_hoje = escala[
        (escala['OPERADOR'] == st.session_state.user) & 
        (escala['DIA_SEMANA'] == dia_pt)
    ]['CLIENTE'].tolist()

    # Adiciona "Suporte" ou "Atividade Interna" como opções padrão
    lista_opcoes = clientes_hoje + ["Suporte", "Atividade Interna"]
    
    if not clientes_hoje:
        st.info("Você não tem clientes alocados no cronograma para o dia de hoje.")

    with st.form("form_lancamento"):
        cliente_sel = st.selectbox("Selecione o Cliente / Atividade", lista_opcoes)
        
        # Sub-filtro condicional se for suporte
        cliente_destino = None
        if cliente_sel == "Suporte":
            todos_clientes = escala['CLIENTE'].dropna().unique().tolist()
            cliente_destino = st.selectbox("Para qual cliente foi o Suporte?", todos_clientes)

        status_trabalho = st.selectbox("Status da Tarefa", ["Realizado Total", "Realizado Parcial", "Não Realizado"]) #[cite: 1]
        
        obs = st.text_area("Justificativa (Obrigatório para Parcial/Não Realizado)", 
                           placeholder="Devido a reunião não foi possível realizar totalmente as tarefas do cliente")

        if st.form_submit_button("🚀 REGISTRAR EXECUÇÃO", use_container_width=True):
            
            # Validação de Justificativa
            if status_trabalho in ["Realizado Parcial", "Não Realizado"] and not obs.strip():
                st.error("A justificativa é obrigatória para status Parcial ou Não Realizado.")
            else:
                # Trata formatação do nome final
                nome_cliente_final = f"Suporte - [{cliente_destino}]" if cliente_sel == "Suporte" else cliente_sel
                
                novo_id = len(st.session_state.df_apontamentos) + 1
                log_ini = f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Criado por {st.session_state.user}."
                
                novo_registro = {
                    'ID': novo_id,
                    'DATA_REGISTRO': hoje.strftime('%Y-%m-%d'),
                    'DIA_SEMANA': dia_pt,
                    'OPERADOR': st.session_state.user,
                    'CLIENTE': nome_cliente_final,
                    'STATUS': status_trabalho,
                    'OBSERVACAO': obs,
                    'LOG_AUDITORIA': log_ini
                }
                st.session_state.df_apontamentos = pd.concat(
                    [st.session_state.df_apontamentos, pd.DataFrame([novo_registro])],
                    ignore_index=True
                )
                st.success("Apontamento registrado com sucesso!")

def aba_editor_apontamentos():
    st.header("⚙️ Editor de Apontamentos (Gestor)")

    if st.session_state.role not in ["Gestor", "Admin"]:
        st.error("🚫 Acesso Negado: Apenas Gestores e Admins podem auditar e editar apontamentos.")
        return

    df = st.session_state.df_apontamentos
    if df.empty:
        st.warning("Não há registros para editar.")
        return

    # Seleção por ID para garantir precisão
    id_selecionado = st.selectbox("Selecione o ID do Apontamento para Editar", df['ID'].tolist())
    
    if id_selecionado:
        registro_atual = df[df['ID'] == id_selecionado].iloc[0]
        
        st.write("---")
        st.write(f"**Operador:** {registro_atual['OPERADOR']} | **Data:** {registro_atual['DATA_REGISTRO']}")
        
        with st.form("form_edicao"):
            novo_cliente = st.text_input("Cliente", value=registro_atual['CLIENTE'])
            novo_status = st.selectbox("Status", ["Realizado Total", "Realizado Parcial", "Não Realizado", "Não Informado"], 
                                       index=["Realizado Total", "Realizado Parcial", "Não Realizado", "Não Informado"].index(registro_atual['STATUS']))
            nova_obs = st.text_area("Observação / Justificativa", value=registro_atual['OBSERVACAO'])
            
            if st.form_submit_button("Salvar Edição"):
                idx = df[df['ID'] == id_selecionado].index[0]
                
                # Registra o log de auditoria
                log_antigo = st.session_state.df_apontamentos.at[idx, 'LOG_AUDITORIA']
                data_hora = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                nova_linha_log = f"\n[{data_hora}] Editado por {st.session_state.user}. Alterações feitas."
                
                st.session_state.df_apontamentos.at[idx, 'CLIENTE'] = novo_cliente
                st.session_state.df_apontamentos.at[idx, 'STATUS'] = novo_status
                st.session_state.df_apontamentos.at[idx, 'OBSERVACAO'] = nova_obs
                st.session_state.df_apontamentos.at[idx, 'LOG_AUDITORIA'] = log_antigo + nova_linha_log
                
                st.success("Apontamento auditado e atualizado!")
                st.rerun()

        st.write("### Histórico de Auditoria do Registro")
        st.code(registro_atual['LOG_AUDITORIA'])

# -----------------------------------------------------------------------------
# MOTOR PRINCIPAL E ROTEAMENTO (UX E SEGURANÇA PREMIUM)
# -----------------------------------------------------------------------------
if not st.session_state.logged_in:
    tela_login()
else:
    # Executa verificação silenciosa de auto-status toda vez que logar
    consolidar_nao_informados()

    with st.sidebar:
        # 1. Logo e Identidade Visual (Cores Corporativas)
        st.markdown(f"""
            <div style='text-align: center; padding: 15px; background-color: #001E57; border-radius: 8px; margin-bottom: 20px; border: 1px solid rgba(255, 255, 255, 0.05); box-shadow: 0 4px 6px rgba(0,0,0,0.1);'>
                <h2 style='color: #FFFFFF; margin: 0; font-weight: 800; letter-spacing: 1px;'>DUARTE</h2>
                <h5 style='color: #FF9200; margin: 0; font-weight: 600; text-transform: uppercase;'>Performance</h5>
            </div>
        """, unsafe_allow_html=True)
        
        # 2. Card do Usuário Logado
        st.markdown(f"""
            <div style='padding: 15px; background: rgba(255, 255, 255, 0.05); border-radius: 8px; margin-bottom: 20px;'>
                <p style='margin: 0; color: #CBD5E1; font-size: 0.85rem;'>Conectado como:</p>
                <h4 style='margin: 5px 0; color: #FFFFFF; font-weight: bold;'>👤 {str(st.session_state.user).title()}</h4>
                <div style='display: inline-block; padding: 4px 10px; background-color: #FF9200; color: #001E57; font-size: 0.75rem; border-radius: 12px; font-weight: 900;'>
                    🛡️ {st.session_state.role.upper()}
                </div>
            </div>
        """, unsafe_allow_html=True)
        
        st.divider()

        # 3. Controle de Acesso Dinâmico no Menu
        opcoes_menu = [
            "📈 Dashboard Gerencial",
            "📅 Escala Semanal",
            "📝 Lançar Execução Diária",
            "📊 Relatórios Operacionais"
        ]
        
        # Apenas Gestor/Admin enxerga a opção de auditar/editar no menu
        if st.session_state.role in ["Gestor", "Admin"]:
            opcoes_menu.append("⚙️ Editor de Apontamentos")

        menu_selecionado = st.radio(
            "Navegação",
            opcoes_menu,
            label_visibility="collapsed" # Esconde o texto "Navegação" para ficar mais clean
        )

        st.divider()
        
        # 4. Botão de Logout de Alta Responsividade e Segurança
        if st.button("🚪 Encerrar Sessão", use_container_width=True):
            # Limpa TODAS as chaves da sessão para evitar vazamento de dados no cache
            for key in list(st.session_state.keys()):
                del st.session_state[key]
            st.rerun()

    # Roteamento de Telas
    if menu_selecionado == "📈 Dashboard Gerencial": 
        aba_dashboard()
    elif menu_selecionado == "📅 Escala Semanal": 
        aba_escala_semanal()
    elif menu_selecionado == "📝 Lançar Execução Diária": 
        aba_lancar_execucao()
    elif menu_selecionado == "📊 Relatórios Operacionais": 
        aba_relatorios()
    elif menu_selecionado == "⚙️ Editor de Apontamentos": 
        aba_editor_apontamentos()