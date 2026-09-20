# Mapa de fala — vídeo do AT-P2

Apoio para falar com as suas palavras, não para ler. Os pontos estão na ordem e cada bloco diz o que
é obrigatório sair da sua boca. O resto é seu.

O roteiro corrido continua em `roteiro-do-video.md`, e serve para **uma coisa**: ler uma vez com
cronômetro para você sentir qual ritmo cabe em cinco minutos. Depois, esqueça-o.

---

## A regra do relógio

Três marcas. Se passar delas, corte e siga em frente — atrasar no começo é o que estoura o vídeo.

| momento | você deve estar |
|---|---|
| **0:20** | terminando a abertura |
| **1:20** | entrando no exercício 11 |
| **3:00** | entrando no exercício 14 |
| **4:30** | fechando |

Se às 3:00 você ainda estiver no 11, **pule direto para o 14**. O 14 não pode ficar de fora: é um
dos três temas pedidos. Melhor falar pouco dos três do que bem de dois.

---

## Abertura — até 0:20

**A única coisa obrigatória:** dizer que são catorze exercícios que constroem um assistente de
diagnóstico, do primeiro agente até um serviço REST, e anunciar os três temas.

Decore só a última frase, porque anúncio malfeito compromete o resto:
> "Vou explicar três decisões: a estrutura de dados do oito, a estratégia de memória do onze e o
> tratamento de erro do catorze."

---

## Exercício 8 — até 1:20 (cerca de 1 minuto)

**A ideia que precisa sair:** campos separados obrigam a chutar um máximo de peças; a lista faz a
quantidade virar dado.

Os pontos, nesta ordem:

1. O painel passou a precisar de uma lista de peças dentro do diagnóstico.
2. As duas opções: lista aninhada, ou peça um, peça dois, peça três.
3. **O argumento:** reservei três, aparece um defeito com quatro, a quarta se perde — e consertar
   significa mexer no modelo, no agente e no painel ao mesmo tempo.
4. Com a lista, zero, duas ou sete peças são a mesma forma.
5. **A limitação que eu assumo:** prioridade é texto livre, "urgentíssimo" passaria na validação.

Se sobrar fôlego, acrescente: no caso de erro devolvo lista vazia, não nulo, então percorrer zero
item não desenha nada e não existe caso especial.

Se estiver atrasado, corte o ponto 5.

---

## Exercício 11 — até 3:00 (cerca de 1 minuto e 40)

É o bloco mais longo e o mais fácil de se perder. Ele tem **duas metades**: como eu avaliei, e o que
eu descobri. Não misture.

**Primeira metade — o método:**

1. O exercício junta memória de conversa e busca semântica, e pede qual basta sozinha.
2. **A decisão de método:** em vez de argumentar, desliguei metade da memória de cada vez para ver
   o que quebra.
3. Também registrei se o agente consultou o manual — resposta certa sem consulta veio da cabeça do
   modelo, e o manual é de equipamento inventado.
4. Sem busca, o agente **inventa**: disse que dá para lavar o radiador com água, o manual diz o
   contrário.

**Segunda metade — o achado.** Anuncie que foi contra o que você esperava, e conte como cena:

5. O técnico pergunta "e depois de apertar, o que eu faço?".
6. O agente reescreve a pergunta antes de buscar e **puxa "cabeçote" da conversa anterior**.
7. Resultado: o trecho certo cai de primeiro para quarto lugar e sai da janela de busca.
8. **A memória atrapalhou a busca.**
9. E o contraintuitivo: a busca errada tem nota **maior**.

Decore literal só esta, que é a frase que ninguém improvisa bem:
> "A nota mede parecença com a pergunta, não acerto da resposta."

Os números: **primeiro contra quarto lugar**. Se lembrar do 0,5869 e do 0,7117, ótimo; se não,
diga "cinquenta e oito centésimos contra setenta e um" ou só as posições.

Se estiver atrasado, corte o ponto 4 e vá direto para a cena.

---

## Exercício 14 — até 4:30 (cerca de 1 minuto e 15)

**A ideia que precisa sair:** o 500 mente sobre quem errou.

Os pontos, nesta ordem:

1. O agente virou serviço: submete, recebe identificador, consulta depois.
2. A pergunta é o que fazer quando consultam um identificador que nunca existiu.
3. Deixei o exercício 13 ingênuo de propósito, para comparar: ele devolve 500 com o rastro da
   exceção. **Rodei os dois e tenho os prints.**
4. **Motivo um:** o 500 quer dizer "o servidor falhou", mas o servidor recebeu um endereço errado.
   Quem recebe isso abre chamado com a equipe errada.
5. **Motivo dois:** "internal server error" são três palavras iguais para qualquer falha do mundo.
6. **Motivo três:** o rastro vaza caminhos de arquivo.
7. O 404 diz qual identificador foi pedido, por que isso acontece e o que fazer.

Se sobrar fôlego, o melhor extra é: a mensagem admite duas causas — nunca existiu, ou se perdeu num
reinício — porque o serviço realmente não distingue as duas.

Se estiver atrasado, corte os motivos dois e três. O motivo um sozinho sustenta a decisão.

---

## Fecho — até 4:40

**A única coisa obrigatória:** amarrar os três numa ideia só.

> "Nas três eu tinha uma resposta pronta antes de medir, e a medição mudou a conclusão."

Depois diga que o restante está documentado nos markdowns e agradeça. Não acrescente nada aqui:
fecho improvisado é onde o tempo estoura.

---

## Se travar no meio

Duas saídas, nesta ordem de preferência:

**Volte para o argumento central do bloco.** Cada um tem um, e eles estão em negrito acima. Repetir
o argumento com outras palavras soa como ênfase, não como travada.

**Passe para o próximo bloco.** Ninguém percebe que você pulou um ponto. Todo mundo percebe silêncio
de dez segundos.

## O que não pode faltar, se tudo der errado

Três frases. Se só isso sair, o vídeo cumpriu o que o professor pediu:

1. Campos separados obrigam a chutar um máximo de peças; a lista faz a quantidade virar dado.
2. A memória reescreveu a pergunta e empurrou o trecho certo de primeiro para quarto lugar.
3. O 500 diz que o servidor falhou quando quem errou foi quem perguntou.
