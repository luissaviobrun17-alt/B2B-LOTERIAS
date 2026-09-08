"""Cálculo da Distância de Hamming posicional e diversificação de carteiras."""
def distancia_hamming(j1, j2):
    return sum(1 for a, b in zip(j1, j2) if a != b)

def diversificacao_carteira(jogos):
    k = len(jogos)
    if k <= 1:
        return 100.0, 0.0
    dist = []
    for i in range(k):
        for j in range(i + 1, k):
            dist.append(distancia_hamming(jogos[i], jogos[j]))
    media_h = sum(dist) / len(dist)
    div = (media_h / 7.0) * 100.0
    return round(div, 2), round(100.0 - div, 2)
