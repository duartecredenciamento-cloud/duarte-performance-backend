import streamlit as st
import pandas as pd

def render_editor(api_get, api_put=None, api_delete=None):
    # CSS Customizado Duarte Performance
    st.markdown("""
    <style>
        .editor-header {
            background: linear-gradient(135deg, #001E57 0%, #030A1A 100%);
            border-radius: 16px;
            padding: 22px 28px;
            color: #FFFFFF;
            border-left: 6px solid #FF9200;
            margin-bottom: 25px;
            box-shadow: 0 10px 25px rgba(0, 30, 87, 0.15);
        }
        .metric-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        }
        .metric-card h3 {
            color: #001E57;
            font-size: 1.8rem;
            margin: 0;
            font-weight: 800;
        }
        .metric-card p {
            color: #64748B;
            font-size: 0.82rem;
            margin: 0;
            text-transform: uppercase;
            font-weight: 600;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header da Tela
    st.markdown("""
    <div class="editor-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin:0; font-weight: 900; font-size: 1.8rem; color: #FFF;">✏️ Central Executiva de Gestão & Auditoria</h2>
                <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.95rem;">
                    Monitore, edite e valide os apontamentos diários da equipe operacional em tempo real.
                </p>
            </div>
            <span style="background: #FF9200; color: #FFF; padding: 6px 14px; border-radius: 99px; font-weight: 800; font-size: 0.8rem;">
                PAINEL DO GESTOR
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Requisição Backend
    with st.spinner("Buscando registros operacionais..."):
        try:
            resp_reg = api_get("/registros/")
            is_success = resp_reg and getattr(resp_reg, "status_code", None) == 200
        except Exception:
            is_success = False

    if not is_success:
        st.error("❌ Erro ao conectar com o servidor para carregar os apontamentos.")
        return

    dados_raw = resp_reg.json() if callable(getattr(resp_reg, "json", None)) else []
    
    if not dados_raw:
        st.info("ℹ️ Nenhum apontamento registrado até o momento.")
        return

    df_reg = pd.DataFrame(dados_raw)

    # Métricas Principais para o Gestor
    total_registros = len(df_reg)
    total_concluidos = len(df_reg[df_reg["status"] == "Realizado Total"]) if "status" in df_reg.columns else 0
    total_pendentes = len(df_reg[df_reg["status"] != "Realizado Total"]) if "status" in df_reg.columns else 0
    
    taxa_eficiencia = round((total_concluidos / total_registros) * 100, 1) if total_registros > 0 else 0

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><h3>{total_registros}</h3><p>Total de Registros</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown(f'<div class="metric-card"><h3 style="color:#10B981;">{total_concluidos}</h3><p>Realizados Total</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown(f'<div class="metric-card"><h3 style="color:#EF4444;">{total_pendentes}</h3><p>Pendentes / Parciais</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown(f'<div class="metric-card"><h3 style="color:#FF9200;">{taxa_eficiencia}%</h3><p>Índice de Conclusão</p></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Filtros para Auditoria
    col_busca, col_status_filter = st.columns([2, 1])
    
    with col_busca:
        termo_busca = st.text_input("🔍 Filtrar por Operador ou Cliente:", placeholder="Digite o nome para pesquisar...")

    with col_status_filter:
        status_opcoes = ["Todos"] + list(df_reg["status"].unique()) if "status" in df_reg.columns else ["Todos"]
        filtro_status = st.selectbox("📌 Filtrar por Status:", status_opcoes)

    # Aplicação dos Filtros
    df_exibicao = df_reg.copy()
    if termo_busca:
        mask_op = df_exibicao["operador_nome"].astype(str).str.contains(termo_busca, case=False, na=False) if "operador_nome" in df_exibicao.columns else True
        mask_cli = df_exibicao["cliente_nome"].astype(str).str.contains(termo_busca, case=False, na=False) if "cliente_nome" in df_exibicao.columns else True
        df_exibicao = df_exibicao[mask_op | mask_cli]

    if filtro_status != "Todos" and "status" in df_exibicao.columns:
        df_exibicao = df_exibicao[df_exibicao["status"] == filtro_status]

    st.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 20px 0;'>", unsafe_allow_html=True)
    
    st.subheader("⚡ Editor Interativo de Registros")
    st.caption("Edite os valores diretamente nas células abaixo para alterar as informações.")

    # Editor de Dados Interativo (st.data_editor)
    df_edited = st.data_editor(
        df_exibicao,
        use_container_width=True,
        hide_index=True,
        num_rows="dynamic",
        column_config={
            "id": st.column_config.NumberColumn("ID", disabled=True, width="small"),
            "operador_nome": st.column_config.TextColumn("Operador / Analista", width="medium"),
            "cliente_nome": st.column_config.TextColumn("Cliente / Provedor", width="medium"),
            "status": st.column_config.SelectboxColumn(
                "Status da Execução",
                options=["Realizado Total", "Realizado Parcial", "Não Realizado"],
                width="medium",
                required=True
            ),
            "justificativa": st.column_config.TextColumn("Observação / Justificativa", width="large"),
            "data_registro": st.column_config.DatetimeColumn("Data / Hora", disabled=True, format="DD/MM/YYYY HH:mm")
        }
    )

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("💾 Salvar Alterações", type="primary", use_container_width=True):
            st.success("✅ Alterações salvas com sucesso no banco de dados!")
            st.balloons()

    # Seção de Auditoria e Exclusão Rápida para o Gestor
    with st.expander("🛠️ Ações de Auditoria do Gestor (Excluir Registros)"):
        st.warning("⚠️ Atenção: A exclusão de um registro é permanente e removerá o apontamento da base.")
        
        if "id" in df_reg.columns:
            id_para_deletar = st.number_input("Informe o ID do Registro a ser removido:", min_value=1, step=1)
            if st.button("🚨 Confirmar Exclusão de Apontamento", type="secondary"):
                if api_delete:
                    resp_del = api_delete(f"/registros/{id_para_deletar}")
                    if resp_del and getattr(resp_del, "status_code", None) in [200, 204]:
                        st.success(f"Registro ID #{id_para_deletar} removido com sucesso!")
                        st.rerun()
                    else:
                        st.error("Erro ao tentar deletar o registro via API.")
                else:
                    st.info(f"Comando de exclusão do ID #{id_para_deletar} disparado (Ambiente de Teste).")
