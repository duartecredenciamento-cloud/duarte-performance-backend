import os
import time
from datetime import datetime, date
from zoneinfo import ZoneInfo

import streamlit as st

from views.permissoes import pode_editar, aviso_somente_leitura
from views.escala import get_cronograma_credenciamento

DIAS_SEMANA_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
FUSO_BR = ZoneInfo("America/Sao_Paulo")

API_URL = os.getenv(
    "BACKEND_URL",
    "https://duarte-performance-backend-production.up.railway.app",
)

PERFIS_VISAO_GERAL = {
    "admin master",
    "admin",
    "gestor",
    "coordenador",
    "visualizador",
}

PERFIS_ADMIN_LANCAR = {
    "admin master",
    "admin",
    "gestor",
    "coordenador",
}

PERFIS_PODEM_LANCAR = PERFIS_VISAO_GERAL | {"operador"}

DEBUG_DIAGNOSTICO = False


def _dia_semana_de_data(d: date) -> str:
    return DIAS_SEMANA_PT[d.weekday()]


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


def _carregar_escala(carregar_cronograma=None):
    token = st.session_state.get("token")

    if carregar_cronograma is not None:
        try:
            df = carregar_cronograma()
            if df is not None and not (hasattr(df, "empty") and df.empty):
                from views.escala import _normalizar_colunas_escala
                return _normalizar_colunas_escala(df)
        except Exception:
            pass

    return get_cronograma_credenciamento(API_URL, token)


def _match_operador(serie_operador, nome_busca: str):
    if not nome_busca or serie_operador is None:
        return serie_operador.astype(str).str.len() < 0

    nome = str(nome_busca).strip()
    s = serie_operador.astype(str).str.strip()
    s_cf = s.str.casefold()
    nome_cf = nome.casefold()
    primeiro = nome.split()[0].casefold() if nome.split() else nome_cf

    return (
        (s_cf == nome_cf)
        | (s_cf == primeiro)
        | s_cf.str.contains(primeiro, na=False)
        | s_cf.str.contains(nome_cf, na=False)
    )


def _nome_padrao_escala(df_escala, nome_busca: str) -> str:
    if not nome_busca:
        return ""
    if df_escala is None or df_escala.empty or "Operador" not in df_escala.columns:
        return str(nome_busca).strip()

    filtro = _match_operador(df_escala["Operador"], nome_busca)
    hits = (
        df_escala.loc[filtro, "Operador"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
        .tolist()
    )
    if not hits:
        return str(nome_busca).strip()

    return min(hits, key=len)


def _clientes_do_dia(
    df_escala,
    nome_operador: str,
    dia_ref: str,
    perfil_usuario: str,
    forcar_todos: bool = False,
) -> list:
    if df_escala is None or df_escala.empty:
        return []
    if dia_ref not in df_escala.columns:
        return []

    perfil_normalizado = (perfil_usuario or "").strip().lower()
    visao_geral = forcar_todos or perfil_normalizado in PERFIS_VISAO_GERAL

    if visao_geral and not nome_operador:
        valores = df_escala[dia_ref].dropna().astype(str).str.strip()
    elif nome_operador:
        filtro = _match_operador(df_escala["Operador"], nome_operador)
        valores = df_escala.loc[filtro, dia_ref].dropna().astype(str).str.strip()
    else:
        return []

    clientes = [v for v in valores.unique().tolist() if v and v != "-"]
    return sorted(clientes)


def _todos_clientes_do_dia(df_escala, dia_ref: str) -> list:
    if df_escala is None or df_escala.empty or dia_ref not in df_escala.columns:
        return []
    valores = df_escala[dia_ref].dropna().astype(str).str.strip()
    clientes = [v for v in valores.unique().tolist() if v and v != "-"]
    return sorted(clientes)


def _todos_clientes_do_cronograma(df_escala) -> list:
    if df_escala is None or df_escala.empty:
        return []

    dias = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
    clientes = set()

    for dia in dias:
        if dia in df_escala.columns:
            valores = df_escala[dia].dropna().astype(str).str.strip()
            for v in valores:
                if v and v != "-":
                    clientes.add(v)

    return sorted(clientes)


def _lista_operadores(df_escala) -> list:
    if df_escala is None or df_escala.empty or "Operador" not in df_escala.columns:
        return []
    ops = (
        df_escala["Operador"]
        .dropna()
        .astype(str)
        .str.strip()
        .replace("", None)
        .dropna()
        .unique()
        .tolist()
    )
    return sorted(ops)


def render_lancamento(api_post, carregar_cronograma=None):
    st.markdown(
        """
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

    @keyframes fadeInUp {
        from { opacity: 0; transform: translateY(22px); }
        to   { opacity: 1; transform: translateY(0); }
    }
    @keyframes floatGradient {
        0%   { background-position: 0% 50%; }
        50%  { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    @keyframes pulseGlow {
        0%   { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.55); }
        70%  { box-shadow: 0 0 0 14px rgba(255, 146, 0, 0); }
        100% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
    }
    @keyframes softFloat {
        0%, 100% { transform: translateY(0); }
        50%      { transform: translateY(-3px); }
    }
    @keyframes slideDown {
        from { opacity: 0; transform: translateY(-12px); max-height: 0; }
        to   { opacity: 1; transform: translateY(0); max-height: 300px; }
    }
    @keyframes borderGlow {
        0%, 100% { border-color: rgba(255, 146, 0, 0.35); }
        50%      { border-color: rgba(255, 146, 0, 0.75); }
    }
    @keyframes successPop {
        0%   { transform: scale(0.8); opacity: 0; }
        50%  { transform: scale(1.05); }
        100% { transform: scale(1); opacity: 1; }
    }

    .lanc-hero {
        background: linear-gradient(-45deg, #001E57, #030A1A, #0B296B, #001233);
        background-size: 300% 300%;
        animation: floatGradient 14s ease infinite, fadeInUp 0.6s ease-out;
        padding: 32px 34px;
        border-radius: 24px;
        color: #fff;
        margin-bottom: 24px;
        border-left: 6px solid #FF9200;
        box-shadow: 0 20px 50px rgba(0, 30, 87, 0.28);
        position: relative;
        overflow: hidden;
    }
    .lanc-hero::before {
        content: '';
        position: absolute;
        top: -50%; right: -8%;
        width: 280px; height: 280px;
        border-radius: 50%;
        background: radial-gradient(circle, rgba(255,146,0,0.18) 0%, transparent 70%);
        pointer-events: none;
        animation: softFloat 6s ease-in-out infinite;
    }
    .lanc-hero h2 {
        margin: 0;
        font-weight: 900;
        font-size: 1.9rem;
        letter-spacing: -0.5px;
        position: relative;
        z-index: 1;
    }
    .lanc-hero p {
        margin: 8px 0 0 0;
        color: #94A3B8;
        font-size: 0.96rem;
        position: relative;
        z-index: 1;
    }
    .lanc-badge {
        display: inline-block;
        margin-top: 16px;
        background: linear-gradient(135deg, #FF9200, #FFB84D);
        color: #fff;
        padding: 7px 16px;
        border-radius: 99px;
        font-weight: 800;
        font-size: 0.73rem;
        letter-spacing: 0.4px;
        animation: pulseGlow 2.4s infinite;
        position: relative;
        z-index: 1;
        box-shadow: 0 4px 14px rgba(255, 146, 0, 0.35);
    }

    .lanc-shell {
        background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
        padding: 28px 26px 22px 26px;
        border-radius: 22px;
        box-shadow: 0 14px 40px rgba(0, 30, 87, 0.08);
        border: 1px solid #E2E8F0;
        border-top: 5px solid #FF9200;
        animation: fadeInUp 0.65s ease-out;
        margin-bottom: 16px;
        transition: box-shadow 0.3s ease;
    }
    .lanc-shell:hover {
        box-shadow: 0 18px 48px rgba(0, 30, 87, 0.12);
    }

    .lanc-chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        margin-bottom: 20px;
        animation: fadeInUp 0.55s ease-out;
    }
    .lanc-chip {
        display: inline-flex;
        align-items: center;
        gap: 7px;
        background: rgba(0, 30, 87, 0.06);
        color: #001E57;
        border: 1px solid rgba(0, 30, 87, 0.1);
        padding: 7px 14px;
        border-radius: 99px;
        font-size: 0.8rem;
        font-weight: 700;
        transition: all 0.25s ease;
    }
    .lanc-chip:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 12px rgba(0, 30, 87, 0.1);
    }
    .lanc-chip.orange {
        background: rgba(255, 146, 0, 0.12);
        color: #C2410C;
        border-color: rgba(255, 146, 0, 0.3);
    }
    .lanc-chip.green {
        background: rgba(16, 185, 129, 0.12);
        color: #047857;
        border-color: rgba(16, 185, 129, 0.28);
    }

    .justificativa-box {
        border-left: 5px solid #FF9200;
        background: linear-gradient(135deg, #FFF9F0 0%, #FFF5E6 100%);
        padding: 18px 18px 8px 18px;
        border-radius: 14px;
        margin: 12px 0 16px 0;
        border: 1px solid rgba(255, 146, 0, 0.25);
        animation: slideDown 0.4s ease-out, borderGlow 3s ease-in-out infinite;
        box-shadow: 0 4px 16px rgba(255, 146, 0, 0.1);
        overflow: hidden;
    }

    .lanc-section-title {
        color: #001E57;
        font-weight: 800;
        font-size: 1.05rem;
        margin: 4px 0 14px 0;
    }

    .admin-box {
        background: linear-gradient(135deg, #F0F7FF 0%, #E0F2FE 100%);
        border: 1px solid #BFDBFE;
        border-left: 5px solid #001E57;
        border-radius: 14px;
        padding: 16px 18px;
        margin-bottom: 18px;
        animation: fadeInUp 0.5s ease-out;
        box-shadow: 0 4px 14px rgba(0, 30, 87, 0.06);
    }

    div.stButton > button[kind="primary"] {
        background: linear-gradient(135deg, #FF9200 0%, #E07A00 100%) !important;
        color: white !important;
        font-weight: 800 !important;
        font-size: 1rem !important;
        height: 54px !important;
        border-radius: 16px !important;
        border: none !important;
        box-shadow: 0 8px 22px rgba(255, 146, 0, 0.35) !important;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
        letter-spacing: 0.3px !important;
    }
    div.stButton > button[kind="primary"]:hover {
        transform: translateY(-3px) !important;
        box-shadow: 0 12px 28px rgba(255, 146, 0, 0.45) !important;
        background: linear-gradient(135deg, #FFA733 0%, #FF9200 100%) !important;
    }
    div.stButton > button[kind="primary"]:active {
        transform: translateY(-1px) !important;
    }

    div[data-testid="stSelectbox"] > div > div,
    div[data-testid="stTextInput"] > div > div,
    div[data-testid="stDateInput"] > div > div {
        border-radius: 12px !important;
        border-color: #E2E8F0 !important;
        transition: border-color 0.2s ease, box-shadow 0.2s ease !important;
    }
    div[data-testid="stSelectbox"] > div > div:hover,
    div[data-testid="stTextInput"] > div > div:hover {
        border-color: #FF9200 !important;
    }
    div[data-baseweb="select"]:focus-within > div,
    div[data-testid="stTextInput"] input:focus {
        border-color: #FF9200 !important;
        box-shadow: 0 0 0 3px rgba(255, 146, 0, 0.15) !important;
    }

    div[data-testid="stTextArea"] textarea {
        border-radius: 12px !important;
        border-color: #E2E8F0 !important;
    }
    div[data-testid="stTextArea"] textarea:focus {
        border-color: #FF9200 !important;
        box-shadow: 0 0 0 3px rgba(255, 146, 0, 0.15) !important;
    }

    .success-box {
        background: linear-gradient(135deg, #ECFDF5 0%, #D1FAE5 100%);
        border: 1px solid #6EE7B7;
        border-left: 5px solid #10B981;
        border-radius: 14px;
        padding: 16px 18px;
        margin: 16px 0;
        animation: successPop 0.45s ease-out;
        color: #065F46;
        font-weight: 600;
    }

    @media (max-width: 640px) {
        .lanc-hero { padding: 22px 20px; border-radius: 18px; }
        .lanc-hero h2 { font-size: 1.45rem; }
        .lanc-shell { padding: 20px 16px; }
        .lanc-chip { font-size: 0.74rem; padding: 6px 11px; }
    }
</style>
""",
        unsafe_allow_html=True,
    )

    st.markdown(
        """
    <div class="lanc-hero">
        <h2>📝 Lançar Execução Diária</h2>
        <p>Registre as atividades operacionais com base na escala atualizada</p>
        <span class="lanc-badge">⚡ APONTAMENTO · ESCALA AO VIVO</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    perfil_usuario = _perfil_usuario_atual()
    nome_logado = (
        st.session_state.get("nome")
        or st.session_state.get("user_nome")
        or st.session_state.get("username")
        or ""
    )

    pode_lancar = perfil_usuario in PERFIS_PODEM_LANCAR or pode_editar(perfil_usuario)
    if not pode_lancar:
        aviso_somente_leitura()
        return

    eh_admin_lancar = perfil_usuario in PERFIS_ADMIN_LANCAR
    df_escala = _carregar_escala(carregar_cronograma)

    data_lancamento = date.today()
    nome_operador = nome_logado

    if eh_admin_lancar:
        st.markdown(
            """
        <div class="admin-box">
            <b>🛡️ Modo gestão</b> — lançar em nome de qualquer operador e ajustar a data.
            O nome gravado segue o <b>padrão da escala</b> (evita duplicar no dashboard).
        </div>
        """,
            unsafe_allow_html=True,
        )
        a1, a2 = st.columns(2)
        with a1:
            ops = _lista_operadores(df_escala)
            opcoes_op = ["Eu mesmo (logado)"] + ops
            escolha_op = st.selectbox(
                "👤 Lançar como operador",
                opcoes_op,
                key="lanc_admin_operador",
            )
            if escolha_op != "Eu mesmo (logado)":
                nome_operador = escolha_op
        with a2:
            data_lancamento = st.date_input(
                "📅 Data do lançamento",
                value=date.today(),
                key="lanc_admin_data",
            )

    nome_para_gravar = _nome_padrao_escala(df_escala, nome_operador)
    dia_ref = _dia_semana_de_data(data_lancamento)

    if eh_admin_lancar and nome_operador:
        clientes_hoje = _clientes_do_dia(
            df_escala, nome_operador, dia_ref, perfil_usuario, forcar_todos=False
        )
    else:
        clientes_hoje = _clientes_do_dia(
            df_escala, nome_operador, dia_ref, perfil_usuario
        )

    todos_clientes_cronograma = _todos_clientes_do_cronograma(df_escala)

    visao_txt = (
        "Visão geral"
        if perfil_usuario in PERFIS_VISAO_GERAL and not eh_admin_lancar
        else "Escala do operador"
    )
    st.markdown(
        f"""
    <div class="lanc-chip-row">
        <span class="lanc-chip">📅 {dia_ref} · {data_lancamento.strftime("%d/%m/%Y")}</span>
        <span class="lanc-chip orange">👤 {nome_para_gravar or nome_operador or "Usuário"}</span>
        <span class="lanc-chip green">🏷️ {perfil_usuario.title()}</span>
        <span class="lanc-chip">📋 {len(clientes_hoje)} cliente(s) · {visao_txt}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="lanc-shell">', unsafe_allow_html=True)
    st.markdown(
        '<p class="lanc-section-title">Novo apontamento</p>',
        unsafe_allow_html=True,
    )

    col1, col2 = st.columns(2)

    with col1:
        opcoes_cliente = (
            ["Selecione..."]
            + clientes_hoje
            + ["Suporte", "Outro (fora da escala)"]
        )
        if not clientes_hoje:
            st.info(
                "ℹ️ Nenhum cliente na escala para este operador/dia. "
                "Use **Outro** se precisar."
            )

        cliente_sel = st.selectbox(
            "🏢 Cliente / Serviço *",
            opcoes_cliente,
            key="lanc_cliente_sel",
        )

        cliente_final = cliente_sel
        if cliente_sel == "Suporte":
            opcoes_suporte = ["Selecione..."] + [
                f"Suporte - {c}" for c in todos_clientes_cronograma
            ]
            cliente_final = st.selectbox(
                "🛠️ Suporte para qual cliente?",
                opcoes_suporte,
                key="lanc_cliente_suporte",
            )
        elif cliente_sel == "Outro (fora da escala)":
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
            "operador_nome": str(nome_para_gravar or nome_operador).strip(),
            # SEMPRE envia a data selecionada
            "data_registro": f"{data_lancamento.isoformat()}T12:00:00",
        }

        with st.spinner("Salvando lançamento..."):
            resposta = api_post("/registros/", payload)

        if resposta is not None and resposta.status_code in [200, 201]:
            st.markdown(
                """
            <div class="success-box">
                ✅ Lançamento registrado com sucesso!
            </div>
            """,
                unsafe_allow_html=True,
            )
            st.balloons()
            time.sleep(1.4)
            st.rerun()
        elif resposta is not None:
            try:
                detalhe = resposta.json().get("detail", resposta.text)
            except Exception:
                detalhe = resposta.text
            st.error(f"❌ Erro ao salvar (status {resposta.status_code}): {detalhe}")
        else:
            st.error("❌ Erro ao salvar. Verifique a conexão com o backend.")