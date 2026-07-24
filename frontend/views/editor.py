import pandas as pd
import streamlit as st


STATUS_COM_JUSTIFICATIVA = [
    "Realizado Parcial",
    "Não Realizado",
    "Não Se Aplica",
]


def render_editor(api_get, api_put, api_delete):

    # =====================================================
    # HEADER EXECUTIVO
    # =====================================================
    st.markdown(
        """
        <div style="
            background: linear-gradient(135deg, #001E57 0%, #0A2540 100%);
            padding: 22px;
            border-radius: 18px;
            color: white;
            margin-bottom: 20px;
            border-left: 5px solid #FF9200;
        ">
            <h2 style="margin:0;">✏️ Central Executiva de Apontamentos</h2>
            <p style="margin:6px 0 0 0; color:#CBD5E1;">
                Edite, audite e acompanhe os registros operacionais da equipe.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # =====================================================
    # CARREGAMENTO
    # =====================================================
    with st.spinner("🔄 Carregando registros..."):
        resposta = api_get("/registros/")

    if resposta is None:
        st.error("❌ Erro de comunicação com o backend.")
        return

    if resposta.status_code == 401:
        st.error("🔒 Sessão expirada. Faça login novamente.")
        return

    if resposta.status_code != 200:
        st.error("❌ Não foi possível carregar os registros.")
        return

    registros = resposta.json()

    if not registros:
        st.info("ℹ️ Nenhum registro encontrado.")
        return

    df = pd.DataFrame(registros)

    # =====================================================
    # TRATAMENTO DE DATA
    # =====================================================
    if "data_registro" in df.columns:
        df["data_registro"] = pd.to_datetime(
            df["data_registro"],
            errors="coerce"
        )

    # =====================================================
    # KPIs
    # =====================================================
    total = len(df)
    concluidos = len(df[df["status"] == "Realizado Total"])
    pendentes = len(df[df["status"] != "Realizado Total"])
    taxa = round((concluidos / total) * 100, 1) if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)

    c1.metric("Total", total)
    c2.metric("Realizados", concluidos)
    c3.metric("Pendentes", pendentes)
    c4.metric("Eficiência", f"{taxa}%")

    st.divider()

    # =====================================================
    # FILTROS
    # =====================================================
    col_f1, col_f2 = st.columns([2, 1])

    with col_f1:
        pesquisa = st.text_input(
            "🔍 Pesquisar Cliente ou Operador"
        )

    with col_f2:
        status_filtro = st.selectbox(
            "Status",
            ["Todos"] + sorted(df["status"].dropna().unique().tolist())
        )

    df_filtrado = df.copy()

    if pesquisa:
        termo = pesquisa.lower()

        filtro = (
            df_filtrado["cliente_nome"]
            .astype(str)
            .str.lower()
            .str.contains(termo, na=False)
        ) | (
            df_filtrado["operador_nome"]
            .astype(str)
            .str.lower()
            .str.contains(termo, na=False)
        )

        df_filtrado = df_filtrado[filtro]

    if status_filtro != "Todos":
        df_filtrado = df_filtrado[
            df_filtrado["status"] == status_filtro
        ]

    # =====================================================
    # TABELA EDITÁVEL
    # =====================================================
    st.subheader("🛠️ Edição Direta dos Registros")

    df_editado = st.data_editor(
        df_filtrado,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        column_config={
            "id": st.column_config.NumberColumn(
                "ID",
                disabled=True,
                width="small"
            ),
            "operador_nome": st.column_config.TextColumn(
                "Operador",
                disabled=True
            ),
            "cliente_nome": st.column_config.TextColumn(
                "Cliente",
                required=True
            ),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=[
                    "Realizado Total",
                    "Realizado Parcial",
                    "Não Realizado",
                    "Não Se Aplica",
                ],
                required=True,
            ),
            "justificativa": st.column_config.TextColumn(
                "Observação / Justificativa"
            ),
            "data_registro": st.column_config.DatetimeColumn(
                "Data / Hora",
                disabled=True,
                format="DD/MM/YYYY HH:mm"
            ),
        },
    )

    st.caption(
        "Status com pendência exigem justificativa obrigatória."
    )

    # =====================================================
    # SALVAR ALTERAÇÕES
    # =====================================================
    if st.button(
        "💾 Salvar Alterações",
        type="primary",
        use_container_width=True,
    ):

        alterados = 0
        erros = 0

        for _, row in df_editado.iterrows():

            registro_id = int(row["id"])

            # Registro original
            original = df[df["id"] == registro_id].iloc[0]

            houve_mudanca = (
                str(row.get("cliente_nome", ""))
                != str(original.get("cliente_nome", ""))
            ) or (
                str(row.get("status", ""))
                != str(original.get("status", ""))
            ) or (
                str(row.get("justificativa", ""))
                != str(original.get("justificativa", ""))
            )

            if not houve_mudanca:
                continue

            # VALIDAÇÃO OBRIGATÓRIA
            status_atual = str(row.get("status", ""))
            justificativa = str(row.get("justificativa", "")).strip()

            if (
                status_atual in STATUS_COM_JUSTIFICATIVA
                and not justificativa
            ):
                st.error(
                    f"❌ Registro #{registro_id}: a justificativa é obrigatória para o status '{status_atual}'."
                )
                return

            payload = {
                "cliente_nome": str(row.get("cliente_nome", "")),
                "status": status_atual,
                "justificativa": justificativa,
            }

            resp = api_put(
                f"/registros/{registro_id}",
                payload
            )

            if resp and resp.status_code in [200, 204]:
                alterados += 1
            else:
                erros += 1

        if erros > 0:
            st.error(
                f"⚠️ {erros} registro(s) não puderam ser atualizados."
            )

        elif alterados > 0:
            st.success(
                f"✅ {alterados} registro(s) atualizados com sucesso!"
            )
            st.balloons()
            st.rerun()

        else:
            st.info("Nenhuma alteração detectada.")

    st.divider()

    # =====================================================
    # EXCLUSÃO
    # =====================================================
    with st.expander("🗑️ Exclusão de Registro (Irreversível)"):

        st.warning(
            "Esta ação remove permanentemente o apontamento do banco de dados."
        )

        ids = df_filtrado["id"].tolist()

        registro_excluir = st.selectbox(
            "Selecione o ID",
            ids
        )

        if st.button(
            "🚨 Confirmar Exclusão",
            use_container_width=True
        ):

            resp = api_delete(
                f"/registros/{registro_excluir}"
            )

            if resp and resp.status_code in [200, 204]:

                st.success(
                    f"Registro #{registro_excluir} excluído com sucesso."
                )

                st.rerun()

            else:

                st.error(
                    "Erro ao excluir o registro."
                )