import streamlit as st
import time

def render_lancamento(api_post, api_get=None):
    st.markdown("## 📝 Lançar Execução Diária")
    st.caption("Cadastre o status das entregas operacionais do dia.")

    with st.form("form_lancamento_diario", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            cliente_nome = st.text_input(
                "🏢 Nome do Cliente / Provedor *",
                placeholder="Ex: Vivest, Clínica X, Hospital Y..."
            )

        with col2:
            status_execucao = st.selectbox(
                "📌 Status da Execução *",
                options=[
                    "Realizado Total",
                    "Realizado Parcial",
                    "Não Realizado",
                    "Não Se Aplica"
                ]
            )

        # CAMPO DINÂMICO DE JUSTIFICATIVA/OBSERVAÇÃO
        # Aparece automaticamente se houver qualquer ressalva ou pendência
        justificativa = ""
        if status_execucao in ["Realizado Parcial", "Não Realizado", "Não Se Aplica"]:
            justificativa = st.text_area(
                "⚠️ Observação / Justificativa (Obrigatório) *",
                placeholder="Descreva o motivo da pendência, falta de documento ou bloqueio operacional...",
                help="Informe com clareza o motivo do status selecionado."
            )
        else:
            justificativa = st.text_area(
                "💬 Observação (Opcional)",
                placeholder="Detalhes adicionais sobre a execução, se houver..."
            )

        submitted = st.form_submit_button("🚀 Confirmar e Salvar Lançamento", type="primary")

        if submitted:
            # Validações dos campos obrigatórios
            if not cliente_nome.strip():
                st.error("❌ O nome do cliente/provedor é obrigatório.")
                return

            if status_execucao in ["Realizado Parcial", "Não Realizado", "Não Se Aplica"] and not justificativa.strip():
                st.warning("⚠️ É necessário preencher a justificativa para este status de execução.")
                return

            payload = {
                "cliente": cliente_nome.strip(),
                "status": status_execucao,
                "observacoes": justificativa.strip(),
                "justificativa": justificativa.strip() # Envia em ambas chaves para compatibilidade com a API
            }

            with st.spinner("Gravando dados no backend..."):
                try:
                    # Tenta a rota /execucoes/ e fallback para /registros/
                    res = api_post("/execucoes/", payload)
                    if not res or getattr(res, "status_code", None) not in [200, 201]:
                        res = api_post("/registros/", payload)

                    if res and getattr(res, "status_code", None) in [200, 201]:
                        st.success("✅ Lançamento registrado com sucesso!")
                        st.balloons()
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Falha ao salvar no banco. Verifique se o backend está ativo e autenticado.")
                except Exception as e:
                    st.error(f"❌ Erro de comunicação com a API: {e}")