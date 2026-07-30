import streamlit as st
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from views.permissoes import pode_editar, aviso_somente_leitura

# Fonte real da escala: é a MESMA função que views/escala.py usa (a tabela
# fixa da matriz de Credenciamento). O backend tem uma rota /cronograma/,
# mas quem realmente popula a tela de Escala Semanal hoje é essa função
# local — então é dela que também puxamos os clientes daqui.
from views.escala import get_cronograma_credenciamento

DIAS_SEMANA_PT = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta", "Sábado", "Domingo"]
FUSO_BR = ZoneInfo("America/Sao_Paulo")

# Perfis que devem enxergar TODOS os clientes da escala do dia,
# independentemente de estarem cadastrados como "Operador" na matriz.
PERFIS_VISAO_GERAL = {"admin master", "admin", "gestor", "coordenador"}

# Flag de desenvolvimento: liga/desliga o caption de diagnóstico
# (usuário / perfil / quantidade de clientes encontrados). Basta trocar
# para False (ou apagar o bloco marcado abaixo) para remover em produção.
DEBUG_DIAGNOSTICO = True


def _dia_semana_atual_brasil() -> str:
    return DIAS_SEMANA_PT[datetime.now(FUSO_BR).weekday()]


def _perfil_usuario_atual() -> str:
    """Busca o perfil/role do usuário logado tentando várias chaves
    possíveis na sessão, sem quebrar caso alguma não exista.
    Retorna o valor já em minúsculas e sem espaços nas pontas, para
    facilitar a comparação com PERFIS_VISAO_GERAL."""
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
    """Usa a mesma tabela (formato largo: Operador, Periodo, Segunda...Sexta)
    que a tela de Escala Semanal usa de verdade, e decide automaticamente
    se retorna:

    - TODOS os clientes/serviços programados para o dia (perfis com visão
      geral: Admin Master, Admin, Gestor, Coordenador); ou
    - Somente os clientes vinculados ao operador logado (demais perfis).
    """
    df_escala = get_cronograma_credenciamento()

    if dia_hoje not in df_escala.columns:
        # Sábado/Domingo não existem na matriz — não tem escala nesses dias.
        return []

    perfil_normalizado = (perfil_usuario or "").strip().lower()
    visao_geral = perfil_normalizado in PERFIS_VISAO_GERAL

    if visao_geral:
        # Perfil de gestão: pega todos os valores da coluna do dia,
        # sem filtrar por operador.
        valores = df_escala[dia_hoje].dropna().astype(str).str.strip()
    else:
        nome_operador = (nome_operador or "").strip()
        if not nome_operador:
            return []

        filtro = df_escala["Operador"].astype(str).str.contains(
            nome_operador, case=False, na=False
        )
        valores = df_escala.loc[filtro, dia_hoje].dropna().astype(str).str.strip()

    clientes = [v for v in valores.unique().tolist() if v and v != "-"]
    return sorted(clientes)


def render_lancamento(api_post, carregar_cronograma=None):
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
            padding: 14px 16px;
            border-radius: 8px;
            margin-bottom: 6px;
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="lancamento-card">', unsafe_allow_html=True)

    # ===================== CABEÇALHO =====================
    st.markdown("""
    <div style="
        background: linear-gradient(135deg, #001E57 0%, #0A2540 100%);
        padding: 28px 30px;
        border-radius: 18px;
        color: white;
        margin-bottom: 25px;
        border-left: 6px solid #FF9200;
        box-shadow: 0 12px 28px rgba(0, 30, 87, 0.15);
    ">
        <h2 style="margin:0; font-weight:900; font-size:1.8rem;">
            📝 Lançar Execução Diária
        </h2>
        <p style="margin:8px 0 0 0; color:#CBD5E1; font-size:0.95rem;">
            Registre as atividades operacionais realizadas no dia
        </p>
    </div>
    """, unsafe_allow_html=True)

    # --- Monta a lista de Clientes/Serviços de hoje, a partir da escala real ---
    dia_hoje = _dia_semana_atual_brasil()
    nome_operador = (
        st.session_state.get("nome")
        or st.session_state.get("user_nome")
        or st.session_state.get("username")
        or ""
    )
    perfil_usuario = _perfil_usuario_atual()

    # ===================== CONTROLE DE PERMISSÃO =====================
    if not pode_editar(perfil_usuario):
        aviso_somente_leitura()
        st.markdown('</div>', unsafe_allow_html=True)
        return

    clientes_hoje = _clientes_do_dia(nome_operador, dia_hoje, perfil_usuario)

    st.caption(f"📅 Hoje é **{dia_hoje}-feira** — mostrando os clientes/serviços da sua escala de hoje.")

    # ===================== BLOCO DE DIAGNÓSTICO =====================
    if DEBUG_DIAGNOSTICO:
        st.caption(
            f"🛠️ [DEV] Usuário: {nome_operador or '(vazio)'} | "
            f"Perfil detectado: {perfil_usuario or '(vazio)'} | "
            f"Visão geral: {perfil_usuario in PERFIS_VISAO_GERAL} | "
            f"Clientes encontrados: {len(clientes_hoje)}"
        )

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