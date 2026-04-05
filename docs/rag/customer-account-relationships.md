# Notas sobre Relacionamento entre Cliente e Conta

Esta página existe porque muitos erros de reporting sobre os dados bancários
nascem da suposição de que a ligação entre cliente e conta é simples. Não é.

O negócio deve ser lido como um modelo relacional:

- uma pessoa pode estar conectada a uma conta de mais de uma forma
- uma conta pode ser compartilhada
- um cartão reflete acesso dentro dessa relação, não apenas identidade do cliente

É por isso que "quantidade de clientes", "quantidade de titulares de conta" e
"quantidade de portadores de cartão" não devem ser tratados como métricas
intercambiáveis.

## O que analistas geralmente querem dizer e onde costumam errar

### "Cliente com conta"

Isso parece simples, mas normalmente esconde uma de três perguntas diferentes:

- clientes que são titulares de uma conta
- clientes ligados a qualquer conta em qualquer papel
- clientes que parecem atuar operacionalmente em uma conta

São populações diferentes. Se você não esclarecer qual delas o negócio quer,
o resultado pode até parecer razoável, mas ainda assim estar conceitualmente errado.

### "Titular da conta"

Titularidade não é a mesma coisa que acesso à conta. Algumas relações indicam
controle principal; outras refletem uso ou autorização. Em discussões internas
essas diferenças costumam ser comprimidas, mas uma boa análise não deveria fazer isso.

Quando uma análise depende de titularidade, o papel dentro da relação importa
mais do que a simples presença de um vínculo cliente-conta.

### "Portador de cartão"

Relatórios de cartão costumam ser inflados porque cartão parece um produto do
cliente. Neste dataset, faz mais sentido entendê-lo como um produto de acesso
ligado a uma relação de conta já existente.

Isso significa que:

- a mesma situação cliente-conta pode existir com ou sem cartão
- contagens de cartão não substituem contagens de clientes
- segmentação por cartão diz mais sobre atendimento e padrão de acesso à conta
  do que sobre o relacionamento completo do cliente

## Hábitos de interpretação recomendados

### Separe identidade de permissão

O modelo mental mais limpo é:

- cliente: quem a pessoa é
- conta: qual relação bancária existe
- papel na relação: o que a pessoa pode fazer em torno daquela conta
- cartão: qual produto de acesso foi emitido dentro daquela relação

Isso pode soar abstrato, mas evita muito reporting ruim.

### Evite contagens de uma etapa em perguntas com forte componente relacional

Se o negócio pedir:

- número de clientes com conta
- número de usuários ativos de conta
- número de clientes com cartões premium
- número de clientes vinculados a crédito

você deve partir do princípio de que a resposta exige interpretação de negócio,
não apenas uma contagem direta.

### Tenha cuidado com deduplicação

Um erro frequente é deduplicar cedo demais ou tarde demais.

Exemplos:

- deduplicar no nível de cliente pode esconder comportamento relevante de múltiplas contas
- contar cada linha de relacionamento pode inflar a população de clientes
- contar cada cartão pode inflar o número de pessoas distintas envolvidas

O nível correto depende da pergunta:

- nível de pessoas
- nível de conta
- nível de relacionamento
- nível de produto

## Padrões de análise que realmente precisam desse contexto

Estes são os tipos de pergunta em que a lógica de relacionamento mais importa:

- Quais clientes parecem controlar mais de uma conta?
- Quantos relacionamentos de contas compartilhadas existem em uma região?
- Cartões premium se concentram entre clientes com relacionamentos bancários mais complexos?
- Clientes com empréstimo costumam estar ligados a um único tipo de relação ou a vários?

## Ressalvas realistas que o analista deve ter em mente

- A linguagem de negócio usada por stakeholders costuma ser mais solta do que o modelo de dados subjacente.
- "Titular", "usuário" e "portador" podem aparecer de forma casual em reuniões, mesmo quando os dados distinguem esses conceitos.
- Uma pessoa ligada a cartão não é necessariamente o melhor proxy para o cliente economicamente principal da conta.
- Métricas fortemente relacionais normalmente deveriam ser anotadas em decks e relatórios, para deixar claro o que exatamente foi contado.

Este dataset fica muito mais fácil de analisar quando você deixa de tratar a
conexão cliente-conta como algo direto e passa a tratá-la como acesso governado
dentro de uma relação bancária contínua.
