# -*- coding: utf-8 -*-
"""
SUITE DE TESTES: ETAPA 2 (LOTOFACIL MODO 4)
=============================================
Valida a especificacao matematica das funcoes objetivo e criterios de
otimizacao, equivalencia exata contra implementacao de referencia independente,
verificacao exata sobre todos os 3.268.760 sorteios de C(25,15), analise de
sensibilidade, desempate deterministico e protecoes epistemologicas em modo -O.
"""

from decimal import Decimal
from fractions import Fraction
import json
import math
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lotofacil_modo4.etapa1_regras_oficiais import (  # noqa: E402
    CLAUSULA_MATEMATICA_OBRIGATORIA,
    DEZENAS_DISPONIVEIS,
    ESPACO_AMOSTRAL_SIMPLES,
    ErroValidacaoLotofacilError,
    probabilidade_pelo_menos_k_exata,
)
from lotofacil_modo4.etapa2_funcao_objetivo import (  # noqa: E402
    CATEGORIAS_PROVA_CIENTIFICA,
    ESPECIFICACAO_COMPONENTES_ETAPA2,
    MODOS_FIXAS_PERMITIDOS,
    NOMES_COMPONENTES,
    PERFIS_PESOS_ETAPA2,
    TABELA_P2_CONJUNTA_EXATA,
    TABELA_P2_MULTIPLAS_15_A_20,
    avaliar_carteira_etapa2,
    probabilidade_conjunta_par_exata,
    probabilidade_conjunta_par_quatro_regioes_detalhada,
    selecionar_melhor_carteira,
    validar_pesos_objetivo,
    validar_pool_e_restricoes,
)
from lotofacil_modo4.etapa2_referencia_independente import (  # noqa: E402
    avaliar_carteira_referencia_independente,
    probabilidade_par_quatro_regioes_referencia,
    verificar_lote_universo_completo,
)


def _exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise AssertionError(mensagem)


class TestLotofacilModo4Etapa2(unittest.TestCase):
    def test_tabela_p2_exata_monotonicidade_e_propriedades(self) -> None:
        p1 = probabilidade_pelo_menos_k_exata(15, 11)
        _exigir(len(TABELA_P2_CONJUNTA_EXATA) == 11, "Tabela p_2 deve cobrir c in [5..15].")
        _exigir(TABELA_P2_CONJUNTA_EXATA[15]["p2_exact"] == p1, "p_2(15) deve igualar p_1.")
        _exigir(
            TABELA_P2_CONJUNTA_EXATA[15]["prob_uniao_2_jogos_exact"] == p1,
            "Uniao de dois jogos clones deve ter probabilidade igual a p_1.",
        )

        _exigir(TABELA_P2_CONJUNTA_EXATA[5]["p2_exact"] == Fraction(0, 1), "p_2(5) deve ser 0 exatamente (11+11-15 = 7 > 5).")
        _exigir(TABELA_P2_CONJUNTA_EXATA[6]["p2_exact"] == Fraction(0, 1), "p_2(6) deve ser 0 exatamente (11+11-15 = 7 > 6).")

        anterior = TABELA_P2_CONJUNTA_EXATA[6]["p2_exact"]
        for c in range(7, 16):
            p2 = TABELA_P2_CONJUNTA_EXATA[c]["p2_exact"]
            _exigir(p2 > anterior, f"p_2({c}) nao cresceu estritamente: {p2} <= {anterior}.")
            anterior = p2
        _exigir(TABELA_P2_CONJUNTA_EXATA[5]["p2_exact"] < p1 * p1, "Intersecao minima c=5 deve ter covariancia negativa.")
        _exigir(TABELA_P2_CONJUNTA_EXATA[10]["p2_exact"] > p1 * p1, "Intersecao alta c=10 deve ter covariancia positiva.")

        # Ressalva 2.2: Conferencia exaustiva de TODAS as combinacoes (m1, m2, c) de 15 a 20 dezenas
        # contra a implementacao independente das 4 regioes
        _exigir(len(TABELA_P2_MULTIPLAS_15_A_20) == 21, "Devem existir exatamente 21 pares (m1 <= m2) entre 15 e 20.")
        for (m1, m2), por_c in TABELA_P2_MULTIPLAS_15_A_20.items():
            for c, det in por_c.items():
                ref_p2 = probabilidade_par_quatro_regioes_referencia(m1, m2, c)
                _exigir(
                    det["p_conjunta_exact"] == ref_p2,
                    f"Divergencia 4-regioes em ({m1}, {m2}, c={c}): {det['p_conjunta_exact']} vs {ref_p2}.",
                )
                regs = det["regioes"]
                _exigir(
                    regs["n0_intersecao"] + regs["n1_exclusivas_primeiro"] + regs["n2_exclusivas_segundo"] + regs["n3_externas_aos_dois"] == 25,
                    "Soma das 4 regioes deve totalizar 25.",
                )
                if c <= 6:
                    _exigir(det["p_conjunta_exact"] == Fraction(0, 1), f"p_2({m1},{m2},{c}) com c <= 6 deve ser zero.")

    def test_equivalencia_exata_contra_referencia_independente(self) -> None:
        casos = [
            # Caso 1: J=1 aposta multipla 16 dezenas
            ([list(range(1, 17))], tuple(range(1, 17)), (), ()),
            # Caso 2: J=1 aposta multipla 17 dezenas
            ([list(range(1, 18))], tuple(range(1, 18)), (), ()),
            # Caso 3: J=2 em p=16
            (
                [
                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16],
                ],
                tuple(range(1, 17)),
                (),
                (),
            ),
            # Caso 4: J=4 dispersa em p=20 com fixas e bloqueadas
            (
                [
                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 16, 17, 18, 19, 20],
                    [1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
                    [1, 2, 3, 4, 5, 6, 7, 11, 12, 13, 16, 17, 18, 19, 20],
                ],
                tuple(range(1, 21)),
                (1, 2, 3, 4, 5),
                (21, 22, 23, 24, 25),
            ),
            # Caso 5: Carteira com duplicata explicita (penalidade unicidade & redundancia)
            (
                [
                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 16, 17],
                ],
                tuple(range(1, 19)),
                (),
                (),
            ),
            # Caso 6: Carteira heterogenea multipla (m=18, m=17, m=15) e composicao_pool
            (
                [
                    list(range(1, 19)),
                    list(range(1, 13)) + list(range(19, 24)),
                    list(range(6, 21)),
                ],
                tuple(range(1, 24)),
                tuple(range(1, 18)),  # 17 fixas permitidas apenas no modo composicao_pool
                (24, 25),
                "composicao_pool",
            ),
        ]

        for idx, item in enumerate(casos):
            if len(item) == 4:
                cart, pool, fixas, bloq = item
                modo_fx = "todos_os_jogos"
            else:
                cart, pool, fixas, bloq, modo_fx = item
            av_motor = avaliar_carteira_etapa2(cart, pool=pool, fixas=fixas, bloqueadas=bloq, modo_fixas=modo_fx)
            av_ref = avaliar_carteira_referencia_independente(cart, pool=pool, fixas=fixas, modo_fixas=modo_fx)

            for nome in NOMES_COMPONENTES:
                diff = abs(av_motor["componentes"][nome] - av_ref["componentes"][nome])
                _exigir(
                    diff <= 1e-12,
                    f"Caso {idx} divergiu no componente '{nome}': motor={av_motor['componentes'][nome]} vs ref={av_ref['componentes'][nome]}.",
                )

            _exigir(
                abs(av_motor["funcao_objetivo_F"] - av_ref["funcao_objetivo_F"]) <= 1e-12,
                f"Caso {idx} divergiu em F(C).",
            )
            _exigir(
                abs(av_motor["funcao_perda_L"] - av_ref["funcao_perda_L"]) <= 1e-12,
                f"Caso {idx} divergiu em L(C).",
            )

            bloco3 = av_motor["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]["3_probabilidade_conjunta_carteira"]
            _exigir(
                abs(bloco3["variancia_bilhetes_dependente_exata"] - float(av_ref["variancia_dependente_exata"])) <= 1e-12,
                f"Caso {idx} divergiu em Var(N_prem).",
            )
            _exigir(
                abs(bloco3["cota_inferior_dawson_sankoff"] - av_ref["cota_inferior_dawson_sankoff"]) <= 1e-12,
                f"Caso {idx} divergiu em Dawson-Sankoff.",
            )
            _exigir(
                abs(bloco3["cota_superior_hunter_worsley"] - av_ref["cota_superior_hunter_worsley"]) <= 1e-12,
                f"Caso {idx} divergiu em Hunter-Worsley.",
            )
            _exigir(
                av_motor["detalhes"]["custo_beneficio"]["custo_total_brl"] == av_ref["custo_total_brl"],
                f"Caso {idx} divergiu no custo total.",
            )

    def test_verificacao_forca_bruta_3268760_sorteios_e_cotas_ds_hw(self) -> None:
        ex_j2 = [
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16],
        ]
        ex_j3_disp = [
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 16, 17, 18],
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 13, 14, 15, 16, 17, 18],
        ]
        ex_j3_conc = [
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16],
            [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 17],
        ]

        ex_m16_m15 = [
            list(range(1, 17)),
            list(range(1, 8)) + list(range(17, 25)),
        ]
        ex_m18_m17 = [
            list(range(1, 19)),
            list(range(1, 13)) + list(range(19, 24)),
        ]

        r_j2, r_disp, r_conc, r_m16, r_m18 = verificar_lote_universo_completo(
            [ex_j2, ex_j3_disp, ex_j3_conc, ex_m16_m15, ex_m18_m17]
        )

        av_j2 = avaliar_carteira_etapa2(ex_j2, pool=tuple(range(1, 17)))
        av_disp = avaliar_carteira_etapa2(ex_j3_disp, pool=tuple(range(1, 19)))
        av_conc = avaliar_carteira_etapa2(ex_j3_conc, pool=tuple(range(1, 19)))
        av_m16 = avaliar_carteira_etapa2(ex_m16_m15, pool=DEZENAS_DISPONIVEIS)
        av_m18 = avaliar_carteira_etapa2(ex_m18_m17, pool=DEZENAS_DISPONIVEIS)

        # Exatidao racional para J=2 e apostas multiplas sobre 3.268.760 sorteios
        for r_pair, av_pair, m1, m2, c_inter in (
            (r_j2, av_j2, 15, 15, 14),
            (r_m16, av_m16, 16, 15, 7),
            (r_m18, av_m18, 18, 17, 12),
        ):
            b3_pair = av_pair["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]["3_probabilidade_conjunta_carteira"]
            _exigir(
                f"{r_pair['probabilidade_ao_menos_1_exata'].numerator}/{r_pair['probabilidade_ao_menos_1_exata'].denominator}"
                == b3_pair["prob_ao_menos_1_exata_fechada"],
                f"Probabilidade exata da uniao ({m1}x{m2}) divergiu da enumeracao de 3.268.760 sorteios.",
            )
            det4 = probabilidade_conjunta_par_quatro_regioes_detalhada(m1, m2, c_inter)
            _exigir(
                r_pair["distribuicao_exata"][2] == det4["p_conjunta_exact"],
                f"p_2({m1},{m2},{c_inter}) 4-regioes divergiu da forca bruta de 3.268.760 sorteios.",
            )

        # Invariancia de esperanca e superioridade na variancia / cobertura conjunta para dispersa vs concentrada
        _exigir(
            r_disp["esperanca_exata"] == r_conc["esperanca_exata"] == 3 * probabilidade_pelo_menos_k_exata(15, 11),
            "E[N_prem] deve ser estritamente invariante entre carteiras de mesmo J.",
        )
        _exigir(
            r_disp["variancia_exata"] < r_conc["variancia_exata"],
            "Carteira dispersa deve possuir variancia Var(N_prem) estritamente menor que a concentrada.",
        )
        _exigir(
            r_disp["probabilidade_ao_menos_1_exata"] > r_conc["probabilidade_ao_menos_1_exata"],
            "Carteira dispersa deve possuir P(N_prem >= 1) estritamente maior que a concentrada.",
        )

        for r_univ, av_m in ((r_j2, av_j2), (r_disp, av_disp), (r_conc, av_conc), (r_m16, av_m16), (r_m18, av_m18)):
            b3 = av_m["detalhes"]["probabilidade_conjunta"]["separacao_indicadores_secao3"]["3_probabilidade_conjunta_carteira"]
            _exigir(
                abs(float(r_univ["variancia_exata"]) - b3["variancia_bilhetes_dependente_exata"]) <= 1e-12,
                "Formula fechada de variancia divergiu da enumeracao exata dos 3.268.760 sorteios.",
            )
            p_exata = float(r_univ["probabilidade_ao_menos_1_exata"])
            _exigir(
                b3["cota_inferior_dawson_sankoff"] - 1e-12 <= p_exata <= b3["cota_superior_hunter_worsley"] + 1e-12,
                f"Cotas [DS={b3['cota_inferior_dawson_sankoff']}, HW={b3['cota_superior_hunter_worsley']}] "
                f"nao enquadraram P_exata={p_exata}.",
            )

        # Ressalva 2.1: J=3 nao pode rotular S_prob nem cota como probabilidade exata da uniao
        p_info_disp = av_disp["detalhes"]["probabilidade_conjunta"]
        _exigir(not p_info_disp["s_prob_equivale_a_uniao_exata"], "S_prob para J>=3 nao equivale a uniao exata.")
        _exigir(
            not p_info_disp["distincao_cinco_grandezas_ressalva_2_1"]["e_probabilidade_exata_uniao_eventos"]["calculada_diretamente"],
            "Para J=3, e_probabilidade_exata_uniao_eventos nao deve afirmar calculo direto fechado.",
        )

        _exigir(
            av_disp["funcao_objetivo_F"] > av_conc["funcao_objetivo_F"],
            "Funcao objetivo F(C) deve preferir carteira dispersa a concentrada.",
        )

    def test_validacao_fail_closed_pesos_pool_e_epistemologia(self) -> None:
        # 1. Rejeicao de pesos que nao somam 1.0 ou usam chave descritiva indevida
        pesos_ruins = [
            {"cobertura_combinatoria": 0.5},  # chaves faltantes
            {**dict(PERFIS_PESOS_ETAPA2["padrao_modo4"]), "historico_atraso": 0.1},  # chave descritiva indevida
            {**dict(PERFIS_PESOS_ETAPA2["padrao_modo4"]), "cobertura_combinatoria": 0.99},  # soma != 1
            {**dict(PERFIS_PESOS_ETAPA2["padrao_modo4"]), "cobertura_combinatoria": -0.1, "probabilidade_conjunta": 0.65},  # negativo
            {**dict(PERFIS_PESOS_ETAPA2["padrao_modo4"]), "cobertura_combinatoria": True},  # bool
        ]
        for pw in pesos_ruins:
            falhou = False
            try:
                validar_pesos_objetivo(pw)
            except ErroValidacaoLotofacilError:
                falhou = True
            _exigir(falhou, f"Pesos invalidos {pw!r} nao foram rejeitados.")

        # 2. Rejeicao de restricoes impossiveis sem alteracoes silenciosas
        restricoes_impossiveis = [
            dict(pool=range(1, 15), fixas=(), bloqueadas=(), quantidade_jogos=1),  # pool < 15
            dict(pool=range(1, 17), fixas=(1, 2), bloqueadas=(2,), quantidade_jogos=1),  # fixa e bloqueada
            dict(pool=range(1, 17), fixas=(20,), bloqueadas=(), quantidade_jogos=1),  # fixa fora do pool
            dict(pool=range(1, 17), fixas=(), bloqueadas=(), quantidade_jogos=17),  # > C(16,15)=16
            dict(pool=range(1, 18), fixas=tuple(range(1, 15)), bloqueadas=(), quantidade_jogos=4),  # > C(3,1)=3
            dict(pool=range(1, 21), fixas=tuple(range(1, 17)), bloqueadas=(), quantidade_jogos=1, modo_fixas="todos_os_jogos"),  # 16 fixas > m=15
            dict(pool=range(1, 21), fixas=(1, 2), bloqueadas=(), quantidade_jogos=1, modo_fixas="modo_inexistente"),
        ]
        for kw in restricoes_impossiveis:
            falhou = False
            try:
                validar_pool_e_restricoes(**kw)
            except ErroValidacaoLotofacilError:
                falhou = True
            _exigir(falhou, f"Restricao impossivel {kw!r} nao foi rejeitada.")

        # 2b. Confirmar composicao_pool aceita |F| > 15 e diagnostico de compatibilidade
        res_comp = validar_pool_e_restricoes(
            pool=range(1, 21),
            fixas=tuple(range(1, 18)),
            bloqueadas=(21, 22, 23, 24, 25),
            quantidade_jogos=5,
            modo_fixas="composicao_pool",
        )
        _exigir(
            res_comp["modo_fixas"] == "composicao_pool"
            and len(res_comp["fixas_por_jogo"]) == 0
            and len(CATEGORIAS_PROVA_CIENTIFICA) == 5
            and set(MODOS_FIXAS_PERMITIDOS) == {"todos_os_jogos", "composicao_pool"},
            "Regra formal composicao_pool ou categorias de prova cientifica inconsistentes.",
        )

        # 3. Separacao obrigatoria dos 3 indicadores e peso zero no painel descritivo
        av = avaliar_carteira_etapa2([list(range(1, 17))], pool=tuple(range(1, 17)))
        epi = av["decomposicao_epistemologica"]
        _exigir(epi["soma_pesos_descritivos_preditivos"] == 0.0, "Peso preditivo de descritivos deve ser zero.")
        _exigir(
            abs(epi["soma_pesos_exatos"] + epi["soma_pesos_heuristicos"] - 1.0) <= 1e-12,
            "Pesos exatos + heuristicos devem somar 1.0.",
        )
        _exigir(
            ESPECIFICACAO_COMPONENTES_ETAPA2["cobertura_combinatoria"]["fundamento_cientifico"] == "EXATO"
            and ESPECIFICACAO_COMPONENTES_ETAPA2["probabilidade_conjunta"]["fundamento_cientifico"] == "EXATO"
            and ESPECIFICACAO_COMPONENTES_ETAPA2["custo_beneficio"]["fundamento_cientifico"] == "EXATO",
            "Componentes exatos rotulados incorretamente.",
        )
        _exigir(
            av["detalhes"]["estrutura_e_descritivo"]["indicadores_descritivos_isolados"]["peso_na_funcao_objetivo"] == 0.0,
            "Painel descritivo isolado deve ter peso 0.0.",
        )
        _exigir(
            av["clausula_obrigatoria"] == CLAUSULA_MATEMATICA_OBRIGATORIA,
            "Clausula matematica obrigatoria deve ser preservada integralmente.",
        )

    def test_desempate_deterministico_simetria_d4_e_atingimento_cotas(self) -> None:
        # Caso 1: Empate exato por simetria D4 {2, 24} <-> {4, 22}
        empate_a = [
            [1, 2, 3, 5, 7, 8, 9, 10, 12, 13, 15, 17, 19, 21, 24],
            [1, 2, 6, 7, 11, 13, 14, 15, 16, 18, 19, 20, 23, 24, 25],
        ]
        mapa = {2: 4, 24: 22}
        empate_b = [sorted(mapa.get(d, d) for d in jg) for jg in empate_a]

        av_a = avaliar_carteira_etapa2(empate_a, pool=DEZENAS_DISPONIVEIS)
        av_b = avaliar_carteira_etapa2(empate_b, pool=DEZENAS_DISPONIVEIS)

        for nome in NOMES_COMPONENTES:
            _exigir(
                abs(av_a["componentes"][nome] - av_b["componentes"][nome]) <= 1e-12,
                f"Simetria D4 deveria empatar em '{nome}': {av_a['componentes'][nome]} vs {av_b['componentes'][nome]}.",
            )
        _exigir(
            abs(av_a["funcao_objetivo_F"] - av_b["funcao_objetivo_F"]) <= 1e-12,
            "Simetria D4 deve produzir empate exato em F(C).",
        )

        r1 = selecionar_melhor_carteira([empate_a, empate_b], pool=DEZENAS_DISPONIVEIS)
        r2 = selecionar_melhor_carteira([empate_b, empate_a], pool=DEZENAS_DISPONIVEIS)
        _exigir(
            r1["vencedora"]["carteira_canonica"] == r2["vencedora"]["carteira_canonica"],
            "Desempate deterministico dependeu da ordem de entrada das candidatas.",
        )

        # Caso 2: Atingimento exato da cota minima de distribuicao (p=16, J=16: cada dezena aparece exatamente 15 vezes)
        import itertools

        pool16 = tuple(range(1, 17))
        todas16 = [list(c) for c in itertools.combinations(pool16, 15)]
        av16 = avaliar_carteira_etapa2(todas16, pool=pool16)
        _exigir(
            abs(av16["componentes"]["distribuicao_dezenas"] - 1.0) <= 1e-12,
            "Design completo em p=16 (J=16) deve atingir S_dist == 1.0.",
        )
        _exigir(
            abs(av16["componentes"]["diversificacao_sobreposicao"] - 1.0) <= 1e-12,
            "Design completo em p=16 (J=16) deve atingir S_div == 1.0 (cota Schur exata).",
        )
        _exigir(
            abs(av16["componentes"]["cobertura_combinatoria"] - 1.0) <= 1e-12,
            "Design completo em p=16 (J=16) deve cobrir 100% de t=1..4.",
        )

    def test_evidencias_etapa2_geradas_e_integridade_textual(self) -> None:
        pasta_aud = os.path.join(BASE_DIR, "auditoria", "lotofacil_modo4")
        caminho_json = os.path.join(pasta_aud, "etapa_02_evidencias.json")
        caminho_md = os.path.join(pasta_aud, "ETAPA_02_FUNCAO_OBJETIVO_E_OTIMIZACAO.md")
        _exigir(os.path.isfile(caminho_json), f"Evidencia JSON da Etapa 2 ausente: {caminho_json}")
        _exigir(os.path.isfile(caminho_md), f"Relatorio MD da Etapa 2 ausente: {caminho_md}")

        with open(caminho_json, "r", encoding="utf-8") as fj:
            ev = json.load(fj)
        _exigir(ev["analise_sensibilidade"]["taxa_estabilidade_vencedora"] == 1.0, "Sensibilidade deveria preservar vencedora em 100% dos cenarios testados.")
        _exigir("limitacao_escopo" in ev["analise_sensibilidade"], "Sensibilidade deve explicitar limitacao de escopo.")
        _exigir(len(ev["prova_universo_completo_3268760"]["casos"]) == 5, "Devem constar 5 provas em universo completo (simples e multiplas).")
        _exigir(len(ev["tabela_p2_multiplas_15_a_20_quatro_regioes"]) == 21, "Devem constar os 21 pares m1<=m2 das 4 regioes.")
        _exigir(ev["clausula_obrigatoria"] == CLAUSULA_MATEMATICA_OBRIGATORIA, "Clausula divergente no JSON da Etapa 2.")

        with open(caminho_md, "r", encoding="utf-8") as fm:
            md_txt = fm.read()
        _exigir("\u2014" not in md_txt and "\u2013" not in md_txt, "Documento Markdown contem travessoes proibidos.")
        _exigir(CLAUSULA_MATEMATICA_OBRIGATORIA in md_txt, "Clausula obrigatoria ausente no MD da Etapa 2.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
