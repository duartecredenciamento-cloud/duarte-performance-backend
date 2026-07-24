import streamlit as st
import requests
import time
import os


API_URL = os.getenv(
    "BACKEND_URL",
    "https://duarte-performance-backend.onrender.com"
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

            background:
            linear-gradient(
            135deg,
            #FF9200,
            #E07A00
            );

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


    espaco1, centro, espaco2 = st.columns(
        [1,2,1]
    )


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


        with st.container():


            usuario = st.text_input(
                "Usuário",
                placeholder="Digite seu usuário"
            )


            senha = st.text_input(
                "Senha",
                type="password",
                placeholder="Digite sua senha"
            )


            entrar = st.button(
                "🚀 Entrar no Sistema",
                use_container_width=True
            )


            if entrar:


                if not usuario or not senha:

                    st.warning(
                        "Informe usuário e senha."
                    )
                    return


                try:


                    with st.spinner(
                        "Conectando ao servidor..."
                    ):


                        resposta = requests.post(

                            f"{API_URL}/token",

                            data={

                                "username":
                                usuario.strip(),

                                "password":
                                senha

                            },

                            headers={

                                "Content-Type":
                                "application/x-www-form-urlencoded"

                            },

                            timeout=60

                        )


                    if resposta.status_code == 200:


                        dados = resposta.json()


                        st.session_state["token"] = (
                            dados["access_token"]
                        )


                        st.session_state["username"] = (
                            dados.get(
                                "username",
                                usuario
                            )
                        )


                        st.session_state["nome"] = (
                            dados.get(
                                "nome",
                                usuario
                            )
                        )


                        st.session_state["role"] = (
                            dados.get(
                                "role",
                                "Operador"
                            )
                        )


                        st.session_state["user_nome"] = (
                            dados.get(
                                "nome",
                                usuario
                            )
                        )


                        st.session_state["user_role"] = (
                            dados.get(
                                "role",
                                "Operador"
                            )
                        )


                        st.success(
                            "✅ Login realizado!"
                        )


                        time.sleep(1)

                        st.rerun()



                    else:


                        try:

                            erro = resposta.json()

                        except:

                            erro = resposta.text



                        st.error(
                            f"❌ Login recusado: {erro}"
                        )



                except requests.exceptions.Timeout:


                    st.error(
                        """
                        ⏳ O servidor demorou para responder.

                        O Render pode estar acordando.
                        Aguarde alguns segundos e tente novamente.
                        """
                    )


                except requests.exceptions.ConnectionError:


                    st.error(
                        """
                        ❌ Não foi possível conectar ao backend.

                        Verifique se o serviço do Render está online.
                        """
                    )


                except Exception as e:


                    st.error(
                        f"Erro inesperado: {e}"
                    )


    st.markdown(
        """
        <br>

        <div style="
        text-align:center;
        color:#94A3B8;
        font-size:13px;
        ">
        Duarte Performance © 2026
        </div>

        """,
        unsafe_allow_html=True
    )