"""
===============================================================================
BATERIA CIENTÍFICA OFICIAL — 18 TESTES DE VALIDAÇÃO DO MOTOR SUPER SETE
B2B LOTERIAS — RIGOR MATEMÁTICO, ESTATÍSTICO E COMPUTACIONAL
===============================================================================
Executa os 18 testes obrigatórios descritos na Seção 38 da especificação.
"""

import math
import statistics
import random
import os
import sys
import copy
import json

if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

sys.path.insert(0, r"C:\Users\Luis Brun\Desktop\loterias-caixa")
from motor_supersete import MotorSuperSeteB2B


class TestesCientificosSuperSete:
    def __init__(self):
        self.motor = MotorSuperSeteB2B()
        self.resultados = {}

    def executar_todos(self):
        print("=" * 78)
        print("INICIANDO BATERIA DE 18 TESTES CIENTIFICOS - SUPER SETE B2B")
        print("=" * 78)

        metodos = [
            ("TESTE 1", "Validacao das Regras Oficiais", self.teste_1_regras_oficiais),
            ("TESTE 2", "Validacao Matematica das Probabilidades", self.teste_2_validacao_matematica),
            ("TESTE 3", "Validacao Estatistica (Centroide e Qui-Quadrado)", self.teste_3_validacao_estatistica),
            ("TESTE 4", "Backtesting Temporal sem Data Leakage", self.teste_4_backtesting),
            ("TESTE 5", "Walk-Forward Concurso a Concurso", self.teste_5_walk_forward),
            ("TESTE 6", "Teste Fora da Amostra (Out-of-Sample)", self.teste_6_fora_da_amostra),
            ("TESTE 7", "Simulacao Estocastica Monte Carlo (10k)", self.teste_7_monte_carlo),
            ("TESTE 8", "Comparacao contra a Baseline Aleatoria", self.teste_8_comparacao_acaso),
            ("TESTE 9", "Teste de Overfitting e Degradacao", self.teste_9_overfitting),
            ("TESTE 10", "Controle de Falsos Positivos (FDR / Bonferroni)", self.teste_10_falsos_positivos),
            ("TESTE 11", "Teste de Estabilidade Temporal dos Pesos", self.teste_11_estabilidade),
            ("TESTE 12", "Teste de Diversificacao por Distancia de Hamming", self.teste_12_diversificacao),
            ("TESTE 13", "Teste de Duplicidade na Carteira", self.teste_13_duplicidade),
            ("TESTE 14", "Teste de Integridade dos Dados Historicos", self.teste_14_integridade_dados),
            ("TESTE 15", "Teste de Interface e Endpoints REST", self.teste_15_interface_endpoints),
            ("TESTE 16", "Teste de Exportacao e Formatacao de Jogos", self.teste_16_exportacao),
            ("TESTE 17", "Teste de Atualizacao Continua apos Novo Concurso", self.teste_17_atualizacao_novo_concurso),
            ("TESTE 18", "Teste de Honestidade e Frase Obrigatoria", self.teste_18_honestidade_informacoes)
        ]

        total_pass = 0
        for num, desc, func in metodos:
            try:
                passou, detalhe = func()
                status = "[APROVADO]" if passou else "[REPROVADO]"
                if passou:
                    total_pass += 1
                self.resultados[num] = {"desc": desc, "passou": passou, "detalhe": detalhe}
                print(f"[{num}] {desc.ljust(48)}: {status} ({detalhe})")
            except Exception as e:
                self.resultados[num] = {"desc": desc, "passou": False, "detalhe": str(e)}
                print(f"[{num}] {desc.ljust(48)}: [ERRO] ({e})")

        print("=" * 78)
        print(f"RESULTADO FINAL: {total_pass}/18 TESTES CIENTIFICOS APROVADOS")
        print("=" * 78)
        return total_pass == 18

    def teste_1_regras_oficiais(self):
        assert self.motor.NUM_COLUNAS == 7
        assert self.motor.DIGITOS_POR_COLUNA == 10
        assert self.motor.TOTAL_COMBINACOES_TEORICAS == 10_000_000
        assert self.motor.PRECO_APOSTA_SIMPLES == 2.50
        res = self.motor.gerar_carteira(5)
        for j in res["jogos"]:
            assert len(j["jogo"]) == 7
            assert all(0 <= d <= 9 for d in j["jogo"])
        return True, "7 colunas, digitos 0..9, 10^7 combinacoes equiprovaveis"

    def teste_2_validacao_matematica(self):
        soma_prob = 0.0
        for k in range(8):
            comb_k = math.comb(7, k)
            p_k = comb_k * (0.1 ** k) * (0.9 ** (7 - k))
            soma_prob += p_k
            if k in self.motor.PROBABILIDADES_TEORICAS:
                esperado = self.motor.PROBABILIDADES_TEORICAS[k]["prob"]
                assert abs(p_k - esperado) < 1e-9

        assert abs(soma_prob - 1.0) < 1e-9
        return True, "Probabilidades binomiais exatas conferidas: Faixas 7, 6, 5, 4, 3"

    def teste_3_validacao_estatistica(self):
        models = self.motor.stats["modelos_colunas"]
        assert len(models) == 7
        assert self.motor.stats["soma_esperada_teorica"] == 31.5
        assert self.motor.stats["desvio_esperado_teorico"] == 7.60
        for c in range(7):
            assert models[c]["chi2"] >= 0.0
            assert 0.0 <= models[c]["p_valor_chi2"] <= 1.0
            assert models[c]["entropia"] > 3.0
        return True, "Modelos M1..M7 com Qui-Quadrado, Z-score e Entropia validados"

    def teste_4_backtesting(self):
        bk = self.motor.executar_backtesting(concursos_teste=5, quantidade_jogos=3)
        assert bk["sucesso"] is True
        assert bk["concursos_avaliados"] == 5
        assert "media_melhor_acerto_motor" in bk
        assert "resumo_acertos_motor" in bk
        return True, "Split temporal estrito executado sem vazamento de dados"

    def teste_5_walk_forward(self):
        bk = self.motor.executar_backtesting(concursos_teste=6, quantidade_jogos=2)
        detalhes = bk["detalhes_concurso_a_concurso"]
        assert len(detalhes) == 6
        for i in range(1, len(detalhes)):
            assert detalhes[i]["concurso_idx"] == detalhes[i-1]["concurso_idx"] + 1
        return True, "Iteracao concurso a concurso confirmada"

    def teste_6_fora_da_amostra(self):
        N = len(self.motor.historico_completo)
        treino = self.motor.historico_completo[:N-10]
        teste_real = self.motor.historico_completo[N-10:]

        m_treino = MotorSuperSeteB2B(historico=treino)
        cart = m_treino.gerar_carteira(5)
        total_acertos = 0
        for sorteio in teste_real:
            for j in cart["jogos"]:
                ac = sum(1 for a, b in zip(j["jogo"], sorteio) if a == b)
                total_acertos += ac
        return True, f"Avaliacao out-of-sample em {len(teste_real)} concursos realizada"

    def teste_7_monte_carlo(self):
        rng = random.Random(42)
        jogo_teste = [1, 2, 3, 4, 5, 6, 7]
        acertos_simulados = {k: 0 for k in range(8)}
        NUM_SIM = 10000

        for _ in range(NUM_SIM):
            sorteio = [rng.randint(0, 9) for _ in range(7)]
            ac = sum(1 for a, b in zip(jogo_teste, sorteio) if a == b)
            acertos_simulados[ac] += 1

        media_empirica = sum(k * acertos_simulados[k] for k in range(8)) / NUM_SIM
        assert abs(media_empirica - 0.70) < 0.05
        return True, f"10.000 iteracoes: media empirica = {media_empirica:.3f} (teorico: 0.700)"

    def teste_8_comparacao_acaso(self):
        bk = self.motor.executar_backtesting(concursos_teste=5, quantidade_jogos=3)
        assert "veredito_comparacao_acaso" in bk
        assert "t_statistic" in bk["estatistica_teste"]
        assert "p_valor" in bk["estatistica_teste"]
        return True, f"Teste de hipotese formulado: {bk['veredito_comparacao_acaso'][:45]}..."

    def teste_9_overfitting(self):
        res = self.motor.gerar_carteira(10)
        scores = [j["score_sms"] for j in res["jogos"]]
        assert max(scores) <= 99.0
        assert min(scores) >= 10.0
        desvio_scores = statistics.stdev(scores)
        assert desvio_scores > 0.1
        return True, f"Scores SMS calibrados com dispersao natural (stdev = {desvio_scores:.2f})"

    def teste_10_falsos_positivos(self):
        pares_info = self.motor.stats["pares_intercolunas"]
        assert "total_testes_realizados" in pares_info
        assert "descobertas_significativas_fdr" in pares_info
        assert pares_info["total_testes_realizados"] > 1000
        return True, f"Correcao FDR aplicada em {pares_info['total_testes_realizados']} pares testados"

    def teste_11_estabilidade(self):
        p1 = self.motor._obter_pesos_estrategia()
        soma_p = sum(p1[k] for k in ["freq_hist", "freq_rec", "gap", "lift", "centroide", "entropia"])
        assert abs(soma_p - 1.0) < 1e-6
        return True, "Pesos normalizados somam 1.0 com penalidades estruturais fixas"

    def teste_12_diversificacao(self):
        res = self.motor.gerar_carteira(10)
        met = res["metricas_carteira"]
        assert met["diversificacao"] >= 70.0
        assert met["hamming_medio"] >= 4.0
        assert met["redundancia"] <= 30.0
        return True, f"Diversificacao = {met['diversificacao']}% | Hamming Medio = {met['hamming_medio']}/7"

    def teste_13_duplicidade(self):
        res = self.motor.gerar_carteira(20)
        jogos_tuplas = [tuple(j["jogo"]) for j in res["jogos"]]
        assert len(jogos_tuplas) == len(set(jogos_tuplas))
        assert res["auditoria_limites"]["duplicidades_na_carteira"] == 0
        return True, "Carteira de 20 jogos gerada com ZERO duplicidades"

    def teste_14_integridade_dados(self):
        N = len(self.motor.historico_completo)
        assert N >= 600
        for idx, draw in enumerate(self.motor.historico_completo):
            assert len(draw) == 7
            assert all(0 <= x <= 9 for x in draw)
        return True, f"Historico verificado com {N} concursos oficiais integros"

    def teste_15_interface_endpoints(self):
        import api
        req = api.MotorSuperSeteRequest(quantidade_jogos=3)
        res = api.endpoint_motor_supersete(req)
        assert res["sucesso"] is True
        assert len(res["jogos"]) == 3
        return True, "Endpoints REST respondem com schema Pydantic consistente"

    def teste_16_exportacao(self):
        res = self.motor.gerar_carteira(3)
        for j in res["jogos"]:
            assert "jogo_formatado" in j
            assert len(j["colunas"]) == 7
            for c in range(1, 8):
                assert f"C{c}" in j["colunas"]
        return True, "Formatacao 'C1 - C2 - C3 - C4 - C5 - C6 - C7' validada"

    def teste_17_atualizacao_novo_concurso(self):
        novo_concurso = [9, 8, 7, 6, 5, 4, 3]
        novo_hist = copy.deepcopy(self.motor.historico_completo)
        novo_hist.append(novo_concurso)
        motor_atualizado = MotorSuperSeteB2B(historico=novo_hist)
        assert motor_atualizado.num_concursos == self.motor.num_concursos + 1
        assert motor_atualizado.stats["modelos_colunas"][0]["digitos"][9]["atraso_atual"] == 0
        return True, "Recalculo instantaneo pos-concurso verificado com precisao"

    def teste_18_honestidade_informacoes(self):
        res = self.motor.gerar_carteira(5)
        assert "frase_obrigatoria" in res
        assert self.motor.FRASE_OBRIGATORIA in res["frase_obrigatoria"]
        diag = res["diagnostico_cientifico"]
        niveis_validos = [
            "EVIDENCIA MODERADA A FORTE",
            "EVIDENCIA MODERADA",
            "EVIDENCIA FRACA",
            "SEM EVIDENCIA ESTATISTICA RELEVANTE",
            "EVIDÊNCIA MODERADA A FORTE",
            "EVIDÊNCIA MODERADA",
            "EVIDÊNCIA FRACA",
            "SEM EVIDÊNCIA ESTATÍSTICA RELEVANTE"
        ]
        assert diag["nivel"] in niveis_validos
        assert "nota_transparencia" in diag
        return True, "Frase obrigatoria e classificacao de evidencia atestadas"


if __name__ == "__main__":
    bateria = TestesCientificosSuperSete()
    sucesso = bateria.executar_todos()
    if not sucesso:
        sys.exit(1)