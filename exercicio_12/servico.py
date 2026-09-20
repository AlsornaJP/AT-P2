"""Exercício 12 - o agente do Exercício 11 exposto por HTTP, com FastAPI.

Para subir o serviço:  uv run exercicio_12/servico.py
Para testar:           uv run exercicio_12/pedir_diagnostico.py  (noutro terminal)
"""

import asyncio
import sys
import time
import uuid
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path

import uvicorn
from fastapi import BackgroundTasks, FastAPI
from pydantic import BaseModel, Field

# O enunciado pede o agente do Exercício 11. Em vez de copiar o código para cá,
# acrescento a RAIZ do projeto ao caminho de busca e importo a pasta dele como
# pacote. Assim é literalmente o mesmo agente, e não uma cópia que envelhece.
# A raiz é necessária porque o Python coloca a pasta do script no caminho, e não
# a do projeto.
sys.path.insert(0, str(Path(__file__).parent.parent))

from exercicio_11 import agente_integrador as agente_do_exercicio_11  # noqa: E402
from agents import Runner  # noqa: E402

# Os resultados prontos ficam aqui. É um dicionário na memória do processo:
# some quando o serviço reinicia e não é compartilhado entre cópias do serviço.
# Para o exercício basta; num sistema de verdade seria banco ou fila.
RESULTADOS: dict[str, dict] = {}


def registrar(mensagem: str) -> None:
    """Escreve no log do serviço na hora.

    Sem o flush, o texto fica esperando no buffer quando a saída não é um
    terminal, e as linhas aparecem fora de ordem em relação às do uvicorn —
    o que atrapalharia justamente a evidência deste exercício.
    """
    print(mensagem, flush=True)


@asynccontextmanager
async def ciclo_de_vida(app: FastAPI):
    """Prepara o índice do manual uma vez, quando o serviço sobe."""
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
        f"{len(agente_do_exercicio_11.TRECHOS)} trechos indexados. "
        "O serviço já pode receber perguntas."
    )
    yield
    registrar("[encerramento] serviço parando.")


app = FastAPI(
    title="Assistente de Campo - Metalúrgica Andrade",
    description="Expõe o agente de diagnóstico para o sistema de despacho de chamados.",
    version="1.0",
    lifespan=ciclo_de_vida,
)


class PerguntaDoTecnico(BaseModel):
    """O que o sistema de despacho envia."""

    codigo_equipamento: str = Field(
        min_length=3, description="o código do equipamento, por exemplo CMP-100"
    )
    pergunta: str = Field(min_length=5, description="a dúvida do técnico, com as palavras dele")


class ChamadoAceito(BaseModel):
    """O que o serviço devolve na hora, sem esperar o agente."""

    id_do_chamado: str
    situacao: str
    recebido_em: datetime
    aviso: str


class RespostaDeTeste(BaseModel):
    """Valores fixos, para o sistema de despacho conferir se o serviço está no ar."""

    servico: str
    situacao: str
    versao: str


async def responder_o_chamado(id_do_chamado: str, pedido: PerguntaDoTecnico) -> None:
    """Roda o agente. Isto acontece depois de a resposta HTTP já ter sido enviada."""
    registrar(f"[fundo] {id_do_chamado}: começou a trabalhar")
    relogio = time.perf_counter()

    pergunta = f"Equipamento {pedido.codigo_equipamento}. {pedido.pergunta}"
    resultado = await Runner.run(agente_do_exercicio_11.criar_agente(com_rag=True), pergunta)
    duracao = time.perf_counter() - relogio

    RESULTADOS[id_do_chamado] = {
        "resposta": resultado.final_output,
        "segundos": round(duracao, 1),
    }
    registrar(f"[fundo] {id_do_chamado}: terminou em {duracao:.1f}s")
    registrar(f"[fundo] {id_do_chamado}: {resultado.final_output}")


@app.post("/chamados", response_model=ChamadoAceito, status_code=202)
async def abrir_chamado(pedido: PerguntaDoTecnico, tarefas: BackgroundTasks) -> ChamadoAceito:
    """Recebe a dúvida do técnico e responde na hora, sem esperar o agente."""
    id_do_chamado = uuid.uuid4().hex[:8]
    registrar(f"[POST /chamados] {id_do_chamado}: {pedido.codigo_equipamento} - {pedido.pergunta}")

    # A tarefa só roda depois que esta função retornar e a resposta for enviada.
    tarefas.add_task(responder_o_chamado, id_do_chamado, pedido)

    return ChamadoAceito(
        id_do_chamado=id_do_chamado,
        situacao="em processamento",
        recebido_em=datetime.now(),
        aviso="O agente leva alguns segundos. Acompanhe pelo log do serviço.",
    )


@app.get("/teste", response_model=RespostaDeTeste)
async def teste() -> RespostaDeTeste:
    """Valor fixo, para o sistema de despacho saber que o serviço responde."""
    return RespostaDeTeste(
        servico="Assistente de Campo",
        situacao="no ar",
        versao="1.0",
    )


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
