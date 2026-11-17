# -*- coding: utf-8 -*-
import json
from collections import Counter
from pathlib import Path

caminho_2000 = Path("catalogo_lotofacil_10000") / "lotofacil_carteira_2000.json"
with open(caminho_2000, "r", encoding="utf-8") as f:
    doc = json.load(f)

jogos = [set(jg) for jg in doc["jogos"]]
j = len(jogos)
pares_tot = j * (j - 1) // 2

contagem_inter = Counter()
soma_inter = 0
for i in range(j):
    ji = jogos[i]
    for k in range(i + 1, j):
        inter = len(ji & jogos[k])
        contagem_inter[inter] += 1
        soma_inter += inter

print(f"Total de pares analisados: {pares_tot:,}")
print(f"Soma inteira das intersecoes: {soma_inter:,}")
print(f"Media exata das intersecoes:  {soma_inter / pares_tot:.12f}")
print("-" * 50)
print("Distribuicao exata de intersecoes:")
for c in sorted(contagem_inter.keys()):
    qtd = contagem_inter[c]
    pct = qtd / pares_tot * 100.0
    print(f"  {c:2d} dezenas em comum: {qtd:8,d} pares ({pct:6.3f}%)")
print("-" * 50)
print(f"Soma das frequencias: {sum(contagem_inter.values()):,}")
