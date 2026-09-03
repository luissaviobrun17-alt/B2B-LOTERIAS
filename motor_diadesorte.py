"""
===============================================================================
🎯 B2B LOTERIAS — NOVO MOTOR DIA DE SORTE
MOTOR MATEMÁTICO, ESTATÍSTICO E PROBABILÍSTICO
===============================================================================
Desenvolvido sob o papel de Matemático e Físico de Renome Internacional.

PRINCÍPIO FUNDAMENTAL: HONESTIDADE MATEMÁTICA
O motor obedece rigorosamente à matemática, à estatística e à probabilidade.
NÃO ALTERA, NÃO MANIPULA, NÃO OMITE E NÃO FORÇA ANÁLISES PARA AGRADAR AO APOSTADOR.
DIFERENCIAÇÃO ESTRITA:
FATO MATEMÁTICO -> EVIDÊNCIA ESTATÍSTICA -> HEURÍSTICA -> HIPÓTESE.

Resultados passados NÃO garantem resultados futuros; a análise histórica serve
para organizar, filtrar e diversificar as combinações no espaço amostral.
===============================================================================
"""

import math
import itertools
import collections
import statistics
import json
import os
import urllib.request
from typing import List, Dict, Tuple, Optional, Any, Set


class MotorDiaDeSorteB2B:
    """
    Núcleo Matemático, Estatístico e Combinatório Oficial do Dia de Sorte — B2B LOTERIAS.
    """

    # Pool Total: 31 números
    TOTAL_NUMEROS = 31
    TAMANHO_JOGO = 7
    TODOS_NUMEROS = list(range(1, 32))

    # Estrutura Canônica Obrigatória:
    # Grupo A: 01 a 15 (15 dezenas)
    # Grupo B: 16 a 31 (16 dezenas)
    GRUPO_A = list(range(1, 16))
    GRUPO_B = list(range(16, 32))

    SET_A = set(GRUPO_A)
    SET_B = set(GRUPO_B)

    # 12 Meses Oficiais do Dia de Sorte
    MESES_OFICIAIS = [
        "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
        "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"
    ]

    # Distribuições Teóricas Hipergeométricas Exatas em C(31, 7) = 2.629.575
    # P(K_A = k_A) = [C(15, k_A) * C(16, 7 - k_A)] / C(31, 7)
    COMBINACOES_TOTAIS = 2629575
    DISTRIBUICOES_TEORICAS = {
        (3, 4): {"combinacoes": 828100, "probabilidade": 828100 / 2629575, "rotulo": "3 + 4"},
        (4, 3): {"combinacoes": 764400, "probabilidade": 764400 / 2629575, "rotulo": "4 + 3"},
        (2, 5): {"combinacoes": 458640, "probabilidade": 458640 / 2629575, "rotulo": "2 + 5"},
        (5, 2): {"combinacoes": 360360, "probabilidade": 360360 / 2629575, "rotulo": "5 + 2"},
        (1, 6): {"combinacoes": 120120, "probabilidade": 120120 / 2629575, "rotulo": "1 + 6"},
        (6, 1): {"combinacoes": 80080, "probabilidade": 80080 / 2629575, "rotulo": "6 + 1"},
        (0, 7): {"combinacoes": 11440, "probabilidade": 11440 / 2629575, "rotulo": "0 + 7"},
        (7, 0): {"combinacoes": 6435, "probabilidade": 6435 / 2629575, "rotulo": "7 + 0"},
    }

    # Modos de Operação Suportados (Seção 18)
    MODOS_VALIDOS = {
        "equilibrada": "1 — EQUILIBRADO (Recomendado)",
        "frequencia_historica": "2 — FREQUÊNCIA HISTÓRICA",
        "frequencia_recente": "3 — FREQUÊNCIA RECENTE",
        "atrasos_recuperacoes": "4 — ATRASOS E RECUPERAÇÕES",
        "pares_trios": "5 — PARES E TRIOS",
        "coocorrencia_lift_zscore": "6 — COOCORRÊNCIA / LIFT / Z-SCORE",
        "auto_pesos": "7 — AUTO PESOS"
    }

    def __init__(
        self,
        historico: Optional[List[List[int]]] = None,
        historico_meses: Optional[List[str]] = None,
        limite_historico: Optional[int] = 30,
        estrategia: str = "equilibrada",
        pool: Optional[List[int]] = None
    ):
        # 1. Validação da Estratégia
        estrategia_norm = str(estrategia).lower().strip().replace("-", "_").replace(" ", "_")
        if estrategia_norm not in self.MODOS_VALIDOS:
            for k in self.MODOS_VALIDOS:
                if k in estrategia_norm:
                    estrategia_norm = k
                    break
            else:
                estrategia_norm = "equilibrada"
        self.estrategia = estrategia_norm

        # 2. Configuração do Pool de Números (Automático ou Personalizado)
        if pool and len(pool) >= 7:
            valid_nums = sorted(list(set(int(x) for x in pool if 1 <= int(x) <= 31)))
            if len(valid_nums) >= 7:
                self.pool = valid_nums
                self.is_custom_pool = True
            else:
                self.pool = list(self.TODOS_NUMEROS)
                self.is_custom_pool = False
        else:
            self.pool = list(self.TODOS_NUMEROS)
            self.is_custom_pool = False

        self.set_pool = set(self.pool)
        self.pool_A = [n for n in self.pool if n in self.SET_A]
        self.pool_B = [n for n in self.pool if n in self.SET_B]

        # 3. Carregamento e Filtro do Histórico Oficial
        self.raw_historico, self.raw_historico_meses = self._carregar_historico_oficial(
            historico, historico_meses
        )

        # 4. Ajuste da Janela de Análise Histórica (Mínimo: 3, Máximo: 100)
        limite = 30
        if limite_historico is not None:
            try:
                limite = int(limite_historico)
            except Exception:
                limite = 30
        limite = max(3, min(100, limite))
        self.limite_historico = limite

        if len(self.raw_historico) > limite:
            self.historico = self.raw_historico[-limite:]
            self.historico_meses = self.raw_historico_meses[-limite:]
        else:
            self.historico = self.raw_historico
            self.historico_meses = self.raw_historico_meses

        self.total_analisado = len(self.historico)

        # 5. Cálculo Estatístico Multidimensional Rigoroso
        self.stats = self._calcular_estatisticas()

        # 6. Auto-Pesos Adaptativos com Regularização Bayesiana
        self.pesos = self._calcular_auto_pesos()

    @staticmethod
    def formatar_dezena(n: int) -> str:
        return f"{int(n):02d}"

    @classmethod
    def normalizar_nome_mes(cls, raw_mes: str) -> str:
        if not raw_mes:
            return cls.MESES_OFICIAIS[0]
        cleaned = str(raw_mes).strip().capitalize()
        mapping = {
            "Janeiro": "Janeiro", "Fevereiro": "Fevereiro", "Marco": "Março", "Março": "Março",
            "Abril": "Abril", "Maio": "Maio", "Junho": "Junho", "Julho": "Julho",
            "Agosto": "Agosto", "Setembro": "Setembro", "Outubro": "Outubro",
            "Novembro": "Novembro", "Dezembro": "Dezembro"
        }
        for k, v in mapping.items():
            if k.lower() in cleaned.lower():
                return v
        return cls.MESES_OFICIAIS[0]

    def _carregar_historico_oficial(
        self,
        historico_externo: Optional[List[List[int]]],
        historico_meses_externo: Optional[List[str]]
    ) -> Tuple[List[List[int]], List[str]]:
        if historico_externo and len(historico_externo) >= 3:
            norm_draws = []
            norm_meses = []
            for idx, draw in enumerate(historico_externo):
                valid = sorted(list(set(int(x) for x in draw if 1 <= int(x) <= 31)))
                if len(valid) == 7:
                    norm_draws.append(valid)
                    if historico_meses_externo and idx < len(historico_meses_externo):
                        norm_meses.append(self.normalizar_nome_mes(historico_meses_externo[idx]))
                    else:
                        norm_meses.append(self.MESES_OFICIAIS[idx % 12])
            if len(norm_draws) >= 3:
                return norm_draws, norm_meses

        base_dir = os.path.dirname(os.path.abspath(__file__))
        cache_dir = os.path.join(base_dir, "data")
        os.makedirs(cache_dir, exist_ok=True)
        cache_file = os.path.join(cache_dir, "diadesorte.json")

        data = None
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                pass

        if not data:
            url = "https://raw.githubusercontent.com/guilhermeasn/loteria.json/master/data/diadesorte.json"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    with open(cache_file, "w", encoding="utf-8") as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
            except Exception as e:
                print(f"[MotorDiaDeSorteB2B] Aviso ao baixar dados: {e}")

        if data:
            sorted_keys = sorted(data.keys(), key=lambda x: int(x))
            norm_draws = []
            norm_meses = []
            for k in sorted_keys:
                item = data[k]
                draw = sorted([int(x) for x in item[:7] if 1 <= int(x) <= 31])
                if len(draw) == 7:
                    norm_draws.append(draw)
                    mes_raw = item[7] if len(item) >= 8 else ""
                    norm_meses.append(self.normalizar_nome_mes(mes_raw))
            if len(norm_draws) >= 3:
                return norm_draws, norm_meses

        fallback_draws = [
            [1, 5, 9, 17, 21, 25, 30],
            [2, 7, 12, 16, 20, 24, 29],
            [3, 8, 14, 18, 22, 27, 31],
            [4, 10, 15, 19, 23, 26, 28],
            [2, 6, 11, 16, 22, 25, 30]
        ]
        fallback_meses = ["Janeiro", "Maio", "Julho", "Setembro", "Dezembro"]
        return fallback_draws, fallback_meses

    def _calcular_estatisticas(self) -> Dict[str, Any]:
        T = self.total_analisado

        # 1. Classificação do Nível de Evidência Estatística (Seção 20)
        if T < 10:
            nivel_evidencia = "AMOSTRA INSUFICIENTE"
            confianca_pct = round((T / 100.0) * 40, 1)
        elif T < 30:
            nivel_evidencia = "BAIXA EVIDÊNCIA"
            confianca_pct = round(40 + ((T - 10) / 20.0) * 25, 1)
        elif T < 60:
            nivel_evidencia = "EVIDÊNCIA MODERADA"
            confianca_pct = round(65 + ((T - 30) / 30.0) * 20, 1)
        else:
            nivel_evidencia = "ALTA EVIDÊNCIA"
            confianca_pct = round(85 + ((T - 60) / 40.0) * 15, 1)

        p_teorica_numero = self.TAMANHO_JOGO / self.TOTAL_NUMEROS  # 7 / 31 ~= 0.225806
        esperanca_freq = T * p_teorica_numero
        var_freq = T * p_teorica_numero * (1.0 - p_teorica_numero)
        sigma_freq = math.sqrt(var_freq) if var_freq > 0 else 1.0

        janela_recente = max(3, min(10, max(3, T // 3)))
        historico_recente = self.historico[-janela_recente:]

        freq_abs = collections.Counter()
        freq_rec = collections.Counter()
        ultimo_concurso: Dict[int, int] = {}
        intervalos_numero: Dict[int, List[int]] = collections.defaultdict(list)
        consecutivos_anteriores: Dict[int, int] = collections.defaultdict(int)

        for idx, draw in enumerate(self.historico):
            set_draw = set(draw)
            for n in self.pool:
                if n in set_draw:
                    freq_abs[n] += 1
                    if n in ultimo_concurso:
                        intervalos_numero[n].append(idx - ultimo_concurso[n])
                    ultimo_concurso[n] = idx
                    if idx > 0 and n in set(self.historico[idx - 1]):
                        consecutivos_anteriores[n] += 1

        for draw in historico_recente:
            for n in draw:
                if n in self.set_pool:
                    freq_rec[n] += 1

        num_stats: Dict[int, Dict[str, Any]] = {}
        for n in self.pool:
            f_abs = freq_abs[n]
            p_obs = f_abs / T if T > 0 else 0.0
            z_score = (f_abs - esperanca_freq) / sigma_freq if sigma_freq > 0 else 0.0
            desvio_relativo = ((f_abs - esperanca_freq) / esperanca_freq) * 100.0 if esperanca_freq > 0 else 0.0

            f_rec = freq_rec[n]
            p_rec = f_rec / janela_recente if janela_recente > 0 else 0.0
            razao_momento = (p_rec + 0.05) / (p_obs + 0.05)

            atraso_atual = (T - 1 - ultimo_concurso[n]) if n in ultimo_concurso else T
            historico_gaps = intervalos_numero[n]
            atraso_medio = statistics.mean(historico_gaps) if historico_gaps else (self.TOTAL_NUMEROS / self.TAMANHO_JOGO)
            maior_atraso = max(historico_gaps) if historico_gaps else atraso_atual

            recuperacoes = consecutivos_anteriores[n]
            dist_centroide = abs(n - 16.0)

            num_stats[n] = {
                "numero": n,
                "grupo": "A" if n in self.SET_A else "B",
                "freq_abs": f_abs,
                "freq_rel": round(p_obs, 4),
                "freq_rec": f_rec,
                "freq_rec_rel": round(p_rec, 4),
                "z_score": round(z_score, 3),
                "desvio_rel_pct": round(desvio_relativo, 1),
                "razao_momento": round(razao_momento, 3),
                "atraso_atual": atraso_atual,
                "atraso_medio": round(atraso_medio, 1),
                "maior_atraso": maior_atraso,
                "recuperacoes": recuperacoes,
                "dist_centroide": dist_centroide
            }

        # 2. Análise das Distribuições Grupo A x Grupo B (Seções 4 e 5)
        contagem_modelos = collections.Counter()
        for draw in self.historico:
            qtd_A = sum(1 for x in draw if x in self.SET_A)
            qtd_B = sum(1 for x in draw if x in self.SET_B)
            contagem_modelos[(qtd_A, qtd_B)] += 1

        modelos_ordenados = []
        for mod, dados_teo in self.DISTRIBUICOES_TEORICAS.items():
            obs = contagem_modelos[mod]
            pct_obs = (obs / T) * 100.0 if T > 0 else 0.0
            alpha = min(1.0, T / 60.0)
            peso_ajustado = (alpha * (obs / T)) + ((1.0 - alpha) * dados_teo["probabilidade"])
            modelos_ordenados.append({
                "modelo": mod,
                "rotulo": dados_teo["rotulo"],
                "ocorrencias": obs,
                "pct_observada": round(pct_obs, 1),
                "pct_teorica": round(dados_teo["probabilidade"] * 100.0, 1),
                "peso_ajustado": peso_ajustado
            })

        # Ordenar decrescente por evidência ajustada
        modelos_ordenados.sort(key=lambda x: (x["ocorrencias"], x["peso_ajustado"]), reverse=True)

        # 3. Matriz de Coocorrência, Lift e Z-Score de Pares
        coocorrencias_pares = collections.Counter()
        for draw in self.historico:
            for a, b in itertools.combinations(draw, 2):
                if a in self.set_pool and b in self.set_pool:
                    pair = (min(a, b), max(a, b))
                    coocorrencias_pares[pair] += 1

        p_par_teorica = (7.0 * 6.0) / (31.0 * 30.0)
        esperanca_par = T * p_par_teorica
        var_par = T * p_par_teorica * (1.0 - p_par_teorica)
        sigma_par = math.sqrt(var_par) if var_par > 0 else 1.0

        pares_stats: Dict[Tuple[int, int], Dict[str, Any]] = {}
        for a, b in itertools.combinations(self.pool, 2):
            pair = (min(a, b), max(a, b))
            obs = coocorrencias_pares[pair]
            f_a = freq_abs[a]
            f_b = freq_abs[b]
            lift = (obs * T) / (f_a * f_b) if (f_a > 0 and f_b > 0) else 0.0
            z_par = (obs - esperanca_par) / sigma_par if sigma_par > 0 else 0.0
            pares_stats[pair] = {
                "par": pair,
                "coocorrencias": obs,
                "lift": round(lift, 3),
                "z_score": round(z_par, 3)
            }

        # 4. Trios de Maior Relevância
        coocorrencias_trios = collections.Counter()
        for draw in self.historico:
            for trio in itertools.combinations(draw, 3):
                if all(x in self.set_pool for x in trio):
                    coocorrencias_trios[tuple(sorted(trio))] += 1

        # 5. Análise dos Meses da Sorte (Seções 15 e 16)
        freq_meses = collections.Counter(self.historico_meses)
        ultimo_mes_idx: Dict[str, int] = {}
        for idx, m in enumerate(self.historico_meses):
            ultimo_mes_idx[m] = idx

        freq_rec_meses = collections.Counter(self.historico_meses[-janela_recente:])

        meses_stats = []
        for m in self.MESES_OFICIAIS:
            f_m = freq_meses[m]
            pct_m = (f_m / T) * 100.0 if T > 0 else 0.0
            f_rec_m = freq_rec_meses[m]
            atraso_m = (T - 1 - ultimo_mes_idx[m]) if m in ultimo_mes_idx else T
            score_mes = (f_m * 1.5) + (f_rec_m * 2.0) + (1.0 / max(1, atraso_m))
            meses_stats.append({
                "mes": m,
                "freq_abs": f_m,
                "freq_rel_pct": round(pct_m, 1),
                "freq_rec": f_rec_m,
                "atraso": atraso_m,
                "score": round(score_mes, 2)
            })
        meses_stats.sort(key=lambda x: (x["score"], x["freq_abs"]), reverse=True)

        return {
            "total_concursos": T,
            "janela_recente": janela_recente,
            "nivel_evidencia": nivel_evidencia,
            "confianca_pct": confianca_pct,
            "numeros": num_stats,
            "modelos_ordenados": modelos_ordenados,
            "pares": pares_stats,
            "trios": coocorrencias_trios,
            "meses": meses_stats,
            "esperanca_freq": esperanca_freq,
            "esperanca_par": esperanca_par
        }

    def _calcular_auto_pesos(self) -> Dict[str, float]:
        T = self.total_analisado
        estrat = self.estrategia

        pesos = {
            "freq_historica": 1.0,
            "freq_recente": 1.2,
            "atraso": 0.8,
            "recuperacao": 0.7,
            "pares": 1.1,
            "trios": 0.9,
            "coocorrencia_lift": 1.3,
            "centroide": 1.0,
            "dispersao": 0.9
        }

        if estrat == "frequencia_historica":
            pesos["freq_historica"] = 3.0
            pesos["freq_recente"] = 0.5
            pesos["atraso"] = 0.3
            pesos["coocorrencia_lift"] = 0.6
        elif estrat == "frequencia_recente":
            pesos["freq_recente"] = 3.5
            pesos["freq_historica"] = 0.6
            pesos["recuperacao"] = 1.8
            pesos["atraso"] = 0.5
        elif estrat == "atrasos_recuperacoes":
            pesos["atraso"] = 3.2
            pesos["recuperacao"] = 2.4
            pesos["freq_historica"] = 0.4
            pesos["freq_recente"] = 0.5
        elif estrat == "pares_trios":
            pesos["pares"] = 3.0
            pesos["trios"] = 2.5
            pesos["coocorrencia_lift"] = 2.0
            pesos["freq_historica"] = 0.7
        elif estrat == "coocorrencia_lift_zscore":
            pesos["coocorrencia_lift"] = 3.5
            pesos["pares"] = 2.0
            pesos["freq_historica"] = 0.8
            pesos["atraso"] = 0.4
        elif estrat == "auto_pesos":
            fator_amostral = min(1.0, T / 60.0)
            pesos["coocorrencia_lift"] = 1.0 + (1.5 * fator_amostral)
            pesos["freq_recente"] = 1.0 + (1.2 * (1.0 - fator_amostral * 0.3))
            pesos["pares"] = 1.0 + (1.0 * fator_amostral)
            pesos["freq_historica"] = 1.0 + (0.8 * fator_amostral)
            pesos["atraso"] = 0.7 + (0.4 * fator_amostral)

        soma = sum(pesos.values())
        return {k: v / soma for k, v in pesos.items()}

    def _pontuar_subconjunto(self, sub: Tuple[int, ...]) -> float:
        score = 0.0
        w = self.pesos
        n_stats = self.stats["numeros"]

        for n in sub:
            st = n_stats[n]
            score += w["freq_historica"] * (st["z_score"] * 2.0 + 10.0)
            score += w["freq_recente"] * (st["razao_momento"] * 8.0)
            gap_ratio = st["atraso_atual"] / max(0.5, st["atraso_medio"])
            if 0.6 <= gap_ratio <= 1.8:
                score += w["atraso"] * 6.0
            else:
                score -= w["atraso"] * 2.0
            score += w["recuperacao"] * (st["recuperacoes"] * 2.0)

        pares_st = self.stats["pares"]
        for p in itertools.combinations(sub, 2):
            par_key = (min(p), max(p))
            if par_key in pares_st:
                p_data = pares_st[par_key]
                score += w["pares"] * (p_data["coocorrencias"] * 1.5)
                score += w["coocorrencia_lift"] * (max(-2.0, min(3.0, p_data["lift"] - 1.0)) * 4.0)

        return score

    def _pontuar_jogo_completo(self, jogo: List[int]) -> float:
        score = 0.0
        w = self.pesos
        pares_st = self.stats["pares"]
        trios_st = self.stats["trios"]
        n_stats = self.stats["numeros"]

        for n in jogo:
            st = n_stats[n]
            score += w["freq_historica"] * (st["z_score"] * 1.5 + 8.0)
            score += w["freq_recente"] * (st["razao_momento"] * 6.0)
            score += w["recuperacao"] * (st["recuperacoes"] * 1.5)

        for p in itertools.combinations(jogo, 2):
            par_key = (min(p), max(p))
            if par_key in pares_st:
                p_data = pares_st[par_key]
                score += w["pares"] * (p_data["coocorrencias"] * 1.2)
                score += w["coocorrencia_lift"] * ((p_data["lift"] - 1.0) * 3.5)

        for t in itertools.combinations(jogo, 3):
            t_key = tuple(sorted(t))
            if t_key in trios_st:
                score += w["trios"] * (trios_st[t_key] * 2.5)

        centroide_jogo = sum(jogo) / 7.0
        dist_centroide = abs(centroide_jogo - 16.0)
        if dist_centroide <= 2.5:
            score += w["centroide"] * 8.0
        elif dist_centroide <= 4.0:
            score += w["centroide"] * 4.0
        else:
            score -= w["centroide"] * (dist_centroide * 2.0)

        f1 = sum(1 for x in jogo if 1 <= x <= 10)
        f2 = sum(1 for x in jogo if 11 <= x <= 20)
        f3 = sum(1 for x in jogo if 21 <= x <= 31)
        if f1 > 0 and f2 > 0 and f3 > 0:
            score += w["dispersao"] * 6.0
        if max(f1, f2, f3) >= 5:
            score -= w["dispersao"] * 8.0

        return round(score, 2)

    @staticmethod
    def validar_sequencia_consecutivos(jogo: List[int]) -> bool:
        sorted_game = sorted(jogo)
        consec = 1
        max_consec = 1
        for i in range(1, len(sorted_game)):
            if sorted_game[i] == sorted_game[i - 1] + 1:
                consec += 1
                if consec > max_consec:
                    max_consec = consec
            else:
                consec = 1
        return max_consec <= 3

    def auditar_jogo(self, jogo: List[int], mes: str, modelo: Tuple[int, int]) -> Tuple[bool, str]:
        if len(jogo) != 7:
            return False, "Jogo não possui 7 números"
        if not all(1 <= x <= 31 for x in jogo):
            return False, "Números fora do intervalo 01..31"
        if len(set(jogo)) != 7:
            return False, "Existem números duplicados no jogo"
        if not all(x in self.set_pool for x in jogo):
            return False, "Contém números fora do pool escolhido"
        kA = sum(1 for x in jogo if x in self.SET_A)
        kB = sum(1 for x in jogo if x in self.SET_B)
        if (kA, kB) != modelo:
            return False, f"Distribuição ({kA}, {kB}) difere do modelo {modelo}"
        if not self.validar_sequencia_consecutivos(jogo):
            return False, "Possui mais de 3 números consecutivos"
        centroide = sum(jogo) / 7.0
        if centroide < 8.0 or centroide > 24.0:
            return False, f"Centroide aberrante ({centroide:.1f})"
        if mes not in self.MESES_OFICIAIS:
            return False, f"Mês inválido: {mes}"
        return True, "Aprovado com rigor matemático"

    def gerar_carteira(self, quantidade_jogos: int = 10) -> Dict[str, Any]:
        Q = max(1, int(quantidade_jogos))
        modelos_ord = self.stats["modelos_ordenados"]

        modelos_viaveis = []
        for m_info in modelos_ord:
            kA, kB = m_info["modelo"]
            if len(self.pool_A) >= kA and len(self.pool_B) >= kB:
                modelos_viaveis.append(m_info)

        if not modelos_viaveis:
            modelos_viaveis = [m_info for m_info in modelos_ord if m_info["modelo"] in [(3, 4), (4, 3)]]

        soma_pesos = sum(m["peso_ajustado"] for m in modelos_viaveis[:4])
        cotas_modelos: Dict[Tuple[int, int], int] = {}
        jogos_restantes = Q

        for m_info in modelos_viaveis[:4]:
            mod = m_info["modelo"]
            cota = max(1, int(round(Q * (m_info["peso_ajustado"] / soma_pesos))))
            if cota > jogos_restantes:
                cota = jogos_restantes
            cotas_modelos[mod] = cota
            jogos_restantes -= cota

        if jogos_restantes > 0:
            top_mod = modelos_viaveis[0]["modelo"]
            cotas_modelos[top_mod] = cotas_modelos.get(top_mod, 0) + jogos_restantes

        jogos_gerados_candidatos: List[Dict[str, Any]] = []

        for mod, cota in cotas_modelos.items():
            if cota <= 0:
                continue
            kA, kB = mod

            subs_A = list(itertools.combinations(self.pool_A, kA))
            scored_A = [(sub, self._pontuar_subconjunto(sub)) for sub in subs_A]
            scored_A.sort(key=lambda x: x[1], reverse=True)
            lim_A = min(len(scored_A), max(15, min(60, cota * 2)))
            top_A = [sub for sub, _ in scored_A[:lim_A]]

            subs_B = list(itertools.combinations(self.pool_B, kB))
            scored_B = [(sub, self._pontuar_subconjunto(sub)) for sub in subs_B]
            scored_B.sort(key=lambda x: x[1], reverse=True)
            lim_B = min(len(scored_B), max(15, min(80, cota * 2)))
            top_B = [sub for sub, _ in scored_B[:lim_B]]

            candidatos_modelo = []
            for subA in top_A:
                for subB in top_B:
                    jogo = sorted(list(subA) + list(subB))
                    if self.validar_sequencia_consecutivos(jogo):
                        score = self._pontuar_jogo_completo(jogo)
                        candidatos_modelo.append({
                            "jogo": jogo,
                            "modelo": mod,
                            "rotulo_modelo": f"{kA} + {kB}",
                            "score": score
                        })

            candidatos_modelo.sort(key=lambda x: x["score"], reverse=True)
            jogos_gerados_candidatos.extend(candidatos_modelo[:max(30, cota * 6)])

        carteira_final: List[Dict[str, Any]] = []
        numeros_usados = collections.Counter()
        meses_disponiveis = [m["mes"] for m in self.stats["meses"]]

        candidatos_por_modelo: Dict[Tuple[int, int], List[Dict[str, Any]]] = collections.defaultdict(list)
        for cand in jogos_gerados_candidatos:
            candidatos_por_modelo[cand["modelo"]].append(cand)

        overlap_limit = 4 if Q <= 100 else (5 if Q <= 300 else 6)
        jogos_set = set()

        jogo_idx = 1
        for mod, cota in cotas_modelos.items():
            pool_mod = candidatos_por_modelo.get(mod, [])
            jogos_selecionados_mod = 0

            for cand in pool_mod:
                if jogos_selecionados_mod >= cota:
                    break

                g = cand["jogo"]
                tup = tuple(g)
                if tup in jogos_set:
                    continue

                if overlap_limit < 6 and carteira_final and len(carteira_final) < 300:
                    sobreposicao_max = 0
                    for item in carteira_final[-100:]:
                        overlap = len(set(g).intersection(set(item["jogo"])))
                        if overlap > sobreposicao_max:
                            sobreposicao_max = overlap
                        if sobreposicao_max > overlap_limit:
                            break
                    if sobreposicao_max > overlap_limit:
                        continue

                mes_escolhido = meses_disponiveis[(jogo_idx - 1) % len(meses_disponiveis)]
                aprovado, motivo = self.auditar_jogo(g, mes_escolhido, mod)
                if not aprovado:
                    continue

                jogos_set.add(tup)
                carteira_final.append({
                    "id": f"JOGO {jogo_idx:02d}",
                    "jogo": g,
                    "dezenas_fmt": " ".join(self.formatar_dezena(x) for x in g),
                    "mes": mes_escolhido,
                    "modelo": cand["rotulo_modelo"],
                    "score": cand["score"]
                })

                for x in g:
                    numeros_usados[x] += 1

                jogos_selecionados_mod += 1
                jogo_idx += 1

        if len(carteira_final) < Q:
            import random
            tentativas_extra = 0
            while len(carteira_final) < Q and tentativas_extra < 50000:
                tentativas_extra += 1
                r = random.random()
                mod = (3, 4) if r < 0.35 else ((4, 3) if r < 0.67 else ((2, 5) if r < 0.85 else (5, 2)))
                kA, kB = mod
                subA = random.sample(self.pool_A, kA)
                subB = random.sample(self.pool_B, kB)
                g = sorted(subA + subB)
                tup = tuple(g)
                if tup in jogos_set:
                    continue
                if not self.validar_sequencia_consecutivos(g):
                    continue
                c_val = sum(g) / 7.0
                if c_val < 9.0 or c_val > 23.0:
                    continue
                mes_escolhido = meses_disponiveis[(jogo_idx - 1) % len(meses_disponiveis)]
                jogos_set.add(tup)
                carteira_final.append({
                    "id": f"JOGO {jogo_idx:02d}",
                    "jogo": g,
                    "dezenas_fmt": " ".join(self.formatar_dezena(x) for x in g),
                    "mes": mes_escolhido,
                    "modelo": f"{kA} + {kB}",
                    "score": self._pontuar_jogo_completo(g)
                })
                jogo_idx += 1

        resumo_modelos = collections.Counter(j["modelo"] for j in carteira_final)
        meses_usados = list(dict.fromkeys(j["mes"] for j in carteira_final))

        return {
            "sucesso": True,
            "total_jogos": len(carteira_final),
            "jogos": carteira_final,
            "distribuicao_modelos": dict(resumo_modelos),
            "meses_utilizados": meses_usados,
            "estrategia_utilizada": self.MODOS_VALIDOS[self.estrategia],
            "concursos_analisados": self.total_analisado,
            "relatorio_pre_geracao": self.gerar_relatorio_pre_geracao(),
            "saida_oficial_texto": self.formatar_saida_oficial(carteira_final)
        }

    def gerar_relatorio_pre_geracao(self) -> Dict[str, Any]:
        st = self.stats
        num_sorted = sorted(st["numeros"].values(), key=lambda x: (x["z_score"], x["freq_rec"]), reverse=True)

        maiores_scores = [f"{self.formatar_dezena(x['numero'])} (Z={x['z_score']:+.2f})" for x in num_sorted[:5]]
        menores_scores = [f"{self.formatar_dezena(x['numero'])} (Z={x['z_score']:+.2f})" for x in num_sorted[-5:]]

        pares_sorted = sorted(st["pares"].values(), key=lambda x: (x["coocorrencias"], x["lift"]), reverse=True)
        top_pares = [
            f"{self.formatar_dezena(p['par'][0])}–{self.formatar_dezena(p['par'][1])} (N={p['coocorrencias']}, Lift={p['lift']})"
            for p in pares_sorted[:4]
        ]

        trios_sorted = st["trios"].most_common(3)
        top_trios = [
            f"{self.formatar_dezena(t[0][0])}–{self.formatar_dezena(t[0][1])}–{self.formatar_dezena(t[0][2])} (N={t[1]})"
            for t in trios_sorted
        ]

        dist_modelos = {
            m["rotulo"]: f"{m['pct_observada']}% (Teórica: {m['pct_teorica']}%)"
            for m in st["modelos_ordenados"][:4]
        }

        top_meses = [f"{m['mes']} ({m['freq_rel_pct']}%)" for m in st["meses"][:3]]

        return {
            "concursos_analisados": self.total_analisado,
            "numeros_analisados": "01–31 (Pool Oficial)" if not self.is_custom_pool else f"Pool Personalizado ({len(self.pool)} números)",
            "estrategia": self.MODOS_VALIDOS[self.estrategia],
            "distribuicoes_identificadas": dist_modelos,
            "numeros_com_maior_score": maiores_scores,
            "numeros_com_menor_score": menores_scores,
            "pares_maior_relevancia": top_pares,
            "trios_maior_relevancia": top_trios,
            "meses_melhor_classificados": top_meses,
            "nivel_confianca_estatistica": f"{st['nivel_evidencia']} ({st['confianca_pct']}%)",
            "advertencia_matematica": (
                "Resultados passados não garantem resultados futuros. A frequência histórica e os atrasos "
                "servem exclusivamente para organizar, filtrar e diversificar as combinações combinatórias, "
                "não para prever deterministicamente o próximo concurso."
            )
        }

    def formatar_saida_oficial(self, carteira: List[Dict[str, Any]]) -> str:
        linhas = []
        linhas.append("=" * 70)
        linhas.append("🎯 B2B LOTERIAS — NOVO MOTOR DIA DE SORTE")
        linhas.append("MOTOR MATEMÁTICO, ESTATÍSTICO E PROBABILÍSTICO")
        linhas.append("=" * 70)
        linhas.append("")

        rel = self.gerar_relatorio_pre_geracao()
        linhas.append("--- RELATÓRIO PRÉ-GERAÇÃO ---")
        linhas.append(f"Concursos analisados: {rel['concursos_analisados']}")
        linhas.append(f"Números analisados: {rel['numeros_analisados']}")
        linhas.append(f"Estratégia: {rel['estrategia']}")
        linhas.append("Distribuições identificadas:")
        for mod, val in rel["distribuicoes_identificadas"].items():
            linhas.append(f"  • {mod} -> {val}")
        linhas.append(f"Números com maior score: {', '.join(rel['numeros_com_maior_score'])}")
        linhas.append(f"Números com menor score: {', '.join(rel['numeros_com_menor_score'])}")
        linhas.append(f"Pares de maior relevância: {', '.join(rel['pares_maior_relevancia'])}")
        linhas.append(f"Trios de maior relevância: {', '.join(rel['trios_maior_relevancia']) if rel['trios_maior_relevancia'] else 'Sem trios com repetição significativa'}")
        linhas.append(f"Mês(es) melhor classificado(s): {', '.join(rel['meses_melhor_classificados'])}")
        linhas.append(f"Nível de confiança estatística: {rel['nivel_confianca_estatistica']}")
        linhas.append(f"Aviso de Honestidade: {rel['advertencia_matematica']}")
        linhas.append("")
        linhas.append("=" * 70)
        linhas.append("--- JOGOS GERADOS ---")
        linhas.append("=" * 70)
        linhas.append("")

        for j in carteira:
            linhas.append(f"{j['id']}")
            linhas.append(f"Números: {j['dezenas_fmt']}")
            linhas.append(f"Mês: {j['mes']}")
            linhas.append(f"Modelo: {j['modelo']}")
            linhas.append(f"Score: {j['score']}")
            linhas.append("")

        linhas.append("=" * 70)
        linhas.append("--- RESUMO FINAL ---")
        linhas.append("=" * 70)
        linhas.append(f"TOTAL DE JOGOS: {len(carteira)}")
        linhas.append("DISTRIBUIÇÃO DOS MODELOS:")
        resumo_mod = collections.Counter(j["modelo"] for j in carteira)
        for mod, qtd in resumo_mod.items():
            linhas.append(f"  • {mod} = {qtd} jogos")
        meses_usados = list(dict.fromkeys(j["mes"] for j in carteira))
        linhas.append(f"MESES UTILIZADOS: {', '.join(meses_usados)}")
        linhas.append(f"CRITÉRIO: {self.MODOS_VALIDOS[self.estrategia]}")
        linhas.append(f"CONCURSOS ANALISADOS: {self.total_analisado}")
        linhas.append("=" * 70)

        return "\n".join(linhas)
