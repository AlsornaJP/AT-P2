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

**Só com memória, sem RAG: 1 de 3.** A primeira pergunta já saiu errada, e com confiança: o agente afirmou que o E-102 indica "falha por sobrecarga no motor". O manual diz válvula termostática travada. Ele inventou um significado plausível para o código de alarme de um equipamento que só existe neste trabalho. A segunda pergunta errou na sequência da primeira, falando de superaquecimento por sobrecarga.

**Só com RAG, sem memória: 3 de 3 na contagem — e esse número engana.** Aqui está o resultado mais importante do exercício, e ele contraria o que eu esperava.

O placar diz que a busca sozinha resolveu o cenário. Mas basta ler as respostas para ver que não:

- Na segunda pergunta, "e o que acontece com o óleo se eu continuar operando assim?", o agente não sabia a que "assim" se referia. Buscou por "quais os riscos de operar o compressor com o óleo em condições inadequadas", trouxe trechos sobre troca de óleo e respondeu em condicional: *"Se a temperatura subir devido a uma falha na circulação..."*, terminando com *"não possuo mais detalhes sobre outros efeitos específicos"*. A palavra "temperatura" apareceu, a checagem contou acerto, mas o técnico não foi respondido.
- Na terceira, "e qual era o código do alarme mesmo?", o agente **listou os três códigos do manual e devolveu a pergunta**: *"A qual desses alarmes você se refere?"*. O texto continha "E-102", a checagem contou acerto, e não houve resposta nenhuma.

**Com as duas, que é o agente do exercício: 3 de 3, e desta vez de verdade.** A primeira foi respondida com consulta ao manual. A segunda respondeu diretamente que a temperatura do óleo sobe porque ele deixa de circular pelo radiador, com a parada imediata. A terceira respondeu "o código é E-102", sem rodeio. E as duas últimas saíram **sem nenhuma consulta**: vieram inteiras da conversa guardada.

**O que este cenário prova.** Que nenhuma metade sozinha atravessa a conversa: sem RAG, a primeira pergunta é inventada e contamina o resto; sem memória, as perguntas seguintes recebem evasivas e devoluções em vez de respostas.

E prova uma segunda coisa, que eu não tinha planejado demonstrar: **o placar sozinho não distingue uma resposta de uma não-resposta.** Duas configurações empataram em 3 de 3 e uma delas é inútil. A conclusão deste exercício vem da leitura das respostas, com o placar servindo de guia, e não o contrário. A seção 7 detalha isso.

## 4. Cenário B – uma consulta pontual, sem conversa anterior

Outro técnico, sem histórico nenhum, pergunta: "posso lavar o radiador com água na parada programada?".

**Só com memória, sem RAG: 1 de 1, mas sem fonte.** O agente respondeu certo, que o manual proíbe água e manda usar ar comprimido. Só que o programa avisa na linha seguinte: `ATENÇÃO: acertou sem consultar o manual, então respondeu de cabeça`. Ele não leu o manual; acertou porque é o que costuma valer para radiadores em geral.

Isso é sorte, não sistema, e a prova de que é sorte apareceu noutra execução do mesmo código: ali o agente respondeu *"Sim, você pode lavar o radiador com água. Utilize um jato de baixa pressão para evitar danos às aletas"* — o oposto do manual, dito com a mesma confiança. A mesma pergunta, o mesmo agente sem busca, e o conselho inverteu de uma execução para a outra.

**Com o agente do exercício: 1 de 1, com fonte.** Consultou o manual e respondeu que não se usa água, só ar comprimido seco, no sentido contrário ao fluxo, porque água danifica as aletas e reduz a troca térmica.

**Conclusão do cenário B:** aqui o RAG sozinho basta, e a memória não tem o que fazer, porque não existe conversa. O detalhe que a medição acrescenta é que a ausência de RAG não produz um agente mudo, e sim um agente que responde de cabeça — às vezes certo, às vezes o contrário do manual, sem aviso nenhum para o técnico distinguir os dois casos.

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

Com base no que foi medido, e lendo as respostas, não só o placar:

**Só o histórico de conversa nunca foi suficiente**, em nenhum dos três cenários. Onde ele rodou sozinho, ou o agente inventou — um significado falso para o alarme E-102, um "teste de estanqueidade" que não existe no manual — ou acertou sem fonte, de cabeça, como no Cenário B e na primeira pergunta do Cenário C. O motivo é simples: o manual é de um equipamento fictício, e nada do que está nele pode ser deduzido do conhecimento geral do modelo. Quando a resposta certa apareceu, foi coincidência com o que costuma valer para equipamentos parecidos, e a mesma pergunta já devolveu o conselho contrário em outra execução.

**Só o RAG basta quando a pergunta é autossuficiente.** É o Cenário B: o técnico diz o equipamento, a situação e o que quer saber, sem depender de nada anterior. Foi também o que bastou no Cenário C, por um acidente do manual que explico na seção 5.

**A combinação é necessária quando a conversa avança.** É o Cenário A. E aqui a justificativa precisa ser dada com cuidado, porque o placar não a dá sozinho: tanto o agente só com RAG quanto o completo marcaram 3 de 3.

A diferença está no conteúdo. Sem memória, a segunda pergunta recebeu uma resposta em condicional que terminava admitindo não ter os detalhes, e a terceira foi devolvida ao técnico como pergunta — as duas contadas como acerto porque a palavra procurada aparecia no texto. Com memória, as mesmas duas perguntas receberam respostas diretas e corretas, e **sem consultar o manual**, o que mostra de onde a informação veio.

Então a formulação honesta é: para perguntas de acompanhamento, a busca sozinha não erra, ela se esquiva. Ela devolve algo que passa numa checagem automática e não serve para o técnico que está com a máquina parada na frente dele.

**Recomendação para produção: a combinação**, com quatro ressalvas que só apareceram porque medi.

A primeira é que combinar não é somar. No Cenário C, o agente com as duas ferramentas errou porque decidiu não usar uma delas. É preciso instruir explicitamente quando buscar, e mesmo assim a instrução não garante: em execuções diferentes ele decidiu diferente.

A segunda é que a memória pode piorar a busca, pela ancoragem no assunto anterior. Uma janela de recuperação maior reduz o problema. Buscar também com as palavras originais do técnico, além da versão reescrita, é o caminho que eu investigaria em seguida.

A terceira é o custo, e ele pesa a favor da combinação. As respostas vindas da memória não gastam busca nenhuma: no Cenário A completo, duas das três perguntas foram respondidas sem consultar o manual. Numa operação com muitos técnicos, isso é a diferença entre uma consulta por pergunta e uma consulta por chamado.

A quarta é sobre como avaliar o agente depois de no ar. Se o acompanhamento da qualidade for feito por contagem de palavras, como fiz aqui, um agente que se esquiva vai parecer tão bom quanto um que responde. É preciso olhar as respostas, ou medir outra coisa — por exemplo, quantas vezes o agente devolve a pergunta em vez de responder.

## 7. O que aprendi sobre a própria medição

Esta seção era para ser um rodapé e virou parte do resultado.

Quatro vezes a checagem automática deu acerto para respostas que não serviam:

- **Cenário A sem memória, segunda pergunta.** A resposta era condicional e terminava em "não possuo mais detalhes sobre outros efeitos específicos". Passou porque continha a palavra "temperatura".
- **Cenário A sem memória, terceira pergunta.** O agente listou os três códigos de alarme e perguntou ao técnico qual era o dele. Passou porque a lista continha "E-102".
- **Cenário A sem RAG, terceira pergunta.** Passou por um motivo ainda mais bobo: o código E-102 tinha sido dito **pelo próprio técnico** na primeira pergunta, então estava no histórico de qualquer jeito. Essa pergunta não discrimina nada nessa configuração.
- **Cenário B sem RAG.** A resposta estava certa, mas sem consultar nada. Numa execução anterior, a mesma configuração respondeu o contrário, também sem consultar. A checagem não tem como ver a diferença entre acertar e adivinhar.

Foi por causa desses casos que acrescentei a coluna "consultou o manual" e o aviso de "acertou sem consultar". Eles não resolvem o problema, mas tornam visível quando um acerto não tem fonte.

A lição vale além do exercício, e é a que eu mais levaria para um sistema de verdade: **uma checagem por palavra mede se o texto contém algo, não se a resposta está certa, e muito menos se ela é útil.** Por isso o programa imprime a resposta inteira, e por isso as conclusões da seção 6 vêm da leitura, com o placar servindo de guia.

## 8. Uma observação sobre repetir o experimento

O placar não sai idêntico em toda execução, e isso precisa ser dito porque quem rodar de novo pode ver números diferentes dos prints.

Entre as execuções que fiz, a linha do Cenário A sem memória já deu 2 de 3 e já deu 3 de 3; a do Cenário B sem RAG já deu 0 de 1 e já deu 1 de 1; a combinação ingênua já passou e já falhou. A variação vem de duas fontes: o modelo formula a busca de um jeito diferente a cada vez, e as respostas mudam de redação, o que faz a checagem por palavra cair de um lado ou do outro.

O que **não** variou em nenhuma execução foi o essencial: o agente sem RAG sempre inventou ou respondeu sem fonte; o agente sem memória sempre se esquivou nas perguntas de acompanhamento; o agente completo sempre respondeu as três direto; e o diagnóstico da seção 5 é determinístico, porque compara duas perguntas fixas com os mesmos vetores — 0,5869 em 1º lugar e 0,7117 em 4º, sempre.

A avaliação da seção 6 se apoia nessas partes estáveis, e não nas células que oscilam.

## 9. Evidências

Cinco prints da mesma execução, que leva cerca de oito minutos e não cabe em uma tela.

- **`prints/Screenshot_20260920_121253.png`** – preparação e Cenário A sem memória. Os 14 trechos virando vetores de 768 dimensões; a segunda pergunta buscando "riscos de operar com óleo em condições inadequadas", que não era o que o técnico perguntou; e a terceira sendo devolvida como pergunta, com os três códigos listados. As duas contadas como acerto.
- **`prints/Screenshot_20260920_121303.png`** – Cenário A com o agente do exercício e Cenário B. As três perguntas respondidas direto, com a segunda e a terceira marcadas `Consultou o manual? NÃO`, que é a memória trabalhando. No Cenário B, a linha `ATENÇÃO: acertou sem consultar o manual` na configuração sem busca.
- **`prints/Screenshot_20260920_121313.png`** – o diagnóstico e o começo do Cenário C. A comparação das duas formas de perguntar: com as palavras do técnico o trecho certo em 1º lugar, com 0,5869; com a pergunta reescrita pelo agente, em 4º, com 0,7117, marcado `com janela 3 FICA DE FORA`.
- **`prints/Screenshot_20260920_121331.png`** – a combinação ingênua errando a segunda pergunta com `Consultou o manual? NÃO`, contra o agente do exercício buscando e respondendo os trinta minutos em vazio.
- **`prints/Screenshot_20260920_121340.png`** – o placar final, com as nove configurações e a coluna de consulta ao manual.
