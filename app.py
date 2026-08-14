from datetime import datetime
import sqlite3
import os
import re

from flask import Flask, render_template, request, redirect, session
from werkzeug.utils import secure_filename

app = Flask(__name__)

app.secret_key = "segredo_super_secreto"
app.config["UPLOAD_FOLDER"] = "static/uploads"

EXTENSOES_PERMITIDAS = {"png", "jpg", "jpeg"}

def arquivo_permitido(nome_arquivo):

    return "." in nome_arquivo and \
        nome_arquivo.rsplit(".", 1)[1].lower() in EXTENSOES_PERMITIDAS
def criar_banco():
    conexao = sqlite3.connect("database/bingolu.db", timeout=10)
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
    cursor.execute("""
CREATE TABLE IF NOT EXISTS pets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT NOT NULL,
    descricao TEXT,
    cidade TEXT,
    contato TEXT,
    usuario_id INTEGER,
    imagem TEXT,
    data_postagem TEXT,
    status TEXT
)
""")
    cursor.execute("""
CREATE TABLE IF NOT EXISTS avistamentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pet_id INTEGER,
    local TEXT,
    observacao TEXT,
    data_avistamento TEXT,
    nome_contato TEXT,
    telefone_contato TEXT,
    email_contato TEXT
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

        conexao = sqlite3.connect("database/bingolu.db", timeout=10)
        cursor = conexao.cursor()

        cursor.execute("""
        SELECT * FROM usuarios
        WHERE email = ? AND senha = ?
        """, (email, senha))

        usuario = cursor.fetchone()

        cursor.close()
        conexao.close()

        if usuario:

            session["usuario_id"] = usuario[0]
            session["usuario_nome"] = usuario[1]

            return redirect("/feed")

        else:
            return "Email ou senha incorretos"

    return render_template("login.html")


@app.route("/logout")
def logout():

    session.clear()

    return redirect("/")
    
@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form["nome"].strip()
        email = request.form["email"].strip()
        senha = request.form["senha"]
        telefone = request.form["telefone"].strip()
        cidade = request.form["cidade"].strip()

        # Validação do nome
        if len(nome) < 3:
            return "Nome deve possuir pelo menos 3 caracteres."

        # Validação do e-mail
        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            return "E-mail inválido."

        # Validação da senha
        if len(senha) < 6:
            return "A senha deve possuir pelo menos 6 caracteres."

        # Validação do telefone
        if not telefone.isdigit():
            return "Telefone deve conter apenas números."

        if len(telefone) < 10 or len(telefone) > 11:
            return "Telefone deve possuir 10 ou 11 dígitos."

        conexao = sqlite3.connect("database/bingolu.db", timeout=10)
        cursor = conexao.cursor()

        try:

            cursor.execute("""
            INSERT INTO usuarios (
                nome,
                email,
                senha,
                telefone,
                cidade
            )
            VALUES (?, ?, ?, ?, ?)
            """, (
                nome,
                email,
                senha,
                telefone,
                cidade
            ))

            conexao.commit()

        except sqlite3.IntegrityError:

            cursor.close()
            conexao.close()

            return "Este e-mail já está cadastrado."

        cursor.close()
        conexao.close()

        return redirect("/login")

    return render_template("cadastro.html")
@app.route("/feed")
def feed():

    if "usuario_id" not in session:
        return redirect("/login")

    cidade = request.args.get("cidade")

    conexao = sqlite3.connect(
        "database/bingolu.db",
        timeout=10
    )

    cursor = conexao.cursor()

    if cidade:

        cursor.execute("""
        SELECT
            id,
            nome,
            descricao,
            cidade,
            contato,
            imagem,
            data_postagem,
            status,
            usuario_id
        FROM pets
        WHERE status = 'Perdido'
        AND cidade LIKE ?
        ORDER BY id DESC
        """, (f"%{cidade}%",))

    else:

        cursor.execute("""
        SELECT
            id,
            nome,
            descricao,
            cidade,
            contato,
            imagem,
            data_postagem,
            status,
            usuario_id
        FROM pets
        WHERE status = 'Perdido'
        ORDER BY id DESC
        """)

    pets = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template(
        "feed.html",
        pets=pets,
        cidade=cidade
    )

@app.route("/encontrados")
def encontrados():

    conexao = sqlite3.connect(
        "database/bingolu.db",
        timeout=10
    )

    cursor = conexao.cursor()

    cursor.execute("""
    SELECT
        id,
        nome,
        descricao,
        cidade,
        contato,
        imagem,
        data_postagem,
        status
    FROM pets
    WHERE status = 'Encontrado'
    ORDER BY id DESC
    """)

    pets = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template(
        "encontrados.html",
        pets=pets
    )

@app.route("/limpar_encontrados")
def limpar_encontrados():

    conexao = sqlite3.connect(
        "database/bingolu.db",
        timeout=10
    )

    cursor = conexao.cursor()

    cursor.execute("""
    DELETE FROM pets
    WHERE status = 'Encontrado'
    """)

    conexao.commit()

    cursor.close()
    conexao.close()

    return "Pets encontrados removidos com sucesso."

@app.route("/teste_status")
def teste_status():

    conexao = sqlite3.connect(
        "database/bingolu.db",
        timeout=10
    )

    cursor = conexao.cursor()

    cursor.execute("""
    SELECT id, nome, status
    FROM pets
    """)

    pets = cursor.fetchall()

    cursor.close()
    conexao.close()

    return str(pets)

@app.route("/meus_posts")
def meus_posts():

    if "usuario_id" not in session:
        return redirect("/login")

    conexao = sqlite3.connect("database/bingolu.db", timeout=10)

    cursor = conexao.cursor()

    cursor.execute("""
    SELECT
        id,
        nome,
        descricao,
        cidade,
        contato,
        imagem,
        data_postagem, 
        status
    FROM pets
    WHERE usuario_id = ?
    AND status = 'Perdido'
    ORDER BY id DESC
    """, (session["usuario_id"],))

    pets = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template("meus_posts.html", pets=pets)

@app.route("/marcar_encontrado/<int:id_post>")
def marcar_encontrado(id_post):

    if "usuario_id" not in session:
        return redirect("/login")

    conexao = sqlite3.connect("database/bingolu.db", timeout=10)

    cursor = conexao.cursor()

    cursor.execute("""
    UPDATE pets
    SET status = 'Encontrado'
    WHERE id = ? AND usuario_id = ?
    """, (
        id_post,
        session["usuario_id"]
    ))

    conexao.commit()

    cursor.close()
    conexao.close()

    return redirect("/meus_posts")

@app.route("/editar_post/<int:id_post>", methods=["GET", "POST"])
def editar_post(id_post):

    if "usuario_id" not in session:
        return redirect("/login")

    conexao = sqlite3.connect("database/bingolu.db", timeout=10)

    cursor = conexao.cursor()

    if request.method == "POST":

        nome = request.form["nome"]
        descricao = request.form["descricao"]
        cidade = request.form["cidade"]
        contato = request.form["contato"]

        cursor.execute("""
        UPDATE pets
        SET
            nome = ?,
            descricao = ?,
            cidade = ?,
            contato = ?
        WHERE id = ?
        AND usuario_id = ?
        """, (
            nome,
            descricao,
            cidade,
            contato,
            id_post,
            session["usuario_id"]
        ))

        conexao.commit()

        cursor.close()
        conexao.close()

        return redirect("/meus_posts")

    cursor.execute("""
    SELECT
        id,
        nome,
        descricao,
        cidade,
        contato
    FROM pets
    WHERE id = ?
    AND usuario_id = ?
    """, (
        id_post,
        session["usuario_id"]
    ))

    pet = cursor.fetchone()

    cursor.close()
    conexao.close()

    return render_template("editar_post.html", pet=pet)

@app.route("/excluir_post/<int:id_post>")
def excluir_post(id_post):

    if "usuario_id" not in session:
        return redirect("/login")

    conexao = sqlite3.connect("database/bingolu.db", timeout=10)

    cursor = conexao.cursor()

    cursor.execute("""
    DELETE FROM pets
    WHERE id = ?
    AND usuario_id = ?
    """, (
        id_post,
        session["usuario_id"]
    ))

    conexao.commit()

    cursor.close()
    conexao.close()

    return redirect("/meus_posts")

@app.route("/post_pet", methods=["GET", "POST"])
def post_pet():

    if "usuario_id" not in session:
        return redirect("/login")

    if request.method == "POST":

        nome = request.form["nome"]
        descricao = request.form["descricao"]
        cidade = request.form["cidade"]
        contato = request.form["contato"]
        data_postagem = datetime.now().strftime("%d/%m/%Y")
        status = "Perdido"

        imagem = request.files["imagem"]
        if not arquivo_permitido(imagem.filename):
            return "Formato de imagem inválido"

        nome_arquivo = secure_filename(imagem.filename)

        caminho_imagem = os.path.join(
            app.config["UPLOAD_FOLDER"],
            nome_arquivo
        )

        imagem.save(caminho_imagem)

        conexao = sqlite3.connect("database/bingolu.db", timeout=10)
        cursor = conexao.cursor()

        cursor.execute("""
        INSERT INTO pets (
            nome,
            descricao,
            cidade,
            contato,
            usuario_id,
            imagem,
            data_postagem,
            status
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome,
            descricao,
            cidade,
            contato,
            session["usuario_id"],
            nome_arquivo,
            data_postagem,
            status
        ))

        conexao.commit()
        cursor.close()
        conexao.close()

        return redirect("/feed")
    return render_template("post_pet.html")


@app.route("/avistar/<int:id_pet>", methods=["GET", "POST"])
def avistar(id_pet):

    if request.method == "POST":

        local = request.form["local"]
        observacao = request.form["observacao"]

        nome_contato = request.form["nome_contato"]
        telefone_contato = request.form["telefone_contato"]
        email_contato = request.form["email_contato"]

        data_avistamento = datetime.now().strftime("%d/%m/%Y")

        conexao = sqlite3.connect(
            "database/bingolu.db",
            timeout=10
        )

        cursor = conexao.cursor()

        cursor.execute("""
        INSERT INTO avistamentos (
            pet_id,
            local,
            observacao,
            data_avistamento,
            nome_contato,
            telefone_contato,
            email_contato
        )
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            id_pet,
            local,
            observacao,
            data_avistamento,
            nome_contato,
            telefone_contato,
            email_contato
        ))

        conexao.commit()

        cursor.close()
        conexao.close()

        return redirect("/feed")

    return render_template(
        "avistar.html",
        id_pet=id_pet
    )


@app.route("/meus_avistamentos")
def meus_avistamentos():

    if "usuario_id" not in session:
        return redirect("/login")

    conexao = sqlite3.connect(
        "database/bingolu.db",
        timeout=10
    )

    cursor = conexao.cursor()

    cursor.execute("""
    SELECT        
        pets.nome,
        avistamentos.local,
        avistamentos.observacao,
        avistamentos.data_avistamento,
        avistamentos.nome_contato,
        avistamentos.telefone_contato,
        avistamentos.email_contato
    FROM avistamentos
    INNER JOIN pets
        ON avistamentos.pet_id = pets.id
    WHERE pets.usuario_id = ?
    ORDER BY avistamentos.id DESC
    """, (session["usuario_id"],))

    avistamentos = cursor.fetchall()

    cursor.close()
    conexao.close()

    return render_template(
    "meus_avistamentos.html",
    avistamentos=avistamentos
)
@app.route("/limpar_avistamentos")
def limpar_avistamentos():

    conexao = sqlite3.connect(
        "database/bingolu.db",
        timeout=10 
    )

    cursor = conexao.cursor()

    cursor.execute("""
    DELETE FROM avistamentos
    """)

    conexao.commit()

    cursor.close()
    conexao.close()

    return "Todos os avistamentos foram removidos"

@app.route("/reset_demo")
def reset_demo():

    conn = sqlite3.connect("database/bingolu.db")

    cursor = conn.cursor()

    cursor.execute("DELETE FROM avistamentos")
    cursor.execute("DELETE FROM pets")

    conn.commit()

    conn.close()

    return "Sistema resetado para a demonstração."

if __name__ == "__main__":
    app.run(debug=True)

    