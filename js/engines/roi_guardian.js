/**
 * ╔══════════════════════════════════════════════════════════════════════════╗
 * ║  ROI GUARDIAN v1.0 — Guardião de Retorno sobre Investimento            ║
 * ║  "A verdade que nenhum motor de loteria te conta"                       ║
 * ║                                                                        ║
 * ║  Calcula ROI REAL antes de gerar jogos:                                ║
 * ║  • Probabilidade exata por faixa (distribuição hipergeométrica)        ║
 * ║  • Retorno esperado (EV) por concurso                                  ║
 * ║  • ROI % real                                                          ║
 * ║  • Break-even: quantos jogos para 50% de chance de acertar faixa X    ║
 * ║  • Kelly Criterion simplificado                                        ║
 * ╚══════════════════════════════════════════════════════════════════════════╝
 */
class ROIGuardian {

    // ═══ TABELA DE PRÊMIOS MÉDIOS (atualizáveis) ═══════════════════════
    // Fonte: médias dos últimos 12 meses de resultados da Caixa
    static getPrizeTable() {
        return {
            megasena: {
                ticketCost: 6.00,
                range: 60, draw: 6,
                // [acertos, prêmio médio estimado, nome da faixa]
                prizes: [
                    { hits: 6, avgPrize: 40000000, name: 'Sena' },
                    { hits: 5, avgPrize: 40000,    name: 'Quina' },
                    { hits: 4, avgPrize: 900,      name: 'Quadra' }
                ]
            },
            lotofacil: {
                ticketCost: 3.50,
                range: 25, draw: 15,
                prizes: [
                    { hits: 15, avgPrize: 1500000, name: '15 acertos' },
                    { hits: 14, avgPrize: 1200,    name: '14 acertos' },
                    { hits: 13, avgPrize: 30,      name: '13 acertos' },
                    { hits: 12, avgPrize: 12,      name: '12 acertos' },
                    { hits: 11, avgPrize: 6,       name: '11 acertos' }
                ]
            },
            quina: {
                ticketCost: 2.50,
                range: 80, draw: 5,
                prizes: [
                    { hits: 5, avgPrize: 6000000, name: 'Quina' },
                    { hits: 4, avgPrize: 6500,    name: 'Quadra' },
                    { hits: 3, avgPrize: 4,       name: 'Terno' },
                    { hits: 2, avgPrize: 2,       name: 'Duque' }
                ]
            },
            duplasena: {
                ticketCost: 2.50,
                range: 50, draw: 6,
                prizes: [
                    { hits: 6, avgPrize: 3000000, name: 'Sena' },
                    { hits: 5, avgPrize: 5000,    name: 'Quina' },
                    { hits: 4, avgPrize: 60,      name: 'Quadra' },
                    { hits: 3, avgPrize: 3,       name: 'Terno' }
                ]
            },
            lotomania: {
                ticketCost: 3.00,
                range: 100, draw: 20,
                prizes: [
                    { hits: 20, avgPrize: 5000000, name: '20 acertos' },
                    { hits: 19, avgPrize: 50000,   name: '19 acertos' },
                    { hits: 18, avgPrize: 1500,    name: '18 acertos' },
                    { hits: 17, avgPrize: 30,      name: '17 acertos' },
                    { hits: 16, avgPrize: 10,      name: '16 acertos' },
                    { hits: 15, avgPrize: 5,       name: '15 acertos' },
                    { hits: 0,  avgPrize: 5,       name: '0 acertos' }
                ]
            },
            timemania: {
                ticketCost: 3.50,
                range: 80, draw: 7,
                prizes: [
                    { hits: 7, avgPrize: 7000000, name: '7 acertos' },
                    { hits: 6, avgPrize: 8000,    name: '6 acertos' },
                    { hits: 5, avgPrize: 20,      name: '5 acertos' },
                    { hits: 4, avgPrize: 7,       name: '4 acertos' },
                    { hits: 3, avgPrize: 2,       name: '3 acertos' }
                ]
            },
            diadesorte: {
                ticketCost: 2.50,
                range: 31, draw: 7,
                prizes: [
                    { hits: 7, avgPrize: 1500000, name: '7 acertos' },
                    { hits: 6, avgPrize: 1500,    name: '6 acertos' },
                    { hits: 5, avgPrize: 25,      name: '5 acertos' },
                    { hits: 4, avgPrize: 5,       name: '4 acertos' }
                ]
            }
        };
    }

    // ═══ COMBINAÇÕES C(n,k) ═══════════════════════════════════════════
    static _comb(n, k) {
        if (k < 0 || k > n) return 0;
        if (k === 0 || k === n) return 1;
        if (k > n - k) k = n - k;
        let r = 1;
        for (let i = 0; i < k; i++) {
            r = r * (n - i) / (i + 1);
        }
        return Math.round(r);
    }

    // ═══ PROBABILIDADE HIPERGEOMÉTRICA ═════════════════════════════════
    // P(acertar exatamente k | apostando betSize números, sorteando draw de range)
    static _hypergeometric(k, range, draw, betSize) {
        // P = C(draw,k) × C(range-draw, betSize-k) / C(range, betSize)
        const num = this._comb(draw, k) * this._comb(range - draw, betSize - k);
        const den = this._comb(range, betSize);
        return den > 0 ? num / den : 0;
    }

    // ═══ ANÁLISE ROI COMPLETA ═════════════════════════════════════════
    /**
     * Calcula ROI real para um cenário de aposta
     * @param {string} gameKey - chave da loteria
     * @param {number} numGames - quantidade de jogos
     * @param {number} betSize - números por jogo (pode ser > minBet)
     * @param {object} customPrizes - prêmios customizados (opcional, para jackpots)
     * @returns {object} análise completa de ROI
     */
    static analyze(gameKey, numGames, betSize, customPrizes) {
        const table = this.getPrizeTable();
        const info = table[gameKey];
        if (!info) return { error: 'Loteria não encontrada: ' + gameKey };

        const actualBetSize = betSize || info.draw;
        const ticketCost = info.ticketCost;
        const investment = numGames * ticketCost;
        const range = info.range;
        const draw = info.draw;

        // Calcular probabilidade e EV para cada faixa
        const breakdown = [];
        let totalEV = 0;

        for (const prize of info.prizes) {
            const prob = this._hypergeometric(prize.hits, range, draw, actualBetSize);
            const probPerGame = prob;
            const expectedWinsTotal = probPerGame * numGames;
            const avgPrize = (customPrizes && customPrizes[prize.hits]) || prize.avgPrize;
            const ev = expectedWinsTotal * avgPrize;
            totalEV += ev;

            // Break-even: quantos jogos para 50% de chance de pelo menos 1 acerto
            // P(pelo menos 1) = 1 - (1-p)^n = 0.5 → n = log(0.5)/log(1-p)
            const gamesFor50pct = prob > 0 ? Math.ceil(Math.log(0.5) / Math.log(1 - prob)) : Infinity;

            breakdown.push({
                faixa: prize.name,
                hits: prize.hits,
                probability: prob,
                probabilityPct: (prob * 100).toFixed(6) + '%',
                expectedWins: expectedWinsTotal,
                prize: avgPrize,
                ev: ev,
                gamesFor50pct: gamesFor50pct,
                investmentFor50pct: gamesFor50pct * ticketCost
            });
        }

        const roi = investment > 0 ? ((totalEV - investment) / investment) * 100 : 0;
        const netResult = totalEV - investment;

        // Kelly Criterion simplificado (para a faixa de maior prêmio)
        const topPrize = breakdown[0];
        const kellyFraction = topPrize.probability > 0
            ? (topPrize.probability * (topPrize.prize / ticketCost) - (1 - topPrize.probability)) / (topPrize.prize / ticketCost)
            : 0;

        // Rating de viabilidade
        let rating, ratingEmoji, ratingColor;
        if (roi >= -20) { rating = 'FAVORÁVEL'; ratingEmoji = '🟢'; ratingColor = '#10B981'; }
        else if (roi >= -50) { rating = 'ACEITÁVEL'; ratingEmoji = '🟡'; ratingColor = '#F59E0B'; }
        else if (roi >= -70) { rating = 'DESFAVORÁVEL'; ratingEmoji = '🟠'; ratingColor = '#F97316'; }
        else { rating = 'NÃO RECOMENDADO'; ratingEmoji = '🔴'; ratingColor = '#EF4444'; }

        // Ratio draw/range (indicador de "amigabilidade" para IA)
        const drawRangeRatio = (draw / range * 100).toFixed(1);
        let iaAdvantage;
        if (draw / range >= 0.5) iaAdvantage = 'ALTA — IA faz diferença real';
        else if (draw / range >= 0.2) iaAdvantage = 'MODERADA — IA ajuda nos filtros';
        else if (draw / range >= 0.1) iaAdvantage = 'BAIXA — IA pouco impacta';
        else iaAdvantage = 'NENHUMA — equivalente ao acaso';

        return {
            gameKey,
            investment,
            ticketCost,
            numGames,
            betSize: actualBetSize,
            totalEV: Math.round(totalEV * 100) / 100,
            netResult: Math.round(netResult * 100) / 100,
            roi: Math.round(roi * 100) / 100,
            rating,
            ratingEmoji,
            ratingColor,
            breakdown,
            kelly: {
                fraction: Math.max(0, kellyFraction),
                recommended: kellyFraction > 0,
                explanation: kellyFraction > 0
                    ? 'Kelly recomenda apostar ' + (kellyFraction * 100).toFixed(4) + '% do bankroll'
                    : 'Kelly recomenda NÃO apostar (EV negativo)'
            },
            drawRangeRatio: drawRangeRatio + '%',
            iaAdvantage,
            // Resumo em português
            summary: `${ratingEmoji} ${rating} | Investimento: R$ ${investment.toFixed(2)} | Retorno esperado: R$ ${totalEV.toFixed(2)} | ROI: ${roi.toFixed(1)}%`
        };
    }

    // ═══ RANKING DE LOTERIAS POR EV ═══════════════════════════════════
    /**
     * Compara todas as loterias e retorna ranking por ROI
     * @param {number} numGames - jogos por loteria para comparação
     * @param {object} jackpots - prêmios atuais {megasena: 50000000, ...}
     * @returns {Array} ranking ordenado por ROI (melhor → pior)
     */
    static rankAllLotteries(numGames, jackpots) {
        const table = this.getPrizeTable();
        const results = [];

        for (const gameKey of Object.keys(table)) {
            const customPrizes = {};
            if (jackpots && jackpots[gameKey]) {
                // Substituir prêmio máximo pelo jackpot atual
                const maxHits = table[gameKey].prizes[0].hits;
                customPrizes[maxHits] = jackpots[gameKey];
            }
            const analysis = this.analyze(gameKey, numGames || 10, null, customPrizes);
            results.push(analysis);
        }

        results.sort((a, b) => b.roi - a.roi);
        return results;
    }

    // ═══ GERAR HTML DO PAINEL ROI ═══════════════════════════════════════
    static renderPanel(gameKey, numGames, betSize, customPrizes) {
        // ★ GOD MODE v2: Buscar jackpot REAL do StatsService
        if (!customPrizes && typeof StatsService !== 'undefined' && StatsService.prizeStore) {
            var liveInfo = StatsService.prizeStore[gameKey];
            if (liveInfo && liveInfo.estimatedPrize > 0) {
                var table = this.getPrizeTable();
                var gameInfo = table[gameKey];
                if (gameInfo && gameInfo.prizes && gameInfo.prizes.length > 0) {
                    customPrizes = {};
                    customPrizes[gameInfo.prizes[0].hits] = liveInfo.estimatedPrize;
                }
            }
        }
        const r = this.analyze(gameKey, numGames, betSize, customPrizes);
        if (r.error) return `<div style="color:#EF4444">${r.error}</div>`;

        let html = `
        <div style="background:linear-gradient(145deg,rgba(15,23,42,0.98),rgba(30,41,59,0.95));border:2px solid ${r.ratingColor}40;border-radius:14px;padding:16px;margin-top:12px;box-shadow:0 4px 20px rgba(0,0,0,0.4);">
            <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px;">
                <span style="font-size:1.3rem;">${r.ratingEmoji}</span>
                <span style="color:${r.ratingColor};font-weight:800;font-size:1rem;text-transform:uppercase;letter-spacing:1px;">${r.rating}</span>
                <span style="margin-left:auto;color:#94a3b8;font-size:0.7rem;">ROI Guardian v1.0</span>
            </div>

            <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:14px;">
                <div style="background:rgba(0,0,0,0.3);padding:10px;border-radius:10px;text-align:center;">
                    <div style="color:#94a3b8;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.5px;">Investimento</div>
                    <div style="color:#F87171;font-size:1.1rem;font-weight:800;">R$ ${r.investment.toFixed(2)}</div>
                </div>
                <div style="background:rgba(0,0,0,0.3);padding:10px;border-radius:10px;text-align:center;">
                    <div style="color:#94a3b8;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.5px;">Retorno Esperado</div>
                    <div style="color:#34D399;font-size:1.1rem;font-weight:800;">R$ ${r.totalEV.toFixed(2)}</div>
                </div>
            </div>

            <div style="background:rgba(0,0,0,0.4);padding:10px;border-radius:10px;text-align:center;margin-bottom:14px;border:1px solid ${r.ratingColor}30;">
                <div style="color:#94a3b8;font-size:0.65rem;text-transform:uppercase;margin-bottom:2px;">ROI Esperado</div>
                <div style="color:${r.ratingColor};font-size:1.4rem;font-weight:900;">${r.roi.toFixed(1)}%</div>
                <div style="color:#64748b;font-size:0.6rem;margin-top:2px;">Resultado líquido: R$ ${r.netResult.toFixed(2)}</div>
            </div>

            <div style="margin-bottom:10px;">
                <div style="color:#cbd5e1;font-size:0.7rem;font-weight:700;margin-bottom:6px;text-transform:uppercase;letter-spacing:0.5px;">📊 Detalhamento por Faixa</div>
                <table style="width:100%;border-collapse:collapse;font-size:0.68rem;">
                    <tr style="color:#64748b;border-bottom:1px solid #334155;">
                        <td style="padding:4px;">Faixa</td>
                        <td style="padding:4px;text-align:right;">Probabilidade</td>
                        <td style="padding:4px;text-align:right;">Acertos Esp.</td>
                        <td style="padding:4px;text-align:right;">Prêmio</td>
                    </tr>`;

        for (const b of r.breakdown) {
            const probColor = b.probability > 0.01 ? '#34D399' : b.probability > 0.001 ? '#FBBF24' : '#F87171';
            html += `
                    <tr style="border-bottom:1px solid #1e293b;">
                        <td style="padding:4px;color:#e2e8f0;">${b.faixa}</td>
                        <td style="padding:4px;text-align:right;color:${probColor};">${b.probabilityPct}</td>
                        <td style="padding:4px;text-align:right;color:#94a3b8;">${b.expectedWins < 0.01 ? '<0.01' : b.expectedWins.toFixed(2)}</td>
                        <td style="padding:4px;text-align:right;color:#cbd5e1;">R$ ${b.prize.toLocaleString('pt-BR')}</td>
                    </tr>`;
        }

        html += `
                </table>
            </div>

            <div style="display:flex;gap:6px;flex-wrap:wrap;margin-top:8px;">
                <div style="flex:1;min-width:120px;background:rgba(59,130,246,0.08);border:1px solid rgba(59,130,246,0.2);padding:6px 8px;border-radius:8px;">
                    <div style="color:#60a5fa;font-size:0.6rem;text-transform:uppercase;">Draw/Range</div>
                    <div style="color:#93c5fd;font-size:0.85rem;font-weight:700;">${r.drawRangeRatio}</div>
                </div>
                <div style="flex:1;min-width:120px;background:rgba(139,92,246,0.08);border:1px solid rgba(139,92,246,0.2);padding:6px 8px;border-radius:8px;">
                    <div style="color:#a78bfa;font-size:0.6rem;text-transform:uppercase;">Vantagem IA</div>
                    <div style="color:#c4b5fd;font-size:0.72rem;font-weight:600;">${r.iaAdvantage}</div>
                </div>
            </div>

            <div style="margin-top:8px;padding:6px 8px;background:rgba(0,0,0,0.3);border-radius:8px;font-size:0.6rem;color:#64748b;">
                💡 ${r.kelly.explanation}
            </div>
        </div>`;

        return html;
    }
}

// Exportar para uso global
if (typeof window !== 'undefined') window.ROIGuardian = ROIGuardian;
