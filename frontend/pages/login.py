import streamlit as st
import requests

def render_login():
    st.title("Duarte Performance")
    st.markdown("### Login")

    username = st.text_input("Usuário")
    senha = st.text_input("Senha", type="password")

    if st.button("Entrar", type="primary"):
        try:
            resp = requests.post("https://duarte-performance-backend.onrender.com/token", 
                               data={"username": username, "password": senha})
            if resp.status_code == 200:
                data = resp.json()
                st.session_state.logged_in = True
                st.session_state.user = data.get("nome", username)
                st.session_state.role = data.get("role", "Operador")
                st.success("Login realizado!")
                st.rerun()
            else:
                st.error("Usuário ou senha incorretos")
        except:
            st.error("Erro de conexão")