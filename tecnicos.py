
import sqlite3

from flask import Blueprint, request, jsonify
from werkzeug.security import generate_password_hash

from database import conectar
from auth import permissao


tecnicos = Blueprint("tecnicos", __name__)


def validar_tecnico(dados, cadastro=False):

    if not isinstance(dados, dict):
        return None

    campos = [
        "nome",
        "telefone",
        "especialidade",
        "status"
    ]

    if cadastro:
        campos.extend(["login", "senha"])

    resultado = {}

    for campo in campos:

        valor = dados.get(
            campo,
            "Disponível" if campo == "status" else ""
        )

        if not isinstance(valor, str):
            return None

        resultado[campo] = valor.strip()

    if not resultado["nome"] or not resultado["telefone"]:
        return None

    if resultado["status"] not in [
        "Disponível",
        "Ocupado",
        "Inativo"
    ]:
        return None

    if cadastro:

        if not resultado["login"]:
            return None

        if len(resultado["senha"]) < 6:
            return None

    return resultado


# LISTAR TÉCNICOS

@tecnicos.route("/api/tecnicos", methods=["GET"])
@permissao("administrador", "atendente", "gerente")
def listar_tecnicos():

    conexao = conectar()

    try:
        registros = conexao.execute("""
            SELECT t.*, u.login
            FROM tecnicos t
            LEFT JOIN usuarios u
                ON t.usuario_id = u.id
            ORDER BY t.nome
        """).fetchall()

        return jsonify([
            dict(tecnico) for tecnico in registros
        ])

    finally:
        conexao.close()


# CONSULTAR TÉCNICO

@tecnicos.route("/api/tecnicos/<int:id>", methods=["GET"])
@permissao("administrador", "atendente", "gerente")
def consultar_tecnico(id):

    conexao = conectar()

    try:
        tecnico = conexao.execute("""
            SELECT t.*, u.login
            FROM tecnicos t
            LEFT JOIN usuarios u
                ON t.usuario_id = u.id
            WHERE t.id = ?
        """, (id,)).fetchone()

        if tecnico is None:
            return jsonify({
                "erro": "Técnico não encontrado."
            }), 404

        return jsonify(dict(tecnico))

    finally:
        conexao.close()


# CADASTRAR TÉCNICO

@tecnicos.route("/api/tecnicos", methods=["POST"])
@permissao("administrador")
def cadastrar_tecnico():

    dados = validar_tecnico(
        request.get_json(silent=True),
        cadastro=True
    )

    if dados is None:
        return jsonify({
            "erro": "Informe nome, telefone, login e senha válida."
        }), 400

    conexao = conectar()

    try:
        usuario = conexao.execute("""
            INSERT INTO usuarios
            (nome, login, senha_hash, perfil, ativo)
            VALUES (?, ?, ?, ?, ?)
        """, (
            dados["nome"],
            dados["login"],
            generate_password_hash(dados["senha"]),
            "tecnico",
            int(dados["status"] != "Inativo")
        ))

        cursor = conexao.execute("""
            INSERT INTO tecnicos
            (usuario_id, nome, telefone, especialidade, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            usuario.lastrowid,
            dados["nome"],
            dados["telefone"],
            dados["especialidade"],
            dados["status"]
        ))

        conexao.commit()

        return jsonify({
            "mensagem": "Técnico cadastrado com sucesso.",
            "id": cursor.lastrowid
        }), 201

    except sqlite3.IntegrityError:

        conexao.rollback()

        return jsonify({
            "erro": "Login já cadastrado."
        }), 409

    finally:
        conexao.close()


# EDITAR TÉCNICO

@tecnicos.route("/api/tecnicos/<int:id>", methods=["PUT"])
@permissao("administrador")
def editar_tecnico(id):

    dados = validar_tecnico(
        request.get_json(silent=True)
    )

    if dados is None:
        return jsonify({
            "erro": "Dados do técnico inválidos."
        }), 400

    conexao = conectar()

    try:
        tecnico = conexao.execute("""
            SELECT * FROM tecnicos WHERE id = ?
        """, (id,)).fetchone()

        if tecnico is None:
            return jsonify({
                "erro": "Técnico não encontrado."
            }), 404

        conexao.execute("""
            UPDATE tecnicos
            SET nome = ?,
                telefone = ?,
                especialidade = ?,
                status = ?
            WHERE id = ?
        """, (
            dados["nome"],
            dados["telefone"],
            dados["especialidade"],
            dados["status"],
            id
        ))

        conexao.execute("""
            UPDATE usuarios
            SET nome = ?, ativo = ?
            WHERE id = ?
        """, (
            dados["nome"],
            int(dados["status"] != "Inativo"),
            tecnico["usuario_id"]
        ))

        conexao.commit()

        return jsonify({
            "mensagem": "Técnico atualizado com sucesso."
        })

    finally:
        conexao.close()


# EXCLUIR TÉCNICO

@tecnicos.route("/api/tecnicos/<int:id>", methods=["DELETE"])
@permissao("administrador")
def excluir_tecnico(id):

    conexao = conectar()

    try:
        tecnico = conexao.execute("""
            SELECT * FROM tecnicos WHERE id = ?
        """, (id,)).fetchone()

        if tecnico is None:
            return jsonify({
                "erro": "Técnico não encontrado."
            }), 404

        conexao.execute(
            "DELETE FROM tecnicos WHERE id = ?",
            (id,)
        )

        conexao.execute("""
            UPDATE usuarios
            SET ativo = 0
            WHERE id = ?
        """, (tecnico["usuario_id"],))

        conexao.commit()

        return jsonify({
            "mensagem": "Técnico excluído com sucesso."
        })

    except sqlite3.IntegrityError:

        conexao.rollback()

        return jsonify({
            "erro": "Técnico possui chamados vinculados."
        }), 409

    finally:
        conexao.close()
