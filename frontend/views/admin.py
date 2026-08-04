import os
import pandas as pd
import requests
import streamlit as st

from tabela_pro import inject_tabela_css, mostrar_tabela

API_URL = os.getenv(
    "BACKEND_URL", "https://duarte-performance-backend-production.up.railway.app"
)


def inject_admin_css():
    st.markdown(
        """
        <style>
            @keyframes fadeInUp {
                from { opacity: 0; transform: translateY(14px); }
                to   { opacity: 1; transform: translateY(0); }
            }
            @keyframes floatGradient {
                0%   { background-position: 0% 50%; }
                50%  { background-position: 100% 50%; }
                100% { background-position: 0% 50%; }
            }

            .admin-hero {
                background: linear-gradient(-45deg, #001E57, #030A1A, #0B296B, #001233);
                background-size: 300% 300%;
                animation: floatGradient 12s ease infinite, fadeInUp 0.5s ease-out;
                border-radius: 20px;
                padding: 28px 32px;
                color: #FFF;
                border-left: 6px solid #FF9200;
                margin-bottom: 22px;
                box-shadow: 0 16px 40px rgba(0, 30, 87, 0.22);
            }
            .admin-hero h2 {
                margin: 0;
                font-weight: 900;
                font-size: 1.85rem;
            }
            .admin-hero p {
                margin: 8px 0 0 0;
                color: #94A3B8;
                font-size: 0.95rem;
            }

            .admin-card {
                background-color: #FFFFFF;
                border-radius: 14px;
                padding: 20px;
                border-left: 5px solid #001E57;
                box-shadow: 0 6px 18px rgba(0, 30, 87, 0.06);
                margin-bottom: 20px;
                animation: fadeInUp 0.55s ease-out;
            }
            .admin-header {
                color: #001E57;
                font-size: 24px;
                font-weight: 800;
                margin-bottom: 10px;
            }
            .info-box {
                background-color: #F8FAFC;
                border-radius: 12px;
                padding: 15px;
                border: 1px solid #E2E8F0;
                color: #334155;
            }
        </style>
    """,
        unsafe_allow_html=True,
    )


def render_painel_admin():
    inject_admin_css()
    inject_tabela_css()

    st.markdown(
        """
    <div class="admin-hero">
        <h2>🛡️ Painel Administrativo Executivo</h2>
        <p>Gestão de Acessos, Cadastros e Auditoria Operacional — Duarte Gestão</p>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # =========================================================
    # 1. VALIDAÇÃO DE SEGURANÇA
    # =========================================================
    user_role = st.session_state.get("user_role") or st.session_state.get(
        "role", "Operador"
    )

    if str(user_role).strip() not in ("Admin", "Admin Master", "admin", "admin master"):
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
    # 2. ABAS
    # =========================================================
    aba_cadastrar, aba_usuarios, aba_funcoes, aba_senhas, aba_auditoria = st.tabs([
        "➕ Cadastrar Novo Usuário",
        "👥 Usuários e Acessos",
        "🔧 Gerenciar Funções",
        "🔑 Solicitações de Senha",
        "📜 Logs de Auditoria",
    ])

    # ---------------------------------------------------------
    # ABA 1: CADASTRO
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
                    "Nível de Permissão (Role)",
                    ["Operador", "Visualizador", "Gestor", "Admin"],
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
                        <li><b>Operador:</b> Lança execução e vê a própria escala.</li>
                        <li><b>Visualizador:</b> Consulta + pode lançar; não edita/exclui.</li>
                        <li><b>Gestor / Admin:</b> Acesso ampliado e este painel.</li>
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
            "Usuários autorizados no ecossistema Duarte Performance."
        )

        try:
            resp_lista = requests.get(
                f"{API_URL}/usuarios/todos", headers=headers, timeout=25
            )
        except Exception as e:
            resp_lista = None
            st.error(f"🌐 Erro de conexão com o servidor: {e}")

        if resp_lista is not None and resp_lista.status_code == 200:
            usuarios_api = resp_lista.json()

            if usuarios_api:
                df_equipe = pd.DataFrame(usuarios_api)
                cols = [c for c in ["nome", "username", "email", "role"] if c in df_equipe.columns]
                df_equipe = df_equipe[cols]
                mostrar_tabela(
                    df_equipe,
                    mapa_colunas={
                        "nome": "Nome",
                        "username": "Login / Usuário",
                        "email": "E-mail",
                        "role": "Função",
                    },
                    titulo="👥 Equipe cadastrada",
                    max_linhas=200,
                    injetar_css=False,
                )
            else:
                st.info("ℹ️ Nenhum usuário cadastrado ainda.")
        elif resp_lista is not None:
            if resp_lista.status_code == 403:
                st.error(
                    "⛔ Seu perfil não tem permissão para listar usuários."
                )
            else:
                st.error(
                    f"❌ Não foi possível carregar os usuários"
                    f" (status {resp_lista.status_code})."
                )

    # ---------------------------------------------------------
    # ABA 3: GERENCIAR FUNÇÕES
    # ---------------------------------------------------------
    with aba_funcoes:
        st.markdown("### 🔧 Gerenciar Função (Role) dos Usuários")
        st.write(
            "Selecione um usuário para visualizar seus dados e alterar o"
            " nível de permissão."
        )

        ROLES_DISPONIVEIS = ["Operador", "Visualizador", "Gestor", "Admin"]

        with st.spinner("Carregando usuários..."):
            try:
                resp_usuarios = requests.get(
                    f"{API_URL}/usuarios/todos", headers=headers, timeout=25
                )
            except Exception as e:
                resp_usuarios = None
                st.error(f"🌐 Erro de conexão com o servidor: {e}")

        if resp_usuarios is not None and resp_usuarios.status_code == 200:
            lista_usuarios = resp_usuarios.json()

            if not lista_usuarios:
                st.info("ℹ️ Nenhum usuário cadastrado ainda.")
            else:
                opcoes = {
                    f"{u['nome']} ({u['username']}) — {u['role']}": u
                    for u in lista_usuarios
                }

                rotulo_selecionado = st.selectbox(
                    "Selecione o usuário:",
                    list(opcoes.keys()),
                    key="select_usuario_funcao",
                )
                usuario_sel = opcoes[rotulo_selecionado]

                col_dados, col_acao = st.columns([1, 1])

                with col_dados:
                    st.markdown(
                        f"""
                        <div class="info-box">
                            <b>Nome:</b> {usuario_sel['nome']}<br>
                            <b>Usuário:</b> {usuario_sel['username']}<br>
                            <b>E-mail:</b> {usuario_sel.get('email', '-')}<br>
                            <b>Função Atual:</b> {usuario_sel['role']}
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                with col_acao:
                    role_atual = usuario_sel["role"]
                    indice_atual = (
                        ROLES_DISPONIVEIS.index(role_atual)
                        if role_atual in ROLES_DISPONIVEIS
                        else 0
                    )
                    nova_role = st.selectbox(
                        "Nova Função:",
                        ROLES_DISPONIVEIS,
                        index=indice_atual,
                        key="select_nova_role",
                    )

                    if st.button(
                        "💾 Salvar Alteração de Função",
                        use_container_width=True,
                        type="primary",
                        key="btn_salvar_role",
                    ):
                        if nova_role == role_atual:
                            st.info(
                                "ℹ️ Essa já é a função atual deste usuário."
                            )
                        else:
                            with st.spinner("Atualizando função..."):
                                try:
                                    resp_role = requests.put(
                                        f"{API_URL}/usuarios/"
                                        f"{usuario_sel['id']}/role",
                                        json={"role": nova_role},
                                        headers=headers,
                                        timeout=25,
                                    )
                                    if resp_role.status_code == 200:
                                        st.success(
                                            f"✅ Função de"
                                            f" **{usuario_sel['nome']}**"
                                            f" atualizada para"
                                            f" **{nova_role}**!"
                                        )
                                        st.rerun()
                                    elif resp_role.status_code == 403:
                                        st.error(
                                            "⛔ Apenas o Admin pode alterar"
                                            " funções."
                                        )
                                    elif resp_role.status_code == 404:
                                        st.error(
                                            "❌ Usuário não encontrado."
                                        )
                                    else:
                                        st.error(
                                            "❌ Erro ao atualizar:"
                                            f" {resp_role.text}"
                                        )
                                except Exception as e:
                                    st.error(f"🌐 Erro de conexão: {e}")

                st.caption(
                    "👁️ **Visualizador**: leitura ampla e pode lançar execução;"
                    " não edita/exclui em massa."
                )
        elif resp_usuarios is not None:
            if resp_usuarios.status_code == 403:
                st.error(
                    "⛔ Seu perfil não tem permissão para listar usuários."
                )
            else:
                st.error(
                    "❌ Não foi possível carregar os usuários"
                    f" (status {resp_usuarios.status_code})."
                )

    # ---------------------------------------------------------
    # ABA 4: SOLICITAÇÕES DE SENHA
    # ---------------------------------------------------------
    with aba_senhas:
        st.markdown("### 🔑 Solicitações de Recuperação de Senha")
        st.info(
            "Você **autoriza** ou **rejeita** — nunca vê nem define a senha"
            " de ninguém. Ao autorizar, o usuário tem **10 minutos** para"
            " definir a própria senha nova."
        )

        try:
            resp_solic = requests.get(
                f"{API_URL}/admin/solicitacoes-senha",
                headers=headers,
                timeout=25,
            )
        except Exception as e:
            resp_solic = None
            st.error(f"🌐 Erro de conexão com o servidor: {e}")

        if resp_solic is not None and resp_solic.status_code == 200:
            solicitacoes = resp_solic.json()
            pendentes = [s for s in solicitacoes if s["status"] == "pendente"]
            outras = [s for s in solicitacoes if s["status"] != "pendente"]

            st.markdown(f"#### 🟡 Pendentes ({len(pendentes)})")

            if not pendentes:
                st.caption("Nenhuma solicitação pendente no momento.")
            else:
                for s in pendentes:
                    with st.container():
                        st.markdown(
                            f"""
                            <div class="info-box" style="margin-bottom:10px;">
                                <b>Usuário:</b> {s['username']}<br>
                                <b>E-mail:</b> {s.get('email') or '-'}<br>
                                <b>Telefone:</b> {s.get('telefone') or '-'}<br>
                                <b>Solicitado em:</b> {s['solicitado_em']}
                            </div>
                            """,
                            unsafe_allow_html=True,
                        )
                        col_aut, col_rej = st.columns(2)
                        with col_aut:
                            if st.button(
                                "✅ Autorizar",
                                key=f"btn_autorizar_{s['id']}",
                                use_container_width=True,
                                type="primary",
                            ):
                                try:
                                    r = requests.post(
                                        f"{API_URL}/admin/solicitacoes-senha"
                                        f"/{s['id']}/autorizar",
                                        headers=headers,
                                        timeout=25,
                                    )
                                    if r.status_code == 200:
                                        st.success(
                                            "✅ Autorizado! O usuário tem 10"
                                            " minutos para trocar a senha."
                                        )
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Erro: {r.text}")
                                except Exception as e:
                                    st.error(f"🌐 Erro de conexão: {e}")
                        with col_rej:
                            if st.button(
                                "🚫 Rejeitar",
                                key=f"btn_rejeitar_{s['id']}",
                                use_container_width=True,
                            ):
                                try:
                                    r = requests.post(
                                        f"{API_URL}/admin/solicitacoes-senha"
                                        f"/{s['id']}/rejeitar",
                                        headers=headers,
                                        timeout=25,
                                    )
                                    if r.status_code == 200:
                                        st.warning("🚫 Solicitação rejeitada.")
                                        st.rerun()
                                    else:
                                        st.error(f"❌ Erro: {r.text}")
                                except Exception as e:
                                    st.error(f"🌐 Erro de conexão: {e}")
                        st.divider()

            with st.expander(f"📋 Histórico ({len(outras)})"):
                if not outras:
                    st.caption("Nenhuma solicitação anterior.")
                else:
                    ICONE_STATUS = {
                        "autorizado": "🟢",
                        "usado": "✅",
                        "expirado": "⏱️",
                        "rejeitado": "🚫",
                    }
                    df_hist = pd.DataFrame(outras)
                    if "status" in df_hist.columns:
                        df_hist["status"] = df_hist["status"].apply(
                            lambda s: f"{ICONE_STATUS.get(s, '')} {s}"
                        )
                    colunas = [
                        "username",
                        "status",
                        "solicitado_em",
                        "autorizado_em",
                        "expira_em",
                        "autorizado_por",
                    ]
                    colunas_existentes = [
                        c for c in colunas if c in df_hist.columns
                    ]
                    mostrar_tabela(
                        df_hist[colunas_existentes],
                        mapa_colunas={
                            "username": "Usuário",
                            "status": "Status",
                            "solicitado_em": "Solicitado em",
                            "autorizado_em": "Autorizado em",
                            "expira_em": "Expira em",
                            "autorizado_por": "Autorizado por",
                        },
                        titulo="📋 Histórico de solicitações",
                        max_linhas=100,
                        injetar_css=False,
                    )
        elif resp_solic is not None:
            if resp_solic.status_code == 403:
                st.error(
                    "⛔ Apenas o Admin pode ver as solicitações de senha."
                )
            else:
                st.error(
                    "❌ Não foi possível carregar as solicitações"
                    f" (status {resp_solic.status_code})."
                )

    # ---------------------------------------------------------
    # ABA 5: LOGS DE AUDITORIA
    # ---------------------------------------------------------
    with aba_auditoria:
        st.markdown("### 📜 Registros de Auditoria e Atividades")
        st.write(
            "Histórico de ações, cadastros e acessos para rastreabilidade."
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
        mostrar_tabela(
            df_logs,
            titulo="📜 Logs de auditoria",
            max_linhas=100,
            injetar_css=False,
        )
        st.caption(
            "Quando o backend tiver endpoint de logs reais, esta aba passa a"
            " consumir a API automaticamente."
        )


if __name__ == "__main__":
    render_painel_admin()