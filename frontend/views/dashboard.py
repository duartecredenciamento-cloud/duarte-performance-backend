import os
import pandas as pd
import plotly.express as px
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


def render_dashboard():
    st.title("📊 Dashboard de Performance")
    st.caption(
        "Acompanhamento em tempo real dos resultados operacionais, entregas e"
        " pendências."
    )

    st.markdown("---")

    # 1. Busca os dados do backend
    dados = fetch_dashboard_data()

    # 2. TRATAMENTO DE ERROS E ESTADOS VAZIOS
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

    # 3. FILTROS DINÂMICOS
    col_f1, col_f2 = st.columns(2)

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

    st.markdown("---")

    # 4. CARDS DE MÉTRICAS (KPIs)
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

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("📋 Total", total_registros)
    col2.metric("✅ Total 100%", total_sucesso)
    col3.metric("⚠️ Parcial", total_parcial)
    col4.metric("❌ Não Realizado", total_nao_realizado)
    col5.metric("🎯 Taxa Sucesso", f"{taxa_sucesso:.1f}%")

    st.markdown("---")

    # 5. GRÁFICOS DE ACOMPANHAMENTO
    if not df_filtered.empty and "status" in df_filtered.columns:
        col_g1, col_g2 = st.columns(2, gap="large")

        with col_g1:
            st.subheader("📌 Distribuição por Status")
            status_counts = df_filtered["status"].value_counts().reset_index()
            status_counts.columns = ["Status", "Quantidade"]

            # Mapeamento de cores da marca
            color_map = {
                "Realizado Total": "#2ecc71",
                "Realizado Parcial": "#f39c12",
                "Não Realizado": "#e74c3c",
            }

            fig_pie = px.pie(
                status_counts,
                values="Quantidade",
                names="Status",
                hole=0.45,
                color="Status",
                color_discrete_map=color_map,
            )
            fig_pie.update_traces(
                textposition="inside", textinfo="percent+label"
            )
            fig_pie.update_layout(
                margin=dict(t=20, b=20, l=20, r=20), showlegend=False
            )
            st.plotly_chart(fig_pie, use_container_width=True)

        with col_g2:
            st.subheader("🏢 Top Clientes / Provedores")
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
                    color="Lançamentos",
                    color_continuous_scale="Blues",
                )
                fig_bar.update_layout(
                    yaxis={"categoryorder": "total ascending"},
                    margin=dict(t=20, b=20, l=20, r=20),
                    coloraxis_showscale=False,
                )
                st.plotly_chart(fig_bar, use_container_width=True)

    # 6. DETALHAMENTO DE PENDÊNCIAS E JUSTIFICATIVAS
    st.markdown("---")
    st.subheader("⚠️ Central de Pendências & Observações")

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
            
            # Renomeia para exibição bonita na tabela
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
render_dashboard()