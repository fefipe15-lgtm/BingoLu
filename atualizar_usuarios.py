import sqlite3

conexao = sqlite3.connect("database/bingolu.db")
cursor = conexao.cursor()

print("Atualizando a tabela de usuários...")

try:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN latitude REAL DEFAULT 0.0;")
    print("-> Coluna 'latitude' adicionada.")
except sqlite3.OperationalError:
    print("-> Coluna 'latitude' já existe.")

try:
    cursor.execute("ALTER TABLE usuarios ADD COLUMN longitude REAL DEFAULT 0.0;")
    print("-> Coluna 'longitude' adicionada.")
except sqlite3.OperationalError:
    print("-> Coluna 'longitude' já existe.")

conexao.commit()
cursor.close()
conexao.close()
print("Pronto! O erro foi corrigido.")
