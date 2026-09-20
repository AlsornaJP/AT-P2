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

Essa etapa roda **sem o agente**, direto do programa para a busca. O motivo é separar o que cada parte do sistema faz, e está explicado na seção 6.

A similaridade de cosseno está escrita à mão, em Python puro, sem biblioteca nenhuma. São três linhas: o produto dos vetores dividido pelo tamanho de cada um. O resultado vai de -1 a 1, e quanto mais perto de 1, mais parecido é o sentido dos dois textos.

## 5. O agente respondendo

Só então entra o agente do SDK, com uma ferramenta chamada `buscar_no_manual`, que faz exatamente a busca da seção anterior e devolve os três trechos mais parecidos. A instrução manda responder apenas com o que estiver nesses trechos, citar o número do trecho usado e avisar quando a informação não estiver lá.

O agente recuperou o trecho 9 em primeiro lugar e respondeu com o valor certo: quarenta e cinco newton-metro, aplicados em duas etapas, com sequência cruzada do centro para as bordas, citando o trecho 9.

O jeito como ele respondeu merece atenção, porque não foi o esperado e ficou melhor do que o esperado. Em vez de afirmar que "tampa superior" é o cabeçote, ele **avisou que o manual não usa o termo "tampa superior"**, deu o torque dos parafusos do cabeçote que encontrou no trecho 9, e terminou dizendo que, se a tampa for outra peça, a informação não está no manual.

Isso é a instrução funcionando. Eu mandei responder apenas com o que estiver nos trechos e avisar quando não encontrar, e ele levou a sério: não inventou a equivalência entre o vocabulário do técnico e o do manual, só apontou a correspondência provável e deixou a conferência para a pessoa. Num manual de manutenção, em que apertar o parafuso errado com o torque errado estraga equipamento, essa cautela é o comportamento desejado.

Vale notar também que o agente não caiu no distrator. O trecho 9 contém **os dois** valores de torque, os 45 do cabeçote e os 80 da base, e ele trouxe só o que correspondia aos parafusos de cima.

## 6. O agente reescreve a pergunta, e isso é normal

Uma coisa que aparece nos prints e merece explicação: a pergunta que chega à ferramenta não é exatamente a que o técnico fez.

Eu pergunto "com que força eu devo apertar os parafusos da tampa superior do compressor?", e a ferramenta recebe algo como "força de aperto parafusos tampa superior compressor CMP-100". Numa das execuções o agente chegou a trocar "força" por "torque" por conta própria, antes de buscar.

Isso não é defeito, é o agente fazendo o trabalho dele. Traduzir a fala de quem pergunta para o vocabulário de quem escreveu o documento é uma técnica conhecida em RAG, e melhora a busca: o modelo tira as palavras que não ajudam, acrescenta o código do equipamento e aproxima a pergunta da linguagem do manual. O que o exercício exige é que o trecho certo seja recuperado e usado na resposta, e é o que acontece.

O motivo de eu rodar a busca isolada na seção 4 é outro: **separar a contribuição de cada parte.** Com o agente no meio, dois mecanismos ajudam ao mesmo tempo, e fica impossível saber se a busca sozinha daria conta. Rodando a pergunta literal do técnico direto na busca, sem o modelo, dá para afirmar com segurança que os embeddings já encontram o trecho certo por conta própria, e que a reescrita do agente é um ganho em cima disso, e não uma muleta.

Nos prints dá para comparar as duas buscas lado a lado: a da seção 4 recebeu a pergunta exatamente como o técnico escreveu, e a do agente recebeu a versão reescrita por ele. As duas colocam o trecho 9 em primeiro lugar.

## 7. O que ficou de fora, de propósito

**Não guardo os vetores em arquivo** entre uma execução e outra. Recalcular custa uma chamada e cerca de dois segundos, e um arquivo de cache esconderia justamente a etapa que o exercício quer mostrar. Num sistema de verdade isso seria feito uma vez e guardado.

**Não uso banco de vetores.** Com 14 trechos, comparar um a um é instantâneo. Um banco de vetores serve para quando são milhões de trechos e comparar todos fica caro; o que ele faz por dentro é uma versão esperta dessa mesma comparação. Fazer na mão aqui mostra melhor o que está acontecendo.

## 8. Evidências

Os dois prints são da mesma execução, que não cabia em uma tela só.

- Print 1 – `prints/Screenshot_20260920_103814.png`: as Partes 1, 2 e 3.
  - A tabela dos 14 trechos, com tamanho e parágrafos de origem, e a confirmação de que o torque do cabeçote caiu nos trechos 8 e 9, por causa da sobreposição.
  - Os 14 vetores de 768 dimensões gerados numa chamada só.
  - A busca por palavra-chave achando só a palavra "compressor", com a resposta explícita `o trecho com o torque do cabeçote entrou nos 3 primeiros? NÃO`.
  - A busca semântica logo abaixo, com os trechos 9 e 8 em primeiro e segundo lugar, com notas de 0,7575 e 0,7036.
- Print 2 – `prints/Screenshot_20260920_103819.png`: a rolagem da mesma execução até a Parte 4.
  - A pergunta que o agente enviou à ferramenta, já reescrita por ele: `força aperto parafusos tampa superior compressor CMP-100`.
  - O ranking da busca feita pelo agente, também com o trecho 9 em primeiro lugar.
  - A resposta final, com os 45 N·m, a citação do trecho 9 e a ressalva sobre o termo "tampa superior" não existir no manual.
