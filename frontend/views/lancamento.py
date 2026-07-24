import streamlit as st
import time


def render_lancamento(api_post):
    st.markdown("## 📝 Lançar Execução Diária")
    st.caption(
        "Registre a execução das atividades operacionais realizadas no dia."
    )

    with st.form("form_lancamento", clear_on_submit=True):

        col1, col2 = st.columns(2)

        with col1:
            cliente = st.text_input(
                "🏢 Cliente / Prestador *",
                placeholder="Ex: Vivest, Hospital X..."
            )

        with col2:
            status = st.selectbox(
                "📌 Status da Execução *",
                [
                    "Realizado Total",
                    "Realizado Parcial",
                    "Não Realizado",
                    "Não Se Aplica",
                ],
            )

        justificativa = ""

        if status != "Realizado Total":

            justificativa = st.text_area(
                "⚠️ Justificativa *",
                placeholder="Explique o motivo..."
            )

        else:

            justificativa = st.text_area(
                "💬 Observação (Opcional)",
                placeholder="Informações adicionais..."
            )

        salvar = st.form_submit_button(
            "🚀 Salvar Lançamento",
            use_container_width=True,
            type="primary",
        )

    if not salvar:
        return

    # ==========================
    # VALIDAÇÕES
    # ==========================

    if not cliente.strip():

        st.error("Informe o cliente.")

        return

    if (
        status != "Realizado Total"
        and not justificativa.strip()
    ):

        st.warning(
            "Informe uma justificativa."
        )

        return

    payload = {

        "cliente_nome": cliente.strip(),

        "status": status,

        "justificativa": justificativa.strip(),

    }

    with st.spinner("Salvando lançamento..."):

        resposta = api_post(
            "/registros/",
            payload
        )

    if resposta is None:

        st.error(
            "Erro de comunicação com o servidor."
        )

        return

    if resposta.status_code in [200, 201]:

        st.success(
            "✅ Lançamento registrado com sucesso!"
        )

        st.balloons()

        time.sleep(1)

        st.rerun()

    else:

        try:

            erro = resposta.json()

        except Exception:

            erro = resposta.text

        st.error(
            f"Erro ao salvar: {erro}"
        )