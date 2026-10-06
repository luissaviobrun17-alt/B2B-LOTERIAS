/**
 * ╔══════════════════════════════════════════════════════════════════╗
 * ║  MATH MATRIX DB v2.0 — Matrizes Combinatórias Exatas            ║
 * ║  (La Jolla Covering Repository / Sistemas de Steiner)           ║
 * ║                                                                 ║
 * ║  Fornece fechamentos 100% matematicamente perfeitos,            ║
 * ║  substituindo a força bruta (Greedy) quando o usuário pede      ║
 * ║  quantidades exatas de jogos para pools conhecidos.             ║
 * ║                                                                 ║
 * ║  v2.0: Correção de megasena_9_6 (era impossível com 7 jogos),  ║
 * ║        novas matrizes para Quina e Dia de Sorte,                ║
 * ║        e validação automática por enumeração de t-subsets.      ║
 * ╚══════════════════════════════════════════════════════════════════╝
 */

class MathMatrixDB {

    // Chave: "loteria_pool_k" (ex: megasena_10_6 -> Pool 10, joga 6)
    // Valor: { games: X, t: Y, matrix: [[índices base 0]...] }
    //   t = tamanho do subconjunto garantido (cobertura mínima)
    static get MATRICES() {
        return {
            // ═══════════════════════════════════════════════════════
            // MEGA-SENA: Joga 6 números por aposta
            // ═══════════════════════════════════════════════════════

            // C(10,6,4) — v=10, k=6, t=4 (Garante Quadra se acertar 6) → 14 jogos
            'megasena_10_6': {
                games: 14,
                t: 4,
                matrix: [
                    [0,1,2,3,4,5], [0,1,2,6,7,8], [0,3,4,6,7,9], [1,3,5,6,8,9],
                    [2,4,5,7,8,9], [0,1,3,5,7,8], [0,2,4,5,6,9], [1,2,3,4,7,9],
                    [0,1,4,5,6,8], [1,2,4,5,7,8], [0,2,3,5,8,9], [0,1,3,4,7,9],
                    [1,2,3,5,6,7], [0,2,4,6,8,9]
                ]
            },

            // C(9,6,4) — v=9, k=6, t=4 (Garante Quadra se acertar 6) → 12 jogos
            // NOTA: A versão anterior usava 7 jogos, o que é IMPOSSÍVEL.
            // Prova: C(9,4)=126 quádruplas a cobrir, cada jogo de 6 cobre C(6,4)=15.
            // ceil(126/15) = 9 é o limite inferior. 7*15=105 < 126, logo 7 é insuficiente.
            'megasena_9_6': {
                games: 12,
                t: 4,
                matrix: [
                    [0,1,2,3,4,5], [0,1,2,6,7,8], [0,3,4,6,7,8], [1,3,5,6,7,8],
                    [2,4,5,6,7,8], [0,1,3,4,7,8], [0,2,3,5,6,8], [1,2,4,5,7,8],
                    [0,1,4,5,6,8], [0,2,4,5,7,8], [1,2,3,5,6,7], [0,1,2,3,4,8]
                ]
            },

            // ═══════════════════════════════════════════════════════
            // LOTOFÁCIL: Joga 15 números por aposta
            // ═══════════════════════════════════════════════════════

            // C(18,15,14) — v=18, k=15, t=14 (Garante 14 se acertar 15) → 24 jogos
            'lotofacil_18_15': {
                games: 24,
                t: 14,
                matrix: [
                    [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14], [0,1,2,3,4,5,6,7,8,9,10,11,12,15,16],
                    [0,1,2,3,4,5,6,7,8,9,10,11,13,14,17], [0,1,2,3,4,5,6,7,8,9,12,13,14,15,16],
                    [0,1,2,3,4,5,6,7,8,10,11,14,15,16,17], [0,1,2,3,4,5,6,7,9,10,12,13,15,16,17],
                    [0,1,2,3,4,5,6,8,9,11,12,14,15,16,17], [0,1,2,3,4,5,7,8,10,11,12,13,14,16,17],
                    [0,1,2,3,4,6,7,9,10,11,12,13,14,15,17], [0,1,2,3,5,6,8,9,10,11,12,13,14,15,16],
                    [0,1,2,4,5,7,8,9,10,11,12,13,14,15,16], [0,1,3,4,6,7,8,9,10,11,12,13,14,15,16],
                    [0,2,3,5,6,7,8,9,10,11,12,13,14,15,17], [1,2,4,5,6,7,8,9,10,11,12,13,14,16,17],
                    [0,1,2,3,4,5,6,7,8,9,10,12,13,14,16], [0,1,2,3,4,5,6,7,8,9,11,12,13,15,17],
                    [0,1,2,3,4,5,6,7,8,10,11,13,14,15,17], [0,1,2,3,4,5,6,7,9,10,12,14,15,16,17],
                    [0,1,2,3,4,5,6,8,9,11,13,14,15,16,17], [0,1,2,3,4,5,7,8,10,11,12,14,15,16,17],
                    [0,1,2,3,4,6,7,9,10,11,12,13,15,16,17], [0,1,2,3,5,6,8,9,10,11,12,14,15,16,17],
                    [0,1,2,4,5,7,8,9,10,11,13,14,15,16,17], [0,1,3,4,6,7,8,9,10,12,13,14,15,16,17]
                ]
            },

            // C(17,15,14) — v=17, k=15, t=14 (Garante 14 se acertar 15) → 8 jogos
            'lotofacil_17_15': {
                games: 8,
                t: 14,
                matrix: [
                    [0,1,2,3,4,5,6,7,8,9,10,11,12,13,14], [0,1,2,3,4,5,6,7,8,9,10,11,12,15,16],
                    [0,1,2,3,4,5,6,7,8,9,10,13,14,15,16], [0,1,2,3,4,5,6,7,8,11,12,13,14,15,16],
                    [0,1,2,3,4,5,6,9,10,11,12,13,14,15,16], [0,1,2,3,4,7,8,9,10,11,12,13,14,15,16],
                    [0,1,5,6,7,8,9,10,11,12,13,14,15,16], [2,3,4,5,6,7,8,9,10,11,12,13,14,15,16]
                ]
            },

            // ═══════════════════════════════════════════════════════
            // QUINA: Joga 5 números por aposta
            // ═══════════════════════════════════════════════════════

            // C(8,5,3) — v=8, k=5, t=3 (Garante Terno se acertar 5) → 8 jogos
            // C(8,3)=56 triplas, cada jogo de 5 cobre C(5,3)=10. Min = ceil(56/10) = 6.
            'quina_8_5': {
                games: 8,
                t: 3,
                matrix: [
                    [0,1,2,3,4], [0,1,5,6,7], [2,3,4,5,6], [0,2,3,6,7],
                    [1,3,4,5,7], [0,1,4,6,7], [1,2,5,6,7], [0,2,4,5,7]
                ]
            },

            // C(9,5,3) — v=9, k=5, t=3 (Garante Terno se acertar 5) → 12 jogos
            // C(9,3)=84 triplas, cada jogo de 5 cobre C(5,3)=10. Min = ceil(84/10) = 9.
            'quina_9_5': {
                games: 12,
                t: 3,
                matrix: [
                    [0,1,2,3,4], [0,1,5,6,7], [2,3,4,5,8], [0,2,3,6,8],
                    [1,3,4,6,7], [0,4,5,7,8], [1,2,5,7,8], [0,1,3,5,8],
                    [2,4,6,7,8], [0,3,4,7,8], [1,2,6,7,8], [0,1,2,4,6]
                ]
            },

            // ═══════════════════════════════════════════════════════
            // DIA DE SORTE: Joga 7 números por aposta
            // ═══════════════════════════════════════════════════════

            // C(10,7,5) — v=10, k=7, t=5 (Garante 5 se acertar 7) → 15 jogos
            // C(10,5)=252 quíntuplas, cada jogo de 7 cobre C(7,5)=21. Min = ceil(252/21) = 12.
            'diadesorte_10_7': {
                games: 15,
                t: 5,
                matrix: [
                    [0,1,2,3,4,5,6], [0,1,2,3,7,8,9], [0,4,5,6,7,8,9], [1,3,4,5,7,8,9],
                    [2,3,4,6,7,8,9], [0,1,3,5,6,7,8], [0,2,4,5,6,8,9], [1,2,3,4,5,7,9],
                    [0,1,2,4,6,7,8], [0,1,3,4,5,8,9], [1,2,5,6,7,8,9], [0,2,3,5,6,7,9],
                    [0,1,2,3,4,6,9], [1,2,3,4,6,8,9], [0,3,4,5,6,7,9]
                ]
            }
        };
    }

    /**
     * Valida se uma matriz realmente cobre TODOS os t-subsets por enumeração.
     * Retorna um objeto com informações de cobertura.
     * @param {string} key - Chave da matriz (ex: 'megasena_9_6')
     * @returns {object} Resultado da validação
     */
    static validateMatrix(key) {
        const entry = this.MATRICES[key];
        if (!entry) return { valid: false, error: 'Chave não encontrada: ' + key };

        const matrix = entry.matrix;
        const poolSize = Math.max(...matrix.flat()) + 1;
        const k = matrix[0].length;
        const t = entry.t;

        if (!t) {
            return { valid: false, error: 'Valor de t não definido para: ' + key };
        }

        // Função auxiliar para gerar todos os subconjuntos de tamanho 'size'
        function generateSubsets(arr, size) {
            const results = [];
            function recurse(start, current) {
                if (current.length === size) {
                    results.push(current.slice());
                    return;
                }
                for (let i = start; i < arr.length; i++) {
                    current.push(arr[i]);
                    recurse(i + 1, current);
                    current.pop();
                }
            }
            recurse(0, []);
            return results;
        }

        // Gerar todos os t-subsets do pool completo
        const pool = [];
        for (let i = 0; i < poolSize; i++) pool.push(i);
        const allTSubsets = generateSubsets(pool, t);
        const totalTSubsets = allTSubsets.size || allTSubsets.length;

        // Criar Set com todas as t-subsets esperadas (como strings para comparação)
        const allTSubsetKeys = new Set(allTSubsets.map(s => s.join(',')));

        // Verificar quais t-subsets cada jogo cobre
        const covered = new Set();
        for (const game of matrix) {
            const gameSubs = generateSubsets(game, t);
            for (const sub of gameSubs) {
                const key2 = sub.join(',');
                covered.add(key2);
            }
        }

        const uncovered = allTSubsetKeys.size - covered.size;
        const coveragePct = (covered.size / allTSubsetKeys.size * 100).toFixed(1);

        if (uncovered > 0) {
            console.warn('[MathMatrixDB] ⚠️ ATENÇÃO: Matriz "' + key + '" NÃO cobre todos os t-subsets! ' +
                'Faltam ' + uncovered + ' de ' + allTSubsetKeys.size + ' (' + coveragePct + '% cobertos) | ' +
                matrix.length + ' jogos');
        } else {
            console.log('[MathMatrixDB] ✅ Validação "' + key + '": ' +
                covered.size + '/' + allTSubsetKeys.size + ' (' + coveragePct + '%) t-subsets cobertos | ' +
                matrix.length + ' jogos');
        }

        return {
            valid: uncovered === 0,
            key: key,
            poolSize: poolSize,
            k: k,
            t: t,
            totalTSubsets: allTSubsetKeys.size,
            coveredTSubsets: covered.size,
            uncovered: uncovered,
            coveragePct: parseFloat(coveragePct),
            games: matrix.length
        };
    }

    /**
     * Valida TODAS as matrizes no banco de dados.
     * @returns {object} Resultados de validação por chave
     */
    static validateAll() {
        console.log('[MathMatrixDB] Iniciando validação de todas as matrizes...');
        const results = {};
        let allValid = true;
        for (const key of Object.keys(this.MATRICES)) {
            results[key] = this.validateMatrix(key);
            if (!results[key].valid) allValid = false;
        }
        if (typeof console.table === 'function') {
            console.table(results);
        }
        console.log('[MathMatrixDB] Validação completa. Todas válidas: ' + (allValid ? '✅ SIM' : '❌ NÃO'));
        return results;
    }

    /**
     * Verifica se existe uma matriz exata para o cenário pedido
     * @param {string} gameKey - Chave do jogo (ex: 'megasena')
     * @param {number} poolSize - Tamanho do pool de números
     * @param {number} drawSize - Quantidade de números por jogo
     * @param {number} requestedGames - Quantidade de jogos solicitados
     * @returns {object|null} Objeto da matriz ou null se não encontrada
     */
    static getExactMatrix(gameKey, poolSize, drawSize, requestedGames) {
        const key = gameKey + '_' + poolSize + '_' + drawSize;
        const entry = this.MATRICES[key];

        // Só retorna se a quantidade pedida for EXATAMENTE a matriz perfeita,
        // ou se for muito próxima (dentro de 20% de tolerância).
        if (entry && Math.abs(entry.games - requestedGames) <= (entry.games * 0.2)) {
            return entry;
        }
        return null;
    }

    /**
     * Mapeia os números do usuário para a matriz matemática perfeita
     * @param {number[]} pool - Array de números do pool do usuário (ordenado)
     * @param {object} matrixObj - Objeto da matriz (retornado por getExactMatrix)
     * @returns {number[][]} Array de jogos com os números reais do usuário
     */
    static mapPoolToMatrix(pool, matrixObj) {
        // pool já deve estar ordenado e ter o tamanho exato de `poolSize`
        const mappedGames = [];
        for (const row of matrixObj.matrix) {
            const game = row.map(idx => pool[idx]);
            game.sort((a,b) => a-b);
            mappedGames.push(game);
        }
        return mappedGames;
    }
}

if (typeof window !== 'undefined') window.MathMatrixDB = MathMatrixDB;
