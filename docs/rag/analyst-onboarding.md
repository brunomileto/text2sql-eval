# Notas de Onboarding para Analytics Bancário

Se você está começando a trabalhar com este dataset, o erro mais comum é tratá-lo
como se fosse um único razão de clientes. Ele está mais próximo de um retrato
de banco relacional: pessoas têm contas, podem participar da mesma conta em
papéis diferentes, cartões estão vinculados a essas relações com a conta, e o
histórico operacional aparece principalmente em transações, ordens e empréstimos.

A maior parte das perguntas recorrentes dos analistas cai em quatro grupos:

- perguntas sobre relacionamento entre cliente e conta
- perguntas sobre atividade de conta e movimentação financeira
- perguntas sobre crédito e pagamento de empréstimos
- perguntas sobre segmentação por agência, distrito ou região

O dataset é útil para análise de negócio, mas não foi desenhado como um data mart
de reporting perfeito. É normal que alguns conceitos estejam espalhados em mais
de uma entidade, especialmente em temas como titularidade de conta, uso de cartão
e atribuição regional.

## Como pensar os principais conceitos de negócio

### Cliente não é a mesma coisa que conta

Uma pessoa é um cliente. Uma conta é um produto bancário. A relação entre os
dois é uma das peças de contexto mais importantes deste banco de dados.

Na prática:

- um cliente pode estar ligado a várias contas
- uma conta pode envolver várias pessoas
- nem toda pessoa vinculada a uma conta deve ser interpretada como titular

Se uma pergunta de negócio usar expressões como "clientes com conta", "contas
conjuntas", "titulares de conta" ou "portadores de cartão", vale a pena reduzir
o ritmo e definir o que a área realmente quer dizer antes de agregar qualquer coisa.

### Cartões fazem parte da relação com a conta, não apenas do perfil do cliente

Os cartões de crédito deste dataset fazem mais sentido quando vistos como produtos
de acesso vinculados a uma relação bancária já existente. Quando o analista pula
direto de "cartão" para "cliente", normalmente superestima o quão direta essa
ligação realmente é.

### As transações contam a história operacional

Quando alguém pergunta o que os clientes estão fazendo, a resposta normalmente
não está no cadastro do cliente em si. Ela costuma aparecer no comportamento de
transação, nos saldos, nas instruções de pagamento e nos produtos vinculados à conta.

Para perguntas sobre atividade, o histórico transacional é o que mais se aproxima
do pulso operacional do dataset.

### Informação distrital é contexto, não uma verdade universal

Os campos regionais são muito úteis, mas não significam a mesma coisa em todos os
lugares. Em alguns casos a geografia descreve o cliente. Em outros, descreve a
agência ou o contexto da conta. Analistas devem ter cuidado quando comparam
comportamento de cliente com performance de agência.

## Para que este dado funciona bem

O dataset é especialmente bom para:

- análise da relação cliente-conta
- comportamento de pagamentos e transações
- visões de portfólio sobre empréstimos e cartões
- cortes regionais ou por agência da base de clientes e contas

Ele é menos naturalmente adequado para:

- reconstrução completa do ciclo de vida do cliente
- resolução de identidade em nível domiciliar
- análise de rentabilidade por produto
- sequenciamento operacional fino que exigiria um histórico de auditoria mais rico

## Perguntas que analistas costumam fazer

Exemplos de perguntas que combinam bem com esse dataset:

- Que tipos de clientes tendem a manter mais de uma relação com conta?
- Como saques em dinheiro diferem de transferências?
- Quais grupos de conta parecem mais expostos a crédito?
- Quais regiões concentram determinados comportamentos ou produtos?

Exemplos de perguntas que exigem mais cuidado do que parece à primeira vista:

- Quantos clientes são titulares de uma conta?
- Quais clientes usam ativamente uma conta?
- Quais portadores de cartão são "high value"?
- Qual região tem o melhor desempenho?

Essas perguntas são possíveis, mas só depois de decidir o que "ser titular",
"usar", "high value" ou "região" devem significar naquele contexto de reporting.

## Recomendações práticas para novos analistas

- Comece entendendo a relação de negócio, não a lista de tabelas.
- Espere ambiguidades baseadas em papéis ao redor de contas e cartões.
- Trate direção da transação e canal da transação como conceitos diferentes.
- Separe instruções permanentes de pagamento da atividade financeira efetivamente postada.
- Tenha cautela ao alternar entre geografia do cliente e geografia da agência.

As análises mais consistentes neste dataset normalmente começam com uma definição
de negócio clara antes de qualquer pessoa escrever SQL.
