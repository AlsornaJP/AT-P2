"""Cliente do Exercício 14: o fluxo completo, do jeito que o sistema de
despacho faria — submeter, acompanhar, obter o diagnóstico.

Suba o serviço antes, noutro terminal:

    uv run exercicio_14/servico_completo.py
"""

import time

import httpx2 as httpx

ENDERECO = "http://127.0.0.1:8002"
SEGUNDOS_ENTRE_CONSULTAS = 3
TASK_ID_INVENTADO = "00000000"


def titulo(texto: str) -> None:
    print()
    print("=" * 72)
    print(texto)
    print("=" * 72)


def mostrar_diagnostico(dados: dict) -> None:
    print(f"  codigo ............: {dados['codigo']}")
    print(f"  causa_provavel ....: {dados['causa_provavel']}")
    print(f"  acao_recomendada ..: {dados['acao_recomendada']}")
    print(f"  pecas_recomendadas : {len(dados['pecas_recomendadas'])} peça(s)")
    for numero, peca in enumerate(dados["pecas_recomendadas"], start=1):
        print(
            f"     {numero}. {peca['nome']}  |  quantidade: {peca['quantidade']}"
            f"  |  prioridade: {peca['prioridade']}"
        )


def main() -> None:
    with httpx.Client(timeout=60) as cliente:
        titulo("FLUXO COMPLETO - submeter, acompanhar, obter")

        pedido = {
            "codigo_equipamento": "CMP-100",
            "pergunta": "Deu o erro E-102. Qual a causa, o que faço e que peças eu levo?",
        }
        print(f"Equipamento: {pedido['codigo_equipamento']}")
        print(f"Pergunta...: {pedido['pergunta']}")
        print()

        inicio = time.perf_counter()
        resposta = cliente.post(f"{ENDERECO}/agent/run", json=pedido)
        aceito = resposta.json()
        task_id = aceito["task_id"]
        print(f"1. POST /agent/run  ->  {resposta.status_code} em "
              f"{time.perf_counter() - inicio:.3f}s")
        print(f"   task_id: {task_id}")
        print(f"   onde acompanhar: {aceito['onde_acompanhar']}")
        print()

        print("2. GET /agent/response cedo demais, de propósito:")
        cedo = cliente.get(f"{ENDERECO}/agent/response/{task_id}")
        print(f"   -> {cedo.status_code} ({cedo.json()['detail']['erro']})")
        print(f"      {cedo.json()['detail']['o_que_fazer']}")
        print()

        print("3. GET /agent/status até virar done:")
        consulta = 0
        while True:
            consulta += 1
            estado = cliente.get(f"{ENDERECO}/agent/status/{task_id}").json()
            print(f"   consulta {consulta} ({time.perf_counter() - inicio:5.1f}s): "
                  f"{estado['estado']}")
            if estado["estado"] != "pending":
                break
            time.sleep(SEGUNDOS_ENTRE_CONSULTAS)

        print()
        if estado["estado"] == "error":
            print(f"   A tarefa falhou: {estado['erro']}")
            return

        print(f"4. GET /agent/response  (a tarefa levou {estado['segundos']}s)")
        final = cliente.get(f"{ENDERECO}/agent/response/{task_id}")
        print(f"   -> {final.status_code}")
        print()
        mostrar_diagnostico(final.json())

        titulo("CASO DE BORDA - um task_id que nunca existiu")

        print(f"Consultando o status do task_id inventado '{TASK_ID_INVENTADO}':")
        r = cliente.get(f"{ENDERECO}/agent/status/{TASK_ID_INVENTADO}")
        print(f"   -> HTTP {r.status_code}")
        for chave, valor in r.json()["detail"].items():
            print(f"      {chave}: {valor}")
        print()

        print(f"Pedindo o diagnóstico do mesmo task_id inventado:")
        r = cliente.get(f"{ENDERECO}/agent/response/{TASK_ID_INVENTADO}")
        print(f"   -> HTTP {r.status_code} ({r.json()['detail']['erro']})")
        print()
        print("O serviço continuou no ar: os dois pedidos foram recusados com")
        print("404 e uma explicação, sem rastro de exceção e sem erro 500.")


if __name__ == "__main__":
    main()
