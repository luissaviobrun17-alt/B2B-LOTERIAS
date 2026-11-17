import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
from lotofacil_modo4.etapa4_arquitetura_adaptativa import executar_arquitetura_adaptativa_etapa4, MotorIncrementalOtimizadoEtapa4
from lotofacil_modo4.etapa2_funcao_objetivo import avaliar_carteira_etapa2
from lotofacil_modo4.etapa2_referencia_independente import avaliar_carteira_referencia_independente

res = executar_arquitetura_adaptativa_etapa4(
    pool=range(1, 26),
    quantidade_jogos=1000,
    tamanho_aposta=15,
    semente=2026,
    max_avaliacoes=2000,
    forcar_algoritmo="algoritmo_guloso",
    medir_memoria=False,
)
carteira = res["carteira"]
pesos = res["especificacao"]["pesos"]

# Validador 1: Motor incremental Etapa 4
motor = MotorIncrementalOtimizadoEtapa4(carteira, tuple(range(1, 26)), (), pesos)
f_e4 = motor.score_atual()

# Validador 2: Etapa 2 oficial
ev_e2 = avaliar_carteira_etapa2(carteira)
f_e2 = float(ev_e2["funcao_objetivo_F"])

# Validador 3: Referencia independente
ev_ref = avaliar_carteira_referencia_independente(carteira)
f_ref = float(ev_ref["funcao_objetivo_F"])

print(f"F E4:  {f_e4:.16f}")
print(f"F E2:  {f_e2:.16f}")
print(f"F Ref: {f_ref:.16f}")
print(f"|E4 - E2|:  {abs(f_e4 - f_e2):.2e}")
print(f"|E4 - Ref|: {abs(f_e4 - f_ref):.2e}")
print(f"|E2 - Ref|: {abs(f_e2 - f_ref):.2e}")
