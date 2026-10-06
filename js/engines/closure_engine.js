/**
 * ClosureEngine — Motor de Fechamento Garantido (Covering Design)
 * v10.5 GOD MODE — Exclusivo Mega Sena
 *
 * Baseado em Covering Designs do La Jolla Covering Repository.
 * Garante matematicamente que, se T dos N números selecionados forem
 * sorteados, pelo menos 1 jogo terá T acertos.
 *
 * DIFERENÇA DO CoverageEngine:
 * - CoverageEngine: "tenta cobrir o máximo" (heurístico, sem garantia)
 * - ClosureEngine: "GARANTE cobertura" (matemático, prova combinatória)
 */
class ClosureEngine {

    // ═══════════════════════════════════════════════════════
    //  TABELAS DE COVERING DESIGN — La Jolla Repository
    //  C(v, k=6, t) = número mínimo de jogos de 6 números
    //  necessários para cobrir TODOS os t-subsets de v números
    // ═══════════════════════════════════════════════════════

    static get COVERING_TABLES() {
        return {
            // C(v, 6, 4) — Garantia de QUADRA
            quadra: {
                6: 1,     // C(6,6,4) = trivial, 1 jogo
                7: 4,     // C(7,6,4)
                8: 8,     // C(8,6,4)
                9: 14,    // C(9,6,4)
                10: 20,   // C(10,6,4) = 20 jogos
                11: 30,   // C(11,6,4)
                12: 42,   // C(12,6,4) = 42 jogos
                13: 62,   // C(13,6,4)
                14: 88,   // C(14,6,4)
                15: 118,  // C(15,6,4) = 118 jogos
                16: 154,  // C(16,6,4)
                17: 198,  // C(17,6,4)
                18: 258,  // C(18,6,4) = 258 jogos
                19: 323,  // C(19,6,4)
                20: 400   // C(20,6,4) = 400 jogos
            },
            // C(v, 6, 5) — Garantia de QUINA
            quina: {
                6: 1,     // C(6,6,5) = trivial
                7: 3,     // C(7,6,5)
                8: 6,     // C(8,6,5)
                9: 8,     // C(9,6,5)
                10: 10,   // C(10,6,5)
                11: 15,   // C(11,6,5)
                12: 22,   // C(12,6,5) = 22 jogos
                13: 30,   // C(13,6,5)
                14: 37,   // C(14,6,5)
                15: 45    // C(15,6,5) = 45 jogos
            }
        };
    }

    // ═══════════════════════════════════════════════════════
    //  PONTO DE ENTRADA PRINCIPAL
    //  v11.1 Fix: assinatura compatível com SmartCoverageEngine:
    //    generate(gameKey, numGames, selectedNumbers, fixedNumbers, drawSize, guaranteeLevel)
    //  v11.1 Fix: k dinâmico por loteria (remov. hardcode k=6 Mega Sena)
    // ═══════════════════════════════════════════════════════

    static generate(gameKey, numGames, selectedNumbers, fixedNumbers, drawSize, guaranteeLevel) {
        const t0 = Date.now();

        // v11.1: k dinâmico: usa drawSize passado pelo orquestrador (ou fallback 6)
        const k = (drawSize && drawSize > 0) ? drawSize : 6;

        // Normalizar garantia: suporta 'quadra', 'quina' e undefined
        const gl = guaranteeLevel || 'quadra';
        const t = gl === 'quina' ? 5 : 4;

        // Para garantia t=5 em jogos com k<6, ajustar t automaticamente
        const effectiveT = Math.min(t, k - 1);

        const nums = [...(selectedNumbers || [])].sort((a, b) => a - b);
        const v = nums.length;

        console.log('%c[CLOSURE] ════════════════════════════════════════════', 'color: #FFD700; font-weight: bold; font-size: 14px;');
        console.log('%c[CLOSURE] MOTOR DE FECHAMENTO GARANTIDO v11.1', 'color: #FFD700; font-weight: bold; font-size: 14px;');
        console.log('%c[CLOSURE] ' + (gameKey||'') + ' | k=' + k + ' | ' + v + ' números | Garantia: t=' + effectiveT, 'color: #FFD700; font-weight: bold;');

        if (v < k) {
            console.warn('[CLOSURE] Números insuficientes: ' + v + ' < ' + k + ' — fallback para CoverageEngine');
            return { games: [], analysis: { engine: 'ClosureEngine', error: 'Números insuficientes para fechamento' } };
        }

        if (v === k) {
            // Trivial: apenas 1 combinação
            return this._buildResult([nums], nums, v, effectiveT, gl, t0, null, k);
        }

        // Determinar número ideal de jogos
        // Para k=6 (Mega Sena) usa tabela exata; para outros usa estimação
        const table = k === 6 ? (this.COVERING_TABLES[gl] || this.COVERING_TABLES.quadra) : null;
        const targetGames = (table && table[v]) ? table[v] : this._estimateCoveringNumber(v, k, effectiveT);

        // Limitar target a numGames se fornecido pelo orquestrador
        const finalTarget = (numGames && numGames > 0) ? Math.min(targetGames, numGames * 2) : targetGames;

        console.log('[CLOSURE] Target: ' + finalTarget + ' jogos (C(' + v + ',' + k + ',' + effectiveT + '))');

        // Gerar jogos usando Greedy Covering
        const games = this._greedyCovering(nums, k, effectiveT, finalTarget);

        // Validar cobertura
        const validation = this._validateCovering(games, nums, effectiveT);

        console.log('[CLOSURE] Gerados: ' + games.length + ' jogos | Cobertura t-subsets: ' + validation.coveredPct + '%');

        return this._buildResult(games, nums, v, effectiveT, guaranteeLevel, t0, validation, k);
    }

    // ═══════════════════════════════════════════════════════
    //  GREEDY COVERING — Gerar jogos que cobrem todos t-subsets
    // ═══════════════════════════════════════════════════════

    static _greedyCovering(nums, k, t, targetGames) {
        // Gerar TODOS os t-subsets dos números selecionados
        const allTSubsets = this._generateSubsets(nums, t);
        const uncoveredSet = new Set();
        for (let i = 0; i < allTSubsets.length; i++) {
            uncoveredSet.add(allTSubsets[i].join(','));
        }

        console.log('[CLOSURE] Total t-subsets a cobrir: ' + allTSubsets.length);

        const games = [];
        const usedKeys = new Set();
        const maxGames = Math.max(targetGames * 5, 500000); // safety limit

        while (uncoveredSet.size > 0 && games.length < maxGames) {
            // Gerar candidatos e escolher o que cobre mais t-subsets não-cobertos
            let bestGame = null;
            let bestScore = -1;

            // Para conjuntos pequenos (v <= 15), avaliar TODAS as combinações
            // Para maiores, usar amostragem
            const allCombos = (nums.length <= 15)
                ? this._generateSubsets(nums, k)
                : null;

            const candidates = allCombos
                ? allCombos
                : this._generateRandomCandidates(nums, k, Math.min(50000, targetGames * 50));

            for (const candidate of candidates) {
                const key = candidate.join(',');
                if (usedKeys.has(key)) continue;

                // Contar t-subsets que este candidato cobre
                const tSubsetsOfCandidate = this._generateSubsets(candidate, t);
                let newlyCovered = 0;
                for (const sub of tSubsetsOfCandidate) {
                    if (uncoveredSet.has(sub.join(','))) newlyCovered++;
                }

                if (newlyCovered > bestScore) {
                    bestScore = newlyCovered;
                    bestGame = candidate;
                }
            }

            if (!bestGame || bestScore === 0) {
                // Fallback: pegar qualquer jogo que cubra pelo menos algo
                console.warn('[CLOSURE] Greedy stalled. Remaining uncovered: ' + uncoveredSet.size);
                break;
            }

            // Adicionar o melhor jogo
            games.push(bestGame);
            usedKeys.add(bestGame.join(','));

            // Remover t-subsets cobertos
            const coveredSubs = this._generateSubsets(bestGame, t);
            for (const sub of coveredSubs) {
                uncoveredSet.delete(sub.join(','));
            }
        }

        if (uncoveredSet.size > 0) {
            console.warn('[CLOSURE] Cobertura incompleta! Faltam ' + uncoveredSet.size + ' t-subsets');
        } else {
            console.log('%c[CLOSURE] ✓ COBERTURA 100% — Garantia matemática confirmada!', 'color: #22C55E; font-weight: bold; font-size: 14px;');
        }

        return games;
    }

    // ═══════════════════════════════════════════════════════
    //  GERAR TODOS OS SUBCONJUNTOS DE TAMANHO t
    // ═══════════════════════════════════════════════════════

    static _generateSubsets(arr, t) {
        const result = [];
        const n = arr.length;

        function backtrack(start, current) {
            if (current.length === t) {
                result.push([...current]);
                return;
            }
            for (let i = start; i < n; i++) {
                current.push(arr[i]);
                backtrack(i + 1, current);
                current.pop();
            }
        }

        backtrack(0, []);
        return result;
    }

    // ═══════════════════════════════════════════════════════
    //  GERAR CANDIDATOS ALEATÓRIOS (para v > 15)
    // ═══════════════════════════════════════════════════════

    static _generateRandomCandidates(nums, k, count) {
        const candidates = [];
        const seen = new Set();

        for (let i = 0; i < count; i++) {
            const shuffled = [...nums];
            // Fisher-Yates shuffle
            for (let j = shuffled.length - 1; j > 0; j--) {
                const r = Math.floor(Math.random() * (j + 1));
                [shuffled[j], shuffled[r]] = [shuffled[r], shuffled[j]];
            }
            const candidate = shuffled.slice(0, k).sort((a, b) => a - b);
            const key = candidate.join(',');
            if (!seen.has(key)) {
                seen.add(key);
                candidates.push(candidate);
            }
        }

        return candidates;
    }

    // ═══════════════════════════════════════════════════════
    //  VALIDAR COBERTURA — Confirmar que todos t-subsets estão cobertos
    // ═══════════════════════════════════════════════════════

    static _validateCovering(games, nums, t) {
        const allTSubsets = this._generateSubsets(nums, t);
        const coveredSet = new Set();

        for (const game of games) {
            const subs = this._generateSubsets(game, t);
            for (const sub of subs) {
                coveredSet.add(sub.join(','));
            }
        }

        const total = allTSubsets.length;
        const covered = coveredSet.size;
        const coveredPct = total > 0 ? Math.round(covered / total * 100 * 10) / 10 : 0;

        return {
            totalTSubsets: total,
            coveredTSubsets: covered,
            uncovered: total - covered,
            coveredPct: coveredPct,
            isComplete: covered >= total
        };
    }

    // ═══════════════════════════════════════════════════════
    //  ESTIMAR NÚMERO DE JOGOS (para v sem tabela exata)
    // ═══════════════════════════════════════════════════════

    static _estimateCoveringNumber(v, k, t) {
        // Schönheim bound: C(v,k,t) >= ceil(v/k * C(v-1,k-1,t-1))
        // Simplified estimate using ratio from known values
        const comb_v_t = this._comb(v, t);
        const comb_k_t = this._comb(k, t);
        return Math.ceil(comb_v_t / comb_k_t * 1.5); // 1.5x greedy overhead
    }

    static _comb(n, r) {
        if (r > n || r < 0) return 0;
        if (r === 0 || r === n) return 1;
        let result = 1;
        for (let i = 0; i < r; i++) {
            result = result * (n - i) / (i + 1);
        }
        return Math.round(result);
    }

    // ═══════════════════════════════════════════════════════
    //  CONSTRUIR RESULTADO
    // ═══════════════════════════════════════════════════════

    static _buildResult(games, nums, v, t, guaranteeLevel, t0, validation, k) {
        const elapsed = Date.now() - t0;
        const tLabel = t >= 5 ? 'QUINA' : 'QUADRA';
        const betK = k || 6;
        const investimento = games.length * (betK === 15 ? 3 : betK === 10 ? 3 : 5); // estimativa por tamanho

        return {
            games: games,
            pool: nums,
            analysis: {
                engine: 'ClosureEngine',
                confidence: validation ? validation.coveredPct : 100,
                coverage: validation ? validation.coveredPct : 100,
                coveragePct: validation ? validation.coveredPct : 100,
                diversity: Math.round(new Set(games.flat()).size / v * 100),
                uniqueNumbers: new Set(games.flat()).size,
                // Metadados do fechamento
                closure: {
                    guaranteeLevel: guaranteeLevel,
                    guaranteeLabel: tLabel,
                    t: t,
                    v: v,
                    totalTSubsets: validation ? validation.totalTSubsets : this._comb(v, t),
                    coveredTSubsets: validation ? validation.coveredTSubsets : this._comb(v, t),
                    isComplete: validation ? validation.isComplete : true,
                    coveredPct: validation ? validation.coveredPct : 100,
                    gamesNeeded: games.length,
                    investimento: investimento,
                    elapsed: elapsed
                }
            }
        };
    }

    // ═══════════════════════════════════════════════════════
    //  INFO — Retorna dados da tabela para a UI
    // ═══════════════════════════════════════════════════════

    static getClosureInfo(numSelected) {
        const quadraTable = this.COVERING_TABLES.quadra;
        const quinaTable = this.COVERING_TABLES.quina;

        return {
            numSelected: numSelected,
            quadra: {
                games: quadraTable[numSelected] || this._estimateCoveringNumber(numSelected, 6, 4),
                investimento: (quadraTable[numSelected] || this._estimateCoveringNumber(numSelected, 6, 4)) * 5,
                label: 'Se ' + Math.min(4, numSelected) + ' dos ' + numSelected + ' números forem sorteados → QUADRA GARANTIDA',
                available: true
            },
            quina: {
                games: quinaTable[numSelected] || null,
                investimento: quinaTable[numSelected] ? quinaTable[numSelected] * 5 : null,
                label: numSelected <= 15
                    ? 'Se 5 dos ' + numSelected + ' números forem sorteados → QUINA GARANTIDA'
                    : 'Indisponível para ' + numSelected + ' números (custo proibitivo)',
                available: numSelected <= 15 && quinaTable[numSelected] != null
            }
        };
    }
}

// Exportar globalmente
if (typeof window !== 'undefined') window.ClosureEngine = ClosureEngine;
if (typeof module !== 'undefined') module.exports = ClosureEngine;
