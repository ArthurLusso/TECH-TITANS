
import streamlit as st

from datetime import datetime, timezone, timedelta

from data_base.entregas import (
    STATUS_ENTREGA,
    sincronizar_entregas,
    listar_entregas,
    atualizar_entrega
)

from data_base.pedidos import listar_itens_pedido


def formatar_preco(valor):
    return (
        f"R$ {valor:,.2f}"
        .replace(",", "X")
        .replace(".", ",")
        .replace("X", ".")
    )


def formatar_data_hora(valor):
    if not valor:
        return "Não informada"

    try:
        data = datetime.fromisoformat(valor)

        if data.tzinfo is None:
            data = data.replace(tzinfo=timezone.utc)

        horario_brasilia = timezone(timedelta(hours=-3))

        data_local = data.astimezone(horario_brasilia)

        return data_local.strftime("%d/%m/%Y às %H:%M")

    except (ValueError, TypeError):
        return valor


st.title("🚚 Entregas")
st.write("Acompanhe e gerencie as entregas dos pedidos.")


try:
    sincronizar_entregas()
    todas_entregas = listar_entregas()

except Exception as erro:
    st.error(f"Erro ao carregar as entregas: {erro}")
    st.stop()


total_entregas = len(todas_entregas)

aguardando = sum(
    1 for entrega in todas_entregas
    if entrega["status_entrega"] == "Aguardando"
)

em_rota = sum(
    1 for entrega in todas_entregas
    if entrega["status_entrega"] == "Saiu para entrega"
)

concluidas = sum(
    1 for entrega in todas_entregas
    if entrega["status_entrega"] == "Entregue"
)


col1, col2, col3, col4 = st.columns(4)

col1.metric("Total de entregas", total_entregas)
col2.metric("Aguardando", aguardando)
col3.metric("Em rota", em_rota)
col4.metric("Concluídas", concluidas)


st.divider()

st.subheader("Gerenciamento de entregas")

st.info(
    "Os pedidos aparecem nesta tela automaticamente quando seu status "
    "é alterado para 'Em preparo' na tela Pedidos."
)


col1, col2 = st.columns([2, 1])

with col1:
    busca = st.text_input(
        "Pesquisar entrega",
        placeholder="Nome, telefone, número do pedido ou entregador..."
    )

with col2:
    filtro_status = st.selectbox(
        "Filtrar por status",
        ["Todas"] + STATUS_ENTREGA
    )


try:
    entregas = listar_entregas(
        busca=busca,
        status=filtro_status
    )

except Exception as erro:
    st.error(f"Erro ao consultar entregas: {erro}")
    entregas = []


if not entregas:

    st.info("Nenhuma entrega encontrada.")

else:

    st.caption(f"{len(entregas)} entrega(s) encontrada(s).")

    for entrega in entregas:

        entrega_id = entrega["entrega_id"]
        pedido_id = entrega["pedido_id"]
        status_atual = entrega["status_entrega"]

        with st.expander(
            f"Pedido nº {pedido_id} | "
            f"{entrega['cliente_nome']} | "
            f"{status_atual}"
        ):

            col1, col2 = st.columns(2)

            with col1:
                st.write(f"**Cliente:** {entrega['cliente_nome']}")

                st.write(
                    f"**Telefone:** {entrega['telefone'] or 'Não informado'}"
                )

                st.write(
                    f"**Endereço:** {entrega['rua'] or 'Não informado'}, "
                    f"{entrega['numero'] or 'S/N'}"
                )

                st.write(
                    f"**Bairro:** {entrega['bairro'] or 'Não informado'}"
                )

                st.write(
                    f"**Cidade:** {entrega['cidade'] or 'Não informado'}"
                )

                if entrega["complemento"]:
                    st.write(
                        f"**Complemento:** {entrega['complemento']}"
                    )

            with col2:
                st.write(
                    f"**Valor do pedido:** {formatar_preco(entrega['total'])}"
                )

                st.write(
                    f"**Data do pedido:** "
                    f"{formatar_data_hora(entrega['data_pedido'])}"
                )

                st.write(
                    f"**Entregador:** "
                    f"{entrega['entregador'] or 'Não atribuído'}"
                )

                st.write(
                    f"**Previsão:** "
                    f"{entrega['previsao_entrega'] or 'Não informada'}"
                )

                if entrega["data_saida"]:
                    st.write(
                        f"**Saída:** "
                        f"{formatar_data_hora(entrega['data_saida'])}"
                    )

                if entrega["data_entrega"]:
                    st.write(
                        f"**Entrega concluída:** "
                        f"{formatar_data_hora(entrega['data_entrega'])}"
                    )

            st.divider()

            st.markdown("#### Pratos do pedido")

            try:
                itens = listar_itens_pedido(pedido_id)

                if itens:
                    for item in itens:
                        st.write(
                            f"**{item['quantidade']}x {item['produto_nome']}**"
                        )

                        st.caption(
                            f"Subtotal: {formatar_preco(item['subtotal'])}"
                        )

                else:
                    st.caption("Nenhum prato encontrado neste pedido.")

            except Exception as erro:
                st.error(f"Erro ao carregar os pratos: {erro}")

            st.divider()

            st.markdown("#### Atualizar entrega")

            opcoes_status = STATUS_ENTREGA.copy()

            indice_status = (
                opcoes_status.index(status_atual)
                if status_atual in opcoes_status
                else 0
            )

            with st.form(f"form_entrega_{entrega_id}"):

                entregador = st.text_input(
                    "Nome do entregador",
                    value=entrega["entregador"] or ""
                )

                previsao = st.text_input(
                    "Previsão de entrega",
                    value=entrega["previsao_entrega"] or "",
                    placeholder="Ex.: 14:30"
                )

                novo_status = st.selectbox(
                    "Status da entrega",
                    opcoes_status,
                    index=indice_status
                )

                salvar = st.form_submit_button(
                    "Salvar alterações",
                    use_container_width=True
                )

                if salvar:

                    try:
                        atualizar_entrega(
                            entrega_id,
                            entregador,
                            previsao,
                            novo_status
                        )

                        st.success("Entrega atualizada com sucesso!")
                        st.rerun()

                    except Exception as erro:
                        st.error(f"Erro ao atualizar entrega: {erro}")
