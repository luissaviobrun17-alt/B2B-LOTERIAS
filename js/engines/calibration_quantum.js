/**
 * ╔══════════════════════════════════════════════════════════════════════╗
 * ║  QUANTUM CALIBRATION ENGINE — MOTOR DE CALIBRAÇÃO META-HEURÍSTICO  ║
 * ║  Versão: QCAL-V3 (Universal — Todas as Loterias)                   ║
 * ╠══════════════════════════════════════════════════════════════════════╣
 * ║  VETOR 1: ENTROPIA E MECÂNICA QUÂNTICA                             ║
 * ║    • Colapso de função de onda em sorteios passados                ║
 * ║    • Emaranhamento temporal — atratores estranhos                   ║
 * ║    • Simulação de flutuação de qubits                              ║
 * ║                                                                    ║
 * ║  VETOR 2: CLARIVIDÊNCIA COMPUTACIONAL                              ║
 * ║    • Densidade de probabilidade de conjuntos não sorteados         ║
 * ║    • Varredura de padrões de "vácuo" (ausência + pressão estatíst) ║
 * ║    • Projeção de cenários de previsibilidade                       ║
 * ║                                                                    ║
 * ║  VETOR 3: FILTROS DE CALIBRAÇÃO ATÔMICA                           ║
 * ║    • Equilíbrio Térmico: Proporção Par/Ímpar baseada em histórico  ║
 * ║    • Distribuição de Quadrantes: Evitar aglomerações               ║
 * ║    • Frequência de Fibonacci e Primos (proporção áurea)            ║
 * ╚══════════════════════════════════════════════════════════════════════╝
 * "O passado não é apenas um evento — é um colapso de função de onda."
 */

const QuantumCalibration = {

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // CONFIGURAÇÕES POR LOTERIA (limites reais baseados em dados)
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    GAME_CONFIG: {
        megasena:   { min: 1,  max: 60,  draw: 6,  name: 'Mega Sena',   vacuumWindow: 8,  enthropyDepth: 30 },
        lotofacil:  { min: 1,  max: 25,  draw: 15, name: 'Lotofácil',   vacuumWindow: 5,  enthropyDepth: 20 },
        quina:      { min: 1,  max: 80,  draw: 5,  name: 'Quina',       vacuumWindow: 10, enthropyDepth: 35 },
        duplasena:  { min: 1,  max: 50,  draw: 6,  name: 'Dupla Sena',  vacuumWindow: 8,  enthropyDepth: 30 },
        lotomania:  { min: 0,  max: 99,  draw: 20, name: 'Lotomania',   vacuumWindow: 6,  enthropyDepth: 25 },
        timemania:  { min: 1,  max: 80,  draw: 10, name: 'Timemania',   vacuumWindow: 10, enthropyDepth: 35 },
        diadesorte: { min: 1,  max: 31,  draw: 7,  name: 'Dia de Sorte',vacuumWindow: 6,  enthropyDepth: 20 }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // MÉTODO PRINCIPAL: Calibrar scores para um conjunto de jogos
    // Retorna mapa de scores { num: score } para todos os números
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    calibrate(gameKey, history, drawSize) {
        const cfg = this.GAME_CONFIG[gameKey];
        if (!cfg || !history || history.length < 3) return null;

        const min = cfg.min, max = cfg.max;
        console.log('[QCAL-V3] ⚛️ Calibração Quântica ativada: ' + cfg.name + ' (' + history.length + ' sorteios)');

        // ── VETOR 1: ENTROPIA QUÂNTICA ──────────────────────────────
        const entropyScores  = this._vector1_QuantumEntropy(history, min, max, cfg);

        // ── VETOR 2: CLARIVIDÊNCIA COMPUTACIONAL ───────────────────
        const vacuumScores   = this._vector2_ComputationalClairvoyance(history, min, max, cfg, drawSize);

        // ── VETOR 3: FILTROS ATÔMICOS ──────────────────────────────
        const atomicScores   = this._vector3_AtomicFilters(history, min, max, cfg, drawSize);

        // ── SÍNTESE FINAL: Coordenadas de Colapso Probabilístico ───
        const finalScores = {};
        for (let n = min; n <= max; n++) {
            finalScores[n] =
                (entropyScores[n]  || 0) * 0.38 +   // Entropia: maior peso (padrão temporal)
                (vacuumScores[n]   || 0) * 0.38 +   // Vácuo: igual ao entropia (pressão acumulada)
                (atomicScores[n]   || 0) * 0.24;    // Filtros: calibração fina
        }

        // Normalizar para [0,1]
        const norm = this._normalize(finalScores, min, max);

        console.log('[QCAL-V3] ✅ ' + cfg.name + ': ' + Object.keys(norm).length + ' coordenadas de colapso calculadas');
        return norm;
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // VETOR 1: ENTROPIA E MECÂNICA QUÂNTICA
    // Conceito: cada sorteio é um "colapso de função de onda"
    // Detecta atratores estranhos (padrões recorrentes não lineares)
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _vector1_QuantumEntropy(history, min, max, cfg) {
        const scores = {};
        for (let n = min; n <= max; n++) scores[n] = 0;

        const depth = Math.min(cfg.enthropyDepth, history.length);

        // ── 1a. EMARANHAMENTO TEMPORAL: correlação entre sorteios não adjacentes
        // "Se X saiu no sorteio T-k, qual a prob de sair em T?"
        // Detecta padrões de período (q: número de sorteios entre aparições)
        const periodMap = {};
        for (let n = min; n <= max; n++) {
            const appearances = [];
            for (let i = 0; i < depth; i++) {
                if ((history[i].numbers || []).concat(history[i].numbers2 || []).includes(n)) {
                    appearances.push(i);
                }
            }
            if (appearances.length < 2) { periodMap[n] = null; continue; }

            // Calcular períodos entre aparições
            const periods = [];
            for (let k = 1; k < appearances.length; k++) {
                periods.push(appearances[k] - appearances[k-1]);
            }

            // Período médio e desvio padrão
            const avgPeriod = periods.reduce((s, p) => s + p, 0) / periods.length;
            const stdPeriod = Math.sqrt(periods.reduce((s, p) => s + (p - avgPeriod)**2, 0) / periods.length);

            periodMap[n] = { avgPeriod, stdPeriod, appearances, lastSeen: appearances[0] };
        }

        // ── 1b. ATRATORES ESTRANHOS: Números que mostram periodicidade estável
        // Score alto = número que "deve" sair em breve segundo seu período próprio
        for (let n = min; n <= max; n++) {
            if (!periodMap[n]) { scores[n] += 0.30; continue; }
            const { avgPeriod, stdPeriod, lastSeen } = periodMap[n];

            if (avgPeriod <= 0) { scores[n] += 0.20; continue; }

            // Há quantos sorteios o número "deveria" ter saído pela última vez?
            const expectedAtSorteio = lastSeen + avgPeriod;
            const currentSorteio = 0; // sorteio 0 = o próximo (estamos prevendo)
            const distToExpected = Math.abs(expectedAtSorteio - currentSorteio);

            // Coeficiente de entropia: < stdDev = alta probabilidade de colapso
            const entropyCoeff = stdPeriod > 0
                ? Math.exp(-distToExpected / (stdPeriod * 2))
                : (distToExpected < 2 ? 1.0 : 0.1);

            // Estabilidade do período (baixo desvio = atrator estável)
            const stability = avgPeriod > 0 ? Math.max(0, 1 - stdPeriod / avgPeriod) : 0.5;

            scores[n] += entropyCoeff * stability * 0.7 + 0.1;
        }

        // ── 1c. FLUTUAÇÃO DE QUBITS: Injeção de variância quântica
        // Simula o efeito de um qubit que "flutua" entre estados
        // Números próximos a número muito quentes têm chance de "tunelamento"
        const recentSet = new Set((history[0]?.numbers || []).concat(history[0]?.numbers2 || []));
        const prevSet   = new Set((history[1]?.numbers || []).concat(history[1]?.numbers2 || []));

        for (let n = min; n <= max; n++) {
            // Tunelamento quântico: número vizinho de um número quente
            const neighbors = [n-2, n-1, n+1, n+2].filter(x => x >= min && x <= max);
            let tunnelScore = 0;
            for (const nb of neighbors) {
                if (recentSet.has(nb)) tunnelScore += 0.15;
                if (prevSet.has(nb))   tunnelScore += 0.08;
            }
            scores[n] += Math.min(0.4, tunnelScore);

            // Anti-correlação: número que saiu no sorteio anterior tende a não sair (exceto Lotofácil)
            if (recentSet.has(n) && cfg.draw < 15) scores[n] *= 0.65;
        }

        // ── 1d. TENDÊNCIA DE ENTROPIA LOCAL: Shannon Entropy por janela
        // Mede o "caos" recente — zonas de alta entropia têm mais probabilidade
        const numZones = Math.ceil((max - min + 1) / 10);
        const zoneEntropyBonus = new Array(numZones).fill(0);

        for (let z = 0; z < numZones; z++) {
            const zMin = min + z * 10;
            const zMax = Math.min(max, zMin + 9);
            const zRange = zMax - zMin + 1;

            // Contar aparições por número na zona (últimos 10 sorteios)
            const zCounts = {};
            const windowSize = Math.min(10, history.length);
            for (let i = 0; i < windowSize; i++) {
                const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
                for (const n of nums) {
                    if (n >= zMin && n <= zMax) zCounts[n] = (zCounts[n] || 0) + 1;
                }
            }

            // Calcular entropia de Shannon para a zona
            const total = Object.values(zCounts).reduce((s, c) => s + c, 0);
            if (total === 0) { zoneEntropyBonus[z] = 0.5; continue; }

            let entropy = 0;
            for (const c of Object.values(zCounts)) {
                const p = c / total;
                if (p > 0) entropy -= p * Math.log2(p);
            }
            const maxEntropy = Math.log2(zRange);
            zoneEntropyBonus[z] = maxEntropy > 0 ? (entropy / maxEntropy) * 0.3 : 0.15;
        }

        // Aplicar bônus de zona
        for (let n = min; n <= max; n++) {
            const z = Math.min(numZones - 1, Math.floor((n - min) / 10));
            scores[n] += zoneEntropyBonus[z];
        }

        return scores;
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // VETOR 2: CLARIVIDÊNCIA COMPUTACIONAL
    // Identifica "vácuos": números com ausência prolongada + alta
    // pressão estatística para retorno
    // Calcula densidade de probabilidade de conjuntos não sorteados
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _vector2_ComputationalClairvoyance(history, min, max, cfg, drawSize) {
        const scores = {};
        for (let n = min; n <= max; n++) scores[n] = 0;

        const totalRange = max - min + 1;
        const N = history.length;
        if (N < 3) return scores;

        // ── 2a. ANÁLISE DE VÁCUO (ausência prolongada + pressão de retorno)
        // Calcula há quantos sorteios cada número não aparece (delay)
        // E a "pressão estatística" acumulada nesse período
        const expectedFreq = drawSize / totalRange; // Frequência esperada por sorteio
        const delay        = {};
        const cumPressure  = {};

        for (let n = min; n <= max; n++) {
            let lastSeen = -1;
            for (let i = 0; i < N; i++) {
                const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
                if (nums.includes(n)) { lastSeen = i; break; }
            }
            delay[n] = lastSeen < 0 ? N : lastSeen;

            // Pressão acumulada = soma de "chances perdidas"
            // Quanto mais sorteios sem aparecer, maior a pressão
            const d = delay[n];
            const pressureRaw = d * expectedFreq; // Probabilidade acumulada "devida"
            // Função sigmoide suaviza valores extremos
            cumPressure[n] = 2 / (1 + Math.exp(-pressureRaw * 0.8)) - 1;
        }

        // ── 2b. DENSIDADE DE PROBABILIDADE DE CONJUNTOS
        // Monte Carlo leve: simular quais combinações ainda não saíram
        // e identificar quais números aparecem em combinações "sob-representadas"
        // Monte Carlo leve: 60 iterações (era 500 — gargalo crítico com 1000 jogos)
        const MONTE_RUNS = 60;

        const combinationDensity = {};
        for (let n = min; n <= max; n++) combinationDensity[n] = 0;

        // Verificar quais números são mais comuns em combinações recentes (últimos vacuumWindow sorteios)
        const recentWindow = Math.min(cfg.vacuumWindow, N);
        const recentNumbers = new Set();
        for (let i = 0; i < recentWindow; i++) {
            const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            for (const n of nums) {
                if (n >= min && n <= max) recentNumbers.add(n);
            }
        }

        // Números NÃO em recentNumbers têm maior densidade de combinações "frescas"
        for (let n = min; n <= max; n++) {
            if (!recentNumbers.has(n)) {
                combinationDensity[n] += 0.6; // Não apareceu na janela recente
            }
        }

        // Monte Carlo: sortear combinações aleatórias ponderadas por pressão e ver quais números dominam
        for (let run = 0; run < MONTE_RUNS; run++) {
            const candidate = [];
            const used = new Set();
            // Sortear números com peso proporcional à pressão acumulada
            const pool = Array.from({ length: totalRange }, (_, i) => min + i);
            const weights = pool.map(n => Math.max(0.01, cumPressure[n] + 0.1));
            const totalW = weights.reduce((s, w) => s + w, 0);

            for (let k = 0; k < drawSize && candidate.length < drawSize; k++) {
                let rand = Math.random() * totalW;
                for (let j = 0; j < pool.length; j++) {
                    if (used.has(pool[j])) { rand -= 0; continue; }
                    rand -= weights[j];
                    if (rand <= 0) {
                        candidate.push(pool[j]);
                        used.add(pool[j]);
                        break;
                    }
                }
            }

            // Verificar se essa combinação é "nova" (não apareceu no histórico recente)
            const isNew = !history.slice(0, Math.min(5, N)).some(draw => {
                const dNums = (draw.numbers || []).concat(draw.numbers2 || []);
                let overlap = 0;
                for (const n of candidate) if (dNums.includes(n)) overlap++;
                return overlap >= Math.ceil(drawSize * 0.7);
            });

            // Se a combinação é "nova", os números nela ganham peso de densidade
            if (isNew) {
                for (const n of candidate) {
                    combinationDensity[n] += 1 / MONTE_RUNS;
                }
            }
        }

        // ── 2c. AFINIDADE GEOMÉTRICA E ARITMÉTICA
        // Detectar progressões numéricas que ainda não apareceram
        // Ex: 10, 20, 30 (progressão aritmética) ou 2, 4, 8 (geométrica)
        const arithBonus = {};
        for (let n = min; n <= max; n++) arithBonus[n] = 0;

        // Verificar progressões aritméticas de passo entre 2 e 5
        for (let step = 2; step <= 5; step++) {
            for (let start = min; start <= max - step * 2; start++) {
                const trio = [start, start + step, start + step * 2].filter(x => x >= min && x <= max);
                if (trio.length < 3) continue;

                // Verificar se esse trio não apareceu nos últimos sorteios
                const appearedRecently = history.slice(0, Math.min(8, N)).some(draw => {
                    const dNums = new Set((draw.numbers || []).concat(draw.numbers2 || []));
                    return trio.every(n => dNums.has(n));
                });

                if (!appearedRecently) {
                    // Este padrão está em "vácuo" — boost leve
                    for (const n of trio) arithBonus[n] += 0.08;
                }
            }
        }

        // ── SÍNTESE DO VETOR 2 ────────────────────────────────────
        for (let n = min; n <= max; n++) {
            scores[n] =
                cumPressure[n]         * 0.45 +    // Pressão de vácuo (principal)
                combinationDensity[n]  * 0.35 +    // Densidade de combinações frescas
                (arithBonus[n] || 0)   * 0.20;     // Afinidade geométrica
        }

        return scores;
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // VETOR 3: FILTROS DE CALIBRAÇÃO ATÔMICA
    // Aplica parâmetros de refinamento baseados em dados históricos reais
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _vector3_AtomicFilters(history, min, max, cfg, drawSize) {
        const scores = {};
        for (let n = min; n <= max; n++) scores[n] = 0;

        const N = history.length;
        if (N < 2) return scores;

        // ── 3a. EQUILÍBRIO TÉRMICO: Proporção Par/Ímpar histórica
        // Analisa qual proporção real ocorre nos sorteios
        let totalEven = 0, totalCount = 0;
        const windowSize = Math.min(20, N);
        for (let i = 0; i < windowSize; i++) {
            const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            const relevant = nums.filter(n => n >= min && n <= max);
            if (relevant.length === 0) continue;
            totalEven += relevant.filter(n => n % 2 === 0).length;
            totalCount += relevant.length;
        }

        const historicalEvenRatio = totalCount > 0 ? totalEven / totalCount : 0.5;
        // Score para pares e ímpares baseado na proporção histórica
        for (let n = min; n <= max; n++) {
            if (n % 2 === 0) {
                // Número par: score proporcional à frequência histórica de pares
                scores[n] += historicalEvenRatio * 0.5 + 0.25;
            } else {
                // Número ímpar: score inversamente proporcional
                scores[n] += (1 - historicalEvenRatio) * 0.5 + 0.25;
            }
        }

        // ── 3b. DISTRIBUIÇÃO DE QUADRANTES: Evitar aglomerações
        // Divide o volante em 4 quadrantes e analisa distribuição histórica
        const totalRange = max - min + 1;
        const quadrantSize = Math.ceil(totalRange / 4);
        const quadrantFreq = [0, 0, 0, 0];
        let quadrantTotal = 0;

        for (let i = 0; i < windowSize; i++) {
            const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            for (const n of nums) {
                if (n < min || n > max) continue;
                const q = Math.min(3, Math.floor((n - min) / quadrantSize));
                quadrantFreq[q]++;
                quadrantTotal++;
            }
        }

        const quadrantIdealRatio = 1 / 4; // 25% por quadrante
        for (let n = min; n <= max; n++) {
            const q = Math.min(3, Math.floor((n - min) / quadrantSize));
            const qRatio = quadrantTotal > 0 ? quadrantFreq[q] / quadrantTotal : quadrantIdealRatio;

            // Boost para quadrantes sub-representados, penalidade para super-representados
            const deviation = quadrantIdealRatio - qRatio;
            scores[n] += deviation * 1.2 + 0.3; // desvio positivo = boost, negativo = redução
        }

        // ── 3c. FIBONACCI E PROPORÇÃO ÁUREA
        // Números na sequência de Fibonacci ou próximos da razão áurea
        // têm propriedades de distribuição mais naturais
        const phi = (1 + Math.sqrt(5)) / 2; // 1.618...
        const fibNumbers = this._getFibonacciInRange(min, max);
        const fibSet = new Set(fibNumbers);

        for (let n = min; n <= max; n++) {
            if (fibSet.has(n)) {
                scores[n] += 0.35; // Boost para números Fibonacci
            } else {
                // Verificar proximidade à razão áurea
                const phiNeighbor = Math.round(n * phi);
                if (phiNeighbor >= min && phiNeighbor <= max) {
                    scores[n] += 0.15; // Boost para números com vizinho-phi no range
                }
            }
        }

        // ── 3d. ANÁLISE DE PRIMOS: Proporção histórica
        const primesInRange = this._getPrimesInRange(min, max);
        const primeSet = new Set(primesInRange);

        // Calcular proporção histórica de primos
        let totalPrimesHist = 0, totalNumsHist = 0;
        for (let i = 0; i < windowSize; i++) {
            const nums = (history[i].numbers || []).concat(history[i].numbers2 || []);
            const relevant = nums.filter(n => n >= min && n <= max);
            totalPrimesHist += relevant.filter(n => primeSet.has(n)).length;
            totalNumsHist += relevant.length;
        }

        const historicalPrimeRatio = totalNumsHist > 0 ? totalPrimesHist / totalNumsHist : 0.3;
        const primeRangeRatio = primesInRange.length / (max - min + 1);

        for (let n = min; n <= max; n++) {
            if (primeSet.has(n)) {
                // Score proporcional à frequência histórica de primos
                const primeBoost = historicalPrimeRatio / Math.max(0.01, primeRangeRatio);
                scores[n] += Math.min(0.4, primeBoost * 0.25);
            }
        }

        // ── 3e. SOMA IDEAL: Faixa de soma baseada em dados históricos reais
        // Calcular faixa de soma dos sorteios reais
        const sums = [];
        for (let i = 0; i < Math.min(30, N); i++) {
            const nums = (history[i].numbers || []).filter(n => n >= min && n <= max);
            if (nums.length === drawSize) {
                sums.push(nums.reduce((s, x) => s + x, 0));
            }
        }

        if (sums.length > 3) {
            sums.sort((a, b) => a - b);
            const p10 = sums[Math.floor(sums.length * 0.10)];
            const p90 = sums[Math.floor(sums.length * 0.90)];
            const medianSum = sums[Math.floor(sums.length * 0.50)];

            // Dar boost a números cujo valor numérico os posiciona bem na soma
            // (heurística: preferir números que "cabem" na faixa ideal)
            const avgSumTarget = medianSum / drawSize;
            for (let n = min; n <= max; n++) {
                const distToIdeal = Math.abs(n - avgSumTarget);
                const sumScore = Math.exp(-distToIdeal * distToIdeal / (avgSumTarget * avgSumTarget));
                scores[n] += sumScore * 0.3;
            }
        }

        return scores;
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // MÉTODO DE PÓS-FILTRO: Aplica calibração quântica sobre um jogo
    // Verifica se um jogo já gerado passa pelos filtros atômicos
    // Retorna score de qualidade [0-1]
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    scoreGame(ticket, gameKey, history, calibrationScores) {
        if (!ticket || ticket.length === 0) return 0;
        const cfg = this.GAME_CONFIG[gameKey];
        if (!cfg) return 0.5;

        const N = history ? history.length : 0;
        const drawSize = ticket.length;
        let score = 0;

        // Score base: soma dos scores calibrados dos números
        if (calibrationScores) {
            const avgCalib = ticket.reduce((s, n) => s + (calibrationScores[n] || 0), 0) / drawSize;
            score += avgCalib * 0.5;
        }

        // ── FILTRO ATÔMICO: Equilíbrio Par/Ímpar ──
        const evenCount = ticket.filter(n => n % 2 === 0).length;
        const oddCount  = drawSize - evenCount;
        const evenRatio = evenCount / drawSize;
        // Penalizar extremos: 0% ou 100% pares = score reduzido
        const thermalBalance = 1 - Math.abs(evenRatio - 0.5) * 1.5;
        score += Math.max(0, thermalBalance) * 0.15;

        // ── FILTRO DE QUADRANTE: Verificar distribuição ──
        const min = cfg.min, max = cfg.max;
        const totalRange = max - min + 1;
        const quadrantSize = Math.ceil(totalRange / 4);
        const qCount = [0, 0, 0, 0];
        for (const n of ticket) {
            const q = Math.min(3, Math.floor((n - min) / quadrantSize));
            qCount[q]++;
        }
        const ideal = drawSize / 4;
        const qDeviation = qCount.reduce((s, c) => s + Math.abs(c - ideal), 0) / drawSize;
        score += Math.max(0, 1 - qDeviation) * 0.20;

        // ── FILTRO DE FIBONACCI: Verificar proporção ──
        const fibs = this._getFibonacciInRange(min, max);
        const fibSet = new Set(fibs);
        const fibCount = ticket.filter(n => fibSet.has(n)).length;
        const fibRatio = fibCount / drawSize;
        // Proporção ideal de Fibonacci na maioria das loterias: 15-40%
        const fibScore = 1 - Math.abs(fibRatio - 0.25) * 2;
        score += Math.max(0, fibScore) * 0.10;

        // ── ANTI-SEQUÊNCIA: Penalizar más de 2 consecutivos ──
        let maxRun = 1, curRun = 1;
        const sorted = [...ticket].sort((a, b) => a - b);
        for (let i = 1; i < sorted.length; i++) {
            if (sorted[i] === sorted[i-1] + 1) { curRun++; maxRun = Math.max(maxRun, curRun); }
            else curRun = 1;
        }
        if (maxRun >= 3) score -= 0.15;
        if (maxRun >= 4) score -= 0.20;

        return Math.max(0, Math.min(1, score));
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // FUNÇÕES AUXILIARES
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

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
    },

    _getFibonacciInRange(min, max) {
        const fibs = [];
        let a = 1, b = 1;
        while (a <= max) {
            if (a >= min) fibs.push(a);
            [a, b] = [b, a + b];
        }
        return fibs;
    },

    _getPrimesInRange(min, max) {
        const sieve = new Array(max + 1).fill(true);
        sieve[0] = sieve[1] = false;
        for (let i = 2; i * i <= max; i++) {
            if (sieve[i]) for (let j = i * i; j <= max; j += i) sieve[j] = false;
        }
        const primes = [];
        for (let n = Math.max(2, min); n <= max; n++) {
            if (sieve[n]) primes.push(n);
        }
        return primes;
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // GERAR JOGOS COM CALIBRAÇÃO QUÂNTICA TOTAL
    // Método de entrada para uso direto
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    generateCalibratedGames(gameKey, numGames, history, drawSize, fixedNumbers) {
        const cfg = this.GAME_CONFIG[gameKey];
        if (!cfg) return [];

        const calibScores = this.calibrate(gameKey, history, drawSize || cfg.draw);
        if (!calibScores) return [];

        const min = cfg.min, max = cfg.max;
        const draw = drawSize || cfg.draw;
        const fixed = fixedNumbers || [];

        // Criar pool ponderado pelos scores calibrados
        const allNums = Array.from({ length: max - min + 1 }, (_, i) => min + i);

        // Ordenar por score calibrado (top 60% do pool)
        const poolSize = Math.max(draw * 3, Math.min(allNums.length, draw * 6));
        const sorted   = allNums.sort((a, b) => (calibScores[b] || 0) - (calibScores[a] || 0));
        const basePool  = sorted.slice(0, poolSize);

        const games   = [];
        const usedKeys = new Set();
        const usedCount = {};
        basePool.forEach(n => usedCount[n] = 0);

        const maxUsePerNum = Math.max(3, Math.ceil(numGames * 0.30));
        let attempts = 0;
        // LIMITE EXPANDIDO: suporta 10.000+ jogos
        const maxAttempts = Math.min(numGames * 500, 5000000);
        const tStart = Date.now();
        const MAX_MS  = 180000; // 3 minutos

        while (games.length < numGames && attempts < maxAttempts && (Date.now() - tStart) < MAX_MS) {
            attempts++;


            // Pesos dinâmicos: combina calibração + penalidade de uso
            const ticket = [...fixed.filter(f => basePool.includes(f) && f >= min && f <= max)];
            const usedSet = new Set(ticket);

            const available = basePool.filter(n => !usedSet.has(n) && (usedCount[n] || 0) < maxUsePerNum);
            if (available.length < draw - ticket.length) {
                // Ampliar pool se necessário
                const extra = allNums.filter(n => !usedSet.has(n) && !basePool.includes(n));
                for (const n of extra) {
                    if (available.length + extra.indexOf(n) + 1 >= draw) break;
                    available.push(n);
                }
            }

            const weights = available.map(n => {
                const calScore = (calibScores[n] || 0.01) + 0.1;
                const usagePen = Math.pow(1 - (usedCount[n] || 0) / maxUsePerNum, 2);
                const noise    = Math.random() * 0.25;
                return calScore * usagePen + noise;
            });

            // Seleção ponderada até completar o jogo
            const totalW = weights.reduce((s, w) => s + w, 0);
            while (ticket.length < draw && available.length > 0) {
                let rand = Math.random() * totalW;
                let chosen = available[0];
                let chosenIdx = 0;
                for (let k = 0; k < available.length; k++) {
                    rand -= weights[k];
                    if (rand <= 0) { chosen = available[k]; chosenIdx = k; break; }
                }

                // Anti-sequência: evitar 3+ consecutivos
                if (ticket.length >= 2) {
                    const sorted = [...ticket, chosen].sort((a, b) => a - b);
                    let hasRun3 = false;
                    for (let i = 2; i < sorted.length; i++) {
                        if (sorted[i] === sorted[i-1] + 1 && sorted[i-1] === sorted[i-2] + 1) {
                            hasRun3 = true; break;
                        }
                    }
                    if (hasRun3 && attempts < maxAttempts * 0.8) {
                        // Remover temporariamente e tentar outro
                        weights[chosenIdx] = 0;
                        continue;
                    }
                }

                ticket.push(chosen);
                usedSet.add(chosen);
                // Remover do disponível
                const remIdx = available.indexOf(chosen);
                if (remIdx >= 0) { available.splice(remIdx, 1); weights.splice(remIdx, 1); }
            }

            if (ticket.length < draw) continue;
            ticket.sort((a, b) => a - b);

            const key = ticket.join(',');
            if (usedKeys.has(key)) continue;

            // Score de qualidade do jogo
            const gameScore = this.scoreGame(ticket, gameKey, history, calibScores);
            if (gameScore < 0.20 && attempts < maxAttempts * 0.75) continue;

            games.push(ticket);
            usedKeys.add(key);
            ticket.forEach(n => usedCount[n] = (usedCount[n] || 0) + 1);
        }

        console.log('[QCAL-V3] ✅ ' + cfg.name + ': ' + games.length + '/' + numGames + ' jogos calibrados (' + attempts + ' iterações)');
        return games;
    }
};
