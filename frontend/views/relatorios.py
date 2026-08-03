import os
import io
import zipfile
import pandas as pd
import requests
import streamlit as st
import plotly.graph_objects as go

# Mesma fonte de dados da Escala Semanal — usada aqui só na aba de Backup,
# pra permitir exportar cronograma junto com os registros, sem duplicar
# nenhuma tabela nova.
from views.escala import get_cronograma_credenciamento

# URL base do backend
API_URL = os.getenv(
    "BACKEND_URL", "https://duarte-performance-backend-production.up.railway.app"
)

# ===================== PALETA DE CORES DUARTE PERFORMANCE =====================
COR_AZUL_MARINHO = "#001E57"
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
}


def _layout_padrao(fig, altura=320):
    """Layout consistente com a identidade visual em qualquer figura Plotly."""
    fig.update_layout(
        height=altura,
        margin=dict(l=10, r=10, t=40, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#334155", size=13),
        title_font=dict(color=COR_AZUL_MARINHO, size=16, family="Inter, sans-serif"),
        legend=dict(orientation="h", yanchor="bottom", y=-0.25, xanchor="center", x=0.5),
    )
    return fig


def _grafico_status(df: pd.DataFrame, titulo: str, altura: int = 300):
    """Gráfico de rosca com a distribuição de status, nas cores da marca.
    Reaproveitado nas três abas (semanal, mensal, personalizado)."""
    if df.empty or "status" not in df.columns:
        st.info("Sem dados suficientes para exibir o gráfico.")
        return

    contagem = df["status"].value_counts().reset_index()
    contagem.columns = ["status", "quantidade"]

    fig = go.Figure(
        data=[
            go.Pie(
                labels=contagem["status"],
                values=contagem["quantidade"],
                hole=0.55,
                marker=dict(
                    colors=[CORES_STATUS.get(s, COR_CINZA) for s in contagem["status"]]
                ),
                textinfo="percent+value",
                textfont=dict(color="white", size=12),
            )
        ]
    )
    fig.update_layout(title=titulo)
    fig = _layout_padrao(fig, altura=altura)
    st.plotly_chart(fig, use_container_width=True)


def _grafico_evolucao(df: pd.DataFrame, titulo: str, altura: int = 260):
    """Linha temporal simples de quantidade de registros por dia."""
    if df.empty or "data_dt" not in df.columns:
        return

    df_validos = df.dropna(subset=["data_dt"]).copy()
    if df_validos.empty:
        return

    df_validos["dia"] = df_validos["data_dt"].dt.date
    serie = df_validos.groupby("dia").size().reset_index(name="quantidade")

    fig = go.Figure(
        data=[
            go.Scatter(
                x=serie["dia"],
                y=serie["quantidade"],
                mode="lines+markers",
                line=dict(color=COR_AZUL_MARINHO, width=3),
                marker=dict(color=COR_LARANJA, size=7),
                fill="tozeroy",
                fillcolor="rgba(255, 146, 0, 0.08)",
            )
        ]
    )
    fig.update_layout(title=titulo)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=True, gridcolor="#F1F5F9")
    fig = _layout_padrao(fig, altura=altura)
    st.plotly_chart(fig, use_container_width=True)


def fetch_report_data():
    """Busca o histórico completo de execuções no backend com suporte a autenticação JWT."""
    token = st.session_state.get("token", "")
    headers = {"Authorization": f"Bearer {token}"} if token else {}

    # Lista de possíveis rotas para resiliência de API
    endpoints = ["/execucoes/", "/registros/", "/apontamentos/"]

    for endpoint in endpoints:
        try:
            res = requests.get(
                f"{API_URL}{endpoint}", headers=headers, timeout=25
            )
            if res.status_code == 200:
                data = res.json()
                if isinstance(data, list):
                    return data
            elif res.status_code == 401:
                st.error(
                    "🔒 Sessão expirada. Por favor, refaça o login no sistema."
                )
                return None
        except Exception:
            continue
    return None


def inject_custom_css():
    """Estilos premium — Relatórios Duarte Performance."""
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
            0%   { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.45); }
            70%  { box-shadow: 0 0 0 12px rgba(255, 146, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
        }
        @keyframes shimmer {
            0%   { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        .report-header {
            background: linear-gradient(-45deg, #001E57, #030A1A, #0A2540, #001233);
            background-size: 300% 300%;
            animation: floatGradient 12s ease infinite, fadeInUp 0.55s ease-out;
            border-radius: 20px;
            padding: 28px 32px;
            color: #FFFFFF;
            border-left: 6px solid #FF9200;
            margin-bottom: 26px;
            box-shadow: 0 16px 40px rgba(0, 30, 87, 0.22);
            position: relative;
            overflow: hidden;
        }
        .report-header::after {
            content: '';
            position: absolute;
            top: -40%;
            right: -10%;
            width: 220px;
            height: 220px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,146,0,0.18) 0%, transparent 70%);
            pointer-events: none;
        }
        .report-header h2 {
            margin: 0;
            font-weight: 900;
            font-size: 1.85rem;
            letter-spacing: -0.5px;
            color: #FFF;
            position: relative;
            z-index: 1;
        }
        .report-header p {
            margin: 8px 0 0 0;
            color: #94A3B8;
            font-size: 0.95rem;
            position: relative;
            z-index: 1;
        }
        .report-badge {
            display: inline-block;
            margin-top: 14px;
            background: #FF9200;
            color: #FFF;
            padding: 6px 14px;
            border-radius: 99px;
            font-weight: 800;
            font-size: 0.72rem;
            letter-spacing: 0.4px;
            animation: pulseGlow 2.2s infinite;
            position: relative;
            z-index: 1;
        }

        .metric-card-summary {
            background: rgba(255, 255, 255, 0.97);
            border-radius: 16px;
            padding: 20px 16px;
            border: 1px solid #E2E8F0;
            text-align: center;
            box-shadow: 0 6px 20px rgba(0, 30, 87, 0.05);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            animation: fadeInUp 0.65s ease-out;
        }
        .metric-card-summary:hover {
            transform: translateY(-5px);
            border-color: rgba(255, 146, 0, 0.45);
            box-shadow: 0 14px 30px rgba(255, 146, 0, 0.12);
        }
        .metric-card-summary h5 {
            color: #64748B;
            margin: 0;
            font-size: 0.75rem;
            text-transform: uppercase;
            font-weight: 800;
            letter-spacing: 0.4px;
        }
        .metric-card-summary h3 {
            color: #001E57;
            margin: 8px 0 0 0;
            font-size: 1.75rem;
            font-weight: 900;
        }
        .metric-card-summary h3.accent {
            color: #FF9200;
        }

        .chart-card {
            background: #FFFFFF;
            padding: 22px;
            border-radius: 18px;
            box-shadow: 0 10px 28px rgba(0, 30, 87, 0.06);
            border: 1px solid #E2E8F0;
            animation: fadeInUp 0.7s ease-out;
            transition: border-color 0.25s ease, box-shadow 0.25s ease;
        }
        .chart-card:hover {
            border-color: rgba(255, 146, 0, 0.35);
            box-shadow: 0 14px 32px rgba(0, 30, 87, 0.1);
        }

        .backup-card {
            background: linear-gradient(135deg, #FFF9F0 0%, #FFF5E6 100%);
            border-left: 4px solid #FF9200;
            border-radius: 14px;
            padding: 18px 20px;
            margin-bottom: 16px;
            animation: fadeInUp 0.6s ease-out;
            box-shadow: 0 4px 16px rgba(255, 146, 0, 0.08);
        }

        .filter-bar {
            background: #F8FAFC;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 14px 16px;
            margin-bottom: 18px;
            animation: fadeInUp 0.5s ease-out;
        }

        .section-title {
            color: #001E57;
            font-weight: 800;
            font-size: 1.1rem;
            margin: 8px 0 14px 0;
            letter-spacing: -0.2px;
        }

        /* Botões da área de relatório */
        div[data-testid="stHorizontalBlock"] .stButton > button {
            border-radius: 12px !important;
            font-weight: 700 !important;
            transition: all 0.25s ease !important;
        }
        div[data-testid="stHorizontalBlock"] .stButton > button:hover {
            transform: translateY(-2px);
            box-shadow: 0 8px 20px rgba(255, 146, 0, 0.25) !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_relatorios():
    inject_custom_css()

    st.markdown(
        """
    <div class="report-header">
        <h2>📄 Relatórios Operacionais & Auditoria</h2>
        <p>
            Consolidação de desempenho · bases por período · rastreio de lançamentos
        </p>
        <span class="report-badge">⚡ PERFORMANCE · TEMPO REAL</span>
    </div>
    """,
        unsafe_allow_html=True,
    )

    with st.spinner("⏳ Carregando histórico e gerando consolidados..."):
        dados = fetch_report_data()

    if dados is None:
        st.error(
            "❌ Falha na conexão: Não foi possível obter os dados do relatório"
            " no backend."
        )
        st.info(
            "💡 **Dica de Diagnóstico:** Verifique se sua sessão não expirou ou"
            " tente novamente após o servidor do Render responder."
        )
        return

    if not dados:
        st.warning(
            "ℹ️ Nenhum registro operacional encontrado no banco de dados."
        )
        return

    df = pd.DataFrame(dados)

    # Tratamento flexível de datas.
    # Importante: se nenhuma coluna de data for encontrada, NÃO preenchemos
    # com "agora" pra todas as linhas (isso quebrava silenciosamente os
    # filtros de Semana/Mês, fazendo tudo parecer "de hoje"). Em vez disso,
    # deixamos a coluna vazia (NaT) e avisamos o usuário.
    date_col = None
    for candidate in ["created_at", "data_registro", "data", "created_date"]:
        if candidate in df.columns:
            date_col = candidate
            break

    if date_col:
        df["data_dt"] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        df["data_dt"] = pd.NaT
        st.warning(
            "⚠️ Não foi encontrada uma coluna de data reconhecida nos"
            " registros. Os filtros de período (Semanal/Mensal) podem não"
            " funcionar corretamente."
        )

    # Normalização de colunas exibidas
    cols_display = [
        c
        for c in [
            "id",
            "cliente",
            "status",
            "observacoes",
            "justificativa",
            date_col,
        ]
        if c in df.columns
    ]

    def _ocultar_observacao_quando_total(df_in: pd.DataFrame) -> pd.DataFrame:
        """A observação/justificativa só faz sentido pra status que não são
        'Realizado Total' (é justamente o motivo da pendência). Mesmo que o
        campo venha vazio do backend nesses casos, aqui garantimos que nunca
        apareça nada na tela pra linhas 'Realizado Total' — só na exibição,
        o CSV de exportação mantém os dados originais intactos para auditoria."""
        if df_in.empty or "status" not in df_in.columns:
            return df_in
        df_out = df_in.copy()
        for col in ["observacoes", "justificativa"]:
            if col in df_out.columns:
                df_out.loc[df_out["status"] == "Realizado Total", col] = ""
        return df_out


    # --- ABAS DE NAVEGAÇÃO DOS RELATÓRIOS ---
    aba_semanal, aba_mensal, aba_personalizado, aba_exportar, aba_backup = st.tabs([
        "📅 Visão Semanal",
        "🗓️ Visão Mensal",
        "🔍 Filtro Personalizado",
        "📥 Exportar Dados",
        "🗄️ Backup Completo",
    ])

    # ----------------------------------------------------
    # 1. ABA SEMANAL
    # ----------------------------------------------------
    with aba_semanal:
        st.subheader("📊 Relatório Operacional da Semana Atual (Últimos 7 dias)")
        data_limite_semana = pd.Timestamp.now() - pd.Timedelta(days=7)
        df_semanal = df[df["data_dt"] >= data_limite_semana].copy()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                '<div class="metric-card-summary"><h5>Total'
                f" Semana</h5><h3>{len(df_semanal)}</h3></div>",
                unsafe_allow_html=True,
            )
        with c2:
            realizados = (
                len(df_semanal[df_semanal["status"] == "Realizado Total"])
                if "status" in df_semanal.columns
                else 0
            )
            st.markdown(
                '<div class="metric-card-summary"><h5>Realizados</h5><h3'
                f' style="color:#10B981;">{realizados}</h3></div>',
                unsafe_allow_html=True,
            )
        with c3:
            parciais = (
                len(df_semanal[df_semanal["status"] == "Realizado Parcial"])
                if "status" in df_semanal.columns
                else 0
            )
            st.markdown(
                '<div class="metric-card-summary"><h5>Parciais</h5><h3'
                f' style="color:#F59E0B;">{parciais}</h3></div>',
                unsafe_allow_html=True,
            )
        with c4:
            nao_realizados = (
                len(df_semanal[df_semanal["status"] == "Não Realizado"])
                if "status" in df_semanal.columns
                else 0
            )
            st.markdown(
                '<div class="metric-card-summary"><h5>Não Realizados</h5><h3'
                f' style="color:#EF4444;">{nao_realizados}</h3></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráficos: distribuição de status + evolução diária da semana
        g1, g2 = st.columns([1, 1.4])
        with g1:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            _grafico_status(df_semanal, "Distribuição de Status — Semana")
            st.markdown('</div>', unsafe_allow_html=True)
        with g2:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            _grafico_evolucao(df_semanal, "Execuções por Dia — Semana")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(
            df_semanal[cols_display].pipe(_ocultar_observacao_quando_total) if not df_semanal.empty else df_semanal,
            use_container_width=True,
            hide_index=True,
        )

    # ----------------------------------------------------
    # 2. ABA MENSAL
    # ----------------------------------------------------
    with aba_mensal:
        st.subheader("🗓️ Relatório Operacional do Mês Vigente")
        now = pd.Timestamp.now()
        df_mensal = df[
            (df["data_dt"].dt.month == now.month)
            & (df["data_dt"].dt.year == now.year)
        ].copy()

        m1, m2, m3, m4 = st.columns(4)
        with m1:
            st.markdown(
                '<div class="metric-card-summary"><h5>Total'
                f" Mês</h5><h3>{len(df_mensal)}</h3></div>",
                unsafe_allow_html=True,
            )
        with m2:
            realizados_m = (
                len(df_mensal[df_mensal["status"] == "Realizado Total"])
                if "status" in df_mensal.columns
                else 0
            )
            st.markdown(
                '<div class="metric-card-summary"><h5>Realizados</h5><h3'
                f' style="color:#10B981;">{realizados_m}</h3></div>',
                unsafe_allow_html=True,
            )
        with m3:
            parciais_m = (
                len(df_mensal[df_mensal["status"] == "Realizado Parcial"])
                if "status" in df_mensal.columns
                else 0
            )
            st.markdown(
                '<div class="metric-card-summary"><h5>Parciais</h5><h3'
                f' style="color:#F59E0B;">{parciais_m}</h3></div>',
                unsafe_allow_html=True,
            )
        with m4:
            taxa_m = (
                ((realizados_m / len(df_mensal)) * 100)
                if len(df_mensal) > 0
                else 0.0
            )
            st.markdown(
                '<div class="metric-card-summary"><h5>Taxa Eficiência</h5><h3'
                f' style="color:#FF9200;">{taxa_m:.1f}%</h3></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        g3, g4 = st.columns([1, 1.4])
        with g3:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            _grafico_status(df_mensal, "Distribuição de Status — Mês")
            st.markdown('</div>', unsafe_allow_html=True)
        with g4:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            _grafico_evolucao(df_mensal, "Execuções por Dia — Mês")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(
            df_mensal[cols_display].pipe(_ocultar_observacao_quando_total) if not df_mensal.empty else df_mensal,
            use_container_width=True,
            hide_index=True,
        )

    # ----------------------------------------------------
    # 3. ABA FILTRO PERSONALIZADO
    # ----------------------------------------------------
    with aba_personalizado:
        st.subheader("🔍 Pesquisa Avançada e Filtros Customizados")

        f_col1, f_col2, f_col3 = st.columns(3)
        with f_col1:
            cliente_filtro = st.text_input(
                "Filtrar por Cliente/Provedor:",
                placeholder="Digite o nome do cliente...",
            )
        with f_col2:
            status_opcoes = (
                ["Todos"] + sorted(list(df["status"].dropna().unique()))
                if "status" in df.columns
                else ["Todos"]
            )
            status_filtro = st.selectbox("Filtrar por Status:", status_opcoes)
        with f_col3:
            dt_inicio = st.date_input(
                "Data Inicial:",
                value=pd.Timestamp.now() - pd.Timedelta(days=30),
            )

        df_custom = df.copy()
        if cliente_filtro and "cliente" in df_custom.columns:
            df_custom = df_custom[
                df_custom["cliente"]
                .astype(str)
                .str.contains(cliente_filtro, case=False, na=False)
            ]
        if status_filtro != "Todos" and "status" in df_custom.columns:
            df_custom = df_custom[df_custom["status"] == status_filtro]
        if "data_dt" in df_custom.columns:
            df_custom = df_custom[df_custom["data_dt"].dt.date >= dt_inicio]

        st.markdown("<br>", unsafe_allow_html=True)

        g5, g6 = st.columns([1, 1.4])
        with g5:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            _grafico_status(df_custom, "Distribuição de Status — Filtro")
            st.markdown('</div>', unsafe_allow_html=True)
        with g6:
            st.markdown('<div class="chart-card">', unsafe_allow_html=True)
            _grafico_evolucao(df_custom, "Execuções por Dia — Filtro")
            st.markdown('</div>', unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        st.dataframe(
            df_custom[cols_display].pipe(_ocultar_observacao_quando_total) if not df_custom.empty else df_custom,
            use_container_width=True,
            hide_index=True,
        )

    # ----------------------------------------------------
    # 4. ABA EXPORTAR DADOS
    # ----------------------------------------------------
    with aba_exportar:
        st.subheader("📥 Exportação para Auditoria e Excel")
        st.write(
            "Baixe a base completa de apontamentos operacionais no formato CSV"
            " para análise offline."
        )

        csv_data = df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="📄 Baixar Relatório Completo em CSV",
            data=csv_data,
            file_name=(
                "relatorio_operacional_duarte_"
                f"{pd.Timestamp.now().strftime('%Y%m%d')}.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )

    # ----------------------------------------------------
    # 5. ABA BACKUP COMPLETO (NOVA)
    # ----------------------------------------------------
    with aba_backup:
        st.subheader("🗄️ Backup Completo do Sistema")

        st.markdown(
            """
            <div class="backup-card">
                <strong>O que este backup inclui:</strong>
                <ul style="margin: 8px 0 0 0;">
                    <li>Todos os registros de execução diária (histórico completo)</li>
                    <li>A matriz de escala/cronograma atual</li>
                </ul>
                <p style="margin: 10px 0 0 0; color: #64748B; font-size: 0.85rem;">
                    Recomendado: gere um backup periodicamente (ex: semanal) e
                    guarde o arquivo em um local seguro (Google Drive, OneDrive, etc.),
                    como camada extra de segurança além do banco de dados principal.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")

        # Monta o ZIP em memória com os dois CSVs (registros + cronograma)
        buffer_zip = io.BytesIO()
        try:
            df_cronograma = get_cronograma_credenciamento()
        except Exception:
            df_cronograma = pd.DataFrame()

        with zipfile.ZipFile(buffer_zip, "w", zipfile.ZIP_DEFLATED) as zip_arquivo:
            zip_arquivo.writestr(
                f"registros_{timestamp}.csv",
                df.to_csv(index=False).encode("utf-8"),
            )
            if not df_cronograma.empty:
                zip_arquivo.writestr(
                    f"cronograma_{timestamp}.csv",
                    df_cronograma.to_csv(index=False).encode("utf-8"),
                )

        buffer_zip.seek(0)

        b1, b2, b3 = st.columns(3)
        with b1:
            st.markdown(
                f'<div class="metric-card-summary"><h5>Registros no Backup</h5>'
                f'<h3>{len(df)}</h3></div>',
                unsafe_allow_html=True,
            )
        with b2:
            st.markdown(
                f'<div class="metric-card-summary"><h5>Linhas de Cronograma</h5>'
                f'<h3>{len(df_cronograma)}</h3></div>',
                unsafe_allow_html=True,
            )
        with b3:
            st.markdown(
                f'<div class="metric-card-summary"><h5>Gerado em</h5>'
                f'<h3 style="font-size:1.1rem;">{pd.Timestamp.now().strftime("%d/%m %H:%M")}</h3></div>',
                unsafe_allow_html=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)

        st.download_button(
            label="🗄️ Baixar Backup Completo (ZIP)",
            data=buffer_zip,
            file_name=f"backup_duarte_performance_{timestamp}.zip",
            mime="application/zip",
            use_container_width=True,
            type="primary",
        )


if __name__ == "__main__":
    render_relatorios()