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
            0%   { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.5); }
            70%  { box-shadow: 0 0 0 12px rgba(255, 146, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
        }

        .editor-header {
            background: linear-gradient(-45deg, #001E57, #030A1A, #0A2540, #001233);
            background-size: 300% 300%;
            animation: floatGradient 11s ease infinite, fadeInUp 0.55s ease-out;
            padding: 28px 32px;
            border-radius: 20px;
            color: white;
            margin-bottom: 26px;
            border-left: 6px solid #FF9200;
            box-shadow:
                0 16px 40px rgba(0, 30, 87, 0.22),
                0 0 0 1px rgba(255, 146, 0, 0.1);
            position: relative;
            overflow: hidden;
        }
        .editor-header::before {
            content: '';
            position: absolute;
            top: -45%;
            right: -6%;
            width: 240px;
            height: 240px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,146,0,0.2) 0%, transparent 70%);
            pointer-events: none;
        }
        .editor-header h2 {
            margin: 0;
            font-weight: 900;
            font-size: 1.85rem;
            letter-spacing: -0.5px;
            position: relative;
            z-index: 1;
        }
        .editor-header p {
            margin: 8px 0 0 0;
            color: #94A3B8;
            font-size: 0.95rem;
            position: relative;
            z-index: 1;
        }
        .editor-badge {
            display: inline-block;
            margin-top: 14px;
            background: linear-gradient(135deg, #FF9200, #FFB84D);
            color: #FFF;
            padding: 6px 14px;
            border-radius: 99px;
            font-weight: 800;
            font-size: 0.72rem;
            letter-spacing: 0.4px;
            animation: pulseGlow 2.2s infinite;
            position: relative;
            z-index: 1;
        }

        .editor-metric {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 18px 14px;
            text-align: center;
            box-shadow: 0 6px 18px rgba(0, 30, 87, 0.05);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            animation: fadeInUp 0.6s ease-out;
        }
        .editor-metric:hover {
            transform: translateY(-4px);
            border-color: rgba(255, 146, 0, 0.45);
            box-shadow: 0 12px 28px rgba(255, 146, 0, 0.12);
        }
        .editor-metric h3 {
            margin: 0;
            color: #001E57;
            font-size: 1.7rem;
            font-weight: 900;
        }
        .editor-metric h3.accent { color: #FF9200; }
        .editor-metric p {
            margin: 6px 0 0 0;
            color: #64748B;
            font-size: 0.72rem;
            font-weight: 800;
            text-transform: uppercase;
            letter-spacing: 0.4px;
        }

        /* Data editor mais clean */
        [data-testid="stDataFrame"],
        .stDataEditor {
            border-radius: 16px !important;
            box-shadow: 0 10px 30px rgba(0, 30, 87, 0.08) !important;
            border: 1px solid #E2E8F0 !important;
            overflow: hidden;
            animation: fadeInUp 0.7s ease-out;
        }

        .editor-toolbar {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 16px;
            animation: fadeInUp 0.5s ease-out;
        }

        .danger-zone {
            background: linear-gradient(135deg, #FFF5F5 0%, #FEF2F2 100%);
            border: 1px solid #FECACA;
            border-left: 4px solid #EF4444;
            border-radius: 14px;
            padding: 16px 18px;
            margin-top: 12px;
        }

        /* Botão salvar destaque */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #001E57 0%, #0B296B 100%) !important;
            border: none !important;
            border-radius: 12px !important;
            font-weight: 800 !important;
            height: 48px !important;
            transition: all 0.25s ease !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #FF9200 0%, #E07A00 100%) !important;
            transform: translateY(-2px);
            box-shadow: 0 8px 22px rgba(255, 146, 0, 0.3) !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # Header
    st.markdown(
        """
    <div class="editor-header">
        <h2>✏️ Editor de Apontamentos</h2>
        <p>Auditoria e correção em massa dos registros operacionais</p>
        <span class="editor-badge">🛡️ GESTÃO · MODO AUDITORIA</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

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