"""
Fase 2 - Transformação da camada Raw para Silver.

Aqui os dados armazenados como texto na camada Raw são
limpos, convertidos e inseridos nas tabelas da camada Silver.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from banco import conectar, executar, inserir_em_lote


#Quantidade de registros que serão processados por vez
TAMANHO_LOTE = 5000

#Formato utilizado nas datas dos arquivos CSV
FORMATO_DATA = "%d/%m/%Y"


def limpar_texto(valor):
    """
    Remove espaços antes e depois dos textos.

    Quando o campo estiver vazio retorna None para que o PostgreSQL
    armazene o valor como NULL
    """

    if valor is None:
        return None

    valor = valor.strip()

    return valor if valor else None


def converter_decimal(valor):
    """
    Converte valores no formato brasileiro para decimal 
    """

    valor = limpar_texto(valor)

    if valor is None:
        return None

    #Retira o simbolo da moeda e os espaços
    valor = valor.replace("R$", "").replace(" ", "")

    # Retira o ponto de milhar e troca a vírgula decimal por ponto.
    valor = valor.replace(".", "").replace(",", ".")

    try:
        return Decimal(valor)

    except InvalidOperation as erro:
        raise ValueError(
            f"Não foi possível converter '{valor}' para decimal."
        ) from erro


def converter_data(valor):
    """
    Converte a data que veio como texto para o formato de data do Python

    Quando o campo estiver vazio retorna None
    """

    valor = limpar_texto(valor)

    if valor is None:
        return None

    try:
        return datetime.strptime(valor, FORMATO_DATA).date()

    except ValueError as erro:
        raise ValueError(
            f"Não foi possível converter a data '{valor}'."
        ) from erro


def converter_inteiro(valor):
    """
    Converte um valor de texto para número inteiro.

    Essa função é usada na sequência dos trechos.
    """

    valor = limpar_texto(valor)

    if valor is None:
        return None

    try:
        return int(valor)

    except ValueError as erro:
        raise ValueError(
            f"Não foi possível converter '{valor}' para inteiro."
        ) from erro


def transformar_viagens(conexao):
    """
    Lê os registros da raw_viagem, faz as conversões necessárias
    e insere os resultados na silver_viagem.

    Também calcula o valor total e a duração de cada viagem.
    """

    #consulta os campos da tabela Raw que serão usados na Silver
    sql_select = """
        SELECT
            id_viagem,
            num_proposta,
            situacao,
            viagem_urgente,
            cod_orgao_superior,
            nome_orgao_superior,
            nome_viajante,
            cargo,
            data_inicio,
            data_fim,
            destinos,
            motivo,
            valor_diarias,
            valor_passagens,
            valor_devolucao,
            valor_outros_gastos
        FROM public.raw_viagem;
    """

    #comando utilizado para inserir os dados tratados na Silver
    sql_insert = """
        INSERT INTO public.silver_viagem (
            id_viagem,
            num_proposta,
            situacao,
            viagem_urgente,
            cod_orgao_superior,
            nome_orgao_superior,
            nome_viajante,
            cargo,
            data_inicio,
            data_fim,
            destinos,
            motivo,
            valor_diarias,
            valor_passagens,
            valor_devolucao,
            valor_outros_gastos,
            valor_total,
            duracao_dias
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s, %s
        );
    """

    cursor = conexao.cursor()
    cursor.execute(sql_select)

    total_inserido = 0

    #repete o processo enquanto ainda existirem registros na Raw
    while True:
        registros = cursor.fetchmany(TAMANHO_LOTE)

        if not registros:
            break

        lote = []

        for registro in registros:
            (
                id_viagem,
                num_proposta,
                situacao,
                viagem_urgente,
                cod_orgao_superior,
                nome_orgao_superior,
                nome_viajante,
                cargo,
                data_inicio_texto,
                data_fim_texto,
                destinos,
                motivo,
                valor_diarias_texto,
                valor_passagens_texto,
                valor_devolucao_texto,
                valor_outros_texto,
            ) = registro

            #converte as datas que estavam armazenadas como texto
            data_inicio = converter_data(data_inicio_texto)
            data_fim = converter_data(data_fim_texto)

            #converte os valores que estão em moeda para decimal
            valor_diarias = converter_decimal(valor_diarias_texto)
            valor_passagens = converter_decimal(valor_passagens_texto)
            valor_devolucao = converter_decimal(valor_devolucao_texto)
            valor_outros = converter_decimal(valor_outros_texto)

            #para realizar o cálculo os campos vazios são considerados zero
            total_diarias = valor_diarias or Decimal("0")
            total_passagens = valor_passagens or Decimal("0")
            total_devolucao = valor_devolucao or Decimal("0")
            total_outros = valor_outros or Decimal("0")

            #soma os gastos e desconta o valor devolvido
            valor_total = (
                total_diarias
                + total_passagens
                + total_outros
                - total_devolucao
            )

            #calcula a duração incluindo o primeiro e o ultimo dia
            if data_inicio is not None and data_fim is not None:
                duracao_dias = (data_fim - data_inicio).days + 1
            else:
                duracao_dias = None

            #organiza os valores na mesma ordem das colunas do INSERT
            linha_tratada = (
                limpar_texto(id_viagem),
                limpar_texto(num_proposta),
                limpar_texto(situacao),
                limpar_texto(viagem_urgente),
                limpar_texto(cod_orgao_superior),
                limpar_texto(nome_orgao_superior),
                limpar_texto(nome_viajante),
                limpar_texto(cargo),
                data_inicio,
                data_fim,
                limpar_texto(destinos),
                limpar_texto(motivo),
                valor_diarias,
                valor_passagens,
                valor_devolucao,
                valor_outros,
                valor_total,
                duracao_dias,
            )

            lote.append(linha_tratada)

        #insere o lote tratado no PostgreSQL
        inserir_em_lote(conexao, sql_insert, lote)
        total_inserido += len(lote)

        print(
            f"silver_viagem: {total_inserido} registros processados.",
            end="\r",
        )

    cursor.close()

    print(
        f"silver_viagem: {total_inserido} registros inseridos.      "
    )
    

def transformar_pagamentos(conexao):
    """
    Lê os pagamentos da camada Raw, converte os valores e insere
    os registros tratados na silver_pagamento
    """

    #o JOIN seleciona apenas pagamentos ligados a viagens
    #existentes na tabela silver_viagem
    sql_select = """
        SELECT
            rp.id_viagem,
            rp.num_proposta,
            rp.nome_orgao_pagador,
            rp.nome_ug_pagadora,
            rp.tipo_pagamento,
            rp.valor
        FROM public.raw_pagamento AS rp
        INNER JOIN public.silver_viagem AS sv
            ON sv.id_viagem = TRIM(rp.id_viagem);
    """

    sql_insert = """
        INSERT INTO public.silver_pagamento (
            id_viagem,
            num_proposta,
            nome_orgao_pagador,
            nome_ug_pagadora,
            tipo_pagamento,
            valor
        )
        VALUES (%s, %s, %s, %s, %s, %s);
    """

    cursor = conexao.cursor()
    cursor.execute(sql_select)

    total_inserido = 0

    while True:
        registros = cursor.fetchmany(TAMANHO_LOTE)

        if not registros:
            break

        lote = []

        for registro in registros:
            (
                id_viagem,
                num_proposta,
                nome_orgao_pagador,
                nome_ug_pagadora,
                tipo_pagamento,
                valor_texto,
            ) = registro

            linha_tratada = (
                limpar_texto(id_viagem),
                limpar_texto(num_proposta),
                limpar_texto(nome_orgao_pagador),
                limpar_texto(nome_ug_pagadora),
                limpar_texto(tipo_pagamento),
                converter_decimal(valor_texto),
            )

            lote.append(linha_tratada)

        inserir_em_lote(conexao, sql_insert, lote)
        total_inserido += len(lote)

        print(
            f"silver_pagamento: {total_inserido} registros processados.",
            end="\r",
        )

    cursor.close()

    print(
        f"silver_pagamento: {total_inserido} registros inseridos.      "
    )


def transformar_passagens(conexao):
    """
    Lê as passagens da camada Raw converte os valores e a data
    de emissão e insere os registros na silver_passagem
    """

    #o JOIN seleciona somente passagens ligadas a viagens
    #existentes na tabela silver_viagem
    sql_select = """
        SELECT
            rp.id_viagem,
            rp.meio_transporte,
            rp.pais_origem_ida,
            rp.uf_origem_ida,
            rp.cidade_origem_ida,
            rp.pais_destino_ida,
            rp.uf_destino_ida,
            rp.cidade_destino_ida,
            rp.valor_passagem,
            rp.taxa_servico,
            rp.data_emissao
        FROM public.raw_passagem AS rp
        INNER JOIN public.silver_viagem AS sv
            ON sv.id_viagem = TRIM(rp.id_viagem);
    """

    sql_insert = """
        INSERT INTO public.silver_passagem (
            id_viagem,
            meio_transporte,
            pais_origem_ida,
            uf_origem_ida,
            cidade_origem_ida,
            pais_destino_ida,
            uf_destino_ida,
            cidade_destino_ida,
            valor_passagem,
            taxa_servico,
            data_emissao
        )
        VALUES (
            %s, %s, %s, %s, %s, %s,
            %s, %s, %s, %s, %s
        );
    """

    cursor = conexao.cursor()
    cursor.execute(sql_select)

    total_inserido = 0

    while True:
        registros = cursor.fetchmany(TAMANHO_LOTE)

        if not registros:
            break

        lote = []

        for registro in registros:
            (
                id_viagem,
                meio_transporte,
                pais_origem_ida,
                uf_origem_ida,
                cidade_origem_ida,
                pais_destino_ida,
                uf_destino_ida,
                cidade_destino_ida,
                valor_passagem_texto,
                taxa_servico_texto,
                data_emissao_texto,
            ) = registro

            linha_tratada = (
                limpar_texto(id_viagem),
                limpar_texto(meio_transporte),
                limpar_texto(pais_origem_ida),
                limpar_texto(uf_origem_ida),
                limpar_texto(cidade_origem_ida),
                limpar_texto(pais_destino_ida),
                limpar_texto(uf_destino_ida),
                limpar_texto(cidade_destino_ida),
                converter_decimal(valor_passagem_texto),
                converter_decimal(taxa_servico_texto),
                converter_data(data_emissao_texto),
            )

            lote.append(linha_tratada)

        inserir_em_lote(conexao, sql_insert, lote)
        total_inserido += len(lote)

        print(
            f"silver_passagem: {total_inserido} registros processados.",
            end="\r",
        )

    cursor.close()

    print(
        f"silver_passagem: {total_inserido} registros inseridos.      "
    )


def transformar_trechos(conexao):
    """
    Converte os trechos da camada Raw e os insere na Silver

    A sequencia é convertida para inteiro, as datas para date e
    o número de diárias para decimal
    """

    sql_select = """
        SELECT
            rt.id_viagem,
            rt.sequencia_trecho,
            rt.origem_data,
            rt.origem_uf,
            rt.origem_cidade,
            rt.destino_data,
            rt.destino_uf,
            rt.destino_cidade,
            rt.meio_transporte,
            rt.numero_diarias
        FROM public.raw_trecho AS rt
        INNER JOIN public.silver_viagem AS sv
            ON sv.id_viagem = TRIM(rt.id_viagem);
    """

    sql_insert = """
        INSERT INTO public.silver_trecho (
            id_viagem,
            sequencia_trecho,
            origem_data,
            origem_uf,
            origem_cidade,
            destino_data,
            destino_uf,
            destino_cidade,
            meio_transporte,
            numero_diarias
        )
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s);
    """

    cursor = conexao.cursor()
    cursor.execute(sql_select)

    total_inserido = 0

    while True:
        registros = cursor.fetchmany(TAMANHO_LOTE)

        if not registros:
            break

        lote = []

        for registro in registros:
            (
                id_viagem,
                sequencia_trecho,
                origem_data_texto,
                origem_uf,
                origem_cidade,
                destino_data_texto,
                destino_uf,
                destino_cidade,
                meio_transporte,
                numero_diarias_texto,
            ) = registro

            linha_tratada = (
                limpar_texto(id_viagem),
                converter_inteiro(sequencia_trecho),
                converter_data(origem_data_texto),
                limpar_texto(origem_uf),
                limpar_texto(origem_cidade),
                converter_data(destino_data_texto),
                limpar_texto(destino_uf),
                limpar_texto(destino_cidade),
                limpar_texto(meio_transporte),
                converter_decimal(numero_diarias_texto),
            )

            lote.append(linha_tratada)

        inserir_em_lote(conexao, sql_insert, lote)
        total_inserido += len(lote)

        print(
            f"silver_trecho: {total_inserido} registros processados.",
            end="\r",
        )

    cursor.close()

    print(
        f"silver_trecho: {total_inserido} registros inseridos.      "
    )


def main():
    """
    Executa a transformação completa da camada Raw para Silver.
    """

    conexao = None

    try:
        print("Iniciando a transformação da camada Silver...")

        conexao = conectar()

        #esvazia todas as tabelas Silver e reinicia os IDs automáticos
        #as quatro tabelas são truncadas juntas por causa das chaves
        #estrangeiras existentes entre elas
        executar(
            conexao,
            """
            TRUNCATE TABLE
                public.silver_pagamento,
                public.silver_passagem,
                public.silver_trecho,
                public.silver_viagem
            RESTART IDENTITY;
            """,
        )

        #as viagens são carregadas primeiro porque as outras tabelas
        #dependem delas através da chave estrangeira
        transformar_viagens(conexao)

        #as tabelas abaixo possuem chave estrangeira para silver_viagem
        transformar_pagamentos(conexao)
        transformar_passagens(conexao)
        transformar_trechos(conexao)

        print("Transformação da camada Silver concluída com sucesso.")

    except Exception as erro:
        if conexao is not None:
            conexao.rollback()

        print(f"Erro durante a transformação: {erro}")

    finally:
        if conexao is not None:
            conexao.close()
            print("Conexão com o PostgreSQL encerrada.")


if __name__ == "__main__":
    main()