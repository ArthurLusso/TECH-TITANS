
from data_base.conexao import conectar


def adicionar_colunas(conexao, tabela, colunas):
    resultado = conexao.execute(
        f'PRAGMA table_info("{tabela}")'
    ).fetchall()

    existentes = {linha[1] for linha in resultado}

    for nome, definicao in colunas.items():
        if nome not in existentes:
            conexao.execute(
                f'ALTER TABLE "{tabela}" ADD COLUMN "{nome}" {definicao}'
            )


def atualizar_integracoes():
    conexao = conectar()

    try:
        adicionar_colunas(
            conexao,
            "pedidos",
            {
                "subtotal": "REAL NOT NULL DEFAULT 0",
                "taxa_entrega": "REAL NOT NULL DEFAULT 0",
                "forma_pagamento": "TEXT",
                "status_pagamento": "TEXT NOT NULL DEFAULT 'Pendente'",
                "data_pagamento": "TEXT"
            }
        )

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS produto_variacoes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                produto_id INTEGER NOT NULL,
                variacao_id INTEGER NOT NULL,
                quantidade_necessaria REAL NOT NULL,
                unidade TEXT NOT NULL,

                FOREIGN KEY (produto_id)
                    REFERENCES produtos(id),

                FOREIGN KEY (variacao_id)
                    REFERENCES variacoes_ingrediente(id),

                UNIQUE (produto_id, variacao_id),

                CHECK (quantidade_necessaria > 0)
            )
        """)

        conexao.execute("""
            CREATE TABLE IF NOT EXISTS baixas_estoque_pedido (
                pedido_id INTEGER PRIMARY KEY,
                data_baixa TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (pedido_id)
                    REFERENCES pedidos(id)
            )
        """)

        conexao.execute("""
            UPDATE pedidos
            SET subtotal = COALESCE(
                (
                    SELECT SUM(ip.subtotal)
                    FROM itens_pedido ip
                    WHERE ip.pedido_id = pedidos.id
                ),
                MAX(total - taxa_entrega, 0)
            )
            WHERE subtotal = 0
        """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS idx_produto_variacoes_produto
            ON produto_variacoes(produto_id)
        """)

        conexao.execute("""
            CREATE INDEX IF NOT EXISTS idx_produto_variacoes_variacao
            ON produto_variacoes(variacao_id)
        """)

        conexao.commit()

        print("Atualização das integrações concluída com sucesso!")

    except Exception as erro:
        conexao.rollback()
        print(f"Erro ao atualizar as integrações: {erro}")
        raise

    finally:
        conexao.close()


if __name__ == "__main__":
    atualizar_integracoes()
