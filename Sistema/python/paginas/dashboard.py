
import streamlit as st
import pandas as pd

from datetime import datetime, timedelta, timezone

from data_base.conexao import conectar


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


def carregar_dados():

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        hoje = datetime.now(FUSO_BRASILIA).date()
        inicio_periodo = hoje - timedelta(days=6)

        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(
                    CASE
                        WHEN status IN (
                            'Pendente',
                            'Agendado',
                            'Em preparo',
                            'Saiu para entrega'
                        )
                        THEN 1 ELSE 0
                    END
                ) AS andamento,
                SUM(
                    CASE WHEN status = 'Entregue'
                    THEN 1 ELSE 0 END
                ) AS entregues,
                SUM(
                    CASE WHEN status = 'Cancelado'
                    THEN 1 ELSE 0 END
                ) AS cancelados
            FROM pedidos
        """)

        resumo = cursor.fetchone()

        cursor.execute("""
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN p.status_pagamento IN (
                                'Pago',
                                'Reembolso parcial'
                            )
                            THEN MAX(
                                p.total -
                                CASE
                                    WHEN c.status_reembolso = 'Reembolsado'
                                    THEN c.valor_reembolso
                                    ELSE 0
                                END,
                                0
                            )
                            ELSE 0
                        END
                    ),
                    0
                ) AS recebido,

                COALESCE(
                    SUM(
                        CASE
                            WHEN p.status_pagamento = 'Pendente'
                                AND p.status != 'Cancelado'
                            THEN p.total
                            ELSE 0
                        END
                    ),
                    0
                ) AS pendente,

                COALESCE(
                    SUM(
                        CASE
                            WHEN p.status_pagamento IN (
                                'Pago',
                                'Reembolso parcial'
                            )
                            THEN p.taxa_entrega
                            ELSE 0
                        END
                    ),
                    0
                ) AS taxas_entrega

            FROM pedidos p
            LEFT JOIN cancelamentos c
                ON c.pedido_id = p.id
        """)

        financeiro = cursor.fetchone()

        cursor.execute("""
            SELECT
                COALESCE(
                    SUM(
                        CASE
                            WHEN p.status_pagamento IN (
                                'Pago',
                                'Reembolso parcial'
                            )
                            THEN MAX(
                                p.total -
                                CASE
                                    WHEN c.status_reembolso = 'Reembolsado'
                                    THEN c.valor_reembolso
                                    ELSE 0
                                END,
                                0
                            )
                            ELSE 0
                        END
                    ),
                    0
                )
            FROM pedidos p
            LEFT JOIN cancelamentos c
                ON c.pedido_id = p.id
            WHERE date(
                COALESCE(p.data_pagamento, p.data_pedido),
                '-3 hours'
            ) = ?
        """, (hoje.isoformat(),))

        recebido_hoje = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT
                COALESCE(SUM(
                    CASE
                        WHEN status_reembolso != 'Pendente'
                        THEN valor_prejuizo
                        ELSE 0
                    END
                ), 0)
            FROM cancelamentos
        """)

        valores_nao_reembolsados = cursor.fetchone()[0] or 0

        cursor.execute("""
            SELECT
                date(data_pedido, '-3 hours') AS dia,
                COUNT(*) AS quantidade
            FROM pedidos
            WHERE date(data_pedido, '-3 hours') BETWEEN ? AND ?
            GROUP BY date(data_pedido, '-3 hours')
            ORDER BY dia
        """, (
            inicio_periodo.isoformat(),
            hoje.isoformat()
        ))

        resultados_dias = cursor.fetchall()

        pedidos_por_dia = {
            linha["dia"]: linha["quantidade"]
            for linha in resultados_dias
        }

        datas_periodo = [
            inicio_periodo + timedelta(days=i)
            for i in range(7)
        ]

        dados_diarios = pd.DataFrame({
            "Dia": [
                data.strftime("%d/%m")
                for data in datas_periodo
            ],
            "Pedidos": [
                pedidos_por_dia.get(data.isoformat(), 0)
                for data in datas_periodo
            ]
        })

        cursor.execute("""
            SELECT
                status,
                COUNT(*) AS quantidade
            FROM pedidos
            GROUP BY status
        """)

        resultados_status = cursor.fetchall()

        quantidade_status = {
            linha["status"]: linha["quantidade"]
            for linha in resultados_status
        }

        status_conhecidos = [
            "Pendente",
            "Agendado",
            "Em preparo",
            "Saiu para entrega",
            "Entregue",
            "Cancelado"
        ]

        dados_status = pd.DataFrame([
            {
                "Status": status,
                "Quantidade": quantidade_status.get(status, 0)
            }
            for status in status_conhecidos
        ])

        cursor.execute("""
            SELECT
                ip.produto_nome,
                SUM(ip.quantidade) AS quantidade
            FROM itens_pedido ip
            INNER JOIN pedidos p
                ON p.id = ip.pedido_id
            WHERE p.status != 'Cancelado'
            GROUP BY ip.produto_nome
            ORDER BY quantidade DESC
            LIMIT 5
        """)

        produtos_populares = pd.DataFrame([
            {
                "Prato": linha["produto_nome"],
                "Quantidade": linha["quantidade"]
            }
            for linha in cursor.fetchall()
        ])

        cursor.execute("""
            SELECT
                i.nome AS ingrediente,
                i.categoria,
                v.nome AS variacao,
                v.quantidade,
                v.unidade,
                v.estoque_minimo
            FROM variacoes_ingrediente v
            INNER JOIN ingredientes i
                ON i.id = v.ingrediente_id
            WHERE v.estoque_minimo > 0
              AND v.quantidade <= v.estoque_minimo
            ORDER BY i.nome, v.nome
        """)

        estoque_baixo = [
            {
                "Ingrediente": linha["ingrediente"],
                "Categoria": linha["categoria"],
                "Variação": linha["variacao"],
                "Quantidade atual": (
                    f"{linha['quantidade']:g} {linha['unidade']}"
                ),
                "Estoque mínimo": (
                    f"{linha['estoque_minimo']:g} {linha['unidade']}"
                )
            }
            for linha in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT
                id,
                cliente_nome,
                total,
                status,
                status_pagamento,
                data_pedido
            FROM pedidos
            ORDER BY id DESC
            LIMIT 8
        """)

        pedidos_recentes = [
            {
                "Pedido": f"#{linha['id']}",
                "Cliente": linha["cliente_nome"],
                "Valor": formatar_preco(linha["total"]),
                "Status do pedido": linha["status"],
                "Pagamento": linha["status_pagamento"],
                "Data": formatar_data_hora(linha["data_pedido"])
            }
            for linha in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(
                    CASE WHEN disponivel = 1
                    THEN 1 ELSE 0 END
                ) AS ativos
            FROM produtos
        """)

        resumo_cardapio = cursor.fetchone()

        return {
            "resumo": resumo,
            "financeiro": financeiro,
            "recebido_hoje": recebido_hoje,
            "valores_nao_reembolsados": valores_nao_reembolsados,
            "dados_diarios": dados_diarios,
            "dados_status": dados_status,
            "produtos_populares": produtos_populares,
            "estoque_baixo": estoque_baixo,
            "pedidos_recentes": pedidos_recentes,
            "resumo_cardapio": resumo_cardapio
        }

    finally:
        conexao.close()


st.title("🌮 Visão geral")
st.caption(
    "Acompanhe os principais indicadores e a operação do restaurante."
)

col_atualizacao, col_atualizar = st.columns([5, 1])

with col_atualizacao:
    agora = datetime.now(FUSO_BRASILIA)

    st.caption(
        f"Última atualização: {agora.strftime('%d/%m/%Y às %H:%M')}"
    )

with col_atualizar:
    if st.button("↻ Atualizar", use_container_width=True):
        st.rerun()

st.divider()


try:
    dados = carregar_dados()

except Exception as erro:
    st.error(f"Não foi possível carregar o Dashboard: {erro}")
    st.stop()


resumo = dados["resumo"]
financeiro = dados["financeiro"]
cardapio = dados["resumo_cardapio"]

total_pedidos = resumo["total"] or 0
pedidos_andamento = resumo["andamento"] or 0
pedidos_entregues = resumo["entregues"] or 0
pedidos_cancelados = resumo["cancelados"] or 0

total_recebido = financeiro["recebido"] or 0
pagamentos_pendentes = financeiro["pendente"] or 0
taxas_entrega = financeiro["taxas_entrega"] or 0

total_pratos = cardapio["total"] or 0
pratos_ativos = cardapio["ativos"] or 0


st.subheader("Indicadores gerais")

col1, col2, col3, col4 = st.columns(4)

col1.metric("Total de pedidos", total_pedidos)
col2.metric("Em andamento", pedidos_andamento)
col3.metric("Entregues", pedidos_entregues)
col4.metric("Cancelados", pedidos_cancelados)

st.divider()

st.subheader("Resumo financeiro")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Total recebido",
    formatar_preco(total_recebido)
)

col2.metric(
    "Recebimentos hoje",
    formatar_preco(dados["recebido_hoje"])
)

col3.metric(
    "Pagamentos pendentes",
    formatar_preco(pagamentos_pendentes)
)

st.caption(
    "Os valores recebidos consideram pagamentos marcados como pagos, "
    "descontando os reembolsos efetivamente registrados."
)

col1, col2, col3 = st.columns(3)

col1.metric(
    "Taxas de entrega em pedidos pagos",
    formatar_preco(taxas_entrega)
)

col2.metric(
    "Valores não reembolsados",
    formatar_preco(dados["valores_nao_reembolsados"])
)

col3.metric(
    "Pratos disponíveis",
    f"{pratos_ativos} / {total_pratos}"
)

st.divider()

st.subheader("Acompanhamento dos pedidos")

st.markdown("##### Pedidos nos últimos 7 dias")

st.bar_chart(
    dados["dados_diarios"],
    x="Dia",
    y="Pedidos",
    color="#8F302B",
    height=280,
    width="stretch",
    sort=False
)

st.caption(
    "Quantidade de pedidos registrados em cada dia, considerando "
    "o horário de Brasília."
)

st.divider()

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Pedidos por status")

    st.bar_chart(
        dados["dados_status"],
        x="Status",
        y="Quantidade",
        color="#8F302B",
        horizontal=True,
        height=320,
        width="stretch",
        sort=False
    )

with col2:
    st.markdown("##### Pratos mais pedidos")

    if not dados["produtos_populares"].empty:

        st.bar_chart(
            dados["produtos_populares"],
            x="Prato",
            y="Quantidade",
            color="#8F302B",
            horizontal=True,
            height=320,
            width="stretch",
            sort=False
        )

    else:
        st.info("Ainda não existem pedidos com pratos registrados.")

st.divider()

st.subheader("⚠️ Atenção ao estoque")

if dados["estoque_baixo"]:

    st.warning(
        f"{len(dados['estoque_baixo'])} variação(ões) de ingredientes "
        "estão no nível mínimo ou abaixo dele."
    )

    st.dataframe(
        pd.DataFrame(dados["estoque_baixo"]),
        use_container_width=True,
        hide_index=True
    )

else:
    st.success(
        "Nenhuma variação está abaixo do estoque mínimo configurado."
    )

st.divider()

st.subheader("Pedidos recentes")

if dados["pedidos_recentes"]:

    st.dataframe(
        pd.DataFrame(dados["pedidos_recentes"]),
        use_container_width=True,
        hide_index=True
    )

else:
    st.info("Ainda não existem pedidos cadastrados.")
