import streamlit as st
import time

def render_lancamento(api_post_form):
    # Header Principal
    st.markdown("""
    <div style="margin-bottom: 25px;">
        <h1 style="color: #001E57; font-weight: 900; font-size: 2.2rem; margin-bottom: 4px;">
            📝 Apontamento de Execução Diária
        </h1>
        <p style="color: #64748B; font-size: 1rem; margin: 0;">
            Registre os resultados operacionais, pendências e justificativas das entregas do dia.
        </p>
    </div>
    """, unsafe_allow_html=True)

    # Identificação do Operador Conectado
    operador_atual = st.session_state.get("nome") or st.session_state.get("username") or "Operador"

    st.markdown(f"""
    <div style="background: rgba(0, 30, 87, 0.04); border-left: 4px solid #FF9200; padding: 12px 18px; border-radius: 8px; margin-bottom: 25px; display: flex; align-items: center; justify-content: space-between;">
        <span style="color: #001E57; font-weight: 700;">👤 Responsável pelo Apontamento: <strong style="color: #FF9200;">{operador_atual}</strong></span>
        <span style="background: #001E57; color: #FFF; font-size: 0.75rem; padding: 4px 10px; border-radius: 99px; font-weight: 700;">SESSÃO ATIVA</span>
    </div>
    """, unsafe_allow_html=True)

    # Formulário Principal Envelopado
    with st.form("form_diario_pro", clear_on_submit=True):
        col1, col2 = st.columns([1.5, 1], gap="medium")

        with col1:
            cliente_nome = st.text_input(
                "🏢 Nome do Cliente / Provedor *",
                placeholder="Ex: Vivest, Clinica X, Hospital Y...",
                help="Informe o nome exato do cliente ou prestador em atualização."
            )

            status = st.selectbox(
                "📌 Status da Execução *",
                options=["Realizado Total", "Realizado Parcial", "Não Realizado"],
                help="Selecione o resultado do trabalho executado hoje."
            )

        with col2:
            st.markdown("""
            <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 16px; margin-top: 25px;">
                <h5 style="color: #001E57; margin-bottom: 8px; font-weight: 800;">💡 Orientação Rápida</h5>
                <ul style="color: #64748B; font-size: 0.85rem; padding-left: 18px; margin: 0;">
                    <li><strong>Realizado Total:</strong> Processo 100% concluído.</li>
                    <li><strong>Realizado Parcial:</strong> Faltaram dados ou houve bloqueio.</li>
                    <li><strong>Não Realizado:</strong> Detalhar o motivo na justificativa.</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)

        # Campo Dinâmico de Justificativa
        justificativa = st.text_area(
            "💬 Observações / Justificativa Detalhada",
            placeholder="Descreva o que foi realizado ou o motivo de pendências/imprevistos...",
            height=120,
            help="Obrigatório para status Parcial ou Não Realizado."
        )

        # Upload de Evidência / Print (Opcional)
        arquivo_evidencia = st.file_uploader(
            "📎 Anexar Evidência / Comprovante (Opcional)",
            type=["png", "jpg", "pdf", "xlsx"],
            help="Anexe relatórios ou prints do sistema que comprovem a execução."
        )

        st.markdown("<br>", unsafe_allow_html=True)

        # Botão de Envio
        btn_submeter = st.form_submit_button("🚀 REGISTRAR APONTAMENTO DIÁRIO", type="primary", use_container_width=True)

    # Processamento do Formulário ao Clicar
    if btn_submeter:
        if not cliente_nome.strip():
            st.warning("⚠️ Por favor, informe o nome do cliente antes de enviar.")
        elif status != "Realizado Total" and not justificativa.strip():
            st.warning("⚠️ Para status 'Parcial' ou 'Não Realizado', a justificativa é obrigatória.")
        else:
            payload = {
                "operador_nome": operador_atual,
                "cliente_nome": cliente_nome.strip(),
                "status": status,
                "justificativa": justificativa.strip()
            }

            files_dict = None
            if arquivo_evidencia:
                files_dict = {"file": (arquivo_evidencia.name, arquivo_evidencia.getvalue(), arquivo_evidencia.type)}

            with st.spinner("Gravando dados no backend..."):
                resp = api_post_form("/registros/", data=payload, files=files_dict)

            if resp and resp.status_code in [200, 201]:
                st.balloons()
                st.success(f"✨ Apontamento do cliente **'{cliente_nome}'** gravado com sucesso!")
                time.sleep(1)
            else:
                st.error("❌ Não foi possível gravar o apontamento. Verifique a conexão com o servidor.")