# AT-P2

## Vídeo de apresentação

https://youtu.be/wVWASWHSNAA

O vídeo explica as decisões de três exercícios: a estrutura de dados aninhada do exercício 8, a
estratégia de memória do exercício 11 e o tratamento de `task_id` inexistente do exercício 14.

## Como executar

1. Instale as dependências: `uv sync`
2. Copie o `.env.example` para `.env` e preencha a chave de API.
3. Execute o exercício desejado, sempre a partir da raiz do projeto, por exemplo: `uv run exercicio_01/agente_equipamentos.py`

O markdown de cada exercício começa dizendo qual arquivo executar.

### Exercícios que sobem um serviço

Os exercícios 12, 13 e 14 são serviços HTTP e precisam de **dois terminais**: um para o serviço e outro para o cliente de teste. Cada um usa uma porta diferente, então podem ficar ligados ao mesmo tempo.

| Exercício | Serviço | Cliente de teste | Porta |
|---|---|---|---|
| 12 | `uv run exercicio_12/servico.py` | `uv run exercicio_12/pedir_diagnostico.py` | 8000 |
| 13 | `uv run exercicio_13/servico_tarefas.py` | `uv run exercicio_13/acompanhar_tarefa.py` | 8001 |
| 14 | `uv run exercicio_14/servico_completo.py` | `uv run exercicio_14/cliente_despacho.py` | 8002 |

### O projeto é um só

Os exercícios reaproveitam uns aos outros, como o enunciado pede em vários pontos. Uns leem os manuais gerados antes; os últimos importam o código do agente em vez de copiá-lo:

- 6 e 7 leem o manual do exercício 5
- 9 lê o manual do exercício 8
- 11 lê o manual longo do exercício 10
- 12 e 13 importam o agente do exercício 11
- 14 importa os modelos do exercício 8 e o agente do exercício 11

Por isso o projeto precisa ser executado inteiro, a partir da raiz. Separar uma pasta de exercício não funciona.

### Tempo de execução

As respostas dependem da API do Gemini no plano gratuito, então os tempos variam bastante entre execuções. O exercício 11 é o mais demorado, porque roda os mesmos cenários em nove configurações. Alguns programas têm pausas propositais entre as chamadas, para respeitar o limite de requisições por minuto.

## Uso de ferramentas de IA

Todas as respostas geradas com apoio de IA foram revisadas e validadas por mim.

| Exercício | Parte | Agente | Modelo |
|---|---|---|---|
| 1 | Configuração do ambiente com uv, código do agente e texto discursivo | Claude Code | Claude Opus 5 |
| 1 | Parte do corpo da função `formatar_resposta` (linha que mostra a resposta) | Antigravity (Tab Completion) | Gemini 3.6 Flash |
| 2 | Código da conversa multi-turno e dos testes de parâmetros, texto discursivo | Claude Code | Claude Opus 5 |
| 3 | Código do agente de diagnóstico, system message com regras de segurança, texto discursivo | Claude Code | Claude Opus 5 |
| 4 | Código de seleção de modelos, streaming, métricas e texto discursivo | Claude Code | Claude Opus 5 |
| 5 | Gerador do manual em JSON, ferramenta consultar_manual_equipamento e texto discursivo | Claude Code | Claude Opus 5 |
| 6 | Segunda ferramenta, controle de tool_choice/stop_on_first_tool, histórico e texto discursivo | Claude Code | Claude Opus 5 |
| 7 | Tratamento de erro da ferramenta, saída estruturada com Pydantic, sessão SQLite e texto discursivo | Claude Code | Claude Opus 5 |
| 8 | Manual com peças, modelos Pydantic aninhados, ferramenta assíncrona com tratamento de erro próprio e texto discursivo | Claude Code | Claude Opus 5 |
| 9 | Histórico com lista de TResponseInputItem, sessão SQLite persistente entre execuções e texto discursivo | Claude Code | Claude Opus 5 |
| 10 | Manual longo, segmentação com sobreposição, embeddings e busca semântica integrados ao SDK, e texto discursivo | Claude Code | Claude Opus 5 |
| 11 | Agente com sessão e RAG juntos, experimento desligando cada metade, diagnóstico da busca e avaliação de estratégia | Claude Code | Claude Opus 5 |
| 12 | Serviço FastAPI com modelos Pydantic de entrada e saída, BackgroundTasks e cliente de teste, e texto discursivo | Claude Code | Claude Opus 5 |
| 13 | Endpoints POST /agent/run e GET /agent/status/{task_id}, registro de tarefas com pending/done/error e texto discursivo | Claude Code | Claude Opus 5 |
| 14 | Serviço REST completo com os três endpoints, agente integrador com as duas fontes, tratamento de task_id inexistente e texto discursivo | Claude Code | Claude Opus 5 |
