import pandas as pd
import streamlit as st
from datetime import datetime

def render_relatorios(api_get):
    # ===================== CSS PREMIUM =====================
    st.markdown("""
    <style>
        .report-header {
            background: linear-gradient(135deg, #001E57 0%, #0A2540 100%);
            padding: 30px;
            border-radius: 20px;
            color: white;
            margin-bottom: 25px;
        }
        .metric-card {
            background: white;
            padding: 22px;
            border-radius: 16px;
            box-shadow: 0 10px 25px rgba(0,0,0,0.07);
            text-align: center;
        }
        .stDownloadButton > button {
            background: #FF9200;
            color: white;
            font-weight: 700;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown("""
    <div class="report-header">
        <h2 style="margin:0;">📑 Relatórios Operacionais</h2>
        <p style="margin:8px 0 0 0; opacity:0.9;">Consolidação e análise completa dos apontamentos</p>
    </div>
    """, unsafe_allow_html=True)

    # Carregar dados
    with st.spinner("Carregando relatórios..."):
        resp = api_get("/registros/")

    if resp is None or resp.status_code != 200:
        st.error("Erro ao carregar dados.")
        return

    df = pd.DataFrame(resp.json())

    if df.empty:
        st.info("Nenhum registro encontrado.")
        return

    if "data_registro" in df.columns:
        df["data_registro"] = pd.to_datetime(df["data_registro"], errors="coerce")

    # Filtros
    col1, col2, col3 = st.columns(3)
    with col1:
        operador = st.selectbox("Operador", ["Todos"] + sorted(df["operador_nome"].dropna().unique().tolist()))
    with col2:
        status = st.selectbox("Status", ["Todos"] + sorted(df["status"].dropna().unique().tolist()))
    with col3:
        data_inicio = st.date_input("A partir de", value=df["data_registro"].min().date() if not df.empty else datetime.now().date())

    # Aplicar filtros
    df_filtered = df.copy()
    if operador != "Todos":
        df_filtered = df_filtered[df_filtered["operador_nome"] == operador]
    if status != "Todos":
        df_filtered = df_filtered[df_filtered["status"] == status]
    df_filtered = df_filtered[df_filtered["data_registro"].dt.date >= data_inicio]

    # Métricas
    total = len(df_filtered)
    concluidos = len(df_filtered[df_filtered["status"] == "Realizado Total"])
    taxa = round((concluidos / total * 100), 1) if total > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Registros", total)
    c2.metric("Concluídos", concluidos)
    c3.metric("Taxa de Conclusão", f"{taxa}%")

    st.divider()

    # Tabela
    st.subheader("📋 Detalhamento dos Registros")
    st.dataframe(
        df_filtered.sort_values("data_registro", ascending=False),
        use_container_width=True,
        hide_index=True
    )

    # Gráficos
    col_g1, col_g2 = st.columns(2)
    with col_g1:
        st.subheader("📊 Por Operador")
        if "operador_nome" in df_filtered.columns:
            st.bar_chart(df_filtered["operador_nome"].value_counts())

    with col_g2:
        st.subheader("📈 Distribuição por Status")
        st.bar_chart(df_filtered["status"].value_counts())

    # Exportação
    st.divider()
    csv = df_filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Baixar Relatório CSV",
        data=csv,
        file_name=f"relatorio_{datetime.now().strftime('%Y%m%d')}.csv",
        mime="text/csv",
        use_container_width=True
    )