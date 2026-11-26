
from data_base.conexao import conectar
from data_base.receitas import converter_quantidade


STATUS_PEDIDO = [
    "Pendente",
    "Em preparo",
    "Saiu para entrega",
    "Entregue"
]

FORMAS_PAGAMENTO = [
    "Pix",
    "Dinheiro",
    "Cartão de crédito",
    "Cartão de débito",
    "Outro"
]

STATUS_PAGAMENTO = [
    "Pendente",
    "Pago"
]


def listar_produtos_disponiveis():
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT id, nome, descricao, categoria, preco, imagem
            FROM produtos
            WHERE disponivel = 1
            ORDER BY nome
        """)

        return cursor.fetchall()

    finally:
        conexao.close()


def cadastrar_pedido(
    cliente_nome,
    telefone,
    rua,
    numero,
    bairro,
    cidade,
    complemento,
    itens,
    taxa_entrega=0,
    forma_pagamento="Pix",
    status_pagamento="Pendente"
):
    cliente_nome = cliente_nome.strip()
    telefone = telefone.strip() if telefone else ""
    rua = rua.strip()
    numero = numero.strip()
    bairro = bairro.strip()
    cidade = cidade.strip()
    complemento = complemento.strip() if complemento else ""

    taxa_entrega = float(taxa_entrega)

    if not cliente_nome:
        raise ValueError("Informe o nome do cliente.")

    if not rua or not numero or not bairro or not cidade:
        raise ValueError("Preencha todos os campos obrigatórios do endereço.")

    if not itens:
        raise ValueError("Selecione pelo menos um prato.")

    if taxa_entrega < 0:
        raise ValueError("A taxa de entrega não pode ser negativa.")

    if forma_pagamento not in FORMAS_PAGAMENTO:
        raise ValueError("Forma de pagamento inválida.")

    if status_pagamento not in STATUS_PAGAMENTO:
        raise ValueError("Status de pagamento inválido.")

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        itens_validados = []
        subtotal_pedido = 0

        for item in itens:
            produto_id = int(item["produto_id"])
            quantidade = int(item["quantidade"])

            if quantidade <= 0:
                raise ValueError("A quantidade deve ser maior que zero.")

            cursor.execute("""
                SELECT id, nome, preco, disponivel
                FROM produtos
                WHERE id = ?
            """, (produto_id,))

            produto = cursor.fetchone()

            if produto is None:
                raise ValueError("Um dos pratos selecionados não existe.")

            if produto["disponivel"] != 1:
                raise ValueError(
                    f'O prato {produto["nome"]} não está disponível.'
                )

            preco_unitario = float(produto["preco"])
            subtotal = round(preco_unitario * quantidade, 2)

            subtotal_pedido += subtotal

            itens_validados.append({
                "produto_id": produto["id"],
                "produto_nome": produto["nome"],
                "quantidade": quantidade,
                "preco_unitario": preco_unitario,
                "subtotal": subtotal
            })

        subtotal_pedido = round(subtotal_pedido, 2)
        total_pedido = round(subtotal_pedido + taxa_entrega, 2)

        cursor.execute("""
            INSERT INTO pedidos (
                cliente_nome,
                telefone,
                rua,
                numero,
                bairro,
                cidade,
                complemento,
                subtotal,
                taxa_entrega,
                total,
                forma_pagamento,
                status_pagamento,
                data_pagamento,
                status
            )
            VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                CASE WHEN ? = 'Pago' THEN CURRENT_TIMESTAMP ELSE NULL END,
                'Pendente'
            )
        """, (
            cliente_nome,
            telefone,
            rua,
            numero,
            bairro,
            cidade,
            complemento,
            subtotal_pedido,
            taxa_entrega,
            total_pedido,
            forma_pagamento,
            status_pagamento,
            status_pagamento
        ))

        pedido_id = cursor.lastrowid

        for item in itens_validados:
            cursor.execute("""
                INSERT INTO itens_pedido (
                    pedido_id,
                    produto_id,
                    produto_nome,
                    quantidade,
                    preco_unitario,
                    subtotal
                )
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                pedido_id,
                item["produto_id"],
                item["produto_nome"],
                item["quantidade"],
                item["preco_unitario"],
                item["subtotal"]
            ))

        conexao.commit()

        return pedido_id

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def deduzir_estoque_pedido(conexao, pedido_id):
    cursor = conexao.cursor()

    cursor.execute("""
        SELECT pedido_id
        FROM baixas_estoque_pedido
        WHERE pedido_id = ?
    """, (pedido_id,))

    if cursor.fetchone():
        return

    cursor.execute("""
        SELECT produto_id, produto_nome, quantidade
        FROM itens_pedido
        WHERE pedido_id = ?
    """, (pedido_id,))

    itens = cursor.fetchall()

    if not itens:
        raise ValueError("Este pedido não possui pratos registrados.")

    consumo_total = {}

    for item in itens:

        produto_id = item["produto_id"]
        produto_nome = item["produto_nome"]
        quantidade_pedida = int(item["quantidade"])

        cursor.execute("""
            SELECT
                pv.variacao_id,
                pv.quantidade_necessaria,
                pv.unidade AS unidade_receita,
                v.nome AS variacao,
                v.quantidade AS estoque_atual,
                v.unidade AS unidade_estoque,
                i.nome AS ingrediente
            FROM produto_variacoes pv
            INNER JOIN variacoes_ingrediente v
                ON v.id = pv.variacao_id
            INNER JOIN ingredientes i
                ON i.id = v.ingrediente_id
            WHERE pv.produto_id = ?
        """, (produto_id,))

        receita = cursor.fetchall()

        if not receita:
            raise ValueError(
                f'O prato "{produto_nome}" não possui ingredientes '
                "cadastrados na ficha técnica do Cardápio."
            )

        for componente in receita:

            variacao_id = componente["variacao_id"]

            consumo_unitario = converter_quantidade(
                componente["quantidade_necessaria"],
                componente["unidade_receita"],
                componente["unidade_estoque"]
            )

            consumo = round(
                consumo_unitario * quantidade_pedida,
                6
            )

            if variacao_id not in consumo_total:
                consumo_total[variacao_id] = {
                    "ingrediente": componente["ingrediente"],
                    "variacao": componente["variacao"],
                    "quantidade_atual": float(componente["estoque_atual"]),
                    "unidade": componente["unidade_estoque"],
                    "consumo": 0
                }

            consumo_total[variacao_id]["consumo"] += consumo

    for variacao_id, dados in consumo_total.items():

        necessario = round(dados["consumo"], 6)
        disponivel = dados["quantidade_atual"]

        if disponivel < necessario:
            raise ValueError(
                f'Estoque insuficiente para {dados["ingrediente"]} '
                f'({dados["variacao"]}). '
                f'Disponível: {disponivel:g} {dados["unidade"]}. '
                f'Necessário: {necessario:g} {dados["unidade"]}.'
            )

    for variacao_id, dados in consumo_total.items():

        necessario = round(dados["consumo"], 6)

        cursor.execute("""
            UPDATE variacoes_ingrediente
            SET quantidade = quantidade - ?
            WHERE id = ?
              AND quantidade >= ?
        """, (
            necessario,
            variacao_id,
            necessario
        ))

        if cursor.rowcount == 0:
            raise ValueError(
                f'Estoque insuficiente para {dados["ingrediente"]} '
                f'({dados["variacao"]}).'
            )

        cursor.execute("""
            INSERT INTO movimentacoes_variacoes (
                variacao_id,
                tipo,
                quantidade,
                motivo
            )
            VALUES (?, 'Saída', ?, ?)
        """, (
            variacao_id,
            necessario,
            f"Consumo do pedido #{pedido_id}"
        ))

    cursor.execute("""
        INSERT INTO baixas_estoque_pedido (pedido_id)
        VALUES (?)
    """, (pedido_id,))


def listar_pedidos(busca="", status=None):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        sql = """
            SELECT
                id,
                cliente_nome,
                telefone,
                rua,
                numero,
                bairro,
                cidade,
                complemento,
                data_pedido,
                subtotal,
                taxa_entrega,
                total,
                status,
                forma_pagamento,
                status_pagamento,
                data_pagamento
            FROM pedidos
            WHERE 1 = 1
        """

        parametros = []

        if busca:
            termo = f"%{busca}%"

            sql += """
                AND (
                    cliente_nome LIKE ?
                    OR telefone LIKE ?
                    OR CAST(id AS TEXT) LIKE ?
                )
            """

            parametros.extend([termo, termo, termo])

        if status and status != "Todos":
            sql += " AND status = ?"
            parametros.append(status)

        sql += " ORDER BY id DESC"

        cursor.execute(sql, parametros)

        return cursor.fetchall()

    finally:
        conexao.close()


def listar_itens_pedido(pedido_id):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                produto_nome,
                quantidade,
                preco_unitario,
                subtotal
            FROM itens_pedido
            WHERE pedido_id = ?
            ORDER BY id
        """, (pedido_id,))

        return cursor.fetchall()

    finally:
        conexao.close()


def atualizar_status_pedido(pedido_id, novo_status):
    if novo_status not in STATUS_PEDIDO:
        raise ValueError("Status de pedido inválido.")

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT status
            FROM pedidos
            WHERE id = ?
        """, (pedido_id,))

        pedido = cursor.fetchone()

        if pedido is None:
            raise ValueError("Pedido não encontrado.")

        status_atual = pedido["status"]

        transicoes = {
            "Pendente": "Em preparo",
            "Agendado": "Em preparo",
            "Em preparo": "Saiu para entrega",
            "Saiu para entrega": "Entregue"
        }

        if status_atual == novo_status:
            return

        if transicoes.get(status_atual) != novo_status:
            raise ValueError(
                f"Não é possível mudar de {status_atual} para {novo_status}. "
                "Siga a ordem das etapas do pedido."
            )

        if novo_status == "Em preparo":
            deduzir_estoque_pedido(conexao, pedido_id)

        cursor.execute("""
            UPDATE pedidos
            SET status = ?
            WHERE id = ?
        """, (novo_status, pedido_id))

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def atualizar_pagamento(
    pedido_id,
    forma_pagamento,
    status_pagamento
):
    if forma_pagamento not in FORMAS_PAGAMENTO:
        raise ValueError("Forma de pagamento inválida.")

    if status_pagamento not in STATUS_PAGAMENTO:
        raise ValueError("Status de pagamento inválido.")

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT status, status_pagamento
            FROM pedidos
            WHERE id = ?
        """, (pedido_id,))

        pedido = cursor.fetchone()

        if pedido is None:
            raise ValueError("Pedido não encontrado.")

        if pedido["status"] == "Cancelado":
            raise ValueError(
                "Gerencie os pagamentos de pedidos cancelados "
                "pela tela Cancelamentos."
            )

        if pedido["status_pagamento"] in (
            "Reembolsado",
            "Reembolso parcial"
        ):
            raise ValueError(
                "Este pedido possui reembolso registrado e não pode "
                "ter o pagamento alterado por esta tela."
            )

        cursor.execute("""
            UPDATE pedidos
            SET forma_pagamento = ?,
                status_pagamento = ?,
                data_pagamento = CASE
                    WHEN ? = 'Pago'
                    THEN COALESCE(data_pagamento, CURRENT_TIMESTAMP)
                    ELSE NULL
                END
            WHERE id = ?
        """, (
            forma_pagamento,
            status_pagamento,
            status_pagamento,
            pedido_id
        ))

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()
