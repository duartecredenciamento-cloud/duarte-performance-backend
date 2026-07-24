import os
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import requests
import streamlit as st

# URL base da API
API_URL = os.getenv(
    "BACKEND_URL", "https://duarte-performance-backend.onrender.com"
)


def fetch_dashboard_data():
    """Busca os registros de execução no backend com suporte a autenticação."""
    token = st.session_state.get("token", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    try:
        res = requests.get(
            f"{API_URL}/execucoes/", headers=headers, timeout=10
        )
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 401:
            st.error("🔒 Sessão expirada. Por favor, faça login novamente.")
            return None
        else:
            return None
    except Exception:
        return None


def inject_custom_css():
    """Injeta animações avançadas e estilos de nível executivo."""
    st.markdown(
        """
    <style>
        /* ---------------- ANIMAÇÕES KEYFRAMES AVANÇADAS ---------------- */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(22px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes floatGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        @keyframes pulseGlow {
            0% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.6); }
            70% { box-shadow: 0 0 0 14px rgba(255, 146, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
        }

        @keyframes shimmer {
            0% { background-position: -200% 0; }
            100% { background-position: 200% 0; }
        }

        /* ---------------- HEADER EXECUTIVO ANIMADO ---------------- */
        .dash-header {
            background: linear-gradient(-45deg, #001E57, #030A1A, #0A2540, #001233);
            background-size: 300% 300%;
            animation: floatGradient 12s ease infinite, fadeIn 0.8s cubic-bezier(0.16, 1, 0.3, 1);
            border-radius: 20px;
            padding: 28px 36px;
            color: #FFFFFF;
            border-left: 6px solid #FF9200;
            margin-bottom: 28px;
            box-shadow: 0 15px 35px rgba(0, 30, 87, 0.25);
            position: relative;
            overflow: hidden;
        }

        .dash-header::after {
            content: '';
            position: absolute;
            top: 0; left: -100%; width: 50%; height: 100%;
            background: linear-gradient(90deg, transparent, rgba(255,255,255,0.08), transparent);
            transform: skewX(-25deg);
            animation: shimmer 6s infinite;
        }

        .badge-live {
            background: rgba(16, 185, 129, 0.15);
            border: 1px solid #10B981;
            color: #10B981;
            padding: 6px 14px;
            border-radius: 99px;
            font-weight: 700;
            font-size: 0.78rem;
            letter-spacing: 0.8px;
            display: inline-flex;
            align-items: center;
            gap: 6px;
        }

        .badge-live-dot {
            width: 8px;
            height: 8px;
            background-color: #10B981;
            border-radius: 50%;
            box-shadow: 0 0 8px #10B981;
        }

        /* ---------------- CARDS DE KPI METRIC GLASSMORPHISM ---------------- */
        .kpi-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
            gap: 16px;
            margin-bottom: 25px;
            animation: fadeIn 1s cubic-bezier(0.16, 1, 0.3, 1);
        }

        .kpi-card {
            background: rgba(255, 255, 255, 0.85);
            backdrop-filter: blur(12px);
            border: 1px solid rgba(226, 232, 240, 0.8);
            border-radius: 18px;
            padding: 20px 16px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.03);
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .kpi-card::before {
            content: '';
            position: absolute;
            top: 0; left: 0; width: 100%; height: 4px;
            background: #E2E8F0;
            transition: all 0.3s ease;
        }

        .kpi-card:hover {
            transform: translateY(-6px) scale(1.02);
            box-shadow: 0 20px 35px rgba(0, 30, 87, 0.12);
        }

        .kpi-card.total:hover::before { background: #001E57; }
        .kpi-card.sucesso:hover::before { background: #10B981; }
        .kpi-card.parcial:hover::before { background: #F59E0B; }
        .kpi-card.erro:hover::before { background: #EF4444; }
        .kpi-card.taxa:hover::before { background: #FF9200; }

        .kpi-card h4 {
            color: #64748B;
            font-size: 0.78rem;
            margin: 0;
            text-transform: uppercase;
            font-weight: 800;
            letter-spacing: 0.6px;
        }

        .kpi-card h2 {
            font-size: 2.2rem;
            margin: 8px 0 0 0;
            font-weight: 900;
            letter-spacing: -0.8px;
            line-height: 1;
        }

        /* ---------------- SEÇÕES E CONTAINERS ---------------- */
        .chart-box {
            background: #FFFFFF;
            border-radius: 20px;
            padding: 24px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.03);
            animation: fadeIn 1.2s ease-out;
            margin-bottom: 20px;
        }

        .section-title {
            color: #001E57;
            font-weight: 800;
            font-size: 1.15rem;
            margin-bottom: 16px;
            display: flex;
            align-items: center;
            gap: 8px;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_dashboard():
    inject_custom_css()

    # 1. HEADER EXECUTIVO COM ANIMAÇÕES METÁLICAS
    st.markdown(
        """
    <div class="dash-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h2 style="margin:0; font-weight: 900; font-size: 2rem; color: #FFF; letter-spacing: -0.5px;">
                    📊 Painel de Performance Operacional
                </h2>
                <p style="margin: 6px 0 0 0; color: #CBD5E1; font-size: 0.95rem; font-weight: 400;">
                    Monitoramento estratégico em tempo real de throughput, SLAs e pendências operacionais.
                </p>
            </div>
            <span class="badge-live">
                <span class="badge-live-dot"></span> REAL-TIME CLUSTER
            </span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 2. BUSCA OS DADOS DO BACKEND
    with st.spinner("⚡ Atualizando indicadores estratégicos..."):
        dados = fetch_dashboard_data()

    if dados is None:
        st.warning(
            "⚠️ Não foi possível conectar ao servidor backend ou atualizar as"
            " métricas no momento. Verifique sua conexão."
        )
        return

    if not dados or len(dados) == 0:
        st.info(
            "ℹ️ **Nenhum registro encontrado no sistema.**\n\nUtilize o menu"
            " **'Lançar Execução Diária'** para começar a cadastrar as"
            " entregas do dia!"
        )
        return

    # Converte os dados recebidos para DataFrame
    df = pd.DataFrame(dados)

    # 3. FILTROS DINÂMICOS COM DESIGN ELEVO
    col_f1, col_f2 = st.columns(2, gap="medium")

    with col_f1:
        clientes_lista = ["Todos"]
        if "cliente" in df.columns:
            clientes_lista += sorted(
                list(df["cliente"].dropna().unique())
            )
        cliente_sel = st.selectbox(
            "🏢 Filtrar por Cliente / Provedor:", clientes_lista
        )

    with col_f2:
        status_lista = [
            "Todos",
            "Realizado Total",
            "Realizado Parcial",
            "Não Realizado",
        ]
        status_sel = st.selectbox("📌 Filtrar por Status:", status_lista)

    # Aplicação dos Filtros no DataFrame
    df_filtered = df.copy()
    if cliente_sel != "Todos" and "cliente" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["cliente"] == cliente_sel]
    if status_sel != "Todos" and "status" in df_filtered.columns:
        df_filtered = df_filtered[df_filtered["status"] == status_sel]

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. CARDS DE MÉTRICAS PERSONALIZADOS (GLASSMORPHISM KPIs)
    total_registros = len(df_filtered)
    total_sucesso = (
        len(df_filtered[df_filtered["status"] == "Realizado Total"])
        if "status" in df_filtered.columns
        else 0
    )
    total_parcial = (
        len(df_filtered[df_filtered["status"] == "Realizado Parcial"])
        if "status" in df_filtered.columns
        else 0
    )
    total_nao_realizado = (
        len(df_filtered[df_filtered["status"] == "Não Realizado"])
        if "status" in df_filtered.columns
        else 0
    )

    taxa_sucesso = (
        (total_sucesso / total_registros * 100) if total_registros > 0 else 0.0
    )

    st.markdown(
        f"""
    <div class="kpi-container">
        <div class="kpi-card total">
            <h4>📋 Registros Totais</h4>
            <h2 style="color: #001E57;">{total_registros}</h2>
        </div>
        <div class="kpi-card sucesso">
            <h4>✅ Realizado Total</h4>
            <h2 style="color: #10B981;">{total_sucesso}</h2>
        </div>
        <div class="kpi-card parcial">
            <h4>⚠️ Realizado Parcial</h4>
            <h2 style="color: #F59E0B;">{total_parcial}</h2>
        </div>
        <div class="kpi-card erro">
            <h4>❌ Não Realizado</h4>
            <h2 style="color: #EF4444;">{total_nao_realizado}</h2>
        </div>
        <div class="kpi-card taxa">
            <h4>🎯 Índice Sucesso</h4>
            <h2 style="color: #FF9200;">{taxa_sucesso:.1f}%</h2>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 5. GRÁFICOS INTERATIVOS
    if not df_filtered.empty and "status" in df_filtered.columns:
        col_g1, col_g2 = st.columns(2, gap="large")

        with col_g1:
            st.markdown('<div class="section-title">🍩 Distribuição de Status de Execução</div>', unsafe_allow_html=True)
            status_counts = df_filtered["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Quantidade"]

            color_map = {
                "Realizado Total": "#10B981",
                "Realizado Parcial": "#F59E0B",
                "Não Realizado": "#EF4444",
                "Não Se Aplica": "#94A3B8",
            }

            fig_pie = px.pie(
                status_counts,
                values="Quantidade",
                names="Status",
                hole=0.6,
                color="Status",
                color_discrete_map=color_map,
            )
            
            fig_pie.update_traces(
                textposition="inside", 
                textinfo="percent+label",
                marker=dict(line=dict(color='#FFFFFF', width=3)),
                hoverinfo="label+value+percent"
            )
            
            fig_pie.update_layout(
                margin=dict(t=10, b=10, l=10, r=10),
                showlegend=True,
                legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(family="Inter, sans-serif", size=13, color="#001E57")
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_g2:
            st.markdown('<div class="section-title">📊 Top Clientes com Maior Volume</div>', unsafe_allow_html=True)
            if "cliente" in df_filtered.columns:
                cliente_counts = (
                    df_filtered["cliente"]
                    .value_counts()
                    .head(5)
                    .reset_index()
                )
                cliente_counts.columns = ["Cliente", "Lançamentos"]

                fig_bar = px.bar(
                    cliente_counts,
                    x="Lançamentos",
                    y="Cliente",
                    orientation="h",
                    text="Lançamentos",
                    color="Lançamentos",
                    color_continuous_scale=["#001E57", "#003399", "#FF9200"],
                )
                
                fig_bar.update_traces(
                    textposition="outside",
                    marker=dict(cornerRadius=6)
                )
                
                fig_bar.update_layout(
                    yaxis={"categoryorder": "total ascending", "title": None},
                    xaxis={"title": None, "showgrid": False},
                    margin=dict(t=10, b=10, l=10, r=20),
                    coloraxis_showscale=False,
                    paper_bgcolor="rgba(0,0,0,0)",
                    plot_bgcolor="rgba(0,0,0,0)",
                    font=dict(family="Inter, sans-serif", size=12, color="#001E57")
                )
                st.plotly_chart(fig_bar, use_container_width=True)

    # 6. CENTRAL DE PENDÊNCIAS E AUDITORIA DETALHADA
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown('<div class="section-title">⚠️ Central Executiva de Pendências & Observações</div>', unsafe_allow_html=True)

    if "status" in df_filtered.columns:
        pendencias = df_filtered[
            df_filtered["status"].isin(
                ["Realizado Parcial", "Não Realizado", "Não Se Aplica"]
            )
        ]

        if not pendencias.empty:
            cols_exibicao = [
                c
                for c in ["cliente", "status", "observacoes", "created_at"]
                if c in pendencias.columns
            ]
            
            df_exibir = pendencias[cols_exibicao].copy()
            df_exibir.columns = [
                col.capitalize().replace("_", " ") for col in df_exibir.columns
            ]

            st.dataframe(
                df_exibir,
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.success(
                "🎉 Nenhuma pendência ou justificativa registrada para os"
                " filtros selecionados!"
            )


# Execução automática da página
if __name__ == "__main__":
    render_dashboard()