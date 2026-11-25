
import streamlit as st

from data_base.estoque import (
    CATEGORIAS,
    UNIDADES,
    listar_ingredientes,
    listar_variacoes,
    cadastrar_ingrediente,
    adicionar_variacao,
    editar_variacao,
    remover_variacao,
    movimentar_estoque,
    listar_movimentacoes
)


st.title("📦 Estoque")
st.caption("Gerenciamento de ingredientes e insumos do TacoLoko.")

st.divider()


with st.expander("➕ Cadastrar grupo de ingredientes"):

    with st.form("form_cadastro_grupo"):

        nome = st.text_input(
            "Nome do grupo",
            placeholder="Ex: Carne de Boi"
        )

        categoria = st.selectbox(
            "Categoria",
            CATEGORIAS
        )

        cadastrar = st.form_submit_button(
            "Cadastrar grupo",
            use_container_width=True
        )

        if cadastrar:

            try:
                cadastrar_ingrediente(nome, categoria)

                st.success("Grupo cadastrado com sucesso!")
                st.rerun()

            except ValueError as erro:
                st.error(str(erro))

            except Exception as erro:
                st.error(f"Erro ao cadastrar grupo: {erro}")


st.subheader("Ingredientes cadastrados")

abas = st.tabs(CATEGORIAS)


for categoria, aba in zip(CATEGORIAS, abas):

    with aba:

        grupos = listar_ingredientes(categoria)

        if not grupos:

            st.info(
                f"Nenhum grupo cadastrado em {categoria}."
            )

        else:

            for grupo in grupos:

                ingrediente_id = grupo["id"]

                variacoes = listar_variacoes(ingrediente_id)

                with st.container(border=True):

                    st.subheader(grupo["nome"])

                    st.caption(
                        f"{categoria} • {len(variacoes)} variação(ões)"
                    )

                    with st.expander("➕ Adicionar variação"):

                        with st.form(
                            f"form_adicionar_{ingrediente_id}"
                        ):

                            nome_variacao = st.text_input(
                                "Nome da variação",
                                placeholder="Ex: Fraldinha"
                            )

                            col1, col2, col3 = st.columns(3)

                            with col1:
                                quantidade_inicial = st.number_input(
                                    "Quantidade inicial",
                                    min_value=0.0,
                                    value=0.0,
                                    step=0.5
                                )

                            with col2:
                                unidade = st.selectbox(
                                    "Unidade",
                                    UNIDADES,
                                    key=f"unidade_{ingrediente_id}"
                                )

                            with col3:
                                estoque_minimo = st.number_input(
                                    "Estoque mínimo",
                                    min_value=0.0,
                                    value=1.0,
                                    step=0.5
                                )

                            adicionar = st.form_submit_button(
                                "Adicionar variação",
                                use_container_width=True
                            )

                            if adicionar:

                                try:
                                    adicionar_variacao(
                                        ingrediente_id,
                                        nome_variacao,
                                        quantidade_inicial,
                                        unidade,
                                        estoque_minimo
                                    )

                                    st.success(
                                        "Variação cadastrada com sucesso!"
                                    )

                                    st.rerun()

                                except ValueError as erro:
                                    st.error(str(erro))

                                except Exception as erro:
                                    st.error(
                                        f"Erro ao cadastrar variação: {erro}"
                                    )

                    if not variacoes:

                        st.info(
                            "Este grupo ainda não possui variações."
                        )

                    for variacao in variacoes:

                        variacao_id = variacao["id"]

                        quantidade = float(
                            variacao["quantidade"]
                        )

                        minimo = float(
                            variacao["estoque_minimo"]
                        )

                        unidade_atual = variacao["unidade"]

                        st.divider()

                        col1, col2, col3 = st.columns([2, 1, 1])

                        with col1:
                            st.markdown(
                                f"**{variacao['nome']}**"
                            )

                            if quantidade <= minimo:
                                st.warning("Estoque baixo!")

                            else:
                                st.success("Estoque adequado")

                        with col2:
                            st.metric(
                                "Quantidade",
                                f"{quantidade:g} {unidade_atual}"
                            )

                        with col3:
                            st.metric(
                                "Estoque mínimo",
                                f"{minimo:g} {unidade_atual}"
                            )

                        with st.expander(
                            f"Gerenciar {variacao['nome']}"
                        ):

                            aba_mov, aba_edit, aba_hist = st.tabs([
                                "Movimentação",
                                "Editar",
                                "Histórico"
                            ])

                            with aba_mov:

                                with st.form(
                                    f"form_movimento_{variacao_id}"
                                ):

                                    tipo = st.selectbox(
                                        "Tipo de movimentação",
                                        ["Entrada", "Saída"],
                                        key=f"tipo_{variacao_id}"
                                    )

                                    quantidade_movimento = st.number_input(
                                        f"Quantidade ({unidade_atual})",
                                        min_value=0.001,
                                        value=1.0,
                                        step=0.5,
                                        key=f"quant_{variacao_id}"
                                    )

                                    motivo = st.text_input(
                                        "Motivo",
                                        key=f"motivo_{variacao_id}"
                                    )

                                    salvar = st.form_submit_button(
                                        "Confirmar movimentação",
                                        use_container_width=True
                                    )

                                    if salvar:

                                        try:
                                            movimentar_estoque(
                                                variacao_id,
                                                tipo,
                                                quantidade_movimento,
                                                motivo
                                            )

                                            st.success(
                                                "Estoque atualizado!"
                                            )

                                            st.rerun()

                                        except ValueError as erro:
                                            st.error(str(erro))

                                        except Exception as erro:
                                            st.error(str(erro))

                            with aba_edit:

                                indice_unidade = (
                                    UNIDADES.index(unidade_atual)
                                    if unidade_atual in UNIDADES
                                    else 0
                                )

                                with st.form(
                                    f"form_editar_{variacao_id}"
                                ):

                                    novo_nome = st.text_input(
                                        "Nome da variação",
                                        value=variacao["nome"]
                                    )

                                    nova_unidade = st.selectbox(
                                        "Unidade de medida",
                                        UNIDADES,
                                        index=indice_unidade,
                                        key=f"edit_unidade_{variacao_id}"
                                    )

                                    novo_minimo = st.number_input(
                                        "Estoque mínimo",
                                        min_value=0.0,
                                        value=minimo,
                                        step=0.5,
                                        key=f"edit_minimo_{variacao_id}"
                                    )

                                    salvar_edicao = st.form_submit_button(
                                        "Salvar alterações",
                                        use_container_width=True
                                    )

                                    if salvar_edicao:

                                        try:
                                            editar_variacao(
                                                variacao_id,
                                                novo_nome,
                                                nova_unidade,
                                                novo_minimo
                                            )

                                            st.success(
                                                "Variação atualizada!"
                                            )

                                            st.rerun()

                                        except ValueError as erro:
                                            st.error(str(erro))

                                        except Exception as erro:
                                            st.error(str(erro))

                                st.divider()

                                confirmar_remocao = st.checkbox(
                                    "Confirmo que desejo remover esta variação.",
                                    key=f"confirmar_remocao_{variacao_id}"
                                )

                                if st.button(
                                    "Remover variação",
                                    key=f"remover_{variacao_id}",
                                    disabled=not confirmar_remocao
                                ):

                                    try:
                                        remover_variacao(variacao_id)

                                        st.success(
                                            "Variação removida!"
                                        )

                                        st.rerun()

                                    except ValueError as erro:
                                        st.error(str(erro))

                                    except Exception as erro:
                                        st.error(str(erro))

                            with aba_hist:

                                historico = listar_movimentacoes(
                                    variacao_id
                                )

                                if historico:

                                    st.dataframe(
                                        historico,
                                        use_container_width=True,
                                        hide_index=True
                                    )

                                else:

                                    st.info(
                                        "Nenhuma movimentação registrada."
                                    )

                st.divider()
