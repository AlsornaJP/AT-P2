import asyncio
import json
import os
from pathlib import Path

from agents import Agent, OpenAIChatCompletionsModel, Runner, function_tool, set_tracing_disabled
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

set_tracing_disabled(True)

CAMINHO_DO_MANUAL = Path(__file__).parent / "manuais.json"


@function_tool
def consultar_manual_equipamento(codigo_equipamento: str) -> str:
    """Consulta o manual técnico e devolve os dados de um equipamento.

    Args:
        codigo_equipamento: o código do equipamento, por exemplo CMP-100 ou TRN-300.

    Returns:
        O nome do equipamento e a lista de erros conhecidos, com causa provável e
        ação recomendada. Se o código não existir no manual, devolve um aviso.
    """
    print(f"[tool consultar_manual_equipamento] procurando o código {codigo_equipamento}")

    manual = json.loads(CAMINHO_DO_MANUAL.read_text(encoding="utf-8"))

    for equipamento in manual:
        if equipamento["codigo"].upper() == codigo_equipamento.upper():
            return json.dumps(equipamento, ensure_ascii=False)

    codigos = [equipamento["codigo"] for equipamento in manual]
    return f"Equipamento {codigo_equipamento} não encontrado no manual. Códigos disponíveis: {codigos}"


def criar_agente() -> Agent:
    cliente = AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url=os.getenv("GEMINI_BASE_URL"),
    )
    return Agent(
        name="Especialista em Diagnóstico",
        instructions=(
            "Você é um especialista em diagnóstico de equipamentos industriais da Metalúrgica Andrade. "
            "Antes de sugerir qualquer ação, consulte o manual do equipamento com a ferramenta "
            "consultar_manual_equipamento. Responda usando apenas o que estiver no manual e cite o "
            "código do erro, a causa provável e a ação recomendada."
        ),
        model=OpenAIChatCompletionsModel(
            model=os.getenv("GEMINI_MODEL"),
            openai_client=cliente,
        ),
        tools=[consultar_manual_equipamento],
    )


async def perguntar(pergunta: str) -> None:
    print("=" * 70)
    print(f"Pergunta: {pergunta}")
    print("=" * 70)
    resultado = await Runner.run(criar_agente(), pergunta)
    print(f"Resposta: {resultado.final_output}")
    print()


async def main() -> None:
    await perguntar("O torno CNC de código TRN-300 parou e mostrou o erro E-202 no painel. O que houve e o que eu faço?")
    await perguntar("A bomba BMB-210 está com o erro E-503. O que o manual diz?")


if __name__ == "__main__":
    asyncio.run(main())
