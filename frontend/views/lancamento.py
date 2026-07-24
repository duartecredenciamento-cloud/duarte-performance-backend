import streamlit as st
import time


def render_lancamento(api_post):
    # ===================== CSS PREMIUM (idêntico ao original — cores e identidade Duarte) =====================
    st.markdown("""
    <style>
        .lancamento-card {
            background: white;
            padding: 28px;
            border-radius: 20px;
            box-shadow: 0 15px 35px rgba(0, 30, 87, 0.08);
            border-top: 5px solid #FF9200;
        }
        .status-select {
            border-radius: 12px;
        }
        .stButton > button {
            background: linear-gradient(135deg, #FF9200, #E07A00);
            color: white;
            font-weight: 700;
            height: 52px;
            border-radius: 12px;
        }
        .justificativa-box {
            border-left: 4px solid #FF9200;
            background: #FFF9F0;
            padding: 14px 16px;
            border-radius: 8px;
            margin-bottom: 6px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="lancamento-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Lançar Execução Diária")
    st.caption("Registre as atividades realizadas hoje")

    # IMPORTANTE: aqui NÃO usamos st.form. Dentro de um st.form, mudar o
    # selectbox de status não dispara um rerender imediato — o campo de
    # justificativa só apareceria depois de clicar em salvar, o que não é
    # o comportamento pedido ("aparece assim que escolher o status").
    # Por isso os campos ficam soltos, e só o clique final é tratado como
    # "salvar".
    col1, col2 = st.columns(2)

    with col1:
        cliente = st.text_input(
            "🏢 Cliente / Prestador *",
            placeholder="Ex: Vivest, Hospital Santa Casa...",
            key="lanc_cliente",
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
            key="lanc_status",
        )

    # Justificativa só existe (é criada) quando o status exige. Para
    # "Realizado Total" ela nem aparece na tela.
    justificativa = ""
    exige_justificativa = status != "Realizado Total"

    if exige_justificativa:
        st.markdown('<div class="justificativa-box">', unsafe_allow_html=True)
        justificativa = st.text_area(
            "⚠️ Motivo / Justificativa *",
            placeholder="Explique o motivo deste status (obrigatório)...",
            height=110,
            key="lanc_justificativa",
        )
        st.markdown("</div>", unsafe_allow_html=True)

    salvar = st.button(
        "💾 Salvar Lançamento",
        use_container_width=True,
        type="primary",
        key="lanc_salvar",
    )

    st.markdown('</div>', unsafe_allow_html=True)

    if salvar:
        if not cliente.strip():
            st.error("❌ Informe o nome do cliente.")
            return

        if exige_justificativa and not justificativa.strip():
            st.error("❌ Justificativa é obrigatória para este status!")
            return

        payload = {
            "cliente_nome": cliente.strip(),
            "status": status,
            "justificativa": justificativa.strip(),
            # Campo extra de segurança: caso o backend ainda exija saber
            # quem lançou (não vinha no seu payload de referência, mas
            # evita um 422 caso o endpoint /registros/ ainda peça esse
            # campo obrigatoriamente). Não atrapalha se o backend ignorar.
            "operador_nome": (
                st.session_state.get("nome")
                or st.session_state.get("username")
                or ""
            ),
        }

        with st.spinner("Salvando..."):
            resposta = api_post("/registros/", payload)

        if resposta is not None and resposta.status_code in [200, 201]:
            st.success("✅ Lançamento registrado com sucesso!")
            st.balloons()
            time.sleep(1.2)
            st.rerun()
        elif resposta is not None:
            try:
                detalhe = resposta.json().get("detail", resposta.text)
            except Exception:
                detalhe = resposta.text
            st.error(f"❌ Erro ao salvar (status {resposta.status_code}): {detalhe}")
        else:
            st.error("❌ Erro ao salvar. Verifique a conexão com o backend.")