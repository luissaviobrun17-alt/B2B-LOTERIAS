# -*- coding: utf-8 -*-
"""
ETAPA 1: LEVANTAMENTO DAS REGRAS OFICIAIS E FORMALIZACAO MATEMATICA
======================================================================
Modulo fundacional do projeto LOTOFACIL MODO 4.

Principios adotados:
- Aritmetica inteira e racional exata (math.comb e fractions.Fraction), sem
  aproximacoes silenciosas nos calculos combinatorios e probabilisticos.
- Valores monetarios oficiais em decimal exato (decimal.Decimal).
- Versionamento explicito das regras de premiacao (regular, final zero,
  Lotofacil da Independencia) com vigencia e fonte oficial verificada.
- Validacoes estritas por excecoes explicitas (nunca apenas assert), mantendo
  integridade integral mesmo sob execucao com python -O.
- Separacao programatica entre calculo exato, heuristica e indicador descritivo.
- Veracidade cientifica e preservacao literal da clausula matematica obrigatoria.
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
import math
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Mapping, Optional, Tuple


class ErroValidacaoLotofacilError(ValueError):
    """Excecao explicita para violacao de regras oficiais ou contratos de entrada."""


CLAUSULA_MATEMATICA_OBRIGATORIA = (
    "O sistema não prevê resultados futuros nem altera a probabilidade matemática "
    "individual de premiação de qualquer bilhete. Seu objetivo é otimizar a "
    "distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a "
    "redundância entre eventos premiados e melhorar a cobertura conjunta observada."
)

FONTE_OFICIAL_CAIXA_URL = "https://loterias.caixa.gov.br/Paginas/Lotofacil.aspx"
API_OFICIAL_CAIXA_URL = "https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil"
DATA_CONFERENCIA_OFICIAL_CAIXA = "2026-11-13"

UNIVERSO_TOTAL = 25
DEZENAS_DISPONIVEIS = tuple(range(1, UNIVERSO_TOTAL + 1))
TAMANHO_SORTEIO = 15
MIN_DEZENAS_APOSTA = 15
MAX_DEZENAS_APOSTA = 20
FAIXAS_PREMIADAS = (15, 14, 13, 12, 11)
ESPACO_AMOSTRAL_SIMPLES = math.comb(UNIVERSO_TOTAL, TAMANHO_SORTEIO)  # 3_268_760

PRECO_APOSTA_SIMPLES = Decimal("3.50")
PERCENTUAL_PREMIO_BRUTO = Decimal("0.4379")

PREMIOS_FIXOS = MappingProxyType(
    {
        11: Decimal("7.00"),
        12: Decimal("14.00"),
        13: Decimal("35.00"),
    }
)

REGRAS_PREMIACAO_REGULAR = MappingProxyType(
    {
        "codigo_regime": "concurso_regular",
        "nome": "Concurso Regular da Lotofacil",
        "versao_regra": "2025.07-v1",
        "vigencia_desde_data": "2025-07-10",
        "vigencia_desde_concurso": 3439,
        "fonte_oficial_url": FONTE_OFICIAL_CAIXA_URL,
        "conferido_em": DATA_CONFERENCIA_OFICIAL_CAIXA,
        "preco_aposta_simples_brl": PRECO_APOSTA_SIMPLES,
        "percentual_premio_bruto": PERCENTUAL_PREMIO_BRUTO,
        "premios_fixos_brl": PREMIOS_FIXOS,
        "rateio_saldo_variavel": MappingProxyType(
            {
                "15_acertos": Decimal("0.62"),
                "14_acertos": Decimal("0.13"),
                "acumulado_final_zero": Decimal("0.10"),
                "acumulado_independencia": Decimal("0.15"),
            }
        ),
        "observacao_normativa": "Deducao previa dos premios fixos (11, 12 e 13 acertos) antes do rateio percentual do saldo variavel.",
    }
)

REGRAS_PREMIACAO_FINAL_ZERO = MappingProxyType(
    {
        "codigo_regime": "concurso_final_zero",
        "nome": "Concurso Especial de Final Zero (terminados em 0, exceto Independencia)",
        "versao_regra": "2025.07-v1",
        "vigencia_desde_data": "2025-07-10",
        "vigencia_desde_concurso": 3439,
        "fonte_oficial_url": FONTE_OFICIAL_CAIXA_URL,
        "conferido_em": DATA_CONFERENCIA_OFICIAL_CAIXA,
        "preco_aposta_simples_brl": PRECO_APOSTA_SIMPLES,
        "percentual_premio_bruto": PERCENTUAL_PREMIO_BRUTO,
        "premios_fixos_brl": PREMIOS_FIXOS,
        "rateio_saldo_variavel": MappingProxyType(
            {
                "15_acertos": Decimal("0.72"),
                "14_acertos": Decimal("0.13"),
                "acumulado_independencia": Decimal("0.15"),
            }
        ),
        "observacao_normativa": "Recebe o acumulado reservado nos 9 concursos anteriores de final 1 a 9 (10% do saldo variavel).",
    }
)

REGRAS_PREMIACAO_INDEPENDENCIA = MappingProxyType(
    {
        "codigo_regime": "lotofacil_independencia",
        "nome": "Concurso Especial Lotofacil da Independência",
        "versao_regra": "2025.07-v1",
        "vigencia_desde_data": "2025-07-10",
        "vigencia_desde_concurso": 3439,
        "fonte_oficial_url": FONTE_OFICIAL_CAIXA_URL,
        "conferido_em": DATA_CONFERENCIA_OFICIAL_CAIXA,
        "preco_aposta_simples_brl": PRECO_APOSTA_SIMPLES,
        "percentual_premio_bruto": PERCENTUAL_PREMIO_BRUTO,
        "premios_fixos_brl": PREMIOS_FIXOS,
        "rateio_saldo_variavel": MappingProxyType(
            {
                "15_acertos": Decimal("0.87"),
                "14_acertos": Decimal("0.13"),
            }
        ),
        "observacao_normativa": (
            "Nao acumula; 87% do saldo variavel vai para 15 acertos e 13% para 14 acertos, somado ao fundo acumulado "
            "(15% do saldo dos concursos anteriores). Em situacoes excepcionais de arrecadacao/ganhadores, a CAIXA "
            "pode aplicar ajuste proporcional nas faixas fixas (observado na base oficial no concurso 3780 em 15/09/2026)."
        ),
    }
)

REGRAS_PREMIACAO_VERSIONADAS = MappingProxyType(
    {
        "regras_premiacao_regular": REGRAS_PREMIACAO_REGULAR,
        "regras_premiacao_final_zero": REGRAS_PREMIACAO_FINAL_ZERO,
        "regras_premiacao_independencia": REGRAS_PREMIACAO_INDEPENDENCIA,
    }
)

HISTORICO_FAIXAS_FIXAS_CAIXA = (
    MappingProxyType({"concurso_inicio": 1, "data_inicio": "2003-09-29", "p11": Decimal("2.00"), "p12": Decimal("4.00"), "p13": Decimal("10.00")}),
    MappingProxyType({"concurso_inicio": 460, "data_inicio": "2009-09-10", "p11": Decimal("2.50"), "p12": Decimal("5.00"), "p13": Decimal("12.50")}),
    MappingProxyType({"concurso_inicio": 1054, "data_inicio": "2014-05-12", "p11": Decimal("3.00"), "p12": Decimal("6.00"), "p13": Decimal("15.00")}),
    MappingProxyType({"concurso_inicio": 1213, "data_inicio": "2015-05-25", "p11": Decimal("4.00"), "p12": Decimal("8.00"), "p13": Decimal("20.00")}),
    MappingProxyType({"concurso_inicio": 1889, "data_inicio": "2019-11-11", "p11": Decimal("5.00"), "p12": Decimal("10.00"), "p13": Decimal("25.00")}),
    MappingProxyType({"concurso_inicio": 2801, "data_inicio": "2023-05-02", "p11": Decimal("6.00"), "p12": Decimal("12.00"), "p13": Decimal("30.00")}),
    MappingProxyType({"concurso_inicio": 3439, "data_inicio": "2025-07-10", "p11": Decimal("7.00"), "p12": Decimal("14.00"), "p13": Decimal("35.00")}),
)

RATEIO_SALDO_VARIAVEL = MappingProxyType(
    {
        "concurso_regular": REGRAS_PREMIACAO_REGULAR["rateio_saldo_variavel"],
        "concurso_final_zero": REGRAS_PREMIACAO_FINAL_ZERO["rateio_saldo_variavel"],
        "lotofacil_independencia": REGRAS_PREMIACAO_INDEPENDENCIA["rateio_saldo_variavel"],
    }
)

FUNDAMENTOS_CIENTIFICOS_PERMITIDOS = ("EXATO", "HEURISTICO", "DESCRITIVO")

ESCALA_APOSTAS_OFICIAIS = MappingProxyType(
    {
        m: MappingProxyType(
            {
                "dezenas_marcadas": m,
                "combinacoes_simples": math.comb(m, TAMANHO_SORTEIO),
                "valor_aposta_brl": (
                    PRECO_APOSTA_SIMPLES * Decimal(math.comb(m, TAMANHO_SORTEIO))
                ),
            }
        )
        for m in range(MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA + 1)
    }
)

LIMITE_BOLAO_POR_DEZENAS = MappingProxyType(
    {
        15: MappingProxyType({"cotas_min": 2, "cotas_max": 7, "cota_min_brl": Decimal("4.50"), "bolao_min_brl": Decimal("14.00"), "max_jogos_recibo": 10}),
        16: MappingProxyType({"cotas_min": 2, "cotas_max": 35, "cota_min_brl": Decimal("4.50"), "bolao_min_brl": Decimal("56.00"), "max_jogos_recibo": 10}),
        17: MappingProxyType({"cotas_min": 2, "cotas_max": 40, "cota_min_brl": Decimal("11.90"), "bolao_min_brl": Decimal("476.00"), "max_jogos_recibo": 10}),
        18: MappingProxyType({"cotas_min": 2, "cotas_max": 50, "cota_min_brl": Decimal("57.12"), "bolao_min_brl": Decimal("2856.00"), "max_jogos_recibo": 10}),
        19: MappingProxyType({"cotas_min": 2, "cotas_max": 85, "cota_min_brl": Decimal("159.60"), "bolao_min_brl": Decimal("13566.00"), "max_jogos_recibo": 9}),
        20: MappingProxyType({"cotas_min": 2, "cotas_max": 100, "cota_min_brl": Decimal("542.64"), "bolao_min_brl": Decimal("54264.00"), "max_jogos_recibo": 4}),
    }
)

REGRAS_OFICIAIS_LOTOFACIL = MappingProxyType(
    {
        "fonte_oficial_url": FONTE_OFICIAL_CAIXA_URL,
        "api_oficial_url": API_OFICIAL_CAIXA_URL,
        "data_conferencia_caixa": DATA_CONFERENCIA_OFICIAL_CAIXA,
        "universo_total": UNIVERSO_TOTAL,
        "dezenas_disponiveis": DEZENAS_DISPONIVEIS,
        "quantidade_sorteada": TAMANHO_SORTEIO,
        "min_dezenas_aposta": MIN_DEZENAS_APOSTA,
        "max_dezenas_aposta": MAX_DEZENAS_APOSTA,
        "faixas_premiadas": FAIXAS_PREMIADAS,
        "espaco_amostral_simples": ESPACO_AMOSTRAL_SIMPLES,
        "preco_aposta_simples_brl": PRECO_APOSTA_SIMPLES,
        "percentual_premio_bruto": PERCENTUAL_PREMIO_BRUTO,
        "premios_fixos_brl": PREMIOS_FIXOS,
        "rateio_saldo_variavel": RATEIO_SALDO_VARIAVEL,
        "escala_apostas_oficiais": ESCALA_APOSTAS_OFICIAIS,
        "limites_bolao": LIMITE_BOLAO_POR_DEZENAS,
        "teimosinha_concursos_validos": (2, 3, 4, 6, 8, 9, 12, 18, 24),
        "prescricao_dias": 90,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }
)

# Conjuntos estruturais canonicos da matriz 5x5 e indicadores aritmeticos (01..25)
PRIMOS_25 = frozenset({2, 3, 5, 7, 11, 13, 17, 19, 23})
FIBONACCI_25 = frozenset({1, 2, 3, 5, 8, 13, 21})
MULTIPLOS_3_25 = frozenset(d for d in DEZENAS_DISPONIVEIS if d % 3 == 0)
MULTIPLOS_5_25 = frozenset(d for d in DEZENAS_DISPONIVEIS if d % 5 == 0)
MOLDURA_5X5 = frozenset({1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25})
CENTRO_5X5 = frozenset({7, 8, 9, 12, 13, 14, 17, 18, 19})
DIAGONAL_PRINCIPAL_5X5 = frozenset({1, 7, 13, 19, 25})
DIAGONAL_SECUNDARIA_5X5 = frozenset({5, 9, 13, 17, 21})
LINHAS_5X5 = tuple(tuple(range(r * 5 + 1, r * 5 + 6)) for r in range(5))
COLUNAS_5X5 = tuple(tuple(r * 5 + c + 1 for r in range(5)) for c in range(5))


def _construir_mascara(dezenas: Iterable[int]) -> int:
    mascara = 0
    for d in dezenas:
        mascara |= 1 << (d - 1)
    return mascara


MASCARAS_LINHAS_5X5 = tuple(_construir_mascara(linha) for linha in LINHAS_5X5)
MASCARAS_COLUNAS_5X5 = tuple(_construir_mascara(col) for col in COLUNAS_5X5)
MASCARA_MOLDURA_5X5 = _construir_mascara(MOLDURA_5X5)
MASCARA_CENTRO_5X5 = _construir_mascara(CENTRO_5X5)
MASCARA_PARES = _construir_mascara(d for d in DEZENAS_DISPONIVEIS if d % 2 == 0)
MASCARA_IMPARES = _construir_mascara(d for d in DEZENAS_DISPONIVEIS if d % 2 == 1)
MASCARA_PRIMOS = _construir_mascara(PRIMOS_25)
MASCARA_FIBONACCI = _construir_mascara(FIBONACCI_25)


def validar_inteiro_estrito(
    valor: Any,
    nome: str,
    minimo: Optional[int] = None,
    maximo: Optional[int] = None,
) -> int:
    """Valida tipo int estrito (rejeitando bool, float e str) e faixa permitida."""
    if type(valor) is not int:
        raise ErroValidacaoLotofacilError(
            f"Parametro '{nome}' deve ser int estrito; recebido {type(valor).__name__}."
        )
    if minimo is not None and valor < minimo:
        raise ErroValidacaoLotofacilError(
            f"Parametro '{nome}' ({valor}) abaixo do minimo permitido ({minimo})."
        )
    if maximo is not None and valor > maximo:
        raise ErroValidacaoLotofacilError(
            f"Parametro '{nome}' ({valor}) acima do maximo permitido ({maximo})."
        )
    return valor


def validar_aposta_lotofacil(
    dezenas: Iterable[int],
    tamanho_esperado: Optional[int] = None,
) -> Tuple[int, ...]:
    """
    Valida uma aposta ou resultado da Lotofacil quanto a cardinalidade,
    tipo inteiro estrito, unicidade e dominio [1..25], retornando tupla ordenada.
    """
    if isinstance(dezenas, (str, bytes)) or not isinstance(dezenas, Iterable):
        raise ErroValidacaoLotofacilError("A aposta deve ser um iteravel de dezenas inteiras.")

    lista = list(dezenas)
    for idx, d in enumerate(lista):
        validar_inteiro_estrito(d, f"dezenas[{idx}]", 1, UNIVERSO_TOTAL)

    ordenadas = tuple(sorted(set(lista)))
    if len(ordenadas) != len(lista):
        raise ErroValidacaoLotofacilError("Aposta invalida: contem dezenas duplicadas.")

    if tamanho_esperado is not None:
        validar_inteiro_estrito(
            tamanho_esperado, "tamanho_esperado", MIN_DEZENAS_APOSTA, UNIVERSO_TOTAL
        )
        if len(ordenadas) != tamanho_esperado:
            raise ErroValidacaoLotofacilError(
                f"Quantidade de dezenas ({len(ordenadas)}) diverge do esperado ({tamanho_esperado})."
            )
    elif not (MIN_DEZENAS_APOSTA <= len(ordenadas) <= MAX_DEZENAS_APOSTA):
        raise ErroValidacaoLotofacilError(
            f"Quantidade de dezenas ({len(ordenadas)}) fora da faixa oficial [{MIN_DEZENAS_APOSTA}..{MAX_DEZENAS_APOSTA}]."
        )
    return ordenadas


def combinacao_exata(n: int, k: int) -> int:
    """Calcula coeficiente binomial exato C(n, k) com validacao estrita de inteiros."""
    n_ok = validar_inteiro_estrito(n, "n", 0)
    k_ok = validar_inteiro_estrito(k, "k", 0)
    if k_ok > n_ok:
        raise ErroValidacaoLotofacilError(f"Nao existe C({n_ok}, {k_ok}) com k > n.")
    return math.comb(n_ok, k_ok)


def custo_aposta_oficial(m: int) -> Decimal:
    """Retorna o custo oficial em R$ de uma aposta unica com m dezenas (15..20)."""
    m_ok = validar_inteiro_estrito(m, "m", MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA)
    return ESCALA_APOSTAS_OFICIAIS[m_ok]["valor_aposta_brl"]


def probabilidade_hipergeometrica_exata(m: int, k: int) -> Fraction:
    """
    Calcula a probabilidade exata P(X = k) da quantidade X de acertos em um
    sorteio uniforme sem reposicao de 15 dezenas dentre 25, ao marcar m dezenas:
        P(X = k | m) = C(m, k) * C(25 - m, 15 - k) / C(25, 15)
    """
    m_ok = validar_inteiro_estrito(m, "m", MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA)
    k_ok = validar_inteiro_estrito(k, "k", 0, TAMANHO_SORTEIO)
    suporte_min = max(0, m_ok + TAMANHO_SORTEIO - UNIVERSO_TOTAL)
    suporte_max = min(m_ok, TAMANHO_SORTEIO)
    if k_ok < suporte_min or k_ok > suporte_max:
        return Fraction(0, 1)
    favoraveis = math.comb(m_ok, k_ok) * math.comb(UNIVERSO_TOTAL - m_ok, TAMANHO_SORTEIO - k_ok)
    return Fraction(favoraveis, ESPACO_AMOSTRAL_SIMPLES)


def probabilidade_pelo_menos_k_exata(m: int, k_min: int = 11) -> Fraction:
    """
    Calcula P(X >= k_min) exata para aposta unica de m dezenas (15..20).
    Observacao matematica: uma aposta multipla de m dezenas contem ao menos
    um bilhete simples de 15 dezenas com >= k_min acertos se e somente se a
    propria selecao de m dezenas intercepta o sorteio em >= k_min dezenas.
    """
    m_ok = validar_inteiro_estrito(m, "m", MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA)
    k_ok = validar_inteiro_estrito(k_min, "k_min", 0, TAMANHO_SORTEIO)
    total = Fraction(0, 1)
    for k in range(k_ok, TAMANHO_SORTEIO + 1):
        total += probabilidade_hipergeometrica_exata(m_ok, k)
    return total


def distribuicao_hipergeometrica_aposta(m: int) -> Dict[str, Any]:
    """
    Retorna a distribuicao hipergeometrica exata completa H(25, 15, m),
    incluindo soma unitaria comprovada, valor esperado exato, variancia exata
    e razao de chance '1 em X' para cada valor possivel de k.
    """
    m_ok = validar_inteiro_estrito(m, "m", MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA)
    k_min = max(0, m_ok + TAMANHO_SORTEIO - UNIVERSO_TOTAL)
    k_max = min(m_ok, TAMANHO_SORTEIO)

    faixas: Dict[int, Dict[str, Any]] = {}
    soma_probs = Fraction(0, 1)
    media_esperada = Fraction(m_ok * TAMANHO_SORTEIO, UNIVERSO_TOTAL)
    variancia_teorica = Fraction(
        m_ok * TAMANHO_SORTEIO * (UNIVERSO_TOTAL - m_ok) * (UNIVERSO_TOTAL - TAMANHO_SORTEIO),
        (UNIVERSO_TOTAL ** 2) * (UNIVERSO_TOTAL - 1),
    )

    for k in range(k_min, k_max + 1):
        favoraveis = math.comb(m_ok, k) * math.comb(UNIVERSO_TOTAL - m_ok, TAMANHO_SORTEIO - k)
        prob = Fraction(favoraveis, ESPACO_AMOSTRAL_SIMPLES)
        soma_probs += prob
        chance_inversa = Fraction(prob.denominator, prob.numerator)
        faixas[k] = {
            "acertos": k,
            "combinacoes_favoraveis": favoraveis,
            "probabilidade_exata": prob,
            "probabilidade_num": prob.numerator,
            "probabilidade_den": prob.denominator,
            "chance_1_em_exata": chance_inversa,
            "chance_1_em_float": float(chance_inversa),
            "probabilidade_percentual": float(prob * 100),
            "premiada": k in FAIXAS_PREMIADAS,
        }

    if soma_probs != Fraction(1, 1):
        raise ErroValidacaoLotofacilError(
            f"Inconsistencia matematica: soma da distribuicao para m={m_ok} foi {soma_probs}."
        )

    prob_premiacao = probabilidade_pelo_menos_k_exata(m_ok, 11)
    return {
        "dezenas_marcadas": m_ok,
        "combinacoes_simples": math.comb(m_ok, TAMANHO_SORTEIO),
        "custo_brl": str(custo_aposta_oficial(m_ok)),
        "espaco_amostral": ESPACO_AMOSTRAL_SIMPLES,
        "suporte_k": (k_min, k_max),
        "soma_probabilidades": "1/1",
        "valor_esperado_acertos": str(media_esperada),
        "valor_esperado_acertos_float": float(media_esperada),
        "variancia_acertos": str(variancia_teorica),
        "probabilidade_alguma_premiacao_exata": f"{prob_premiacao.numerator}/{prob_premiacao.denominator}",
        "probabilidade_alguma_premiacao_percentual": float(prob_premiacao * 100),
        "distribuicao": faixas,
    }


def multiplicidade_premios_aposta(m: int, h: int) -> Dict[str, Any]:
    """
    Calcula a quantidade exata de bilhetes simples premiados em cada faixa
    (15, 14, 13, 12, 11) contidos em uma aposta de m dezenas (15..20) quando
    exatamente h dezenas dessa aposta coincidem com as 15 sorteadas.

    Formula combinatoria exata:
        N_j(m, h) = C(h, j) * C(m - h, 15 - j)
    """
    m_ok = validar_inteiro_estrito(m, "m", MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA)
    suporte_min = max(0, m_ok + TAMANHO_SORTEIO - UNIVERSO_TOTAL)
    h_ok = validar_inteiro_estrito(h, "h", suporte_min, TAMANHO_SORTEIO)

    premios_por_faixa: Dict[int, int] = {}
    for j in FAIXAS_PREMIADAS:
        faltam = TAMANHO_SORTEIO - j
        if j <= h_ok and 0 <= faltam <= (m_ok - h_ok):
            premios_por_faixa[j] = math.comb(h_ok, j) * math.comb(m_ok - h_ok, faltam)
        else:
            premios_por_faixa[j] = 0

    total_subjogos = 0
    for j in range(0, TAMANHO_SORTEIO + 1):
        faltam = TAMANHO_SORTEIO - j
        if j <= h_ok and 0 <= faltam <= (m_ok - h_ok):
            total_subjogos += math.comb(h_ok, j) * math.comb(m_ok - h_ok, faltam)

    esperado = math.comb(m_ok, TAMANHO_SORTEIO)
    if total_subjogos != esperado:
        raise ErroValidacaoLotofacilError(
            f"Conservacao de Vandermonde violada para m={m_ok}, h={h_ok}: {total_subjogos} != {esperado}."
        )

    retorno_fixo_brl = sum(
        PREMIOS_FIXOS[j] * Decimal(premios_por_faixa[j]) for j in (11, 12, 13)
    )
    return {
        "dezenas_marcadas": m_ok,
        "acertos_no_subconjunto": h_ok,
        "total_combinacoes_aposta": esperado,
        "premios_por_faixa": premios_por_faixa,
        "total_bilhetes_premiados": sum(premios_por_faixa.values()),
        "retorno_premios_fixos_brl": str(retorno_fixo_brl),
    }


def probabilidade_split_bivariada_exata(tamanho_grupo_a: int, acertos_grupo_a: int) -> Fraction:
    """
    Probabilidade hipergeometrica exata de um sorteio (15 de 25) conter exatamente
    'acertos_grupo_a' dezenas no Grupo A de tamanho 'tamanho_grupo_a' e o restante
    no Grupo B (25 - tamanho_grupo_a).
    """
    tam_a = validar_inteiro_estrito(tamanho_grupo_a, "tamanho_grupo_a", 1, UNIVERSO_TOTAL - 1)
    a_ok = validar_inteiro_estrito(acertos_grupo_a, "acertos_grupo_a", 0, TAMANHO_SORTEIO)
    tam_b = UNIVERSO_TOTAL - tam_a
    b_ok = TAMANHO_SORTEIO - a_ok
    if a_ok > tam_a or b_ok > tam_b:
        return Fraction(0, 1)
    return Fraction(math.comb(tam_a, a_ok) * math.comb(tam_b, b_ok), ESPACO_AMOSTRAL_SIMPLES)


def matriz_5x5_coordenadas(dezena: int) -> Tuple[int, int]:
    """Retorna (linha_0_a_4, coluna_0_a_4) da dezena (1..25) no volante 5x5."""
    d_ok = validar_inteiro_estrito(dezena, "dezena", 1, UNIVERSO_TOTAL)
    return (d_ok - 1) // 5, (d_ok - 1) % 5


def definicao_formal_conceitos_secao3() -> Dict[str, Any]:
    """
    Formalizacao matematica das distincoes obrigatorias (Secao 3) e do isomorfismo
    binario no espaco amostral da Lotofacil.
    """
    p_prem = probabilidade_pelo_menos_k_exata(MIN_DEZENAS_APOSTA, 11)
    favoraveis_prem = sum(
        math.comb(TAMANHO_SORTEIO, k) * math.comb(UNIVERSO_TOTAL - TAMANHO_SORTEIO, TAMANHO_SORTEIO - k)
        for k in FAIXAS_PREMIADAS
    )
    pct_prem = float(p_prem * 100)
    return {
        "espaco_amostral": {
            "notacao": "Omega = {S subconjunto {1..25} : |S| = 15}",
            "cardinalidade_exata": ESPACO_AMOSTRAL_SIMPLES,
            "medida_uniforme": "P({omega}) = 1 / C(25,15) = 1 / 3.268.760",
            "isomorfismo_bitmask": "phi(S) = sum_{d in S} 2^(d-1) em [0, 2^25 - 1]; |S1 inter S2| = popcount(phi(S1) & phi(S2))",
        },
        "distincoes_conceituais_obrigatorias": {
            "1_probabilidade_individual_bilhete": {
                "definicao": (
                    f"Para um bilhete B_i de 15 dezenas, P(H_i >= 11) = sum_{{k=11}}^{{15}} "
                    f"C(15,k)*C(10,15-k) / C(25,15) = {favoraveis_prem:,} / {ESPACO_AMOSTRAL_SIMPLES:,} "
                    f"(= {p_prem.numerator:,}/{p_prem.denominator:,}, ~{pct_prem:.4f}%)."
                ).replace(",", "."),
                "invariancia": "Identica para todo bilhete valido, independentemente de paridade, soma, matriz ou historico.",
            },
            "2_probabilidade_ao_menos_um_premiado_carteira": {
                "definicao": "Para carteira C = {B_1, ..., B_J}, P(existe i : H_i >= 11) = P(U_i A_i), onde A_i = {omega in Omega : |B_i inter omega| >= 11}.",
                "formula_inclusao_exclusao": "P(U_i A_i) = sum P(A_i) - sum_{i<j} P(A_i inter A_j) + ..., dependendo diretamente das intersecoes entre eventos de premiacao.",
            },
            "3_distribuicao_numero_premiacoes": {
                "definicao": "Distribuicao completa da variavel aleatoria N_prem(C) = sum_{i=1}^{J} 1(H_i >= 11) em {0, 1, ..., J}.",
                "observacao": "Carteiras altamente redundantes concentram massa em N_prem=0 ou N_prem alto; carteiras dispersas transferem massa de eventos multiplos redundantes para P(N_prem >= 1).",
            },
            "4_quantidade_esperada_bilhetes_premiados": {
                "definicao": (
                    f"E[N_prem(C)] = sum_{{i=1}}^{{J}} P(H_i >= 11) = J * ({p_prem.numerator}/{p_prem.denominator})."
                ),
                "invariancia": "Pela linearidade da esperanca, E[N_prem(C)] depende EXCLUSIVAMENTE de J para apostas simples, sendo invariante a estrategia combinatoria.",
            },
            "5_cobertura_combinatoria_carteira": {
                "definicao": "Cov_t(C) = |U_{i=1}^{J} subconjuntos_t(B_i)| / C(|U|, t), medindo fracao deterministica de t-subconjuntos (ex.: pares t=2, trincas t=3, ou quadras t=4) cobertos pela carteira.",
                "observacao": "Cobertura deterministica de t-subconjuntos nao equivale a garantia automatica de premiacao (faixas 11..15) salvo demonstracao formal condicional.",
            },
        },
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }


def validar_natureza_componente(fundamento: str, usa_como_ganho_preditivo: bool = False) -> str:
    """
    Garante no proprio codigo a separacao cientifica obrigatoria entre parcelas
    EXATAS, HEURISTICAS e DESCRITIVAS, bloqueando a conversao de indicadores
    historicos/descritivos em ganho preditivo de probabilidade futura.
    """
    if fundamento not in FUNDAMENTOS_CIENTIFICOS_PERMITIDOS:
        raise ErroValidacaoLotofacilError(
            f"Fundamento cientifico invalido '{fundamento}'. Permitidos: {FUNDAMENTOS_CIENTIFICOS_PERMITIDOS}."
        )
    if usa_como_ganho_preditivo:
        raise ErroValidacaoLotofacilError(
            "Proibido atribuir ganho preditivo ou alteracao da probabilidade individual futura a "
            f"componentes do motor (fundamento='{fundamento}')."
        )
    return fundamento


def _serializar_regra_premiacao(regra: Mapping[str, Any]) -> Dict[str, Any]:
    return {
        "codigo_regime": regra["codigo_regime"],
        "nome": regra["nome"],
        "versao_regra": regra["versao_regra"],
        "vigencia_desde_data": regra["vigencia_desde_data"],
        "vigencia_desde_concurso": regra["vigencia_desde_concurso"],
        "fonte_oficial_url": regra["fonte_oficial_url"],
        "conferido_em": regra["conferido_em"],
        "preco_aposta_simples_brl": str(regra["preco_aposta_simples_brl"]),
        "percentual_premio_bruto": str(regra["percentual_premio_bruto"]),
        "premios_fixos_brl": {str(k): str(v) for k, v in regra["premios_fixos_brl"].items()},
        "rateio_saldo_variavel": {str(k): str(v) for k, v in regra["rateio_saldo_variavel"].items()},
        "observacao_normativa": regra["observacao_normativa"],
    }


def gerar_resumo_formal_etapa1() -> Dict[str, Any]:
    """Gera o pacote consolidado de formulas e tabelas exatas verificadas na Etapa 1."""
    distribuicoes = {
        m: distribuicao_hipergeometrica_aposta(m)
        for m in range(MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA + 1)
    }

    multiplicidade_exemplos = {
        f"m{m}_h{h}": multiplicidade_premios_aposta(m, h)
        for m in range(MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA + 1)
        for h in range(11, TAMANHO_SORTEIO + 1)
    }

    splits_13_12 = {}
    soma_split_13_12 = Fraction(0, 1)
    for a in range(3, 14):
        p = probabilidade_split_bivariada_exata(13, a)
        soma_split_13_12 += p
        splits_13_12[f"{a}/{15 - a}"] = {
            "fracao_exata": f"{p.numerator}/{p.denominator}",
            "percentual": float(p * 100),
        }

    splits_12_13 = {}
    soma_split_12_13 = Fraction(0, 1)
    for a in range(2, 13):
        p = probabilidade_split_bivariada_exata(12, a)
        soma_split_12_13 += p
        splits_12_13[f"{a}/{15 - a}"] = {
            "fracao_exata": f"{p.numerator}/{p.denominator}",
            "percentual": float(p * 100),
        }

    if soma_split_13_12 != Fraction(1, 1) or soma_split_12_13 != Fraction(1, 1):
        raise ErroValidacaoLotofacilError("Soma das distribuicoes bivariadas de split difere de 1.")

    # Converter Fractions em representacao JSON estavel sem perda de exatidao
    distribuicoes_json: Dict[str, Any] = {}
    for m, info in distribuicoes.items():
        dist_clean: Dict[str, Any] = {}
        for k, f_info in info["distribuicao"].items():
            dist_clean[str(k)] = {
                "acertos": f_info["acertos"],
                "combinacoes_favoraveis": f_info["combinacoes_favoraveis"],
                "probabilidade_fracao": f"{f_info['probabilidade_num']}/{f_info['probabilidade_den']}",
                "probabilidade_percentual": round(f_info["probabilidade_percentual"], 10),
                "chance_1_em": round(f_info["chance_1_em_float"], 4),
                "premiada": f_info["premiada"],
            }
        info_copy = dict(info)
        info_copy["distribuicao"] = dist_clean
        distribuicoes_json[str(m)] = info_copy

    return {
        "etapa": "ETAPA_1_REGRAS_E_FORMALIZACAO_MATEMATICA",
        "fonte_oficial_url": FONTE_OFICIAL_CAIXA_URL,
        "data_conferencia_caixa": DATA_CONFERENCIA_OFICIAL_CAIXA,
        "regras_oficiais": {
            "universo_total": UNIVERSO_TOTAL,
            "quantidade_sorteada": TAMANHO_SORTEIO,
            "min_dezenas_aposta": MIN_DEZENAS_APOSTA,
            "max_dezenas_aposta": MAX_DEZENAS_APOSTA,
            "faixas_premiadas": list(FAIXAS_PREMIADAS),
            "espaco_amostral_simples": ESPACO_AMOSTRAL_SIMPLES,
            "preco_aposta_simples_brl": str(PRECO_APOSTA_SIMPLES),
            "percentual_premio_bruto": str(PERCENTUAL_PREMIO_BRUTO),
            "premios_fixos_brl": {str(k): str(v) for k, v in PREMIOS_FIXOS.items()},
        },
        "regras_premiacao_versionadas": {
            chave: _serializar_regra_premiacao(regra)
            for chave, regra in REGRAS_PREMIACAO_VERSIONADAS.items()
        },
        "historico_transicoes_faixas_fixas": [
            {
                "concurso_inicio": item["concurso_inicio"],
                "data_inicio": item["data_inicio"],
                "premios_fixos_brl": {
                    "11": str(item["p11"]),
                    "12": str(item["p12"]),
                    "13": str(item["p13"]),
                },
            }
            for item in HISTORICO_FAIXAS_FIXAS_CAIXA
        ],
        "principios_independencia_estatistica": {
            "independencia_entre_concursos": True,
            "falacia_apostador_proibida": True,
            "uso_permitido_historico": "caracterizacao_descritiva_e_backtesting_retrospectivo",
            "conversao_atraso_em_predicao_permitida": False,
        },
        "distribuicoes_hipergeometricas_15_a_20": distribuicoes_json,
        "multiplicidade_premios_15_a_20": multiplicidade_exemplos,
        "splits_teoricos": {
            "divisao_principal_13_12_soma": str(soma_split_13_12),
            "divisao_principal_13_12": splits_13_12,
            "divisao_alternativa_12_13_soma": str(soma_split_12_13),
            "divisao_alternativa_12_13": splits_12_13,
        },
        "conceitos_formais_secao3": definicao_formal_conceitos_secao3(),
    }
