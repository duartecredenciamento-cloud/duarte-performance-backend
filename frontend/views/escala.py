import os
import pandas as pd
import streamlit as st
import requests

from tabela_pro import inject_tabela_css, mostrar_tabela

API_URL = os.getenv(
    "BACKEND_URL",
    "https://duarte-performance-backend-production.up.railway.app",
)


def _normalizar_colunas_escala(df: pd.DataFrame) -> pd.DataFrame:
    if df is None or (hasattr(df, "empty") and df.empty):
        return pd.DataFrame(
            columns=["Operador", "Periodo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
        )

    df = df.copy()

    mapa = {
        "operador": "Operador", "Operador": "Operador", "OPERADOR": "Operador",
        "analista": "Operador", "Analista": "Operador",
        "periodo": "Periodo", "Periodo": "Periodo", "PERIODO": "Periodo",
        "período": "Periodo", "Período": "Periodo",
        "segunda": "Segunda", "Segunda": "Segunda", "SEGUNDA": "Segunda",
        "terca": "Terça", "terça": "Terça", "Terca": "Terça", "Terça": "Terça",
        "TERÇA": "Terça", "TERCA": "Terça",
        "quarta": "Quarta", "Quarta": "Quarta", "QUARTA": "Quarta",
        "quinta": "Quinta", "Quinta": "Quinta", "QUINTA": "Quinta",
        "sexta": "Sexta", "Sexta": "Sexta", "SEXTA": "Sexta",
        "id": "id", "Id": "id", "ID": "id",
    }

    colunas_lower = {str(c).strip().lower(): c for c in df.columns}
    rename_dict = {}
    for chave_mapa, nome_padrao in mapa.items():
        chave_l = chave_mapa.lower()
        if chave_l in colunas_lower:
            rename_dict[colunas_lower[chave_l]] = nome_padrao

    if rename_dict:
        df = df.rename(columns=rename_dict)

    obrigatorias = ["Operador", "Periodo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
    for col in obrigatorias:
        if col not in df.columns:
            df[col] = "-"

    for col in obrigatorias:
        df[col] = df[col].fillna("-").astype(str).str.strip()
        df[col] = df[col].replace({"": "-", "nan": "-", "None": "-"})

    cols_final = obrigatorias + (["id"] if "id" in df.columns else [])
    return df[[c for c in cols_final if c in df.columns]]


def get_cronograma_credenciamento(api_url=None, token=None):
    url = api_url or API_URL
    if url and token:
        try:
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(f"{url}/cronograma/", headers=headers, timeout=8)
            if response.status_code == 200:
                dados_api = response.json()
                if dados_api:
                    return _normalizar_colunas_escala(pd.DataFrame(dados_api))
        except Exception:
            pass

    dados = [
        {"Operador": "LARISSA", "Periodo": "MANHÃ", "Segunda": "EV-CITI", "Terça": "CONVACARE", "Quarta": "IMC", "Quinta": "MEDLIGTH", "Sexta": "PRÉ ALINHAMENTO"},
        {"Operador": "LARISSA", "Periodo": "TARDE", "Segunda": "-", "Terça": "-", "Quarta": "-", "Quinta": "-", "Sexta": "RESCINDIDOS - UNICLIN/MAR/SILMARO e ETC"},
        {"Operador": "KARINE", "Periodo": "MANHÃ", "Segunda": "ALPHA LABs", "Terça": "CLINICA TOPÁZIO", "Quarta": "RALG 1° e 3° SEMANA", "Quinta": "ATIVAMENTE", "Sexta": "MVS"},
        {"Operador": "KARINE", "Periodo": "TARDE", "Segunda": "-", "Terça": "-", "Quarta": "PRIME 2° SEMANA", "Quinta": "-", "Sexta": "DIOGO PARAUAPEBAS"},
        {"Operador": "NEIA", "Periodo": "MANHÃ", "Segunda": "CLINICA VIVENCY", "Terça": "RBL 1° e 3° SEMANA", "Quarta": "CLINICA AMINO", "Quinta": "CLINICA FARFALLA", "Sexta": "INST. VER"},
        {"Operador": "NEIA", "Periodo": "TARDE", "Segunda": "-", "Terça": "-", "Quarta": "-", "Quinta": "-", "Sexta": "-"},
        {"Operador": "SILVANA", "Periodo": "MANHÃ", "Segunda": "PRO-EXAME", "Terça": "CLIN COFFI", "Quarta": "HOSP. AMATO", "Quinta": "TRIDES", "Sexta": "HARMONY"},
        {"Operador": "SILVANA", "Periodo": "TARDE", "Segunda": "-", "Terça": "-", "Quarta": "LAB. BRUNO", "Quinta": "-", "Sexta": "-"},
        {"Operador": "JULIA", "Periodo": "MANHÃ", "Segunda": "FR FISIO", "Terça": "CANTAREIRA", "Quarta": "CIE FISIO - SJC", "Quinta": "CLINICA ROSANA", "Sexta": "VIVA - TEA"},
        {"Operador": "JULIA", "Periodo": "TARDE", "Segunda": "-", "Terça": "-", "Quarta": "-", "Quinta": "-", "Sexta": "-"},
        {"Operador": "EDVÂNIA", "Periodo": "MANHÃ", "Segunda": "REGULAÇÃO", "Terça": "EDITAIS", "Quarta": "EDITAIS", "Quinta": "FISO LIFE", "Sexta": "EMS-BETESDA 1º e 3º SEMANA"},
        {"Operador": "EDVÂNIA", "Periodo": "TARDE", "Segunda": "-", "Terça": "-", "Quarta": "-", "Quinta": "-", "Sexta": "MULHER MODERNA 2° SEMANA"},
    ]
    return _normalizar_colunas_escala(pd.DataFrame(dados))


def _headers():
    token = st.session_state.get("token")
    return {"Authorization": f"Bearer {token}"} if token else {}


def _linhas_com_id(df: pd.DataFrame) -> list:
    if df is None or df.empty or "id" not in df.columns:
        return []
    out = []
    for _, r in df.iterrows():
        try:
            iid = int(float(r["id"]))
            out.append(f"#{iid} — {r['Operador']} ({r['Periodo']})")
        except Exception:
            continue
    return out


def render_escala(carregar_cronograma_custom=None):
    st.markdown(
        """
    <style>
        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to   { opacity: 1; transform: translateY(0); }
        }
        @keyframes floatGradient {
            0%   { background-position: 0% 50%; }
            50%  { background-position: 100% 50%; }
            100% { background-position: 0% 50%; }
        }
        @keyframes pulseGlow {
            0%   { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0.55); }
            70%  { box-shadow: 0 0 0 14px rgba(255, 146, 0, 0); }
            100% { box-shadow: 0 0 0 0 rgba(255, 146, 0, 0); }
        }

        .escala-header {
            background: linear-gradient(-45deg, #001E57, #030A1A, #0B296B, #001233);
            background-size: 320% 320%;
            animation: floatGradient 11s ease infinite, fadeInUp 0.55s ease-out;
            border-radius: 22px;
            padding: 28px 32px;
            color: #FFFFFF;
            border-left: 6px solid #FF9200;
            margin-bottom: 26px;
            box-shadow:
                0 18px 45px rgba(0, 30, 87, 0.28),
                0 0 0 1px rgba(255, 146, 0, 0.12);
            position: relative;
            overflow: hidden;
        }
        .escala-header::before {
            content: '';
            position: absolute;
            top: -50%;
            right: -8%;
            width: 280px;
            height: 280px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(255,146,0,0.22) 0%, transparent 68%);
            pointer-events: none;
        }
        .escala-header::after {
            content: '';
            position: absolute;
            bottom: -40%;
            left: 15%;
            width: 180px;
            height: 180px;
            border-radius: 50%;
            background: radial-gradient(circle, rgba(11,41,107,0.5) 0%, transparent 70%);
            pointer-events: none;
        }
        .escala-header h2 {
            margin: 0;
            font-weight: 900;
            font-size: 1.9rem;
            letter-spacing: -0.6px;
            color: #FFF;
            position: relative;
            z-index: 1;
        }
        .escala-header p {
            margin: 8px 0 0 0;
            color: #A5B4C8;
            font-size: 0.95rem;
            position: relative;
            z-index: 1;
        }

        .badge-status-matriz {
            background: linear-gradient(135deg, #FF9200 0%, #FFB84D 100%);
            color: #FFF;
            padding: 7px 16px;
            border-radius: 99px;
            font-weight: 800;
            font-size: 0.75rem;
            letter-spacing: 0.5px;
            animation: pulseGlow 2.2s infinite;
            box-shadow: 0 4px 16px rgba(255, 146, 0, 0.35);
            position: relative;
            z-index: 1;
        }
        .badge-lock {
            background: linear-gradient(135deg, #10B981 0%, #34D399 100%);
            color: #FFF;
            padding: 7px 16px;
            border-radius: 99px;
            font-weight: 800;
            font-size: 0.75rem;
            box-shadow: 0 4px 14px rgba(16, 185, 129, 0.3);
            position: relative;
            z-index: 1;
        }

        .metric-card {
            background: linear-gradient(180deg, #FFFFFF 0%, #F8FAFC 100%);
            border: 1px solid #E2E8F0;
            border-radius: 18px;
            padding: 22px 16px;
            text-align: center;
            box-shadow: 0 8px 24px rgba(0, 30, 87, 0.06);
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            animation: fadeInUp 0.65s ease-out;
        }
        .metric-card:hover {
            transform: translateY(-6px) scale(1.02);
            border-color: rgba(255, 146, 0, 0.5);
            box-shadow: 0 16px 36px rgba(255, 146, 0, 0.15);
        }
        .metric-card h3 {
            color: #001E57;
            font-size: 2rem;
            margin: 0;
            font-weight: 900;
            letter-spacing: -0.5px;
        }
        .metric-card p {
            color: #64748B;
            font-size: 0.72rem;
            margin: 6px 0 0 0;
            text-transform: uppercase;
            font-weight: 800;
            letter-spacing: 0.5px;
        }

        .op-card {
            background: #FFFFFF;
            border: 1px solid #E8EEF5;
            border-radius: 18px;
            padding: 22px;
            margin-bottom: 16px;
            position: relative;
            overflow: hidden;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
            box-shadow: 0 6px 20px rgba(0, 30, 87, 0.04);
            animation: fadeInUp 0.75s ease-out;
        }
        .op-card::before {
            content: '';
            position: absolute;
            top: 0;
            left: 0;
            width: 5px;
            height: 100%;
            background: linear-gradient(180deg, #001E57 0%, #FF9200 100%);
        }
        .op-card:hover {
            transform: translateY(-6px);
            border-color: rgba(255, 146, 0, 0.4);
            box-shadow: 0 18px 40px rgba(255, 146, 0, 0.14);
        }

        .badge-manhatarde {
            background: linear-gradient(135deg, rgba(0, 30, 87, 0.1), rgba(11, 41, 107, 0.08));
            color: #001E57;
            padding: 5px 12px;
            border-radius: 8px;
            font-size: 0.7rem;
            font-weight: 800;
            letter-spacing: 0.6px;
            border: 1px solid rgba(0, 30, 87, 0.12);
        }
        .badge-cliente {
            background: linear-gradient(135deg, rgba(255, 146, 0, 0.16) 0%, rgba(255, 184, 77, 0.1) 100%);
            color: #C2410C;
            border: 1px solid rgba(255, 146, 0, 0.35);
            padding: 8px 14px;
            border-radius: 12px;
            font-size: 0.9rem;
            font-weight: 800;
            display: inline-block;
            margin-top: 8px;
        }

        div[data-testid="stHorizontalBlock"] label {
            font-weight: 700 !important;
            color: #001E57 !important;
        }
    </style>
    """,
        unsafe_allow_html=True,
    )

    inject_tabela_css()

    user_nome_sessao = str(
        st.session_state.get("user_nome") or st.session_state.get("nome") or ""
    ).strip()
    user_role = str(
        st.session_state.get("user_role") or st.session_state.get("role") or "operador"
    ).strip().lower()

    FUNCOES_VISAO_COMPLETA = ["gestor", "admin", "admin master", "coordenador", "visualizador"]
    tem_visao_completa = user_role in FUNCOES_VISAO_COMPLETA
    is_admin_gestor = user_role in ["admin", "admin master", "gestor"]
    is_visualizador = user_role == "visualizador"

    df_escala = None
    if carregar_cronograma_custom:
        try:
            df_escala = carregar_cronograma_custom()
        except Exception:
            df_escala = None

    if df_escala is None or (hasattr(df_escala, "empty") and df_escala.empty):
        df_escala = get_cronograma_credenciamento(API_URL, st.session_state.get("token"))

    df_escala = _normalizar_colunas_escala(df_escala)

    if not tem_visao_completa and user_nome_sessao:
        df_user = df_escala[
            df_escala["Operador"].astype(str).str.contains(user_nome_sessao, case=False, na=False)
        ]
        if not df_user.empty:
            df_escala = df_user
            modo_isolado = True
        else:
            modo_isolado = False
    else:
        modo_isolado = False

    if modo_isolado:
        badge_header = f'<span class="badge-lock">🔒 MINHA AGENDA ({user_nome_sessao.upper()})</span>'
    elif is_visualizador:
        badge_header = '<span class="badge-status-matriz">👁️ SOMENTE LEITURA</span>'
    else:
        badge_header = '<span class="badge-status-matriz">🌐 MATRIZ GERAL DA EQUIPE</span>'

    st.markdown(
        f"""
    <div class="escala-header">
        <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:15px;">
            <div>
                <h2 style="margin:0;font-weight:900;font-size:1.85rem;color:#FFF;">
                    🗓️ Escala Semanal de Credenciamento
                </h2>
                <p style="margin:6px 0 0 0;color:#94A3B8;font-size:0.95rem;">
                    Matriz Duarte Gestão — Agosto
                </p>
            </div>
            <div>{badge_header}</div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    total_analistas = df_escala["Operador"].nunique() if not df_escala.empty else 0
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.markdown(f'<div class="metric-card"><h3>{total_analistas}</h3><p>Analistas</p></div>', unsafe_allow_html=True)
    with c2:
        st.markdown('<div class="metric-card"><h3>28+</h3><p>Contas Ativas</p></div>', unsafe_allow_html=True)
    with c3:
        st.markdown('<div class="metric-card"><h3>5 Dias</h3><p>Cobertura</p></div>', unsafe_allow_html=True)
    with c4:
        st.markdown('<div class="metric-card"><h3 style="color:#FF9200;">100%</h3><p>Capacidade</p></div>', unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    col_mode, col_dia, col_busca = st.columns([1.2, 1.2, 1.6])
    with col_mode:
        modo_view = st.radio("Modo de Visão:", ["🎴 Cards por Dia", "📊 Tabela Completa"], horizontal=True)
    with col_dia:
        dia_selecionado = st.selectbox("Filtrar Dia:", ["Segunda", "Terça", "Quarta", "Quinta", "Sexta"])
    with col_busca:
        busca_termo = st.text_input("🔍 Pesquisa:", placeholder="Ex: EV-CITI, Karine...")

    st.markdown("<hr style='border:0;border-top:1px solid #E2E8F0;margin:20px 0;'>", unsafe_allow_html=True)

    df_filtrado = df_escala.copy()
    if busca_termo:
        mask = (
            df_filtrado["Operador"].str.contains(busca_termo, case=False, na=False)
            | df_filtrado["Segunda"].str.contains(busca_termo, case=False, na=False)
            | df_filtrado["Terça"].str.contains(busca_termo, case=False, na=False)
            | df_filtrado["Quarta"].str.contains(busca_termo, case=False, na=False)
            | df_filtrado["Quinta"].str.contains(busca_termo, case=False, na=False)
            | df_filtrado["Sexta"].str.contains(busca_termo, case=False, na=False)
        )
        df_filtrado = df_filtrado[mask]

    if "Cards" in modo_view:
        st.subheader(f"📌 Agenda — {dia_selecionado.upper()}-FEIRA")
        ops = df_filtrado["Operador"].unique() if not df_filtrado.empty else []
        if len(ops) == 0:
            st.info("Nenhum serviço encontrado.")
        else:
            cols = st.columns(2, gap="medium")
            for idx, op in enumerate(ops):
                sub = df_filtrado[df_filtrado["Operador"] == op]
                with cols[idx % 2]:
                    st.markdown(
                        f"""<div class="op-card"><strong style="color:#001E57;font-size:1.15rem;">👤 {op}</strong>""",
                        unsafe_allow_html=True,
                    )
                    tem = False
                    for _, row in sub.iterrows():
                        cli = row.get(dia_selecionado, "-")
                        per = row.get("Periodo", "GERAL")
                        if cli and cli != "-":
                            tem = True
                            st.markdown(
                                f"""<div style="margin:10px 0;">
                                <span class="badge-manhatarde">{per}</span><br>
                                <div class="badge-cliente">🏥 {cli}</div></div>""",
                                unsafe_allow_html=True,
                            )
                    if not tem:
                        st.caption(f"Sem alocação em {dia_selecionado.lower()}.")
                    st.markdown("</div>", unsafe_allow_html=True)
    else:
        # ===== TABELA PREMIUM =====
        cols_vis = [
            c for c in ["Operador", "Periodo", "Segunda", "Terça", "Quarta", "Quinta", "Sexta"]
            if c in df_filtrado.columns
        ]
        mostrar_tabela(
            df_filtrado[cols_vis] if cols_vis else df_filtrado,
            titulo="📋 Matriz Completa da Escala",
            max_linhas=200,
            injetar_css=False,
        )

    # =====================================================
    # GESTÃO ADMIN
    # =====================================================
    if is_admin_gestor and not modo_isolado:
        st.markdown("---")
        st.subheader("🛠️ Gestão da Escala (Admin)")

        tab_add, tab_edit, tab_del = st.tabs([
            "➕ Adicionar",
            "✏️ Editar linha",
            "🗑️ Excluir",
        ])

        with tab_add:
            st.caption("Cria uma nova linha na matriz (operador + período + clientes).")
            c1, c2 = st.columns(2)
            with c1:
                novo_op = st.text_input("Nome do operador *", placeholder="Ex: MARIA", key="add_op")
                novo_periodo = st.selectbox("Período *", ["MANHÃ", "TARDE", "INTEGRAL"], key="add_per")
            with c2:
                seg = st.text_input("Segunda", value="-", key="add_seg")
                ter = st.text_input("Terça", value="-", key="add_ter")
                qua = st.text_input("Quarta", value="-", key="add_qua")
                qui = st.text_input("Quinta", value="-", key="add_qui")
                sex = st.text_input("Sexta", value="-", key="add_sex")

            if st.button("💾 Salvar na escala", type="primary", use_container_width=True, key="btn_add"):
                if not novo_op.strip():
                    st.error("Informe o nome do operador.")
                else:
                    payload = {
                        "Operador": novo_op.strip().upper(),
                        "Periodo": novo_periodo,
                        "Segunda": seg.strip() or "-",
                        "Terça": ter.strip() or "-",
                        "Quarta": qua.strip() or "-",
                        "Quinta": qui.strip() or "-",
                        "Sexta": sex.strip() or "-",
                    }
                    try:
                        r = requests.post(
                            f"{API_URL}/cronograma/",
                            json=payload,
                            headers={**_headers(), "Content-Type": "application/json"},
                            timeout=20,
                        )
                        if r.status_code in (200, 201):
                            st.success("✅ Linha adicionada!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Erro: {r.text}")
                    except Exception as e:
                        st.error(f"Falha: {e}")

        with tab_edit:
            st.caption("Altera operador, período ou clientes de uma linha existente.")
            linhas = _linhas_com_id(df_escala)

            if not linhas:
                st.warning(
                    "A API ainda não retornou IDs (matriz local em uso). "
                    "Depois que o backend gravar no banco, a edição aparece aqui."
                )
            else:
                escolha = st.selectbox("Escolha a linha", linhas, key="edit_sel")
                item_id = int(escolha.split("—")[0].replace("#", "").strip())
                row = df_escala[df_escala["id"].astype(str).str.replace(".0", "", regex=False) == str(item_id)]
                if row.empty:
                    st.error("Linha não encontrada.")
                else:
                    row = row.iloc[0]
                    periodos = ["MANHÃ", "TARDE", "INTEGRAL"]
                    per_atual = str(row.get("Periodo", "MANHÃ"))
                    idx_per = periodos.index(per_atual) if per_atual in periodos else 0

                    e1, e2 = st.columns(2)
                    with e1:
                        ed_op = st.text_input("Operador", value=str(row["Operador"]), key="ed_op")
                        ed_per = st.selectbox("Período", periodos, index=idx_per, key="ed_per")
                    with e2:
                        ed_seg = st.text_input("Segunda", value=str(row["Segunda"]), key="ed_seg")
                        ed_ter = st.text_input("Terça", value=str(row["Terça"]), key="ed_ter")
                        ed_qua = st.text_input("Quarta", value=str(row["Quarta"]), key="ed_qua")
                        ed_qui = st.text_input("Quinta", value=str(row["Quinta"]), key="ed_qui")
                        ed_sex = st.text_input("Sexta", value=str(row["Sexta"]), key="ed_sex")

                    if st.button("💾 Salvar alterações", type="primary", use_container_width=True, key="btn_edit"):
                        payload = {
                            "Operador": ed_op.strip().upper(),
                            "Periodo": ed_per,
                            "Segunda": ed_seg.strip() or "-",
                            "Terça": ed_ter.strip() or "-",
                            "Quarta": ed_qua.strip() or "-",
                            "Quinta": ed_qui.strip() or "-",
                            "Sexta": ed_sex.strip() or "-",
                        }
                        try:
                            r = requests.put(
                                f"{API_URL}/cronograma/{item_id}",
                                json=payload,
                                headers={**_headers(), "Content-Type": "application/json"},
                                timeout=20,
                            )
                            if r.status_code in (200, 201):
                                st.success("✅ Escala atualizada!")
                                st.cache_data.clear()
                                st.rerun()
                            else:
                                st.error(f"Erro: {r.text}")
                        except Exception as e:
                            st.error(f"Falha: {e}")

        with tab_del:
            st.caption("Remove uma linha da matriz.")
            linhas_del = _linhas_com_id(df_escala)
            if not linhas_del:
                st.warning("API ainda não retornou IDs (matriz local em uso).")
            else:
                escolha_del = st.selectbox("Linha para excluir", linhas_del, key="del_sel")
                if st.button("🗑️ Confirmar exclusão", type="secondary", key="btn_del"):
                    item_id = int(escolha_del.split("—")[0].replace("#", "").strip())
                    try:
                        r = requests.delete(
                            f"{API_URL}/cronograma/{item_id}",
                            headers=_headers(),
                            timeout=20,
                        )
                        if r.status_code in (200, 204):
                            st.success("Linha excluída!")
                            st.cache_data.clear()
                            st.rerun()
                        else:
                            st.error(f"Erro: {r.text}")
                    except Exception as e:
                        st.error(f"Falha: {e}")