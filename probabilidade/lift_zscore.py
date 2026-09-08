"""Matriz de Coocorrência, Lift e Z-Score com suavização de Laplace."""
import math

def calcular_lift_par(observado, N, p1=0.1, p2=0.1):
    esperado = N * p1 * p2
    lift_laplace = ((observado + 1) / (N + 100)) / (p1 * p2)
    var = N * (p1 * p2) * (1 - (p1 * p2))
    z = (observado - esperado) / math.sqrt(var) if var > 0 else 0.0
    return round(lift_laplace, 3), round(z, 2)
