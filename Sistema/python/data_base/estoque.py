
from data_base.conexao import conectar


CATEGORIAS = [
    "Massas",
    "Congelados",
    "Verduras",
    "Bebidas"
]


UNIDADES = [
    "kg",
    "g",
    "L",
    "ml",
    "unidade",
    "pacote"
]


def listar_ingredientes(categoria=None):

    conexao = conectar()

    try:
        if categoria:
            resultado = conexao.execute(
                """
                SELECT *
                FROM ingredientes
                WHERE categoria = ?
                ORDER BY nome
                """,
                (categoria,)
            ).fetchall()

        else:
            resultado = conexao.execute(
                """
                SELECT *
                FROM ingredientes
                ORDER BY categoria, nome
                """
            ).fetchall()

        return [dict(item) for item in resultado]

    finally:
        conexao.close()


def cadastrar_ingrediente(
    nome,
    categoria,
    quantidade,
    unidade,
    estoque_minimo
):

    nome = nome.strip()

    if not nome:
        raise ValueError("Informe o nome do ingrediente.")

    if categoria not in CATEGORIAS:
        raise ValueError("Categoria inválida.")

    if unidade not in UNIDADES:
        raise ValueError("Unidade inválida.")

    if quantidade < 0 or estoque_minimo < 0:
        raise ValueError("As quantidades não podem ser negativas.")

    conexao = conectar()

    try:
        existente = conexao.execute(
            """
            SELECT id FROM ingredientes
            WHERE nome = ? COLLATE NOCASE
            AND categoria = ?
            """,
            (nome, categoria)
        ).fetchone()

        if existente:
            raise ValueError(
                "Já existe um ingrediente com esse nome nessa categoria."
            )

        cursor = conexao.execute(
            """
            INSERT INTO ingredientes (
                nome,
                categoria,
                quantidade,
                unidade,
                estoque_minimo
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (nome, categoria, quantidade, unidade, estoque_minimo)
        )

        ingrediente_id = cursor.lastrowid

        if quantidade > 0:
            conexao.execute(
                """
                INSERT INTO movimentacoes_estoque (
                    ingrediente_id,
                    tipo,
                    quantidade,
                    motivo
                )
                VALUES (?, ?, ?, ?)
                """,
                (
                    ingrediente_id,
                    "Entrada",
                    quantidade,
                    "Cadastro inicial"
                )
            )

        conexao.commit()

        return ingrediente_id

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def movimentar_estoque(
    ingrediente_id,
    tipo,
    quantidade,
    motivo=""
):

    if tipo not in ("Entrada", "Saída"):
        raise ValueError("Tipo de movimentação inválido.")

    if quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")

    conexao = conectar()

    try:
        ingrediente = conexao.execute(
            """
            SELECT quantidade
            FROM ingredientes
            WHERE id = ?
            """,
            (ingrediente_id,)
        ).fetchone()

        if ingrediente is None:
            raise ValueError("Ingrediente não encontrado.")

        estoque_atual = ingrediente["quantidade"]

        if tipo == "Saída":
            if quantidade > estoque_atual:
                raise ValueError(
                    "Estoque insuficiente para essa saída."
                )

            novo_estoque = estoque_atual - quantidade

        else:
            novo_estoque = estoque_atual + quantidade

        conexao.execute(
            """
            UPDATE ingredientes
            SET quantidade = ?,
                atualizado_em = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (novo_estoque, ingrediente_id)
        )

        conexao.execute(
            """
            INSERT INTO movimentacoes_estoque (
                ingrediente_id,
                tipo,
                quantidade,
                motivo
            )
            VALUES (?, ?, ?, ?)
            """,
            (ingrediente_id, tipo, quantidade, motivo)
        )

        conexao.commit()

        return novo_estoque

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()
