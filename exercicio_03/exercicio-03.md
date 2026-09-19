# Exercício 3 – Primitivos do SDK e configuração do agente de diagnóstico

## 1. Os seis primitivos do OpenAI Agents SDK

Os primitivos são as peças básicas do SDK. Cada um cuida de uma parte do trabalho:

1. **Agent (agente):** é a configuração do agente. Nele ficam o nome, as instruções (a system message), o modelo, o formato da resposta (`output_type`) e as ferramentas. Criar um `Agent` não chama o modelo, só descreve quem ele é e como deve se comportar.
2. **Runner (executor):** é quem faz o agente funcionar. Ele recebe o agente e a pergunta, monta as mensagens, chama o modelo, executa ferramentas se o modelo pedir e repete isso até ter a resposta final. Tem três formas de uso: `run_sync` (espera a resposta travando o programa), `run` (assíncrono, com `await`) e `run_streamed` (entrega a resposta aos poucos).
3. **Tools (ferramentas):** são funções Python que o agente pode chamar, como consultar um banco de dados ou uma API. Com o decorador `@function_tool`, o SDK transforma a função em algo que o modelo sabe usar.
4. **Handoffs (transferências):** permitem que um agente passe a conversa para outro agente mais especializado. Por exemplo, um agente de triagem pode passar a conversa para o agente de diagnóstico.
5. **Guardrails (proteções):** são verificações que rodam na entrada ou na saída do agente. Elas podem bloquear uma pergunta fora do assunto antes de gastar o modelo principal, ou barrar uma resposta com problema.
6. **Tracing (rastreamento):** registra tudo o que aconteceu em uma execução: chamadas ao modelo, ferramentas usadas e transferências. Serve para depurar e acompanhar o agente. Neste projeto ele está desligado com `set_tracing_disabled(True)`, porque por padrão os registros vão para a plataforma da OpenAI e a chave usada é do Gemini.

## 2. Configuração do agente

O código está em `exercicio_03/agente_diagnostico.py`. Para executar: `uv run exercicio_03/agente_diagnostico.py`

O `Agent` é criado com os três itens pedidos, todos definidos de forma explícita:

- `instructions`: recebe a `MENSAGEM_DE_SISTEMA`, explicada na seção 3.
- `output_type`: recebe a classe `RespostaDiagnostico`, feita com o Pydantic. Ela obriga o modelo a devolver sempre três campos: `pergunta_aceita` (verdadeiro ou falso), `resposta` (o texto) e `regras_aplicadas` (a lista de regras de segurança usadas). Assim o programa recebe um objeto organizado, e não um texto solto.
- `model`: usa o `OpenAIChatCompletionsModel` com o modelo do Gemini lido do `.env` (`GEMINI_MODEL`), igual ao exercício 1.

### run_sync e run

- A função `executar_sincrono` usa `Runner.run_sync`. O programa para e espera a resposta, sem precisar de `async` e `await`.
- A função `executar_assincrono` usa `await Runner.run`, dentro de uma função `async`, iniciada com `asyncio.run`.

Os dois fazem a mesma coisa por baixo. A diferença é que o `run` assíncrono deixa o programa fazer outras coisas enquanto espera, o que é útil quando há várias perguntas ao mesmo tempo.

Um problema apareceu no caminho: na primeira versão, o cliente do Gemini era criado uma vez só, no começo do arquivo. O `run_sync` funcionou, mas o `run` deu o erro `is bound to a different event loop`. Isso acontece porque cada forma de execução usa o seu próprio "loop" de eventos, e o cliente fica preso ao primeiro. A solução foi colocar a criação do cliente e do agente dentro da função `criar_agente`, chamada em cada execução.

## 3. A system message

A `MENSAGEM_DE_SISTEMA` tem três partes, todas no mesmo texto:

1. **Papel:** o agente é um especialista em diagnóstico de equipamentos industriais da empresa fictícia Metalúrgica Andrade, e ajuda técnicos a descobrir a causa de falhas.
2. **Restrições de domínio:** só responde sobre diagnóstico e manutenção de equipamentos. Recusa perguntas administrativas (férias, salário, ponto, benefícios, escala). Quando recusa, deve marcar `pergunta_aceita` como falso e deixar a lista de regras vazia.
3. **Base de conhecimento:** três regras fictícias de segurança da empresa:
   - **SEG-01:** antes de mexer em qualquer máquina, desligar a chave geral e colocar o cadeado laranja com etiqueta de nome e matrícula.
   - **SEG-02:** equipamentos acima de 60 °C só podem ser tocados depois de 40 minutos desligados e depois de medir a temperatura com o termômetro infravermelho do setor.
   - **SEG-03:** mexer em painel elétrico exige dois técnicos no local, e pelo menos um com o crachá verde de habilitação elétrica.

As regras usam detalhes inventados (cadeado laranja, 40 minutos, crachá verde) de propósito. Se esses detalhes aparecem na resposta, fica claro que vieram da base de conhecimento, e não do que o modelo já sabia.

## 4. Confirmação de que o agente aplica as regras

**Execução com `run_sync`:** a pergunta foi "O forno de tratamento térmico 2 parou de esquentar e o painel elétrico dele está com cheiro de queimado. Vou abrir o painel agora para ver. O que devo verificar?". A situação envolve as três regras: mexer na máquina, um forno quente e um painel elétrico. O agente aceitou a pergunta, preencheu `regras_aplicadas` com SEG-01, SEG-02 e SEG-03 e, no texto, mandou verificar contatores, disjuntores e cabos de potência em busca de derretimento ou curto-circuito. Junto disso, citou a chave geral e o cadeado (SEG-01), o prazo de 40 minutos com medição da temperatura antes de tocar (SEG-02) e a presença de dois técnicos, sendo um com crachá verde (SEG-03). Os detalhes "40 minutos" e "crachá verde" só existem na base de conhecimento da system message, o que prova que o agente usou as regras.

**Execução com `run` assíncrono:** a pergunta foi "Quantos dias de férias eu ainda tenho para tirar este ano?". O agente marcou `pergunta_aceita` como falso, deixou `regras_aplicadas` vazia e respondeu que sua função é limitada ao suporte técnico e ao diagnóstico de falhas em equipamentos industriais, e que por isso não pode responder questões administrativas.

## 5. Evidências

- Print 1 – Execução do programa com as duas respostas: o `run_sync` aceitando a pergunta do forno e aplicando as três regras, e o `run` assíncrono recusando a pergunta sobre férias: `prints/Screenshot_20260919_190413.png`
