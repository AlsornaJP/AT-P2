import json
import random
from pathlib import Path

SEED = 7

EQUIPAMENTOS = ["CMP-100", "TRN-300", "EST-450", "FRN-720", "BMB-210"]

SERVICOS = [
    "troca do filtro de ar",
    "substituição do rolamento dianteiro",
    "limpeza do radiador de óleo",
    "calibração do sensor de temperatura",
    "reaperto das conexões do painel",
    "troca da correia de transmissão",
]

TECNICOS = ["Marcos Lima", "Ana Prado", "Carlos Ferreira", "Juliana Alves"]


def gerar_historico() -> list:
    random.seed(SEED)
    historico = []

    for codigo in EQUIPAMENTOS:
        servicos = []
        for numero in range(1, 4):
            servicos.append(
                {
                    "data": f"2026-0{numero}-1{numero}",
                    "servico": random.choice(SERVICOS),
                    "tecnico": random.choice(TECNICOS),
                    "horas_paradas": random.choice([1, 2, 4, 8]),
                }
            )
        historico.append({"codigo": codigo, "manutencoes": servicos})

    return historico


if __name__ == "__main__":
    caminho = Path(__file__).parent / "historico.json"
    historico = gerar_historico()
    caminho.write_text(json.dumps(historico, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Arquivo gerado: {caminho}")
    print(f"Equipamentos: {len(historico)} | Seed usada: {SEED}")
    for equipamento in historico:
        datas = [manutencao["data"] for manutencao in equipamento["manutencoes"]]
        print(f"- {equipamento['codigo']}: {datas}")
