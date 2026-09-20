# Exercício 14 — o task_id que nunca existiu, com exemplo

Anotação de estudo, para defender a decisão de devolver 404 em vez de deixar quebrar.

## A analogia, para começar

Alguém liga para a empresa e pede o ramal 9999, que não existe.

**Resposta ruim:** a recepcionista grita "o sistema telefônico quebrou!", desliga na cara, e antes
de desligar ainda lê em voz alta o diagrama da central telefônica. Quem ligou vai reclamar com a
equipe de telefonia — que não tem problema nenhum.

**Resposta boa:** "esse ramal não existe aqui. Você pediu o 9999. Pode ser que nunca tenha
existido, ou que fosse de alguém que saiu e a lista foi refeita. Se quiser, ligue para o ramal
principal e peça de novo."

A primeira é o erro 500. A segunda é o 404 que eu implementei.

## O caso concreto

O sistema de despacho submete uma pergunta e recebe um identificador, tipo `bb000c9c`. Depois
consulta o resultado com esse identificador.

E se ele consultar `00000000`, que nunca foi emitido?

**No exercício 13, que eu deixei ingênuo de propósito para comparar**, o código procura a chave no
registro e deixa quebrar. Rodei e obtive:

| o que o cliente recebe | o que aparece no log do serviço |
|---|---|
| `HTTP 500` | `Exception in ASGI application` |
| corpo: `Internal Server Error` | rastro completo, com caminhos de arquivo e linhas do FastAPI e do uvicorn, ocupando a tela |

**No exercício 14**, o mesmo pedido devolve `HTTP 404` com quatro informações no corpo:

| campo | conteúdo |
|---|---|
| erro | task_id não encontrado |
| task_id | 00000000 |
| explicacao | nunca foi emitido por este serviço, ou foi perdido quando o serviço reiniciou, porque o registro fica em memória |
| o_que_fazer | submeta a pergunta de novo em POST /agent/run |

E no log aparece uma linha só: `[404] task_id desconhecido: 00000000`. Registro, não falha.

## Os três motivos, um de cada vez

### 1. O 500 mente sobre quem errou

Os códigos HTTP se dividem em duas famílias. Os que começam com **4** querem dizer "o problema está
no pedido". Os que começam com **5** querem dizer "o problema está no servidor".

Aqui o servidor está perfeito: recebeu um endereço que não existe. **A culpa é de quem perguntou, e
o 500 diz que é de quem respondeu.**

A consequência é prática, não teórica. Um time de despacho que receber 500 vai abrir chamado com a
equipe do serviço, que vai investigar um problema que não tem. Com 404, o time sabe na hora que
precisa conferir o identificador do lado dele.

### 2. O 500 não diz nada

O corpo é `Internal Server Error`. Três palavras, iguais para qualquer falha do mundo: banco fora
do ar, erro de programação, disco cheio, identificador errado.

Quem está do outro lado **não consegue distinguir** "esse identificador não existe" de "o serviço
caiu". E são situações com reações opostas: uma se resolve conferindo o número, a outra exige
avisar alguém de madrugada.

### 3. O rastro de exceção vaza informação

O log do 500 mostra caminhos de arquivo, nomes de variável e a estrutura interna do programa.

Em produção isso é material de reconhecimento para quem estiver sondando o serviço. E, mesmo sem
pensar em ataque, é ruído: quem lê o log procurando um problema de verdade tropeça num rastro
enorme que era só um número errado.

## Por que não as alternativas

**Devolver 200 com o estado "desconhecido"** foi a alternativa que eu mais considerei, e ela tem
uma vantagem real: o cliente trataria tudo igual, lendo sempre o campo de estado.

Recusei porque mistura duas coisas. `pending`, `done` e `error` são estados de uma tarefa **que
existe**. "Não existe" não é um estado da tarefa — é a ausência dela. É como responder que o
funcionário está "de status inexistente" em vez de dizer que ninguém com aquele nome trabalha ali.

E tem um efeito colateral: devolver 200 faz qualquer painel de monitoramento contar o pedido como
sucesso.

**Devolver 204, sem conteúdo**, perderia justamente a explicação, que é a parte útil.

**Devolver 400** seria dizer que o pedido está malformado, e não está: `00000000` é um identificador
perfeitamente bem formado, que só não corresponde a nada.

## A parte que eu mais gosto: a mensagem admite duas causas

O texto do 404 diz que o identificador **nunca foi emitido, ou se perdeu quando o serviço
reiniciou**.

Seria mais bonito afirmar só a primeira. Mas seria mentira metade das vezes, porque o registro de
tarefas fica na memória do processo: depois de uma reinicialização, todo identificador emitido antes
some. E o serviço **genuinamente não consegue distinguir** um caso do outro.

Então a mensagem diz as duas possibilidades. Uma mensagem de erro que afirma mais do que o serviço
sabe é uma mensagem que engana com educação.

## Um caso vizinho, que resolvi diferente

E se o identificador existe, mas o diagnóstico ainda não ficou pronto?

Aí não é 404, porque o recurso existe. E não é erro de ninguém: o técnico só chegou cedo. Devolvo
**409**, dizendo que ainda não está pronto e orientando a acompanhar o status.

Isso mostra que a escolha do código não é decoreba: cada situação tem uma resposta que descreve o
que de fato aconteceu.

## Se me perguntarem

**"Não é exagero se preocupar com isso? É só um identificador errado."**
É o caso mais comum de todos, justamente por ser bobo: alguém copia e cola errado, um
identificador antigo fica guardado numa tela, o serviço reinicia. Um erro comum merece uma resposta
boa mais do que um erro raro.

**"Por que deixou o exercício 13 quebrado?"**
De propósito, para ter o antes e o depois medidos. A justificativa do exercício 14 pede que eu me
apoie em execução real, então rodei os dois serviços e tenho os dois prints. Está escrito no
markdown do 13 que o comportamento é deliberado.

**"E se o cliente ignorar o corpo da resposta?"**
Ele ainda recebe o 404, que sozinho já diz mais que o 500: identifica a família do problema. O
corpo é para quem quiser tratar bem; o código é para quem só olha o número.

## Em uma frase

O 500 diz que o servidor falhou quando quem errou foi quem perguntou; o 404 diz a verdade, mostra
qual identificador foi pedido e diz o que fazer em seguida.
