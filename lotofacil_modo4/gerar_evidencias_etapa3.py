# -*- coding: utf-8 -*-
"""
GERADOR DE EVIDENCIAS VERIFICAVEIS: ETAPA 3 (LOTOFACIL MODO 4)
=================================================================
Executa benchmarks comparativos controlados sob condicoes estritamente
identicas para todos os algoritmos da Etapa 3:
  - Instancias pequenas com prova de otimo global (busca_exata_pequena vs heuristicas vs baseline);
  - Instancias medias e grandes (pools 20, 22, 25), modos de fixas (`todos_os_jogos` e
    `composicao_pool`), apostas multiplas (m=17) e carteiras mistas (m=16 + 3x15);
  - Planejamento exato por orcamento e comparacao contra referencia independente;
  - Emissao de `auditoria/lotofacil_modo4/etapa_03_evidencias.json` e
    `auditoria/lotofacil_modo4/ETAPA_03_ALGORITMOS_DE_OTIMIZACAO.md`.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Tuple

from .etapa1_regras_oficiais import CLAUSULA_MATEMATICA_OBRIGATORIA, DEZENAS_DISPONIVEIS
from .etapa2_funcao_objetivo import CATEGORIAS_PROVA_CIENTIFICA
from .etapa3_otimizadores import (
    ALGORITMOS_ETAPA3,
    ESPECIFICACAO_ALGORITMOS_ETAPA3,
    VERSAO_OTIMIZADOR_ETAPA3,
    comparar_algoritmos_etapa3,
    otimizar_carteira_etapa3,
    planejar_composicoes_orcamento,
)
from .etapa3_referencia_independente import verificar_equivalencia_etapa3_contra_referencia
from .sincronizador_caixa import calcular_sha256_arquivo


def _compactar_comparacao(comp: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "escopo_epistemologico": comp["escopo_epistemologico"],
        "condicoes_identicas": comp["condicoes_identicas"],
        "status_busca_exata": comp["status_busca_exata"],
        "melhor_algoritmo_empirico": comp["melhor_algoritmo_empirico"],
        "tabela_comparativa": comp["tabela_comparativa"],
    }


def gerar_pacote_etapa3(diretorio_repo: str | None = None) -> Dict[str, Any]:
    base_dir = diretorio_repo or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta_aud = os.path.join(base_dir, "auditoria", "lotofacil_modo4")
    os.makedirs(pasta_aud, exist_ok=True)

    instancias_cfg: List[Tuple[str, Dict[str, Any]]] = [
        (
            "inst_peq_p16_J4_exata",
            dict(
                pool=range(1, 17),
                fixas=(),
                bloqueadas=range(21, 26),
                modo_fixas="todos_os_jogos",
                quantidade_jogos=4,
                tamanho_aposta=15,
                semente=42,
                max_avaliacoes=250,
                max_iteracoes=150,
                incluir_exato_se_viavel=True,
                limite_combinacoes_exatas=10_000,
            ),
        ),
        (
            "inst_peq_p18_f11_J3_exata",
            dict(
                pool=range(1, 19),
                fixas=range(1, 12),
                bloqueadas=range(19, 26),
                modo_fixas="todos_os_jogos",
                quantidade_jogos=3,
                tamanho_aposta=15,
                semente=42,
                max_avaliacoes=250,
                max_iteracoes=150,
                incluir_exato_se_viavel=True,
                limite_combinacoes_exatas=10_000,
            ),
        ),
        (
            "inst_med_p20_J10_fix3_todos_jogos_s42",
            dict(
                pool=range(1, 21),
                fixas=(1, 2, 3),
                bloqueadas=(21, 22, 23, 24, 25),
                modo_fixas="todos_os_jogos",
                quantidade_jogos=10,
                tamanho_aposta=15,
                semente=42,
                max_avaliacoes=300,
                max_iteracoes=150,
                incluir_exato_se_viavel=False,
            ),
        ),
        (
            "inst_med_p20_J10_fix3_todos_jogos_s101",
            dict(
                pool=range(1, 21),
                fixas=(1, 2, 3),
                bloqueadas=(21, 22, 23, 24, 25),
                modo_fixas="todos_os_jogos",
                quantidade_jogos=10,
                tamanho_aposta=15,
                semente=101,
                max_avaliacoes=300,
                max_iteracoes=150,
                incluir_exato_se_viavel=False,
            ),
        ),
        (
            "inst_med_p22_J12_f16_composicao_pool",
            dict(
                pool=range(1, 23),
                fixas=range(1, 17),  # 16 fixas no pool (> m=15)
                bloqueadas=(23, 24, 25),
                modo_fixas="composicao_pool",
                quantidade_jogos=12,
                tamanho_aposta=15,
                semente=42,
                max_avaliacoes=300,
                max_iteracoes=150,
                incluir_exato_se_viavel=False,
            ),
        ),
        (
            "inst_grd_p25_orc56_J16_simples",
            dict(
                pool=DEZENAS_DISPONIVEIS,
                fixas=(),
                bloqueadas=(),
                modo_fixas="todos_os_jogos",
                orcamento_brl="56.00",
                tamanho_aposta=15,
                semente=42,
                max_avaliacoes=320,
                max_iteracoes=160,
                incluir_exato_se_viavel=False,
            ),
        ),
        (
            "inst_mult_p20_J4_m17",
            dict(
                pool=range(1, 21),
                fixas=(),
                bloqueadas=(21, 22, 23, 24, 25),
                modo_fixas="todos_os_jogos",
                quantidade_jogos=4,
                tamanho_aposta=17,
                semente=42,
                max_avaliacoes=200,
                max_iteracoes=100,
                incluir_exato_se_viavel=False,
            ),
        ),
        (
            "inst_mult_mista_p20_m16_mais_3x15",
            dict(
                pool=range(1, 21),
                fixas=(1, 2),
                bloqueadas=(21, 22, 23, 24, 25),
                modo_fixas="todos_os_jogos",
                tamanhos_jogos=(16, 15, 15, 15),
                semente=42,
                max_avaliacoes=200,
                max_iteracoes=100,
                incluir_exato_se_viavel=False,
            ),
        ),
    ]

    benchmarks: Dict[str, Any] = {}
    verificacoes_ref: List[Dict[str, Any]] = []
    vitorias_por_algoritmo: Dict[str, int] = {a: 0 for a in ALGORITMOS_ETAPA3}

    for nome_inst, cfg in instancias_cfg:
        comp = comparar_algoritmos_etapa3(**cfg)
        benchmarks[nome_inst] = _compactar_comparacao(comp)
        vencedor = comp["melhor_algoritmo_empirico"]
        vitorias_por_algoritmo[vencedor] = vitorias_por_algoritmo.get(vencedor, 0) + 1

        for nome_alg, res_alg in comp["resultados_completos"].items():
            chk = verificar_equivalencia_etapa3_contra_referencia(res_alg)
            if not chk["equivalente_1e_12"]:
                raise RuntimeError(
                    f"Falha de equivalencia na instancia '{nome_inst}', algoritmo '{nome_alg}': {chk}"
                )
            verificacoes_ref.append(
                {
                    "instancia": nome_inst,
                    "algoritmo": nome_alg,
                    "conforme_restricoes": chk["conforme_restricoes"],
                    "diferenca_F_modulo": chk["diferenca_F_modulo"],
                }
            )

    # Teste de reprodutibilidade estrita (duas execucoes com mesma semente)
    r_a = otimizar_carteira_etapa3(
        algoritmo="estrategia_combinada",
        pool=range(1, 21),
        fixas=(1, 2, 3),
        bloqueadas=(21, 22, 23, 24, 25),
        quantidade_jogos=8,
        semente=777,
        max_avaliacoes=200,
    )
    r_b = otimizar_carteira_etapa3(
        algoritmo="estrategia_combinada",
        pool=range(1, 21),
        fixas=(1, 2, 3),
        bloqueadas=(21, 22, 23, 24, 25),
        quantidade_jogos=8,
        semente=777,
        max_avaliacoes=200,
    )
    reprodutibilidade = {
        "mesma_semente_identica_sha256": r_a["sha256_execucao"] == r_b["sha256_execucao"],
        "mesma_carteira_canonica": r_a["carteira_otimizada"] == r_b["carteira_otimizada"],
        "sha256_execucao": r_a["sha256_execucao"],
        "historico_utilizado": r_a["historico_utilizado"],
    }

    composicoes_orc_600 = planejar_composicoes_orcamento("600.00", tamanho_pool=20, quantidade_fixas_por_jogo=0)

    hashes_codigo = {
        "lotofacil_modo4/etapa3_otimizadores.py": calcular_sha256_arquivo(
            os.path.join(base_dir, "lotofacil_modo4", "etapa3_otimizadores.py")
        ),
        "lotofacil_modo4/etapa3_referencia_independente.py": calcular_sha256_arquivo(
            os.path.join(base_dir, "lotofacil_modo4", "etapa3_referencia_independente.py")
        ),
        "lotofacil_modo4/gerar_evidencias_etapa3.py": calcular_sha256_arquivo(
            os.path.join(base_dir, "lotofacil_modo4", "gerar_evidencias_etapa3.py")
        ),
        "testes/test_lotofacil_modo4_etapa3.py": (
            calcular_sha256_arquivo(os.path.join(base_dir, "testes", "test_lotofacil_modo4_etapa3.py"))
            if os.path.isfile(os.path.join(base_dir, "testes", "test_lotofacil_modo4_etapa3.py"))
            else None
        ),
    }

    evidencias = {
        "etapa": "ETAPA_3_ALGORITMOS_DE_OTIMIZACAO",
        "versao_otimizador": VERSAO_OTIMIZADOR_ETAPA3,
        "categorias_prova_cientifica": dict(CATEGORIAS_PROVA_CIENTIFICA),
        "especificacao_algoritmos": {k: dict(v) for k, v in ESPECIFICACAO_ALGORITMOS_ETAPA3.items()},
        "benchmarks_controlados": benchmarks,
        "resumo_vitorias_instancias_testadas": vitorias_por_algoritmo,
        "verificacao_referencia_independente": {
            "total_execucoes_conferidas": len(verificacoes_ref),
            "todas_equivalentes_1e_12_e_conformes": all(
                v["conforme_restricoes"] and v["diferenca_F_modulo"] <= 1e-12 for v in verificacoes_ref
            ),
            "maior_diferenca_F_observada": max(v["diferenca_F_modulo"] for v in verificacoes_ref),
        },
        "reprodutibilidade_deterministica": reprodutibilidade,
        "exemplo_planejamento_orcamento_600_brl_p20": composicoes_orc_600[:6],
        "hashes_artefatos_etapa3": hashes_codigo,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }

    caminho_json = os.path.join(pasta_aud, "etapa_03_evidencias.json")
    with open(caminho_json, "w", encoding="utf-8") as fj:
        json.dump(evidencias, fj, ensure_ascii=False, indent=2)
        fj.write("\n")

    # Documento Markdown rigoroso (sem travessao em-dash ou en-dash)
    linhas: List[str] = [
        "# LOTOFACIL MODO 4 : ETAPA 3 (Especificacao dos Algoritmos de Otimizacao)",
        "",
        "## 1. Arquitetura, Especificacao e Complexidade dos Algoritmos",
        "| Algoritmo | Categoria | Complexidade Tempo | Complexidade Espaco | Garante Otimo Global? |",
        "| :--- | :--- | :--- | :--- | :---: |",
    ]
    for nome_alg in ALGORITMOS_ETAPA3:
        sp = ESPECIFICACAO_ALGORITMOS_ETAPA3[nome_alg]
        g_txt = "Sim (quando C(K,J) <= limite)" if sp["garante_otimo_global"] else "Nao (heuristica / baseline)"
        linhas.append(
            f"| `{nome_alg}` | `{sp['categoria']}` | `{sp['complexidade_tempo']}` | `{sp['complexidade_espaco']}` | {g_txt} |"
        )

    linhas.extend(
        [
            "",
            "## 2. Comparacao Empirica Controlada Sob Condicoes Identicas",
            "Todas as comparacoes abaixo utilizam identico pool, mesmas restricoes (`todos_os_jogos` ou `composicao_pool`), mesma quantidade de jogos e dimensoes, mesmo orcamento, mesma funcao objetivo $F_{\\text{MODO4}}$, mesma semente SHA-256 e mesmo teto de avaliacoes (`max_avaliacoes`).",
            "",
        ]
    )

    for nome_inst, bm in benchmarks.items():
        cond = bm["condicoes_identicas"]
        linhas.append(
            f"### 2.1 Instancia `{nome_inst}` (`escopo: {bm['escopo_epistemologico']}`)"
        )
        linhas.append(
            f"- **Configuracao:** pool=`{cond['tamanho_pool']}`, fixas=`{len(cond['fixas'])}`, "
            f"bloqueadas=`{len(cond['bloqueadas'])}`, modo=`{cond['modo_fixas']}`, "
            f"jogos=`{len(cond['tamanhos_jogos'])}` (`{sorted(set(cond['tamanhos_jogos']))}`), "
            f"custo=`R$ {cond['custo_total_brl']}`, semente=`{cond['semente']}`, teto_eval=`{cond['max_avaliacoes']}`."
        )
        linhas.append("")
        linhas.append(
            "| Pos | Algoritmo | Score F(C) | Ganho vs Aleatorio | Gap p/ Exato | Pares | Trincas | I_max | Var(N_prem) | Avaliacoes | Tempo (s) |"
        )
        linhas.append("| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |")
        for row in bm["tabela_comparativa"]:
            ganho = f"{row['ganho_sobre_aleatorio']:+.6f}" if row["ganho_sobre_aleatorio"] is not None else "N/A"
            gap = f"{row['gap_para_otimo_exato']:.6f}" if row["gap_para_otimo_exato"] is not None else "N/A"
            linhas.append(
                f"| {row['posicao']} | `{row['algoritmo']}` | {row['funcao_objetivo_F']:.6f} | {ganho} | {gap} | "
                f"{row['pares_cobertos']} | {row['trincas_cobertas']} | {row['intersecao_maxima']} | "
                f"{row['variancia_N_prem']:.4f} | {row['avaliacoes']} | {row['tempo_segundos']:.4f} |"
            )
        linhas.append("")

    linhas.extend(
        [
            "## 3. Conferencia Contra Referencia Independente e Reprodutibilidade",
            f"- **Execucoes conferidas vs referencia independente:** `{len(verificacoes_ref)}/{len(verificacoes_ref)}` conformes e equivalentes.",
            f"- **Maior divergencia numerica observada em F(C):** `{evidencias['verificacao_referencia_independente']['maior_diferenca_F_observada']:.2e}` (limite `1.00e-12`).",
            f"- **Reprodutibilidade sob mesma semente (`777`):** `SHA-256` identico (`{reprodutibilidade['mesma_semente_identica_sha256']}`), carteira identica (`{reprodutibilidade['mesma_carteira_canonica']}`), `historico_utilizado={reprodutibilidade['historico_utilizado']}`.",
            "",
            "## 4. Limitacao de Escopo das Comparacoes (Ressalva 2.3)",
            "- As instancias `inst_peq_p16_J4_exata` e `inst_peq_p18_f11_J3_exata` pertencem a categoria `PROVA_OTIMO_GLOBAL_INSTANCIA_PEQUENA`, onde a busca exata enumerou todas as carteiras viaveis do espaco.",
            "- As demais instancias pertencem a categoria `COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`, medindo desempenho empirico dentro dos parametros e orcamentos avaliados sem declarar superioridade universal absoluta.",
            "",
            "## 5. Clausula Obrigatoria de Veracidade Cientifica",
            f"> {CLAUSULA_MATEMATICA_OBRIGATORIA}",
            "",
        ]
    )

    caminho_md = os.path.join(pasta_aud, "ETAPA_03_ALGORITMOS_DE_OTIMIZACAO.md")
    with open(caminho_md, "w", encoding="utf-8") as fm:
        fm.write("\n".join(linhas))

    return {
        "evidencias_json": caminho_json,
        "relatorio_md": caminho_md,
        "resumo_vitorias_instancias_testadas": vitorias_por_algoritmo,
        "verificacao_referencia_independente": evidencias["verificacao_referencia_independente"],
        "reprodutibilidade_deterministica": reprodutibilidade,
        "hashes_artefatos_etapa3": hashes_codigo,
    }


if __name__ == "__main__":
    print(json.dumps(gerar_pacote_etapa3(), ensure_ascii=False, indent=2))
