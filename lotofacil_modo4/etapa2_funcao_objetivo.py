# -*- coding: utf-8 -*-
"""
ETAPA 2: ESPECIFICACAO DAS FUNCOES OBJETIVO E CRITERIOS DE OTIMIZACAO
======================================================================
Define formalmente o modelo matematico de avaliacao de carteiras da Lotofacil,
com separacao explicita entre:
  - Componentes EXATOS (combinatoria fechada, covariancia/variancia conjunta p_2(c),
    cotas de Cauchy-Schwarz/Johnson, Dawson-Sankoff e Hunter-Worsley, unicidade e custo);
  - Componentes HEURISTICOS (regularizacao de sobreposicao, suavizacao de uso das
    dezenas e diversidade estrutural entre bilhetes);
  - Componentes DESCRITIVOS (aderencia teorica/historica de paridade, soma e matriz 5x5),
    mantidos com peso preditivo nulo por imposicao de codigo.

Nao depende de libs externas (apenas Python stdlib + Etapa 1).
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
from functools import lru_cache
import itertools
import math
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .etapa1_regras_oficiais import (
    CENTRO_5X5,
    CLAUSULA_MATEMATICA_OBRIGATORIA,
    COLUNAS_5X5,
    DIAGONAL_PRINCIPAL_5X5,
    DIAGONAL_SECUNDARIA_5X5,
    ESPACO_AMOSTRAL_SIMPLES,
    FIBONACCI_25,
    LINHAS_5X5,
    MAX_DEZENAS_APOSTA,
    MIN_DEZENAS_APOSTA,
    MOLDURA_5X5,
    MULTIPLOS_3_25,
    MULTIPLOS_5_25,
    PRECO_APOSTA_SIMPLES,
    PRIMOS_25,
    TAMANHO_SORTEIO,
    UNIVERSO_TOTAL,
    ErroValidacaoLotofacilError,
    custo_aposta_oficial,
    distribuicao_hipergeometrica_aposta,
    multiplicidade_premios_aposta,
    probabilidade_pelo_menos_k_exata,
    validar_aposta_lotofacil,
    validar_inteiro_estrito,
    validar_natureza_componente,
)

VERSAO_MODELO_OBJETIVO_ETAPA2 = "2.1.0-etapa2-ressalvas"

MODOS_FIXAS_PERMITIDOS = ("todos_os_jogos", "composicao_pool")

CATEGORIAS_PROVA_CIENTIFICA = MappingProxyType(
    {
        "VALIDACAO_EXAUSTIVA_UNIVERSO_SORTEIOS": (
            "Enumeracao completa dos 3.268.760 sorteios possiveis C(25,15) para carteiras ou pares especificos."
        ),
        "VALIDACAO_CASOS_ESPECIFICOS_CARTEIRAS": (
            "Conferencia exata de formulas matematicas e custos para exemplos e carteiras nominais."
        ),
        "COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS": (
            "Comparacao empirica controlada sob identico pool, restricoes, orcamento, semente e limite computacional."
        ),
        "PROVA_OTIMO_GLOBAL_INSTANCIA_PEQUENA": (
            "Enumeracao exaustiva de todas as carteiras admissiveis de uma instancia pequena garantindo otimalidade global."
        ),
        "DEMONSTRACAO_PROPRIEDADE_MATEMATICA_GERAL": (
            "Teorema analitico valido para todo o dominio (ex.: impossibilidade simultanea c <= 6, cotas Schur/DS/HW)."
        ),
    }
)

# Ordem fixa dos 6 componentes da funcao objetivo principal
NOMES_COMPONENTES = (
    "cobertura_combinatoria",
    "probabilidade_conjunta",
    "diversificacao_sobreposicao",
    "distribuicao_dezenas",
    "custo_beneficio",
    "diversidade_estrutural",
)

ESPECIFICACAO_COMPONENTES_ETAPA2 = MappingProxyType(
    {
        "cobertura_combinatoria": MappingProxyType(
            {
                "codigo": "S_cov",
                "fundamento_cientifico": "EXATO",
                "direcao": "maximizar",
                "dominio": "[0, 1]",
                "descricao": (
                    "Media ponderada da eficiencia combinatoria exata de cobertura de subconjuntos "
                    "t in {1,2,3,4} em P normalizada pela cota intransponivel U_t(J, p, f)."
                ),
            }
        ),
        "probabilidade_conjunta": MappingProxyType(
            {
                "codigo": "S_prob",
                "fundamento_cientifico": "EXATO",
                "papel_exato": "metrica_de_otimizacao_baseada_em_probabilidades_pareadas_e_limites",
                "nao_equivale_a": "probabilidade_exata_da_uniao_para_J_maior_que_2",
                "direcao": "maximizar",
                "dominio": "[0, 1]",
                "descricao": (
                    "Metrica de otimizacao baseada em probabilidades pareadas exatas p_2(m_i, m_k, I_ik) "
                    "e limites matematicos (Cauchy-Schwarz, Dawson-Sankoff e Hunter-Worsley), reduzindo "
                    "a soma de covariancias e a variancia Var(N_prem(C)); nao deve ser confundida com o "
                    "valor exato de P(U_i A_i) em carteiras com 3 ou mais bilhetes."
                ),
            }
        ),
        "diversificacao_sobreposicao": MappingProxyType(
            {
                "codigo": "S_div",
                "fundamento_cientifico": "HEURISTICO",
                "base_matematica_exata": "Cota inferior inteira S_{I,min} (Cauchy-Schwarz/Schur) e distancias exatas I_ij, d_H",
                "direcao": "maximizar",
                "dominio": "[0, 1]",
                "descricao": (
                    "Penalizacao quadratica de picos de sobreposicao I_ij acima da cota minima "
                    "teorica combinada ao excesso medio normalizado entre pares de bilhetes."
                ),
            }
        ),
        "distribuicao_dezenas": MappingProxyType(
            {
                "codigo": "S_dist",
                "fundamento_cientifico": "HEURISTICO",
                "base_matematica_exata": "Cota inferior inteira exata SS_min = r(1 - r/p_livre) para variancia de uso",
                "direcao": "maximizar",
                "dominio": "[0, 1]",
                "descricao": (
                    "Aproximacao ao equilibrio uniforme inteiro u_d das dezenas livres do pool, "
                    "evitando concentracao artificial ou abandono de candidatas."
                ),
            }
        ),
        "custo_beneficio": MappingProxyType(
            {
                "codigo": "S_cb",
                "fundamento_cientifico": "EXATO",
                "direcao": "maximizar",
                "dominio": "[0, 1]",
                "descricao": (
                    "Unicidade exata de combinacoes simples pagas combinada a densidade de pares "
                    "cobertos por investimento em comparacao ao limite combinatorio do orcamento."
                ),
            }
        ),
        "diversidade_estrutural": MappingProxyType(
            {
                "codigo": "S_div_est",
                "fundamento_cientifico": "HEURISTICO",
                "direcao": "maximizar",
                "dominio": "[0, 1]",
                "descricao": (
                    "Dispersao dos perfis estruturais (paridade, moldura/centro, faixas de soma) "
                    "e equilibrio de ocupacao de linhas e colunas da matriz 5x5 sem carater preditivo."
                ),
            }
        ),
    }
)

# Pesos somam exatamente 1.00; perfis alternativos servem para analise de sensibilidade
PERFIS_PESOS_ETAPA2 = MappingProxyType(
    {
        "padrao_modo4": MappingProxyType(
            {
                "cobertura_combinatoria": 0.30,
                "probabilidade_conjunta": 0.25,
                "diversificacao_sobreposicao": 0.20,
                "distribuicao_dezenas": 0.10,
                "custo_beneficio": 0.10,
                "diversidade_estrutural": 0.05,
            }
        ),
        "foco_cobertura_subconjuntos": MappingProxyType(
            {
                "cobertura_combinatoria": 0.45,
                "probabilidade_conjunta": 0.20,
                "diversificacao_sobreposicao": 0.15,
                "distribuicao_dezenas": 0.05,
                "custo_beneficio": 0.10,
                "diversidade_estrutural": 0.05,
            }
        ),
        "foco_minima_redundancia": MappingProxyType(
            {
                "cobertura_combinatoria": 0.20,
                "probabilidade_conjunta": 0.35,
                "diversificacao_sobreposicao": 0.25,
                "distribuicao_dezenas": 0.10,
                "custo_beneficio": 0.05,
                "diversidade_estrutural": 0.05,
            }
        ),
        "foco_equilibrio_matriz_pool": MappingProxyType(
            {
                "cobertura_combinatoria": 0.25,
                "probabilidade_conjunta": 0.20,
                "diversificacao_sobreposicao": 0.20,
                "distribuicao_dezenas": 0.20,
                "custo_beneficio": 0.05,
                "diversidade_estrutural": 0.10,
            }
        ),
    }
)

# Esperancas matematicas teoricas exatas da hipergeometrica H(25, 15) por bilhete simples
ESPERANCAS_TEORICAS_BILHETE_SIMPLES = MappingProxyType(
    {
        "pares": Fraction(15 * 12, 25),            # 36/5 = 7.20
        "impares": Fraction(15 * 13, 25),          # 39/5 = 7.80
        "soma": Fraction(15 * sum(range(1, 26)), 25),  # 195
        "moldura": Fraction(15 * 16, 25),          # 48/5 = 9.60
        "centro": Fraction(15 * 9, 25),            # 27/5 = 5.40
        "grupo_a_01_13": Fraction(15 * 13, 25),    # 39/5 = 7.80
        "grupo_b_14_25": Fraction(15 * 12, 25),    # 36/5 = 7.20
        "primos": Fraction(15 * len(PRIMOS_25), 25),      # 27/5 = 5.40
        "fibonacci": Fraction(15 * len(FIBONACCI_25), 25),  # 21/5 = 4.20
    }
)


def _mascara_dezenas(dezenas: Iterable[int]) -> int:
    m = 0
    for d in dezenas:
        m |= 1 << (d - 1)
    return m


@lru_cache(maxsize=256)
def probabilidade_conjunta_par_exata(m1: int, m2: int, c: int, k_min: int = 11) -> Fraction:
    """
    Calcula exatamente P(|B1 inter S| >= k_min e |B2 inter S| >= k_min) sobre
    todos os C(25,15) = 3.268.760 sorteios possiveis, dadas as cardinalidades
    m1 = |B1|, m2 = |B2| (em [15..20]) e intersecao c = |B1 inter B2|.

    Usa particao tetranomial exata dos 25 elementos em:
      n0 = c (B1 inter B2)
      n1 = m1 - c (B1 - B2)
      n2 = m2 - c (B2 - B1)
      n3 = 25 - m1 - m2 + c (fora de B1 U B2)
    """
    m1_ok = validar_inteiro_estrito(m1, "m1", MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA)
    m2_ok = validar_inteiro_estrito(m2, "m2", MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA)
    k_ok = validar_inteiro_estrito(k_min, "k_min", 1, TAMANHO_SORTEIO)
    c_min = max(0, m1_ok + m2_ok - UNIVERSO_TOTAL)
    c_max = min(m1_ok, m2_ok)
    c_ok = validar_inteiro_estrito(c, "c", c_min, c_max)

    n0 = c_ok
    n1 = m1_ok - c_ok
    n2 = m2_ok - c_ok
    n3 = UNIVERSO_TOTAL - m1_ok - m2_ok + c_ok

    favoraveis = 0
    for x0 in range(0, min(n0, TAMANHO_SORTEIO) + 1):
        c0 = math.comb(n0, x0)
        x1_min = max(0, k_ok - x0)
        x1_max = min(n1, TAMANHO_SORTEIO - x0)
        if x1_min > x1_max:
            continue
        for x1 in range(x1_min, x1_max + 1):
            c01 = c0 * math.comb(n1, x1)
            x2_min = max(0, k_ok - x0)
            x2_max = min(n2, TAMANHO_SORTEIO - x0 - x1)
            if x2_min > x2_max:
                continue
            for x2 in range(x2_min, x2_max + 1):
                x3 = TAMANHO_SORTEIO - x0 - x1 - x2
                if 0 <= x3 <= n3:
                    favoraveis += c01 * math.comb(n2, x2) * math.comb(n3, x3)

    return Fraction(favoraveis, ESPACO_AMOSTRAL_SIMPLES)


def construir_tabela_p2_simples() -> Mapping[int, Mapping[str, Any]]:
    """
    Gera a tabela exata de probabilidades conjuntas p_2(c) para dois bilhetes
    simples de 15 dezenas com intersecao c in [5..15].
    """
    p1 = probabilidade_pelo_menos_k_exata(MIN_DEZENAS_APOSTA, 11)
    tabela: Dict[int, Mapping[str, Any]] = {}
    anterior = Fraction(-1, 1)
    for c in range(5, 16):
        p2 = probabilidade_conjunta_par_exata(15, 15, c, 11)
        if p2 < anterior:
            raise ErroValidacaoLotofacilError(
                f"Quebra de monotonicidade em p_2(c): p_2({c})={p2} < anterior={anterior}."
            )
        anterior = p2
        cov = p2 - (p1 * p1)
        p_uniao = (2 * p1) - p2
        tabela[c] = MappingProxyType(
            {
                "intersecao": c,
                "p2_fracao": f"{p2.numerator}/{p2.denominator}",
                "p2_exact": p2,
                "p2_float": float(p2),
                "covariancia_exact": cov,
                "covariancia_float": float(cov),
                "prob_uniao_2_jogos_exact": p_uniao,
                "prob_uniao_2_jogos_float": float(p_uniao),
                "correlacao_pearson": float(cov / (p1 * (1 - p1))),
            }
        )
    if tabela[15]["p2_exact"] != p1:
        raise ErroValidacaoLotofacilError("Invariante p_2(15) == p_1 violada.")
    return MappingProxyType(tabela)


TABELA_P2_CONJUNTA_EXATA = construir_tabela_p2_simples()


def probabilidade_conjunta_par_quatro_regioes_detalhada(
    m1: int,
    m2: int,
    c: int,
    k_min: int = 11,
) -> Dict[str, Any]:
    """
    Formalizacao explicita pela particao hipergeometrica de quatro regioes
    para apostas simples e multiplas (15 a 20 dezenas):
      - n0 = c: intersecao dos dois bilhetes (B1 inter B2)
      - n1 = m1 - c: dezenas exclusivas do primeiro bilhete (B1 - B2)
      - n2 = m2 - c: dezenas exclusivas do segundo bilhete (B2 - B1)
      - n3 = 25 - m1 - m2 + c: dezenas externas aos dois bilhetes (U - (B1 U B2))
    """
    m1_ok = validar_inteiro_estrito(m1, "m1", MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA)
    m2_ok = validar_inteiro_estrito(m2, "m2", MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA)
    k_ok = validar_inteiro_estrito(k_min, "k_min", 1, TAMANHO_SORTEIO)
    c_min = max(0, m1_ok + m2_ok - UNIVERSO_TOTAL)
    c_max = min(m1_ok, m2_ok)
    c_ok = validar_inteiro_estrito(c, "c", c_min, c_max)

    p1 = probabilidade_pelo_menos_k_exata(m1_ok, k_ok)
    p2_b2 = probabilidade_pelo_menos_k_exata(m2_ok, k_ok)
    p_conj = probabilidade_conjunta_par_exata(m1_ok, m2_ok, c_ok, k_ok)
    p_uniao = p1 + p2_b2 - p_conj
    cov = p_conj - (p1 * p2_b2)
    denom_corr = math.sqrt(float(p1 * (1 - p1) * p2_b2 * (1 - p2_b2)))
    corr = float(cov) / denom_corr if denom_corr > 0 else 0.0

    return {
        "m1": m1_ok,
        "m2": m2_ok,
        "intersecao_c": c_ok,
        "limiar_acertos_k_min": k_ok,
        "regioes": {
            "n0_intersecao": c_ok,
            "n1_exclusivas_primeiro": m1_ok - c_ok,
            "n2_exclusivas_segundo": m2_ok - c_ok,
            "n3_externas_aos_dois": UNIVERSO_TOTAL - m1_ok - m2_ok + c_ok,
        },
        "condicao_x0_minima_disjuncao": max(0, 2 * k_ok - TAMANHO_SORTEIO),
        "p_individual_b1_exact": p1,
        "p_individual_b2_exact": p2_b2,
        "p_conjunta_exact": p_conj,
        "p_conjunta_fracao": f"{p_conj.numerator}/{p_conj.denominator}",
        "p_conjunta_float": float(p_conj),
        "p_uniao_exact": p_uniao,
        "p_uniao_fracao": f"{p_uniao.numerator}/{p_uniao.denominator}",
        "p_uniao_float": float(p_uniao),
        "covariancia_exact": cov,
        "covariancia_float": float(cov),
        "correlacao_pearson": corr,
    }


def construir_tabela_p2_multiplas() -> Mapping[Tuple[int, int], Mapping[int, Mapping[str, Any]]]:
    """
    Constroi a tabela completa de probabilidades conjuntas p_2(m1, m2, c)
    para todos os pares 15 <= m1 <= m2 <= 20 e toda intersecao viavel c,
    verificando monotonicidade nao decrescente em c e igualdade p_2(m, m, m) == p_1(m).
    """
    matriz: Dict[Tuple[int, int], Mapping[int, Mapping[str, Any]]] = {}
    for m1 in range(MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA + 1):
        for m2 in range(m1, MAX_DEZENAS_APOSTA + 1):
            c_min = max(0, m1 + m2 - UNIVERSO_TOTAL)
            c_max = min(m1, m2)
            por_c: Dict[int, Mapping[str, Any]] = {}
            anterior = Fraction(-1, 1)
            for c in range(c_min, c_max + 1):
                det = probabilidade_conjunta_par_quatro_regioes_detalhada(m1, m2, c, 11)
                if det["p_conjunta_exact"] < anterior:
                    raise ErroValidacaoLotofacilError(
                        f"Quebra de monotonicidade em p_2({m1},{m2},{c})."
                    )
                anterior = det["p_conjunta_exact"]
                por_c[c] = MappingProxyType(det)
            if m1 == m2 and por_c[m1]["p_conjunta_exact"] != por_c[m1]["p_individual_b1_exact"]:
                raise ErroValidacaoLotofacilError(f"Invariante p_2({m1},{m1},{m1}) == p_1({m1}) violada.")
            matriz[(m1, m2)] = MappingProxyType(por_c)
    return MappingProxyType(matriz)


TABELA_P2_MULTIPLAS_15_A_20 = construir_tabela_p2_multiplas()


def validar_pesos_objetivo(pesos: Optional[Mapping[str, Any]] = None) -> Dict[str, float]:
    """
    Valida estritamente o vetor de pesos da funcao objetivo:
      - Deve conter exatamente os 6 componentes permitidos (sem indicadores descritivos
        ou preditivos nao autorizados).
      - Todos os pesos devem estar em [0, 1] e somar exatamente 1.0 (tolerancia 1e-9).
    """
    if pesos is None:
        return dict(PERFIS_PESOS_ETAPA2["padrao_modo4"])
    if not isinstance(pesos, Mapping):
        raise ErroValidacaoLotofacilError("Pesos devem ser um mapeamento componente -> valor.")

    chaves_esperadas = set(NOMES_COMPONENTES)
    chaves_recebidas = set(pesos.keys())
    if chaves_recebidas != chaves_esperadas:
        raise ErroValidacaoLotofacilError(
            f"Conjunto de chaves de peso invalido. Esperado: {sorted(chaves_esperadas)}; "
            f"recebido: {sorted(chaves_recebidas)}."
        )

    validados: Dict[str, float] = {}
    for nome in NOMES_COMPONENTES:
        val = pesos[nome]
        if isinstance(val, bool) or not isinstance(val, (int, float, Decimal)):
            raise ErroValidacaoLotofacilError(f"Peso '{nome}' deve ser numerico; recebido {val!r}.")
        fval = float(val)
        if not math.isfinite(fval) or fval < 0.0 or fval > 1.0:
            raise ErroValidacaoLotofacilError(f"Peso '{nome}' ({fval}) fora de [0.0, 1.0].")
        spec = ESPECIFICACAO_COMPONENTES_ETAPA2[nome]
        validar_natureza_componente(spec["fundamento_cientifico"], usa_como_ganho_preditivo=False)
        validados[nome] = fval

    soma = sum(validados.values())
    if abs(soma - 1.0) > 1e-9:
        raise ErroValidacaoLotofacilError(
            f"Soma dos pesos da funcao objetivo deve ser 1.0; obtido {soma:.12f}."
        )
    return validados


def validar_pool_e_restricoes(
    pool: Iterable[int],
    fixas: Iterable[int] = (),
    bloqueadas: Iterable[int] = (),
    quantidade_jogos: Optional[int] = None,
    tamanho_jogo: int = TAMANHO_SORTEIO,
    modo_fixas: str = "todos_os_jogos",
) -> Dict[str, Any]:
    """
    Valida viabilidade combinatoria do pool (15..25), fixas, bloqueadas,
    modo formal das dezenas fixas e quantidade solicitada de jogos distintos
    (fail-closed sem ajustes silenciosos).

    Modos formais de dezenas fixas (`modo_fixas`):
      - "todos_os_jogos": F subconjunto obrigatorio de CADA bilhete B_i (exige |F| <= tamanho_jogo).
      - "composicao_pool": F obrigatorio apenas na composicao do pool P (permite |F| ate |P|
        sem exigir que cada bilhete individual contenha todas as dezenas de F).
    """
    if modo_fixas not in MODOS_FIXAS_PERMITIDOS:
        raise ErroValidacaoLotofacilError(
            f"modo_fixas invalido '{modo_fixas}'. Permitidos: {MODOS_FIXAS_PERMITIDOS}."
        )
    m_ok = validar_inteiro_estrito(tamanho_jogo, "tamanho_jogo", MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA)
    if isinstance(pool, (str, bytes)) or not isinstance(pool, Iterable):
        raise ErroValidacaoLotofacilError("Pool deve ser um iteravel de dezenas inteiras.")

    pool_list = list(pool)
    for idx, d in enumerate(pool_list):
        validar_inteiro_estrito(d, f"pool[{idx}]", 1, UNIVERSO_TOTAL)
    pool_ord = tuple(sorted(set(pool_list)))
    if len(pool_ord) != len(pool_list):
        raise ErroValidacaoLotofacilError("Pool contem dezenas duplicadas.")
    if not (TAMANHO_SORTEIO <= len(pool_ord) <= UNIVERSO_TOTAL):
        raise ErroValidacaoLotofacilError(
            f"Tamanho do pool ({len(pool_ord)}) deve estar entre 15 e 25."
        )
    if len(pool_ord) < m_ok:
        raise ErroValidacaoLotofacilError(
            f"Pool ({len(pool_ord)}) menor que o tamanho da aposta ({m_ok})."
        )

    fixas_list = list(fixas)
    for idx, d in enumerate(fixas_list):
        validar_inteiro_estrito(d, f"fixas[{idx}]", 1, UNIVERSO_TOTAL)
    fixas_ord = tuple(sorted(set(fixas_list)))
    if len(fixas_ord) != len(fixas_list):
        raise ErroValidacaoLotofacilError("Lista de dezenas fixas contem duplicatas.")

    bloq_list = list(bloqueadas)
    for idx, d in enumerate(bloq_list):
        validar_inteiro_estrito(d, f"bloqueadas[{idx}]", 1, UNIVERSO_TOTAL)
    bloq_ord = tuple(sorted(set(bloq_list)))
    if len(bloq_ord) != len(bloq_list):
        raise ErroValidacaoLotofacilError("Lista de dezenas bloqueadas contem duplicatas.")

    set_pool = set(pool_ord)
    set_fixas = set(fixas_ord)
    set_bloq = set(bloq_ord)

    conflito_fb = sorted(set_fixas & set_bloq)
    if conflito_fb:
        raise ErroValidacaoLotofacilError(
            f"Conflito de restricoes: dezenas simultaneamente fixas e bloqueadas: {conflito_fb}."
        )
    fora_pool = sorted(set_fixas - set_pool)
    if fora_pool:
        raise ErroValidacaoLotofacilError(
            f"Dezenas fixas fora do pool selecionado: {fora_pool}."
        )
    conflito_pb = sorted(set_pool & set_bloq)
    if conflito_pb:
        raise ErroValidacaoLotofacilError(
            f"Dezenas bloqueadas presentes no pool ativo: {conflito_pb}."
        )
    if len(set_pool) + len(set_bloq) > UNIVERSO_TOTAL:
        raise ErroValidacaoLotofacilError(
            f"|P| ({len(set_pool)}) + |E| ({len(set_bloq)}) excede o universo de 25 dezenas."
        )

    if modo_fixas == "todos_os_jogos":
        if len(fixas_ord) > m_ok:
            raise ErroValidacaoLotofacilError(
                f"No modo 'todos_os_jogos', quantidade de dezenas fixas ({len(fixas_ord)}) "
                f"excede tamanho da aposta ({m_ok}). Use modo_fixas='composicao_pool' para fixar apenas no pool."
            )
        fixas_por_jogo = fixas_ord
        livres_para_jogos = tuple(sorted(set_pool - set_fixas))
        max_jogos_distintos = math.comb(len(livres_para_jogos), m_ok - len(fixas_ord))
    else:
        # composicao_pool: F fixa a permanencia no pool, mas os bilhetes variam sobre todo P
        fixas_por_jogo = ()
        livres_para_jogos = pool_ord
        max_jogos_distintos = math.comb(len(pool_ord), m_ok)

    livres_no_pool = tuple(sorted(set_pool - set_fixas))
    if quantidade_jogos is not None:
        j_ok = validar_inteiro_estrito(quantidade_jogos, "quantidade_jogos", 1)
        if j_ok > max_jogos_distintos:
            raise ErroValidacaoLotofacilError(
                f"Impossivel gerar {j_ok} jogos distintos de {m_ok} dezenas em pool={len(pool_ord)} "
                f"(modo_fixas='{modo_fixas}', |F|={len(fixas_ord)}): teto combinatorio = {max_jogos_distintos}."
            )

    return {
        "pool": pool_ord,
        "tamanho_pool": len(pool_ord),
        "fixas": fixas_ord,
        "fixas_no_pool": fixas_ord,
        "fixas_por_jogo": fixas_por_jogo,
        "modo_fixas": modo_fixas,
        "quantidade_fixas": len(fixas_ord),
        "quantidade_fixas_por_jogo": len(fixas_por_jogo),
        "bloqueadas": bloq_ord,
        "livres": livres_para_jogos,
        "livres_no_pool": livres_no_pool,
        "quantidade_livres": len(livres_para_jogos),
        "tamanho_jogo": m_ok,
        "max_jogos_distintos": max_jogos_distintos,
        "diagnostico_compatibilidade": {
            "pool_subconjunto_universo": True,
            "fixas_contidas_em_pool": True,
            "fixas_disjuntas_bloqueadas": True,
            "pool_disjunto_bloqueadas": True,
            "cardinalidade_conjunta_valida": True,
            "modo_fixas_aplicado": modo_fixas,
        },
    }


def extrair_perfil_estrutural_jogo(dezenas: Iterable[int]) -> Dict[str, Any]:
    """
    Calcula indicadores estruturais e da matriz 5x5 para um jogo valido.
    Estes indicadores sao descritivos e de diversificacao combinatoria.
    """
    ord_dezs = validar_aposta_lotofacil(dezenas)
    m = len(ord_dezs)
    mask = _mascara_dezenas(ord_dezs)

    pares = sum(1 for d in ord_dezs if d % 2 == 0)
    impares = m - pares
    soma = sum(ord_dezs)
    moldura = sum(1 for d in ord_dezs if d in MOLDURA_5X5)
    centro = m - moldura
    primos = sum(1 for d in ord_dezs if d in PRIMOS_25)
    fibonacci = sum(1 for d in ord_dezs if d in FIBONACCI_25)
    mult3 = sum(1 for d in ord_dezs if d in MULTIPLOS_3_25)
    mult5 = sum(1 for d in ord_dezs if d in MULTIPLOS_5_25)
    grupo_a = sum(1 for d in ord_dezs if d <= 13)
    grupo_b = m - grupo_a

    # Contagem de blocos consecutivos e maior sequencia consecutiva
    blocos = 1
    run = 1
    max_seq = 1
    for i in range(1, m):
        if ord_dezs[i] == ord_dezs[i - 1] + 1:
            run += 1
            if run > max_seq:
                max_seq = run
        else:
            blocos += 1
            run = 1

    linhas = tuple(sum(1 for d in linha if d in ord_dezs) for linha in LINHAS_5X5)
    colunas = tuple(sum(1 for d in col if d in ord_dezs) for col in COLUNAS_5X5)
    diag_p = sum(1 for d in ord_dezs if d in DIAGONAL_PRINCIPAL_5X5)
    diag_s = sum(1 for d in ord_dezs if d in DIAGONAL_SECUNDARIA_5X5)

    return {
        "dezenas": ord_dezs,
        "mascara": mask,
        "tamanho": m,
        "pares": pares,
        "impares": impares,
        "soma": soma,
        "moldura": moldura,
        "centro": centro,
        "primos": primos,
        "fibonacci": fibonacci,
        "multiplos_3": mult3,
        "multiplos_5": mult5,
        "grupo_a_01_13": grupo_a,
        "grupo_b_14_25": grupo_b,
        "max_consecutivas": max_seq,
        "blocos_consecutivos": blocos,
        "linhas_5x5": linhas,
        "colunas_5x5": colunas,
        "diagonal_principal": diag_p,
        "diagonal_secundaria": diag_s,
    }


def _cota_minima_intersecao_exata(tamanhos: Sequence[int], p: int, f: int) -> Tuple[int, float]:
    """
    Calcula o minimo teorico exato possivel da soma de intersecoes pareadas
    sum_{1 <= i < j <= J} |B_i inter B_j| para J jogos dentro de pool p com f fixas.

    Prova exata: sum_{i<j} |B_i inter B_j| = sum_{d in P} C(u_d, 2).
    Para as f dezenas fixas, u_d = J => C(J, 2)*f.
    Para as p_livre = p - f dezenas livres, sum u_d = M_livre = sum(m_i - f).
    Por convexidade estrita de C(u, 2), a soma e minimizada unicamente quando
    os u_d assumem valores q e q+1 com M_livre = q * p_livre + r.
    """
    j = len(tamanhos)
    if j <= 1:
        return 0, 0.0
    pares_jogos = j * (j - 1) // 2
    soma_fixa = pares_jogos * f
    p_livre = p - f
    if p_livre <= 0:
        return soma_fixa, float(soma_fixa / pares_jogos)
    m_livre = sum(m - f for m in tamanhos)
    q, r = divmod(m_livre, p_livre)
    soma_livre = (p_livre - r) * math.comb(q, 2) + r * math.comb(q + 1, 2)
    total = soma_fixa + soma_livre
    return total, float(total / pares_jogos)


def _cota_minima_variancia_uso_exata(tamanhos: Sequence[int], p: int, f: int) -> Tuple[float, float, float]:
    """
    Retorna (media_livre, SS_min_exata, SS_max_exata) para u_d em P - F.
    """
    p_livre = p - f
    if p_livre <= 0:
        return 0.0, 0.0, 0.0
    livres_por_jogo = [m - f for m in tamanhos]
    if all(x == 0 for x in livres_por_jogo):
        return 0.0, 0.0, 0.0
    m_livre = sum(livres_por_jogo)
    mu = m_livre / p_livre
    _, r = divmod(m_livre, p_livre)
    ss_min = r * (1.0 - r / p_livre)

    # Pior caso exato permitido pelo pool: cada jogo i concentra seus (m_i - f)
    # marcacoes nas primeiras (m_i - f) dezenas livres.
    u_pior = [0] * p_livre
    for k_i in livres_por_jogo:
        for pos in range(min(k_i, p_livre)):
            u_pior[pos] += 1
    ss_max = sum((u - mu) ** 2 for u in u_pior)
    return mu, ss_min, max(ss_max, ss_min)


def _limite_dawson_sankoff(p_individuais: Sequence[Fraction], s2: Fraction) -> Fraction:
    """
    Calcula o limite inferior matematico de Dawson-Sankoff (1967) para P(U_{i=1}^J A_i)
    usando apenas S1 = sum P(A_i) e S2 = sum_{i<j} P(A_i inter A_j):
        P(U A_i) >= max_{k >= 1} ( 2*S1/(k+1) - 2*S2/(k*(k+1)) )
    Maximiza exatamente sobre o k inteiro otimo e k in {k_opt-1, k_opt, k_opt+1}.
    """
    if not p_individuais:
        return Fraction(0, 1)
    s1 = sum(p_individuais, Fraction(0, 1))
    if s1 <= 0:
        return Fraction(0, 1)
    melhor = max(p_individuais)
    j = len(p_individuais)
    if j == 1:
        return s1
    k_opt = int((2 * s2) // s1) + 1
    candidatos_k = {1, 2, max(1, k_opt - 1), k_opt, min(j, k_opt + 1)}
    for k in candidatos_k:
        if 1 <= k <= j:
            val = (2 * s1) / Fraction(k + 1, 1) - (2 * s2) / Fraction(k * (k + 1), 1)
            if val > melhor:
                melhor = val
    if melhor > Fraction(1, 1):
        melhor = Fraction(1, 1)
    return melhor


def _limite_hunter_worsley(p_individuais: Sequence[Fraction], matriz_p2: Sequence[Sequence[Fraction]]) -> Fraction:
    """
    Calcula o limite superior rigoroso de Hunter-Worsley (1976):
        P(U A_i) <= S1 - peso(Arvore Geradora Maxima sobre P(A_i inter A_j))
    Algoritmo deterministico de Prim em O(J^2) com aritmetica Fraction exata.
    """
    j = len(p_individuais)
    if j == 0:
        return Fraction(0, 1)
    s1 = sum(p_individuais, Fraction(0, 1))
    if j == 1:
        return min(Fraction(1, 1), s1)
    if j == 2:
        return min(Fraction(1, 1), s1 - matriz_p2[0][1])

    visitados = [False] * j
    melhor_aresta = [Fraction(-1, 1)] * j
    visitados[0] = True
    for v in range(1, j):
        melhor_aresta[v] = matriz_p2[0][v]

    soma_mst = Fraction(0, 1)
    for _ in range(j - 1):
        u = -1
        maior = Fraction(-2, 1)
        for cand in range(j):
            if not visitados[cand] and melhor_aresta[cand] > maior:
                maior = melhor_aresta[cand]
                u = cand
        if u < 0:
            break
        visitados[u] = True
        soma_mst += maior
        for v in range(j):
            if not visitados[v] and matriz_p2[u][v] > melhor_aresta[v]:
                melhor_aresta[v] = matriz_p2[u][v]

    cota_sup = s1 - soma_mst
    return min(Fraction(1, 1), max(Fraction(0, 1), cota_sup))


def avaliar_cobertura_subconjuntos_exata(
    jogos_validos: Sequence[Tuple[int, ...]],
    pool_ord: Tuple[int, ...],
    fixas_ord: Tuple[int, ...],
    ordens_t: Tuple[int, ...] = (1, 2, 3, 4),
) -> Dict[str, Any]:
    """
    Avalia exatamente a cobertura deterministica de t-subconjuntos do pool P
    para t in (1, 2, 3, 4) (dezenas, pares, trincas, quadras) e calcula a
    eficiencia contra o teto teorico intransponivel U_t(J, p, f).
    """
    p = len(pool_ord)
    f = len(fixas_ord)
    set_pool = set(pool_ord)
    for idx, jg in enumerate(jogos_validos):
        if not set(jg).issubset(set_pool):
            raise ErroValidacaoLotofacilError(f"Jogo {idx} contem dezenas fora do pool fornecido.")
        if not set(fixas_ord).issubset(set(jg)):
            raise ErroValidacaoLotofacilError(f"Jogo {idx} viola dezenas fixas obrigatorias.")

    resultados_t: Dict[int, Dict[str, Any]] = {}
    pesos_t = {1: 0.15, 2: 0.35, 3: 0.35, 4: 0.15}
    s_cov_composto = 0.0

    for t in ordens_t:
        total_pool_t = math.comb(p, t)
        cobertos_t: set[Tuple[int, ...]] = set()
        for jg in jogos_validos:
            cobertos_t.update(itertools.combinations(jg, t))

        # Cota superior exata de cobertura alcançavel por estes tamanhos de jogos
        # Cada jogo cobre no maximo C(m_i, t) - C(f, t) novos subconjuntos alem dos fixos.
        c_fixos = math.comb(f, t) if f >= t else 0
        soma_capacidade_nova = sum((math.comb(len(jg), t) - c_fixos) for jg in jogos_validos)
        teto_alcancavel = min(total_pool_t, c_fixos + soma_capacidade_nova)
        qtd_cobertos = len(cobertos_t)

        cobertura_bruta = qtd_cobertos / total_pool_t if total_pool_t > 0 else 1.0
        eficiencia_teto = qtd_cobertos / teto_alcancavel if teto_alcancavel > 0 else 1.0
        resultados_t[t] = {
            "ordem_t": t,
            "cobertos": qtd_cobertos,
            "total_no_pool": total_pool_t,
            "teto_teorico_alcancavel": teto_alcancavel,
            "cobertura_bruta": cobertura_bruta,
            "eficiencia_sobre_teto": min(1.0, eficiencia_teto),
        }
        s_cov_composto += pesos_t.get(t, 0.0) * min(1.0, eficiencia_teto)

    return {
        "fundamento_cientifico": "EXATO",
        "por_ordem_t": resultados_t,
        "score_cobertura_combinatoria": min(1.0, max(0.0, s_cov_composto)),
    }


def avaliar_probabilidade_conjunta_carteira(
    jogos_validos: Sequence[Tuple[int, ...]],
    pool_ord: Tuple[int, ...],
    fixas_ord: Tuple[int, ...],
    perfis_jogos: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Separa explicitamente os tres indicadores obrigatorios da Secao 3 e Ressalva 1.C:
      1) Probabilidade individual de cada bilhete (e distribuicao por faixa em multiplas);
      2) Quantidade esperada / multiplicidade N_j(m, h) de combinacoes simples premiadas;
      3) Probabilidade conjunta da carteira P(U_i A_i) via covariancia exata p_2(c),
         variancia exata Var(N_prem(C)), cota inferior Dawson-Sankoff e cota superior Hunter-Worsley.
    """
    j = len(jogos_validos)
    tamanhos = [len(jg) for jg in jogos_validos]
    p1_simples = probabilidade_pelo_menos_k_exata(TAMANHO_SORTEIO, 11)

    p_ind_lista = [probabilidade_pelo_menos_k_exata(m, 11) for m in tamanhos]
    total_comb_simples = sum(math.comb(m, TAMANHO_SORTEIO) for m in tamanhos)
    esperado_bilhetes_prem = sum(p_ind_lista, Fraction(0, 1))
    esperado_simples_prem = Fraction(total_comb_simples, 1) * p1_simples

    # Matriz exata p_2(i, k) = P(A_i inter A_k)
    matriz_p2: List[List[Fraction]] = [[Fraction(0, 1)] * j for _ in range(j)]
    soma_p2_pares = Fraction(0, 1)
    soma_cov_pares = Fraction(0, 1)
    pares_totais = j * (j - 1) // 2

    for i in range(j):
        matriz_p2[i][i] = p_ind_lista[i]
        mi = tamanhos[i]
        mask_i = perfis_jogos[i]["mascara"]
        pi = p_ind_lista[i]
        for k in range(i + 1, j):
            mk = tamanhos[k]
            pk = p_ind_lista[k]
            inter = (mask_i & perfis_jogos[k]["mascara"]).bit_count()
            p2 = probabilidade_conjunta_par_exata(mi, mk, inter, 11)
            matriz_p2[i][k] = p2
            matriz_p2[k][i] = p2
            soma_p2_pares += p2
            soma_cov_pares += p2 - (pi * pk)

    variancia_independente = sum(p * (Fraction(1, 1) - p) for p in p_ind_lista)
    variancia_dependente_exata = variancia_independente + (2 * soma_cov_pares)

    cota_inf_ds = _limite_dawson_sankoff(p_ind_lista, soma_p2_pares)
    cota_sup_hw = _limite_hunter_worsley(p_ind_lista, matriz_p2)
    prob_conjunta_exata_fechada: Optional[Fraction] = None
    if j == 1:
        prob_conjunta_exata_fechada = p_ind_lista[0]
    elif j == 2:
        prob_conjunta_exata_fechada = (p_ind_lista[0] + p_ind_lista[1]) - matriz_p2[0][1]

    # Referencia normalizada S_prob para carteira de jogos simples ou mistos:
    # Compara soma_p2_pares com pior caso (jogos clones de mesmo tamanho) vs cota teorica minima.
    if j <= 1:
        s_prob = 1.0
    else:
        soma_p2_max = Fraction(0, 1)
        soma_p2_ref_min = Fraction(0, 1)
        p = len(pool_ord)
        f = len(fixas_ord)
        s_i_min_int, _ = _cota_minima_intersecao_exata(tamanhos, p, f)
        i_min_rac = Fraction(s_i_min_int, pares_totais)
        c_low = i_min_rac.numerator // i_min_rac.denominator
        c_high = c_low + (1 if i_min_rac > c_low else 0)
        frac_c = i_min_rac - c_low

        for i in range(j):
            mi = tamanhos[i]
            for k in range(i + 1, j):
                mk = tamanhos[k]
                c_max_par = min(mi, mk)
                soma_p2_max += probabilidade_conjunta_par_exata(mi, mk, c_max_par, 11)

                c_min_par = max(0, mi + mk - p, f)
                if mi == mk == TAMANHO_SORTEIO:
                    # Interpolacao convexa no limite medio de Cauchy-Schwarz
                    cl = max(c_min_par, min(c_max_par, c_low))
                    ch = max(c_min_par, min(c_max_par, c_high))
                    p_l = probabilidade_conjunta_par_exata(mi, mk, cl, 11)
                    p_h = probabilidade_conjunta_par_exata(mi, mk, ch, 11)
                    soma_p2_ref_min += p_l + frac_c * (p_h - p_l)
                else:
                    soma_p2_ref_min += probabilidade_conjunta_par_exata(mi, mk, c_min_par, 11)

        den = soma_p2_max - soma_p2_ref_min
        if den <= 0:
            s_prob = 1.0
        else:
            razao = float((soma_p2_max - soma_p2_pares) / den)
            s_prob = min(1.0, max(0.0, razao))

    detalhe_multiplas: List[Dict[str, Any]] = []
    for idx, m in enumerate(tamanhos):
        if m > TAMANHO_SORTEIO:
            h_dist = distribuicao_hipergeometrica_aposta(m)
            tabela_mult = {
                str(h): multiplicidade_premios_aposta(m, h)["premios_por_faixa"]
                for h in range(11, TAMANHO_SORTEIO + 1)
            }
            detalhe_multiplas.append(
                {
                    "indice_bilhete": idx,
                    "dezenas_marcadas": m,
                    "prob_alguma_premiacao_bilhete": h_dist["probabilidade_alguma_premiacao_exata"],
                    "multiplicidade_simples_por_acertos": tabela_mult,
                }
            )

    pares_detalhados: List[Dict[str, Any]] = []
    if j <= 10:
        for i in range(j):
            for k in range(i + 1, j):
                p2_ik = matriz_p2[i][k]
                inter_ik = (perfis_jogos[i]["mascara"] & perfis_jogos[k]["mascara"]).bit_count()
                pares_detalhados.append(
                    {
                        "par": [i, k],
                        "m1": tamanhos[i],
                        "m2": tamanhos[k],
                        "intersecao": inter_ik,
                        "p2_fracao": f"{p2_ik.numerator}/{p2_ik.denominator}",
                        "p2_float": float(p2_ik),
                    }
                )

    razao_var = (
        float(variancia_dependente_exata / variancia_independente)
        if variancia_independente > 0
        else 1.0
    )

    return {
        "fundamento_cientifico": "EXATO",
        "natureza_score_S_prob": "metrica_de_otimizacao_baseada_em_probabilidades_pareadas_e_limites_exatos",
        "s_prob_equivale_a_uniao_exata": bool(j <= 1),
        "distincao_cinco_grandezas_ressalva_2_1": {
            "a_probabilidade_individual_cada_bilhete": [
                {
                    "indice_bilhete": idx,
                    "dezenas_marcadas": tamanhos[idx],
                    "probabilidade_fracao": f"{p.numerator}/{p.denominator}",
                    "probabilidade_percentual": float(p * 100),
                }
                for idx, p in enumerate(p_ind_lista)
            ],
            "b_probabilidade_pareada_simultanea": {
                "pares_avaliados": pares_totais,
                "soma_p2_pares_fracao": f"{soma_p2_pares.numerator}/{soma_p2_pares.denominator}",
                "soma_p2_pares_float": float(soma_p2_pares),
                "detalhes_pares_quando_J_menor_igual_10": pares_detalhados,
            },
            "c_esperanca_e_variancia_premiados": {
                "esperanca_bilhetes_premiados_fracao": f"{esperado_bilhetes_prem.numerator}/{esperado_bilhetes_prem.denominator}",
                "esperanca_bilhetes_premiados_float": float(esperado_bilhetes_prem),
                "esperanca_combinacoes_simples_premiadas_float": float(esperado_simples_prem),
                "variancia_dependente_exata_fracao": f"{variancia_dependente_exata.numerator}/{variancia_dependente_exata.denominator}",
                "variancia_dependente_exata_float": float(variancia_dependente_exata),
                "razao_acoplamento_variancia": razao_var,
            },
            "d_limites_uniao_pelo_menos_uma_premiacao": {
                "cota_inferior_dawson_sankoff_fracao": f"{cota_inf_ds.numerator}/{cota_inf_ds.denominator}",
                "cota_inferior_dawson_sankoff": float(cota_inf_ds),
                "cota_superior_hunter_worsley_fracao": f"{cota_sup_hw.numerator}/{cota_sup_hw.denominator}",
                "cota_superior_hunter_worsley": float(cota_sup_hw),
                "aviso": "Cotas matematicas para P(U_i A_i); nao equivalem necessariamente ao valor exato da uniao quando J >= 3.",
            },
            "e_probabilidade_exata_uniao_eventos": {
                "calculada_diretamente": bool(prob_conjunta_exata_fechada is not None),
                "metodo": (
                    "identidade_bilhete_unico"
                    if j == 1
                    else (
                        "inclusao_exclusao_exata_2_eventos"
                        if j == 2
                        else "nao_calculada_diretamente_para_J_maior_2_requer_enumeracao_universo_ou_inclusao_exclusao_completa"
                    )
                ),
                "valor_fracao": (
                    f"{prob_conjunta_exata_fechada.numerator}/{prob_conjunta_exata_fechada.denominator}"
                    if prob_conjunta_exata_fechada is not None
                    else None
                ),
                "valor_percentual": (
                    float(prob_conjunta_exata_fechada * 100)
                    if prob_conjunta_exata_fechada is not None
                    else None
                ),
            },
        },
        "separacao_indicadores_secao3": {
            "1_probabilidade_individual_bilhetes": {
                "bilhete_simples_15_fracao": f"{p1_simples.numerator}/{p1_simples.denominator}",
                "bilhete_simples_15_percentual": float(p1_simples * 100),
                "por_bilhete_percentual": [float(p * 100) for p in p_ind_lista],
                "detalhe_apostas_multiplas": detalhe_multiplas,
            },
            "2_quantidade_esperada_combinacoes_premiadas": {
                "total_combinacoes_simples_pagas": total_comb_simples,
                "esperado_bilhetes_premiados_fracao": f"{esperado_bilhetes_prem.numerator}/{esperado_bilhetes_prem.denominator}",
                "esperado_bilhetes_premiados_float": float(esperado_bilhetes_prem),
                "esperado_combinacoes_simples_premiadas_float": float(esperado_simples_prem),
                "nota_invariancia": "E[N_simples_prem] depende apenas do total de combinacoes simples pagas; nao aumenta com otimizacao.",
            },
            "3_probabilidade_conjunta_carteira": {
                "soma_p2_pares_float": float(soma_p2_pares),
                "soma_covariancias_pares_float": float(soma_cov_pares),
                "variancia_bilhetes_independente_hipotetica": float(variancia_independente),
                "variancia_bilhetes_dependente_exata": float(variancia_dependente_exata),
                "razao_acoplamento_variancia": razao_var,
                "prob_ao_menos_1_exata_fechada": (
                    f"{prob_conjunta_exata_fechada.numerator}/{prob_conjunta_exata_fechada.denominator}"
                    if prob_conjunta_exata_fechada is not None
                    else None
                ),
                "prob_ao_menos_1_exata_percentual": (
                    float(prob_conjunta_exata_fechada * 100)
                    if prob_conjunta_exata_fechada is not None
                    else None
                ),
                "cota_inferior_dawson_sankoff": float(cota_inf_ds),
                "cota_superior_hunter_worsley": float(cota_sup_hw),
                "pares_avaliados": pares_totais,
            },
        },
        "score_probabilidade_conjunta": s_prob,
    }


def avaliar_diversificacao_sobreposicao(
    jogos_validos: Sequence[Tuple[int, ...]],
    pool_ord: Tuple[int, ...],
    fixas_ord: Tuple[int, ...],
    perfis_jogos: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calcula distribuicao exata de intersecoes I_ij e distancias de Hamming/Jaccard,
    comparando com a cota minima inteira S_{I,min} (Cauchy-Schwarz/Schur) e
    calculando o escore heuristico S_div in [0, 1].
    """
    j = len(jogos_validos)
    tamanhos = [len(jg) for jg in jogos_validos]
    p = len(pool_ord)
    f = len(fixas_ord)
    s_i_min, i_min_medio = _cota_minima_intersecao_exata(tamanhos, p, f)

    if j <= 1:
        return {
            "fundamento_cientifico": "HEURISTICO",
            "base_matematica_exata": "Cota S_{I,min} e distancia simetrica d_H",
            "soma_intersecoes": 0,
            "cota_minima_intersecoes_soma": 0,
            "intersecao_media": 0.0,
            "cota_minima_intersecao_media": 0.0,
            "intersecao_minima": 0,
            "intersecao_maxima": 0,
            "hamming_medio": 0.0,
            "jaccard_medio": 0.0,
            "pares_duplicados": 0,
            "score_diversificacao": 1.0,
        }

    intersecoes: List[int] = []
    hammings: List[int] = []
    jaccards: List[float] = []
    pares_duplicados = 0
    s_i_max = 0
    penalidades_pico: List[float] = []

    for i in range(j):
        mi = tamanhos[i]
        mask_i = perfis_jogos[i]["mascara"]
        for k in range(i + 1, j):
            mk = tamanhos[k]
            mask_k = perfis_jogos[k]["mascara"]
            inter = (mask_i & mask_k).bit_count()
            uniao = (mask_i | mask_k).bit_count()
            intersecoes.append(inter)
            hammings.append(mi + mk - 2 * inter)
            jaccards.append(1.0 - (inter / uniao))
            c_max = min(mi, mk)
            s_i_max += c_max
            if mi == mk and inter == mi:
                pares_duplicados += 1
            denom_pico = max(1.0, c_max - i_min_medio)
            excesso = max(0.0, inter - i_min_medio) / denom_pico
            penalidades_pico.append(excesso ** 2)

    soma_inter = sum(intersecoes)
    if s_i_max <= s_i_min:
        excesso_medio = 0.0
    else:
        excesso_medio = max(0.0, (soma_inter - s_i_min) / (s_i_max - s_i_min))

    e_pico = sum(penalidades_pico) / len(penalidades_pico)
    s_div = min(1.0, max(0.0, 1.0 - (0.50 * excesso_medio + 0.50 * e_pico)))

    return {
        "fundamento_cientifico": "HEURISTICO",
        "base_matematica_exata": "Cota S_{I,min} (Schur/Cauchy-Schwarz) e distancias de Hamming/Jaccard",
        "soma_intersecoes": soma_inter,
        "cota_minima_intersecoes_soma": s_i_min,
        "cota_maxima_intersecoes_soma": s_i_max,
        "intersecao_media": soma_inter / len(intersecoes),
        "cota_minima_intersecao_media": i_min_medio,
        "intersecao_minima": min(intersecoes),
        "intersecao_maxima": max(intersecoes),
        "hamming_medio": sum(hammings) / len(hammings),
        "jaccard_medio": sum(jaccards) / len(jaccards),
        "pares_duplicados": pares_duplicados,
        "score_diversificacao": s_div,
    }


def avaliar_distribuicao_dezenas(
    jogos_validos: Sequence[Tuple[int, ...]],
    pool_ord: Tuple[int, ...],
    fixas_ord: Tuple[int, ...],
) -> Dict[str, Any]:
    """
    Mede o equilibrio de utilizacao u_d das dezenas do pool contra o minimo
    teorico inteiro SS_min das dezenas livres (P - F).
    """
    contagem: Dict[int, int] = {d: 0 for d in pool_ord}
    for jg in jogos_validos:
        for d in jg:
            contagem[d] += 1

    set_fixas = set(fixas_ord)
    livres = [d for d in pool_ord if d not in set_fixas]
    tamanhos = [len(jg) for jg in jogos_validos]
    mu_livre, ss_min, ss_max = _cota_minima_variancia_uso_exata(tamanhos, len(pool_ord), len(fixas_ord))

    if not livres:
        return {
            "fundamento_cientifico": "HEURISTICO",
            "base_matematica_exata": "Cota inteira SS_min = r(1 - r/p_livre)",
            "frequencia_por_dezena": contagem,
            "media_alvo_livres": 0.0,
            "ss_observada_livres": 0.0,
            "ss_minima_teorica_livres": 0.0,
            "amplitude_uso_livres": 0,
            "dezenas_nao_utilizadas": 0,
            "score_distribuicao": 1.0,
        }

    usos_livres = [contagem[d] for d in livres]
    ss_obs = sum((u - mu_livre) ** 2 for u in usos_livres)
    if ss_max <= ss_min + 1e-12:
        s_dist = 1.0
    else:
        raz = (ss_obs - ss_min) / (ss_max - ss_min)
        s_dist = min(1.0, max(0.0, 1.0 - raz))

    return {
        "fundamento_cientifico": "HEURISTICO",
        "base_matematica_exata": "Cota inteira SS_min = r(1 - r/p_livre)",
        "frequencia_por_dezena": contagem,
        "media_alvo_livres": mu_livre,
        "ss_observada_livres": ss_obs,
        "ss_minima_teorica_livres": ss_min,
        "ss_maxima_referencia": ss_max,
        "amplitude_uso_livres": max(usos_livres) - min(usos_livres),
        "dezenas_nao_utilizadas": sum(1 for u in usos_livres if u == 0),
        "score_distribuicao": s_dist,
    }


def avaliar_custo_beneficio(
    jogos_validos: Sequence[Tuple[int, ...]],
    pool_ord: Tuple[int, ...],
    fixas_ord: Tuple[int, ...],
    aval_cov: Mapping[str, Any],
) -> Dict[str, Any]:
    """
    Avalia investimento oficial em R$, quantidade e unicidade de combinacoes simples
    e eficiencia de cobertura por unidade monetaria investida.
    """
    custo_total = Decimal("0.00")
    total_comb_pagas = 0
    combinacoes_unicas: set[Tuple[int, ...]] = set()
    avaliacao_exata_combinacoes = True

    for jg in jogos_validos:
        m = len(jg)
        custo_total += custo_aposta_oficial(m)
        total_comb_pagas += math.comb(m, TAMANHO_SORTEIO)

    if total_comb_pagas <= 25_000:
        for jg in jogos_validos:
            combinacoes_unicas.update(itertools.combinations(jg, TAMANHO_SORTEIO))
        qtd_unicas = len(combinacoes_unicas)
    else:
        avaliacao_exata_combinacoes = False
        # Para apostas multiplas muito extensas, conta bilhetes distintos sem expandi-los na memoria
        bilhetes_distintos = len(set(jogos_validos))
        qtd_unicas = total_comb_pagas if bilhetes_distintos == len(jogos_validos) else len(set(jogos_validos))

    taxa_unicidade = qtd_unicas / total_comb_pagas if total_comb_pagas > 0 else 1.0
    cov2 = aval_cov["por_ordem_t"][2]
    cov3 = aval_cov["por_ordem_t"][3]
    custo_float = float(custo_total)

    s_cb = min(1.0, max(0.0, 0.65 * taxa_unicidade + 0.35 * cov2["eficiencia_sobre_teto"]))
    return {
        "fundamento_cientifico": "EXATO",
        "custo_total_brl": str(custo_total),
        "custo_total_float": custo_float,
        "combinacoes_simples_pagas": total_comb_pagas,
        "combinacoes_simples_unicas": qtd_unicas,
        "unicidade_exactamente_verificada": avaliacao_exata_combinacoes,
        "taxa_unicidade_simples": taxa_unicidade,
        "pares_cobertos_por_real": cov2["cobertos"] / custo_float if custo_float > 0 else 0.0,
        "trincas_cobertas_por_real": cov3["cobertos"] / custo_float if custo_float > 0 else 0.0,
        "score_custo_beneficio": s_cb,
    }


def avaliar_estrutura_e_descritivo(
    perfis_jogos: Sequence[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Calcula:
      1) S_div_est (HEURISTICO): diversidade estrutural entre os jogos da carteira
         e equilibrio espacial na matriz 5x5;
      2) Bloco DESCRITIVO isolado (peso preditivo obrigatoriamente zero): comparacao
         contra as esperancas teoricas da hipergeometrica H(25, 15).
    """
    validar_natureza_componente("HEURISTICO", usa_como_ganho_preditivo=False)
    validar_natureza_componente("DESCRITIVO", usa_como_ganho_preditivo=False)

    j = len(perfis_jogos)
    assinaturas = {(p["pares"], p["moldura"], p["soma"] // 15) for p in perfis_jogos}
    taxa_perfis_unicos = len(assinaturas) / j if j > 0 else 1.0

    # Ocupacao agregada de linhas e colunas na matriz 5x5
    linhas_tot = [sum(p["linhas_5x5"][r] for p in perfis_jogos) for r in range(5)]
    colunas_tot = [sum(p["colunas_5x5"][c] for p in perfis_jogos) for c in range(5)]
    total_marcas = sum(p["tamanho"] for p in perfis_jogos)
    alvo_linha = total_marcas / 5.0
    desvio_l = sum(abs(x - alvo_linha) for x in linhas_tot)
    desvio_c = sum(abs(x - alvo_linha) for x in colunas_tot)
    # Pior concentracao teorica dentro da 5x5: colocar maximo de dezenas em poucas linhas/colunas (<= 8/5 * total_marcas)
    desvio_norm_max = max(1.0, 2.0 * total_marcas * 0.8)
    equilibrio_5x5 = min(1.0, max(0.0, 1.0 - (desvio_l + desvio_c) / (2.0 * desvio_norm_max)))

    s_div_est = min(1.0, max(0.0, 0.60 * taxa_perfis_unicos + 0.40 * equilibrio_5x5))

    # Painel estritamente DESCRITIVO (peso preditivo = 0.0)
    media_pares = sum(p["pares"] for p in perfis_jogos) / j
    media_soma = sum(p["soma"] for p in perfis_jogos) / j
    media_moldura = sum(p["moldura"] for p in perfis_jogos) / j
    media_grupo_a = sum(p["grupo_a_01_13"] for p in perfis_jogos) / j
    media_primos = sum(p["primos"] for p in perfis_jogos) / j
    media_max_seq = sum(p["max_consecutivas"] for p in perfis_jogos) / j

    return {
        "diversidade_estrutural_otimizacao": {
            "fundamento_cientifico": "HEURISTICO",
            "perfis_estruturais_distintos": len(assinaturas),
            "taxa_perfis_unicos": taxa_perfis_unicos,
            "ocupacao_linhas_5x5": linhas_tot,
            "ocupacao_colunas_5x5": colunas_tot,
            "equilibrio_matriz_5x5": equilibrio_5x5,
            "score_diversidade_estrutural": s_div_est,
        },
        "indicadores_descritivos_isolados": {
            "fundamento_cientifico": "DESCRITIVO",
            "peso_na_funcao_objetivo": 0.0,
            "uso_preditivo_permitido": False,
            "medias_carteira": {
                "pares": media_pares,
                "soma": media_soma,
                "moldura": media_moldura,
                "grupo_a_01_13": media_grupo_a,
                "primos": media_primos,
                "max_consecutivas": media_max_seq,
            },
            "esperanca_teorica_jogo_simples": {
                "pares": float(ESPERANCAS_TEORICAS_BILHETE_SIMPLES["pares"]),
                "soma": float(ESPERANCAS_TEORICAS_BILHETE_SIMPLES["soma"]),
                "moldura": float(ESPERANCAS_TEORICAS_BILHETE_SIMPLES["moldura"]),
                "grupo_a_01_13": float(ESPERANCAS_TEORICAS_BILHETE_SIMPLES["grupo_a_01_13"]),
                "primos": float(ESPERANCAS_TEORICAS_BILHETE_SIMPLES["primos"]),
            },
        },
    }


def chave_desempate_deterministica(avaliacao: Mapping[str, Any]) -> Tuple[Any, ...]:
    """
    Ordem total lexicografica para desempate deterministico entre duas carteiras:
      1) Maior funcao objetivo F(C) (arredondada em 12 casas contra ruido binario);
      2) Maior cobertura exata de subconjuntos S_cov;
      3) Maior eficiencia probabilistica conjunta S_prob (menor variancia/redundancia);
      4) Menor intersecao maxima inter-jogos;
      5) Menor variancia observada SS_obs do uso das dezenas;
      6) Ordem lexicografica reversa da tupla canonica dos jogos (para tie-break unico).
    """
    comp = avaliacao["componentes"]
    inter_max = avaliacao["detalhes"]["diversificacao_sobreposicao"]["intersecao_maxima"]
    ss_obs = avaliacao["detalhes"]["distribuicao_dezenas"]["ss_observada_livres"]
    jogos_canonicos = tuple(tuple(jg) for jg in avaliacao["carteira_canonica"])

    # Inverte sinais para ser usado tanto com max() quanto documentado claramente
    # Nota: para ordem lexicografica de strings/tuplas em desempate unico, usa hash deterministico negativo ou comparador explicito
    return (
        round(float(avaliacao["funcao_objetivo_F"]), 12),
        round(float(comp["cobertura_combinatoria"]), 12),
        round(float(comp["probabilidade_conjunta"]), 12),
        -int(inter_max),
        -round(float(ss_obs), 12),
        tuple(tuple(-d for d in jg) for jg in jogos_canonicos),
    )


def avaliar_carteira_etapa2(
    carteira: Iterable[Iterable[int]],
    pool: Optional[Iterable[int]] = None,
    fixas: Iterable[int] = (),
    bloqueadas: Iterable[int] = (),
    pesos: Optional[Mapping[str, Any]] = None,
    perfil_pesos: Optional[str] = None,
    modo_fixas: str = "todos_os_jogos",
) -> Dict[str, Any]:
    """
    Funcao objetivo formal completa F_MODO4(C | P, theta) da ETAPA 2.
    Retorna pontuacao escalar F(C) in [0, 1], funcao de perda L(C) = 1 - F(C),
    decomposicao por parcela (EXATO vs HEURISTICO vs DESCRITIVO), as cinco
    grandezas probabilisticas explicitamente separadas, diagnostico de
    compatibilidade de restricoes (`modo_fixas`) e a chave de desempate.
    """
    if isinstance(carteira, (str, bytes)) or not isinstance(carteira, Iterable):
        raise ErroValidacaoLotofacilError("Carteira deve ser um iteravel de jogos.")

    jogos_raw = list(carteira)
    if not jogos_raw:
        raise ErroValidacaoLotofacilError("Carteira vazia nao e permitida.")

    jogos_validos: List[Tuple[int, ...]] = [validar_aposta_lotofacil(jg) for jg in jogos_raw]
    jogos_canonicos = tuple(sorted(jogos_validos))

    if pool is None:
        pool_derivado = sorted({d for jg in jogos_canonicos for d in jg})
        # Se a carteira de 1 jogo tem 15..20 dezenas, o pool minimo valido e o proprio conjunto
        pool_arg: Iterable[int] = pool_derivado
    else:
        pool_arg = pool

    meta_pool = validar_pool_e_restricoes(
        pool=pool_arg,
        fixas=fixas,
        bloqueadas=bloqueadas,
        quantidade_jogos=None,
        tamanho_jogo=min(len(jg) for jg in jogos_canonicos),
        modo_fixas=modo_fixas,
    )
    pool_ord: Tuple[int, ...] = meta_pool["pool"]
    fixas_ord: Tuple[int, ...] = meta_pool["fixas"]
    fixas_jogo_ord: Tuple[int, ...] = meta_pool["fixas_por_jogo"]

    if pesos is not None and perfil_pesos is not None:
        raise ErroValidacaoLotofacilError("Informe apenas 'pesos' ou 'perfil_pesos', nao ambos.")
    if perfil_pesos is not None:
        if perfil_pesos not in PERFIS_PESOS_ETAPA2:
            raise ErroValidacaoLotofacilError(
                f"Perfil de pesos desconhecido '{perfil_pesos}'. Disponiveis: {sorted(PERFIS_PESOS_ETAPA2)}."
            )
        pesos_validos = validar_pesos_objetivo(PERFIS_PESOS_ETAPA2[perfil_pesos])
    else:
        pesos_validos = validar_pesos_objetivo(pesos)

    perfis_jogos = [extrair_perfil_estrutural_jogo(jg) for jg in jogos_canonicos]

    aval_cov = avaliar_cobertura_subconjuntos_exata(jogos_canonicos, pool_ord, fixas_jogo_ord)
    aval_prob = avaliar_probabilidade_conjunta_carteira(jogos_canonicos, pool_ord, fixas_jogo_ord, perfis_jogos)
    aval_div = avaliar_diversificacao_sobreposicao(jogos_canonicos, pool_ord, fixas_jogo_ord, perfis_jogos)
    aval_dist = avaliar_distribuicao_dezenas(jogos_canonicos, pool_ord, fixas_jogo_ord)
    aval_cb = avaliar_custo_beneficio(jogos_canonicos, pool_ord, fixas_jogo_ord, aval_cov)
    aval_est = avaliar_estrutura_e_descritivo(perfis_jogos)

    scores = {
        "cobertura_combinatoria": aval_cov["score_cobertura_combinatoria"],
        "probabilidade_conjunta": aval_prob["score_probabilidade_conjunta"],
        "diversificacao_sobreposicao": aval_div["score_diversificacao"],
        "distribuicao_dezenas": aval_dist["score_distribuicao"],
        "custo_beneficio": aval_cb["score_custo_beneficio"],
        "diversidade_estrutural": aval_est["diversidade_estrutural_otimizacao"]["score_diversidade_estrutural"],
    }

    contribuicoes_ponderadas = {
        nome: pesos_validos[nome] * scores[nome] for nome in NOMES_COMPONENTES
    }
    funcao_objetivo_f = sum(contribuicoes_ponderadas.values())
    funcao_perda_l = 1.0 - funcao_objetivo_f

    contribuicao_exatos = sum(
        contribuicoes_ponderadas[n]
        for n in NOMES_COMPONENTES
        if ESPECIFICACAO_COMPONENTES_ETAPA2[n]["fundamento_cientifico"] == "EXATO"
    )
    contribuicao_heuristicos = sum(
        contribuicoes_ponderadas[n]
        for n in NOMES_COMPONENTES
        if ESPECIFICACAO_COMPONENTES_ETAPA2[n]["fundamento_cientifico"] == "HEURISTICO"
    )

    resultado: Dict[str, Any] = {
        "versao_modelo": VERSAO_MODELO_OBJETIVO_ETAPA2,
        "quantidade_jogos": len(jogos_canonicos),
        "pool_utilizado": list(pool_ord),
        "tamanho_pool": len(pool_ord),
        "modo_fixas": modo_fixas,
        "fixas_utilizadas": list(fixas_ord),
        "fixas_obrigatorias_por_jogo": list(fixas_jogo_ord),
        "bloqueadas": list(meta_pool["bloqueadas"]),
        "compatibilidade_pool_fixas_bloqueadas": meta_pool["diagnostico_compatibilidade"],
        "carteira_canonica": [list(jg) for jg in jogos_canonicos],
        "pesos": pesos_validos,
        "componentes": scores,
        "contribuicoes_ponderadas": contribuicoes_ponderadas,
        "decomposicao_epistemologica": {
            "soma_pesos_exatos": sum(
                pesos_validos[n]
                for n in NOMES_COMPONENTES
                if ESPECIFICACAO_COMPONENTES_ETAPA2[n]["fundamento_cientifico"] == "EXATO"
            ),
            "soma_pesos_heuristicos": sum(
                pesos_validos[n]
                for n in NOMES_COMPONENTES
                if ESPECIFICACAO_COMPONENTES_ETAPA2[n]["fundamento_cientifico"] == "HEURISTICO"
            ),
            "soma_pesos_descritivos_preditivos": 0.0,
            "contribuicao_parcelas_exatas": contribuicao_exatos,
            "contribuicao_parcelas_heuristicas": contribuicao_heuristicos,
            "contribuicao_parcelas_descritivas": 0.0,
        },
        "funcao_objetivo_F": funcao_objetivo_f,
        "funcao_perda_L": funcao_perda_l,
        "detalhes": {
            "cobertura_combinatoria": aval_cov,
            "probabilidade_conjunta": aval_prob,
            "diversificacao_sobreposicao": aval_div,
            "distribuicao_dezenas": aval_dist,
            "custo_beneficio": aval_cb,
            "estrutura_e_descritivo": aval_est,
        },
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }
    resultado["chave_desempate"] = chave_desempate_deterministica(resultado)
    return resultado


def selecionar_melhor_carteira(
    candidatas: Sequence[Iterable[Iterable[int]]],
    pool: Optional[Iterable[int]] = None,
    fixas: Iterable[int] = (),
    bloqueadas: Iterable[int] = (),
    pesos: Optional[Mapping[str, Any]] = None,
    perfil_pesos: Optional[str] = None,
    modo_fixas: str = "todos_os_jogos",
) -> Dict[str, Any]:
    """
    Avalia e ordena deterministicamente um conjunto de carteiras candidatas,
    resolvendo qualquer empate exatamente via chave_desempate_deterministica.
    """
    if not candidatas:
        raise ErroValidacaoLotofacilError("Lista de carteiras candidatas vazia.")
    avaliacoes = [
        avaliar_carteira_etapa2(
            cand,
            pool=pool,
            fixas=fixas,
            bloqueadas=bloqueadas,
            pesos=pesos,
            perfil_pesos=perfil_pesos,
            modo_fixas=modo_fixas,
        )
        for cand in candidatas
    ]
    ranking = sorted(avaliacoes, key=lambda av: av["chave_desempate"], reverse=True)
    return {
        "vencedora": ranking[0],
        "ranking": ranking,
    }
