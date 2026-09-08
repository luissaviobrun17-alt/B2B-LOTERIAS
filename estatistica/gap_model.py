"""Modelo de atrasos (gaps), atraso médio, máximo e desvio-padrão."""
import collections, statistics

def calcular_gaps_coluna(serie, N):
    gaps = collections.defaultdict(list)
    ultimos = {}
    for d in range(10):
        ult = -1
        for idx, val in enumerate(serie):
            if val == d:
                if ult != -1:
                    gaps[d].append(idx - ult - 1)
                else:
                    gaps[d].append(idx)
                ult = idx
        ultimos[d] = (N - 1) - ult if ult != -1 else N
    
    resumo = {}
    for d in range(10):
        resumo[d] = {
            "atraso_atual": ultimos[d],
            "atraso_medio": round(statistics.mean(gaps[d]), 2) if gaps[d] else 9.0,
            "atraso_maximo": max(gaps[d]) if gaps[d] else N
        }
    return resumo
