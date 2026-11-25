
from data_base.conexao import conectar


def adicionar_colunas(conexao, tabela, colunas):
    resultado = conexao.execute(
        f"PRAGMA table_info({tabela})"
    ).fetchall()

    colunas_existentes = {linha[1] for linha in resultado}

    for nome, definicao in colunas.items():
        if nome not in colunas_existentes:
            conexao.execute(
                f'ALTER TABLE "{tabela}" ADD COLUMN "{nome}" {definicao}'
            )


def criar_tabelas():

    conexao = conectar()

    try:

        conexao.executescript("""

        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            descricao TEXT,
            categoria TEXT,
            preco REAL NOT NULL CHECK (preco >= 0),
            disponivel INTEGER NOT NULL DEFAULT 1,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS ingredientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            categoria TEXT NOT NULL,
            quantidade REAL NOT NULL DEFAULT 0,
            unidade TEXT NOT NULL DEFAULT 'kg',
            estoque_minimo REAL NOT NULL DEFAULT 0,
            atualizado_em TEXT DEFAULT CURRENT_TIMESTAMP,
            CHECK (quantidade >= 0),
            CHECK (estoque_minimo >= 0),
            CHECK (categoria IN (
                'Massas',
                'Congelados',
                'Verduras',
                'Bebidas'
            ))
        );

        CREATE TABLE IF NOT EXISTS produto_ingredientes (
            produto_id INTEGER NOT NULL,
            ingrediente_id INTEGER NOT NULL,
            quantidade_necessaria REAL NOT NULL,
            unidade TEXT NOT NULL,
            PRIMARY KEY (produto_id, ingrediente_id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id),
            FOREIGN KEY (ingrediente_id) REFERENCES ingredientes(id),
            CHECK (quantidade_necessaria > 0)
        );

        CREATE TABLE IF NOT EXISTS pedidos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_nome TEXT NOT NULL,
            telefone TEXT,
            rua TEXT,
            numero TEXT,
            bairro TEXT,
            cidade TEXT,
            complemento TEXT,
            data_pedido TEXT DEFAULT CURRENT_TIMESTAMP,
            data_agendada TEXT,
            total REAL NOT NULL DEFAULT 0,
            status TEXT NOT NULL DEFAULT 'Agendado'
        );

        CREATE TABLE IF NOT EXISTS itens_pedido (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL,
            produto_id INTEGER NOT NULL,
            produto_nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL,
            preco_unitario REAL NOT NULL,
            subtotal REAL NOT NULL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
            FOREIGN KEY (produto_id) REFERENCES produtos(id),
            CHECK (quantidade > 0),
            CHECK (preco_unitario >= 0),
            CHECK (subtotal >= 0)
        );

        CREATE TABLE IF NOT EXISTS entregas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL UNIQUE,
            entregador TEXT,
            status TEXT NOT NULL DEFAULT 'Aguardando',
            data_saida TEXT,
            previsao_entrega TEXT,
            data_entrega TEXT,
            latitude REAL,
            longitude REAL,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id)
        );

        CREATE TABLE IF NOT EXISTS cancelamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            pedido_id INTEGER NOT NULL UNIQUE,
            motivo TEXT NOT NULL,
            status_reembolso TEXT NOT NULL DEFAULT 'Pendente',
            valor_reembolso REAL NOT NULL DEFAULT 0,
            valor_prejuizo REAL NOT NULL DEFAULT 0,
            data_cancelamento TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pedido_id) REFERENCES pedidos(id),
            CHECK (valor_reembolso >= 0),
            CHECK (valor_prejuizo >= 0)
        );

        CREATE TABLE IF NOT EXISTS movimentacoes_estoque (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            ingrediente_id INTEGER NOT NULL,
            tipo TEXT NOT NULL,
            quantidade REAL NOT NULL,
            motivo TEXT,
            data_movimentacao TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (ingrediente_id) REFERENCES ingredientes(id),
            CHECK (quantidade > 0),
            CHECK (tipo IN ('Entrada', 'Saída', 'Ajuste'))
        );

        """)

        migracoes = {
            "produtos": {
                "disponivel": "INTEGER NOT NULL DEFAULT 1",
                "criado_em": "TEXT"
            },
            "pedidos": {
                "rua": "TEXT",
                "numero": "TEXT",
                "bairro": "TEXT",
                "cidade": "TEXT",
                "complemento": "TEXT",
                "data_agendada": "TEXT"
            },
            "itens_pedido": {
                "produto_nome": "TEXT"
            },
            "entregas": {
                "previsao_entrega": "TEXT",
                "latitude": "REAL",
                "longitude": "REAL"
            },
            "cancelamentos": {
                "status_reembolso": "TEXT NOT NULL DEFAULT 'Pendente'",
                "valor_reembolso": "REAL NOT NULL DEFAULT 0",
                "valor_prejuizo": "REAL NOT NULL DEFAULT 0"
            }
        }

        for tabela, colunas in migracoes.items():
            adicionar_colunas(conexao, tabela, colunas)

        conexao.executescript("""

        CREATE INDEX IF NOT EXISTS idx_pedidos_status
        ON pedidos(status);

        CREATE INDEX IF NOT EXISTS idx_pedidos_data
        ON pedidos(data_pedido);

        CREATE INDEX IF NOT EXISTS idx_pedidos_bairro
        ON pedidos(bairro);

        CREATE INDEX IF NOT EXISTS idx_ingredientes_categoria
        ON ingredientes(categoria);

        """)

        conexao.commit()

        print("Banco de dados do TacoLoko preparado com sucesso!")

    except Exception as erro:
        conexao.rollback()
        print(f"Erro ao preparar o banco de dados: {erro}")
        raise

    finally:
        conexao.close()


if __name__ == "__main__":
    criar_tabelas()
