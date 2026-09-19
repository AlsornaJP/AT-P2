import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

cliente = OpenAI(
    api_key=os.getenv("OPENROUTER_API_KEY"),
    base_url=os.getenv("OPENROUTER_BASE_URL"),
)
MODELO = os.getenv("OPENROUTER_MODEL")

INSTRUCAO_SISTEMA = (
    "Você é um assistente de manutenção industrial. "
    "Responda em português, de forma clara e curta."
)


def perguntar(mensagens: list, **parametros) -> str:
    resposta = cliente.chat.completions.create(
        model=MODELO,
        messages=mensagens,
        extra_body={"reasoning": {"enabled": False}},
        **parametros,
    )
    return resposta.choices[0].message.content


def mostrar(titulo: str, texto: str) -> None:
    print("=" * 60)
    print(titulo)
    print("=" * 60)
    print(texto)
    print()


def conversa_com_historico() -> None:
    historico = [
        {"role": "system", "content": INSTRUCAO_SISTEMA},
        {"role": "user", "content": "O compressor de ar da linha 3 está desligando sozinho depois de uns 20 minutos ligado."},
    ]

    primeira_resposta = perguntar(historico)
    historico.append({"role": "assistant", "content": primeira_resposta})
    mostrar("Turno 1 - técnico cita o equipamento", primeira_resposta)

    historico.append({"role": "user", "content": "E qual peça dele eu devo verificar primeiro?"})
    segunda_resposta = perguntar(historico)
    historico.append({"role": "assistant", "content": segunda_resposta})
    mostrar("Turno 2 - pergunta que depende do turno 1", segunda_resposta)

    print(f"Total de mensagens no histórico: {len(historico)}")
    print()


def diagnostico_com_parametros() -> None:
    pergunta = [
        {"role": "system", "content": INSTRUCAO_SISTEMA},
        {"role": "user", "content": "Um motor elétrico trifásico está vibrando muito e esquentando. Qual é a causa mais provável?"},
    ]

    resposta_focada = perguntar(pergunta, temperature=0.1, top_p=0.3)
    mostrar("Diagnóstico com temperature=0.1 e top_p=0.3", resposta_focada)

    resposta_criativa = perguntar(pergunta, temperature=1.5, top_p=1.0)
    mostrar("Diagnóstico com temperature=1.5 e top_p=1.0", resposta_criativa)


def sugestao_com_parametros() -> None:
    pergunta = [
        {"role": "system", "content": INSTRUCAO_SISTEMA},
        {"role": "user", "content": "Liste 15 sugestões de manutenção preventiva para as bombas centrífugas de uma fábrica."},
    ]

    resposta_padrao = perguntar(pergunta)
    mostrar("Sugestões sem ajuste de parâmetros", resposta_padrao)

    resposta_ajustada = perguntar(pergunta, temperature=0.9, max_tokens=400, frequency_penalty=0.8)
    mostrar("Sugestões com temperature=0.9, max_tokens=400 e frequency_penalty=0.8", resposta_ajustada)


if __name__ == "__main__":
    conversa_com_historico()
    diagnostico_com_parametros()
    sugestao_com_parametros()
