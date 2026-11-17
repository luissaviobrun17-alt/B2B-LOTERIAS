import time
import random

apostas = [random.getrandbits(25) for _ in range(1000)]
sorteios = [random.getrandbits(25) for _ in range(10000)]

t0 = time.perf_counter()
contagens = [0] * 26
for s in sorteios:
    for a in apostas:
        c = (a & s).bit_count()
        contagens[c] += 1
t1 = time.perf_counter()

print(f"Tempo para 10.000 sorteios x 1.000 jogos: {t1 - t0:.3f} s")
print(f"Estimativa para 100.000 sorteios: {(t1 - t0) * 10:.2f} s")
print(f"Estimativa para 11 carteiras x 100.000 sorteios: {(t1 - t0) * 110:.2f} s")
