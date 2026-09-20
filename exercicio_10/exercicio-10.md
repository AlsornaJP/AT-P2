# Exercício 10 – Pipeline de RAG sobre os manuais técnicos

O código está em `exercicio_10/rag_manual.py`. Para executar: `uv run exercicio_10/rag_manual.py`

O manual longo é gerado por `gerar_manual_longo.py`, que escreve o `manual_longo.txt`. O texto é fixo, escrito à mão no próprio arquivo, e não sorteado: assim o exercício dá o mesmo resultado toda vez.

RAG quer dizer recuperar antes de responder. Em vez de mandar o manual inteiro para o modelo, o programa procura os pedaços que interessam e manda só eles. É o que permite trabalhar com manuais que não caberiam numa chamada só.

## 1. O manual longo e o dado escondido

São 24 parágrafos, cerca de 4.500 caracteres, divididos em seis assuntos: instalação, lubrificação, sistema elétrico, procedimentos de aperto, alarmes e parada programada.

No parágrafo 14, que fica no meio do documento, está o dado que o exercício vai procurar: o torque de aperto dos parafusos do cabeçote, que é de quarenta e cinco newton-metro. Esse valor não aparece em nenhum outro lugar do manual.

Plantei também um distrator no parágrafo 15, logo em seguida: outro valor de torque, oitenta newton-metro, mas para os parafusos da base, que são outros parafusos. Serve para conferir se o agente pega o número certo, e não simplesmente o primeiro número de torque que encontrar.

## 2. A segmentação em trechos

O programa lê os parágrafos e vai juntando um ao outro até o trecho chegar perto de 600 caracteres. Quando passaria do limite, fecha o trecho e começa outro.

A parte que vale explicar é a **sobreposição**: cada trecho novo começa repetindo o último parágrafo do trecho anterior. Isso existe porque a divisão é cega, feita por tamanho, e não por assunto. Sem a repetição, uma informação que caísse bem na fronteira entre dois trechos ficaria cortada ao meio, e nenhum dos dois pedaços responderia direito.

Deu para ver o efeito na prática. Os 24 parágrafos viraram 14 trechos, e o parágrafo 14, o do torque, acabou aparecendo em dois deles: no trecho 8 (parágrafos 13 e 14) e no trecho 9 (parágrafos 14 e 15). Duas chances de ser encontrado, em vez de uma.

O custo dessa escolha é repetição: o mesmo texto ocupa espaço duas vezes e é transformado em vetor duas vezes. Num manual de verdade, com milhares de parágrafos, isso pesaria, e valeria ajustar o tamanho da sobreposição.

O programa imprime a tabela dos 14 trechos com o tamanho de cada um e de quais parágrafos ele veio.

## 3. Os trechos viram vetores

Cada trecho é transformado num vetor de números pelo modelo `gemini-embedding-001`. Um vetor desses é uma forma de representar o sentido do texto: textos que falam da mesma coisa viram vetores que apontam para direções parecidas, mesmo que usem palavras diferentes.

Pedi vetores de 768 dimensões, em vez das 3.072 que o modelo entrega por padrão. Menos dimensões ocupam menos memória e a comparação fica mais rápida; para 14 trechos a diferença é irrelevante, mas é o tipo de ajuste que importa quando a base cresce.

Os 14 trechos são enviados **numa única chamada**, todos juntos. Isso é importante por causa do limite de chamadas por minuto da conta gratuita: uma chamada por trecho gastaria 14 chamadas e esbarraria na cota.

## 4. A busca semântica, testada sozinha

Aqui está o centro do exercício, e ele é feito em duas etapas de propósito.

A pergunta do técnico é: "Com que força eu devo apertar os parafusos da tampa superior do compressor?". Ela foi escrita para **não** usar as palavras do manual. O manual diz "torque de aperto dos parafusos do cabeçote"; o técnico disse "força" e "tampa superior". Um técnico real fala assim.

**Primeiro, a maneira simples.** O programa faz uma busca por palavra-chave, contando quantas palavras da pergunta aparecem em cada trecho. O resultado: o melhor trecho é o número 1, com **uma** palavra em comum, "compressor" — que é justamente a palavra menos útil, porque o manual inteiro é sobre o compressor. O trecho que tem a resposta **não entra nem nos três primeiros**. A busca por palavra-chave falha porque "força" e "tampa" não estão escritas em lugar nenhum do manual.

**Depois, a busca semântica.** A mesma pergunta, com as mesmas palavras, é transformada em vetor e comparada com os 14 trechos por similaridade de cosseno. O resultado: o trecho 9, que contém o parágrafo 14, fica em primeiro lugar com 0,7575, e o trecho 8, que também contém o parágrafo 14, fica em segundo com 0,7036. Os dois pedaços que guardam a resposta ocuparam as duas primeiras posições.

Essa etapa roda **sem o agente**, direto do programa para a busca. Isso não é um detalhe: é o que torna o teste válido, e explico o motivo na seção 6.

A similaridade de cosseno está escrita à mão, em Python puro, sem biblioteca nenhuma. São três linhas: o produto dos vetores dividido pelo tamanho de cada um. O resultado vai de -1 a 1, e quanto mais perto de 1, mais parecido é o sentido dos dois textos.

## 5. O agente respondendo

Só então entra o agente do SDK, com uma ferramenta chamada `buscar_no_manual`, que faz exatamente a busca da seção anterior e devolve os três trechos mais parecidos. A instrução manda responder apenas com o que estiver nesses trechos e citar o número do trecho usado.

O agente respondeu: quarenta e cinco newton-metro, em duas etapas, com sequência cruzada do centro para as bordas, citando o trecho 9.

Duas coisas valem ser notadas nessa resposta. A primeira é que o número está certo, apesar do distrator: o trecho 9 contém **os dois** valores de torque, o de 45 do cabeçote e o de 80 da base, e o agente escolheu o certo, porque a pergunta era sobre os parafusos de cima. A segunda é que ele citou a fonte, o que num painel de despacho real permitiria ao técnico conferir no manual.

## 6. Uma ressalva honesta sobre o teste

Quando montei o exercício, a primeira versão fazia a pergunta direto ao agente e olhava o resultado. Deu certo, mas o teste estava furado, e prefiro registrar isso a esconder.

O que aconteceu foi que **o agente reescreveu a pergunta antes de buscar**. Eu perguntei com "força", e a ferramenta recebeu uma pergunta já contendo a palavra "torque". Ou seja: quem traduziu o jeito de falar do técnico para o jeito de escrever do manual foi o modelo, antes da busca. Se eu tivesse parado ali, estaria dando à busca semântica um crédito que era do modelo.

Por isso o programa faz a busca isolada da seção 4, com as palavras literais do técnico, sem o modelo no meio. É essa etapa que prova que os embeddings entendem o sentido, e não o agente.

Vale notar que, no funcionamento normal, essa reescrita é boa: duas etapas de ajuda em vez de uma. Só não serve como prova de que a busca funciona. Nos prints dá para comparar as duas: a busca isolada recebeu a pergunta exatamente como o técnico escreveu, e a busca feita pelo agente recebeu uma versão reescrita por ele.

## 7. O que ficou de fora, de propósito

**Não guardo os vetores em arquivo** entre uma execução e outra. Recalcular custa uma chamada e cerca de dois segundos, e um arquivo de cache esconderia justamente a etapa que o exercício quer mostrar. Num sistema de verdade isso seria feito uma vez e guardado.

**Não uso banco de vetores.** Com 14 trechos, comparar um a um é instantâneo. Um banco de vetores serve para quando são milhões de trechos e comparar todos fica caro; o que ele faz por dentro é uma versão esperta dessa mesma comparação. Fazer na mão aqui mostra melhor o que está acontecendo.

## 8. Evidências

*(inserir o print depois de tirá-lo)*

- Print – a execução completa: `prints/...`
  - **Parte 1:** a tabela dos 14 trechos, com tamanho e parágrafos de origem, e a confirmação de que o torque do cabeçote caiu nos trechos 8 e 9, por causa da sobreposição.
  - **Parte 2:** os 14 vetores de 768 dimensões gerados numa chamada só.
  - **Parte 3:** a busca por palavra-chave achando só a palavra "compressor" e não trazendo o trecho certo, contra a busca semântica pondo os trechos 9 e 8 em primeiro e segundo lugar.
  - **Parte 4:** o agente citando o trecho 9 e respondendo quarenta e cinco newton-metro, sem cair no distrator dos oitenta.
