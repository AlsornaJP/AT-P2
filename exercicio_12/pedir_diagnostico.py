"""Cliente de teste do Exercício 12.

Faz o papel do sistema de despacho: chama o serviço por HTTP e mostra quanto
tempo cada chamada levou. Suba o serviço antes, noutro terminal:

    uv run exercicio_12/servico.py
"""

import time

import httpx2 as httpx

ENDERECO = "http://127.0.0.1:8000"


def titulo(texto: str) -> None:
    print("=" * 70)
    print(texto)
    print("=" * 70)


def mostrar_tempo(inicio: float, rotulo: str) -> None:
    print(f"  -> {rotulo} em {time.perf_counter() - inicio:.3f} segundos")


def main() -> None:
    with httpx.Client(timeout=30) as cliente:
        titulo("1. GET /teste - o valor fixo, para saber se o serviço responde")
        inicio = time.perf_counter()
        resposta = cliente.get(f"{ENDERECO}/teste")
        mostrar_tempo(inicio, "respondeu")
        print(f"  status HTTP: {resposta.status_code}")
        print(f"  corpo: {resposta.json()}")
        print()

        titulo("2. POST /chamados - duas perguntas seguidas")
        pedidos = [
            {
                "codigo_equipamento": "CMP-100",
                "pergunta": "Com que força eu aperto os parafusos da tampa de cima?",
            },
            {
                "codigo_equipamento": "CMP-100",
                "pergunta": "Posso lavar o radiador com água na parada programada?",
            },
        ]

        relogio_total = time.perf_counter()
        for numero, pedido in enumerate(pedidos, start=1):
            print(f"  Pergunta {numero}: {pedido['pergunta']}")
            inicio = time.perf_counter()
            resposta = cliente.post(f"{ENDERECO}/chamados", json=pedido)
            mostrar_tempo(inicio, "o serviço aceitou")
            print(f"  status HTTP: {resposta.status_code} (202 = aceito, vou processar)")
            print(f"  corpo: {resposta.json()}")
            print()

        total = time.perf_counter() - relogio_total
        print(f"  As duas chamadas juntas levaram {total:.3f} segundos.")
        print("  O agente leva dezenas de segundos por pergunta. Olhe o outro")
        print("  terminal: o trabalho ainda está acontecendo lá.")
        print()

        titulo("3. POST /chamados com corpo inválido - a validação do Pydantic")
        print("  Enviando um pedido sem o campo 'pergunta':")
        resposta = cliente.post(f"{ENDERECO}/chamados", json={"codigo_equipamento": "CMP-100"})
        print(f"  status HTTP: {resposta.status_code} (422 = corpo não passou na validação)")
        for erro in resposta.json()["detail"]:
            print(f"  campo {erro['loc']}: {erro['msg']}")
        print()
        print("  O agente não chegou a ser acionado: o pedido parou na porta.")


if __name__ == "__main__":
    main()
