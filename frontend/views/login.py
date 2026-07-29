import streamlit as st
import requests
import time
import os

API_URL = os.getenv(
    "BACKEND_URL",
    "https://duarte-performance-backend-production.up.railway.app"
)


def render_login():

    st.markdown(
        """
        <style>
        .login-title{
            text-align:center;
            font-size:38px;
            font-weight:900;
            color:#001E57;
            margin-bottom:5px;
        }
        .login-title span{
            color:#FF9200;
        }
        .login-sub{
            text-align:center;
            color:#64748B;
            font-size:18px;
            margin-bottom:35px;
        }
        div.stButton > button {
            background: linear-gradient(135deg, #FF9200, #E07A00);
            color:white;
            font-weight:800;
            height:50px;
            border-radius:12px;
            border:none;
        }
        div.stButton > button:hover{
            transform:translateY(-2px);
        }
        input{
            border-radius:12px !important;
            height:45px !important;
        }
        </style>
        """,
        unsafe_allow_html=True
    )

    # Controle de telas
    if "tela_login" not in st.session_state:
        st.session_state["tela_login"] = "login"  # login | cadastro | recuperar

    espaco1, centro, espaco2 = st.columns([1, 2, 1])

    with centro:

        st.markdown(
            """
            <div class="login-title">
            Duarte <span>Performance</span>
            </div>
            <div class="login-sub">
            Gestão Operacional Inteligente
            </div>
            """,
            unsafe_allow_html=True
        )

        # ===================== TELA DE LOGIN =====================
        if st.session_state["tela_login"] == "login":

            usuario = st.text_input("Usuário", placeholder="Digite seu usuário", key="login_user")
            senha = st.text_input("Senha", type="password", placeholder="Digite sua senha", key="login_pass")

            if st.button("🚀 Entrar no Sistema", use_container_width=True, key="btn_login"):
                if not usuario or not senha:
                    st.warning("Informe usuário e senha.")
                else:
                    try:
                        with st.spinner("Conectando ao servidor..."):
                            resposta = requests.post(
                                f"{API_URL}/token",
                                data={"username": usuario.strip(), "password": senha},
                                headers={"Content-Type": "application/x-www-form-urlencoded"},
                                timeout=60
                            )

                        if resposta.status_code == 200:
                            dados = resposta.json()
                            st.session_state["token"] = dados["access_token"]
                            st.session_state["username"] = dados.get("username", usuario)
                            st.session_state["nome"] = dados.get("nome", usuario)
                            st.session_state["role"] = dados.get("role", "Operador")
                            st.session_state["user_nome"] = dados.get("nome", usuario)
                            st.session_state["user_role"] = dados.get("role", "Operador")
                            st.success("✅ Login realizado!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error("❌ Usuário ou senha incorretos")
                    except Exception as e:
                        st.error(f"❌ Erro de conexão: {e}")

            st.markdown("<br>", unsafe_allow_html=True)

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("📝 Criar nova conta", use_container_width=True):
                    st.session_state["tela_login"] = "cadastro"
                    st.rerun()
            with col_b:
                if st.button("🔑 Recuperar senha", use_container_width=True):
                    st.session_state["tela_login"] = "recuperar"
                    st.rerun()

        # ===================== TELA DE CADASTRO =====================
        elif st.session_state["tela_login"] == "cadastro":

            st.subheader("📝 Criar nova conta")

            nome = st.text_input("Nome completo *", placeholder="Seu nome completo", key="cad_nome")
            usuario = st.text_input("Usuário *", placeholder="Escolha um usuário", key="cad_user")
            email = st.text_input("E-mail *", placeholder="seu@email.com", key="cad_email")
            telefone = st.text_input("Telefone", placeholder="(11) 99999-9999", key="cad_tel")
            senha = st.text_input("Senha *", type="password", placeholder="Crie uma senha", key="cad_pass")
            senha2 = st.text_input("Confirmar senha *", type="password", placeholder="Repita a senha", key="cad_pass2")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 Cadastrar", use_container_width=True, type="primary"):
                    if not nome or not usuario or not email or not senha:
                        st.warning("Preencha os campos obrigatórios.")
                    elif senha != senha2:
                        st.error("As senhas não coincidem.")
                    else:
                        try:
                            resposta = requests.post(
                                f"{API_URL}/register",
                                json={
                                    "nome": nome.strip(),
                                    "username": usuario.strip(),
                                    "email": email.strip(),
                                    "telefone": telefone.strip(),
                                    "password": senha
                                },
                                timeout=30
                            )
                            if resposta.status_code in [200, 201]:
                                st.success("✅ Conta criada com sucesso!")
                                time.sleep(1.5)
                                st.session_state["tela_login"] = "login"
                                st.rerun()
                            else:
                                st.error(f"Erro: {resposta.text}")
                        except Exception as e:
                            st.error(f"Erro de conexão: {e}")

            with col2:
                if st.button("← Voltar", use_container_width=True):
                    st.session_state["tela_login"] = "login"
                    st.rerun()

        # ===================== TELA RECUPERAR SENHA =====================
        elif st.session_state["tela_login"] == "recuperar":

            st.subheader("🔑 Recuperar Senha")

            usuario_rec = st.text_input("Usuário", placeholder="Seu usuário", key="rec_user")
            email_rec = st.text_input("E-mail cadastrado", placeholder="seu@email.com", key="rec_email")
            nova_senha = st.text_input("Nova senha", type="password", placeholder="Digite a nova senha", key="rec_pass")
            nova_senha2 = st.text_input("Confirmar nova senha", type="password", placeholder="Repita a nova senha", key="rec_pass2")

            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔄 Alterar Senha", use_container_width=True, type="primary"):
                    if not usuario_rec or not email_rec or not nova_senha:
                        st.warning("Preencha todos os campos.")
                    elif nova_senha != nova_senha2:
                        st.error("As senhas não coincidem.")
                    else:
                        try:
                            resposta = requests.post(
                                f"{API_URL}/recuperar-senha",
                                json={
                                    "username": usuario_rec.strip(),
                                    "email": email_rec.strip(),
                                    "nova_senha": nova_senha
                                },
                                timeout=30
                            )
                            if resposta.status_code in [200, 201]:
                                st.success("✅ Senha alterada com sucesso!")
                                time.sleep(1.5)
                                st.session_state["tela_login"] = "login"
                                st.rerun()
                            else:
                                st.error(f"Erro: {resposta.text}")
                        except Exception as e:
                            st.error(f"Erro de conexão: {e}")

            with col2:
                if st.button("← Voltar", use_container_width=True, key="btn_voltar_rec"):
                    st.session_state["tela_login"] = "login"
                    st.rerun()

    st.markdown(
        """
        <br>
        <div style="text-align:center; color:#94A3B8; font-size:13px;">
        Duarte Performance © 2026
        </div>
        """,
        unsafe_allow_html=True
    )