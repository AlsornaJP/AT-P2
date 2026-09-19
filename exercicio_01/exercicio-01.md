# Exercício 1 – Ambiente e primeiro agente do projeto

## 1. Configuração do ambiente

O projeto foi criado com o `uv`, um gerenciador de projetos Python. O comando `uv init` criou a base do projeto (o arquivo `pyproject.toml`, que lista as dependências, e o `.python-version`, que fixa o Python 3.12). Em seguida, o comando `uv add openai-agents python-dotenv` instalou as bibliotecas e criou automaticamente o ambiente virtual isolado na pasta `.venv`. Dessa forma, as bibliotecas deste projeto não se misturam com as do sistema nem com as de outros projetos.

A chave de API fica fora do código-fonte, em um arquivo `.env` na raiz do projeto. O programa lê esse arquivo com a biblioteca `python-dotenv`. O `.env` está listado no `.gitignore` para não ser enviado a nenhum repositório. Para mostrar quais variáveis são necessárias sem expor a chave, existe o arquivo `.env.example`, que é só um modelo a ser copiado.

São usadas três variáveis: `GEMINI_API_KEY` (a chave do Google AI Studio), `GEMINI_BASE_URL` (o endereço do Gemini que aceita o mesmo formato da API da OpenAI) e `GEMINI_MODEL` (o modelo que o agente vai usar). Como os nomes não começam com `OPENAI_`, o código cria o cliente com `AsyncOpenAI` e passa a chave e o endereço de forma explícita.

Para executar: `uv run exercicio_01/agente_equipamentos.py`

## 2. Papel do Editor, do Agent Manager e do Playground no Antigravity

O Editor é onde eu escrevo e reviso o código no dia a dia. Ele é parecido com o VS Code e traz duas ajudas de IA: o Tab Completion, que sugere a continuação do código enquanto digito e é aceito com a tecla Tab, e o Command, que permite dar uma instrução em texto para criar ou alterar um trecho específico direto no arquivo. No meu fluxo, o Editor é usado para mudanças pequenas e para revisar tudo o que a IA produzir.

O Agent Manager é o painel onde eu delego tarefas maiores para agentes. Nele eu descrevo o que quero, o agente monta um plano, altera vários arquivos, executa comandos no terminal e mostra o que fez para eu aprovar ou pedir ajustes. Também é possível acompanhar mais de um agente trabalhando ao mesmo tempo. No meu fluxo, ele será usado para funcionalidades novas que envolvem vários arquivos, sempre com a minha revisão antes de aceitar o resultado.

O Playground é um espaço de testes separado do projeto. Nele posso conversar com o agente para tirar dúvidas, testar uma ideia ou experimentar um prompt sem mexer nos arquivos do projeto. No meu fluxo, ele serve para validar ideias rapidamente antes de levá-las para o código de verdade.

## 3. O primeiro agente

O código está em `exercicio_01/agente_equipamentos.py` e funciona assim:

- A função `perguntar_ao_agente` é assíncrona (declarada com `async def`). Ela cria um `Agent` com a instrução "Responda perguntas gerais sobre equipamentos industriais" e o executa com `Runner.run`. Como a chamada ao modelo demora, usamos `await` para esperar a resposta sem travar o programa.
- A função `main` também é assíncrona. Ela faz uma pergunta de exemplo, espera a resposta e imprime o resultado já formatado.
- O `asyncio.run(main())` no final é quem inicia a execução do código assíncrono.

Duas configurações foram feitas no início do arquivo para o código funcionar com qualquer provedor compatível com a OpenAI. A primeira é o uso de `OpenAIChatCompletionsModel`, que faz o agente usar o formato de API mais comum entre os provedores. A segunda, `set_tracing_disabled(True)`, desliga o envio de registros de execução para a plataforma da OpenAI, o que causaria erro quando a chave é de outro provedor.

### Função auxiliar de formatação

Parte do corpo da função `formatar_resposta` foi gerada no Editor do Antigravity com o Tab Completion. Escrevi a linha com o nome da função, os parâmetros e a primeira linha com `print`, que mostra a pergunta. Em seguida, o Editor sugeriu, em cinza, a linha que mostra a resposta. Aceitei a sugestão com a tecla Tab, revisei o código e rodei o programa. A função só imprime na tela e não devolve nenhum valor, por isso o retorno dela é `None`, e a `main` apenas chama a função, sem usar `print` em volta.

## 4. Tab Completion ou Agente da IDE?

**Ajuste pontual em uma linha já existente:** o ideal é o Tab Completion. A mudança é pequena e fica em um só lugar, e eu já sei exatamente o que quero. O Tab Completion sugere o código ali mesmo, na linha em que estou, usando o contexto do arquivo aberto, e eu aceito ou ignoro na hora. Chamar o Agente para isso seria mais lento, gastaria mais recursos e ainda exigiria revisar um plano e alterações para algo que resolvo em segundos.

**Planejamento de uma nova funcionalidade que mexe em vários arquivos:** o ideal é o Agente da IDE. O Tab Completion só enxerga o trecho onde estou digitando e não consegue planejar nem coordenar mudanças entre arquivos. O Agente consegue ler o projeto inteiro, montar um plano de implementação, alterar vários arquivos de forma coerente e rodar comandos para testar. Além disso, ele mostra o plano e as alterações antes de eu aceitar, o que me permite revisar cada decisão.

## 5. Evidências

- Print 1 – Sugestão do Tab Completion aparecendo em cinza na linha 21 da função `formatar_resposta`, antes de ser aceita: `prints/Screenshot_20260919_180319.png`
- Print 2 – Execução do agente no terminal, mostrando a pergunta e a resposta do Gemini: `prints/Screenshot_20260919_180436.png`
