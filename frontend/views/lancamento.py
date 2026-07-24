import os
import requests
import streamlit as st

# URL base da API (obtida de variável de ambiente ou fallback)
API_URL = os.getenv("BACKEND_URL", "https://duarte-performance-backend.onrender.com")


def render_lancamento():
    st.title("📝 Apontamento de Execução Diária")
    st.caption(
        "Registre os resultados operacionais, pendências e justificativas das entregas do dia."
    )

    # Identificação do usuário ativo na sessão
    user_nome = st.session_state.get("user_nome", "Operador")
    st.info(f"👤 **Responsável pelo Apontamento:** {user_nome}")

    st.markdown("---")

    # Formulário de inserção com limpeza automática ao enviar
    with st.form("form_execucao", clear_on_submit=True):
        col_form, col_orientacao = st.columns([2, 1], gap="large")

        with col_form:
            cliente = st.text_input(
                "🏢 Nome do Cliente / Provedor *",
                placeholder="Ex: Vivest, Clínica X, Hospital Y...",
            )

            status_execucao = st.selectbox(
                "📌 Status da Execução *",
                ["Realizado Total", "Realizado Parcial", "Não Realizado", "Não Se Aplica"],
                index=0,
            )

            # 🎯 REGRA CONDICIONAL: Ouve o status e só exibe o campo se for Parcial ou Não Realizado
            observacoes = ""
            if status_execucao in ["Realizado Parcial", "Não Realizado", "Não Se Aplica"]:
                observacoes = st.text_area(
                    "💬 Observações / Justificativa Detalhada *",
                    placeholder=(
                        "Descreva o motivo da pendência, bloqueios de sistema,"
                        " falhas ou itens pendentes..."
                    ),
                    height=120,
                )

        with col_orientacao:
            st.markdown("""
            ### 💡 Orientação Rápida

            * **Realizado Total:**  
              Processo 100% concluído e sem pendências.

            * **Realizado Parcial:**  
              Faltaram dados, documentos ou o sistema apresentou bloqueios parciais.

            * **Não Realizado:**  
              Entrega não efetuada. **Obrigatório informar a justificativa.**
            """)

        st.markdown("---")
        submit = st.form_submit_button(
            "🚀 GRAVAR EXECUÇÃO", type="primary", use_container_width=True
        )

        if submit:
            # 1. Validação do Nome do Cliente
            if not cliente.strip():
                st.warning("⚠️ Preencha o nome do cliente / provedor.")

            # 2. Validação da Observação Condicional
            elif (
                status_execucao in ["Realizado Parcial", "Não Realizado", "Não Se Aplica"]
                and not observacoes.strip()
            ):
                st.error(
                    "⚠️ Para status Parcial ou Não Realizado, o campo de"
                    " Observação/Justificativa é obrigatório!"
                )

            # 3. Processamento do Envio para o Backend
            else:
                payload = {
                    "cliente": cliente.strip(),
                    "status": status_execucao,
                    "observacoes": observacoes.strip(),
                }

                # Recupera token do usuário se houver autenticação
                token = st.session_state.get("token", "")
                headers = {"Authorization": f"Bearer {token}"} if token else {}

                try:
                    res = requests.post(
                        f"{API_URL}/execucoes/", json=payload, headers=headers
                    )

                    if res.status_code in [200, 201]:
                        st.success("✅ Execução registrada com sucesso!")
                        st.balloons()
                    else:
                        st.error(
                            f"❌ Erro ao salvar registro ({res.status_code}):"
                            f" {res.text}"
                        )

                except Exception as e:
                    st.error(
                        f"❌ Erro de conexão com o servidor backend: {e}"
                    )


# Execução direta do render da tela
render_lancamento()