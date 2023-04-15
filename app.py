# Importar os módulos Flask, render_template, request, session e redirect do Flask e o módulo sqlite3
from flask import Flask, render_template, request, session, redirect
import sqlite3

# Criar uma instância do Flask e definir a variável "app" para isso
app = Flask(__name__)

# Definir a chave secreta do aplicativo como "mysecretkey"
# Isso é usado para assinar sessões e proteger os dados de sessão
app.secret_key = "mysecretkey"

# Conectar-se ao banco de dados SQLite "database.db"
conn = sqlite3.connect("database.db")

# Criar um cursor para executar comandos SQL no banco de dados
c = conn.cursor()

# Criar uma tabela "users" se ela ainda não existir, com os campos "id", "name", "email", "password"
c.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, password TEXT)")

# Salvar as alterações no banco de dados
conn.commit()
# Fechar a conexão com o banco de dados
conn.close()

# Definir uma rota para a página inicial ("/") e retornar a página HTML "index.html" 
# Através da função render_template
@app.route("/")
def index():
    return render_template("index.html")

# Definir uma rota para a página de cadastro ("/signup") com os métodos permitidos GET e POST
@app.route("/signup", methods=["GET", "POST"])
def signup():
    # Se o método for POST
    if request.method == "POST":
        # Pegar os dados do formulário enviado pelo usuário
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        # Conectar-se ao banco de dados SQLite "database.db"
        conn = sqlite3.connect("database.db")
        # Criar um cursor para executar comandos SQL no banco de dados
        c = conn.cursor()
        # Adicionar os dados do usuário à tabela "users" do banco de dados SQLite
        c.execute("INSERT INTO users (name, email, password) VALUES (?, ?, ?)", (name, email, password))
        # Salvar as alterações no banco de dados
        conn.commit()
        # Fechar a conexão com o banco de dados
        conn.close()
        # Redirecionar o usuário para a página de login ("/login")
        return redirect("/login")
    # Se o método for GET
    return render_template("signup.html")

# Definir uma rota para a página de login ("/login") com os métodos permitidos GET e POST
@app.route("/login", methods=["GET", "POST"])
def login():
    # Se o método for POST
    if request.method == "POST":
        # Pegar os dados do formulário enviado pelo usuário
        email = request.form["email"]
        password = request.form["password"]

        # Conectar-se ao banco de dados SQLite "database.db"
        conn = sqlite3.connect("database.db")

        # Criar um cursor para executar comandos SQL no banco de dados
        c = conn.cursor()

        # Executar uma consulta SQL na tabela "users" do banco de dados SQLite
        # para encontrar um usuário com o email e a senha fornecidos
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))

        # Obter o resultado da consulta SQL
        user = c.fetchone()

        # Fechar a conexão com o banco de dados
        conn.close()

        # Se um usuário for encontrado com o email e a senha fornecidos
        if user:
            # Definir a variável de sessão "user" para o usuário encontrado
            session["user"] = user

            # Redirecionar o usuário para a página do painel ("/dashboard")
            return redirect("/dashboard")
        # Se um usuário não for encontrado com o email e a senha fornecidos
        else:
            # Definir uma mensagem de erro
            error = "Invalid email or password"

            # Retornar a página HTML "login.html" com a mensagem de erro
            return render_template("login.html", error=error)

    # Se o método for GET
    return render_template("login.html")


# Definir uma rota para a página do painel ("/dashboard")
@app.route("/dashboard")
def dashboard():
    # Obter o usuário atual da variável de sessão "user"
    user = session.get("user")

    # Se houver um usuário na variável de sessão "user"
    if user:
        # Retornar a página HTML "dashboard.html" com o usuário atual
        return render_template("dashboard.html", user=user)
    # Se não houver um usuário na variável de sessão "user"
    else:
        # Redirecionar o usuário para a página de login ("/login")
        return redirect("/login")


# Definir uma rota para a página de logout ("/logout")
@app.route("/logout")
def logout():
    # Remover a variável de sessão "user"
    session.pop("user", None)

    # Redirecionar o usuário para a página de login ("/login")
    return redirect("/login")


# Executar o aplicativo Flask quando o script for executado diretamente
if __name__ == "__main__":
    # Iniciar o aplicativo Flask em modo de depuração
    app.run(debug=True)
