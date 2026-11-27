
from datetime import date

from flask import Blueprint, request, jsonify

from database import conectar
from auth import permissao


relatorios = Blueprint("relatorios", __name__)


@relatorios.route("/api/relatorios", methods=["GET"])
@permissao("administrador", "atendente", "gerente")
def gerar_relatorio():

    data_inicio = request.args.get("data_inicio", "")
    data_fim = request.args.get("data_fim", "")
    tecnico_id = request.args.get("tecnico_id", "")
    status = request.args.get("status", "")
    prioridade = request.args.get("prioridade", "")

    # Validar período

    try:

        if data_inicio:
            date.fromisoformat(data_inicio)

        if data_fim:
            date.fromisoformat(data_fim)

    except ValueError:

        return jsonify({
            "erro": "Período informado é inválido."
        }), 400

    if data_inicio and data_fim and data_inicio > data_fim:

        return jsonify({
            "erro": "A data inicial não pode ser maior que a final."
        }), 400

    if status and status not in [
        "Aberto", "Em Andamento", "Concluído"
    ]:

        return jsonify({
            "erro": "Status inválido."
        }), 400

    if prioridade and prioridade not in [
        "Alta", "Média", "Baixa"
    ]:

        return jsonify({
            "erro": "Prioridade inválida."
        }), 400

    if tecnico_id:

        try:

            tecnico_id = int(tecnico_id)

            if tecnico_id <= 0:
                raise ValueError

        except ValueError:

            return jsonify({
                "erro": "Técnico inválido."
            }), 400

    filtros = []
    parametros = []

    if data_inicio:

        filtros.append("""
            date(ch.data_abertura, '-3 hours') >= ?
        """)

        parametros.append(data_inicio)

    if data_fim:

        filtros.append("""
            date(ch.data_abertura, '-3 hours') <= ?
        """)

        parametros.append(data_fim)

    if tecnico_id:

        filtros.append("ch.tecnico_id = ?")
        parametros.append(tecnico_id)

    if status:

        filtros.append("ch.status = ?")
        parametros.append(status)

    if prioridade:

        filtros.append("ch.prioridade = ?")
        parametros.append(prioridade)

    where = ""

    if filtros:

        where = " WHERE " + " AND ".join(filtros)

    conexao = conectar()

    try:

        # Indicadores gerais

        indicadores = conexao.execute(f"""
            SELECT

                COUNT(*) AS total,

                COUNT(
                    CASE WHEN ch.status = 'Aberto'
                    THEN 1 END
                ) AS abertos,

                COUNT(
                    CASE WHEN ch.status = 'Em Andamento'
                    THEN 1 END
                ) AS em_andamento,

                COUNT(
                    CASE WHEN ch.status = 'Concluído'
                    THEN 1 END
                ) AS concluidos,

                ROUND(
                    AVG(
                        CASE
                            WHEN ch.status = 'Concluído'
                            AND ch.data_encerramento IS NOT NULL
                            THEN (
                                julianday(ch.data_encerramento)
                                - julianday(ch.data_abertura)
                            ) * 24
                        END
                    ),
                    2
                ) AS tempo_medio_horas

            FROM chamados ch

            {where}

        """, parametros).fetchone()

        resultado = dict(indicadores)

        total = resultado["total"]

        resultado["taxa_resolucao"] = (

            round(
                resultado["concluidos"] / total * 100,
                1
            )

            if total > 0 else 0

        )

        # Distribuição por prioridade

        prioridades = conexao.execute(f"""
            SELECT
                ch.prioridade,
                COUNT(*) AS quantidade

            FROM chamados ch

            {where}

            GROUP BY ch.prioridade

        """, parametros).fetchall()

        resultado["prioridades"] = [
            dict(p) for p in prioridades
        ]

        # Desempenho dos técnicos

        desempenho = conexao.execute(f"""
            SELECT

                ch.tecnico_id,

                COALESCE(
                    t.nome,
                    'Não atribuído'
                ) AS tecnico,

                COUNT(*) AS total,

                COUNT(
                    CASE WHEN ch.status = 'Aberto'
                    THEN 1 END
                ) AS abertos,

                COUNT(
                    CASE WHEN ch.status = 'Em Andamento'
                    THEN 1 END
                ) AS em_andamento,

                COUNT(
                    CASE WHEN ch.status = 'Concluído'
                    THEN 1 END
                ) AS concluidos

            FROM chamados ch

            LEFT JOIN tecnicos t
                ON ch.tecnico_id = t.id

            {where}

            GROUP BY ch.tecnico_id, t.nome

            ORDER BY total DESC, tecnico

        """, parametros).fetchall()

        resultado["desempenho"] = []

        for registro in desempenho:

            item = dict(registro)

            item["taxa_resolucao"] = round(
                item["concluidos"] / item["total"] * 100,
                1
            )

            resultado["desempenho"].append(item)

        # Lista detalhada de chamados

        registros = conexao.execute(f"""
            SELECT

                ch.id,
                c.nome AS cliente_nome,

                COALESCE(
                    t.nome,
                    'Não atribuído'
                ) AS tecnico_nome,

                ch.descricao,
                ch.prioridade,
                ch.status,
                ch.data_abertura,
                ch.data_encerramento

            FROM chamados ch

            INNER JOIN clientes c
                ON ch.cliente_id = c.id

            LEFT JOIN tecnicos t
                ON ch.tecnico_id = t.id

            {where}

            ORDER BY ch.id DESC

        """, parametros).fetchall()

        resultado["chamados"] = [
            dict(chamado)
            for chamado in registros
        ]

        return jsonify(resultado)

    finally:

        conexao.close()
