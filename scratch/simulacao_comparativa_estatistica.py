import os
import sys
import json
import time
import math
import random
from pathlib import Path
from typing import Any, Dict, List, Tuple, Set

sys.path.insert(0, os.path.abspath("."))
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

from lotofacil_modo4.etapa1_regras_oficiais import validar_aposta_lotofacil

NUM_SORTEIOS = 100_000
SEMENTE_SORTEIOS = 999_999
SEMENTES_REFERENCIA = [1001, 1002, 1003, 1004, 1005, 1006, 1007, 1008, 1009, 1010]
J = 1000

def cdf_normal(z: float) -> float:
    """Função de distribuição acumulada da normal padrão N(0,1)."""
    return 0.5 * (1.0 + math.erf(z / math.sqrt(2.0)))

def p_valor_mcnemar(n10: int, n01: int) -> Tuple[float, float]:
    """
    Calcula qui-quadrado de McNemar com correção de continuidade de Edwards
    e p-valor bicaudal exato via erfc.
    """
    soma = n10 + n01
    if soma == 0:
        return 0.0, 1.0
    diff = abs(n10 - n01)
    # Correção de continuidade
    chi2 = ((diff - 1.0) ** 2) / soma if diff > 0 else 0.0
    # Para 1 grau de liberdade: P(chi2 >= x) = erfc(sqrt(x / 2))
    p_val = math.erfc(math.sqrt(chi2 / 2.0))
    return chi2, min(1.0, max(0.0, p_val))

def teste_wilcoxon_pareado(difs: List[int]) -> Tuple[float, float]:
    """
    Teste de postos sinalizados de Wilcoxon para amostras grandes pareadas.
    Calcula ranks com empates (ties) e estatística Z assintótica com correção.
    """
    # Remove diferenças nulas
    nao_nulas = [d for d in difs if d != 0]
    n = len(nao_nulas)
    if n == 0:
        return 0.0, 1.0
    
    # Ordena por valor absoluto
    abs_difs = [(abs(d), d, i) for i, d in enumerate(nao_nulas)]
    abs_difs.sort(key=lambda x: x[0])
    
    # Atribui ranks médios em caso de empate
    ranks = [0.0] * n
    idx = 0
    empates = []
    while idx < n:
        j_idx = idx
        while j_idx < n and abs_difs[j_idx][0] == abs_difs[idx][0]:
            j_idx += 1
        tamanho_bloco = j_idx - idx
        rank_medio = (idx + 1 + j_idx) / 2.0
        for k in range(idx, j_idx):
            ranks[k] = rank_medio
        if tamanho_bloco > 1:
            empates.append(tamanho_bloco)
        idx = j_idx
        
    w_pos = sum(ranks[k] for k in range(n) if abs_difs[k][1] > 0)
    w_neg = sum(ranks[k] for k in range(n) if abs_difs[k][1] < 0)
    
    # Média e variância sob H0
    e_w = n * (n + 1.0) / 4.0
    var_w = (n * (n + 1.0) * (2.0 * n + 1.0)) / 24.0
    if empates:
        correcao_empates = sum(t * (t * t - 1.0) for t in empates) / 48.0
        var_w -= correcao_empates
        
    desvio_w = math.sqrt(max(1e-12, var_w))
    # Correção de continuidade
    diff_w = w_pos - e_w
    if diff_w > 0:
        z = (diff_w - 0.5) / desvio_w
    elif diff_w < 0:
        z = (diff_w + 0.5) / desvio_w
    else:
        z = 0.0
        
    p_val = 2.0 * (1.0 - cdf_normal(abs(z)))
    return z, min(1.0, max(0.0, p_val))

def correcao_holm_bonferroni(p_valores: List[float], alfa: float = 0.05) -> List[Dict[str, Any]]:
    """Aplica correção de Holm-Bonferroni sobre uma lista de p-valores."""
    m = len(p_valores)
    ordenados = sorted(enumerate(p_valores), key=lambda x: x[1])
    resultados = [None] * m
    rejeita_atual = True
    
    for rank, (idx_orig, p_val) in enumerate(ordenados):
        limiar = alfa / (m - rank)
        p_ajustado = min(1.0, p_val * (m - rank))
        if p_val > limiar:
            rejeita_atual = False
        significativo = rejeita_atual and (p_val <= limiar)
        resultados[idx_orig] = {
            "p_valor_original": p_val,
            "p_valor_ajustado": p_ajustado,
            "limiar_holm": limiar,
            "significativo_alfa_005": significativo,
        }
    return resultados

def gerar_carteira_aleatoria(semente: int, tamanho: int = 1000) -> List[Tuple[int, ...]]:
    rng = random.Random(semente)
    vistos: Set[Tuple[int, ...]] = set()
    jogos: List[Tuple[int, ...]] = []
    
    pool = list(range(1, 26))
    while len(jogos) < tamanho:
        jg = tuple(sorted(rng.sample(pool, 15)))
        if jg not in vistos:
            vistos.add(jg)
            jogos.append(jg)
    return sorted(jogos)

def simular_carteira(
    mascaras_jogos: List[int],
    mascaras_sorteios: List[int],
) -> Dict[str, Any]:
    """
    Avalia os 100.000 sorteios contra uma carteira de 1.000 jogos em alta performance.
    Coleta contagens por faixa, premiações por concurso e indicadores binários.
    """
    num_sorteios = len(mascaras_sorteios)
    
    # Totais acumulados por faixa de acertos (0 a 15)
    totais_faixa = [0] * 16
    
    # Vetores por concurso
    premios_por_concurso = [0] * num_sorteios  # Faixas 11 a 15
    acertos_14_por_concurso = [0] * num_sorteios
    acertos_13_por_concurso = [0] * num_sorteios
    
    # Indicadores binários por concurso
    tem_premio_geral = [False] * num_sorteios  # N_prem >= 1 (11..15)
    tem_14_acertos = [False] * num_sorteios    # N_14 >= 1
    tem_13_acertos = [False] * num_sorteios    # N_13 >= 1
    tem_15_acertos = [False] * num_sorteios    # N_15 >= 1
    
    for s_idx, mask_s in enumerate(mascaras_sorteios):
        n_prem = 0
        n_14 = 0
        n_13 = 0
        n_15 = 0
        
        for mask_j in mascaras_jogos:
            hits = (mask_j & mask_s).bit_count()
            totais_faixa[hits] += 1
            if hits >= 11:
                n_prem += 1
                if hits == 13:
                    n_13 += 1
                elif hits == 14:
                    n_14 += 1
                elif hits == 15:
                    n_15 += 1
                    
        premios_por_concurso[s_idx] = n_prem
        acertos_14_por_concurso[s_idx] = n_14
        acertos_13_por_concurso[s_idx] = n_13
        
        if n_prem > 0:
            tem_premio_geral[s_idx] = True
        if n_13 > 0:
            tem_13_acertos[s_idx] = True
        if n_14 > 0:
            tem_14_acertos[s_idx] = True
        if n_15 > 0:
            tem_15_acertos[s_idx] = True

    # Estatísticas de N_prem por concurso
    media_premios = sum(premios_por_concurso) / num_sorteios
    var_premios = sum((x - media_premios) ** 2 for x in premios_por_concurso) / (num_sorteios - 1)
    desvio_premios = math.sqrt(var_premios)
    
    return {
        "totais_por_faixa": {
            "acertos_11": totais_faixa[11],
            "acertos_12": totais_faixa[12],
            "acertos_13": totais_faixa[13],
            "acertos_14": totais_faixa[14],
            "acertos_15": totais_faixa[15],
            "total_premios_11_a_15": sum(totais_faixa[11:16]),
        },
        "concursos_com_premio": {
            "geral_ao_menos_1_premio": sum(tem_premio_geral),
            "ao_menos_1_acerto_13": sum(tem_13_acertos),
            "ao_menos_1_acerto_14": sum(tem_14_acertos),
            "ao_menos_1_acerto_15": sum(tem_15_acertos),
            "taxa_cobertura_geral_pct": sum(tem_premio_geral) / num_sorteios * 100.0,
            "taxa_cobertura_14_pct": sum(tem_14_acertos) / num_sorteios * 100.0,
        },
        "estatisticas_premios_concurso": {
            "media": round(media_premios, 6),
            "variancia": round(var_premios, 6),
            "desvio_padrao": round(desvio_premios, 6),
        },
        "vetores_brutos": {
            "premios_por_concurso": premios_por_concurso,
            "tem_premio_geral": tem_premio_geral,
            "tem_14_acertos": tem_14_acertos,
            "tem_13_acertos": tem_13_acertos,
        }
    }

def bootstrap_diferenca_variancia(
    vetor_m4: List[int],
    vetor_ref: List[int],
    num_bootstrap: int = 1000,
    semente: int = 42,
) -> Dict[str, float]:
    """
    Calcula intervalo de confianca de 95% via bootstrap para a diferenca
    de variancias Var(N_M4) - Var(N_Ref).
    """
    n = len(vetor_m4)
    rng = random.Random(semente)
    dif_vars: List[float] = []
    tamanho_amostra = 10_000

    for _ in range(num_bootstrap):
        # Amostragem com reposicao de indices pareados
        idx_amostra = [rng.randrange(n) for _ in range(tamanho_amostra)]
        am_m4 = [vetor_m4[i] for i in idx_amostra]
        am_ref = [vetor_ref[i] for i in idx_amostra]

        m_m4 = sum(am_m4) / tamanho_amostra
        m_ref = sum(am_ref) / tamanho_amostra
        v_m4 = sum((x - m_m4) ** 2 for x in am_m4) / (tamanho_amostra - 1)
        v_ref = sum((x - m_ref) ** 2 for x in am_ref) / (tamanho_amostra - 1)
        dif_vars.append(v_m4 - v_ref)

    dif_vars.sort()
    ic_inf = dif_vars[int(0.025 * len(dif_vars))]
    ic_sup = dif_vars[int(0.975 * len(dif_vars))]

    return {
        "ic_95_inferior": round(ic_inf, 6),
        "ic_95_superior": round(ic_sup, 6),
        "media_diferenca_variancia": round(sum(dif_vars) / len(dif_vars), 6),
    }

def main():
    print("=" * 80)
    print("SIMULACAO COMPARATIVA ESTATISTICA: LOTOFACIL MODO 4 vs 10 CARTEIRAS ALEATORIAS")
    print(f"Escopo: {NUM_SORTEIOS:,} concursos pareados | J = 1.000 jogos | Semente Sorteios = {SEMENTE_SORTEIOS}")
    print("=" * 80)

    # 1. Carregar Carteira Oficial Canônica MODO 4
    caminho_cat = Path("catalogo_lotofacil_10000/lotofacil_carteira_1000.json")
    if not caminho_cat.is_file():
        raise FileNotFoundError(f"Catálogo oficial não encontrado em: {caminho_cat}")
    with open(caminho_cat, "r", encoding="utf-8") as f:
        cat_m4 = json.load(f)
        
    jogos_m4 = [tuple(sorted(jg)) for jg in cat_m4["jogos"]]
    mascaras_m4 = [sum(1 << (d - 1) for d in jg) for jg in jogos_m4]
    sha_m4 = cat_m4["sha256_jogos_canonicos"]
    print(f"Carteira MODO 4 carregada:")
    print(f"  Jogos: {len(jogos_m4)} | Semente: {cat_m4['semente']} | SHA-256: {sha_m4[:16]}...")
    
    # 2. Gerar Painel de 10 Carteiras Aleatórias de Referência
    print(f"\nGerando painel com 10 carteiras aleatórias de referência (sementes {SEMENTES_REFERENCIA})...")
    painel_ref = []
    for s_ref in SEMENTES_REFERENCIA:
        cart_ref = gerar_carteira_aleatoria(s_ref, J)
        masc_ref = [sum(1 << (d - 1) for d in jg) for jg in cart_ref]
        painel_ref.append({
            "semente": s_ref,
            "jogos": cart_ref,
            "mascaras": masc_ref,
        })
    print(f"Painel de referências concluído: 10 carteiras de 1.000 jogos distintos cada.")

    # 3. Gerar os 100.000 Sorteios Pseudoaleatórios
    print(f"\nGerando {NUM_SORTEIOS:,} sorteios pseudoaleatórios com semente {SEMENTE_SORTEIOS}...")
    t0_sort = time.perf_counter()
    rng_sorteios = random.Random(SEMENTE_SORTEIOS)
    pool_dezenas = list(range(1, 26))
    mascaras_sorteios = []
    for _ in range(NUM_SORTEIOS):
        sorteio = rng_sorteios.sample(pool_dezenas, 15)
        m_s = sum(1 << (d - 1) for d in sorteio)
        mascaras_sorteios.append(m_s)
    t1_sort = time.perf_counter()
    print(f"Sorteios gerados em {t1_sort - t0_sort:.3f} s.")

    # 4. Executar Simulação da Carteira MODO 4
    print(f"\nExecutando simulação para Carteira MODO 4...")
    t0_m4 = time.perf_counter()
    res_m4 = simular_carteira(mascaras_m4, mascaras_sorteios)
    t1_m4 = time.perf_counter()
    print(f"Simulação MODO 4 concluída em {t1_m4 - t0_m4:.3f} s.")

    # 5. Executar Simulação para as 10 Carteiras de Referência
    print(f"\nExecutando simulação para as 10 carteiras aleatórias...")
    resultados_ref = []
    for idx_ref, item_ref in enumerate(painel_ref):
        s_ref = item_ref["semente"]
        t0_r = time.perf_counter()
        r_sim = simular_carteira(item_ref["mascaras"], mascaras_sorteios)
        t1_r = time.perf_counter()
        resultados_ref.append({
            "semente": s_ref,
            "tempo_s": round(t1_r - t0_r, 3),
            "resultado": r_sim,
        })
        print(f"  Ref {idx_ref + 1}/10 (Semente {s_ref}): Concluída em {t1_r - t0_r:.3f} s | Total Prêmios: {r_sim['totais_por_faixa']['total_premios_11_a_15']:,}")

    # 6. Confronto Estatístico Pareado (McNemar e Wilcoxon)
    print("\nExecutando testes estatísticos pareados (McNemar e Wilcoxon com Holm-Bonferroni)...")
    comparacoes_pareadas = []
    p_vals_mcnemar_geral = []
    p_vals_mcnemar_14 = []
    p_vals_mcnemar_13 = []
    p_vals_wilcoxon = []

    m4_geral = res_m4["vetores_brutos"]["tem_premio_geral"]
    m4_14 = res_m4["vetores_brutos"]["tem_14_acertos"]
    m4_13 = res_m4["vetores_brutos"]["tem_13_acertos"]
    m4_premios = res_m4["vetores_brutos"]["premios_por_concurso"]

    for item in resultados_ref:
        s_ref = item["semente"]
        r_sim = item["resultado"]
        ref_geral = r_sim["vetores_brutos"]["tem_premio_geral"]
        ref_14 = r_sim["vetores_brutos"]["tem_14_acertos"]
        ref_13 = r_sim["vetores_brutos"]["tem_13_acertos"]
        ref_premios = r_sim["vetores_brutos"]["premios_por_concurso"]

        # Tabelas de contingência McNemar
        # Geral (11..15)
        n10_g = sum(1 for i in range(NUM_SORTEIOS) if m4_geral[i] and not ref_geral[i])
        n01_g = sum(1 for i in range(NUM_SORTEIOS) if not m4_geral[i] and ref_geral[i])
        chi2_g, p_g = p_valor_mcnemar(n10_g, n01_g)
        p_vals_mcnemar_geral.append(p_g)

        # 14 acertos
        n10_14 = sum(1 for i in range(NUM_SORTEIOS) if m4_14[i] and not ref_14[i])
        n01_14 = sum(1 for i in range(NUM_SORTEIOS) if not m4_14[i] and ref_14[i])
        chi2_14, p_14 = p_valor_mcnemar(n10_14, n01_14)
        p_vals_mcnemar_14.append(p_14)

        # 13 acertos
        n10_13 = sum(1 for i in range(NUM_SORTEIOS) if m4_13[i] and not ref_13[i])
        n01_13 = sum(1 for i in range(NUM_SORTEIOS) if not m4_13[i] and ref_13[i])
        chi2_13, p_13 = p_valor_mcnemar(n10_13, n01_13)
        p_vals_mcnemar_13.append(p_13)

        # Teste de Wilcoxon para contagens pareadas de bilhetes premiados
        difs_premios = [m4_premios[i] - ref_premios[i] for i in range(NUM_SORTEIOS)]
        z_w, p_w = teste_wilcoxon_pareado(difs_premios)
        p_vals_wilcoxon.append(p_w)

        # Bootstrap de diferença de variância
        boot = bootstrap_diferenca_variancia(m4_premios, ref_premios, num_bootstrap=2000, semente=s_ref)

        comparacoes_pareadas.append({
            "semente_referencia": s_ref,
            "mcnemar_geral": {"n10_m4_ganha": n10_g, "n01_ref_ganha": n01_g, "chi2": round(chi2_g, 4), "p_valor": p_g},
            "mcnemar_14": {"n10_m4_ganha": n10_14, "n01_ref_ganha": n01_14, "chi2": round(chi2_14, 4), "p_valor": p_14},
            "mcnemar_13": {"n10_m4_ganha": n10_13, "n01_ref_ganha": n01_13, "chi2": round(chi2_13, 4), "p_valor": p_13},
            "wilcoxon_premios": {"z_score": round(z_w, 4), "p_valor": p_w},
            "bootstrap_diferenca_variancia": boot,
        })

    # Correções de Holm-Bonferroni
    corr_mcnemar_geral = correcao_holm_bonferroni(p_vals_mcnemar_geral)
    corr_mcnemar_14 = correcao_holm_bonferroni(p_vals_mcnemar_14)
    corr_mcnemar_13 = correcao_holm_bonferroni(p_vals_mcnemar_13)
    corr_wilcoxon = correcao_holm_bonferroni(p_vals_wilcoxon)

    for i, comp in enumerate(comparacoes_pareadas):
        comp["mcnemar_geral"]["holm"] = corr_mcnemar_geral[i]
        comp["mcnemar_14"]["holm"] = corr_mcnemar_14[i]
        comp["mcnemar_13"]["holm"] = corr_mcnemar_13[i]
        comp["wilcoxon_premios"]["holm"] = corr_wilcoxon[i]

    # 7. Consolidação Estatística do Painel de Referência
    totais_ref_11 = [r["resultado"]["totais_por_faixa"]["acertos_11"] for r in resultados_ref]
    totais_ref_12 = [r["resultado"]["totais_por_faixa"]["acertos_12"] for r in resultados_ref]
    totais_ref_13 = [r["resultado"]["totais_por_faixa"]["acertos_13"] for r in resultados_ref]
    totais_ref_14 = [r["resultado"]["totais_por_faixa"]["acertos_14"] for r in resultados_ref]
    totais_ref_15 = [r["resultado"]["totais_por_faixa"]["acertos_15"] for r in resultados_ref]
    totais_ref_geral = [r["resultado"]["totais_por_faixa"]["total_premios_11_a_15"] for r in resultados_ref]
    
    conc_ref_geral = [r["resultado"]["concursos_com_premio"]["geral_ao_menos_1_premio"] for r in resultados_ref]
    conc_ref_14 = [r["resultado"]["concursos_com_premio"]["ao_menos_1_acerto_14"] for r in resultados_ref]
    conc_ref_13 = [r["resultado"]["concursos_com_premio"]["ao_menos_1_acerto_13"] for r in resultados_ref]
    
    var_ref = [r["resultado"]["estatisticas_premios_concurso"]["variancia"] for r in resultados_ref]

    # Remove vetores brutos para economizar memória e tamanho no JSON final
    del res_m4["vetores_brutos"]
    for r in resultados_ref:
        del r["resultado"]["vetores_brutos"]

    relatorio_completo = {
        "estudo": "SIMULACAO_COMPARATIVA_ESTATISTICA_MODO4_VS_ALEATORIO",
        "parametros_gerais": {
            "num_sorteios_simulados": NUM_SORTEIOS,
            "semente_sorteios": SEMENTE_SORTEIOS,
            "tamanho_carteiras": J,
            "universo_dezenas": 25,
            "dezenas_sorteadas": 15,
            "probabilidade_exata_15_pontos_por_jogo": "1 / 3.268.760",
            "probabilidade_analitica_ao_menos_1_acerto_15_em_1000_jogos": 1000 / 3268760.0,
            "esperanca_15_pontos_em_100k_sorteios": 100_000 * (1000 / 3268760.0),
        },
        "carteira_modo4": {
            "identificador": "LOTOFACIL_MODO4_J1000_CANONICA",
            "sha256_jogos": sha_m4,
            "b_cand": 32,
            "semente": 2027,
            "totais_por_faixa": res_m4["totais_por_faixa"],
            "concursos_com_premio": res_m4["concursos_com_premio"],
            "estatisticas_premios_concurso": res_m4["estatisticas_premios_concurso"],
        },
        "painel_referencia_aleatoria": {
            "quantidade_carteiras": len(SEMENTES_REFERENCIA),
            "sementes_utilizadas": SEMENTES_REFERENCIA,
            "totais_acumulados_faixa": {
                "acertos_11": {"media": sum(totais_ref_11) / 10.0, "min": min(totais_ref_11), "max": max(totais_ref_11)},
                "acertos_12": {"media": sum(totais_ref_12) / 10.0, "min": min(totais_ref_12), "max": max(totais_ref_12)},
                "acertos_13": {"media": sum(totais_ref_13) / 10.0, "min": min(totais_ref_13), "max": max(totais_ref_13)},
                "acertos_14": {"media": sum(totais_ref_14) / 10.0, "min": min(totais_ref_14), "max": max(totais_ref_14)},
                "acertos_15": {"media": sum(totais_ref_15) / 10.0, "min": min(totais_ref_15), "max": max(totais_ref_15)},
                "total_premios": {"media": sum(totais_ref_geral) / 10.0, "min": min(totais_ref_geral), "max": max(totais_ref_geral)},
            },
            "concursos_com_premio": {
                "geral_ao_menos_1_premio": {"media": sum(conc_ref_geral) / 10.0, "min": min(conc_ref_geral), "max": max(conc_ref_geral)},
                "ao_menos_1_acerto_14": {"media": sum(conc_ref_14) / 10.0, "min": min(conc_ref_14), "max": max(conc_ref_14)},
                "ao_menos_1_acerto_13": {"media": sum(conc_ref_13) / 10.0, "min": min(conc_ref_13), "max": max(conc_ref_13)},
            },
            "variancia_premios_concurso": {
                "media": sum(var_ref) / 10.0,
                "min": min(var_ref),
                "max": max(var_ref),
            },
            "resultados_individuais": [
                {
                    "semente": r["semente"],
                    "totais": r["resultado"]["totais_por_faixa"],
                    "concursos": r["resultado"]["concursos_com_premio"],
                    "variancia": r["resultado"]["estatisticas_premios_concurso"]["variancia"],
                }
                for r in resultados_ref
            ]
        },
        "comparacoes_pareadas_detalhadas": comparacoes_pareadas,
    }

    caminho_saida = Path("scratch/resultado_simulacao_comparativa.json")
    with open(caminho_saida, "w", encoding="utf-8") as f:
        json.dump(relatorio_completo, f, indent=2, ensure_ascii=False)
        
    print(f"\nSimulação concluída com sucesso! Relatório salvo em: {caminho_saida}")

if __name__ == "__main__":
    main()
