"""Análise de frequências históricas, recentes e ponderadas por coluna."""
import collections, math

def calcular_frequencias_coluna(serie, N):
    cont = collections.Counter(serie)
    return {d: cont.get(d, 0) / N if N > 0 else 0.1 for d in range(10)}

def frequencia_exponencial(serie, N, lamb=0.04):
    res = collections.defaultdict(float)
    for t in range(N):
        w = math.exp(-lamb * (N - 1 - t))
        res[serie[t]] += w
    return res
