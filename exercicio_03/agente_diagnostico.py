import asyncio
import os

from agents import Agent, OpenAIChatCompletionsModel, Runner, set_tracing_disabled
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel

load_dotenv()

set_tracing_disabled(True)

MENSAGEM_DE_SISTEMA = """
Você é um especialista em diagnóstico de equipamentos industriais da empresa Metalúrgica Andrade.
Seu papel é ajudar técnicos de manutenção a descobrir a causa de falhas em máquinas e indicar o que verificar.

Restrições de domínio:
- Responda somente perguntas sobre diagnóstico e manutenção de equipamentos industriais.
- Recuse perguntas administrativas, como férias, salário, ponto, benefícios ou escala de trabalho.
  Nesses casos, marque pergunta_aceita como falso, explique em uma frase que só trata de diagnóstico
  de equipamentos e deixe regras_aplicadas vazia.

Base de conhecimento - regras de segurança operacional da Metalúrgica Andrade:
- REGRA SEG-01: antes de abrir ou mexer em qualquer máquina, o técnico deve desligar a chave geral
  e colocar o cadeado LARANJA com a etiqueta com seu nome e matrícula.
- REGRA SEG-02: equipamentos que operam acima de 60 °C só podem ser tocados depois de 40 minutos
  desligados e após medir a temperatura com o termômetro infravermelho do setor.
- REGRA SEG-03: qualquer intervenção em painel elétrico exige dois técnicos no local,
  e pelo menos um deles precisa ter o crachá VERDE de habilitação elétrica.

Sempre que uma dessas regras valer para a situação descrita, cite a regra pelo código na resposta
e coloque o código em regras_aplicadas.
"""


class RespostaDiagnostico(BaseModel):
    pergunta_aceita: bool
    resposta: str
    regras_aplicadas: list[str]


def criar_agente() -> Agent:
    cliente_gemini = AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url=os.getenv("GEMINI_BASE_URL"),
    )
    return Agent(
        name="Especialista em Diagnóstico",
        instructions=MENSAGEM_DE_SISTEMA,
        output_type=RespostaDiagnostico,
        model=OpenAIChatCompletionsModel(
            model=os.getenv("GEMINI_MODEL"),
            openai_client=cliente_gemini,
        ),
    )


def mostrar(titulo: str, pergunta: str, saida: RespostaDiagnostico) -> None:
    print("=" * 60)
    print(titulo)
    print("=" * 60)
    print(f"Pergunta: {pergunta}")
    print(f"Pergunta aceita: {saida.pergunta_aceita}")
    print(f"Regras aplicadas: {saida.regras_aplicadas}")
    print(f"Resposta: {saida.resposta}")
    print()


def executar_sincrono() -> None:
    pergunta = (
        "O forno de tratamento térmico 2 parou de esquentar e o painel elétrico dele "
        "está com cheiro de queimado. Vou abrir o painel agora para ver. O que devo verificar?"
    )
    resultado = Runner.run_sync(criar_agente(), pergunta)
    mostrar("Execução com Runner.run_sync", pergunta, resultado.final_output)


async def executar_assincrono() -> None:
    pergunta = "Quantos dias de férias eu ainda tenho para tirar este ano?"
    resultado = await Runner.run(criar_agente(), pergunta)
    mostrar("Execução com Runner.run (assíncrono)", pergunta, resultado.final_output)


if __name__ == "__main__":
    executar_sincrono()
    asyncio.run(executar_assincrono())
