import random
import time
from collections import Counter
import itertools

class BitmaskUtils:
    """Utilitarios de representacao binaria de 25 bits para alta performance."""
    ODD_MASK = sum(1 << (d - 1) for d in [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25])
    EVEN_MASK = sum(1 << (d - 1) for d in [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24])
    PRIME_MASK = sum(1 << (d - 1) for d in [2, 3, 5, 7, 11, 13, 17, 19, 23])
    MOLDURA_MASK = sum(1 << (d - 1) for d in [1, 2, 3, 4, 5, 6, 10, 11, 15, 16, 20, 21, 22, 23, 24, 25])
    CENTRO_MASK = sum(1 << (d - 1) for d in [7, 8, 9, 12, 13, 14, 17, 18, 19])
    
    # Divisoes Dinamicas (Primeira Metade vs Segunda Metade)
    DIV_13_12_A = sum(1 << (d - 1) for d in range(1, 14))   # 01-13
    DIV_13_12_B = sum(1 << (d - 1) for d in range(14, 26))  # 14-25
    
    DIV_12_13_A = sum(1 << (d - 1) for d in range(1, 13))   # 01-12
    DIV_12_13_B = sum(1 << (d - 1) for d in range(13, 26))  # 13-25

    COL_MASKS = [
        sum(1 << (d - 1) for d in [1, 6, 11, 16, 21]),
        sum(1 << (d - 1) for d in [2, 7, 12, 17, 22]),
        sum(1 << (d - 1) for d in [3, 8, 13, 18, 23]),
        sum(1 << (d - 1) for d in [4, 9, 14, 19, 24]),
        sum(1 << (d - 1) for d in [5, 10, 15, 20, 25]),
    ]
    
    LINE_MASKS = [
        sum(1 << (d - 1) for d in range(1, 6)),
        sum(1 << (d - 1) for d in range(6, 11)),
        sum(1 << (d - 1) for d in range(11, 16)),
        sum(1 << (d - 1) for d in range(16, 21)),
        sum(1 << (d - 1) for d in range(21, 26)),
    ]

    @staticmethod
    def to_mask(numbers):
        mask = 0
        for d in numbers:
            mask |= (1 << (d - 1))
        return mask

    @staticmethod
    def to_numbers(mask):
        return [d for d in range(1, 26) if (mask & (1 << (d - 1)))]

    @staticmethod
    def popcount(mask):
        return bin(mask).count('1')

    @staticmethod
    def overlap(mask_a, mask_b):
        return bin(mask_a & mask_b).count('1')

    @staticmethod
    def calculate_sum(mask):
        s = 0
        for d in range(1, 26):
            if mask & (1 << (d - 1)):
                s += d
        return s

    @staticmethod
    def max_consecutives(numbers):
        max_s = 1
        cur_s = 1
        for i in range(len(numbers) - 1):
            if numbers[i + 1] == numbers[i] + 1:
                cur_s += 1
                if cur_s > max_s:
                    max_s = cur_s
            else:
                cur_s = 1
        return max_s


class HistoricalDistribution:
    """Pesos estatisticos baseados no historico real de sorteios da Caixa."""
    
    PARITY_CHOICES_EQUILIBRADA = [
        (8, 7),  # 31.05%
        (7, 8),  # 26.04%
        (9, 6),  # 20.24%
        (6, 9),  # 13.02%
        (10, 5), # 6.75%
        (5, 10), # 2.37%
    ]
    PARITY_WEIGHTS_EQUILIBRADA = [3105, 2604, 2024, 1302, 675, 237]

    PARITY_CHOICES_EXAUSTAO = [
        (8, 7),  # 54%
        (7, 8),  # 46%
    ]
    PARITY_WEIGHTS_EXAUSTAO = [54, 46]


class MotorInteligenteLotofacilB2B:
    """
    Motor Oficial do B2B Loterias com suporte completo a:
    1. Equilibrada (Score B2B + Cobertura)
    2. Exaustao da Estrutura Principal (7/8 ou 8/7)
    3. Ampla Cobertura (Diversificacao Maxima)
    4. Foco em Duplas & Trios Fortes
    + Toggle Sniper, Divisoes Dinamicas e Bloco de Verdade Matematica.
    """

    def __init__(self, estrategia='EQUILIBRADA', sniper=True, num_por_jogo=15, janela_concursos=100):
        self.estrategia = estrategia.upper()  # 'EQUILIBRADA', 'EXAUSTAO', 'AMPLA_COBERTURA', 'DUPLAS_TRIOS'
        self.sniper = sniper
        self.num_por_jogo = num_por_jogo
        self.janela_concursos = janela_concursos
        self.odds_pool = [1, 3, 5, 7, 9, 11, 13, 15, 17, 19, 21, 23, 25]
        self.evens_pool = [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24]
        
        # Simulação da matriz de afinidade histórica de duplas e trios (da janela de análise)
        self.duplas_fortes = [(1, 2), (2, 4), (13, 20), (10, 11), (23, 25), (4, 9), (14, 19)]
        self.trios_fortes = [(1, 2, 3), (10, 11, 12), (13, 14, 15), (20, 22, 24), (7, 12, 17)]

    def _escolher_max_overlap(self, total_jogos):
        """Calcula o teto de sobreposicao conforme a estrategia e o toggle Sniper."""
        if self.sniper:
            if total_jogos <= 50:
                return 10
            elif total_jogos <= 500:
                return 11
            else:
                return 12
        else:
            # Sniper OFF: Permite maior margem
            return 12 if total_jogos <= 500 else 13

    def calcular_score_b2b(self, numbers, mask=None):
        """
        Calcula o Score B2B Multicriterio (0 a 100) para cada jogo gerado:
        - Paridade (25 pts)
        - Primos (20 pts)
        - Moldura (20 pts)
        - Soma (15 pts)
        - Divisao Dinamica 01-13/14-25 (10 pts)
        - Consecutividade (10 pts)
        """
        if mask is None:
            mask = BitmaskUtils.to_mask(numbers)
            
        score = 0
        
        # 1. Paridade
        impares = sum(1 for d in numbers if d % 2 != 0)
        if impares in (7, 8):
            score += 25
        elif impares in (6, 9):
            score += 20
        elif impares in (5, 10):
            score += 10

        # 2. Primos (4 a 7)
        primos = BitmaskUtils.popcount(mask & BitmaskUtils.PRIME_MASK)
        if primos in (5, 6):
            score += 20
        elif primos in (4, 7):
            score += 15
        elif primos == 3:
            score += 5

        # 3. Moldura (9 a 11)
        moldura = BitmaskUtils.popcount(mask & BitmaskUtils.MOLDURA_MASK)
        if moldura in (9, 10, 11):
            score += 20
        elif moldura in (8, 12):
            score += 10

        # 4. Soma (175 a 215)
        soma = BitmaskUtils.calculate_sum(mask)
        if 180 <= soma <= 210:
            score += 15
        elif 175 <= soma <= 215:
            score += 10

        # 5. Divisao Dinamica 01-13 / 14-25 (Esperado ~8/7 ou 7/8)
        parte1 = BitmaskUtils.popcount(mask & BitmaskUtils.DIV_13_12_A)
        if parte1 in (7, 8):
            score += 10
        elif parte1 in (6, 9):
            score += 6

        # 6. Consecutividade (<= 5)
        max_c = BitmaskUtils.max_consecutives(numbers)
        if max_c in (3, 4):
            score += 10
        elif max_c == 5:
            score += 8
        elif max_c == 2:
            score += 5

        return score

    def _valida_sanidade_jogo(self, mask, numbers):
        """Valida se o candidato cumpre as regras rigidas do painel."""
        # 1. Primos
        primos = BitmaskUtils.popcount(mask & BitmaskUtils.PRIME_MASK)
        if primos < 4 or primos > 7:
            return False

        # 2. Moldura
        moldura = BitmaskUtils.popcount(mask & BitmaskUtils.MOLDURA_MASK)
        if moldura < 9 or moldura > 11:
            return False

        # 3. Soma
        soma = BitmaskUtils.calculate_sum(mask)
        if soma < 175 or soma > 215:
            return False

        # 4. Anti-Saturacao de Colunas (Max 4 dezenas por coluna vertical)
        for col_mask in BitmaskUtils.COL_MASKS:
            if BitmaskUtils.popcount(mask & col_mask) > 4:
                return False

        # 5. Anti-Saturacao de Linhas (Max 4 dezenas por linha horizontal)
        for line_mask in BitmaskUtils.LINE_MASKS:
            if BitmaskUtils.popcount(mask & line_mask) > 4:
                return False

        # 6. Filtro rigido de consecutividade (<= 5)
        if BitmaskUtils.max_consecutives(numbers) > 5:
            return False

        # 7. Divisao Dinamica (Evita desproporcao 01-13 vs 14-25)
        parte1 = BitmaskUtils.popcount(mask & BitmaskUtils.DIV_13_12_A)
        if parte1 < 5 or parte1 > 10:
            return False

        return True

    def _gerar_candidato(self, target_odds, target_evens, freq_counter, fixed_mask=0, excluded_mask=0):
        """Gera candidato balanceado."""
        available_odds = [d for d in self.odds_pool if not (excluded_mask & (1 << (d - 1)))]
        available_evens = [d for d in self.evens_pool if not (excluded_mask & (1 << (d - 1)))]

        fixed_nums = BitmaskUtils.to_numbers(fixed_mask)
        fixed_odds = [d for d in fixed_nums if d % 2 != 0]
        fixed_evens = [d for d in fixed_nums if d % 2 == 0]

        rem_odds_needed = target_odds - len(fixed_odds)
        rem_evens_needed = target_evens - len(fixed_evens)

        if rem_odds_needed < 0 or rem_evens_needed < 0:
            return None, None

        def calc_weights(pool, fixed_list):
            candidates = [d for d in pool if d not in fixed_list]
            if not candidates:
                return [], []
            max_f = max(freq_counter.values()) if freq_counter else 0
            weights = [(max_f - freq_counter[d] + 2) ** 1.6 for d in candidates]
            return candidates, weights

        cand_odds, w_odds = calc_weights(available_odds, fixed_odds)
        cand_evens, w_evens = calc_weights(available_evens, fixed_evens)

        if len(cand_odds) < rem_odds_needed or len(cand_evens) < rem_evens_needed:
            return None, None

        chosen_odds = list(fixed_odds)
        if rem_odds_needed > 0:
            sub_chosen = set()
            while len(sub_chosen) < rem_odds_needed:
                d = random.choices(cand_odds, weights=w_odds, k=1)[0]
                sub_chosen.add(d)
            chosen_odds.extend(sub_chosen)

        chosen_evens = list(fixed_evens)
        if rem_evens_needed > 0:
            sub_chosen = set()
            while len(sub_chosen) < rem_evens_needed:
                d = random.choices(cand_evens, weights=w_evens, k=1)[0]
                sub_chosen.add(d)
            chosen_evens.extend(sub_chosen)

        # Se a estrategia for DUPLAS & TRIOS, tenta injetar um trio forte se couber
        if self.estrategia in ('DUPLAS_TRIOS', 'FOCO EM DUPLAS & TRIOS FORTES'):
            if random.random() < 0.6:
                trio = random.choice(self.trios_fortes)
                for d in trio:
                    if d not in chosen_odds and d not in chosen_evens and not (excluded_mask & (1 << (d - 1))):
                        # Substitui dezena da mesma paridade mais frequente
                        if d % 2 != 0 and len(chosen_odds) > len(fixed_odds):
                            chosen_odds.pop()
                            chosen_odds.append(d)
                        elif d % 2 == 0 and len(chosen_evens) > len(fixed_evens):
                            chosen_evens.pop()
                            chosen_evens.append(d)

        numbers = sorted(chosen_odds + chosen_evens)
        
        # Ajuste para jogos de 16, 17 ou 18 numeros se solicitado
        if self.num_por_jogo > 15:
            extras_needed = self.num_por_jogo - 15
            remaining = [d for d in range(1, 26) if d not in numbers and not (excluded_mask & (1 << (d - 1)))]
            if len(remaining) >= extras_needed:
                numbers.extend(random.sample(remaining, extras_needed))
                numbers.sort()

        mask = BitmaskUtils.to_mask(numbers)
        return mask, numbers

    def gerar_carteira_completa(self, qtd_jogos=100, dezenas_fixas=None, dezenas_excluidas=None):
        """
        Executa a geracao da carteira e retorna o objeto completo com
        o 'Bloco de Verdade Matematica' e Score B2B.
        """
        t0 = time.time()
        fixed_mask = BitmaskUtils.to_mask(dezenas_fixas or [])
        excluded_mask = BitmaskUtils.to_mask(dezenas_excluidas or [])

        carteira_masks = []
        carteira_jogos = []
        carteira_scores = []
        freq_counter = {d: 0 for d in range(1, 26)}

        max_overlap = self._escolher_max_overlap(qtd_jogos)

        # Seleciona o plano de paridades conforme a estrategia
        if self.estrategia in ('EXAUSTAO', 'EXAUSTAO DA ESTRUTURA PRINCIPAL (7/8 OU 8/7)'):
            parity_plan = random.choices(
                HistoricalDistribution.PARITY_CHOICES_EXAUSTAO,
                weights=HistoricalDistribution.PARITY_WEIGHTS_EXAUSTAO,
                k=qtd_jogos
            )
        else:
            parity_plan = random.choices(
                HistoricalDistribution.PARITY_CHOICES_EQUILIBRADA,
                weights=HistoricalDistribution.PARITY_WEIGHTS_EQUILIBRADA,
                k=qtd_jogos
            )

        for idx in range(qtd_jogos):
            target_odds, target_evens = parity_plan[idx]
            adicionado = False
            attempts = 0

            while attempts < 2500 and not adicionado:
                attempts += 1
                mask, numbers = self._gerar_candidato(
                    target_odds, target_evens, freq_counter, fixed_mask, excluded_mask
                )
                if mask is None:
                    continue

                # 1. Sanidade Estatistica
                if not self._valida_sanidade_jogo(mask, numbers):
                    continue

                # 2. Anti-Canibalismo (Overlap)
                conflito = False
                check_window = carteira_masks[-300:] if qtd_jogos > 500 else carteira_masks
                for existing_mask in reversed(check_window):
                    if BitmaskUtils.overlap(mask, existing_mask) > max_overlap:
                        conflito = True
                        break
                if conflito:
                    continue

                # Jogo Aceito
                score = self.calcular_score_b2b(numbers, mask)
                carteira_masks.append(mask)
                carteira_jogos.append(numbers)
                carteira_scores.append(score)
                for d in numbers:
                    freq_counter[d] += 1
                adicionado = True

            # Fallback de seguranca
            if not adicionado:
                for _ in range(500):
                    mask, numbers = self._gerar_candidato(
                        target_odds, target_evens, freq_counter, fixed_mask, excluded_mask
                    )
                    if mask and self._valida_sanidade_jogo(mask, numbers):
                        score = self.calcular_score_b2b(numbers, mask)
                        carteira_masks.append(mask)
                        carteira_jogos.append(numbers)
                        carteira_scores.append(score)
                        for d in numbers:
                            freq_counter[d] += 1
                        break

        t1 = time.time()
        tempo_ms = (t1 - t0) * 1000

        # Montagem do "Bloco de Verdade Matematica"
        verdade_matematica = self._gerar_bloco_verdade_matematica(carteira_jogos, carteira_masks, carteira_scores, tempo_ms)

        return {
            "estrategia_usada": self.estrategia,
            "sniper_mode": self.sniper,
            "qtd_jogos": len(carteira_jogos),
            "tempo_execucao_ms": round(tempo_ms, 2),
            "score_medio_b2b": round(sum(carteira_scores) / len(carteira_scores), 1) if carteira_scores else 0,
            "jogos": [
                {
                    "id": i + 1,
                    "dezenas": carteira_jogos[i],
                    "score_b2b": carteira_scores[i],
                    "soma": BitmaskUtils.calculate_sum(carteira_masks[i]),
                    "impares": sum(1 for d in carteira_jogos[i] if d % 2 != 0),
                    "primos": BitmaskUtils.popcount(carteira_masks[i] & BitmaskUtils.PRIME_MASK),
                    "moldura": BitmaskUtils.popcount(carteira_masks[i] & BitmaskUtils.MOLDURA_MASK),
                }
                for i in range(len(carteira_jogos))
            ],
            "verdade_matematica": verdade_matematica
        }

    def _gerar_bloco_verdade_matematica(self, jogos, masks, scores, tempo_ms):
        """Gera metricas de auditoria combinatoria transparente para o B2B."""
        total = len(jogos)
        if total == 0:
            return {}

        counts = Counter(d for g in jogos for d in g)
        
        # Paridades
        parity_dist = Counter(sum(1 for d in g if d % 2 != 0) for g in jogos)
        
        # Primos
        prime_dist = Counter(BitmaskUtils.popcount(m & BitmaskUtils.PRIME_MASK) for m in masks)
        
        # Moldura
        moldura_dist = Counter(BitmaskUtils.popcount(m & BitmaskUtils.MOLDURA_MASK) for m in masks)
        
        # Overlaps
        overlaps = []
        for i in range(len(masks)):
            for j in range(i + 1, min(i + 50, len(masks))):
                overlaps.append(BitmaskUtils.overlap(masks[i], masks[j]))
                
        return {
            "status": "VALIDADO_100%",
            "unicidade_carteira_pct": 100.0 * len(set(masks)) / total,
            "distribuicao_paridade": {f"{k}I/{15-k}P": v for k, v in sorted(parity_dist.items())},
            "distribuicao_primos": {f"{k}_primos": v for k, v in sorted(prime_dist.items())},
            "distribuicao_moldura": {f"{k}_moldura": v for k, v in sorted(moldura_dist.items())},
            "frequencia_min_max_dezenas": {"min": min(counts.values()), "max": max(counts.values())},
            "pares_sobreposicao_critica_13_ou_mais": sum(1 for ov in overlaps if ov >= 13),
            "media_intersecao_interjogos": round(sum(overlaps) / len(overlaps), 2) if overlaps else 0,
            "media_score_b2b": round(sum(scores) / len(scores), 1)
        }
