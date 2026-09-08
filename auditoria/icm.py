"""Índice de Confiança Matemática (ICM) e Diagnóstico de Honestidade."""
def calcular_icm(score_sms, diversificacao, n_amostra):
    fator_amostra = min(1.0, n_amostra / 100.0)
    icm = (score_sms * 0.50) + (diversificacao * 0.35) + (fator_amostra * 100.0 * 0.15)
    return int(max(10, min(92, round(icm))))
