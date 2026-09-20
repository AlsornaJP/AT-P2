import asyncio
import os

from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

cliente_gemini = AsyncOpenAI(
    api_key=os.getenv("GEMINI_API_KEY"),
    base_url=os.getenv("GEMINI_BASE_URL"),
)

set_tracing_disabled(True)


def formatar_resposta(pergunta: str, resposta: str) -> None:
    """Monta um texto organizado com a pergunta e a resposta do agente."""
    print(f"Pergunta: {pergunta}")
    print(f"Resposta: {resposta}")



async def perguntar_ao_agente(pergunta: str) -> str:
    agente = Agent(
        name="Assistente de Equipamentos",
        instructions="Responda perguntas gerais sobre equipamentos industriais.",
        model=OpenAIChatCompletionsModel(
            model=os.getenv("GEMINI_MODEL"),
            openai_client=cliente_gemini,
        ),
    )

    resultado = await Runner.run(agente, pergunta)
    return resultado.final_output


async def main():
    pergunta = "Para que serve um compressor de ar em uma fábrica?"
    resposta = await perguntar_ao_agente(pergunta)
    formatar_resposta(pergunta, resposta)


if __name__ == "__main__":
    asyncio.run(main())
