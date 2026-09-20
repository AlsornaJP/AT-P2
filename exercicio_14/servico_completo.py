"""Exercício 14 - o agente integrador como serviço REST completo.

Fluxo: submeter, acompanhar, obter o diagnóstico estruturado.

    POST /agent/run                 -> 202 com o task_id
    GET  /agent/status/{task_id}    -> pending, done ou error
    GET  /agent/response/{task_id}  -> o DiagnosticoEquipamento do Exercício 8

Para subir:   uv run exercicio_14/servico_completo.py
Para testar:  uv run exercicio_14/cliente_despacho.py   (noutro terminal)
"""

import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import uvicorn
from dotenv import load_dotenv
from fastapi import BackgroundTasks, FastAPI, HTTPException
from pydantic import BaseModel, Field

# A raiz do projeto entra no caminho de busca do Python, porque ao rodar um
# script ele coloca ali a pasta do próprio script, e não a do projeto. Com a raiz
# no caminho, cada pasta de exercício pode ser importada como pacote.
RAIZ = Path(__file__).parent.parent
sys.path.insert(0, str(RAIZ))

# Do Exercício 8 vêm os modelos aninhados e a ferramenta do manual com peças.
from exercicio_08 import diagnostico_completo as exercicio_08  # noqa: E402

# Do Exercício 11 vem a busca semântica sobre o manual longo.
from exercicio_11 import agente_integrador as exercicio_11  # noqa: E402
from agents import (  # noqa: E402
    Agent,
    MaxTurnsExceeded,
    OpenAIChatCompletionsModel,
    Runner,
)
from openai import AsyncOpenAI  # noqa: E402
import os  # noqa: E402

load_dotenv()

TAREFAS: dict[str, dict] = {}
MAXIMO_DE_RODADAS = 8


def registrar(mensagem: str) -> None:
    print(mensagem, flush=True)


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    registrar("[arranque] indexando o manual longo para a busca semântica...")
    relogio = time.perf_counter()

    texto = exercicio_11.CAMINHO_DO_MANUAL.read_text(encoding="utf-8")
    paragrafos = [p.strip() for p in texto.split("\n\n") if p.strip()]
    exercicio_11.TRECHOS.extend(exercicio_11.montar_trechos(paragrafos))
    exercicio_11.VETORES.extend(
        await exercicio_11.gerar_vetores([t["texto"] for t in exercicio_11.TRECHOS])
    )

    registrar(
        f"[arranque] pronto em {time.perf_counter() - relogio:.2f}s: "
        f"{len(exercicio_11.TRECHOS)} trechos indexados."
    )
    registrar(f"[arranque] manual com peças: {exercicio_08.CAMINHO_DO_MANUAL.name}")
    yield
    registrar("[encerramento] serviço parando.")


app = FastAPI(
    title="Assistente de Campo - serviço completo",
    description="Submissão, acompanhamento e obtenção do diagnóstico estruturado.",
    version="1.0",
    lifespan=ciclo_de_vida,
)


class PerguntaDoTecnico(BaseModel):
    codigo_equipamento: str = Field(min_length=3, description="por exemplo CMP-100")
    pergunta: str = Field(min_length=5, description="a dúvida do técnico")


class TarefaAceita(BaseModel):
    task_id: str
    estado: str
    recebido_em: datetime
    onde_acompanhar: str


class EstadoDaTarefa(BaseModel):
    task_id: str
    estado: str
    pergunta: str
    segundos: float | None = None
    erro: str | None = None


def criar_agente_integrador() -> Agent:
    """O agente integrador: as duas fontes mais a saída estruturada.

    A instrução diz qual ferramenta serve para quê. Sem isso, o Exercício 11
    mostrou que o agente com duas fontes decide não usar uma delas.
    """
    cliente = AsyncOpenAI(
        api_key=os.getenv("GEMINI_API_KEY"), base_url=os.getenv("GEMINI_BASE_URL")
    )
    return Agent(
        name="Assistente de Campo",
        instructions=(
            "Você é o assistente dos técnicos de campo da Metalúrgica Andrade. "
            "Você tem duas fontes e precisa usar as duas. "
            "Use consultar_manual_equipamento para achar a causa provável, a ação recomendada e, "
            "principalmente, a lista de peças de reposição daquele erro: as peças só existem nessa "
            "fonte, então sem essa consulta a lista fica vazia. "
            "Use buscar_no_manual para achar detalhes de procedimento no manual longo, e some esse "
            "detalhe ao campo acao_recomendada, sem contrariar o que a primeira fonte disse. "
            "Consulte as duas antes de responder, mesmo que ache que já sabe. "
            "Se a consulta ao manual falhar, explique no campo causa_provavel, oriente no campo "
            "acao_recomendada e devolva a lista de peças vazia."
        ),
        model=OpenAIChatCompletionsModel(
            model=os.getenv("GEMINI_MODEL"), openai_client=cliente
        ),
        output_type=exercicio_08.DiagnosticoEquipamento,
        tools=[exercicio_08.consultar_manual_equipamento, exercicio_11.buscar_no_manual],
    )


async def processar(task_id: str, pedido: PerguntaDoTecnico) -> None:
    registrar(f"[fundo] {task_id}: começou (pending)")
    relogio = time.perf_counter()

    try:
        pergunta = f"Equipamento {pedido.codigo_equipamento}. {pedido.pergunta}"
        resultado = await Runner.run(
            criar_agente_integrador(), pergunta, max_turns=MAXIMO_DE_RODADAS
        )

        TAREFAS[task_id]["estado"] = "done"
        TAREFAS[task_id]["diagnostico"] = resultado.final_output
        TAREFAS[task_id]["segundos"] = round(time.perf_counter() - relogio, 1)
        registrar(f"[fundo] {task_id}: terminou em {TAREFAS[task_id]['segundos']}s -> done")

    except MaxTurnsExceeded:
        # Saída estruturada com ferramenta foi o que entrou em laço no Exercício 7.
        # Se acontecer aqui, a tarefa termina em error com a explicação, em vez
        # de ficar presa para sempre.
        TAREFAS[task_id]["estado"] = "error"
        TAREFAS[task_id]["erro"] = (
            "O agente ficou chamando as ferramentas sem concluir e passou de "
            f"{MAXIMO_DE_RODADAS} rodadas."
        )
        TAREFAS[task_id]["segundos"] = round(time.perf_counter() - relogio, 1)
        registrar(f"[fundo] {task_id}: laço de ferramenta -> error")

    except Exception as erro:
        TAREFAS[task_id]["estado"] = "error"
        TAREFAS[task_id]["erro"] = f"{type(erro).__name__}: {erro}"
        TAREFAS[task_id]["segundos"] = round(time.perf_counter() - relogio, 1)
        registrar(f"[fundo] {task_id}: falhou -> error: {type(erro).__name__}")


def buscar_tarefa(task_id: str) -> dict:
    """Acha a tarefa ou recusa o pedido com 404 e uma mensagem que orienta.

    A decisão de projeto do enunciado está aqui, e está explicada no texto:
    um task_id que nunca existiu é um endereço errado, não uma falha do
    serviço, então a resposta é 404 e não 500.
    """
    tarefa = TAREFAS.get(task_id)
    if tarefa is None:
        registrar(f"[404] task_id desconhecido: {task_id}")
        raise HTTPException(
            status_code=404,
            detail={
                "erro": "task_id não encontrado",
                "task_id": task_id,
                "explicacao": (
                    "Este identificador nunca foi emitido por este serviço, ou foi perdido "
                    "quando o serviço reiniciou, porque o registro de tarefas fica em memória."
                ),
                "o_que_fazer": "Submeta a pergunta de novo em POST /agent/run.",
            },
        )
    return tarefa


@app.post("/agent/run", response_model=TarefaAceita, status_code=202)
async def submeter(pedido: PerguntaDoTecnico, tarefas: BackgroundTasks) -> TarefaAceita:
    task_id = uuid.uuid4().hex[:8]
    TAREFAS[task_id] = {
        "task_id": task_id,
        "estado": "pending",
        "pergunta": pedido.pergunta,
        "diagnostico": None,
        "erro": None,
        "segundos": None,
    }
    registrar(f"[POST /agent/run] {task_id}: {pedido.codigo_equipamento} - {pedido.pergunta}")
    tarefas.add_task(processar, task_id, pedido)

    return TarefaAceita(
        task_id=task_id,
        estado="pending",
        recebido_em=datetime.now(),
        onde_acompanhar=f"/agent/status/{task_id}",
    )


@app.get("/agent/status/{task_id}", response_model=EstadoDaTarefa)
async def consultar_estado(task_id: str) -> EstadoDaTarefa:
    tarefa = buscar_tarefa(task_id)
    registrar(f"[GET /agent/status] {task_id}: {tarefa['estado']}")
    return EstadoDaTarefa(
        task_id=tarefa["task_id"],
        estado=tarefa["estado"],
        pergunta=tarefa["pergunta"],
        segundos=tarefa["segundos"],
        erro=tarefa["erro"],
    )


@app.get("/agent/response/{task_id}", response_model=exercicio_08.DiagnosticoEquipamento)
async def obter_diagnostico(task_id: str):
    """Devolve o diagnóstico estruturado, quando a tarefa está done."""
    tarefa = buscar_tarefa(task_id)

    if tarefa["estado"] == "pending":
        registrar(f"[409] {task_id}: pediram o resultado antes da hora")
        raise HTTPException(
            status_code=409,
            detail={
                "erro": "o diagnóstico ainda não está pronto",
                "estado": "pending",
                "o_que_fazer": f"Acompanhe em /agent/status/{task_id} até o estado virar done.",
            },
        )

    if tarefa["estado"] == "error":
        registrar(f"[409] {task_id}: pediram o resultado de uma tarefa que falhou")
        raise HTTPException(
            status_code=409,
            detail={
                "erro": "o processamento falhou, não há diagnóstico",
                "estado": "error",
                "motivo": tarefa["erro"],
            },
        )

    registrar(f"[GET /agent/response] {task_id}: entregando o diagnóstico")
    return tarefa["diagnostico"]


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002, log_level="info")
