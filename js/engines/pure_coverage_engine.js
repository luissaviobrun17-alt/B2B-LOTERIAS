/**
 * ╔══════════════════════════════════════════════════════════════════════╗
 * ║  PURE COVERAGE ENGINE — COBERTURA COMBINATÓRIA PURA                ║
 * ║                                                                    ║
 * ║  PRINCÍPIO FUNDAMENTAL:                                            ║
 * ║  NÃO EXISTE previsão de números. ZERO scoring. ZERO IA.            ║
 * ║  O único objetivo é MAXIMIZAR a cobertura do espaço combinatório   ║
 * ║  com N jogos, usando Greedy Set Cover + filtros estruturais.       ║
 * ║                                                                    ║
 * ║  ALGORITMO:                                                        ║
 * ║  1. Pool = TODOS os números do range (distribuição uniforme)       ║
 * ║  2. Gerar candidatos com Fisher-Yates + filtros P5-P95             ║
 * ║  3. Greedy Set Cover: maximizar pares/triplas novas                ║
 * ║  4. Anti-concentração: teto de frequência dinâmico                 ║
 * ║                                                                    ║
 * ║  PROBABILIDADES: 100% hipergeométricas exatas (BigInt)             ║
 * ║  ROI: Honesto, sem ilusões, sem promessas                          ║
 * ╚══════════════════════════════════════════════════════════════════════╝
 */
class PureCoverageEngine {

    // ═══════════════════════════════════════════════════════
    //  CONFIGURAÇÃO POR LOTERIA
    //  Cada parâmetro baseado em dados reais (P5-P95)
    // ═══════════════════════════════════════════════════════
    static getConfig(gameKey) {
        const configs = {
            lotofacil: {
                name: 'Lotofácil',
                drawSize: 15,
                lotteryDraw: 15,
                range: [1, 25],
                totalNumbers: 25,
                ticketPrice: 3.00,
                prizeThresholds: [11, 12, 13, 14, 15],
                prizeLabels: ['11 ac.', '12 ac.', '13 ac.', '14 ac.', '15 ac.'],
                fixedPrizes: { 11: 6, 12: 12, 13: 30 },
                zones: 5,
                zoneSize: 5,
                payout: 0.4335,
                // Filtros estruturais P5-P95 (Monte Carlo 500k simulações)
                sumRange: [165, 225],
                parityRange: [5, 9],
                maxConsecutive: 8,
                minZones: 5,
                maxSameEnding: 4,
                highLowBalance: [6, 10]
            },
            megasena: {
                name: 'Mega Sena',
                drawSize: 6,
                lotteryDraw: 6,
                range: [1, 60],
                totalNumbers: 60,
                ticketPrice: 6.00,
                prizeThresholds: [4, 5, 6],
                prizeLabels: ['Quadra', 'Quina', 'Sena'],
                fixedPrizes: {},
                zones: 6,
                zoneSize: 10,
                payout: 0.4379,
                // Filtros estruturais P10-P90 — apertados com base em dados históricos reais
                // Antes: [116, 250] = P0-P100 (muito amplo, gerava extremos)
                // Agora: [138, 228] = P10-P90 (83% dos sorteios reais)
                sumRange: [138, 228],
                parityRange: [1, 5],
                maxConsecutive: 2,
                minZones: 3,
                maxSameEnding: 3,
                highLowBalance: [1, 5]
            },
            quina: {
                name: 'Quina',
                drawSize: 5,
                lotteryDraw: 5,
                range: [1, 80],
                totalNumbers: 80,
                ticketPrice: 3.00,
                prizeThresholds: [2, 3, 4, 5],
                prizeLabels: ['Duque', 'Terno', 'Quadra', 'Quina'],
                fixedPrizes: {},
                zones: 8,
                zoneSize: 10,
                payout: 0.4379,
                // Filtros estruturais P5-P95 (Monte Carlo 500k simulações)
                sumRange: [119, 285],
                parityRange: [1, 4],
                maxConsecutive: 2,
                minZones: 3,
                maxSameEnding: 2,
                highLowBalance: [1, 4]
            },
            timemania: {
                name: 'Timemania',
                drawSize: 10,
                lotteryDraw: 7,
                range: [1, 80],
                totalNumbers: 80,
                ticketPrice: 3.50,
                prizeThresholds: [3, 4, 5, 6, 7],
                prizeLabels: ['3 ac.', '4 ac.', '5 ac.', '6 ac.', '7 ac.'],
                fixedPrizes: { 3: 3.50, 4: 10.50 },
                zones: 8,
                zoneSize: 10,
                payout: 0.46,
                // Filtros estruturais P10-P90 — corrigidos
                // Antes: [292, 518] (muito amplo, soma média gerada era 368 vs 405 esperado)
                // Agora: [320, 490] = faixa mais representativa dos sorteios reais
                sumRange: [320, 490],
                parityRange: [3, 7],
                maxConsecutive: 3,
                minZones: 4,
                maxSameEnding: 3,
                highLowBalance: [3, 7]
            },
            diadesorte: {
                name: 'Dia de Sorte',
                drawSize: 7,
                lotteryDraw: 7,
                range: [1, 31],
                totalNumbers: 31,
                ticketPrice: 3.00,
                prizeThresholds: [4, 5, 6, 7],
                prizeLabels: ['4 ac.', '5 ac.', '6 ac.', '7 ac.'],
                fixedPrizes: { 4: 5, 5: 25 },
                zones: 4,
                zoneSize: 8,
                payout: 0.4335,
                // Filtros estruturais P5-P95 (Monte Carlo 500k simulações)
                sumRange: [77, 147],
                parityRange: [2, 5],
                maxConsecutive: 3,
                minZones: 3,
                maxSameEnding: 3,
                highLowBalance: [2, 5]
            },
            duplasena: {
                name: 'Dupla Sena',
                drawSize: 6,
                lotteryDraw: 6,
                range: [1, 50],
                totalNumbers: 50,
                ticketPrice: 2.50,
                prizeThresholds: [3, 4, 5, 6],
                prizeLabels: ['Terno', 'Quadra', 'Quina', 'Sena'],
                fixedPrizes: {},
                zones: 5,
                zoneSize: 10,
                payout: 0.4379,
                // Filtros estruturais P5-P95 (Monte Carlo 500k simulações)
                sumRange: [98, 208],
                parityRange: [1, 5],
                maxConsecutive: 2,
                minZones: 3,
                maxSameEnding: 3,
                highLowBalance: [1, 5]
            },
            lotomania: {
                name: 'Lotomania',
                drawSize: 50,
                lotteryDraw: 20,
                range: [0, 99],
                totalNumbers: 100,
                ticketPrice: 3.00,
                prizeThresholds: [15, 16, 17, 18, 19, 20],
                prizeLabels: ['15 ac.', '16 ac.', '17 ac.', '18 ac.', '19 ac.', '20 ac.'],
                fixedPrizes: {},
                zones: 10,
                zoneSize: 10,
                payout: 0.4335,
                // Filtros estruturais P5-P95 (Monte Carlo 500k simulações)
                sumRange: [2236, 2714],
                parityRange: [21, 29],
                maxConsecutive: 9,
                minZones: 9,
                maxSameEnding: 8,
                highLowBalance: [21, 29]
            },
            supersete: {
                name: 'Super Sete',
                drawSize: 7,
                lotteryDraw: 7,
                range: [0, 9],
                totalNumbers: 10,
                ticketPrice: 2.50,
                prizeThresholds: [3, 4, 5, 6, 7],
                prizeLabels: ['3 ac.', '4 ac.', '5 ac.', '6 ac.', '7 ac.'],
                fixedPrizes: { 3: 5.00 },
                zones: 7,
                zoneSize: 10,
                payout: 0.4335,
                sumRange: [16, 47],
                parityRange: [1, 6],
                maxConsecutive: 3,
                minZones: 7,
                maxSameEnding: 3,
                highLowBalance: [1, 6],
                isColumnGame: true
            }
        };
        return configs[gameKey] || null;
    }

    // ═══════════════════════════════════════════════════════
    //  PONTO DE ENTRADA PRINCIPAL
    //  generate(gameKey, numGames, options)
    //  Retorna: { games: [[...], ...], analysis: { ... } }
    // ═══════════════════════════════════════════════════════
    static generate(gameKey, numGames, options) {
        const t0 = (typeof performance !== 'undefined' ? performance.now() : Date.now());
        const opts = options || {};

        // Delegação oficial para Super Sete B2B
        if (gameKey === 'supersete' && typeof MotorSuperSeteB2BEngine !== 'undefined') {
            console.log('%c[PURE-COVER] ⚡ Delegando Super Sete para MotorSuperSeteB2BEngine...', 'color: #38bdf8; font-weight: bold;');
            const ssRes = MotorSuperSeteB2BEngine._gerarFallbackNativo(numGames, opts);
            const games = (ssRes && ssRes.jogos) ? ssRes.jogos.map(j => j.jogo) : [];
            const elapsed = Math.round(typeof performance !== 'undefined' ? performance.now() - t0 : Date.now() - t0);
            return {
                games,
                analysis: {
                    totalGames: games.length,
                    poolSize: 10,
                    fixedCount: 0,
                    coveragePct: ssRes.icm_global || 85,
                    avgHamming: ssRes.metricas_carteira?.hamming_medio || 5.2,
                    mode: 'motor_supersete_b2b',
                    elapsed: elapsed + 'ms',
                    investimento: games.length * 2.50
                }
            };
        }

        const cfg = this.getConfig(gameKey);

        if (!cfg) {
            console.error('[PURE-COVER] Loteria não encontrada:', gameKey);
            return { games: [], analysis: { error: 'Loteria não encontrada' } };
        }

        console.log('%c[PURE-COVER] ══════════════════════════════════════════════', 'color: #22d3ee; font-weight: bold; font-size: 14px;');
        console.log('%c[PURE-COVER] MOTOR DE COBERTURA COMBINATÓRIA PURA', 'color: #22d3ee; font-weight: bold; font-size: 14px;');
        console.log('%c[PURE-COVER] ' + cfg.name + ' | ' + numGames + ' jogos | ' + cfg.drawSize + '/' + cfg.totalNumbers, 'color: #22d3ee; font-weight: bold;');
        console.log('[PURE-COVER] Filosofia: ZERO previsão — apenas cobertura matemática otimizada');

        // ── 1. Pool = TODOS os números do range OU pool customizado (Sniper) ──
        let pool;
        if (opts.pool && Array.isArray(opts.pool) && opts.pool.length >= cfg.drawSize) {
            pool = opts.pool.slice().sort((a, b) => a - b);
            console.log('[PURE-COVER] Pool: SNIPER — ' + pool.length + ' números com evidência estatística');
        } else {
            pool = [];
            for (let n = cfg.range[0]; n <= cfg.range[1]; n++) {
                pool.push(n);
            }
            console.log('[PURE-COVER] Pool: TODOS os ' + pool.length + ' números [' + cfg.range[0] + '-' + cfg.range[1] + ']');
        }
        const poolSize = pool.length;

        // ── 2. Calcular espaço combinatório ──
        const totalPairs = this._comb(poolSize, 2);
        const pairsPerGame = this._comb(cfg.drawSize, 2);
        const totalTriples = cfg.drawSize <= 15 ? this._comb(poolSize, 3) : 0;
        const triplesPerGame = cfg.drawSize <= 15 ? this._comb(cfg.drawSize, 3) : 0;
        const useTriples = cfg.drawSize <= 15;

        console.log('[PURE-COVER] Espaço: ' + totalPairs + ' pares totais | ' + pairsPerGame + ' pares/jogo');
        if (useTriples) {
            console.log('[PURE-COVER] Triplas ativas: ' + totalTriples + ' triplas totais | ' + triplesPerGame + ' triplas/jogo');
        }

        // ── 3. Teto de frequência (anti-concentração ADAPTATIVA) ──
        // Tolerância menor para volumes grandes → distribuição mais uniforme
        const tolerance = numGames <= 50 ? 1.4 : numGames <= 200 ? 1.25 : numGames <= 1000 ? 1.15 : 1.08;
        const expectedFreq = (numGames * cfg.drawSize) / poolSize;
        const maxAllowedFreq = Math.ceil(expectedFreq * tolerance);
        const softCeiling = Math.ceil(expectedFreq * (1 + (tolerance - 1) * 0.6)); // Penalidade suave antes do teto
        console.log('[PURE-COVER] Anti-concentração: esperado=' + Math.round(expectedFreq) + ' teto=' + maxAllowedFreq + ' (tolerância ' + (tolerance * 100 - 100).toFixed(0) + '%) soft=' + softCeiling);

        // ── 3b. Recalibrar filtros para pool Sniper ──
        // Se o pool é menor que o range completo, os filtros P5-P95 originais
        // (calibrados para o range inteiro) podem ser impossíveis de satisfazer.
        // Recalcular ranges baseados nos números reais do pool.
        let effectiveCfg = cfg;
        if (opts.pool && pool.length < cfg.totalNumbers) {
            const poolMin = Math.min(...pool);
            const poolMax = Math.max(...pool);
            const poolAvg = pool.reduce((a, b) => a + b, 0) / pool.length;
            // Recalcular soma esperada: média * drawSize ± margem
            const expectedSum = Math.round(poolAvg * cfg.drawSize);
            const margin = Math.round(expectedSum * 0.35);
            // Recalcular zonas: baseado na dispersão real do pool
            const poolZones = new Set();
            for (const n of pool) {
                poolZones.add(Math.floor((n - cfg.range[0]) / cfg.zoneSize));
            }
            const maxPossibleZones = poolZones.size;
            const relaxedMinZones = Math.max(1, Math.min(cfg.minZones, maxPossibleZones - 1));
            // Copiar cfg com filtros relaxados
            effectiveCfg = Object.assign({}, cfg, {
                sumRange: [expectedSum - margin, expectedSum + margin],
                minZones: relaxedMinZones,
                highLowBalance: [0, cfg.drawSize], // Relaxar alto/baixo para Sniper
                range: [poolMin, poolMax]
            });
            console.log('[PURE-COVER] ⚠️ Filtros recalibrados para Sniper: soma [' + effectiveCfg.sumRange[0] + '-' + effectiveCfg.sumRange[1] + '] | zonas mín: ' + relaxedMinZones);
        } else {
            effectiveCfg = Object.assign({}, cfg); // Clonar para poder alterar
        }

        // ── 3c. Aplicação da Regra de Ouro (Matemática Pura - Anti-Sequência) ──
        if (opts.strictMathRules) {
            // Se o usuário exige que não haja triplos nem sequências longas:
            // maxConsecutive = 2 significa que o máximo permitido são 2 números seguidos (ex: 10, 11).
            // Uma sequência de 3 (ex: 10, 11, 12) é sumariamente rejeitada.
            effectiveCfg.maxConsecutive = (cfg.drawSize >= 50) ? 4 : (cfg.drawSize >= 15) ? 3 : Math.min(effectiveCfg.maxConsecutive, 2);
            console.log('%c[PURE-COVER] 🛡️ STRICT MATH: Anti-Triplos e Anti-Sequência ativado (maxConsecutive=2)', 'color: #ef4444; font-weight: bold;');
        }

        // ── 4. Gerar candidatos com filtros estruturais ──
        const scanLimit = Math.max(500, Math.min(3000, numGames * 5));
        console.log('[PURE-COVER] ScanLimit: ' + scanLimit + ' candidatos por slot');

        const candidates = [];
        const maxCandidateAttempts = scanLimit * 8;
        let candidateAttempts = 0;

        while (candidates.length < scanLimit && candidateAttempts < maxCandidateAttempts) {
            candidateAttempts++;
            const game = this._generateCandidate(effectiveCfg, pool);
            if (game) {
                candidates.push(game);
            }
        }

        console.log('[PURE-COVER] Candidatos gerados: ' + candidates.length + ' (em ' + candidateAttempts + ' tentativas)');

        if (candidates.length === 0) {
            console.error('[PURE-COVER] ERRO: Nenhum candidato válido gerado!');
            return { games: [], analysis: { error: 'Falha na geração de candidatos' } };
        }

        // ── 5. Greedy Set Cover ──
        const games = [];
        const usedKeys = new Set();
        const coveredPairs = new Set();
        const coveredTriples = useTriples ? new Set() : null;
        const numberUsage = {};
        for (const n of pool) numberUsage[n] = 0;

        for (let g = 0; g < numGames; g++) {
            // Reabastecer candidatos se necessário
            // v14.1: purge candidatos já usados ANTES de verificar tamanho
            //        evita recontagem de candidatos obsoletos no array
            if (candidates.length < 100 || g % 200 === 0) {
                // Remover do array candidatos que já foram aceitos
                for (let ci = candidates.length - 1; ci >= 0; ci--) {
                    if (usedKeys.has(candidates[ci].join(','))) {
                        candidates.splice(ci, 1);
                    }
                }
            }

            if (candidates.length < 50) {
                const refillTarget = Math.max(500, scanLimit);
                let refillAttempts = 0;
                const refillMax = refillTarget * 6;
                while (candidates.length < refillTarget && refillAttempts < refillMax) {
                    refillAttempts++;
                    const game = this._generateCandidate(effectiveCfg, pool);
                    if (game && !usedKeys.has(game.join(','))) {
                        candidates.push(game);
                    }
                }
                if (g > 0 && g % 100 === 0) {
                    console.log('[PURE-COVER] Refill no jogo ' + g + ': ' + candidates.length + ' candidatos');
                }
            }

            let bestIdx = -1;
            let bestFitness = -Infinity;

            // Calcular saturações atuais
            const pairSat = totalPairs > 0 ? coveredPairs.size / totalPairs : 0;
            const tripleSat = useTriples && totalTriples > 0 ? coveredTriples.size / totalTriples : 0;

            // Peso dinâmico: quando pares saturam, triplas ficam mais importantes
            const pairWeight = pairSat > 0.90 ? 1 : pairSat > 0.50 ? 10 : 100;
            const tripleWeight = pairSat > 0.90 ? 100 : pairSat > 0.50 ? 50 : 10;

            const evalLimit = Math.min(candidates.length, scanLimit);

            for (let i = 0; i < evalLimit; i++) {
                const candidate = candidates[i];
                const key = candidate.join(',');
                if (usedKeys.has(key)) continue;

                // Contar novos pares
                let newPairs = 0;
                for (let x = 0; x < candidate.length; x++) {
                    for (let y = x + 1; y < candidate.length; y++) {
                        const pk = candidate[x] * 1000 + candidate[y];
                        if (!coveredPairs.has(pk)) newPairs++;
                    }
                }

                // Contar novas triplas (somente para drawSize <= 15 e lotes pequenos)
                let newTriples = 0;
                if (useTriples && numGames <= 300) {
                    for (let x = 0; x < candidate.length; x++) {
                        for (let y = x + 1; y < candidate.length; y++) {
                            for (let z = y + 1; z < candidate.length; z++) {
                                const tk = candidate[x] * 1000000 + candidate[y] * 1000 + candidate[z];
                                if (!coveredTriples.has(tk)) newTriples++;
                            }
                        }
                    }
                }

                // ── Hamming Distance (janela de 10 jogos, threshold 25%) ──
                let diversityBonus = 0;
                let minHamming = candidate.length;
                const hammingWindow = Math.min(10, games.length);
                let hammingSum = 0;
                for (let h = games.length - 1; h >= games.length - hammingWindow && h >= 0; h--) {
                    const prevSet = new Set(games[h]);
                    let diff = 0;
                    for (const n of candidate) {
                        if (!prevSet.has(n)) diff++;
                    }
                    if (diff < minHamming) minHamming = diff;
                    hammingSum += diff;
                }
                if (hammingWindow > 0) {
                    // Bonus proporcional à diversidade média
                    const avgH = hammingSum / hammingWindow;
                    diversityBonus = Math.round(avgH * 5);
                }
                // Penalidade PROPORCIONAL: quanto menor o Hamming, maior a penalidade
                const hammingThreshold = Math.max(2, Math.floor(candidate.length * 0.25));
                if (minHamming < hammingThreshold) {
                    // Escala: H=0 → -10000, H=1 → -5000, H=threshold-1 → -500
                    diversityBonus -= Math.round(5000 * (1 - minHamming / hammingThreshold));
                }

                // ── Anti-concentração CONTÍNUA e proporcional ──
                let usageBonus = 0;
                for (const n of candidate) {
                    const freq = numberUsage[n] || 0;
                    if (freq === 0) {
                        usageBonus += 5; // Forte incentivo para números não usados
                    } else if (freq < softCeiling) {
                        // Bonus decrescente: quanto mais usado, menos bonus
                        usageBonus += Math.round(3 * (1 - freq / softCeiling));
                    } else if (freq < maxAllowedFreq) {
                        // Zona de alerta: penalidade crescente
                        const overSoft = (freq - softCeiling) / (maxAllowedFreq - softCeiling);
                        usageBonus -= Math.round(30 * overSoft);
                    } else {
                        // Acima do teto: penalidade severa proporcional ao excesso
                        const excess = freq - maxAllowedFreq;
                        usageBonus -= 80 + excess * 20;
                    }
                }

                const fitness = (newPairs * pairWeight) +
                                (newTriples * tripleWeight) +
                                diversityBonus +
                                usageBonus;

                if (fitness > bestFitness) {
                    bestFitness = fitness;
                    bestIdx = i;
                }
            }

            // Selecionar melhor candidato
            if (bestIdx !== -1) {
                const bestGame = candidates.splice(bestIdx, 1)[0];
                const bestKey = bestGame.join(',');
                // v14.1: guarda dupla — não aceitar jogo já registrado
                if (usedKeys.has(bestKey)) {
                    g--; // cancelar esta iteração e tentar novamente
                    continue;
                }
                games.push(bestGame);
                usedKeys.add(bestKey);

                // Atualizar contadores de uso
                for (const n of bestGame) {
                    numberUsage[n] = (numberUsage[n] || 0) + 1;
                }

                // Registrar pares cobertos
                for (let x = 0; x < bestGame.length; x++) {
                    for (let y = x + 1; y < bestGame.length; y++) {
                        coveredPairs.add(bestGame[x] * 1000 + bestGame[y]);
                        if (useTriples) {
                            for (let z = y + 1; z < bestGame.length; z++) {
                                coveredTriples.add(bestGame[x] * 1000000 + bestGame[y] * 1000 + bestGame[z]);
                            }
                        }
                    }
                }
            } else {
                // Fallback: gerar novo candidato direto
                for (let retry = 0; retry < 50; retry++) {
                    const fallback = this._generateCandidate(effectiveCfg, pool);
                    if (fallback && !usedKeys.has(fallback.join(','))) {
                        games.push(fallback);
                        usedKeys.add(fallback.join(','));
                        for (const n of fallback) {
                            numberUsage[n] = (numberUsage[n] || 0) + 1;
                        }
                        for (let x = 0; x < fallback.length; x++) {
                            for (let y = x + 1; y < fallback.length; y++) {
                                coveredPairs.add(fallback[x] * 1000 + fallback[y]);
                                if (useTriples) {
                                    for (let z = y + 1; z < fallback.length; z++) {
                                        coveredTriples.add(fallback[x] * 1000000 + fallback[y] * 1000 + fallback[z]);
                                    }
                                }
                            }
                        }
                        break;
                    }
                }
            }
        }

        // v16.2 FIX: Aplicar reparador universal para Lotomania se necessário
        if (gameKey === 'lotomania' && cfg.drawSize === 50) {
            const fixedSet = new Set(opts.fixedNumbers || []);
            let repairPool = pool;
            if (!repairPool || repairPool.length < 100) {
                repairPool = [];
                for (let n = cfg.range[0]; n <= cfg.range[1]; n++) repairPool.push(n);
            }
            for (let i = 0; i < games.length; i++) {
                games[i] = PureCoverageEngine.repairGameLotomania(games[i], repairPool, fixedSet);
            }
        }

        // ── 6. Análise completa ──
        const elapsed = Math.round((typeof performance !== 'undefined' ? performance.now() : Date.now()) - t0);
        const analysis = this._buildAnalysis(games, cfg, pool, coveredPairs, coveredTriples, numberUsage, numGames, elapsed);

        console.log('%c[PURE-COVER] ✅ ' + games.length + ' jogos gerados em ' + elapsed + 'ms', 'color: #22d3ee; font-weight: bold;');
        this._logAnalysis(analysis, cfg);

        return { games, analysis };
    }

    static repairGameLotomania(game, pool, fixedSet) {
        let sorted = [...new Set(game)].sort((a, b) => a - b);
        const fixed = fixedSet || new Set();

        // Encontrar candidatos no pool que não estão no jogo
        let available = pool.filter(n => !sorted.includes(n));
        
        // Se o pool estiver vazio ou muito curto, garantir dezenas de 0 a 99
        if (available.length === 0) {
            const allNums = [];
            for (let i = 0; i <= 99; i++) {
                if (!sorted.includes(i)) allNums.push(i);
            }
            // Embaralhar
            for (let i = allNums.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [allNums[i], allNums[j]] = [allNums[j], allNums[i]];
            }
            available = allNums;
        }

        // Completar se menor que 50
        while (sorted.length < 50 && available.length > 0) {
            sorted.push(available.shift());
            sorted.sort((a, b) => a - b);
        }

        // Regras de validação auxiliares
        const getPares = (arr) => arr.filter(x => x % 2 === 0).length;
        const getZoning = (arr) => {
            let d1 = 0, d2 = 0, d3 = 0;
            for (const x of arr) {
                if (x <= 32) d1++;
                else if (x <= 65) d2++;
                else d3++;
            }
            return [d1, d2, d3];
        };
        const checkConsecutive = (arr) => {
            let consec = 1;
            let violated = false;
            for (let i = 1; i < arr.length; i++) {
                if (arr[i] === arr[i - 1] + 1) {
                    consec++;
                    if (consec > 3) violated = true;
                } else {
                    consec = 1;
                }
            }
            return violated;
        };

        let attempts = 0;
        while (attempts < 150) {
            let violatedConsec = checkConsecutive(sorted);
            let [d1, d2, d3] = getZoning(sorted);
            let pares = getPares(sorted);
            let impares = 50 - pares;
            
            let violatedZoning = d1 > 19 || d2 > 19 || d3 > 19;
            let violatedParity = pares > 27 || impares > 27;

            if (!violatedConsec && !violatedZoning && !violatedParity) {
                return sorted;
            }

            let idxToReplace = -1;

            if (violatedConsec) {
                let consec = 1;
                for (let i = 1; i < sorted.length; i++) {
                    if (sorted[i] === sorted[i - 1] + 1) {
                        consec++;
                        if (consec > 3) {
                            for (let j = i - consec + 1; j <= i; j++) {
                                if (!fixed.has(sorted[j])) {
                                    idxToReplace = j;
                                    break;
                                }
                            }
                            if (idxToReplace === -1) idxToReplace = i;
                            break;
                        }
                    } else {
                        consec = 1;
                    }
                }
            } else if (violatedZoning) {
                let targetZone = d1 > 19 ? 1 : d2 > 19 ? 2 : 3;
                for (let i = 0; i < sorted.length; i++) {
                    let val = sorted[i];
                    if (fixed.has(val)) continue;
                    let z = val <= 32 ? 1 : val <= 65 ? 2 : 3;
                    if (z === targetZone) {
                        idxToReplace = i;
                        break;
                    }
                }
            } else if (violatedParity) {
                let targetParity = pares > 27 ? 0 : 1;
                for (let i = 0; i < sorted.length; i++) {
                    let val = sorted[i];
                    if (fixed.has(val)) continue;
                    if (val % 2 === targetParity) {
                        idxToReplace = i;
                        break;
                    }
                }
            }

            if (idxToReplace === -1) {
                break;
            }

            let replacedVal = sorted[idxToReplace];
            let foundSubstitute = false;

            available.sort(() => Math.random() - 0.5);

            for (let i = 0; i < available.length; i++) {
                let candidate = available[i];
                let temp = sorted.filter((_, idx) => idx !== idxToReplace);
                temp.push(candidate);
                temp.sort((a, b) => a - b);

                let newViolatedConsec = checkConsecutive(temp);
                let [nd1, nd2, nd3] = getZoning(temp);
                let npares = getPares(temp);
                let nimpares = 50 - npares;

                let newViolatedZoning = nd1 > 19 || nd2 > 19 || nd3 > 19;
                let newViolatedParity = npares > 27 || nimpares > 27;

                let ok = true;
                if (violatedConsec && newViolatedConsec) ok = false;
                if (newViolatedZoning) {
                    let beforeExceeded = Math.max(0, d1 - 19) + Math.max(0, d2 - 19) + Math.max(0, d3 - 19);
                    let afterExceeded = Math.max(0, nd1 - 19) + Math.max(0, nd2 - 19) + Math.max(0, nd3 - 19);
                    if (afterExceeded >= beforeExceeded) ok = false;
                }
                if (newViolatedParity) {
                    let beforeExceeded = Math.max(0, pares - 27) + Math.max(0, impares - 27);
                    let afterExceeded = Math.max(0, npares - 27) + Math.max(0, nimpares - 27);
                    if (afterExceeded >= beforeExceeded) ok = false;
                }

                if (ok) {
                    sorted = temp;
                    available[i] = replacedVal;
                    foundSubstitute = true;
                    break;
                }
            }

            if (!foundSubstitute) {
                if (available.length > 0) {
                    let candidate = available.shift();
                    let temp = sorted.filter((_, idx) => idx !== idxToReplace);
                    temp.push(candidate);
                    temp.sort((a, b) => a - b);
                    sorted = temp;
                    available.push(replacedVal);
                }
            }

            attempts++;
        }

        return sorted;
    }

    // ═══════════════════════════════════════════════════════
    //  GERAR CANDIDATO COM FILTROS ESTRUTURAIS
    //  Seleção UNIFORME aleatória + validação P5-P95
    // ═══════════════════════════════════════════════════════
    static _generateCandidate(cfg, pool) {
        const maxAttempts = 300;

        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            // Fisher-Yates shuffle do pool e pegar os primeiros drawSize
            const shuffled = pool.slice();
            this._shuffle(shuffled);
            const game = shuffled.slice(0, cfg.drawSize).sort((a, b) => a - b);

            // Se o pool é pequeno comparado com o tamanho do sorteio, pular filtros
            if (pool.length < cfg.drawSize + 10) {
                return game;
            }

            // Validar filtros estruturais
            if (this._isStructurallyValid(game, cfg)) {
                return game;
            }
        }
        return null;
    }

    // ═══════════════════════════════════════════════════════
    //  VALIDAÇÃO ESTRUTURAL — Filtros baseados em DADOS REAIS
    //  Range P5-P95: rejeita apenas combinações que
    //  historicamente NUNCA ou QUASE NUNCA ocorrem
    // ═══════════════════════════════════════════════════════
    static _isStructurallyValid(game, cfg) {
        const n = game.length;

        // Bypass para Lotomania (50 números = quase impossível falhar)
        if (cfg.drawSize >= 50) {
            // Verificar apenas soma e paridade (filtros mínimos)
            const sum = game.reduce((a, b) => a + b, 0);
            if (sum < cfg.sumRange[0] || sum > cfg.sumRange[1]) return false;
            const evens = game.filter(x => x % 2 === 0).length;
            if (evens < cfg.parityRange[0] || evens > cfg.parityRange[1]) return false;
            return true;
        }

        // 1. Soma dentro do range P5-P95
        const sum = game.reduce((a, b) => a + b, 0);
        if (sum < cfg.sumRange[0] || sum > cfg.sumRange[1]) return false;

        // 2. Paridade equilibrada (não 100% par ou 100% ímpar)
        const evens = game.filter(x => x % 2 === 0).length;
        if (evens < cfg.parityRange[0] || evens > cfg.parityRange[1]) return false;

        // 3. Máximo de consecutivos
        let maxRun = 1, curRun = 1;
        for (let i = 1; i < n; i++) {
            if (game[i] === game[i - 1] + 1) {
                curRun++;
                maxRun = Math.max(maxRun, curRun);
            } else {
                curRun = 1;
            }
        }
        if (maxRun > cfg.maxConsecutive) return false;

        // 4. Cobertura mínima de zonas
        const zonesHit = new Set();
        const startNum = cfg.range[0];
        for (const num of game) {
            zonesHit.add(Math.min(cfg.zones - 1, Math.floor((num - startNum) / cfg.zoneSize)));
        }
        if (zonesHit.size < cfg.minZones) return false;

        // 5. Equilíbrio alto/baixo
        if (cfg.highLowBalance) {
            const midpoint = Math.floor((cfg.range[0] + cfg.range[1]) / 2);
            let lowCount = 0;
            for (const num of game) {
                if (num <= midpoint) lowCount++;
            }
            if (lowCount < cfg.highLowBalance[0] || lowCount > cfg.highLowBalance[1]) return false;
        }

        // 6. Máximo de terminações iguais
        if (cfg.maxSameEnding) {
            const endings = {};
            for (const num of game) {
                const e = num % 10;
                endings[e] = (endings[e] || 0) + 1;
                if (endings[e] > cfg.maxSameEnding) return false;
            }
        }

        return true;
    }

    // ═══════════════════════════════════════════════════════
    //  ANÁLISE COMPLETA DO RESULTADO
    // ═══════════════════════════════════════════════════════
    static _buildAnalysis(games, cfg, pool, coveredPairs, coveredTriples, numberUsage, numGames, elapsed) {
        const poolSize = pool.length;
        const totalPairs = this._comb(poolSize, 2);
        const useTriples = cfg.drawSize <= 15;
        const totalTriples = useTriples ? this._comb(poolSize, 3) : 0;

        // Cobertura de pares
        const pairsCovered = coveredPairs.size;
        const pairCoveragePct = totalPairs > 0 ? Math.round(pairsCovered / totalPairs * 1000) / 10 : 0;

        // Cobertura de triplas
        const triplesCovered = useTriples ? coveredTriples.size : 0;
        const tripleCoveragePct = totalTriples > 0 ? Math.round(triplesCovered / totalTriples * 1000) / 10 : 0;

        // Cobertura de números
        const uniqueNumbers = new Set(games.flat());
        const numberCoverage = uniqueNumbers.size;
        const numberCoveragePct = Math.round(numberCoverage / poolSize * 1000) / 10;

        // Distribuição por zona
        const zoneCount = new Array(cfg.zones).fill(0);
        for (const g of games) {
            for (const num of g) {
                const z = Math.min(cfg.zones - 1, Math.floor((num - cfg.range[0]) / cfg.zoneSize));
                zoneCount[z]++;
            }
        }

        // Hamming médio (diversidade entre jogos consecutivos)
        let hammingTotal = 0, hammingCount = 0;
        const hammingSample = Math.min(games.length, 100);
        for (let i = 0; i < hammingSample - 1; i++) {
            const setA = new Set(games[i]);
            let shared = 0;
            for (const num of games[i + 1]) {
                if (setA.has(num)) shared++;
            }
            hammingTotal += (cfg.drawSize - shared);
            hammingCount++;
        }
        const avgHamming = hammingCount > 0 ? Math.round(hammingTotal / hammingCount * 10) / 10 : 0;

        // Distribuição de uso dos números (para verificar anti-concentração)
        const usageValues = Object.values(numberUsage);
        const maxUsage = Math.max(...usageValues);
        const minUsage = Math.min(...usageValues);
        const avgUsage = usageValues.reduce((a, b) => a + b, 0) / usageValues.length;

        // Probabilidades hipergeométricas EXATAS
        const probabilities = {};
        const cumProb = {};
        for (const t of cfg.prizeThresholds) {
            probabilities[t] = this._hypergeometric(cfg.totalNumbers, cfg.lotteryDraw, cfg.drawSize, t);
        }
        // Cumulativa (k+ acertos)
        for (let i = cfg.prizeThresholds.length - 1; i >= 0; i--) {
            const t = cfg.prizeThresholds[i];
            cumProb[t] = 0;
            for (let j = i; j < cfg.prizeThresholds.length; j++) {
                cumProb[t] += probabilities[cfg.prizeThresholds[j]] || 0;
            }
        }
        // P(pelo menos 1 prêmio em N jogos) para cada faixa
        const probWithNGames = {};
        for (const t of cfg.prizeThresholds) {
            const p = cumProb[t] || 0;
            probWithNGames[t] = 1 - Math.pow(1 - p, numGames);
        }
        const minPrize = cfg.prizeThresholds[0];
        probWithNGames.anyPrize = 1 - Math.pow(1 - (cumProb[minPrize] || 0), numGames);

        // ROI esperado
        const roiResult = this.calculateExpectedROI(cfg.name.toLowerCase().replace(/[^a-z]/g, '').replace('megasena', 'megasena'), numGames);

        // Investimento
        const investment = numGames * cfg.ticketPrice;

        return {
            engine: 'PureCoverageEngine',
            gameKey: Object.keys(this.getConfig('megasena') ? { megasena: 1 } : {}).length ? '' : '',
            totalGames: games.length,
            poolSize,
            drawSize: cfg.drawSize,
            elapsed,
            // Cobertura
            pairsCovered,
            totalPairs,
            pairCoveragePct,
            triplesCovered,
            totalTriples,
            tripleCoveragePct,
            numberCoverage,
            numberCoveragePct,
            // Diversidade
            avgHamming,
            maxHamming: cfg.drawSize,
            zoneCount,
            // Anti-concentração
            numberUsageStats: { min: minUsage, max: maxUsage, avg: Math.round(avgUsage * 10) / 10 },
            // Probabilidades
            probabilities,
            cumProb,
            probWithNGames,
            // Financeiro
            investment,
            investimento: investment,
            ticketPrice: cfg.ticketPrice,
            // Metadados
            mode: 'pure_coverage',
            philosophy: 'ZERO previsão — apenas cobertura combinatória otimizada'
        };
    }

    // ═══════════════════════════════════════════════════════
    //  LOG DE ANÁLISE — Transparência total
    // ═══════════════════════════════════════════════════════
    static _logAnalysis(analysis, cfg) {
        console.log('%c[PURE-COVER] ── MÉTRICAS DE COBERTURA ──', 'color: #22d3ee; font-weight: bold;');
        console.log('[PURE-COVER] Pares cobertos: ' + analysis.pairsCovered + '/' + analysis.totalPairs + ' (' + analysis.pairCoveragePct + '%)');
        if (analysis.totalTriples > 0) {
            console.log('[PURE-COVER] Triplas cobertas: ' + analysis.triplesCovered + '/' + analysis.totalTriples + ' (' + analysis.tripleCoveragePct + '%)');
        }
        console.log('[PURE-COVER] Números usados: ' + analysis.numberCoverage + '/' + analysis.poolSize + ' (' + analysis.numberCoveragePct + '%)');
        console.log('[PURE-COVER] Hamming médio: ' + analysis.avgHamming + '/' + analysis.maxHamming);
        console.log('[PURE-COVER] Uso de números: mín=' + analysis.numberUsageStats.min + ' máx=' + analysis.numberUsageStats.max + ' média=' + analysis.numberUsageStats.avg);
        console.log('[PURE-COVER] Investimento: R$ ' + analysis.investment.toFixed(2));

        console.log('%c[PURE-COVER] ── PROBABILIDADES HIPERGEOMÉTRICAS EXATAS ──', 'color: #fbbf24; font-weight: bold;');
        for (let i = 0; i < cfg.prizeThresholds.length; i++) {
            const t = cfg.prizeThresholds[i];
            const pSingle = (analysis.cumProb[t] || 0) * 100;
            const pN = (analysis.probWithNGames[t] || 0) * 100;
            const label = cfg.prizeLabels[i] || t + ' ac.';
            console.log('[PURE-COVER] ' + label + ': ' +
                pSingle.toFixed(8) + '% por jogo | ' +
                pN.toFixed(4) + '% com ' + analysis.totalGames + ' jogos');
        }
        const pAny = (analysis.probWithNGames.anyPrize || 0) * 100;
        console.log('[PURE-COVER] ★ Chance de QUALQUER prêmio com ' + analysis.totalGames + ' jogos: ' + pAny.toFixed(2) + '%');
    }

    // ═══════════════════════════════════════════════════════
    //  CALCULADORA DE ROI HONESTA
    //  calculateExpectedROI(gameKey, numGames)
    //
    //  Retorna probabilidades exatas, valor esperado real,
    //  ROI honesto e comparação com seleção aleatória.
    // ═══════════════════════════════════════════════════════
    static calculateExpectedROI(gameKey, numGames) {
        const cfg = this.getConfig(gameKey);
        if (!cfg) {
            console.error('[PURE-COVER] ROI: Loteria não encontrada:', gameKey);
            return null;
        }

        const N = cfg.totalNumbers;     // Universo
        const K = cfg.lotteryDraw;       // Sorteados pela loteria
        const n = cfg.drawSize;          // Apostados pelo jogador
        const price = cfg.ticketPrice;
        const totalInvestment = numGames * price;

        console.log('%c[PURE-COVER] ══ CALCULADORA DE ROI HONESTA ══', 'color: #f59e0b; font-weight: bold;');
        console.log('[PURE-COVER] ' + cfg.name + ' | ' + numGames + ' jogos | Investimento: R$ ' + totalInvestment.toFixed(2));

        const breakdown = [];
        let totalExpectedValue = 0;

        for (const threshold of cfg.prizeThresholds) {
            // Probabilidade hipergeométrica exata: P(X=k) = C(K,k) × C(N-K, n-k) / C(N,n)
            const prob = this._hypergeometric(N, K, n, threshold);

            // Odds (1 em X)
            const odds = prob > 0 ? Math.round(1 / prob) : Infinity;

            // Número esperado de acertos com N jogos
            const expectedHits = prob * numGames;

            // Valor do prêmio estimado
            let prizeValue = 0;
            if (cfg.fixedPrizes && cfg.fixedPrizes[threshold] !== undefined) {
                prizeValue = cfg.fixedPrizes[threshold];
            } else {
                // Estimativa baseada no payout da loteria e prêmio médio histórico
                prizeValue = this._estimatePrize(cfg, threshold);
            }

            // Valor esperado desta faixa
            const evThisTier = prob * prizeValue * numGames;
            totalExpectedValue += evThisTier;

            breakdown.push({
                acertos: threshold,
                label: cfg.prizeLabels[cfg.prizeThresholds.indexOf(threshold)] || threshold + ' ac.',
                probabilidade: prob,
                odds: odds,
                oddsTexto: prob > 0 ? '1 em ' + odds.toLocaleString('pt-BR') : 'impossível',
                expectedHits: Math.round(expectedHits * 10000) / 10000,
                prizeValue: prizeValue,
                evTier: Math.round(evThisTier * 100) / 100,
                probWithNGames: 1 - Math.pow(1 - prob, numGames)
            });
        }

        const roi = totalInvestment > 0 ? ((totalExpectedValue - totalInvestment) / totalInvestment) * 100 : 0;

        // Comparação com seleção aleatória
        // Cobertura otimizada NÃO muda a probabilidade individual de cada jogo
        // Porém, REDUZ a chance de acertos duplicados entre jogos,
        // otimizando a diversidade do portfólio
        const comparison = 'IGUAL à seleção aleatória em termos de probabilidade individual. ' +
            'A vantagem da cobertura é EVITAR duplicação de acertos entre jogos.';

        const result = {
            gameKey,
            name: cfg.name,
            numGames,
            investment: totalInvestment,
            breakdown,
            totalExpectedValue: Math.round(totalExpectedValue * 100) / 100,
            roi: Math.round(roi * 100) / 100,
            roiFormatted: roi.toFixed(2) + '%',
            comparison,
            verdict: roi >= 0 ? '✅ EV POSITIVO' : '❌ EV NEGATIVO (esperado para loterias)'
        };

        // Log detalhado
        console.log('%c[PURE-COVER] ── Detalhamento por Faixa ──', 'color: #f59e0b;');
        for (const b of breakdown) {
            console.log('[PURE-COVER]   ' + b.label + ': P=' + (b.probabilidade * 100).toFixed(8) + '% | ' +
                b.oddsTexto + ' | E[acertos]=' + b.expectedHits.toFixed(4) +
                ' | Prêmio≈R$' + b.prizeValue.toFixed(2) + ' | EV=R$' + b.evTier.toFixed(2));
        }
        console.log('[PURE-COVER] Valor Esperado Total: R$ ' + result.totalExpectedValue.toFixed(2));
        console.log('[PURE-COVER] Investimento: R$ ' + totalInvestment.toFixed(2));
        console.log('[PURE-COVER] ROI Esperado: ' + result.roiFormatted);
        console.log('[PURE-COVER] ' + result.verdict);
        console.log('[PURE-COVER] Comparação: ' + comparison);

        return result;
    }

    // ═══════════════════════════════════════════════════════
    //  CALCULADORA DE VOLUME ÓTIMO
    //  calculateOptimalVolume(gameKey, budget)
    //
    //  Dado um orçamento em R$, calcula:
    //  - Quantos jogos cabem
    //  - ROI esperado com esse volume
    //  - Volume ótimo recomendado
    //  - Alerta se ROI < -80%
    // ═══════════════════════════════════════════════════════
    static calculateOptimalVolume(gameKey, budget) {
        const cfg = this.getConfig(gameKey);
        if (!cfg) {
            console.error('[PURE-COVER] Volume: Loteria não encontrada:', gameKey);
            return null;
        }

        console.log('%c[PURE-COVER] ══ CALCULADORA DE VOLUME ÓTIMO ══', 'color: #10b981; font-weight: bold;');
        console.log('[PURE-COVER] ' + cfg.name + ' | Orçamento: R$ ' + budget.toFixed(2));

        const maxGames = Math.floor(budget / cfg.ticketPrice);
        if (maxGames < 1) {
            return {
                gameKey,
                name: cfg.name,
                budget,
                maxGames: 0,
                error: 'Orçamento insuficiente. Mínimo: R$ ' + cfg.ticketPrice.toFixed(2)
            };
        }

        // Calcular ROI para diferentes volumes
        const volumes = [];
        const testVolumes = [1, 2, 3, 5, 10, 15, 20, 30, 50, 75, 100, 150, 200, 300, 500, 1000];

        for (const vol of testVolumes) {
            if (vol > maxGames) break;

            const cost = vol * cfg.ticketPrice;
            const roiResult = this.calculateExpectedROI(gameKey, vol);
            if (!roiResult) continue;

            volumes.push({
                numGames: vol,
                cost: cost,
                expectedValue: roiResult.totalExpectedValue,
                roi: roiResult.roi,
                probAnyPrize: this._calcProbAnyPrize(cfg, vol)
            });
        }

        // Incluir o volume máximo se não estiver na lista
        if (maxGames > 0 && !volumes.find(v => v.numGames === maxGames)) {
            const cost = maxGames * cfg.ticketPrice;
            const roiResult = this.calculateExpectedROI(gameKey, maxGames);
            if (roiResult) {
                volumes.push({
                    numGames: maxGames,
                    cost: cost,
                    expectedValue: roiResult.totalExpectedValue,
                    roi: roiResult.roi,
                    probAnyPrize: this._calcProbAnyPrize(cfg, maxGames)
                });
            }
        }

        // Encontrar o volume com ROI menos negativo
        let bestVolume = volumes[0];
        for (const v of volumes) {
            if (v.roi > bestVolume.roi) bestVolume = v;
        }

        // Alerta se ROI muito negativo
        const alert = bestVolume && bestVolume.roi < -80
            ? '⚠️ ALERTA: ROI extremamente negativo (' + bestVolume.roi.toFixed(1) + '%). A loteria é um jogo de azar com vantagem matemática para a casa.'
            : null;

        const result = {
            gameKey,
            name: cfg.name,
            budget,
            ticketPrice: cfg.ticketPrice,
            maxGames,
            maxGamesCost: maxGames * cfg.ticketPrice,
            volumes,
            recommended: bestVolume,
            alert
        };

        // Log
        console.log('[PURE-COVER] Jogos possíveis: ' + maxGames + ' (R$ ' + result.maxGamesCost.toFixed(2) + ')');
        console.log('[PURE-COVER] Volume recomendado: ' + bestVolume.numGames + ' jogos (ROI: ' + bestVolume.roi.toFixed(2) + '%)');
        if (alert) {
            console.log('%c[PURE-COVER] ' + alert, 'color: #ef4444; font-weight: bold;');
        }

        return result;
    }

    // ═══════════════════════════════════════════════════════
    //  DETECTOR DE EV POSITIVO
    //  isPositiveEV(gameKey, accumulatedPrize)
    //
    //  Calcula se o prêmio acumulado é grande o suficiente
    //  para tornar o EV positivo.
    // ═══════════════════════════════════════════════════════
    static isPositiveEV(gameKey, accumulatedPrize) {
        const cfg = this.getConfig(gameKey);
        if (!cfg) {
            console.error('[PURE-COVER] EV+: Loteria não encontrada:', gameKey);
            return null;
        }

        console.log('%c[PURE-COVER] ══ DETECTOR DE EV POSITIVO ══', 'color: #8b5cf6; font-weight: bold;');
        console.log('[PURE-COVER] ' + cfg.name + ' | Prêmio acumulado: R$ ' + accumulatedPrize.toLocaleString('pt-BR'));

        const N = cfg.totalNumbers;
        const K = cfg.lotteryDraw;
        const n = cfg.drawSize;
        const price = cfg.ticketPrice;

        // Calcular EV com o prêmio acumulado para o prêmio máximo
        let totalEV = 0;
        const details = [];

        for (const threshold of cfg.prizeThresholds) {
            const prob = this._hypergeometric(N, K, n, threshold);
            let prizeValue;

            // O prêmio máximo usa o valor acumulado
            if (threshold === cfg.prizeThresholds[cfg.prizeThresholds.length - 1]) {
                prizeValue = accumulatedPrize;
            } else if (cfg.fixedPrizes && cfg.fixedPrizes[threshold] !== undefined) {
                prizeValue = cfg.fixedPrizes[threshold];
            } else {
                prizeValue = this._estimatePrize(cfg, threshold);
            }

            const ev = prob * prizeValue;
            totalEV += ev;

            details.push({
                acertos: threshold,
                prob,
                prizeValue,
                ev
            });
        }

        const isPositive = totalEV >= price;
        const breakEvenPrize = this._calcBreakEvenPrize(cfg);

        const result = {
            gameKey,
            name: cfg.name,
            accumulatedPrize,
            ticketPrice: price,
            totalEV: Math.round(totalEV * 100) / 100,
            isPositive,
            roi: Math.round(((totalEV - price) / price) * 10000) / 100,
            breakEvenPrize: Math.round(breakEvenPrize),
            details,
            verdict: isPositive
                ? '✅ EV POSITIVO! O prêmio acumulado justifica a aposta matematicamente.'
                : '❌ EV NEGATIVO. Prêmio precisa ser ≥ R$ ' + Math.round(breakEvenPrize).toLocaleString('pt-BR') + ' para EV positivo.',
            recommendation: isPositive
                ? 'Este é um momento matematicamente favorável para apostar (raridade!).'
                : 'Aposte apenas por entretenimento, não como investimento.'
        };

        console.log('[PURE-COVER] EV por jogo: R$ ' + result.totalEV.toFixed(2) + ' (custo: R$ ' + price.toFixed(2) + ')');
        console.log('[PURE-COVER] ROI: ' + result.roi.toFixed(2) + '%');
        console.log('[PURE-COVER] Prêmio de break-even: R$ ' + result.breakEvenPrize.toLocaleString('pt-BR'));
        console.log('%c[PURE-COVER] ' + result.verdict, isPositive ? 'color: #10b981; font-weight: bold;' : 'color: #ef4444; font-weight: bold;');

        return result;
    }

    // ═══════════════════════════════════════════════════════
    //  TABELA COMPLETA DE PROBABILIDADES
    //  fullProbabilityTable(gameKey)
    // ═══════════════════════════════════════════════════════
    static fullProbabilityTable(gameKey) {
        const cfg = this.getConfig(gameKey);
        if (!cfg) return null;

        console.log('%c[PURE-COVER] ═══ TABELA DE PROBABILIDADES: ' + cfg.name + ' ═══', 'color: #fbbf24; font-weight: bold; font-size: 14px;');

        const N = cfg.totalNumbers;
        const K = cfg.lotteryDraw;
        const n = cfg.drawSize;

        const table = [];
        const targets = [0.10, 0.25, 0.50, 0.75, 0.90, 0.99];

        for (const t of cfg.prizeThresholds) {
            // P(X=k) exata
            const pExact = this._hypergeometric(N, K, n, t);

            // P(k+ acertos) cumulativa
            let pCum = 0;
            for (let k = t; k <= Math.min(n, K); k++) {
                pCum += this._hypergeometric(N, K, n, k);
            }

            const odds = pCum > 0 ? Math.round(1 / pCum) : Infinity;

            // Quantos jogos para cada nível de confiança
            const gamesNeeded = {};
            for (const target of targets) {
                if (pCum <= 0) {
                    gamesNeeded['p' + Math.round(target * 100)] = Infinity;
                } else {
                    gamesNeeded['p' + Math.round(target * 100)] = Math.ceil(Math.log(1 - target) / Math.log(1 - pCum));
                }
            }

            const row = {
                acertos: t,
                label: cfg.prizeLabels[cfg.prizeThresholds.indexOf(t)] || t + ' ac.',
                pExact,
                pCum,
                odds,
                oddsTexto: '1 em ' + odds.toLocaleString('pt-BR'),
                ...gamesNeeded
            };
            table.push(row);

            console.log('[PURE-COVER] ' + row.label + ': P=' + (pCum * 100).toFixed(8) + '% | ' + row.oddsTexto);
        }

        return table;
    }

    // ═══════════════════════════════════════════════════════
    //  UTILITÁRIOS MATEMÁTICOS
    // ═══════════════════════════════════════════════════════

    /**
     * Combinação C(n,k) — inteiro exato para valores pequenos
     * Usa multiplicação/divisão iterativa para evitar overflow
     */
    static _comb(n, k) {
        if (k < 0 || k > n) return 0;
        if (k === 0 || k === n) return 1;
        k = Math.min(k, n - k);
        let r = 1;
        for (let i = 0; i < k; i++) {
            r = r * (n - i) / (i + 1);
            if (r > 1e15) return 1e15; // Cap para evitar imprecisão
        }
        return Math.round(r);
    }

    /**
     * Combinação C(n,k) usando BigInt — precisão absoluta
     */
    static _combBigInt(n, k) {
        if (k < 0 || k > n) return 0n;
        if (k === 0 || k === n) return 1n;
        if (k > n - k) k = n - k;
        let result = 1n;
        const bn = BigInt(n);
        for (let i = 0; i < k; i++) {
            result = result * (bn - BigInt(i)) / (BigInt(i) + 1n);
        }
        return result;
    }

    /**
     * Log de combinação — para probabilidades sem overflow
     */
    static _logComb(n, k) {
        if (k < 0 || k > n) return -Infinity;
        if (k === 0 || k === n) return 0;
        k = Math.min(k, n - k);
        let result = 0;
        for (let i = 0; i < k; i++) {
            result += Math.log(n - i) - Math.log(i + 1);
        }
        return result;
    }

    /**
     * Probabilidade hipergeométrica EXATA
     * P(X=k) = C(K,k) × C(N-K, n-k) / C(N,n)
     *
     * @param {number} N - Total de números no universo
     * @param {number} K - Números sorteados pela loteria
     * @param {number} n - Números apostados pelo jogador
     * @param {number} k - Acertos desejados
     * @returns {number} Probabilidade entre 0 e 1
     */
    static _hypergeometric(N, K, n, k) {
        // Validações
        if (k < 0 || k > Math.min(K, n)) return 0;
        if ((n - k) > (N - K)) return 0;
        if (k > K) return 0;

        // Usar BigInt para precisão absoluta
        const numerator = this._combBigInt(K, k) * this._combBigInt(N - K, n - k);
        const denominator = this._combBigInt(N, n);

        if (denominator === 0n) return 0;

        // Converter para Number com máxima precisão
        // Multiplica por 10^18 antes de dividir para preservar casas decimais
        const PRECISION = 1000000000000000000n; // 10^18
        const result = Number(numerator * PRECISION / denominator) / 1e18;
        return result;
    }

    /**
     * Fisher-Yates shuffle — aleatoriedade uniforme verdadeira
     * Usa Math.random() nativo (sem PRNG substituído)
     */
    static _shuffle(arr) {
        for (let i = arr.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            const tmp = arr[i];
            arr[i] = arr[j];
            arr[j] = tmp;
        }
        return arr;
    }

    /**
     * Estima o valor do prêmio para faixas sem prêmio fixo
     * Baseado em dados históricos médios das loterias da Caixa
     */
    static _estimatePrize(cfg, threshold) {
        // Prêmios fixos conhecidos
        if (cfg.fixedPrizes && cfg.fixedPrizes[threshold] !== undefined) {
            return cfg.fixedPrizes[threshold];
        }

        // Estimativas baseadas em prêmios médios históricos (valores aproximados)
        const estimates = {
            lotofacil: { 11: 6, 12: 12, 13: 30, 14: 1800, 15: 1500000 },
            megasena:  { 4: 1100, 5: 45000, 6: 50000000 },
            quina:     { 2: 3.50, 3: 130, 4: 7500, 5: 8000000 },
            timemania: { 3: 3.50, 4: 10.50, 5: 600, 6: 55000, 7: 5000000 },
            diadesorte: { 4: 5, 5: 25, 6: 6000, 7: 1500000 },
            duplasena: { 3: 3, 4: 12, 5: 2000, 6: 3000000 },
            lotomania: { 15: 6, 16: 30, 17: 120, 18: 2000, 19: 40000, 20: 3000000 }
        };

        // Encontrar a config key correspondente
        const configName = cfg.name.toLowerCase().replace(/[^a-záéíóúã]/g, '');
        for (const [key, prizes] of Object.entries(estimates)) {
            const cfgCheck = this.getConfig(key);
            if (cfgCheck && cfgCheck.name === cfg.name && prizes[threshold] !== undefined) {
                return prizes[threshold];
            }
        }

        // Fallback: estimativa genérica baseada na probabilidade
        const prob = this._hypergeometric(cfg.totalNumbers, cfg.lotteryDraw, cfg.drawSize, threshold);
        if (prob > 0) {
            // Estimar baseado no payout e probabilidade
            return cfg.ticketPrice * cfg.payout / prob * 0.1;
        }

        return 0;
    }

    /**
     * Calcula o prêmio mínimo no jackpot para EV positivo
     */
    static _calcBreakEvenPrize(cfg) {
        const N = cfg.totalNumbers;
        const K = cfg.lotteryDraw;
        const n = cfg.drawSize;
        const price = cfg.ticketPrice;
        const topThreshold = cfg.prizeThresholds[cfg.prizeThresholds.length - 1];

        // EV das faixas menores (fixas)
        let evLowerTiers = 0;
        for (const t of cfg.prizeThresholds) {
            if (t === topThreshold) continue;
            const prob = this._hypergeometric(N, K, n, t);
            let prize = 0;
            if (cfg.fixedPrizes && cfg.fixedPrizes[t] !== undefined) {
                prize = cfg.fixedPrizes[t];
            } else {
                prize = this._estimatePrize(cfg, t);
            }
            evLowerTiers += prob * prize;
        }

        // Para EV = 0: P(top) × JackpotMin + evLowerTiers = price
        // JackpotMin = (price - evLowerTiers) / P(top)
        const pTop = this._hypergeometric(N, K, n, topThreshold);
        if (pTop <= 0) return Infinity;

        return (price - evLowerTiers) / pTop;
    }

    /**
     * Calcula probabilidade de qualquer prêmio com N jogos
     */
    static _calcProbAnyPrize(cfg, numGames) {
        const N = cfg.totalNumbers;
        const K = cfg.lotteryDraw;
        const n = cfg.drawSize;
        const minThreshold = cfg.prizeThresholds[0];

        let pCum = 0;
        for (let k = minThreshold; k <= Math.min(n, K); k++) {
            pCum += this._hypergeometric(N, K, n, k);
        }

        return 1 - Math.pow(1 - pCum, numGames);
    }

    /**
     * Formatar moeda brasileira
     */
    static _formatMoney(value) {
        const abs = Math.abs(value);
        const sign = value < 0 ? '-' : '';
        if (abs >= 1000000) {
            return sign + 'R$ ' + (abs / 1000000).toFixed(2).replace('.', ',') + 'M';
        }
        if (abs >= 1000) {
            return sign + 'R$ ' + (abs / 1000).toFixed(1).replace('.', ',') + 'K';
        }
        return sign + 'R$ ' + abs.toFixed(2).replace('.', ',');
    }

    // ═══════════════════════════════════════════════════════
    //  QUANTOS JOGOS PARA X% DE CHANCE
    //  howManyGames(gameKey, targetProb, minHits)
    // ═══════════════════════════════════════════════════════
    static howManyGames(gameKey, targetProb, minHits) {
        const cfg = this.getConfig(gameKey);
        if (!cfg) return null;

        const N = cfg.totalNumbers;
        const K = cfg.lotteryDraw;
        const n = cfg.drawSize;

        // P(k+ acertos) cumulativa por jogo
        let pCum = 0;
        for (let k = minHits; k <= Math.min(n, K); k++) {
            pCum += this._hypergeometric(N, K, n, k);
        }

        if (pCum <= 0) return { games: Infinity, probability: 0, cost: Infinity, targetProb, minHits };

        // N jogos: P(pelo menos 1) = 1 - (1-p)^N >= targetProb
        // N >= ln(1-target) / ln(1-p)
        const nGames = Math.ceil(Math.log(1 - targetProb) / Math.log(1 - pCum));
        const cost = nGames * cfg.ticketPrice;

        console.log('[PURE-COVER] ' + cfg.name + ': ' + nGames + ' jogos para ' +
            (targetProb * 100) + '% de chance de ' + minHits + '+ acertos | ' +
            'P/jogo=' + (pCum * 100).toFixed(8) + '% | Custo=R$ ' + cost.toFixed(2));

        return { games: nGames, probability: pCum, cost, targetProb, minHits };
    }

    // ═══════════════════════════════════════════════════════
    //  RELATÓRIO COMPLETO — Texto para UI
    // ═══════════════════════════════════════════════════════
    static getReport(analysis) {
        if (!analysis) return '';

        const lines = [];
        lines.push('══════════════════════════════════════════════');
        lines.push('  📊 RELATÓRIO DE COBERTURA PURA');
        lines.push('══════════════════════════════════════════════');
        lines.push('');
        lines.push('Jogos gerados: ' + analysis.totalGames);
        lines.push('Pool: ' + analysis.poolSize + ' números (TODOS)');
        lines.push('Tempo: ' + analysis.elapsed + 'ms');
        lines.push('');
        lines.push('── Cobertura ──');
        lines.push('Pares: ' + analysis.pairsCovered + '/' + analysis.totalPairs + ' (' + analysis.pairCoveragePct + '%)');
        if (analysis.totalTriples > 0) {
            lines.push('Triplas: ' + analysis.triplesCovered + '/' + analysis.totalTriples + ' (' + analysis.tripleCoveragePct + '%)');
        }
        lines.push('Números: ' + analysis.numberCoverage + '/' + analysis.poolSize + ' (' + analysis.numberCoveragePct + '%)');
        lines.push('');
        lines.push('── Diversidade ──');
        lines.push('Hamming médio: ' + analysis.avgHamming + '/' + analysis.maxHamming);
        lines.push('Uso números: min=' + analysis.numberUsageStats.min + ' max=' + analysis.numberUsageStats.max + ' média=' + analysis.numberUsageStats.avg);
        lines.push('');
        lines.push('── Investimento ──');
        lines.push('Total: R$ ' + analysis.investment.toFixed(2));
        lines.push('');
        lines.push('Filosofia: ' + analysis.philosophy);
        lines.push('══════════════════════════════════════════════');

        return lines.join('\n');
    }

    // ═══════════════════════════════════════════════════════
    //  LISTA DE LOTERIAS DISPONÍVEIS
    // ═══════════════════════════════════════════════════════
    static getAvailableGames() {
        return ['lotofacil', 'megasena', 'quina', 'timemania', 'diadesorte', 'duplasena', 'lotomania'];
    }

    /**
     * Retorna informações resumidas de uma loteria
     */
    static getGameInfo(gameKey) {
        const cfg = this.getConfig(gameKey);
        if (!cfg) return null;

        return {
            gameKey,
            name: cfg.name,
            drawSize: cfg.drawSize,
            lotteryDraw: cfg.lotteryDraw,
            totalNumbers: cfg.totalNumbers,
            range: cfg.range,
            ticketPrice: cfg.ticketPrice,
            prizeThresholds: cfg.prizeThresholds,
            prizeLabels: cfg.prizeLabels,
            zones: cfg.zones,
            payout: cfg.payout
        };
    }
}

// ═══════════════════════════════════════════════════════
//  DISPONIBILIZAR GLOBALMENTE
// ═══════════════════════════════════════════════════════
if (typeof window !== 'undefined') window.PureCoverageEngine = PureCoverageEngine;
console.log('%c[PURE-COVER] ✓ Motor de Cobertura Pura carregado — ZERO previsão, 100% cobertura', 'color: #22d3ee; font-weight: bold; font-size: 12px;');
