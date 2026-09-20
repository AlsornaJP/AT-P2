import asyncio
import json
import os
import time
from pathlib import Path
from typing import Any

from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    RunContextWrapper,
    Runner,
    function_tool,
    set_tracing_disabled,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

load_dotenv()

set_tracing_disabled(True)

CAMINHO_DO_MANUAL = Path(__file__).parent / "manuais_com_pecas.json"


class EquipamentoNaoEncontrado(Exception):
    """Erro lançado quando o código do equipamento não está no manual."""


class PecaRecomendada(BaseModel):
    nome: str = Field(description="o nome da peça, como está escrito no manual")
    quantidade: int = Field(description="quantas unidades dessa peça o técnico deve levar")
    prioridade: str = Field(description="a urgência da troca: alta, media ou baixa")


class DiagnosticoEquipamento(BaseModel):
    codigo: str = Field(description="o código do equipamento, por exemplo CMP-100")
    causa_provavel: str = Field(description="a causa provável da falha, segundo o manual")
    acao_recomendada: str = Field(description="a ação que o técnico deve executar, segundo o manual")
    pecas_recomendadas: list[PecaRecomendada] = Field(
        description=(
            "a lista de peças de reposição do manual para esse erro. "
            "Deve ficar vazia se o equipamento não for encontrado."
        )
    )


async def avisar_erro_ao_modelo(contexto: RunContextWrapper[Any], erro: Exception) -> str:
    print(f"[failure_error_function] a tool falhou: {erro}")
    return (
        f"A consulta ao manual falhou: {erro} "
        "Peça ao técnico que confira o código do equipamento no painel da máquina. "
        "Não invente peças de reposição: devolva a lista de peças vazia."
    )


@function_tool(failure_error_function=avisar_erro_ao_modelo)
async def consultar_manual_equipamento(codigo_equipamento: str) -> str:
    """Consulta o manual de fábrica e devolve os dados de um equipamento.

    Args:
        codigo_equipamento: o código do equipamento, por exemplo CMP-100.

    Returns:
        O nome do equipamento e a lista de erros conhecidos, cada um com causa
        provável, ação recomendada e as peças de reposição indicadas.

    Raises:
        EquipamentoNaoEncontrado: se o código não existir no manual.
    """
    print(f"[tool consultar_manual_equipamento] início da consulta a {codigo_equipamento}")

    # Ler arquivo trava a thread. Dentro de to_thread, a leitura sai do laço de
    # eventos e as outras requisições continuam andando enquanto esta espera.
    texto = await asyncio.to_thread(CAMINHO_DO_MANUAL.read_text, encoding="utf-8")
    manual = json.loads(texto)

    for equipamento in manual:
        if equipamento["codigo"].upper() == codigo_equipamento.upper():
            print(f"[tool consultar_manual_equipamento] fim da consulta a {codigo_equipamento}")
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
            "Preencha a lista de peças recomendadas com as peças que o manual indica para aquele erro, "
            "copiando nome, quantidade e prioridade como estão. "
            "Se a consulta falhar, explique o problema no campo causa_provavel, diga o que fazer no "
            "campo acao_recomendada e deixe a lista de peças vazia."
        ),
        model=OpenAIChatCompletionsModel(
            model=os.getenv("GEMINI_MODEL"),
            openai_client=cliente,
        ),
        output_type=DiagnosticoEquipamento,
        tools=[consultar_manual_equipamento],
    )


def mostrar(titulo: str, saida: DiagnosticoEquipamento) -> None:
    print("=" * 70)
    print(titulo)
    print("=" * 70)
    print(f"Tipo do objeto recebido: {type(saida).__name__}")
    print(f"  codigo.............: {saida.codigo}")
    print(f"  causa_provavel.....: {saida.causa_provavel}")
    print(f"  acao_recomendada...: {saida.acao_recomendada}")
    print(f"  pecas_recomendadas.: {len(saida.pecas_recomendadas)} peça(s)")

    for numero, peca in enumerate(saida.pecas_recomendadas, start=1):
        print(f"    peça {numero}: tipo {type(peca).__name__}")
        print(f"      nome......: {peca.nome}")
        print(f"      quantidade: {peca.quantidade} (tipo {type(peca.quantidade).__name__})")
        print(f"      prioridade: {peca.prioridade}")
    print()


async def perguntar(agente: Agent, rotulo: str, pergunta: str, inicio: float):
    """Roda uma pergunta e marca em que segundo ela começou e terminou."""
    print(f"[{rotulo}] começou em {time.perf_counter() - inicio:.1f}s")
    resultado = await Runner.run(agente, pergunta)
    print(f"[{rotulo}] terminou em {time.perf_counter() - inicio:.1f}s")
    return resultado


async def main() -> None:
    agente = criar_agente()

    valida = "O compressor CMP-100 apresentou o erro E-102. O que houve e o que devo levar?"
    invalida = "O equipamento XYZ-999 apresentou o erro E-102. O que houve e o que devo levar?"

    print("As duas perguntas são enviadas ao mesmo tempo, com asyncio.gather.")
    print(f"Pergunta A (código válido).: {valida}")
    print(f"Pergunta B (código inválido): {invalida}")
    print()

    inicio = time.perf_counter()
    resposta_valida, resposta_invalida = await asyncio.gather(
        perguntar(agente, "Pergunta A", valida, inicio),
        perguntar(agente, "Pergunta B", invalida, inicio),
    )
    duracao = time.perf_counter() - inicio
    print()

    mostrar("Pergunta A - código válido (CMP-100)", resposta_valida.final_output)
    mostrar("Pergunta B - código inválido (XYZ-999)", resposta_invalida.final_output)

    print(f"As duas execuções juntas levaram {duracao:.1f} segundos.")
    print("As duas começaram perto de 0s e correram juntas: se fossem uma depois da")
    print("outra, a segunda só começaria quando a primeira terminasse.")
    print("A execução não quebrou, mesmo com o código inválido.")


if __name__ == "__main__":
    asyncio.run(main())
