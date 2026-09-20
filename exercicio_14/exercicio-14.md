# Exercício 14 – Síntese: o agente como serviço REST completo

O código está em `exercicio_14/servico_completo.py`. São **dois terminais**:

- Para subir o serviço: `uv run exercicio_14/servico_completo.py`
- Para o fluxo completo, noutro terminal: `uv run exercicio_14/cliente_despacho.py`

O serviço roda na porta 8002, para conviver com os dos exercícios 12 e 13.

## 1. O que o serviço junta

Este exercício não constrói nada novo: ele costura o que já existe num fluxo que o sistema de despacho consegue consumir sozinho, sem tocar em código Python.

- Os modelos **`DiagnosticoEquipamento` e `PecaRecomendada` vêm do Exercício 8**, importados. Não são cópias: é o mesmo modelo aninhado de lá, com a lista de peças dentro do diagnóstico.
- A **ferramenta do manual com peças** também vem do Exercício 8. As peças só existem nesse manual, que é o do Exercício 5 acrescido delas — os equipamentos são os mesmos: CMP-100, TRN-300, EST-450, FRN-720 e BMB-210.
- A **busca semântica** vem do Exercício 11, sobre o manual longo do Exercício 10.
- O **padrão de submissão e consulta** vem do Exercício 13.

## 2. O agente integrador, com as duas fontes

O agente tem as duas ferramentas ao mesmo tempo, mais a saída estruturada. Cada fonte serve para uma coisa, e a instrução diz isso explicitamente:

A ferramenta do manual com peças dá a causa provável, a ação recomendada e, principalmente, a **lista de peças** — que não existe em nenhuma outra fonte. A busca semântica dá **detalhe de procedimento**, tirado do manual longo, que é somado ao campo `acao_recomendada`.

Essa divisão precisou ser dita em voz alta na instrução por causa do que o Exercício 11 mediu: um agente com duas fontes decide, sozinho, não usar uma delas. Aqui a instrução manda consultar as duas antes de responder, mesmo que ele ache que já sabe.

**Por que o detalhe do manual longo vai para dentro do `acao_recomendada`** e não para um campo próprio: o enunciado pede o `DiagnosticoEquipamento` do Exercício 8, e eu não posso acrescentar campos a ele sem deixar de ser o modelo pedido. Então a contribuição da segunda fonte enriquece um campo existente.

**Um risco conhecido, tratado.** Saída estruturada com ferramenta foi exatamente a combinação que entrou em laço no Exercício 7. Aqui há duas ferramentas, então o risco é maior. Por isso a execução tem limite de 8 rodadas, e o estouro desse limite é capturado: a tarefa termina em `error` explicando que o agente ficou chamando as ferramentas sem concluir, em vez de ficar presa para sempre. Na execução registrada o laço não aconteceu — a tarefa levou 4,7 segundos — mas a proteção está lá.

## 3. Os três endpoints e os códigos de resposta

| Chamada | Quando | Resposta |
|---|---|---|
| `POST /agent/run` | sempre | **202** com o `task_id` e o caminho para acompanhar |
| `GET /agent/status/{task_id}` | o `task_id` existe | **200** com `pending`, `done` ou `error` |
| `GET /agent/status/{task_id}` | o `task_id` nunca existiu | **404** com explicação |
| `GET /agent/response/{task_id}` | estado `done` | **200** com o `DiagnosticoEquipamento` |
| `GET /agent/response/{task_id}` | estado `pending` | **409** dizendo para acompanhar o status |
| `GET /agent/response/{task_id}` | estado `error` | **409** com o motivo da falha |
| `GET /agent/response/{task_id}` | o `task_id` nunca existiu | **404** com explicação |

O 202 do POST inclui o campo `onde_acompanhar`, com o caminho pronto do status. É uma gentileza com quem consome: o sistema de despacho não precisa montar a URL por conta própria.

## 4. A execução de ponta a ponta

A pergunta foi sobre o compressor CMP-100 com o erro E-102: "qual a causa, o que faço e que peças eu levo?".

**1. Submissão.** O `POST /agent/run` respondeu **202 em 0,004 segundos**, com o `task_id` `88eed4bb`.

**2. Pedido antes da hora, de propósito.** O cliente pediu o diagnóstico imediatamente e recebeu **409**, com a mensagem "o diagnóstico ainda não está pronto" e a orientação de acompanhar o status. Não é erro do serviço: é o recurso ainda não existir naquele estado.

**3. Acompanhamento.** Três consultas de status: `pending`, `pending`, `done`. A tarefa levou 4,7 segundos.

**4. Resultado.** O `GET /agent/response` devolveu **200** com o diagnóstico estruturado:

O campo `codigo` veio CMP-100 e o `causa_provavel`, "válvula termostática travada", os dois do manual com peças. A lista de peças veio com dois itens, cada um com nome, quantidade e prioridade: válvula termostática 3/4, quantidade 1, prioridade alta; e jogo de juntas, quantidade 2, prioridade média. São exatamente os dados do manual.

E o `acao_recomendada` mostra as duas fontes juntas: começa com "substituir o componente e registrar a troca no histórico", que é a ação do manual com peças, e continua com o aviso de que o erro exige parada imediata porque a válvula travada impede a circulação de óleo pelo radiador — isso não está no manual com peças, veio da busca semântica no manual longo.

O log do serviço confirma que as duas ferramentas foram chamadas: `consultar_manual_equipamento` para o CMP-100, e `buscar_no_manual` com a consulta "erro E-102 no CMP-100", que trouxe os trechos 11, 10, 12, 1 e 2 — a seção de alarmes do manual longo.

## 5. A decisão de projeto: o `task_id` que nunca existiu

Esta é a parte que o enunciado pede por escrito, e eu tenho as duas execuções para comparar.

### O que eu observei antes

O serviço do Exercício 13 procura o identificador direto no dicionário, sem verificar se ele existe. Pedi a ele o status de um `task_id` inventado e obtive:

**HTTP 500, com o corpo `Internal Server Error`** e, no log do serviço, o rastro completo da exceção `KeyError`.

Isso é ruim por três motivos, e nenhum deles é estético.

**Mente sobre quem errou.** O código 500 quer dizer "o servidor falhou". Mas o servidor não falhou: ele recebeu um endereço que não existe. A culpa é de quem perguntou, e a resposta está dizendo que é de quem respondeu. Um time de despacho que receber 500 vai abrir chamado com a equipe do serviço, quando o problema está no lado dele.

**Não diz nada.** O corpo é `Internal Server Error`, três palavras iguais para qualquer falha do mundo. Quem está do outro lado não tem como distinguir "esse identificador não existe" de "o serviço quebrou de verdade".

**Vaza informação.** O rastro de exceção no log expõe nomes de variáveis e caminhos de arquivo. Em produção, mensagens de erro detalhadas são material de reconhecimento para quem está sondando um serviço.

### A decisão

**Devolver 404 com uma explicação estruturada.**

O 404 é o código que diz "esse recurso não existe aqui", e é exatamente o caso: o `task_id` é o endereço de uma tarefa, e a tarefa não existe. É a mesma família de resposta que um endereço web errado recebe.

O corpo carrega quatro informações, e cada uma tem uma razão de estar lá: o aviso de que o `task_id` não foi encontrado; o identificador que foi pedido, para o outro lado conferir se digitou certo; uma explicação de **por que** isso pode acontecer; e o que fazer em seguida.

A explicação foi escrita com cuidado, porque existem dois motivos diferentes para um identificador não ser encontrado, e o serviço **não consegue distinguir os dois**: ou ele nunca foi emitido, ou ele foi emitido e se perdeu quando o serviço reiniciou, já que o registro fica em memória. A mensagem diz as duas possibilidades em vez de afirmar só a primeira. Seria mais bonito escrever "este identificador nunca existiu", mas seria mentira metade das vezes.

### Por que não as outras saídas

**Devolver 200 com o estado `unknown`** foi a alternativa que mais considerei. Ela tem uma vantagem real: o cliente trata tudo do mesmo jeito, lendo sempre o campo de estado. Recusei porque mistura duas coisas diferentes. `pending`, `done` e `error` são estados de uma tarefa que existe; "não existe" não é um estado da tarefa, é a ausência dela. E devolver 200 para um pedido malsucedido faz qualquer painel de monitoramento contar como sucesso.

**Devolver 204, sem conteúdo**, foi descartado porque perderia justamente a explicação, que é a parte útil.

**Devolver 400** seria dizer que o pedido está malformado, e não está: `00000000` é um identificador perfeitamente bem formado, que só não corresponde a nada.

### O que a execução mostrou

O cliente pediu o status e depois o diagnóstico do `task_id` inventado `00000000`. Os dois responderam **404**, com a explicação completa, e o serviço continuou atendendo normalmente. Nenhum rastro de exceção apareceu no log — só a linha `[404] task_id desconhecido: 00000000`, que é registro, não falha.

A diferença entre os dois prints é a mesma diferença entre um serviço que quebra e um que recusa.

## 6. O que continua limitado

O registro de tarefas segue sendo um dicionário na memória do processo. Isso tem uma consequência que o próprio texto do 404 admite: depois de uma reinicialização, todo `task_id` emitido antes passa a ser desconhecido. O sistema de despacho não tem como saber se o identificador se perdeu ou se nunca existiu, e nem o serviço tem.

Resolver isso não é questão de tratar melhor o erro: é trocar o dicionário por um banco, e as tarefas de fundo por uma fila que garanta que o trabalho não se perde. Foi o que ficou de fora destes três exercícios de serviço, e é o que eu faria em seguida.

## 7. Evidências

*(inserir os prints depois de tirá-los)*

- Print – o fluxo completo, os dois terminais: `prints/...`
  - No cliente: o 202 com o `task_id`, o 409 do pedido antes da hora, as consultas de status até `done`, o 200 com o diagnóstico e a lista de peças item a item, e por fim os dois 404 do `task_id` inventado.
  - No serviço: as chamadas às duas ferramentas, `consultar_manual_equipamento` e `buscar_no_manual`, a tarefa terminando em `done`, e as linhas `[404] task_id desconhecido` sem nenhum rastro de exceção.
- Print – o comportamento antigo, do Exercício 13: `prints/...`
  - O mesmo pedido, de um `task_id` inexistente, recebendo `HTTP 500 Internal Server Error`, e o rastro da exceção no log do serviço. É o contraste que justifica a decisão da seção 5.
