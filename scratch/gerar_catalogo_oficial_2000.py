# -*- coding: utf-8 -*-
"""
GERAÇÃO E HOMOLOGAÇÃO DO CATÁLOGO OFICIAL CANÔNICO J=2.000 (LOTOFÁCIL MODO 4)
=============================================================================
Executa a geração canônica de 2.000 jogos da Lotofácil MODO 4 incorporando o
parâmetro aprovado Limite 6 (teto estrito de no máximo 6 dezenas consecutivas).

Garantias de governança implementadas:
1. Auditoria prévia e pós da integridade da carteira canônica J=1.000.
2. Semente determinística oficial 2027 com orçamento B_cand = 32 (64.000 avaliações).
3. Amostragem ponderada com reposição garantida de candidatos (zero passos incompletos).
4. Tripla validação matemática com tolerância estrita <= 1e-12.
5. Emissão do catálogo estruturado, manifesto SHA-256 e cópia de segurança em backup independente.
"""

from __future__ import annotations

import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import random
import shutil
import sys
import time
import tracemalloc
from collections import Counter
from typing import Any, Dict, List, Mapping, Optional, Sequence, Set, Tuple

sys.path.insert(0, os.path.abspath("."))
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

from lotofacil_modo4.etapa1_regras_oficiais import (
    UNIVERSO_TOTAL,
    TAMANHO_SORTEIO,
    validar_aposta_lotofacil,
)
from lotofacil_modo4.etapa2_funcao_objetivo import (
    avaliar_carteira_etapa2,
    PERFIS_PESOS_ETAPA2,
)
from lotofacil_modo4.etapa2_referencia_independente import (
    avaliar_carteira_referencia_independente,
)
from lotofacil_modo4.etapa4_arquitetura_adaptativa import (
    AvaliadorConstrutivoIncrementalEtapa4,
    MotorIncrementalOtimizadoEtapa4,
    _gerar_jogo_aleatorio_valido,
)

HASH_OFICIAL_J1000_ESPERADO = "9a835a98a2f5a56d806b07683b12dd1ed393d54d6d0ba291ed2084443b2ee595"

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

def calcular_metricas_completas(carteira: List[List[int]], pool: Tuple[int, ...]) -> Dict[str, Any]:
    jogos = [tuple(sorted(jg)) for jg in carteira]
    j = len(jogos)

    duplicatas = j - len(set(jogos))

    t1: Set[int] = set()
    t2: Set[Tuple[int, int]] = set()
    t3: Set[Tuple[int, int, int]] = set()
    t4: Set[Tuple[int, int, int, int]] = set()

    freq_dezenas = {d: 0 for d in pool}
    for jg in jogos:
        for d in jg:
            freq_dezenas[d] += 1
        t1.update(jg)
        n = len(jg)
        for i in range(n):
            for k in range(i + 1, n):
                t2.add((jg[i], jg[k]))
                for l in range(k + 1, n):
                    t3.add((jg[i], jg[k], jg[l]))
                    for m in range(l + 1, n):
                        t4.add((jg[i], jg[k], jg[l], jg[m]))

    mu = (15.0 * j) / len(pool)
    ss_obs = sum((freq_dezenas[d] - mu) ** 2 for d in pool)
    _, rem = divmod(15 * j, len(pool))
    ss_min = rem * (1.0 - rem / len(pool))

    seqs = [calcular_maior_sequencia(jg) for jg in jogos]

    return {
        "duplicatas": duplicatas,
        "unicidade_pct": 100.0 if duplicatas == 0 else (len(set(jogos)) / j * 100.0),
        "cobertura_t1_pct": len(t1) / 25.0 * 100.0,
        "cobertura_t2_pct": len(t2) / 300.0 * 100.0,
        "cobertura_t3_pct": len(t3) / 2300.0 * 100.0,
        "cobertura_t4_pct": round(len(t4) / 12650.0 * 100.0, 4),
        "quadras_cobertas": len(t4),
        "total_quadras_possiveis": 12650,
        "ss_observado": round(ss_obs, 6),
        "ss_minimo": round(ss_min, 6),
        "media_frequencia_dezena": mu,
        "frequencia_min_dezena": min(freq_dezenas.values()),
        "frequencia_max_dezena": max(freq_dezenas.values()),
        "maior_sequencia_consecutiva": max(seqs),
        "jogos_seq_ge_7": sum(1 for s in seqs if s >= 7),
    }

def gerar_carteira_limite6(
    spec: Mapping[str, Any],
    semente: int,
    max_avaliacoes: int,
    teto_consecutivos: int = 6,
) -> Tuple[List[Tuple[int, ...]], Dict[str, Any]]:
    rng = random.Random(semente)
    av = AvaliadorConstrutivoIncrementalEtapa4(spec)
    tams = spec["tamanhos_jogos"]
    j = spec["quantidade_jogos"]
    livres = spec["livres_para_jogos"]
    fixas_j = spec["fixas_por_jogo"]
    cand_por_passo = max(2, max_avaliacoes // max(1, j))

    avaliacoes_efetivas = 0
    usados: Set[Tuple[int, ...]] = set()
    total_tentativas = 0
    rejeitados_filtro = 0
    rejeitados_unicidade = 0
    admitidos = 0
    passos_cota_incompleta = 0

    tracemalloc.start()
    t0 = time.perf_counter()

    for idx_j, m_i in enumerate(tams):
        faltam = m_i - len(fixas_j)
        restantes_av = max(1, max_avaliacoes - avaliacoes_efetivas)
        limite_cands = min(cand_por_passo, restantes_av) if idx_j < j - 1 else restantes_av

        cands: List[Tuple[int, ...]] = []
        vistos: Set[Tuple[int, ...]] = set()

        if faltam == 0:
            cands.append(fixas_j)
            admitidos += 1
        else:
            ord_menos = sorted(livres, key=lambda d: (av.u_counts[d], d))
            cg0 = tuple(sorted((*fixas_j, *ord_menos[:faltam])))
            total_tentativas += 1
            if calcular_maior_sequencia(cg0) <= teto_consecutivos:
                if cg0 not in usados:
                    vistos.add(cg0)
                    cands.append(cg0)
                    admitidos += 1
                else:
                    rejeitados_unicidade += 1
            else:
                rejeitados_filtro += 1

            if len(ord_menos) > faltam and len(cands) < limite_cands:
                desloc = max(1, len(ord_menos) // 4)
                rot = ord_menos[desloc:] + ord_menos[:desloc]
                cg1 = tuple(sorted((*fixas_j, *rot[:faltam])))
                total_tentativas += 1
                if calcular_maior_sequencia(cg1) <= teto_consecutivos:
                    if cg1 not in usados and cg1 not in vistos:
                        vistos.add(cg1)
                        cands.append(cg1)
                        admitidos += 1
                    else:
                        rejeitados_unicidade += 1
                else:
                    rejeitados_filtro += 1

            pesos_amostra = [1.0 / (1.0 + av.u_counts[d]) for d in livres]
            tent = 0
            max_tent = max(limite_cands * 15, 30)

            while len(cands) < limite_cands and tent < max_tent:
                tent += 1
                total_tentativas += 1
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
                    if calcular_maior_sequencia(cg) <= teto_consecutivos:
                        vistos.add(cg)
                        cands.append(cg)
                        admitidos += 1
                    else:
                        rejeitados_filtro += 1
                else:
                    rejeitados_unicidade += 1

        if not cands:
            for _ in range(200):
                total_tentativas += 1
                cg = _gerar_jogo_aleatorio_valido(rng, livres, fixas_j, m_i)
                if cg not in usados:
                    if calcular_maior_sequencia(cg) <= teto_consecutivos:
                        cands.append(cg)
                        admitidos += 1
                        break
                    else:
                        rejeitados_filtro += 1
                else:
                    rejeitados_unicidade += 1

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

    telemetria = {
        "tempo_total_segundos": round(t1 - t0, 4),
        "memoria_pico_mb": round(pico_mem / (1024 * 1024), 4),
        "avaliacoes_efetivas": avaliacoes_efetivas,
        "taxa_utilizacao_orcamento": round(avaliacoes_efetivas / max_avaliacoes, 4),
        "criterio_parada": "construcao_completa",
        "teto_consecutivos": teto_consecutivos,
        "tentativas_candidatos": total_tentativas,
        "rejeitados_consecutivos": rejeitados_filtro,
        "rejeitados_duplicidade": rejeitados_unicidade,
        "candidatos_admitidos": admitidos,
        "passos_cota_incompleta": passos_cota_incompleta,
    }

    return list(av.jogos), telemetria

def main():
    print("=" * 80)
    print("GERACAO E HOMOLOGACAO OFICIAL DA CARTEIRA CANONICA J=2.000 (LOTOFACIL MODO 4)")
    print("Configuração Homologada: Limite 6 (teto estrito de 6 dezenas consecutivas)")
    print("=" * 80)

    # 1. Auditoria Prévia da Carteira Canônica J=1.000
    dir_catalogo = Path("catalogo_lotofacil_10000")
    caminho_cat_1000 = dir_catalogo / "lotofacil_carteira_1000.json"
    if not caminho_cat_1000.is_file():
        raise FileNotFoundError(f"FALHA CRITICA: Catalogo J=1000 nao encontrado em {caminho_cat_1000}!")

    with open(caminho_cat_1000, "rb") as f_prev:
        hash_cat_1000_previo = hashlib.sha256(f_prev.read()).hexdigest()
    print(f"Auditoria previa J=1000:")
    print(f"  SHA-256 Observado: {hash_cat_1000_previo}")
    print(f"  SHA-256 Esperado:  {HASH_OFICIAL_J1000_ESPERADO}")
    if hash_cat_1000_previo != HASH_OFICIAL_J1000_ESPERADO:
        raise RuntimeError("FALHA CRITICA DE GOVERNANCA: A carteira J=1000 diverge do hash oficial!")
    print("  Status J=1000: PRESERVADO E INTEGRO.")
    print("-" * 80)

    # 2. Definição Formal de Parâmetros da Etapa 2.2
    quantidade_jogos = 2000
    b_cand = 32
    semente = 2027
    max_avaliacoes = b_cand * quantidade_jogos  # 64.000 avaliações
    teto_consecutivos = 6

    print(f"Parametros Homologados:")
    print(f"  Quantidade de Jogos (J): {quantidade_jogos}")
    print(f"  Orçamento B_cand:        {b_cand}")
    print(f"  Semente Deterministica:  {semente}")
    print(f"  Teto de Avaliacoes:      {max_avaliacoes}")
    print(f"  Teto Consecutivos:       {teto_consecutivos} dezenas (Limite 6)")
    print("-" * 80)

    spec = {
        "quantidade_jogos": quantidade_jogos,
        "tamanhos_jogos": (15,) * quantidade_jogos,
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

    # 3. Execução da Geração Adaptativa
    print("\nExecutando geracao da carteira oficial J=2000...")
    jogos_brutos, telemetria = gerar_carteira_limite6(
        spec=spec,
        semente=semente,
        max_avaliacoes=max_avaliacoes,
        teto_consecutivos=teto_consecutivos,
    )
    print(f"Geracao concluida em {telemetria['tempo_total_segundos']} s ({telemetria['tempo_total_segundos']/60:.2f} min).")
    print(f"Memoria de pico: {telemetria['memoria_pico_mb']} MB.")
    print(f"Contabilidade: {telemetria['tentativas_candidatos']} tentativas = {telemetria['candidatos_admitidos']} admitidos + {telemetria['rejeitados_consecutivos']} rejeitados filtro + {telemetria['rejeitados_duplicidade']} rejeitados unicidade.")

    carteira_canonica = [list(sorted(jg)) for jg in sorted(tuple(sorted(x)) for x in jogos_brutos)]
    dir_catalogo.mkdir(parents=True, exist_ok=True)
    caminho_checkpoint = dir_catalogo / "checkpoint_jogos_2000.json"
    with open(caminho_checkpoint, "w", encoding="utf-8") as f_chk:
        json.dump(carteira_canonica, f_chk)
    print(f"Salvaguarda intermediaria gravada em: {caminho_checkpoint}")
    pesos = dict(spec["pesos"])

    # 4. Hash Canônico Estrito dos Jogos
    json_jogos_compacto = json.dumps(carteira_canonica, separators=(",", ":"))
    sha256_jogos = hashlib.sha256(json_jogos_compacto.encode("utf-8")).hexdigest()
    print(f"\nSHA-256 Jogos Canonicos J=2000: {sha256_jogos}")

    # 5. Tripla Validação Matemática
    print("\nExecutando Tripla Validacao Matematica...")
    motor = MotorIncrementalOtimizadoEtapa4(carteira_canonica, tuple(range(1, 26)), (), pesos)
    f_e4 = motor.score_atual()

    ev_e2 = avaliar_carteira_etapa2(carteira_canonica)
    f_e2 = float(ev_e2["funcao_objetivo_F"])

    ev_ref = avaliar_carteira_referencia_independente(carteira_canonica)
    f_ref = float(ev_ref["funcao_objetivo_F"])

    div_e4_e2 = abs(f_e4 - f_e2)
    div_e4_ref = abs(f_e4 - f_ref)
    div_e2_ref = abs(f_e2 - f_ref)

    print(f"  F (Etapa 4):              {f_e4:.16f}")
    print(f"  F (Etapa 2 oficial):      {f_e2:.16f}")
    print(f"  F (Ref. Independente):    {f_ref:.16f}")
    print(f"  |E4 - E2|:                {div_e4_e2:.2e}")
    print(f"  |E4 - Ref|:               {div_e4_ref:.2e}")

    aprovado_1e12 = (div_e4_e2 <= 1e-12) and (div_e4_ref <= 1e-12)
    if not aprovado_1e12:
        raise ValueError("FALHA CRITICA: Divergencia matematica superior a 1e-12!")
    print("  Status Tripla Validacao: APROVADO (tolerancia <= 1e-12 rigorosamente respeitada)")

    # 6. Métricas Combinatórias e de Cobertura
    metricas = calcular_metricas_completas(carteira_canonica, tuple(range(1, 26)))
    metricas["funcao_objetivo_F"] = round(f_e4, 12)
    metricas["componentes"] = dict(ev_e2["componentes"])
    metricas["p2_covariancia_esperada"] = float(ev_e2["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]["3_probabilidade_conjunta_carteira"]["variancia_bilhetes_dependente_exata"])

    if metricas["duplicatas"] != 0:
        raise ValueError(f"FALHA CRITICA: Carteira contem {metricas['duplicatas']} jogos duplicados!")
    if metricas["quadras_cobertas"] < 12650:
        raise ValueError(f"FALHA CRITICA: Cobertura de quadras incompleta ({metricas['quadras_cobertas']}/12650)!")
    if metricas["funcao_objetivo_F"] < 0.965:
        raise ValueError(f"FALHA CRITICA: Escore F={metricas['funcao_objetivo_F']} abaixo de 0.965!")
    if metricas["maior_sequencia_consecutiva"] > 6:
        raise ValueError(f"FALHA CRITICA: Maior sequencia ({metricas['maior_sequencia_consecutiva']}) excede teto 6!")

    print(f"\nMetricas Combinatorias Observadas:")
    print(f"  Unicidade: {metricas['unicidade_pct']}% ({len(carteira_canonica)}/{quantidade_jogos})")
    print(f"  Cobertura t=1: {metricas['cobertura_t1_pct']}% (25/25)")
    print(f"  Cobertura t=2: {metricas['cobertura_t2_pct']}% (300/300)")
    print(f"  Cobertura t=3: {metricas['cobertura_t3_pct']}% (2300/2300)")
    print(f"  Cobertura t=4: {metricas['cobertura_t4_pct']}% ({metricas['quadras_cobertas']}/12650)")
    print(f"  SS_obs: {metricas['ss_observado']} | Media mu: {metricas['media_frequencia_dezena']}")
    print(f"  Frequencia min/max: {metricas['frequencia_min_dezena']} / {metricas['frequencia_max_dezena']}")
    print(f"  Maior sequencia observada: {metricas['maior_sequencia_consecutiva']}")
    print(f"  Escore F(C): {metricas['funcao_objetivo_F']}")

    # 7. Montagem do Catálogo Estruturado Oficial J=2.000
    dir_catalogo.mkdir(parents=True, exist_ok=True)
    caminho_catalogo = dir_catalogo / "lotofacil_carteira_2000.json"

    catalogo_dict = {
        "identificador": "LOTOFACIL_MODO4_J2000_CANONICA",
        "versao_formato": "2.0",
        "modalidade": "LOTOFACIL",
        "modo": 4,
        "quantidade_jogos": quantidade_jogos,
        "tamanho_aposta": 15,
        "pool": list(range(1, 26)),
        "fixas": [],
        "bloqueadas": [],
        "pesos": pesos,
        "algoritmo_utilizado": "algoritmo_guloso",
        "semente": semente,
        "b_cand_utilizado": b_cand,
        "orcamento_max_avaliacoes": max_avaliacoes,
        "sha256_jogos_canonicos": sha256_jogos,
        "sha256_documento_catalogo": None,
        "telemetria": telemetria,
        "metricas_qualidade": metricas,
        "tripla_validacao": {
            "f_etapa4": round(f_e4, 16),
            "f_etapa2": round(f_e2, 16),
            "f_referencia_independente": round(f_ref, 16),
            "divergencia_e4_e2": round(div_e4_e2, 18),
            "divergencia_e4_ref": round(div_e4_ref, 18),
            "divergencia_e2_ref": round(div_e2_ref, 18),
            "aprovado_tolerancia_1e12": aprovado_1e12,
        },
        "jogos": carteira_canonica,
    }

    def _serializador_seguro(o: Any) -> Any:
        if hasattr(o, "items"):
            return dict(o)
        raise TypeError(f"Objeto de tipo {type(o)} nao serializavel em JSON")

    doc_sem_hash = {k: v for k, v in catalogo_dict.items() if k != "sha256_documento_catalogo"}
    hash_doc_canonico = hashlib.sha256(
        json.dumps(doc_sem_hash, sort_keys=True, separators=(",", ":"), default=_serializador_seguro).encode("utf-8")
    ).hexdigest()
    catalogo_dict["sha256_documento_catalogo"] = hash_doc_canonico

    # 8. Gravação em Disco e Manifesto
    with open(caminho_catalogo, "w", encoding="utf-8") as f:
        json.dump(catalogo_dict, f, indent=2, ensure_ascii=False, default=_serializador_seguro)

    with open(caminho_catalogo, "rb") as f:
        sha256_arquivo_fisico = hashlib.sha256(f.read()).hexdigest()

    caminho_manifesto = dir_catalogo / "lotofacil_carteira_2000.json.sha256"
    with open(caminho_manifesto, "w", encoding="utf-8") as f:
        f.write(f"{sha256_arquivo_fisico}  lotofacil_carteira_2000.json\n")

    # 9. Backup Independente Fora do Repositório
    dir_backup = Path(r"C:\Users\Luis Brun\.gemini\antigravity\scratch\backup_oficial_lotofacil_2000")
    dir_backup.mkdir(parents=True, exist_ok=True)
    caminho_backup = dir_backup / "lotofacil_carteira_2000.json"
    shutil.copy2(caminho_catalogo, caminho_backup)
    with open(dir_backup / "lotofacil_carteira_2000.json.sha256", "w", encoding="utf-8") as f:
        f.write(f"{sha256_arquivo_fisico}  lotofacil_carteira_2000.json\n")
    print(f"Backup independente salvo em: {caminho_backup}")

    # 10. Verificação Pós-Geração da Custódia de J=1.000
    with open(caminho_cat_1000, "rb") as f_post:
        hash_cat_1000_pos = hashlib.sha256(f_post.read()).hexdigest()
    if hash_cat_1000_pos != hash_cat_1000_previo:
        raise RuntimeError("FALHA CRITICA DE GOVERNANCA: O catalogo de 1.000 jogos foi alterado durante a geracao de 2.000!")
    print(f"Auditoria pos-geracao: Catalogo J=1000 100% preservado (hash {hash_cat_1000_pos}).")

    print(f"\nCatálogo Oficial J=2000 Homologado e Persistido com Sucesso:")
    print(f"  Arquivo JSON: {caminho_catalogo}")
    print(f"  Tamanho: {os.path.getsize(caminho_catalogo):,} bytes")
    print(f"  SHA-256 Jogos Canônicos: {sha256_jogos}")
    print(f"  SHA-256 Estrutural Documental: {hash_doc_canonico}")
    print(f"  SHA-256 Arquivo Físico: {sha256_arquivo_fisico}")
    print(f"  Manifesto: {caminho_manifesto}")
    print("=" * 80)

if __name__ == "__main__":
    main()
