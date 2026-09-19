import asyncio
import os
import time
from dataclasses import dataclass

from agents import (
    Agent,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RunContextWrapper,
    Runner,
    function_tool,
    set_tracing_disabled,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

set_tracing_disabled(True)

INSTRUCAO_TRIAGEM = (
    "Você faz a triagem de chamados de manutenção industrial. "
    "Classifique o chamado como BAIXA, MEDIA ou ALTA prioridade e diga em uma frase o porquê."
)

INSTRUCAO_DIAGNOSTICO = (
    "Você é um especialista em diagnóstico de equipamentos industriais. "
    "Explique a causa mais provável da falha e liste o que o técnico deve verificar."
)

CHAMADO_SIMPLES = "A lâmpada do painel da esteira 4 queimou. A esteira continua funcionando normalmente."

FALHA_COMPLEXA = (
    "O compressor de parafuso da linha 2 está desarmando por alta temperatura depois de 40 minutos "
    "de operação. O nível de óleo está correto, o radiador foi limpo há uma semana e a temperatura "
    "ambiente é de 28 °C. A pressão de trabalho subiu de 7 para 8,5 bar no último mês."
)


@dataclass
class ContextoDaFilial:
    filial_id: str


def cliente_gemini() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url=os.getenv("GEMINI_BASE_URL"),
    )


def cliente_openrouter() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.getenv("OPENROUTER_API_KEY"),
        base_url=os.getenv("OPENROUTER_BASE_URL"),
    )


@function_tool
def consultar_filial(wrapper: RunContextWrapper[ContextoDaFilial]) -> str:
    """Informa de qual filial o técnico está chamando."""
    filial = wrapper.context.filial_id
    print(f"[tool consultar_filial] chamada pelo agente, filial do contexto: {filial}")
    return f"O chamado veio da filial {filial}."


async def pausa_para_o_limite_da_api() -> None:
    print("(pausa de 30 segundos para respeitar o limite de chamadas por minuto do plano gratuito)")
    print()
    await asyncio.sleep(30)


def titulo(texto: str) -> None:
    print("=" * 70)
    print(texto)
    print("=" * 70)


async def parte_1_dois_modelos() -> None:
    titulo("Parte 1 - mesma triagem em dois modelos diferentes")

    for nome_variavel in ("GEMINI_MODEL", "GEMINI_MODEL_AVANCADO"):
        modelo = os.getenv(nome_variavel)
        agente = Agent(
            name="Triagem",
            instructions=INSTRUCAO_TRIAGEM,
            model=OpenAIChatCompletionsModel(model=modelo, openai_client=cliente_gemini()),
        )

        inicio = time.time()
        resultado = await Runner.run(agente, CHAMADO_SIMPLES)
        duracao = time.time() - inicio
        uso = resultado.context_wrapper.usage

        print(f"Modelo: {modelo}")
        print(f"Tempo: {duracao:.2f} s | Tokens: {uso.total_tokens}")
        print(f"Resposta: {resultado.final_output}")
        print()


async def parte_2_provedor_alternativo() -> None:
    titulo("Parte 2 - triagem na filial que só tem contrato com o OpenRouter")

    modelo = os.getenv("OPENROUTER_MODEL")
    agente = Agent(
        name="Triagem",
        instructions=INSTRUCAO_TRIAGEM,
        model=OpenAIChatCompletionsModel(model=modelo, openai_client=cliente_openrouter()),
    )

    inicio = time.time()
    resultado = await Runner.run(agente, CHAMADO_SIMPLES)
    duracao = time.time() - inicio
    uso = resultado.context_wrapper.usage

    print(f"Provedor: OpenRouter | Modelo: {modelo}")
    print(f"Tempo: {duracao:.2f} s | Tokens: {uso.total_tokens}")
    print(f"Resposta: {resultado.final_output}")
    print()


def agente_de_diagnostico() -> Agent:
    return Agent(
        name="Diagnóstico Complexo",
        instructions=INSTRUCAO_DIAGNOSTICO + " Use a tool consultar_filial para saber de qual filial é o chamado e cite a filial na resposta.",
        model=OpenAIChatCompletionsModel(
            model=os.getenv("GEMINI_MODEL_AVANCADO"),
            openai_client=cliente_gemini(),
        ),
        model_settings=ModelSettings(
            temperature=0.2,
            max_tokens=600,
            include_usage=True,
            extra_args={"reasoning_effort": "none"},
        ),
        tools=[consultar_filial],
    )


async def parte_3_contexto_e_model_settings() -> None:
    titulo("Parte 3 - filial injetada pelo contexto e ModelSettings")

    agente = agente_de_diagnostico()
    print(f"temperature configurada: {agente.model_settings.temperature}")
    print(f"max_tokens configurado: {agente.model_settings.max_tokens}")

    contexto = ContextoDaFilial(filial_id="FIL-07")
    resultado = await Runner.run(agente, FALHA_COMPLEXA, context=contexto)
    uso = resultado.context_wrapper.usage

    print(f"Tokens gerados na resposta: {uso.output_tokens} (limite configurado: 600)")
    print(f"Resposta: {resultado.final_output}")
    print()


async def partes_4_e_5_streaming_e_metricas() -> dict:
    titulo("Partes 4 e 5 - streaming, uso de tokens e métricas")

    agente = agente_de_diagnostico()
    contexto = ContextoDaFilial(filial_id="FIL-07")

    inicio = time.time()
    execucao = Runner.run_streamed(agente, FALHA_COMPLEXA, context=contexto)

    async for evento in execucao.stream_events():
        if evento.type == "raw_response_event" and evento.data.type == "response.output_text.delta":
            print(evento.data.delta, end="", flush=True)
    print()

    duracao = time.time() - inicio
    uso = execucao.context_wrapper.usage

    metricas = {
        "task_id": "diagnostico-001",
        "status": "done",
        "tempo_total_segundos": round(duracao, 2),
        "total_tokens": uso.total_tokens,
    }

    print()
    print(f"Tokens de entrada: {uso.input_tokens} | Tokens de saída: {uso.output_tokens}")
    print(f"Métricas: {metricas}")
    return metricas


async def main() -> None:
    await parte_1_dois_modelos()
    await parte_2_provedor_alternativo()
    await pausa_para_o_limite_da_api()
    await parte_3_contexto_e_model_settings()
    await pausa_para_o_limite_da_api()
    await partes_4_e_5_streaming_e_metricas()


if __name__ == "__main__":
    asyncio.run(main())
