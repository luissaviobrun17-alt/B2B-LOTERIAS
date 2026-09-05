import unittest
from motor_quina import MotorQuinaB2B


class TestMotorQuinaB2B(unittest.TestCase):

    def setUp(self):
        self.motor_padrao = MotorQuinaB2B(limite_historico=30, estrategia="equilibrada")

    def test_01_geracao_volumes_distintos(self):
        """Testa geração de 1, 5, 10 e 50 jogos com respeito estrito à quantidade e 10 checks."""
        for qtd in [1, 5, 10, 50]:
            res = self.motor_padrao.gerar_carteira(qtd)
            self.assertTrue(res["sucesso"])
            self.assertEqual(res["total_solicitado"], qtd)
            self.assertEqual(res["total_gerado"], qtd)
            self.assertEqual(len(res["jogos"]), qtd)
            self.assertTrue(res["checks_auditoria"]["aprovacao_integral_10_de_10"])

    def test_02_limite_rigido_dois_consecutivos(self):
        """Regra mandatória (Item 28): NÃO pode haver mais de 2 números consecutivos (<= 2 permitido, >= 3 proibido)."""
        res = self.motor_padrao.gerar_carteira(50)
        for j in res["jogos"]:
            nums = sorted(j["numeros"])
            max_c = MotorQuinaB2B.contar_max_consecutivos(nums)
            self.assertLessEqual(max_c, 2, f"Jogo {nums} violou o limite com {max_c} consecutivos!")

    def test_03_ausencia_duplicidades(self):
        """Nenhum jogo pode ser repetido na carteira e nenhuma dezena repetida no jogo."""
        res = self.motor_padrao.gerar_carteira(50)
        jogos_tuplas = [tuple(j["numeros"]) for j in res["jogos"]]
        self.assertEqual(len(jogos_tuplas), len(set(jogos_tuplas)), "Há jogos duplicados na carteira!")
        for j in res["jogos"]:
            self.assertEqual(len(j["numeros"]), len(set(j["numeros"])), "Há números duplicados no jogo!")

    def test_04_range_valido_01_a_80(self):
        """Todos os números devem estar estritamente entre 01 e 80 (5 números por jogo)."""
        res = self.motor_padrao.gerar_carteira(30)
        for j in res["jogos"]:
            self.assertEqual(len(j["numeros"]), 5)
            for n in j["numeros"]:
                self.assertTrue(1 <= n <= 80, f"Número {n} fora do range 01-80!")

    def test_05_pool_personalizado(self):
        """Testa respeito estrito ao pool personalizado do apostador."""
        custom_pool = [5, 10, 15, 20, 25, 30, 35, 40, 45, 50, 55, 60, 65, 70, 75, 80]
        motor_custom = MotorQuinaB2B(limite_historico=30, pool=custom_pool)
        res = motor_custom.gerar_carteira(10)
        self.assertTrue(res["sucesso"])
        self.assertEqual(len(res["jogos"]), 10)
        for j in res["jogos"]:
            for n in j["numeros"]:
                self.assertIn(n, custom_pool, f"Número {n} fora do pool personalizado!")

    def test_06_modo_sniper(self):
        """Testa o Modo Sniper com seleção de alta coesão e pontuação IGA elevada."""
        motor_sniper = MotorQuinaB2B(limite_historico=30, estrategia="sniper")
        res = motor_sniper.gerar_carteira(10)
        self.assertTrue(res["sucesso"])
        self.assertEqual(len(res["jogos"]), 10)
        self.assertTrue(res["checks_auditoria"]["aprovacao_integral_10_de_10"])
        for j in res["jogos"]:
            self.assertGreaterEqual(j["iga"], 50.0)

    def test_07_janelas_extremas_3_e_100(self):
        """Testa histórico mínimo de 3 concursos e máximo de 100 concursos (Item 9)."""
        motor_3 = MotorQuinaB2B(limite_historico=3)
        res_3 = motor_3.gerar_carteira(5)
        self.assertTrue(res_3["sucesso"])
        self.assertEqual(res_3["relatorio_tecnico"]["concursos_utilizados"], 3)
        self.assertTrue(res_3["checks_auditoria"]["aprovacao_integral_10_de_10"])

        motor_100 = MotorQuinaB2B(limite_historico=100)
        res_100 = motor_100.gerar_carteira(20)
        self.assertTrue(res_100["sucesso"])
        self.assertEqual(res_100["relatorio_tecnico"]["concursos_utilizados"], 100)
        self.assertTrue(res_100["checks_auditoria"]["aprovacao_integral_10_de_10"])

    def test_08_modelos_especificos(self):
        """Testa geração por modelos hipergeométricos 3/2, 2/3, 4/1, 1/4."""
        for modelo in ["3/2", "2/3", "4/1", "1/4"]:
            motor_mod = MotorQuinaB2B(limite_historico=30, modelo_preferencial=modelo)
            res = motor_mod.gerar_carteira(5)
            self.assertTrue(res["sucesso"])
            for j in res["jogos"]:
                nA = sum(1 for n in j["numeros"] if n <= 40)
                nB = 5 - nA
                self.assertEqual(f"{nA}/{nB}", modelo, f"Modelo gerado {nA}/{nB} diferente do solicitado {modelo}")

    def test_09_iga_e_explicacao_presentes(self):
        """Garante que cada jogo possui IGA (0-100) e explicação técnica clara (Item 4, 38, 39)."""
        res = self.motor_padrao.gerar_carteira(5)
        for j in res["jogos"]:
            self.assertIn("iga", j)
            self.assertIn("iga_fmt", j)
            self.assertIn("explicacao_resumida", j)
            self.assertTrue(isinstance(j["iga"], (int, float)))
            self.assertGreater(len(j["explicacao_resumida"]), 10)

    def test_10_centroide_simetrico_202_5(self):
        """Testa o centróide simétrico na esperança de 202.5 e intervalo [120, 285] (Item 19)."""
        res = self.motor_padrao.gerar_carteira(20)
        for j in res["jogos"]:
            soma = sum(j["numeros"])
            self.assertGreaterEqual(soma, 120, f"Soma {soma} abaixo do mínimo aceitável 120!")
            self.assertLessEqual(soma, 285, f"Soma {soma} acima do máximo aceitável 285!")

    def test_11_backtesting_walk_forward(self):
        """Testa simulação walk-forward sem lookahead bias (Item 23, 24)."""
        bk = self.motor_padrao.executar_backtesting(concursos_teste=5, quantidade_jogos=10)
        self.assertTrue(bk["sucesso"])
        self.assertEqual(bk["concursos_testados"], 5)
        self.assertIn("totais_por_faixa", bk)
        self.assertIn("quina_5", bk["totais_por_faixa"])
        self.assertIn("quadra_4", bk["totais_por_faixa"])
        self.assertIn("terno_3", bk["totais_por_faixa"])
        self.assertIn("duque_2", bk["totais_por_faixa"])

    def test_12_robustez_indicadores(self):
        """Testa módulo de robustez de indicadores (Item 9, 36)."""
        rob = self.motor_padrao.testar_robustez_indicadores()
        self.assertTrue(rob["sucesso"])
        self.assertIn("janelas_comparadas", rob)
        self.assertIn("taxa_estabilidade", rob)


if __name__ == "__main__":
    unittest.main()
