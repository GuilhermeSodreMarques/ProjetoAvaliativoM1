"""
Fase 2 - Transformação da camada Raw para Silver.

Aqui os dados armazenados como texto na camada Raw são
limpos, convertidos e inseridos nas tabelas da camada Silver.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from banco import conectar, executar, inserir_em_lote


#define quantos registros serão processados por vez
TAMANHO_LOTE = 5000


def limpar_texto(valor):
    """
    Remove espaços antes e depois do texto.

    Campos vazios são convertidos para None, que representa
    NULL no PostgreSQL.
    """

    if valor is None:
        return None

    valor = valor.strip()

    return valor if valor else None


def converter_decimal(valor):
    """
    Converte valores no formato brasileiro para Decimal.

    Exemplo:
    "1.272,97" será convertido para Decimal("1272.97").
    """

    valor = limpar_texto(valor)

    if valor is None:
        return None

    # Remove símbolo de moeda e espaços.
    valor = valor.replace("R$", "").replace(" ", "")

    # Remove separador de milhar e ajusta o separador decimal.
    valor = valor.replace(".", "").replace(",", ".")

    try:
        return Decimal(valor)

    except InvalidOperation as erro:
        raise ValueError(
            f"Não foi possível converter '{valor}' para decimal."
        ) from erro


def converter_data(valor):
    """
    Converte uma data DD/MM/AAAA para o tipo date do Python.
    """

    valor = limpar_texto(valor)

    if valor is None:
        return None

    try:
        return datetime.strptime(valor, "%d/%m/%Y").date()

    except ValueError as erro:
        raise ValueError(
            f"Não foi possível converter a data '{valor}'."
        ) from erro


def converter_inteiro(valor):
    """
    Converte um texto para número inteiro.
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
    Converte os registros da raw_viagem e os insere na silver_viagem.

    Também calcula o valor total e a duração de cada viagem.
    """

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

            data_inicio = converter_data(data_inicio_texto)
            data_fim = converter_data(data_fim_texto)

            valor_diarias = converter_decimal(valor_diarias_texto)
            valor_passagens = converter_decimal(valor_passagens_texto)
            valor_devolucao = converter_decimal(valor_devolucao_texto)
            valor_outros = converter_decimal(valor_outros_texto)

            # Nos cálculos, campos vazios são considerados como zero.
            total_diarias = valor_diarias or Decimal("0")
            total_passagens = valor_passagens or Decimal("0")
            total_devolucao = valor_devolucao or Decimal("0")
            total_outros = valor_outros or Decimal("0")

            # O valor devolvido é descontado do custo da viagem.
            valor_total = (
                total_diarias
                + total_passagens
                + total_outros
                - total_devolucao
            )

            # A duração inclui o primeiro e o último dia.
            if data_inicio is not None and data_fim is not None:
                duracao_dias = (data_fim - data_inicio).days + 1
            else:
                duracao_dias = None

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