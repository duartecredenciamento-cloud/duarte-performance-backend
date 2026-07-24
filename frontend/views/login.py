import streamlit as st
import requests
import time

API_URL = "https://duarte-performance-backend.onrender.com"

def render_login():
    st.markdown("""
    <style>
        .main-login {
            background: linear-gradient(135deg, #001E57 0%, #0A2540 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-card {
            background: white;
            border-radius: 20px;
            box-shadow: 0 25px 50px rgba(0, 30, 87, 0.15);
            padding: 40px 35px;
            max-width: 420px;
            width: 100%;
        }
        .logo-duarte {
            font-size: 2.8rem;
            font-weight: 900;
            color: #001E57;
            text-align: center;
            margin-bottom: 8px;
        }
        .logo-duarte span {
            color: #FF9200;
        }
        .tagline {
            text-align: center;
            color: #64748B;
            font-size: 1.05rem;
            margin-bottom: 30px;
        }
        .stTextInput input {
            border-radius: 12px;
            padding: 14px 16px;
            border: 2px solid #E2E8F0;
        }
        .stButton button {
            background: linear-gradient(135deg, #FF9200, #E07A00);
            color: white;
            height: 52px;
            font-weight: 700;
            border-radius: 12px;
            font-size: 1.05rem;
        }
    </style>
    """, unsafe_allow_html=True)

    # Centralizar
    col = st.columns([1, 2, 1])[1]

    with col:
        st.markdown('<div class="login-card">', unsafe_allow_html=True)

        st.markdown('<div class="logo-duarte">Duarte <span>Performance</span></div>', unsafe_allow_html=True)
        st.markdown('<p class="tagline">Gestão Operacional Inteligente</p>', unsafe_allow_html=True)

        username = st.text_input("Usuário Corporativo", placeholder="admin")
        password = st.text_input("Senha", type="password", placeholder="Duarte1234#")

        if st.button("🚀 Entrar no Sistema", use_container_width=True):
            if username and password:
                with st.spinner("Autenticando..."):
                    try:
                        resp = requests.post(
                            f"{API_URL}/token",
                            data={"username": username.strip(), "password": password},
                            timeout=12
                        )
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.update({
                                "token": data["access_token"],
                                "username": username,
                                "nome": data.get("nome", username),
                                "role": data.get("role", "Operador")
                            })
                            st.success("✅ Bem-vindo!")
                            time.sleep(0.8)
                            st.rerun()
                        else:
                            st.error("❌ Usuário ou senha incorretos")
                    except:
                        st.error("❌ Servidor indisponível. Tente novamente.")
            else:
                st.warning("Preencha todos os campos")

        st.markdown('</div>', unsafe_allow_html=True)

    st.markdown("<br><br><p style='text-align:center; color:#94A3B8;'>Duarte Performance © 2026</p>", unsafe_allow_html=True)