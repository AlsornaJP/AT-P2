# Exercício 12 – Expondo o agente via FastAPI

O código está em `exercicio_12/servico.py`. São **dois terminais**:

- Para subir o serviço: `uv run exercicio_12/servico.py`
- Para testar, noutro terminal: `uv run exercicio_12/pedir_diagnostico.py`

O `pedir_diagnostico.py` faz o papel do sistema de despacho descrito no enunciado: um programa de fora que fala com o agente por HTTP, sem importar código Python nenhum.

## 1. O agente é o do Exercício 11, importado de verdade

Nos exercícios anteriores eu vinha copiando código de um para o outro. Aqui a cópia seria de umas 150 linhas, o pipeline de RAG inteiro mais o agente, e ela envelheceria: qualquer ajuste no Exercício 11 deixaria de valer aqui.

Então o serviço acrescenta a pasta do Exercício 11 ao caminho de busca do Python, em três linhas, e importa o módulo. O enunciado diz "o agente integrador do Exercício 11", e assim é literalmente ele, com a instrução reforçada e a janela de 5 trechos que ficaram como padrão lá.

## 2. O trabalho caro acontece no arranque

O FastAPI tem um gancho que roda quando o serviço sobe e quando ele para. É ali que o manual é segmentado em trechos e transformado em vetores, uma única vez.

O log mostra: `pronto em 1.09s: 14 trechos indexados`. Depois disso, cada pergunta que chega já encontra o índice montado. Se essa preparação ficasse dentro do endpoint, toda pergunta pagaria de novo por um trabalho que não muda.

## 3. Os três modelos Pydantic

**`PerguntaDoTecnico`** é o corpo do POST: `codigo_equipamento` e `pergunta`, os dois com tamanho mínimo. É o que o enunciado chama de modelo de request.

**`ChamadoAceito`** é a resposta do POST: o identificador do chamado, a situação, o instante do recebimento e um aviso de que o agente vai demorar.

**`RespostaDeTeste`** é a resposta do GET: nome do serviço, situação e versão, todos fixos.

Os dois endpoints declaram o modelo de saída no decorador, com `response_model`. Isso faz o FastAPI validar também o que sai, e não só o que entra — se eu devolvesse um campo a mais ou um tipo errado, o erro apareceria no serviço, e não no sistema de despacho.

A validação de entrada aparece no print. O cliente envia de propósito um pedido sem o campo `pergunta`, e o serviço responde **422**, dizendo `campo ['body', 'pergunta']: Field required`. O agente nem chegou a ser acionado: o pedido parou na porta.

## 4. O POST que não espera

Esta é a parte central do enunciado.

O endpoint `POST /chamados` recebe a pergunta, gera um identificador, **agenda** o trabalho com `BackgroundTasks` e retorna. A tarefa agendada só começa a rodar depois que a função do endpoint termina e a resposta HTTP é enviada.

Escolhi responder com o código **202** em vez do 200 habitual. Em HTTP, 200 quer dizer "aqui está a resposta"; 202 quer dizer "recebi e aceitei, vou processar". Como o serviço está devolvendo um protocolo e não um diagnóstico, o 202 descreve melhor o que aconteceu, e avisa ao sistema de despacho que a resposta de verdade vem depois.

### A prova de que não bloqueia

Está nos dois prints, e são três evidências que se apoiam.

**Os tempos.** O cliente mediu: as duas chamadas POST levaram **0,001 e 0,003 segundos**. No log do serviço, as mesmas duas perguntas levaram **10,3 e 19,1 segundos** para o agente responder. O sistema de despacho foi liberado milhares de vezes mais rápido do que o trabalho de fato.

**A ordem no log.** O serviço registra `POST /chamados HTTP/1.1" 202 Accepted` e **só depois** registra `[fundo] começou a trabalhar`. Se o endpoint estivesse esperando o agente, a ordem seria a inversa. Essa ordem é a demonstração mais direta de que a resposta saiu antes de o trabalho começar.

**As duas ao mesmo tempo.** As duas tarefas de fundo começaram antes de qualquer uma terminar, e o serviço continuou atendendo enquanto trabalhava — tanto que ainda respondeu o terceiro pedido, o inválido, com 422, no meio disso.

## 5. O que o serviço faz com a resposta pronta

A tarefa de fundo guarda o resultado num dicionário na memória do processo e registra no log quanto tempo levou.

**Não criei endpoint para consultar esse resultado**, de propósito. O enunciado deste exercício pede um POST que aceita e um GET que devolve um valor fixo de teste; consultar o diagnóstico por identificador é assunto dos exercícios seguintes, e não quis invadir o escopo deles.

## 6. Um detalhe de implementação que quase estragou a evidência

As mensagens do serviço são escritas com uma função própria, que força a saída na hora.

Quando o Python percebe que a saída não é um terminal, ele guarda o texto num buffer e só escreve de vez em quando. Na primeira versão isso aconteceu: as minhas linhas apareceram todas juntas no fim, fora de ordem em relação às do uvicorn. Como a evidência deste exercício é justamente **a ordem** entre o `202 Accepted` e o `começou a trabalhar`, o log estaria mostrando uma sequência que não foi a real.

No seu terminal isso provavelmente não aconteceria, porque terminal tem comportamento diferente. Mas prefiro não depender disso.

## 7. Limitações conhecidas

**O dicionário em memória** some quando o serviço reinicia e não é compartilhado se houver mais de uma cópia do serviço no ar. Para o exercício está correto, porque o ponto é o `BackgroundTasks`. Num sistema de verdade isso seria um banco ou uma fila de mensagens.

**O `BackgroundTasks` roda dentro do mesmo processo do serviço.** Se o serviço for reiniciado no meio de um chamado, o trabalho se perde e ninguém é avisado. É a diferença entre uma tarefa de fundo e uma fila de verdade: a fila guarda o trabalho até alguém confirmar que terminou.

**O sistema de despacho não tem como saber que a resposta ficou pronta.** Ele recebe o identificador e, por enquanto, não tem onde consultá-lo. Resolver isso é o caminho natural dos próximos exercícios.

## 8. Evidências

*(inserir os prints depois de tirá-los)*

- Print – o terminal do serviço: `prints/...`
  - O arranque indexando os 14 trechos antes de aceitar requisições.
  - A ordem das linhas: o `202 Accepted` registrado **antes** do `[fundo] começou a trabalhar`.
  - As duas tarefas terminando em 10,3 e 19,1 segundos, com as respostas do agente.
  - O `422 Unprocessable Entity` do pedido inválido, no meio do trabalho.
- Print – o terminal do cliente: `prints/...`
  - O GET devolvendo o valor fixo.
  - Os dois POST aceitos em 0,001 e 0,003 segundos, com status 202.
  - O pedido inválido recebendo 422 e a mensagem da validação do Pydantic.
