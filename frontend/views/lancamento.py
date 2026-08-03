import streamlit as st
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from views.permissoes import pode_editar, aviso_somente_leitura
from views.escala import get_cronograma_credenciamento

DIAS_SEMANA_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
FUSO_BR = ZoneInfo("America/Sao_Paulo")

PERFIS_VISAO_GERAL = {
    "admin master",
    "admin",
    "gestor",
    "coordenador",
    "visualizador",
}

PERFIS_PODEM_LANCAR = PERFIS_VISAO_GERAL | {"operador"}

DEBUG_DIAGNOSTICO = False


def _dia_semana_atual_brasil() -> str:
    return DIAS_SEMANA_PT[datetime.now(FUSO_BR).weekday()]


def _perfil_usuario_atual() -> str:
    perfil = (
        st.session_state.get("user_role")
        or st.session_state.get("perfil")
        or st.session_state.get("role")
        or st.session_state.get("perfil_usuario")
        or st.session_state.get("cargo")
        or ""
    )
    return str(perfil).strip().lower()


def _clientes_do_dia(nome_operador: str, dia_hoje: str, perfil_usuario: str) -> list:
    df_escala = get_cronograma_credenciamento()

    if dia_hoje not in df_escala.columns:
        return []

    perfil_normalizado = (perfil_usuario or "").strip().lower()
    visao_geral = perfil_normalizado in PERFIS_VISAO_GERAL

    if visao_geral:
        valores = df_escala[dia_hoje].dropna().astype(str).str.strip()
    else:
        nome_operador = (nome_operador or "").strip()
        if not nome_operador:
            return []
        primeiro_nome = nome_operador.split()[0] if nome_operador.split() else nome_operador
        filtro = (
            df_escala["Operador"].astype(str).str.strip().str.casefold()
            == primeiro_nome.strip().casefold()
        )
        valores = df_escala.loc[filtro, dia_hoje].dropna().astype(str).str.strip()

    clientes = [v for v in valores.unique().tolist() if v and v != "-"]
    return sorted(clientes)


def _todos_clientes_do_dia(dia_hoje: str) -> list:
    df_escala = get_cronograma_credenciamento()
    if dia_hoje not in df_escala.columns:
        return []
    valores = df_escala[dia_hoje].dropna().astype(str).str.strip()
    clientes = [v for v in valores.unique().tolist() if v and v != "-"]
    return sorted(clientes)


def render_lancamento(api_post, carregar_cronograma=None):
    # ===================== CSS PREMIUM =====================
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

        .lanc-hero {
            background: linear-gradient(-45deg, #001E57, #030A1A, #0B296B, #001233);
            background-size: 300% 300%;
            animation: floatGradient 12s ease infinite, fadeInUp 0.55s ease-out;
            padding: 28px 32px;
            border-radius: 22px;
            color: #fff;
            margin-bottom: 22px;
            border-left: 6px solid #FF9200;
            box-shadow: 0 16px 40px rgba(0, 30, 87, 0.22);
            position: relative;
            overflow: hidden;
        }
        .lanc-hero::before {
            content: '';
            position: absolute;
            top: -40%;
            right: -8%;
            width: 240px;
            height: 240px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,146,0,0.22) 0%, transparent 70%);
            pointer-events: none;
        }
        .lanc-hero h2 {
            margin: 0;
            font-weight: 900;
            font-size: 1.85rem;
            letter-spacing: -0.5px;
            position: relative;
            z-index: 1;
        }
        .lanc-hero p {
            margin: 8px 0 0 0;
            color: #94A3B8;
            font-size: 0.95rem;
            position: relative;
            z-index: 1;
        }
        .lanc-badge {
            display: inline-block;
            margin-top: 14px;
            background: linear-gradient(135deg, #FF9200, #FFB84D);
            color: #fff;
            padding: 6px 14px;
            border-radius: 99px;
            font-weight: 800;
            font-size: 0.72rem;
            letter-spacing: 0.4px;
            animation: pulseGlow 2.2s infinite;
            position: relative;
            z-index: 1;
        }

        .lanc-shell {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            padding: 26px 24px 20px 24px;
            border-radius: 20px;
            box-shadow: 0 12px 32px rgba(0, 30, 87, 0.07);
            border: 1px solid #E2E8F0;
            border-top: 5px solid #FF9200;
            animation: fadeInUp 0.6s ease-out;
            margin-bottom: 12px;
        }

        .lanc-chip-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin-bottom: 18px;
        }
        .lanc-chip {
            display: inline-flex;
            align-items: center;
            gap: 6px;
            background: rgba(0, 30, 87, 0.06);
            color: #001E57;
            border: 1px solid rgba(0, 30, 87, 0.1);
            padding: 6px 12px;
            border-radius: 99px;
            font-size: 0.78rem;
            font-weight: 700;
        }
        .lanc-chip.orange {
            background: rgba(255, 146, 0, 0.12);
            color: #C2410C;
            border-color: rgba(255, 146, 0, 0.28);
        }
        .lanc-chip.green {
            background: rgba(16, 185, 129, 0.12);
            color: #047857;
            border-color: rgba(16, 185, 129, 0.25);
        }

        .justificativa-box {
            border-left: 4px solid #FF9200;
            background: linear-gradient(135deg, #FFF9F0 0%, #FFF5E6 100%);
            padding: 16px 16px 6px 16px;
            border-radius: 12px;
            margin: 8px 0 14px 0;
            border: 1px solid rgba(255, 146, 0, 0.2);
            animation: fadeInUp 0.4s ease-out;
        }

        .lanc-section-title {
            color: #001E57;
            font-weight: 800;
            font-size: 1rem;
            margin: 4px 0 12px 0;
            letter-spacing: -0.2px;
        }

        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #FF9200 0%, #E07A00 100%) !important;
            color: white !important;
            font-weight: 800 !important;
            height: 52px !important;
            border-radius: 14px !important;
            border: none !important;
            box-shadow: 0 6px 18px rgba(255, 146, 0, 0.3) !important;
            transition: all 0.25s ease !important;
        }
        div.stButton > button[kind="primary"]:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 26px rgba(255, 146, 0, 0.4) !important;
            background: linear-gradient(135deg, #FFA733 0%, #FF9200 100%) !important;
        }

        div[data-testid="stSelectbox"] label,
        div[data-testid="stTextInput"] label,
        div[data-testid="stTextArea"] label {
            font-weight: 700 !important;
            color: #001E57 !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # ===================== HEADER =====================
    st.markdown(
        """
    <div class="lanc-hero">
        <h2>📝 Lançar Execução Diária</h2>
        <p>Registre as atividades operacionais do dia com base na escala</p>
        <span class="lanc-badge">⚡ APONTAMENTO · DIA CORRENTE</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    dia_hoje = _dia_semana_atual_brasil()
    nome_operador = (
        st.session_state.get("nome")
        or st.session_state.get("user_nome")
        or st.session_state.get("username")
        or ""
    )
    perfil_usuario = _perfil_usuario_atual()

    pode_lancar = perfil_usuario in PERFIS_PODEM_LANCAR or pode_editar(perfil_usuario)
    if not pode_lancar:
        aviso_somente_leitura()
        return

    clientes_hoje = _clientes_do_dia(nome_operador, dia_hoje, perfil_usuario)
    todos_clientes_hoje = _todos_clientes_do_dia(dia_hoje)

    # Chips de contexto
    visao_txt = "Visão geral do dia" if perfil_usuario in PERFIS_VISAO_GERAL else "Minha escala"
    st.markdown(
        f"""
    <div class="lanc-chip-row">
        <span class="lanc-chip">📅 {dia_hoje}</span>
        <span class="lanc-chip orange">👤 {nome_operador or "Usuário"}</span>
        <span class="lanc-chip green">🏷️ {perfil_usuario.title()}</span>
        <span class="lanc-chip">📋 {len(clientes_hoje)} cliente(s) · {visao_txt}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if DEBUG_DIAGNOSTICO:
        st.caption(
            f"🛠️ [DEV] Usuário: {nome_operador or '(vazio)'} | "
            f"Perfil: {perfil_usuario or '(vazio)'} | "
            f"Visão geral: {perfil_usuario in PERFIS_VISAO_GERAL} | "
            f"Clientes: {len(clientes_hoje)}"
        )

    # ===================== FORMULÁRIO =====================
    st.markdown('<div class="lanc-shell">', unsafe_allow_html=True)
    st.markdown('<p class="lanc-section-title">Novo apontamento</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)

    with col1:
        opcoes_cliente = (
            ["Selecione..."]
            + clientes_hoje
            + ["Suporte", "Outro (fora da escala de hoje)"]
        )
        if not clientes_hoje:
            st.info(
                "ℹ️ Nenhum cliente/serviço na escala de hoje. "
                "Use **Suporte** ou **Outro**."
            )

        cliente_sel = st.selectbox(
            "🏢 Cliente / Serviço *",
            opcoes_cliente,
            key="lanc_cliente_sel",
        )

        cliente_final = cliente_sel
        if cliente_sel == "Suporte":
            opcoes_suporte = ["Selecione..."] + [
                f"Suporte - {c}" for c in todos_clientes_hoje
            ]
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

    st.markdown("<br>", unsafe_allow_html=True)

    salvar = st.button(
        "💾 Salvar Lançamento",
        use_container_width=True,
        type="primary",
        key="lanc_salvar",
    )

    st.markdown("</div>", unsafe_allow_html=True)

    # ===================== SALVAR =====================
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
            "cliente_nome": str(cliente_final).strip(),
            "status": status,
            "justificativa": justificativa.strip(),
            "operador_nome": nome_operador,
        }

        with st.spinner("Salvando lançamento..."):
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