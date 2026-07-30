"""
Helper de permissões reutilizável entre as views do Streamlit.

Uso sugerido em qualquer tela com botões de criar/editar/excluir
(ex.: views/editor.py, views/lancamento.py):

    from views.permissoes import pode_editar, aviso_somente_leitura

    role = st.session_state.get("user_role", "operador")

    if not pode_editar(role):
        aviso_somente_leitura()
    else:
        # mostra os botões/formulários normalmente
        ...
"""

import streamlit as st

# Perfis que podem criar, editar ou excluir informações.
ROLES_COM_EDICAO = {"admin", "gestor", "operador", "coordenador"}

# Perfil somente-leitura (Admin Leitura).
ROLES_SOMENTE_LEITURA = {"visualizador"}


def pode_editar(role: str) -> bool:
    """True se o perfil pode criar/editar/excluir informações."""
    return (role or "").strip().lower() in ROLES_COM_EDICAO


def eh_visualizador(role: str) -> bool:
    """True se o perfil é Visualizador (Admin Leitura)."""
    return (role or "").strip().lower() in ROLES_SOMENTE_LEITURA


def aviso_somente_leitura():
    """Exibe o aviso padrão de modo leitura, usado onde haveria
    botões de ação/salvar/excluir."""
    st.info(
        "👁️ **Modo Somente Leitura** — seu perfil (Visualizador) permite"
        " consultar todas as informações, mas não criar, editar ou excluir"
        " dados."
    )