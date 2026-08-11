import streamlit as st
import streamlit.components.v1 as components
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from contextlib import contextmanager
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo
    FUSO_BR = ZoneInfo("America/Sao_Paulo")
except Exception:
    FUSO_BR = None

# ===================== PALETA DUARTE =====================
COR_AZUL = "#001E57"
COR_AZUL_CLARO = "#0B296B"
COR_LARANJA = "#FF9200"
COR_VERDE = "#10B981"
COR_AMARELO = "#F59E0B"
COR_VERMELHO = "#EF4444"
COR_CINZA = "#94A3B8"

CORES_STATUS = {
    "Realizado Total": COR_VERDE,
    "Realizado Parcial": COR_AMARELO,
    "Não Realizado": COR_VERMELHO,
    "Não Se Aplica": COR_CINZA,
    "Não Informado": "#64748B",
}

try:
    _fig_teste = go.Figure(go.Bar(x=[1], y=[1], marker=dict(cornerradius=6)))
    _fig_teste.to_dict()
    SUPORTA_CORNER_RADIUS = True
except Exception:
    SUPORTA_CORNER_RADIUS = False


# ===================== HELPERS =====================
def _chave_operador(nome: str) -> str:
    if nome is None or (isinstance(nome, float) and pd.isna(nome)):
        return ""
    s = str(nome).strip()
    if not s:
        return ""
    primeiro = s.split()[0]
    mapa = str.maketrans(
        "áàâãäéèêëíìîïóòôõöúùûüçÁÀÂÃÄÉÈÊËÍÌÎÏÓÒÔÕÖÚÙÛÜÇ",
        "aaaaaeeeeiiiiooooouuuucAAAAAEEEEIIIIOOOOOUUUUC",
    )
    return primeiro.translate(mapa).casefold()


def _rotulo_operador(series_nomes: pd.Series) -> str:
    nomes = [str(n).strip() for n in series_nomes if n and str(n).strip()]
    if not nomes:
        return "Sem nome"
    return max(nomes, key=len)


def _normalizar_operadores(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "operador_nome" not in df.columns:
        df["op_key"] = ""
        df["operador_exibicao"] = "Sem nome"
        return df
    df["op_key"] = df["operador_nome"].apply(_chave_operador)
    mapa = df.groupby("op_key")["operador_nome"].apply(_rotulo_operador).to_dict()
    df["operador_exibicao"] = df["op_key"].map(mapa).fillna(df["operador_nome"].astype(str))
    return df


@st.cache_data(ttl=15, show_spinner=False)
def _fetch_registros(_api_get):
    try:
        resp = _api_get("/registros/")
        if resp is None or resp.status_code != 200:
            return None
        dados = resp.json()
        if isinstance(dados, dict) and "data" in dados:
            return dados["data"]
        if isinstance(dados, list):
            return dados
        return []
    except Exception:
        return None


def _agora_br():
    if FUSO_BR:
        return datetime.now(FUSO_BR)
    return datetime.now()


def _layout_padrao(fig, altura=320):
    fig.update_layout(
        height=altura,
        margin=dict(l=12, r=12, t=18, b=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, system-ui, sans-serif", color="#334155", size=13),
        hoverlabel=dict(
            bgcolor="#001E57",
            font_color="#FFFFFF",
            font_size=12,
            font_family="Inter, system-ui, sans-serif",
            bordercolor="#001E57",
        ),
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=-0.28,
            xanchor="center",
            x=0.5,
            font=dict(size=12),
        ),
    )
    return fig


@contextmanager
def chart_card(icon: str, titulo: str, badge: str | None = None):
    card = st.container(border=True)
    with card:
        badge_html = f'<span class="card-badge">{badge}</span>' if badge else ""
        st.markdown(
            f"""
            <div class="card-head">
                <span class="card-icon">{icon}</span>
                <h4>{titulo}</h4>
                {badge_html}
            </div>
            """,
            unsafe_allow_html=True,
        )
        yield card


def _kpi_html(valor, label, sub, css_class="", suffix=""):
    return f"""
    <div class="metric-card">
        <h3 class="{css_class} kpi-number" data-target="{valor}" data-suffix="{suffix}">0{suffix}</h3>
        <p>{label}</p>
        <div class="sub">{sub}</div>
    </div>
    """


def _inject_count_up():
    components.html(
        """
        <script>
        (function() {
            const doc = window.parent.document;

            function animar(el) {
                const alvo = parseFloat(el.getAttribute('data-target')) || 0;
                const sufixo = el.getAttribute('data-suffix') || '';
                const casas = sufixo.includes('%') ? 1 : 0;
                const duracao = 700;
                const inicio = performance.now();

                el.textContent = (casas ? alvo.toFixed(casas) : Math.round(alvo)) + sufixo;

                function passo(agora) {
                    const p = Math.min((agora - inicio) / duracao, 1);
                    const suave = 1 - Math.pow(1 - p, 3);
                    const valor = alvo * suave;
                    el.textContent = (casas ? valor.toFixed(casas) : Math.round(valor)) + sufixo;
                    if (p < 1) requestAnimationFrame(passo);
                }
                requestAnimationFrame(passo);
            }

            setTimeout(function() {
                const elementos = doc.querySelectorAll('.kpi-number');
                elementos.forEach(function(el) {
                    el.textContent = '0' + (el.getAttribute('data-suffix') || '');
                    animar(el);
                });
            }, 60);
        })();
        </script>
        """,
        height=0,
    )


def render_dashboard(api_get):
    # ===================== CSS =====================
    st.markdown(
        """
    <style>
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(16px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes floatGradient {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes pulseGlow {
            0%   { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.45); }
            70%  { box-shadow: 0 0 0 12px rgba(255, 146, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
        }
        @keyframes softBounce {
            0%, 100% { transform: translateY(0); }
            50%      { transform: translateY(-2px); }
        }

        .dash-header {
            background: linear-gradient(-45deg, #001E57, #030A1A, #0A2540, #001233);
            background-size: 300% 300%;
            animation: floatGradient 14s ease infinite, fadeInUp 0.5s ease-out;
            padding: 26px 30px;
            border-radius: 20px;
            color: #fff;
            margin-bottom: 20px;
            border-left: 5px solid #FF9200;
            box-shadow: 0 16px 40px rgba(0, 30, 87, 0.22);
            position: relative;
            overflow: hidden;
        }
        .dash-header::before {
            content: '';
            position: absolute;
            top: -40%; right: -5%;
            width: 240px; height: 240px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,146,0,0.16) 0%, transparent 70%);
            pointer-events: none;
        }
        .dash-header h2 {
            margin: 0; font-weight: 900; font-size: 1.7rem;
            letter-spacing: -0.4px; position: relative; z-index: 1;
        }
        .dash-header p {
            margin: 6px 0 0 0; color: #94A3B8; font-size: 0.9rem;
            position: relative; z-index: 1;
        }
        .dash-badge {
            display: inline-block; margin-top: 11px;
            background: linear-gradient(135deg, #FF9200, #FFB84D);
            color: #fff; padding: 5px 12px; border-radius: 99px;
            font-weight: 800; font-size: 0.68rem; letter-spacing: 0.3px;
            animation: pulseGlow 2.5s infinite; position: relative; z-index: 1;
        }

        .metric-card {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 16px 12px;
            text-align: center;
            box-shadow: 0 8px 22px rgba(0, 30, 87, 0.06);
            transition: all 0.28s cubic-bezier(0.4, 0, 0.2, 1);
            animation: fadeInUp 0.5s ease-out backwards;
            height: 100%;
        }
        .metric-card:hover {
            transform: translateY(-4px);
            border-color: rgba(255, 146, 0, 0.45);
            box-shadow: 0 14px 30px rgba(255, 146, 0, 0.13);
        }
        .metric-card h3 {
            margin: 0; color: #001E57; font-size: 1.65rem; font-weight: 900;
            font-variant-numeric: tabular-nums;
        }
        .metric-card h3.accent { color: #FF9200; }
        .metric-card h3.green  { color: #10B981; }
        .metric-card h3.red    { color: #EF4444; }
        .metric-card h3.yellow { color: #F59E0B; }
        .metric-card p {
            margin: 5px 0 0 0; color: #64748B; font-size: 0.70rem;
            font-weight: 800; text-transform: uppercase; letter-spacing: 0.4px;
        }
        .metric-card .sub { margin-top: 3px; font-size: 0.67rem; color: #94A3B8; font-weight: 600; }

        div[data-testid="stVerticalBlockBorderWrapper"] {
            border-radius: 18px !important;
            border: 1px solid #E2E8F0 !important;
            box-shadow: 0 10px 28px rgba(0, 30, 87, 0.06) !important;
            animation: fadeInUp 0.55s ease-out backwards;
            transition: box-shadow .28s ease, transform .28s ease, border-color .28s ease;
        }
        div[data-testid="stVerticalBlockBorderWrapper"]:hover {
            box-shadow: 0 16px 36px rgba(0, 30, 87, 0.11) !important;
            border-color: rgba(255, 146, 0, 0.35) !important;
            transform: translateY(-2px);
        }

        .card-head {
            display: flex; align-items: center; gap: 10px;
            margin: 0 0 12px 0;
        }
        .card-icon {
            display: inline-flex; align-items: center; justify-content: center;
            width: 30px; height: 30px; border-radius: 10px;
            background: linear-gradient(135deg, rgba(255,146,0,0.14), rgba(0,30,87,0.08));
            font-size: 15px;
            animation: softBounce 2.8s ease-in-out infinite;
        }
        .card-head h4 { margin: 0; color: #001E57; font-weight: 800; font-size: 0.98rem; flex: 1; }
        .card-badge {
            font-size: 0.65rem; font-weight: 800; text-transform: uppercase;
            letter-spacing: .04em; color: #FF9200;
            background: rgba(255,146,0,0.10); padding: 3px 9px; border-radius: 99px;
        }

        .insight-box {
            background: linear-gradient(135deg, #FFF7ED 0%, #FFEDD5 100%);
            border: 1px solid #FDBA74; border-left: 5px solid #FF9200;
            border-radius: 14px; padding: 13px 16px; margin-bottom: 12px;
            animation: fadeInUp 0.5s ease-out backwards;
        }
        .insight-box strong { color: #9A3412; }
        .insight-box span { color: #7C2D12; font-size: 0.9rem; }

        .section-title {
            color: #001E57; font-weight: 900; font-size: 1.1rem;
            margin: 22px 0 12px 0; padding-left: 10px; border-left: 4px solid #FF9200;
        }

        div[data-testid="stDataFrame"] {
            background: #FFFFFF !important; border: 1px solid #E2E8F0 !important;
            border-radius: 16px !important; box-shadow: 0 10px 28px rgba(0, 30, 87, 0.07) !important;
            overflow: hidden !important;
        }
        div[data-testid="stDataFrame"] thead tr th {
            background: linear-gradient(135deg, #001E57 0%, #0B296B 100%) !important;
            color: #FFFFFF !important; font-weight: 800 !important; font-size: 0.75rem !important;
            text-transform: uppercase !important; letter-spacing: 0.35px !important;
            padding: 11px 13px !important; border: none !important;
        }
        div[data-testid="stDataFrame"] tbody tr td {
            padding: 10px 13px !important; font-size: 0.86rem !important;
            color: #1E293B !important; border-bottom: 1px solid #F1F5F9 !important;
        }
        div[data-testid="stDataFrame"] tbody tr:nth-child(even) td { background: #F8FAFC !important; }
        div[data-testid="stDataFrame"] tbody tr:hover td { background: rgba(255, 146, 0, 0.08) !important; }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # ===================== HEADER =====================
    st.markdown(
        """
    <div class="dash-header">
        <h2>📊 Dashboard Gerencial</h2>
        <p>Visão consolidada das execuções operacionais · performance da equipe</p>
        <span class="dash-badge">⚡ PERFORMANCE · DUARTE</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # ===================== CARREGAMENTO =====================
    with st.spinner("Carregando indicadores..."):
        dados = _fetch_registros(api_get)

    if dados is None:
        st.error("Erro ao carregar registros da API.")
        return

    df = pd.DataFrame(dados)
    if df.empty:
        st.info("Nenhum registro encontrado.")
        return

    if "data_registro" in df.columns:
        df["data_registro"] = pd.to_datetime(df["data_registro"], errors="coerce")

    df = _normalizar_operadores(df)

    # ===================== FILTROS =====================
    st.markdown("##### 🎛️ Filtros")
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

    # ===== CORREÇÃO PRINCIPAL: só filtra data se NÃO for "Todos" =====
    if periodo != "Todos" and "data_registro" in df_f.columns:
        # Remove timezone se existir
        try:
            if getattr(df_f["data_registro"].dt, "tz", None) is not None:
                df_f["data_registro"] = (
                    df_f["data_registro"]
                    .dt.tz_convert("America/Sao_Paulo")
                    .dt.tz_localize(None)
                )
        except Exception:
            pass

        # Mantém apenas linhas que TÊM data válida quando o filtro de período está ativo
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

    # Filtros de Operador / Status / Cliente
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

    if df_f.empty:
        st.warning("Nenhum registro encontrado com os filtros selecionados.")
        return

    # ===================== KPIs =====================
    total = len(df_f)
    realizados = len(df_f[df_f["status"] == "Realizado Total"]) if "status" in df_f.columns else 0
    parciais = len(df_f[df_f["status"] == "Realizado Parcial"]) if "status" in df_f.columns else 0
    nao = len(df_f[df_f["status"] == "Não Realizado"]) if "status" in df_f.columns else 0
    eficiencia = round((realizados / total * 100), 1) if total else 0.0

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
        st.markdown(_kpi_html(eficiencia, "Eficiência", "Realizado Total", "accent", suffix="%"), unsafe_allow_html=True)

    _inject_count_up()
    st.markdown("<br>", unsafe_allow_html=True)

    # ===================== INSIGHTS =====================
    insights = []
    if "operador_exibicao" in df_f.columns and "status" in df_f.columns:
        rank = (
            df_f.groupby("operador_exibicao")
            .agg(total=("status", "count"), realizados=("status", lambda x: (x == "Realizado Total").sum()))
            .reset_index()
        )
        rank["eficiencia"] = (rank["realizados"] / rank["total"] * 100).round(1)
        rank = rank[rank["total"] >= 3]

        if not rank.empty:
            melhor = rank.loc[rank["eficiencia"].idxmax()]
            pior = rank.loc[rank["eficiencia"].idxmin()]
            if melhor["eficiencia"] >= 80:
                insights.append(
                    f"🏆 <strong>{melhor['operador_exibicao']}</strong> lidera em eficiência "
                    f"({melhor['eficiencia']}% com {int(melhor['total'])} lançamentos)."
                )
            if pior["eficiencia"] < 50 and pior["total"] >= 5:
                insights.append(
                    f"⚠️ <strong>{pior['operador_exibicao']}</strong> está com eficiência baixa "
                    f"({pior['eficiencia']}% em {int(pior['total'])} lançamentos)."
                )

    taxa_problema = round(((parciais + nao) / total * 100), 1) if total else 0.0
    if taxa_problema > 35:
        insights.append(
            f"📉 Taxa de problemas (Parcial + Não Realizado) está em <strong>{taxa_problema}%</strong> neste período."
        )

    for ins in insights[:3]:
        st.markdown(f'<div class="insight-box"><span>{ins}</span></div>', unsafe_allow_html=True)

    # ===================== GRÁFICOS =====================
    c1, c2 = st.columns(2)

    with c1:
        with chart_card("🎯", "Distribuição por Status"):
            if "status" in df_f.columns and not df_f["status"].isna().all():
                vc = df_f["status"].value_counts().reset_index()
                vc.columns = ["status", "qtd"]
                fig = px.pie(
                    vc, names="status", values="qtd", color="status",
                    color_discrete_map=CORES_STATUS, hole=0.62,
                )
                fig.update_traces(
                    textposition="inside",
                    textinfo="percent",
                    marker=dict(line=dict(color="#FFFFFF", width=2)),
                    hovertemplate="<b>%{label}</b><br>%{value} lançamentos (%{percent})<extra></extra>",
                )
                fig.add_annotation(
                    text=f"<b style='font-size:24px;color:{COR_AZUL}'>{eficiencia}%</b><br><span style='font-size:11px;color:#94A3B8'>EFICIÊNCIA</span>",
                    x=0.5, y=0.5, showarrow=False, align="center",
                )
                fig = _layout_padrao(fig, 340)
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
                    fig2 = _layout_padrao(fig2, max(340, 30 * len(rank_plot) + 70))
                    fig2.update_yaxes(title="")
                    fig2.update_xaxes(title="Eficiência %", gridcolor="#F1F5F9", range=[0, 112])
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
            fig_comp.update_layout(xaxis_title="", yaxis_title="Lançamentos", legend_title="Status")
            fig_comp.update_xaxes(tickangle=-20)
            fig_comp.update_yaxes(gridcolor="#F1F5F9")
            fig_comp = _layout_padrao(fig_comp, 370)
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
            cli = cli.sort_values("total", ascending=False).head(12)

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
                fig_cli.update_xaxes(tickangle=-25)
                fig_cli = _layout_padrao(fig_cli, 380)
                st.plotly_chart(fig_cli, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sem dados de clientes.")

    with chart_card("📈", "Evolução das Execuções"):
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
                        marker=dict(color=COR_LARANJA, size=8),
                        fill="tozeroy", fillcolor="rgba(255, 146, 0, 0.10)",
                        hovertemplate="<b>%{x}</b><br>Volume: %{y}<extra></extra>",
                    ))
                    fig3.add_trace(go.Scatter(
                        x=efic["dia"], y=efic["eficiencia"], mode="lines+markers", name="Eficiência %",
                        yaxis="y2", line=dict(color=COR_VERDE, width=2.5, dash="dot"), marker=dict(size=7),
                        hovertemplate="<b>%{x}</b><br>Eficiência: %{y}%<extra></extra>",
                    ))
                    fig3.update_layout(
                        yaxis=dict(title="Volume", gridcolor="#F1F5F9"),
                        yaxis2=dict(title="Eficiência %", overlaying="y", side="right", range=[0, 105], showgrid=False),
                        legend=dict(orientation="h", y=-0.22),
                        hovermode="x unified",
                    )
                else:
                    fig3 = go.Figure(data=[go.Scatter(
                        x=serie["dia"], y=serie["quantidade"], mode="lines+markers",
                        line=dict(color=COR_AZUL, width=3, shape="spline"),
                        marker=dict(color=COR_LARANJA, size=9),
                        fill="tozeroy", fillcolor="rgba(255, 146, 0, 0.12)",
                    )])

                fig3 = _layout_padrao(fig3, 320)
                st.plotly_chart(fig3, use_container_width=True, config={"displayModeBar": False})
            else:
                st.info("Sem dados suficientes para a evolução.")

    # ===================== TABELA =====================
    st.markdown('<p class="section-title">📋 Lançamentos filtrados</p>', unsafe_allow_html=True)

    cols = [c for c in ["data_registro", "operador_nome", "cliente_nome", "status", "justificativa"] if c in df_f.columns]

    if cols:
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

        st.caption(f"Exibindo {min(50, len(tabela))} de {len(tabela)} registros")
        st.dataframe(tabela.head(50), use_container_width=True, hide_index=True, height=420)
    else:
        st.info("Sem lançamentos para listar.")