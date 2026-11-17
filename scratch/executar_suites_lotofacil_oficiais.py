# -*- coding: utf-8 -*-
import os
import subprocess
import sys

suites = [
    "testes/test_lotofacil_modo4_etapa1.py",
    "testes/test_lotofacil_modo4_etapa2.py",
    "testes/test_lotofacil_modo4_etapa3.py",
    "testes/test_lotofacil_modo4_etapa4.py",
    "testes/test_lotofacil_modo4_equivalencia_fase1.py",
    "testes/test_lotofacil_modo4_fase2_catalogo.py",
    "testes/test_integracao_operacional_catalogo_lotofacil.py",
]

print("=" * 80)
print("EXECUÇÃO CONSOLIDADA DAS SUÍTES OFICIAIS LOTOFÁCIL MODO 4")
print("=" * 80)

todas_ok = True
resultados = []

for s in suites:
    cmd = [sys.executable, "-m", "unittest", s]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    sucesso = (proc.returncode == 0)
    if not sucesso:
        todas_ok = False
    resultados.append((s, proc.returncode, sucesso, proc.stderr.strip()))
    status_str = "APROVADO (OK)" if sucesso else f"FALHOU (Código {proc.returncode})"
    print(f"[{status_str:<18}] {s}")

print("-" * 80)
if todas_ok:
    print("TODAS AS SUÍTES OFICIAIS DA LOTOFÁCIL MODO 4 FORAM 100% APROVADAS (CÓDIGO 0).")
else:
    print("HOUVE FALHAS NAS SEGUINTES SUÍTES:")
    for s, code, suc, err in resultados:
        if not suc:
            print(f"--- {s} (código {code}) ---")
            print(err[:500])
print("=" * 80)
