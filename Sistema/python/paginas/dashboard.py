
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
                COUNT(*) AS quantidade,
                COALESCE(SUM(
                    CASE
                        WHEN status = 'Entregue'
                        THEN total ELSE 0
                    END
                ), 0) AS faturamento
            FROM pedidos
            WHERE date(data_pedido, '-3 hours') = ?
        """, (hoje.isoformat(),))

        dados_hoje = cursor.fetchone()

        cursor.execute("""
            SELECT COALESCE(SUM(total), 0)
            FROM pedidos
            WHERE status = 'Entregue'
        """)

        faturamento_total = cursor.fetchone()[0] or 0

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

        dados_status = [
            {
                "Status": status,
                "Quantidade": quantidade_status.get(status, 0)
            }
            for status in status_conhecidos
        ]

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

        dados_diarios = pd.DataFrame(
            {
                "Pedidos": [
                    pedidos_por_dia.get(data.isoformat(), 0)
                    for data in datas_periodo
                ]
            },
            index=[
                data.strftime("%d/%m")
                for data in datas_periodo
            ]
        )

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

        produtos_populares = [
            {
                "Prato": linha["produto_nome"],
                "Quantidade": linha["quantidade"]
            }
            for linha in cursor.fetchall()
        ]

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
                "Status": linha["status"],
                "Data": formatar_data_hora(linha["data_pedido"])
            }
            for linha in cursor.fetchall()
        ]

        cursor.execute("""
            SELECT
                COUNT(*) AS total,
                SUM(CASE WHEN disponivel = 1 THEN 1 ELSE 0 END) AS ativos
            FROM produtos
        """)

        resumo_cardapio = cursor.fetchone()

        return {
            "resumo": resumo,
            "dados_hoje": dados_hoje,
            "faturamento_total": faturamento_total,
            "dados_status": dados_status,
            "dados_diarios": dados_diarios,
            "produtos_populares": produtos_populares,
            "estoque_baixo": estoque_baixo,
            "pedidos_recentes": pedidos_recentes,
            "resumo_cardapio": resumo_cardapio
        }

    finally:
        conexao.close()


st.set_page_config(
    page_title="TacoLoko - Dashboard",
    page_icon="🌮",
    layout="wide"
)

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
dados_hoje = dados["dados_hoje"]
cardapio = dados["resumo_cardapio"]

total_pedidos = resumo["total"] or 0
pedidos_andamento = resumo["andamento"] or 0
pedidos_entregues = resumo["entregues"] or 0
pedidos_cancelados = resumo["cancelados"] or 0

pedidos_hoje = dados_hoje["quantidade"] or 0
faturamento_hoje = dados_hoje["faturamento"] or 0

total_pratos = cardapio["total"] or 0
pratos_ativos = cardapio["ativos"] or 0


st.subheader("Indicadores gerais")

col1, col2, col3, col4 = st.columns(4)

col1.metric(
    "Total de pedidos",
    total_pedidos,
    help="Quantidade de pedidos registrados no sistema."
)

col2.metric(
    "Em andamento",
    pedidos_andamento,
    help="Pedidos pendentes, em preparo ou em rota."
)

col3.metric(
    "Entregues",
    pedidos_entregues,
    help="Quantidade de pedidos concluídos."
)

col4.metric(
    "Cancelados",
    pedidos_cancelados,
    help="Quantidade total de pedidos cancelados."
)


st.divider()

st.subheader("Resumo do dia")

col1, col2, col3 = st.columns(3)

col1.metric(
    "Pedidos recebidos hoje",
    pedidos_hoje
)

col2.metric(
    "Faturamento entregue hoje",
    formatar_preco(faturamento_hoje),
    help="Soma dos pedidos marcados como entregues hoje."
)

col3.metric(
    "Pratos disponíveis",
    f"{pratos_ativos} / {total_pratos}",
    help="Quantidade de pratos ativos em relação ao total cadastrado."
)


st.divider()

st.subheader("Acompanhamento dos pedidos")

col1, col2 = st.columns(2)

with col1:
    st.markdown("##### Pedidos nos últimos 7 dias")

    st.line_chart(
        dados["dados_diarios"],
        use_container_width=True
    )

with col2:
    st.markdown("##### Distribuição por status")

    dados_grafico_status = pd.DataFrame(
        dados["dados_status"]
    ).set_index("Status")

    st.bar_chart(
        dados_grafico_status,
        use_container_width=True
    )


st.divider()

col1, col2 = st.columns(2)

with col1:
    st.subheader("Pratos mais pedidos")

    if dados["produtos_populares"]:

        grafico_produtos = pd.DataFrame(
            dados["produtos_populares"]
        ).set_index("Prato")

        st.bar_chart(
            grafico_produtos,
            use_container_width=True
        )

    else:
        st.info("Ainda não existem pedidos com pratos registrados.")


with col2:
    st.subheader("Resumo financeiro")

    st.metric(
        "Total de pedidos entregues",
        formatar_preco(dados["faturamento_total"])
    )

    st.caption(
        "Valor acumulado dos pedidos com status Entregue. "
        "Não representa necessariamente valores já recebidos."
    )

    st.metric(
        "Prejuízo com cancelamentos",
        formatar_preco(
            sum(
                float(item["valor_prejuizo"])
                for item in __import__(
                    "data_base.cancelamentos",
                    fromlist=["listar_cancelamentos"]
                ).listar_cancelamentos()
            )
        )
    )

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
