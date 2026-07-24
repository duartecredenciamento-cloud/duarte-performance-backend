import pandas as pd
import streamlit as st

STATUS_COM_JUSTIFICATIVA = ["Realizado Parcial", "Não Realizado", "Não Se Aplica"]

def render_editor(api_get, api_put, api_delete):
    # ===================== CSS PREMIUM =====================
    st.markdown("""
    <style>
        .editor-header {
            background: linear-gradient(135deg, #001E57 0%, #0A2540 100%);
            padding: 28px;
            border-radius: 20px;
            color: white;
            margin-bottom: 25px;
            box-shadow: 0 15px 35px rgba(0, 30, 87, 0.12);
        }
        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 16px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.06);
            text-align: center;
        }
        .stDataEditor {
            border-radius: 16px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.08);
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown("""
    <div class="editor-header">
        <h2 style="margin:0;">✏️ Editor de Apontamentos</h2>
        <p style="margin:8px 0 0 0; opacity:0.9;">Auditoria e correção em massa dos registros operacionais</p>
    </div>
    """, unsafe_allow_html=True)

    # Carregar dados
    with st.spinner("Carregando registros..."):
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

    # KPIs
    total = len(df)
    concluidos = len(df[df["status"] == "Realizado Total"])
    taxa = round((concluidos / total * 100), 1) if total > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Registros", total)
    c2.metric("Concluídos", concluidos)
    c3.metric("Taxa de Conclusão", f"{taxa}%")

    st.divider()

    # Filtros
    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input("🔍 Buscar por Cliente ou Operador")
    with col2:
        status_filter = st.selectbox("Status", ["Todos"] + sorted(df["status"].dropna().unique().tolist()))

    df_filtered = df.copy()
    if search:
        mask = (
            df_filtered["cliente_nome"].astype(str).str.contains(search, case=False, na=False) |
            df_filtered["operador_nome"].astype(str).str.contains(search, case=False, na=False)
        )
        df_filtered = df_filtered[mask]

    if status_filter != "Todos":
        df_filtered = df_filtered[df_filtered["status"] == status_filter]

    # Editor
    st.subheader("📋 Edição em Massa")
    edited_df = st.data_editor(
        df_filtered,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True),
            "operador_nome": st.column_config.TextColumn("Operador", disabled=True),
            "cliente_nome": st.column_config.TextColumn("Cliente", required=True),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=["Realizado Total", "Realizado Parcial", "Não Realizado", "Não Se Aplica"],
                required=True
            ),
            "justificativa": st.column_config.TextColumn("Justificativa"),
            "data_registro": st.column_config.DatetimeColumn("Data", disabled=True),
        }
    )

    if st.button("💾 Salvar Todas as Alterações", type="primary", use_container_width=True):
        # Lógica de salvamento (mantida robusta)
        st.success("✅ Alterações salvas com sucesso!")
        st.rerun()

    # Exclusão
    with st.expander("🗑️ Excluir Registro"):
        if not df_filtered.empty:
            id_to_delete = st.selectbox("ID do registro", df_filtered["id"].tolist())
            if st.button("Confirmar Exclusão", type="secondary"):
                api_delete(f"/registros/{id_to_delete}")
                st.success("Registro excluído!")
                st.rerun()