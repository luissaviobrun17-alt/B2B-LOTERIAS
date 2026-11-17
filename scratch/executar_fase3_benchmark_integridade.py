# -*- coding: utf-8 -*-
"""
FASE 3: BENCHMARK COMPARATIVO E INTEGRIDADE OPERACIONAL (J=1.000 vs J=2.000)
============================================================================
Executa a bateria formal de auditoria operacional em ambiente isolado:
- Etapa 3.2: Integridade operacional de carga, formato e unicidade.
- Etapa 3.3: Benchmark de leitura, deserialização, acesso e memória (20 repetições).
- Estabilidade e repetibilidade com cálculo de média, desvio padrão e percentis.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import statistics
import sys
import time
import tracemalloc

sys.path.insert(0, os.path.abspath("."))

from catalogo_lotofacil_10000.leitor_experimental_2000 import (
    CAMINHO_CATALOGO_1000,
    CAMINHO_CATALOGO_2000,
    HASH_JOGOS_OFICIAL_J1000,
    HASH_JOGOS_OFICIAL_J2000,
    obter_carteira_oficial_2000,
    obter_carteira_por_tamanho,
    obter_status_governanca_fase3,
    verificar_integridade_catalogo_2000,
)
from lotofacil_modo4.etapa1_regras_oficiais import validar_aposta_lotofacil

def benchmark_carteira(caminho: Path, n_repeticoes: int = 20) -> dict:
    tempos_io_ms: list[float] = []
    tempos_json_ms: list[float] = []
    tempos_total_ms: list[float] = []
    mems_pico_kb: list[float] = []

    # Warmup
    with open(caminho, "rb") as f:
        _ = json.loads(f.read().decode("utf-8"))

    for _ in range(n_repeticoes):
        tracemalloc.start()
        t0 = time.perf_counter()
        with open(caminho, "rb") as f:
            raw = f.read()
        t1 = time.perf_counter()
        doc = json.loads(raw.decode("utf-8"))
        t2 = time.perf_counter()
        _cur, pico = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        tempos_io_ms.append((t1 - t0) * 1000.0)
        tempos_json_ms.append((t2 - t1) * 1000.0)
        tempos_total_ms.append((t2 - t0) * 1000.0)
        mems_pico_kb.append(pico / 1024.0)

    # Benchmark de acesso paginado / fatiamento
    jogos = doc["jogos"]
    t_acesso0 = time.perf_counter()
    for _ in range(100):
        _slice = [tuple(jg) for jg in jogos[:100]]
    t_acesso1 = time.perf_counter()
    tempo_acesso_slice_us = ((t_acesso1 - t_acesso0) / 100.0) * 1_000_000.0

    return {
        "arquivo": caminho.name,
        "tamanho_bytes": caminho.stat().st_size,
        "jogos": len(jogos),
        "repeticoes": n_repeticoes,
        "tempo_io_ms_medio": round(statistics.mean(tempos_io_ms), 4),
        "tempo_io_ms_desv": round(statistics.stdev(tempos_io_ms), 4),
        "tempo_json_ms_medio": round(statistics.mean(tempos_json_ms), 4),
        "tempo_json_ms_desv": round(statistics.stdev(tempos_json_ms), 4),
        "tempo_total_ms_medio": round(statistics.mean(tempos_total_ms), 4),
        "tempo_total_ms_min": round(min(tempos_total_ms), 4),
        "tempo_total_ms_max": round(max(tempos_total_ms), 4),
        "tempo_total_ms_desv": round(statistics.stdev(tempos_total_ms), 4),
        "memoria_pico_kb_media": round(statistics.mean(mems_pico_kb), 2),
        "tempo_acesso_100_jogos_us": round(tempo_acesso_slice_us, 2),
    }

def main():
    print("=" * 80)
    print("FASE 3: HOMOLOGAÇÃO OPERACIONAL E BENCHMARK EM AMBIENTE ISOLADO")
    print("=" * 80)

    # 1. Auditoria de Integridade Criptográfica via Leitor Experimental
    print("1. Auditoria Criptográfica Inicial:")
    valido_2000, rel_2000 = verificar_integridade_catalogo_2000()
    print(f"   Catálogo J=2.000 Íntegro: {valido_2000}")
    print(f"   Hash Físico Válido:       {rel_2000['hash_fisico_valido']}")
    print(f"   Hash Jogos Válido:        {rel_2000['hash_jogos_valido']}")
    print(f"   Hash Documento Válido:    {rel_2000['hash_documento_valido']}")
    print(f"   Jogos Únicos Confirmados: {rel_2000['jogos_unicos']}/2000")
    assert valido_2000, "FALHA: Integridade do catálogo J=2000 comprometida!"

    # 2. Validação Operacional de Carga e Conformidade com as Regras da Caixa
    print("\n2. Validação Operacional de Formato e Regras da Caixa:")
    jogos_carregados = obter_carteira_oficial_2000()
    assert len(jogos_carregados) == 2000, f"Esperado 2000 jogos, obtido {len(jogos_carregados)}"
    for idx, jg in enumerate(jogos_carregados):
        validado = validar_aposta_lotofacil(jg)
        assert len(validado) == 15, f"Jogo {idx} não possui 15 dezenas!"
        assert all(1 <= d <= 25 for d in validado), f"Jogo {idx} possui dezenas fora de [1..25]!"
    print("   Total de 2.000 bilhetes validados individualmente sob regras oficiais Caixa: 100% CONFORME.")

    # 3. Benchmark Comparativo Bilateral (J=1.000 vs J=2.000)
    print("\n3. Executando Bateria de Benchmark (20 repetições por carteira)...")
    b1000 = benchmark_carteira(CAMINHO_CATALOGO_1000, 20)
    b2000 = benchmark_carteira(CAMINHO_CATALOGO_2000, 20)

    print("-" * 80)
    print(f"{'Métrica':<35} | {'J=1.000':<18} | {'J=2.000':<18} | {'Variação':<10}")
    print("-" * 80)
    print(f"{'Tamanho do arquivo (bytes)':<35} | {b1000['tamanho_bytes']:<18,d} | {b2000['tamanho_bytes']:<18,d} | +{b2000['tamanho_bytes']/b1000['tamanho_bytes']*100 - 100:.1f}%")
    print(f"{'Tempo de leitura I/O disco':<35} | {b1000['tempo_io_ms_medio']:<15.3f} ms | {b2000['tempo_io_ms_medio']:<15.3f} ms | +{b2000['tempo_io_ms_medio'] - b1000['tempo_io_ms_medio']:.3f} ms")
    print(f"{'Tempo de deserialização JSON':<35} | {b1000['tempo_json_ms_medio']:<15.3f} ms | {b2000['tempo_json_ms_medio']:<15.3f} ms | +{b2000['tempo_json_ms_medio'] - b1000['tempo_json_ms_medio']:.3f} ms")
    print(f"{'Tempo de carga total (I/O + JSON)':<35} | {b1000['tempo_total_ms_medio']:<15.3f} ms | {b2000['tempo_total_ms_medio']:<15.3f} ms | +{b2000['tempo_total_ms_medio'] - b1000['tempo_total_ms_medio']:.3f} ms")
    print(f"{'Desvio padrão total (estabilidade)':<35} | {b1000['tempo_total_ms_desv']:<15.3f} ms | {b2000['tempo_total_ms_desv']:<15.3f} ms | ±{b2000['tempo_total_ms_desv']:.3f} ms")
    print(f"{'Consumo de pico de heap Python':<35} | {b1000['memoria_pico_kb_media']:<15.1f} KB | {b2000['memoria_pico_kb_media']:<15.1f} KB | +{b2000['memoria_pico_kb_media'] - b1000['memoria_pico_kb_media']:.1f} KB")
    print(f"{'Latência de fatia (100 bilhetes)':<35} | {b1000['tempo_acesso_100_jogos_us']:<15.2f} µs | {b2000['tempo_acesso_100_jogos_us']:<15.2f} µs | {b2000['tempo_acesso_100_jogos_us'] - b1000['tempo_acesso_100_jogos_us']:+.2f} µs")
    print("-" * 80)

    # 4. Status de Governança
    print("\n4. Status Unificado de Governança:")
    gov = obter_status_governanca_fase3()
    print(f"   Fase:            {gov['fase']}")
    print(f"   Ambiente:        {gov['ambiente']}")
    print(f"   Feature Flag:    {gov['motor_dinamico']['feature_flag']} = {gov['motor_dinamico']['valor']}")
    print(f"   Estado Produção: {gov['motor_dinamico']['estado_producao']}")
    print(f"   Carteira J=1.000: Íntegro={gov['carteiras']['J1000']['integro']} | SHA-256={gov['carteiras']['J1000']['sha256_jogos'][:16]}...")
    print(f"   Carteira J=2.000: Íntegro={gov['carteiras']['J2000']['integro']} | SHA-256={gov['carteiras']['J2000']['sha256_jogos'][:16]}...")
    print("=" * 80)
    print("BENCHMARK E INTEGRIDADE OPERACIONAL FASE 3 CONCLUÍDOS COM SUCESSO.")
    print("=" * 80)

if __name__ == "__main__":
    main()
