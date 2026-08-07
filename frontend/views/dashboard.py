import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
    "Não Informado": "#64748B",
}


def _layout_padrao(fig, altura=320):
    fig.update_layout(
        height=altura,
        margin=dict(l=12, r=12, t=48, b=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color="#334155", size=13),
        title_font=dict(color=COR_AZUL, size=16, family="Inter, sans-serif"),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.28,
            xanchor="center",
            x=0.5,
            font=dict(size=12),
        ),
    )
    return fig


def _chave_operador(nome: str) -> str:
    if nome is None or (isinstance(nome, float) and pd.isna(nome)):
        return ""
    s = str(nome).strip()
    if not s:
        return ""
    primeiro = s.split()[0]
    mapa = str.maketrans(
        "áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ",
        "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC",
    )
    return primeiro.translate(mapa).casefold()


def _rotulo_operador(series_nomes: pd.Series) -> str:
    nomes = [str(n).strip() for n in series_nomes if n and str(n).strip()]
    if not nomes:
        return "Sem nome"
    return max(nomes, key=len)


def _normalizar_operadores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "operador_nome" not in df.columns:
        df["op_key"] = ""
        df["operador_exibicao"] = "Sem nome"
        return df
    df["op_key"] = df["operador_nome"].apply(_chave_operador)
    mapa = (
        df.groupby("op_key")["operador_nome"].apply(_rotulo_operador).to_dict()
    )
    df["operador_exibicao"] = (
        df["op_key"].map(mapa).fillna(df["operador_nome"].astype(str))
    )
    return df


def render_dashboard(api_get):
        # ===================== CSS PREMIUM =====================
    st.markdown(
        """
    <style>
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes floatGradient {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes pulseGlow {
            0%   { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.45); }
            70%  { box-shadow: 0 0 0 14px rgba(255, 146, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
        }

        .dash-header {
            background: linear-gradient(-45deg, #001E57, #030A1A, #0A2540, #001233);
            background-size: 300% 300%;
            animation: floatGradient 12s ease infinite, fadeInUp 0.55s ease-out;
            padding: 32px 34px;
            border-radius: 22px;
            color: #fff;
            margin-bottom: 26px;
            border-left: 6px solid #FF9200;
            box-shadow:
                0 18px 42px rgba(0, 30, 87, 0.22),
                0 0 0 1px rgba(255, 146, 0, 0.08);
            position: relative;
            overflow: hidden;
        }
        .dash-header::before {
            content: '';
            position: absolute;
            top: -40%; right: -5%;
            width: 260px; height: 260px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,146,0,0.18) 0%, transparent 70%);
            pointer-events: none;
        }
        .dash-header h2 {
            margin: 0;
            font-weight: 900;
            font-size: 1.9rem;
            letter-spacing: -0.4px;
            position: relative; z-index: 1;
        }
        .dash-header p {
            margin: 8px 0 0 0;
            color: #94A3B8;
            font-size: 0.95rem;
            position: relative; z-index: 1;
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
            letter-spacing: 0.3px;
            animation: pulseGlow 2.4s infinite;
            position: relative; z-index: 1;
        }

        .metric-card {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 18px 14px;
            text-align: center;
            box-shadow: 0 8px 22px rgba(0, 30, 87, 0.06);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            animation: fadeInUp 0.6s ease-out;
            height: 100%;
        }
        .metric-card:hover {
            transform: translateY(-4px);
            border-color: rgba(255, 146, 0, 0.4);
            box-shadow: 0 14px 32px rgba(255, 146, 0, 0.12);
        }
        .metric-card h3 {
            margin: 0;
            color: #001E57;
            font-size: 1.75rem;
            font-weight: 900;
        }
        .metric-card h3.accent { color: #FF9200; }
        .metric-card h3.green  { color: #10B981; }
        .metric-card h3.red    { color: #EF4444; }
        .metric-card h3.yellow { color: #F59E0B; }
        .metric-card p {
            margin: 6px 0 0 0;
            color: #64748B;
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.45px;
        }

        .chart-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 18px;
            padding: 18px 16px 8px 16px;
            box-shadow: 0 10px 28px rgba(0, 30, 87, 0.06);
            animation: fadeInUp 0.7s ease-out;
            margin-bottom: 8px;
        }
        .chart-card h4 {
            margin: 0 0 6px 8px;
            color: #001E57;
            font-weight: 800;
            font-size: 1rem;
        }

        /* ===== TABELA PREMIUM ===== */
        div[data-testid="stDataFrame"] {
            background: #FFFFFF !important;
            border: 1px solid #E2E8F0 !important;
            border-radius: 16px !important;
            box-shadow: 0 10px 28px rgba(0, 30, 87, 0.07) !important;
            overflow: hidden !important;
            animation: fadeInUp 0.75s ease-out;
        }
        div[data-testid="stDataFrame"] table {
            border-collapse: separate !important;
            border-spacing: 0 !important;
            width: 100% !important;
        }
        div[data-testid="stDataFrame"] thead tr th {
            background: linear-gradient(135deg, #001E57 0%, #0B296B 100%) !important;
            color: #FFFFFF !important;
            font-weight: 800 !important;
            font-size: 0.78rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.4px !important;
            padding: 12px 14px !important;
            border: none !important;
        }
        div[data-testid="stDataFrame"] tbody tr td {
            padding: 11px 14px !important;
            font-size: 0.88rem !important;
            color: #1E293B !important;
            border-bottom: 1px solid #F1F5F9 !important;
        }
        div[data-testid="stDataFrame"] tbody tr:nth-child(even) td {
            background: #F8FAFC !important;
        }
        div[data-testid="stDataFrame"] tbody tr:hover td {
            background: rgba(255, 146, 0, 0.08) !important;
        }
        .table-section-title {
            color: #001E57;
            font-weight: 900;
            font-size: 1.15rem;
            margin: 18px 0 12px 0;
            padding-left: 10px;
            border-left: 4px solid #FF9200;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="dash-header">
        <h2>📊 Dashboard Gerencial</h2>
        <p>Visão consolidada das execuções operacionais · tempo real</p>
        <span class="dash-badge">⚡ PERFORMANCE · DUARTE</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.spinner("Carregando indicadores..."):
        resp = api_get("/registros/")

    if resp is None or resp.status_code != 200:
        st.error("Erro ao carregar registros.")
        return

    df = pd.DataFrame(resp.json())
    if df.empty:
        st.info("Nenhum registro encontrado.")
        return

    if "data_registro" in df.columns:
        df["data_registro"] = pd.to_datetime(df["data_registro"], errors="coerce")

    periodo = st.selectbox(
        "📅 Período",
        ["Hoje", "Últimos 7 dias", "Últimos 30 dias", "Todos"],
        index=3,
        key="dash_periodo",
    )

    agora = datetime.utcnow()
    df_f = df.copy()
    if "data_registro" in df_f.columns:
        if periodo == "Hoje":
            df_f = df_f[df_f["data_registro"].dt.date == agora.date()]
        elif periodo == "Últimos 7 dias":
            df_f = df_f[df_f["data_registro"] >= agora - timedelta(days=7)]
        elif periodo == "Últimos 30 dias":
            df_f = df_f[df_f["data_registro"] >= agora - timedelta(days=30)]

    if df_f.empty:
        st.warning("Nenhum registro neste período.")
        return

    df_f = _normalizar_operadores(df_f)

    total = len(df_f)
    realizados = (
        len(df_f[df_f["status"] == "Realizado Total"])
        if "status" in df_f.columns
        else 0
    )
    parciais = (
        len(df_f[df_f["status"] == "Realizado Parcial"])
        if "status" in df_f.columns
        else 0
    )
    nao = (
        len(df_f[df_f["status"] == "Não Realizado"])
        if "status" in df_f.columns
        else 0
    )
    eficiencia = round((realizados / total * 100), 1) if total else 0.0

       # ----- KPIs -----
    k1, k2, k3, k4, k5 = st.columns(5)
    with k1:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3>{total}</h3>
            <p>Total</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with k2:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3 class="green">{realizados}</h3>
            <p>Realizados</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with k3:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3 class="yellow">{parciais}</h3>
            <p>Parciais</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with k4:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3 class="red">{nao}</h3>
            <p>Não realizados</p>
        </div>
        """,
            unsafe_allow_html=True,
        )
    with k5:
        st.markdown(
            f"""
        <div class="metric-card">
            <h3 class="accent">{eficiencia}%</h3>
            <p>Eficiência</p>
        </div>
        """,
            unsafe_allow_html=True,
        )

    st.markdown("<br>", unsafe_allow_html=True)

    # ----- Gráficos -----
    c1, c2 = st.columns(2)

    with c1:
        st.markdown(
            '<div class="chart-card"><h4>🎯 Distribuição por Status</h4>',
            unsafe_allow_html=True,
        )
        if "status" in df_f.columns and not df_f["status"].isna().all():
            vc = df_f["status"].value_counts().reset_index()
            vc.columns = ["status", "qtd"]
            fig = px.pie(
                vc,
                names="status",
                values="qtd",
                color="status",
                color_discrete_map=CORES_STATUS,
                hole=0.52,
            )
            fig.update_traces(
                textposition="inside",
                textinfo="percent+label",
                marker=dict(line=dict(color="#FFFFFF", width=2)),
            )
            fig = _layout_padrao(fig, 360)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de status.")
        st.markdown("</div>", unsafe_allow_html=True)

    with c2:
        st.markdown(
            '<div class="chart-card"><h4>👥 Execuções por Operador</h4>',
            unsafe_allow_html=True,
        )
        por_op = (
            df_f.groupby("operador_exibicao", dropna=False)
            .size()
            .reset_index(name="qtd")
            .sort_values("qtd", ascending=True)
        )
        if not por_op.empty:
            fig2 = px.bar(
                por_op,
                x="qtd",
                y="operador_exibicao",
                orientation="h",
                color="qtd",
                color_continuous_scale=[
                    "#FFD59A",
                    "#FF9200",
                    "#E07A00",
                    "#001E57",
                ],
            )
            fig2.update_traces(
                marker_line_width=0,
                hovertemplate="<b>%{y}</b><br>%{x} lançamentos<extra></extra>",
            )
            fig2.update_layout(coloraxis_showscale=False)
            fig2 = _layout_padrao(fig2, max(360, 30 * len(por_op) + 90))
            fig2.update_yaxes(title="")
            fig2.update_xaxes(title="Lançamentos", gridcolor="#F1F5F9")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sem dados de operador.")
        st.markdown("</div>", unsafe_allow_html=True)

    # ----- Comparativo status x operador -----
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="chart-card"><h4>📊 Comparativo: Status por Operador</h4>',
        unsafe_allow_html=True,
    )
    if (
        "status" in df_f.columns
        and "operador_exibicao" in df_f.columns
        and not df_f.empty
    ):
        comp = (
            df_f.groupby(["operador_exibicao", "status"])
            .size()
            .reset_index(name="qtd")
        )
        fig_comp = px.bar(
            comp,
            x="operador_exibicao",
            y="qtd",
            color="status",
            barmode="stack",
            color_discrete_map=CORES_STATUS,
        )
        fig_comp.update_layout(
            xaxis_title="",
            yaxis_title="Lançamentos",
            legend_title="Status",
        )
        fig_comp.update_xaxes(tickangle=-25)
        fig_comp.update_yaxes(gridcolor="#F1F5F9")
        fig_comp = _layout_padrao(fig_comp, 380)
        st.plotly_chart(fig_comp, use_container_width=True)
    else:
        st.info("Sem dados para comparativo.")
    st.markdown("</div>", unsafe_allow_html=True)

    # ----- Evolução temporal -----
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<div class="chart-card"><h4>📈 Evolução das Execuções</h4>',
        unsafe_allow_html=True,
    )
    if "data_registro" in df_f.columns:
        tmp = df_f.dropna(subset=["data_registro"]).copy()
        if not tmp.empty:
            tmp["dia"] = tmp["data_registro"].dt.date
            serie = (
                tmp.groupby("dia")
                .size()
                .reset_index(name="quantidade")
                .sort_values("dia")
            )
            fig3 = go.Figure(
                data=[
                    go.Scatter(
                        x=serie["dia"],
                        y=serie["quantidade"],
                        mode="lines+markers",
                        line=dict(color=COR_AZUL, width=3, shape="spline"),
                        marker=dict(
                            color=COR_LARANJA,
                            size=9,
                            line=dict(color="#FFF", width=2),
                        ),
                        fill="tozeroy",
                        fillcolor="rgba(255, 146, 0, 0.12)",
                        hovertemplate="%{x}<br><b>%{y}</b> lançamentos<extra></extra>",
                    )
                ]
            )
            fig3.update_xaxes(showgrid=False)
            fig3.update_yaxes(showgrid=True, gridcolor="#F1F5F9")
            fig3 = _layout_padrao(fig3, 300)
            st.plotly_chart(fig3, use_container_width=True)
        else:
            st.info("Sem dados suficientes para a evolução.")
    st.markdown("</div>", unsafe_allow_html=True)

    # ----- Tabela premium -----
    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown(
        '<p class="table-section-title">📋 Últimos lançamentos</p>',
        unsafe_allow_html=True,
    )

    cols = [
        c
        for c in [
            "data_registro",
            "operador_nome",
            "cliente_nome",
            "status",
            "justificativa",
        ]
        if c in df_f.columns
    ]

    if cols and "data_registro" in df_f.columns:
        tabela = (
            df_f[cols]
            .sort_values("data_registro", ascending=False)
            .head(20)
            .copy()
        )
        tabela["data_registro"] = pd.to_datetime(
            tabela["data_registro"], errors="coerce"
        ).dt.strftime("%d/%m/%Y %H:%M")

        # renomeia colunas pra exibição
        rename_map = {
            "data_registro": "Data",
            "operador_nome": "Operador",
            "cliente_nome": "Cliente",
            "status": "Status",
            "justificativa": "Justificativa",
        }
        tabela = tabela.rename(
            columns={k: v for k, v in rename_map.items() if k in tabela.columns}
        )

        st.dataframe(
            tabela,
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Sem lançamentos para listar.")