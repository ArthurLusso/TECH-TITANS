
import streamlit as st

from data_base.estoque import (
    CATEGORIAS,
    UNIDADES,
    listar_ingredientes,
    cadastrar_ingrediente,
    movimentar_estoque
)


st.title("📦 Estoque")
st.caption("Gerenciamento dos ingredientes e insumos do TacoLoko.")

st.divider()


with st.expander("➕ Cadastrar novo ingrediente", expanded=False):

    with st.form("form_cadastro_ingrediente"):

        nome = st.text_input("Nome do ingrediente")

        categoria = st.selectbox(
            "Categoria",
            CATEGORIAS
        )

        col1, col2, col3 = st.columns(3)

        with col1:
            quantidade = st.number_input(
                "Quantidade inicial",
                min_value=0.0,
                value=0.0,
                step=0.5
            )

        with col2:
            unidade = st.selectbox(
                "Unidade de medida",
                UNIDADES
            )

        with col3:
            estoque_minimo = st.number_input(
                "Estoque mínimo",
                min_value=0.0,
                value=1.0,
                step=0.5
            )

        cadastrar = st.form_submit_button(
            "Cadastrar ingrediente",
            use_container_width=True
        )

        if cadastrar:

            try:
                cadastrar_ingrediente(
                    nome,
                    categoria,
                    quantidade,
                    unidade,
                    estoque_minimo
                )

                st.success("Ingrediente cadastrado com sucesso!")
                st.rerun()

            except ValueError as erro:
                st.error(str(erro))

            except Exception as erro:
                st.error(f"Erro ao cadastrar ingrediente: {erro}")


st.subheader("Ingredientes cadastrados")

abas = st.tabs(CATEGORIAS)


for categoria, aba in zip(CATEGORIAS, abas):

    with aba:

        ingredientes = listar_ingredientes(categoria)

        if not ingredientes:

            st.info(
                f"Nenhum ingrediente cadastrado na categoria {categoria}."
            )

        else:

            for ingrediente in ingredientes:

                with st.container():

                    col1, col2 = st.columns([2, 1])

                    with col1:

                        st.markdown(
                            f"### {ingrediente['nome']}"
                        )

                        st.write(
                            f"Categoria: {ingrediente['categoria']}"
                        )

                        quantidade_atual = ingrediente["quantidade"]
                        estoque_minimo_atual = ingrediente["estoque_minimo"]
                        unidade_atual = ingrediente["unidade"]

                        st.write(
                            f"Quantidade disponível: "
                            f"**{quantidade_atual:g} {unidade_atual}**"
                        )

                        if quantidade_atual <= estoque_minimo_atual:
                            st.warning("Estoque baixo! Necessário repor.")

                    with col2:

                        st.metric(
                            "Estoque mínimo",
                            f"{estoque_minimo_atual:g} {unidade_atual}"
                        )

                        with st.expander("Movimentar estoque"):

                            with st.form(
                                f"form_movimento_{ingrediente['id']}"
                            ):

                                tipo = st.selectbox(
                                    "Tipo de movimentação",
                                    ["Entrada", "Saída"],
                                    key=f"tipo_{ingrediente['id']}"
                                )

                                quantidade_movimento = st.number_input(
                                    "Quantidade",
                                    min_value=0.1,
                                    value=1.0,
                                    step=0.5,
                                    key=f"quantidade_{ingrediente['id']}"
                                )

                                motivo = st.text_input(
                                    "Motivo",
                                    key=f"motivo_{ingrediente['id']}"
                                )

                                salvar = st.form_submit_button(
                                    "Confirmar movimentação"
                                )

                                if salvar:

                                    try:
                                        movimentar_estoque(
                                            ingrediente["id"],
                                            tipo,
                                            quantidade_movimento,
                                            motivo
                                        )

                                        st.success(
                                            "Estoque atualizado com sucesso!"
                                        )

                                        st.rerun()

                                    except ValueError as erro:
                                        st.error(str(erro))

                                    except Exception as erro:
                                        st.error(
                                            f"Erro ao atualizar estoque: {erro}"
                                        )

                    st.divider()
