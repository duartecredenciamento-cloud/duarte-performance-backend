import streamlit as st
import pandas as pd
from datetime import datetime

def render_relatorios(api_get):
    # Header com Identidade Visual
    st.markdown("""
    <div style="margin-bottom: 20px;">
        <h1 style="color: #001E57; font-weight: 900; font-size: 2.2rem; margin-bottom: 4px;">
            📑 Relatórios Operacionais
        </h1>
        <p style="color: #64748B; font-size: 1rem; margin: 0;">
            Extração de bases, filtros consolidados e auditoria de registros.
        </p>
    </div>
    """, unsafe_allow_html=True)

    with st.spinner("Buscando registros na API..."):
        resp_reg = api_get("/registros/")

    if not resp_reg or resp_reg.status_code != 200:
        st.error("⚠️ Falha ao obter dados do relatório. Verifique a conexão com o backend.")
        return

    dados = resp_reg.json()
    df_raw = pd.DataFrame(dados) if dados else pd.DataFrame()

    if df_raw.empty:
        st.info("ℹ️ Nenhum dado disponível para geração de relatórios no momento.")
        return

    # Normalização preventiva de nomes de colunas
    col_map = {col: col.lower().strip() for col in df_raw.columns}
    df = df_raw.copy()

    # Mapeamento para garantir nomes amigáveis
    col_status = next((c for c in df.columns if c.lower() in ['status', 'st']), df.columns[0])
    col_data = next((c for c in df.columns if 'data' in c.lower() or 'created' in c.lower()), None)
    col_operador = next((c for c in df.columns if 'operador' in c.lower() or 'usuario' in c.lower() or 'user' in c.lower()), None)

    # Convertendo data se existir
    if col_data:
        try:
            df[col_data] = pd.to_datetime(df[col_data], errors='coerce')
        except Exception:
            pass

    # ================= 1. PAINEL DE FILTROS AVANÇADOS =================
    with st.expander("🎯 **Painel de Filtros Avançados**", expanded=True):
        f_col1, f_col2, f_col3 = st.columns(3)

        # Filtro por Status
        with f_col1:
            opcoes_status = sorted(df[col_status].astype(str).unique().tolist()) if col_status in df.columns else []
            status_sel = st.multiselect("Filtrar por Status:", opcoes_status, placeholder="Todos os status")

        # Filtro por Operador
        with f_col2:
            if col_operador and col_operador in df.columns:
                opcoes_op = sorted(df[col_operador].astype(str).unique().tolist())
                operador_sel = st.multiselect("Filtrar por Operador:", opcoes_op, placeholder="Todos os operadores")
            else:
                operador_sel = []
                st.text_input("Operador:", value="N/A", disabled=True)

        # Filtro por Busca Global
        with f_col3:
            busca_texto = st.text_input("🔎 Pesquisa Global no Relatório:", placeholder="Digite cliente, ID ou termo...")

    # Aplicando os filtros ao DataFrame
    df_filtrado = df.copy()

    if status_sel:
        df_filtrado = df_filtrado[df_filtrado[col_status].astype(str).isin(status_sel)]

    if operador_sel and col_operador:
        df_filtrado = df_filtrado[df_filtrado[col_operador].astype(str).isin(operador_sel)]

    if busca_texto:
        mask = df_filtrado.astype(str).apply(lambda row: row.str.contains(busca_texto, case=False, na=False).any(), axis=1)
        df_filtrado = df_filtrado[mask]

    # ================= 2. CARDS RESUMO DO RELATÓRIO =================
    st.markdown("<br>", unsafe_allow_html=True)
    c_kpi1, c_kpi2, c_kpi3 = st.columns(3)

    total_filtrado = len(df_filtrado)
    concluidos = len(df_filtrado[df_filtrado[col_status].astype(str).str.contains("Realizado Total|Concluído|OK", case=False, na=False)])
    pendentes = total_filtrado - concluidos

    with c_kpi1:
        st.markdown(f"""
        <div style="background: #FFFFFF; border-radius: 12px; padding: 15px; border-left: 5px solid #001E57; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
            <div style="color: #64748B; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Registros Encontrados</div>
            <div style="color: #001E57; font-size: 1.6rem; font-weight: 900;">{total_filtrado}</div>
        </div>
        """, unsafe_allow_html=True)

    with c_kpi2:
        st.markdown(f"""
        <div style="background: #FFFFFF; border-radius: 12px; padding: 15px; border-left: 5px solid #10B981; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
            <div style="color: #64748B; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Concluídos na Seleção</div>
            <div style="color: #10B981; font-size: 1.6rem; font-weight: 900;">{concluidos}</div>
        </div>
        """, unsafe_allow_html=True)

    with c_kpi3:
        st.markdown(f"""
        <div style="background: #FFFFFF; border-radius: 12px; padding: 15px; border-left: 5px solid #FF9200; box-shadow: 0 4px 12px rgba(0,0,0,0.03);">
            <div style="color: #64748B; font-size: 0.8rem; font-weight: 700; text-transform: uppercase;">Pendentes / Outros</div>
            <div style="color: #FF9200; font-size: 1.6rem; font-weight: 900;">{pendentes}</div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ================= 3. AÇÕES DE EXPORTAÇÃO E TABELA =================
    header_col1, header_col2 = st.columns([3, 1])

    with header_col1:
        st.markdown("### 📋 Base de Dados Consolidadas")

    with header_col2:
        # Exportação para CSV com UTF-8-SIG para Excel abrir perfeito no Windows
        csv_data = df_filtrado.to_csv(index=False, sep=";", encoding="utf-8-sig").encode("utf-8-sig")
        data_hoje = datetime.now().strftime("%Y_%m_%d")

        st.download_button(
            label="📥 Baixar em Excel/CSV",
            data=csv_data,
            file_name=f"relatorio_duarte_{data_hoje}.csv",
            mime="text/csv",
            use_container_width=True
        )

    # Exibição da Tabela Customizada
    st.dataframe(
        df_filtrado,
        use_container_width=True,
        hide_index=True
    )