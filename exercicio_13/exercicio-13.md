# Exercício 13 – Padrão de submissão e consulta assíncrona

O código está em `exercicio_13/servico_tarefas.py`. São **dois terminais**:

- Para subir o serviço: `uv run exercicio_13/servico_tarefas.py`
- Para testar, noutro terminal: `uv run exercicio_13/acompanhar_tarefa.py`

O serviço roda na porta 8001, para poder conviver com o do Exercício 12, que usa a 8000. O agente é o do Exercício 11, importado, como no exercício anterior.

## 1. O padrão que o enunciado pede

O sistema de despacho não pode ficar esperando. Então a conversa entre ele e o serviço passa a ter duas etapas separadas:

1. **Submeter.** Ele manda a pergunta em `POST /agent/run` e recebe na hora um `task_id`, com o código 202. O diagnóstico ainda não existe.
2. **Consultar.** Quando quiser, ele chama `GET /agent/status/{task_id}` e recebe o estado: `pending` se ainda está sendo processado, `done` com a resposta, ou `error` com a descrição da falha.

A diferença para o Exercício 12 é que lá o identificador não servia para nada — o resultado ficava guardado e não havia como pedir. Aqui o identificador é a peça que liga as duas chamadas.

## 2. O registro das tarefas

É um dicionário onde a chave é o `task_id`. Cada entrada guarda o estado, a pergunta, e os campos que só existem depois: a resposta, o erro e quanto tempo levou.

**Um detalhe do código que vale explicar.** A entrada nasce no POST, com estado `pending`, **antes** de a resposta HTTP sair — e não dentro da função que roda em segundo plano.

O motivo é uma corrida. Se a entrada fosse criada só quando a tarefa de fundo começasse, haveria um instante em que o sistema de despacho já teria o `task_id` em mãos e a consulta ainda não encontraria nada. É curto, mas é o tipo de intervalo em que um sistema rápido cai. Criando a entrada antes de responder, o `task_id` já é consultável no instante em que é entregue.

O print comprova: a primeira consulta do cliente acontece a 0,0 segundo do POST e já devolve `pending`.

## 3. Os três estados

**`pending`** é o estado inicial, posto pelo POST.

**`done`** é posto pela tarefa de fundo quando o agente responde. Junto vão a resposta e o tempo que levou.

**`error`** é posto quando alguma coisa dá errado. Toda a execução em segundo plano está dentro de um `try/except`, e isso não é zelo excessivo: **se uma exceção escapasse dali, ela sumiria em silêncio.** A tarefa de fundo roda depois que a resposta HTTP já foi enviada, então não existe ninguém para receber o erro. A tarefa ficaria `pending` para sempre, e o sistema de despacho ficaria consultando um estado que nunca mudaria.

## 4. Como o estado de erro foi demonstrado

Aqui preciso ser claro sobre uma escolha.

O `try/except` cobre falhas reais, mas falha real não acontece na hora em que a gente quer mostrar. Eu não quis inventar um erro de mentira, do tipo "se a pergunta for X, levante uma exceção", porque isso não exercita o caminho de verdade.

O que fiz foi um campo opcional no pedido, `usar_modelo_invalido`, que faz aquela tarefa apontar para um nome de modelo que não existe. O provedor recusa a chamada e devolve um erro autêntico, que sobe pela mesma pilha e cai no mesmo `try/except`. O erro guardado no print é este, na íntegra: `NotFoundError: Error code: 404 - models/modelo-que-nao-existe is not found for API version v1main`.

**Esse campo existe só para o teste e não faria parte de um serviço de produção.** Ninguém deixa o cliente escolher como quebrar o servidor. Registro isso aqui em vez de esconder o campo.

Vale notar uma coisa que o print mostra: a tarefa com erro falhou em **0,3 segundo**, muito antes das que dão certo. Faz sentido — o provedor recusa o nome do modelo na primeira chamada, sem processar nada.

## 5. O que a execução mostrou

**Caso 1, o caminho normal.** O POST respondeu em 0,003 segundos com o `task_id` `ce2d9ba9` e o estado `pending`. A primeira consulta, imediata, devolveu `pending`. A segunda, três segundos depois, devolveu `done`, com a resposta sobre os intervalos de troca do óleo: primeira troca em 500 horas, depois a cada 4.000 horas ou 12 meses. O log do serviço mostra que o agente consultou o manual e levou 1,9 segundo.

**Caso 2, a falha.** O POST respondeu igualmente rápido, com o `task_id` `8f5fc019`. A primeira consulta devolveu `pending`; a segunda, `error`, com a mensagem do provedor guardada. O serviço continuou no ar normalmente: a falha ficou contida dentro da tarefa.

Nos dois casos o sistema de despacho foi liberado em milésimos de segundo e voltou para consultar quando quis. É exatamente o que o contexto do enunciado pede.

## 6. Uma coisa deliberadamente não tratada

**Consultar um `task_id` que não existe quebra o serviço, com erro 500.** O código procura a chave no dicionário e não a encontra.

Isso é assim de propósito neste exercício, e não por descuido. Tratar esse caso é o assunto do Exercício 14, e resolvê-lo aqui deixaria o próximo sem tema. Registro para que fique claro que o comportamento é conhecido.

O que **está** tratado é a entrada do POST, pelo Pydantic: um pedido sem pergunta, ou com pergunta curta demais, é recusado com 422 antes de qualquer processamento, como no Exercício 12.

## 7. Limitações que continuam valendo

São as mesmas do Exercício 12, e vale repetir porque este exercício se apoia nelas.

O registro de tarefas é um dicionário na memória do processo: some quando o serviço reinicia, e não é compartilhado se houver mais de uma cópia do serviço no ar. Numa reinicialização, tarefas que estavam `pending` desaparecem sem deixar rastro — o sistema de despacho ficaria com um `task_id` que, a partir dali, não existe mais. Num sistema de verdade, o registro seria um banco, e as tarefas iriam para uma fila que garante que o trabalho não se perde.

## 8. Evidências

*(inserir os prints depois de tirá-los)*

- Print – o terminal do cliente: `prints/...`
  - Caso 1: o POST respondendo em 0,003 s com 202 e o `task_id`, a consulta 1 em `pending`, a consulta 2 em `done`, e a resposta do agente.
  - Caso 2: o mesmo padrão terminando em `error`, com a mensagem do provedor.
- Print – o terminal do serviço: `prints/...`
  - O arranque indexando os trechos.
  - Para cada tarefa: o `202 Accepted`, o `[fundo] começou (estado atual: pending)`, as linhas de consulta mostrando o estado mudando, e o desfecho `-> done` ou `-> error`.
  - Os `200 OK` das consultas de status intercalados com o trabalho do agente.
