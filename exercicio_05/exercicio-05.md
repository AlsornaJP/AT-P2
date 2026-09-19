# Exercício 5 – Primeira ferramenta: consulta ao manual do equipamento

São dois programas nesta pasta:

- `exercicio_05/gerar_manual.py`: cria o arquivo de dados. Para executar: `uv run exercicio_05/gerar_manual.py`
- `exercicio_05/agente_manual.py`: o agente com a ferramenta. Para executar: `uv run exercicio_05/agente_manual.py`

## 1. O arquivo de dados com seed fixa

O programa `gerar_manual.py` cria o arquivo `manuais.json` com cinco equipamentos fictícios da Metalúrgica Andrade: um compressor, um torno CNC, uma esteira, um forno e uma bomba.

Cada equipamento tem três campos: `codigo` (por exemplo, `TRN-300`), `nome` e `erros_conhecidos`. Cada erro conhecido tem o `codigo_erro`, a `causa_provavel` e a `acao_recomendada`. Os códigos de erro seguem a posição do equipamento na lista: o primeiro equipamento tem E-101, E-102 e E-103, o segundo tem E-201, E-202 e E-203, e assim por diante. Assim nenhum código se repete entre equipamentos.

A causa e a ação de cada erro são sorteadas de duas listas prontas, com `random.choice`. Antes do sorteio, o programa chama `random.seed(42)`. A seed é o ponto de partida do sorteio: com o mesmo número, os sorteios saem sempre na mesma ordem. Por isso qualquer pessoa que rodar o programa vai gerar exatamente o mesmo arquivo, e o resultado do exercício pode ser conferido.

## 2. A ferramenta

A função `consultar_manual_equipamento` está no arquivo `agente_manual.py`, logo acima do agente, e tem três coisas que o SDK usa:

- **O decorador `@function_tool`:** é ele que transforma a função comum em uma ferramenta que o modelo pode pedir para executar.
- **As type annotations:** a função recebe `codigo_equipamento: str` e devolve `str`. O SDK usa esses tipos para montar a descrição que vai junto com o pedido ao modelo, e assim o modelo sabe que precisa mandar um texto.
- **A docstring:** explica o que a ferramenta faz, o que é o parâmetro (com um exemplo de código) e o que ela devolve. Essa descrição é o que o modelo lê para decidir quando chamar a ferramenta. Sem ela, o modelo teria que adivinhar.

Por dentro, a função lê o `manuais.json`, procura o equipamento pelo código, sem diferenciar maiúsculas de minúsculas, e devolve os dados em JSON. Se o código não existir, ela devolve um aviso com a lista de códigos disponíveis, em vez de quebrar o programa.

A função também imprime uma linha na tela toda vez que é chamada. Isso não é necessário para funcionar, é só para provar, na hora da execução, que o agente realmente usou a ferramenta.

Nas instruções do agente está escrito que ele deve consultar o manual antes de sugerir qualquer ação e responder usando apenas o que estiver lá.

## 3. Confirmação de que a resposta vem do arquivo

O programa faz duas perguntas ao agente. A saída mostra, nas duas, a linha `[tool consultar_manual_equipamento] procurando o código ...`, ou seja, a ferramenta foi chamada de verdade.

**Pergunta 1:** "O torno CNC de código TRN-300 parou e mostrou o erro E-202 no painel. O que houve e o que eu faço?"

O agente respondeu: causa provável "excesso de carga na partida" e ação recomendada "aguardar o resfriamento e conferir o aperto das conexões".

**Pergunta 2:** "A bomba BMB-210 está com o erro E-503. O que o manual diz?"

O agente respondeu: causa provável "válvula termostática travada" e ação recomendada "substituir o componente e registrar a troca no histórico".

As duas respostas são exatamente o que está no `manuais.json`, palavra por palavra. E isso não poderia vir do conhecimento geral do modelo por dois motivos: os equipamentos são inventados, e as combinações de causa e ação foram sorteadas. Uma prova disso é a resposta da bomba: "válvula termostática travada" é uma causa típica de compressor, não de bomba centrífuga. O modelo repetiu o que o arquivo diz, em vez de responder pelo que ele acha que faz sentido.

## 4. Evidências

- Print 1 – As duas execuções na mesma tela: `prints/Screenshot_20260919_193328.png`
  - Em cima, o `gerar_manual.py`, mostrando a seed 42, os cinco equipamentos e os códigos de erro criados.
  - Embaixo, o `agente_manual.py`, com a linha da ferramenta sendo chamada em cada pergunta e as duas respostas.

Para conferir que a resposta veio do arquivo, basta abrir o `manuais.json` e comparar o erro E-202 do TRN-300 e o E-503 do BMB-210 com o que o agente respondeu no print.
