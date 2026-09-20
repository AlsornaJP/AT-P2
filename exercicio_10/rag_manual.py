"""Exercício 10 - RAG sobre um manual técnico longo.

O caminho é: quebrar o manual em trechos, transformar cada trecho em vetor,
transformar a pergunta em vetor, achar os trechos mais parecidos e entregar só
eles ao agente.
"""

import asyncio
import math
import os
from pathlib import Path

from agents import (
    Agent,
    OpenAIChatCompletionsModel,
    Runner,
    function_tool,
    set_tracing_disabled,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

set_tracing_disabled(True)

CAMINHO_DO_MANUAL = Path(__file__).parent / "manual_longo.txt"
MODELO_DE_EMBEDDING = "gemini-embedding-001"
DIMENSOES = 768
LIMITE_DO_TRECHO = 600
QUANTOS_TRECHOS_BUSCAR = 3

# Preenchidos uma vez, antes de o agente rodar.
TRECHOS: list[dict] = []
VETORES: list[list[float]] = []


def cliente_openai() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url=os.getenv("GEMINI_BASE_URL"),
    )


def ler_paragrafos() -> list[str]:
    texto = CAMINHO_DO_MANUAL.read_text(encoding="utf-8")
    return [p.strip() for p in texto.split("\n\n") if p.strip()]


def montar_trechos(paragrafos: list[str]) -> list[dict]:
    """Junta parágrafos até o trecho chegar ao limite de caracteres.

    O trecho seguinte começa repetindo o último parágrafo do anterior. Essa
    repetição é a sobreposição: serve para uma informação que caia na fronteira
    entre dois trechos não ficar cortada ao meio.
    """
    trechos = []
    inicio = 0

    while inicio < len(paragrafos):
        fim = inicio
        tamanho = 0

        while fim < len(paragrafos) and tamanho + len(paragrafos[fim]) <= LIMITE_DO_TRECHO:
            tamanho += len(paragrafos[fim])
            fim += 1

        # Garante pelo menos um parágrafo, mesmo que ele sozinho passe do limite.
        if fim == inicio:
            fim = inicio + 1

        trechos.append(
            {
                "numero": len(trechos) + 1,
                "texto": "\n\n".join(paragrafos[inicio:fim]),
                "primeiro_paragrafo": inicio + 1,
                "ultimo_paragrafo": fim,
            }
        )

        if fim >= len(paragrafos):
            break

        # Volta um parágrafo: é a sobreposição.
        inicio = fim - 1

    return trechos


async def gerar_vetores(textos: list[str]) -> list[list[float]]:
    cliente = cliente_openai()
    resposta = await cliente.embeddings.create(
        model=MODELO_DE_EMBEDDING,
        input=textos,
        dimensions=DIMENSOES,
    )
    return [item.embedding for item in resposta.data]


def similaridade(a: list[float], b: list[float]) -> float:
    """Similaridade de cosseno: quanto dois vetores apontam para o mesmo lado.

    Vai de -1 a 1. Quanto mais perto de 1, mais parecido é o sentido dos textos.
    """
    produto = sum(x * y for x, y in zip(a, b))
    tamanho_a = math.sqrt(sum(x * x for x in a))
    tamanho_b = math.sqrt(sum(y * y for y in b))
    return produto / (tamanho_a * tamanho_b)


async def ranquear(pergunta: str) -> list:
    """Põe todos os trechos em ordem de parecença com a pergunta."""
    vetor_da_pergunta = (await gerar_vetores([pergunta]))[0]
    notas = [
        (similaridade(vetor_da_pergunta, vetor), trecho)
        for vetor, trecho in zip(VETORES, TRECHOS)
    ]
    notas.sort(key=lambda par: par[0], reverse=True)
    return notas


def mostrar_ranking(notas: list, prefixo: str = "") -> None:
    for posicao, (nota, trecho) in enumerate(notas[:5], start=1):
        marca = "  <== escolhido" if posicao <= QUANTOS_TRECHOS_BUSCAR else ""
        faixa = f"parágrafos {trecho['primeiro_paragrafo']} a {trecho['ultimo_paragrafo']}"
        print(f"{prefixo}    {posicao}º  trecho {trecho['numero']:>2} ({faixa}): {nota:.4f}{marca}")


PALAVRAS_SEM_VALOR = {
    "com", "que", "eu", "devo", "os", "do", "da", "de", "a", "o", "no", "na", "um", "uma", "e",
}


def buscar_por_palavra_chave(pergunta: str) -> list:
    """Busca simples: conta quantas palavras da pergunta aparecem em cada trecho."""
    palavras = {
        p.strip("?.,").lower()
        for p in pergunta.split()
        if p.strip("?.,").lower() not in PALAVRAS_SEM_VALOR
    }
    achados = []
    for trecho in TRECHOS:
        texto = trecho["texto"].lower()
        encontradas = sorted(p for p in palavras if p in texto)
        achados.append((len(encontradas), encontradas, trecho))
    achados.sort(key=lambda t: t[0], reverse=True)
    return palavras, achados


@function_tool
async def buscar_no_manual(pergunta: str) -> str:
    """Busca no manual técnico os trechos que respondem a uma pergunta.

    Args:
        pergunta: a dúvida do técnico, escrita com as palavras dele.

    Returns:
        Os trechos do manual mais parecidos com a pergunta, em ordem.
    """
    print(f"[tool buscar_no_manual] pergunta recebida: {pergunta}")

    notas = await ranquear(pergunta)

    print("[tool buscar_no_manual] ranking dos trechos por similaridade:")
    mostrar_ranking(notas, prefixo="")

    escolhidos = notas[:QUANTOS_TRECHOS_BUSCAR]
    return "\n\n---\n\n".join(
        f"[trecho {trecho['numero']}]\n{trecho['texto']}" for _, trecho in escolhidos
    )


def criar_agente() -> Agent:
    return Agent(
        name="Especialista no Manual",
        instructions=(
            "Você é um especialista no manual técnico do compressor CMP-100. "
            "Use a ferramenta de busca para achar os trechos do manual e responda apenas com o "
            "que estiver neles. "
            "Cite o número do trecho de onde tirou a resposta. "
            "Se a informação não estiver nos trechos, diga que não encontrou no manual."
        ),
        model=OpenAIChatCompletionsModel(
            model=os.getenv("GEMINI_MODEL"),
            openai_client=cliente_openai(),
        ),
        tools=[buscar_no_manual],
    )


def titulo(texto: str) -> None:
    print("=" * 70)
    print(texto)
    print("=" * 70)


async def preparar() -> None:
    titulo("Parte 1 - segmentação do manual em trechos")

    paragrafos = ler_paragrafos()
    print(f"Parágrafos lidos de {CAMINHO_DO_MANUAL.name}: {len(paragrafos)}")
    print(f"Limite de tamanho por trecho: {LIMITE_DO_TRECHO} caracteres")
    print("Sobreposição: cada trecho recomeça no último parágrafo do trecho anterior.")
    print()

    TRECHOS.extend(montar_trechos(paragrafos))

    for trecho in TRECHOS:
        faixa = f"parágrafos {trecho['primeiro_paragrafo']} a {trecho['ultimo_paragrafo']}"
        print(f"  trecho {trecho['numero']:>2}: {len(trecho['texto']):>3} caracteres, {faixa}")

    print()
    print(f"Total de trechos: {len(TRECHOS)}")

    onde = [t["numero"] for t in TRECHOS if "quarenta e cinco" in t["texto"]]
    print(f"O torque do cabeçote (o dado procurado) está no(s) trecho(s): {onde}")
    print()

    titulo("Parte 2 - transformando os trechos em vetores")
    print(f"Modelo de embedding: {MODELO_DE_EMBEDDING}")
    VETORES.extend(await gerar_vetores([t["texto"] for t in TRECHOS]))
    print(f"Vetores gerados: {len(VETORES)}, com {len(VETORES[0])} dimensões cada.")
    print("Foi uma única chamada ao provedor, com todos os trechos juntos.")
    print()


PERGUNTA_DO_TECNICO = "Com que força eu devo apertar os parafusos da tampa superior do compressor?"


async def parte_3_busca_isolada() -> None:
    titulo("Parte 3 - a busca sozinha, sem o agente")

    print(f"Pergunta, com as palavras do técnico: {PERGUNTA_DO_TECNICO}")
    print()
    print("O manual não usa nenhuma dessas palavras para o dado procurado: ele fala")
    print("em 'torque de aperto dos parafusos do cabeçote'. Aqui a pergunta vai direto")
    print("para a busca, sem passar pelo modelo, para o resultado ser só dela.")
    print()

    palavras, achados = buscar_por_palavra_chave(PERGUNTA_DO_TECNICO)
    melhor_quantidade, melhor_lista, melhor_trecho = achados[0]
    print("Busca por palavra-chave (a maneira simples):")
    print(f"  palavras procuradas: {sorted(palavras)}")
    print(f"  melhor trecho por contagem: trecho {melhor_trecho['numero']}, "
          f"com {melhor_quantidade} palavra(s): {melhor_lista}")
    achou_certo = any(
        "quarenta e cinco" in trecho["texto"] for _, _, trecho in achados[:QUANTOS_TRECHOS_BUSCAR]
    )
    print(f"  o trecho com o torque do cabeçote entrou nos 3 primeiros? {'sim' if achou_certo else 'NÃO'}")
    print()

    print("Busca semântica (com embeddings):")
    notas = await ranquear(PERGUNTA_DO_TECNICO)
    mostrar_ranking(notas)
    primeiro = notas[0][1]
    print(f"  o primeiro colocado contém o torque do cabeçote? "
          f"{'sim' if 'quarenta e cinco' in primeiro['texto'] else 'NÃO'}")
    print()


async def parte_4_agente() -> None:
    titulo("Parte 4 - o agente respondendo com os trechos recuperados")

    print(f"Pergunta do técnico: {PERGUNTA_DO_TECNICO}")
    print()

    resultado = await Runner.run(criar_agente(), PERGUNTA_DO_TECNICO)
    print()
    print(f"Resposta do agente: {resultado.final_output}")


async def main() -> None:
    await preparar()
    await parte_3_busca_isolada()
    await parte_4_agente()


if __name__ == "__main__":
    asyncio.run(main())
