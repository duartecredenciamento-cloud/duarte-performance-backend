import streamlit as st
import requests
import time

API_URL = "https://duarte-performance-backend.onrender.com"

def render_login():
    # CSS Premium Moderno
    st.markdown("""
    <style>
        .login-container {
            max-width: 420px;
            margin: 2rem auto;
            padding: 2.5rem;
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 40px rgba(0, 30, 87, 0.1);
            border-top: 5px solid #FF9200;
        }
        .logo {
            text-align: center;
            margin-bottom: 1.5rem;
        }
        .logo h1 {
            font-size: 2.8rem;
            font-weight: 900;
            background: linear-gradient(90deg, #001E57, #FF9200);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin: 0;
        }
        .subtitle {
            text-align: center;
            color: #64748B;
            font-size: 1.05rem;
            margin-bottom: 2rem;
        }
        .stTextInput > div > div > input {
            border-radius: 12px;
            border: 2px solid #E2E8F0;
            padding: 14px 16px;
            font-size: 1rem;
        }
        .stButton > button {
            background: linear-gradient(135deg, #001E57, #0A2540);
            color: white;
            border-radius: 12px;
            height: 52px;
            font-weight: 700;
            font-size: 1.05rem;
            width: 100%;
        }
        .stButton > button:hover {
            background: linear-gradient(135deg, #FF9200, #E07A00);
            box-shadow: 0 8px 20px rgba(255, 146, 0, 0.4);
        }
    </style>
    """, unsafe_allow_html=True)

    st.markdown('<div class="login-container">', unsafe_allow_html=True)

    # Logo
    st.markdown('<div class="logo"><h1>Duarte Performance</h1></div>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Gestão Operacional Inteligente</p>', unsafe_allow_html=True)

    tab1, tab2 = st.tabs(["🔑 Entrar", "🆕 Solicitar Acesso"])

    with tab1:
        with st.form("login_form"):
            username = st.text_input("Usuário Corporativo", placeholder="ex: admin")
            password = st.text_input("Senha", type="password", placeholder="••••••••")
            submitted = st.form_submit_button("🚀 Entrar no Sistema", use_container_width=True)

            if submitted:
                if not username or not password:
                    st.error("Preencha usuário e senha")
                else:
                    with st.spinner("Autenticando..."):
                        try:
                            resp = requests.post(
                                f"{API_URL}/token",
                                data={"username": username.strip(), "password": password},
                                timeout=15
                            )
                            if resp.status_code == 200:
                                data = resp.json()
                                st.session_state.update({
                                    "token": data["access_token"],
                                    "username": data.get("username"),
                                    "nome": data.get("nome"),
                                    "role": data.get("role", "Operador")
                                })
                                st.success("✅ Login realizado!")
                                time.sleep(0.8)
                                st.rerun()
                            else:
                                st.error("❌ Usuário ou senha incorretos")
                        except:
                            st.error("❌ Erro de conexão com servidor")

    with tab2:
        st.info("Solicitação de acesso enviada para o administrador.")

    st.markdown('</div>', unsafe_allow_html=True)