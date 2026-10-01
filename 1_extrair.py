"""
1_extrair.py

fase 1 do projeto: download dos arquivos e carga da camada raw.

o script baixa o arquivo zip do google drive, extrai os quatro
arquivos csv e carrega os dados nas tabelas raw do postgresql.

os arquivos são processados em blocos para evitar o uso excessivo
de memória. os dados são mantidos como texto nesta etapa.
"""

import zipfile

import pandas as pd
import requests

from psycopg2.extras import execute_values

from banco import conectar
from config import (
    ARQUIVOS,
    CSV_ENCODING,
    CSV_SEPARADOR,
    DRIVE_FILE_ID,
    PASTA_DADOS,
    TAMANHO_BLOCO,
)


def baixar_dados():
    """
    baixa o arquivo zip e extrai os csvs na pasta data.
    se os quatro arquivos já existirem, o download não é repetido.
    """

    nomes_arquivos = [
        dados["csv"]
        for dados in ARQUIVOS.values()
    ]

    arquivos_existentes = all(
        (PASTA_DADOS / nome).exists()
        for nome in nomes_arquivos
    )

    if arquivos_existentes:
        print(
            "Os quatro arquivos CSV já estão na pasta data. "
            "O download não será repetido."
        )
        return

    if not DRIVE_FILE_ID:
        raise RuntimeError(
            "O identificador do arquivo do Google Drive "
            "não foi informado no config.py."
        )

    #cria a pasta data caso ela ainda não exista
    PASTA_DADOS.mkdir(
        parents=True,
        exist_ok=True
    )

    caminho_zip = (
        PASTA_DADOS
        / "viagens_2025_6meses.zip"
    )

    url_download = (
        "https://drive.usercontent.google.com/download"
        f"?id={DRIVE_FILE_ID}"
        "&export=download"
        "&confirm=t"
    )

    print("Baixando o arquivo ZIP do Google Drive...")

    #baixa o arquivo aos poucos para não carregar tudo na memória
    with requests.get(
        url_download,
        stream=True,
        timeout=120
    ) as resposta:

        resposta.raise_for_status()

        with caminho_zip.open("wb") as arquivo_zip:
            for parte in resposta.iter_content(
                chunk_size=1024 * 1024
            ):
                if parte:
                    arquivo_zip.write(parte)

    if not zipfile.is_zipfile(caminho_zip):
        raise RuntimeError(
            "O arquivo baixado não é um ZIP válido. "
            "Confira o compartilhamento do arquivo no Google Drive."
        )

    print("Descompactando os arquivos CSV...")

    with zipfile.ZipFile(caminho_zip) as arquivo_zip:
        arquivo_zip.extractall(
            PASTA_DADOS
        )

    #move os csvs para a pasta data caso o zip possua uma subpasta
    caminhos_csv = list(
        PASTA_DADOS.rglob("*.csv")
    )

    for caminho_csv in caminhos_csv:
        if caminho_csv.parent != PASTA_DADOS:
            destino = (
                PASTA_DADOS
                / caminho_csv.name
            )

            caminho_csv.replace(
                destino
            )

    #confere se os quatro arquivos esperados foram encontrados
    arquivos_faltando = [
        nome
        for nome in nomes_arquivos
        if not (PASTA_DADOS / nome).exists()
    ]

    if arquivos_faltando:
        raise FileNotFoundError(
            "Os seguintes arquivos não foram encontrados: "
            + ", ".join(arquivos_faltando)
        )

    print("Os quatro arquivos CSV estão prontos para uso.")


def carregar_raw(
    conexao,
    nome_csv,
    tabela
):
    """
    esvazia uma tabela raw e carrega o arquivo csv em blocos.
    nenhuma limpeza ou conversão é realizada nesta fase.
    """

    caminho_csv = (
        PASTA_DADOS
        / nome_csv
    )

    if not caminho_csv.exists():
        raise FileNotFoundError(
            f"Arquivo não encontrado: {caminho_csv}"
        )

    total_carregado = 0

    with conexao.cursor() as cursor:

        #remove os dados da execução anterior
        cursor.execute(
            f"TRUNCATE TABLE {tabela};"
        )

        blocos = pd.read_csv(
            caminho_csv,
            sep=CSV_SEPARADOR,
            encoding=CSV_ENCODING,
            dtype=str,
            keep_default_na=False,
            chunksize=TAMANHO_BLOCO
        )

        #cada bloco é inserido antes da leitura do próximo
        for bloco in blocos:
            linhas = list(
                bloco.itertuples(
                    index=False,
                    name=None
                )
            )

            execute_values(
                cursor,
                f"INSERT INTO {tabela} VALUES %s",
                linhas
            )

            total_carregado += len(linhas)

            print(
                f"   {total_carregado} registros carregados"
            )

    return total_carregado


def contar_registros(
    conexao,
    tabela
):
    """consulta a quantidade de registros existente na tabela."""

    with conexao.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) FROM {tabela};"
        )

        return cursor.fetchone()[0]


def main():
    """executa o download e a carga das quatro tabelas raw."""

    conexao = None

    try:
        baixar_dados()

        conexao = conectar()

        resultados = []

        print("\nIniciando a carga da camada Raw...")

        for dados in ARQUIVOS.values():
            nome_csv = dados["csv"]
            tabela = dados["tabela_raw"]

            print(
                f"\nCarregando {nome_csv} em {tabela}..."
            )

            total_csv = carregar_raw(
                conexao,
                nome_csv,
                tabela
            )

            #confirma a carga da tabela atual
            conexao.commit()

            total_tabela = contar_registros(
                conexao,
                tabela
            )

            resultados.append(
                (
                    tabela,
                    total_csv,
                    total_tabela
                )
            )

        print(
            "\nCarga da camada Raw concluída com sucesso."
        )

        print("\nConferência dos registros:")

        for (
            tabela,
            total_csv,
            total_tabela
        ) in resultados:

            situacao = (
                "OK"
                if total_csv == total_tabela
                else "DIFERENTE"
            )

            print(
                f"{tabela:<20} "
                f"{total_csv:>9} lidos | "
                f"{total_tabela:>9} inseridos | "
                f"{situacao}"
            )

    except Exception as erro:
        if conexao is not None:
            conexao.rollback()

        print(
            "\nErro durante a extração ou carga: "
            f"{type(erro).__name__}: {erro}"
        )

    finally:
        if conexao is not None:
            conexao.close()

            print(
                "\nConexão com o PostgreSQL encerrada."
            )


if __name__ == "__main__":
    main()