/**
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  STATISTICAL BIAS ENGINE v1.0                                   ║
 * ║  Detector de Viés Estatístico — Matemática Pura                 ║
 * ║                                                                 ║
 * ║  PRINCÍPIO: Não prevemos nada. Detectamos EVIDÊNCIA.            ║
 * ║  Se o RNG da loteria tem viés → detectamos com p-valor.         ║
 * ║  Se não tem viés → dizemos HONESTAMENTE.                        ║
 * ║                                                                 ║
 * ║  TESTES IMPLEMENTADOS:                                          ║
 * ║  1. Chi-Quadrado (χ²) com p-valor real                         ║
 * ║  2. Runs Test (Teste de Sequências) para independência          ║
 * ║  3. Autocorrelação Serial (lag 1-5)                             ║
 * ║  4. Z-score por número com significância individual             ║
 * ║                                                                 ║
 * ║  SAÍDA: Ranking de números por EVIDÊNCIA ESTATÍSTICA,           ║
 * ║  não por frequência bruta ou "tendência".                       ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */
class StatisticalBiasEngine {

    // ═══════════════════════════════════════════════════════════
    //  PONTO DE ENTRADA: Análise completa
    //  Retorna: { tests, numberScores, suggestedPool, verdict }
    // ═══════════════════════════════════════════════════════════
    static analyze(gameKey, history, poolSize, options) {
        const t0 = Date.now();
        const _opts = options || {};
        const cfg = this._getConfig(gameKey);
        if (!cfg) return null;

        // Extrair apenas os sorteios (arrays de números)
        const draws = this._extractDraws(history, cfg);
        if (draws.length < 20) {
            console.warn('[BIAS] Dados insuficientes: ' + draws.length + ' sorteios (mínimo 20)');
            return { error: 'Dados insuficientes', draws: draws.length, minRequired: 20 };
        }

        console.log('%c[BIAS] ══════════════════════════════════════════', 'color: #8B5CF6; font-weight: bold;');
        console.log('%c[BIAS] DETECTOR DE VIÉS ESTATÍSTICO v1.0', 'color: #8B5CF6; font-weight: bold;');
        console.log('%c[BIAS] ' + cfg.name + ' | ' + draws.length + ' sorteios analisados', 'color: #8B5CF6; font-weight: bold;');

        // ── JANELAS DE ANÁLISE ──
        const windows = _opts.windows || [
            { label: 'Curto (30)', size: 30 },
            { label: 'Médio (60)', size: 60 },
            { label: 'Longo (150)', size: 150 },
            { label: 'Total', size: draws.length }
        ];

        const analyses = {};
        for (const w of windows) {
            const windowDraws = draws.slice(0, Math.min(w.size, draws.length));
            if (windowDraws.length < 15) continue;
            analyses[w.label] = this._analyzeWindow(windowDraws, cfg);
        }

        // ── TESTES FORMAIS ──
        const chiSquared = this._chiSquaredTest(draws, cfg);
        const runsTest = this._runsTest(draws, cfg);
        const autocorr = this._serialAutocorrelation(draws, cfg, 5);

        // ── SCORE POR NÚMERO ──
        const numberScores = this._computeNumberScores(draws, cfg, analyses, windows);

        // ── POOL SUGERIDO ──
        const suggestedSize = poolSize || Math.min(cfg.totalNumbers, cfg.drawSize * 3);
        const suggestedPool = this._buildEvidencePool(numberScores, suggestedSize, cfg);

        // ── VEREDICTO ──
        const verdict = this._buildVerdict(chiSquared, runsTest, autocorr);

        const elapsed = Date.now() - t0;
        console.log('[BIAS] Análise completa em ' + elapsed + 'ms');
        this._logResults(chiSquared, runsTest, autocorr, verdict);

        return {
            gameKey,
            draws: draws.length,
            tests: { chiSquared, runsTest, autocorrelation: autocorr },
            windowAnalyses: analyses,
            numberScores,
            suggestedPool,
            verdict,
            elapsed
        };
    }

    // ═══════════════════════════════════════════════════════════
    //  TESTE 1: Chi-Quadrado (χ²) com P-Valor Real
    //
    //  H0: Todos os números têm a mesma probabilidade
    //  H1: Alguns números saem mais/menos que o esperado
    //
    //  Se p < 0.05 → evidência de viés
    //  Se p > 0.05 → sem evidência (aleatoriedade normal)
    // ═══════════════════════════════════════════════════════════
    static _chiSquaredTest(draws, cfg) {
        const [startNum, endNum] = cfg.range;
        const totalNumbers = endNum - startNum + 1;
        const totalDrawn = draws.length * cfg.drawSize;
        const expected = totalDrawn / totalNumbers;

        // Contar frequências observadas
        const observed = {};
        for (let n = startNum; n <= endNum; n++) observed[n] = 0;
        for (const draw of draws) {
            for (const num of draw) {
                observed[num] = (observed[num] || 0) + 1;
            }
        }

        // χ² = Σ((O - E)² / E)
        let chiSq = 0;
        const perNumber = {};
        for (let n = startNum; n <= endNum; n++) {
            const o = observed[n] || 0;
            const deviation = (o - expected);
            const contribution = (deviation * deviation) / expected;
            chiSq += contribution;

            // Z-score individual: z = (O - E) / √E
            const zScore = deviation / Math.sqrt(expected);
            // P-valor individual (bicaudal)
            const pIndividual = 2 * (1 - this._normalCDF(Math.abs(zScore)));

            perNumber[n] = {
                observed: o,
                expected: Math.round(expected * 10) / 10,
                deviation: Math.round(deviation * 10) / 10,
                deviationPct: Math.round((deviation / expected) * 1000) / 10,
                zScore: Math.round(zScore * 100) / 100,
                pValue: Math.round(pIndividual * 10000) / 10000,
                significant: pIndividual < 0.05
            };
        }

        const df = totalNumbers - 1;
        const pValue = 1 - this._chiSquaredCDF(chiSq, df);

        return {
            testName: 'Chi-Quadrado (χ²)',
            chiSquared: Math.round(chiSq * 100) / 100,
            degreesOfFreedom: df,
            pValue: Math.round(pValue * 10000) / 10000,
            significant: pValue < 0.05,
            strongSignificant: pValue < 0.01,
            expected: Math.round(expected * 10) / 10,
            perNumber,
            interpretation: pValue < 0.01
                ? '🔴 VIÉS FORTE DETECTADO (p < 0.01) — Distribuição NÃO é uniforme'
                : pValue < 0.05
                    ? '🟡 VIÉS POSSÍVEL (p < 0.05) — Desvio marginalmente significativo'
                    : '✅ SEM VIÉS (p > 0.05) — Distribuição compatível com aleatoriedade'
        };
    }

    // ═══════════════════════════════════════════════════════════
    //  TESTE 2: Runs Test (Teste de Sequências)
    //
    //  Para cada número, cria sequência binária (saiu/não saiu)
    //  Conta "runs" (sequências consecutivas de 0 ou 1)
    //  Se R muito alto → alternância excessiva (anti-clustering)
    //  Se R muito baixo → clustering (dependência)
    //
    //  H0: Aparições são independentes entre sorteios
    //  H1: Existe dependência temporal
    // ═══════════════════════════════════════════════════════════
    static _runsTest(draws, cfg) {
        const [startNum, endNum] = cfg.range;
        const results = {};
        let totalZ = 0;
        let validTests = 0;

        // Testar os 10 números mais frequentes (representativos)
        const freq = {};
        for (let n = startNum; n <= endNum; n++) freq[n] = 0;
        for (const draw of draws) {
            for (const num of draw) freq[num]++;
        }
        const sortedNums = Object.keys(freq).map(Number)
            .sort((a, b) => freq[b] - freq[a])
            .slice(0, Math.min(15, endNum - startNum + 1));

        for (const num of sortedNums) {
            // Criar sequência binária: 1 se apareceu, 0 se não
            const sequence = draws.map(d => d.includes(num) ? 1 : 0);
            const n1 = sequence.filter(x => x === 1).length;
            const n0 = sequence.length - n1;

            if (n1 < 2 || n0 < 2) continue; // Insuficiente para testar

            // Contar runs
            let runs = 1;
            for (let i = 1; i < sequence.length; i++) {
                if (sequence[i] !== sequence[i - 1]) runs++;
            }

            // Expectativa e variância sob H0
            const N = n1 + n0;
            const expectedRuns = 1 + (2 * n1 * n0) / N;
            const varRuns = (2 * n1 * n0 * (2 * n1 * n0 - N)) / (N * N * (N - 1));

            if (varRuns <= 0) continue;

            const zRuns = (runs - expectedRuns) / Math.sqrt(varRuns);
            const pRuns = 2 * (1 - this._normalCDF(Math.abs(zRuns)));

            results[num] = {
                runs,
                expectedRuns: Math.round(expectedRuns * 10) / 10,
                zScore: Math.round(zRuns * 100) / 100,
                pValue: Math.round(pRuns * 10000) / 10000,
                independent: pRuns > 0.05,
                n1, n0
            };

            totalZ += zRuns * zRuns;
            validTests++;
        }

        // Teste combinado: média dos Z² (qui-quadrado combinado)
        const combinedChi = totalZ;
        const combinedP = validTests > 0 ? (1 - this._chiSquaredCDF(combinedChi, validTests)) : 1;
        const dependentCount = Object.values(results).filter(r => !r.independent).length;

        return {
            testName: 'Runs Test (Independência)',
            numbersTested: validTests,
            dependentNumbers: dependentCount,
            combinedPValue: Math.round(combinedP * 10000) / 10000,
            independent: combinedP > 0.05,
            perNumber: results,
            interpretation: combinedP < 0.01
                ? '🔴 DEPENDÊNCIA DETECTADA — Sorteios NÃO são independentes'
                : combinedP < 0.05
                    ? '🟡 DEPENDÊNCIA POSSÍVEL — Evidência marginalmente significativa'
                    : '✅ INDEPENDENTE — Sorteios são independentes (sem padrão temporal)'
        };
    }

    // ═══════════════════════════════════════════════════════════
    //  TESTE 3: Autocorrelação Serial
    //
    //  Verifica se o resultado do sorteio N afeta o sorteio N+k
    //  Para cada lag k (1 a maxLag):
    //    r_k = correlação entre draw[t] e draw[t+k]
    //  Se |r_k| > 2/√n → correlação significativa
    // ═══════════════════════════════════════════════════════════
    static _serialAutocorrelation(draws, cfg, maxLag) {
        // Converter cada sorteio em um vetor-soma (fingerprint simples)
        const sums = draws.map(d => d.reduce((a, b) => a + b, 0));
        const n = sums.length;
        const mean = sums.reduce((a, b) => a + b, 0) / n;
        const variance = sums.reduce((a, b) => a + (b - mean) * (b - mean), 0) / n;

        if (variance === 0) return { testName: 'Autocorrelação Serial', correlations: [], significant: false };

        const correlations = [];
        const threshold = 2 / Math.sqrt(n); // Limiar de significância (95%)
        let anySignificant = false;

        for (let lag = 1; lag <= Math.min(maxLag, Math.floor(n / 4)); lag++) {
            let cov = 0;
            for (let t = 0; t < n - lag; t++) {
                cov += (sums[t] - mean) * (sums[t + lag] - mean);
            }
            const r = cov / ((n - lag) * variance);
            const significant = Math.abs(r) > threshold;
            if (significant) anySignificant = true;

            correlations.push({
                lag,
                r: Math.round(r * 10000) / 10000,
                threshold: Math.round(threshold * 10000) / 10000,
                significant
            });
        }

        return {
            testName: 'Autocorrelação Serial',
            correlations,
            threshold: Math.round(threshold * 10000) / 10000,
            significant: anySignificant,
            interpretation: anySignificant
                ? '🟡 CORRELAÇÃO DETECTADA — Pode existir dependência entre sorteios'
                : '✅ SEM CORRELAÇÃO — Cada sorteio é independente do anterior'
        };
    }

    // ═══════════════════════════════════════════════════════════
    //  SCORE POR NÚMERO — Multi-janela com evidência
    //
    //  Para cada número, combina z-scores de múltiplas janelas
    //  Peso maior para janelas onde a evidência é significativa
    //  Score final = evidência ponderada (não frequência bruta)
    // ═══════════════════════════════════════════════════════════
    static _computeNumberScores(draws, cfg, analyses, windows) {
        const [startNum, endNum] = cfg.range;
        const scores = {};

        for (let n = startNum; n <= endNum; n++) {
            let evidenceScore = 0;
            let totalWeight = 0;
            const windowDetails = {};

            for (const w of windows) {
                const a = analyses[w.label];
                if (!a || !a.perNumber || !a.perNumber[n]) continue;

                const data = a.perNumber[n];
                // Peso proporcional à confiança: janelas maiores pesam mais
                // mas janelas com p < 0.05 recebem bônus
                let weight = Math.sqrt(Math.min(w.size, draws.length));
                if (data.pValue < 0.05) weight *= 2.0; // Evidência significativa
                if (data.pValue < 0.01) weight *= 1.5; // Evidência forte

                evidenceScore += data.zScore * weight;
                totalWeight += weight;
                windowDetails[w.label] = {
                    zScore: data.zScore,
                    pValue: data.pValue,
                    deviationPct: data.deviationPct,
                    significant: data.significant
                };
            }

            const finalScore = totalWeight > 0 ? evidenceScore / totalWeight : 0;

            scores[n] = {
                num: n,
                evidenceScore: Math.round(finalScore * 1000) / 1000,
                absEvidence: Math.round(Math.abs(finalScore) * 1000) / 1000,
                direction: finalScore > 0.1 ? 'acima' : finalScore < -0.1 ? 'abaixo' : 'neutro',
                windows: windowDetails,
                // Flag de significância: pelo menos 1 janela com p < 0.05
                hasSignificance: Object.values(windowDetails).some(w => w.significant)
            };
        }

        return scores;
    }

    // ═══════════════════════════════════════════════════════════
    //  CONSTRUIR POOL BASEADO EM EVIDÊNCIA
    //
    //  Estratégia:
    //  1. Se existe viés detectado (p < 0.05):
    //     → Priorizar números com MAIOR desvio positivo significativo
    //  2. Se NÃO existe viés:
    //     → Distribuição equilibrada por zonas
    //     → Alerta ao usuário que sugestão = aleatório
    // ═══════════════════════════════════════════════════════════
    static _buildEvidencePool(numberScores, poolSize, cfg) {
        const allNumbers = Object.values(numberScores)
            .map(s => ({ ...s }));

        // Separar em significativos vs não-significativos
        const significant = allNumbers.filter(s => s.hasSignificance && s.direction === 'acima');
        const neutral = allNumbers.filter(s => !s.hasSignificance || s.direction !== 'acima');

        let pool = [];
        let method = '';

        if (significant.length >= Math.ceil(poolSize * 0.3)) {
            // Existe evidência → priorizar significativos + preencher com equilibrados
            method = 'evidence_weighted';
            significant.sort((a, b) => b.evidenceScore - a.evidenceScore);
            neutral.sort((a, b) => b.evidenceScore - a.evidenceScore);

            // 60% significativos, 40% equilibrados
            const sigCount = Math.min(significant.length, Math.ceil(poolSize * 0.6));
            const neutCount = poolSize - sigCount;

            pool = [
                ...significant.slice(0, sigCount).map(s => s.num),
                ...neutral.slice(0, neutCount).map(s => s.num)
            ];
            console.log('%c[BIAS] 🎯 Pool por EVIDÊNCIA: ' + sigCount + ' significativos + ' + neutCount + ' equilibrados', 'color: #22C55E; font-weight: bold;');
        } else {
            // Sem evidência significativa → distribuição equilibrada por zona
            method = 'balanced_coverage';
            const zonesCount = cfg.zones || 5;
            const perZone = Math.ceil(poolSize / zonesCount);
            const zoneSize = cfg.zoneSize || Math.ceil(cfg.totalNumbers / zonesCount);
            const [startNum] = cfg.range;

            // Distribuir equilibradamente por zona, ordenando por score dentro de cada zona
            for (let z = 0; z < zonesCount; z++) {
                const zoneStart = startNum + z * zoneSize;
                const zoneEnd = Math.min(startNum + (z + 1) * zoneSize - 1, cfg.range[1]);
                const zoneNumbers = allNumbers
                    .filter(s => s.num >= zoneStart && s.num <= zoneEnd)
                    .sort((a, b) => b.evidenceScore - a.evidenceScore)
                    .slice(0, perZone);
                pool.push(...zoneNumbers.map(s => s.num));
            }
            pool = pool.slice(0, poolSize);
            console.log('%c[BIAS] ⚖️ Pool EQUILIBRADO (sem viés detectado): ' + pool.length + ' números em ' + zonesCount + ' zonas', 'color: #F59E0B; font-weight: bold;');
        }

        pool.sort((a, b) => a - b);

        return {
            numbers: pool,
            method,
            size: pool.length,
            hasStatisticalBasis: method === 'evidence_weighted',
            warning: method === 'balanced_coverage'
                ? 'Nenhum viés significativo detectado. Pool equilibrado por zonas — equivalente a seleção aleatória.'
                : null
        };
    }

    // ═══════════════════════════════════════════════════════════
    //  ANÁLISE DE JANELA (Chi-² parcial)
    // ═══════════════════════════════════════════════════════════
    static _analyzeWindow(draws, cfg) {
        const [startNum, endNum] = cfg.range;
        const totalNumbers = endNum - startNum + 1;
        const totalDrawn = draws.length * cfg.drawSize;
        const expected = totalDrawn / totalNumbers;

        const observed = {};
        for (let n = startNum; n <= endNum; n++) observed[n] = 0;
        for (const draw of draws) {
            for (const num of draw) observed[num] = (observed[num] || 0) + 1;
        }

        const perNumber = {};
        for (let n = startNum; n <= endNum; n++) {
            const o = observed[n] || 0;
            const deviation = o - expected;
            const zScore = deviation / Math.sqrt(Math.max(expected, 0.1));
            const pValue = 2 * (1 - this._normalCDF(Math.abs(zScore)));
            perNumber[n] = {
                observed: o, expected: Math.round(expected * 10) / 10,
                deviation: Math.round(deviation * 10) / 10,
                deviationPct: Math.round((deviation / Math.max(expected, 0.01)) * 1000) / 10,
                zScore: Math.round(zScore * 100) / 100,
                pValue: Math.round(pValue * 10000) / 10000,
                significant: pValue < 0.05
            };
        }

        return { draws: draws.length, expected, perNumber };
    }

    // ═══════════════════════════════════════════════════════════
    //  VEREDICTO FINAL
    // ═══════════════════════════════════════════════════════════
    static _buildVerdict(chiSq, runs, autocorr) {
        const biasDetected = chiSq.significant;
        const dependenceDetected = !runs.independent;
        const correlationDetected = autocorr.significant;

        let level = 'ALEATÓRIO';
        let emoji = '✅';
        let recommendation = 'Foque em COBERTURA COMBINATÓRIA (CoverageEngine). Sugestões de números são equivalentes a seleção aleatória.';

        if (chiSq.strongSignificant || (biasDetected && dependenceDetected)) {
            level = 'VIÉS FORTE';
            emoji = '🔴';
            recommendation = 'Evidência forte de viés. Pool sugerido prioriza números com desvio estatisticamente significativo.';
        } else if (biasDetected || dependenceDetected || correlationDetected) {
            level = 'VIÉS POSSÍVEL';
            emoji = '🟡';
            recommendation = 'Evidência marginal de viés. Pool sugerido considera os desvios, mas com cautela.';
        }

        return {
            level,
            emoji,
            biasDetected,
            dependenceDetected,
            correlationDetected,
            recommendation,
            summary: emoji + ' ' + level + ' — ' + recommendation
        };
    }

    // ═══════════════════════════════════════════════════════════
    //  FUNÇÕES MATEMÁTICAS PURAS
    // ═══════════════════════════════════════════════════════════

    /**
     * CDF da distribuição normal padrão (Φ(z))
     * Aproximação de Abramowitz & Stegun (fórmula 7.1.26)
     * Erro máximo: 1.5 × 10⁻⁷
     */
    static _normalCDF(z) {
        if (z < -8) return 0;
        if (z > 8) return 1;
        const a1 = 0.254829592, a2 = -0.284496736, a3 = 1.421413741;
        const a4 = -1.453152027, a5 = 1.061405429, p = 0.3275911;
        const sign = z < 0 ? -1 : 1;
        const x = Math.abs(z) / Math.sqrt(2);
        const t = 1.0 / (1.0 + p * x);
        const y = 1.0 - (((((a5 * t + a4) * t) + a3) * t + a2) * t + a1) * t * Math.exp(-x * x);
        return 0.5 * (1.0 + sign * y);
    }

    /**
     * CDF da distribuição Chi-Quadrado
     * Usa a função gamma incompleta regularizada
     * Baseado na aproximação de Wilson-Hilferty para df > 30
     * e série para df <= 30
     */
    static _chiSquaredCDF(x, df) {
        if (x <= 0) return 0;
        if (df <= 0) return 1;

        // Para df grande, usar aproximação de Wilson-Hilferty
        if (df > 100) {
            const z = Math.pow(x / df, 1/3) - (1 - 2 / (9 * df));
            const denom = Math.sqrt(2 / (9 * df));
            return this._normalCDF(z / denom);
        }

        // Para df menor, usar função gamma incompleta
        return this._regularizedGammaP(df / 2, x / 2);
    }

    /**
     * Função Gamma Incompleta Regularizada P(a, x)
     * Implementação por série para x < a+1, fração contínua para x >= a+1
     */
    static _regularizedGammaP(a, x) {
        if (x < 0) return 0;
        if (x === 0) return 0;

        if (x < a + 1) {
            // Série
            let sum = 1 / a;
            let term = 1 / a;
            for (let n = 1; n < 200; n++) {
                term *= x / (a + n);
                sum += term;
                if (Math.abs(term) < 1e-12 * Math.abs(sum)) break;
            }
            return sum * Math.exp(-x + a * Math.log(x) - this._logGamma(a));
        } else {
            // Fração contínua (Lentz's method)
            return 1 - this._regularizedGammaQ(a, x);
        }
    }

    /**
     * Função Gamma Incompleta Regularizada Q(a, x) = 1 - P(a, x)
     * Fração contínua
     */
    static _regularizedGammaQ(a, x) {
        let f = 1e-30;
        let c = 1e-30;
        let d = 1 / (x + 1 - a);
        let h = d;

        for (let i = 1; i < 200; i++) {
            const an = -i * (i - a);
            const bn = x + 2 * i + 1 - a;
            d = bn + an * d;
            if (Math.abs(d) < 1e-30) d = 1e-30;
            c = bn + an / c;
            if (Math.abs(c) < 1e-30) c = 1e-30;
            d = 1 / d;
            const del = d * c;
            h *= del;
            if (Math.abs(del - 1) < 1e-12) break;
        }

        return Math.exp(-x + a * Math.log(x) - this._logGamma(a)) * h;
    }

    /**
     * Log da função Gamma — Aproximação de Stirling
     */
    static _logGamma(z) {
        if (z < 0.5) {
            // Reflexão: Γ(z) = π / (sin(πz) × Γ(1-z))
            return Math.log(Math.PI / Math.sin(Math.PI * z)) - this._logGamma(1 - z);
        }
        z -= 1;
        const g = 7;
        const c = [
            0.99999999999980993, 676.5203681218851, -1259.1392167224028,
            771.32342877765313, -176.61502916214059, 12.507343278686905,
            -0.13857109526572012, 9.9843695780195716e-6, 1.5056327351493116e-7
        ];
        let x = c[0];
        for (let i = 1; i < g + 2; i++) x += c[i] / (z + i);
        const t = z + g + 0.5;
        return 0.5 * Math.log(2 * Math.PI) + (z + 0.5) * Math.log(t) - t + Math.log(x);
    }

    // ═══════════════════════════════════════════════════════════
    //  UTILITÁRIOS
    // ═══════════════════════════════════════════════════════════

    static _extractDraws(history, cfg) {
        if (!history || !Array.isArray(history)) return [];
        // Suporta formato [{numbers: [...]}, ...] ou [[...], ...]
        return history.map(entry => {
            if (Array.isArray(entry)) return entry;
            if (entry.numbers) return entry.numbers;
            if (entry.dezenas) return entry.dezenas.map(Number);
            if (entry.listaDezenas) return entry.listaDezenas.map(Number);
            return null;
        }).filter(d => d && d.length >= cfg.drawSize);
    }

    static _getConfig(gameKey) {
        const configs = {
            lotofacil: { name: 'Lotofácil', drawSize: 15, range: [1, 25], totalNumbers: 25, zones: 5, zoneSize: 5 },
            megasena:  { name: 'Mega Sena', drawSize: 6, range: [1, 60], totalNumbers: 60, zones: 6, zoneSize: 10 },
            quina:     { name: 'Quina', drawSize: 5, range: [1, 80], totalNumbers: 80, zones: 8, zoneSize: 10 },
            duplasena: { name: 'Dupla Sena', drawSize: 6, range: [1, 50], totalNumbers: 50, zones: 5, zoneSize: 10 },
            lotomania: { name: 'Lotomania', drawSize: 20, range: [0, 99], totalNumbers: 100, zones: 10, zoneSize: 10 },
            timemania: { name: 'Timemania', drawSize: 7, range: [1, 80], totalNumbers: 80, zones: 8, zoneSize: 10 },
            diadesorte:{ name: 'Dia de Sorte', drawSize: 7, range: [1, 31], totalNumbers: 31, zones: 4, zoneSize: 8 }
        };
        return configs[gameKey] || null;
    }

    static _logResults(chiSq, runs, autocorr, verdict) {
        console.log('%c[BIAS] ── RESULTADOS DOS TESTES FORMAIS ──', 'color: #8B5CF6; font-weight: bold;');
        console.log('[BIAS] ' + chiSq.interpretation);
        console.log('[BIAS]   χ²=' + chiSq.chiSquared + ' | df=' + chiSq.degreesOfFreedom + ' | p=' + chiSq.pValue);
        console.log('[BIAS] ' + runs.interpretation);
        console.log('[BIAS]   Testados=' + runs.numbersTested + ' | Dependentes=' + runs.dependentNumbers + ' | p_combinado=' + runs.combinedPValue);
        console.log('[BIAS] ' + autocorr.interpretation);
        for (const c of autocorr.correlations) {
            console.log('[BIAS]   lag ' + c.lag + ': r=' + c.r + (c.significant ? ' ⚠️ SIGNIFICATIVO' : ''));
        }
        console.log('%c[BIAS] ══ VEREDICTO: ' + verdict.summary, 'color: ' + (verdict.level === 'ALEATÓRIO' ? '#22C55E' : verdict.level === 'VIÉS POSSÍVEL' ? '#F59E0B' : '#EF4444') + '; font-weight: bold; font-size: 14px;');
    }
}

// Exportar globalmente
if (typeof window !== 'undefined') window.StatisticalBiasEngine = StatisticalBiasEngine;
console.log('%c[BIAS] ✓ Detector de Viés Estatístico v1.0 carregado', 'color: #8B5CF6; font-weight: bold;');
