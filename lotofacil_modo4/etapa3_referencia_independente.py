# -*- coding: utf-8 -*-
"""
ETAPA 3: IMPLEMENTACAO DE REFERENCIA INDEPENDENTE E AUDITORIA DE RESTRICOES
===========================================================================
Implementacao totalmente desacoplada de `etapa3_otimizadores.py` e
`etapa2_funcao_objetivo.py`, utilizando apenas `etapa1_regras_oficiais.py` e
`etapa2_referencia_independente.py` para conferencia independente:
  1. Auditoria estrutural de conformidade da carteira com todas as restricoes;
  2. Solucionador exato independente por enumeracao exaustiva para instancias pequenas;
  3. Conferencia cruzada independente dos escores de qualquer otimizador da Etapa 3.
"""

from __future__ import annotations

from decimal import Decimal
import itertools
import math
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .etapa1_regras_oficiais import (
    MAX_DEZENAS_APOSTA,
    MIN_DEZENAS_APOSTA,
    PRECO_APOSTA_SIMPLES,
    TAMANHO_SORTEIO,
    UNIVERSO_TOTAL,
    validar_aposta_lotofacil,
)
from .etapa2_referencia_independente import avaliar_carteira_referencia_independente


def auditar_conformidade_carteira_referencia(
    carteira: Iterable[Iterable[int]],
    pool: Iterable[int],
    fixas: Iterable[int] = (),
    bloqueadas: Iterable[int] = (),
    modo_fixas: str = "todos_os_jogos",
    tamanhos_esperados: Optional[Sequence[int]] = None,
    orcamento_max_brl: Optional[Decimal | str] = None,
) -> Dict[str, Any]:
    """
    Auditor independente de restricoes: verifica se a carteira respeita
    pool, bloqueadas, modo_fixas, unicidade de bilhetes, dimensoes e orcamento.
    """
    pool_set = set(pool)
    fixas_set = set(fixas)
    bloq_set = set(bloqueadas)
    violacoes: List[str] = []

    if modo_fixas not in ("todos_os_jogos", "composicao_pool"):
        violacoes.append(f"modo_fixas invalido: {modo_fixas!r}")
    if not (TAMANHO_SORTEIO <= len(pool_set) <= UNIVERSO_TOTAL):
        violacoes.append(f"Tamanho do pool fora de [15..25]: {len(pool_set)}")
    if not fixas_set.issubset(pool_set):
        violacoes.append(f"Fixas fora do pool: {sorted(fixas_set - pool_set)}")
    if fixas_set & bloq_set:
        violacoes.append(f"Fixas e bloqueadas em conflito: {sorted(fixas_set & bloq_set)}")
    if pool_set & bloq_set:
        violacoes.append(f"Pool contem bloqueadas: {sorted(pool_set & bloq_set)}")

    jogos = [validar_aposta_lotofacil(jg) for jg in carteira]
    if not jogos:
        violacoes.append("Carteira vazia.")
    if len(set(jogos)) != len(jogos):
        violacoes.append("Carteira contem bilhetes duplicados.")

    for idx, jg in enumerate(jogos):
        s_jg = set(jg)
        if not s_jg.issubset(pool_set):
            violacoes.append(f"Jogo {idx} possui dezenas fora do pool: {sorted(s_jg - pool_set)}")
        if s_jg & bloq_set:
            violacoes.append(f"Jogo {idx} possui dezenas bloqueadas: {sorted(s_jg & bloq_set)}")
        if modo_fixas == "todos_os_jogos" and not fixas_set.issubset(s_jg):
            violacoes.append(f"Jogo {idx} nao contem todas as fixas: faltando {sorted(fixas_set - s_jg)}")

    tamanhos_reais = sorted(len(jg) for jg in jogos)
    if tamanhos_esperados is not None and tamanhos_reais != sorted(tamanhos_esperados):
        violacoes.append(f"Dimensoes divergentes: obtido {tamanhos_reais} vs esperado {sorted(tamanhos_esperados)}")

    custo = sum((PRECO_APOSTA_SIMPLES * Decimal(math.comb(len(jg), TAMANHO_SORTEIO)) for jg in jogos), Decimal("0.00"))
    if orcamento_max_brl is not None and custo > Decimal(str(orcamento_max_brl)):
        violacoes.append(f"Custo R$ {custo} excede orcamento R$ {orcamento_max_brl}")

    return {
        "conforme": len(violacoes) == 0,
        "violacoes": violacoes,
        "quantidade_jogos": len(jogos),
        "custo_total_brl": str(custo),
    }


def _chave_desempate_referencia(
    jogos_canonicos: Tuple[Tuple[int, ...], ...],
    av_ref: Mapping[str, Any],
    pool_ord: Tuple[int, ...],
    fixas_jogo: Tuple[int, ...],
) -> Tuple[Any, ...]:
    comps = av_ref["componentes"]
    sets = [set(jg) for jg in jogos_canonicos]
    j = len(sets)
    if j <= 1:
        inter_max = 0
    else:
        inter_max = max(len(sets[i] & sets[k]) for i in range(j) for k in range(i + 1, j))

    livres = [d for d in pool_ord if d not in set(fixas_jogo)]
    if not livres:
        ss_obs = 0.0
    else:
        m_livre = sum(len(jg) - len(fixas_jogo) for jg in jogos_canonicos)
        mu = m_livre / len(livres)
        ss_obs = sum((sum(1 for cj in sets if d in cj) - mu) ** 2 for d in livres)

    return (
        round(float(av_ref["funcao_objetivo_F"]), 12),
        round(float(comps["cobertura_combinatoria"]), 12),
        round(float(comps["probabilidade_conjunta"]), 12),
        -int(inter_max),
        -round(float(ss_obs), 12),
        tuple(tuple(-d for d in jg) for jg in jogos_canonicos),
    )


def resolver_exato_referencia_independente(
    pool: Iterable[int],
    fixas: Iterable[int] = (),
    bloqueadas: Iterable[int] = (),
    modo_fixas: str = "todos_os_jogos",
    quantidade_jogos: int = 1,
    tamanho_aposta: int = TAMANHO_SORTEIO,
    pesos: Optional[Mapping[str, float]] = None,
    limite_combinacoes_exatas: int = 15_000,
) -> Dict[str, Any]:
    """
    Solucionador exato independente via enumeracao combinatoria completa sobre
    `avaliar_carteira_referencia_independente`.
    """
    pool_ord = tuple(sorted(set(pool)))
    fixas_ord = tuple(sorted(set(fixas)))
    bloq_ord = tuple(sorted(set(bloqueadas)))
    if pool_ord and (set(pool_ord) & set(bloq_ord)):
        raise ValueError("Conflito pool x bloqueadas.")
    if not (MIN_DEZENAS_APOSTA <= tamanho_aposta <= MAX_DEZENAS_APOSTA):
        raise ValueError("tamanho_aposta fora de [15..20].")

    fixas_jogo = fixas_ord if modo_fixas == "todos_os_jogos" else ()
    livres = tuple(d for d in pool_ord if d not in set(fixas_jogo))
    candidatos = [
        tuple(sorted((*fixas_jogo, *comb)))
        for comb in itertools.combinations(livres, tamanho_aposta - len(fixas_jogo))
    ]
    total_cartes = math.comb(len(candidatos), quantidade_jogos)
    if total_cartes > limite_combinacoes_exatas:
        raise ValueError(f"Espaco C({len(candidatos)},{quantidade_jogos}) = {total_cartes} acima do limite exato.")

    melhor_chave: Optional[Tuple[Any, ...]] = None
    melhor_cart: Optional[Tuple[Tuple[int, ...], ...]] = None
    melhor_av: Optional[Dict[str, Any]] = None

    for comb_cart in itertools.combinations(candidatos, quantidade_jogos):
        cart_ord = tuple(sorted(comb_cart))
        av = avaliar_carteira_referencia_independente(
            cart_ord, pool=pool_ord, fixas=fixas_ord, pesos=pesos, modo_fixas=modo_fixas
        )
        ch = _chave_desempate_referencia(cart_ord, av, pool_ord, fixas_jogo)
        if melhor_chave is None or ch > melhor_chave:
            melhor_chave = ch
            melhor_cart = cart_ord
            melhor_av = av

    assert melhor_cart is not None and melhor_av is not None
    return {
        "total_carteiras_enumeradas": total_cartes,
        "carteira_otima": [list(jg) for jg in melhor_cart],
        "funcao_objetivo_F": melhor_av["funcao_objetivo_F"],
        "avaliacao_referencia": melhor_av,
        "chave_desempate": melhor_chave,
    }


def verificar_equivalencia_etapa3_contra_referencia(
    resultado_etapa3: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Verifica independentemente um resultado emitido por qualquer algoritmo da
    Etapa 3 (conformidade de restricoes + igualdade numerica F(C) e custo).
    """
    params = resultado_etapa3["parametros_execucao"]
    cart = resultado_etapa3["carteira_otimizada"]
    aud = auditar_conformidade_carteira_referencia(
        carteira=cart,
        pool=params["pool"],
        fixas=params["fixas"],
        bloqueadas=params["bloqueadas"],
        modo_fixas=params["modo_fixas"],
        tamanhos_esperados=params["tamanhos_jogos"],
        orcamento_max_brl=params["custo_total_brl"],
    )
    av_ref = avaliar_carteira_referencia_independente(
        carteira=cart,
        pool=params["pool"],
        fixas=params["fixas"],
        pesos=params["pesos"],
        modo_fixas=params["modo_fixas"],
    )
    diff_f = abs(float(resultado_etapa3["funcao_objetivo_F"]) - float(av_ref["funcao_objetivo_F"]))
    return {
        "conforme_restricoes": aud["conforme"],
        "violacoes": aud["violacoes"],
        "diferenca_F_modulo": diff_f,
        "equivalente_1e_12": bool(aud["conforme"] and diff_f <= 1e-12),
        "custo_referencia_brl": av_ref["custo_total_brl"],
    }
