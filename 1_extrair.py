"""
Fase 1 - Extração e carga da camada Raw.

Este script lê os quatro arquivos CSV disponibilizados para o projeto
e carrega os dados originais nas tabelas Raw do PostgreSQL.

Os dados são mantidos como texto, sem limpeza ou conversão nesta etapa.
"""

import csv
from pathlib import Path

from banco import conectar, executar, inserir_em_lote


# Pasta onde estão armazenados os quatro arquivos CSV.
PASTA_DATASET = Path(__file__).parent / "dataset"

# Quantidade de registros inseridos em cada lote.
TAMANHO_LOTE = 5000


# Relaciona cada arquivo CSV com a tabela e às respectivas colunas.
ARQUIVOS = {
    "2025_Viagem.csv": {
        "tabela": "raw_viagem",
        "colunas": [
            "id_viagem",
            "num_proposta",
            "situacao",
            "viagem_urgente",
            "justificativa_urgencia",
            "cod_orgao_superior",
            "nome_orgao_superior",
            "cod_orgao_solicitante",
            "nome_orgao_solicitante",
            "cpf_viajante",
            "nome_viajante",
            "cargo",
            "funcao",
            "descricao_funcao",
            "data_inicio",
            "data_fim",
            "destinos",
            "motivo",
            "valor_diarias",
            "valor_passagens",
            "valor_devolucao",
            "valor_outros_gastos",
        ],
    },
    "2025_Pagamento.csv": {
        "tabela": "raw_pagamento",
        "colunas": [
            "id_viagem",
            "num_proposta",
            "cod_orgao_superior",
            "nome_orgao_superior",
            "cod_orgao_pagador",
            "nome_orgao_pagador",
            "cod_ug_pagadora",
            "nome_ug_pagadora",
            "tipo_pagamento",
            "valor",
        ],
    },
    "2025_Passagem.csv": {
        "tabela": "raw_passagem",
        "colunas": [
            "id_viagem",
            "num_proposta",
            "meio_transporte",
            "pais_origem_ida",
            "uf_origem_ida",
            "cidade_origem_ida",
            "pais_destino_ida",
            "uf_destino_ida",
            "cidade_destino_ida",
            "pais_origem_volta",
            "uf_origem_volta",
            "cidade_origem_volta",
            "pais_destino_volta",
            "uf_destino_volta",
            "cidade_destino_volta",
            "valor_passagem",
            "taxa_servico",
            "data_emissao",
            "hora_emissao",
        ],
    },
    "2025_Trecho.csv": {
        "tabela": "raw_trecho",
        "colunas": [
            "id_viagem",
            "num_proposta",
            "sequencia_trecho",
            "origem_data",
            "origem_pais",
            "origem_uf",
            "origem_cidade",
            "destino_data",
            "destino_pais",
            "destino_uf",
            "destino_cidade",
            "meio_transporte",
            "numero_diarias",
            "missao",
        ],
    },
}


def carregar_arquivo(conexao, nome_arquivo, configuracao):
    """
    Lê um arquivo CSV em lotes e insere os registros na tabela Raw.

    Antes da carga, a tabela é esvaziada com TRUNCATE para evitar
    registros duplicados quando o script for executado novamente.
    """

    caminho = PASTA_DATASET / nome_arquivo
    tabela = configuracao["tabela"]
    colunas = configuracao["colunas"]

    if not caminho.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")

    # Remove os registros da execução anterior.
    executar(conexao, f"TRUNCATE TABLE public.{tabela};")

    nomes_colunas = ", ".join(colunas)
    marcadores = ", ".join(["%s"] * len(colunas))

    sql_insert = (
        f"INSERT INTO public.{tabela} "
        f"({nomes_colunas}) VALUES ({marcadores});"
    )

    total_inserido = 0
    lote = []

    # Os arquivos fornecidos utilizam latin-1 e ponto e vírgula.
    with caminho.open(
        mode="r",
        encoding="latin-1",
        newline="",
    ) as arquivo_csv:

        leitor = csv.reader(arquivo_csv, delimiter=";")

        # Ignora a primeira linha, pois ela contém o cabeçalho.
        next(leitor)

        for numero_linha, linha in enumerate(leitor, start=2):

            # Ignora linhas completamente vazias.
            if not linha or not any(linha):
                continue

            # Confere se a quantidade de valores corresponde à tabela.
            if len(linha) != len(colunas):
                raise ValueError(
                    f"{nome_arquivo}, linha {numero_linha}: "
                    f"esperadas {len(colunas)} colunas, "
                    f"mas foram encontradas {len(linha)}."
                )

            lote.append(tuple(linha))

            # Insere o lote quando atingir o tamanho definido.
            if len(lote) >= TAMANHO_LOTE:
                inserir_em_lote(conexao, sql_insert, lote)
                total_inserido += len(lote)
                lote.clear()

        # Insere o último lote, caso restem registros.
        if lote:
            inserir_em_lote(conexao, sql_insert, lote)
            total_inserido += len(lote)

    print(
        f"{nome_arquivo}: {total_inserido} registros "
        f"inseridos em {tabela}."
    )


def main():
    """Executa a carga dos quatro arquivos na camada Raw."""

    conexao = None

    try:
        print("Iniciando a carga da camada Raw...")

        conexao = conectar()

        for nome_arquivo, configuracao in ARQUIVOS.items():
            carregar_arquivo(
                conexao,
                nome_arquivo,
                configuracao,
            )

        print("Carga da camada Raw concluída com sucesso.")

    except Exception as erro:
        if conexao is not None:
            conexao.rollback()

        print(f"Erro durante a carga da camada Raw: {erro}")

    finally:
        if conexao is not None:
            conexao.close()
            print("Conexão com o PostgreSQL encerrada.")


if __name__ == "__main__":
    main()