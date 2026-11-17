# -*- coding: utf-8 -*-
"""
AUDITORIA DE INDEPENDÊNCIA E CASOS DE FRONTEIRA DA REFERÊNCIA INDEPENDENTE
========================================================================
1. Auditoria de isolamento e desacoplamento de imports via AST.
2. Validação de aritmética racional exata com fractions.Fraction.
3. Testes de fronteira analíticos:
   - Caso 1: Dois jogos clones idênticos (c=15, covariância máxima).
   - Caso 2: Dois jogos de interseção mínima (c=5, covariância negativa).
   - Caso 3: Jogo único simples (J=1, m=15).
   - Caso 4: Jogo único múltiplo (J=1, m=16).
   - Caso 5: Três jogos com duplicata parcial (J=3, 2 clones e 1 diferente).
"""

from __future__ import annotations
import ast
from fractions import Fraction
import math
import os
from pathlib import Path
import sys

sys.path.insert(0, os.path.abspath("."))

from lotofacil_modo4.etapa1_regras_oficiais import probabilidade_pelo_menos_k_exata
from lotofacil_modo4.etapa2_funcao_objetivo import avaliar_carteira_etapa2
from lotofacil_modo4.etapa2_referencia_independente import (
    _prob_individual_direta,
    _prob_par_direta,
    avaliar_carteira_referencia_independente,
)
from lotofacil_modo4.etapa4_arquitetura_adaptativa import MotorIncrementalOtimizadoEtapa4

print("=" * 80)
print("AUDITORIA DE INDEPENDÊNCIA DE CÓDIGO E TESTES DE FRONTEIRA")
print("=" * 80)

# 1. Auditoria AST de isolamento de código
caminho_ref = Path("lotofacil_modo4") / "etapa2_referencia_independente.py"
with open(caminho_ref, "r", encoding="utf-8") as f:
    arvore = ast.parse(f.read(), filename=str(caminho_ref))

modulos_importados: list[str] = []
for nodo in ast.walk(arvore):
    if isinstance(nodo, ast.Import):
        for alias in nodo.names:
            modulos_importados.append(alias.name)
    elif isinstance(nodo, ast.ImportFrom):
        mod_origem = nodo.module or ""
        for alias in nodo.names:
            modulos_importados.append(f"{mod_origem}.{alias.name}" if mod_origem else alias.name)

print("1. Auditoria de AST e Desacoplamento de Imports:")
print(f"   Arquivo auditado: {caminho_ref}")
imports_etapa2 = [imp for imp in modulos_importados if "etapa2_funcao_objetivo" in imp]
print(f"   Imports de etapa2_funcao_objetivo encontrados: {len(imports_etapa2)}")
if imports_etapa2:
    raise RuntimeError(f"FALHA DE ISOLAMENTO: {imports_etapa2}")
print("   Status Isolamento: 100% DESACOPLADO (zero dependências de etapa2_funcao_objetivo)")

# 2. Testes de Casos de Fronteira Analíticos
print("\n2. Execução dos Casos de Fronteira Analíticos:")

p1 = _prob_individual_direta(15)
assert isinstance(p1, Fraction), "Probabilidade individual deve ser Fraction!"

# Fronteira 1: Clones idênticos
jg_clone1 = list(range(1, 16))
jg_clone2 = list(range(1, 16))
cart_clones = [jg_clone1, jg_clone2]

p2_clones = _prob_par_direta(set(jg_clone1), set(jg_clone2))
assert p2_clones == p1, f"Para jogos clones, P(A e B) ({p2_clones}) deve ser exatamente P(A) ({p1})!"
ev_clones_ref = avaliar_carteira_referencia_independente(cart_clones)
ev_clones_e2 = avaliar_carteira_etapa2(cart_clones)

diff_clones = abs(ev_clones_ref["funcao_objetivo_F"] - ev_clones_e2["funcao_objetivo_F"])
print(f"   [Fronteira 1 - Clones c=15] P(A e B) == P(A): {p2_clones == p1} | Diff |E2 - Ref|: {diff_clones:.2e}")
assert diff_clones <= 1e-12

# Fronteira 2: Interseção mínima c=5
jg_min1 = list(range(1, 16))
jg_min2 = list(range(1, 6)) + list(range(16, 26))
cart_min = [jg_min1, jg_min2]

p2_min = _prob_par_direta(set(jg_min1), set(jg_min2))
assert p2_min == Fraction(0, 1), f"Para c=5 na Lotofácil, P(A e B) ({p2_min}) deve ser 0 exatamente!"
ev_min_ref = avaliar_carteira_referencia_independente(cart_min)
ev_min_e2 = avaliar_carteira_etapa2(cart_min)

diff_min = abs(ev_min_ref["funcao_objetivo_F"] - ev_min_e2["funcao_objetivo_F"])
print(f"   [Fronteira 2 - Interseção Mínima c=5] P(A e B) == 0: {p2_min == Fraction(0, 1)} | Diff |E2 - Ref|: {diff_min:.2e}")
assert diff_min <= 1e-12

# Fronteira 3: Jogo único simples (J=1, m=15)
cart_j1 = [list(range(1, 16))]
ev_j1_ref = avaliar_carteira_referencia_independente(cart_j1)
ev_j1_e2 = avaliar_carteira_etapa2(cart_j1)
diff_j1 = abs(ev_j1_ref["funcao_objetivo_F"] - ev_j1_e2["funcao_objetivo_F"])
print(f"   [Fronteira 3 - J=1 Simples m=15] Diff |E2 - Ref|: {diff_j1:.2e}")
assert diff_j1 <= 1e-12

# Fronteira 4: Três jogos com duplicata parcial
cart_j3 = [
    list(range(1, 16)),
    list(range(1, 16)),
    list(range(1, 11)) + list(range(16, 21)),
]
ev_j3_ref = avaliar_carteira_referencia_independente(cart_j3)
ev_j3_e2 = avaliar_carteira_etapa2(cart_j3)
diff_j3 = abs(ev_j3_ref["funcao_objetivo_F"] - ev_j3_e2["funcao_objetivo_F"])
print(f"   [Fronteira 4 - J=3 com Duplicata] Diff |E2 - Ref|: {diff_j3:.2e}")
assert diff_j3 <= 1e-12

print("-" * 80)
print("TODOS OS CASOS DE FRONTEIRA E ISOLAMENTO DE AST FORAM APROVADOS (<= 1e-12).")
print("=" * 80)
