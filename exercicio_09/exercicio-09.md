# Exercício 9 – Histórico de conversa e sessão persistente

O código está em `exercicio_09/conversa_persistente.py`. Para executar: `uv run exercicio_09/conversa_persistente.py`

**Este programa é feito para rodar duas vezes.** Ele percebe sozinho em qual execução está: olha se o arquivo de sessão já tem mensagens gravadas. Se não tem, é a primeira; se tem, é a segunda. Assim o mesmo comando, digitado duas vezes, mostra os dois lados do exercício.

O agente consulta o manual do Exercício 8 (`exercicio_08/manuais_com_pecas.json`), com a mesma ferramenta assíncrona de lá. Aqui ele responde em texto corrido, sem saída estruturada, porque o assunto deste exercício é o histórico.

## 1. O histórico na mão, com uma lista

A primeira parte simula três perguntas do mesmo técnico sobre a mesma esteira, numa execução só, sem usar sessão nenhuma. Quem carrega a conversa de uma pergunta para a outra sou eu, numa variável chamada `historico`, declarada como `list[TResponseInputItem]`.

O `TResponseInputItem` é o tipo de cada item que pode ser enviado ao agente. Não é só "mensagem do usuário": a lista guarda também a chamada da ferramenta, o resultado que ela devolveu e a resposta do modelo. É por isso que os números crescem de três em três, e não de um em um.

O ciclo de cada rodada é simples. Eu monto a entrada juntando o histórico acumulado com a pergunta nova, chamo o `Runner.run` com essa lista inteira, e depois substituo o histórico por `resultado.to_input_list()`. Esse método devolve tudo o que foi enviado mais o que voltou, já no formato de entrada, pronto para a próxima rodada.

**O que a execução mostra.** A lista começa com 1 item, só a primeira pergunta. Depois da primeira resposta ela tem 4: a pergunta do técnico, a chamada da ferramenta, o resultado da consulta ao manual e a resposta do agente. A segunda rodada envia 5 itens e termina com 6; a terceira envia 7 e termina com 8.

A prova de que o histórico está funcionando está no conteúdo das perguntas. A segunda é "E quais peças eu levo para resolver?" e a terceira é "Qual é a prioridade da primeira dessas peças?". Nenhuma das duas diz de que equipamento se trata, nem qual é o erro, nem quais são as peças. Mesmo assim o agente respondeu a graxa de lítio EP-2 e o retentor do mancal, com as quantidades certas, e depois disse que a prioridade da primeira é alta — tudo confere com o manual para o erro E-302 da esteira EST-450.

Repare também que a ferramenta só foi chamada uma vez, na primeira pergunta. Nas outras duas o agente respondeu a partir do que já estava na lista.

No fim da parte 1 o programa avisa: essa lista está na memória do processo. Quando o programa fecha, ela some. **É exatamente a queixa do técnico no enunciado.**

## 2. A sessão que sobrevive ao programa

A segunda parte resolve essa queixa com a `SQLiteSession`, gravando em `exercicio_09/sessao_tecnico.db`, com o identificador `"tecnico-joao"`.

**Na primeira execução,** o técnico pergunta sobre o forno FRN-720 com o erro E-401. O agente consulta o manual e responde: vazamento na linha de pressão, levar 1 mangueira de pressão e 4 abraçadeiras, aguardando o resfriamento antes de mexer. O programa mostra que ficaram 4 mensagens gravadas no arquivo e informa o tamanho dele em disco. Aí ele pede para rodar de novo.

**Na segunda execução,** que é um processo totalmente novo, o programa já começa diferente: antes de perguntar qualquer coisa, ele encontra as 4 mensagens no arquivo e anuncia que esta é a segunda execução. Nada disso veio da memória, porque memória não existe mais — veio do disco.

A pergunta de acompanhamento é "Qual era mesmo a ação recomendada para aquele erro?". Ela não diz o equipamento, não diz o código do erro, não diz nada. O agente respondeu "aguardar o resfriamento do forno e conferir o aperto das conexões", que é o que o manual traz para o E-401 do FRN-720.

Ao final, a sessão passa a ter 6 mensagens. Cresceu de 2, e não de 4 como na primeira execução, porque desta vez não houve chamada de ferramenta: entrou só a pergunta e a resposta.

## 3. A diferença entre as duas partes, que é o ponto do exercício

As duas partes fazem a mesma coisa: garantir que o modelo receba a conversa anterior junto com a pergunta nova. O modelo não lembra de nada por conta própria, nunca. Toda memória de agente é, no fundo, reenviar o que já aconteceu.

O que muda é **quem faz esse trabalho e onde a conversa fica guardada.**

Na parte 1, quem faz sou eu. Eu declaro a lista, junto a pergunta nova, passo tudo ao `Runner.run` e atualizo a lista com o retorno. Isso me dá controle total: eu poderia descartar itens antigos, resumir o começo da conversa, apagar uma pergunta específica. Em troca, a conversa mora na memória do processo e morre com ele.

Na parte 2, quem faz é o SDK. Eu passo `session=sessao` e ele cuida de tudo: grava o que entrou e o que saiu, e reenvia sozinho na execução seguinte. Eu perco o controle fino sobre o que é enviado, mas ganho a persistência — e persistência era o problema a resolver.

Escolher entre os dois é escolher entre controle e conveniência. Para o caso do enunciado, em que o técnico fecha o assistente e volta no dia seguinte, só a sessão serve.

## 4. Dois detalhes do código que valem explicar

**A ferramenta proibida na pergunta de acompanhamento.** Na segunda execução, o agente roda com `agente.clone(model_settings=ModelSettings(tool_choice="none"))`. Isso resolve dois problemas de uma vez. O primeiro é o laço que apareceu no Exercício 7, em que o agente com sessão e ferramenta insistia em consultar o manual sem parar. O segundo é de prova: se o agente não pode consultar o manual, a resposta certa só pode ter vindo do arquivo em disco. Sem essa trava, alguém poderia dizer que ele apenas consultou o manual de novo e acertou por sorte.

**A detecção automática da execução.** O programa poderia receber um argumento na linha de comando dizendo qual execução é. Preferi que ele descubra sozinho, contando as mensagens da sessão, porque isso deixa a demonstração mais honesta: é o mesmo comando, digitado duas vezes, produzindo saídas diferentes. A diferença vem do arquivo em disco, que é justamente o que o exercício quer mostrar.

Uma consequência prática: para repetir a demonstração do zero, é preciso apagar o `sessao_tecnico.db` antes. Por isso o arquivo não é versionado no Git — se ele viesse junto com o código, a primeira execução de quem baixasse o projeto já seria tratada como segunda.

## 5. Evidências

*(inserir os prints depois de tirá-los)*

- Print 1 – primeira execução: o aviso de que nenhuma mensagem foi encontrada, as três rodadas da Parte 1 com a lista crescendo de 1 para 8 itens e as perguntas incompletas sendo respondidas certo, e a Parte 2 gravando as 4 primeiras mensagens no arquivo: `prints/...`
- Print 2 – segunda execução: o mesmo comando encontrando as 4 mensagens em disco, reconhecendo que é a segunda execução, e a pergunta de acompanhamento respondida sem o técnico repetir o contexto e sem nenhuma chamada da ferramenta: `prints/...`
