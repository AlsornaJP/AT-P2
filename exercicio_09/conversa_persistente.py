"""Exercício 9 - histórico de conversa na mão e sessão que sobrevive ao programa.

Rode duas vezes. O script percebe sozinho em qual execução está, olhando se a
sessão gravada em disco já tem mensagens.
"""

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
    TResponseInputItem,
    function_tool,
    set_tracing_disabled,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

set_tracing_disabled(True)

CAMINHO_DO_MANUAL = Path(__file__).parent.parent / "exercicio_08" / "manuais_com_pecas.json"
CAMINHO_DA_SESSAO = Path(__file__).parent / "sessao_tecnico.db"


class EquipamentoNaoEncontrado(Exception):
    """Erro lançado quando o código do equipamento não está no manual."""


async def avisar_erro_ao_modelo(contexto: RunContextWrapper[Any], erro: Exception) -> str:
    print(f"[failure_error_function] a tool falhou: {erro}")
    return (
        f"A consulta ao manual falhou: {erro} "
        "Peça ao técnico que confira o código do equipamento no painel da máquina."
    )


@function_tool(failure_error_function=avisar_erro_ao_modelo)
async def consultar_manual_equipamento(codigo_equipamento: str) -> str:
    """Consulta o manual de fábrica e devolve os dados de um equipamento.

    Args:
        codigo_equipamento: o código do equipamento, por exemplo EST-450.

    Returns:
        O nome do equipamento e a lista de erros conhecidos, cada um com causa
        provável, ação recomendada e as peças de reposição indicadas.

    Raises:
        EquipamentoNaoEncontrado: se o código não existir no manual.
    """
    print(f"[tool consultar_manual_equipamento] código {codigo_equipamento}")

    texto = await asyncio.to_thread(CAMINHO_DO_MANUAL.read_text, encoding="utf-8")
    manual = json.loads(texto)

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
            "Responda em no máximo três frases curtas, em português. "
            "Se a informação já tiver aparecido antes nesta conversa, responda direto, sem chamar a "
            "ferramenta de novo."
        ),
        model=OpenAIChatCompletionsModel(
            model=os.getenv("GEMINI_MODEL"),
            openai_client=cliente,
        ),
        tools=[consultar_manual_equipamento],
    )


def titulo(texto: str) -> None:
    print("=" * 70)
    print(texto)
    print("=" * 70)


async def pausa() -> None:
    print("(pausa de 20 segundos para respeitar o limite de chamadas por minuto)")
    print()
    await asyncio.sleep(20)


async def parte_1_historico_na_mao(agente: Agent) -> None:
    titulo("Parte 1 - histórico na mão, com uma lista de TResponseInputItem")

    perguntas = [
        "A esteira EST-450 apresentou o erro E-302. Qual é a causa provável?",
        "E quais peças eu levo para resolver?",
        "Qual é a prioridade da primeira dessas peças?",
    ]

    # A lista começa vazia. Eu mesmo carrego a conversa de uma rodada para a outra.
    historico: list[TResponseInputItem] = []

    for numero, pergunta in enumerate(perguntas, start=1):
        entrada = historico + [{"role": "user", "content": pergunta}]
        print(f"Pergunta {numero}: {pergunta}")
        print(f"  itens enviados ao modelo: {len(entrada)}")

        resultado = await Runner.run(agente, entrada)
        print(f"  Resposta: {resultado.final_output}")

        # to_input_list devolve tudo o que foi enviado mais o que voltou, já no
        # formato de entrada. É isso que vira o histórico da próxima rodada.
        historico = resultado.to_input_list()
        print(f"  itens na lista depois da resposta: {len(historico)}")
        print()

        if numero < len(perguntas):
            await pausa()

    print(f"No fim das três rodadas a lista tem {len(historico)} itens.")
    print("Essa lista está só na memória deste processo: quando o programa fechar, ela some.")
    print()


async def parte_2_primeira_execucao(agente: Agent, sessao: SQLiteSession) -> None:
    titulo("Parte 2 - primeira execução: gravando a sessão em disco")

    pergunta = "O forno FRN-720 apresentou o erro E-401. Qual é a causa e o que devo levar?"
    print(f"Pergunta do técnico: {pergunta}")

    resultado = await Runner.run(agente, pergunta, session=sessao)
    print(f"Resposta: {resultado.final_output}")
    print()

    itens = await sessao.get_items()
    print(f"Mensagens gravadas em {CAMINHO_DA_SESSAO.name}: {len(itens)}")
    print(f"Tamanho do arquivo em disco: {CAMINHO_DA_SESSAO.stat().st_size} bytes")
    print()
    print("Agora feche e rode o programa de novo, com o mesmo comando.")
    print("O técnico vai voltar amanhã e não vai repetir o contexto.")


async def parte_2_segunda_execucao(agente: Agent, sessao: SQLiteSession) -> None:
    titulo("Parte 2 - segunda execução: processo novo, lendo a sessão do disco")

    itens_antes = await sessao.get_items()
    print("Este processo começou sem nada na memória.")
    print(f"Mensagens encontradas em {CAMINHO_DA_SESSAO.name}: {len(itens_antes)}")
    print()

    pergunta = "Qual era mesmo a ação recomendada para aquele erro?"
    print(f"Pergunta de acompanhamento: {pergunta}")
    print("(não diz o equipamento nem o código do erro)")
    print()

    # Proibir a ferramenta faz a resposta só poder vir do que estava no arquivo.
    agente_so_com_memoria = agente.clone(model_settings=ModelSettings(tool_choice="none"))
    resultado = await Runner.run(agente_so_com_memoria, pergunta, session=sessao)
    print(f"Resposta: {resultado.final_output}")
    print()

    itens = await sessao.get_items()
    print(f"Mensagens gravadas agora em {CAMINHO_DA_SESSAO.name}: {len(itens)}")


async def main() -> None:
    sessao = SQLiteSession("tecnico-joao", str(CAMINHO_DA_SESSAO))
    itens_existentes = await sessao.get_items()
    primeira_vez = len(itens_existentes) == 0

    print(f"Arquivo de sessão: {CAMINHO_DA_SESSAO}")
    print(f"Mensagens já gravadas nele: {len(itens_existentes)}")
    if primeira_vez:
        print("Nenhuma mensagem encontrada, então esta é a PRIMEIRA execução.")
    else:
        print("Já existem mensagens, então esta é a SEGUNDA execução.")
    print()

    agente = criar_agente()

    if primeira_vez:
        await parte_1_historico_na_mao(agente)
        await pausa()
        await parte_2_primeira_execucao(agente, sessao)
    else:
        await parte_2_segunda_execucao(agente, sessao)


if __name__ == "__main__":
    asyncio.run(main())
