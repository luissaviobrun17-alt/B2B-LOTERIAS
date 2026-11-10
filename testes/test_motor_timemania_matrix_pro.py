import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from motor_timemania import MotorTimemaniaB2B

print("=" * 70)
print("TESTE DE VALIDAÇÃO: MOTOR TIMEMANIA MATRIX PRO (B2B LOTERIAS)")
print("=" * 70)

motor = MotorTimemaniaB2B()
print("Motor inicializado com sucesso!")

# 1. Teste de Reprodução dos 384 Jogos Originais
desd = motor.gerar_desdobramentos_matriz()
print(f"[1] Desdobramentos da Base Direta: {len(desd)} jogos gerados (esperado: 384)")
assert len(desd) == 384, f"Esperado 384, obtido {len(desd)}"

# 2. Teste da Base Invertida (Boustrophedon)
base_inv = motor.calcular_base_invertida()
print(f"[2] Base Invertida calculada com sucesso: 8 linhas x {len(base_inv[0])} colunas")
desd_ambas = motor.gerar_desdobramentos_matriz(ambas_bases=True)
print(f"[3] Desdobramentos combinados (Base Direta + Invertida): {len(desd_ambas)} jogos (esperado: 768)")
assert len(desd_ambas) == 768, f"Esperado 768, obtido {len(desd_ambas)}"

# 3. Teste de Cobertura das 80 Dezenas e 100% de Pares
cob_768 = motor.calcular_matriz_cobertura_80([j["dezenas"] for j in desd_ambas])
cob_pct = cob_768["cobertura_dezenas_pct"]
pares_pct = cob_768["cobertura_pares"]["percentual"]
pares_cob = cob_768["cobertura_pares"]["total_cobertos"]
print(f"[4] Cobertura das 80 dezenas (768 jogos): {cob_pct}% ({cob_768['total_dezenas_cobertas']}/80)")
print(f"[5] Cobertura de pares C(80,2): {pares_pct}% ({pares_cob}/3160)")
assert cob_pct == 100.0, "Esperado 100% de dezenas cobertas!"
assert pares_pct == 100.0, "Esperado 100% de pares cobertos!"

# 4. Teste dos 7 Modos de Operação
print("\n[6] Testando os 7 Modos de Operação:")
modos = ["original", "aprimorado", "matematico_puro", "estatistico", "hibrido", "diversificacao", "experimental"]
for m in modos:
    res = motor.gerar_carteira(quantidade_jogos=12, modo=m)
    print(f"    - Modo {m:16s}: {len(res['jogos'])} jogos | Score Médio: {res['score_medio']} | Custo: R$ {res['custo_total_rs']:.2f}")
    assert len(res["jogos"]) == 12, f"Erro na quantidade de jogos no modo {m}"

# 5. Teste do Comparador de Desdobramentos
print("\n[7] Executando o Comparador de Desdobramentos (Original vs Aprimorado vs Híbrido):")
comp = motor.comparar_desdobramentos(quantidade_jogos=32, concursos_backtest=20)
print(f"    Concursos avaliados: {comp['concursos_avaliados']}")
for row in comp["tabela_comparativa"]:
    print(f"    - {row['criterio']:<38} | Orig: {row['original']:<15} | Aprim: {row['aprimorado']:<15} | Hibr: {row['hibrido']}")

print("\n" + "=" * 70)
print("TODOS OS TESTES DE VALIDAÇÃO FORAM CONCLUÍDOS COM 100% DE SUCESSO!")
print("=" * 70)
