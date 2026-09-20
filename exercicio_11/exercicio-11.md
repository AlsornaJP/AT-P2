# Exercício 11 – Agente integrador com memória e avaliação de estratégia

O código está em `exercicio_11/agente_integrador.py`. Para executar: `uv run exercicio_11/agente_integrador.py`

O programa demora alguns minutos, porque roda os mesmos cenários em várias configurações, com pausas para respeitar o limite de chamadas por minuto da conta gratuita.

## 1. O agente integrador

É um agente só, o "Assistente de Campo", que junta as duas formas de memória construídas nos exercícios anteriores:

- **Memória de conversa**, com a `SQLiteSession` do Exercício 9, que guarda as perguntas e respostas e reenvia tudo na próxima pergunta.
- **Recuperação semântica**, com o pipeline de RAG do Exercício 10: o manual longo é segmentado em 14 trechos, cada trecho vira um vetor, e a ferramenta `buscar_no_manual` devolve os mais parecidos com a pergunta.

A instrução manda usar a conversa anterior para entender perguntas curtas, usar a busca quando precisar de um procedimento, responder apenas com o que estiver na conversa ou nos trechos, e dizer que não sabe em vez de inventar.

## 2. Como eu medi

Para avaliar qual estratégia é necessária, não basta rodar o agente completo e ver que ele funciona. É preciso **desligar cada metade e ver o que quebra**. Então o mesmo cenário roda em configurações diferentes: só com RAG, só com memória, e com os dois.

Cada pergunta tem um dado esperado, e o programa confere se ele aparece na resposta. O programa também registra **se o agente consultou o manual**, o que é tão importante quanto o acerto: uma resposta certa sem consulta não veio do manual, veio da cabeça do modelo, e não é confiável.

Essa checagem é simples, por palavra, e erra em alguns casos. Isso apareceu de verdade nos resultados, e está relatado na seção 7, porque é parte honesta do que eu observei.

## 3. Cenário A – três perguntas de acompanhamento sobre o mesmo chamado

Um técnico abre um chamado sobre o alarme E-102 e faz três perguntas encadeadas, cada uma mais curta e mais dependente do que veio antes. A terceira é "e qual era o código do alarme mesmo?".

**Só com RAG, sem memória: 2 de 3.** A segunda pergunta, "e o que acontece com o óleo se eu continuar operando assim?", quebrou de um jeito interessante: sem a conversa, o agente não sabia a que "assim" se referia, então buscou no manual por "consequências de operar o compressor com óleo inadequado", trouxe os trechos errados e respondeu que não encontrou. A busca funcionou; o que faltou foi saber o que buscar.

A terceira pergunta foi marcada como acerto, mas não foi. O agente listou os três códigos de alarme do manual e perguntou de volta "qual deles você está observando no painel?". Ele não sabia qual era o alarme do chamado, porque não tinha a conversa.

**Com tudo ligado: 3 de 3.** E o detalhe que mais importa está na coluna de consulta ao manual: a segunda e a terceira perguntas foram respondidas **sem nenhuma consulta**. Vieram inteiras da conversa guardada.

**Conclusão do cenário A:** para perguntas de acompanhamento, quem resolve é a memória de conversa. O RAG não atrapalha, mas também não substitui: ele responde a pergunta que recebe, e perguntas de acompanhamento chegam incompletas.

## 4. Cenário B – uma consulta pontual, sem conversa anterior

Outro técnico, sem histórico nenhum, faz uma pergunta única sobre um procedimento que está num parágrafo do fim do manual: "posso lavar o radiador com água na parada programada?".

**Só com memória, sem RAG: 0 de 1.** E não foi um erro qualquer. O agente respondeu: *"Sim, você pode lavar o radiador com água. Utilize um jato de baixa pressão para evitar danos às aletas."* O manual diz o contrário: limpar com ar comprimido seco, e que água danifica as aletas.

Isso é o pior tipo de falha. O agente não disse que não sabia, como a instrução mandava. Ele respondeu com segurança uma informação plausível, do conhecimento geral dele sobre radiadores, e essa resposta estragaria o equipamento.

**Com tudo ligado: 1 de 1.** Consultou o manual e respondeu que não se usa água, só ar comprimido seco, no sentido contrário ao fluxo.

**Conclusão do cenário B:** para consultas pontuais, quem resolve é o RAG. A memória de conversa não tem nada a oferecer, porque não existe conversa. E a ausência de RAG não deixa o agente mudo: deixa ele inventando.

## 5. Cenário C – o acompanhamento que exige um procedimento novo

Aqui está o caso que o enunciado pede: o cenário em que uma das duas não basta.

O técnico pergunta o torque dos parafusos do cabeçote, que está num trecho do manual. Depois pergunta, curto: "e depois de apertar, o que eu faço?". Essa segunda pergunta precisa das duas coisas ao mesmo tempo. Da conversa, para saber que "apertar" se refere aos parafusos do cabeçote. Do manual, para achar o procedimento de rodar trinta minutos em vazio e reconferir, que está em **outro** trecho, e que nunca foi conversado.

**Só com RAG: 1 de 2.** A segunda pergunta falhou, e o agente nem chegou a buscar: sem a conversa, "depois de apertar" não tinha sentido, e ele improvisou uma resposta genérica sobre verificar vazamentos.

**Só com memória: 1 de 2.** A primeira pergunta foi marcada como acerto, mas o programa avisa que ele **não consultou o manual**: acertou os 45 N·m de cabeça. É sorte, não sistema. A segunda falhou, inventando um "teste de estanqueidade" que não existe no manual.

**Com os dois ligados, instrução original: 1 de 2.** Este é o resultado mais instrutivo do exercício. O agente tinha memória e tinha busca, e mesmo assim errou — porque **decidiu não buscar**. Ele achou que já sabia o bastante pela conversa e respondeu que "o manual não especifica procedimentos adicionais". Ter as duas ferramentas não garante que as duas sejam usadas.

### O diagnóstico, que é a parte mais reveladora

Antes de culpar a busca, o programa mede se ela acharia o trecho certo, se fosse chamada. E o resultado explica tudo:

- Com **as palavras do próprio técnico**, "E depois de apertar, o que eu faço?", o trecho que responde fica em **1º lugar**, com similaridade 0,5869.
- Com **a pergunta reescrita pelo agente**, "procedimento após aperto dos parafusos do cabeçote do compressor CMP-100", o mesmo trecho cai para **4º lugar**, com 0,7117 — **fora** da janela de 3 trechos que a ferramenta devolve.

O que aconteceu foi que o agente, ao reescrever a pergunta, puxou "cabeçote" e "CMP-100" da conversa anterior. Isso ancorou a busca no assunto velho, e os trechos sobre o torque do cabeçote afundaram o trecho sobre o que fazer depois.

Ou seja: **a memória de conversa atrapalhou a recuperação semântica.** Essa mesma reescrita tinha ajudado no Exercício 10, onde traduziu a fala do técnico para o vocabulário do manual. Aqui, ela contaminou a busca com contexto que já não era o assunto.

Repare também num detalhe contraintuitivo dos números: a busca com a pergunta reescrita tem notas **mais altas** (0,74 contra 0,58), e ainda assim traz os trechos errados. Similaridade alta não quer dizer resposta certa; quer dizer parecença com o que foi perguntado. Se a pergunta aponta para o lado errado, a busca acerta o alvo errado com precisão.

### As duas correções testadas

**Instrução reforçada:** mandei consultar o manual sempre que a pergunta envolver procedimento, valor ou passo de manutenção, mesmo que o agente ache que já sabe. Na execução do print, isso resolveu: 2 de 2. Mas numa execução anterior a mesma configuração falhou, porque a pergunta reescrita saiu diferente e o trecho certo ficou de fora de novo. A instrução aumenta a chance, não garante — a mesma lição dos exercícios 6 e 7.

**Janela maior:** ampliar de 3 para 5 os trechos devolvidos pela busca. Como o trecho certo estava em 4º lugar, ele entra na janela. Essa correção é mais confiável que a instrução, porque não depende de como o modelo formulou a pergunta naquela execução. O custo é mandar mais texto ao modelo a cada resposta.

## 6. A avaliação de estratégia, que é o que o enunciado pede

Com base no que foi observado:

**Só histórico de conversa basta** quando o técnico já recebeu a informação e está desdobrando o mesmo assunto. É o Cenário A a partir da segunda pergunta: as respostas saíram sem nenhuma consulta ao manual. É a situação mais comum no dia a dia de um chamado, e é barata, porque não custa busca nenhuma.

**Só RAG basta** quando a pergunta é autossuficiente: o técnico diz o equipamento, o problema e o que quer saber, e não há conversa anterior. É o Cenário B. É a situação típica de quem abre o assistente para tirar uma dúvida pontual e fecha.

**A combinação é necessária** quando a pergunta é curta mas o assunto é novo. É o Cenário C, e não é um caso raro: é o que acontece naturalmente quando um chamado avança. O técnico não volta a dizer o nome do equipamento a cada frase, e ao mesmo tempo vai precisando de procedimentos diferentes conforme o serviço anda. Nesse caso, a memória diz **sobre o quê** e a busca diz **o quê**, e faltando qualquer uma das duas a resposta sai errada.

**Para o lançamento em produção, a recomendação é a combinação**, com duas ressalvas que os testes mostraram e que eu não teria previsto sem medir:

A primeira é que combinar as duas não é somar. No Cenário C com tudo ligado, o agente errou porque decidiu não buscar. É preciso instruir explicitamente quando usar cada mecanismo, e mesmo assim a instrução não garante.

A segunda é que a memória pode piorar a busca. Como o contexto da conversa entra na formulação da pergunta enviada ao índice, conversas longas tendem a ancorar as buscas no assunto que já passou. Uma janela de recuperação maior reduz o problema; buscar também com as palavras originais do técnico, sem a reescrita, é o caminho que eu investigaria em seguida.

## 7. O que aprendi sobre a própria medição

Duas vezes a minha checagem automática deu acerto para uma resposta ruim, e vale registrar.

No Cenário A sem memória, a terceira pergunta foi marcada como acerto porque a resposta continha "E-102" — só que continha por estar **listando todos os códigos** do manual e perguntando qual era o do técnico. Não era uma resposta, era uma devolução da pergunta.

Numa execução anterior, no Cenário B, a resposta errada "sim, pode lavar com água, evitando danificar as aletas" foi marcada como acerto porque eu tinha posto "aletas" entre as palavras esperadas. Corrigi para exigir "ar comprimido", que é o que a resposta certa necessariamente diz, e aí a falha apareceu.

A lição vale além do exercício: uma checagem por palavra mede se o texto contém algo, não se a resposta está certa. Por isso o programa também mostra a resposta inteira e se houve consulta ao manual, para dar de conferir à mão o que a contagem automática diz.

## 8. Evidências

*(inserir os prints depois de tirá-los)*

- Print – Cenários A e B: `prints/...`
  - O Cenário A sem memória errando a segunda pergunta e devolvendo a terceira como pergunta, contra o completo acertando as três, com as duas últimas **sem consultar o manual**.
  - O Cenário B sem RAG respondendo que pode lavar o radiador com água, contra o completo respondendo que só ar comprimido seco.
- Print – Diagnóstico e Cenário C: `prints/...`
  - A comparação das duas formas de perguntar, com o trecho certo em 1º lugar pelas palavras do técnico e em 4º pela pergunta reescrita pelo agente.
  - As configurações do Cenário C, incluindo a do agente completo que não chegou a buscar.
- Print – Placar final: `prints/...`
  - A tabela com todas as configurações, os acertos e a coluna que mostra em quais perguntas o manual foi consultado.
