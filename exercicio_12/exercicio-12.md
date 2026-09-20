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

O log mostra: `pronto em 1.23s: 14 trechos indexados`. Depois disso, cada pergunta que chega já encontra o índice montado. Se essa preparação ficasse dentro do endpoint, toda pergunta pagaria de novo por um trabalho que não muda.

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

Está nos prints, e são três evidências que se apoiam.

**Os tempos.** O cliente mediu: o GET respondeu em 0,003 segundos e as duas chamadas POST em **0,002 e 0,004 segundos**. No log do serviço, as mesmas duas perguntas levaram **7,9 e 19,6 segundos** para o agente responder. O sistema de despacho foi liberado cerca de cinco mil vezes mais rápido do que o trabalho levou de fato.

**A ordem no log.** O serviço registra `POST /chamados HTTP/1.1" 202 Accepted` e **só depois** registra `[fundo] começou a trabalhar`. Isso acontece nas duas perguntas. Se o endpoint estivesse esperando o agente, a ordem seria a inversa. É a demonstração mais direta de que a resposta saiu antes de o trabalho começar.

**A ordem em que terminaram.** Esta é a evidência mais bonita, e eu não a tinha planejado. O chamado `237cc967`, o primeiro a chegar, terminou em 19,6 segundos. O chamado `048cbd19`, que chegou **depois**, terminou em 7,9 segundos — ou seja, **antes**. As duas tarefas estavam rodando ao mesmo tempo, e quem acabou primeiro foi quem teve a resposta mais rápida do provedor, não quem chegou primeiro.

Num serviço que bloqueasse, isso seria impossível: a segunda pergunta nem teria começado antes de a primeira terminar.

E, no meio disso tudo, o serviço ainda respondeu o terceiro pedido, o inválido, com `422 Unprocessable Entity`. Ele continuou atendendo enquanto trabalhava.

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

São três prints, de dois terminais. Os identificadores dos chamados, `237cc967` e `048cbd19`, aparecem nos dois lados e ligam uma imagem à outra.

- **`prints/Screenshot_20260920_124316.png`** – o serviço subindo. As linhas do arranque aparecem entre o `Waiting for application startup` e o `Application startup complete`: `pronto em 1.23s: 14 trechos indexados`. O índice fica pronto antes de o serviço aceitar a primeira requisição.
- **`prints/Screenshot_20260920_124409.png`** – o log do serviço durante o atendimento. Mostra, em ordem: o `GET /teste` com 200; os dois POST com `202 Accepted` **antes** das linhas `[fundo] começou a trabalhar`; o `422 Unprocessable Entity` do pedido inválido no meio do trabalho; e as duas tarefas terminando fora de ordem, `048cbd19` em 7,9 segundos e `237cc967` em 19,6 segundos, com as respostas do agente.
- **`prints/Screenshot_20260920_124502.png`** – o terminal do cliente. O GET devolvendo o valor fixo em 0,003 segundos; os dois POST aceitos em 0,002 e 0,004 segundos, com status 202 e os identificadores dos chamados; e o pedido sem o campo `pergunta` recebendo 422 com a mensagem `campo ['body', 'pergunta']: Field required`.
