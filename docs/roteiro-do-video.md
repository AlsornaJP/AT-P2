# Roteiro do vídeo — AT-P2

Alvo: **4 min 40 s de fala**, deixando 20 segundos de folga nos 5 minutos. O texto abaixo está
escrito para ser falado, não lido. Fale devagar: se acelerar, sobra tempo; se atrasar, a seção
"O que cortar" no fim diz o que sacrificar.

Os três temas são os que o professor pediu. O resto do trabalho é citado em uma frase e mais nada.

---

## [0:00 – 0:20] Abertura

> Este trabalho são catorze exercícios que constroem um assistente de diagnóstico para técnicos de
> campo, do primeiro agente até um serviço REST completo. Nos cinco minutos eu vou explicar três
> decisões: a estrutura de dados do exercício oito, a estratégia de memória do onze, e o tratamento
> de erro do catorze.

**Na tela:** a pasta do projeto aberta, com os catorze exercícios à vista.

---

## [0:20 – 1:30] Exercício 8 — a estrutura de dados aninhada

> No exercício oito, o painel de despacho passou a precisar de uma lista de peças de reposição
> dentro do diagnóstico. A decisão era: uma lista aninhada, ou campos separados, tipo peça um,
> peça dois, peça três.
>
> Escolhi a lista aninhada, e o motivo principal é que campos separados obrigam a chutar um número
> máximo de peças na hora de escrever o modelo. Se eu reservo três e aparece um defeito com quatro,
> a quarta se perde, e corrigir isso significa mexer no modelo, no agente e no painel ao mesmo
> tempo. Se eu reservo dez, quase todo diagnóstico viaja com oito grupos de campos vazios.
>
> Com a lista, a quantidade de peças deixa de ser parte da estrutura e vira simplesmente um dado.
> Zero peça, duas ou sete são todas a mesma forma.
>
> Para quem consome isso no painel, muda três coisas. O painel percorre a lista em vez de ler campos
> fixos. Eu devolvo lista vazia em vez de campo nulo, então o caso de erro não vira exceção: 
> percorrer zero item simplesmente não desenha nada. E a quantidade é número, não texto, então dá
> para somar as peças de vários chamados e montar um pedido ao almoxarifado.
>
> Uma limitação que eu registrei: a prioridade é texto livre, como o enunciado pede. Então
> "urgentíssimo" passaria na validação. A garantia viria de declarar o campo com valores fixos.

**Na tela:** o `exercicio-08.md` na seção 4, e o print mostrando o diagnóstico com as duas peças.

---

## [1:30 – 3:15] Exercício 11 — memória e RAG

> O exercício onze junta as duas formas de memória: o histórico de conversa e a busca semântica.
> E pede para avaliar qual das duas basta sozinha.
>
> Eu poderia responder isso argumentando. Preferi medir: montei três cenários e rodei cada um com
> metade da memória desligada, para ver o que quebra. Também registrei, em cada pergunta, se o
> agente consultou o manual — porque resposta certa sem consulta não veio do manual, veio da cabeça
> do modelo, e o manual é de um equipamento fictício.
>
> O resultado: só memória nunca bastou. Sem a busca, o agente inventou o significado de um alarme e
> afirmou que dá para lavar o radiador com água, quando o manual diz o contrário. Só a busca basta
> quando a pergunta é completa, sem conversa anterior. E a combinação é necessária quando a conversa
> avança, que é o caso normal de um chamado.
>
> Mas o achado que eu mais quero mostrar é outro, e ele foi contra o que eu esperava.
>
> Quando o técnico pergunta "e depois de apertar, o que eu faço?", o agente reescreve a pergunta
> antes de buscar, e puxa o assunto da conversa anterior. Medindo: com as palavras do próprio
> técnico, o trecho certo do manual fica em primeiro lugar. Com a pergunta reescrita pelo agente,
> que enfiou a palavra "cabeçote" vinda da conversa, o mesmo trecho cai para quarto lugar e fica
> fora da janela de busca.
>
> Ou seja: a memória de conversa atrapalhou a recuperação semântica. Ancorou a busca no assunto que
> já tinha passado.
>
> E tem um detalhe contraintuitivo: a busca que deu errado tem nota de similaridade mais alta. 
> Porque a nota mede parecença com a pergunta que eu fiz, não acerto da resposta. Se a pergunta
> aponta para o lado errado, a busca acerta o alvo errado com precisão.
>
> Por isso a minha recomendação para produção é a combinação, mas com uma janela de busca maior, e
> sabendo que ter as duas ferramentas não garante que as duas sejam usadas: num dos testes o agente
> tinha as duas e errou porque decidiu não buscar.

**Na tela:** o print do diagnóstico, com as duas listas de similaridade lado a lado — 0,5869 em
primeiro e 0,7117 em quarto, com o "FICA DE FORA" visível.

---

## [3:15 – 4:20] Exercício 14 — o task_id que nunca existiu

> No exercício catorze o agente virou um serviço REST. O sistema de despacho submete a pergunta,
> recebe um identificador e consulta o resultado depois.
>
> A decisão que eu quero explicar é o que fazer quando alguém consulta um identificador que nunca
> existiu.
>
> O comportamento ingênuo, que eu deixei no exercício treze de propósito para comparar, é procurar
> a chave e deixar quebrar. Isso devolve erro quinhentos, "internal server error", com o rastro da
> exceção no log. Eu rodei os dois e tenho os prints.
>
> Escolhi devolver quatrocentos e quatro, com uma explicação. São três motivos.
>
> O quinhentos mente sobre quem errou. Ele quer dizer "o servidor falhou", mas o servidor não
> falhou: recebeu um endereço que não existe. Quem receber isso vai abrir chamado com a equipe do
> serviço, quando o problema está do lado dele.
>
> O quinhentos não diz nada. São três palavras iguais para qualquer falha do mundo.
>
> E o rastro de exceção vaza informação: expõe caminhos de arquivo e nomes de variável.
>
> O corpo do quatrocentos e quatro diz o identificador pedido, explica por que isso pode acontecer e
> diz o que fazer em seguida. E ele admite duas causas: ou o identificador nunca foi emitido, ou ele
> se perdeu quando o serviço reiniciou, porque o registro fica em memória. Seria mais bonito afirmar
> só a primeira, mas seria mentira metade das vezes, porque o serviço realmente não distingue as
> duas.
>
> Também considerei devolver duzentos com o estado "desconhecido". Recusei porque "não existe" não é
> um estado da tarefa — é a ausência dela.

**Na tela:** os dois prints lado a lado — a tela cheia de rastro de exceção do treze, e o 404 com a
explicação do catorze.

---

## [4:20 – 4:40] Fecho

> Fechando: são três decisões diferentes, mas com uma coisa em comum. Em todas elas eu tinha uma
> resposta pronta antes de medir, e a medição mudou a conclusão. Foi medindo que eu descobri que a
> memória atrapalha a busca, e que o agente com duas ferramentas às vezes usa só uma.
>
> Todo o restante está documentado nos markdowns de cada exercício. Obrigado.

---

## Como usar este roteiro

**Ensaie com cronômetro antes de gravar.** O texto foi dimensionado para um ritmo calmo. Se você
terminar em menos de quatro minutos, está falando rápido demais para assunto técnico — vale regravar
mais devagar.

**Os números que precisam sair certos.** São poucos, e são os que sustentam os argumentos:

- Exercício 11: o trecho certo em **1º** lugar com as palavras do técnico, em **4º** com a pergunta
  reescrita. E a nota da busca errada é **maior**.
- Exercício 14: **500** no comportamento ingênuo, **404** na decisão.

O resto pode ser dito em aproximação, sem decorar.

**A frase mais difícil de improvisar** é a do exercício 11 sobre a similaridade. Vale decorar quase
literal: *"a nota mede parecença com a pergunta, não acerto da resposta"*. Só depois cite os números.

## O que cortar, se estiver atrasado

Nesta ordem, da primeira perda para a última:

1. No exercício 8, o parágrafo das três consequências para o painel. Guarde só a primeira, a de
   percorrer a lista.
2. No exercício 14, o terceiro motivo (o vazamento de informação) e o parágrafo do duzentos com
   estado desconhecido.
3. No exercício 11, o último parágrafo, sobre ter as duas ferramentas e usar só uma.

**Não corte:** a comparação de primeiro contra quarto lugar do exercício 11, e o motivo de o
quinhentos mentir sobre quem errou, no catorze. São o núcleo de dois dos três temas pedidos.

## Se perguntarem depois

Os pontos frágeis que eu conheço estão reunidos em `guia-dos-exercicios.md`, nos itens "Defender".
O mais provável de virar pergunta, no exercício 11: o placar mostra empate de três a três entre a
busca sozinha e o agente completo. A resposta é que o placar conta se a palavra esperada apareceu, e
sem memória o agente devolveu a pergunta ao técnico em vez de responder — o que passa na contagem e
não serve para nada.
