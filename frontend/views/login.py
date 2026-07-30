import os
import time
import requests
import streamlit as st

API_URL = os.getenv(
    "BACKEND_URL",
    "https://duarte-performance-backend-production.up.railway.app",
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
        unsafe_allow_html=True,
    )

    # Controle de telas (login | cadastro | recuperar)
    if "tela_login" not in st.session_state:
        st.session_state["tela_login"] = "login"

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
            unsafe_allow_html=True,
        )

        # ===================== TELA DE LOGIN =====================
        if st.session_state["tela_login"] == "login":
            usuario = st.text_input(
                "Usuário", placeholder="Digite seu usuário", key="login_user"
            )
            senha = st.text_input(
                "Senha",
                type="password",
                placeholder="Digite sua senha",
                key="login_pass",
            )

            if st.button(
                "🚀 Entrar no Sistema",
                use_container_width=True,
                key="btn_login",
            ):
                if not usuario or not senha:
                    st.warning("Informe usuário e senha.")
                else:
                    try:
                        with st.spinner("Conectando ao servidor..."):
                            # O FastAPI espera requisição Form Data em /token
                            resposta = requests.post(
                                f"{API_URL}/token",
                                data={
                                    "username": usuario.strip(),
                                    "password": senha,
                                },
                                timeout=30,
                            )

                        if resposta.status_code == 200:
                            dados = resposta.json()
                            st.session_state["token"] = dados["access_token"]
                            st.session_state["username"] = dados.get(
                                "username", usuario
                            )
                            st.session_state["nome"] = dados.get(
                                "nome", usuario
                            )
                            st.session_state["role"] = dados.get(
                                "role", "Operador"
                            )
                            st.session_state["user_nome"] = dados.get(
                                "nome", usuario
                            )
                            st.session_state["user_role"] = dados.get(
                                "role", "Operador"
                            )
                            st.success("✅ Login realizado com sucesso!")
                            time.sleep(1)
                            st.rerun()
                        else:
                            # Pega a mensagem de erro detalhada da API
                            erro_msg = "Usuário ou senha incorretos."
                            try:
                                erro_msg = resposta.json().get(
                                    "detail", erro_msg
                                )
                            except Exception:
                                pass
                            st.error(f"❌ {erro_msg}")
                    except Exception as e:
                        st.error(f"❌ Erro de conexão com o servidor: {e}")

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
            st.caption(
                "Selecione seu nome na escala e complete com o sobrenome —"
                " isso evita conflito quando duas pessoas tiverem o mesmo"
                " primeiro nome."
            )

            # Busca os nomes da escala que ainda não têm conta
            if "cad_nomes_escala" not in st.session_state:
                try:
                    resp_nomes = requests.get(
                        f"{API_URL}/nomes-escala-disponiveis", timeout=20
                    )
                    st.session_state["cad_nomes_escala"] = (
                        resp_nomes.json()
                        if resp_nomes.status_code == 200
                        else []
                    )
                except Exception:
                    st.session_state["cad_nomes_escala"] = []

            nomes_disponiveis = st.session_state["cad_nomes_escala"]

            if not nomes_disponiveis:
                st.warning(
                    "⚠️ Não há nomes disponíveis na escala no momento (ou"
                    " todos já possuem conta). Fale com o Administrador."
                )

            nome_escala = st.selectbox(
                "Seu nome na escala *",
                ["Selecione..."] + nomes_disponiveis,
                key="cad_nome_escala",
            )
            sobrenome = st.text_input(
                "Seu sobrenome *",
                placeholder="Ex: Martinez",
                key="cad_sobrenome",
            )

            username_sugerido = ""
            if nome_escala != "Selecione..." and sobrenome.strip():
                try:
                    resp_sug = requests.get(
                        f"{API_URL}/sugerir-username",
                        params={
                            "nome_escala": nome_escala,
                            "sobrenome": sobrenome.strip(),
                        },
                        timeout=20,
                    )
                    if resp_sug.status_code == 200:
                        username_sugerido = resp_sug.json().get(
                            "username_sugerido", ""
                        )
                except Exception:
                    pass

            usuario = st.text_input(
                "Usuário (login) *",
                value=username_sugerido,
                placeholder="Preenchido automaticamente após o sobrenome",
                key="cad_user",
                help=(
                    "Sugerido no formato nome.sobrenome. Você pode ajustar"
                    " se quiser."
                ),
            )
            email = st.text_input(
                "E-mail de contato *",
                placeholder="seu@email.com",
                key="cad_email",
            )
            telefone = st.text_input(
                "Telefone de contato",
                placeholder="(11) 90000-0000",
                key="cad_telefone",
            )
            senha = st.text_input(
                "Senha *",
                type="password",
                placeholder="Crie uma senha",
                key="cad_pass",
            )
            senha2 = st.text_input(
                "Confirmar senha *",
                type="password",
                placeholder="Repita a senha",
                key="cad_pass2",
            )

            col1, col2 = st.columns(2)
            with col1:
                if st.button(
                    "💾 Cadastrar", use_container_width=True, type="primary"
                ):
                    nome_completo = (
                        f"{nome_escala.strip().title()} {sobrenome.strip().title()}"
                        if nome_escala != "Selecione..."
                        else ""
                    )
                    if (
                        nome_escala == "Selecione..."
                        or not sobrenome.strip()
                        or not usuario.strip()
                        or not senha
                    ):
                        st.warning("Preencha os campos obrigatórios (*).")
                    elif senha != senha2:
                        st.error("As senhas não coincidem.")
                    else:
                        try:
                            payload = {
                                "nome": nome_completo,
                                "username": usuario.strip(),
                                "email": (
                                    email.strip()
                                    if email
                                    else usuario.strip()
                                ),
                                "telefone": (
                                    telefone.strip() if telefone else None
                                ),
                                "senha": senha,
                                "role": "Operador",
                            }
                            resposta = requests.post(
                                f"{API_URL}/usuarios/",
                                json=payload,
                                timeout=30,
                            )

                            if resposta.status_code in [200, 201]:
                                st.success("✅ Conta criada com sucesso!")
                                st.session_state.pop(
                                    "cad_nomes_escala", None
                                )
                                time.sleep(1.5)
                                st.session_state["tela_login"] = "login"
                                st.rerun()
                            else:
                                erro_detalhe = "Erro ao realizar cadastro."
                                try:
                                    erro_detalhe = resposta.json().get(
                                        "detail", resposta.text
                                    )
                                except Exception:
                                    pass
                                st.error(f"⚠️ {erro_detalhe}")
                        except Exception as e:
                            st.error(f"Erro de conexão: {e}")

            with col2:
                if st.button("← Voltar", use_container_width=True):
                    st.session_state.pop("cad_nomes_escala", None)
                    st.session_state["tela_login"] = "login"
                    st.rerun()

        # ===================== TELA RECUPERAR SENHA =====================
        elif st.session_state["tela_login"] == "recuperar":
            st.subheader("🔑 Recuperar Senha")

            modo_recuperacao = st.radio(
                "O que você precisa?",
                [
                    "📨 Solicitar recuperação",
                    "✅ Já fui autorizado — definir nova senha",
                ],
                key="rec_modo",
                label_visibility="collapsed",
            )

            # --------- SOLICITAR RECUPERAÇÃO ---------
            if "Solicitar" in modo_recuperacao:
                st.info(
                    "Informe seus dados. Um administrador vai analisar e"
                    " autorizar a troca — ele **não vê nem define** sua"
                    " senha, só libera o acesso por 10 minutos."
                )

                rec_usuario = st.text_input(
                    "Usuário *", placeholder="Seu login", key="rec_user"
                )
                rec_email = st.text_input(
                    "E-mail cadastrado",
                    placeholder="seu@email.com",
                    key="rec_email",
                )
                rec_telefone = st.text_input(
                    "Telefone cadastrado",
                    placeholder="(11) 90000-0000",
                    key="rec_telefone",
                )

                if st.button(
                    "📨 Solicitar recuperação",
                    use_container_width=True,
                    type="primary",
                    key="btn_solicitar_rec",
                ):
                    if not rec_usuario.strip():
                        st.warning("Informe o usuário.")
                    else:
                        try:
                            payload = {
                                "username": rec_usuario.strip(),
                                "email": (
                                    rec_email.strip() if rec_email else None
                                ),
                                "telefone": (
                                    rec_telefone.strip()
                                    if rec_telefone
                                    else None
                                ),
                            }
                            resposta = requests.post(
                                f"{API_URL}/recuperar-senha",
                                json=payload,
                                timeout=30,
                            )
                            if resposta.status_code == 200:
                                st.success(
                                    "✅ Solicitação registrada! Aguarde a"
                                    " autorização do administrador."
                                )
                            else:
                                erro_detalhe = "Erro ao solicitar."
                                try:
                                    erro_detalhe = resposta.json().get(
                                        "detail", resposta.text
                                    )
                                except Exception:
                                    pass
                                st.error(f"⚠️ {erro_detalhe}")
                        except Exception as e:
                            st.error(f"Erro de conexão: {e}")

            # --------- DEFINIR NOVA SENHA (JÁ AUTORIZADO) ---------
            else:
                st.info(
                    "Se o administrador já autorizou, você tem **10"
                    " minutos** a partir da autorização para definir a"
                    " nova senha aqui."
                )

                nova_usuario = st.text_input(
                    "Usuário *", placeholder="Seu login", key="nova_user"
                )
                nova_senha = st.text_input(
                    "Nova senha *",
                    type="password",
                    placeholder="Digite a nova senha",
                    key="nova_senha1",
                )
                nova_senha2 = st.text_input(
                    "Confirmar nova senha *",
                    type="password",
                    placeholder="Repita a nova senha",
                    key="nova_senha2",
                )

                if st.button(
                    "🔓 Definir nova senha",
                    use_container_width=True,
                    type="primary",
                    key="btn_definir_senha",
                ):
                    if not nova_usuario.strip() or not nova_senha:
                        st.warning("Preencha usuário e a nova senha.")
                    elif nova_senha != nova_senha2:
                        st.error("As senhas não coincidem.")
                    else:
                        try:
                            payload = {
                                "username": nova_usuario.strip(),
                                "nova_senha": nova_senha,
                                "confirmar_senha": nova_senha2,
                            }
                            resposta = requests.post(
                                f"{API_URL}/redefinir-senha-autorizada",
                                json=payload,
                                timeout=30,
                            )
                            if resposta.status_code == 200:
                                st.success(
                                    "✅ Senha redefinida! Você já pode"
                                    " entrar com a nova senha."
                                )
                                time.sleep(1.5)
                                st.session_state["tela_login"] = "login"
                                st.rerun()
                            else:
                                erro_detalhe = "Erro ao redefinir senha."
                                try:
                                    erro_detalhe = resposta.json().get(
                                        "detail", resposta.text
                                    )
                                except Exception:
                                    pass
                                st.error(f"⚠️ {erro_detalhe}")
                        except Exception as e:
                            st.error(f"Erro de conexão: {e}")

            st.markdown("<br>", unsafe_allow_html=True)
            if st.button(
                "← Voltar ao Login",
                use_container_width=True,
                key="btn_voltar_rec",
            ):
                st.session_state["tela_login"] = "login"
                st.rerun()

    st.markdown(
        """
        <br>
        <div style="text-align:center; color:#94A3B8; font-size:13px;">
        Duarte Performance © 2026
        </div>
        """,
        unsafe_allow_html=True,
    )