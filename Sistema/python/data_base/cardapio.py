
from data_base.conexao import conectar


def listar_pratos(busca="", categoria=None, disponibilidade=None):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        sql = """
            SELECT id, nome, descricao, categoria, preco, disponivel, imagem
            FROM produtos
            WHERE 1 = 1
        """
        parametros = []

        if busca:
            sql += " AND nome LIKE ?"
            parametros.append(f"%{busca}%")

        if categoria and categoria != "Todas":
            sql += " AND categoria = ?"
            parametros.append(categoria)

        if disponibilidade is not None:
            sql += " AND disponivel = ?"
            parametros.append(int(disponibilidade))

        sql += " ORDER BY nome"

        cursor.execute(sql, parametros)

        return cursor.fetchall()

    finally:
        conexao.close()


def listar_categorias():
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT DISTINCT categoria
            FROM produtos
            WHERE categoria IS NOT NULL
              AND categoria != ''
            ORDER BY categoria
        """)

        return [linha["categoria"] for linha in cursor.fetchall()]

    finally:
        conexao.close()


def cadastrar_prato(nome, descricao, categoria, preco, imagem=None):
    nome = nome.strip()
    descricao = descricao.strip() if descricao else ""
    categoria = categoria.strip()

    if not nome:
        raise ValueError("Informe o nome do prato.")

    if not categoria:
        raise ValueError("Informe a categoria do prato.")

    if preco < 0:
        raise ValueError("O preço não pode ser negativo.")

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            INSERT INTO produtos (
                nome,
                descricao,
                categoria,
                preco,
                disponivel,
                imagem
            )
            VALUES (?, ?, ?, ?, 1, ?)
        """, (nome, descricao, categoria, preco, imagem))

        conexao.commit()

        return cursor.lastrowid

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def editar_prato(prato_id, nome, descricao, categoria, preco, imagem=None):
    nome = nome.strip()
    descricao = descricao.strip() if descricao else ""
    categoria = categoria.strip()

    if not nome:
        raise ValueError("Informe o nome do prato.")

    if not categoria:
        raise ValueError("Informe a categoria do prato.")

    if preco < 0:
        raise ValueError("O preço não pode ser negativo.")

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            UPDATE produtos
            SET nome = ?,
                descricao = ?,
                categoria = ?,
                preco = ?,
                imagem = COALESCE(?, imagem)
            WHERE id = ?
        """, (nome, descricao, categoria, preco, imagem, prato_id))

        if cursor.rowcount == 0:
            raise ValueError("Prato não encontrado.")

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def alterar_disponibilidade(prato_id, disponivel):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            UPDATE produtos
            SET disponivel = ?
            WHERE id = ?
        """, (int(disponivel), prato_id))

        if cursor.rowcount == 0:
            raise ValueError("Prato não encontrado.")

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def remover_imagem_prato(prato_id):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            UPDATE produtos
            SET imagem = NULL
            WHERE id = ?
        """, (prato_id,))

        if cursor.rowcount == 0:
            raise ValueError("Prato não encontrado.")

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def excluir_prato(prato_id):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute(
            "DELETE FROM produtos WHERE id = ?",
            (prato_id,)
        )

        if cursor.rowcount == 0:
            raise ValueError("Prato não encontrado.")

        conexao.commit()

    except Exception as erro:
        conexao.rollback()

        if "FOREIGN KEY constraint failed" in str(erro):
            raise ValueError(
                "Este prato já está vinculado a um pedido ou a outra "
                "informação do sistema. Desative sua disponibilidade "
                "em vez de excluí-lo."
            ) from erro

        raise

    finally:
        conexao.close()
