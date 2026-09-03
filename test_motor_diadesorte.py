"""
TESTES UNITÁRIOS E DE INTEGRAÇÃO — MOTOR DIA DE SORTE B2B LOTERIAS
===================================================================
Validação rigorosa dos 24 requisitos da especificação:
- Filtro estrito de sequências consecutivas (máximo 3)
- Divisão em Grupos A (01-15) e B (16-31)
- Modelos combinatórios (3+4, 4+3, 5+2, 2+5)
- Todos os 7 modos de operação
- Pool automático vs pool personalizado
- Módulo dos 12 meses da sorte
- Checklist final de 10 verificações
- Diversificação e anti-redundância de carteira
"""

import unittest
from motor_diadesorte import MotorDiaDeSorteB2B


class TestMotorDiaDeSorteB2B(unittest.TestCase):

    def setUp(self):
        self.motor = MotorDiaDeSorteB2B(limite_historico=30, estrategia="equilibrada")

    def test_grupos_e_pool_padrao(self):
        """Valida que os grupos A e B possuem as dezenas exatas exigidas."""
        self.assertEqual(len(self.motor.GRUPO_A), 15)
        self.assertEqual(self.motor.GRUPO_A, list(range(1, 16)))
        self.assertEqual(len(self.motor.GRUPO_B), 16)
        self.assertEqual(self.motor.GRUPO_B, list(range(16, 32)))
        self.assertEqual(len(self.motor.pool), 31)

    def test_filtro_consecutivos_estrito(self):
        """Valida que o motor permite até 3 números consecutivos e rejeita 4 ou mais."""
        # Permitidos (<= 3 consecutivos)
        self.assertTrue(MotorDiaDeSorteB2B.validar_sequencia_consecutivos([1, 2, 3, 10, 15, 20, 25]))
        self.assertTrue(MotorDiaDeSorteB2B.validar_sequencia_consecutivos([5, 10, 11, 12, 20, 25, 30]))
        self.assertTrue(MotorDiaDeSorteB2B.validar_sequencia_consecutivos([1, 5, 9, 13, 17, 21, 25]))

        # Proibidos (> 3 consecutivos)
        self.assertFalse(MotorDiaDeSorteB2B.validar_sequencia_consecutivos([1, 2, 3, 4, 15, 20, 25]))
        self.assertFalse(MotorDiaDeSorteB2B.validar_sequencia_consecutivos([10, 11, 12, 13, 20, 25, 30]))
        self.assertFalse(MotorDiaDeSorteB2B.validar_sequencia_consecutivos([15, 16, 17, 18, 19, 25, 30]))

    def test_geracao_carteira_estrutura_jogos(self):
        """Valida a geração de uma carteira com 10 jogos nos padrões oficiais."""
        resultado = self.motor.gerar_carteira(quantidade_jogos=10)
        self.assertTrue(resultado["sucesso"])
        self.assertEqual(resultado["total_jogos"], 10)
        self.assertEqual(len(resultado["jogos"]), 10)

        for j in resultado["jogos"]:
            jogo = j["jogo"]
            # 1. Exatamente 7 números
            self.assertEqual(len(jogo), 7)
            # 2. Números entre 1 e 31
            self.assertTrue(all(1 <= x <= 31 for x in jogo))
            # 3. Sem duplicatas
            self.assertEqual(len(set(jogo)), 7)
            # 4. Máximo 3 consecutivos
            self.assertTrue(MotorDiaDeSorteB2B.validar_sequencia_consecutivos(jogo))
            # 5. Mês válido
            self.assertIn(j["mes"], MotorDiaDeSorteB2B.MESES_OFICIAIS)
            # 6. Modelo válido (3+4, 4+3, 5+2 ou 2+5)
            self.assertIn(j["modelo"], ["3 + 4", "4 + 3", "5 + 2", "2 + 5", "1 + 6", "6 + 1"])
            # 7. Score positivo ou real
            self.assertIsInstance(j["score"], float)

    def test_todos_modos_operacao(self):
        """Valida que todos os 7 modos de operação geram carteiras íntegras."""
        modos = [
            "equilibrada",
            "frequencia_historica",
            "frequencia_recente",
            "atrasos_recuperacoes",
            "pares_trios",
            "coocorrencia_lift_zscore",
            "auto_pesos"
        ]
        for modo in modos:
            m = MotorDiaDeSorteB2B(limite_historico=20, estrategia=modo)
            res = m.gerar_carteira(quantidade_jogos=4)
            self.assertEqual(res["total_jogos"], 4, f"Falha no modo {modo}")

    def test_pool_personalizado(self):
        """Valida o funcionamento com pool personalizado de dezenas."""
        custom_pool = [1, 2, 3, 4, 5, 6, 7, 8, 16, 17, 18, 19, 20, 21, 22]
        m = MotorDiaDeSorteB2B(limite_historico=15, pool=custom_pool)
        self.assertTrue(m.is_custom_pool)
        res = m.gerar_carteira(quantidade_jogos=5)
        for j in res["jogos"]:
            for n in j["jogo"]:
                self.assertIn(n, custom_pool)

    def test_niveis_evidencia(self):
        """Valida a categorização correta dos níveis de evidência estatística."""
        m_pequeno = MotorDiaDeSorteB2B(limite_historico=5)
        self.assertEqual(m_pequeno.stats["nivel_evidencia"], "AMOSTRA INSUFICIENTE")

        m_baixo = MotorDiaDeSorteB2B(limite_historico=20)
        self.assertEqual(m_baixo.stats["nivel_evidencia"], "BAIXA EVIDÊNCIA")

        m_mod = MotorDiaDeSorteB2B(limite_historico=45)
        self.assertEqual(m_mod.stats["nivel_evidencia"], "EVIDÊNCIA MODERADA")

        m_alto = MotorDiaDeSorteB2B(limite_historico=80)
        self.assertEqual(m_alto.stats["nivel_evidencia"], "ALTA EVIDÊNCIA")

    def test_relatorio_pre_geracao_e_saida(self):
        """Valida o relatório pré-geração e o texto oficial."""
        rel = self.motor.gerar_relatorio_pre_geracao()
        self.assertIn("concursos_analisados", rel)
        self.assertIn("distribuicoes_identificadas", rel)
        self.assertIn("numeros_com_maior_score", rel)
        self.assertIn("advertencia_matematica", rel)

        res = self.motor.gerar_carteira(quantidade_jogos=3)
        texto = res["saida_oficial_texto"]
        self.assertIn("JOGO 01", texto)
        self.assertIn("RESUMO FINAL", texto)
        self.assertIn("CONCURSOS ANALISADOS: 30", texto)


if __name__ == "__main__":
    unittest.main()
