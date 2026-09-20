# Guia dos 14 exercícios — o que foi decidido e por quê

Resumo de consulta rápida, para não precisar reler os 14 markdowns. Cada bloco tem o que o
exercício faz, as decisões que tomei e o ponto que eu preciso saber defender.

---

## Como os exercícios se encadeiam

**1 a 4** montam a base: ambiente, protocolo de conversa, primitivos do SDK e escolha de modelo.
**5 a 9** constroem o agente: ferramenta, controle de ferramenta, erro e saída estruturada, modelos
aninhados, memória de conversa. **10 e 11** acrescentam a recuperação semântica e avaliam a
estratégia de memória. **12 a 14** expõem tudo como serviço HTTP.

Quem lê o quê: 6 e 7 leem o manual do 5; 9 lê o manual do 8; 11 lê o manual longo do 10; 12 e 13
importam o agente do 11; 14 importa os modelos do 8 e o agente do 11.

---

## Ex. 1 — Ambiente e primeiro agente

Projeto com `uv`, chave no `.env` fora do código, primeiro agente assíncrono.

- **Cliente explícito, não por variável de ambiente.** Como as variáveis não começam com `OPENAI_`,
  o código cria o `AsyncOpenAI` passando chave e endereço na mão.
- **`OpenAIChatCompletionsModel` em vez do padrão**, para funcionar com qualquer provedor que fale
  o formato da OpenAI. Essa escolha vale para o projeto inteiro.
- **`set_tracing_disabled(True)`**, senão o SDK tenta mandar registros para a OpenAI com uma chave
  do Gemini e dá erro.
- **Defender:** uma linha da função de formatação veio do Tab Completion do Antigravity; está
  documentada no README com o modelo usado.

## Ex. 2 — Protocolo de Chat Completions

A API chamada direto, sem o SDK, para ver o que ele faz por baixo.

- **Troquei o Gemini pelo OpenRouter** porque o Gemini recusa `frequency_penalty` com
  `Unknown name`. O exercício pedia os quatro parâmetros.
- **Desliguei o raciocínio interno do modelo** (`reasoning: enabled false`), senão ele gastava todo
  o `max_tokens` pensando e a resposta vinha vazia.
- **Defender:** na comparação das sugestões, mudei `temperature`, `max_tokens` e
  `frequency_penalty` ao mesmo tempo, então o efeito do `frequency_penalty` **não está isolado**.
  É o ponto mais frágil deste exercício.

## Ex. 3 — Primitivos do SDK e regras de segurança

Agente de diagnóstico com system message em três partes e saída estruturada.

- **Regras de segurança com detalhes inventados** (cadeado laranja, 40 minutos, crachá verde). Se
  esses detalhes aparecem na resposta, provam que vieram da instrução e não do que o modelo sabia.
- **Cliente criado dentro da função**, não no topo do arquivo: misturar `run_sync` e `run` com um
  cliente único dá `is bound to a different event loop`.
- **Defender:** a lista dos "seis primitivos" foi escolha minha. A documentação não traz uma lista
  fechada de seis. Vale conferir com o material da aula.

## Ex. 4 — Seleção de modelo, streaming e métricas

Dois modelos na mesma triagem, provedor alternativo, contexto, streaming e dicionário de métricas.

- **Modelo barato para volume, caro para raciocínio.** Os dois acertaram a triagem; o caro levou
  50% mais tempo e cinco vezes mais tokens.
- **`include_usage=True`**, senão o total de tokens volta zero no streaming.
- **Filtrar os eventos de texto** no streaming, senão os argumentos da ferramenta aparecem no meio
  da resposta.
- **Defender:** o "modelo caro" acabou sendo o `gemini-3.6-flash`, porque o `gemini-3.1-pro` tem
  cota zero na chave. Os dois são gratuitos — medi tokens e tempo, não preço.

## Ex. 5 — Primeira ferramenta

Manual em JSON gerado localmente e a ferramenta que o consulta.

- **Seed fixa (42)** no gerador, para qualquer pessoa gerar o mesmo arquivo e poder conferir.
- **A docstring é o que o modelo lê** para decidir chamar a ferramenta — não o código.
- **Prova de que a resposta veio do arquivo:** a bomba BMB-210 tem "válvula termostática travada"
  como causa, que é típica de compressor. O sorteio criou uma combinação que o modelo não
  inventaria; ele repetiu o que estava no arquivo.

## Ex. 6 — Controle de seleção de ferramenta

Duas ferramentas parecidas, descrições vagas contra descrições claras, `tool_choice` e
`stop_on_first_tool`.

- **Dizer o que a ferramenta NÃO contém** foi o que mais ajudou o modelo a escolher.
- **`stop_on_first_tool` cortou de 3 chamadas ao modelo para 1**, quando só se quer o dado.
- **Defender:** a escolha varia entre execuções — a situação 1d deu 1 ferramenta num teste e 2 no
  print. Virou a conclusão do exercício: descrição boa aumenta a chance, só o `tool_choice`
  garante.

## Ex. 7 — Erro tratado e saída estruturada

Exceção na ferramenta, `failure_error_function`, Pydantic e sessão SQLite.

- **Descrições nos campos do Pydantic foram necessárias:** sem elas, o modelo preenchia `codigo`
  com o código do erro em vez do código do equipamento.
- **`tool_choice="none"` na segunda pergunta da sessão.** Motivo real: com saída estruturada mais
  ferramenta mais sessão, o agente entrava em laço e estourava `MaxTurnsExceeded`. Medido: laço em
  3 de 4 execuções sem a trava, 0 em 6 com ela.
- **Defender:** o laço é **aleatório**. Testei e descartei duas suspeitas (as assinaturas de
  raciocínio do Gemini e o tamanho da resposta da ferramenta). Detalhes em
  `investigacao-laco-exercicio-07.md`.

## Ex. 8 — Modelos aninhados e ferramenta assíncrona

`PecaRecomendada` dentro de `DiagnosticoEquipamento`, ferramenta `async` e as duas perguntas em
paralelo.

- **Lista aninhada em vez de campos separados:** campos separados obrigariam a chutar um número
  máximo de peças. Com a lista, a quantidade vira dado, não estrutura. **(Ponto exigido no vídeo.)**
- **`asyncio.to_thread` na leitura do arquivo**, senão `async def` seria enfeite: a leitura travaria
  o laço de eventos.
- **Lista vazia em vez de nulo** no caso de erro, para o painel não precisar de verificação.
- **Defender:** `prioridade` é texto livre, como o enunciado pede, então "urgentíssimo" passaria na
  validação. A garantia viria de um tipo restrito. É limitação consciente, está escrita.

## Ex. 9 — Histórico e sessão persistente

Lista de `TResponseInputItem` na mão contra `SQLiteSession` em disco.

- **O script detecta sozinho se é a 1ª ou a 2ª execução**, contando as mensagens gravadas. Assim o
  mesmo comando, digitado duas vezes, mostra os dois lados.
- **O `.db` fica fora do Git**, senão a primeira execução de quem baixasse já seria tratada como
  segunda.
- **A ideia central:** as duas partes fazem a mesma coisa, porque o modelo nunca lembra de nada
  sozinho. O que muda é quem carrega a conversa e onde ela mora.

## Ex. 10 — RAG sobre o manual longo

24 parágrafos, segmentação com sobreposição, embeddings e busca semântica.

- **Sobreposição de um parágrafo** entre trechos: a divisão é por tamanho, não por assunto, e sem a
  repetição uma informação na fronteira ficaria cortada. O parágrafo do torque caiu em dois trechos.
- **Um embedding para todos os trechos numa chamada só**, por causa do limite de requisições.
- **Similaridade de cosseno escrita à mão**, sem biblioteca, e sem banco de vetores: com 14 trechos,
  comparar um a um mostra melhor o que acontece.
- **Defender:** a busca roda duas vezes, uma sem o agente. É para separar o que os embeddings fazem
  do que o modelo faz — o agente reescreve a pergunta antes de buscar, o que é técnica normal de
  RAG. Sem a busca isolada, eu daria aos embeddings um crédito que era do modelo.

## Ex. 11 — Memória e RAG juntos, com avaliação medida

Um agente com sessão e busca, e os mesmos cenários rodados com metade da memória desligada.

- **Medir em vez de argumentar:** nove configurações, e uma coluna que registra **se o manual foi
  consultado** — resposta certa sem consulta veio da cabeça do modelo, não do manual.
- **O achado principal, determinístico:** com as palavras do técnico o trecho certo fica em 1º
  lugar (0,5869); com a pergunta reescrita pelo agente, que puxa "cabeçote" da conversa, cai para 4º
  (0,7117) e sai da janela. **A memória contaminou a busca.** E a busca pior tem nota maior —
  similaridade mede parecença com a pergunta, não acerto da resposta. **(Ponto exigido no vídeo.)**
- **Combinar não é somar:** com as duas ferramentas, o agente errou porque **decidiu não buscar**.
- **Defender, e é o ponto mais delicado do trabalho:** a conclusão do Cenário A **não se sustenta
  pelo placar** — só RAG e o agente completo empataram em 3/3. Ela vem da leitura das respostas:
  sem memória, o agente respondeu em condicional e devolveu a pergunta ao técnico. O placar não
  distingue uma resposta de uma esquiva.
- **Defender também:** o Cenário C foi desenhado esperando exigir as duas memórias e a medição
  mostrou que não exige, porque o manual diz "após qualquer aperto". Está relatado como erro de
  desenho.

## Ex. 12 — O agente exposto em FastAPI

POST que aceita e responde na hora, GET de teste, `BackgroundTasks`.

- **O agente é importado do Ex. 11, não copiado** — seriam 150 linhas que envelheceriam. A partir
  daqui o projeto não pode ser separado por pasta.
- **O índice do manual é montado no arranque**, não a cada pergunta.
- **202 em vez de 200:** 200 é "aqui está a resposta", 202 é "recebi e vou processar".
- **A prova de que não bloqueia:** o chamado que chegou **depois terminou antes** (7,9s contra
  19,6s). Num serviço que bloqueasse, o segundo nem teria começado.
- **Detalhe que quase estragou a evidência:** sem `flush`, as linhas do log saem fora de ordem e a
  ordem é justamente a prova.

## Ex. 13 — Submissão e consulta por task_id

`POST /agent/run` e `GET /agent/status/{task_id}` com `pending`, `done` e `error`.

- **A entrada nasce no POST, antes de a resposta sair.** Se nascesse na tarefa de fundo, haveria um
  instante em que o cliente teria o `task_id` e a consulta não o encontraria.
- **Tudo em `try/except`:** a tarefa roda depois da resposta HTTP, então não há ninguém para receber
  a exceção — ela sumiria em silêncio e a tarefa ficaria `pending` para sempre.
- **O estado `error` é demonstrado com falha real**, apontando a tarefa para um modelo inexistente;
  o 404 do provedor é autêntico.
- **Defender:** o `task_id` inexistente continua dando **500 de propósito**, porque é o tema do
  Ex. 14. Está escrito no texto que é deliberado.

## Ex. 14 — O serviço REST completo

Os três endpoints, o agente integrador com as duas fontes, e o tratamento do `task_id` inexistente.

- **O agente tem as duas ferramentas**, porque o contexto do enunciado fala no resultado do agente
  integrador. As peças só existem no manual do Ex. 8; a busca semântica enriquece os campos de
  texto. Não dá para acrescentar campos ao modelo, que tem de ser o do Ex. 8.
- **404 com explicação, em vez de 500.** Três argumentos: o 500 **mente sobre quem errou** (diz que
  o servidor falhou quando o endereço é que estava errado), **não diz nada** (três palavras iguais
  para qualquer falha) e **vaza informação** (o rastro expõe caminhos e variáveis). Recusei também o
  200 com estado `unknown`, porque "não existe" não é um estado da tarefa. **(Ponto exigido no
  vídeo.)**
- **A mensagem admite as duas causas** — nunca existiu, ou se perdeu num reinício — porque o serviço
  realmente não distingue as duas.
- **409 quando se pede o resultado cedo demais**, que não é erro de ninguém.
- **Defender:** a execução do print levou 102 s porque o agente voltou duas vezes ao manual longo;
  noutra execução levou 4,7 s com uma busca só. Mesma pergunta, mesmo código.

---

## Três lições que se repetem no trabalho inteiro

**Instrução influencia, parâmetro garante.** Aparece no 6 (descrição contra `tool_choice`), no 7 (o
pedido em texto não segurou o laço, o `tool_choice="none"` segurou) e no 11 (a instrução reforçada
aumentou a chance de buscar, a janela maior resolveu).

**O mesmo código não dá o mesmo resultado.** Aparece no 6, no 7, no 11 e no 14. Por isso quase todo
número deste trabalho foi medido mais de uma vez, e por isso o diagnóstico determinístico do 11 é o
que sustenta a avaliação.

**Medir muda a conclusão.** O 11 derrubou duas hipóteses minhas e o desenho de um cenário; o 10
mostrou que eu estava dando à busca um crédito do modelo; o 14 revelou que o agente costura quatro
trechos de duas fontes. Em todos, o que eu ia escrever de cabeça estava errado.

---

## Os três pontos exigidos no vídeo

| Tema | Onde está | A frase |
|---|---|---|
| Estrutura aninhada | Ex. 8, seção 4 | Campos separados obrigam a chutar um máximo; a lista faz a quantidade virar dado |
| Memória e RAG | Ex. 11, seção 5 | A memória contaminou a busca: o trecho certo caiu de 1º para 4º |
| `task_id` inexistente | Ex. 14, seção 5 | O 500 mente sobre quem errou; o 404 diz a verdade e orienta |
