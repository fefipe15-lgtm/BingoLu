import sqlite3

conexao = sqlite3.connect("database/bingolu.db")

cursor = conexao.cursor()

cursor.execute("""
ALTER TABLE pets
ADD COLUMN data_postagem TEXT
""")

conexao.commit()

conexao.close()

print("Coluna adicionada com sucesso")