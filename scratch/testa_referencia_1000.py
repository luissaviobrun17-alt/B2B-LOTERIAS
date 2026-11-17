import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
from lotofacil_modo4.etapa4_arquitetura_adaptativa import executar_arquitetura_adaptativa_etapa4
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
print(f"Jogos gerados: {len(carteira)}")

t0 = time.perf_counter()
res_ref = avaliar_carteira_referencia_independente(carteira)
t1 = time.perf_counter()

print(f"Tempo referencia independente: {t1-t0:.3f} s")
print(f"F referencia: {res_ref['funcao_objetivo_F']:.12f}")
print(f"F Etapa 4: {res['funcao_objetivo_F']:.12f}")
print(f"Diferenca: {abs(res_ref['funcao_objetivo_F'] - res['funcao_objetivo_F']):.2e}")
