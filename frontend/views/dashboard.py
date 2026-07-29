import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

# ===================== PALETA DE CORES DUARTE PERFORMANCE =====================
COR_AZUL_MARINHO = "#001E57"
COR_LARANJA = "#FF9200"
COR_VERDE = "#10B981"
COR_AMARELO = "#F59E0B"
COR_VERMELHO = "#EF4444"
COR_CINZA = "#94A3B8"

CORES_STATUS = {
    "Realizado Total": COR_VERDE,
    "Realizado Parcial": COR_AMARELO,
    "Não Realizado": COR_VERMELHO,
    "Não Se Aplica": COR_CINZA,
}


def _layout_padrao(fig, altura=320):
    """Aplica um layout consistente com a identidade visual em qualquer
    figura Plotly, pra não repetir isso em cada gráfico."""
    fig.update_layout(
        height=altura,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#334155", size=13),
        title_font=dict(color=COR_AZUL_MARINHO, size=16, family="Inter, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    return fig


def render_dashboard(api_get):
    # ===================== CSS PREMIUM =====================
    st.markdown("""
    <style>
        .dash-header {
            background: linear-gradient(135deg, #001E57 0%, #0A2540 100%);
            padding: 35px 30px;
            border-radius: 20px;
            color: white;
            margin-bottom: 30px;
            box-shadow: 0 15px 35px rgba(0, 30, 87, 0.15);
            animation: fadeIn 0.8s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .metric-card {
            background: white;
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.06);
            text-align: center;
            transition: all 0.3s ease;
            border: 1px solid #E2E8F0;
        }
        .metric-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 15px 30px rgba(255, 146, 0, 0.15);
            border-color: #FF9200;
        }
        .metric-value {
            font-size: 2.4rem;
            font-weight: 900;
            color: #001E57;
            margin: 0;
        }
        .metric-label {
            color: #64748B;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.5px;
        }
        .chart-card {
            background: white;
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.05);
            border: 1px solid #E2E8F0;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    nome = st.session_state.get("nome", "Usuário")
    role = st.session_state.get("role", "Operador")

    st.markdown(f"""
    <div class="dash-header">
        <h1 style="margin:0; font-size:2.4rem;">📊 Dashboard Gerencial</h1>
        <p style="margin:10px 0 0 0; opacity:0.9;">Bem-vindo, <strong>{nome}</strong> • {role}</p>
    </div>
    """, unsafe_allow_html=True)

    # Carregar dados
    resposta = api_get("/registros/")

    if resposta is None or resposta.status_code != 200:
        st.error("Não foi possível carregar os dados.")
        return

    registros = resposta.json()
    if not registros:
        st.info("Nenhum registro encontrado ainda.")
        return

    df = pd.DataFrame(registros)

    if "data_registro" in df.columns:
        df["data_registro"] = pd.to_datetime(df["data_registro"], errors="coerce")

    # Filtro
    periodo = st.selectbox("Período", ["Hoje", "Últimos 7 dias", "Últimos 30 dias", "Todos"], index=1)

    hoje = datetime.now()
    if "data_registro" in df.columns:
        if periodo == "Hoje":
            df = df[df["data_registro"].dt.date == hoje.date()]
        elif periodo == "Últimos 7 dias":
            df = df[df["data_registro"] >= hoje - timedelta(days=7)]
        elif periodo == "Últimos 30 dias":
            df = df[df["data_registro"] >= hoje - timedelta(days=30)]

    # Métricas (com verificação segura da coluna 'status')
    total = len(df)
    tem_status = "status" in df.columns
    realizados = len(df[df["status"] == "Realizado Total"]) if tem_status else 0
    parciais = len(df[df["status"] == "Realizado Parcial"]) if tem_status else 0
    pendentes = len(df[df["status"] == "Não Realizado"]) if tem_status else 0
    eficiencia = round((realizados / total * 100), 1) if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{total}</div><div class="metric-label">Total Execuções</div></div>', unsafe_allow_html=True)

    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#10B981">{realizados}</div><div class="metric-label">Realizados</div></div>', unsafe_allow_html=True)

    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#F59E0B">{parciais}</div><div class="metric-label">Parciais</div></div>', unsafe_allow_html=True)

    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#FF9200">{eficiencia}%</div><div class="metric-label">Eficiência</div></div>', unsafe_allow_html=True)

    st.divider()

    # ===================== GRÁFICOS (Plotly, identidade visual Duarte) =====================
    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.subheader("📊 Distribuição por Status")
        if not df.empty and tem_status:
            contagem_status = df["status"].value_counts().reset_index()
            contagem_status.columns = ["status", "quantidade"]

            fig_status = go.Figure(
                data=[
                    go.Pie(
                        labels=contagem_status["status"],
                        values=contagem_status["quantidade"],
                        hole=0.55,
                        marker=dict(
                            colors=[
                                CORES_STATUS.get(s, COR_CINZA)
                                for s in contagem_status["status"]
                            ]
                        ),
                        textinfo="percent+value",
                        textfont=dict(color="white", size=12),
                    )
                ]
            )
            fig_status = _layout_padrao(fig_status, altura=320)
            st.plotly_chart(fig_status, use_container_width=True)
        else:
            st.info("Sem dados suficientes para exibir o gráfico.")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.subheader("👥 Execuções por Operador")
        if "operador_nome" in df.columns and not df.empty:
            contagem_op = (
                df["operador_nome"]
                .value_counts()
                .sort_values(ascending=True)
                .reset_index()
            )
            contagem_op.columns = ["operador_nome", "quantidade"]

            fig_operador = go.Figure(
                data=[
                    go.Bar(
                        x=contagem_op["quantidade"],
                        y=contagem_op["operador_nome"],
                        orientation="h",
                        marker=dict(
                            color=COR_LARANJA,
                            line=dict(color=COR_AZUL_MARINHO, width=0.5),
                        ),
                        text=contagem_op["quantidade"],
                        textposition="outside",
                    )
                ]
            )
            fig_operador.update_xaxes(showgrid=True, gridcolor="#F1F5F9")
            fig_operador.update_yaxes(showgrid=False)
            fig_operador = _layout_padrao(fig_operador, altura=320)
            st.plotly_chart(fig_operador, use_container_width=True)
        else:
            st.info("Sem dados suficientes para exibir o gráfico.")
        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Linha temporal: execuções ao longo do período selecionado
    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.subheader("📈 Evolução das Execuções")
    if "data_registro" in df.columns and not df.empty:
        df_tempo = df.copy()
        df_tempo["dia"] = df_tempo["data_registro"].dt.date
        serie_diaria = df_tempo.groupby("dia").size().reset_index(name="quantidade")

        fig_linha = go.Figure(
            data=[
                go.Scatter(
                    x=serie_diaria["dia"],
                    y=serie_diaria["quantidade"],
                    mode="lines+markers",
                    line=dict(color=COR_AZUL_MARINHO, width=3),
                    marker=dict(color=COR_LARANJA, size=8),
                    fill="tozeroy",
                    fillcolor="rgba(255, 146, 0, 0.08)",
                )
            ]
        )
        fig_linha.update_xaxes(showgrid=False)
        fig_linha.update_yaxes(showgrid=True, gridcolor="#F1F5F9")
        fig_linha = _layout_padrao(fig_linha, altura=280)
        st.plotly_chart(fig_linha, use_container_width=True)
    else:
        st.info("Sem dados suficientes para exibir a evolução temporal.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.divider()

    st.subheader("📋 Últimos Lançamentos")
    colunas = ["data_registro", "operador_nome", "cliente_nome", "status", "justificativa"]
    colunas_exist = [c for c in colunas if c in df.columns]

    if colunas_exist and "data_registro" in df.columns and not df.empty:
        st.dataframe(
            df[colunas_exist].sort_values("data_registro", ascending=False).head(15),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhum lançamento para exibir no período selecionado.")