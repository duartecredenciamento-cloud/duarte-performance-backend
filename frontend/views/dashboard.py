import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta

from tabela_pro import inject_tabela_css, mostrar_lancamentos

# ===================== PALETA DUARTE =====================
COR_AZUL = "#001E57"
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


def _layout_padrao(fig, altura=340, show_legend=True):
    fig.update_layout(
        height=altura,
        margin=dict(l=12, r=12, t=48, b=12),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color="#334155", size=12),
        title=dict(
            font=dict(color=COR_AZUL, size=15, family="Inter, sans-serif"),
            x=0.02,
            xanchor="left",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.28,
            xanchor="center",
            x=0.5,
            bgcolor="rgba(0,0,0,0)",
        )
        if show_legend
        else dict(visible=False),
        hoverlabel=dict(
            bgcolor="white",
            font_size=12,
            font_family="Inter, sans-serif",
            bordercolor="#E2E8F0",
        ),
    )
    return fig


def render_dashboard(api_get):
    st.markdown(
        """
    <style>
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(18px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes floatGradient {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes pulseGlow {
            0%   { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.45); }
            70%  { box-shadow: 0 0 0 12px rgba(255, 146, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
        }

        .dash-header {
            background: linear-gradient(-45deg, #001E57, #030A1A, #0B296B, #001233);
            background-size: 300% 300%;
            animation: floatGradient 12s ease infinite, fadeInUp 0.55s ease-out;
            padding: 32px 34px;
            border-radius: 22px;
            color: white;
            margin-bottom: 26px;
            border-left: 6px solid #FF9200;
            box-shadow: 0 18px 45px rgba(0, 30, 87, 0.25);
            position: relative;
            overflow: hidden;
        }
        .dash-header::before {
            content: '';
            position: absolute;
            top: -40%;
            right: -8%;
            width: 260px;
            height: 260px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,146,0,0.22) 0%, transparent 70%);
            pointer-events: none;
        }
        .dash-header h1 {
            margin: 0;
            font-size: 2.15rem;
            font-weight: 900;
            letter-spacing: -0.6px;
            position: relative;
            z-index: 1;
        }
        .dash-header p {
            margin: 10px 0 0 0;
            color: #94A3B8;
            font-size: 0.98rem;
            position: relative;
            z-index: 1;
        }
        .dash-badge {
            display: inline-block;
            margin-top: 14px;
            background: linear-gradient(135deg, #FF9200, #FFB84D);
            color: #fff;
            padding: 6px 14px;
            border-radius: 99px;
            font-weight: 800;
            font-size: 0.72rem;
            letter-spacing: 0.4px;
            animation: pulseGlow 2.2s infinite;
            position: relative;
            z-index: 1;
        }

        .metric-card {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            padding: 22px 16px;
            border-radius: 18px;
            box-shadow: 0 8px 24px rgba(0, 30, 87, 0.06);
            text-align: center;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            border: 1px solid #E2E8F0;
            animation: fadeInUp 0.6s ease-out;
        }
        .metric-card:hover {
            transform: translateY(-6px) scale(1.02);
            box-shadow: 0 16px 36px rgba(255, 146, 0, 0.14);
            border-color: rgba(255, 146, 0, 0.45);
        }
        .metric-value {
            font-size: 2.35rem;
            font-weight: 900;
            color: #001E57;
            margin: 0;
            letter-spacing: -0.5px;
            line-height: 1.1;
        }
        .metric-label {
            color: #64748B;
            font-weight: 800;
            text-transform: uppercase;
            font-size: 0.72rem;
            letter-spacing: 0.55px;
            margin-top: 6px;
        }

        .chart-card {
            background: #FFFFFF;
            padding: 20px 18px 8px 18px;
            border-radius: 18px;
            box-shadow: 0 10px 28px rgba(0, 30, 87, 0.06);
            border: 1px solid #E2E8F0;
            animation: fadeInUp 0.7s ease-out;
            margin-bottom: 8px;
        }
        .chart-title {
            color: #001E57;
            font-weight: 800;
            font-size: 1rem;
            margin: 0 0 4px 4px;
        }

        .filter-bar {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 12px 14px;
            margin-bottom: 18px;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    inject_tabela_css()

    nome = st.session_state.get("nome", "Usuário")
    role = st.session_state.get("role", "Operador")

    st.markdown(
        f"""
    <div class="dash-header">
        <h1>📊 Dashboard Gerencial</h1>
        <p>Bem-vindo, <strong>{nome}</strong> · {role}</p>
        <span class="dash-badge">⚡ PERFORMANCE · TEMPO REAL</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.spinner("Carregando indicadores..."):
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

    st.markdown('<div class="filter-bar">', unsafe_allow_html=True)
    f1, f2 = st.columns([1.2, 2])
    with f1:
        periodo = st.selectbox(
            "📅 Período",
            ["Hoje", "Últimos 7 dias", "Últimos 30 dias", "Todos"],
            index=1,
        )
    with f2:
        operadores = ["Todos"]
        if "operador_nome" in df.columns:
            operadores += sorted(
                [str(x) for x in df["operador_nome"].dropna().unique().tolist()]
            )
        filtro_op = st.selectbox("👤 Operador", operadores)
    st.markdown("</div>", unsafe_allow_html=True)

    hoje = datetime.now()
    if "data_registro" in df.columns:
        if periodo == "Hoje":
            df = df[df["data_registro"].dt.date == hoje.date()]
        elif periodo == "Últimos 7 dias":
            df = df[df["data_registro"] >= hoje - timedelta(days=7)]
        elif periodo == "Últimos 30 dias":
            df = df[df["data_registro"] >= hoje - timedelta(days=30)]

    if filtro_op != "Todos" and "operador_nome" in df.columns:
        df = df[df["operador_nome"].astype(str) == filtro_op]

    total = len(df)
    tem_status = "status" in df.columns
    realizados = len(df[df["status"] == "Realizado Total"]) if tem_status else 0
    parciais = len(df[df["status"] == "Realizado Parcial"]) if tem_status else 0
    nao_real = len(df[df["status"] == "Não Realizado"]) if tem_status else 0
    eficiencia = round((realizados / total * 100), 1) if total > 0 else 0

    c1, c2, c3, c4, c5 = st.columns(5)
    cards = [
        (c1, str(total), "Total", COR_AZUL),
        (c2, str(realizados), "Realizados", COR_VERDE),
        (c3, str(parciais), "Parciais", COR_AMARELO),
        (c4, str(nao_real), "Não Realizados", COR_VERMELHO),
        (c5, f"{eficiencia}%", "Eficiência", COR_LARANJA),
    ]
    for col, val, label, cor in cards:
        with col:
            st.markdown(
                f"""
            <div class="metric-card">
                <div class="metric-value" style="color:{cor}">{val}</div>
                <div class="metric-label">{label}</div>
            </div>
            """,
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(
            '<p class="chart-title">🍩 Distribuição por Status</p>',
            unsafe_allow_html=True,
        )
        if not df.empty and tem_status:
            contagem = df["status"].value_counts().reset_index()
            contagem.columns = ["status", "quantidade"]
            fig = go.Figure(
                data=[
                    go.Pie(
                        labels=contagem["status"],
                        values=contagem["quantidade"],
                        hole=0.62,
                        marker=dict(
                            colors=[
                                CORES_STATUS.get(s, COR_CINZA)
                                for s in contagem["status"]
                            ],
                            line=dict(color="#FFFFFF", width=2),
                        ),
                        textinfo="percent",
                        textfont=dict(size=12, color="#0F172A"),
                        hovertemplate="<b>%{label}</b><br>%{value} registros<br>%{percent}<extra></extra>",
                    )
                ]
            )
            fig.add_annotation(
                text=f"<b>{total}</b><br><span style='font-size:11px;color:#64748B'>total</span>",
                showarrow=False,
                font=dict(size=20, color=COR_AZUL),
                x=0.5,
                y=0.5,
            )
            fig = _layout_padrao(fig, 340)
            st.plotly_chart(
                fig, use_container_width=True, config={"displayModeBar": False}
            )
        else:
            st.info("Sem dados para o gráfico de status.")
        st.markdown("</div>", unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(
            '<p class="chart-title">👥 Execuções por Operador</p>',
            unsafe_allow_html=True,
        )
        if "operador_nome" in df.columns and not df.empty:
            contagem_op = (
                df["operador_nome"]
                .value_counts()
                .sort_values(ascending=True)
                .tail(12)
                .reset_index()
            )
            contagem_op.columns = ["operador_nome", "quantidade"]
            fig = go.Figure(
                data=[
                    go.Bar(
                        x=contagem_op["quantidade"],
                        y=contagem_op["operador_nome"],
                        orientation="h",
                        marker=dict(
                            color=contagem_op["quantidade"],
                            colorscale=[[0, "#FED7AA"], [1, COR_LARANJA]],
                            line=dict(width=0),
                        ),
                        text=contagem_op["quantidade"],
                        textposition="outside",
                        textfont=dict(color=COR_AZUL, size=11),
                        hovertemplate="<b>%{y}</b><br>%{x} execuções<extra></extra>",
                    )
                ]
            )
            fig.update_xaxes(showgrid=True, gridcolor="#F1F5F9", zeroline=False)
            fig.update_yaxes(showgrid=False)
            fig = _layout_padrao(fig, 340, show_legend=False)
            st.plotly_chart(
                fig, use_container_width=True, config={"displayModeBar": False}
            )
        else:
            st.info("Sem dados por operador.")
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    st.markdown('<div class="chart-card">', unsafe_allow_html=True)
    st.markdown(
        '<p class="chart-title">📈 Evolução das Execuções</p>',
        unsafe_allow_html=True,
    )
    if "data_registro" in df.columns and not df.empty:
        df_t = df.copy()
        df_t["dia"] = df_t["data_registro"].dt.date
        serie = df_t.groupby("dia").size().reset_index(name="quantidade")

        fig = go.Figure()
        fig.add_trace(
            go.Scatter(
                x=serie["dia"],
                y=serie["quantidade"],
                mode="lines+markers",
                line=dict(color=COR_AZUL, width=3, shape="spline"),
                marker=dict(
                    color=COR_LARANJA,
                    size=9,
                    line=dict(color="#fff", width=2),
                ),
                fill="tozeroy",
                fillcolor="rgba(255, 146, 0, 0.10)",
                hovertemplate="<b>%{x}</b><br>%{y} execuções<extra></extra>",
            )
        )
        fig.update_xaxes(showgrid=False, zeroline=False)
        fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9", zeroline=False)
        fig = _layout_padrao(fig, 300, show_legend=False)
        st.plotly_chart(
            fig, use_container_width=True, config={"displayModeBar": False}
        )
    else:
        st.info("Sem dados temporais.")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    if tem_status and "operador_nome" in df.columns and not df.empty:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(
            '<p class="chart-title">📊 Status por Operador (empilhado)</p>',
            unsafe_allow_html=True,
        )
        pivot = (
            df.groupby(["operador_nome", "status"])
            .size()
            .reset_index(name="qtd")
        )
        fig = go.Figure()
        for status, cor in CORES_STATUS.items():
            sub = pivot[pivot["status"] == status]
            if sub.empty:
                continue
            fig.add_trace(
                go.Bar(
                    name=status,
                    x=sub["operador_nome"],
                    y=sub["qtd"],
                    marker_color=cor,
                    hovertemplate="<b>%{x}</b><br>" + status + ": %{y}<extra></extra>",
                )
            )
        fig.update_layout(barmode="stack")
        fig.update_xaxes(showgrid=False)
        fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9")
        fig = _layout_padrao(fig, 360)
        st.plotly_chart(
            fig, use_container_width=True, config={"displayModeBar": False}
        )
        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ===== TABELA PREMIUM (tabela_pro) =====
    mostrar_lancamentos(df, max_linhas=20, titulo="📋 Últimos Lançamentos")