/**
 * ╔══════════════════════════════════════════════════════════════════════════╗
 * ║  ENSEMBLE ENGINE v1.0 — Sistema de Consenso Multi-Motor               ║
 * ║                                                                        ║
 * ║  PRINCÍPIO: Múltiplos engines pontuam cada número independentemente.   ║
 * ║  O consenso é mais robusto que qualquer engine individual.             ║
 * ║  Os pesos são calibrados por backtest contra sorteios REAIS.           ║
 * ║                                                                        ║
 * ║  ENGINES CONSULTADOS:                                                  ║
 * ║   1. NovaEraEngine   — 18 camadas de análise (freq, Markov, etc.)     ║
 * ║   2. QuantumGodEngine — Monte Carlo (28 camadas, temperature decay)   ║
 * ║   3. StatisticalBias  — Z-scores, Chi², p-valor formal               ║
 * ║   4. PrecisionCalibrator — Tendências últimos 3 + probabilidade cond. ║
 * ║                                                                        ║
 * ║  FASES:                                                                ║
 * ║   1. Consulta → cada engine retorna scores por número                 ║
 * ║   2. Normalização → scores em [0, 1] com min-max                     ║
 * ║   3. Calibração → pesos via backtest contra últimos 30 sorteios       ║
 * ║   4. Consenso → combinação ponderada + bônus de agreement            ║
 * ║   5. Filtro Adaptativo → estratégia muda por volume de jogos          ║
 * ║   6. Geração → delega para CoverageEngine com scores combinados      ║
 * ║   7. Validação Cruzada → descarta jogos com score fraco no consenso   ║
 * ╚══════════════════════════════════════════════════════════════════════════╝
 */
class EnsembleEngine {

    // Cache de calibração (recalcula só quando histórico muda)
    static _calibrationCache = {};
    static _calibrationHistoryLength = {};

    // ═══════════════════════════════════════════════════════════
    //  PONTO DE ENTRADA PRINCIPAL
    //  Substitui SmartCoverageEngine.generate() como orquestrador
    // ═══════════════════════════════════════════════════════════
    static generate(gameKey, numGames, selectedNumbers, fixedNumbers, drawSize, options) {
        const t0 = Date.now();
        const opts = options || {};
        console.log('%c[ENSEMBLE] ══════════════════════════════════════════', 'color: #06B6D4; font-weight: bold;');
        console.log('%c[ENSEMBLE] v1.0 — Sistema de Consenso Multi-Motor', 'color: #06B6D4; font-weight: bold;');
        console.log('[ENSEMBLE] Loteria: ' + gameKey + ' | Jogos: ' + numGames + ' | Draw: ' + drawSize);

        // 1. Obter histórico
        const history = this._getHistory(gameKey);
        if (history.length < 10) {
            console.warn('[ENSEMBLE] Histórico insuficiente (' + history.length + '). Fallback para SmartCoverageEngine.');
            return this._fallback(gameKey, numGames, selectedNumbers, fixedNumbers, drawSize, opts);
        }

        // 2. Se o usuário selecionou números, usa-os como pool (sem scoring ensemble)
        if (selectedNumbers && selectedNumbers.length > 0) {
            console.log('[ENSEMBLE] Pool do usuário: ' + selectedNumbers.length + ' números. Delegando para SmartCoverageEngine.');
            return this._fallback(gameKey, numGames, selectedNumbers, fixedNumbers, drawSize, opts);
        }

        // 3. Scoring multi-engine + consenso
        const ensemble = this.score(gameKey, numGames, history, drawSize);

        // 4. Construir pool adaptativo por volume
        const pool = this._buildAdaptivePool(ensemble, numGames, drawSize, gameKey);

        // 5. Construir layeredPool para CoverageEngine
        const layeredPool = this._buildLayeredPool(ensemble, pool, gameKey, drawSize);

        // 6. Delegar geração para CoverageEngine
        // v14.0: DAMPENING ADAPTATIVO DE SCORES POR VOLUME
        // Problema: scores brutos (amplitude 0.1–2.0) usados como pesos de roleta
        //   → números top recebem 20x mais presença → CV 54% em 10.000 jogos
        // Solução: amortecimento exponencial proporcional ao volume
        //   → preserva leve preferência histórica sem concentração severa
        const dampedScores = this._dampScoresByVolume(ensemble.scores, numGames, ensemble.startNum, ensemble.endNum);
        const coverageOpts = {
            precisionMode: pool.length < ensemble.totalRange,
            precisionPool: pool.length < ensemble.totalRange ? pool : null,
            layeredPool: layeredPool,
            quantumScores: dampedScores
        };

        let result;
        if (typeof CoverageEngine !== 'undefined') {
            try {
                result = CoverageEngine.generate(
                    gameKey, numGames, pool,
                    fixedNumbers || [], drawSize, coverageOpts
                );
            } catch (e) {
                console.error('[ENSEMBLE] CoverageEngine falhou:', e.message);
                return this._fallback(gameKey, numGames, selectedNumbers, fixedNumbers, drawSize, opts);
            }
        } else {
            return this._fallback(gameKey, numGames, selectedNumbers, fixedNumbers, drawSize, opts);
        }

        if (!result || !result.games || result.games.length === 0) {
            console.warn('[ENSEMBLE] CoverageEngine retornou vazio. Fallback.');
            return this._fallback(gameKey, numGames, selectedNumbers, fixedNumbers, drawSize, opts);
        }

        // 7. Validação cruzada — descartar jogos fracos e substituir
        result.games = this._crossValidate(result.games, ensemble, drawSize, numGames);

        // 8. Montar relatório
        result.analysis = result.analysis || {};
        result.analysis.ensemble = {
            version: '1.0',
            enginesUsed: ensemble.enginesUsed,
            weights: ensemble.weights,
            calibration: ensemble.calibration,
            strategy: pool._strategy,
            poolSize: pool.length,
            consensusTop10: this._getConsensusTop(ensemble, 10),
            elapsed: (Date.now() - t0) + 'ms'
        };
        result.analysis.strategy = 'ENSEMBLE';
        result.analysis.engineVersion = 'EnsembleEngine-v1.0';
        result.analysis.elapsed = (Date.now() - t0) + 'ms';

        console.log('%c[ENSEMBLE] ✓ Geração completa: ' + result.games.length + ' jogos em ' + result.analysis.elapsed, 'color: #06B6D4; font-weight: bold;');
        return result;
    }

    // ═══════════════════════════════════════════════════════════
    //  FASE 0-4: QUANTIDADE → SCORING → NORMALIZAÇÃO → CALIBRAÇÃO → CONSENSO
    //
    //  O numGames é o PRIMEIRO fator. Ele determina:
    //   - Quais engines pesam mais (precision vs cobertura)
    //   - Limiar de consenso (rigoroso vs flexível)
    //   - Intensidade do bônus de consenso
    //   - Quantos parceiros cada número precisa ter
    // ═══════════════════════════════════════════════════════════
    static score(gameKey, numGames, history, drawSize) {
        const profile = this._getProfile(gameKey);
        const startNum = profile.range[0];
        const endNum = profile.range[1];
        const totalRange = endNum - startNum + 1;

        // ══ FASE 0: PERFIL DE VOLUME ══
        // O volume solicitado determina o DNA de toda a análise
        const volumeProfile = this._getVolumeProfile(numGames, drawSize, totalRange);
        console.log('[ENSEMBLE] 📐 Perfil de volume: ' + volumeProfile.name +
            ' | Foco: ' + volumeProfile.focus +
            ' | Consenso mín: ' + volumeProfile.minConsensus + '/' + '4');

        // ── FASE 1: Consultar cada engine ──
        const rawScores = {};
        const enginesUsed = [];

        // Engine 1: NovaEraEngine (18+ camadas — forte em análise individual)
        if (typeof NovaEraEngine !== 'undefined') {
            try {
                const neProfile = NovaEraEngine.getProfile(gameKey);
                NovaEraEngine._currentDrawSize = drawSize;
                // Volume alto → ativar sniperMode para floor de diversidade
                NovaEraEngine._sniperMode = numGames > 100;
                let scores;
                try {
                    scores = NovaEraEngine._scoreAllNumbers(gameKey, neProfile, history, startNum, endNum, totalRange);
                } finally {
                    NovaEraEngine._sniperMode = false;
                }
                if (scores && Object.keys(scores).length > 0) {
                    rawScores.novaEra = scores;
                    enginesUsed.push('NovaEra');
                }
            } catch (e) {
                console.warn('[ENSEMBLE] ✗ NovaEra falhou:', e.message);
            }
        }

        // Engine 2: QuantumGodEngine (Monte Carlo — forte em padrões ocultos)
        if (typeof QuantumGodEngine !== 'undefined') {
            try {
                const weightProfile = QuantumGodEngine.getWeightProfile(gameKey);
                if (weightProfile) {
                    const qScores = this._extractQuantumScores(gameKey, history, weightProfile, startNum, endNum, drawSize);
                    if (qScores && Object.keys(qScores).length > 0) {
                        rawScores.quantum = qScores;
                        enginesUsed.push('Quantum');
                    }
                }
            } catch (e) {
                console.warn('[ENSEMBLE] ✗ Quantum falhou:', e.message);
            }
        }

        // Engine 3: StatisticalBiasEngine (z-scores — forte em cobertura equilibrada)
        if (typeof StatisticalBiasEngine !== 'undefined' && history.length >= 20) {
            try {
                const biasResult = StatisticalBiasEngine.analyze(gameKey, history, totalRange);
                if (biasResult && biasResult.numberScores) {
                    const biasScores = {};
                    for (let n = startNum; n <= endNum; n++) {
                        const s = biasResult.numberScores[n];
                        biasScores[n] = s ? s.evidenceScore : 0;
                    }
                    rawScores.bias = biasScores;
                    rawScores._biasVerdict = biasResult.verdict;
                    enginesUsed.push('StatisticalBias');
                }
            } catch (e) {
                console.warn('[ENSEMBLE] ✗ StatisticalBias falhou:', e.message);
            }
        }

        // Engine 4: PrecisionCalibrator (tendências curtas — forte em poucos jogos)
        if (typeof PrecisionCalibrator !== 'undefined' && history.length >= 4) {
            try {
                const last3Scores = PrecisionCalibrator.analyzeLast3Trends(gameKey, history, startNum, endNum);
                const condScores = PrecisionCalibrator.buildConditionalProbMatrix(gameKey, history, startNum, endNum, drawSize);
                const precisionScores = {};
                for (let n = startNum; n <= endNum; n++) {
                    precisionScores[n] = ((last3Scores[n] || 0.5) * 0.55) + ((condScores[n] || 0.5) * 0.45);
                }
                rawScores.precision = precisionScores;
                enginesUsed.push('Precision');
            } catch (e) {
                console.warn('[ENSEMBLE] ✗ Precision falhou:', e.message);
            }
        }

        if (enginesUsed.length === 0) {
            console.error('[ENSEMBLE] Nenhum engine disponível!');
            return { scores: {}, weights: {}, enginesUsed: [], totalRange };
        }

        console.log('[ENSEMBLE] Engines ativos: ' + enginesUsed.join(' + '));

        // ── FASE 2: Normalizar cada engine para [0, 1] ──
        const normalized = {};
        for (const engine of Object.keys(rawScores)) {
            if (engine.startsWith('_')) continue;
            normalized[engine] = this._normalizeMinMax(rawScores[engine], startNum, endNum);
        }

        // ── FASE 3: Pesos calibrados por loteria (backtest real) + ajuste por volume ──
        // FONTE PRIMÁRIA: pesos medidos empiricamente por loteria via grid search
        const lotteryWeights = this._getCalibratedWeightsByLottery(gameKey);
        // FONTE SECUNDÁRIA: backtest leave-one-out (valida se há dados suficientes)
        const calibration = this._calibrate(gameKey, history, startNum, endNum, totalRange, drawSize, enginesUsed, lotteryWeights);
        // Volume MODULA os pesos base:

        const weights = this._adjustWeightsByVolume(calibration.weights, volumeProfile, enginesUsed);

        // ── FASE 4: Combinar com consenso ADAPTATIVO ao volume ──
        const combinedScores = {};
        const agreement = {};
        const partnerStrength = {}; // Novo: força dos parceiros para cada número
        const engineNames = Object.keys(normalized);

        // 4a. Calcular pares fortes (co-ocorrência) — moldado pelo volume
        const pairMap = this._buildPairMap(history, startNum, endNum, volumeProfile);

        for (let n = startNum; n <= endNum; n++) {
            let weightedSum = 0;
            let weightSum = 0;
            let topHalfCount = 0;
            const nScores = [];

            for (const engine of engineNames) {
                const s = normalized[engine][n];
                if (s === undefined) continue;
                const w = weights[engine] || (1 / engineNames.length);
                weightedSum += s * w;
                weightSum += w;
                nScores.push(s);
                if (s >= 0.5) topHalfCount++;
            }

            const baseScore = weightSum > 0 ? weightedSum / weightSum : 0.5;

            // Bônus de consenso — INTENSIDADE depende do volume
            let consensusMultiplier = 1.0;
            if (topHalfCount >= engineNames.length) {
                // Unanimidade: poucos jogos = bônus forte, muitos jogos = bônus leve
                consensusMultiplier = 1.0 + volumeProfile.consensusBonus;
            } else if (topHalfCount >= engineNames.length - 1 && engineNames.length >= 3) {
                consensusMultiplier = 1.0 + (volumeProfile.consensusBonus * 0.5);
            } else if (topHalfCount <= 1 && engineNames.length >= 3) {
                // Maioria discorda → penalizar mais em poucos jogos
                consensusMultiplier = 1.0 - (volumeProfile.disagreementPenalty);
            }

            // Penalidade por variância (discordância)
            if (nScores.length >= 2) {
                const mean = nScores.reduce((a, b) => a + b, 0) / nScores.length;
                const variance = nScores.reduce((a, b) => a + (b - mean) * (b - mean), 0) / nScores.length;
                const stdDev = Math.sqrt(variance);
                if (stdDev > 0.35) {
                    consensusMultiplier *= (1.0 - volumeProfile.disagreementPenalty);
                }
            }

            // Bônus de parceiros fortes (co-ocorrência)
            const partnerScore = pairMap[n] || 0;
            const partnerBonus = partnerScore * volumeProfile.partnerWeight;

            combinedScores[n] = (baseScore * consensusMultiplier) + partnerBonus;
            agreement[n] = topHalfCount;
            partnerStrength[n] = partnerScore;
        }

        console.log('[ENSEMBLE] Pesos finais (backtest + volume): ' +
            engineNames.map(e => e + '=' + (weights[e] * 100).toFixed(0) + '%').join(', '));

        return {
            scores: combinedScores,
            agreement: agreement,
            partnerStrength: partnerStrength,
            rawScores: rawScores,
            normalized: normalized,
            weights: weights,
            calibration: calibration,
            volumeProfile: volumeProfile,
            enginesUsed: enginesUsed,
            startNum: startNum,
            endNum: endNum,
            totalRange: totalRange,
            biasVerdict: rawScores._biasVerdict || null
        };
    }

    // ═══════════════════════════════════════════════════════════
    //  PERFIL DE VOLUME — o DNA da geração baseado em numGames
    //
    //  NOTA DE HONESTIDADE: O consensusBonus e disagreementPenalty
    //  ainda são estimativas razoáveis mas NÃO foram medidos no
    //  backtest (só afetam a geração, não o scoring individual).
    //  Os engineBias SÃO derivados dos lifts medidos empiricamente.
    // ═══════════════════════════════════════════════════════════
    static _getVolumeProfile(numGames, drawSize, totalRange) {
        // Lotofácil especial: 15/25 sorteados → cobertura total sempre
        // Backtest confirmou: TODOS os scorers = lift 1.000 (sem discriminação)
        const isFullCoverage = (drawSize / totalRange) > 0.50;

        if (isFullCoverage) {
            return {
                name: 'COBERTURA_TOTAL',
                focus: 'Loteria de alta cobertura — scoring não discrimina',
                engineBias: { novaEra: 0.5, quantum: 0.5, bias: 1.0, precision: 0.5 },
                minConsensus: 0,
                consensusBonus: 0.0,
                disagreementPenalty: 0.0,
                partnerWeight: 0.0,
                pairWindow: 10
            };
        }

        if (numGames <= 10) {
            return {
                name: 'CIRURGICO',
                focus: 'Precisão individual máxima — cada jogo conta',
                // Backtest: Zona e Atraso têm melhor lift individual na maioria das loterias
                // Frequência mostrou lifts negativos em Timemania e Dia de Sorte
                engineBias: { novaEra: 1.1, quantum: 1.0, bias: 1.2, precision: 1.0 },
                minConsensus: 3,
                consensusBonus: 0.20,
                disagreementPenalty: 0.20,
                partnerWeight: 0.08,
                pairWindow: 15
            };
        }
        if (numGames <= 50) {
            return {
                name: 'FOCADO',
                focus: 'Consenso + diversidade controlada',
                engineBias: { novaEra: 1.0, quantum: 1.0, bias: 1.1, precision: 1.0 },
                minConsensus: 2,
                consensusBonus: 0.12,
                disagreementPenalty: 0.12,
                partnerWeight: 0.05,
                pairWindow: 20
            };
        }
        if (numGames <= 200) {
            return {
                name: 'EQUILIBRADO',
                focus: 'Cobertura inteligente com scoring',
                // Backtest: StatisticalBias (zona) consistente em todas as loterias
                engineBias: { novaEra: 0.9, quantum: 0.9, bias: 1.2, precision: 0.9 },
                minConsensus: 1,
                consensusBonus: 0.07,
                disagreementPenalty: 0.07,
                partnerWeight: 0.03,
                pairWindow: 25
            };
        }
        if (numGames <= 1000) {
            return {
                name: 'COBERTURA',
                focus: 'Maximizar pares/triplas distintas',
                engineBias: { novaEra: 0.8, quantum: 0.8, bias: 1.3, precision: 0.7 },
                minConsensus: 0,
                consensusBonus: 0.04,
                disagreementPenalty: 0.04,
                partnerWeight: 0.01,
                pairWindow: 30
            };
        }
        return {
            name: 'MAXIMO',
            focus: 'Cobertura combinatória total',
            engineBias: { novaEra: 0.7, quantum: 0.7, bias: 1.4, precision: 0.6 },
            minConsensus: 0,
            consensusBonus: 0.02,
            disagreementPenalty: 0.02,
            partnerWeight: 0.0,
            pairWindow: 30
        };
    }

    // ═══════════════════════════════════════════════════════════
    //  PESOS CALIBRADOS EMPIRICAMENTE POR LOTERIA
    //
    //  Origem: backtest_calibration.js rodado contra REAL_HISTORY_DB
    //  Método: grid search de 625 combinações, 20 sorteios de teste
    //  Métrica: lift = acertos_reais / acertos_esperados_aleatório
    //
    //  TRANSPARÊNCIA:
    //   - Mega Sena: freq+delay dominam, pares prejudicam
    //   - Lotofácil: nenhum scorer discrimina (cobertura 60%)
    //   - Quina: freq+zona funcionam, pares PREJUDICAM (-20%)
    //   - Timemania: zona+atraso funcionam, freq PREJUDICA (-29%)
    //   - Dia de Sorte: zona domina, freq PREJUDICA (-26%)
    //  Loterias sem dados (duplasena, lotomania): pesos iguais
    // ═══════════════════════════════════════════════════════════
    static _getCalibratedWeightsByLottery(gameKey) {
        const calibrated = {
            // freq=50% delay=33% pares=0% zona=17% → lift=1.28
            megasena:   { novaEra: 0.42, quantum: 0.25, bias: 0.17, precision: 0.16 },
            // TODOS lift=1.0 → pesos iguais, foco em cobertura
            lotofacil:  { novaEra: 0.25, quantum: 0.25, bias: 0.25, precision: 0.25 },
            // freq=50% zona=50% delay=0% pares=0% → lift=1.33
            quina:      { novaEra: 0.35, quantum: 0.15, bias: 0.35, precision: 0.15 },
            // freq=30% delay=30% zona=40% pares=0% → lift=1.36
            timemania:  { novaEra: 0.20, quantum: 0.15, bias: 0.40, precision: 0.25 },
            // delay=25% zona=75% freq=0% → lift=1.08
            diadesorte: { novaEra: 0.15, quantum: 0.10, bias: 0.55, precision: 0.20 },
            // Sem dados suficientes no backtest → pesos iguais
            duplasena:  { novaEra: 0.25, quantum: 0.25, bias: 0.25, precision: 0.25 },
            lotomania:  { novaEra: 0.25, quantum: 0.25, bias: 0.25, precision: 0.25 }
        };
        return calibrated[gameKey] || { novaEra: 0.25, quantum: 0.25, bias: 0.25, precision: 0.25 };
    }

    // ═══════════════════════════════════════════════════════════
    //  AJUSTAR PESOS DO BACKTEST PELO PERFIL DE VOLUME
    //  backtest dá a base, volume modula
    // ═══════════════════════════════════════════════════════════
    static _adjustWeightsByVolume(backtestWeights, volumeProfile, enginesUsed) {
        const adjusted = {};
        let total = 0;

        for (const engineName of enginesUsed) {
            const key = this._engineToKey(engineName);
            const base = backtestWeights[key] || 0.25;
            const bias = volumeProfile.engineBias[key] || 1.0;
            adjusted[key] = base * bias;
            total += adjusted[key];
        }

        // Renormalizar
        for (const key of Object.keys(adjusted)) {
            adjusted[key] = total > 0 ? adjusted[key] / total : 1 / Object.keys(adjusted).length;
        }

        return adjusted;
    }

    // ═══════════════════════════════════════════════════════════
    //  MAPA DE PARCEIROS (CO-OCORRÊNCIA)
    //  Números que saem juntos frequentemente ganham bônus
    //  A janela de análise depende do volume
    // ═══════════════════════════════════════════════════════════
    static _buildPairMap(history, startNum, endNum, volumeProfile) {
        const pairFreq = {};
        const limit = Math.min(volumeProfile.pairWindow, history.length);

        for (let i = 0; i < limit; i++) {
            const nums = (history[i].numbers || []).filter(x => x >= startNum && x <= endNum);
            const decay = 1 / (1 + i * 0.1); // Sorteios recentes pesam mais
            for (let a = 0; a < nums.length; a++) {
                for (let b = a + 1; b < nums.length; b++) {
                    const key = Math.min(nums[a], nums[b]) + '-' + Math.max(nums[a], nums[b]);
                    pairFreq[key] = (pairFreq[key] || 0) + decay;
                }
            }
        }

        // Converter para score por número
        const partnerScore = {};
        for (let n = startNum; n <= endNum; n++) partnerScore[n] = 0;

        for (const key of Object.keys(pairFreq)) {
            if (pairFreq[key] >= 2) { // Par apareceu pelo menos 2x
                const [a, b] = key.split('-').map(Number);
                partnerScore[a] += pairFreq[key] * 0.01;
                partnerScore[b] += pairFreq[key] * 0.01;
            }
        }

        return partnerScore;
    }

    // ═══════════════════════════════════════════════════════════
    //  EXTRAÇÃO DE SCORES DO QUANTUMGODENGINE
    //  (O QuantumGod não tem método direto de scoring —
    //   extraímos via suas camadas internas)
    // ═══════════════════════════════════════════════════════════
    static _extractQuantumScores(gameKey, history, weightProfile, startNum, endNum, drawSize) {
        const scores = {};
        const N = history.length;
        if (N < 5) return scores;

        // Inicializar
        for (let n = startNum; n <= endNum; n++) scores[n] = 0;

        // Camada 1: Frequência Recente (últimos 5)
        const recentLimit = Math.min(5, N);
        for (let i = 0; i < recentLimit; i++) {
            const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            const decay = 1 / (i + 1);
            for (const n of nums) {
                if (n >= startNum && n <= endNum) scores[n] += decay * (weightProfile.recentFreq || 0.1);
            }
        }

        // Camada 2: Frequência Geral
        const genLimit = Math.min(100, N);
        for (let i = 0; i < genLimit; i++) {
            const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            for (const n of nums) {
                if (n >= startNum && n <= endNum) scores[n] += (1 / genLimit) * (weightProfile.generalFreq || 0.05);
            }
        }

        // Camada 3: Atraso (números "devendo")
        const lastSeen = {};
        for (let n = startNum; n <= endNum; n++) lastSeen[n] = N; // default: nunca visto
        for (let i = 0; i < Math.min(50, N); i++) {
            const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            for (const n of nums) {
                if (n >= startNum && n <= endNum && lastSeen[n] === N) lastSeen[n] = i;
            }
        }
        const totalRange = endNum - startNum + 1;
        const expectedGap = totalRange / drawSize;
        for (let n = startNum; n <= endNum; n++) {
            const gap = lastSeen[n];
            if (gap > expectedGap) {
                scores[n] += Math.min(1, (gap - expectedGap) / (expectedGap * 3)) * (weightProfile.latency || 0.05);
            }
        }

        // Camada 5: Repetição do último sorteio
        if (N >= 1) {
            const lastDraw = new Set((history[0].numbers || []).concat(history[0].numbers2 || []));
            for (const n of lastDraw) {
                if (n >= startNum && n <= endNum) {
                    scores[n] += (weightProfile.repetition || 0.10);
                }
            }
        }

        // Camada 6: Pares (co-ocorrência)
        const pairFreq = {};
        const pairLimit = Math.min(30, N);
        for (let i = 0; i < pairLimit; i++) {
            const nums = (history[i].numbers || []).filter(x => x >= startNum && x <= endNum);
            for (let a = 0; a < nums.length; a++) {
                for (let b = a + 1; b < nums.length; b++) {
                    const key = Math.min(nums[a], nums[b]) + '-' + Math.max(nums[a], nums[b]);
                    pairFreq[key] = (pairFreq[key] || 0) + 1;
                }
            }
        }
        // Boost números com pares fortes
        for (const key of Object.keys(pairFreq)) {
            if (pairFreq[key] >= 3) {
                const [a, b] = key.split('-').map(Number);
                scores[a] += pairFreq[key] * 0.02 * (weightProfile.pairs || 0.08);
                scores[b] += pairFreq[key] * 0.02 * (weightProfile.pairs || 0.08);
            }
        }

        // Camada 15: Markov (transições)
        if (N >= 3) {
            const transitions = {};
            for (let i = 0; i < Math.min(30, N - 1); i++) {
                const current = new Set((history[i].numbers || []).filter(x => x >= startNum && x <= endNum));
                const next = (history[i + 1].numbers || []).filter(x => x >= startNum && x <= endNum);
                for (const from of next) {
                    for (const to of current) {
                        if (!transitions[from]) transitions[from] = {};
                        transitions[from][to] = (transitions[from][to] || 0) + 1;
                    }
                }
            }
            // Aplicar transições do último sorteio
            const lastNums = (history[0].numbers || []).filter(x => x >= startNum && x <= endNum);
            for (const from of lastNums) {
                if (transitions[from]) {
                    for (const to of Object.keys(transitions[from])) {
                        const n = parseInt(to);
                        if (n >= startNum && n <= endNum) {
                            scores[n] += transitions[from][n] * 0.01 * (weightProfile.markov || 0.08);
                        }
                    }
                }
            }
        }

        return scores;
    }

    // ═══════════════════════════════════════════════════════════
    //  NORMALIZAÇÃO MIN-MAX → [0, 1]
    // ═══════════════════════════════════════════════════════════
    static _normalizeMinMax(scores, startNum, endNum) {
        let min = Infinity, max = -Infinity;
        for (let n = startNum; n <= endNum; n++) {
            const s = scores[n] || 0;
            if (s < min) min = s;
            if (s > max) max = s;
        }
        const range = max - min;
        const result = {};
        for (let n = startNum; n <= endNum; n++) {
            result[n] = range > 0 ? ((scores[n] || 0) - min) / range : 0.5;
        }
        return result;
    }

    // ═══════════════════════════════════════════════════════════
    //  CALIBRAÇÃO POR BACKTEST
    //  Testa cada engine contra os últimos W sorteios reais
    //  e calcula lift ratio (desempenho vs acaso)
    // ═══════════════════════════════════════════════════════════
    static _calibrate(gameKey, history, startNum, endNum, totalRange, drawSize, enginesUsed, lotteryWeights) {
        // Usar cache se histórico não mudou
        if (this._calibrationCache[gameKey] && this._calibrationHistoryLength[gameKey] === history.length) {
            return this._calibrationCache[gameKey];
        }

        const W = Math.min(20, Math.floor(history.length / 3));

        // Se não há dados suficientes para backtest leave-one-out,
        // usar os pesos medidos empiricamente (grid search offline)
        if (W < 5) {
            const weights = {};
            if (lotteryWeights) {
                for (const e of enginesUsed) {
                    const key = this._engineToKey(e);
                    weights[key] = lotteryWeights[key] || (1 / enginesUsed.length);
                }
                // Renormalizar para os engines disponíveis
                let total = Object.values(weights).reduce((s, v) => s + v, 0);
                for (const k of Object.keys(weights)) weights[k] = total > 0 ? weights[k] / total : 1 / enginesUsed.length;
            } else {
                const eq = 1 / enginesUsed.length;
                for (const e of enginesUsed) weights[this._engineToKey(e)] = eq;
            }
            return { weights, lifts: {}, backtestWindow: 0, reason: 'Pesos por loteria (backtest offline)' };
        }

        const K = Math.min(drawSize * 3, totalRange); // Top K números para avaliar
        const lifts = {};

        for (const engineName of enginesUsed) {
            const key = this._engineToKey(engineName);
            let totalHits = 0;
            let totalExpected = 0;
            let validTests = 0;

            for (let w = 0; w < W; w++) {
                // Histórico SEM o sorteio w (leave-one-out)
                const testHistory = history.slice(w + 1);
                if (testHistory.length < 5) continue;

                // Obter scores deste engine
                const engineScores = this._getEngineScores(key, gameKey, testHistory, startNum, endNum, totalRange, drawSize);
                if (!engineScores || Object.keys(engineScores).length === 0) continue;

                // Top K números
                const ranked = [];
                for (let n = startNum; n <= endNum; n++) {
                    ranked.push({ num: n, score: engineScores[n] || 0 });
                }
                ranked.sort((a, b) => b.score - a.score);
                const topK = new Set(ranked.slice(0, K).map(r => r.num));

                // Contar acertos no sorteio w
                const drawn = new Set((history[w].numbers || []).concat(history[w].numbers2 || []));
                let hits = 0;
                for (const n of drawn) {
                    if (topK.has(n)) hits++;
                }

                const expectedRandom = K * drawSize / totalRange;
                totalHits += hits;
                totalExpected += expectedRandom;
                validTests++;
            }

            if (validTests > 0 && totalExpected > 0) {
                lifts[key] = totalHits / totalExpected; // lift > 1 = melhor que acaso
            } else {
                lifts[key] = 1.0; // Neutro
            }
        }

        // Converter lifts em pesos (normalizar)
        const engineKeys = Object.keys(lifts);
        let totalLift = 0;
        for (const key of engineKeys) {
            totalLift += Math.max(0.1, lifts[key]); // Mínimo 10% para qualquer engine
        }
        const weights = {};
        for (const key of engineKeys) {
            weights[key] = Math.max(0.1, lifts[key]) / totalLift;
        }

        console.log('[ENSEMBLE] 📊 Calibração (backtest ' + W + ' sorteios):');
        for (const key of engineKeys) {
            const liftPct = ((lifts[key] - 1) * 100).toFixed(1);
            const emoji = lifts[key] > 1.05 ? '🟢' : lifts[key] < 0.95 ? '🔴' : '⚪';
            console.log('[ENSEMBLE]   ' + emoji + ' ' + key + ': lift=' + lifts[key].toFixed(3) +
                ' (' + (liftPct > 0 ? '+' : '') + liftPct + '% vs acaso) → peso=' + (weights[key] * 100).toFixed(0) + '%');
        }

        const result = { weights, lifts, backtestWindow: W, reason: 'Calibrado' };
        this._calibrationCache[gameKey] = result;
        this._calibrationHistoryLength[gameKey] = history.length;
        return result;
    }

    // ═══════════════════════════════════════════════════════════
    //  OBTER SCORES DE UM ENGINE ESPECÍFICO (para backtest)
    // ═══════════════════════════════════════════════════════════
    static _getEngineScores(engineKey, gameKey, history, startNum, endNum, totalRange, drawSize) {
        try {
            switch (engineKey) {
                case 'novaEra': {
                    if (typeof NovaEraEngine === 'undefined') return null;
                    const profile = NovaEraEngine.getProfile(gameKey);
                    NovaEraEngine._currentDrawSize = drawSize;
                    let scores;
                    try { scores = NovaEraEngine._scoreAllNumbers(gameKey, profile, history, startNum, endNum, totalRange); }
                    finally { NovaEraEngine._sniperMode = false; }
                    return scores;
                }
                case 'quantum': {
                    if (typeof QuantumGodEngine === 'undefined') return null;
                    const wp = QuantumGodEngine.getWeightProfile(gameKey);
                    return this._extractQuantumScores(gameKey, history, wp, startNum, endNum, drawSize);
                }
                case 'bias': {
                    if (typeof StatisticalBiasEngine === 'undefined' || history.length < 20) return null;
                    const result = StatisticalBiasEngine.analyze(gameKey, history, totalRange);
                    if (!result || !result.numberScores) return null;
                    const scores = {};
                    for (let n = startNum; n <= endNum; n++) {
                        scores[n] = result.numberScores[n] ? result.numberScores[n].evidenceScore : 0;
                    }
                    return scores;
                }
                case 'precision': {
                    if (typeof PrecisionCalibrator === 'undefined') return null;
                    const last3 = PrecisionCalibrator.analyzeLast3Trends(gameKey, history, startNum, endNum);
                    const cond = PrecisionCalibrator.buildConditionalProbMatrix(gameKey, history, startNum, endNum, drawSize);
                    const scores = {};
                    for (let n = startNum; n <= endNum; n++) {
                        scores[n] = ((last3[n] || 0.5) * 0.55) + ((cond[n] || 0.5) * 0.45);
                    }
                    return scores;
                }
            }
        } catch (e) {
            console.warn('[ENSEMBLE] Backtest ' + engineKey + ' falhou:', e.message);
        }
        return null;
    }

    // ═══════════════════════════════════════════════════════════
    //  FASE 5: POOL ADAPTATIVO POR VOLUME
    // ═══════════════════════════════════════════════════════════
    static _buildAdaptivePool(ensemble, numGames, drawSize, gameKey) {
        const { scores, agreement, startNum, endNum, totalRange } = ensemble;
        const engineCount = ensemble.enginesUsed.length;

        // Ranking por score final
        const ranked = [];
        for (let n = startNum; n <= endNum; n++) {
            ranked.push({ num: n, score: scores[n] || 0, agreement: agreement[n] || 0 });
        }
        ranked.sort((a, b) => b.score - a.score);

        let pool, strategy;

        if (numGames <= 10) {
            // CONSENSO MÁXIMO — só números com agreement alto
            strategy = 'CONSENSO_MAXIMO';
            const minAgreement = Math.max(2, engineCount - 1);
            const consensusPicks = ranked.filter(r => r.agreement >= minAgreement);
            // Mínimo: drawSize * 2
            const minPool = drawSize * 2;
            if (consensusPicks.length >= minPool) {
                pool = consensusPicks.slice(0, Math.max(minPool, drawSize * 3)).map(r => r.num);
            } else {
                pool = ranked.slice(0, Math.max(minPool, drawSize * 3)).map(r => r.num);
            }
        } else if (numGames <= 50) {
            // CONSENSO + DIVERSIDADE
            strategy = 'CONSENSO_DIVERSIDADE';
            const poolSize = Math.min(totalRange, Math.round(drawSize * 4.5));
            pool = ranked.slice(0, poolSize).map(r => r.num);
        } else if (numGames <= 200) {
            // COBERTURA INTELIGENTE
            strategy = 'COBERTURA_INTELIGENTE';
            const poolSize = Math.min(totalRange, Math.round(drawSize * 6));
            pool = ranked.slice(0, poolSize).map(r => r.num);
        } else if (numGames <= 1000) {
            // COBERTURA AMPLA
            strategy = 'COBERTURA_AMPLA';
            const poolSize = Math.min(totalRange, Math.round(totalRange * 0.7));
            pool = ranked.slice(0, poolSize).map(r => r.num);
        } else {
            // COBERTURA MÁXIMA — usa quase todo range mas ordena por score
            strategy = 'COBERTURA_MAXIMA';
            pool = ranked.map(r => r.num);
        }

        pool.sort((a, b) => a - b);
        pool._strategy = strategy;

        console.log('[ENSEMBLE] Estratégia: ' + strategy + ' | Pool: ' + pool.length + '/' + totalRange + ' números');
        return pool;
    }

    // ═══════════════════════════════════════════════════════════
    //  CONSTRUIR LAYERED POOL PARA COVERAGEENGINE
    // ═══════════════════════════════════════════════════════════
    static _buildLayeredPool(ensemble, pool, gameKey, drawSize) {
        const { scores, startNum, endNum } = ensemble;
        const ranked = [];
        for (let n = startNum; n <= endNum; n++) {
            ranked.push({ num: n, score: scores[n] || 0 });
        }
        ranked.sort((a, b) => b.score - a.score);

        // Tamanhos adaptativos por loteria
        let coreSize = Math.round(drawSize * 2);
        let hotSize = Math.round(drawSize * 3.5);

        const lotteryMultipliers = {
            lotofacil: { core: 1.2, hot: 1.5 },
            lotomania: { core: 3.0, hot: 4.0 },
            timemania: { core: 2.0, hot: 3.0 },
            diadesorte: { core: 1.7, hot: 2.5 }
        };

        if (lotteryMultipliers[gameKey]) {
            coreSize = Math.round(drawSize * lotteryMultipliers[gameKey].core);
            hotSize = Math.round(drawSize * lotteryMultipliers[gameKey].hot);
        }

        return {
            core: ranked.slice(0, coreSize).map(r => r.num).sort((a, b) => a - b),
            hot: ranked.slice(0, hotSize).map(r => r.num).sort((a, b) => a - b),
            full: ranked.map(r => r.num).sort((a, b) => a - b),
            scores: scores,
            ranked: ranked
        };
    }

    // ═══════════════════════════════════════════════════════════
    //  DAMPENING DE SCORES POR VOLUME — v14.0
    //
    //  PROBLEMA: scores brutos têm amplitude de ~20x entre o número
    //  mais e menos favorecido. Quando passados como pesos de roleta
    //  ao CoverageEngine, causam CV de 54% em 10.000 jogos.
    //
    //  SOLUÇÃO: amortecimento por potência fracionária.
    //   score_damp = score_normalizado ^ exponent
    //   onde exponent diminui com o volume:
    //
    //   volume=10    → exponent=1.0  (scores brutos — bias máximo)
    //   volume=50    → exponent=0.80 (leve amortecimento)
    //   volume=200   → exponent=0.60 (moderado)
    //   volume=1000  → exponent=0.40 (forte)
    //   volume=10000 → exponent=0.15 (quase-uniforme, CV esperado < 8%)
    // ═══════════════════════════════════════════════════════════
    static _dampScoresByVolume(scores, numGames, startNum, endNum) {
        let exponent;
        if      (numGames <= 10)   exponent = 1.00;
        else if (numGames <= 50)   exponent = 0.80;
        else if (numGames <= 200)  exponent = 0.60;
        else if (numGames <= 1000) exponent = 0.40;
        else if (numGames <= 5000) exponent = 0.25;
        else                       exponent = 0.15;

        if (exponent >= 1.0) return scores;

        let minScore = Infinity, maxScore = -Infinity;
        for (let n = startNum; n <= endNum; n++) {
            const s = scores[n] || 0;
            if (s < minScore) minScore = s;
            if (s > maxScore) maxScore = s;
        }
        const range = maxScore - minScore;
        const damped = {};
        for (let n = startNum; n <= endNum; n++) {
            const s = scores[n] || 0;
            const normalized = range > 0 ? 0.01 + (s - minScore) / range * 0.99 : 0.5;
            damped[n] = Math.pow(normalized, exponent);
        }

        const dampedVals = Object.values(damped);
        const ampDepois = (Math.max(...dampedVals) / Math.min(...dampedVals)).toFixed(2);
        console.log('[ENSEMBLE] Dampening v14: volume=' + numGames + ' | exponent=' + exponent + ' | amplitude após=' + ampDepois + 'x');
        return damped;
    }

    // ═══════════════════════════════════════════════════════════
    //  FASE 7: VALIDAÇÃO CRUZADA PÓS-GERAÇÃO
    //  Cada jogo é avaliado pelo consenso. Jogos fracos são
    //  substituídos por jogos melhores do lote rejeitado.
    // ═══════════════════════════════════════════════════════════
    static _crossValidate(games, ensemble, drawSize, numGames) {
        if (games.length <= 5 || numGames > 500) return games; // Skip para lotes muito grandes (performance)

        const { scores } = ensemble;

        // Pontuar cada jogo pelo score médio do consenso
        const scored = games.map((game, idx) => {
            const avgScore = game.reduce((sum, n) => sum + (scores[n] || 0), 0) / game.length;
            return { game, avgScore, idx };
        });

        // Ordenar por score
        scored.sort((a, b) => b.avgScore - a.avgScore);

        // Remover os 10% piores (se possível) e substituir por versões do melhor grupo
        const cutoff = Math.max(1, Math.floor(scored.length * 0.10));
        const weakCount = Math.min(cutoff, scored.length - numGames);

        if (weakCount <= 0) return games;

        // Só descartar se temos excedente
        const kept = scored.slice(0, scored.length - weakCount).map(s => s.game);

        const replacedCount = scored.length - kept.length;
        if (replacedCount > 0) {
            console.log('[ENSEMBLE] 🔄 Validação cruzada: ' + replacedCount + ' jogos fracos descartados');
        }

        return kept.length >= numGames ? kept.slice(0, numGames) : games.slice(0, numGames);
    }

    // ═══════════════════════════════════════════════════════════
    //  TOP N DO CONSENSO (para exibição na UI)
    // ═══════════════════════════════════════════════════════════
    static _getConsensusTop(ensemble, n) {
        const { scores, agreement, startNum, endNum } = ensemble;
        const ranked = [];
        for (let num = startNum; num <= endNum; num++) {
            ranked.push({ num, score: +(scores[num] || 0).toFixed(3), agreement: agreement[num] || 0 });
        }
        ranked.sort((a, b) => b.score - a.score);
        return ranked.slice(0, n);
    }

    // ═══════════════════════════════════════════════════════════
    //  UTILITÁRIOS
    // ═══════════════════════════════════════════════════════════

    static _getHistory(gameKey) {
        let history = [];
        try {
            if (typeof StatsService !== 'undefined') {
                history = StatsService.getRecentResults(gameKey, 200) || [];
            }
            if (history.length === 0 && typeof REAL_HISTORY_DB !== 'undefined') {
                history = REAL_HISTORY_DB[gameKey] || [];
            }
        } catch (e) {
            console.warn('[ENSEMBLE] Falha ao obter histórico:', e.message);
        }
        return history;
    }

    static _getProfile(gameKey) {
        const profiles = {
            megasena:   { range: [1, 60], drawSize: 6, zones: 6, zoneSize: 10 },
            lotofacil:  { range: [1, 25], drawSize: 15, zones: 5, zoneSize: 5 },
            quina:      { range: [1, 80], drawSize: 5, zones: 8, zoneSize: 10 },
            duplasena:  { range: [1, 50], drawSize: 6, zones: 5, zoneSize: 10 },
            lotomania:  { range: [0, 99], drawSize: 20, zones: 10, zoneSize: 10 },
            timemania:  { range: [1, 80], drawSize: 7, zones: 8, zoneSize: 10 },
            diadesorte: { range: [1, 31], drawSize: 7, zones: 4, zoneSize: 8 }
        };
        return profiles[gameKey] || profiles.megasena;
    }

    static _engineToKey(engineName) {
        const map = { 'NovaEra': 'novaEra', 'Quantum': 'quantum', 'StatisticalBias': 'bias', 'Precision': 'precision' };
        return map[engineName] || engineName.toLowerCase();
    }

    static _fallback(gameKey, numGames, selectedNumbers, fixedNumbers, drawSize, opts) {
        if (typeof SmartCoverageEngine !== 'undefined') {
            return SmartCoverageEngine.generate(gameKey, numGames, selectedNumbers, fixedNumbers, drawSize, opts);
        }
        if (typeof CoverageEngine !== 'undefined') {
            return CoverageEngine.generate(gameKey, numGames, selectedNumbers || [], fixedNumbers || [], drawSize, opts);
        }
        return { games: [], analysis: { error: 'Nenhum engine disponível' } };
    }

    // ═══════════════════════════════════════════════════════════
    //  RELATÓRIO DE CALIBRAÇÃO (para UI)
    // ═══════════════════════════════════════════════════════════
    static getCalibrationReport(gameKey) {
        const history = this._getHistory(gameKey);
        if (history.length < 10) return { error: 'Histórico insuficiente' };

        const profile = this._getProfile(gameKey);
        const startNum = profile.range[0];
        const endNum = profile.range[1];
        const totalRange = endNum - startNum + 1;
        const drawSize = profile.drawSize;
        const enginesUsed = [];

        if (typeof NovaEraEngine !== 'undefined') enginesUsed.push('NovaEra');
        if (typeof QuantumGodEngine !== 'undefined') enginesUsed.push('Quantum');
        if (typeof StatisticalBiasEngine !== 'undefined') enginesUsed.push('StatisticalBias');
        if (typeof PrecisionCalibrator !== 'undefined') enginesUsed.push('Precision');

        return this._calibrate(gameKey, history, startNum, endNum, totalRange, drawSize, enginesUsed);
    }
}

console.log('%c[ENSEMBLE] ★ EnsembleEngine v1.0 — Consenso Multi-Motor carregado', 'color: #06B6D4; font-weight: bold; font-size: 14px;');
