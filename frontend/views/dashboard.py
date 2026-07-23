import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render_dashboard(api_get):
    # Header Principal da Tela
    st.markdown("""
    <div style="margin-bottom: 25px;">
        <h1 style="color: #001E57; font-weight: 900; font-size: 2.2rem; margin-bottom: 4px;">
            📊 Dashboard Gerencial de Performance
        </h1>
        <p style="color: #64748B; font-size: 1rem; margin: 0;">
            Acompanhamento em tempo real das métricas operacionais e status de entregas.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Carregando indicadores..."):
        resp_reg = api_get("/registros/")

    if resp_reg.status_code != 200:
        st.error("⚠️ Não foi possível carregar os dados do backend no momento.")
        return

    dados = resp_reg.json()
    df_reg = pd.DataFrame(dados) if dados else pd.DataFrame()

    if df_reg.empty:
        st.info("ℹ️ Nenhum apontamento registrado até o momento para exibição das métricas.")
        return

    # Tratamento básico de colunas para garantir exibição
    col_status = 'status' if 'status' in df_reg.columns else 'Status'
    col_cliente = 'cliente_nome' if 'cliente_nome' in df_reg.columns else ('cliente' if 'cliente' in df_reg.columns else 'Cliente')

    # Cálculos de Métricas
    total_registros = len(df_reg)
    concluidos = len(df_reg[df_reg[col_status].astype(str).str.contains("Realizado Total|Concluído|OK", case=False, na=False)])
    parciais_pendentes = total_registros - concluidos
    taxa_eficiencia = (concluidos / total_registros * 100) if total_registros > 0 else 0

    # ================= 1. CARDS DE KPIS ANIMADOS =================
    st.markdown("""
    <style>
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            margin-bottom: 25px;
        }
        .kpi-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 20px;
            box-shadow: 0 4px 20px rgba(0,0,0,0.03);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            animation: fadeInUp 0.5s ease-out forwards;
            position: relative;
            overflow: hidden;
        }
        .kpi-card:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 25px rgba(0, 30, 87, 0.12);
            border-color: #FF9200;
        }
        .kpi-title {
            color: #64748B;
            font-size: 0.85rem;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            margin-bottom: 8px;
        }
        .kpi-value {
            color: #001E57;
            font-size: 1.8rem;
            font-weight: 900;
        }
        .kpi-sub {
            color: #FF9200;
            font-size: 0.8rem;
            font-weight: 600;
            margin-top: 4px;
        }
        .kpi-stripe {
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: linear-gradient(90deg, #001E57 0%, #FF9200 100%);
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-stripe"></div>
            <div class="kpi-title">Total de Registros</div>
            <div class="kpi-value">{total_registros}</div>
            <div class="kpi-sub">📋 Apontamentos ativos</div>
        </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-stripe"></div>
            <div class="kpi-title">Concluídos / Total</div>
            <div class="kpi-value" style="color: #10B981;">{concluidos}</div>
            <div class="kpi-sub">✅ Execuções completas</div>
        </div>
        """, unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-stripe"></div>
            <div class="kpi-title">Parciais / Atenção</div>
            <div class="kpi-value" style="color: #F59E0B;">{parciais_pendentes}</div>
            <div class="kpi-sub">⚠️ Requer acompanhamento</div>
        </div>
        """, unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="kpi-card">
            <div class="kpi-stripe"></div>
            <div class="kpi-title">Taxa de Eficiência</div>
            <div class="kpi-value" style="color: #FF9200;">{taxa_eficiencia:.1f}%</div>
            <div class="kpi-sub">🎯 Performance média</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ================= 2. GRÁFICOS VISUAIS INTERATIVOS =================
    g_col1, g_col2 = st.columns([1, 1.3], gap="large")

    with g_col1:
        st.markdown("##### 📌 Status dos Apontamentos")
        if col_status in df_reg.columns:
            status_counts = df_reg[col_status].value_counts().reset_index()
            status_counts.columns = ['Status', 'Qtd']

            fig_donut = px.pie(
                status_counts, 
                names='Status', 
                values='Qtd', 
                hole=0.55,
                color_discrete_sequence=['#001E57', '#FF9200', '#0B296B', '#CBD5E1']
            )
            fig_donut.update_traces(
                textposition='inside', 
                textinfo='percent+label',
                marker=dict(line=dict(color='#FFFFFF', width=2))
            )
            fig_donut.update_layout(
                showlegend=False,
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=280
            )
            st.plotly_chart(fig_donut, use_container_width=True)

    with g_col2:
        st.markdown("##### 🏢 Top Clientes em Operação")
        if col_cliente in df_reg.columns:
            top_clientes = df_reg[col_cliente].value_counts().head(7).reset_index()
            top_clientes.columns = ['Cliente', 'Qtd']

            fig_bar = px.bar(
                top_clientes, 
                x='Qtd', 
                y='Cliente', 
                orientation='h',
                text='Qtd',
                color_discrete_sequence=['#FF9200']
            )
            fig_bar.update_traces(
                texttemplate='%{text}', 
                textposition='outside',
                marker=dict(cornerRadius=6)
            )
            fig_bar.update_layout(
                yaxis=dict(autorange="reversed", title=None),
                xaxis=dict(title=None, showgrid=False),
                margin=dict(t=10, b=10, l=10, r=10),
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                height=280
            )
            st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # ================= 3. DETALHAMENTO DOS DADOS =================
    st.markdown("### 🔍 Detalhamento dos Registros")

    # Busca rápida
    termo_busca = st.text_input("🔎 Pesquisar cliente ou operador na visão geral:", placeholder="Digite para filtrar...")

    df_exibicao = df_reg.copy()
    if termo_busca:
        mask = df_exibicao.astype(str).apply(lambda row: row.str.contains(termo_busca, case=False).any(), axis=1)
        df_exibicao = df_exibicao[mask]

    st.dataframe(
        df_exibicao,
        use_container_width=True,
        hide_index=True,
        column_config={
            col_status: st.column_config.TextColumn("Status", help="Situação da atividade"),
            col_cliente: st.column_config.TextColumn("Cliente", help="Nome do cliente/provedor")
        }
    )