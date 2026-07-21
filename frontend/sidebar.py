import streamlit as st

def render_sidebar():
    with st.sidebar:
        st.markdown("### Duarte Performance")
        
        # Avatar
        nome = st.session_state.get("user", "Usuário")
        partes = nome.split()
        iniciais = (partes[0][0] + partes[-1][0]).upper() if len(partes) >= 2 else nome[:2].upper()
        
        st.markdown(f"""
        <div style="text-align:center; margin:20px 0;">
            <div style="background: linear-gradient(#F26419, #d95615); color:white; width:70px;height:70px;border-radius:50%; 
                        display:flex;align-items:center;justify-content:center;font-size:28px;font-weight:900;margin:auto;">
                {iniciais}
            </div>
            <strong>{nome}</strong><br>
            <small>{st.session_state.get('role', 'Operador')}</small>
        </div>
        """, unsafe_allow_html=True)
        
        # Menu
        menu = st.radio("Menu", ["Dashboard", "Escala Semanal", "Relatórios", "Lançar Atividade", "Editor"], key="menu")
        st.session_state.menu = menu
        
        if st.button("Sair"):
            st.session_state.logged_in = False
            st.rerun()