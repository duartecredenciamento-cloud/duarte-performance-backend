import streamlit as st
from datetime import datetime
import pandas as pd

def render_escala():
    st.header("🗓️ Escala Semanal")
    
    if st.session_state.df_escala.empty:
        st.info("Nenhuma escala importada.")
    else:
        st.dataframe(st.session_state.df_escala, use_container_width=True)
    
    st.subheader("Adicionar Item")
    with st.form("add_escala"):
        col1, col2 = st.columns(2)
        data = col1.date_input("Data", datetime.now())
        operador = col2.selectbox("Operador", st.session_state.equipe)
        cliente = st.text_input("Cliente")
        
        if st.form_submit_button("Adicionar"):
            if cliente:
                novo = {'DATA': data.strftime('%Y-%m-%d'), 'OPERADOR': operador, 'CLIENTE': cliente}
                st.session_state.df_escala = pd.concat([st.session_state.df_escala, pd.DataFrame([novo])], ignore_index=True)
                st.success("Adicionado!")
                st.rerun()