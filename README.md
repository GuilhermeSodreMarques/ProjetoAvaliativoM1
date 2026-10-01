Pipeline de Dados de Viagens a Serviço

Sobre o projeto

Este projeto foi desenvolvido para a atividade avaliativa do Módulo 1 do curso do SENAI.

A proposta foi criar um pipeline de dados utilizando informações de viagens a serviço do Portal da Transparência. Durante o projeto, os dados foram baixados, armazenados no PostgreSQL, tratados e depois utilizados para responder algumas perguntas de negócio.

O pipeline foi dividido nas camadas Raw, Silver e Gold, seguindo a Arquitetura Medallion.

Os arquivos utilizados possuem dados dos seis primeiros meses de 2025.

Camada Raw

A camada Raw guarda os dados da mesma forma que eles aparecem nos arquivos CSV.

Todas as colunas foram criadas como `VARCHAR`, sem realizar limpeza ou conversão. Dessa forma, os dados originais continuam disponíveis caso seja necessário conferir alguma informação.

O arquivo `1_extrair.py` baixa o arquivo ZIP automaticamente, descompacta os quatro CSVs e faz a carga no PostgreSQL em blocos de 50.000 registros.

Antes de carregar os dados, o script utiliza `TRUNCATE` para não duplicar os registros caso seja executado novamente.

Camada Silver

Na camada Silver os dados da Raw são tratados e convertidos para os tipos corretos.

Foram realizadas conversões de:

- textos;
- datas;
- valores monetários;
- números inteiros.

Também foram utilizadas chaves primárias, chaves estrangeiras e outras restrições para manter a integridade das tabelas.

Nesta etapa foram calculadas as colunas:

- `valor_total`;
- `duracao_dias`.

Camada Gold

A camada Gold foi criada para deixar algumas informações já agrupadas e facilitar as análises.

Foram criadas duas tabelas:

- `gold_pagamento_resumo`;
- `gold_trecho_resumo`.

Também foram criadas duas views:

- `vw_gold_pagamento_resumo`;
- `vw_gold_trecho_resumo`.

Para criar esses objetos foram utilizados comandos como `JOIN`, `GROUP BY`, `COUNT` e `SUM`.

Arquivos do projeto


`0_criar_banco.sql` | Cria as tabelas Raw e Silver 
`1_extrair.py` | Baixa os arquivos e carrega a camada Raw 
`2_transformar.py` | Trata os dados e carrega a camada Silver 
`3_analise.ipynb` | Cria a camada Gold e apresenta as análises 
`banco.py` | Possui as funções de conexão com o PostgreSQL 
`config.py` | Possui as configurações utilizadas nos scripts 
`.env.example` | Exemplo das informações necessárias no arquivo `.env` 
`requirements.txt` | Lista as bibliotecas utilizadas 
`.gitignore` | Define os arquivos que não serão enviados ao GitHub 

Dados utilizados

O projeto utiliza os seguintes arquivos:

- `2025_Viagem.csv`;
- `2025_Pagamento.csv`;
- `2025_Passagem.csv`;
- `2025_Trecho.csv`.

Esses arquivos são baixados automaticamente pelo `1_extrair.py` e ficam armazenados na pasta `data`.

A pasta não é enviada ao GitHub porque os arquivos podem ser baixados novamente pelo script.

Quantidade de registros

Depois da carga e da transformação, foram obtidas as seguintes quantidades:

Tabela | Quantidade de registros 

`raw_viagem` | 341.860 
`raw_pagamento` | 606.916 
`raw_passagem` | 167.260 
`raw_trecho` | 763.349 
`silver_viagem` | 341.860 
`silver_pagamento` | 606.916 
`silver_passagem` | 167.260 
`silver_trecho` | 763.349 

Também foram feitas conferências entre as camadas Raw e Silver para verificar se os registros e os valores foram carregados corretamente.

Perguntas respondidas

No notebook foram respondidas as seguintes perguntas:

1. Quais são os cinco órgãos com maior custo total?
2. Quais são os três destinos com maior custo médio por viagem?
3. Qual foi a viagem com maior duração e qual foi o seu custo total?
4. Qual tipo de pagamento possui o maior valor médio?
5. Qual foi o meio de transporte mais usado nos trechos?
6. Qual UF de destino aparece em mais trechos?
7. Qual órgão pagou o maior valor total?

As análises consideram somente as viagens com situação `Realizada`.

Na análise dos destinos, foram considerados apenas os que possuem no mínimo 100 viagens. Esse filtro foi utilizado para evitar uma média baseada em poucos registros.

Outros insights

Além das perguntas principais, também foram feitas outras três análises:

1. Evolução mensal da quantidade e dos custos das viagens;
2. Comparação entre viagens urgentes e não urgentes;
3. Composição dos gastos com diárias, passagens, outros gastos e devoluções.

As respostas são apresentadas com consultas SQL, tabelas, gráficos e uma pequena conclusão.

Tecnologias utilizadas

- Python;
- PostgreSQL;
- SQL;
- Pandas;
- Matplotlib;
- Psycopg2;
- Requests;
- Jupyter Notebook;
- Git e GitHub.

Como executar

Primeiro, instale as bibliotecas utilizadas:

```powershell
python -m pip install -r requirements.txt
```

Depois, crie um arquivo chamado `.env` na pasta do projeto. O arquivo `.env.example` pode ser utilizado como modelo:

```env
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_USER=postgres
POSTGRES_PASSWORD=sua_senha
POSTGRES_DATABASE=transparencia
```

Com o PostgreSQL aberto, crie o banco `transparencia` e execute o arquivo:

```text
0_criar_banco.sql
```

Depois disso, execute os arquivos na seguinte ordem:

```powershell
python 1_extrair.py
python 2_transformar.py
```

Por último, abra o arquivo `3_analise.ipynb` no VS Code ou no Jupyter Notebook e execute todas as células na ordem.