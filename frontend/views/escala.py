import streamlit as st
import pandas as pd

def get_cronograma_credenciamento():
    """
    Estrutura exata baseada na matriz de Credenciamento / Gestão Comercial
    """
    dados = [
        {
            "Operador": "LARISSA",
            "Periodo": "MANHÃ",
            "Segunda": "EV-CITI",
            "Terça": "CONVACARE",
            "Quarta": "IMC",
            "Quinta": "MEDLIGTH",
            "Sexta": "PRÉ ALINHAMENTO"
        },
        {
            "Operador": "LARISSA",
            "Periodo": "TARDE",
            "Segunda": "-",
            "Terça": "-",
            "Quarta": "-",
            "Quinta": "-",
            "Sexta": "RESCINDIDOS (UNICLIN/MAR/SILMARO etc)"
        },
        {
            "Operador": "KARINE",
            "Periodo": "MANHÃ",
            "Segunda": "ALPHA LABs",
            "Terça": "CLINICA TOPÁZIO",
            "Quarta": "RALG (1ª e 3ª sem)",
            "Quinta": "ATIVAMENTE",
            "Sexta": "MVS"
        },
        {
            "Operador": "KARINE",
            "Periodo": "TARDE",
            "Segunda": "-",
            "Terça": "-",
            "Quarta": "PRIME (2ª sem)",
            "Quinta": "-",
            "Sexta": "DIOGO PARAUAPEBAS"
        },
        {
            "Operador": "NEIA",
            "Periodo": "MANHÃ",
            "Segunda": "CLINICA VIVENCY",
            "Terça": "LAB. BRUNO",
            "Quarta": "CLINICA AMINO",
            "Quinta": "CLINICA FARFALLA",
            "Sexta": "PRO-EXAME"
        },
        {
            "Operador": "VITÓRIA - I",
            "Periodo": "MANHÃ",
            "Segunda": "SUPORTE GERAL",
            "Terça": "SUPORTE GERAL",
            "Quarta": "SUPORTE GERAL",
            "Quinta": "SUPORTE GERAL",
            "Sexta": "SUPORTE GERAL"
        },
        {
            "Operador": "SILVANA",
            "Periodo": "MANHÃ",
            "Segunda": "HOSP. AMATO",
            "Terça": "CLIN COFFI",
            "Quarta": "RBL (1ª e 3ª sem)",
            "Quinta": "TRIDES",
            "Sexta": "HARMONY"
        },
        {
            "Operador": "SILVANA",
            "Periodo": "TARDE",
            "Segunda": "-",
            "Terça": "-",
            "Quarta": "INST. VER (2ª sem)",
            "Quinta": "-",
            "Sexta": "-"
        },
        {
            "Operador": "JULIA",
            "Periodo": "MANHÃ",
            "Segunda": "FR FISIO",
            "Terça": "CANTAREIRA",
            "Quarta": "CIE FISIO - SJC",
            "Quinta": "CLINICA ROSANA",
            "Sexta": "VIVA - TEA"
        },
        {
            "Operador": "EDVÂNIA",
            "Periodo": "MANHÃ",
            "Segunda": "REGULAÇÃO",
            "Terça": "EDITAIS",
            "Quarta": "EDITAIS",
            "Quinta": "FISO LIFE",
            "Sexta": "EMS-BETESDA (1ª e 3ª sem)"
        },
        {
            "Operador": "EDVÂNIA",
            "Periodo": "TARDE",
            "Segunda": "-",
            "Terça": "-",
            "Quarta": "-",
            "Quinta": "-",
            "Sexta": "MULHER MODERNA (2ª sem)"
        }
    ]
    return pd.DataFrame(dados)


def render_escala(carregar_cronograma_custom=None):
    # CSS Customizado Duarte Performance
    st.markdown("""
    <style>
        .escala-header {
            background: linear-gradient(135deg, #001E57 0%, #030A1A 100%);
            border-radius: 16px;
            padding: 24px 30px;
            color: #FFFFFF;
            border-left: 6px solid #FF9200;
            margin-bottom: 25px;
            box-shadow: 0 10px 25px rgba(0, 30, 87, 0.15);
        }
        .metric-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 12px;
            padding: 16px;
            text-align: center;
            box-shadow: 0 4px 12px rgba(0,0,0,0.03);
        }
        .metric-card h3 {
            color: #001E57;
            font-size: 1.8rem;
            margin: 0;
            font-weight: 800;
        }
        .metric-card p {
            color: #64748B;
            font-size: 0.82rem;
            margin: 0;
            text-transform: uppercase;
            font-weight: 600;
        }
        .op-card {
            background: #FFFFFF;
            border: 1px solid #E2E8F0;
            border-radius: 14px;
            padding: 18px;
            margin-bottom: 15px;
            transition: all 0.2s ease;
        }
        .op-card:hover {
            border-color: #FF9200;
            box-shadow: 0 6px 18px rgba(255, 146, 0, 0.12);
        }
        .badge-manhatarde {
            background: rgba(0, 30, 87, 0.08);
            color: #001E57;
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 0.72rem;
            font-weight: 700;
        }
        .badge-cliente {
            background: rgba(255, 146, 0, 0.12);
            color: #D97706;
            border: 1px solid rgba(255, 146, 0, 0.3);
            padding: 4px 10px;
            border-radius: 8px;
            font-size: 0.88rem;
            font-weight: 700;
            display: inline-block;
            margin-top: 4px;
        }
    </style>
    """, unsafe_allow_html=True)

    # Top Header
    st.markdown("""
    <div class="escala-header">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <div>
                <h2 style="margin:0; font-weight: 900; font-size: 1.8rem; color: #FFF;">🗓️ Escala Semanal de Credenciamento</h2>
                <p style="margin: 4px 0 0 0; color: #94A3B8; font-size: 0.95rem;">
                    Distribuição Operacional & Gestão Comercial (Matriz de Atendimento)
                </p>
            </div>
            <span style="background: #FF9200; color: #FFF; padding: 6px 14px; border-radius: 99px; font-weight: 800; font-size: 0.8rem;">
                MATRIZ OFICIAL
            </span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    # Carrega dados padrão ou a função injetada
    df_escala = get_cronograma_credenciamento()

    # Métricas Superiores
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown('<div class="metric-card"><h3>7</h3><p>Analistas Escalados</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="metric-card"><h3>28+</h3><p>Contas Ativas</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="metric-card"><h3>5 Dias</h3><p>Cobertura Semanal</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="metric-card"><h3 style="color:#FF9200;">100%</h3><p>Capacidade Operacional</p></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Controles de Visualização e Filtro
    col_mode, col_dia, col_busca = st.columns([1.2, 1.2, 1.6])
    
    with col_mode:
        modo_view = st.radio("Modo de Visão:", ["🎴 Cards por Dia", "📊 Tabela Completa"], horizontal=True)

    with col_dia:
        dia_selecionado = st.selectbox(
            "Filtrar Dia da Semana:",
            ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
        )

    with col_busca:
        busca_termo = st.text_input("🔍 Buscar Cliente ou Operador:", placeholder="Ex: EV-CITI, Karine, Hosp. Amato...")

    st.markdown("<hr style='border: 0; border-top: 1px solid #E2E8F0; margin: 20px 0;'>", unsafe_allow_html=True)

    # FILTRAGEM
    if busca_termo:
        df_filtrado = df_escala[
            df_escala["Operador"].str.contains(busca_termo, case=False, na=False) |
            df_escala["Segunda"].str.contains(busca_termo, case=False, na=False) |
            df_escala["Terça"].str.contains(busca_termo, case=False, na=False) |
            df_escala["Quarta"].str.contains(busca_termo, case=False, na=False) |
            df_escala["Quinta"].str.contains(busca_termo, case=False, na=False) |
            df_escala["Sexta"].str.contains(busca_termo, case=False, na=False)
        ]
    else:
        df_filtrado = df_escala

    # MODO 1: CARDS POR DIA
    if "Cards" in modo_view:
        st.subheader(f"📌 Agenda de Atendimento — {dia_selecionado.upper()}-FEIRA")
        
        ops = df_filtrado["Operador"].unique()
        cols_cards = st.columns(2)
        
        idx = 0
        for op in ops:
            sub_df = df_filtrado[df_filtrado["Operador"] == op]
            target_col = cols_cards[idx % 2]
            
            with target_col:
                st.markdown(f'''
                <div class="op-card">
                    <div style="display:flex; justify-size: space-between; align-items:center; margin-bottom: 10px;">
                        <strong style="color: #001E57; font-size: 1.1rem;">👤 {op}</strong>
                    </div>
                ''', unsafe_allow_html=True)
                
                for _, row in sub_df.iterrows():
                    cliente_dia = row[dia_selecionado]
                    periodo = row["Periodo"]
                    if cliente_dia != "-":
                        st.markdown(f'''
                        <div style="margin-bottom: 8px;">
                            <span class="badge-manhatarde">{periodo}</span>
                            <div class="badge-cliente">{cliente_dia}</div>
                        </div>
                        ''', unsafe_allow_html=True)
                
                st.markdown('</div>', unsafe_allow_html=True)
            idx += 1

    # MODO 2: TABELA COMPLETA (VISÃO MATRIZ)
    else:
        st.subheader("📋 Matriz Completa de Escala Semanal")
        st.dataframe(
            df_filtrado,
            use_container_width=True,
            hide_index=True,
            column_config={
                "Operador": st.column_config.TextColumn("Analista / Operador", width="medium"),
                "Periodo": st.column_config.TextColumn("Período", width="small"),
                "Segunda": st.column_config.TextColumn("Segunda-Feira"),
                "Terça": st.column_config.TextColumn("Terça-Feira"),
                "Quarta": st.column_config.TextColumn("Quarta-Feira"),
                "Quinta": st.column_config.TextColumn("Quinta-Feira"),
                "Sexta": st.column_config.TextColumn("Sexta-Feira"),
            }
        )