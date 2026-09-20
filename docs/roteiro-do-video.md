# Roteiro do vídeo — AT-P2

Dimensionado para **4 min 30 s de fala** a um ritmo calmo, deixando folga nos 5 minutos. O texto
está escrito para ser falado, não lido.

Os três temas são os que o professor pediu. O resto do trabalho é citado em uma frase.

---

## [0:00 – 0:18] Abertura

> Este trabalho são catorze exercícios que constroem um assistente de diagnóstico para técnicos de
> campo, do primeiro agente até um serviço REST. Vou explicar três decisões: a estrutura de dados do
> exercício oito, a estratégia de memória do onze e o tratamento de erro do catorze.

**Na tela:** a pasta do projeto, com os catorze exercícios à vista.

---

## [0:18 – 1:15] Exercício 8 — a estrutura de dados aninhada

> No exercício oito, o diagnóstico passou a precisar de uma lista de peças de reposição dentro dele.
> A decisão era: lista aninhada, ou campos separados, tipo peça um, peça dois, peça três.
>
> Escolhi a lista, porque campos separados obrigam a chutar um número máximo de peças. Se eu reservo
> três e aparece um defeito com quatro, a quarta se perde — e corrigir isso significa mexer no
> modelo, no agente e no painel ao mesmo tempo.
>
> Com a lista, a quantidade deixa de ser parte da estrutura e vira um dado. Zero, duas ou sete peças
> são a mesma forma. O painel percorre a lista em vez de ler campos fixos. E no caso de erro eu
> devolvo lista vazia, não nulo: percorrer zero item simplesmente não desenha nada, sem exceção.
>
> Uma limitação que eu registrei: a prioridade é texto livre, como o enunciado pede. Então
> "urgentíssimo" passaria na validação.

**Na tela:** o `exercicio-08.md` na seção 4, e o print com o diagnóstico e as duas peças.

---

## [1:15 – 2:55] Exercício 11 — memória e RAG

> O exercício onze junta as duas formas de memória: o histórico de conversa e a busca semântica. E
> pede para avaliar qual delas basta sozinha.
>
> Eu poderia responder argumentando. Preferi medir: rodei três cenários com metade da memória
> desligada, para ver o que quebra. E registrei, em cada pergunta, se o agente consultou o manual —
> porque resposta certa sem consulta veio da cabeça do modelo, e o manual é de um equipamento
> fictício.
>
> Só memória nunca bastou: sem a busca, o agente afirmou que dá para lavar o radiador com água,
> quando o manual diz o contrário. E a combinação é necessária quando a conversa avança, que é o
> caso normal de um chamado.
>
> Mas o achado principal foi contra o que eu esperava.
>
> Quando o técnico pergunta "e depois de apertar, o que eu faço?", o agente reescreve a pergunta
> antes de buscar, puxando o assunto da conversa. Medindo: com as palavras do próprio técnico, o
> trecho certo do manual fica em primeiro lugar. Com a pergunta reescrita, que enfiou a palavra
> "cabeçote", o mesmo trecho cai para quarto e sai da janela de busca.
>
> Ou seja: a memória de conversa atrapalhou a recuperação semântica.
>
> E a busca que deu errado tem nota de similaridade mais alta. Porque a nota mede parecença com a
> pergunta, não acerto da resposta.
>
> Por isso eu recomendo a combinação, mas com uma janela de busca maior.

**Na tela:** o print do diagnóstico, com as duas listas lado a lado: 0,5869 em primeiro, 0,7117 em
quarto, com o "FICA DE FORA" visível.

---

## [2:55 – 4:10] Exercício 14 — o task_id que nunca existiu

> No catorze o agente virou serviço REST: o despacho submete a pergunta, recebe um identificador e
> consulta o resultado depois.
>
> A decisão é o que fazer quando consultam um identificador que nunca existiu.
>
> O comportamento ingênuo, que eu deixei no exercício treze de propósito para comparar, é procurar a
> chave e deixar quebrar. Isso devolve erro quinhentos, com o rastro da exceção no log. Rodei os
> dois e tenho os prints.
>
> Escolhi devolver quatrocentos e quatro, por três motivos.
>
> O quinhentos mente sobre quem errou: ele diz que o servidor falhou, mas o servidor recebeu um
> endereço que não existe — e quem recebe isso abre chamado com a equipe errada. O quinhentos não
> diz nada: são três palavras iguais para qualquer falha. E o rastro de exceção vaza informação,
> expondo caminhos de arquivo.
>
> O corpo do quatrocentos e quatro diz qual identificador foi pedido e o que fazer em seguida. E ele
> admite duas causas: ou nunca foi emitido, ou se perdeu num reinício, porque o registro fica em
> memória. Seria mais bonito afirmar só a primeira, mas seria mentira metade das vezes.

**Na tela:** os dois prints lado a lado — a tela cheia de rastro de exceção do treze, e o 404 com a
explicação do catorze.

---

## [4:10 – 4:30] Fecho

> São três decisões diferentes, com uma coisa em comum: em todas eu tinha uma resposta pronta antes
> de medir, e a medição mudou a conclusão. O restante está documentado nos markdowns de cada
> exercício. Obrigado.

---

## Como usar este roteiro

**Ensaie com cronômetro antes de gravar.** Se você terminar em menos de quatro minutos, está
falando rápido demais para assunto técnico.

**Os números que precisam sair certos** são só estes:

- Exercício 11: trecho certo em **1º** lugar com as palavras do técnico, em **4º** com a pergunta
  reescrita — e a nota da busca errada é **maior**.
- Exercício 14: **500** no ingênuo, **404** na decisão.

**A frase mais difícil de improvisar** é a da similaridade. Vale decorar quase literal: *"a nota
mede parecença com a pergunta, não acerto da resposta"*. Só depois cite os números.

## O que cortar, se estiver atrasado

Nesta ordem:

1. No exercício 8, a frase sobre a lista vazia e o campo nulo.
2. No exercício 14, o terceiro motivo, o do vazamento de informação.
3. No exercício 11, a frase da janela de busca maior, no fim.

**Não corte:** a comparação de primeiro contra quarto lugar do onze, e o motivo de o quinhentos
mentir sobre quem errou, no catorze. São o núcleo de dois dos três temas pedidos.

## Se perguntarem depois

Os pontos frágeis estão reunidos em `guia-dos-exercicios.md`, nos itens "Defender". O mais provável
de virar pergunta, no exercício 11: o placar mostra empate de três a três entre a busca sozinha e o
agente completo. A resposta é que o placar só conta se a palavra esperada apareceu, e sem memória o
agente devolveu a pergunta ao técnico em vez de responder — o que passa na contagem e não serve
para nada.
