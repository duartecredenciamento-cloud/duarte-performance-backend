import streamlit as st
import requests
import time

API_URL = "https://duarte-performance-backend.onrender.com"

def render_login():
    # Estilos CSS Exclusivos para a Tela de Autenticação Premium
    st.markdown("""
    <style>
        /* Card de Destaque Esquerdo */
        .brand-hero {
            background: linear-gradient(145deg, #001E57 0%, #030A1A 100%);
            border-radius: 24px;
            padding: 45px;
            color: #FFFFFF;
            border: 1px solid rgba(255, 255, 255, 0.08);
            box-shadow: 0 20px 40px rgba(0, 30, 87, 0.25);
            position: relative;
            overflow: hidden;
            animation: fadeInUp 0.5s ease-out forwards;
        }

        .brand-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            background: rgba(255, 146, 0, 0.15);
            border: 1px solid rgba(255, 146, 0, 0.4);
            color: #FF9200;
            padding: 6px 14px;
            border-radius: 99px;
            font-size: 0.8rem;
            font-weight: 700;
            letter-spacing: 0.5px;
            text-transform: uppercase;
            margin-bottom: 24px;
        }

        .pulse-dot {
            width: 8px;
            height: 8px;
            background-color: #FF9200;
            border-radius: 50%;
            box-shadow: 0 0 10px #FF9200;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.7); }
            70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(255, 146, 0, 0); }
            100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
        }

        .hero-title {
            font-size: 3.2rem;
            font-weight: 900;
            line-height: 1.1;
            margin-bottom: 16px;
            letter-spacing: -1px;
        }

        .hero-subtitle {
            color: #94A3B8;
            font-size: 1.1rem;
            line-height: 1.6;
            margin-bottom: 35px;
        }

        /* Metrics Grid de Fundo */
        .hero-metrics {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 16px;
            border-top: 1px solid rgba(255, 255, 255, 0.1);
            padding-top: 25px;
        }

        .metric-item {
            background: rgba(255, 255, 255, 0.03);
            border-radius: 12px;
            padding: 12px 16px;
            border: 1px solid rgba(255, 255, 255, 0.05);
        }

        .metric-val {
            font-size: 1.2rem;
            font-weight: 800;
            color: #FF9200;
        }

        .metric-lbl {
            font-size: 0.75rem;
            color: #64748B;
            text-transform: uppercase;
            font-weight: 600;
        }

        /* Container do Formulário */
        .login-card-container {
            background: #FFFFFF;
            border-radius: 24px;
            padding: 35px;
            border: 1px solid #E2E8F0;
            box-shadow: 0 15px 35px rgba(0,0,0,0.04);
        }
    </style>
    """, unsafe_allow_html=True)

    col_brand, col_form = st.columns([1.2, 1], gap="large")

    # ================= 1. BRAND HERO (LADO ESQUERDO) =================
    with col_brand:
        st.markdown('''
        <div class="brand-hero">
            <div class="brand-badge">
                <div class="pulse-dot"></div> Sistema Operacional v2.4
            </div>
            
            <div class="hero-title">
                Duarte<br><span style="color: #FF9200;">Performance</span>
            </div>
            
            <div class="hero-subtitle">
                Central de Inteligência Operacional & Credenciamento de Saúde. Acompanhamento e auditoria em tempo real.
            </div>

            <div class="hero-metrics">
                <div class="metric-item">
                    <div class="metric-val">100% Digital</div>
                    <div class="metric-lbl">Fluxo Automatizado</div>
                </div>
                <div class="metric-item">
                    <div class="metric-val">99.8% SLA</div>
                    <div class="metric-lbl">Disponibilidade</div>
                </div>
            </div>
        </div>
        ''', unsafe_allow_html=True)

    # ================= 2. FORMULÁRIO DE ACESSO (LADO DIREITO) =================
    with col_form:
        st.markdown('<div class="login-card-container">', unsafe_allow_html=True)
        
        tab_login, tab_signup = st.tabs(["🔑 Acessar Conta", "🆕 Solicitar Acesso"])

        # ----- TAB 1: LOGIN -----
        with tab_login:
            st.markdown("<br>", unsafe_allow_html=True)
            username_input = st.text_input("Usuário ou E-mail Corporate", placeholder="ex: erick.duarte", key="login_username")
            senha_input = st.text_input("Senha de Segurança", type="password", placeholder="••••••••", key="login_senha")

            st.markdown("<br>", unsafe_allow_html=True)
            
            if st.button("🚀 ENTRAR NA PLATAFORMA", type="primary", use_container_width=True):
                if not username_input or not senha_input:
                    st.warning("⚠️ Preencha seu usuário e senha para continuar.")
                else:
                    try:
                        with st.spinner("Verificando credenciais..."):
                            resp = requests.post(
                                f"{API_URL}/token", 
                                data={"username": username_input.strip(), "password": senha_input}, 
                                timeout=12
                            )
                        
                        if resp.status_code == 200:
                            data = resp.json()
                            st.session_state.update({
                                "token": data["access_token"],
                                "username": data.get("username"),
                                "nome": data.get("nome"),
                                "role": data.get("role", "Operador"),
                                "perfil_completo": data.get("perfil_completo", True)
                            })
                            st.success("✨ Autenticado com sucesso! Carregando seu ambiente...")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Credenciais inválidas. Verifique seu usuário e senha.")
                    except Exception:
                        st.error("⚠️ Servidor indisponível no momento. Tente novamente em instantes.")

        # ----- TAB 2: SOLICITAÇÃO DE CADASTRO -----
        with tab_signup:
            st.markdown("<br>", unsafe_allow_html=True)
            novo_nome = st.text_input("Nome Completo", placeholder="ex: Erick Duarte", key="signup_nome")
            novo_user = st.text_input("Usuário Desejado", placeholder="ex: erick.duarte", key="signup_user")
            nova_senha = st.text_input("Crie uma Senha", type="password", placeholder="••••••••", key="signup_pass")

            st.markdown("<br>", unsafe_allow_html=True)

            if st.button("📩 SOLICITAR CREDENCIAMENTO", use_container_width=True):
                if not novo_nome or not novo_user or not nova_senha:
                    st.warning("⚠️ Preencha todos os campos obrigatórios.")
                else:
                    try:
                        with st.spinner("Enviando solicitação à gestão..."):
                            payload = {
                                "nome": novo_nome.strip(),
                                "username": novo_user.strip(),
                                "password": nova_senha
                            }
                            resp = requests.post(f"{API_URL}/usuarios/solicitar", json=payload, timeout=12)
                            
                        if resp.status_code in [200, 201]:
                            st.success("✅ Solicitação enviada! Aguarde a liberação do seu gestor.")
                        else:
                            st.info("ℹ️ Solicitação enviada. Um administrador entrará em contato para liberar seu acesso.")
                    except Exception:
                        st.error("⚠️ Falha ao registrar solicitação. Verifique sua conexão.")

        st.markdown('</div>', unsafe_allow_html=True)