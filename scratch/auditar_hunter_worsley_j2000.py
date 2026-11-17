# -*- coding: utf-8 -*-
"""
AUDITORIA INDEPENDENTE DA COTA DE HUNTER-WORSLEY E ÁRVORE GERADORA MÁXIMA (J=2.000)
=================================================================================
Verifica explicitamente:
1. Grafo completo com 2.000 vértices e 1.999.000 arestas ponderadas por P(Ei ∩ Ej).
2. Algoritmo de Kruskal com Union-Find e compressão de caminhos.
3. Seleção estrita de exatamente 1.999 arestas acíclicas.
4. Conectividade total (1 componente conexo).
5. Desempate lexicográfico determinístico.
6. Fechamento analítico da cota Hunter-Worsley em Fraction vs float.
"""

from __future__ import annotations
from fractions import Fraction
import json
import math
import os
from pathlib import Path
import sys

sys.path.insert(0, os.path.abspath("."))

from lotofacil_modo4.etapa2_referencia_independente import (
    _prob_individual_direta,
    _prob_par_direta,
    _mst_max_kruskal,
    avaliar_carteira_referencia_independente,
)

caminho_2000 = Path("catalogo_lotofacil_10000") / "lotofacil_carteira_2000.json"
with open(caminho_2000, "r", encoding="utf-8") as f:
    doc = json.load(f)

jogos = [set(jg) for jg in doc["jogos"]]
j = len(jogos)
pares_tot = j * (j - 1) // 2

# Probabilidade individual (m=15)
p_ind = _prob_individual_direta(15)
s1 = Fraction(j, 1) * p_ind

print("=" * 80)
print("AUDITORIA DA ARVORE GERADORA MAXIMA E COTA DE HUNTER-WORSLEY (J=2.000)")
print("=" * 80)
print(f"Vertices no grafo:             {j:,}")
print(f"Arestas totais no grafo:       {pares_tot:,}")
print(f"Probabilidade marginal P(Ei):  {p_ind} (~ {float(p_ind):.10f})")
print(f"Soma S1 = sum P(Ei):           {s1} (~ {float(s1):.10f})")

# Construção das probabilidades conjuntas com desempate determinístico
arestas: list[tuple[Fraction, int, int]] = []
arestas_dict: dict[tuple[int, int], Fraction] = {}

for u in range(j):
    for v in range(u + 1, j):
        p_uv = _prob_par_direta(jogos[u], jogos[v])
        arestas.append((p_uv, u, v))
        arestas_dict[(u, v)] = p_uv

# Ordenação decrescente de peso com desempate lexicográfico determinístico por (u, v)
arestas.sort(key=lambda item: (-item[0], item[1], item[2]))

# Union-Find com compressão de caminhos
pai = list(range(j))
rank = [0] * j

def find(x: int) -> int:
    while pai[x] != x:
        pai[x] = pai[pai[x]]
        x = pai[x]
    return x

def union(x: int, y: int) -> bool:
    rx, ry = find(x), find(y)
    if rx == ry:
        return False
    if rank[rx] < rank[ry]:
        pai[rx] = ry
    elif rank[rx] > rank[ry]:
        pai[ry] = rx
    else:
        pai[ry] = rx
        rank[rx] += 1
    return True

arestas_mst: list[tuple[int, int, Fraction]] = []
soma_peso_mst = Fraction(0, 1)

for w, u, v in arestas:
    if union(u, v):
        arestas_mst.append((u, v, w))
        soma_peso_mst += w
        if len(arestas_mst) == j - 1:
            break

# Verificações topológicas
num_arestas_mst = len(arestas_mst)
componentes = len({find(i) for i in range(j)})
peso_mst_kruskal_modulo = _mst_max_kruskal(j, arestas_dict)
diff_peso_mst = abs(soma_peso_mst - peso_mst_kruskal_modulo)

cota_hw_bruta = s1 - soma_peso_mst
cota_hw_probabilidade = min(Fraction(1, 1), max(Fraction(0, 1), cota_hw_bruta))

# Comparação com o módulo oficial independente
ev_ref = avaliar_carteira_referencia_independente(doc["jogos"])
cota_hw_modulo = ev_ref["cota_superior_hunter_worsley"]
diff_hw = abs(float(cota_hw_probabilidade) - cota_hw_modulo)

print("-" * 80)
print(f"Arestas selecionadas na MST:  {num_arestas_mst} (esperado: {j - 1})")
print(f"Componentes conexos:           {componentes} (esperado: 1 conexo)")
print(f"Acyclicidade comprovada:       {num_arestas_mst == j - 1 and componentes == 1}")
print(f"Soma dos pesos da MST:         {soma_peso_mst} (~ {float(soma_peso_mst):.12f})")
print(f"MST do modulo independente:    {peso_mst_kruskal_modulo} (~ {float(peso_mst_kruskal_modulo):.12f})")
print(f"Divergencia no peso da MST:    {float(diff_peso_mst):.2e}")
print(f"Cota Hunter-Worsley bruta:     {cota_hw_bruta} (~ {float(cota_hw_bruta):.12f})")
print(f"Cota HW (teto prob. min(1,x)): {cota_hw_probabilidade} (~ {float(cota_hw_probabilidade):.12f})")
print(f"Cota Hunter-Worsley modulo:    {cota_hw_modulo:.12f}")
print(f"Divergência analítica final:   {diff_hw:.2e}")
print(f"Fechamento validado (<=1e-12): {diff_hw <= 1e-12 and diff_peso_mst == 0}")
print("=" * 80)
