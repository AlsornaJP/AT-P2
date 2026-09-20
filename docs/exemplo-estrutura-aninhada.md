# Exercício 8 — a escolha da estrutura, com exemplo

Anotação de estudo, para explicar a decisão do exercício 8 com um caso concreto na mão.

## A analogia, para começar

Pense numa ficha de cadastro de papel com **três linhas impressas** para dependentes.

Se o funcionário tem um dependente, duas linhas ficam em branco. Se tem cinco, não cabe — e para
resolver é preciso reimprimir o formulário e refazer o sistema que lê essas fichas.

Agora pense numa ficha que tem, em vez das três linhas, uma **folha anexa** onde se escreve quantos
dependentes forem. Um, cinco ou nenhum: a ficha é a mesma. A quantidade deixou de ser parte do
formulário e virou só o conteúdo do anexo.

Campos separados são as três linhas impressas. A lista aninhada é a folha anexa. **O resto deste
texto é essa ideia aplicada ao diagnóstico.**

## O mesmo diagnóstico, das duas formas

Caso real do manual: compressor CMP-100, erro E-102.

**Com campos separados**, reservando espaço para três peças:

| campo | valor |
|---|---|
| codigo | CMP-100 |
| causa_provavel | válvula termostática travada |
| acao_recomendada | substituir o componente e registrar a troca no histórico |
| peca_1_nome | válvula termostática 3/4 |
| peca_1_quantidade | 1 |
| peca_1_prioridade | alta |
| peca_2_nome | jogo de juntas |
| peca_2_quantidade | 2 |
| peca_2_prioridade | media |
| peca_3_nome | *(vazio)* |
| peca_3_quantidade | *(vazio)* |
| peca_3_prioridade | *(vazio)* |

**Com a lista aninhada**, que foi o que eu fiz:

| campo | valor |
|---|---|
| codigo | CMP-100 |
| causa_provavel | válvula termostática travada |
| acao_recomendada | substituir o componente e registrar a troca no histórico |
| pecas_recomendadas | uma lista com **dois** itens |

E cada item da lista tem a mesma forma:

| nome | quantidade | prioridade |
|---|---|---|
| válvula termostática 3/4 | 1 | alta |
| jogo de juntas | 2 | media |

Repare que na primeira versão já sobram três campos vazios, e o diagnóstico nem tem peça demais.

## Três situações que separam as duas escolhas

### 1. Um defeito que exige quatro peças

No manual atual, todos os erros têm duas peças. Mas isso é o manual de hoje: nada garante que um
equipamento novo não traga um erro com quatro.

Com campos separados, a quarta peça **se perde**. E consertar não é acrescentar um campo: é alterar
o modelo, o agente que preenche e o painel que lê, os três ao mesmo tempo, e combinar a mudança com
quem consome o serviço.

Com a lista, não acontece nada. Chegam quatro itens onde antes chegavam dois. Nenhum código muda.

### 2. O diagnóstico sem peça nenhuma

É o caso de erro do exercício: equipamento que não está no manual. Aqui não há peça a recomendar.

Com campos separados, os nove campos vêm vazios, e o painel precisa saber que vazio significa
"não existe peça" — e não "o campo não foi preenchido".

Com a lista, ela vem vazia. O painel percorre zero item e não desenha nada. **Não existe caso
especial a tratar**, e foi por isso que escolhi lista vazia em vez de campo nulo: campo nulo
obrigaria a verificar antes de usar, e essa verificação é exatamente o tipo de coisa que alguém
esquece.

### 3. Somar as peças de vários chamados

O almoxarifado quer saber quantas válvulas termostáticas pedir, somando os chamados da semana.

Com a lista, é percorrer os diagnósticos e somar os itens. Com campos separados, é olhar `peca_1`,
depois `peca_2`, depois `peca_3`, sempre pulando os vazios, e torcendo para ninguém acrescentar um
`peca_4` depois.

E isso só funciona porque a quantidade é **número**, e não texto. Se fosse "1 unidade", o
almoxarifado teria que extrair o número de dentro da frase antes de somar.

## Por que objetos na lista, e não frases

Uma terceira opção seria uma lista de frases, do tipo "2 unidades de jogo de juntas, prioridade
média".

Seria mais fácil de gerar e péssimo de consumir: o painel teria que separar número, nome e urgência
de dentro de uma frase, com todos os erros que isso traz. Com três campos nomeados, cada informação
chega pronta e no tipo certo.

## Se me perguntarem

**"Campos separados não são mais simples de ler?"**
Para um diagnóstico só, talvez. Mas a simplicidade é do programador que escreve o modelo, não de
quem consome. Quem consome paga em campos vazios e em medo de acrescentar peça.

**"E se o painel só souber exibir três peças?"**
Aí o limite é do painel, e é lá que ele deve estar — não engessado no formato dos dados. O
diagnóstico continua carregando o que o manual manda, e o painel decide o que mostrar.

**"Qual a desvantagem da lista?"**
Duas. Ela é um pouco mais trabalhosa de percorrer do que ler um campo fixo. E a ordem dos itens é a
ordem do manual, que não é promessa nenhuma: se o painel quiser as de prioridade alta no topo, tem
que ordenar por conta própria.

## Em uma frase

Campos separados obrigam a decidir, na hora de escrever o modelo, quantas peças um diagnóstico pode
ter no máximo — e essa decisão é um chute. Com a lista, a quantidade deixa de ser parte da
estrutura e passa a ser um dado.
