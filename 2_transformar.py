"""
2_transformar.py

fase 2 do projeto: transformação da camada raw para a camada silver.

o script lê as tabelas raw em blocos, limpa os textos, converte
valores e datas e grava os resultados nas tabelas silver.

na tabela de viagens também são calculadas as colunas valor_total
e duracao_dias.
"""

import warnings

import pandas as pd

from psycopg2.extras import execute_values

from banco import conectar
from config import TAMANHO_BLOCO


#ignora o aviso do pandas sobre o uso direto do psycopg2
warnings.filterwarnings(
    "ignore",
    message="pandas only supports SQLAlchemy"
)


#funções utilizadas nas conversões

def limpar_texto(coluna):
    """remove espaços e transforma textos vazios em valores nulos."""

    coluna = coluna.str.strip()

    return coluna.where(
        coluna != ""
    )


def texto_para_decimal(coluna):
    """converte valores com vírgula decimal para números."""

    coluna = (
        coluna
        .str.strip()
        .str.replace(
            ",",
            ".",
            regex=False
        )
    )

    return pd.to_numeric(
        coluna,
        errors="coerce"
    )


def texto_para_data(coluna):
    """converte datas no formato dia, mês e ano."""

    return pd.to_datetime(
        coluna.str.strip(),
        format="%d/%m/%Y",
        errors="coerce"
    )


def texto_para_inteiro(coluna):
    """converte uma coluna de texto para valores inteiros."""

    return pd.to_numeric(
        coluna,
        errors="coerce"
    )


#configuração das colunas utilizadas em cada tabela

TABELAS = [
    {
        "raw": "raw_viagem",
        "silver": "silver_viagem",
        "textos": [
            "id_viagem",
            "num_proposta",
            "situacao",
            "viagem_urgente",
            "cod_orgao_superior",
            "nome_orgao_superior",
            "nome_viajante",
            "cargo",
            "destinos",
            "motivo",
        ],
        "valores": [
            "valor_diarias",
            "valor_passagens",
            "valor_devolucao",
            "valor_outros_gastos",
        ],
        "datas": [
            "data_inicio",
            "data_fim",
        ],
        "inteiros": [],
    },
    {
        "raw": "raw_pagamento",
        "silver": "silver_pagamento",
        "textos": [
            "id_viagem",
            "num_proposta",
            "nome_orgao_pagador",
            "nome_ug_pagadora",
            "tipo_pagamento",
        ],
        "valores": [
            "valor",
        ],
        "datas": [],
        "inteiros": [],
    },
    {
        "raw": "raw_passagem",
        "silver": "silver_passagem",
        "textos": [
            "id_viagem",
            "meio_transporte",
            "pais_origem_ida",
            "uf_origem_ida",
            "cidade_origem_ida",
            "pais_destino_ida",
            "uf_destino_ida",
            "cidade_destino_ida",
        ],
        "valores": [
            "valor_passagem",
            "taxa_servico",
        ],
        "datas": [
            "data_emissao",
        ],
        "inteiros": [],
    },
    {
        "raw": "raw_trecho",
        "silver": "silver_trecho",
        "textos": [
            "id_viagem",
            "origem_uf",
            "origem_cidade",
            "destino_uf",
            "destino_cidade",
            "meio_transporte",
        ],
        "valores": [
            "numero_diarias",
        ],
        "datas": [
            "origem_data",
            "destino_data",
        ],
        "inteiros": [
            "sequencia_trecho",
        ],
    },
]


def transformar_bloco(
    bloco,
    configuracao
):
    """
    realiza as conversões necessárias em um bloco de registros.
    """

    for coluna in configuracao["textos"]:
        bloco[coluna] = limpar_texto(
            bloco[coluna]
        )

    for coluna in configuracao["valores"]:
        bloco[coluna] = texto_para_decimal(
            bloco[coluna]
        )

    for coluna in configuracao["datas"]:
        bloco[coluna] = texto_para_data(
            bloco[coluna]
        )

    for coluna in configuracao["inteiros"]:
        bloco[coluna] = texto_para_inteiro(
            bloco[coluna]
        )

    #calcula as duas colunas adicionais da tabela de viagens
    if configuracao["silver"] == "silver_viagem":

        bloco["valor_total"] = (
            bloco["valor_diarias"].fillna(0)
            + bloco["valor_passagens"].fillna(0)
            + bloco["valor_outros_gastos"].fillna(0)
            - bloco["valor_devolucao"].fillna(0)
        ).round(2)

        bloco["duracao_dias"] = (
            bloco["data_fim"]
            - bloco["data_inicio"]
        ).dt.days + 1

    #substitui valores ausentes por none para serem gravados como null
    bloco = bloco.astype(object).where(
        pd.notna(bloco),
        None
    )

    return bloco


def carregar_silver(
    conexao,
    configuracao
):
    """
    lê uma tabela raw em blocos, transforma e grava na silver.
    """

    colunas = (
        configuracao["textos"]
        + configuracao["valores"]
        + configuracao["datas"]
        + configuracao["inteiros"]
    )

    consulta = (
        f"SELECT {', '.join(colunas)} "
        f"FROM {configuracao['raw']};"
    )

    blocos = pd.read_sql_query(
        consulta,
        conexao,
        chunksize=TAMANHO_BLOCO
    )

    total_gravado = 0

    with conexao.cursor() as cursor:

        for bloco in blocos:
            bloco = transformar_bloco(
                bloco,
                configuracao
            )

            linhas = list(
                bloco.itertuples(
                    index=False,
                    name=None
                )
            )

            comando_insert = (
                f"INSERT INTO {configuracao['silver']} "
                f"({', '.join(bloco.columns)}) "
                "VALUES %s"
            )

            execute_values(
                cursor,
                comando_insert,
                linhas
            )

            total_gravado += len(linhas)

            print(
                f"   {total_gravado} registros gravados"
            )

    return total_gravado


def consultar_valor(
    cursor,
    consulta
):
    """executa uma consulta que retorna somente um valor."""

    cursor.execute(
        consulta
    )

    return cursor.fetchone()[0]


def conferir_dados(conexao):
    """
    compara as quantidades e algumas conversões realizadas.
    """

    resultados = []

    with conexao.cursor() as cursor:

        for configuracao in TABELAS:
            tabela_raw = configuracao["raw"]
            tabela_silver = configuracao["silver"]

            quantidade_raw = consultar_valor(
                cursor,
                f"SELECT COUNT(*) FROM {tabela_raw};"
            )

            quantidade_silver = consultar_valor(
                cursor,
                f"SELECT COUNT(*) FROM {tabela_silver};"
            )

            resultados.append(
                (
                    f"{tabela_raw} x {tabela_silver}",
                    quantidade_raw,
                    quantidade_silver
                )
            )

        datas_vazias_raw = consultar_valor(
            cursor,
            """
            SELECT COUNT(*)
            FROM raw_passagem
            WHERE TRIM(data_emissao) = '';
            """
        )

        datas_nulas_silver = consultar_valor(
            cursor,
            """
            SELECT COUNT(*)
            FROM silver_passagem
            WHERE data_emissao IS NULL;
            """
        )

        soma_pagamentos_raw = consultar_valor(
            cursor,
            """
            SELECT SUM(
                REPLACE(
                    NULLIF(TRIM(valor), ''),
                    ',',
                    '.'
                )::NUMERIC
            )
            FROM raw_pagamento;
            """
        )

        soma_pagamentos_silver = consultar_valor(
            cursor,
            """
            SELECT SUM(valor)
            FROM silver_pagamento;
            """
        )

    print("\nConferência Raw x Silver:")

    tudo_correto = True

    for (
        descricao,
        valor_raw,
        valor_silver
    ) in resultados:

        situacao = (
            "OK"
            if valor_raw == valor_silver
            else "DIFERENTE"
        )

        if valor_raw != valor_silver:
            tudo_correto = False

        print(
            f"{descricao:<45} "
            f"{valor_raw:>9} x "
            f"{valor_silver:>9} | "
            f"{situacao}"
        )

    print("\nConferência das datas vazias:")
    print(
        f"Raw: {datas_vazias_raw} | "
        f"Silver: {datas_nulas_silver}"
    )

    print("\nConferência da soma dos pagamentos:")
    print(
        f"Raw: {soma_pagamentos_raw} | "
        f"Silver: {soma_pagamentos_silver}"
    )

    if datas_vazias_raw != datas_nulas_silver:
        tudo_correto = False

    if soma_pagamentos_raw != soma_pagamentos_silver:
        tudo_correto = False

    if not tudo_correto:
        raise RuntimeError(
            "Foram encontradas diferenças entre as camadas Raw e Silver."
        )


def main():
    """executa a transformação completa da camada silver."""

    conexao = None

    try:
        conexao = conectar()

        print(
            "Iniciando a transformação da camada Silver..."
        )

        #esvazia as quatro tabelas no mesmo comando por causa das chaves estrangeiras
        with conexao.cursor() as cursor:
            cursor.execute(
                """
                TRUNCATE TABLE
                    silver_pagamento,
                    silver_passagem,
                    silver_trecho,
                    silver_viagem
                RESTART IDENTITY;
                """
            )

        #a tabela de viagens é carregada primeiro porque é a tabela principal
        for configuracao in TABELAS:

            print(
                f"\nTransformando "
                f"{configuracao['raw']} para "
                f"{configuracao['silver']}..."
            )

            carregar_silver(
                conexao,
                configuracao
            )

        #realiza as conferências antes de confirmar as alterações
        conferir_dados(
            conexao
        )

        conexao.commit()

        print(
            "\nTransformação da camada Silver concluída com sucesso."
        )

    except Exception as erro:
        if conexao is not None:
            conexao.rollback()

        print(
            "\nErro durante a transformação: "
            f"{type(erro).__name__}: {erro}"
        )

    finally:
        if conexao is not None:
            conexao.close()

            print(
                "Conexão com o PostgreSQL encerrada."
            )


if __name__ == "__main__":
    main()