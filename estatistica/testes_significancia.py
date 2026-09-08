"""Testes de significância e correção para múltiplos testes (Benjamini-Hochberg FDR)."""
def benjamini_hochberg_fdr(p_valores, alpha=0.05):
    p_ordenados = sorted(p_valores)
    m = len(p_ordenados)
    descobertas = 0
    for rank, p in enumerate(p_ordenados, 1):
        if p <= (rank / m) * alpha:
            descobertas = rank
    return descobertas
