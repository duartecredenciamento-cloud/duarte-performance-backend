import pandas as pd
import streamlit as st

from views.permissoes import pode_editar, aviso_somente_leitura

STATUS_COM_JUSTIFICATIVA = [
    "Realizado Parcial",
    "Não Realizado",
    "Não Se Aplica",
    "Não Informado"
]

def render_editor(api_get, api_put, api_delete):

    # ===================== CSS =====================
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
        search = st.text_input("🔍 Buscar por Cliente ou Operador", key="editor_search")
    with col2:
        status_filter = st.selectbox(
            "Status",
            ["Todos"] + sorted(df["status"].dropna().unique().tolist()),
            key="editor_status_filter"
        )

    df_filtered = df.copy()

    if search:
        mask = (
            df_filtered["cliente_nome"].astype(str).str.contains(search, case=False, na=False) |
            df_filtered["operador_nome"].astype(str).str.contains(search, case=False, na=False)
        )
        df_filtered = df_filtered[mask]

    if status_filter != "Todos":
        df_filtered = df_filtered[df_filtered["status"] == status_filter]

    # ===================== CONTROLE DE PERMISSÃO =====================
    role_atual = st.session_state.get("user_role", "operador")

    if not pode_editar(role_atual):
        aviso_somente_leitura()

        st.subheader("📋 Registros (Somente Leitura)")
        colunas_mostrar = [
            "id",
            "operador_nome",
            "cliente_nome",
            "status",
            "justificativa",
            "data_registro",
        ]
        colunas_existentes = [
            c for c in colunas_mostrar if c in df_filtered.columns
        ]
        st.dataframe(
            df_filtered[colunas_existentes],
            use_container_width=True,
            hide_index=True,
        )
        return

    # ===================== EDITOR =====================
    st.subheader("📋 Edição em Massa")

    # Colunas que vamos mostrar (evita erro de DOM)
    colunas_mostrar = [
        "id",
        "operador_nome",
        "cliente_nome",
        "status",
        "justificativa",
        "data_registro"
    ]
    colunas_existentes = [c for c in colunas_mostrar if c in df_filtered.columns]
    df_edit = df_filtered[colunas_existentes].copy()

    edited_df = st.data_editor(
        df_edit,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="editor_data_editor",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "operador_nome": st.column_config.TextColumn("Operador", disabled=True),
            "cliente_nome": st.column_config.TextColumn("Cliente", required=True),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=[
                    "Realizado Total",
                    "Realizado Parcial",
                    "Não Realizado",
                    "Não Se Aplica",
                    "Não Informado"   # ← NOVO STATUS
                ],
                required=True
            ),
            "justificativa": st.column_config.TextColumn("Justificativa"),
            "data_registro": st.column_config.DatetimeColumn("Data", disabled=True, format="DD/MM/YYYY HH:mm"),
        }
    )

    # ===================== SALVAR =====================
    if st.button("💾 Salvar Todas as Alterações", type="primary", use_container_width=True):

        alterados = 0
        erros = 0

        for _, row in edited_df.iterrows():
            registro_id = int(row["id"])
            original = df[df["id"] == registro_id].iloc[0]

            houve_mudanca = (
                str(row.get("cliente_nome", "")) != str(original.get("cliente_nome", "")) or
                str(row.get("status", "")) != str(original.get("status", "")) or
                str(row.get("justificativa", "")) != str(original.get("justificativa", ""))
            )

            if not houve_mudanca:
                continue

            status_atual = str(row.get("status", ""))
            justificativa = str(row.get("justificativa", "")).strip()

            # Validação de justificativa
            if status_atual in STATUS_COM_JUSTIFICATIVA and not justificativa:
                st.error(f"❌ Registro #{registro_id}: justificativa obrigatória para o status '{status_atual}'.")
                return

            payload = {
                "cliente_nome": str(row.get("cliente_nome", "")),
                "status": status_atual,
                "justificativa": justificativa,
            }

            resp = api_put(f"/registros/{registro_id}", payload)

            if resp and resp.status_code in [200, 204]:
                alterados += 1
            else:
                erros += 1

        if erros > 0:
            st.error(f"⚠️ {erros} registro(s) não puderam ser atualizados.")
        elif alterados > 0:
            st.success(f"✅ {alterados} registro(s) atualizados com sucesso!")
            st.rerun()
        else:
            st.info("Nenhuma alteração detectada.")

    # ===================== EXCLUSÃO =====================
    with st.expander("🗑️ Excluir Registro"):
        if not df_filtered.empty:
            id_to_delete = st.selectbox(
                "ID do registro",
                df_filtered["id"].tolist(),
                key="editor_delete_id"
            )
            if st.button("Confirmar Exclusão", type="secondary", key="btn_delete"):
                resp = api_delete(f"/registros/{id_to_delete}")
                if resp and resp.status_code in [200, 204]:
                    st.success(f"Registro #{id_to_delete} excluído!")
                    st.rerun()
                else:
                    st.error("Erro ao excluir o registro.")