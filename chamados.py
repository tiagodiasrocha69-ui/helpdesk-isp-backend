
from flask import Blueprint, request, jsonify, session

from database import conectar
from auth import permissao, login_obrigatorio


chamados = Blueprint("chamados", __name__)


# ABRIR CHAMADO

@chamados.route("/api/chamados", methods=["POST"])
@permissao("administrador", "atendente")
def abrir_chamado():

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "erro": "Dados inválidos."
        }), 400

    cliente_id = dados.get("cliente_id")
    descricao = dados.get("descricao")
    prioridade = dados.get("prioridade")
    endereco = dados.get("endereco")

    if (
        type(cliente_id) is not int
        or cliente_id <= 0
        or not isinstance(descricao, str)
        or not descricao.strip()
        or not isinstance(endereco, str)
        or not endereco.strip()
        or prioridade not in ["Baixa", "Média", "Alta"]
    ):
        return jsonify({
            "erro": "Preencha corretamente todos os campos."
        }), 400

    conexao = conectar()

    try:
        cliente = conexao.execute("""
            SELECT id FROM clientes WHERE id = ?
        """, (cliente_id,)).fetchone()

        if cliente is None:
            return jsonify({
                "erro": "Cliente não encontrado."
            }), 404

        cursor = conexao.execute("""
            INSERT INTO chamados
            (cliente_id, descricao, endereco, prioridade, status)
            VALUES (?, ?, ?, ?, ?)
        """, (
            cliente_id,
            descricao.strip(),
            endereco.strip(),
            prioridade,
            "Aberto"
        ))

        chamado_id = cursor.lastrowid

        conexao.execute("""
            INSERT INTO historico_chamados
            (
                chamado_id,
                usuario_id,
                status_novo,
                observacao
            )
            VALUES (?, ?, ?, ?)
        """, (
            chamado_id,
            session["usuario_id"],
            "Aberto",
            "Chamado registrado no sistema."
        ))

        conexao.commit()

        return jsonify({
            "mensagem": "Chamado aberto com sucesso.",
            "id": chamado_id,
            "status": "Aberto"
        }), 201

    finally:
        conexao.close()


# LISTAR CHAMADOS

@chamados.route("/api/chamados", methods=["GET"])
@login_obrigatorio
def listar_chamados():

    conexao = conectar()

    try:
        sql = """
            SELECT
                ch.*,
                c.nome AS cliente_nome,
                c.telefone AS cliente_telefone,
                t.nome AS tecnico_nome
            FROM chamados ch
            INNER JOIN clientes c
                ON ch.cliente_id = c.id
            LEFT JOIN tecnicos t
                ON ch.tecnico_id = t.id
            WHERE 1 = 1
        """

        parametros = []

        if session.get("perfil") == "tecnico":

            sql += " AND t.usuario_id = ?"

            parametros.append(
                session["usuario_id"]
            )

        status = request.args.get("status")

        if status:

            sql += " AND ch.status = ?"
            parametros.append(status)

        prioridade = request.args.get("prioridade")

        if prioridade:

            sql += " AND ch.prioridade = ?"
            parametros.append(prioridade)

        sql += " ORDER BY ch.id DESC"

        registros = conexao.execute(
            sql,
            parametros
        ).fetchall()

        return jsonify([
            dict(chamado) for chamado in registros
        ])

    finally:
        conexao.close()


# CONSULTAR CHAMADO

@chamados.route("/api/chamados/<int:id>", methods=["GET"])
@login_obrigatorio
def consultar_chamado(id):

    conexao = conectar()

    try:
        sql = """
            SELECT
                ch.*,
                c.nome AS cliente_nome,
                c.telefone AS cliente_telefone,
                t.nome AS tecnico_nome
            FROM chamados ch
            INNER JOIN clientes c
                ON ch.cliente_id = c.id
            LEFT JOIN tecnicos t
                ON ch.tecnico_id = t.id
            WHERE ch.id = ?
        """

        parametros = [id]

        if session.get("perfil") == "tecnico":

            sql += " AND t.usuario_id = ?"

            parametros.append(
                session["usuario_id"]
            )

        chamado = conexao.execute(
            sql,
            parametros
        ).fetchone()

        if chamado is None:
            return jsonify({
                "erro": "Chamado não encontrado."
            }), 404

        return jsonify(dict(chamado))

    finally:
        conexao.close()
