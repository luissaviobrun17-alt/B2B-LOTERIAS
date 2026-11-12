# -*- coding: utf-8 -*-
"""
Testes Unitarios Rigorosos para a Evolucao Matematica do MOTOR LOTOMANIA (v3.0).
Valida:
1. Analise das 4 janelas temporais (3, 5, 10, 15).
2. Investigacao de pares e trios com Bonferroni.
3. Calculo e ranking do IFM (10 dimensoes).
4. Geracao nos 6 modos estrategicos com auditoria de 10 regras.
5. Backtesting cronologico walk-forward com teste t pareado e Monte Carlo.
6. Relatorio de auditoria e integridade.
"""

import unittest
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motor_lotomania import MotorLotomaniaB2B


class TestMotorLotomaniaEvolution(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cache_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "lotomania.json")
        historico = []
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                sorted_keys = sorted(data.keys(), key=lambda x: int(x))
                for key in sorted_keys:
                    historico.append([int(x) for x in data[key]])
        if len(historico) < 50:
            import random
            rnd_hist = random.Random(20261111)
            historico = [sorted(rnd_hist.sample(range(1, 101), 20)) for _ in range(50)]
        cls.historico = historico
        cls.motor = MotorLotomaniaB2B(historico=cls.historico, estrategia="matematico_puro")

    def test_analise_quatro_janelas(self):
        """Verifica a analise individual e integrada das 4 janelas temporais."""
        res = self.motor.analisar_quatro_janelas()
        self.assertTrue(res["sucesso"])
        self.assertIn("janela_3", res["janelas"])
        self.assertIn("janela_5", res["janelas"])
        self.assertIn("janela_10", res["janelas"])
        self.assertIn("janela_15", res["janelas"])

        # Verifica tamanho das janelas
        self.assertEqual(res["janelas"]["janela_3"]["tamanho_janela"], 3)
        self.assertEqual(res["janelas"]["janela_5"]["tamanho_janela"], 5)
        self.assertEqual(res["janelas"]["janela_10"]["tamanho_janela"], 10)
        self.assertEqual(res["janelas"]["janela_15"]["tamanho_janela"], 15)

        # Verifica analise integrada
        integrada = res["analise_integrada"]
        self.assertIn("quentes_persistentes", integrada)
        self.assertIn("frias_persistentes", integrada)
        self.assertIn("top_10_estaveis", integrada)
        self.assertEqual(integrada["ponderacao_recomendada"]["tipo"], "neutra")

    def test_analise_pares_e_bonferroni(self):
        """Verifica a analise de 4.950 pares e aplicacao do limiar de Bonferroni."""
        res = self.motor.analisar_pares(limite_top=10)
        self.assertTrue(res["sucesso"])
        self.assertEqual(res["total_pares_analisados"], 4950)
        self.assertGreater(res["esperado_teorico"], 0)
        self.assertEqual(res["z_critico_bonferroni"], 4.41)
        # Nao deve haver pares com Z >= 4.41
        self.assertEqual(res["total_significativos_bonferroni"], 0)
        self.assertEqual(len(res["top_pares"]), 10)

    def test_analise_trios(self):
        """Verifica a analise de trios e controle de falsos padroes."""
        res = self.motor.analisar_trios(limite_top=5)
        self.assertTrue(res["sucesso"])
        self.assertEqual(res["total_trios_analisados"], 161700)
        self.assertGreater(res["esperado_teorico"], 0)
        self.assertEqual(res["z_critico_bonferroni"], 5.12)
        self.assertEqual(res["total_significativos_bonferroni"], 0)
        self.assertEqual(len(res["top_trios"]), 5)

    def test_calculo_ifm(self):
        """Verifica o calculo do Indice de Forca Matematica em 10 dimensoes."""
        res = self.motor.calcular_ifm()
        self.assertTrue(res["sucesso"])
        self.assertEqual(res["total_dezenas"], 100)
        self.assertEqual(len(res["ranking"]), 100)
        # Verifica componentes do primeiro colocado
        top1 = res["ranking"][0]
        self.assertIn("ifm_score", top1)
        self.assertIn("componentes", top1)
        self.assertEqual(len(top1["componentes"]), 10)
        self.assertEqual(top1["posicao_ranking"], 1)

    def test_geracao_seis_modos(self):
        """Testa geracao de bilhetes nos 6 modos estrategicos com auditoria 10 pontos."""
        modos = [
            "matematico_puro",
            "estatistico_multijanela",
            "associacao_pares_trios",
            "otimizacao_combinatoria",
            "hibrido",
            "experimental"
        ]
        for modo in modos:
            res = self.motor.gerar_carteira_modo(modo=modo, quantidade_jogos=3, seed=123)
            self.assertTrue(res["sucesso"], f"Falha no modo: {modo}")
            self.assertEqual(len(res["jogos"]), 3)
            self.assertEqual(res["modo_selecionado"], modo)
            self.assertEqual(res["auditoria_carteira"]["auditoria_10_testes"]["status_geral"], "LIBERADO")

    def test_backtesting_multiplo_cronologico(self):
        """Testa o backtesting walk-forward em 10 concursos com comparacao aleatoria."""
        res = self.motor.executar_backtesting_multiplo(
            concursos_teste=10,
            quantidade_jogos_por_concurso=5,
            modo="matematico_puro",
            seed=42
        )
        self.assertTrue(res["sucesso"])
        self.assertEqual(res["concursos_avaliados"], 10)
        self.assertEqual(res["total_jogos_testados"], 50)
        self.assertIn("media_acertos_motor", res)
        self.assertIn("media_acertos_aleatorio", res)
        self.assertIn("p_valor", res)
        self.assertIn("ic_95_acertos_motor", res)
        self.assertIn("premios_motor", res)
        self.assertIn("conclusao_honestidade_cientifica", res)

    def test_relatorio_auditoria_completo(self):
        """Verifica geracao do relatorio integrado de auditoria."""
        res = self.motor.gerar_relatorio_auditoria_completo()
        self.assertTrue(res["sucesso"])
        self.assertIn("janelas_resumo", res)
        self.assertIn("pares_resumo", res)
        self.assertIn("trios_resumo", res)
        self.assertIn("ifm_resumo", res)
        self.assertIn("diretriz_honestidade_cientifica", res)


if __name__ == "__main__":
    unittest.main()
