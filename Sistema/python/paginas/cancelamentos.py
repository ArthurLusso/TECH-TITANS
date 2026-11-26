
import streamlit as st

from datetime import datetime, timezone, timedelta

from data_base.cancelamentos import (
    STATUS_REEMBOLSO,
    listar_pedidos_cancelaveis,
    registrar_cancelamento,
    listar_cancelamentos,
    atualizar_reembolso
)

from data_base.pedidos import listar_itens_pedido


FUSO_BRASILIA = timezone(timedelta(hours=-3))


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

        data = data.astimezone(FUSO_BRASILIA)

        return data.strftime("%d/%m/%Y às %H:%M")

    except (ValueError, TypeError):
        return valor


st.title("❌ Cancelamentos")
st.write("Gerencie os pedidos cancelados e seus reembolsos.")


try:
    todos_cancelamentos = listar_cancelamentos()

except Exception as erro:
    st.error(f"Erro ao carregar os cancelamentos: {erro}")
    st.stop()


total_cancelamentos = len(todos_cancelamentos)

reembolsos_pendentes = sum(
    1 for item in todos_cancelamentos
    if item["status_reembolso"] == "Pendente"
)

valor_reembolsos = sum(
    float(item["valor_reembolso"])
    for item in todos_cancelamentos
    if item["status_reembolso"] == "Reembolsado"
)

valor_nao_reembolsado = sum(
    float(item["valor_prejuizo"])
    for item in todos_cancelamentos
    if item["status_reembolso"] != "Pendente"
)


col1, col2, col3, col4 = st.columns(4)

col1.metric("Total de cancelamentos", total_cancelamentos)
col2.metric("Reembolsos pendentes", reembolsos_pendentes)
col3.metric("Valores reembolsados", formatar_preco(valor_reembolsos))
col4.metric(
    "Valores não reembolsados",
    formatar_preco(valor_nao_reembolsado)
)


st.divider()

aba_novo, aba_historico = st.tabs([
    "➕ Novo cancelamento",
    "📋 Histórico de cancelamentos"
])


with aba_novo:

    st.subheader("Registrar cancelamento")

    try:
        pedidos_cancelaveis = listar_pedidos_cancelaveis()

    except Exception as erro:
        st.error(f"Erro ao carregar os pedidos: {erro}")
        pedidos_cancelaveis = []

    if not pedidos_cancelaveis:

        st.info(
            "Não existem pedidos disponíveis para cancelamento. "
            "Pedidos já cancelados ou entregues não podem ser selecionados."
        )

    else:

        pedidos_opcoes = {}

        for pedido in pedidos_cancelaveis:
            identificacao = (
                f"Pedido nº {pedido['id']} | "
                f"{pedido['cliente_nome']} | "
                f"{formatar_preco(pedido['total'])}"
            )

            pedidos_opcoes[identificacao] = pedido

        pedido_escolhido = st.selectbox(
            "Selecione o pedido",
            list(pedidos_opcoes.keys()),
            key="pedido_para_cancelar"
        )

        pedido = pedidos_opcoes[pedido_escolhido]
        pedido_id = pedido["id"]
        total_pedido = float(pedido["total"])

        col1, col2, col3 = st.columns(3)

        col1.metric("Número do pedido", f"#{pedido_id}")
        col2.metric("Cliente", pedido["cliente_nome"])
        col3.metric("Valor do pedido", formatar_preco(total_pedido))

        st.write(
            f"**Data do pedido:** "
            f"{formatar_data_hora(pedido['data_pedido'])}"
        )

        st.write(f"**Status atual:** {pedido['status']}")

        st.write(
            f"**Forma de pagamento:** "
            f"{pedido['forma_pagamento'] or 'Não informada'}"
        )

        st.write(
            f"**Situação do pagamento:** "
            f"{pedido['status_pagamento']}"
        )

        if pedido["estoque_descontado"]:
            st.warning(
                "Os ingredientes deste pedido já foram descontados do estoque. "
                "O cancelamento não devolve automaticamente esses ingredientes."
            )

        try:
            itens = listar_itens_pedido(pedido_id)

            if itens:
                st.markdown("#### Pratos do pedido")

                for item in itens:
                    st.write(
                        f"**{item['quantidade']}x {item['produto_nome']}**"
                    )

                    st.caption(
                        f"Subtotal: {formatar_preco(item['subtotal'])}"
                    )

        except Exception as erro:
            st.error(f"Erro ao carregar os itens do pedido: {erro}")

        st.divider()

        with st.form("form_novo_cancelamento"):

            motivo = st.text_area(
                "Motivo do cancelamento",
                placeholder="Informe o motivo do cancelamento..."
            )

            status_reembolso = st.selectbox(
                "Status do reembolso",
                STATUS_REEMBOLSO
            )

            valor_reembolso = st.number_input(
                "Valor do reembolso (R$)",
                min_value=0.0,
                max_value=total_pedido,
                value=total_pedido,
                step=1.0,
                format="%.2f"
            )

            valor_considerado = (
                0
                if status_reembolso == "Não reembolsado"
                else valor_reembolso
            )

            prejuizo_estimado = round(
                total_pedido - valor_considerado,
                2
            )

            st.write(
                f"**Valor não reembolsado:** "
                f"{formatar_preco(prejuizo_estimado)}"
            )

            confirmar = st.form_submit_button(
                "Confirmar cancelamento",
                type="primary",
                use_container_width=True
            )

            if confirmar:

                if not motivo.strip():
                    st.warning("Informe o motivo do cancelamento.")

                else:

                    try:
                        cancelamento_id = registrar_cancelamento(
                            pedido_id,
                            motivo,
                            status_reembolso,
                            valor_reembolso
                        )

                        st.success(
                            f"Pedido nº {pedido_id} cancelado com sucesso! "
                            f"Registro de cancelamento nº {cancelamento_id}."
                        )

                        st.rerun()

                    except Exception as erro:
                        st.error(
                            f"Não foi possível registrar o cancelamento: {erro}"
                        )


with aba_historico:

    st.subheader("Histórico de cancelamentos")

    col1, col2 = st.columns([2, 1])

    with col1:
        busca = st.text_input(
            "Pesquisar cancelamento",
            placeholder="Nome do cliente, telefone, pedido ou motivo..."
        )

    with col2:
        filtro_reembolso = st.selectbox(
            "Filtrar por reembolso",
            ["Todos"] + STATUS_REEMBOLSO
        )

    try:
        cancelamentos = listar_cancelamentos(
            busca=busca,
            status_reembolso=filtro_reembolso
        )

    except Exception as erro:
        st.error(f"Erro ao consultar cancelamentos: {erro}")
        cancelamentos = []

    if not cancelamentos:

        st.info("Nenhum cancelamento encontrado.")

    else:

        st.caption(
            f"{len(cancelamentos)} cancelamento(s) encontrado(s)."
        )

        for cancelamento in cancelamentos:

            cancelamento_id = cancelamento["cancelamento_id"]
            pedido_id = cancelamento["pedido_id"]

            with st.expander(
                f"Pedido nº {pedido_id} | "
                f"{cancelamento['cliente_nome']} | "
                f"{cancelamento['status_reembolso']}"
            ):

                col1, col2 = st.columns(2)

                with col1:
                    st.write(
                        f"**Cliente:** {cancelamento['cliente_nome']}"
                    )

                    st.write(
                        f"**Telefone:** "
                        f"{cancelamento['telefone'] or 'Não informado'}"
                    )

                    st.write(
                        f"**Data do cancelamento:** "
                        f"{formatar_data_hora(cancelamento['data_cancelamento'])}"
                    )

                    st.write(
                        f"**Motivo:** {cancelamento['motivo']}"
                    )

                    st.write(
                        f"**Forma de pagamento:** "
                        f"{cancelamento['forma_pagamento'] or 'Não informada'}"
                    )

                with col2:
                    st.write(
                        f"**Valor do pedido:** "
                        f"{formatar_preco(cancelamento['total_pedido'])}"
                    )

                    st.write(
                        f"**Situação do pagamento:** "
                        f"{cancelamento['status_pagamento']}"
                    )

                    st.write(
                        f"**Status do reembolso:** "
                        f"{cancelamento['status_reembolso']}"
                    )

                    st.write(
                        f"**Valor reembolsado:** "
                        f"{formatar_preco(cancelamento['valor_reembolso'])}"
                    )

                    st.write(
                        f"**Valor não reembolsado:** "
                        f"{formatar_preco(cancelamento['valor_prejuizo'])}"
                    )

                st.divider()

                st.markdown("#### Pratos do pedido")

                try:
                    itens = listar_itens_pedido(pedido_id)

                    if itens:
                        for item in itens:
                            st.write(
                                f"**{item['quantidade']}x "
                                f"{item['produto_nome']}**"
                            )

                            st.caption(
                                f"Subtotal: "
                                f"{formatar_preco(item['subtotal'])}"
                            )

                    else:
                        st.caption("Nenhum prato encontrado.")

                except Exception as erro:
                    st.error(f"Erro ao carregar os pratos: {erro}")

                st.divider()

                st.markdown("#### Gerenciar reembolso")

                with st.form(f"form_reembolso_{cancelamento_id}"):

                    status_atual = cancelamento["status_reembolso"]

                    indice_status = STATUS_REEMBOLSO.index(
                        status_atual
                    )

                    novo_status = st.selectbox(
                        "Status do reembolso",
                        STATUS_REEMBOLSO,
                        index=indice_status
                    )

                    novo_valor = st.number_input(
                        "Valor do reembolso (R$)",
                        min_value=0.0,
                        max_value=float(cancelamento["total_pedido"]),
                        value=float(cancelamento["valor_reembolso"]),
                        step=1.0,
                        format="%.2f"
                    )

                    salvar_reembolso = st.form_submit_button(
                        "Salvar alterações",
                        use_container_width=True
                    )

                    if salvar_reembolso:

                        try:
                            atualizar_reembolso(
                                cancelamento_id,
                                novo_status,
                                novo_valor
                            )

                            st.success(
                                "Informações do reembolso atualizadas!"
                            )

                            st.rerun()

                        except Exception as erro:
                            st.error(
                                f"Erro ao atualizar o reembolso: {erro}"
                            )
