"""
Módulo: dashboard.py
Sistema: Duarte Performance — Duarte Gestão em Saúde
Descrição: Dashboard Gerencial — visão consolidada das execuções operacionais.

Reescrita 2.0 — o que foi corrigido nesta versão:
  • BUG CRÍTICO DE ESTRUTURA: no arquivo original, TODO o corpo da página
    (header, fetch de dados, filtros, KPIs, insights, gráficos e tabela)
    estava indentado dentro de `_inject_count_up()`, que ainda se
    autochamava recursivamente no meio do próprio corpo (linha 524 do
    arquivo original). Isso foi separado em funções coesas, com um único
    ponto de entrada `render_dashboard(api_get)`.
  • BUG DOS KPIs "CONGELADOS": o script de animação (count-up) usava
    `if (el.dataset.animated === "true") return;` — ou seja, uma vez
    animado, o número NUNCA MAIS era atualizado no DOM, mesmo trocando
    o filtro e o `data-target` mudando por trás. A trava agora compara
    o VALOR-ALVO (`data-target`) anterior com o atual: só pula a
    re-animação se o valor realmente não mudou. Isso resolve o "166 fica
    parado quando eu filtro por operador".
  • Pequeno bug de escopo no bloco de insights (`rank = df_temp.groupby(...)`
    ficava fora do `if "operador_exibicao" in df_f.columns:` que criava
    `df_temp` — corrigido para não estourar `NameError` em bases sem essa
    coluna).
  • Imports duplicados removidos.
"""

import functools
import html
from contextlib import contextmanager
from datetime import datetime, timedelta
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from utils import api_get

try:
    from zoneinfo import ZoneInfo
    FUSO_BR = ZoneInfo("America/Sao_Paulo")
except Exception:
    FUSO_BR = None

# ===================== PALETA DUARTE =====================

# Cores da Marca (Brand Identity)
COR_AZUL = "#001E57"          # Navy Institucional
COR_AZUL_CLARO = "#0B296B"    # Azul Secundário / Gradientes
COR_AZUL_ESCURO = "#030A1A"   # Fundo para Headers / Glassmorphism
COR_LARANJA = "#FF9200"       # Accent Principal (Duarte Orange)
COR_LARANJA_SOFT = "#FFB84D"  # Hover / Accents Suaves

# Cores Semânticas de Status
COR_VERDE = "#10B981"          # Realizado Total (Emerald)
COR_AMARELO = "#F59E0B"        # Realizado Parcial (Amber)
COR_VERMELHO = "#EF4444"       # Não Realizado (Rose Red)
COR_CINZA = "#94A3B8"          # Não Se Aplica (Slate)
COR_GRAFITE = "#64748B"        # Não Informado (Muted)

# Cores de Interface e Superfície
COR_BG_CARD = "#FFFFFF"
COR_BORDER = "#E2E8F0"
COR_TEXT_MAIN = "#0F172A"
COR_TEXT_MUTED = "#64748B"

# Mapeamento estático por status (Plotly & Streamlit)
CORES_STATUS = {
    "Realizado Total": COR_VERDE,
    "Realizado Parcial": COR_AMARELO,
    "Não Realizado": COR_VERMELHO,
    "Não Se Aplica": COR_CINZA,
    "Não Informado": COR_GRAFITE,
}

# Escala contínua para rankings e medidores de eficiência
ESCALA_EFICIENCIA = [COR_VERMELHO, COR_AMARELO, COR_VERDE]

# Checagem de compatibilidade com bordas arredondadas no Plotly
try:
    _fig_teste = go.Figure(go.Bar(x=[1], y=[1], marker=dict(cornerradius=6)))
    _fig_teste.to_dict()
    SUPORTA_CORNER_RADIUS = True
except Exception:
    SUPORTA_CORNER_RADIUS = False

# Tabela de remoção de acentos criada uma única vez (evita realocação a cada chamada)
_ACCENT_MAP = str.maketrans(
    "áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ",
    "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC",
)


# ===================== TRATAMENTO E NORMALIZAÇÃO DE DADOS =====================
@functools.lru_cache(maxsize=2048)
def _chave_operador(nome: Any) -> str:
    """Gera chave normalizada (sem acento, minúscula, 1º nome) com cache de memória."""
    if nome is None or pd.isna(nome):
        return ""
    s = str(nome).strip()
    if not s or s.lower() in ("nan", "none", "null"):
        return ""
    primeiro_nome = s.split()[0]
    return primeiro_nome.translate(_ACCENT_MAP).casefold()


def _rotulo_operador(series_nomes: pd.Series) -> str:
    """Retorna o nome de exibição mais completo (mais longo) de um grupo de operador."""
    nomes_validos = [
        s for n in series_nomes if (s := str(n).strip()) and s.lower() not in ("nan", "none", "")
    ]
    return max(nomes_validos, key=len, default="Sem nome")


def _normalizar_operadores(df: pd.DataFrame) -> pd.DataFrame:
    """Vectoriza e padroniza a identificação dos operadores em todo o DataFrame."""
    if df.empty or "operador_nome" not in df.columns:
        return df.assign(op_key="", operador_exibicao="Sem nome")

    df = df.copy()
    df["op_key"] = df["operador_nome"].apply(_chave_operador)

    mapa_rotulos = df.groupby("op_key")["operador_nome"].apply(_rotulo_operador).to_dict()
    df["operador_exibicao"] = df["op_key"].map(mapa_rotulos).fillna(df["operador_nome"].astype(str))

    return df


# ===================== ACESSO A DADOS E FUSO HORÁRIO =====================
@st.cache_data(ttl=15, show_spinner=False)
def _fetch_registros(_api_get: Callable[[str], Any]) -> Optional[Union[List[Dict], Dict]]:
    """Busca registros da API, resiliente a falhas, com cache curto do Streamlit."""
    try:
        resp = _api_get("/registros/")
        if not resp or getattr(resp, "status_code", None) != 200:
            return None
        dados = resp.json()
        if isinstance(dados, dict):
            return dados.get("data", [])
        return dados if isinstance(dados, list) else []
    except Exception:
        return None


def _agora_br() -> datetime:
    """Retorna o horário atual ajustado ao fuso horário brasileiro, se configurado."""
    return datetime.now(FUSO_BR) if FUSO_BR else datetime.now()


# ===================== COMPONENTES VISUAIS REUTILIZÁVEIS =====================
def _layout_padrao(fig, altura: int = 340, margem_b: int = 40):
    """Aplica o Design System visual e tipografia padronizada em gráficos Plotly."""
    fig.update_layout(
        height=altura,
        margin=dict(l=15, r=15, t=30, b=margem_b),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, -apple-system, sans-serif", color="#334155", size=12),
        hoverlabel=dict(
            bgcolor="#001E57",
            font_color="#FFFFFF",
            font_size=12,
            font_family="Inter, sans-serif",
            bordercolor="#FF9200",
        ),
        legend=dict(
            orientation="h", yanchor="bottom", y=-0.35, xanchor="center", x=0.5,
            font=dict(size=11, color="#64748B"),
        ),
        xaxis=dict(showgrid=False, zeroline=False, tickfont=dict(color="#64748B")),
        yaxis=dict(gridcolor="#F1F5F9", zeroline=False, tickfont=dict(color="#64748B")),
    )
    return fig


@contextmanager
def chart_card(icon: str, titulo: str, badge: Optional[str] = None):
    """Context manager para encapsular gráficos em cards modernos, com suporte a badge."""
    card = st.container(border=True)
    with card:
        badge_html = f'<span class="card-badge">{html.escape(badge)}</span>' if badge else ""
        st.markdown(
            f"""
            <div class="card-head" style="display:flex; align-items:center; gap:8px; margin-bottom:12px;">
                <span class="card-icon">{html.escape(icon)}</span>
                <h4 style="margin:0; font-weight:600; font-size:1.05rem; color:#0F172A;">{html.escape(titulo)}</h4>
                {badge_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
        yield card


def _kpi_html(
    valor: Union[int, float],
    label: str,
    sub: str,
    css_class: str = "",
    suffix: str = "",
    prefix: str = "",
) -> str:
    """Gera o HTML higienizado e acessível de um card de métrica (KPI).

    `data-target` carrega o valor ATUAL — é ele que o JS de count-up lê a cada
    rerun para decidir se precisa reanimar o número (ver `_inject_count_up_script`).
    """
    val_clean = float(valor) if isinstance(valor, (int, float)) else 0.0
    return f"""
    <div class="metric-card">
        <h3 class="{html.escape(css_class)} kpi-number"
            data-target="{val_clean}"
            data-prefix="{html.escape(prefix)}"
            data-suffix="{html.escape(suffix)}">
            {html.escape(prefix)}0{html.escape(suffix)}
        </h3>
        <p>{html.escape(label)}</p>
        <div class="sub">{html.escape(sub)}</div>
    </div>
    """


def _inject_css():
    """Injeta o CSS do Design System (Azul Marinho + Laranja Duarte). Chamar UMA vez,
    no início da renderização — antes do header."""
    st.markdown(
        """
    <style>
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(12px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes floatGradient {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes pulseGlow {
            0%   { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.45); }
            70%  { box-shadow: 0 0 0 10px rgba(255, 146, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
        }
        @keyframes popIn {
            0%   { transform: scale(0.9); opacity: 0.4; }
            60%  { transform: scale(1.04); opacity: 1; }
            100% { transform: scale(1); opacity: 1; }
        }

        .dash-header {
            background: linear-gradient(-45deg, #001E57, #051435, #0B296B, #001233);
            background-size: 300% 300%;
            animation: floatGradient 14s ease infinite, fadeInUp 0.4s ease-out;
            padding: 24px 28px;
            border-radius: 18px;
            color: #fff;
            margin-bottom: 22px;
            border-left: 6px solid #FF9200;
            box-shadow: 0 12px 32px rgba(0, 30, 87, 0.18);
            position: relative;
            overflow: hidden;
        }
        .dash-header::before {
            content: '';
            position: absolute;
            top: -50%; right: -5%;
            width: 260px; height: 260px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,146,0,0.18) 0%, transparent 70%);
            pointer-events: none;
        }
        .dash-header h2 {
            margin: 0; font-weight: 800; font-size: 1.65rem;
            letter-spacing: -0.3px; position: relative; z-index: 1;
        }
        .dash-header p {
            margin: 4px 0 0 0; color: #94A3B8; font-size: 0.88rem;
            position: relative; z-index: 1;
        }
        .dash-badge {
            display: inline-block; margin-top: 10px;
            background: linear-gradient(135deg, #FF9200, #FFAE33);
            color: #FFFFFF; padding: 4px 12px; border-radius: 99px;
            font-weight: 800; font-size: 0.65rem; letter-spacing: 0.5px;
            animation: pulseGlow 2.5s infinite; position: relative; z-index: 1;
        }
        .dash-live {
            display: inline-flex; align-items: center; gap: 6px;
            margin-left: 10px; font-size: 0.65rem; font-weight: 700;
            color: #86EFAC; position: relative; z-index: 1;
        }
        .dash-live .dot {
            width: 7px; height: 7px; border-radius: 50%;
            background: #22C55E; animation: pulseGlow 1.6s infinite;
        }

        .metric-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 16px 12px;
            text-align: center;
            box-shadow: 0 4px 16px rgba(0, 30, 87, 0.04);
            transition: all 0.25s ease;
            animation: fadeInUp 0.4s ease-out backwards;
            height: 100%;
        }
        .metric-card:hover {
            transform: translateY(-3px);
            border-color: rgba(255, 146, 0, 0.5);
            box-shadow: 0 8px 24px rgba(255, 146, 0, 0.12);
        }
        .metric-card h3 {
            margin: 0; color: #001E57; font-size: 1.6rem; font-weight: 800;
            font-variant-numeric: tabular-nums;
            transition: color 0.2s ease;
        }
        .metric-card h3.updated { animation: popIn 0.4s ease-out; }
        .metric-card h3.accent { color: #FF9200; }
        .metric-card h3.green  { color: #10B981; }
        .metric-card h3.red    { color: #EF4444; }
        .metric-card h3.yellow { color: #F59E0B; }
        .metric-card p {
            margin: 4px 0 0 0; color: #64748B; font-size: 0.70rem;
            font-weight: 700; text-transform: uppercase; letter-spacing: 0.4px;
        }
        .metric-card .sub { margin-top: 2px; font-size: 0.68rem; color: #94A3B8; font-weight: 600; }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 16px !important;
            border: 1px solid #E2E8F0 !important;
            background: #FFFFFF !important;
            box-shadow: 0 6px 20px rgba(0, 30, 87, 0.04) !important;
            animation: fadeInUp 0.45s ease-out backwards;
            transition: box-shadow .25s ease, transform .25s ease, border-color .25s ease;
            padding: 14px !important;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: 0 10px 28px rgba(0, 30, 87, 0.08) !important;
            border-color: rgba(255, 146, 0, 0.35) !important;
        }

        .card-head {
            display: flex; align-items: center; gap: 8px;
            margin-bottom: 8px; padding-bottom: 6px;
            border-bottom: 1px solid #F1F5F9;
        }
        .card-icon {
            display: inline-flex; align-items: center; justify-content: center;
            width: 28px; height: 28px; border-radius: 8px;
            background: rgba(255, 146, 0, 0.12); font-size: 14px;
        }
        .card-head h4 { margin: 0; color: #001E57; font-weight: 800; font-size: 0.95rem; flex: 1; }
        .card-badge {
            font-size: 0.62rem; font-weight: 800; text-transform: uppercase;
            letter-spacing: .04em; color: #FF9200;
            background: rgba(255,146,0,0.10); padding: 2px 8px; border-radius: 99px;
        }

        .insight-box {
            background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
            border: 1px solid #FDBA74; border-left: 4px solid #FF9200;
            border-radius: 12px; padding: 10px 14px; margin-bottom: 10px;
            animation: fadeInUp 0.4s ease-out backwards;
        }
        .insight-box strong { color: #9A3412; }
        .insight-box span { color: #7C2D12; font-size: 0.86rem; }

        .section-title {
            color: #001E57; font-weight: 800; font-size: 1.05rem;
            margin: 20px 0 10px 0; padding-left: 8px; border-left: 4px solid #FF9200;
        }

        div[data-testid="stDataFrame"] {
            background: #FFFFFF !important; border: 1px solid #E2E8F0 !important;
            border-radius: 14px !important; box-shadow: 0 6px 20px rgba(0, 30, 87, 0.04) !important;
            overflow: hidden !important;
        }
        div[data-testid="stDataFrame"] thead tr th {
            background: #001E57 !important;
            color: #FFFFFF !important; font-weight: 700 !important; font-size: 0.72rem !important;
            text-transform: uppercase !important; letter-spacing: 0.3px !important;
            padding: 10px 12px !important; border: none !important;
        }
        div[data-testid="stDataFrame"] tbody tr td {
            padding: 9px 12px !important; font-size: 0.84rem !important;
            color: #1E293B !important; border-bottom: 1px solid #F1F5F9 !important;
        }
        div[data-testid="stDataFrame"] tbody tr:nth-child(even) td { background: #F8FAFC !important; }
        div[data-testid="stDataFrame"] tbody tr:hover td { background: rgba(255, 146, 0, 0.06) !important; }
    </style>
    """,
        unsafe_allow_html=True,
    )


def _inject_count_up_script():
    """Injeta o JavaScript de animação (count-up) dos KPIs.

    CORREÇÃO DO BUG PRINCIPAL: a versão anterior usava uma trava
    `if (dataset.animated === "true") return`, ou seja, uma vez animado o
    número NUNCA mais era atualizado — mesmo trocando o filtro. Agora a
    trava compara o valor-alvo atual (`data-target`) com o último valor
    exibido (`dataset.lastTarget`): só pula a animação quando o valor
    realmente não mudou. Assim, ao trocar operador/status/cliente/período,
    os cards sempre refletem o novo `data-target` calculado em Python.
    """
    components.html(
        """
        <script>
        (function() {
            const doc = window.parent.document;

            function animar(el) {
                const alvoStr = el.getAttribute('data-target') || "0";
                if (el.dataset.lastTarget === alvoStr) {
                    return; // valor não mudou desde o último render: não reanima
                }
                el.dataset.lastTarget = alvoStr;
                el.classList.remove('updated');
                void el.offsetWidth; // reflow para reiniciar a animação CSS
                el.classList.add('updated');

                const alvo = parseFloat(alvoStr) || 0;
                const sufixo = el.getAttribute('data-suffix') || '';
                const prefixo = el.getAttribute('data-prefix') || '';
                const casas = sufixo.includes('%') || String(alvo).includes('.') ? 1 : 0;
                const duracao = 600;
                const inicio = performance.now();
                const partiuDe = parseFloat(el.dataset.lastRendered || "0") || 0;

                function passo(agora) {
                    const p = Math.min((agora - inicio) / duracao, 1);
                    const suave = 1 - Math.pow(1 - p, 3); // easing outCubic
                    const valor = partiuDe + (alvo - partiuDe) * suave;
                    const formatado = casas ? valor.toFixed(casas) : Math.round(valor);
                    el.textContent = prefixo + formatado.toLocaleString('pt-BR') + sufixo;
                    if (p < 1) {
                        requestAnimationFrame(passo);
                    } else {
                        el.dataset.lastRendered = String(alvo);
                    }
                }
                requestAnimationFrame(passo);
            }

            function varrer() {
                doc.querySelectorAll('.kpi-number').forEach(animar);
            }

            // Primeira varredura logo após montar
            setTimeout(varrer, 50);

            // Observa mudanças no DOM (novo filtro = Streamlit re-renderiza os cards)
            // e revarre sempre que o conteúdo dos KPIs mudar.
            const alvoObservado = doc.body;
            if (alvoObservado && !alvoObservado.dataset.duarteKpiObserverAtivo) {
                alvoObservado.dataset.duarteKpiObserverAtivo = "true";
                const observer = new MutationObserver(() => {
                    clearTimeout(window.__duarteKpiDebounce);
                    window.__duarteKpiDebounce = setTimeout(varrer, 60);
                });
                observer.observe(alvoObservado, { childList: true, subtree: true, attributes: true });
            }
        })();
        </script>
        """,
        height=0,
    )


# ===================== CARGA E FILTRAGEM DE DADOS =====================
def _carregar_dataframe() -> Optional[pd.DataFrame]:
    """Busca os registros na API e devolve um DataFrame já normalizado."""
    with st.spinner("Carregando indicadores..."):
        dados = _fetch_registros(api_get)

    if dados is None:
        return None

    df = pd.DataFrame(dados)
    if df.empty:
        return df

    if "data_registro" in df.columns:
        df["data_registro"] = pd.to_datetime(df["data_registro"], errors="coerce")

    return _normalizar_operadores(df)


def _render_filtros(df: pd.DataFrame) -> pd.DataFrame:
    """Renderiza os controles de filtro e retorna o DataFrame já filtrado.

    Importante: os `selectbox` abaixo são lidos a cada rerun do Streamlit —
    a variável `df_f` retornada por esta função é SEMPRE recalculada a
    partir da seleção atual, então os KPIs, insights, gráficos e tabela que
    consomem esse retorno já nascem coerentes com o filtro escolhido.
    """
    st.markdown("##### 🎛️ Filtros de Pesquisa")
    f1, f2, f3, f4 = st.columns([1.4, 1.3, 1.3, 1.5])

    with f1:
        opcoes_periodo = ["Hoje", "Últimos 7 dias", "Últimos 30 dias", "Este mês", "Todos"]
        if hasattr(st, "segmented_control"):
            periodo = st.segmented_control(
                "Período", opcoes_periodo, default="Todos", key="dash_periodo"
            ) or "Todos"
        else:
            periodo = st.selectbox("Período", opcoes_periodo, index=4, key="dash_periodo")

    agora = _agora_br()
    df_f = df.copy()

    if periodo != "Todos" and "data_registro" in df_f.columns:
        try:
            if getattr(df_f["data_registro"].dt, "tz", None) is not None:
                df_f["data_registro"] = (
                    df_f["data_registro"].dt.tz_convert("America/Sao_Paulo").dt.tz_localize(None)
                )
        except Exception:
            pass

        df_f = df_f[df_f["data_registro"].notna()].copy()

        if periodo == "Hoje":
            df_f = df_f[df_f["data_registro"].dt.date == agora.date()]
        elif periodo == "Últimos 7 dias":
            limite = (agora - timedelta(days=7)).replace(tzinfo=None)
            df_f = df_f[df_f["data_registro"] >= limite]
        elif periodo == "Últimos 30 dias":
            limite = (agora - timedelta(days=30)).replace(tzinfo=None)
            df_f = df_f[df_f["data_registro"] >= limite]
        elif periodo == "Este mês":
            df_f = df_f[
                (df_f["data_registro"].dt.month == agora.month)
                & (df_f["data_registro"].dt.year == agora.year)
            ]

    operadores = ["Todos"]
    if "operador_exibicao" in df_f.columns:
        operadores += sorted(df_f["operador_exibicao"].dropna().unique().tolist())
    with f2:
        filtro_op = st.selectbox("Operador", operadores, key="dash_op")

    status_list = ["Todos"]
    if "status" in df_f.columns:
        status_list += sorted(df_f["status"].dropna().unique().tolist())
    with f3:
        filtro_status = st.selectbox("Status", status_list, key="dash_status")

    clientes = ["Todos"]
    if "cliente_nome" in df_f.columns:
        clientes += sorted(df_f["cliente_nome"].dropna().unique().tolist())
    with f4:
        filtro_cliente = st.selectbox("Cliente", clientes, key="dash_cliente")

    if filtro_op != "Todos" and "operador_exibicao" in df_f.columns:
        df_f = df_f[df_f["operador_exibicao"] == filtro_op]
    if filtro_status != "Todos" and "status" in df_f.columns:
        df_f = df_f[df_f["status"] == filtro_status]
    if filtro_cliente != "Todos" and "cliente_nome" in df_f.columns:
        df_f = df_f[df_f["cliente_nome"] == filtro_cliente]

    return df_f


# ===================== KPIs =====================
def _calcular_kpis(df_f: pd.DataFrame) -> dict:
    total = len(df_f)
    realizados = int((df_f["status"] == "Realizado Total").sum()) if "status" in df_f.columns else 0
    parciais = int((df_f["status"] == "Realizado Parcial").sum()) if "status" in df_f.columns else 0
    nao = int((df_f["status"] == "Não Realizado").sum()) if "status" in df_f.columns else 0
    eficiencia = round((realizados / total * 100), 1) if total else 0.0
    return {
        "total": total,
        "realizados": realizados,
        "parciais": parciais,
        "nao": nao,
        "eficiencia": eficiencia,
    }


def _render_kpis(kpis: dict):
    total = kpis["total"]
    realizados = kpis["realizados"]
    parciais = kpis["parciais"]
    nao = kpis["nao"]
    eficiencia = kpis["eficiencia"]

    k1, k2, k3, k4, k5 = st.columns(5)

    with k1:
        st.markdown(_kpi_html(total, "Total", "lançamentos"), unsafe_allow_html=True)
    with k2:
        pct = round(realizados / total * 100, 1) if total else 0
        st.markdown(_kpi_html(realizados, "Realizados", f"{pct}%", "green"), unsafe_allow_html=True)
    with k3:
        pct = round(parciais / total * 100, 1) if total else 0
        st.markdown(_kpi_html(parciais, "Parciais", f"{pct}%", "yellow"), unsafe_allow_html=True)
    with k4:
        pct = round(nao / total * 100, 1) if total else 0
        st.markdown(_kpi_html(nao, "Não realizados", f"{pct}%", "red"), unsafe_allow_html=True)
    with k5:
        st.markdown(
            _kpi_html(eficiencia, "Eficiência", "Realizado Total", "accent", suffix="%"),
            unsafe_allow_html=True,
        )

    # Injetado DEPOIS dos cards, para que o JS já encontre os elementos no DOM.
    _inject_count_up_script()
    st.markdown("<br>", unsafe_allow_html=True)


# ===================== INSIGHTS =====================
def _render_insights(df_f: pd.DataFrame, kpis: dict):
    insights = []
    total = kpis["total"]
    parciais = kpis["parciais"]
    nao = kpis["nao"]

    if total > 0 and "status" in df_f.columns and "operador_exibicao" in df_f.columns:
        df_temp = df_f.assign(_is_realizado=df_f["status"].eq("Realizado Total"))
        rank = (
            df_temp.groupby("operador_exibicao")
            .agg(total=("status", "count"), realizados=("_is_realizado", "sum"))
            .reset_index()
        )
        rank["eficiencia"] = (rank["realizados"] / rank["total"] * 100).round(1)
        rank_valido = rank[rank["total"] >= 3]

        if not rank_valido.empty:
            melhor = rank_valido.loc[rank_valido["eficiencia"].idxmax()]
            melhor_nome = html.escape(str(melhor["operador_exibicao"]))

            if melhor["eficiencia"] >= 80:
                insights.append(
                    f"🏆 <strong>{melhor_nome}</strong> lidera em eficiência "
                    f"({melhor['eficiencia']}% em {int(melhor['total'])} apontamentos)."
                )

            if len(rank_valido) > 1:
                pior = rank_valido.loc[rank_valido["eficiencia"].idxmin()]
                pior_nome = html.escape(str(pior["operador_exibicao"]))

                if (
                    pior["eficiencia"] < 50
                    and pior["total"] >= 5
                    and pior["operador_exibicao"] != melhor["operador_exibicao"]
                ):
                    insights.append(
                        f"⚠️ <strong>{pior_nome}</strong> registra a menor eficiência do período "
                        f"({pior['eficiencia']}% em {int(pior['total'])} apontamentos)."
                    )

    if total > 0:
        taxa_problema = round(((parciais + nao) / total * 100), 1)
        if taxa_problema > 35:
            insights.append(
                f"📉 A taxa de ocorrências pendentes (Parcial + Não Realizado) está em "
                f"<strong>{taxa_problema}%</strong>."
            )

    for ins in insights[:3]:
        st.markdown(f'<div class="insight-box"><span>{ins}</span></div>', unsafe_allow_html=True)


# ===================== GRÁFICOS =====================
def _render_graficos(df_f: pd.DataFrame, eficiencia: float):
    c1, c2 = st.columns(2)

    with c1:
        with chart_card("🎯", "Distribuição por Status"):
            if "status" in df_f.columns and not df_f["status"].isna().all():
                vc = df_f["status"].value_counts().reset_index()
                vc.columns = ["status", "qtd"]
                fig = px.pie(
                    vc, names="status", values="qtd", color="status",
                    color_discrete_map=CORES_STATUS, hole=0.64,
                )
                fig.update_traces(
                    textposition="inside",
                    textinfo="percent",
                    marker=dict(line=dict(color="#FFFFFF", width=2)),
                    hovertemplate="<b>%{label}</b><br>%{value} lançamentos (%{percent})<extra></extra>",
                )
                fig.add_annotation(
                    text=f"<b style='font-size:22px;color:{COR_AZUL}'>{eficiencia}%</b><br>"
                         f"<span style='font-size:10px;color:#94A3B8'>EFICIÊNCIA</span>",
                    x=0.5, y=0.5, showarrow=False, align="center",
                )
                fig = _layout_padrao(fig, 330, margem_b=50)
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sem dados de status.")

    with c2:
        with chart_card("📈", "Ranking de Eficiência por Operador"):
            if "operador_exibicao" in df_f.columns and "status" in df_f.columns:
                rank_plot = (
                    df_f.groupby("operador_exibicao")
                    .agg(total=("status", "count"), realizados=("status", lambda x: (x == "Realizado Total").sum()))
                    .reset_index()
                )
                rank_plot["eficiencia"] = (rank_plot["realizados"] / rank_plot["total"] * 100).round(1)
                rank_plot = rank_plot.sort_values("eficiencia", ascending=True)

                if not rank_plot.empty:
                    fig2 = px.bar(
                        rank_plot, x="eficiencia", y="operador_exibicao", orientation="h",
                        color="eficiencia", color_continuous_scale=["#EF4444", "#F59E0B", "#10B981"],
                        text="eficiencia",
                    )
                    marker_extra = dict(cornerradius=6) if SUPORTA_CORNER_RADIUS else {}
                    fig2.update_traces(
                        texttemplate="%{text}%", textposition="outside",
                        marker_line_width=0,
                        hovertemplate="<b>%{y}</b><br>Eficiência: %{x}%<extra></extra>",
                        **({"marker": marker_extra} if marker_extra else {}),
                    )
                    fig2.update_layout(coloraxis_showscale=False)
                    fig2 = _layout_padrao(fig2, max(330, 32 * len(rank_plot) + 60), margem_b=25)
                    fig2.update_yaxes(title="")
                    fig2.update_xaxes(title="Eficiência %", gridcolor="#F1F5F9", range=[0, 115])
                    st.plotly_chart(fig2, use_container_width=True, config={"displayModeBar": False})
                else:
                    st.info("Sem dados suficientes.")
            else:
                st.info("Sem dados de operador.")

    with chart_card("👥", "Volume e Status por Operador"):
        if "status" in df_f.columns and "operador_exibicao" in df_f.columns:
            comp = df_f.groupby(["operador_exibicao", "status"]).size().reset_index(name="qtd")
            fig_comp = px.bar(
                comp, x="operador_exibicao", y="qtd", color="status",
                barmode="stack", color_discrete_map=CORES_STATUS,
            )
            fig_comp.update_traces(hovertemplate="<b>%{x}</b><br>%{fullData.name}: %{y}<extra></extra>")
            fig_comp.update_layout(xaxis_title="", yaxis_title="Lançamentos", legend_title="")
            fig_comp.update_xaxes(tickangle=-15)
            fig_comp.update_yaxes(gridcolor="#F1F5F9")
            fig_comp = _layout_padrao(fig_comp, 360, margem_b=60)
            st.plotly_chart(fig_comp, use_container_width=True, config={"displayModeBar": False})
        else:
            st.info("Sem dados para comparativo.")

    if "cliente_nome" in df_f.columns:
        with chart_card("🏢", "Top Clientes (Volume + Eficiência)"):
            cli = (
                df_f.groupby("cliente_nome")
                .agg(total=("status", "count"), realizados=("status", lambda x: (x == "Realizado Total").sum()))
                .reset_index()
            )
            cli["eficiencia"] = (cli["realizados"] / cli["total"] * 100).round(1)
            cli = cli.sort_values("total", ascending=False).head(10)

            if not cli.empty:
                fig_cli = px.bar(
                    cli, x="cliente_nome", y="total", color="eficiencia",
                    color_continuous_scale=["#EF4444", "#F59E0B", "#10B981"], text="total",
                )
                marker_extra = dict(cornerradius=6) if SUPORTA_CORNER_RADIUS else {}
                fig_cli.update_traces(
                    textposition="outside",
                    hovertemplate="<b>%{x}</b><br>Volume: %{y}<br>Eficiência: %{marker.color}%<extra></extra>",
                    **({"marker": marker_extra} if marker_extra else {}),
                )
                fig_cli.update_layout(xaxis_title="", yaxis_title="Lançamentos", coloraxis_colorbar=dict(title="Eficiência %"))
                fig_cli.update_xaxes(tickangle=-20)
                fig_cli = _layout_padrao(fig_cli, 360, margem_b=55)
                st.plotly_chart(fig_cli, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sem dados de clientes.")

    with chart_card("📈", "Evolução Temporal das Execuções"):
        if "data_registro" in df_f.columns:
            tmp = df_f.dropna(subset=["data_registro"]).copy()
            if not tmp.empty:
                tmp["dia"] = tmp["data_registro"].dt.date
                serie = tmp.groupby("dia").size().reset_index(name="quantidade").sort_values("dia")

                if "status" in tmp.columns:
                    tmp["realizado"] = (tmp["status"] == "Realizado Total").astype(int)
                    efic = tmp.groupby("dia").agg(total=("status", "count"), real=("realizado", "sum")).reset_index()
                    efic["eficiencia"] = (efic["real"] / efic["total"] * 100).round(1)

                    fig3 = go.Figure()
                    fig3.add_trace(go.Scatter(
                        x=serie["dia"], y=serie["quantidade"], mode="lines+markers", name="Volume",
                        line=dict(color=COR_AZUL, width=3, shape="spline"),
                        marker=dict(color=COR_LARANJA, size=7),
                        fill="tozeroy", fillcolor="rgba(0, 30, 87, 0.06)",
                        hovertemplate="<b>%{x}</b><br>Volume: %{y}<extra></extra>",
                    ))
                    fig3.add_trace(go.Scatter(
                        x=efic["dia"], y=efic["eficiencia"], mode="lines+markers", name="Eficiência %",
                        yaxis="y2", line=dict(color=COR_VERDE, width=2.5, dash="dot"), marker=dict(size=6),
                        hovertemplate="<b>%{x}</b><br>Eficiência: %{y}%<extra></extra>",
                    ))
                    fig3.update_layout(
                        yaxis=dict(title="Volume", gridcolor="#F1F5F9"),
                        yaxis2=dict(title="Eficiência %", overlaying="y", side="right", range=[0, 105], showgrid=False),
                        hovermode="x unified",
                    )
                else:
                    fig3 = go.Figure(data=[go.Scatter(
                        x=serie["dia"], y=serie["quantidade"], mode="lines+markers",
                        line=dict(color=COR_AZUL, width=3, shape="spline"),
                        marker=dict(color=COR_LARANJA, size=8),
                        fill="tozeroy", fillcolor="rgba(0, 30, 87, 0.06)",
                    )])

                fig3 = _layout_padrao(fig3, 330, margem_b=45)
                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sem dados suficientes para gerar evolução.")
        else:
            st.info("Sem dados de data para gerar evolução.")


# ===================== TABELA =====================
def _render_tabela(df_f: pd.DataFrame):
    st.markdown('<p class="section-title">📋 Lançamentos Registrados</p>', unsafe_allow_html=True)

    cols = [c for c in ["data_registro", "operador_nome", "cliente_nome", "status", "justificativa"] if c in df_f.columns]

    if not cols:
        st.info("Sem lançamentos para listar.")
        return

    tabela = df_f[cols].sort_values(
        "data_registro" if "data_registro" in cols else cols[0], ascending=False
    ).copy()

    if "data_registro" in tabela.columns:
        tabela["data_registro"] = pd.to_datetime(
            tabela["data_registro"], errors="coerce"
        ).dt.strftime("%d/%m/%Y %H:%M")

    rename_map = {
        "data_registro": "Data",
        "operador_nome": "Operador",
        "cliente_nome": "Cliente",
        "status": "Status",
        "justificativa": "Justificativa",
    }
    tabela = tabela.rename(columns={k: v for k, v in rename_map.items() if k in tabela.columns})

    st.caption(f"Exibindo {min(50, len(tabela))} de {len(tabela)} registros filtrados")
    st.dataframe(tabela.head(50), use_container_width=True, hide_index=True, height=400)


# ===================== ENTRY POINT =====================
def render_dashboard(api_get_fn: Optional[Callable[[str], Any]] = None):
    """Ponto de entrada único do Dashboard Gerencial.

    `api_get_fn` é opcional apenas para permitir injeção em testes; em
    produção o módulo usa o `api_get` importado de `utils`, mantendo
    compatibilidade com o restante do app.
    """
    _injetar = api_get_fn or api_get

    _inject_css()

    st.markdown(
        """
    <div class="dash-header">
        <h2>📊 Dashboard Gerencial</h2>
        <p>Visão consolidada das execuções operacionais · performance da equipe</p>
        <span class="dash-badge">⚡ PERFORMANCE · DUARTE GESTÃO</span>
        <span class="dash-live"><span class="dot"></span> DADOS AO VIVO · ATUALIZA A CADA 15S</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    df = _carregar_dataframe()
    if df is None:
        st.error("Erro ao carregar registros da API.")
        return
    if df.empty:
        st.info("Nenhum registro encontrado.")
        return

    df_f = _render_filtros(df)

    if df_f.empty:
        st.warning("Nenhum registro encontrado com os filtros selecionados.")
        return

    kpis = _calcular_kpis(df_f)
    _render_kpis(kpis)
    _render_insights(df_f, kpis)
    _render_graficos(df_f, kpis["eficiencia"])
    _render_tabela(df_f)


# Compatibilidade retroativa: caso algum ponto do app ainda importe e chame
# `_inject_count_up` esperando que ela renderize a página inteira (como no
# arquivo anterior, por causa do bug de indentação), redirecionamos para o
# entry point correto em vez de quebrar silenciosamente.
def _inject_count_up():
    render_dashboard()