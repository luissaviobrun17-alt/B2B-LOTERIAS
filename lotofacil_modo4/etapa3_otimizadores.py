# -*- coding: utf-8 -*-
"""
ETAPA 3: ESPECIFICACAO E IMPLEMENTACAO DOS ALGORITMOS DE OTIMIZACAO
=====================================================================
Implementa a especificacao formal dos algoritmos de geracao e otimizacao de
carteiras da Lotofacil (MODO 4), sob restricoes rigidas, determinismo por
semente SHA-256, avaliador incremental matematicamente equivalente a Etapa 2,
desempate lexicografico unico e zero interferencia historica na geracao.

Algoritmos implementados:
  1. referencia_aleatoria   (Baseline estocastico deterministico)
  2. busca_exata_pequena    (Enumeracao canonica exata com prova de otimo global)
  3. algoritmo_guloso       (Construtivo sequencial por ganho marginal)
  4. busca_local_trocas     (Busca local com movimentos 1-swap e replace-game)
  5. multiplos_reinicios    (Multi-start com sub-sementes SHA-256 e busca local)
  6. estrategia_combinada   (Construtivo guloso + busca local + perturbacao ILS anti-ciclo)
"""

from __future__ import annotations

from decimal import Decimal
from fractions import Fraction
import hashlib
import itertools
import json
import math
import random
import time
from types import MappingProxyType
from typing import Any, Callable, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .etapa1_regras_oficiais import (
    CENTRO_5X5,
    CLAUSULA_MATEMATICA_OBRIGATORIA,
    COLUNAS_5X5,
    DEZENAS_DISPONIVEIS,
    LINHAS_5X5,
    MAX_DEZENAS_APOSTA,
    MIN_DEZENAS_APOSTA,
    MOLDURA_5X5,
    PRECO_APOSTA_SIMPLES,
    TAMANHO_SORTEIO,
    UNIVERSO_TOTAL,
    ErroValidacaoLotofacilError,
    custo_aposta_oficial,
    validar_aposta_lotofacil,
    validar_inteiro_estrito,
    validar_natureza_componente,
)
from .etapa2_funcao_objetivo import (
    ESPECIFICACAO_COMPONENTES_ETAPA2,
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

VERSAO_OTIMIZADOR_ETAPA3 = "3.0.0-etapa3-otimizadores"
HISTORICO_GERACAO_ETAPA3 = None

ALGORITMOS_ETAPA3 = (
    "referencia_aleatoria",
    "busca_exata_pequena",
    "algoritmo_guloso",
    "busca_local_trocas",
    "multiplos_reinicios",
    "estrategia_combinada",
)

ESPECIFICACAO_ALGORITMOS_ETAPA3 = MappingProxyType(
    {
        "referencia_aleatoria": MappingProxyType(
            {
                "categoria": "BASELINE_ALEATORIO",
                "complexidade_tempo": "O(B * J * m)",
                "complexidade_espaco": "O(J * m)",
                "garante_otimo_global": False,
                "descricao": "Amostragem aleatoria deterministica de carteiras admissiveis dentro do orcamento de avaliacoes B.",
            }
        ),
        "busca_exata_pequena": MappingProxyType(
            {
                "categoria": "EXATO_GLOBAL_PEQUENA_ESCALA",
                "complexidade_tempo": "O(C(K, J) * Delta_eval)",
                "complexidade_espaco": "O(K * m + C(p, 4))",
                "garante_otimo_global": True,
                "descricao": "Enumeracao combinatoria exata de todas as C(K, J) carteiras admissiveis ate limite tratavel.",
            }
        ),
        "algoritmo_guloso": MappingProxyType(
            {
                "categoria": "CONSTRUTIVO_GULOSO",
                "complexidade_tempo": "O(J * M_cand * Delta_eval)",
                "complexidade_espaco": "O(J * m + T_cov)",
                "garante_otimo_global": False,
                "descricao": "Construcao sequencial jogo a jogo escolhendo o candidato valido de maior ganho marginal na F_MODO4.",
            }
        ),
        "busca_local_trocas": MappingProxyType(
            {
                "categoria": "BUSCA_LOCAL_TROCAS",
                "complexidade_tempo": "O(B * (C(m-1, 3) + J))",
                "complexidade_espaco": "O(J^2 + T_cov)",
                "garante_otimo_global": False,
                "descricao": "Refinamento por trocas 1-dezena intra-jogo e substituicao de bilhete redundante a partir de semente equilibrada.",
            }
        ),
        "multiplos_reinicios": MappingProxyType(
            {
                "categoria": "MULTI_START_BUSCA_LOCAL",
                "complexidade_tempo": "O(R * (B / R) * (C(m-1, 3) + J))",
                "complexidade_espaco": "O(J^2 + T_cov)",
                "garante_otimo_global": False,
                "descricao": "R reinicios com sub-sementes SHA-256 submetidos a busca local e arbitrados pelo desempate lexicografico.",
            }
        ),
        "estrategia_combinada": MappingProxyType(
            {
                "categoria": "HIBRIDO_CONSTRUTIVO_ILS",
                "complexidade_tempo": "O(B * (C(m-1, 3) + J))",
                "complexidade_espaco": "O(J^2 + T_cov + |visitados|)",
                "garante_otimo_global": False,
                "descricao": "Hibrido de partida gulosa/balanceada, busca local 1-swap, perturbacao de jogos redundantes (ILS) e memoria anti-ciclo.",
            }
        ),
    }
)

_BITS_DEZENA = tuple((1 << (d - 1)) if d >= 1 else 0 for d in range(UNIVERSO_TOTAL + 1))
_PESOS_T_COBERTURA = {1: 0.15, 2: 0.35, 3: 0.35, 4: 0.15}


def _derivar_seed_int(semente: int, rotulo: str) -> int:
    s_ok = validar_inteiro_estrito(semente, "semente", 0)
    payload = f"LOTOFACIL_MODO4_ETAPA3|{s_ok}|{rotulo}".encode("utf-8")
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _sha256_json_deterministico(obj: Any) -> str:
    txt = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(txt.encode("utf-8")).hexdigest()


def _validar_limites_computacionais(
    semente: int,
    max_avaliacoes: int,
    max_iteracoes: int,
    limite_tempo_segundos: Optional[float],
) -> Tuple[int, int, int, Optional[float]]:
    s_ok = validar_inteiro_estrito(semente, "semente", 0)
    av_ok = validar_inteiro_estrito(max_avaliacoes, "max_avaliacoes", 1)
    it_ok = validar_inteiro_estrito(max_iteracoes, "max_iteracoes", 1)
    if limite_tempo_segundos is None:
        return s_ok, av_ok, it_ok, None
    if isinstance(limite_tempo_segundos, bool) or not isinstance(limite_tempo_segundos, (int, float)):
        raise ErroValidacaoLotofacilError("limite_tempo_segundos deve ser numerico ou None.")
    t_val = float(limite_tempo_segundos)
    if not math.isfinite(t_val) or t_val <= 0.0:
        raise ErroValidacaoLotofacilError("limite_tempo_segundos deve ser positivo finito.")
    return s_ok, av_ok, it_ok, t_val


def planejar_composicoes_orcamento(
    orcamento_brl: Decimal | str | float | int,
    tamanho_pool: int,
    quantidade_fixas_por_jogo: int = 0,
    incluir_mistas: bool = True,
) -> List[Dict[str, Any]]:
    """
    Lista composicoes oficiais viaveis de tamanhos de aposta (15..20) dentro do
    orcamento informado em reais, usando aritmetica Decimal exata.
    """
    if isinstance(orcamento_brl, bool):
        raise ErroValidacaoLotofacilError("Orcamento nao pode ser booleano.")
    try:
        orc_dec = Decimal(str(orcamento_brl))
    except Exception as exc:
        raise ErroValidacaoLotofacilError(f"Orcamento invalido: {orcamento_brl!r}.") from exc
    if not orc_dec.is_finite() or orc_dec < PRECO_APOSTA_SIMPLES:
        raise ErroValidacaoLotofacilError(
            f"Orcamento R$ {orc_dec} insuficiente para ao menos 1 aposta simples (R$ {PRECO_APOSTA_SIMPLES})."
        )

    p_ok = validar_inteiro_estrito(tamanho_pool, "tamanho_pool", TAMANHO_SORTEIO, UNIVERSO_TOTAL)
    f_ok = validar_inteiro_estrito(quantidade_fixas_por_jogo, "quantidade_fixas_por_jogo", 0, p_ok)

    opcoes: List[Dict[str, Any]] = []
    # 1. Composicoes homogeneas (J bilhetes de m dezenas)
    for m in range(MIN_DEZENAS_APOSTA, min(MAX_DEZENAS_APOSTA, p_ok) + 1):
        if f_ok > m:
            continue
        preco_m = custo_aposta_oficial(m)
        if preco_m > orc_dec:
            continue
        j_max_orc = int(orc_dec // preco_m)
        teto_comb = math.comb(p_ok - f_ok, m - f_ok)
        j_eff = min(j_max_orc, teto_comb)
        if j_eff >= 1:
            gasto = preco_m * Decimal(j_eff)
            tamanhos = [m] * j_eff
            opcoes.append(
                {
                    "nome": f"homogenea_{j_eff}x_m{m}",
                    "tamanhos_jogos": tamanhos,
                    "quantidade_jogos": j_eff,
                    "custo_total_brl": str(gasto),
                    "troco_brl": str(orc_dec - gasto),
                    "combinacoes_simples_totais": j_eff * math.comb(m, TAMANHO_SORTEIO),
                }
            )
            # 2. Variante mista: se houver troco >= R$ 3.50, completar com apostas simples de 15
            if incluir_mistas and m > MIN_DEZENAS_APOSTA and f_ok <= MIN_DEZENAS_APOSTA:
                resto = orc_dec - preco_m
                j_15 = min(int(resto // PRECO_APOSTA_SIMPLES), math.comb(p_ok - f_ok, MIN_DEZENAS_APOSTA - f_ok))
                if j_15 >= 1:
                    tamanhos_mista = [m] + [MIN_DEZENAS_APOSTA] * j_15
                    gasto_mista = preco_m + PRECO_APOSTA_SIMPLES * Decimal(j_15)
                    opcoes.append(
                        {
                            "nome": f"mista_1x_m{m}_mais_{j_15}x_m15",
                            "tamanhos_jogos": tamanhos_mista,
                            "quantidade_jogos": len(tamanhos_mista),
                            "custo_total_brl": str(gasto_mista),
                            "troco_brl": str(orc_dec - gasto_mista),
                            "combinacoes_simples_totais": math.comb(m, TAMANHO_SORTEIO) + j_15,
                        }
                    )

    if not opcoes:
        raise ErroValidacaoLotofacilError(
            "Nenhuma composicao de apostas viavel encontrada para o orcamento e restricoes informados."
        )
    return opcoes


def _resolver_especificacao_problema(
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
) -> Dict[str, Any]:
    pool_efetivo = DEZENAS_DISPONIVEIS if pool is None else pool
    if pesos is not None and perfil_pesos is not None:
        raise ErroValidacaoLotofacilError("Informe apenas 'pesos' ou 'perfil_pesos', nao ambos.")
    if perfil_pesos is not None:
        if perfil_pesos not in PERFIS_PESOS_ETAPA2:
            raise ErroValidacaoLotofacilError(f"Perfil de pesos desconhecido '{perfil_pesos}'.")
        pesos_validos = validar_pesos_objetivo(PERFIS_PESOS_ETAPA2[perfil_pesos])
    else:
        pesos_validos = validar_pesos_objetivo(pesos)

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

    # Validar viabilidade combinatoria para cada tamanho presente em `tams`
    p = meta_base["tamanho_pool"]
    f_j = meta_base["quantidade_fixas_por_jogo"]
    contagem_por_m: Dict[int, int] = {}
    for m_i in tams:
        if m_i > p:
            raise ErroValidacaoLotofacilError(
                f"Aposta de {m_i} dezenas incompatível com tamanho do pool ({p})."
            )
        if f_j > m_i:
            raise ErroValidacaoLotofacilError(
                f"Quantidade de fixas por jogo ({f_j}) excede aposta de {m_i} dezenas."
            )
        contagem_por_m[m_i] = contagem_por_m.get(m_i, 0) + 1

    for m_i, qtd_m in contagem_por_m.items():
        teto_m = math.comb(p - f_j, m_i - f_j)
        if qtd_m > teto_m:
            raise ErroValidacaoLotofacilError(
                f"Impossivel gerar {qtd_m} apostas distintas de {m_i} dezenas em pool={p} "
                f"(modo_fixas='{modo_fixas}', fixas_por_jogo={f_j}): teto = {teto_m}."
            )

    custo_total = sum((custo_aposta_oficial(m_i) for m_i in tams), Decimal("0.00"))
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
        "diagnostico_compatibilidade": meta_base["diagnostico_compatibilidade"],
    }


def _combinacoes_bitmask(bits_lista: Sequence[int], r: int) -> List[int]:
    if r == 0:
        return [0]
    if r == 1:
        return list(bits_lista)
    if r == 2:
        n = len(bits_lista)
        return [bits_lista[i] | bits_lista[k] for i in range(n) for k in range(i + 1, n)]
    if r == 3:
        n = len(bits_lista)
        out: List[int] = []
        for i in range(n - 2):
            bi = bits_lista[i]
            for j in range(i + 1, n - 1):
                bij = bi | bits_lista[j]
                for k in range(j + 1, n):
                    out.append(bij | bits_lista[k])
        return out
    return [sum(c) for c in itertools.combinations(bits_lista, r)]


class AvaliadorIncrementalEtapa3:
    """
    Avaliador incremental matematicamente equivalente (<= 1e-12) a
    `avaliar_carteira_etapa2` para uso nos algoritmos de otimizacao.
    Mantem tabelas de cobertura via bitmasks de 25 bits, matriz p_2 exata,
    frequencia de dezenas e perfis estruturais 5x5 sem recalcular toda a carteira.
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

        self.jogos: List[Tuple[int, ...]] = [tuple(sorted(jg)) for jg in jogos_iniciais]
        self.j = len(self.jogos)
        self.tamanhos: List[int] = [len(jg) for jg in self.jogos]
        self.masks: List[int] = [_mascara_dezenas(jg) for jg in self.jogos]
        self.sets: List[set[int]] = [set(jg) for jg in self.jogos]

        # Contagem de uso u_d e invariantes de distribuicao/sobreposicao
        self.u_counts: List[int] = [0] * (UNIVERSO_TOTAL + 1)
        for jg in self.jogos:
            for d in jg:
                self.u_counts[d] += 1

        self.mu_livre, self.ss_min, self.ss_max = _cota_minima_variancia_uso_exata(
            self.tamanhos, self.p, self.f
        )
        self.ss_obs_livres = sum((self.u_counts[d] - self.mu_livre) ** 2 for d in self.livres_jogo)

        # Invariantes de cobertura e unicidade
        self.tetos_t: Dict[int, int] = {}
        self.cov_dict: Dict[int, Dict[int, int]] = {t: {} for t in (1, 2, 3, 4)}
        for t in (1, 2, 3, 4):
            total_pool_t = math.comb(self.p, t)
            c_fix = math.comb(self.f, t) if self.f >= t else 0
            cap_nova = sum((math.comb(m, t) - c_fix) for m in self.tamanhos)
            self.tetos_t[t] = min(total_pool_t, c_fix + cap_nova)

        for jg in self.jogos:
            bits_jg = [_BITS_DEZENA[d] for d in jg]
            for t in (1, 2, 3, 4):
                cd = self.cov_dict[t]
                for key in _combinacoes_bitmask(bits_jg, t):
                    cd[key] = cd.get(key, 0) + 1
        self.cov_unicos: Dict[int, int] = {t: len(self.cov_dict[t]) for t in (1, 2, 3, 4)}

        # Unicidade simples exata (para <= 25.000 combinacoes) ou por bilhete distinto
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

        # Probabilidade pareada exata & sobreposicao entre pares
        self.pares_totais = self.j * (self.j - 1) // 2
        self.s_i_min, self.i_min_medio = _cota_minima_intersecao_exata(self.tamanhos, self.p, self.f)
        self.s_i_max = 0
        self.inter_mat: List[List[int]] = [[0] * self.j for _ in range(self.j)]
        self.p2_mat: List[List[Fraction]] = [[Fraction(0, 1)] * self.j for _ in range(self.j)]
        self.penal_mat: List[List[float]] = [[0.0] * self.j for _ in range(self.j)]

        self.soma_inter = 0
        self.soma_penal = 0.0
        self.soma_p2 = Fraction(0, 1)
        self.soma_p2_max = Fraction(0, 1)
        self.soma_p2_ref_min = Fraction(0, 1)

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
                    self.soma_p2_max += probabilidade_conjunta_par_exata(mi, mk, c_max_par, 11)

                    c_min_par = max(0, mi + mk - self.p, self.f)
                    if mi == mk == TAMANHO_SORTEIO:
                        cl = max(c_min_par, min(c_max_par, c_low))
                        ch = max(c_min_par, min(c_max_par, c_high))
                        pl = probabilidade_conjunta_par_exata(mi, mk, cl, 11)
                        ph = probabilidade_conjunta_par_exata(mi, mk, ch, 11)
                        self.soma_p2_ref_min += pl + frac_c * (ph - pl)
                    else:
                        self.soma_p2_ref_min += probabilidade_conjunta_par_exata(mi, mk, c_min_par, 11)

                    inter = (self.masks[i] & self.masks[k]).bit_count()
                    self.inter_mat[i][k] = self.inter_mat[k][i] = inter
                    p2_ik = probabilidade_conjunta_par_exata(mi, mk, inter, 11)
                    self.p2_mat[i][k] = self.p2_mat[k][i] = p2_ik
                    pen = (max(0.0, inter - self.i_min_medio) / max(1.0, c_max_par - self.i_min_medio)) ** 2
                    self.penal_mat[i][k] = self.penal_mat[k][i] = pen

                    self.soma_inter += inter
                    self.soma_penal += pen
                    self.soma_p2 += p2_ik

        self.den_p2 = self.soma_p2_max - self.soma_p2_ref_min

        # Perfis estruturais 5x5
        self.perfis: List[Dict[str, Any]] = [extrair_perfil_estrutural_jogo(jg) for jg in self.jogos]
        self.sig_dict: Dict[Tuple[int, int, int], int] = {}
        self.linhas_tot = [0] * 5
        self.colunas_tot = [0] * 5
        self.total_marcas = sum(self.tamanhos)
        self.alvo_lc = self.total_marcas / 5.0
        self.desvio_norm_max = max(1.0, 2.0 * self.total_marcas * 0.8)

        for pf in self.perfis:
            sig = (pf["pares"], pf["moldura"], pf["soma"] // 15)
            self.sig_dict[sig] = self.sig_dict.get(sig, 0) + 1
            for r in range(5):
                self.linhas_tot[r] += pf["linhas_5x5"][r]
                self.colunas_tot[r] += pf["colunas_5x5"][r]

    def _calcular_scores_de_totais(
        self,
        cov_unicos: Mapping[int, int],
        soma_p2: Fraction,
        soma_inter: int,
        soma_penal: float,
        ss_obs: float,
        qtd_simples_unicas: int,
        qtd_sigs: int,
        linhas_tot: Sequence[int],
        colunas_tot: Sequence[int],
    ) -> Tuple[float, Dict[str, float]]:
        s_cov = 0.0
        ef2 = 1.0
        for t in (1, 2, 3, 4):
            teto = self.tetos_t[t]
            ef = min(1.0, cov_unicos[t] / teto) if teto > 0 else 1.0
            if t == 2:
                ef2 = ef
            s_cov += _PESOS_T_COBERTURA[t] * ef
        s_cov = min(1.0, max(0.0, s_cov))

        if self.j <= 1 or self.den_p2 <= 0:
            s_prob = 1.0
        else:
            s_prob = min(1.0, max(0.0, float((self.soma_p2_max - soma_p2) / self.den_p2)))

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

        taxa_perfis = qtd_sigs / self.j if self.j > 0 else 1.0
        desvio_l = sum(abs(x - self.alvo_lc) for x in linhas_tot)
        desvio_c = sum(abs(x - self.alvo_lc) for x in colunas_tot)
        eq_5x5 = min(1.0, max(0.0, 1.0 - (desvio_l + desvio_c) / (2.0 * self.desvio_norm_max)))
        s_est = min(1.0, max(0.0, 0.60 * taxa_perfis + 0.40 * eq_5x5))

        comps = {
            "cobertura_combinatoria": s_cov,
            "probabilidade_conjunta": s_prob,
            "diversificacao_sobreposicao": s_div,
            "distribuicao_dezenas": s_dist,
            "custo_beneficio": s_cb,
            "diversidade_estrutural": s_est,
        }
        f_total = sum(self.pesos[n] * comps[n] for n in NOMES_COMPONENTES)
        return f_total, comps

    def score_atual(self) -> float:
        qtd_unicas = (
            len(self.simples_dict)
            if self.rastreia_simples_completo
            else (self.total_comb_pagas if len(self.jogos_dict) == self.j else len(self.jogos_dict))
        )
        f_val, _ = self._calcular_scores_de_totais(
            self.cov_unicos,
            self.soma_p2,
            self.soma_inter,
            self.soma_penal,
            self.ss_obs_livres,
            qtd_unicas,
            len(self.sig_dict),
            self.linhas_tot,
            self.colunas_tot,
        )
        return f_val

    def _contar_simples_delta_troca(self, idx: int, nova_jg: Tuple[int, ...], nova_mask: int) -> int:
        if not self.rastreia_simples_completo:
            old_mask = self.masks[idx]
            if old_mask == nova_mask:
                return self.total_comb_pagas if len(self.jogos_dict) == self.j else len(self.jogos_dict)
            delta_dist = -(1 if self.jogos_dict[old_mask] == 1 else 0) + (
                1 if self.jogos_dict.get(nova_mask, 0) == 0 else 0
            )
            novos_dist = len(self.jogos_dict) + delta_dist
            return self.total_comb_pagas if novos_dist == self.j else novos_dist

        if self.tamanhos[idx] == TAMANHO_SORTEIO:
            old_mask = self.masks[idx]
            if old_mask == nova_mask:
                return len(self.simples_dict)
            return (
                len(self.simples_dict)
                - (1 if self.simples_dict.get(old_mask, 0) == 1 else 0)
                + (1 if self.simples_dict.get(nova_mask, 0) == 0 else 0)
            )

        # Aposta multipla m >= 16: computa intersecao exata de subconjuntos simples
        antigas = {_mascara_dezenas(c) for c in itertools.combinations(self.jogos[idx], TAMANHO_SORTEIO)}
        novas = {_mascara_dezenas(c) for c in itertools.combinations(nova_jg, TAMANHO_SORTEIO)}
        saem = antigas - novas
        entram = novas - antigas
        perdidos = sum(1 for k in saem if self.simples_dict.get(k, 0) == 1)
        ganhos = sum(1 for k in entram if self.simples_dict.get(k, 0) == 0)
        return len(self.simples_dict) - perdidos + ganhos

    def simular_troca_dezena(self, idx: int, d_sai: int, d_entra: int) -> Tuple[float, Dict[str, float]]:
        """
        Avalia sem mutacao o escore exato apos trocar 1 dezena (`d_sai -> d_entra`) no jogo `idx`.
        """
        mask_old = self.masks[idx]
        bit_sai = _BITS_DEZENA[d_sai]
        bit_entra = _BITS_DEZENA[d_entra]
        mask_new = (mask_old ^ bit_sai) | bit_entra
        outros = [d for d in self.jogos[idx] if d != d_sai]
        outros_bits = [_BITS_DEZENA[d] for d in outros]
        nova_jg = tuple(sorted((*outros, d_entra)))

        # 1. Cobertura t = 1..4 somente sobre subconjuntos incidentes em d_sai ou d_entra
        novos_cov: Dict[int, int] = {}
        cd1 = self.cov_dict[1]
        novos_cov[1] = (
            self.cov_unicos[1]
            - (1 if cd1.get(bit_sai, 0) == 1 else 0)
            + (1 if cd1.get(bit_entra, 0) == 0 else 0)
        )
        for t in (2, 3, 4):
            cdt = self.cov_dict[t]
            perd = 0
            ganh = 0
            for base_m in _combinacoes_bitmask(outros_bits, t - 1):
                if cdt.get(base_m | bit_sai, 0) == 1:
                    perd += 1
                if cdt.get(base_m | bit_entra, 0) == 0:
                    ganh += 1
            novos_cov[t] = self.cov_unicos[t] - perd + ganh

        # 2. Linha de intersecoes e p2 exato do jogo idx
        nova_soma_inter = self.soma_inter
        nova_soma_penal = self.soma_penal
        nova_soma_p2 = self.soma_p2
        mi = self.tamanhos[idx]
        for k in range(self.j):
            if k == idx:
                continue
            inter_old = self.inter_mat[idx][k]
            inter_new = (mask_new & self.masks[k]).bit_count()
            if inter_new != inter_old:
                mk = self.tamanhos[k]
                c_max_par = min(mi, mk)
                nova_soma_inter += inter_new - inter_old
                pen_new = (max(0.0, inter_new - self.i_min_medio) / max(1.0, c_max_par - self.i_min_medio)) ** 2
                nova_soma_penal += pen_new - self.penal_mat[idx][k]
                nova_soma_p2 += probabilidade_conjunta_par_exata(mi, mk, inter_new, 11) - self.p2_mat[idx][k]

        # 3. Distribuicao de dezenas livres (delta em 2 entradas)
        u_sai = self.u_counts[d_sai]
        u_ent = self.u_counts[d_entra]
        novo_ss = self.ss_obs_livres
        if d_sai not in self.set_fixas_jogo:
            novo_ss += (u_sai - 1 - self.mu_livre) ** 2 - (u_sai - self.mu_livre) ** 2
        if d_entra not in self.set_fixas_jogo:
            novo_ss += (u_ent + 1 - self.mu_livre) ** 2 - (u_ent - self.mu_livre) ** 2

        # 4. Custo-beneficio e perfis 5x5
        novas_simples = self._contar_simples_delta_troca(idx, nova_jg, mask_new)
        pf_old = self.perfis[idx]
        sig_old = (pf_old["pares"], pf_old["moldura"], pf_old["soma"] // 15)
        pares_new = pf_old["pares"] - (1 if d_sai % 2 == 0 else 0) + (1 if d_entra % 2 == 0 else 0)
        mold_new = pf_old["moldura"] - (1 if d_sai in MOLDURA_5X5 else 0) + (1 if d_entra in MOLDURA_5X5 else 0)
        soma_new = pf_old["soma"] - d_sai + d_entra
        sig_new = (pares_new, mold_new, soma_new // 15)
        novas_sigs = len(self.sig_dict)
        if sig_new != sig_old:
            novas_sigs += (1 if self.sig_dict.get(sig_new, 0) == 0 else 0) - (
                1 if self.sig_dict.get(sig_old, 0) == 1 else 0
            )

        linhas_new = list(self.linhas_tot)
        colunas_new = list(self.colunas_tot)
        r_sai, c_sai = divmod(d_sai - 1, 5)
        r_ent, c_ent = divmod(d_entra - 1, 5)
        linhas_new[r_sai] -= 1
        linhas_new[r_ent] += 1
        colunas_new[c_sai] -= 1
        colunas_new[c_ent] += 1

        return self._calcular_scores_de_totais(
            novos_cov,
            nova_soma_p2,
            nova_soma_inter,
            nova_soma_penal,
            novo_ss,
            novas_simples,
            novas_sigs,
            linhas_new,
            colunas_new,
        )

    def aplicar_substituicao_jogo(self, idx: int, novo_jogo: Sequence[int]) -> float:
        """
        Substitui integralmente o bilhete `idx` mantendo consistencia exata de
        todos os contadores incrementais.
        """
        old_jg = self.jogos[idx]
        new_jg = tuple(sorted(novo_jogo))
        if old_jg == new_jg:
            return self.score_atual()

        old_mask = self.masks[idx]
        new_mask = _mascara_dezenas(new_jg)

        for d in old_jg:
            self.ss_obs_livres -= (self.u_counts[d] - self.mu_livre) ** 2 if d not in self.set_fixas_jogo else 0.0
            self.u_counts[d] -= 1
            if d not in self.set_fixas_jogo:
                self.ss_obs_livres += (self.u_counts[d] - self.mu_livre) ** 2
        for d in new_jg:
            if d not in self.set_fixas_jogo:
                self.ss_obs_livres -= (self.u_counts[d] - self.mu_livre) ** 2
            self.u_counts[d] += 1
            if d not in self.set_fixas_jogo:
                self.ss_obs_livres += (self.u_counts[d] - self.mu_livre) ** 2

        old_bits = [_BITS_DEZENA[d] for d in old_jg]
        new_bits = [_BITS_DEZENA[d] for d in new_jg]
        for t in (1, 2, 3, 4):
            cdt = self.cov_dict[t]
            for key in _combinacoes_bitmask(old_bits, t):
                nv = cdt[key] - 1
                if nv == 0:
                    del cdt[key]
                else:
                    cdt[key] = nv
            for key in _combinacoes_bitmask(new_bits, t):
                cdt[key] = cdt.get(key, 0) + 1
            self.cov_unicos[t] = len(cdt)

        # Unicidade simples & mapa de jogos
        nv_j = self.jogos_dict[old_mask] - 1
        if nv_j == 0:
            del self.jogos_dict[old_mask]
        else:
            self.jogos_dict[old_mask] = nv_j
        self.jogos_dict[new_mask] = self.jogos_dict.get(new_mask, 0) + 1

        if self.rastreia_simples_completo:
            for jg_rem, delta in ((old_jg, -1), (new_jg, +1)):
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
            c_max_par = min(mi, mk)
            inter_new = (new_mask & self.masks[k]).bit_count()
            p2_new = probabilidade_conjunta_par_exata(mi, mk, inter_new, 11)
            pen_new = (max(0.0, inter_new - self.i_min_medio) / max(1.0, c_max_par - self.i_min_medio)) ** 2

            self.soma_inter += inter_new - self.inter_mat[idx][k]
            self.soma_penal += pen_new - self.penal_mat[idx][k]
            self.soma_p2 += p2_new - self.p2_mat[idx][k]

            self.inter_mat[idx][k] = self.inter_mat[k][idx] = inter_new
            self.p2_mat[idx][k] = self.p2_mat[k][idx] = p2_new
            self.penal_mat[idx][k] = self.penal_mat[k][idx] = pen_new

        pf_old = self.perfis[idx]
        sig_old = (pf_old["pares"], pf_old["moldura"], pf_old["soma"] // 15)
        nv_s = self.sig_dict[sig_old] - 1
        if nv_s == 0:
            del self.sig_dict[sig_old]
        else:
            self.sig_dict[sig_old] = nv_s

        pf_new = extrair_perfil_estrutural_jogo(new_jg)
        sig_new = (pf_new["pares"], pf_new["moldura"], pf_new["soma"] // 15)
        self.sig_dict[sig_new] = self.sig_dict.get(sig_new, 0) + 1

        for r in range(5):
            self.linhas_tot[r] += pf_new["linhas_5x5"][r] - pf_old["linhas_5x5"][r]
            self.colunas_tot[r] += pf_new["colunas_5x5"][r] - pf_old["colunas_5x5"][r]

        self.jogos[idx] = new_jg
        self.masks[idx] = new_mask
        self.sets[idx] = set(new_jg)
        self.perfis[idx] = pf_new
        return self.score_atual()

    def aplicar_troca_dezena(self, idx: int, d_sai: int, d_entra: int) -> float:
        nova_jg = sorted(d for d in self.jogos[idx] if d != d_sai)
        nova_jg.append(d_entra)
        return self.aplicar_substituicao_jogo(idx, nova_jg)

    def jogo_mais_redundante(self) -> int:
        """Retorna o indice do bilhete com maior soma pareada p_2 + uso excedente."""
        melhor_idx = 0
        melhor_carga = Fraction(-1, 1)
        for i in range(self.j):
            carga = sum((self.p2_mat[i][k] for k in range(self.j) if k != i), Fraction(0, 1))
            if carga > melhor_carga:
                melhor_carga = carga
                melhor_idx = i
        return melhor_idx

    def assinatura_canonica(self) -> Tuple[Tuple[int, ...], ...]:
        return tuple(sorted(self.jogos))


def _gerar_jogo_aleatorio_valido(
    rng: random.Random,
    livres: Sequence[int],
    fixas_jogo: Tuple[int, ...],
    m: int,
) -> Tuple[int, ...]:
    faltam = m - len(fixas_jogo)
    escolhidas = rng.sample(livres, faltam)
    return tuple(sorted((*fixas_jogo, *escolhidas)))


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
            # Fallback deterministico ordenado caso colisoes aleatorias ocorram em espacos densos
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
    """
    Gera semente inicial equilibrada atribuindo dezenas pela ordem de menor uso
    acumulado (com quebra de empate deterministica), respeitando unicidade.
    """
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
                subs = [d for d in ordem[faltam:] if d != d_out]
                encontrou = False
                for d_in in subs:
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


def _finalizar_resultado_etapa3(
    algoritmo: str,
    spec: Mapping[str, Any],
    carteira: Sequence[Sequence[int]],
    semente: int,
    max_avaliacoes: int,
    max_iteracoes: int,
    limite_tempo_segundos: Optional[float],
    avaliacoes_realizadas: int,
    iteracoes_realizadas: int,
    inicio_perf: float,
    historico_convergencia: Sequence[Mapping[str, Any]],
    otimo_global_comprovado: bool,
    status: str = "CONCLUIDO",
    extras: Optional[Mapping[str, Any]] = None,
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
    resumo_assinavel = {
        "versao_otimizador": VERSAO_OTIMIZADOR_ETAPA3,
        "versao_objetivo": VERSAO_MODELO_OBJETIVO_ETAPA2,
        "algoritmo": algoritmo,
        "semente": semente,
        "pool": list(spec["pool"]),
        "fixas": list(spec["fixas"]),
        "bloqueadas": list(spec["bloqueadas"]),
        "modo_fixas": spec["modo_fixas"],
        "tamanhos_jogos": list(spec["tamanhos_jogos"]),
        "pesos": spec["pesos"],
        "carteira_canonica": avaliacao_oficial["carteira_canonica"],
        "funcao_objetivo_F": round(avaliacao_oficial["funcao_objetivo_F"], 12),
        "avaliacoes_realizadas": avaliacoes_realizadas,
    }
    return {
        "status": status,
        "versao_otimizador": VERSAO_OTIMIZADOR_ETAPA3,
        "versao_modelo_objetivo": VERSAO_MODELO_OBJETIVO_ETAPA2,
        "algoritmo": algoritmo,
        "especificacao_algoritmo": dict(ESPECIFICACAO_ALGORITMOS_ETAPA3[algoritmo]),
        "historico_utilizado": HISTORICO_GERACAO_ETAPA3,
        "otimo_global_comprovado": otimo_global_comprovado,
        "parametros_execucao": {
            "semente": semente,
            "max_avaliacoes": max_avaliacoes,
            "max_iteracoes": max_iteracoes,
            "limite_tempo_segundos": limite_tempo_segundos,
            "pool": list(spec["pool"]),
            "fixas": list(spec["fixas"]),
            "bloqueadas": list(spec["bloqueadas"]),
            "modo_fixas": spec["modo_fixas"],
            "tamanhos_jogos": list(spec["tamanhos_jogos"]),
            "custo_total_brl": spec["custo_total_brl"],
            "pesos": dict(spec["pesos"]),
        },
        "telemetria": {
            "avaliacoes_realizadas": avaliacoes_realizadas,
            "iteracoes_realizadas": iteracoes_realizadas,
            "tempo_execucao_segundos": round(duracao, 6),
        },
        "carteira_otimizada": avaliacao_oficial["carteira_canonica"],
        "funcao_objetivo_F": avaliacao_oficial["funcao_objetivo_F"],
        "funcao_perda_L": avaliacao_oficial["funcao_perda_L"],
        "chave_desempate": avaliacao_oficial["chave_desempate"],
        "avaliacao_etapa2": avaliacao_oficial,
        "historico_convergencia": list(historico_convergencia),
        "extras": dict(extras or {}),
        "sha256_execucao": _sha256_json_deterministico(resumo_assinavel),
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }


def executar_referencia_aleatoria(
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
    semente: int = 42,
    max_avaliacoes: int = 200,
    max_iteracoes: int = 200,
    limite_tempo_segundos: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Baseline deterministico por amostragem aleatoria uniforme no espaco viavel.
    """
    t0 = time.perf_counter()
    s_ok, av_ok, it_ok, t_lim = _validar_limites_computacionais(
        semente, max_avaliacoes, max_iteracoes, limite_tempo_segundos
    )
    spec = _resolver_especificacao_problema(
        pool, fixas, bloqueadas, modo_fixas, quantidade_jogos, tamanho_aposta, tamanhos_jogos, orcamento_brl, pesos, perfil_pesos
    )
    rng = random.Random(_derivar_seed_int(s_ok, "referencia_aleatoria"))
    passos = min(av_ok, it_ok)

    melhor_av: Optional[Dict[str, Any]] = None
    melhor_chave: Optional[Tuple[Any, ...]] = None
    conv: List[Dict[str, Any]] = []
    avaliacoes = 0

    for passo in range(passos):
        if t_lim is not None and passo > 0 and (time.perf_counter() - t0) >= t_lim:
            break
        cand = _gerar_carteira_aleatoria_distinta(rng, spec)
        av = avaliar_carteira_etapa2(
            cand,
            pool=spec["pool"],
            fixas=spec["fixas"],
            bloqueadas=spec["bloqueadas"],
            pesos=spec["pesos"],
            modo_fixas=spec["modo_fixas"],
        )
        avaliacoes += 1
        chave = av["chave_desempate"]
        if melhor_chave is None or chave > melhor_chave:
            melhor_chave = chave
            melhor_av = av
            conv.append({"avaliacao": avaliacoes, "F": round(av["funcao_objetivo_F"], 8)})

    assert melhor_av is not None
    return _finalizar_resultado_etapa3(
        algoritmo="referencia_aleatoria",
        spec=spec,
        carteira=melhor_av["carteira_canonica"],
        semente=s_ok,
        max_avaliacoes=av_ok,
        max_iteracoes=it_ok,
        limite_tempo_segundos=t_lim,
        avaliacoes_realizadas=avaliacoes,
        iteracoes_realizadas=avaliacoes,
        inicio_perf=t0,
        historico_convergencia=conv,
        otimo_global_comprovado=False,
    )


def executar_busca_exata_pequena(
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
    semente: int = 42,
    limite_combinacoes_exatas: int = 15_000,
    limite_tempo_segundos: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Busca exata por enumeracao combinatoria integral do espaco admissivel de
    instancias pequenas, com prova de otimo global garantida via `chave_desempate_deterministica`.
    Falha de forma explicita (fail-closed) quando o espaco excede `limite_combinacoes_exatas`.
    """
    t0 = time.perf_counter()
    s_ok, lim_ok, _, t_lim = _validar_limites_computacionais(
        semente, limite_combinacoes_exatas, 1, limite_tempo_segundos
    )
    spec = _resolver_especificacao_problema(
        pool, fixas, bloqueadas, modo_fixas, quantidade_jogos, tamanho_aposta, tamanhos_jogos, orcamento_brl, pesos, perfil_pesos
    )
    tams = spec["tamanhos_jogos"]
    if len(set(tams)) != 1:
        raise ErroValidacaoLotofacilError(
            "busca_exata_pequena requer tamanhos de aposta homogeneos (use avaliador/heuristica para mistas)."
        )

    m = tams[0]
    j = spec["quantidade_jogos"]
    fixas_j = spec["fixas_por_jogo"]
    livres = spec["livres_para_jogos"]
    total_jogos = math.comb(len(livres), m - len(fixas_j))
    total_carteiras = math.comb(total_jogos, j)

    if total_carteiras > lim_ok:
        raise ErroValidacaoLotofacilError(
            f"Espaco combinatorio C({total_jogos}, {j}) = {total_carteiras} excede limite exato ({lim_ok})."
        )

    todos_jogos = [tuple(sorted((*fixas_j, *comb))) for comb in itertools.combinations(livres, m - len(fixas_j))]
    melhor_f = -1.0
    melhor_empates: List[Tuple[Tuple[int, ...], ...]] = []
    conv: List[Dict[str, Any]] = []
    avaliacoes = 0

    iter_cart = itertools.combinations(range(len(todos_jogos)), j)
    primeira = next(iter_cart)
    eval_inc = AvaliadorIncrementalEtapa3(
        [todos_jogos[idx] for idx in primeira], spec["pool"], fixas_j, spec["pesos"]
    )
    indices_atuais = list(primeira)
    f0 = eval_inc.score_atual()
    avaliacoes += 1
    melhor_f = f0
    melhor_empates = [eval_inc.assinatura_canonica()]
    conv.append({"avaliacao": 1, "F": round(f0, 8)})

    for comb_idx in iter_cart:
        if t_lim is not None and (time.perf_counter() - t0) >= t_lim:
            raise ErroValidacaoLotofacilError(
                "Limite de tempo excedido durante busca_exata_pequena; otimo global nao concluido."
            )
        for pos in range(j):
            if comb_idx[pos] != indices_atuais[pos]:
                eval_inc.aplicar_substituicao_jogo(pos, todos_jogos[comb_idx[pos]])
                indices_atuais[pos] = comb_idx[pos]
        f_val = eval_inc.score_atual()
        avaliacoes += 1
        if f_val > melhor_f + 1e-12:
            melhor_f = f_val
            melhor_empates = [eval_inc.assinatura_canonica()]
            conv.append({"avaliacao": avaliacoes, "F": round(f_val, 8)})
        elif abs(f_val - melhor_f) <= 1e-12:
            melhor_empates.append(eval_inc.assinatura_canonica())

    # Desempate oficial exato sobre todos os empatados dentro da faixa numerica 1e-12
    sel = selecionar_melhor_carteira(
        melhor_empates,
        pool=spec["pool"],
        fixas=spec["fixas"],
        bloqueadas=spec["bloqueadas"],
        pesos=spec["pesos"],
        modo_fixas=spec["modo_fixas"],
    )
    return _finalizar_resultado_etapa3(
        algoritmo="busca_exata_pequena",
        spec=spec,
        carteira=sel["vencedora"]["carteira_canonica"],
        semente=s_ok,
        max_avaliacoes=lim_ok,
        max_iteracoes=total_carteiras,
        limite_tempo_segundos=t_lim,
        avaliacoes_realizadas=avaliacoes,
        iteracoes_realizadas=avaliacoes,
        inicio_perf=t0,
        historico_convergencia=conv,
        otimo_global_comprovado=True,
        extras={
            "total_jogos_viaveis_K": total_jogos,
            "total_carteiras_enumeradas": avaliacoes,
            "empates_no_otimo": len(melhor_empates),
        },
    )


def _gerar_candidatos_jogo_guloso(
    spec: Mapping[str, Any],
    u_counts: Sequence[int],
    usados: set[Tuple[int, ...]],
    m: int,
    rng: random.Random,
    limite_cands: int,
) -> List[Tuple[int, ...]]:
    fixas_j = spec["fixas_por_jogo"]
    livres = spec["livres_para_jogos"]
    faltam = m - len(fixas_j)
    total_possiveis = math.comb(len(livres), faltam)

    if total_possiveis <= limite_cands:
        out = [
            tuple(sorted((*fixas_j, *comb)))
            for comb in itertools.combinations(livres, faltam)
        ]
        return [c for c in out if c not in usados][:limite_cands]

    cands: List[Tuple[int, ...]] = []
    vistos: set[Tuple[int, ...]] = set(usados)

    # 1. Candidatos ordenados deterministicamente por sub-utilizacao u_d com rotacoes
    livres_ord = sorted(livres, key=lambda d: (u_counts[d], d))
    for desloc in range(min(len(livres_ord), 8)):
        janela = livres_ord[desloc : desloc + faltam]
        if len(janela) < faltam:
            janela = janela + livres_ord[: faltam - len(janela)]
        cg = tuple(sorted((*fixas_j, *janela)))
        if cg not in vistos:
            vistos.add(cg)
            cands.append(cg)
            if len(cands) >= limite_cands:
                return cands

    # 2. Amostragem guiada com viés inverso a frequencia u_d (deterministica por rng)
    pesos_amostra = [1.0 / (1.0 + u_counts[d]) for d in livres]
    tentativas = 0
    max_tent = limite_cands * 6
    while len(cands) < limite_cands and tentativas < max_tent:
        tentativas += 1
        escolhidos: List[int] = []
        pool_disp = list(livres)
        pesos_disp = list(pesos_amostra)
        for _ in range(faltam):
            tot_w = sum(pesos_disp)
            alvo = rng.random() * tot_w
            acum = 0.0
            idx_pick = len(pool_disp) - 1
            for k, wk in enumerate(pesos_disp):
                acum += wk
                if acum >= alvo:
                    idx_pick = k
                    break
            escolhidos.append(pool_disp.pop(idx_pick))
            pesos_disp.pop(idx_pick)
        cg = tuple(sorted((*fixas_j, *escolhidos)))
        if cg not in vistos:
            vistos.add(cg)
            cands.append(cg)

    return cands


def executar_algoritmo_guloso(
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
    semente: int = 42,
    max_avaliacoes: int = 400,
    max_iteracoes: int = 400,
    limite_tempo_segundos: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Algoritmo construtivo guloso sequencial: monta a carteira bilhete a bilhete
    selecionando a cada passo o candidato que maximiza o ganho marginal na F_MODO4.
    """
    t0 = time.perf_counter()
    s_ok, av_ok, it_ok, t_lim = _validar_limites_computacionais(
        semente, max_avaliacoes, max_iteracoes, limite_tempo_segundos
    )
    spec = _resolver_especificacao_problema(
        pool, fixas, bloqueadas, modo_fixas, quantidade_jogos, tamanho_aposta, tamanhos_jogos, orcamento_brl, pesos, perfil_pesos
    )
    rng = random.Random(_derivar_seed_int(s_ok, "algoritmo_guloso"))
    tams = spec["tamanhos_jogos"]
    j = spec["quantidade_jogos"]

    # Orcamento de candidatos por jogo proporcional a max_avaliacoes / J
    cand_por_passo = max(2, av_ok // max(1, j))
    u_counts = [0] * (UNIVERSO_TOTAL + 1)
    carteira_atual: List[Tuple[int, ...]] = []
    usados: set[Tuple[int, ...]] = set()
    avaliacoes = 0
    conv: List[Dict[str, Any]] = []

    for idx_j, m_i in enumerate(tams):
        if t_lim is not None and idx_j > 0 and (time.perf_counter() - t0) >= t_lim:
            # Completa os restantes deterministica e rapidamente sem violar restricoes
            pass
        restantes_av = max(1, av_ok - avaliacoes)
        limite_step = min(cand_por_passo, restantes_av) if idx_j < j - 1 else restantes_av
        if idx_j == 0:
            # Passo 1: compara candidatos equilibrados no pool inteiro
            cands = _gerar_candidatos_jogo_guloso(spec, u_counts, usados, m_i, rng, max(1, min(limite_step, 16)))
        else:
            cands = _gerar_candidatos_jogo_guloso(spec, u_counts, usados, m_i, rng, max(1, limite_step))

        if not cands:
            cands = [_gerar_jogo_aleatorio_valido(rng, spec["livres_para_jogos"], spec["fixas_por_jogo"], m_i)]

        melhor_cand = cands[0]
        if len(cands) == 1 or avaliacoes >= av_ok:
            escolhido = melhor_cand
        else:
            melhor_chave: Optional[Tuple[Any, ...]] = None
            escolhido = cands[0]
            for cg in cands:
                if avaliacoes >= av_ok:
                    break
                av_p = avaliar_carteira_etapa2(
                    [*carteira_atual, cg],
                    pool=spec["pool"],
                    fixas=spec["fixas"],
                    bloqueadas=spec["bloqueadas"],
                    pesos=spec["pesos"],
                    modo_fixas=spec["modo_fixas"],
                )
                avaliacoes += 1
                ch = av_p["chave_desempate"]
                if melhor_chave is None or ch > melhor_chave:
                    melhor_chave = ch
                    escolhido = cg
                    f_parcial = av_p["funcao_objetivo_F"]
            conv.append({"passo_jogo": idx_j + 1, "avaliacao": avaliacoes, "F_parcial": round(f_parcial, 8)})

        carteira_atual.append(escolhido)
        usados.add(escolhido)
        for d in escolhido:
            u_counts[d] += 1

    return _finalizar_resultado_etapa3(
        algoritmo="algoritmo_guloso",
        spec=spec,
        carteira=carteira_atual,
        semente=s_ok,
        max_avaliacoes=av_ok,
        max_iteracoes=it_ok,
        limite_tempo_segundos=t_lim,
        avaliacoes_realizadas=max(1, avaliacoes),
        iteracoes_realizadas=j,
        inicio_perf=t0,
        historico_convergencia=conv,
        otimo_global_comprovado=False,
    )


def _executar_refinamento_local_interno(
    carteira_inicial: Sequence[Sequence[int]],
    spec: Mapping[str, Any],
    rng: random.Random,
    orcamento_avaliacoes: int,
    max_iteracoes: int,
    t0: float,
    limite_tempo_segundos: Optional[float],
    usar_replace_game: bool = True,
) -> Tuple[List[Tuple[int, ...]], float, int, int, List[Dict[str, Any]]]:
    eval_inc = AvaliadorIncrementalEtapa3(
        carteira_inicial, spec["pool"], spec["fixas_por_jogo"], spec["pesos"]
    )
    f_atual = eval_inc.score_atual()
    avaliacoes = 1
    iteracoes = 0
    conv = [{"avaliacao": 1, "F": round(f_atual, 8)}]
    livres_set = set(spec["livres_para_jogos"])

    while avaliacoes < orcamento_avaliacoes and iteracoes < max_iteracoes:
        if limite_tempo_segundos is not None and (time.perf_counter() - t0) >= limite_tempo_segundos:
            break
        iteracoes += 1
        melhorou = False

        # Ordena bilhetes do mais redundante ao menos redundante
        cargas = [
            (sum((eval_inc.p2_mat[i][k] for k in range(eval_inc.j) if k != i), Fraction(0, 1)), i)
            for i in range(eval_inc.j)
        ]
        cargas.sort(reverse=True)
        ordem_jogos = [idx for _, idx in cargas]

        melhor_movimento: Optional[Tuple[str, int, Any, float]] = None
        melhor_f_mov = f_atual + 1e-11

        # Vizinhanca 1: Troca 1-dezena (d_sai mais frequente -> d_entra menos frequente no pool)
        for idx in ordem_jogos:
            if avaliacoes >= orcamento_avaliacoes:
                break
            jg_set = eval_inc.sets[idx]
            dezs_sai = sorted((d for d in jg_set if d in livres_set), key=lambda d: (-eval_inc.u_counts[d], d))
            dezs_ent = sorted((d for d in livres_set if d not in jg_set), key=lambda d: (eval_inc.u_counts[d], d))
            if not dezs_sai or not dezs_ent:
                continue

            mask_i = eval_inc.masks[idx]
            for d_sai in dezs_sai[:6]:
                for d_ent in dezs_ent[:6]:
                    if avaliacoes >= orcamento_avaliacoes:
                        break
                    nova_mask = (mask_i ^ _BITS_DEZENA[d_sai]) | _BITS_DEZENA[d_ent]
                    if nova_mask in eval_inc.jogos_dict:
                        continue
                    f_cand, _ = eval_inc.simular_troca_dezena(idx, d_sai, d_ent)
                    avaliacoes += 1
                    if f_cand > melhor_f_mov:
                        melhor_f_mov = f_cand
                        melhor_movimento = ("swap1", idx, (d_sai, d_ent), f_cand)
                        break  # First-improvement agil dentro do jogo redundante
                if melhor_movimento is not None:
                    break
            if melhor_movimento is not None:
                break

        if melhor_movimento is not None:
            _, idx_m, (d_sai, d_ent), _ = melhor_movimento
            f_atual = eval_inc.aplicar_troca_dezena(idx_m, d_sai, d_ent)
            conv.append({"avaliacao": avaliacoes, "F": round(f_atual, 8)})
            melhorou = True
            continue

        # Vizinhanca 2: Substituicao completa do bilhete mais redundante
        if usar_replace_game and avaliacoes < orcamento_avaliacoes:
            idx_red = eval_inc.jogo_mais_redundante()
            cands_rep = _gerar_candidatos_jogo_guloso(
                spec,
                eval_inc.u_counts,
                set(eval_inc.jogos),
                eval_inc.tamanhos[idx_red],
                rng,
                min(10, orcamento_avaliacoes - avaliacoes),
            )
            jg_orig = eval_inc.jogos[idx_red]
            melhor_rep: Optional[Tuple[int, ...]] = None
            melhor_f_rep = f_atual + 1e-11
            for cg in cands_rep:
                if avaliacoes >= orcamento_avaliacoes:
                    break
                f_rep = eval_inc.aplicar_substituicao_jogo(idx_red, cg)
                avaliacoes += 1
                if f_rep > melhor_f_rep:
                    melhor_f_rep = f_rep
                    melhor_rep = cg
            if melhor_rep is not None:
                f_atual = eval_inc.aplicar_substituicao_jogo(idx_red, melhor_rep)
                conv.append({"avaliacao": avaliacoes, "F": round(f_atual, 8)})
                melhorou = True
            else:
                eval_inc.aplicar_substituicao_jogo(idx_red, jg_orig)

        if not melhorou:
            break

    return list(eval_inc.jogos), f_atual, avaliacoes, iteracoes, conv


def executar_busca_local_trocas(
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
    semente: int = 42,
    max_avaliacoes: int = 400,
    max_iteracoes: int = 200,
    limite_tempo_segundos: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Busca local deterministica com vizinhancas 1-swap direcionado (sobre dezenas
    sub/super-utilizadas) e substituicao de bilhete mais redundante.
    """
    t0 = time.perf_counter()
    s_ok, av_ok, it_ok, t_lim = _validar_limites_computacionais(
        semente, max_avaliacoes, max_iteracoes, limite_tempo_segundos
    )
    spec = _resolver_especificacao_problema(
        pool, fixas, bloqueadas, modo_fixas, quantidade_jogos, tamanho_aposta, tamanhos_jogos, orcamento_brl, pesos, perfil_pesos
    )
    rng = random.Random(_derivar_seed_int(s_ok, "busca_local_trocas"))
    inicial = _gerar_carteira_equilibrada_inicial(spec, rng=None)
    cart_otm, _, av_real, it_real, conv = _executar_refinamento_local_interno(
        inicial, spec, rng, av_ok, it_ok, t0, t_lim, usar_replace_game=True
    )
    return _finalizar_resultado_etapa3(
        algoritmo="busca_local_trocas",
        spec=spec,
        carteira=cart_otm,
        semente=s_ok,
        max_avaliacoes=av_ok,
        max_iteracoes=it_ok,
        limite_tempo_segundos=t_lim,
        avaliacoes_realizadas=av_real,
        iteracoes_realizadas=it_real,
        inicio_perf=t0,
        historico_convergencia=conv,
        otimo_global_comprovado=False,
    )


def executar_multiplos_reinicios(
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
    semente: int = 42,
    max_avaliacoes: int = 400,
    max_iteracoes: int = 200,
    num_reinicios: int = 5,
    limite_tempo_segundos: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Otimizacao por multiplos reinicios deterministicos (sub-sementes SHA-256),
    aplicando busca local em cada partida e selecionando pelo desempate oficial.
    """
    t0 = time.perf_counter()
    s_ok, av_ok, it_ok, t_lim = _validar_limites_computacionais(
        semente, max_avaliacoes, max_iteracoes, limite_tempo_segundos
    )
    r_ok = validar_inteiro_estrito(num_reinicios, "num_reinicios", 1)
    spec = _resolver_especificacao_problema(
        pool, fixas, bloqueadas, modo_fixas, quantidade_jogos, tamanho_aposta, tamanhos_jogos, orcamento_brl, pesos, perfil_pesos
    )

    reinicios_efetivos = min(r_ok, av_ok)
    av_por_r = max(1, av_ok // reinicios_efetivos)
    candidatas: List[List[Tuple[int, ...]]] = []
    avaliacoes_tot = 0
    iteracoes_tot = 0
    conv: List[Dict[str, Any]] = []
    melhor_f_hist = -1.0

    for r_idx in range(reinicios_efetivos):
        if avaliacoes_tot >= av_ok:
            break
        if t_lim is not None and r_idx > 0 and (time.perf_counter() - t0) >= t_lim:
            break
        rng_r = random.Random(_derivar_seed_int(s_ok, f"multi_start:{r_idx}"))
        partida = (
            _gerar_carteira_equilibrada_inicial(spec, rng=None)
            if r_idx == 0
            else _gerar_carteira_aleatoria_distinta(rng_r, spec)
        )
        orc_r = (av_ok - avaliacoes_tot) if r_idx == reinicios_efetivos - 1 else min(av_por_r, av_ok - avaliacoes_tot)
        cart_r, f_r, av_r, it_r, _ = _executar_refinamento_local_interno(
            partida, spec, rng_r, orc_r, it_ok, t0, t_lim, usar_replace_game=True
        )
        avaliacoes_tot += av_r
        iteracoes_tot += it_r
        candidatas.append(cart_r)
        if f_r > melhor_f_hist + 1e-12:
            melhor_f_hist = f_r
            conv.append({"reinicio": r_idx + 1, "avaliacao": avaliacoes_tot, "F": round(f_r, 8)})

    sel = selecionar_melhor_carteira(
        candidatas,
        pool=spec["pool"],
        fixas=spec["fixas"],
        bloqueadas=spec["bloqueadas"],
        pesos=spec["pesos"],
        modo_fixas=spec["modo_fixas"],
    )
    return _finalizar_resultado_etapa3(
        algoritmo="multiplos_reinicios",
        spec=spec,
        carteira=sel["vencedora"]["carteira_canonica"],
        semente=s_ok,
        max_avaliacoes=av_ok,
        max_iteracoes=it_ok,
        limite_tempo_segundos=t_lim,
        avaliacoes_realizadas=avaliacoes_tot,
        iteracoes_realizadas=iteracoes_tot,
        inicio_perf=t0,
        historico_convergencia=conv,
        otimo_global_comprovado=False,
        extras={"reinicios_executados": len(candidatas)},
    )


def executar_estrategia_combinada(
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
    semente: int = 42,
    max_avaliacoes: int = 400,
    max_iteracoes: int = 200,
    limite_tempo_segundos: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Estrategia hibrida combinada:
      1. Partida estruturada pelo construtivo guloso (com orcamento proporcional);
      2. Refinamento exato via busca local de trocas;
      3. Ciclos de Perturbacao Direcionada (ILS) nos jogos de maior covariancia
         com memoria anti-ciclo ate o orcamento de avaliacoes.
    """
    t0 = time.perf_counter()
    s_ok, av_ok, it_ok, t_lim = _validar_limites_computacionais(
        semente, max_avaliacoes, max_iteracoes, limite_tempo_segundos
    )
    spec = _resolver_especificacao_problema(
        pool, fixas, bloqueadas, modo_fixas, quantidade_jogos, tamanho_aposta, tamanhos_jogos, orcamento_brl, pesos, perfil_pesos
    )

    orc_guloso = max(1, min(av_ok, av_ok // 3))
    res_gul = executar_algoritmo_guloso(
        pool=spec["pool"],
        fixas=spec["fixas"],
        bloqueadas=spec["bloqueadas"],
        modo_fixas=spec["modo_fixas"],
        tamanhos_jogos=spec["tamanhos_jogos"],
        pesos=spec["pesos"],
        semente=s_ok,
        max_avaliacoes=orc_guloso,
        max_iteracoes=it_ok,
        limite_tempo_segundos=t_lim,
    )
    avaliacoes_tot = res_gul["telemetria"]["avaliacoes_realizadas"]
    melhor_cart = [tuple(jg) for jg in res_gul["carteira_otimizada"]]
    melhor_f = res_gul["funcao_objetivo_F"]
    conv: List[Dict[str, Any]] = [{"fase": "guloso", "avaliacao": avaliacoes_tot, "F": round(melhor_f, 8)}]
    iteracoes_tot = 1

    # Compara com semente equilibrada ciclica se ainda houver orcamento
    cart_eq = _gerar_carteira_equilibrada_inicial(spec, rng=None)
    if avaliacoes_tot < av_ok:
        av_eq = avaliar_carteira_etapa2(
            cart_eq,
            pool=spec["pool"],
            fixas=spec["fixas"],
            bloqueadas=spec["bloqueadas"],
            pesos=spec["pesos"],
            modo_fixas=spec["modo_fixas"],
        )
        avaliacoes_tot += 1
        if av_eq["funcao_objetivo_F"] > melhor_f + 1e-12:
            melhor_f = av_eq["funcao_objetivo_F"]
            melhor_cart = cart_eq
            conv.append({"fase": "equilibrada", "avaliacao": avaliacoes_tot, "F": round(melhor_f, 8)})

    visitados: set[Tuple[Tuple[int, ...], ...]] = {tuple(sorted(melhor_cart))}
    rng = random.Random(_derivar_seed_int(s_ok, "estrategia_combinada_ils"))

    ciclo = 0
    while avaliacoes_tot < av_ok:
        if t_lim is not None and (time.perf_counter() - t0) >= t_lim:
            break
        orc_ls = av_ok - avaliacoes_tot
        if ciclo == 0:
            partida_ciclo = melhor_cart
        else:
            # Perturbacao dirigida: substitui o jogo de maior p_2 por candidato pouco usado
            eval_tmp = AvaliadorIncrementalEtapa3(
                melhor_cart, spec["pool"], spec["fixas_por_jogo"], spec["pesos"]
            )
            qtd_pert = 1 if eval_tmp.j <= 3 else max(1, min(2, eval_tmp.j // 4))
            indices_pert = sorted(
                range(eval_tmp.j),
                key=lambda i: sum((eval_tmp.p2_mat[i][k] for k in range(eval_tmp.j) if k != i), Fraction(0, 1)),
                reverse=True,
            )[:qtd_pert]
            usados_c = set(eval_tmp.jogos)
            for idx_p in indices_pert:
                cands_p = _gerar_candidatos_jogo_guloso(
                    spec, eval_tmp.u_counts, usados_c, eval_tmp.tamanhos[idx_p], rng, 6
                )
                if cands_p:
                    escolha_p = cands_p[rng.randrange(len(cands_p))]
                    usados_c.discard(eval_tmp.jogos[idx_p])
                    usados_c.add(escolha_p)
                    eval_tmp.aplicar_substituicao_jogo(idx_p, escolha_p)
            partida_ciclo = list(eval_tmp.jogos)
            assin = tuple(sorted(partida_ciclo))
            if assin in visitados:
                partida_ciclo = _gerar_carteira_aleatoria_distinta(rng, spec)
            visitados.add(tuple(sorted(partida_ciclo)))

        orc_passo = max(1, min(orc_ls, max(20, (av_ok - orc_guloso) // 3)))
        cart_r, f_r, av_r, it_r, _ = _executar_refinamento_local_interno(
            partida_ciclo, spec, rng, orc_passo, it_ok, t0, t_lim, usar_replace_game=True
        )
        avaliacoes_tot += av_r
        iteracoes_tot += it_r
        if f_r > melhor_f + 1e-12:
            melhor_f = f_r
            melhor_cart = cart_r
            conv.append({"fase": f"ils_ciclo_{ciclo}", "avaliacao": avaliacoes_tot, "F": round(melhor_f, 8)})
        ciclo += 1
        if ciclo >= 6:
            break

    candidatas_fin = [res_gul["carteira_otimizada"], melhor_cart]
    sel = selecionar_melhor_carteira(
        candidatas_fin,
        pool=spec["pool"],
        fixas=spec["fixas"],
        bloqueadas=spec["bloqueadas"],
        pesos=spec["pesos"],
        modo_fixas=spec["modo_fixas"],
    )
    return _finalizar_resultado_etapa3(
        algoritmo="estrategia_combinada",
        spec=spec,
        carteira=sel["vencedora"]["carteira_canonica"],
        semente=s_ok,
        max_avaliacoes=av_ok,
        max_iteracoes=it_ok,
        limite_tempo_segundos=t_lim,
        avaliacoes_realizadas=avaliacoes_tot,
        iteracoes_realizadas=iteracoes_tot,
        inicio_perf=t0,
        historico_convergencia=conv,
        otimo_global_comprovado=False,
        extras={"ciclos_ils": ciclo},
    )


_DISPATCH_ALGORITMOS: Mapping[str, Callable[..., Dict[str, Any]]] = MappingProxyType(
    {
        "referencia_aleatoria": executar_referencia_aleatoria,
        "busca_exata_pequena": executar_busca_exata_pequena,
        "algoritmo_guloso": executar_algoritmo_guloso,
        "busca_local_trocas": executar_busca_local_trocas,
        "multiplos_reinicios": executar_multiplos_reinicios,
        "estrategia_combinada": executar_estrategia_combinada,
    }
)


def otimizar_carteira_etapa3(algoritmo: str = "estrategia_combinada", **kwargs: Any) -> Dict[str, Any]:
    """Ponto de entrada unificado dos algoritmos da Etapa 3."""
    if algoritmo not in _DISPATCH_ALGORITMOS:
        raise ErroValidacaoLotofacilError(
            f"Algoritmo desconhecido '{algoritmo}'. Disponiveis: {ALGORITMOS_ETAPA3}."
        )
    return _DISPATCH_ALGORITMOS[algoritmo](**kwargs)


def comparar_algoritmos_etapa3(
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
    semente: int = 42,
    max_avaliacoes: int = 400,
    max_iteracoes: int = 200,
    incluir_exato_se_viavel: bool = True,
    limite_combinacoes_exatas: int = 15_000,
    algoritmos: Sequence[str] = (
        "referencia_aleatoria",
        "algoritmo_guloso",
        "busca_local_trocas",
        "multiplos_reinicios",
        "estrategia_combinada",
    ),
) -> Dict[str, Any]:
    """
    Executa todos os algoritmos selecionados sob condicoes estritamente identicas:
    mesmo pool, mesmas restricoes, mesma quantidade/dimensoes, mesmo orcamento,
    mesma funcao objetivo, mesma semente e mesmo limite de avaliacoes.
    """
    spec = _resolver_especificacao_problema(
        pool, fixas, bloqueadas, modo_fixas, quantidade_jogos, tamanho_aposta, tamanhos_jogos, orcamento_brl, pesos, perfil_pesos
    )
    resultados: Dict[str, Dict[str, Any]] = {}
    status_exato = "NAO_SOLICITADO"
    f_otimo_exato: Optional[float] = None

    if incluir_exato_se_viavel:
        try:
            res_ex = executar_busca_exata_pequena(
                pool=spec["pool"],
                fixas=spec["fixas"],
                bloqueadas=spec["bloqueadas"],
                modo_fixas=spec["modo_fixas"],
                tamanhos_jogos=spec["tamanhos_jogos"] if len(set(spec["tamanhos_jogos"])) == 1 else None,
                pesos=spec["pesos"],
                semente=semente,
                limite_combinacoes_exatas=limite_combinacoes_exatas,
            )
            resultados["busca_exata_pequena"] = res_ex
            status_exato = "EXECUTADO_OTIMO_GLOBAL_COMPROVADO"
            f_otimo_exato = res_ex["funcao_objetivo_F"]
        except ErroValidacaoLotofacilError as exc:
            status_exato = f"NAO_APLICAVEL_LIMITE_COMBINATORIO: {exc}"

    kwargs_comuns = {
        "pool": spec["pool"],
        "fixas": spec["fixas"],
        "bloqueadas": spec["bloqueadas"],
        "modo_fixas": spec["modo_fixas"],
        "tamanhos_jogos": spec["tamanhos_jogos"],
        "pesos": spec["pesos"],
        "semente": semente,
        "max_avaliacoes": max_avaliacoes,
        "max_iteracoes": max_iteracoes,
    }
    for alg in algoritmos:
        if alg == "busca_exata_pequena":
            continue
        resultados[alg] = otimizar_carteira_etapa3(algoritmo=alg, **kwargs_comuns)

    ranking = sorted(
        resultados.items(),
        key=lambda kv: kv[1]["chave_desempate"],
        reverse=True,
    )
    f_baseline = (
        resultados["referencia_aleatoria"]["funcao_objetivo_F"]
        if "referencia_aleatoria" in resultados
        else None
    )

    tabela_comparativa: List[Dict[str, Any]] = []
    for pos, (nome, res) in enumerate(ranking, start=1):
        av = res["avaliacao_etapa2"]
        b3 = av["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]["3_probabilidade_conjunta_carteira"]
        cov_det = av["detalhes"]["cobertura_combinatoria"]["por_ordem_t"]
        div_det = av["detalhes"]["diversificacao_sobreposicao"]
        dist_det = av["detalhes"]["distribuicao_dezenas"]
        f_val = res["funcao_objetivo_F"]
        tabela_comparativa.append(
            {
                "posicao": pos,
                "algoritmo": nome,
                "otimo_global_comprovado": res["otimo_global_comprovado"],
                "funcao_objetivo_F": round(f_val, 8),
                "ganho_sobre_aleatorio": (round(f_val - f_baseline, 8) if f_baseline is not None else None),
                "gap_para_otimo_exato": (round(f_otimo_exato - f_val, 8) if f_otimo_exato is not None else None),
                "S_cov": round(av["componentes"]["cobertura_combinatoria"], 6),
                "S_prob": round(av["componentes"]["probabilidade_conjunta"], 6),
                "pares_cobertos": cov_det[2]["cobertos"],
                "trincas_cobertas": cov_det[3]["cobertos"],
                "intersecao_maxima": div_det["intersecao_maxima"],
                "amplitude_uso_livres": dist_det["amplitude_uso_livres"],
                "variancia_N_prem": round(b3["variancia_bilhetes_dependente_exata"], 6),
                "cota_ds_percentual": round(b3["cota_inferior_dawson_sankoff"] * 100, 4),
                "cota_hw_percentual": round(b3["cota_superior_hunter_worsley"] * 100, 4),
                "avaliacoes": res["telemetria"]["avaliacoes_realizadas"],
                "tempo_segundos": res["telemetria"]["tempo_execucao_segundos"],
                "sha256_execucao": res["sha256_execucao"],
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
            "semente": semente,
            "max_avaliacoes": max_avaliacoes,
            "max_iteracoes": max_iteracoes,
        },
        "status_busca_exata": status_exato,
        "melhor_algoritmo_empirico": ranking[0][0],
        "tabela_comparativa": tabela_comparativa,
        "resultados_completos": resultados,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }
