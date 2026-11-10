import json
from motor_lotofacil import MotorLotofacilB2B

# Amostra de histórico da Lotofácil (12 concursos)
amostra_historico = [
    [1, 2, 4, 5, 6, 8, 9, 12, 16, 17, 18, 19, 21, 23, 24],
    [1, 2, 3, 7, 8, 9, 10, 13, 14, 18, 20, 21, 22, 23, 24],
    [1, 4, 6, 8, 9, 10, 12, 14, 15, 16, 18, 21, 22, 24, 25],
    [1, 3, 4, 6, 8, 10, 14, 15, 16, 18, 20, 21, 22, 24, 25],
    [1, 3, 4, 9, 10, 11, 12, 13, 14, 15, 19, 20, 22, 23, 25],
    [1, 3, 5, 7, 8, 9, 10, 14, 15, 17, 21, 22, 23, 24, 25],
    [1, 3, 7, 8, 9, 10, 12, 13, 14, 17, 18, 19, 20, 23, 25],
    [2, 5, 6, 7, 8, 9, 12, 15, 18, 19, 20, 21, 22, 24, 25],
    [1, 2, 3, 4, 5, 7, 8, 9, 11, 15, 16, 19, 22, 24, 25],
    [1, 2, 3, 5, 6, 10, 11, 14, 15, 17, 18, 19, 21, 23, 24],
    [1, 3, 4, 5, 6, 10, 12, 14, 17, 19, 20, 22, 23, 24, 25],
    [4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 15, 18, 20, 23, 25]
]

motor = MotorLotofacilB2B(amostra_historico, limite_historico=10)
res = motor.gerar_carteira(quantidade_jogos=10)

print(f"Sucesso: {res['sucesso']}")
print(f"Total Gerado: {res['total_gerado']}")
print(f"Divisão Selecionada: {res['estrutura_recomendada']['divisao_selecionada']}")
print(f"Estruturas Prioritárias: {res['estrutura_recomendada']['estruturas_prioritarias']}")
print(f"Cobertura 25 dezenas: {res['auditoria_carteira']['cobertura_25_pct']}%")
print(f"Score Médio: {res['auditoria_carteira']['score_medio']}")
for j in res['jogos'][:3]:
    print(f"{j['ranking']} | Score: {j['score_b2b']} | Jogos: {j['numeros_formatados']}")
print("\n--- VERDADE MATEMÁTICA ---")
print(res['verdade_matematica']['declaracao_fundamental'])


# =====================================================================
# TESTES DO FECHAMENTO POR GRUPOS (8 GRUPOS E 5 GRUPOS)
# =====================================================================
print("\n--- TESTES DE FECHAMENTO POR GRUPOS ---")

# 1. Fechamento 5 Grupos de 5 Dezenas: 1º Conjunto Base Apenas (qtd_conjuntos=1 -> 10 jogos)
res_g5_1 = MotorLotofacilB2B.gerar_jogos_por_grupos(MotorLotofacilB2B.GRUPOS_EXEMPLO_PADRAO_5, qtd_conjuntos=1)
assert res_g5_1["sucesso"] is True, "Falha na geracao de 5 grupos base"
assert res_g5_1["total_conjuntos"] == 1, f"Esperado 1 conjunto, obtido {res_g5_1['total_conjuntos']}"
assert res_g5_1["total_jogos"] == 10, f"Esperado 10 jogos, obtido {res_g5_1['total_jogos']}"
assert res_g5_1["jogos_duplicados"] == 0, "Nao deve haver jogos duplicados"
assert res_g5_1["custo_total_brl"] == 35.0, f"Esperado R$ 30,00, obtido {res_g5_1['custo_total_brl']}"
assert len(res_g5_1["dezenas_ausentes"]) == 0, "Deveria cobrir 100% das 25 dezenas"
for j in res_g5_1["jogos"]:
    assert len(j["numeros"]) == 15, "Cada jogo deve ter exatamente 15 dezenas"
    assert j["numeros"] == sorted(j["numeros"]), "Dezenas devem estar em ordem crescente"
print("[OK] Teste 5 Grupos (1 Conjunto Base): 10 jogos gerados com 100% de cobertura (25/25 dezenas).")

# 1b. Fechamento 5 Grupos: Desdobramento Parcial (37 conjuntos = 370 jogos)
res_g5_37 = MotorLotofacilB2B.gerar_jogos_por_grupos(MotorLotofacilB2B.GRUPOS_EXEMPLO_PADRAO_5, qtd_conjuntos=37)
assert res_g5_37["sucesso"] is True, "Falha no desdobramento de 37 conjuntos"
assert res_g5_37["total_conjuntos"] == 37, f"Esperado 37 conjuntos, obtido {res_g5_37['total_conjuntos']}"
assert res_g5_37["total_jogos"] == 370, f"Esperado 370 jogos, obtido {res_g5_37['total_jogos']}"
assert res_g5_37["jogos_unicos"] == 370, f"Esperado 370 jogos unicos, obtido {res_g5_37['jogos_unicos']}"
assert res_g5_37["jogos_duplicados"] == 0, f"Esperado 0 jogos duplicados, obtido {res_g5_37['jogos_duplicados']}"
assert res_g5_37["custo_total_brl"] == 1295.0, f"Esperado R$ 1.110,00, obtido {res_g5_37['custo_total_brl']}"
print("[OK] Teste 5 Grupos (37 Conjuntos Horizontais): 370 jogos 100% unicos sem duplicidade.")

# 1c. Fechamento 5 Grupos: Desdobramento Completo Planilha do Apostador (97 conjuntos = 970 jogos 100% unicos)
res_g5_97 = MotorLotofacilB2B.gerar_jogos_por_grupos(MotorLotofacilB2B.GRUPOS_EXEMPLO_PADRAO_5, qtd_conjuntos=97)
assert res_g5_97["sucesso"] is True, "Falha no desdobramento rotativo de 97 conjuntos"
assert res_g5_97["total_conjuntos"] == 97, f"Esperado 97 conjuntos, obtido {res_g5_97['total_conjuntos']}"
assert res_g5_97["total_jogos"] == 970, f"Esperado 970 jogos, obtido {res_g5_97['total_jogos']}"
assert res_g5_97["jogos_unicos"] == 970, f"Esperado 970 jogos unicos, obtido {res_g5_97['jogos_unicos']}"
assert res_g5_97["jogos_duplicados"] == 0, f"Esperado 0 jogos duplicados, obtido {res_g5_97['jogos_duplicados']}"
assert res_g5_97["custo_total_brl"] == 3395.0, f"Esperado R$ 2.910,00, obtido {res_g5_97['custo_total_brl']}"
assert len(res_g5_97["dezenas_ausentes"]) == 0, "Deveria cobrir 100% das 25 dezenas"
for j in res_g5_97["jogos"]:
    assert len(j["numeros"]) == 15, "Cada jogo deve ter exatamente 15 dezenas"
    assert j["numeros"] == sorted(j["numeros"]), "Dezenas devem estar em ordem crescente"
print("[OK] Teste 5 Grupos (Desdobramento IA 97 Conjuntos): 970 jogos 100% unicos sem duplicidade.")

# 1d. Fechamento 5 Grupos: Teto Maximo Matricial sem Duplicidade (1.246 conjuntos = 12.460 jogos 100% unicos)
res_g5_max = MotorLotofacilB2B.gerar_jogos_por_grupos(MotorLotofacilB2B.GRUPOS_EXEMPLO_PADRAO_5, qtd_conjuntos=1246)
assert res_g5_max["sucesso"] is True, "Falha no desdobramento de teto maximo"
assert res_g5_max["total_conjuntos"] == 1246, f"Esperado 1246 conjuntos, obtido {res_g5_max['total_conjuntos']}"
assert res_g5_max["total_jogos"] == 12460, f"Esperado 12460 jogos, obtido {res_g5_max['total_jogos']}"
assert res_g5_max["jogos_unicos"] == 12460, f"Esperado 12460 jogos unicos, obtido {res_g5_max['jogos_unicos']}"
assert res_g5_max["jogos_duplicados"] == 0, f"Esperado 0 jogos duplicados, obtido {res_g5_max['jogos_duplicados']}"
assert res_g5_max["custo_total_brl"] == 43610.0, f"Esperado R$ 37.380,00, obtido {res_g5_max['custo_total_brl']}"
assert len(res_g5_max["dezenas_ausentes"]) == 0, "Deveria cobrir 100% das 25 dezenas"
print("[OK] Teste 5 Grupos (Teto Maximo Matricial 1.246 Conjuntos): 12.460 jogos 100% unicos sem duplicidade.")

# 2. Fechamento 8 Grupos de 3 Dezenas (Matriz Planilha 48 jogos)
res_g8_48 = MotorLotofacilB2B.gerar_jogos_por_grupos(MotorLotofacilB2B.GRUPOS_EXEMPLO_PADRAO, modo="planilha_48", qtd_conjuntos=1)
assert res_g8_48["sucesso"] is True, "Falha na geracao de 8 grupos planilha"
assert res_g8_48["total_jogos"] == 48, f"Esperado 48 jogos, obtido {res_g8_48['total_jogos']}"
print("[OK] Teste 8 Grupos (Planilha 48): 48 jogos gerados com sucesso.")

# 3. Fechamento 8 Grupos de 3 Dezenas (Fechamento Total C(8,5) = 56 jogos)
res_g8_56 = MotorLotofacilB2B.gerar_jogos_por_grupos(MotorLotofacilB2B.GRUPOS_EXEMPLO_PADRAO, qtd_grupos_por_jogo=5, qtd_conjuntos=1)
assert res_g8_56["sucesso"] is True, "Falha na geracao de 8 grupos total"
assert res_g8_56["total_jogos"] == 56, f"Esperado 56 jogos, obtido {res_g8_56['total_jogos']}"
print("[OK] Teste 8 Grupos (Fechamento Total C(8,5)): 56 jogos gerados com sucesso.")
