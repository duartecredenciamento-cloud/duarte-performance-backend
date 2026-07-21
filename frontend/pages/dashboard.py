import streamlit as st

def render_dashboard():
    st.header("📈 Dashboard Gerencial")
    df = st.session_state.get("df_apontamentos", None)
    
    if df is None or df.empty:
        st.info("Sem dados ainda.")
        return
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total", len(df))
    col2.metric("Realizado Total", (df['STATUS'] == 'Realizado Total').sum())
    col3.metric("Realizado Parcial", (df['STATUS'] == 'Realizado Parcial').sum())
    col4.metric("Não Realizado", (df['STATUS'] == 'Não Realizado').sum())
    
    st.subheader("Gráficos")
    st.bar_chart(df['STATUS'].value_counts())