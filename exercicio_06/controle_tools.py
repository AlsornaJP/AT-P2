import asyncio
import json
import os
from datetime import datetime
from pathlib import Path

from agents import (
    Agent,
    ModelSettings,
    OpenAIChatCompletionsModel,
    Runner,
    function_tool,
    set_tracing_disabled,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

set_tracing_disabled(True)

PASTA = Path(__file__).parent
CAMINHO_DO_MANUAL = PASTA.parent / "exercicio_05" / "manuais.json"
CAMINHO_DO_HISTORICO = PASTA / "historico.json"

historico_de_execucao: list[dict] = []


def registrar(papel: str, conteudo: str) -> None:
    historico_de_execucao.append(
        {
            "role": papel,
            "content": conteudo,
            "timestamp": datetime.now().isoformat(timespec="seconds"),
        }
    )


def buscar_manual(codigo_equipamento: str) -> str:
    registrar("tool_call", f"consultar_manual_equipamento(codigo_equipamento='{codigo_equipamento}')")
    print(f"[tool consultar_manual_equipamento] código {codigo_equipamento}")

    manual = json.loads(CAMINHO_DO_MANUAL.read_text(encoding="utf-8"))
    for equipamento in manual:
        if equipamento["codigo"].upper() == codigo_equipamento.upper():
            saida = json.dumps(equipamento, ensure_ascii=False)
            registrar("tool_output", saida)
            return saida

    saida = f"Equipamento {codigo_equipamento} não encontrado no manual."
    registrar("tool_output", saida)
    return saida


def buscar_historico(codigo_equipamento: str) -> str:
    registrar("tool_call", f"consultar_historico_manutencao(codigo_equipamento='{codigo_equipamento}')")
    print(f"[tool consultar_historico_manutencao] código {codigo_equipamento}")

    historico = json.loads(CAMINHO_DO_HISTORICO.read_text(encoding="utf-8"))
    for equipamento in historico:
        if equipamento["codigo"].upper() == codigo_equipamento.upper():
            saida = json.dumps(equipamento, ensure_ascii=False)
            registrar("tool_output", saida)
            return saida

    saida = f"Equipamento {codigo_equipamento} não encontrado no histórico."
    registrar("tool_output", saida)
    return saida


manual_vaga = function_tool(
    buscar_manual,
    name_override="consultar_manual_equipamento",
    description_override="Consulta informações técnicas de um equipamento industrial pelo código.",
)

historico_vaga = function_tool(
    buscar_historico,
    name_override="consultar_historico_manutencao",
    description_override="Consulta informações de manutenção de um equipamento industrial pelo código.",
)

manual_clara = function_tool(
    buscar_manual,
    name_override="consultar_manual_equipamento",
    description_override=(
        "Consulta o MANUAL DE FÁBRICA do equipamento. Use somente para saber o significado de um "
        "código de erro do painel, a causa provável da falha e a ação recomendada. "
        "NÃO tem datas, nomes de técnicos nem serviços já executados."
    ),
)

historico_clara = function_tool(
    buscar_historico,
    name_override="consultar_historico_manutencao",
    description_override=(
        "Consulta o HISTÓRICO DE SERVIÇOS JÁ EXECUTADOS no equipamento. Use somente para saber o que "
        "foi feito no passado: datas das manutenções, serviço realizado, técnico responsável e horas "
        "paradas. NÃO explica códigos de erro nem causas de falha."
    ),
)


def criar_agente(tools: list, model_settings: ModelSettings | None = None, tool_use_behavior: str = "run_llm_again") -> Agent:
    cliente = AsyncOpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL"),
    )
    return Agent(
        name="Especialista em Diagnóstico",
        instructions=(
            "Você é um especialista em manutenção industrial da Metalúrgica Andrade. "
            "Use as ferramentas disponíveis para responder com dados reais."
        ),
        model=OpenAIChatCompletionsModel(
            model=os.getenv("OPENROUTER_MODEL"),
            openai_client=cliente,
        ),
        model_settings=model_settings or ModelSettings(),
        tools=tools,
        tool_use_behavior=tool_use_behavior,
    )


def titulo(texto: str) -> None:
    print("=" * 70)
    print(texto)
    print("=" * 70)


PERGUNTA_NEUTRA = "Preciso de informações sobre o compressor CMP-100."
PERGUNTA_DE_MANUAL = "O que significa o erro E-102 do compressor CMP-100?"
PERGUNTA_DE_HISTORICO = "Quantas horas o compressor CMP-100 ficou parado nas últimas manutenções?"


async def rodar_e_contar(rotulo: str, tools: list, pergunta: str) -> None:
    titulo(rotulo)
    print(f"Pergunta: {pergunta}")

    marca = len(historico_de_execucao)
    resultado = await Runner.run(criar_agente(tools), pergunta)
    chamadas_de_tool = [r for r in historico_de_execucao[marca:] if r["role"] == "tool_call"]

    print(f"Ferramentas chamadas: {len(chamadas_de_tool)}")
    print(f"Chamadas ao modelo: {resultado.context_wrapper.usage.requests}")
    print(f"Resposta: {resultado.final_output[:300]}")
    print()


async def parte_1_docstrings() -> None:
    await rodar_e_contar("Parte 1a - pergunta neutra, descrições vagas", [manual_vaga, historico_vaga], PERGUNTA_NEUTRA)
    await rodar_e_contar("Parte 1b - pergunta neutra, descrições reescritas", [manual_clara, historico_clara], PERGUNTA_NEUTRA)
    await rodar_e_contar("Parte 1c - pergunta do manual, descrições vagas", [manual_vaga, historico_vaga], PERGUNTA_DE_MANUAL)
    await rodar_e_contar("Parte 1d - pergunta do manual, descrições reescritas", [manual_clara, historico_clara], PERGUNTA_DE_MANUAL)
    await rodar_e_contar("Parte 1e - pergunta do histórico, descrições vagas", [manual_vaga, historico_vaga], PERGUNTA_DE_HISTORICO)
    await rodar_e_contar("Parte 1f - pergunta do histórico, descrições reescritas", [manual_clara, historico_clara], PERGUNTA_DE_HISTORICO)


async def parte_2_tool_choice_e_stop() -> None:
    pergunta = "O compressor CMP-100 apresentou o erro E-102. Me explique a situação desse equipamento."

    titulo("Parte 2a - tool_choice forçando a tool do histórico")
    agente = criar_agente(
        [manual_clara, historico_clara],
        model_settings=ModelSettings(tool_choice="consultar_historico_manutencao"),
    )
    resultado = await Runner.run(agente, pergunta)
    chamadas_com_texto_final = resultado.context_wrapper.usage.requests
    print(f"Chamadas ao modelo: {chamadas_com_texto_final}")
    print(f"Resposta: {resultado.final_output}")
    print()

    titulo("Parte 2b - stop_on_first_tool: encerra assim que a tool responde")
    agente = criar_agente(
        [manual_clara, historico_clara],
        model_settings=ModelSettings(tool_choice="consultar_historico_manutencao"),
        tool_use_behavior="stop_on_first_tool",
    )
    resultado = await Runner.run(agente, pergunta)
    chamadas_parando_na_tool = resultado.context_wrapper.usage.requests
    print(f"Chamadas ao modelo: {chamadas_parando_na_tool}")
    print(f"Resposta (saída crua da tool): {resultado.final_output[:200]}...")
    print()

    titulo("Parte 2c - comparação")
    print(f"Com resposta gerada pelo modelo: {chamadas_com_texto_final} chamadas")
    print(f"Com stop_on_first_tool:          {chamadas_parando_na_tool} chamada")
    print()


def parte_3_mostrar_historico() -> None:
    titulo("Parte 3 - histórico das invocações de ferramenta")
    print(f"Total de registros: {len(historico_de_execucao)}")
    for registro in historico_de_execucao:
        conteudo = registro["content"]
        if len(conteudo) > 90:
            conteudo = conteudo[:90] + "..."
        print(f"{registro['timestamp']} | {registro['role']:<12} | {conteudo}")
    print()


async def main() -> None:
    await parte_1_docstrings()
    await parte_2_tool_choice_e_stop()
    parte_3_mostrar_historico()


if __name__ == "__main__":
    asyncio.run(main())
