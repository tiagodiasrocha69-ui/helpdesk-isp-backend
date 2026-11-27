
from flask import Blueprint, jsonify, session

from database import conectar
from auth import login_obrigatorio


dashboard = Blueprint("dashboard", __name__)


@dashboard.route("/api/dashboard", methods=["GET"])
@login_obrigatorio
def consultar_dashboard():

    conexao = conectar()

    try:

        perfil = session["perfil"]

        filtro = ""
        parametros = []

        # Técnico visualiza somente seus chamados

        if perfil == "tecnico":

            filtro = """
                WHERE tecnico_id IN (
                    SELECT id FROM tecnicos
                    WHERE usuario_id = ?
                )
            """

            parametros.append(session["usuario_id"])


        indicadores = conexao.execute(f"""
            SELECT
                COUNT(*) AS total,

                COUNT(
                    CASE WHEN status = 'Aberto'
                    THEN 1 END
                ) AS abertos,

                COUNT(
                    CASE WHEN status = 'Em Andamento'
                    THEN 1 END
                ) AS em_andamento,

                COUNT(
                    CASE WHEN status = 'Concluído'
                    THEN 1 END
                ) AS concluidos

            FROM chamados
            {filtro}

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


        # Indicadores administrativos

        if perfil != "tecnico":

            resultado["total_clientes"] = conexao.execute(
                "SELECT COUNT(*) FROM clientes"
            ).fetchone()[0]

            resultado["total_tecnicos"] = conexao.execute(
                "SELECT COUNT(*) FROM tecnicos"
            ).fetchone()[0]

            resultado["tecnicos_disponiveis"] = conexao.execute("""
                SELECT COUNT(*)
                FROM tecnicos t
                INNER JOIN usuarios u
                    ON t.usuario_id = u.id
                WHERE t.status = 'Disponível'
                    AND u.ativo = 1
            """).fetchone()[0]


        # Distribuição por prioridade

        prioridades = conexao.execute(f"""
            SELECT
                prioridade,
                COUNT(*) AS quantidade
            FROM chamados
            {filtro}
            GROUP BY prioridade
        """, parametros).fetchall()

        resultado["prioridades"] = [
            dict(registro)
            for registro in prioridades
        ]


        # Chamados recentes

        sql = """
            SELECT
                ch.id,
                c.nome AS cliente_nome,
                t.nome AS tecnico_nome,
                ch.prioridade,
                ch.status,
                ch.data_abertura

            FROM chamados ch

            INNER JOIN clientes c
                ON ch.cliente_id = c.id

            LEFT JOIN tecnicos t
                ON ch.tecnico_id = t.id
        """

        parametros_recentes = []

        if perfil == "tecnico":

            sql += " WHERE t.usuario_id = ?"

            parametros_recentes.append(
                session["usuario_id"]
            )

        sql += " ORDER BY ch.id DESC LIMIT 5"

        recentes = conexao.execute(
            sql,
            parametros_recentes
        ).fetchall()

        resultado["recentes"] = [
            dict(registro)
            for registro in recentes
        ]

        return jsonify(resultado)

    finally:

        conexao.close()
