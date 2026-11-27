
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


def listar_variacoes(ingrediente_id):

    conexao = conectar()

    try:
        resultado = conexao.execute(
            """
            SELECT *
            FROM variacoes_ingrediente
            WHERE ingrediente_id = ?
            ORDER BY nome
            """,
            (ingrediente_id,)
        ).fetchall()

        return [dict(item) for item in resultado]

    finally:
        conexao.close()


def cadastrar_ingrediente(nome, categoria):

    nome = nome.strip()

    if not nome:
        raise ValueError("Informe o nome do grupo.")

    if categoria not in CATEGORIAS:
        raise ValueError("Categoria inválida.")

    conexao = conectar()

    try:
        existente = conexao.execute(
            """
            SELECT id
            FROM ingredientes
            WHERE nome = ? COLLATE NOCASE
            AND categoria = ?
            """,
            (nome, categoria)
        ).fetchone()

        if existente:
            raise ValueError(
                "Esse grupo já existe nessa categoria."
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
            VALUES (?, ?, 0, 'kg', 0)
            """,
            (nome, categoria)
        )

        conexao.commit()

        return cursor.lastrowid

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def adicionar_variacao(
    ingrediente_id,
    nome,
    quantidade,
    unidade,
    estoque_minimo
):

    nome = nome.strip()

    if not nome:
        raise ValueError("Informe o nome da variação.")

    if quantidade < 0 or estoque_minimo < 0:
        raise ValueError("As quantidades não podem ser negativas.")

    if unidade not in UNIDADES:
        raise ValueError("Unidade inválida.")

    conexao = conectar()

    try:
        ingrediente = conexao.execute(
            """
            SELECT id
            FROM ingredientes
            WHERE id = ?
            """,
            (ingrediente_id,)
        ).fetchone()

        if ingrediente is None:
            raise ValueError("Grupo não encontrado.")

        existente = conexao.execute(
            """
            SELECT id
            FROM variacoes_ingrediente
            WHERE ingrediente_id = ?
            AND nome = ? COLLATE NOCASE
            """,
            (ingrediente_id, nome)
        ).fetchone()

        if existente:
            raise ValueError("Essa variação já existe no grupo.")

        cursor = conexao.execute(
            """
            INSERT INTO variacoes_ingrediente (
                ingrediente_id,
                nome,
                quantidade,
                unidade,
                estoque_minimo
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                ingrediente_id,
                nome,
                quantidade,
                unidade,
                estoque_minimo
            )
        )

        variacao_id = cursor.lastrowid

        if quantidade > 0:
            conexao.execute(
                """
                INSERT INTO movimentacoes_variacoes (
                    variacao_id,
                    tipo,
                    quantidade,
                    motivo
                )
                VALUES (?, 'Entrada', ?, ?)
                """,
                (
                    variacao_id,
                    quantidade,
                    "Estoque inicial da variação"
                )
            )

        conexao.commit()

        return variacao_id

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def editar_variacao(
    variacao_id,
    nome,
    unidade,
    estoque_minimo
):

    nome = nome.strip()

    if not nome:
        raise ValueError("Informe o nome da variação.")

    if unidade not in UNIDADES:
        raise ValueError("Unidade inválida.")

    if estoque_minimo < 0:
        raise ValueError("O estoque mínimo não pode ser negativo.")

    conexao = conectar()

    try:
        variacao = conexao.execute(
            """
            SELECT ingrediente_id
            FROM variacoes_ingrediente
            WHERE id = ?
            """,
            (variacao_id,)
        ).fetchone()

        if variacao is None:
            raise ValueError("Variação não encontrada.")

        existente = conexao.execute(
            """
            SELECT id
            FROM variacoes_ingrediente
            WHERE ingrediente_id = ?
            AND nome = ? COLLATE NOCASE
            AND id != ?
            """,
            (variacao["ingrediente_id"], nome, variacao_id)
        ).fetchone()

        if existente:
            raise ValueError("Já existe uma variação com esse nome.")

        conexao.execute(
            """
            UPDATE variacoes_ingrediente
            SET nome = ?,
                unidade = ?,
                estoque_minimo = ?
            WHERE id = ?
            """,
            (nome, unidade, estoque_minimo, variacao_id)
        )

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()



def remover_variacao(variacao_id):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT id
            FROM variacoes_ingrediente
            WHERE id = ?
        """, (variacao_id,))

        variacao = cursor.fetchone()

        if variacao is None:
            raise ValueError("Variação não encontrada.")

        cursor.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
        """)

        tabelas_existentes = {
            linha["name"]
            for linha in cursor.fetchall()
        }

        if "produto_variacoes" in tabelas_existentes:
            cursor.execute("""
                DELETE FROM produto_variacoes
                WHERE variacao_id = ?
            """, (variacao_id,))

        if "movimentacoes_variacoes" in tabelas_existentes:
            cursor.execute("""
                DELETE FROM movimentacoes_variacoes
                WHERE variacao_id = ?
            """, (variacao_id,))

        cursor.execute("""
            DELETE FROM variacoes_ingrediente
            WHERE id = ?
        """, (variacao_id,))

        if cursor.rowcount == 0:
            raise ValueError("Não foi possível excluir a variação.")

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()



def movimentar_estoque(
    variacao_id,
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
        conexao.execute("BEGIN IMMEDIATE")

        variacao = conexao.execute(
            """
            SELECT quantidade
            FROM variacoes_ingrediente
            WHERE id = ?
            """,
            (variacao_id,)
        ).fetchone()

        if variacao is None:
            raise ValueError("Variação não encontrada.")

        estoque_atual = variacao["quantidade"]

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
            UPDATE variacoes_ingrediente
            SET quantidade = ?
            WHERE id = ?
            """,
            (novo_estoque, variacao_id)
        )

        conexao.execute(
            """
            INSERT INTO movimentacoes_variacoes (
                variacao_id,
                tipo,
                quantidade,
                motivo
            )
            VALUES (?, ?, ?, ?)
            """,
            (variacao_id, tipo, quantidade, motivo)
        )

        conexao.commit()

        return novo_estoque

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def listar_movimentacoes(variacao_id):

    conexao = conectar()

    try:
        resultado = conexao.execute(
            """
            SELECT tipo, quantidade, motivo, data_movimentacao
            FROM movimentacoes_variacoes
            WHERE variacao_id = ?
            ORDER BY id DESC
            """,
            (variacao_id,)
        ).fetchall()

        return [dict(item) for item in resultado]

    finally:
        conexao.close()
