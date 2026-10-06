/**
 * ╔══════════════════════════════════════════════════════════════════════════╗
 * ║  SMART COVERAGE ENGINE v1.0 — Adaptativo por Volume                    ║
 * ║  Motor Unificado de Cobertura — Substitui SmartBetsEngine              ║
 * ║                                                                        ║
 * ║  Princípio: a estratégia ótima depende do VOLUME solicitado.           ║
 * ║  • 1–20 jogos  → ClosureEngine (fechamento exato) ou CoverageEngine    ║
 * ║                  com candidatos altos (melhor cobertura por jogo).     ║
 * ║  • 21–500      → CoverageEngine puro (Set Cover matemático).           ║
 * ║  • 501+        → CoverageEngine adaptativo com candidatos reduzidos.   ║
 * ║                                                                        ║
 * ║  v1.0 — Sem DOM, sem IA de predição. Pura matemática combinatória.    ║
 * ╚══════════════════════════════════════════════════════════════════════════╝
 */
class SmartCoverageEngine {

    // ─── Estratégia por volume ────────────────────────────────────────────
    static _getStrategy(numGames) {
        if (numGames <= 20)  return 'CLOSURE';
        if (numGames <= 500) return 'COVERAGE';
        return 'COVERAGE_FAST';
    }

    // ─── Cache do Sniper Pool e do NovaEra Scoring (TTL 60s) ────────────
    // Inicializado abaixo da classe para compatibilidade com browsers antigos
    // (static class fields requerem suporte ES2022)

    static _clearSniperCache(gameKey) {
        if (!SmartCoverageEngine._sniperCache) SmartCoverageEngine._sniperCache = {};
        if (!SmartCoverageEngine._novaEraCache) SmartCoverageEngine._novaEraCache = {};
        if (gameKey) {
            delete SmartCoverageEngine._sniperCache[gameKey + '_20'];
            delete SmartCoverageEngine._novaEraCache[gameKey];
        } else {
            SmartCoverageEngine._sniperCache = {};
            SmartCoverageEngine._novaEraCache = {};
        }
    }

    // ─── Construção do Alvo do Sniper ────────────────────────────────────
    static _buildSniperPool(gameKey, game, numGames, poolSizePreference) {
        let history = [];
        if (typeof StatsService !== 'undefined') history = StatsService.getRecentResults(gameKey, 200) || [];
        if (history.length === 0 && typeof REAL_HISTORY_DB !== 'undefined') history = REAL_HISTORY_DB[gameKey] || [];

        const start = game.range[0];
        const end = game.range[1];
        const totalRange = end - start + 1;
        // v16.1 FIX: usar game.draw com fallback para game.minBet (evita NaN)
        const gameDraw = game.draw || game.minBet || 6;

        // v16.1 FIX: Validar poolSizePreference — parseInt pode retornar NaN
        let targetSize = (poolSizePreference && !isNaN(poolSizePreference) && poolSizePreference > 0)
            ? Math.floor(poolSizePreference) : 0;

        if (!targetSize) {
            if (numGames <= 10)       targetSize = Math.round(gameDraw * 2.8);
            else if (numGames <= 30)  targetSize = Math.round(gameDraw * 3.8);
            else if (numGames <= 100) targetSize = Math.round(gameDraw * 5.0);
            else                      targetSize = Math.round(gameDraw * 7.0);
        }
        targetSize = Math.max(gameDraw, Math.min(targetSize, totalRange));

        // v16.2 CACHE TTL: Verificar cache antes de recalcular
        const cacheKey = gameKey + '_' + targetSize;
        if (!SmartCoverageEngine._sniperCache) SmartCoverageEngine._sniperCache = {};
        const cached = SmartCoverageEngine._sniperCache[cacheKey];
        const CACHE_TTL = 60000;
        if (cached && (Date.now() - cached.ts) < CACHE_TTL && cached.pool.length >= gameDraw) {
            console.log('[SmartCoverage] 🎯 Sniper CACHE HIT: ' + cached.pool.length + ' dezenas (expira em ' + Math.round((CACHE_TTL - (Date.now() - cached.ts)) / 1000) + 's)');
            return cached.pool;
        }

        // v16.1 FIX: Se não há histórico, retornar pool uniforme
        if (history.length === 0) {
            console.warn('[SmartCoverage] ⚠️ Sniper sem histórico: seleção uniforme de ' + targetSize + ' números.');
            const uniformPool = [];
            const step = totalRange / targetSize;
            for (let ui = 0; ui < targetSize; ui++) {
                uniformPool.push(Math.min(end, Math.round(start + ui * step)));
            }
            return [...new Set(uniformPool)].sort((a, b) => a - b);
        }

        // 1. v16.2 SCORING RÁPIDO — 3 camadas em vez de 21 (100x mais rápido)
        // NovaEraEngine._scoreAllNumbers leva 400ms-7s bloqueando o UI.
        // Para o pool sniper, frequência + atraso + tendência recente são suficientes.
        const t0pool = Date.now();
        const quantumScores = {};
        const freq = {};      // frequência total
        const lastSeen = {};  // último sorteio em que apareceu (índice)
        for (let i = start; i <= end; i++) { freq[i] = 0; lastSeen[i] = history.length; }

        // Camada 1: Frequência ponderada (sorteios recentes valem mais)
        const histLimit = Math.min(history.length, 100);
        for (let hi = 0; hi < histLimit; hi++) {
            const decay = 1 / (1 + hi * 0.03); // decay temporal
            const nums = (history[hi].numbers || []).concat(history[hi].numbers2 || []);
            nums.forEach(n => {
                if (n >= start && n <= end) {
                    freq[n] = (freq[n] || 0) + decay;
                    if (lastSeen[n] === history.length) lastSeen[n] = hi; // primeiro achado = atraso
                }
            });
        }

        // Camada 2: Atraso (números com maior atraso recebem impulso)
        const maxDelay = Math.max(...Object.values(lastSeen));
        for (let i = start; i <= end; i++) {
            const delay = lastSeen[i] === history.length ? maxDelay : lastSeen[i];
            const delayScore = delay / Math.max(1, maxDelay); // 0-1: 1 = mais atrasado
            quantumScores[i] = (freq[i] || 0) + delayScore * 0.5;
        }

        // Camada 3: Impulso recente (últimos 5 sorteios valem 3x)
        history.slice(0, 5).forEach(draw => {
            (draw.numbers || []).concat(draw.numbers2 || []).forEach(n => {
                if (n >= start && n <= end) quantumScores[n] = (quantumScores[n] || 0) + 3;
            });
        });

        console.log('[SmartCoverage] ⚡ Scoring rápido (3 camadas): ' + (Date.now() - t0pool) + 'ms | ' + histLimit + ' sorteios analisados');

        // 2. Bônus adicional de DUPLAS (solicitação específica para o Sniper)
        // Analisa as últimas 15 extrações para ver quem sai junto com mais frequência
        const recentDraws = history.slice(0, 15);
        const pairsFreq = {};
        const numberPairBonus = {};
        for (let i = start; i <= end; i++) numberPairBonus[i] = 0;

        recentDraws.forEach(draw => {
            const nums = (draw.numbers || []).concat(draw.numbers2 || []);
            for (let i = 0; i < nums.length; i++) {
                for (let j = i + 1; j < nums.length; j++) {
                    const n1 = nums[i], n2 = nums[j];
                    if (n1 >= start && n1 <= end && n2 >= start && n2 <= end) {
                        const key = n1 < n2 ? `${n1}-${n2}` : `${n2}-${n1}`;
                        pairsFreq[key] = (pairsFreq[key] || 0) + 1;
                    }
                }
            }
        });

        // Para cada dezena, soma o peso das duplas fortes que ela forma
        Object.keys(pairsFreq).forEach(key => {
            const freq = pairsFreq[key];
            if (freq > 1) { // Só consideramos duplas que repetiram nos últimos 15 concursos
                const [n1, n2] = key.split('-').map(Number);
                numberPairBonus[n1] += freq * 2; // peso forte
                numberPairBonus[n2] += freq * 2;
            }
        });

        // 3. Tendência de Curto Prazo (Últimos 3 sorteios ganham impulso forte)
        const shortTermDraws = history.slice(0, 3);
        const shortTermBonus = {};
        for (let i = start; i <= end; i++) shortTermBonus[i] = 0;
        shortTermDraws.forEach(draw => {
            const nums = (draw.numbers || []).concat(draw.numbers2 || []);
            nums.forEach(n => {
                if (n >= start && n <= end) shortTermBonus[n] += 15;
            });
        });

        // 4. [targetSize já calculado acima — v16.1 movido para o início]

        // 5. v14.0: Evidência Estatística (Detector de Viés com p-valor)
        // Se o StatisticalBiasEngine estiver disponível, usar z-scores formais
        // ao invés de frequência bruta para informar o pool do Sniper
        const biasBonus = {};
        for (let i = start; i <= end; i++) biasBonus[i] = 0;
        let biasVerdict = null;

        if (typeof StatisticalBiasEngine !== 'undefined' && history.length >= 30) {
            try {
                const biasResult = StatisticalBiasEngine.analyze(gameKey, history, targetSize);
                if (biasResult && biasResult.numberScores) {
                    biasVerdict = biasResult.verdict;
                    const scores = biasResult.numberScores;
                    
                    // Se viés detectado → peso forte nos números com evidência
                    // Se sem viés → peso leve (apenas para equilíbrio de zonas)
                    const biasWeight = biasVerdict.biasDetected ? 30 : 8;
                    
                    for (let n = start; n <= end; n++) {
                        if (scores[n]) {
                            // Números com evidência significativa de aparição acima do esperado
                            if (scores[n].hasSignificance && scores[n].direction === 'acima') {
                                biasBonus[n] += scores[n].absEvidence * biasWeight;
                            }
                            // Penalizar números significativamente ABAIXO (com evidência)
                            else if (scores[n].hasSignificance && scores[n].direction === 'abaixo') {
                                biasBonus[n] -= scores[n].absEvidence * (biasWeight * 0.5);
                            }
                        }
                    }
                    console.log('[SmartCoverage] 🔬 BiasEngine: ' + biasVerdict.emoji + ' ' + biasVerdict.level +
                        ' | Peso aplicado: ' + biasWeight);
                }
            } catch (e) {
                console.warn('[SmartCoverage] BiasEngine indisponível:', e.message);
            }
        }

        // 6. Combinar todos os scores para criar o RANKING FINAL DO SNIPER
        const finalScores = {};
        for (let i = start; i <= end; i++) {
            finalScores[i] = (quantumScores[i] || 1) + (numberPairBonus[i] || 0) + (shortTermBonus[i] || 0) + (biasBonus[i] || 0);
        }

        const sortedNumbers = Object.keys(finalScores)
            .map(Number)
            .sort((a, b) => finalScores[b] - finalScores[a]);

        const sniperPool = sortedNumbers.slice(0, targetSize).sort((a, b) => a - b);
        
        console.log(`[SmartCoverage] 🎯 Sniper: ${sniperPool.length} dezenas | ${history.length} sorteios | pool=${poolSizePreference}, draw=${gameDraw}`);
        // Salvar no cache para próximas chamadas (instantâneo por 60s)
        SmartCoverageEngine._sniperCache[cacheKey] = { pool: sniperPool, ts: Date.now() };
        return sniperPool;
    }

    // ─── Ponto de entrada ─────────────────────────────────────────────────
    static generate(gameKey, numGames, selectedNumbers, fixedNumbers, drawSize, options) {
        const t0 = Date.now();
        const opts = options || {};

        // Delegação oficial para Super Sete B2B
        if (gameKey === 'supersete' && typeof MotorSuperSeteB2BEngine !== 'undefined') {
            console.log('%c[SmartCoverage] ⚡ Delegando Super Sete para MotorSuperSeteB2BEngine...', 'color: #38bdf8; font-weight: bold;');
            const ssRes = MotorSuperSeteB2BEngine._gerarFallbackNativo(numGames, opts);
            const games = (ssRes && ssRes.jogos) ? ssRes.jogos.map(j => j.jogo) : [];
            return {
                games,
                analysis: {
                    strategy: 'MOTOR_SUPERSETE_B2B',
                    engineVersion: 'MotorSuperSeteB2B',
                    avgHamming: ssRes.metricas_carteira?.hamming_medio || 5.2,
                    coveragePct: ssRes.icm_global || 85,
                    elapsed: (Date.now() - t0) + 'ms'
                }
            };
        }

        const strategy = this._getStrategy(numGames);

        console.log('[SmartCoverage] Strategy:', strategy, '| Games:', numGames, '| Game:', gameKey, '| drawSize:', drawSize);

        // ── CLOSURE: Para poucos jogos, tenta fechamento via ClosureEngine ──
        if (strategy === 'CLOSURE') {
            const v = selectedNumbers ? selectedNumbers.length : 0;
            // v12.11: ClosureEngine é para Fechamentos Matemáticos Pequenos (v <= 25).
            // Para v maiores (ex: 60 números da Mega Sena), a explosão combinatória O(N^t) trava o navegador.
            if (typeof ClosureEngine !== 'undefined' && drawSize <= 15 && v > 0 && v <= 25) {
                try {
                    const result = ClosureEngine.generate(gameKey, numGames, selectedNumbers, fixedNumbers, drawSize);
                    if (result && result.games && result.games.length > 0) {
                        result.analysis = result.analysis || {};
                        result.analysis.strategy = 'CLOSURE';
                        result.analysis.engineVersion = 'SmartCoverage-v1.0';
                        console.log('[SmartCoverage] ClosureEngine OK:', result.games.length, 'jogos em', (Date.now() - t0) + 'ms');
                        return result;
                    }
                } catch (e) {
                    console.warn('[SmartCoverage] ClosureEngine falhou, fallback para CoverageEngine:', e.message);
                }
            }
            // Fallback: CoverageEngine com candidatos altos para poucos jogos
            console.log('[SmartCoverage] Fallback para CoverageEngine (poucos jogos)');
        }

        // ── COVERAGE: Set Cover matemático puro ────────────────────────────
        if (typeof CoverageEngine === 'undefined') {
            console.error('[SmartCoverage] CoverageEngine não disponível!');
            return { games: [], analysis: { error: 'CoverageEngine não carregado' } };
        }

        // v12.2 Auto-Fixador Cirúrgico (Lotofácil)
        // Se alto volume, trava os 3 melhores numeros do mapa de calor espacial como FIXOS
        let lotoFixed = fixedNumbers || [];
        if (gameKey === 'lotofacil' && numGames >= 1000 && (!selectedNumbers || selectedNumbers.length === 0) && (!fixedNumbers || fixedNumbers.length === 0)) {
            const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
            if (game) {
                const heatPool = this._buildSniperPool(gameKey, game, numGames, 25);
                lotoFixed = heatPool.slice(0, 3); // Fixa os Top 3
                console.log('[SmartCoverage] Auto-Fixador Lotofácil ativado. Top 3 fixos:', lotoFixed);
            }
        }

        // v12.5 Auto-Fixador Lotomania
        if (gameKey === 'lotomania' && numGames >= 1000 && (!selectedNumbers || selectedNumbers.length === 0) && (!fixedNumbers || fixedNumbers.length === 0)) {
            const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
            if (game) {
                const heatPool = this._buildSniperPool(gameKey, game, numGames, 100);
                lotoFixed = heatPool.slice(0, 15); // Fixa as Top 15 estatísticas (v12.6)
                console.log('[SmartCoverage] Auto-Fixador Lotomania ativado. Top 15 fixos:', lotoFixed);
            }
        }

        // v14.0: POOL COMPLETO PARA TODOS OS VOLUMES ALTOS
        // BUG CORRIGIDO: As amputações abaixo eliminavam 15-45% dos números de cada loteria,
        // gerando jogos que NUNCA cobriam parte do volante.
        // Evidência: análise de 10.000 jogos mostrou 20 números ausentes na Timemania,
        // 6 ausentes no Dia de Sorte, e cobertura < 65% em Quina e Dupla Sena.
        //
        // ESTRATÉGIA CORRIGIDA: Pool sempre completo para alto volume.
        // O scoring do NovaEra já ordena por relevância; o CoverageEngine
        // usa Set Cover que naturalmente distribui entre todos os números.
        //
        // Removido:
        //   Lotomania: precisionPoolSize = 80 (era 100 → 80, perdia 20 números)
        //   Dia de Sorte: precisionPoolSize = 28 (era 31 → 28, perdia 6 números)
        //   Timemania: precisionPoolSize = 65 (era 80 → 65, perdia 20 números)
        //   Dupla Sena: precisionPoolSize = 28 (era 50 → 28, perdia 22 números)
        //   Quina: precisionPoolSize = 30-40 (era 80 → 30-40, perdia 40-50 números)
        console.log('[SmartCoverage] v14.0: Pool completo ativado para ' + gameKey + ' (' + numGames + ' jogos)');

        // ══════════════════════════════════════════════════════════════
        // v13.3: POOL ESCALONADO MULTI-LOTERIA — 21 Camadas de Inteligência
        // Em vez de gerar aleatório, usa NovaEraEngine._scoreAllNumbers()
        // para ranquear os números e construir as camadas de pool dinamicamente:
        // ══════════════════════════════════════════════════════════════
        if (!selectedNumbers || selectedNumbers.length === 0) {
            if (typeof NovaEraEngine !== 'undefined') {
                try {
                    const profile = NovaEraEngine.getProfile(gameKey);
                    const startNum = profile.range[0];
                    const endNum = profile.range[1];
                    const totalRange = endNum - startNum + 1;

                    // Obter histórico
                    let history = [];
                    if (typeof StatsService !== 'undefined') {
                        history = StatsService.getRecentResults(gameKey, 200) || [];
                    }
                    if (history.length === 0 && typeof REAL_HISTORY_DB !== 'undefined') {
                        history = REAL_HISTORY_DB[gameKey] || [];
                    }

                    if (history.length > 0) {
                        // ★ PILAR 1: 21 CAMADAS DE INTELIGÊNCIA
                        // v16.2 CACHE: NovaEra leva 400ms-7s — cachear por 60s por loteria
                        if (!SmartCoverageEngine._novaEraCache) SmartCoverageEngine._novaEraCache = {};
                        const neCacheKey = gameKey;
                        const neCached = SmartCoverageEngine._novaEraCache[neCacheKey];
                        const NE_TTL = 60000;
                        let scores;
                        if (neCached && (Date.now() - neCached.ts) < NE_TTL) {
                            scores = neCached.scores;
                            console.log('[SmartCoverage] ⚡ NovaEra CACHE HIT: ' + gameKey + ' (expira em ' + Math.round((NE_TTL - (Date.now() - neCached.ts)) / 1000) + 's)');
                        } else {
                            const profileDrawSize = profile.drawSize || drawSize;
                            NovaEraEngine._currentDrawSize = profileDrawSize;
                            NovaEraEngine._sniperMode = numGames > 100;
                            try {
                                scores = NovaEraEngine._scoreAllNumbers(
                                    gameKey, profile, history, startNum, endNum, totalRange
                                );
                                // Salvar no cache
                                SmartCoverageEngine._novaEraCache[neCacheKey] = { scores, ts: Date.now() };
                            } finally {
                                NovaEraEngine._sniperMode = false;
                            }
                        }

                        // Ranking por score (maior → menor)
                        const ranked = [];
                        for (let n = startNum; n <= endNum; n++) {
                            ranked.push({ num: n, score: scores[n] || 0 });
                        }
                        ranked.sort((a, b) => b.score - a.score);

                        // ★ PILAR 2: POOL ESCALONADO DINÂMICO
                        let coreSize = 12;
                        let hotSize = 24;
                        if (gameKey === 'lotofacil') { coreSize = 18; hotSize = 22; }
                        else if (gameKey === 'quina') { coreSize = 10; hotSize = 20; }
                        else if (gameKey === 'duplasena') { coreSize = 12; hotSize = 22; }
                        else if (gameKey === 'lotomania') { coreSize = 60; hotSize = 80; }
                        else if (gameKey === 'timemania') { coreSize = 15; hotSize = 25; }
                        else if (gameKey === 'diadesorte') { coreSize = 12; hotSize = 18; }
                        
                        opts.layeredPool = {
                            core:    ranked.slice(0, coreSize).map(r => r.num).sort((a,b) => a-b),
                            hot:     ranked.slice(0, hotSize).map(r => r.num).sort((a,b) => a-b),
                            full:    ranked.map(r => r.num).sort((a,b) => a-b),
                            scores:  scores,
                            ranked:  ranked
                        };

                        console.log('%c[SmartCoverage] v13.3 ★ 21 CAMADAS ATIVAS PARA ' + gameKey.toUpperCase(), 'color: #F59E0B; font-weight: bold;');
                        console.log('[SmartCoverage] NÚCLEO QUENTE (Top ' + coreSize + '):', 
                            opts.layeredPool.core.map(n => n + '(' + scores[n].toFixed(2) + ')').join(', '));
                        console.log('[SmartCoverage] ZONA QUENTE (Top ' + hotSize + '):', 
                            opts.layeredPool.hot.join(', '));
                        console.log('[SmartCoverage] Histórico analisado:', history.length, 'sorteios');
                    }
                } catch (e) {
                    console.warn('[SmartCoverage] v13.3 NovaEra falhou, fallback aleatório:', e.message);
                }
            }
        }

        // Se o Sniper está ativo e o usuário não forçou números, calcula a Âncora Topológica
        let sniperPool = [];
        if (opts.precisionMode && (!selectedNumbers || selectedNumbers.length === 0)) {
            const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
            if (game) {
                sniperPool = this._buildSniperPool(gameKey, game, numGames, opts.precisionPoolSize);
                console.log('[SmartCoverage] 🎯 Sniper Ativo: Alvo concentrado em', sniperPool.length, 'dezenas:', sniperPool);
            }
        }

        // Passar opções de pool para CoverageEngine
        const coverageOpts = {
            precisionMode: opts.precisionMode || false,
            precisionPool: sniperPool.length > 0 ? sniperPool : null,
            strategy: strategy,
            layeredPool: opts.layeredPool || null,
            quantumScores: opts.layeredPool ? opts.layeredPool.scores : null
        };

        // v13.2: Sem modo rápido — qualidade sobre velocidade
        console.log('[SmartCoverage] Strategy:', strategy, '| Layered:', !!opts.layeredPool);

        let result;
        try {
            result = CoverageEngine.generate(
                gameKey,
                numGames,
                selectedNumbers || [],
                lotoFixed.length > 0 ? lotoFixed : (fixedNumbers || []), // v12.9 FIX: Passa a âncora fixa pro motor
                drawSize,
                coverageOpts // v12.9 FIX: O 6o parametro e options, nao previousGames
            );
        } catch (e) {
            console.error('[SmartCoverage] CoverageEngine falhou:', e.message);
            return { games: [], analysis: { error: e.message } };
        }

        if (!result) result = { games: [], analysis: {} };
        result.analysis = result.analysis || {};
        result.analysis.strategy = strategy;
        result.analysis.engineVersion = 'SmartCoverage-v1.1-Sniper';
        result.analysis.elapsed = (Date.now() - t0) + 'ms';
        if (sniperPool.length > 0) {
            result.analysis.sniperPoolSize = sniperPool.length;
        }

        // ── Calcular Distância de Hamming média ───────────────────────────
        if (result.games && result.games.length > 1) {
            result.analysis.avgHamming = this._calcAvgHamming(result.games, drawSize);
        }

        console.log('[SmartCoverage] Resultado:', result.games.length, 'jogos em', result.analysis.elapsed,
            '| Hamming:', result.analysis.avgHamming || 'N/A');
        return result;
    }

    // ─── Distância de Hamming média entre jogos ────────────────────────────────────
    // v11.1 Fix: amostra de pares ALEATÓRIOS (não adjacentes).
    // Pares adjacentes no Set Cover têndem a ser semelhantes, subestimando a diversidade real.
    static _calcAvgHamming(games, drawSize) {
        if (games.length < 2) return drawSize;
        let totalDiff = 0;
        let count = 0;
        const sampleSize = Math.min(games.length, 50);
        // Amostra de pares aleatórios (não apenas adjacentes)
        for (let s = 0; s < sampleSize; s++) {
            const i = Math.floor(Math.random() * games.length);
            let j = Math.floor(Math.random() * games.length);
            if (j === i) j = (i + 1) % games.length;
            const setA = new Set(games[i]);
            let diff = 0;
            for (const n of games[j]) { if (!setA.has(n)) diff++; }
            totalDiff += diff;
            count++;
        }
        return count > 0 ? Math.round(totalDiff / count) : drawSize;
    }

    // ─── Calcular métricas honestas para exibição ──────────────────────────────
    // Retorna probabilidades hipergeométricas REAIS por faixa de prêmio
    // v11.1 Fix: usa game.draw (bolas sorteadas) não game.minBet (aposta do jogador)
    static calcRealMetrics(games, gameKey) {
        const game = (typeof GAMES !== 'undefined') ? GAMES[gameKey] : null;
        if (!game || !games || games.length === 0) return {};

        const n = game.range[1] - game.range[0] + 1;  // total de números na loteria
        // v11.1: sorteados pela loteria (ex: Timemania=7, Mega Sena=6, Lotofácil=15)
        // game.draw é o campo correto; game.minBet é o tamanho da APOSTA
        const K = game.draw || game.minBet;            // bolas sorteadas
        const numGames = games.length;
        const drawSize = games[0] ? games[0].length : (game.minBet); // tamanho da aposta

        // Probabilidade de acertar exatamente `hits` em um jogo
        // P(X=hits) = C(K,hits) * C(n-K, drawSize-hits) / C(n, drawSize)
        const _comb = (a, b) => {
            if (b < 0 || b > a) return 0;
            if (b === 0 || b === a) return 1;
            b = Math.min(b, a - b);
            let r = 1;
            for (let i = 0; i < b; i++) { r = r * (a - i) / (i + 1); /* Sem limite de e15 para Lotomania */ }
            return r;
        };

        const totalCombos = _comb(n, drawSize);
        const metrics = {};

        // Faixas de prêmio: do máximo ao mínimo premíado
        const prizes = [];
        const maxHits = Math.min(K, drawSize);
        const minPrizedHits = Math.max(maxHits - 3, 0);
        for (let hits = maxHits; hits >= minPrizedHits; hits--) {
            const prob = (_comb(K, hits) * _comb(n - K, drawSize - hits)) / totalCombos;
            if (prob > 0) prizes.push({ hits, prob, probPct: (prob * 100).toFixed(8) });
        }

        // Probabilidade de PELO MENOS UM jogo acertar, em `numGames` tentativas
        prizes.forEach(p => {
            const probAtLeastOne = 1 - Math.pow(1 - p.prob, numGames);
            p.probAtLeastOnePct = (probAtLeastOne * 100).toFixed(4);
        });

        metrics.prizes = prizes;
        metrics.totalCombos = totalCombos.toExponential(2);
        metrics.numGames = numGames;
        metrics.drawSize = drawSize;
        metrics.K = K;
        metrics.note = 'Probabilidades hipergeométricas exatas. Loteria é independente de histórico.';

        return metrics;
    }
}

// Inicialização dos caches fora da classe (compatível com todos os browsers)
SmartCoverageEngine._sniperCache   = {};   // Pool do Sniper — TTL 60s por loteria
SmartCoverageEngine._novaEraCache  = {};   // Scores NovaEra — TTL 60s por loteria
