/**
 * ClosingEngine v3.1 — Motor de Fechamento Matemático L99
 * 
 * CORREÇÃO CRÍTICA v3.1:
 *   GARANTIA CONDICIONAL: Se T é a garantia e F são fixos,
 *   a garantia efetiva no espaço variável = T - F
 *   
 *   Fixar números REDUZ variáveis → REDUZ apostas!
 * 
 * LÓGICA:
 *   - Jogador seleciona N números e fixa F deles
 *   - Cada jogo = F fixos + (betSize - F) variáveis
 *   - Para garantir T acertos: precisa (T - F) acertos variáveis
 *   - Cobrir todos os (T-F)-subconjuntos de variáveis
 *   - Lower bound = C(variableCount, T-F) / C(slotsVariable, T-F)
 * 
 * EXEMPLOS (N=20, F=6, betSize=15):
 *   G15 = 2.002 jogos (sem fixos = 15.504)
 *   G14 = ~334 jogos (sem fixos = ~2.584)
 *   G13 = ~96 jogos  (sem fixos = ~780)
 *   G12 = ~36 jogos
 *   G11 = ~16 jogos
 * 
 * ALGORITMO HÍBRIDO:
 *   - Greedy Exato: candidatos ≤ 25.000 E subconjuntos ≤ 200.000
 *   - Greedy Amostrado: para espaços maiores
 *   - Heurístico Verificado: para espaços enormes
 */

class ClosingEngine {

    // ═══════════════════════════════════════════
    //  COMBINATÓRIA: C(n,k)
    // ═══════════════════════════════════════════
    static nCr(n, k) {
        if (k < 0 || k > n) return 0;
        if (k === 0 || k === n) return 1;
        if (k > n / 2) k = n - k;
        let r = 1;
        for (let i = 1; i <= k; i++) {
            r = r * (n - i + 1) / i;
        }
        return Math.round(r);
    }

    // ═══════════════════════════════════════════
    //  OBTER betSize CORRETO PARA CADA LOTERIA
    // ═══════════════════════════════════════════
    static getBetSize(gameKey) {
        const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        if (!game) return 6;
        switch (gameKey) {
            case 'timemania': return game.minBet;
            case 'lotomania': return game.minBet;
            default: return game.draw;
        }
    }

    static effectiveGuarantee(guarantee, fixedCount, gameKey = 'megasena', numSelected = 0) {
        // Garantia de Fechamento Condicional Honesta: Assume que acertamos as dezenas fixas.
        // Portanto, a garantia necessária no espaço das dezenas variáveis é exatamente guarantee - fixedCount.
        return Math.max(1, guarantee - fixedCount);
    }

    // ═══════════════════════════════════════════
    //  GERAR TODOS SUBCONJUNTOS DE TAMANHO K
    // ═══════════════════════════════════════════
    static _generateSubsets(arr, k) {
        const result = [];
        const n = arr.length;
        if (k > n || k <= 0) return result;
        const indices = [];
        for (let i = 0; i < k; i++) indices.push(i);
        while (true) {
            result.push(indices.map(i => arr[i]));
            let i = k - 1;
            while (i >= 0 && indices[i] === n - k + i) i--;
            if (i < 0) break;
            indices[i]++;
            for (let j = i + 1; j < k; j++) indices[j] = indices[j - 1] + 1;
        }
        return result;
    }

    // ═══════════════════════════════════════════
    //  GERAR N SUBCONJUNTOS ALEATÓRIOS ÚNICOS
    // ═══════════════════════════════════════════
    static _generateRandomSubsets(arr, k, maxCount) {
        const n = arr.length;
        if (k > n || k <= 0) return [];
        if (this.nCr(n, k) <= maxCount) return this._generateSubsets(arr, k);

        const result = [];
        const seen = new Set();
        let attempts = 0;
        const maxAttempts = maxCount * 8;
        while (result.length < maxCount && attempts < maxAttempts) {
            attempts++;
            const available = [...Array(n).keys()];
            const indices = [];
            for (let i = 0; i < k; i++) {
                const randIdx = i + Math.floor(Math.random() * (n - i));
                [available[i], available[randIdx]] = [available[randIdx], available[i]];
                indices.push(available[i]);
            }
            indices.sort((a, b) => a - b);
            const key = indices.join(',');
            if (!seen.has(key)) {
                seen.add(key);
                result.push(indices.map(i => arr[i]));
            }
        }
        return result;
    }

    static _subsetKey(subset) {
        return subset.join(',');
    }

    // ═══════════════════════════════════════════════════════
    //  ESTIMAR JOGOS (COM FIXOS — GARANTIA CONDICIONAL)
    //  
    //  Fórmula: C(variableCount, effG) / C(slotsVariable, effG) × factor
    //  Onde effG = guarantee - fixedCount
    // ═══════════════════════════════════════════════════════
    static estimateGames(numSelected, guarantee, betSize = 6, fixedCount = 0, gameKey = 'megasena') {
        if (numSelected < betSize) return 0;

        const slotsVariable = betSize - fixedCount;
        const variableCount = numSelected - fixedCount;
        const effG = this.effectiveGuarantee(guarantee, fixedCount, gameKey, numSelected);

        // Se effG = slotsVariable: ALL combinações
        if (effG === slotsVariable) {
            return this.nCr(variableCount, slotsVariable);
        }

        // Fórmula principal
        const totalSubsets = this.nCr(variableCount, effG);
        const coversPerGame = this.nCr(slotsVariable, effG);

        if (coversPerGame === 0) return this.nCr(variableCount, slotsVariable);

        const lowerBound = Math.ceil(totalSubsets / coversPerGame);

        // Fator de ajuste para greedy
        const ratio = effG / slotsVariable;
        let factor;
        if (gameKey === 'lotomania' && guarantee >= 19) {
            factor = guarantee === 20 ? 2.56 : 2.0;
        } else if (ratio >= 0.9) factor = 1.5;
        else if (ratio >= 0.7) factor = 1.35;
        else if (ratio >= 0.5) factor = 1.2;
        else factor = 1.1;

        return Math.max(lowerBound, Math.ceil(lowerBound * factor));
    }

    // ═══════════════════════════════════════════════════════════════
    //  MÉTODO PRINCIPAL: GERAR FECHAMENTO v3.1
    //  CORRIGIDO: Fixos REDUZEM variáveis → REDUZEM apostas
    // ═══════════════════════════════════════════════════════════════
    static generateClosure(selectedNumbers, guarantee, betSize = 6, gameKey = 'megasena', fixedNumbers = [], requestedQuantity = 0) {
        const t0 = Date.now();
        const nums = [...selectedNumbers].sort((a, b) => a - b);
        const N = nums.length;
        const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        const pricePerGame = game ? game.price : 6.00;
        const fixedSet = new Set(fixedNumbers || []);
        const fixedCount = fixedSet.size;

        if (gameKey && typeof GAMES !== 'undefined') {
            betSize = this.getBetSize(gameKey);
        }

        const slotsVariable = betSize - fixedCount;
        const fixedArr = nums.filter(n => fixedSet.has(n));
        const variableNums = nums.filter(n => !fixedSet.has(n));
        const variableCount = variableNums.length;
        const totalCandidates = slotsVariable > 0 ? this.nCr(variableCount, slotsVariable) : 1;
        const effG = this.effectiveGuarantee(guarantee, fixedCount, gameKey, N);

        console.log('[CLOSING-v3.1] ══════════════════════════════════════');
        console.log('[CLOSING-v3.1] 🎯 Motor Fechamento v3.1 (Condicional)');
        console.log('[CLOSING-v3.1] Jogo: ' + gameKey + ' | N=' + N + ' | BetSize=' + betSize + ' | Garantia=' + guarantee);
        if (fixedCount > 0) {
            console.log('[CLOSING-v3.1] 📌 Fixos (' + fixedCount + '): [' + fixedArr.join(', ') + ']');
            console.log('[CLOSING-v3.1] 🔢 Variáveis: ' + variableCount + ' | Slots: ' + slotsVariable);
            console.log('[CLOSING-v3.1] 📐 Garantia Efetiva: ' + guarantee + ' - ' + fixedCount + ' = ' + effG + ' acertos variáveis');
        }
        console.log('[CLOSING-v3.1] 📊 Candidatos: C(' + variableCount + ',' + slotsVariable + ') = ' + totalCandidates.toLocaleString('pt-BR'));

        // ━━ VALIDAÇÕES ━━
        if (N < betSize) {
            return this._errorResult('Selecione pelo menos ' + betSize + ' números.', guarantee, nums, fixedSet);
        }
        if (fixedCount >= betSize) {
            return this._errorResult('Fixos (' + fixedCount + ') devem ser menor que tamanho do jogo (' + betSize + ').', guarantee, nums, fixedSet);
        }
        if (guarantee > betSize) {
            return this._errorResult('Garantia (' + guarantee + ') não pode ser maior que ' + betSize + '.', guarantee, nums, fixedSet);
        }
        if (guarantee < 3) {
            return this._errorResult('Garantia mínima: 3 acertos.', guarantee, nums, fixedSet);
        }
        if (variableCount < slotsVariable) {
            return this._errorResult('Selecione mais números (precisa ' + slotsVariable + ' variáveis, tem ' + variableCount + ').', guarantee, nums, fixedSet);
        }

        // ━━ CASO: effG ≤ 0 → 1 jogo basta ━━
        if (effG <= 0) {
            const oneGame = [...fixedArr, ...variableNums.slice(0, slotsVariable)].sort((a, b) => a - b);
            return {
                games: [oneGame], guarantee, totalGames: 1,
                totalSubsets: 1, covered: 1, coveragePct: 100,
                cost: pricePerGame, mode: 'TRIVIAL', elapsed: Date.now() - t0,
                selectedNumbers: nums, fixedNumbers: [...fixedSet],
                confidence: 100, effectiveGuarantee: effG,
                msg: 'Com ' + fixedCount + ' fixos, garantia de ' + guarantee + ' acertos é coberta com apenas 1 jogo!'
            };
        }

        // ━━ CASO: Fechamento Completo (effG = slotsVariable) ━━
        if (effG === slotsVariable) {
            if (totalCandidates > 500000) {
                return {
                    games: [], guarantee, totalGames: totalCandidates,
                    totalSubsets: totalCandidates, covered: 0, coveragePct: 100,
                    cost: totalCandidates * pricePerGame,
                    error: 'Fechamento completo de ' + guarantee + ' acertos' +
                        (fixedCount > 0 ? ' (' + fixedCount + ' fixos)' : '') +
                        ' geraria ' + totalCandidates.toLocaleString('pt-BR') + ' jogos (R$ ' +
                        (totalCandidates * pricePerGame).toLocaleString('pt-BR', { minimumFractionDigits: 2 }) +
                        '). Reduza números selecionados ou use garantia menor.',
                    selectedNumbers: nums, fixedNumbers: [...fixedSet]
                };
            }

            console.log('[CLOSING-v3.1] Modo: COMPLETO → ' + totalCandidates + ' jogos');
            const games = this._buildAllCandidates(fixedArr, variableNums, slotsVariable);
            return {
                games, guarantee, totalGames: games.length,
                totalSubsets: totalCandidates, covered: totalCandidates,
                coveragePct: 100, cost: games.length * pricePerGame,
                mode: 'COMPLETO', elapsed: Date.now() - t0,
                selectedNumbers: nums, fixedNumbers: [...fixedSet],
                confidence: 100, effectiveGuarantee: effG
            };
        }

        // ━━ INJEÇÃO DE INTELIGÊNCIA ARTIFICIAL (SYNERGY) ━━
        const aiSynergy = this._getAISynergy(gameKey, nums);
        if (aiSynergy) {
            console.log('[CLOSING-v3.1] 🧠 IA Sinergética Ativada: ' + gameKey + ' (Scores + Duplas Históricas)');
        }

        // ━━ SELECIONAR ALGORITMO ━━
        const totalVarTSubsets = this.nCr(variableCount, effG);
        console.log('[CLOSING-v3.1] Subconjuntos efetivos: C(' + variableCount + ',' + effG + ') = ' + totalVarTSubsets.toLocaleString('pt-BR'));

        if (totalCandidates <= 25000 && totalVarTSubsets <= 200000) {
            console.log('[CLOSING-v3.1] → GREEDY EXATO');
            return this._greedyExact(fixedArr, variableNums, slotsVariable, effG, guarantee, betSize, pricePerGame, t0, gameKey, nums, fixedSet, aiSynergy, requestedQuantity);
        } else {
            console.log('[CLOSING-v3.1] → GREEDY AMOSTRADO');
            return this._greedySampled(fixedArr, variableNums, slotsVariable, effG, guarantee, betSize, pricePerGame, t0, gameKey, nums, fixedSet, aiSynergy, requestedQuantity);
        }
    }

    // ═══════════════════════════════════════════
    //  CONSTRUIR TODOS OS CANDIDATOS
    // ═══════════════════════════════════════════
    static _buildAllCandidates(fixedArr, variableNums, slotsVariable) {
        const variableCombos = this._generateSubsets(variableNums, slotsVariable);
        return variableCombos.map(combo => [...fixedArr, ...combo].sort((a, b) => a - b));
    }

    // ═══════════════════════════════════════════
    //  IA SINERGÉTICA (Scores e Duplas/Trios)
    // ═══════════════════════════════════════════
    static _getAISynergy(gameKey, selectedNumbers) {
        if (typeof NovaEraEngine === 'undefined' || typeof StatsService === 'undefined') return null;
        try {
            const history = (StatsService.getRecentResults && typeof StatsService.getRecentResults === 'function') 
                ? StatsService.getRecentResults(gameKey, 200) 
                : (typeof window !== 'undefined' && window.REAL_HISTORY_DB && window.REAL_HISTORY_DB[gameKey] ? window.REAL_HISTORY_DB[gameKey] : []);
            
            if (!history || history.length === 0) return null;
            const profile = NovaEraEngine.getProfile(gameKey);
            const range = profile.range || [1, 60];
            const scoresInfo = NovaEraEngine._scoreAllNumbers(gameKey, profile, history, range[0], range[1], range[1] - range[0] + 1);
            
            const pairMatrix = {};
            selectedNumbers.forEach(n => { pairMatrix[n] = {}; selectedNumbers.forEach(m => pairMatrix[n][m] = 0); });
            
            history.forEach(draw => {
                const nums = draw.numeros || draw;
                const match = nums.filter(n => selectedNumbers.includes(n));
                for(let i=0; i<match.length; i++) {
                    for(let j=i+1; j<match.length; j++) {
                        pairMatrix[match[i]][match[j]]++;
                        pairMatrix[match[j]][match[i]]++;
                    }
                }
            });
            
            return { scores: scoresInfo.scores, pairs: pairMatrix };
        } catch(e) {
            console.error('[CLOSING-AI] Erro ao injetar IA', e);
            return null;
        }
    }

    static _evalSynergy(vp, fixedArr, aiSynergy) {
        let score = 0;
        const combo = [...fixedArr, ...vp];
        combo.forEach(n => {
            score += (aiSynergy.scores[n] || 1.0);
        });
        // Peso das duplas que caem juntas
        for(let i=0; i<combo.length; i++) {
            for(let j=i+1; j<combo.length; j++) {
                if (aiSynergy.pairs[combo[i]] && aiSynergy.pairs[combo[i]][combo[j]]) {
                    score += aiSynergy.pairs[combo[i]][combo[j]] * 0.15;
                }
            }
        }
        return score;
    }

    // ═══════════════════════════════════════════════════════
    //  GREEDY EXATO: Cobertura exata de effG-subconjuntos
    // ═══════════════════════════════════════════════════════
    static _greedyExact(fixedArr, variableNums, slotsVariable, effG, guarantee, betSize, pricePerGame, t0, gameKey, allNums, fixedSet, aiSynergy, requestedQuantity = 0) {
        const variableCount = variableNums.length;

        // 1. Enumerar TODOS os effG-subconjuntos de variáveis
        const allTSubsets = this._generateSubsets(variableNums, effG);
        const totalSubsets = allTSubsets.length;
        console.log('[CLOSING-v3.1] Subconjuntos a cobrir: ' + totalSubsets);

        const subsetKeyToIndex = new Map();
        for (let i = 0; i < totalSubsets; i++) {
            subsetKeyToIndex.set(this._subsetKey(allTSubsets[i]), i);
        }

        const uncovered = new Set();
        for (let i = 0; i < totalSubsets; i++) uncovered.add(i);

        // 2. Enumerar TODOS os candidatos (parte variável)
        let allVariableParts = this._generateSubsets(variableNums, slotsVariable);
        
        // ORDENAÇÃO POR IA (Trios/Duplas/Calor)
        if (aiSynergy) {
            allVariableParts.forEach(vp => { vp._synergy = this._evalSynergy(vp, fixedArr, aiSynergy); });
            allVariableParts.sort((a, b) => b._synergy - a._synergy);
            // Limpa cache de sinergia para economizar memoria
            allVariableParts.forEach(vp => delete vp._synergy);
        }
        
        console.log('[CLOSING-v3.1] Candidatos: ' + allVariableParts.length);

        // 3. Pré-calcular coberturas
        const candidateCovers = [];
        for (const vp of allVariableParts) {
            const covers = new Set();
            const tSubs = this._generateSubsets(vp, effG);
            for (const sub of tSubs) {
                const idx = subsetKeyToIndex.get(this._subsetKey(sub));
                if (idx !== undefined) covers.add(idx);
            }
            candidateCovers.push(covers);
        }

        // 4. Greedy Set Cover
        const selectedIndices = [];
        const usedCandidates = new Set();
        const TIMEOUT = 120000;

        const maxGames = requestedQuantity > 0 ? requestedQuantity : Infinity;
        while (uncovered.size > 0 && selectedIndices.length < maxGames && (Date.now() - t0) < TIMEOUT) {
            let bestCandidate = -1;
            let bestCount = 0;
            for (let c = 0; c < allVariableParts.length; c++) {
                if (usedCandidates.has(c)) continue;
                let count = 0;
                for (const idx of candidateCovers[c]) {
                    if (uncovered.has(idx)) count++;
                }
                if (count > bestCount) {
                    bestCount = count;
                    bestCandidate = c;
                }
            }
            if (bestCandidate === -1 || bestCount === 0) break;
            selectedIndices.push(bestCandidate);
            usedCandidates.add(bestCandidate);
            for (const idx of candidateCovers[bestCandidate]) uncovered.delete(idx);

            if (selectedIndices.length % 50 === 0) {
                console.log('[CLOSING-v3.1] → ' + selectedIndices.length + ' jogos (' + ((totalSubsets - uncovered.size) / totalSubsets * 100).toFixed(1) + '%)');
            }
        }

        // 5. Montar jogos
        const games = selectedIndices.map(idx =>
            [...fixedArr, ...allVariableParts[idx]].sort((a, b) => a - b)
        );
        const covered = totalSubsets - uncovered.size;
        const coveragePct = totalSubsets > 0 ? (covered / totalSubsets * 100) : 0;
        const elapsed = Date.now() - t0;

        console.log('[CLOSING-v3.1] ✅ ' + games.length + ' jogos | Cobertura: ' + coveragePct.toFixed(1) + '% | ' + elapsed + 'ms');

        return {
            games, guarantee, totalGames: games.length,
            totalSubsets, covered, coveragePct: parseFloat(coveragePct.toFixed(2)),
            cost: games.length * pricePerGame, mode: 'GREEDY_EXATO',
            elapsed, selectedNumbers: allNums, fixedNumbers: [...fixedSet],
            confidence: coveragePct >= 99.9 ? 100 : parseFloat(coveragePct.toFixed(1)),
            effectiveGuarantee: effG
        };
    }

    // ═══════════════════════════════════════════════════════
    //  GREEDY AMOSTRADO: Para espaços médios
    // ═══════════════════════════════════════════════════════
    static _greedySampled(fixedArr, variableNums, slotsVariable, effG, guarantee, betSize, pricePerGame, t0, gameKey, allNums, fixedSet, aiSynergy, requestedQuantity = 0) {
        const variableCount = variableNums.length;
        const TIMEOUT = 120000;

        // 1. Enumerar ou amostrar effG-subconjuntos
        const totalVarTSubsets = this.nCr(variableCount, effG);
        let sampledTSubsets;
        let useFullCoverage = totalVarTSubsets <= 200000;
        if (useFullCoverage) {
            sampledTSubsets = this._generateSubsets(variableNums, effG);
        } else {
            const sampleSize = totalVarTSubsets > 10000000 ? 50000 : 100000;
            sampledTSubsets = this._generateRandomSubsets(variableNums, effG, sampleSize);
        }

        const subsetKeyToIndex = new Map();
        for (let i = 0; i < sampledTSubsets.length; i++) {
            subsetKeyToIndex.set(this._subsetKey(sampledTSubsets[i]), i);
        }
        const uncovered = new Set();
        for (let i = 0; i < sampledTSubsets.length; i++) uncovered.add(i);

        // 2. Greedy iterativo com lotes
        const selectedGames = [];
        const MAX_ROUNDS = 500000; // Aumentado para permitir fechamentos completos sem limites baixos
        let rounds = 0;

        // Otimização: Containment Check quando gerar subconjuntos for muito lento
        const subsetsPerCandidate = this.nCr(slotsVariable, effG);
        const useContainmentCheck = subsetsPerCandidate > 1000;

        // Ajustar tamanho do lote de candidatos dinamicamente para velocidade
        const BATCH_SIZE = useContainmentCheck ? 1000 : 15000;

        const maxGames = requestedQuantity > 0 ? requestedQuantity : Infinity;
        while (selectedGames.length < maxGames && rounds < MAX_ROUNDS && (Date.now() - t0) < TIMEOUT) {
            if (uncovered.size === 0) {
                if (useFullCoverage) break;
                const newSample = this._generateRandomSubsets(variableNums, effG, sampleSize);
                sampledTSubsets = newSample;
                subsetKeyToIndex.clear();
                for (let i = 0; i < sampledTSubsets.length; i++) {
                    subsetKeyToIndex.set(this._subsetKey(sampledTSubsets[i]), i);
                    uncovered.add(i);
                }
            }
            rounds++;
            let candidates;
            if (effG >= 6 && uncovered.size > 0) {
                candidates = this._generateDirectedCandidates(uncovered, sampledTSubsets, variableNums, slotsVariable, 50);
            } else {
                candidates = this._generateRandomSubsets(variableNums, slotsVariable, BATCH_SIZE);
            }
            if (aiSynergy) {
                candidates.forEach(vp => { vp._synergy = this._evalSynergy(vp, fixedArr, aiSynergy); });
                candidates.sort((a, b) => b._synergy - a._synergy);
                candidates.forEach(vp => delete vp._synergy);
            }

            let bestCandidate = null;
            let bestCount = 0;

            if (useContainmentCheck) {
                // Checagem de inclusão invertida ultra rápida (evita crash do browser)
                for (const candidate of candidates) {
                    let count = 0;
                    const inCand = new Array(105).fill(false);
                    for (let i = 0; i < candidate.length; i++) inCand[candidate[i]] = true;
                    
                    for (const idx of uncovered) {
                        const sub = sampledTSubsets[idx];
                        let contained = true;
                        for (let i = 0; i < sub.length; i++) {
                            if (!inCand[sub[i]]) {
                                contained = false;
                                break;
                            }
                        }
                        if (contained) count++;
                    }
                    if (count > bestCount) {
                        bestCount = count;
                        bestCandidate = candidate;
                    }
                }
            } else {
                for (const candidate of candidates) {
                    const tSubs = this._generateSubsets(candidate, effG);
                    let count = 0;
                    for (const sub of tSubs) {
                        const idx = subsetKeyToIndex.get(this._subsetKey(sub));
                        if (idx !== undefined && uncovered.has(idx)) count++;
                    }
                    if (count > bestCount) {
                        bestCount = count;
                        bestCandidate = candidate;
                    }
                }
            }

            if (!bestCandidate || bestCount === 0) {
                // Candidato direcionado
                const uncovIdx = uncovered.values().next().value;
                const targetSub = sampledTSubsets[uncovIdx];
                if (targetSub) {
                    const candidate = new Set(targetSub);
                    const remaining = variableNums.filter(n => !candidate.has(n)).sort(() => Math.random() - 0.5);
                    for (const num of remaining) {
                        if (candidate.size >= slotsVariable) break;
                        candidate.add(num);
                    }
                    bestCandidate = [...candidate].sort((a, b) => a - b);
                } else continue;
            }

            selectedGames.push([...fixedArr, ...bestCandidate].sort((a, b) => a - b));

            // Remover do uncovered
            if (useContainmentCheck) {
                const inCand = new Array(105).fill(false);
                for (let i = 0; i < bestCandidate.length; i++) inCand[bestCandidate[i]] = true;
                
                for (const idx of uncovered) {
                    const sub = sampledTSubsets[idx];
                    let contained = true;
                    for (let i = 0; i < sub.length; i++) {
                        if (!inCand[sub[i]]) {
                            contained = false;
                            break;
                        }
                    }
                    if (contained) {
                        uncovered.delete(idx);
                    }
                }
            } else {
                const tSubs = this._generateSubsets(bestCandidate, effG);
                for (const sub of tSubs) {
                    const idx = subsetKeyToIndex.get(this._subsetKey(sub));
                    if (idx !== undefined) uncovered.delete(idx);
                }
            }

            if (selectedGames.length % 20 === 0) {
                console.log('[CLOSING-v3.1] → ' + selectedGames.length + ' jogos (' + ((sampledTSubsets.length - uncovered.size) / sampledTSubsets.length * 100).toFixed(1) + '%)');
            }
        }

        const coveragePct = ((sampledTSubsets.length - uncovered.size) / sampledTSubsets.length * 100);
        const elapsed = Date.now() - t0;

        console.log('[CLOSING-v3.1] ✅ ' + selectedGames.length + ' jogos | Cobertura: ' + coveragePct.toFixed(1) + '% | ' + elapsed + 'ms');

        return {
            games: selectedGames, guarantee, totalGames: selectedGames.length,
            totalSubsets: this.nCr(allNums.length, guarantee),
            covered: Math.round(sampledTSubsets.length * coveragePct / 100),
            coveragePct: parseFloat(coveragePct.toFixed(2)),
            cost: selectedGames.length * pricePerGame, mode: 'GREEDY_AMOSTRADO',
            elapsed, selectedNumbers: allNums, fixedNumbers: [...fixedSet],
            confidence: parseFloat(Math.min(100, coveragePct).toFixed(1)),
            effectiveGuarantee: effG,
            note: useFullCoverage ? 'Cobertura exata.' : 'Cobertura estimada por ' + sampledTSubsets.length.toLocaleString('pt-BR') + ' amostras.'
        };
    }

    // ═══════════════════════════════════════════════════════
    //  HEURÍSTICO VERIFICADO: Para espaços enormes
    // ═══════════════════════════════════════════════════════
    static _heuristicVerified(fixedArr, variableNums, slotsVariable, effG, guarantee, betSize, pricePerGame, t0, gameKey, allNums, fixedSet, aiSynergy, requestedQuantity = 0) {
        const variableCount = variableNums.length;
        const totalVarSubsets = this.nCr(variableCount, effG);
        const coversPerCandidate = this.nCr(slotsVariable, effG);
        const lowerBound = coversPerCandidate > 0 ? Math.ceil(totalVarSubsets / coversPerCandidate) : totalVarSubsets;

        const ratio = effG / slotsVariable;
        let factor = ratio >= 0.9 ? 2.0 : ratio >= 0.7 ? 1.6 : ratio >= 0.5 ? 1.4 : 1.2;
        const targetGames = Math.max(lowerBound, Math.ceil(lowerBound * factor));
        const maxGames = requestedQuantity > 0 ? requestedQuantity : targetGames;

        console.log('[CLOSING-v3.1] Estimativa: lower=' + lowerBound + ' → target=' + targetGames + ' → max=' + maxGames);

        const selectedGames = [];
        const usedKeys = new Set();
        const TIMEOUT = 90000;
        const zonesCount = Math.max(2, Math.ceil(variableCount / Math.max(slotsVariable, 1)));
        const zones = [];
        for (let z = 0; z < zonesCount; z++) {
            const start = z * Math.floor(variableCount / zonesCount);
            const end = Math.min(start + Math.ceil(variableCount / zonesCount), variableCount);
            zones.push(variableNums.slice(start, end));
        }

        let attempts = 0;
        while (selectedGames.length < maxGames && attempts < maxGames * 30 && (Date.now() - t0) < TIMEOUT) {
            attempts++;
            
            // Gerar pequeno batch e pegar o melhor via IA
            let candidate;
            if (aiSynergy) {
                let bestCand = null, bestScore = -1;
                for(let b=0; b<15; b++) {
                    const vp = this._generateDiverseCandidate(variableNums, slotsVariable, zones);
                    const score = this._evalSynergy(vp, fixedArr, aiSynergy);
                    if(score > bestScore) { bestScore = score; bestCand = vp; }
                }
                candidate = [...fixedArr, ...bestCand].sort((a, b) => a - b);
            } else {
                const variablePart = this._generateDiverseCandidate(variableNums, slotsVariable, zones);
                candidate = [...fixedArr, ...variablePart].sort((a, b) => a - b);
            }
            
            const key = candidate.join(',');
            if (!usedKeys.has(key)) {
                usedKeys.add(key);
                selectedGames.push([...candidate]);
            }
        }

        const coverageEstimate = this._verifyFullCoverage(selectedGames, allNums, guarantee, 15000);
        const elapsed = Date.now() - t0;

        console.log('[CLOSING-v3.1] ✅ ' + selectedGames.length + ' jogos | Cobertura: ' + coverageEstimate.toFixed(1) + '% | ' + elapsed + 'ms');

        return {
            games: selectedGames, guarantee, totalGames: selectedGames.length,
            totalSubsets: this.nCr(allNums.length, guarantee),
            covered: Math.round(this.nCr(allNums.length, guarantee) * coverageEstimate / 100),
            coveragePct: parseFloat(coverageEstimate.toFixed(2)),
            cost: selectedGames.length * pricePerGame, mode: 'HEURÍSTICO',
            elapsed, selectedNumbers: allNums, fixedNumbers: [...fixedSet],
            confidence: parseFloat(Math.min(100, coverageEstimate).toFixed(1)),
            effectiveGuarantee: effG,
            note: 'Cobertura estimada por amostragem de 15.000 subconjuntos.'
        };
    }

    // ═══════════════════════════════════════════
    //  GERAR CANDIDATO DIVERSO
    // ═══════════════════════════════════════════
    static _generateDiverseCandidate(nums, betSize, zones) {
        const candidate = new Set();
        if (Math.random() < 0.6 && zones.length > 1) {
            const perZone = Math.max(1, Math.floor(betSize / zones.length));
            for (const zone of zones) {
                const shuffled = [...zone].sort(() => Math.random() - 0.5);
                for (let i = 0; i < Math.min(perZone, shuffled.length) && candidate.size < betSize; i++) {
                    candidate.add(shuffled[i]);
                }
            }
        }
        const remaining = nums.filter(n => !candidate.has(n)).sort(() => Math.random() - 0.5);
        for (const num of remaining) {
            if (candidate.size >= betSize) break;
            candidate.add(num);
        }
        return [...candidate];
    }

    // ═══════════════════════════════════════════
    //  VERIFICAR COBERTURA (amostragem)
    // ═══════════════════════════════════════════
    static _verifyFullCoverage(games, allNums, guarantee, sampleSize) {
        if (games.length === 0) return 0;
        const samples = this._generateRandomSubsets(allNums, guarantee, sampleSize);
        if (samples.length === 0) return 0;
        const gameSets = games.map(g => new Set(g));
        let covered = 0;
        for (const sample of samples) {
            for (const gameSet of gameSets) {
                if (sample.every(n => gameSet.has(n))) { covered++; break; }
            }
        }
        return (covered / samples.length) * 100;
    }

    // ═══════════════════════════════════════════
    //  RESULTADO DE ERRO
    // ═══════════════════════════════════════════
    static _errorResult(error, guarantee, nums, fixedSet) {
        return {
            games: [], guarantee, totalGames: 0, totalSubsets: 0,
            covered: 0, coveragePct: 0, cost: 0,
            error, selectedNumbers: nums, fixedNumbers: [...fixedSet]
        };
    }

    // ═══════════════════════════════════════════════════════
    //  PREVIEW DO FECHAMENTO (COM FIXOS CONDICIONAIS)
    // ═══════════════════════════════════════════════════════
    static getClosurePreview(numSelected, guarantee, betSize = 6, gameKey = 'megasena', fixedCount = 0) {
        const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        const price = game ? game.price : 6.00;
        if (gameKey && typeof GAMES !== 'undefined') betSize = this.getBetSize(gameKey);

        if (numSelected < betSize) {
            return { games: 0, cost: 0, subsets: 0, possible: false, msg: 'Selecione pelo menos ' + betSize + ' números' };
        }

        const effG = this.effectiveGuarantee(guarantee, fixedCount, gameKey, numSelected);
        const slotsVariable = betSize - fixedCount;
        const variableCount = numSelected - fixedCount;

        if (variableCount < slotsVariable) {
            return { games: 0, cost: 0, subsets: 0, possible: false, msg: 'Selecione mais números (precisa ' + (slotsVariable + fixedCount) + ' total)' };
        }

        const estimatedGames = this.estimateGames(numSelected, guarantee, betSize, fixedCount, gameKey);
        const cost = estimatedGames * price;

        // Mostrar redução vs sem fixos
        let reductionMsg = '';
        if (fixedCount > 0) {
            const withoutFixed = this.estimateGames(numSelected, guarantee, betSize, 0, gameKey);
            if (withoutFixed > estimatedGames) {
                const reduction = Math.round((1 - estimatedGames / withoutFixed) * 100);
                reductionMsg = ' (↓' + reduction + '% menos que sem fixos)';
            }
        }

        const label = guarantee + ' Pontos';

        // Calcular probabilidade hipergeométrica exata da condição dos fixos
        let fixedHitProb = 1.0;
        let maxHitsInFixed = 0;
        if (fixedCount > 0 && game) {
            const drawSize = game.draw;
            maxHitsInFixed = Math.min(fixedCount, Math.floor(drawSize * (fixedCount / numSelected)));
            fixedHitProb = this.hypergeometricCDF(numSelected, fixedCount, drawSize, maxHitsInFixed);
        }

        return {
            games: estimatedGames, cost, possible: estimatedGames <= 500000,
            subsets: this.nCr(numSelected, guarantee),
            guarantee, label, fixedCount, effectiveGuarantee: effG,
            fixedHitProb: fixedHitProb,
            maxHitsInFixed: maxHitsInFixed,
            msg: numSelected + ' números' + (fixedCount > 0 ? ' (' + fixedCount + ' fixos)' : '') +
                ' → Fechamento ' + label + ' = ~' + estimatedGames.toLocaleString('pt-BR') +
                ' jogos (R$ ' + cost.toLocaleString('pt-BR', { minimumFractionDigits: 2 }) + ')' + reductionMsg
        };
    }

    // Probabilidade hipergeométrica PMF
    static hypergeometricPMF(N, K, n, x) {
        if (x < Math.max(0, n + K - N) || x > Math.min(K, n)) return 0;
        const num1 = this.nCr(K, x);
        const num2 = this.nCr(N - K, n - x);
        const den = this.nCr(N, n);
        if (den === 0) return 0;
        return (num1 * num2) / den;
    }

    // Probabilidade hipergeométrica CDF (acumulada P(X >= minX))
    static hypergeometricCDF(N, K, n, minX) {
        let prob = 0;
        const maxX = Math.min(K, n);
        for (let x = minX; x <= maxX; x++) {
            prob += this.hypergeometricPMF(N, K, n, x);
        }
        return Math.min(1.0, prob);
    }

    // ═══════════════════════════════════════════════════════
    //  NÍVEIS DINÂMICOS — TODOS VIÁVEIS COM FIXOS
    //  (fixar REDUZ jogos, não impossibilita)
    // ═══════════════════════════════════════════════════════
    static getDynamicClosingLevels(gameKey, fixedCount = 0, numSelected = 0) {
        const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        if (!game) return [];

        const betSize = this.getBetSize(gameKey);
        const baseLevels = game.closingLevels || [];
        const icons = { 3: '✅', 4: '🔥', 5: '⭐', 6: '🎯', 7: '🎯', 8: '💎', 9: '💎', 10: '👑', 11: '👑', 12: '👑', 13: '🔥', 14: '⭐', 15: '🎯', 17: '✅', 18: '🔥', 19: '⭐', 20: '🎯' };

        const allLevels = [];
        for (const cl of baseLevels) {
            const effG = this.effectiveGuarantee(cl.guarantee, fixedCount, gameKey, numSelected);
            const reduction = fixedCount > 0
                ? ' (efetivo: ' + effG + ' variáveis)'
                : '';

            allLevels.push({
                id: cl.id,
                label: cl.label + reduction,
                guarantee: cl.guarantee,
                icon: cl.icon || icons[cl.guarantee] || '🎯',
                feasible: true,
                effectiveGuarantee: effG
            });
        }

        // Ordenar por garantia decrescente
        allLevels.sort((a, b) => b.guarantee - a.guarantee);
        return allLevels;
    }

    static _generateDirectedCandidates(uncovered, sampledTSubsets, variableNums, slotsVariable, count) {
        const candidates = [];
        const uncoveredArray = Array.from(uncovered);
        const limit = Math.min(count, uncoveredArray.length);
        
        for (let i = 0; i < limit; i++) {
            const randIdx = Math.floor(Math.random() * uncoveredArray.length);
            const idx = uncoveredArray[randIdx];
            const sub = sampledTSubsets[idx];
            if (!sub) continue;
            
            const candSet = new Set(sub);
            const remaining = variableNums.filter(n => !candSet.has(n));
            
            for (let j = remaining.length - 1; j > 0; j--) {
                const k = Math.floor(Math.random() * (j + 1));
                const temp = remaining[j];
                remaining[j] = remaining[k];
                remaining[k] = temp;
            }
            
            for (const num of remaining) {
                if (candSet.size >= slotsVariable) break;
                candSet.add(num);
            }
            candidates.push([...candSet].sort((a, b) => a - b));
        }
        return candidates;
    }
}

if (typeof window !== 'undefined') {
    window.ClosingEngine = ClosingEngine;
}
