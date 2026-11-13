# -*- coding: utf-8 -*-
"""
SUITE DE TESTES : ETAPA 4 (LOTOFACIL MODO 4)
============================================
Valida arquitetura adaptativa deterministica, equivalencia numerica do motor
otimizado (array('H') + cache N_p2) e do construtivo guloso incremental,
independencia AST do modulo de referencia zero-dependencia, preservacao dos
artefatos congelados das Etapas 1, 2 e 3, escalabilidade e limites de execucao.

Importante: sem uso de 'assert' como barreira critica; 100% efetivo sob -O.
"""

from __future__ import annotations

import json
import os
import random
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lotofacil_modo4.etapa1_regras_oficiais import ErroValidacaoLotofacilError
from lotofacil_modo4.etapa2_funcao_objetivo import (
    VERSAO_MODELO_OBJETIVO_ETAPA2,
    avaliar_carteira_etapa2,
)
from lotofacil_modo4.etapa4_arquitetura_adaptativa import (
    ALGORITMOS_ETAPA4,
    HISTORICO_GERACAO_ETAPA4,
    VERSAO_ARQUITETURA_ETAPA4,
    AvaliadorConstrutivoIncrementalEtapa4,
    MotorIncrementalOtimizadoEtapa4,
    _resolver_especificacao_etapa4,
    analisar_espaco_e_despachar_etapa4,
    executar_arquitetura_adaptativa_etapa4,
)
from lotofacil_modo4.etapa4_referencia_independente import (
    auditar_independencia_ast_etapa4,
    avaliar_carteira_ref_etapa4,
    resolver_exato_etapa4_ref,
    verificar_equivalencia_etapa4_contra_referencia,
    verificar_preservacao_etapas_1_2_3_ref,
)


def _exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise AssertionError(mensagem)


class TestLotofacilModo4Etapa4(unittest.TestCase):
    def test_independencia_ast_referencia_e_preservacao_etapas_anteriores(self) -> None:
        ast_chk = auditar_independencia_ast_etapa4()
        _exigir(ast_chk["independencia_comprovada"], f"Referencia Etapa 4 possui dependencias proibidas: {ast_chk['violacoes']}")
        _exigir(ast_chk["dependencias_internas_detectadas"] == 0, "Contador de dependencias internas deve ser 0.")

        preserv = verificar_preservacao_etapas_1_2_3_ref(BASE_DIR)
        _exigir(
            preserv["preservado_integralmente"],
            f"Artefatos congelados das Etapas 1-3 foram alterados: {preserv['divergencias']}",
        )
        _exigir(preserv["total_arquivos_congelados"] == 20, "Devem ser auditados exatamente 20 artefatos congelados.")

    def test_equivalencia_motor_otimizado_e_construtivo_incremental(self) -> None:
        rng = random.Random(2026)
        pool = list(range(1, 21))
        fixas = (1, 2)
        bloqueadas = (21, 22, 23, 24, 25)
        livres = [d for d in pool if d not in fixas]

        # 1. Carteira heterogenea [17, 16, 15] submetida a 25 trocas e substituicoes
        jogos_het = [
            tuple(sorted((*fixas, *rng.sample(livres, 15)))),
            tuple(sorted((*fixas, *rng.sample(livres, 14)))),
            tuple(sorted((*fixas, *rng.sample(livres, 13)))),
        ]
        spec_het = _resolver_especificacao_etapa4(
            pool, fixas, bloqueadas, "todos_os_jogos", None, 15, [17, 16, 15], None, None, None
        )
        motor = MotorIncrementalOtimizadoEtapa4(jogos_het, spec_het["pool"], spec_het["fixas_por_jogo"], spec_het["pesos"])

        av_e2_0 = avaliar_carteira_etapa2(jogos_het, pool=pool, fixas=fixas, bloqueadas=bloqueadas, modo_fixas="todos_os_jogos")
        av_ref_0 = avaliar_carteira_ref_etapa4(jogos_het, pool=pool, fixas=fixas, bloqueadas=bloqueadas, modo_fixas="todos_os_jogos")
        _exigir(abs(motor.score_atual() - av_e2_0["funcao_objetivo_F"]) <= 1e-12, "Divergencia inicial motor Etapa 4 vs Etapa 2.")
        _exigir(abs(motor.score_atual() - av_ref_0["funcao_objetivo_F"]) <= 1e-12, "Divergencia inicial motor Etapa 4 vs Ref Zero-Dep.")

        aplicados = 0
        for _ in range(80):
            idx = rng.randrange(3)
            jg = motor.jogos[idx]
            outs = [d for d in jg if d not in fixas]
            ins = [d for d in livres if d not in jg]
            d_out = rng.choice(outs)
            d_in = rng.choice(ins)
            f_sim = motor.simular_troca_dezena(idx, d_out, d_in)
            if f_sim is None:
                continue
            f_ap = motor.aplicar_troca_dezena(idx, d_out, d_in)
            av_e2 = avaliar_carteira_etapa2(motor.jogos, pool=pool, fixas=fixas, bloqueadas=bloqueadas, modo_fixas="todos_os_jogos")
            av_ref = avaliar_carteira_ref_etapa4(motor.jogos, pool=pool, fixas=fixas, bloqueadas=bloqueadas, modo_fixas="todos_os_jogos")
            _exigir(abs(f_sim - f_ap) <= 1e-12, f"Simulacao 1-swap divergiu da aplicacao: {f_sim} vs {f_ap}")
            _exigir(abs(f_ap - av_e2["funcao_objetivo_F"]) <= 1e-12, "Motor Etapa 4 divergiu da Etapa 2 apos troca.")
            _exigir(abs(f_ap - av_ref["funcao_objetivo_F"]) <= 1e-12, "Motor Etapa 4 divergiu da Ref Zero-Dep apos troca.")
            aplicados += 1
            if aplicados >= 25:
                break
        _exigir(aplicados >= 20, "Quantidade insuficiente de trocas aplicadas no teste.")

        # 2. Construtivo incremental passo k=1..5 (mista [16, 15, 15, 17, 15])
        spec_g = _resolver_especificacao_etapa4(
            pool, fixas, bloqueadas, "todos_os_jogos", None, 15, [16, 15, 15, 17, 15], None, None, None
        )
        constr = AvaliadorConstrutivoIncrementalEtapa4(spec_g)
        c_parcial = []
        for m_i in [16, 15, 15, 17, 15]:
            cand = tuple(sorted((*fixas, *rng.sample(livres, m_i - len(fixas)))))
            while cand in c_parcial:
                cand = tuple(sorted((*fixas, *rng.sample(livres, m_i - len(fixas)))))
            f_step = constr.simular_adicao_jogo(cand)
            c_parcial.append(cand)
            constr.adicionar_jogo(cand)
            av_e2_p = avaliar_carteira_etapa2(c_parcial, pool=pool, fixas=fixas, bloqueadas=bloqueadas, modo_fixas="todos_os_jogos")
            av_ref_p = avaliar_carteira_ref_etapa4(c_parcial, pool=pool, fixas=fixas, bloqueadas=bloqueadas, modo_fixas="todos_os_jogos")
            _exigir(abs(f_step - av_e2_p["funcao_objetivo_F"]) <= 1e-12, f"Construtivo k={len(c_parcial)} divergiu Etapa 2.")
            _exigir(abs(f_step - av_ref_p["funcao_objetivo_F"]) <= 1e-12, f"Construtivo k={len(c_parcial)} divergiu Ref Zero-Dep.")

    def test_despacho_adaptativo_regimes_descartes_e_limites_parada(self) -> None:
        # 1. Espaco unitario
        r_unit = executar_arquitetura_adaptativa_etapa4(
            pool=list(range(1, 16)),
            bloqueadas=list(range(16, 26)),
            quantidade_jogos=1,
            max_avaliacoes=50,
        )
        _exigir(r_unit["despacho_adaptativo"]["algoritmo_escolhido"] == "busca_exata_pequena", "Unitario deve usar busca exata.")
        _exigir(r_unit["otimo_global_comprovado"] is True, "Unitario deve certificar otimo global.")
        _exigir(r_unit["telemetria"]["criterio_parada"] == "espaco_unitario", "Criterio parada esperado: espaco_unitario.")

        # 2. Espaco pequeno com orcamento >= C(K,J) -> busca_exata_pequena; orcamento menor -> descarta exata
        r_ex = executar_arquitetura_adaptativa_etapa4(
            pool=list(range(1, 17)),
            bloqueadas=[21, 22, 23, 24, 25],
            quantidade_jogos=4,
            max_avaliacoes=2000,
            max_iteracoes=2000,
        )
        _exigir(r_ex["despacho_adaptativo"]["algoritmo_escolhido"] == "busca_exata_pequena", "Pequena c/ B=2000 deve usar exata.")
        _exigir(r_ex["otimo_global_comprovado"] is True, "Enumeracao completa deve certificar otimo global.")
        _exigir(len(r_ex["despacho_adaptativo"]["alternativas_descartadas"]) == len(ALGORITMOS_ETAPA4) - 1, "Deve registrar todos os 5 descartes.")

        r_peq_b_baixo = executar_arquitetura_adaptativa_etapa4(
            pool=list(range(1, 17)),
            bloqueadas=[21, 22, 23, 24, 25],
            quantidade_jogos=4,
            max_avaliacoes=150,
        )
        _exigir(r_peq_b_baixo["despacho_adaptativo"]["algoritmo_escolhido"] != "busca_exata_pequena", "B=150 < 1820 nao pode escolher exata.")
        _exigir(
            "busca_exata_pequena" in r_peq_b_baixo["despacho_adaptativo"]["alternativas_descartadas"],
            "Busca exata deve constar nos descartes com motivo tecnico.",
        )
        _exigir(r_peq_b_baixo["otimo_global_comprovado"] is False, "Heuristica jamais certifica otimo global.")

        # 3. Busca exata interrompida antes do fim -> NUNCA certifica otimo global (Condicionante V)
        r_ex_cort = executar_arquitetura_adaptativa_etapa4(
            pool=list(range(1, 17)),
            bloqueadas=[21, 22, 23, 24, 25],
            quantidade_jogos=4,
            forcar_algoritmo="busca_exata_pequena",
            max_avaliacoes=50,
            max_iteracoes=2000,
        )
        _exigir(r_ex_cort["otimo_global_comprovado"] is False, "Busca exata interrompida em B=50 nao pode marcar otimo global.")
        _exigir(r_ex_cort["telemetria"]["criterio_parada"] == "teto_avaliacoes", "Deve registrar criterio_parada='teto_avaliacoes'.")

        # 4. Baixa latencia / micro-orcamento -> algoritmo_guloso
        spec_25 = _resolver_especificacao_etapa4(list(range(1, 26)), (), (), "todos_os_jogos", 12, 15, None, None, None, None)
        dec_micro = analisar_espaco_e_despachar_etapa4(spec_25, max_avaliacoes=20)
        _exigir(dec_micro["algoritmo_escolhido"] == "algoritmo_guloso", "Micro-orcamento deve despachar guloso.")

        # 5. Medio vs Amplo vs Qualidade Maxima
        spec_med = _resolver_especificacao_etapa4(
            list(range(1, 21)), (1, 2, 3), (21, 22, 23, 24, 25), "todos_os_jogos", 10, 15, None, None, None, None
        )
        dec_med = analisar_espaco_e_despachar_etapa4(spec_med, max_avaliacoes=150)
        _exigir(dec_med["algoritmo_escolhido"] == "busca_local_trocas", "Medio com B=150 deve concentrar em busca_local_trocas.")

        spec_amp = _resolver_especificacao_etapa4(list(range(1, 26)), (), (), "todos_os_jogos", 16, 15, None, None, None, None)
        dec_amp = analisar_espaco_e_despachar_etapa4(spec_amp, max_avaliacoes=320)
        _exigir(dec_amp["algoritmo_escolhido"] == "multiplos_reinicios", "Espaco amplo c/ B=320 deve despachar multiplos_reinicios.")

        dec_alta = analisar_espaco_e_despachar_etapa4(spec_med, max_avaliacoes=600, prioridade="qualidade_maxima")
        _exigir(dec_alta["algoritmo_escolhido"] == "estrategia_combinada", "qualidade_maxima c/ B=600 deve despachar estrategia_combinada.")

        # 6. Limite estrito de memoria/tempo corta execucao com criterio explicito
        r_mem = executar_arquitetura_adaptativa_etapa4(
            pool=list(range(1, 26)),
            quantidade_jogos=12,
            forcar_algoritmo="busca_local_trocas",
            max_avaliacoes=200,
            limite_memoria_mb=0.01,
        )
        _exigir(r_mem["telemetria"]["criterio_parada"] == "limite_memoria", "Limite minimo de RAM deve registrar criterio_parada='limite_memoria'.")

    def test_integracao_etapas_1_2_3_reprodutibilidade_e_fail_closed(self) -> None:
        r1 = executar_arquitetura_adaptativa_etapa4(
            pool=list(range(1, 22)),
            fixas=[1, 2],
            bloqueadas=[22, 23, 24, 25],
            orcamento_brl="42.00",
            tipo_concurso="lotofacil_independencia",
            semente=314,
            max_avaliacoes=200,
        )
        r2 = executar_arquitetura_adaptativa_etapa4(
            pool=list(range(1, 22)),
            fixas=[1, 2],
            bloqueadas=[22, 23, 24, 25],
            orcamento_brl="42.00",
            tipo_concurso="lotofacil_independencia",
            semente=314,
            max_avaliacoes=200,
        )
        _exigir(r1["sha256_execucao"] == r2["sha256_execucao"], "Determinismo SHA-256 quebrado na Etapa 4.")
        _exigir(r1["carteira"] == r2["carteira"], "Determinismo de carteira quebrado na Etapa 4.")
        _exigir(r1["versao_arquitetura"] == VERSAO_ARQUITETURA_ETAPA4, "Versao Etapa 4 divergente.")
        _exigir(r1["versao_objetivo"] == VERSAO_MODELO_OBJETIVO_ETAPA2, "Versao Etapa 2 divergente.")
        _exigir(r1["historico_utilizado"] is None and HISTORICO_GERACAO_ETAPA4 is None, "Historico deve permanecer None.")
        _exigir(
            r1["especificacao"]["regra_caixa_etapa1"]["chave_regra_etapa1"] == "regras_premiacao_independencia",
            "Integracao de regime CAIXA Etapa 1 falhou.",
        )

        # Condicionante VI: seis grandezas distintas e uniao J >= 3 nao calculada diretamente
        g6 = r1["distincao_seis_grandezas_probabilisticas"]
        _exigir(len(g6) == 8, f"Estrutura de distincao probabilistica incompleta (len={len(g6)}).")
        _exigir(g6["5_probabilidade_exata_uniao"]["status"] == "nao_calculada_diretamente", "Uniao J=12 deve permanecer nao_calculada_diretamente.")

        chk = verificar_equivalencia_etapa4_contra_referencia(r1)
        _exigir(chk["equivalente_1e_12"], f"Equivalencia contra referencia zero-dep falhou: {chk}")

        # Casos negativos fail-closed
        casos_invalidos = [
            {"usar_historico": True},
            {"historico": [[1, 2, 3]]},
            {"tipo_concurso": "inexistente"},
            {"prioridade": "magica"},
            {"limite_tempo_segundos": -1.0},
            {"limite_memoria_mb": 0.0},
            {"forcar_algoritmo": "oraculo"},
        ]
        for kw in casos_invalidos:
            falhou = False
            try:
                executar_arquitetura_adaptativa_etapa4(pool=list(range(1, 20)), quantidade_jogos=2, **kw)
            except ErroValidacaoLotofacilError:
                falhou = True
            _exigir(falhou, f"Caso invalido nao falhou em modo fail-closed: {kw}")

    def test_evidencias_etapa4_geradas_e_integridade(self) -> None:
        caminho_json = os.path.join(BASE_DIR, "auditoria", "lotofacil_modo4", "etapa_04_evidencias.json")
        caminho_md = os.path.join(BASE_DIR, "auditoria", "lotofacil_modo4", "ETAPA_04_ARQUITETURA_ADAPTATIVA.md")
        _exigir(os.path.isfile(caminho_json), f"Arquivo ausente: {caminho_json}")
        _exigir(os.path.isfile(caminho_md), f"Relatorio ausente: {caminho_md}")

        with open(caminho_json, "r", encoding="utf-8") as f:
            doc = json.load(f)
        with open(caminho_md, "r", encoding="utf-8") as f:
            md = f.read()

        _exigir("\u2014" not in md and "\u2013" not in md, "Relatorio MD contem travessao proibido.")
        _exigir(doc["independencia_referencia_ast"]["etapa4_zero_dependencia"]["independencia_comprovada"] is True, "Independencia AST deve constar como True.")
        _exigir(doc["preservacao_etapas_anteriores"]["pos_execucao_ok"] is True, "Preservacao pos-Etapa 4 deve ser True.")
        _exigir(doc["verificacao_referencia_independente"]["todas_equivalentes_1e_12_e_conformes"] is True, "Conferencia independente falhou no JSON.")
        _exigir(doc["verificacao_referencia_independente"]["total_execucoes_conferidas"] >= 60, "Esperado ao menos 60 execucoes conferidas.")
        _exigir(doc["prova_exata_mista_referencia"]["coincide_carteira_e_score"] is True, "Prova exata mista deve coincidir com referencia.")
        _exigir(len(doc["resumo_despacho_adaptativo"]) == 10, "Devem existir 10 instancias no resumo adaptativo.")

        # Validar campos obrigatorios de telemetria justa (Requisito 3.2) em todas as linhas
        for inst_id, bloco in doc["benchmarks_escalabilidade"].items():
            for row in bloco["tabela_comparativa"]:
                for campo in (
                    "orcamento_max_avaliacoes",
                    "avaliacoes_efetivas",
                    "taxa_utilizacao_orcamento",
                    "quantidade_reinicios",
                    "criterio_parada",
                    "tempo_total_segundos",
                    "memoria_maxima_bytes",
                    "funcao_objetivo_F",
                ):
                    _exigir(campo in row, f"Campo '{campo}' ausente em {inst_id}.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
