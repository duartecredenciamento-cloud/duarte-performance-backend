import pandas as pd
import streamlit as st


def get_cronograma_credenciamento():
    """Estrutura exata baseada na matriz de Credenciamento / Gestão Comercial"""
    dados = [
        {
            "Operador": "LARISSA",
            "Periodo": "MANHÃ",
            "Segunda": "EV-CITI",
            "Terça": "CONVACARE",
            "Quarta": "IMC",
            "Quinta": "MEDLIGTH",
            "Sexta": "PRÉ ALINHAMENTO",
        },
        {
            "Operador": "LARISSA",
            "Periodo": "TARDE",
            "Segunda": "-",
            "Terça": "-",
            "Quarta": "-",
            "Quinta": "-",
            "Sexta": "RESCINDIDOS (UNICLIN/MAR/SILMARO etc)",
        },
        {
            "Operador": "KARINE",
            "Periodo": "MANHÃ",
            "Segunda": "ALPHA LABs",
            "Terça": "CLINICA TOPÁZIO",
            "Quarta": "RALG (1ª e 3ª sem)",
            "Quinta": "ATIVAMENTE",
            "Sexta": "MVS",
        },
        {
            "Operador": "KARINE",
            "Periodo": "TARDE",
            "Segunda": "-",
            "Terça": "-",
            "Quarta": "PRIME (2ª sem)",
            "Quinta": "-",
            "Sexta": "DIOGO PARAUAPEBAS",
        },
        {
            "Operador": "NEIA",
            "Periodo": "MANHÃ",
            "Segunda": "CLINICA VIVENCY",
            "Terça": "LAB. BRUNO",
            "Quarta": "CLINICA AMINO",
            "Quinta": "CLINICA FARFALLA",
            "Sexta": "PRO-EXAME",
        },
        {
            "Operador": "VITÓRIA - I",
            "Periodo": "MANHÃ",
            "Segunda": "SUPORTE GERAL",
            "Terça": "SUPORTE GERAL",
            "Quarta": "SUPORTE GERAL",
            "Quinta": "SUPORTE GERAL",
            "Sexta": "SUPORTE GERAL",
        },
        {
            "Operador": "SILVANA",
            "Periodo": "MANHÃ",
            "Segunda": "HOSP. AMATO",
            "Terça": "CLIN COFFI",
            "Quarta": "RBL (1ª e 3ª sem)",
            "Quinta": "TRIDES",
            "Sexta": "HARMONY",
        },
        {
            "Operador": "SILVANA",
            "Periodo": "TARDE",
            "Segunda": "-",
            "Terça": "-",
            "Quarta": "INST. VER (2ª sem)",
            "Quinta": "-",
            "Sexta": "-",
        },
        {
            "Operador": "JULIA",
            "Periodo": "MANHÃ",
            "Segunda": "FR FISIO",
            "Terça": "CANTAREIRA",
            "Quarta": "CIE FISIO - SJC",
            "Quinta": "CLINICA ROSANA",
            "Sexta": "VIVA - TEA",
        },
        {
            "Operador": "EDVÂNIA",
            "Periodo": "MANHÃ",
            "Segunda": "REGULAÇÃO",
            "Terça": "EDITAIS",
            "Quarta": "EDITAIS",
            "Quinta": "FISO LIFE",
            "Sexta": "EMS-BETESDA (1ª e 3ª sem)",
        },
        {
            "Operador": "EDVÂNIA",
            "Periodo": "TARDE",
            "Segunda": "-",
            "Terça": "-",
            "Quarta": "-",
            "Quinta": "-",
            "Sexta": "MULHER MODERNA (2ª sem)",
        },
    ]
    return pd.DataFrame(dados)


def render_escala(carregar_cronograma_custom=None):
    # CSS Customizado Duarte Performance - Elite Design & Animations
    st.markdown(
        """
    <style>
        /* ---------------- KEYFRAMES & ANIMAÇÕES ---------------- */
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(16px); }
            to { opacity: 1; transform: translateY(0); }
        }

        @keyframes floatGradient {
            0% { background-position: 0% 50%; }
            50% { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }

        @keyframes pulseGlow {
            0% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.5); }
            70% { box-shadow: 0 0 0 10px rgba(255, 146, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
        }

        /* ---------------- HEADER ANIMADO ---------------- */
        .escala-header {
            background: linear-gradient(-45deg, #001E57, #030A1A, #0A2540, #001233);
            background-size: 300% 300%;
            animation: floatGradient 10s ease infinite, fadeIn 0.8s ease-out;
            border-radius: 18px;
            padding: 24px 30px;
            color: #FFFFFF;
            border-left: 6px solid #FF9200;
            margin-bottom: 25px;
            box-shadow: 0 12px 28px rgba(0, 30, 87, 0.2);
        }

        .badge-status-matriz {
            background: #FF9200;
            color: #FFF;
            padding: 6px 14px;
            border-radius: 99px;
            font-weight: 800;
            font-size: 0.78rem;
            letter-spacing: 0.5px;
            animation: pulseGlow 2s infinite;
        }

        .badge-lock {
            background: #10B981;
            color: #FFF;
            padding: 6px 14px;
            border-radius: 99px;
            font-weight: 800;
            font-size: 0.78rem;
        }

        /* ---------------- METRIC CARDS ---------------- */
        .metric-card {
            background: rgba(255, 255, 255, 0.95);
            backdrop-filter: blur(8px);
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 18px;
            text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.03);
            transition: all 0.3s ease;
            animation: fadeIn 0.9s ease-out;
        }

        .metric-card:hover {
            transform: translateY(-4px);
            border-color: #FF9200;
            box-shadow: 0 8px 20px rgba(0, 30, 87, 0.08);
        }

        .metric-card h3 {
            color: #001E57;
            font-size: 1.9rem;
            margin: 0;
            font-weight: 800;
        }

        .metric-card p {
            color: #64748B;
            font-size: 0.8rem;
            margin: 4px 0 0 0;
            text-transform: uppercase;
            font-weight: 700;
        }

        /* ---------------- CARDS DO OPERADOR ---------------- */
        .op-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 16px;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 4px 12px rgba(0,0,0,0.02);
            animation: fadeIn 1s ease-out;
            position: relative;
            overflow: hidden;
        }

        .op-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 4px;
            height: 100%;
            background: #001E57;
            transition: all 0.3s ease;
        }

        .op-card:hover {
            border-color: #FF9200;
            transform: translateY(-5px) scale(1.005);
            box-shadow: 0 12px 25px rgba(255, 146, 0, 0.15);
        }

        .op-card:hover::before {
            background: #FF9200;
        }

        .badge-manhatarde {
            background: rgba(0, 30, 87, 0.08);
            color: #001E57;
            padding: 4px 10px;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.5px;
        }

        .badge-cliente {
            background: linear-gradient(135deg, rgba(255, 146, 0, 0.1) 0%, rgba(255, 146, 0, 0.05) 100%);
            color: #B45309;
            border: 1px solid rgba(255, 146, 0, 0.3);
            padding: 6px 12px;
            border-radius: 10px;
            font-size: 0.9rem;
            font-weight: 700;
            display: inline-block;
            margin-top: 6px;
            transition: all 0.2s ease;
        }

        .badge-cliente:hover {
            background: rgba(255, 146, 0, 0.2);
            transform: scale(1.02);
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    # 1. IDENTIFICAÇÃO DO USUÁRIO E REGRA DE SEGURANÇA/ISOLAMENTO
    user_nome_sessao = st.session_state.get("user_nome", "").strip()
    user_role = (
        st.session_state.get("user_role", "operador").strip().lower()
    )  # 'gestor' ou 'operador'

    is_gestor = user_role in ["gestor", "admin", "coordenador"]

    # Carrega base bruta de escala
    df_escala = get_cronograma_credenciamento()

    # 2. FILTRAGEM INDIVIDUAL x VISÃO GERAL
    if not is_gestor and user_nome_sessao:
        # Tenta casar o nome do usuário logado com a coluna Operador
        df_escala_user = df_escala[
            df_escala["Operador"]
            .astype(str)
            .str.contains(user_nome_sessao, case=False, na=False)
        ]

        # Se encontrou registros específicos para este operador, aplica o isolamento
        if not df_escala_user.empty:
            df_escala = df_escala_user
            modo_isolado = True
        else:
            modo_isolado = False
    else:
        modo_isolado = False

    # 3. HEADER PRINCIPAL DA TELA
    badge_header = (
        f'<span class="badge-lock">🔒 MINHA AGENDA INDIVIDUAL ({user_nome_sessao.upper()})</span>'
        if modo_isolado
        else '<span class="badge-status-matriz">🌐 MATRIZ GERAL DA EQUIPE</span>'
    )

    st.markdown(
        f"""
    <div class="escala-header">
        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 15px;">
            <div>
                <h2 style="margin:0; font-weight: 900; font-size: 1.85rem; color: #FFF; letter-spacing: -0.5px;">
                    🗓️ Escala Semanal de Credenciamento
                </h2>
                <p style="margin: 6px 0 0 0; color: #94A3B8; font-size: 0.95rem;">
                    Distribuição Operacional & Gestão Comercial (Matriz Duarte Gestão)
                </p>
            </div>
            <div>
                {badge_header}
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    # 4. MÉTRICAS DINÂMICAS DEDICADAS
    dias_cols = ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]

    if modo_isolado:
        # Métricas focadas no Operador Logado
        total_contas = sum(
            (df_escala[dia] != "-").sum() for dia in dias_cols if dia in df_escala.columns
        )
        turnos_alocados = len(df_escala)

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f'<div class="metric-card"><h3>1</h3><p>Analista Logado ({user_nome_sessao.split()[0]})</p></div>',
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                f'<div class="metric-card"><h3'
                f' style="color:#FF9200;">{total_contas}</h3><p>Meus Serviços'
                " / Contas</p></div>",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                f'<div class="metric-card"><h3'
                f' style="color:#001E57;">{turnos_alocados}</h3><p>Turnos'
                " Escalados</p></div>",
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                '<div class="metric-card"><h3 style="color:#10B981;">100%</h3><p>Minha'
                " Capacidade</p></div>",
                unsafe_allow_html=True,
            )
    else:
        # Métricas Gerais da Operação
        total_analistas = df_escala["Operador"].nunique()

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(
                f'<div class="metric-card"><h3>{total_analistas}</h3><p>Analistas'
                " Escalados</p></div>",
                unsafe_allow_html=True,
            )
        with c2:
            st.markdown(
                '<div class="metric-card"><h3>28+</h3><p>Contas'
                " Ativas</p></div>",
                unsafe_allow_html=True,
            )
        with c3:
            st.markdown(
                '<div class="metric-card"><h3>5 Dias</h3><p>Cobertura'
                " Semanal</p></div>",
                unsafe_allow_html=True,
            )
        with c4:
            st.markdown(
                '<div class="metric-card"><h3'
                ' style="color:#FF9200;">100%</h3><p>Capacidade'
                " Operacional</p></div>",
                unsafe_allow_html=True,
            )

    st.markdown("<br>", unsafe_allow_html=True)

    # 5. BARRA DE CONTROLES E PESQUISA
    col_mode, col_dia, col_busca = st.columns([1.2, 1.2, 1.6])

    with col_mode:
        modo_view = st.radio(
            "Modo de Visão:",
            ["🎴 Cards por Dia", "📊 Tabela Completa"],
            horizontal=True,
        )

    with col_dia:
        dia_selecionado = st.selectbox(
            "Filtrar Dia da Semana:",
            ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"],
        )

    with col_busca:
        # Se for gestor, permite filtrar por qualquer operador. Se for operador, pesquisa apenas seus serviços.
        placeholder_busca = (
            "Ex: EV-CITI, Hosp. Amato..."
            if modo_isolado
            else "Ex: EV-CITI, Karine, Silvana..."
        )
        busca_termo = st.text_input(
            "🔍 Pesquisa Rápida:", placeholder=placeholder_busca
        )

    st.markdown(
        "<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 20px"
        " 0;'>",
        unsafe_allow_html=True,
    )

    # 6. FILTRAGEM INTERATIVA
    df_filtrado = df_escala.copy()

    if busca_termo:
        condicao_busca = (
            df_filtrado["Operador"].str.contains(
                busca_termo, case=False, na=False
            )
            | df_filtrado["Segunda"].str.contains(
                busca_termo, case=False, na=False
            )
            | df_filtrado["Terça"].str.contains(
                busca_termo, case=False, na=False
            )
            | df_filtrado["Quarta"].str.contains(
                busca_termo, case=False, na=False
            )
            | df_filtrado["Quinta"].str.contains(
                busca_termo, case=False, na=False
            )
            | df_filtrado["Sexta"].str.contains(
                busca_termo, case=False, na=False
            )
        )
        df_filtrado = df_filtrado[condicao_busca]

    # 7. MODO 1: CARDS ANIMADOS POR DIA
    if "Cards" in modo_view:
        st.subheader(
            f"📌 Agenda de Atendimento — {dia_selecionado.upper()}-FEIRA"
        )

        ops = df_filtrado["Operador"].unique()

        if len(ops) == 0:
            st.info(
                "ℹ️ Nenhum serviço ou atendimento encontrado para os filtros"
                " selecionados."
            )
            return

        cols_cards = st.columns(2, gap="medium")

        for idx, op in enumerate(ops):
            sub_df = df_filtrado[df_filtrado["Operador"] == op]
            target_col = cols_cards[idx % 2]

            with target_col:
                st.markdown(
                    f"""
                <div class="op-card">
                    <div style="display:flex; justify-content: space-between; align-items:center; margin-bottom: 12px;">
                        <strong style="color: #001E57; font-size: 1.15rem; font-weight: 900;">
                            👤 {op}
                        </strong>
                        <span style="font-size: 0.75rem; color: #64748B; font-weight: 700;">
                            ANALYST
                        </span>
                    </div>
                """,
                    unsafe_allow_html=True,
                )

                tem_atendimento = False
                for _, row in sub_df.iterrows():
                    cliente_dia = row.get(dia_selecionado, "-")
                    periodo = row.get("Periodo", "GERAL")

                    if cliente_dia != "-":
                        tem_atendimento = True
                        st.markdown(
                            f"""
                        <div style="margin-bottom: 12px;">
                            <span class="badge-manhatarde">{periodo}</span><br>
                            <div class="badge-cliente">🏥 {cliente_dia}</div>
                        </div>
                        """,
                            unsafe_allow_html=True,
                        )

                if not tem_atendimento:
                    st.markdown(
                        "<p style='color: #94A3B8; font-size: 0.85rem;"
                        " font-style: italic; margin: 5px 0;'>Sem alocação"
                        f" programada para {dia_selecionado.lower()}.</p>",
                        unsafe_allow_html=True,
                    )

                st.markdown("</div>", unsafe_allow_html=True)

    # 8. MODO 2: TABELA COMPLETA (VISÃO MATRIZ COMPACTA)
    else:
        st.subheader("📋 Matriz Completa de Escala Semanal")
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Operador": st.column_config.TextColumn(
                    "Analista / Operador", width="medium"
                ),
                "Periodo": st.column_config.TextColumn(
                    "Período", width="small"
                ),
                "Segunda": st.column_config.TextColumn("Segunda-Feira"),
                "Terça": st.column_config.TextColumn("Terça-Feira"),
                "Quarta": st.column_config.TextColumn("Quarta-Feira"),
                "Quinta": st.column_config.TextColumn("Quinta-Feira"),
                "Sexta": st.column_config.TextColumn("Sexta-Feira"),
            },
        )