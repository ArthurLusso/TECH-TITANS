
from data_base.conexao import conectar


STATUS_REEMBOLSO = [
    "Pendente",
    "Reembolsado",
    "Não reembolsado"
]


def listar_pedidos_cancelaveis():
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                p.id,
                p.cliente_nome,
                p.total,
                p.status,
                p.data_pedido,
                p.status_pagamento,
                p.forma_pagamento,
                EXISTS (
                    SELECT 1
                    FROM baixas_estoque_pedido b
                    WHERE b.pedido_id = p.id
                ) AS estoque_descontado
            FROM pedidos p
            WHERE p.status NOT IN ('Cancelado', 'Entregue')
            ORDER BY p.id DESC
        """)

        return cursor.fetchall()

    finally:
        conexao.close()


def registrar_cancelamento(
    pedido_id,
    motivo,
    status_reembolso,
    valor_reembolso
):
    motivo = motivo.strip()

    if not motivo:
        raise ValueError("Informe o motivo do cancelamento.")

    if status_reembolso not in STATUS_REEMBOLSO:
        raise ValueError("Status de reembolso inválido.")

    valor_reembolso = float(valor_reembolso)

    if valor_reembolso < 0:
        raise ValueError("O valor do reembolso não pode ser negativo.")

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT total, status, status_pagamento
            FROM pedidos
            WHERE id = ?
        """, (pedido_id,))

        pedido = cursor.fetchone()

        if pedido is None:
            raise ValueError("Pedido não encontrado.")

        if pedido["status"] in ("Cancelado", "Entregue"):
            raise ValueError("Este pedido não pode ser cancelado.")

        total_pedido = float(pedido["total"])

        if valor_reembolso > total_pedido:
            raise ValueError(
                "O valor do reembolso não pode ser maior que o pedido."
            )

        if status_reembolso == "Não reembolsado":
            valor_reembolso = 0

        if status_reembolso == "Reembolsado":
            if pedido["status_pagamento"] not in (
                "Pago",
                "Reembolso parcial"
            ):
                raise ValueError(
                    "Não é possível registrar um reembolso sem que "
                    "o pagamento tenha sido marcado como Pago."
                )

            if valor_reembolso <= 0:
                raise ValueError(
                    "Informe um valor maior que zero para o reembolso."
                )

        valor_reembolso = round(valor_reembolso, 2)
        valor_prejuizo = round(total_pedido - valor_reembolso, 2)

        cursor.execute("""
            INSERT INTO cancelamentos (
                pedido_id,
                motivo,
                status_reembolso,
                valor_reembolso,
                valor_prejuizo
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            pedido_id,
            motivo,
            status_reembolso,
            valor_reembolso,
            valor_prejuizo
        ))

        cursor.execute("""
            UPDATE pedidos
            SET status = 'Cancelado'
            WHERE id = ?
        """, (pedido_id,))

        if status_reembolso == "Reembolsado":
            if valor_reembolso >= total_pedido:
                novo_status_pagamento = "Reembolsado"
            else:
                novo_status_pagamento = "Reembolso parcial"

            cursor.execute("""
                UPDATE pedidos
                SET status_pagamento = ?
                WHERE id = ?
            """, (novo_status_pagamento, pedido_id))

        conexao.commit()

        return cursor.lastrowid

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def listar_cancelamentos(busca="", status_reembolso=None):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        sql = """
            SELECT
                c.id AS cancelamento_id,
                c.pedido_id,
                c.motivo,
                c.status_reembolso,
                c.valor_reembolso,
                c.valor_prejuizo,
                c.data_cancelamento,
                p.cliente_nome,
                p.telefone,
                p.total AS total_pedido,
                p.data_pedido,
                p.forma_pagamento,
                p.status_pagamento
            FROM cancelamentos c
            INNER JOIN pedidos p
                ON p.id = c.pedido_id
            WHERE 1 = 1
        """

        parametros = []

        if busca:
            termo = f"%{busca}%"

            sql += """
                AND (
                    p.cliente_nome LIKE ?
                    OR p.telefone LIKE ?
                    OR CAST(p.id AS TEXT) LIKE ?
                    OR c.motivo LIKE ?
                )
            """

            parametros.extend([
                termo,
                termo,
                termo,
                termo
            ])

        if status_reembolso and status_reembolso != "Todos":
            sql += " AND c.status_reembolso = ?"
            parametros.append(status_reembolso)

        sql += " ORDER BY c.id DESC"

        cursor.execute(sql, parametros)

        return cursor.fetchall()

    finally:
        conexao.close()


def atualizar_reembolso(
    cancelamento_id,
    status_reembolso,
    valor_reembolso
):
    if status_reembolso not in STATUS_REEMBOLSO:
        raise ValueError("Status de reembolso inválido.")

    valor_reembolso = float(valor_reembolso)

    if valor_reembolso < 0:
        raise ValueError("O valor do reembolso não pode ser negativo.")

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                c.pedido_id,
                p.total,
                p.status_pagamento
            FROM cancelamentos c
            INNER JOIN pedidos p
                ON p.id = c.pedido_id
            WHERE c.id = ?
        """, (cancelamento_id,))

        cancelamento = cursor.fetchone()

        if cancelamento is None:
            raise ValueError("Cancelamento não encontrado.")

        pedido_id = cancelamento["pedido_id"]
        total_pedido = float(cancelamento["total"])
        pagamento_atual = cancelamento["status_pagamento"]

        if valor_reembolso > total_pedido:
            raise ValueError(
                "O valor do reembolso não pode ser maior que o pedido."
            )

        if status_reembolso == "Não reembolsado":
            valor_reembolso = 0

        if status_reembolso == "Reembolsado":

            if pagamento_atual not in (
                "Pago",
                "Reembolso parcial",
                "Reembolsado"
            ):
                raise ValueError(
                    "Este pedido ainda não está marcado como pago."
                )

            if valor_reembolso <= 0:
                raise ValueError(
                    "Informe um valor maior que zero para o reembolso."
                )

        valor_reembolso = round(valor_reembolso, 2)
        valor_prejuizo = round(total_pedido - valor_reembolso, 2)

        cursor.execute("""
            UPDATE cancelamentos
            SET status_reembolso = ?,
                valor_reembolso = ?,
                valor_prejuizo = ?
            WHERE id = ?
        """, (
            status_reembolso,
            valor_reembolso,
            valor_prejuizo,
            cancelamento_id
        ))

        if status_reembolso == "Reembolsado":

            if valor_reembolso >= total_pedido:
                novo_status_pagamento = "Reembolsado"
            else:
                novo_status_pagamento = "Reembolso parcial"

            cursor.execute("""
                UPDATE pedidos
                SET status_pagamento = ?
                WHERE id = ?
            """, (novo_status_pagamento, pedido_id))

        elif pagamento_atual in (
            "Reembolsado",
            "Reembolso parcial"
        ):
            cursor.execute("""
                UPDATE pedidos
                SET status_pagamento = 'Pago'
                WHERE id = ?
            """, (pedido_id,))

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()
