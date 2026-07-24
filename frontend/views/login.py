import os
import requests
import streamlit as st

# URL base do Backend
API_URL = os.getenv(
    "BACKEND_URL", "https://duarte-performance-backend.onrender.com"
)


def autenticar(username: str, password: str) -> tuple[dict | None, str | None]:
    """Realiza a requisição de autenticação para a API do backend.

    Retorna uma tupla (dados_json, mensagem_erro).
    """
    try:
        response = requests.post(
            f"{API_URL}/token",
            data={"username": username, "password": password},
            timeout=25,  # Tempo estendido para o 'cold start' do Render
        )

        if response.status_code == 200:
            return response.json(), None
        elif response.status_code in (401, 400):
            return None, "🔑 Usuário ou senha incorretos."
        else:
            return (
                None,
                f"⚠️ O servidor respondeu com o código {response.status_code}.",
            )

    except requests.exceptions.Timeout:
        return (
            None,
            "⏳ O servidor demorou a responder (pode estar inicializando)."
            " Tente novamente em instantes.",
        )
    except requests.exceptions.RequestException:
        return (
            None,
            "🌐 Erro de conexão com o servidor. Verifique sua conexão de"
            " internet.",
        )
    except Exception as e:
        return None, f"❌ Erro inesperado: {str(e)}"


def inject_login_css():
    """Injeta estilos customizados para a tela de autenticação."""
    st.markdown(
        """
    <style>
        /* Ocultar elementos nativos desnecessários */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        
        /* Container principal do login */
        .login-card {
            background-color: #FFFFFF;
            border-radius: 16px;
            padding: 32px 28px;
            box-shadow: 0 10px 30px rgba(0, 30, 87, 0.08);
            border: 1px solid #E2E8F0;
            border-top: 6px solid #FF9200;
            margin-bottom: 20px;
        }

        .login-header {
            text-align: center;
            margin-bottom: 24px;
        }

        .login-title {
            color: #001E57;
            font-size: 28px;
            font-weight: 900;
            margin: 0;
            letter-spacing: -0.5px;
        }

        .login-subtitle {
            color: #64748B;
            font-size: 14px;
            margin-top: 6px;
            font-weight: 500;
        }

        /* Estilização dos Inputs */
        div[data-baseweb="input"] {
            border-radius: 10px !important;
        }

        /* Estilização do Botão Principal */
        div.stButton > button {
            background-color: #001E57 !important;
            color: #FFFFFF !important;
            border-radius: 10px !important;
            font-weight: 700 !important;
            height: 48px !important;
            border: none !important;
            transition: all 0.3s ease !important;
        }

        div.stButton > button:hover {
            background-color: #FF9200 !important;
            box-shadow: 0 4px 12px rgba(255, 146, 0, 0.3) !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )


def render_login():
    """Renderiza a interface de login da aplicação."""
    inject_login_css()

    # Centralização do formulário em telas médias/grandes
    _, col_main, _ = st.columns([1, 1.3, 1])

    with col_main:
        # Card de Boas-vindas
        st.markdown(
            """
            <div class="login-card">
                <div class="login-header">
                    <div class="login-title">🟠 Duarte Performance</div>
                    <div class="login-subtitle">Gestão Operacional & Monitoramento Inteligente</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

        # Formulário com suporte à tecla Enter
        with st.form(key="login_form", clear_on_submit=False):
            usuario = st.text_input(
                "Usuário",
                placeholder="Informe seu usuário corporativo",
                autocomplete="username",
            )

            senha = st.text_input(
                "Senha",
                type="password",
                placeholder="Informe sua senha",
                autocomplete="current-password",
            )

            entrar = st.form_submit_button(
                "🔐 Entrar no Sistema", use_container_width=True
            )

        if entrar:
            usuario_clean = usuario.strip()

            if not usuario_clean or not senha:
                st.warning("⚠️ Por favor, informe o usuário e a senha.")
                return

            with st.spinner("⏳ Autenticando com o servidor..."):
                dados, erro = autenticar(usuario_clean, senha)

            if dados:
                # Salva todas as variáveis de sessão necessárias
                st.session_state["token"] = dados.get("access_token", "")
                st.session_state["username"] = dados.get(
                    "username", usuario_clean
                )
                st.session_state["nome"] = dados.get("nome", usuario_clean)
                st.session_state["user_nome"] = dados.get(
                    "nome", usuario_clean
                )
                st.session_state["role"] = dados.get("role", "Operador")
                st.session_state["user_role"] = dados.get("role", "Operador")
                st.session_state["perfil_completo"] = dados.get(
                    "perfil_completo", True
                )

                st.success("✅ Acesso liberado com sucesso!")
                st.rerun()
            else:
                st.error(erro)


if __name__ == "__main__":
    render_login()