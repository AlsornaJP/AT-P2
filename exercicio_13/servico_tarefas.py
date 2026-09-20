"""Exercício 13 - submeter agora, consultar depois.

O sistema de despacho manda a pergunta, recebe um task_id na hora e consulta o
resultado numa chamada separada, quando quiser.

Para subir o serviço:  uv run exercicio_13/servico_tarefas.py
Para testar:           uv run exercicio_13/acompanhar_tarefa.py  (noutro terminal)
"""

import os
import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import BackgroundTasks, FastAPI
from openai import AsyncOpenAI
from pydantic import BaseModel, Field

# Mesmo caminho do Exercício 12: o agente é o do Exercício 11, importado.
sys.path.insert(0, str(Path(__file__).parent.parent / "exercicio_11"))

import agente_integrador as agente_do_exercicio_11  # noqa: E402
from agents import OpenAIChatCompletionsModel, Runner  # noqa: E402

# O registro das tarefas: task_id -> o que se sabe sobre ela.
# Os três estados são os que o enunciado pede: pending, done e error.
TAREFAS: dict[str, dict] = {}


def registrar(mensagem: str) -> None:
    """Escreve no log na hora, sem esperar o buffer."""
    print(mensagem, flush=True)


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    registrar("[arranque] segmentando o manual e gerando os vetores...")
    relogio = time.perf_counter()

    texto = agente_do_exercicio_11.CAMINHO_DO_MANUAL.read_text(encoding="utf-8")
    paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    agente_do_exercicio_11.TRECHOS.extend(agente_do_exercicio_11.montar_trechos(paragrafos))
    vetores = await agente_do_exercicio_11.gerar_vetores(
        [t["texto"] for t in agente_do_exercicio_11.TRECHOS]
    )
    agente_do_exercicio_11.VETORES.extend(vetores)

    registrar(
        f"[arranque] pronto em {time.perf_counter() - relogio:.2f}s: "
        f"{len(agente_do_exercicio_11.TRECHOS)} trechos indexados."
    )
    yield
    registrar("[encerramento] serviço parando.")


app = FastAPI(
    title="Assistente de Campo - submissão e consulta",
    description="Submeta a pergunta em POST /agent/run e acompanhe em GET /agent/status/{task_id}.",
    version="1.0",
    lifespan=ciclo_de_vida,
)


class PerguntaDoTecnico(BaseModel):
    codigo_equipamento: str = Field(min_length=3, description="por exemplo CMP-100")
    pergunta: str = Field(min_length=5, description="a dúvida do técnico")

    # Este campo existe só para demonstrar o estado "error" com uma falha de
    # verdade: a tarefa passa a usar um nome de modelo que não existe, e o
    # provedor devolve um erro autêntico. Não faria parte de um serviço real.
    usar_modelo_invalido: bool = Field(
        default=False, description="só para teste: força uma falha real no processamento"
    )


class TarefaAceita(BaseModel):
    task_id: str
    estado: str
    recebido_em: datetime


class EstadoDaTarefa(BaseModel):
    task_id: str
    estado: str
    pergunta: str
    resposta: str | None = None
    erro: str | None = None
    segundos: float | None = None


def montar_agente(usar_modelo_invalido: bool):
    """O agente do Exercício 11. Com o sinalizador de teste, aponta para um
    modelo inexistente, o que faz o provedor recusar a chamada de verdade."""
    agente = agente_do_exercicio_11.criar_agente(com_rag=True)
    if not usar_modelo_invalido:
        return agente

    cliente = AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"), base_url=os.getenv("GEMINI_BASE_URL")
    )
    return agente.clone(
        model=OpenAIChatCompletionsModel(
            model="modelo-que-nao-existe", openai_client=cliente
        )
    )


async def processar(task_id: str, pedido: PerguntaDoTecnico) -> None:
    """Roda o agente e anota o desfecho no registro das tarefas.

    Tudo dentro de try/except: se uma exceção escapasse daqui, ela sumiria em
    silêncio e a tarefa ficaria em pending para sempre, sem ninguém saber.
    """
    registrar(f"[fundo] {task_id}: começou (estado atual: pending)")
    relogio = time.perf_counter()

    try:
        pergunta = f"Equipamento {pedido.codigo_equipamento}. {pedido.pergunta}"
        resultado = await Runner.run(montar_agente(pedido.usar_modelo_invalido), pergunta)

        TAREFAS[task_id]["estado"] = "done"
        TAREFAS[task_id]["resposta"] = resultado.final_output
        TAREFAS[task_id]["segundos"] = round(time.perf_counter() - relogio, 1)
        registrar(f"[fundo] {task_id}: terminou em {TAREFAS[task_id]['segundos']}s -> done")

    except Exception as erro:
        TAREFAS[task_id]["estado"] = "error"
        TAREFAS[task_id]["erro"] = f"{type(erro).__name__}: {erro}"
        TAREFAS[task_id]["segundos"] = round(time.perf_counter() - relogio, 1)
        registrar(f"[fundo] {task_id}: falhou em {TAREFAS[task_id]['segundos']}s -> error")
        registrar(f"[fundo] {task_id}: {type(erro).__name__}: {str(erro)[:120]}")


@app.post("/agent/run", response_model=TarefaAceita, status_code=202)
async def submeter(pedido: PerguntaDoTecnico, tarefas: BackgroundTasks) -> TarefaAceita:
    """Recebe a pergunta, devolve o task_id na hora e processa depois."""
    task_id = uuid.uuid4().hex[:8]

    # A tarefa já nasce registrada como pending, antes de a resposta sair.
    # Se ela nascesse dentro da função de fundo, haveria um instante em que o
    # sistema de despacho teria o task_id e a consulta não o encontraria.
    TAREFAS[task_id] = {
        "task_id": task_id,
        "estado": "pending",
        "pergunta": pedido.pergunta,
        "resposta": None,
        "erro": None,
        "segundos": None,
    }

    registrar(f"[POST /agent/run] {task_id}: {pedido.pergunta}")
    tarefas.add_task(processar, task_id, pedido)

    return TarefaAceita(task_id=task_id, estado="pending", recebido_em=datetime.now())


@app.get("/agent/status/{task_id}", response_model=EstadoDaTarefa)
async def consultar(task_id: str) -> EstadoDaTarefa:
    """Devolve o estado atual da tarefa: pending, done ou error.

    Consultar um task_id que não existe quebra aqui, com erro 500. É assim de
    propósito neste exercício; tratar esse caso é assunto do Exercício 14.
    """
    tarefa = TAREFAS[task_id]
    registrar(f"[GET /agent/status] {task_id}: {tarefa['estado']}")
    return EstadoDaTarefa(**tarefa)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8001, log_level="info")
