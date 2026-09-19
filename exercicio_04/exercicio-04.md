# Exercício 4 – Seleção de modelo, streaming e monitoramento

O código está em `exercicio_04/selecao_modelos.py`. Para executar: `uv run exercicio_04/selecao_modelos.py`

O programa roda as cinco partes em sequência, com pausas de 30 segundos no meio. As pausas existem porque a conta gratuita do Gemini limita o número de chamadas por minuto em cada modelo, e o programa faz várias chamadas seguidas.

## 1. Dois modelos, a mesma triagem

Dois agentes com as mesmas instruções de triagem receberam o mesmo chamado simples: "A lâmpada do painel da esteira 4 queimou. A esteira continua funcionando normalmente."

| Modelo | Tempo | Tokens | Resposta |
|---|---|---|---|
| `gemini-3.1-flash-lite` (barato) | 2,12 s | 95 | BAIXA prioridade, por ser falha estética que não compromete a operação nem a segurança |
| `gemini-3.6-flash` (mais caro) | 3,22 s | 470 | BAIXA prioridade, por ser falha de sinalização visual que não impacta operação, produtividade nem segurança |

Os dois acertaram a classificação, com respostas praticamente iguais. O modelo mais caro levou 50% mais tempo e gastou cinco vezes mais tokens, porque ele "pensa" antes de responder, e esse raciocínio também é cobrado.

### Justificativa da escolha

**Triagem simples: modelo barato (`gemini-3.1-flash-lite`).**

- **Custo:** a triagem é a tarefa mais repetida do sistema. Com dez filiais abrindo chamados o dia inteiro, o volume é grande. Como o resultado foi o mesmo, pagar quatro vezes mais por chamado não traz retorno.
- **Latência:** o técnico está no campo esperando a resposta. Cerca de 2 segundos contra 3,2 segundos faz diferença na fila de chamados.
- **Qualidade:** classificar um chamado em três níveis é uma tarefa fácil. As duas respostas foram equivalentes, o que mostra que o modelo maior está sobrando aqui.

**Diagnóstico complexo: modelo mais caro (`gemini-3.6-flash`).**

- **Qualidade:** o diagnóstico precisa cruzar várias informações do chamado (tempo até o desarme, nível de óleo, limpeza do radiador, aumento de pressão) e ainda ler trechos de manuais. Aqui o raciocínio a mais compensa. Na parte 3 o modelo ligou o aumento de pressão de 7 para 8,5 bar ao aquecimento e apontou a válvula termostática, uma conclusão que exige juntar dados.
- **Custo:** o diagnóstico complexo é raro perto da triagem, então o gasto maior fica diluído.
- **Latência:** alguns segundos a mais são aceitáveis, porque o técnico já está parado analisando a máquina.

Em resumo: o modelo barato faz o trabalho de volume, e o caro entra só quando a tarefa exige raciocínio. Isso é o que segura o orçamento de API das dez filiais.

## 2. A filial com outro provedor

Uma das filiais só tem contrato com o OpenRouter. Para atender a ela, o agente de triagem continua igual (mesmas `instructions`, mesmo `Agent`, mesmo `Runner`) e só muda o modelo passado: um `OpenAIChatCompletionsModel` com o cliente do OpenRouter e o modelo `deepseek/deepseek-v4-flash-0731:free`.

Isso funciona porque o OpenRouter usa a mesma interface da OpenAI. Muda só a chave e o endereço, lidos do `.env` (`OPENROUTER_API_KEY` e `OPENROUTER_BASE_URL`).

Resultado: mesma tarefa, mesma classificação (BAIXA prioridade), em 3,83 s e 272 tokens. Ou seja, trocar de provedor não exigiu mudar a lógica do agente.

## 3. Filial injetada pelo contexto e ModelSettings

**A filial pelo contexto.** A classe `ContextoDaFilial` guarda o identificador da filial. Ela é passada na execução com `Runner.run(agente, pergunta, context=contexto)`. A tool `consultar_filial` recebe o `RunContextWrapper` e lê o valor em `wrapper.context.filial_id`.

O ponto importante: esse identificador **não** está na pergunta enviada ao modelo. O modelo só descobre a filial se chamar a tool. Isso é o que o exercício 5 vai precisar, para buscar o manual certo sem que o técnico precise digitar o código da filial.

A prova disso está na saída: a linha `[tool consultar_filial] chamada pelo agente, filial do contexto: FIL-07` aparece durante a execução, e a resposta do agente começa citando a filial FIL-07.

**ModelSettings.** O agente de diagnóstico foi criado com `ModelSettings(temperature=0.2, max_tokens=600, include_usage=True, extra_args={"reasoning_effort": "none"})`. Os dois primeiros são os valores pedidos, diferentes do padrão (que deixa o modelo escolher).

A execução respeita a configuração, e isso aparece de duas formas na saída:

- O programa imprime os valores guardados no agente: `temperature configurada: 0.2` e `max_tokens configurado: 600`.
- O texto da resposta termina cortado no meio da palavra "separ", em "Verificar a pressão diferencial (ΔP) no filtro separ". O modelo não escolheu parar ali: ele bateu no limite de 600 tokens. Essa é a prova de que o `max_tokens` valeu.

O contador mostra 608 tokens gerados, um pouco acima do limite, e isso tem explicação: a execução fez duas chamadas ao modelo. A primeira foi curta, só para pedir a tool `consultar_filial` (cerca de 8 tokens), e a segunda foi a resposta, limitada a 600. O `usage` soma as duas. O limite de 600 vale para cada chamada, não para a execução inteira.

Os outros dois ajustes foram necessários por causa do provedor: o `reasoning_effort: "none"` desliga o raciocínio interno do Gemini, que consumia quase todo o `max_tokens` e deixava a resposta vazia; e o `include_usage=True` faz o provedor devolver a contagem de tokens quando a resposta vem em streaming (sem isso, o total volta zero).

## 4. Streaming e contagem de tokens

A parte 4 usa `Runner.run_streamed`. Diferente do `run`, ele devolve um objeto de execução, e os eventos são lidos com `async for evento in execucao.stream_events()`.

O programa filtra os eventos do tipo `response.output_text.delta`, que são os pedaços de texto, e imprime cada pedaço na hora, com `end=""` e `flush=True`. É assim que a interface de campo do técnico mostra a resposta aparecendo aos poucos, em vez de esperar tudo ficar pronto.

Na mesma execução aparecem outros eventos, como a chamada da tool. Por isso o filtro é necessário: sem ele, aparecia também o `{}` dos argumentos da tool no meio do texto.

Terminado o streaming, o total de tokens sai de `execucao.context_wrapper.usage`: 381 tokens de entrada e 608 de saída, 989 no total. Pelo mesmo motivo da parte 3, a saída passa de 600: são as duas chamadas somadas, a do pedido da tool e a da resposta final.

## 5. Dicionário de métricas

No fim, o programa monta o dicionário que no futuro vai alimentar o endpoint `GET /agent/status/{task_id}`:

`{'task_id': 'diagnostico-001', 'status': 'done', 'tempo_total_segundos': 9.26, 'total_tokens': 989}`

O tempo é medido com `time.time()` antes e depois da execução. O total de tokens vem do `usage`. O campo `status` é fixo em `"done"`, como o enunciado pede, porque aqui a execução já terminou quando as métricas são montadas. O `task_id` está fixo agora, e no serviço REST será o identificador do chamado.

## 6. Evidências

Os três prints são da mesma execução, das 19:22 às 19:25, rolando o terminal.

- Print 1 – Partes 1 e 2 (a mesma triagem nos dois modelos do Gemini e no OpenRouter, com tempo e tokens) e o começo da parte 3, com os valores do ModelSettings e a tool lendo a filial FIL-07 do contexto: `prints/Screenshot_20260919_192444.png`
- Print 2 – Fim da parte 3, com a resposta cortada pelo limite de tokens, e começo das partes 4 e 5, com a resposta saindo em streaming: `prints/Screenshot_20260919_192451.png`
- Print 3 – Fim das partes 4 e 5, com os tokens de entrada e saída e o dicionário de métricas com `status: done`: `prints/Screenshot_20260919_192501.png`
