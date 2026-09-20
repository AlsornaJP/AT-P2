# Como funciona a busca por vetores, em linguagem comum

Anotação de estudo, escrita em 20/09/2026. Não faz parte da entrega: serve para eu conseguir
explicar com as minhas palavras a busca semântica dos exercícios 10 e 11.

## 1. O problema que essa busca resolve

Um computador compara textos letra por letra. Ele consegue dizer se duas frases têm palavras em
comum, e é só isso. Não consegue dizer se elas falam da mesma coisa.

Isso ficou claro no Exercício 10. O técnico perguntou "com que força eu devo apertar os parafusos
da tampa superior?" e o manual dizia "torque de aperto dos parafusos do cabeçote". As duas frases
falam exatamente da mesma coisa e quase não compartilham palavras. A busca por contagem de palavras
achou só "compressor" em comum, que é a palavra mais inútil do manual inteiro, já que o manual é
todo sobre o compressor.

Então a pergunta é: como fazer o computador achar um texto pelo **sentido**, e não pela escrita?

## 2. A ideia: transformar sentido em endereço

Existe um tipo de modelo, chamado modelo de embedding, cujo trabalho é só esse: você entrega um
texto e ele devolve uma lista de números. No nosso caso, 768 números.

A melhor forma de pensar nisso é um mapa.

Num mapa comum, cada lugar tem duas coordenadas: latitude e longitude. Duas cidades vizinhas têm
coordenadas parecidas. Se eu te der só os números, sem o nome, você ainda consegue dizer quais
cidades estão perto umas das outras — basta comparar os números.

O modelo de embedding faz a mesma coisa, só que o mapa dele não é de lugares, é de **assuntos**. E
em vez de 2 coordenadas, cada texto ganha 768. Textos que falam da mesma coisa caem em regiões
vizinhas desse mapa, mesmo quando estão escritos com palavras completamente diferentes.

Uma dúvida que aparece naturalmente: o que cada um dos 768 números significa? A resposta honesta é
que ninguém sabe, e ninguém decidiu. O modelo aprendeu essas coordenadas sozinho, lendo uma
quantidade enorme de texto, e foi ajustando até que textos de assunto parecido caíssem perto. Não
existe um número que seja "o número da mecânica" e outro que seja "o número da eletricidade". O
significado está espalhado pelos 768 de um jeito que não dá para ler diretamente. O que importa é
que a vizinhança funciona.

Por que 768? O modelo entrega 3.072 por padrão, e eu pedi uma versão reduzida. Mais números
significam mais capacidade de distinguir assuntos parecidos, e também mais memória e mais tempo de
comparação. Com 14 trechos, 768 sobra.

## 3. A comparação: ângulo, não distância

Agora eu tenho 14 endereços, um por trecho do manual, e preciso achar qual está mais perto do
endereço da pergunta.

Imagine cada endereço como uma **seta** que sai do centro do mapa e vai até aquele ponto. Para
comparar dois textos, eu meço o **ângulo entre as duas setas**:

- Setas apontando para o mesmo lado, ângulo perto de zero: os textos falam da mesma coisa.
- Setas em direções sem relação: os textos falam de coisas diferentes.

O número que sai dessa conta vai de -1 a 1, e na prática, com textos, fica entre 0 e 1. Quanto mais
perto de 1, mais alinhadas estão as setas, mais parecido é o assunto. Esse número tem um nome
técnico, similaridade de cosseno, mas a ideia é só essa: o quanto duas setas apontam para o mesmo
lado.

**Por que ângulo e não distância?** Porque a distância seria afetada pelo tamanho da seta, e o
tamanho tem a ver com o tamanho e a intensidade do texto, não com o assunto. Um parágrafo longo e
uma frase curta sobre o mesmo tema devem contar como parecidos. Medindo o ângulo, eu ignoro o
comprimento e olho só a direção — que é onde mora o assunto.

Na conta, isso aparece assim: eu multiplico os números correspondentes das duas listas e somo tudo,
e depois divido pelo comprimento de cada seta. É exatamente essa divisão pelo comprimento que tira
o efeito do tamanho. São três linhas de Python, sem biblioteca nenhuma.

## 4. O caminho completo, do começo ao fim

1. O manual é quebrado em 14 trechos.
2. Cada trecho é enviado ao modelo de embedding e volta como uma lista de 768 números. Mando os 14
   de uma vez só, numa chamada, porque a conta gratuita limita chamadas por minuto.
3. A pergunta do técnico é enviada do mesmo jeito e vira outra lista de 768 números.
4. Comparo a seta da pergunta com as 14 setas dos trechos, uma por uma, e ordeno da mais alinhada
   para a menos alinhada.
5. Pego os primeiros da fila e entrego só eles ao agente, junto com a pergunta.
6. O agente responde usando apenas esses trechos.

O passo 5 é a "janela". No Exercício 10 eu entregava 3 trechos; no Exercício 11 passei a entregar 5,
por um motivo que está explicado na seção 6.

## 5. Por que não usei banco de vetores

Existe um tipo de banco de dados feito para guardar esses endereços e achar os vizinhos rapidamente.
Eu não usei, de propósito.

Com 14 trechos, comparar um por um é instantâneo. Um banco de vetores serve quando são milhões de
trechos e percorrer todos fica caro; o que ele faz por dentro é uma versão esperta dessa mesma
comparação, que evita olhar todos. Fazendo na mão, o exercício mostra o que está realmente
acontecendo, em vez de esconder atrás de uma biblioteca.

## 6. A armadilha dos números, que eu preciso saber explicar

Esta é a parte que mais rende pergunta, porque é contraintuitiva.

No Exercício 11, comparei duas formas de perguntar a mesma coisa:

- Com as palavras do técnico, "E depois de apertar, o que eu faço?", o trecho certo ficou em **1º
  lugar**, com nota **0,5869**.
- Com a pergunta reescrita pelo agente, "procedimento após aperto dos parafusos do cabeçote do
  compressor CMP-100", o trecho certo caiu para **4º lugar**, com nota **0,7117**.

Repare: a busca que deu errado tem nota maior. Isso não é um defeito, é o que a nota mede.

A nota diz **o quanto o trecho se parece com a pergunta que eu fiz**. Ela não diz se a resposta está
certa. Quando o agente reescreveu a pergunta enfiando "cabeçote" e "CMP-100", ele criou uma pergunta
muito parecida com os trechos sobre o torque do cabeçote — e esses trechos subiram, com notas altas,
empurrando para baixo o trecho que falava do que fazer depois do aperto.

Daí a regra prática: **as notas só podem ser comparadas entre si dentro da mesma pergunta.** Comparar
o 0,58 de uma busca com o 0,71 de outra não quer dizer nada, porque são perguntas diferentes.

Foi por isso que ampliei a janela de 3 para 5 trechos no Exercício 11: o trecho certo estava em 4º
lugar, e com 5 ele entra.

## 7. Se me perguntarem

**"O modelo entende o texto?"**
Não no sentido de compreender. Ele aprendeu, lendo muito texto, que certas palavras aparecem nos
mesmos contextos, e isso basta para colocar "força de aperto" e "torque" em regiões vizinhas do
mapa. É estatística sobre uso de linguagem, não compreensão.

**"Por que 768 números? Por que não 10, ou 2?"**
Porque assunto é uma coisa complicada de representar. Com poucos números, textos diferentes acabam
caindo no mesmo lugar e a busca confunde tudo. O modelo oferece 3.072 por padrão; reduzi para 768
para economizar memória e tempo, o que não faz diferença com 14 trechos.

**"A nota 0,58 é ruim? Parece baixa."**
Não dá para julgar isoladamente. O que importa é a ordem: naquela busca, 0,5869 foi o maior de todos
e era o trecho certo. Em outra busca, 0,71 foi o maior e estava errado. A nota é uma régua relativa
dentro de cada consulta.

**"Por que não comparar a pergunta com o manual inteiro, sem quebrar em trechos?"**
Por duas razões. O manual inteiro não caberia no contexto de uma chamada, que é o problema que o
exercício quer resolver. E mesmo que coubesse, um endereço único para um texto grande fica uma
média de todos os assuntos dele, e média de assuntos não é parecida com nada em específico.

**"Isso é o mesmo que a busca do Google?"**
É a mesma família de ideia, a de achar por sentido em vez de por palavra exata. O que eu fiz aqui é
a versão mínima e explícita: sem banco de vetores, sem otimização, comparando um por um.
