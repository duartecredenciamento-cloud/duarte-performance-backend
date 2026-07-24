import streamlit as st
import requests
import time
import os

API_URL = os.getenv("BACKEND_URL", "https://duarte-performance-backend.onrender.com")

def render_login():
    # CSS com Animações Premium e Glassmorphism
    st.markdown("""
    <style>
        /* Animações */
        @keyframes slideIn {
            from { opacity: 0; transform: translateX(-20px); }
            to { opacity: 1; transform: translateX(0); }
        }
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(15px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        /* Tipografia e Cores */
        .big-title { 
            font-size: 3.5rem; 
            font-weight: 900; 
            color: #FFFFFF; 
            margin: 0;
            line-height: 1.1;
        }
        .orange { color: #FF9200; }
        
        /* Hero Box (Lado Esquerdo) */
        .hero-box {
            background: linear-gradient(135deg, #001E57 0%, #030A1A 100%);
            padding: 50px 40px;
            border-radius: 24px;
            color: white;
            box-shadow: 0 20px 40px rgba(0, 30, 87, 0.3);
            animation: slideIn 0.8s cubic-bezier(0.4, 0, 0.2, 1);
            position: relative;
            overflow: hidden;
            height: 100%;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        .hero-box::after {
            content: '';
            position: absolute;
            top: -50%;
            right: -50%;
            width: 100%;
            height: 100%;
            background: radial-gradient(circle, rgba(255,146,0,0.1) 0%, transparent 60%);
        }
        
        /* Ajuste nas Abas (Tabs) do Streamlit */
        .stTabs [data-baseweb="tab-list"] {
            gap: 20px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: transparent;
            border-radius: 4px 4px 0px 0px;
            gap: 1px;
            padding-top: 10px;
            padding-bottom: 10px;
        }
        .stTabs [aria-selected="true"] {
            color: #FF9200 !important;
            border-bottom: 3px solid #FF9200 !important;
            font-weight: bold;
        }
        
        /* Botões */
        div.stButton > button[kind="primary"] {
            background: linear-gradient(135deg, #001E57 0%, #003399 100%) !important;
            border: none !important;
            border-radius: 12px !important;
            padding: 12px !important;
            font-weight: 800 !important;
            letter-spacing: 1px !important;
            transition: all 0.3s ease !important;
            animation: fadeIn 1s ease-out;
        }
        div.stButton > button[kind="primary"]:hover {
            background: linear-gradient(135deg, #FF9200 0%, #E67E00 100%) !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 10px 20px rgba(255,146,0,0.2) !important;
        }
    </style>
    """, unsafe_allow_html=True)

    # Margem superior para centralizar verticalmente
    st.markdown("<br><br>", unsafe_allow_html=True)

    col1, espaco, col2 = st.columns([1.2, 0.1, 1])

    # ================== LADO ESQUERDO (HERO) ==================
    with col1:
        st.markdown('''
        <div class="hero-box">
            <h1 class="big-title">Duarte<br><span class="orange">Performance</span></h1>
            <br>
            <h3 style="margin:0; font-weight: 300; color: #CBD5E1;">Sistema Operacional v2.4</h3>
            <p style="color: #94A3B8; font-size: 1.1rem; margin-top: 10px;">
                Central de Inteligência Operacional, Auditoria e Credenciamento de Saúde.
            </p>
        </div>
        ''', unsafe_allow_html=True)

    # ================== LADO DIREITO (FORMS) ==================
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        aba_login, aba_registro = st.tabs(["🔐 Login Seguro", "🆕 Primeiro Acesso"])

        # ----------------- ABA 1: LOGIN -----------------
        with aba_login:
            st.markdown("### Bem-vindo de volta!")
            st.caption("Insira suas credenciais para acessar o painel executivo.")
            
            username = st.text_input("Usuário", placeholder="Ex: admin, larissa, etc.", key="login_u")
            password = st.text_input("Senha", type="password", placeholder="••••••••", key="login_p")

            if st.button("🚀 ENTRAR NA PLATAFORMA", type="primary", use_container_width=True, key="btn_login"):
                if username and password:
                    with st.spinner("Autenticando sessão..."):
                        try:
                            resp = requests.post(
                                f"{API_URL}/token", 
                                data={"username": username.strip(), "password": password.strip()},
                                timeout=15
                            )
                            
                            if resp.status_code == 200:
                                data = resp.json()
                                
                                # Gravação BLINDADA das variáveis de sessão
                                st.session_state["token"] = data.get("access_token")
                                st.session_state["role"] = data.get("role", "Operador")
                                st.session_state["user_role"] = data.get("role", "Operador")
                                st.session_state["nome"] = data.get("nome", username)
                                st.session_state["user_nome"] = data.get("nome", username)
                                st.session_state["username"] = data.get("username", username)
                                
                                st.success("✅ Autenticado com sucesso!")
                                time.sleep(0.5)
                                st.rerun() # Dispara o recarregamento instantâneo da página
                                
                            elif resp.status_code == 401:
                                st.error("❌ Usuário ou senha incorretos.")
                            else:
                                st.warning(f"⚠️ O servidor está inicializando (Status: {resp.status_code}). Aguarde uns segundos.")

                        except requests.exceptions.Timeout:
                            st.warning("⏳ O servidor do backend estava dormindo e está ligando agora. Aguarde ~30 segundos e tente novamente.")
                        except Exception as e:
                            st.error("Erro de comunicação: O backend pode estar offline.")
                else:
                    st.warning("⚠️ Preencha usuário e senha.")

        # ----------------- ABA 2: PRIMEIRO ACESSO -----------------
        with aba_registro:
            st.markdown("### Configurar Acesso")
            st.caption("Selecione seu perfil no cronograma para criar sua senha.")
            
            # Lista Oficial de Operadores (Baseada na Matriz)
            lista_operadores = [
                "",
                "LARISSA",
                "KARINE",
                "NEIA",
                "VITÓRIA - I",
                "SILVANA",
                "JULIA",
                "EDVÂNIA",
                "ABRAÃO SANTOS (Gestor)",
                "OUTRO..."
            ]
            
            novo_nome = st.selectbox("Identificação do Operador:", lista_operadores)
            
            if novo_nome == "OUTRO...":
                novo_nome = st.text_input("Digite seu Nome Completo:")
            
            novo_usuario = st.text_input("Defina um Nome de Usuário (Login):", placeholder="Ex: larissa.duarte", key="reg_u")
            nova_senha = st.text_input("Crie uma Senha:", type="password", key="reg_p1")
            confirma_senha = st.text_input("Confirme a Senha:", type="password", key="reg_p2")
            
            if st.button("✨ CRIAR MINHA CONTA", type="primary", use_container_width=True, key="btn_registro"):
                if not novo_nome or not novo_usuario or not nova_senha:
                    st.warning("⚠️ Preencha todos os campos obrigatórios.")
                elif nova_senha != confirma_senha:
                    st.error("❌ As senhas não conferem. Tente novamente.")
                else:
                    with st.spinner("Registrando novo acesso..."):
                        try:
                            # Define o nível de permissão base
                            perfil_role = "Gestor" if "Gestor" in novo_nome else "Operador"
                            
                            # Ajuste este endpoint para combinar com a sua rota de criação de usuário no FastAPI
                            payload_registro = {
                                "nome": novo_nome.replace(" (Gestor)", ""),
                                "username": novo_usuario.strip(),
                                "password": nova_senha.strip(),
                                "role": perfil_role
                            }
                            
                            resp_reg = requests.post(f"{API_URL}/usuarios/", json=payload_registro, timeout=15)
                            
                            if resp_reg.status_code in [200, 201]:
                                st.success(f"🎉 Conta criada com sucesso para {novo_nome}! Agora volte na aba Login e acesse.")
                                st.balloons()
                            elif resp_reg.status_code == 400:
                                st.error("❌ Este nome de usuário já está em uso.")
                            else:
                                st.error(f"⚠️ Erro ao registrar. (Status: {resp_reg.status_code})")
                                
                        except Exception as e:
                            st.error("Erro de comunicação com o servidor ao tentar registrar.")