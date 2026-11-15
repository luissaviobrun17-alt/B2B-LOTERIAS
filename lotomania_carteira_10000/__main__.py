# -*- coding: utf-8 -*-
"""
Executor CLI do modulo isolado `lotomania_carteira_10000`.
"""

import argparse
import hashlib
import json
import os
import sys
from typing import Any, Dict

DIR_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if DIR_RAIZ not in sys.path:
    sys.path.insert(0, DIR_RAIZ)

from lotomania_carteira_10000.auditoria import auditar_carteira_completa
from lotomania_carteira_10000.otimizador_swap import gerar_carteira_10000_otimizada
from lotomania_carteira_10000.validacao import (
    BASELINE_ORDEM4_10000_REFERENCIA,
    CLAUSULA_OBRIGATORIA,
    VERSAO_ALGORITMO,
    exigir,
)


def executar_benchmark_ordem6_passo1(
    *,
    dir_saida: str,
    seed: int = 330001,
    J: int = 10000,
    max_tentativas: int = 1080000,
    passo_checkpoint: int = 60000,
) -> Dict[str, Any]:
    """
    Executa a geracao completa J=10.000 com checkpoints 60k, trilha JSONL,
    auditoria independente R1-R12 e comparativo contra o baseline Ordem 4.
    """
    os.makedirs(dir_saida, exist_ok=True)
    caminho_trilha = os.path.join(
        dir_saida, f"trilha_swaps_{J}_seed{seed}.jsonl"
    )
    caminho_carteira = os.path.join(
        dir_saida, f"carteira_{J}_seed{seed}.json"
    )
    caminho_relatorio = os.path.join(
        dir_saida, f"benchmark_{J}_seed{seed}.json"
    )

    rel_exec = gerar_carteira_10000_otimizada(
        seed=seed,
        J=J,
        max_tentativas_f3=max_tentativas,
        passo_checkpoint=passo_checkpoint,
        auditar_100pct_swaps=True,
        auditar_intersecoes_bruto=False,
        incluir_jogos_no_retorno=True,
        caminho_trilha_jsonl=caminho_trilha,
        caminho_carteira_saida=caminho_carteira,
        caminho_relatorio_saida=caminho_relatorio,
    )
    jogos = rel_exec["jogos"]
    aud_indep = auditar_carteira_completa(
        jogos,
        teto_kmax=35,
        baseline_ordem4=BASELINE_ORDEM4_10000_REFERENCIA if J == 10000 else None,
    )
    exigir(
        aud_indep["aprovacao_restricoes"]["todas_travas_aprovadas"],
        "Auditoria independente detectou falha nas travas R1-R12",
    )

    caminho_auditoria = os.path.join(
        dir_saida, f"auditoria_independente_{J}_seed{seed}.json"
    )
    with open(caminho_auditoria, "w", encoding="utf-8") as fa:
        json.dump(aud_indep, fa, indent=2)

    with open(caminho_auditoria, "rb") as fa:
        sha_auditoria = hashlib.sha256(fa.read()).hexdigest()

    dossie = {
        "versao_algoritmo": VERSAO_ALGORITMO,
        "clausula_obrigatoria": CLAUSULA_OBRIGATORIA,
        "seed": seed,
        "J": J,
        "max_tentativas_f3": max_tentativas,
        "tempo_fase12_s": rel_exec["tempo_fase12_s"],
        "tempo_fase3_s": rel_exec["tempo_fase3_s"],
        "tempo_total_s": rel_exec["tempo_total_s"],
        "swaps_aceitos": rel_exec["swaps_aceitos"],
        "recalculos_dmax_queda": rel_exec["recalculos_dmax_queda"],
        "pre_fase3": rel_exec["pre_fase3"],
        "pos_fase3": rel_exec["pos_fase3"],
        "homologacao_kmax": rel_exec["homologacao_kmax"],
        "checkpoints_60k": rel_exec["checkpoints_60k"],
        "auditoria_restricoes": rel_exec["auditoria_restricoes"],
        "aprovacao_auditoria_independente": aud_indep["aprovacao_restricoes"],
        "comparacao_baseline_ordem4": aud_indep.get("comparacao_baseline_ordem4"),
        "cobertura_por_faixa": aud_indep["cobertura_por_faixa"],
        "sha256_auditoria_independente": sha_auditoria,
    }
    with open(caminho_relatorio, "w", encoding="utf-8") as fr:
        json.dump(dossie, fr, indent=2)
    return dossie


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Modulo isolado lotomania_carteira_10000 (Ordem 5-R3 + S1 1.080k)"
    )
    parser.add_argument("--seed", type=int, default=330001)
    parser.add_argument("--J", type=int, default=10000)
    parser.add_argument("--max-tentativas", type=int, default=1080000)
    parser.add_argument("--passo-checkpoint", type=int, default=60000)
    parser.add_argument("--dir-saida", type=str, default="auditoria/lotomania_carteira_10000")
    args = parser.parse_args()

    res = executar_benchmark_ordem6_passo1(
        dir_saida=args.dir_saida,
        seed=args.seed,
        J=args.J,
        max_tentativas=args.max_tentativas,
        passo_checkpoint=args.passo_checkpoint,
    )
    pos = res["pos_fase3"]
    print(
        f"CONCLUIDO J={res['J']} seed={res['seed']} swaps={res['swaps_aceitos']} "
        f"phi2={pos['phi2']} Q+={pos['q_global_plus']} Dmax={pos['d_max']} "
        f"kmax={pos['k_max']} P>25={pos['P_gt_25']} Rwin={pos['R_win']} "
        f"sha256={res['auditoria_restricoes']['sha256_carteira']}"
    )


if __name__ == "__main__":
    main()
