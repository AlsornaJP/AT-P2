# Exercício 11 – Agente integrador com memória e avaliação de estratégia

O código está em `exercicio_11/agente_integrador.py`. Para executar: `uv run exercicio_11/agente_integrador.py`

O programa demora cerca de dez minutos, porque roda os mesmos cenários em várias configurações, com pausas para respeitar o limite de chamadas por minuto da conta gratuita.

## 1. O agente integrador

É um agente só, o "Assistente de Campo", que junta as duas formas de memória construídas antes:

- **Memória de conversa**, com a `SQLiteSession` do Exercício 9, que guarda perguntas e respostas e reenvia tudo na pergunta seguinte.
- **Recuperação semântica**, com o pipeline de RAG do Exercício 10: o manual longo é segmentado em 14 trechos, cada trecho vira um vetor, e a ferramenta `buscar_no_manual` devolve os mais parecidos com a pergunta.

O agente vem configurado com o que os testes mostraram ser melhor: a instrução que manda consultar o manual sempre que a pergunta envolver procedimento, valor ou passo de manutenção, e uma janela de 5 trechos por busca. As configurações mais fracas existem no arquivo apenas para servir de comparação no experimento, e as seções seguintes explicam por que elas ficaram para trás.

## 2. Como eu medi

Rodar o agente completo e ver que ele funciona não responde ao que o enunciado pergunta. Para saber qual estratégia é necessária, é preciso **desligar cada metade e ver o que quebra**. Então cada cenário roda em até três configurações: só com RAG, só com memória, e com as duas.

Cada pergunta tem um dado esperado, e o programa confere se ele aparece na resposta. Mais importante que isso, o programa registra **se o agente consultou o manual**. Uma resposta certa sem consulta não veio do manual: veio do conhecimento geral do modelo, e num manual de fábrica isso não vale, porque o modelo não conhece este equipamento fictício.

A checagem é simples, por palavra, e erra em alguns casos. Errou de verdade nos resultados, e isso está na seção 7.

## 3. Cenário A – três perguntas seguidas sobre o mesmo chamado

Um técnico abre um chamado sobre o alarme E-102 e faz três perguntas encadeadas. A primeira precisa do manual; as duas seguintes dependem do que já foi dito.

**Só com RAG, sem memória: 2 de 3.** A segunda pergunta, "e o que acontece com o óleo se eu continuar operando assim?", quebrou de um jeito revelador: sem a conversa, o agente não sabia a que "assim" se referia, então buscou por "consequências de operar o compressor com óleo inadequado", trouxe os trechos errados e respondeu que não encontrou. A busca funcionou bem; faltou saber **o que** buscar.

**Só com memória, sem RAG: 1 de 3.** A primeira pergunta já saiu errada, e com confiança: o agente afirmou que o E-102 indica "falha na pressão do óleo". O manual diz válvula termostática travada. Ele inventou um significado plausível para um código de alarme de um equipamento fictício. A segunda pergunta errou na sequência da primeira.

**Com as duas, que é o agente do exercício: 3 de 3.** A primeira foi respondida com consulta ao manual; a segunda e a terceira, **sem nenhuma consulta**, saíram inteiras da conversa guardada.

**Este é o cenário que prova a necessidade da combinação.** Nenhuma das metades sozinha atravessa a conversa inteira: sem RAG, a primeira pergunta é inventada e contamina o resto; sem memória, as perguntas seguintes ficam sem assunto. E repare que não é um caso exótico — é o formato normal de um chamado, em que a dúvida inicial precisa do manual e o desdobramento precisa do que já foi dito.

## 4. Cenário B – uma consulta pontual, sem conversa anterior

Outro técnico, sem histórico nenhum, pergunta: "posso lavar o radiador com água na parada programada?".

**Só com memória, sem RAG: 0 de 1.** O agente respondeu: *"Sim, você pode lavar o radiador com água. Utilize um jato de baixa pressão para evitar danos às aletas."* O manual diz o contrário: só ar comprimido seco, porque água danifica as aletas.

É o pior tipo de falha. Ele não disse que não sabia, como a instrução mandava. Respondeu com segurança uma informação plausível, tirada do conhecimento geral sobre radiadores, e essa resposta estragaria o equipamento.

**Com o agente do exercício: 1 de 1.** Consultou o manual e respondeu que não se usa água, só ar comprimido seco, no sentido contrário ao fluxo.

**Conclusão do cenário B:** aqui o RAG sozinho basta. Não existe conversa para a memória guardar, e a pergunta chega completa. A memória não ajuda nem atrapalha.

## 5. Cenário C – o cenário que eu desenhei errado, e o que ele ensinou

Eu montei este cenário esperando que ele fosse **o** caso em que a combinação é obrigatória. O técnico pergunta o torque dos parafusos do cabeçote e depois, curto, "e depois de apertar, o que eu faço?". A ideia era que a segunda pergunta precisasse da conversa para saber de quais parafusos se trata, e do manual para achar o procedimento seguinte.

**A medição mostrou que eu estava errado.** Com só RAG, sem memória nenhuma, o agente acertou as duas perguntas. O motivo está no próprio manual: o parágrafo diz "após **qualquer** aperto, o equipamento roda trinta minutos em vazio". Como o procedimento vale para qualquer parafuso, saber quais eram não faz diferença. A pergunta parecia depender do contexto, mas a resposta não dependia.

Prefiro registrar isso a esconder, porque é o tipo de erro de desenho experimental que só aparece quando se mede. E o cenário acabou revelando duas outras coisas mais interessantes.

### A combinação ingênua falha

Com memória e busca ligadas, mas com a instrução original e a janela de 3 trechos, o agente errou a segunda pergunta: **decidiu não buscar**. Achou que já sabia pela conversa e respondeu que "o manual não especifica um procedimento de verificação imediata após o aperto". Ter as duas ferramentas não garante que as duas sejam usadas.

### A memória pode estragar a busca

Antes de culpar a busca, o programa mede se ela acharia o trecho certo. O resultado é determinístico, sempre o mesmo, e é a parte mais reveladora do exercício:

- Com **as palavras do próprio técnico**, "E depois de apertar, o que eu faço?", o trecho que responde fica em **1º lugar**, com similaridade 0,5869.
- Com **a pergunta reescrita pelo agente**, "procedimento após aperto dos parafusos do cabeçote do compressor CMP-100", o mesmo trecho cai para **4º**, com 0,7117.

O agente, ao reescrever a pergunta, puxou "cabeçote" e "CMP-100" da conversa anterior. Isso ancorou a busca no assunto velho, e os trechos sobre o torque afundaram o trecho sobre o que fazer depois. **A memória de conversa contaminou a recuperação semântica.** A mesma reescrita que ajudou no Exercício 10, traduzindo a fala do técnico para o vocabulário do manual, atrapalhou aqui.

Repare num detalhe contraintuitivo: a busca ruim tem notas **mais altas** (0,74 contra 0,58) e ainda assim traz os trechos errados. Similaridade alta não significa resposta certa; significa parecença com o que foi perguntado. Se a pergunta aponta para o lado errado, a busca acerta com precisão o alvo errado.

Foi por causa dessa medição que o agente do exercício usa janela de 5 e não de 3: com 5, o trecho que estava em 4º lugar entra. E é por isso que a janela é uma correção melhor que a instrução — ela não depende de como o modelo formulou a pergunta naquela execução.

## 6. A avaliação de estratégia, que é o que o enunciado pede

Com base no que foi medido:

**Só o histórico de conversa nunca foi suficiente**, em nenhum dos três cenários. Onde ele rodou sozinho, o agente inventou: um significado falso para o alarme E-102, uma autorização falsa para lavar o radiador com água, um "teste de estanqueidade" que não existe. O motivo é simples: o manual é de um equipamento fictício, e nada do que está nele pode ser deduzido do conhecimento geral do modelo. A memória de conversa só sabe o que já foi dito na conversa; se a informação nunca entrou, ela não aparece.

**Só o RAG basta quando a pergunta é autossuficiente.** É o Cenário B: o técnico diz o equipamento, a situação e o que quer saber, sem depender de nada anterior. Também foi suficiente no Cenário C, por acidente do manual, como expliquei na seção 5.

**A combinação é necessária quando a conversa avança.** É o Cenário A, e a prova é direta: só RAG dá 2 de 3, só memória dá 1 de 3, as duas juntas dão 3 de 3. A primeira pergunta de um chamado quase sempre precisa do manual; da segunda em diante, o técnico para de repetir o contexto e passa a depender do histórico. As duas coisas acontecem na mesma conversa.

**Recomendação para produção: a combinação**, com três ressalvas que só apareceram porque medi.

A primeira é que combinar não é somar. No Cenário C, o agente com as duas ferramentas errou porque decidiu não usar uma delas. É preciso instruir explicitamente quando buscar, e mesmo assim a instrução não garante — em execuções diferentes ele decidiu diferente.

A segunda é que a memória pode piorar a busca, pela ancoragem no assunto anterior. Uma janela de recuperação maior reduz o problema. Buscar também com as palavras originais do técnico, além da versão reescrita, é o caminho que eu investigaria em seguida.

A terceira é que o custo não é igual. As respostas vindas da memória não gastam busca nenhuma: no Cenário A completo, duas das três perguntas foram respondidas sem consultar o manual. Numa operação com muitos técnicos, isso é a diferença entre uma consulta por pergunta e uma consulta por chamado.

## 7. O que aprendi sobre a própria medição

Três vezes a checagem automática deu acerto para respostas que não eram boas, e vale registrar, porque é a parte do trabalho que mais me surpreendeu.

No Cenário A sem memória, a terceira pergunta foi marcada como acerto porque a resposta continha "E-102" — só que continha por estar **listando todos os códigos** do manual e devolvendo a pergunta: "qual deles você está observando no painel?".

No Cenário A sem RAG, a mesma terceira pergunta também passou, por um motivo ainda mais bobo: o código E-102 tinha sido dito **pelo próprio técnico** na primeira pergunta, então estava no histórico de qualquer jeito. A pergunta não discrimina nada nessa configuração.

E numa execução anterior, no Cenário B, a resposta errada "sim, pode lavar com água, evitando danificar as aletas" passou porque eu tinha posto "aletas" entre as palavras esperadas. Corrigi para exigir "ar comprimido", que é o que a resposta certa necessariamente diz, e a falha apareceu.

A lição vale além do exercício: uma checagem por palavra mede se o texto contém algo, não se a resposta está certa. Por isso o programa mostra a resposta inteira e a coluna de consulta ao manual, para dar de conferir à mão o que a contagem automática diz. Nas conclusões da seção 6, eu usei a leitura das respostas, e não só o placar.

## 8. Uma observação sobre repetir o experimento

O placar não sai idêntico em toda execução. A linha da combinação ingênua, por exemplo, já passou e já falhou, porque a pergunta que o agente monta muda de uma vez para outra. As conclusões qualitativas se repetiram em todas as execuções que fiz, e o diagnóstico da seção 5 é determinístico — mesma pergunta, mesmos vetores, mesmo resultado. É nele que a avaliação se apoia.

## 9. Evidências

*(inserir os prints depois de tirá-los)*

- Print – Cenário A, nas três configurações: `prints/...`
  - Sem RAG, o agente inventando que o E-102 é "falha na pressão do óleo".
  - Sem memória, a segunda pergunta buscando o assunto errado e a terceira sendo devolvida como pergunta.
  - O agente do exercício acertando as três, com a segunda e a terceira **sem consultar o manual**.
- Print – Cenário B e o diagnóstico: `prints/...`
  - Sem RAG, a resposta de que pode lavar o radiador com água.
  - O agente do exercício respondendo que só ar comprimido seco.
  - A comparação das duas formas de perguntar: o trecho certo em 1º lugar com as palavras do técnico e em 4º com a pergunta reescrita pelo agente.
- Print – Cenário C e o placar final: `prints/...`
  - A combinação ingênua errando a segunda pergunta sem sequer buscar.
  - O agente do exercício acertando as duas.
  - A tabela final, com os acertos e a coluna que mostra em quais perguntas o manual foi consultado.
