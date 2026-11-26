
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
                id,
                cliente_nome,
                total,
                status,
                data_pedido
            FROM pedidos
            WHERE status NOT IN ('Cancelado', 'Entregue')
            ORDER BY id DESC
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
            SELECT total, status
            FROM pedidos
            WHERE id = ?
        """, (pedido_id,))

        pedido = cursor.fetchone()

        if pedido is None:
            raise ValueError("Pedido não encontrado.")

        if pedido["status"] in ("Cancelado", "Entregue"):
            raise ValueError(
                "Este pedido não pode ser cancelado."
            )

        total_pedido = float(pedido["total"])

        if status_reembolso == "Não reembolsado":
            valor_reembolso = 0

        if valor_reembolso > total_pedido:
            raise ValueError(
                "O valor do reembolso não pode ser maior que o pedido."
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
                p.data_pedido
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
                p.total
            FROM cancelamentos c
            INNER JOIN pedidos p
                ON p.id = c.pedido_id
            WHERE c.id = ?
        """, (cancelamento_id,))

        cancelamento = cursor.fetchone()

        if cancelamento is None:
            raise ValueError("Cancelamento não encontrado.")

        total_pedido = float(cancelamento["total"])

        if status_reembolso == "Não reembolsado":
            valor_reembolso = 0

        if valor_reembolso > total_pedido:
            raise ValueError(
                "O valor do reembolso não pode ser maior que o pedido."
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

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()
