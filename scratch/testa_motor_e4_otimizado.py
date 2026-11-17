import os
import random
import sys
import time

BASE_DIR = r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lotofacil_modo4.etapa1_regras_oficiais import DEZENAS_DISPONIVEIS, TAMANHO_SORTEIO
from lotofacil_modo4.etapa2_funcao_objetivo import (
    avaliar_carteira_etapa2,
)
from lotofacil_modo4.etapa4_arquitetura_adaptativa import (
    MotorIncrementalOtimizadoEtapa4,
    _resolver_especificacao_etapa4,
    _CACHE_NP2_EXATO,
)

# Testar para J=10000
random.seed(42)
J = 10000
jogos = [tuple(sorted(random.sample(range(1, 26), 15))) for _ in range(J)]
spec = _resolver_especificacao_etapa4(
    DEZENAS_DISPONIVEIS, (), (), "todos_os_jogos", J, 15, None, None, None, None
)

t0 = time.perf_counter()
av_e2 = avaliar_carteira_etapa2(jogos, pool=DEZENAS_DISPONIVEIS)
t_e2 = time.perf_counter() - t0

t0 = time.perf_counter()
motor = MotorIncrementalOtimizadoEtapa4(jogos, spec["pool"], spec["fixas_por_jogo"], spec["pesos"])
score_e4 = motor.score_atual()
t_e4 = time.perf_counter() - t0

diff = abs(score_e4 - av_e2["funcao_objetivo_F"])
print(f"J={J} | Tempo E2: {t_e2:.4f} s | Tempo E4: {t_e4:.4f} s | diff: {diff:.2e}")
