import sqlite3
from flask import Flask, render_template, request, redirect

app = Flask(__name__)

def criar_banco():
    conexao = sqlite3.connect("database/bingolu.db")
    cursor = conexao.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        senha TEXT NOT NULL,
        telefone TEXT,
        cidade TEXT
    )
    """)

    conexao.commit()
    conexao.close()

# cria o banco ao iniciar
criar_banco()

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        senha = request.form["senha"]

        conexao = sqlite3.connect("database/bingolu.db")
        cursor = conexao.cursor()

        cursor.execute("""
        SELECT * FROM usuarios WHERE email = ? AND senha = ?
        """, (email, senha))

        usuario = cursor.fetchone()

        conexao.close()

        if usuario:
            return redirect("/feed")
        else:
            return "Email ou senha incorretos"
    return render_template("login.html")

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():
    if request.method == "POST":
        nome = request.form["nome"]
        email = request.form["email"]
        senha = request.form["senha"]
        telefone = request.form["telefone"]
        cidade = request.form["cidade"]

        conexao = sqlite3.connect("database/bingolu.db")
        cursor = conexao.cursor()

        cursor.execute("""
        INSERT INTO usuarios (nome, email, senha, telefone, cidade)
        VALUES (?, ?, ?, ?, ?)
        """, (nome, email, senha, telefone, cidade))

        conexao.commit()
        conexao.close()

        return redirect("/login")

    return render_template("cadastro.html")

@app.route("/feed")
def feed():
    return render_template("feed.html")

@app.route("/post_pet")
def post_pet():
    return render_template("post_pet.html")

if __name__ == "__main__":
    app.run(debug=True)