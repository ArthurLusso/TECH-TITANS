
from data_base.conexao import conectar


UNIDADES = {
    "kg": ("massa", 1000),
    "g": ("massa", 1),
    "L": ("volume", 1000),
    "ml": ("volume", 1),
    "unidade": ("unidade", 1),
    "pacote": ("pacote", 1)
}


def unidades_compativeis(unidade_estoque):
    if unidade_estoque not in UNIDADES:
        raise ValueError("Unidade de estoque não reconhecida.")

    grupo = UNIDADES[unidade_estoque][0]

    return [
        unidade
        for unidade, dados in UNIDADES.items()
        if dados[0] == grupo
    ]


def converter_quantidade(quantidade, unidade_origem, unidade_destino):
    if unidade_origem not in UNIDADES:
        raise ValueError("Unidade da receita não reconhecida.")

    if unidade_destino not in UNIDADES:
        raise ValueError("Unidade do estoque não reconhecida.")

    grupo_origem, fator_origem = UNIDADES[unidade_origem]
    grupo_destino, fator_destino = UNIDADES[unidade_destino]

    if grupo_origem != grupo_destino:
        raise ValueError(
            f"Não é possível converter {unidade_origem} para {unidade_destino}."
        )

    quantidade_base = float(quantidade) * fator_origem

    return round(quantidade_base / fator_destino, 6)


def listar_variacoes_estoque():
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                v.id,
                i.nome AS ingrediente,
                i.categoria,
                v.nome AS variacao,
                v.quantidade,
                v.unidade,
                v.estoque_minimo
            FROM variacoes_ingrediente v
            INNER JOIN ingredientes i
                ON i.id = v.ingrediente_id
            ORDER BY i.nome, v.nome
        """)

        return cursor.fetchall()

    finally:
        conexao.close()


def listar_receita(produto_id):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT
                pv.id AS receita_id,
                pv.variacao_id,
                pv.quantidade_necessaria,
                pv.unidade AS unidade_receita,
                i.nome AS ingrediente,
                i.categoria,
                v.nome AS variacao,
                v.quantidade AS estoque_atual,
                v.unidade AS unidade_estoque
            FROM produto_variacoes pv
            INNER JOIN variacoes_ingrediente v
                ON v.id = pv.variacao_id
            INNER JOIN ingredientes i
                ON i.id = v.ingrediente_id
            WHERE pv.produto_id = ?
            ORDER BY i.nome, v.nome
        """, (produto_id,))

        return cursor.fetchall()

    finally:
        conexao.close()


def salvar_item_receita(
    produto_id,
    variacao_id,
    quantidade_necessaria,
    unidade
):
    quantidade_necessaria = float(quantidade_necessaria)

    if quantidade_necessaria <= 0:
        raise ValueError("A quantidade necessária deve ser maior que zero.")

    if unidade not in UNIDADES:
        raise ValueError("Unidade da receita inválida.")

    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            SELECT id
            FROM produtos
            WHERE id = ?
        """, (produto_id,))

        if cursor.fetchone() is None:
            raise ValueError("Prato não encontrado.")

        cursor.execute("""
            SELECT unidade
            FROM variacoes_ingrediente
            WHERE id = ?
        """, (variacao_id,))

        variacao = cursor.fetchone()

        if variacao is None:
            raise ValueError("Variação do estoque não encontrada.")

        unidade_estoque = variacao["unidade"]

        converter_quantidade(
            quantidade_necessaria,
            unidade,
            unidade_estoque
        )

        cursor.execute("""
            INSERT INTO produto_variacoes (
                produto_id,
                variacao_id,
                quantidade_necessaria,
                unidade
            )
            VALUES (?, ?, ?, ?)
            ON CONFLICT(produto_id, variacao_id)
            DO UPDATE SET
                quantidade_necessaria = excluded.quantidade_necessaria,
                unidade = excluded.unidade
        """, (
            produto_id,
            variacao_id,
            quantidade_necessaria,
            unidade
        ))

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()


def remover_item_receita(receita_id):
    conexao = conectar()

    try:
        cursor = conexao.cursor()

        cursor.execute("""
            DELETE FROM produto_variacoes
            WHERE id = ?
        """, (receita_id,))

        if cursor.rowcount == 0:
            raise ValueError("Ingrediente da receita não encontrado.")

        conexao.commit()

    except Exception:
        conexao.rollback()
        raise

    finally:
        conexao.close()
