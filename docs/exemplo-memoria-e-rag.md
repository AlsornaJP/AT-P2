# Exercício 11 — memória e RAG, com exemplo

Anotação de estudo, para defender a avaliação de estratégia de memória com casos concretos.

## A analogia, para começar

Pense num colega experiente ajudando um técnico pelo rádio.

Esse colega tem **duas capacidades diferentes**. A primeira é lembrar do que foi dito nos últimos
minutos: se o técnico falou do compressor CMP-100 lá atrás, ele entende o "e agora?" que vem
depois. A segunda é ir até a estante e consultar o manual, quando a pergunta exige um dado que ele
não tem de cabeça.

São coisas separadas. Um colega com ótima memória e nenhum manual **inventa**. Um colega com o
manual na mão e nenhuma memória não entende perguntas curtas, porque não sabe de que equipamento se
está falando.

Memória de conversa é a primeira capacidade. RAG é a segunda.

## Como eu descobri qual delas importa

Aqui está a decisão de método, e ela é defensável sozinha.

Eu poderia ter escrito que as duas são necessárias. Seria razoável e não provaria nada. Em vez
disso usei uma ideia simples: **para saber qual dos dois funcionários faz o trabalho, dê folga a um
de cada vez.**

Então montei três cenários e rodei cada um em três configurações: só com memória, só com busca, e
com as duas. O que quebra em cada caso diz quem estava carregando o trabalho.

E acrescentei uma segunda medida, que acabou sendo decisiva: **registrar se o agente consultou o
manual em cada pergunta**. Isso separa "acertou" de "acertou com fonte". Resposta certa sem
consulta veio do conhecimento geral do modelo — e como o manual é de um equipamento inventado, esse
acerto é sorte, não sistema.

## O que apareceu em cada configuração

**Só memória, sem busca.** O agente afirmou, com segurança, que o alarme E-102 significa "falha na
pressão do óleo". O manual diz válvula termostática travada. Noutro cenário, disse que **pode lavar
o radiador com água** — o manual diz exatamente o contrário, que água danifica as aletas.

Este é o ponto mais forte contra usar só memória: ela não deixa o agente mudo, deixa o agente
**inventando com confiança**. E uma resposta dessas estraga equipamento.

**Só busca, sem memória.** O agente não erra, ele **se esquiva**. Na segunda pergunta do chamado
respondeu em condicional e terminou dizendo que não tinha os detalhes. Na terceira, quando o
técnico perguntou "qual era mesmo o código do alarme?", ele **listou os três códigos do manual e
devolveu a pergunta**: "a qual desses você se refere?". Ele não sabia, porque não tinha a conversa.

**As duas juntas.** As três perguntas respondidas direto — e as duas últimas **sem consultar o
manual**, o que mostra de onde veio a informação: da conversa guardada.

## O achado principal: a memória atrapalhou a busca

Esta é a parte que eu mais quero saber explicar, porque é contraintuitiva e foi contra o que eu
esperava.

Volte ao colega do rádio, agora na estante. O técnico pergunta: **"e depois de apertar, o que eu
faço?"**

O colega, que lembra que vocês estavam falando do cabeçote, vai até a estante procurando
"procedimento após aperto **dos parafusos do cabeçote**". E volta com três textos sobre torque do
cabeçote — que era o assunto velho. O texto que respondia a pergunta, o que diz que **após qualquer
aperto** o equipamento roda trinta minutos em vazio, ficou de fora.

A memória o ajudou a entender a pergunta e, ao mesmo tempo, **estragou a consulta**.

Medindo isso no meu programa, com a mesma pergunta feita de duas formas:

| forma da consulta | posição do trecho certo | nota |
|---|---|---|
| com as palavras do próprio técnico | **1º lugar** | 0,5869 |
| com a pergunta reescrita pelo agente | **4º lugar** | 0,7117 |

Como a busca devolvia três trechos, o certo ficou de fora por uma posição.

**Esse teste é determinístico:** são duas frases fixas comparadas com os mesmos vetores. Rodei
várias vezes e dá sempre isso. É a parte da avaliação que não depende de sorte.

## O detalhe que mais confunde: nota alta não é resposta certa

Repare na tabela acima: a busca que **deu errado** tem nota maior, 0,71 contra 0,58.

Isso não é defeito, é o que a nota mede. Ela diz **o quanto o trecho se parece com a pergunta que
foi feita** — não se a resposta está certa. Quando o agente enfiou "cabeçote" e "CMP-100" na
consulta, criou uma pergunta muito parecida com os textos sobre torque do cabeçote. Esses textos
subiram, com notas altas, e empurraram para baixo o que realmente respondia.

**Se a pergunta aponta para o lado errado, a busca acerta o alvo errado com precisão.**

Daí a regra prática: notas só podem ser comparadas dentro da mesma consulta. Comparar o 0,58 de uma
com o 0,71 de outra não quer dizer nada.

## Combinar não é somar

Um resultado que eu não esperava: num dos testes o agente **tinha as duas ferramentas e mesmo assim
errou**, porque decidiu não buscar. Achou que já sabia pela conversa e respondeu que "o manual não
especifica".

Ter as duas capacidades não garante que as duas sejam usadas. Foi preciso dizer na instrução qual
serve para quê, e mesmo assim a instrução não garante — em execuções diferentes ele decidiu
diferente. O que resolveu de forma confiável foi ampliar a janela de busca, que não depende da
vontade do modelo.

## Se me perguntarem

**"O placar mostra três a três entre só busca e as duas juntas. Então a combinação não era
necessária?"**

Esta é a pergunta mais provável, e a resposta precisa estar na ponta da língua. O placar conta se a
palavra esperada apareceu no texto. Sem memória, na terceira pergunta, o agente listou todos os
códigos de alarme e devolveu a pergunta ao técnico — e como "E-102" estava na lista, a contagem deu
acerto. **Passou na contagem e não respondeu nada.** Por isso a conclusão vem da leitura das
respostas, com o placar servindo de guia. Isso está escrito na seção 6 do markdown.

**"Você não desenhou um cenário só para provar o que queria?"**

Ao contrário: desenhei o Cenário C esperando que ele exigisse as duas memórias, e a medição mostrou
que não exige — porque o manual diz "após **qualquer** aperto", então saber de quais parafusos se
tratava não fazia diferença. Relatei o erro de desenho em vez de esconder, e quem acabou provando a
necessidade da combinação foi o Cenário A.

**"Por que não confiar só no modelo, que já sabe muito?"**

Porque o manual é de equipamentos que não existem. Nada do que está nele pode ser deduzido. Foi
exatamente aí que o agente sem busca inventou o significado do alarme e liberou água no radiador.

**"Isso vale para qualquer sistema?"**

O efeito de a memória ancorar a busca no assunto anterior tende a piorar em conversas longas, que é
o caso de um chamado que se arrasta. A correção que eu recomendaria em seguida é buscar também com
as palavras originais do usuário, além da versão reescrita, e comparar os dois resultados.

## Em uma frase

A memória diz **sobre o quê** e a busca diz **o quê** — e a medição mostrou que a memória, ao
reescrever a pergunta, pode empurrar para fora da busca justamente o trecho que responderia.
