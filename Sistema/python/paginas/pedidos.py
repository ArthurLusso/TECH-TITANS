
import streamlit as st

from pathlib import Path

from data_base.pedidos import (
    STATUS_PEDIDO,
    listar_produtos_disponiveis,
    cadastrar_pedido,
    listar_pedidos,
    listar_itens_pedido,
    atualizar_status_pedido
)


BASE_DIR = Path(__file__).resolve().parent.parent
PASTA_PRATOS = (BASE_DIR / "assets" / "pratos").resolve()


def formatar_preco(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def obter_imagem(caminho):
    if not caminho:
        return None

    arquivo = (BASE_DIR / caminho).resolve()

    try:
        arquivo.relative_to(PASTA_PRATOS)
    except ValueError:
        return None

    if arquivo.is_file():
        return str(arquivo)

    return None


st.title("🛒 Pedidos")
st.write("Gerencie os pedidos realizados no TacoLoko.")

try:
    todos_pedidos = listar_pedidos()

    total_pedidos = len(todos_pedidos)

    pendentes = sum(
        1 for pedido in todos_pedidos
        if pedido["status"] == "Pendente"
    )

    em_preparo = sum(
        1 for pedido in todos_pedidos
        if pedido["status"] == "Em preparo"
    )

    concluidos = sum(
        1 for pedido in todos_pedidos
        if pedido["status"] == "Entregue"
    )

except Exception as erro:
    st.error(f"Erro ao carregar os pedidos: {erro}")
    st.stop()


col1, col2, col3, col4 = st.columns(4)

col1.metric("Total de pedidos", total_pedidos)
col2.metric("Pendentes", pendentes)
col3.metric("Em preparo", em_preparo)
col4.metric("Concluídos", concluidos)

st.divider()

aba_novo, aba_consulta = st.tabs([
    "➕ Novo pedido",
    "📋 Consultar pedidos"
])


with aba_novo:

    st.subheader("Cadastrar novo pedido")

    try:
        produtos = listar_produtos_disponiveis()

    except Exception as erro:
        st.error(f"Erro ao carregar o cardápio: {erro}")
        produtos = []

    if not produtos:
        st.warning(
            "Não existem pratos disponíveis no cardápio. "
            "Cadastre ou ative um prato antes de criar um pedido."
        )

    else:

        produtos_por_id = {
            produto["id"]: produto
            for produto in produtos
        }

        with st.expander("Visualizar cardápio disponível"):

            for produto in produtos:

                col_foto, col_info = st.columns([1, 4])

                with col_foto:
                    caminho_imagem = obter_imagem(produto["imagem"])

                    if caminho_imagem:
                        st.image(caminho_imagem, width=110)
                    else:
                        st.markdown("🌮")

                with col_info:
                    st.write(f"**{produto['nome']}**")
                    st.caption(produto["categoria"] or "Sem categoria")
                    st.write(formatar_preco(produto["preco"]))

                    if produto["descricao"]:
                        st.caption(produto["descricao"])

                st.divider()

        st.subheader("Produtos do pedido")

        produtos_selecionados = st.multiselect(
            "Selecione os pratos desejados",
            options=list(produtos_por_id.keys()),
            format_func=lambda produto_id: (
                f"{produtos_por_id[produto_id]['nome']} - "
                f"{formatar_preco(produtos_por_id[produto_id]['preco'])}"
            ),
            key="pedido_produtos"
        )

        itens_pedido = []
        total_pedido = 0

        if produtos_selecionados:

            for produto_id in produtos_selecionados:

                produto = produtos_por_id[produto_id]

                col_foto, col_info, col_quantidade = st.columns([1, 3, 1])

                with col_foto:
                    caminho_imagem = obter_imagem(produto["imagem"])

                    if caminho_imagem:
                        st.image(caminho_imagem, width=100)
                    else:
                        st.markdown("🌮")

                with col_info:
                    st.write(f"**{produto['nome']}**")
                    st.caption(produto["categoria"] or "Sem categoria")
                    st.write(formatar_preco(produto["preco"]))

                with col_quantidade:
                    quantidade = st.number_input(
                        "Quantidade",
                        min_value=1,
                        value=1,
                        step=1,
                        key=f"quantidade_pedido_{produto_id}"
                    )

                subtotal = float(produto["preco"]) * quantidade

                itens_pedido.append({
                    "produto_id": produto_id,
                    "quantidade": quantidade
                })

                total_pedido += subtotal

                st.caption(
                    f"Subtotal: {formatar_preco(subtotal)}"
                )

                st.divider()

        else:
            st.info("Selecione pelo menos um prato para continuar.")

        st.subheader("Dados do cliente")

        col1, col2 = st.columns(2)

        with col1:
            cliente_nome = st.text_input(
                "Nome do cliente",
                key="pedido_cliente_nome"
            )

        with col2:
            telefone = st.text_input(
                "Telefone",
                key="pedido_telefone"
            )

        col1, col2 = st.columns([3, 1])

        with col1:
            rua = st.text_input(
                "Rua",
                key="pedido_rua"
            )

        with col2:
            numero = st.text_input(
                "Número",
                key="pedido_numero"
            )

        col1, col2 = st.columns(2)

        with col1:
            bairro = st.text_input(
                "Bairro",
                key="pedido_bairro"
            )

        with col2:
            cidade = st.text_input(
                "Cidade",
                key="pedido_cidade"
            )

        complemento = st.text_input(
            "Complemento",
            key="pedido_complemento"
        )

        st.divider()

        st.subheader("Resumo do pedido")

        st.metric(
            "Valor total",
            formatar_preco(total_pedido)
        )

        if st.button(
            "Registrar pedido",
            type="primary",
            use_container_width=True,
            key="registrar_pedido"
        ):

            if not cliente_nome.strip():
                st.warning("Informe o nome do cliente.")

            elif not itens_pedido:
                st.warning("Selecione pelo menos um prato.")

            else:

                try:
                    pedido_id = cadastrar_pedido(
                        cliente_nome,
                        telefone,
                        rua,
                        numero,
                        bairro,
                        cidade,
                        complemento,
                        itens_pedido
                    )

                    st.success(
                        f"Pedido nº {pedido_id} cadastrado com sucesso!"
                    )

                except Exception as erro:
                    st.error(f"Não foi possível registrar o pedido: {erro}")


with aba_consulta:

    st.subheader("Pedidos cadastrados")

    col1, col2 = st.columns([2, 1])

    with col1:
        busca = st.text_input(
            "Pesquisar pedido",
            placeholder="Nome do cliente, telefone ou número do pedido..."
        )

    with col2:
        filtro_status = st.selectbox(
            "Filtrar por status",
            ["Todos"] + STATUS_PEDIDO + ["Agendado", "Cancelado"]
        )

    try:
        pedidos = listar_pedidos(
            busca=busca,
            status=filtro_status
        )

    except Exception as erro:
        st.error(f"Erro ao consultar pedidos: {erro}")
        pedidos = []

    if not pedidos:

        st.info("Nenhum pedido encontrado.")

    else:

        st.caption(f"{len(pedidos)} pedido(s) encontrado(s).")

        for pedido in pedidos:

            pedido_id = pedido["id"]
            status_atual = pedido["status"]

            with st.expander(
                f"Pedido nº {pedido_id} | "
                f"{pedido['cliente_nome']} | "
                f"{formatar_preco(pedido['total'])} | "
                f"{status_atual}"
            ):

                st.write(f"**Cliente:** {pedido['cliente_nome']}")
                st.write(f"**Telefone:** {pedido['telefone'] or 'Não informado'}")

                st.write(
                    f"**Endereço:** {pedido['rua']}, "
                    f"{pedido['numero']} - {pedido['bairro']}, "
                    f"{pedido['cidade']}"
                )

                if pedido["complemento"]:
                    st.write(
                        f"**Complemento:** {pedido['complemento']}"
                    )

                st.write(f"**Data do pedido:** {pedido['data_pedido']}")
                st.write(f"**Status:** {status_atual}")

                st.divider()

                st.markdown("#### Pratos do pedido")

                itens = listar_itens_pedido(pedido_id)

                for item in itens:

                    st.write(
                        f"**{item['quantidade']}x {item['produto_nome']}**"
                    )

                    st.caption(
                        f"{formatar_preco(item['preco_unitario'])} "
                        f"cada | Subtotal: "
                        f"{formatar_preco(item['subtotal'])}"
                    )

                st.divider()

                st.markdown("#### Total do pedido")

                st.subheader(formatar_preco(pedido["total"]))

                if status_atual == "Cancelado":

                    st.warning(
                        "Este pedido foi cancelado. "
                        "Consulte a aba Cancelamentos para mais informações."
                    )

                else:

                    opcoes_status = STATUS_PEDIDO.copy()

                    if status_atual not in opcoes_status:
                        opcoes_status.insert(0, status_atual)

                    indice_status = opcoes_status.index(status_atual)

                    novo_status = st.selectbox(
                        "Atualizar status",
                        opcoes_status,
                        index=indice_status,
                        key=f"status_pedido_{pedido_id}"
                    )

                    if st.button(
                        "Salvar status",
                        key=f"salvar_status_{pedido_id}",
                        use_container_width=True
                    ):

                        if novo_status == status_atual:
                            st.info("O pedido já possui esse status.")

                        else:

                            try:
                                atualizar_status_pedido(
                                    pedido_id,
                                    novo_status
                                )

                                st.success("Status atualizado com sucesso!")
                                st.rerun()

                            except Exception as erro:
                                st.error(f"Erro ao atualizar status: {erro}")
