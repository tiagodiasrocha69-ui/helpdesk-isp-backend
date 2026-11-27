
import os

from flask import Flask, jsonify
from flask_cors import CORS

from database import criar_banco, conectar
from auth import auth, criar_admin
from clientes import clientes
from tecnicos import tecnicos
from chamados import chamados
from dashboard import dashboard
from usuarios import usuarios
from relatorios import relatorios

app = Flask(__name__)

app.config["SECRET_KEY"] = os.environ["SECRET_KEY"]
app.config["SESSION_COOKIE_HTTPONLY"] = True
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"


CORS(
    app,
    origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ],
    supports_credentials=True
)


criar_banco()
criar_admin()


app.register_blueprint(auth)
app.register_blueprint(clientes)
app.register_blueprint(tecnicos)
app.register_blueprint(chamados)
app.register_blueprint(dashboard)
app.register_blueprint(usuarios)
app.register_blueprint(relatorios)


@app.route("/", methods=["GET"])
def inicio():

    return jsonify({
        "sistema": "HelpDesk ISP",
        "versao": "1.0.0",
        "status": "API funcionando"
    })


@app.route("/api/health", methods=["GET"])
def verificar_api():

    conexao = conectar()

    try:
        conexao.execute("SELECT 1")

        return jsonify({
            "api": "online",
            "banco": "conectado"
        })

    finally:
        conexao.close()


if __name__ == "__main__":

    app.run(
        host="127.0.0.1",
        port=5000,
        debug=False
    )
