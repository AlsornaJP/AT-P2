# Exercício 7 – Erros seguros e saída estruturada do diagnóstico

O código está em `exercicio_07/diagnostico_estruturado.py`. Para executar: `uv run exercicio_07/diagnostico_estruturado.py`

O programa usa o mesmo arquivo de manual do exercício 5 (`exercicio_05/manuais.json`) e roda as três partes em sequência, com pausas de 20 segundos, porque a conta gratuita do Gemini permite 15 chamadas por minuto.

## 1. Erro tratado sem quebrar a execução

Antes, quando o código não existia, a ferramenta devolvia um texto dizendo que não achou. Agora ela **lança uma exceção**: a classe `EquipamentoNaoEncontrado`, criada no próprio arquivo. Isso é melhor porque separa o caminho normal do caminho de erro, como se faz em qualquer programa Python.

Só que uma exceção dentro de uma ferramenta derruba a execução inteira do agente, e foi isso que parou o serviço de uma filial. A solução é a `failure_error_function`, passada no decorador: `@function_tool(failure_error_function=avisar_erro_ao_modelo)`.

A função `avisar_erro_ao_modelo` recebe o contexto da execução e a exceção. Ela não relança o erro: devolve um texto ao modelo, explicando que a consulta falhou e pedindo que o técnico confira o código no painel da máquina. Para o modelo, isso chega como se fosse a resposta da ferramenta, e ele continua trabalhando normalmente.

**Resultado da execução.** A pergunta foi sobre o equipamento inexistente XYZ-999. A saída mostra, em ordem: a ferramenta sendo chamada, a linha `[failure_error_function] a tool falhou: o código XYZ-999 não existe no manual.`, a confirmação `A execução não quebrou.` e, em seguida, a resposta do agente já estruturada, dizendo que o código não foi localizado no manual e que o técnico deve conferir o código diretamente no painel da máquina.

Ou seja: o erro aconteceu, foi tratado, e o painel de despacho ainda recebeu uma resposta com os três campos preenchidos, em vez de uma queda do serviço.

## 2. Saída estruturada com Pydantic

A classe `DiagnosticoEquipamento` é um `BaseModel` do Pydantic com três campos, todos textos: `codigo`, `causa_provavel` e `acao_recomendada`. Cada campo tem uma descrição escrita com `Field(description=...)`, que é enviada ao modelo junto com o formato esperado.

Essas descrições foram necessárias: sem elas, o modelo preencheu o campo `codigo` com o código do erro (`E-201`) em vez do código do equipamento (`TRN-300`). Com a descrição "o código do equipamento, por exemplo CMP-100", ele passou a preencher certo.

O `output_type=DiagnosticoEquipamento` no agente faz o SDK exigir esse formato do modelo e devolver um objeto Python pronto, e não texto livre. O programa comprova isso imprimindo `Tipo do objeto recebido: DiagnosticoEquipamento` e acessando cada campo separadamente, com `saida.codigo`, `saida.causa_provavel` e `saida.acao_recomendada`. É esse objeto que o painel de despacho consegue ler sempre da mesma forma.

Na pergunta sobre o compressor CMP-100 com erro E-102, os campos vieram com "válvula termostática travada" e "substituir o componente e registrar a troca no histórico", exatamente como está no manual.

## 3. Memória entre perguntas com SQLiteSession

A `SQLiteSession` guarda as mensagens da conversa em um arquivo SQLite, o `sessao.db`, dentro da pasta do exercício. Cada sessão tem um identificador, aqui `"chamado-001"`. Ao passar `session=sessao` no `Runner.run`, o SDK grava a pergunta e a resposta e, na execução seguinte, reenvia tudo ao modelo automaticamente.

**Primeira pergunta:** "O torno TRN-300 apresentou o erro E-201. Qual é a causa?" O agente consultou o manual e respondeu "filtro de ar saturado".

**Segunda pergunta:** "E qual a ação recomendada mesmo?" Essa pergunta não diz qual é o equipamento nem qual é o erro. Mesmo assim, o agente respondeu com o código TRN-300 e a ação "parar o equipamento e abrir chamado para a manutenção elétrica", que é o que o manual traz para o E-201. Repare que na saída não aparece nenhuma linha de chamada da ferramenta nessa segunda pergunta: a resposta veio só do histórico.

No fim, o programa mostra que ficaram 6 mensagens guardadas no `sessao.db`. O arquivo está no `.gitignore`, porque é um dado de execução, não código.

### Um detalhe do código que vale explicar

Na segunda pergunta, o agente é o mesmo, mas roda com a escolha de ferramenta travada em "none", o que é feito com `agente.clone(model_settings=ModelSettings(tool_choice="none"))`. Vale explicar por quê.

O motivo principal é um problema real que apareceu nos testes. Com `output_type` e ferramenta ao mesmo tempo, e já com o histórico da sessão carregado, o Gemini muitas vezes chamava a ferramenta de novo, recebia o mesmo dado, chamava outra vez, e a execução acabava parando no limite de rodadas do SDK, com o erro `MaxTurnsExceeded`. Isso acontece porque, com saída estruturada, o SDK só encerra quando o modelo devolve a resposta final em vez de uma nova chamada de ferramenta — enquanto ele insistir na ferramenta, a execução não termina.

A instrução em texto pedindo "se a informação já apareceu antes, responda direto, sem chamar a ferramenta de novo" não resolveu. Ela continua no agente, mas é só um pedido: o modelo obedece às vezes. Medindo, o agente sem restrição entrou em laço em 3 de 4 execuções; com `tool_choice="none"`, foram 6 execuções seguidas respondendo direto, nenhuma delas chamando a ferramenta. A lição é que instrução em texto influencia o modelo, mas só o parâmetro garante o comportamento — o mesmo ponto que apareceu no Exercício 6.

Vale registrar o que eu **não** encontrei. Cheguei a suspeitar que a culpa fosse de algo guardado no histórico da sessão, em especial as assinaturas de raciocínio que o Gemini grava junto com a chamada de ferramenta, ou o tamanho da resposta da ferramenta. Testei as duas coisas isoladamente e nenhuma explica o laço: o mesmo histórico falhou numa execução e passou em outra. O comportamento é variável, e é justamente por isso que depender da instrução em texto não serve.

O segundo motivo é didático: proibida de usar a ferramenta, a única fonte possível para a resposta é o histórico guardado na sessão, o que torna a demonstração da memória mais convincente.

Uma vantagem dessa solução em relação à anterior, que criava um segundo agente sem ferramenta, é que agora existe um agente só no exercício, como o enunciado descreve. O que muda entre as duas perguntas é apenas um parâmetro de execução.

Também testei o mesmo caso no OpenRouter, com o DeepSeek, e ele falhou de outro jeito: devolveu um JSON inválido para o formato pedido.

## 4. Evidências

- Print único – `prints/Screenshot_20260920_090841.png`: a execução completa das três partes, de uma vez só.
  - **Parte 1:** a chamada da ferramenta para o XYZ-999, a linha do `failure_error_function` avisando que o código não existe, a confirmação `A execução não quebrou.` e a resposta estruturada logo em seguida.
  - **Parte 2:** o CMP-100 com os três campos preenchidos a partir do manual.
  - **Parte 3:** a Pergunta 1 com a consulta ao manual e a Pergunta 2 **sem nenhuma linha de chamada da ferramenta**, respondendo TRN-300 com a ação correta, e o total de 6 mensagens guardadas no `sessao.db`.
