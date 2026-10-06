/**
 * ╔══════════════════════════════════════════════════════════════════════╗
 * ║  MathPureEngine — Motor Matemático Puro para Sugestão de Números   ║
 * ║                                                                    ║
 * ║  Zero heurísticas. Zero falácias. Apenas matemática.               ║
 * ║                                                                    ║
 * ║  Fundamentos:                                                      ║
 * ║  1. Distribuição Hipergeométrica (probabilidades exatas)           ║
 * ║  2. Probabilidade Condicional via DP (funções geradoras)           ║
 * ║  3. Princípio da Máxima Entropia (Jaynes/Lagrange)                ║
 * ║  4. Scoring de Combinações Inteiras (interações)                   ║
 * ║  5. Roulette Wheel Selection (score^α)                            ║
 * ║  6. Pool Ótimo K* (otimização hipergeométrica)                    ║
 * ╚══════════════════════════════════════════════════════════════════════╝
 */
class MathPureEngine {

    // ══════════════════════════════════════════════════════════════
    //  CACHE DE COMBINAÇÕES — C(n,k) com memoização
    // ══════════════════════════════════════════════════════════════
    static _cCache = {};

    static C(n, k) {
        if (k < 0 || k > n) return 0;
        if (k === 0 || k === n) return 1;
        if (k === 1) return n;
        if (k > n - k) k = n - k; // Simetria: C(n,k) = C(n, n-k)

        const key = n + ',' + k;
        if (this._cCache[key] !== undefined) return this._cCache[key];

        // Usar multiplicação iterativa para evitar overflow
        let result = 1;
        for (let i = 0; i < k; i++) {
            result = result * (n - i) / (i + 1);
        }
        result = Math.round(result);
        this._cCache[key] = result;
        return result;
    }

    // Log de C(n,k) para evitar overflow em loterias grandes
    static logC(n, k) {
        if (k < 0 || k > n) return -Infinity;
        if (k === 0 || k === n) return 0;
        if (k > n - k) k = n - k;
        let result = 0;
        for (let i = 0; i < k; i++) {
            result += Math.log(n - i) - Math.log(i + 1);
        }
        return result;
    }

    // ══════════════════════════════════════════════════════════════
    //  DISTRIBUIÇÃO HIPERGEOMÉTRICA
    //  P(X = x | N total, K sucessos, n amostras)
    // ══════════════════════════════════════════════════════════════

    // P(X = x) — Probabilidade de exatamente x acertos
    static hypergeometricPMF(N, K, n, x) {
        if (x < Math.max(0, n + K - N) || x > Math.min(K, n)) return 0;

        // Usar log para evitar overflow
        const logP = this.logC(K, x) + this.logC(N - K, n - x) - this.logC(N, n);
        return Math.exp(logP);
    }

    // P(X >= minX) — Probabilidade de pelo menos minX acertos
    static hypergeometricCDF(N, K, n, minX) {
        let prob = 0;
        const maxX = Math.min(K, n);
        for (let x = minX; x <= maxX; x++) {
            prob += this.hypergeometricPMF(N, K, n, x);
        }
        return Math.min(1.0, prob);
    }

    // ══════════════════════════════════════════════════════════════
    //  POOL ÓTIMO K* — Maximiza P(≥ t acertos) / custo
    //  Para cada loteria, calcula o tamanho de pool mais eficiente
    // ══════════════════════════════════════════════════════════════
    static optimalPoolSize(N, n, drawSize, minHits) {
        let bestK = drawSize + 1;
        let bestEfficiency = 0;

        for (let K = drawSize + 1; K <= N; K++) {
            const prob = this.hypergeometricCDF(N, K, n, minHits);
            // Custo = C(K, drawSize) = nº de jogos possíveis no pool
            const logCost = this.logC(K, drawSize);
            // Eficiência = probabilidade / log(custo) — queremos máxima prob com mínimo custo
            const efficiency = prob / Math.max(1, logCost);

            if (efficiency > bestEfficiency) {
                bestEfficiency = efficiency;
                bestK = K;
            }
        }

        return {
            optimalK: bestK,
            probability: this.hypergeometricCDF(N, bestK, n, minHits),
            efficiency: bestEfficiency
        };
    }

    // Pool ótimo pré-calculado para cada loteria
    static getOptimalPool(gameKey) {
        const configs = {
            megasena:   { N: 60,  n: 6,  d: 6,  minHits: 4 },
            lotofacil:  { N: 25,  n: 15, d: 15, minHits: 11 },
            quina:      { N: 80,  n: 5,  d: 5,  minHits: 2 },
            duplasena:  { N: 50,  n: 6,  d: 6,  minHits: 4 },
            lotomania:  { N: 100, n: 20, d: 50, minHits: 15 },
            timemania:  { N: 80,  n: 7,  d: 10, minHits: 3 },
            diadesorte: { N: 31,  n: 7,  d: 7,  minHits: 5 }
        };

        const cfg = configs[gameKey];
        if (!cfg) return { optimalK: 20, probability: 0 };

        return this.optimalPoolSize(cfg.N, cfg.n, cfg.d, cfg.minHits);
    }

    // ══════════════════════════════════════════════════════════════
    //  PROBABILIDADE CONDICIONAL EXATA VIA DYNAMIC PROGRAMMING
    //  Para cada número X: P(X está numa combinação válida)
    //  Válida = soma ∈ range E paridade ∈ range
    //  Usa DP: dp[escolhidos][soma][pares]
    // ══════════════════════════════════════════════════════════════
    static conditionalProbabilityDP(gameKey, startNum, endNum, drawSize, sumRange, evenOddRange) {
        const totalRange = endNum - startNum + 1;

        // Para loterias grandes (Lotomania: 50 de 100), usar Monte Carlo
        if (totalRange > 50 || drawSize > 20) {
            return this._conditionalProbMonteCarlo(startNum, endNum, drawSize, sumRange, evenOddRange);
        }

        const probabilities = {};

        // Contar TOTAL de combinações válidas (sem fixar nenhum número)
        const totalValid = this._countValidCombinations(
            startNum, endNum, drawSize, sumRange, evenOddRange
        );

        if (totalValid === 0) {
            // Fallback: todos com mesma probabilidade
            for (let n = startNum; n <= endNum; n++) {
                probabilities[n] = drawSize / totalRange;
            }
            return probabilities;
        }

        // Para cada número X: contar combinações válidas que CONTÊM X
        for (let x = startNum; x <= endNum; x++) {
            const validWithX = this._countValidCombinationsContaining(
                x, startNum, endNum, drawSize, sumRange, evenOddRange
            );
            probabilities[x] = validWithX / totalValid;
        }

        return probabilities;
    }

    // DP: Contar combinações de drawSize números de [startNum, endNum]
    // com soma ∈ sumRange e pares ∈ evenOddRange
    static _countValidCombinations(startNum, endNum, drawSize, sumRange, evenOddRange) {
        const numbers = [];
        for (let i = startNum; i <= endNum; i++) numbers.push(i);
        const N = numbers.length;

        // dp[j][s][e] = nº de maneiras de escolher j números com soma s e e pares
        // j: 0..drawSize, s: 0..sumRange[1], e: 0..drawSize
        const maxSum = sumRange[1];
        const dp = this._createDP(drawSize, maxSum, drawSize);

        dp[0][0][0] = 1;

        for (let i = 0; i < N; i++) {
            const num = numbers[i];
            const isEven = num % 2 === 0 ? 1 : 0;

            // Iterar de trás para frente para não contar duas vezes
            for (let j = Math.min(drawSize - 1, i); j >= 0; j--) {
                for (let s = 0; s <= maxSum - num; s++) {
                    for (let e = 0; e <= j; e++) {
                        if (dp[j][s][e] === 0) continue;
                        const newS = s + num;
                        const newE = e + isEven;
                        if (newS <= maxSum && j + 1 <= drawSize && newE <= drawSize) {
                            dp[j + 1][newS][newE] += dp[j][s][e];
                        }
                    }
                }
            }
        }

        // Somar todas as combinações válidas
        let count = 0;
        for (let s = sumRange[0]; s <= sumRange[1]; s++) {
            for (let e = evenOddRange[0]; e <= evenOddRange[1]; e++) {
                if (e <= drawSize && s <= maxSum) {
                    count += dp[drawSize][s][e] || 0;
                }
            }
        }
        return count;
    }

    // DP: Contar combinações válidas que CONTÊM o número target
    static _countValidCombinationsContaining(target, startNum, endNum, drawSize, sumRange, evenOddRange) {
        const numbers = [];
        for (let i = startNum; i <= endNum; i++) {
            if (i !== target) numbers.push(i);
        }
        const N = numbers.length;
        const remaining = drawSize - 1;
        const targetIsEven = target % 2 === 0 ? 1 : 0;

        // Ajustar ranges para excluir o target
        const adjSumMin = Math.max(0, sumRange[0] - target);
        const adjSumMax = sumRange[1] - target;
        const adjEvenMin = Math.max(0, evenOddRange[0] - targetIsEven);
        const adjEvenMax = evenOddRange[1] - targetIsEven;

        if (adjSumMax < 0 || adjEvenMax < 0 || remaining < 0) return 0;

        const maxSum = adjSumMax;
        const dp = this._createDP(remaining, maxSum, remaining);
        dp[0][0][0] = 1;

        for (let i = 0; i < N; i++) {
            const num = numbers[i];
            const isEven = num % 2 === 0 ? 1 : 0;

            for (let j = Math.min(remaining - 1, i); j >= 0; j--) {
                for (let s = 0; s <= maxSum - num; s++) {
                    for (let e = 0; e <= j; e++) {
                        if (dp[j][s][e] === 0) continue;
                        const newS = s + num;
                        const newE = e + isEven;
                        if (newS <= maxSum && j + 1 <= remaining && newE <= remaining) {
                            dp[j + 1][newS][newE] += dp[j][s][e];
                        }
                    }
                }
            }
        }

        let count = 0;
        for (let s = adjSumMin; s <= adjSumMax; s++) {
            for (let e = adjEvenMin; e <= adjEvenMax; e++) {
                if (e <= remaining && s <= maxSum) {
                    count += dp[remaining][s][e] || 0;
                }
            }
        }
        return count;
    }

    // Criar array 3D para DP
    static _createDP(maxJ, maxS, maxE) {
        const dp = [];
        for (let j = 0; j <= maxJ; j++) {
            dp[j] = [];
            for (let s = 0; s <= maxS; s++) {
                dp[j][s] = new Float64Array(maxE + 1);
            }
        }
        return dp;
    }

    // Monte Carlo para loterias grandes (Lotomania, etc)
    static _conditionalProbMonteCarlo(startNum, endNum, drawSize, sumRange, evenOddRange) {
        const totalRange = endNum - startNum + 1;
        const SAMPLES = 100000;
        const counts = {};
        let totalValid = 0;

        for (let n = startNum; n <= endNum; n++) counts[n] = 0;

        for (let s = 0; s < SAMPLES; s++) {
            // Gerar combinação aleatória
            const combo = this._randomCombo(startNum, endNum, drawSize);

            // Verificar validade
            let sum = 0, evens = 0;
            for (const n of combo) {
                sum += n;
                if (n % 2 === 0) evens++;
            }

            if (sum >= sumRange[0] && sum <= sumRange[1] &&
                evens >= evenOddRange[0] && evens <= evenOddRange[1]) {
                totalValid++;
                for (const n of combo) counts[n]++;
            }
        }

        const probabilities = {};
        for (let n = startNum; n <= endNum; n++) {
            probabilities[n] = totalValid > 0 ? counts[n] / totalValid : drawSize / totalRange;
        }
        return probabilities;
    }

    // Gerar combinação aleatória
    static _randomCombo(startNum, endNum, drawSize) {
        const pool = [];
        for (let i = startNum; i <= endNum; i++) pool.push(i);
        const result = [];
        for (let i = 0; i < drawSize && pool.length > 0; i++) {
            const idx = Math.floor(Math.random() * pool.length);
            result.push(pool.splice(idx, 1)[0]);
        }
        return result.sort((a, b) => a - b);
    }

    // ══════════════════════════════════════════════════════════════
    //  MÁXIMA ENTROPIA (JAYNES) SOB RESTRIÇÕES
    //  Calcula os pesos ótimos p_i para cada número i, tal que:
    //  - Σ p_i = 1
    //  - Σ p_i × i ≈ soma_esperada
    //  - Σ p_i × (i%2==0) ≈ paridade_esperada
    //  - H = -Σ p_i ln(p_i) é MÁXIMO
    // ══════════════════════════════════════════════════════════════
    static maxEntropyWeights(startNum, endNum, drawSize, sumRange, evenOddRange) {
        const N = endNum - startNum + 1;

        // Soma esperada por número = média do range
        const targetSumPerNum = (sumRange[0] + sumRange[1]) / 2 / drawSize;
        // Paridade esperada = média do range de pares
        const targetEvenRatio = (evenOddRange[0] + evenOddRange[1]) / 2 / drawSize;

        // Resolver multiplicadores de Lagrange via Newton-Raphson
        // p_i = exp(-λ₀ - λ₁×i - λ₂×(i%2==0)) / Z
        let lambda0 = 0, lambda1 = 0, lambda2 = 0;
        const lr = 0.001; // Learning rate
        const ITERS = 500;

        for (let iter = 0; iter < ITERS; iter++) {
            // Calcular Z e expectativas
            let Z = 0;
            let expectSum = 0;
            let expectEven = 0;

            const rawP = [];
            for (let i = startNum; i <= endNum; i++) {
                const isEven = i % 2 === 0 ? 1 : 0;
                const logp = -lambda0 - lambda1 * i - lambda2 * isEven;
                const p = Math.exp(Math.max(-50, Math.min(50, logp))); // Clamp para estabilidade
                rawP.push({ num: i, p: p, isEven: isEven });
                Z += p;
            }

            // Normalizar e calcular expectativas
            for (const item of rawP) {
                const pNorm = item.p / Z;
                expectSum += pNorm * item.num;
                expectEven += pNorm * item.isEven;
            }

            // Gradientes (diferença entre expectativa e target)
            const gradSum = expectSum - targetSumPerNum;
            const gradEven = expectEven - targetEvenRatio;

            // Atualizar lambdas
            lambda1 += lr * gradSum;
            lambda2 += lr * gradEven;

            // Convergência
            if (Math.abs(gradSum) < 0.01 && Math.abs(gradEven) < 0.001) break;
        }

        // Calcular probabilidades finais
        const weights = {};
        let Z = 0;
        for (let i = startNum; i <= endNum; i++) {
            const isEven = i % 2 === 0 ? 1 : 0;
            const logp = -lambda0 - lambda1 * i - lambda2 * isEven;
            weights[i] = Math.exp(Math.max(-50, Math.min(50, logp)));
            Z += weights[i];
        }

        // Normalizar
        for (let i = startNum; i <= endNum; i++) {
            weights[i] /= Z;
        }

        return weights;
    }

    // ══════════════════════════════════════════════════════════════
    //  SCORING DE COMBINAÇÃO INTEIRA
    //  Avalia uma combinação como um TODO, não números individuais
    //  Inclui termos de interação entre números
    // ══════════════════════════════════════════════════════════════
    static scoreCombination(nums, profile, conditionalProbs) {
        const sorted = nums.slice().sort((a, b) => a - b);
        const n = sorted.length;
        const startNum = profile.range[0];
        const endNum = profile.range[1];
        const totalRange = endNum - startNum + 1;

        let score = 0;

        // 1. Soma dos scores individuais (probabilidade condicional)
        let sumIndividual = 0;
        for (const num of sorted) {
            sumIndividual += conditionalProbs[num] || (1 / totalRange);
        }
        score += sumIndividual * 40; // Peso 40%

        // 2. Distância Hamming média (espalhamento no range)
        let totalDist = 0;
        let pairs = 0;
        for (let i = 0; i < n; i++) {
            for (let j = i + 1; j < n; j++) {
                totalDist += Math.abs(sorted[i] - sorted[j]);
                pairs++;
            }
        }
        const avgDist = pairs > 0 ? totalDist / pairs : 0;
        const idealDist = totalRange / (n + 1); // Distribuição uniforme ideal
        const distScore = 1 - Math.abs(avgDist - idealDist) / idealDist;
        score += Math.max(0, distScore) * 20; // Peso 20%

        // 3. Soma — proximidade à média ideal
        const sum = sorted.reduce((a, b) => a + b, 0);
        const idealSum = (profile.sumRange[0] + profile.sumRange[1]) / 2;
        const sumSigma = (profile.sumRange[1] - profile.sumRange[0]) / 4; // ~2σ
        const sumDeviation = Math.abs(sum - idealSum) / Math.max(1, sumSigma);
        const sumScore = Math.exp(-0.5 * sumDeviation * sumDeviation); // Gaussiana
        score += sumScore * 15; // Peso 15%

        // 4. Entropia de paridade
        const evens = sorted.filter(x => x % 2 === 0).length;
        const evenRatio = evens / n;
        const idealEvenRatio = (profile.evenOddRange[0] + profile.evenOddRange[1]) / 2 / n;
        const parityScore = 1 - Math.abs(evenRatio - idealEvenRatio) * 3;
        score += Math.max(0, parityScore) * 10; // Peso 10%

        // 5. Cobertura zonal
        const zoneSize = profile.zoneSize || Math.ceil(totalRange / (profile.zones || 4));
        const zones = new Set(sorted.map(x => Math.floor((x - startNum) / zoneSize)));
        const zoneRatio = zones.size / (profile.zones || 4);
        score += zoneRatio * 10; // Peso 10%

        // 6. Penalidade por consecutivos longos
        let maxConsec = 1, curConsec = 1;
        for (let i = 1; i < n; i++) {
            if (sorted[i] === sorted[i - 1] + 1) {
                curConsec++;
                maxConsec = Math.max(maxConsec, curConsec);
            } else {
                curConsec = 1;
            }
        }
        const maxAllowed = profile.maxConsecutive || 3;
        const consecPenalty = maxConsec > maxAllowed ? -10 : (maxConsec <= 2 ? 5 : 0);
        score += consecPenalty; // Peso 5%

        return score;
    }

    // ══════════════════════════════════════════════════════════════
    //  VALIDAÇÃO COMBINATÓRIA COMPLETA
    //  Verifica TODAS as propriedades estruturais
    // ══════════════════════════════════════════════════════════════
    static validateSuggestion(nums, profile) {
        const sorted = nums.slice().sort((a, b) => a - b);
        const n = sorted.length;
        const startNum = profile.range[0];
        const endNum = profile.range[1];
        const totalRange = endNum - startNum + 1;

        // 1. Soma
        const sum = sorted.reduce((a, b) => a + b, 0);
        if (sum < profile.sumRange[0] || sum > profile.sumRange[1]) return false;

        // 2. Paridade
        const evens = sorted.filter(x => x % 2 === 0).length;
        if (evens < profile.evenOddRange[0] || evens > profile.evenOddRange[1]) return false;

        // 3. Zonas cobertas
        const zoneSize = profile.zoneSize || Math.ceil(totalRange / (profile.zones || 4));
        const zones = new Set(sorted.map(x => Math.floor((x - startNum) / zoneSize)));
        if (zones.size < (profile.minZonesCovered || 2)) return false;

        // 4. Consecutivos
        let maxConsec = 1, curConsec = 1;
        for (let i = 1; i < n; i++) {
            if (sorted[i] === sorted[i - 1] + 1) {
                curConsec++;
                maxConsec = Math.max(maxConsec, curConsec);
            } else {
                curConsec = 1;
            }
        }
        if (maxConsec > (profile.maxConsecutive || 3)) return false;

        // 5. Equilíbrio alto/baixo (se definido no perfil)
        if (profile.highLowBalance) {
            const midPoint = Math.floor((startNum + endNum) / 2);
            const lows = sorted.filter(x => x <= midPoint).length;
            if (lows < profile.highLowBalance[0] || lows > profile.highLowBalance[1]) return false;
        }

        // 6. Máximo de números com mesmo final (se definido)
        if (profile.maxSameEnding) {
            const endings = {};
            for (const num of sorted) {
                const ending = num % 10;
                endings[ending] = (endings[ending] || 0) + 1;
                if (endings[ending] > profile.maxSameEnding) return false;
            }
        }

        return true;
    }

    // ══════════════════════════════════════════════════════════════
    //  ROULETTE WHEEL SELECTION (score^α)
    //  Seleção probabilística proporcional ao score elevado a α
    // ══════════════════════════════════════════════════════════════
    static rouletteSelect(probabilities, count, profile, startNum, endNum, alpha) {
        const candidates = [];
        for (let n = startNum; n <= endNum; n++) {
            const p = probabilities[n] || 0;
            candidates.push({ num: n, weight: Math.pow(Math.max(0.0001, p), alpha) });
        }

        const result = [];
        const used = new Set();
        const maxAttempts = count * 20;
        let attempts = 0;

        while (result.length < count && attempts < maxAttempts) {
            attempts++;

            // Calcular soma total dos pesos restantes
            let totalWeight = 0;
            for (const c of candidates) {
                if (!used.has(c.num)) totalWeight += c.weight;
            }
            if (totalWeight <= 0) break;

            // Selecionar por roleta
            let rand = Math.random() * totalWeight;
            let selected = null;
            for (const c of candidates) {
                if (used.has(c.num)) continue;
                rand -= c.weight;
                if (rand <= 0) {
                    selected = c.num;
                    break;
                }
            }
            if (selected === null) selected = candidates[candidates.length - 1].num;

            // Verificar se adicionar este número mantém a combinação potencialmente válida
            const tempResult = [...result, selected].sort((a, b) => a - b);

            // Verificação leve: consecutivos
            let valid = true;
            let maxRun = 1, curRun = 1;
            for (let i = 1; i < tempResult.length; i++) {
                if (tempResult[i] === tempResult[i - 1] + 1) {
                    curRun++;
                    if (curRun > (profile.maxConsecutive || 3)) { valid = false; break; }
                } else {
                    curRun = 1;
                }
            }

            if (valid && !used.has(selected)) {
                result.push(selected);
                used.add(selected);
            }
        }

        // Fallback se não conseguiu preencher
        if (result.length < count) {
            for (let n = startNum; n <= endNum; n++) {
                if (result.length >= count) break;
                if (!used.has(n)) {
                    result.push(n);
                    used.add(n);
                }
            }
        }

        return result.sort((a, b) => a - b);
    }

    // ══════════════════════════════════════════════════════════════
    //  MÉTODO PRINCIPAL: SUGESTÃO ÓTIMA
    //  Combina todas as técnicas acima
    // ══════════════════════════════════════════════════════════════
    static suggestOptimal(gameKey, count) {
        const profile = this._getProfile(gameKey);
        if (!profile) return [];

        const startNum = profile.range[0];
        const endNum = profile.range[1];
        const totalRange = endNum - startNum + 1;
        const drawSize = count || profile.drawSize;

        console.log('[MathPure] ═══ Início: ' + profile.name + ' | ' + drawSize + ' números ═══');
        const t0 = performance.now();

        // PASSO 1: Probabilidade condicional exata via DP
        console.log('[MathPure] Passo 1: Probabilidade condicional (DP)...');
        const conditionalProbs = this.conditionalProbabilityDP(
            gameKey, startNum, endNum, drawSize,
            profile.sumRange, profile.evenOddRange
        );

        // PASSO 2: Pesos de máxima entropia (Jaynes)
        console.log('[MathPure] Passo 2: Máxima entropia (Jaynes)...');
        const entropyWeights = this.maxEntropyWeights(
            startNum, endNum, drawSize,
            profile.sumRange, profile.evenOddRange
        );

        // PASSO 3: Combinar probabilidade condicional + entropia
        // Fusão: 60% condicional + 40% entropia
        const fusedProbs = {};
        for (let n = startNum; n <= endNum; n++) {
            fusedProbs[n] = (conditionalProbs[n] || 0) * 0.60 +
                           (entropyWeights[n] || 0) * 0.40;
        }

        // PASSO 4: Determinar α para Roulette Wheel
        // Loterias esparsas → α menor (mais exploratório)
        // Loterias densas → α maior (mais focado)
        const density = drawSize / totalRange;
        const alpha = density > 0.4 ? 4.0 :   // Lotofácil (60%), Lotomania (50%)
                      density > 0.15 ? 3.0 :   // Dia de Sorte (22.6%)
                      2.5;                      // Mega (10%), Quina (6.25%)

        // PASSO 5: Gerar N candidatos e escolher o melhor
        console.log('[MathPure] Passo 5: Gerando 200 candidatos (α=' + alpha + ')...');
        const NUM_CANDIDATES = 200;
        let bestCandidate = null;
        let bestScore = -Infinity;
        let validCount = 0;

        for (let i = 0; i < NUM_CANDIDATES; i++) {
            const candidate = this.rouletteSelect(
                fusedProbs, drawSize, profile, startNum, endNum, alpha
            );

            // Validar
            if (!this.validateSuggestion(candidate, profile)) continue;
            validCount++;

            // Scorar combinação inteira
            const score = this.scoreCombination(candidate, profile, conditionalProbs);

            if (score > bestScore) {
                bestScore = score;
                bestCandidate = candidate;
            }
        }

        const elapsed = (performance.now() - t0).toFixed(1);
        console.log('[MathPure] ═══ ' + validCount + '/' + NUM_CANDIDATES + ' válidos | Melhor score: ' + (bestScore || 0).toFixed(2) + ' | ' + elapsed + 'ms ═══');

        // Fallback se nenhum candidato passou nos filtros
        if (!bestCandidate) {
            console.warn('[MathPure] Nenhum candidato válido. Relaxando filtros...');
            bestCandidate = this.rouletteSelect(
                fusedProbs, drawSize, profile, startNum, endNum, alpha
            );
        }

        // Armazenar métricas para o display de confiança
        if (bestCandidate) {
            this._lastSuggestion = {
                numbers: bestCandidate,
                score: bestScore,
                validRatio: validCount / NUM_CANDIDATES,
                alpha: alpha,
                elapsed: elapsed,
                method: 'DP+Jaynes+Roulette',
                conditionalProbs: conditionalProbs,
                optimalPool: this.getOptimalPool(gameKey)
            };
        }

        return bestCandidate || [];
    }

    // Obter última métrica de sugestão (para display na UI)
    static getLastMetrics() {
        return this._lastSuggestion || null;
    }

    // ══════════════════════════════════════════════════════════════
    //  PERFIS — Espelho do NovaEraEngine mas sem camadas de falácia
    // ══════════════════════════════════════════════════════════════
    static _getProfile(gameKey) {
        const profiles = {
            megasena: {
                name: 'Mega Sena', drawSize: 6, range: [1, 60],
                zoneSize: 10, zones: 6, minZonesCovered: 3,
                maxConsecutive: 2, evenOddRange: [2, 4],
                sumRange: [110, 250],
                highLowBalance: [2, 4], maxSameEnding: 2
            },
            lotofacil: {
                name: 'Lotofácil', drawSize: 15, range: [1, 25],
                zoneSize: 5, zones: 5, minZonesCovered: 5,
                maxConsecutive: 10, evenOddRange: [5, 10],
                sumRange: [155, 235]
            },
            quina: {
                name: 'Quina', drawSize: 5, range: [1, 80],
                zoneSize: 10, zones: 8, minZonesCovered: 3,
                maxConsecutive: 2, evenOddRange: [1, 4],
                sumRange: [50, 340]
            },
            duplasena: {
                name: 'Dupla Sena', drawSize: 6, range: [1, 50],
                zoneSize: 10, zones: 5, minZonesCovered: 3,
                maxConsecutive: 2, evenOddRange: [2, 4],
                sumRange: [55, 245],
                highLowBalance: [2, 4], maxSameEnding: 2
            },
            lotomania: {
                name: 'Lotomania', drawSize: 50, range: [0, 99],
                zoneSize: 10, zones: 10, minZonesCovered: 8,
                maxConsecutive: 5, evenOddRange: [22, 28],
                sumRange: [2050, 2950]
            },
            timemania: {
                name: 'Timemania', drawSize: 10, range: [1, 80],
                zoneSize: 10, zones: 8, minZonesCovered: 4,
                maxConsecutive: 2, evenOddRange: [3, 7],
                sumRange: [200, 610]
            },
            diadesorte: {
                name: 'Dia de Sorte', drawSize: 7, range: [1, 31],
                zoneSize: 8, zones: 4, minZonesCovered: 3,
                maxConsecutive: 2, evenOddRange: [2, 5],
                sumRange: [55, 170],
                highLowBalance: [2, 5], maxSameEnding: 2
            }
        };
        return profiles[gameKey] || null;
    }

    // Storage interno
    static _lastSuggestion = null;
}

// Exportar globalmente
if (typeof window !== 'undefined') {
    window.MathPureEngine = MathPureEngine;
}

console.log('%c[MATH-PURE] ═══ Motor Matemático Puro v1.0 CARREGADO ═══', 'color: #22C55E; font-size: 14px; font-weight: bold; background: #0a0a1a;');
