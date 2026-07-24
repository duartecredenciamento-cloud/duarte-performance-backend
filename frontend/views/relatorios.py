import pandas as pd
import streamlit as st


def render_relatorios(api_get):
    st.title("📑 Relatórios Operacionais")

    st.caption(
        "Consolidação dos registros operacionais da equipe."
    )

    resposta = api_get("/registros/")

    if resposta is None:
        st.error("Erro de comunicação com o backend.")
        return

    if resposta.status_code != 200:
        st.error("Não foi possível carregar os registros.")
        return

    registros = resposta.json()

    if not registros:
        st.info("Nenhum registro encontrado.")
        return

    df = pd.DataFrame(registros)

    df["data_registro"] = pd.to_datetime(
        df["data_registro"],
        errors="coerce"
    )

    # ===========================
    # FILTROS
    # ===========================

    col1, col2, col3 = st.columns(3)

    with col1:

        operador = st.selectbox(
            "Operador",
            ["Todos"] +
            sorted(df["operador_nome"].dropna().unique())
        )

    with col2:

        status = st.selectbox(
            "Status",
            ["Todos"] +
            sorted(df["status"].dropna().unique())
        )

    with col3:

        periodo = st.date_input(
            "A partir de",
            value=df["data_registro"].min().date()
        )

    if operador != "Todos":

        df = df[
            df["operador_nome"] == operador
        ]

    if status != "Todos":

        df = df[
            df["status"] == status
        ]

    df = df[
        df["data_registro"].dt.date >= periodo
    ]

    # ===========================
    # MÉTRICAS
    # ===========================

    total = len(df)

    realizados = len(
        df[
            df["status"] ==
            "Realizado Total"
        ]
    )

    parcial = len(
        df[
            df["status"] ==
            "Realizado Parcial"
        ]
    )

    nao = len(
        df[
            df["status"] ==
            "Não Realizado"
        ]
    )

    c1, c2, c3, c4 = st.columns(4)

    c1.metric(
        "Total",
        total
    )

    c2.metric(
        "Realizados",
        realizados
    )

    c3.metric(
        "Parciais",
        parcial
    )

    c4.metric(
        "Não Realizados",
        nao
    )

    st.divider()

    # ===========================
    # TABELA
    # ===========================

    st.subheader(
        "Detalhamento"
    )

    st.dataframe(

        df.sort_values(
            "data_registro",
            ascending=False
        ),

        use_container_width=True,

        hide_index=True

    )

    st.divider()

    # ===========================
    # PRODUÇÃO POR OPERADOR
    # ===========================

    st.subheader(
        "Produção por Operador"
    )

    producao = (

        df.groupby(
            "operador_nome"
        )

        .size()

        .sort_values(
            ascending=False
        )

    )

    st.bar_chart(
        producao
    )

    st.divider()

    # ===========================
    # STATUS
    # ===========================

    st.subheader(
        "Distribuição por Status"
    )

    status_chart = (

        df["status"]

        .value_counts()

    )

    st.bar_chart(
        status_chart
    )

    st.divider()

    # ===========================
    # EXPORTAÇÃO
    # ===========================

    csv = df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(

        "📥 Exportar CSV",

        csv,

        "relatorio_operacional.csv",

        "text/csv",

        use_container_width=True

    )