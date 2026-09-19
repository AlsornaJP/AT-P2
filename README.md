# AT-P2

## Como executar

1. Instale as dependências: `uv sync`
2. Copie o `.env.example` para `.env` e preencha a chave de API.
3. Execute o exercício desejado, por exemplo: `uv run exercicio_01/agente_equipamentos.py`

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
