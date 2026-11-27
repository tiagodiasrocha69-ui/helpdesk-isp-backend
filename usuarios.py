
import sqlite3

from flask import Blueprint, request, jsonify, session
from werkzeug.security import generate_password_hash

from database import conectar
from auth import permissao


usuarios = Blueprint("usuarios", __name__)

PERFIS = [
    "administrador",
    "atendente",
    "gerente"
]


# LISTAR USUÁRIOS

@usuarios.route("/api/usuarios", methods=["GET"])
@permissao("administrador")
def listar_usuarios():

    conexao = conectar()

    try:

        registros = conexao.execute("""
            SELECT
                id,
                nome,
                login,
                perfil,
                ativo,
                criado_em
            FROM usuarios
            ORDER BY nome
        """).fetchall()

        return jsonify([
            dict(usuario)
            for usuario in registros
        ])

    finally:

        conexao.close()


# CADASTRAR USUÁRIO

@usuarios.route("/api/usuarios", methods=["POST"])
@permissao("administrador")
def cadastrar_usuario():

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):

        return jsonify({
            "erro": "Dados inválidos."
        }), 400

    nome = dados.get("nome", "")
    login = dados.get("login", "")
    senha = dados.get("senha", "")
    perfil = dados.get("perfil", "")

    if not all(
        isinstance(valor, str)
        for valor in [nome, login, senha, perfil]
    ):

        return jsonify({
            "erro": "Dados inválidos."
        }), 400

    nome = nome.strip()
    login = login.strip()

    if not nome or not login or len(senha) < 6:

        return jsonify({
            "erro": "Informe nome, login e senha com pelo menos 6 caracteres."
        }), 400

    if perfil not in PERFIS:

        return jsonify({
            "erro": "Perfil inválido."
        }), 400

    conexao = conectar()

    try:

        cursor = conexao.execute("""
            INSERT INTO usuarios
            (nome, login, senha_hash, perfil, ativo)
            VALUES (?, ?, ?, ?, 1)
        """, (
            nome,
            login,
            generate_password_hash(senha),
            perfil
        ))

        conexao.commit()

        return jsonify({
            "mensagem": "Usuário cadastrado com sucesso.",
            "id": cursor.lastrowid
        }), 201

    except sqlite3.IntegrityError:

        conexao.rollback()

        return jsonify({
            "erro": "Login já cadastrado."
        }), 409

    finally:

        conexao.close()


# EDITAR USUÁRIO

@usuarios.route("/api/usuarios/<int:id>", methods=["PUT"])
@permissao("administrador")
def editar_usuario(id):

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):

        return jsonify({
            "erro": "Dados inválidos."
        }), 400

    nome = dados.get("nome", "")
    perfil = dados.get("perfil", "")

    if (
        not isinstance(nome, str)
        or not isinstance(perfil, str)
        or not nome.strip()
    ):

        return jsonify({
            "erro": "Informe os dados corretamente."
        }), 400

    conexao = conectar()

    try:

        conexao.execute("BEGIN IMMEDIATE")

        usuario = conexao.execute("""
            SELECT * FROM usuarios
            WHERE id = ?
        """, (id,)).fetchone()

        if usuario is None:

            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        if usuario["perfil"] == "tecnico":

            return jsonify({
                "erro": "Edite os dados pelo cadastro de técnicos."
            }), 409

        if perfil not in PERFIS:

            return jsonify({
                "erro": "Perfil inválido."
            }), 400

        if (
            id == session["usuario_id"]
            and perfil != "administrador"
        ):

            return jsonify({
                "erro": "Você não pode remover seu próprio perfil administrativo."
            }), 409

        conexao.execute("""
            UPDATE usuarios
            SET nome = ?, perfil = ?
            WHERE id = ?
        """, (
            nome.strip(),
            perfil,
            id
        ))

        conexao.commit()

        return jsonify({
            "mensagem": "Usuário atualizado com sucesso."
        })

    finally:

        conexao.close()


# ATIVAR OU DESATIVAR USUÁRIO

@usuarios.route(
    "/api/usuarios/<int:id>/status",
    methods=["PUT"]
)
@permissao("administrador")
def alterar_status_usuario(id):

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):

        return jsonify({
            "erro": "Dados inválidos."
        }), 400

    ativo = dados.get("ativo")

    if type(ativo) is not int or ativo not in [0, 1]:

        return jsonify({
            "erro": "Status inválido."
        }), 400

    if id == session["usuario_id"] and ativo == 0:

        return jsonify({
            "erro": "Você não pode desativar sua própria conta."
        }), 409

    conexao = conectar()

    try:

        conexao.execute("BEGIN IMMEDIATE")

        usuario = conexao.execute("""
            SELECT * FROM usuarios
            WHERE id = ?
        """, (id,)).fetchone()

        if usuario is None:

            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        if usuario["perfil"] == "tecnico":

            return jsonify({
                "erro": "Altere a disponibilidade pelo cadastro de técnicos."
            }), 409

        conexao.execute("""
            UPDATE usuarios
            SET ativo = ?
            WHERE id = ?
        """, (ativo, id))

        conexao.commit()

        return jsonify({
            "mensagem": (
                "Usuário ativado com sucesso."
                if ativo
                else "Usuário desativado com sucesso."
            )
        })

    finally:

        conexao.close()


# REDEFINIR SENHA

@usuarios.route(
    "/api/usuarios/<int:id>/senha",
    methods=["PUT"]
)
@permissao("administrador")
def redefinir_senha(id):

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):

        return jsonify({
            "erro": "Dados inválidos."
        }), 400

    senha = dados.get("senha", "")

    if not isinstance(senha, str) or len(senha) < 6:

        return jsonify({
            "erro": "A senha deve possuir pelo menos 6 caracteres."
        }), 400

    conexao = conectar()

    try:

        cursor = conexao.execute("""
            UPDATE usuarios
            SET senha_hash = ?
            WHERE id = ?
        """, (
            generate_password_hash(senha),
            id
        ))

        if cursor.rowcount == 0:

            return jsonify({
                "erro": "Usuário não encontrado."
            }), 404

        conexao.commit()

        return jsonify({
            "mensagem": "Senha redefinida com sucesso."
        })

    finally:

        conexao.close()
