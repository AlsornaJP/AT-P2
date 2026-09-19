import json
import random
from pathlib import Path

SEED = 42

EQUIPAMENTOS = [
    ("CMP-100", "Compressor de Parafuso Andrade AR-7"),
    ("TRN-300", "Torno CNC Andrade T-300"),
    ("EST-450", "Esteira Transportadora Andrade E-450"),
    ("FRN-720", "Forno de Tratamento Térmico Andrade F-720"),
    ("BMB-210", "Bomba Centrífuga Andrade B-210"),
]

CAUSAS = [
    "sensor de temperatura descalibrado",
    "filtro de ar saturado",
    "correia frouxa ou desgastada",
    "falta de lubrificação no mancal",
    "válvula termostática travada",
    "desequilíbrio de tensão entre as fases",
    "rolamento com folga acima do limite",
    "placa de controle com mau contato",
    "vazamento na linha de pressão",
    "excesso de carga na partida",
]

ACOES = [
    "parar o equipamento e abrir chamado para a manutenção elétrica",
    "substituir o componente e registrar a troca no histórico",
    "limpar o conjunto e medir novamente antes de religar",
    "aguardar o resfriamento e conferir o aperto das conexões",
]


def gerar_manual() -> list:
    random.seed(SEED)
    manual = []

    for posicao, (codigo, nome) in enumerate(EQUIPAMENTOS, start=1):
        erros = []
        for numero in range(1, 4):
            erros.append(
                {
                    "codigo_erro": f"E-{posicao}0{numero}",
                    "causa_provavel": random.choice(CAUSAS),
                    "acao_recomendada": random.choice(ACOES),
                }
            )
        manual.append({"codigo": codigo, "nome": nome, "erros_conhecidos": erros})

    return manual


if __name__ == "__main__":
    caminho = Path(__file__).parent / "manuais.json"
    manual = gerar_manual()
    caminho.write_text(json.dumps(manual, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Arquivo gerado: {caminho}")
    print(f"Equipamentos: {len(manual)} | Seed usada: {SEED}")
    for equipamento in manual:
        codigos = [erro["codigo_erro"] for erro in equipamento["erros_conhecidos"]]
        print(f"- {equipamento['codigo']} ({equipamento['nome']}): {codigos}")
