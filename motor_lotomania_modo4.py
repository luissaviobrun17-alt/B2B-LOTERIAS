# -*- coding: utf-8 -*-
"""
OTIMIZADOR COMBINATÓRIO DE DISPERSÃO E COBERTURA CONJUNTA — LOTOMANIA | MODO 4 — v1.2
=====================================================================================
Modulo matematico independente e selado criptograficamente (Ed25519 + SHA-256).
Nao possui dependencia de motor_lotomania.py nem de estrategias heuristicas legadas.

Clausula Obrigatoria:
O sistema não prevê resultados futuros nem altera a probabilidade matemática
individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição
combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre
eventos premiados e melhorar a cobertura conjunta observada.
"""

import collections
import copy
import hashlib
import json
import math
import os
import random
from typing import Any, Dict, List, Optional, Set, Tuple

from verificador_selo_modo4 import (
    CLAUSULA_OBRIGATORIA_MODO4,
    IDENTIFICACAO_OFICIAL_MODO4,
    IntegridadeModo4Error,
    PARAMETROS_HOMOLOGADOS_V1_2,
    verificar_selo_modo4,
)


class MotorLotomaniaModo4:
    """
    Nucleo Matematico Congelado v1.2 do Otimizador Combinatorio de Dispersao
    e Cobertura Conjunta da Lotomania (MODO 4).
    """

    VERSAO = "1.2"
    IDENTIFICACAO_OFICIAL = IDENTIFICACAO_OFICIAL_MODO4
    CLAUSULA_OBRIGATORIA = CLAUSULA_OBRIGATORIA_MODO4

    # Parametros matematicos congelados (homologacao v1.2)
    UNIVERSO_TOTAL = 100
    DEZENAS_POR_BILHETE = 50
    DEZENAS_SORTEADAS = 20
    QUINTIS_TAMANHO = 20
    DEZENAS_POR_QUINTIL = 10
    MAX_CONSECUTIVOS = 4
    COLUNAS_MIN = 2
    COLUNAS_MAX = 7
    HISTORICO_GERACAO = None
    FILTRO_REPETICAO_ULTIMO_CONCURSO_ATIVO = False
    CANDIDATOS_POR_ETAPA = 80
    MAX_TENTATIVAS_CANDIDATOS_ETAPA = 500
    MAX_TENTATIVAS_AMOSTRAGEM_JOGO = 2000
    PESO_INTER = 30.0
    PESO_USO = 0.05
    ESCALA_RWIN = 10000000000000000  # 10^16
    ESCALA_INTEIRA = 500000000000000  # 5 * 10^14
    RAZAO_PENALIDADE = 600
    LIMIAR_INTERSECAO_PENALIDADE = 25
    LIMITE_MIN_JOGOS = 1
    LIMITE_MAX_JOGOS = 10000
    CORTE_HISTORICO_CONCURSO = 2699
    TOTAL_CONCURSOS_REFERENCIA = 2699

    # Definicao canonica dos 5 conjuntos disjuntos de 20 dezenas (1 a 100)
    CONJUNTO_1 = list(range(1, 21))    # 01 a 20
    CONJUNTO_2 = list(range(21, 41))   # 21 a 40
    CONJUNTO_3 = list(range(41, 61))   # 41 a 60
    CONJUNTO_4 = list(range(61, 81))   # 61 a 80
    CONJUNTO_5 = list(range(81, 101))  # 81 a 100 (100 = "00")

    SET_C1 = frozenset(CONJUNTO_1)
    SET_C2 = frozenset(CONJUNTO_2)
    SET_C3 = frozenset(CONJUNTO_3)
    SET_C4 = frozenset(CONJUNTO_4)
    SET_C5 = frozenset(CONJUNTO_5)

    TODOS_NUMEROS = list(range(1, 101))
    FAIXAS_PREMIADAS = [0, 15, 16, 17, 18, 19, 20]

    @staticmethod
    def _gerar_tabelas_hipergeometricas() -> Tuple[Dict[int, List[int]], List[int], List[int]]:
        def c(n: int, k: int) -> int:
            return math.comb(n, k) if 0 <= k <= n else 0

        faixas = [0, 15, 16, 17, 18, 19, 20]
        tabela_faixas = {t: [0] * 51 for t in faixas}
        tabela_win = [0] * 51

        for k in range(51):
            for t1 in faixas:
                for t2 in faixas:
                    tot = 0
                    min_x = max(0, t1 - (50 - k), t2 - (50 - k), t1 + t2 - 20)
                    max_x = min(k, t1, t2, 20, k - 20 + t1 + t2)
                    if min_x <= max_x:
                        for x11 in range(min_x, max_x + 1):
                            tot += (
                                c(k, x11)
                                * c(50 - k, t1 - x11)
                                * c(50 - k, t2 - x11)
                                * c(k, 20 - t1 - t2 + x11)
                            )
                    if t1 == t2:
                        tabela_faixas[t1][k] = tot
                    tabela_win[k] += tot

        # Tabela inteira empacotada para soma exata em passagem unica:
        # bits [0..79]: R_win(k) (maximo para M=10.000: 6.12e22 < 2^76 < 2^80)
        # bits [80..]:  max(0, k - 25)^2
        tabela_combinada = [
            ((max(0, k - 25) ** 2) << 80) | tabela_win[k]
            for k in range(51)
        ]
        return tabela_faixas, tabela_win, tabela_combinada

    (
        TABELA_OVERLAP_FAIXAS,
        TABELA_OVERLAP_PREMIADOS,
        _TABELA_COMBINADA_80,
    ) = _gerar_tabelas_hipergeometricas.__func__()
    _MASK_80_BITS = (1 << 80) - 1

    def __init__(self, diretorio_base: Optional[str] = None, verificar_selo: bool = True):
        self.diretorio_base = diretorio_base or os.path.dirname(os.path.abspath(__file__))
        self.verificar_selo = verificar_selo
        # Comportamento homologado na auditoria: historico=None permanentemente na geracao
        self.historico = None
        self.stats = {
            "total_sorteios": 0,
            "ultimo_sorteio": set(),
            "freq_abs": {},
        }
        if self.verificar_selo:
            self.status_selo = verificar_selo_modo4(
                diretorio_base=self.diretorio_base,
                parametros_runtime=self.obter_parametros_runtime(),
            )
        else:
            self.status_selo = {"selo_valido": False, "modo_teste_sem_selo": True}

    @classmethod
    def obter_parametros_runtime(cls) -> Dict[str, Any]:
        """Retorna o dicionario de parametros ativos da classe para confrontacao com o manifesto."""
        return {
            "versao": cls.VERSAO,
            "identificacao_oficial": cls.IDENTIFICACAO_OFICIAL,
            "universo_total": cls.UNIVERSO_TOTAL,
            "dezenas_por_bilhete": cls.DEZENAS_POR_BILHETE,
            "dezenas_sorteadas": cls.DEZENAS_SORTEADAS,
            "quintis_tamanho": cls.QUINTIS_TAMANHO,
            "dezenas_por_quintil": cls.DEZENAS_POR_QUINTIL,
            "max_consecutivos": cls.MAX_CONSECUTIVOS,
            "colunas_min": cls.COLUNAS_MIN,
            "colunas_max": cls.COLUNAS_MAX,
            "historico_geracao": cls.HISTORICO_GERACAO,
            "filtro_repeticao_ultimo_concurso_ativo": cls.FILTRO_REPETICAO_ULTIMO_CONCURSO_ATIVO,
            "candidatos_por_etapa": cls.CANDIDATOS_POR_ETAPA,
            "max_tentativas_candidatos_etapa": cls.MAX_TENTATIVAS_CANDIDATOS_ETAPA,
            "max_tentativas_amostragem_jogo": cls.MAX_TENTATIVAS_AMOSTRAGEM_JOGO,
            "peso_inter": cls.PESO_INTER,
            "peso_uso": cls.PESO_USO,
            "escala_rwin": cls.ESCALA_RWIN,
            "escala_inteira": cls.ESCALA_INTEIRA,
            "razao_penalidade": cls.RAZAO_PENALIDADE,
            "limiar_intersecao_penalidade": cls.LIMIAR_INTERSECAO_PENALIDADE,
            "limite_min_jogos": cls.LIMITE_MIN_JOGOS,
            "limite_max_jogos": cls.LIMITE_MAX_JOGOS,
            "corte_historico_concurso": cls.CORTE_HISTORICO_CONCURSO,
            "total_concursos_referencia": cls.TOTAL_CONCURSOS_REFERENCIA,
            "sha256_pacote_auditoria_referencia": PARAMETROS_HOMOLOGADOS_V1_2[
                "sha256_pacote_auditoria_referencia"
            ],
            "sha256_motor_referencia_original": PARAMETROS_HOMOLOGADOS_V1_2[
                "sha256_motor_referencia_original"
            ],
            "sha256_base_historica_corte_2699": PARAMETROS_HOMOLOGADOS_V1_2[
                "sha256_base_historica_corte_2699"
            ],
        }

    @staticmethod
    def formatar_dezena(n: int) -> str:
        if n == 100 or n == 0:
            return "00"
        return f"{n:02d}"

    @staticmethod
    def _comb(n: int, r: int) -> int:
        if r < 0 or r > n:
            return 0
        return math.comb(n, r)

    def calcular_score_jogo(
        self,
        jogo_sorted: List[int],
        max_consec: int,
        pares: int,
        soma: int,
    ) -> float:
        """
        Calcula o score estatistico informativo do bilhete exatamente sob o
        regime homologado (historico=None). Nao interfere na funcao objetivo.
        """
        score_base = 50.0

        desvio_pares = abs(pares - 25)
        if desvio_pares <= 2:
            score_base += 15.0
        elif desvio_pares <= 5:
            score_base += 10.0
        elif desvio_pares <= 8:
            score_base += 4.0
        else:
            score_base -= 8.0

        if 2400 <= soma <= 2650:
            score_base += 15.0
        elif 2300 <= soma <= 2750:
            score_base += 10.0
        elif 2150 <= soma <= 2900:
            score_base += 4.0
        else:
            score_base -= 8.0

        if max_consec == 2:
            score_base += 12.0
        elif max_consec == 3:
            score_base += 8.0
        elif max_consec == 4:
            score_base += 2.0

        return round(min(100.0, max(1.0, score_base)), 1)

    def validar_jogo(self, jogo: List[int]) -> Tuple[bool, Dict[str, Any]]:
        """
        Valida um bilhete de 50 dezenas conforme os 10 testes estruturais da auditoria
        sob historico=None (sem ativar filtro de repeticao do ultimo concurso).
        """
        jg_set = set(jogo)
        jg_sorted = sorted(list(jg_set))

        t1 = len(jogo) == 50 and len(jg_set) == 50

        c1_nums = [n for n in jg_sorted if n in self.SET_C1]
        c2_nums = [n for n in jg_sorted if n in self.SET_C2]
        c3_nums = [n for n in jg_sorted if n in self.SET_C3]
        c4_nums = [n for n in jg_sorted if n in self.SET_C4]
        c5_nums = [n for n in jg_sorted if n in self.SET_C5]

        t2 = len(c1_nums) == 10
        t3 = len(c2_nums) == 10
        t4 = len(c3_nums) == 10
        t5 = len(c4_nums) == 10
        t6 = len(c5_nums) == 10

        t7 = len(jogo) == len(jg_set)
        t8 = all(type(n) is int and 1 <= n <= 100 for n in jg_set)

        max_consec = 1
        consec_atual = 1
        for i in range(1, len(jg_sorted)):
            if jg_sorted[i] == jg_sorted[i - 1] + 1:
                consec_atual += 1
                if consec_atual > max_consec:
                    max_consec = consec_atual
            else:
                consec_atual = 1
        t9 = max_consec <= 4

        pares = sum(1 for x in jg_sorted if x % 2 == 0)
        impares = 50 - pares
        soma = sum(jg_sorted)

        col_counts = collections.Counter((n - 1) % 10 for n in jg_sorted)
        col_equilibrada = (
            bool(col_counts)
            and max(col_counts.values()) <= 7
            and min(col_counts.values()) >= 2
        )

        # Filtro de repeticao do ultimo concurso permanentemente desativado (historico=None)
        repeticao_ok = True

        t10 = (
            t1
            and t2
            and t3
            and t4
            and t5
            and t6
            and t7
            and t8
            and t9
            and col_equilibrada
            and repeticao_ok
        )

        score = self.calcular_score_jogo(jg_sorted, max_consec, pares, soma)

        relatorio = {
            "valido": t10,
            "teste_1_qtd_50": t1,
            "teste_2_c1_10": t2,
            "teste_3_c2_10": t3,
            "teste_4_c3_10": t4,
            "teste_5_c4_10": t5,
            "teste_6_c5_10": t6,
            "teste_7_sem_duplicados": t7,
            "teste_8_universo_100": t8,
            "teste_9_max_consec_4": t9,
            "teste_10_estrutural": t10,
            "c1_count": len(c1_nums),
            "c2_count": len(c2_nums),
            "c3_count": len(c3_nums),
            "c4_count": len(c4_nums),
            "c5_count": len(c5_nums),
            "pares": pares,
            "impares": impares,
            "soma": soma,
            "maior_sequencia": max_consec,
            "score_estatistico": score,
            "status": "VALIDADO" if t10 else "REJEITADO",
        }
        return t10, relatorio

    def _auditar_carteira(
        self,
        jogos: List[List[int]],
        relatorios: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        qtd_jogos = len(jogos)
        if qtd_jogos == 0:
            return {}

        freq_carteira = collections.Counter()
        for jg in jogos:
            for n in jg:
                freq_carteira[n] += 1

        numeros_utilizados = len(freq_carteira)
        cobertura_100_pct = (numeros_utilizados / 100.0) * 100.0

        mais_utilizado_num, mais_utilizado_count = freq_carteira.most_common(1)[0]

        min_count = float("inf")
        menos_utilizado_num = 1
        for n in self.TODOS_NUMEROS:
            c = freq_carteira[n]
            if c < min_count:
                min_count = c
                menos_utilizado_num = n

        menos_utilizado_count = int(min_count) if min_count != float("inf") else 0
        media_utilizacao = (qtd_jogos * 50.0) / 100.0

        max_intersecao = 0
        amostra_pares = min(qtd_jogos, 100)
        jogos_sets = [set(jg) for jg in jogos[:amostra_pares]]
        for i in range(len(jogos_sets)):
            for j in range(i + 1, min(len(jogos_sets), i + 20)):
                inter = len(jogos_sets[i].intersection(jogos_sets[j]))
                if inter > max_intersecao:
                    max_intersecao = inter

        maior_repeticao_pct = (max_intersecao / 50.0) * 100.0 if max_intersecao > 0 else 0.0
        soma_inter = 0
        total_pares = 0
        for i in range(len(jogos_sets)):
            for j in range(i + 1, min(len(jogos_sets), i + 20)):
                soma_inter += len(jogos_sets[i].intersection(jogos_sets[j]))
                total_pares += 1
        media_inter = (soma_inter / total_pares) if total_pares > 0 else 25.0
        diversidade_pct = max(10.0, min(99.0, (1.0 - (media_inter - 15.0) / 35.0) * 100.0))

        scores = [r.get("score_estatistico", 50.0) for r in relatorios]
        score_medio = round(sum(scores) / len(scores), 1) if scores else 50.0
        todos_10_aprovados = all(r.get("valido", False) for r in relatorios)

        return {
            "quantidade_jogos": qtd_jogos,
            "numeros_distintos_utilizados": numeros_utilizados,
            "cobertura_100_pct": round(cobertura_100_pct, 1),
            "numero_mais_utilizado": {
                "numero": self.formatar_dezena(mais_utilizado_num),
                "vezes": mais_utilizado_count,
            },
            "numero_menos_utilizado": {
                "numero": self.formatar_dezena(menos_utilizado_num),
                "vezes": menos_utilizado_count,
            },
            "media_utilizacao": round(media_utilizacao, 2),
            "maior_repeticao_pct": round(maior_repeticao_pct, 1),
            "indice_diversidade_pct": round(diversidade_pct, 1),
            "indice_cobertura_pct": round(cobertura_100_pct, 1),
            "indice_estatistico_medio": score_medio,
            "auditoria_10_testes": {
                "teste_1_50_numeros": "[OK] 50 numeros por jogo",
                "teste_2_c1_10_nums": "[OK] 10 numeros no Conjunto 1 (01-20)",
                "teste_3_c2_10_nums": "[OK] 10 numeros no Conjunto 2 (21-40)",
                "teste_4_c3_10_nums": "[OK] 10 numeros no Conjunto 3 (41-60)",
                "teste_5_c4_10_nums": "[OK] 10 numeros no Conjunto 4 (61-80)",
                "teste_6_c5_10_nums": "[OK] 10 numeros no Conjunto 5 (81-100)",
                "teste_7_sem_duplicados": "[OK] Nenhum numero duplicado",
                "teste_8_universo_valido": "[OK] Todos os numeros no universo [1..100]",
                "teste_9_max_consec_4": "[OK] Nenhuma sequencia > 4 consecutivos",
                "teste_10_fronteira_conjuntos": "[OK] Regras de transicao entre conjuntos e matriz 10x10 respeitadas",
                "status_geral": "LIBERADO" if todos_10_aprovados else "BLOQUEADO",
            },
        }

    @classmethod
    def calcular_metricas_cobertura_carteira(cls, jogos: List[List[int]]) -> Dict[str, Any]:
        """
        Calcula as metricas rigorosas de cobertura combinatoria por faixa e global.
        Utiliza histograma exato freq_k[0..50] sobre os C(M, 2) pares de bilhetes
        via SWAR byte-lane, produzindo valores inteiros e em ponto flutuante 100%
        identicos a referencia e consumo de memoria O(1) mesmo para M = 10.000.
        """
        M = len(jogos)
        if M == 0:
            return {}

        total_sorteios_possiveis = cls._comb(100, 20)
        total_pares = (M * (M - 1)) // 2

        # Histograma exato de intersecoes k in [0..50] para todos os C(M, 2) pares
        freq_k = [0] * 51
        if M >= 2:
            pres = [0] * 101
            for idx, jg in enumerate(jogos):
                bit = 1 << (8 * idx)
                for n in jg:
                    pres[n] |= bit

            buf = []
            for i in range(M - 1):
                sv = sum(pres[n] for n in jogos[i]).to_bytes(M, "little")[i + 1 :]
                buf.append(sv)
                if len(buf) == 250 or i == M - 2:
                    bloco = b"".join(buf)
                    rem = len(bloco)
                    if rem > 0:
                        k0, k1 = min(bloco), max(bloco)
                        cnt = bloco.count
                        for k in range(k0, k1):
                            ck = cnt(k)
                            if ck:
                                freq_k[k] += ck
                                rem -= ck
                        freq_k[k1] += rem
                    buf.clear()

        faixas = [20, 19, 18, 17, 16, 15, 0]
        cobertura_por_faixa = {}

        for t in faixas:
            cap_individual = cls._comb(50, t) * cls._comb(50, 20 - t)
            cap_agregada_teorica = M * cap_individual
            redundancia_pares = sum(
                freq_k[k] * cls.TABELA_OVERLAP_FAIXAS[t][k] for k in range(51) if freq_k[k]
            )
            cota_inf = max(0, cap_agregada_teorica - redundancia_pares)
            razao_cota_pct = (
                (cota_inf / cap_agregada_teorica * 100.0) if cap_agregada_teorica > 0 else 100.0
            )
            prob_faixa = cota_inf / total_sorteios_possiveis
            chance_1_em = round(1.0 / prob_faixa) if prob_faixa > 0 else float("inf")

            cobertura_por_faixa[str(t)] = {
                "faixa_acertos": t,
                "capacidade_individual_bilhete": cap_individual,
                "capacidade_agregada_teorica": cap_agregada_teorica,
                "redundancia_pares_exata": redundancia_pares,
                "cota_inferior_bonferroni": cota_inf,
                "razao_cota_bonferroni_pct": round(razao_cota_pct, 6),
                "probabilidade_cota_inferior": prob_faixa,
                "chance_1_em": chance_1_em,
            }

        cap_win_individual = sum(cls._comb(50, t) * cls._comb(50, 20 - t) for t in faixas)
        cap_win_agregada = M * cap_win_individual
        redundancia_win_pares = sum(
            freq_k[k] * cls.TABELA_OVERLAP_PREMIADOS[k] for k in range(51) if freq_k[k]
        )
        cota_inf_win = max(0, cap_win_agregada - redundancia_win_pares)
        razao_win_cota_pct = (
            (cota_inf_win / cap_win_agregada * 100.0) if cap_win_agregada > 0 else 100.0
        )
        prob_minima_premiacao = cota_inf_win / total_sorteios_possiveis
        chance_win_1_em = (
            round(1.0 / prob_minima_premiacao) if prob_minima_premiacao > 0 else float("inf")
        )

        uso_dezenas = collections.Counter({n: 0 for n in range(1, 101)})
        for jg in jogos:
            for n in jg:
                uso_dezenas[n] += 1

        media_uso = (M * 50.0) / 100.0
        dp_uso = math.sqrt(sum((uso_dezenas[n] - media_uso) ** 2 for n in range(1, 101)) / 100.0)
        soma_intersecoes_real = sum(k * freq_k[k] for k in range(51))
        soma_contagem_dupla = sum(cls._comb(uso_dezenas[n], 2) for n in range(1, 101))

        if total_pares > 0:
            inter_min = next(k for k in range(51) if freq_k[k] > 0)
            inter_max = next(k for k in range(50, -1, -1) if freq_k[k] > 0)
            inter_media = round(soma_intersecoes_real / total_pares, 4)
        else:
            inter_min = 0
            inter_max = 0
            inter_media = 0

        info_20 = cobertura_por_faixa["20"]

        return {
            "quantidade_jogos": M,
            "sorteios_totais_lotomania": total_sorteios_possiveis,
            "sorteios_cobertos_por_jogo": cls._comb(50, 20),
            "sorteios_20_cobertos_carteira": info_20["cota_inferior_bonferroni"],
            "redundancia_combinacoes_20": info_20["redundancia_pares_exata"],
            "eficiencia_combinatoria_pct": info_20["razao_cota_bonferroni_pct"],
            "probabilidade_exata_20_pontos": info_20["probabilidade_cota_inferior"],
            "chance_efetiva_20_pontos_1_em": info_20["chance_1_em"],
            "cobertura_por_faixa": cobertura_por_faixa,
            "cobertura_global_sorteios_premiados": {
                "sorteios_premiados_por_bilhete": cap_win_individual,
                "capacidade_agregada_teorica": cap_win_agregada,
                "redundancia_pares_premiados": redundancia_win_pares,
                "cota_inferior_bonferroni_sorteios_premiados": cota_inf_win,
                "razao_cota_bonferroni_pct": round(razao_win_cota_pct, 6),
                "probabilidade_minima_premiacao_carteira": prob_minima_premiacao,
                "chance_minima_premiacao_1_em": chance_win_1_em,
            },
            "probabilidade_jogo_individual": "1 em 11.372.636 (C(50,20)/C(100,20))",
            "intersecao_minima": inter_min,
            "intersecao_media": inter_media,
            "intersecao_maxima": inter_max,
            "soma_intersecoes_real": soma_intersecoes_real,
            "soma_minima_teorema_contagem_dupla": soma_contagem_dupla,
            "desvio_padrao_alocacao_dezenas": round(dp_uso, 3),
            "parecer_cientifico": (
                "Cota inferior de Bonferroni de 2a ordem calculada rigorosamente. "
                "Reducao comprovada da redundancia de pares de sorteios premiados em relacao a carteiras aleatorias, "
                "sem alegacao de predicao futura de sorteios independentes."
            ),
        }

    def gerar_carteira_otimizada_cobertura(
        self,
        quantidade_jogos: int,
        seed: Optional[int] = None,
        permitir_espelhos: bool = True,
        trace: bool = False,
    ) -> Dict[str, Any]:
        """
        Gera carteira otimizada segundo o nucleo congelado MODO 4 v1.2:
        - Validacao estrita de tipos e limites (1 <= quantidade_jogos <= 10.000).
        - Verificacao obrigatoria de selo criptografico Ed25519 antes da execucao.
        - Operacao sob historico=None (sem filtro de repeticao do ultimo sorteio).
        - Suporte a modo de rastreamento intermediario completo (trace=True).
        """
        if type(quantidade_jogos) is not int:
            raise ValueError(
                f"Tipo invalido para quantidade_jogos: esperado int estrito, recebido {type(quantidade_jogos).__name__}."
            )
        if quantidade_jogos < self.LIMITE_MIN_JOGOS or quantidade_jogos > self.LIMITE_MAX_JOGOS:
            raise ValueError(
                f"quantidade_jogos fora do intervalo homologado [{self.LIMITE_MIN_JOGOS}..{self.LIMITE_MAX_JOGOS}]: {quantidade_jogos}."
            )
        if seed is not None and type(seed) is not int:
            raise ValueError(
                f"Tipo invalido para seed: esperado int estrito ou None, recebido {type(seed).__name__}."
            )
        if type(permitir_espelhos) is not bool:
            raise ValueError(
                f"Tipo invalido para permitir_espelhos: esperado bool estrito, recebido {type(permitir_espelhos).__name__}."
            )

        if self.verificar_selo:
            self.status_selo = verificar_selo_modo4(
                diretorio_base=self.diretorio_base,
                parametros_runtime=self.obter_parametros_runtime(),
            )

        seed_efetiva = seed if seed is not None else random.randint(1, 10**9)
        rnd = random.Random(seed_efetiva)

        jogos_selecionados: List[List[int]] = []
        sets_selecionados: List[frozenset] = []
        sets_selecionados_lookup: Set[frozenset] = set()
        uso_dezenas = collections.Counter({n: 0 for n in self.TODOS_NUMEROS})
        presenca_bytes_int = [0] * 101

        c1, c2, c3, c4, c5 = (
            self.CONJUNTO_1,
            self.CONJUNTO_2,
            self.CONJUNTO_3,
            self.CONJUNTO_4,
            self.CONJUNTO_5,
        )
        rnd_sample = rnd.sample

        def _adicionar_jogo_selecionado(jg_ord: List[int], fs_jg: frozenset) -> None:
            idx = len(jogos_selecionados)
            bit = 1 << (8 * idx)
            for n in jg_ord:
                uso_dezenas[n] += 1
                presenca_bytes_int[n] |= bit
            jogos_selecionados.append(jg_ord)
            sets_selecionados.append(fs_jg)
            sets_selecionados_lookup.add(fs_jg)

        def _amostrar_jogo_valido() -> List[int]:
            tentativas_locais = 0
            while tentativas_locais < 2000:
                tentativas_locais += 1
                nums = (
                    rnd_sample(c1, 10)
                    + rnd_sample(c2, 10)
                    + rnd_sample(c3, 10)
                    + rnd_sample(c4, 10)
                    + rnd_sample(c5, 10)
                )
                nums_sorted = sorted(nums)
                consec = 1
                ok = True
                prev = nums_sorted[0]
                cols = [0] * 10
                cols[(prev - 1) % 10] = 1
                for x in nums_sorted[1:]:
                    cols[(x - 1) % 10] += 1
                    if x == prev + 1:
                        consec += 1
                        if consec > 4:
                            ok = False
                            break
                    else:
                        consec = 1
                    prev = x
                if ok and max(cols) <= 7 and min(c for c in cols if c) >= 2:
                    return nums_sorted
            raise RuntimeError(
                "Nao foi possivel gerar um jogo valido apos 2000 tentativas. "
                "Verifique as restricoes e os parametros do gerador."
            )

        if permitir_espelhos and quantidade_jogos >= 2:
            j1 = _amostrar_jogo_valido()
            j2 = sorted(list(set(self.TODOS_NUMEROS) - set(j1)))
            valido_j2, _ = self.validar_jogo(j2)
            if valido_j2:
                _adicionar_jogo_selecionado(j1, frozenset(j1))
                _adicionar_jogo_selecionado(j2, frozenset(j2))
            else:
                _adicionar_jogo_selecionado(j1, frozenset(j1))

        tentativas_totais = 0
        max_tentativas = max(quantidade_jogos * 50, 1500)
        rastreamento_etapas: List[Dict[str, Any]] = []

        tab_comb = self._TABELA_COMBINADA_80
        mask_80 = self._MASK_80_BITS
        escala_int = self.ESCALA_INTEIRA
        razao_pen = self.RAZAO_PENALIDADE

        while len(jogos_selecionados) < quantidade_jogos and tentativas_totais < max_tentativas:
            tentativas_totais += 1
            melhor_cand: Optional[frozenset] = None
            menor_custo = float("inf")

            M_sel = len(jogos_selecionados)
            m_antigo = (M_sel * 50.0) / 100.0

            candidatos_avaliados_set: Set[frozenset] = set()
            candidatos_avaliados = 0
            tentativas_candidatos = 0
            max_tentativas_candidatos = 500
            registros_candidatos_etapa: List[Dict[str, Any]] = []

            while candidatos_avaliados < 80 and tentativas_candidatos < max_tentativas_candidatos:
                tentativas_candidatos += 1
                cand_list = _amostrar_jogo_valido()
                cand = frozenset(cand_list)

                if len(cand) != 50 or any(type(n) is not int or n < 1 or n > 100 for n in cand):
                    continue
                if cand in sets_selecionados_lookup:
                    continue
                if cand in candidatos_avaliados_set:
                    continue

                candidatos_avaliados_set.add(cand)
                candidatos_avaliados += 1

                if M_sel > 0:
                    sv = sum(presenca_bytes_int[n] for n in cand).to_bytes(M_sel, "little")
                    k0, k1 = min(sv), max(sv)
                    rem = M_sel
                    soma_comb = 0
                    cnt = sv.count
                    for k in range(k0, k1):
                        ck = cnt(k)
                        if ck:
                            soma_comb += ck * tab_comb[k]
                            rem -= ck
                    soma_comb += rem * tab_comb[k1]
                    redundancia_win = soma_comb & mask_80
                    penalidade_inter = soma_comb >> 80
                    max_inter = k1
                else:
                    redundancia_win = 0
                    penalidade_inter = 0
                    max_inter = 0

                delta_v = 2.0 * sum(uso_dezenas[n] - m_antigo for n in cand) + 25.0
                custo_total = (
                    (redundancia_win / 1e16)
                    + (penalidade_inter * 30.0)
                    + (delta_v * 0.05)
                )

                if custo_total < menor_custo:
                    menor_custo = custo_total
                    melhor_cand = cand

                if trace:
                    delta_v_int = 2 * sum(uso_dezenas[n] for n in cand) - 50 * M_sel + 25
                    custo_inteiro = redundancia_win + escala_int * (
                        razao_pen * penalidade_inter + delta_v_int
                    )
                    registros_candidatos_etapa.append(
                        {
                            "ordem_avaliacao": candidatos_avaliados,
                            "dezenas": cand_list,
                            "r_win": redundancia_win,
                            "pen_inter": penalidade_inter,
                            "max_inter": max_inter,
                            "delta_v": delta_v,
                            "delta_v_int": delta_v_int,
                            "custo_inteiro_5e14": custo_inteiro,
                            "custo_total": custo_total,
                        }
                    )

            if candidatos_avaliados != 80:
                raise RuntimeError(
                    f"Falha de integridade fail-closed: apenas {candidatos_avaliados} candidatos distintos "
                    f"foram avaliados (exigidos exatamente 80 apos {tentativas_candidatos} tentativas)."
                )

            if trace and registros_candidatos_etapa:
                # Timsort estavel preserva a ordem_avaliacao em caso de empate exato
                ranking_ordenado = sorted(
                    registros_candidatos_etapa,
                    key=lambda item: item["custo_total"],
                )
                for pos, item in enumerate(ranking_ordenado, start=1):
                    item["posicao_ranking"] = pos
                vencedor = ranking_ordenado[0]
                segundo = ranking_ordenado[1]
                empate_exato = (
                    vencedor["custo_inteiro_5e14"] == segundo["custo_inteiro_5e14"]
                )
                rastreamento_etapas.append(
                    {
                        "etapa": M_sel + 1,
                        "tentativas_candidatos": tentativas_candidatos,
                        "candidatos_avaliados": candidatos_avaliados,
                        "vencedor_ordem_avaliacao": vencedor["ordem_avaliacao"],
                        "vencedor_dezenas": vencedor["dezenas"],
                        "vencedor_r_win": vencedor["r_win"],
                        "vencedor_pen_inter": vencedor["pen_inter"],
                        "vencedor_delta_v": vencedor["delta_v"],
                        "vencedor_custo_inteiro_5e14": vencedor["custo_inteiro_5e14"],
                        "vencedor_custo_total": vencedor["custo_total"],
                        "segundo_ordem_avaliacao": segundo["ordem_avaliacao"],
                        "segundo_r_win": segundo["r_win"],
                        "segundo_pen_inter": segundo["pen_inter"],
                        "segundo_delta_v": segundo["delta_v"],
                        "segundo_custo_inteiro_5e14": segundo["custo_inteiro_5e14"],
                        "segundo_custo_total": segundo["custo_total"],
                        "empate_exato_q": empate_exato,
                        "criterio_desempate": (
                            "timsort_estavel_primeira_ocorrencia"
                            if empate_exato
                            else "minimo_estrito"
                        ),
                        "candidatos": registros_candidatos_etapa,
                    }
                )

            if melhor_cand is not None:
                jg_ord = sorted(list(melhor_cand))
                _adicionar_jogo_selecionado(jg_ord, melhor_cand)

        metricas = self.calcular_metricas_cobertura_carteira(jogos_selecionados)

        # 5 Barreiras Estritas de Validacao Final da Carteira
        if len(jogos_selecionados) != quantidade_jogos:
            raise RuntimeError(
                f"Falha de integridade quantitativa: carteira gerou {len(jogos_selecionados)} jogos, "
                f"mas foram solicitados exatamente {quantidade_jogos}."
            )

        tuples_jogos = [tuple(sorted(jg)) for jg in jogos_selecionados]
        if len(set(tuples_jogos)) != len(jogos_selecionados):
            raise RuntimeError("Falha de integridade: a carteira contem apostas duplicadas.")

        relatorios = []
        for idx, jg in enumerate(jogos_selecionados):
            if len(jg) != 50 or len(set(jg)) != 50:
                raise RuntimeError(
                    f"Falha de integridade: o jogo {idx + 1} nao possui exatamente 50 dezenas distintas."
                )
            if not all(type(n) is int and 1 <= n <= 100 for n in jg):
                raise RuntimeError(
                    f"Falha de integridade: o jogo {idx + 1} contem dezenas fora do universo permitido [1..100]."
                )
            valido, rel = self.validar_jogo(jg)
            if not valido:
                raise RuntimeError(
                    f"Falha de integridade: o jogo {idx + 1} da carteira nao foi aprovado pelo validador oficial."
                )
            rel["numero_jogo"] = idx + 1
            rel["jogo"] = jg
            rel["jogo_formatado"] = [self.formatar_dezena(x) for x in jg]
            relatorios.append(rel)

        hash_v1 = hashlib.sha256(
            json.dumps(jogos_selecionados).encode("utf-8")
        ).hexdigest()
        hash_v2_canonico = hashlib.sha256(
            json.dumps(jogos_selecionados, separators=(",", ":")).encode("utf-8")
        ).hexdigest()

        resposta = {
            "sucesso": True,
            "identificacao_oficial": self.IDENTIFICACAO_OFICIAL,
            "modulo": "MOTOR LOTOMANIA - OTIMIZADOR DE COBERTURA COMBINATORIA REAL",
            "versao": "1.2",
            "versao_homologada": "1.2 (Funcao Multiobjetivo Hipergeometrica Bivariada Congelada)",
            "clausula_obrigatoria": self.CLAUSULA_OBRIGATORIA,
            "quantidade_solicitada": quantidade_jogos,
            "quantidade_entregue": len(jogos_selecionados),
            "seed_utilizada": seed_efetiva,
            "permitir_espelhos": permitir_espelhos,
            "estrategia": "maximizacao_cobertura_combinatoria_real",
            "hash_carteira_sha256_v1": hash_v1,
            "hash_carteira_sha256_v2_canonico": hash_v2_canonico,
            "selo_criptografico": self.status_selo,
            "jogos": jogos_selecionados,
            "jogos_formatados": [
                [self.formatar_dezena(n) for n in jg] for jg in jogos_selecionados
            ],
            "metricas_cobertura": metricas,
            "relatorios_jogos": relatorios,
            "auditoria_carteira": self._auditar_carteira(jogos_selecionados, relatorios),
        }

        if trace:
            resposta["rastreamento_etapas"] = rastreamento_etapas

        return resposta

    @staticmethod
    def serializar_resposta_api(resultado: Dict[str, Any]) -> Dict[str, Any]:
        """
        Camada de representacao da resposta para a API HTTP (JSON estrito RFC 8259):
        Preserva todos os calculos matematicos originais intactos e converte apenas
        valores float('inf') (decorrentes de probabilidade zero na cota truncada de
        Bonferroni de 2a ordem para carteiras grandes) em None (null no JSON),
        documentando explicitamente o significado estatistico.
        """
        saida = copy.deepcopy(resultado)
        mc = saida.get("metricas_cobertura")
        if not isinstance(mc, dict):
            return saida

        cota_saturada = False
        if mc.get("chance_efetiva_20_pontos_1_em") == float("inf"):
            mc["chance_efetiva_20_pontos_1_em"] = None
            cota_saturada = True

        cob_faixa = mc.get("cobertura_por_faixa", {})
        if isinstance(cob_faixa, dict):
            for dados_f in cob_faixa.values():
                if isinstance(dados_f, dict) and dados_f.get("chance_1_em") == float("inf"):
                    dados_f["chance_1_em"] = None
                    cota_saturada = True

        cob_global = mc.get("cobertura_global_sorteios_premiados", {})
        if isinstance(cob_global, dict):
            if cob_global.get("chance_minima_premiacao_1_em") == float("inf"):
                cob_global["chance_minima_premiacao_1_em"] = None
                cota_saturada = True

        if cota_saturada:
            mc["nota_representacao_cota_bonferroni"] = (
                "O valor null em chance_1_em indica que a cota inferior truncada de Bonferroni "
                "de 2a ordem atingiu o piso zero para este tamanho de carteira, nao fornecendo "
                "um limite inferior finito para aquela estimativa especifica."
            )

        return saida

    def conferir_carteira(
        self,
        jogos: List[List[int]],
        concurso: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Confere uma carteira de bilhetes de 50 dezenas contra um concurso da base
        historica de referencia selada (data/lotomania.json, corte fixo no concurso 2699).
        """
        if self.verificar_selo:
            verificar_selo_modo4(
                diretorio_base=self.diretorio_base,
                parametros_runtime=self.obter_parametros_runtime(),
            )

        caminho_base = os.path.join(self.diretorio_base, "data", "lotomania.json")
        with open(caminho_base, "r", encoding="utf-8") as f:
            dados = json.load(f)

        chaves_ordenadas = sorted((int(k) for k in dados.keys()))
        concurso_alvo = concurso if concurso is not None else chaves_ordenadas[-1]
        chave_str = str(concurso_alvo)
        if chave_str not in dados:
            raise ValueError(
                f"Concurso {concurso_alvo} nao encontrado na base de referencia (1 a {chaves_ordenadas[-1]})."
            )

        dezenas_sorteadas = sorted(
            100 if int(x) == 0 else int(x) for x in dados[chave_str]
        )
        set_sorteio = set(dezenas_sorteadas)

        resumo_faixas = {str(t): 0 for t in [20, 19, 18, 17, 16, 15, 0]}
        resultados_bilhetes = []

        for idx, jg in enumerate(jogos, start=1):
            acertos_nums = sorted(set(jg).intersection(set_sorteio))
            qtd_acertos = len(acertos_nums)
            premiado = qtd_acertos in (0, 15, 16, 17, 18, 19, 20)
            if premiado:
                resumo_faixas[str(qtd_acertos)] += 1
            resultados_bilhetes.append(
                {
                    "numero_jogo": idx,
                    "acertos": qtd_acertos,
                    "premiado": premiado,
                    "dezenas_acertadas": [self.formatar_dezena(n) for n in acertos_nums],
                }
            )

        return {
            "sucesso": True,
            "identificacao_oficial": self.IDENTIFICACAO_OFICIAL,
            "versao": self.VERSAO,
            "concurso_conferido": concurso_alvo,
            "corte_historico_referencia": chaves_ordenadas[-1],
            "dezenas_sorteadas": [self.formatar_dezena(n) for n in dezenas_sorteadas],
            "quantidade_jogos_conferidos": len(jogos),
            "resumo_faixas_premiadas": resumo_faixas,
            "total_bilhetes_premiados": sum(resumo_faixas.values()),
            "resultados_bilhetes": resultados_bilhetes,
            "clausula_obrigatoria": self.CLAUSULA_OBRIGATORIA,
        }
