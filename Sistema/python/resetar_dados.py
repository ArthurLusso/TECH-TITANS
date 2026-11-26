
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
print("Esta operação apagará:")
print("- Todos os pedidos e seus itens")
print("- Todas as entregas")
print("- Todos os cancelamentos")
print("- Todos os pratos do cardápio")
print("- Todos os vínculos entre pratos e ingredientes")
print()
print("O estoque e seus históricos serão preservados.")
print()

confirmacao = input(
    "Digite APAGAR para confirmar a limpeza: "
)

if confirmacao != "APAGAR":
    print("Operação cancelada. Nenhum dado foi removido.")
    raise SystemExit


conexao = conectar()

try:
    conexao.execute("PRAGMA foreign_keys = ON")

    with conexao:

        tabelas = [
            "cancelamentos",
            "entregas",
            "itens_pedido",
            "produto_ingredientes",
            "pedidos",
            "produtos"
        ]

        for tabela in tabelas:
            conexao.execute(f"DELETE FROM {tabela}")

        conexao.execute("""
            DELETE FROM sqlite_sequence
            WHERE name IN (
                'cancelamentos',
                'entregas',
                'itens_pedido',
                'pedidos',
                'produtos'
            )
        """)

    print()
    print("Sistema limpo com sucesso!")
    print("Os IDs dos registros também foram reiniciados.")
    print("Estoque preservado.")
    print("Backup disponível em:", BACKUP.name)

except Exception as erro:
    print("Erro ao limpar o banco:", erro)
    raise

finally:
    conexao.close()
