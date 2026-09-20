# Exercício 8 – Modelos aninhados e agente de diagnóstico completo

O código está em `exercicio_08/diagnostico_completo.py`. Para executar: `uv run exercicio_08/diagnostico_completo.py`

O manual deste exercício é próprio, o `manuais_com_pecas.json`, gerado por `gerar_manual_com_pecas.py`. Ele usa a mesma seed do Exercício 5, então os erros conhecidos saem idênticos aos de lá; o que muda é que cada erro agora traz também a lista de peças de reposição. Preferi um arquivo próprio a alterar o do Exercício 5, que já está entregue e tem print tirado.

## 1. Os dois modelos, um dentro do outro

São duas classes Pydantic. A `PecaRecomendada` tem `nome` (texto), `quantidade` (número inteiro) e `prioridade` (texto). A `DiagnosticoEquipamento` tem os três campos que já existiam no Exercício 7 e ganhou um quarto: `pecas_recomendadas`, declarado como `list[PecaRecomendada]`.

Essa anotação é o ponto central do exercício. Ela diz duas coisas ao mesmo tempo: que o campo é uma lista, de tamanho livre, e que cada item dessa lista tem que ter a forma da `PecaRecomendada`. O SDK transforma isso no formato que é enviado ao modelo, e o Pydantic valida a resposta que volta.

O programa comprova que o aninhamento funcionou de verdade, e não só no papel. Ele imprime o tipo do objeto de fora (`DiagnosticoEquipamento`), percorre a lista item a item e imprime o tipo de cada peça (`PecaRecomendada`) e o tipo do campo quantidade (`int`). Ou seja: o que chega ao programa é objeto Python de verdade, com número onde deve haver número, e não um texto que só parece um.

Como no Exercício 7, cada campo tem uma descrição escrita com `Field(description=...)`. Na descrição da lista eu incluí a regra do caso de erro: a lista deve ficar vazia se o equipamento não for encontrado.

## 2. A ferramenta assíncrona e o tratamento de erro dela

A ferramenta agora é declarada com `async def`. Só que trocar a palavra na frente da função não torna nada simultâneo. Se o corpo dela continuasse lendo o arquivo de forma comum, essa leitura travaria o laço de eventos, e todas as outras requisições ficariam paradas esperando — o `async` seria enfeite.

Por isso a leitura do manual é feita com `asyncio.to_thread`. Essa função joga o trabalho que trava para outra thread e devolve o controle ao laço de eventos enquanto isso. É o que permite ao programa cuidar de várias requisições ao mesmo tempo, que é o motivo dado no enunciado.

O `failure_error_function` também é `async def`. O SDK aceita as duas formas: o tipo que ele espera para essa função permite retorno assíncrono. Escrevi uma versão específica deste exercício porque agora existe um risco novo. Quando a consulta falha, o modelo ainda precisa devolver o objeto completo, inclusive o campo da lista de peças. Sem orientação, a tendência dele é preencher a lista com peças inventadas, para não deixar o campo vazio. Então a mensagem de erro, além de pedir a conferência do código no painel da máquina, diz explicitamente para não inventar peças e devolver a lista vazia.

Funcionou: no teste com o código inválido, a lista voltou com zero peças.

## 3. As duas perguntas ao mesmo tempo

Para mostrar que a ferramenta assíncrona serve para alguma coisa, as duas perguntas do enunciado, a do código válido e a do inválido, são disparadas juntas com `asyncio.gather`, no mesmo agente.

Cada pergunta imprime em que segundo começou e em que segundo terminou, contados do início do programa. Na execução registrada no print, as duas começaram em 0,0 segundo; a Pergunta B terminou em 5,8 segundos enquanto a Pergunta A ainda estava rodando; e a A terminou em 22,6 segundos.

É isso que prova a simultaneidade. Se as perguntas fossem feitas uma depois da outra, a segunda só poderia começar depois que a primeira terminasse, e nenhuma das duas mostraria começo em 0,0 segundo. O tempo total, 22,6 segundos, é o da pergunta mais demorada, e não a soma das duas.

Um detalhe que aparece no print e vale explicar: as linhas da ferramenta saem fora de ordem, a do XYZ-999 antes da do CMP-100. Isso é normal e é consequência da simultaneidade. Quem chega primeiro imprime primeiro, e a ordem depende de qual resposta o provedor devolveu antes, não da ordem em que eu escrevi as perguntas no código.

## 4. Justificativa da estrutura de dados

Esta é a parte que o enunciado pede por escrito.

**A escolha.** As peças são uma lista aninhada de objetos, e não campos separados no diagnóstico. A alternativa seria algo como `peca_1_nome`, `peca_1_quantidade`, `peca_1_prioridade`, `peca_2_nome`, e assim por diante.

**Por que a lista.** Os campos separados obrigam a decidir, na hora de escrever o modelo, quantas peças no máximo um diagnóstico pode ter. Essa decisão é um chute. Se eu reservar três e aparecer um defeito que exige quatro peças, a quarta se perde, e corrigir isso significa mexer no modelo, no agente e no painel de despacho ao mesmo tempo. Se eu reservar dez e o caso comum tiver duas, quase todo diagnóstico viaja com oito grupos de campos vazios, que o painel precisa aprender a ignorar.

Com a lista, a quantidade de peças deixa de ser parte da estrutura e passa a ser simplesmente um dado. Zero peça, duas peças ou sete peças são todas a mesma forma, e nada precisa ser alterado para acomodá-las.

**Por que objetos dentro da lista, e não textos soltos.** A lista poderia ser de frases, do tipo "2 unidades de junta de vedação, prioridade média". Seria mais fácil de gerar e péssimo de consumir: o painel teria que separar número, nome e urgência de dentro de uma frase, com todos os erros que isso costuma trazer. Mantendo três campos nomeados, cada informação chega pronta e no tipo certo.

**O que isso significa para quem consome o JSON no painel.** Três consequências práticas.

A primeira é que o painel percorre a lista em vez de ler campos com nome fixo. Um trecho que desenha uma linha por peça funciona igual para qualquer quantidade, e a lista vazia do caso de erro não vira exceção: percorrer zero item simplesmente não desenha nada. Por isso escolhi lista vazia em vez de campo nulo — campo nulo obrigaria o painel a verificar antes de usar, e essa verificação é exatamente o tipo de coisa que alguém esquece.

A segunda é que `quantidade` é número, e não texto. O painel consegue somar as peças de vários chamados para montar um pedido ao almoxarifado, ou ordenar por quantidade, sem converter nada antes.

A terceira é uma limitação que prefiro registrar a esconder. `prioridade` é texto livre, como o enunciado pede. Isso quer dizer que "alta", "Alta", "ALTA" e "urgentíssimo" passariam todas pela validação, e o painel que quiser pintar de vermelho as prioridades altas vai ter que lidar com isso. No manual eu uso sempre "alta", "media" e "baixa", em minúsculas e sem acento, e a descrição do campo repete esses três valores ao modelo, mas isso é uma combinação, não uma garantia. A forma de transformar em garantia seria declarar o campo com os três valores fixos, usando um tipo restrito do Pydantic, e aí qualquer outro texto seria recusado na validação. É o mesmo padrão dos exercícios anteriores: descrição em texto influencia, tipo declarado garante.

**Uma escolha menor.** A ordem da lista é a ordem em que as peças estão no manual, que coloca a peça principal primeiro. Isso não é uma promessa do formato. Se o painel quiser exibir sempre as de prioridade alta no topo, deve ordenar por conta própria, e não confiar na ordem em que os itens chegaram.

## 5. Evidências

*(inserir o print depois de tirá-lo)*

- Print – a execução completa: as duas perguntas disparadas juntas, com os tempos de começo e fim mostrando a sobreposição; a Pergunta A com as duas peças do manual e os tipos `PecaRecomendada` e `int`; a Pergunta B com o erro tratado e a lista de peças vazia: `prints/...`
