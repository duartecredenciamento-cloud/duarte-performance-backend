import os
import pandas as pd
import requests
import streamlit as st

# URL base da API Backend (ajusta automaticamente via variável de ambiente ou padrão)
API_URL = os.getenv(
    "BACKEND_URL", "https://duarte-performance-backend.onrender.com"
)


def inject_admin_css():
    """Injeta estilos customizados para a Central Administrativa."""
    st.markdown(
        """
        <style>
            .admin-card {
                background-color: #FFFFFF;
                border-radius: 12px;
                padding: 20px;
                border-left: 5px solid #001E57;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
                margin-bottom: 20px;
            }
            .admin-header {
                color: #001E57;
                font-size: 24px;
                font-weight: 800;
                margin-bottom: 10px;
            }
            .info-box {
                background-color: #F8FAFC;
                border-radius: 10px;
                padding: 15px;
                border: 1px solid #E2E8F0;
                color: #334155;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )


def render_painel_admin():
    """Renderiza a Central Executiva Administrativa da Duarte Gestão."""
    inject_admin_css()

    st.title("🛡️ Painel Administrativo Executivo")
    st.caption(
        "Gestão de Acessos, Cadastros e Auditoria Operacional — Duarte Gestão"
    )

    # =========================================================
    # 1. VALIDAÇÃO DE SEGURANÇA E PERMISSÃO
    # =========================================================
    user_role = st.session_state.get("user_role") or st.session_state.get(
        "role", "Operador"
    )

    if user_role != "Admin":
        st.error(
            "⛔ **Acesso Restrito:** Apenas usuários com perfil **Admin** possuem"
            " acesso a esta área."
        )
        st.info(
            "Se você precisa de acesso administrativo, solicite a alteração do"
            " seu perfil ao gestor do sistema."
        )
        return

    token = st.session_state.get("token")
    if not token:
        st.warning(
            "⚠️ Sessão não encontrada ou expirada. Por favor, faça o login"
            " novamente."
        )
        return

    headers = {"Authorization": f"Bearer {token}"}

    # =========================================================
    # 2. ESTRUTURA DE ABAS NATIVAS
    # =========================================================
    aba_cadastrar, aba_usuarios, aba_auditoria = st.tabs([
        "➕ Cadastrar Novo Usuário",
        "👥 Usuários e Acessos",
        "📜 Logs de Auditoria",
    ])

    # ---------------------------------------------------------
    # ABA 1: CADASTRO DE USUÁRIO
    # ---------------------------------------------------------
    with aba_cadastrar:
        st.markdown("### 👤 Cadastrar Novo Membro na Equipe")
        st.write(
            "Crie o login e senha de acesso para novos operadores ou gestores."
        )

        col_form, col_info = st.columns([2, 1])

        with col_form:
            with st.form("form_cadastrar_usuario", clear_on_submit=True):
                nome = st.text_input(
                    "Nome Completo *", placeholder="Ex: Lucas Silva"
                )
                username = st.text_input(
                    "Login / E-mail Corporativo *",
                    placeholder="Ex: lucas@duarte.com",
                )
                email = st.text_input(
                    "E-mail de Contato (Opcional)",
                    placeholder="Ex: lucas.silva@duartegestao.com.br",
                )
                senha = st.text_input(
                    "Senha Inicial *",
                    type="password",
                    placeholder="Digite uma senha segura",
                )
                role = st.selectbox(
                    "Nível de Permissão (Role)", ["Operador", "Admin"]
                )

                submit = st.form_submit_button(
                    "🚀 Cadastrar Usuário",
                    use_container_width=True,
                    type="primary",
                )

                if submit:
                    if not nome.strip() or not username.strip() or not senha:
                        st.warning(
                            "⚠️ Preencha todos os campos obrigatórios (*)."
                        )
                    else:
                        payload = {
                            "nome": nome.strip(),
                            "username": username.strip(),
                            "email": (
                                email.strip() if email else username.strip()
                            ),
                            "senha": senha,
                            "role": role,
                        }

                        with st.spinner("Cadastrando usuário na API..."):
                            try:
                                response = requests.post(
                                    f"{API_URL}/usuarios/",
                                    json=payload,
                                    headers=headers,
                                    timeout=25,
                                )

                                if response.status_code in (200, 201):
                                    st.success(
                                        f"✅ Usuário **{nome}** ({role})"
                                        " cadastrado com sucesso!"
                                    )
                                elif response.status_code == 400:
                                    detalhe = response.json().get(
                                        "detail",
                                        "Este e-mail/login já está cadastrado.",
                                    )
                                    st.error(f"⚠️ {detalhe}")
                                else:
                                    st.error(
                                        f"❌ Erro ao cadastrar:"
                                        f" {response.text}"
                                    )
                            except Exception as e:
                                st.error(
                                    f"🌐 Erro de conexão com o servidor: {e}"
                                )

        with col_info:
            st.markdown(
                """
                <div class="admin-card">
                    <h4>💡 Recomendações</h4>
                    <ul>
                        <li><b>Login:</b> Utilize o e-mail corporativo como usuário.</li>
                        <li><b>Senha Inicial:</b> Escolha uma senha provisória e repasse ao funcionário.</li>
                        <li><b>Perfil Operador:</b> Acesso padrão para preencher execuções e cronogramas.</li>
                        <li><b>Perfil Admin:</b> Acesso total a relatórios, edições e à esta tela.</li>
                    </ul>
                </div>
                """,
                unsafe_allow_html=True,
            )

    # ---------------------------------------------------------
    # ABA 2: USUÁRIOS E ACESSOS
    # ---------------------------------------------------------
    with aba_usuarios:
        st.markdown("### 👥 Gestão da Equipe & Status de Acesso")
        st.info(
            "Abaixo estão os usuários atualmente autorizados no ecossistema"
            " Duarte Performance."
        )

        # Exibição estruturada da equipe da Duarte Gestão
        equipe_dados = [
            {
                "Nome": "Administrador",
                "Login / E-mail": "admin@duarte.com",
                "Função": "Admin",
                "Status": "🟢 Ativo",
            },
        ]

        df_equipe = pd.DataFrame(equipe_dados)
        st.dataframe(df_equipe, use_container_width=True, hide_index=True)

    # ---------------------------------------------------------
    # ABA 3: LOGS DE AUDITORIA
    # ---------------------------------------------------------
    with aba_auditoria:
        st.markdown("### 📜 Registros de Auditoria e Atividades")
        st.write(
            "Histórico de ações, cadastros e acessos para rastreabilidade de"
            " segurança."
        )

        logs_exemplo = [
            {
                "Data / Hora": "2026-07-29 15:10",
                "Usuário": "admin@duarte.com",
                "Ação": "Novo Cadastro",
                "Detalhes": "Cadastrou novo operador no sistema",
            },
        ]

        df_logs = pd.DataFrame(logs_exemplo)
        st.dataframe(df_logs, use_container_width=True, hide_index=True)


if __name__ == "__main__":
    render_painel_admin()