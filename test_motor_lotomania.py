import sys
sys.path.append(r'C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS')
from motor_lotomania import MotorLotomaniaB2B

print("=== INICIANDO TESTES DO MOTOR LOTOMANIA (10 GRUPOS 2D) ===")

# 1. Teste 1 Conjunto Base no modo 10 jogos espelho
res_1_10 = MotorLotomaniaB2B.gerar_jogos_por_grupos(
    MotorLotomaniaB2B.GRUPOS_EXEMPLO_PADRAO_10,
    modo="10_jogos",
    qtd_conjuntos=1
)
assert res_1_10["sucesso"] is True, "Falha na geracao 1 conjunto 10 jogos"
assert res_1_10["total_conjuntos"] == 1, f"Esperado 1 conjunto, obtido {res_1_10['total_conjuntos']}"
assert res_1_10["total_jogos"] == 10, f"Esperado 10 jogos, obtido {res_1_10['total_jogos']}"
assert res_1_10["jogos_duplicados"] == 0, "Nao deve haver jogos duplicados"
assert len(res_1_10["dezenas_ausentes"]) == 0, "Deveria cobrir 100% das 100 dezenas"
for j in res_1_10["jogos"]:
    assert len(j["numeros"]) == 50, f"Cada jogo deve ter 50 dezenas, obtido {len(j['numeros'])}"
    assert j["numeros"] == sorted(j["numeros"]), "Dezenas devem estar ordenadas"
print("[OK] Teste 1 Conjunto Base (10 Jogos Espelho): 10 jogos de 50 dezenas com 100% de cobertura.")

# 2. Teste 1 Conjunto Base no modo Planilha 126
res_1_126 = MotorLotomaniaB2B.gerar_jogos_por_grupos(
    MotorLotomaniaB2B.GRUPOS_EXEMPLO_PADRAO_10,
    modo="planilha_126",
    qtd_conjuntos=1
)
assert res_1_126["sucesso"] is True, "Falha na geracao 1 conjunto 126 jogos"
assert res_1_126["total_conjuntos"] == 1, f"Esperado 1 conjunto, obtido {res_1_126['total_conjuntos']}"
assert res_1_126["total_jogos"] == 126, f"Esperado 126 jogos, obtido {res_1_126['total_jogos']}"
assert res_1_126["jogos_duplicados"] == 0, "Nao deve haver jogos duplicados"
print("[OK] Teste 1 Conjunto Base (Planilha 126): 126 jogos gerados com sucesso.")

# 3. Teste 12 Conjuntos da Planilha do Apostador (11 Horizontais + 1 Vertical Transposta) no modo 10 jogos
res_12_10 = MotorLotomaniaB2B.gerar_jogos_por_grupos(
    MotorLotomaniaB2B.GRUPOS_EXEMPLO_PADRAO_10,
    modo="10_jogos",
    qtd_conjuntos=12
)
assert res_12_10["sucesso"] is True, "Falha na geracao 12 conjuntos 10 jogos"
assert res_12_10["total_conjuntos"] == 12, f"Esperado 12 conjuntos, obtido {res_12_10['total_conjuntos']}"
assert res_12_10["total_jogos"] == 120, f"Esperado 120 jogos, obtido {res_12_10['total_jogos']}"
assert res_12_10["jogos_duplicados"] == 0, "Nao deve haver jogos duplicados em 12 conjuntos"
print("[OK] Teste 12 Conjuntos (10 Jogos por Conjunto = 120 Jogos): 100% unicos sem duplicidade.")

# 4. Teste 12 Conjuntos da Planilha no modo Planilha 126 (1.505 jogos unicos)
res_12_126 = MotorLotomaniaB2B.gerar_jogos_por_grupos(
    MotorLotomaniaB2B.GRUPOS_EXEMPLO_PADRAO_10,
    modo="planilha_126",
    qtd_conjuntos=12,
    eliminar_duplicados=True
)
assert res_12_126["sucesso"] is True, "Falha na geracao 12 conjuntos planilha 126"
assert res_12_126["total_conjuntos"] == 12, f"Esperado 12 conjuntos, obtido {res_12_126['total_conjuntos']}"
assert res_12_126["total_jogos"] == 1505, f"Esperado 1505 jogos unicos, obtido {res_12_126['total_jogos']}"
assert res_12_126["jogos_duplicados"] == 7, f"Esperado 7 duplicatas filtradas, obtido {res_12_126['jogos_duplicados']}"
print("[OK] Teste 12 Conjuntos (Planilha 126 = 1.505 Jogos): 100% unicos sem duplicidade.")

print("\nTODOS OS TESTES DA LOTOMANIA FORAM CONCLUIDOS COM SUCESSO!")
