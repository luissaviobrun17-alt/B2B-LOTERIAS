/**
 * Smart Combination Engine v4.0 — Motor Profundo
 * Análises avançadas para maximizar chances com poucos cartões:
 * 
 * 1. FREQUÊNCIA PONDERADA — Números quentes/frios com peso temporal
 * 2. DUPLAS FREQUENTES — Pares que costumam sair juntos
 * 3. TRIOS FREQUENTES — Trios que costumam sair juntos
 * 4. CADEIA DE MARKOV — Se X saiu, qual a chance de Y sair no próximo?
 * 5. ATRASO (DELAY) — Números "atrasados" que não saem há muito tempo
 * 6. SOMA MÉDIA — Filtrar jogos com soma próxima à média histórica
 * 7. DISTRIBUIÇÃO POR DEZENA — Equilíbrio entre faixas (01-10, 11-20...)
 * 8. PAR/ÍMPAR — Equilíbrio histórico
 * 9. ANTI-SEQUÊNCIA — Penalizar sequências longas (raramente acontecem)
 * 10. ANTI-SOBREPOSIÇÃO — Maximizar cobertura entre cartões
 * 11. SCORE COMPOSTO — Combinar todos os critérios em nota final
 */

class CombinationEngine {

    // ═══════════════════════════════════════════
    //  FÓRMULA COMBINATÓRIA nCr
    // ═══════════════════════════════════════════
    static nCr(n, r) {
        if (r < 0 || r > n) return 0;
        if (r === 0 || r === n) return 1;
        if (r > n / 2) r = n - r;
        let res = 1;
        for (let i = 1; i <= r; i++) {
            res = res * (n - i + 1) / i;
        }
        return res;
    }

    // ═══════════════════════════════════════════
    //  1. FREQUÊNCIA COM PESO TEMPORAL
    //  Sorteios mais recentes têm peso maior
    // ═══════════════════════════════════════════
    static analyzeWeightedFrequency(history, game) {
        const freq = {};
        for (let i = game.range[0]; i <= game.range[1]; i++) {
            freq[i] = 0;
        }
        
        const total = history.length;
        history.forEach((draw, index) => {
            // Peso: sorteio mais recente (index 0) = peso máximo
            const weight = 1 + (total - index) / total; // 1.0 a 2.0
            
            if (draw.numbers) {
                draw.numbers.forEach(n => { 
                    if (freq[n] !== undefined) freq[n] += weight; 
                });
            }
            if (draw.numbers2) {
                draw.numbers2.forEach(n => { 
                    if (freq[n] !== undefined) freq[n] += weight; 
                });
            }
        });

        return freq;
    }

    // ═══════════════════════════════════════════
    //  2. DUPLAS FREQUENTES
    // ═══════════════════════════════════════════
    static analyzePairs(history, topCount = 30) {
        const pairMap = {};
        
        history.forEach(draw => {
            const nums = draw.numbers || [];
            const allNums = draw.numbers2 ? nums.concat(draw.numbers2) : nums;
            
            for (let i = 0; i < allNums.length; i++) {
                for (let j = i + 1; j < allNums.length; j++) {
                    const key = Math.min(allNums[i], allNums[j]) + '-' + Math.max(allNums[i], allNums[j]);
                    pairMap[key] = (pairMap[key] || 0) + 1;
                }
            }
        });

        return Object.entries(pairMap)
            .map(([key, count]) => {
                const [a, b] = key.split('-').map(Number);
                return { pair: [a, b], count };
            })
            .filter(p => p.count >= 2) // Mínimo 2 ocorrências
            .sort((a, b) => b.count - a.count)
            .slice(0, topCount);
    }

    // ═══════════════════════════════════════════
    //  3. TRIOS FREQUENTES
    // ═══════════════════════════════════════════
    static analyzeTrios(history, topCount = 20) {
        const trioMap = {};
        
        history.forEach(draw => {
            const nums = draw.numbers || [];
            const allNums = draw.numbers2 ? nums.concat(draw.numbers2) : nums;
            
            for (let i = 0; i < allNums.length; i++) {
                for (let j = i + 1; j < allNums.length; j++) {
                    for (let k = j + 1; k < allNums.length; k++) {
                        const sorted = [allNums[i], allNums[j], allNums[k]].sort((a, b) => a - b);
                        const key = sorted.join('-');
                        trioMap[key] = (trioMap[key] || 0) + 1;
                    }
                }
            }
        });

        return Object.entries(trioMap)
            .map(([key, count]) => {
                const nums = key.split('-').map(Number);
                return { trio: nums, count };
            })
            .filter(t => t.count >= 2) // Mínimo 2 ocorrências
            .sort((a, b) => b.count - a.count)
            .slice(0, topCount);
    }

    // ═══════════════════════════════════════════
    //  4. CADEIA DE MARKOV
    //  Se o número X saiu no sorteio anterior,
    //  qual a chance do número Y sair no próximo?
    // ═══════════════════════════════════════════
    static analyzeMarkov(history, game) {
        const transitions = {};
        // Inicializar
        for (let i = game.range[0]; i <= game.range[1]; i++) {
            transitions[i] = {};
        }

        // Percorrer pares de sorteios consecutivos
        for (let d = 0; d < history.length - 1; d++) {
            const current = history[d].numbers || [];
            const previous = history[d + 1].numbers || [];
            
            previous.forEach(prevNum => {
                current.forEach(currNum => {
                    if (!transitions[prevNum][currNum]) transitions[prevNum][currNum] = 0;
                    transitions[prevNum][currNum]++;
                });
            });
        }

        return transitions;
    }

    // ═══════════════════════════════════════════
    //  5. ANÁLISE DE ATRASO (DELAY)
    //  Quantos sorteios cada número não sai
    // ═══════════════════════════════════════════
    static analyzeDelay(history, game) {
        const delay = {};
        for (let i = game.range[0]; i <= game.range[1]; i++) {
            delay[i] = history.length; // Default: nunca saiu
        }

        for (let d = 0; d < history.length; d++) {
            const nums = history[d].numbers || [];
            const allNums = history[d].numbers2 ? nums.concat(history[d].numbers2) : nums;
            
            allNums.forEach(n => {
                if (delay[n] === history.length) {
                    delay[n] = d; // Primeira aparição (d=0 é o mais recente)
                }
            });
        }

        return delay;
    }

    // ═══════════════════════════════════════════
    //  6. SOMA MÉDIA DOS SORTEIOS
    // ═══════════════════════════════════════════
    static analyzeSumStats(history) {
        if (history.length === 0) return { avg: 0, stdDev: 0 };
        
        const sums = history
            .filter(d => d.numbers && d.numbers.length > 0)
            .map(d => d.numbers.reduce((a, b) => a + b, 0));
        
        if (sums.length === 0) return { avg: 0, stdDev: 0 };
        
        const avg = sums.reduce((a, b) => a + b, 0) / sums.length;
        const variance = sums.reduce((acc, s) => acc + Math.pow(s - avg, 2), 0) / sums.length;
        const stdDev = Math.sqrt(variance);
        
        return { avg: Math.round(avg), stdDev: Math.round(stdDev) };
    }

    // ═══════════════════════════════════════════
    //  7. DISTRIBUIÇÃO POR DEZENAS
    // ═══════════════════════════════════════════
    static analyzeDecadeDistribution(history, game) {
        const rangeSize = game.range[1] - game.range[0] + 1;
        const decadeSize = 10;
        const numDecades = Math.ceil(rangeSize / decadeSize);
        const avgDistribution = new Array(numDecades).fill(0);
        let validDraws = 0;

        history.forEach(draw => {
            if (!draw.numbers || draw.numbers.length === 0) return;
            validDraws++;
            draw.numbers.forEach(n => {
                const decade = Math.floor((n - game.range[0]) / decadeSize);
                if (decade >= 0 && decade < numDecades) {
                    avgDistribution[decade]++;
                }
            });
        });

        if (validDraws > 0) {
            for (let d = 0; d < numDecades; d++) {
                avgDistribution[d] = avgDistribution[d] / validDraws;
            }
        }

        return { numDecades, decadeSize, avgDistribution, rangeStart: game.range[0] };
    }

    // ═══════════════════════════════════════════
    //  8. ANÁLISE PAR/ÍMPAR
    // ═══════════════════════════════════════════
    static analyzeParImpar(history) {
        let totalPar = 0, totalImpar = 0, count = 0;
        history.forEach(draw => {
            if (!draw.numbers) return;
            count++;
            draw.numbers.forEach(n => {
                if (n % 2 === 0) totalPar++;
                else totalImpar++;
            });
        });
        if (count === 0) return { avgPar: 0, avgImpar: 0, ratioPar: 0.5 };
        return {
            avgPar: totalPar / count,
            avgImpar: totalImpar / count,
            ratioPar: totalPar / (totalPar + totalImpar)
        };
    }

    // ═══════════════════════════════════════════
    //  9. NÚMEROS CONSECUTIVOS — média histórica
    // ═══════════════════════════════════════════
    static analyzeConsecutives(history) {
        let totalConsec = 0, count = 0;
        history.forEach(draw => {
            if (!draw.numbers || draw.numbers.length < 2) return;
            count++;
            const sorted = [...draw.numbers].sort((a, b) => a - b);
            let consec = 0;
            for (let i = 1; i < sorted.length; i++) {
                if (sorted[i] === sorted[i - 1] + 1) consec++;
            }
            totalConsec += consec;
        });
        return count > 0 ? totalConsec / count : 0;
    }

    // ═══════════════════════════════════════════
    //  10. CICLOS DE REPETIÇÃO
    //  Detecta se certos números reaparecem em
    //  intervalos regulares (ex: a cada 3-5 sorteios)
    // ═══════════════════════════════════════════
    static analyzeCycles(history, game) {
        const cycleHits = {};
        for (let n = game.range[0]; n <= game.range[1]; n++) {
            // Encontrar onde este número apareceu
            const appearances = [];
            for (let d = 0; d < history.length; d++) {
                const allNums = (history[d].numbers || []).concat(history[d].numbers2 || []);
                if (allNums.includes(n)) appearances.push(d);
            }
            
            if (appearances.length >= 3) {
                // Calcular intervalos entre aparições
                const gaps = [];
                for (let i = 1; i < appearances.length; i++) {
                    gaps.push(appearances[i] - appearances[i - 1]);
                }
                
                // Verificar se há um intervalo dominante (ciclo)
                const gapFreq = {};
                gaps.forEach(g => { gapFreq[g] = (gapFreq[g] || 0) + 1; });
                
                const dominantGap = Object.entries(gapFreq)
                    .sort((a, b) => b[1] - a[1])[0];
                
                if (dominantGap && dominantGap[1] >= 2) {
                    const cycleLen = parseInt(dominantGap[0]);
                    const lastApp = appearances[0]; // Mais recente
                    
                    // Se está "no ciclo" para sair no próximo sorteio
                    if (lastApp > 0 && (lastApp % cycleLen === 0 || lastApp === cycleLen - 1)) {
                        cycleHits[n] = {
                            cycleLength: cycleLen,
                            confidence: dominantGap[1] / gaps.length, // % de gaps que seguem o ciclo
                            nextExpected: lastApp + cycleLen
                        };
                    }
                }
            }
        }
        return cycleHits;
    }

    // ═══════════════════════════════════════════
    //  11. NÚMEROS ESPELHO
    //  Se 13 sai, 31 tende a sair depois?
    //  Se 24 sai, 42 tende a sair?
    // ═══════════════════════════════════════════
    static analyzeMirrors(history, game) {
        const mirrorPairs = {};
        
        for (let d = 0; d < history.length - 1; d++) {
            const current = history[d].numbers || [];
            const next = history[d + 1].numbers || [];
            
            next.forEach(prevNum => {
                // Calcular espelho (inverter dígitos)
                const mirror = parseInt(String(prevNum).split('').reverse().join(''));
                
                if (mirror >= game.range[0] && mirror <= game.range[1] && mirror !== prevNum) {
                    if (current.includes(mirror)) {
                        const key = Math.min(prevNum, mirror) + '->' + Math.max(prevNum, mirror);
                        mirrorPairs[key] = (mirrorPairs[key] || 0) + 1;
                    }
                }
            });
        }

        // Retornar espelhos que aconteceram 2+ vezes
        return Object.entries(mirrorPairs)
            .filter(([_, count]) => count >= 2)
            .map(([key, count]) => {
                const parts = key.split('->').map(Number);
                return { pair: parts, count };
            })
            .sort((a, b) => b.count - a.count);
    }

    // ═══════════════════════════════════════════
    //  12. FIBONACCI GAPS
    //  Verifica se as diferenças entre números
    //  consecutivos seguem padrão de Fibonacci
    // ═══════════════════════════════════════════
    static analyzeFibonacciPattern(history) {
        const fib = [1, 1, 2, 3, 5, 8, 13, 21];
        let fibCount = 0;
        let totalGaps = 0;

        history.forEach(draw => {
            if (!draw.numbers || draw.numbers.length < 2) return;
            const sorted = [...draw.numbers].sort((a, b) => a - b);
            for (let i = 1; i < sorted.length; i++) {
                const gap = sorted[i] - sorted[i - 1];
                totalGaps++;
                if (fib.includes(gap)) fibCount++;
            }
        });

        return {
            fibRatio: totalGaps > 0 ? fibCount / totalGaps : 0,
            fibNumbers: fib
        };
    }

    // ═══════════════════════════════════════════
    //  13. PADRÃO DE SOMA MODULAR
    //  A soma dos números mod N segue padrão?
    // ═══════════════════════════════════════════
    static analyzeSumModPattern(history) {
        const patterns = {};
        const modValues = [3, 5, 7, 10];

        modValues.forEach(mod => {
            const modResults = {};
            history.forEach(draw => {
                if (!draw.numbers) return;
                const sum = draw.numbers.reduce((a, b) => a + b, 0);
                const modResult = sum % mod;
                modResults[modResult] = (modResults[modResult] || 0) + 1;
            });

            // Encontrar o mod mais frequente
            const entries = Object.entries(modResults).sort((a, b) => b[1] - a[1]);
            if (entries.length > 0) {
                const topMod = parseInt(entries[0][0]);
                const topCount = entries[0][1];
                const totalDraws = history.filter(d => d.numbers).length;
                const concentration = topCount / totalDraws;

                // Se um mod concentra mais de 30% dos resultados, é padrão
                if (concentration > 0.3) {
                    patterns[mod] = {
                        preferredMod: topMod,
                        concentration: concentration,
                        count: topCount,
                        total: totalDraws
                    };
                }
            }
        });

        return patterns;
    }

    // ═══════════════════════════════════════════
    //  14. DETECÇÃO DE QUADRANTE/GRID
    //  Em um grid 5x5 ou 10x5, detectar se há
    //  diagonais ou linhas favorecidas
    // ═══════════════════════════════════════════
    static analyzeGridPattern(history, game) {
        const cols = 10; // Grid 10xN
        const gridHeat = {};
        
        history.forEach(draw => {
            if (!draw.numbers) return;
            draw.numbers.forEach(n => {
                const col = (n - game.range[0]) % cols;
                const row = Math.floor((n - game.range[0]) / cols);
                const key = row + ',' + col;
                gridHeat[key] = (gridHeat[key] || 0) + 1;
            });
        });

        // Encontrar posições "quentes" no grid
        const hotPositions = Object.entries(gridHeat)
            .sort((a, b) => b[1] - a[1])
            .slice(0, 15)
            .map(([key, count]) => {
                const [row, col] = key.split(',').map(Number);
                return { row, col, count, number: row * cols + col + game.range[0] };
            });

        return { cols, hotPositions };
    }

    // ═══════════════════════════════════════════
    //  SCORE DE QUALIDADE PROFUNDO (15 critérios)
    // ═══════════════════════════════════════════
    static scoreTicket(ticket, analysis) {
        let score = 0;
        const { freq, topPairs, topTrios, markov, delay, sumStats, 
                decadeDist, parImpar, avgConsec, game, lastDraw } = analysis;

        // ── 1. FREQUÊNCIA PONDERADA (0-30 pontos) ──
        const maxFreq = Math.max(...Object.values(freq), 1);
        let freqScore = 0;
        ticket.forEach(n => {
            freqScore += (freq[n] || 0) / maxFreq;
        });
        score += freqScore * (30 / ticket.length);

        // ── 2. DUPLAS FREQUENTES (0-25 pontos) ──
        let pairBonus = 0;
        topPairs.forEach(p => {
            if (ticket.includes(p.pair[0]) && ticket.includes(p.pair[1])) {
                pairBonus += p.count;
            }
        });
        score += Math.min(25, pairBonus * 2);

        // ── 3. TRIOS FREQUENTES (0-20 pontos) ──
        let trioBonus = 0;
        topTrios.forEach(t => {
            if (ticket.includes(t.trio[0]) && ticket.includes(t.trio[1]) && ticket.includes(t.trio[2])) {
                trioBonus += t.count;
            }
        });
        score += Math.min(20, trioBonus * 3);

        // ── 4. CADEIA DE MARKOV (0-15 pontos) ──
        // Se o último sorteio teve os números X, bonificar Y's que seguem X historicamente
        if (markov && lastDraw && lastDraw.length > 0) {
            let markovBonus = 0;
            lastDraw.forEach(prevNum => {
                if (markov[prevNum]) {
                    ticket.forEach(currNum => {
                        if (markov[prevNum][currNum]) {
                            markovBonus += markov[prevNum][currNum];
                        }
                    });
                }
            });
            score += Math.min(15, markovBonus * 0.5);
        }

        // ── 5. ATRASO / DELAY (0-15 pontos) ──
        // Bônus para números "atrasados" (que não saem há muitos sorteios)
        if (delay) {
            let delayBonus = 0;
            const maxDelay = Math.max(...Object.values(delay), 1);
            ticket.forEach(n => {
                const d = delay[n] || 0;
                if (d >= 5) { // Atrasado (5+ sorteios sem sair)
                    delayBonus += d / maxDelay;
                }
            });
            // Bônus moderado — incluir ALGUNS atrasados, não muitos
            const atrasados = ticket.filter(n => (delay[n] || 0) >= 5).length;
            if (atrasados >= 1 && atrasados <= Math.ceil(ticket.length * 0.3)) {
                score += Math.min(15, delayBonus * 5);
            }
        }

        // ── 6. SOMA DENTRO DA FAIXA ESPERADA (0-20 pontos / -20 penalidade) ──
        if (sumStats && sumStats.avg > 0) {
            const ticketSum = ticket.reduce((a, b) => a + b, 0);
            const deviation = Math.abs(ticketSum - sumStats.avg);
            const tolerance = Math.max(1, sumStats.stdDev * 1.5); // 1.5 desvios padrão (min 1 para evitar divisão por zero)
            
            if (deviation <= tolerance) {
                // Dentro da faixa esperada — bônus proporcional
                score += 20 * (1 - deviation / tolerance);
            } else {
                // Fora da faixa — penalidade forte
                score -= 15 * (deviation / sumStats.avg);
            }
        }

        // ── 7. DISTRIBUIÇÃO POR DEZENAS (-15 penalidade) ──
        if (decadeDist) {
            const ticketDist = new Array(decadeDist.numDecades).fill(0);
            ticket.forEach(n => {
                const decade = Math.floor((n - decadeDist.rangeStart) / decadeDist.decadeSize);
                if (decade >= 0 && decade < decadeDist.numDecades) {
                    ticketDist[decade]++;
                }
            });
            
            let distPenalty = 0;
            for (let d = 0; d < decadeDist.numDecades; d++) {
                const expected = decadeDist.avgDistribution[d];
                const actual = ticketDist[d];
                distPenalty += Math.abs(actual - expected);
            }
            score -= distPenalty * 3;
        }

        // ── 8. EQUILÍBRIO PAR/ÍMPAR (-10 penalidade) ──
        if (parImpar && parImpar.avgPar > 0) {
            let pares = 0;
            ticket.forEach(n => { if (n % 2 === 0) pares++; });
            const expectedPares = Math.round(ticket.length * parImpar.ratioPar);
            const diffPar = Math.abs(pares - expectedPares);
            score -= diffPar * 4;
        }

        // ── 9. ANTI-SEQUÊNCIA LONGA (-15 penalidade) ──
        let maxConsecutive = 1, currentConsecutive = 1;
        for (let i = 1; i < ticket.length; i++) {
            if (ticket[i] === ticket[i - 1] + 1) {
                currentConsecutive++;
                maxConsecutive = Math.max(maxConsecutive, currentConsecutive);
            } else {
                currentConsecutive = 1;
            }
        }
        // Permitir 2-3 consecutivos (normal), penalizar 4+
        if (maxConsecutive >= 4) score -= (maxConsecutive - 3) * 8;

        // ── 10. CONSECUTIVOS NA MÉDIA (-5 penalidade) ──
        if (avgConsec > 0) {
            let actualConsec = 0;
            const sorted = [...ticket].sort((a, b) => a - b);
            for (let i = 1; i < sorted.length; i++) {
                if (sorted[i] === sorted[i - 1] + 1) actualConsec++;
            }
            const diff = Math.abs(actualConsec - avgConsec);
            if (diff > 2) score -= diff * 2;
        }

        return score;
    }

    // Bônus extra dos padrões ocultos no score
    static _applyHiddenPatternBonus(score, ticket, analysis) {
        const { cycles, mirrors, fibPattern, sumModPattern, lastDraw } = analysis;

        // ── CICLOS: bônus se inclui números "no ciclo" ──
        if (cycles) {
            let cycleBonus = 0;
            ticket.forEach(n => {
                if (cycles[n] && cycles[n].confidence >= 0.5) {
                    cycleBonus += cycles[n].confidence * 5;
                }
            });
            score += Math.min(10, cycleBonus);
        }

        // ── ESPELHOS: bônus se inclui par espelho do último sorteio ──
        if (mirrors && mirrors.length > 0 && lastDraw) {
            let mirrorBonus = 0;
            lastDraw.forEach(prev => {
                const mirror = parseInt(String(prev).split('').reverse().join(''));
                if (ticket.includes(mirror)) mirrorBonus += 2;
            });
            score += Math.min(8, mirrorBonus);
        }

        // ── FIBONACCI: bônus se gaps seguem Fibonacci ──
        if (fibPattern && fibPattern.fibRatio > 0.3) {
            const fib = fibPattern.fibNumbers;
            let fibHits = 0;
            for (let i = 1; i < ticket.length; i++) {
                if (fib.includes(ticket[i] - ticket[i - 1])) fibHits++;
            }
            const ratio = fibHits / (ticket.length - 1);
            if (ratio >= fibPattern.fibRatio * 0.8) {
                score += ratio * 8;
            }
        }

        // ── SOMA MODULAR: bônus se soma segue o padrão detectado ──
        if (sumModPattern) {
            const ticketSum = ticket.reduce((a, b) => a + b, 0);
            Object.entries(sumModPattern).forEach(([mod, pattern]) => {
                if (ticketSum % parseInt(mod) === pattern.preferredMod) {
                    score += pattern.concentration * 6;
                }
            });
        }

        return score;
    }

    // ═══════════════════════════════════════════
    //  COBERTURA ANTI-SOBREPOSIÇÃO
    // ═══════════════════════════════════════════
    static coverageScore(newTicket, existingGames) {
        if (existingGames.length === 0) return 100;
        
        let maxOverlap = 0;
        existingGames.forEach(existing => {
            const overlap = newTicket.filter(n => existing.includes(n)).length;
            maxOverlap = Math.max(maxOverlap, overlap);
        });

        // Quanto MENOS sobreposição máxima, melhor
        return 100 - (maxOverlap / newTicket.length * 100);
    }

    // ═══════════════════════════════════════════
    //  GERAÇÃO INTELIGENTE v4.0 — MOTOR PROFUNDO
    // ═══════════════════════════════════════════
    static generate(gameType, strategyMatch, quantity = 10, customPool = null, fixedNumbers = []) {
        const game = GAMES[gameType];
        if (!game) return { pool: [], games: [] };

        // Preparar pool
        let pool = customPool && customPool.length > 0 ? [...customPool] : [];
        const universe = [];
        for (let i = game.range[0]; i <= game.range[1]; i++) {
            universe.push(i);
        }

        if (pool.length < game.minBet) {
            const missingCount = game.minBet - pool.length;
            const remainingUniverse = universe.filter(n => !pool.includes(n));
            const supplement = this.getRandomSubset(remainingUniverse, missingCount);
            pool = pool.concat(supplement);
        }

        // ══ AUTO-EXPANSÃO INTELIGENTE ══
        // Se C(pool, minBet) < quantidade solicitada, expandir pool automaticamente
        // usando números mais frequentes do histórico
        const possibleCombinations = this.nCr(pool.length, game.minBet);
        
        // ★ GOD MODE FIX: Circuit Breaker ajustado (Out of Memory não é mais um risco pois usamos geração randômica/heurística)
        const realComb = this.nCr(pool.length - fixedNumbers.length, game.minBet - fixedNumbers.length);
        if (realComb > 50000000) { // Limite aumentado para não bloquear Mega Sena (que tem ~50M combinações)
            console.warn(`[Circuit Breaker] Matriz muito grande (${realComb}), mas o motor heurístico vai limitar os candidatos a ${quantity}.`);
        }
        if (possibleCombinations < quantity && pool.length < universe.length) {
            const history = (typeof StatsService !== 'undefined' && StatsService.historyStore[gameType]) 
                ? StatsService.historyStore[gameType] 
                : (typeof REAL_HISTORY_DB !== 'undefined' ? REAL_HISTORY_DB[gameType] || [] : []);
            
            // Calcular frequência de todos os números do universo
            const freqMap = {};
            history.forEach(draw => {
                (draw.numbers || []).forEach(n => { freqMap[n] = (freqMap[n] || 0) + 1; });
            });

            // Números disponíveis para adicionar (não estão no pool), ordenados por frequência
            const candidates = universe
                .filter(n => !pool.includes(n))
                .sort((a, b) => (freqMap[b] || 0) - (freqMap[a] || 0));

            // Adicionar números até ter combinações suficientes (ou esgotar candidatos)
            let expandCount = 0;
            while (this.nCr(pool.length, game.minBet) < quantity * 1.5 && candidates.length > 0) {
                pool.push(candidates.shift());
                expandCount++;
                // Limite de segurança — não expandir além de 80% do universo
                if (pool.length >= universe.length * 0.8) break;
            }

            if (expandCount > 0) {
                console.log(`[CombEngine v4] 🔄 Auto-expansão: +${expandCount} números (pool: ${pool.length - expandCount} → ${pool.length}) para gerar ${quantity} jogos`);
            }
        }

        // Validar fixos
        const validFixed = fixedNumbers.filter(f => pool.includes(f));
        const needed = game.minBet - validFixed.length;
        if (needed < 0) return { pool, games: [] };

        const availablePool = pool.filter(n => !validFixed.includes(n));

        // ═══════════════════════════════════════
        //  ANÁLISE PROFUNDA DE TODO O HISTÓRICO
        // ═══════════════════════════════════════
        const history = (typeof StatsService !== 'undefined' && StatsService.historyStore[gameType]) 
            ? StatsService.historyStore[gameType] 
            : (typeof REAL_HISTORY_DB !== 'undefined' ? REAL_HISTORY_DB[gameType] || [] : []);

        const freq = this.analyzeWeightedFrequency(history, game);
        const topPairs = this.analyzePairs(history, 30);
        const topTrios = this.analyzeTrios(history, 20);
        const markov = this.analyzeMarkov(history, game);
        const delay = this.analyzeDelay(history, game);
        const sumStats = this.analyzeSumStats(history);
        const decadeDist = this.analyzeDecadeDistribution(history, game);
        const parImpar = this.analyzeParImpar(history);
        const avgConsec = this.analyzeConsecutives(history);

        
        // ══ PADRÕES OCULTOS ══
        const cycles = this.analyzeCycles(history, game);
        const mirrors = this.analyzeMirrors(history, game);
        const fibPattern = this.analyzeFibonacciPattern(history);
        const sumModPattern = this.analyzeSumModPattern(history);
        const gridPattern = this.analyzeGridPattern(history, game);
        
        // Último sorteio (para Markov)
        const lastDraw = history.length > 0 ? (history[0].numbers || []) : [];

        const analysis = { 
            freq, topPairs, topTrios, markov, delay, sumStats,
            decadeDist, parImpar, avgConsec, game, lastDraw,
            cycles, mirrors, fibPattern, sumModPattern, gridPattern
        };

        console.log(`[CombEngine v4] 🧠 Análise profunda: ${history.length} sorteios`);
        console.log(`[CombEngine v4] 📊 Soma média: ${sumStats.avg} ± ${sumStats.stdDev}`);
        console.log(`[CombEngine v4] 🔗 ${topPairs.length} duplas, 🔺 ${topTrios.length} trios`);
        console.log(`[CombEngine v4] 🔄 Consecutivos média: ${avgConsec.toFixed(1)}`);
        console.log(`[CombEngine v4] ⚖️ Par/Ímpar: ${parImpar.avgPar.toFixed(1)}/${parImpar.avgImpar.toFixed(1)}`);
        console.log(`[CombEngine v4] 🔍 Padrões ocultos: ${Object.keys(cycles).length} ciclos, ${mirrors.length} espelhos, Fib=${(fibPattern.fibRatio*100).toFixed(0)}%, ${Object.keys(sumModPattern).length} padrões mod`);

        // ═══════════════════════════════════════
        //  GERAÇÃO MASSIVA DE CANDIDATOS + SCORING
        // ═══════════════════════════════════════
        const games = [];
        const safeQuantity = Math.min(quantity, 500000);
        const usedCombinations = new Set();
        
        // Gerar MUITOS candidatos para selecionar os melhores
        // Para volumes altos (>5000), reduzir multiplicador para evitar travamento
        const candidatesMult = safeQuantity <= 5000 ? 20 : (safeQuantity <= 15000 ? 8 : 4);
        const candidatesTarget = Math.max(200, safeQuantity * candidatesMult);
        let bestCandidates = [];

        // Construir tabela de pesos para seleção ponderada
        const poolWeights = availablePool.map(n => {
            let w = 1;
            w += (freq[n] || 0) * 0.5; // Frequência
            const d = delay[n] || 0;
            if (d >= 5 && d <= 15) w += d * 0.3; // Atraso moderado = bônus
            return Math.max(0.5, w);
        });
        const totalWeight = poolWeights.reduce((a, b) => a + b, 0);

        // ── Método 1: Seleção ponderada por frequência + atraso (60% dos candidatos) ──
        for (let attempt = 0; attempt < candidatesTarget * 0.6; attempt++) {
            const ticket = this._generateWeightedTicket(validFixed, availablePool, poolWeights, totalWeight, needed);
            if (!ticket) continue;
            
            const key = ticket.join(',');
            if (!usedCombinations.has(key)) {
                usedCombinations.add(key);
                bestCandidates.push({ ticket, score: this._applyHiddenPatternBonus(this.scoreTicket(ticket, analysis), ticket, analysis) });
            }
        }

        // ── Método 2: Baseado em duplas frequentes (20% dos candidatos) ──
        for (let attempt = 0; attempt < candidatesTarget * 0.2; attempt++) {
            const ticket = this._generatePairBasedTicket(validFixed, availablePool, topPairs, needed, game);
            if (!ticket) continue;
            
            const key = ticket.join(',');
            if (!usedCombinations.has(key)) {
                usedCombinations.add(key);
                bestCandidates.push({ ticket, score: this._applyHiddenPatternBonus(this.scoreTicket(ticket, analysis), ticket, analysis) });
            }
        }

        // ── Método 3: Baseado em Markov (seguindo o último sorteio) (20% dos candidatos) ──
        for (let attempt = 0; attempt < candidatesTarget * 0.2; attempt++) {
            const ticket = this._generateMarkovTicket(validFixed, availablePool, markov, lastDraw, needed);
            if (!ticket) continue;
            
            const key = ticket.join(',');
            if (!usedCombinations.has(key)) {
                usedCombinations.add(key);
                bestCandidates.push({ ticket, score: this._applyHiddenPatternBonus(this.scoreTicket(ticket, analysis), ticket, analysis) });
            }
        }

        console.log(`[CombEngine v4] 🎲 ${bestCandidates.length} candidatos gerados, selecionando top ${safeQuantity}`);

        // Ordenar por score
        bestCandidates.sort((a, b) => b.score - a.score);

        // Seleção final com maximização de cobertura
        const minCoverage = Math.max(15, 50 - safeQuantity * 2); // Menos exigente com mais jogos
        
        for (let i = 0; i < bestCandidates.length && games.length < safeQuantity; i++) {
            const candidate = bestCandidates[i];
            const coverage = this.coverageScore(candidate.ticket, games);
            
            // Top 2 sempre entram; depois, exigir cobertura mínima
            if (games.length < 2 || coverage >= minCoverage) {
                games.push(candidate.ticket);
            }
        }

        // Fallback: se não atingiu a quantidade
        if (games.length < safeQuantity) {
            for (let i = 0; i < bestCandidates.length && games.length < safeQuantity; i++) {
                if (!games.some(g => g.join(',') === bestCandidates[i].ticket.join(','))) {
                    games.push(bestCandidates[i].ticket);
                }
            }
        }

        // Estatísticas dos jogos gerados
        const allNums = new Set();
        games.forEach(g => g.forEach(n => allNums.add(n)));
        const avgScore = bestCandidates.length > 0 
            ? (bestCandidates.slice(0, games.length).reduce((a, c) => a + c.score, 0) / games.length).toFixed(1)
            : '0';

        console.log(`[CombEngine v4] ✅ ${games.length} jogos: ${allNums.size} únicos, score médio: ${avgScore}`);

        // Identificar números "atrasados" usados
        const delayedUsed = [];
        if (delay) {
            allNums.forEach(n => {
                if (delay[n] >= 5) delayedUsed.push({ num: n, delay: delay[n] });
            });
            delayedUsed.sort((a, b) => b.delay - a.delay);
        }

        return {
            pool: pool,
            games: games,
            smartAnalysis: {
                engineVersion: 'v4.0 Profundo',
                historySize: history.length,
                candidatesGenerated: bestCandidates.length,
                avgScore: avgScore,
                sumRange: `${sumStats.avg} ± ${sumStats.stdDev}`,
                parImparRatio: `${parImpar.avgPar.toFixed(1)}P / ${parImpar.avgImpar.toFixed(1)}I`,
                avgConsecutives: avgConsec.toFixed(1),
                pairsUsed: topPairs.slice(0, 5).map(p => p.pair.join('-') + ' (' + p.count + '×)'),
                triosUsed: topTrios.slice(0, 3).map(t => t.trio.join('-') + ' (' + t.count + '×)'),
                delayedNumbers: delayedUsed.slice(0, 5).map(d => d.num.toString().padStart(2, '0') + ' (' + d.delay + ' atraso)'),
                uniqueNumbers: allNums.size,
                // Padrões ocultos detectados
                cyclesDetected: Object.keys(cycles).length,
                cycleNumbers: Object.entries(cycles).slice(0, 5).map(([n, c]) => n.toString().padStart(2, '0') + ' (ciclo ' + c.cycleLength + ')'),
                mirrorsDetected: mirrors.slice(0, 3).map(m => m.pair.join('↔') + ' (' + m.count + '×)'),
                fibonacciRatio: (fibPattern.fibRatio * 100).toFixed(0) + '%',
                sumModPatterns: Object.entries(sumModPattern).map(([mod, p]) => `mod${mod}=${p.preferredMod} (${(p.concentration*100).toFixed(0)}%)`)
            }
        };
    }

    // ═══════════════════════════════════════════
    //  GERAÇÃO PONDERADA POR FREQUÊNCIA + ATRASO
    // ═══════════════════════════════════════════
    static _generateWeightedTicket(validFixed, availablePool, weights, totalWeight, needed) {
        let ticket = [...validFixed];
        const selected = new Set(validFixed);
        let safety = 0;

        while (selected.size < validFixed.length + needed && safety < needed * 15) {
            safety++;
            let rand = Math.random() * totalWeight;
            for (let i = 0; i < availablePool.length; i++) {
                rand -= weights[i];
                if (rand <= 0) {
                    if (!selected.has(availablePool[i])) {
                        selected.add(availablePool[i]);
                        ticket.push(availablePool[i]);
                    }
                    break;
                }
            }
        }

        // Preencher se necessário
        if (ticket.length < validFixed.length + needed) {
            const remaining = availablePool.filter(n => !selected.has(n));
            const shuffled = remaining.sort(() => 0.5 - Math.random());
            for (let i = 0; i < shuffled.length && ticket.length < validFixed.length + needed; i++) {
                ticket.push(shuffled[i]);
            }
        }

        ticket.sort((a, b) => a - b);
        return ticket.length === validFixed.length + needed ? ticket : null;
    }

    // ═══════════════════════════════════════════
    //  GERAÇÃO BASEADA EM DUPLAS FREQUENTES
    //  Força inclusão de pelo menos 1-2 duplas top
    // ═══════════════════════════════════════════
    static _generatePairBasedTicket(validFixed, availablePool, topPairs, needed, game) {
        let ticket = [...validFixed];
        const selected = new Set(validFixed);

        // Escolher 1-2 duplas frequentes para "semear" o jogo
        const shuffledPairs = topPairs.slice(0, 15).sort(() => 0.5 - Math.random());
        let pairsAdded = 0;

        for (const p of shuffledPairs) {
            if (pairsAdded >= 2) break;
            const [a, b] = p.pair;
            if (availablePool.includes(a) && availablePool.includes(b)) {
                if (!selected.has(a) && ticket.length < validFixed.length + needed) {
                    selected.add(a);
                    ticket.push(a);
                }
                if (!selected.has(b) && ticket.length < validFixed.length + needed) {
                    selected.add(b);
                    ticket.push(b);
                }
                pairsAdded++;
            }
        }

        // Completar com seleção aleatória
        const remaining = availablePool.filter(n => !selected.has(n)).sort(() => 0.5 - Math.random());
        for (let i = 0; i < remaining.length && ticket.length < validFixed.length + needed; i++) {
            ticket.push(remaining[i]);
            selected.add(remaining[i]);
        }

        ticket.sort((a, b) => a - b);
        return ticket.length === validFixed.length + needed ? ticket : null;
    }

    // ═══════════════════════════════════════════
    //  GERAÇÃO BASEADA EM MARKOV
    //  Prioriza números que seguem o último sorteio
    // ═══════════════════════════════════════════
    static _generateMarkovTicket(validFixed, availablePool, markov, lastDraw, needed) {
        let ticket = [...validFixed];
        const selected = new Set(validFixed);

        // Calcular score de Markov para cada número do pool
        const markovScores = availablePool.map(n => {
            let score = 0;
            lastDraw.forEach(prev => {
                if (markov[prev] && markov[prev][n]) {
                    score += markov[prev][n];
                }
            });
            return { num: n, score: score + Math.random() * 2 }; // Ruído para diversidade
        });

        markovScores.sort((a, b) => b.score - a.score);

        // Selecionar top com alguma aleatoriedade
        const topMarkov = markovScores.slice(0, needed * 3);
        const shuffled = topMarkov.sort(() => 0.5 - Math.random());

        for (const item of shuffled) {
            if (ticket.length >= validFixed.length + needed) break;
            if (!selected.has(item.num)) {
                selected.add(item.num);
                ticket.push(item.num);
            }
        }

        // Preencher se necessário
        if (ticket.length < validFixed.length + needed) {
            const remaining = availablePool.filter(n => !selected.has(n)).sort(() => 0.5 - Math.random());
            for (let i = 0; i < remaining.length && ticket.length < validFixed.length + needed; i++) {
                ticket.push(remaining[i]);
            }
        }

        ticket.sort((a, b) => a - b);
        return ticket.length === validFixed.length + needed ? ticket : null;
    }

    static getRandomSubset(arr, size) {
        const shuffled = arr.slice().sort(() => 0.5 - Math.random());
        return shuffled.slice(0, size);
    }

    // ═══════════════════════════════════════════
    //  CÁLCULO DE INVESTIMENTO
    // ═══════════════════════════════════════════
    static calculateInvestment(gameType, poolSize) {
        const game = GAMES[gameType];
        if (!game) return null;

        if (poolSize < game.minBet) {
            return { valid: false, message: `Selecione pelo menos ${game.minBet} números.` };
        }

        const totalCombinations = this.nCr(poolSize, game.minBet);
        const totalCost = totalCombinations * game.price;

        let estimates = [];

        estimates.push({
            label: `Garantia Máxima (${game.minBet}pts)`,
            qty: totalCombinations,
            cost: totalCost,
            strategyId: game.strategies[0].match
        });

        game.strategies.forEach(strat => {
            if (strat.match === game.minBet) return;

            let reduction = 1;

            if (gameType === 'lotofacil') {
                if (strat.match === 14) reduction = 25;
                if (strat.match === 13) reduction = 150;
                if (strat.match === 12) reduction = 500;
                if (strat.match === 11) reduction = 1500;
            } else if (gameType === 'megasena') {
                if (strat.match === 5) reduction = 50;
                if (strat.match === 4) reduction = 800;
            } else if (gameType === 'lotomania') {
                if (strat.match === 19) reduction = 15;
                if (strat.match === 18) reduction = 80;
                if (strat.match === 17) reduction = 400;
                if (strat.match === 16) reduction = 2000;
            } else if (gameType === 'duplasena') {
                if (strat.match === 5) reduction = 50;
                if (strat.match === 4) reduction = 800;
            } else if (gameType === 'timemania') {
                if (strat.match === 6) reduction = 20;
                if (strat.match === 5) reduction = 200;
            } else if (gameType === 'diadesorte') {
                if (strat.match === 6) reduction = 15;
                if (strat.match === 5) reduction = 120;
            } else {
                const baseRef = game.draw || game.minBet;
                const diff = baseRef - strat.match;
                reduction = Math.pow(10, Math.min(diff, 5));
            }

            const estQty = Math.max(1, Math.ceil(totalCombinations / reduction));

            if (estQty < totalCombinations) {
                estimates.push({
                    label: `Fechar ${strat.label} (Est.)`,
                    qty: estQty,
                    cost: estQty * game.price,
                    strategyId: strat.match
                });
            }
        });

        return {
            valid: true,
            poolSize,
            totalCombinations,
            totalCost,
            estimates
        };
    }
}
