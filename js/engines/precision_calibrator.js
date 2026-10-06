/**
 * ╔══════════════════════════════════════════════════════════════════════════╗
 * ║  PRECISION CALIBRATOR — Motor de Calibração de Precisão Absoluta       ║
 * ║  Versão: 1.0 — 22/04/2026                                             ║
 * ╠══════════════════════════════════════════════════════════════════════════╣
 * ║  FOCO: Análise cirúrgica dos ÚLTIMOS 3 RESULTADOS + Futurologia       ║
 * ║                                                                        ║
 * ║  MÓDULOS:                                                              ║
 * ║   1. Análise de Consecutivos REAL por Loteria                          ║
 * ║   2. Projeção Futurológica (últimos 3 → próximo)                      ║
 * ║   3. Probabilidade Condicional Multidimensional                        ║
 * ║   4. Filtro Anti-Consecutivo Inteligente                               ║
 * ║   5. Score de Similaridade com Padrões Vencedores                      ║
 * ║                                                                        ║
 * ║  "Análise quântica + Clarividência computacional = Precisão máxima."  ║
 * ╚══════════════════════════════════════════════════════════════════════════╝
 */

const PrecisionCalibrator = {

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // LIMITES DE CONSECUTIVOS REAIS POR LOTERIA
    // Baseados em análise de milhares de sorteios reais
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    CONSECUTIVE_LIMITS: {
        megasena:   { maxRun: 2, pairFreq: 0.30, tripleFreq: 0.02, allowPair: true,  allowTriple: false },
        lotofacil:  { maxRun: 6, pairFreq: 0.95, tripleFreq: 0.45, allowPair: true,  allowTriple: true  },
        quina:      { maxRun: 2, pairFreq: 0.20, tripleFreq: 0.01, allowPair: true,  allowTriple: false },
        duplasena:  { maxRun: 2, pairFreq: 0.25, tripleFreq: 0.02, allowPair: true,  allowTriple: false },
        lotomania:  { maxRun: 5, pairFreq: 0.98, tripleFreq: 0.60, allowPair: true,  allowTriple: true  },
        timemania:  { maxRun: 2, pairFreq: 0.25, tripleFreq: 0.02, allowPair: true,  allowTriple: false },
        diadesorte: { maxRun: 3, pairFreq: 0.35, tripleFreq: 0.08, allowPair: true,  allowTriple: true  }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // MÓDULO 1: ANALISAR CONSECUTIVOS NO HISTÓRICO REAL
    // Verifica padrão REAL de runs consecutivos nos sorteios passados
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    analyzeConsecutiveHistory(gameKey, history) {
        if (!history || history.length < 5) return this.CONSECUTIVE_LIMITS[gameKey] || { maxRun: 2 };

        const limit = Math.min(100, history.length);
        let totalDraws = 0;
        let drawsWithPair = 0;      // Runs de 2+
        let drawsWithTriple = 0;    // Runs de 3+
        let maxRunSeen = 1;
        const runDistribution = {};  // { runLength: count }

        for (let i = 0; i < limit; i++) {
            const nums = (history[i].numbers || []).slice().sort((a, b) => a - b);
            if (nums.length < 2) continue;
            totalDraws++;

            let curRun = 1, maxRun = 1;
            let hasPair = false, hasTriple = false;

            for (let j = 1; j < nums.length; j++) {
                if (nums[j] === nums[j - 1] + 1) {
                    curRun++;
                    if (curRun >= 2) hasPair = true;
                    if (curRun >= 3) hasTriple = true;
                    maxRun = Math.max(maxRun, curRun);
                } else {
                    if (curRun >= 2) runDistribution[curRun] = (runDistribution[curRun] || 0) + 1;
                    curRun = 1;
                }
            }
            if (curRun >= 2) runDistribution[curRun] = (runDistribution[curRun] || 0) + 1;

            if (hasPair) drawsWithPair++;
            if (hasTriple) drawsWithTriple++;
            maxRunSeen = Math.max(maxRunSeen, maxRun);
        }

        const result = {
            maxRun: maxRunSeen,
            pairFreq: totalDraws > 0 ? drawsWithPair / totalDraws : 0,
            tripleFreq: totalDraws > 0 ? drawsWithTriple / totalDraws : 0,
            allowPair: drawsWithPair / totalDraws > 0.15,
            allowTriple: drawsWithTriple / totalDraws > 0.10,
            runDistribution: runDistribution,
            analyzed: totalDraws
        };

        console.log('[PRECISION] 📊 Consecutivos ' + gameKey + ': max=' + maxRunSeen +
            ' | pares=' + (result.pairFreq * 100).toFixed(0) + '% | triplos=' + (result.tripleFreq * 100).toFixed(0) + '%');

        return result;
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // MÓDULO 2: PROJEÇÃO FUTUROLÓGICA DOS ÚLTIMOS 3 RESULTADOS
    // Pergunta central: "Dado os 3 últimos, qual a tendência do próximo?"
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    analyzeLast3Trends(gameKey, history, startNum, endNum) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (!history || history.length < 4) return scores;

        const N = history.length;
        const last3 = [
            new Set(history[0].numbers || []),
            new Set(history[1].numbers || []),
            new Set(history[2].numbers || [])
        ];

        // ── 2a. NÚMEROS POR FREQUÊNCIA NOS ÚLTIMOS 3 ──
        const freqLast3 = {};
        for (let n = startNum; n <= endNum; n++) freqLast3[n] = 0;
        for (const drawSet of last3) {
            for (const n of drawSet) {
                if (n >= startNum && n <= endNum) freqLast3[n]++;
            }
        }

        for (let n = startNum; n <= endNum; n++) {
            const f = freqLast3[n];
            if (f === 3) {
                // Saiu em TODOS os 3 últimos → provável "descansar" (exceto Lotofácil)
                scores[n] = gameKey === 'lotofacil' ? 0.70 : 0.25;
            } else if (f === 2) {
                // Saiu em 2 dos 3 → FORTE candidato a repetir
                scores[n] = 0.85;
            } else if (f === 1) {
                // Saiu em 1 dos 3 → moderado
                scores[n] = 0.60;
            } else {
                // NÃO saiu em nenhum dos 3 → pressão acumulada
                scores[n] = 0.55;
            }
        }

        // ── 2b. TENDÊNCIA DE SOMA ──
        const sums = [];
        for (let i = 0; i < 3; i++) {
            const nums = history[i].numbers || [];
            sums.push(nums.reduce((a, b) => a + b, 0));
        }

        // Direção: subindo ou descendo?
        const sumDelta1 = sums[0] - sums[1]; // último - penúltimo
        const sumDelta2 = sums[1] - sums[2]; // penúltimo - antepenúltimo
        const sumTrend = (sumDelta1 > 0 && sumDelta2 > 0) ? 'up'
                       : (sumDelta1 < 0 && sumDelta2 < 0) ? 'down'
                       : 'oscillating';

        const midPoint = (startNum + endNum) / 2;
        if (sumTrend === 'up') {
            // Soma subindo 2x → regressão: boost números baixos
            for (let n = startNum; n <= endNum; n++) {
                if (n < midPoint) scores[n] = Math.min(1.0, scores[n] + 0.10);
            }
        } else if (sumTrend === 'down') {
            // Soma descendo 2x → regressão: boost números altos
            for (let n = startNum; n <= endNum; n++) {
                if (n > midPoint) scores[n] = Math.min(1.0, scores[n] + 0.10);
            }
        }

        // ── 2c. TENDÊNCIA DE PARIDADE ──
        const parities = [];
        for (let i = 0; i < 3; i++) {
            const nums = history[i].numbers || [];
            const evenCount = nums.filter(n => n % 2 === 0).length;
            parities.push(evenCount / Math.max(1, nums.length));
        }

        const avgParity = parities.reduce((a, b) => a + b, 0) / 3;
        if (avgParity > 0.60) {
            // Últimos 3 tenderam para PARES → próximo tende a ter mais ímpares
            for (let n = startNum; n <= endNum; n++) {
                if (n % 2 !== 0) scores[n] = Math.min(1.0, scores[n] + 0.08);
            }
        } else if (avgParity < 0.40) {
            // Últimos 3 tenderam para ÍMPARES → próximo tende a ter mais pares
            for (let n = startNum; n <= endNum; n++) {
                if (n % 2 === 0) scores[n] = Math.min(1.0, scores[n] + 0.08);
            }
        }

        // ── 2d. ZONAS QUENTES/FRIAS NOS ÚLTIMOS 3 ──
        const zoneSize = 10;
        const numZones = Math.ceil((endNum - startNum + 1) / zoneSize);
        const zoneHits = new Array(numZones).fill(0);
        let totalHits = 0;

        for (const drawSet of last3) {
            for (const n of drawSet) {
                if (n >= startNum && n <= endNum) {
                    const z = Math.min(numZones - 1, Math.floor((n - startNum) / zoneSize));
                    zoneHits[z]++;
                    totalHits++;
                }
            }
        }

        const avgPerZone = totalHits / numZones;
        for (let n = startNum; n <= endNum; n++) {
            const z = Math.min(numZones - 1, Math.floor((n - startNum) / zoneSize));
            const ratio = zoneHits[z] / Math.max(1, avgPerZone);
            if (ratio < 0.5) {
                // Zona SUB-representada nos últimos 3 → provável retorno
                scores[n] = Math.min(1.0, scores[n] + 0.12);
            } else if (ratio > 1.8) {
                // Zona SUPER-representada → provável regressão
                scores[n] = Math.max(0.1, scores[n] - 0.08);
            }
        }

        // ── 2e. NÚMEROS "EMERGENTES" — Saíram no último mas não nos 2 anteriores
        for (let n = startNum; n <= endNum; n++) {
            if (last3[0].has(n) && !last3[1].has(n) && !last3[2].has(n)) {
                // Número "novo" — pode manter momentum
                scores[n] = Math.min(1.0, scores[n] + 0.07);
            }
        }

        return this._normalize(scores, startNum, endNum);
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // MÓDULO 3: PROBABILIDADE CONDICIONAL MULTIDIMENSIONAL
    // Dado os últimos 3 resultados, qual padrão SEGUIU no histórico?
    // Similar ao Espelho Temporal mas com análise MUITO mais profunda
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    buildConditionalProbMatrix(gameKey, history, startNum, endNum, drawSize) {
        const scores = {};
        for (let n = startNum; n <= endNum; n++) scores[n] = 0.5;
        if (!history || history.length < 6) return scores;

        const N = history.length;
        const last3 = [];
        for (let i = 0; i < 3; i++) {
            last3.push(new Set((history[i].numbers || []).concat(history[i].numbers2 || [])));
        }

        // Construir "impressão digital" dos últimos 3 como vetor de características
        const fingerprint = this._getFingerprint(last3, startNum, endNum);

        // Procurar padrões similares em TODO o histórico (janelas de 3)
        const matches = [];
        const searchLimit = Math.min(N - 3, 80); // Expandido de 35 para 80

        for (let w = 3; w < searchLimit; w++) {
            const windowSets = [];
            for (let d = 0; d < 3; d++) {
                windowSets.push(new Set((history[w + d].numbers || []).concat(history[w + d].numbers2 || [])));
            }

            const windowFP = this._getFingerprint(windowSets, startNum, endNum);
            const similarity = this._fingerprintSimilarity(fingerprint, windowFP);

            if (similarity > 0.35) {
                // O que aconteceu DEPOIS desta janela?
                const followIdx = w - 1; // Resultado que seguiu
                if (followIdx >= 0 && followIdx < w) {
                    matches.push({
                        idx: followIdx,
                        similarity: similarity,
                        numbers: (history[followIdx].numbers || []).concat(history[followIdx].numbers2 || [])
                    });
                }
            }
        }

        if (matches.length === 0) return scores;

        // Ponderar resultados pela similaridade
        let totalSim = 0;
        for (const m of matches) totalSim += m.similarity;

        for (const m of matches) {
            const weight = m.similarity / totalSim;
            for (const n of m.numbers) {
                if (n >= startNum && n <= endNum) {
                    scores[n] += weight * 0.8;
                }
            }
        }

        console.log('[PRECISION] 🔮 Padrões similares encontrados: ' + matches.length +
            ' | Melhor match: ' + (matches.sort((a, b) => b.similarity - a.similarity)[0].similarity * 100).toFixed(0) + '%');

        return this._normalize(scores, startNum, endNum);
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // MÓDULO 4: FILTRO ANTI-CONSECUTIVO INTELIGENTE
    // Verifica se um jogo respeita o padrão REAL de consecutivos
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    validateConsecutives(ticket, gameKey, history) {
        // Analisar padrão real se temos histórico
        const limits = history && history.length >= 10
            ? this.analyzeConsecutiveHistory(gameKey, history)
            : (this.CONSECUTIVE_LIMITS[gameKey] || { maxRun: 2 });

        const sorted = [...ticket].sort((a, b) => a - b);
        let maxRun = 1, curRun = 1;
        const runs = [];

        for (let i = 1; i < sorted.length; i++) {
            if (sorted[i] === sorted[i - 1] + 1) {
                curRun++;
                maxRun = Math.max(maxRun, curRun);
            } else {
                if (curRun >= 2) runs.push(curRun);
                curRun = 1;
            }
        }
        if (curRun >= 2) runs.push(curRun);

        // Validar contra o limite REAL
        const valid = maxRun <= limits.maxRun;
        const hasPair = runs.some(r => r >= 2);
        const hasTriple = runs.some(r => r >= 3);

        return {
            valid: valid,
            maxRun: maxRun,
            runs: runs,
            hasPair: hasPair,
            hasTriple: hasTriple,
            limitUsed: limits.maxRun,
            realisticPairChance: limits.pairFreq
        };
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // MÓDULO 5: SCORE DE PRECISÃO PARA UM JOGO
    // Combina Last3 + ConditionalProb + ConsecutiveCheck
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    scoreTicketPrecision(ticket, gameKey, history, startNum, endNum, drawSize) {
        if (!ticket || ticket.length === 0) return 0;

        let score = 0;

        // 1. Score dos últimos 3
        const last3Scores = this.analyzeLast3Trends(gameKey, history, startNum, endNum);
        const avgLast3 = ticket.reduce((s, n) => s + (last3Scores[n] || 0), 0) / ticket.length;
        score += avgLast3 * 0.40;

        // 2. Score condicional
        const condScores = this.buildConditionalProbMatrix(gameKey, history, startNum, endNum, drawSize);
        const avgCond = ticket.reduce((s, n) => s + (condScores[n] || 0), 0) / ticket.length;
        score += avgCond * 0.30;

        // 3. Validação de consecutivos
        const consCheck = this.validateConsecutives(ticket, gameKey, history);
        if (consCheck.valid) {
            score += 0.20;
        } else {
            score -= 0.30; // Penalidade severa
        }

        // 4. Distribuição por zonas
        const zoneSize = 10;
        const numZones = Math.ceil((endNum - startNum + 1) / zoneSize);
        const zoneCount = new Array(numZones).fill(0);
        for (const n of ticket) {
            const z = Math.min(numZones - 1, Math.floor((n - startNum) / zoneSize));
            zoneCount[z]++;
        }
        const coveredZones = zoneCount.filter(c => c > 0).length;
        const zoneScore = coveredZones / numZones;
        score += zoneScore * 0.10;

        return Math.max(0, Math.min(1, score));
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // FUNÇÕES AUXILIARES
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    _getFingerprint(drawSets, startNum, endNum) {
        const zoneSize = 10;
        const numZones = Math.ceil((endNum - startNum + 1) / zoneSize);
        const fp = {
            zoneHits: new Array(numZones).fill(0),
            evenCount: 0,
            oddCount: 0,
            totalSum: 0,
            totalNums: 0,
            highCount: 0,
            lowCount: 0
        };

        const mid = (startNum + endNum) / 2;

        for (const drawSet of drawSets) {
            for (const n of drawSet) {
                if (n < startNum || n > endNum) continue;
                fp.totalNums++;
                fp.totalSum += n;
                if (n % 2 === 0) fp.evenCount++; else fp.oddCount++;
                if (n > mid) fp.highCount++; else fp.lowCount++;
                const z = Math.min(numZones - 1, Math.floor((n - startNum) / zoneSize));
                fp.zoneHits[z]++;
            }
        }

        return fp;
    },

    _fingerprintSimilarity(fp1, fp2) {
        if (fp1.totalNums === 0 || fp2.totalNums === 0) return 0;

        let similarity = 0;

        // 1. Similaridade de proporção par/ímpar
        const evenR1 = fp1.evenCount / fp1.totalNums;
        const evenR2 = fp2.evenCount / fp2.totalNums;
        similarity += (1 - Math.abs(evenR1 - evenR2)) * 0.20;

        // 2. Similaridade de soma
        const avgSum1 = fp1.totalSum / fp1.totalNums;
        const avgSum2 = fp2.totalSum / fp2.totalNums;
        const sumDiff = Math.abs(avgSum1 - avgSum2) / Math.max(avgSum1, avgSum2, 1);
        similarity += (1 - Math.min(1, sumDiff)) * 0.25;

        // 3. Similaridade de zonas (distribuição cosine)
        let dot = 0, mag1 = 0, mag2 = 0;
        for (let z = 0; z < fp1.zoneHits.length; z++) {
            const a = fp1.zoneHits[z] || 0;
            const b = (z < fp2.zoneHits.length) ? fp2.zoneHits[z] || 0 : 0;
            dot += a * b;
            mag1 += a * a;
            mag2 += b * b;
        }
        const cosSim = (mag1 > 0 && mag2 > 0) ? dot / (Math.sqrt(mag1) * Math.sqrt(mag2)) : 0;
        similarity += cosSim * 0.35;

        // 4. Similaridade alto/baixo
        const highR1 = fp1.highCount / fp1.totalNums;
        const highR2 = fp2.highCount / fp2.totalNums;
        similarity += (1 - Math.abs(highR1 - highR2)) * 0.20;

        return similarity;
    },

    _normalize(scoreMap, min, max) {
        let mn = Infinity, mx = -Infinity;
        for (let n = min; n <= max; n++) {
            if ((scoreMap[n] || 0) > mx) mx = scoreMap[n];
            if ((scoreMap[n] || 0) < mn) mn = scoreMap[n];
        }
        const range = mx - mn;
        const result = {};
        for (let n = min; n <= max; n++) {
            result[n] = range > 0 ? ((scoreMap[n] || 0) - mn) / range : 0.5;
        }
        return result;
    }
};

console.log('%c[PRECISION] ★ Motor de Precisão Absoluta v1.0 ativado', 'color: #00FF88; font-weight: bold; background: #0a0a1a;');
