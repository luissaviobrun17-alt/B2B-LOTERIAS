# -*- coding: utf-8 -*-
"""
Fase 3 da Ordem 5-R3: otimizacao incremental atomica por 2-Swap (`S1_atual_top8`)
com orcamento experimental homologado de 1.080.000 tentativas para J=10.000.
"""

import copy
import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Sequence, TextIO, Tuple

from lotomania_carteira_10000.auditoria import (
    calcular_coocorrencia_global_bruta,
    calcular_metricas_intersecao_bruta,
    verificar_consistencia_lam_e_presenca,
)
from lotomania_carteira_10000.construtiva import (
    inicializar_carteira_fase12,
    somar_comb_vetor,
)
from lotomania_carteira_10000.validacao import (
    BLOCOS,
    BLOCK_OF,
    CLAUSULA_OBRIGATORIA,
    ESTRATEGIA_FASE3_PADRAO,
    MASK_80,
    VERSAO_ALGORITMO,
    calcular_hashes_certificados,
    classificar_homologacao_kmax,
    exigir,
    validar_entrada_carteira,
    validar_r1_r9_rapido,
    validar_trilha_jsonl_em_disco,
)


class FalhaInjetadaAtomica(Exception):
    """Excecao controlada para validar rollback atomico sob falha injetada."""


def capturar_snapshot_estado(estado: Dict[str, Any]) -> Dict[str, Any]:
    """Captura instantaneo completo do estado mutavel da Fase 3."""
    return {
        "jogos_selecionados": copy.deepcopy(estado["jogos_selecionados"]),
        "lam": copy.deepcopy(estado["lam"]),
        "presenca_bytes_int": list(estado["presenca_bytes_int"]),
        "sets_lookup": set(estado["sets_lookup"]),
        "u": list(estado["u"]),
        "estado_canonico_buf": bytes(estado["estado_canonico_buf"]),
        "current_phi2": estado["current_phi2"],
        "current_q_plus": estado["current_q_plus"],
        "current_d_max": estado["current_d_max"],
        "cnt_d_max": estado["cnt_d_max"],
        "current_p25": estado["current_p25"],
        "current_rwin": estado["current_rwin"],
        "sha256_estado_atual": estado["sha256_estado_atual"],
        "sha256_ultimo_swap": estado["sha256_ultimo_swap"],
        "swaps_aceitos": estado["swaps_aceitos"],
    }


def comparar_estado_snapshot(estado: Dict[str, Any], snap: Dict[str, Any]) -> List[str]:
    """Compara estado mutavel atual contra um instantaneo imutavel anterior."""
    divergencias: List[str] = []
    if estado["jogos_selecionados"] != snap["jogos_selecionados"]:
        divergencias.append("jogos_selecionados")
    if estado["lam"] != snap["lam"]:
        divergencias.append("lam")
    if estado["presenca_bytes_int"] != snap["presenca_bytes_int"]:
        divergencias.append("presenca_bytes_int")
    if estado["sets_lookup"] != snap["sets_lookup"]:
        divergencias.append("sets_lookup")
    if estado["u"] != snap["u"]:
        divergencias.append("u")
    if bytes(estado["estado_canonico_buf"]) != snap["estado_canonico_buf"]:
        divergencias.append("estado_canonico_buf")
    for campo in (
        "current_phi2",
        "current_q_plus",
        "current_d_max",
        "cnt_d_max",
        "current_p25",
        "current_rwin",
        "sha256_estado_atual",
        "sha256_ultimo_swap",
        "swaps_aceitos",
    ):
        if estado[campo] != snap[campo]:
            divergencias.append(campo)
    return divergencias


def avaliar_delta_q_dmax_local(
    x: int,
    y: int,
    u_diff: Sequence[int],
    w_diff: Sequence[int],
    lam: Sequence[Sequence[int]],
    J_total: int,
    r_block: int,
    current_d_max: int,
) -> Tuple[bool, int, int]:
    """
    Calcula o delta exato de `Q^+_global(Lambda)`, garante teto `<= current_d_max` e
    retorna a variacao exata da contagem de pares no pico `current_d_max`.
    """
    row_x = lam[x]
    row_y = lam[y]
    j_18 = 18 * J_total
    j_19 = 19 * J_total
    d_q_plus = 0
    delta_cnt_dmax = 0

    for z in u_diff:
        if z == x:
            continue
        q_J = j_18 if BLOCK_OF[z] == r_block else j_19

        d_old_xz = 76 * row_x[z] - q_J
        d_new_xz = d_old_xz - 76
        abs_new_xz = abs(d_new_xz)
        if abs_new_xz > current_d_max:
            return False, 0, 0
        if abs(d_old_xz) == current_d_max:
            delta_cnt_dmax -= 1
        if abs_new_xz == current_d_max:
            delta_cnt_dmax += 1
        if d_old_xz > 0:
            d_q_plus -= d_old_xz * d_old_xz
        if d_new_xz > 0:
            d_q_plus += d_new_xz * d_new_xz

        d_old_yz = 76 * row_y[z] - q_J
        d_new_yz = d_old_yz + 76
        abs_new_yz = abs(d_new_yz)
        if abs_new_yz > current_d_max:
            return False, 0, 0
        if abs(d_old_yz) == current_d_max:
            delta_cnt_dmax -= 1
        if abs_new_yz == current_d_max:
            delta_cnt_dmax += 1
        if d_old_yz > 0:
            d_q_plus -= d_old_yz * d_old_yz
        if d_new_yz > 0:
            d_q_plus += d_new_yz * d_new_yz

    for z in w_diff:
        if z == y:
            continue
        q_J = j_18 if BLOCK_OF[z] == r_block else j_19

        d_old_yz = 76 * row_y[z] - q_J
        d_new_yz = d_old_yz - 76
        abs_new_yz = abs(d_new_yz)
        if abs_new_yz > current_d_max:
            return False, 0, 0
        if abs(d_old_yz) == current_d_max:
            delta_cnt_dmax -= 1
        if abs_new_yz == current_d_max:
            delta_cnt_dmax += 1
        if d_old_yz > 0:
            d_q_plus -= d_old_yz * d_old_yz
        if d_new_yz > 0:
            d_q_plus += d_new_yz * d_new_yz

        d_old_xz = 76 * row_x[z] - q_J
        d_new_xz = d_old_xz + 76
        abs_new_xz = abs(d_new_xz)
        if abs_new_xz > current_d_max:
            return False, 0, 0
        if abs(d_old_xz) == current_d_max:
            delta_cnt_dmax -= 1
        if abs_new_xz == current_d_max:
            delta_cnt_dmax += 1
        if d_old_xz > 0:
            d_q_plus -= d_old_xz * d_old_xz
        if d_new_xz > 0:
            d_q_plus += d_new_xz * d_new_xz

    return True, d_q_plus, delta_cnt_dmax


def _recalcular_dmax_global(lam: Sequence[Sequence[int]], J: int) -> Tuple[int, int]:
    dmax_new = 0
    cnt_new = 0
    j_18 = 18 * J
    j_19 = 19 * J
    for a in range(1, 101):
        ba = BLOCK_OF[a]
        ra = lam[a]
        for b in range(a + 1, 101):
            ad = abs(76 * ra[b] - (j_18 if BLOCK_OF[b] == ba else j_19))
            if ad > dmax_new:
                dmax_new = ad
                cnt_new = 1
            elif ad == dmax_new:
                cnt_new += 1
    return dmax_new, cnt_new


def avaliar_e_aplicar_swap_fase3(
    estado: Dict[str, Any],
    u_idx: int,
    v_idx: int,
    w_idx: int,
    r_block: int,
    proposta_idx: int,
    falha_injetada: Optional[str] = None,
    auditar_100pct_swaps: bool = True,
    auditar_intersecoes_bruto: bool = False,
    trilha_fp: Optional[TextIO] = None,
) -> Tuple[str, Optional[Dict[str, Any]]]:
    """
    Avalia um movimento 2-Swap pelo seletor `S1_atual_top8`, valida R1-R12 e travas
    monotonicas e aplica commit estritamente atomico (reversao integral em falha).
    """
    sha_antes_proposta = estado["sha256_estado_atual"]
    J = estado["J"]
    jogos_selecionados = estado["jogos_selecionados"]
    lam = estado["lam"]
    presenca = estado["presenca_bytes_int"]
    sets_lookup = estado["sets_lookup"]
    teto_fase3 = estado["teto_fase3"]
    current_d_max = estado["current_d_max"]

    if u_idx < 2 or w_idx < 2 or u_idx == w_idx:
        estado["rej_r1_r10"] += 1
        return "rej_r1_r10", None

    tu = jogos_selecionados[u_idx]
    tw = jogos_selecionados[w_idx]
    tu_set = set(tu)
    tw_set = set(tw)
    b_nums = BLOCOS[r_block]
    u_diff = [z for z in tu if z not in tw_set]
    w_diff = [z for z in tw if z not in tu_set]

    if u_idx != v_idx:
        tv_set = set(jogos_selecionados[v_idx])
        diff_u = [x for x in u_diff if b_nums[0] <= x <= b_nums[-1] and x in tv_set]
        diff_w = [y for y in w_diff if b_nums[0] <= y <= b_nums[-1] and y not in tv_set]
        if not diff_u or not diff_w:
            diff_u = [x for x in u_diff if b_nums[0] <= x <= b_nums[-1]]
            diff_w = [y for y in w_diff if b_nums[0] <= y <= b_nums[-1]]
    else:
        diff_u = [x for x in u_diff if b_nums[0] <= x <= b_nums[-1]]
        diff_w = [y for y in w_diff if b_nums[0] <= y <= b_nums[-1]]

    if not diff_u or not diff_w:
        estado["rej_sem_par_xy"] += 1
        return "rej_sem_par_xy", None

    const_m = 2 * (len(u_diff) - 1)
    sx_map = {
        xc: sum(lam[xc][z] for z in w_diff) - sum(lam[xc][z] for z in u_diff if z != xc)
        for xc in diff_u
    }
    sy_map = {
        yc: sum(lam[yc][z] for z in u_diff) - sum(lam[yc][z] for z in w_diff if z != yc)
        for yc in diff_w
    }

    pares_cand: List[Tuple[int, int, int]] = []
    for x_cand in diff_u:
        rx = lam[x_cand]
        sx_val = const_m + sx_map[x_cand]
        for y_cand in diff_w:
            d_div = sx_val + sy_map[y_cand] - 2 * rx[y_cand]
            if d_div <= 0:
                pares_cand.append((d_div, x_cand, y_cand))

    if falha_injetada == "delta_phi2_positivo":
        pares_cand = []

    if not pares_cand:
        estado["rej_phi2"] += 1
        return "rej_phi2", None

    pares_cand.sort(key=lambda item: item[0])
    tu_new = tw_new = None
    fsu_new = fsw_new = None
    x = y = delta_phi2_div = d_q_plus = delta_cnt_dmax = 0
    passou_r1_r10 = False
    passou_q_dmax = False

    for d_div, x_cand, y_cand in pares_cand[:8]:
        tu_cand = sorted((tu_set - {x_cand}) | {y_cand})
        tw_cand = sorted((tw_set - {y_cand}) | {x_cand})
        cand_ok = validar_r1_r9_rapido(tu_cand) and validar_r1_r9_rapido(tw_cand)
        if cand_ok:
            fsu_c = frozenset(tu_cand)
            fsw_c = frozenset(tw_cand)
            if fsu_c == fsw_c or fsu_c in sets_lookup or fsw_c in sets_lookup:
                cand_ok = False
        else:
            fsu_c = fsw_c = None

        if falha_injetada == "violacao_r1_r10":
            cand_ok = False
        if not cand_ok:
            continue
        passou_r1_r10 = True

        dmax_ok, d_qp, d_cnt = avaliar_delta_q_dmax_local(
            x_cand, y_cand, u_diff, w_diff, lam, J, r_block, current_d_max
        )
        if falha_injetada == "violacao_dmax":
            dmax_ok = False
        elif falha_injetada == "violacao_q_plus":
            d_qp = 1

        if not dmax_ok or d_qp > 0:
            continue

        x, y, delta_phi2_div, d_q_plus, delta_cnt_dmax = (
            x_cand,
            y_cand,
            d_div,
            d_qp,
            d_cnt,
        )
        tu_new, tw_new, fsu_new, fsw_new = tu_cand, tw_cand, fsu_c, fsw_c
        passou_q_dmax = True
        break

    if not passou_r1_r10:
        estado["rej_r1_r10"] += 1
        return "rej_r1_r10", None
    if not passou_q_dmax:
        estado["rej_q_plus_ou_dmax"] += 1
        return "rej_q_plus_ou_dmax", None

    sum_tu_old = sum(presenca[n] for n in tu)
    sum_tw_old = sum(presenca[n] for n in tw)
    sv_u_old = sum_tu_old.to_bytes(J, "little")
    sv_w_old = sum_tw_old.to_bytes(J, "little")

    bit_u = 1 << (8 * u_idx)
    bit_w = 1 << (8 * w_idx)
    pres_x_new = (presenca[x] & ~bit_u) | bit_w
    pres_y_new = (presenca[y] & ~bit_w) | bit_u

    sv_u_after = (sum_tu_old - presenca[x] + pres_y_new).to_bytes(J, "little")
    sv_w_after = (sum_tw_old - presenca[y] + pres_x_new).to_bytes(J, "little")

    max_ok = True
    for k_bad in range(teto_fase3 + 1, 50):
        if sv_u_after.count(k_bad) > 0 or sv_w_after.count(k_bad) > 0:
            max_ok = False
            break
    if falha_injetada == "violacao_kmax":
        max_ok = False

    if not max_ok or sv_u_after.count(50) > 1 or sv_w_after.count(50) > 1:
        estado["rej_kmax"] += 1
        return "rej_kmax", None

    comb_before = somar_comb_vetor(sv_u_old) + somar_comb_vetor(sv_w_old)
    comb_after = somar_comb_vetor(sv_u_after) + somar_comb_vetor(sv_w_after)
    d_p25 = (comb_after >> 80) - (comb_before >> 80)
    d_rwin = (comb_after & MASK_80) - (comb_before & MASK_80)

    if falha_injetada == "violacao_p25":
        d_p25 = 1
    elif falha_injetada == "violacao_rwin":
        d_rwin = 1
    elif falha_injetada == "empate_sem_melhora":
        delta_phi2_div = 0
        d_q_plus = 0
        d_p25 = 0
        d_rwin = 0

    melhorou = (delta_phi2_div < 0) or (d_q_plus < 0) or (d_p25 < 0) or (d_rwin < 0)
    if not (d_p25 <= 0 and d_rwin <= 0 and melhorou):
        estado["rej_p25_rwin"] += 1
        return "rej_p25_rwin", None

    fsu_old = frozenset(tu)
    fsw_old = frozenset(tw)
    old_px = presenca[x]
    old_py = presenca[y]
    prev_phi2 = estado["current_phi2"]
    prev_q_plus = estado["current_q_plus"]
    prev_d_max = estado["current_d_max"]
    prev_cnt_d_max = estado["cnt_d_max"]
    prev_recalc_dmax = estado["recalculos_dmax_queda"]
    prev_p25 = estado["current_p25"]
    prev_rwin = estado["current_rwin"]
    prev_sha_atual = estado["sha256_estado_atual"]
    prev_sha_ultimo = estado["sha256_ultimo_swap"]
    buf = estado["estado_canonico_buf"]
    su0, su1 = 50 * u_idx, 50 * (u_idx + 1)
    sw0, sw1 = 50 * w_idx, 50 * (w_idx + 1)
    old_buf_u = bytes(buf[su0:su1])
    old_buf_w = bytes(buf[sw0:sw1])

    lam_mutated = False
    sets_mutated = False
    buf_mutated = False

    def _rollback() -> None:
        presenca[x] = old_px
        presenca[y] = old_py
        if lam_mutated:
            for z in u_diff:
                if z != x:
                    lam[x][z] += 1
                    lam[z][x] += 1
                    lam[y][z] -= 1
                    lam[z][y] -= 1
            for z in w_diff:
                if z != y:
                    lam[y][z] += 1
                    lam[z][y] += 1
                    lam[x][z] -= 1
                    lam[z][x] -= 1
        if sets_mutated:
            sets_lookup.discard(fsu_new)
            sets_lookup.discard(fsw_new)
            sets_lookup.add(fsu_old)
            sets_lookup.add(fsw_old)
            jogos_selecionados[u_idx] = tu
            jogos_selecionados[w_idx] = tw
        if buf_mutated:
            buf[su0:su1] = old_buf_u
            buf[sw0:sw1] = old_buf_w
        estado["current_phi2"] = prev_phi2
        estado["current_q_plus"] = prev_q_plus
        estado["current_d_max"] = prev_d_max
        estado["cnt_d_max"] = prev_cnt_d_max
        estado["recalculos_dmax_queda"] = prev_recalc_dmax
        estado["current_p25"] = prev_p25
        estado["current_rwin"] = prev_rwin
        estado["sha256_estado_atual"] = prev_sha_atual
        estado["sha256_ultimo_swap"] = prev_sha_ultimo

    try:
        presenca[x] = pres_x_new
        presenca[y] = pres_y_new

        for z in u_diff:
            if z != x:
                lam[x][z] -= 1
                lam[z][x] -= 1
                lam[y][z] += 1
                lam[z][y] += 1
        for z in w_diff:
            if z != y:
                lam[y][z] -= 1
                lam[z][y] -= 1
                lam[x][z] += 1
                lam[z][x] += 1
        lam_mutated = True

        sets_lookup.remove(fsu_old)
        sets_lookup.remove(fsw_old)
        sets_lookup.add(fsu_new)
        sets_lookup.add(fsw_new)
        jogos_selecionados[u_idx] = tu_new
        jogos_selecionados[w_idx] = tw_new
        sets_mutated = True

        buf[su0:su1] = bytes(tu_new)
        buf[sw0:sw1] = bytes(tw_new)
        buf_mutated = True

        if falha_injetada == "excecao_interna":
            raise FalhaInjetadaAtomica("Falha injetada apos mutacao parcial de commit")

        estado["current_phi2"] = prev_phi2 + delta_phi2_div * 11552
        estado["current_q_plus"] = prev_q_plus + d_q_plus
        estado["current_p25"] = prev_p25 + d_p25
        estado["current_rwin"] = prev_rwin + d_rwin
        cnt_d_max = prev_cnt_d_max + delta_cnt_dmax
        if cnt_d_max == 0:
            estado["recalculos_dmax_queda"] += 1
            dmax_new, cnt_new = _recalcular_dmax_global(lam, J)
            estado["current_d_max"] = dmax_new
            estado["cnt_d_max"] = cnt_new
        else:
            estado["cnt_d_max"] = cnt_d_max

        r1_r10_ok = (
            len(tu_new) == 50
            and len(tw_new) == 50
            and len(set(tu_new)) == 50
            and len(set(tw_new)) == 50
            and tu_new[0] >= 1
            and tu_new[-1] <= 100
            and tw_new[0] >= 1
            and tw_new[-1] <= 100
            and validar_r1_r9_rapido(tu_new)
            and validar_r1_r9_rapido(tw_new)
            and len(sets_lookup) == J
        )
        r11_ok = (
            u_idx >= 2
            and w_idx >= 2
            and max_ok
            and sv_u_after.count(50) == 1
            and sv_w_after.count(50) == 1
            and len(set(jogos_selecionados[0]) & set(jogos_selecionados[1])) == 0
        )
        target_u = estado["u"]
        r12_ok = all(presenca[n].bit_count() == target_u[n] for n in range(1, 101))
        if J % 2 == 0:
            half_j = J // 2
            r12_ok = r12_ok and all(
                presenca[n].bit_count() == half_j for n in range(1, 101)
            )

        if auditar_100pct_swaps:
            bruto = calcular_coocorrencia_global_bruta(lam, J)
            exigir(
                bruto["phi2"] == estado["current_phi2"],
                f"Phi2 divergente no swap {estado['swaps_aceitos']}",
            )
            exigir(
                bruto["q_global_plus"] == estado["current_q_plus"],
                f"Q+ divergente no swap {estado['swaps_aceitos']}",
            )
            exigir(
                bruto["d_max"] == estado["current_d_max"],
                f"D_max divergente no swap {estado['swaps_aceitos']}",
            )
            exigir(
                bruto["cnt_dmax"] == estado["cnt_d_max"],
                f"cnt_dmax divergente no swap {estado['swaps_aceitos']}",
            )
            exigir(estado["current_phi2"] <= prev_phi2, "Monotonicidade Phi2 violada")
            exigir(estado["current_q_plus"] <= prev_q_plus, "Monotonicidade Q+ violada")
            exigir(estado["current_d_max"] <= prev_d_max, "Monotonicidade D_max violada")
            exigir(estado["current_p25"] <= prev_p25, "Monotonicidade P>25 violada")
            exigir(estado["current_rwin"] <= prev_rwin, "Monotonicidade R_win violada")
            exigir(r1_r10_ok, f"R1-R10 violado no swap {estado['swaps_aceitos']}")
            exigir(r11_ok, f"R11 violado no swap {estado['swaps_aceitos']}")
            exigir(r12_ok, f"R12 violado no swap {estado['swaps_aceitos']}")
            exigir(
                sv_u_after == sum(presenca[n] for n in tu_new).to_bytes(J, "little"),
                "Assinatura SWAR de u_idx inconsistente",
            )
            exigir(
                sv_w_after == sum(presenca[n] for n in tw_new).to_bytes(J, "little"),
                "Assinatura SWAR de w_idx inconsistente",
            )

        if auditar_intersecoes_bruto:
            verificar_consistencia_lam_e_presenca(
                jogos_selecionados, lam, presenca, target_u
            )
            _, k_max_b, p25_b, rwin_b = calcular_metricas_intersecao_bruta(
                presenca, jogos_selecionados
            )
            exigir(k_max_b <= teto_fase3, "k_max excedeu teto_fase3")
            exigir(p25_b == estado["current_p25"], "P_gt_25 bruto divergente")
            exigir(rwin_b == estado["current_rwin"], "R_win bruto divergente")

        sha_depois = hashlib.sha256(buf).hexdigest()
        exigir(
            sha_antes_proposta == estado["sha256_ultimo_swap"],
            f"Quebra da cadeia SHA-256 no swap {estado['swaps_aceitos']}",
        )
        estado["sha256_estado_atual"] = sha_depois
        estado["sha256_ultimo_swap"] = sha_depois
    except FalhaInjetadaAtomica:
        _rollback()
        estado["rej_excecao"] += 1
        return "excecao_revertida", None
    except Exception:
        _rollback()
        raise

    reg = {
        "swap_idx": estado["swaps_aceitos"],
        "proposta_idx": proposta_idx,
        "u_idx": u_idx,
        "w_idx": w_idx,
        "x": x,
        "y": y,
        "delta_phi2": delta_phi2_div * 11552,
        "delta_q_plus": d_q_plus,
        "d_max_antes": prev_d_max,
        "d_max_depois": estado["current_d_max"],
        "p25_antes": prev_p25,
        "p25_depois": estado["current_p25"],
        "rwin_antes": str(prev_rwin),
        "rwin_depois": str(estado["current_rwin"]),
        "r1_r10_ok": r1_r10_ok,
        "r11_ok": r11_ok,
        "r12_ok": r12_ok,
        "sha256_estado_antes": sha_antes_proposta,
        "sha256_estado_depois": sha_depois,
    }
    estado["swaps_aceitos"] += 1
    if len(estado["amostra_primeiros_swaps"]) < 3:
        estado["amostra_primeiros_swaps"].append(reg)
    estado["amostra_ultimos_swaps"].append(reg)
    if len(estado["amostra_ultimos_swaps"]) > 3:
        estado["amostra_ultimos_swaps"].pop(0)

    if trilha_fp is not None:
        trilha_fp.write(json.dumps(reg, separators=(",", ":")) + "\n")

    return "ACEITO", reg


def gerar_carteira_10000_otimizada(
    *,
    seed: int = 330001,
    J: int = 10000,
    max_tentativas_f3: int = 1080000,
    tau_primario: int = 35,
    alpha_25: float = 30.0,
    alpha_win: float = 1.0,
    alpha_1: float = 0.08,
    alpha_2: float = 0.25,
    gamma_plus: float = 0.02,
    batch0: int = 80,
    passo_checkpoint: Optional[int] = None,
    auditar_100pct_swaps: bool = True,
    auditar_intersecoes_bruto: bool = False,
    incluir_jogos_no_retorno: bool = True,
    caminho_trilha_jsonl: Optional[str] = None,
    caminho_carteira_saida: Optional[str] = None,
    caminho_relatorio_saida: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executa integralmente o pipeline Ordem 5-R3 (`Fases 1-2` + `Fase 3 S1_atual_top8`)
    com orcamento padrao de 1.080.000 tentativas para `J=10.000` e auditoria completa.
    """
    validar_entrada_carteira(
        J=J, seed=seed, max_tentativas_f3=max_tentativas_f3, tau_primario=tau_primario
    )
    if passo_checkpoint is not None and (
        type(passo_checkpoint) is not int or passo_checkpoint <= 0
    ):
        raise ValueError("passo_checkpoint deve ser inteiro positivo ou None.")

    rnd, estado = inicializar_carteira_fase12(
        seed=seed,
        J=J,
        tau_primario=tau_primario,
        alpha_25=alpha_25,
        alpha_win=alpha_win,
        alpha_1=alpha_1,
        alpha_2=alpha_2,
        gamma_plus=gamma_plus,
        batch0=batch0,
    )

    t_f3_0 = time.perf_counter()
    tentativas_f3 = 0
    checkpoints: List[Dict[str, Any]] = []
    prev_swaps = 0
    prev_phi2 = estado["current_phi2"]
    prev_qp = estado["current_q_plus"]
    prev_p25 = estado["current_p25"]
    prev_rwin = estado["current_rwin"]

    pares_34_35 = estado["pares_34_35"]
    pares_32_33 = estado["pares_32_33"]
    n_34 = len(pares_34_35)
    n_32 = len(pares_32_33)

    trilha_fp = (
        open(caminho_trilha_jsonl, "w", encoding="utf-8", buffering=1024 * 256)
        if caminho_trilha_jsonl
        else None
    )
    try:
        if J >= 4 and max_tentativas_f3 > 0:
            while tentativas_f3 < max_tentativas_f3:
                mod4 = tentativas_f3 & 3
                if mod4 == 0 and n_34 > 0:
                    u_idx, v_idx = pares_34_35[rnd.randrange(n_34)]
                    if ((tentativas_f3 & 4) != 0 and v_idx >= 2) or u_idx < 2:
                        u_idx, v_idx = v_idx, u_idx
                elif mod4 == 1 and n_32 > 0:
                    u_idx, v_idx = pares_32_33[rnd.randrange(n_32)]
                    if ((tentativas_f3 & 4) != 0 and v_idx >= 2) or u_idx < 2:
                        u_idx, v_idx = v_idx, u_idx
                else:
                    u_idx = rnd.randrange(2, J)
                    v_idx = u_idx
                if u_idx < 2:
                    u_idx = rnd.randrange(2, J)
                if J == 4 and u_idx != v_idx:
                    v_idx = u_idx

                w_idx = rnd.randrange(2, J)
                if w_idx == u_idx or w_idx == v_idx:
                    continue
                r_block = rnd.randrange(5)

                avaliar_e_aplicar_swap_fase3(
                    estado,
                    u_idx,
                    v_idx,
                    w_idx,
                    r_block,
                    tentativas_f3,
                    falha_injetada=None,
                    auditar_100pct_swaps=auditar_100pct_swaps,
                    auditar_intersecoes_bruto=auditar_intersecoes_bruto,
                    trilha_fp=trilha_fp,
                )
                tentativas_f3 += 1

                if passo_checkpoint is not None and (
                    tentativas_f3 % passo_checkpoint == 0
                    or tentativas_f3 == max_tentativas_f3
                ):
                    cooc_cp = calcular_coocorrencia_global_bruta(estado["lam"], J)
                    exigir(
                        cooc_cp["phi2"] == estado["current_phi2"],
                        f"Phi2 divergente no checkpoint {tentativas_f3}",
                    )
                    exigir(
                        cooc_cp["q_global_plus"] == estado["current_q_plus"],
                        f"Q+ divergente no checkpoint {tentativas_f3}",
                    )
                    exigir(
                        cooc_cp["d_max"] == estado["current_d_max"],
                        f"D_max divergente no checkpoint {tentativas_f3}",
                    )
                    checkpoints.append(
                        {
                            "tentativas": tentativas_f3,
                            "swaps_acumulados": estado["swaps_aceitos"],
                            "swaps_na_faixa": estado["swaps_aceitos"] - prev_swaps,
                            "phi2": estado["current_phi2"],
                            "delta_phi2_na_faixa": estado["current_phi2"] - prev_phi2,
                            "q_global_plus": estado["current_q_plus"],
                            "delta_q_plus_na_faixa": estado["current_q_plus"] - prev_qp,
                            "d_max": estado["current_d_max"],
                            "cnt_dmax": estado["cnt_d_max"],
                            "P_gt_25": estado["current_p25"],
                            "delta_p25_na_faixa": estado["current_p25"] - prev_p25,
                            "R_win": str(estado["current_rwin"]),
                            "delta_rwin_na_faixa": str(
                                estado["current_rwin"] - prev_rwin
                            ),
                            "sigma_intra": cooc_cp["sigma_intra"],
                            "sigma_inter": cooc_cp["sigma_inter"],
                            "recalculos_dmax_acum": estado["recalculos_dmax_queda"],
                            "tempo_fase3_acum_s": round(
                                time.perf_counter() - t_f3_0, 4
                            ),
                        }
                    )
                    prev_swaps = estado["swaps_aceitos"]
                    prev_phi2 = estado["current_phi2"]
                    prev_qp = estado["current_q_plus"]
                    prev_p25 = estado["current_p25"]
                    prev_rwin = estado["current_rwin"]
    finally:
        if trilha_fp is not None:
            trilha_fp.close()

    tempo_fase3 = time.perf_counter() - t_f3_0
    jogos_selecionados = estado["jogos_selecionados"]
    lam = estado["lam"]
    presenca = estado["presenca_bytes_int"]
    u = estado["u"]

    verificar_consistencia_lam_e_presenca(jogos_selecionados, lam, presenca, u)
    cooc_post = calcular_coocorrencia_global_bruta(lam, J)
    exigir(cooc_post["phi2"] == estado["current_phi2"], "Phi2 final divergente")
    exigir(
        cooc_post["q_global_plus"] == estado["current_q_plus"], "Q+ final divergente"
    )
    exigir(cooc_post["d_max"] == estado["current_d_max"], "D_max final divergente")
    exigir(cooc_post["cnt_dmax"] == estado["cnt_d_max"], "cnt_dmax final divergente")

    freq_k_final, k_max, p_25_tot, r_win_tot = calcular_metricas_intersecao_bruta(
        presenca, jogos_selecionados
    )
    exigir(k_max <= estado["teto_fase3"], "k_max final excedeu teto_fase3")
    exigir(p_25_tot == estado["current_p25"], "P_gt_25 final divergente")
    exigir(r_win_tot == estado["current_rwin"], "R_win final divergente")

    buf_reconstruido = bytearray(n for jg in jogos_selecionados for n in jg)
    exigir(
        estado["estado_canonico_buf"] == buf_reconstruido,
        "Buffer canonico divergente dos jogos finais",
    )
    sha_canonico_final = hashlib.sha256(buf_reconstruido).hexdigest()
    exigir(
        sha_canonico_final == estado["sha256_estado_atual"],
        "Hash SHA-256 do estado canonico divergente",
    )

    if caminho_trilha_jsonl:
        n_trilha = validar_trilha_jsonl_em_disco(
            caminho_trilha_jsonl,
            estado["pre_fase3"]["sha256_estado_inicial_fase3"],
            sha_canonico_final,
            estado["swaps_aceitos"],
        )
        exigir(
            n_trilha == estado["swaps_aceitos"],
            "Contagem da trilha JSONL divergente",
        )
        with open(caminho_trilha_jsonl, "rb") as ft:
            sha256_trilha_jsonl = hashlib.sha256(ft.read()).hexdigest()
    else:
        sha256_trilha_jsonl = None

    certificados = calcular_hashes_certificados(
        jogos_selecionados,
        seed=seed,
        J=J,
        max_tentativas_f3=max_tentativas_f3,
        versao_algoritmo=VERSAO_ALGORITMO,
    )
    exigir(
        certificados["sha256_estado_canonico"] == sha_canonico_final,
        "Hash canonico certificado divergente",
    )

    sha256_arquivo_carteira = None
    if caminho_carteira_saida:
        dados_carteira = {
            "versao_algoritmo": VERSAO_ALGORITMO,
            "seed": seed,
            "J": J,
            "max_tentativas_f3": max_tentativas_f3,
            "sha256_carteira": certificados["sha256_carteira"],
            "hash_carteira_sha256_v1": certificados["hash_carteira_sha256_v1"],
            "hash_carteira_sha256_v2_canonico": certificados[
                "hash_carteira_sha256_v2_canonico"
            ],
            "sha256_estado_canonico": sha_canonico_final,
            "sha256_matriz_incidencia_100": certificados[
                "sha256_matriz_incidencia_100"
            ],
            "jogos": jogos_selecionados,
        }
        with open(caminho_carteira_saida, "w", encoding="utf-8") as fc:
            json.dump(dados_carteira, fc, separators=(",", ":"))
        with open(caminho_carteira_saida, "rb") as fc:
            sha256_arquivo_carteira = hashlib.sha256(fc.read()).hexdigest()

    relatorio: Dict[str, Any] = {
        "versao_algoritmo": VERSAO_ALGORITMO,
        "estrategia": ESTRATEGIA_FASE3_PADRAO,
        "clausula_obrigatoria": CLAUSULA_OBRIGATORIA,
        "seed": seed,
        "J": J,
        "max_tentativas_f3": max_tentativas_f3,
        "contingencias": estado["contingencias"],
        "tempo_fase12_s": round(estado["tempo_fase12_s"], 4),
        "tempo_fase3_s": round(tempo_fase3, 4),
        "tempo_total_s": round(estado["tempo_fase12_s"] + tempo_fase3, 4),
        "auditoria_100pct_swaps_executada": auditar_100pct_swaps,
        "auditoria_intersecoes_bruto_executada": auditar_intersecoes_bruto,
        "tentativas_fase3": tentativas_f3,
        "swaps_aceitos": estado["swaps_aceitos"],
        "recalculos_dmax_queda": estado["recalculos_dmax_queda"],
        "rejeicoes": {
            "sem_par_xy": estado["rej_sem_par_xy"],
            "delta_phi2_positivo": estado["rej_phi2"],
            "violacao_r1_r10": estado["rej_r1_r10"],
            "violacao_q_plus_ou_dmax": estado["rej_q_plus_ou_dmax"],
            "violacao_kmax": estado["rej_kmax"],
            "sem_melhora_p25_rwin": estado["rej_p25_rwin"],
            "excecao_revertida": estado["rej_excecao"],
        },
        "pre_fase3": estado["pre_fase3"],
        "pos_fase3": {
            "k_max": k_max,
            "k_eq_35": freq_k_final[35],
            "k_ge_36": sum(freq_k_final[k] for k in range(36, 51)),
            "f_k": {str(k): freq_k_final[k] for k in range(51)},
            "P_gt_25": p_25_tot,
            "R_win": str(r_win_tot),
            "phi2": cooc_post["phi2"],
            "q_global_plus": cooc_post["q_global_plus"],
            "d_max": cooc_post["d_max"],
            "cnt_dmax": cooc_post["cnt_dmax"],
            "sigma_intra": cooc_post["sigma_intra"],
            "sigma_inter": cooc_post["sigma_inter"],
        },
        "homologacao_kmax": classificar_homologacao_kmax(k_max),
        "checkpoints_60k": checkpoints,
        "auditoria_restricoes": {
            **certificados,
            "sha256_arquivo_carteira": sha256_arquivo_carteira,
            "sha256_trilha_jsonl": sha256_trilha_jsonl,
            "u_min": min(u[1:]),
            "u_max": max(u[1:]),
            "intersecao_par_inicial": len(
                set(jogos_selecionados[0]) & set(jogos_selecionados[1])
            ),
            "cadeia_hashes_swaps_integra": estado["cadeia_hashes_integra"],
        },
        "amostra_trilha_swaps": {
            "primeiros": estado["amostra_primeiros_swaps"],
            "ultimos": estado["amostra_ultimos_swaps"],
        },
        "sha256_carteira": certificados["sha256_carteira"],
    }
    if caminho_relatorio_saida:
        with open(caminho_relatorio_saida, "w", encoding="utf-8") as fr:
            json.dump(relatorio, fr, indent=2)
    if incluir_jogos_no_retorno:
        relatorio["jogos"] = jogos_selecionados
    return relatorio
