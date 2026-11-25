
import sqlite3

from flask import Blueprint, request, jsonify
from database import conectar
from auth import permissao


clientes = Blueprint("clientes", __name__)


def validar_cliente(dados):

    if not isinstance(dados, dict):
        return None

    campos = [
        "nome",
        "cpf_cnpj",
        "telefone",
        "email",
        "endereco"
    ]

    resultado = {}

    for campo in campos:

        valor = dados.get(campo, "")

        if not isinstance(valor, str):
            return None

        resultado[campo] = valor.strip()

    if not all(
        resultado[campo]
        for campo in ["nome", "telefone", "endereco"]
    ):
        return None

    return resultado


# LISTAR CLIENTES

@clientes.route("/api/clientes", methods=["GET"])
@permissao("administrador", "atendente", "gerente")
def listar_clientes():

    conexao = conectar()

    try:
        registros = conexao.execute("""
            SELECT * FROM clientes
            ORDER BY nome
        """).fetchall()

        return jsonify([
            dict(cliente) for cliente in registros
        ])

    finally:
        conexao.close()


# CONSULTAR CLIENTE

@clientes.route("/api/clientes/<int:id>", methods=["GET"])
@permissao("administrador", "atendente", "gerente")
def consultar_cliente(id):

    conexao = conectar()

    try:
        cliente = conexao.execute(
            "SELECT * FROM clientes WHERE id = ?",
            (id,)
        ).fetchone()

        if cliente is None:
            return jsonify({
                "erro": "Cliente não encontrado."
            }), 404

        return jsonify(dict(cliente))

    finally:
        conexao.close()


# CADASTRAR CLIENTE

@clientes.route("/api/clientes", methods=["POST"])
@permissao("administrador", "atendente")
def cadastrar_cliente():

    dados = validar_cliente(
        request.get_json(silent=True)
    )

    if dados is None:
        return jsonify({
            "erro": "Informe nome, telefone e endereço."
        }), 400

    conexao = conectar()

    try:
        cursor = conexao.execute("""
            INSERT INTO clientes
            (nome, cpf_cnpj, telefone, email, endereco)
            VALUES (?, ?, ?, ?, ?)
        """, (
            dados["nome"],
            dados["cpf_cnpj"] or None,
            dados["telefone"],
            dados["email"],
            dados["endereco"]
        ))

        conexao.commit()

        return jsonify({
            "mensagem": "Cliente cadastrado com sucesso.",
            "id": cursor.lastrowid
        }), 201

    except sqlite3.IntegrityError:

        conexao.rollback()

        return jsonify({
            "erro": "CPF ou CNPJ já cadastrado."
        }), 409

    finally:
        conexao.close()


# EDITAR CLIENTE

@clientes.route("/api/clientes/<int:id>", methods=["PUT"])
@permissao("administrador", "atendente")
def editar_cliente(id):

    dados = validar_cliente(
        request.get_json(silent=True)
    )

    if dados is None:
        return jsonify({
            "erro": "Dados obrigatórios inválidos."
        }), 400

    conexao = conectar()

    try:
        cursor = conexao.execute("""
            UPDATE clientes
            SET nome = ?,
                cpf_cnpj = ?,
                telefone = ?,
                email = ?,
                endereco = ?
            WHERE id = ?
        """, (
            dados["nome"],
            dados["cpf_cnpj"] or None,
            dados["telefone"],
            dados["email"],
            dados["endereco"],
            id
        ))

        if cursor.rowcount == 0:
            return jsonify({
                "erro": "Cliente não encontrado."
            }), 404

        conexao.commit()

        return jsonify({
            "mensagem": "Cliente atualizado com sucesso."
        })

    except sqlite3.IntegrityError:

        conexao.rollback()

        return jsonify({
            "erro": "CPF ou CNPJ já cadastrado."
        }), 409

    finally:
        conexao.close()


# EXCLUIR CLIENTE

@clientes.route("/api/clientes/<int:id>", methods=["DELETE"])
@permissao("administrador", "atendente")
def excluir_cliente(id):

    conexao = conectar()

    try:
        cursor = conexao.execute(
            "DELETE FROM clientes WHERE id = ?",
            (id,)
        )

        if cursor.rowcount == 0:
            return jsonify({
                "erro": "Cliente não encontrado."
            }), 404

        conexao.commit()

        return jsonify({
            "mensagem": "Cliente excluído com sucesso."
        })

    except sqlite3.IntegrityError:

        conexao.rollback()

        return jsonify({
            "erro": "Cliente possui chamados vinculados."
        }), 409

    finally:
        conexao.close()
