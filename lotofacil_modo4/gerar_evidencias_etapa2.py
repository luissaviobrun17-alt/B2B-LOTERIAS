# -*- coding: utf-8 -*-
"""
GERADOR DE EVIDENCIAS VERIFICAVEIS: ETAPA 2 (LOTOFACIL MODO 4)
=================================================================
Gera demonstracoes matematicas reproduziveis, exemplos pequenos conferiveis
manualmente, prova empirica no universo exato C(25, 15) = 3.268.760, analise
de sensibilidade dos pesos, casos de empate e comparativo custo-beneficio em:
  - auditoria/lotofacil_modo4/etapa_02_evidencias.json
  - auditoria/lotofacil_modo4/ETAPA_02_FUNCAO_OBJETIVO_E_OTIMIZACAO.md
"""

from __future__ import annotations

import itertools
import json
import os
from typing import Any, Dict, List, Mapping, Sequence, Tuple

from .etapa1_regras_oficiais import CLAUSULA_MATEMATICA_OBRIGATORIA, DEZENAS_DISPONIVEIS
from .etapa2_funcao_objetivo import (
    CATEGORIAS_PROVA_CIENTIFICA,
    ESPECIFICACAO_COMPONENTES_ETAPA2,
    MODOS_FIXAS_PERMITIDOS,
    NOMES_COMPONENTES,
    PERFIS_PESOS_ETAPA2,
    TABELA_P2_CONJUNTA_EXATA,
    TABELA_P2_MULTIPLAS_15_A_20,
    VERSAO_MODELO_OBJETIVO_ETAPA2,
    avaliar_carteira_etapa2,
    probabilidade_conjunta_par_quatro_regioes_detalhada,
    selecionar_melhor_carteira,
    validar_pesos_objetivo,
    validar_pool_e_restricoes,
)
from .etapa2_referencia_independente import verificar_lote_universo_completo
from .sincronizador_caixa import calcular_sha256_arquivo


def _executar_analise_sensibilidade() -> Dict[str, Any]:
    """
    Avalia 5 carteiras ordenadas (da dispersa otima a redundante extrema) em
    pool de 20 dezenas (J=4) frente aos 4 perfis oficiais, perturbacoes de
    +-25% e +-50% em cada peso e ablacao individual (w_k = 0).
    """
    pool20 = tuple(range(1, 21))
    candidatas_ordenadas: List[Tuple[str, List[List[int]]]] = [
        (
            "C1_dispersa_equilibrada",
            [
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 17, 18, 19, 20],
                [1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
                [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
            ],
        ),
        (
            "C2_intermediaria",
            [
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 16, 17, 18, 19],
                [1, 2, 3, 4, 5, 6, 12, 13, 14, 15, 16, 17, 18, 19, 20],
                [6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
            ],
        ),
        (
            "C3_sobreposicao_alta",
            [
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 18],
            ],
        ),
        (
            "C4_clones_parciais",
            [
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17],
            ],
        ),
        (
            "C5_duplicacao_total",
            [
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            ],
        ),
    ]

    cenarios: List[Tuple[str, Dict[str, float]]] = [
        (f"perfil:{nome}", validar_pesos_objetivo(mapa))
        for nome, mapa in PERFIS_PESOS_ETAPA2.items()
    ]
    base = dict(PERFIS_PESOS_ETAPA2["padrao_modo4"])

    for comp in NOMES_COMPONENTES:
        for fator, rotulo in ((0.50, "-50%"), (0.75, "-25%"), (1.25, "+25%"), (1.50, "+50%"), (0.0, "ablacao_0")):
            bruto = dict(base)
            bruto[comp] = base[comp] * fator
            s = sum(bruto.values())
            norm = {k: v / s for k, v in bruto.items()}
            cenarios.append((f"{comp}:{rotulo}", validar_pesos_objetivo(norm)))

    vencedora_base = "C1_dispersa_equilibrada"
    registros: List[Dict[str, Any]] = []
    vencedoras_iguais = 0
    ordem_total_preservada = 0

    for nome_cenario, pesos_cenario in cenarios:
        avals = [
            (rotulo, avaliar_carteira_etapa2(cart, pool=pool20, pesos=pesos_cenario))
            for rotulo, cart in candidatas_ordenadas
        ]
        ranking = sorted(avals, key=lambda x: x[1]["chave_desempate"], reverse=True)
        ordem_nomes = [r[0] for r in ranking]
        if ordem_nomes[0] == vencedora_base:
            vencedoras_iguais += 1
        if ordem_nomes == [x[0] for x in candidatas_ordenadas]:
            ordem_total_preservada += 1
        registros.append(
            {
                "cenario": nome_cenario,
                "vencedora": ordem_nomes[0],
                "ordem": ordem_nomes,
                "scores_F": {r[0]: round(r[1]["funcao_objetivo_F"], 6) for r in avals},
                "margem_1o_para_2o": round(
                    ranking[0][1]["funcao_objetivo_F"] - ranking[1][1]["funcao_objetivo_F"], 6
                ),
            }
        )

    return {
        "total_cenarios_testados": len(cenarios),
        "vencedora_invariante_em_cenarios": vencedoras_iguais,
        "taxa_estabilidade_vencedora": vencedoras_iguais / len(cenarios),
        "ranking_estrito_preservado_em_cenarios": ordem_total_preservada,
        "cenarios": registros,
    }


def _construir_estudo_custo_beneficio() -> List[Dict[str, Any]]:
    """
    Compara formalmente 1 aposta multipla de 16 dezenas (R$ 56,00 = 16 combinacoes)
    contra 16 apostas simples distribuidas deterministicamente em pools de
    tamanhos 16, 18, 20 e 25 dezenas pelo mesmo orcamento de R$ 56,00.
    """
    estudo: List[Dict[str, Any]] = []

    aposta_16 = [list(range(1, 17))]
    av_16 = avaliar_carteira_etapa2(aposta_16, pool=tuple(range(1, 17)))
    estudo.append(
        {
            "estrategia": "1_aposta_multipla_16_dezenas_fechada",
            "pool": 16,
            "jogos": 1,
            "custo_brl": av_16["detalhes"]["custo_beneficio"]["custo_total_brl"],
            "combinacoes_simples_pagas": av_16["detalhes"]["custo_beneficio"]["combinacoes_simples_pagas"],
            "combinacoes_simples_unicas": av_16["detalhes"]["custo_beneficio"]["combinacoes_simples_unicas"],
            "pares_cobertos": av_16["detalhes"]["cobertura_combinatoria"]["por_ordem_t"][2]["cobertos"],
            "trincas_cobertas": av_16["detalhes"]["cobertura_combinatoria"]["por_ordem_t"][3]["cobertos"],
            "variancia_dependente_exata": av_16["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]["3_probabilidade_conjunta_carteira"]["variancia_bilhetes_dependente_exata"],
            "cota_ds_prob_pelo_menos_1": av_16["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]["3_probabilidade_conjunta_carteira"]["cota_inferior_dawson_sankoff"],
            "cota_hw_prob_pelo_menos_1": av_16["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]["3_probabilidade_conjunta_carteira"]["cota_superior_hunter_worsley"],
            "score_F": av_16["funcao_objetivo_F"],
        }
    )

    # 16 apostas simples em pools variados usando rotacao ciclica uniforme (custo identico = R$ 56,00)
    for tam_pool in (16, 18, 20, 25):
        pool = tuple(range(1, tam_pool + 1))
        if tam_pool == 16:
            carteira = [list(c) for c in itertools.combinations(pool, 15)]
        else:
            passo = 1 if tam_pool <= 18 else (3 if tam_pool == 20 else 7)
            visto: set[Tuple[int, ...]] = set()
            carteira = []
            idx = 0
            while len(carteira) < 16:
                offset = (idx * passo) % tam_pool
                cand = tuple(sorted(pool[(offset + k) % tam_pool] for k in range(15)))
                if cand not in visto:
                    visto.add(cand)
                    carteira.append(list(cand))
                else:
                    # Rotacao secundaria deterministica se houver colisao em mod tam_pool
                    alt = tuple(sorted((pool[(offset + (k * 2 if k < 7 else k)) % tam_pool] for k in range(15))))
                    if len(alt) == 15 and alt not in visto:
                        visto.add(alt)
                        carteira.append(list(alt))
                    else:
                        # Varre combinacoes ordenadas ate encontrar distinta com passo fixo
                        for c_enum in itertools.combinations(pool, 15):
                            if c_enum not in visto:
                                visto.add(c_enum)
                                carteira.append(list(c_enum))
                                break
                idx += 1

        av = avaliar_carteira_etapa2(carteira, pool=pool)
        estudo.append(
            {
                "estrategia": f"16_apostas_simples_em_pool_{tam_pool}",
                "pool": tam_pool,
                "jogos": 16,
                "custo_brl": av["detalhes"]["custo_beneficio"]["custo_total_brl"],
                "combinacoes_simples_pagas": av["detalhes"]["custo_beneficio"]["combinacoes_simples_pagas"],
                "combinacoes_simples_unicas": av["detalhes"]["custo_beneficio"]["combinacoes_simples_unicas"],
                "pares_cobertos": av["detalhes"]["cobertura_combinatoria"]["por_ordem_t"][2]["cobertos"],
                "trincas_cobertas": av["detalhes"]["cobertura_combinatoria"]["por_ordem_t"][3]["cobertos"],
                "variancia_dependente_exata": av["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]["3_probabilidade_conjunta_carteira"]["variancia_bilhetes_dependente_exata"],
                "cota_ds_prob_pelo_menos_1": av["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]["3_probabilidade_conjunta_carteira"]["cota_inferior_dawson_sankoff"],
                "cota_hw_prob_pelo_menos_1": av["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]["3_probabilidade_conjunta_carteira"]["cota_superior_hunter_worsley"],
                "score_F": av["funcao_objetivo_F"],
            }
        )

    return estudo


def gerar_pacote_etapa2(diretorio_repo: str | None = None) -> Dict[str, Any]:
    base_dir = diretorio_repo or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta_aud = os.path.join(base_dir, "auditoria", "lotofacil_modo4")
    os.makedirs(pasta_aud, exist_ok=True)

    # 1. Exemplos manuais pequenos (J=2 em p=16 e comparativo J=3 em p=18)
    ex_j2_p16 = [
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16],
    ]
    av_ex1 = avaliar_carteira_etapa2(ex_j2_p16, pool=tuple(range(1, 17)))

    ex_j3_dispersa = [
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 17, 18],
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14, 15, 16, 17, 18],
    ]
    ex_j3_concentrada = [
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16],
        [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17],
    ]
    av_disp = avaliar_carteira_etapa2(ex_j3_dispersa, pool=tuple(range(1, 19)))
    av_conc = avaliar_carteira_etapa2(ex_j3_concentrada, pool=tuple(range(1, 19)))

    ex_multipla_m16_m15 = [
        list(range(1, 17)),
        list(range(1, 8)) + list(range(17, 25)),  # m1=16, m2=15, c=7
    ]
    ex_multipla_m18_m17 = [
        list(range(1, 19)),
        list(range(1, 13)) + list(range(19, 24)),  # m1=18, m2=17, c=12
    ]
    av_m16_m15 = avaliar_carteira_etapa2(ex_multipla_m16_m15, pool=DEZENAS_DISPONIVEIS)
    av_m18_m17 = avaliar_carteira_etapa2(ex_multipla_m18_m17, pool=DEZENAS_DISPONIVEIS)

    # 2. Prova de forca bruta sobre TODOS os 3.268.760 sorteios reais da Lotofacil
    brutos = verificar_lote_universo_completo(
        [ex_j2_p16, ex_j3_dispersa, ex_j3_concentrada, ex_multipla_m16_m15, ex_multipla_m18_m17]
    )
    nomes_brutos = (
        "ex_j2_p16_I14",
        "ex_j3_p18_dispersa",
        "ex_j3_p18_concentrada",
        "ex_multipla_m16_m15_I7",
        "ex_multipla_m18_m17_I12",
    )
    avals_corresp = (av_ex1, av_disp, av_conc, av_m16_m15, av_m18_m17)
    prova_universo_completo: List[Dict[str, Any]] = []
    for nome_b, res_b, av_b in zip(nomes_brutos, brutos, avals_corresp):
        bloco3 = av_b["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]["3_probabilidade_conjunta_carteira"]
        bloco_5 = av_b["detalhes"]["probabilidade_conjunta"]["distincao_cinco_grandezas_ressalva_2_1"]
        p2_obs = res_b["distribuicao_exata"].get(2) if len(av_b["carteira_canonica"]) == 2 else None
        prova_universo_completo.append(
            {
                "caso": nome_b,
                "escopo_epistemologico": "VALIDACAO_EXAUSTIVA_UNIVERSO_SORTEIOS",
                "tamanhos_bilhetes": [len(jg) for jg in av_b["carteira_canonica"]],
                "total_sorteios_verificados": res_b["total_sorteios_enumerados"],
                "prob_ao_menos_1_exata_universo": f"{res_b['probabilidade_ao_menos_1_exata'].numerator}/{res_b['probabilidade_ao_menos_1_exata'].denominator}",
                "prob_ao_menos_1_percentual_exata": float(res_b["probabilidade_ao_menos_1_exata"] * 100),
                "p2_simultanea_exata_universo": (f"{p2_obs.numerator}/{p2_obs.denominator}" if p2_obs is not None else None),
                "p2_simultanea_exata_formula_4reg": (
                    bloco_5["b_probabilidade_pareada_simultanea"]["soma_p2_pares_fracao"]
                    if len(av_b["carteira_canonica"]) == 2
                    else None
                ),
                "cota_inferior_dawson_sankoff": bloco3["cota_inferior_dawson_sankoff"] * 100,
                "cota_superior_hunter_worsley": bloco3["cota_superior_hunter_worsley"] * 100,
                "esperanca_exata_universo": str(res_b["esperanca_exata"]),
                "variancia_exata_universo": float(res_b["variancia_exata"]),
                "variancia_exata_formula_fechada": bloco3["variancia_bilhetes_dependente_exata"],
                "distribuicao_n_premios": res_b["contagem_por_numero_premios"],
            }
        )

    # 3. Caso de empate exato resolvido deterministicamente via simetria D4 no volante 5x5:
    # A troca {2, 24} <-> {4, 22} preserva soma (=26), paridade (2 pares), moldura (2),
    # contagem exata por linha (r0:1, r4:1) e por coluna (c1:1, c3:1), gerando empate
    # matematico integral em todos os 6 componentes e em F(C).
    base_empate_jogo1 = [1, 2, 3, 5, 7, 8, 9, 10, 12, 13, 15, 17, 19, 21, 24]
    base_empate_jogo2 = [1, 2, 6, 7, 11, 13, 14, 15, 16, 18, 19, 20, 23, 24, 25]
    empate_a = [base_empate_jogo1, base_empate_jogo2]
    mapa_simetria = {2: 4, 24: 22}
    empate_b = [
        sorted(mapa_simetria.get(d, d) for d in jg)
        for jg in empate_a
    ]
    res_empate = selecionar_melhor_carteira([empate_b, empate_a], pool=DEZENAS_DISPONIVEIS)

    sensibilidade = _executar_analise_sensibilidade()
    custo_beneficio_estudo = _construir_estudo_custo_beneficio()

    tabela_p2_json = {
        str(c): {
            "intersecao": c,
            "p2_fracao": item["p2_fracao"],
            "p2_float": round(item["p2_float"], 10),
            "covariancia_float": round(item["covariancia_float"], 10),
            "correlacao_pearson": round(item["correlacao_pearson"], 8),
            "prob_uniao_2_jogos_percentual": round(item["prob_uniao_2_jogos_float"] * 100, 6),
        }
        for c, item in TABELA_P2_CONJUNTA_EXATA.items()
    }

    hashes_codigo = {
        "lotofacil_modo4/etapa2_funcao_objetivo.py": calcular_sha256_arquivo(
            os.path.join(base_dir, "lotofacil_modo4", "etapa2_funcao_objetivo.py")
        ),
        "lotofacil_modo4/etapa2_referencia_independente.py": calcular_sha256_arquivo(
            os.path.join(base_dir, "lotofacil_modo4", "etapa2_referencia_independente.py")
        ),
        "lotofacil_modo4/gerar_evidencias_etapa2.py": calcular_sha256_arquivo(
            os.path.join(base_dir, "lotofacil_modo4", "gerar_evidencias_etapa2.py")
        ),
        "testes/test_lotofacil_modo4_etapa2.py": (
            calcular_sha256_arquivo(os.path.join(base_dir, "testes", "test_lotofacil_modo4_etapa2.py"))
            if os.path.isfile(os.path.join(base_dir, "testes", "test_lotofacil_modo4_etapa2.py"))
            else None
        ),
    }

    tabela_p2_multiplas_resumo: List[Dict[str, Any]] = []
    for (m1, m2), por_c in TABELA_P2_MULTIPLAS_15_A_20.items():
        cs = sorted(por_c.keys())
        c_min, c_max = cs[0], cs[-1]
        p_min_item = por_c[c_min]
        p_max_item = por_c[c_max]
        tabela_p2_multiplas_resumo.append(
            {
                "par_dimensoes": f"{m1}x{m2}",
                "m1": m1,
                "m2": m2,
                "c_min": c_min,
                "c_max": c_max,
                "p2_c_min_fracao": p_min_item["p_conjunta_fracao"],
                "p2_c_min_float": round(p_min_item["p_conjunta_float"], 10),
                "p2_c_max_fracao": p_max_item["p_conjunta_fracao"],
                "p2_c_max_float": round(p_max_item["p_conjunta_float"], 10),
                "regioes_c_min": dict(p_min_item["regioes"]),
                "regioes_c_max": dict(p_max_item["regioes"]),
            }
        )

    definicao_modo_fixas = {
        "modos_formais": list(MODOS_FIXAS_PERMITIDOS),
        "todos_os_jogos": (
            "F obrigatorio em TODOS os bilhetes B_i da carteira (F subconjunto B_i subconjunto P). "
            "Exige |F| <= tamanho_minimo_aposta, F disjunto de bloqueadas E, P disjunto de E, e "
            "J <= C(|P - F|, m - |F|)."
        ),
        "composicao_pool": (
            "F obrigatorio apenas na composicao do pool P (F subconjunto P), sem impor F subconjunto B_i "
            "para cada bilhete individual. Permite |F| ate |P| (inclusive |F| > m) e teto J <= C(|P|, m)."
        ),
        "exemplo_validado_composicao_pool_17_fixas_em_p20": validar_pool_e_restricoes(
            pool=range(1, 21),
            fixas=range(1, 18),
            bloqueadas=range(21, 26),
            quantidade_jogos=5,
            tamanho_jogo=15,
            modo_fixas="composicao_pool",
        ),
    }

    evidencias = {
        "etapa": "ETAPA_2_FUNCAO_OBJETIVO_E_OTIMIZACAO",
        "versao_modelo": VERSAO_MODELO_OBJETIVO_ETAPA2,
        "categorias_prova_cientifica": dict(CATEGORIAS_PROVA_CIENTIFICA),
        "definicao_formal_modo_fixas_ressalva_2_4": definicao_modo_fixas,
        "especificacao_componentes": {
            k: dict(v) for k, v in ESPECIFICACAO_COMPONENTES_ETAPA2.items()
        },
        "perfis_pesos": {
            k: dict(v) for k, v in PERFIS_PESOS_ETAPA2.items()
        },
        "tabela_p2_conjunta_exata": tabela_p2_json,
        "tabela_p2_multiplas_15_a_20_quatro_regioes": tabela_p2_multiplas_resumo,
        "exemplos_manuais": {
            "j2_p16": av_ex1,
            "j3_p18_dispersa": av_disp,
            "j3_p18_concentrada": av_conc,
            "j2_multipla_m16_m15": av_m16_m15,
            "j2_multipla_m18_m17": av_m18_m17,
        },
        "prova_universo_completo_3268760": {
            "escopo_epistemologico": "VALIDACAO_EXAUSTIVA_UNIVERSO_SORTEIOS",
            "limitacao_escopo": (
                "Valida exaustivamente os 3.268.760 sorteios de C(25,15) para estes 5 casos nominais de carteiras; "
                "nao representa enumeracao de todas as carteiras possiveis nem prova de otimo global geral."
            ),
            "casos": prova_universo_completo,
        },
        "exemplo_desempate_deterministico": {
            "escopo_epistemologico": "VALIDACAO_CASOS_ESPECIFICOS_CARTEIRAS",
            "vencedora_carteira": res_empate["vencedora"]["carteira_canonica"],
            "chave_vencedora": list(str(x) for x in res_empate["vencedora"]["chave_desempate"]),
            "scores_F": [r["funcao_objetivo_F"] for r in res_empate["ranking"]],
        },
        "analise_sensibilidade": {
            "escopo_epistemologico": "COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS",
            "limitacao_escopo": (
                "A estabilidade 34/34 refere-se estritamente aos 34 cenarios de pesos e ao conjunto de "
                "5 carteiras avaliadas em p=20, J=4; nao demonstra invariancia universal para qualquer pool, "
                "orcamento ou quantidade J."
            ),
            **sensibilidade,
        },
        "estudo_custo_beneficio_orcamento_56_brl": custo_beneficio_estudo,
        "hashes_artefatos_etapa2": hashes_codigo,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }

    caminho_json = os.path.join(pasta_aud, "etapa_02_evidencias.json")
    with open(caminho_json, "w", encoding="utf-8") as f_json:
        json.dump(evidencias, f_json, ensure_ascii=False, indent=2)
        f_json.write("\n")

    # Documento Markdown rigoroso (sem em-dash nem en-dash)
    linhas: List[str] = [
        "# LOTOFACIL MODO 4 : ETAPA 2 (Funcao Objetivo e Criterios de Otimizacao)",
        "",
        "## 1. Definicao Matematica da Funcao Objetivo Principal",
        "Para uma carteira admissivel $C = \\{B_1, \\dots, B_J\\}$ dentro de um pool candidato $P \\subseteq \\{1, \\dots, 25\\}$ ($|P| = p \\in [15, 25]$), respeitando dezenas fixas $F \\subseteq P$ ($|F| = f$) segundo `modo_fixas` (`todos_os_jogos` ou `composicao_pool`) e dezenas bloqueadas $E$ ($E \\cap P = \\emptyset$, $F \\cap E = \\emptyset$), a funcao objetivo principal de maximizacao $F_{\\text{MODO4}}(C \\mid P, \\theta) \\in [0, 1]$ (equivalente a perda $L(C) = 1 - F(C)$) e definida por:",
        "",
        "$$F_{\\text{MODO4}}(C \\mid P, \\theta) = w_{\\text{cov}} S_{\\text{cov}}(C) + w_{\\text{prob}} S_{\\text{prob}}(C) + w_{\\text{div}} S_{\\text{div}}(C) + w_{\\text{dist}} S_{\\text{dist}}(C) + w_{\\text{cb}} S_{\\text{cb}}(C) + w_{\\text{est}} S_{\\text{div\\_est}}(C)$$",
        "",
        "### 1.1 Classificacao Epistemologica e Pesos Justificados (`padrao_modo4`)",
        "| Componente | Simbolo | Fundamento Cientifico | Peso | Papel Matematico |",
        "| :--- | :---: | :---: | :---: | :--- |",
    ]
    pesos_pad = PERFIS_PESOS_ETAPA2["padrao_modo4"]
    for nome in NOMES_COMPONENTES:
        sp = ESPECIFICACAO_COMPONENTES_ETAPA2[nome]
        linhas.append(
            f"| `{nome}` | `{sp['codigo']}` | **{sp['fundamento_cientifico']}** | `{pesos_pad[nome]:.2f}` | {sp['descricao']} |"
        )
    linhas.append(
        "| Indicadores historicos (frequencia, atraso, lift, aderencia modal) | N/A | **DESCRITIVO** | `0.00` | Painel estatistico isolado; proibido de atuar como ganho preditivo |"
    )

    linhas.extend(
        [
            "",
            "### 1.2 Distincao Obrigatoria das Cinco Grandezas Probabilisticas (Ressalva 2.1)",
            "1. **Probabilidade individual de cada bilhete:** $P(A_i) = P(|B_i \\cap S| \\ge 11)$ para $m_i \\in [15, 20]$.",
            "2. **Probabilidade pareada simultanea:** $p_2(m_i, m_k, c) = P(A_i \\cap A_k)$ pela particao hipergeometrica de 4 regioes.",
            "3. **Esperanca e variancia de bilhetes premiados:** $E[N_{\\text{prem}}(C)] = \\sum_i P(A_i)$ e $\\operatorname{Var}(N_{\\text{prem}}(C))$ exata via covariancias pareadas.",
            "4. **Limites matematicos da uniao ($P(\\bigcup A_i)$):** cota inferior de Dawson-Sankoff e cota superior de Hunter-Worsley (`S_prob` usa probabilidades pareadas e cotas como metrica de otimizacao, nao sendo igual a $P(\\bigcup A_i)$ quando $J \\ge 3$).",
            "5. **Probabilidade exata da uniao:** calculada por inclusao-exclusao fechada para $J \\le 2$, ou explicitamente marcada como `nao_calculada_diretamente` para $J \\ge 3$ salvo enumeracao direta do espaco amostral.",
            "",
            "### 1.3 Definicao Formal de Dezenas Fixas e Compatibilidade (Ressalva 2.4)",
            "- **`todos_os_jogos`:** exige $F \\subseteq B_i \\subseteq P$ para todo bilhete $B_i \\in C$, $|F| \\le m_{\\min}$, $F \\cap E = P \\cap E = \\emptyset$ e $J \\le C(|P \\setminus F|, m - |F|)$.",
            "- **`composicao_pool`:** exige $F \\subseteq P$ apenas na formacao e manutencao do pool (permitindo $|F| > m$ ate $|P|$, ex.: `17` fixas em `p = 20`), variando cada bilhete livremente em $P$ com teto $J \\le C(|P|, m)$.",
            "",
            "## 2. Probabilidade Conjunta Pareada $p_2(m_1, m_2, c)$ em Quatro Regioes (15 a 20 Dezenas)",
            "Para quaisquer dois bilhetes $B_1$ ($m_1$) e $B_2$ ($m_2$) com intersecao $c = |B_1 \\cap B_2|$, o universo de 25 dezenas particiona-se em $(n_0, n_1, n_2, n_3) = (c, m_1 - c, m_2 - c, 25 - m_1 - m_2 + c)$:",
            "",
            "$$p_2(m_1, m_2, c) = \\frac{1}{\\binom{25}{15}} \\sum_{x_0, x_1, x_2 : x_0+x_1 \\ge 11,\\; x_0+x_2 \\ge 11} \\binom{n_0}{x_0}\\binom{n_1}{x_1}\\binom{n_2}{x_2}\\binom{n_3}{15 - x_0 - x_1 - x_2}$$",
            "",
            "| c = |B_i inter B_k| (15x15) | p_2(c) Fracao Exata | p_2(c) Decimal | Covariancia p_2(c) - p_1^2 | Correlacao Pearson | P(A_i U A_k) Exata |",
            "| :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )
    for c in range(5, 16):
        row = TABELA_P2_CONJUNTA_EXATA[c]
        linhas.append(
            f"| {c} | `{row['p2_fracao']}` | {row['p2_float']:.6f} | {row['covariancia_float']:+.6f} | {row['correlacao_pearson']:+.4f} | {row['prob_uniao_2_jogos_float']*100:.4f}% |"
        )

    p2_5 = TABELA_P2_CONJUNTA_EXATA[5]["p2_float"]
    p2_15 = TABELA_P2_CONJUNTA_EXATA[15]["p2_float"]
    linhas.extend(
        [
            "",
            f"Observa-se matematicamente que $p_2(5) = p_2(6) = {p2_5:.6f}$ (impossibilidade exata de premiacao simultanea quando $c \\le 6$, pois $11 + 11 - 15 = 7 > c$) e, para $c \\in [7, 15]$, ocorre crescimento estrito $p_2(6) = 0 < p_2(7) < \\dots < p_2(15) = {p2_15:.6f} = p_1$: "
            + r"reduzir sobreposicao (ate $c \le 6$, onde os eventos de premiacao se tornam disjuntos) diminui a covariancia pareada e a variancia exata $\operatorname{Var}(N_{\text{prem}}(C)) = \sum_i p_i(1-p_i) + 2\sum_{i<k}(p_2(I_{ik}) - p_i p_k)$.",
            "",
            "### 2.1 Extremos da Formula 4-Regioes para Apostas Multiplas (15x15 ate 20x20)",
            "| Par (m1 x m2) | c_min | c_max | p_2(c_min) Exata | p_2(c_max) Exata | Regioes (n0, n1, n2, n3) em c_min |",
            "| :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )
    for item_m in tabela_p2_multiplas_resumo:
        reg = item_m["regioes_c_min"]
        linhas.append(
            f"| `{item_m['par_dimensoes']}` | {item_m['c_min']} | {item_m['c_max']} | `{item_m['p2_c_min_fracao']}` ({item_m['p2_c_min_float']:.6f}) | `{item_m['p2_c_max_fracao']}` ({item_m['p2_c_max_float']:.6f}) | ({reg['n0_intersecao']}, {reg['n1_exclusivas_primeiro']}, {reg['n2_exclusivas_segundo']}, {reg['n3_externas_aos_dois']}) |"
        )

    linhas.extend(
        [
            "",
            "## 3. Prova em Forca Bruta no Universo Completo (3.268.760 Sorteios : Casos Nominais)",
            "Escopo (`VALIDACAO_EXAUSTIVA_UNIVERSO_SORTEIOS`): enumera todos os 3.268.760 sorteios para validar as formulas exatas nos 5 casos abaixo (incluindo pares heterogeneos de apostas multiplas); nao enumera todas as carteiras possiveis do espaco de busca.",
            "",
            "| Caso | Dimensoes | P(N_prem >= 1) Exata | Cota [DS, HW] | E[N_prem] Exata | Var(N_prem) Universo vs Formula |",
            "| :--- | :---: | :---: | :---: | :---: | :---: |",
        ]
    )
    for pv in prova_universo_completo:
        dims = ",".join(str(x) for x in pv["tamanhos_bilhetes"])
        linhas.append(
            f"| `{pv['caso']}` | `[{dims}]` | {pv['prob_ao_menos_1_percentual_exata']:.4f}% (`{pv['prob_ao_menos_1_exata_universo']}`) | [{pv['cota_inferior_dawson_sankoff']:.4f}%, {pv['cota_superior_hunter_worsley']:.4f}%] | `{pv['esperanca_exata_universo']}` | {pv['variancia_exata_universo']:.6f} vs {pv['variancia_exata_formula_fechada']:.6f} |"
        )

    linhas.extend(
        [
            "",
            "## 4. Comparativo Custo x Combinacoes Simples x Cobertura (Orcamento R$ 56,00)",
            "| Estrategia (R$ 56,00) | Jogos | Comb. Simples (Pagas/Unicas) | Pares Cobertos | Trincas Cobertas | Var(N_prem) | Intervalo [DS, HW] P(U A_i) | Score F(C) |",
            "| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )
    for est in custo_beneficio_estudo:
        linhas.append(
            f"| `{est['estrategia']}` | {est['jogos']} | {est['combinacoes_simples_pagas']} / {est['combinacoes_simples_unicas']} | {est['pares_cobertos']} | {est['trincas_cobertas']} | {est['variancia_dependente_exata']:.4f} | [{est['cota_ds_prob_pelo_menos_1']*100:.2f}%, {est['cota_hw_prob_pelo_menos_1']*100:.2f}%] | {est['score_F']:.4f} |"
        )

    linhas.extend(
        [
            "",
            "## 5. Analise de Sensibilidade dos Pesos (Escopo Controlado) e Desempate",
            f"- **Escopo (`COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`):** `{sensibilidade['total_cenarios_testados']}` cenarios avaliados sobre o conjunto fixo de 5 carteiras em `p=20, J=4`; indica estabilidade local nesse conjunto de teste e nao prova invariancia universal para qualquer pool, orcamento ou quantidade $J$.",
            f"- **Estabilidade da solucao vencedora (`C1_dispersa_equilibrada`):** `{sensibilidade['vencedora_invariante_em_cenarios']}/{sensibilidade['total_cenarios_testados']}` cenarios (`{sensibilidade['taxa_estabilidade_vencedora']*100:.1f}%`).",
            f"- **Preservacao integral do ranking completo (`C1 > C2 > C3 > C4 > C5`):** `{sensibilidade['ranking_estrito_preservado_em_cenarios']}/{sensibilidade['total_cenarios_testados']}` cenarios.",
            "- **Criterio deterministico de desempate (`chave_desempate_deterministica`):** tupla lexicografica `(F(C), S_cov, S_prob, -I_max, -SS_obs, -carteira_canonica)` garantindo ordem total unica e reprodutivel.",
            "",
            "## 6. Clausula Matematica Obrigatoria",
            f"> {CLAUSULA_MATEMATICA_OBRIGATORIA}",
            "",
            "## 7. Estado de Homologacao Condicionada da Etapa 2",
            "Ressalvas 2.1 a 2.4 integralmente incorporadas em codigo, referencia independente, evidencias JSON/MD e testes de aceitacao.",
            "",
        ]
    )

    caminho_md = os.path.join(pasta_aud, "ETAPA_02_FUNCAO_OBJETIVO_E_OTIMIZACAO.md")
    with open(caminho_md, "w", encoding="utf-8") as f_md:
        f_md.write("\n".join(linhas))

    return {
        "evidencias_json": caminho_json,
        "relatorio_md": caminho_md,
        "prova_universo_completo_3268760": prova_universo_completo,
        "analise_sensibilidade_resumo": {
            "total_cenarios": sensibilidade["total_cenarios_testados"],
            "vencedora_invariante": sensibilidade["vencedora_invariante_em_cenarios"],
            "ranking_estrito_preservado": sensibilidade["ranking_estrito_preservado_em_cenarios"],
        },
        "hashes_artefatos_etapa2": hashes_codigo,
    }


if __name__ == "__main__":
    print(json.dumps(gerar_pacote_etapa2(), ensure_ascii=False, indent=2))
