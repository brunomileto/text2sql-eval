# Notas de Reporting sobre Pagamentos e Atividade

A maior parte das perguntas analíticas do dia a dia sobre este dado é, na prática,
uma pergunta sobre atividade. Mesmo quando o stakeholder começa falando de cliente,
o sinal real costuma estar na movimentação da conta, no comportamento de pagamento
e na história do saldo ao longo do tempo.

Esta página é o tipo de atalho interno que normalmente passamos para um analista
novo antes de ele começar a montar cortes de pagamento ou transação.

## Pense em atividade postada versus intenção de pagamento

Um dos erros mais comuns é misturar transações efetivamente postadas com pagamentos
permanentes ou instruções de pagamento.

Em linguagem de negócio:

- transações postadas mostram o que realmente bateu na conta
- ordens de pagamento mostram o que o cliente programou ou autorizou

As duas coisas importam, mas respondem perguntas diferentes.

Se um stakeholder perguntar:

- "Em que os clientes estão pagando?"
- "Quanto sai por mês?"
- "Com que frequência as pessoas enviam dinheiro para outros bancos?"

você precisa decidir se ele quer atividade realmente postada, comportamento de
pagamento programado ou uma combinação dos dois.

## Direção e canal são conceitos diferentes

Analistas muitas vezes correm para resumos de entrada versus saída e param por aí.
Isso normalmente perde nuance operacional.

Direção indica se valor está entrando ou saindo da conta.
Canal, modo ou operação indica como aquilo aconteceu.

Essas duas ideias normalmente deveriam aparecer separadas no reporting:

- entrada versus saída
- dinheiro em espécie versus transferência versus comportamento ligado a cartão

Essa distinção importa bastante quando a área quer entender comportamento do
cliente, uso de serviço ou mix operacional.

## Alguns códigos importam mais do que parece

Alguns valores codificados são importantes demais para ficarem enterrados no dado bruto.

No lado transacional, o dataset distingue créditos e saques, e também separa
atividades como:

- saques com cartão
- depósitos em dinheiro
- transferências recebidas ou cobranças oriundas de outro banco
- saques em dinheiro
- transferências enviadas

Em revisões de negócio, essas categorias costumam contar histórias diferentes:

- comportamento mais intensivo em espécie
- contas mais orientadas a transferência
- padrões parecidos com entrada salarial
- uso mais transacional versus uso mais parado

Você não precisa expor cada código bruto para um stakeholder, mas precisa conhecer
essas diferenças ao construir a análise.

## Saldo é útil, mas fácil de usar mal

O saldo corrente pode ser valioso para interpretação, principalmente quando é
analisado junto com valor e direção da transação. Mas ele não deve ser tratado,
sozinho, como indicador completo de saúde financeira.

Por quê:

- ele está no nível da conta, não necessariamente no nível do cliente
- ele reflete o estado após eventos postados, não a relação inteira
- ele pode parecer forte ou fraco dependendo do momento observado

Na prática, saldo tende a funcionar melhor como contexto de apoio do que como
única base para segmentar clientes.

## O que analistas costumam perguntar nesta parte do dado

Perguntas comuns:

- Quais contas mostram maior volume de transferências de saída?
- Com que frequência os clientes usam dinheiro em espécie versus canais de transferência?
- Quais contas recebem entradas mas mantêm saldos baixos?
- Quais categorias de pagamento aparecem mais em saídas recorrentes?

Essas perguntas são, em geral, adequadas. As versões mais fracas são aquelas que
colapsam tudo em uma única métrica de volume sem distinguir o tipo de movimentação.

## Armadilhas recorrentes de reporting

- Tratar ordens de pagamento como se já fossem transações postadas.
- Tratar direção de entrada/saída como contexto suficiente por si só.
- Ignorar o modo operacional da transação.
- Ler atividade de conta como comportamento direto do cliente sem antes decidir
  qual relação cliente-conta realmente importa.
- Interpretar toda saída financeira como se fosse o mesmo evento de negócio.

## Um modelo mental prático para esta parte do dado

Se for para guardar uma única lógica de trabalho aqui, use esta:

- ordens descrevem comportamento de pagamento pretendido ou programado
- transações descrevem atividade efetiva de conta
- saldos ajudam a contextualizar essa atividade
- interpretação em nível de cliente normalmente exige contexto relacional do lado da conta

Esse enquadramento costuma ser suficiente para evitar a primeira rodada de análise
enganosa sobre pagamentos.
