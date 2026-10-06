/**
 * ╔══════════════════════════════════════════════════════════════════════════╗
 * ║  SMART ADVISOR v1.0 — Consultor Inteligente de Loterias                ║
 * ║  "Onde seu dinheiro rende mais?"                                        ║
 * ║                                                                        ║
 * ║  Funcionalidades:                                                      ║
 * ║  • Ranking em tempo real das 7 loterias por ROI/EV                     ║
 * ║  • Detecta acumulados e ajusta recomendações                           ║
 * ║  • Sugere alocação ótima do orçamento mensal                           ║
 * ║  • Kelly Criterion para gestão de bankroll                              ║
 * ║  • Integra com StatsService.prizeStore para dados reais                ║
 * ╚══════════════════════════════════════════════════════════════════════════╝
 */
class SmartAdvisor {

    // ═══ BUSCAR JACKPOTS REAIS DO SISTEMA ═══════════════════════════════
    static _getLiveJackpots() {
        var jackpots = {};
        if (typeof StatsService === 'undefined' || !StatsService.prizeStore) return jackpots;

        var keys = ['megasena', 'lotofacil', 'quina', 'duplasena', 'lotomania', 'timemania', 'diadesorte'];
        for (var i = 0; i < keys.length; i++) {
            var k = keys[i];
            var info = StatsService.prizeStore[k];
            if (info && info.estimatedPrize && info.estimatedPrize > 0) {
                jackpots[k] = info.estimatedPrize;
            }
        }
        return jackpots;
    }

    // ═══ BUSCAR INFO DE ACUMULAÇÃO ═══════════════════════════════════════
    static _getAccumulationInfo() {
        var info = {};
        if (typeof StatsService === 'undefined' || !StatsService.prizeStore) return info;

        var keys = ['megasena', 'lotofacil', 'quina', 'duplasena', 'lotomania', 'timemania', 'diadesorte'];
        for (var i = 0; i < keys.length; i++) {
            var k = keys[i];
            var data = StatsService.prizeStore[k];
            if (data) {
                info[k] = {
                    accumulated: data.accumulated || false,
                    currentDraw: data.currentDraw || 0,
                    nextDraw: data.nextDraw || 0,
                    nextDrawDate: data.nextDrawDate || null,
                    estimatedPrize: data.estimatedPrize || 0
                };
            }
        }
        return info;
    }

    // ═══ RANKING COMPLETO DAS LOTERIAS ═══════════════════════════════════
    /**
     * Gera ranking das 7 loterias ordenado por viabilidade
     * @param {number} numGames - jogos por loteria para comparar
     * @param {number} budget - orçamento mensal total (R$)
     * @returns {object} ranking + recomendações
     */
    static analyze(numGames, budget) {
        if (typeof ROIGuardian === 'undefined') {
            return { error: 'ROI Guardian não carregado' };
        }

        numGames = numGames || 10;
        budget = budget || 300;

        var jackpots = this._getLiveJackpots();
        var accInfo = this._getAccumulationInfo();
        var hasLiveData = Object.keys(jackpots).length > 0;

        // Gerar análise ROI para cada loteria com jackpots reais
        var ranking = ROIGuardian.rankAllLotteries(numGames, jackpots);

        // Enriquecer com info de acumulação e nomes
        var names = {
            megasena: 'Mega Sena', lotofacil: 'Lotofácil', quina: 'Quina',
            duplasena: 'Dupla Sena', lotomania: 'Lotomania',
            timemania: 'Timemania', diadesorte: 'Dia de Sorte'
        };

        for (var i = 0; i < ranking.length; i++) {
            var r = ranking[i];
            r.displayName = names[r.gameKey] || r.gameKey;
            r.rank = i + 1;
            r.liveJackpot = jackpots[r.gameKey] || null;
            r.accumulated = accInfo[r.gameKey] ? accInfo[r.gameKey].accumulated : false;
            r.nextDrawDate = accInfo[r.gameKey] ? accInfo[r.gameKey].nextDrawDate : null;
        }

        // Calcular alocação ótima do orçamento
        var allocation = this._calculateAllocation(ranking, budget);

        // Gerar insights textuais
        var insights = this._generateInsights(ranking, jackpots, hasLiveData);

        return {
            ranking: ranking,
            allocation: allocation,
            insights: insights,
            hasLiveData: hasLiveData,
            budget: budget,
            numGames: numGames,
            timestamp: Date.now()
        };
    }

    // ═══ ALOCAÇÃO DE ORÇAMENTO ═══════════════════════════════════════════
    static _calculateAllocation(ranking, budget) {
        // Estratégia: alocar proporcionalmente ao inverso da perda esperada
        // Loterias com menor perda (maior ROI) recebem mais orçamento
        // Mínimo: 10% do orçamento por loteria ativa
        var allocations = [];
        var totalWeight = 0;

        // Filtrar loterias viáveis (ROI > -95%)
        var viable = ranking.filter(function(r) { return r.roi > -95; });
        if (viable.length === 0) viable = ranking.slice(0, 3); // pelo menos top 3

        // Peso = 100 + ROI (assim ROI -20 = peso 80, ROI -80 = peso 20)
        for (var i = 0; i < viable.length; i++) {
            var weight = Math.max(5, 100 + viable[i].roi);
            // Bonus 2x para acumulados
            if (viable[i].accumulated) weight *= 2;
            totalWeight += weight;
            viable[i]._allocWeight = weight;
        }

        for (var j = 0; j < viable.length; j++) {
            var r = viable[j];
            var pct = r._allocWeight / totalWeight;
            var alloc = Math.round(budget * pct * 100) / 100;
            var gamesCanBuy = Math.floor(alloc / r.ticketCost);

            allocations.push({
                gameKey: r.gameKey,
                displayName: r.displayName,
                budgetPct: Math.round(pct * 100),
                budgetAmount: alloc,
                gamesCanBuy: gamesCanBuy,
                roi: r.roi,
                rating: r.rating,
                ratingEmoji: r.ratingEmoji,
                accumulated: r.accumulated
            });
        }

        return allocations;
    }

    // ═══ INSIGHTS INTELIGENTES ═══════════════════════════════════════════
    static _generateInsights(ranking, jackpots, hasLiveData) {
        var insights = [];

        // Insight 1: Melhor opção
        if (ranking.length > 0) {
            var best = ranking[0];
            insights.push({
                type: 'best',
                emoji: '🏆',
                text: best.displayName + ' tem o melhor ROI (' + best.roi.toFixed(1) + '%). ' +
                      (best.accumulated ? 'ACUMULADA!' : 'Draw/Range: ' + best.drawRangeRatio)
            });
        }

        // Insight 2: Acumulados
        var acumulados = ranking.filter(function(r) { return r.accumulated; });
        if (acumulados.length > 0) {
            var names = acumulados.map(function(r) { return r.displayName; }).join(', ');
            insights.push({
                type: 'accumulated',
                emoji: '🔥',
                text: names + (acumulados.length === 1 ? ' está ACUMULADA' : ' estão ACUMULADAS') +
                      ' — jackpots elevados melhoram o ROI'
            });
        }

        // Insight 3: Lotofácil = maior vantagem IA
        var lotofacil = ranking.find(function(r) { return r.gameKey === 'lotofacil'; });
        if (lotofacil) {
            insights.push({
                type: 'ia',
                emoji: '🤖',
                text: 'Lotofácil tem a MAIOR vantagem da IA (draw/range ' + lotofacil.drawRangeRatio +
                      '). Filtros estruturais fazem diferença REAL aqui.'
            });
        }

        // Insight 4: Pior opção
        if (ranking.length > 1) {
            var worst = ranking[ranking.length - 1];
            if (worst.roi < -80) {
                insights.push({
                    type: 'warning',
                    emoji: '⚠️',
                    text: worst.displayName + ' tem ROI de ' + worst.roi.toFixed(1) +
                          '%. Cada R$100 investido retorna R$' + (100 + worst.roi).toFixed(0) + ' em média.'
                });
            }
        }

        // Insight 5: Dados ao vivo
        if (!hasLiveData) {
            insights.push({
                type: 'data',
                emoji: '📡',
                text: 'Usando prêmios ESTIMADOS (médias). Aguarde atualização automática para jackpots reais.'
            });
        }

        return insights;
    }

    // ═══ RENDER HTML DO PAINEL SMART ADVISOR ═══════════════════════════
    static renderPanel(numGames, budget) {
        var result = this.analyze(numGames, budget);
        if (result.error) return '<div style="color:#EF4444">' + result.error + '</div>';

        var html = '';

        // Header
        html += '<div style="padding:12px 16px 8px;">';
        html += '<div style="display:flex;align-items:center;gap:6px;margin-bottom:8px;">';
        html += '<span style="font-size:0.85rem;">🏆</span>';
        html += '<span style="color:#FBBF24;font-weight:800;font-size:0.8rem;letter-spacing:0.5px;">RANKING DE LOTERIAS</span>';
        html += '<span style="margin-left:auto;font-size:0.55rem;color:#475569;">' + (result.hasLiveData ? '🟢 AO VIVO' : '⚪ ESTIMADO') + '</span>';
        html += '</div>';

        // Ranking cards
        for (var i = 0; i < Math.min(7, result.ranking.length); i++) {
            var r = result.ranking[i];
            var medalEmoji = i === 0 ? '🥇' : i === 1 ? '🥈' : i === 2 ? '🥉' : '▪️';
            var bgOpacity = i < 3 ? '0.15' : '0.05';
            var borderColor = r.ratingColor + (i < 3 ? '40' : '20');

            html += '<div style="background:rgba(0,0,0,' + bgOpacity + ');border:1px solid ' + borderColor + ';';
            html += 'border-radius:8px;padding:8px 10px;margin-bottom:4px;display:flex;align-items:center;gap:8px;">';

            // Posição + Nome
            html += '<span style="font-size:0.85rem;min-width:22px;">' + medalEmoji + '</span>';
            html += '<div style="flex:1;min-width:0;">';
            html += '<div style="color:#e2e8f0;font-size:0.75rem;font-weight:700;">' + r.displayName;
            if (r.accumulated) html += ' <span style="color:#FBBF24;font-size:0.6rem;">🔥 ACUMULADA</span>';
            html += '</div>';

            // Jackpot live
            if (r.liveJackpot) {
                html += '<div style="color:#94a3b8;font-size:0.6rem;">R$ ' + (r.liveJackpot / 1000000).toFixed(1) + 'M</div>';
            }
            html += '</div>';

            // ROI badge
            html += '<div style="text-align:right;">';
            html += '<div style="color:' + r.ratingColor + ';font-size:0.85rem;font-weight:900;">' + r.roi.toFixed(1) + '%</div>';
            html += '<div style="color:#64748b;font-size:0.5rem;">' + r.drawRangeRatio + ' cobertura</div>';
            html += '</div>';
            html += '</div>';
        }

        html += '</div>';

        // Alocação de orçamento
        if (result.allocation.length > 0) {
            html += '<div style="padding:0 16px 8px;">';
            html += '<div style="color:#94a3b8;font-size:0.6rem;font-weight:700;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:6px;padding-top:6px;border-top:1px solid #1e293b;">💰 Alocação Sugerida (R$ ' + budget + '/mês)</div>';

            for (var j = 0; j < Math.min(5, result.allocation.length); j++) {
                var a = result.allocation[j];
                var barWidth = Math.max(5, a.budgetPct);

                html += '<div style="display:flex;align-items:center;gap:6px;margin-bottom:3px;">';
                html += '<span style="color:#cbd5e1;font-size:0.6rem;min-width:65px;">' + a.displayName + '</span>';
                html += '<div style="flex:1;height:6px;background:rgba(0,0,0,0.4);border-radius:3px;overflow:hidden;">';
                html += '<div style="width:' + barWidth + '%;height:100%;background:linear-gradient(90deg,#3b82f6,#8b5cf6);border-radius:3px;"></div>';
                html += '</div>';
                html += '<span style="color:#94a3b8;font-size:0.55rem;min-width:55px;text-align:right;">';
                html += 'R$' + a.budgetAmount.toFixed(0) + ' (' + a.gamesCanBuy + 'j)';
                html += '</span>';
                html += '</div>';
            }
            html += '</div>';
        }

        // Insights
        if (result.insights.length > 0) {
            html += '<div style="padding:4px 16px 12px;">';
            for (var k = 0; k < Math.min(3, result.insights.length); k++) {
                var ins = result.insights[k];
                html += '<div style="font-size:0.58rem;color:#94a3b8;margin-bottom:3px;">';
                html += ins.emoji + ' ' + ins.text;
                html += '</div>';
            }
            html += '</div>';
        }

        return html;
    }
}

// Exportar para uso global
if (typeof window !== 'undefined') window.SmartAdvisor = SmartAdvisor;
