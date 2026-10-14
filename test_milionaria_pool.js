const MotorMilionariaB2BEngine = require('./js/engines/motor_milionaria_engine.js');
const MotorFechamentoManual = require('./js/engines/motor_fechamento_manual.js');

// Mock GAMES global for MotorFechamentoManual
global.GAMES = {
    milionaria: {
        name: "+Milionária",
        range: [1, 50],
        draw: 6,
        minBet: 6,
        maxBet: 50,
        price: 6.00
    }
};

async function runTests() {
    console.log("==================================================================");
    console.log("  TESTES DE CONFORMIDADE: +MILIONÁRIA - POOL E FECHAMENTO MANUAL");
    console.log("==================================================================");

    let allPassed = true;

    // --- TESTE 1: MotorFechamentoManual com diferentes pools e fixos ---
    const manualTestCases = [
        { name: "Pool 6 (Mínimo)", pool: [3, 14, 22, 35, 41, 49], fixed: [], qty: 1 },
        { name: "Pool 10, 0 Fixos, 15 Jogos", pool: [5, 8, 12, 17, 23, 29, 34, 40, 45, 50], fixed: [], qty: 15 },
        { name: "Pool 12, 2 Fixos, 20 Jogos", pool: [2, 7, 11, 19, 24, 28, 33, 37, 42, 44, 48, 50], fixed: [7, 33], qty: 20 },
        { name: "Pool 25 (Metade do Volante), 3 Fixos, 50 Jogos", pool: Array.from({length: 25}, (_, i) => i * 2 + 1), fixed: [1, 15, 31], qty: 50 }
    ];

    console.log("\n--- PARTE 1: MotorFechamentoManual ---");
    for (const tc of manualTestCases) {
        const res = MotorFechamentoManual.generate('milionaria', tc.pool, tc.fixed, tc.qty, 6);
        const games = res.games || [];
        const poolSet = new Set(tc.pool);
        
        let invalidCount = 0;
        let missingFixedCount = 0;
        
        games.forEach(g => {
            g.forEach(n => {
                if (!poolSet.has(n)) invalidCount++;
            });
            tc.fixed.forEach(f => {
                if (!g.includes(f)) missingFixedCount++;
            });
        });

        const ok = games.length > 0 && invalidCount === 0 && missingFixedCount === 0;
        if (!ok) allPassed = false;
        console.log(`  [${ok ? 'PASS' : 'FAIL'}] ${tc.name}: ${games.length} jogos gerados. Fora do pool: ${invalidCount}. Fixos ausentes: ${missingFixedCount}.`);
    }

    // --- TESTE 2: MotorMilionariaB2BEngine com pool personalizado ---
    console.log("\n--- PARTE 2: MotorMilionariaB2BEngine (Motor Oficial da Milionária) ---");
    const engineTestCases = [
        { name: "Pool 6 (Mínimo)", pool: [4, 12, 19, 28, 37, 46], fixed: [], qty: 5 },
        { name: "Pool 10, 0 Fixos, 10 Jogos", pool: [1, 9, 14, 20, 27, 32, 38, 41, 47, 50], fixed: [], qty: 10 },
        { name: "Pool 14, 2 Fixos, 25 Jogos", pool: [3, 6, 10, 15, 21, 25, 30, 34, 39, 43, 45, 48, 49, 50], fixed: [10, 39], qty: 25 },
        { name: "Pool 20, 3 Fixos, 30 Jogos", pool: [2, 4, 6, 8, 10, 12, 14, 16, 18, 20, 22, 24, 26, 28, 30, 32, 34, 36, 38, 40], fixed: [4, 18, 30], qty: 30 }
    ];

    for (const tc of engineTestCases) {
        const res = await MotorMilionariaB2BEngine.gerarCarteira(tc.qty, {
            pool: tc.pool,
            fixedNumbers: tc.fixed,
            poolTamanho: tc.pool.length
        });
        
        const jogos = (res && res.jogos) || [];
        const poolSet = new Set(tc.pool);
        
        let invalidCount = 0;
        let missingFixedCount = 0;
        let invalidTrevos = 0;

        jogos.forEach(j => {
            const dezenas = j.dezenas || [];
            const trevos = j.trevos || [];

            dezenas.forEach(n => {
                if (!poolSet.has(n)) invalidCount++;
            });

            tc.fixed.forEach(f => {
                if (!dezenas.includes(f)) missingFixedCount++;
            });

            if (!Array.isArray(trevos) || trevos.length !== 2 || trevos[0] < 1 || trevos[0] > 6 || trevos[1] < 1 || trevos[1] > 6 || trevos[0] === trevos[1]) {
                invalidTrevos++;
            }
        });

        const ok = jogos.length > 0 && invalidCount === 0 && missingFixedCount === 0 && invalidTrevos === 0;
        if (!ok) allPassed = false;
        console.log(`  [${ok ? 'PASS' : 'FAIL'}] ${tc.name}: ${jogos.length} jogos gerados. Fora do pool: ${invalidCount}. Fixos ausentes: ${missingFixedCount}. Trevos inválidos: ${invalidTrevos}.`);
    }

    console.log("\n==================================================================");
    if (allPassed) {
        console.log("  >>> RESULTADO: 100% DOS TESTES PASSARAM COM SUCESSO! <<<");
    } else {
        console.log("  >>> RESULTADO: FALHA EM ALGUNS TESTES! <<<");
    }
    console.log("==================================================================");

    process.exit(allPassed ? 0 : 1);
}

runTests();
