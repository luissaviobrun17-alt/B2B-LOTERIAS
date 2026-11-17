import os
import sys
import json
import time
import hashlib
from decimal import Decimal
from pathlib import Path
from typing import Any, Dict, List, Tuple, Set

sys.path.insert(0, os.path.abspath("."))
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass

from lotofacil_modo4.etapa1_regras_oficiais import validar_aposta_lotofacil
from lotofacil_modo4.etapa2_funcao_objetivo import avaliar_carteira_etapa2
from lotofacil_modo4.etapa2_referencia_independente import avaliar_carteira_referencia_independente
from lotofacil_modo4.etapa4_arquitetura_adaptativa import (
    executar_arquitetura_adaptativa_etapa4,
    MotorIncrementalOtimizadoEtapa4,
)

def calcular_metricas_completas(carteira: List[List[int]], pool: Tuple[int, ...]) -> Dict[str, Any]:
    jogos = [tuple(sorted(jg)) for jg in carteira]
    j = len(jogos)
    
    # Unicidade
    duplicatas = j - len(set(jogos))
    
    # Coberturas t=1..4
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
                        
    # Cota minima de variancia SS_min
    # M_livre = 15 * 2000 = 30.000. Com pool de 25, 30000 % 25 = 0, logo r = 0 e SS_min = 0.
    mu = (15 * j) / len(pool)
    ss_obs = sum((freq_dezenas[d] - mu) ** 2 for d in pool)
    _, rem = divmod(15 * j, len(pool))
    ss_min = rem * (1.0 - rem / len(pool))
    
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
    }

def main():
    print("=" * 80)
    print("GERACAO E HOMOLOGACAO DO CATALOGO OFICIAL CANONICO J=2.000 (LOTOFACIL MODO 4)")
    print("=" * 80)
    
    # 0. Protecao e Auditoria Prévia da Carteira Canônica J=1.000
    dir_catalogo = Path("catalogo_lotofacil_10000")
    caminho_cat_1000 = dir_catalogo / "lotofacil_carteira_1000.json"
    if not caminho_cat_1000.is_file():
        raise FileNotFoundError(f"FALHA CRITICA: Catalogo J=1000 nao encontrado em {caminho_cat_1000}!")
    
    with open(caminho_cat_1000, "rb") as f_prev:
        hash_cat_1000_previo = hashlib.sha256(f_prev.read()).hexdigest()
    print(f"Auditoria previa J=1000 preservada. SHA-256: {hash_cat_1000_previo}")
    
    # 1. Parametros formalmente delimitados na Etapa 2.2
    quantidade_jogos = 2000
    b_cand = 32
    semente = 2027
    max_avaliacoes = b_cand * quantidade_jogos  # 64.000 avaliacoes
    
    print(f"Parametros Selecionados:")
    print(f"  Quantidade de jogos (J): {quantidade_jogos}")
    print(f"  B_cand orcamento-base:   {b_cand}")
    print(f"  Semente deterministica:  {semente}")
    print(f"  Teto de avaliacoes:      {max_avaliacoes}")
    print(f"  Distribuicao planejada:  16 (jogo 1) + 63.936 (jogos 2..1999) + 48 (jogo 2000) = 64.000")
    print("-" * 80)
    
    # 2. Executar geracao oficial com arquitetura adaptativa
    print("\nExecutando geracao da carteira oficial J=2000...")
    t0 = time.perf_counter()
    res = executar_arquitetura_adaptativa_etapa4(
        pool=range(1, 26),
        quantidade_jogos=quantidade_jogos,
        tamanho_aposta=15,
        semente=semente,
        max_avaliacoes=max_avaliacoes,
        forcar_algoritmo="algoritmo_guloso",
        medir_memoria=True,
    )
    t1 = time.perf_counter()
    duracao_geracao = t1 - t0
    print(f"Geracao concluida em {duracao_geracao:.3f} s.")
    
    # Formatacao canônica e garantia de input estritamente identico para validadores
    carteira_canonica = [list(sorted(jg)) for jg in sorted(tuple(sorted(x)) for x in res["carteira"])]
    pesos = res["especificacao"]["pesos"]
    
    # 3. Hash canônico estrito dos jogos
    json_jogos_compacto = json.dumps(carteira_canonica, separators=(",", ":"))
    sha256_jogos = hashlib.sha256(json_jogos_compacto.encode("utf-8")).hexdigest()
    print(f"SHA-256 Jogos Canonicos: {sha256_jogos}")
    
    # 4. Tripla Validacao Matematica (mesma carteira_canonica nos 3 validadores)
    print("\nExecutando Tripla Validacao Matematica...")
    # Validador 1: Motor incremental Etapa 4
    motor = MotorIncrementalOtimizadoEtapa4(carteira_canonica, tuple(range(1, 26)), (), pesos)
    f_e4 = motor.score_atual()
    
    # Validador 2: Etapa 2 oficial
    ev_e2 = avaliar_carteira_etapa2(carteira_canonica)
    f_e2 = float(ev_e2["funcao_objetivo_F"])
    
    # Validador 3: Referencia independente
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
    print(f"  |E2 - Ref|:               {div_e2_ref:.2e}")
    
    aprovado_1e12 = (div_e4_e2 <= 1e-12) and (div_e4_ref <= 1e-12)
    if not aprovado_1e12:
        raise ValueError("FALHA CRITICA: Divergencia matematica superior a 1e-12!")
    print("  Status Tripla Validacao: APROVADO (tolerancia <= 1e-12 rigorosamente respeitada)")
    
    # 5. Metricas Combinatorias e de Cobertura
    metricas = calcular_metricas_completas(carteira_canonica, tuple(range(1, 26)))
    metricas["funcao_objetivo_F"] = round(f_e4, 12)
    metricas["componentes"] = dict(ev_e2["componentes"])
    metricas["p2_covariancia_esperada"] = float(ev_e2["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]["3_probabilidade_conjunta_carteira"]["variancia_bilhetes_dependente_exata"])
    
    # Validacao de requisitos de homologacao estritos (sem intervalos de escore artificiais)
    if metricas["duplicatas"] != 0:
        raise ValueError(f"FALHA CRITICA: Carteira contem {metricas['duplicatas']} jogos duplicados!")
    if metricas["quadras_cobertas"] < 12650:
        raise ValueError(f"FALHA CRITICA: Cobertura de quadras incompleta ({metricas['quadras_cobertas']}/12650)!")
    if metricas["funcao_objetivo_F"] < 0.965:
        raise ValueError(f"FALHA CRITICA: Escore F={metricas['funcao_objetivo_F']} abaixo do patamar minimo de 0.965!")
    
    print(f"\nMetricas Combinatorias Observadas:")
    print(f"  Duplicatas: {metricas['duplicatas']} (Unicidade: {metricas['unicidade_pct']}%)")
    print(f"  Cobertura t=1 (dezenas): {metricas['cobertura_t1_pct']}% (25/25)")
    print(f"  Cobertura t=2 (pares):   {metricas['cobertura_t2_pct']}% (300/300)")
    print(f"  Cobertura t=3 (trincas): {metricas['cobertura_t3_pct']}% (2300/2300)")
    print(f"  Cobertura t=4 (quadras): {metricas['cobertura_t4_pct']}% ({metricas['quadras_cobertas']}/12650)")
    print(f"  SS_obs: {metricas['ss_observado']} | SS_min teorico: {metricas['ss_minimo']} | Media mu: {metricas['media_frequencia_dezena']}")
    print(f"  Escore F(C) medido: {metricas['funcao_objetivo_F']}")
    
    # 6. Montagem do Catalogo Estruturado J=2.000
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
        "b_cand_base": b_cand,
        "orcamento_max_avaliacoes": max_avaliacoes,
        "sha256_jogos_canonicos": sha256_jogos,
        "sha256_documento_catalogo": None,
        "telemetria": {
            "avaliacoes_efetivas": res["telemetria"]["avaliacoes_efetivas"],
            "taxa_utilizacao_orcamento": res["telemetria"]["taxa_utilizacao_orcamento"],
            "tempo_total_segundos": round(duracao_geracao, 4),
            "memoria_pico_mb": res["telemetria"]["memoria_pico_mb"],
            "criterio_parada": res["telemetria"]["criterio_parada"],
            "detalhamento_avaliacoes": {
                "jogo_1_inicial": 16,
                "jogos_2_a_1999_intermediarios": 63936,
                "jogo_2000_final": 48,
                "total_avaliacoes": 64000,
            },
        },
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
    
    # Hash documental canônico (excluindo sha256_documento_catalogo)
    doc_sem_hash = {k: v for k, v in catalogo_dict.items() if k != "sha256_documento_catalogo"}
    hash_doc_canonico = hashlib.sha256(
        json.dumps(doc_sem_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    catalogo_dict["sha256_documento_catalogo"] = hash_doc_canonico
    
    # 7. Persistência estrita do arquivo JSON de 2.000 jogos
    with open(caminho_catalogo, "w", encoding="utf-8") as f:
        json.dump(catalogo_dict, f, indent=2, ensure_ascii=False)
        
    # 8. Hash do arquivo físico em disco para manifesto (.sha256)
    with open(caminho_catalogo, "rb") as f:
        sha256_arquivo_fisico = hashlib.sha256(f.read()).hexdigest()
        
    caminho_manifesto = dir_catalogo / "lotofacil_carteira_2000.json.sha256"
    with open(caminho_manifesto, "w", encoding="utf-8") as f:
        f.write(f"{sha256_arquivo_fisico}  lotofacil_carteira_2000.json\n")
        
    # 9. Verificacao de Nao Regressao e Intocabilidade de J=1.000
    with open(caminho_cat_1000, "rb") as f_post:
        hash_cat_1000_pos = hashlib.sha256(f_post.read()).hexdigest()
    if hash_cat_1000_pos != hash_cat_1000_previo:
        raise RuntimeError("FALHA CRITICA DE GOVERNANCA: O catalogo de 1.000 jogos foi alterado durante a geracao de 2.000!")
    print(f"Verificacao pos-geracao: Catalogo J=1000 100% preservado (hash {hash_cat_1000_pos}).")
    
    print(f"\nCatálogo Oficial J=2000 Persistido com Sucesso:")
    print(f"  Arquivo JSON: {caminho_catalogo}")
    print(f"  Tamanho: {os.path.getsize(caminho_catalogo):,} bytes")
    print(f"  SHA-256 Jogos Canônicos: {sha256_jogos}")
    print(f"  SHA-256 Estrutural Documental: {hash_doc_canonico}")
    print(f"  SHA-256 Arquivo Físico: {sha256_arquivo_fisico}")
    print(f"  Manifesto: {caminho_manifesto}")
    print("=" * 80)

if __name__ == "__main__":
    main()
