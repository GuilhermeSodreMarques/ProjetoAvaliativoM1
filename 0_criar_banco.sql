
-- PROJETO AVALIATIVO - PIPELINE DE DADOS
-- FASE 0: CRIAÇÃO DO BANCO E DAS TABELAS RAW E SILVER
-- Banco utilizado: PostgreSQL


-- Nesta primeira etapa, crio o banco de dados que será utilizado
-- durante todo o desenvolvimento do projeto.
-- Este comando deve ser executado conectado ao banco "postgres".
CREATE DATABASE transparencia;

-- CRIAÇÃO DAS TABELAS
-- A partir deste ponto, os comandos devem ser executados em uma
-- nova Query Tool conectada ao banco "transparencia".

-- Inicio uma transação para que a criação das tabelas seja confirmada
-- somente quando todos os comandos forem executados corretamente.
BEGIN;


-- Verifico se os comandos estão sendo executados no banco correto.
-- Caso a conexão esteja em outro banco, o PostgreSQL apresentará uma
-- mensagem de erro e interromperá a execução.
DO $$
BEGIN
    IF current_database() <> 'transparencia' THEN
        RAISE EXCEPTION 'Abra o Query Tool no banco transparencia.';
    END IF;
END;
$$;



-- CAMADA RAW
-- A camada Raw armazena uma cópia fiel dos arquivos CSV.
-- Por esse motivo, todas as colunas foram criadas como VARCHAR.
-- Nesta camada não são aplicadas chaves ou outras constraints,
-- pois os dados ainda não passaram pelo processo de tratamento.



-- TABELA RAW_VIAGEM
-- Armazena os dados originais do arquivo 2025_Viagem.csv.
-- A tabela possui informações gerais da viagem, do viajante,
-- dos órgãos envolvidos, do período e dos valores apresentados.
CREATE TABLE public.raw_viagem (
    id_viagem VARCHAR,
    num_proposta VARCHAR,
    situacao VARCHAR,
    viagem_urgente VARCHAR,
    justificativa_urgencia VARCHAR,
    cod_orgao_superior VARCHAR,
    nome_orgao_superior VARCHAR,
    cod_orgao_solicitante VARCHAR,
    nome_orgao_solicitante VARCHAR,
    cpf_viajante VARCHAR,
    nome_viajante VARCHAR,
    cargo VARCHAR,
    funcao VARCHAR,
    descricao_funcao VARCHAR,
    data_inicio VARCHAR,
    data_fim VARCHAR,
    destinos VARCHAR,
    motivo VARCHAR,
    valor_diarias VARCHAR,
    valor_passagens VARCHAR,
    valor_devolucao VARCHAR,
    valor_outros_gastos VARCHAR
);



-- TABELA RAW_PAGAMENTO
-- Armazena os dados originais do arquivo 2025_Pagamento.csv.
-- Cada registro representa um pagamento relacionado a uma viagem,
-- incluindo o órgão pagador, a unidade gestora, o tipo e o valor.
CREATE TABLE public.raw_pagamento (
    id_viagem VARCHAR,
    num_proposta VARCHAR,
    cod_orgao_superior VARCHAR,
    nome_orgao_superior VARCHAR,
    cod_orgao_pagador VARCHAR,
    nome_orgao_pagador VARCHAR,
    cod_ug_pagadora VARCHAR,
    nome_ug_pagadora VARCHAR,
    tipo_pagamento VARCHAR,
    valor VARCHAR
);



-- TABELA RAW_PASSAGEM
-- Armazena os dados originais do arquivo 2025_Passagem.csv.
-- A tabela mantém informações de ida e volta, meio de transporte,
-- valor da passagem, taxa de serviço e momento da emissão.
CREATE TABLE public.raw_passagem (
    id_viagem VARCHAR,
    num_proposta VARCHAR,
    meio_transporte VARCHAR,
    pais_origem_ida VARCHAR,
    uf_origem_ida VARCHAR,
    cidade_origem_ida VARCHAR,
    pais_destino_ida VARCHAR,
    uf_destino_ida VARCHAR,
    cidade_destino_ida VARCHAR,
    pais_origem_volta VARCHAR,
    uf_origem_volta VARCHAR,
    cidade_origem_volta VARCHAR,
    pais_destino_volta VARCHAR,
    uf_destino_volta VARCHAR,
    cidade_destino_volta VARCHAR,
    valor_passagem VARCHAR,
    taxa_servico VARCHAR,
    data_emissao VARCHAR,
    hora_emissao VARCHAR
);



-- TABELA RAW_TRECHO
-- Armazena os dados originais do arquivo 2025_Trecho.csv.
-- Cada registro representa um trecho percorrido durante uma viagem,
-- com origem, destino, datas, transporte e número de diárias.
CREATE TABLE public.raw_trecho (
    id_viagem VARCHAR,
    num_proposta VARCHAR,
    sequencia_trecho VARCHAR,
    origem_data VARCHAR,
    origem_pais VARCHAR,
    origem_uf VARCHAR,
    origem_cidade VARCHAR,
    destino_data VARCHAR,
    destino_pais VARCHAR,
    destino_uf VARCHAR,
    destino_cidade VARCHAR,
    meio_transporte VARCHAR,
    numero_diarias VARCHAR,
    missao VARCHAR
);



-- CAMADA SILVER
-- A camada Silver receberá os dados tratados da camada Raw.
-- Nesta camada são aplicados os tipos corretos, como DATE, INT e
-- DECIMAL, além das chaves e constraints necessárias para garantir
-- a qualidade e a integridade dos dados.



-- TABELA SILVER_VIAGEM
-- Esta é a tabela principal da camada Silver.
-- O identificador da viagem foi definido como chave primária.
-- Também foram adicionadas as colunas calculadas valor_total e
-- duracao_dias, que serão preenchidas na fase de transformação.
CREATE TABLE public.silver_viagem (
    id_viagem VARCHAR(20) PRIMARY KEY,
    num_proposta VARCHAR(20),
    situacao VARCHAR(50),
    viagem_urgente VARCHAR(5),
    cod_orgao_superior VARCHAR(20),

    -- O nome do órgão é obrigatório.
    nome_orgao_superior VARCHAR(255) NOT NULL,

    nome_viajante VARCHAR(255),
    cargo VARCHAR(255),
    data_inicio DATE,
    data_fim DATE,
    destinos VARCHAR(4000),
    motivo VARCHAR(4000),
    valor_diarias DECIMAL(10,2),
    valor_passagens DECIMAL(10,2),
    valor_devolucao DECIMAL(10,2),
    valor_outros_gastos DECIMAL(10,2),
    valor_total DECIMAL(12,2),
    duracao_dias INT,

    -- Impede o armazenamento de um valor negativo para as diárias.
    CONSTRAINT ck_viagem_valor_diarias
        CHECK (valor_diarias >= 0)
);



-- TABELA SILVER_PAGAMENTO
-- Armazena os pagamentos tratados.
-- O id_pagamento é gerado automaticamente pelo PostgreSQL.
-- A chave estrangeira relaciona cada pagamento com uma viagem
-- existente na tabela silver_viagem.
CREATE TABLE public.silver_pagamento (
    id_pagamento INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_viagem VARCHAR(20) NOT NULL,
    num_proposta VARCHAR(20),
    nome_orgao_pagador VARCHAR(255),
    nome_ug_pagadora VARCHAR(255),

    -- Todo pagamento deve possuir um tipo informado.
    tipo_pagamento VARCHAR(50) NOT NULL,

    valor DECIMAL(10,2),

    -- Relaciona o pagamento com a sua respectiva viagem.
    CONSTRAINT fk_pagamento_viagem
        FOREIGN KEY (id_viagem)
        REFERENCES public.silver_viagem (id_viagem),

    -- Impede pagamentos com valores negativos.
    CONSTRAINT ck_pagamento_valor
        CHECK (valor >= 0)
);



-- TABELA SILVER_PASSAGEM
-- Armazena os dados tratados das passagens.
-- Cada passagem possui um identificador gerado automaticamente
-- e fica relacionada a uma viagem da tabela silver_viagem.
CREATE TABLE public.silver_passagem (
    id_passagem INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_viagem VARCHAR(20) NOT NULL,
    meio_transporte VARCHAR(50),
    pais_origem_ida VARCHAR(60),
    uf_origem_ida VARCHAR(40),
    cidade_origem_ida VARCHAR(80),
    pais_destino_ida VARCHAR(60),
    uf_destino_ida VARCHAR(40),
    cidade_destino_ida VARCHAR(80),
    valor_passagem DECIMAL(10,2),
    taxa_servico DECIMAL(10,2),
    data_emissao DATE,

    -- Relaciona a passagem com a sua respectiva viagem.
    CONSTRAINT fk_passagem_viagem
        FOREIGN KEY (id_viagem)
        REFERENCES public.silver_viagem (id_viagem),

    -- Impede valores negativos no preço da passagem.
    CONSTRAINT ck_passagem_valor
        CHECK (valor_passagem >= 0),

    -- Impede valores negativos na taxa de serviço.
    CONSTRAINT ck_passagem_taxa
        CHECK (taxa_servico >= 0)
);



-- TABELA SILVER_TRECHO
-- Armazena os trechos tratados das viagens.
-- A combinação entre a viagem e a sequência do trecho deve ser
-- única, evitando que um mesmo trecho seja incluído mais de uma vez.
CREATE TABLE public.silver_trecho (
    id_trecho INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    id_viagem VARCHAR(20) NOT NULL,
    sequencia_trecho INT,
    origem_data DATE,
    origem_uf VARCHAR(40),
    origem_cidade VARCHAR(80),
    destino_data DATE,
    destino_uf VARCHAR(40),
    destino_cidade VARCHAR(80),
    meio_transporte VARCHAR(50),
    numero_diarias DECIMAL(10,2),

    -- Relaciona o trecho com a sua respectiva viagem.
    CONSTRAINT fk_trecho_viagem
        FOREIGN KEY (id_viagem)
        REFERENCES public.silver_viagem (id_viagem),

    -- Impede o armazenamento de um número negativo de diárias.
    CONSTRAINT ck_trecho_numero_diarias
        CHECK (numero_diarias >= 0),

    -- Impede sequências repetidas dentro da mesma viagem.
    CONSTRAINT uq_trecho_viagem_sequencia
        UNIQUE (id_viagem, sequencia_trecho)
);


-- Confirmo a transação após a criação das oito tabelas.
COMMIT;



-- CONFERÊNCIA DAS TABELAS CRIADAS
-- Ao final, realizo uma consulta no catálogo do PostgreSQL para
-- conferir se as oito tabelas foram criadas e verificar a quantidade
-- de colunas presente em cada uma delas.
SELECT
    t.table_name,
    COUNT(c.column_name) AS quantidade_colunas
FROM information_schema.tables AS t
JOIN information_schema.columns AS c
    ON c.table_catalog = t.table_catalog
    AND c.table_schema = t.table_schema
    AND c.table_name = t.table_name
WHERE t.table_schema = 'public'
  AND t.table_type = 'BASE TABLE'
  AND t.table_name IN (
      'raw_viagem',
      'raw_pagamento',
      'raw_passagem',
      'raw_trecho',
      'silver_viagem',
      'silver_pagamento',
      'silver_passagem',
      'silver_trecho'
  )
GROUP BY t.table_name
ORDER BY t.table_name;