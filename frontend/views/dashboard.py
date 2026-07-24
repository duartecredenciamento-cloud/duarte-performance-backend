import streamlit as st
import pandas as pd
from datetime import datetime, timedelta


def render_dashboard(api_get):

    # =====================================================
    # CSS VISUAL DUARTE PERFORMANCE
    # =====================================================

    st.markdown(
        """
        <style>

        .dash-header {

            background:
            linear-gradient(
                135deg,
                #001E57,
                #0A2540
            );

            padding:30px;
            border-radius:18px;
            color:white;
            border-left:6px solid #FF9200;
            margin-bottom:25px;

        }


        .card {

            background:white;
            padding:20px;
            border-radius:15px;
            border:1px solid #E2E8F0;
            text-align:center;
            box-shadow:
            0 5px 15px rgba(0,0,0,.05);

        }


        .card h1 {

            color:#001E57;
            margin:0;
            font-weight:900;

        }


        .card p {

            color:#64748B;
            font-size:13px;
            font-weight:700;
            text-transform:uppercase;

        }


        </style>
        """,
        unsafe_allow_html=True
    )


    # =====================================================
    # HEADER
    # =====================================================

    nome = st.session_state.get(
        "nome",
        "Usuário"
    )

    role = st.session_state.get(
        "role",
        "Operador"
    )


    st.markdown(
        f"""
        <div class="dash-header">

        <h1 style="
        margin:0;
        color:white;
        font-weight:900;
        ">
        📊 Dashboard Gerencial
        </h1>


        <p style="
        color:#CBD5E1;
        margin-top:8px;
        ">
        Bem-vindo, {nome} • Perfil: {role}
        </p>


        </div>
        """,
        unsafe_allow_html=True
    )



    # =====================================================
    # BUSCA DOS REGISTROS
    # =====================================================


    resposta = api_get(
        "/registros/"
    )


    if resposta is None:

        st.error(
            "Falha ao comunicar com o backend."
        )

        return



    if resposta.status_code != 200:

        st.warning(
            "Não foi possível carregar os registros."
        )

        return



    registros = resposta.json()



    if not registros:

        st.info(
            "Nenhuma execução registrada ainda."
        )

        return



    df = pd.DataFrame(
        registros
    )



    # =====================================================
    # TRATAMENTO DE DADOS
    # =====================================================


    if "data_registro" in df.columns:

        df["data_registro"] = pd.to_datetime(
            df["data_registro"],
            errors="coerce"
        )


    else:

        df["data_registro"] = datetime.now()



    # =====================================================
    # FILTRO DE PERÍODO
    # =====================================================


    periodo = st.selectbox(

        "Período de análise",

        [
            "Hoje",
            "Últimos 7 dias",
            "Últimos 30 dias",
            "Todos"
        ]

    )



    hoje = datetime.now()



    if periodo == "Hoje":

        df = df[
            df["data_registro"].dt.date
            ==
            hoje.date()
        ]



    elif periodo == "Últimos 7 dias":

        df = df[
            df["data_registro"]
            >=
            hoje - timedelta(days=7)
        ]



    elif periodo == "Últimos 30 dias":

        df = df[
            df["data_registro"]
            >=
            hoje - timedelta(days=30)
        ]



    # =====================================================
    # INDICADORES
    # =====================================================


    total = len(df)


    realizados = len(
        df[
            df["status"]
            ==
            "Realizado Total"
        ]
    )


    parciais = len(
        df[
            df["status"]
            ==
            "Realizado Parcial"
        ]
    )


    pendentes = len(
        df[
            df["status"]
            ==
            "Não Realizado"
        ]
    )



    eficiencia = (

        realizados / total * 100

        if total > 0

        else 0

    )



    c1,c2,c3,c4 = st.columns(4)



    with c1:

        st.markdown(
            f"""
            <div class="card">

            <h1>
            {total}
            </h1>

            <p>
            Total Execuções
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )



    with c2:

        st.markdown(
            f"""
            <div class="card">

            <h1 style="color:#10B981">
            {realizados}
            </h1>

            <p>
            Realizados
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )



    with c3:

        st.markdown(
            f"""
            <div class="card">

            <h1 style="color:#F59E0B">
            {parciais}
            </h1>

            <p>
            Parciais
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )



    with c4:

        st.markdown(
            f"""
            <div class="card">

            <h1 style="color:#FF9200">
            {eficiencia:.1f}%
            </h1>

            <p>
            Eficiência
            </p>

            </div>
            """,
            unsafe_allow_html=True
        )



    st.markdown(
        "<br>",
        unsafe_allow_html=True
    )



    # =====================================================
    # GRÁFICOS
    # =====================================================


    col1,col2 = st.columns(2)



    with col1:

        st.subheader(
            "📌 Distribuição de Status"
        )


        grafico = (
            df["status"]
            .value_counts()
        )


        st.bar_chart(
            grafico
        )



    with col2:

        st.subheader(
            "👥 Produção por Operador"
        )


        if "operador_nome" in df.columns:

            operador = (
                df["operador_nome"]
                .value_counts()
            )


            st.bar_chart(
                operador
            )



    # =====================================================
    # ÚLTIMOS LANÇAMENTOS
    # =====================================================


    st.divider()


    st.subheader(
        "📝 Últimos Lançamentos"
    )


    colunas = [

        "data_registro",
        "operador_nome",
        "cliente_nome",
        "status",
        "justificativa"

    ]


    colunas_existentes = [

        c for c in colunas
        if c in df.columns

    ]


    st.dataframe(

        df[
            colunas_existentes
        ]
        .sort_values(
            "data_registro",
            ascending=False
        )
        .head(20),

        use_container_width=True,

        hide_index=True

    )