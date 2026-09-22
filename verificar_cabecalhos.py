
#utilizei esse código para descobrir os cabeçalhos dos arquivos CSV antes da criação da tabelas da camada Raw.

import csv
from pathlib import Path
#procura todos os arquivos CSV de 2025 dentro do projeto
for arquivo in Path(".").rglob("2025_*.csv"):
    with arquivo.open(encoding="latin-1", newline="") as csv_file:   #abre o arquivo con encoding e o saparador utilizados na base
        cabecalho = next(csv.reader(csv_file, delimiter=";"))   #le somente a primeira linha correspondente ao cabeçalho

    print(f"\nARQUIVO: {arquivo.name}")
    print(cabecalho)
    
    #Observação: Não foi utilizado o encondig="utf-8" pois ocorreu o erro UnicodeDecoderError: 'utf-8' codec can't decode byte.