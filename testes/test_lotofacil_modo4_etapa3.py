# -*- coding: utf-8 -*-
"""
SUITE DE TESTES: ETAPA 3 (LOTOFACIL MODO 4)
=============================================
Valida algoritmos de otimizacao, avaliador incremental exato, busca exata
contra referencia independente, comparacao controlada, restricoes (`todos_os_jogos`
e `composicao_pool`), apostas multiplas/mistas, determinismo e validacao negativa
em modo normal e Python -O.
"""

import json
import os
import random
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lotofacil_modo4.etapa1_regras_oficiais import (  # noqa: E402
    CLAUSULA_MATEMATICA_OBRIGATORIA,
    DEZENAS_DISPONIVEIS,
    ErroValidacaoLotofacilError,
)
from lotofacil_modo4.etapa2_funcao_objetivo import (  # noqa: E402
    avaliar_carteira_etapa2,
)
from lotofacil_modo4.etapa3_otimizadores import (  # noqa: E402
    ALGORITMOS_ETAPA3,
    HISTORICO_GERACAO_ETAPA3,
    AvaliadorIncrementalEtapa3,
    comparar_algoritmos_etapa3,
    executar_busca_exata_pequena,
    otimizar_carteira_etapa3,
    planejar_composicoes_orcamento,
)
from lotofacil_modo4.etapa3_referencia_independente import (  # noqa: E402
    resolver_exato_referencia_independente,
    verificar_equivalencia_etapa3_contra_referencia,
)


def _exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise AssertionError(mensagem)


class TestLotofacilModo4Etapa3(unittest.TestCase):
    def test_avaliador_incremental_equivalente_etapa2_apos_sequencia_trocas(self) -> None:
        casos = [
            # Caso 1: Simples p=20, fixas por jogo
            (
                [
                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15],
                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 16, 17, 18, 19, 20, 10],
                    [1, 2, 3, 4, 5, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20],
                ],
                tuple(range(1, 21)),
                (1, 2, 3),
                "todos_os_jogos",
            ),
            # Caso 2: Mistas (16 + 15 + 15) com composicao_pool e 16 fixas no pool
            (
                [
                    list(range(1, 17)),
                    list(range(1, 16)),
                    list(range(6, 21)),
                ],
                tuple(range(1, 22)),
                tuple(range(1, 17)),
                "composicao_pool",
            ),
        ]

        rng = random.Random(2026)
        for cart, pool, fixas, modo in casos:
            av0 = avaliar_carteira_etapa2(cart, pool=pool, fixas=fixas, modo_fixas=modo)
            fix_jogo = tuple(av0["fixas_obrigatorias_por_jogo"])
            inc = AvaliadorIncrementalEtapa3(cart, pool, fix_jogo, av0["pesos"])
            _exigir(
                abs(inc.score_atual() - av0["funcao_objetivo_F"]) <= 1e-12,
                "Avaliador incremental divergiu no estado inicial.",
            )

            livres = [d for d in pool if d not in set(fix_jogo)]
            for step in range(25):
                idx = step % inc.j
                fora = [d for d in livres if d not in inc.sets[idx]]
                dentro_livres = [d for d in inc.jogos[idx] if d not in set(fix_jogo)]
                d_sai = rng.choice(dentro_livres)
                d_ent = rng.choice(fora)
                f_sim, _ = inc.simular_troca_dezena(idx, d_sai, d_ent)
                f_ap = inc.aplicar_troca_dezena(idx, d_sai, d_ent)
                av_full = avaliar_carteira_etapa2(inc.jogos, pool=pool, fixas=fixas, modo_fixas=modo)
                _exigir(
                    abs(f_sim - av_full["funcao_objetivo_F"]) <= 1e-12,
                    f"simular_troca_dezena divergiu no passo {step}: {f_sim} vs {av_full['funcao_objetivo_F']}.",
                )
                _exigir(
                    abs(f_ap - av_full["funcao_objetivo_F"]) <= 1e-12,
                    f"aplicar_troca_dezena divergiu no passo {step}: {f_ap} vs {av_full['funcao_objetivo_F']}.",
                )

    def test_busca_exata_igual_referencia_independente_e_otimo_global_real(self) -> None:
        instancias = [
            dict(pool=tuple(range(1, 17)), fixas=(), bloqueadas=tuple(range(21, 26)), modo_fixas="todos_os_jogos", quantidade_jogos=3, tamanho_aposta=15),
            dict(pool=tuple(range(1, 19)), fixas=tuple(range(1, 12)), bloqueadas=tuple(range(19, 26)), modo_fixas="todos_os_jogos", quantidade_jogos=3, tamanho_aposta=15),
        ]
        for cfg in instancias:
            res_ex = executar_busca_exata_pequena(semente=42, limite_combinacoes_exatas=10_000, **cfg)
            ref_ex = resolver_exato_referencia_independente(limite_combinacoes_exatas=10_000, **cfg)
            _exigir(res_ex["otimo_global_comprovado"], "busca_exata_pequena deve marcar otimo_global_comprovado=True.")
            _exigir(
                res_ex["carteira_otimizada"] == ref_ex["carteira_otima"],
                f"Carteira otima divergiu da referencia independente:\n{res_ex['carteira_otimizada']}\nvs\n{ref_ex['carteira_otima']}",
            )
            _exigir(
                abs(res_ex["funcao_objetivo_F"] - ref_ex["funcao_objetivo_F"]) <= 1e-12,
                "Otimo global F(C) divergiu da referencia independente.",
            )

            # Comparacao controlada: nenhuma heuristica pode superar o otimo global comprovado
            comp = comparar_algoritmos_etapa3(
                pool=cfg["pool"],
                fixas=cfg["fixas"],
                bloqueadas=cfg["bloqueadas"],
                modo_fixas=cfg["modo_fixas"],
                quantidade_jogos=cfg["quantidade_jogos"],
                tamanho_aposta=cfg["tamanho_aposta"],
                semente=42,
                max_avaliacoes=150,
                max_iteracoes=100,
                incluir_exato_se_viavel=True,
                limite_combinacoes_exatas=10_000,
            )
            f_star = res_ex["funcao_objetivo_F"]
            for nome, r_alg in comp["resultados_completos"].items():
                chk = verificar_equivalencia_etapa3_contra_referencia(r_alg)
                _exigir(chk["equivalente_1e_12"], f"Falha de referencia no algoritmo {nome}: {chk}")
                _exigir(
                    r_alg["funcao_objetivo_F"] <= f_star + 1e-12,
                    f"Algoritmo {nome} alegou F={r_alg['funcao_objetivo_F']} > F*={f_star}.",
                )

    def test_validacao_fail_closed_intratavel_e_parametros_invalidos(self) -> None:
        casos_invalidos = [
            ("busca_exata_pequena", dict(pool=DEZENAS_DISPONIVEIS, quantidade_jogos=10, limite_combinacoes_exatas=10_000)),
            ("algoritmo_inexistente", dict(pool=DEZENAS_DISPONIVEIS, quantidade_jogos=2)),
            ("estrategia_combinada", dict(pool=range(1, 21), fixas=(1, 2), bloqueadas=(2,), quantidade_jogos=3)),
            ("algoritmo_guloso", dict(pool=range(1, 21), fixas=range(1, 17), modo_fixas="todos_os_jogos", quantidade_jogos=2)),
            ("busca_local_trocas", dict(pool=DEZENAS_DISPONIVEIS, orcamento_brl="2.00")),
            ("multiplos_reinicios", dict(pool=DEZENAS_DISPONIVEIS, quantidade_jogos=2, semente=-1)),
            ("referencia_aleatoria", dict(pool=DEZENAS_DISPONIVEIS, quantidade_jogos=2, orcamento_brl="20.00")),
        ]
        for alg, kwargs in casos_invalidos:
            falhou = False
            try:
                otimizar_carteira_etapa3(algoritmo=alg, **kwargs)
            except ErroValidacaoLotofacilError:
                falhou = True
            _exigir(falhou, f"Execucao invalida ({alg}, {kwargs!r}) nao foi rejeitada em fail-closed.")

    def test_conformidade_modos_fixas_multiplas_e_determinismo(self) -> None:
        _exigir(HISTORICO_GERACAO_ETAPA3 is None, "Historico de geracao na Etapa 3 deve permanecer None.")

        # Testar composicao por orcamento (R$ 56,00 e R$ 600,00)
        plan = planejar_composicoes_orcamento("56.00", tamanho_pool=18, quantidade_fixas_por_jogo=0)
        nomes_plan = {op["nome"] for op in plan}
        _exigir("homogenea_16x_m15" in nomes_plan and "homogenea_1x_m16" in nomes_plan, "Planejamento R$ 56,00 incompleto.")

        # Testar TODOS os algoritmos heuristicos em carteira heterogenea (17 + 15 + 15) e composicao_pool
        for alg in ("referencia_aleatoria", "algoritmo_guloso", "busca_local_trocas", "multiplos_reinicios", "estrategia_combinada"):
            r1 = otimizar_carteira_etapa3(
                algoritmo=alg,
                pool=range(1, 22),
                fixas=range(1, 17),  # 16 fixas permitidas em composicao_pool
                bloqueadas=(22, 23, 24, 25),
                modo_fixas="composicao_pool",
                tamanhos_jogos=(17, 15, 15),
                semente=123,
                max_avaliacoes=60,
                max_iteracoes=40,
            )
            r2 = otimizar_carteira_etapa3(
                algoritmo=alg,
                pool=range(1, 22),
                fixas=range(1, 17),
                bloqueadas=(22, 23, 24, 25),
                modo_fixas="composicao_pool",
                tamanhos_jogos=(17, 15, 15),
                semente=123,
                max_avaliacoes=60,
                max_iteracoes=40,
            )
            _exigir(
                r1["sha256_execucao"] == r2["sha256_execucao"] and r1["carteira_otimizada"] == r2["carteira_otimizada"],
                f"Algoritmo '{alg}' quebrou reprodutibilidade deterministica.",
            )
            _exigir(r1["historico_utilizado"] is None, f"Algoritmo '{alg}' deve manter historico_utilizado=None.")
            _exigir(r1["clausula_obrigatoria"] == CLAUSULA_MATEMATICA_OBRIGATORIA, "Clausula modificada.")
            chk = verificar_equivalencia_etapa3_contra_referencia(r1)
            _exigir(chk["equivalente_1e_12"], f"Algoritmo '{alg}' falhou na conferencia independente: {chk}")

    def test_evidencias_etapa3_geradas_e_integridade_textual(self) -> None:
        pasta_aud = os.path.join(BASE_DIR, "auditoria", "lotofacil_modo4")
        caminho_json = os.path.join(pasta_aud, "etapa_03_evidencias.json")
        caminho_md = os.path.join(pasta_aud, "ETAPA_03_ALGORITMOS_DE_OTIMIZACAO.md")
        _exigir(os.path.isfile(caminho_json), f"JSON da Etapa 3 ausente: {caminho_json}")
        _exigir(os.path.isfile(caminho_md), f"Markdown da Etapa 3 ausente: {caminho_md}")

        with open(caminho_json, "r", encoding="utf-8") as fj:
            ev = json.load(fj)
        _exigir(
            set(ev["especificacao_algoritmos"].keys()) == set(ALGORITMOS_ETAPA3),
            "Especificacao dos algoritmos incompleta no JSON da Etapa 3.",
        )
        _exigir(
            ev["verificacao_referencia_independente"]["todas_equivalentes_1e_12_e_conformes"],
            "Benchmark da Etapa 3 falhou na conferencia contra referencia independente.",
        )
        _exigir(
            ev["reprodutibilidade_deterministica"]["mesma_semente_identica_sha256"]
            and ev["reprodutibilidade_deterministica"]["mesma_carteira_canonica"],
            "Benchmark da Etapa 3 falhou na reprodutibilidade.",
        )
        _exigir(ev["clausula_obrigatoria"] == CLAUSULA_MATEMATICA_OBRIGATORIA, "Clausula divergente no JSON da Etapa 3.")

        with open(caminho_md, "r", encoding="utf-8") as fm:
            md_txt = fm.read()
        _exigir("\u2014" not in md_txt and "\u2013" not in md_txt, "Documento MD da Etapa 3 contem travessoes proibidos.")
        _exigir(CLAUSULA_MATEMATICA_OBRIGATORIA in md_txt, "Clausula obrigatoria ausente no MD da Etapa 3.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
