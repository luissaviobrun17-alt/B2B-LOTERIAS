import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
from lotofacil_modo4.etapa4_arquitetura_adaptativa import executar_arquitetura_adaptativa_etapa4

t0 = time.perf_counter()
res = executar_arquitetura_adaptativa_etapa4(
    pool=range(1, 26),
    quantidade_jogos=1000,
    tamanho_aposta=15,
    semente=2026,
    max_avaliacoes=2000,
    forcar_algoritmo="algoritmo_guloso",
    medir_memoria=False,
)
t1 = time.perf_counter()
print(f"Tempo: {t1-t0:.3f} s, F: {res['funcao_objetivo_F']:.8f}, Evals: {res['telemetria']['avaliacoes_efetivas']}")
print(f"Criterio parada: {res['telemetria']['criterio_parada']}")
