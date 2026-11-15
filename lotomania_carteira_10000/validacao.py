# -*- coding: utf-8 -*-
"""
Constantes matematicas, tabelas hipergeometricas e validadores estritos (Ordem 5-R3)
para a carteira otimizada de ate 10.000 jogos da Lotomania.

Implementado com zero instrucoes `assert` (100% compativel com `python` e `python -O`).
"""

import hashlib
import json
import math
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

VERSAO_ALGORITMO = "ordem5-r3-s1-1080k-v1.0"
ESTRATEGIA_FASE3_PADRAO = "S1_atual_top8"

CLAUSULA_OBRIGATORIA = (
    "O sistema não prevê resultados futuros nem altera a probabilidade matemática "
    "individual de premiação de qualquer bilhete. Seu objetivo é otimizar a "
    "distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a "
    "redundância entre eventos premiados e melhorar a cobertura conjunta observada."
)

PARAMETROS_PADRAO: Dict[str, Any] = {
    "seed": 330001,
    "J": 10000,
    "max_tentativas_f3": 1080000,
    "tau_primario": 35,
    "alpha_25": 30.0,
    "alpha_win": 1.0,
    "alpha_1": 0.08,
    "alpha_2": 0.25,
    "gamma_plus": 0.02,
    "batch0": 80,
    "estrategia_fase3": ESTRATEGIA_FASE3_PADRAO,
}

BLOCOS: Tuple[Tuple[int, ...], ...] = tuple(
    tuple(range(20 * r + 1, 20 * (r + 1) + 1)) for r in range(5)
)
BLOCK_OF: Tuple[int, ...] = (0,) + tuple((n - 1) // 20 for n in range(1, 101))
FAIXAS_PREMIACAO: Tuple[int, ...] = (0, 15, 16, 17, 18, 19, 20)
FAIXAS_PREMIACAO_RELATORIO: Tuple[int, ...] = (20, 19, 18, 17, 16, 15, 0)
MASK_80: int = (1 << 80) - 1

BASELINE_ORDEM4_10000_REFERENCIA: Dict[str, Any] = {
    "identificacao": "MotorLotomaniaModo4 v1.2 (seed=330001, J=10000)",
    "seed": 330001,
    "J": 10000,
    "tempo_geracao_s": 216.494,
    "k_min": 11,
    "k_max": 39,
    "P_gt_25": 161467468,
    "R_win": "3510697068640806703944584",
    "sigma_intra": 83.9,
    "sigma_inter": 58.84,
    "u_min": 4984,
    "u_max": 5012,
    "amplitude_u": 28,
    "pares_k_ge_32": 238632,
    "pares_k_ge_35": 3626,
    "pares_k_ge_36": 629,
    "pares_k_ge_37": 98,
    "pares_k_ge_38": 5,
    "k_eq_35": 2997,
    "k_eq_36": 531,
    "k_eq_37": 93,
    "k_eq_38": 4,
    "k_eq_39": 1,
}


def exigir(condicao: bool, mensagem: str) -> None:
    """Garante invariante em tempo de execucao inclusive sob `python -O`."""
    if condicao is not True:
        raise RuntimeError(mensagem)


def _comb_segura(n: int, k: int) -> int:
    return math.comb(n, k) if 0 <= k <= n else 0


def calcular_n2_celula(k: int, t1: int, t2: int) -> int:
    """
    Calcula exatamente N_2(k; t1, t2) = numero de sorteios de 20 dezenas em U=100
    que produzem t1 acertos no bilhete G1 e t2 acertos no bilhete G2 com |G1 cap G2| = k.
    """
    tot = 0
    min_x = max(0, t1 - (50 - k), t2 - (50 - k), t1 + t2 - 20)
    max_x = min(k, t1, t2, 20, k - 20 + t1 + t2)
    if min_x <= max_x:
        for x11 in range(min_x, max_x + 1):
            tot += (
                _comb_segura(k, x11)
                * _comb_segura(50 - k, t1 - x11)
                * _comb_segura(50 - k, t2 - x11)
                * _comb_segura(k, 20 - t1 - t2 + x11)
            )
    return tot


def gerar_tabelas_hipergeometricas() -> Tuple[
    Dict[int, Tuple[int, ...]],
    Dict[int, Dict[Tuple[int, int], int]],
    Tuple[int, ...],
    Tuple[int, ...],
]:
    """Gera tabelas exatas N_2(k; t1, t2), R_win(k) e tabela combinada SWAR."""
    tabela_faixas_mut: Dict[int, List[int]] = {t: [0] * 51 for t in FAIXAS_PREMIACAO}
    tabela_bivariada: Dict[int, Dict[Tuple[int, int], int]] = {}
    tabela_win_mut: List[int] = [0] * 51

    for k in range(51):
        celulas_k: Dict[Tuple[int, int], int] = {}
        soma_k = 0
        for t1 in FAIXAS_PREMIACAO:
            for t2 in FAIXAS_PREMIACAO:
                tot = calcular_n2_celula(k, t1, t2)
                celulas_k[(t1, t2)] = tot
                if t1 == t2:
                    tabela_faixas_mut[t1][k] = tot
                soma_k += tot
        tabela_bivariada[k] = celulas_k
        tabela_win_mut[k] = soma_k

    tabela_faixas = {t: tuple(vals) for t, vals in tabela_faixas_mut.items()}
    tabela_win = tuple(tabela_win_mut)
    tabela_combinada = tuple(
        ((max(0, k - 25) ** 2) << 80) | tabela_win[k] for k in range(51)
    )
    return tabela_faixas, tabela_bivariada, tabela_win, tabela_combinada


(
    TABELA_OVERLAP_FAIXAS,
    TABELA_OVERLAP_BIVARIADA,
    TABELA_OVERLAP_PREMIADOS,
    TABELA_COMBINADA,
) = gerar_tabelas_hipergeometricas()


def validar_entrada_carteira(
    J: Any,
    seed: Any = 330001,
    max_tentativas_f3: Any = 1080000,
    tau_primario: Any = 35,
) -> None:
    """Valida estritamente tipos e limites dos parametros de entrada."""
    if type(J) is not int:
        raise TypeError(f"J deve ser int exato (recebido {type(J).__name__}).")
    if J < 2 or J > 10000 or J % 2 != 0:
        raise ValueError(f"J deve ser par entre 2 e 10000 (recebido {J}).")
    if type(seed) is not int:
        raise TypeError(f"seed deve ser int exato (recebido {type(seed).__name__}).")
    if type(max_tentativas_f3) is not int:
        raise TypeError(
            f"max_tentativas_f3 deve ser int exato (recebido {type(max_tentativas_f3).__name__})."
        )
    if max_tentativas_f3 < 0:
        raise ValueError(
            f"max_tentativas_f3 deve ser nao negativo (recebido {max_tentativas_f3})."
        )
    if type(tau_primario) is not int:
        raise TypeError(
            f"tau_primario deve ser int exato (recebido {type(tau_primario).__name__})."
        )
    if tau_primario < 25 or tau_primario > 50:
        raise ValueError(
            f"tau_primario deve estar em [25, 50] (recebido {tau_primario})."
        )


def validar_bilhete_individual(bilhete: Any) -> Tuple[bool, Dict[str, Any]]:
    """
    Valida estritamente R1-R9 de forma defensiva e em curto-circuito antes de usar `set(...)`.
    Retorna `(True/False, diagnostico)` sem lancar `TypeError` em entradas invalidas.
    """
    if not isinstance(bilhete, (list, tuple)):
        return False, {
            "ok": False,
            "violacoes": ["R1_tipo_sequencia"],
            "detalhe": f"Tipo invalido: {type(bilhete).__name__}",
        }
    if len(bilhete) != 50:
        return False, {
            "ok": False,
            "violacoes": ["R1_tamanho_diferente_de_50"],
            "tamanho": len(bilhete),
        }
    for pos, n in enumerate(bilhete):
        if type(n) is not int or n < 1 or n > 100:
            return False, {
                "ok": False,
                "violacoes": ["R1_elemento_fora_do_dominio_int_1_100"],
                "indice": pos,
                "tipo_elemento": type(n).__name__,
            }
    if len(set(bilhete)) != 50:
        return False, {
            "ok": False,
            "violacoes": ["R2_dezenas_duplicadas_internas"],
        }

    s = sorted(bilhete)
    pares = 0
    soma = 0
    cols = [0] * 10
    lins = [0] * 10
    consec = 1
    max_consec = 1
    prev = -10

    for x in s:
        if (x & 1) == 0:
            pares += 1
        soma += x
        cols[(x - 1) % 10] += 1
        lins[(x - 1) // 10] += 1
        if x == prev + 1:
            consec += 1
            if consec > max_consec:
                max_consec = consec
        else:
            consec = 1
        prev = x

    blocos_cnt = [lins[2 * r] + lins[2 * r + 1] for r in range(5)]
    violacoes: List[str] = []
    if any(b != 10 for b in blocos_cnt):
        violacoes.append("R4_blocos_10_10_10_10_10")
    if max_consec > 4:
        violacoes.append("R5_consecutivos_max_4")
    if min(cols) < 3 or max(cols) > 7:
        violacoes.append("R6_colunas_3_a_7")
    if min(lins) < 2 or max(lins) > 8:
        violacoes.append("R7_linhas_2_a_8")
    if pares < 18 or pares > 32:
        violacoes.append("R8_paridade_18_a_32")
    if soma < 2350 or soma > 2700:
        violacoes.append("R9_soma_2350_a_2700")

    return len(violacoes) == 0, {
        "ok": len(violacoes) == 0,
        "violacoes": violacoes,
        "pares": pares,
        "soma": soma,
        "max_consec": max_consec,
        "blocos": blocos_cnt,
        "min_col": min(cols),
        "max_col": max(cols),
        "min_lin": min(lins),
        "max_lin": max(lins),
    }


def validar_r1_r9_rapido(jg_sorted: Sequence[int]) -> bool:
    """Verificacao rapida R1-R9 para sequencia ja validada em int[1..100] ordenada."""
    if len(jg_sorted) != 50:
        return False
    pares = sum(1 for x in jg_sorted if (x & 1) == 0)
    if pares < 18 or pares > 32:
        return False
    soma = sum(jg_sorted)
    if soma < 2350 or soma > 2700:
        return False
    cols = [0] * 10
    lins = [0] * 10
    consec = 1
    prev = -10
    for x in jg_sorted:
        cols[(x - 1) % 10] += 1
        lins[(x - 1) // 10] += 1
        if x == prev + 1:
            consec += 1
            if consec > 4:
                return False
        else:
            consec = 1
        prev = x
    if min(cols) < 3 or max(cols) > 7:
        return False
    if min(lins) < 2 or max(lins) > 8:
        return False
    for r in range(5):
        if lins[2 * r] + lins[2 * r + 1] != 10:
            return False
    return True


def classificar_homologacao_kmax(k_max: int) -> Dict[str, Any]:
    """Classifica o status normativo conforme teto maximo de intersecao k_max."""
    if type(k_max) is not int:
        raise TypeError(f"k_max deve ser int exato (recebido {type(k_max).__name__}).")
    if k_max <= 35:
        return {
            "k_max": k_max,
            "status": "APROVADO",
            "meta_kmax_35_atingida": True,
            "ressalva_contingencia": False,
        }
    if k_max == 36:
        return {
            "k_max": k_max,
            "status": "INCONCLUSIVO / RESSALVA DE CONTINGÊNCIA",
            "meta_kmax_35_atingida": False,
            "ressalva_contingencia": True,
        }
    return {
        "k_max": k_max,
        "status": "REPROVADO",
        "meta_kmax_35_atingida": False,
        "ressalva_contingencia": False,
    }


def sha256_matriz_incidencia_canonica(jogos_selecionados: Sequence[Sequence[int]]) -> str:
    """Hash SHA-256 canonico da matriz binaria J x 100 em ordem linha por coluna."""
    h = hashlib.sha256()
    for jg in jogos_selecionados:
        linha = bytearray(100)
        for n in jg:
            linha[n - 1] = 1
        h.update(linha)
    return h.hexdigest()


def calcular_hashes_certificados(
    jogos_selecionados: Sequence[Sequence[int]],
    *,
    seed: int,
    J: int,
    max_tentativas_f3: int,
    versao_algoritmo: str = VERSAO_ALGORITMO,
) -> Dict[str, str]:
    """Gera hashes criptograficos v1 (carteira) e v2 (canonico com metadados)."""
    payload_v1 = json.dumps(jogos_selecionados, separators=(",", ":")).encode("utf-8")
    hash_v1 = hashlib.sha256(payload_v1).hexdigest()

    payload_v2 = json.dumps(
        {
            "versao_algoritmo": versao_algoritmo,
            "seed": seed,
            "J": J,
            "max_tentativas_f3": max_tentativas_f3,
            "jogos": jogos_selecionados,
        },
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    hash_v2 = hashlib.sha256(payload_v2).hexdigest()

    estado_canonico = bytearray(n for jg in jogos_selecionados for n in jg)
    sha_estado = hashlib.sha256(estado_canonico).hexdigest()
    sha_matriz = sha256_matriz_incidencia_canonica(jogos_selecionados)
    return {
        "sha256_carteira": hash_v1,
        "hash_carteira_sha256_v1": hash_v1,
        "hash_carteira_sha256_v2_canonico": hash_v2,
        "sha256_estado_canonico": sha_estado,
        "sha256_matriz_incidencia_100": sha_matriz,
    }


def validar_trilha_jsonl_em_disco(
    caminho_jsonl: str,
    sha_inicial_esperado: str,
    sha_final_esperado: str,
    swaps_esperados: int,
) -> int:
    """Valida cadeia SHA-256, monotonicidade e R1-R12 da trilha JSONL em disco."""
    cnt = 0
    sha_chain = sha_inicial_esperado
    with open(caminho_jsonl, "r", encoding="utf-8") as f:
        for idx, line in enumerate(f):
            rec = json.loads(line)
            exigir(rec["swap_idx"] == idx, f"swap_idx divergente na linha {idx}")
            exigir(
                rec["sha256_estado_antes"] == sha_chain,
                f"Quebra da cadeia SHA-256 antes do swap {idx}",
            )
            exigir(rec["delta_phi2"] <= 0, f"delta_phi2 > 0 no swap {idx}")
            exigir(rec["delta_q_plus"] <= 0, f"delta_q_plus > 0 no swap {idx}")
            exigir(rec["d_max_depois"] <= rec["d_max_antes"], f"D_max subiu no swap {idx}")
            exigir(rec["p25_depois"] <= rec["p25_antes"], f"P_gt_25 subiu no swap {idx}")
            exigir(
                int(rec["rwin_depois"]) <= int(rec["rwin_antes"]),
                f"R_win subiu no swap {idx}",
            )
            exigir(
                bool(rec["r1_r10_ok"]) and bool(rec["r11_ok"]) and bool(rec["r12_ok"]),
                f"Trava R1-R12 violada na trilha swap {idx}",
            )
            sha_chain = rec["sha256_estado_depois"]
            cnt += 1
    exigir(
        cnt == swaps_esperados,
        f"Trilha JSONL com {cnt} swaps vs esperado {swaps_esperados}",
    )
    exigir(
        sha_chain == sha_final_esperado,
        "Hash final da trilha JSONL diverge do estado canonico final",
    )
    return cnt
