import unittest
import json
import os
from motor_lotomania import MotorLotomaniaB2B


class TestMotorLotomaniaB2B(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Carrega histórico se existir
        cache_path = os.path.join("data", "lotomania.json")
        historico = []
        if os.path.exists(cache_path):
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                sorted_keys = sorted(data.keys(), key=lambda x: int(x))
                for key in sorted_keys:
                    historico.append([int(x) for x in data[key]])
        cls.historico = historico
        cls.motor = MotorLotomaniaB2B(historico=cls.historico, estrategia="equilibrada")

    def test_divisao_5_conjuntos(self):
        """Verifica a definição exata dos 5 conjuntos de 20 números."""
        self.assertEqual(len(self.motor.CONJUNTO_1), 20)
        self.assertEqual(len(self.motor.CONJUNTO_2), 20)
        self.assertEqual(len(self.motor.CONJUNTO_3), 20)
        self.assertEqual(len(self.motor.CONJUNTO_4), 20)
        self.assertEqual(len(self.motor.CONJUNTO_5), 20)

        self.assertEqual(self.motor.CONJUNTO_1[0], 1)
        self.assertEqual(self.motor.CONJUNTO_1[-1], 20)
        self.assertEqual(self.motor.CONJUNTO_2[0], 21)
        self.assertEqual(self.motor.CONJUNTO_2[-1], 40)
        self.assertEqual(self.motor.CONJUNTO_3[0], 41)
        self.assertEqual(self.motor.CONJUNTO_3[-1], 60)
        self.assertEqual(self.motor.CONJUNTO_4[0], 61)
        self.assertEqual(self.motor.CONJUNTO_4[-1], 80)
        self.assertEqual(self.motor.CONJUNTO_5[0], 81)
        self.assertEqual(self.motor.CONJUNTO_5[-1], 100)

    def test_geracao_10_jogos_validacao_10_pontos(self):
        """Gera 10 jogos e valida todas as 10 regras estritas."""
        res = self.motor.gerar_carteira(10)
        self.assertEqual(len(res["jogos"]), 10)
        self.assertEqual(res["auditoria_carteira"]["auditoria_10_testes"]["status_geral"], "LIBERADO")

        for r in res["relatorios_jogos"]:
            self.assertTrue(r["valido"], f"Jogo {r['numero_jogo']} invalido")
            self.assertEqual(r["c1_count"], 10, "C1 diferente de 10")
            self.assertEqual(r["c2_count"], 10, "C2 diferente de 10")
            self.assertEqual(r["c3_count"], 10, "C3 diferente de 10")
            self.assertEqual(r["c4_count"], 10, "C4 diferente de 10")
            self.assertEqual(r["c5_count"], 10, "C5 diferente de 10")
            self.assertTrue(r["maior_sequencia"] <= 4, f"Sequencia > 4: {r['maior_sequencia']}")
            self.assertEqual(len(r["jogo"]), 50)
            self.assertEqual(r["status"], "VALIDADO")

    def test_geracao_100_jogos_diversidade_e_cobertura(self):
        """Gera 100 jogos e verifica cobertura dos 100 números e diversidade."""
        res = self.motor.gerar_carteira(100)
        self.assertEqual(len(res["jogos"]), 100)
        
        aud = res["auditoria_carteira"]
        self.assertEqual(aud["auditoria_10_testes"]["status_geral"], "LIBERADO")
        self.assertEqual(aud["cobertura_100_pct"], 100.0, "Cobertura deve atingir 100% com 100 jogos")
        self.assertGreater(aud["indice_diversidade_pct"], 50.0)

    def test_filtro_consecutividade_fronteira_conjuntos(self):
        """Testa que 5 números consecutivos na fronteira entre conjuntos são rejeitados."""
        # 17, 18, 19, 20 (C1) e 21 (C2) -> 5 consecutivos
        c1 = [1, 3, 5, 7, 9, 11, 17, 18, 19, 20] # 10 números
        c2 = [21, 23, 25, 27, 29, 31, 33, 35, 37, 39] # 10 números
        c3 = [41, 43, 45, 47, 49, 51, 53, 55, 57, 59] # 10 números
        c4 = [61, 63, 65, 67, 69, 71, 73, 75, 77, 79] # 10 números
        c5 = [81, 83, 85, 87, 89, 91, 93, 95, 97, 99] # 10 números
        jogo_invalido = c1 + c2 + c3 + c4 + c5
        
        valido, rel = self.motor.validar_jogo(jogo_invalido)
        self.assertFalse(valido)
        self.assertFalse(rel["teste_9_max_consec_4"])
        self.assertEqual(rel["maior_sequencia"], 5)
        self.assertEqual(rel["status"], "REJEITADO")

    def test_backtesting(self):
        """Testa o backtesting histórico."""
        if len(self.historico) > 50:
            res_backtest = self.motor.executar_backtesting(concurso_alvo_idx=len(self.historico)-1, quantidade_jogos=10)
            self.assertIn("acertos_resumo", res_backtest)
            self.assertIn("media_acertos", res_backtest)
            self.assertEqual(res_backtest["quantidade_jogos_testados"], 10)


if __name__ == "__main__":
    unittest.main()
