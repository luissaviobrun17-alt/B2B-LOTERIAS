"""
===============================================================================
TESTES AUTOMATIZADOS — NOVO MOTOR MEGA-SENA (B2B LOTERIAS)
===============================================================================
Validação estrita de todos os critérios de aceitação:
- Geração de 1, 5, 10, 50 jogos
- Pool completo (01-60) e Pool personalizado
- Modelos hipergeométricos 3/3, 2/4, 4/2, 1/5, 5/1
- Modo Equilibrado e Modo Sniper
- Janela de 3 concursos e 100 concursos
- Eliminação total de duplicidades
- Limite de sequências (máximo 3 números consecutivos, proibido >= 4)
- Validação estrita dos 60 números
- Auditoria integral dos 10 Checks
- Backtesting walk-forward
- Teste de robustez de indicadores
===============================================================================
"""

import unittest
from motor_megasena import MotorMegaSenaB2B


class TestMotorMegaSenaB2B(unittest.TestCase):

    def setUp(self):
        self.motor_padrao = MotorMegaSenaB2B(limite_historico=30, estrategia="equilibrada")

    def test_01_geracao_volumes_distintos(self):
        """Testa geração de 1, 5, 10 e 50 jogos com respeito à quantidade e 10 checks."""
        for qtd in [1, 5, 10, 50]:
            res = self.motor_padrao.gerar_carteira(qtd)
            self.assertTrue(res["sucesso"])
            self.assertEqual(res["total_solicitado"], qtd)
            self.assertEqual(res["total_gerado"], qtd)
            self.assertEqual(len(res["jogos"]), qtd)
            self.assertTrue(res["checks_auditoria"]["aprovacao_integral_10_de_10"])

    def test_02_limite_de_consecutivos(self):
        """Regra mandatória: Não pode haver mais de 3 números consecutivos (<=3 permitido, >=4 proibido)."""
        res = self.motor_padrao.gerar_carteira(50)
        for j in res["jogos"]:
            nums = sorted(j["numeros"])
            max_c = MotorMegaSenaB2B.contar_max_consecutivos(nums)
            self.assertLessEqual(max_c, 3, f"Jogo {nums} excedeu o limite com {max_c} consecutivos!")

    def test_03_ausencia_duplicidades_na_carteira(self):
        """Nenhum jogo pode ser repetido na carteira."""
        res = self.motor_padrao.gerar_carteira(50)
        jogos_tuplas = [tuple(j["numeros"]) for j in res["jogos"]]
        self.assertEqual(len(jogos_tuplas), len(set(jogos_tuplas)), "Há jogos duplicados na carteira!")

    def test_04_range_valido_01_a_60(self):
        """Todos os números devem estar estritamente entre 01 e 60."""
        res = self.motor_padrao.gerar_carteira(30)
        for j in res["jogos"]:
            self.assertEqual(len(j["numeros"]), 6)
            for n in j["numeros"]:
                self.assertTrue(1 <= n <= 60, f"Número {n} fora do range 01-60!")

    def test_05_pool_personalizado(self):
        """Testa respeito estrito ao pool personalizado do apostador."""
        custom_pool = [3, 7, 9, 12, 16, 18, 21, 24, 27, 30, 31, 34, 37, 40, 43, 45, 49, 52, 55, 60]
        motor_custom = MotorMegaSenaB2B(limite_historico=30, pool=custom_pool)
        res = motor_custom.gerar_carteira(15)
        self.assertTrue(res["sucesso"])
        self.assertEqual(len(res["jogos"]), 15)
        for j in res["jogos"]:
            for n in j["numeros"]:
                self.assertIn(n, custom_pool, f"Número {n} fora do pool personalizado!")

    def test_06_modo_sniper(self):
        """Testa o Modo Sniper com seleção de alta coesão e pontuação."""
        motor_sniper = MotorMegaSenaB2B(limite_historico=50, estrategia="sniper")
        res = motor_sniper.gerar_carteira(10)
        self.assertTrue(res["sucesso"])
        self.assertEqual(len(res["jogos"]), 10)
        self.assertTrue(res["checks_auditoria"]["aprovacao_integral_10_de_10"])
        # No sniper, os scores devem ser elevados
        for j in res["jogos"]:
            self.assertGreaterEqual(j["score_b2b"], 700)

    def test_07_janelas_extremas_3_e_100(self):
        """Testa histórico mínimo de 3 concursos e máximo de 100 concursos."""
        motor_3 = MotorMegaSenaB2B(limite_historico=3)
        res_3 = motor_3.gerar_carteira(5)
        self.assertTrue(res_3["sucesso"])
        self.assertEqual(res_3["relatorio_tecnico"]["concursos_utilizados"], 3)
        self.assertTrue(res_3["checks_auditoria"]["aprovacao_integral_10_de_10"])

        motor_100 = MotorMegaSenaB2B(limite_historico=100)
        res_100 = motor_100.gerar_carteira(20)
        self.assertTrue(res_100["sucesso"])
        self.assertEqual(res_100["relatorio_tecnico"]["concursos_utilizados"], 100)
        self.assertTrue(res_100["checks_auditoria"]["aprovacao_integral_10_de_10"])

    def test_08_modelos_especificos(self):
        """Testa geração forçada por modelos hipergeométricos 3/3, 2/4, 4/2, 1/5, 5/1."""
        for modelo in ["3/3", "2/4", "4/2", "1/5", "5/1"]:
            motor_mod = MotorMegaSenaB2B(limite_historico=30, modelo_preferencial=modelo)
            res = motor_mod.gerar_carteira(5)
            self.assertTrue(res["sucesso"])
            for j in res["jogos"]:
                self.assertEqual(j["modelo_ab"], modelo, f"Jogo gerado com modelo {j['modelo_ab']} diferente do solicitado {modelo}!")

    def test_09_backtesting_walk_forward(self):
        """Testa o backtesting walk-forward livre de contaminação futura."""
        bt = self.motor_padrao.executar_backtesting(concursos_teste=5, quantidade_jogos=5)
        self.assertTrue(bt["sucesso"])
        self.assertEqual(bt["concursos_testados"], 5)
        self.assertIn("totais_por_faixa", bt)
        self.assertIn("media_acertos_por_jogo", bt)

    def test_10_robustez_e_transparencia(self):
        """Testa relatório de robustez e fatores de transparência de cada jogo."""
        res = self.motor_padrao.gerar_carteira(5)
        for j in res["jogos"]:
            f = j["fatores_transparencia"]
            self.assertIn("frequencia_historica", f)
            self.assertIn("frequencia_recente", f)
            self.assertIn("pares_e_trios", f)
            self.assertIn("centroide_simetrico", f)
            self.assertIn("modelo_ab", f)
            self.assertIn("score_final", f)

        rob = self.motor_padrao.testar_robustez_indicadores()
        self.assertIn("veredito", rob)


if __name__ == "__main__":
    unittest.main()
