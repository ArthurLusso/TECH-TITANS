
import streamlit as st

from data_base.pedidos import (
    STATUS_PEDIDO,
    FORMAS_PAGAMENTO,
    STATUS_PAGAMENTO,
    listar_produtos_disponiveis,
    cadastrar_pedido,
    listar_pedidos,
    listar_itens_pedido,
    atualizar_status_pedido,
    atualizar_pagamento
)


def formatar_preco(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


st.title("🛒 Pedidos")
st.write("Gerencie os pedidos realizados no TacoLoko.")

try:
    todos_pedidos = listar_pedidos()

except Exception as erro:
    st.error(f"Erro ao carregar os pedidos: {erro}")
    st.stop()


total_pedidos = len(todos_pedidos)

pendentes = sum(
    1 for pedido in todos_pedidos
    if pedido["status"] in ("Pendente", "Agendado")
)

em_preparo = sum(
    1 for pedido in todos_pedidos
    if pedido["status"] == "Em preparo"
)

em_entrega = sum(
    1 for pedido in todos_pedidos
    if pedido["status"] == "Saiu para entrega"
)

entregues = sum(
    1 for pedido in todos_pedidos
    if pedido["status"] == "Entregue"
)


col1, col2, col3, col4 = st.columns(4)

col1.metric("Total de pedidos", total_pedidos)
col2.metric("Pendentes", pendentes)
col3.metric("Em andamento", em_preparo + em_entrega)
col4.metric("Entregues", entregues)

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
                    if produto["imagem"]:
                        from pathlib import Path

                        base_dir = Path(__file__).resolve().parent.parent
                        caminho = (base_dir / produto["imagem"]).resolve()
                        pasta = (base_dir / "assets" / "pratos").resolve()

                        try:
                            caminho.relative_to(pasta)
                            imagem_valida = caminho.is_file()
                        except ValueError:
                            imagem_valida = False

                        if imagem_valida:
                            st.image(str(caminho), width=110)
                        else:
                            st.markdown("🌮")
                    else:
                        st.markdown("🌮")

                with col_info:
                    st.write(f"**{produto['nome']}**")
                    st.caption(produto["categoria"] or "Sem categoria")
                    st.write(formatar_preco(produto["preco"]))

                    if produto["descricao"]:
                        st.caption(produto["descricao"])

                st.divider()

        st.subheader("Pratos do pedido")

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
        subtotal_pedido = 0

        if produtos_selecionados:

            for produto_id in produtos_selecionados:

                produto = produtos_por_id[produto_id]

                col_foto, col_info, col_quantidade = st.columns([1, 3, 1])

                with col_foto:
                    if produto["imagem"]:
                        from pathlib import Path

                        base_dir = Path(__file__).resolve().parent.parent
                        caminho = (base_dir / produto["imagem"]).resolve()
                        pasta = (base_dir / "assets" / "pratos").resolve()

                        try:
                            caminho.relative_to(pasta)
                            imagem_valida = caminho.is_file()
                        except ValueError:
                            imagem_valida = False

                        if imagem_valida:
                            st.image(str(caminho), width=100)
                        else:
                            st.markdown("🌮")
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
                subtotal_pedido += subtotal

                itens_pedido.append({
                    "produto_id": produto_id,
                    "quantidade": quantidade
                })

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

        st.subheader("Entrega e pagamento")

        taxa_entrega = st.number_input(
            "Taxa de entrega (R$)",
            min_value=0.0,
            value=0.0,
            step=1.0,
            format="%.2f"
        )

        col1, col2 = st.columns(2)

        with col1:
            forma_pagamento = st.selectbox(
                "Forma de pagamento",
                FORMAS_PAGAMENTO
            )

        with col2:
            status_pagamento = st.selectbox(
                "Situação do pagamento",
                STATUS_PAGAMENTO
            )

        total_pedido = round(
            subtotal_pedido + taxa_entrega,
            2
        )

        st.divider()

        st.subheader("Resumo do pedido")

        col1, col2, col3 = st.columns(3)

        col1.metric(
            "Subtotal dos pratos",
            formatar_preco(subtotal_pedido)
        )

        col2.metric(
            "Taxa de entrega",
            formatar_preco(taxa_entrega)
        )

        col3.metric(
            "Total do pedido",
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
                        itens_pedido,
                        taxa_entrega,
                        forma_pagamento,
                        status_pagamento
                    )

                    st.success(
                        f"Pedido nº {pedido_id} cadastrado com sucesso!"
                    )

                    st.rerun()

                except Exception as erro:
                    st.error(
                        f"Não foi possível registrar o pedido: {erro}"
                    )


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
                st.write(
                    f"**Telefone:** {pedido['telefone'] or 'Não informado'}"
                )

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

                st.divider()

                st.markdown("#### Pratos do pedido")

                itens = listar_itens_pedido(pedido_id)

                for item in itens:
                    st.write(
                        f"**{item['quantidade']}x {item['produto_nome']}**"
                    )

                    st.caption(
                        f"{formatar_preco(item['preco_unitario'])} cada | "
                        f"Subtotal: {formatar_preco(item['subtotal'])}"
                    )

                st.divider()

                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Pratos",
                    formatar_preco(pedido["subtotal"])
                )

                col2.metric(
                    "Entrega",
                    formatar_preco(pedido["taxa_entrega"])
                )

                col3.metric(
                    "Total",
                    formatar_preco(pedido["total"])
                )

                st.divider()

                st.markdown("#### Pagamento")

                st.write(
                    f"**Forma:** {pedido['forma_pagamento'] or 'Não informada'}"
                )

                st.write(
                    f"**Situação:** {pedido['status_pagamento']}"
                )

                if pedido["data_pagamento"]:
                    st.write(
                        f"**Data do pagamento:** {pedido['data_pagamento']}"
                    )

                if status_atual != "Cancelado":

                    with st.form(f"form_pagamento_{pedido_id}"):

                        indice_forma = (
                            FORMAS_PAGAMENTO.index(pedido["forma_pagamento"])
                            if pedido["forma_pagamento"] in FORMAS_PAGAMENTO
                            else 0
                        )

                        indice_pagamento = (
                            STATUS_PAGAMENTO.index(pedido["status_pagamento"])
                            if pedido["status_pagamento"] in STATUS_PAGAMENTO
                            else 0
                        )

                        nova_forma = st.selectbox(
                            "Forma de pagamento",
                            FORMAS_PAGAMENTO,
                            index=indice_forma
                        )

                        novo_pagamento = st.selectbox(
                            "Situação do pagamento",
                            STATUS_PAGAMENTO,
                            index=indice_pagamento
                        )

                        salvar_pagamento = st.form_submit_button(
                            "Atualizar pagamento",
                            use_container_width=True
                        )

                        if salvar_pagamento:

                            try:
                                atualizar_pagamento(
                                    pedido_id,
                                    nova_forma,
                                    novo_pagamento
                                )

                                st.success("Pagamento atualizado!")
                                st.rerun()

                            except Exception as erro:
                                st.error(
                                    f"Erro ao atualizar o pagamento: {erro}"
                                )

                st.divider()

                st.markdown("#### Andamento do pedido")

                proximas_etapas = {
                    "Pendente": "Em preparo",
                    "Agendado": "Em preparo",
                    "Em preparo": "Saiu para entrega",
                    "Saiu para entrega": "Entregue"
                }

                proximo_status = proximas_etapas.get(status_atual)

                if status_atual == "Cancelado":

                    st.warning("Este pedido foi cancelado.")

                elif status_atual == "Entregue":

                    st.success("Este pedido já foi entregue.")

                elif proximo_status:

                    if st.button(
                        f"Avançar para: {proximo_status}",
                        key=f"avancar_{pedido_id}",
                        type="primary",
                        use_container_width=True
                    ):

                        try:
                            atualizar_status_pedido(
                                pedido_id,
                                proximo_status
                            )

                            st.success(
                                f"Pedido atualizado para {proximo_status}!"
                            )

                            st.rerun()

                        except Exception as erro:
                            st.error(
                                f"Não foi possível avançar o pedido: {erro}"
                            )

                    if proximo_status == "Em preparo":
                        st.caption(
                            "Ao iniciar o preparo, o sistema verificará a "
                            "ficha técnica de cada prato e descontará os "
                            "ingredientes utilizados no estoque."
                        )
