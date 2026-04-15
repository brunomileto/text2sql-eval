# Base de Dados Financeira — Documentação do Esquema

Base de dados do benchmark BIRD (mini-dev), versão em português brasileiro.
Contém informações de contas bancárias, clientes, cartões de crédito, empréstimos, transações e ordens de pagamento de um banco tcheco.

---

## Tabelas

| Tabela | Descrição |
|---|---|
| [conta](#1-conta) | Contas bancárias e frequência de emissão de extratos |
| [cartao](#2-cartao) | Cartões de crédito emitidos |
| [cliente](#3-cliente) | Dados cadastrais dos clientes |
| [disposicao](#4-disposicao) | Relacionamento entre clientes e contas |
| [distrito](#5-distrito) | Dados demográficos e socioeconômicos dos distritos |
| [emprestimo](#6-emprestimo) | Empréstimos concedidos |
| [ordem](#7-ordem) | Ordens de pagamento permanentes |
| [transacao](#8-transacao) | Registro de todas as transações bancárias |

---

## 1. conta

Contém informações sobre as contas bancárias, incluindo localização da agência, periodicidade de emissão de extratos e data de abertura.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_da_conta` | id da conta | id da conta | inteiro | — |
| `id_do_distrito` | localização da agência | localização da agência | inteiro | — |
| `frequencia` | frequência | frequência da conta | texto | `TAXA MENSAL` — emissão mensal; `TAXA POR SEMANA` — emissão semanal; `TAXA APOS O ROTEIRO` — emissão após transação |
| `data` | data | data de criação da conta | data | formato AAMMDD |

---

## 2. cartao

Informações sobre cartões de crédito emitidos, incluindo tipo e data de emissão.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `identificacao_do_cartao` | id do cartão de crédito | número identificador do cartão de crédito | inteiro | — |
| `id_de_disp.` | id de disposição | id de disposição | inteiro | — |
| `tipo` | tipo | tipo do cartão de crédito | texto | `junior` — classe júnior; `classic` — classe padrão; `gold` — cartão de alto nível |
| `publicado` | emitido | data de emissão do cartão de crédito | data | formato AAMMDD |

---

## 3. cliente

Dados cadastrais dos clientes do banco, incluindo informações demográficas básicas.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_do_cliente` | — | o número único do cliente | inteiro | — |
| `genero` | — | gênero do cliente | texto | `F` — feminino; `M` — masculino |
| `data_de_nascimento` | — | data de nascimento | data | — |
| `id_do_distrito` | localização da agência | localização da agência | inteiro | — |

---

## 4. disposicao

Relacionamento entre clientes e contas, indicando o tipo de acesso do cliente à conta.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_de_disp.` | id de disposição | número único de identificação desta linha de registro | inteiro | — |
| `id_do_cliente` | — | número identificador do cliente | inteiro | — |
| `id_da_conta` | — | número identificador da conta | inteiro | — |
| `tipo` | — | tipo de disposição | texto | `PROPRIETARIO` — proprietário da conta; `DISTRIBUIDOR` — disponente da conta. Apenas o proprietário pode emitir ordens permanentes ou solicitar empréstimos. |

---

## 5. distrito

Informações demográficas e socioeconômicas dos distritos, incluindo dados populacionais, taxa de desemprego, salário médio e criminalidade.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_do_distrito` | localização da agência | localização da agência | inteiro | — |
| `a2` | nome do distrito | nome do distrito | texto | — |
| `a3` | região | região | texto | — |
| `a4` | número de habitantes | — | texto | — |
| `a5` | nº de municípios com habitantes < 499 | município < distrito < região | texto | — |
| `a6` | nº de municípios com habitantes 500–1999 | município < distrito < região | texto | — |
| `a7` | nº de municípios com habitantes 2000–9999 | município < distrito < região | texto | — |
| `a8` | nº de municípios com habitantes > 10000 | município < distrito < região | texto | — |
| `a9` | número de cidades | número de cidades | texto | — |
| `a10` | proporção de habitantes urbanos | proporção de habitantes urbanos | real | — |
| `a11` | salário médio | salário médio | inteiro | — |
| `a12` | taxa de desemprego 1995 | taxa de desemprego 1995 | real | — |
| `a13` | taxa de desemprego 1996 | taxa de desemprego 1996 | real | — |
| `a14` | nº de empreendedores por 1000 habitantes | nº de empreendedores por 1000 habitantes | inteiro | — |
| `a15` | nº de crimes cometidos em 1995 | nº de crimes cometidos em 1995 | inteiro | — |
| `a16` | nº de crimes cometidos em 1996 | nº de crimes cometidos em 1996 | inteiro | — |

---

## 6. emprestimo

Registro de empréstimos concedidos, incluindo valor, prazo, parcelas mensais e status de pagamento.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_do_emprestimo` | — | número identificador dos dados do empréstimo | inteiro | — |
| `id_da_conta` | — | número identificador da conta | inteiro | — |
| `data` | — | data de aprovação do empréstimo | data | — |
| `quantia` | — | valor aprovado | inteiro | unidade: dólar americano |
| `duracao` | — | duração do empréstimo | inteiro | unidade: mês |
| `pagamentos` | pagamentos mensais | pagamentos mensais | real | unidade: mês |
| `status` | — | status do reembolso | texto | `A` — contrato concluído sem problemas; `B` — contrato concluído com empréstimo não pago; `C` — contrato em andamento, ok até agora; `D` — contrato em andamento com cliente em dívida |

---

## 7. ordem

Ordens de pagamento permanentes configuradas nas contas, especificando destinatário, valor e finalidade.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `id_do_pedido` | — | identificando o pedido único | inteiro | — |
| `id_da_conta` | — | número identificador da conta | inteiro | — |
| `banco_para` | banco do destinatário | banco do destinatário | texto | — |
| `conta_para` | conta do destinatário | conta do destinatário | inteiro | cada banco tem um código único de duas letras |
| `quantia` | quantia debitada | quantia debitada | real | — |
| `simbolo_k` | caracterização do pagamento | finalidade do pagamento | texto | `POJISTNE` — pagamento de seguro; `SIPO` — pagamento doméstico; `LEASING` — locação; `UVER` — pagamento de empréstimo |

---

## 8. transacao

Registro detalhado de todas as transações bancárias, incluindo depósitos, saques, transferências e saldo resultante.

| Coluna | Nome Legível | Descrição | Tipo | Valores |
|---|---|---|---|---|
| `identificacao_trans` | id da transação | id da transação | inteiro | — |
| `id_da_conta` | — | — | inteiro | — |
| `data` | data da transação | data da transação | data | — |
| `tipo` | +/- transação | +/- transação | texto | `RECEPCAO` — crédito; `EMITIR` — saque |
| `operacao` | modo de transação | modo de transação | texto | `ESCOLHER CARTOU` — saque no cartão de crédito; `DEPOSITO` — crédito em dinheiro; `TRANSFERENCIA DA CONTA` — cobrança de outro banco; `ESCOLHER` — saque em dinheiro; `TRANSFERENCIA PARA CONTA` — remessa para outro banco |
| `quantia` | valor do dinheiro | valor do dinheiro | inteiro | unidade: USD |
| `equilibrio` | saldo após transação | saldo após transação | inteiro | unidade: USD |
| `simbolo_k` | caracterização da transação | — | texto | `POJISTNE` — pagamento de seguro; `SLUZBY` — pagamento por extrato; `UROK` — juros creditados; `SANKC. UROK` — juros de sanção por saldo negativo; `SIPO` — pagamento doméstico; `DUCHOD` — aposentadoria por velhice; `UVER` — pagamento de empréstimo |
| `banco` | banco do parceiro | — | texto | cada banco tem um código único de duas letras |
| `conta` | conta do parceiro | — | inteiro | — |
