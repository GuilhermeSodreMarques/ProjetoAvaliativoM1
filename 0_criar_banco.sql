-- 0_criar_banco.sql
-- Fase 0: criação do banco e das tabelas Raw e Silver

-- O arquivo possui duas partes:
-- Parte 1: criação do banco de dados.
-- Parte 2: criação das oito tabelas do projeto.

-- -----------------------------------------------------------------------------
-- PARTE 1
-- Executar conectado ao banco postgres.
-- -----------------------------------------------------------------------------

CREATE DATABASE transparencia;


-- -----------------------------------------------------------------------------
-- PARTE 2
-- Executar conectado ao banco transparencia.
-- -----------------------------------------------------------------------------


-- Remove os objetos da camada Gold, caso já tenham sido criados pelo notebook.

DROP VIEW IF EXISTS vw_gold_pagamento_resumo;
DROP VIEW IF EXISTS vw_gold_trecho_resumo;

DROP TABLE IF EXISTS gold_pagamento_resumo;
DROP TABLE IF EXISTS gold_trecho_resumo;


-- remove as tabelas Silver.
-- as tabelas filhas são removidas antes da tabela silver_viagem.

DROP TABLE IF EXISTS silver_pagamento;
DROP TABLE IF EXISTS silver_passagem;
DROP TABLE IF EXISTS silver_trecho;
DROP TABLE IF EXISTS silver_viagem;


--remove as tabelas Raw.

DROP TABLE IF EXISTS raw_pagamento;
DROP TABLE IF EXISTS raw_passagem;
DROP TABLE IF EXISTS raw_trecho;
DROP TABLE IF EXISTS raw_viagem;


-- CAMADA RAW
--os dados são armazenados como vieram dos arquivos CSV.
--todas as colunas são VARCHAR e não possuem constraints.
--a ordem das colunas é a mesma encontrada nos arquivos.

--dados gerais das viagens

CREATE TABLE raw_viagem (
    id_viagem              VARCHAR(255),
    num_proposta           VARCHAR(255),
    situacao               VARCHAR(255),
    viagem_urgente         VARCHAR(255),
    justificativa_urgencia VARCHAR(4000),
    cod_orgao_superior     VARCHAR(255),
    nome_orgao_superior    VARCHAR(255),
    cod_orgao_solicitante  VARCHAR(255),
    nome_orgao_solicitante VARCHAR(255),
    cpf_viajante           VARCHAR(255),
    nome_viajante          VARCHAR(255),
    cargo                  VARCHAR(255),
    funcao                 VARCHAR(255),
    descricao_funcao       VARCHAR(255),
    data_inicio            VARCHAR(255),
    data_fim               VARCHAR(255),
    destinos               VARCHAR(4000),
    motivo                 VARCHAR(4000),
    valor_diarias          VARCHAR(255),
    valor_passagens        VARCHAR(255),
    valor_devolucao        VARCHAR(255),
    valor_outros_gastos    VARCHAR(255)
);


--dados dos pagamentos

CREATE TABLE raw_pagamento (
    id_viagem           VARCHAR(255),
    num_proposta        VARCHAR(255),
    cod_orgao_superior  VARCHAR(255),
    nome_orgao_superior VARCHAR(255),
    cod_orgao_pagador   VARCHAR(255),
    nome_orgao_pagador  VARCHAR(255),
    cod_ug_pagadora     VARCHAR(255),
    nome_ug_pagadora    VARCHAR(255),
    tipo_pagamento      VARCHAR(255),
    valor               VARCHAR(255)
);


--dados das passagens

CREATE TABLE raw_passagem (
    id_viagem            VARCHAR(255),
    num_proposta         VARCHAR(255),
    meio_transporte      VARCHAR(255),
    pais_origem_ida      VARCHAR(255),
    uf_origem_ida        VARCHAR(255),
    cidade_origem_ida    VARCHAR(255),
    pais_destino_ida     VARCHAR(255),
    uf_destino_ida       VARCHAR(255),
    cidade_destino_ida   VARCHAR(255),
    pais_origem_volta    VARCHAR(255),
    uf_origem_volta      VARCHAR(255),
    cidade_origem_volta  VARCHAR(255),
    pais_destino_volta   VARCHAR(255),
    uf_destino_volta     VARCHAR(255),
    cidade_destino_volta VARCHAR(255),
    valor_passagem       VARCHAR(255),
    taxa_servico         VARCHAR(255),
    data_emissao         VARCHAR(255),
    hora_emissao         VARCHAR(255)
);


--dados dos trechos percorridos

CREATE TABLE raw_trecho (
    id_viagem        VARCHAR(255),
    num_proposta     VARCHAR(255),
    sequencia_trecho VARCHAR(255),
    origem_data      VARCHAR(255),
    origem_pais      VARCHAR(255),
    origem_uf        VARCHAR(255),
    origem_cidade    VARCHAR(255),
    destino_data     VARCHAR(255),
    destino_pais     VARCHAR(255),
    destino_uf       VARCHAR(255),
    destino_cidade   VARCHAR(255),
    meio_transporte  VARCHAR(255),
    numero_diarias   VARCHAR(255),
    missao           VARCHAR(255)
);


-- CAMADA SILVER
--nesta camada os dados possuem tipos corretos e regras de integridade.
--a silver_viagem é criada primeiro porque as outras tabelas dependem dela.

--dados tratados das viagens

CREATE TABLE silver_viagem (
    id_viagem           VARCHAR(20) NOT NULL,
    num_proposta        VARCHAR(20),
    situacao            VARCHAR(50),
    viagem_urgente      VARCHAR(5),
    cod_orgao_superior  VARCHAR(20),
    nome_orgao_superior VARCHAR(255) NOT NULL,
    nome_viajante       VARCHAR(255),
    cargo               VARCHAR(255),
    data_inicio         DATE,
    data_fim            DATE,
    destinos            VARCHAR(4000),
    motivo              VARCHAR(4000),
    valor_diarias       DECIMAL(10, 2),
    valor_passagens     DECIMAL(10, 2),
    valor_devolucao     DECIMAL(10, 2),
    valor_outros_gastos DECIMAL(10, 2),
    valor_total         DECIMAL(12, 2),
    duracao_dias        INT,

    PRIMARY KEY (id_viagem),

    CONSTRAINT ck_viagem_valor_diarias
        CHECK (valor_diarias >= 0)
);


--dados tratados dos pagamentos

CREATE TABLE silver_pagamento (
    id_pagamento       SERIAL,
    id_viagem          VARCHAR(20) NOT NULL,
    num_proposta       VARCHAR(20),
    nome_orgao_pagador VARCHAR(255),
    nome_ug_pagadora   VARCHAR(255),
    tipo_pagamento     VARCHAR(50) NOT NULL,
    valor              DECIMAL(10, 2),

    PRIMARY KEY (id_pagamento),

    CONSTRAINT fk_pagamento_viagem
        FOREIGN KEY (id_viagem)
        REFERENCES silver_viagem (id_viagem),

    CONSTRAINT ck_pagamento_valor
        CHECK (valor >= 0)
);


--dados tratados das passagens

CREATE TABLE silver_passagem (
    id_passagem        SERIAL,
    id_viagem          VARCHAR(20) NOT NULL,
    meio_transporte    VARCHAR(50),
    pais_origem_ida    VARCHAR(60),
    uf_origem_ida      VARCHAR(40),
    cidade_origem_ida  VARCHAR(80),
    pais_destino_ida   VARCHAR(60),
    uf_destino_ida     VARCHAR(40),
    cidade_destino_ida VARCHAR(80),
    valor_passagem     DECIMAL(10, 2),
    taxa_servico       DECIMAL(10, 2),
    data_emissao       DATE,

    PRIMARY KEY (id_passagem),

    CONSTRAINT fk_passagem_viagem
        FOREIGN KEY (id_viagem)
        REFERENCES silver_viagem (id_viagem),

    CONSTRAINT ck_passagem_valor
        CHECK (valor_passagem >= 0),

    CONSTRAINT ck_passagem_taxa
        CHECK (taxa_servico >= 0)
);


--dados tratados dos trechos

CREATE TABLE silver_trecho (
    id_trecho        SERIAL,
    id_viagem        VARCHAR(20) NOT NULL,
    sequencia_trecho INT,
    origem_data      DATE,
    origem_uf        VARCHAR(40),
    origem_cidade    VARCHAR(80),
    destino_data     DATE,
    destino_uf       VARCHAR(40),
    destino_cidade   VARCHAR(80),
    meio_transporte  VARCHAR(50),
    numero_diarias   DECIMAL(10, 2),

    PRIMARY KEY (id_trecho),

    CONSTRAINT fk_trecho_viagem
        FOREIGN KEY (id_viagem)
        REFERENCES silver_viagem (id_viagem),

    CONSTRAINT ck_trecho_diarias
        CHECK (numero_diarias >= 0),

    CONSTRAINT uq_trecho_viagem_sequencia
        UNIQUE (id_viagem, sequencia_trecho)
);


--conferência das tabelas criadas

SELECT
    table_name
FROM information_schema.tables
WHERE table_schema = 'public'
  AND table_type = 'BASE TABLE'
ORDER BY table_name;