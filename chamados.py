
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


# ATRIBUIR CHAMADO AO TÉCNICO

@chamados.route(
    "/api/chamados/<int:id>/atribuir",
    methods=["PUT"]
)
@permissao("administrador", "atendente")
def atribuir_chamado(id):

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "erro": "Dados inválidos."
        }), 400

    tecnico_id = dados.get("tecnico_id")

    if type(tecnico_id) is not int or tecnico_id <= 0:
        return jsonify({
            "erro": "Selecione um técnico válido."
        }), 400

    conexao = conectar()

    try:

        conexao.execute("BEGIN IMMEDIATE")

        chamado = conexao.execute("""
            SELECT * FROM chamados WHERE id = ?
        """, (id,)).fetchone()

        if chamado is None:
            return jsonify({
                "erro": "Chamado não encontrado."
            }), 404

        if chamado["status"] != "Aberto":
            return jsonify({
                "erro": "Somente chamados abertos podem ser atribuídos."
            }), 409

        tecnico = conexao.execute("""
            SELECT t.*
            FROM tecnicos t
            INNER JOIN usuarios u
                ON t.usuario_id = u.id
            WHERE t.id = ?
                AND t.status = 'Disponível'
                AND u.ativo = 1
        """, (tecnico_id,)).fetchone()

        if tecnico is None:
            return jsonify({
                "erro": "Técnico indisponível."
            }), 409

        conexao.execute("""
            UPDATE chamados
            SET tecnico_id = ?
            WHERE id = ?
        """, (tecnico_id, id))

        conexao.execute("""
            INSERT INTO historico_chamados
            (
                chamado_id,
                usuario_id,
                status_anterior,
                status_novo,
                observacao
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            id,
            session["usuario_id"],
            chamado["status"],
            chamado["status"],
            f"Chamado atribuído ao técnico {tecnico['nome']}."
        ))

        conexao.commit()

        return jsonify({
            "mensagem": "Chamado atribuído com sucesso."
        })

    finally:

        conexao.close()


# ATUALIZAR STATUS E ENCERRAR CHAMADO

@chamados.route(
    "/api/chamados/<int:id>/status",
    methods=["PUT"]
)
@permissao("administrador", "tecnico")
def atualizar_status(id):

    dados = request.get_json(silent=True)

    if not isinstance(dados, dict):
        return jsonify({
            "erro": "Dados inválidos."
        }), 400

    novo_status = dados.get("status")

    observacao = dados.get("observacao", "")

    if not isinstance(observacao, str):
        return jsonify({
            "erro": "Observação inválida."
        }), 400

    observacao = observacao.strip()

    if novo_status not in [
        "Em Andamento",
        "Concluído"
    ]:
        return jsonify({
            "erro": "Status inválido."
        }), 400

    conexao = conectar()

    try:

        conexao.execute("BEGIN IMMEDIATE")

        chamado = conexao.execute("""
            SELECT
                ch.*,
                t.usuario_id AS tecnico_usuario_id
            FROM chamados ch
            LEFT JOIN tecnicos t
                ON ch.tecnico_id = t.id
            WHERE ch.id = ?
        """, (id,)).fetchone()

        if chamado is None:
            return jsonify({
                "erro": "Chamado não encontrado."
            }), 404

        if session["perfil"] == "tecnico":

            if (
                chamado["tecnico_usuario_id"]
                != session["usuario_id"]
            ):
                return jsonify({
                    "erro": "Acesso não autorizado."
                }), 403

        if chamado["tecnico_id"] is None:
            return jsonify({
                "erro": "Atribua um técnico antes de iniciar."
            }), 409

        status_anterior = chamado["status"]

        transicoes = {
            "Aberto": ["Em Andamento"],
            "Em Andamento": ["Concluído"],
            "Concluído": []
        }

        if novo_status not in transicoes.get(
            status_anterior, []
        ):
            return jsonify({
                "erro": "Alteração de status não permitida."
            }), 409

        if novo_status == "Concluído":

            if not observacao:
                return jsonify({
                    "erro": "Informe a solução do problema."
                }), 400

            conexao.execute("""
                UPDATE chamados
                SET status = ?,
                    data_encerramento = CURRENT_TIMESTAMP
                WHERE id = ?
            """, (novo_status, id))

        else:

            conexao.execute("""
                UPDATE chamados
                SET status = ?
                WHERE id = ?
            """, (novo_status, id))

        conexao.execute("""
            INSERT INTO historico_chamados
            (
                chamado_id,
                usuario_id,
                status_anterior,
                status_novo,
                observacao
            )
            VALUES (?, ?, ?, ?, ?)
        """, (
            id,
            session["usuario_id"],
            status_anterior,
            novo_status,
            observacao or "Status atualizado."
        ))

        conexao.commit()

        return jsonify({
            "mensagem": "Status atualizado com sucesso.",
            "status": novo_status
        })

    finally:

        conexao.close()


# CONSULTAR HISTÓRICO DO CHAMADO

@chamados.route(
    "/api/chamados/<int:id>/historico",
    methods=["GET"]
)
@login_obrigatorio
def consultar_historico(id):

    conexao = conectar()

    try:

        chamado = conexao.execute("""
            SELECT
                ch.id,
                t.usuario_id AS tecnico_usuario_id
            FROM chamados ch
            LEFT JOIN tecnicos t
                ON ch.tecnico_id = t.id
            WHERE ch.id = ?
        """, (id,)).fetchone()

        if chamado is None:
            return jsonify({
                "erro": "Chamado não encontrado."
            }), 404

        if session["perfil"] == "tecnico":

            if (
                chamado["tecnico_usuario_id"]
                != session["usuario_id"]
            ):
                return jsonify({
                    "erro": "Acesso não autorizado."
                }), 403

        registros = conexao.execute("""
            SELECT
                h.*,
                u.nome AS usuario_nome
            FROM historico_chamados h
            LEFT JOIN usuarios u
                ON h.usuario_id = u.id
            WHERE h.chamado_id = ?
            ORDER BY h.id DESC
        """, (id,)).fetchall()

        return jsonify([
            dict(registro)
            for registro in registros
        ])

    finally:

        conexao.close()
