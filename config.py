"""
config.py

Este arquivo reúne as configurações utilizadas pelos scripts do projeto.
As credenciais do PostgreSQL são lidas do arquivo .env.
"""

import os
from pathlib import Path


#pasta principal do projeto
PASTA_RAIZ = Path(__file__).resolve().parent

#pasta onde os arquivos CSV serão armazenados
PASTA_DADOS = PASTA_RAIZ / "dataset"


def carregar_env():
    """faz a leitura das informações existentes no arquivo .env."""

    arquivo_env = PASTA_RAIZ / ".env"

    if not arquivo_env.exists():
        return

    linhas = arquivo_env.read_text(
        encoding="utf-8"
    ).splitlines()

    for linha in linhas:
        linha = linha.strip()

        # Ignora linhas vazias e comentários
        if (
            not linha
            or linha.startswith("#")
            or "=" not in linha
        ):
            continue

        chave, valor = linha.split("=", 1)

        os.environ.setdefault(
            chave.strip(),
            valor.strip()
        )


#carrega as variáveis antes de montar a configuração
carregar_env()


#configurações utilizadas na conexão com o PostgreSQL
POSTGRES_CONFIG = {
    "host": os.environ.get(
        "POSTGRES_HOST",
        "localhost"
    ),
    "port": int(
        os.environ.get(
            "POSTGRES_PORT",
            "5432"
        )
    ),
    "user": os.environ.get(
        "POSTGRES_USER",
        "postgres"
    ),
    "password": os.environ.get(
        "POSTGRES_PASSWORD",
        ""
    ),
    "dbname": os.environ.get(
        "POSTGRES_DATABASE",
        "transparencia"
    ),
}


#ano dos arquivos utilizados no projeto
ANO = "2025"

#identificador do arquivo ZIP disponibilizado no Google Drive
DRIVE_FILE_ID = "1R6re1574aCeqNfwJXQ_T7BwHCEsPfgvc"

# Quantidade de registros processados de cada vez
TAMANHO_BLOCO = 50_000


#relaciona os arquivos CSV com suas tabelas Raw
ARQUIVOS = {
    "viagem": {
        "csv": f"{ANO}_Viagem.csv",
        "tabela_raw": "public.raw_viagem",
    },
    "pagamento": {
        "csv": f"{ANO}_Pagamento.csv",
        "tabela_raw": "public.raw_pagamento",
    },
    "passagem": {
        "csv": f"{ANO}_Passagem.csv",
        "tabela_raw": "public.raw_passagem",
    },
    "trecho": {
        "csv": f"{ANO}_Trecho.csv",
        "tabela_raw": "public.raw_trecho",
    },
}


#Características dos arquivos CSV
CSV_SEPARADOR = ";"
CSV_ENCODING = "latin-1"