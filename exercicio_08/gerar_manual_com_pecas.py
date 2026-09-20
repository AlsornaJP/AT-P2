"""Gera o manual do Exercício 8: o mesmo do Exercício 5, agora com peças de reposição.

As causas e ações são geradas com a mesma seed do Exercício 5, então os erros
conhecidos saem idênticos. A novidade é a lista de peças dentro de cada erro.
"""

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

# Cada causa tem as peças que costumam ser trocadas para resolvê-la. Isso é fixo,
# e não sorteado, para o manual fazer sentido: a peça combina com o defeito.
PECAS_POR_CAUSA = {
    "sensor de temperatura descalibrado": [
        ("sensor de temperatura PT-100", 1, "alta"),
        ("cabo de sinal blindado 2x0,5mm", 1, "baixa"),
    ],
    "filtro de ar saturado": [
        ("elemento filtrante de ar", 2, "alta"),
        ("junta de vedação do filtro", 2, "media"),
    ],
    "correia frouxa ou desgastada": [
        ("correia dentada A-42", 1, "alta"),
        ("polia tensora", 1, "media"),
    ],
    "falta de lubrificação no mancal": [
        ("graxa de lítio EP-2 (tubo 400g)", 3, "alta"),
        ("retentor do mancal", 2, "media"),
    ],
    "válvula termostática travada": [
        ("válvula termostática 3/4", 1, "alta"),
        ("jogo de juntas", 2, "media"),
    ],
    "desequilíbrio de tensão entre as fases": [
        ("contator tripolar 25A", 1, "alta"),
        ("fusível retardado 32A", 3, "media"),
    ],
    "rolamento com folga acima do limite": [
        ("rolamento 6205-2RS", 2, "alta"),
        ("anel elástico de retenção", 2, "baixa"),
    ],
    "placa de controle com mau contato": [
        ("placa de controle CP-12", 1, "alta"),
        ("conector de 16 vias", 1, "media"),
    ],
    "vazamento na linha de pressão": [
        ("mangueira de pressão 1/2", 1, "alta"),
        ("abraçadeira inox 20mm", 4, "baixa"),
    ],
    "excesso de carga na partida": [
        ("relé térmico regulável", 1, "alta"),
        ("mola de acoplamento", 2, "media"),
    ],
}


def pecas_da_causa(causa: str) -> list:
    return [
        {"nome": nome, "quantidade": quantidade, "prioridade": prioridade}
        for nome, quantidade, prioridade in PECAS_POR_CAUSA[causa]
    ]


def gerar_manual() -> list:
    random.seed(SEED)
    manual = []

    for posicao, (codigo, nome) in enumerate(EQUIPAMENTOS, start=1):
        erros = []
        for numero in range(1, 4):
            causa = random.choice(CAUSAS)
            erros.append(
                {
                    "codigo_erro": f"E-{posicao}0{numero}",
                    "causa_provavel": causa,
                    "acao_recomendada": random.choice(ACOES),
                    "pecas_recomendadas": pecas_da_causa(causa),
                }
            )
        manual.append({"codigo": codigo, "nome": nome, "erros_conhecidos": erros})

    return manual


if __name__ == "__main__":
    caminho = Path(__file__).parent / "manuais_com_pecas.json"
    manual = gerar_manual()
    caminho.write_text(json.dumps(manual, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Arquivo gerado: {caminho}")
    print(f"Equipamentos: {len(manual)} | Seed usada: {SEED}")
    for equipamento in manual:
        for erro in equipamento["erros_conhecidos"]:
            pecas = ", ".join(peca["nome"] for peca in erro["pecas_recomendadas"])
            print(f"- {equipamento['codigo']} {erro['codigo_erro']}: {pecas}")
