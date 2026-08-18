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
    
import re
import requests

@app.route("/cadastro", methods=["GET", "POST"])
def cadastro():

    if request.method == "POST":

        nome = request.form["nome"].strip()
        email = request.form["email"].strip()
        senha = request.form["senha"]
        
        # Recebe os dados formatados do HTML
        telefone_formatado = request.form["telefone"].strip()
        cep_formatado = request.form["cep"].strip()

        # Remove parênteses, traços e espaços para realizar as validações numéricas nativas do seu código
        telefone_limpo = re.sub(r"\D", "", telefone_formatado)
        cep_limpo = re.sub(r"\D", "", cep_formatado)

        # --- SUAS VALIDAÇÕES ADAPTADAS PARA O NOVO FORMATO ---
        if len(nome) < 3:
            return "Nome deve possuir pelo menos 3 caracteres."

        if not re.match(r"^[^@]+@[^@]+\.[^@]+$", email):
            return "E-mail inválido."

        if len(senha) < 6:
            return "A senha deve possuir pelo menos 6 caracteres."

        # Valida usando a string limpa (apenas números)
        if not telefone_limpo.isdigit():
            return "Telefone deve conter apenas números."

        if len(telefone_limpo) < 10 or len(telefone_limpo) > 11:
            return "Telefone deve possuir 10 ou 11 dígitos."
            
        if len(cep_limpo) != 8:
            return "CEP inválido. Deve conter exatamente 8 números."

        cidade = request.form["cidade"].strip()

        # --- LÓGICA DE GEOLOCALIZAÇÃO (Usa o CEP limpo para a API) ---
        latitude = 0.0
        longitude = 0.0
        try:
            response_cep = requests.get(f"https://viacep.com.br{cep_limpo}/json/", timeout=5).json()
            if "erro" not in response_cep:
                rua = response_cep.get("logradouro", "")
                bairro = response_cep.get("bairro", "")
                cidade_cep = response_cep.get("localidade", "")
                
                endereco_busca = f"{rua}, {bairro}, {cidade_cep}, Brazil"
                headers = {'User-Agent': 'BingoLuPetFinderApp/1.0'}
                response_geo = requests.get(
                    f"https://openstreetmap.org{endereco_busca}", 
                    headers=headers, 
                    timeout=5
                ).json()
                
                if response_geo:
                    latitude = float(response_geo["lat"])
                    longitude = float(response_geo["lon"])
        except Exception as e:
            print(f"Erro na geolocalização: {e}")

        # --- SALVANDO NO BANCO ---
        conexao = sqlite3.connect("database/bingolu.db", timeout=10)
        cursor = conexao.cursor()

        try:
            cursor.execute("""
            INSERT INTO usuarios (nome, email, senha, telefone, cidade, latitude, longitude)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                nome,
                email,
                senha,
                telefone_formatado, # Salvamos formatado (XX) XXXXX-XXXX para ficar bonito nos cards
                cidade,
                latitude,
                longitude
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


import math
from datetime import datetime, timedelta

def calcular_distancia(lat1, lon1, lat2, lon2):
    """ Calcula a distância em KM entre duas coordenadas usando Haversine """
    if lat1 is None or lon1 is None or lat2 is None or lon2 is None:
        return float('inf')
    if lat1 == 0.0 or lon1 == 0.0 or lat2 == 0.0 or lon2 == 0.0:
        return float('inf')
        
    raio_terra = 6371.0
    lat1, lon1, lat2, lon2 = map(math.radians, [lat1, lon1, lat2, lon2])
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = math.sin(dlat / 2)**2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return raio_terra * c

@app.route("/feed")
def feed():
    if "usuario_id" not in session:
        return redirect("/login")

    cidade = request.args.get("cidade")
    especie = request.args.get("especie")
    
    # Novo parâmetro na URL para saber se o usuário clicou na aba 'alertas'
    aba = request.args.get("aba", "geral") 

    conexao = sqlite3.connect("database/bingolu.db", timeout=10)
    cursor = conexao.cursor()

    # 1. Pega a localização do usuário logado
    cursor.execute("SELECT latitude, longitude FROM usuarios WHERE id = ?", (session["usuario_id"],))
    usuario_geo = cursor.fetchone()
    user_lat = usuario_geo[0] if (usuario_geo and usuario_geo[0]) else 0.0
    user_lng = usuario_geo[1] if (usuario_geo and usuario_geo[1]) else 0.0

    # 2. Busca todos os pets perdidos do banco
    query = """
    SELECT
        id, nome, descricao, cidade, contato,
        imagem, data_postagem, status, usuario_id,
        especie, sexo, porte, latitude, longitude
    FROM pets
    WHERE status = 'Perdido'
    """
    parametros = []

    # Se estiver na aba GERAL, aplica os filtros visuais de Cidade e Espécie escolhidos
    if aba == "geral":
        if cidade:
            query += " AND cidade LIKE ?"
            parametros.append(f"%{cidade}%")
        if especie:
            query += " AND especie = ?"
            parametros.append(especie)

    query += " ORDER BY id DESC"
    cursor.execute(query, tuple(parametros))
    todos_os_pets = cursor.fetchall()
    cursor.close()
    conexao.close()

    pets_filtrados = []
    
    # 3. Processamento Geográfico dos Filtros
    for pet in todos_os_pets:
        pet_lat = pet[12]
        pet_lng = pet[13]
        distancia = calcular_distancia(user_lat, user_lng, pet_lat, pet_lng)
        
        pet_lista = list(pet)
        pet_lista.append(round(distancia, 1) if distancia != float('inf') else None) # pet[14] = Distância

        if aba == "alertas":
            # REGRA DE ALERTAS DE AVISTAMENTO: 
            # Raio super curto (2 km) para QUALQUER espécie, focado na vizinhança imediata
            if distancia <= 2.0:
                pets_filtrados.append(pet_lista)
        else:
            # REGRA DO FEED REGIONAL PADRÃO: 
            # Raio de 5 km (Mostra também os que não têm coordenada para testes antigos não sumirem)
            if distancia <= 5.0 or pet_lat == 0.0 or pet_lat is None or user_lat == 0.0:
                pets_filtrados.append(pet_lista)

    # 4. Ordenação por Proximidade
    pets_filtrados.sort(key=lambda x: x[14] if x[14] is not None else 9999)

    return render_template(
        "feed.html",
        pets=pets_filtrados,
        cidade=cidade,
        especie_ativa=especie,
        aba_ativa=aba
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

        # NOVAS ADIÇÕES: Coleta os novos campos do formulário
        especie = request.form.get("especie")
        sexo = request.form.get("sexo")
        
        # Só captura o porte se for Canino, senão grava como None (vazio) no SQLite
        porte = request.form.get("porte") if especie == "Canino" else None

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

        # INSERT atualizado para incluir especie, sexo e porte
        cursor.execute("""
        INSERT INTO pets (
            nome,
            descricao,
            cidade,
            contato,
            usuario_id,
            imagem,
            data_postagem,
            status,
            especie,
            sexo,
            porte
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            nome,
            descricao,
            cidade,
            contato,
            session["usuario_id"],
            nome_arquivo,
            data_postagem,
            status,
            especie,   # Novo parâmetro
            sexo,      # Novo parâmetro
            porte      # Novo parâmetro
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


import re

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

    avistamentos_brutos = cursor.fetchall()

    cursor.close()
    conexao.close()

    # Formata os números de telefone vindos do banco antes de enviar para o HTML
    avistamentos_formatados = []
    for aviso in avistamentos_brutos:
        aviso_lista = list(aviso)
        
        # Pega o telefone na posição 5 da consulta SQL
        telefone_bruto = str(aviso_lista[5]).strip()
        
        # Remove tudo o que não for número (limpeza idêntica à do cadastro)
        telefone_limpo = re.sub(r"\D", "", telefone_bruto)
        
        # Aplica a máscara padrão brasileira baseada na quantidade de dígitos
        if len(telefone_limpo) == 11:
            telefone_formatado = f"({telefone_limpo[:2]}) {telefone_limpo[2:7]}-{telefone_limpo[7:]}"
        elif len(telefone_limpo) == 10:
            telefone_formatado = f"({telefone_limpo[:2]}) {telefone_limpo[2:6]}-{telefone_limpo[6:]}"
        else:
            # Se já veio formatado corretamente do banco, mantém o formato original
            telefone_formatado = telefone_bruto

        # Substitui o telefone original pelo número formatado na lista
        aviso_lista[5] = telefone_formatado
        avistamentos_formatados.append(aviso_lista)

    return render_template(
        "meus_avistamentos.html",
        avistamentos=avistamentos_formatados
    )

@app.route("/encontrados")
def encontrados():

    if "usuario_id" not in session:
        return redirect("/login")

    conexao = sqlite3.connect(
        "database/bingolu.db",
        timeout=10
    )

    cursor = conexao.cursor()

    # SELECT estruturado exatamente igual ao do feed, mas filtrando por 'Encontrado'
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
        usuario_id,
        especie,
        sexo,
        porte
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

    