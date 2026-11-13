# -*- coding: utf-8 -*-
"""
GERADOR DE EVIDENCIAS E AUDITORIA DA ETAPA 4 (LOTOFACIL MODO 4)
===============================================================
Executa a bateria completa de integracao, comparacao Etapa 3 vs Etapa 4,
despacho adaptativo deterministico, escalabilidade sob orcamentos equivalentes,
verificacao de independencia AST do modulo de referencia e conferencia dos
hashes congelados das Etapas 1, 2 e 3.
"""

from __future__ import annotations

import hashlib
import json
import os
import sys
import time
import tracemalloc
from typing import Any, Dict, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lotofacil_modo4.etapa1_regras_oficiais import CLAUSULA_MATEMATICA_OBRIGATORIA
from lotofacil_modo4.etapa3_otimizadores import (
    comparar_algoritmos_etapa3,
    otimizar_carteira_etapa3,
)
from lotofacil_modo4.etapa4_arquitetura_adaptativa import (
    HISTORICO_GERACAO_ETAPA4,
    VERSAO_ARQUITETURA_ETAPA4,
    comparar_algoritmos_etapa4,
    executar_arquitetura_adaptativa_etapa4,
)
from lotofacil_modo4.etapa4_referencia_independente import (
    VERSAO_REFERENCIA_ETAPA4,
    auditar_independencia_ast_etapa4,
    resolver_exato_etapa4_ref,
    verificar_equivalencia_etapa4_contra_referencia,
    verificar_preservacao_etapas_1_2_3_ref,
)


def _sha256_arquivo(caminho: str) -> str:
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def _medir_etapa3_vs_etapa4() -> List[Dict[str, Any]]:
    """
    Compara tempo de execucao e pico de memoria entre Etapa 3 e Etapa 4 sob
    exatamente os mesmos parametros, orcamentos e sementes.
    """
    casos = [
        {
            "nome": "bench_guloso_p25_J16_b320",
            "algoritmo": "algoritmo_guloso",
            "kwargs": {
                "pool": list(range(1, 26)),
                "quantidade_jogos": 16,
                "semente": 42,
                "max_avaliacoes": 320,
                "max_iteracoes": 200,
            },
        },
        {
            "nome": "bench_local_p20_J10_b300",
            "algoritmo": "busca_local_trocas",
            "kwargs": {
                "pool": list(range(1, 21)),
                "fixas": [1, 2, 3],
                "bloqueadas": [21, 22, 23, 24, 25],
                "modo_fixas": "todos_os_jogos",
                "quantidade_jogos": 10,
                "semente": 42,
                "max_avaliacoes": 300,
                "max_iteracoes": 200,
            },
        },
        {
            "nome": "bench_multistart_p25_J16_b320",
            "algoritmo": "multiplos_reinicios",
            "kwargs": {
                "pool": list(range(1, 26)),
                "quantidade_jogos": 16,
                "semente": 42,
                "max_avaliacoes": 320,
                "max_iteracoes": 200,
            },
        },
        {
            "nome": "bench_exata_p16_J4",
            "algoritmo": "busca_exata_pequena",
            "kwargs": {
                "pool": list(range(1, 17)),
                "bloqueadas": [21, 22, 23, 24, 25],
                "quantidade_jogos": 4,
                "semente": 42,
                "max_avaliacoes": 2000,
                "max_iteracoes": 2000,
            },
        },
    ]

    comparativo: List[Dict[str, Any]] = []
    for c in casos:
        alg = c["algoritmo"]
        kw = c["kwargs"]
        kw3 = {k: v for k, v in kw.items() if k not in ("max_avaliacoes", "max_iteracoes")} if alg == "busca_exata_pequena" else kw

        # 1. Medicao limpa de tempo de CPU (sem sobrecarga de rastreamento de memoria)
        t0_3 = time.perf_counter()
        res3 = otimizar_carteira_etapa3(algoritmo=alg, **kw3)
        dt3 = time.perf_counter() - t0_3

        t0_4 = time.perf_counter()
        res4 = executar_arquitetura_adaptativa_etapa4(forcar_algoritmo=alg, medir_memoria=False, **kw)
        dt4 = time.perf_counter() - t0_4

        # 2. Medicao dedicada de pico de memoria via tracemalloc sob condicoes identicas
        tracemalloc.start()
        _ = otimizar_carteira_etapa3(algoritmo=alg, **kw3)
        _, pico3 = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        tracemalloc.start()
        _ = executar_arquitetura_adaptativa_etapa4(forcar_algoritmo=alg, medir_memoria=False, **kw)
        _, pico4 = tracemalloc.get_traced_memory()
        tracemalloc.stop()

        f3 = float(res3["funcao_objetivo_F"])
        f4 = float(res4["funcao_objetivo_F"])
        speedup = dt3 / dt4 if dt4 > 0 else 0.0
        reducao_mem_pct = ((pico3 - pico4) / pico3 * 100.0) if pico3 > 0 else 0.0

        comparativo.append(
            {
                "caso": c["nome"],
                "algoritmo": alg,
                "score_F_etapa3": round(f3, 8),
                "score_F_etapa4": round(f4, 8),
                "delta_score_F": round(f4 - f3, 8),
                "tempo_etapa3_s": round(dt3, 5),
                "tempo_etapa4_s": round(dt4, 5),
                "fator_aceleracao_x": round(speedup, 2),
                "memoria_pico_etapa3_kb": round(pico3 / 1024.0, 2),
                "memoria_pico_etapa4_kb": round(pico4 / 1024.0, 2),
                "reducao_memoria_pico_pct": round(reducao_mem_pct, 2),
                "avaliacoes_etapa3": res3["telemetria"]["avaliacoes_realizadas"],
                "avaliacoes_etapa4": res4["telemetria"]["avaliacoes_efetivas"],
            }
        )
    return comparativo


def gerar_pacote_etapa4() -> Dict[str, Any]:
    out_dir = os.path.join(BASE_DIR, "auditoria", "lotofacil_modo4")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Auditoria AST de independencia da Etapa 4 e diagnostico da Etapa 3
    caminho_ref4 = os.path.join(BASE_DIR, "lotofacil_modo4", "etapa4_referencia_independente.py")
    caminho_ref3 = os.path.join(BASE_DIR, "lotofacil_modo4", "etapa3_referencia_independente.py")
    ast_ref4 = auditar_independencia_ast_etapa4(caminho_ref4)
    ast_ref3_diag = auditar_independencia_ast_etapa4(caminho_ref3)

    if not ast_ref4["independencia_comprovada"]:
        raise RuntimeError(f"Referencia Etapa 4 falhou na auditoria AST: {ast_ref4['violacoes']}")

    # 2. Preservacao pre-execucao dos hashes das Etapas 1, 2 e 3
    preservacao_pre = verificar_preservacao_etapas_1_2_3_ref(BASE_DIR)
    if not preservacao_pre["preservado_integralmente"]:
        raise RuntimeError(f"Divergencia pre-Etapa 4 em artefatos congelados: {preservacao_pre['divergencias']}")

    # 3. Benchmark de otimizacao Etapa 3 vs Etapa 4
    bench_e3_e4 = _medir_etapa3_vs_etapa4()

    # 4. Bateria ampliada de escalabilidade e comparacao controlada sob orcamentos equivalentes
    instancias_cfg: List[Dict[str, Any]] = [
        {
            "id": "e4_unit_p15_J1",
            "pool": list(range(1, 16)),
            "bloqueadas": list(range(16, 26)),
            "quantidade_jogos": 1,
            "semente": 42,
            "max_avaliacoes": 100,
            "incluir_exato_se_viavel": True,
        },
        {
            "id": "e4_peq_p16_J4_b2000_exata",
            "pool": list(range(1, 17)),
            "bloqueadas": [21, 22, 23, 24, 25],
            "quantidade_jogos": 4,
            "semente": 42,
            "max_avaliacoes": 2000,
            "max_iteracoes": 2000,
            "incluir_exato_se_viavel": True,
        },
        {
            "id": "e4_peq_mista_p17_m16_e_2x15_exata",
            "pool": list(range(1, 18)),
            "fixas": list(range(1, 15)),
            "bloqueadas": list(range(18, 26)),
            "modo_fixas": "todos_os_jogos",
            "tamanhos_jogos": [16, 15, 15],
            "semente": 42,
            "max_avaliacoes": 200,
            "incluir_exato_se_viavel": True,
        },
        {
            "id": "e4_micro_orc_p25_J12_b30",
            "pool": list(range(1, 26)),
            "quantidade_jogos": 12,
            "semente": 42,
            "max_avaliacoes": 30,
            "incluir_exato_se_viavel": False,
        },
        {
            "id": "e4_med_p20_J10_f3_todos_s42",
            "pool": list(range(1, 21)),
            "fixas": [1, 2, 3],
            "bloqueadas": [21, 22, 23, 24, 25],
            "modo_fixas": "todos_os_jogos",
            "quantidade_jogos": 10,
            "semente": 42,
            "max_avaliacoes": 300,
            "incluir_exato_se_viavel": False,
        },
        {
            "id": "e4_med_p22_J12_f16_pool_s42",
            "pool": list(range(1, 23)),
            "fixas": list(range(1, 17)),
            "bloqueadas": [23, 24, 25],
            "modo_fixas": "composicao_pool",
            "quantidade_jogos": 12,
            "semente": 42,
            "max_avaliacoes": 300,
            "incluir_exato_se_viavel": False,
        },
        {
            "id": "e4_amp_p25_J16_orc56_s42",
            "pool": list(range(1, 26)),
            "orcamento_brl": "56.00",
            "semente": 42,
            "max_avaliacoes": 320,
            "incluir_exato_se_viavel": False,
        },
        {
            "id": "e4_amp_p25_J16_orc56_s101",
            "pool": list(range(1, 26)),
            "orcamento_brl": "56.00",
            "semente": 101,
            "max_avaliacoes": 320,
            "incluir_exato_se_viavel": False,
        },
        {
            "id": "e4_esc_p25_J30_orc105_b450",
            "pool": list(range(1, 26)),
            "orcamento_brl": "105.00",
            "semente": 42,
            "max_avaliacoes": 450,
            "incluir_exato_se_viavel": False,
        },
        {
            "id": "e4_mult_mista_p21_2x16_8x15_b350",
            "pool": list(range(1, 22)),
            "fixas": [1, 2],
            "bloqueadas": [22, 23, 24, 25],
            "modo_fixas": "todos_os_jogos",
            "tamanhos_jogos": [16, 16, 15, 15, 15, 15, 15, 15, 15, 15],
            "semente": 42,
            "max_avaliacoes": 350,
            "incluir_exato_se_viavel": False,
        },
    ]

    benchmarks: Dict[str, Any] = {}
    conferencias_ref: List[Dict[str, Any]] = []
    vitorias_por_algoritmo: Dict[str, int] = {
        "despacho_adaptativo": 0,
        "busca_exata_pequena": 0,
        "multiplos_reinicios": 0,
        "busca_local_trocas": 0,
        "estrategia_combinada": 0,
        "algoritmo_guloso": 0,
        "referencia_aleatoria": 0,
    }
    resumo_despacho_adaptativo: List[Dict[str, Any]] = []
    maior_div_f = 0.0
    total_runs_verificadas = 0

    for cfg in instancias_cfg:
        inst_id = cfg["id"]
        kwargs = {k: v for k, v in cfg.items() if k != "id"}
        comp = comparar_algoritmos_etapa4(**kwargs)

        top = comp["tabela_comparativa"][0]
        # Quando ha empate em 12 casas entre adaptativo e outro algoritmo, registra ambos os lideres e vencedor do desempate
        f_top = comp["resultados_completos"][top["algoritmo"]]["funcao_objetivo_F"]
        lideres_empate = [
            row["algoritmo"]
            for row in comp["tabela_comparativa"]
            if abs(comp["resultados_completos"][row["algoritmo"]]["funcao_objetivo_F"] - f_top) <= 1e-12
        ]
        vitorias_por_algoritmo[top["algoritmo"]] = vitorias_por_algoritmo.get(top["algoritmo"], 0) + 1

        row_adapt = next(r for r in comp["tabela_comparativa"] if r["algoritmo"] == "despacho_adaptativo")
        dec = comp["decisao_despacho_adaptativo"]
        resumo_despacho_adaptativo.append(
            {
                "instancia": inst_id,
                "algoritmo_despachado": dec["algoritmo_escolhido"],
                "regime": dec["regime_identificado"],
                "posicao_ranking": row_adapt["posicao"],
                "empatado_no_topo": "despacho_adaptativo" in lideres_empate,
                "score_F_adaptativo": row_adapt["funcao_objetivo_F"],
                "score_F_lider_instancia": top["funcao_objetivo_F"],
                "gap_adaptativo_para_lider": round(top["funcao_objetivo_F"] - row_adapt["funcao_objetivo_F"], 8),
                "avaliacoes_efetivas": row_adapt["avaliacoes_efetivas"],
                "orcamento_max": row_adapt["orcamento_max_avaliacoes"],
                "taxa_utilizacao": row_adapt["taxa_utilizacao_orcamento"],
                "tempo_s": row_adapt["tempo_total_segundos"],
                "memoria_pico_mb": row_adapt["memoria_pico_mb"],
                "criterio_parada": row_adapt["criterio_parada"],
            }
        )

        # Conferencia cruzada independente (zero-dependencia) de todas as execucoes
        for nome_alg, res_alg in comp["resultados_completos"].items():
            chk = verificar_equivalencia_etapa4_contra_referencia(res_alg)
            total_runs_verificadas += 1
            if chk["diferenca_F"] > maior_div_f:
                maior_div_f = chk["diferenca_F"]
            if not chk["equivalente_1e_12"]:
                raise RuntimeError(
                    f"Falha de equivalencia/conformidade em {inst_id}/{nome_alg}: {chk}"
                )
            conferencias_ref.append(
                {
                    "instancia": inst_id,
                    "algoritmo": nome_alg,
                    "conforme": chk["conforme"],
                    "equivalente_1e_12": chk["equivalente_1e_12"],
                    "diferenca_F": chk["diferenca_F"],
                    "diferenca_max_componente": chk["diferenca_max_componente"],
                }
            )

        # Remove objetos pesados da sub-arvore de avaliacao_etapa2 para JSON compacto
        resumos_compactos = {}
        for k_alg, r_alg in comp["resultados_completos"].items():
            resumos_compactos[k_alg] = {
                "algoritmo": r_alg["algoritmo"],
                "otimo_global_comprovado": r_alg["otimo_global_comprovado"],
                "status_distancia_otimo": r_alg["status_distancia_otimo"],
                "distancia_otimo_global": r_alg["distancia_otimo_global"],
                "funcao_objetivo_F": r_alg["funcao_objetivo_F"],
                "componentes": r_alg["componentes"],
                "distincao_seis_grandezas_probabilisticas": r_alg["distincao_seis_grandezas_probabilisticas"],
                "telemetria": r_alg["telemetria"],
                "sha256_execucao": r_alg["sha256_execucao"],
                "carteira": r_alg["carteira"],
            }

        benchmarks[inst_id] = {
            "escopo_epistemologico": comp["escopo_epistemologico"],
            "condicoes_identicas": comp["condicoes_identicas"],
            "decisao_despacho_adaptativo": comp["decisao_despacho_adaptativo"],
            "status_busca_exata": comp["status_busca_exata"],
            "lideres_empate_topo": lideres_empate,
            "tabela_comparativa": comp["tabela_comparativa"],
            "resultados_resumidos": resumos_compactos,
        }

    # 5. Prova exata independente na instancia pequena mista (e4_peq_mista_p17_m16_e_2x15_exata)
    exato_ref_mista = resolver_exato_etapa4_ref(
        pool=list(range(1, 18)),
        fixas=list(range(1, 15)),
        bloqueadas=list(range(18, 26)),
        modo_fixas="todos_os_jogos",
        tamanhos_jogos=[16, 15, 15],
        limite_combinacoes=500,
    )
    adapt_mista = benchmarks["e4_peq_mista_p17_m16_e_2x15_exata"]["resultados_resumidos"]["despacho_adaptativo"]
    exato_mista_coincide = (
        abs(exato_ref_mista["funcao_objetivo_F"] - adapt_mista["funcao_objetivo_F"]) <= 1e-12
        and exato_ref_mista["carteira_otima"] == adapt_mista["carteira"]
    )
    if not exato_mista_coincide:
        raise RuntimeError("Busca exata mista da Etapa 4 divergiu da referencia independente!")

    # 6. Teste de integracao dos regimes de premiacao Etapa 1 + reprodutibilidade deterministica
    r_det1 = executar_arquitetura_adaptativa_etapa4(
        pool=list(range(1, 22)),
        fixas=[1, 2],
        bloqueadas=[22, 23, 24, 25],
        orcamento_brl="42.00",
        tipo_concurso="lotofacil_independencia",
        semente=909,
        max_avaliacoes=250,
    )
    r_det2 = executar_arquitetura_adaptativa_etapa4(
        pool=list(range(1, 22)),
        fixas=[1, 2],
        bloqueadas=[22, 23, 24, 25],
        orcamento_brl="42.00",
        tipo_concurso="lotofacil_independencia",
        semente=909,
        max_avaliacoes=250,
    )
    reprodutibilidade = {
        "semente_testada": 909,
        "tipo_concurso_integrado": r_det1["especificacao"]["regra_caixa_etapa1"],
        "mesma_semente_identica_sha256": r_det1["sha256_execucao"] == r_det2["sha256_execucao"],
        "mesma_carteira_canonica": r_det1["carteira"] == r_det2["carteira"],
        "mesmo_despacho": r_det1["despacho_adaptativo"]["algoritmo_escolhido"] == r_det2["despacho_adaptativo"]["algoritmo_escolhido"],
        "sha256_execucao": r_det1["sha256_execucao"],
        "historico_utilizado": HISTORICO_GERACAO_ETAPA4,
    }

    # 7. Preservacao pos-execucao das Etapas 1, 2 e 3 (Condicionante IV)
    preservacao_pos = verificar_preservacao_etapas_1_2_3_ref(BASE_DIR)
    if not preservacao_pos["preservado_integralmente"]:
        raise RuntimeError(f"Violacao de preservacao pos-Etapa 4: {preservacao_pos['divergencias']}")

    hashes_etapa4 = {
        "lotofacil_modo4/etapa4_referencia_independente.py": _sha256_arquivo(
            os.path.join(BASE_DIR, "lotofacil_modo4", "etapa4_referencia_independente.py")
        ),
        "lotofacil_modo4/etapa4_arquitetura_adaptativa.py": _sha256_arquivo(
            os.path.join(BASE_DIR, "lotofacil_modo4", "etapa4_arquitetura_adaptativa.py")
        ),
        "lotofacil_modo4/gerar_evidencias_etapa4.py": _sha256_arquivo(
            os.path.join(BASE_DIR, "lotofacil_modo4", "gerar_evidencias_etapa4.py")
        ),
        "testes/test_lotofacil_modo4_etapa4.py": _sha256_arquivo(
            os.path.join(BASE_DIR, "testes", "test_lotofacil_modo4_etapa4.py")
        )
        if os.path.isfile(os.path.join(BASE_DIR, "testes", "test_lotofacil_modo4_etapa4.py"))
        else None,
    }

    evidencias = {
        "etapa": "ETAPA_4_ARQUITETURA_ADAPTATIVA",
        "versao_arquitetura": VERSAO_ARQUITETURA_ETAPA4,
        "versao_referencia_independente": VERSAO_REFERENCIA_ETAPA4,
        "historico_utilizado": HISTORICO_GERACAO_ETAPA4,
        "independencia_referencia_ast": {
            "etapa4_zero_dependencia": ast_ref4,
            "diagnostico_etapa3_anterior": ast_ref3_diag,
        },
        "preservacao_etapas_anteriores": {
            "pre_execucao_ok": preservacao_pre["preservado_integralmente"],
            "pos_execucao_ok": preservacao_pos["preservado_integralmente"],
            "total_arquivos_congelados": preservacao_pos["total_arquivos_congelados"],
            "divergencias": preservacao_pos["divergencias"],
        },
        "benchmark_otimizacao_etapa3_vs_etapa4": bench_e3_e4,
        "resumo_despacho_adaptativo": resumo_despacho_adaptativo,
        "vitorias_ranking_controlado": vitorias_por_algoritmo,
        "benchmarks_escalabilidade": benchmarks,
        "prova_exata_mista_referencia": {
            "coincide_carteira_e_score": exato_mista_coincide,
            "espaco_enumerado": exato_ref_mista["espaco_enumerado"],
            "funcao_objetivo_F": exato_ref_mista["funcao_objetivo_F"],
            "carteira_otima": exato_ref_mista["carteira_otima"],
        },
        "verificacao_referencia_independente": {
            "total_execucoes_conferidas": total_runs_verificadas,
            "todas_equivalentes_1e_12_e_conformes": True,
            "maior_diferenca_F_observada": maior_div_f,
            "amostras": conferencias_ref,
        },
        "reprodutibilidade_e_integracao_etapa1": reprodutibilidade,
        "hashes_artefatos_etapa4": hashes_etapa4,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }

    caminho_json = os.path.join(out_dir, "etapa_04_evidencias.json")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(evidencias, f, ensure_ascii=False, indent=2)

    linhas_md = [
        "# LOTOFACIL MODO 4 : ETAPA 4 (Arquitetura Adaptativa, Integracao e Otimizacao)",
        "",
        "## 1. Independencia da Validacao (AST) e Preservacao das Etapas 1 a 3",
        f"- **Referencia Etapa 4 (`{VERSAO_REFERENCIA_ETAPA4}`):** `independencia_comprovada={ast_ref4['independencia_comprovada']}`, dependencias internas detectadas=`{ast_ref4['dependencias_internas_detectadas']}` (somente biblioteca padrao: `{', '.join(ast_ref4['modulos_importados'])}`).",
        f"- **Diagnostico da Etapa 3 anterior (`etapa3_referencia_independente.py`):** detectadas `{ast_ref3_diag['dependencias_internas_detectadas']}` importacoes internas (`{', '.join(x for x in ast_ref3_diag['modulos_importados'] if 'etapa' in x)}`); lacuna eliminada integralmente na Etapa 4.",
        f"- **Preservacao de artefatos congelados (Etapas 1, 2 e 3):** `{preservacao_pos['total_arquivos_congelados']}/{preservacao_pos['total_arquivos_congelados']}` arquivos preservados sem alteracao (`preservado_integralmente={preservacao_pos['preservado_integralmente']}`).",
        "",
        "## 2. Benchmark de Desempenho e Memoria: Etapa 3 vs Etapa 4",
        "| Caso | Algoritmo | Tempo E3 (s) | Tempo E4 (s) | Aceleracao | Pico Mem E3 (KB) | Pico Mem E4 (KB) | Reducao Mem (%) | Delta F(C) |",
        "| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
    ]
    for b in bench_e3_e4:
        linhas_md.append(
            f"| `{b['caso']}` | `{b['algoritmo']}` | {b['tempo_etapa3_s']:.5f} | {b['tempo_etapa4_s']:.5f} | {b['fator_aceleracao_x']:.2f}x | "
            f"{b['memoria_pico_etapa3_kb']:.2f} | {b['memoria_pico_etapa4_kb']:.2f} | {b['reducao_memoria_pico_pct']:.2f}% | {b['delta_score_F']:+.8f} |"
        )

    linhas_md.extend(
        [
            "",
            "## 3. Despacho Adaptativo Deterministico e Escalabilidade Sob Orcamento Equivalente",
            "| Instancia | Despachado | Regime | Pos | F(C) Adaptativo | F(C) Lider | Gap p/ Lider | Evals Efetivas / Teto (% Uso) | Reinicios | Parada | Tempo (s) | Mem Pico (MB) |",
            "| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: |",
        ]
    )
    for row in resumo_despacho_adaptativo:
        dec = benchmarks[row["instancia"]]["decisao_despacho_adaptativo"]
        uso_pct = row["taxa_utilizacao"] * 100.0
        n_re = next(
            r["quantidade_reinicios"]
            for r in benchmarks[row["instancia"]]["tabela_comparativa"]
            if r["algoritmo"] == "despacho_adaptativo"
        )
        linhas_md.append(
            f"| `{row['instancia']}` | `{row['algoritmo_despachado']}` | `{row['regime']}` | {row['posicao_ranking']} | "
            f"{row['score_F_adaptativo']:.6f} | {row['score_F_lider_instancia']:.6f} | {row['gap_adaptativo_para_lider']:.6f} | "
            f"{row['avaliacoes_efetivas']}/{row['orcamento_max']} ({uso_pct:.1f}%) | {n_re} | `{row['criterio_parada']}` | "
            f"{row['tempo_s']:.4f} | {row['memoria_pico_mb']:.4f} |"
        )

    linhas_md.extend(["", "## 4. Comparacao Justa Detalhada nas Instancias Chave (Telemetria Completa)"])
    for inst_id in (
        "e4_peq_p16_J4_b2000_exata",
        "e4_peq_mista_p17_m16_e_2x15_exata",
        "e4_med_p20_J10_f3_todos_s42",
        "e4_amp_p25_J16_orc56_s42",
        "e4_amp_p25_J16_orc56_s101",
        "e4_esc_p25_J30_orc105_b450",
        "e4_mult_mista_p21_2x16_8x15_b350",
    ):
        b = benchmarks[inst_id]
        cond = b["condicoes_identicas"]
        linhas_md.extend(
            [
                "",
                f"### 4.1 `{inst_id}` (`{b['escopo_epistemologico']}`)",
                f"- **Parametros:** pool=`{cond['tamanho_pool']}`, fixas=`{len(cond['fixas'])}` (`{cond['modo_fixas']}`), bloqueadas=`{len(cond['bloqueadas'])}`, jogos=`{len(cond['tamanhos_jogos'])}` (`{sorted(set(cond['tamanhos_jogos']))}`), espaco=`{cond['espaco_admissivel']}`, semente=`{cond['semente']}`, teto=`{cond['max_avaliacoes']}`.",
                f"- **Motivo despacho:** {b['decisao_despacho_adaptativo']['motivo_tecnico_escolha']}",
                "",
                "| Pos | Algoritmo | Score F(C) | Dist. Otimo Exato | Efetivas / Teto | % Uso | Reinicios | Crit. Parada | Tempo (s) | Mem (MB) |",
                "| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: |",
            ]
        )
        for row in b["tabela_comparativa"]:
            dist_s = f"{row['distancia_otimo_global']:.6f}" if row["distancia_otimo_global"] is not None else "N/A (Heur.)"
            uso_pct = row["taxa_utilizacao_orcamento"] * 100.0
            linhas_md.append(
                f"| {row['posicao']} | `{row['algoritmo']}` | {row['funcao_objetivo_F']:.6f} | {dist_s} | "
                f"{row['avaliacoes_efetivas']}/{row['orcamento_max_avaliacoes']} | {uso_pct:.1f}% | {row['quantidade_reinicios']} | "
                f"`{row['criterio_parada']}` | {row['tempo_total_segundos']:.4f} | {row['memoria_pico_mb']:.4f} |"
            )

    linhas_md.extend(
        [
            "",
            "## 5. Verificacao Cruzada Independente, Reprodutibilidade e Principio Cientifico",
            f"- **Execucoes auditadas pela referencia zero-dependencia:** `{total_runs_verificadas}/{total_runs_verificadas}` equivalentes em <= 1e-12 e conformes (`maior_diferenca_F_observada={maior_div_f:.2e}`).",
            f"- **Prova exata mista independente (`e4_peq_mista_p17_m16_e_2x15_exata`):** coincide integralmente (`{exato_mista_coincide}`) em `{exato_ref_mista['espaco_enumerado']}` carteiras enumeradas.",
            f"- **Reprodutibilidade e integracao CAIXA (semente `909`, `{reprodutibilidade['tipo_concurso_integrado']['tipo_concurso']}`):** SHA-256 identico=`{reprodutibilidade['mesma_semente_identica_sha256']}` (`{reprodutibilidade['sha256_execucao']}`), `historico_utilizado={reprodutibilidade['historico_utilizado']}`.",
            "",
            f"> {CLAUSULA_MATEMATICA_OBRIGATORIA}",
        ]
    )

    caminho_md = os.path.join(out_dir, "ETAPA_04_ARQUITETURA_ADAPTATIVA.md")
    with open(caminho_md, "w", encoding="utf-8") as f:
        f.write("\n".join(linhas_md))

    return {
        "evidencias_json": caminho_json,
        "relatorio_md": caminho_md,
        "independencia_ast_etapa4": ast_ref4["independencia_comprovada"],
        "preservacao_etapas_1_2_3_ok": preservacao_pos["preservado_integralmente"],
        "total_execucoes_conferidas": total_runs_verificadas,
        "maior_diferenca_F": maior_div_f,
        "benchmark_etapa3_vs_etapa4": bench_e3_e4,
        "vitorias_ranking_controlado": vitorias_por_algoritmo,
        "hashes_artefatos_etapa4": hashes_etapa4,
    }


if __name__ == "__main__":
    print(json.dumps(gerar_pacote_etapa4(), ensure_ascii=False, indent=2))
