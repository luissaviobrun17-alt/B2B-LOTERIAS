"""
MOTOR +MILIONÁRIA — B2B LOTERIAS (NÚCLEO MATEMÁTICO, FÍSICO E ESTATÍSTICO)
==========================================================================
Desenvolvido sob a ótica de Matemático e Físico de Renome Internacional.
Foco absoluto em: RIGOR CIENTÍFICO, HONESTIDADE ESTATÍSTICA, COBERTURA,
DIVERSIFICAÇÃO DE CARTEIRA, MODELO DE TREVOS INDEPENDENTE E TRANSPARÊNCIA.

Regras Oficiais:
- Universo Principal: 50 dezenas (01 a 50). Cada aposta simples utiliza 6 dezenas.
  Espaço Combinatório: C(50, 6) = 15.890.700 combinações.
- Universo de Trevos: 6 trevos (1 a 6). Cada aposta simples utiliza 2 trevos.
  Espaço Combinatório: C(6, 2) = 15 pares possíveis de trevos.
- Espaço Total de Apostas Elementares: 15.890.700 * 15 = 238.360.500.

Princípio Fundamental:
NÃO PROMETE PREVISÃO DETERMINÍSTICA NEM GARANTIA DE PREMIAÇÃO.
Organiza a informação histórica, analisa o espaço combinatório, seleciona um pool
de qualidade, constrói carteiras com máxima diversificação e cobertura, e reporta
os limites estatísticos com honestidade científica incondicional.
"""

import math
import random
import itertools
import collections
import statistics
import json
import os
from typing import List, Dict, Tuple, Optional, Any, Set


class MotorMilionariaB2B:
    """Núcleo Matemático e Estatístico Avançado do Motor +Milionária."""

    # 50 Números Principais
    TODOS_NUMEROS = list(range(1, 51))
    TOTAL_UNIVERSO = 50
    TAMANHO_JOGO = 6

    # 6 Trevos
    TODOS_TREVOS = list(range(1, 7))
    QTD_TREVOS = 2
    PARES_TREVOS_POSSIVEIS = list(itertools.combinations(TODOS_TREVOS, 2))  # 15 pares

    # 5 Faixas de 10 Números
    FAIXAS = {
        1: list(range(1, 11)),   # 01 a 10
        2: list(range(11, 21)),  # 11 a 20
        3: list(range(21, 31)),  # 21 a 30
        4: list(range(31, 41)),  # 31 a 40
        5: list(range(41, 51))   # 41 a 50
    }

    # Centróide Teórico
    CENTRO_INTERVALO = 25.5
    SOMA_ESPERADA_6 = 6 * 25.5  # 153.0

    DECLARACAO_HONESTIDADE = (
        "Este motor utiliza modelos matemáticos, estatísticos e combinatórios para análise "
        "e otimização de carteiras. Os resultados históricos não constituem garantia de resultados futuros. "
        "Quando não houver evidência estatística suficiente, o sistema declara explicitamente essa limitação."
    )

    def __init__(
        self,
        historico: Optional[List[List[int]]] = None,
        historico_trevos: Optional[List[List[int]]] = None,
        limite_historico: Optional[int] = None,
        pool_tamanho: int = 50,
        estrategia: str = "equilibrada",
        janela_recente: int = 10,
        sniper: str = "desativado",
        bloquear_acima_3_consecutivos: bool = True,
        estrategia_trevo: str = "cobertura_equilibrada",
        trevos_fixos: Optional[List[int]] = None
    ):
        self.bloquear_consecutivos = bloquear_acima_3_consecutivos
        self.estrategia = estrategia or "equilibrada"
        self.janela_recente = janela_recente if janela_recente in [5, 10, 15, 20] else 10
        self.sniper = sniper or "desativado"
        self.estrategia_trevo = estrategia_trevo or "cobertura_equilibrada"
        self.trevos_fixos = trevos_fixos

        # Carregar histórico se não fornecido
        if historico is None or historico_trevos is None:
            hist_num, hist_tr = self._carregar_historico_oficial()
            self.historico = hist_num if historico is None else historico
            self.historico_trevos = hist_tr if historico_trevos is None else historico_trevos
        else:
            self.historico = historico
            self.historico_trevos = historico_trevos

        if limite_historico and limite_historico > 0 and len(self.historico) > limite_historico:
            self.historico = self.historico[-limite_historico:]
            self.historico_trevos = self.historico_trevos[-limite_historico:]

        self.total_concursos = len(self.historico)
        self.pool_tamanho = max(20, min(50, int(pool_tamanho)))

        self.stats_numeros = self._calcular_estatisticas_numeros()
        self.stats_trevos = self._calcular_estatisticas_trevos()
        self.matriz_coocorrencia, self.matriz_zscore = self._calcular_coocorrencia()
        self.scores_ifm = self._calcular_ifm()
        self.pool_efetivo = self._selecionar_pool()

    def _carregar_historico_oficial(self) -> Tuple[List[List[int]], List[List[int]]]:
        caminhos = [
            os.path.join(os.path.dirname(__file__), "data", "maismilionaria.json"),
            os.path.join("data", "maismilionaria.json"),
            os.path.join(os.path.expanduser("~"), "Desktop", "loterias-caixa", "data", "maismilionaria.json"),
            os.path.join(os.path.expanduser("~"), ".gemini", "antigravity", "scratch", "loteria_b2b", "data", "maismilionaria.json"),
            os.path.join(os.path.expanduser("~"), ".gemini", "antigravity", "scratch", "data", "maismilionaria.json")
        ]

        dados = None
        for p in caminhos:
            if os.path.exists(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        dados = json.load(f)
                    break
                except Exception:
                    continue

        if not dados:
            return [], []

        sorted_keys = sorted(dados.keys(), key=lambda x: int(x))
        hist_num = []
        hist_tr = []

        for k in sorted_keys:
            vals = dados[k]
            if len(vals) >= 8:
                nums = sorted([int(x) for x in vals[:6]])
                trevs = sorted([int(x) for x in vals[6:8]])
                hist_num.append(nums)
                hist_tr.append(trevs)

        return hist_num, hist_tr

    def _calcular_estatisticas_numeros(self) -> Dict[int, Dict[str, Any]]:
        stats = {}
        T = max(1, self.total_concursos)

        for n in self.TODOS_NUMEROS:
            ocorrencias_idx = [i for i, draw in enumerate(self.historico) if n in draw]
            freq_abs = len(ocorrencias_idx)
            freq_rel = freq_abs / T

            rec_5 = sum(1 for d in self.historico[-5:] if n in d) if T >= 5 else 0
            rec_10 = sum(1 for d in self.historico[-10:] if n in d) if T >= 10 else 0
            rec_15 = sum(1 for d in self.historico[-15:] if n in d) if T >= 15 else 0
            rec_20 = sum(1 for d in self.historico[-20:] if n in d) if T >= 20 else 0

            if ocorrencias_idx:
                gaps = []
                for idx in range(1, len(ocorrencias_idx)):
                    gaps.append(ocorrencias_idx[idx] - ocorrencias_idx[idx - 1] - 1)
                atraso_atual = (T - 1) - ocorrencias_idx[-1]
                gap_medio = statistics.mean(gaps) if gaps else atraso_atual
                gap_max = max(gaps) if gaps else atraso_atual
                gap_std = statistics.stdev(gaps) if len(gaps) > 1 else 1.0
            else:
                atraso_atual = T
                gap_medio = T / (6 / 50)
                gap_max = T
                gap_std = 1.0

            if atraso_atual <= gap_medio + 0.5 * gap_std:
                gap_status = "ATRASO NORMAL"
            elif atraso_atual <= gap_medio + 1.5 * gap_std:
                gap_status = "ATRASO ELEVADO"
            else:
                gap_status = "ATRASO EXTREMO"

            recuperacao_flag = False
            if len(ocorrencias_idx) >= 2:
                ultimo_gap = (ocorrencias_idx[-1] - ocorrencias_idx[-2] - 1) if len(ocorrencias_idx) >= 2 else 0
                if ultimo_gap > gap_medio and atraso_atual <= 2:
                    recuperacao_flag = True
                    gap_status = "RECUPERAÇÃO ESTATÍSTICA"

            faixa = ((n - 1) // 10) + 1
            is_par = (n % 2 == 0)
            dist_centro = abs(n - self.CENTRO_INTERVALO)

            stats[n] = {
                "numero": n,
                "freq_abs": freq_abs,
                "freq_rel": freq_rel,
                "rec_5": rec_5,
                "rec_10": rec_10,
                "rec_15": rec_15,
                "rec_20": rec_20,
                "atraso_atual": atraso_atual,
                "gap_medio": round(gap_medio, 2),
                "gap_max": gap_max,
                "gap_std": round(gap_std, 2),
                "gap_status": gap_status,
                "recuperacao_flag": recuperacao_flag,
                "faixa": faixa,
                "par": is_par,
                "dist_centro": dist_centro
            }

        return stats

    def _calcular_estatisticas_trevos(self) -> Dict[str, Any]:
        T = max(1, len(self.historico_trevos))
        stats_indiv = {}
        for t in self.TODOS_TREVOS:
            ocorr = [i for i, draw in enumerate(self.historico_trevos) if t in draw]
            freq_abs = len(ocorr)
            freq_rel = freq_abs / T
            atraso = (T - 1 - ocorr[-1]) if ocorr else T
            stats_indiv[t] = {
                "trevo": t,
                "freq_abs": freq_abs,
                "freq_rel": round(freq_rel, 4),
                "atraso": atraso,
                "rec_10": sum(1 for d in self.historico_trevos[-10:] if t in d) if T >= 10 else 0
            }

        stats_pares = {}
        for p in self.PARES_TREVOS_POSSIVEIS:
            t1, t2 = p
            ocorr_par = sum(1 for d in self.historico_trevos if t1 in d and t2 in d)
            p_t1 = stats_indiv[t1]["freq_rel"]
            p_t2 = stats_indiv[t2]["freq_rel"]
            p_conj = ocorr_par / T
            lift = (p_conj / (p_t1 * p_t2)) if (p_t1 * p_t2) > 0 else 1.0
            score_par = min(100.0, max(10.0, 50.0 + (lift - 1.0) * 30.0 + (ocorr_par / max(1, T)) * 200.0))

            stats_pares[p] = {
                "par": p,
                "ocorr_par": ocorr_par,
                "lift": round(lift, 3),
                "score_ifm": round(score_par, 1)
            }

        return {
            "individuais": stats_indiv,
            "pares": stats_pares
        }

    def _calcular_coocorrencia(self) -> Tuple[Dict[Tuple[int, int], int], Dict[Tuple[int, int], float]]:
        cooc = collections.defaultdict(int)
        T = max(1, self.total_concursos)

        for draw in self.historico:
            for a, b in itertools.combinations(sorted(draw), 2):
                cooc[(a, b)] += 1

        zscores = {}
        p_par_teorica = (self.TAMANHO_JOGO * (self.TAMANHO_JOGO - 1)) / (self.TOTAL_UNIVERSO * (self.TOTAL_UNIVERSO - 1))
        esperado_par = T * p_par_teorica
        var_par = esperado_par * (1.0 - p_par_teorica)
        std_par = math.sqrt(var_par) if var_par > 0 else 1.0

        for a, b in itertools.combinations(self.TODOS_NUMEROS, 2):
            par = (a, b)
            obs = cooc[par]
            z = (obs - esperado_par) / std_par if std_par > 0 else 0.0
            zscores[par] = round(z, 3)

        return dict(cooc), zscores

    def _calcular_ifm(self) -> Dict[int, float]:
        if self.total_concursos == 0:
            return {n: 50.0 for n in self.TODOS_NUMEROS}

        scores = {}
        freqs_rel = [s["freq_rel"] for s in self.stats_numeros.values()]
        min_f, max_f = min(freqs_rel), max(freqs_rel)
        span_f = max(1e-6, max_f - min_f)

        rec_campo = f"rec_{self.janela_recente}"
        recs = [s[rec_campo] for s in self.stats_numeros.values()]
        min_r, max_r = min(recs), max(recs)
        span_r = max(1e-6, max_r - min_r)

        z_sums = collections.defaultdict(float)
        for (a, b), z in self.matriz_zscore.items():
            z_sums[a] += z
            z_sums[b] += z
        z_vals = list(z_sums.values())
        min_z, max_z = min(z_vals), max(z_vals)
        span_z = max(1e-6, max_z - min_z)

        for n, st in self.stats_numeros.items():
            norm_freq = (st["freq_rel"] - min_f) / span_f
            norm_rec = (st[rec_campo] - min_r) / span_r

            g = st["atraso_atual"]
            gm = st["gap_medio"]
            gs = st["gap_std"]
            if st["recuperacao_flag"]:
                comp_gap = 0.85
            elif g <= gm:
                comp_gap = 0.50 + 0.35 * (g / max(1.0, gm))
            else:
                excesso = (g - gm) / max(1.0, gs)
                comp_gap = max(0.20, 0.85 - 0.15 * excesso)

            norm_assoc = (z_sums[n] - min_z) / span_z
            dist_c = st["dist_centro"]
            norm_centro = 1.0 - (dist_c / 25.0)

            if self.estrategia == "frequencia_pura" or self.estrategia == "frequencia":
                w_f, w_r, w_g, w_a, w_c = 0.60, 0.10, 0.10, 0.10, 0.10
            elif self.estrategia == "frequencia_recente":
                w_f, w_r, w_g, w_a, w_c = 0.10, 0.60, 0.10, 0.10, 0.10
            elif self.estrategia == "atraso" or self.estrategia == "atraso_recuperacao":
                w_f, w_r, w_g, w_a, w_c = 0.10, 0.10, 0.60, 0.10, 0.10
            elif self.estrategia == "associacao":
                w_f, w_r, w_g, w_a, w_c = 0.15, 0.15, 0.10, 0.50, 0.10
            elif self.estrategia == "matematica_pura":
                w_f, w_r, w_g, w_a, w_c = 0.15, 0.15, 0.15, 0.15, 0.40
            else:
                w_f, w_r, w_g, w_a, w_c = 0.30, 0.20, 0.20, 0.20, 0.10

            raw_score = (
                w_f * norm_freq +
                w_r * norm_rec +
                w_g * comp_gap +
                w_a * norm_assoc +
                w_c * norm_centro
            )

            ifm = round(raw_score * 80.0 + 15.0, 1)
            scores[n] = max(10.0, min(99.0, ifm))

        return scores

    def _selecionar_pool(self) -> List[int]:
        if self.pool_tamanho >= 50 and self.sniper == "desativado":
            return sorted(self.TODOS_NUMEROS)

        ranking_ifm = sorted(self.TODOS_NUMEROS, key=lambda n: self.scores_ifm[n], reverse=True)

        alvo_pool = self.pool_tamanho
        if self.sniper == "conservador":
            alvo_pool = max(20, min(self.pool_tamanho, int(self.TOTAL_UNIVERSO * 0.70)))
        elif self.sniper == "balanceado":
            alvo_pool = max(20, min(self.pool_tamanho, int(self.TOTAL_UNIVERSO * 0.50)))
        elif self.sniper == "agressivo":
            alvo_pool = max(20, min(self.pool_tamanho, int(self.TOTAL_UNIVERSO * 0.40)))

        pool_selecionado = set()
        for f_id, nums_f in self.FAIXAS.items():
            nums_ordenados = sorted(nums_f, key=lambda n: self.scores_ifm[n], reverse=True)
            pool_selecionado.update(nums_ordenados[:2])

        for n in ranking_ifm:
            if len(pool_selecionado) >= alvo_pool:
                break
            pool_selecionado.add(n)

        return sorted(list(pool_selecionado))

    def validar_combinacao_6(self, dezenas: List[int]) -> bool:
        if len(dezenas) != 6:
            return False
        if len(set(dezenas)) != 6:
            return False
        if any(d < 1 or d > 50 for d in dezenas):
            return False

        if self.bloquear_consecutivos:
            s_dez = sorted(dezenas)
            consec = 1
            max_consec = 1
            for i in range(1, len(s_dez)):
                if s_dez[i] == s_dez[i - 1] + 1:
                    consec += 1
                    if consec > max_consec:
                        max_consec = consec
                else:
                    consec = 1
            if max_consec > 3:
                return False

        pares = sum(1 for d in dezenas if d % 2 == 0)
        if pares == 0 or pares == 6:
            return False

        faixa_counts = collections.defaultdict(int)
        for d in dezenas:
            f = ((d - 1) // 10) + 1
            faixa_counts[f] += 1
        if any(c > 4 for c in faixa_counts.values()):
            return False

        soma = sum(dezenas)
        if soma < 70 or soma > 235:
            return False

        return True

    @staticmethod
    def calcular_distancia(jogo1: List[int], jogo2: List[int]) -> float:
        s1 = set(jogo1)
        s2 = set(jogo2)
        inter = len(s1.intersection(s2))
        return round(1.0 - (inter / 6.0), 3)

    def gerar_carteira(self, quantidade_jogos: int = 10, seed_offset: int = 0) -> Dict[str, Any]:
        qtd = max(1, min(5000, int(quantidade_jogos)))
        pool = self.pool_efetivo
        rng = random.Random(42 + seed_offset + self.total_concursos)

        pares_trevos_disponiveis = list(self.PARES_TREVOS_POSSIVEIS)
        rng.shuffle(pares_trevos_disponiveis)

        if self.estrategia_trevo == "fixo" and self.trevos_fixos and len(self.trevos_fixos) == 2:
            par_fixo = tuple(sorted(self.trevos_fixos))
            pares_trevos_carteira = [par_fixo] * qtd
        elif self.estrategia_trevo == "maior_ifm":
            pares_ordenados = sorted(
                self.PARES_TREVOS_POSSIVEIS,
                key=lambda p: self.stats_trevos["pares"][p]["score_ifm"],
                reverse=True
            )
            pares_trevos_carteira = [pares_ordenados[i % len(pares_ordenados)] for i in range(qtd)]
        else:
            pares_trevos_carteira = []
            for i in range(qtd):
                pares_trevos_carteira.append(pares_trevos_disponiveis[i % len(pares_trevos_disponiveis)])

        jogos_gerados = []
        numeros_utilizados_contagem = collections.defaultdict(int)
        pares_utilizados = set()

        tentativas_max = qtd * 300
        tentativas = 0

        pesos_dezenas = [self.scores_ifm[n] ** 1.3 for n in pool]
        total_pesos = sum(pesos_dezenas)
        prob_dezenas = [p / total_pesos for p in pesos_dezenas]

        while len(jogos_gerados) < qtd and tentativas < tentativas_max:
            tentativas += 1

            candidato = sorted(rng.choices(pool, weights=prob_dezenas, k=6))
            if len(set(candidato)) != 6:
                unicos = list(set(candidato))
                restantes = [n for n in pool if n not in unicos]
                rng.shuffle(restantes)
                candidato = sorted(unicos + restantes[:6 - len(unicos)])

            if not self.validar_combinacao_6(candidato):
                continue

            if jogos_gerados:
                distancias = [self.calcular_distancia(candidato, j["dezenas"]) for j in jogos_gerados]
                min_dist = min(distancias)
                if min_dist < 0.50 and tentativas < tentativas_max * 0.85:
                    continue

            score_dezenas = statistics.mean([self.scores_ifm[d] for d in candidato])
            par_trevo = pares_trevos_carteira[len(jogos_gerados)]
            score_trevo = self.stats_trevos["pares"][par_trevo]["score_ifm"]
            score_total_jogo = round(0.75 * score_dezenas + 0.25 * score_trevo, 1)

            jogos_gerados.append({
                "indice": len(jogos_gerados) + 1,
                "dezenas": candidato,
                "trevos": list(par_trevo),
                "score": score_total_jogo,
                "dezenas_formatadas": " ".join(f"{d:02d}" for d in candidato),
                "trevos_formatados": f"🍀 {par_trevo[0]:02d} {par_trevo[1]:02d}"
            })

            for d in candidato:
                numeros_utilizados_contagem[d] += 1
            for p in itertools.combinations(candidato, 2):
                pares_utilizados.add(p)

        dezenas_cobertas = len(numeros_utilizados_contagem)
        cobertura_pool_pct = round((dezenas_cobertas / len(pool)) * 100.0, 1)

        distancias_carteira = []
        for i in range(len(jogos_gerados)):
            for j in range(i + 1, len(jogos_gerados)):
                distancias_carteira.append(
                    self.calcular_distancia(jogos_gerados[i]["dezenas"], jogos_gerados[j]["dezenas"])
                )
        distancia_media = round(statistics.mean(distancias_carteira), 3) if distancias_carteira else 1.0
        repeticao_media = round((1.0 - distancia_media) * 6.0, 2)

        contagem_trevos = collections.defaultdict(int)
        for j in jogos_gerados:
            for t in j["trevos"]:
                contagem_trevos[t] += 1

        score_medio_carteira = round(statistics.mean([j["score"] for j in jogos_gerados]), 1) if jogos_gerados else 0.0

        pares_total = sum(sum(1 for d in j["dezenas"] if d % 2 == 0) for j in jogos_gerados)
        impares_total = len(jogos_gerados) * 6 - pares_total

        faixas_dist = {f"F{i}": 0 for i in range(1, 6)}
        for j in jogos_gerados:
            for d in j["dezenas"]:
                f_idx = ((d - 1) // 10) + 1
                faixas_dist[f"F{f_idx}"] += 1

        mais_utilizadas = sorted(numeros_utilizados_contagem.items(), key=lambda x: x[1], reverse=True)[:5]
        menos_utilizadas = sorted(
            [(n, numeros_utilizados_contagem.get(n, 0)) for n in pool],
            key=lambda x: x[1]
        )[:5]

        auditoria_status = {
            "filtro_1_seis_dezenas": all(len(j["dezenas"]) == 6 for j in jogos_gerados),
            "filtro_2_faixa_1_a_50": all(all(1 <= d <= 50 for d in j["dezenas"]) for j in jogos_gerados),
            "filtro_3_sem_duplicidade": all(len(set(j["dezenas"])) == 6 for j in jogos_gerados),
            "filtro_4_max_3_consecutivos": all(self.validar_combinacao_6(j["dezenas"]) for j in jogos_gerados),
            "filtro_5_controle_paridade": True,
            "filtro_6_distribuicao_faixas": True,
            "filtro_7_cobertura_pool": f"{cobertura_pool_pct}% ({dezenas_cobertas}/{len(pool)})",
            "filtro_8_distancia_combinatoria": f"Distância Média {distancia_media}",
            "filtro_9_dois_trevos_validos": all(len(j["trevos"]) == 2 and j["trevos"][0] != j["trevos"][1] for j in jogos_gerados),
            "filtro_10_verdade_matematica": "CONFORME (Sem promessa de prêmio)"
        }

        return {
            "sucesso": True,
            "modalidade": "+Milionária",
            "quantidade_jogos": len(jogos_gerados),
            "pool_tamanho": len(pool),
            "pool": pool,
            "estrategia": self.estrategia,
            "sniper": self.sniper,
            "jogos": jogos_gerados,
            "relatorio": {
                "cobertura_pool_pct": cobertura_pool_pct,
                "dezenas_cobertas": dezenas_cobertas,
                "total_pares_cobertos": len(pares_utilizados),
                "distancia_media": distancia_media,
                "repeticao_media": repeticao_media,
                "score_medio_carteira": score_medio_carteira,
                "pares_total": pares_total,
                "impares_total": impares_total,
                "distribuicao_faixas": faixas_dist,
                "mais_utilizadas": [{"numero": n, "qtd": q} for n, q in mais_utilizadas],
                "menos_utilizadas": [{"numero": n, "qtd": q} for n, q in menos_utilizadas],
                "distribuicao_trevos": {f"Trevo {k}": v for k, v in sorted(contagem_trevos.items())}
            },
            "auditoria_10_filtros": auditoria_status,
            "declaracao_honestidade": self.DECLARACAO_HONESTIDADE
        }

    def obter_ranking_numeros(self) -> List[Dict[str, Any]]:
        pool_set = set(self.pool_efetivo)
        tabela = []
        ranking_ordenado = sorted(self.TODOS_NUMEROS, key=lambda n: self.scores_ifm[n], reverse=True)

        for pos, n in enumerate(ranking_ordenado, start=1):
            st = self.stats_numeros[n]
            ifm = self.scores_ifm[n]

            if n not in pool_set:
                classif = "🔴 BLOQUEADO"
            elif ifm >= 80.0:
                classif = "🔵 ELITE"
            elif ifm >= 65.0:
                classif = "🟢 FORTE"
            elif ifm >= 45.0:
                classif = "🟡 NEUTRO"
            else:
                classif = "🟠 FRACO"

            freq_label = "Alta" if st["freq_rel"] >= 0.14 else ("Média" if st["freq_rel"] >= 0.10 else "Baixa")
            rec_campo = f"rec_{self.janela_recente}"
            rec_val = st[rec_campo]
            rec_label = "Alta" if rec_val >= 2 else ("Média" if rec_val == 1 else "Baixa")

            z_avg = statistics.mean([z for (a, b), z in self.matriz_zscore.items() if a == n or b == n])
            assoc_label = "Forte" if z_avg > 0.4 else ("Neutra" if z_avg >= -0.3 else "Fraca")

            tabela.append({
                "posicao": pos,
                "numero": n,
                "numero_formatado": f"{n:02d}",
                "ifm": ifm,
                "frequencia_absoluta": st["freq_abs"],
                "frequencia": freq_label,
                "recencia": rec_label,
                "gap": st["atraso_atual"],
                "gap_medio": st["gap_medio"],
                "gap_status": st["gap_status"],
                "associacao": assoc_label,
                "classificacao": classif,
                "no_pool": n in pool_set,
                "faixa": st["faixa"],
                "par": st["par"]
            })

        return tabela

    def obter_detalhe_numero(self, numero: int) -> Dict[str, Any]:
        n = int(numero)
        if n not in self.stats_numeros:
            return {"erro": "Número inválido"}

        st = self.stats_numeros[n]
        ifm = self.scores_ifm[n]

        parceiros = []
        for outro in self.TODOS_NUMEROS:
            if outro == n:
                continue
            par = tuple(sorted((n, outro)))
            z = self.matriz_zscore.get(par, 0.0)
            cooc_abs = self.matriz_coocorrencia.get(par, 0)
            parceiros.append({"parceiro": outro, "zscore": z, "coocorrencias": cooc_abs})

        top_parceiros = sorted(parceiros, key=lambda x: x["zscore"], reverse=True)[:3]
        pares_fracos = sorted(parceiros, key=lambda x: x["zscore"])[:3]

        return {
            "numero": n,
            "numero_formatado": f"{n:02d}",
            "ifm": ifm,
            "estatisticas": st,
            "top_parceiros_fortes": top_parceiros,
            "parceiros_mais_fracos": pares_fracos,
            "declaracao": (
                f"O número {n:02d} possui score IFM {ifm}/100 calculado estritamente a partir "
                f"do histórico de {self.total_concursos} concursos. Esse valor reflete apenas "
                f"a densidade de conexões estatísticas passadas e não constitui garantia de sorteio futuro."
            )
        }

    def executar_backtesting(
        self,
        concursos_teste: int = 30,
        quantidade_jogos: int = 10,
        estrategia: str = "equilibrada"
    ) -> Dict[str, Any]:
        T = len(self.historico)
        if T < 25:
            return {
                "sucesso": False,
                "erro": "AMOSTRA INSUFICIENTE PARA CONCLUSÃO ROBUSTA (mínimo 25 concursos)."
            }

        qtd_teste = min(concursos_teste, T - 15)
        concursos_alvo = list(range(T - qtd_teste, T))

        acertos_dezenas_dist = collections.defaultdict(int)
        acertos_trevos_dist = collections.defaultdict(int)
        total_acertos_dezenas = []

        acertos_baseline_dezenas = []
        rng_base = random.Random(999)

        for idx in concursos_alvo:
            hist_treino = self.historico[:idx]
            hist_trevos_treino = self.historico_trevos[:idx]
            resultado_real_dezenas = set(self.historico[idx])
            resultado_real_trevos = set(self.historico_trevos[idx])

            motor_retro = MotorMilionariaB2B(
                historico=hist_treino,
                historico_trevos=hist_trevos_treino,
                pool_tamanho=self.pool_tamanho,
                estrategia=estrategia,
                bloquear_acima_3_consecutivos=self.bloquear_consecutivos,
                estrategia_trevo=self.estrategia_trevo
            )

            res = motor_retro.gerar_carteira(quantidade_jogos=quantidade_jogos, seed_offset=idx)

            for j in res["jogos"]:
                acertos_dez = len(set(j["dezenas"]).intersection(resultado_real_dezenas))
                acertos_tr = len(set(j["trevos"]).intersection(resultado_real_trevos))
                acertos_dezenas_dist[acertos_dez] += 1
                acertos_trevos_dist[acertos_tr] += 1
                total_acertos_dezenas.append(acertos_dez)

            for _ in range(quantidade_jogos):
                rand_dez = set(rng_base.sample(self.TODOS_NUMEROS, 6))
                acertos_base = len(rand_dez.intersection(resultado_real_dezenas))
                acertos_baseline_dezenas.append(acertos_base)

        total_apostas = len(total_acertos_dezenas)
        media_estrategia = round(statistics.mean(total_acertos_dezenas), 3) if total_acertos_dezenas else 0.0
        media_baseline = round(statistics.mean(acertos_baseline_dezenas), 3) if acertos_baseline_dezenas else 0.0
        diferenca_acaso = round(media_estrategia - media_baseline, 3)

        std_estrategia = statistics.stdev(total_acertos_dezenas) if len(total_acertos_dezenas) > 1 else 0.0
        se = std_estrategia / math.sqrt(total_apostas) if total_apostas > 0 else 1.0
        z_stat = (media_estrategia - media_baseline) / se if se > 0 else 0.0

        if abs(z_stat) < 1.96:
            conclusao = "Não foi identificada vantagem estatística consistente sobre a aleatoriedade no período analisado."
            alerta_overfitting = "Resultado compatível com a hipótese nula de independência estocástica."
        elif z_stat >= 1.96:
            conclusao = "Desempenho ligeiramente superior ao acaso nos parâmetros testados (significância estatística local)."
            alerta_overfitting = "Atenção: padrões passados podem sofrer regressão à média em novos concursos."
        else:
            conclusao = "Desempenho no período inferior ao baseline aleatório."
            alerta_overfitting = "Estratégia sub-ótima para a janela temporal selecionada."

        return {
            "sucesso": True,
            "estrategia_testada": estrategia,
            "concursos_analisados": len(concursos_alvo),
            "total_apostas_geradas": total_apostas,
            "metricas": {
                "media_acertos_motor": media_estrategia,
                "media_acertos_baseline_aleatorio": media_baseline,
                "diferenca_sobre_acaso": diferenca_acaso,
                "maior_acerto": max(total_acertos_dezenas) if total_acertos_dezenas else 0,
                "menor_acerto": min(total_acertos_dezenas) if total_acertos_dezenas else 0,
                "desvio_padrao": round(std_estrategia, 3),
                "distribuicao_dezenas": {f"{k}_acertos": v for k, v in sorted(acertos_dezenas_dist.items())},
                "distribuicao_trevos": {f"{k}_trevos": v for k, v in sorted(acertos_trevos_dist.items())}
            },
            "auditoria_cientifica": {
                "z_score_significancia": round(z_stat, 2),
                "nivel_confianca": "95%",
                "conclusao_honesta": conclusao,
                "alerta_interpretacao": alerta_overfitting
            },
            "declaracao_obrigatoria": self.DECLARACAO_HONESTIDADE
        }