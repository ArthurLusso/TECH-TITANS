
from pathlib import Path
from datetime import datetime
from shutil import copy2

from data_base.conexao import conectar


BASE_DIR = Path(__file__).resolve().parent
BANCO = BASE_DIR / "data_base" / "tacoloko.db"

if not BANCO.exists():
    raise FileNotFoundError("Banco de dados não encontrado.")

nome_backup = (
    f"tacoloko_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db"
)

BACKUP = BASE_DIR / "data_base" / nome_backup

copy2(BANCO, BACKUP)

print("Backup criado:", BACKUP.name)
print()
print("Serão apagados:")
print("- Todos os pedidos e seus itens")
print("- Todas as entregas")
print("- Todos os cancelamentos")
print("- Todos os pratos do cardápio")
print("- Todas as fichas técnicas")
print("- Todos os registros de baixa de estoque dos pedidos")
print()
print("O estoque e seu histórico serão preservados.")
print()

confirmacao = input(
    "Digite APAGAR para confirmar a limpeza: "
)

if confirmacao != "APAGAR":
    print("Operação cancelada. Nenhum dado foi removido.")
    raise SystemExit


conexao = conectar()

try:
    tabelas = [
        "cancelamentos",
        "baixas_estoque_pedido",
        "entregas",
        "itens_pedido",
        "produto_ingredientes",
        "produto_variacoes",
        "pedidos",
        "produtos"
    ]

    existentes = {
        linha[0]
        for linha in conexao.execute("""
            SELECT name
            FROM sqlite_master
            WHERE type = 'table'
        """).fetchall()
    }

    with conexao:

        for tabela in tabelas:
            if tabela in existentes:
                conexao.execute(
                    f'DELETE FROM "{tabela}"'
                )

        conexao.execute("""
            DELETE FROM sqlite_sequence
            WHERE name IN (
                'cancelamentos',
                'entregas',
                'itens_pedido',
                'pedidos',
                'produtos',
                'produto_variacoes'
            )
        """)

    print()
    print("Sistema limpo com sucesso!")
    print("IDs reiniciados.")
    print("Estoque preservado.")
    print("Backup disponível:", BACKUP.name)

except Exception as erro:
    print("Erro ao limpar o banco:", erro)
    raise

finally:
    conexao.close()
