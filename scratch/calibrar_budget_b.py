import os
import sys
import json
import time
import math
import statistics
from typing import Any, Dict, List, Tuple

sys.path.insert(0, os.path.abspath("."))
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

from lotofacil_modo4.etapa4_arquitetura_adaptativa import (
    executar_arquitetura_adaptativa_etapa4,
    AvaliadorConstrutivoIncrementalEtapa4,
)

B_CAND_NIVEIS = [2, 4, 8, 16, 32, 64]
SEMENTES = [2026, 2027, 2028]
J = 1000
POOL = tuple(range(1, 26))

def calcular_coberturas(carteira: List[Any]) -> Dict[str, Any]:
    carteira_tuplas = [tuple(sorted(jg)) for jg in carteira]
    
    # Unicidade
    duplicatas = len(carteira_tuplas) - len(set(carteira_tuplas))
    
    # t = 1 (25 dezenas)
    t1_set = set()
    for jg in carteira_tuplas:
        t1_set.update(jg)
    cob_t1 = len(t1_set) / 25.0
    
    # t = 2 (300 pares)
    t2_set = set()
    for jg in carteira_tuplas:
        for i in range(len(jg)):
            for k in range(i + 1, len(jg)):
                t2_set.add((jg[i], jg[k]))
    cob_t2 = len(t2_set) / 300.0
    
    # t = 3 (2.300 trincas)
    t3_set = set()
    for jg in carteira_tuplas:
        for i in range(len(jg)):
            for k in range(i + 1, len(jg)):
                for l in range(k + 1, len(jg)):
                    t3_set.add((jg[i], jg[k], jg[l]))
    cob_t3 = len(t3_set) / 2300.0
    
    # t = 4 (12.650 quadras)
    t4_set = set()
    for jg in carteira_tuplas:
        for i in range(len(jg)):
            for k in range(i + 1, len(jg)):
                for l in range(k + 1, len(jg)):
                    for m in range(l + 1, len(jg)):
                        t4_set.add((jg[i], jg[k], jg[l], jg[m]))
    cob_t4 = len(t4_set) / 12650.0
    
    return {
        "duplicatas": duplicatas,
        "cobertura_t1_pct": cob_t1 * 100.0,
        "cobertura_t2_pct": cob_t2 * 100.0,
        "cobertura_t3_pct": cob_t3 * 100.0,
        "cobertura_t4_pct": cob_t4 * 100.0,
        "quadras_cobertas": len(t4_set),
    }

def main():
    print("=" * 80)
    print("CALIBRACAO EXPERIMENTAL DO BUDGET B (B_cand) - LOTOFACIL MODO 4 (J=1.000)")
    print("=" * 80)
    print(f"Niveis B_cand: {B_CAND_NIVEIS}")
    print(f"Sementes: {SEMENTES}")
    print(f"Total de execucoes planejadas: {len(B_CAND_NIVEIS) * len(SEMENTES)}")
    print("-" * 80)

    resultados_detalhados = []
    
    # Wrapper para medir latencia de cada insercao
    tempos_passo_atual = []
    t_ultimo_passo = [0.0]
    orig_adicionar = AvaliadorConstrutivoIncrementalEtapa4.adicionar_jogo

    def instrumented_adicionar(self, jogo):
        t_agora = time.perf_counter()
        if t_ultimo_passo[0] > 0.0:
            tempos_passo_atual.append(t_agora - t_ultimo_passo[0])
        orig_adicionar(self, jogo)
        t_ultimo_passo[0] = time.perf_counter()

    AvaliadorConstrutivoIncrementalEtapa4.adicionar_jogo = instrumented_adicionar

    try:
        for b_cand in B_CAND_NIVEIS:
            max_av = b_cand * J
            print(f"\n>>> INICIANDO NIVEL B_cand = {b_cand} (max_avaliacoes = {max_av})")
            
            for semente in SEMENTES:
                tempos_passo_atual.clear()
                t_ultimo_passo[0] = time.perf_counter()
                
                t_inicio = time.perf_counter()
                res = executar_arquitetura_adaptativa_etapa4(
                    pool=POOL,
                    quantidade_jogos=J,
                    tamanho_aposta=15,
                    semente=semente,
                    max_avaliacoes=max_av,
                    forcar_algoritmo="algoritmo_guloso",
                    medir_memoria=True,
                )
                t_fim = time.perf_counter()
                duracao_total = t_fim - t_inicio
                
                # Metricas de insercao
                tempos_passo = list(tempos_passo_atual)
                if tempos_passo:
                    t_medio_ins = sum(tempos_passo) / len(tempos_passo)
                    sorted_t = sorted(tempos_passo)
                    idx_p95 = min(len(sorted_t) - 1, int(0.95 * len(sorted_t)))
                    p95_ins = sorted_t[idx_p95]
                else:
                    t_medio_ins = duracao_total / J
                    p95_ins = t_medio_ins
                
                f_val = float(res["funcao_objetivo_F"])
                av_efetivas = int(res["telemetria"]["avaliacoes_efetivas"])
                pico_mb = float(res["telemetria"]["memoria_pico_mb"])
                carteira = res["carteira"]
                
                cob = calcular_coberturas(carteira)
                
                dados_exec = {
                    "b_cand": b_cand,
                    "semente": semente,
                    "max_avaliacoes": max_av,
                    "avaliacoes_efetivas": av_efetivas,
                    "funcao_objetivo_F": f_val,
                    "tempo_total_s": round(duracao_total, 4),
                    "tempo_medio_insercao_ms": round(t_medio_ins * 1000.0, 4),
                    "latencia_p95_insercao_ms": round(p95_ins * 1000.0, 4),
                    "memoria_pico_mb": round(pico_mb, 4),
                    "duplicatas": cob["duplicatas"],
                    "cobertura_t1_pct": cob["cobertura_t1_pct"],
                    "cobertura_t2_pct": cob["cobertura_t2_pct"],
                    "cobertura_t3_pct": cob["cobertura_t3_pct"],
                    "cobertura_t4_pct": round(cob["cobertura_t4_pct"], 4),
                    "quadras_cobertas": cob["quadras_cobertas"],
                }
                resultados_detalhados.append(dados_exec)
                
                print(
                    f"  Semente {semente}: F = {f_val:.8f} | Evals = {av_efetivas} | "
                    f"Tempo = {duracao_total:.3f} s | Ins_medio = {t_medio_ins*1000.0:.2f} ms | "
                    f"P95 = {p95_ins*1000.0:.2f} ms | RAM = {pico_mb:.2f} MB | "
                    f"Quadras = {cob['quadras_cobertas']}/12650 ({cob['cobertura_t4_pct']:.2f}%)"
                )
    finally:
        AvaliadorConstrutivoIncrementalEtapa4.adicionar_jogo = orig_adicionar

    # Consolidacao Estatistica por Nivel de B_cand
    sumario_niveis = []
    f_medio_anterior = None
    av_medio_anterior = None

    for b_cand in B_CAND_NIVEIS:
        execs = [r for r in resultados_detalhados if r["b_cand"] == b_cand]
        f_vals = [r["funcao_objetivo_F"] for r in execs]
        av_vals = [r["avaliacoes_efetivas"] for r in execs]
        t_vals = [r["tempo_total_s"] for r in execs]
        ins_vals = [r["tempo_medio_insercao_ms"] for r in execs]
        p95_vals = [r["latencia_p95_insercao_ms"] for r in execs]
        ram_vals = [r["memoria_pico_mb"] for r in execs]
        q_vals = [r["quadras_cobertas"] for r in execs]
        
        f_medio = statistics.mean(f_vals)
        f_std = statistics.stdev(f_vals) if len(f_vals) > 1 else 0.0
        av_medio = statistics.mean(av_vals)
        t_medio = statistics.mean(t_vals)
        ins_medio = statistics.mean(ins_vals)
        p95_medio = statistics.mean(p95_vals)
        ram_medio = statistics.mean(ram_vals)
        q_medio = statistics.mean(q_vals)
        
        # Ganho marginal por milhao de avaliacoes: (Delta F / Delta Evals) * 10^6
        if f_medio_anterior is not None and av_medio_anterior is not None:
            delta_f = f_medio - f_medio_anterior
            delta_av = av_medio - av_medio_anterior
            ganho_marginal = (delta_f / delta_av * 1e6) if delta_av > 0 else 0.0
        else:
            ganho_marginal = None
        
        f_medio_anterior = f_medio
        av_medio_anterior = av_medio
        
        sumario_niveis.append({
            "b_cand": b_cand,
            "f_medio": round(f_medio, 10),
            "f_std": round(f_std, 10),
            "f_min": round(min(f_vals), 10),
            "f_max": round(max(f_vals), 10),
            "avaliacoes_efetivas_media": round(av_medio, 1),
            "tempo_total_medio_s": round(t_medio, 4),
            "tempo_insercao_medio_ms": round(ins_medio, 4),
            "latencia_p95_media_ms": round(p95_medio, 4),
            "memoria_pico_media_mb": round(ram_medio, 4),
            "quadras_cobertas_media": round(q_medio, 1),
            "ganho_marginal_por_milhao": round(ganho_marginal, 6) if ganho_marginal is not None else None,
        })

    # Decisao do B_cand otimo pelo criterio de corte marginal (< 10^-5)
    b_otimo = B_CAND_NIVEIS[0]
    for s in sumario_niveis:
        if s["ganho_marginal_por_milhao"] is not None:
            if s["ganho_marginal_por_milhao"] >= 1e-5:
                b_otimo = s["b_cand"]
            else:
                # Primeiro ponto onde ganho marginal < 10^-5
                break

    # Melhor semente para o b_otimo escolhido
    execs_otimo = [r for r in resultados_detalhados if r["b_cand"] == b_otimo]
    melhor_exec = max(execs_otimo, key=lambda r: r["funcao_objetivo_F"])
    melhor_semente = melhor_exec["semente"]

    resultado_final = {
        "estudo": "CALIBRACAO_BUDGET_B_ETAPA2_1",
        "j": J,
        "niveis_testados": B_CAND_NIVEIS,
        "sementes_testadas": SEMENTES,
        "sumario_por_nivel": sumario_niveis,
        "execucoes_detalhadas": resultados_detalhados,
        "b_cand_otimo_selecionado": b_otimo,
        "criterio_selecao": "ponto onde ganho marginal (Delta F / Delta Evals)*10^6 satura ou atinge melhor custo-beneficio operacional",
        "melhor_semente_selecionada": melhor_semente,
        "melhor_f_obtido": melhor_exec["funcao_objetivo_F"],
    }

    caminho_json = "scratch/resultado_calibracao_budget_b.json"
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(resultado_final, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("SUMARIO CONSOLIDADO DA CALIBRACAO")
    print("=" * 80)
    print(f"{'B_cand':<8} | {'F Médio':<12} | {'Desvio Std':<10} | {'Evals':<8} | {'Tempo (s)':<10} | {'P95 (ms)':<9} | {'Ganho/10^6':<12}")
    print("-" * 80)
    for s in sumario_niveis:
        g_str = f"{s['ganho_marginal_por_milhao']:+.6f}" if s["ganho_marginal_por_milhao"] is not None else "Referência"
        print(f"{s['b_cand']:<8} | {s['f_medio']:<12.8f} | {s['f_std']:<10.2e} | {s['avaliacoes_efetivas_media']:<8.0f} | {s['tempo_total_medio_s']:<10.3f} | {s['latencia_p95_media_ms']:<9.2f} | {g_str:<12}")
    print("-" * 80)
    print(f"B_cand Ótimo Selecionado: {b_otimo}")
    print(f"Melhor Semente: {melhor_semente} (F = {melhor_exec['funcao_objetivo_F']:.8f})")
    print(f"Arquivo salvo: {caminho_json}")

if __name__ == "__main__":
    main()
