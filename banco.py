"""
banco.py

funções utilizadas pelos scripts para trabalhar com o PostgreSQL.
"""

import psycopg2

from psycopg2 import Error

from config import POSTGRES_CONFIG


def conectar():
    """
    cria a conexão com o banco configurado no arquivo .env.
    caso a conexão não funcione, apresenta uma mensagem com o erro.
    """

    try:
        return psycopg2.connect(
            **POSTGRES_CONFIG
        )

    except (Error, UnicodeDecodeError) as erro:
        raise RuntimeError(
            "Não foi possível conectar ao PostgreSQL em "
            f"{POSTGRES_CONFIG['host']}:"
            f"{POSTGRES_CONFIG['port']} no banco "
            f"'{POSTGRES_CONFIG['dbname']}'. "
            "Confira o arquivo .env e verifique se o banco foi criado. "
            f"Detalhes: {erro}"
        ) from erro


def executar(conexao, comando_sql):
    """
    executa um comando SQL e confirma a alteração no banco.
    """

    with conexao.cursor() as cursor:
        cursor.execute(
            comando_sql
        )

    conexao.commit()


def inserir_em_lote(
    conexao,
    comando_insert,
    registros
):
    """
    insere uma lista de registros no banco utilizando executemany.
    """

    if not registros:
        return

    with conexao.cursor() as cursor:
        cursor.executemany(
            comando_insert,
            registros
        )

    conexao.commit()