# -*- coding: utf-8 -*-
"""
Fases 1 e 2 (inicializacao complementar e construcao gulosa guiada) para a
carteira otimizada de ate 10.000 jogos da Lotomania (Ordem 5-R3).
"""

import hashlib
import random
import struct
import time
from typing import Any, Dict, List, Optional, Sequence, Set, Tuple

from lotomania_carteira_10000.auditoria import (
    calcular_coocorrencia_global_bruta,
    verificar_consistencia_lam_e_presenca,
)
from lotomania_carteira_10000.validacao import (
    BLOCOS,
    MASK_80,
    TABELA_COMBINADA,
    TABELA_OVERLAP_PREMIADOS,
    exigir,
    validar_entrada_carteira,
    validar_r1_r9_rapido,
)


def somar_comb_vetor(sv_bytes: bytes) -> int:
    """Soma exata de `(P_>25 << 80) | R_win` para intersecoes `0 <= k <= 49`."""
    s_c = 0
    cnt_fn = sv_bytes.count
    rem = len(sv_bytes) - cnt_fn(50)
    if rem <= 0:
        return 0
    k0 = min(sv_bytes)
    for k_val in range(k0, 50):
        ck = cnt_fn(k_val)
        if ck:
            s_c += ck * TABELA_COMBINADA[k_val]
            rem -= ck
            if rem == 0:
                break
    return s_c


def calcular_q_plus(
    cand_list: Sequence[int], lam: Sequence[Sequence[int]], M_sel: int
) -> int:
    """Calcula a soma quadratica dos desvios positivos de coocorrencia para um candidato."""
    c_intra = -18 * M_sel + 58
    c_inter = -19 * M_sel + 57
    th_intra = (-c_intra) // 76 + 1 if c_intra < 0 else 0
    th_inter = (-c_inter) // 76 + 1 if c_inter < 0 else 0
    tot_q = 0
    for b_idx in range(5):
        base = 10 * b_idx
        for i in range(base, base + 9):
            row_a = lam[cand_list[i]]
            for j in range(i + 1, base + 10):
                lv = row_a[cand_list[j]]
                if lv >= th_intra:
                    d = 76 * lv + c_intra
                    tot_q += d * d
        for i in range(base, base + 10):
            row_a = lam[cand_list[i]]
            for j in range(base + 10, 50):
                lv = row_a[cand_list[j]]
                if lv >= th_inter:
                    d = 76 * lv + c_inter
                    tot_q += d * d
    return tot_q


def _selecionar_bloco_guiado(
    rnd: random.Random,
    u: Sequence[int],
    rem_after: int,
    m_r: List[int],
    f_r: List[int],
    tf: List[int],
    mf: List[int],
    bf: List[int],
    u_min_val: int,
    u_max_val: int,
) -> List[int]:
    need = 10 - len(m_r)
    if need == 0:
        return list(m_r)
    if need == len(f_r):
        return m_r + f_r
    if rem_after == 2:
        target_mand_next = rnd.choice((0, 1, 1, 2))
        k_top = len(m_r) + len(tf) - target_mand_next
        k_top = max(need - len(bf), min(need, len(tf), k_top))
        k_bot = need - k_top
        return m_r + rnd.sample(tf, k_top) + rnd.sample(bf, k_bot)
    if rem_after in (3, 4):
        k_top = min(need, len(tf))
        rem_need = need - k_top
        k_mid = min(rem_need, len(mf))
        k_bot = rem_need - k_mid
        if len(mf) - k_mid < 2 and k_mid > 0 and len(bf) > k_bot and rnd.random() < 0.35:
            k_mid -= 1
            k_bot += 1
        return (
            m_r
            + (rnd.sample(tf, k_top) if k_top < len(tf) else list(tf))
            + (rnd.sample(mf, k_mid) if k_mid < len(mf) else list(mf))
            + (rnd.sample(bf, k_bot) if k_bot < len(bf) else list(bf))
        )
    if rem_after <= 60 and u_max_val > u_min_val:
        s1 = m_r + rnd.sample(f_r, need)
        s2 = m_r + rnd.sample(f_r, need)
        s = s1 if sum(u[x] for x in s1) <= sum(u[x] for x in s2) else s2
        if rem_after <= 30 and u_max_val - u_min_val >= 2:
            s3 = m_r + rnd.sample(f_r, need)
            if sum(u[x] for x in s3) < sum(u[x] for x in s):
                s = s3
        return s
    return m_r + rnd.sample(f_r, need)


def _verificar_bloco_res_ultimo(
    s_set: Set[int],
    bloco_r: Tuple[int, ...],
    u: Sequence[int],
    quota_alvo: int,
    r1_max: int,
    max_add_col: int,
    cols_res: List[int],
    tail_len_res: int,
    last_num_res: int,
) -> Optional[Tuple[List[int], int, int]]:
    s_res = sorted(
        x for x in bloco_r if (quota_alvo - u[x] - (1 if x in s_set else 0)) == 1
    )
    if len(s_res) != 10:
        return None
    if sum(1 for x in s_res if x <= r1_max) < 2 or sum(1 for x in s_res if x <= r1_max) > 8:
        return None
    for x in s_res:
        cols_res[(x - 1) % 10] += 1
    for c_idx in range(10):
        cv_r = cols_res[c_idx]
        if cv_r > 7 or cv_r + max_add_col < 3:
            for x in s_res:
                cols_res[(x - 1) % 10] -= 1
            return None
    consec_r = tail_len_res
    prev_r = last_num_res
    for x in s_res:
        if x == prev_r + 1:
            consec_r += 1
            if consec_r > 4:
                for xr in s_res:
                    cols_res[(xr - 1) % 10] -= 1
                return None
        else:
            consec_r = 1
        prev_r = x
    return s_res, consec_r, prev_r


def _amostrar_candidato_guiado(
    rnd: random.Random,
    u: Sequence[int],
    presenca_bytes_int: Sequence[int],
    sets_lookup: Set[frozenset],
    jogos_selecionados: Sequence[Sequence[int]],
    J: int,
    j_pos: int,
    tau_primario: int,
) -> Optional[List[int]]:
    quota_alvo = J // 2
    rem_after = J - j_pos
    mand: List[List[int]] = [[] for _ in range(5)]
    free: List[List[int]] = [[] for _ in range(5)]
    top_free: List[List[int]] = [[] for _ in range(5)]
    mid_free: List[List[int]] = [[] for _ in range(5)]
    bot_free: List[List[int]] = [[] for _ in range(5)]
    u_min_b = [min(u[x] for x in BLOCOS[r]) for r in range(5)]
    u_max_b = [max(u[x] for x in BLOCOS[r]) for r in range(5)]

    for r in range(5):
        for x in BLOCOS[r]:
            rn = quota_alvo - u[x]
            if rn == rem_after + 1:
                mand[r].append(x)
            elif rn > 0:
                free[r].append(x)
                if rem_after <= 4:
                    if rn == rem_after:
                        top_free[r].append(x)
                    elif rn == 1:
                        bot_free[r].append(x)
                    else:
                        mid_free[r].append(x)

    max_outer = 2500 if rem_after <= 3 else 400
    max_inner = 60 if rem_after <= 3 else 20

    for _ in range(max_outer):
        cols = [0] * 10
        cols_res = [0] * 10
        c_all: List[int] = []
        c_res_all: List[int] = []
        pares = 0
        soma = 0
        tail_len = 0
        last_num = -10
        tail_len_res = 0
        last_num_res = -10
        ok_5 = True

        for r in range(5):
            rem_blocks = 4 - r
            max_add_col = 2 * rem_blocks
            r1_max = 20 * r + 10
            found_b = False
            for _ in range(max_inner):
                s = _selecionar_bloco_guiado(
                    rnd,
                    u,
                    rem_after,
                    mand[r],
                    free[r],
                    top_free[r],
                    mid_free[r],
                    bot_free[r],
                    u_min_b[r],
                    u_max_b[r],
                )
                r1 = sum(1 for x in s if x <= r1_max)
                if r1 < 2 or r1 > 8:
                    continue
                s.sort()
                consec = tail_len
                prev = last_num
                c_ok = True
                for x in s:
                    if x == prev + 1:
                        consec += 1
                        if consec > 4:
                            c_ok = False
                            break
                    else:
                        consec = 1
                    prev = x
                if not c_ok:
                    continue

                col_ok = True
                for x in s:
                    cols[(x - 1) % 10] += 1
                for c_idx in range(10):
                    cv = cols[c_idx]
                    if cv > 7 or cv + max_add_col < 3:
                        col_ok = False
                        break
                if not col_ok:
                    if rem_after > 4:
                        break
                    for x in s:
                        cols[(x - 1) % 10] -= 1
                    continue

                if rem_after == 1:
                    res_chk = _verificar_bloco_res_ultimo(
                        set(s),
                        BLOCOS[r],
                        u,
                        quota_alvo,
                        r1_max,
                        max_add_col,
                        cols_res,
                        tail_len_res,
                        last_num_res,
                    )
                    if res_chk is None:
                        for x in s:
                            cols[(x - 1) % 10] -= 1
                        continue
                    s_res, tail_len_res, last_num_res = res_chk
                    c_res_all.extend(s_res)

                tail_len = consec
                last_num = prev
                c_all.extend(s)
                pares += sum(1 for x in s if (x & 1) == 0)
                soma += sum(s)
                found_b = True
                break
            if not found_b:
                ok_5 = False
                break

        if ok_5 and 18 <= pares <= 32 and 2350 <= soma <= 2700:
            fs = frozenset(c_all)
            if fs in sets_lookup:
                continue
            if rem_after == 1:
                if not validar_r1_r9_rapido(c_res_all):
                    continue
                fs_res = frozenset(c_res_all)
                if fs_res in sets_lookup or fs_res == fs:
                    continue
                if len(fs.intersection(fs_res)) > tau_primario:
                    continue
                if jogos_selecionados:
                    sv_res = sum(presenca_bytes_int[n] for n in c_res_all).to_bytes(
                        len(jogos_selecionados), "little"
                    )
                    if max(sv_res) > tau_primario:
                        continue
            return c_all
    return None


def inicializar_carteira_fase12(
    seed: int = 330001,
    J: int = 10000,
    tau_primario: int = 35,
    alpha_25: float = 30.0,
    alpha_win: float = 1.0,
    alpha_1: float = 0.08,
    alpha_2: float = 0.25,
    gamma_plus: float = 0.02,
    batch0: int = 80,
) -> Tuple[random.Random, Dict[str, Any]]:
    """
    Executa as Fases 1 (par complementar inicial) e 2 (construcao gulosa com travas
    marginais R1-R12) e prepara o estado canonico para a Fase 3.
    """
    validar_entrada_carteira(J=J, seed=seed, max_tentativas_f3=0, tau_primario=tau_primario)
    t0 = time.perf_counter()
    rnd = random.Random(seed)
    u = [0] * 101
    lam = [[0] * 101 for _ in range(101)]
    vec_lam = [0] * 101
    bit_lam_single = [1 << (32 * a) for a in range(101)]
    presenca_bytes_int = [0] * 101
    jogos_selecionados: List[List[int]] = []
    sets_lookup: Set[frozenset] = set()

    def adicionar_bilhete(jg_sorted: List[int]) -> None:
        idx = len(jogos_selecionados)
        bit = 1 << (8 * idx)
        mask_t = 0
        for n in jg_sorted:
            u[n] += 1
            presenca_bytes_int[n] |= bit
            mask_t |= bit_lam_single[n]
        for i in range(50):
            a = jg_sorted[i]
            vec_lam[a] += mask_t - bit_lam_single[a]
            row_a = lam[a]
            for j_idx in range(i + 1, 50):
                b = jg_sorted[j_idx]
                row_a[b] += 1
                lam[b][a] += 1
        jogos_selecionados.append(jg_sorted)
        sets_lookup.add(frozenset(jg_sorted))

    quota_alvo = J // 2

    while True:
        j1 = _amostrar_candidato_guiado(
            rnd, u, presenca_bytes_int, sets_lookup, jogos_selecionados, J, 1, tau_primario
        )
        exigir(j1 is not None, "Falha ao amostrar jogo inicial j1")
        j1_set = set(j1)
        j2 = [x for x in range(1, 101) if x not in j1_set]
        if validar_r1_r9_rapido(j2):
            adicionar_bilhete(j1)
            adicionar_bilhete(j2)
            break

    escala_j2 = 1225.0 * (76.0 ** 2)
    contingencias = 0

    for j_pos in range(3, J + 1):
        M_sel = len(jogos_selecionados)
        if j_pos == J:
            c_final = sorted([x for x in range(1, 101) if quota_alvo - u[x] == 1])
            exigir(
                len(c_final) == 50 and validar_r1_r9_rapido(c_final),
                "Jogo final de fechamento marginal violou R1-R9",
            )
            fs_final = frozenset(c_final)
            exigir(fs_final not in sets_lookup, "Jogo final violou unicidade R10")
            sv_fin = sum(presenca_bytes_int[n] for n in c_final).to_bytes(M_sel, "little")
            exigir(
                max(sv_fin) <= tau_primario,
                f"Jogo final excedeu teto k_max <= {tau_primario}",
            )
            adicionar_bilhete(c_final)
            continue

        u_spread_global = max(
            max(u[x] for x in BLOCOS[r]) - min(u[x] for x in BLOCOS[r]) for r in range(5)
        )
        if (J - j_pos) <= 60:
            alpha_1_eff = alpha_1 * 40.0
        elif u_spread_global >= 8:
            alpha_1_eff = alpha_1 * 4.0
        else:
            alpha_1_eff = alpha_1

        melhor_cand: Optional[List[int]] = None
        menor_score = float("inf")
        avaliados = 0
        tentativas_etapa = 0
        vistos: Set[frozenset] = set()

        for lote in range(8):
            alvo_lote = batch0 if lote == 0 else batch0 * (lote + 1)
            max_tent_lote = alvo_lote * 6
            cands_lote: List[Tuple[float, float, List[int]]] = []
            while avaliados < alvo_lote and tentativas_etapa < max_tent_lote:
                cand_list = _amostrar_candidato_guiado(
                    rnd,
                    u,
                    presenca_bytes_int,
                    sets_lookup,
                    jogos_selecionados,
                    J,
                    j_pos,
                    tau_primario,
                )
                if cand_list is None:
                    break
                tentativas_etapa += 1
                fs = frozenset(cand_list)
                if fs in vistos:
                    continue
                vistos.add(fs)

                sv = sum(presenca_bytes_int[n] for n in cand_list).to_bytes(M_sel, "little")
                k1 = max(sv)
                if k1 > tau_primario:
                    continue
                avaliados += 1
                k0 = min(sv)
                rem = M_sel
                soma_comb = 0
                cnt = sv.count
                for k in range(k0, k1):
                    ck = cnt(k)
                    if ck:
                        soma_comb += ck * TABELA_COMBINADA[k]
                        rem -= ck
                soma_comb += rem * TABELA_COMBINADA[k1]
                r_win = soma_comb & MASK_80
                p_25 = soma_comb >> 80

                d_s1 = 2.0 * sum(u[n] for n in cand_list) - 50.0 * M_sel + 25.0
                sv_lam = sum(vec_lam[b] for b in cand_list).to_bytes(404, "little")
                unp_lam = struct.unpack("<101I", sv_lam)
                sum_lam_c = sum(unp_lam[a] for a in cand_list) // 2
                sum_d_ab = 76 * sum_lam_c - 23050 * M_sel
                d_phi2_global = 152 * sum_d_ab + 5323800

                base_score = (
                    alpha_25 * (p_25 / M_sel)
                    + alpha_win * (r_win / (M_sel * 1e16))
                    + alpha_1_eff * (d_s1 / 50.0)
                    + alpha_2 * (d_phi2_global / escala_j2)
                )
                cands_lote.append((base_score, d_s1, cand_list))

            if cands_lote:
                if (J - j_pos) <= 45:
                    cands_lote.sort(key=lambda item: (item[1], item[0]))
                    cands_lote = cands_lote[: max(4, len(cands_lote) // 6)]
                elif (J - j_pos) <= 90 and u_spread_global >= 3:
                    cands_neg = [item for item in cands_lote if item[1] <= 0.0]
                    if cands_neg:
                        cands_lote = cands_neg

                cands_lote.sort(key=lambda item: item[0])
                for base_sc, _, cand_list in cands_lote:
                    if base_sc >= menor_score:
                        break
                    q_plus = calcular_q_plus(cand_list, lam, M_sel)
                    sc_total = base_sc + alpha_2 * (gamma_plus * q_plus / escala_j2)
                    if sc_total < menor_score:
                        menor_score = sc_total
                        melhor_cand = cand_list
                break

        if melhor_cand is None:
            contingencias += 1
            raise RuntimeError(f"Contingencia em j_pos={j_pos}")
        adicionar_bilhete(melhor_cand)

    tempo_f12 = time.perf_counter() - t0
    cooc_pre = calcular_coocorrencia_global_bruta(lam, J)

    freq_k = [0] * 51
    pares_34_35: List[Tuple[int, int]] = []
    pares_32_33: List[Tuple[int, int]] = []
    for i in range(J - 1):
        sv = sum(presenca_bytes_int[n] for n in jogos_selecionados[i]).to_bytes(
            J, "little"
        )[i + 1 :]
        k0, k1 = min(sv), max(sv)
        if k1 >= 32:
            for k_t in range(k1, 31, -1):
                start_pos = 0
                target_list = pares_34_35 if k_t >= 34 else pares_32_33
                while True:
                    pos = sv.find(k_t, start_pos)
                    if pos == -1:
                        break
                    target_list.append((i, i + 1 + pos))
                    start_pos = pos + 1
        rem = len(sv)
        cnt = sv.count
        for k in range(k0, k1):
            ck = cnt(k)
            if ck:
                freq_k[k] += ck
                rem -= ck
        freq_k[k1] += rem

    k_star = max(k for k in range(51) if freq_k[k] > 0)
    teto_fase3 = min(tau_primario, k_star)
    p25_pre = sum(((k - 25) ** 2) * freq_k[k] for k in range(26, 51))
    rwin_pre = sum(TABELA_OVERLAP_PREMIADOS[k] * freq_k[k] for k in range(51))
    verificar_consistencia_lam_e_presenca(jogos_selecionados, lam, presenca_bytes_int, u)

    estado_canonico_buf = bytearray(n for jg in jogos_selecionados for n in jg)
    sha_init = hashlib.sha256(estado_canonico_buf).hexdigest()
    pre_fase3 = {
        "k_star": k_star,
        "teto_fase3": teto_fase3,
        "P_gt_25": p25_pre,
        "R_win": str(rwin_pre),
        "phi2": cooc_pre["phi2"],
        "q_global_plus": cooc_pre["q_global_plus"],
        "d_max": cooc_pre["d_max"],
        "cnt_dmax": cooc_pre["cnt_dmax"],
        "sigma_intra": cooc_pre["sigma_intra"],
        "sigma_inter": cooc_pre["sigma_inter"],
        "sha256_estado_inicial_fase3": sha_init,
    }
    estado: Dict[str, Any] = {
        "seed": seed,
        "J": J,
        "contingencias": contingencias,
        "tempo_fase12_s": tempo_f12,
        "pre_fase3": pre_fase3,
        "jogos_selecionados": jogos_selecionados,
        "lam": lam,
        "presenca_bytes_int": presenca_bytes_int,
        "sets_lookup": sets_lookup,
        "u": u,
        "estado_canonico_buf": estado_canonico_buf,
        "sha256_estado_atual": sha_init,
        "sha256_ultimo_swap": sha_init,
        "pares_34_35": pares_34_35,
        "pares_32_33": pares_32_33,
        "k_star": k_star,
        "teto_fase3": teto_fase3,
        "current_phi2": cooc_pre["phi2"],
        "current_q_plus": cooc_pre["q_global_plus"],
        "current_d_max": cooc_pre["d_max"],
        "cnt_d_max": cooc_pre["cnt_dmax"],
        "current_p25": p25_pre,
        "current_rwin": rwin_pre,
        "swaps_aceitos": 0,
        "recalculos_dmax_queda": 0,
        "rej_sem_par_xy": 0,
        "rej_phi2": 0,
        "rej_r1_r10": 0,
        "rej_q_plus_ou_dmax": 0,
        "rej_kmax": 0,
        "rej_p25_rwin": 0,
        "rej_excecao": 0,
        "cadeia_hashes_integra": True,
        "amostra_primeiros_swaps": [],
        "amostra_ultimos_swaps": [],
    }
    return rnd, estado
