/**
 * BACKTESTING ENGINE V1 — Validação de Performance
 * ================================================
 * Testa os motores SmartBets e QuantumGod contra dados REAIS
 * antes de apresentar jogos ao usuário.
 * 
 * Metodologia:
 * 1. Para cada concurso T nos últimos N, simula geração usando histórico T-1
 * 2. Compara jogos gerados com resultado REAL do concurso T
 * 3. Calcula métricas: média de acertos, % ≥ 11, % ≥ 12, % ≥ 13
 * 4. Compara com baseline aleatório
 * 
 * "Confiança baseada em DADOS, não em esperança."
 */
class BacktestingEngine {

    /**
     * Roda backtesting para um motor específico
     * @param {string} gameKey - 'lotofacil', 'timemania', etc
     * @param {string} engine - 'smart' ou 'quantum'
     * @param {number} numGames - Quantidade de jogos por simulação
     * @param {number} numConcursos - Quantos concursos testar (default: 8)
     * @returns {Object} Resultado do backtesting
     */
    // v11.1 Fix: numConcursos default elevado para 35 (acima do threshold de significância de 30)
    // Bug anterior: default=20 < threshold=30, então a warning "indeterminado" era exibida SEMPRE
    static run(gameKey, engine = 'smart', numGames = 10, numConcursos = 35) {
        const game = GAMES[gameKey];
        if (!game) return null;

        let fullHistory = [];
        try {
            fullHistory = StatsService.getRecentResults(gameKey, 200) || [];
        } catch(e) {
            console.warn('[Backtest] Sem histórico');
            return null;
        }

        if (fullHistory.length < numConcursos + 10) {
            console.warn('[Backtest] Histórico insuficiente:', fullHistory.length);
            return null;
        }

        console.log(`[Backtest] 🧪 Iniciando backtesting ${gameKey} (${engine}) — ${numConcursos} concursos, ${numGames} jogos cada`);

        const results = [];
        // CRITICO: usar game.draw (bolas sorteadas), NAO game.minBet (aposta)
        // Lotomania: minBet=50 (aposta) != draw=20 (sorteio) → bug afeta expectedRandom
        const drawSize = game.draw || game.minBet;
        const betSize  = game.minBet; // tamanho da aposta do jogador (para gerar jogos)

        for (let t = 0; t < numConcursos; t++) {
            // Concurso a testar (resultado real)
            const targetDraw = fullHistory[t];
            // Histórico disponível ANTES desse concurso
            const trainingHistory = fullHistory.slice(t + 1);

            if (!targetDraw || !targetDraw.numbers || trainingHistory.length < 5) continue;

            // Simular geração de jogos
            let games = [];
            
            if (engine === 'smart') {
                // ★ GOD MODE FIX: Clonar historyStore ao invés de sobrescrever
                // Bug anterior: sobrescrever causava race condition se outro código
                // acessasse StatsService durante o backtest
                const savedHistory = StatsService.historyStore[gameKey] ? [...StatsService.historyStore[gameKey]] : [];
                StatsService.historyStore[gameKey] = [...trainingHistory];
                
                try {
                    // v11.0: NovaEraEngine substitui SmartBetsEngine no backtesting
                    const result = NovaEraEngine.generate(gameKey, numGames, null, [], betSize, { precisionMode: false, precisionPoolSize: 0 });
                    games = result.games || [];
                } catch(e) {
                    console.warn('[Backtest] Erro na geração:', e.message);
                }
                
                // Restaurar (com cópia segura)
                StatsService.historyStore[gameKey] = savedHistory;
            } else if (engine === 'quantum') {
                try {
                    const suggested = QuantumGodEngine.runSimulation(gameKey, drawSize, trainingHistory);
                    // O quantum gera sugestões, não jogos completos — usar como pool
                    if (suggested && suggested.length > 0) {
                        // Gerar variações usando o pool quantum
                        games = this._generateFromPool(suggested, drawSize, numGames, game);
                    }
                } catch(e) {
                    console.warn('[Backtest] Erro quantum:', e.message);
                }
            }

            if (games.length === 0) continue;

            // Conferir cada jogo contra o resultado real
            const targetSet = new Set(targetDraw.numbers);
            const drawResults = {
                drawNumber: targetDraw.drawNumber,
                targetNumbers: targetDraw.numbers,
                hits: [],
                bestHit: 0,
                avgHit: 0
            };

            for (const ticket of games) {
                let hits = 0;
                for (const num of ticket) {
                    if (targetSet.has(num)) hits++;
                }
                drawResults.hits.push(hits);
                if (hits > drawResults.bestHit) drawResults.bestHit = hits;
            }

            drawResults.avgHit = drawResults.hits.reduce((a, b) => a + b, 0) / drawResults.hits.length;
            results.push(drawResults);
        }

        if (results.length === 0) return null;

        // Calcular métricas agregadas
        const metrics = this._calculateMetrics(results, gameKey, drawSize);

        console.log(`[Backtest] ✅ Concluído: ${results.length} concursos testados`);
        console.log(`[Backtest] 📊 Média geral: ${metrics.avgHits.toFixed(1)} | Melhor: ${metrics.bestOverall}`);
        console.log(`[Backtest] 📊 ≥11: ${metrics.pct11plus}% | ≥12: ${metrics.pct12plus}% | ≥13: ${metrics.pct13plus}%`);
        console.log(`[Backtest] 📊 vs Acaso: ${metrics.improvement > 0 ? '+' : ''}${metrics.improvement.toFixed(1)}%`);

        return metrics;
    }

    /**
     * Gerar jogos a partir de um pool de números sugeridos
     */
    static _generateFromPool(pool, drawSize, numGames, gameConfig) {
        const games = [];
        const minBet = drawSize;
        
        for (let g = 0; g < numGames; g++) {
            const ticket = [];
            const available = pool.slice();
            
            // Se pool tem tamanho exato = usar direto
            if (available.length <= minBet) {
                games.push(available.sort((a, b) => a - b));
                continue;
            }
            
            // Selecionar aleatoriamente do pool
            while (ticket.length < minBet && available.length > 0) {
                const idx = Math.floor(Math.random() * available.length);
                ticket.push(available[idx]);
                available.splice(idx, 1);
            }
            
            games.push(ticket.sort((a, b) => a - b));
        }
        
        return games;
    }

    /**
     * Calcular métricas detalhadas — V2: adaptativo por jogo
     */
    static _calculateMetrics(results, gameKey, drawSize) {
        let totalHits = 0;
        let totalGames = 0;
        let bestOverall = 0;
        let hitsByDraw = [];

        // V2: Thresholds específicos por jogo (faixas de premiação reais)
        const thresholds = this._getGameThresholds(gameKey);
        const hitCounts = {};
        thresholds.forEach(t => hitCounts[t] = 0);

        for (const draw of results) {
            for (const hit of draw.hits) {
                totalHits += hit;
                totalGames++;
                if (hit > bestOverall) bestOverall = hit;
                thresholds.forEach(t => { if (hit >= t) hitCounts[t]++; });
            }
            hitsByDraw.push({
                draw: draw.drawNumber,
                avg: draw.avgHit.toFixed(1),
                best: draw.bestHit,
                target: draw.targetNumbers.join(', ')
            });
        }

        const avgHits = totalGames > 0 ? totalHits / totalGames : 0;

        // Calcular baseline aleatório
        const game = GAMES[gameKey];
        const totalRange = game ? (game.range[1] - game.range[0] + 1) : 25;
        const drawnPerGame = game ? game.draw : 15;
        // v7.1: Para Lotomania, betSize (50) != drawSize (20)
        // expectedRandom = quantos acertos um jogo de betSize números teria ao acaso
        const actualBetSize = game ? (game.minBet || drawSize) : drawSize;
        const expectedRandom = actualBetSize * drawnPerGame / totalRange;
        const improvement = expectedRandom > 0 ? ((avgHits - expectedRandom) / expectedRandom) * 100 : 0;

        // v11.1: Critério de significância consistente com o default (35 > 30)
        const sampleTooSmall = results.length < 30;
        let confidenceLevel = 'baixa';
        let confidenceColor = '#EF4444';
        if (sampleTooSmall) {
            confidenceLevel = 'indeterminada (amostra < 30)';
            confidenceColor = '#94a3b8';
        } else {
            // GOD MODE: Thresholds mais rigorosos
            // 25%+ melhoria = alta (antes era 10% - muito fácil)
            if (improvement >= 25) { confidenceLevel = 'alta'; confidenceColor = '#10B981'; }
            else if (improvement >= 10) { confidenceLevel = 'média'; confidenceColor = '#F59E0B'; }
            else if (improvement >= 3) { confidenceLevel = 'marginal'; confidenceColor = '#F97316'; }
            else { confidenceLevel = 'baixa'; confidenceColor = '#EF4444'; }
        }

        const pctByThreshold = {};
        thresholds.forEach(t => {
            pctByThreshold[t] = totalGames > 0 ? Math.round(hitCounts[t] / totalGames * 100) : 0;
        });

        return {
            gameKey, engine: 'smart', concursosTested: results.length,
            totalGames, avgHits, bestOverall,
            expectedRandom: expectedRandom.toFixed(1),
            improvement, thresholds, pctByThreshold,
            pct11plus: pctByThreshold[11] || 0,
            pct12plus: pctByThreshold[12] || 0,
            pct13plus: pctByThreshold[13] || 0,
            confidenceLevel, confidenceColor, hitsByDraw,
            sampleTooSmall,
            summary: `Média: ${avgHits.toFixed(1)} hits (acaso: ${expectedRandom}) | Melhor: ${bestOverall}${sampleTooSmall ? ' | ⚠️ amostra < 15' : ''}`
        };
    }

    static _getGameThresholds(gameKey) {
        const map = {
            lotofacil:   [11, 12, 13],
            timemania:   [3, 4, 5],
            megasena:    [4, 5, 6],
            quina:       [2, 3, 4],
            duplasena:   [3, 4, 5],
            // Lotomania: acertos em jogos individuais (jogo tem 50 nums, acerto vs 20 drawn)
            // Premio começa em 0 acertos (!) ou a partir de 15 acertos
            lotomania:   [12, 15, 18],
            diadesorte:  [3, 4, 5]
        };
        return map[gameKey] || [3, 4, 5];
    }

    /**
     * Formatar resultado para exibição na UI — V2: adaptativo
     */
    static formatForUI(metrics) {
        if (!metrics) return '<span style="color: #94A3B8;">Sem dados para backtesting</span>';

        const icon = metrics.improvement >= 5 ? '✅' : (metrics.improvement >= 0 ? '⚠️' : '❌');
        const gameNames = {
            lotofacil: 'Lotofácil', timemania: 'Timemania', megasena: 'Mega Sena',
            quina: 'Quina', duplasena: 'Dupla Sena', lotomania: 'Lotomania', diadesorte: 'Dia de Sorte'
        };

        let thresholdRows = '';
        if (metrics.thresholds && metrics.pctByThreshold) {
            metrics.thresholds.forEach(t => {
                const pct = metrics.pctByThreshold[t] || 0;
                const color = pct > 0 ? '#10B981' : '#F1F5F9';
                const weight = pct > 0 ? '700' : '400';
                thresholdRows += '<span style="color: #CBD5E1;">≥' + t + ' pts:</span>';
                thresholdRows += '<span style="color: ' + color + '; font-weight: ' + weight + '; text-align: right;">' + pct + '%</span>';
            });
        }

        return '<div style="padding: 10px; background: rgba(0,0,0,0.3); border-radius: 8px; border: 1px solid ' + metrics.confidenceColor + '40; margin-top: 8px;">' +
            '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">' +
                '<span style="font-weight: 700; color: ' + metrics.confidenceColor + '; font-size: 0.85rem;">' + icon + ' Backtesting ' + (gameNames[metrics.gameKey] || metrics.gameKey) + '</span>' +
                '<span style="font-size: 0.75rem; color: #94A3B8;">' + metrics.concursosTested + ' concursos</span>' +
            '</div>' +
            '<div style="display: grid; grid-template-columns: 1fr 1fr; gap: 4px; font-size: 0.78rem;">' +
                '<span style="color: #CBD5E1;">Média acertos:</span>' +
                '<span style="color: ' + metrics.confidenceColor + '; font-weight: 600; text-align: right;">' + metrics.avgHits.toFixed(1) + ' (acaso: ' + metrics.expectedRandom + ')</span>' +
                '<span style="color: #CBD5E1;">Melhor resultado:</span>' +
                '<span style="color: #F1F5F9; font-weight: 600; text-align: right;">' + metrics.bestOverall + ' pontos</span>' +
                '<span style="color: #CBD5E1;">Melhoria vs acaso:</span>' +
                '<span style="color: ' + metrics.confidenceColor + '; font-weight: 600; text-align: right;">' + (metrics.improvement >= 0 ? '+' : '') + metrics.improvement.toFixed(1) + '%</span>' +
                thresholdRows +
            '</div>' +
            '<div style="margin-top: 6px; padding-top: 6px; border-top: 1px solid rgba(255,255,255,0.05);">' +
                '<span style="font-size: 0.7rem; color: ' + metrics.confidenceColor + '; font-weight: 600; text-transform: uppercase; letter-spacing: 1px;">Confiança: ' + metrics.confidenceLevel + '</span>' +
                (metrics.sampleTooSmall ? '<span style="font-size: 0.65rem; color: #94a3b8; display:block; margin-top:2px;">⚠️ Amostra < 15 sorteios — resultado estatisticamente inconclusivo</span>' : '') +
            '</div>' +
        '</div>';
    }
}
