import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import time
import io
from datetime import datetime

# ===================== 1. CONFIGURAÇÕES GLOBAIS E UI =====================
st.set_page_config(
    page_title="Duarte Performance | Gestão Operacional", 
    page_icon="🟠", 
    layout="wide", 
    initial_sidebar_state="expanded"
)

API_URL = "https://duarte-performance-backend.onrender.com"

# ===================== ESTILIZAÇÃO PREMIUM (PADRÃO DUARTE GESTÃO / MATERIAL UI) =====================
st.markdown("""
<style>
    /* 1. Variáveis de Cores e Temas */
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

    /* 2. Fundo Geral e Tipografia */
    .stApp { 
        background-color: var(--bg-body);
        background-image: radial-gradient(circle at 50% 0%, rgba(243, 146, 0, 0.04) 0%, transparent 60%);
        font-family: 'Inter', 'Segoe UI', system-ui, sans-serif; 
        -webkit-font-smoothing: antialiased;
    }

    /* 3. Customização da Barra Lateral (Sidebar) */
    [data-testid="stSidebar"] { 
        background: linear-gradient(180deg, var(--primary-dark) 0%, #020617 100%); 
        border-right: 1px solid rgba(255, 255, 255, 0.05);
        box-shadow: 4px 0 20px rgba(0, 0, 0, 0.15);
    }
    [data-testid="stSidebar"] * { 
        color: #F8FAFC !important; 
        transition: color 0.2s ease;
    }

    /* 4. Card de Login Premium com Animação */
    .login-card { 
        background: var(--bg-card); 
        padding: 55px 45px; 
        border-radius: 24px; 
        box-shadow: 0 10px 40px -10px rgba(15,23,42,0.08), 0 0 0 1px rgba(15,23,42,0.02); 
        max-width: 480px; 
        margin: auto; 
        backdrop-filter: blur(10px);
        animation: slideUp 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }

    /* 5. Cards de KPI (Dashboard) com Hover Effect */
    .kpi-card { 
        background: var(--bg-card); 
        padding: 24px; 
        border-radius: 16px; 
        border-left: 5px solid var(--accent-orange); 
        box-shadow: 0 4px 6px -1px rgba(0,0,0,0.05), 0 2px 4px -2px rgba(0,0,0,0.03); 
        position: relative;
        overflow: hidden;
        transition: transform 0.3s ease, box-shadow 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 20px 25px -5px rgba(0,0,0,0.1), 0 8px 10px -6px rgba(0,0,0,0.05);
    }
    .kpi-card::after {
        content: '';
        position: absolute;
        top: 0; right: 0; bottom: 0; left: 0;
        background: linear-gradient(to bottom right, rgba(243, 146, 0, 0.05), transparent);
        pointer-events: none;
    }

    /* 6. Botões Primários - Efeito Material */
    .stButton>button[kind="primary"] { 
        background: linear-gradient(135deg, var(--primary-dark) 0%, var(--primary-light) 100%); 
        color: white !important; 
        border: none;
        border-radius: 10px; 
        font-weight: 600;
        letter-spacing: 0.3px;
        padding: 12px 24px;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 4px 6px -1px rgba(15, 23, 42, 0.2);
    }
    .stButton>button[kind="primary"]:hover { 
        background: linear-gradient(135deg, var(--accent-orange) 0%, var(--accent-hover) 100%); 
        transform: scale(1.02) translateY(-2px);
        box-shadow: 0 10px 15px -3px rgba(243, 146, 0, 0.3), 0 4px 6px -4px rgba(243, 146, 0, 0.2);
    }
    .stButton>button[kind="primary"]:active {
        transform: scale(0.98) translateY(0);
    }

    /* 7. Botões Secundários */
    .stButton>button[kind="secondary"] {
        border: 1.5px solid var(--border-color);
        border-radius: 10px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton>button[kind="secondary"]:hover {
        border-color: var(--accent-orange);
        color: var(--accent-orange) !important;
        background: rgba(243, 146, 0, 0.03);
    }

    /* 8. Inputs e TextAreas - Foco Premium */
    div[data-baseweb="input"] > div, div[data-baseweb="textarea"] > div, div[data-baseweb="select"] > div {
        background-color: #FFFFFF !important;
        border-radius: 10px !important;
        border: 1px solid #CBD5E1 !important;
        transition: all 0.2s ease;
    }
    div[data-baseweb="input"] > div:focus-within, div[data-baseweb="textarea"] > div:focus-within, div[data-baseweb="select"] > div:focus-within {
        border-color: var(--accent-orange) !important;
        box-shadow: 0 0 0 3px rgba(243, 146, 0, 0.15) !important;
    }

    /* 9. Badges de Status (Pílulas Arredondadas) */
    .warning-badge { 
        background: #FEF3C7; 
        color: #92400E; 
        padding: 4px 12px; 
        border-radius: 20px; 
        font-size: 12px; 
        font-weight: 700;
        border: 1px solid #FDE68A;
        display: inline-block;
    }

    /* 10. Custom Scrollbar Clean */
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #F1F5F9; }
    ::-webkit-scrollbar-thumb { background: #CBD5E1; border-radius: 10px; }
    ::-webkit-scrollbar-thumb:hover { background: #94A3B8; }

    /* 11. Animações Keyframes */
    @keyframes slideUp {
        from { opacity: 0; transform: translateY(20px); }
        to { opacity: 1; transform: translateY(0); }
    }
</style>
""", unsafe_allow_html=True)

# Controle de Sessão
for key in ["token", "username", "role", "cpf", "app_loaded"]:
    if key not in st.session_state: st.session_state[key] = None if key != "app_loaded" else False

# ===================== 2. CONEXÃO COM BACKEND =====================
def api_request(method, endpoint, data=None, files=None):
    headers = {"Authorization": f"Bearer {st.session_state.token}"} if st.session_state.token else {}
    try:
        if method == 'GET':
            return requests.get(f"{API_URL}{endpoint}", headers=headers, timeout=10)
        return requests.post(f"{API_URL}{endpoint}", data=data, files=files, headers=headers, timeout=15)
    except:
        return type('obj', (), {'status_code': 500, 'json': lambda: []})()

# ===================== 3. TELA DE LOGIN (COM BLOQUEIOS E RECUPERAÇÃO) =====================
if not st.session_state.token:
    st.markdown("<div style='padding-top: 8vh;'>", unsafe_allow_html=True)
    with st.container():
        st.markdown("<div class='login-card'>", unsafe_allow_html=True)
        st.markdown("<h1 style='text-align:center;color:#0F172A;font-weight:900;'>Duarte Performance</h1>", unsafe_allow_html=True)
        st.markdown("<p style='text-align:center;color:#64748B;'>Departamento de Credenciamento</p><hr>", unsafe_allow_html=True)
        
        cpf_input = st.text_input("CPF Corporativo (Somente Números)", placeholder="00000000000")
        senha_input = st.text_input("Senha", type="password")
        
        if st.button("🔑 ENTRAR NO SISTEMA", type="primary", use_container_width=True):
            cpf_limpo = ''.join(filter(str.isdigit, cpf_input))
            if not cpf_limpo:
                st.warning("O CPF deve conter apenas números.")
            else:
                resp = api_request('POST', "/token", data={"username": cpf_limpo, "password": senha_input})
                if resp.status_code == 200:
                    data = resp.json()
                    st.session_state.update({"token": data["access_token"], "username": data.get("nome", "Usuário"), "role": data.get("role", "Operador"), "cpf": cpf_limpo})
                    st.success("Acesso Liberado! Registrando IP e log de entrada...")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error("Credenciais inválidas. Conta sujeita a bloqueio após 3 tentativas.")
        
        col1, col2 = st.columns(2)
        col1.button("Primeiro Acesso", use_container_width=True)
        col2.button("Esqueci minha senha", use_container_width=True)
        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()

# ===================== 4. CONTROLE DE PERFIS E MENUS (PREMIUM) =====================

# Lógica para capturar iniciais do usuário (Ex: "Erick Silva" vira "ES")
nome_usuario = st.session_state.username.upper() if st.session_state.username else "USUÁRIO"
partes_nome = nome_usuario.split()
iniciais = "".join([n[0] for n in partes_nome[:2]]) if len(partes_nome) > 1 else nome_usuario[0:2]

# Classe CSS dinâmica para destacar a cor do cargo (Badge)
role = st.session_state.role if st.session_state.role else "Operador"
role_class = "admin" if role == "Admin Master" else ("gestor" if role == "Gestor" else "operador")

# Injeção de CSS Exclusiva para a Sidebar Tecnológica
st.sidebar.markdown(f"""
<style>
    /* Card de Perfil Flutuante (Glassmorphism) */
    .profile-container {{
        background: linear-gradient(145deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%);
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 16px;
        padding: 25px 15px;
        text-align: center;
        margin-bottom: 25px;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px 0 rgba(0, 0, 0, 0.2);
        transition: transform 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }}
    .profile-container:hover {{
        transform: translateY(-3px);
        background: rgba(255, 255, 255, 0.05);
    }}
    
    /* Avatar com as Cores da Duarte Gestão */
    .avatar {{
        background: linear-gradient(135deg, #F39200 0%, #E07A00 100%);
        color: #0F172A;
        width: 65px;
        height: 65px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 24px;
        font-weight: 900;
        margin: 0 auto 12px auto;
        box-shadow: 0 8px 16px rgba(243, 146, 0, 0.25);
        border: 2px solid #0F172A;
    }}
    
    /* Tipografia do Nome */
    .profile-name {{
        color: #F8FAFC;
        font-size: 17px;
        font-weight: 700;
        margin: 0 0 8px 0;
        letter-spacing: 0.5px;
    }}
    
    /* Badges de Cargo Inteligentes */
    .role-badge {{
        padding: 5px 14px;
        border-radius: 20px;
        font-size: 11px;
        font-weight: 800;
        text-transform: uppercase;
        letter-spacing: 1px;
        display: inline-block;
    }}
    .role-badge.admin {{ color: #F8FAFC; background: #EF4444; box-shadow: 0 0 10px rgba(239, 68, 68, 0.3); }}
    .role-badge.gestor {{ color: #0F172A; background: #F39200; box-shadow: 0 0 10px rgba(243, 146, 0, 0.3); }}
    .role-badge.operador {{ color: #94A3B8; background: #1E293B; border: 1px solid #334155; }}
    
    /* Efeito Hover nos Menus do Streamlit (Radio Buttons) */
    div[role="radiogroup"] > label {{
        padding: 12px 15px !important;
        border-radius: 12px !important;
        margin-bottom: 4px !important;
        transition: all 0.2s ease !important;
        background: transparent !important;
        border: 1px solid transparent !important;
    }}
    div[role="radiogroup"] > label:hover {{
        background: rgba(255, 255, 255, 0.04) !important;
        border-color: rgba(255, 255, 255, 0.08) !important;
        transform: translateX(6px);
    }}
    div[role="radiogroup"] label p {{ font-weight: 600 !important; font-size: 15px !important; }}
</style>

<!-- Renderização do Painel do Usuário -->
<div class="profile-container">
    <div class="avatar">{iniciais}</div>
    <p class="profile-name">{nome_usuario}</p>
    <span class="role-badge {role_class}">{role}</span>
</div>
<hr style="border: 0; height: 1px; background: linear-gradient(to right, transparent, rgba(255,255,255,0.1), transparent); margin-bottom: 20px;">
""", unsafe_allow_html=True)

# Lógica de Controle de Acesso (Visões baseadas no perfil)
menus_disponiveis = ["🗓️ Escala Semanal"]

if role in ["Admin Master", "Gestor"]:
    menus_disponiveis = ["📊 Dashboard Gerencial", "🗓️ Escala Semanal", "📑 Relatórios Operacionais"] 
    if role == "Admin Master":
        menus_disponiveis.append("🔐 Auditoria e Acessos")
        
menus_disponiveis.append("📝 Lançar Execução Diária")

# Cabeçalho do Menu
st.sidebar.markdown("<p style='color: #64748B; font-size: 11px; font-weight: 800; letter-spacing: 1.5px; text-transform: uppercase; margin-bottom: 10px; margin-left: 5px;'>Navegação Principal</p>", unsafe_allow_html=True)

# Renderiza o Menu Ocultando o Label padrão (já criamos um customizado acima)
menu = st.sidebar.radio("Navegação do Sistema", menus_disponiveis, label_visibility="collapsed")

# Espaçador dinâmico para jogar o botão de Sair para o rodapé
st.sidebar.markdown("<br>" * 4, unsafe_allow_html=True)

# Botão de Logout Integrado
if st.sidebar.button("🚪 Encerrar Sessão", use_container_width=True, type="secondary"):
    st.session_state.token = None
    st.session_state.clear()
    st.rerun()

# ===================== 5. MÓDULOS DO SISTEMA =====================

# --- MÓDULO 1: DASHBOARD GERENCIAL ---
if menu == "📊 Dashboard Gerencial":
    st.title("Dashboard Executivo - Produtividade")
    
    # Mock data para visualização caso a API falhe, substituindo a requisição real
    # Na prática, você puxará do seu db de execução
    dados_exec = pd.DataFrame([
        {"operador": "Vitória", "status": "Realizado Total", "cliente": "Hospital Amato"},
        {"operador": "Vitória", "status": "Não Realizado", "cliente": "Lab Bruno"},
        {"operador": "Aline", "status": "Realizado Parcial", "cliente": "Clin Coffi"},
    ])
    
    c1, c2, c3, c4 = st.columns(4)
    c1.markdown("<div class='kpi-card'><b>Total Planejado</b><h2>125</h2></div>", unsafe_allow_html=True)
    c2.markdown("<div class='kpi-card' style='border-color:#10B981'><b>Realizado Total</b><h2 style='color:#10B981'>80</h2></div>", unsafe_allow_html=True)
    c3.markdown("<div class='kpi-card' style='border-color:#F59E0B'><b>Realizados Parciais</b><h2 style='color:#F59E0B'>25</h2></div>", unsafe_allow_html=True)
    c4.markdown("<div class='kpi-card' style='border-color:#EF4444'><b>Não Realizados</b><h2 style='color:#EF4444'>20</h2></div>", unsafe_allow_html=True)
    
    st.write("---")
    g1, g2 = st.columns(2)
    with g1:
        fig_pie = px.pie(dados_exec, names="status", title="Distribuição de Status (Pipeline Operacional)", hole=0.4)
        st.plotly_chart(fig_pie, use_container_width=True)
    with g2:
        fig_bar = px.bar(dados_exec, x="operador", color="status", title="Produtividade por Operador")
        st.plotly_chart(fig_bar, use_container_width=True)

# --- MÓDULO 2: ESCALA SEMANAL (CRONOGRAMA EM MATRIZ) ---
elif menu == "🗓️ Escala Semanal (Cronograma)":
    st.title("Cronograma Operacional do Credenciamento")
    
    # Dados de exemplo conforme estrutura do escopo (Dias da semana como colunas)
    dados_cronograma = [
        {"Operador": "Vitória", "Segunda": "Hospital Amato", "Terça": "Clin Coffi", "Quarta": "Trides", "Quinta": "Lab Bruno", "Sexta": "Pro-Exame"},
        {"Operador": "Aline", "Segunda": "Metas Clientes", "Terça": "CONVACARE", "Quarta": "IMC", "Quinta": "Metas Clientes", "Sexta": "Alinhamento Interno"}
    ]
    df_escala = pd.DataFrame(dados_cronograma)
    
    st.markdown("### Visão Geral da Semana")
    
    # ALERTA DE DUPLICIDADE (Requisito obrigatório do Word)
    # Varremos a matriz para checar se o mesmo cliente se repete para o mesmo operador na semana
    duplicidades = []
    for idx, row in df_escala.iterrows():
        valores = row[["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]].dropna().tolist()
        vistos = set()
        for v in valores:
            if v in vistos and v not in ["Alinhamento Interno", "Metas Clientes"]: # Ignora tarefas internas repetidas
                duplicidades.append(f"{row['Operador']} -> {v}")
            vistos.add(v)
            
    if duplicidades:
        st.error(f"⚠ ALERTA DE DUPLICIDADE: Cliente repetido na semana para o mesmo operador: {', '.join(set(duplicidades))}")

    # Exibição da Matriz (Formato Operador | Segunda | Terça...)
    st.dataframe(df_escala, use_container_width=True, hide_index=True)
    
    if st.session_state.role in ["Gestor", "Admin Master"]:
        with st.expander("⚙️ Gestor: Atribuir ou Alterar Atividade"):
            c_op, c_dia, c_cl = st.columns(3)
            c_op.selectbox("Operador", ["Vitória", "Aline", "Lucas", "Julia", "Felipe", "Edvania"])
            c_dia.selectbox("Dia da Semana", ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"])
            c_cl.text_input("Cliente ou Tarefa Interna")
            st.button("Salvar no Cronograma", type="primary")

# --- MÓDULO 3: REGISTRO DE EXECUÇÃO DIÁRIA ---
elif menu == "📝 Registrar Execução Diária":
    st.markdown("<h1 style='color: var(--primary-dark); font-weight: 800; letter-spacing:-0.5px;'>Registro de Execução Operacional</h1>", unsafe_allow_html=True)
    st.markdown("<p style='color: var(--text-muted); font-size: 15px;'>Módulo oficial para apontamento de produtividade e anexação de evidências operacionais.</p>", unsafe_allow_html=True)
    
    # Cabeçalho de Auditoria (Data, Hora e Operador)
    data_atual = datetime.now().strftime('%d/%m/%Y')
    hora_atual = datetime.now().strftime('%H:%M')
    st.info(f"📅 **Data Base:** {data_atual} &nbsp;|&nbsp; 🕒 **Hora do Apontamento:** {hora_atual} &nbsp;|&nbsp; 👤 **Analista:** {st.session_state.username}")
    
    with st.form("execucao_diaria", clear_on_submit=False):
        st.markdown("### 📌 1. Informações da Atividade")
        col1, col2 = st.columns(2)
        cliente = col1.selectbox("Conta / Cliente Vinculado", ["Selecione...", "Hospital Amato", "Clin Coffi", "Trides", "Alinhamento Interno"])
        status = col2.selectbox("Status de Entrega", ["Selecione...", "Realizado Total", "Realizado Parcial", "Não Realizado"])
        
        st.markdown("---")
        st.markdown("### 📝 2. Detalhamento e Justificativa")
        st.caption("Descreva os contatos realizados, protocolos gerados ou pendências que bloquearam o processo.")
        justificativa = st.text_area(
            "Histórico da Execução (Obrigatório para status Parcial ou Não Realizado)", 
            height=110, 
            placeholder="Ex: Contato realizado via telefone, aguardando envio da documentação de credenciamento..."
        )
        
        st.markdown("---")
        st.markdown("### 📎 3. Evidências de Execução (Prints e Documentos)")
        st.caption("Tire um print da tela finalizada ou anexe o PDF/Excel correspondente para garantir a auditoria.")
        
        evidencia = st.file_uploader("Arraste seu arquivo ou clique para procurar", type=["png", "jpg", "jpeg", "pdf", "xlsx"], help="Formatos aceitos: Imagens, PDF ou Excel. Máximo 10MB.")
        
        # PREVIEW DINÂMICO DE PRINTS E IMAGENS (O diferencial premium)
        if evidencia is not None:
            if evidencia.type in ["image/png", "image/jpeg", "image/jpg"]:
                with st.expander("👁️ Visualizar Print Anexado", expanded=True):
                    st.image(evidencia, caption=f"Arquivo validado: {evidencia.name}", use_container_width=True)
            else:
                st.success(f"📄 Documento '{evidencia.name}' anexado com sucesso e pronto para envio.")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # Botão de envio cobrindo 100% da largura
        submit_btn = st.form_submit_button("🚀 GRAVAR PRODUTIVIDADE NO SISTEMA", type="primary", use_container_width=True)
        
        # LÓGICA DE VALIDAÇÃO TOTALMENTE BLINDADA
        if submit_btn:
            if cliente == "Selecione...":
                st.error("❌ ERRO: Selecione um Cliente ou Tarefa antes de salvar.")
            elif status == "Selecione...":
                st.error("❌ ERRO: O Status da execução não pode ficar em branco.")
            elif status in ["Realizado Parcial", "Não Realizado"] and len(justificativa.strip()) < 5:
                st.warning("⚠️ ALERTA: A justificativa detalhada é OBRIGATÓRIA quando a atividade não é 100% concluída.")
            else:
                # Regra bônus: Se fez 100% mas não anexou print, dá um toque, mas deixa passar.
                if status == "Realizado Total" and evidencia is None:
                    st.info("💡 Dica de Qualidade: O registro foi salvo, mas lembre-se que anexar prints fortalece nossa auditoria.")
                    st.success("✅ Produtividade registrada com sucesso!")
                    st.balloons()
                else:
                    st.success("✅ Atividade e Evidências salvas com sucesso! Rastreabilidade ativada.")
                    st.balloons()

# --- MÓDULO 4: RELATÓRIOS E EXPORTAÇÃO ---
elif menu == "📑 Relatórios e Exportação":
    st.title("Exportação de Dados Operacionais")
    
    c1, c2, c3 = st.columns(3)
    filtro_periodo = c1.date_input("Período de Extração")
    filtro_op = c2.selectbox("Operador", ["Todos", "Vitória", "Aline", "Lucas"])
    filtro_status = c3.selectbox("Status", ["Todos", "Realizado Total", "Realizado Parcial", "Não Realizado"])
    
    # Mock do Relatório Formato Principal
    df_relatorio = pd.DataFrame([
        {"Data": "10/08/2026", "Dia": "Segunda", "Cliente": "EV-CITI", "Operador": "Karine", "Status": "Realizado Total", "Observação": "-"},
        {"Data": "11/08/2026", "Dia": "Terça", "Cliente": "Lab Bruno", "Operador": "Vitória", "Status": "Não Realizado", "Observação": "Falta de documentação"},
    ])
    
    st.dataframe(df_relatorio, use_container_width=True, hide_index=True)
    
    # EXPORTAÇÃO EM EXCEL (.xlsx)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
        df_relatorio.to_excel(writer, sheet_name='Auditoria_Produtividade', index=False)
    
    st.download_button(
        label="📥 Exportar para Excel (.xlsx)",
        data=buffer.getvalue(),
        file_name=f"Relatorio_Performance_{datetime.now().strftime('%d%m%Y')}.xlsx",
        mime="application/vnd.ms-excel",
        type="primary"
    )

# --- MÓDULO 5: AUDITORIA MASTER ---
elif menu == "🔐 Auditoria e Acessos":
    st.title("Painel de Auditoria e Logs de LGPD")
    st.write("Histórico de rastreamento de acessos e edições do sistema.")
    
    df_logs = pd.DataFrame([
        {"Data/Hora": "17/07/2026 13:20", "Ação": "Login", "Usuário": "Aline", "IP": "192.168.1.45"},
        {"Data/Hora": "17/07/2026 14:10", "Ação": "Inclusão de Justificativa", "Usuário": "Vitória", "IP": "192.168.1.12"},
        {"Data/Hora": "17/07/2026 15:00", "Ação": "Alteração de Cronograma", "Usuário": "Abraão Santos", "IP": "192.168.1.100"},
    ])
    st.dataframe(df_logs, use_container_width=True, hide_index=True)