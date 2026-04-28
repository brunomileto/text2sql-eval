# Base de Dados Financeira — Documentação do Esquema

Base de dados do benchmark BIRD (mini-dev), versão em português brasileiro.
Contém informações de contas bancárias, clientes, cartões de crédito, empréstimos, transações e ordens de pagamento de um banco tcheco.

Esta documentação segue os nomes de tabelas, colunas e valores gerados pelo notebook `notebooks/financial_database_pt_br_correto.ipynb`.

---

## Tabelas

| Tabela | Descrição |
|---|---|
| [conta](#1-conta) | Contas bancárias e frequência de emissão de extratos |
| [cartao](#2-cartao) | Cartões de crédito emitidos |
| [cliente](#3-cliente) | Dados cadastrais dos clientes |
| [disp](#4-disp) | Relacionamento entre clientes e contas |
| [distrito](#5-distrito) | Dados demográficos e socioeconômicos dos distritos |
| [emprestimo](#6-emprestimo) | Empréstimos concedidos |
| [ordem](#7-ordem) | Ordens de pagamento permanentes |
| [trans](#8-trans) | Registro de todas as transações bancárias |

---

## 1. conta

Contém informações sobre as contas bancárias, incluindo localização da agência, periodicidade de emissão de extratos e data de abertura.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_conta` | id da conta | identificador único da conta | inteiro | — |
| `id_distrito` | localização da agência | distrito da agência da conta | inteiro | chave para `distrito.id_distrito` |
| `frequencia` | frequência | periodicidade de emissão de extratos | texto | `TAXA MENSAL` — emissão mensal; `TAXA SEMANAL` — emissão semanal; `TAXA POR OPERACAO` — emissão após operação |
| `data` | data | data de criação da conta | data | formato `YYYY-MM-DD` |

---

## 2. cartao

Informações sobre cartões de crédito emitidos, incluindo tipo e data de emissão.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_cartao` | id do cartão de crédito | identificador único do cartão de crédito | inteiro | — |
| `id_disposicao` | id de disposição | relacionamento cliente-conta associado ao cartão | inteiro | chave para `disp.id_disposicao` |
| `tipo` | tipo | tipo do cartão de crédito | texto | `junior` — classe júnior; `classic` — classe padrão; `gold` — cartão de alto nível |
| `emitido` | emitido | data de emissão do cartão de crédito | data | formato `YYYY-MM-DD` |

---

## 3. cliente

Dados cadastrais dos clientes do banco, incluindo informações demográficas básicas.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_cliente` | id do cliente | identificador único do cliente | inteiro | — |
| `genero` | gênero | gênero do cliente | texto | `F` — feminino; `M` — masculino |
| `data_nascimento` | data de nascimento | data de nascimento do cliente | data | formato `YYYY-MM-DD` |
| `id_distrito` | distrito | distrito do cliente | inteiro | chave para `distrito.id_distrito` |

---

## 4. disp

Relacionamento entre clientes e contas, indicando o tipo de acesso do cliente à conta.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_disposicao` | id de disposição | identificador único da disposição | inteiro | — |
| `id_cliente` | id do cliente | cliente relacionado à conta | inteiro | chave para `cliente.id_cliente` |
| `id_conta` | id da conta | conta relacionada ao cliente | inteiro | chave para `conta.id_conta` |
| `tipo` | tipo | tipo de disposição | texto | `TITULAR` — titular/proprietário da conta; `AUTORIZADO` — cliente autorizado a usar a conta |

---

## 5. distrito

Informações demográficas e socioeconômicas dos distritos, incluindo dados populacionais, taxa de desemprego, salário médio e criminalidade.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_distrito` | id do distrito | identificador único do distrito | inteiro | — |
| `A2` | nome do distrito | nome do distrito | texto | — |
| `A3` | região | região | texto | — |
| `A4` | número de habitantes | população do distrito | texto | — |
| `A5` | nº de municípios com habitantes < 499 | quantidade de municípios com menos de 499 habitantes | texto | — |
| `A6` | nº de municípios com habitantes 500-1999 | quantidade de municípios com 500 a 1999 habitantes | texto | — |
| `A7` | nº de municípios com habitantes 2000-9999 | quantidade de municípios com 2000 a 9999 habitantes | texto | — |
| `A8` | nº de municípios com habitantes > 10000 | quantidade de municípios com mais de 10000 habitantes | inteiro | — |
| `A9` | número de cidades | número de cidades no distrito | inteiro | — |
| `A10` | proporção de habitantes urbanos | proporção de habitantes urbanos | real | — |
| `A11` | salário médio | salário médio | inteiro | — |
| `A12` | taxa de desemprego 1995 | taxa de desemprego em 1995 | real | — |
| `A13` | taxa de desemprego 1996 | taxa de desemprego em 1996 | real | — |
| `A14` | nº de empreendedores por 1000 habitantes | quantidade de empreendedores por 1000 habitantes | inteiro | — |
| `A15` | nº de crimes cometidos em 1995 | quantidade de crimes cometidos em 1995 | inteiro | — |
| `A16` | nº de crimes cometidos em 1996 | quantidade de crimes cometidos em 1996 | inteiro | — |

---

## 6. emprestimo

Registro de empréstimos concedidos, incluindo valor, prazo, parcelas mensais e status de pagamento.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_emprestimo` | id do empréstimo | identificador único do empréstimo | inteiro | — |
| `id_conta` | id da conta | conta associada ao empréstimo | inteiro | chave para `conta.id_conta` |
| `data` | data | data de aprovação do empréstimo | data | formato `YYYY-MM-DD` |
| `valor` | valor | valor aprovado | inteiro | unidade monetária da base original |
| `duracao` | duração | duração do empréstimo | inteiro | unidade: mês |
| `parcelas` | parcelas mensais | valor das parcelas mensais | real | — |
| `status` | status | status do reembolso | texto | `A` — contrato concluído sem problemas; `B` — contrato concluído com empréstimo não pago; `C` — contrato em andamento, ok até agora; `D` — contrato em andamento com cliente em dívida |

---

## 7. ordem

Ordens de pagamento permanentes configuradas nas contas, especificando beneficiário, valor e finalidade.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_ordem` | id da ordem | identificador único da ordem de pagamento | inteiro | — |
| `id_conta` | id da conta | conta que emite a ordem de pagamento | inteiro | chave para `conta.id_conta` |
| `banco_para` | banco do destinatário | banco do destinatário | texto | cada banco tem um código único de duas letras |
| `conta_para` | conta do destinatário | conta do destinatário | inteiro | — |
| `valor` | valor | valor debitado pela ordem | real | — |
| `simbolo_k` | caracterização do pagamento | finalidade do pagamento | texto | `CONTAS DE CONSUMO`; `PAGAMENTO DE EMPRESTIMO`; `PAGAMENTO DE SEGURO`; `LEASING`; vazio |

---

## 8. trans

Registro detalhado de todas as transações bancárias, incluindo depósitos, saques, transferências e saldo resultante.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_transacao` | id da transação | identificador único da transação | inteiro | — |
| `id_conta` | id da conta | conta associada à transação | inteiro | chave para `conta.id_conta` |
| `data` | data da transação | data da transação | data | formato `YYYY-MM-DD` |
| `tipo` | tipo da transação | direção/tipo da movimentação | texto | `CREDITO`; `DEBITO`; `SAQUE` |
| `operacao` | modo de transação | modo de execução da transação | texto | `DEPOSITO EM DINHEIRO`; `SAQUE EM DINHEIRO`; `SAQUE NO CARTAO`; `TRANSFERENCIA ENVIADA`; `TRANSFERENCIA RECEBIDA`; vazio |
| `valor` | valor | valor da transação | inteiro | unidade monetária da base original |
| `saldo` | saldo após transação | saldo após a transação | inteiro | unidade monetária da base original |
| `simbolo_k` | caracterização da transação | finalidade da transação | texto | `CONTAS DE CONSUMO`; `JUROS CREDITADOS`; `JUROS DE MORA`; `PAGAMENTO DE EMPRESTIMO`; `PAGAMENTO DE SEGURO`; `PENSAO`; `TAXA DE SERVICO`; vazio; espaço em branco |
| `banco` | banco do parceiro | banco do parceiro da transação | texto | cada banco tem um código único de duas letras; pode ser vazio |
| `conta` | conta do parceiro | conta do parceiro da transação | inteiro | pode ser vazio |
