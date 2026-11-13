# -*- coding: utf-8 -*-
"""
ETAPA 4: REFERENCIA INDEPENDENTE ZERO-DEPENDENCIA E AUDITORIA DE ISOLAMENTO
==========================================================================
Implementacao totalmente independente de todos os demais modulos do projeto
(`etapa1_*`, `etapa2_*`, `etapa3_*`, `etapa4_arquitetura_adaptativa.py`,
`motor_*`, etc.), utilizando exclusivamente a biblioteca padrao do Python.

Garantias exigidas pelas Condicionantes III, IV, V e VI:
  1. Zero importacoes internas ou reutilizacao de tabelas/funcoes avaliadas
     (verificavel por analise estatica da AST em `auditar_independencia_ast_etapa4`).
  2. Recalculo exato do zero das regras oficiais da CAIXA, probabilidade
     hipergeometrica, formulacao 4-regioes p_2(m1, m2, c), Kruskal MST para
     Hunter-Worsley, Dawson-Sankoff e os quatro componentes heuristicos/exatos.
  3. Verificacao da preservacao integral dos hashes SHA-256 congelados das
     Etapas 1, 2 e 3.
  4. Solucionador exato independente (para espacos pequenos homogeneos ou
     mistos) e conferencia numerica de equivalencia (<= 1e-12).
"""

from __future__ import annotations

import ast
from decimal import Decimal
from fractions import Fraction
import hashlib
import itertools
import math
import os
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

VERSAO_REFERENCIA_ETAPA4 = "4.0.0-referencia-zero-dependencia"

_UNIVERSO = 25
_SORTEIO = 15
_MIN_PREMIO = 11
_MIN_APOSTA = 15
_MAX_APOSTA = 20
_ESPACO_SIMPLES = 3_268_760
_PRECO_SIMPLES = Decimal("3.50")

_PESOS_PADRAO_REF: Dict[str, float] = {
    "cobertura_combinatoria": 0.30,
    "probabilidade_conjunta": 0.25,
    "diversificacao_sobreposicao": 0.20,
    "distribuicao_dezenas": 0.10,
    "custo_beneficio": 0.10,
    "diversidade_estrutural": 0.05,
}
_PESOS_COBERTURA_T: Dict[int, float] = {1: 0.15, 2: 0.35, 3: 0.35, 4: 0.15}
_MOLDURA_REF: Set[int] = {1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25}

_CLAUSULA_CIENTIFICA = (
    "O sistema não prevê resultados futuros nem altera a probabilidade matemática "
    "individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição "
    "combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre "
    "eventos premiados e melhorar a cobertura conjunta observada."
)

# Hashes SHA-256 congelados pre-Etapa 4 para garantia de nao-sobrescrita (Condicionante IV)
HASHES_CONGELADOS_ETAPAS_1_2_3: Dict[str, str] = {
    "lotofacil_modo4/__init__.py": "4ea5d507cdc437af1fe93a4a6e83eee0b8d63edc5f6aefadcacb03aab0a4c664",
    "lotofacil_modo4/etapa1_regras_oficiais.py": "09bc206ca1b35372f59d522a4653931f2d2cc637ca8880eeff149dc4e3ad06af",
    "lotofacil_modo4/sincronizador_caixa.py": "a5199ca0c1b118dfc8933ede402edc5b41c1201fb964ca6cc0e7159d8159f9ae",
    "lotofacil_modo4/gerar_evidencias_etapa1.py": "ec9f94b36df4c45d15278306606c51673c7884ebde87af1fab601631c599108e",
    "lotofacil_modo4/etapa2_funcao_objetivo.py": "664d10d152545799f9fe7705f5d27ffbe441d9daedb5fa6b0c9e20fd203d5bd4",
    "lotofacil_modo4/etapa2_referencia_independente.py": "6bd58b9c3337ec8178100d4e79d26eddafe525041a6db99222f1c59d6749a84f",
    "lotofacil_modo4/gerar_evidencias_etapa2.py": "9f73ee2fbbaf5092ceb1fb9cd17b116fbdc74e8768b42f33e841b071c9208d55",
    "lotofacil_modo4/etapa3_otimizadores.py": "791d40521e93627fbe1f07bfd1c71ccf6b3a2338d48169196150a62ba8ad2663",
    "lotofacil_modo4/etapa3_referencia_independente.py": "ab3fd59d3f8bb10300c376bd789b3c0cd293e01bc74645499dee16ad93344342",
    "lotofacil_modo4/gerar_evidencias_etapa3.py": "1540aa33c82729e41245e3de696cfba3d4aa6afd8885a1843a7bfb86fe2f7e9d",
    "auditoria/lotofacil_modo4/auditoria_base_caixa_etapa1.json": "c14794ab607e3b76e083846aa14d868a0bf347ddb79c32c8e30f7b673e02bd1a",
    "auditoria/lotofacil_modo4/etapa_01_evidencias.json": "54fab20dbc4ce513caecaa8e3442ff26f9e0590d22f3fc8d16f7420a4487bd3e",
    "auditoria/lotofacil_modo4/ETAPA_01_REGRAS_E_FORMALIZACAO_MATEMATICA.md": "354195530957c5ff309b4c08f9954214ccdf0f6918c91d8375a1b744d5561ca0",
    "auditoria/lotofacil_modo4/etapa_02_evidencias.json": "511dc2d862363e3337d293d06d90443802846e134bebad9f869e48a87d51469f",
    "auditoria/lotofacil_modo4/ETAPA_02_FUNCAO_OBJETIVO_E_OTIMIZACAO.md": "52a8513d26cf3d848e14b315fff9d451a6daf712c6df7113553d530fa8ecbc87",
    "auditoria/lotofacil_modo4/etapa_03_evidencias.json": "ecf29ec0cfacfcb9493c2a15b5827693834d41be210e6bba4493a0e90aa8a171",
    "auditoria/lotofacil_modo4/ETAPA_03_ALGORITMOS_DE_OTIMIZACAO.md": "be799bad875e772405009064bbc09be1a9e5071c4ade8916d18c74747801bd4f",
    "testes/test_lotofacil_modo4_etapa1.py": "5eea34fbda9bebb33bd2c92b4f45d93c971499d3e23996bc5938eb8368288685",
    "testes/test_lotofacil_modo4_etapa2.py": "bf12bec5b2baece0d308b1c731a7b3eb38176da5937cf88c9aacda5108b36630",
    "testes/test_lotofacil_modo4_etapa3.py": "7e1507537d56daa390c4b67ef8e3d2800b8b89c8a73256c4fc731a5428ca0367",
}

_PREFIXOS_INTERNOS_PROIBIDOS = (
    "lotofacil_modo4",
    "motor_",
    "auditoria",
    "combinatoria",
    "estatistica",
    "otimizacao",
    "probabilidade",
    "backtest",
    "monte_carlo",
    "simulacao",
    "api",
)


def auditar_independencia_ast_etapa4(
    caminho_arquivo: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Analisa a AST do modulo de referencia independente e comprova que nenhuma
    importacao relativa ou de modulos internos do projeto existe neste arquivo.
    """
    alvo = caminho_arquivo or os.path.abspath(__file__)
    with open(alvo, "r", encoding="utf-8") as f:
        codigo = f.read()

    arvore = ast.parse(codigo, filename=alvo)
    modulos_importados: List[str] = []
    violacoes: List[str] = []

    for node in ast.walk(arvore):
        if isinstance(node, ast.Import):
            for alias in node.names:
                nome = alias.name
                modulos_importados.append(nome)
                raiz = nome.split(".")[0]
                if any(raiz == p or raiz.startswith(p) for p in _PREFIXOS_INTERNOS_PROIBIDOS):
                    violacoes.append(f"Import proibido de modulo interno: '{nome}'")
        elif isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            ident = ("." * node.level) + mod
            modulos_importados.append(ident)
            if node.level > 0:
                violacoes.append(f"Import relativo proibido na referencia independente: '{ident}'")
            raiz = mod.split(".")[0] if mod else ""
            if raiz and any(raiz == p or raiz.startswith(p) for p in _PREFIXOS_INTERNOS_PROIBIDOS):
                violacoes.append(f"ImportFrom proibido de modulo interno: '{mod}'")

    return {
        "arquivo_auditado": alvo,
        "total_imports": len(modulos_importados),
        "modulos_importados": sorted(set(modulos_importados)),
        "dependencias_internas_detectadas": len(violacoes),
        "violacoes": violacoes,
        "independencia_comprovada": len(violacoes) == 0,
    }


def verificar_preservacao_etapas_1_2_3_ref(base_dir: Optional[str] = None) -> Dict[str, Any]:
    """
    Confere se todos os 20 artefatos congelados das Etapas 1, 2 e 3 permanecem
    bit-a-bit identicos aos hashes registrados antes da Etapa 4.
    """
    raiz = base_dir or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    conferidos: Dict[str, str] = {}
    divergencias: List[Dict[str, Any]] = []

    for rel_path, hash_esperado in HASHES_CONGELADOS_ETAPAS_1_2_3.items():
        caminho = os.path.join(raiz, rel_path.replace("/", os.sep))
        if not os.path.isfile(caminho):
            divergencias.append({"arquivo": rel_path, "motivo": "ausente"})
            continue
        with open(caminho, "rb") as f:
            hash_atual = hashlib.sha256(f.read()).hexdigest()
        conferidos[rel_path] = hash_atual
        if hash_atual != hash_esperado:
            divergencias.append(
                {
                    "arquivo": rel_path,
                    "motivo": "hash_divergente",
                    "esperado": hash_esperado,
                    "atual": hash_atual,
                }
            )

    return {
        "total_arquivos_congelados": len(HASHES_CONGELADOS_ETAPAS_1_2_3),
        "preservado_integralmente": len(divergencias) == 0,
        "divergencias": divergencias,
        "hashes_atuais": conferidos,
    }


def _validar_int_estrito_ref(valor: Any, nome: str, minimo: Optional[int] = None, maximo: Optional[int] = None) -> int:
    if isinstance(valor, bool) or not isinstance(valor, int):
        raise ValueError(f"Parametro '{nome}' deve ser inteiro estrito (recebido {type(valor).__name__}).")
    if minimo is not None and valor < minimo:
        raise ValueError(f"Parametro '{nome}'={valor} abaixo do minimo {minimo}.")
    if maximo is not None and valor > maximo:
        raise ValueError(f"Parametro '{nome}'={valor} acima do maximo {maximo}.")
    return valor


def _validar_aposta_ref(aposta: Iterable[int]) -> Tuple[int, ...]:
    vals = [_validar_int_estrito_ref(d, "dezena", 1, _UNIVERSO) for d in aposta]
    ord_vals = tuple(sorted(set(vals)))
    if len(ord_vals) != len(vals):
        raise ValueError("Aposta contem dezenas duplicadas.")
    if not (_MIN_APOSTA <= len(ord_vals) <= _MAX_APOSTA):
        raise ValueError(f"Quantidade de dezenas ({len(ord_vals)}) fora de [15..20].")
    return ord_vals


def prob_individual_ref(m: int) -> Fraction:
    total = 0
    for k in range(_MIN_PREMIO, min(m, _SORTEIO) + 1):
        fora_req = _SORTEIO - k
        if 0 <= fora_req <= _UNIVERSO - m:
            total += math.comb(m, k) * math.comb(_UNIVERSO - m, fora_req)
    return Fraction(total, _ESPACO_SIMPLES)


def prob_par_quatro_regioes_ref(m1: int, m2: int, c: int, k_min: int = _MIN_PREMIO) -> Fraction:
    n0 = c
    n1 = m1 - c
    n2 = m2 - c
    n3 = _UNIVERSO - (m1 + m2 - c)
    if min(n0, n1, n2, n3) < 0:
        raise ValueError(f"Configuracao geometrica invalida: m1={m1}, m2={m2}, c={c}.")

    numerador = 0
    for x0 in range(max(0, 2 * k_min - _SORTEIO), min(n0, _SORTEIO) + 1):
        c0 = math.comb(n0, x0)
        rem_x1_min = max(0, k_min - x0)
        rem_x1_max = min(n1, _SORTEIO - x0)
        if rem_x1_min > rem_x1_max:
            continue
        for x1 in range(rem_x1_min, rem_x1_max + 1):
            c01 = c0 * math.comb(n1, x1)
            rem_x2_min = max(0, k_min - x0)
            rem_x2_max = min(n2, _SORTEIO - x0 - x1)
            if rem_x2_min > rem_x2_max:
                continue
            for x2 in range(rem_x2_min, rem_x2_max + 1):
                x3 = _SORTEIO - x0 - x1 - x2
                if 0 <= x3 <= n3:
                    numerador += c01 * math.comb(n2, x2) * math.comb(n3, x3)
    return Fraction(numerador, _ESPACO_SIMPLES)


def contar_espaco_admissivel_ref(
    tamanhos_jogos: Sequence[int],
    p: int,
    f_jogo: int,
) -> int:
    """
    Calcula o tamanho exato C(K, J) (ou produto por dimensao em carteiras mistas)
    do espaco de carteiras distintas admissiveis.
    """
    contagem: Dict[int, int] = {}
    for m in tamanhos_jogos:
        contagem[m] = contagem.get(m, 0) + 1
    total = 1
    for m, qtd in contagem.items():
        k_m = math.comb(p - f_jogo, m - f_jogo)
        if qtd > k_m:
            return 0
        total *= math.comb(k_m, qtd)
    return total


def _mst_kruskal_ref(j: int, p2_mat: Sequence[Sequence[Fraction]]) -> Fraction:
    arestas: List[Tuple[Fraction, int, int]] = []
    for i in range(j):
        for k in range(i + 1, j):
            arestas.append((p2_mat[i][k], i, k))
    arestas.sort(key=lambda x: x[0], reverse=True)
    pai = list(range(j))

    def achar(x: int) -> int:
        while pai[x] != x:
            pai[x] = pai[pai[x]]
            x = pai[x]
        return x

    soma_mst = Fraction(0, 1)
    ligadas = 0
    for peso, u, v in arestas:
        ru, rv = achar(u), achar(v)
        if ru != rv:
            pai[ru] = rv
            soma_mst += peso
            ligadas += 1
            if ligadas == j - 1:
                break
    return soma_mst


def _cota_ds_ref(j: int, p_ind: Sequence[Fraction], soma_p2_pares: Fraction) -> Fraction:
    if j == 1:
        return p_ind[0]
    s1 = sum(p_ind, Fraction(0, 1))
    s2 = soma_p2_pares
    if s2 == 0:
        return min(Fraction(1, 1), s1)
    k_star = 1 + int((2 * s2) // s1)
    return min(Fraction(1, 1), Fraction(2 * s1, k_star + 1) - Fraction(2 * s2, k_star * (k_star + 1)))


def _cota_min_inter_ref(tams: Sequence[int], p: int, f_jogo: int) -> Tuple[int, float]:
    j = len(tams)
    if j <= 1:
        return 0, 0.0
    pares = j * (j - 1) // 2
    soma_m = sum(tams)
    soma_m_livres = soma_m - j * f_jogo
    p_l = p - f_jogo
    q, r = divmod(soma_m_livres, p_l)
    s_l = r * (q + 1) * q // 2 + (p_l - r) * q * (q - 1) // 2
    s_min = j * (j - 1) // 2 * f_jogo + s_l
    return s_min, s_min / pares


def _cota_var_livres_ref(tams: Sequence[int], p: int, f_jogo: int) -> Tuple[float, float, float]:
    p_l = p - f_jogo
    if p_l <= 0:
        return 0.0, 0.0, 0.0
    soma_livres = sum(max(0, m - f_jogo) for m in tams)
    if soma_livres == 0:
        return 0.0, 0.0, 0.0
    mu = soma_livres / p_l
    q, r = divmod(soma_livres, p_l)
    ss_min = r * (q + 1 - mu) ** 2 + (p_l - r) * (q - mu) ** 2
    if p_l <= 1:
        ss_max = ss_min
    else:
        u_pior = [0] * p_l
        for m_i in tams:
            k_i = min(max(0, m_i - f_jogo), p_l)
            for pos in range(k_i):
                u_pior[pos] += 1
        ss_max = sum((u - mu) ** 2 for u in u_pior)
    return mu, ss_min, max(ss_min, ss_max)


def avaliar_carteira_ref_etapa4(
    carteira: Iterable[Iterable[int]],
    pool: Optional[Iterable[int]] = None,
    fixas: Iterable[int] = (),
    bloqueadas: Iterable[int] = (),
    modo_fixas: str = "todos_os_jogos",
    pesos: Optional[Mapping[str, float]] = None,
) -> Dict[str, Any]:
    """
    Avaliador independente zero-dependencia de etapa1/2/3/4.
    Retorna F_MODO4, componentes, chave de desempate e as seis distincoes
    probabilisticas obrigatorias pela Condicionante VI.
    """
    if modo_fixas not in ("todos_os_jogos", "composicao_pool"):
        raise ValueError(f"modo_fixas invalido: {modo_fixas!r}")
    pool_ord = tuple(sorted(set(range(1, _UNIVERSO + 1) if pool is None else pool)))
    p = len(pool_ord)
    pool_set = set(pool_ord)
    fixas_ord = tuple(sorted(set(fixas)))
    fixas_set = set(fixas_ord)
    bloq_set = set(bloqueadas)

    if not (_MIN_APOSTA <= p <= _UNIVERSO):
        raise ValueError(f"Pool fora de [15..25]: {p}")
    if not fixas_set.issubset(pool_set):
        raise ValueError("Fixas contem dezenas fora do pool.")
    if bloq_set & pool_set or bloq_set & fixas_set:
        raise ValueError("Conflito entre bloqueadas e pool/fixas.")

    jogos = [_validar_aposta_ref(jg) for jg in carteira]
    if not jogos:
        raise ValueError("Carteira vazia.")
    sets = [set(jg) for jg in jogos]
    for s_jg in sets:
        if not s_jg.issubset(pool_set):
            raise ValueError("Jogo contem dezena fora do pool.")
        if modo_fixas == "todos_os_jogos" and not fixas_set.issubset(s_jg):
            raise ValueError("Jogo nao contem todas as dezenas fixas exigidas.")

    fixas_jogo = fixas_ord if modo_fixas == "todos_os_jogos" else ()
    set_fixas_jogo = set(fixas_jogo)
    f_jogo = len(fixas_jogo)
    livres_jogo = [d for d in pool_ord if d not in set_fixas_jogo]

    w = dict(_PESOS_PADRAO_REF)
    if pesos is not None:
        w = {k: float(pesos[k]) for k in _PESOS_PADRAO_REF}
        if abs(sum(w.values()) - 1.0) > 1e-9 or any(val < 0 for val in w.values()):
            raise ValueError("Pesos invalidos na referencia independente.")

    j = len(jogos)
    tams = [len(jg) for jg in jogos]

    # 1. Cobertura combinatoria exata S_cov
    s_cov = 0.0
    ef2 = 1.0
    pares_cob = 0
    trincas_cob = 0
    for t in (1, 2, 3, 4):
        subs: Set[Tuple[int, ...]] = set()
        for jg in jogos:
            subs.update(itertools.combinations(jg, t))
        cob = len(subs)
        if t == 2:
            pares_cob = cob
        elif t == 3:
            trincas_cob = cob
        total_p = math.comb(p, t)
        c_fix = math.comb(f_jogo, t) if f_jogo >= t else 0
        teto = min(total_p, c_fix + sum(math.comb(m, t) - c_fix for m in tams))
        ef = min(1.0, cob / teto) if teto > 0 else 1.0
        if t == 2:
            ef2 = ef
        s_cov += _PESOS_COBERTURA_T[t] * ef
    s_cov = min(1.0, max(0.0, s_cov))

    # 2. Probabilidades e cotas
    p_ind = [prob_individual_ref(m) for m in tams]
    e_n_prem = sum(p_ind, Fraction(0, 1))
    p2_mat = [[Fraction(0, 1)] * j for _ in range(j)]
    inter_mat = [[0] * j for _ in range(j)]
    soma_p2 = Fraction(0, 1)
    soma_p2_max = Fraction(0, 1)
    soma_p2_min = Fraction(0, 1)
    soma_inter = 0
    soma_penal = 0.0
    i_max = 0
    s_i_min, i_min_medio = _cota_min_inter_ref(tams, p, f_jogo)
    s_i_max = 0

    if j > 1:
        pares_tot = j * (j - 1) // 2
        i_rac = Fraction(s_i_min, pares_tot)
        c_low = i_rac.numerator // i_rac.denominator
        c_high = c_low + (1 if i_rac > c_low else 0)
        frac_c = i_rac - c_low

        for i in range(j):
            mi = tams[i]
            for k in range(i + 1, j):
                mk = tams[k]
                c_max_par = min(mi, mk)
                s_i_max += c_max_par
                soma_p2_max += prob_par_quatro_regioes_ref(mi, mk, c_max_par)
                c_min_par = max(0, mi + mk - p, f_jogo)
                if mi == mk == _SORTEIO:
                    cl = max(c_min_par, min(c_max_par, c_low))
                    ch = max(c_min_par, min(c_max_par, c_high))
                    pl = prob_par_quatro_regioes_ref(mi, mk, cl)
                    ph = prob_par_quatro_regioes_ref(mi, mk, ch)
                    soma_p2_min += pl + frac_c * (ph - pl)
                else:
                    soma_p2_min += prob_par_quatro_regioes_ref(mi, mk, c_min_par)

                inter = len(sets[i] & sets[k])
                inter_mat[i][k] = inter_mat[k][i] = inter
                if inter > i_max:
                    i_max = inter
                soma_inter += inter
                p2_ik = prob_par_quatro_regioes_ref(mi, mk, inter)
                p2_mat[i][k] = p2_mat[k][i] = p2_ik
                soma_p2 += p2_ik
                pen = (max(0.0, inter - i_min_medio) / max(1.0, c_max_par - i_min_medio)) ** 2
                soma_penal += pen

    den_p2 = soma_p2_max - soma_p2_min
    s_prob = 1.0 if (j <= 1 or den_p2 <= 0) else min(1.0, max(0.0, float((soma_p2_max - soma_p2) / den_p2)))

    var_n_prem = sum((pi * (1 - pi) for pi in p_ind), Fraction(0, 1))
    for i in range(j):
        for k in range(i + 1, j):
            var_n_prem += 2 * (p2_mat[i][k] - p_ind[i] * p_ind[k])

    ds_low = _cota_ds_ref(j, p_ind, soma_p2)
    hw_high = p_ind[0] if j == 1 else min(Fraction(1, 1), e_n_prem - _mst_kruskal_ref(j, p2_mat))

    if j == 1:
        uniao_exata: Any = str(p_ind[0])
        uniao_exata_float: Optional[float] = float(p_ind[0])
    elif j == 2:
        ux = p_ind[0] + p_ind[1] - p2_mat[0][1]
        uniao_exata = str(ux)
        uniao_exata_float = float(ux)
    else:
        uniao_exata = "nao_calculada_diretamente"
        uniao_exata_float = None

    # 3. Diversificacao sobreposicao
    if j <= 1 or s_i_max <= s_i_min:
        s_div = 1.0
    else:
        ex_med = max(0.0, (soma_inter - s_i_min) / (s_i_max - s_i_min))
        e_pico = soma_penal / (j * (j - 1) // 2)
        s_div = min(1.0, max(0.0, 1.0 - (0.50 * ex_med + 0.50 * e_pico)))

    # 4. Distribuicao livres
    u_counts = {d: 0 for d in range(1, _UNIVERSO + 1)}
    for jg in jogos:
        for d in jg:
            u_counts[d] += 1
    mu_livre, ss_min, ss_max = _cota_var_livres_ref(tams, p, f_jogo)
    ss_obs = sum((u_counts[d] - mu_livre) ** 2 for d in livres_jogo)
    if not livres_jogo or ss_max <= ss_min + 1e-12:
        s_dist = 1.0
    else:
        s_dist = min(1.0, max(0.0, 1.0 - (ss_obs - ss_min) / (ss_max - ss_min)))

    # 5. Custo-beneficio
    comb_pagas = sum(math.comb(m, _SORTEIO) for m in tams)
    if comb_pagas <= 25_000:
        unicas_simples: Set[Tuple[int, ...]] = set()
        for jg in jogos:
            if len(jg) == _SORTEIO:
                unicas_simples.add(jg)
            else:
                unicas_simples.update(itertools.combinations(jg, _SORTEIO))
        n_unicas = len(unicas_simples)
    else:
        n_dist = len(set(jogos))
        n_unicas = comb_pagas if n_dist == j else n_dist
    taxa_unic = n_unicas / comb_pagas if comb_pagas > 0 else 1.0
    s_cb = min(1.0, max(0.0, 0.65 * taxa_unic + 0.35 * ef2))

    # 6. Diversidade estrutural 5x5
    sigs: Set[Tuple[int, int, int]] = set()
    linhas = [0] * 5
    colunas = [0] * 5
    for jg in jogos:
        pares = sum(1 for d in jg if d % 2 == 0)
        mold = sum(1 for d in jg if d in _MOLDURA_REF)
        soma_d = sum(jg)
        sigs.add((pares, mold, soma_d // 15))
        for d in jg:
            linhas[(d - 1) // 5] += 1
            colunas[(d - 1) % 5] += 1
    total_marcas = sum(tams)
    alvo_lc = total_marcas / 5.0
    desv_max = max(1.0, 2.0 * total_marcas * 0.8)
    desv_lc = sum(abs(v - alvo_lc) for v in linhas) + sum(abs(v - alvo_lc) for v in colunas)
    eq_lc = min(1.0, max(0.0, 1.0 - desv_lc / (2.0 * desv_max)))
    s_div_est = min(1.0, max(0.0, 0.60 * (len(sigs) / j) + 0.40 * eq_lc))

    f_val = (
        w["cobertura_combinatoria"] * s_cov
        + w["probabilidade_conjunta"] * s_prob
        + w["diversificacao_sobreposicao"] * s_div
        + w["distribuicao_dezenas"] * s_dist
        + w["custo_beneficio"] * s_cb
        + w["diversidade_estrutural"] * s_div_est
    )
    carteira_canonica = tuple(sorted(jogos))
    chave_desempate = (
        round(f_val, 12),
        round(s_cov, 12),
        round(s_prob, 12),
        -i_max,
        round(-ss_obs, 12),
        tuple(tuple(-d for d in jg) for jg in carteira_canonica),
    )

    custo_brl = _PRECO_SIMPLES * Decimal(comb_pagas)
    return {
        "versao_referencia": VERSAO_REFERENCIA_ETAPA4,
        "funcao_objetivo_F": f_val,
        "componentes": {
            "cobertura_combinatoria": s_cov,
            "probabilidade_conjunta": s_prob,
            "diversificacao_sobreposicao": s_div,
            "distribuicao_dezenas": s_dist,
            "custo_beneficio": s_cb,
            "diversidade_estrutural": s_div_est,
        },
        "distincao_seis_grandezas_probabilisticas": {
            "1_probabilidade_individual": [float(pi) for pi in p_ind],
            "2_probabilidade_pareada_max": max((float(p2_mat[i][k]) for i in range(j) for k in range(i + 1, j)), default=0.0),
            "3_esperanca_N_prem": float(e_n_prem),
            "3_variancia_N_prem": float(var_n_prem),
            "4_cota_inferior_dawson_sankoff": float(ds_low),
            "4_cota_superior_hunter_worsley": float(hw_high),
            "5_probabilidade_exata_uniao_frac": uniao_exata,
            "5_probabilidade_exata_uniao_float": uniao_exata_float,
            "6_nota_escopo_S_prob": "S_prob e metrica pareada normalizada de otimizacao, nao igual a P(U_i A_i) quando J >= 3.",
        },
        "metricas_combinatorias": {
            "pares_cobertos": pares_cob,
            "trincas_cobertas": trincas_cob,
            "intersecao_maxima": i_max,
            "ss_obs_livres": ss_obs,
            "combinacoes_simples_pagas": comb_pagas,
            "combinacoes_simples_unicas": n_unicas,
            "custo_total_brl": str(custo_brl),
        },
        "chave_desempate": chave_desempate,
        "clausula_obrigatoria": _CLAUSULA_CIENTIFICA,
    }


def auditar_conformidade_etapa4_ref(
    carteira: Iterable[Iterable[int]],
    pool: Optional[Iterable[int]] = None,
    fixas: Iterable[int] = (),
    bloqueadas: Iterable[int] = (),
    modo_fixas: str = "todos_os_jogos",
    tamanhos_esperados: Optional[Sequence[int]] = None,
    orcamento_max_brl: Optional[Decimal | str] = None,
) -> Dict[str, Any]:
    pool_ord = tuple(sorted(set(range(1, _UNIVERSO + 1) if pool is None else pool)))
    pool_set = set(pool_ord)
    fixas_set = set(fixas)
    bloq_set = set(bloqueadas)
    violacoes: List[str] = []

    if modo_fixas not in ("todos_os_jogos", "composicao_pool"):
        violacoes.append(f"modo_fixas invalido: {modo_fixas!r}")
    if not (_MIN_APOSTA <= len(pool_set) <= _UNIVERSO):
        violacoes.append(f"Tamanho do pool fora de [15..25]: {len(pool_set)}")
    if not fixas_set.issubset(pool_set):
        violacoes.append(f"Fixas fora do pool: {sorted(fixas_set - pool_set)}")
    if fixas_set & bloq_set:
        violacoes.append(f"Fixas e bloqueadas em conflito: {sorted(fixas_set & bloq_set)}")
    if pool_set & bloq_set:
        violacoes.append(f"Pool contem bloqueadas: {sorted(pool_set & bloq_set)}")

    jogos = [_validar_aposta_ref(jg) for jg in carteira]
    if not jogos:
        violacoes.append("Carteira vazia.")
    if len(set(jogos)) != len(jogos):
        violacoes.append("Carteira possui bilhetes duplicados.")
    for idx, jg in enumerate(jogos):
        s_jg = set(jg)
        if not s_jg.issubset(pool_set):
            violacoes.append(f"Jogo {idx} fora do pool.")
        if s_jg & bloq_set:
            violacoes.append(f"Jogo {idx} contem dezenas bloqueadas.")
        if modo_fixas == "todos_os_jogos" and not fixas_set.issubset(s_jg):
            violacoes.append(f"Jogo {idx} nao contem todas as fixas.")

    if tamanhos_esperados is not None and sorted(len(jg) for jg in jogos) != sorted(tamanhos_esperados):
        violacoes.append("Dimensoes dos bilhetes divergem das esperadas.")

    custo = sum((_PRECO_SIMPLES * Decimal(math.comb(len(jg), _SORTEIO)) for jg in jogos), Decimal("0.00"))
    if orcamento_max_brl is not None and custo > Decimal(str(orcamento_max_brl)):
        violacoes.append(f"Custo R$ {custo} excede orcamento R$ {orcamento_max_brl}")

    return {
        "conforme": len(violacoes) == 0,
        "violacoes": violacoes,
        "quantidade_jogos": len(jogos),
        "custo_total_brl": str(custo),
    }


def resolver_exato_etapa4_ref(
    pool: Iterable[int],
    fixas: Iterable[int],
    bloqueadas: Iterable[int],
    modo_fixas: str,
    tamanhos_jogos: Sequence[int],
    pesos: Optional[Mapping[str, float]] = None,
    limite_combinacoes: int = 8_000,
) -> Dict[str, Any]:
    """
    Solucionador exato independente por enumeracao canonica (suporta apostas
    simples, multiplas homogeneas e carteiras mistas dentro do limite).
    """
    pool_ord = tuple(sorted(set(pool)))
    fixas_ord = tuple(sorted(set(fixas)))
    bloq_set = set(bloqueadas)
    if set(pool_ord) & bloq_set or set(fixas_ord) & bloq_set or not set(fixas_ord).issubset(set(pool_ord)):
        raise ValueError("Restricoes de pool/fixas/bloqueadas inconsistentes.")

    fixas_jogo = fixas_ord if modo_fixas == "todos_os_jogos" else ()
    livres = [d for d in pool_ord if d not in set(fixas_jogo)]
    espaco = contar_espaco_admissivel_ref(tamanhos_jogos, len(pool_ord), len(fixas_jogo))
    if espaco <= 0 or espaco > limite_combinacoes:
        raise ValueError(f"Espaco admissivel ({espaco}) inviavel ou excede limite ({limite_combinacoes}).")

    contagem: Dict[int, int] = {}
    for m in tamanhos_jogos:
        contagem[m] = contagem.get(m, 0) + 1

    grupos_combinacoes = []
    for m in sorted(contagem):
        qtd = contagem[m]
        cands_m = [tuple(sorted((*fixas_jogo, *c))) for c in itertools.combinations(livres, m - len(fixas_jogo))]
        grupos_combinacoes.append(itertools.combinations(cands_m, qtd))

    melhor_chave: Optional[Tuple[Any, ...]] = None
    melhor_av: Optional[Dict[str, Any]] = None
    melhor_carteira: Optional[Tuple[Tuple[int, ...], ...]] = None
    avaliacoes = 0

    for prod in itertools.product(*grupos_combinacoes):
        cart = tuple(sorted(jg for grp in prod for jg in grp))
        av = avaliar_carteira_ref_etapa4(
            cart, pool=pool_ord, fixas=fixas_ord, bloqueadas=bloqueadas, modo_fixas=modo_fixas, pesos=pesos
        )
        avaliacoes += 1
        if melhor_chave is None or av["chave_desempate"] > melhor_chave:
            melhor_chave = av["chave_desempate"]
            melhor_av = av
            melhor_carteira = cart

    if melhor_av is None or melhor_carteira is None:
        raise RuntimeError("Falha inesperada na enumeracao exata: nenhuma carteira admissivel gerada.")
    return {
        "otimo_global_comprovado": True,
        "espaco_enumerado": avaliacoes,
        "carteira_otima": [list(jg) for jg in melhor_carteira],
        "funcao_objetivo_F": melhor_av["funcao_objetivo_F"],
        "avaliacao_referencia": melhor_av,
    }


def verificar_equivalencia_etapa4_contra_referencia(
    resultado_etapa4: Mapping[str, Any],
    tolerancia: float = 1e-12,
) -> Dict[str, Any]:
    """
    Confere conformidade estrutural, igualdade matematica em <= 1e-12 de F(C) e
    componentes, integridade da telemetria e ausencia de historico na Etapa 4.
    """
    req = resultado_etapa4["especificacao"]
    cart = resultado_etapa4["carteira"]
    conf = auditar_conformidade_etapa4_ref(
        carteira=cart,
        pool=req["pool"],
        fixas=req["fixas"],
        bloqueadas=req["bloqueadas"],
        modo_fixas=req["modo_fixas"],
        tamanhos_esperados=req["tamanhos_jogos"],
        orcamento_max_brl=req["custo_total_brl"],
    )
    av_ref = avaliar_carteira_ref_etapa4(
        carteira=cart,
        pool=req["pool"],
        fixas=req["fixas"],
        bloqueadas=req["bloqueadas"],
        modo_fixas=req["modo_fixas"],
        pesos=req["pesos"],
    )

    f_est = float(resultado_etapa4["funcao_objetivo_F"])
    f_ref = float(av_ref["funcao_objetivo_F"])
    dif_f = abs(f_est - f_ref)

    difs_comp: Dict[str, float] = {}
    for k, v_ref in av_ref["componentes"].items():
        difs_comp[k] = abs(float(resultado_etapa4["componentes"][k]) - float(v_ref))

    dif_max_comp = max(difs_comp.values()) if difs_comp else 0.0
    equiv = (
        conf["conforme"]
        and dif_f <= tolerancia
        and dif_max_comp <= tolerancia
        and resultado_etapa4.get("historico_utilizado") is None
    )
    return {
        "conforme": conf["conforme"],
        "violacoes": conf["violacoes"],
        "equivalente_1e_12": equiv,
        "diferenca_F": dif_f,
        "diferenca_max_componente": dif_max_comp,
        "diferencas_componentes": difs_comp,
        "funcao_objetivo_F_etapa4": f_est,
        "funcao_objetivo_F_referencia": f_ref,
        "avaliacao_referencia": av_ref,
    }
