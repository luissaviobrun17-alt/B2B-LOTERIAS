# -*- coding: utf-8 -*-
"""
ETAPA 2: IMPLEMENTACAO DE REFERENCIA INDEPENDENTE E VERIFICACAO EXATA
======================================================================
Implementacao alternativa e totalmente desacoplada de etapa2_funcao_objetivo.py:
  - Nao importa nenhuma funcao de avaliacao nem tabelas pre-computadas de
    etapa2_funcao_objetivo.py.
  - Utiliza exclusivamente estruturas basicas Python (sets, itertools, Kruskal) e
    definicoes combinatorias diretas para validacao cruzada de equivalencia.
  - Inclui enumerador exato de forca bruta sobre os 3.268.760 sorteios de
    C(25, 15) para demonstrar exatidao de p_2(c), E[N_prem], Var(N_prem) e
    cotas Dawson-Sankoff / Hunter-Worsley.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
import itertools
import math
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .etapa1_regras_oficiais import (
    CENTRO_5X5,
    COLUNAS_5X5,
    ESPACO_AMOSTRAL_SIMPLES,
    LINHAS_5X5,
    MOLDURA_5X5,
    PRECO_APOSTA_SIMPLES,
    TAMANHO_SORTEIO,
    UNIVERSO_TOTAL,
    validar_aposta_lotofacil,
)


def _prob_individual_direta(m: int) -> Fraction:
    num = 0
    for k in range(11, min(m, TAMANHO_SORTEIO) + 1):
        if TAMANHO_SORTEIO - k <= UNIVERSO_TOTAL - m:
            num += math.comb(m, k) * math.comb(UNIVERSO_TOTAL - m, TAMANHO_SORTEIO - k)
    return Fraction(num, ESPACO_AMOSTRAL_SIMPLES)


def _prob_par_direta(jogo_a: set[int], jogo_b: set[int], k_min: int = 11) -> Fraction:
    inter = len(jogo_a & jogo_b)
    so_a = len(jogo_a - jogo_b)
    so_b = len(jogo_b - jogo_a)
    fora = UNIVERSO_TOTAL - len(jogo_a | jogo_b)

    total = 0
    for q_inter in range(inter + 1):
        w_inter = math.comb(inter, q_inter)
        for q_a in range(max(0, k_min - q_inter), min(so_a, TAMANHO_SORTEIO - q_inter) + 1):
            w_a = math.comb(so_a, q_a)
            for q_b in range(max(0, k_min - q_inter), min(so_b, TAMANHO_SORTEIO - q_inter - q_a) + 1):
                q_fora = TAMANHO_SORTEIO - q_inter - q_a - q_b
                if 0 <= q_fora <= fora:
                    total += w_inter * w_a * math.comb(so_b, q_b) * math.comb(fora, q_fora)
    return Fraction(total, ESPACO_AMOSTRAL_SIMPLES)


def probabilidade_par_quatro_regioes_referencia(
    m1: int,
    m2: int,
    c: int,
    k_min: int = 11,
) -> Fraction:
    """
    Referencia independente via conjuntos canonicos explicitos e contagem direta
    das 4 regioes disjuntas para quaisquer bilhetes de 15 a 20 dezenas.
    """
    b1 = set(range(1, m1 + 1))
    b2 = set(range(1, c + 1)) | set(range(m1 + 1, m1 + 1 + (m2 - c)))
    return _prob_par_direta(b1, b2, k_min=k_min)


def _mst_max_kruskal(n: int, pesos: Dict[Tuple[int, int], Fraction]) -> Fraction:
    """Algoritmo de Kruskal independente para cota superior de Hunter-Worsley."""
    if n <= 1:
        return Fraction(0, 1)
    pai = list(range(n))

    def _find(x: int) -> int:
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    arestas = sorted(pesos.items(), key=lambda kv: kv[1], reverse=True)
    soma = Fraction(0, 1)
    unidos = 0
    for (u, v), w in arestas:
        ru, rv = _find(u), _find(v)
        if ru != rv:
            pai[ru] = rv
            soma += w
            unidos += 1
            if unidos == n - 1:
                break
    return soma


def avaliar_carteira_referencia_independente(
    carteira: Iterable[Iterable[int]],
    pool: Optional[Iterable[int]] = None,
    fixas: Iterable[int] = (),
    pesos: Optional[Mapping[str, float]] = None,
    modo_fixas: str = "todos_os_jogos",
) -> Dict[str, Any]:
    """
    Implementacao independente de conferencia matematica da ETAPA 2.
    """
    pesos_padrao = {
        "cobertura_combinatoria": 0.30,
        "probabilidade_conjunta": 0.25,
        "diversificacao_sobreposicao": 0.20,
        "distribuicao_dezenas": 0.10,
        "custo_beneficio": 0.10,
        "diversidade_estrutural": 0.05,
    }
    w = dict(pesos) if pesos is not None else pesos_padrao

    jogos = sorted(validar_aposta_lotofacil(jg) for jg in carteira)
    conjuntos = [set(jg) for jg in jogos]
    pool_ord = tuple(sorted(set(pool))) if pool is not None else tuple(sorted(set().union(*conjuntos)))
    fixas_ord = tuple(sorted(set(fixas)))

    p = len(pool_ord)
    f = len(fixas_ord) if modo_fixas == "todos_os_jogos" else 0
    j = len(jogos)
    tamanhos = [len(jg) for jg in jogos]

    # 1. Cobertura combinatoria por enumeracao direta de tuplas
    pesos_t = {1: 0.15, 2: 0.35, 3: 0.35, 4: 0.15}
    s_cov = 0.0
    cob_brutas: Dict[int, int] = {}
    cov2_teto = 1.0
    for t in (1, 2, 3, 4):
        uni: set[Tuple[int, ...]] = set()
        for jg in jogos:
            uni.update(itertools.combinations(jg, t))
        c_fix = math.comb(f, t) if f >= t else 0
        teto = min(math.comb(p, t), c_fix + sum(math.comb(m, t) - c_fix for m in tamanhos))
        ef = len(uni) / teto if teto > 0 else 1.0
        cob_brutas[t] = len(uni)
        if t == 2:
            cov2_teto = min(1.0, ef)
        s_cov += pesos_t[t] * min(1.0, ef)

    # Cota minima inteira de intersecoes via soma de C(u_d, 2) no minimo uniforme inteiro
    p_livre = p - f
    m_livre_total = sum(m - f for m in tamanhos)
    if j <= 1:
        s_i_min = 0
        i_min_medio = 0.0
    elif p_livre <= 0:
        s_i_min = (j * (j - 1) // 2) * f
        i_min_medio = float(f)
    else:
        q, r = divmod(m_livre_total, p_livre)
        s_i_min = (j * (j - 1) // 2) * f + (p_livre - r) * math.comb(q, 2) + r * math.comb(q + 1, 2)
        i_min_medio = s_i_min / (j * (j - 1) // 2)

    # 2. Probabilidade conjunta via definicao direta e Kruskal
    p_inds = [_prob_individual_direta(m) for m in tamanhos]
    s1 = sum(p_inds, Fraction(0, 1))
    s2 = Fraction(0, 1)
    soma_cov = Fraction(0, 1)
    arestas_p2: Dict[Tuple[int, int], Fraction] = {}
    intersecoes: List[int] = []
    s_i_max = 0
    penal_picos: List[float] = []

    for i in range(j):
        for k in range(i + 1, j):
            c_ik = len(conjuntos[i] & conjuntos[k])
            intersecoes.append(c_ik)
            c_max = min(tamanhos[i], tamanhos[k])
            s_i_max += c_max
            penal_picos.append((max(0.0, c_ik - i_min_medio) / max(1.0, c_max - i_min_medio)) ** 2)

            p2_ik = _prob_par_direta(conjuntos[i], conjuntos[k])
            arestas_p2[(i, k)] = p2_ik
            s2 += p2_ik
            soma_cov += p2_ik - (p_inds[i] * p_inds[k])

    var_ind = sum(pi * (Fraction(1, 1) - pi) for pi in p_inds)
    var_dep = var_ind + (2 * soma_cov)

    # Dawson-Sankoff e Hunter-Worsley independentes
    cota_ds = max(p_inds)
    if j >= 2 and s1 > 0:
        for kk in range(1, j + 1):
            cand = (2 * s1) / Fraction(kk + 1, 1) - (2 * s2) / Fraction(kk * (kk + 1), 1)
            if cand > cota_ds:
                cota_ds = cand
    cota_ds = min(Fraction(1, 1), cota_ds)
    cota_hw = min(Fraction(1, 1), max(Fraction(0, 1), s1 - _mst_max_kruskal(j, arestas_p2)))

    if j <= 1:
        s_prob = 1.0
    else:
        pares_tot = j * (j - 1) // 2
        i_min_rac = Fraction(s_i_min, pares_tot)
        c_l = i_min_rac.numerator // i_min_rac.denominator
        c_h = c_l + (1 if i_min_rac > c_l else 0)
        frac_c = i_min_rac - c_l

        s2_max = Fraction(0, 1)
        s2_ref = Fraction(0, 1)
        for i in range(j):
            mi = tamanhos[i]
            for k in range(i + 1, j):
                mk = tamanhos[k]
                c_max_par = min(mi, mk)
                b_base = set(range(1, mi + 1))
                b_clone = set(range(1, c_max_par + 1))
                if len(b_clone) < mk:
                    b_clone.update(range(mi + 1, mi + 1 + (mk - len(b_clone))))
                s2_max += _prob_par_direta(b_base, b_clone)

                c_min_par = max(0, mi + mk - p, f)
                if mi == mk == TAMANHO_SORTEIO:
                    cl = max(c_min_par, min(c_max_par, c_l))
                    ch = max(c_min_par, min(c_max_par, c_h))
                    b_l = set(range(1, cl + 1)) | set(range(16, 16 + (15 - cl)))
                    b_h = set(range(1, ch + 1)) | set(range(16, 16 + (15 - ch)))
                    p_l = _prob_par_direta(set(range(1, 16)), b_l)
                    p_h = _prob_par_direta(set(range(1, 16)), b_h)
                    s2_ref += p_l + frac_c * (p_h - p_l)
                else:
                    b_min = set(range(1, c_min_par + 1)) | set(range(mi + 1, mi + 1 + (mk - c_min_par)))
                    s2_ref += _prob_par_direta(b_base, b_min)

        den_p2 = s2_max - s2_ref
        s_prob = 1.0 if den_p2 <= 0 else min(1.0, max(0.0, float((s2_max - s2) / den_p2)))

    # 3. Diversificacao / Sobreposicao
    if j <= 1 or s_i_max <= s_i_min:
        s_div = 1.0
    else:
        ex_med = max(0.0, (sum(intersecoes) - s_i_min) / (s_i_max - s_i_min))
        e_pico = sum(penal_picos) / len(penal_picos)
        s_div = min(1.0, max(0.0, 1.0 - (0.50 * ex_med + 0.50 * e_pico)))

    # 4. Distribuicao de uso
    livres = [d for d in pool_ord if d not in (set(fixas_ord) if modo_fixas == "todos_os_jogos" else set())]
    if not livres:
        s_dist = 1.0
    else:
        mu = m_livre_total / len(livres)
        _, rem = divmod(m_livre_total, len(livres))
        ss_min = rem * (1.0 - rem / len(livres))
        u_pior = [0] * len(livres)
        for m in tamanhos:
            for pos in range(min(m - f, len(livres))):
                u_pior[pos] += 1
        ss_max = max(ss_min, sum((u - mu) ** 2 for u in u_pior))
        ss_obs = sum((sum(1 for cj in conjuntos if d in cj) - mu) ** 2 for d in livres)
        s_dist = 1.0 if ss_max <= ss_min + 1e-12 else min(1.0, max(0.0, 1.0 - (ss_obs - ss_min) / (ss_max - ss_min)))

    # 5. Custo-beneficio
    comb_pagas = sum(math.comb(m, TAMANHO_SORTEIO) for m in tamanhos)
    if comb_pagas <= 25_000:
        unicas: set[Tuple[int, ...]] = set()
        for jg in jogos:
            unicas.update(itertools.combinations(jg, TAMANHO_SORTEIO))
        qtd_unicas = len(unicas)
    else:
        qtd_unicas = comb_pagas if len(set(jogos)) == j else len(set(jogos))
    taxa_unic = qtd_unicas / comb_pagas if comb_pagas > 0 else 1.0
    s_cb = min(1.0, max(0.0, 0.65 * taxa_unic + 0.35 * cov2_teto))

    # 6. Diversidade estrutural
    sigs = {(sum(1 for d in jg if d % 2 == 0), sum(1 for d in jg if d in MOLDURA_5X5), sum(jg) // 15) for jg in jogos}
    taxa_sigs = len(sigs) / j
    total_marcas = sum(tamanhos)
    alvo_lc = total_marcas / 5.0
    desv_l = sum(abs(sum(1 for cj in conjuntos for d in lin if d in cj) - alvo_lc) for lin in LINHAS_5X5)
    desv_c = sum(abs(sum(1 for cj in conjuntos for d in col if d in cj) - alvo_lc) for col in COLUNAS_5X5)
    eq_5x5 = min(1.0, max(0.0, 1.0 - (desv_l + desv_c) / (2.0 * max(1.0, 2.0 * total_marcas * 0.8))))
    s_est = min(1.0, max(0.0, 0.60 * taxa_sigs + 0.40 * eq_5x5))

    comps = {
        "cobertura_combinatoria": s_cov,
        "probabilidade_conjunta": s_prob,
        "diversificacao_sobreposicao": s_div,
        "distribuicao_dezenas": s_dist,
        "custo_beneficio": s_cb,
        "diversidade_estrutural": s_est,
    }
    f_total = sum(w[k] * comps[k] for k in comps)

    return {
        "componentes": comps,
        "funcao_objetivo_F": f_total,
        "funcao_perda_L": 1.0 - f_total,
        "variancia_dependente_exata": var_dep,
        "cota_inferior_dawson_sankoff": float(cota_ds),
        "cota_superior_hunter_worsley": float(cota_hw),
        "custo_total_brl": str(sum(PRECO_APOSTA_SIMPLES * Decimal(math.comb(m, TAMANHO_SORTEIO)) for m in tamanhos)),
        "cobertos_t": cob_brutas,
    }


def verificar_lote_universo_completo(
    carteiras: Sequence[Iterable[Iterable[int]]],
) -> List[Dict[str, Any]]:
    """
    Enumera todos os C(25, 15) = 3.268.760 sorteios possiveis da Lotofacil
    em uma unica passagem para validar simultaneamente multiplas carteiras.
    """
    preparadas: List[Tuple[int, List[int], List[int]]] = []
    for cart in carteiras:
        jogos = [validar_aposta_lotofacil(jg) for jg in cart]
        mascaras = [sum(1 << (d - 1) for d in jg) for jg in jogos]
        contagens = [0] * (len(jogos) + 1)
        preparadas.append((len(jogos), mascaras, contagens))

    total_sorteios = 0
    bits = tuple(1 << (d - 1) for d in range(1, UNIVERSO_TOTAL + 1))

    def _dfs(pos: int, restantes: int, mask_atual: int) -> None:
        nonlocal total_sorteios
        if restantes == 1:
            for d_idx in range(pos, UNIVERSO_TOTAL):
                mask_final = mask_atual | bits[d_idx]
                total_sorteios += 1
                for _, mascaras, contagens in preparadas:
                    prems = 0
                    for mj in mascaras:
                        if (mj & mask_final).bit_count() >= 11:
                            prems += 1
                    contagens[prems] += 1
            return
        limite = UNIVERSO_TOTAL - restantes + 1
        next_rem = restantes - 1
        for d_idx in range(pos, limite):
            _dfs(d_idx + 1, next_rem, mask_atual | bits[d_idx])

    _dfs(0, TAMANHO_SORTEIO, 0)

    if total_sorteios != ESPACO_AMOSTRAL_SIMPLES:
        raise RuntimeError(f"Contagem de sorteios divergiu de 3.268.760: {total_sorteios}")

    resultados: List[Dict[str, Any]] = []
    for j, _, contagem_premios in preparadas:
        dist_frac = {r: Fraction(contagem_premios[r], ESPACO_AMOSTRAL_SIMPLES) for r in range(j + 1)}
        prob_pelo_menos_1 = Fraction(ESPACO_AMOSTRAL_SIMPLES - contagem_premios[0], ESPACO_AMOSTRAL_SIMPLES)
        esp = sum((r * dist_frac[r] for r in range(j + 1)), Fraction(0, 1))
        seg_mom = sum(((r * r) * dist_frac[r] for r in range(j + 1)), Fraction(0, 1))
        var_exata = seg_mom - (esp * esp)
        resultados.append(
            {
                "total_sorteios_enumerados": total_sorteios,
                "contagem_por_numero_premios": contagem_premios,
                "distribuicao_exata": dist_frac,
                "probabilidade_ao_menos_1_exata": prob_pelo_menos_1,
                "esperanca_exata": esp,
                "variancia_exata": var_exata,
            }
        )
    return resultados


def verificar_distribuicao_exata_universo_completo(
    carteira: Iterable[Iterable[int]],
) -> Dict[str, Any]:
    """
    Wrapper de conveniencia sobre verificar_lote_universo_completo para 1 carteira.
    """
    return verificar_lote_universo_completo([carteira])[0]
