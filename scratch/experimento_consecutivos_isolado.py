# -*- coding: utf-8 -*-
"""
AVALIAÇÃO EXPERIMENTAL ISOLADA: CONTENÇÃO DE SEQUÊNCIAS CONSECUTIVAS
===================================================================
Estudo comparativo rigoroso e pareado entre três cenários:
  - Baseline: gerador atual oficial sem filtro (J=1.000, B=32, semente 2027)
  - Experimento A: contenção com limite máximo de 5 dezenas consecutivas
  - Experimento B: contenção com limite máximo de 6 dezenas consecutivas

Salvaguardas de governança:
  - Rastreabilidade total com registro de hash SHA-256 do próprio script.
  - Execução unificada em ambiente isolado (scratch), sem tocar arquivos de produção.
  - Zero commits e zero push.
"""

from __future__ import annotations

import hashlib
import json
import math
import os
import random
import sys
import time
import tracemalloc
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

CAMINHO_SCRIPT_ATUAL = Path(__file__).resolve()
CAMINHO_REPO = r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS"
if CAMINHO_REPO not in sys.path:
    sys.path.insert(0, CAMINHO_REPO)

from lotofacil_modo4.etapa1_regras_oficiais import UNIVERSO_TOTAL, TAMANHO_SORTEIO
from lotofacil_modo4.etapa2_funcao_objetivo import avaliar_carteira_etapa2, PERFIS_PESOS_ETAPA2
from lotofacil_modo4.etapa2_referencia_independente import avaliar_carteira_referencia_independente
from lotofacil_modo4.etapa4_arquitetura_adaptativa import (
    AvaliadorConstrutivoIncrementalEtapa4,
    MotorIncrementalOtimizadoEtapa4,
    _gerar_jogo_aleatorio_valido,
)

def calcular_hash_arquivo(caminho: Path) -> str:
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()

def calcular_maior_sequencia(jogo: Sequence[int]) -> int:
    """Calcula o comprimento da maior sequência de números consecutivos no jogo ordenado."""
    max_seq = 1
    atual = 1
    for i in range(len(jogo) - 1):
        if jogo[i + 1] == jogo[i] + 1:
            atual += 1
            if atual > max_seq:
                max_seq = atual
        else:
            atual = 1
    return max_seq

def executar_gerador_paramétrico(
    spec: Mapping[str, Any],
    semente: int,
    max_avaliacoes: int,
    teto_consecutivos: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Executa a construção gulosa sob parâmetros idênticos aos da Fase 1/Fase 2,
    aplicando opcionalmente o teto de dezenas consecutivas durante a amostragem.
    """
    rng = random.Random(semente)
    av = AvaliadorConstrutivoIncrementalEtapa4(spec)
    tams = spec["tamanhos_jogos"]
    j = spec["quantidade_jogos"]
    livres = spec["livres_para_jogos"]
    fixas_j = spec["fixas_por_jogo"]
    cand_por_passo = max(2, max_avaliacoes // max(1, j))

    avaliacoes_efetivas = 0
    usados: Set[Tuple[int, ...]] = set()
    total_tentativas_candidatos = 0
    candidatos_rejeitados_filtro = 0
    candidatos_admitidos = 0
    passos_cota_incompleta = 0

    tracemalloc.start()
    t0 = time.perf_counter()

    for idx_j, m_i in enumerate(tams):
        faltam = m_i - len(fixas_j)
        restantes_av = max(1, max_avaliacoes - avaliacoes_efetivas)
        limite_cands = min(cand_por_passo, restantes_av) if idx_j < j - 1 else restantes_av
        if idx_j == 0 and teto_consecutivos is None:
            limite_cands = min(limite_cands, 16)

        cands: List[Tuple[int, ...]] = []
        vistos: Set[Tuple[int, ...]] = set()

        if faltam == 0:
            cands.append(fixas_j)
            candidatos_admitidos += 1
        else:
            # Candidato determinístico inicial se admissível
            ord_menos = sorted(livres, key=lambda d: (av.u_counts[d], d))
            cg0 = tuple(sorted((*fixas_j, *ord_menos[:faltam])))
            total_tentativas_candidatos += 1
            if teto_consecutivos is None or calcular_maior_sequencia(cg0) <= teto_consecutivos:
                if cg0 not in usados:
                    vistos.add(cg0)
                    cands.append(cg0)
                    candidatos_admitidos += 1
            else:
                candidatos_rejeitados_filtro += 1

            if len(ord_menos) > faltam and len(cands) < limite_cands:
                desloc = max(1, len(ord_menos) // 4)
                rot = ord_menos[desloc:] + ord_menos[:desloc]
                cg1 = tuple(sorted((*fixas_j, *rot[:faltam])))
                total_tentativas_candidatos += 1
                if teto_consecutivos is None or calcular_maior_sequencia(cg1) <= teto_consecutivos:
                    if cg1 not in usados and cg1 not in vistos:
                        vistos.add(cg1)
                        cands.append(cg1)
                        candidatos_admitidos += 1
                else:
                    candidatos_rejeitados_filtro += 1

            # Amostragem ponderada pelo inverso da frequência de uso
            pesos_amostra = [1.0 / (1.0 + av.u_counts[d]) for d in livres]
            tent = 0
            max_tent = max(limite_cands * (15 if teto_consecutivos is not None else 6), 30)

            while len(cands) < limite_cands and tent < max_tent:
                tent += 1
                total_tentativas_candidatos += 1
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
                    if teto_consecutivos is None or calcular_maior_sequencia(cg) <= teto_consecutivos:
                        vistos.add(cg)
                        cands.append(cg)
                        candidatos_admitidos += 1
                    else:
                        candidatos_rejeitados_filtro += 1

        # Fallback robusto se cota não preenchida
        if not cands:
            for _ in range(200):
                total_tentativas_candidatos += 1
                cg = _gerar_jogo_aleatorio_valido(rng, livres, fixas_j, m_i)
                if cg not in usados:
                    if teto_consecutivos is None or calcular_maior_sequencia(cg) <= teto_consecutivos:
                        cands.append(cg)
                        candidatos_admitidos += 1
                        break
                    else:
                        candidatos_rejeitados_filtro += 1
            if not cands:
                for _ in range(100):
                    total_tentativas_candidatos += 1
                    cg = _gerar_jogo_aleatorio_valido(rng, livres, fixas_j, m_i)
                    if cg not in usados:
                        cands.append(cg)
                        candidatos_admitidos += 1
                        break

        if len(cands) < limite_cands:
            passos_cota_incompleta += 1

        escolhido = cands[0]
        melhor_f = -1.0
        if len(cands) > 1:
            for cg in cands:
                f_p = av.simular_adicao_jogo(cg)
                avaliacoes_efetivas += 1
                if f_p > melhor_f + 1e-12 or (abs(f_p - melhor_f) <= 1e-12 and cg < escolhido):
                    melhor_f = f_p
                    escolhido = cg
        else:
            avaliacoes_efetivas += 1

        av.adicionar_jogo(escolhido)
        usados.add(escolhido)

    t1 = time.perf_counter()
    _, pico_mem = tracemalloc.get_traced_memory()
    tracemalloc.stop()

    tempo_total = t1 - t0
    memoria_mb = pico_mem / (1024 * 1024)

    carteira_gerada = list(av.jogos)
    qtd_unicos = len(set(carteira_gerada))

    # 1. Tripla Validação Matemática
    motor = MotorIncrementalOtimizadoEtapa4(carteira_gerada, spec["pool"], spec["fixas_por_jogo"], spec["pesos"])
    f_e4 = motor.score_atual()
    ev_e2 = avaliar_carteira_etapa2(carteira_gerada)
    f_e2 = float(ev_e2["funcao_objetivo_F"])
    ev_ref = avaliar_carteira_referencia_independente(carteira_gerada)
    f_ref = float(ev_ref["funcao_objetivo_F"])

    div_e4_e2 = abs(f_e4 - f_e2)
    div_e4_ref = abs(f_e4 - f_ref)

    # 2. Coberturas combinatórias t=1..4 e frequências
    t1_set: Set[int] = set()
    t2_set: Set[Tuple[int, int]] = set()
    t3_set: Set[Tuple[int, int, int]] = set()
    t4_set: Set[Tuple[int, int, int, int]] = set()
    freq_dezenas = Counter()

    for jg in carteira_gerada:
        freq_dezenas.update(jg)
        t1_set.update(jg)
        n = len(jg)
        for i in range(n):
            for k in range(i + 1, n):
                t2_set.add((jg[i], jg[k]))
                for l in range(k + 1, n):
                    t3_set.add((jg[i], jg[k], jg[l]))
                    for m in range(l + 1, n):
                        t4_set.add((jg[i], jg[k], jg[l], jg[m]))

    mu = (15.0 * j) / len(spec["pool"])
    ss_obs = sum((freq_dezenas[d] - mu) ** 2 for d in spec["pool"])

    # 3. Interseções entre todos os pares
    total_pares = j * (j - 1) // 2
    hist_inter = Counter()
    for i in range(j):
        s_i = set(carteira_gerada[i])
        for k in range(i + 1, j):
            c = len(s_i & set(carteira_gerada[k]))
            hist_inter[c] += 1

    # 4. Sequências consecutivas
    seqs = [calcular_maior_sequencia(jg) for jg in carteira_gerada]
    dist_seqs = Counter(seqs)

    taxa_rejeicao = (candidatos_rejeitados_filtro / total_tentativas_candidatos * 100.0) if total_tentativas_candidatos > 0 else 0.0

    return {
        "cenario": "Baseline (Sem Filtro)" if teto_consecutivos is None else f"Limite {teto_consecutivos}",
        "teto_consecutivos": teto_consecutivos,
        "jogos_unicos": qtd_unicos,
        "unicidade_pct": (qtd_unicos / j) * 100.0,
        "tempo_segundos": tempo_total,
        "memoria_pico_mb": memoria_mb,
        "avaliacoes_efetivas": avaliacoes_efetivas,
        "total_tentativas_candidatos": total_tentativas_candidatos,
        "candidatos_rejeitados_filtro": candidatos_rejeitados_filtro,
        "candidatos_admitidos": candidatos_admitidos,
        "passos_cota_incompleta": passos_cota_incompleta,
        "taxa_rejeicao_pct": taxa_rejeicao,
        "funcao_objetivo_F": f_e4,
        "tripla_validacao": {
            "f_e4": f_e4,
            "f_e2": f_e2,
            "f_ref": f_ref,
            "div_e4_e2": div_e4_e2,
            "div_e4_ref": div_e4_ref,
            "aprovado_1e12": (div_e4_e2 <= 1e-12 and div_e4_ref <= 1e-12),
        },
        "componentes": {
            "S_cov": float(ev_e2["componentes"].get("cobertura_combinatoria", 0.0)),
            "S_prob": float(ev_e2["componentes"].get("probabilidade_conjunta", 0.0)),
            "S_div": float(ev_e2["componentes"].get("diversificacao_sobreposicao", 0.0)),
            "S_dist": float(ev_e2["componentes"].get("distribuicao_dezenas", 0.0)),
            "S_cb": float(ev_e2["componentes"].get("custo_beneficio", 0.0)),
            "S_est": float(ev_e2["componentes"].get("diversidade_estrutural", 0.0)),
        },
        "cobertura": {
            "t1": len(t1_set),
            "t2": len(t2_set),
            "t3": len(t3_set),
            "t4": len(t4_set),
            "t4_pct": len(t4_set) / 12650.0 * 100.0,
        },
        "frequencia_dezenas": {
            "min": min(freq_dezenas.values()),
            "max": max(freq_dezenas.values()),
            "amplitude": max(freq_dezenas.values()) - min(freq_dezenas.values()),
            "ss_obs": ss_obs,
        },
        "intersecoes": {
            "total_pares": total_pares,
            "media": sum(k * v for k, v in hist_inter.items()) / total_pares,
            "pares_c14": hist_inter.get(14, 0),
            "pares_c13": hist_inter.get(13, 0),
            "pares_c12": hist_inter.get(12, 0),
            "distribuicao_pct": {k: round(hist_inter[k] / total_pares * 100.0, 3) for k in sorted(hist_inter.keys())},
        },
        "sequencias": {
            "max_absoluto": max(seqs),
            "distribuicao": dict(sorted(dist_seqs.items())),
            "jogos_seq_ge_7": sum(dist_seqs.get(k, 0) for k in range(7, 16)),
            "jogos_seq_ge_8": sum(dist_seqs.get(k, 0) for k in range(8, 16)),
        },
        "primeiros_5_jogos": carteira_gerada[:5],
    }

def main():
    sha_script = calcular_hash_arquivo(CAMINHO_SCRIPT_ATUAL)
    print("=" * 80)
    print("ESTUDO COMPARATIVO EXPERIMENTAL ISOLADO: CONTENÇÃO DE SEQUÊNCIAS CONSECUTIVAS")
    print(f"Hash SHA-256 do Script: {sha_script}")
    print("Tamanho: J=1.000 jogos | Semente: 2027 | Orçamento B=32 (32.000 avaliações)")
    print("=" * 80)

    spec = {
        "quantidade_jogos": 1000,
        "tamanhos_jogos": (15,) * 1000,
        "pool": tuple(range(1, 26)),
        "fixas": (),
        "fixas_por_jogo": (),
        "bloqueadas": (),
        "livres_para_jogos": tuple(range(1, 26)),
        "pesos": PERFIS_PESOS_ETAPA2["padrao_modo4"],
        "tamanho_pool": 25,
        "espaco_admissivel": math.comb(25, 15),
        "modo_fixas": "fixas_todas_apostas",
    }

    cenarios = [
        ("Baseline (Sem Filtro)", None),
        ("Limite 5", 5),
        ("Limite 6", 6),
    ]

    resultados = []
    for nome, teto in cenarios:
        print(f"\n>>> Executando {nome}...")
        res = executar_gerador_paramétrico(spec, semente=2027, max_avaliacoes=32000, teto_consecutivos=teto)
        resultados.append(res)
        print(f"    Tempo: {res['tempo_segundos']:.2f} s | RAM: {res['memoria_pico_mb']:.2f} MB")
        print(f"    F(C): {res['funcao_objetivo_F']:.8f} | Cobertura t4: {res['cobertura']['t4']}/12650 ({res['cobertura']['t4_pct']:.2f}%)")
        print(f"    SS_obs: {res['frequencia_dezenas']['ss_obs']:.2f} | Dezenas min/max: {res['frequencia_dezenas']['min']}/{res['frequencia_dezenas']['max']}")
        print(f"    Maior seq: {res['sequencias']['max_absoluto']} | Jogos seq >= 8: {res['sequencias']['jogos_seq_ge_8']}")
        print(f"    Candidatos gerados: {res['total_tentativas_candidatos']} | Rejeitados: {res['candidatos_rejeitados_filtro']} ({res['taxa_rejeicao_pct']:.2f}%)")
        print(f"    Admitidos: {res['candidatos_admitidos']} | Avaliações efetivas: {res['avaliacoes_efetivas']}")
        print(f"    Passos com cota incompleta: {res['passos_cota_incompleta']}/1000")
        print(f"    Tripla validação: {res['tripla_validacao']['aprovado_1e12']} (|E4-E2|={res['tripla_validacao']['div_e4_e2']:.2e})")

    metadados_globais = {
        "hash_script_sha256": sha_script,
        "data_execucao": time.strftime("%Y-%m-%d %H:%M:%S"),
        "semente": 2027,
        "b_cand": 32,
        "max_avaliacoes_por_cenario": 32000,
        "tamanho_carteira": 1000,
        "cenarios": resultados,
    }

    caminho_saida = Path(r"C:\Users\Luis Brun\.gemini\antigravity\brain\10bd4b49-dfcf-4e32-9b24-d4a0b00e1434\scratch\relatorio_experimento_consecutivos.json")
    with open(caminho_saida, "w", encoding="utf-8") as f:
        json.dump(metadados_globais, f, indent=2, ensure_ascii=False)
    print(f"\nRelatório estruturado salvo com sucesso em: {caminho_saida}")

    print("\n" + "=" * 80)
    print("TABELA COMPARATIVA CONSOLIDADA (10 INDICADORES)")
    print("=" * 80)
    b, e5, e6 = resultados[0], resultados[1], resultados[2]
    linhas = [
        ("Jogos únicos", f"{b['jogos_unicos']}/1000 ({b['unicidade_pct']:.1f}%)", f"{e5['jogos_unicos']}/1000 ({e5['unicidade_pct']:.1f}%)", f"{e6['jogos_unicos']}/1000 ({e6['unicidade_pct']:.1f}%)"),
        ("Cobertura de quadras", f"{b['cobertura']['t4']}/12650 ({b['cobertura']['t4_pct']:.2f}%)", f"{e5['cobertura']['t4']}/12650 ({e5['cobertura']['t4_pct']:.2f}%)", f"{e6['cobertura']['t4']}/12650 ({e6['cobertura']['t4_pct']:.2f}%)"),
        ("F(C)", f"{b['funcao_objetivo_F']:.8f}", f"{e5['funcao_objetivo_F']:.8f}", f"{e6['funcao_objetivo_F']:.8f}"),
        ("SS observado", f"{b['frequencia_dezenas']['ss_obs']:.2f}", f"{e5['frequencia_dezenas']['ss_obs']:.2f}", f"{e6['frequencia_dezenas']['ss_obs']:.2f}"),
        ("Candidatos gerados", f"{b['total_tentativas_candidatos']}", f"{e5['total_tentativas_candidatos']}", f"{e6['total_tentativas_candidatos']}"),
        ("Candidatos rejeitados", f"{b['candidatos_rejeitados_filtro']} ({b['taxa_rejeicao_pct']:.1f}%)", f"{e5['candidatos_rejeitados_filtro']} ({e5['taxa_rejeicao_pct']:.1f}%)", f"{e6['candidatos_rejeitados_filtro']} ({e6['taxa_rejeicao_pct']:.1f}%)"),
        ("Avaliações efetivas", f"{b['avaliacoes_efetivas']}", f"{e5['avaliacoes_efetivas']}", f"{e6['avaliacoes_efetivas']}"),
        ("Maior sequência", f"{b['sequencias']['max_absoluto']}", f"{e5['sequencias']['max_absoluto']}", f"{e6['sequencias']['max_absoluto']}"),
        ("Tempo total", f"{b['tempo_segundos']:.2f} s", f"{e5['tempo_segundos']:.2f} s", f"{e6['tempo_segundos']:.2f} s"),
        ("Memória máxima", f"{b['memoria_pico_mb']:.2f} MB", f"{e5['memoria_pico_mb']:.2f} MB", f"{e6['memoria_pico_mb']:.2f} MB"),
    ]
    print(f"| Indicador | Baseline | Limite 5 | Limite 6 |")
    print(f"|---|---:|---:|---:|")
    for rotulo, vb, v5, v6 in linhas:
        print(f"| {rotulo} | {vb} | {v5} | {v6} |")

if __name__ == "__main__":
    main()
