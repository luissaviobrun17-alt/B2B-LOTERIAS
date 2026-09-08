"""Detecção de desvios e anomalias estatísticas por teste Qui-Quadrado."""
import math

def teste_qui_quadrado_uniformidade(contagens, N):
    esperado = N / 10.0
    chi2 = sum(((contagens.get(d, 0) - esperado) ** 2) / esperado for d in range(10))
    return round(chi2, 3)
