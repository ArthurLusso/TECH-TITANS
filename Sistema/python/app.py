
import streamlit as st

# Configurações da página
st.set_page_config(
    page_title="TacoLoko - Gestão",
    page_icon="🌮",
    layout="wide"
)

# Configuração das páginas
paginas = [
    st.Page(
        "paginas/dashboard.py",
        title="Dashboard",
        icon="📊",
        default=True
    ),

    st.Page(
        "paginas/cardapio.py",
        title="Cardápio",
        icon="🌮"
    ),

    st.Page(
        "paginas/pedidos.py",
        title="Pedidos",
        icon="🛒"
    ),

    st.Page(
        "paginas/entregas.py",
        title="Entregas",
        icon="🚚"
    ),

    st.Page(
        "paginas/cancelamentos.py",
        title="Cancelamentos",
        icon="❌"
    ),

    st.Page(
        "paginas/estoque.py",
        title="Estoque",
        icon="📦"
    )
]

# Criação da navegação
pagina = st.navigation(paginas, position="sidebar")

# Execução da página selecionada
pagina.run()
