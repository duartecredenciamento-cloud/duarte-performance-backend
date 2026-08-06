import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta

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
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#334155", size=13),
        title_font=dict(color=COR_AZUL, size=16),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5
        ),
    )
    return fig


def _chave_operador(nome: str) -> str:
    """Chave estável: primeiro nome em minúsculo, sem acento simples."""
    if nome is None or (isinstance(nome, float) and pd.isna(nome)):
        return ""
    s = str(nome).strip()
    if not s:
        return ""
    primeiro = s.split()[0]
    # normaliza basico
    mapa = str.maketrans(
        "áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ",
        "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC",
    )
    return primeiro.translate(mapa).casefold()


def _rotulo_operador(series_nomes: pd.Series) -> str:
    """Escolhe o nome mais completo do grupo para exibir no gráfico."""
    nomes = [str(n).strip() for n in series_nomes if n and str(n).strip()]
    if not nomes:
        return "Sem nome"
    # prioriza o mais longo (nome completo do cadastro)
    return max(nomes, key=len)


def _normalizar_operadores(df: pd.DataFrame) -> pd.DataFrame:
    """Cria colunas op_key e operador_exibicao (sem duplicar a mesma pessoa)."""
    df = df.copy()
    if "operador_nome" not in df.columns:
        df["op_key"] = ""
        df["operador_exibicao"] = "Sem nome"
        return df

    df["op_key"] = df["operador_nome"].apply(_chave_operador)
    mapa_rotulo = (
        df.groupby("op_key")["operador_nome"]
        .apply(_rotulo_operador)
        .to_dict()
    )
    df["operador_exibicao"] = df["op_key"].map(mapa_rotulo).fillna(
        df["operador_nome"].astype(str)
    )
    return df


def render_dashboard(api_get):
    st.markdown(
        """
    <style>
        .dash-header {
            background: linear-gradient(135deg, #001E57 0%, #0A2540 100%);
            padding: 28px 30px;
            border-radius: 18px;
            color: white;
            margin-bottom: 22px;
            border-left: 6px solid #FF9200;
        }
        .dash-header h2 { margin: 0; font-weight: 900; }
        .dash-header p { margin: 6px 0 0 0; color: #94A3B8; font-size: 0.9rem; }
    </style>
    <div class="dash-header">
        <h2>📊 Dashboard Gerencial</h2>
        <p>Visão consolidada das execuções operacionais</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.spinner("Carregando..."):
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

    # ----- Filtro de período -----
    periodo = st.selectbox(
        "Período",
        ["Hoje", "Últimos 7 dias", "Últimos 30 dias", "Todos"],
        index=3,
        key="dash_periodo",
    )

    agora = datetime.utcnow()
    df_f = df.copy()
    if periodo == "Hoje" and "data_registro" in df_f.columns:
        hoje = agora.date()
        df_f = df_f[df_f["data_registro"].dt.date == hoje]
    elif periodo == "Últimos 7 dias" and "data_registro" in df_f.columns:
        ini = agora - timedelta(days=7)
        df_f = df_f[df_f["data_registro"] >= ini]
    elif periodo == "Últimos 30 dias" and "data_registro" in df_f.columns:
        ini = agora - timedelta(days=30)
        df_f = df_f[df_f["data_registro"] >= ini]

    if df_f.empty:
        st.warning("Nenhum registro neste período.")
        return

    # Unifica nomes de operador
    df_f = _normalizar_operadores(df_f)

    total = len(df_f)
    realizados = len(df_f[df_f["status"] == "Realizado Total"]) if "status" in df_f.columns else 0
    parciais = len(df_f[df_f["status"] == "Realizado Parcial"]) if "status" in df_f.columns else 0
    nao = len(df_f[df_f["status"] == "Não Realizado"]) if "status" in df_f.columns else 0
    eficiencia = round((realizados / total * 100), 1) if total else 0

    m1, m2, m3, m4, m5 = st.columns(5)
    m1.metric("TOTAL", total)
    m2.metric("REALIZADOS", realizados)
    m3.metric("PARCIAIS", parciais)
    m4.metric("NÃO REALIZADOS", nao)
    m5.metric("EFICIÊNCIA", f"{eficiencia}%")

    st.divider()

    c1, c2 = st.columns(2)

    with c1:
        st.subheader("Distribuição por Status")
        if "status" in df_f.columns:
            vc = df_f["status"].value_counts().reset_index()
            vc.columns = ["status", "qtd"]
            fig = px.pie(
                vc,
                names="status",
                values="qtd",
                color="status",
                color_discrete_map=CORES_STATUS,
                hole=0.45,
            )
            fig.update_traces(textposition="inside", textinfo="percent")
            fig = _layout_padrao(fig, 340)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Sem dados de status.")

    with c2:
        st.subheader("Execuções por Operador")
        # AGRUPA pela chave unificada
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
                color_continuous_scale=["#FFB84D", "#FF9200", "#001E57"],
            )
            fig2.update_layout(coloraxis_showscale=False)
            fig2 = _layout_padrao(fig2, max(340, 28 * len(por_op) + 80))
            fig2.update_yaxes(title="")
            fig2.update_xaxes(title="Lançamentos")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.info("Sem dados de operador.")

    st.divider()
    st.subheader("📋 Últimos lançamentos")

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
        st.dataframe(
            df_f[cols]
            .sort_values("data_registro", ascending=False)
            .head(20),
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("Sem lançamentos para listar.")