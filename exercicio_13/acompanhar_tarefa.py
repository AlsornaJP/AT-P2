"""Cliente do Exercício 13: submete e fica consultando até a tarefa acabar.

Suba o serviço antes, noutro terminal:

    uv run exercicio_13/servico_tarefas.py
"""

import time

import httpx2 as httpx

ENDERECO = "http://127.0.0.1:8001"
SEGUNDOS_ENTRE_CONSULTAS = 3


def titulo(texto: str) -> None:
    print("=" * 70)
    print(texto)
    print("=" * 70)


def submeter_e_acompanhar(cliente: httpx.Client, pedido: dict, rotulo: str) -> None:
    titulo(rotulo)
    print(f"Pergunta: {pedido['pergunta']}")
    print()

    inicio = time.perf_counter()
    resposta = cliente.post(f"{ENDERECO}/agent/run", json=pedido)
    demora_do_post = time.perf_counter() - inicio
    aceito = resposta.json()
    task_id = aceito["task_id"]

    print(f"POST /agent/run respondeu em {demora_do_post:.3f}s")
    print(f"  status HTTP: {resposta.status_code} (202 Accepted)")
    print(f"  task_id: {task_id}")
    print(f"  estado inicial: {aceito['estado']}")
    print()

    print("Agora consultando o estado, de 3 em 3 segundos:")
    consulta = 0
    while True:
        consulta += 1
        estado_agora = cliente.get(f"{ENDERECO}/agent/status/{task_id}").json()
        decorrido = time.perf_counter() - inicio
        print(f"  consulta {consulta} ({decorrido:5.1f}s): estado = {estado_agora['estado']}")

        if estado_agora["estado"] != "pending":
            break
        time.sleep(SEGUNDOS_ENTRE_CONSULTAS)

    print()
    if estado_agora["estado"] == "done":
        print(f"  Pronto em {estado_agora['segundos']}s.")
        print(f"  Resposta: {estado_agora['resposta']}")
    else:
        print(f"  A tarefa falhou depois de {estado_agora['segundos']}s.")
        print(f"  Erro guardado: {estado_agora['erro'][:160]}")
    print()


def main() -> None:
    with httpx.Client(timeout=30) as cliente:
        submeter_e_acompanhar(
            cliente,
            {
                "codigo_equipamento": "CMP-100",
                "pergunta": "Qual é o intervalo de troca do óleo e do separador?",
            },
            "Caso 1 - o caminho normal: pending ate ficar done",
        )

        submeter_e_acompanhar(
            cliente,
            {
                "codigo_equipamento": "CMP-100",
                "pergunta": "Qual é o torque dos parafusos da base?",
                "usar_modelo_invalido": True,
            },
            "Caso 2 - uma falha de verdade: pending ate ficar error",
        )

        print("Nos dois casos o sistema de despacho foi liberado na hora, e só")
        print("voltou para consultar o resultado quando quis.")


if __name__ == "__main__":
    main()
