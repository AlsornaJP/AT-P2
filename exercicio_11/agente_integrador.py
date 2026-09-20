"""Exercício 11 - agente com memória de conversa e busca semântica, e a medição de
quando cada uma das duas é necessária.

O experimento: os mesmos cenários rodam com metade da memória desligada, para dar
de ver o que quebra em cada caso.
"""

import asyncio
import math
import os
import unicodedata
from pathlib import Path

from agents import (
    Agent,
    ModelBehaviorError,
    OpenAIChatCompletionsModel,
    Runner,
    SQLiteSession,
    function_tool,
    set_tracing_disabled,
)
from dotenv import load_dotenv
from openai import AsyncOpenAI

load_dotenv()

set_tracing_disabled(True)

CAMINHO_DO_MANUAL = Path(__file__).parent.parent / "exercicio_10" / "manual_longo.txt"
PASTA_DAS_SESSOES = Path(__file__).parent / "sessoes"
MODELO_DE_EMBEDDING = "gemini-embedding-001"
DIMENSOES = 768
LIMITE_DO_TRECHO = 600

# Quantos trechos a busca devolve. O valor natural seria 3, mas a medição da
# seção do diagnóstico mostrou que, quando o agente reescreve a pergunta puxando
# o assunto da conversa, o trecho certo pode cair para 4º lugar. Com 5 ele entra.
QUANTOS_TRECHOS_BUSCAR = 5
JANELA_ESTREITA = 3
SEGUNDOS_DE_PAUSA = 10

TRECHOS: list[dict] = []
VETORES: list[list[float]] = []
CHAMADAS_DA_BUSCA = 0
JANELA_DA_BUSCA = QUANTOS_TRECHOS_BUSCAR


def cliente_openai() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"),
        base_url=os.getenv("GEMINI_BASE_URL"),
    )


# ---------------------------------------------------------------- busca semântica
# Mesma receita do Exercício 10: segmentar com sobreposição, virar vetor, comparar.


def montar_trechos(paragrafos: list[str]) -> list[dict]:
    trechos = []
    inicio = 0

    while inicio < len(paragrafos):
        fim = inicio
        tamanho = 0

        while fim < len(paragrafos) and tamanho + len(paragrafos[fim]) <= LIMITE_DO_TRECHO:
            tamanho += len(paragrafos[fim])
            fim += 1

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

        inicio = fim - 1

    return trechos


async def gerar_vetores(textos: list[str]) -> list[list[float]]:
    cliente = cliente_openai()
    resposta = await cliente.embeddings.create(
        model=MODELO_DE_EMBEDDING, input=textos, dimensions=DIMENSOES
    )
    return [item.embedding for item in resposta.data]


def similaridade(a: list[float], b: list[float]) -> float:
    produto = sum(x * y for x, y in zip(a, b))
    return produto / (math.sqrt(sum(x * x for x in a)) * math.sqrt(sum(y * y for y in b)))


@function_tool
async def buscar_no_manual(pergunta: str) -> str:
    """Busca no manual técnico os trechos que respondem a uma pergunta.

    Args:
        pergunta: a dúvida do técnico, escrita com as palavras dele.

    Returns:
        Os trechos do manual mais parecidos com a pergunta, em ordem.
    """
    global CHAMADAS_DA_BUSCA
    CHAMADAS_DA_BUSCA += 1
    vetor = (await gerar_vetores([pergunta]))[0]
    notas = sorted(
        ((similaridade(vetor, v), t) for v, t in zip(VETORES, TRECHOS)),
        key=lambda par: par[0],
        reverse=True,
    )
    escolhidos = notas[:JANELA_DA_BUSCA]
    numeros = [t["numero"] for _, t in escolhidos]
    print(f"      [busca no manual] '{pergunta}' -> trechos {numeros}")
    return "\n\n---\n\n".join(f"[trecho {t['numero']}]\n{t['texto']}" for _, t in escolhidos)


# ---------------------------------------------------------------------- o agente


INSTRUCAO_BASE = (
    "Você é o assistente dos técnicos de campo da Metalúrgica Andrade, especialista no "
    "manual do compressor CMP-100. "
    "Responda em no máximo três frases curtas. "
    "Use a conversa anterior para entender perguntas curtas do técnico. "
    "Quando precisar de um procedimento do manual, use a ferramenta de busca. "
    "Responda apenas com o que estiver na conversa ou nos trechos do manual. "
    "Se não tiver a informação, diga claramente que não sabe e não invente nada."
)

# A instrução base deixa o agente decidir quando buscar, e ele às vezes decide que
# não precisa, mesmo tendo a ferramenta à mão. Esta é a instrução que o agente do
# exercício usa: ela tira essa decisão dele para perguntas de procedimento. A base
# fica no arquivo para servir de comparação no experimento.
INSTRUCAO_REFORCADA = INSTRUCAO_BASE + (
    " Sempre que a pergunta envolver um procedimento, um valor ou um passo de manutenção, "
    "consulte o manual com a ferramenta antes de responder, mesmo que você ache que já sabe a "
    "resposta e mesmo que o assunto já tenha aparecido na conversa. "
    "Use a conversa anterior para entender a que equipamento e a que situação a pergunta se "
    "refere, e a busca para achar o procedimento."
)


# Nas configurações sem RAG o agente não tem ferramenta nenhuma. Mandar consultar
# uma ferramenta inexistente faz o modelo inventar uma chamada e a execução quebra
# com ModelBehaviorError. Então essa configuração recebe uma instrução sem busca.
INSTRUCAO_SEM_BUSCA = (
    "Você é o assistente dos técnicos de campo da Metalúrgica Andrade, especialista no "
    "manual do compressor CMP-100. "
    "Responda em no máximo três frases curtas. "
    "Use a conversa anterior para entender perguntas curtas do técnico. "
    "Responda apenas com o que estiver na conversa. "
    "Se não tiver a informação, diga claramente que não sabe e não invente nada."
)


def escolher_instrucao(com_rag: bool, reforcada: bool) -> str:
    if not com_rag:
        return INSTRUCAO_SEM_BUSCA
    return INSTRUCAO_REFORCADA if reforcada else INSTRUCAO_BASE


def criar_agente(com_rag: bool, reforcada: bool = True) -> Agent:
    return Agent(
        name="Assistente de Campo",
        instructions=escolher_instrucao(com_rag, reforcada),
        model=OpenAIChatCompletionsModel(
            model=os.getenv("GEMINI_MODEL"), openai_client=cliente_openai()
        ),
        tools=[buscar_no_manual] if com_rag else [],
    )


# ------------------------------------------------------------------- experimento


def sem_acento(texto: str) -> str:
    normalizado = unicodedata.normalize("NFD", texto.lower())
    return "".join(c for c in normalizado if unicodedata.category(c) != "Mn")


def contem(resposta: str, esperado: list[str]) -> bool:
    """Confere se a resposta traz o dado esperado. É uma checagem simples, por palavra."""
    texto = sem_acento(resposta)
    return any(sem_acento(e) in texto for e in esperado)


async def executar_com_retentativa(agente: Agent, pergunta: str, sessao):
    """Tenta de novo quando o provedor responde 503 ou 429.

    A execução inteira faz muitas chamadas seguidas, e o plano gratuito recusa
    algumas por excesso de demanda. Sem isso, o experimento morre no meio.
    """
    espera = 15
    for tentativa in range(1, 5):
        try:
            return await Runner.run(agente, pergunta, session=sessao)
        except Exception as erro:
            codigo = getattr(erro, "status_code", None)
            recuperavel = codigo in (429, 503) or isinstance(erro, ModelBehaviorError)
            if not recuperavel or tentativa == 4:
                raise
            motivo = f"provedor respondeu {codigo}" if codigo else f"{type(erro).__name__}"
            print(f"      ({motivo}; nova tentativa em {espera}s)")
            await asyncio.sleep(espera)
            espera *= 2


async def rodar_cenario(
    rotulo: str,
    perguntas: list[dict],
    com_rag: bool,
    com_memoria: bool,
    reforcada: bool = True,
    quantos_trechos: int = QUANTOS_TRECHOS_BUSCAR,
) -> list[dict]:
    global JANELA_DA_BUSCA
    JANELA_DA_BUSCA = quantos_trechos
    partes = []
    partes.append("RAG ligado" if com_rag else "RAG DESLIGADO")
    partes.append("memória ligada" if com_memoria else "memória DESLIGADA")
    if not reforcada:
        partes.append("instrução base, sem reforço")
    if quantos_trechos != QUANTOS_TRECHOS_BUSCAR:
        partes.append(f"janela estreita, de {quantos_trechos} trechos")
    print("-" * 70)
    print(f"{rotulo}  ({', '.join(partes)})")
    print("-" * 70)

    sessao = None
    if com_memoria:
        PASTA_DAS_SESSOES.mkdir(exist_ok=True)
        caminho = PASTA_DAS_SESSOES / f"{sem_acento(rotulo).replace(' ', '_')}.db"
        caminho.unlink(missing_ok=True)
        sessao = SQLiteSession("tecnico", str(caminho))

    agente = criar_agente(com_rag, reforcada)
    resultados = []

    for numero, item in enumerate(perguntas, start=1):
        global CHAMADAS_DA_BUSCA
        antes = CHAMADAS_DA_BUSCA
        print(f"   {numero}. Técnico: {item['pergunta']}")
        resultado = await executar_com_retentativa(agente, item["pergunta"], sessao)
        resposta = resultado.final_output
        usou_a_busca = CHAMADAS_DA_BUSCA > antes
        acertou = contem(resposta, item["esperado"])

        print(f"      Assistente: {resposta}")
        print(f"      Consultou o manual? {'sim' if usou_a_busca else 'NÃO'}")
        print(f"      Esperado no texto: {item['esperado']}  ->  {'OK' if acertou else 'FALHOU'}")
        if acertou and not usou_a_busca and item.get("exige_manual"):
            print("      ATENÇÃO: acertou sem consultar o manual, então respondeu de cabeça.")
        print()

        resultados.append(
            {"pergunta": item["pergunta"], "acertou": acertou, "usou_a_busca": usou_a_busca}
        )
        await asyncio.sleep(SEGUNDOS_DE_PAUSA)

    return resultados


CENARIO_A = [
    {
        "pergunta": "O compressor CMP-100 está com o alarme E-102. O que isso significa?",
        "esperado": ["termostatica"],
    },
    {
        "pergunta": "E o que acontece com o óleo se eu continuar operando assim?",
        "esperado": ["radiador", "temperatura"],
    },
    {"pergunta": "E qual era o código do alarme mesmo?", "esperado": ["e-102", "e102"]},
]

CENARIO_B = [
    {
        "pergunta": "Posso lavar o radiador com água na parada programada?",
        "esperado": ["ar comprimido"],
        "exige_manual": True,
    },
]

CENARIO_C = [
    {
        "pergunta": "Qual é o torque dos parafusos do cabeçote?",
        "esperado": ["quarenta e cinco", "45"],
        "exige_manual": True,
    },
    {
        "pergunta": "E depois de apertar, o que eu faço?",
        "esperado": ["trinta minutos", "30 minutos", "vazio"],
        "exige_manual": True,
    },
]


def titulo(texto: str) -> None:
    print()
    print("=" * 70)
    print(texto)
    print("=" * 70)


async def preparar() -> None:
    titulo("Preparação - o manual longo vira vetores")
    paragrafos = [
        p.strip() for p in CAMINHO_DO_MANUAL.read_text(encoding="utf-8").split("\n\n") if p.strip()
    ]
    TRECHOS.extend(montar_trechos(paragrafos))
    VETORES.extend(await gerar_vetores([t["texto"] for t in TRECHOS]))
    print(f"Manual: {CAMINHO_DO_MANUAL.name}, {len(paragrafos)} parágrafos")
    print(f"Trechos: {len(TRECHOS)} | vetores de {len(VETORES[0])} dimensões")


def linha_do_placar(nome: str, resultados: list[dict]) -> str:
    marcas = " ".join("OK " if r["acertou"] else "FALHA" for r in resultados)
    buscas = " ".join("sim " if r["usou_a_busca"] else "não " for r in resultados)
    acertos = sum(1 for r in resultados if r["acertou"])
    return f"  {nome:<34} {marcas:<18} {acertos}/{len(resultados)}   consultou: {buscas}"


async def main() -> None:
    await preparar()

    placar = []

    titulo("Cenário A - três perguntas de acompanhamento sobre o mesmo chamado")
    print("A primeira pergunta precisa do manual; a segunda e a terceira, da conversa.")
    print("Por isso este cenário roda nas três configurações.")
    print()
    a_sem_memoria = await rodar_cenario("Cenário A sem memória", CENARIO_A, True, False)
    a_sem_rag = await rodar_cenario("Cenário A sem RAG", CENARIO_A, False, True)
    a_completo = await rodar_cenario("Cenário A - agente do exercício", CENARIO_A, True, True)
    placar.append(("A sem memória (só RAG)", a_sem_memoria))
    placar.append(("A sem RAG (só memória)", a_sem_rag))
    placar.append(("A agente do exercício", a_completo))

    titulo("Cenário B - uma consulta pontual, sem conversa anterior")
    print("A resposta está num parágrafo do fim do manual e nunca foi conversada.")
    print()
    b_sem_rag = await rodar_cenario("Cenário B sem RAG", CENARIO_B, False, True)
    b_completo = await rodar_cenario("Cenário B - agente do exercício", CENARIO_B, True, True)
    placar.append(("B sem RAG (só memória)", b_sem_rag))
    placar.append(("B agente do exercício", b_completo))

    titulo("Diagnóstico - o trecho da segunda pergunta do Cenário C é achável?")
    print("A resposta está no trecho que fala em rodar trinta minutos em vazio.")
    print("Comparo duas formas de perguntar a mesma coisa à busca.")
    print()
    consultas = [
        ("as palavras do próprio técnico", "E depois de apertar, o que eu faço?"),
        (
            "a versão que o agente monta, puxando o assunto da conversa",
            "procedimento após aperto dos parafusos do cabeçote do compressor CMP-100",
        ),
    ]
    for rotulo_consulta, consulta in consultas:
        vetor = (await gerar_vetores([consulta]))[0]
        notas = sorted(
            ((similaridade(vetor, v), t) for v, t in zip(VETORES, TRECHOS)),
            key=lambda par: par[0],
            reverse=True,
        )
        print(f"   Consulta com {rotulo_consulta}:")
        print(f"     '{consulta}'")
        for posicao, (nota, trecho) in enumerate(notas[:6], start=1):
            se_3 = "entra" if posicao <= JANELA_ESTREITA else "FICA DE FORA"
            se_5 = "entra" if posicao <= QUANTOS_TRECHOS_BUSCAR else "fica de fora"
            marca = "  <== o trecho que responde" if "trinta minutos" in trecho["texto"] else ""
            print(f"       {posicao}º trecho {trecho['numero']:>2}: {nota:.4f}  "
                  f"(com janela 3 {se_3}; com janela 5 {se_5}){marca}")
        print()

    titulo("Cenário C - acompanhamento curto que exige um procedimento novo")
    print("A segunda pergunta é curta (depende da conversa) e pede um procedimento")
    print("que está em outro trecho do manual (depende da busca).")
    print()
    c_sem_memoria = await rodar_cenario("Cenário C sem memória", CENARIO_C, True, False)
    c_sem_rag = await rodar_cenario("Cenário C sem RAG", CENARIO_C, False, True)
    print("Agora as duas formas de combinar memória e busca: a ingênua e a do exercício.")
    print()
    c_ingenuo = await rodar_cenario(
        "Cenário C combinação ingênua",
        CENARIO_C,
        True,
        True,
        reforcada=False,
        quantos_trechos=JANELA_ESTREITA,
    )
    print("A combinação ingênua costuma falhar aqui, por dois motivos: o agente decide")
    print("que não precisa buscar, e quando busca o trecho certo fica fora da janela de 3.")
    print("Abaixo, o agente do exercício, com a instrução reforçada e a janela de 5.")
    print()
    c_completo = await rodar_cenario("Cenário C - agente do exercício", CENARIO_C, True, True)

    placar.append(("C sem memória (só RAG)", c_sem_memoria))
    placar.append(("C sem RAG (só memória)", c_sem_rag))
    placar.append(("C combinação ingênua", c_ingenuo))
    placar.append(("C agente do exercício", c_completo))

    titulo("Placar final")
    for nome, resultados in placar:
        print(linha_do_placar(nome, resultados))


if __name__ == "__main__":
    asyncio.run(main())
