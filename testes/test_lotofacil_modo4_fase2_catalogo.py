# -*- coding: utf-8 -*-
"""
SUÍTE DE TESTES AUTOMATIZADOS: FASE 2 / ETAPAS 2.1 E 2.2
==================================================
Validação integral da integridade, conformidade combinatória,
unicidade, coberturas t=1..4 e tripla validação matemática
do catálogo oficial canônico de 1.000 jogos da Lotofácil MODO 4.
"""

from __future__ import annotations

import hashlib
import json
import os
import unittest
from pathlib import Path
from typing import List, Set, Tuple

from lotofacil_modo4.etapa1_regras_oficiais import validar_aposta_lotofacil
from lotofacil_modo4.etapa2_funcao_objetivo import avaliar_carteira_etapa2
from lotofacil_modo4.etapa2_referencia_independente import avaliar_carteira_referencia_independente
from lotofacil_modo4.etapa4_arquitetura_adaptativa import MotorIncrementalOtimizadoEtapa4

CAMINHO_CATALOGO_1000 = Path(__file__).resolve().parent.parent / "catalogo_lotofacil_10000" / "lotofacil_carteira_1000.json"
CAMINHO_CATALOGO_2000 = Path(__file__).resolve().parent.parent / "catalogo_lotofacil_10000" / "lotofacil_carteira_2000.json"


class TestLotofacilModo4Fase2Catalogo1000(unittest.TestCase):
    """Bateria de testes de homologação do catálogo canônico J=1.000."""

    @classmethod
    def setUpClass(cls):
        if not CAMINHO_CATALOGO_1000.is_file():
            raise unittest.SkipTest(
                f"Catálogo oficial de 1.000 jogos ainda não gerado em: {CAMINHO_CATALOGO_1000}"
            )
        with open(CAMINHO_CATALOGO_1000, "r", encoding="utf-8") as f:
            cls.catalogo = json.load(f)
        cls.jogos = [tuple(sorted(jg)) for jg in cls.catalogo["jogos"]]

    def test_01_arquivo_e_esquema_basico(self):
        """Verifica existência e metadados estruturais do catálogo."""
        cat = self.catalogo
        self.assertEqual(cat["identificador"], "LOTOFACIL_MODO4_J1000_CANONICA")
        self.assertEqual(cat["versao_formato"], "2.0")
        self.assertEqual(cat["modalidade"], "LOTOFACIL")
        self.assertEqual(cat["modo"], 4)
        self.assertEqual(cat["quantidade_jogos"], 1000)
        self.assertEqual(cat["tamanho_aposta"], 15)
        self.assertEqual(cat["pool"], list(range(1, 26)))
        self.assertEqual(cat["fixas"], [])
        self.assertEqual(cat["bloqueadas"], [])
        self.assertEqual(cat["algoritmo_utilizado"], "algoritmo_guloso")
        self.assertIn("semente", cat)
        self.assertIn("b_cand_utilizado", cat)
        self.assertIn("orcamento_max_avaliacoes", cat)
        self.assertIn("sha256_jogos_canonicos", cat)
        self.assertIn("sha256_documento_catalogo", cat)

    def test_02_integridade_hash_jogos_canonicos(self):
        """Verifica se o hash dos jogos bate com o cálculo SHA-256 canônico."""
        serializacao = json.dumps(self.catalogo["jogos"], separators=(",", ":"))
        hash_calc = hashlib.sha256(serializacao.encode("utf-8")).hexdigest()
        self.assertEqual(
            hash_calc,
            self.catalogo["sha256_jogos_canonicos"],
            "Hash SHA-256 dos jogos canônicos diverge do registrado no catálogo.",
        )

    def test_03_unicidade_estrita_e_regras_caixa(self):
        """Valida que todos os 1.000 bilhetes são válidos e estritamente únicos."""
        self.assertEqual(len(self.jogos), 1000, "Carteira deve conter exatamente 1.000 jogos.")
        jogos_unicos = set(self.jogos)
        self.assertEqual(len(jogos_unicos), 1000, "Não são permitidas apostas duplicadas.")
        self.assertEqual(self.catalogo["metricas_qualidade"]["duplicatas"], 0)
        self.assertEqual(self.catalogo["metricas_qualidade"]["unicidade_pct"], 100.0)

        for jg in self.jogos:
            validado = validar_aposta_lotofacil(jg)
            self.assertEqual(len(validado), 15)
            self.assertTrue(all(1 <= d <= 25 for d in validado))

    def test_04_coberturas_combinatorias_t1_t2_t3_t4(self):
        """Garante coberturas mínimas homologatórias (100% em t=1..3 e >=99.5% em t=4)."""
        t1: Set[int] = set()
        t2: Set[Tuple[int, int]] = set()
        t3: Set[Tuple[int, int, int]] = set()
        t4: Set[Tuple[int, int, int, int]] = set()

        for jg in self.jogos:
            t1.update(jg)
            n = len(jg)
            for i in range(n):
                for j in range(i + 1, n):
                    t2.add((jg[i], jg[j]))
                    for k in range(j + 1, n):
                        t3.add((jg[i], jg[j], jg[k]))
                        for m in range(k + 1, n):
                            t4.add((jg[i], jg[j], jg[k], jg[m]))

        self.assertEqual(len(t1), 25, "Cobertura t=1 deve ser de 100% (25 dezenas).")
        self.assertEqual(len(t2), 300, "Cobertura t=2 deve ser de 100% (300 pares).")
        self.assertEqual(len(t3), 2300, "Cobertura t=3 deve ser de 100% (2.300 trincas).")
        self.assertGreaterEqual(
            len(t4),
            12587,
            f"Cobertura t=4 ({len(t4)}/12650) deve ser >= 99,5% (mínimo 12.587 quadras).",
        )

        cob_reg = self.catalogo["metricas_qualidade"]
        self.assertEqual(cob_reg["cobertura_t1_pct"], 100.0)
        self.assertEqual(cob_reg["cobertura_t2_pct"], 100.0)
        self.assertEqual(cob_reg["cobertura_t3_pct"], 100.0)
        self.assertGreaterEqual(cob_reg["cobertura_t4_pct"], 99.5)

    def test_05_cota_minima_variancia(self):
        """Valida que SS_min = 0 exato para pool 25 com 1.000 jogos de 15 dezenas."""
        metricas = self.catalogo["metricas_qualidade"]
        self.assertEqual(metricas["ss_minimo"], 0.0)
        self.assertGreaterEqual(metricas["ss_observado"], 0.0)

    def test_06_escore_minimo_funcao_objetivo(self):
        """Valida que F(C) >= 0.965 conforme protocolo homologatório."""
        f_val = self.catalogo["metricas_qualidade"]["funcao_objetivo_F"]
        self.assertGreaterEqual(f_val, 0.965, f"Escore F(C)={f_val} inferior a 0.965.")

    def test_07_tripla_validacao_divergencia_estrita(self):
        """Valida equivalência matemática estrita (|E4 - E2| <= 1e-12 e |E4 - Ref| <= 1e-12)."""
        pesos = self.catalogo["pesos"]
        
        # Validador 1: Motor Incremental Etapa 4
        motor = MotorIncrementalOtimizadoEtapa4(self.jogos, tuple(range(1, 26)), (), pesos)
        f_e4 = motor.score_atual()

        # Validador 2: Etapa 2 oficial
        ev_e2 = avaliar_carteira_etapa2(self.jogos)
        f_e2 = float(ev_e2["funcao_objetivo_F"])

        # Validador 3: Referência Independente
        ev_ref = avaliar_carteira_referencia_independente(self.jogos)
        f_ref = float(ev_ref["funcao_objetivo_F"])

        div_e4_e2 = abs(f_e4 - f_e2)
        div_e4_ref = abs(f_e4 - f_ref)

        self.assertLessEqual(
            div_e4_e2,
            1e-12,
            f"Divergência |E4 - E2| ({div_e4_e2:.2e}) excede tolerância de 1e-12.",
        )
        self.assertLessEqual(
            div_e4_ref,
            1e-12,
            f"Divergência |E4 - Ref| ({div_e4_ref:.2e}) excede tolerância de 1e-12.",
        )

        # Checa se o catálogo reflete os valores reais
        tv = self.catalogo["tripla_validacao"]
        self.assertAlmostEqual(tv["f_etapa4"], f_e4, places=12)
        self.assertAlmostEqual(tv["f_etapa2"], f_e2, places=12)
        self.assertAlmostEqual(tv["f_referencia_independente"], f_ref, places=12)
        self.assertTrue(tv["aprovado_tolerancia_1e12"])

    def test_08_integracao_leitor_oficial_e_governanca(self):
        """Valida integração do pacote oficial de catálogo e leitor com governança OFF_STANDBY."""
        from catalogo_lotofacil_10000.leitor import (
            obter_carteira_oficial_1000,
            obter_status_governanca,
            verificar_integridade_catalogo_1000,
        )

        integro, relatorio = verificar_integridade_catalogo_1000()
        self.assertTrue(integro, f"Auditoria do leitor falhou: {relatorio.get('motivo')}")
        self.assertTrue(relatorio["hash_fisico_valido"])
        self.assertTrue(relatorio["hash_jogos_valido"])
        self.assertTrue(relatorio["hash_documento_valido"])

        jogos_leitor = obter_carteira_oficial_1000(auto_recuperar=False)
        self.assertEqual(len(jogos_leitor), 1000)

        gov = obter_status_governanca()
        self.assertEqual(gov["estado_operacional"], "OFF_STANDBY")
        self.assertFalse(gov["em_producao"])
        self.assertTrue(gov["integridade_confirmada"])


class TestLotofacilModo4Fase2Catalogo2000(unittest.TestCase):
    """Bateria de testes de homologação do catálogo canônico J=2.000."""

    @classmethod
    def setUpClass(cls):
        if not CAMINHO_CATALOGO_2000.is_file():
            raise unittest.SkipTest(
                f"Catálogo oficial de 2.000 jogos ainda não gerado em: {CAMINHO_CATALOGO_2000}"
            )
        with open(CAMINHO_CATALOGO_2000, "r", encoding="utf-8") as f:
            cls.catalogo = json.load(f)
        cls.jogos = [tuple(sorted(jg)) for jg in cls.catalogo["jogos"]]

    def test_01_arquivo_e_esquema_basico(self):
        """Verifica existência e metadados estruturais do catálogo J=2.000."""
        cat = self.catalogo
        self.assertEqual(cat["identificador"], "LOTOFACIL_MODO4_J2000_CANONICA")
        self.assertEqual(cat["versao_formato"], "2.0")
        self.assertEqual(cat["modalidade"], "LOTOFACIL")
        self.assertEqual(cat["modo"], 4)
        self.assertEqual(cat["quantidade_jogos"], 2000)
        self.assertEqual(cat["tamanho_aposta"], 15)
        self.assertEqual(cat["pool"], list(range(1, 26)))
        self.assertEqual(cat["fixas"], [])
        self.assertEqual(cat["bloqueadas"], [])
        self.assertEqual(cat["algoritmo_utilizado"], "algoritmo_guloso")
        self.assertEqual(cat["b_cand_utilizado"], 32)
        self.assertEqual(cat["orcamento_max_avaliacoes"], 64000)
        self.assertIn("semente", cat)
        self.assertIn("sha256_jogos_canonicos", cat)
        self.assertIn("sha256_documento_catalogo", cat)

    def test_02_integridade_hash_jogos_canonicos(self):
        """Verifica se o hash dos jogos bate com o cálculo SHA-256 canônico."""
        serializacao = json.dumps(self.catalogo["jogos"], separators=(",", ":"))
        hash_calc = hashlib.sha256(serializacao.encode("utf-8")).hexdigest()
        self.assertEqual(
            hash_calc,
            self.catalogo["sha256_jogos_canonicos"],
            "Hash SHA-256 dos jogos canônicos diverge do registrado no catálogo.",
        )

    def test_03_unicidade_estrita_e_regras_caixa(self):
        """Valida que todos os 2.000 bilhetes são válidos e estritamente únicos."""
        self.assertEqual(len(self.jogos), 2000, "Carteira deve conter exatamente 2.000 jogos.")
        jogos_unicos = set(self.jogos)
        self.assertEqual(len(jogos_unicos), 2000, "Não são permitidas apostas duplicadas.")
        self.assertEqual(self.catalogo["metricas_qualidade"]["duplicatas"], 0)
        self.assertEqual(self.catalogo["metricas_qualidade"]["unicidade_pct"], 100.0)

        for jg in self.jogos:
            validado = validar_aposta_lotofacil(jg)
            self.assertEqual(len(validado), 15)
            self.assertTrue(all(1 <= d <= 25 for d in validado))

    def test_04_coberturas_combinatorias_t1_t2_t3_t4(self):
        """Garante coberturas mínimas homologatórias (100% em t=1..4)."""
        t1: Set[int] = set()
        t2: Set[Tuple[int, int]] = set()
        t3: Set[Tuple[int, int, int]] = set()
        t4: Set[Tuple[int, int, int, int]] = set()

        for jg in self.jogos:
            t1.update(jg)
            n = len(jg)
            for i in range(n):
                for j in range(i + 1, n):
                    t2.add((jg[i], jg[j]))
                    for k in range(j + 1, n):
                        t3.add((jg[i], jg[j], jg[k]))
                        for m in range(k + 1, n):
                            t4.add((jg[i], jg[j], jg[k], jg[m]))

        self.assertEqual(len(t1), 25, "Cobertura t=1 deve ser de 100% (25 dezenas).")
        self.assertEqual(len(t2), 300, "Cobertura t=2 deve ser de 100% (300 pares).")
        self.assertEqual(len(t3), 2300, "Cobertura t=3 deve ser de 100% (2.300 trincas).")
        self.assertEqual(len(t4), 12650, "Cobertura t=4 deve ser de 100% (12.650 quadras).")

        cob_reg = self.catalogo["metricas_qualidade"]
        self.assertEqual(cob_reg["cobertura_t1_pct"], 100.0)
        self.assertEqual(cob_reg["cobertura_t2_pct"], 100.0)
        self.assertEqual(cob_reg["cobertura_t3_pct"], 100.0)
        self.assertEqual(cob_reg["cobertura_t4_pct"], 100.0)

    def test_05_cota_minima_variancia(self):
        """Valida que SS_min = 0 exato para pool 25 com 2.000 jogos de 15 dezenas."""
        metricas = self.catalogo["metricas_qualidade"]
        self.assertEqual(metricas["ss_minimo"], 0.0)
        self.assertGreaterEqual(metricas["ss_observado"], 0.0)

    def test_06_escore_minimo_funcao_objetivo(self):
        """Valida que F(C) >= 0.965 conforme protocolo homologatório."""
        f_val = self.catalogo["metricas_qualidade"]["funcao_objetivo_F"]
        self.assertGreaterEqual(f_val, 0.965, f"Escore F(C)={f_val} inferior a 0.965.")

    def test_07_tripla_validacao_divergencia_estrita(self):
        """Valida equivalência matemática estrita (|E4 - E2| <= 1e-12 e |E4 - Ref| <= 1e-12)."""
        pesos = self.catalogo["pesos"]

        motor = MotorIncrementalOtimizadoEtapa4(self.jogos, tuple(range(1, 26)), (), pesos)
        f_e4 = motor.score_atual()

        ev_e2 = avaliar_carteira_etapa2(self.jogos)
        f_e2 = float(ev_e2["funcao_objetivo_F"])

        ev_ref = avaliar_carteira_referencia_independente(self.jogos)
        f_ref = float(ev_ref["funcao_objetivo_F"])

        div_e4_e2 = abs(f_e4 - f_e2)
        div_e4_ref = abs(f_e4 - f_ref)

        self.assertLessEqual(
            div_e4_e2,
            1e-12,
            f"Divergência |E4 - E2| ({div_e4_e2:.2e}) excede tolerância de 1e-12.",
        )
        self.assertLessEqual(
            div_e4_ref,
            1e-12,
            f"Divergência |E4 - Ref| ({div_e4_ref:.2e}) excede tolerância de 1e-12.",
        )

        tv = self.catalogo["tripla_validacao"]
        self.assertAlmostEqual(tv["f_etapa4"], f_e4, places=12)
        self.assertAlmostEqual(tv["f_etapa2"], f_e2, places=12)
        self.assertAlmostEqual(tv["f_referencia_independente"], f_ref, places=12)
        self.assertTrue(tv["aprovado_tolerancia_1e12"])


if __name__ == "__main__":
    unittest.main()
