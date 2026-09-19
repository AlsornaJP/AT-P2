# Exercício 6 – Controle de seleção de tool e histórico de execução

São dois programas nesta pasta:

- `exercicio_06/gerar_historico.py`: cria o `historico.json`, com o histórico de serviços já executados em cada equipamento. Usa seed fixa (7), como no exercício 5. Para executar: `uv run exercicio_06/gerar_historico.py`
- `exercicio_06/controle_tools.py`: o programa do exercício. Para executar: `uv run exercicio_06/controle_tools.py`

A ferramenta do manual é a mesma do exercício 5 e lê o mesmo arquivo `exercicio_05/manuais.json`.

## 1. Duas ferramentas parecidas

A segunda ferramenta, `consultar_historico_manutencao`, tem nome e descrição parecidos com a do manual. As duas recebem o mesmo parâmetro (o código do equipamento) e devolvem dados do mesmo equipamento. A diferença é o conteúdo: uma traz códigos de erro e causas de falha, a outra traz serviços já feitos, com data, técnico e horas paradas.

Cada ferramenta existe em duas versões no código, com a mesma função por dentro e descrições diferentes:

- **Versão vaga:** "Consulta informações técnicas de um equipamento industrial pelo código" e "Consulta informações de manutenção de um equipamento industrial pelo código".
- **Versão reescrita:** diz em letras maiúsculas do que se trata (MANUAL DE FÁBRICA ou HISTÓRICO DE SERVIÇOS JÁ EXECUTADOS), lista o que cada uma contém e, principalmente, diz o que ela **não** contém. A do manual avisa que não tem datas nem nomes de técnicos; a do histórico avisa que não explica códigos de erro.

### Por que o agente escolhe uma ou outra

O modelo não vê o código da função. Ele só recebe o nome, a descrição e os parâmetros de cada ferramenta. A escolha é feita comparando o texto da pergunta com esses textos. Quando as descrições são parecidas e a pergunta não deixa claro o que se quer, não existe um critério para decidir, e o modelo tende a chamar as duas por segurança, ou escolher uma sem motivo forte.

### O que as execuções mostraram

A mesma pergunta foi feita com as duas versões de descrição. O modelo usado é o `deepseek/deepseek-v4-flash-0731:free`, pelo OpenRouter. A tabela abaixo é a execução dos prints, das 19:57 às 19:59.

| Situação | Ferramentas chamadas |
|---|---|
| 1a – pergunta neutra ("Preciso de informações sobre o compressor CMP-100"), descrições vagas | 2 |
| 1b – pergunta neutra, descrições reescritas | 2 |
| 1c – pergunta do manual ("O que significa o erro E-102?"), descrições vagas | 2 |
| 1d – pergunta do manual, descrições reescritas | 2 |
| 1e – pergunta do histórico ("Quantas horas ficou parado?"), descrições vagas | 2 |
| 1f – pergunta do histórico, descrições reescritas | **1** |

Com as descrições vagas, o agente chamou as duas ferramentas em todas as perguntas, inclusive nas específicas. Nada nas descrições dizia que uma delas não serviria, então ele buscou os dois arquivos por segurança.

Com as descrições reescritas, a pergunta do histórico passou a chamar só uma ferramenta (1f), o que economiza uma leitura de arquivo e reduz o texto enviado ao modelo na rodada seguinte. Já a pergunta do manual continuou chamando as duas (1d).

**A escolha varia entre execuções.** Em um teste que rodei antes dos prints, com o mesmo código e a mesma pergunta, a situação 1d chamou só uma ferramenta. Isso acontece porque a escolha da ferramenta é uma decisão do modelo, e modelos não dão sempre a mesma resposta. Ou seja: descrições claras **aumentam a chance** de o agente chamar só o necessário, mas não garantem isso. Quando a garantia é obrigatória, como em um teste automatizado, o jeito certo é o `tool_choice` da parte 2, que não depende da vontade do modelo.

Na pergunta neutra, as duas ferramentas são chamadas nas duas versões, e isso está certo: quem faz uma pergunta genérica realmente precisa dos dois tipos de dado.

### Observação sobre o modelo

Antes de usar o OpenRouter, rodei o mesmo teste com o `gemini-3.1-flash-lite`. Nele, as descrições vagas já bastavam: o modelo acertava a escolha sozinho. Ou seja, o problema relatado pelo time de qualidade depende do modelo. Quanto mais simples o modelo, mais ele depende de descrições bem escritas, e é isso que faz o mesmo código se comportar de forma parecida em provedores diferentes.

## 2. tool_choice e stop_on_first_tool

A mesma pergunta foi feita nas duas configurações: "O compressor CMP-100 apresentou o erro E-102. Me explique a situação desse equipamento."

**`tool_choice="consultar_historico_manutencao"`** (em `ModelSettings`) obriga o modelo a chamar essa ferramenta na primeira rodada, mesmo que a pergunta seja sobre um código de erro. É o que se usa em teste automatizado, para garantir que o caminho testado é sempre o mesmo. Resultado: **3 chamadas ao modelo**. A primeira decidiu chamar a ferramenta obrigatória, a segunda ainda pediu a ferramenta do manual (o agente entendeu que faltava a explicação do erro) e a terceira escreveu o texto final.

**`tool_use_behavior="stop_on_first_tool"`** (no `Agent`) encerra a execução assim que a primeira ferramenta responde. O resultado final vira a saída crua da ferramenta, o JSON do histórico, sem nenhum texto escrito pelo modelo. Resultado: **1 chamada ao modelo**.

**Comparação:** 3 chamadas contra 1. Esse é exatamente o problema que o time de qualidade relatou: o agente continuava gerando texto depois de a ferramenta já ter respondido. Quando o sistema só precisa do dado (por exemplo, para preencher uma tela do aplicativo do técnico), o `stop_on_first_tool` corta duas chamadas ao modelo e o custo cai junto. Quando a resposta precisa ser um texto explicativo para o técnico ler, o modo normal é necessário.

## 3. Histórico das invocações no formato TResponseInputItem

Toda chamada de ferramenta é registrada em uma lista Python de dicionários, a `historico_de_execucao`. A função `registrar` grava dois itens por invocação, no mesmo formato de um `TResponseInputItem`:

- `role`: `tool_call` para a entrada (o nome da ferramenta e o argumento usado) e `tool_output` para a saída (o que a ferramenta devolveu).
- `content`: o texto da entrada ou da saída.
- `timestamp`: a hora do registro, gerada com `datetime.now().isoformat()`.

A parte 3 do programa imprime a lista inteira, com o conteúdo cortado em 90 caracteres para caber na tela. Na execução do print foram 28 registros, ou seja, 14 invocações de ferramenta somando todas as partes.

É esse formato que a empresa pretende salvar entre execuções: como é uma lista de dicionários simples, ela pode ser gravada em JSON e recarregada depois, para o agente continuar de onde parou.

## 4. Evidências

Os quatro prints são da mesma execução, das 19:57 às 20:00, rolando o terminal.

- Print 1 – Execução do `gerar_historico.py`, com a seed 7, e o começo da parte 1 (situações 1a e 1b): `prints/Screenshot_20260919_200026.png`
- Print 2 – Situações 1c, 1d e 1e, com a contagem de ferramentas chamadas em cada uma: `prints/Screenshot_20260919_200038.png`
- Print 3 – Situação 1f (uma ferramenta só) e a parte 2a, com o tool_choice e as 3 chamadas ao modelo: `prints/Screenshot_20260919_200045.png`
- Print 4 – Parte 2b com stop_on_first_tool e 1 chamada, a comparação da parte 2c e a lista de histórico da parte 3, com os 28 registros: `prints/Screenshot_20260919_200055.png`
