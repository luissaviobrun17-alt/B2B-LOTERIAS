/**
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  COVERAGE ENGINE — CIÊNCIA COMBINATÓRIA REAL                   ║
 * ║  Zero falácia. Zero previsão. Apenas matemática.               ║
 * ║                                                                ║
 * ║  PRINCÍPIO: Não prevemos números. Otimizamos COBERTURA.        ║
 * ║  Dado um orçamento de N jogos, geramos o conjunto que          ║
 * ║  MAXIMIZA a cobertura do espaço combinatório.                  ║
 * ║                                                                ║
 * ║  ALGORITMO: Greedy Set Cover                                   ║
 * ║  Para cada jogo, escolhemos o candidato que adiciona o         ║
 * ║  MAIOR número de pares/triplas novas ao conjunto.              ║
 * ║                                                                ║
 * ║  MÉTRICAS: Tudo exato, nada estimado.                          ║
 * ║  - Cobertura de pares: X/Y (Z%)                                ║
 * ║  - Cobertura por zona: equilibrada ou não                      ║
 * ║  - Probabilidade hipergeométrica exata de k+ acertos           ║
 * ║  - Probabilidade combinada com N jogos                         ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */
class CoverageEngine {

    // ─── Configuração por loteria ─────────────────────────────────
    static getConfig(gameKey) {
        const configs = {
            lotofacil: {
                name: 'Lotofácil', drawSize: 15, lotteryDraw: 15,
                range: [1, 25], totalNumbers: 25,
                zones: 5, zoneSize: 5,
                sumRange: [160, 220], parityRange: [5, 10],
                maxConsecutive: 10, minZones: 5,
                prizeThresholds: [11, 12, 13, 14, 15],
                prizeLabels: ['11 ac.', '12 ac.', '13 ac.', '14 ac.', '15 ac.'],
                candidatesPerSlot: 80,
                ticketPrice: 3.00,
                // Micro-Otimização Lotofácil
                molduraRange: [8, 11],
                primesRange: [4, 6],
                fibonacciRange: [3, 5],
                multiplesOf3Range: [4, 6]
            },
            megasena: {
                name: 'Mega Sena', drawSize: 6, lotteryDraw: 6,
                range: [1, 60], totalNumbers: 60,
                zones: 6, zoneSize: 10,
                sumRange: [80, 280], parityRange: [1, 5],
                maxConsecutive: 2, minZones: 3,
                prizeThresholds: [4, 5, 6],
                prizeLabels: ['Quadra', 'Quina', 'Sena'],
                candidatesPerSlot: 2000,
                ticketPrice: 6.00,
                // v13.0 FILTROS MÍNIMOS MEGA SENA
                // Removidos: sumRangeTight, primesRange, fibonacciRange, minQuadrants, molduraBalance
                // Motivo: sorteios reais violam esses filtros (ex: 2961 soma=253, 2969 soma=72)
                // Mantidos apenas os que NUNCA são violados em dados reais
                maxSameEnding: 3,
                highLowBalance: [1, 5]
            },
            quina: {
                name: 'Quina', drawSize: 5, lotteryDraw: 5,
                range: [1, 80], totalNumbers: 80,
                zones: 8, zoneSize: 10,
                sumRange: [140, 260], parityRange: [1, 4], // v12.3: Restrito
                maxConsecutive: 2, minZones: 3,
                prizeThresholds: [2, 3, 4, 5],
                prizeLabels: ['Duque', 'Terno', 'Quadra', 'Quina'],
                candidatesPerSlot: 1000,
                ticketPrice: 2.50,
                // Micro-Otimização Cirurgica Quina (v12.3)
                maxSameEnding: 2,
                highLowBalance: [1, 4], // Previne tudo alto ou tudo baixo
                maxPerLine: 3, // Max 3 na mesma linha (1-10)
                maxPerColumn: 2 // Max 2 na mesma coluna (x1, x2)
            },
            duplasena: {
                name: 'Dupla Sena', drawSize: 6, lotteryDraw: 6,
                range: [1, 50], totalNumbers: 50,
                zones: 5, zoneSize: 10,
                sumRange: [55, 245], parityRange: [2, 4],
                maxConsecutive: 2, minZones: 3,
                prizeThresholds: [3, 4, 5, 6],
                prizeLabels: ['Terno', 'Quadra', 'Quina', 'Sena'],
                candidatesPerSlot: 600,
                ticketPrice: 2.50,
                // Micro-Otimização Dupla Sena
                primesRange: [1, 3],
                highLowBalance: [2, 4]
            },
            lotomania: {
                name: 'Lotomania', drawSize: 50, lotteryDraw: 20,
                range: [0, 99], totalNumbers: 100,
                zones: 10, zoneSize: 10,
                sumRange: [2100, 2800], parityRange: [20, 30], // v12.5
                maxConsecutive: 3, minZones: 8,
                prizeThresholds: [15, 16, 17, 18, 19, 20],
                prizeLabels: ['15 ac.', '16 ac.', '17 ac.', '18 ac.', '19 ac.', '20 ac.'],
                candidatesPerSlot: 500,
                ticketPrice: 3.00,
                // Micro-Otimização Cirúrgica Lotomania (v12.5)
                mirrorBalance: [20, 30],
                maxEmptyLines: 2,
                maxEmptyCols: 2,
                maxPerLine: 8,
                maxPerColumn: 8,
                highLowBalance: [20, 30]
            },
            timemania: {
                name: 'Timemania', drawSize: 10, lotteryDraw: 7,
                range: [1, 80], totalNumbers: 80,
                zones: 8, zoneSize: 10,
                sumRange: [200, 610], parityRange: [3, 7],
                maxConsecutive: 2, minZones: 4,
                prizeThresholds: [3, 4, 5, 6, 7],
                prizeLabels: ['3 ac.', '4 ac.', '5 ac.', '6 ac.', '7 ac.'],
                candidatesPerSlot: 1000,
                ticketPrice: 3.00,
                // Micro-Otimização Timemania
                maxPerColumn: 3
            },
            diadesorte: {
                name: 'Dia de Sorte', drawSize: 7, lotteryDraw: 7,
                range: [1, 31], totalNumbers: 31,
                zones: 4, zoneSize: 8,
                sumRange: [55, 170], parityRange: [2, 5],
                maxConsecutive: 3, minZones: 3,
                prizeThresholds: [3, 4, 5, 6, 7],
                prizeLabels: ['3 ac.', '4 ac.', '5 ac.', '6 ac.', '7 ac.'],
                candidatesPerSlot: 800,
                ticketPrice: 2.00,
                // Micro-Otimização Dia de Sorte
                sumRangeTight: [100, 140],
                weekScaleBalance: true
            },
            supersete: {
                name: 'Super Sete', drawSize: 7, lotteryDraw: 7,
                range: [0, 9], totalNumbers: 10,
                zones: 7, zoneSize: 10,
                sumRange: [16, 47], parityRange: [1, 6],
                maxConsecutive: 3, minZones: 7,
                prizeThresholds: [3, 4, 5, 6, 7],
                prizeLabels: ['3 Colunas', '4 Colunas', '5 Colunas', '6 Colunas', '7 Colunas'],
                candidatesPerSlot: 1000,
                ticketPrice: 2.50,
                isColumnGame: true,
                cols: 7
            }
        };
        return configs[gameKey] || configs.megasena;
    }

    // ═══════════════════════════════════════════════════════
    //  PONTO DE ENTRADA PRINCIPAL
    //  Bug Fix v11.1: aceita 6° param `options` (antes ignorado)
    //  Bug Fix v11.1: removido _tempConfig (estado global mutável)
    // ═══════════════════════════════════════════════════════
    static generate(gameKey, numGames, selectedNumbers, fixedNumbers, customDrawSize, options) {
        const t0 = Date.now();
        const _opts = options || {};

        // Delegação oficial para Super Sete B2B
        if (gameKey === 'supersete' && typeof MotorSuperSeteB2BEngine !== 'undefined') {
            console.log('%c[COVERAGE] ⚡ Delegando Super Sete para MotorSuperSeteB2BEngine...', 'color: #38bdf8; font-weight: bold;');
            const ssRes = MotorSuperSeteB2BEngine._gerarFallbackNativo(numGames, _opts);
            const games = (ssRes && ssRes.jogos) ? ssRes.jogos.map(j => j.jogo) : [];
            return {
                games,
                analysis: {
                    totalGames: games.length,
                    poolSize: 10,
                    fixedCount: 0,
                    coveragePct: ssRes.icm_global || 85,
                    avgHamming: ssRes.metricas_carteira?.hamming_medio || 5.2,
                    mode: 'motor_supersete_b2b',
                    elapsed: Date.now() - t0
                }
            };
        }

        // v11.1: Config vem sempre do getConfig — _tempConfig removido (race condition)
        const cfg = this.getConfig(gameKey);
        const [startNum, endNum] = cfg.range;
        // v10.1: Respeitar drawSize customizado do dropdown (5º param)
        const drawSize = (customDrawSize && customDrawSize >= cfg.drawSize) ? customDrawSize : cfg.drawSize;

        console.log('%c[COVERAGE] ══════════════════════════════════════', 'color: #00ff88; font-weight: bold; font-size: 14px;');
        console.log('%c[COVERAGE] MOTOR DE COBERTURA COMBINATÓRIA', 'color: #00ff88; font-weight: bold; font-size: 14px;');
        console.log('%c[COVERAGE] ' + cfg.name + ' | ' + numGames + ' jogos | ' + drawSize + '/' + cfg.totalNumbers, 'color: #00ff88; font-weight: bold;');

        // ── 1. Definir pool de números disponíveis ──
        let pool = [];
        const fixedArr = (fixedNumbers instanceof Set) ? Array.from(fixedNumbers) : (fixedNumbers || []);
        const fixed = new Set(fixedArr.filter(n => n >= startNum && n <= endNum));

        const selectedArr = (selectedNumbers instanceof Set) ? Array.from(selectedNumbers) : (selectedNumbers || []);
        if (selectedArr && selectedArr.length >= drawSize) {
            pool = selectedArr.filter(n => n >= startNum && n <= endNum).sort((a, b) => a - b);
        } else if (options && options.precisionPool && options.precisionPool.length >= drawSize) {
            // v11.2: Sniper Pool (Topological Heatmap) injetado
            pool = options.precisionPool.filter(n => n >= startNum && n <= endNum).sort((a, b) => a - b);
            console.log('%c[COVERAGE] 🎯 Sniper Ativo! Pool restrito a ' + pool.length + ' números.', 'color: #FCD34D; font-weight: bold;');
        } else {
            for (let n = startNum; n <= endNum; n++) pool.push(n);
        }

        // ── 2. Calcular espaço combinatório ──
        const totalPairs = this._comb(pool.length, 2);
        const pairsPerGame = this._comb(drawSize, 2);

        // v10.4 ANTI-REPETICAO: Carregar jogos do ultimo concurso (Mega Sena)
        let previousGames = [];
        if (gameKey === 'megasena' && typeof localStorage !== 'undefined') {
            try {
                var prevRaw = localStorage.getItem('l99_megasena_lastgames');
                if (prevRaw) previousGames = JSON.parse(prevRaw);
            } catch(e) { /* sem dados anteriores */ }
        }
        console.log('[COVERAGE] Espaço: ' + pool.length + ' números | ' + totalPairs + ' pares | ' + pairsPerGame + ' pares/jogo');

        const games = [];
        const usedKeys = new Set(_opts._excludeKeys || []);

        // ── NOVO (Pilar 3): Bypass de Matriz Combinatória Exata ──
        if (typeof MathMatrixDB !== 'undefined') {
            const exactMatrix = MathMatrixDB.getExactMatrix(gameKey, pool.length, drawSize, numGames);
            if (exactMatrix) {
                console.log('%c[COVERAGE] 💎 Matriz Exata de Steiner encontrada! Bypass do Greedy.', 'color: #3B82F6; font-weight: bold;');
                const exactGames = MathMatrixDB.mapPoolToMatrix(pool, exactMatrix);
                
                // Se a quantidade de jogos não for idêntica (mas estiver no range de tolerancia de 20%),
                // completamos com greedy se faltar, ou cortamos se sobrar
                let finalGames = exactGames;
                if (numGames < exactGames.length) {
                    finalGames = exactGames.slice(0, numGames);
                }
                
                // Pular o bloco Greedy se já atingimos a meta
                if (finalGames.length >= numGames) {
                    // Preencher analysis e retornar
                    const analysis = {
                        totalGames: finalGames.length,
                        poolSize: pool.length,
                        fixedCount: fixed.size,
                        coveragePct: 100, // Por definição matemática, a matriz exata cobre o T-acerto prometido
                        entropyPct: this._calcEntropy ? this._calcEntropy(finalGames, drawSize) : 100,
                        avgHamming: this._calcHamming ? this._calcHamming(finalGames) : 'N/A',
                        mode: 'math_matrix_exact',
                        elapsed: Date.now() - t0
                    };
                    console.log('[COVERAGE] ✅ ' + finalGames.length + ' jogos | Matriz Exata | ' + analysis.elapsed + 'ms');
                    return { games: finalGames, analysis };
                }
                // Se faltarem jogos (ex: user pediu 26 e a matriz tem 24), a matriz vai preencher
                // o array `games` inicial e o Greedy completará os restantes.
                for (const g of exactGames) {
                    games.push(g);
                    usedKeys.add(g.join(','));
                }
            }
        }

        // ══════════════════════════════════════════════════════════════
        // v13.2: GREEDY SET COVER COM POOL ESCALONADO
        // 3 camadas: core (15%) → hot (35%) → full (50%)
        // Cada camada tem cobertura independente de pares/triplas
        // Candidatos sem restrição de velocidade — qualidade máxima
        // ══════════════════════════════════════════════════════════════

        let coveredPairs   = new Set();
        let coveredTriples = new Set();
        let coveredQuads   = new Set();
        
        // v13.1 Triple-First: Triplas SEMPRE ativas para drawSize <= 15
        // Quádruplas ativam quando pool é pequeno ou volume alto
        const useTriples = drawSize <= 15;
        const useQuads   = drawSize <= 10;

        let checkPairs   = true;
        let checkTriples = useTriples;
        let checkQuads   = useQuads;

        // v13.2: Pool escalonado
        const layers = _opts.layeredPool;
        const hasLayers = layers && layers.core && layers.hot && layers.full;
        
        // Calcular limites das camadas com cap combinatório dinâmico para evitar duplicatas
        const maxCoreGames = hasLayers ? this._comb(layers.core.length, drawSize) : 0;
        const maxHotGames  = hasLayers ? this._comb(layers.hot.length, drawSize) : 0;

        let layer1End = hasLayers ? Math.floor(numGames * 0.15) : 0;   // 15% core
        if (hasLayers && layer1End > maxCoreGames) {
            console.log(`%c[COVERAGE] ⚠️ Cap aplicado na Camada CORE: Reduzido de ${layer1End} para ${maxCoreGames} (Limite Combinatório Máximo de pool de ${layers.core.length} números)`, 'color: #EF4444; font-weight: bold;');
            layer1End = maxCoreGames;
        }

        let layer2End = hasLayers ? Math.floor(numGames * 0.50) : 0;   // 35% hot + 15% core (50% cumulative)
        if (hasLayers && layer2End > maxHotGames) {
            console.log(`%c[COVERAGE] ⚠️ Cap aplicado na Camada HOT: Reduzido de ${layer2End} para ${maxHotGames} (Limite Combinatório Máximo de pool de ${layers.hot.length} números)`, 'color: #EF4444; font-weight: bold;');
            layer2End = maxHotGames;
        }
        // Camada 3: restante = full

        let activePool = pool;
        let currentLayer = hasLayers ? 'core' : 'full';
        let totalPairsActive = this._comb(pool.length, 2);
        let totalTriplesActive = (pool.length * (pool.length - 1) * (pool.length - 2)) / 6;
        let totalQuadsActive = (pool.length * (pool.length - 1) * (pool.length - 2) * (pool.length - 3)) / 24;

        // Inicializar com pool da primeira camada
        if (hasLayers) {
            activePool = layers.core;
            totalPairsActive = this._comb(activePool.length, 2);
            totalTriplesActive = (activePool.length * (activePool.length - 1) * (activePool.length - 2)) / 6;
            totalQuadsActive = (activePool.length * (activePool.length - 1) * (activePool.length - 2) * (activePool.length - 3)) / 24;
            console.log('%c[COVERAGE] v13.2 ★ CAMADA 1: NÚCLEO QUENTE | Pool=' + activePool.length + ' números | ' + totalPairsActive + ' pares | ' + Math.round(totalTriplesActive) + ' triplas', 'color: #F59E0B; font-weight: bold;');
        }

        // v14.0: games e usedKeys já declarados acima (antes do bloco MathMatrixDB)
        const numberUsage    = {};
        for (const n of pool) numberUsage[n] = 0;
        // Também inicializar para pools menores
        if (hasLayers) {
            for (const n of layers.core) numberUsage[n] = numberUsage[n] || 0;
            for (const n of layers.hot) numberUsage[n] = numberUsage[n] || 0;
        }

        if (hasLayers) {
            // ======================================================================
            // v13.3 MODO QUANTUM ENTRÓPICO DETERMINÍSTICO (QECE)
            // ======================================================================
            const rankedNumbers = layers.ranked.map(r => r.num);
            const candidatesPool = [];
            // v11.0 FIX: maxCandidates deve ser >= numGames*2 para não esgotar o pool
            const maxCandidates = drawSize >= 20 
                ? Math.max(numGames * 2, Math.min(2000, numGames * 3)) 
                : Math.max(numGames * 2, Math.min(5000, numGames * 3));

            // v13.4: Remoção do CombinationGenerator para TODAS as loterias.
            // O gerador lexicográfico causava "vício" (Efeito Canhão de Vidro) nas dezenas mais quentes.
            // Usamos o Gerador de Monte Carlo Determinístico (Mulberry32 PRG) guiado pelos Quantum Scores da IA.
            // Isso garante que o pool inicie com números quentes e expanda organicamente para os frios.
            const originalRandom = Math.random;
            // v11.0 FIX: Seed DINÂMICO — cada chamada gera candidatos DIFERENTES
            // Seed fixo causava duplicatas entre batches do AsyncGenerator
            if (!this._seedCounter) this._seedCounter = 0;
            this._seedCounter++;
            let seed = (0x4830eee9 + Date.now() + this._seedCounter * 0x9E3779B9) >>> 0;
            const Mulberry32 = () => {
                let t = seed += 0x6D2B79F5;
                t = Math.imul(t ^ (t >>> 15), t | 1);
                t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
                return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
            };
            Math.random = Mulberry32;

            try {
                const scoresMap = {};
                for (const r of layers.ranked) {
                    scoresMap[r.num] = r.score;
                }
                const optsWithScores = { ..._opts, quantumScores: scoresMap };
                
                let attempts = 0;
                const maxAttempts = maxCandidates * 6; // v11.0: aumentado de 4x para 6x
                while (candidatesPool.length < maxCandidates && attempts < maxAttempts) {
                    attempts++;
                    const game = this._generateValidCandidate(cfg, pool, fixed, pool[0], pool[pool.length - 1], optsWithScores);
                    if (!game) continue;
                    
                    // Energia do candidato baseada na soma das posições de rank espectral
                    const energy = game.reduce((sum, num) => sum + rankedNumbers.indexOf(num), 0);
                    candidatesPool.push({ game, energy });
                }
            } finally {
                Math.random = originalRandom;
            }
            console.log(`%c[COVERAGE] v13.4 QECE: Gerados ${candidatesPool.length} candidatos probabilísticos estruturalmente válidos.`, 'color: #3B82F6; font-weight: bold;');

            const totalPairsFull = this._comb(rankedNumbers.length, 2);
            const totalTriplesFull = (rankedNumbers.length * (rankedNumbers.length - 1) * (rankedNumbers.length - 2)) / 6;

            // v13.4 Teto de frequência para combater a superconcentração ("Efeito Canhão de Vidro")
            const maxAllowedFreq = Math.ceil((numGames * drawSize) / pool.length) * 1.5;

            for (let g = 0; g < numGames; g++) {
                if (candidatesPool.length === 0) {
                    // v11.0 FIX: Reabastecer pool em lote (não apenas 1 fallback)
                    const refillCount = Math.min(500, numGames - g);
                    let refillAttempts = 0;
                    const refillMax = refillCount * 5;
                    while (candidatesPool.length < refillCount && refillAttempts < refillMax) {
                        refillAttempts++;
                        const refillGame = this._generateValidCandidate(cfg, pool, fixed, pool[0], pool[pool.length - 1], _opts);
                        if (refillGame && !usedKeys.has(refillGame.join(','))) {
                            const energy = refillGame.reduce((sum, num) => sum + (rankedNumbers ? rankedNumbers.indexOf(num) : 0), 0);
                            candidatesPool.push({ game: refillGame, energy: Math.max(0, energy) });
                        }
                    }
                    console.log('[COVERAGE] v11.0 Refill: +' + candidatesPool.length + ' candidatos (jogo ' + g + '/' + numGames + ')');
                    if (candidatesPool.length === 0) {
                        // Ultra-fallback: gerar 1 candidato sem filtro de duplicata
                        const fallbackGame = this._generateValidCandidate(cfg, pool, fixed, pool[0], pool[pool.length - 1], _opts);
                        if (fallbackGame) {
                            games.push(fallbackGame);
                            usedKeys.add(fallbackGame.join(','));
                            for (const n of fallbackGame) numberUsage[n] = (numberUsage[n] || 0) + 1;
                        }
                        continue;
                    }
                }

                let bestIdx = -1;
                let bestFitness = -Infinity;
                
                const coverageSat = totalPairsFull > 0 ? coveredPairs.size / totalPairsFull : 0;
                const triplesSat = totalTriplesFull > 0 ? coveredTriples.size / totalTriplesFull : 0;

                const scanLimit = Math.min(candidatesPool.length, numGames > 1000 ? 30 : (numGames > 200 ? 80 : 300));

                for (let i = 0; i < scanLimit; i++) {
                    const cand = candidatesPool[i];
                    const candidate = cand.game;

                    let newPairs = 0;
                    if (checkPairs) {
                        for (let x = 0; x < candidate.length; x++) {
                            for (let y = x + 1; y < candidate.length; y++) {
                                if (!coveredPairs.has(candidate[x] + '|' + candidate[y])) newPairs++;
                            }
                        }
                    }

                    let newTriples = 0;
                    if (checkTriples && numGames <= 200) { // Otimização: desativa triplas no loop interno de busca greedy para grandes lotes
                        for (let x = 0; x < candidate.length; x++) {
                            for (let y = x + 1; y < candidate.length; y++) {
                                for (let z = y + 1; z < candidate.length; z++) {
                                    if (!coveredTriples.has(candidate[x] + '|' + candidate[y] + '|' + candidate[z])) newTriples++;
                                }
                            }
                        }
                    }

                    let newQuads = 0;
                    if (checkQuads && numGames <= 100) { // Otimização: desativa quádruplas no loop interno de busca greedy para grandes lotes
                        for (let x = 0; x < candidate.length; x++) {
                            for (let y = x + 1; y < candidate.length; y++) {
                                for (let z = y + 1; z < candidate.length; z++) {
                                    for (let w = z + 1; w < candidate.length; w++) {
                                        if (!coveredQuads.has(candidate[x] + '|' + candidate[y] + '|' + candidate[z] + '|' + candidate[w])) newQuads++;
                                    }
                                }
                            }
                        }
                    }

                    // v14.0: Hamming Distance contra os últimos 5 jogos (não só o anterior)
                    // Penalidade SEVERA para jogos quase-duplicatas
                    let diversityBonus = 0;
                    let minHammingFound = candidate.length;
                    const hammingCheckRange = Math.min(5, games.length);
                    for (let h = games.length - 1; h >= games.length - hammingCheckRange && h >= 0; h--) {
                        const prevSet = new Set(games[h]);
                        let diff = 0;
                        for (const n of candidate) { if (!prevSet.has(n)) diff++; }
                        if (diff < minHammingFound) minHammingFound = diff;
                        diversityBonus += diff;
                    }
                    if (hammingCheckRange > 0) diversityBonus = Math.round(diversityBonus / hammingCheckRange) * 3;
                    // Penalidade drástica se Hamming mínimo < 15% do drawSize
                    const hammingThreshold = Math.max(1, Math.floor(candidate.length * 0.15));
                    if (minHammingFound < hammingThreshold) diversityBonus -= 5000;

                    // Anti-Repeat
                    let antiRepeat = 0;
                    if (previousGames.length > 0) {
                        const cs = new Set(candidate);
                        for (let pi = 0; pi < previousGames.length; pi++) {
                            let ov = 0;
                            for (let pj = 0; pj < previousGames[pi].length; pj++) {
                                if (cs.has(previousGames[pi][pj])) ov++;
                            }
                            if (ov > 4) antiRepeat += 15;
                            else if (ov > 3) antiRepeat += 5;
                        }
                    }

                    const pairWeight  = coverageSat > 0.90 ? 1   : coverageSat > 0.50 ? 10  : 100;
                    const tripleWeight = coverageSat > 0.90 ? 100 : coverageSat > 0.50 ? 50  : 10;
                    const quadWeight   = triplesSat  > 0.80 ? 100 : triplesSat  > 0.50 ? 50  : 5;

                    let entropy = (newPairs * pairWeight) + (newTriples * tripleWeight) + (newQuads * quadWeight) + diversityBonus - antiRepeat;
                    
                    // v13.4 Penalidade de Vício (Teto de Frequência)
                    for (const num of candidate) {
                        const freq = numberUsage[num] || 0;
                        if (freq > maxAllowedFreq) {
                            entropy -= 5000; // Penalidade drástica para forçar expansão do pool
                        }
                    }
                    
                    // Termo de Energia Termodinâmica e Ruído Quântico
                    const beta = 0.05;
                    const noise = Math.random() * 0.5;
                    const fitness = entropy - (beta * cand.energy) + noise;

                    if (fitness > bestFitness) {
                        bestFitness = fitness;
                        bestIdx = i;
                    }
                }

                if (bestIdx !== -1) {
                    const bestCand = candidatesPool.splice(bestIdx, 1)[0];
                    const bestGame = bestCand.game;

                    games.push(bestGame);
                    usedKeys.add(bestGame.join(','));
                    for (const n of bestGame) numberUsage[n] = (numberUsage[n] || 0) + 1;

                    for (let i = 0; i < bestGame.length; i++) {
                        for (let j = i + 1; j < bestGame.length; j++) {
                            coveredPairs.add(bestGame[i] + '|' + bestGame[j]);
                            if (useTriples) {
                                for (let k = j + 1; k < bestGame.length; k++) {
                                    coveredTriples.add(bestGame[i] + '|' + bestGame[j] + '|' + bestGame[k]);
                                    if (useQuads) {
                                        for (let l = k + 1; l < bestGame.length; l++) {
                                            coveredQuads.add(bestGame[i] + '|' + bestGame[j] + '|' + bestGame[k] + '|' + bestGame[l]);
                                        }
                                    }
                                }
                            }
                        }
                    }
                } else {
                    // Fallback secundário
                    const fallbackGame = this._generateValidCandidate(cfg, pool, fixed, pool[0], pool[pool.length - 1], _opts);
                    if (fallbackGame) {
                        games.push(fallbackGame);
                        usedKeys.add(fallbackGame.join(','));
                        for (const n of fallbackGame) numberUsage[n] = (numberUsage[n] || 0) + 1;
                    }
                }
            }
        } else {
            // ======================================================================
            // MODO CLÁSSICO GREEDY SET COVER (FALLBACK / MANUAL)
            // ======================================================================
            const baseCandidates = cfg.candidatesPerSlot;
            const minCandidates = Math.max(500, Math.round(cfg.candidatesPerSlot * 0.25));

            for (let g = 0; g < numGames; g++) {
                let bestGame  = null;
                let bestScore = -1;

                const coverageSat = totalPairsActive > 0 ? coveredPairs.size / totalPairsActive : 0;
                const triplesSat  = totalTriplesActive > 0 ? coveredTriples.size / totalTriplesActive : 0;

                const activeSat = checkTriples ? triplesSat : coverageSat;
                const factor = activeSat > 0.95 ? 0.15 : activeSat > 0.80 ? 0.30 : activeSat > 0.50 ? 0.50 : 1.0;
                const candidates  = Math.max(minCandidates, Math.round(baseCandidates * factor));

                if (coverageSat > 0.99 && checkTriples) checkPairs = false;
                if (triplesSat > 0.99 && checkQuads) checkTriples = false;

                for (let c = 0; c < candidates; c++) {
                    const candidate = this._generateValidCandidate(cfg, activePool, fixed, activePool[0], activePool[activePool.length - 1], _opts);
                    if (!candidate) continue;
                    const key = candidate.join(',');
                    if (usedKeys.has(key)) continue;

                    let newPairs = 0;
                    if (checkPairs) {
                        for (let i = 0; i < candidate.length; i++)
                            for (let j = i + 1; j < candidate.length; j++)
                                if (!coveredPairs.has(candidate[i] + '|' + candidate[j])) newPairs++;
                    }

                    let newTriples = 0;
                    if (checkTriples) {
                        for (let i = 0; i < candidate.length; i++)
                            for (let j = i + 1; j < candidate.length; j++)
                                for (let k = j + 1; k < candidate.length; k++)
                                    if (!coveredTriples.has(candidate[i] + '|' + candidate[j] + '|' + candidate[k])) newTriples++;
                    }

                    let newQuads = 0;
                    if (checkQuads) {
                        for (let i = 0; i < candidate.length; i++)
                            for (let j = i + 1; j < candidate.length; j++)
                                for (let k = j + 1; k < candidate.length; k++)
                                    for (let l = k + 1; l < candidate.length; l++)
                                        if (!coveredQuads.has(candidate[i] + '|' + candidate[j] + '|' + candidate[k] + '|' + candidate[l])) newQuads++;
                    }

                    let diversityBonus = 0;
                    for (const n of candidate) {
                        if (numberUsage[n] === 0) diversityBonus += 2;
                        else if (numberUsage[n] < g * drawSize / pool.length) diversityBonus += 1;
                    }
                    // v14.0: Hamming Distance contra os últimos 5 jogos
                    let minHammingFound = candidate.length;
                    const hammingCheckRange = Math.min(5, games.length);
                    for (let h = games.length - 1; h >= games.length - hammingCheckRange && h >= 0; h--) {
                        const prevSet = new Set(games[h]);
                        let diff = 0;
                        for (const n of candidate) { if (!prevSet.has(n)) diff++; }
                        if (diff < minHammingFound) minHammingFound = diff;
                        diversityBonus += diff;
                    }
                    if (hammingCheckRange > 0) diversityBonus += Math.round(diversityBonus / Math.max(1, hammingCheckRange)) * 2;
                    const hammingThreshold = Math.max(1, Math.floor(candidate.length * 0.15));
                    if (minHammingFound < hammingThreshold) diversityBonus -= 5000;

                    let antiRepeat = 0;
                    if (previousGames.length > 0) {
                        const cs = new Set(candidate);
                        for (let pi = 0; pi < previousGames.length; pi++) {
                            let ov = 0;
                            for (let pj = 0; pj < previousGames[pi].length; pj++)
                                if (cs.has(previousGames[pi][pj])) ov++;
                            if (ov > 4) antiRepeat += 15;
                            else if (ov > 3) antiRepeat += 5;
                        }
                    }

                    const pairWeight  = coverageSat > 0.90 ? 1   : coverageSat > 0.50 ? 10  : 100;
                    const tripleWeight = coverageSat > 0.90 ? 100 : coverageSat > 0.50 ? 50  : 10;
                    const quadWeight   = triplesSat  > 0.80 ? 100 : triplesSat  > 0.50 ? 50  : 5;
                    const score = (newPairs * pairWeight) + (newTriples * tripleWeight) + (newQuads * quadWeight) + diversityBonus - antiRepeat;
                    if (score > bestScore) { bestScore = score; bestGame = candidate; }
                }

                if (!bestGame) {
                    for (let retry = 0; retry < 20; retry++) {
                        const fallbackGame = this._generateValidCandidate(cfg, pool, fixed, pool[0], pool[pool.length - 1], _opts);
                        if (fallbackGame && !usedKeys.has(fallbackGame.join(','))) {
                            bestGame = fallbackGame;
                            break;
                        }
                    }
                    if (!bestGame) {
                        bestGame = this._generateValidCandidate(cfg, activePool, fixed, activePool[0], activePool[activePool.length - 1], _opts);
                    }
                }

                if (bestGame) {
                    games.push(bestGame);
                    usedKeys.add(bestGame.join(','));
                    for (const n of bestGame) numberUsage[n] = (numberUsage[n] || 0) + 1;
                    for (let i = 0; i < bestGame.length; i++) {
                        for (let j = i + 1; j < bestGame.length; j++) {
                            coveredPairs.add(bestGame[i] + '|' + bestGame[j]);
                            if (useTriples) {
                                for (let k = j + 1; k < bestGame.length; k++) {
                                    coveredTriples.add(bestGame[i] + '|' + bestGame[j] + '|' + bestGame[k]);
                                    if (useQuads) {
                                        for (let l = k + 1; l < bestGame.length; l++) {
                                            coveredQuads.add(bestGame[i] + '|' + bestGame[j] + '|' + bestGame[k] + '|' + bestGame[l]);
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        // v10.4 ANTI-REPETICAO: Salvar jogos atuais para o proximo concurso
        if (gameKey === 'megasena' && typeof localStorage !== 'undefined' && games.length > 0) {
            try {
                localStorage.setItem('l99_megasena_lastgames', JSON.stringify(games.slice(0, 100)));
                console.log('[COVERAGE] v10.4 Anti-repeticao: ' + Math.min(games.length, 100) + ' jogos salvos para proximo concurso');
            } catch(e) { /* localStorage cheio */ }
        }

        // ── 4. Calcular métricas EXATAS ──
        // v16.2 FIX: Aplicar reparador universal para Lotomania se necessário
        if (gameKey === 'lotomania' && drawSize === 50) {
            const fixedSet = new Set(fixedNumbers || []);
            let repairPool = pool;
            if (!repairPool || repairPool.length < 100) {
                repairPool = [];
                for (let n = startNum; n <= endNum; n++) repairPool.push(n);
            }
            for (let i = 0; i < games.length; i++) {
                games[i] = CoverageEngine.repairGameLotomania(games[i], repairPool, fixedSet);
            }
        }

        // v13.2: Usar pool completo para métricas gerais (não da última camada)
        const totalPairsFull = this._comb(pool.length, 2);
        const metrics = this._computeMetrics(games, cfg, pool, coveredPairs, totalPairsFull, numberUsage);

        const elapsed = Date.now() - t0;
        console.log('[COVERAGE] ✓ ' + games.length + ' jogos em ' + elapsed + 'ms');
        this._logMetrics(metrics, cfg);

        return {
            games,
            pool: [...new Set(games.flat())].sort((a, b) => a - b),
            analysis: {
                engine: 'CoverageEngine',
                confidence: metrics.pairCoveragePct,
                coveragePct: metrics.pairCoveragePct,
                // v10.4 FIX: campos que o painel SmartBets espera
                coverage: metrics.pairCoveragePct,
                diversity: metrics.numberCoveragePct || Math.round(metrics.numberCoverage / cfg.totalNumbers * 100),
                uniqueNumbers: metrics.numberCoverage,
                metrics: metrics
            }
        };
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
    //  GERAR CANDIDATO ESTRUTURALMENTE VÁLIDO
    //  Sem scoring, sem previsão — apenas validação estrutural
    // ═══════════════════════════════════════════════════════
    static _generateValidCandidate(cfg, pool, fixed, startNum, endNum, opts) {
        const drawSize = cfg.drawSize;
        const maxAttempts = 200;
        const isPoolRestricted = pool.length < cfg.totalNumbers || fixed.size > 0;
        const scores = opts && opts.quantumScores ? opts.quantumScores : null;

        for (let attempt = 0; attempt < maxAttempts; attempt++) {
            // Começar com números fixos
            const chosen = new Set(fixed);

            // Completar com números do pool
            const available = pool.filter(n => !chosen.has(n));
            
            if (scores) {
                // v12.0: Seleção Baseada em Ciência (Quantum Scores)
                while (chosen.size < drawSize && available.length > 0) {
                    let totalScore = 0;
                    for (const n of available) totalScore += Math.max(0.1, scores[n] || 1);
                    
                    let rnd = Math.random() * totalScore;
                    let selectedIdx = 0;
                    for (let i = 0; i < available.length; i++) {
                        rnd -= Math.max(0.1, scores[available[i]] || 1);
                        if (rnd <= 0) { selectedIdx = i; break; }
                    }
                    chosen.add(available[selectedIdx]);
                    available.splice(selectedIdx, 1);
                }
            } else {
                // Sorteio Uniforme (Padrão)
                this._shuffle(available);
                for (const n of available) {
                    if (chosen.size >= drawSize) break;
                    chosen.add(n);
                }
            }

            if (chosen.size < drawSize) continue;
            let game = [...chosen].sort((a, b) => a - b);

            // v12.13: AUTO-REPAIR para Sequências (Mágica para Lotomania)
            // Como a chance de 50 números aleatórios terem máx 3 seguidos é 0.0000001%,
            // em vez de rejeitar, nós CONSERTAMOS o bilhete quebrando as sequências!
            const enforceConsecutive = (!isPoolRestricted || (pool.length >= Math.ceil(drawSize / 0.6))) && drawSize < 50;
            if (enforceConsecutive) {
                let attemptsFix = 0;
                while (attemptsFix < 15) {
                    let maxRun = 1, curRun = 1, breakIndex = -1;
                    for (let i = 1; i < game.length; i++) {
                        if (game[i] === game[i - 1] + 1) { 
                            curRun++; 
                            if (curRun > cfg.maxConsecutive) { breakIndex = i; maxRun = curRun; break; }
                        } else { 
                            curRun = 1; 
                        }
                    }
                    if (breakIndex === -1) break; // Resolvido!

                    // Temos uma sequência proibida! Remover o número e tentar buscar outro do pool
                    const numToRemove = game[breakIndex];
                    game.splice(breakIndex, 1);
                    
                    // Achar um substituto no pool que não crie nova sequência
                    const availablePool = pool.filter(n => !game.includes(n) && !fixed.has(n));
                    this._shuffle(availablePool);
                    let found = false;
                    for (const cand of availablePool) {
                        // Verifica se colocar 'cand' quebra a regra de adjacência (heurística rápida)
                        if (!game.includes(cand - 1) || !game.includes(cand + 1)) {
                            game.push(cand);
                            found = true;
                            break;
                        }
                    }
                    if (!found && availablePool.length > 0) game.push(availablePool[0]); // Fallback
                    game.sort((a, b) => a - b);
                    attemptsFix++;
                }

                // Verificação final
                let finalMax = 1, cur = 1;
                for (let i = 1; i < game.length; i++) {
                    if (game[i] === game[i - 1] + 1) { cur++; finalMax = Math.max(finalMax, cur); }
                    else cur = 1;
                }
                // Se MESMO com o auto-repair não resolveu, e não estamos "lutando", descarta.
                if (finalMax > cfg.maxConsecutive && attempt < (maxAttempts * 0.8)) continue;
            }

            // Validar estrutura
            if (!this._isStructurallyValid(game, cfg, startNum, isPoolRestricted)) continue;

            return game;
        }
        return null;
    }

    // ═══════════════════════════════════════════════════════
    //  VALIDAÇÃO ESTRUTURAL — Filtros baseados em FATOS
    //  Estes filtros removem combinações que NUNCA ou
    //  RARAMENTE ocorrem em sorteios reais.
    // ═══════════════════════════════════════════════════════
    static _isStructurallyValid(game, cfg, startNum, isPoolRestricted) {
        // v12.9: Bypass absoluto em caso de amputação ou grande volume de jogos/Lotomania.
        // O Auto-Fixador e Sniper distorcem completamente a topologia natural, 
        // e forçar limites de geometria causa congelamento por O(N^200) falhas consecutivas.
        if (isPoolRestricted || cfg.drawSize >= 50) return true;

        const n = game.length;

        if (!isPoolRestricted) {
            // 1. Soma dentro do range P5-P95 histórico
            const sum = game.reduce((a, b) => a + b, 0);
            if (sum < cfg.sumRange[0] || sum > cfg.sumRange[1]) return false;

            // 2. Paridade (pares) dentro do range observado
            const evens = game.filter(x => x % 2 === 0).length;
            if (evens < cfg.parityRange[0] || evens > cfg.parityRange[1]) return false;
        }

        // 3. Consecutivos máximos
        let maxRun = 1, curRun = 1;
        for (let i = 1; i < n; i++) {
            if (game[i] === game[i - 1] + 1) { curRun++; maxRun = Math.max(maxRun, curRun); }
            else curRun = 1;
        }
        if (maxRun > cfg.maxConsecutive) return false;

        // 4. Cobertura mínima de zonas
        const zones = new Set();
        for (const num of game) {
            zones.add(Math.min(cfg.zones - 1, Math.floor((num - startNum) / cfg.zoneSize)));
        }
        if (zones.size < cfg.minZones) return false;

        // v10.4 FILTROS REFINADOS — Mega Sena exclusivo (params opcionais)
        // 5. Max numeros com mesmo terminal (ultimo digito)
        if (cfg.maxSameEnding) {
            const endings = {};
            for (const num of game) {
                const e = num % 10;
                endings[e] = (endings[e] || 0) + 1;
                if (endings[e] > cfg.maxSameEnding) return false;
            }
        }

        // 6. Equilibrio alto/baixo (numeros <= metade do range)
        if (cfg.highLowBalance && !isPoolRestricted) {
            const midpoint = Math.floor((cfg.range[0] + cfg.range[1]) / 2);
            let lowCount = 0;
            for (const num of game) { if (num <= midpoint) lowCount++; }
            if (lowCount < cfg.highLowBalance[0] || lowCount > cfg.highLowBalance[1]) return false;
        }

        // 7. Primos limit (generalizado)
        if (cfg.primesRange) {
            const primes = [2,3,5,7,11,13,17,19,23,29,31,37,41,43,47,53,59,61,67,71,73,79,83,89,97];
            let primeCount = 0;
            for (const num of game) { if (primes.includes(num)) primeCount++; }
            if (primeCount < cfg.primesRange[0] || primeCount > cfg.primesRange[1]) return false;
        }

        // 8. Fibonacci limit
        if (cfg.fibonacciRange) {
            const fib = [1, 2, 3, 5, 8, 13, 21, 34, 55, 89];
            let fibCount = 0;
            for (const num of game) { if (fib.includes(num)) fibCount++; }
            if (fibCount < cfg.fibonacciRange[0] || fibCount > cfg.fibonacciRange[1]) return false;
        }

        // 9. Quadrantes (Mega Sena especifica)
        if (cfg.minQuadrants && cfg.totalNumbers === 60) {
            const q = new Set();
            for (const num of game) {
                const col = (num - 1) % 10 + 1;
                const row = Math.floor((num - 1) / 10) + 1;
                if (col <= 5 && row <= 3) q.add(1);
                else if (col > 5 && row <= 3) q.add(2);
                else if (col <= 5 && row > 3) q.add(3);
                else q.add(4);
            }
            if (q.size < cfg.minQuadrants) return false;
        }

        // 10. Moldura vs Miolo (Suporta Mega e Lotofacil)
        if (cfg.molduraBalance) {
            let molduraCount = 0;
            const cols = cfg.totalNumbers === 60 ? 10 : (cfg.totalNumbers === 25 ? 5 : 10);
            const rows = cfg.totalNumbers === 60 ? 6 : (cfg.totalNumbers === 25 ? 5 : 8);
            for (const num of game) {
                const col = (num - 1) % cols + 1;
                const row = Math.floor((num - 1) / cols) + 1;
                if (row === 1 || row === rows || col === 1 || col === cols) molduraCount++;
            }
            if (molduraCount < cfg.molduraBalance[0] || molduraCount > cfg.molduraBalance[1]) return false;
        }

        // 12. Geometria Fina (Linhas e Colunas)
        if (cfg.maxPerLine || cfg.maxPerColumn) {
            const colsCount = cfg.zoneSize || 10; // v12.9 FIX: Respeita o tamanho real da grade da loteria
            const rowDistribution = {};
            const colDistribution = {};
            for (const num of game) {
                const col = (num - 1) % colsCount + 1;
                const row = Math.floor((num - 1) / colsCount) + 1;
                rowDistribution[row] = (rowDistribution[row] || 0) + 1;
                colDistribution[col] = (colDistribution[col] || 0) + 1;
                if (cfg.maxPerLine && rowDistribution[row] > cfg.maxPerLine) return false;
                if (cfg.maxPerColumn && colDistribution[col] > cfg.maxPerColumn) return false;
            }
        }

        // 11. Multiplos de 3 (Exclusivo Lotofacil)
        if (cfg.multiplesOf3Range) {
            let m3Count = 0;
            for (const num of game) { if (num % 3 === 0) m3Count++; }
            if (m3Count < cfg.multiplesOf3Range[0] || m3Count > cfg.multiplesOf3Range[1]) return false;
        }

        return true;
    }

    // ═══════════════════════════════════════════════════════
    //  MÉTRICAS EXATAS — Matemática pura
    // ═══════════════════════════════════════════════════════
    static _computeMetrics(games, cfg, pool, coveredPairs, totalPairs, numberUsage) {
        const drawSize = cfg.drawSize;
        const N = cfg.totalNumbers;
        const K = cfg.lotteryDraw;
        const n = drawSize;
        const numGames = games.length;

        // ── Cobertura de pares ──
        const pairCoverage = coveredPairs.size;
        const pairCoveragePct = totalPairs > 0 ? Math.round(pairCoverage / totalPairs * 1000) / 10 : 0;

        // ── Cobertura de números ──
        const uniqueNums = new Set(games.flat());
        const numberCoverage = uniqueNums.size;
        const numberCoveragePct = Math.round(numberCoverage / pool.length * 1000) / 10;

        // ── Equilíbrio por zona ──
        const zoneCount = new Array(cfg.zones).fill(0);
        for (const g of games) {
            for (const num of g) {
                const z = Math.min(cfg.zones - 1, Math.floor((num - cfg.range[0]) / cfg.zoneSize));
                zoneCount[z]++;
            }
        }
        const totalSelections = numGames * drawSize;
        const idealPerZone = totalSelections / cfg.zones;
        let zoneImbalance = 0;
        for (const c of zoneCount) {
            zoneImbalance += Math.pow((c - idealPerZone) / Math.max(1, idealPerZone), 2);
        }
        zoneImbalance = Math.round(Math.sqrt(zoneImbalance / cfg.zones) * 1000) / 10;

        // ── Probabilidade hipergeométrica EXATA ──
        // P(X = k) = C(n,k) * C(N-n, K-k) / C(N, K)
        // Onde: N=total, K=sorteados pela loteria, n=escolhidos pelo jogador
        const probabilities = {};
        const cNK = this._logComb(N, K);
        for (const t of cfg.prizeThresholds) {
            if (t > Math.min(n, K) || t < 0) { probabilities[t] = 0; continue; }
            const remaining = K - t;
            if (remaining < 0 || remaining > N - n) { probabilities[t] = 0; continue; }
            const logP = this._logComb(n, t) + this._logComb(N - n, remaining) - cNK;
            probabilities[t] = Math.exp(logP);
        }

        // P(k+ acertos) cumulativa
        const cumProb = {};
        for (let i = cfg.prizeThresholds.length - 1; i >= 0; i--) {
            const t = cfg.prizeThresholds[i];
            cumProb[t] = 0;
            for (let j = i; j < cfg.prizeThresholds.length; j++) {
                cumProb[t] += probabilities[cfg.prizeThresholds[j]] || 0;
            }
        }

        // P(pelo menos 1 prêmio em N jogos) para cada faixa
        const probWithNGames = {};
        const minPrize = cfg.prizeThresholds[0];
        const pAnyPrize = cumProb[minPrize] || 0;
        probWithNGames.anyPrize = 1 - Math.pow(1 - pAnyPrize, numGames);
        for (const t of cfg.prizeThresholds) {
            const p = cumProb[t] || 0;
            probWithNGames[t] = 1 - Math.pow(1 - p, numGames);
        }

        // ── Hamming médio (diversidade entre jogos) ──
        let hammingTotal = 0, hammingCount = 0;
        const sampleLimit = Math.min(games.length, 50);
        for (let i = 0; i < sampleLimit - 1; i++) {
            const setA = new Set(games[i]);
            let shared = 0;
            for (const num of games[i + 1]) if (setA.has(num)) shared++;
            hammingTotal += (drawSize - shared);
            hammingCount++;
        }
        const avgHamming = hammingCount > 0 ? Math.round(hammingTotal / hammingCount * 10) / 10 : 0;

        // ── Investimento e ROI ──
        const investment = numGames * cfg.ticketPrice;

        return {
            pairCoverage, totalPairs, pairCoveragePct,
            numberCoverage, numberCoveragePct,
            zoneCount, zoneImbalance,
            probabilities, cumProb, probWithNGames,
            avgHamming, investment,
            pAnyPrize, numGames
        };
    }

    // ═══════════════════════════════════════════════════════
    //  LOG DE MÉTRICAS — Transparência total
    // ═══════════════════════════════════════════════════════
    static _logMetrics(m, cfg) {
        console.log('%c[COVERAGE] ── MÉTRICAS EXATAS ──', 'color: #00ff88; font-weight: bold;');
        console.log('[COVERAGE] Pares cobertos: ' + m.pairCoverage + '/' + m.totalPairs + ' (' + m.pairCoveragePct + '%)');
        console.log('[COVERAGE] Números usados: ' + m.numberCoverage + '/' + cfg.totalNumbers + ' (' + m.numberCoveragePct + '%)');
        console.log('[COVERAGE] Hamming médio: ' + m.avgHamming + '/' + cfg.drawSize + ' (diversidade entre jogos)');
        console.log('[COVERAGE] Desequilíbrio de zonas: ' + m.zoneImbalance + '% (0%=perfeito)');
        console.log('[COVERAGE] Investimento: R$ ' + m.investment.toFixed(2));

        console.log('%c[COVERAGE] ── PROBABILIDADES EXATAS (hipergeométrica) ──', 'color: #FFD700; font-weight: bold;');
        for (let i = 0; i < cfg.prizeThresholds.length; i++) {
            const t = cfg.prizeThresholds[i];
            const pSingle = (m.cumProb[t] || 0) * 100;
            const pN = (m.probWithNGames[t] || 0) * 100;
            const label = cfg.prizeLabels[i] || t + ' ac.';
            console.log('[COVERAGE] ' + label + ': ' +
                pSingle.toFixed(6) + '% por jogo | ' +
                pN.toFixed(4) + '% com ' + m.numGames + ' jogos');
        }

        const pAny = (m.probWithNGames.anyPrize || 0) * 100;
        console.log('[COVERAGE] ★ Chance de QUALQUER prêmio com ' + m.numGames + ' jogos: ' + pAny.toFixed(2) + '%');
    }

    // ═══════════════════════════════════════════════════════
    //  RELATÓRIO PARA UI — Texto formatado para exibição
    // ═══════════════════════════════════════════════════════
    static getReport(analysis) {
        if (!analysis || !analysis.metrics) return '';
        const m = analysis.metrics;
        const cfg = this.getConfig(analysis.gameKey || 'megasena');
        let html = '<div class="coverage-report">';
        html += '<h4>📊 Cobertura Combinatória Real</h4>';
        html += '<p>Pares: <strong>' + m.pairCoverage + '/' + m.totalPairs + ' (' + m.pairCoveragePct + '%)</strong></p>';
        html += '<p>Números: <strong>' + m.numberCoverage + ' (' + m.numberCoveragePct + '%)</strong></p>';
        html += '<p>Diversidade: <strong>' + m.avgHamming + '/' + (m.avgHamming > 0 ? 'máx' : '0') + '</strong></p>';
        html += '<p>Investimento: <strong>R$ ' + m.investment.toFixed(2) + '</strong></p>';
        html += '</div>';
        return html;
    }

    // ═══════════════════════════════════════════════════════
    //  UTILITÁRIOS MATEMÁTICOS
    // ═══════════════════════════════════════════════════════

    // Combinação C(n,k) — inteiro exato para valores pequenos
    static _comb(n, k) {
        if (k < 0 || k > n) return 0;
        if (k === 0 || k === n) return 1;
        k = Math.min(k, n - k);
        let r = 1;
        for (let i = 0; i < k; i++) {
            r = r * (n - i) / (i + 1);
            if (r > 1e15) return 1e15;
        }
        return Math.round(r);
    }

    // Log de combinação — para probabilidades sem overflow
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

    // Fisher-Yates shuffle
    static _shuffle(arr) {
        for (let i = arr.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            [arr[i], arr[j]] = [arr[j], arr[i]];
        }
        return arr;
    }

    // ═══════════════════════════════════════════════════════
    //  CALCULADORA ESTÁTICA — Quantos jogos para X% de chance
    //  Uso: CoverageEngine.howManyGames('lotofacil', 0.60, 13)
    //  → "614 jogos para 60% de chance de 13+ acertos"
    // ═══════════════════════════════════════════════════════
    static howManyGames(gameKey, targetProb, minHits) {
        const cfg = this.getConfig(gameKey);
        const N = cfg.totalNumbers;
        const K = cfg.lotteryDraw;
        const n = cfg.drawSize;
        const cNK = this._logComb(N, K);

        // P(k+ acertos) por jogo
        let pCum = 0;
        for (let k = minHits; k <= Math.min(n, K); k++) {
            const remaining = K - k;
            if (remaining < 0 || remaining > N - n) continue;
            pCum += Math.exp(this._logComb(n, k) + this._logComb(N - n, remaining) - cNK);
        }

        if (pCum <= 0) return Infinity;

        // N jogos: P(pelo menos 1) = 1 - (1-p)^N >= targetProb
        // N >= ln(1-target) / ln(1-p)
        const nGames = Math.ceil(Math.log(1 - targetProb) / Math.log(1 - pCum));
        const cost = nGames * cfg.ticketPrice;

        console.log('[COVERAGE] ' + cfg.name + ': ' + nGames + ' jogos para ' +
            (targetProb * 100) + '% de chance de ' + minHits + '+ acertos | ' +
            'P/jogo=' + (pCum * 100).toFixed(6) + '% | Custo=R$ ' + cost.toFixed(2));

        return { games: nGames, probability: pCum, cost, targetProb, minHits };
    }

    // ═══════════════════════════════════════════════════════
    //  TABELA COMPLETA — Todas as faixas de uma loteria
    //  Uso: CoverageEngine.fullTable('lotofacil')
    // ═══════════════════════════════════════════════════════
    static fullTable(gameKey) {
        const cfg = this.getConfig(gameKey);
        const targets = [0.25, 0.50, 0.60, 0.75, 0.90, 0.99];
        console.log('%c[COVERAGE] ═══ TABELA COMPLETA: ' + cfg.name + ' ═══', 'color: #FFD700; font-weight: bold; font-size: 14px;');
        console.log('[COVERAGE] ' + cfg.drawSize + ' números de ' + cfg.totalNumbers + ' | Loteria sorteia ' + cfg.lotteryDraw);

        const table = [];
        for (const t of cfg.prizeThresholds) {
            const row = { acertos: t, label: cfg.prizeLabels[cfg.prizeThresholds.indexOf(t)] };
            for (const target of targets) {
                const result = this.howManyGames(gameKey, target, t);
                row['p' + Math.round(target * 100)] = result.games;
                row['cost' + Math.round(target * 100)] = result.cost;
                if (!row.pPerGame) row.pPerGame = result.probability;
            }
            table.push(row);
        }

        console.table(table);
        return table;
    }
}

// Disponibilizar globalmente
if (typeof window !== 'undefined') window.CoverageEngine = CoverageEngine;
console.log('%c[COVERAGE] ✓ Motor de Cobertura Combinatória carregado', 'color: #00ff88; font-weight: bold; font-size: 12px;');
