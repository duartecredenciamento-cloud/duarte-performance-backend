import streamlit as st
import time
from datetime import datetime
from zoneinfo import ZoneInfo

# Fuso horário do Brasil — necessário pra saber corretamente "qual dia da
# semana é hoje" mesmo rodando num servidor em UTC (Render).
FUSO_BR = ZoneInfo("America/Sao_Paulo")
DIAS_SEMANA_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]


def _dia_semana_atual_brasil() -> str:
    return DIAS_SEMANA_PT[datetime.now(FUSO_BR).weekday()]


def _clientes_do_operador_hoje(df_crono, nome_operador: str, dia_hoje: str) -> list:
    """Filtra o cronograma (formato vindo direto do backend: colunas
    operador, dia_semana, cliente, ...) pra achar só os clientes/serviços
    atribuídos a essa pessoa nesse dia da semana."""
    if df_crono is None or df_crono.empty:
        return []
    colunas_necessarias = {"operador", "dia_semana", "cliente"}
    if not colunas_necessarias.issubset(df_crono.columns):
        return []

    nome_operador = (nome_operador or "").strip().lower()
    filtro = (
        df_crono["operador"].astype(str).str.strip().str.lower() == nome_operador
    ) & (df_crono["dia_semana"] == dia_hoje)

    clientes = df_crono.loc[filtro, "cliente"].dropna().astype(str).str.strip()
    clientes = [c for c in clientes.unique().tolist() if c and c != "-"]
    return sorted(clientes)


def render_lancamento(api_post, carregar_cronograma=None):
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

    # --- Monta a lista de Clientes/Serviços de hoje, a partir da escala real ---
    dia_hoje = _dia_semana_atual_brasil()
    nome_operador = st.session_state.get("nome") or st.session_state.get("username") or ""

    df_crono = carregar_cronograma() if carregar_cronograma else None
    clientes_hoje = _clientes_do_operador_hoje(df_crono, nome_operador, dia_hoje)

    st.caption(f"📅 Hoje é **{dia_hoje}-feira** — mostrando os clientes/serviços da sua escala de hoje.")

    col1, col2 = st.columns(2)

    with col1:
        opcoes_cliente = ["Selecione..."] + clientes_hoje + ["Suporte", "Outro (fora da escala de hoje)"]
        if not clientes_hoje:
            st.info("ℹ️ Não encontramos nenhum cliente/serviço na sua escala de hoje. Use 'Suporte' ou 'Outro'.")

        cliente_sel = st.selectbox(
            "🏢 Cliente / Serviço *",
            opcoes_cliente,
            key="lanc_cliente_sel",
        )

        # Se escolher Suporte, abre um segundo select com os clientes de
        # hoje, formatados como "Suporte - Cliente" — assim fica registrado
        # que foi um atendimento de suporte, e pra quem.
        cliente_final = cliente_sel
        if cliente_sel == "Suporte":
            opcoes_suporte = ["Selecione..."] + [f"Suporte - {c}" for c in clientes_hoje]
            cliente_final = st.selectbox(
                "🛠️ Suporte para qual cliente?",
                opcoes_suporte,
                key="lanc_cliente_suporte",
            )
        elif cliente_sel == "Outro (fora da escala de hoje)":
            cliente_final = st.text_input(
                "Digite o nome do cliente/serviço",
                placeholder="Ex: Vivest, Hospital Santa Casa...",
                key="lanc_cliente_outro",
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
        cliente_invalido = (
            cliente_sel == "Selecione..."
            or not cliente_final
            or cliente_final in ("Selecione...", "")
        )
        if cliente_invalido:
            st.error("❌ Selecione o cliente/serviço antes de salvar.")
            return

        if exige_justificativa and not justificativa.strip():
            st.error("❌ Justificativa é obrigatória para este status!")
            return

        payload = {
            "cliente_nome": cliente_final.strip(),
            "status": status,
            "justificativa": justificativa.strip(),
            # Campo extra de segurança: caso o backend ainda exija saber
            # quem lançou (evita um 422 caso /registros/ ainda peça esse
            # campo obrigatoriamente). Não atrapalha se o backend ignorar.
            "operador_nome": nome_operador,
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