from functools import wraps
import os
import hashlib
import hmac

from flask import (
    Blueprint,
    request,
    jsonify,
    session
)

from werkzeug.security import (
    generate_password_hash,
    check_password_hash
)

from database import conectar


auth = Blueprint("auth", __name__)
def identificador_senha(senha_hash):

    return hashlib.sha256(
        senha_hash.encode("utf-8")
    ).hexdigest()



def criar_admin():

    conexao = conectar()

    try:

        usuario = conexao.execute(
            "SELECT id FROM usuarios WHERE login = ?",
            ("admin",)
        ).fetchone()

        if usuario is None:

            senha_inicial = os.environ.get(
                "ADMIN_PASSWORD", ""
            )

            if len(senha_inicial) < 12:

                raise RuntimeError(
                    "Defina ADMIN_PASSWORD com pelo menos "
                    "12 caracteres para criar o administrador."
                )

            conexao.execute("""
                INSERT INTO usuarios
                (nome, login, senha_hash, perfil)
                VALUES (?, ?, ?, ?)
            """, (
                "Administrador",
                "admin",
                generate_password_hash(senha_inicial),
                "administrador"
            ))

            conexao.commit()

            print("Administrador inicial criado!")

    finally:

        conexao.close()




def login_obrigatorio(funcao):

    @wraps(funcao)
    def verificar(*args, **kwargs):

        usuario_id = session.get("usuario_id")

        if not usuario_id:

            return jsonify({
                "erro": "Autenticação necessária."
            }), 401

        conexao = conectar()

        try:

            usuario = conexao.execute("""
                SELECT
                    id,
                    nome,
                    login,
                    perfil,
                    senha_hash

                FROM usuarios

                WHERE id = ? AND ativo = 1

            """, (usuario_id,)).fetchone()

        finally:

            conexao.close()

        if usuario is None:

            session.clear()

            return jsonify({
                "erro": "Sessão inválida."
            }), 401

        identificador_atual = identificador_senha(
            usuario["senha_hash"]
        )

        identificador_sessao = session.get(
            "identificador_senha", ""
        )

        if not hmac.compare_digest(
            identificador_sessao,
            identificador_atual
        ):

            session.clear()

            return jsonify({
                "erro": "Sessão expirada. Entre novamente."
            }), 401

        session["perfil"] = usuario["perfil"]

        return funcao(*args, **kwargs)

    return verificar



def permissao(*perfis):

    def decorator(funcao):

        @wraps(funcao)
        @login_obrigatorio
        def verificar(*args, **kwargs):

            if session.get("perfil") not in perfis:
                return jsonify({
                    "erro": "Acesso não autorizado."
                }), 403

            return funcao(*args, **kwargs)

        return verificar

    return decorator


@auth.route("/api/login", methods=["POST"])
def login():

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "erro": "Dados inválidos."
        }), 400

    login_usuario = dados.get("login")
    senha = dados.get("senha")

    if (
        not isinstance(login_usuario, str)
        or not isinstance(senha, str)
        or not login_usuario.strip()
        or not senha
    ):
        return jsonify({
            "erro": "Informe login e senha."
        }), 400

    conexao = conectar()

    try:
        usuario = conexao.execute("""
            SELECT * FROM usuarios
            WHERE login = ? AND ativo = 1
        """, (login_usuario.strip(),)).fetchone()

        if not usuario or not check_password_hash(
            usuario["senha_hash"], senha
        ):
            return jsonify({
                "erro": "Login ou senha inválidos."
            }), 401

        session.clear()

        session["usuario_id"] = usuario["id"]
        session["perfil"] = usuario["perfil"]

        session["identificador_senha"] = identificador_senha(
            usuario["senha_hash"]
        )

        return jsonify({
            "mensagem": "Login realizado com sucesso.",
            "usuario": {
                "id": usuario["id"],
                "nome": usuario["nome"],
                "login": usuario["login"],
                "perfil": usuario["perfil"]
            }
        })

    finally:
        conexao.close()


@auth.route("/api/logout", methods=["POST"])
def logout():

    session.clear()

    return jsonify({
        "mensagem": "Logout realizado com sucesso."
    })


@auth.route("/api/me", methods=["GET"])
@login_obrigatorio
def usuario_atual():

    conexao = conectar()

    try:
        usuario = conexao.execute("""
            SELECT id, nome, login, perfil
            FROM usuarios
            WHERE id = ? AND ativo = 1
        """, (session["usuario_id"],)).fetchone()

        if usuario is None:
            session.clear()

            return jsonify({
                "erro": "Sessão inválida."
            }), 401

        return jsonify(dict(usuario))

    finally:
        conexao.close()


@auth.route("/api/admin/teste", methods=["GET"])
@permissao("administrador")
def testar_permissao():

    return jsonify({
        "mensagem": "Acesso administrativo autorizado."
    })