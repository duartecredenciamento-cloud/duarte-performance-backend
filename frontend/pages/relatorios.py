import streamlit as st

def render_relatorios():
    st.header("📊 Relatórios")
    df = st.session_state.get("df_apontamentos", None)
    if df is None or df.empty:
        st.warning("Sem dados.")
        return
    st.dataframe(df, use_container_width=True)