import streamlit as st

from componentes.estilo import aplicar_estilo


st.set_page_config(
    page_title="TacoLoko - Gestão",
    page_icon="🌮",
    layout="wide",
    initial_sidebar_state="expanded"
)

aplicar_estilo()


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


pagina = st.navigation(
    paginas,
    position="sidebar"
)

pagina.run()