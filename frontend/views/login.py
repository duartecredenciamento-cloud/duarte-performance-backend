import streamlit as st
import requests
import time

API_URL = "https://duarte-performance-backend.onrender.com"

def render_login():
    st.markdown("""
    <style>
        .hero {
            background: linear-gradient(135deg, #001E57 0%, #0A2540 100%);
            padding: 60px 40px;
            border-radius: 24px;
            color: white;
            text-align: center;
            margin-bottom: 30px;
        }
        .logo {
            font-size: 3.2rem;
            font-weight: 900;
            background: linear-gradient(90deg, #FF9200, white);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .login-box {
            background: white;
            padding: 40px;
            border-radius: 20px;
            box-shadow: 0 20px 50px rgba(0,30,87,0.1);
            max-width: 420px;
            margin: 0 auto;
        }
        .stTextInput input {
            border-radius: 12px;
            padding: 14px;
        }
        .stButton button {
            background: linear-gradient(135deg, #FF9200, #E07A00);
            color: white;
            height: 52px;
            font-weight: 700;
            border-radius: 12px;
        }
    </style>
    """, unsafe_allow_html=True)

    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.markdown('<div class="hero"><div class="logo">Duarte</div><h2>Performance</h2><p>Gestão Operacional Inteligente</p></div>', unsafe_allow_html=True)

    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.subheader("Acessar Conta")

        username = st.text_input("Usuário Corporativo", placeholder="admin")
        password = st.text_input("Senha", type="password", placeholder="Duarte1234#")

        if st.button("🚀 Entrar no Sistema", use_container_width=True):
            if username and password:
                with st.spinner("Autenticando..."):
                    try:
                        resp = requests.post(f"{API_URL}/token", data={"username": username, "password": password}, timeout=15)
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.update({
                                "token": data["access_token"],
                                "username": username,
                                "nome": data.get("nome", username),
                                "role": data.get("role", "Operador")
                            })
                            st.success("✅ Login realizado!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Usuário ou senha incorretos")
                    except:
                        st.error("❌ Erro de conexão com o servidor")
            else:
                st.warning("Preencha os campos")

        st.markdown('</div>', unsafe_allow_html=True)