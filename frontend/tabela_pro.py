"""
Tabela premium Duarte Performance — reutilizável em Dashboard, Relatórios, Editor, etc.

Uso:
    from views.tabela_pro import mostrar_tabela, inject_tabela_css

    inject_tabela_css()  # uma vez por tela (ou no app.py global)

    mostrar_tabela(
        df,
        mapa_colunas={
            "data_registro": "Data",
            "operador_nome": "Operador",
            "cliente_nome": "Cliente",
            "status": "Status",
            "justificativa": "Justificativa",
        },
        max_linhas=20,
        titulo="📋 Últimos Lançamentos",
    )
"""

import html
from datetime import datetime

import pandas as pd
import streamlit as st


def inject_tabela_css():
    """CSS avançado da tabela pro (chamar 1x por tela)."""
    st.markdown(
        """
    <style>
        @keyframes tpFadeIn {
            from { opacity: 0; transform: translateY(14px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes tpShine {
            0%   { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        .tp-wrap {
            animation: tpFadeIn 0.55s ease-out;
            border-radius: 18px;
            overflow: hidden;
            border: 1px solid #E2E8F0;
            box-shadow: 0 12px 32px rgba(0, 30, 87, 0.08);
            margin: 8px 0 18px 0;
            background: #FFFFFF;
        }

        .tp-title {
            background: linear-gradient(135deg, #001E57 0%, #0B296B 100%);
            color: #FFFFFF;
            font-weight: 900;
            font-size: 1rem;
            letter-spacing: -0.2px;
            padding: 14px 18px;
            border-bottom: 3px solid #FF9200;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .tp-title span.count {
            margin-left: auto;
            background: rgba(255, 146, 0, 0.2);
            color: #FFB84D;
            font-size: 0.72rem;
            font-weight: 800;
            padding: 4px 10px;
            border-radius: 99px;
            letter-spacing: 0.3px;
        }

        .tp-scroll {
            overflow-x: auto;
            max-height: 480px;
            overflow-y: auto;
        }

        table.tp-table {
            width: 100%;
            border-collapse: collapse;
            font-family: Inter, system-ui, -apple-system, sans-serif;
            font-size: 0.9rem;
        }

        table.tp-table thead th {
            position: sticky;
            top: 0;
            z-index: 2;
            background: linear-gradient(180deg, #001E57 0%, #0A2540 100%);
            color: #FFFFFF;
            font-weight: 800;
            font-size: 0.72rem;
            text-transform: uppercase;
            letter-spacing: 0.55px;
            padding: 12px 14px;
            text-align: left;
            border: none;
            white-space: nowrap;
        }

        table.tp-table tbody td {
            padding: 12px 14px;
            color: #0F172A;
            border-bottom: 1px solid #F1F5F9;
            vertical-align: middle;
            transition: background 0.2s ease;
        }

        table.tp-table tbody tr {
            transition: background 0.2s ease, transform 0.15s ease;
        }
        table.tp-table tbody tr:nth-child(even) td {
            background: #F8FAFC;
        }
        table.tp-table tbody tr:hover td {
            background: rgba(255, 146, 0, 0.10) !important;
        }

        /* Badges de status */
        .tp-badge {
            display: inline-block;
            padding: 4px 10px;
            border-radius: 99px;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.3px;
            white-space: nowrap;
        }
        .tp-badge.ok {
            background: rgba(16, 185, 129, 0.15);
            color: #047857;
            border: 1px solid rgba(16, 185, 129, 0.3);
        }
        .tp-badge.warn {
            background: rgba(245, 158, 11, 0.15);
            color: #B45309;
            border: 1px solid rgba(245, 158, 11, 0.3);
        }
        .tp-badge.danger {
            background: rgba(239, 68, 68, 0.12);
            color: #B91C1C;
            border: 1px solid rgba(239, 68, 68, 0.28);
        }
        .tp-badge.muted {
            background: rgba(100, 116, 139, 0.12);
            color: #475569;
            border: 1px solid rgba(100, 116, 139, 0.25);
        }

        .tp-empty {
            text-align: center;
            padding: 28px 16px;
            color: #64748B;
            font-weight: 600;
        }

        /* Fallback: dataframe nativo também estilizado */
        [data-testid="stDataFrame"],
        [data-testid="stDataFrame"] > div {
            border-radius: 16px !important;
            overflow: hidden !important;
            border: 1px solid #E2E8F0 !important;
            box-shadow: 0 8px 24px rgba(0, 30, 87, 0.06) !important;
        }
        [data-testid="stDataFrame"] thead tr th {
            background: #001E57 !important;
            color: #FFFFFF !important;
            font-weight: 800 !important;
            font-size: 0.78rem !important;
            text-transform: uppercase !important;
            letter-spacing: 0.4px !important;
            border: none !important;
        }
        [data-testid="stDataFrame"] tbody tr:nth-child(even) {
            background: #F8FAFC !important;
        }
        [data-testid="stDataFrame"] tbody tr:hover {
            background: rgba(255, 146, 0, 0.08) !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def _formatar_valor(col: str, valor) -> str:
    if valor is None or (isinstance(valor, float) and pd.isna(valor)):
        return "—"

    texto = str(valor).strip()
    if not texto or texto.lower() in ("nan", "none", "nat"):
        return "—"

    # Data
    col_l = col.lower()
    if "data" in col_l or col_l.endswith("_em") or col_l == "data_registro":
        try:
            dt = pd.to_datetime(valor, errors="coerce")
            if pd.notna(dt):
                return dt.strftime("%d/%m/%Y %H:%M")
        except Exception:
            pass

    # Status com badge
    if col_l == "status" or col_l.endswith("status"):
        mapa = {
            "realizado total": "ok",
            "realizado parcial": "warn",
            "não realizado": "danger",
            "nao realizado": "danger",
            "não se aplica": "muted",
            "nao se aplica": "muted",
        }
        cls = mapa.get(texto.lower(), "muted")
        return f'<span class="tp-badge {cls}">{html.escape(texto)}</span>'

    return html.escape(texto)


def mostrar_tabela(
    df: pd.DataFrame,
    mapa_colunas: dict = None,
    max_linhas: int = 50,
    titulo: str = None,
    colunas: list = None,
    injetar_css: bool = True,
    usar_html: bool = True,
):
    """
    Renderiza tabela premium.

    - mapa_colunas: renomeia colunas técnicas → labels PT
    - colunas: ordem/filtro das colunas (nomes originais do df)
    - usar_html: True = tabela HTML custom (mais bonita)
                 False = st.dataframe com CSS
    """
    if injetar_css:
        inject_tabela_css()

    if df is None or df.empty:
        if titulo:
            st.markdown(
                f'<div class="tp-wrap"><div class="tp-title">{html.escape(titulo)}</div>'
                f'<div class="tp-empty">Nenhum registro para exibir.</div></div>',
                unsafe_allow_html=True,
            )
        else:
            st.info("Nenhum dado para exibir.")
        return

    tabela = df.copy()

    if colunas:
        exist = [c for c in colunas if c in tabela.columns]
        tabela = tabela[exist]

    # Formata data_registro antes do rename (se existir)
    for c in list(tabela.columns):
        if "data" in c.lower() and pd.api.types.is_datetime64_any_dtype(tabela[c]):
            pass  # formata no HTML

    if mapa_colunas:
        tabela = tabela.rename(columns=mapa_colunas)

    total = len(tabela)
    tabela = tabela.head(max_linhas)

    if not usar_html:
        if titulo:
            st.markdown(f"**{titulo}**")
        st.dataframe(tabela, use_container_width=True, hide_index=True)
        return

    # ----- HTML premium -----
    headers = list(tabela.columns)
    thead = "".join(f"<th>{html.escape(str(h))}</th>" for h in headers)

    rows_html = []
    for _, row in tabela.iterrows():
        cells = []
        for h in headers:
            # tenta achar nome original para detectar status/data
            cells.append(f"<td>{_formatar_valor(str(h), row[h])}</td>")
        rows_html.append("<tr>" + "".join(cells) + "</tr>")

    titulo_html = ""
    if titulo:
        titulo_html = (
            f'<div class="tp-title">{html.escape(titulo)}'
            f'<span class="count">{total} registro{"s" if total != 1 else ""}</span></div>'
        )

    html_final = f"""
    <div class="tp-wrap">
        {titulo_html}
        <div class="tp-scroll">
            <table class="tp-table">
                <thead><tr>{thead}</tr></thead>
                <tbody>
                    {''.join(rows_html)}
                </tbody>
            </table>
        </div>
    </div>
    """
    st.markdown(html_final, unsafe_allow_html=True)


# Atalho pronto pro Dashboard / Relatórios
MAPA_LANCAMENTOS = {
    "data_registro": "Data",
    "operador_nome": "Operador",
    "cliente_nome": "Cliente",
    "status": "Status",
    "justificativa": "Justificativa",
}


def mostrar_lancamentos(df: pd.DataFrame, max_linhas: int = 20, titulo: str = "📋 Últimos Lançamentos"):
    """Atalho específico para tabela de lançamentos."""
    cols = [c for c in MAPA_LANCAMENTOS.keys() if c in df.columns]
    if "data_registro" in df.columns:
        df = df.sort_values("data_registro", ascending=False)
    mostrar_tabela(
        df,
        mapa_colunas=MAPA_LANCAMENTOS,
        colunas=cols,
        max_linhas=max_linhas,
        titulo=titulo,
    )