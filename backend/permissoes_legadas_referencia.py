"""
Helper de permissões reutilizável entre as views do Streamlit.

Uso sugerido:

    from views.permissoes import pode_editar, pode_lancar, aviso_somente_leitura

    role = st.session_state.get("user_role", "operador")

    # Editor / excluir / ações destrutivas
    if not pode_editar(role):
        aviso_somente_leitura()
        return

    # Lançamento diário (Visualizador PODE)
    if not pode_lancar(role):
        aviso_somente_leitura()
        return
"""

import streamlit as st

# Criar / editar / excluir (Editor, gestão, etc.)
ROLES_COM_EDICAO = {
    "admin",
    "admin master",
    "gestor",
    "operador",
    "coordenador",
}

# Lançar execução diária (inclui Visualizador)
ROLES_PODEM_LANCAR = {
    "admin",
    "admin master",
    "gestor",
    "operador",
    "coordenador",
    "visualizador",
}

# Perfil identificado como visualizador
ROLES_SOMENTE_LEITURA = {
    "visualizador",
}


def pode_editar(role: str) -> bool:
    """True se o perfil pode criar/editar/excluir informações."""
    return (role or "").strip().lower() in ROLES_COM_EDICAO


def pode_lancar(role: str) -> bool:
    """True se o perfil pode registrar lançamento diário (inclui Visualizador)."""
    return (role or "").strip().lower() in ROLES_PODEM_LANCAR


def eh_visualizador(role: str) -> bool:
    """True se o perfil é Visualizador."""
    return (role or "").strip().lower() in ROLES_SOMENTE_LEITURA


def aviso_somente_leitura():
    """Aviso padrão de modo leitura."""
    st.info(
        "👁️ **Modo Somente Leitura** — seu perfil permite consultar "
        "as informações, mas não criar, editar ou excluir dados nesta tela. "
        "Se precisar registrar o dia, use **Lançar Execução Diária**."
    )