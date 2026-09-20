# Busca por vetores — versão curta, para falar

Meia página, para o vídeo. A versão longa, para estudar, está em
[como-funciona-a-busca-por-vetores.md](como-funciona-a-busca-por-vetores.md).

---

**O problema.** O computador compara textos letra por letra. Por isso a busca por palavra-chave
falhou no meu teste: o técnico perguntou com que "força" apertar os parafusos, e o manual fala em
"torque". Mesma coisa, nenhuma palavra em comum.

**O truque.** Existe um modelo que lê um texto e devolve uma lista de números — aqui, 768 números.
É como um endereço num mapa. Num mapa comum o endereço tem dois números, latitude e longitude, e
cidades vizinhas têm números parecidos. Esse mapa tem 768 eixos, e o que fica perto não são
cidades, são assuntos. Textos que falam da mesma coisa ganham endereços vizinhos, mesmo escritos
com palavras diferentes. Ninguém decidiu o que cada número significa; o modelo aprendeu sozinho,
lendo muito texto.

**A comparação.** Penso em cada endereço como uma seta saindo do centro do mapa. Para comparar dois
textos, meço o ângulo entre as duas setas: apontando para o mesmo lado, mesmo assunto. Isso dá um
número entre 0 e 1. Uso o ângulo, e não a distância, porque a distância seria influenciada pelo
tamanho do texto, e eu quero comparar assunto, não tamanho. São três linhas de Python, sem
biblioteca.

**O caminho.** Quebrei o manual em 14 trechos, virei cada um em endereço, virei a pergunta em
endereço, comparei com os 14 e entreguei os 5 mais alinhados ao agente.

**A armadilha, que é o que eu mais quero mostrar.** No Exercício 11 comparei duas formas de
perguntar a mesma coisa. Com as palavras do técnico, o trecho certo ficou em 1º lugar, com nota
0,5869. Com a pergunta reescrita pelo agente, que puxou "cabeçote" da conversa anterior, o trecho
certo caiu para 4º, com nota 0,7117. **A busca errada tem a nota maior.** Porque a nota mede
parecença com a pergunta que eu fiz, não acerto da resposta. Se a pergunta aponta para o lado
errado, a busca acerta o alvo errado com precisão.
