from flask import Flask, render_template, request, session, redirect, url_for, make_response
import matplotlib.pyplot as plt
import io
import base64
import sqlite3
import numpy as np

app = Flask(__name__)
app.secret_key = "mysecretkey"

conn = sqlite3.connect("users.db")
c = conn.cursor()
c.execute("CREATE TABLE IF NOT EXISTS login (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, email TEXT, password TEXT)")
conn.commit()
conn.close()


conn = sqlite3.connect('movimentaçoes.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS extrato
                  (banco TEXT, data_movimento TEXT, nome_movimento TEXT, tipo_movimento TEXT, valor_despesa REAL, valor_receita REAL, saldo REAL)''')
conn.commit()
conn.close()

conn = sqlite3.connect('orçamento.db')
cursor = conn.cursor()
cursor.execute('''CREATE TABLE IF NOT EXISTS previsao
                  (data_prevista TEXT, nome_movimento TEXT, tipo_movimento TEXT, orçamento_previsto REAL)''')
conn.commit()
conn.close()


@app.route("/")
def index():
    return render_template("index.html")

@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        password = request.form["password"]
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("INSERT INTO login (name, email, password) VALUES (?, ?, ?)", (name, email, password))
        conn.commit()
        conn.close()
        return redirect("/login")
    return render_template("signup.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        conn = sqlite3.connect("users.db")
        c = conn.cursor()
        c.execute("SELECT * FROM login WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()
        if user:
            session["user"] = user
            return redirect("/dashboard")
        else:
            error = "Invalid email or password"
            return render_template("login.html", error=error)
    return render_template("login.html")

@app.route("/dashboard", methods=['GET', 'POST'])
def dashboard():
    user = session.get("user")
    if not user:
        return redirect("/login")

    if request.method == 'POST':
        if 'informar_saldo' in request.form:
            banco = request.form['banco']
            data_movimento = request.form['data_movimento']
            saldo: float = request.form['saldo']
            conn = sqlite3.connect('movimentaçoes.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO extrato (banco, data_movimento, saldo) VALUES (?, ?, ?)", (banco, data_movimento, saldo))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))

        elif 'cadastrar_receita' in request.form:
            banco = request.form['banco']
            data_movimento = request.form['data_movimento']
            nome_movimento = request.form['nome_movimento']
            tipo_movimento = request.form['tipo_movimento']
            valor_receita: float = request.form['valor_receita'].replace(',', '.')
            conn = sqlite3.connect('movimentaçoes.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO extrato (banco, data_movimento, nome_movimento, tipo_movimento, valor_receita) VALUES (?, ?, ?, ?, ?)", (banco, data_movimento, nome_movimento, tipo_movimento, valor_receita))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))

        elif 'cadastrar_despesa' in request.form:
            banco = request.form['banco']
            data_movimento = request.form['data_movimento']
            nome_movimento = request.form['nome_movimento']
            tipo_movimento = request.form['tipo_movimento']
            valor_despesa: float = request.form['valor_despesa'].replace(',', '.')
            conn = sqlite3.connect('movimentaçoes.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO extrato (banco, data_movimento, nome_movimento, tipo_movimento, valor_despesa) VALUES (?, ?, ?, ?, ?)", (banco, data_movimento, nome_movimento, tipo_movimento, valor_despesa))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))

        elif 'cadastrar_orçamento' in request.form:
            data_prevista = request.form['data_prevista']
            nome_movimento = request.form['nome_movimento']
            tipo_movimento = request.form['tipo_movimento']
            orçamento_previsto: float = request.form['orçamento_previsto'].replace(',', '.')
            conn = sqlite3.connect('orçamento.db')
            cursor = conn.cursor()
            cursor.execute("INSERT INTO previsao (data_prevista, nome_movimento, tipo_movimento, orçamento_previsto) VALUES (?, ?, ?, ?)", (data_prevista, nome_movimento, tipo_movimento, orçamento_previsto))
            conn.commit()
            conn.close()
            return redirect(url_for('dashboard'))


    # Cálculo do saldo atual
    conn = sqlite3.connect('movimentaçoes.db')
    cursor = conn.cursor()

    cursor.execute("SELECT COALESCE(SUM(REPLACE(saldo, ',', '.')), 0) FROM extrato")
    soma_saldo = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(REPLACE(valor_receita, ',', '.')), 0) FROM extrato")
    receitas = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(REPLACE(valor_despesa, ',', '.')), 0) FROM extrato")
    despesas = cursor.fetchone()[0]

    soma_saldo_receitas = soma_saldo + receitas
    saldo_atual = soma_saldo_receitas - despesas

    conn.close()

    saldo_atual_formatado = "{:.2f}".format(saldo_atual).replace('.', ',')

    return render_template("dashboard.html", user=user, saldo_atual=saldo_atual_formatado)



@app.route("/graficos", methods=['GET', 'POST'])
def graficos():
    user = session.get("user")
    if not user:
        return redirect("/login")

    # Recupere os dados do banco de dados "movimentaçoes" para gerar os gráficos
    conn_movimentacoes = sqlite3.connect('movimentaçoes.db')
    cursor_movimentacoes = conn_movimentacoes.cursor()

    # Consulta para obter o total de despesas
    cursor_movimentacoes.execute("SELECT SUM(valor_despesa) FROM extrato WHERE tipo_movimento='Despesa'")
    total_despesas = cursor_movimentacoes.fetchone()[0] or 0

    # Consulta para obter o total de receitas
    cursor_movimentacoes.execute("SELECT SUM(valor_receita) FROM extrato WHERE tipo_movimento='Receita'")
    total_receitas = cursor_movimentacoes.fetchone()[0] or 0

    conn_movimentacoes.close()

    # Recupere os dados do banco de dados "orçamento" para gerar o novo gráfico
    conn_orcamento = sqlite3.connect('orçamento.db')
    cursor_orcamento = conn_orcamento.cursor()

    # Consulta para obter o total de despesas previstas
    cursor_orcamento.execute("SELECT SUM(orçamento_previsto) FROM previsao WHERE tipo_movimento='Despesa'")
    total_despesas_previstas = cursor_orcamento.fetchone()[0] or 0

    # Consulta para obter o total de receitas previstas
    cursor_orcamento.execute("SELECT SUM(orçamento_previsto) FROM previsao WHERE tipo_movimento='Receita'")
    total_receitas_previstas = cursor_orcamento.fetchone()[0] or 0

    conn_orcamento.close()

    # Dados para plotar o gráfico de despesas e receitas
    labels_movimentacoes = ['Despesas', 'Receitas']
    values_movimentacoes = [total_despesas, total_receitas]

    # Dados para plotar o novo gráfico de despesas previstas e receitas previstas
    labels_orcamento = ['Despesas Previstas', 'Receitas Previstas']
    values_orcamento = [total_despesas_previstas, total_receitas_previstas]

    # Função para formatar os valores com o sinal de "R$"
    def format_value(value):
        return "R$" + format(value, ".2f")

    # Criação do gráfico de movimentações (despesas e receitas)
    plt.figure(figsize=(8, 6))
    plt.subplot(121)  # Subplot para as movimentações
    plt.pie(values_movimentacoes, labels=labels_movimentacoes, autopct=lambda pct: format_value(pct * sum(values_movimentacoes) / 100))
    plt.title("Despesas vs. Receitas")

    # Criação do gráfico de previsões (despesas previstas e receitas previstas)
    plt.subplot(122)  # Subplot para as previsões
    plt.pie(values_orcamento, labels=labels_orcamento, autopct=lambda pct: format_value(pct * sum(values_orcamento) / 100))
    plt.title("Despesas Previstas vs. Receitas Previstas")

    # Ajustes de layout dos subplots
    plt.tight_layout()

    # Salva o gráfico em um buffer
    buffer = io.BytesIO()
    plt.savefig(buffer, format='png')
    buffer.seek(0)

    # Codifica o gráfico em base64
    image_base64 = base64.b64encode(buffer.read()).decode('utf-8')

    # Renderiza a página de gráficos com a imagem do gráfico embutida
    return render_template("graficos.html", user=user, image_base64=image_base64)



@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect("/login")

if __name__ == "__main__":
    app.run(debug=True)
