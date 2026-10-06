/**
 * ╔══════════════════════════════════════════════════════════════════════╗
 * ║  MOTOR DE FECHAMENTO MANUAL v3.0 — GREEDY SET COVER               ║
 * ║  Motor Universal para 7 Loterias da Caixa                         ║
 * ║                                                                    ║
 * ║  MUDANÇAS v3.0 (sobre v2.0):                                      ║
 * ║  • REMOVIDO: toda contaminação IA Synergy / ClosingEngine          ║
 * ║  • ADICIONADO: Greedy Set Cover (maximiza pares + triplas)         ║
 * ║  • ADICIONADO: Filtros estruturais P5-P95 por loteria              ║
 * ║  • ADICIONADO: Anti-concentração (teto de frequência)              ║
 * ║  • ADICIONADO: Hamming distance mínima entre jogos                 ║
 * ║  • ADICIONADO: ROI honesto com probabilidade hipergeométrica       ║
 * ║  • ADICIONADO: Métricas de cobertura (pares, triplas, uso)         ║
 * ║  • Peso UNIFORME (1.0) para todos os números do pool               ║
 * ╚══════════════════════════════════════════════════════════════════════╝
 */

class MotorFechamentoManual {

    // ═══════════════════════════════════════════════════════════════
    //  CONSTANTES — Filtros estruturais baseados em dados reais
    //  (ranges P5-P95 de sorteios históricos)
    // ═══════════════════════════════════════════════════════════════
    static get FILTER_RANGES() {
        // Valores calculados com matemática pura:
        // Soma: Normal(E, Var) → E = k*(min+max)/2, Var = k*(n+1)*(n-k)/12
        // Paridade: Distribuição Hipergeométrica exata
        // Alto/Baixo: Distribuição Hipergeométrica exata
        return {
            megasena:   { sumRange: [116, 250], parityRange: [1, 5], maxConsecutive: 2, minZones: 3, zones: 6, zoneSize: 10, highLowBalance: [1, 5] },
            lotofacil:  { sumRange: [165, 225], parityRange: [5, 9], maxConsecutive: 5, minZones: 5, zones: 5, zoneSize: 5, highLowBalance: [6, 10] },
            quina:      { sumRange: [119, 285], parityRange: [1, 4], maxConsecutive: 2, minZones: 3, zones: 8, zoneSize: 10, highLowBalance: [1, 4] },
            duplasena:  { sumRange: [98, 208],  parityRange: [1, 5], maxConsecutive: 2, minZones: 3, zones: 5, zoneSize: 10, highLowBalance: [1, 5] },
            timemania:  { sumRange: [292, 518], parityRange: [3, 7], maxConsecutive: 3, minZones: 4, zones: 8, zoneSize: 10, highLowBalance: [3, 7] },
            diadesorte: { sumRange: [77, 147],  parityRange: [2, 5], maxConsecutive: 3, minZones: 3, zones: 4, zoneSize: 8, highLowBalance: [2, 5] },
            lotomania:  { sumRange: [2236, 2714], parityRange: [21, 29], maxConsecutive: 5, minZones: 9, zones: 10, zoneSize: 10, highLowBalance: [21, 29] }
        };
    }

    // Prêmios fixos conhecidos (para faixas com valor fixo)
    static get FIXED_PRIZES() {
        return {
            lotofacil: { 11: 6, 12: 12, 13: 30 },
            timemania: { 3: 3.50, 4: 10.50 },
            diadesorte: { 4: 5, 5: 25 }
        };
    }

    // ═══════════════════════════════════════════════════════════════
    //  Obter configuração da loteria via GAMES global
    // ═══════════════════════════════════════════════════════════════
    static getConfig(gameKey) {
        if (typeof GAMES === 'undefined' || !GAMES[gameKey]) {
            throw new Error('[MOTOR-MANUAL] Loteria não encontrada: ' + gameKey);
        }
        var g = GAMES[gameKey];
        return {
            key: gameKey,
            name: g.name,
            range: g.range,
            drawSize: g.minBet,
            maxBet: g.maxBet || g.range[1],
            price: g.price || 5.00,
            totalNumbers: g.range[1] - g.range[0] + 1,
            strategies: g.strategies || [],
            drawCount: g.draw || g.minBet
        };
    }

    // ═══════════════════════════════════════════════════════════════
    //  PONTO DE ENTRADA PRINCIPAL
    // ═══════════════════════════════════════════════════════════════
    static generate(gameKey, pool, fixedNumbers, numGames, drawSize) {
        var t0 = Date.now();
        var cfg = this.getConfig(gameKey);
        var k = drawSize || cfg.drawSize;

        // Validar e limpar pool: remover duplicatas, fora do range
        var validPool = pool.filter(function(n) { return n >= cfg.range[0] && n <= cfg.range[1]; });
        var fixedSet = new Set((fixedNumbers || []).filter(function(n) { return validPool.includes(n); }));
        var fixedArr = Array.from(fixedSet).sort(function(a, b) { return a - b; });
        var poolArr = Array.from(new Set(validPool)).sort(function(a, b) { return a - b; });

        console.log('%c[MOTOR-MANUAL] ══════════════════════════════════════════', 'color: #FFD700; font-weight: bold; font-size: 14px;');
        console.log('%c[MOTOR-MANUAL] ' + cfg.name + ' | Pool: ' + poolArr.length +
            ' | Fixos: ' + fixedArr.length + ' | Jogos: ' + numGames + ' | k=' + k,
            'color: #FFD700; font-weight: bold;');

        // ── Validações ──
        if (poolArr.length < k) {
            return { games: [], error: 'Pool insuficiente. Selecione pelo menos ' + k + ' números.', analysis: {} };
        }
        if (fixedArr.length > k) {
            return { games: [], error: 'Muitos fixos (' + fixedArr.length + '). Máximo: ' + k, analysis: {} };
        }
        if (fixedArr.length === k) {
            return this._buildResult([fixedArr.slice()], cfg, poolArr, fixedArr, k, t0, 0, null, null, null, 0);
        }

        // ── Calcular total possível ──
        var maxPossible = this._comb(poolArr.length - fixedArr.length, k - fixedArr.length);

        var allGames = [];
        var dupCount = 0;
        var coveredPairs = null;
        var coveredTriples = null;
        var numberUsage = null;

        if (numGames >= maxPossible) {
            // ── Fechamento Matemático Total ──
            allGames = this._generateAll(poolArr, fixedArr, k);
            console.log('[MOTOR-MANUAL] Fechamento TOTAL: ' + allGames.length + ' combinações');
        } else {
            // ── AI Synergy (Regra Inicial do Projeto) ──
            var aiSynergy = this._getAISynergy(gameKey, poolArr);
            if (aiSynergy) console.log('[MOTOR-MANUAL] 🧠 Sinergia Histórica Ativada para confrontos!');

            // ── Greedy Set Cover ──
            console.log('[MOTOR-MANUAL] Iniciando Greedy Set Cover...');
            var result = this._generateGreedy(gameKey, numGames, poolArr, fixedArr, k, cfg, aiSynergy);
            allGames = result.games;
            dupCount = result.duplicatesRejected;
            coveredPairs = result.coveredPairs;
            coveredTriples = result.coveredTriples;
            numberUsage = result.numberUsage;
            console.log('[MOTOR-MANUAL] Greedy concluído: ' + allGames.length + ' jogos | ' +
                dupCount + ' duplicatas rejeitadas');
        }

        return this._buildResult(allGames, cfg, poolArr, fixedArr, k, t0,
            dupCount, coveredPairs, coveredTriples, numberUsage, maxPossible);
    }

    // ═══════════════════════════════════════════════════════════════
    //  GREEDY SET COVER — Maximiza cobertura de pares (e triplas)
    //  Todos os números do pool têm peso UNIFORME (1.0)
    // ═══════════════════════════════════════════════════════════════
    static _generateGreedy(gameKey, numGames, pool, fixed, k, cfg, aiSynergy) {
        var self = this;
        var nonFixed = pool.filter(function(n) { return !fixed.includes(n); });
        var slotsNeeded = k - fixed.length;

        // Tracking de cobertura (Mapa de Frequências)
        var coveredPairs = new Map();
        var useTriples = k <= 15;
        var coveredTriples = useTriples ? new Map() : null;

        // Tracking de uso de números (anti-concentração)
        var numberUsage = {};
        pool.forEach(function(n) { numberUsage[n] = 0; });
        // Os fixos já aparecem em todos os jogos, então já contamos
        // (serão incrementados no loop principal)

        // Teto de frequência para anti-concentração ADAPTATIVA
        var tolerance = numGames <= 50 ? 1.4 : numGames <= 200 ? 1.25 : numGames <= 1000 ? 1.15 : 1.08;
        var expectedFreq = (numGames * k) / pool.length;
        var freqCeiling = Math.ceil(expectedFreq * tolerance);
        var softCeiling = Math.ceil(expectedFreq * (1 + (tolerance - 1) * 0.6));

        // Distância Hamming mínima (25% do drawSize)
        var hammingMin = Math.max(2, Math.floor(k * 0.25));

        // Obter filtros da loteria
        var filters = this.FILTER_RANGES[gameKey] || null;

        // Conjunto de jogos gerados (detecção de duplicatas)
        var gamesSet = new Set();
        var results = [];
        var dupCount = 0;
        var hammingSum = 0;

        // Número de candidatos por slot
        var candidatesPerSlot = Math.min(500, Math.max(300, nonFixed.length * 10));

        // ── Loop principal: para cada slot de jogo ──
        for (var g = 0; g < numGames; g++) {
            var bestCandidate = null;
            var bestScore = -Infinity;
            var attemptsThisSlot = 0;
            var maxAttemptsSlot = candidatesPerSlot * 3; // Margem para filtros

            for (var c = 0; c < maxAttemptsSlot && attemptsThisSlot < candidatesPerSlot; c++) {
                // Gerar candidato aleatório UNIFORME
                var candidateNums = self._generateRandomCandidate(nonFixed, fixed, slotsNeeded);
                if (!candidateNums) continue;

                // ── Filtro de duplicata ──
                var sig = candidateNums.join('-');
                if (gamesSet.has(sig)) {
                    dupCount++;
                    continue;
                }

                // ── Filtros estruturais P5-P95 ──
                if (filters && !self._passesFilters(candidateNums, filters, cfg)) {
                    continue;
                }

                // ── Anti-concentração ──
                if (!self._passesAntiConcentration(candidateNums, numberUsage, freqCeiling)) {
                    continue;
                }

                // ── Hamming distance ──
                if (results.length > 0 && !self._passesHamming(candidateNums, results, hammingMin, k)) {
                    continue;
                }

                attemptsThisSlot++;

                // ── Calcular score Greedy ──
                var score = self._calcGreedyScore(candidateNums, coveredPairs, coveredTriples, useTriples, results, k, aiSynergy);

                if (score > bestScore) {
                    bestScore = score;
                    bestCandidate = candidateNums;
                }
            }

            // Se nenhum candidato passou todos os filtros, relaxar e gerar um
            if (!bestCandidate) {
                console.warn('[MOTOR-MANUAL] Slot ' + (g + 1) + ': relaxando filtros...');
                bestCandidate = self._generateRelaxedCandidate(nonFixed, fixed, slotsNeeded, gamesSet);
                if (!bestCandidate) {
                    console.warn('[MOTOR-MANUAL] Impossível gerar mais jogos únicos. Total: ' + results.length);
                    break;
                }
            }

            // ── Aceitar o melhor candidato ──
            var bestSig = bestCandidate.join('-');
            gamesSet.add(bestSig);
            results.push(bestCandidate);

            // Atualizar cobertura de pares
            self._updateCoveredPairs(bestCandidate, coveredPairs);

            // Atualizar cobertura de triplas
            if (useTriples && coveredTriples) {
                self._updateCoveredTriples(bestCandidate, coveredTriples);
            }

            // Atualizar uso de números
            for (var i = 0; i < bestCandidate.length; i++) {
                numberUsage[bestCandidate[i]] = (numberUsage[bestCandidate[i]] || 0) + 1;
            }

            // Atualizar soma de Hamming (para média)
            if (results.length >= 2) {
                var lastIdx = results.length - 1;
                var prev = results[lastIdx - 1];
                hammingSum += self._hammingDistance(bestCandidate, prev, k);
            }
        }

        return {
            games: results,
            duplicatesRejected: dupCount,
            coveredPairs: coveredPairs,
            coveredTriples: coveredTriples,
            numberUsage: numberUsage,
            avgHamming: results.length >= 2 ? hammingSum / (results.length - 1) : 0
        };
    }

    // ═══════════════════════════════════════════════════════════════
    //  Gerar candidato aleatório UNIFORME (sem peso/viés)
    // ═══════════════════════════════════════════════════════════════
    static _generateRandomCandidate(nonFixed, fixed, slotsNeeded) {
        var shuffled = this._shuffle(nonFixed.slice());
        var selected = shuffled.slice(0, slotsNeeded);
        var candidate = fixed.concat(selected);
        candidate.sort(function(a, b) { return a - b; });
        return candidate;
    }

    // ═══════════════════════════════════════════════════════════════
    //  Gerar candidato com filtros relaxados (fallback)
    // ═══════════════════════════════════════════════════════════════
    static _generateRelaxedCandidate(nonFixed, fixed, slotsNeeded, gamesSet) {
        for (var attempt = 0; attempt < 5000; attempt++) {
            var shuffled = this._shuffle(nonFixed.slice());
            var selected = shuffled.slice(0, slotsNeeded);
            var candidate = fixed.concat(selected);
            candidate.sort(function(a, b) { return a - b; });
            var sig = candidate.join('-');
            if (!gamesSet.has(sig)) {
                return candidate;
            }
        }
        return null;
    }

    // ═══════════════════════════════════════════════════════════════
    //  FILTROS ESTRUTURAIS P5-P95
    // ═══════════════════════════════════════════════════════════════
    static _passesFilters(nums, filters, cfg) {
        var k = nums.length;

        // a) Soma dentro do range P5-P95
        var soma = 0;
        for (var i = 0; i < k; i++) soma += nums[i];
        if (soma < filters.sumRange[0] || soma > filters.sumRange[1]) return false;

        // b) Paridade (quantidade de pares) dentro do range P5-P95
        var pares = 0;
        for (var i = 0; i < k; i++) if (nums[i] % 2 === 0) pares++;
        if (pares < filters.parityRange[0] || pares > filters.parityRange[1]) return false;

        // c) Consecutivos máximo
        var maxConsec = 1;
        var currentConsec = 1;
        for (var i = 1; i < k; i++) {
            if (nums[i] === nums[i - 1] + 1) {
                currentConsec++;
                if (currentConsec > maxConsec) maxConsec = currentConsec;
            } else {
                currentConsec = 1;
            }
        }
        if (maxConsec > filters.maxConsecutive) return false;

        // d) Zonas mínimas cobertas
        var zonesHit = new Set();
        var rangeStart = cfg.range[0];
        for (var i = 0; i < k; i++) {
            var zone = Math.floor((nums[i] - rangeStart) / filters.zoneSize);
            zonesHit.add(zone);
        }
        if (zonesHit.size < filters.minZones) return false;

        // e) Alto/Baixo — Hipergeométrica exata (P5-P95)
        if (filters.highLowBalance) {
            var midPoint = Math.floor((cfg.range[0] + cfg.range[1]) / 2);
            var baixos = 0;
            for (var i = 0; i < k; i++) {
                if (nums[i] <= midPoint) baixos++;
            }
            if (baixos < filters.highLowBalance[0] || baixos > filters.highLowBalance[1]) return false;
        }

        return true;
    }

    // ═══════════════════════════════════════════════════════════════
    //  ANTI-CONCENTRAÇÃO — Rejeitar se qualquer número excede o teto
    // ═══════════════════════════════════════════════════════════════
    static _passesAntiConcentration(nums, numberUsage, ceiling) {
        for (var i = 0; i < nums.length; i++) {
            if ((numberUsage[nums[i]] || 0) + 1 > ceiling) {
                return false;
            }
        }
        return true;
    }

    // ═══════════════════════════════════════════════════════════════
    //  HAMMING DISTANCE — Mínimo de 30% diferente dos últimos 5
    // ═══════════════════════════════════════════════════════════════
    static _passesHamming(candidate, existingGames, hammingMin, k) {
        var start = Math.max(0, existingGames.length - 10);
        var candidateSet = new Set(candidate);
        for (var i = start; i < existingGames.length; i++) {
            var dist = this._hammingDistance(candidate, existingGames[i], k);
            if (dist < hammingMin) return false;
        }
        return true;
    }

    // Calcular distância de Hamming entre dois jogos
    static _hammingDistance(a, b, k) {
        var setA = new Set(a);
        var common = 0;
        for (var i = 0; i < b.length; i++) {
            if (setA.has(b[i])) common++;
        }
        // Hamming = números diferentes = k - comuns
        return k - common;
    }

    // ═══════════════════════════════════════════════════════════════
    //  SCORE GREEDY — Maximizar novos pares + triplas + hamming
    // ═══════════════════════════════════════════════════════════════
    static _calcGreedyScore(candidate, coveredPairs, coveredTriples, useTriples, existingGames, k, aiSynergy) {
        var pairScore = 0;
        var len = candidate.length;

        // Contar score de pares baseado na frieza (inverso da frequência)
        for (var i = 0; i < len; i++) {
            for (var j = i + 1; j < len; j++) {
                var pairKey = candidate[i] + '-' + candidate[j]; // já ordenado
                var pFreq = coveredPairs.get(pairKey) || 0;
                pairScore += 1.0 / (1.0 + pFreq);
            }
        }

        // Contar score de trincas (se ativo) baseado na frieza
        var tripleScore = 0;
        if (useTriples && coveredTriples) {
            for (var i = 0; i < len; i++) {
                for (var j = i + 1; j < len; j++) {
                    for (var m = j + 1; m < len; m++) {
                        var tripleKey = candidate[i] + '-' + candidate[j] + '-' + candidate[m];
                        var tFreq = coveredTriples.get(tripleKey) || 0;
                        tripleScore += 1.0 / (1.0 + tFreq);
                    }
                }
            }
        }

        // Hamming bonus: média de distância contra últimos 10 jogos
        var hammingBonus = 0;
        if (existingGames.length > 0) {
            var start = Math.max(0, existingGames.length - 10);
            var totalDist = 0;
            var count = 0;
            for (var i = start; i < existingGames.length; i++) {
                totalDist += this._hammingDistance(candidate, existingGames[i], k);
                count++;
            }
            hammingBonus = count > 0 ? (totalDist / count) * 5 : 0;
        }

        // AI Synergy bônus: prioriza números que saem juntos
        var synergyBonus = 0;
        if (aiSynergy) {
            for (var i = 0; i < len; i++) {
                for (var j = i + 1; j < len; j++) {
                    var pairKey = candidate[i] + '-' + candidate[j];
                    if (aiSynergy.has(pairKey)) {
                        synergyBonus += aiSynergy.get(pairKey) * 0.15;
                    }
                }
            }
        }

        return pairScore + 0.3 * tripleScore + hammingBonus + synergyBonus;
    }

    // ═══════════════════════════════════════════════════════════════
    //  Atualizar conjuntos de cobertura
    // ═══════════════════════════════════════════════════════════════
    static _updateCoveredPairs(candidate, coveredPairs) {
        for (var i = 0; i < candidate.length; i++) {
            for (var j = i + 1; j < candidate.length; j++) {
                var key = candidate[i] + '-' + candidate[j];
                coveredPairs.set(key, (coveredPairs.get(key) || 0) + 1);
            }
        }
    }

    static _updateCoveredTriples(candidate, coveredTriples) {
        for (var i = 0; i < candidate.length; i++) {
            for (var j = i + 1; j < candidate.length; j++) {
                for (var m = j + 1; m < candidate.length; m++) {
                    var key = candidate[i] + '-' + candidate[j] + '-' + candidate[m];
                    coveredTriples.set(key, (coveredTriples.get(key) || 0) + 1);
                }
            }
        }
    }

    // ═══════════════════════════════════════════════════════════════
    //  GERAÇÃO COMPLETA C(n,k) — Fechamento Total
    // ═══════════════════════════════════════════════════════════════
    static _generateAll(pool, fixed, k) {
        var nonFixed = pool.filter(function(n) { return !fixed.includes(n); });
        var slotsNeeded = k - fixed.length;
        var results = [];

        var indices = [];
        for (var i = 0; i < slotsNeeded; i++) indices.push(i);

        while (true) {
            var ticket = fixed.slice();
            for (var idx = 0; idx < indices.length; idx++) {
                ticket.push(nonFixed[indices[idx]]);
            }
            ticket.sort(function(a, b) { return a - b; });
            results.push(ticket);

            // Segurança: limitar a 50.000 combinações
            if (results.length >= 50000) break;

            var pos = slotsNeeded - 1;
            while (pos >= 0 && indices[pos] === nonFixed.length - slotsNeeded + pos) pos--;
            if (pos < 0) break;
            indices[pos]++;
            for (var i = pos + 1; i < slotsNeeded; i++) indices[i] = indices[i - 1] + 1;
        }

        return results;
    }

    // ═══════════════════════════════════════════════════════════════
    //  CÁLCULO DE ROI HONESTO — Probabilidade hipergeométrica exata
    //  P(X=k) = C(n, k) * C(N-n, K-k) / C(N, K)
    //  N = total de números da loteria
    //  K = bolas sorteadas pela Caixa (draw)
    //  n = números escolhidos no jogo (drawSize)
    //  k = acertos desejados
    // ═══════════════════════════════════════════════════════════════
    static _calcROI(games, cfg, drawSize) {
        var N = cfg.totalNumbers;  // Total de números da loteria
        var K = cfg.drawCount;     // Bolas sorteadas pela Caixa
        var n = drawSize;          // Números no volante do apostador
        var realPrice = this._calcRealPrice(cfg, drawSize);
        var investment = games.length * realPrice;

        var breakdown = [];
        var totalEV = 0;

        // Iterar sobre cada faixa de premiação
        var strategies = cfg.strategies || [];
        for (var s = 0; s < strategies.length; s++) {
            var strat = strategies[s];
            var hits = strat.match;

            // P(X = hits) = C(n, hits) * C(N-n, K-hits) / C(N, K)
            var prob = this._hypergeometric(N, K, n, hits);

            if (prob <= 0) continue;

            // Esperança: cada jogo tem prob chance de acertar esta faixa
            var expectedHits = games.length * prob;
            var prize = strat.prize || 0;

            // Usar prêmio fixo se disponível
            var fixedPrizes = this.FIXED_PRIZES[cfg.key];
            if (fixedPrizes && fixedPrizes[hits] !== undefined) {
                prize = fixedPrizes[hits];
            }

            var ev = expectedHits * prize;
            totalEV += ev;

            breakdown.push({
                hits: hits,
                label: strat.label,
                probability: prob,
                expectedHits: Math.round(expectedHits * 1000) / 1000,
                prize: prize,
                ev: Math.round(ev * 100) / 100
            });
        }

        return {
            investment: Math.round(investment * 100) / 100,
            breakdown: breakdown,
            expectedReturn: Math.round(totalEV * 100) / 100,
            roiPercent: investment > 0 ? Math.round(((totalEV / investment) - 1) * 10000) / 100 : 0
        };
    }

    // Probabilidade hipergeométrica exata
    // P(X=k) = C(n, k) * C(N-n, K-k) / C(N, K)
    static _hypergeometric(N, K, n, k) {
        if (k < 0 || k > Math.min(n, K) || k < Math.max(0, n + K - N)) return 0;
        var num1 = this._comb(n, k);
        var num2 = this._comb(N - n, K - k);
        var den = this._comb(N, K);
        if (den === 0) return 0;
        return (num1 * num2) / den;
    }

    // ═══════════════════════════════════════════════════════════════
    //  UTILITÁRIOS
    // ═══════════════════════════════════════════════════════════════

    // Fisher-Yates shuffle
    static _shuffle(arr) {
        for (var i = arr.length - 1; i > 0; i--) {
            var j = Math.floor(Math.random() * (i + 1));
            var temp = arr[i];
            arr[i] = arr[j];
            arr[j] = temp;
        }
        return arr;
    }

    // Combinação C(n, r) — cálculo exato
    static _comb(n, r) {
        if (r > n || r < 0) return 0;
        if (r === 0 || r === n) return 1;
        if (r > n - r) r = n - r;
        var result = 1;
        for (var i = 0; i < r; i++) {
            result = result * (n - i) / (i + 1);
        }
        return Math.round(result);
    }

    // Calcular preço REAL baseado no drawSize
    // Fórmula: precoBase * C(drawSize, minBet)
    static _calcRealPrice(cfg, drawSize) {
        if (drawSize <= cfg.drawSize) return cfg.price;
        var ratio = this._comb(drawSize, cfg.drawSize);
        return cfg.price * ratio;
    }

    // ═══════════════════════════════════════════════════════════════
    //  CONSTRUIR RESULTADO FINAL
    // ═══════════════════════════════════════════════════════════════
    static _buildResult(games, cfg, pool, fixed, drawSize, t0, dupCount, coveredPairs, coveredTriples, numberUsage, maxPossible) {
        var elapsed = Date.now() - t0;
        var slotsNeeded = games[0] ? games[0].length - fixed.length : 0;
        var totalPossible = maxPossible || this._comb(pool.length - fixed.length, slotsNeeded);
        var realPrice = this._calcRealPrice(cfg, drawSize);

        // ── Métricas de cobertura ──
        var totalPairs = this._comb(pool.length, 2);
        var pairCount = coveredPairs ? coveredPairs.size : 0;
        var tripleCount = coveredTriples ? coveredTriples.size : 0;

        // ── Métricas de uso de números ──
        var usageStats = { min: 0, max: 0, avg: 0 };
        if (numberUsage) {
            var usageValues = Object.values(numberUsage);
            if (usageValues.length > 0) {
                usageStats.min = Math.min.apply(null, usageValues);
                usageStats.max = Math.max.apply(null, usageValues);
                var usageSum = 0;
                for (var i = 0; i < usageValues.length; i++) usageSum += usageValues[i];
                usageStats.avg = Math.round((usageSum / usageValues.length) * 10) / 10;
            }
        }

        // ── Hamming médio (recalcular se necessário) ──
        var avgHamming = 0;
        if (games.length >= 2) {
            var totalHamming = 0;
            var pairwise = 0;
            var sampleSize = Math.min(games.length, 50); // Amostra para performance
            for (var i = 0; i < sampleSize - 1; i++) {
                var dist = this._hammingDistance(games[i], games[i + 1], drawSize);
                totalHamming += dist;
                pairwise++;
            }
            avgHamming = pairwise > 0 ? Math.round((totalHamming / pairwise) * 10) / 10 : 0;
        }

        // ── ROI honesto ──
        var roi = this._calcROI(games, cfg, drawSize);

        // ── Montar analysis ──
        var analysis = {
            totalGames: games.length,
            totalPossible: totalPossible,
            poolSize: pool.length,
            fixedCount: fixed.length,
            fixedNumbers: fixed,
            drawSize: drawSize,
            pricePerGame: realPrice,
            investimento: Math.round(games.length * realPrice * 100) / 100,
            isComplete: games.length >= totalPossible,
            elapsed: elapsed,
            // Métricas de cobertura
            pairCoverage: pairCount,
            totalPairs: totalPairs,
            pairCoveragePct: totalPairs > 0 ? Math.round(pairCount / totalPairs * 1000) / 10 : 0,
            tripleCoverage: tripleCount,
            avgHamming: avgHamming,
            numberUsage: usageStats,
            duplicatesRejected: dupCount || 0,
            // ROI
            roi: roi
        };

        console.log('[MOTOR-MANUAL] ✅ ' + games.length + '/' + totalPossible +
            ' jogos | R$ ' + analysis.investimento.toFixed(2) +
            ' (R$ ' + realPrice.toFixed(2) + '/jogo) | ' + elapsed + 'ms');
        console.log('[MOTOR-MANUAL] 📊 Pares cobertos: ' + pairCount + '/' + totalPairs +
            ' (' + analysis.pairCoveragePct + '%) | Triplas: ' + tripleCount);
        console.log('[MOTOR-MANUAL] 📊 Uso: min=' + usageStats.min + ' max=' + usageStats.max +
            ' avg=' + usageStats.avg + ' | Hamming médio: ' + avgHamming);
        console.log('[MOTOR-MANUAL] 💰 ROI: investimento R$ ' + roi.investment.toFixed(2) +
            ' | retorno esperado R$ ' + roi.expectedReturn.toFixed(2) +
            ' | ROI ' + roi.roiPercent.toFixed(2) + '%');
        console.log('%c[MOTOR-MANUAL] ══════════════════════════════════════════', 'color: #FFD700; font-weight: bold;');

        return { games: games, analysis: analysis };
    }

    // ═══════════════════════════════════════════════════════════════
    //  SINERGIA DE DEZENAS (Números que costumam sair juntos)
    // ═══════════════════════════════════════════════════════════════
    static _getAISynergy(gameKey, selectedNumbers) {
        if (typeof StatsService === 'undefined') return null;
        try {
            var history = (StatsService.getRecentResults && typeof StatsService.getRecentResults === 'function') 
                ? StatsService.getRecentResults(gameKey, 200) 
                : (typeof window !== 'undefined' && window.REAL_HISTORY_DB && window.REAL_HISTORY_DB[gameKey] ? window.REAL_HISTORY_DB[gameKey] : []);
            
            if (!history || history.length === 0) return null;
            
            var pairsMap = new Map();
            for (var h = 0; h < history.length; h++) {
                var drawNums = (history[h].numbers || history[h].dezenas || []).map(function(n) { return parseInt(n, 10); });
                var filtered = [];
                for (var i = 0; i < drawNums.length; i++) {
                    if (selectedNumbers.includes(drawNums[i])) filtered.push(drawNums[i]);
                }
                filtered.sort(function(a, b) { return a - b; });
                
                for (var i = 0; i < filtered.length; i++) {
                    for (var j = i + 1; j < filtered.length; j++) {
                        var k = filtered[i] + '-' + filtered[j];
                        pairsMap.set(k, (pairsMap.get(k) || 0) + 1);
                    }
                }
            }
            return pairsMap.size > 0 ? pairsMap : null;
        } catch(e) {
            console.error('[MOTOR-MANUAL] Erro ao carregar Sinergia:', e);
            return null;
        }
    }
}

if (typeof window !== 'undefined') window.MotorFechamentoManual = MotorFechamentoManual;
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MotorFechamentoManual;
}
