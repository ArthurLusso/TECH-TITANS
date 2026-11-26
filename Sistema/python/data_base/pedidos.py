
from data_base.conexao import conectar


STATUS_PEDIDO = [
    "Pendente",
    "Em preparo",
    "Saiu para entrega",
    "Entregue"
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
    itens
):
    cliente_nome = cliente_nome.strip()
    telefone = telefone.strip() if telefone else ""
    rua = rua.strip()
    numero = numero.strip()
    bairro = bairro.strip()
    cidade = cidade.strip()
    complemento = complemento.strip() if complemento else ""

    if not cliente_nome:
        raise ValueError("Informe o nome do cliente.")

    if not rua or not numero or not bairro or not cidade:
        raise ValueError("Preencha todos os campos obrigatórios do endereço.")

    if not itens:
        raise ValueError("Selecione pelo menos um prato.")

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        itens_validados = []
        total = 0

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

            total += subtotal

            itens_validados.append({
                "produto_id": produto["id"],
                "produto_nome": produto["nome"],
                "quantidade": quantidade,
                "preco_unitario": preco_unitario,
                "subtotal": subtotal
            })

        total = round(total, 2)

        cursor.execute("""
            INSERT INTO pedidos (
                cliente_nome,
                telefone,
                rua,
                numero,
                bairro,
                cidade,
                complemento,
                total,
                status
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            cliente_nome,
            telefone,
            rua,
            numero,
            bairro,
            cidade,
            complemento,
            total,
            "Pendente"
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
                total,
                status
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
            UPDATE pedidos
            SET status = ?
            WHERE id = ?
              AND status != 'Cancelado'
        """, (novo_status, pedido_id))

        if cursor.rowcount == 0:
            raise ValueError(
                "Pedido não encontrado ou já cancelado."
            )

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()
