import pandas as pd
import streamlit as st
from datetime import datetime

from views.permissoes import pode_editar, aviso_somente_leitura

STATUS_COM_JUSTIFICATIVA = [
    "Realizado Parcial",
    "Não Realizado",
    "Não Se Aplica",
    "Não Informado",
]

STATUS_OPCOES = [
    "Realizado Total",
    "Realizado Parcial",
    "Não Realizado",
    "Não Se Aplica",
    "Não Informado",
]


def _to_dt(v):
    """Converte para datetime Python limpo (sem timezone e sem microsegundos)."""
    if v is None:
        return None
    try:
        if pd.isna(v):
            return None
    except Exception:
        pass

    try:
        ts = pd.Timestamp(v)
        if pd.isna(ts):
            return None
        dt = ts.to_pydatetime()
        if getattr(dt, "tzinfo", None) is not None:
            dt = dt.replace(tzinfo=None)
        return dt.replace(microsecond=0)
    except Exception:
        return None


def render_editor(api_get, api_put, api_delete):

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
            box-shadow: 0 16px 40px rgba(0, 30, 87, 0.22);
            position: relative;
            overflow: hidden;
        }
        .editor-header h2 {
            margin: 0; font-weight: 900; font-size: 1.85rem;
            position: relative; z-index: 1;
        }
        .editor-header p {
            margin: 8px 0 0 0; color: #94A3B8; font-size: 0.95rem;
            position: relative; z-index: 1;
        }
        .editor-badge {
            display: inline-block; margin-top: 14px;
            background: linear-gradient(135deg, #FF9200, #FFB84D);
            color: #FFF; padding: 6px 14px; border-radius: 99px;
            font-weight: 800; font-size: 0.72rem;
            animation: pulseGlow 2.2s infinite; position: relative; z-index: 1;
        }
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #001E57 0%, #0B296B 100%) !important;
            border: none !important; border-radius: 12px !important;
            font-weight: 800 !important; height: 48px !important;
        }
        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #FF9200 0%, #E07A00 100%) !important;
            transform: translateY(-2px);
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="editor-header">
        <h2>✏️ Editor de Apontamentos</h2>
        <p>Auditoria e correção — cliente, status, justificativa e <b>data</b></p>
        <span class="editor-badge">🛡️ GESTÃO · DATA EDITÁVEL</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.spinner("Carregando registros..."):
        resp = api_get("/registros/")

    if resp is None or resp.status_code != 200:
        st.error("Erro ao carregar dados.")
        return

    df = pd.DataFrame(resp.json())
    if df.empty:
        st.info("Nenhum registro encontrado.")
        return

    # Normaliza a data para datetime limpo (sem timezone)
    if "data_registro" in df.columns:
        df["data_registro"] = pd.to_datetime(df["data_registro"], errors="coerce")
        # Remove timezone se existir
        try:
            if df["data_registro"].dt.tz is not None:
                df["data_registro"] = df["data_registro"].dt.tz_localize(None)
        except Exception:
            pass

    total = len(df)
    concluidos = (
        len(df[df["status"] == "Realizado Total"]) if "status" in df.columns else 0
    )
    taxa = round((concluidos / total * 100), 1) if total > 0 else 0

    c1, c2, c3 = st.columns(3)
    c1.metric("Total Registros", total)
    c2.metric("Concluídos", concluidos)
    c3.metric("Taxa de Conclusão", f"{taxa}%")

    st.divider()

    col1, col2 = st.columns([3, 1])
    with col1:
        search = st.text_input(
            "🔍 Buscar por Cliente ou Operador", key="editor_search"
        )
    with col2:
        status_filter = st.selectbox(
            "Status",
            ["Todos"] + sorted(df["status"].dropna().unique().tolist()),
            key="editor_status_filter",
        )

    df_filtered = df.copy()
    if search:
        mask = (
            df_filtered["cliente_nome"]
            .astype(str)
            .str.contains(search, case=False, na=False)
            | df_filtered["operador_nome"]
            .astype(str)
            .str.contains(search, case=False, na=False)
        )
        df_filtered = df_filtered[mask]
    if status_filter != "Todos":
        df_filtered = df_filtered[df_filtered["status"] == status_filter]

    role_atual = (
        st.session_state.get("user_role")
        or st.session_state.get("role")
        or "operador"
    )

    if not pode_editar(role_atual):
        aviso_somente_leitura()
        colunas_mostrar = [
            "id",
            "operador_nome",
            "cliente_nome",
            "status",
            "justificativa",
            "data_registro",
        ]
        cols = [c for c in colunas_mostrar if c in df_filtered.columns]
        st.dataframe(df_filtered[cols], use_container_width=True, hide_index=True)
        return

    st.subheader("📋 Edição em Massa")
    st.caption(
        "Altere cliente, status, justificativa e **data** · depois clique em Salvar."
    )

    colunas_mostrar = [
        "id",
        "operador_nome",
        "cliente_nome",
        "status",
        "justificativa",
        "data_registro",
    ]
    colunas_existentes = [c for c in colunas_mostrar if c in df_filtered.columns]
    df_edit = df_filtered[colunas_existentes].copy()

    # Garante que a coluna de data esteja como datetime limpo para o editor
    if "data_registro" in df_edit.columns:
        df_edit["data_registro"] = pd.to_datetime(
            df_edit["data_registro"], errors="coerce"
        )

    edited_df = st.data_editor(
        df_edit,
        use_container_width=True,
        hide_index=True,
        num_rows="fixed",
        key="editor_data_editor",
        column_config={
            "id": st.column_config.NumberColumn(
                "ID", disabled=True, width="small"
            ),
            "operador_nome": st.column_config.TextColumn(
                "Operador", disabled=True
            ),
            "cliente_nome": st.column_config.TextColumn(
                "Cliente", required=True
            ),
            "status": st.column_config.SelectboxColumn(
                "Status",
                options=STATUS_OPCOES,
                required=True,
            ),
            "justificativa": st.column_config.TextColumn("Justificativa"),
            "data_registro": st.column_config.DatetimeColumn(
                "Data",
                format="DD/MM/YYYY HH:mm",
                step=60,
                required=False,
            ),
        },
    )

    if st.button(
        "💾 Salvar Todas as Alterações",
        type="primary",
        use_container_width=True,
        key="btn_salvar_editor",
    ):
        alterados = 0
        erros = 0

        for _, row in edited_df.iterrows():
            try:
                registro_id = int(row["id"])
            except Exception:
                continue

            try:
                original = df[df["id"] == registro_id].iloc[0]
            except Exception:
                continue

            cliente_novo = str(row.get("cliente_nome", "") or "").strip()
            status_novo = str(row.get("status", "") or "").strip()
            just_nova = str(row.get("justificativa", "") or "").strip()

            data_nova_dt = _to_dt(row.get("data_registro"))
            data_antiga_dt = _to_dt(original.get("data_registro"))

            # Detecta se a data mudou
            data_mudou = False
            if data_nova_dt is not None and data_antiga_dt is not None:
                data_mudou = data_nova_dt.replace(second=0, microsecond=0) != data_antiga_dt.replace(
                    second=0, microsecond=0
                )
            elif data_nova_dt is not None and data_antiga_dt is None:
                data_mudou = True

            houve_mudanca = (
                cliente_novo != str(original.get("cliente_nome", "") or "").strip()
                or status_novo != str(original.get("status", "") or "").strip()
                or just_nova != str(original.get("justificativa", "") or "").strip()
                or data_mudou
            )

            if not houve_mudanca:
                continue

            if status_novo in STATUS_COM_JUSTIFICATIVA and not just_nova:
                st.error(
                    f"❌ Registro #{registro_id}: justificativa obrigatória "
                    f"para o status '{status_novo}'."
                )
                return

            payload = {
                "cliente_nome": cliente_novo,
                "status": status_novo,
                "justificativa": just_nova,
            }

            # Envia a data se ela existir
            if data_nova_dt is not None:
                payload["data_registro"] = data_nova_dt.strftime("%Y-%m-%dT%H:%M:%S")

            resp = api_put(f"/registros/{registro_id}", payload)

            if resp is not None and resp.status_code in (200, 204):
                alterados += 1
            else:
                erros += 1
                detalhe = "sem resposta"
                if resp is not None:
                    try:
                        detalhe = resp.json().get("detail", resp.text)
                    except Exception:
                        detalhe = resp.text
                st.warning(f"Falha no #{registro_id}: {detalhe}")

        if erros > 0:
            st.error(f"⚠️ {erros} registro(s) não atualizados.")
        if alterados > 0:
            st.success(f"✅ {alterados} registro(s) atualizados!")
            st.rerun()
        elif erros == 0:
            st.info("Nenhuma alteração detectada.")

    with st.expander("🗑️ Excluir Registro"):
        if not df_filtered.empty and "id" in df_filtered.columns:
            id_to_delete = st.selectbox(
                "ID do registro",
                df_filtered["id"].tolist(),
                key="editor_delete_id",
            )
            if st.button(
                "Confirmar Exclusão", type="secondary", key="btn_delete"
            ):
                resp = api_delete(f"/registros/{id_to_delete}")
                if resp is not None and resp.status_code in (200, 204):
                    st.success(f"Registro #{id_to_delete} excluído!")
                    st.rerun()
                else:
                    st.error("Erro ao excluir o registro.")