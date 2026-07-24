import os
import pandas as pd
import requests
import streamlit as st

# URL base do backend
API_URL = os.getenv(
    "BACKEND_URL", "https://duarte-performance-backend.onrender.com"
)


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
    """Injeta estilos visuais alinhados à identidade Duarte Performance."""
    st.markdown(
        """
    <style>
        .report-header {
            background: linear-gradient(-45deg, #001E57, #0A2540, #001233);
            border-radius: 16px;
            padding: 24px 32px;
            color: #FFFFFF;
            border-left: 6px solid #FF9200;
            margin-bottom: 24px;
            box-shadow: 0 10px 25px rgba(0, 30, 87, 0.15);
        }
        
        .metric-card-summary {
            background: #FFFFFF;
            border-radius: 12px;
            padding: 16px;
            border: 1px solid #E2E8F0;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        }
        
        .metric-card-summary h5 {
            color: #64748B;
            margin: 0;
            font-size: 0.8rem;
            text-transform: uppercase;
            font-weight: 700;
        }
        
        .metric-card-summary h3 {
            color: #001E57;
            margin: 6px 0 0 0;
            font-size: 1.6rem;
            font-weight: 800;
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
        <h2 style="margin:0; font-weight: 900; font-size: 1.8rem; color: #FFF;">
            📄 Relatórios Operacionais & Auditoria Consolidados
        </h2>
        <p style="margin: 6px 0 0 0; color: #CBD5E1; font-size: 0.9rem;">
            Extração de bases, consolidação temporal (Semanal / Mensal / Personalizado) e auditoria de registros.
        </p>
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

    # Tratamento flexível de datas
    date_col = None
    for candidate in ["created_at", "data_registro", "data", "created_date"]:
        if candidate in df.columns:
            date_col = candidate
            break

    if date_col:
        df["data_dt"] = pd.to_datetime(df[date_col], errors="coerce")
    else:
        df["data_dt"] = pd.Timestamp.now()

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
    aba_semanal, aba_mensal, aba_personalizado, aba_exportar = st.tabs([
        "📅 Visão Semanal",
        "🗓️ Visão Mensal",
        "🔍 Filtro Personalizado",
        "📥 Exportar Dados",
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


if __name__ == "__main__":
    render_relatorios()