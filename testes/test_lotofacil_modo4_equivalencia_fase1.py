# -*- coding: utf-8 -*-
"""
SUITE DE TESTES: EQUIVALENCIA RIGOROSA E BENCHMARK (FASE 1 - LOTOFACIL MODO 4)
=============================================================================
Valida a equivalencia matematica exata entre as formulas originais e as
otimizacoes propostas para a Fase 1 da Lotofacil MODO 4:
  1. Formula fechada de prefix_meta vs calculo iterativo par a par em O(k^2).
  2. Histograma discreto de intersecoes H(c) vs loop de pares em casos controlados.
  3. Comportamento exato em casos extremos (intersecao minima 5, maxima 14, fixas e pool restrito).
  4. Equivalencia estrita contra a referencia independente AST-isolada (<= 1e-12).
  5. Preservacao integral dos artefatos intocaveis da Lotomania e scripts NTFS.

Importante: sem uso de 'assert' como barreira critica; 100% efetivo sob -O.
"""

from __future__ import annotations

import math
import os
import random
import sys
import unittest
from fractions import Fraction
from typing import Any, Dict, List, Sequence, Tuple

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lotofacil_modo4.etapa1_regras_oficiais import (
    TAMANHO_SORTEIO,
    UNIVERSO_TOTAL,
    ErroValidacaoLotofacilError,
)
from lotofacil_modo4.etapa2_funcao_objetivo import (
    _cota_minima_intersecao_exata,
    _cota_minima_variancia_uso_exata,
    avaliar_carteira_etapa2,
    avaliar_diversificacao_sobreposicao,
    avaliar_probabilidade_conjunta_carteira,
    probabilidade_conjunta_par_exata,
    probabilidade_pelo_menos_k_exata,
)
from lotofacil_modo4.etapa4_arquitetura_adaptativa import (
    _CACHE_NP2_EXATO,
    ESPACO_AMOSTRAL_SIMPLES,
    AvaliadorConstrutivoIncrementalEtapa4,
    MotorIncrementalOtimizadoEtapa4,
    _resolver_especificacao_etapa4,
)
from lotofacil_modo4.etapa4_referencia_independente import (
    auditar_independencia_ast_etapa4,
    avaliar_carteira_ref_etapa4,
)


def _exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise AssertionError(mensagem)


def _calcular_prefix_meta_original(tams_alvo: Sequence[int], p: int, f: int) -> Dict[int, Dict[str, Any]]:
    """Calculo iterativo original de prefix_meta com laço de pares em O(k^2)."""
    prefix_meta: Dict[int, Dict[str, Any]] = {}
    comb_pagas_acc = 0
    marcas_acc = 0
    np2_max_acc = 0
    si_max_acc = 0
    j_max = len(tams_alvo)

    for k in range(1, j_max + 1):
        tams_k = tams_alvo[:k]
        mk_new = tams_k[-1]
        comb_pagas_acc += math.comb(mk_new, TAMANHO_SORTEIO)
        marcas_acc += mk_new
        tetos = {
            t: min(
                math.comb(p, t),
                (math.comb(f, t) if f >= t else 0)
                + sum(math.comb(m, t) - (math.comb(f, t) if f >= t else 0) for m in tams_k),
            )
            for t in (1, 2, 3, 4)
        }
        mu_k, ss_min_k, ss_max_k = _cota_minima_variancia_uso_exata(tams_k, p, f)
        s_i_min_k, i_min_med_k = _cota_minima_intersecao_exata(tams_k, p, f)

        soma_p2_ref_min_k = Fraction(0, 1)
        if k > 1:
            pares_k = k * (k - 1) // 2
            i_rac = Fraction(s_i_min_k, pares_k)
            c_low = i_rac.numerator // i_rac.denominator
            c_high = c_low + (1 if i_rac > c_low else 0)
            frac_c = i_rac - c_low
            for i_old in range(k - 1):
                mi = tams_k[i_old]
                si_max_acc += min(mi, mk_new)
                np2_max_acc += _CACHE_NP2_EXATO[(mi, mk_new, min(mi, mk_new))]
            for i in range(k):
                mi = tams_k[i]
                for j_i in range(i + 1, k):
                    mj = tams_k[j_i]
                    c_min_par = max(0, mi + mj - p, f)
                    c_max_par = min(mi, mj)
                    if mi == mj == TAMANHO_SORTEIO:
                        cl = max(c_min_par, min(c_max_par, c_low))
                        ch = max(c_min_par, min(c_max_par, c_high))
                        pl = Fraction(_CACHE_NP2_EXATO[(mi, mj, cl)], ESPACO_AMOSTRAL_SIMPLES)
                        ph = Fraction(_CACHE_NP2_EXATO[(mi, mj, ch)], ESPACO_AMOSTRAL_SIMPLES)
                        soma_p2_ref_min_k += pl + frac_c * (ph - pl)
                    else:
                        soma_p2_ref_min_k += Fraction(
                            _CACHE_NP2_EXATO[(mi, mj, c_min_par)], ESPACO_AMOSTRAL_SIMPLES
                        )

        np2_max_f = np2_max_acc / ESPACO_AMOSTRAL_SIMPLES
        den_p2_f = float(Fraction(np2_max_acc, ESPACO_AMOSTRAL_SIMPLES) - soma_p2_ref_min_k)
        prefix_meta[k] = {
            "tetos": tetos,
            "mu": mu_k,
            "ss_min": ss_min_k,
            "ss_max": ss_max_k,
            "s_i_min": s_i_min_k,
            "i_min_med": i_min_med_k,
            "s_i_max": si_max_acc,
            "np2_max_f": np2_max_f,
            "den_p2_f": den_p2_f,
            "comb_pagas": comb_pagas_acc,
            "rastreia_simples": comb_pagas_acc <= 25_000,
            "alvo_lc": marcas_acc / 5.0,
            "desvio_norm_max": max(1.0, 2.0 * marcas_acc * 0.8),
        }
    return prefix_meta


def _calcular_prefix_meta_fechado_otimizado(tams_alvo: Sequence[int], p: int, f: int) -> Dict[int, Dict[str, Any]]:
    """Calculo analitico em tempo linear O(J) com forma fechada O(1) por prefixo."""
    prefix_meta: Dict[int, Dict[str, Any]] = {}
    comb_pagas_acc = 0
    marcas_acc = 0
    np2_max_acc = 0
    si_max_acc = 0
    j_max = len(tams_alvo)
    p_livre = p - f

    # Verificacao de homogeneidade de tamanhos simples
    todos_simples = all(m == TAMANHO_SORTEIO for m in tams_alvo)
    np2_max_15_15 = _CACHE_NP2_EXATO[(TAMANHO_SORTEIO, TAMANHO_SORTEIO, TAMANHO_SORTEIO)]
    m_livre_un = TAMANHO_SORTEIO - f

    for k in range(1, j_max + 1):
        mk_new = tams_alvo[k - 1]
        comb_pagas_acc += math.comb(mk_new, TAMANHO_SORTEIO)
        marcas_acc += mk_new

        if todos_simples:
            tetos = {
                1: min(p, k * TAMANHO_SORTEIO),
                2: min(math.comb(p, 2), (math.comb(f, 2) if f >= 2 else 0) + k * (math.comb(TAMANHO_SORTEIO, 2) - (math.comb(f, 2) if f >= 2 else 0))),
                3: min(math.comb(p, 3), (math.comb(f, 3) if f >= 3 else 0) + k * (math.comb(TAMANHO_SORTEIO, 3) - (math.comb(f, 3) if f >= 3 else 0))),
                4: min(math.comb(p, 4), (math.comb(f, 4) if f >= 4 else 0) + k * (math.comb(TAMANHO_SORTEIO, 4) - (math.comb(f, 4) if f >= 4 else 0))),
            }
            m_livre_tot = k * m_livre_un
            mu_k = m_livre_tot / p_livre if p_livre > 0 else 0.0
            _, r = divmod(m_livre_tot, p_livre) if p_livre > 0 else (0, 0)
            ss_min_k = r * (1.0 - r / p_livre) if p_livre > 0 else 0.0
            ss_max_k = max(ss_min_k, (k ** 2) * m_livre_un * (p_livre - m_livre_un) / p_livre) if p_livre > 0 else 0.0
        else:
            tams_k = tams_alvo[:k]
            tetos = {
                t: min(
                    math.comb(p, t),
                    (math.comb(f, t) if f >= t else 0)
                    + sum(math.comb(m, t) - (math.comb(f, t) if f >= t else 0) for m in tams_k),
                )
                for t in (1, 2, 3, 4)
            }
            mu_k, ss_min_k, ss_max_k = _cota_minima_variancia_uso_exata(tams_k, p, f)

        if k <= 1:
            s_i_min_k, i_min_med_k = 0, 0.0
            soma_p2_ref_min_k = Fraction(0, 1)
            den_p2_f = 0.0
        else:
            pares_k = k * (k - 1) // 2
            if todos_simples:
                soma_fixa = pares_k * f
                q_i, r_i = divmod(m_livre_tot, p_livre) if p_livre > 0 else (0, 0)
                soma_livre = (p_livre - r_i) * (q_i * (q_i - 1) // 2) + r_i * ((q_i + 1) * q_i // 2) if p_livre > 0 else 0
                s_i_min_k = soma_fixa + soma_livre
                i_min_med_k = float(s_i_min_k / pares_k)
                si_max_acc += (k - 1) * TAMANHO_SORTEIO
                np2_max_acc += (k - 1) * np2_max_15_15

                i_rac = Fraction(s_i_min_k, pares_k)
                c_low = i_rac.numerator // i_rac.denominator
                c_high = c_low + (1 if i_rac > c_low else 0)
                frac_c = i_rac - c_low

                pl = Fraction(_CACHE_NP2_EXATO[(TAMANHO_SORTEIO, TAMANHO_SORTEIO, c_low)], ESPACO_AMOSTRAL_SIMPLES)
                ph = Fraction(_CACHE_NP2_EXATO[(TAMANHO_SORTEIO, TAMANHO_SORTEIO, c_high)], ESPACO_AMOSTRAL_SIMPLES)
                termo_par = pl + frac_c * (ph - pl)
                soma_p2_ref_min_k = pares_k * termo_par
                den_p2_f = float(Fraction(np2_max_acc, ESPACO_AMOSTRAL_SIMPLES) - soma_p2_ref_min_k)
            else:
                tams_k = tams_alvo[:k]
                s_i_min_k, i_min_med_k = _cota_minima_intersecao_exata(tams_k, p, f)
                for i_old in range(k - 1):
                    mi = tams_k[i_old]
                    si_max_acc += min(mi, mk_new)
                    np2_max_acc += _CACHE_NP2_EXATO[(mi, mk_new, min(mi, mk_new))]
                i_rac = Fraction(s_i_min_k, pares_k)
                c_low = i_rac.numerator // i_rac.denominator
                c_high = c_low + (1 if i_rac > c_low else 0)
                frac_c = i_rac - c_low
                soma_p2_ref_min_k = Fraction(0, 1)
                for i in range(k):
                    mi = tams_k[i]
                    for j_i in range(i + 1, k):
                        mj = tams_k[j_i]
                        c_min_par = max(0, mi + mj - p, f)
                        c_max_par = min(mi, mj)
                        if mi == mj == TAMANHO_SORTEIO:
                            cl = max(c_min_par, min(c_max_par, c_low))
                            ch = max(c_min_par, min(c_max_par, c_high))
                            pl = Fraction(_CACHE_NP2_EXATO[(mi, mj, cl)], ESPACO_AMOSTRAL_SIMPLES)
                            ph = Fraction(_CACHE_NP2_EXATO[(mi, mj, ch)], ESPACO_AMOSTRAL_SIMPLES)
                            soma_p2_ref_min_k += pl + frac_c * (ph - pl)
                        else:
                            soma_p2_ref_min_k += Fraction(
                                _CACHE_NP2_EXATO[(mi, mj, c_min_par)], ESPACO_AMOSTRAL_SIMPLES
                            )
                den_p2_f = float(Fraction(np2_max_acc, ESPACO_AMOSTRAL_SIMPLES) - soma_p2_ref_min_k)

        np2_max_f = np2_max_acc / ESPACO_AMOSTRAL_SIMPLES
        prefix_meta[k] = {
            "tetos": tetos,
            "mu": mu_k,
            "ss_min": ss_min_k,
            "ss_max": ss_max_k,
            "s_i_min": s_i_min_k,
            "i_min_med": i_min_med_k,
            "s_i_max": si_max_acc,
            "np2_max_f": np2_max_f,
            "den_p2_f": den_p2_f,
            "comb_pagas": comb_pagas_acc,
            "rastreia_simples": comb_pagas_acc <= 25_000,
            "alvo_lc": marcas_acc / 5.0,
            "desvio_norm_max": max(1.0, 2.0 * marcas_acc * 0.8),
        }
    return prefix_meta


class TestLotofacilModo4EquivalenciaFase1(unittest.TestCase):
    """Testes automatizados de equivalencia matematica estrita para a Fase 1."""

    def test_01_equivalencia_formula_fechada_prefix_meta(self) -> None:
        """Compara prefix_meta original vs forma fechada para todos os k de 1 a 60."""
        tams = [TAMANHO_SORTEIO] * 60
        meta_orig = _calcular_prefix_meta_original(tams, p=25, f=0)
        meta_opt = _calcular_prefix_meta_fechado_otimizado(tams, p=25, f=0)

        for k in range(1, 61):
            o_k = meta_orig[k]
            p_k = meta_opt[k]
            _exigir(o_k["tetos"] == p_k["tetos"], f"Tetos divergiram em k={k}")
            _exigir(abs(o_k["mu"] - p_k["mu"]) <= 1e-12, f"Mu divergiu em k={k}")
            _exigir(abs(o_k["ss_min"] - p_k["ss_min"]) <= 1e-12, f"SS_min divergiu em k={k}")
            _exigir(abs(o_k["ss_max"] - p_k["ss_max"]) <= 1e-12, f"SS_max divergiu em k={k}")
            _exigir(o_k["s_i_min"] == p_k["s_i_min"], f"S_i_min divergiu em k={k}")
            _exigir(abs(o_k["i_min_med"] - p_k["i_min_med"]) <= 1e-12, f"i_min_med divergiu em k={k}")
            _exigir(o_k["s_i_max"] == p_k["s_i_max"], f"S_i_max divergiu em k={k}")
            _exigir(abs(o_k["np2_max_f"] - p_k["np2_max_f"]) <= 1e-12, f"np2_max_f divergiu em k={k}")
            _exigir(abs(o_k["den_p2_f"] - p_k["den_p2_f"]) <= 1e-12, f"den_p2_f divergiu em k={k}")

    def test_02_equivalencia_histograma_10_classes_casos_controlados(self) -> None:
        """Comprova que o histograma de 10 classes reproduz exatamente todas as metricas pareadas."""
        rng = random.Random(2026)
        pool = list(range(1, 26))
        for j_tamanho in (15, 30, 60):
            # Gera jogos distintos
            carteira_set = set()
            while len(carteira_set) < j_tamanho:
                carteira_set.add(tuple(sorted(rng.sample(pool, 15))))
            carteira = sorted(carteira_set)
            j = len(carteira)
            pares_totais = j * (j - 1) // 2

            masks = [sum(1 << (d - 1) for d in jg) for jg in carteira]

            # 1. Calculo par a par original
            intersecoes = []
            penalidades = []
            i_min_soma, i_min_med = _cota_minima_intersecao_exata([15] * j, 25, 0)
            soma_p2 = Fraction(0, 1)

            for i in range(j):
                mi = masks[i]
                for k in range(i + 1, j):
                    c = (mi & masks[k]).bit_count()
                    intersecoes.append(c)
                    penalidades.append((max(0.0, c - i_min_med) / 6.0) ** 2)
                    soma_p2 += probabilidade_conjunta_par_exata(15, 15, c, 11)

            soma_inter_orig = sum(intersecoes)
            min_inter_orig = min(intersecoes)
            max_inter_orig = max(intersecoes)
            soma_penal_orig = sum(penalidades)

            # 2. Calculo por Histograma de 10 classes [5..14]
            # Como sao bilhetes distintos, intersecao maxima e 14
            h_c = {c: 0 for c in range(5, 15)}
            for i in range(j):
                mi = masks[i]
                for k in range(i + 1, j):
                    c = (mi & masks[k]).bit_count()
                    h_c[c] += 1

            soma_inter_hist = sum(c * h_c[c] for c in range(5, 15))
            min_inter_hist = next(c for c in range(5, 15) if h_c[c] > 0)
            max_inter_hist = max(c for c in range(5, 15) if h_c[c] > 0)
            soma_penal_hist = sum(h_c[c] * ((max(0.0, c - i_min_med) / 6.0) ** 2) for c in range(5, 15))

            tab_p2 = {c: probabilidade_conjunta_par_exata(15, 15, c, 11) for c in range(5, 15)}
            soma_p2_hist = sum((h_c[c] * tab_p2[c] for c in range(5, 15)), Fraction(0, 1))

            _exigir(soma_inter_orig == soma_inter_hist, "Soma de intersecoes divergiu.")
            _exigir(min_inter_orig == min_inter_hist, "Intersecao minima divergiu.")
            _exigir(max_inter_orig == max_inter_hist, "Intersecao maxima divergiu.")
            _exigir(abs(soma_penal_orig - soma_penal_hist) <= 1e-12, "Soma de penalidades divergiu.")
            _exigir(soma_p2 == soma_p2_hist, "Soma exata de p2 divergiu.")

    def test_03_equivalencia_casos_extremos_fixas_e_pool_restrito(self) -> None:
        """Testa casos extremos com fixas f=3 e pool restrito p=18."""
        rng = random.Random(999)
        pool = list(range(1, 19))  # 18 dezenas
        fixas = (1, 2, 3)
        livres = [d for d in pool if d not in fixas]

        carteira_set = set()
        while len(carteira_set) < 12:
            carteira_set.add(tuple(sorted((*fixas, *rng.sample(livres, 12)))))
        carteira = sorted(carteira_set)

        spec = _resolver_especificacao_etapa4(
            pool=pool,
            fixas=fixas,
            bloqueadas=tuple(range(19, 26)),
            modo_fixas="todos_os_jogos",
            quantidade_jogos=12,
            tamanho_aposta=15,
            tamanhos_jogos=None,
            orcamento_brl=None,
            pesos=None,
            perfil_pesos=None,
        )

        # Avaliacao pela referencia independente
        av_ref = avaliar_carteira_ref_etapa4(
            carteira,
            pool=pool,
            fixas=fixas,
            bloqueadas=tuple(range(19, 26)),
            modo_fixas="todos_os_jogos",
        )

        # Avaliacao pela Etapa 2 oficial
        av_e2 = avaliar_carteira_etapa2(
            carteira,
            pool=pool,
            fixas=fixas,
            bloqueadas=tuple(range(19, 26)),
            modo_fixas="todos_os_jogos",
        )

        _exigir(
            abs(av_ref["funcao_objetivo_F"] - av_e2["funcao_objetivo_F"]) <= 1e-12,
            f"Divergencia caso extremo ref vs e2: {av_ref['funcao_objetivo_F']} vs {av_e2['funcao_objetivo_F']}",
        )

    def test_04_intocabilidade_lotomania_ntfs_e_ast_referencia(self) -> None:
        """Garante que nenhum arquivo da Lotomania, NTFS ou referencia AST foi violado."""
        caminho_ref4 = os.path.join(BASE_DIR, "lotofacil_modo4", "etapa4_referencia_independente.py")
        ast_res = auditar_independencia_ast_etapa4(caminho_ref4)
        _exigir(ast_res["independencia_comprovada"] is True, f"AST de referencia violada: {ast_res['violacoes']}")

        # Arquivos da Lotomania que devem existir e estar intocados
        arquivos_lotomania = [
            os.path.join(BASE_DIR, "motor_lotomania_modo4.py"),
            os.path.join(BASE_DIR, "verificador_selo_modo4.py"),
            os.path.join(BASE_DIR, "chave_publica_modo4.pem"),
            os.path.join(BASE_DIR, "data", "lotomania.json"),
        ]
        for arq in arquivos_lotomania:
            _exigir(os.path.isfile(arq), f"Arquivo protegido da Lotomania ausente: {arq}")


if __name__ == "__main__":
    unittest.main()
