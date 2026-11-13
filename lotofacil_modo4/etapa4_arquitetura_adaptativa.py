# -*- coding: utf-8 -*-
"""
ETAPA 4: ARQUITETURA ADAPTATIVA, INTEGRACAO (ETAPAS 1-3) E OTIMIZACAO
=====================================================================
Implementa a camada unificada de integracao e otimizacao de alto desempenho do
LOTOFACIL MODO 4, preservando congelados todos os artefatos das Etapas 1, 2 e 3.

Principais avancos da Etapa 4:
  1. MotorIncrementalOtimizadoEtapa4: substituicao de dicts de bitmasks por
     tabelas combinadicas densas em array('H') (~30,5 KB fixos para t=1..4)
     e cache exato de numeradores inteiros N_p2(m1, m2, c) sobre 3.268.760,
     eliminando alocacoes de Fraction e listas temporarias nos loops quentes.
  2. Construcao gulosa incremental: evita reavaliacoes O(J^2 * C(m,4)) da
     Etapa 3 por meio de avaliacao incremental por prefixo k=1..J.
  3. Despacho adaptativo deterministico e justificavel: seleciona entre os 6
     algoritmos com base em C(K,J), orcamento B, J, dimensoes, tempo/RAM
     disponiveis e restricoes, registrando motivo da escolha e descartes.
  4. Telemetria justa completa (avaliacoes efetivas, taxa de uso do orcamento,
     tempo s, memoria pico tracemalloc, reinicios, criterio de parada e gap
     para o otimo global quando certificado).
"""

from __future__ import annotations

from array import array
from decimal import Decimal
from fractions import Fraction
import hashlib
import itertools
import json
import math
import random
import time
import tracemalloc
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .etapa1_regras_oficiais import (
    CENTRO_5X5,
    CLAUSULA_MATEMATICA_OBRIGATORIA,
    COLUNAS_5X5,
    DEZENAS_DISPONIVEIS,
    ESPACO_AMOSTRAL_SIMPLES,
    LINHAS_5X5,
    MAX_DEZENAS_APOSTA,
    MIN_DEZENAS_APOSTA,
    MOLDURA_5X5,
    PRECO_APOSTA_SIMPLES,
    REGRAS_PREMIACAO_VERSIONADAS,
    TAMANHO_SORTEIO,
    UNIVERSO_TOTAL,
    ErroValidacaoLotofacilError,
    custo_aposta_oficial,
    validar_aposta_lotofacil,
    validar_inteiro_estrito,
    validar_natureza_componente,
)
from .etapa2_funcao_objetivo import (
    CATEGORIAS_PROVA_CIENTIFICA,
    MODOS_FIXAS_PERMITIDOS,
    NOMES_COMPONENTES,
    PERFIS_PESOS_ETAPA2,
    VERSAO_MODELO_OBJETIVO_ETAPA2,
    _cota_minima_intersecao_exata,
    _cota_minima_variancia_uso_exata,
    _mascara_dezenas,
    avaliar_carteira_etapa2,
    chave_desempate_deterministica,
    extrair_perfil_estrutural_jogo,
    probabilidade_conjunta_par_exata,
    selecionar_melhor_carteira,
    validar_pesos_objetivo,
    validar_pool_e_restricoes,
)

VERSAO_ARQUITETURA_ETAPA4 = "4.0.0-etapa4-arquitetura-adaptativa"
HISTORICO_GERACAO_ETAPA4 = None

ALGORITMOS_ETAPA4 = (
    "referencia_aleatoria",
    "busca_exata_pequena",
    "algoritmo_guloso",
    "busca_local_trocas",
    "multiplos_reinicios",
    "estrategia_combinada",
)

REGIMES_PREMIACAO_MAPA = MappingProxyType(
    {
        "concurso_regular": "regras_premiacao_regular",
        "concurso_final_zero": "regras_premiacao_final_zero",
        "lotofacil_independencia": "regras_premiacao_independencia",
    }
)

PRIORIDADES_DESPACHO_PERMITIDAS = (
    "equilibrio_adaptativo",
    "qualidade_maxima",
    "baixa_latencia",
)

CRITERIOS_PARADA_PERMITIDOS = (
    "espaco_unitario",
    "enumeracao_completa",
    "teto_avaliacoes",
    "limite_tempo",
    "limite_memoria",
    "otimo_local_sem_melhora",
    "construcao_completa",
)

_PESOS_T_COB = (0.0, 0.15, 0.35, 0.35, 0.15)
_BITS_DEZENA = tuple((1 << (d - 1)) if d >= 1 else 0 for d in range(UNIVERSO_TOTAL + 1))

# Tabelas combinadicas para ranking bijetivo de subconjuntos em [0..24] -> O(1) em array('H')
_C1 = tuple(math.comb(i, 1) for i in range(UNIVERSO_TOTAL))
_C2 = tuple(math.comb(i, 2) for i in range(UNIVERSO_TOTAL))
_C3 = tuple(math.comb(i, 3) for i in range(UNIVERSO_TOTAL))
_C4 = tuple(math.comb(i, 4) for i in range(UNIVERSO_TOTAL))

_TAM_COV1 = math.comb(UNIVERSO_TOTAL, 1)  # 25
_TAM_COV2 = math.comb(UNIVERSO_TOTAL, 2)  # 300
_TAM_COV3 = math.comb(UNIVERSO_TOTAL, 3)  # 2.300
_TAM_COV4 = math.comb(UNIVERSO_TOTAL, 4)  # 12.650

# Cache exato dos numeradores inteiros N_p2(m1, m2, c) sobre ESPACO_AMOSTRAL_SIMPLES = 3.268.760
def _construir_cache_np2_exato() -> Dict[Tuple[int, int, int], int]:
    tabela: Dict[Tuple[int, int, int], int] = {}
    for m1 in range(MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA + 1):
        for m2 in range(m1, MAX_DEZENAS_APOSTA + 1):
            c_min_dom = max(0, m1 + m2 - UNIVERSO_TOTAL)
            for c in range(c_min_dom, min(m1, m2) + 1):
                fr = probabilidade_conjunta_par_exata(m1, m2, c, 11)
                mult = ESPACO_AMOSTRAL_SIMPLES // fr.denominator
                if fr.denominator * mult != ESPACO_AMOSTRAL_SIMPLES:
                    raise RuntimeError("Denominador inesperado na tabela N_p2 exata.")
                num = fr.numerator * mult
                tabela[(m1, m2, c)] = num
                tabela[(m2, m1, c)] = num
    return tabela


_CACHE_NP2_EXATO: Dict[Tuple[int, int, int], int] = _construir_cache_np2_exato()

# Matriz precomputada por dezena para perfil estrutural 5x5 sem alocacoes no loop quente
_DEZENA_INFO = tuple(
    (
        1 if d % 2 == 0 else 0,
        1 if d in MOLDURA_5X5 else 0,
        (d - 1) // 5,
        (d - 1) % 5,
    )
    for d in range(UNIVERSO_TOTAL + 1)
)


def _derivar_seed_int(semente: int, rotulo: str) -> int:
    digest = hashlib.sha256(f"lotofacil-modo4-etapa4|{semente}|{rotulo}".encode("utf-8")).digest()
    return int.from_bytes(digest[:8], "big")


def _validar_limites_computacionais(
    semente: int,
    max_avaliacoes: int,
    max_iteracoes: int,
    limite_tempo_segundos: Optional[float],
    limite_memoria_mb: Optional[float],
) -> Tuple[int, int, int, Optional[float], Optional[float]]:
    s_ok = validar_inteiro_estrito(semente, "semente", 0)
    av_ok = validar_inteiro_estrito(max_avaliacoes, "max_avaliacoes", 1)
    it_ok = validar_inteiro_estrito(max_iteracoes, "max_iteracoes", 1)
    t_lim: Optional[float] = None
    if limite_tempo_segundos is not None:
        if isinstance(limite_tempo_segundos, bool) or not isinstance(limite_tempo_segundos, (int, float)):
            raise ErroValidacaoLotofacilError("limite_tempo_segundos deve ser numerico positivo.")
        t_lim = float(limite_tempo_segundos)
        if not math.isfinite(t_lim) or t_lim <= 0.0:
            raise ErroValidacaoLotofacilError("limite_tempo_segundos deve ser finito e positivo.")
    m_lim: Optional[float] = None
    if limite_memoria_mb is not None:
        if isinstance(limite_memoria_mb, bool) or not isinstance(limite_memoria_mb, (int, float)):
            raise ErroValidacaoLotofacilError("limite_memoria_mb deve ser numerico positivo.")
        m_lim = float(limite_memoria_mb)
        if not math.isfinite(m_lim) or m_lim <= 0.0:
            raise ErroValidacaoLotofacilError("limite_memoria_mb deve ser finito e positivo.")
    return s_ok, av_ok, it_ok, t_lim, m_lim


def contar_espaco_admissivel_etapa4(
    tamanhos_jogos: Sequence[int],
    tamanho_pool: int,
    fixas_por_jogo: int,
) -> int:
    """
    Calcula o tamanho exato do espaco de carteiras distintas admissiveis para
    apostas homogeneas C(K, J) ou heterogeneas Prod_m C(K_m, qtd_m).
    """
    contagem: Dict[int, int] = {}
    for m in tamanhos_jogos:
        contagem[m] = contagem.get(m, 0) + 1
    total = 1
    for m, qtd in contagem.items():
        k_m = math.comb(tamanho_pool - fixas_por_jogo, m - fixas_por_jogo)
        if qtd > k_m:
            return 0
        total *= math.comb(k_m, qtd)
    return total


def _validar_sem_historico(kwargs_proibidos: Mapping[str, Any]) -> None:
    if kwargs_proibidos.get("usar_historico") is True:
        raise ErroValidacaoLotofacilError(
            "Uso de historico na geracao/otimizacao proibido (HISTORICO_GERACAO_ETAPA4=None)."
        )
    if kwargs_proibidos.get("historico") is not None:
        raise ErroValidacaoLotofacilError(
            "Parametro 'historico' nao e aceito pelo otimizador combinatorio (HISTORICO_GERACAO_ETAPA4=None)."
        )


def integrar_configuracao_caixa_etapa1(
    tipo_concurso: str = "concurso_regular",
) -> Dict[str, Any]:
    """
    Integra regras versionadas oficiais da CAIXA (Etapa 1) ao pipeline da Etapa 4.
    """
    if tipo_concurso not in REGIMES_PREMIACAO_MAPA:
        raise ErroValidacaoLotofacilError(
            f"tipo_concurso invalido '{tipo_concurso}'. Permitidos: {sorted(REGIMES_PREMIACAO_MAPA)}."
        )
    validar_natureza_componente("EXATO", usa_como_ganho_preditivo=False)
    chave = REGIMES_PREMIACAO_MAPA[tipo_concurso]
    regra = REGRAS_PREMIACAO_VERSIONADAS[chave]
    return {
        "tipo_concurso": tipo_concurso,
        "chave_regra_etapa1": chave,
        "versao_regra": regra["versao_regra"],
        "vigencia_desde_concurso": regra["vigencia_desde_concurso"],
        "vigencia_desde_data": regra["vigencia_desde_data"],
        "fonte_oficial_url": regra["fonte_oficial_url"],
        "preco_aposta_simples_brl": str(PRECO_APOSTA_SIMPLES),
        "rateio_saldo_variavel": {k: str(v) for k, v in regra["rateio_saldo_variavel"].items()},
    }


def _resolver_especificacao_etapa4(
    pool: Optional[Iterable[int]],
    fixas: Iterable[int],
    bloqueadas: Iterable[int],
    modo_fixas: str,
    quantidade_jogos: Optional[int],
    tamanho_aposta: int,
    tamanhos_jogos: Optional[Sequence[int]],
    orcamento_brl: Optional[Decimal | str | float | int],
    pesos: Optional[Mapping[str, Any]],
    perfil_pesos: Optional[str],
    tipo_concurso: str = "concurso_regular",
) -> Dict[str, Any]:
    pool_efetivo = DEZENAS_DISPONIVEIS if pool is None else pool
    if pesos is not None and perfil_pesos is not None:
        raise ErroValidacaoLotofacilError("Informe apenas 'pesos' ou 'perfil_pesos', nao ambos.")
    if perfil_pesos is not None:
        if perfil_pesos not in PERFIS_PESOS_ETAPA2:
            raise ErroValidacaoLotofacilError(f"Perfil de pesos desconhecido '{perfil_pesos}'.")
        pesos_validos = validar_pesos_objetivo(PERFIS_PESOS_ETAPA2[perfil_pesos])
        nome_perfil = perfil_pesos
    else:
        pesos_validos = validar_pesos_objetivo(pesos)
        nome_perfil = "padrao_modo4" if pesos is None else "personalizado"

    if tamanhos_jogos is not None and (quantidade_jogos is not None or orcamento_brl is not None):
        raise ErroValidacaoLotofacilError(
            "Informe 'tamanhos_jogos' OU ('quantidade_jogos'/'orcamento_brl'), sem ambiguidade."
        )
    if quantidade_jogos is not None and orcamento_brl is not None:
        raise ErroValidacaoLotofacilError(
            "Informe apenas 'quantidade_jogos' ou 'orcamento_brl', nao ambos simultaneamente."
        )

    m_pad = validar_inteiro_estrito(tamanho_aposta, "tamanho_aposta", MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA)
    meta_base = validar_pool_e_restricoes(
        pool=pool_efetivo,
        fixas=fixas,
        bloqueadas=bloqueadas,
        quantidade_jogos=None,
        tamanho_jogo=m_pad,
        modo_fixas=modo_fixas,
    )

    if tamanhos_jogos is not None:
        tams = [validar_inteiro_estrito(x, "tamanhos_jogos[i]", MIN_DEZENAS_APOSTA, MAX_DEZENAS_APOSTA) for x in tamanhos_jogos]
        if not tams:
            raise ErroValidacaoLotofacilError("tamanhos_jogos nao pode ser vazio.")
    elif orcamento_brl is not None:
        try:
            orc_dec = Decimal(str(orcamento_brl))
        except Exception as exc:
            raise ErroValidacaoLotofacilError(f"Orcamento invalido: {orcamento_brl!r}.") from exc
        if isinstance(orcamento_brl, bool) or not orc_dec.is_finite() or orc_dec < PRECO_APOSTA_SIMPLES:
            raise ErroValidacaoLotofacilError(f"Orcamento invalido ou inferior a R$ {PRECO_APOSTA_SIMPLES}.")
        preco_m = custo_aposta_oficial(m_pad)
        j_orc = int(orc_dec // preco_m)
        if j_orc < 1:
            raise ErroValidacaoLotofacilError(
                f"Orcamento R$ {orc_dec} insuficiente para 1 aposta de {m_pad} dezenas (R$ {preco_m})."
            )
        tams = [m_pad] * j_orc
    else:
        j_req = 1 if quantidade_jogos is None else validar_inteiro_estrito(quantidade_jogos, "quantidade_jogos", 1)
        tams = [m_pad] * j_req

    p = meta_base["tamanho_pool"]
    f_j = meta_base["quantidade_fixas_por_jogo"]
    contagem_por_m: Dict[int, int] = {}
    for m_i in tams:
        if m_i > p:
            raise ErroValidacaoLotofacilError(f"Aposta de {m_i} dezenas incompatível com pool={p}.")
        if f_j > m_i:
            raise ErroValidacaoLotofacilError(f"Fixas por jogo ({f_j}) excede aposta de {m_i} dezenas.")
        contagem_por_m[m_i] = contagem_por_m.get(m_i, 0) + 1

    for m_i, qtd_m in contagem_por_m.items():
        teto_m = math.comb(p - f_j, m_i - f_j)
        if qtd_m > teto_m:
            raise ErroValidacaoLotofacilError(
                f"Impossivel gerar {qtd_m} apostas distintas de {m_i} dezenas em pool={p} "
                f"(modo_fixas='{modo_fixas}', fixas_por_jogo={f_j}): teto={teto_m}."
            )

    custo_total = sum((custo_aposta_oficial(m_i) for m_i in tams), Decimal("0.00"))
    espaco_adm = contar_espaco_admissivel_etapa4(tams, p, f_j)
    regra_caixa = integrar_configuracao_caixa_etapa1(tipo_concurso)

    return {
        "pool": meta_base["pool"],
        "tamanho_pool": p,
        "fixas": meta_base["fixas"],
        "fixas_por_jogo": meta_base["fixas_por_jogo"],
        "bloqueadas": meta_base["bloqueadas"],
        "modo_fixas": modo_fixas,
        "livres_no_pool": meta_base["livres_no_pool"],
        "livres_para_jogos": meta_base["livres"],
        "tamanhos_jogos": tuple(tams),
        "quantidade_jogos": len(tams),
        "custo_total_brl": str(custo_total),
        "pesos": pesos_validos,
        "nome_perfil_pesos": nome_perfil,
        "espaco_admissivel": espaco_adm,
        "regra_caixa": regra_caixa,
        "diagnostico_compatibilidade": meta_base["diagnostico_compatibilidade"],
    }


def _atualizar_cov_jogo_array(
    z_list: Sequence[int],
    delta: int,
    cov1: array,
    cov2: array,
    cov3: array,
    cov4: array,
    cov_unicos: List[int],
) -> None:
    """Atualiza contadores densos t=1..4 para um bilhete completo em 0-based."""
    c1, c2, c3, c4 = _C1, _C2, _C3, _C4
    n = len(z_list)
    u1, u2, u3, u4 = cov_unicos[1], cov_unicos[2], cov_unicos[3], cov_unicos[4]
    if delta > 0:
        for i in range(n):
            zi = z_list[i]
            if cov1[zi] == 0:
                u1 += 1
            cov1[zi] += 1
            c1i = c1[zi]
            for j in range(i + 1, n):
                zj = z_list[j]
                idx2 = c1i + c2[zj]
                if cov2[idx2] == 0:
                    u2 += 1
                cov2[idx2] += 1
                c12 = c1i + c2[zj]
                for k in range(j + 1, n):
                    zk = z_list[k]
                    idx3 = c12 + c3[zk]
                    if cov3[idx3] == 0:
                        u3 += 1
                    cov3[idx3] += 1
                    c123 = c12 + c3[zk]
                    for l in range(k + 1, n):
                        idx4 = c123 + c4[z_list[l]]
                        if cov4[idx4] == 0:
                            u4 += 1
                        cov4[idx4] += 1
    else:
        for i in range(n):
            zi = z_list[i]
            nv1 = cov1[zi] - 1
            cov1[zi] = nv1
            if nv1 == 0:
                u1 -= 1
            c1i = c1[zi]
            for j in range(i + 1, n):
                zj = z_list[j]
                idx2 = c1i + c2[zj]
                nv2 = cov2[idx2] - 1
                cov2[idx2] = nv2
                if nv2 == 0:
                    u2 -= 1
                c12 = c1i + c2[zj]
                for k in range(j + 1, n):
                    zk = z_list[k]
                    idx3 = c12 + c3[zk]
                    nv3 = cov3[idx3] - 1
                    cov3[idx3] = nv3
                    if nv3 == 0:
                        u3 -= 1
                    c123 = c12 + c3[zk]
                    for l in range(k + 1, n):
                        idx4 = c123 + c4[z_list[l]]
                        nv4 = cov4[idx4] - 1
                        cov4[idx4] = nv4
                        if nv4 == 0:
                            u4 -= 1
    cov_unicos[1], cov_unicos[2], cov_unicos[3], cov_unicos[4] = u1, u2, u3, u4


def _delta_cov_troca_array(
    kept_z: Sequence[int],
    zu: int,
    zv: int,
    cov1: array,
    cov2: array,
    cov3: array,
    cov4: array,
) -> Tuple[int, int, int, int]:
    """
    Calcula o delta exato de subconjuntos unicos (d1, d2, d3, d4) ao trocar
    zu por zv mantendo kept_z (len = m - 1, estritamente crescente).
    Percorre cada subconjunto de kept_z UMA unica vez para zu e zv juntos.
    """
    c1, c2, c3, c4 = _C1, _C2, _C3, _C4
    c1u, c2u, c3u, c4u = c1[zu], c2[zu], c3[zu], c4[zu]
    c1v, c2v, c3v, c4v = c1[zv], c2[zv], c3[zv], c4[zv]

    d1 = (-1 if cov1[zu] == 1 else 0) + (1 if cov1[zv] == 0 else 0)
    d2 = 0
    d3 = 0
    d4 = 0
    nk = len(kept_z)

    for i in range(nk):
        x = kept_z[i]
        c1x, c2x = c1[x], c2[x]
        i2_u = (c1u + c2x) if zu < x else (c1x + c2u)
        i2_v = (c1v + c2x) if zv < x else (c1x + c2v)
        if cov2[i2_u] == 1:
            d2 -= 1
        if cov2[i2_v] == 0:
            d2 += 1

        c3x = c3[x]
        for j in range(i + 1, nk):
            y = kept_z[j]
            c2y, c3y = c2[y], c3[y]
            if zu < x:
                i3_u = c1u + c2x + c3y
            elif zu < y:
                i3_u = c1x + c2u + c3y
            else:
                i3_u = c1x + c2y + c3u
            if zv < x:
                i3_v = c1v + c2x + c3y
            elif zv < y:
                i3_v = c1x + c2v + c3y
            else:
                i3_v = c1x + c2y + c3v
            if cov3[i3_u] == 1:
                d3 -= 1
            if cov3[i3_v] == 0:
                d3 += 1

            c1x2y = c1x + c2y
            c1x3y = c1x + c3y
            for k in range(j + 1, nk):
                z = kept_z[k]
                c3z, c4z = c3[z], c4[z]
                if zu < x:
                    i4_u = c1u + c2x + c3y + c4z
                elif zu < y:
                    i4_u = c1x + c2u + c3y + c4z
                elif zu < z:
                    i4_u = c1x2y + c3u + c4z
                else:
                    i4_u = c1x2y + c3z + c4u

                if zv < x:
                    i4_v = c1v + c2x + c3y + c4z
                elif zv < y:
                    i4_v = c1x + c2v + c3y + c4z
                elif zv < z:
                    i4_v = c1x2y + c3v + c4z
                else:
                    i4_v = c1x2y + c3z + c4v

                if cov4[i4_u] == 1:
                    d4 -= 1
                if cov4[i4_v] == 0:
                    d4 += 1

    return d1, d2, d3, d4


def _aplicar_troca_cov_array(
    kept_z: Sequence[int],
    zu: int,
    zv: int,
    cov1: array,
    cov2: array,
    cov3: array,
    cov4: array,
    cov_unicos: List[int],
) -> None:
    c1, c2, c3, c4 = _C1, _C2, _C3, _C4
    c1u, c2u, c3u, c4u = c1[zu], c2[zu], c3[zu], c4[zu]
    c1v, c2v, c3v, c4v = c1[zv], c2[zv], c3[zv], c4[zv]

    nv1 = cov1[zu] - 1
    cov1[zu] = nv1
    if nv1 == 0:
        cov_unicos[1] -= 1
    if cov1[zv] == 0:
        cov_unicos[1] += 1
    cov1[zv] += 1

    u2, u3, u4 = cov_unicos[2], cov_unicos[3], cov_unicos[4]
    nk = len(kept_z)
    for i in range(nk):
        x = kept_z[i]
        c1x, c2x = c1[x], c2[x]
        i2_u = (c1u + c2x) if zu < x else (c1x + c2u)
        nv2 = cov2[i2_u] - 1
        cov2[i2_u] = nv2
        if nv2 == 0:
            u2 -= 1
        i2_v = (c1v + c2x) if zv < x else (c1x + c2v)
        if cov2[i2_v] == 0:
            u2 += 1
        cov2[i2_v] += 1

        for j in range(i + 1, nk):
            y = kept_z[j]
            c2y, c3y = c2[y], c3[y]
            i3_u = (c1u + c2x + c3y) if zu < x else ((c1x + c2u + c3y) if zu < y else (c1x + c2y + c3u))
            nv3 = cov3[i3_u] - 1
            cov3[i3_u] = nv3
            if nv3 == 0:
                u3 -= 1
            i3_v = (c1v + c2x + c3y) if zv < x else ((c1x + c2v + c3y) if zv < y else (c1x + c2y + c3v))
            if cov3[i3_v] == 0:
                u3 += 1
            cov3[i3_v] += 1

            c1x2y = c1x + c2y
            for k in range(j + 1, nk):
                z = kept_z[k]
                c3z, c4z = c3[z], c4[z]
                if zu < x:
                    i4_u = c1u + c2x + c3y + c4z
                elif zu < y:
                    i4_u = c1x + c2u + c3y + c4z
                elif zu < z:
                    i4_u = c1x2y + c3u + c4z
                else:
                    i4_u = c1x2y + c3z + c4u
                nv4 = cov4[i4_u] - 1
                cov4[i4_u] = nv4
                if nv4 == 0:
                    u4 -= 1

                if zv < x:
                    i4_v = c1v + c2x + c3y + c4z
                elif zv < y:
                    i4_v = c1x + c2v + c3y + c4z
                elif zv < z:
                    i4_v = c1x2y + c3v + c4z
                else:
                    i4_v = c1x2y + c3z + c4v
                if cov4[i4_v] == 0:
                    u4 += 1
                cov4[i4_v] += 1

    cov_unicos[2], cov_unicos[3], cov_unicos[4] = u2, u3, u4


def _extrair_assinatura_linha_coluna(jg: Sequence[int]) -> Tuple[Tuple[int, int, int], List[int], List[int]]:
    pares = 0
    mold = 0
    soma = 0
    lin = [0, 0, 0, 0, 0]
    col = [0, 0, 0, 0, 0]
    for d in jg:
        ep, em, rl, rc = _DEZENA_INFO[d]
        pares += ep
        mold += em
        soma += d
        lin[rl] += 1
        col[rc] += 1
    return (pares, mold, soma // 15), lin, col


class MotorIncrementalOtimizadoEtapa4:
    """
    Avaliador incremental exato otimizado em memoria e tempo:
      - Contadores densos em array('H') (30,5 KB fixos para toda cobertura t=1..4)
      - Numeradores inteiros exatos N_p2(m1, m2, c) sem alocacoes de Fraction no loop
      - Sem listas ou dicionarios temporarios no avaliador delta 1-swap
    Matematicamente equivalente a `avaliar_carteira_etapa2` (<= 1e-12).
    """

    def __init__(
        self,
        jogos_iniciais: Sequence[Sequence[int]],
        pool_ord: Tuple[int, ...],
        fixas_jogo_ord: Tuple[int, ...],
        pesos_validos: Mapping[str, float],
    ) -> None:
        self.pool_ord = tuple(pool_ord)
        self.p = len(self.pool_ord)
        self.fixas_jogo_ord = tuple(fixas_jogo_ord)
        self.set_fixas_jogo = set(self.fixas_jogo_ord)
        self.f = len(self.fixas_jogo_ord)
        self.livres_jogo = tuple(d for d in self.pool_ord if d not in self.set_fixas_jogo)
        self.pesos = dict(pesos_validos)
        self.w_cov = float(self.pesos["cobertura_combinatoria"])
        self.w_prob = float(self.pesos["probabilidade_conjunta"])
        self.w_div = float(self.pesos["diversificacao_sobreposicao"])
        self.w_dist = float(self.pesos["distribuicao_dezenas"])
        self.w_cb = float(self.pesos["custo_beneficio"])
        self.w_est = float(self.pesos["diversidade_estrutural"])

        self.jogos: List[Tuple[int, ...]] = [tuple(sorted(jg)) for jg in jogos_iniciais]
        self.jogos_z: List[Tuple[int, ...]] = [tuple(d - 1 for d in jg) for jg in self.jogos]
        self.j = len(self.jogos)
        self.tamanhos: List[int] = [len(jg) for jg in self.jogos]
        self.masks: List[int] = [_mascara_dezenas(jg) for jg in self.jogos]
        self.sets: List[set[int]] = [set(jg) for jg in self.jogos]

        self.u_counts: List[int] = [0] * (UNIVERSO_TOTAL + 1)
        for jg in self.jogos:
            for d in jg:
                self.u_counts[d] += 1
        self.mu_livre, self.ss_min, self.ss_max = _cota_minima_variancia_uso_exata(
            self.tamanhos, self.p, self.f
        )
        self.ss_obs_livres = sum((self.u_counts[d] - self.mu_livre) ** 2 for d in self.livres_jogo)

        tipo_arr = "H" if self.j <= 60_000 else "I"
        self.cov1 = array(tipo_arr, [0]) * _TAM_COV1
        self.cov2 = array(tipo_arr, [0]) * _TAM_COV2
        self.cov3 = array(tipo_arr, [0]) * _TAM_COV3
        self.cov4 = array(tipo_arr, [0]) * _TAM_COV4
        self.cov_unicos: List[int] = [0, 0, 0, 0, 0]

        self.tetos_t: Dict[int, int] = {}
        for t in (1, 2, 3, 4):
            total_pool_t = math.comb(self.p, t)
            c_fix = math.comb(self.f, t) if self.f >= t else 0
            cap_nova = sum((math.comb(m, t) - c_fix) for m in self.tamanhos)
            self.tetos_t[t] = min(total_pool_t, c_fix + cap_nova)

        for jg_z in self.jogos_z:
            _atualizar_cov_jogo_array(jg_z, 1, self.cov1, self.cov2, self.cov3, self.cov4, self.cov_unicos)

        self.total_comb_pagas = sum(math.comb(m, TAMANHO_SORTEIO) for m in self.tamanhos)
        self.rastreia_simples_completo = self.total_comb_pagas <= 25_000
        self.simples_dict: Dict[int, int] = {}
        self.jogos_dict: Dict[int, int] = {}
        for idx, jg in enumerate(self.jogos):
            mk = self.masks[idx]
            self.jogos_dict[mk] = self.jogos_dict.get(mk, 0) + 1
            if self.rastreia_simples_completo:
                if len(jg) == TAMANHO_SORTEIO:
                    self.simples_dict[mk] = self.simples_dict.get(mk, 0) + 1
                else:
                    for comb in itertools.combinations(jg, TAMANHO_SORTEIO):
                        cm = _mascara_dezenas(comb)
                        self.simples_dict[cm] = self.simples_dict.get(cm, 0) + 1

        self.pares_totais = self.j * (self.j - 1) // 2
        self.s_i_min, self.i_min_medio = _cota_minima_intersecao_exata(self.tamanhos, self.p, self.f)
        self.s_i_max = 0
        self.inter_mat: List[List[int]] = [[0] * self.j for _ in range(self.j)]
        self.np2_mat: List[List[int]] = [[0] * self.j for _ in range(self.j)]
        self.penal_mat: List[List[float]] = [[0.0] * self.j for _ in range(self.j)]

        self.soma_inter = 0
        self.soma_penal = 0.0
        self.soma_np2 = 0
        self.soma_np2_max = 0
        self.soma_p2_ref_min_frac = Fraction(0, 1)

        if self.j > 1:
            i_min_rac = Fraction(self.s_i_min, self.pares_totais)
            c_low = i_min_rac.numerator // i_min_rac.denominator
            c_high = c_low + (1 if i_min_rac > c_low else 0)
            frac_c = i_min_rac - c_low

            for i in range(self.j):
                mi = self.tamanhos[i]
                for k in range(i + 1, self.j):
                    mk = self.tamanhos[k]
                    c_max_par = min(mi, mk)
                    self.s_i_max += c_max_par
                    self.soma_np2_max += _CACHE_NP2_EXATO[(mi, mk, c_max_par)]

                    c_min_par = max(0, mi + mk - self.p, self.f)
                    if mi == mk == TAMANHO_SORTEIO:
                        cl = max(c_min_par, min(c_max_par, c_low))
                        ch = max(c_min_par, min(c_max_par, c_high))
                        pl = Fraction(_CACHE_NP2_EXATO[(mi, mk, cl)], ESPACO_AMOSTRAL_SIMPLES)
                        ph = Fraction(_CACHE_NP2_EXATO[(mi, mk, ch)], ESPACO_AMOSTRAL_SIMPLES)
                        self.soma_p2_ref_min_frac += pl + frac_c * (ph - pl)
                    else:
                        self.soma_p2_ref_min_frac += Fraction(
                            _CACHE_NP2_EXATO[(mi, mk, c_min_par)], ESPACO_AMOSTRAL_SIMPLES
                        )

                    inter = (self.masks[i] & self.masks[k]).bit_count()
                    self.inter_mat[i][k] = self.inter_mat[k][i] = inter
                    np2_ik = _CACHE_NP2_EXATO[(mi, mk, inter)]
                    self.np2_mat[i][k] = self.np2_mat[k][i] = np2_ik
                    pen = (max(0.0, inter - self.i_min_medio) / max(1.0, c_max_par - self.i_min_medio)) ** 2
                    self.penal_mat[i][k] = self.penal_mat[k][i] = pen

                    self.soma_inter += inter
                    self.soma_penal += pen
                    self.soma_np2 += np2_ik

        self.soma_p2_max_frac = Fraction(self.soma_np2_max, ESPACO_AMOSTRAL_SIMPLES)
        self.den_p2_frac = self.soma_p2_max_frac - self.soma_p2_ref_min_frac
        # Escala exata em float para calculo O(1) equivalente a Fraction(soma_np2, D)
        self.soma_p2_max_f = self.soma_np2_max / ESPACO_AMOSTRAL_SIMPLES
        self.den_p2_f = float(self.den_p2_frac)

        self.perfis_sig: List[Tuple[int, int, int]] = []
        self.perfis_lin: List[List[int]] = []
        self.perfis_col: List[List[int]] = []
        self.sig_dict: Dict[Tuple[int, int, int], int] = {}
        self.linhas_tot = [0, 0, 0, 0, 0]
        self.colunas_tot = [0, 0, 0, 0, 0]
        self.total_marcas = sum(self.tamanhos)
        self.alvo_lc = self.total_marcas / 5.0
        self.desvio_norm_max = max(1.0, 2.0 * self.total_marcas * 0.8)

        for jg in self.jogos:
            sig, lin, col = _extrair_assinatura_linha_coluna(jg)
            self.perfis_sig.append(sig)
            self.perfis_lin.append(lin)
            self.perfis_col.append(col)
            self.sig_dict[sig] = self.sig_dict.get(sig, 0) + 1
            for r in range(5):
                self.linhas_tot[r] += lin[r]
                self.colunas_tot[r] += col[r]

    def _calcular_scores_de_totais(
        self,
        u1: int,
        u2: int,
        u3: int,
        u4: int,
        soma_np2: int,
        soma_inter: int,
        soma_penal: float,
        ss_obs: float,
        qtd_simples_unicas: int,
        qtd_sigs: int,
        linhas_tot: Sequence[int],
        colunas_tot: Sequence[int],
    ) -> float:
        t1, t2, t3, t4 = self.tetos_t[1], self.tetos_t[2], self.tetos_t[3], self.tetos_t[4]
        ef1 = min(1.0, u1 / t1) if t1 > 0 else 1.0
        ef2 = min(1.0, u2 / t2) if t2 > 0 else 1.0
        ef3 = min(1.0, u3 / t3) if t3 > 0 else 1.0
        ef4 = min(1.0, u4 / t4) if t4 > 0 else 1.0
        s_cov = min(1.0, max(0.0, 0.15 * ef1 + 0.35 * ef2 + 0.35 * ef3 + 0.15 * ef4))

        if self.j <= 1 or self.den_p2_f <= 0.0:
            s_prob = 1.0
        else:
            s_prob = min(1.0, max(0.0, (self.soma_p2_max_f - (soma_np2 / ESPACO_AMOSTRAL_SIMPLES)) / self.den_p2_f))

        if self.j <= 1 or self.s_i_max <= self.s_i_min:
            s_div = 1.0
        else:
            ex_med = max(0.0, (soma_inter - self.s_i_min) / (self.s_i_max - self.s_i_min))
            e_pico = soma_penal / self.pares_totais
            s_div = min(1.0, max(0.0, 1.0 - (0.50 * ex_med + 0.50 * e_pico)))

        if not self.livres_jogo or self.ss_max <= self.ss_min + 1e-12:
            s_dist = 1.0
        else:
            s_dist = min(1.0, max(0.0, 1.0 - (ss_obs - self.ss_min) / (self.ss_max - self.ss_min)))

        taxa_unic = qtd_simples_unicas / self.total_comb_pagas if self.total_comb_pagas > 0 else 1.0
        s_cb = min(1.0, max(0.0, 0.65 * taxa_unic + 0.35 * ef2))

        alvo = self.alvo_lc
        desvio_lc = (
            abs(linhas_tot[0] - alvo) + abs(linhas_tot[1] - alvo) + abs(linhas_tot[2] - alvo)
            + abs(linhas_tot[3] - alvo) + abs(linhas_tot[4] - alvo)
            + abs(colunas_tot[0] - alvo) + abs(colunas_tot[1] - alvo) + abs(colunas_tot[2] - alvo)
            + abs(colunas_tot[3] - alvo) + abs(colunas_tot[4] - alvo)
        )
        eq_lc = min(1.0, max(0.0, 1.0 - desvio_lc / (2.0 * self.desvio_norm_max)))
        s_div_est = min(1.0, max(0.0, 0.60 * (qtd_sigs / self.j) + 0.40 * eq_lc))

        return (
            self.w_cov * s_cov
            + self.w_prob * s_prob
            + self.w_div * s_div
            + self.w_dist * s_dist
            + self.w_cb * s_cb
            + self.w_est * s_div_est
        )

    def qtd_simples_unicas_atual(self) -> int:
        if self.rastreia_simples_completo:
            return len(self.simples_dict)
        return self.total_comb_pagas if len(self.jogos_dict) == self.j else len(self.jogos_dict)

    def score_atual(self) -> float:
        return self._calcular_scores_de_totais(
            self.cov_unicos[1],
            self.cov_unicos[2],
            self.cov_unicos[3],
            self.cov_unicos[4],
            self.soma_np2,
            self.soma_inter,
            self.soma_penal,
            self.ss_obs_livres,
            self.qtd_simples_unicas_atual(),
            len(self.sig_dict),
            self.linhas_tot,
            self.colunas_tot,
        )

    def simular_troca_dezena(self, idx: int, d_out: int, d_in: int) -> Optional[float]:
        """Simula troca 1-dezena em O(delta) sem mutar estado interno e sem alocar dicts."""
        if d_in in self.sets[idx] or d_out not in self.sets[idx]:
            return None

        old_mask = self.masks[idx]
        new_mask = (old_mask ^ _BITS_DEZENA[d_out]) | _BITS_DEZENA[d_in]
        if new_mask in self.jogos_dict:
            return None

        old_jg = self.jogos[idx]
        old_z = self.jogos_z[idx]
        zu = d_out - 1
        zv = d_in - 1
        kept_z = [z for z in old_z if z != zu]
        d1, d2, d3, d4 = _delta_cov_troca_array(
            kept_z, zu, zv, self.cov1, self.cov2, self.cov3, self.cov4
        )
        u1 = self.cov_unicos[1] + d1
        u2 = self.cov_unicos[2] + d2
        u3 = self.cov_unicos[3] + d3
        u4 = self.cov_unicos[4] + d4

        novo_ss = self.ss_obs_livres
        if d_out not in self.set_fixas_jogo:
            u_o = self.u_counts[d_out]
            novo_ss += (u_o - 1 - self.mu_livre) ** 2 - (u_o - self.mu_livre) ** 2
        if d_in not in self.set_fixas_jogo:
            u_i = self.u_counts[d_in]
            novo_ss += (u_i + 1 - self.mu_livre) ** 2 - (u_i - self.mu_livre) ** 2

        mi = self.tamanhos[idx]
        if self.rastreia_simples_completo:
            if mi == TAMANHO_SORTEIO:
                rem = 1 if self.simples_dict.get(old_mask, 0) == 1 else 0
                add = 1 if self.simples_dict.get(new_mask, 0) == 0 else 0
                novas_simples = len(self.simples_dict) - rem + add
            else:
                new_jg_tmp = tuple(sorted(d for d in old_jg if d != d_out) + [d_in])
                delta_s: Dict[int, int] = {}
                for comb in itertools.combinations(old_jg, TAMANHO_SORTEIO):
                    cm = _mascara_dezenas(comb)
                    delta_s[cm] = delta_s.get(cm, 0) - 1
                for comb in itertools.combinations(new_jg_tmp, TAMANHO_SORTEIO):
                    cm = _mascara_dezenas(comb)
                    delta_s[cm] = delta_s.get(cm, 0) + 1
                novas_simples = len(self.simples_dict)
                for cm, dv in delta_s.items():
                    ant = self.simples_dict.get(cm, 0)
                    dep = ant + dv
                    if ant > 0 and dep == 0:
                        novas_simples -= 1
                    elif ant == 0 and dep > 0:
                        novas_simples += 1
        else:
            rem_j = 1 if self.jogos_dict.get(old_mask, 0) == 1 else 0
            add_j = 1 if self.jogos_dict.get(new_mask, 0) == 0 else 0
            novos_dist = len(self.jogos_dict) - rem_j + add_j
            novas_simples = self.total_comb_pagas if novos_dist == self.j else novos_dist

        nova_soma_inter = self.soma_inter
        nova_soma_penal = self.soma_penal
        nova_soma_np2 = self.soma_np2
        inter_row = self.inter_mat[idx]
        np2_row = self.np2_mat[idx]
        pen_row = self.penal_mat[idx]
        masks = self.masks
        tams = self.tamanhos
        i_med = self.i_min_medio

        for k in range(self.j):
            if k == idx:
                continue
            mk = tams[k]
            inter_new = (new_mask & masks[k]).bit_count()
            inter_old = inter_row[k]
            if inter_new != inter_old:
                nova_soma_inter += inter_new - inter_old
                nova_soma_np2 += _CACHE_NP2_EXATO[(mi, mk, inter_new)] - np2_row[k]
                c_max_par = mi if mi <= mk else mk
                pen_new = (max(0.0, inter_new - i_med) / max(1.0, c_max_par - i_med)) ** 2
                nova_soma_penal += pen_new - pen_row[k]

        ep_o, em_o, rl_o, rc_o = _DEZENA_INFO[d_out]
        ep_i, em_i, rl_i, rc_i = _DEZENA_INFO[d_in]
        sig_old = self.perfis_sig[idx]
        nova_soma = (sum(old_jg) - d_out + d_in) // 15
        sig_new = (sig_old[0] - ep_o + ep_i, sig_old[1] - em_o + em_i, nova_soma)
        novas_sigs = len(self.sig_dict)
        if sig_new != sig_old:
            if self.sig_dict.get(sig_old, 0) == 1:
                novas_sigs -= 1
            if self.sig_dict.get(sig_new, 0) == 0:
                novas_sigs += 1

        linhas_new = self.linhas_tot.copy()
        colunas_new = self.colunas_tot.copy()
        linhas_new[rl_o] -= 1
        linhas_new[rl_i] += 1
        colunas_new[rc_o] -= 1
        colunas_new[rc_i] += 1

        return self._calcular_scores_de_totais(
            u1, u2, u3, u4,
            nova_soma_np2,
            nova_soma_inter,
            nova_soma_penal,
            novo_ss,
            novas_simples,
            novas_sigs,
            linhas_new,
            colunas_new,
        )

    def aplicar_substituicao_jogo(self, idx: int, novo_jogo: Sequence[int]) -> float:
        """Substitui integralmente o bilhete `idx` mantendo invariantes exatos."""
        old_jg = self.jogos[idx]
        new_jg = tuple(sorted(novo_jogo))
        if old_jg == new_jg:
            return self.score_atual()

        old_mask = self.masks[idx]
        new_mask = _mascara_dezenas(new_jg)

        for d in old_jg:
            if d not in self.set_fixas_jogo:
                u_o = self.u_counts[d]
                self.ss_obs_livres += (u_o - 1 - self.mu_livre) ** 2 - (u_o - self.mu_livre) ** 2
            self.u_counts[d] -= 1
        for d in new_jg:
            if d not in self.set_fixas_jogo:
                u_i = self.u_counts[d]
                self.ss_obs_livres += (u_i + 1 - self.mu_livre) ** 2 - (u_i - self.mu_livre) ** 2
            self.u_counts[d] += 1

        old_z = self.jogos_z[idx]
        new_z = tuple(d - 1 for d in new_jg)
        _atualizar_cov_jogo_array(old_z, -1, self.cov1, self.cov2, self.cov3, self.cov4, self.cov_unicos)
        _atualizar_cov_jogo_array(new_z, 1, self.cov1, self.cov2, self.cov3, self.cov4, self.cov_unicos)

        nv_j = self.jogos_dict[old_mask] - 1
        if nv_j == 0:
            del self.jogos_dict[old_mask]
        else:
            self.jogos_dict[old_mask] = nv_j
        self.jogos_dict[new_mask] = self.jogos_dict.get(new_mask, 0) + 1

        if self.rastreia_simples_completo:
            for jg_rem, delta in ((old_jg, -1), (new_jg, 1)):
                if len(jg_rem) == TAMANHO_SORTEIO:
                    mk = _mascara_dezenas(jg_rem)
                    if delta < 0:
                        c = self.simples_dict[mk] - 1
                        if c == 0:
                            del self.simples_dict[mk]
                        else:
                            self.simples_dict[mk] = c
                    else:
                        self.simples_dict[mk] = self.simples_dict.get(mk, 0) + 1
                else:
                    for comb in itertools.combinations(jg_rem, TAMANHO_SORTEIO):
                        cm = _mascara_dezenas(comb)
                        if delta < 0:
                            c = self.simples_dict[cm] - 1
                            if c == 0:
                                del self.simples_dict[cm]
                            else:
                                self.simples_dict[cm] = c
                        else:
                            self.simples_dict[cm] = self.simples_dict.get(cm, 0) + 1

        mi = self.tamanhos[idx]
        for k in range(self.j):
            if k == idx:
                continue
            mk = self.tamanhos[k]
            inter_new = (new_mask & self.masks[k]).bit_count()
            inter_old = self.inter_mat[idx][k]
            if inter_new != inter_old:
                np2_new = _CACHE_NP2_EXATO[(mi, mk, inter_new)]
                c_max_par = mi if mi <= mk else mk
                pen_new = (max(0.0, inter_new - self.i_min_medio) / max(1.0, c_max_par - self.i_min_medio)) ** 2

                self.soma_inter += inter_new - inter_old
                self.soma_np2 += np2_new - self.np2_mat[idx][k]
                self.soma_penal += pen_new - self.penal_mat[idx][k]

                self.inter_mat[idx][k] = self.inter_mat[k][idx] = inter_new
                self.np2_mat[idx][k] = self.np2_mat[k][idx] = np2_new
                self.penal_mat[idx][k] = self.penal_mat[k][idx] = pen_new

        sig_old = self.perfis_sig[idx]
        lin_old = self.perfis_lin[idx]
        col_old = self.perfis_col[idx]
        sig_new, lin_new, col_new = _extrair_assinatura_linha_coluna(new_jg)

        nv_s = self.sig_dict[sig_old] - 1
        if nv_s == 0:
            del self.sig_dict[sig_old]
        else:
            self.sig_dict[sig_old] = nv_s
        self.sig_dict[sig_new] = self.sig_dict.get(sig_new, 0) + 1

        for r in range(5):
            self.linhas_tot[r] += lin_new[r] - lin_old[r]
            self.colunas_tot[r] += col_new[r] - col_old[r]

        self.jogos[idx] = new_jg
        self.jogos_z[idx] = new_z
        self.masks[idx] = new_mask
        self.sets[idx] = set(new_jg)
        self.perfis_sig[idx] = sig_new
        self.perfis_lin[idx] = lin_new
        self.perfis_col[idx] = col_new
        return self.score_atual()

    def aplicar_troca_dezena(self, idx: int, d_out: int, d_in: int) -> float:
        old_jg = self.jogos[idx]
        novo = [d for d in old_jg if d != d_out]
        novo.append(d_in)
        return self.aplicar_substituicao_jogo(idx, novo)


class AvaliadorConstrutivoIncrementalEtapa4:
    """
    Avaliador incremental especifico para construcao sequencial jogo a jogo (algoritmo
    guloso). Elimina o gargalo O(J^2 * C(m,4)) da Etapa 3 preservando equivalencia exata
    com `avaliar_carteira_etapa2` em cada prefixo k=1..J.
    """

    def __init__(self, spec: Mapping[str, Any]) -> None:
        self.p = int(spec["tamanho_pool"])
        self.fixas_jogo_ord = tuple(spec["fixas_por_jogo"])
        self.set_fixas_jogo = set(self.fixas_jogo_ord)
        self.f = len(self.fixas_jogo_ord)
        self.livres_jogo = tuple(spec["livres_para_jogos"])
        pesos = spec["pesos"]
        self.w_cov = float(pesos["cobertura_combinatoria"])
        self.w_prob = float(pesos["probabilidade_conjunta"])
        self.w_div = float(pesos["diversificacao_sobreposicao"])
        self.w_dist = float(pesos["distribuicao_dezenas"])
        self.w_cb = float(pesos["custo_beneficio"])
        self.w_est = float(pesos["diversidade_estrutural"])

        self.tams_alvo = tuple(spec["tamanhos_jogos"])
        self.j_max = len(self.tams_alvo)
        tipo_arr = "H" if self.j_max <= 60_000 else "I"
        self.cov1 = array(tipo_arr, [0]) * _TAM_COV1
        self.cov2 = array(tipo_arr, [0]) * _TAM_COV2
        self.cov3 = array(tipo_arr, [0]) * _TAM_COV3
        self.cov4 = array(tipo_arr, [0]) * _TAM_COV4
        self.cov_unicos = [0, 0, 0, 0, 0]

        self.jogos: List[Tuple[int, ...]] = []
        self.masks: List[int] = []
        self.tamanhos: List[int] = []
        self.u_counts: List[int] = [0] * (UNIVERSO_TOTAL + 1)
        self.simples_dict: Dict[int, int] = {}
        self.jogos_dict: Dict[int, int] = {}
        self.sig_dict: Dict[Tuple[int, int, int], int] = {}
        self.linhas_tot = [0, 0, 0, 0, 0]
        self.colunas_tot = [0, 0, 0, 0, 0]
        self.soma_inter = 0
        self.soma_np2 = 0
        self.total_comb_pagas = 0
        self.total_marcas = 0
        self.inter_pares: List[Tuple[int, int, int]] = []

        # Pre-computar invariantes exatos de cada prefixo k=1..J
        self.prefix_meta: Dict[int, Dict[str, Any]] = {}
        comb_pagas_acc = 0
        marcas_acc = 0
        np2_max_acc = 0
        si_max_acc = 0
        for k in range(1, self.j_max + 1):
            tams_k = self.tams_alvo[:k]
            mk_new = tams_k[-1]
            comb_pagas_acc += math.comb(mk_new, TAMANHO_SORTEIO)
            marcas_acc += mk_new
            tetos = {
                t: min(
                    math.comb(self.p, t),
                    (math.comb(self.f, t) if self.f >= t else 0)
                    + sum(math.comb(m, t) - (math.comb(self.f, t) if self.f >= t else 0) for m in tams_k),
                )
                for t in (1, 2, 3, 4)
            }
            mu_k, ss_min_k, ss_max_k = _cota_minima_variancia_uso_exata(tams_k, self.p, self.f)
            s_i_min_k, i_min_med_k = _cota_minima_intersecao_exata(tams_k, self.p, self.f)

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
                        c_min_par = max(0, mi + mj - self.p, self.f)
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
            self.prefix_meta[k] = {
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

    def simular_adicao_jogo(self, cand: Tuple[int, ...]) -> float:
        k_new = len(self.jogos) + 1
        pm = self.prefix_meta[k_new]
        m_new = len(cand)
        cand_mask = _mascara_dezenas(cand)
        cand_z = tuple(d - 1 for d in cand)

        # Delta cobertura t=1..4 sem mutar arrays
        u1, u2, u3, u4 = self.cov_unicos[1], self.cov_unicos[2], self.cov_unicos[3], self.cov_unicos[4]
        c1, c2, c3, c4 = _C1, _C2, _C3, _C4
        cov1, cov2, cov3, cov4 = self.cov1, self.cov2, self.cov3, self.cov4
        for i in range(m_new):
            zi = cand_z[i]
            if cov1[zi] == 0:
                u1 += 1
            c1i = c1[zi]
            for j in range(i + 1, m_new):
                zj = cand_z[j]
                if cov2[c1i + c2[zj]] == 0:
                    u2 += 1
                c12 = c1i + c2[zj]
                for l in range(j + 1, m_new):
                    zl = cand_z[l]
                    if cov3[c12 + c3[zl]] == 0:
                        u3 += 1
                    c123 = c12 + c3[zl]
                    for r in range(l + 1, m_new):
                        if cov4[c123 + c4[cand_z[r]]] == 0:
                            u4 += 1

        tetos = pm["tetos"]
        ef1 = min(1.0, u1 / tetos[1]) if tetos[1] > 0 else 1.0
        ef2 = min(1.0, u2 / tetos[2]) if tetos[2] > 0 else 1.0
        ef3 = min(1.0, u3 / tetos[3]) if tetos[3] > 0 else 1.0
        ef4 = min(1.0, u4 / tetos[4]) if tetos[4] > 0 else 1.0
        s_cov = min(1.0, max(0.0, 0.15 * ef1 + 0.35 * ef2 + 0.35 * ef3 + 0.15 * ef4))

        # Pares com jogos anteriores
        soma_inter_new = self.soma_inter
        soma_np2_new = self.soma_np2
        i_med = pm["i_min_med"]
        soma_penal_new = 0.0
        if k_new > 1:
            for inter_old, c_max_old in self.inter_pares:
                soma_penal_new += (max(0.0, inter_old - i_med) / max(1.0, c_max_old - i_med)) ** 2
            for idx_old, old_mask in enumerate(self.masks):
                mk_old = self.tamanhos[idx_old]
                inter = (cand_mask & old_mask).bit_count()
                soma_inter_new += inter
                soma_np2_new += _CACHE_NP2_EXATO[(m_new, mk_old, inter)]
                c_max_par = m_new if m_new <= mk_old else mk_old
                soma_penal_new += (max(0.0, inter - i_med) / max(1.0, c_max_par - i_med)) ** 2

        den_p2_f = pm["den_p2_f"]
        s_prob = 1.0 if (k_new <= 1 or den_p2_f <= 0.0) else min(
            1.0, max(0.0, (pm["np2_max_f"] - (soma_np2_new / ESPACO_AMOSTRAL_SIMPLES)) / den_p2_f)
        )

        s_i_min = pm["s_i_min"]
        s_i_max = pm["s_i_max"]
        if k_new <= 1 or s_i_max <= s_i_min:
            s_div = 1.0
        else:
            ex_med = max(0.0, (soma_inter_new - s_i_min) / (s_i_max - s_i_min))
            e_pico = soma_penal_new / (k_new * (k_new - 1) // 2)
            s_div = min(1.0, max(0.0, 1.0 - (0.50 * ex_med + 0.50 * e_pico)))

        # Distribuicao livres
        if not self.livres_jogo or pm["ss_max"] <= pm["ss_min"] + 1e-12:
            s_dist = 1.0
        else:
            cand_set = set(cand)
            mu = pm["mu"]
            ss_obs = 0.0
            for d in self.livres_jogo:
                cnt = self.u_counts[d] + (1 if d in cand_set else 0)
                ss_obs += (cnt - mu) ** 2
            s_dist = min(1.0, max(0.0, 1.0 - (ss_obs - pm["ss_min"]) / (pm["ss_max"] - pm["ss_min"])))

        # Custo-beneficio
        comb_pagas = pm["comb_pagas"]
        if pm["rastreia_simples"]:
            # Caso todas as apostas ate aqui tenham sido simples ou multiplas dentro de 25k
            if self.total_comb_pagas <= 25_000 and m_new == TAMANHO_SORTEIO:
                n_unicas = len(self.simples_dict) + (1 if cand_mask not in self.simples_dict else 0)
            else:
                novas_s = set(self.simples_dict)
                if m_new == TAMANHO_SORTEIO:
                    novas_s.add(cand_mask)
                else:
                    for cb in itertools.combinations(cand, TAMANHO_SORTEIO):
                        novas_s.add(_mascara_dezenas(cb))
                n_unicas = len(novas_s)
        else:
            n_dist_j = len(self.jogos_dict) + (1 if cand_mask not in self.jogos_dict else 0)
            n_unicas = comb_pagas if n_dist_j == k_new else n_dist_j
        taxa_unic = n_unicas / comb_pagas if comb_pagas > 0 else 1.0
        s_cb = min(1.0, max(0.0, 0.65 * taxa_unic + 0.35 * ef2))

        # Diversidade estrutural 5x5
        sig_new, lin_new, col_new = _extrair_assinatura_linha_coluna(cand)
        qtd_sigs = len(self.sig_dict) + (1 if sig_new not in self.sig_dict else 0)
        alvo = pm["alvo_lc"]
        desvio = 0.0
        for r in range(5):
            desvio += abs(self.linhas_tot[r] + lin_new[r] - alvo) + abs(self.colunas_tot[r] + col_new[r] - alvo)
        eq_lc = min(1.0, max(0.0, 1.0 - desvio / (2.0 * pm["desvio_norm_max"])))
        s_div_est = min(1.0, max(0.0, 0.60 * (qtd_sigs / k_new) + 0.40 * eq_lc))

        return (
            self.w_cov * s_cov
            + self.w_prob * s_prob
            + self.w_div * s_div
            + self.w_dist * s_dist
            + self.w_cb * s_cb
            + self.w_est * s_div_est
        )

    def adicionar_jogo(self, cand: Tuple[int, ...]) -> None:
        m_new = len(cand)
        cand_mask = _mascara_dezenas(cand)
        cand_z = tuple(d - 1 for d in cand)
        _atualizar_cov_jogo_array(cand_z, 1, self.cov1, self.cov2, self.cov3, self.cov4, self.cov_unicos)

        for idx_old, old_mask in enumerate(self.masks):
            mk_old = self.tamanhos[idx_old]
            inter = (cand_mask & old_mask).bit_count()
            self.soma_inter += inter
            self.soma_np2 += _CACHE_NP2_EXATO[(m_new, mk_old, inter)]
            self.inter_pares.append((inter, min(m_new, mk_old)))

        self.jogos.append(cand)
        self.masks.append(cand_mask)
        self.tamanhos.append(m_new)
        for d in cand:
            self.u_counts[d] += 1

        self.total_comb_pagas += math.comb(m_new, TAMANHO_SORTEIO)
        self.total_marcas += m_new
        self.jogos_dict[cand_mask] = self.jogos_dict.get(cand_mask, 0) + 1
        if self.total_comb_pagas <= 25_000:
            if m_new == TAMANHO_SORTEIO:
                self.simples_dict[cand_mask] = self.simples_dict.get(cand_mask, 0) + 1
            else:
                for cb in itertools.combinations(cand, TAMANHO_SORTEIO):
                    cm = _mascara_dezenas(cb)
                    self.simples_dict[cm] = self.simples_dict.get(cm, 0) + 1

        sig_new, lin_new, col_new = _extrair_assinatura_linha_coluna(cand)
        self.sig_dict[sig_new] = self.sig_dict.get(sig_new, 0) + 1
        for r in range(5):
            self.linhas_tot[r] += lin_new[r]
            self.colunas_tot[r] += col_new[r]


def _gerar_jogo_aleatorio_valido(
    rng: random.Random,
    livres: Sequence[int],
    fixas_j: Sequence[int],
    m_i: int,
) -> Tuple[int, ...]:
    faltam = m_i - len(fixas_j)
    if faltam == 0:
        return tuple(fixas_j)
    escolhidas = rng.sample(livres, faltam)
    return tuple(sorted((*fixas_j, *escolhidas)))


def _gerar_carteira_aleatoria_distinta(
    rng: random.Random,
    spec: Mapping[str, Any],
) -> List[Tuple[int, ...]]:
    livres = spec["livres_para_jogos"]
    fixas_j = spec["fixas_por_jogo"]
    jogos: List[Tuple[int, ...]] = []
    usados: set[Tuple[int, ...]] = set()
    for m_i in spec["tamanhos_jogos"]:
        for _ in range(300):
            cand = _gerar_jogo_aleatorio_valido(rng, livres, fixas_j, m_i)
            if cand not in usados:
                usados.add(cand)
                jogos.append(cand)
                break
        else:
            for comb in itertools.combinations(livres, m_i - len(fixas_j)):
                cand = tuple(sorted((*fixas_j, *comb)))
                if cand not in usados:
                    usados.add(cand)
                    jogos.append(cand)
                    break
    return sorted(jogos)


def _gerar_carteira_equilibrada_inicial(
    spec: Mapping[str, Any],
    rng: Optional[random.Random] = None,
) -> List[Tuple[int, ...]]:
    livres = list(spec["livres_para_jogos"])
    fixas_j = spec["fixas_por_jogo"]
    u = {d: 0 for d in livres}
    usados: set[Tuple[int, ...]] = set()
    jogos: List[Tuple[int, ...]] = []

    for idx_j, m_i in enumerate(spec["tamanhos_jogos"]):
        faltam = m_i - len(fixas_j)
        ordem = list(livres)
        if rng is not None:
            rng.shuffle(ordem)
        else:
            desloc = (idx_j * 5) % max(1, len(ordem))
            ordem = ordem[desloc:] + ordem[:desloc]
        ordem.sort(key=lambda d: u[d])
        escolhidas = tuple(sorted((*fixas_j, *ordem[:faltam])))
        if escolhidas in usados:
            for d_out in reversed(ordem[:faltam]):
                encontrou = False
                for d_in in ordem[faltam:]:
                    if d_in == d_out:
                        continue
                    cand = tuple(sorted([*(d for d in escolhidas if d != d_out), d_in]))
                    if cand not in usados:
                        escolhidas = cand
                        encontrou = True
                        break
                if encontrou:
                    break
            if escolhidas in usados:
                for comb in itertools.combinations(livres, faltam):
                    cand = tuple(sorted((*fixas_j, *comb)))
                    if cand not in usados:
                        escolhidas = cand
                        break
        usados.add(escolhidas)
        jogos.append(escolhidas)
        for d in escolhidas:
            if d in u:
                u[d] += 1
    return sorted(jogos)


def _iniciar_medicao_memoria() -> Tuple[bool, int]:
    """
    Inicia rastreamento de memoria de pico sem perturbar um tracemalloc externo.
    Retorna `(dono_do_trace, pico_base)`.
    """
    if not tracemalloc.is_tracing():
        tracemalloc.start()
        return True, 0
    tracemalloc.reset_peak()
    _, pico = tracemalloc.get_traced_memory()
    return False, pico


def _encerrar_medicao_memoria(dono_trace: bool) -> int:
    _, pico = tracemalloc.get_traced_memory()
    if dono_trace:
        tracemalloc.stop()
    return pico


def _excedeu_tempo_ou_memoria(
    t0: float,
    t_lim: Optional[float],
    m_lim_bytes: Optional[int],
) -> Optional[str]:
    if t_lim is not None and (time.perf_counter() - t0) >= t_lim:
        return "limite_tempo"
    if m_lim_bytes is not None and tracemalloc.is_tracing():
        cur, _ = tracemalloc.get_traced_memory()
        if cur >= m_lim_bytes:
            return "limite_memoria"
    return None


def _refinamento_local_v4(
    jogos_iniciais: Sequence[Sequence[int]],
    spec: Mapping[str, Any],
    rng: random.Random,
    max_avaliacoes: int,
    max_iteracoes: int,
    t0: float,
    t_lim: Optional[float],
    m_lim_bytes: Optional[int],
    usar_replace_game: bool = True,
) -> Tuple[List[Tuple[int, ...]], float, int, int, str, List[Dict[str, Any]]]:
    av = MotorIncrementalOtimizadoEtapa4(
        jogos_iniciais=jogos_iniciais,
        pool_ord=spec["pool"],
        fixas_jogo_ord=spec["fixas_por_jogo"],
        pesos_validos=spec["pesos"],
    )
    f_atual = av.score_atual()
    avaliacoes = 1
    iteracoes = 0
    conv: List[Dict[str, Any]] = [{"iteracao": 0, "avaliacao": 1, "F": round(f_atual, 8)}]
    criterio_parada = "teto_avaliacoes" if avaliacoes >= max_avaliacoes else "otimo_local_sem_melhora"

    livres = spec["livres_para_jogos"]
    set_fixas_j = av.set_fixas_jogo
    mu = av.mu_livre

    while avaliacoes < max_avaliacoes and iteracoes < max_iteracoes:
        motivo_lim = _excedeu_tempo_ou_memoria(t0, t_lim, m_lim_bytes)
        if motivo_lim is not None:
            criterio_parada = motivo_lim
            break
        iteracoes += 1
        melhor_mov: Optional[Tuple[Any, ...]] = None
        melhor_f = f_atual + 1e-12

        if av.j > 1:
            soma_inter_jogo = [sum(av.inter_mat[i]) for i in range(av.j)]
            ordem_jogos = sorted(range(av.j), key=lambda i: soma_inter_jogo[i], reverse=True)
        else:
            ordem_jogos = [0]

        sub_ins_base = sorted(livres, key=lambda d: (av.u_counts[d], d))
        cortado_limite = False

        for idx in ordem_jogos:
            jg = av.jogos[idx]
            cand_outs = sorted(
                (d for d in jg if d not in set_fixas_j),
                key=lambda d: (-(av.u_counts[d] - mu), d),
            )[:6]
            cand_ins = [d for d in sub_ins_base if d not in av.sets[idx]][:6]

            for d_out in cand_outs:
                for d_in in cand_ins:
                    if avaliacoes >= max_avaliacoes:
                        criterio_parada = "teto_avaliacoes"
                        cortado_limite = True
                        break
                    motivo_lim = _excedeu_tempo_ou_memoria(t0, t_lim, m_lim_bytes)
                    if motivo_lim is not None:
                        criterio_parada = motivo_lim
                        cortado_limite = True
                        break
                    f_cand = av.simular_troca_dezena(idx, d_out, d_in)
                    avaliacoes += 1
                    if f_cand is not None and f_cand > melhor_f:
                        melhor_f = f_cand
                        melhor_mov = ("swap", idx, d_out, d_in)
                        break
                if cortado_limite or melhor_mov is not None:
                    break
            if cortado_limite or melhor_mov is not None:
                break

        if melhor_mov is None and usar_replace_game and not cortado_limite and avaliacoes < max_avaliacoes:
            idx_pior = ordem_jogos[0]
            m_i = av.tamanhos[idx_pior]
            faltam = m_i - len(spec["fixas_por_jogo"])
            if faltam > 0:
                candidatos_rep: List[Tuple[int, ...]] = []
                ord_sub = sorted(livres, key=lambda d: av.u_counts[d])
                c0 = tuple(sorted((*spec["fixas_por_jogo"], *ord_sub[:faltam])))
                if _mascara_dezenas(c0) not in av.jogos_dict:
                    candidatos_rep.append(c0)
                for _ in range(8):
                    cg = _gerar_jogo_aleatorio_valido(rng, livres, spec["fixas_por_jogo"], m_i)
                    if _mascara_dezenas(cg) not in av.jogos_dict:
                        candidatos_rep.append(cg)

                if candidatos_rep:
                    snap_jg = list(av.jogos)
                    for cg in candidatos_rep:
                        if avaliacoes >= max_avaliacoes:
                            criterio_parada = "teto_avaliacoes"
                            cortado_limite = True
                            break
                        motivo_lim = _excedeu_tempo_ou_memoria(t0, t_lim, m_lim_bytes)
                        if motivo_lim is not None:
                            criterio_parada = motivo_lim
                            cortado_limite = True
                            break
                        av.aplicar_substituicao_jogo(idx_pior, cg)
                        f_rep = av.score_atual()
                        avaliacoes += 1
                        if f_rep > melhor_f:
                            melhor_f = f_rep
                            melhor_mov = ("replace", idx_pior, cg)
                    av.aplicar_substituicao_jogo(idx_pior, snap_jg[idx_pior])

        if melhor_mov is not None:
            if melhor_mov[0] == "swap":
                _, idx, d_out, d_in = melhor_mov
                f_atual = av.aplicar_troca_dezena(idx, d_out, d_in)
            else:
                _, idx, cg = melhor_mov
                f_atual = av.aplicar_substituicao_jogo(idx, cg)
            conv.append({"iteracao": iteracoes, "avaliacao": avaliacoes, "F": round(f_atual, 8)})
            if avaliacoes >= max_avaliacoes:
                criterio_parada = "teto_avaliacoes"
                break
        else:
            if not cortado_limite:
                criterio_parada = "teto_avaliacoes" if avaliacoes >= max_avaliacoes else "otimo_local_sem_melhora"
            break

    if criterio_parada not in CRITERIOS_PARADA_PERMITIDOS:
        criterio_parada = "teto_avaliacoes" if avaliacoes >= max_avaliacoes else "otimo_local_sem_melhora"

    return sorted(av.jogos), f_atual, avaliacoes, iteracoes, criterio_parada, conv


def _construir_guloso_v4(
    spec: Mapping[str, Any],
    rng: random.Random,
    max_avaliacoes: int,
    t0: float,
    t_lim: Optional[float],
    m_lim_bytes: Optional[int],
) -> Tuple[List[Tuple[int, ...]], float, int, str, List[Dict[str, Any]]]:
    av = AvaliadorConstrutivoIncrementalEtapa4(spec)
    tams = spec["tamanhos_jogos"]
    j = spec["quantidade_jogos"]
    livres = spec["livres_para_jogos"]
    fixas_j = spec["fixas_por_jogo"]
    cand_por_passo = max(2, max_avaliacoes // max(1, j))

    avaliacoes = 0
    usados: set[Tuple[int, ...]] = set()
    conv: List[Dict[str, Any]] = []
    criterio_parada = "construcao_completa"

    for idx_j, m_i in enumerate(tams):
        faltam = m_i - len(fixas_j)
        restantes_av = max(1, max_avaliacoes - avaliacoes)
        limite_cands = min(cand_por_passo, restantes_av) if idx_j < j - 1 else restantes_av
        if idx_j == 0:
            limite_cands = min(limite_cands, 16)

        cands: List[Tuple[int, ...]] = []
        vistos: set[Tuple[int, ...]] = set()
        if faltam == 0:
            cands.append(fixas_j)
        else:
            ord_menos = sorted(livres, key=lambda d: (av.u_counts[d], d))
            cg0 = tuple(sorted((*fixas_j, *ord_menos[:faltam])))
            if cg0 not in usados:
                vistos.add(cg0)
                cands.append(cg0)
            if len(ord_menos) > faltam and len(cands) < limite_cands:
                desloc = max(1, len(ord_menos) // 4)
                rot = ord_menos[desloc:] + ord_menos[:desloc]
                cg1 = tuple(sorted((*fixas_j, *rot[:faltam])))
                if cg1 not in usados and cg1 not in vistos:
                    vistos.add(cg1)
                    cands.append(cg1)
            pesos_amostra = [1.0 / (1.0 + av.u_counts[d]) for d in livres]
            tent = 0
            max_tent = max(limite_cands * 6, 12)
            while len(cands) < limite_cands and tent < max_tent:
                tent += 1
                escolhidos: List[int] = []
                p_disp = list(livres)
                w_disp = list(pesos_amostra)
                for _ in range(faltam):
                    tot = sum(w_disp)
                    alvo = rng.random() * tot
                    acum = 0.0
                    pick = len(p_disp) - 1
                    for k, wk in enumerate(w_disp):
                        acum += wk
                        if acum >= alvo:
                            pick = k
                            break
                    escolhidos.append(p_disp.pop(pick))
                    w_disp.pop(pick)
                cg = tuple(sorted((*fixas_j, *escolhidos)))
                if cg not in usados and cg not in vistos:
                    vistos.add(cg)
                    cands.append(cg)

        if not cands:
            for _ in range(100):
                cg = _gerar_jogo_aleatorio_valido(rng, livres, fixas_j, m_i)
                if cg not in usados:
                    cands.append(cg)
                    break
            if not cands:
                for comb in itertools.combinations(livres, faltam):
                    cg = tuple(sorted((*fixas_j, *comb)))
                    if cg not in usados:
                        cands.append(cg)
                        break

        escolhido = cands[0]
        melhor_f = -1.0
        motivo_lim = _excedeu_tempo_ou_memoria(t0, t_lim, m_lim_bytes)
        if motivo_lim is not None:
            criterio_parada = motivo_lim
        elif avaliacoes >= max_avaliacoes:
            criterio_parada = "teto_avaliacoes"
        elif len(cands) > 1:
            for cg in cands:
                if avaliacoes >= max_avaliacoes:
                    criterio_parada = "teto_avaliacoes"
                    break
                motivo_lim = _excedeu_tempo_ou_memoria(t0, t_lim, m_lim_bytes)
                if motivo_lim is not None:
                    criterio_parada = motivo_lim
                    break
                f_p = av.simular_adicao_jogo(cg)
                avaliacoes += 1
                if f_p > melhor_f + 1e-12 or (abs(f_p - melhor_f) <= 1e-12 and cg < escolhido):
                    melhor_f = f_p
                    escolhido = cg

        av.adicionar_jogo(escolhido)
        usados.add(escolhido)
        if melhor_f < 0.0:
            # Avalia passo final para log se completado rapidamente
            pass
        conv.append({"passo_jogo": idx_j + 1, "avaliacao": avaliacoes})

    av_final = MotorIncrementalOtimizadoEtapa4(
        av.jogos, spec["pool"], spec["fixas_por_jogo"], spec["pesos"]
    )
    f_final = av_final.score_atual()
    if avaliacoes == 0:
        avaliacoes = 1
    return sorted(av.jogos), f_final, avaliacoes, criterio_parada, conv


def analisar_espaco_e_despachar_etapa4(
    spec: Mapping[str, Any],
    max_avaliacoes: int = 400,
    max_iteracoes: int = 200,
    limite_tempo_segundos: Optional[float] = None,
    limite_memoria_mb: Optional[float] = None,
    limite_combinacoes_exatas: int = 10_000,
    prioridade: str = "equilibrio_adaptativo",
    forcar_algoritmo: Optional[str] = None,
    distancia_exata_referencia: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Despacho adaptativo deterministico e auditavel (Requisito 3.1 / Condicionante I).
    Avalia objetivamente espaco admissivel C(K,J), orcamento B, J, dimensoes,
    limites de tempo/RAM e restricoes, registrando motivo tecnico da escolha e
    razoes de descarte de todas as alternativas nao selecionadas.
    """
    if prioridade not in PRIORIDADES_DESPACHO_PERMITIDAS:
        raise ErroValidacaoLotofacilError(
            f"Prioridade invalida '{prioridade}'. Permitidas: {PRIORIDADES_DESPACHO_PERMITIDAS}."
        )
    if forcar_algoritmo is not None and forcar_algoritmo not in ALGORITMOS_ETAPA4:
        raise ErroValidacaoLotofacilError(f"Algoritmo desconhecido '{forcar_algoritmo}'.")

    p = int(spec["tamanho_pool"])
    f_j = len(spec["fixas_por_jogo"])
    f_tot = len(spec["fixas"])
    e_tot = len(spec["bloqueadas"])
    tams = spec["tamanhos_jogos"]
    j = int(spec["quantidade_jogos"])
    m_min, m_max = min(tams), max(tams)
    heterogeneo = len(set(tams)) > 1
    espaco_adm = int(spec["espaco_admissivel"])
    viz_1swap = sum((m_i - f_j) * (p - m_i) for m_i in tams)

    # Estimativas conservadoras de custo computacional por avaliacao incremental
    custo_comb_est = sum(math.comb(m_i - 1, 3) for m_i in tams) / max(1, j)
    tempo_por_eval_est = 0.00018 * max(1.0, (custo_comb_est / 364.0) * (1.0 + j / 25.0))
    mem_base_mb_est = 0.08 + (j * j * 40 + (25_000 if sum(math.comb(m, 15) for m in tams) <= 25_000 else 0) * 64) / (1024 * 1024)
    tempo_exato_est = espaco_adm * tempo_por_eval_est if espaco_adm <= 1_000_000 else float("inf")

    min_evals_por_reinicio = max(40, 2 * j)
    r_planejado = min(6, max(3, max_avaliacoes // min_evals_por_reinicio)) if max_avaliacoes >= 3 * min_evals_por_reinicio else 1

    tem_rest_especial = (
        f_tot > 0 or e_tot > 0 or spec["modo_fixas"] != "todos_os_jogos" or heterogeneo or m_max > TAMANHO_SORTEIO
    )

    descartes: Dict[str, Dict[str, Any]] = {}
    lim_exact = validar_inteiro_estrito(limite_combinacoes_exatas, "limite_combinacoes_exatas", 1)

    if forcar_algoritmo is not None:
        escolhido = forcar_algoritmo
        regime = f"FORCA_EXPLICITA_{forcar_algoritmo.upper()}"
        motivo = (
            f"Selecao explicita pelo chamador ({forcar_algoritmo}) sob espaco={espaco_adm}, "
            f"J={j}, pool={p}, fixas_jogo={f_j}, orcamento_B={max_avaliacoes}."
        )
        for alg in ALGORITMOS_ETAPA4:
            if alg != escolhido:
                descartes[alg] = {
                    "descartado": True,
                    "motivo_tecnico": f"Substituido por selecao explicita do algoritmo '{escolhido}'.",
                }
    elif espaco_adm == 1:
        escolhido = "busca_exata_pequena"
        regime = "ESPACO_UNITARIO"
        motivo = "Espaco admissivel possui exatamente 1 carteira unica; enumeracao trivial certifica o otimo global."
        for alg in ALGORITMOS_ETAPA4:
            if alg != escolhido:
                descartes[alg] = {
                    "descartado": True,
                    "motivo_tecnico": "Desnecessario quando C(K,J)=1; busca exata certifica otimo em 1 passo.",
                }
    else:
        exato_cabe_comb = espaco_adm <= lim_exact
        exato_cabe_budget = espaco_adm <= max_avaliacoes
        exato_cabe_tempo = limite_tempo_segundos is None or tempo_exato_est <= (0.85 * limite_tempo_segundos)
        exato_cabe_mem = limite_memoria_mb is None or (mem_base_mb_est * 1.25) <= limite_memoria_mb

        if exato_cabe_comb and exato_cabe_budget and exato_cabe_tempo and exato_cabe_mem:
            escolhido = "busca_exata_pequena"
            regime = "EXATO_GLOBAL_TRATAVEL"
            motivo = (
                f"Espaco admissivel={espaco_adm} cabe integralmente no teto combinatorio ({lim_exact}), "
                f"no orcamento de avaliacoes (B={max_avaliacoes}), no tempo estimado ({tempo_exato_est:.4f}s) "
                f"e na memoria estimada ({mem_base_mb_est:.2f} MB), permitindo prova deterministica de otimo global."
            )
            for alg in ALGORITMOS_ETAPA4:
                if alg != escolhido:
                    descartes[alg] = {
                        "descartado": True,
                        "motivo_tecnico": "Inferior em garantia epistemologica: instancia pequena permite prova exata.",
                    }
        else:
            razoes_sem_exato: List[str] = []
            if not exato_cabe_comb:
                razoes_sem_exato.append(f"C={espaco_adm}>{lim_exact}")
            if not exato_cabe_budget:
                razoes_sem_exato.append(f"C={espaco_adm}>B={max_avaliacoes}")
            if not exato_cabe_tempo:
                razoes_sem_exato.append(f"tempo_est={tempo_exato_est:.3f}s excede limite={limite_tempo_segundos}s")
            if not exato_cabe_mem:
                razoes_sem_exato.append(f"mem_est={mem_base_mb_est:.2f}MB excede limite={limite_memoria_mb}MB")

            descartes["busca_exata_pequena"] = {
                "descartado": True,
                "motivo_tecnico": "Inviavel nos limites configurados: " + "; ".join(razoes_sem_exato) + ".",
            }
            descartes["referencia_aleatoria"] = {
                "descartado": True,
                "motivo_tecnico": "Utilizada apenas como linha de base comparativa sem refinamento combinatorio.",
            }

            orcamento_micro = (
                prioridade == "baixa_latencia"
                or max_avaliacoes < max(36, 3 * j)
                or (limite_tempo_segundos is not None and limite_tempo_segundos < 0.04)
            )
            espaco_amplo_estrutural = (
                (p - f_j) >= 18
                or j >= 14
                or (heterogeneo and p >= 20)
                or max_avaliacoes >= max(240, 20 * j)
            )
            if orcamento_micro:
                escolhido = "algoritmo_guloso"
                regime = "MICRO_ORCAMENTO_OU_BAIXA_LATENCIA"
                motivo = (
                    f"Prioridade='{prioridade}' ou teto restrito (B={max_avaliacoes} para J={j}, "
                    f"limite_tempo={limite_tempo_segundos}) favorecem construcao sequencial incremental O(B)."
                )
                for alg in ("busca_local_trocas", "multiplos_reinicios", "estrategia_combinada"):
                    descartes[alg] = {
                        "descartado": True,
                        "motivo_tecnico": f"Orcamento B={max_avaliacoes}/latencia insuficiente para ciclos de troca/reinicio em J={j}.",
                    }
            elif (
                prioridade == "qualidade_maxima"
                and max_avaliacoes >= max(450, 12 * j)
                and viz_1swap >= max(40, 3 * j)
            ):
                escolhido = "estrategia_combinada"
                regime = "ORCAMENTO_ALTO_EXPLORACAO_HIBRIDA"
                motivo = (
                    f"Prioridade='qualidade_maxima' com orcamento folgado (B={max_avaliacoes} >= {max(450, 12 * j)} "
                    f"para J={j}, vizinhanca_1swap={viz_1swap}) sustenta partida construtiva + busca local + perturbacoes ILS."
                )
                descartes["algoritmo_guloso"] = {
                    "descartado": True,
                    "motivo_tecnico": "Construcao isolada sem refinamento 1-swap subutiliza orcamento elevado.",
                }
                descartes["busca_local_trocas"] = {
                    "descartado": True,
                    "motivo_tecnico": "Sem perturbacao ILS ou reinicios pode estagnar cedo quando B permite exploracao ampla.",
                }
                descartes["multiplos_reinicios"] = {
                    "descartado": True,
                    "motivo_tecnico": "Substituido por estrategia hibrida com memoria anti-ciclo sob B alto e prioridade qualidade_maxima.",
                }
            elif (
                espaco_amplo_estrutural
                and max_avaliacoes >= 3 * min_evals_por_reinicio
                and viz_1swap >= max(50, 3 * j)
            ):
                escolhido = "multiplos_reinicios"
                regime = "ESPACO_AMPLO_MULTIPLOS_REINICIOS_HIPOTESE"
                motivo = (
                    f"Espaco combinatorio amplo (p={p}, f_jogo={f_j}, J={j}, vizinhanca_1swap={viz_1swap}) "
                    f"com B={max_avaliacoes} comporta {r_planejado} reinicios bem financiados "
                    f"(>= {min_evals_por_reinicio} evals/reinicio), adotando multi-start como hipotese de engenharia "
                    "para mitigar minimos locais sob validacao empirica continua."
                )
                descartes["algoritmo_guloso"] = {
                    "descartado": True,
                    "motivo_tecnico": "Sem busca local posterior apresenta pior cobertura e maior variancia em espacos amplos.",
                }
                descartes["busca_local_trocas"] = {
                    "descartado": True,
                    "motivo_tecnico": "Ponto de partida unico tende a estagnar em minimos locais quando (p-f) >= 18 ou J >= 14.",
                }
                descartes["estrategia_combinada"] = {
                    "descartado": True,
                    "motivo_tecnico": f"Sob B={max_avaliacoes}, parcela construtiva+ILS dilui o orcamento frente a R={r_planejado} descidas puras.",
                }
            else:
                escolhido = "busca_local_trocas"
                regime = "MEDIO_REFINAMENTO_LOCAL_CONCENTRADO"
                motivo = (
                    f"Orcamento moderado/concentrado (B={max_avaliacoes}, J={j}, p={p}, limiar multi-start={3 * min_evals_por_reinicio}): "
                    "concentrar 100% de B em refinamento 1-swap + replace-game sobre semente balanceada evita fragmentacao "
                    "prematura das avaliacoes por reinicio."
                )
                descartes["algoritmo_guloso"] = {
                    "descartado": True,
                    "motivo_tecnico": "Menor eficiencia terminal por ausencia de refinamento pos-construcao.",
                }
                descartes["multiplos_reinicios"] = {
                    "descartado": True,
                    "motivo_tecnico": f"Fragmentaria B={max_avaliacoes} em menos de {min_evals_por_reinicio} evals/reinicio.",
                }
                descartes["estrategia_combinada"] = {
                    "descartado": True,
                    "motivo_tecnico": f"Sobrecarga construtiva+ILS reduz profundidade da descida dentro de B={max_avaliacoes}.",
                }

    return {
        "algoritmo_escolhido": escolhido,
        "regime_identificado": regime,
        "num_reinicios_planejado": r_planejado if escolhido == "multiplos_reinicios" else 1,
        "status_epistemologico": (
            "PROVA_OTIMO_GLOBAL_INSTANCIA_PEQUENA"
            if escolhido == "busca_exata_pequena"
            else "OTIMIZACAO_HEURISTICA_SEM_PROVA_GLOBAL"
        ),
        "parametros_decisao": {
            "tamanho_pool": p,
            "fixas_totais": f_tot,
            "fixas_por_jogo": f_j,
            "bloqueadas_totais": e_tot,
            "modo_fixas": spec["modo_fixas"],
            "restricoes_especiais": tem_rest_especial,
            "quantidade_jogos": j,
            "tamanhos_jogos_min_max": [m_min, m_max],
            "carteira_heterogenea": heterogeneo,
            "espaco_admissivel": espaco_adm,
            "vizinhanca_1swap_aprox": viz_1swap,
            "max_avaliacoes": max_avaliacoes,
            "max_iteracoes": max_iteracoes,
            "limite_tempo_segundos": limite_tempo_segundos,
            "limite_memoria_mb": limite_memoria_mb,
            "limite_combinacoes_exatas": lim_exact,
            "tempo_exato_estimado_s": None if not math.isfinite(tempo_exato_est) else round(tempo_exato_est, 6),
            "memoria_base_estimada_mb": round(mem_base_mb_est, 4),
            "prioridade": prioridade,
        },
        "motivo_tecnico_escolha": motivo,
        "alternativas_descartadas": descartes,
    }


def _finalizar_resultado_etapa4(
    algoritmo: str,
    spec: Mapping[str, Any],
    carteira: Sequence[Sequence[int]],
    semente: int,
    max_avaliacoes: int,
    max_iteracoes: int,
    limite_tempo_segundos: Optional[float],
    limite_memoria_mb: Optional[float],
    avaliacoes_efetivas: int,
    iteracoes_realizadas: int,
    quantidade_reinicios: int,
    criterio_parada: str,
    inicio_perf: float,
    memoria_pico_bytes: int,
    historico_convergencia: Sequence[Mapping[str, Any]],
    otimo_global_comprovado: bool,
    decisao_despacho: Optional[Mapping[str, Any]] = None,
    f_otimo_conhecido: Optional[float] = None,
) -> Dict[str, Any]:
    validar_natureza_componente("EXATO", usa_como_ganho_preditivo=False)
    avaliacao_oficial = avaliar_carteira_etapa2(
        carteira=carteira,
        pool=spec["pool"],
        fixas=spec["fixas"],
        bloqueadas=spec["bloqueadas"],
        pesos=spec["pesos"],
        modo_fixas=spec["modo_fixas"],
    )
    duracao = time.perf_counter() - inicio_perf
    f_val = float(avaliacao_oficial["funcao_objetivo_F"])
    gap_exato = (
        max(0.0, float(f_otimo_conhecido) - f_val)
        if f_otimo_conhecido is not None
        else (0.0 if otimo_global_comprovado else None)
    )
    cart_norm = [list(sorted(jg)) for jg in sorted(tuple(sorted(x)) for x in carteira)]

    sep = avaliacao_oficial["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]
    b1 = sep["1_probabilidade_individual_bilhetes"]
    b2 = sep["2_quantidade_esperada_combinacoes_premiadas"]
    b3 = sep["3_probabilidade_conjunta_carteira"]
    dist_5 = avaliacao_oficial["detalhes"]["probabilidade_conjunta"]["distincao_cinco_grandezas_ressalva_2_1"]
    uniao_e = dict(dist_5["e_probabilidade_exata_uniao_eventos"])
    uniao_e["status"] = "calculada" if uniao_e["calculada_diretamente"] else "nao_calculada_diretamente"

    resumo_assinavel = {
        "versao_arquitetura": VERSAO_ARQUITETURA_ETAPA4,
        "versao_objetivo": VERSAO_MODELO_OBJETIVO_ETAPA2,
        "algoritmo": algoritmo,
        "semente": semente,
        "pool": list(spec["pool"]),
        "fixas": list(spec["fixas"]),
        "bloqueadas": list(spec["bloqueadas"]),
        "modo_fixas": spec["modo_fixas"],
        "tamanhos_jogos": list(spec["tamanhos_jogos"]),
        "pesos": spec["pesos"],
        "carteira": cart_norm,
        "F": round(f_val, 12),
        "historico_utilizado": HISTORICO_GERACAO_ETAPA4,
    }
    sha_exec = hashlib.sha256(
        json.dumps(resumo_assinavel, ensure_ascii=False, separators=(",", ":"), sort_keys=True).encode("utf-8")
    ).hexdigest()

    return {
        "etapa": "ETAPA_4_ARQUITETURA_ADAPTATIVA",
        "versao_arquitetura": VERSAO_ARQUITETURA_ETAPA4,
        "versao_objetivo": VERSAO_MODELO_OBJETIVO_ETAPA2,
        "modo_operacao": "COMBINATORIO_EXATO_ADAPTATIVO",
        "historico_utilizado": HISTORICO_GERACAO_ETAPA4,
        "algoritmo": algoritmo,
        "semente": semente,
        "otimo_global_comprovado": bool(otimo_global_comprovado),
        "status_distancia_otimo": (
            "CERTIFICADO_OTIMO_GLOBAL"
            if otimo_global_comprovado
            else ("MEDIDA_CONTRA_EXATO_DA_INSTANCIA" if gap_exato is not None else "NAO_CERTIFICADO_HIPOTESE_HEURISTICA")
        ),
        "distancia_otimo_global": gap_exato,
        "carteira": cart_norm,
        "funcao_objetivo_F": f_val,
        "componentes": dict(avaliacao_oficial["componentes"]),
        "chave_desempate": avaliacao_oficial["chave_desempate"],
        "distincao_seis_grandezas_probabilisticas": {
            "1_probabilidade_individual": b1["por_bilhete_percentual"],
            "2_probabilidade_pareada_detalhes": dist_5["b_probabilidade_pareada_simultanea"],
            "3_esperanca_N_prem": b2["esperado_bilhetes_premiados_float"],
            "3_variancia_N_prem": b3["variancia_bilhetes_dependente_exata"],
            "4_cota_inferior_dawson_sankoff": b3["cota_inferior_dawson_sankoff"],
            "4_cota_superior_hunter_worsley": b3["cota_superior_hunter_worsley"],
            "5_probabilidade_exata_uniao": uniao_e,
            "6_nota_escopo_S_prob": dist_5["d_limites_uniao_pelo_menos_uma_premiacao"]["aviso"],
        },
        "despacho_adaptativo": dict(decisao_despacho) if decisao_despacho is not None else None,
        "especificacao": {
            "pool": list(spec["pool"]),
            "tamanho_pool": spec["tamanho_pool"],
            "fixas": list(spec["fixas"]),
            "fixas_por_jogo": list(spec["fixas_por_jogo"]),
            "bloqueadas": list(spec["bloqueadas"]),
            "modo_fixas": spec["modo_fixas"],
            "tamanhos_jogos": list(spec["tamanhos_jogos"]),
            "quantidade_jogos": spec["quantidade_jogos"],
            "custo_total_brl": spec["custo_total_brl"],
            "pesos": dict(spec["pesos"]),
            "nome_perfil_pesos": spec["nome_perfil_pesos"],
            "espaco_admissivel": spec["espaco_admissivel"],
            "regra_caixa_etapa1": spec["regra_caixa"],
        },
        "telemetria": {
            "orcamento_max_avaliacoes": max_avaliacoes,
            "avaliacoes_efetivas": avaliacoes_efetivas,
            "taxa_utilizacao_orcamento": round(avaliacoes_efetivas / max(1, max_avaliacoes), 6),
            "iteracoes_realizadas": iteracoes_realizadas,
            "max_iteracoes": max_iteracoes,
            "quantidade_reinicios": quantidade_reinicios,
            "criterio_parada": criterio_parada,
            "tempo_total_segundos": round(duracao, 6),
            "limite_tempo_segundos": limite_tempo_segundos,
            "memoria_maxima_bytes": memoria_pico_bytes,
            "memoria_pico_mb": round(memoria_pico_bytes / (1024 * 1024), 6),
            "limite_memoria_mb": limite_memoria_mb,
            "historico_convergencia": list(historico_convergencia),
        },
        "avaliacao_etapa2": avaliacao_oficial,
        "sha256_execucao": sha_exec,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }


def _executar_algoritmo_interno_v4(
    algoritmo: str,
    spec: Mapping[str, Any],
    s_ok: int,
    av_ok: int,
    it_ok: int,
    t_lim: Optional[float],
    m_lim: Optional[float],
    num_reinicios: int,
    limite_combinacoes_exatas: int,
    decisao_despacho: Optional[Mapping[str, Any]],
    f_otimo_conhecido: Optional[float],
    medir_memoria: bool,
) -> Dict[str, Any]:
    t0 = time.perf_counter()
    m_lim_bytes = int(m_lim * 1024 * 1024) if m_lim is not None else None
    dono_trace = False
    if medir_memoria:
        dono_trace, _ = _iniciar_medicao_memoria()

    try:
        if algoritmo == "referencia_aleatoria":
            rng = random.Random(_derivar_seed_int(s_ok, "referencia_aleatoria"))
            n_amostras = min(av_ok, it_ok)
            melhor_cart: Optional[List[Tuple[int, ...]]] = None
            melhor_chave: Optional[Tuple[Any, ...]] = None
            melhor_f = -1.0
            conv: List[Dict[str, Any]] = []
            av_real = 0
            criterio = "teto_avaliacoes"

            for idx_a in range(n_amostras):
                motivo_lim = _excedeu_tempo_ou_memoria(t0, t_lim, m_lim_bytes)
                if motivo_lim is not None and idx_a > 0:
                    criterio = motivo_lim
                    break
                cand = _gerar_carteira_aleatoria_distinta(rng, spec)
                av_m = MotorIncrementalOtimizadoEtapa4(
                    cand, spec["pool"], spec["fixas_por_jogo"], spec["pesos"]
                )
                f_c = av_m.score_atual()
                av_real += 1
                chave_c = (round(f_c, 12), tuple(tuple(-d for d in jg) for jg in cand))
                if melhor_chave is None or chave_c > melhor_chave:
                    melhor_chave = chave_c
                    melhor_f = f_c
                    melhor_cart = cand
                    conv.append({"amostra": idx_a + 1, "F": round(f_c, 8)})

            if melhor_cart is None:
                raise RuntimeError("Nenhuma carteira amostrada na referencia aleatoria.")
            pico = _encerrar_medicao_memoria(dono_trace) if medir_memoria else 0
            return _finalizar_resultado_etapa4(
                algoritmo=algoritmo,
                spec=spec,
                carteira=melhor_cart,
                semente=s_ok,
                max_avaliacoes=av_ok,
                max_iteracoes=it_ok,
                limite_tempo_segundos=t_lim,
                limite_memoria_mb=m_lim,
                avaliacoes_efetivas=av_real,
                iteracoes_realizadas=av_real,
                quantidade_reinicios=1,
                criterio_parada=criterio,
                inicio_perf=t0,
                memoria_pico_bytes=pico,
                historico_convergencia=conv,
                otimo_global_comprovado=False,
                decisao_despacho=decisao_despacho,
                f_otimo_conhecido=f_otimo_conhecido,
            )

        if algoritmo == "busca_exata_pequena":
            espaco = int(spec["espaco_admissivel"])
            lim_ex = validar_inteiro_estrito(limite_combinacoes_exatas, "limite_combinacoes_exatas", 1)
            if espaco <= 0 or espaco > lim_ex:
                raise ErroValidacaoLotofacilError(
                    f"Espaco admissivel ({espaco}) excede limite_combinacoes_exatas={lim_ex}."
                )
            tams = spec["tamanhos_jogos"]
            contagem: Dict[int, int] = {}
            for m_i in tams:
                contagem[m_i] = contagem.get(m_i, 0) + 1
            fixas_j = spec["fixas_por_jogo"]
            livres = spec["livres_para_jogos"]

            grupos = []
            for m_i in sorted(contagem):
                cands_m = [tuple(sorted((*fixas_j, *cb))) for cb in itertools.combinations(livres, m_i - len(fixas_j))]
                grupos.append(itertools.combinations(cands_m, contagem[m_i]))

            melhor_cart: Optional[Tuple[Tuple[int, ...], ...]] = None
            melhor_chave: Optional[Tuple[Any, ...]] = None
            melhor_f = -1.0
            av_real = 0
            interrompido = False
            criterio = "espaco_unitario" if espaco == 1 else "enumeracao_completa"
            avaliador_reuso: Optional[MotorIncrementalOtimizadoEtapa4] = None

            for prod in itertools.product(*grupos):
                if av_real >= av_ok:
                    interrompido = True
                    criterio = "teto_avaliacoes"
                    break
                motivo_lim = _excedeu_tempo_ou_memoria(t0, t_lim, m_lim_bytes)
                if motivo_lim is not None and av_real > 0:
                    interrompido = True
                    criterio = motivo_lim
                    break
                cart = tuple(sorted(jg for grp in prod for jg in grp))
                if avaliador_reuso is None or spec["quantidade_jogos"] != avaliador_reuso.j or list(len(x) for x in cart) != avaliador_reuso.tamanhos:
                    avaliador_reuso = MotorIncrementalOtimizadoEtapa4(
                        cart, spec["pool"], fixas_j, spec["pesos"]
                    )
                    f_c = avaliador_reuso.score_atual()
                else:
                    # Atualiza apenas posicoes diferentes de forma incremental
                    for idx_u, novo_u in enumerate(cart):
                        if avaliador_reuso.jogos[idx_u] != novo_u:
                            avaliador_reuso.aplicar_substituicao_jogo(idx_u, novo_u)
                    f_c = avaliador_reuso.score_atual()

                av_real += 1
                chave_c = (round(f_c, 12), tuple(tuple(-d for d in jg) for jg in cart))
                if melhor_chave is None or chave_c > melhor_chave:
                    # Desempate completo em empates numericos proximos
                    if melhor_chave is not None and abs(f_c - melhor_f) <= 1e-10:
                        av_a = avaliar_carteira_etapa2(
                            carteira=cart,
                            pool=spec["pool"],
                            fixas=spec["fixas"],
                            bloqueadas=spec["bloqueadas"],
                            pesos=spec["pesos"],
                            modo_fixas=spec["modo_fixas"],
                        )
                        av_b = avaliar_carteira_etapa2(
                            carteira=melhor_cart,  # type: ignore[arg-type]
                            pool=spec["pool"],
                            fixas=spec["fixas"],
                            bloqueadas=spec["bloqueadas"],
                            pesos=spec["pesos"],
                            modo_fixas=spec["modo_fixas"],
                        )
                        if av_a["chave_desempate"] > av_b["chave_desempate"]:
                            melhor_f = f_c
                            melhor_chave = chave_c
                            melhor_cart = cart
                    else:
                        melhor_f = f_c
                        melhor_chave = chave_c
                        melhor_cart = cart

            if melhor_cart is None:
                raise RuntimeError("Nenhuma carteira enumerada na busca exata.")
            pico = _encerrar_medicao_memoria(dono_trace) if medir_memoria else 0
            # Condicionante V: somente prova otimo global se concluiu toda a enumeracao!
            provado = not interrompido and av_real == espaco
            return _finalizar_resultado_etapa4(
                algoritmo=algoritmo,
                spec=spec,
                carteira=melhor_cart,
                semente=s_ok,
                max_avaliacoes=av_ok,
                max_iteracoes=it_ok,
                limite_tempo_segundos=t_lim,
                limite_memoria_mb=m_lim,
                avaliacoes_efetivas=av_real,
                iteracoes_realizadas=av_real,
                quantidade_reinicios=1,
                criterio_parada=criterio,
                inicio_perf=t0,
                memoria_pico_bytes=pico,
                historico_convergencia=[{"avaliacoes": av_real, "espaco_admissivel": espaco, "F": round(melhor_f, 8)}],
                otimo_global_comprovado=provado,
                decisao_despacho=decisao_despacho,
                f_otimo_conhecido=melhor_f if provado else f_otimo_conhecido,
            )

        if algoritmo == "algoritmo_guloso":
            rng = random.Random(_derivar_seed_int(s_ok, "algoritmo_guloso"))
            cart_g, _, av_real, crit_g, conv_g = _construir_guloso_v4(
                spec, rng, av_ok, t0, t_lim, m_lim_bytes
            )
            pico = _encerrar_medicao_memoria(dono_trace) if medir_memoria else 0
            return _finalizar_resultado_etapa4(
                algoritmo=algoritmo,
                spec=spec,
                carteira=cart_g,
                semente=s_ok,
                max_avaliacoes=av_ok,
                max_iteracoes=it_ok,
                limite_tempo_segundos=t_lim,
                limite_memoria_mb=m_lim,
                avaliacoes_efetivas=av_real,
                iteracoes_realizadas=spec["quantidade_jogos"],
                quantidade_reinicios=1,
                criterio_parada=crit_g,
                inicio_perf=t0,
                memoria_pico_bytes=pico,
                historico_convergencia=conv_g,
                otimo_global_comprovado=False,
                decisao_despacho=decisao_despacho,
                f_otimo_conhecido=f_otimo_conhecido,
            )

        if algoritmo == "busca_local_trocas":
            rng = random.Random(_derivar_seed_int(s_ok, "busca_local_trocas"))
            inicial = _gerar_carteira_equilibrada_inicial(spec, rng=rng)
            cart_otm, _, av_real, it_real, crit, conv = _refinamento_local_v4(
                inicial, spec, rng, av_ok, it_ok, t0, t_lim, m_lim_bytes, usar_replace_game=True
            )
            pico = _encerrar_medicao_memoria(dono_trace) if medir_memoria else 0
            return _finalizar_resultado_etapa4(
                algoritmo=algoritmo,
                spec=spec,
                carteira=cart_otm,
                semente=s_ok,
                max_avaliacoes=av_ok,
                max_iteracoes=it_ok,
                limite_tempo_segundos=t_lim,
                limite_memoria_mb=m_lim,
                avaliacoes_efetivas=av_real,
                iteracoes_realizadas=it_real,
                quantidade_reinicios=1,
                criterio_parada=crit,
                inicio_perf=t0,
                memoria_pico_bytes=pico,
                historico_convergencia=conv,
                otimo_global_comprovado=False,
                decisao_despacho=decisao_despacho,
                f_otimo_conhecido=f_otimo_conhecido,
            )

        if algoritmo == "multiplos_reinicios":
            r_efetivos = min(validar_inteiro_estrito(num_reinicios, "num_reinicios", 1), av_ok)
            av_por_r = max(1, av_ok // r_efetivos)
            candidatas: List[List[Tuple[int, ...]]] = []
            av_tot = 0
            it_tot = 0
            reinicios_exec = 0
            conv: List[Dict[str, Any]] = []
            melhor_f_hist = -1.0
            criterio_final = "teto_avaliacoes"

            for r_idx in range(r_efetivos):
                if av_tot >= av_ok:
                    criterio_final = "teto_avaliacoes"
                    break
                motivo_lim = _excedeu_tempo_ou_memoria(t0, t_lim, m_lim_bytes)
                if motivo_lim is not None and r_idx > 0:
                    criterio_final = motivo_lim
                    break
                rng_r = random.Random(_derivar_seed_int(s_ok, f"multi_start:{r_idx}"))
                partida = (
                    _gerar_carteira_equilibrada_inicial(spec, rng=rng_r)
                    if r_idx == 0
                    else _gerar_carteira_aleatoria_distinta(rng_r, spec)
                )
                orc_r = (av_ok - av_tot) if r_idx == r_efetivos - 1 else min(av_por_r, av_ok - av_tot)
                cart_r, f_r, av_r, it_r, crit_r, _ = _refinamento_local_v4(
                    partida, spec, rng_r, orc_r, it_ok, t0, t_lim, m_lim_bytes, usar_replace_game=True
                )
                reinicios_exec += 1
                av_tot += av_r
                it_tot += it_r
                criterio_final = crit_r
                candidatas.append(cart_r)
                if f_r > melhor_f_hist + 1e-12:
                    melhor_f_hist = f_r
                    conv.append({"reinicio": reinicios_exec, "avaliacao": av_tot, "F": round(f_r, 8)})

            sel = selecionar_melhor_carteira(
                candidatas,
                pool=spec["pool"],
                fixas=spec["fixas"],
                bloqueadas=spec["bloqueadas"],
                pesos=spec["pesos"],
                modo_fixas=spec["modo_fixas"],
            )
            if av_tot >= av_ok and criterio_final == "otimo_local_sem_melhora":
                criterio_final = "teto_avaliacoes"
            pico = _encerrar_medicao_memoria(dono_trace) if medir_memoria else 0
            return _finalizar_resultado_etapa4(
                algoritmo=algoritmo,
                spec=spec,
                carteira=sel["vencedora"]["carteira_canonica"],
                semente=s_ok,
                max_avaliacoes=av_ok,
                max_iteracoes=it_ok,
                limite_tempo_segundos=t_lim,
                limite_memoria_mb=m_lim,
                avaliacoes_efetivas=av_tot,
                iteracoes_realizadas=it_tot,
                quantidade_reinicios=reinicios_exec,
                criterio_parada=criterio_final,
                inicio_perf=t0,
                memoria_pico_bytes=pico,
                historico_convergencia=conv,
                otimo_global_comprovado=False,
                decisao_despacho=decisao_despacho,
                f_otimo_conhecido=f_otimo_conhecido,
            )

        if algoritmo == "estrategia_combinada":
            rng = random.Random(_derivar_seed_int(s_ok, "estrategia_combinada"))
            orc_gul = max(spec["quantidade_jogos"], int(0.30 * av_ok))
            cart_gul, f_gul, av_gul, crit_g, _ = _construir_guloso_v4(
                spec, rng, orc_gul, t0, t_lim, m_lim_bytes
            )
            av_tot = av_gul
            it_tot = spec["quantidade_jogos"]
            conv_h: List[Dict[str, Any]] = [{"fase": "guloso", "avaliacao": av_tot, "F": round(f_gul, 8)}]
            candidatas_comb: List[List[Tuple[int, ...]]] = [cart_gul]
            reinicios_ils = 1

            restante = max(1, av_ok - av_tot)
            orc_loc = max(1, int(0.45 * restante))
            cart_loc, f_loc, av_loc, it_loc, crit_l, _ = _refinamento_local_v4(
                cart_gul, spec, rng, orc_loc, it_ok, t0, t_lim, m_lim_bytes, usar_replace_game=True
            )
            av_tot += av_loc
            it_tot += it_loc
            candidatas_comb.append(cart_loc)
            conv_h.append({"fase": "busca_local_1", "avaliacao": av_tot, "F": round(f_loc, 8)})

            # Segunda partida balanceada deterministica quando o orcamento restante comporta
            if av_tot < av_ok - max(20, spec["quantidade_jogos"]):
                mot_lim = _excedeu_tempo_ou_memoria(t0, t_lim, m_lim_bytes)
                if mot_lim is None:
                    cart_bal = _gerar_carteira_equilibrada_inicial(spec, rng=rng)
                    orc_bal = max(1, (av_ok - av_tot) // 2)
                    cart_b2, f_b2, av_b2, it_b2, crit_l, _ = _refinamento_local_v4(
                        cart_bal, spec, rng, orc_bal, it_ok, t0, t_lim, m_lim_bytes, usar_replace_game=True
                    )
                    av_tot += av_b2
                    it_tot += it_b2
                    reinicios_ils += 1
                    candidatas_comb.append(cart_b2)
                    conv_h.append({"fase": "busca_local_balanceada", "avaliacao": av_tot, "F": round(f_b2, 8)})

            sel_melhor = selecionar_melhor_carteira(
                candidatas_comb,
                pool=spec["pool"],
                fixas=spec["fixas"],
                bloqueadas=spec["bloqueadas"],
                pesos=spec["pesos"],
                modo_fixas=spec["modo_fixas"],
            )
            melhor_cart = [tuple(jg) for jg in sel_melhor["vencedora"]["carteira_canonica"]]
            visitados: set[Tuple[Tuple[int, ...], ...]] = {tuple(sorted(melhor_cart))}
            criterio_final = crit_l

            for pert_idx in range(4):
                if av_tot >= av_ok:
                    criterio_final = "teto_avaliacoes"
                    break
                mot_lim = _excedeu_tempo_ou_memoria(t0, t_lim, m_lim_bytes)
                if mot_lim is not None:
                    criterio_final = mot_lim
                    break
                av_p = MotorIncrementalOtimizadoEtapa4(
                    melhor_cart, spec["pool"], spec["fixas_por_jogo"], spec["pesos"]
                )
                n_trocas = max(1, min(3, av_p.j))
                if av_p.j > 1:
                    somas = [sum(av_p.inter_mat[i]) for i in range(av_p.j)]
                    alvos = sorted(range(av_p.j), key=lambda i: somas[i], reverse=True)[:n_trocas]
                else:
                    alvos = [0]
                pert = list(av_p.jogos)
                us_p = set(pert)
                for idx_a in alvos:
                    m_i = len(pert[idx_a])
                    if m_i - len(spec["fixas_por_jogo"]) > 0:
                        for _ in range(15):
                            cg = _gerar_jogo_aleatorio_valido(rng, spec["livres_para_jogos"], spec["fixas_por_jogo"], m_i)
                            if cg not in us_p:
                                us_p.discard(pert[idx_a])
                                pert[idx_a] = cg
                                us_p.add(cg)
                                break
                pert_ord = tuple(sorted(pert))
                if pert_ord in visitados:
                    continue
                visitados.add(pert_ord)
                reinicios_ils += 1
                orc_ils = min(max(10, (av_ok - av_tot)), max(15, av_ok // 5))
                cart_i, f_i, av_i, it_i, crit_i, _ = _refinamento_local_v4(
                    pert_ord, spec, rng, orc_ils, max(20, it_ok // 2), t0, t_lim, m_lim_bytes, usar_replace_game=True
                )
                av_tot += av_i
                it_tot += it_i
                criterio_final = crit_i
                candidatas_comb.append(cart_i)
                conv_h.append({"fase": f"ils_pert_{pert_idx + 1}", "avaliacao": av_tot, "F": round(f_i, 8)})

            sel_final = selecionar_melhor_carteira(
                candidatas_comb,
                pool=spec["pool"],
                fixas=spec["fixas"],
                bloqueadas=spec["bloqueadas"],
                pesos=spec["pesos"],
                modo_fixas=spec["modo_fixas"],
            )
            if av_tot >= av_ok and criterio_final == "otimo_local_sem_melhora":
                criterio_final = "teto_avaliacoes"
            pico = _encerrar_medicao_memoria(dono_trace) if medir_memoria else 0
            return _finalizar_resultado_etapa4(
                algoritmo=algoritmo,
                spec=spec,
                carteira=sel_final["vencedora"]["carteira_canonica"],
                semente=s_ok,
                max_avaliacoes=av_ok,
                max_iteracoes=it_ok,
                limite_tempo_segundos=t_lim,
                limite_memoria_mb=m_lim,
                avaliacoes_efetivas=av_tot,
                iteracoes_realizadas=it_tot,
                quantidade_reinicios=reinicios_ils,
                criterio_parada=criterio_final,
                inicio_perf=t0,
                memoria_pico_bytes=pico,
                historico_convergencia=conv_h,
                otimo_global_comprovado=False,
                decisao_despacho=decisao_despacho,
                f_otimo_conhecido=f_otimo_conhecido,
            )

        raise ErroValidacaoLotofacilError(f"Algoritmo desconhecido: {algoritmo!r}")
    except Exception:
        if medir_memoria and dono_trace and tracemalloc.is_tracing():
            tracemalloc.stop()
        raise


def executar_arquitetura_adaptativa_etapa4(
    pool: Optional[Iterable[int]] = None,
    fixas: Iterable[int] = (),
    bloqueadas: Iterable[int] = (),
    modo_fixas: str = "todos_os_jogos",
    quantidade_jogos: Optional[int] = None,
    tamanho_aposta: int = TAMANHO_SORTEIO,
    tamanhos_jogos: Optional[Sequence[int]] = None,
    orcamento_brl: Optional[Decimal | str | float | int] = None,
    pesos: Optional[Mapping[str, Any]] = None,
    perfil_pesos: Optional[str] = None,
    tipo_concurso: str = "concurso_regular",
    semente: int = 42,
    max_avaliacoes: int = 400,
    max_iteracoes: int = 200,
    limite_tempo_segundos: Optional[float] = None,
    limite_memoria_mb: Optional[float] = None,
    limite_combinacoes_exatas: int = 10_000,
    prioridade: str = "equilibrio_adaptativo",
    forcar_algoritmo: Optional[str] = None,
    f_otimo_conhecido: Optional[float] = None,
    medir_memoria: bool = True,
    **kwargs_extra: Any,
) -> Dict[str, Any]:
    """
    Ponto de entrada principal da Etapa 4: integra validacao oficial CAIXA (Etapa 1),
    funcao objetivo F_MODO4 (Etapa 2), despacho adaptativo deterministico, motor
    incremental otimizado e telemetria completa (Condicionantes I a VI).
    """
    _validar_sem_historico(kwargs_extra)
    if kwargs_extra:
        raise ErroValidacaoLotofacilError(f"Parametros nao suportados: {sorted(kwargs_extra)}")

    s_ok, av_ok, it_ok, t_lim, m_lim = _validar_limites_computacionais(
        semente, max_avaliacoes, max_iteracoes, limite_tempo_segundos, limite_memoria_mb
    )
    spec = _resolver_especificacao_etapa4(
        pool=pool,
        fixas=fixas,
        bloqueadas=bloqueadas,
        modo_fixas=modo_fixas,
        quantidade_jogos=quantidade_jogos,
        tamanho_aposta=tamanho_aposta,
        tamanhos_jogos=tamanhos_jogos,
        orcamento_brl=orcamento_brl,
        pesos=pesos,
        perfil_pesos=perfil_pesos,
        tipo_concurso=tipo_concurso,
    )
    decisao = analisar_espaco_e_despachar_etapa4(
        spec=spec,
        max_avaliacoes=av_ok,
        max_iteracoes=it_ok,
        limite_tempo_segundos=t_lim,
        limite_memoria_mb=m_lim,
        limite_combinacoes_exatas=limite_combinacoes_exatas,
        prioridade=prioridade,
        forcar_algoritmo=forcar_algoritmo,
    )
    return _executar_algoritmo_interno_v4(
        algoritmo=decisao["algoritmo_escolhido"],
        spec=spec,
        s_ok=s_ok,
        av_ok=av_ok,
        it_ok=it_ok,
        t_lim=t_lim,
        m_lim=m_lim,
        num_reinicios=decisao["num_reinicios_planejado"],
        limite_combinacoes_exatas=limite_combinacoes_exatas,
        decisao_despacho=decisao,
        f_otimo_conhecido=f_otimo_conhecido,
        medir_memoria=medir_memoria,
    )


def comparar_algoritmos_etapa4(
    pool: Optional[Iterable[int]] = None,
    fixas: Iterable[int] = (),
    bloqueadas: Iterable[int] = (),
    modo_fixas: str = "todos_os_jogos",
    quantidade_jogos: Optional[int] = None,
    tamanho_aposta: int = TAMANHO_SORTEIO,
    tamanhos_jogos: Optional[Sequence[int]] = None,
    orcamento_brl: Optional[Decimal | str | float | int] = None,
    pesos: Optional[Mapping[str, Any]] = None,
    perfil_pesos: Optional[str] = None,
    tipo_concurso: str = "concurso_regular",
    semente: int = 42,
    max_avaliacoes: int = 350,
    max_iteracoes: int = 200,
    limite_tempo_segundos: Optional[float] = None,
    limite_memoria_mb: Optional[float] = None,
    incluir_exato_se_viavel: bool = True,
    limite_combinacoes_exatas: int = 10_000,
) -> Dict[str, Any]:
    """
    Compara sob condicoes e orcamentos equivalentes os algoritmos da Etapa 4 e
    o despacho adaptativo deterministico (Requisito 3.2 / Condicionantes II e V).
    """
    s_ok, av_ok, it_ok, t_lim, m_lim = _validar_limites_computacionais(
        semente, max_avaliacoes, max_iteracoes, limite_tempo_segundos, limite_memoria_mb
    )
    spec = _resolver_especificacao_etapa4(
        pool, fixas, bloqueadas, modo_fixas, quantidade_jogos, tamanho_aposta, tamanhos_jogos, orcamento_brl, pesos, perfil_pesos, tipo_concurso
    )

    resultados: Dict[str, Dict[str, Any]] = {}
    f_otimo_exato: Optional[float] = None
    status_exato = "NAO_APLICAVEL_LIMITE_COMBINATORIO"

    if incluir_exato_se_viavel and 0 < spec["espaco_admissivel"] <= limite_combinacoes_exatas:
        res_ex = _executar_algoritmo_interno_v4(
            algoritmo="busca_exata_pequena",
            spec=spec,
            s_ok=s_ok,
            av_ok=max(av_ok, spec["espaco_admissivel"]),
            it_ok=max(it_ok, spec["espaco_admissivel"]),
            t_lim=t_lim,
            m_lim=m_lim,
            num_reinicios=1,
            limite_combinacoes_exatas=limite_combinacoes_exatas,
            decisao_despacho=None,
            f_otimo_conhecido=None,
            medir_memoria=True,
        )
        if res_ex["otimo_global_comprovado"]:
            resultados["busca_exata_pequena"] = res_ex
            f_otimo_exato = res_ex["funcao_objetivo_F"]
            status_exato = "EXECUTADO_OTIMO_GLOBAL_COMPROVADO"

    # Despacho adaptativo sob exatamente o mesmo max_avaliacoes das demais heuristicas
    decisao_adapt = analisar_espaco_e_despachar_etapa4(
        spec=spec,
        max_avaliacoes=av_ok,
        max_iteracoes=it_ok,
        limite_tempo_segundos=t_lim,
        limite_memoria_mb=m_lim,
        limite_combinacoes_exatas=limite_combinacoes_exatas,
        prioridade="equilibrio_adaptativo",
    )
    res_adapt = _executar_algoritmo_interno_v4(
        algoritmo=decisao_adapt["algoritmo_escolhido"],
        spec=spec,
        s_ok=s_ok,
        av_ok=av_ok,
        it_ok=it_ok,
        t_lim=t_lim,
        m_lim=m_lim,
        num_reinicios=decisao_adapt["num_reinicios_planejado"],
        limite_combinacoes_exatas=limite_combinacoes_exatas,
        decisao_despacho=decisao_adapt,
        f_otimo_conhecido=f_otimo_exato,
        medir_memoria=True,
    )
    resultados["despacho_adaptativo"] = res_adapt

    r_heur = max(3, min(6, av_ok // max(40, 2 * spec["quantidade_jogos"])))
    for alg in (
        "referencia_aleatoria",
        "algoritmo_guloso",
        "busca_local_trocas",
        "multiplos_reinicios",
        "estrategia_combinada",
    ):
        resultados[alg] = _executar_algoritmo_interno_v4(
            algoritmo=alg,
            spec=spec,
            s_ok=s_ok,
            av_ok=av_ok,
            it_ok=it_ok,
            t_lim=t_lim,
            m_lim=m_lim,
            num_reinicios=r_heur if alg == "multiplos_reinicios" else 1,
            limite_combinacoes_exatas=limite_combinacoes_exatas,
            decisao_despacho=None,
            f_otimo_conhecido=f_otimo_exato,
            medir_memoria=True,
        )

    ranking = sorted(resultados.items(), key=lambda kv: kv[1]["chave_desempate"], reverse=True)
    f_base = resultados["referencia_aleatoria"]["funcao_objetivo_F"]

    tabela: List[Dict[str, Any]] = []
    for pos, (nome, res) in enumerate(ranking, start=1):
        tel = res["telemetria"]
        f_val = res["funcao_objetivo_F"]
        tabela.append(
            {
                "posicao": pos,
                "algoritmo": nome,
                "algoritmo_despachado": decisao_adapt["algoritmo_escolhido"] if nome == "despacho_adaptativo" else nome,
                "otimo_global_comprovado": res["otimo_global_comprovado"],
                "funcao_objetivo_F": round(f_val, 8),
                "ganho_sobre_aleatorio": round(f_val - f_base, 8),
                "distancia_otimo_global": round(res["distancia_otimo_global"], 8) if res["distancia_otimo_global"] is not None else None,
                "orcamento_max_avaliacoes": tel["orcamento_max_avaliacoes"],
                "avaliacoes_efetivas": tel["avaliacoes_efetivas"],
                "taxa_utilizacao_orcamento": tel["taxa_utilizacao_orcamento"],
                "quantidade_reinicios": tel["quantidade_reinicios"],
                "criterio_parada": tel["criterio_parada"],
                "tempo_total_segundos": tel["tempo_total_segundos"],
                "memoria_maxima_bytes": tel["memoria_maxima_bytes"],
                "memoria_pico_mb": tel["memoria_pico_mb"],
            }
        )

    return {
        "escopo_epistemologico": (
            "PROVA_OTIMO_GLOBAL_INSTANCIA_PEQUENA"
            if f_otimo_exato is not None
            else "COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS"
        ),
        "condicoes_identicas": {
            "pool": list(spec["pool"]),
            "tamanho_pool": spec["tamanho_pool"],
            "fixas": list(spec["fixas"]),
            "bloqueadas": list(spec["bloqueadas"]),
            "modo_fixas": spec["modo_fixas"],
            "tamanhos_jogos": list(spec["tamanhos_jogos"]),
            "custo_total_brl": spec["custo_total_brl"],
            "espaco_admissivel": spec["espaco_admissivel"],
            "semente": s_ok,
            "max_avaliacoes": av_ok,
            "max_iteracoes": it_ok,
        },
        "decisao_despacho_adaptativo": decisao_adapt,
        "status_busca_exata": status_exato,
        "tabela_comparativa": tabela,
        "resultados_completos": resultados,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }
