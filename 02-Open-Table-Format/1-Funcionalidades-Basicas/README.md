**Antes de começar, execute os passos abaixo para configurar o ambiente caso não tenha feito isso ainda na aula de HOJE: [Preparando Credenciais](../../00-create-codespaces/Inicio-de-aula.md)**

Neste laboratório, você explorará as funcionalidades básicas do Apache Iceberg e aprenderá a criar e modificar tabelas do Iceberg com o Amazon Athena.

Observe que o Amazon Athena fornece suporte integrado para o Apache Iceberg, para que você possa ler e gravar em tabelas do Iceberg sem adicionar nenhuma dependência ou configuração adicional. Isso é válido para o [Tabelas Iceberg v2]([https://iceberg.apache.org/spec/\#version\-2\-row\-level\-deletes](https://iceberg.apache.org/spec/#version-2-row-level-deletes)).


## Principais pontos de aprendizagem

---
* Criando tabelas Iceberg
* Atualizando um único registro
* Excluindo registros de uma tabela Iceberg (conformidade com [GDPR](https://gdpr-info.eu/))
* Evoluindo o esquema de uma tabela Iceberg

---

## Pré-requisitos e criação do ambiente

1. No codespace da disciplina, abra um terminal integrado (geralmente já esta aberto ao iniciar a ferramenta).

![](img/terminal-inicial.png)

2. No terminal, Execute este script para preparar automaticamente o ambiente de laboratório no Athena, baixando os dados TPC-DS, enviando-os ao S3 e criando todas as tabelas necessárias para as consultas:

``` bash
 cd /workspaces/fiap-cloud-based-analytics && bash setup_athena_tpcds.sh
```
![img/criacao-tabela.png](img/criacao-tabela.png)

## Configurando o Athena

3. Navegue até o [console do Amazon Athena](https://us-east-1.console.aws.amazon.com/athena/home?region=us-east-1#/landing-page){:target="_blank"} usando o link.

4. Selecione **Consulte seus dados no console do Athena** e depois **Iniciar editor de consultas**.

![athena_searchbar](img/athena_launch_query_editor.png)

5. Quando estiver dentro do Amazon Athena, clique em **Editar configurações**. Em seguida clique em **Gerenciar**.

![athena_setup](img/athena_initial_setup.png)

![athena_setup1](img/athena_initial_setup1.png)

6. Clique em `Browse S3`, clique no bucket que inicia com `otfs-aula` e selecione a pasta `athena_res/`. CLique em `Choose` e `Salvar` em sequencia. Isso garantirá que os resultados das consultas sejam armazenados em um local específico no Amazon S3.

![athena_reslocation_setup](img/athena_reslocation_setup.png)

![athena_reslocation_setup](img/athena_reslocation_setup1.png)

![athena_reslocation_setup](img/athena_reslocation_setup2.png)

![athena_reslocation_setup](img/athena_reslocation_setup3.png)

7. Selecione **Editor** para a página do editor de consultas.

![athena_editor](img/athena-editor.png)

---

## Criando tabelas Iceberg
8. Para criar o Banco de Dados, copie a consulta abaixo no editor de consultas e clique em **Executar**. Você precisa estar no **Editor de Consultas** do Athena para executar os comandos abaixo.

``` sql
create database athena_iceberg_db;
```

![create-iceberg-db](img/create-iceberg-db.png)

---

9. Para criar a tabela Iceberg, copie a consulta abaixo no editor de consultas, substitua `<your-account-id>` pelo ID da conta atual e clique em **Executar**.

![](img/getIdAccount.png)

``` sql
CREATE TABLE athena_iceberg_db.customer_iceberg (
    c_customer_sk INT COMMENT 'unique id',
    c_customer_id STRING,
    c_first_name STRING,
    c_last_name STRING,
    c_email_address STRING)
LOCATION 's3://otfs-aula-<your-account-id>/datasets/athena_iceberg/customer_iceberg'
TBLPROPERTIES (
  'table_type'='iceberg',
  'format'='PARQUET',
  'write_compression'='zstd'
);
```

![Create-iceberg-table](img/create-iceberg-table.png)

![](img/create-iceberg-table-2.png)

---

10. Você pode verificar se a nova tabela `customer_iceberg` foi criada no banco de dados. Não há dados na tabela no momento.

Você também pode selecionar o nome do banco de dados no menu suspenso no painel esquerdo para visualizar as tabelas dentro desse banco de dados.

``` sql
SHOW TABLES IN athena_iceberg_db;
```

![Create-iceberg-table](img/show_tables_in_db.png)

---

11. Você pode verificar o esquema e a definição de partição da tabela com a consulta DESCRIBE. Você também pode selecionar o nome da tabela no painel esquerdo para visualizar os detalhes da tabela.

``` sql
DESCRIBE customer_iceberg;
```

![Create-iceberg-table](img/describe_athena_iceberg_table.png)

---

## Estrutura da tabela iceberg

Aqui está um diagrama representando a estrutura da tabela subjacente do Iceberg:

* Cada operação de confirmação (inserir, atualizar, excluir, mesclar, compactar) no Iceberg gera um novo Snapshot (por exemplo, S0, S1, ...).
* Cada operação (confirmação, atualização de esquema, roll\-back, roll\-forward) no Iceberg gera um novo arquivo de metadados.
* A tabela de catálogo do Iceberg aponta para o arquivo de metadados mais recente (ponteiro de metadados atual).
* O arquivo de metadados, entre outras informações, contém a lista de snapshots disponíveis e o ID do snapshot atual.
* Cada snapshot de tabela é associado a um arquivo de lista de manifesto.
* Cada arquivo de lista de manifesto, entre outras informações, aponta para um ou muitos arquivos de manifesto.
* Cada arquivo de manifesto aponta para um ou muitos arquivos de dados.

![Create-iceberg-table](img/iceberg_underlying_table_structure.png)

As tabelas Athena Iceberg expõem vários metadados de tabela, como arquivos de tabela, manifestos, histórico, partição, snapshot por meio de tabelas de metadados. Nós os consultaremos em momentos diferentes como parte deste exercicio.

12. Você pode executar uma consulta `SELECT` usando a sintaxe `<table_name>$files` para consultar os metadados da tabela `files` do Iceberg. A tabela `customer` não contém nenhum dado no momento. Então, ela não mostrará nenhum arquivo.

``` sql
SELECT * FROM "athena_iceberg_db"."customer_iceberg$files"
```

![Create-iceberg-table](img/athena_table_files_no_data.png)

* Você pode executar uma consulta `SELECT` usando a sintaxe `<table_name>$manifests` para consultar os metadados da tabela `manifests` do Iceberg. A consulta abaixo não mostrará dados, pois a tabela está vazia.

``` sql
SELECT * FROM "athena_iceberg_db"."customer_iceberg$manifests"
```

* Você pode executar uma consulta `SELECT` usando a sintaxe `<table_name>$snapshots` para consultar os metadados da tabela `$snapshots` do Iceberg. A consulta abaixo não mostrará dados, pois a tabela está vazia.

``` sql
SELECT * FROM "athena_iceberg_db"."customer_iceberg$snapshots"
```

---

13. Agora vamos pegar alguns registros da tabela `tpcds.prepared_customer` e inseri-los dentro da tabela `customer_iceberg`.

``` sql
INSERT INTO athena_iceberg_db.customer_iceberg
SELECT * FROM tpcds.prepared_customer 
```

Você deverá ver a mensagem "Consulta bem-sucedida" nos resultados da consulta.

---

14. Verifique se os dados estão carregados corretamente consultando a tabela. Copie a consulta abaixo no editor de consultas e clique em **Executar**

``` sql
select * from athena_iceberg_db.customer_iceberg limit 10;
```

![iceberg-test-query](img/query-iceberg-table.png)


15. Verifique se o comando insert inseriu 2.000.000 de registros de clientes na tabela.

``` sql
select count(*) from athena_iceberg_db.customer_iceberg;
```

Você deve ver `20000 'nos resultados da consulta.


16. Dentro do local da tabela do [Amazon S3](https://us-east-1.console.aws.amazon.com/s3/home?region=us-east-1): `s3://otfs-aula-<your-account-id>/datasets/athena_iceberg/customer_iceberg/` (`<your-account-id>` é o ID da sua conta atual), você verá duas pastas, **data** e **metadata**. A pasta **data** contém os dados reais no formato parquet e a pasta **metadata** contém vários arquivos de metadados.
Existem três tipos de arquivos de metadados:

* arquivo de metadados, terminando com `.metadata.json`
* lista de manifesto, terminando com `*-m*.avro`
* arquivos de manifesto, no formato de `snap-*.avro`

Um novo arquivo de metadados será criado sempre que você fizer alterações na tabela.

Pasta de metadados:

![iceberg-test-query](img/iceberg_table_metadata_s3_folder.png)

Pasta de dados:

![iceberg-test-query](img/iceberg_table_data_s3_folder.png)

Agora vamos consultar os metadados da tabela Iceberg.

* Execute a seguinte instrução para listar os arquivos da tabela Iceberg.

``` sql
SELECT * FROM "athena_iceberg_db"."customer_iceberg$files"
```

Nos resultados da consulta, você verá detalhes sobre o caminho dos arquivos de dados do S3 na coluna `file_path` (extensão `.parquet`).

* Execute a seguinte instrução para listar os manifestos da tabela Iceberg.

``` sql
SELECT * FROM "athena_iceberg_db"."customer_iceberg$manifests"
```

Nos resultados da consulta, você verá detalhes sobre o caminho dos arquivos de manifesto do S3 na coluna `path` (extensão `.avro`).

* Execute a seguinte instrução para ver o histórico de ações da tabela Iceberg.

``` sql
SELECT * FROM "athena_iceberg_db"."customer_iceberg$history"
```

Nos resultados da consulta, você verá `snapshot_id`, `parent_id`, etc.


* Execute a seguinte instrução para ver os detalhes do instantâneo da tabela Iceberg.

``` sql
SELECT * FROM "athena_iceberg_db"."customer_iceberg$snapshots"
```

Nos resultados da consulta, você verá `snapshot_id`, `parent_id`, `manifest_list`, etc.

---

**Parabéns, você criou uma tabela Iceberg! Agora vamos explorar alguns dos principais recursos do Athena Iceberg.**

---

## Atualizar registros

Sua próxima tarefa é fazer uma limpeza de dados. Na seção a seguir, você se concentrará em um cliente específico que inseriu seu sobrenome e e-mail incorretamente. Como resultado, esses dois campos são `Null` e você tem a tarefa de corrigi-los.

17. Copie a consulta abaixo no editor de consultas e clique em **Executar**.

``` sql
select * from athena_iceberg_db.customer_iceberg
WHERE c_customer_sk = 15
```

Observe que o sobrenome (`c_last_name`) e o endereço de e-mail (`c_email_address`) do usuário Tonya são `null`. Sua equipe de atendimento ao cliente coletou o sobrenome e o e-mail dele e os forneceu a você.

18. Você pode facilmente fazer essa alteração usando a consulta `UPDATE`. Consultas `UPDATE` aceitam um filtro para corresponder linhas a serem atualizadas. Copie a consulta abaixo no editor de consultas e clique em **Executar**.

``` sql
UPDATE athena_iceberg_db.customer_iceberg
SET c_last_name = 'John', c_email_address = 'johnTonya@abx.com' 
WHERE c_customer_sk = 15
```

A consulta deverá ser executada com sucesso e você verá a mensagem "Consulta bem-sucedida" nos resultados da consulta.

19. Verifique se o sobrenome e o endereço de e-mail de Tonya estão fixos. Copie a consulta abaixo no editor de consultas e clique em **Executar**.

``` sql
select * from athena_iceberg_db.customer_iceberg
WHERE c_customer_sk = 15
```

Observe que o sobrenome e o endereço de e-mail de Tonya foram atualizados agora.

Athena usa [merge-on-read](https://docs.aws.amazon.com/pt_br/prescriptive-guidance/latest/apache-iceberg-on-aws/best-practices-write.html) para operações UPDATE.
Isso significa que ele grava arquivos de exclusão de posição Iceberg e linhas recém-atualizadas como arquivos de dados na mesma transação.
Arquivos de exclusão baseados em posição identificam linhas excluídas por arquivo e posição em um ou mais arquivos de dados.
Em contraste com uma atualização **copy\-on\-write**, uma atualização merge\-on\-read é mais eficiente porque não reescreve arquivos de dados inteiros.
Quando lemos uma tabela Iceberg configurada com atualizações **merge\-on\-read**, o mecanismo mescla os arquivos de exclusão de posição Iceberg com arquivos de dados para produzir a visualização mais recente de uma tabela.
Uma operação UPDATE no Iceberg pode ser imaginada como uma combinação de INSERT INTO e DELETE.

20. Você pode verificar como essa operação UPDATE impacta a camada de dados do Iceberg. Observe que há um novo arquivo parquet criado devido à alteração acima. Você pode identificar esse novo arquivo verificando o timestamp do arquivo `LastModified` inspecionando na pasta **data** da tabela S3.

A declaração a seguir lista os arquivos para uma tabela Iceberg.

``` sql
SELECT * FROM "athena_iceberg_db"."customer_iceberg$files"
```

![iceberg-test-query](img/data_file_path_after_update.png)

---

## Delete rows from Iceberg table

Tonya escolheu optar por sair do aplicativo com base em seus direitos GDPR. Agora você precisa excluir seus registros.ds.

Você pode fazer essa alteração facilmente usando a consulta `DELETE FROM`. As consultas `DELETE FROM` aceitam um filtro para corresponder às linhas a serem excluídas.


Athena usa `merge-on-read` para operações DELETE.
Isso significa que ele cria arquivos de exclusão baseados em Position\ ao executar instruções DELETE.
Arquivos de exclusão baseados em Position\ identificam linhas excluídas por arquivo e posição em um ou mais arquivos de dados.
Em contraste com uma exclusão **copy\-on\-write**, uma exclusão merge\-on\-read é mais eficiente porque não reescreve arquivos de dados inteiros.
Quando lemos uma tabela Iceberg configurada com exclusões **merge\-on\-read**, o mecanismo mescla os arquivos de exclusão de posição Iceberg com arquivos de dados para produzir a visualização mais recente de uma tabela.

21. Copie a consulta abaixo no editor de consultas e clique em **Executar**.

``` sql
delete from athena_iceberg_db.customer_iceberg
WHERE c_customer_sk = 15
```

A consulta deverá ser executada com sucesso e você verá a mensagem "Consulta bem-sucedida" nos resultados da consulta.


22. Verifique se o registro de Tonya foi removido da tabela Iceberg.

``` sql
SELECT * FROM athena_iceberg_db.customer_iceberg WHERE c_customer_sk = 15
```

Você deverá ver "Nenhum resultado" nos resultados da consulta.

---

## Time Travel
O Time\-travel permite consultas reproduzíveis apontando para um instantâneo de tabela específico e permite que os usuários examinem facilmente as alterações.

Cada alteração em uma tabela Iceberg cria uma versão independente da árvore de metadados, chamada snapshot. Você verá 3 snapshots no total usando a seguinte consulta.

* operação de inserção inicial (append)
* operação de atualização (overwrite)
* operação de exclusão (delete)
Observe que a consulta abaixo está direcionada a uma tabela de metadados de histórico.

23. Para consultar o histórico da tabela, copie a consulta abaixo no editor de consultas e clique em **Executar**.

``` sql
SELECT * FROM "athena_iceberg_db"."customer_iceberg$history"
order by made_current_at;
```

![iceberg-test-query](img/iceberg_table_history.png)

* Linha 1 corresponde à operação de inserção inicial que realizamos para preencher a tabela. A coluna `snapshot_id` mostra o primeiro snapshot criado.
* Linha 2 corresponde à operação de atualização que realizamos. A coluna `snapshot_id` mostra o segundo snapshot criado.
* Linha 3 corresponde à operação de exclusão que realizamos. A coluna `snapshot_id` mostra o terceiro (mais recente) snapshot criado.

24. Substitua `5418594889737463157` pelo `snapshot_id` da Linha 2 para consultar o estado da tabela correspondente ao segundo snapshot (antes da operação de exclusão ser executada).

``` sql
select * from athena_iceberg_db.customer_iceberg
FOR VERSION AS OF  5418594889737463157
WHERE c_customer_sk = 15
```

No resultado da consulta, você deve ver o registro do cliente Tonya.

25. Como alternativa, podemos usar a coluna `made_current_at` para consultar um instantâneo específico.

Copie a consulta abaixo no editor de consultas, substitua `2024-03-03 07:45:10.651 UTC` na consulta pelo valor `made_current_at` da Linha 2 (ponto 16\) e clique em **Executar**.

``` sql
select * from athena_iceberg_db.customer_iceberg
FOR TIMESTAMP AS OF TIMESTAMP '2024-04-16 17:21:49.771 UTC'
WHERE c_customer_sk = 15
```

No resultado da consulta, você deve ver o registro do cliente Tonya.

---

## Evolução do esquema

As atualizações do esquema Iceberg são alterações somente de metadados. Nenhum arquivo de dados é alterado quando você executa uma atualização de esquema. O formato Iceberg suporta as seguintes alterações de evolução de esquema:


* Adicionar – Adiciona uma nova coluna a uma tabela ou a uma struct aninhada.
* Soltar – Remove uma coluna existente de uma tabela ou struct aninhada.
* Renomear – Renomeia uma coluna ou campo existente em uma struct aninhada.
* Reordenar – Altera a ordem das colunas.
* Promoção de tipo – Amplia o tipo de uma coluna, campo de struct, chave de mapa, valor de mapa ou elemento de lista. Atualmente, os seguintes casos são suportados para tabelas Iceberg:
  + inteiro para inteiro grande
  + flutuante para duplo
  + aumentando a precisão de um tipo decimal

26. Vamos consultar os arquivos de dados.

``` sql
SELECT * FROM "athena_iceberg_db"."customer_iceberg$files"
```

Anote o caminho e o nome do arquivo de dados.

27. Agora altere o nome de uma coluna. Você pode usar o seguinte comando DDL para alterar o nome da coluna `c_email_address` para `email`.

``` sql
ALTER TABLE athena_iceberg_db.customer_iceberg 
change column c_email_address email STRING
```

A consulta deve ser executada sem nenhum erro.

28. Vamos consultar os arquivos de dados novamente para verificar se eles não foram alterados.

``` sql
SELECT * FROM "athena_iceberg_db"."customer_iceberg$files"
```

Observe que não há nenhum novo arquivo de dados criado devido à evolução do esquema. As alterações do esquema são armazenadas na camada de metadados.

Verifique se a coluna foi renomeada executando a consulta `DESCRIBE customer_iceberg;`.

29. Use o seguinte comando DDL para adicionar uma nova coluna chamada `c_birth_date`.

``` sql
ALTER TABLE athena_iceberg_db.customer_iceberg ADD COLUMNS (c_birth_date int)
```
Verifique se a nova coluna foi adicionada executando a consulta `DESCRIBE customer_iceberg;`.


30. Execute a consulta a seguir para ver a tabela com a nova coluna. Observe que a nova coluna tem valores `null` para todos os registros atualmente presentes dentro da tabela.



``` sql
SELECT *
FROM athena_iceberg_db.customer_iceberg
LIMIT 10
```