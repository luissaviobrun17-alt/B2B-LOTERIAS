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
