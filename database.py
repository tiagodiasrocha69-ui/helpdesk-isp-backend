import sqlite3
from pathlib import Path

DATABASE = Path(__file__).parent / "helpdesk.db"


def conectar():
    conexao = sqlite3.connect(DATABASE)
    conexao.row_factory = sqlite3.Row
    conexao.execute("PRAGMA foreign_keys = ON")
    return conexao


def criar_banco():
    conexao = conectar()

    try:
        conexao.executescript("""
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                login TEXT NOT NULL UNIQUE,
                senha_hash TEXT NOT NULL,
                perfil TEXT NOT NULL CHECK (
                    perfil IN (
                        'administrador',
                        'atendente',
                        'tecnico',
                        'gerente'
                    )
                ),
                ativo INTEGER NOT NULL DEFAULT 1,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS clientes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                cpf_cnpj TEXT UNIQUE,
                telefone TEXT NOT NULL,
                email TEXT,
                endereco TEXT NOT NULL,
                criado_em TEXT DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS tecnicos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                usuario_id INTEGER UNIQUE,
                nome TEXT NOT NULL,
                telefone TEXT NOT NULL,
                especialidade TEXT,
                status TEXT NOT NULL DEFAULT 'Disponível',

                FOREIGN KEY (usuario_id)
                    REFERENCES usuarios(id)
            );

            CREATE TABLE IF NOT EXISTS chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                cliente_id INTEGER NOT NULL,
                tecnico_id INTEGER,
                descricao TEXT NOT NULL,
                endereco TEXT NOT NULL,

                prioridade TEXT NOT NULL CHECK (
                    prioridade IN ('Baixa', 'Média', 'Alta')
                ),

                status TEXT NOT NULL DEFAULT 'Aberto'
                    CHECK (
                        status IN (
                            'Aberto',
                            'Em Andamento',
                            'Concluído'
                        )
                    ),

                data_abertura TEXT DEFAULT CURRENT_TIMESTAMP,
                data_encerramento TEXT,

                FOREIGN KEY (cliente_id)
                    REFERENCES clientes(id),

                FOREIGN KEY (tecnico_id)
                    REFERENCES tecnicos(id)
            );

            CREATE TABLE IF NOT EXISTS historico_chamados (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chamado_id INTEGER NOT NULL,
                usuario_id INTEGER,
                status_anterior TEXT,
                status_novo TEXT,
                observacao TEXT,
                data_hora TEXT DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (chamado_id)
                    REFERENCES chamados(id),

                FOREIGN KEY (usuario_id)
                    REFERENCES usuarios(id)
            );
        """)

        conexao.commit()
        print("Banco de dados criado com sucesso!")

    finally:
        conexao.close()


if __name__ == "__main__":
    criar_banco()