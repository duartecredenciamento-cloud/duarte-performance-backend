"""
Módulo: dashboard.py
Sistema: Duarte Performance — Duarte Gestão em Saúde

Dashboard gerencial de execuções operacionais.

Uso no app.py:
    from views.dashboard import render_dashboard
    render_dashboard(api_get)
"""

from __future__ import annotations

import html
import json
import unicodedata
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Callable, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

try:
    from zoneinfo import ZoneInfo

    FUSO_BR = ZoneInfo("America/Sao_Paulo")
except Exception:
    FUSO_BR = None


# ============================================================
# IDENTIDADE VISUAL
# ============================================================

AZUL = "#001E57"
AZUL_MEDIO = "#0B296B"
LARANJA = "#FF9200"
LARANJA_CLARO = "#FFB84D"

VERDE = "#10B981"
AMARELO = "#F59E0B"
VERMELHO = "#EF4444"
CINZA = "#94A3B8"
GRAFITE = "#64748B"

TEXTO = "#0F172A"
TEXTO_SECUNDARIO = "#64748B"

STATUS_ORDEM = [
    "Realizado Total",
    "Realizado Parcial",
    "Não Realizado",
    "Não Se Aplica",
    "Não Informado",
]

CORES_STATUS = {
    "Realizado Total": VERDE,
    "Realizado Parcial": AMARELO,
    "Não Realizado": VERMELHO,
    "Não Se Aplica": CINZA,
    "Não Informado": GRAFITE,
}

ESCALA_EFICIENCIA = [
    [0.0, VERMELHO],
    [0.5, AMARELO],
    [1.0, VERDE],
]

CONFIG_GRAFICO = {
    "displayModeBar": False,
    "responsive": True,
}


# ============================================================
# HELPERS DE HTML
# ============================================================

def _html_em_uma_linha(conteudo: str) -> str:
    """
    Evita que o Markdown do Streamlit interprete HTML recuado
    como bloco de código.

    Usar este helper para TODOS os fragmentos HTML renderizados
    com st.markdown(..., unsafe_allow_html=True).
    """
    return " ".join(
        linha.strip()
        for linha in conteudo.splitlines()
        if linha.strip()
    )


def _render_html(conteudo: str) -> None:
    st.markdown(
        _html_em_uma_linha(conteudo),
        unsafe_allow_html=True,
    )


# ============================================================
# NORMALIZAÇÃO E ACESSO A DADOS
# ============================================================

def _texto(valor: Any) -> str:
    if valor is None:
        return ""

    try:
        if pd.isna(valor):
            return ""
    except (TypeError, ValueError):
        pass

    resultado = str(valor).strip()

    if resultado.casefold() in {"nan", "none", "null", "nat"}:
        return ""

    return resultado


def _sem_acentos(valor: str) -> str:
    normalizado = unicodedata.normalize("NFKD", valor)

    return "".join(
        caractere
        for caractere in normalizado
        if not unicodedata.combining(caractere)
    )


def _chave_nome(nome: Any) -> str:
    """
    Normaliza o nome completo, sem juntar operadores diferentes
    que compartilham apenas o primeiro nome.
    """
    nome_limpo = " ".join(_texto(nome).split())
    return _sem_acentos(nome_limpo).casefold()


def _rotulo_operador(nomes: pd.Series) -> str:
    validos = [_texto(nome) for nome in nomes]
    validos = [nome for nome in validos if nome]

    if not validos:
        return "Não informado"

    return max(validos, key=lambda nome: (len(nome), nome))


def _normalizar_status(valor: Any) -> str:
    texto = _texto(valor)

    if not texto:
        return "Não Informado"

    chave = _sem_acentos(texto).casefold()

    equivalencias = {
        "realizado": "Realizado Total",
        "realizado total": "Realizado Total",
        "realizado parcial": "Realizado Parcial",
        "nao realizado": "Não Realizado",
        "nao se aplica": "Não Se Aplica",
        "n/a": "Não Se Aplica",
        "nao informado": "Não Informado",
    }

    return equivalencias.get(chave, texto)


def _agora_br() -> datetime:
    return datetime.now(FUSO_BR) if FUSO_BR else datetime.now()


def _converter_data_br(valor: Any) -> pd.Timestamp:
    if valor is None or _texto(valor) == "":
        return pd.NaT

    try:
        data = pd.Timestamp(valor)

        if pd.isna(data):
            return pd.NaT

        if data.tzinfo is not None:
            if FUSO_BR is not None:
                data = data.tz_convert(FUSO_BR)

            data = data.tz_localize(None)

        return data

    except (TypeError, ValueError, OverflowError):
        return pd.NaT


def _buscar_registros(
    api_get_fn: Callable[[str], Any],
) -> Optional[list[dict]]:
    """
    Busca sem cache global, pois os registros são acessados
    em sessões autenticadas.
    """
    try:
        resposta = api_get_fn("/registros/")

        if resposta is None:
            return None

        if getattr(resposta, "status_code", None) != 200:
            return None

        dados = resposta.json()

        if isinstance(dados, dict):
            dados = dados.get("data", [])

        if not isinstance(dados, list):
            return None

        return [
            item
            for item in dados
            if isinstance(item, dict)
        ]

    except Exception:
        return None


def _carregar_dataframe(
    api_get_fn: Callable[[str], Any],
) -> Optional[pd.DataFrame]:
    with st.spinner("Carregando indicadores gerenciais..."):
        dados = _buscar_registros(api_get_fn)

    if dados is None:
        return None

    df = pd.DataFrame(dados)

    if df.empty:
        return df

    for coluna in (
        "operador_nome",
        "cliente_nome",
        "status",
        "justificativa",
    ):
        if coluna not in df.columns:
            df[coluna] = ""

    if "data_registro" not in df.columns:
        df["data_registro"] = pd.NaT
    else:
        df["data_registro"] = pd.to_datetime(
            df["data_registro"].map(_converter_data_br),
            errors="coerce",
        )

    df["status"] = df["status"].map(_normalizar_status)

    df["operador_nome"] = df["operador_nome"].map(_texto)
    df["cliente_nome"] = df["cliente_nome"].map(_texto)
    df["justificativa"] = df["justificativa"].map(_texto)

    df["op_key"] = df["operador_nome"].map(_chave_nome)

    mapa_operadores = (
        df.groupby("op_key", dropna=False)["operador_nome"]
        .apply(_rotulo_operador)
        .to_dict()
    )

    df["operador_exibicao"] = (
        df["op_key"]
        .map(mapa_operadores)
        .fillna("Não informado")
    )

    df["cliente_exibicao"] = df["cliente_nome"].replace(
        "",
        "Não informado",
    )

    return df


# ============================================================
# CSS — DESIGN SYSTEM DUARTE
# ============================================================

def _injetar_css() -> None:
    st.markdown(
        """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

@keyframes duarteRise {
    from {
        opacity: 0;
        transform: translateY(14px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

@keyframes duarteBorderFlow {
    0%, 100% {
        background-position: 50% 0%;
    }

    50% {
        background-position: 50% 100%;
    }
}

@keyframes duarteHeroGlow {
    0%, 100% {
        opacity: .35;
        transform: translate3d(0, 0, 0);
    }

    50% {
        opacity: .70;
        transform: translate3d(-24px, 8px, 0);
    }
}

@keyframes duarteCardShine {
    from {
        transform: translateX(-180%) skewX(-22deg);
    }

    to {
        transform: translateX(340%) skewX(-22deg);
    }
}

@keyframes duarteProgressReveal {
    from {
        transform: scaleX(0);
    }

    to {
        transform: scaleX(1);
    }
}

@keyframes duarteValueArrival {
    from {
        opacity: .72;
        transform: translateY(5px);
    }

    to {
        opacity: 1;
        transform: translateY(0);
    }
}

.dash-hero,
.dash-kpi,
.dash-section,
.dash-insight,
.dash-chart-title {
    font-family: Inter, system-ui, -apple-system, sans-serif;
    -webkit-font-smoothing: antialiased;
}

/* CABEÇALHO */

.dash-hero {
    position: relative;
    isolation: isolate;
    overflow: hidden;

    min-height: 218px;
    padding: clamp(24px, 3vw, 36px);
    margin-bottom: 24px;

    border: 1px solid rgba(255,255,255,.10);
    border-radius: 19px;

    background:
        radial-gradient(
            circle at 78% 105%,
            rgba(255,146,0,.11),
            transparent 37%
        ),
        linear-gradient(
            108deg,
            #09162F 0%,
            #101E3D 51%,
            #242329 100%
        );

    box-shadow:
        0 22px 42px rgba(0,30,87,.14),
        0 7px 16px rgba(0,30,87,.08);

    color: #FFFFFF;
    animation: duarteRise .55s ease-out both;
}

.dash-hero::before {
    content: "";

    position: absolute;
    z-index: 2;
    top: 0;
    bottom: 0;
    left: 0;

    width: 4px;

    background: linear-gradient(
        180deg,
        #E67900 0%,
        #FF9200 26%,
        #FFE2B0 48%,
        #FF9200 69%,
        #D96C00 100%
    );

    background-size: 100% 300%;

    box-shadow:
        0 0 14px rgba(255,146,0,.65),
        3px 0 22px rgba(255,146,0,.20);

    animation: duarteBorderFlow 4.5s ease-in-out infinite;
}

.dash-hero::after {
    content: "";

    position: absolute;
    z-index: -1;

    width: 310px;
    height: 310px;

    right: -95px;
    top: -135px;

    border-radius: 50%;

    background: radial-gradient(
        circle,
        rgba(255,146,0,.15) 0%,
        rgba(255,146,0,.06) 37%,
        transparent 72%
    );

    pointer-events: none;
    animation: duarteHeroGlow 9s ease-in-out infinite;
}

.dash-hero__eyebrow {
    display: inline-flex;
    align-items: center;
    gap: 9px;

    color: #FFC373;

    font-size: .68rem;
    font-weight: 850;
    letter-spacing: .15em;
    text-transform: uppercase;
}

.dash-hero__eyebrow::before {
    content: "";

    width: 17px;
    height: 2px;

    border-radius: 99px;
    background: #FF9200;
}

.dash-hero h1 {
    margin: 18px 0 10px;

    color: #FFFFFF;

    font-size: clamp(1.7rem, 2.8vw, 2.45rem);
    font-weight: 900;
    letter-spacing: -.05em;
    line-height: 1.13;
}

.dash-hero p {
    max-width: 710px;
    margin: 0;

    color: #CFD7E6;

    font-size: .90rem;
    line-height: 1.65;
}

.dash-hero__footer {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    gap: 9px;

    margin-top: 21px;
}

.dash-hero__tag {
    display: inline-flex;
    align-items: center;

    min-height: 29px;
    padding: 5px 11px;

    border: 1px solid rgba(255,255,255,.16);
    border-radius: 999px;

    background: rgba(255,255,255,.07);
    backdrop-filter: blur(8px);

    color: #F8FAFC;

    font-size: .67rem;
    font-weight: 750;
}

.dash-hero__tag--orange {
    border-color: rgba(255,146,0,.35);
    background: rgba(255,146,0,.13);
    color: #FFD29A;
}

/* TÍTULOS DE SEÇÃO */

.dash-section {
    display: flex;
    align-items: center;
    gap: 10px;

    margin: 22px 0 13px;

    color: #001E57;

    font-size: 1rem;
    font-weight: 850;
    letter-spacing: -.025em;
}

.dash-section::before {
    content: "";

    width: 4px;
    height: 20px;
    flex: 0 0 4px;

    border-radius: 99px;
    background: #FF9200;
}

.dash-section__detail {
    margin-left: auto;

    color: #64748B;

    font-size: .70rem;
    font-weight: 600;
    letter-spacing: 0;
}

/* CARDS DE KPI */

.dash-kpi {
    position: relative;
    isolation: isolate;
    overflow: hidden;

    height: 100%;
    min-height: 165px;

    padding: 20px 16px 17px;

    border: 1px solid #E2E8F0;
    border-top: 3px solid var(--kpi-accent, #001E57);
    border-radius: 17px;

    background:
        radial-gradient(
            circle at 100% 0%,
            var(--kpi-wash, rgba(0,30,87,.045)),
            transparent 44%
        ),
        linear-gradient(
            155deg,
            #FFFFFF 0%,
            #FBFCFF 100%
        );

    box-shadow:
        0 10px 25px rgba(0,30,87,.06),
        0 1px 3px rgba(0,30,87,.035);

    animation: duarteRise .52s ease-out both;

    transition:
        transform .25s ease,
        box-shadow .25s ease,
        border-color .25s ease;
}

.dash-kpi:hover {
    transform: translateY(-5px);

    border-color: rgba(255,146,0,.48);
    border-top-color: var(--kpi-accent, #001E57);

    box-shadow:
        0 19px 37px rgba(0,30,87,.12),
        0 5px 12px rgba(255,146,0,.055);
}

.dash-kpi::after {
    content: "";

    position: absolute;
    z-index: -1;

    top: -35%;
    left: -30%;

    width: 36%;
    height: 180%;

    background: linear-gradient(
        90deg,
        transparent,
        rgba(255,255,255,.85),
        transparent
    );

    transform: translateX(-180%) skewX(-22deg);
    pointer-events: none;
}

.dash-kpi:hover::after {
    animation: duarteCardShine .85s ease-out 1;
}

.dash-kpi__top {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 8px;

    margin-bottom: 16px;
}

.dash-kpi__label {
    margin: 0;

    color: #52637C;

    font-size: .65rem;
    font-weight: 850;
    letter-spacing: .065em;
    line-height: 1.3;
    text-transform: uppercase;
}

.dash-kpi__symbol {
    display: inline-flex;
    align-items: center;
    justify-content: center;

    width: 26px;
    height: 26px;
    flex: 0 0 26px;

    border: 1px solid rgba(0,30,87,.10);
    border-radius: 9px;

    background: var(--kpi-wash, rgba(0,30,87,.05));

    color: var(--kpi-accent, #001E57);

    font-size: .77rem;
    font-weight: 900;
    font-style: normal;
}

.dash-kpi__value {
    min-height: 36px;
    margin: 0;

    color: var(--kpi-accent, #001E57);

    font-size: clamp(1.63rem, 2.15vw, 2rem);
    font-weight: 900;
    letter-spacing: -.065em;
    line-height: 1.1;

    font-variant-numeric: tabular-nums;
    white-space: nowrap;
}

.dash-kpi__value.is-animating {
    animation: duarteValueArrival .36s ease-out both;
}

.dash-kpi__detail {
    min-height: 27px;
    margin-top: 7px;

    color: #64748B;

    font-size: .68rem;
    font-weight: 600;
    line-height: 1.4;
}

.dash-kpi__track {
    height: 5px;
    margin-top: 11px;

    overflow: hidden;

    border-radius: 99px;
    background: #EAF0F7;
}

.dash-kpi__fill {
    width: var(--kpi-progress, 0%);
    height: 100%;

    border-radius: inherit;

    background: linear-gradient(
        90deg,
        var(--kpi-accent, #001E57),
        var(--kpi-accent-end, #0B296B)
    );

    transform-origin: left center;

    box-shadow: 0 0 10px var(--kpi-glow, rgba(0,30,87,.20));
    animation: duarteProgressReveal .9s ease-out both;
}

/* INSIGHTS E TÍTULOS DOS GRÁFICOS */

.dash-insight {
    padding: 13px 15px;
    margin-bottom: 9px;

    border: 1px solid #FED7AA;
    border-left: 4px solid #FF9200;
    border-radius: 13px;

    background: linear-gradient(
        110deg,
        #FFF9F0 0%,
        #FFFFFF 100%
    );

    color: #7C2D12;

    font-size: .82rem;
    line-height: 1.55;

    animation: duarteRise .45s ease-out both;
}

.dash-insight strong {
    color: #001E57;
}

.dash-chart-title {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 10px;

    padding-bottom: 12px;
    margin-bottom: 7px;

    border-bottom: 1px solid #F1F5F9;

    color: #001E57;

    font-size: .92rem;
    font-weight: 850;
}

.dash-chart-title__mark {
    width: 9px;
    height: 9px;
    flex: 0 0 9px;

    border-radius: 3px;
    background: #FF9200;

    box-shadow: 0 0 0 4px rgba(255,146,0,.13);
}

.dash-chart-title__badge {
    margin-left: auto;
    padding: 4px 9px;

    border-radius: 999px;
    background: #FFF3E3;

    color: #9A4B00;

    font-size: .63rem;
    font-weight: 850;
}

/* STREAMLIT: APENAS COMPONENTES DO DASHBOARD */

.st-key-dash_filtros [data-testid="stVerticalBlockBorderWrapper"],
.st-key-dash_grafico_status [data-testid="stVerticalBlockBorderWrapper"],
.st-key-dash_grafico_ranking [data-testid="stVerticalBlockBorderWrapper"],
.st-key-dash_grafico_operadores [data-testid="stVerticalBlockBorderWrapper"],
.st-key-dash_grafico_clientes [data-testid="stVerticalBlockBorderWrapper"],
.st-key-dash_grafico_evolucao [data-testid="stVerticalBlockBorderWrapper"] {
    border: 1px solid #E2E8F0 !important;
    border-radius: 18px !important;

    background: #FFFFFF !important;

    box-shadow:
        0 9px 24px rgba(0,30,87,.05) !important;
}

.st-key-dash_filtros [data-testid="stVerticalBlockBorderWrapper"] {
    border-top: 3px solid #FF9200 !important;
}

.st-key-dash_filtros label {
    color: #001E57 !important;
    font-weight: 700 !important;
}

.st-key-dash_filtros [data-baseweb="select"] > div {
    border-radius: 10px !important;
}

.st-key-dash_atualizar button {
    border: 1px solid #001E57 !important;
    border-radius: 10px !important;

    background: #FFFFFF !important;
    color: #001E57 !important;

    font-weight: 800 !important;

    transition:
        transform .2s ease,
        border-color .2s ease,
        background .2s ease !important;
}

.st-key-dash_atualizar button:hover {
    transform: translateY(-2px);

    border-color: #FF9200 !important;
    background: #FFF7ED !important;
}

@media (max-width: 768px) {
    .dash-hero {
        min-height: auto;
        padding: 24px 21px;
    }

    .dash-kpi {
        min-height: 147px;
    }

    .dash-section__detail {
        display: none;
    }
}

@media (prefers-reduced-motion: reduce) {
    .dash-hero,
    .dash-hero::before,
    .dash-hero::after,
    .dash-kpi,
    .dash-kpi::after,
    .dash-kpi__fill,
    .dash-kpi__value,
    .dash-insight {
        animation: none !important;
    }

    .dash-kpi,
    .st-key-dash_atualizar button {
        transition: none !important;
    }
}
</style>
        """,
        unsafe_allow_html=True,
    )


def _secao(titulo: str, detalhe: str = "") -> None:
    detalhe_html = ""

    if detalhe:
        detalhe_html = (
            '<span class="dash-section__detail">'
            f"{html.escape(detalhe)}"
            "</span>"
        )

    _render_html(
        f"""
        <div class="dash-section">
            <span>{html.escape(titulo)}</span>
            {detalhe_html}
        </div>
        """
    )


def _render_cabecalho() -> None:
    atualizado = _agora_br().strftime("%d/%m/%Y às %H:%M")

    _render_html(
        f"""
        <div class="dash-hero">
            <div class="dash-hero__eyebrow">
                Duarte Gestão em Saúde
            </div>

            <h1>Dashboard Gerencial</h1>

            <p>
                Visão consolidada das execuções operacionais,
                do desempenho da equipe e dos pontos que exigem atenção.
            </p>

            <div class="dash-hero__footer">
                <span class="dash-hero__tag dash-hero__tag--orange">
                    DUARTE PERFORMANCE
                </span>

                <span class="dash-hero__tag">
                    Consulta realizada em {html.escape(atualizado)}
                </span>
            </div>
        </div>
        """
    )


@contextmanager
def _card_grafico(
    titulo: str,
    badge: Optional[str] = None,
    key: Optional[str] = None,
):
    with st.container(border=True, key=key):
        badge_html = ""

        if badge:
            badge_html = (
                '<span class="dash-chart-title__badge">'
                f"{html.escape(badge)}"
                "</span>"
            )

        _render_html(
            f"""
            <div class="dash-chart-title">
                <span class="dash-chart-title__mark"></span>
                <span>{html.escape(titulo)}</span>
                {badge_html}
            </div>
            """
        )

        yield


def _layout_grafico(
    figura: go.Figure,
    altura: int = 350,
    margem_inferior: int = 44,
) -> go.Figure:
    figura.update_layout(
        height=altura,
        margin=dict(
            l=12,
            r=20,
            t=20,
            b=margem_inferior,
        ),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(
            family="Inter, system-ui, sans-serif",
            color=TEXTO,
            size=12,
        ),
        hoverlabel=dict(
            bgcolor=AZUL,
            bordercolor=LARANJA,
            font=dict(
                color="#FFFFFF",
                size=12,
                family="Inter, sans-serif",
            ),
        ),
        legend=dict(
            orientation="h",
            yanchor="top",
            y=-0.18,
            xanchor="center",
            x=0.5,
            font=dict(
                size=11,
                color=TEXTO_SECUNDARIO,
            ),
        ),
        xaxis=dict(
            showline=False,
            zeroline=False,
            showgrid=False,
            tickfont=dict(
                color=TEXTO_SECUNDARIO,
            ),
        ),
        yaxis=dict(
            showline=False,
            zeroline=False,
            gridcolor="#F1F5F9",
            tickfont=dict(
                color=TEXTO_SECUNDARIO,
            ),
        ),
    )

    return figura


# ============================================================
# FILTROS
# ============================================================

def _opcoes_texto(serie: pd.Series) -> list[str]:
    valores = {
        _texto(valor)
        for valor in serie
        if _texto(valor)
    }

    return [
        "Todos",
        *sorted(valores, key=str.casefold),
    ]


def _selectbox_seguro(
    titulo: str,
    opcoes: list[str],
    key: str,
) -> str:
    if st.session_state.get(key) not in opcoes:
        st.session_state[key] = "Todos"

    return st.selectbox(
        titulo,
        opcoes,
        key=key,
    )


def _render_filtros(df: pd.DataFrame) -> pd.DataFrame:
    _secao(
        "Filtros de pesquisa",
        "Todos os indicadores seguem a seleção abaixo",
    )

    with st.container(border=True, key="dash_filtros"):
        (
            col_periodo,
            col_operador,
            col_status,
            col_cliente,
        ) = st.columns(
            [1.15, 1.25, 1.2, 1.45],
            gap="medium",
        )

        with col_periodo:
            periodos = [
                "Hoje",
                "Últimos 7 dias",
                "Últimos 30 dias",
                "Este mês",
                "Todos",
            ]

            if st.session_state.get("dash_periodo") not in periodos:
                st.session_state["dash_periodo"] = "Todos"

            periodo = st.selectbox(
                "Período",
                periodos,
                key="dash_periodo",
            )

        df_periodo = df

        if periodo != "Todos":
            datas = df["data_registro"]
            hoje = _agora_br().date()
            dias = datas.dt.date

            if periodo == "Hoje":
                mascara = dias.eq(hoje)

            elif periodo == "Últimos 7 dias":
                mascara = (
                    dias.ge(hoje - timedelta(days=6))
                    & dias.le(hoje)
                )

            elif periodo == "Últimos 30 dias":
                mascara = (
                    dias.ge(hoje - timedelta(days=29))
                    & dias.le(hoje)
                )

            else:
                mascara = (
                    datas.dt.year.eq(hoje.year)
                    & datas.dt.month.eq(hoje.month)
                )

            df_periodo = df.loc[
                mascara.fillna(False)
            ].copy()

        with col_operador:
            operador = _selectbox_seguro(
                "Operador",
                _opcoes_texto(
                    df_periodo["operador_exibicao"]
                ),
                "dash_op",
            )

        with col_status:
            status = _selectbox_seguro(
                "Status",
                _opcoes_texto(
                    df_periodo["status"]
                ),
                "dash_status",
            )

        with col_cliente:
            cliente = _selectbox_seguro(
                "Cliente",
                _opcoes_texto(
                    df_periodo["cliente_exibicao"]
                ),
                "dash_cliente",
            )

        col_info, col_acao = st.columns([3, 1])

        with col_info:
            st.caption(
                "A consulta é feita ao abrir ou atualizar o dashboard. "
                "Os filtros reorganizam os dados carregados."
            )

        with col_acao:
            if st.button(
                "Atualizar dados",
                key="dash_atualizar",
                use_container_width=True,
            ):
                st.rerun()

    resultado = df_periodo

    if operador != "Todos":
        resultado = resultado.loc[
            resultado["operador_exibicao"].eq(operador)
        ]

    if status != "Todos":
        resultado = resultado.loc[
            resultado["status"].eq(status)
        ]

    if cliente != "Todos":
        resultado = resultado.loc[
            resultado["cliente_exibicao"].eq(cliente)
        ]

    return resultado.copy()


# ============================================================
# INDICADORES E ANIMAÇÃO
# ============================================================

def _calcular_kpis(
    df: pd.DataFrame,
) -> dict[str, float | int]:
    total = len(df)
    contagens = df["status"].value_counts()

    realizados = int(
        contagens.get("Realizado Total", 0)
    )

    parciais = int(
        contagens.get("Realizado Parcial", 0)
    )

    nao_realizados = int(
        contagens.get("Não Realizado", 0)
    )

    eficiencia = (
        round(100 * realizados / total, 1)
        if total
        else 0.0
    )

    return {
        "total": total,
        "realizados": realizados,
        "parciais": parciais,
        "nao_realizados": nao_realizados,
        "eficiencia": eficiencia,
    }


def _formatar_numero(valor: int | float) -> str:
    if isinstance(valor, float):
        return (
            f"{valor:,.1f}"
            .replace(",", "_")
            .replace(".", ",")
            .replace("_", ".")
        )

    return f"{valor:,}".replace(",", ".")


def _card_kpi(
    identificador: str,
    titulo: str,
    valor: int | float,
    descricao: str,
    simbolo: str,
    cor: str,
    cor_final: str,
    fundo: str,
    brilho: str,
    progresso: float,
    percentual: bool = False,
) -> str:
    progresso = max(
        0.0,
        min(float(progresso), 100.0),
    )

    numero_formatado = _formatar_numero(valor)

    if percentual:
        numero_formatado += "%"

    return f"""
        <div
            class="dash-kpi"
            style="
                --kpi-accent:{cor};
                --kpi-accent-end:{cor_final};
                --kpi-wash:{fundo};
                --kpi-glow:{brilho};
                --kpi-progress:{progresso:.1f}%;
            "
        >
            <div class="dash-kpi__top">
                <div class="dash-kpi__label">
                    {html.escape(titulo)}
                </div>

                <span
                    class="dash-kpi__symbol"
                    aria-hidden="true"
                >
                    {html.escape(simbolo)}
                </span>
            </div>

            <div
                class="dash-kpi__value"
                data-duarte-kpi="{html.escape(identificador)}"
            >
                {html.escape(numero_formatado)}
            </div>

            <div class="dash-kpi__detail">
                {html.escape(descricao)}
            </div>

            <div
                class="dash-kpi__track"
                aria-hidden="true"
            >
                <div class="dash-kpi__fill"></div>
            </div>
        </div>
    """


def _animar_numeros_kpi(
    anteriores: Optional[dict[str, float]],
    atuais: dict[str, float],
) -> None:
    """
    Anima apenas mudanças entre duas renderizações da mesma sessão.

    Os valores finais já estão no HTML: se o JavaScript não executar,
    o dashboard continua mostrando números corretos.
    """
    if anteriores is None:
        return

    if anteriores == atuais:
        return

    payload = json.dumps(
        {
            "anteriores": anteriores,
            "atuais": atuais,
        },
        ensure_ascii=False,
    )

    components.html(
        f"""
<script>
(function () {{
    const dados = {payload};

    let doc;

    try {{
        doc = window.parent.document;
    }} catch (erro) {{
        return;
    }}

    if (!doc) {{
        return;
    }}

    const reduzirMovimento = window.matchMedia(
        "(prefers-reduced-motion: reduce)"
    ).matches;

    if (reduzirMovimento) {{
        return;
    }}

    const inteiro = new Intl.NumberFormat("pt-BR", {{
        maximumFractionDigits: 0
    }});

    const decimal = new Intl.NumberFormat("pt-BR", {{
        minimumFractionDigits: 1,
        maximumFractionDigits: 1
    }});

    function formatar(valor, percentual) {{
        if (percentual) {{
            return decimal.format(valor) + "%";
        }}

        return inteiro.format(Math.round(valor));
    }}

    function executar() {{
        for (const [chave, alvo] of Object.entries(dados.atuais)) {{
            const origem = dados.anteriores[chave];

            if (
                typeof origem !== "number" ||
                typeof alvo !== "number" ||
                origem === alvo
            ) {{
                continue;
            }}

            const elemento = doc.querySelector(
                '[data-duarte-kpi="' + chave + '"]'
            );

            if (!elemento) {{
                continue;
            }}

            const percentual = chave === "eficiencia";
            const inicio = performance.now();
            const duracao = 780;

            elemento.classList.add("is-animating");

            function quadro(agora) {{
                if (!elemento.isConnected) {{
                    return;
                }}

                const progresso = Math.min(
                    (agora - inicio) / duracao,
                    1
                );

                const suavizado =
                    1 - Math.pow(1 - progresso, 3);

                const valor =
                    origem + (alvo - origem) * suavizado;

                elemento.textContent = formatar(
                    valor,
                    percentual
                );

                if (progresso < 1) {{
                    requestAnimationFrame(quadro);
                }} else {{
                    elemento.textContent = formatar(
                        alvo,
                        percentual
                    );

                    elemento.classList.remove(
                        "is-animating"
                    );
                }}
            }}

            requestAnimationFrame(quadro);
        }}
    }}

    window.setTimeout(executar, 80);
}})();
</script>
        """,
        height=0,
    )


def _render_kpis(
    kpis: dict[str, float | int],
) -> None:
    _secao(
        "Indicadores principais",
        "Base: registros filtrados",
    )

    total = int(kpis["total"])
    realizados = int(kpis["realizados"])
    parciais = int(kpis["parciais"])
    nao_realizados = int(kpis["nao_realizados"])
    eficiencia = float(kpis["eficiencia"])

    def pct(quantidade: int) -> float:
        return (
            100 * quantidade / total
            if total
            else 0.0
        )

    especificacoes = [
        (
            "total",
            "Lançamentos",
            total,
            "Volume no período selecionado",
            "Σ",
            AZUL,
            AZUL_MEDIO,
            "rgba(0,30,87,.055)",
            "rgba(0,30,87,.25)",
            100.0,
            False,
        ),
        (
            "realizados",
            "Realizados",
            realizados,
            (
                f"{_formatar_numero(round(pct(realizados), 1))}% "
                "do total"
            ),
            "✓",
            VERDE,
            "#34D399",
            "rgba(16,185,129,.075)",
            "rgba(16,185,129,.30)",
            pct(realizados),
            False,
        ),
        (
            "parciais",
            "Parciais",
            parciais,
            (
                f"{_formatar_numero(round(pct(parciais), 1))}% "
                "do total"
            ),
            "½",
            AMARELO,
            "#FBBF24",
            "rgba(245,158,11,.075)",
            "rgba(245,158,11,.30)",
            pct(parciais),
            False,
        ),
        (
            "nao_realizados",
            "Não realizados",
            nao_realizados,
            (
                f"{_formatar_numero(round(pct(nao_realizados), 1))}% "
                "do total"
            ),
            "×",
            VERMELHO,
            "#FB7185",
            "rgba(239,68,68,.070)",
            "rgba(239,68,68,.28)",
            pct(nao_realizados),
            False,
        ),
        (
            "eficiencia",
            "Eficiência",
            eficiencia,
            "Realizado Total / lançamentos",
            "%",
            LARANJA,
            LARANJA_CLARO,
            "rgba(255,146,0,.095)",
            "rgba(255,146,0,.32)",
            eficiencia,
            True,
        ),
    ]

    colunas = st.columns(5, gap="small")

    for coluna, dados in zip(colunas, especificacoes):
        with coluna:
            _render_html(
                _card_kpi(*dados)
            )

    atuais = {
        "total": float(total),
        "realizados": float(realizados),
        "parciais": float(parciais),
        "nao_realizados": float(nao_realizados),
        "eficiencia": eficiencia,
    }

    anteriores = st.session_state.get(
        "_dash_kpis_anteriores"
    )

    _animar_numeros_kpi(
        anteriores,
        atuais,
    )

    st.session_state["_dash_kpis_anteriores"] = atuais


# ============================================================
# INSIGHTS
# ============================================================

def _resumo_operadores(
    df: pd.DataFrame,
) -> pd.DataFrame:
    base = df.assign(
        _realizado=df["status"]
        .eq("Realizado Total")
        .astype(int)
    )

    resumo = (
        base.groupby(
            "operador_exibicao",
            dropna=False,
        )
        .agg(
            total=("status", "size"),
            realizados=("_realizado", "sum"),
        )
        .reset_index()
    )

    resumo["eficiencia"] = (
        resumo["realizados"]
        .div(resumo["total"])
        .mul(100)
        .round(1)
    )

    return resumo


def _render_insights(
    df: pd.DataFrame,
    kpis: dict[str, float | int],
) -> None:
    total = int(kpis["total"])

    if not total:
        return

    mensagens: list[str] = []

    resumo = _resumo_operadores(df)

    elegiveis = resumo.loc[
        resumo["total"].ge(3)
    ]

    if not elegiveis.empty:
        melhor = elegiveis.sort_values(
            [
                "eficiencia",
                "total",
                "operador_exibicao",
            ],
            ascending=[
                False,
                False,
                True,
            ],
        ).iloc[0]

        if float(melhor["eficiencia"]) >= 80:
            nome = html.escape(
                str(melhor["operador_exibicao"])
            )

            valor_eficiencia = _formatar_numero(
                float(melhor["eficiencia"])
            )

            mensagens.append(
                f"<strong>{nome}</strong> apresenta a maior "
                "eficiência entre operadores com pelo menos "
                "3 lançamentos: "
                f"<strong>{valor_eficiencia}%</strong> em "
                f"{int(melhor['total'])} registros."
            )

    ocorrencias = (
        int(kpis["parciais"])
        + int(kpis["nao_realizados"])
    )

    taxa_ocorrencias = (
        100 * ocorrencias / total
    )

    if taxa_ocorrencias > 35:
        taxa = _formatar_numero(
            round(taxa_ocorrencias, 1)
        )

        mensagens.append(
            "A participação de lançamentos parciais "
            "ou não realizados chegou a "
            f"<strong>{taxa}%</strong> "
            "no recorte atual."
        )

    if not mensagens:
        return

    _secao("Pontos de atenção")

    for mensagem in mensagens[:2]:
        _render_html(
            f'<div class="dash-insight">{mensagem}</div>'
        )


# ============================================================
# GRÁFICOS
# ============================================================

def _render_status(
    df: pd.DataFrame,
    eficiencia: float,
) -> None:
    with _card_grafico(
        "Distribuição por status",
        "COMPOSIÇÃO",
        "dash_grafico_status",
    ):
        contagem = (
            df["status"]
            .value_counts()
            .rename_axis("status")
            .reset_index(name="quantidade")
        )

        ordem = [
            status
            for status in STATUS_ORDEM
            if status in contagem["status"].values
        ]

        ordem += [
            status
            for status in contagem["status"].tolist()
            if status not in ordem
        ]

        figura = px.pie(
            contagem,
            names="status",
            values="quantidade",
            color="status",
            color_discrete_map=CORES_STATUS,
            category_orders={
                "status": ordem
            },
            hole=0.69,
        )

        figura.update_traces(
            sort=False,
            textinfo="percent",
            textposition="inside",
            textfont=dict(
                size=12,
                color="#FFFFFF",
            ),
            marker=dict(
                line=dict(
                    color="#FFFFFF",
                    width=3,
                )
            ),
            hovertemplate=(
                "<b>%{label}</b><br>"
                "%{value} lançamentos · %{percent}"
                "<extra></extra>"
            ),
        )

        figura.add_annotation(
            x=0.5,
            y=0.5,
            showarrow=False,
            align="center",
            text=(
                f"<b>{_formatar_numero(eficiencia)}%</b>"
                "<br>"
                "<span style='font-size:11px'>"
                "EFICIÊNCIA"
                "</span>"
            ),
            font=dict(
                family="Inter, sans-serif",
                color=AZUL,
                size=22,
            ),
        )

        _layout_grafico(
            figura,
            altura=365,
            margem_inferior=70,
        )

        st.plotly_chart(
            figura,
            use_container_width=True,
            config=CONFIG_GRAFICO,
        )


def _render_ranking(
    df: pd.DataFrame,
) -> None:
    with _card_grafico(
        "Eficiência por operador",
        "RANKING",
        "dash_grafico_ranking",
    ):
        resumo = _resumo_operadores(df)

        if resumo.empty:
            st.info(
                "Sem operadores para apresentar."
            )
            return

        resumo = resumo.sort_values(
            [
                "eficiencia",
                "total",
                "operador_exibicao",
            ],
            ascending=[
                True,
                True,
                True,
            ],
        )

        altura = max(
            365,
            min(
                850,
                75 + len(resumo) * 37,
            ),
        )

        figura = px.bar(
            resumo,
            x="eficiencia",
            y="operador_exibicao",
            orientation="h",
            color="eficiencia",
            color_continuous_scale=ESCALA_EFICIENCIA,
            range_color=(0, 100),
            text="eficiencia",
            custom_data=["total"],
        )

        figura.update_traces(
            marker_line_width=0,
            texttemplate="%{text:.1f}%",
            textposition="outside",
            cliponaxis=False,
            hovertemplate=(
                "<b>%{y}</b><br>"
                "Eficiência: %{x:.1f}%<br>"
                "Lançamentos: %{customdata[0]}"
                "<extra></extra>"
            ),
        )

        figura.update_layout(
            coloraxis_showscale=False,
            bargap=0.35,
        )

        _layout_grafico(
            figura,
            altura=altura,
            margem_inferior=45,
        )

        figura.update_xaxes(
            title="Eficiência (%)",
            range=[0, 115],
            gridcolor="#F1F5F9",
            showgrid=True,
        )

        figura.update_yaxes(title="")

        st.plotly_chart(
            figura,
            use_container_width=True,
            config=CONFIG_GRAFICO,
        )


def _render_volume_operadores(
    df: pd.DataFrame,
) -> None:
    with _card_grafico(
        "Volume e status por operador",
        "EQUIPE",
        "dash_grafico_operadores",
    ):
        resumo = (
            df.groupby(
                [
                    "operador_exibicao",
                    "status",
                ],
                dropna=False,
            )
            .size()
            .reset_index(name="quantidade")
        )

        if resumo.empty:
            st.info(
                "Sem dados para o comparativo."
            )
            return

        ordem_operadores = (
            df["operador_exibicao"]
            .value_counts()
            .index
            .tolist()
        )

        figura = px.bar(
            resumo,
            x="operador_exibicao",
            y="quantidade",
            color="status",
            color_discrete_map=CORES_STATUS,
            category_orders={
                "operador_exibicao": ordem_operadores,
                "status": STATUS_ORDEM,
            },
            barmode="stack",
        )

        figura.update_traces(
            hovertemplate=(
                "<b>%{x}</b><br>"
                "%{fullData.name}: %{y}"
                "<extra></extra>"
            ),
        )

        _layout_grafico(
            figura,
            altura=390,
            margem_inferior=85,
        )

        figura.update_layout(
            bargap=0.38,
            legend_title_text="",
        )

        figura.update_xaxes(
            title="",
            tickangle=-20,
        )

        figura.update_yaxes(
            title="Lançamentos",
            rangemode="tozero",
        )

        st.plotly_chart(
            figura,
            use_container_width=True,
            config=CONFIG_GRAFICO,
        )


def _render_clientes(
    df: pd.DataFrame,
) -> None:
    with _card_grafico(
        "Clientes com maior volume",
        "TOP 10",
        "dash_grafico_clientes",
    ):
        base = df.assign(
            _realizado=df["status"]
            .eq("Realizado Total")
            .astype(int)
        )

        clientes = (
            base.groupby(
                "cliente_exibicao",
                dropna=False,
            )
            .agg(
                total=("status", "size"),
                realizados=(
                    "_realizado",
                    "sum",
                ),
            )
            .reset_index()
        )

        clientes["eficiencia"] = (
            clientes["realizados"]
            .div(clientes["total"])
            .mul(100)
            .round(1)
        )

        clientes = clientes.sort_values(
            [
                "total",
                "cliente_exibicao",
            ],
            ascending=[
                False,
                True,
            ],
        ).head(10)

        if clientes.empty:
            st.info(
                "Sem dados de clientes."
            )
            return

        figura = px.bar(
            clientes,
            x="cliente_exibicao",
            y="total",
            color="eficiencia",
            color_continuous_scale=ESCALA_EFICIENCIA,
            range_color=(0, 100),
            text="total",
            custom_data=["eficiencia"],
        )

        figura.update_traces(
            textposition="outside",
            cliponaxis=False,
            marker_line_width=0,
            hovertemplate=(
                "<b>%{x}</b><br>"
                "Lançamentos: %{y}<br>"
                "Eficiência: %{customdata[0]:.1f}%"
                "<extra></extra>"
            ),
        )

        _layout_grafico(
            figura,
            altura=380,
            margem_inferior=90,
        )

        figura.update_layout(
            bargap=0.38,
            coloraxis_colorbar=dict(
                title="Eficiência",
                ticksuffix="%",
                thickness=11,
                len=0.72,
            ),
        )

        figura.update_xaxes(
            title="",
            tickangle=-22,
        )

        figura.update_yaxes(
            title="Lançamentos",
            rangemode="tozero",
        )

        st.plotly_chart(
            figura,
            use_container_width=True,
            config=CONFIG_GRAFICO,
        )


def _render_evolucao(
    df: pd.DataFrame,
) -> None:
    with _card_grafico(
        "Evolução das execuções",
        "POR DIA",
        "dash_grafico_evolucao",
    ):
        base = df.dropna(
            subset=["data_registro"]
        ).copy()

        if base.empty:
            st.info(
                "Não há datas válidas para gerar a evolução."
            )
            return

        base["dia"] = (
            base["data_registro"]
            .dt.normalize()
        )

        base["_realizado"] = (
            base["status"]
            .eq("Realizado Total")
            .astype(int)
        )

        serie = (
            base.groupby("dia")
            .agg(
                total=("status", "size"),
                realizados=(
                    "_realizado",
                    "sum",
                ),
            )
            .reset_index()
            .sort_values("dia")
        )

        serie["eficiencia"] = (
            serie["realizados"]
            .div(serie["total"])
            .mul(100)
            .round(1)
        )

        figura = go.Figure()

        figura.add_trace(
            go.Scatter(
                x=serie["dia"],
                y=serie["total"],
                name="Volume",
                mode="lines+markers",
                line=dict(
                    color=AZUL,
                    width=3,
                    shape="linear",
                ),
                marker=dict(
                    color=LARANJA,
                    size=8,
                    line=dict(
                        color="#FFFFFF",
                        width=1.5,
                    ),
                ),
                fill="tozeroy",
                fillcolor="rgba(0,30,87,.055)",
                hovertemplate=(
                    "Volume: %{y}"
                    "<extra></extra>"
                ),
            )
        )

        figura.add_trace(
            go.Scatter(
                x=serie["dia"],
                y=serie["eficiencia"],
                name="Eficiência",
                mode="lines+markers",
                yaxis="y2",
                line=dict(
                    color=VERDE,
                    width=2.5,
                    dash="dot",
                ),
                marker=dict(size=7),
                hovertemplate=(
                    "Eficiência: %{y:.1f}%"
                    "<extra></extra>"
                ),
            )
        )

        _layout_grafico(
            figura,
            altura=370,
            margem_inferior=65,
        )

        figura.update_layout(
            hovermode="x unified",
            xaxis=dict(
                title="",
                tickformat="%d/%m/%Y",
            ),
            yaxis=dict(
                title="Lançamentos",
                gridcolor="#F1F5F9",
                rangemode="tozero",
            ),
            yaxis2=dict(
                title="Eficiência (%)",
                overlaying="y",
                side="right",
                range=[0, 105],
                showgrid=False,
                ticksuffix="%",
            ),
        )

        st.plotly_chart(
            figura,
            use_container_width=True,
            config=CONFIG_GRAFICO,
        )


def _render_graficos(
    df: pd.DataFrame,
    eficiencia: float,
) -> None:
    _secao("Análise visual")

    coluna_1, coluna_2 = st.columns(
        2,
        gap="medium",
    )

    with coluna_1:
        _render_status(
            df,
            eficiencia,
        )

    with coluna_2:
        _render_ranking(df)

    _render_volume_operadores(df)
    _render_clientes(df)
    _render_evolucao(df)


# ============================================================
# TABELA
# ============================================================

def _render_tabela(
    df: pd.DataFrame,
) -> None:
    _secao(
        "Lançamentos registrados",
        "50 registros mais recentes do recorte",
    )

    colunas = [
        "data_registro",
        "operador_nome",
        "cliente_nome",
        "status",
        "justificativa",
    ]

    tabela = (
        df[colunas]
        .sort_values(
            "data_registro",
            ascending=False,
            na_position="last",
            kind="stable",
        )
        .head(50)
        .copy()
    )

    tabela["data_registro"] = (
        tabela["data_registro"]
        .dt.strftime("%d/%m/%Y %H:%M")
        .fillna("Data não informada")
    )

    for coluna in (
        "operador_nome",
        "cliente_nome",
        "justificativa",
    ):
        tabela[coluna] = tabela[coluna].replace(
            "",
            "—",
        )

    tabela = tabela.rename(
        columns={
            "data_registro": "Data",
            "operador_nome": "Operador",
            "cliente_nome": "Cliente",
            "status": "Status",
            "justificativa": "Justificativa",
        }
    )

    st.caption(
        f"Exibindo {len(tabela)} de "
        f"{len(df)} lançamentos filtrados."
    )

    st.dataframe(
        tabela,
        use_container_width=True,
        hide_index=True,
        height=410,
    )


# ============================================================
# PONTO DE ENTRADA
# ============================================================

def render_dashboard(
    api_get_fn: Callable[[str], Any],
) -> None:
    """Renderiza o Dashboard Gerencial da Duarte Performance."""
    if not callable(api_get_fn):
        st.error(
            "O dashboard precisa receber a função de acesso à API. "
            "No app.py, utilize: render_dashboard(api_get)."
        )
        return

    _injetar_css()
    _render_cabecalho()

    df = _carregar_dataframe(api_get_fn)

    if df is None:
        st.error(
            "Não foi possível carregar os registros. "
            "Confira a conexão com a API e tente novamente."
        )
        return

    if df.empty:
        st.info(
            "Ainda não há lançamentos registrados "
            "para apresentar neste dashboard."
        )
        return

    df_filtrado = _render_filtros(df)

    if df_filtrado.empty:
        st.warning(
            "Nenhum lançamento corresponde "
            "aos filtros selecionados."
        )
        return

    kpis = _calcular_kpis(df_filtrado)

    _render_kpis(kpis)

    _render_insights(
        df_filtrado,
        kpis,
    )

    _render_graficos(
        df_filtrado,
        float(kpis["eficiencia"]),
    )

    _render_tabela(df_filtrado)