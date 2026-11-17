import random
import sys
import time

BASE_DIR = r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lotofacil_modo4.etapa1_regras_oficiais import DEZENAS_DISPONIVEIS
from lotofacil_modo4.etapa2_funcao_objetivo import avaliar_carteira_etapa2

random.seed(42)
J = 10000
universo = list(range(1, 26))
jogos = [tuple(sorted(random.sample(universo, 15))) for _ in range(J)]

t0 = time.perf_counter()
av = avaliar_carteira_etapa2(jogos, pool=DEZENAS_DISPONIVEIS)
t_tot = time.perf_counter() - t0
print(f"Tempo total avaliar_carteira_etapa2 J=10000: {t_tot:.4f} s")
print(f"Score F: {av['funcao_objetivo_F']}")
