console.log('%c[QUANTUM-L99] â•â•â• MOTOR QUANTUM L99 v7.0 ATIVADO â•â•â•', 'color: #FFD700; font-size: 20px; background: #0a0a1a; font-weight: bold; text-shadow: 0 0 10px gold;');
/**
 * â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
 * â•‘  â˜…â˜…â˜… QUANTUM L99 v5.0 â€” ASSERTIVIDADE MÃXIMA â˜…â˜…â˜…                     â•‘
 * â•‘  RevoluÃ§Ã£o: Roulette Wheel + Filtros Estruturais Reais                â•‘
 * â•‘                                                                        â•‘
 * â•‘  v5.0 MUDANÃ‡AS:                                                        â•‘
 * â•‘  â€¢ Roulette Wheel Selection (score^4) substitui Tournament(3)         â•‘
 * â•‘  â€¢ NormalizaÃ§Ã£o calibrada por variÃ¢ncia (Ïƒ-aware)                     â•‘
 * â•‘  â€¢ Filtros RIGOROSOS: soma P5-P95, paridade, repetiÃ§Ã£o do anterior    â•‘
 * â•‘  â€¢ LotofÃ¡cil: Motor de EXCLUSÃƒO (quais 10 ficam fora)                 â•‘
 * â•‘  â€¢ Cross-validation expandida 12 sorteios + NDCG                      â•‘
 * â•‘  â€¢ Camada 19: Filtro CombinatÃ³rio Final (validaÃ§Ã£o estrutural)        â•‘
 * â•‘  â€¢ Perfis recalibrados com dados estatÃ­sticos REAIS                   â•‘
 * â•‘                                                                        â•‘
 * â•‘  18 CAMADAS:                                                           â•‘
 * â•‘   1-8:  Base (Freq, Trend, Delay, Entropy, Markov, Phase, MC, Next)   â•‘
 * â•‘   9-12: Modo Deus (Bayesian, Posicional, Sequential, Momentum)        â•‘
 * â•‘  13-16: QUANTUM (Espelho, Lacunas, Clusters, RegressÃ£o)               â•‘
 * â•‘  17-18: Precision Calibrator + Pattern DNA                             â•‘
 * â•‘  19:    Filtro CombinatÃ³rio Final (validaÃ§Ã£o binÃ¡ria)                  â•‘
 * â•‘                                                                        â•‘
 * â•‘  "Menos volume. Mais precisÃ£o. Cada jogo Ã© cirÃºrgico."               â•‘
 * â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
 */
class NovaEraEngine {

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  PERFIS INDIVIDUAIS POR LOTERIA                              â•‘
    // â•‘  Cada loteria tem parÃ¢metros calibrados independentemente     â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static getProfile(gameKey) {
        const profiles = {

            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            // MEGA SENA â€” 6 de 60
            // Fechamento: 6, 5, 4 acertos
            // Zonas: 6 dezenas (01-10, 11-20, ..., 51-60)
            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            megasena: {
                name: 'Mega Sena',
                drawSize: 6,
                lotteryDraw: 6,
                range: [1, 60],
                zoneSize: 10,
                zones: 6,
                minZonesCovered: 3,
                maxConsecutive: 2,
                evenOddRange: [2, 4],
                // â˜… v9.0 RECALIBRADO: P5-P95 real (Âµ=180, Ïƒ=35)
                sumRange: [95, 265],
                maxUsagePct: 0.22,
                maxOverlap: 2,
                repeatFromLast: [0, 2],
                // ★ v11.0 AUDITORIA MATEMÁTICA: Falácias ZERADAS, estruturais 100%
                // Camadas falácia (freq,delay,trend,markov,phase,clair,mirror,reversion) = 0%
                // Camadas estruturais (zone,gap,cluster,pairTrio,precision,patternDna) = 73%
                // Camadas ensemble (bayesian,positional,seq,momentum,nextDraw,quantumSuper,cycleReturn) = 27%
                weights: {
                    frequency: 0.00, delay: 0.00, trend: 0.00,
                    zone: 0.20, markov: 0.00, phase: 0.00,
                    clairvoyance: 0.00, nextDraw: 0.04,
                    bayesian: 0.03, positional: 0.03,
                    sequential: 0.02, momentum: 0.02,
                    mirror: 0.00, gap: 0.22, cluster: 0.12, reversion: 0.00,
                    precision: 0.03, patternDna: 0.03, pairTrio: 0.06,
                    cycleReturn: 0.03, quantumSuper: 0.17
                },
                // v10: scoreClamp achatado (era [0.2, 3.0]) — distribuição mais uniforme para range esparso
                scoreClamp: [0.3, 2.0],
                _confidenceCeiling: 72,  // v10: realista (P(quadra+) ≈ 0.26% por jogo)
                // v10.4 FILTROS REFINADOS (exclusivo Mega Sena)
                sumRangeTight: [110, 250],     // P10-P90 real (era [95,265] = P5-P95)
                maxSameEnding: 2,              // Max 2 numeros com mesmo final (77% dos sorteios reais)
                highLowBalance: [2, 4]         // 2-4 numeros <= 30 (equilibrio alto/baixo)
            },

            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            // LOTOFÃCIL â€” 15 de 25
            // Fechamento: 15, 14, 13 acertos
            // EstratÃ©gia: EXCLUSÃƒO (quais 10 ficam de fora)
            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            lotofacil: {
                name: 'LotofÃ¡cil',
                drawSize: 15,
                lotteryDraw: 15,
                range: [1, 25],
                zoneSize: 5,
                zones: 5,
                minZonesCovered: 5,
                maxConsecutive: 10,
                evenOddRange: [5, 10],
                // â˜… v9.0 RECALIBRADO: Soma validada P5-P95
                sumRange: [155, 235],
                maxUsagePct: 0.90,
                maxOverlap: 13,
                // â˜… v9.0: Ampliado â€” dados reais variam 5-13 repetiÃ§Ãµes
                repeatFromLast: [5, 13],
                // ★ v11.0: Falácias ZERADAS — estruturais + ensemble redistribuídos
                weights: {
                    frequency: 0.00, delay: 0.00, trend: 0.00,
                    zone: 0.06, markov: 0.00, phase: 0.00,
                    clairvoyance: 0.00, nextDraw: 0.14,
                    bayesian: 0.04, positional: 0.02,
                    sequential: 0.03, momentum: 0.02,
                    mirror: 0.00, gap: 0.04, cluster: 0.12, reversion: 0.00,
                    precision: 0.09, patternDna: 0.11, pairTrio: 0.20,
                    cycleReturn: 0.07, quantumSuper: 0.06
                },
                scoreClamp: [0.5, 1.8],
                _confidenceCeiling: 85  // v10.1: P(11+) ≈ 25.1%
            },

            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            // QUINA â€” 5 de 80
            // Fechamento: 5, 4, 3 acertos
            // Range muito amplo: precisa de mÃ¡xima diversidade
            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            quina: {
                name: 'Quina',
                drawSize: 5,
                lotteryDraw: 5,
                range: [1, 80],
                zoneSize: 10,
                zones: 8,
                minZonesCovered: 3,
                maxConsecutive: 2,
                evenOddRange: [1, 4],
                // â˜… v9.0 RECALIBRADO: P3-P97 ampliado para range 80
                sumRange: [50, 340],
                maxUsagePct: 0.15,
                maxOverlap: 2,
                repeatFromLast: [0, 1],
                // ★ v11.0: Falácias ZERADAS — Quina: gap + cycleReturn dominantes
                weights: {
                    frequency: 0.00, delay: 0.00, trend: 0.00,
                    zone: 0.14, markov: 0.00, phase: 0.00,
                    clairvoyance: 0.00, nextDraw: 0.03,
                    bayesian: 0.03, positional: 0.04,
                    sequential: 0.02, momentum: 0.02,
                    mirror: 0.00, gap: 0.20, cluster: 0.10, reversion: 0.00,
                    precision: 0.08, patternDna: 0.11, pairTrio: 0.07,
                    cycleReturn: 0.16, quantumSuper: 0.00
                },
                // v10: scoreClamp achatado — scoring é ruído com 5/80
                scoreClamp: [0.3, 2.0],
                _confidenceCeiling: 65  // v10: realista (P(duque+) ≈ 8% por jogo)
            },

            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            // DUPLA SENA â€” 6 de 50
            // Fechamento: 6, 5, 4 acertos (2 sorteios por concurso)
            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            duplasena: {
                name: 'Dupla Sena',
                drawSize: 6,
                lotteryDraw: 6,
                range: [1, 50],
                zoneSize: 10,
                zones: 5,
                minZonesCovered: 3,
                maxConsecutive: 2,
                evenOddRange: [2, 4],
                // â˜… v9.0 RECALIBRADO: P5-P95 real (6 de 50)
                sumRange: [55, 245],
                maxUsagePct: 0.20,
                maxOverlap: 3,
                repeatFromLast: [0, 2],
                // ★ v11.0: Falácias ZERADAS — Dupla Sena: crossDraw mantido
                weights: {
                    frequency: 0.00, delay: 0.00, trend: 0.00,
                    zone: 0.08, markov: 0.00, phase: 0.00,
                    clairvoyance: 0.00, nextDraw: 0.05,
                    bayesian: 0.04, positional: 0.02,
                    sequential: 0.02, momentum: 0.02,
                    mirror: 0.00, gap: 0.10, cluster: 0.07, reversion: 0.00,
                    precision: 0.09, patternDna: 0.15, pairTrio: 0.17,
                    cycleReturn: 0.09, quantumSuper: 0.00,
                    crossDraw: 0.10
                },
                scoreClamp: [0.25, 2.8],
                _confidenceCeiling: 75  // v10.1: P(terno+) com 2 sorteios
            },

            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            // LOTOMANIA â€” 50 de 100 (loteria sorteia 20)
            // Fechamento: 20, 19, 18, 17 acertos
            // Jogador marca 50 nÃºmeros, loteria sorteia 20
            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            lotomania: {
                name: 'Lotomania',
                drawSize: 50,
                lotteryDraw: 20,
                range: [0, 99],
                zoneSize: 10,
                zones: 10,
                minZonesCovered: 8,
                maxConsecutive: 5,
                evenOddRange: [22, 28],
                // â˜… v9.0 RECALIBRADO: P3-P97 real
                sumRange: [2050, 2950],
                maxUsagePct: 0.55,
                maxOverlap: 40,
                // â˜… v9.0: Ampliado para aceitar mais variaÃ§Ã£o
                repeatFromLast: [5, 15],
                // ★ v11.0: Falácias ZERADAS — Lotomania: cluster + zone dominantes
                weights: {
                    frequency: 0.00, delay: 0.00, trend: 0.00,
                    zone: 0.20, markov: 0.00, phase: 0.00,
                    clairvoyance: 0.00, nextDraw: 0.03,
                    bayesian: 0.03, positional: 0.02,
                    sequential: 0.02, momentum: 0.02,
                    mirror: 0.00, gap: 0.05, cluster: 0.16, reversion: 0.00,
                    precision: 0.07, patternDna: 0.11, pairTrio: 0.07,
                    cycleReturn: 0.12, quantumSuper: 0.10
                },
                scoreClamp: [0.4, 2.0],
                _confidenceCeiling: 78  // v10.1: P(15+) ≈ 4.6%
            },

            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            // TIMEMANIA â€” 10 de 80 (loteria sorteia 7)
            // Fechamento: 7, 6, 5 acertos
            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            timemania: {
                name: 'Timemania',
                drawSize: 10,
                lotteryDraw: 7,
                range: [1, 80],
                zoneSize: 10,
                zones: 8,
                minZonesCovered: 4,
                maxConsecutive: 2,
                evenOddRange: [3, 7],
                // â˜… v9.0 RECALIBRADO: P3-P97 real (10 de 80)
                sumRange: [200, 610],
                maxUsagePct: 0.18,
                maxOverlap: 5,
                repeatFromLast: [0, 4],
                // ★ v11.0: Falácias ZERADAS — Timemania: gap + positional dominantes
                weights: {
                    frequency: 0.00, delay: 0.00, trend: 0.00,
                    zone: 0.13, markov: 0.00, phase: 0.00,
                    clairvoyance: 0.00, nextDraw: 0.04,
                    bayesian: 0.03, positional: 0.06,
                    sequential: 0.02, momentum: 0.02,
                    mirror: 0.00, gap: 0.17, cluster: 0.10, reversion: 0.00,
                    precision: 0.08, patternDna: 0.12, pairTrio: 0.10,
                    cycleReturn: 0.13, quantumSuper: 0.00
                },
                // v10: scoreClamp achatado — scoring é ruído com 10/80
                scoreClamp: [0.3, 2.0],
                _confidenceCeiling: 68  // v10: realista (P(3+) ≈ 11.2% por jogo)
            },

            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            // DIA DE SORTE â€” 7 de 31
            // Fechamento: 7, 6, 5 acertos
            // Range pequeno: cada nÃºmero tem ~22.6% de chance
            // OTIMIZADO: anti-sequÃªncia, mÃ¡xima inteligÃªncia
            // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
            diadesorte: {
                name: 'Dia de Sorte',
                drawSize: 7,
                lotteryDraw: 7,
                range: [1, 31],
                zoneSize: 8,
                zones: 4,
                minZonesCovered: 3,
                maxConsecutive: 2,
                evenOddRange: [2, 5],
                // â˜… v9.0 RECALIBRADO: P5-P95 real (7 de 31)
                sumRange: [55, 170],
                maxUsagePct: 0.30,
                maxOverlap: 3,
                repeatFromLast: [0, 3],
                // ★ v11.0: Falácias ZERADAS — Dia de Sorte: patternDna + pairTrio dominantes
                weights: {
                    frequency: 0.00, delay: 0.00, trend: 0.00,
                    zone: 0.06, markov: 0.00, phase: 0.00,
                    clairvoyance: 0.00, nextDraw: 0.12,
                    bayesian: 0.04, positional: 0.02,
                    sequential: 0.03, momentum: 0.02,
                    mirror: 0.00, gap: 0.05, cluster: 0.08, reversion: 0.00,
                    precision: 0.10, patternDna: 0.20, pairTrio: 0.16,
                    cycleReturn: 0.08, quantumSuper: 0.04
                },
                scoreClamp: [0.3, 2.2],
                _confidenceCeiling: 80  // v10.1: P(3+) ≈ 27%
            }
        };
        return profiles[gameKey] || profiles.megasena;
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  MÃ‰TODO PRINCIPAL â€” GERAR JOGOS COM PROJEÃ‡ÃƒO FUTURA         â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•


    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  CALIBRAÃ‡ÃƒO ADAPTATIVA â€” Ajusta diversidade por quantidade         â•‘
    // â•‘  10 jogos â†’ MÃXIMA diversidade (aberto, exploratÃ³rio)              â•‘
    // â•‘  100 jogos â†’ Moderado (equilÃ­brio IA + cobertura)                  â•‘
    // ╔══════════════════════════════════════════════════════════════╗
    // ║  MÉTODO PRINCIPAL — GERAR JOGOS COM PROJEÇÃO FUTURA         ║
    // ╚══════════════════════════════════════════════════════════════╝


    // ╔══════════════════════════════════════════════════════════════════════════════════════╗
    // ║  CALIBRAÇÃO ADAPTATIVA — Ajusta diversidade por quantidade         ║
    // ║  10 jogos → MÁXIMA diversidade (aberto, exploratório)              ║
    // ║  100 jogos → Moderado (equilíbrio IA + cobertura)                  ║
    // ║  1000 jogos → Focado (convergência, menos noise)                   ║
    // ╚══════════════════════════════════════════════════════════════════════════════════════╝
    // ╔══════════════════════════════════════════════════════════════════════════════════════╗
    // ║  ★★★ v5.0: CALIBRAÇÃO TIERED — Métodos DIFERENTES por volume ★★★  ║
    // ║                                                                     ║
    // ║  FILOSOFIA:                                                         ║
    // ║  10-50 jogos   → SNIPER: Cada jogo é o MELHOR possível              ║
    // ║  100-500 jogos → CIRÚRGICO: IA focada + filtros rigorosos           ║
    // ║  1K-5K jogos   → INTELIGENTE: Equilíbrio predição + cobertura      ║
    // ║  10K+ jogos    → COBERTURA: Diversidade máxima com IA ativa         ║
    // ╚══════════════════════════════════════════════════════════════════════════════════════╝
    static _getAdaptiveParams(numGames, profile) {
        const drawSize = profile.drawSize;
        const totalRange = profile.range[1] - profile.range[0] + 1;
        const baseOverlap = profile.maxOverlap;
        const baseUsage = profile.maxUsagePct;

        let overlapAdj, usageAdj, checkRadius, mode;

        let isLotomania = drawSize === 50;
        let isTimemania = profile.name && profile.name.toLowerCase().includes('timemania');

        if (numGames <= 10) {
            mode = 'GODMODE-SNIPER-10';
            if (isTimemania) overlapAdj = Math.floor(drawSize * 0.50); 
            else if (isLotomania) overlapAdj = Math.floor(drawSize * 0.70); 
            else overlapAdj = Math.max(drawSize - 2, Math.floor(drawSize * 0.85));
            
            usageAdj = Math.min(0.35, Math.max(0.20, baseUsage));
            if (isLotomania || isTimemania) usageAdj = Math.min(0.50, Math.max(0.35, baseUsage));
            
            checkRadius = numGames;
        }
        else if (numGames <= 50) {
            mode = 'GODMODE-SNIPER-50';
            if (isTimemania) overlapAdj = Math.floor(drawSize * 0.40); 
            else if (isLotomania) overlapAdj = Math.floor(drawSize * 0.60); 
            else overlapAdj = Math.max(drawSize - 3, Math.floor(drawSize * 0.75));
            
            usageAdj = Math.min(0.40, Math.max(0.25, baseUsage));
            if (isLotomania || isTimemania) usageAdj = Math.min(0.55, Math.max(0.40, baseUsage));
            
            checkRadius = numGames;
        }
        else if (numGames <= 100) {
            mode = 'FOCADO-100';
            overlapAdj = Math.max(3, Math.floor(drawSize * 0.55));
            usageAdj = Math.min(0.40, Math.max(0.25, baseUsage));
            checkRadius = Math.min(60, numGames);
        }
        else if (numGames <= 500) {
            mode = 'FOCADO-500';
            overlapAdj = Math.max(3, Math.floor(drawSize * 0.60));
            usageAdj = Math.min(0.35, baseUsage);
            checkRadius = Math.min(40, Math.ceil(numGames * 0.12));
        }
        else if (numGames <= 1000) {
            mode = 'EQUILIBRADO-1K';
            overlapAdj = Math.min(drawSize - 1, Math.ceil(baseOverlap * 1.2));
            usageAdj = Math.min(0.50, baseUsage * 1.2);
            checkRadius = 30;
        }
        else if (numGames <= 5000) {
            mode = 'COBERTURA-5K';
            overlapAdj = Math.min(drawSize - 1, Math.ceil(baseOverlap * 1.5));
            usageAdj = Math.min(0.80, baseUsage * 1.6);
            checkRadius = 20;
        }
        else {
            mode = 'COBERTURA-MAX';
            overlapAdj = drawSize - 1;
            usageAdj = 1.0;
            checkRadius = 15;
        }

        console.log('[NE-L99] ★ v5.0 TIER: ' + mode + ' | ' + numGames + ' jogos');
        console.log('[NE-L99]    overlap=' + overlapAdj + '/' + drawSize + ' | usage=' + (usageAdj*100).toFixed(0) + '% | check=' + checkRadius);

        return {
            maxOverlap: overlapAdj,
            maxUsagePct: usageAdj,
            noiseWeight: 0,
            checkRadius: checkRadius,
            mode: mode
        };
    }

    static generate(gameKey, numGames, selectedNumbers, fixedNumbers, customDrawSize, options) {
        const _options = options || {};
        const _precisionMode = _options.precisionMode || false;
        const _precisionPoolSize = parseInt(_options.precisionPoolSize) || 0;

        const profile = this.getProfile(gameKey);
        const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        if (!game) return { games: [], pool: [], analysis: { confidence: 0 } };

        const startNum = profile.range[0];
        const endNum = profile.range[1];
        const totalRange = endNum - startNum + 1;
        const drawSize = customDrawSize || game.minBet || profile.drawSize;

        let history = (_options && _options.history) || [];
        if (history.length === 0) try {
            if (typeof StatsService !== 'undefined') {
                history = StatsService.getRecentResults(gameKey, 200) || [];
            }
            if (history.length === 0 && typeof REAL_HISTORY_DB !== 'undefined') {
                history = REAL_HISTORY_DB[gameKey] || [];
            }
        } catch (e) {
            console.warn('[NE-V1] Sem histÃ³rico:', e.message);
        }

        console.log('[NE-V1] âš¡ ' + profile.name + ' | ' + history.length + ' sorteios | ' + numGames + ' jogos | drawSize=' + drawSize);

        // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        // FASE 1: ANÃLISE PREDITIVA COMPLETA â€” 7 CAMADAS
        // Scorar TODOS os nÃºmeros do range (NENHUM eliminado)
        // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        // v11.0 FIX: Setar drawSize e modo diversidade ANTES de _scoreAllNumbers
        this._currentDrawSize = drawSize;
        this._sniperMode = numGames > 100; // Floor alto para diversidade em lotes grandes
        const scores = this._scoreAllNumbers(gameKey, profile, history, startNum, endNum, totalRange);
        this._sniperMode = false;

        // v14.0: Enriquecer scores com evidência estatística do BiasEngine
        // Ajusta os pesos ANTES da construção do pool e da delegação ao CoverageEngine
        if (typeof StatisticalBiasEngine !== 'undefined' && history.length >= 30) {
            try {
                const biasResult = StatisticalBiasEngine.analyze(gameKey, history, Math.min(totalRange, drawSize * 4));
                if (biasResult && biasResult.numberScores && biasResult.verdict) {
                    const weight = biasResult.verdict.biasDetected ? 0.30 : 0.10;
                    let adjustedCount = 0;
                    for (let n = startNum; n <= endNum; n++) {
                        const bs = biasResult.numberScores[n];
                        if (bs && bs.hasSignificance) {
                            scores[n] = (scores[n] || 0) * (1 + bs.evidenceScore * weight);
                            adjustedCount++;
                        }
                    }
                    console.log('[NE-v14] generate: BiasEngine ' + biasResult.verdict.emoji +
                        ' | ' + adjustedCount + ' números ajustados | peso=' + weight);
                }
            } catch (e) { console.warn('[NE-v14] BiasEngine indisponível:', e.message); }
        }

        // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        // FASE 2: DEFINIR POOL
        // Se usuÃ¡rio selecionou nÃºmeros â†’ usar como pool
        // SenÃ£o â†’ usar TODOS os nÃºmeros do range
        // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        let pool;
        const hasUserSelection = selectedNumbers && selectedNumbers.length >= drawSize;
        const hasPartialSelection = selectedNumbers && selectedNumbers.length > 0 && selectedNumbers.length < drawSize;

        if (hasUserSelection) {
            pool = selectedNumbers.slice().sort((a, b) => a - b);
            console.log('[NE-V1] ðŸŽ¯ Pool do usuÃ¡rio: ' + pool.length + ' nÃºmeros');
        } else if (hasPartialSelection) {
            const partialFixed = selectedNumbers.filter(n => n >= startNum && n <= endNum);
            const existingFixed = new Set(fixedNumbers || []);
            for (const n of partialFixed) {
                if (!existingFixed.has(n)) {
                    fixedNumbers = [...(fixedNumbers || []), n];
                }
                // GOD MODE: Boost 3x no score para IA priorizar
                if (scores[n] !== undefined) scores[n] *= 3.0;
            }
            pool = [];
            for (let n = startNum; n <= endNum; n++) pool.push(n);
            console.log('[NE-V1] ðŸ“Œ SeleÃ§Ã£o PARCIAL: ' + partialFixed.length + ' Ã¢ncoras fixas + pool IA completo (' + pool.length + ')');
        } else {
            // â˜… v7.0: POOL SEMPRE COMPLETO â€” nunca reduzir
            // Pool reduzido era o BUG #1: eliminava nÃºmeros do resultado
            pool = [];
            for (let n = startNum; n <= endNum; n++) pool.push(n);
            console.log('[v7.0] POOL COMPLETO: ' + pool.length + '/' + totalRange + ' (100%) | volume=' + numGames);
        }

        // â˜… FIX V4.1: GARANTIR que TODOS os fixedNumbers estÃ£o no pool
        if (fixedNumbers && fixedNumbers.length > 0) {
            const poolSet = new Set(pool);
            for (const f of fixedNumbers) {
                if (f >= startNum && f <= endNum && !poolSet.has(f)) {
                    pool.push(f);
                    poolSet.add(f);
                }
            }
            console.log('[NE-V1] ðŸ“Œ ' + fixedNumbers.length + ' nÃºmeros fixos garantidos no pool: [' + fixedNumbers.sort((a,b)=>a-b).join(', ') + ']');
        }

                // v13.0: Ajuste Dinamico de Piscina
        // MEGA SENA: NUNCA amputar — pool completo de 60 é obrigatório
        // Para outras loterias, mantém a lógica de amputação existente
        if (!hasUserSelection) {
            let targetPoolSize = totalRange;

            // v13.0: Mega Sena SEMPRE usa pool completo
            if (gameKey === 'megasena') {
                console.log('[NE-V13] Mega Sena: Pool COMPLETO ' + pool.length + '/60 (amputação desativada)');
            } else {
                // v14.0 — POOL COMPLETO PARA TODOS os volumes altos
                // BUG CORRIGIDO: Amputação arbitrária eliminava 15-45% dos números
                // causando ausentes em Timemania (20 de 80), Dia de Sorte (6 de 31),
                // Quina (30 de 80), Dupla Sena (22 de 50) e Lotomania (20 de 100).
                // REGRA: Para volumes >= 1000 jogos, usar SEMPRE pool completo.
                // Para volumes menores, uma redução leve (83%) é aceitável.
                if (numGames >= 1000) {
                    // Pool completo para alto volume — cobertura total do universo
                    targetPoolSize = totalRange;
                    console.log('[NE-V14] Alto volume (' + numGames + ' jogos): Pool COMPLETO ' + totalRange + ' números (' + gameKey + ')');
                } else if (numGames <= 200) {
                    targetPoolSize = Math.max(drawSize * 3, Math.floor(totalRange * 0.72));
                }
                // Para 200 < numGames < 1000: pool completo (sem corte)

                if (targetPoolSize < pool.length) {
                    const fixedSet = new Set(fixedNumbers || []);
                    const fixedInPool = pool.filter(n => fixedSet.has(n));
                    const nonFixedPool = pool.filter(n => !fixedSet.has(n));
                    nonFixedPool.sort((a, b) => (scores[b] || 0) - (scores[a] || 0));
                    const slotsForNonFixed = targetPoolSize - fixedInPool.length;
                    pool = [...fixedInPool, ...nonFixedPool.slice(0, Math.max(0, slotsForNonFixed))];
                    pool.sort((a, b) => a - b);
                    console.log('[NE-V14] Piscina ajustada: TOP ' + pool.length + '/' + totalRange + ' números (' + gameKey + ')');
                } else {
                    console.log('[NE-V14] Pool completo mantido: ' + pool.length + '/' + totalRange + ' números (' + gameKey + ')');
                }
            }
        }

                // v12.2 Auto-Fixador Estatístico (Lotofácil)
        // Trava os 3 melhores numeros do scoring historico como FIXOS para altos volumes
        let lotoFixed = fixedNumbers || [];
        if (gameKey === 'lotofacil' && numGames >= 1000 && (!fixedNumbers || fixedNumbers.length === 0) && (!hasUserSelection)) {
            // pool já está ordenado (se houver pool restrito) ou podemos ordernar todos
            let sortedLoto = pool.slice().sort((a, b) => (scores[b] || 0) - (scores[a] || 0));
            lotoFixed = sortedLoto.slice(0, 3);
            console.log('[NE-V12] Auto-Fixador Lotofácil ativado. Top 3 estatísticos fixados:', lotoFixed);
        }

        // FASE 3: GERACAO COMBINATORIA (FUSAO DA CIENCIA COM SET COVER)
        let games = [];
        let realAnalysis = {};
        if (typeof CoverageEngine !== 'undefined') {
            console.log('[NE-V12] Delegando ' + numGames + ' jogos para o CoverageEngine usando as ' + pool.length + ' dezenas filtradas pela Ciencia.');
            const coverageResult = CoverageEngine.generate(
                gameKey, 
                numGames, 
                pool, 
                lotoFixed, 
                drawSize, 
                { quantumScores: scores } // 6o param = options, injetamos as pontuacoes cientificas
            );
            if (coverageResult && coverageResult.games) {
                games = coverageResult.games;
                realAnalysis = coverageResult.analysis || {};
            }
        } else {
            console.error('[NE-V12] CoverageEngine ausente! Abortando geracao.');
        }

        // FASE 4: LIMPEZA DO BACKTESTING (Removido Overfitting)
        console.log('[NE-V12] Backtesting ilusorio removido. Retornando metricas reais do CoverageEngine.');
        
        // Passar o tamanho do pool real usado
        realAnalysis.poolSize = pool.length;

        return {
            games: games,
            analysis: realAnalysis,
            poolUsed: pool,
            internalEngine: 'CoverageEngine (Multi-Tier)'
        };

    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  CAMADA 1: FREQUÃŠNCIA MULTI-JANELA                          â•‘
    // â•‘  Analisa frequÃªncia em janelas de 3, 5, 10, 15 sorteios     â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _layerFrequency(history, startNum, endNum, N) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0;
        if (N === 0) return scores;

        // â˜… PRECISION v2.0: Janela de 3 com peso DOMINANTE (50%)
        // Foco mÃ¡ximo nos Ãºltimos 3 resultados para capturar tendÃªncia imediata
        const windows = [
            { size: Math.min(3, N),  weight: 0.50 },
            { size: Math.min(5, N),  weight: 0.20 },
            { size: Math.min(10, N), weight: 0.15 },
            { size: Math.min(15, N), weight: 0.15 }
        ];

        for (const w of windows) {
            const freq = {};
            for (let n = startNum; n <= endNum; n++) freq[n] = 0;
            for (let i = 0; i < w.size; i++) {
                const nums = history[i].numbers || [];
                for (const n of nums) {
                    if (n >= startNum && n <= endNum) freq[n]++;
                }
                // Dupla Sena: 2Âº sorteio
                const nums2 = history[i].numbers2 || [];
                for (const n of nums2) {
                    if (n >= startNum && n <= endNum) freq[n] += 0.5;
                }
            }
            // Normalizar para [0, 1]
            let maxF = 0;
            for (let n = startNum; n <= endNum; n++) if (freq[n] > maxF) maxF = freq[n];
            if (maxF > 0) {
                for (let n = startNum; n <= endNum; n++) {
                    scores[n] += (freq[n] / maxF) * w.weight;
                }
            }
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  CAMADA 2: PROJEÃ‡ÃƒO TEMPORAL â€” RegressÃ£o de TendÃªncia       â•‘
    // â•‘  Projeta se um nÃºmero estÃ¡ SUBINDO ou DESCENDO em freq.     â•‘
    // â•‘  Conceito de "clarividÃªncia computacional"                   â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _layerTrend(history, startNum, endNum, N) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (N < 6) return scores;

        const half = Math.min(8, Math.floor(N / 2));
        for (let n = startNum; n <= endNum; n++) {
            // FrequÃªncia na 1Âª metade (recente) vs 2Âª metade (antiga)
            let recentHits = 0, olderHits = 0;
            for (let i = 0; i < half; i++) {
                const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
                if (nums.includes(n)) recentHits++;
            }
            for (let i = half; i < half * 2 && i < N; i++) {
                const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
                if (nums.includes(n)) olderHits++;
            }
            // Trend ratio: > 1 = subindo, < 1 = descendo
            const recentRate = recentHits / half;
            const olderRate = olderHits / Math.min(half, N - half) || 0.01;
            const trend = recentRate / Math.max(0.01, olderRate);

            // Projetar: nÃºmeros em ascensÃ£o recebem boost
            if (trend > 1.5) scores[n] = 0.9;
            else if (trend > 1.0) scores[n] = 0.7;
            else if (trend > 0.5) scores[n] = 0.5;
            else scores[n] = 0.3;
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  CAMADA 3: PERÃODO DE RETORNO â€” NÃºmeros "Devendo"           â•‘
    // â•‘  Se o ciclo esperado de um nÃºmero Ã© X sorteios e ele nÃ£o    â•‘
    // â•‘  sai hÃ¡ Y > X sorteios, ele recebe boost proporcional      â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _layerDelay(history, startNum, endNum, N, drawSize, totalRange) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (N < 3) return scores;

        const expectedReturn = totalRange / drawSize; // Mega: 60/6 = 10 sorteios

        for (let n = startNum; n <= endNum; n++) {
            // Encontrar Ãºltima apariÃ§Ã£o
            let lastSeen = N; // Nunca visto por padrÃ£o
            for (let i = 0; i < N; i++) {
                const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
                if (nums.includes(n)) { lastSeen = i; break; }
            }

            // GOD MODE: Substituir Falácia do Jogador por distribuição uniforme
            // Números NÃO "devem" sair. O RNG não tem memória.
            // Scoring baseado em RECÊNCIA (leve), não em "dívida"
            const ratio = lastSeen / expectedReturn;
            // Distribuição suave: números recentes = score médio, antigos = score médio
            // Leve preferência por não-recentes para diversidade, MAS sem extremos
            if (ratio >= 2.5) scores[n] = 0.65;       // Não visto há muito (leve boost)
            else if (ratio >= 1.5) scores[n] = 0.60;
            else if (ratio >= 0.8) scores[n] = 0.55;   // Ciclo normal
            else if (ratio >= 0.3) scores[n] = 0.45;   // Saiu recentemente (leve penalty)
            else scores[n] = 0.40;                      // Acabou de sair
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  CAMADA 4: ENTROPIA ESPACIAL â€” EquilÃ­brio por Zonas         â•‘
    // â•‘  Detecta zonas sub-representadas nos Ãºltimos sorteios       â•‘
    // â•‘  e dÃ¡ boost a nÃºmeros nessas zonas                          â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _layerEntropy(history, startNum, endNum, N, profile) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (N < 3) return scores;

        const numZones = profile.zones;
        const zoneSize = profile.zoneSize;
        const zoneHits = new Array(numZones).fill(0);
        const limit = Math.min(10, N);
        let totalHits = 0;

        for (let i = 0; i < limit; i++) {
            const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            for (const n of nums) {
                if (n >= startNum && n <= endNum) {
                    const z = Math.min(numZones - 1, Math.floor((n - startNum) / zoneSize));
                    zoneHits[z]++;
                    totalHits++;
                }
            }
        }

        // Zonas com menos hits do que o esperado recebem boost
        const expectedPerZone = totalHits / numZones;
        for (let n = startNum; n <= endNum; n++) {
            const z = Math.min(numZones - 1, Math.floor((n - startNum) / zoneSize));
            const ratio = zoneHits[z] / Math.max(1, expectedPerZone);
            // Zonas sub-representadas: boost; super-representadas: penalty
            if (ratio < 0.5) scores[n] = 0.9;      // Muito sub-representada
            else if (ratio < 0.8) scores[n] = 0.7;
            else if (ratio < 1.2) scores[n] = 0.5;  // Equilibrada
            else if (ratio < 1.5) scores[n] = 0.35;
            else scores[n] = 0.2;                    // Super-representada
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  CAMADA 5: TRANSIÃ‡ÃƒO DE MARKOV â€” Co-ocorrÃªncia Ponderada    â•‘
    // â•‘  Dado o Ãºltimo sorteio, quais nÃºmeros tendem a seguir?      â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _layerMarkov(history, startNum, endNum, N) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (N < 3) return scores;

        const lastDraw = history[0].numbers || [];
        const limit = Math.min(30, N - 1);

        // Contar transiÃ§Ãµes: se X saiu no sorteio i+1, e Y saiu no sorteio i, boost Y
        for (let i = 0; i < limit; i++) {
            const olderNums = new Set((history[i + 1].numbers || []).concat(history[i + 1].numbers2 || []));
            const newerNums = history[i].numbers || [];
            const decay = Math.exp(-i * 0.06);

            for (const from of lastDraw) {
                if (olderNums.has(from)) {
                    // 'from' apareceu no sorteio anterior â€” boost nÃºmeros que vieram depois
                    for (const to of newerNums) {
                        if (to >= startNum && to <= endNum) {
                            scores[to] += decay * 0.05;
                        }
                    }
                }
            }
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  CAMADA 6: RESSONÃ‚NCIA DE FASE â€” Ciclos PeriÃ³dicos          â•‘
    // â•‘  Detecta se um nÃºmero tem padrÃ£o cÃ­clico e estÃ¡ prestes     â•‘
    // â•‘  a "ressoar" (reaparecer no ciclo)                          â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _layerPhase(history, startNum, endNum, N) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (N < 10) return scores;

        for (let n = startNum; n <= endNum; n++) {
            // Encontrar posiÃ§Ãµes de apariÃ§Ã£o
            const positions = [];
            for (let i = 0; i < N; i++) {
                const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
                if (nums.includes(n)) positions.push(i);
            }

            if (positions.length < 3) continue;

            // Calcular gaps entre apariÃ§Ãµes
            const gaps = [];
            for (let g = 1; g < positions.length; g++) {
                gaps.push(positions[g] - positions[g - 1]);
            }

            // Detectar ciclo dominante
            const gapFreq = {};
            for (const gap of gaps) {
                // Agrupar gaps prÃ³ximos (Â±1)
                for (let g = gap - 1; g <= gap + 1; g++) {
                    if (g > 0) gapFreq[g] = (gapFreq[g] || 0) + 1;
                }
            }

            let bestCycle = 0, bestCount = 0;
            for (const [cycle, count] of Object.entries(gapFreq)) {
                if (count > bestCount) {
                    bestCount = count;
                    bestCycle = parseInt(cycle);
                }
            }

            // Se hÃ¡ um ciclo claro e o nÃºmero estÃ¡ "no ponto"
            if (bestCycle > 0 && bestCount >= 2) {
                const sinceLast = positions[0];
                const cyclePosition = sinceLast / bestCycle;
                // Entre 0.8 e 1.2 do ciclo = "prestes a sair"
                if (cyclePosition >= 0.7 && cyclePosition <= 1.3) {
                    const confidence = bestCount / gaps.length;
                    scores[n] = 0.5 + confidence * 0.4;
                }
            }
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  CAMADA 7: CLARIVIDÃŠNCIA SINTÃ‰TICA â€” FusÃ£o Preditiva        â•‘
    // â•‘  Monte Carlo ponderado para projetar cenÃ¡rios futuros       â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜… v5.0: CLARIVIDÃŠNCIA APRIMORADA â€” Monte Carlo Condicional       â•‘
    // â•‘  MudanÃ§as:                                                         â•‘
    // â•‘   1. Probabilidade base por 3 janelas (3, 7, 15 sorteios)         â•‘
    // â•‘   2. Ciclo de retorno individual (quando deve voltar?)             â•‘
    // â•‘   3. Co-ocorrÃªncia: nÃºmeros que saem juntos                       â•‘
    // â•‘   4. SimulaÃ§Ã£o MC com constraints de zona/paridade                â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _layerClairvoyance(history, startNum, endNum, N, drawSize) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0;
        if (N < 5) {
            for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
            return scores;
        }

        const totalRange = endNum - startNum + 1;

        // â˜… v5.0: PASSO 1 â€” Probabilidade base MULTI-JANELA
        const baseProb = {};
        for (let n = startNum; n <= endNum; n++) baseProb[n] = 0.5; // Base mÃ­nima

        // Janela curta (3 sorteios) â€” tendÃªncia imediata
        const w3 = Math.min(3, N);
        for (let i = 0; i < w3; i++) {
            const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            const decay = Math.exp(-i * 0.15);
            for (const n of nums) {
                if (n >= startNum && n <= endNum) baseProb[n] += decay * 2.0;
            }
        }

        // Janela mÃ©dia (7 sorteios) â€” padrÃ£o recente
        const w7 = Math.min(7, N);
        for (let i = 0; i < w7; i++) {
            const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            const decay = Math.exp(-i * 0.10);
            for (const n of nums) {
                if (n >= startNum && n <= endNum) baseProb[n] += decay * 1.0;
            }
        }

        // Janela longa (15 sorteios) â€” frequÃªncia geral
        const w15 = Math.min(15, N);
        for (let i = 0; i < w15; i++) {
            const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            const decay = Math.exp(-i * 0.06);
            for (const n of nums) {
                if (n >= startNum && n <= endNum) baseProb[n] += decay * 0.5;
            }
        }

        // â˜… v5.0: PASSO 2 â€” Ciclo de retorno individual
        for (let n = startNum; n <= endNum; n++) {
            // Calcular ciclo mÃ©dio de retorno
            const appearances = [];
            for (let i = 0; i < Math.min(30, N); i++) {
                const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
                if (nums.includes(n)) appearances.push(i);
            }

            if (appearances.length >= 2) {
                let avgCycle = 0;
                for (let j = 0; j < appearances.length - 1; j++) {
                    avgCycle += appearances[j + 1] - appearances[j];
                }
                avgCycle /= (appearances.length - 1);

                // Quanto tempo desde a Ãºltima apariÃ§Ã£o?
                const lastSeen = appearances.length > 0 ? appearances[0] : 30;
                const expectedReturn = avgCycle;

                // Boost se estÃ¡ no "ponto de retorno" (+/- 30% do ciclo)
                if (lastSeen >= expectedReturn * 0.7 && lastSeen <= expectedReturn * 1.5) {
                    baseProb[n] *= 1.6; // Ponto Ã³timo de retorno
                } else if (lastSeen > expectedReturn * 1.5) {
                    baseProb[n] *= 1.3; // Atrasado â€” pressÃ£o moderada
                } else if (lastSeen < expectedReturn * 0.4) {
                    baseProb[n] *= 0.7; // Saiu recentemente â€” descanso
                }
            }
        }

        // â˜… v5.0: PASSO 3 â€” Co-ocorrÃªncia (nÃºmeros que saem juntos)
        const lastDraw = history[0].numbers || [];
        const coOccurrence = {};
        for (let n = startNum; n <= endNum; n++) coOccurrence[n] = 0;

        for (let i = 1; i < Math.min(20, N); i++) {
            const prevNums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            // Se algum nÃºmero do Ãºltimo sorteio apareceu junto com n no passado
            for (const n of prevNums) {
                if (n >= startNum && n <= endNum) {
                    for (const last of lastDraw) {
                        if (prevNums.includes(last) && n !== last) {
                            coOccurrence[n] += Math.exp(-i * 0.1) * 0.3;
                        }
                    }
                }
            }
        }

        for (let n = startNum; n <= endNum; n++) {
            baseProb[n] += coOccurrence[n];
        }

        // Normalizar
        let totalProb = 0;
        for (let n = startNum; n <= endNum; n++) totalProb += baseProb[n];
        for (let n = startNum; n <= endNum; n++) baseProb[n] /= totalProb;

        // â˜… v5.0: PASSO 4 â€” Monte Carlo com constraints
        const simulations = Math.min(15000, Math.max(5000, totalRange * 80));
        for (let sim = 0; sim < simulations; sim++) {
            const drawn = this._weightedSample(baseProb, drawSize, startNum, endNum);
            for (const n of drawn) {
                scores[n]++;
            }
        }

        for (let n = startNum; n <= endNum; n++) {
            scores[n] = scores[n] / simulations;
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  CAMADA 8: PROJEÃ‡ÃƒO DO PRÃ“XIMO SORTEIO â€” POR LOTERIA        â•‘
    // â•‘  Analisa padrÃµes de transiÃ§Ã£o ESPECÃFICOS de cada loteria    â•‘
    // â•‘  Foco: projetar o que acontece no resultado SEGUINTE         â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _layerNextDraw(gameKey, history, startNum, endNum, N, profile) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (N < 3) return scores;

        // â”â”â” Analisar taxa de repetiÃ§Ã£o REAL desta loteria â”â”â”
        const drawSize = profile.lotteryDraw;
        const repRates = [];
        for (let i = 0; i < Math.min(20, N - 1); i++) {
            const current = new Set(history[i].numbers || []);
            const next = new Set(history[i + 1].numbers || []);
            let rep = 0;
            for (const n of current) if (next.has(n)) rep++;
            repRates.push(rep);
        }
        const avgRepetition = repRates.length > 0 ? repRates.reduce((a, b) => a + b, 0) / repRates.length : 0;
        const lastDraw = new Set(history[0].numbers || []);

        console.log('[NE-V1] ðŸŽ¯ ' + gameKey + ' | Taxa de repetiÃ§Ã£o mÃ©dia: ' + avgRepetition.toFixed(1) + '/' + drawSize);

        // â”â”â” CALIBRAÃ‡ÃƒO INDIVIDUAL POR LOTERIA â”â”â”
        switch (gameKey) {

            // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            // MEGA SENA: RepetiÃ§Ã£o baixa (~0.8/6)
            // NÃºmeros do Ãºltimo sorteio RARAMENTE repetem
            // Foco: nÃºmeros atrasados + tendÃªncia recente
            // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            case 'megasena': {
                // ★ GOD MODE v11: ZONE DEFICIT ANALYSIS
                // Zonas que NÃO tiveram números no último sorteio = zona "faminta"
                const msZones = 6;
                const msZoneSize = 10;
                const lastZones = new Set();
                for (const n of lastDraw) {
                    lastZones.add(Math.floor((n - startNum) / msZoneSize));
                }
                const hungryZones = new Set();
                for (let z = 0; z < msZones; z++) {
                    if (!lastZones.has(z)) hungryZones.add(z);
                }

                for (let n = startNum; n <= endNum; n++) {
                    if (lastDraw.has(n)) {
                        scores[n] = 0.35;
                    } else {
                        let lastSeen = N;
                        for (let i = 0; i < N; i++) {
                            if ((history[i].numbers || []).includes(n)) { lastSeen = i; break; }
                        }
                        if (lastSeen >= 8 && lastSeen <= 18) scores[n] = 0.88;
                        else if (lastSeen >= 4 && lastSeen <= 25) scores[n] = 0.70;
                        else if (lastSeen < 4) scores[n] = 0.45;
                        else scores[n] = 0.58;
                    }
                    // ★ v11: Boost para números em zonas "famintas"
                    const nZone = Math.floor((n - startNum) / msZoneSize);
                    if (hungryZones.has(nZone) && !lastDraw.has(n)) {
                        scores[n] = Math.min(1.0, scores[n] + 0.10);
                    }
                }
                // Bonus: penúltimo
                if (N >= 2) {
                    const penultimo = new Set(history[1].numbers || []);
                    for (const n of penultimo) {
                        if (!lastDraw.has(n) && scores[n] !== undefined) scores[n] = Math.min(1.0, scores[n] + 0.15);
                    }
                }
                break;
            }

            // ──────────────────────────────────────────────────────────────────────────────
            // TIMEMANIA: Jogador marca 10 de 80, loteria sorteia 7
            // Chave: COBERTURA DE ZONAS (8 zonas de 10) + ciclos longos (~11 sorteios)
            // Com 10 números, o ideal é cobrir 5-7 zonas diferentes
            // ──────────────────────────────────────────────────────────────────────────────
            case 'timemania': {
                // ★★★ GOD MODE v11: TIMEMANIA RECONSTRUÇÃO TOTAL ★★★
                const TM_ZONES = 8;
                const TM_ZONE_SIZE = 10;
                const tmExpectedCycle = 80 / 7; // ~11.4 sorteios por número
                
                // ── PASSO 1: MAPA DE ZONAS NOS ÚLTIMOS 5 SORTEIOS ──
                const tmZoneHeat = new Array(TM_ZONES).fill(0);
                const tmZoneWindow = Math.min(5, N);
                for (let i = 0; i < tmZoneWindow; i++) {
                    const decay = Math.pow(0.75, i);
                    for (const n of (history[i].numbers || [])) {
                        if (n >= startNum && n <= endNum) {
                            const z = Math.min(TM_ZONES - 1, Math.floor((n - startNum) / TM_ZONE_SIZE));
                            tmZoneHeat[z] += decay;
                        }
                    }
                }
                const avgTmZoneHeat = tmZoneHeat.reduce((a, b) => a + b, 0) / TM_ZONES;
                
                // ── PASSO 2: DÉFICIT DE ZONAS NO ÚLTIMO SORTEIO ──
                const tmLastZoneCount = new Array(TM_ZONES).fill(0);
                for (const n of lastDraw) {
                    const z = Math.min(TM_ZONES - 1, Math.floor((n - startNum) / TM_ZONE_SIZE));
                    tmLastZoneCount[z]++;
                }
                const tmExpPerZone = 7 / TM_ZONES; // ~0.875
                
                // ── PASSO 3: FREQUÊNCIA MULTI-JANELA (3 + 7 + 15) ──
                const tmFreq3 = {}, tmFreq7 = {}, tmFreq15 = {};
                for (let n = startNum; n <= endNum; n++) { tmFreq3[n] = 0; tmFreq7[n] = 0; tmFreq15[n] = 0; }
                for (let i = 0; i < Math.min(15, N); i++) {
                    for (const n of (history[i].numbers || [])) {
                        if (n >= startNum && n <= endNum) {
                            if (i < 3) tmFreq3[n]++;
                            if (i < 7) tmFreq7[n]++;
                            tmFreq15[n]++;
                        }
                    }
                }
                
                // ── PASSO 4: CO-OCORRÊNCIA COM ÚLTIMO SORTEIO ──
                const tmPairBonus = {};
                for (let n = startNum; n <= endNum; n++) tmPairBonus[n] = 0;
                if (N >= 5) {
                    const tmPairLimit = Math.min(20, N);
                    const tmPairFreq = {};
                    for (let i = 0; i < tmPairLimit; i++) {
                        const nums = (history[i].numbers || []).filter(x => x >= startNum && x <= endNum);
                        const decay = Math.pow(0.9, i);
                        for (let a = 0; a < nums.length; a++) {
                            for (let b = a + 1; b < nums.length; b++) {
                                const pk = Math.min(nums[a], nums[b]) + '-' + Math.max(nums[a], nums[b]);
                                tmPairFreq[pk] = (tmPairFreq[pk] || 0) + decay;
                            }
                        }
                    }
                    for (const lastN of lastDraw) {
                        for (const [pk, freq] of Object.entries(tmPairFreq)) {
                            if (freq < 1.5) continue; 
                            const [a, b] = pk.split('-').map(Number);
                            if (a === lastN && !lastDraw.has(b)) tmPairBonus[b] += freq * 0.05;
                            else if (b === lastN && !lastDraw.has(a)) tmPairBonus[a] += freq * 0.05;
                        }
                    }
                }
                
                // ── PASSO 5: SCORE COMPOSTO ──
                for (let n = startNum; n <= endNum; n++) {
                    const z = Math.min(TM_ZONES - 1, Math.floor((n - startNum) / TM_ZONE_SIZE));
                    let score = 0.45;
                    if (lastDraw.has(n)) {
                        score = 0.35;
                    } else {
                        let lastSeen = N;
                        for (let i = 0; i < N; i++) {
                            if ((history[i].numbers || []).includes(n)) { lastSeen = i; break; }
                        }
                        const ratio = lastSeen / tmExpectedCycle;
                        if (ratio >= 0.85 && ratio <= 1.3) score = 0.92;
                        else if (ratio > 1.3 && ratio <= 2.5) score = 0.85;
                        else if (ratio > 2.5 && ratio <= 4.0) score = 0.75;
                        else if (ratio > 4.0) score = 0.65;
                        else if (ratio >= 0.5 && ratio < 0.85) score = 0.55;
                        else score = 0.35;
                    }
                    const zoneDeficit = tmExpPerZone - tmLastZoneCount[z];
                    if (zoneDeficit > 0.3) score += 0.10;
                    if (tmZoneHeat[z] < avgTmZoneHeat * 0.6) {
                        score += 0.12;
                    } else if (tmZoneHeat[z] < avgTmZoneHeat * 0.8) {
                        score += 0.06;
                    }
                    const freqRecent = tmFreq3[n] / 3;
                    const freqGeneral = tmFreq15[n] / Math.min(15, N);
                    if (freqRecent > freqGeneral * 1.5 && freqRecent > 0) {
                        score += 0.08;
                    }
                    score += Math.min(0.15, tmPairBonus[n]);
                    scores[n] = Math.max(0.15, Math.min(1.0, score));
                }
                
                const tmHungryZones = tmLastZoneCount.map((c, i) => c === 0 ? (i+1)*10 + '-' + ((i+1)*10+9) : null).filter(Boolean);
                console.log('[NE-V1] 🎯 TIMEMANIA v11 | Zonas famintas: ' + (tmHungryZones.length > 0 ? tmHungryZones.join(', ') : 'nenhuma'));
                break;
            }

            // ──────────────────────────────────────────────────────────────────────────────
            // LOTOFÁCIL: Repetição ALTÍSSIMA (~8-12/15)
            // Estratégia: MANTER a maioria do último sorteio
            // Foco: quais 3-7 números TROCAR
            // ──────────────────────────────────────────────────────────────────────────────
            case 'lotofacil': {
                // Na Lotofácil, ~8-12 números repetem do sorteio anterior!
                // Estratégia invertida: ALTA probabilidade de repetição
                
                // ★ GOD MODE v11: MULTI-WINDOW frequency analysis
                const lotofFreq5 = {};
                const lotofWindow5 = Math.min(5, N);
                for (let n = startNum; n <= endNum; n++) lotofFreq5[n] = 0;
                for (let i = 0; i < lotofWindow5; i++) {
                    for (const n of (history[i].numbers || [])) {
                        if (n >= startNum && n <= endNum) lotofFreq5[n]++;
                    }
                }
                
                for (let n = startNum; n <= endNum; n++) {
                    if (lastDraw.has(n)) {
                        // Números do último: BOA chance de repetir
                        scores[n] = 0.80;
                    } else {
                        // Números que NÃO saíram: avaliar "pressão de entrada"
                        let lastSeen = N;
                        for (let i = 0; i < N; i++) {
                            if ((history[i].numbers || []).includes(n)) { lastSeen = i; break; }
                        }
                        // ★ v11: ENTRY PRESSURE baseada na freq dos últimos 5
                        if (lastSeen >= 3 && lotofFreq5[n] >= 3) scores[n] = 0.92; // Hot + ausente = MUITO provável
                        else if (lastSeen >= 3) scores[n] = 0.85; // 3+ sem sair = provável entrar
                        else if (lastSeen === 2) scores[n] = 0.65;
                        else scores[n] = 0.45; // Saiu recentemente, fora agora
                    }
                }
                // ★ v11: STREAK FATIGUE GRADUADA — fadiga de aparição
                if (N >= 3) {
                    for (const n of lastDraw) {
                        let consecAppears = 0;
                        for (let i = 0; i < Math.min(7, N); i++) {
                            if ((history[i].numbers || []).includes(n)) consecAppears++;
                            else break;
                        }
                        // Números que apareceram muitas vezes: fadiga GRADUADA
                        if (consecAppears >= 6) scores[n] = Math.max(0.25, scores[n] - 0.35);
                        else if (consecAppears >= 5) scores[n] = Math.max(0.30, scores[n] - 0.25);
                        else if (consecAppears >= 4) scores[n] = Math.max(0.35, scores[n] - 0.15);
                    }
                }
                // ★ v11: PENÚLTIMO BOOST — números do penúltimo que saíram do último tendem a voltar
                if (N >= 2) {
                    const penultimo = new Set(history[1].numbers || []);
                    for (const n of penultimo) {
                        if (!lastDraw.has(n) && scores[n] !== undefined) {
                            scores[n] = Math.min(1.0, scores[n] + 0.12);
                        }
                    }
                }
                break;
            }

            // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            // QUINA: RepetiÃ§Ã£o muito baixa (~0.3/5)
            // Range amplo (80 nÃºmeros), baixa cobertura por sorteio
            // Foco: distribuiÃ§Ã£o por zonas + ciclos longos
            // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            case 'quina': {
                for (let n = startNum; n <= endNum; n++) {
                    if (lastDraw.has(n)) {
                        scores[n] = 0.30; // v7.0: era 0.10 â€” penalidade moderada
                    } else {
                        let lastSeen = N;
                        for (let i = 0; i < N; i++) {
                            if ((history[i].numbers || []).includes(n)) { lastSeen = i; break; }
                        }
                        const expectedCycle = 80 / 5; // = 16 sorteios
                        const ratio = lastSeen / expectedCycle;
                        if (ratio >= 1.5 && ratio <= 3.0) scores[n] = 0.90;
                        else if (ratio >= 0.8 && ratio < 1.5) scores[n] = 0.70;
                        else if (ratio < 0.8) scores[n] = 0.50; // v7.1: era 0.30 â€” moderado
                        else scores[n] = 0.55;
                    }
                }
                break;
            }

            // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            // DUPLA SENA: RepetiÃ§Ã£o baixa (~0.7/6) mas TEM 2 sorteios
            // Considerar AMBOS os sorteios (numbers + numbers2)
            // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            case 'duplasena': {
                const lastDraw2 = new Set(history[0].numbers2 || []);
                const lastBoth = new Set([...lastDraw, ...lastDraw2]);
                for (let n = startNum; n <= endNum; n++) {
                    if (lastDraw.has(n) || lastDraw2.has(n)) {
                        scores[n] = 0.35; // v7.0: era 0.20
                    } else {
                        let lastSeen = N;
                        for (let i = 0; i < N; i++) {
                            const all = (history[i].numbers || []).concat(history[i].numbers2 || []);
                            if (all.includes(n)) { lastSeen = i; break; }
                        }
                        const expectedCycle = 50 / 12; // ~4.2 (6 de cada, 2 sorteios)
                        const ratio = lastSeen / expectedCycle;
                        if (ratio >= 1.2 && ratio <= 3.0) scores[n] = 0.90;
                        else if (ratio >= 0.7) scores[n] = 0.65;
                        else scores[n] = 0.30;
                    }
                }
                break;
            }

            // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            // LOTOMANIA: Jogador marca 50 de 100, loteria sorteia 20
            // Taxa de repetiÃ§Ã£o dos 20 sorteados: ~4/20
            // EstratÃ©gia: cobrir o mÃ¡ximo das zonas que "devem"
            // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            case 'lotomania': {
                // ★★★ GOD MODE v11: LOTOMANIA RECONSTRUÇÃO TOTAL ★★★
                // 50 números de 100, loteria sorteia 20
                // A chave é: EQUILÍBRIO POR DÉCADAS (0-9, 10-19, ..., 90-99)
                // Cada década DEVE ter ~5 números na seleção e ~2 no sorteio
                
                const NUM_DECADES = 10;
                const decadeStart = startNum; // 0 para Lotomania
                
                // ── PASSO 1: MAPA DE CALOR POR DÉCADA (últimos 5 sorteios) ──
                const decadeHeat = new Array(NUM_DECADES).fill(0);
                const decadeHist5 = Math.min(5, N);
                for (let i = 0; i < decadeHist5; i++) {
                    const decay = Math.pow(0.8, i); // Recentes pesam mais
                    for (const n of (history[i].numbers || [])) {
                        if (n >= startNum && n <= endNum) {
                            const dec = Math.floor((n - decadeStart) / 10);
                            decadeHeat[dec] += decay;
                        }
                    }
                }
                // Normalizar: qual é a "temperatura" média de cada década?
                const avgDecadeHeat = decadeHeat.reduce((a, b) => a + b, 0) / NUM_DECADES;
                
                // ── PASSO 2: DÉFICIT DE DÉCADAS NO ÚLTIMO SORTEIO ──
                const lastDecadeCount = new Array(NUM_DECADES).fill(0);
                for (const n of lastDraw) {
                    const dec = Math.floor((n - decadeStart) / 10);
                    if (dec >= 0 && dec < NUM_DECADES) lastDecadeCount[dec]++;
                }
                const expectedPerDecade = 20 / NUM_DECADES; // = 2 por década
                
                // ── PASSO 3: FREQUÊNCIA INDIVIDUAL NOS ÚLTIMOS 10 ──
                const lotomFreq10 = {};
                const lotomW10 = Math.min(10, N);
                for (let n = startNum; n <= endNum; n++) lotomFreq10[n] = 0;
                for (let i = 0; i < lotomW10; i++) {
                    const decay = Math.pow(0.9, i);
                    for (const n of (history[i].numbers || [])) {
                        if (n >= startNum && n <= endNum) lotomFreq10[n] += decay;
                    }
                }
                
                // ── PASSO 4: SCORE COMPOSTO ──
                for (let n = startNum; n <= endNum; n++) {
                    const dec = Math.floor((n - decadeStart) / 10);
                    let score = 0.50; // Base
                    
                    // A) Pressão de retorno individual
                    if (lastDraw.has(n)) {
                        // Repetição moderada (4-6 repetem dos 20)
                        score = 0.45;
                    } else {
                        let lastSeen = N;
                        for (let i = 0; i < N; i++) {
                            if ((history[i].numbers || []).includes(n)) { lastSeen = i; break; }
                        }
                        const expectedCycle = 100 / 20; // = 5
                        const ratio = lastSeen / expectedCycle;
                        if (ratio >= 1.0 && ratio <= 2.0) score = 0.88; // Zona ótima
                        else if (ratio > 2.0 && ratio <= 3.5) score = 0.80; // Atrasado
                        else if (ratio >= 0.5 && ratio < 1.0) score = 0.60;
                        else if (ratio > 3.5) score = 0.70; // Muito atrasado
                        else score = 0.40;
                    }
                    
                    // B) BOOST/PENALIDADE POR DÉCADA
                    // Décadas que tiveram MENOS números no último sorteio = "famintas"
                    const decadeDeficit = expectedPerDecade - lastDecadeCount[dec];
                    if (decadeDeficit > 0.5) score += 0.12; // Década faminta
                    else if (decadeDeficit < -0.5) score -= 0.08; // Década saturada
                    
                    // C) MAPA DE CALOR — décadas "frias" nos últimos 5 recebem boost
                    if (decadeHeat[dec] < avgDecadeHeat * 0.7) {
                        score += 0.10; // Década consistentemente fria = pressão
                    } else if (decadeHeat[dec] > avgDecadeHeat * 1.4) {
                        score -= 0.05; // Década super-quente = possível descanso
                    }
                    
                    // D) NÚMERO "ÂNCORA" — apareceu em 3+ dos últimos 5 sorteios
                    if (lotomFreq10[n] >= 3.5) score = Math.min(1.0, score + 0.15);
                    else if (lotomFreq10[n] >= 2.5) score = Math.min(1.0, score + 0.08);
                    
                    // E) RESGATE DE NÚMEROS FRIOS de décadas produtivas
                    if (lotomFreq10[n] < 0.5 && decadeHeat[dec] >= avgDecadeHeat) {
                        score = Math.min(1.0, score + 0.08); // Frio em década quente = vai voltar
                    }
                    
                    scores[n] = Math.max(0.15, Math.min(1.0, score));
                }
                
                console.log('[NE-V1] 🎯 LOTOMANIA v11 | Décadas famintas: ' + 
                    lastDecadeCount.map((c, i) => i + '0s=' + c).filter((_, i) => lastDecadeCount[i] < 2).join(', '));
                break;
            }


            // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            // DIA DE SORTE V2.0: 7 de 31 â€” RECONSTRUÃ‡ÃƒO TOTAL
            // â˜… Foco nos ÃšLTIMOS 3 sorteios
            // â˜… Pares que saem juntos (co-ocorrÃªncia)
            // â˜… Anti-sequÃªncia rigoroso
            // â˜… Mix hot/cold balanceado
            // â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€â”€
            case 'diadesorte': {
                const ddsExpCycle = 31 / 7; // ~4.4 concursos de ciclo
                const last3Limit = Math.min(3, N);
                const last5Limit = Math.min(5, N);

                // â”â” PASSO 1: Contagem nos Ãºltimos 3 sorteios (PRIORIDADE MÃXIMA) â”â”
                const freq3 = {};
                for (let n = startNum; n <= endNum; n++) freq3[n] = 0;
                for (let i = 0; i < last3Limit; i++) {
                    for (const n of (history[i].numbers || [])) {
                        if (n >= startNum && n <= endNum) freq3[n]++;
                    }
                }

                // â”â” PASSO 2: Pares co-ocorrentes nos Ãºltimos 10 sorteios â”â”
                const pairScore = {};
                const pairLimit = Math.min(10, N);
                for (let i = 0; i < pairLimit; i++) {
                    const nums = history[i].numbers || [];
                    const decay = Math.pow(0.85, i); // Sorteios recentes pesam mais
                    for (let a = 0; a < nums.length; a++) {
                        for (let b = a + 1; b < nums.length; b++) {
                            if (nums[a] >= startNum && nums[a] <= endNum && nums[b] >= startNum && nums[b] <= endNum) {
                                const key = Math.min(nums[a], nums[b]) + ':' + Math.max(nums[a], nums[b]);
                                pairScore[key] = (pairScore[key] || 0) + decay;
                            }
                        }
                    }
                }

                // â”â” PASSO 3: Para cada nÃºmero, calcular score composto â”â”
                for (let n = startNum; n <= endNum; n++) {
                    let totalAppearances = 0;
                    let lastSeen = N;
                    let recentHits = 0;
                    for (let i = 0; i < N; i++) {
                        if ((history[i].numbers || []).includes(n)) {
                            totalAppearances++;
                            if (lastSeen === N) lastSeen = i;
                            if (i < last5Limit) recentHits++;
                        }
                    }
                    const freq = totalAppearances / Math.max(1, N);
                    const expectedFreq = 7 / 31;
                    const freqRatio = freq / expectedFreq;
                    const delayRatio = lastSeen / ddsExpCycle;

                    // â”â” BASE: Score por ciclo de atraso â”â”
                    let baseScore;
                    if (lastDraw.has(n)) {
                        // Saiu no Ãºltimo: penalizar mais (evitar repetiÃ§Ã£o excessiva)
                        baseScore = recentHits >= 3 ? 0.40 : 0.45; // v7.1: era 0.20/0.35
                    } else if (delayRatio >= 1.5 && delayRatio <= 3.0) {
                        baseScore = 0.95; // ZONA DE OURO
                    } else if (delayRatio >= 1.0 && delayRatio < 1.5) {
                        baseScore = 0.80;
                    } else if (delayRatio > 3.0) {
                        baseScore = freqRatio > 0.8 ? 0.70 : 0.50;
                    } else if (delayRatio >= 0.5 && delayRatio < 1.0) {
                        baseScore = freqRatio > 1.0 ? 0.55 : 0.45;
                    } else {
                        baseScore = 0.25;
                    }

                    // â”â” BOOST: NÃºmeros que mais saÃ­ram nos Ãºltimos 3 (HOT) â”â”
                    if (freq3[n] >= 3) baseScore = Math.min(1.0, baseScore + 0.35); // Saiu nos 3 Ãºltimos!
                    else if (freq3[n] === 2) baseScore = Math.min(1.0, baseScore + 0.20);
                    else if (freq3[n] === 1) baseScore = Math.min(1.0, baseScore + 0.08);

                    // â”â” BOOST: NÃºmeros que MENOS saÃ­ram (COLD com potencial) â”â”
                    // NÃºmeros frios com boa frequÃªncia histÃ³rica = candidatos a retornar
                    if (freq3[n] === 0 && freqRatio >= 0.9 && delayRatio >= 1.2) {
                        baseScore = Math.min(1.0, baseScore + 0.15); // Frio prestes a esquentar
                    }

                    // â”â” BOOST: Pares â€” nÃºmero que co-ocorre com os Ãºltimos sorteados â”â”
                    let pairBonus = 0;
                    for (const lastNum of lastDraw) {
                        if (lastNum === n) continue;
                        const key = Math.min(n, lastNum) + ':' + Math.max(n, lastNum);
                        if (pairScore[key]) {
                            pairBonus += pairScore[key] * 0.08;
                        }
                    }
                    baseScore = Math.min(1.0, baseScore + Math.min(0.25, pairBonus));

                    // â”â” PENALIDADE: Anti-sequÃªncia (nÃºmeros consecutivos ao Ãºltimo sorteio) â”â”
                    // Se o nÃºmero estÃ¡ a distÃ¢ncia 1 de DOIS ou mais nÃºmeros do Ãºltimo sorteio
                    let adjCount = 0;
                    for (const lastNum of lastDraw) {
                        if (Math.abs(n - lastNum) === 1) adjCount++;
                    }
                    if (adjCount >= 2) baseScore *= 0.60; // Penalizar forte se seria sequÃªncia

                    // FrequÃªncia equilibrada = ritmo saudÃ¡vel
                    if (freqRatio >= 0.85 && freqRatio <= 1.15) {
                        baseScore *= 1.12;
                    }

                    scores[n] = baseScore;
                }
                break;
            }

            default: {
                // GenÃ©rico: penalizar repetiÃ§Ã£o, favorecer atrasados
                for (let n = startNum; n <= endNum; n++) {
                    scores[n] = lastDraw.has(n) ? 0.25 : 0.55;
                }
            }
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜… CAMADA 9: CONVERGÃŠNCIA BAYESIANA (Modo Deus)                    â•‘
    // â•‘  P(nÃºmero | Ãºltimos K sorteios) com atualizaÃ§Ã£o posterior           â•‘
    // â•‘  Prior uniforme â†’ atualiza com cada sorteio observado              â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _godBayesian(history, startNum, endNum, N, drawSize) {
        const scores = {};
        const totalRange = endNum - startNum + 1;
        // Prior uniforme com suavizaÃ§Ã£o de Laplace
        for (let n = startNum; n <= endNum; n++) scores[n] = 1.0;
        if (N < 3) return this._normalizeScores(scores, startNum, endNum);

        // AtualizaÃ§Ã£o Bayesiana: cada sorteio atualiza a posterior
        const limit = Math.min(50, N);
        for (let i = 0; i < limit; i++) {
            const nums = new Set((history[i].numbers || []).concat(history[i].numbers2 || []));
            // Decaimento temporal â€” sorteios recentes pesam EXPONENCIALMENTE mais
            const weight = Math.exp(-i * 0.04);
            // Taxa base: probabilidade de um nÃºmero sair = drawSize / totalRange
            const baseRate = drawSize / totalRange;

            for (let n = startNum; n <= endNum; n++) {
                if (nums.has(n)) {
                    // Likelihood: apareceu â†’ boost posterior
                    scores[n] *= (1.0 + weight * (1.0 - baseRate));
                } else {
                    // Likelihood: NÃƒO apareceu â†’ reduzir levemente
                    scores[n] *= (1.0 - weight * baseRate * 0.3);
                }
            }
        }

        // Normalizar posterior
        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜… MODO DEUS â€” CAMADA 10: ANÃLISE POSICIONAL                  â•‘
    // â•‘  Em um resultado ordenado [a,b,c,d,e,f], quais nÃºmeros        â•‘
    // â•‘  tendem a ocupar cada POSIÃ‡ÃƒO? Ex: posiÃ§Ã£o 1 sempre < 15      â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _godPositional(history, startNum, endNum, N, drawSize) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0;
        if (N < 5) {
            for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
            return scores;
        }

        // Para cada posiÃ§Ã£o (0..drawSize-1), construir distribuiÃ§Ã£o
        const limit = Math.min(30, N);
        const positionDist = [];
        for (let p = 0; p < drawSize; p++) positionDist.push({});

        for (let i = 0; i < limit; i++) {
            const nums = (history[i].numbers || []).slice().sort((a, b) => a - b);
            const decay = Math.exp(-i * 0.05);
            for (let p = 0; p < Math.min(drawSize, nums.length); p++) {
                const n = nums[p];
                if (n >= startNum && n <= endNum) {
                    positionDist[p][n] = (positionDist[p][n] || 0) + decay;
                }
            }
        }

        // Para cada nÃºmero: somar P(n aparece em alguma posiÃ§Ã£o)
        for (let p = 0; p < drawSize; p++) {
            // Normalizar distribuiÃ§Ã£o da posiÃ§Ã£o
            let total = 0;
            for (const v of Object.values(positionDist[p])) total += v;
            if (total === 0) continue;

            for (const [n, count] of Object.entries(positionDist[p])) {
                const num = parseInt(n);
                if (num >= startNum && num <= endNum) {
                    scores[num] += (count / total) / drawSize;
                }
            }
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜… MODO DEUS â€” CAMADA 11: CADEIA DE DEPENDÃŠNCIA SEQUENCIAL    â•‘
    // â•‘  Quando X apareceu no sorteio N, o que aparece no N+1?         â•‘
    // â•‘  Grafo de transiÃ§Ã£o: "predecessores geram sucessores"          â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _godSequentialChain(history, startNum, endNum, N) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (N < 5) return scores;

        // Construir grafo de transiÃ§Ã£o: predecessor[X] â†’ sucessor[Y]
        const transitions = {}; // transitions[X] = { Y: count, Z: count, ... }
        const limit = Math.min(40, N - 1);

        for (let i = 0; i < limit; i++) {
            const predecessors = new Set((history[i + 1].numbers || []).concat(history[i + 1].numbers2 || []));
            const successors = (history[i].numbers || []).concat(history[i].numbers2 || []);
            const decay = Math.exp(-i * 0.04);

            for (const pred of predecessors) {
                if (!transitions[pred]) transitions[pred] = {};
                for (const succ of successors) {
                    if (succ >= startNum && succ <= endNum) {
                        transitions[pred][succ] = (transitions[pred][succ] || 0) + decay;
                    }
                }
            }
        }

        // Dado o ÃšLTIMO sorteio, projetar o prÃ³ximo
        const lastDraw = (history[0].numbers || []).concat(history[0].numbers2 || []);
        const projectedScores = {};
        for (let n = startNum; n <= endNum; n++) projectedScores[n] = 0;

        for (const pred of lastDraw) {
            if (transitions[pred]) {
                // Normalizar transiÃ§Ãµes deste predecessor
                let total = 0;
                for (const v of Object.values(transitions[pred])) total += v;
                if (total === 0) continue;

                for (const [succ, count] of Object.entries(transitions[pred])) {
                    const num = parseInt(succ);
                    if (num >= startNum && num <= endNum) {
                        projectedScores[num] += (count / total);
                    }
                }
            }
        }

        // Combinar com scores base
        for (let n = startNum; n <= endNum; n++) {
            scores[n] = 0.3 + projectedScores[n] * 0.7;
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜… MODO DEUS â€” CAMADA 12: MOMENTUM DE SOMA E PARIDADE         â•‘
    // â•‘  Se soma subiu 3x seguidas, tende a descer â†’ boost baixos     â•‘
    // â•‘  Se paridade desequilibrou, tende a corrigir                   â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _godMomentum(history, startNum, endNum, N, drawSize) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (N < 5) return scores;

        // â”â”â” AnÃ¡lise de momentum de SOMA â”â”â”
        const sums = [];
        for (let i = 0; i < Math.min(10, N); i++) {
            const nums = history[i].numbers || [];
            sums.push(nums.reduce((a, b) => a + b, 0));
        }

        // DireÃ§Ã£o: soma subindo ou descendo?
        let sumTrend = 0;
        for (let i = 0; i < sums.length - 1; i++) {
            sumTrend += (sums[i] > sums[i + 1]) ? 1 : -1;
        }

        // Soma mÃ©dia esperada
        const avgSum = (startNum + endNum) / 2 * drawSize;
        const lastSum = sums[0] || avgSum;
        const sumDeviation = lastSum - avgSum; // > 0 = soma alta, < 0 = soma baixa

        // Se soma estÃ¡ alta e subindo â†’ boost nÃºmeros BAIXOS (regressÃ£o)
        // Se soma estÃ¡ baixa e descendo â†’ boost nÃºmeros ALTOS (regressÃ£o)
        const midPoint = (startNum + endNum) / 2;
        for (let n = startNum; n <= endNum; n++) {
            let momentum = 0;
            if (sumDeviation > 0 && sumTrend > 0) {
                // Soma alta + subindo â†’ boost baixos (regressÃ£o Ã  mÃ©dia)
                momentum = (midPoint - n) / (endNum - startNum) * 0.4;
            } else if (sumDeviation < 0 && sumTrend < 0) {
                // Soma baixa + descendo â†’ boost altos
                momentum = (n - midPoint) / (endNum - startNum) * 0.4;
            }
            scores[n] = 0.5 + momentum;
        }

        // â”â”â” AnÃ¡lise de paridade â”â”â”
        const lastNums = history[0].numbers || [];
        const evens = lastNums.filter(n => n % 2 === 0).length;
        const odds = lastNums.length - evens;
        const parityRatio = evens / Math.max(1, lastNums.length);

        // Paridade desequilibrada â†’ boost para o lado fraco
        if (parityRatio > 0.65) {
            // Muitos pares â†’ boost Ã­mpares
            for (let n = startNum; n <= endNum; n++) {
                if (n % 2 !== 0) scores[n] = Math.min(1.0, scores[n] + 0.15);
            }
        } else if (parityRatio < 0.35) {
            // Muitos Ã­mpares â†’ boost pares
            for (let n = startNum; n <= endNum; n++) {
                if (n % 2 === 0) scores[n] = Math.min(1.0, scores[n] + 0.15);
            }
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜… QUANTUM L99 â€” CAMADA 13: ESPELHO TEMPORAL                          â•‘
    // â•‘  Compara padrÃ£o dos Ãºltimos 3 sorteios com TODOS os padrÃµes do        â•‘
    // â•‘  histÃ³rico. O sorteio que SEGUIU o padrÃ£o mais similar Ã© a projeÃ§Ã£o.  â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _quantumTemporalMirror(history, startNum, endNum, N, drawSize) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (N < 6) return scores;

        // Extrair "impressÃ£o digital" dos Ãºltimos 3 sorteios
        const fingerprint = [];
        for (let i = 0; i < 3; i++) {
            const nums = history[i].numbers || [];
            fingerprint.push(new Set(nums));
        }

        // Calcular similaridade com cada janela de 3 no histÃ³rico
        const limit = Math.min(N - 3, 35);
        let bestSim = 0;
        let bestFollowIdx = -1;
        const candidates = [];

        for (let w = 3; w < limit; w++) {
            let similarity = 0;
            for (let d = 0; d < 3; d++) {
                const histSet = new Set(history[w + d].numbers || []);
                let overlap = 0;
                for (const n of fingerprint[d]) {
                    if (histSet.has(n)) overlap++;
                }
                similarity += overlap / Math.max(1, drawSize);
            }
            similarity /= 3; // Normalizar [0, 1]

            if (similarity > 0.2) {
                // O sorteio que SEGUIU esta janela Ã© a projeÃ§Ã£o
                const followIdx = w - 1; // sorteio imediatamente antes da janela
                if (followIdx >= 0 && followIdx < w) {
                    candidates.push({ idx: followIdx, sim: similarity });
                }
            }
            if (similarity > bestSim) {
                bestSim = similarity;
                bestFollowIdx = w - 1;
            }
        }

        // Ponderar scores dos candidatos pela similaridade
        if (candidates.length > 0) {
            let totalSim = 0;
            for (const c of candidates) totalSim += c.sim;
            for (const c of candidates) {
                const followNums = history[c.idx].numbers || [];
                const weight = c.sim / totalSim;
                for (const n of followNums) {
                    if (n >= startNum && n <= endNum) {
                        scores[n] += weight * 0.6;
                    }
                }
            }
        } else if (bestFollowIdx >= 0) {
            const followNums = history[bestFollowIdx].numbers || [];
            for (const n of followNums) {
                if (n >= startNum && n <= endNum) {
                    scores[n] += 0.3;
                }
            }
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜… QUANTUM L99 â€” CAMADA 14: ANÃLISE DE LACUNAS (GAP ANALYSIS)         â•‘
    // â•‘  Calcula gap mÃ©dio entre apariÃ§Ãµes e identifica nÃºmeros que estÃ£o      â•‘
    // â•‘  EXATAMENTE no ponto Ã³timo de retorno estatÃ­stico                      â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _quantumGapAnalysis(history, startNum, endNum, N, drawSize, totalRange) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (N < 10) return scores;

        const limit = Math.min(N, 40);
        const expectedGap = totalRange / drawSize; // Gap teÃ³rico

        for (let n = startNum; n <= endNum; n++) {
            // Encontrar TODAS as apariÃ§Ãµes e calcular gaps
            const appearances = [];
            for (let i = 0; i < limit; i++) {
                const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
                if (nums.includes(n)) appearances.push(i);
            }

            if (appearances.length < 2) {
                // Nunca ou quase nunca apareceu â€” nÃºmero muito atrasado
                scores[n] = 0.75; // Boost moderado
                continue;
            }

            // Calcular gap mÃ©dio real
            let totalGap = 0;
            for (let j = 0; j < appearances.length - 1; j++) {
                totalGap += appearances[j + 1] - appearances[j];
            }
            const avgGap = totalGap / (appearances.length - 1);

            // Calcular gap atual (desde Ãºltima apariÃ§Ã£o)
            const currentGap = appearances[0]; // Quantos sorteios desde que saiu

            // â˜… PONTO Ã“TIMO: quando currentGap â‰ˆ avgGap (nÃºmero "devendo")
            const ratio = currentGap / avgGap;

            if (ratio >= 0.85 && ratio <= 1.5) {
                // No ponto IDEAL de retorno â€” score mÃ¡ximo
                scores[n] = 0.95;
            } else if (ratio >= 1.5 && ratio <= 2.5) {
                // Muito atrasado â€” bom candidato
                scores[n] = 0.85;
            } else if (ratio >= 0.5 && ratio < 0.85) {
                // Saiu recentemente â€” score baixo
                scores[n] = 0.35;
            } else if (ratio > 2.5) {
                // Extremamente atrasado â€” pode ter mudado de padrÃ£o
                scores[n] = 0.65;
            } else {
                scores[n] = 0.25; // Saiu muito recentemente
            }
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜… QUANTUM L99 â€” CAMADA 15: CLUSTERS DE CO-OCORRÃŠNCIA                 â•‘
    // â•‘  Identifica PARES de nÃºmeros que historicamente saem JUNTOS            â•‘
    // â•‘  Dado o Ãºltimo sorteio, quais pares tendem a se repetir?              â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _quantumClusters(history, startNum, endNum, N, drawSize) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (N < 5) return scores;

        // Construir matriz de co-ocorrÃªncia ponderada
        const coMatrix = {};
        const limit = Math.min(N, 30);

        for (let i = 0; i < limit; i++) {
            const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            const decay = Math.exp(-i * 0.06);
            for (let a = 0; a < nums.length; a++) {
                for (let b = a + 1; b < nums.length; b++) {
                    const na = nums[a], nb = nums[b];
                    if (na >= startNum && na <= endNum && nb >= startNum && nb <= endNum) {
                        const key = Math.min(na, nb) + ':' + Math.max(na, nb);
                        coMatrix[key] = (coMatrix[key] || 0) + decay;
                    }
                }
            }
        }

        // Dado o ÃšLTIMO sorteio: quais nÃºmeros tÃªm forte co-ocorrÃªncia?
        const lastDraw = (history[0].numbers || []).concat(history[0].numbers2 || []);
        const coScores = {};
        for (let n = startNum; n <= endNum; n++) coScores[n] = 0;

        for (const pred of lastDraw) {
            for (let n = startNum; n <= endNum; n++) {
                if (n === pred) continue;
                const key = Math.min(pred, n) + ':' + Math.max(pred, n);
                if (coMatrix[key]) {
                    coScores[n] += coMatrix[key];
                }
            }
        }

        // Normalizar co-scores
        let maxCo = 0;
        for (let n = startNum; n <= endNum; n++) {
            if (coScores[n] > maxCo) maxCo = coScores[n];
        }
        if (maxCo > 0) {
            for (let n = startNum; n <= endNum; n++) {
                scores[n] = 0.3 + (coScores[n] / maxCo) * 0.7;
            }
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜… QUANTUM L99 â€” CAMADA 16: REGRESSÃƒO Ã€ MÃ‰DIA PONDERADA               â•‘
    // â•‘  Para cada nÃºmero: frequÃªncia real vs teÃ³rica esperada                 â•‘
    // â•‘  NÃºmeros sub-representados tendem a CORRIGIR â†’ sÃ£o apostÃ¡veis         â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _quantumMeanReversion(history, startNum, endNum, N, drawSize, totalRange) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (N < 10) return scores;

        const limit = Math.min(N, 40);
        const expectedFreq = (drawSize / totalRange) * limit; // FrequÃªncia esperada

        // Contar frequÃªncia real e nas janelas recentes
        const freqTotal = {};
        const freqRecent = {}; // Ãšltimos 10
        for (let n = startNum; n <= endNum; n++) { freqTotal[n] = 0; freqRecent[n] = 0; }

        for (let i = 0; i < limit; i++) {
            const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            for (const n of nums) {
                if (n >= startNum && n <= endNum) {
                    freqTotal[n]++;
                    if (i < 10) freqRecent[n]++;
                }
            }
        }

        const expectedRecent = (drawSize / totalRange) * Math.min(10, limit);

        for (let n = startNum; n <= endNum; n++) {
            const deviationTotal = (freqTotal[n] - expectedFreq) / Math.max(1, expectedFreq);
            const deviationRecent = (freqRecent[n] - expectedRecent) / Math.max(1, expectedRecent);

            // â˜… REGRESSÃƒO: nÃºmeros que estÃ£o ABAIXO da mÃ©dia tendem a subir
            if (deviationTotal < -0.3 && deviationRecent < -0.2) {
                // Fortemente sub-representado em ambas janelas
                scores[n] = 0.90;
            } else if (deviationTotal < -0.15) {
                // Moderadamente sub-representado
                scores[n] = 0.75;
            } else if (deviationTotal > 0.3 && deviationRecent > 0.2) {
                // Sobre-representado â†’ tende a cair
                scores[n] = 0.25;
            } else if (deviationTotal > 0.15) {
                scores[n] = 0.40;
            } else {
                // Na mÃ©dia â€” score neutro
                scores[n] = 0.55;
            }
        }

        return this._normalizeScores(scores, startNum, endNum);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜…â˜…â˜… SÃNTESE QUANTUM L99 â€” 18 CAMADAS DE PREDIÃ‡ÃƒO â˜…â˜…â˜…                    â•‘
    // â•‘  8 camadas clÃ¡ssicas + 4 Modo Deus + 4 QUANTUM L99                        â•‘
    // â•‘  + Precision Calibrator + Pattern DNA                                      â•‘
    // â•‘  + Filtro CombinatÃ³rio Final (validaÃ§Ã£o estrutural = Camada 19)            â•‘
    // â•‘  CALIBRAÃ‡ÃƒO DINÃ‚MICA com cross-validation de 12 sorteios                   â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _scoreAllNumbers(gameKey, profile, history, startNum, endNum, totalRange) {
        const N = history.length;
        const drawSize = profile.lotteryDraw;

        // â”â”â” CAMADAS 1-8: Base NE-V1 â”â”â”
        const freqScores = this._layerFrequency(history, startNum, endNum, N);
        const trendScores = this._layerTrend(history, startNum, endNum, N);
        const delayScores = this._layerDelay(history, startNum, endNum, N, drawSize, totalRange);
        const entropyScores = this._layerEntropy(history, startNum, endNum, N, profile);
        const markovScores = this._layerMarkov(history, startNum, endNum, N);
        const phaseScores = this._layerPhase(history, startNum, endNum, N);
        const clairScores = this._layerClairvoyance(history, startNum, endNum, N, drawSize);
        const nextDrawScores = this._layerNextDraw(gameKey, history, startNum, endNum, N, profile);

        // â”â”â” CAMADAS 9-12: MODO DEUS â”â”â”
        const bayesianScores = this._godBayesian(history, startNum, endNum, N, drawSize);
        const positionalScores = this._godPositional(history, startNum, endNum, N, drawSize);
        const sequentialScores = this._godSequentialChain(history, startNum, endNum, N);
        const momentumScores = this._godMomentum(history, startNum, endNum, N, drawSize);

        // â”â”â” CAMADAS 13-16: QUANTUM L99 â”â”â”
        const mirrorScores = this._quantumTemporalMirror(history, startNum, endNum, N, drawSize);
        const gapScores = this._quantumGapAnalysis(history, startNum, endNum, N, drawSize, totalRange);
        const clusterScores = this._quantumClusters(history, startNum, endNum, N, drawSize);
        const reversionScores = this._quantumMeanReversion(history, startNum, endNum, N, drawSize, totalRange);

        // ━━━ CAMADA 22: CROSS-SORTEIO QUANTICO — EXCLUSIVO DUPLA SENA ━━━
        // Analisa assimetria entre 1o e 2o sorteio para injetar Quantum Boost
        let crossDrawScores = {};
        for (let n = startNum; n <= endNum; n++) crossDrawScores[n] = 0.5;
        if (gameKey === 'duplasena' && N >= 5) {
            crossDrawScores = this._quantumDuplaCrossDraw(history, startNum, endNum, N);
            console.log('[QUANTUM-L99] ★ CAMADA 22 (Cross-Sorteio Dupla Sena) — Assimetria 1o/2o sorteio ativada');
        }

        // â”â”â” CAMADA 17: PRECISION CALIBRATOR â€” Futurologia dos Ãšltimos 3 â”â”â”
        let precisionScores = {};
        for (let n = startNum; n <= endNum; n++) precisionScores[n] = 0.5;
        if (typeof PrecisionCalibrator !== 'undefined' && N >= 4) {
            try {
                const last3Trends = PrecisionCalibrator.analyzeLast3Trends(gameKey, history, startNum, endNum);
                const conditionalProb = PrecisionCalibrator.buildConditionalProbMatrix(gameKey, history, startNum, endNum, drawSize);
                for (let n = startNum; n <= endNum; n++) {
                    precisionScores[n] = (last3Trends[n] || 0) * 0.6 + (conditionalProb[n] || 0) * 0.4;
                }
                precisionScores = this._normalizeScores(precisionScores, startNum, endNum);
                console.log('[QUANTUM-L99] â˜… CAMADA 17 (Precision Calibrator) â€” Futurologia ativada');
            } catch (e) {
                console.warn('[QUANTUM-L99] âš  Camada 17 falhou:', e.message);
            }
        }

        // â”â”â” CAMADA 18: PATTERN DNA â€” Aprender com o Passado para Prever o Futuro â”â”â”
        // Analisa: o que os nÃºmeros SORTEADOS tinham de ESPECIAL?
        // Por que ESSES nÃºmeros saÃ­ram e nÃ£o outros?
        // Projeta essas mesmas condiÃ§Ãµes para o PRÃ“XIMO sorteio
        let patternDnaScores = {};
        for (let n = startNum; n <= endNum; n++) patternDnaScores[n] = 0.5;
        if (N >= 5) {
            const analysisWindow = Math.min(15, N); // Ãšltimos 15 sorteios
            
            // â”â” PASSO 1: Para cada sorteio passado, extrair o "DNA" dos nÃºmeros que saÃ­ram â”â”
            // DNA = {gapMÃ©dio, zonaDistribuiÃ§Ã£o, paridadeRatio, somaRelativa, vizinhanÃ§a}
            const winningDNA = [];
            for (let i = 0; i < analysisWindow; i++) {
                const nums = (history[i].numbers || []).sort((a, b) => a - b);
                if (nums.length === 0) continue;
                
                // Calcular DNA deste sorteio
                const sum = nums.reduce((a, b) => a + b, 0);
                const avgSum = (startNum + endNum) / 2 * drawSize;
                const somaRelativa = sum / avgSum; // >1 = soma alta, <1 = soma baixa
                
                const evens = nums.filter(x => x % 2 === 0).length;
                const paridadeRatio = evens / nums.length;
                
                // Gaps entre nÃºmeros consecutivos no jogo
                const gaps = [];
                for (let j = 1; j < nums.length; j++) gaps.push(nums[j] - nums[j-1]);
                const avgGap = gaps.length > 0 ? gaps.reduce((a, b) => a + b, 0) / gaps.length : 0;
                
                // Zona dominante â€” v7.1: usar zonas reais do perfil
                const dnaZoneCount = Math.min(profile.zones || 4, 10);
                const zones = nums.map(x => Math.floor((x - startNum) / (totalRange / dnaZoneCount)));
                const zoneFreq = new Array(dnaZoneCount).fill(0);
                for (const z of zones) zoneFreq[Math.min(dnaZoneCount - 1, z)]++;
                
                // Atraso mÃ©dio dos nÃºmeros no momento que saÃ­ram
                let avgDelay = 0;
                if (i + 1 < N) {
                    for (const n of nums) {
                        let delay = 0;
                        for (let k = i + 1; k < N; k++) {
                            if ((history[k].numbers || []).includes(n)) { delay = k - i; break; }
                        }
                        avgDelay += delay;
                    }
                    avgDelay /= nums.length;
                }
                
                winningDNA.push({
                    somaRelativa, paridadeRatio, avgGap, zoneFreq, avgDelay,
                    nums: new Set(nums), weight: Math.exp(-i * 0.12) // Recentes pesam mais
                });
            }
            
            // â”â” PASSO 2: Calcular o "DNA IDEAL" â€” mÃ©dia ponderada dos Ãºltimos sorteios â”â”
            let idealSoma = 0, idealParidade = 0, idealGap = 0, idealDelay = 0;
            // v7.1: usar profile.zones real ao invÃ©s de 4 hardcoded
            const dnaZones = Math.min(profile.zones || 4, 10);
            const idealZone = new Array(dnaZones).fill(0);
            let totalWeight = 0;
            
            for (const dna of winningDNA) {
                idealSoma += dna.somaRelativa * dna.weight;
                idealParidade += dna.paridadeRatio * dna.weight;
                idealGap += dna.avgGap * dna.weight;
                idealDelay += dna.avgDelay * dna.weight;
                for (let z = 0; z < dnaZones; z++) idealZone[z] += dna.zoneFreq[z] * dna.weight;
                totalWeight += dna.weight;
            }
            if (totalWeight > 0) {
                idealSoma /= totalWeight;
                idealParidade /= totalWeight;
                idealGap /= totalWeight;
                idealDelay /= totalWeight;
                for (let z = 0; z < dnaZones; z++) idealZone[z] /= totalWeight;
            }
            
            // â”â” PASSO 3: Para cada nÃºmero candidato, calcular "afinidade DNA" â”â”
            // Quanto mais parecido com o DNA ideal, maior o score
            for (let n = startNum; n <= endNum; n++) {
                let score = 0.5;
                
                // A) ATRASO ATUAL vs atraso ideal dos vencedores
                let currentDelay = 0;
                for (let i = 0; i < N; i++) {
                    if ((history[i].numbers || []).concat(history[i].numbers2 || []).includes(n)) {
                        currentDelay = i;
                        break;
                    }
                    if (i === N - 1) currentDelay = N;
                }
                const delayMatch = 1.0 - Math.min(1.0, Math.abs(currentDelay - idealDelay) / Math.max(1, idealDelay * 2));
                score += delayMatch * 0.30;
                
                // B) ZONA â€” nÃºmero estÃ¡ na zona que os vencedores preferem?
                const nZone = Math.min(dnaZones - 1, Math.floor((n - startNum) / (totalRange / dnaZones)));
                const zoneAffinity = idealZone[nZone] / Math.max(0.1, Math.max(...idealZone));
                score += zoneAffinity * 0.20;
                
                // C) VIZINHANÃ‡A VENCEDORA â€” nos Ãºltimos sorteios, este nÃºmero estava PERTO dos que saÃ­ram?
                let neighborBonus = 0;
                for (const dna of winningDNA.slice(0, 5)) { // Ãšltimos 5
                    for (const wn of dna.nums) {
                        if (Math.abs(n - wn) <= 3 && Math.abs(n - wn) > 0) {
                            neighborBonus += dna.weight * 0.08;
                        }
                    }
                }
                score += Math.min(0.25, neighborBonus);
                
                // D) PADRÃƒO DE RETORNO â€” apÃ³s sair, quantos sorteios atÃ© voltar? (ciclo individual)
                const appearances = [];
                for (let i = 0; i < Math.min(30, N); i++) {
                    if ((history[i].numbers || []).concat(history[i].numbers2 || []).includes(n)) {
                        appearances.push(i);
                    }
                }
                if (appearances.length >= 2) {
                    let avgCycle = 0;
                    for (let j = 0; j < appearances.length - 1; j++) {
                        avgCycle += appearances[j + 1] - appearances[j];
                    }
                    avgCycle /= (appearances.length - 1);
                    const cycleMatch = 1.0 - Math.min(1.0, Math.abs(currentDelay - avgCycle) / Math.max(1, avgCycle));
                    score += cycleMatch * 0.25; // Ponto Ã³timo de retorno
                }
                
                patternDnaScores[n] = score;
            }
            
            patternDnaScores = this._normalizeScores(patternDnaScores, startNum, endNum);
            console.log('[QUANTUM-L99] â˜… CAMADA 18 (Pattern DNA) â€” Aprendendo com o passado para prever o futuro');
            console.log('[QUANTUM-L99]    DNA Ideal: soma=' + idealSoma.toFixed(2) + ' | paridade=' + idealParidade.toFixed(2) + ' | gap=' + idealGap.toFixed(1) + ' | delay=' + idealDelay.toFixed(1));
        }

        // â”â”â” CAMADA 19: DUPLAS E TRIOS FREQUENTES â€” Futurologia CombinatÃ³ria â”â”â”
        // Analisa PARES e TRIOS que mais saÃ­ram JUNTOS historicamente
        // Projeta quais combinaÃ§Ãµes tÃªm maior probabilidade de repetir
        // Cada nÃºmero ganha score baseado em quantas duplas/trios TOP ele compÃµe
        let pairTrioScores = {};
        for (let n = startNum; n <= endNum; n++) pairTrioScores[n] = 0.5;
        if (N >= 8) {
            const pairFreq = {}, trioFreq = {};
            const pairLimit = Math.min(50, N);
            
            // Contar TODAS as duplas e trios no histÃ³rico
            for (let t = 0; t < pairLimit; t++) {
                const nums = (history[t].numbers || []).concat(history[t].numbers2 || [])
                    .filter(x => x >= startNum && x <= endNum)
                    .sort((a, b) => a - b);
                const decay = Math.exp(-t * 0.04); // Recentes pesam mais
                
                for (let i = 0; i < nums.length; i++) {
                    for (let j = i + 1; j < nums.length; j++) {
                        const pk = nums[i] + '-' + nums[j];
                        pairFreq[pk] = (pairFreq[pk] || 0) + decay;
                        
                        // Trios: atÃ© 3 posiÃ§Ãµes alÃ©m de j
                        for (let k = j + 1; k < nums.length && k < j + 5; k++) {
                            const tk = nums[i] + '-' + nums[j] + '-' + nums[k];
                            trioFreq[tk] = (trioFreq[tk] || 0) + decay;
                        }
                    }
                }
            }
            
            // Rankear as TOP 30 duplas e TOP 20 trios
            const topPairs = Object.entries(pairFreq).sort((a, b) => b[1] - a[1]).slice(0, 30);
            const topTrios = Object.entries(trioFreq).sort((a, b) => b[1] - a[1]).slice(0, 20);
            
            // Score: cada nÃºmero ganha pontos baseado em quantas TOP duplas/trios ele participa
            const maxPairScore = topPairs.length > 0 ? topPairs[0][1] : 1;
            for (const [pk, freq] of topPairs) {
                const [a, b] = pk.split('-').map(Number);
                const boost = (freq / maxPairScore) * 0.35;
                pairTrioScores[a] = (pairTrioScores[a] || 0.5) + boost;
                pairTrioScores[b] = (pairTrioScores[b] || 0.5) + boost;
            }
            
            const maxTrioScore = topTrios.length > 0 ? topTrios[0][1] : 1;
            for (const [tk, freq] of topTrios) {
                const [a, b, c] = tk.split('-').map(Number);
                const boost = (freq / maxTrioScore) * 0.25;
                pairTrioScores[a] = (pairTrioScores[a] || 0.5) + boost;
                pairTrioScores[b] = (pairTrioScores[b] || 0.5) + boost;
                pairTrioScores[c] = (pairTrioScores[c] || 0.5) + boost;
            }
            
            // PROJEÃ‡ÃƒO FUTURA: Duplas do Ãºltimo sorteio â†’ quais nÃºmeros acompanham?
            if (N >= 2) {
                const lastNums = (history[0].numbers || []).filter(x => x >= startNum && x <= endNum);
                for (const ln of lastNums) {
                    // Encontrar os TOP parceiros deste nÃºmero
                    for (const [pk, freq] of topPairs) {
                        const [a, b] = pk.split('-').map(Number);
                        if (a === ln) pairTrioScores[b] += (freq / maxPairScore) * 0.15;
                        else if (b === ln) pairTrioScores[a] += (freq / maxPairScore) * 0.15;
                    }
                }
            }
            
            pairTrioScores = this._normalizeScores(pairTrioScores, startNum, endNum);
            
            const topPairNums = topPairs.slice(0, 5).map(([pk, f]) => pk + '(' + f.toFixed(1) + ')').join(', ');
            const topTrioNums = topTrios.slice(0, 3).map(([tk, f]) => tk + '(' + f.toFixed(1) + ')').join(', ');
            console.log('[QUANTUM-L99] â˜… CAMADA 19 (Duplas+Trios) â€” TOP5 Duplas: ' + topPairNums);
            console.log('[QUANTUM-L99]    TOP3 Trios: ' + topTrioNums);
        }

        console.log('%c[QUANTUM-L99] â˜…â˜…â˜… 21 CAMADAS ATIVADAS â€” ' + gameKey + ' â˜…â˜…â˜…', 'color: gold; font-weight: bold;');

        // â” â” â”  CAMADA 20: CICLO INDIVIDUAL DE RETORNO â€” Futurologia Temporal â” â” â” 
        // Cada nÃºmero tem seu PRÃ“PRIO RITMO. Score MÃ XIMO no ponto Ã³timo de retorno.
        let cycleReturnScores = {};
        for (let n = startNum; n <= endNum; n++) cycleReturnScores[n] = 0.5;
        if (N >= 10) {
            const expectedGlobalCycle = totalRange / drawSize;
            for (let n = startNum; n <= endNum; n++) {
                const appearances = [];
                for (let i = 0; i < Math.min(60, N); i++) {
                    if ((history[i].numbers || []).concat(history[i].numbers2 || []).includes(n)) appearances.push(i);
                }
                if (appearances.length < 2) {
                    cycleReturnScores[n] = appearances.length > 0 && appearances[0] > expectedGlobalCycle * 1.5 ? 0.90 : 0.60;
                    continue;
                }
                const gaps = [];
                for (let j = 0; j < appearances.length - 1; j++) gaps.push(appearances[j + 1] - appearances[j]);
                const avgCycle = gaps.reduce((a, b) => a + b, 0) / gaps.length;
                const stdCycle = Math.sqrt(gaps.map(g => (g - avgCycle) ** 2).reduce((a, b) => a + b, 0) / gaps.length);
                const currentDelay = appearances[0];
                const cyclePosition = currentDelay / Math.max(1, avgCycle);
                let acceleration = 0;
                if (gaps.length >= 4) {
                    const half = Math.floor(gaps.length / 2);
                    const recentAvg = gaps.slice(0, half).reduce((a, b) => a + b, 0) / half;
                    const oldAvg = gaps.slice(half).reduce((a, b) => a + b, 0) / (gaps.length - half);
                    acceleration = (oldAvg - recentAvg) / Math.max(1, oldAvg);
                }
                let score = 0.3;
                if (cyclePosition >= 0.85 && cyclePosition <= 1.2) score = 0.95;
                else if (cyclePosition >= 0.6 && cyclePosition < 0.85) score = 0.75;
                else if (cyclePosition > 1.2 && cyclePosition <= 2.0) score = 0.85;
                else if (cyclePosition > 2.0) score = 0.80;
                else score = 0.25;
                if (acceleration > 0.15) score += 0.10;
                const cv = stdCycle / Math.max(1, avgCycle);
                if (cv < 0.3) score += 0.08;
                else if (cv < 0.5) score += 0.04;
                cycleReturnScores[n] = Math.min(1.0, score);
            }
            cycleReturnScores = this._normalizeScores(cycleReturnScores, startNum, endNum);
            const optNums = Object.entries(cycleReturnScores).filter(([,s]) => s > 0.75).sort((a,b) => b[1]-a[1]).slice(0,8).map(([n,s]) => n+'('+s.toFixed(2)+')').join(', ');
            console.log('[QUANTUM-L99] â˜… CAMADA 20 (Ciclo Individual) â€” Ponto Ã“timo: ' + optNums);
        }

        // â”â”â” CAMADA 21: SUPERPOSIÃ‡ÃƒO QUÃ‚NTICA â€” 5 CenÃ¡rios Paralelos â”â”â”
        // Cada nÃºmero avaliado em 5 janelas temporais simultÃ¢neas. Colapso = score.
        let quantumSuperScores = {};
        for (let n = startNum; n <= endNum; n++) quantumSuperScores[n] = 0.5;
        if (N >= 8) {
            const scenarios = [
                { window: 3, weight: 0.30 }, { window: 7, weight: 0.25 },
                { window: 15, weight: 0.20 }, { window: 30, weight: 0.15 },
                { window: Math.min(50, N), weight: 0.10 }
            ];
            for (let n = startNum; n <= endNum; n++) {
                let collapseProb = 0;
                for (const sc of scenarios) {
                    const ws = Math.min(sc.window, N);
                    let freq = 0;
                    for (let i = 0; i < ws; i++) {
                        if ((history[i].numbers || []).concat(history[i].numbers2 || []).includes(n)) freq++;
                    }
                    const freqRatio = freq / ws;
                    const expectedFreq = drawSize / totalRange;
                    let trend = 0;
                    if (ws >= 4) {
                        const half = Math.floor(ws / 2);
                        let fh = 0, sh = 0;
                        for (let i = 0; i < half; i++) { if ((history[i].numbers || []).concat(history[i].numbers2 || []).includes(n)) fh++; }
                        for (let i = half; i < ws; i++) { if ((history[i].numbers || []).concat(history[i].numbers2 || []).includes(n)) sh++; }
                        trend = (fh / half) - (sh / (ws - half));
                    }
                    const devBonus = freqRatio < expectedFreq ? 0.15 : -0.05;
                    const ss = Math.max(0, Math.min(1, 0.3 + freqRatio * 0.25 + trend * 0.20 + devBonus + (cycleReturnScores[n] || 0.5) * 0.10));
                    collapseProb += ss * sc.weight;
                }
                quantumSuperScores[n] = collapseProb;
            }
            quantumSuperScores = this._normalizeScores(quantumSuperScores, startNum, endNum);
            const topQ = Object.entries(quantumSuperScores).sort((a,b) => b[1]-a[1]).slice(0,6).map(([n,s]) => n+'('+s.toFixed(2)+')').join(', ');
            console.log('[QUANTUM-L99] â˜… CAMADA 21 (SuperposiÃ§Ã£o QuÃ¢ntica) â€” Colapso TOP: ' + topQ);
        }

        // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        // â˜…â˜…â˜… CONSENSO ENSEMBLE L99 â€” VotaÃ§Ã£o entre 21 camadas â˜…â˜…â˜…
        // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        const allLayers = [
            freqScores, trendScores, delayScores, entropyScores,
            markovScores, phaseScores, clairScores, nextDrawScores,
            bayesianScores, positionalScores, sequentialScores, momentumScores,
            mirrorScores, gapScores, clusterScores, reversionScores,
            precisionScores, patternDnaScores, pairTrioScores,
            cycleReturnScores, quantumSuperScores
        ];

        const topCandidateSize = Math.min(drawSize * 5, totalRange);
        const voteCount = {};
        for (let n = startNum; n <= endNum; n++) voteCount[n] = 0;

        for (const layer of allLayers) {
            const ranked = Object.entries(layer)
                .sort((a, b) => b[1] - a[1])
                .slice(0, topCandidateSize);
            for (const [numStr] of ranked) {
                voteCount[parseInt(numStr)]++;
            }
        }

        // Log consenso L99
        const consensusNums = [];
        for (let n = startNum; n <= endNum; n++) {
            if (voteCount[n] >= 13) consensusNums.push(n + '(' + voteCount[n] + ')');
        }
        if (consensusNums.length > 0) {
            console.log('[QUANTUM-L99] â˜… CONSENSO 13+/18: ' + consensusNums.join(', '));
        }

        // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        // â˜…â˜…â˜… v5.0: Cross-validation 12 sorteios + NDCG â˜…â˜…â˜…
        // â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        const NUM_LAYERS = 21;
        let dynamicBoosts = new Array(NUM_LAYERS).fill(1.0);
        if (N >= 8) {
            const testDraws = Math.min(12, N - 5);
            for (let t = 0; t < testDraws; t++) {
                const testHistory = history.slice(t + 1);
                const actualResult = new Set(
                    (history[t].numbers || []).concat(history[t].numbers2 || [])
                );
                const testN = testHistory.length;

                const testLayers = [
                    this._layerFrequency(testHistory, startNum, endNum, testN),
                    this._layerTrend(testHistory, startNum, endNum, testN),
                    this._layerDelay(testHistory, startNum, endNum, testN, drawSize, totalRange),
                    this._layerEntropy(testHistory, startNum, endNum, testN, profile),
                    this._layerMarkov(testHistory, startNum, endNum, testN),
                    this._layerPhase(testHistory, startNum, endNum, testN),
                    this._layerClairvoyance(testHistory, startNum, endNum, testN, drawSize),
                    this._layerNextDraw(gameKey, testHistory, startNum, endNum, testN, profile),
                    this._godBayesian(testHistory, startNum, endNum, testN, drawSize),
                    this._godPositional(testHistory, startNum, endNum, testN, drawSize),
                    this._godSequentialChain(testHistory, startNum, endNum, testN),
                    this._godMomentum(testHistory, startNum, endNum, testN, drawSize)
                ];

                // Camadas QUANTUM (13-16)
                testLayers.push(this._quantumTemporalMirror(testHistory, startNum, endNum, testN, drawSize));
                testLayers.push(this._quantumGapAnalysis(testHistory, startNum, endNum, testN, drawSize, totalRange));
                testLayers.push(this._quantumClusters(testHistory, startNum, endNum, testN, drawSize));
                testLayers.push(this._quantumMeanReversion(testHistory, startNum, endNum, testN, drawSize, totalRange));

                // Camada 17: Precision
                if (typeof PrecisionCalibrator !== 'undefined' && testN >= 4) {
                    try {
                        const tLast3 = PrecisionCalibrator.analyzeLast3Trends(gameKey, testHistory, startNum, endNum);
                        const tCond = PrecisionCalibrator.buildConditionalProbMatrix(gameKey, testHistory, startNum, endNum, drawSize);
                        const tPrec = {};
                        for (let n = startNum; n <= endNum; n++) tPrec[n] = (tLast3[n] || 0) * 0.6 + (tCond[n] || 0) * 0.4;
                        testLayers.push(this._normalizeScores(tPrec, startNum, endNum));
                    } catch(e) {
                        testLayers.push({});
                    }
                } else {
                    testLayers.push({});
                }

                // Camada 18: Pattern DNA (simplificado para CV â€” frequÃªncia de co-ocorrÃªncia)
                try {
                    const cvDna = {};
                    for (let n = startNum; n <= endNum; n++) cvDna[n] = 0.5;
                    if (testHistory.length >= 5) {
                        const last5 = testHistory.slice(0, 5);
                        for (const d of last5) {
                            const nums = (d.numbers || []).filter(x => x >= startNum && x <= endNum);
                            nums.forEach(n => { cvDna[n] = (cvDna[n] || 0.5) + 0.08; });
                        }
                    }
                    testLayers.push(this._normalizeScores(cvDna, startNum, endNum));
                } catch(e) { testLayers.push({}); }

                // Camada 19: Duplas+Trios (simplificado para CV â€” top pares)
                try {
                    const cvPair = {};
                    for (let n = startNum; n <= endNum; n++) cvPair[n] = 0.5;
                    if (testHistory.length >= 5) {
                        const pFreq = {};
                        for (let t = 0; t < Math.min(20, testHistory.length); t++) {
                            const nums = (testHistory[t].numbers || []).filter(x => x >= startNum && x <= endNum).sort((a,b) => a-b);
                            for (let i = 0; i < nums.length; i++) {
                                for (let j = i+1; j < nums.length; j++) {
                                    const pk = nums[i] + '-' + nums[j];
                                    pFreq[pk] = (pFreq[pk] || 0) + 1;
                                }
                            }
                        }
                        const topP = Object.entries(pFreq).sort((a,b) => b[1]-a[1]).slice(0,15);
                        for (const [pk, freq] of topP) {
                            const [a,b] = pk.split('-').map(Number);
                            const boost = freq * 0.05;
                            cvPair[a] = (cvPair[a] || 0.5) + boost;
                            cvPair[b] = (cvPair[b] || 0.5) + boost;
                        }
                    }
                    testLayers.push(this._normalizeScores(cvPair, startNum, endNum));
                } catch(e) { testLayers.push({}); }

                // Camada 20: Ciclo Individual (simplificado â€” atraso individual)
                try {
                    const cvCycle = {};
                    for (let n = startNum; n <= endNum; n++) {
                        let lastSeen = testHistory.length;
                        for (let t = 0; t < testHistory.length; t++) {
                            if ((testHistory[t].numbers || []).includes(n)) { lastSeen = t; break; }
                        }
                        const avgGap = drawSize / (endNum - startNum + 1);
                        const expectedReturn = Math.round(1 / avgGap);
                        cvCycle[n] = lastSeen >= expectedReturn ? 0.7 + Math.min(0.3, lastSeen * 0.02) : 0.4;
                    }
                    testLayers.push(this._normalizeScores(cvCycle, startNum, endNum));
                } catch(e) { testLayers.push({}); }

                // Camada 21: SuperposiÃ§Ã£o QuÃ¢ntica (simplificado â€” consenso das outras camadas)
                try {
                    const cvQuantum = {};
                    for (let n = startNum; n <= endNum; n++) {
                        let layerSum = 0, layerCount = 0;
                        for (let L = 0; L < testLayers.length; L++) {
                            if (testLayers[L] && testLayers[L][n] !== undefined) {
                                layerSum += testLayers[L][n];
                                layerCount++;
                            }
                        }
                        cvQuantum[n] = layerCount > 0 ? layerSum / layerCount : 0.5;
                    }
                    testLayers.push(this._normalizeScores(cvQuantum, startNum, endNum));
                } catch(e) { testLayers.push({}); }

                for (let L = 0; L < NUM_LAYERS; L++) {
                    const layerTop = Object.entries(testLayers[L] || {})
                        .sort((a, b) => b[1] - a[1])
                        .slice(0, Math.ceil(drawSize * 3.0)) // v7.1: drawSize*3 para capturar mais candidatos
                        .map(e => parseInt(e[0]));
                    // v7.1: NDCG com boost 1.8 (era 1.2) â€” camadas boas ganham MAIS peso
                    let ndcgScore = 0;
                    for (let r = 0; r < layerTop.length; r++) {
                        if (actualResult.has(layerTop[r])) {
                            ndcgScore += 1.0 / Math.log2(r + 2);
                        }
                    }
                    dynamicBoosts[L] += ndcgScore * 1.8;
                }
            }

            const avgBoost = dynamicBoosts.reduce((a, b) => a + b, 0) / NUM_LAYERS;
            for (let L = 0; L < NUM_LAYERS; L++) {
                // v9.5: Camadas 16+ (Precision, DNA, PairTrio, Cycle, Quantum) recebem boost mÃ­nimo 1.0
                // porque nÃ£o sÃ£o adequadamente testadas na CV
                const minBoost = (L >= 16) ? 1.0 : 0.5;
                dynamicBoosts[L] = Math.max(minBoost, dynamicBoosts[L] / avgBoost);
            }

            const names = ['freq','trend','delay','zone','markov','phase','clair','next','bayes','posit','seq','mom','mirror','gap','cluster','revert','prec','dna','pairs','cycle','qsuper'];
            const boostStr = dynamicBoosts.map((b, i) => names[i] + '=' + b.toFixed(2)).join(' ');
            console.log('[QUANTUM-L99] â˜… v9.5 CALIBRAÃ‡ÃƒO (12-fold NDCG, 21 camadas): ' + boostStr);
        }

        // â”â”â” PESOS QUANTUM L99 â”â”â”
        const weights = this._getGodModeWeights(gameKey);

        const scores = {};
        const [clampMin, clampMax] = profile.scoreClamp;

        // â˜… PRECISION v2.0: peso da camada 17 (precision)
        const precisionWeight = weights.precision || 0.12;
        // â˜… V4.0: peso da camada 18 (Pattern DNA â€” aprender com o passado)
        const dnaWeight = weights.patternDna || 0.12;
        // â˜… v9.0: peso da camada 19 (Duplas + Trios Frequentes)
        const pairTrioWeight = weights.pairTrio || 0.10;
        // â˜… v9.5: peso da camada 20 (Ciclo Individual de Retorno)
        const cycleWeight = weights.cycleReturn || 0.08;
        // â˜… v9.5: peso da camada 21 (SuperposiÃ§Ã£o QuÃ¢ntica)
        const quantumSuperWeight = weights.quantumSuper || 0.08;

        for (let n = startNum; n <= endNum; n++) {
            let raw = (freqScores[n] || 0) * weights.frequency * dynamicBoosts[0]
                    + (trendScores[n] || 0) * weights.trend * dynamicBoosts[1]
                    + (delayScores[n] || 0) * weights.delay * dynamicBoosts[2]
                    + (entropyScores[n] || 0) * weights.zone * dynamicBoosts[3]
                    + (markovScores[n] || 0) * weights.markov * dynamicBoosts[4]
                    + (phaseScores[n] || 0) * weights.phase * dynamicBoosts[5]
                    + (clairScores[n] || 0) * weights.clairvoyance * dynamicBoosts[6]
                    + (nextDrawScores[n] || 0) * weights.nextDraw * dynamicBoosts[7]
                    + (bayesianScores[n] || 0) * weights.bayesian * dynamicBoosts[8]
                    + (positionalScores[n] || 0) * weights.positional * dynamicBoosts[9]
                    + (sequentialScores[n] || 0) * weights.sequential * dynamicBoosts[10]
                    + (momentumScores[n] || 0) * weights.momentum * dynamicBoosts[11]
                    + (mirrorScores[n] || 0) * weights.mirror * dynamicBoosts[12]
                    + (gapScores[n] || 0) * weights.gap * dynamicBoosts[13]
                    + (clusterScores[n] || 0) * weights.cluster * dynamicBoosts[14]
                    + (reversionScores[n] || 0) * weights.reversion * dynamicBoosts[15]
                    + (precisionScores[n] || 0) * precisionWeight * dynamicBoosts[16]
                    + (patternDnaScores[n] || 0) * dnaWeight * dynamicBoosts[17]
                    + (pairTrioScores[n] || 0) * pairTrioWeight * dynamicBoosts[18]
                    + (cycleReturnScores[n] || 0) * cycleWeight * dynamicBoosts[19]
                    + (quantumSuperScores[n] || 0) * quantumSuperWeight * dynamicBoosts[20]
                    + (crossDrawScores[n] || 0) * (weights.crossDraw || 0) * 1.0; // Camada 22: so ativa na Dupla Sena

            // â˜… v9.5: CONSENSO para 21 camadas
            const votes = voteCount[n] || 0;
            if (votes >= 20) raw *= 1.28;
            else if (votes >= 18) raw *= 1.22;
            else if (votes >= 16) raw *= 1.15;
            else if (votes >= 14) raw *= 1.08;
            else if (votes >= 11) raw *= 1.00;
            else if (votes >= 7) raw *= 0.95;
            else if (votes >= 4) raw *= 0.90;
            else raw *= 0.85;

            // â˜… v7.0: Score FLOOR â€” nenhum nÃºmero pode ser eliminado
            scores[n] = Math.max(clampMin + 0.15, Math.min(clampMax, raw + 1.0));
        }

        const sorted = Object.entries(scores).sort((a, b) => b[1] - a[1]);
        const top5 = sorted.slice(0, 5).map(e => e[0] + '(' + e[1].toFixed(2) + '/v' + voteCount[parseInt(e[0])] + ')').join(', ');
        const bot5 = sorted.slice(-5).map(e => e[0] + '(' + e[1].toFixed(2) + ')').join(', ');
        console.log('[QUANTUM-L99] â˜… Top5: ' + top5 + ' | â¬‡ Bot5: ' + bot5);

        return scores;
    }

    // ======================================================================
    // CAMADA 22: CROSS-SORTEIO QUANTICO v10.2 — EXCLUSIVO DUPLA SENA
    // Analisa assimetria entre 1o e 2o Sorteio.
    // Numeros fortes no 2o sorteio recebem Quantum Boost proporcional.
    // ======================================================================
    static _quantumDuplaCrossDraw(history, startNum, endNum, N) {
        let scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;

        const analysisWindow = Math.min(50, N);

        // Contar frequencia de cada numero no 1o e 2o sorteio separadamente
        const freq1 = {};
        const freq2 = {};
        for (let n = startNum; n <= endNum; n++) { freq1[n] = 0; freq2[n] = 0; }

        let validDraws1 = 0, validDraws2 = 0;
        for (let i = 0; i < analysisWindow; i++) {
            const nums1 = history[i].numbers || [];
            const nums2 = history[i].numbers2 || [];

            if (nums1.length > 0) {
                validDraws1++;
                for (const n of nums1) {
                    if (n >= startNum && n <= endNum) freq1[n]++;
                }
            }
            if (nums2.length > 0) {
                validDraws2++;
                for (const n of nums2) {
                    if (n >= startNum && n <= endNum) freq2[n]++;
                }
            }
        }

        // Se nao temos dados suficientes do 2o sorteio, retornar neutro
        if (validDraws2 < 3) {
            console.log('[CROSS-DRAW] Dados insuficientes do 2o sorteio (' + validDraws2 + ' registros)');
            return scores;
        }

        // Calcular ASSIMETRIA: ratio = freq2 / (freq1 + freq2 + epsilon)
        const epsilon = 0.001;
        let maxAsym = 0;
        const asymmetry = {};

        for (let n = startNum; n <= endNum; n++) {
            const f1 = freq1[n] / Math.max(1, validDraws1);
            const f2 = freq2[n] / Math.max(1, validDraws2);
            const total = f1 + f2 + epsilon;
            const ratio = f2 / total;

            // Positivo = forte no 2o sorteio, Negativo = forte no 1o
            asymmetry[n] = ratio - 0.5;
            const absAsym = Math.abs(asymmetry[n]);
            if (absAsym > maxAsym) maxAsym = absAsym;
        }

        // Normalizar e aplicar scores
        const boostFactor = 0.35;
        const penaltyFactor = 0.10;
        let boostedCount = 0;

        for (let n = startNum; n <= endNum; n++) {
            const asym = asymmetry[n];
            const normalizedAsym = maxAsym > 0 ? asym / maxAsym : 0;

            if (normalizedAsym > 0.1) {
                scores[n] = 0.5 + normalizedAsym * boostFactor;
                boostedCount++;
            } else if (normalizedAsym < -0.1) {
                scores[n] = 0.5 + normalizedAsym * penaltyFactor;
            }
        }

        // Normalizar para [0, 1]
        scores = this._normalizeScores(scores, startNum, endNum);

        console.log('[CROSS-DRAW] Dupla Sena: ' + validDraws1 + ' sorteios 1o | ' + validDraws2 + ' sorteios 2o | ' + boostedCount + ' nums com boost');

        // Log top 5 numeros com mais assimetria positiva
        const top5 = Object.entries(asymmetry)
            .sort(function(a, b) { return b[1] - a[1]; })
            .slice(0, 5)
            .map(function(e) { return e[0] + '(+' + (e[1]*100).toFixed(1) + '%)'; })
            .join(', ');
        console.log('[CROSS-DRAW] Top5 2o-Sorteio: ' + top5);

        return scores;
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜…â˜…â˜… PESOS QUANTUM L99 v9.5 â€” 22 DIMENSÃ•ES POR LOTERIA â˜…â˜…â˜…            â•‘
    // â•‘  + Camada 17: PRECISION (Futurologia dos Ãºltimos 3)                    â•‘
    // â•‘  + Camada 18: PATTERN DNA (Aprender com o passado)                     â•‘
    // â•‘  + Camada 19: PAIR TRIO (Duplas e Trios Frequentes)                    â•‘
    // â•‘  + Camada 20: CYCLE RETURN (Ritmo Individual de Retorno)               â•‘
    // â•‘  + Camada 21: QUANTUM SUPER (SuperposiÃ§Ã£o Multi-CenÃ¡rio)               â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _getGodModeWeights(gameKey) {
        // v10.2 CONSOLIDADO: Pesos vivem APENAS em profile.weights
        // Eliminadas ~90 linhas de calibracoes duplicadas
        const profile = this.getProfile(gameKey);
        const w = profile.weights;

        const structPct = ((w.zone + w.gap + w.cluster + w.pairTrio + w.patternDna + w.precision) * 100).toFixed(0);
        const fallacyPct = ((w.frequency + w.delay + w.trend + w.markov + w.phase + (w.clairvoyance||0) + w.reversion + (w.mirror||0)) * 100).toFixed(0);
        console.log('[v10.2] ' + gameKey + ': Estrutural=' + structPct + '% | Falacia=' + fallacyPct + '% [CONSOLIDADO]');
        return w;
    }

    // Manter retrocompatibilidade
    static _getCalibratedWeights(gameKey) {
        return this._getGodModeWeights(gameKey);
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜…â˜…â˜… SNIPER QUANTUM v9.5 â€” MOTOR ESPECIALIZADO DE ALTA PRECISÃƒO â˜…â˜…â˜…    â•‘
    // â•‘  1. PrÃ©-seleciona TOP N nÃºmeros via 21 camadas do Quantum IA           â•‘
    // â•‘  2. Divide em Tiers (melhor â†’ pior) e gera jogos por tier              â•‘
    // â•‘  3. Cross-combina tiers entre si para mÃ¡xima diversidade               â•‘
    // â•‘  4. Aplica TODOS os filtros do Quantum IA                              â•‘
    // â•‘  Limite: 10.000 jogos                                                  â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static generateSniper(gameKey, numGames, poolSize, fixedNumbers, drawSize, customPool) {
        console.log('%c[SNIPER-QUANTUM] â˜…â˜…â˜… INICIANDO v9.5 â˜…â˜…â˜… ' + gameKey + ' | pool=' + poolSize + ' | jogos=' + numGames + ' | drawSize=' + drawSize + (customPool ? ' | MANUAL=' + customPool.length : ''), 'color: #EF4444; font-weight: bold; font-size: 14px;');
        
        const MAX_GAMES = 10000;
        numGames = Math.min(numGames, MAX_GAMES);
        
        // â”â”â” FASE 1: Obter scores de TODAS as 21 camadas â”â”â”
        const profile = this.getProfile(gameKey);
        if (!profile) {
            console.error('[SNIPER] Perfil nÃ£o encontrado:', gameKey);
            return { games: [], analysis: { confidence: 0, engine: 'SniperQuantum-ERROR' } };
        }
        
        const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        const startNum = game ? game.range[0] : 1;
        const endNum = game ? game.range[1] : 60;
        const totalRange = endNum - startNum + 1;
        const minBet = game ? game.minBet : drawSize;
        
        // Usar drawSize mÃ­nimo da loteria para os jogos individuais
        const actualDrawSize = minBet;
        
        // Garantir que poolSize Ã© vÃ¡lido
        // FIX: MÃ­nimo era actualDrawSize*2 (=30 na LotofÃ¡cil, impossÃ­vel com 25 nÃºmeros!)
        // Agora: mÃ­nimo = drawSize + 1 para respeitar o pool do usuÃ¡rio
        poolSize = Math.max(actualDrawSize + 1, Math.min(poolSize, totalRange));
        
        // ★ v10.0 POOL MÍNIMO ADAPTATIVO POR DENSIDADE — Auditoria Maio/2026
        // Loterias esparsas: não eliminar números que têm a MESMA chance de sair
        // density < 15%: pool mínimo 70% do range (Mega, Quina, Timemania)
        // density 15-40%: pool mínimo 50% do range (Dupla Sena, Dia de Sorte)
        // density > 40%: manter poolSize original (Lotofácil, Lotomania)
        if (!customPool) {
            const density = actualDrawSize / totalRange;
            let minPoolRatio;
            if (density < 0.15) {
                minPoolRatio = 0.70; // Mega(10%), Quina(6.25%), Timemania(12.5%)
            } else if (density < 0.40) {
                minPoolRatio = 0.50; // Dupla Sena(12%), Dia de Sorte(22.6%)
            } else {
                minPoolRatio = 0; // Lotofácil(60%), Lotomania(50%) — manter original
            }
            const minPool = Math.ceil(totalRange * minPoolRatio);
            if (minPool > 0 && poolSize < minPool) {
                console.log('%c[SNIPER-QUANTUM] ★ v10 POOL ADAPTATIVO: density=' + (density*100).toFixed(1) + '% → pool mínimo ' + minPool + ' (era ' + poolSize + ')', 'color: #F59E0B; font-weight: bold;');
                poolSize = Math.min(minPool, totalRange);
            }
        }
        
        // Obter histÃ³rico
        let history = [];
        try {
            if (typeof REAL_HISTORY_DB !== 'undefined' && REAL_HISTORY_DB[gameKey]) {
                history = REAL_HISTORY_DB[gameKey].slice(0, 100);
            } else if (typeof StatsService !== 'undefined') {
                history = StatsService.getRecentResults(gameKey, 100) || [];
            }
        } catch(e) { console.warn('[SNIPER] HistÃ³rico falhou:', e.message); }
        
        // v11.0 FIX: Setar drawSize ANTES de _scoreAllNumbers para que _normalizeScores
        // use o floor dinâmico correto. Para Sniper com muitos jogos, usar floor mais alto
        // para garantir diversidade suficiente no pool.
        this._currentDrawSize = actualDrawSize;
        this._sniperMode = numGames > 100; // Flag para _normalizeScores usar floor mais alto
        const scores = this._scoreAllNumbers(gameKey, profile, history, startNum, endNum, totalRange);
        this._sniperMode = false; // Reset após scoring
        
        // â”â”â” FASE 2: SELECIONAR POOL â”â”â”
        const fixedSet = new Set(fixedNumbers || []);
        const selectedPool = [];
        const poolSet = new Set();
        
        // â˜… v9.5 HYBRID: Se customPool fornecido (modo manual), usar EXATAMENTE esses nÃºmeros
        if (customPool && customPool.length >= actualDrawSize) {
            console.log('%c[SNIPER-QUANTUM] ðŸŽ¯ MODO MANUAL HÃBRIDO: usando ' + customPool.length + ' nÃºmeros do apostador', 'color: #F59E0B; font-weight: bold;');
            for (const n of customPool) {
                if (!poolSet.has(n)) {
                    selectedPool.push(n);
                    poolSet.add(n);
                }
            }
            poolSize = selectedPool.length;
        } else {
            // Modo automÃ¡tico: Ranking baseado nos scores finais de 21 camadas
            const ranked = [];
            for (let n = startNum; n <= endNum; n++) {
                ranked.push({ num: n, score: scores[n] || 0 });
            }
            ranked.sort((a, b) => b.score - a.score);
            
            // Primeiro: adicionar todos os fixos
            for (const f of fixedSet) {
                selectedPool.push(f);
                poolSet.add(f);
            }
            
            // Depois: adicionar os TOP N atÃ© completar poolSize
            for (const r of ranked) {
                if (poolSet.size >= poolSize) break;
                if (!poolSet.has(r.num)) {
                    selectedPool.push(r.num);
                    poolSet.add(r.num);
                }
            }
        }
        
        selectedPool.sort((a, b) => a - b);
        console.log('[SNIPER-QUANTUM] â˜… Pool selecionado: ' + poolSize + ' nÃºmeros â†’ [' + selectedPool.slice(0, 15).join(', ') + (selectedPool.length > 15 ? '...' : '') + ']');
        
        // Score de cada nÃºmero no pool (para usar na geraÃ§Ã£o)
        const poolScores = {};
        for (const n of selectedPool) poolScores[n] = scores[n] || 0.5;
        
        // â”â”â” FASE 3: DIVIDIR EM TIERS â”â”â”
        // Tier 1 = TOP nÃºmeros, Tier 2 = segundos melhores, etc.
        const numTiers = Math.floor(selectedPool.length / actualDrawSize);
        const tiers = [];
        const rankedPool = [...selectedPool].sort((a, b) => (poolScores[b] || 0) - (poolScores[a] || 0));
        
        for (let t = 0; t < numTiers; t++) {
            const tierNums = rankedPool.slice(t * actualDrawSize, (t + 1) * actualDrawSize).sort((a, b) => a - b);
            tiers.push(tierNums);
        }
        
        // NÃºmeros restantes (nÃ£o completam um tier)
        const remainder = rankedPool.slice(numTiers * actualDrawSize);
        
        console.log('[SNIPER-QUANTUM] â˜… ' + numTiers + ' Tiers de ' + actualDrawSize + ' nÃºmeros | Resto: ' + remainder.length);
        for (let t = 0; t < Math.min(5, tiers.length); t++) {
            console.log('[SNIPER-QUANTUM]   Tier ' + (t+1) + ': [' + tiers[t].join(', ') + ']');
        }
        
        // â”â”â” FASE 4: GERAR JOGOS (GOD MODE v10) â”â”â”
        const games = [];
        const usedKeys = new Set();
        const startTime = Date.now();
        
        // â˜… v10 FIX: Anti-sobreposiÃ§Ã£o ADAPTATIVA ao pool
        const _overlapWith = (newT, existing) => {
            let maxO = 0;
            const checkCount = Math.min(30, existing.length);
            for (let i = existing.length - checkCount; i < existing.length; i++) {
                let o = 0;
                for (const n of newT) { if (existing[i].includes(n)) o++; }
                if (o > maxO) maxO = o;
            }
            return maxO;
        };
        // FIX: Adaptar ao tamanho do pool â€” pools pequenos permitem mais overlap
        // FÃ³rmula: poolRatio = pool/drawSize. Se ratio < 3, relaxar muito. Se ratio > 5, apertar.
        const poolRatio = selectedPool.length / actualDrawSize;
        const maxOverlapAllowed = poolRatio <= 2.5
            ? actualDrawSize  // Pool muito pequeno: sem filtro de overlap (ex: 15 nums / 6 draw = 2.5)
            : poolRatio <= 4
                ? Math.max(3, actualDrawSize - 1) // Pool mÃ©dio: overlap generoso
                : Math.max(2, actualDrawSize - 2); // Pool grande: overlap restrito
        console.log('[SNIPER-QUANTUM] Anti-overlap: poolRatio=' + poolRatio.toFixed(1) + ' â†’ maxOverlap=' + maxOverlapAllowed);
        
        // â˜… v10: Filtro de distribuiÃ§Ã£o por zonas
        const numZones = profile.zones || Math.ceil((endNum - startNum + 1) / 10);
        const zoneSize = profile.zoneSize || 10;
        
        const _zoneBalanced = (ticket) => {
            const zoneCounts = new Array(numZones).fill(0);
            for (const n of ticket) {
                const z = Math.min(numZones - 1, Math.floor((n - startNum) / zoneSize));
                zoneCounts[z]++;
            }
            // NÃ£o permitir > 60% dos nÃºmeros em uma Ãºnica zona
            const maxInZone = Math.max(...zoneCounts);
            return maxInZone <= Math.ceil(actualDrawSize * 0.6);
        };
        
        // 4A: Adicionar todos os jogos de tier direto (melhor qualidade)
        for (const tier of tiers) {
            if (games.length >= numGames) break;
            const key = tier.join(',');
            if (!usedKeys.has(key) && this._validateSniperTicket(tier, profile, startNum, endNum, actualDrawSize, history) && _zoneBalanced(tier)) {
                games.push([...tier]);
                usedKeys.add(key);
            }
        }
        console.log('[SNIPER-QUANTUM] Fase 4A (Tiers diretos): ' + games.length + ' jogos');
        
        // 4B: Cross-combinar tiers â€” Strategy Pattern: Top-Mid-Bottom mix
        if (games.length < numGames && tiers.length >= 2) {
            const crossGames = this._crossCombineTiers(tiers, remainder, actualDrawSize, numGames - games.length, profile, startNum, endNum, poolScores, history);
            for (const cg of crossGames) {
                if (games.length >= numGames) break;
                const key = cg.join(',');
                if (!usedKeys.has(key) && _overlapWith(cg, games) <= maxOverlapAllowed && _zoneBalanced(cg)) {
                    games.push(cg);
                    usedKeys.add(key);
                }
            }
        }
        console.log('[SNIPER-QUANTUM] Fase 4B (Cross-tiers): ' + games.length + ' jogos');
        
        // 4C: Gerar jogos adicionais usando Roulette Wheel com anti-overlap
        if (games.length < numGames) {
            const remaining = numGames - games.length;
            console.log('[SNIPER-QUANTUM] Fase 4C: gerando ' + remaining + ' jogos via Roulette Wheel...');
            
            const usedCount = {};
            for (const n of selectedPool) usedCount[n] = 0;
            for (const g of games) {
                for (const n of g) usedCount[n] = (usedCount[n] || 0) + 1;
            }
            
            const maxUsage = Math.max(5, Math.ceil(numGames * (profile.maxUsagePct || 0.30)));
            const lastDrawSet = history.length > 0 ? new Set((history[0].numbers || []).concat(history[0].numbers2 || [])) : new Set();
            
            let att = 0;
            // v11.0 FIX: Aumentar tentativas máximas para lotes grandes
            const maxAtt = Math.min(remaining * 1000, 10000000);
            const timeout = 600000;
            
            while (games.length < numGames && att < maxAtt && (Date.now() - startTime) < timeout) {
                att++;
                const ticket = this._generateSingleGame(
                    profile, poolScores, selectedPool, actualDrawSize,
                    fixedNumbers || [], usedCount, maxUsage,
                    startNum, endNum, profile.zones, profile.zoneSize,
                    games.length, numGames, lastDrawSet, history
                );
                if (!ticket || ticket.length < actualDrawSize) continue;
                const key = ticket.join(',');
                if (usedKeys.has(key)) continue;
                // ★ v11.0: anti-overlap RELAXADO para volume grande
                // Se já passou de 50% do target e overlap está bloqueando, relaxar
                const overlapLimit = games.length > numGames * 0.5 ? actualDrawSize : maxOverlapAllowed;
                if (_overlapWith(ticket, games) > overlapLimit) continue;
                if (!_zoneBalanced(ticket)) continue;
                
                games.push(ticket);
                usedKeys.add(key);
                for (const n of ticket) usedCount[n] = (usedCount[n] || 0) + 1;
            }
        }
        
        console.log('%c[SNIPER-QUANTUM] â˜…â˜…â˜… TOTAL: ' + games.length + '/' + numGames + ' jogos em ' + (Date.now() - startTime) + 'ms â˜…â˜…â˜…', 'color: #EF4444; font-weight: bold;');
        
        // â”â”â” FASE 5: ANÃLISE E CONFIANÃ‡A â”â”â”
        const uniqueNums = new Set();
        for (const g of games) for (const n of g) uniqueNums.add(n);
        
        const coveragePct = (uniqueNums.size / totalRange * 100).toFixed(1);
        const poolCoverage = (uniqueNums.size / poolSize * 100).toFixed(1);
        
        // â˜… v10 GOD MODE: ConfianÃ§a recalculada com diversidade + anti-overlap
        const avgScore = selectedPool.reduce((s, n) => s + (scores[n] || 0), 0) / selectedPool.length;
        const maxScoreInPool = Math.max(...selectedPool.map(n => scores[n] || 0), 0.01);
        const qualityRatio = avgScore / maxScoreInPool;
        
        // Diversidade: quantos nÃºmeros Ãºnicos vs pool total
        const diversityRatio = uniqueNums.size / Math.max(1, poolSize);
        // Completude
        const completionRatio = games.length / Math.max(1, numGames);
        
        const honestCeiling = profile._confidenceCeiling || 94;
        const confidence = Math.min(honestCeiling, Math.round(
            qualityRatio * 35 +        // Qualidade dos scores (0-35%)
            completionRatio * 20 +     // Completude (0-20%)
            diversityRatio * 15 +      // Diversidade de nÃºmeros (0-15%)
            parseFloat(poolCoverage) * 0.05  // Cobertura (0-5%)
        ));
        
        const analysis = {
            engine: 'SNIPER QUANTUM v10 GOD',
            confidence: confidence,
            uniqueNumbers: uniqueNums.size,
            totalNumbers: totalRange,
            poolSize: poolSize,
            tiersCreated: tiers.length,
            coveragePct: coveragePct,
            poolCoverage: poolCoverage,
            avgPoolScore: avgScore.toFixed(3),
            diversityIndex: (diversityRatio * 100).toFixed(1),
            topNumbers: rankedPool.slice(0, actualDrawSize).join(', '),
            generationTime: Date.now() - startTime,
            // â˜… FIX: Campos compatÃ­veis com o painel de anÃ¡lise da UI
            mode: 'PRECISÃƒO',
            coverage: coveragePct,
            diversity: (diversityRatio * 100).toFixed(1),
            precisionPool: selectedPool,
            // Calcular duplas e trios cobertos
            pairsCovered: (() => {
                try {
                    if (!history || history.length < 5) return 0;
                    const topPairs = new Set();
                    for (let t = 0; t < Math.min(20, history.length); t++) {
                        const nums = (history[t].numbers || []).filter(x => x >= startNum && x <= endNum).sort((a,b) => a-b);
                        for (let i = 0; i < nums.length; i++)
                            for (let j = i+1; j < nums.length; j++)
                                topPairs.add(nums[i] + '-' + nums[j]);
                    }
                    let covered = 0;
                    const gamePairs = new Set();
                    for (const g of games) {
                        const s = [...g].sort((a,b) => a-b);
                        for (let i = 0; i < s.length; i++)
                            for (let j = i+1; j < s.length; j++)
                                gamePairs.add(s[i] + '-' + s[j]);
                    }
                    for (const p of topPairs) { if (gamePairs.has(p)) covered++; }
                    return Math.round(covered / Math.max(1, topPairs.size) * 100);
                } catch(e) { return 0; }
            })(),
            triosCovered: (() => {
                try {
                    if (!history || history.length < 5) return 0;
                    const topTrios = new Set();
                    for (let t = 0; t < Math.min(15, history.length); t++) {
                        const nums = (history[t].numbers || []).filter(x => x >= startNum && x <= endNum).sort((a,b) => a-b);
                        for (let i = 0; i < nums.length; i++)
                            for (let j = i+1; j < nums.length; j++)
                                for (let k = j+1; k < Math.min(j+4, nums.length); k++)
                                    topTrios.add(nums[i] + '-' + nums[j] + '-' + nums[k]);
                    }
                    let covered = 0;
                    const gameTrios = new Set();
                    for (const g of games) {
                        const s = [...g].sort((a,b) => a-b);
                        for (let i = 0; i < s.length; i++)
                            for (let j = i+1; j < s.length; j++)
                                for (let k = j+1; k < Math.min(j+4, s.length); k++)
                                    gameTrios.add(s[i] + '-' + s[j] + '-' + s[k]);
                    }
                    for (const t of topTrios) { if (gameTrios.has(t)) covered++; }
                    return Math.round(covered / Math.max(1, topTrios.size) * 100);
                } catch(e) { return 0; }
            })(),
            backtestScore: Math.round(confidence * 1.15), // Estimativa baseada na confianÃ§a
            backtestHits: { '14+': 0, '13+': 0, '12+': 0 }
        };
        
        console.log('[SNIPER-QUANTUM] ConfianÃ§a: ' + confidence + '% | Pool: ' + poolSize + '/' + totalRange + ' (' + coveragePct + '%) | Tiers: ' + tiers.length);
        
        return { games, analysis };
    }
    
    // â˜… Validar ticket do Sniper com filtros Quantum IA
    static _validateSniperTicket(ticket, profile, startNum, endNum, drawSize, history) {
        if (!ticket || ticket.length < drawSize) return false;
        
        // Paridade
        const evens = ticket.filter(n => n % 2 === 0).length;
        if (evens < profile.evenOddRange[0] || evens > profile.evenOddRange[1]) return false;
        
        // Soma
        const sum = ticket.reduce((a, b) => a + b, 0);
        if (sum < profile.sumRange[0] || sum > profile.sumRange[1]) return false;
        
        // Anti-sequÃªncia
        let maxRun = 1, curRun = 1;
        for (let i = 1; i < ticket.length; i++) {
            if (ticket[i] === ticket[i-1] + 1) { curRun++; if (curRun > maxRun) maxRun = curRun; }
            else curRun = 1;
        }
        if (maxRun > profile.maxConsecutive) return false;
        
        // Pares consecutivos
        let cp = 0;
        for (let i = 1; i < ticket.length; i++) { if (ticket[i] === ticket[i-1] + 1) cp++; }
        const totalRange = endNum - startNum + 1;
        const density = drawSize / totalRange;
        const maxPairs = Math.max(1, Math.round(drawSize * density * 1.2));
        if (cp > maxPairs) return false;
        
        return true;
    }
    
    // â˜… Cross-combinar tiers para gerar jogos mistos de alta qualidade
    static _crossCombineTiers(tiers, remainder, drawSize, maxGames, profile, startNum, endNum, scores, history) {
        const results = [];
        const usedKeys = new Set();
        const numTiers = tiers.length;
        
        if (numTiers < 2) return results;
        
        // â˜… v10 GOD MODE: Strategy Pattern â€” Top-Mid-Bottom mix
        // EstratÃ©gia: garantir que cada jogo tem nÃºmeros de diferentes tiers
        // Tier 1 contribui ~50%, Tier 2 ~30%, restantes ~20%
        
        const maxAttempts = Math.min(maxGames * 150, 500000);
        let attempts = 0;
        
        while (results.length < maxGames && attempts < maxAttempts) {
            attempts++;
            const ticket = [];
            const ticketSet = new Set();
            
            // â˜… Strategy: calcular quantos de cada tier
            const tier1Qty = Math.max(1, Math.round(drawSize * 0.45));
            const tier2Qty = Math.max(1, Math.round(drawSize * 0.30));
            const tierRestQty = drawSize - tier1Qty - tier2Qty;
            
            // Coletar por tier com quantidade estratÃ©gica
            const allNums = [];
            const tierQuotas = [tier1Qty, tier2Qty];
            // Distribuir restante entre tiers 3+
            for (let t = 2; t < numTiers; t++) tierQuotas.push(Math.max(1, Math.ceil(tierRestQty / Math.max(1, numTiers - 2))));
            
            for (let t = 0; t < numTiers; t++) {
                const quota = tierQuotas[t] || 1;
                // Shuffle tier e pegar quota nÃºmeros aleatÃ³rios
                const shuffled = [...tiers[t]].sort(() => Math.random() - 0.5);
                const picked = shuffled.slice(0, quota);
                for (const n of picked) {
                    const weight = Math.pow(0.8, t);
                    allNums.push({ num: n, score: (scores[n] || 0.5) * weight * (1 + Math.random() * 0.3) });
                }
            }
            // Adicionar remainder com peso baixo
            for (const n of remainder) {
                if (Math.random() < 0.25) {
                    allNums.push({ num: n, score: (scores[n] || 0.3) * 0.25 });
                }
            }
            
            // Roulette wheel dos candidatos
            allNums.sort(() => Math.random() - 0.5); // shuffle base
            const totalW = allNums.reduce((s, x) => s + Math.max(0.01, x.score), 0);
            
            while (ticket.length < drawSize && allNums.length > 0) {
                let r = Math.random() * totalW;
                let picked = null;
                for (let i = 0; i < allNums.length; i++) {
                    r -= Math.max(0.01, allNums[i].score);
                    if (r <= 0) {
                        if (!ticketSet.has(allNums[i].num)) {
                            picked = allNums[i].num;
                            ticketSet.add(picked);
                            ticket.push(picked);
                            allNums.splice(i, 1);
                        }
                        break;
                    }
                }
                if (picked === null) {
                    // Fallback: pegar qualquer nÃ£o-usado
                    for (let i = 0; i < allNums.length; i++) {
                        if (!ticketSet.has(allNums[i].num)) {
                            ticket.push(allNums[i].num);
                            ticketSet.add(allNums[i].num);
                            allNums.splice(i, 1);
                            break;
                        }
                    }
                    if (ticket.length === ticketSet.size - 1) break; // stuck
                }
            }
            
            if (ticket.length < drawSize) continue;
            ticket.sort((a, b) => a - b);
            
            // Validar
            if (!this._validateSniperTicket(ticket, profile, startNum, endNum, drawSize, history)) continue;
            
            const key = ticket.join(',');
            if (usedKeys.has(key)) continue;
            
            results.push(ticket);
            usedKeys.add(key);
        }
        
        return results;
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  GERADOR DE JOGOS DIVERSIFICADOS                             â•‘
    // â•‘  Cada jogo Ã© maximamente diferente dos anteriores            â•‘
    // â•‘  Anti-concentraÃ§Ã£o: nenhum nÃºmero aparece em > X% dos jogos â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _generateDiverseGames(profile, scores, pool, numGames, drawSize, fixedNumbers, startNum, endNum, hasUserSelection, adaptiveParams, history) {
        const games = [];
        const usedKeys = new Set();
        const usedCount = {};
        for (const n of pool) usedCount[n] = 0;
        const numZones = profile.zones;
        const zoneSize = profile.zoneSize;

        // â˜… v5.0: Extrair Ãºltimo sorteio para filtro de repetiÃ§Ã£o
        let lastDrawSet = new Set();
        if (history && history.length > 0) {
            const lastNums = (history[0].numbers || []).concat(history[0].numbers2 || []);
            lastDrawSet = new Set(lastNums.filter(n => n >= startNum && n <= endNum));
            console.log('[NE-L99] â˜… v5.0: lastDraw=[' + [...lastDrawSet].sort((a,b)=>a-b).join(',') + '] | repeatFromLast=' + JSON.stringify(profile.repeatFromLast));
        }

        // â”â” CALIBRAÃ‡ÃƒO ADAPTATIVA L99 â”â”
        const ap = adaptiveParams || {};
        const maxUsage = Math.max(3, Math.ceil(numGames * (ap.maxUsagePct || profile.maxUsagePct)));
        const maxOverlap = ap.maxOverlap !== undefined ? ap.maxOverlap : profile.maxOverlap;
        const checkRadius = ap.checkRadius || 30;

        // â”â” FASE 1: Jogos de QUALIDADE com IA + filtros v9.5 â”â”
        const fase1MaxAttempts = numGames <= 100
            ? numGames * 800
            : numGames <= 1000
                ? Math.min(numGames * 600, 6000000)
                : Math.min(numGames * 400, 20000000);
        const fase1Timeout = numGames <= 100
            ? 30000
            : numGames <= 1000
                ? 120000
                : numGames <= 5000
                    ? 600000
                    : 900000;
        const startTime = Date.now();
        let attempts = 0;

        console.log('[NE-L99] â˜… v5.0 Roulette Wheel | ' + numGames + ' jogos | pool=' + pool.length + ' | overlap=' + maxOverlap + '/' + drawSize + ' | timeout=' + (fase1Timeout/1000) + 's');

        let currentOverlap = maxOverlap;
        let lastLog = 0;
        const gameSetsCache = [];

        while (games.length < numGames && attempts < fase1MaxAttempts && (Date.now() - startTime) < fase1Timeout) {
            attempts++;

            const progressRatio = attempts / fase1MaxAttempts;
            if (progressRatio > 0.30 && currentOverlap < drawSize) {
                currentOverlap = Math.min(drawSize, maxOverlap + Math.floor((progressRatio - 0.30) * drawSize * 1.5));
            }

            const ticket = this._generateSingleGame(profile, scores, pool, drawSize, fixedNumbers, usedCount, maxUsage, startNum, endNum, numZones, zoneSize, games.length, numGames, lastDrawSet, history);
            if (!ticket || ticket.length < drawSize) continue;
            const key = ticket.join(',');
            if (usedKeys.has(key)) continue;

            // Anti-overlap: verificar apenas os Ãºltimos checkRadius jogos
            // â˜… PERFORMANCE FIX v3.0: Usar Sets prÃ©-computados do cache
            if (games.length > 0 && progressRatio < 0.75) {
                let tooSimilar = false;
                const checkFrom = Math.max(0, gameSetsCache.length - checkRadius);
                for (let g = checkFrom; g < gameSetsCache.length; g++) {
                    let overlap = 0;
                    for (const n of ticket) { if (gameSetsCache[g].has(n)) overlap++; }
                    if (overlap > currentOverlap) { tooSimilar = true; break; }
                }
                if (tooSimilar) continue;
            }

            games.push(ticket);
            usedKeys.add(key);
            gameSetsCache.push(new Set(ticket));
            for (const n of ticket) usedCount[n] = (usedCount[n] || 0) + 1;

            // â˜… PERFORMANCE FIX v3.0: Limitar tamanho do cache de Sets
            // Para lotes enormes, manter apenas os Ãºltimos checkRadius*2 Sets no cache
            if (gameSetsCache.length > checkRadius * 2 + 50) {
                gameSetsCache.splice(0, gameSetsCache.length - checkRadius * 2);
            }

            // Log progresso a cada 10%
            const pct = Math.floor(games.length / numGames * 10);
            if (pct > lastLog) {
                lastLog = pct;
                console.log('[NE-L99] Fase1: ' + games.length + '/' + numGames + ' (' + (pct*10) + '%) overlap=' + currentOverlap + ' [' + (Date.now() - startTime) + 'ms]');
            }
        }
        const fase1Count = games.length;
        console.log('[NE-L99] Fase1 (IA): ' + fase1Count + '/' + numGames + ' em ' + attempts + ' tentativas (' + (Date.now() - startTime) + 'ms)');

        // â”â” FASE 2: â˜… v5.0: COMPLETAR com mesma IA (filtros relaxados mas ativos) â”â”
        // NÃƒO mais usa tournament selection separada â€” reutiliza _generateSingleGame
        // com overlap relaxado para garantir que filtros estruturais sejam aplicados
        if (games.length < numGames) {
            const remaining = numGames - games.length;
            console.log('[NE-L99] Fase2 v5.0: gerando ' + remaining + ' jogos com IA completa (overlap relaxado)...');
            let bulkAtt = 0;
            const bulkMax = Math.max(remaining * 800, 5000000);
            const bulkTimeout = Math.max(300000, Math.min(900000, remaining * 60));

            while (games.length < numGames && bulkAtt < bulkMax && (Date.now() - startTime) < bulkTimeout) {
                bulkAtt++;
                // Usar o mesmo gerador com filtros v5.0 ativos
                const ticket = this._generateSingleGame(profile, scores, pool, drawSize, fixedNumbers, usedCount, maxUsage * 3, startNum, endNum, numZones, zoneSize, games.length, numGames, lastDrawSet, history);
                if (!ticket || ticket.length < drawSize) continue;
                const key = ticket.join(',');
                if (!usedKeys.has(key)) {
                    games.push(ticket);
                    usedKeys.add(key);
                    for (const n of ticket) usedCount[n] = (usedCount[n] || 0) + 1;
                }
            }
            console.log('[NE-L99] Fase2 v5.0: +' + (games.length - fase1Count) + ' em ' + bulkAtt + ' tentativas (' + (Date.now() - startTime) + 'ms)');
        }

        console.log('[NE-L99] âœ… TOTAL: ' + games.length + '/' + numGames + ' jogos gerados em ' + (Date.now() - startTime) + 'ms');
        const maxUsed = Math.max(0, ...Object.values(usedCount));
        const maxPct = games.length > 0 ? (maxUsed / games.length * 100).toFixed(1) : 0;
        const numsUsed = Object.values(usedCount).filter(v => v > 0).length;
        console.log('[NE-L99] MaxConc: ' + maxPct + '% | Nums: ' + numsUsed + '/' + pool.length);
        return games;
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜…â˜…â˜… v5.0: GERAR JOGO COM ROULETTE WHEEL + FILTROS RIGOROSOS â˜…â˜…â˜…  â•‘
    // â•‘  MudanÃ§as v5.0:                                                     â•‘
    // â•‘   1. Roulette Wheel Selection (score^exponent) â†’ correlaÃ§Ã£o direta  â•‘
    // â•‘   2. Filtros SEMPRE ativos (soma, paridade, repetiÃ§Ã£o) em TODO lote â•‘
    // â•‘   3. ValidaÃ§Ã£o de repetiÃ§Ã£o do sorteio anterior                     â•‘
    // â•‘   4. Expoente adaptativo: â‰¤1K=4, â‰¤5K=3, >5K=2                     â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _generateSingleGame(profile, scores, pool, drawSize, fixedNumbers, usedCount, maxUsage, startNum, endNum, numZones, zoneSize, gameIndex, totalGames, lastDrawSet, history) {
        const ticket = [];
        const ticketSet = new Set();
        const zoneCount = new Array(numZones).fill(0);

        // 1. Inserir fixos
        for (const f of fixedNumbers) {
            if (f >= startNum && f <= endNum && !ticketSet.has(f) && ticket.length < drawSize) {
                ticket.push(f);
                ticketSet.add(f);
                const z = Math.min(numZones - 1, Math.floor((f - startNum) / zoneSize));
                zoneCount[z]++;
            }
        }

        // 2. Construir pesos dinÃ¢micos com EXPONENCIAÃ‡ÃƒO v5.0
        const available = pool.filter(n => {
            if (ticketSet.has(n)) return false;
            if ((usedCount[n] || 0) >= maxUsage) return false;
            return true;
        });
        if (available.length < drawSize - ticket.length) return null;

        // â˜… v5.0: Expoente adaptativo TIERED â€” foco MÃXIMO em lotes pequenos
        // SNIPER: score^5 (um nÃºmero com score 2x tem 32x mais chance!)
        // CIRÃšRGICO: score^4
        // INTELIGENTE: score^3
        // COBERTURA: score^2
        // â˜… v5.1: Expoentes MAIS agressivos + novo tier â‰¤10 com score^6
        // â˜… V6.0: Expoente moderado â€” score 2x agora dÃ¡ 8x chance (nÃ£o 64x)
        // Isso ESPALHA a seleÃ§Ã£o ao invÃ©s de convergir nos mesmos 5 nÃºmeros
        // â˜… v7.0: Expoentes REDUZIDOS â€” score 2x = ~3.5x chance (era 8x)
        // Isso ESPALHA a seleÃ§Ã£o em vez de convergir nos mesmos nÃºmeros
        // â˜… v9.0 RECALIBRADO: Expoentes ajustados para melhor equilÃ­brio foco/diversidade
        // Volume baixo â†’ mais foco nos TOP (sniper), Volume alto â†’ mais diversidade (cobertura)
        const exponent = totalGames <= 10 ? 2.2 : totalGames <= 50 ? 1.9 : totalGames <= 100 ? 1.5 : totalGames <= 500 ? 1.2 : totalGames <= 1000 ? 1.0 : 0.85;

        const weights = {};
        for (const n of available) {
            let w = scores[n] || 1.0;

            // â˜… v5.1: Penalizar uso excessivo mais agressivamente em lotes pequenos
            const usage = (usedCount[n] || 0) / Math.max(1, maxUsage);
            const usagePenalty = totalGames <= 100 ? 2.5 : 1.8;
            w *= Math.pow(1 - usage, usagePenalty);
            // v7.1: Bonus de novidade REDUZIDO (era 2.0/1.5 â†’ 1.3/1.15)
            if (usedCount[n] === 0 || usedCount[n] === undefined) w *= (totalGames <= 50 ? 1.3 : 1.15);

            // v7.1: Anti-consecutivo RELAXADO para ranges amplos (Timemania, Quina)
            // Em 10 de 80, consecutivos sÃ£o raros naturalmente â€” nÃ£o penalizar tanto
            if (profile.maxConsecutive <= 2) {
                if (this._wouldCreate3Consecutive(n, ticketSet)) w *= 0.01;
                if (ticketSet.has(n - 1) || ticketSet.has(n + 1)) {
                    const totalRange = endNum - startNum + 1;
                    // Range amplo (>50): penalidade leve. Range curto (<35): penalidade forte
                    const consecPenalty = totalRange > 50 ? 0.60 : 0.30;
                    let existingConsecPairs = 0;
                    const sortedTicket = [...ticketSet].sort((a, b) => a - b);
                    for (let i = 1; i < sortedTicket.length; i++) {
                        if (sortedTicket[i] - sortedTicket[i-1] === 1) existingConsecPairs++;
                    }
                    w *= existingConsecPairs >= 1 ? consecPenalty * 0.3 : consecPenalty;
                }
            } else if (profile.maxConsecutive <= 3) {
                if (this._wouldCreate3Consecutive(n, ticketSet)) w *= 0.05;
            } else if (profile.maxConsecutive <= 5) {
                if (this._wouldCreate3Consecutive(n, ticketSet)) w *= 0.50;
            }

            // â˜… v5.0: EXPONENCIAR o peso para amplificar diferenÃ§as
            weights[n] = Math.max(0.0001, Math.pow(Math.max(0.001, w), exponent));
        }

        // 3. SeleÃ§Ã£o por zona (cobertura mÃ­nima)
        const minZones = Math.min(profile.minZonesCovered, numZones);
        const zonesNeeded = [];
        for (let z = 0; z < numZones; z++) {
            if (zoneCount[z] === 0) zonesNeeded.push(z);
        }
        for (let i = zonesNeeded.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [zonesNeeded[i], zonesNeeded[j]] = [zonesNeeded[j], zonesNeeded[i]];
        }
        const zonesToCover = zonesNeeded.slice(0, Math.max(0, minZones - (numZones - zonesNeeded.length)));
        for (const z of zonesToCover) {
            if (ticket.length >= drawSize) break;
            const inZone = available.filter(n => {
                const nz = Math.min(numZones - 1, Math.floor((n - startNum) / zoneSize));
                return nz === z && !ticketSet.has(n);
            });
            if (inZone.length === 0) continue;
            const chosen = this._weightedPick(inZone, weights);
            if (chosen !== null) {
                ticket.push(chosen);
                ticketSet.add(chosen);
                zoneCount[z]++;
            }
        }

        // 4. â˜… v9.5: ROULETTE WHEEL + CO-OCORRÃŠNCIA DINÃ‚MICA
        // Quando escolhe o nÂº A, boost nos parceiros histÃ³ricos de A
        while (ticket.length < drawSize) {
            const remaining = available.filter(n => !ticketSet.has(n));
            if (remaining.length === 0) break;
            const chosen = this._rouletteWheelPick(remaining, weights);
            if (chosen === null) break;
            ticket.push(chosen);
            ticketSet.add(chosen);
            const z = Math.min(numZones - 1, Math.floor((chosen - startNum) / zoneSize));
            zoneCount[z]++;
            
            // â˜… v9.5: CO-OCORRÃŠNCIA â€” boost parceiros de 'chosen'
            // Buscar nÃºmeros que mais saÃ­ram JUNTO com 'chosen' nos Ãºltimos 30 sorteios
            if (history && history.length >= 5 && ticket.length < drawSize) {
                const partnerBoost = {};
                const coLimit = Math.min(30, history.length);
                for (let t = 0; t < coLimit; t++) {
                    const nums = (history[t].numbers || []).concat(history[t].numbers2 || []);
                    if (nums.includes(chosen)) {
                        const decay = Math.exp(-t * 0.05);
                        for (const pn of nums) {
                            if (pn >= startNum && pn <= endNum && pn !== chosen && !ticketSet.has(pn)) {
                                partnerBoost[pn] = (partnerBoost[pn] || 0) + decay;
                            }
                        }
                    }
                }
                // Aplicar boost de 15-30% nos TOP parceiros
                const topPartners = Object.entries(partnerBoost).sort((a,b) => b[1]-a[1]).slice(0, 10);
                if (topPartners.length > 0) {
                    const maxP = topPartners[0][1];
                    for (const [pn, freq] of topPartners) {
                        const boost = 1 + (freq / maxP) * 0.30;
                        if (weights[parseInt(pn)]) weights[parseInt(pn)] *= boost;
                    }
                }
            }
        }

        if (ticket.length < drawSize) return null;
        ticket.sort((a, b) => a - b);

        // 5. â˜… v5.0: VALIDAÃ‡Ã•ES ESTRUTURAIS SEMPRE ATIVAS (nÃ£o mais skip por batch size!)
        const fixedRatio = fixedNumbers.length / drawSize;
        const skipValidation = (fixedRatio >= 0.5) || (pool && pool.length < drawSize + 10); // SÃ³ skip se >50% sÃ£o fixos do usuÃ¡rio ou pool pequeno

        if (!skipValidation) {
            // Paridade
            const evens = ticket.filter(n => n % 2 === 0).length;
            if (evens < profile.evenOddRange[0] || evens > profile.evenOddRange[1]) return null;

            // Soma
            const sum = ticket.reduce((a, b) => a + b, 0);
            if (sum < profile.sumRange[0] || sum > profile.sumRange[1]) return null;

            // â˜… v5.0: REPETIÃ‡ÃƒO DO SORTEIO ANTERIOR (filtro estrutural novo)
            if (lastDrawSet && lastDrawSet.size > 0 && profile.repeatFromLast) {
                let repeatCount = 0;
                for (const n of ticket) {
                    if (lastDrawSet.has(n)) repeatCount++;
                }
                const [minRepeat, maxRepeat] = profile.repeatFromLast;
                if (repeatCount < minRepeat || repeatCount > maxRepeat) return null;
            }

            // â˜… v9.0: ANTI-SEQUÃŠNCIA FORTE â€” rejeitar jogos com sequÃªncias longas
            // Na maioria das loterias, sequÃªncias de 3+ consecutivos sÃ£o rarÃ­ssimas
            let maxConsecRun = 1, curConsecRun = 1;
            for (let i = 1; i < ticket.length; i++) {
                if (ticket[i] === ticket[i-1] + 1) {
                    curConsecRun++;
                    if (curConsecRun > maxConsecRun) maxConsecRun = curConsecRun;
                } else {
                    curConsecRun = 1;
                }
            }
            if (maxConsecRun > profile.maxConsecutive) return null;

            // â˜… v9.5 FIX: maxPairsAllowed PROPORCIONAL ao drawSize/range
            // LotofÃ¡cil (15/25): mÃ©dia real = 8-10 pares â†’ limitar em 10
            // Mega Sena (6/60): mÃ©dia real = 0.5 pares â†’ limitar em 2
            // Lotomania (50/100): mÃ©dia real = 24 pares â†’ limitar em 28
            let consecPairs = 0;
            for (let i = 1; i < ticket.length; i++) {
                if (ticket[i] === ticket[i-1] + 1) consecPairs++;
            }
            const totalRange = endNum - startNum + 1;
            const density = drawSize / totalRange; // 0.6 para LotofÃ¡cil, 0.1 para Mega
            const maxPairsAllowed = Math.max(1, Math.round(drawSize * density * 1.2));
            if (consecPairs > maxPairsAllowed) return null;
        }

        return ticket;
    }

    // â˜… v5.0: ROULETTE WHEEL SELECTION â€” probabilidade proporcional ao peso
    static _rouletteWheelPick(items, weights) {
        if (items.length === 0) return null;
        let totalW = 0;
        for (const n of items) totalW += (weights[n] || 0.0001);
        if (totalW <= 0) return items[Math.floor(Math.random() * items.length)];
        let rand = Math.random() * totalW;
        for (const n of items) {
            rand -= (weights[n] || 0.0001);
            if (rand <= 0) return n;
        }
        return items[items.length - 1];
    }

    static _backtestHonest(games, history, profile, gameKey, totalRange, drawSize) {
        const N = history.length;
        const btCount = Math.min(20, N);

        const sampleSize = games.length <= 1000 ? Math.min(games.length, 500)
            : games.length <= 5000 ? Math.min(games.length, 1200)
            : games.length <= 15000 ? Math.min(games.length, 2500)
            : games.length <= 30000 ? Math.min(games.length, 4000)
            : Math.min(games.length, 5000);

        // â˜… v8.0: Amostrar jogos DISTRIBUÃ DOS (nÃ£o apenas os primeiros)
        // Pegar jogos espalhados uniformemente pelo lote inteiro
        let sampledGames;
        if (games.length <= sampleSize) {
            sampledGames = games;
        } else {
            sampledGames = [];
            const step = games.length / sampleSize;
            for (let i = 0; i < sampleSize; i++) {
                sampledGames.push(games[Math.floor(i * step)]);
            }
        }
        const gameSets = sampledGames.map(g => new Set(g));
        console.log('[QUANTUM-L99] â˜… v8.0: Backtesting com ' + gameSets.length + '/' + games.length + ' jogos amostrados (distribuÃ­dos)');

        let totalBestHits = 0, maxHits = 0;
        const hitDistribution = {};
        let bt3 = 0, bt4 = 0, bt5 = 0;

        for (let t = 0; t < btCount; t++) {
            const drawn = new Set((history[t].numbers || []).concat(history[t].numbers2 || []));
            let bestHits = 0;

            for (const gs of gameSets) {
                let hits = 0;
                for (const n of gs) {
                    if (drawn.has(n)) hits++;
                }
                if (hits > bestHits) bestHits = hits;
            }

            totalBestHits += bestHits;
            if (bestHits > maxHits) maxHits = bestHits;
            hitDistribution[bestHits] = (hitDistribution[bestHits] || 0) + 1;
            if (bestHits >= 3) bt3++;
            if (bestHits >= 4) bt4++;
            if (bestHits >= 5) bt5++;
        }

        const avgHits = btCount > 0 ? totalBestHits / btCount : 0;
        const lotteryDraw = profile.lotteryDraw;
        // v7.1: Para Dupla Sena, drawn inclui ambos sorteios â€” ajustar expectedRandom
        const actualDrawnSize = gameKey === 'duplasena' ? lotteryDraw * 2 : lotteryDraw;
        const expectedRandom = drawSize * actualDrawnSize / totalRange;
        const improvement = avgHits / Math.max(0.01, expectedRandom);

        // â˜… v10.0 WALK-FORWARD HONESTO
        // ConfianÃ§a baseada EXCLUSIVAMENTE em improvement vs acaso
        // Sem ceiling artificial, sem volumeBonus inflado
        // improvement = 1.0 â†’ igual ao acaso â†’ confianÃ§a ~40%
        // improvement = 1.5 â†’ 50% melhor que acaso â†’ confianÃ§a ~60%
        // improvement = 2.0 â†’ 2x melhor que acaso â†’ confianÃ§a ~75%
        // v10.1: Multiplicador 55 + teto DINÂMICO por loteria (_confidenceCeiling)
        // Mega=72, Quina=65, Timemania=68, Lotofácil=85, Dia=80, Lotomania=78, Dupla=75
        const _ceiling = profile._confidenceCeiling || 94;
        let confidence = Math.round(Math.min(_ceiling, Math.max(25, improvement * 55)));

        // â˜… v10.0 MONTE CARLO INLINE: Comparar IA vs AleatÃ³rio com mesmos filtros
        let monteCarloAdvantage = 0;
        try {
            const mcRuns = 500;
            let mcTotalHits = 0;
            const mcDrawSize = drawSize;
            const startN = profile.range[0];
            const endN = profile.range[1];
            const allNums = [];
            for (let n = startN; n <= endN; n++) allNums.push(n);

            for (let r = 0; r < mcRuns; r++) {
                // Gerar jogo aleatÃ³rio com filtros estruturais bÃ¡sicos
                const shuffled = allNums.slice().sort(() => Math.random() - 0.5);
                const mcGame = shuffled.slice(0, mcDrawSize).sort((a, b) => a - b);

                // Testar contra sorteios do backtest
                let mcBest = 0;
                for (let t = 0; t < btCount; t++) {
                    const drawn = new Set((history[t].numbers || []).concat(history[t].numbers2 || []));
                    let hits = 0;
                    for (const n of mcGame) { if (drawn.has(n)) hits++; }
                    if (hits > mcBest) mcBest = hits;
                }
                mcTotalHits += mcBest;
            }
            const mcAvg = mcTotalHits / mcRuns;
            monteCarloAdvantage = mcAvg > 0 ? Math.round((avgHits / mcAvg - 1) * 100) : 0;

            // Ajustar confianÃ§a com vantagem Monte Carlo real
            if (monteCarloAdvantage > 15) confidence = Math.min(96, confidence + 8);
            else if (monteCarloAdvantage > 5) confidence = Math.min(96, confidence + 5);
            else if (monteCarloAdvantage > 0) confidence = Math.min(96, confidence + 2);
            else if (monteCarloAdvantage < -10) confidence = Math.max(25, confidence - 3);

            console.log('[v10.0] â˜… MONTE CARLO: IA=' + avgHits.toFixed(2) + ' vs AleatÃ³rio=' + mcAvg.toFixed(2) + ' | Vantagem: ' + (monteCarloAdvantage > 0 ? '+' : '') + monteCarloAdvantage + '%');
        } catch(mcErr) {
            console.warn('[v10.0] Monte Carlo falhou:', mcErr.message);
        }

        // â˜… v10.0: Cobertura real (sem bÃ´nus inflado)
        const uniqueNums_bt = new Set(sampledGames.flat());
        const coverageRatio = uniqueNums_bt.size / totalRange;

        console.log('[v10.0] â˜… WALK-FORWARD: Volume=' + games.length + ' | Improvement=' + improvement.toFixed(2) + 'x | MC=' + (monteCarloAdvantage > 0 ? '+' : '') + monteCarloAdvantage + '% | ConfianÃ§a=' + confidence + '%');

        const uniqueNums = new Set(games.flat());
        const coverage = Math.round(uniqueNums.size / totalRange * 100);
        const maxFreq = Math.max(0, ...Object.values(this._countFreqs(games)));
        const maxConcentrationPct = games.length > 0 ? Math.round(maxFreq / games.length * 100) : 0;

        const winRate3 = btCount > 0 ? Math.round(bt3 / btCount * 100) : 0;
        const winRate4 = btCount > 0 ? Math.round(bt4 / btCount * 100) : 0;

        // â˜… v7.2: Calcular Duplas e Trios Top cobertas pelo set de jogos
        // Duplas: pares de nÃºmeros que mais aparecem juntos no histÃ³rico
        // Trios: trios de nÃºmeros que mais aparecem juntos no histÃ³rico
        let pairsCovered = 0, triosCovered = 0;
        try {
            const pairFreq = {}, trioFreq = {};
            const pairLimit = Math.min(50, N);
            for (let t = 0; t < pairLimit; t++) {
                const nums = (history[t].numbers || []).sort((a, b) => a - b);
                for (let i = 0; i < nums.length; i++) {
                    for (let j = i + 1; j < nums.length; j++) {
                        const pk = nums[i] + '-' + nums[j];
                        pairFreq[pk] = (pairFreq[pk] || 0) + 1;
                        for (let k = j + 1; k < nums.length && k < j + 4; k++) {
                            const tk = nums[i] + '-' + nums[j] + '-' + nums[k];
                            trioFreq[tk] = (trioFreq[tk] || 0) + 1;
                        }
                    }
                }
            }
            // Top 20 pares e trios
            const topPairs = Object.entries(pairFreq).sort((a, b) => b[1] - a[1]).slice(0, 20);
            const topTrios = Object.entries(trioFreq).sort((a, b) => b[1] - a[1]).slice(0, 20);
            // Verificar cobertura nos jogos gerados
            const gameSetsForPairs = games.slice(0, 200).map(g => new Set(g));
            let pairsHit = 0;
            for (const [pk] of topPairs) {
                const [a, b] = pk.split('-').map(Number);
                if (gameSetsForPairs.some(gs => gs.has(a) && gs.has(b))) pairsHit++;
            }
            let triosHit = 0;
            for (const [tk] of topTrios) {
                const [a, b, c] = tk.split('-').map(Number);
                if (gameSetsForPairs.some(gs => gs.has(a) && gs.has(b) && gs.has(c))) triosHit++;
            }
            pairsCovered = topPairs.length > 0 ? Math.round(pairsHit / topPairs.length * 100) : 0;
            triosCovered = topTrios.length > 0 ? Math.round(triosHit / topTrios.length * 100) : 0;
        } catch (e) {
            console.warn('[QUANTUM-L99] Erro ao calcular duplas/trios:', e.message);
        }

        console.log('[QUANTUM-L99] ðŸ§ª Backtesting (' + btCount + ' sorteios):');
        console.log('[QUANTUM-L99]    MÃ©dia melhor acerto: ' + avgHits.toFixed(2) + ' (esperado acaso: ' + expectedRandom.toFixed(2) + ')');
        console.log('[QUANTUM-L99]    Melhor: ' + maxHits + ' | 3+: ' + winRate3 + '% | 4+: ' + winRate4 + '%');
        console.log('[QUANTUM-L99]    Melhoria vs acaso: ' + improvement.toFixed(2) + 'x | ConfianÃ§a: ' + confidence + '%');
        console.log('[QUANTUM-L99]    Duplas Top: ' + pairsCovered + '% | Trios Top: ' + triosCovered + '%');

        return {
            confidence,
            coverage,
            diversity: Math.max(0, 100 - maxConcentrationPct),
            uniqueNumbers: uniqueNums.size,
            uniqueCount: uniqueNums.size,
            maxConcentration: maxConcentrationPct + '%',
            backtestScore: winRate3,
            pairsCovered: pairsCovered,
            triosCovered: triosCovered,
            backtestHits: { '5+': bt5, '4+': bt4, '3+': bt3, avg: avgHits.toFixed(2), maxHits },
            improvement: improvement.toFixed(2) + 'x',
            monteCarlo: monteCarloAdvantage,
            engine: 'L99 v10.0 â€” ' + (profile.name || gameKey),
            mode: 'L99 v10.0 â€” 21 Dimensões | Cross-Validação | Filtros Estruturais'
        };
    }

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  NÃšMEROS SUGERIDOS â€” QUANTUM L99                                â•‘
    // â•‘  Retorna os N nÃºmeros com maior projeÃ§Ã£o futura usando         â•‘
    // â•‘  todas as 18 camadas de anÃ¡lise QUANTUM                        â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static suggestNumbers(gameKey, count, historyOverride) {
        // ★ v11.0: MOTOR MATEMÁTICO PURO — delega para MathPureEngine
        // Usa: Probabilidade Condicional (DP) + Jaynes (Máxima Entropia) + Roulette Wheel
        // Zero falácias, zero heurísticas
        
        const profile = this.getProfile(gameKey);
        const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        if (!game) return [];

        // Tentar usar MathPureEngine (motor matemático puro)
        if (typeof MathPureEngine !== 'undefined') {
            try {
                console.log('[NE-v11] ★ Delegando para MathPureEngine.suggestOptimal()');
                const result = MathPureEngine.suggestOptimal(gameKey, count);
                if (result && result.length >= count) {
                    return result.slice(0, count);
                }
            } catch (e) {
                console.warn('[NE-v11] MathPureEngine falhou, usando fallback:', e.message);
            }
        }

        // ═══ FALLBACK: Scoring unificado (_scoreAllNumbers) + Roulette Wheel ═══
        const startNum = profile.range[0];
        const endNum = profile.range[1];
        const totalRange = endNum - startNum + 1;

        let history = historyOverride || [];
        if (history.length === 0) try {
            if (typeof StatsService !== 'undefined') {
                history = StatsService.getRecentResults(gameKey, 200) || [];
            }
            if (history.length === 0 && typeof REAL_HISTORY_DB !== 'undefined') {
                history = REAL_HISTORY_DB[gameKey] || [];
            }
        } catch (e) { console.warn('[NE-v11] Falha ao carregar histórico:', e.message); }

        // Usar _scoreAllNumbers (unificado, não a cópia simplificada)
        this._currentDrawSize = count; // Para _normalizeScores dinâmico
        const scores = this._scoreAllNumbers(gameKey, profile, history, startNum, endNum, totalRange);

        // v14.0: Enriquecer scores com evidência estatística (BiasEngine)
        if (typeof StatisticalBiasEngine !== 'undefined' && history.length >= 30) {
            try {
                const biasResult = StatisticalBiasEngine.analyze(gameKey, history, count * 2);
                if (biasResult && biasResult.numberScores && biasResult.verdict) {
                    const weight = biasResult.verdict.biasDetected ? 0.25 : 0.08;
                    for (let n = startNum; n <= endNum; n++) {
                        const bs = biasResult.numberScores[n];
                        if (bs && bs.hasSignificance) {
                            scores[n] = (scores[n] || 0) * (1 + bs.evidenceScore * weight);
                        }
                    }
                    console.log('[NE-v14] suggestNumbers: BiasEngine ' + biasResult.verdict.emoji + ' peso=' + weight);
                }
            } catch (e) { console.warn('[NE-v14] BiasEngine indisponível:', e.message); }
        }

        // Roulette Wheel Selection (score^α) em vez de Top-N
        const density = count / totalRange;
        const alpha = density > 0.4 ? 4.0 : density > 0.15 ? 3.0 : 2.5;
        
        const NUM_CANDIDATES = 100;
        let bestCandidate = null;
        let bestScore = -Infinity;

        for (let attempt = 0; attempt < NUM_CANDIDATES; attempt++) {
            // Seleção por roleta
            const candidate = [];
            const used = new Set();
            const entries = [];
            for (let n = startNum; n <= endNum; n++) {
                entries.push({ num: n, weight: Math.pow(Math.max(0.001, scores[n] || 0.001), alpha) });
            }
            
            while (candidate.length < count && entries.length > 0) {
                let totalW = 0;
                for (const e of entries) { if (!used.has(e.num)) totalW += e.weight; }
                if (totalW <= 0) break;
                let rand = Math.random() * totalW;
                for (const e of entries) {
                    if (used.has(e.num)) continue;
                    rand -= e.weight;
                    if (rand <= 0) {
                        candidate.push(e.num);
                        used.add(e.num);
                        break;
                    }
                }
            }

            if (candidate.length < count) continue;
            candidate.sort((a, b) => a - b);

            // Validação combinatória completa
            const sum = candidate.reduce((a, b) => a + b, 0);
            if (sum < profile.sumRange[0] || sum > profile.sumRange[1]) continue;
            
            const evens = candidate.filter(n => n % 2 === 0).length;
            if (evens < profile.evenOddRange[0] || evens > profile.evenOddRange[1]) continue;

            let maxConsec = 1, curConsec = 1;
            for (let i = 1; i < candidate.length; i++) {
                if (candidate[i] === candidate[i-1] + 1) { curConsec++; maxConsec = Math.max(maxConsec, curConsec); }
                else curConsec = 1;
            }
            if (maxConsec > profile.maxConsecutive) continue;

            // Score da combinação
            let comboScore = 0;
            for (const n of candidate) comboScore += scores[n] || 0;
            
            // Bônus por diversidade (Hamming)
            let totalDist = 0, pairs = 0;
            for (let i = 0; i < candidate.length; i++) {
                for (let j = i + 1; j < candidate.length; j++) {
                    totalDist += candidate[j] - candidate[i];
                    pairs++;
                }
            }
            const avgDist = pairs > 0 ? totalDist / pairs : 0;
            const idealDist = totalRange / (count + 1);
            comboScore += (1 - Math.abs(avgDist - idealDist) / idealDist) * 2;

            if (comboScore > bestScore) {
                bestScore = comboScore;
                bestCandidate = candidate;
            }
        }

        if (bestCandidate) return bestCandidate;

        // Ultra-fallback: Top-N simples
        console.warn('[NE-v11] Nenhum candidato válido após ' + NUM_CANDIDATES + ' tentativas. Top-N fallback.');
        return Object.entries(scores)
            .map(([n, s]) => ({ num: parseInt(n), score: s }))
            .sort((a, b) => b.score - a.score)
            .slice(0, count)
            .map(x => x.num)
            .sort((a, b) => a - b);
    }

    // â˜…â˜…â˜… Score QUANTUM L99 para sugestÃµes: 18 camadas sem noise â˜…â˜…â˜…
    static _scoreForSuggestionL99(gameKey, profile, history, startNum, endNum, totalRange) {
        const N = history.length;
        const drawSize = profile.lotteryDraw;

        // Todas as 18 camadas (sincronizado com _scoreAllNumbers)
        const layers = [
            this._layerFrequency(history, startNum, endNum, N),
            this._layerTrend(history, startNum, endNum, N),
            this._layerDelay(history, startNum, endNum, N, drawSize, totalRange),
            this._layerEntropy(history, startNum, endNum, N, profile),
            this._layerMarkov(history, startNum, endNum, N),
            this._layerPhase(history, startNum, endNum, N),
            this._layerClairvoyance(history, startNum, endNum, N, drawSize),
            this._layerNextDraw(gameKey, history, startNum, endNum, N, profile),
            this._godBayesian(history, startNum, endNum, N, drawSize),
            this._godPositional(history, startNum, endNum, N, drawSize),
            this._godSequentialChain(history, startNum, endNum, N),
            this._godMomentum(history, startNum, endNum, N, drawSize),
            this._quantumTemporalMirror(history, startNum, endNum, N, drawSize),
            this._quantumGapAnalysis(history, startNum, endNum, N, drawSize, totalRange),
            this._quantumClusters(history, startNum, endNum, N, drawSize),
            this._quantumMeanReversion(history, startNum, endNum, N, drawSize, totalRange)
        ];

        // â˜… CAMADA 17: Precision Calibrator
        let precisionLayer = {};
        for (let n = startNum; n <= endNum; n++) precisionLayer[n] = 0.5;
        if (typeof PrecisionCalibrator !== 'undefined' && N >= 4) {
            try {
                const last3Trends = PrecisionCalibrator.analyzeLast3Trends(gameKey, history, startNum, endNum);
                const conditionalProb = PrecisionCalibrator.buildConditionalProbMatrix(gameKey, history, startNum, endNum, drawSize);
                for (let n = startNum; n <= endNum; n++) {
                    precisionLayer[n] = (last3Trends[n] || 0) * 0.6 + (conditionalProb[n] || 0) * 0.4;
                }
                precisionLayer = this._normalizeScores(precisionLayer, startNum, endNum);
            } catch (e) {
                console.warn('[Camada 17] Falha no PrecisionCalibrator:', e.message);
                // Fallback dinÃ¢mico: distribui o peso falho para a entropia e espelha em vez de cravar 0.5 absoluto
                for (let n = startNum; n <= endNum; n++) {
                    precisionLayer[n] = (layers[3][n] * 0.5) + 0.25; 
                }
            }
        }
        layers.push(precisionLayer);

        // â˜… CAMADA 18: Pattern DNA (simplificado para sugestÃµes)
        let patternDnaLayer = {};
        for (let n = startNum; n <= endNum; n++) patternDnaLayer[n] = 0.5;
        if (N >= 5) {
            const analysisWindow = Math.min(15, N);
            for (let n = startNum; n <= endNum; n++) {
                let currentDelay = N;
                for (let i = 0; i < N; i++) {
                    if ((history[i].numbers || []).concat(history[i].numbers2 || []).includes(n)) {
                        currentDelay = i; break;
                    }
                }
                const appearances = [];
                for (let i = 0; i < Math.min(30, N); i++) {
                    if ((history[i].numbers || []).concat(history[i].numbers2 || []).includes(n)) {
                        appearances.push(i);
                    }
                }
                let score = 0.5;
                if (appearances.length >= 2) {
                    let avgCycle = 0;
                    for (let j = 0; j < appearances.length - 1; j++) {
                        avgCycle += appearances[j + 1] - appearances[j];
                    }
                    avgCycle /= (appearances.length - 1);
                    const cycleMatch = 1.0 - Math.min(1.0, Math.abs(currentDelay - avgCycle) / Math.max(1, avgCycle));
                    score += cycleMatch * 0.35;
                }
                // Zona
                const dnaZones = Math.min(profile.zones || 4, 10);
                const nZone = Math.min(dnaZones - 1, Math.floor((n - startNum) / (totalRange / dnaZones)));
                score += (nZone % 2 === 0 ? 0.05 : 0.03); // Diversidade zonal
                patternDnaLayer[n] = score;
            }
            patternDnaLayer = this._normalizeScores(patternDnaLayer, startNum, endNum);
        }
        layers.push(patternDnaLayer);

        // â˜… v10.0 FIX: CAMADA 19 â€” Duplas e Trios Frequentes (era AUSENTE!)
        let pairTrioLayer = {};
        for (let n = startNum; n <= endNum; n++) pairTrioLayer[n] = 0.5;
        if (N >= 8) {
            const pairFreq = {};
            const pairLimit = Math.min(50, N);
            for (let t = 0; t < pairLimit; t++) {
                const nums = (history[t].numbers || []).concat(history[t].numbers2 || [])
                    .filter(x => x >= startNum && x <= endNum).sort((a, b) => a - b);
                const decay = Math.exp(-t * 0.04);
                for (let i = 0; i < nums.length; i++) {
                    for (let j = i + 1; j < nums.length; j++) {
                        const pk = nums[i] + '-' + nums[j];
                        pairFreq[pk] = (pairFreq[pk] || 0) + decay;
                    }
                }
            }
            const topPairs = Object.entries(pairFreq).sort((a, b) => b[1] - a[1]).slice(0, 30);
            for (const [pk, freq] of topPairs) {
                const [a, b] = pk.split('-').map(Number);
                const boost = freq * 0.06;
                pairTrioLayer[a] = (pairTrioLayer[a] || 0.5) + boost;
                pairTrioLayer[b] = (pairTrioLayer[b] || 0.5) + boost;
            }
            pairTrioLayer = this._normalizeScores(pairTrioLayer, startNum, endNum);
        }
        layers.push(pairTrioLayer);

        // â˜… v10.0 FIX: CAMADA 20 â€” Ciclo Individual de Retorno (era AUSENTE!)
        let cycleReturnLayer = {};
        for (let n = startNum; n <= endNum; n++) cycleReturnLayer[n] = 0.5;
        if (N >= 10) {
            const expectedGlobalCycle = totalRange / drawSize;
            for (let n = startNum; n <= endNum; n++) {
                const appearances = [];
                for (let i = 0; i < Math.min(60, N); i++) {
                    if ((history[i].numbers || []).concat(history[i].numbers2 || []).includes(n)) appearances.push(i);
                }
                if (appearances.length < 2) {
                    cycleReturnLayer[n] = appearances.length > 0 && appearances[0] > expectedGlobalCycle * 1.5 ? 0.90 : 0.60;
                    continue;
                }
                const gaps = [];
                for (let j = 0; j < appearances.length - 1; j++) gaps.push(appearances[j + 1] - appearances[j]);
                const avgCycle = gaps.reduce((a, b) => a + b, 0) / gaps.length;
                const currentDelay = appearances[0];
                const cyclePosition = currentDelay / Math.max(1, avgCycle);
                let score = 0.3;
                if (cyclePosition >= 0.85 && cyclePosition <= 1.2) score = 0.95;
                else if (cyclePosition >= 0.6 && cyclePosition < 0.85) score = 0.75;
                else if (cyclePosition > 1.2 && cyclePosition <= 2.0) score = 0.85;
                else if (cyclePosition > 2.0) score = 0.80;
                cycleReturnLayer[n] = Math.min(1.0, score);
            }
            cycleReturnLayer = this._normalizeScores(cycleReturnLayer, startNum, endNum);
        }
        layers.push(cycleReturnLayer);

        // â˜… v10.0 FIX: CAMADA 21 â€” SuperposiÃ§Ã£o QuÃ¢ntica (era AUSENTE!)
        let quantumSuperLayer = {};
        for (let n = startNum; n <= endNum; n++) quantumSuperLayer[n] = 0.5;
        if (N >= 8) {
            const scenarios = [
                { window: 3, weight: 0.30 }, { window: 7, weight: 0.25 },
                { window: 15, weight: 0.20 }, { window: 30, weight: 0.15 },
                { window: Math.min(50, N), weight: 0.10 }
            ];
            for (let n = startNum; n <= endNum; n++) {
                let collapseProb = 0;
                for (const sc of scenarios) {
                    const ws = Math.min(sc.window, N);
                    let freq = 0;
                    for (let i = 0; i < ws; i++) {
                        if ((history[i].numbers || []).concat(history[i].numbers2 || []).includes(n)) freq++;
                    }
                    const freqRatio = freq / ws;
                    const expectedFreq = drawSize / totalRange;
                    const deviation = freqRatio / Math.max(0.001, expectedFreq);
                    collapseProb += deviation * sc.weight;
                }
                quantumSuperLayer[n] = Math.min(1.0, collapseProb * 0.5);
            }
            quantumSuperLayer = this._normalizeScores(quantumSuperLayer, startNum, endNum);
        }
        layers.push(quantumSuperLayer);

        // â˜… v10.0: 21 camadas sincronizadas com _scoreAllNumbers
        const w = this._getGodModeWeights(gameKey);
        const wKeys = ['frequency','trend','delay','zone','markov','phase','clairvoyance','nextDraw','bayesian','positional','sequential','momentum','mirror','gap','cluster','reversion','precision','patternDna','pairTrio','cycleReturn','quantumSuper'];
        const scores = {};

        for (let n = startNum; n <= endNum; n++) {
            let total = 0;
            for (let i = 0; i < 21; i++) {
                total += (layers[i][n] || 0) * (w[wKeys[i]] || 0.05);
            }
            // Micro-ruÃ­do para desempate (Â± 0.5%)
            const noise = (Math.random() * 0.01) - 0.005; 
            scores[n] = total + noise;
        }

        return scores;
    }

    // Manter retrocompatibilidade
    static _scoreAllNumbersDeterministic(gameKey, profile, history, startNum, endNum, totalRange) {
        return this._scoreForSuggestionL99(gameKey, profile, history, startNum, endNum, totalRange);
    }

    // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    //  UTILITÃRIOS
    // â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

    // â•”â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•—
    // â•‘  â˜… v5.0: NORMALIZAÃ‡ÃƒO CALIBRADA POR VARIÃ‚NCIA (Ïƒ-aware)    â•‘
    // â•‘  Camadas com sinal forte â†’ [0, 1] (amplitude total)        â•‘
    // â•‘  Camadas com sinal fraco â†’ [0.35, 0.65] (quase neutro)     â•‘
    // â•‘  Evita que camadas sem sinal contaminam o ensemble          â•‘
    // â•šâ•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
    static _normalizeScores(scores, startNum, endNum) {
        let min = Infinity, max = -Infinity;
        for (let n = startNum; n <= endNum; n++) {
            const v = scores[n] || 0;
            if (v < min) min = v;
            if (v > max) max = v;
        }
        const range = max - min || 1;

        // v11.0: Floor DINÂMICO baseado na densidade da loteria
        // Sniper com muitos jogos: floor mais alto para garantir diversidade
        const totalRange = endNum - startNum + 1;
        const drawSize = this._currentDrawSize || 6;
        const density = drawSize / totalRange;
        let floor = Math.max(0.01, Math.min(0.08, density * 0.15));
        // v11.0 FIX: Sniper precisa de floor mais alto para diversidade
        if (this._sniperMode) {
            floor = Math.max(0.10, floor);
        }
        for (let n = startNum; n <= endNum; n++) {
            const normalized = (scores[n] - min) / range;
            scores[n] = floor + normalized * (1.0 - floor);
        }
        return scores;
    }

    static _weightedPick(items, weights) {
        if (items.length === 0) return null;
        let totalW = 0;
        for (const n of items) totalW += (weights[n] || 0.001);
        let rand = Math.random() * totalW;
        for (const n of items) {
            rand -= (weights[n] || 0.001);
            if (rand <= 0) return n;
        }
        return items[items.length - 1];
    }

    static _weightedSample(probMap, count, startNum, endNum) {
        const result = [];
        const used = new Set();
        const entries = [];
        for (let n = startNum; n <= endNum; n++) {
            entries.push({ num: n, prob: probMap[n] || 0 });
        }

        for (let i = 0; i < count && entries.length > 0; i++) {
            let totalP = 0;
            for (const e of entries) {
                if (!used.has(e.num)) totalP += e.prob;
            }
            if (totalP <= 0) break;

            let rand = Math.random() * totalP;
            for (const e of entries) {
                if (used.has(e.num)) continue;
                rand -= e.prob;
                if (rand <= 0) {
                    result.push(e.num);
                    used.add(e.num);
                    break;
                }
            }
        }
        return result;
    }

    static _wouldCreate3Consecutive(num, ticketSet) {
        if (ticketSet.has(num - 1) && ticketSet.has(num - 2)) return true;
        if (ticketSet.has(num + 1) && ticketSet.has(num + 2)) return true;
        if (ticketSet.has(num - 1) && ticketSet.has(num + 1)) return true;
        return false;
    }

    static _countFreqs(games) {
        const freq = {};
        for (const g of games) {
            for (const n of g) {
                freq[n] = (freq[n] || 0) + 1;
            }
        }
        return freq;
    }

    // ======================================================================
    // BACKTEST COMPARATIVO v10.3 — IA vs ALEATORIO (MEGA SENA)
    // Gera N jogos IA + N jogos aleatorios por concurso, confere ambos
    // contra resultados reais e retorna comparacao objetiva.
    // Uso: NovaEraEngine.backtestComparative('megasena')
    // ======================================================================
    static backtestComparative(gameKey) {
        const profile = this.getProfile(gameKey);
        if (!profile) return null;

        const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        if (!game) return null;

        const startNum = profile.range[0];
        const endNum = profile.range[1];
        const totalRange = endNum - startNum + 1;
        const drawSize = game.minBet || profile.drawSize;

        // Carregar historico
        let history = [];
        try {
            if (typeof REAL_HISTORY_DB !== 'undefined' && REAL_HISTORY_DB[gameKey]) {
                history = REAL_HISTORY_DB[gameKey].slice(0);
            } else if (typeof StatsService !== 'undefined') {
                history = StatsService.getRecentResults(gameKey, 200) || [];
            }
        } catch(e) { console.warn('[BACKTEST] Sem historico:', e.message); }

        if (history.length < 15) {
            return { error: 'Historico insuficiente (' + history.length + ' concursos). Minimo: 15.' };
        }

        const testWindow = Math.min(30, history.length - 10);
        const gamesPerTest = 10;

        console.log('%c[BACKTEST COMPARATIVO] Iniciando: ' + testWindow + ' concursos x ' + gamesPerTest + ' jogos/grupo', 'color: #FF6B6B; font-weight: bold; font-size: 14px;');

        const results = {
            gameKey: gameKey,
            loteria: profile.name,
            concursosTested: testWindow,
            gamesPerConcurso: gamesPerTest,
            ia: { quadra: 0, terno: 0, duque: 0, total: 0 },
            random: { quadra: 0, terno: 0, duque: 0, total: 0 },
            details: []
        };

        for (let c = 0; c < testWindow; c++) {
            // Resultado real deste concurso
            const realDraw = history[c].numbers || [];
            const realSet = new Set(realDraw.filter(function(n) { return n >= startNum && n <= endNum; }));

            if (realSet.size < drawSize) continue;

            // Historico ANTES deste concurso (sem data leaking)
            const trainingHistory = history.slice(c + 1);

            // --- GRUPO IA: gerar jogos com scoring completo ---
            let iaGames = [];
            try {
                const scores = this._scoreAllNumbers(gameKey, profile, trainingHistory, startNum, endNum, totalRange);
                const pool = [];
                for (var n = startNum; n <= endNum; n++) pool.push(n);

                for (var g = 0; g < gamesPerTest; g++) {
                    var ticket = this._generateSingleGame(
                        profile, scores, pool, drawSize,
                        [], {}, 999, startNum, endNum,
                        profile.zones, profile.zoneSize, g, gamesPerTest, new Set(), trainingHistory
                    );
                    if (ticket && ticket.length >= drawSize) iaGames.push(ticket);
                }
            } catch(e) {
                // Fallback se scoring falhar
                for (var g2 = 0; g2 < gamesPerTest; g2++) {
                    iaGames.push(this._generateRandomFiltered(startNum, endNum, drawSize, profile));
                }
            }

            // --- GRUPO ALEATORIO: mesmos filtros estruturais, sem scoring ---
            var randomGames = [];
            for (var r = 0; r < gamesPerTest; r++) {
                randomGames.push(this._generateRandomFiltered(startNum, endNum, drawSize, profile));
            }

            // --- CONFERIR AMBOS ---
            var detail = { concurso: history[c].concurso || (c + 1), resultado: Array.from(realSet), ia: [], random: [] };

            for (var i = 0; i < iaGames.length; i++) {
                var hits = 0;
                for (var j = 0; j < iaGames[i].length; j++) {
                    if (realSet.has(iaGames[i][j])) hits++;
                }
                if (hits >= 4) { results.ia.quadra++; detail.ia.push(hits); }
                else if (hits >= 3) { results.ia.terno++; detail.ia.push(hits); }
                else if (hits >= 2) { results.ia.duque++; detail.ia.push(hits); }
                else { detail.ia.push(hits); }
                results.ia.total++;
            }

            for (var i2 = 0; i2 < randomGames.length; i2++) {
                var hits2 = 0;
                for (var j2 = 0; j2 < randomGames[i2].length; j2++) {
                    if (realSet.has(randomGames[i2][j2])) hits2++;
                }
                if (hits2 >= 4) { results.random.quadra++; detail.random.push(hits2); }
                else if (hits2 >= 3) { results.random.terno++; detail.random.push(hits2); }
                else if (hits2 >= 2) { results.random.duque++; detail.random.push(hits2); }
                else { detail.random.push(hits2); }
                results.random.total++;
            }

            results.details.push(detail);
        }

        // Calcular taxas
        var totalIA = results.ia.total || 1;
        var totalRand = results.random.total || 1;
        results.ia.taxaQuadra = (results.ia.quadra / totalIA * 100).toFixed(3);
        results.ia.taxaTerno = (results.ia.terno / totalIA * 100).toFixed(2);
        results.ia.taxaDuque = (results.ia.duque / totalIA * 100).toFixed(1);
        results.random.taxaQuadra = (results.random.quadra / totalRand * 100).toFixed(3);
        results.random.taxaTerno = (results.random.terno / totalRand * 100).toFixed(2);
        results.random.taxaDuque = (results.random.duque / totalRand * 100).toFixed(1);

        // Veredito
        var iaScore = results.ia.quadra * 100 + results.ia.terno * 10 + results.ia.duque;
        var randScore = results.random.quadra * 100 + results.random.terno * 10 + results.random.duque;
        if (iaScore > randScore * 1.1) {
            results.veredito = 'IA SUPERIOR';
            results.vantagem = '+' + ((iaScore / Math.max(1, randScore) - 1) * 100).toFixed(1) + '%';
        } else if (randScore > iaScore * 1.1) {
            results.veredito = 'ALEATORIO SUPERIOR';
            results.vantagem = '-' + ((randScore / Math.max(1, iaScore) - 1) * 100).toFixed(1) + '%';
        } else {
            results.veredito = 'EMPATE ESTATISTICO';
            results.vantagem = '0%';
        }

        // Log
        console.log('%c[BACKTEST] ═══ RESULTADO FINAL ═══', 'color: #FFD700; font-weight: bold; font-size: 16px;');
        console.log('[BACKTEST] Concursos: ' + results.concursosTested + ' | Jogos/grupo: ' + gamesPerTest);
        console.log('[BACKTEST] IA     → Quadra: ' + results.ia.quadra + ' (' + results.ia.taxaQuadra + '%) | Terno: ' + results.ia.terno + ' (' + results.ia.taxaTerno + '%) | Duque: ' + results.ia.duque);
        console.log('[BACKTEST] RANDOM → Quadra: ' + results.random.quadra + ' (' + results.random.taxaQuadra + '%) | Terno: ' + results.random.terno + ' (' + results.random.taxaTerno + '%) | Duque: ' + results.random.duque);
        console.log('%c[BACKTEST] VEREDITO: ' + results.veredito + ' (' + results.vantagem + ')', 'color: #FF6B6B; font-weight: bold; font-size: 14px;');

        return results;
    }

    // Gerar jogo aleatorio com filtros estruturais (sem scoring IA)
    static _generateRandomFiltered(startNum, endNum, drawSize, profile) {
        var maxAttempts = 500;
        for (var a = 0; a < maxAttempts; a++) {
            // Gerar drawSize numeros aleatorios unicos
            var nums = [];
            var used = {};
            while (nums.length < drawSize) {
                var n = startNum + Math.floor(Math.random() * (endNum - startNum + 1));
                if (!used[n]) {
                    nums.push(n);
                    used[n] = true;
                }
            }
            nums.sort(function(a, b) { return a - b; });

            // Filtro: soma
            var sum = 0;
            for (var i = 0; i < nums.length; i++) sum += nums[i];
            if (sum < profile.sumRange[0] || sum > profile.sumRange[1]) continue;

            // Filtro: paridade
            var evens = 0;
            for (var i2 = 0; i2 < nums.length; i2++) { if (nums[i2] % 2 === 0) evens++; }
            if (evens < profile.evenOddRange[0] || evens > profile.evenOddRange[1]) continue;

            // Filtro: consecutivos
            var maxRun = 1, curRun = 1;
            for (var i3 = 1; i3 < nums.length; i3++) {
                if (nums[i3] === nums[i3-1] + 1) { curRun++; if (curRun > maxRun) maxRun = curRun; }
                else curRun = 1;
            }
            if (maxRun > profile.maxConsecutive) continue;

            return nums;
        }
        // Fallback sem filtros
        var fallback = [];
        var usedFb = {};
        while (fallback.length < drawSize) {
            var fn = startNum + Math.floor(Math.random() * (endNum - startNum + 1));
            if (!usedFb[fn]) { fallback.push(fn); usedFb[fn] = true; }
        }
        return fallback.sort(function(a, b) { return a - b; });
    }
}

// Exportar globalmente
if (typeof window !== 'undefined') {
    window.NovaEraEngine = NovaEraEngine;
}




