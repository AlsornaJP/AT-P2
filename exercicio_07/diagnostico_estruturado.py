import asyncio
import json
import os
from pathlib import Path
from typing import Any

from agents import (
    Agent,
    ModelSettings,
    OpenAIChatCompletionsModel,
    RunContextWrapper,
    Runner,
    SQLiteSession,
    function_tool,
    set_tracing_disabled,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

load_dotenv()

set_tracing_disabled(True)

CAMINHO_DO_MANUAL = Path(__file__).parent.parent / "exercicio_05" / "manuais.json"
CAMINHO_DA_SESSAO = Path(__file__).parent / "sessao.db"


class EquipamentoNaoEncontrado(Exception):
    """Erro lançado quando o código do equipamento não está no manual."""


class DiagnosticoEquipamento(BaseModel):
    codigo: str = Field(description="o código do equipamento, por exemplo CMP-100")
    causa_provavel: str = Field(description="a causa provável da falha, segundo o manual")
    acao_recomendada: str = Field(description="a ação que o técnico deve executar, segundo o manual")


def avisar_erro_ao_modelo(contexto: RunContextWrapper[Any], erro: Exception) -> str:
    print(f"[failure_error_function] a tool falhou: {erro}")
    return (
        f"A consulta ao manual falhou: {erro} "
        "Peça ao técnico que confira o código do equipamento no painel da máquina."
    )


@function_tool(failure_error_function=avisar_erro_ao_modelo)
def consultar_manual_equipamento(codigo_equipamento: str) -> str:
    """Consulta o manual de fábrica e devolve os dados de um equipamento.

    Args:
        codigo_equipamento: o código do equipamento, por exemplo CMP-100.

    Returns:
        O nome do equipamento e a lista de erros conhecidos, com causa provável
        e ação recomendada.

    Raises:
        EquipamentoNaoEncontrado: se o código não existir no manual.
    """
    print(f"[tool consultar_manual_equipamento] código {codigo_equipamento}")

    manual = json.loads(CAMINHO_DO_MANUAL.read_text(encoding="utf-8"))
    for equipamento in manual:
        if equipamento["codigo"].upper() == codigo_equipamento.upper():
            return json.dumps(equipamento, ensure_ascii=False)

    raise EquipamentoNaoEncontrado(f"o código {codigo_equipamento} não existe no manual.")


def criar_agente() -> Agent:
    cliente = AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url=os.getenv("GEMINI_BASE_URL"),
    )
    return Agent(
        name="Especialista em Diagnóstico",
        instructions=(
            "Você é um especialista em diagnóstico de equipamentos industriais da Metalúrgica Andrade. "
            "Consulte o manual com a ferramenta antes de responder e use apenas o que estiver nele. "
            "Se a informação já tiver aparecido antes nesta conversa, responda direto, sem chamar a "
            "ferramenta de novo. "
            "Se a consulta falhar, explique o problema no campo causa_provavel e diga o que fazer "
            "no campo acao_recomendada."
        ),
        model=OpenAIChatCompletionsModel(
            model=os.getenv("GEMINI_MODEL"),
            openai_client=cliente,
        ),
        output_type=DiagnosticoEquipamento,
        tools=[consultar_manual_equipamento],
    )


def titulo(texto: str) -> None:
    print("=" * 70)
    print(texto)
    print("=" * 70)


def mostrar(saida: DiagnosticoEquipamento) -> None:
    print(f"Tipo do objeto recebido: {type(saida).__name__}")
    print(f"  codigo.............: {saida.codigo}")
    print(f"  causa_provavel.....: {saida.causa_provavel}")
    print(f"  acao_recomendada...: {saida.acao_recomendada}")
    print()


async def parte_1_erro_seguro() -> None:
    titulo("Parte 1 - código de equipamento que não existe")
    pergunta = "O equipamento XYZ-999 apresentou o erro E-102. O que houve?"
    print(f"Pergunta: {pergunta}")

    resultado = await Runner.run(criar_agente(), pergunta)
    print("A execução não quebrou.")
    mostrar(resultado.final_output)


async def parte_2_saida_estruturada() -> None:
    titulo("Parte 2 - código válido e saída estruturada")
    pergunta = "O compressor CMP-100 apresentou o erro E-102. O que houve?"
    print(f"Pergunta: {pergunta}")

    resultado = await Runner.run(criar_agente(), pergunta)
    mostrar(resultado.final_output)


async def parte_3_sessao() -> None:
    titulo("Parte 3 - memória entre perguntas com SQLiteSession")

    if CAMINHO_DA_SESSAO.exists():
        CAMINHO_DA_SESSAO.unlink()

    sessao = SQLiteSession("chamado-001", str(CAMINHO_DA_SESSAO))

    agente = criar_agente()

    primeira = "O torno TRN-300 apresentou o erro E-201. Qual é a causa?"
    print(f"Pergunta 1 (o agente pode usar a ferramenta): {primeira}")
    resultado = await Runner.run(agente, primeira, session=sessao)
    mostrar(resultado.final_output)

    # A resposta já está no histórico, então a ferramenta não é mais necessária.
    # Pedir isso na instrução não basta: o modelo às vezes chama a ferramenta de
    # novo sem parar, e a execução estoura o limite de turnos. Com tool_choice
    # igual a "none" o mesmo agente fica proibido de chamar a ferramenta e
    # precisa responder com o que já está na memória.
    agente_so_com_memoria = agente.clone(model_settings=ModelSettings(tool_choice="none"))

    segunda = "E qual a ação recomendada mesmo?"
    print(f"Pergunta 2 (mesmo agente, com tool_choice=none): {segunda}")
    resultado = await Runner.run(agente_so_com_memoria, segunda, session=sessao)
    mostrar(resultado.final_output)

    itens = await sessao.get_items()
    print(f"Mensagens guardadas no arquivo {CAMINHO_DA_SESSAO.name}: {len(itens)}")
    print()


async def pausa() -> None:
    print("(pausa de 20 segundos para respeitar o limite de chamadas por minuto do plano gratuito)")
    print()
    await asyncio.sleep(20)


async def main() -> None:
    await parte_1_erro_seguro()
    await pausa()
    await parte_2_saida_estruturada()
    await pausa()
    await parte_3_sessao()


if __name__ == "__main__":
    asyncio.run(main())
