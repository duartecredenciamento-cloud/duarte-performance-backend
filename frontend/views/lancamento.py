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


def _dia_semana_atual_brasil() -> str:
    return DIAS_SEMANA_PT[datetime.now(FUSO_BR).weekday()]


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
    """Sempre tenta a API com token. Fallback só se a API falhar."""
    token = st.session_state.get("token")

    # 1) Função passada pelo app.py (cache)
    if carregar_cronograma is not None:
        try:
            df = carregar_cronograma()
            if df is not None and not (hasattr(df, "empty") and df.empty):
                from views.escala import _normalizar_colunas_escala
                return _normalizar_colunas_escala(df)
        except Exception:
            pass

    # 2) API direta com token
    df = get_cronograma_credenciamento(API_URL, token)
    return df


def _match_operador(serie_operador, nome_busca: str):
    """Match flexível: nome completo, primeiro nome, contém."""
    if not nome_busca or serie_operador is None:
        return serie_operador.astype(str).str.len() < 0  # máscara vazia

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
        .lanc-hero h2 { margin: 0; font-weight: 900; font-size: 1.85rem; position: relative; z-index: 1; }
        .lanc-hero p { margin: 8px 0 0 0; color: #94A3B8; font-size: 0.95rem; position: relative; z-index: 1; }
        .lanc-badge {
            display: inline-block; margin-top: 14px;
            background: linear-gradient(135deg, #FF9200, #FFB84D);
            color: #fff; padding: 6px 14px; border-radius: 99px;
            font-weight: 800; font-size: 0.72rem;
            animation: pulseGlow 2.2s infinite; position: relative; z-index: 1;
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
        .lanc-chip-row { display: flex; flex-wrap: wrap; gap: 8px; margin-bottom: 18px; }
        .lanc-chip {
            display: inline-flex; align-items: center; gap: 6px;
            background: rgba(0, 30, 87, 0.06); color: #001E57;
            border: 1px solid rgba(0, 30, 87, 0.1);
            padding: 6px 12px; border-radius: 99px;
            font-size: 0.78rem; font-weight: 700;
        }
        .lanc-chip.orange {
            background: rgba(255, 146, 0, 0.12); color: #C2410C;
            border-color: rgba(255, 146, 0, 0.28);
        }
        .lanc-chip.green {
            background: rgba(16, 185, 129, 0.12); color: #047857;
            border-color: rgba(16, 185, 129, 0.25);
        }
        .justificativa-box {
            border-left: 4px solid #FF9200;
            background: linear-gradient(135deg, #FFF9F0 0%, #FFF5E6 100%);
            padding: 16px 16px 6px 16px;
            border-radius: 12px; margin: 8px 0 14px 0;
            border: 1px solid rgba(255, 146, 0, 0.2);
        }
        .lanc-section-title {
            color: #001E57; font-weight: 800; font-size: 1rem; margin: 4px 0 12px 0;
        }
        .admin-box {
            background: #F0F7FF;
            border: 1px solid #BFDBFE;
            border-left: 4px solid #001E57;
            border-radius: 12px;
            padding: 14px 16px;
            margin-bottom: 16px;
        }
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #FF9200 0%, #E07A00 100%) !important;
            color: white !important; font-weight: 800 !important;
            height: 52px !important; border-radius: 14px !important; border: none !important;
            box-shadow: 0 6px 18px rgba(255, 146, 0, 0.3) !important;
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

    # Escala SEMPRE da API (com token)
    df_escala = _carregar_escala(carregar_cronograma)

    # ----- Admin: operador + data -----
    data_lancamento = date.today()
    nome_operador = nome_logado

    if eh_admin_lancar:
        st.markdown(
            """
        <div class="admin-box">
            <b>🛡️ Modo gestão</b> — você pode lançar em nome de qualquer operador
            e ajustar a data (correção / atraso).
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

    dia_ref = _dia_semana_de_data(data_lancamento)

    # Clientes do dia (da matriz atual da API)
    if eh_admin_lancar and nome_operador:
        clientes_hoje = _clientes_do_dia(
            df_escala, nome_operador, dia_ref, perfil_usuario, forcar_todos=False
        )
    else:
        clientes_hoje = _clientes_do_dia(
            df_escala, nome_operador, dia_ref, perfil_usuario
        )

    todos_clientes_hoje = _todos_clientes_do_dia(df_escala, dia_ref)

    visao_txt = (
        "Visão geral"
        if perfil_usuario in PERFIS_VISAO_GERAL and not eh_admin_lancar
        else "Escala do operador"
    )
    st.markdown(
        f"""
    <div class="lanc-chip-row">
        <span class="lanc-chip">📅 {dia_ref} · {data_lancamento.strftime("%d/%m/%Y")}</span>
        <span class="lanc-chip orange">👤 {nome_operador or "Usuário"}</span>
        <span class="lanc-chip green">🏷️ {perfil_usuario.title()}</span>
        <span class="lanc-chip">📋 {len(clientes_hoje)} cliente(s) · {visao_txt}</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    if DEBUG_DIAGNOSTICO:
        st.caption(
            f"[DEV] op={nome_operador} | perfil={perfil_usuario} | "
            f"dia={dia_ref} | clientes={clientes_hoje} | "
            f"linhas_escala={0 if df_escala is None else len(df_escala)}"
        )

    # ----- Formulário -----
    st.markdown('<div class="lanc-shell">', unsafe_allow_html=True)
    st.markdown('<p class="lanc-section-title">Novo apontamento</p>', unsafe_allow_html=True)

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
                "Confira se a escala foi salva na API ou use **Outro**."
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
            "operador_nome": str(nome_operador).strip(),
        }

        # Admin: data fixa ao meio-dia (evita fuso / “sem data”)
        if eh_admin_lancar:
            payload["data_registro"] = (
                f"{data_lancamento.isoformat()}T12:00:00"
            )

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