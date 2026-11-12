#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTE 1: EQUIVALÊNCIA MATEMÁTICA E DE RASTREAMENTO INTERMEDIÁRIO (MODO 4 v1.2)
=============================================================================
Compara registro a registro o módulo independente `motor_lotomania_modo4.py`
contra a referência oficial `motor_lotomania.py` (`MotorLotomaniaB2B`) sem
utilizar instruções `assert` (compatível com `python -O`, lançando `RuntimeError`
explícito diante de qualquer divergência):
1. Hashes SHA-256 completos (64 caracteres hex) do pacote de referência, do motor
   original (`motor_lotomania.py`) e da base histórica `data/lotomania.json` (corte fixo 2699).
2. Invariância da semente e política `historico=None` (filtro 7..13 desativado).
3. Equivalência exata nas 10 sementes (330001..330010): jogos, SHA-256 v1 e v2.
4. Comparação registro a registro das 189 etapas intermediárias de seleção
   (15.120 candidatos avaliados, interseções, R_win, P_inter, Delta_V, custos
   inteiros na escala 5*10^14 e reprodução exata dos 7 empates em Q).
"""

from fractions import Fraction
import importlib.util
import json
import os
import sys
import unittest

DIR_TESTES = os.path.dirname(os.path.abspath(__file__))
DIR_RAIZ = os.path.dirname(DIR_TESTES)
if DIR_RAIZ not in sys.path:
    sys.path.insert(0, DIR_RAIZ)

from motor_lotomania_modo4 import MotorLotomaniaModo4
from verificador_selo_modo4 import (
    PARAMETROS_HOMOLOGADOS_V1_2,
    calcular_sha256_arquivo,
    verificar_selo_modo4,
)

SEEDS_10 = list(range(330001, 330011))

HASHES_V1_REFERENCIA = {
    330001: "a98c0b0267b1c2d91c630b363bb9be6744dd1d2a6d6943d447f869d705844f0f",
    330002: "c5c3f21ca9bee8ad107d169619763f6a6e527b33e08d343423feabc4be5fbb71",
    330003: "8a50e329b767a1a0f7394646265d408d47a16e2dedd1194e749fb286c77b035e",
    330004: "5d6579b2f452eb826fe702017875c24624552b187563223b874d4c4a884ff07b",
    330005: "560233f78dbdc071c4cf41005d7aa98ce507b30e073683b022492a73382b9f5c",
    330006: "56ca8dd40c00e11b907a740179fd4fbc851b5a0b4fd0c9be4cd96c1523583455",
    330007: "a9abe41b8d391690c34c4c25f6cdb44455c1d1b175eb3e0730c369b078c797bf",
    330008: "ccb4390a4a9383bf7b20e662817b4360b51782e503d163ebd8b806903910c13c",
    330009: "dbf05f13b93f5d9b849f67ef927ee640101657b0f22eebc1583ffe2a6086c3f0",
    330010: "d5faaad0be1cb03cc471d4e94f39491a5106e565f8198889cf865d2059ce8480",
}

HASHES_V2_REFERENCIA = {
    330001: "31a34473b0fe1e09f00dca01cebccc2a96abc59331bb472df926d2735a3b211f",
    330002: "a9764997aafb36c8357b9dde03880e0371873899a55b1c8953924c06aded9064",
    330003: "8e0470f2c55fbee21074a1932557fffa0a71a3116856965d2397d180dc019d10",
    330004: "2131a62d501d235e039693aef18cfae839adebe083e8423cdc81a871f15cd55f",
    330005: "0a22ae4b8e28f9bebfec4af98fff26775f29403e55e5ee71bfae718628705d2c",
    330006: "e527bf00e3f295476561be3892f69b4c076561b0192fad389cb70666c699caba",
    330007: "fbb9081b8ec614f97c146842a1a81c64909fa84e1dfe732d927972b426362198",
    330008: "ba553f4a1f3be3b8f981bca7db9fb25f0249f056eb0f9451ce0c292ed7b984cf",
    330009: "5320296decd82a10bd4613625407c578bb32b62edce319b936019a6d2ef7f1c8",
    330010: "8fcf590b3767542663588bda426c35221f8debdfd09bb512c298c083106d21b1",
}


def exigir(condicao: bool, mensagem: str) -> None:
    if condicao is not True:
        raise RuntimeError(f"Falha no teste de equivalencia: {mensagem}")


def carregar_motor_referencia():
    """Carrega o arquivo oficial motor_lotomania.py (MotorLotomaniaB2B) para comparação direta."""
    hash_esperado = PARAMETROS_HOMOLOGADOS_V1_2["sha256_motor_referencia_original"]
    caminhos_possiveis = [
        os.path.join(DIR_RAIZ, "motor_lotomania.py"),
        os.path.join(DIR_RAIZ, "motor_lotomania_ref.py"),
        r"C:\Users\Luis Brun\.gemini\antigravity\brain\f3af3942-aca3-4c9a-a3dd-e56f90feb848\scratch\ref\motor_lotomania.py",
    ]
    for cam in caminhos_possiveis:
        if os.path.isfile(cam):
            h = calcular_sha256_arquivo(cam)
            if h == hash_esperado:
                spec = importlib.util.spec_from_file_location("motor_lotomania_ref_mod", cam)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                return mod.MotorLotomaniaB2B, cam, h
    raise RuntimeError("Arquivo motor_lotomania.py de referência com hash esperado não encontrado.")


def verificar_identidade_delta_v_casos_borda() -> dict:
    """
    Comprova algebricamente em aritmética racional exata (Fraction) que a variação
    de dispersão V(u') - V(u) ao inserir um bilhete G de 50 dezenas em carteira de
    M_sel jogos obedece identicamente a Delta_V = 2 * sum_{n in G}(u_n - m_ant) + 25
    = 2 * sum_{n in G} u_n - 50 * M_sel + 25 em casos extremos e gerais.
    """
    def _dispersao_exata(contadores: dict) -> Fraction:
        m = Fraction(sum(contadores.values()), 100)
        return sum((Fraction(contadores[n]) - m) ** 2 for n in range(1, 101))

    def _aplicar_e_conferir(jogos_existentes: list, novo_jogo: list, esperado: int) -> None:
        m_sel = len(jogos_existentes)
        u = {n: 0 for n in range(1, 101)}
        for jg in jogos_existentes:
            for n in jg:
                u[n] += 1
        m_ant = Fraction(50 * m_sel, 100)
        v1 = _dispersao_exata(u)
        u_pos = dict(u)
        for n in novo_jogo:
            u_pos[n] += 1
        v2 = _dispersao_exata(u_pos)
        dv_direto = v2 - v1
        dv_formula_m = Fraction(2) * sum(Fraction(u[n]) - m_ant for n in novo_jogo) + Fraction(25)
        dv_formula_int = Fraction(2 * sum(u[n] for n in novo_jogo) - 50 * m_sel + 25)
        exigir(dv_direto == dv_formula_m == dv_formula_int == Fraction(esperado), (
            f"Falha na identidade Delta V (M_sel={m_sel}): direto={dv_direto}, "
            f"formula_m={dv_formula_m}, esperado={esperado}"
        ))

    j_base = list(range(1, 51))
    j_espelho = list(range(51, 101))
    j_medio = list(range(1, 26)) + list(range(51, 76))

    # M_sel = 0 (carteira vazia -> +25)
    _aplicar_e_conferir([], j_base, 25)
    # M_sel = 1, espelho k=0 (-25), identico k=50 (+75), medio k=25 (+25)
    _aplicar_e_conferir([j_base], j_espelho, -25)
    _aplicar_e_conferir([j_base], j_base, 75)
    _aplicar_e_conferir([j_base], j_medio, 25)

    return {
        "m_sel_0": 25,
        "m_sel_1_espelho_k0": -25,
        "m_sel_1_identico_k50": 75,
        "m_sel_1_corte_k25": 25,
    }


def executar_testes_equivalencia() -> dict:
    casos_borda_delta_v = verificar_identidade_delta_v_casos_borda()
    cls_ref, cam_ref, hash_ref = carregar_motor_referencia()

    # 1. Verificar selo criptográfico e hash da base histórica (corte fixo no concurso 2699)
    status_selo = verificar_selo_modo4(DIR_RAIZ)
    exigir(status_selo.get("selo_valido") is True, "Selo criptográfico inválido.")

    cam_hist = os.path.join(DIR_RAIZ, "data", "lotomania.json")
    hash_hist = calcular_sha256_arquivo(cam_hist)
    exigir(
        hash_hist == PARAMETROS_HOMOLOGADOS_V1_2["sha256_base_historica_corte_2699"],
        "Hash da base histórica data/lotomania.json diverge do corte 2699.",
    )
    with open(cam_hist, "r", encoding="utf-8") as f:
        dados_hist = json.load(f)
    exigir(len(dados_hist) == 2699, f"Total de concursos diverge de 2699: {len(dados_hist)}")
    exigir("2699" in dados_hist, "Concurso 2699 ausente em data/lotomania.json.")

    # 2. Verificar que MotorLotomaniaModo4 opera estritamente com historico=None e sem filtro 7..13
    exigir(MotorLotomaniaModo4.HISTORICO_GERACAO is None, "HISTORICO_GERACAO deve ser None.")
    exigir(
        MotorLotomaniaModo4.FILTRO_REPETICAO_ULTIMO_CONCURSO_ATIVO is False,
        "FILTRO_REPETICAO_ULTIMO_CONCURSO_ATIVO deve ser False.",
    )
    rejeitou_historico_construtor = False
    try:
        MotorLotomaniaModo4(historico=dados_hist)
    except TypeError:
        rejeitou_historico_construtor = True
    exigir(rejeitou_historico_construtor is True, "Construtor não rejeitou argumento historico.")

    motor_m4 = MotorLotomaniaModo4(verificar_selo=True, diretorio_base=DIR_RAIZ)
    res_sem_hist = motor_m4.gerar_carteira_otimizada_cobertura(20, seed=330001, permitir_espelhos=True)
    exigir(
        res_sem_hist["hash_carteira_sha256_v1"] == HASHES_V1_REFERENCIA[330001],
        "Hash v1 para seed=330001 diverge da referência.",
    )

    # 3. Comparar as 10 sementes homologadas (330001..330010) e as 189 etapas intermediárias
    motor_ref = cls_ref(historico=None)
    total_etapas = 0
    total_candidatos = 0
    total_delta_v_verificados = 0
    minimos_estritos = 0
    total_minimizadores_empates = 0
    empates_exatos_q = []
    hashes_verificados = {}

    for idx_rodada, seed in enumerate(SEEDS_10, start=1):
        res_ref = motor_ref.gerar_carteira_otimizada_cobertura(
            quantidade_jogos=20,
            seed=seed,
            permitir_espelhos=True,
        )
        res_m4 = motor_m4.gerar_carteira_otimizada_cobertura(
            quantidade_jogos=20,
            seed=seed,
            permitir_espelhos=True,
            trace=True,
        )

        # Jogos finais e métricas de cobertura idênticos à referência
        exigir(res_m4["jogos"] == res_ref["jogos"], f"Jogos divergentes na semente {seed}")
        exigir(
            res_m4["hash_carteira_sha256_v1"] == HASHES_V1_REFERENCIA[seed],
            f"Hash v1 divergente na semente {seed}",
        )
        exigir(
            res_m4["hash_carteira_sha256_v2_canonico"] == HASHES_V2_REFERENCIA[seed],
            f"Hash v2 divergente na semente {seed}",
        )

        mc_ref = res_ref["metricas_cobertura"]
        mc_m4 = res_m4["metricas_cobertura"]
        exigir(mc_m4["intersecao_minima"] == mc_ref["intersecao_minima"], "intersecao_minima diverge.")
        exigir(mc_m4["intersecao_media"] == mc_ref["intersecao_media"], "intersecao_media diverge.")
        exigir(mc_m4["intersecao_maxima"] == mc_ref["intersecao_maxima"], "intersecao_maxima diverge.")
        exigir(mc_m4["soma_intersecoes_real"] == mc_ref["soma_intersecoes_real"], "soma_intersecoes_real diverge.")
        exigir(
            mc_m4["soma_minima_teorema_contagem_dupla"] == mc_ref["soma_minima_teorema_contagem_dupla"],
            "soma_minima_teorema_contagem_dupla diverge.",
        )
        exigir(
            mc_m4["desvio_padrao_alocacao_dezenas"] == mc_ref["desvio_padrao_alocacao_dezenas"],
            "desvio_padrao_alocacao_dezenas diverge.",
        )
        exigir(
            mc_m4["cobertura_global_sorteios_premiados"]["cota_inferior_bonferroni_sorteios_premiados"]
            == mc_ref["cobertura_global_sorteios_premiados"]["cota_inferior_bonferroni_sorteios_premiados"],
            "cota_inferior_bonferroni_sorteios_premiados diverge.",
        )

        hashes_verificados[str(seed)] = {
            "hash_v1": res_m4["hash_carteira_sha256_v1"],
            "hash_v2_canonico": res_m4["hash_carteira_sha256_v2_canonico"],
        }

        etapas = res_m4["rastreamento_etapas"]
        for et in etapas:
            total_etapas += 1
            exigir(et["candidatos_avaliados"] == 80, "candidatos_avaliados != 80.")
            exigir(len(et["candidatos"]) == 80, "len(candidatos) != 80.")
            total_candidatos += len(et["candidatos"])

            idx_bilhete = et["etapa"] - 1
            exigir(
                res_m4["jogos"][idx_bilhete] == et["vencedor_dezenas"],
                "Bilhete vencedor da etapa diverge do jogo na carteira final.",
            )

            # Reconstroi contadores exatos de uso antes da etapa (M_sel = idx_bilhete)
            m_sel_et = idx_bilhete
            uso_et = [0] * 101
            for jg_ant in res_m4["jogos"][:m_sel_et]:
                for d_ant in jg_ant:
                    uso_et[d_ant] += 1
            v4_antes = sum((2 * uso_et[n] - m_sel_et) ** 2 for n in range(1, 101))

            min_custo_int = min(c["custo_inteiro_5e14"] for c in et["candidatos"])
            minimizadores_et = []
            for cand_reg in et["candidatos"]:
                cset = set(cand_reg["dezenas"])
                v4_depois = sum(
                    (2 * (uso_et[n] + (1 if n in cset else 0)) - (m_sel_et + 1)) ** 2
                    for n in range(1, 101)
                )
                diff_v4 = v4_depois - v4_antes
                exigir(diff_v4 % 4 == 0, "4 * Delta V não múltiplo de 4.")
                dv_direto_int = diff_v4 // 4
                dv_formula_rec = 2 * sum(uso_et[n] for n in cand_reg["dezenas"]) - 50 * m_sel_et + 25
                exigir(
                    dv_direto_int == dv_formula_rec == cand_reg["delta_v_int"]
                    and abs(cand_reg["delta_v"] - float(dv_direto_int)) < 1e-9,
                    f"Divergência Delta V na seed {seed}, etapa {et['etapa']}: {dv_direto_int} vs {cand_reg['delta_v_int']}",
                )
                total_delta_v_verificados += 1
                if cand_reg["custo_inteiro_5e14"] == min_custo_int:
                    minimizadores_et.append(cand_reg)

            if et["empate_exato_q"]:
                exigir(len(minimizadores_et) >= 2, "Etapa marcada como empate com menos de 2 minimizadores.")
                custos_racionais_q = {
                    Fraction(c["r_win"], 10**16) + Fraction(30 * c["pen_inter"]) + Fraction(c["delta_v_int"], 20)
                    for c in minimizadores_et
                }
                exigir(len(custos_racionais_q) == 1, "Minimizadores empatados não coincidem exatamente em Q!")
                total_minimizadores_empates += len(minimizadores_et)
                empates_exatos_q.append({
                    "rodada": idx_rodada,
                    "seed": seed,
                    "etapa_bilhete": et["etapa"],
                    "minimizadores_empatados_qtd": len(minimizadores_et),
                    "vencedor_ordem_avaliacao": et["vencedor_ordem_avaliacao"],
                    "segundo_ordem_avaliacao": et["segundo_ordem_avaliacao"],
                    "custo_inteiro_5e14": et["vencedor_custo_inteiro_5e14"],
                    "custo_total": et["vencedor_custo_total"],
                })
                exigir(
                    et["vencedor_ordem_avaliacao"] < et["segundo_ordem_avaliacao"],
                    "Ordem de desempate inválida no empate exato em Q.",
                )
            else:
                exigir(len(minimizadores_et) == 1, "Mínimo estrito apresentou múltiplos minimizadores inteiros.")
                minimos_estritos += 1
                exigir(
                    et["vencedor_custo_inteiro_5e14"] < et["segundo_custo_inteiro_5e14"],
                    "Mínimo estrito sem desigualdade estrita no custo inteiro.",
                )

    exigir(total_etapas == 189, f"Esperado 189 etapas, obtido {total_etapas}")
    exigir(minimos_estritos == 182, f"Esperado 182 mínimos estritos, obtido {minimos_estritos}")
    exigir(len(empates_exatos_q) == 7, f"Esperado 7 empates exatos em Q, obtido {len(empates_exatos_q)}")
    exigir(
        total_minimizadores_empates == 33,
        f"Esperado total de 33 minimizadores conjuntos nas 7 etapas empatadas, obtido {total_minimizadores_empates}",
    )
    exigir(total_candidatos == 15120, f"Esperado 15.120 candidatos avaliados, obtido {total_candidatos}")
    exigir(total_delta_v_verificados == 15120, f"Esperado 15.120 verificações Delta V, obtido {total_delta_v_verificados}")

    # 4. Confrontar diretamente com o artefato detalhamento_7_etapas_empates.json
    cam_det7 = r"C:\Users\Luis Brun\.gemini\antigravity\brain\f3af3942-aca3-4c9a-a3dd-e56f90feb848\detalhamento_7_etapas_empates.json"
    if os.path.isfile(cam_det7):
        with open(cam_det7, "r", encoding="utf-8") as f:
            det7_ref = json.load(f)
        exigir(len(det7_ref) == len(empates_exatos_q) == 7, "Quantidade de empates diverge de 7.")
        for item_ref, item_m4 in zip(det7_ref, empates_exatos_q):
            exigir(item_m4["rodada"] == item_ref["rodada"], "Rodada do empate diverge.")
            exigir(item_m4["seed"] == item_ref["seed_carteira"], "Seed do empate diverge.")
            exigir(item_m4["etapa_bilhete"] == item_ref["etapa_bilhete"], "Etapa do empate diverge.")
            exigir(
                item_m4["minimizadores_empatados_qtd"] == item_ref["minimizadores_empatados_qtd"],
                "Quantidade de minimizadores empatados diverge da referência.",
            )
            exigir(
                item_m4["vencedor_ordem_avaliacao"] == item_ref["vencedor_selecionado"]["cand_eval"],
                "Ordem do vencedor no empate diverge.",
            )

    return {
        "sucesso": True,
        "hash_pacote_auditoria_referencia": PARAMETROS_HOMOLOGADOS_V1_2["sha256_pacote_auditoria_referencia"],
        "arquivo_fisico_motor_referencia": "motor_lotomania.py",
        "hash_motor_referencia_original": hash_ref,
        "hash_base_historica_corte_2699": hash_hist,
        "concurso_corte": 2699,
        "historico_geracao": None,
        "filtro_repeticao_ultimo_concurso_ativo": False,
        "casos_borda_delta_v": casos_borda_delta_v,
        "sementes_testadas": len(SEEDS_10),
        "total_etapas_verificadas": total_etapas,
        "minimos_estritos_verificados": minimos_estritos,
        "empates_exatos_q_reproduzidos": len(empates_exatos_q),
        "total_minimizadores_conjuntos_empates": total_minimizadores_empates,
        "total_candidatos_intermediarios_verificados": total_candidatos,
        "total_verificacoes_exatas_delta_v": total_delta_v_verificados,
        "detalhe_7_empates_q": empates_exatos_q,
        "hashes_10_sementes": hashes_verificados,
    }


def test_identidade_delta_v_casos_borda():
    res = verificar_identidade_delta_v_casos_borda()
    exigir(res["m_sel_1_espelho_k0"] == -25 and res["m_sel_1_identico_k50"] == 75, "Falha em casos-borda Delta V.")


def test_equivalencia_189_etapas_e_33_minimizadores_q():
    res = executar_testes_equivalencia()
    exigir(res["sucesso"] is True, "Falha na equivalência completa.")
    exigir(res["total_minimizadores_conjuntos_empates"] == 33, "33 minimizadores conjuntos não confirmados.")


class TestModo4Equivalencia(unittest.TestCase):
    def test_delta_v_casos_borda(self):
        test_identidade_delta_v_casos_borda()

    def test_equivalencia_registro_a_registro_10_sementes(self):
        test_equivalencia_189_etapas_e_33_minimizadores_q()


if __name__ == "__main__":
    resultado = executar_testes_equivalencia()
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
