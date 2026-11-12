# -*- coding: utf-8 -*-
"""
TESTES AUTOMATIZADOS DE VALIDACAO DA FORMULA RWIN(K)
====================================================
1. Confronto exaustivo com enumeracao de todos os sorteios em universos reduzidos (toy models).
2. Verificacao estrita dos casos-limite em Lotomania (k=0, k=25, k=50).
3. Verificacao da conservacao do espaco amostral total sum N(k; t1, t2) = C(100, 20) para todos os k in [0..50].
4. Confronto integral dos 51 valores de Rwin(k) com formulacao analitica direta.
5. Auditoria por SEGUNDO METODO INDEPENDENTE (Programacao Dinamica / Funcoes Geratrizes) para todos os 51 valores.
6. Verificacao da simetria exata N(k; t1, t2) = N(k; t2, t1) para todos os k in [0..50].
"""

import unittest
import itertools
import math
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from motor_lotomania import MotorLotomaniaB2B

class TestValidacaoRwin(unittest.TestCase):

    def setUp(self):
        self.motor = MotorLotomaniaB2B()

    def test_toy_universe_exhaustive_enumeration(self):
        """
        Valida que a formula da convolucao hipergeometrica bivariada com as cotas exatas
        do hipercubo combinatorio (c_min, c_max) reproduz rigorosamente a contagem por forca
        bruta exaustiva de TODOS os sorteios possiveis sem excecoes ou aproximacoes.
        """
        def verificar_modelo(U, m, s, k):
            q = U - 2 * m + k
            g1 = set(range(m))
            g2 = set(range(m - k, 2 * m - k))
            self.assertEqual(len(g1.intersection(g2)), k)

            all_draws = list(itertools.combinations(range(U), s))
            contagem_real = {}
            for d in all_draws:
                d_set = set(d)
                h1 = len(g1.intersection(d_set))
                h2 = len(g2.intersection(d_set))
                contagem_real[(h1, h2)] = contagem_real.get((h1, h2), 0) + 1

            for t1 in range(s + 1):
                for t2 in range(s + 1):
                    esperado = contagem_real.get((t1, t2), 0)
                    c_min = max(0, t1 - (m - k), t2 - (m - k), t1 + t2 - s)
                    c_max = min(k, t1, t2, s, q - s + t1 + t2)
                    calculado = 0
                    if c_min <= c_max:
                        for c in range(c_min, c_max + 1):
                            calculado += (
                                math.comb(k, c) *
                                math.comb(m - k, t1 - c) *
                                math.comb(m - k, t2 - c) *
                                math.comb(q, s - t1 - t2 + c)
                            )
                    self.assertEqual(
                        esperado, calculado,
                        f"Divergencia em U={U}, m={m}, s={s}, k={k}, t1={t1}, t2={t2}: esperado={esperado}, calculado={calculado}"
                    )

        # 1. Caso especifico do parecer do auditor: U=10, m=4, s=3, k=2
        verificar_modelo(U=10, m=4, s=3, k=2)

        # 2. Varredura completa para U=10, m=5, s=4 para todos os k in [0..5]
        for k_val in range(6):
            verificar_modelo(U=10, m=5, s=4, k=k_val)

    def test_caso_limite_k0_jogos_espelho(self):
        """
        No caso k=0 (jogos complementares/espelho), |G1 cap G2| = 0.
        Para qualquer sorteio de 20 dezenas, h1 + h2 = 20.
        Logo, se h1 in {15, 16, 17, 18, 19, 20}, entao h2 = 20 - h1 in {5, 4, 3, 2, 1, 0}.
        O unico par de acertos onde AMBOS estao em T_win = {0, 15, 16, 17, 18, 19, 20} eh:
        (20, 0) e (0, 20).
        Portanto, R_win(0) deve ser EXATAMENTE 2 * C(50, 20) = 94.258.424.487.920.
        """
        c50_20 = math.comb(50, 20)
        esperado_k0 = 2 * c50_20
        self.assertEqual(esperado_k0, 94258424487920)
        self.assertEqual(self.motor.TABELA_OVERLAP_PREMIADOS[0], esperado_k0)

    def test_caso_limite_k50_jogos_identicos(self):
        """
        No caso k=50 (jogos identicos), |G1 cap G2| = 50.
        Para qualquer sorteio, h1 = h2.
        Logo, a sobreposicao eh o suporte inteiro de sorteios premiados de um bilhete individual:
        R_win(50) = sum_{t in T_win} C(50, t) * C(50, 20 - t) = 6.119.632.172.014.985.995.
        """
        faixas = [0, 15, 16, 17, 18, 19, 20]
        esperado_k50 = sum(math.comb(50, t) * math.comb(50, 20 - t) for t in faixas)
        self.assertEqual(esperado_k50, 6119632172014985995)
        self.assertEqual(self.motor.TABELA_OVERLAP_PREMIADOS[50], esperado_k50)

    def test_caso_k25_conservacao_espaco_amostral(self):
        """
        Para k=25 (intersecao media), a soma de N(25; t1, t2) sobre todos os t1, t2 in [0..20]
        deve recompor exatamente o espaco amostral total da Lotomania: C(100, 20).
        """
        total_lotomania = math.comb(100, 20)
        self.assertEqual(total_lotomania, 535983370403809682970)

        soma_convolucao = 0
        def c(n, k): return math.comb(n, k) if 0 <= k <= n else 0

        k = 25
        for t1 in range(21):
            for t2 in range(21):
                min_x = max(0, t1 - 25, t2 - 25)
                max_x = min(25, t1, t2)
                for x11 in range(min_x, max_x + 1):
                    x10 = t1 - x11
                    x01 = t2 - x11
                    x00 = 20 - t1 - t2 + x11
                    if 0 <= x10 <= 25 and 0 <= x01 <= 25 and 0 <= x00 <= 25:
                        soma_convolucao += c(25, x11) * c(25, x10) * c(25, x01) * c(25, x00)

        self.assertEqual(soma_convolucao, total_lotomania)
        self.assertEqual(self.motor.TABELA_OVERLAP_PREMIADOS[25], 57160170570478645)

    def test_confronto_integral_51_valores_tabela_rwin(self):
        """
        Auditoria matematica integral: confronta a totalidade dos 51 valores
        da tabela TABELA_OVERLAP_PREMIADOS (k = 0 ate k = 50) com uma implementacao
        independente de referencia direta da convolucao hipergeometrica bivariada.
        """
        faixas = [0, 15, 16, 17, 18, 19, 20]
        for k in range(51):
            tot_ref = 0
            q = k  # 100 - 2*50 + k = k
            for t1 in faixas:
                for t2 in faixas:
                    c_min = max(0, t1 - (50 - k), t2 - (50 - k), t1 + t2 - 20)
                    c_max = min(k, t1, t2, 20, q - 20 + t1 + t2)
                    if c_min <= c_max:
                        for c in range(c_min, c_max + 1):
                            tot_ref += (
                                math.comb(k, c) *
                                math.comb(50 - k, t1 - c) *
                                math.comb(50 - k, t2 - c) *
                                math.comb(k, 20 - t1 - t2 + c)
                            )
            val_motor = self.motor.TABELA_OVERLAP_PREMIADOS[k]
            self.assertEqual(
                val_motor, tot_ref,
                f"Discrepancia em k={k}: motor={val_motor}, referencia={tot_ref}"
            )

    def test_auditoria_segundo_metodo_convolucao_dinamica_51_valores(self):
        """
        Auditoria matematica independente por SEGUNDO METODO (Programacao Dinamica /
        Convolucao Polinomial Bivariada de Funcoes Geratrizes):
        Calcula R_win(k) para todos os 51 valores de k in [0..50] por composicao sequencial
        das particoes disjuntas (A -> B -> C -> D), sem recorrer a formula fechada de c_min/c_max.
        Valida que ambos os metodos independentes produzem valores inteiros 100% identicos.
        """
        faixas = {0, 15, 16, 17, 18, 19, 20}
        for k in range(51):
            # Grupo A: tamanho k (fornece acertos simultaneos a G1 e G2)
            dp = {}
            for xa in range(min(k, 20) + 1):
                dp[(xa, xa, xa)] = math.comb(k, xa)
            
            # Grupo B: tamanho 50-k (fornece acertos exclusivos a G1)
            dp2 = {}
            for (s, t1, t2), count in dp.items():
                for xb in range(min(50 - k, 20 - s) + 1):
                    ns, nt1, nt2 = s + xb, t1 + xb, t2
                    ways = count * math.comb(50 - k, xb)
                    dp2[(ns, nt1, nt2)] = dp2.get((ns, nt1, nt2), 0) + ways
                    
            # Grupo C: tamanho 50-k (fornece acertos exclusivos a G2)
            dp3 = {}
            for (s, t1, t2), count in dp2.items():
                for xc in range(min(50 - k, 20 - s) + 1):
                    ns, nt1, nt2 = s + xc, t1, t2 + xc
                    ways = count * math.comb(50 - k, xc)
                    dp3[(ns, nt1, nt2)] = dp3.get((ns, nt1, nt2), 0) + ways
                    
            # Grupo D: tamanho k (fornece acertos externos a ambos)
            tot_rwin_dp = 0
            for (s, t1, t2), count in dp3.items():
                xd = 20 - s
                if 0 <= xd <= k:
                    ways = count * math.comb(k, xd)
                    if t1 in faixas and t2 in faixas:
                        tot_rwin_dp += ways
                        
            val_motor = self.motor.TABELA_OVERLAP_PREMIADOS[k]
            self.assertEqual(
                val_motor, tot_rwin_dp,
                f"Discrepancia no segundo metodo DP para k={k}: motor={val_motor}, dp={tot_rwin_dp}"
            )

    def test_auditoria_conservacao_integral_espaco_amostral_todos_51_k(self):
        """
        Verifica a conservacao estrita do espaco amostral total da Lotomania:
        Para CADA UM dos 51 valores de k in [0..50], a soma integral de N(k; t1, t2)
        sobre todos os pares (t1, t2) in [0..20]^2 deve ser EXATAMENTE C(100, 20) = 535.983.370.403.809.682.970.
        """
        c100_20 = math.comb(100, 20)
        self.assertEqual(c100_20, 535983370403809682970)
        
        for k in range(51):
            soma_k = 0
            q = k
            for t1 in range(21):
                for t2 in range(21):
                    c_min = max(0, t1 - (50 - k), t2 - (50 - k), t1 + t2 - 20)
                    c_max = min(k, t1, t2, 20, q - 20 + t1 + t2)
                    if c_min <= c_max:
                        for c in range(c_min, c_max + 1):
                            soma_k += (
                                math.comb(k, c) *
                                math.comb(50 - k, t1 - c) *
                                math.comb(50 - k, t2 - c) *
                                math.comb(k, 20 - t1 - t2 + c)
                            )
            self.assertEqual(
                soma_k, c100_20,
                f"Falha na conservacao do espaco amostral para k={k}: soma={soma_k}, esperado={c100_20}"
            )

    def test_auditoria_simetria_rigorosa_todos_51_k(self):
        """
        Verifica a simetria exata N(k; t1, t2) == N(k; t2, t1) para todo k in [0..50]
        e para todos os pares (t1, t2) in [0..20]^2.
        """
        for k in range(51):
            q = k
            for t1 in range(21):
                for t2 in range(t1 + 1, 21):
                    # N(k; t1, t2)
                    c_min1 = max(0, t1 - (50 - k), t2 - (50 - k), t1 + t2 - 20)
                    c_max1 = min(k, t1, t2, 20, q - 20 + t1 + t2)
                    n1 = 0
                    if c_min1 <= c_max1:
                        for c in range(c_min1, c_max1 + 1):
                            n1 += (
                                math.comb(k, c) *
                                math.comb(50 - k, t1 - c) *
                                math.comb(50 - k, t2 - c) *
                                math.comb(k, 20 - t1 - t2 + c)
                            )
                    # N(k; t2, t1)
                    c_min2 = max(0, t2 - (50 - k), t1 - (50 - k), t2 + t1 - 20)
                    c_max2 = min(k, t2, t1, 20, q - 20 + t2 + t1)
                    n2 = 0
                    if c_min2 <= c_max2:
                        for c in range(c_min2, c_max2 + 1):
                            n2 += (
                                math.comb(k, c) *
                                math.comb(50 - k, t2 - c) *
                                math.comb(50 - k, t1 - c) *
                                math.comb(k, 20 - t2 - t1 + c)
                            )
                    self.assertEqual(
                        n1, n2,
                        f"Assimetria detectada para k={k}, par ({t1}, {t2}): n1={n1}, n2={n2}"
                    )

if __name__ == "__main__":
    unittest.main()
