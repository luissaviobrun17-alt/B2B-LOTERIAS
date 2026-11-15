# -*- coding: utf-8 -*-
"""
Auditoria matematica independente e verificadores de forca bruta para
`lotomania_carteira_10000`.
"""

import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from lotomania_carteira_10000.validacao import (
    BLOCK_OF,
    CLAUSULA_OBRIGATORIA,
    FAIXAS_PREMIACAO_RELATORIO,
    TABELA_OVERLAP_FAIXAS,
    TABELA_OVERLAP_PREMIADOS,
    classificar_homologacao_kmax,
    exigir,
    sha256_matriz_incidencia_canonica,
    validar_bilhete_individual,
)


def verificar_consistencia_lam_e_presenca(
    jogos_selecionados: Sequence[Sequence[int]],
    lam: Sequence[Sequence[int]],
    presenca_bytes_int: Sequence[int],
    u_vec: Sequence[int],
) -> None:
    """Confronta integralmente `lam`, `presenca_bytes_int` e `u` por reconstrucao bruta."""
    J = len(jogos_selecionados)
    lam_chk = [[0] * 101 for _ in range(101)]
    u_chk = [0] * 101
    pres_chk = [0] * 101
    for idx, jg in enumerate(jogos_selecionados):
        bit = 1 << (8 * idx)
        for a in range(50):
            na = jg[a]
            u_chk[na] += 1
            pres_chk[na] |= bit
            row_a = lam_chk[na]
            for b in range(a + 1, 50):
                nb = jg[b]
                row_a[nb] += 1
    for a in range(1, 101):
        exigir(u_chk[a] == u_vec[a], f"Marginal u[{a}] divergente")
        exigir(
            pres_chk[a] == presenca_bytes_int[a],
            f"presenca_bytes_int[{a}] divergente",
        )
        for b in range(a + 1, 101):
            exigir(
                lam_chk[a][b] == lam[a][b] and lam_chk[a][b] == lam[b][a],
                f"lam[{a}][{b}] divergente",
            )
    exigir(J >= 0, "Tamanho J negativo inesperado")


def calcular_coocorrencia_global_bruta(
    lam_mat: Sequence[Sequence[int]], M_val: int
) -> Dict[str, Any]:
    """Calcula Phi_2, Q^+_global, D_max, cnt_dmax e sigmas sobre todos os 4.950 pares."""
    intra_v: List[int] = []
    inter_v: List[int] = []
    phi2_val = 0
    q_plus_global = 0
    d_max_val = 0
    cnt_dmax = 0
    for a in range(1, 101):
        ba = BLOCK_OF[a]
        row_a = lam_mat[a]
        for b in range(a + 1, 101):
            bb = BLOCK_OF[b]
            lv = row_a[b]
            if ba == bb:
                intra_v.append(lv)
                q_ab = 18
            else:
                inter_v.append(lv)
                q_ab = 19
            d_ab = 76 * lv - q_ab * M_val
            abs_d = abs(d_ab)
            d_sq = d_ab * d_ab
            phi2_val += d_sq
            if d_ab > 0:
                q_plus_global += d_sq
            if abs_d > d_max_val:
                d_max_val = abs_d
                cnt_dmax = 1
            elif abs_d == d_max_val:
                cnt_dmax += 1
    m_in = sum(intra_v) / len(intra_v)
    s_in = math.sqrt(sum((v - m_in) ** 2 for v in intra_v) / len(intra_v))
    m_out = sum(inter_v) / len(inter_v)
    s_out = math.sqrt(sum((v - m_out) ** 2 for v in inter_v) / len(inter_v))
    return {
        "phi2": phi2_val,
        "q_global_plus": q_plus_global,
        "d_max": d_max_val,
        "cnt_dmax": cnt_dmax,
        "media_intra": m_in,
        "sigma_intra": s_in,
        "min_intra": min(intra_v),
        "max_intra": max(intra_v),
        "media_inter": m_out,
        "sigma_inter": s_out,
        "min_inter": min(inter_v),
        "max_inter": max(inter_v),
    }


def calcular_metricas_intersecao_bruta(
    presenca_bytes_int: Sequence[int],
    jogos_selecionados: Sequence[Sequence[int]],
) -> Tuple[List[int], int, int, int]:
    """Recalcula globalmente freq_k, k_max, P_gt_25 e R_win sobre C(J, 2) pares."""
    J = len(jogos_selecionados)
    freq_k = [0] * 51
    buf: List[bytes] = []
    for i in range(J - 1):
        sv = sum(presenca_bytes_int[n] for n in jogos_selecionados[i]).to_bytes(
            J, "little"
        )[i + 1 :]
        buf.append(sv)
        if len(buf) == 250 or i == J - 2:
            bloco = b"".join(buf)
            rem = len(bloco)
            if rem > 0:
                k0, k1 = min(bloco), max(bloco)
                cnt = bloco.count
                for k in range(k0, k1):
                    ck = cnt(k)
                    if ck:
                        freq_k[k] += ck
                        rem -= ck
                freq_k[k1] += rem
            buf.clear()
    k_max = max(k for k in range(51) if freq_k[k] > 0)
    p_25 = sum(((k - 25) ** 2) * freq_k[k] for k in range(26, 51))
    r_win = sum(TABELA_OVERLAP_PREMIADOS[k] * freq_k[k] for k in range(51))
    return freq_k, k_max, p_25, r_win


def calcular_delta_phi2_exato_candidato(
    tu: Sequence[int],
    tw: Sequence[int],
    x: int,
    y: int,
    lam: Sequence[Sequence[int]],
) -> int:
    """
    Calcula o incremento global exato `Delta Phi_2_global` de um 2-Swap `(x in tu\\tw <-> y in tw\\tu)`
    pela identidade fechada em `lam`, independentemente dos 4.950 pares inalterados.
    """
    tu_set = set(tu)
    tw_set = set(tw)
    exigir(x in tu_set and x not in tw_set, "x deve pertencer exclusivamente a tu")
    exigir(y in tw_set and y not in tu_set, "y deve pertencer exclusivamente a tw")
    exigir(BLOCK_OF[x] == BLOCK_OF[y], "x e y devem pertencer ao mesmo bloco")

    u_diff = [z for z in tu if z not in tw_set]
    w_diff = [z for z in tw if z not in tu_set]
    const_m = 2 * (len(u_diff) - 1)
    rx = lam[x]
    ry = lam[y]
    sx = sum(rx[z] for z in w_diff) - sum(rx[z] for z in u_diff if z != x)
    sy = sum(ry[z] for z in u_diff) - sum(ry[z] for z in w_diff if z != y)
    d_div = const_m + sx + sy - 2 * rx[y]
    return 11552 * d_div


def auditar_carteira_completa(
    jogos: Sequence[Sequence[int]],
    *,
    teto_kmax: int = 35,
    baseline_ordem4: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Executa auditoria combinatoria independente completa (R1-R12, matriz Lambda
    de 4.950 pares, histograma de intersecoes, identidade de contagem dupla e
    cobertura hipergeometrica por faixa).
    """
    J = len(jogos)
    exigir(J >= 2 and J % 2 == 0, f"Carteira deve ter J par >= 2 (recebido {J})")

    uso = [0] * 101
    r1_r9_ok = 0
    sets_unicos = set()
    pres = [0] * 101
    lam = [[0] * 101 for _ in range(101)]

    for idx, jg in enumerate(jogos):
        ok_jg, _ = validar_bilhete_individual(jg)
        if ok_jg:
            r1_r9_ok += 1
        s_jg = sorted(jg)
        sets_unicos.add(frozenset(s_jg))
        bit = 1 << (8 * idx)
        for i in range(50):
            a = s_jg[i]
            uso[a] += 1
            pres[a] |= bit
            row_a = lam[a]
            for j_col in range(i + 1, 50):
                b = s_jg[j_col]
                row_a[b] += 1
                lam[b][a] += 1

    freq_k, k_max, p_25, r_win = calcular_metricas_intersecao_bruta(pres, jogos)
    k_min = next(k for k in range(51) if freq_k[k] > 0)
    exigir(
        sum(freq_k) == J * (J - 1) // 2,
        "Soma do histograma f(k) diverge de C(J, 2)",
    )

    cooc = calcular_coocorrencia_global_bruta(lam, J)
    sum_k_sq = sum((k * k) * freq_k[k] for k in range(51))
    sum_dc_pairs = sum(
        lam[a][b] * (lam[a][b] - 1) for a in range(1, 101) for b in range(a + 1, 101)
    )
    sum_dc_diag = sum(uso[n] * (uso[n] - 1) // 2 for n in range(1, 101))
    identidade_dupla_ok = sum_k_sq == sum_dc_pairs + sum_dc_diag

    total_sorteios = math.comb(100, 20)
    cobertura_por_faixa: Dict[str, Any] = {}
    for t in FAIXAS_PREMIACAO_RELATORIO:
        cap_ind = math.comb(50, t) * math.comb(50, 20 - t)
        cap_ag = J * cap_ind
        red = sum(freq_k[k] * TABELA_OVERLAP_FAIXAS[t][k] for k in range(51) if freq_k[k])
        cota_inf = max(0, cap_ag - red)
        razao_pct = (cota_inf / cap_ag * 100.0) if cap_ag > 0 else 100.0
        cobertura_por_faixa[str(t)] = {
            "redundancia_pares_exata": str(red),
            "cota_inferior_bonferroni": str(cota_inf),
            "razao_cota_bonferroni_pct": round(razao_pct, 6),
            "probabilidade_cota_inferior": cota_inf / total_sorteios,
        }

    inter_par_inicial = len(set(jogos[0]).intersection(jogos[1]))
    u_min = min(uso[1:])
    u_max = max(uso[1:])
    aprovacao_restricoes = {
        "r1_r9_integral_ok": r1_r9_ok == J,
        "r10_unicidade_ok": len(sets_unicos) == J,
        "r11_espelho_inicial_disjunto_ok": inter_par_inicial == 0,
        "r11_kmax_teto_ok": k_max <= teto_kmax,
        "r12_marginais_exatas_ok": u_min == J // 2 and u_max == J // 2,
        "identidade_contagem_dupla_ok": identidade_dupla_ok,
    }
    aprovacao_restricoes["todas_travas_aprovadas"] = all(aprovacao_restricoes.values())

    resultado: Dict[str, Any] = {
        "clausula_obrigatoria": CLAUSULA_OBRIGATORIA,
        "J": J,
        "homologacao_kmax": classificar_homologacao_kmax(k_max),
        "aprovacao_restricoes": aprovacao_restricoes,
        "fechamento": {
            "total_jogos": J,
            "validos_r1_r9": r1_r9_ok,
            "unicos_r10": len(sets_unicos),
            "intersecao_par_inicial": inter_par_inicial,
            "u_min": u_min,
            "u_max": u_max,
            "sigma_u": math.sqrt(sum((uso[n] - J / 2.0) ** 2 for n in range(1, 101)) / 100.0),
            "k_min": k_min,
            "k_max": k_max,
            "k_eq_35": freq_k[35],
            "k_ge_36": sum(freq_k[k] for k in range(36, 51)),
            "P_gt_25": p_25,
            "R_win": str(r_win),
            "sha256_matriz_incidencia_100": sha256_matriz_incidencia_canonica(jogos),
        },
        "coocorrencia_4950": cooc,
        "histograma_k": {str(k): freq_k[k] for k in range(51)},
        "cobertura_por_faixa": cobertura_por_faixa,
    }

    if baseline_ordem4 is not None:
        base_rwin = int(baseline_ordem4["R_win"])
        base_p25 = int(baseline_ordem4["P_gt_25"])
        resultado["comparacao_baseline_ordem4"] = {
            "P_gt_25": {"otimizado": p_25, "baseline": base_p25, "diff": p_25 - base_p25},
            "R_win": {
                "otimizado": str(r_win),
                "baseline": str(base_rwin),
                "diff": str(r_win - base_rwin),
            },
            "k_max": {"otimizado": k_max, "baseline": baseline_ordem4["k_max"]},
            "sigma_intra": {
                "otimizado": round(cooc["sigma_intra"], 4),
                "baseline": baseline_ordem4["sigma_intra"],
            },
            "sigma_inter": {
                "otimizado": round(cooc["sigma_inter"], 4),
                "baseline": baseline_ordem4["sigma_inter"],
            },
        }
    return resultado
