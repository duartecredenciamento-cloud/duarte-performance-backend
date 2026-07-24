import streamlit as st
import time

def render_lancamento(api_post):
    # ===================== CSS PREMIUM =====================
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
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="lancamento-card">', unsafe_allow_html=True)
    st.markdown("### 📝 Lançar Execução Diária")
    st.caption("Registre as atividades realizadas hoje")

    with st.form("form_lancamento", clear_on_submit=True):
        col1, col2 = st.columns(2)

        with col1:
            cliente = st.text_input(
                "🏢 Cliente / Prestador *",
                placeholder="Ex: Vivest, Hospital Santa Casa..."
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
                key="status_select"
            )

        # LÓGICA DE JUSTIFICATIVA OBRIGATÓRIA
        justificativa = st.text_area(
            "⚠️ Justificativa / Observação",
            placeholder="Explique o motivo (obrigatório para status não total)...",
            height=120,
            key="justif"
        )

        # Validação visual
        if status != "Realizado Total":
            st.warning("⚠️ Justificativa é **obrigatória** para este status.")

        salvar = st.form_submit_button(
            "💾 Salvar Lançamento", 
            use_container_width=True,
            type="primary"
        )

    st.markdown('</div>', unsafe_allow_html=True)

    if salvar:
        if not cliente.strip():
            st.error("❌ Informe o nome do cliente.")
            return

        if status != "Realizado Total" and not justificativa.strip():
            st.error("❌ Justificativa é obrigatória para este status!")
            return

        payload = {
            "cliente_nome": cliente.strip(),
            "status": status,
            "justificativa": justificativa.strip()
        }

        with st.spinner("Salvando..."):
            resposta = api_post("/registros/", payload)

        if resposta and resposta.status_code in [200, 201]:
            st.success("✅ Lançamento registrado com sucesso!")
            st.balloons()
            time.sleep(1.2)
            st.rerun()
        else:
            st.error("❌ Erro ao salvar. Verifique a conexão.")