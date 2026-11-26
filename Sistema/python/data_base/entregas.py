
from data_base.conexao import conectar


STATUS_ENTREGA = [
    "Aguardando",
    "Saiu para entrega",
    "Entregue"
]


def sincronizar_entregas():
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT id, status
            FROM pedidos
            WHERE status IN (
                'Em preparo',
                'Saiu para entrega',
                'Entregue'
            )
        """)

        pedidos = cursor.fetchall()

        for pedido in pedidos:

            pedido_id = pedido["id"]
            status_pedido = pedido["status"]

            if status_pedido == "Em preparo":
                status_entrega = "Aguardando"
            else:
                status_entrega = status_pedido

            cursor.execute("""
                SELECT id
                FROM entregas
                WHERE pedido_id = ?
            """, (pedido_id,))

            entrega = cursor.fetchone()

            if entrega is None:

                cursor.execute("""
                    INSERT INTO entregas (
                        pedido_id,
                        status,
                        data_saida,
                        data_entrega
                    )
                    VALUES (
                        ?,
                        ?,
                        CASE
                            WHEN ? IN ('Saiu para entrega', 'Entregue')
                            THEN CURRENT_TIMESTAMP
                            ELSE NULL
                        END,
                        CASE
                            WHEN ? = 'Entregue'
                            THEN CURRENT_TIMESTAMP
                            ELSE NULL
                        END
                    )
                """, (
                    pedido_id,
                    status_entrega,
                    status_pedido,
                    status_pedido
                ))

            elif status_pedido in (
                "Saiu para entrega",
                "Entregue"
            ):

                cursor.execute("""
                    UPDATE entregas
                    SET status = ?,
                        data_saida = COALESCE(
                            data_saida,
                            CURRENT_TIMESTAMP
                        ),
                        data_entrega = CASE
                            WHEN ? = 'Entregue'
                            THEN COALESCE(data_entrega, CURRENT_TIMESTAMP)
                            ELSE data_entrega
                        END
                    WHERE pedido_id = ?
                """, (
                    status_entrega,
                    status_pedido,
                    pedido_id
                ))

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def listar_entregas(busca="", status=None):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        sql = """
            SELECT
                e.id AS entrega_id,
                e.pedido_id,
                e.entregador,
                e.status AS status_entrega,
                e.data_saida,
                e.previsao_entrega,
                e.data_entrega,
                p.cliente_nome,
                p.telefone,
                p.rua,
                p.numero,
                p.bairro,
                p.cidade,
                p.complemento,
                p.data_pedido,
                p.subtotal,
                p.taxa_entrega,
                p.total,
                p.forma_pagamento,
                p.status_pagamento,
                p.status AS status_pedido
            FROM entregas e
            INNER JOIN pedidos p
                ON p.id = e.pedido_id
            WHERE p.status != 'Cancelado'
        """

        parametros = []

        if busca:
            termo = f"%{busca}%"

            sql += """
                AND (
                    p.cliente_nome LIKE ?
                    OR p.telefone LIKE ?
                    OR CAST(p.id AS TEXT) LIKE ?
                    OR e.entregador LIKE ?
                )
            """

            parametros.extend([
                termo,
                termo,
                termo,
                termo
            ])

        if status and status != "Todas":
            sql += " AND e.status = ?"
            parametros.append(status)

        sql += " ORDER BY e.id DESC"

        cursor.execute(sql, parametros)

        return cursor.fetchall()

    finally:
        conexao.close()


def atualizar_entrega(
    entrega_id,
    entregador,
    previsao_entrega,
    novo_status
):
    if novo_status not in STATUS_ENTREGA:
        raise ValueError("Status de entrega inválido.")

    entregador = entregador.strip() if entregador else ""

    previsao_entrega = (
        previsao_entrega.strip()
        if previsao_entrega
        else ""
    )

    if novo_status != "Aguardando" and not entregador:
        raise ValueError(
            "Informe o nome do entregador antes de iniciar ou concluir a entrega."
        )

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT pedido_id, status
            FROM entregas
            WHERE id = ?
        """, (entrega_id,))

        entrega = cursor.fetchone()

        if entrega is None:
            raise ValueError("Entrega não encontrada.")

        pedido_id = entrega["pedido_id"]

        cursor.execute("""
            SELECT status
            FROM pedidos
            WHERE id = ?
        """, (pedido_id,))

        pedido = cursor.fetchone()

        if pedido is None or pedido["status"] == "Cancelado":
            raise ValueError(
                "Este pedido não está disponível para entrega."
            )

        status_pedido = pedido["status"]

        transicoes = {
            "Em preparo": ["Aguardando", "Saiu para entrega"],
            "Saiu para entrega": ["Saiu para entrega", "Entregue"],
            "Entregue": ["Entregue"]
        }

        permitidos = transicoes.get(status_pedido, [])

        if novo_status not in permitidos:
            raise ValueError(
                "Essa alteração não corresponde à etapa atual do pedido. "
                "Verifique o andamento na tela Pedidos."
            )

        cursor.execute("""
            UPDATE entregas
            SET entregador = ?,
                previsao_entrega = ?,
                status = ?,
                data_saida = CASE
                    WHEN ? IN ('Saiu para entrega', 'Entregue')
                    THEN COALESCE(data_saida, CURRENT_TIMESTAMP)
                    ELSE data_saida
                END,
                data_entrega = CASE
                    WHEN ? = 'Entregue'
                    THEN COALESCE(data_entrega, CURRENT_TIMESTAMP)
                    ELSE data_entrega
                END
            WHERE id = ?
        """, (
            entregador or None,
            previsao_entrega or None,
            novo_status,
            novo_status,
            novo_status,
            entrega_id
        ))

        if novo_status == "Aguardando":
            novo_status_pedido = "Em preparo"

        elif novo_status == "Saiu para entrega":
            novo_status_pedido = "Saiu para entrega"

        else:
            novo_status_pedido = "Entregue"

        cursor.execute("""
            UPDATE pedidos
            SET status = ?
            WHERE id = ?
        """, (novo_status_pedido, pedido_id))

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()
