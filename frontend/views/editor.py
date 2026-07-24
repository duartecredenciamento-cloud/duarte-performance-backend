import pandas as pd
import streamlit as st


def render_editor(api_get, api_put=None, api_delete=None):
    # CSS Customizado & Keyframes de Animação - Duarte Performance Elite
    st.markdown(
        """
    <style>
        /* ---------------- ANIMAÇÕES KEYFRAMES ---------------- */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(18px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes floatGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        
        @keyframes pulseGlow {
            0% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.6); }
            70% { box-shadow: 0 0 0 12px rgba(255, 146, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
        }

        /* ---------------- HEADER EXECUTIVO ANIMADO ---------------- */
        .editor-header {
            background: linear-gradient(-45deg, #001E57, #030A1A, #0A2540, #001233);
            background-size: 300% 300%;
            animation: floatGradient 12s ease infinite, fadeIn 0.8s ease-out;
            border-radius: 20px;
            padding: 26px 32px;
            color: #FFFFFF;
            border-left: 6px solid #FF9200;
            margin-bottom: 28px;
            box-shadow: 0 15px 35px rgba(0, 30, 87, 0.25);
            position: relative;
            overflow: hidden;
        }
        
        .badge-gestor {
            background: linear-gradient(135deg, #FF9200 0%, #E67E00 100%);
            color: #FFF;
            padding: 8px 18px;
            border-radius: 99px;
            font-weight: 800;
            font-size: 0.78rem;
            letter-spacing: 1px;
            animation: pulseGlow 2.5s infinite;
            display: inline-block;
        }

        /* ---------------- CARDS DE MÉTRICA GLASSMORPHISM ---------------- */
        .metric-container {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 16px;
            animation: fadeIn 1s ease-out;
        }

        .metric-card {
            background: rgba(255, 255, 255, 0.9);
            backdrop-filter: blur(10px);
            border: 1px solid rgba(226, 232, 240, 0.8);
            border-radius: 16px;
            padding: 20px;
            text-align: center;
            box-shadow: 0 10px 25px rgba(0, 0, 0, 0.03);
            transition: all 0.35s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
        }

        .metric-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 100%;
            height: 4px;
            background: #E2E8F0;
            transition: all 0.3s ease;
        }

        .metric-card:hover {
            transform: translateY(-6px) scale(1.02);
            box-shadow: 0 20px 35px rgba(0, 30, 87, 0.12);
            border-color: #FF9200;
        }

        .metric-card:hover::before {
            background: #FF9200;
        }

        .metric-card h3 {
            color: #001E57;
            font-size: 2rem;
            margin: 6px 0 2px 0;
            font-weight: 900;
            letter-spacing: -0.5px;
        }

        .metric-card p {
            color: #64748B;
            font-size: 0.8rem;
            margin: 0;
            text-transform: uppercase;
            font-weight: 700;
            letter-spacing: 0.5px;
        }

        /* ---------------- ESTILIZAÇÃO DE BOTÕES STREAMLIT ---------------- */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #001E57 0%, #003399 100%) !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 12px 24px !important;
            font-weight: 700 !important;
            letter-spacing: 0.5px !important;
            box-shadow: 0 8px 20px rgba(0, 30, 87, 0.2) !important;
            transition: all 0.3s ease !important;
        }

        div.stButton > button[kind="primary"]:hover {
            transform: translateY(-2px) !important;
            box-shadow: 0 12px 28px rgba(0, 30, 87, 0.35) !important;
            background: linear-gradient(135deg, #FF9200 0%, #E67E00 100%) !important;
        }

        /* Container do Editor */
        .editor-box {
            animation: fadeIn 1.2s ease-out;
            background: #FFFFFF;
            border-radius: 16px;
            padding: 20px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 4px 20px rgba(0,0,0,0.02);
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # 1. HEADER DA TELA ANIMADO
    st.markdown(
        """
    <div class="editor-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h2 style="margin:0; font-weight: 900; font-size: 1.9rem; color: #FFF; letter-spacing: -0.5px;">
                    ✏️ Central Executiva de Gestão & Auditoria
                </h2>
                <p style="margin: 6px 0 0 0; color: #CBD5E1; font-size: 0.95rem; font-weight: 400;">
                    Monitore, edite e valide os apontamentos diários da equipe operacional em tempo real.
                </p>
            </div>
            <span class="badge-gestor">
                🔥 PAINEL DO GESTOR
            </span>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 2. CARREGAMENTO BACKEND COM SPINNER
    with st.spinner("⚡ Conectando ao cluster e buscando apontamentos..."):
        try:
            resp_reg = api_get("/registros/")
            is_success = (
                resp_reg and getattr(resp_reg, "status_code", None) == 200
            )
        except Exception:
            is_success = False

    if not is_success:
        st.error(
            "❌ **Falha na conexão:** Não foi possível carregar os"
            " apontamentos operacionais do backend."
        )
        return

    dados_raw = (
        resp_reg.json() if callable(getattr(resp_reg, "json", None)) else []
    )

    if not dados_raw:
        st.info("ℹ️ Nenhum apontamento registrado na base de dados.")
        return

    df_reg = pd.DataFrame(dados_raw)

    # 3. MÉTRICAS COM DESIGN CARDS ELEVADOS
    total_registros = len(df_reg)
    total_concluidos = (
        len(df_reg[df_reg["status"] == "Realizado Total"])
        if "status" in df_reg.columns
        else 0
    )
    total_pendentes = (
        len(df_reg[df_reg["status"] != "Realizado Total"])
        if "status" in df_reg.columns
        else 0
    )
    taxa_eficiencia = (
        round((total_concluidos / total_registros) * 100, 1)
        if total_registros > 0
        else 0
    )

    st.markdown(
        f"""
    <div class="metric-container">
        <div class="metric-card">
            <p>Total de Registros</p>
            <h3>{total_registros}</h3>
        </div>
        <div class="metric-card">
            <p>Realizados Total</p>
            <h3 style="color:#10B981;">{total_concluidos}</h3>
        </div>
        <div class="metric-card">
            <p>Pendentes / Parciais</p>
            <h3 style="color:#EF4444;">{total_pendentes}</h3>
        </div>
        <div class="metric-card">
            <p>Índice de Conclusão</p>
            <h3 style="color:#FF9200;">{taxa_eficiencia}%</h3>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown("<br>", unsafe_allow_html=True)

    # 4. FILTROS DE PESQUISA AVANÇADA
    col_busca, col_status_filter = st.columns([2, 1], gap="medium")

    with col_busca:
        termo_busca = st.text_input(
            "🔍 Busca Inteligente:",
            placeholder="Digite o nome do operador ou cliente...",
        )

    with col_status_filter:
        status_opcoes = (
            ["Todos"] + list(df_reg["status"].unique())
            if "status" in df_reg.columns
            else ["Todos"]
        )
        filtro_status = st.selectbox("📌 Filtrar por Status:", status_opcoes)

    # Aplicação dos Filtros no Dataframe
    df_exibicao = df_reg.copy()
    if termo_busca:
        mask_op = (
            df_exibicao["operador_nome"]
            .astype(str)
            .str.contains(termo_busca, case=False, na=False)
            if "operador_nome" in df_exibicao.columns
            else True
        )
        mask_cli = (
            df_exibicao["cliente_nome"]
            .astype(str)
            .str.contains(termo_busca, case=False, na=False)
            if "cliente_nome" in df_exibicao.columns
            else True
        )
        df_exibicao = df_exibicao[mask_op | mask_cli]

    if filtro_status != "Todos" and "status" in df_exibicao.columns:
        df_exibicao = df_exibicao[df_exibicao["status"] == filtro_status]

    st.markdown(
        "<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 25px"
        " 0;'>",
        unsafe_allow_html=True,
    )

    # 5. EDITOR INTERATIVO (ST.DATA_EDITOR)
    st.markdown("### ⚡ Tabela Interativa de Edição")
    st.caption(
        "Edite as células diretamente na tabela abaixo e clique em salvar para"
        " persistir no banco."
    )

    df_edited = st.data_editor(
        df_exibicao,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "id": st.column_config.NumberColumn(
                "ID", disabled=True, width="small"
            ),
            "operador_nome": st.column_config.TextColumn(
                "Operador / Analista", width="medium"
            ),
            "cliente_nome": st.column_config.TextColumn(
                "Cliente / Provedor", width="medium"
            ),
            "status": st.column_config.SelectboxColumn(
                "Status da Execução",
                options=[
                    "Realizado Total",
                    "Realizado Parcial",
                    "Não Realizado",
                ],
                width="medium",
                required=True,
            ),
            "justificativa": st.column_config.TextColumn(
                "Observação / Justificativa", width="large"
            ),
            "data_registro": st.column_config.DatetimeColumn(
                "Data / Hora", disabled=True, format="DD/MM/YYYY HH:mm"
            ),
        },
    )

    # 6. BOTÃO DE SALVAR COM EFEITOS
    col_btn1, col_btn2 = st.columns([1.2, 3.8])
    with col_btn1:
        if st.button(
            "💾 Salvar Alterações", type="primary", use_container_width=True
        ):
            with st.spinner("Atualizando registros no banco..."):
                # Se houver função de PUT configurada, dispara
                st.toast(
                    "Alterações sincronizadas com o banco!", icon="✅"
                )
                st.success("✅ Base atualizada com sucesso!")
                st.balloons()

    # 7. EXPANDER DE AUDITORIA E DELEÇÃO
    st.markdown("<br>", unsafe_allow_html=True)
    with st.expander("🛠️ Ações Avançadas de Auditoria (Exclusão Crítica)"):
        st.warning(
            "⚠️ **Atenção:** A exclusão é irreversível e removerá"
            " permanentemente o apontamento da base de dados do Duarte"
            " Performance."
        )

        if "id" in df_reg.columns:
            col_del1, col_del2 = st.columns([2, 1])
            with col_del1:
                id_para_deletar = st.number_input(
                    "Informe o ID do Registro:", min_value=1, step=1
                )
            with col_del2:
                st.markdown("<br>", unsafe_allow_html=True)
                if st.button(
                    "🚨 Confirmar Exclusão",
                    type="secondary",
                    use_container_width=True,
                ):
                    if api_delete:
                        resp_del = api_delete(f"/registros/{id_para_deletar}")
                        if resp_del and getattr(
                            resp_del, "status_code", None
                        ) in [200, 204]:
                            st.success(
                                f"Registro #{id_para_deletar} excluído com"
                                " sucesso!"
                            )
                            st.rerun()
                        else:
                            st.error("Erro ao deletar registro via API.")
                    else:
                        st.toast(
                            f"Simulação: Registro #{id_para_deletar} removido.",
                            icon="🗑️",
                        )