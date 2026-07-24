import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

def render_dashboard(api_get):
    # ===================== CSS PREMIUM =====================
    st.markdown("""
    <style>
        .dash-header {
            background: linear-gradient(135deg, #001E57 0%, #0A2540 100%);
            padding: 35px 30px;
            border-radius: 20px;
            color: white;
            margin-bottom: 30px;
            box-shadow: 0 15px 35px rgba(0, 30, 87, 0.15);
            animation: fadeIn 0.8s ease-out;
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }
        .metric-card {
            background: white;
            padding: 24px;
            border-radius: 16px;
            box-shadow: 0 8px 25px rgba(0,0,0,0.06);
            text-align: center;
            transition: all 0.3s ease;
            border: 1px solid #E2E8F0;
        }
        .metric-card:hover {
            transform: translateY(-6px);
            box-shadow: 0 15px 30px rgba(255, 146, 0, 0.15);
            border-color: #FF9200;
        }
        .metric-value {
            font-size: 2.4rem;
            font-weight: 900;
            color: #001E57;
            margin: 0;
        }
        .metric-label {
            color: #64748B;
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.85rem;
            letter-spacing: 0.5px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Header
    nome = st.session_state.get("nome", "Usuário")
    role = st.session_state.get("role", "Operador")

    st.markdown(f"""
    <div class="dash-header">
        <h1 style="margin:0; font-size:2.4rem;">📊 Dashboard Gerencial</h1>
        <p style="margin:10px 0 0 0; opacity:0.9;">Bem-vindo, <strong>{nome}</strong> • {role}</p>
    </div>
    """, unsafe_allow_html=True)

    # Carregar dados
    resposta = api_get("/registros/")

    if resposta is None or resposta.status_code != 200:
        st.error("Não foi possível carregar os dados.")
        return

    registros = resposta.json()
    if not registros:
        st.info("Nenhum registro encontrado ainda.")
        return

    df = pd.DataFrame(registros)

    if "data_registro" in df.columns:
        df["data_registro"] = pd.to_datetime(df["data_registro"], errors="coerce")

    # Filtro
    periodo = st.selectbox("Período", ["Hoje", "Últimos 7 dias", "Últimos 30 dias", "Todos"], index=1)

    hoje = datetime.now()
    if periodo == "Hoje":
        df = df[df["data_registro"].dt.date == hoje.date()]
    elif periodo == "Últimos 7 dias":
        df = df[df["data_registro"] >= hoje - timedelta(days=7)]
    elif periodo == "Últimos 30 dias":
        df = df[df["data_registro"] >= hoje - timedelta(days=30)]

    # Métricas
    total = len(df)
    realizados = len(df[df["status"] == "Realizado Total"])
    parciais = len(df[df["status"] == "Realizado Parcial"])
    pendentes = len(df[df["status"] == "Não Realizado"])
    eficiencia = round((realizados / total * 100), 1) if total > 0 else 0

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        st.markdown(f'<div class="metric-card"><div class="metric-value">{total}</div><div class="metric-label">Total Execuções</div></div>', unsafe_allow_html=True)

    with c2:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#10B981">{realizados}</div><div class="metric-label">Realizados</div></div>', unsafe_allow_html=True)

    with c3:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#F59E0B">{parciais}</div><div class="metric-label">Parciais</div></div>', unsafe_allow_html=True)

    with c4:
        st.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#FF9200">{eficiencia}%</div><div class="metric-label">Eficiência</div></div>', unsafe_allow_html=True)

    st.divider()

    # Gráficos e Tabela
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📊 Status")
        if not df.empty:
            st.bar_chart(df["status"].value_counts())

    with col2:
        st.subheader("👥 Por Operador")
        if "operador_nome" in df.columns and not df.empty:
            st.bar_chart(df["operador_nome"].value_counts())

    st.divider()

    st.subheader("📋 Últimos Lançamentos")
    colunas = ["data_registro", "operador_nome", "cliente_nome", "status", "justificativa"]
    colunas_exist = [c for c in colunas if c in df.columns]

    st.dataframe(
        df[colunas_exist].sort_values("data_registro", ascending=False).head(15),
        use_container_width=True,
        hide_index=True
    )