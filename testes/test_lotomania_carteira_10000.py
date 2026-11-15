# -*- coding: utf-8 -*-
"""
Suite de testes T1-T10 da implementacao isolada `lotomania_carteira_10000`
(Ordem 5-R3 + S1_atual_top8 + 1.080.000 tentativas).

Executada sem instrucoes `assert` para total paridade entre `python` e `python -O`.
"""

from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import math
import os
import subprocess
import sys
import tempfile
import unittest

DIR_TESTES = os.path.dirname(os.path.abspath(__file__))
DIR_RAIZ = os.path.dirname(DIR_TESTES)
if DIR_RAIZ not in sys.path:
    sys.path.insert(0, DIR_RAIZ)

from lotomania_carteira_10000 import (  # noqa: E402
    BASELINE_ORDEM4_10000_REFERENCIA,
    BLOCK_OF,
    FAIXAS_PREMIACAO,
    TABELA_OVERLAP_BIVARIADA,
    TABELA_OVERLAP_FAIXAS,
    TABELA_OVERLAP_PREMIADOS,
    VERSAO_ALGORITMO,
    auditar_carteira_completa,
    avaliar_e_aplicar_swap_fase3,
    calcular_coocorrencia_global_bruta,
    calcular_delta_phi2_exato_candidato,
    calcular_hashes_certificados,
    calcular_n2_celula,
    capturar_snapshot_estado,
    classificar_homologacao_kmax,
    comparar_estado_snapshot,
    gerar_carteira_10000_otimizada,
    inicializar_carteira_fase12,
    validar_bilhete_individual,
    validar_entrada_carteira,
    validar_trilha_jsonl_em_disco,
)
from lotomania_carteira_10000.__main__ import executar_benchmark_ordem6_passo1  # noqa: E402
from verificador_selo_modo4 import verificar_selo_modo4  # noqa: E402

HASHES_ARQUIVOS_PROTEGIDOS = {
    "lotofacil_modo4/promocao_producao.py": "5bc19c7e8313f0042afd7414373de334ddb6832350789c1c026aca3996a66996",
    "api.py": "d60cad46afbf563530a77e4950b142c1ebd54bcd2fef2e17bc23d84fc9de7c0b",
    "motor_lotofacil.py": "7dcaf017f8a4845fe42f5a58cb978c81e95e8f55b96ef558b9a0ec551ba077c3",
    "js/engines/motor_lotofacil_modo4_engine.js": "943b4bba0a6928dfc9402c6f5f57598a7820302b4faaa3a10c48528a11231413",
    "index.html": "639bf551a59a3eeef9b1ee322ba16e9eeb6bc3477616338fef996fc155a12de0",
    "js/ui.js": "e11df28bae9c9671b5ea4a69dfd389c8c66663ecf4caf139be56f0b2f14ca427",
    "B2B_Loterias_Mobile.html": "22d7439d279073dae543eb1a8c89649dd38abe18c5dd76727edfff29b2ac02e3",
    "motor_lotomania_modo4.py": "94a2d1001d235e0e9bd543aeee697bac0ac6c60b1d24654838e452d6f42c68f9",
    "verificador_selo_modo4.py": "632388d3c58aee37ae41cd33e44ddd8fad78ea22ebdb339f2aff4fae59b89e46",
    "chave_publica_modo4.pem": "d810ed9f31f476b159590cd2e053632dc32e8e6e62a5a17f7c2f371a45084b0f",
    "data/lotomania.json": "3f11b71e15b936940c8cef40cf39c0a67f5c47f7a15b12a8c2608763ec39f873",
}

HISTOGRAMA_BASELINE_ORDEM4 = {
    11: 3,
    12: 10,
    13: 114,
    14: 719,
    15: 3731,
    16: 16535,
    17: 62025,
    18: 193553,
    19: 517689,
    20: 1180911,
    21: 2308764,
    22: 3891592,
    23: 5663544,
    24: 7127251,
    25: 7787076,
    26: 7309805,
    27: 5833086,
    28: 3960349,
    29: 2293428,
    30: 1130631,
    31: 475552,
    32: 169684,
    33: 51890,
    34: 13432,
    35: 2997,
    36: 531,
    37: 93,
    38: 4,
    39: 1,
}


def _sha256_arquivo(rel_path: str) -> str:
    abs_path = os.path.join(DIR_RAIZ, rel_path.replace("/", os.sep))
    with open(abs_path, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


class TestLotomaniaCarteira10000(unittest.TestCase):
    """Bateria normativa T1-T10 da Ordem 5-R3 para Lotomania 10.000 jogos."""

    def test_01_selos_preservados_r1_curto_circuito_e_hashes_duplos(self):
        for rel_path, sha_esp in HASHES_ARQUIVOS_PROTEGIDOS.items():
            self.assertEqual(
                _sha256_arquivo(rel_path),
                sha_esp,
                f"Arquivo protegido alterado: {rel_path}",
            )
        selo = verificar_selo_modo4()
        self.assertTrue(selo["selo_valido"])

        base_validos = list(range(1, 51))
        entradas_invalidas = [
            [1],
            {1: 2},
            set(),
            True,
            False,
            10.0,
            "10",
            Decimal("10"),
            None,
            [True] * 50,
            [10.0] * 50,
            base_validos[:49] + [True],
            base_validos[:49] + ["50"],
            base_validos[:49] + [10.0],
            base_validos[:49] + [Decimal("50")],
            base_validos[:49] + [0],
            base_validos[:49] + [101],
            [1] * 50,
        ]
        for cand in entradas_invalidas:
            ok, info = validar_bilhete_individual(cand)
            self.assertFalse(ok, f"Entrada invalida aceita inesperadamente: {cand!r}")
            self.assertFalse(info["ok"])
            self.assertGreaterEqual(len(info["violacoes"]), 1)

        carteira_demo = [list(range(1, 51)), list(range(51, 101))]
        c1 = calcular_hashes_certificados(
            carteira_demo, seed=1, J=2, max_tentativas_f3=10, versao_algoritmo=VERSAO_ALGORITMO
        )
        c2 = calcular_hashes_certificados(
            carteira_demo, seed=2, J=2, max_tentativas_f3=10, versao_algoritmo=VERSAO_ALGORITMO
        )
        self.assertEqual(c1["hash_carteira_sha256_v1"], c2["hash_carteira_sha256_v1"])
        self.assertNotEqual(
            c1["hash_carteira_sha256_v2_canonico"],
            c2["hash_carteira_sha256_v2_canonico"],
        )

    def test_02_carteira_j200_travas_r1_a_r12_e_trilha(self):
        with tempfile.TemporaryDirectory(prefix="ltm_t2_") as tmp:
            trilha = os.path.join(tmp, "trilha_200.jsonl")
            rel = gerar_carteira_10000_otimizada(
                seed=330001,
                J=200,
                max_tentativas_f3=60000,
                passo_checkpoint=20000,
                auditar_100pct_swaps=True,
                auditar_intersecoes_bruto=True,
                caminho_trilha_jsonl=trilha,
            )
            aud = auditar_carteira_completa(rel["jogos"], teto_kmax=35)
            self.assertTrue(aud["aprovacao_restricoes"]["todas_travas_aprovadas"])
            self.assertEqual(aud["fechamento"]["total_jogos"], 200)
            self.assertEqual(aud["fechamento"]["u_min"], 100)
            self.assertEqual(aud["fechamento"]["u_max"], 100)
            self.assertEqual(aud["fechamento"]["intersecao_par_inicial"], 0)
            self.assertLessEqual(rel["pos_fase3"]["phi2"], rel["pre_fase3"]["phi2"])
            self.assertLessEqual(
                rel["pos_fase3"]["q_global_plus"], rel["pre_fase3"]["q_global_plus"]
            )
            self.assertLessEqual(rel["pos_fase3"]["d_max"], rel["pre_fase3"]["d_max"])
            self.assertLessEqual(rel["pos_fase3"]["P_gt_25"], rel["pre_fase3"]["P_gt_25"])
            self.assertLessEqual(
                int(rel["pos_fase3"]["R_win"]), int(rel["pre_fase3"]["R_win"])
            )
            self.assertEqual(len(rel["checkpoints_60k"]), 3)
            self.assertGreater(rel["swaps_aceitos"], 0)
            n_trilha = validar_trilha_jsonl_em_disco(
                trilha,
                rel["pre_fase3"]["sha256_estado_inicial_fase3"],
                rel["auditoria_restricoes"]["sha256_estado_canonico"],
                rel["swaps_aceitos"],
            )
            self.assertEqual(n_trilha, rel["swaps_aceitos"])

    def test_03_carteira_j2000_escalabilidade_e_contagem_dupla(self):
        rel = gerar_carteira_10000_otimizada(
            seed=330001,
            J=2000,
            max_tentativas_f3=60000,
            passo_checkpoint=30000,
            auditar_100pct_swaps=True,
            auditar_intersecoes_bruto=False,
        )
        aud = auditar_carteira_completa(rel["jogos"], teto_kmax=35)
        self.assertTrue(aud["aprovacao_restricoes"]["todas_travas_aprovadas"])
        self.assertEqual(aud["fechamento"]["total_jogos"], 2000)
        self.assertEqual(aud["fechamento"]["u_min"], 1000)
        self.assertEqual(aud["fechamento"]["u_max"], 1000)
        self.assertLessEqual(aud["fechamento"]["k_max"], rel["pre_fase3"]["teto_fase3"])
        self.assertLess(rel["pos_fase3"]["phi2"], rel["pre_fase3"]["phi2"])
        self.assertLess(rel["pos_fase3"]["q_global_plus"], rel["pre_fase3"]["q_global_plus"])

    def test_04_atomicidade_9_falhas_injetadas_e_limites_j2_j4(self):
        r_j2 = gerar_carteira_10000_otimizada(seed=330001, J=2, max_tentativas_f3=100)
        self.assertEqual(r_j2["swaps_aceitos"], 0)
        aud_j2 = auditar_carteira_completa(r_j2["jogos"], teto_kmax=35)
        self.assertTrue(aud_j2["aprovacao_restricoes"]["todas_travas_aprovadas"])

        r_j4 = gerar_carteira_10000_otimizada(seed=330001, J=4, max_tentativas_f3=200)
        aud_j4 = auditar_carteira_completa(r_j4["jogos"], teto_kmax=35)
        self.assertTrue(aud_j4["aprovacao_restricoes"]["todas_travas_aprovadas"])

        rnd, estado = inicializar_carteira_fase12(seed=330001, J=200)
        snap_mestre = capturar_snapshot_estado(estado)
        pares_34_35 = estado["pares_34_35"]
        pares_32_33 = estado["pares_32_33"]
        n_34 = len(pares_34_35)
        n_32 = len(pares_32_33)

        tentativa_viavel = None
        for prop in range(5000):
            mod4 = prop & 3
            if mod4 == 0 and n_34 > 0:
                u_idx, v_idx = pares_34_35[rnd.randrange(n_34)]
                if ((prop & 4) != 0 and v_idx >= 2) or u_idx < 2:
                    u_idx, v_idx = v_idx, u_idx
            elif mod4 == 1 and n_32 > 0:
                u_idx, v_idx = pares_32_33[rnd.randrange(n_32)]
                if ((prop & 4) != 0 and v_idx >= 2) or u_idx < 2:
                    u_idx, v_idx = v_idx, u_idx
            else:
                u_idx = rnd.randrange(2, 200)
                v_idx = u_idx
            if u_idx < 2:
                u_idx = rnd.randrange(2, 200)
            w_idx = rnd.randrange(2, 200)
            if w_idx == u_idx or w_idx == v_idx:
                continue
            r_block = rnd.randrange(5)

            estado_probe = {
                **capturar_snapshot_estado(estado),
                "seed": estado["seed"],
                "J": estado["J"],
                "k_star": estado["k_star"],
                "teto_fase3": estado["teto_fase3"],
                "estado_canonico_buf": bytearray(snap_mestre["estado_canonico_buf"]),
                "rej_sem_par_xy": 0,
                "rej_phi2": 0,
                "rej_r1_r10": 0,
                "rej_q_plus_ou_dmax": 0,
                "rej_kmax": 0,
                "rej_p25_rwin": 0,
                "rej_excecao": 0,
                "recalculos_dmax_queda": 0,
                "cadeia_hashes_integra": True,
                "amostra_primeiros_swaps": [],
                "amostra_ultimos_swaps": [],
            }
            st_p, _ = avaliar_e_aplicar_swap_fase3(
                estado_probe,
                u_idx,
                v_idx,
                w_idx,
                r_block,
                prop,
                falha_injetada=None,
                auditar_100pct_swaps=True,
                auditar_intersecoes_bruto=True,
            )
            if st_p == "ACEITO":
                tentativa_viavel = (u_idx, v_idx, w_idx, r_block, prop)
                break

        self.assertIsNotNone(tentativa_viavel)
        u_idx, v_idx, w_idx, r_block, prop = tentativa_viavel

        cenarios_falha = [
            ("delta_phi2_positivo", "rej_phi2"),
            ("violacao_r1_r10", "rej_r1_r10"),
            ("violacao_dmax", "rej_q_plus_ou_dmax"),
            ("violacao_q_plus", "rej_q_plus_ou_dmax"),
            ("violacao_kmax", "rej_kmax"),
            ("violacao_p25", "rej_p25_rwin"),
            ("violacao_rwin", "rej_p25_rwin"),
            ("empate_sem_melhora", "rej_p25_rwin"),
            ("excecao_interna", "excecao_revertida"),
        ]
        for falha, esperado in cenarios_falha:
            st_ret, reg_ret = avaliar_e_aplicar_swap_fase3(
                estado,
                u_idx,
                v_idx,
                w_idx,
                r_block,
                prop,
                falha_injetada=falha,
                auditar_100pct_swaps=True,
                auditar_intersecoes_bruto=True,
            )
            self.assertEqual(st_ret, esperado, f"Cenario {falha} retornou {st_ret}")
            self.assertIsNone(reg_ret)
            self.assertEqual(comparar_estado_snapshot(estado, snap_mestre), [])

        st_ok, reg_ok = avaliar_e_aplicar_swap_fase3(
            estado,
            u_idx,
            v_idx,
            w_idx,
            r_block,
            prop,
            falha_injetada=None,
            auditar_100pct_swaps=True,
            auditar_intersecoes_bruto=True,
        )
        self.assertEqual(st_ok, "ACEITO")
        self.assertIsNotNone(reg_ok)
        self.assertEqual(reg_ok["sha256_estado_antes"], snap_mestre["sha256_estado_atual"])
        self.assertNotEqual(reg_ok["sha256_estado_depois"], reg_ok["sha256_estado_antes"])

    def test_05_identidade_delta_phi2_global_e_nao_compensacao_q_plus(self):
        _, estado = inicializar_carteira_fase12(seed=330001, J=200)
        jogos = estado["jogos_selecionados"]
        lam = estado["lam"]
        phi2_base = calcular_coocorrencia_global_bruta(lam, 200)["phi2"]
        self.assertEqual(phi2_base, estado["current_phi2"])

        verificados = 0
        for u_idx in range(2, 20):
            tu = jogos[u_idx]
            tw = jogos[u_idx + 1]
            tu_set = set(tu)
            tw_set = set(tw)
            u_diff = [z for z in tu if z not in tw_set]
            w_diff = [z for z in tw if z not in tu_set]
            par_xy = next(
                (
                    (x, y)
                    for x in u_diff
                    for y in w_diff
                    if BLOCK_OF[x] == BLOCK_OF[y]
                ),
                None,
            )
            if par_xy is None:
                continue
            x, y = par_xy
            delta_local = calcular_delta_phi2_exato_candidato(tu, tw, x, y, lam)

            lam_mut = [list(row) for row in lam]
            for z in u_diff:
                if z != x:
                    lam_mut[x][z] -= 1
                    lam_mut[z][x] -= 1
                    lam_mut[y][z] += 1
                    lam_mut[z][y] += 1
            for z in w_diff:
                if z != y:
                    lam_mut[y][z] -= 1
                    lam_mut[z][y] -= 1
                    lam_mut[x][z] += 1
                    lam_mut[z][x] += 1
            phi2_bruto_pos = calcular_coocorrencia_global_bruta(lam_mut, 200)["phi2"]
            self.assertEqual(delta_local, phi2_bruto_pos - phi2_base)
            verificados += 1
            if verificados >= 5:
                break
        self.assertGreaterEqual(verificados, 5)

        desvios_equilibrados = (0, 0, 0)
        desvios_compensados = (76, -38, -38)
        self.assertEqual(sum(desvios_equilibrados), sum(desvios_compensados))
        q_plus_eq = sum(d * d for d in desvios_equilibrados if d > 0)
        q_plus_comp = sum(d * d for d in desvios_compensados if d > 0)
        self.assertEqual(q_plus_eq, 0)
        self.assertEqual(q_plus_comp, 5776)
        self.assertGreater(q_plus_comp, q_plus_eq)

    def test_06_bloqueio_global_2swap_e_classificacao_kmax(self):
        _, estado = inicializar_carteira_fase12(seed=330001, J=200)
        snap = capturar_snapshot_estado(estado)

        st_prot, reg_prot = avaliar_e_aplicar_swap_fase3(
            estado, u_idx=0, v_idx=0, w_idx=2, r_block=0, proposta_idx=0
        )
        self.assertEqual(st_prot, "rej_r1_r10")
        self.assertIsNone(reg_prot)
        self.assertEqual(comparar_estado_snapshot(estado, snap), [])

        estado["teto_fase3"] = 0
        qualquer_par = False
        for w_idx in range(3, 50):
            st_kmax, _ = avaliar_e_aplicar_swap_fase3(
                estado,
                u_idx=2,
                v_idx=2,
                w_idx=w_idx,
                r_block=w_idx % 5,
                proposta_idx=w_idx,
                auditar_100pct_swaps=True,
            )
            if st_kmax == "rej_kmax":
                qualquer_par = True
                break
        self.assertTrue(qualquer_par)
        self.assertEqual(comparar_estado_snapshot(estado, snap), [])
        estado["teto_fase3"] = snap_teto = estado["k_star"]
        self.assertLessEqual(snap_teto, 35)

        c34 = classificar_homologacao_kmax(34)
        c35 = classificar_homologacao_kmax(35)
        c36 = classificar_homologacao_kmax(36)
        c37 = classificar_homologacao_kmax(37)
        self.assertEqual(c34["status"], "APROVADO")
        self.assertEqual(c35["status"], "APROVADO")
        self.assertTrue(c35["meta_kmax_35_atingida"])
        self.assertEqual(c36["status"], "INCONCLUSIVO / RESSALVA DE CONTINGÊNCIA")
        self.assertFalse(c36["meta_kmax_35_atingida"])
        self.assertTrue(c36["ressalva_contingencia"])
        self.assertEqual(c37["status"], "REPROVADO")
        self.assertFalse(c37["meta_kmax_35_atingida"])

    def test_07_matematica_2499_celulas_racionais_e_baseline_ordem4(self):
        celulas_verificadas = 0
        for k in range(51):
            soma_win_k = 0
            for t1 in FAIXAS_PREMIACAO:
                for t2 in FAIXAS_PREMIACAO:
                    q = k
                    min_x = max(0, t1 - (50 - k), t2 - (50 - k), t1 + t2 - 20)
                    max_x = min(k, t1, t2, 20, q - 20 + t1 + t2)
                    indep = 0
                    if min_x <= max_x:
                        for c in range(min_x, max_x + 1):
                            indep += (
                                math.comb(k, c)
                                * math.comb(50 - k, t1 - c)
                                * math.comb(50 - k, t2 - c)
                                * math.comb(q, 20 - t1 - t2 + c)
                            )
                    self.assertEqual(TABELA_OVERLAP_BIVARIADA[k][(t1, t2)], indep)
                    self.assertEqual(calcular_n2_celula(k, t1, t2), indep)
                    if t1 == t2:
                        self.assertEqual(TABELA_OVERLAP_FAIXAS[t1][k], indep)
                    soma_win_k += indep
                    celulas_verificadas += 1
            self.assertEqual(TABELA_OVERLAP_PREMIADOS[k], soma_win_k)
        self.assertEqual(celulas_verificadas, 2499)

        self.assertEqual(TABELA_OVERLAP_PREMIADOS[0], 94258424487920)
        self.assertEqual(TABELA_OVERLAP_PREMIADOS[11], 77285790113844)
        self.assertEqual(TABELA_OVERLAP_PREMIADOS[25], 57160170570478645)
        self.assertEqual(TABELA_OVERLAP_PREMIADOS[35], 545367310991925478)
        self.assertEqual(TABELA_OVERLAP_PREMIADOS[50], 6119632172014985995)

        omega_blocos = (math.comb(20, 10)) ** 5
        self.assertEqual(omega_blocos, 215274582490246006282187776)

        poly = [1]
        p_bloco = [math.comb(10, j) ** 2 for j in range(11)]
        for _ in range(5):
            prox = [0] * (len(poly) + len(p_bloco) - 1)
            for i, vi in enumerate(poly):
                for j, vj in enumerate(p_bloco):
                    prox[i + j] += vi * vj
            poly = prox
        self.assertEqual(sum(poly), omega_blocos)
        ew_exact = Fraction(
            sum(poly[k] * TABELA_OVERLAP_PREMIADOS[k] for k in range(51)),
            omega_blocos,
        )
        self.assertEqual(
            ew_exact,
            Fraction(14726857078461010696251650276404305, 209142348143684384),
        )

        self.assertEqual(sum(HISTOGRAMA_BASELINE_ORDEM4.values()), 49995000)
        r_win_base = sum(
            fk * TABELA_OVERLAP_PREMIADOS[k] for k, fk in HISTOGRAMA_BASELINE_ORDEM4.items()
        )
        p25_base = sum(
            ((k - 25) ** 2) * fk
            for k, fk in HISTOGRAMA_BASELINE_ORDEM4.items()
            if k > 25
        )
        self.assertEqual(r_win_base, int(BASELINE_ORDEM4_10000_REFERENCIA["R_win"]))
        self.assertEqual(p25_base, BASELINE_ORDEM4_10000_REFERENCIA["P_gt_25"])

    def test_08_reprodutibilidade_subprocesso_std_vs_opt_j200(self):
        script = (
            "import json, sys; sys.path.insert(0, r'" + DIR_RAIZ + "'); "
            "from lotomania_carteira_10000 import gerar_carteira_10000_otimizada; "
            "r = gerar_carteira_10000_otimizada(seed=330001, J=200, max_tentativas_f3=30000, incluir_jogos_no_retorno=False); "
            "print(json.dumps({'v1': r['auditoria_restricoes']['hash_carteira_sha256_v1'], "
            "'v2': r['auditoria_restricoes']['hash_carteira_sha256_v2_canonico'], "
            "'canon': r['auditoria_restricoes']['sha256_estado_canonico'], "
            "'mat': r['auditoria_restricoes']['sha256_matriz_incidencia_100'], "
            "'swaps': r['swaps_aceitos'], 'phi2': r['pos_fase3']['phi2'], "
            "'q': r['pos_fase3']['q_global_plus'], 'd': r['pos_fase3']['d_max'], "
            "'p25': r['pos_fase3']['P_gt_25'], 'rwin': r['pos_fase3']['R_win']}, sort_keys=True))"
        )
        p_std = subprocess.run(
            [sys.executable, "-c", script], capture_output=True, text=True, check=True
        )
        p_opt = subprocess.run(
            [sys.executable, "-O", "-c", script],
            capture_output=True,
            text=True,
            check=True,
        )
        self.assertEqual(p_std.stdout.strip(), p_opt.stdout.strip())

    def test_09_rejeicao_estrita_entradas_invalidas(self):
        j_invalidos_tipo = [200.0, True, False, "200", None, Decimal("200")]
        for bad_j in j_invalidos_tipo:
            with self.assertRaises(TypeError):
                validar_entrada_carteira(J=bad_j)
            with self.assertRaises(TypeError):
                gerar_carteira_10000_otimizada(J=bad_j, max_tentativas_f3=10)

        j_invalidos_valor = [0, -1, -200, 1, 3, 199, 10001, 10002]
        for bad_j in j_invalidos_valor:
            with self.assertRaises(ValueError):
                validar_entrada_carteira(J=bad_j)
            with self.assertRaises(ValueError):
                gerar_carteira_10000_otimizada(J=bad_j, max_tentativas_f3=10)

        with self.assertRaises(TypeError):
            validar_entrada_carteira(J=200, seed="330001")
        with self.assertRaises(TypeError):
            validar_entrada_carteira(J=200, max_tentativas_f3=10.5)
        with self.assertRaises(ValueError):
            validar_entrada_carteira(J=200, max_tentativas_f3=-1)
        with self.assertRaises(ValueError):
            validar_entrada_carteira(J=200, tau_primario=24)

    def test_10_integracao_paridade_integral_j10000_task938(self):
        with tempfile.TemporaryDirectory(prefix="ltm_t10_") as tmp:
            dossie = executar_benchmark_ordem6_passo1(
                dir_saida=tmp,
                seed=330001,
                J=10000,
                max_tentativas=1080000,
                passo_checkpoint=60000,
            )
            self.assertEqual(
                dossie["auditoria_restricoes"]["sha256_carteira"],
                "589947b2385147f6acce8a36b78c5d3ed295cfbf1a588a710f9559b597fccb6d",
            )
            self.assertEqual(
                dossie["auditoria_restricoes"]["sha256_estado_canonico"],
                "747e25a84986e676a11c3706bf6d178c1c5a78e99dce76d9bfc0c08e74c3950e",
            )
            self.assertEqual(
                dossie["auditoria_restricoes"]["sha256_matriz_incidencia_100"],
                "75ff1e068d8c81c90b26e2f8e1a8fa151d57a967815fc0fb43f13e911ee4b127",
            )
            self.assertEqual(dossie["swaps_aceitos"], 10261)
            self.assertEqual(dossie["recalculos_dmax_queda"], 61)
            pos = dossie["pos_fase3"]
            self.assertEqual(pos["phi2"], 232285184)
            self.assertEqual(pos["q_global_plus"], 61041440)
            self.assertEqual(pos["d_max"], 1140)
            self.assertEqual(pos["cnt_dmax"], 4)
            self.assertEqual(pos["P_gt_25"], 161144723)
            self.assertEqual(pos["R_win"], "3509128436603630355147408")
            self.assertEqual(pos["k_max"], 35)
            self.assertEqual(pos["k_eq_35"], 2802)
            self.assertEqual(pos["k_ge_36"], 0)
            self.assertEqual(dossie["homologacao_kmax"]["status"], "APROVADO")
            self.assertTrue(dossie["aprovacao_auditoria_independente"]["todas_travas_aprovadas"])

            cp_map = {cp["tentativas"]: cp for cp in dossie["checkpoints_60k"]}
            self.assertEqual(cp_map[360000]["swaps_acumulados"], 9397)
            self.assertEqual(cp_map[360000]["phi2"], 439747552)
            self.assertEqual(cp_map[360000]["q_global_plus"], 102555312)
            self.assertEqual(cp_map[360000]["d_max"], 1520)
            self.assertEqual(cp_map[720000]["swaps_acumulados"], 9991)
            self.assertEqual(cp_map[720000]["phi2"], 284638848)
            self.assertEqual(cp_map[720000]["q_global_plus"], 72586832)
            self.assertEqual(cp_map[720000]["d_max"], 1292)


if __name__ == "__main__":
    unittest.main(verbosity=2)
