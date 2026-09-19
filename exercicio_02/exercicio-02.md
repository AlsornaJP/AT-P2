# Exercício 2 – Protocolo de conversa do agente

## 1. O que é o protocolo de Chat Completions

Neste exercício não usei o SDK de Agents. Chamei a API direto, pelo método `chat.completions.create` da biblioteca `openai`. É isso que o SDK faz por baixo quando o agente conversa com o modelo.

A conversa é uma lista de mensagens. Cada mensagem tem um papel (`role`) e um texto (`content`):

- `system`: a instrução geral, que diz como o modelo deve se comportar. Aqui ela diz que ele é um assistente de manutenção industrial e deve responder em português, de forma clara e curta.
- `user`: o que o técnico pergunta.
- `assistant`: o que o modelo respondeu antes.

O modelo não guarda nada entre uma chamada e outra. Ele só "lembra" do que estiver na lista enviada naquela chamada.

O código está em `exercicio_02/conversa_chat.py`. Para executar: `uv run exercicio_02/conversa_chat.py`

## 2. Autenticação com python-dotenv

A chave fica no arquivo `.env`, fora do código, e o `.env` está no `.gitignore`. O programa chama `load_dotenv()`, que lê o arquivo e coloca as variáveis no ambiente. Depois, o `os.getenv` pega a chave (`OPENROUTER_API_KEY`), o endereço da API (`OPENROUTER_BASE_URL`) e o nome do modelo (`OPENROUTER_MODEL`). O `.env.example` mostra quais variáveis são necessárias, sem a chave de verdade.

### Por que OpenRouter e não Gemini

Primeiro tentei com o Gemini, o mesmo do exercício 1. As perguntas com `temperature`, `top_p` e `max_tokens` funcionaram, mas o Gemini recusou o `frequency_penalty` com o erro `Unknown name "frequency_penalty"`. Por isso mudei para o OpenRouter, que também usa o formato da OpenAI. Escolhi o modelo gratuito `deepseek/deepseek-v4-flash-0731:free`, que aceita os quatro parâmetros pedidos.

Esse modelo tem um "raciocínio interno": antes de responder, ele gasta tokens pensando. Nos testes, às vezes ele gastava todos os tokens pensando e a resposta vinha vazia. Por isso a chamada envia `extra_body={"reasoning": {"enabled": False}}`, que desliga esse raciocínio. Assim, o `max_tokens` conta só o texto da resposta e a comparação entre os parâmetros fica justa.

## 3. Conversa com histórico (multi-turno)

A função `conversa_com_historico` monta a lista assim:

1. `system` com a instrução geral.
2. `user`: "O compressor de ar da linha 3 está desligando sozinho depois de uns 20 minutos ligado."
3. `assistant`: a resposta do modelo, que eu adiciono na lista com `append`.
4. `user`: "E qual peça dele eu devo verificar primeiro?"
5. `assistant`: a segunda resposta, também adicionada na lista.

A segunda pergunta não diz qual é o equipamento, só "dele". Ela só faz sentido porque a lista inteira, com a primeira pergunta e a primeira resposta, é enviada de novo. Na execução, o modelo respondeu sobre o compressor: mandou verificar primeiro o filtro de ar e depois o nível de óleo, que ele mesmo tinha citado no primeiro turno, e ainda falou das aletas do cabeçote. No fim, o programa mostra que o histórico tem 5 mensagens.

## 4. Diagnóstico: variando temperature e top_p

A mesma pergunta de diagnóstico ("Um motor elétrico trifásico está vibrando muito e esquentando. Qual é a causa mais provável?") foi feita duas vezes:

- `temperature=0.1` e `top_p=0.3`: resposta direta e organizada. Apontou desequilíbrio de tensão ou corrente entre as fases como causa principal, listou outras causas (rolamentos, desalinhamento, rotor desbalanceado) e deu uma ação imediata (medir tensão e corrente nas três fases).
- `temperature=1.5` e `top_p=1.0`: a ideia principal foi parecida, mas o texto ficou menos confiável. Apareceram termos que não fazem sentido no contexto ("vibração por brush/output", "derretimento interno"), um conceito errado (chamar diferença de corrente entre fases de "surto") e emojis no meio da lista. Em um teste anterior com os mesmos valores, a resposta chegou a virar uma mistura de palavras sem sentido, com trechos em outros idiomas.

A `temperature` controla o quanto o modelo arrisca na escolha da próxima palavra. Com valor baixo, ele escolhe quase sempre a palavra mais provável. Com valor alto, palavras pouco prováveis passam a ter chance. O `top_p` limita de quantas palavras ele pode escolher: com 0.3, só entram as mais prováveis, que somam 30% da chance; com 1.0, entram todas.

## 5. Sugestões de manutenção: ajustando max_tokens e frequency_penalty

A pergunta "Liste 15 sugestões de manutenção preventiva para as bombas centrífugas de uma fábrica" tende a repetir palavras e estruturas, porque é uma lista longa sobre o mesmo assunto. Ela foi feita duas vezes:

- Sem ajuste: 15 itens completos, mas vários começam do mesmo jeito: três com "Verificação", dois com "Inspeção" e dois com "Limpeza".
- Com `temperature=0.9`, `max_tokens=400` e `frequency_penalty=0.8`: cada item começa com um nome curto e diferente ("Lubrificação", "Vibração", "Temperatura", "Vazão e pressão"...), sem repetir o mesmo verbo no início. Mas a resposta foi cortada no meio do item 14 ("Pressão de selagem: A"), porque chegou ao limite de 400 tokens.

O `frequency_penalty` diminui a chance de o modelo repetir palavras que já usou. Quanto mais vezes uma palavra aparece, maior a penalidade. O `max_tokens` é o tamanho máximo da resposta. Ele controla o custo e o tempo, mas se for pequeno demais corta o texto no meio, como aconteceu aqui.

## 6. Qual combinação usar em cada caso

**Diagnóstico técnico:** `temperature` baixa (0 a 0.3) e `top_p` baixo (0.3 a 0.5). No diagnóstico, quero a resposta mais provável e segura, sempre parecida para o mesmo problema. Criatividade aqui é risco: uma causa inventada pode levar o técnico a trocar a peça errada ou a trabalhar de forma insegura. O teste com `temperature=1.5` mostrou isso: a resposta trouxe termos sem sentido e um conceito errado. Não usei `frequency_penalty` aqui, porque em texto técnico repetir o termo certo (por exemplo, "fase" ou "rolamento") é bom.

**Sugestões abertas de manutenção preventiva:** `temperature` média (0.7 a 0.9), `top_p` alto (0.9 a 1.0) e `frequency_penalty` moderado (0.5 a 0.8). Aqui eu quero variedade de ideias, e as ideias diferentes aparecem com mais liberdade na escolha das palavras. A penalidade evita a lista repetitiva. O `max_tokens` deve ter folga para o tamanho pedido: 400 foi pouco para 15 itens. Para essa pergunta, algo em torno de 800 seria o adequado, ou então pedir menos itens.

## 7. Evidências

- Print 1 – Conversa com histórico (os dois turnos e o total de 5 mensagens) e as duas respostas de diagnóstico, com temperature 0.1/top_p 0.3 e com temperature 1.5/top_p 1.0: `prints/Screenshot_20260919_182708.png`
- Print 2 – Continuação da mesma execução: final do diagnóstico com temperature 1.5 e as sugestões de manutenção sem ajuste e com max_tokens, frequency_penalty e temperature, cortadas no item 14: `prints/Screenshot_20260919_182719.png`
