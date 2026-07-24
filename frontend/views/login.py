import streamlit as st
import requests
import time
import os

API_URL = os.getenv("BACKEND_URL", "https://duarte-performance-backend.onrender.com")

def render_login():
    st.set_page_config(page_title="Duarte Performance", layout="wide")
    
    # Estilização CSS
    st.markdown("""
    <style>
        .big-title { font-size: 3.5rem; font-weight: 900; color: #001E57; margin: 0; }
        .orange { color: #FF9200; }
        .hero-box {
            background: linear-gradient(145deg, #001E57, #030A1A);
            padding: 40px;
            border-radius: 20px;
            color: white;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1.1, 1])

    with col1:
        st.markdown('<div class="hero-box">', unsafe_allow_html=True)
        st.markdown('<h1 class="big-title">Duarte <span class="orange">Performance</span></h1>', unsafe_allow_html=True)
        st.subheader("Sistema Operacional v2.4")
        st.write("Central de Inteligência Operacional & Credenciamento de Saúde")
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.markdown("### Acessar Conta")
        username = st.text_input("Usuário", placeholder="admin", key="u")
        password = st.text_input("Senha", type="password", placeholder="Duarte1234#", key="p")

        if st.button("🚀 ENTRAR NA PLATAFORMA", type="primary", use_container_width=True):
            if username and password:
                try:
                    resp = requests.post(
                        f"{API_URL}/token", 
                        data={"username": username.strip(), "password": password.strip()}
                    )
                    
                    if resp.status_code == 200:
                        data = resp.json()
                        
                        # 🔑 REGISTRA A SESSÃO NO STREAMLIT
                        st.session_state["token"] = data.get("access_token")
                        st.session_state["user_role"] = data.get("role")
                        st.session_state["user_nome"] = data.get("nome")
                        st.session_state["username"] = data.get("username")
                        st.session_state["logged_in"] = True
                        
                        st.success(f"✅ Autenticado com sucesso! Bem-vindo(a), {data.get('nome', username)}.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error("❌ Credenciais erradas ou usuário não cadastrado.")
                except Exception as e:
                    st.error(f"Erro de conexão com o backend: {e}")
            else:
                st.warning("Preencha os campos de usuário e senha.")

    st.caption("Ainda com problema? Tente reiniciar o Streamlit (Ctrl+C e rode novamente)")