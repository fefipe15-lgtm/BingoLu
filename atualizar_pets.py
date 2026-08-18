import sqlite3

def adicionar_colunas_pets():
    # Conecta ao seu banco de dados
    conexao = sqlite3.connect("database/bingolu.db")
    cursor = conexao.cursor()

    print("Atualizando a tabela de pets...")

    # Adiciona a coluna latitude na tabela pets
    try:
        cursor.execute("ALTER TABLE pets ADD COLUMN latitude REAL DEFAULT 0.0;")
        print("-> Coluna 'latitude' adicionada com sucesso na tabela pets.")
    except sqlite3.OperationalError:
        print("-> Coluna 'latitude' já existe na tabela pets ou a tabela não foi encontrada.")

    # Adiciona a coluna longitude na tabela pets
    try:
        cursor.execute("ALTER TABLE pets ADD COLUMN longitude REAL DEFAULT 0.0;")
        print("-> Coluna 'longitude' adicionada com sucesso na tabela pets.")
    except sqlite3.OperationalError:
        print("-> Coluna 'longitude' já existe na tabela pets.")

    # Salva as alterações e fecha as conexões
    conexao.commit()
    cursor.close()
    conexao.close()
    print("Atualização concluída! Pode fechar este script e reiniciar o app.py.")

if __name__ == "__main__":
    adicionar_colunas_pets()

