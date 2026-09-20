# O laço de ferramenta do Exercício 7 — o que estava acontecendo

Anotação de estudo, escrita em 20/09/2026. Não faz parte da entrega: serve para eu conseguir
explicar o problema e a decisão do `tool_choice` com as minhas palavras, na apresentação.

## 1. O sintoma

Na parte 3 do Exercício 7, a segunda pergunta da sessão ("E qual a ação recomendada mesmo?")
às vezes nunca terminava. A saída ficava repetindo a mesma linha, `[tool consultar_manual_equipamento] código TRN-300`,
uma atrás da outra, e no fim o programa parava com o erro `MaxTurnsExceeded: Max turns (10) exceeded`.

Quer dizer: o agente chamava a ferramenta, recebia o dado do manual, e em vez de responder,
chamava a ferramenta de novo, com exatamente os mesmos argumentos. Dez vezes. Aí o SDK desistia.

## 2. Como funciona o laço do agente, que é onde o problema mora

Esta é a parte central para explicar. Um agente não é uma chamada só ao modelo. O `Runner.run`
roda um laço, e cada volta desse laço é uma "rodada" (turn):

1. O SDK manda para o modelo a conversa inteira mais a lista de ferramentas disponíveis.
2. O modelo responde uma de duas coisas: ou **uma chamada de ferramenta**, ou **a resposta final**.
3. Se foi chamada de ferramenta, o SDK executa a função Python, coloca o resultado na conversa
   e **volta ao passo 1**.
4. Se foi resposta final, o laço termina e o `Runner.run` devolve o resultado.

Repare na consequência: **quem decide que a conversa acabou é o modelo**, não o meu código. O laço
só para quando o modelo resolve parar de pedir ferramenta. O `max_turns` (10 por padrão) é apenas
uma trava de segurança para o programa não rodar para sempre.

O `output_type` deixa isso mais rígido ainda. Com saída estruturada, a única forma de encerrar é o
modelo devolver o JSON com os três campos do `DiagnosticoEquipamento`. Enquanto ele insistir em
chamar a ferramenta, não existe resposta final, e o laço continua até bater no `max_turns`.

## 3. Por que o modelo insistia

Na segunda pergunta, o dado já estava na conversa: a sessão tinha guardado a pergunta anterior, a
chamada da ferramenta, o resultado do manual e a resposta. O modelo não precisava consultar nada.

Só que duas coisas empurravam para o outro lado:

- A ferramenta continuava **disponível** naquela rodada. Nada no código impedia o uso dela.
- A instrução do sistema mandava "consulte o manual com a ferramenta antes de responder". Eu tinha
  acrescentado uma ressalva ("se a informação já tiver aparecido antes nesta conversa, responda
  direto, sem chamar a ferramenta de novo"), mas isso é **um pedido em texto**, não uma regra.

E a pergunta "E qual a ação recomendada mesmo?" é vaga de propósito. Um modelo pequeno como o
`gemini-3.1-flash-lite`, em dúvida, faz o que a instrução principal mandou: consulta o manual. Recebe
o dado, continua em dúvida, consulta de novo. Nada no estado da conversa muda o suficiente entre uma
rodada e outra para ele mudar de ideia — por isso o laço se repete idêntico.

## 4. O ponto mais importante: era aleatório

Isto é o que eu mais preciso saber explicar, porque é contraintuitivo.

O mesmo código, com o mesmo histórico, falhava numa execução e funcionava na seguinte. Medindo o
agente sem restrição: **laço em 3 de 4 execuções**. Ou seja, não era um defeito que sempre acontece
nem um erro de programação no sentido comum. Era uma escolha do modelo, e escolhas de modelo têm
uma dose de acaso.

Isso muda a natureza da solução. Não adianta "consertar" com um texto melhor na instrução, porque
não dá para garantir obediência. Um comportamento que eu preciso que aconteça sempre tem que ser
imposto por **parâmetro**, não pedido por instrução.

## 5. Duas suspeitas que eu testei e descartei

Antes de chegar nessa conclusão, investiguei duas explicações que pareciam boas e não eram. Vale
contar, porque mostra que a conclusão veio de teste e não de chute.

**Suspeita 1 — as assinaturas de raciocínio do Gemini.** Quando o Gemini chama uma ferramenta, ele
devolve junto um campo chamado `thought_signature`, uma espécie de lacre do raciocínio dele. A
`SQLiteSession` guarda esse campo no histórico e o reenvia nas rodadas seguintes. Eu suspeitei que
reenviar um lacre antigo estivesse confundindo o modelo. Montei duas versões do mesmo histórico, uma
com o campo e outra sem, e rodei as duas. **Na primeira tentativa pareceu confirmar** — a versão com
assinatura entrou em laço e a sem assinatura não. Mas quando repeti três vezes de cada lado, as duas
versões responderam direto. Era coincidência. Descartada.

**Suspeita 2 — o tamanho da resposta da ferramenta.** O manual do torno devolve três erros conhecidos,
um bloco de texto razoavelmente grande. Suspeitei que o modelo estivesse se perdendo nele. Cortei a
resposta para um erro só e rodei. Continuou entrando em laço. Descartada.

A lição desses dois testes: **uma única execução não prova nada** quando o comportamento é aleatório.
Foi repetindo que eu percebi o que realmente estava acontecendo.

## 6. A solução e por que ela funciona

Na segunda pergunta, o mesmo agente roda com a escolha de ferramenta travada:
`agente.clone(model_settings=ModelSettings(tool_choice="none"))`.

O `tool_choice` é um parâmetro do próprio protocolo de chat, enviado na requisição junto com a lista
de ferramentas. Com o valor `"none"`, o provedor **não aceita** uma chamada de ferramenta como
resposta. O modelo deixa de ter essa saída disponível e é obrigado a produzir a resposta final — que,
no nosso caso, só pode vir do histórico guardado na sessão.

Resultado medido: **6 execuções seguidas**, todas respondendo direto, nenhuma chamada de ferramenta.

O `clone` é o que permite manter um agente só. Ele cria uma cópia do agente mudando apenas o que eu
pedir; tudo o mais (nome, instruções, modelo, ferramentas, `output_type`) continua igual. Então o que
muda entre a primeira e a segunda pergunta é um parâmetro de execução, não o agente.

## 7. Se me perguntarem

**"Por que não tirou a ferramenta do agente na segunda pergunta?"**
Era a solução anterior e funcionava, mas criava dois agentes diferentes, e o enunciado fala de um
agente com sessão. Com `tool_choice="none"` o agente é um só.

**"Você não está trapaceando ao proibir a ferramenta? O modelo poderia ter acertado sozinho."**
Poderia, e às vezes acertava. O problema é justamente o "às vezes". Além disso, proibir a ferramenta
torna a demonstração da memória mais forte: se ele não pode consultar o manual, a resposta correta só
pode ter vindo do histórico. A proibição é ao mesmo tempo a correção do defeito e a prova do conceito.

**"Isso é um defeito do Gemini?"**
Não exatamente. É o comportamento esperado de um laço de agente quando a ferramenta continua
disponível e a decisão de parar fica com o modelo. Um modelo maior erraria menos, mas a garantia
continuaria vindo do parâmetro. Testei o mesmo caso no OpenRouter com o DeepSeek e ele falhou de
outro jeito: devolveu um JSON inválido para o formato pedido.

**"Qual a relação com o Exercício 6?"**
É a mesma lição, vista de outro ângulo. No Exercício 6 eu mostrei que uma boa descrição de ferramenta
aumenta a chance de o modelo escolher certo, mas só o `tool_choice` garante. Aqui a mesma coisa
aparece como um defeito concreto: o pedido em texto não segurou, o parâmetro segurou.
