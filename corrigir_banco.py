import sqlite3

def adicionar_colunas():
    # Conecta ao seu banco de dados
    conexao = sqlite3.connect("database/bingolu.db")
    cursor = conexao.cursor()

    print("Iniciando a atualização do banco de dados...")

    # Adiciona a coluna especie
    try:
        cursor.execute("ALTER TABLE pets ADD COLUMN especie TEXT;")
        print("-> Coluna 'especie' adicionada com sucesso.")
    except sqlite3.OperationalError:
        print("-> Coluna 'especie' já existe ou a tabela não foi encontrada.")

    # Adiciona a coluna sexo
    try:
        cursor.execute("ALTER TABLE pets ADD COLUMN sexo TEXT;")
        print("-> Coluna 'sexo' adicionada com sucesso.")
    except sqlite3.OperationalError:
        print("-> Coluna 'sexo' já existe.")

    # Adiciona a coluna porte
    try:
        cursor.execute("ALTER TABLE pets ADD COLUMN porte TEXT;")
        print("-> Coluna 'porte' adicionada com sucesso.")
    except sqlite3.OperationalError:
        print("-> Coluna 'porte' já existe.")

    # Salva as alterações e fecha as conexões
    conexao.commit()
    cursor.close()
    conexao.close()
    print("Atualização concluída! Você já pode fechar este script e rodar o app.py.")

if __name__ == "__main__":
    adicionar_colunas()
