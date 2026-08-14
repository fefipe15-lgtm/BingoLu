import sqlite3

conexao = sqlite3.connect("database/bingolu.db")

cursor = conexao.cursor()

cursor.execute("""
ALTER TABLE pets
ADD COLUMN status TEXT
""")

conexao.commit()

conexao.close()

print("Coluna status adicionada")