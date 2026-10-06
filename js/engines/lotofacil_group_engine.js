/**
 * ╔══════════════════════════════════════════════════════════════════════════╗
 * ║  LOTOFÁCIL GROUP ENGINE — LGE-V1                                         ║
 * ║  Análise por 5 Grupos de 5 Números + 5 Colunas (matriz 5×5)             ║
 * ╠══════════════════════════════════════════════════════════════════════════╣
 * ║  Metodologia:                                                             ║
 * ║  - G1:[1-5]  G2:[6-10]  G3:[11-15]  G4:[16-20]  G5:[21-25]            ║
 * ║  - C1:[1,6,11,16,21]  C2:[2,7,12,17,22] ... C5:[5,10,15,20,25]        ║
 * ║  - Cada sorteio gera um "perfil" [g1,g2,g3,g4,g5] somando 15           ║
 * ║  - Análise de frequência de perfis, rotação de grupos, correlações      ║
 * ╚══════════════════════════════════════════════════════════════════════════╝
 */
const LotofacilGroupEngine = {

    DRAW: 15,
    RANGE: 25,

    // ── 5 GRUPOS (linhas da matriz 5×5) ──────────────────────────────────
    GROUPS: [
        { id: 1, label: 'G1', nums: [1,2,3,4,5],      range: '01–05', color: '#EF4444', emoji: '🔴' },
        { id: 2, label: 'G2', nums: [6,7,8,9,10],     range: '06–10', color: '#F97316', emoji: '🟠' },
        { id: 3, label: 'G3', nums: [11,12,13,14,15], range: '11–15', color: '#EAB308', emoji: '🟡' },
        { id: 4, label: 'G4', nums: [16,17,18,19,20], range: '16–20', color: '#22C55E', emoji: '🟢' },
        { id: 5, label: 'G5', nums: [21,22,23,24,25], range: '21–25', color: '#6366f1', emoji: '🔵' }
    ],

    // ── 5 COLUNAS (colunas da matriz 5×5) ────────────────────────────────
    COLS: [
        { id: 'C1', label: 'C1', nums: [1,6,11,16,21] },
        { id: 'C2', label: 'C2', nums: [2,7,12,17,22] },
        { id: 'C3', label: 'C3', nums: [3,8,13,18,23] },
        { id: 'C4', label: 'C4', nums: [4,9,14,19,24] },
        { id: 'C5', label: 'C5', nums: [5,10,15,20,25] }
    ],

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // ANÁLISE COMPLETA DO HISTÓRICO
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    analyze(history) {
        const N = Math.min(200, (history || []).length);
        if (N < 5) return null;

        const getN = d => (d.numbers || []).filter(x => x >= 1 && x <= 25);

        // ── Parse cada sorteio para perfil de grupos ──────────────────────
        const drawProfiles = [];
        for (let i = 0; i < N; i++) {
            const nums = getN(history[i]);
            const numSet = new Set(nums);
            const profile = this.GROUPS.map(g => g.nums.filter(n => numSet.has(n)).length);
            // Perfil canônico: assinatura ordenada decrescente
            const canonSig = [...profile].sort((a,b) => b-a).join('-');
            // Perfil posicional: assinatura exata G1-G2-G3-G4-G5
            const exactSig = profile.join('-');
            drawProfiles.push({ profile, nums, numSet, canonSig, exactSig, draw: history[i].drawNumber });
        }

        // ── 1. FREQUÊNCIAS DE PERFIL ──────────────────────────────────────
        const canonFreq = {}, exactFreq = {};
        drawProfiles.forEach(dp => {
            canonFreq[dp.canonSig] = (canonFreq[dp.canonSig] || 0) + 1;
            exactFreq[dp.exactSig] = (exactFreq[dp.exactSig] || 0) + 1;
        });

        const topCanon = Object.entries(canonFreq)
            .map(([sig, cnt]) => ({ sig, cnt, pct: Math.round(cnt/N*100) }))
            .sort((a,b) => b.cnt - a.cnt).slice(0, 12);

        const topExact = Object.entries(exactFreq)
            .map(([sig, cnt]) => ({ sig, cnt, pct: Math.round(cnt/N*100) }))
            .sort((a,b) => b.cnt - a.cnt).slice(0, 8);

        // ── 2. SCORES DE GRUPOS (multi-janela) ───────────────────────────
        const groupScores = this.GROUPS.map((g, gi) => {
            const w3  = drawProfiles.slice(0,  Math.min(3,N)).reduce((s,dp)=>s+dp.profile[gi],0);
            const w5  = drawProfiles.slice(0,  Math.min(5,N)).reduce((s,dp)=>s+dp.profile[gi],0);
            const w10 = drawProfiles.slice(0, Math.min(10,N)).reduce((s,dp)=>s+dp.profile[gi],0);
            const w20 = drawProfiles.slice(0, Math.min(20,N)).reduce((s,dp)=>s+dp.profile[gi],0);
            const wAll = drawProfiles.reduce((s,dp) => s+dp.profile[gi], 0);

            const avgAll = wAll / N;           // ~3.0 esperado
            const avg10  = w10 / Math.min(10,N);
            const avg5   = w5  / Math.min(5,N);
            const avg3   = w3  / Math.min(3,N);

            // Momentum: recente vs histórico
            const momentum = avgAll > 0 ? avg5 / avgAll : 1;

            // Tendência de aceleração (últimos 3 vs últimos 10)
            const acceleration = avg10 > 0 ? avg3 / avg10 : 1;

            // Pressão de retorno (se acima ou abaixo da média histórica)
            const regression = 3 - avgAll; // força de volta ao equilíbrio

            // Atraso: quando o grupo contribuiu abaixo de 3 pela última vez?
            let lastLow = -1, lastHigh = -1;
            for (let i = 0; i < N; i++) {
                if (lastLow < 0 && drawProfiles[i].profile[gi] < 3) lastLow = i;
                if (lastHigh < 0 && drawProfiles[i].profile[gi] > 3) lastHigh = i;
                if (lastLow >= 0 && lastHigh >= 0) break;
            }

            // Status comportamental
            let status, statusEmoji;
            if (avg3 >= 4.0)       { status = 'Super-Quente'; statusEmoji = '🔥🔥'; }
            else if (avg3 >= 3.5)  { status = 'Quente';       statusEmoji = '🔥'; }
            else if (avg3 <= 1.5)  { status = 'Frio';         statusEmoji = '🧊'; }
            else if (avg3 <= 2.5)  { status = 'Esfriando';    statusEmoji = '❄️'; }
            else if (momentum > 1.2){ status = 'Subindo';      statusEmoji = '📈'; }
            else if (momentum < 0.8){ status = 'Caindo';       statusEmoji = '📉'; }
            else                    { status = 'Estável';      statusEmoji = '➡️'; }

            return {
                ...g, gi,
                w3, w5, w10, w20, wAll,
                avg3: avg3.toFixed(2), avg5: avg5.toFixed(2),
                avg10: avg10.toFixed(2), avgAll: avgAll.toFixed(2),
                momentum: momentum.toFixed(2),
                acceleration: acceleration.toFixed(2),
                regression: regression.toFixed(2),
                deviation: (((avgAll - 3) / 3) * 100).toFixed(1),
                lastLow, lastHigh,
                status, statusEmoji
            };
        });

        // ── 3. SCORES DE COLUNAS ──────────────────────────────────────────
        const colScores = this.COLS.map((col, ci) => {
            const w10  = drawProfiles.slice(0, Math.min(10,N)).reduce((s,dp) =>
                s + col.nums.filter(n => dp.numSet.has(n)).length, 0);
            const w20  = drawProfiles.slice(0, Math.min(20,N)).reduce((s,dp) =>
                s + col.nums.filter(n => dp.numSet.has(n)).length, 0);
            const wAll = drawProfiles.reduce((s,dp) =>
                s + col.nums.filter(n => dp.numSet.has(n)).length, 0);

            const avgAll = wAll / N;    // ~3.0 esperado (15/25 * 5 = 3)
            const avg10  = w10 / Math.min(10,N);
            const deviation = ((avgAll - 3) / 3 * 100).toFixed(1);
            const momentum = avgAll > 0 ? avg10 / avgAll : 1;

            let status;
            if (avg10 >= 3.5)      status = '🔥 Quente';
            else if (avg10 <= 2.5) status = '❄️ Fria';
            else                   status = '➡️ Normal';

            return { ...col, ci, w10, w20, wAll, avg10: avg10.toFixed(2), avgAll: avgAll.toFixed(2), deviation, momentum: momentum.toFixed(2), status };
        });

        // ── 4. MATRIZ DE CALOR 5×5 ───────────────────────────────────────
        // heatMatrix[gi][ci] = quantas vezes número[gi][ci] foi sorteado
        const heatMatrix = Array.from({length:5}, () => Array(5).fill(0));
        const heatMatrixPos = Array.from({length:5}, (_, gi) =>
            Array.from({length:5}, (__, ci) => this.GROUPS[gi].nums[ci])
        );
        drawProfiles.forEach(dp => {
            dp.nums.forEach(n => {
                const gi = this.GROUPS.findIndex(g => g.nums.includes(n));
                const ci = this.COLS.findIndex(c => c.nums.includes(n));
                if (gi >= 0 && ci >= 0) heatMatrix[gi][ci]++;
            });
        });
        const heatMax = Math.max(...heatMatrix.flat());
        const heatMin = Math.min(...heatMatrix.flat());

        // ── 5. SCORE INDIVIDUAL DE CADA NÚMERO ───────────────────────────
        const numScores = {};
        for (let n = 1; n <= 25; n++) {
            const cnt3  = drawProfiles.slice(0,3).filter(dp => dp.numSet.has(n)).length;
            const cnt5  = drawProfiles.slice(0,5).filter(dp => dp.numSet.has(n)).length;
            const cnt10 = drawProfiles.slice(0,10).filter(dp => dp.numSet.has(n)).length;
            const cntAll = drawProfiles.filter(dp => dp.numSet.has(n)).length;

            // Delay
            let delay = 0;
            for (let i = 0; i < N; i++) {
                if (drawProfiles[i].numSet.has(n)) break;
                delay++;
            }

            // Expected return: ~1.67 sorteios (25/15)
            const expReturn = 25/15;
            const delayPressure = Math.min(1, delay / (expReturn * 4));

            // Frequência ponderada (recente > antigo)
            const freqScore = (cnt3/3)*0.38 + (cnt5/5)*0.28 + (cnt10/10)*0.22 + (cntAll/N)*0.12;

            // Momentum dentro do grupo
            const gi    = this.GROUPS.findIndex(g => g.nums.includes(n));
            const gsAvg = gi >= 0 ? parseFloat(groupScores[gi].avg5) : 3;
            const groupMomentum = gsAvg / 3;

            const totalScore = freqScore * 0.65 + delayPressure * 0.20 + (groupMomentum - 1) * 0.15;

            numScores[n] = { num: n, cnt3, cnt5, cnt10, cntAll, delay, freqScore: Math.round(freqScore*100), delayPressure: Math.round(delayPressure*100), totalScore: Math.max(0, Math.round(totalScore * 1000)/1000) };
        }

        // ── 6. CORRELAÇÕES ENTRE GRUPOS ──────────────────────────────────
        // corr[i][j] > 0: quando Gi é alto (>3), Gj também tende a ser alto
        // corr[i][j] < 0: quando Gi é alto, Gj tende a ser baixo (complementar)
        const corrMatrix = Array.from({length:5}, () => Array(5).fill(0));
        drawProfiles.forEach(dp => {
            for (let i = 0; i < 5; i++) {
                const devI = dp.profile[i] - 3;
                for (let j = 0; j < 5; j++) {
                    const devJ = dp.profile[j] - 3;
                    corrMatrix[i][j] += devI * devJ;
                }
            }
        });
        // Normalizar
        const corrNorm = corrMatrix.map(row => row.map(v => Number((v/N).toFixed(3))));

        // ── 7. PADRÕES TEMPORAIS nos últimos sorteios ────────────────────
        const recentPattern = drawProfiles.slice(0, 10).map(dp => ({
            draw: dp.draw, profile: dp.profile, exactSig: dp.exactSig
        }));

        // ── 8. SEQUÊNCIAS: algum grupo dominant 3+ vezes seguidas? ───────
        const streaks = this.GROUPS.map((g, gi) => {
            let streak = 0, streakType = '';
            for (let i = 0; i < Math.min(10,N); i++) {
                if (drawProfiles[i].profile[gi] >= 4) { if(streakType === 'H') streak++; else { streak=1; streakType='H'; } }
                else if (drawProfiles[i].profile[gi] <= 2) { if(streakType === 'L') streak++; else { streak=1; streakType='L'; } }
                else break;
            }
            return { group: g.label, streak, streakType, emoji: streakType === 'H' ? '🔴' : streakType === 'L' ? '🔵' : '⚪' };
        });

        // ── 9. PREVISÃO DO PRÓXIMO PERFIL ─────────────────────────────────
        const prediction = this._predictNextProfile(drawProfiles, groupScores, corrNorm);

        console.log(`[LGE-V1] ✅ Análise: ${N} sorteios | Top perfil: "${topCanon[0]?.sig}" (${topCanon[0]?.pct}%) | Pred: ${prediction.map(p => p.predicted).join('-')}`);

        return {
            N, gameKey: 'lotofacil',
            drawProfiles, topCanon, topExact,
            groupScores, colScores,
            heatMatrix, heatMatrixPos, heatMax, heatMin,
            numScores, corrNorm, recentPattern, streaks, prediction
        };
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // PREVISÃO DO PRÓXIMO PERFIL
    // Considera: regressão à média, momentum, correlações, anti-streak
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _predictNextProfile(drawProfiles, groupScores, corrNorm) {
        const recent5 = drawProfiles.slice(0, Math.min(5, drawProfiles.length));

        const rawPredicted = this.GROUPS.map((g, gi) => {
            const avg5  = recent5.reduce((s,dp) => s+dp.profile[gi], 0) / recent5.length;
            const avgAll = parseFloat(groupScores[gi].avgAll);
            const mom    = parseFloat(groupScores[gi].momentum);
            const accel  = parseFloat(groupScores[gi].acceleration);

            // Componente 1: regressão à média (pressão de voltar para 3)
            const regress = (3 - avg5) * 0.6;

            // Componente 2: inércia de momentum (mas atenuada)
            const inertia = (mom - 1) * 0.2;

            // Componente 3: anti-streak (se grupo teve streak alta, tende a cair)
            const antiStreak = accel > 1.4 ? -0.3 : accel < 0.6 ? +0.3 : 0;

            // Componente 4: desvio histórico longo (viés estrutural)
            const structBias = (avgAll - 3) * 0.15;

            // Componente 5: correlação com o último sorteio
            const lastProfile = drawProfiles[0]?.profile || [3,3,3,3,3];
            let corrEffect = 0;
            for (let j = 0; j < 5; j++) {
                if (j !== gi) corrEffect += corrNorm[j][gi] * (lastProfile[j] - 3) * 0.1;
            }

            const raw = 3 + regress + inertia + antiStreak + structBias + corrEffect;
            return { group: g.label, color: g.color, gi, raw: Math.max(0.5, Math.min(5, raw)) };
        });

        // Normalizar para soma = 15
        const total = rawPredicted.reduce((s,p) => s+p.raw, 0);
        const factor = 15 / total;
        return rawPredicted.map(p => {
            const predicted = Math.max(1, Math.round(p.raw * factor * 10) / 10);
            return { ...p, predicted, rounded: Math.round(predicted) };
        });
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // GERAÇÃO DE NÚMEROS USANDO ANÁLISE DE GRUPOS
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    generate(history, targetCount = 15, useColBalance = true) {
        const analysis = this.analyze(history);
        if (!analysis) return { numbers: [], analysis: null };

        const { prediction, numScores, colScores } = analysis;
        const result = [];

        // Determinar quantos pegar de cada grupo (arredondamento inteligente)
        const targets = this._allocateByProfile(prediction, targetCount);

        // Selecionar números dentro de cada grupo
        for (let gi = 0; gi < 5; gi++) {
            const group = this.GROUPS[gi];
            const want  = targets[gi];
            if (want <= 0) continue;

            // Ordenar números do grupo por score total
            const groupNums = group.nums
                .map(n => numScores[n])
                .sort((a,b) => b.totalScore - a.totalScore);

            // Selecionar com pequena aleatoriedade ponderada por score
            const pool = groupNums.slice(0, Math.min(want + 2, 5));
            const picked = this._weightedSample(pool, want, n => Math.max(0.001, n.totalScore));
            picked.forEach(ns => result.push(ns.num));
        }

        // Ajustar para exatamente targetCount
        this._fillToTarget(result, numScores, targetCount);

        // Otimizar equilíbrio de colunas (opcional)
        if (useColBalance) {
            this._optimizeColumnBalance(result, numScores, colScores);
        }

        return {
            numbers: [...new Set(result)].sort((a,b) => a-b).slice(0, targetCount),
            analysis,
            groupAllocation: targets,
            profile: targets.join('-')
        };
    },

    // Distribuir targetCount pelos grupos baseado na previsão
    _allocateByProfile(prediction, total) {
        // Arredondamento pelo maior resto
        const floats = prediction.map(p => p.predicted * total / 15);
        const floors = floats.map(f => Math.floor(f));
        const remainder = total - floors.reduce((s,f) => s+f, 0);
        const indices = floats.map((f,i) => ({ i, frac: f - floors[i] }))
            .sort((a,b) => b.frac - a.frac);
        for (let k = 0; k < remainder; k++) floors[indices[k].i]++;
        return floors;
    },

    // Seleção ponderada por score sem reposição
    _weightedSample(pool, count, scoreFn) {
        const selected = [];
        const avail = [...pool];
        for (let k = 0; k < count && avail.length > 0; k++) {
            const totalW = avail.reduce((s,x) => s + scoreFn(x), 0);
            let rand = Math.random() * totalW;
            let chosen = avail[0];
            for (const item of avail) {
                rand -= scoreFn(item);
                if (rand <= 0) { chosen = item; break; }
            }
            selected.push(chosen);
            avail.splice(avail.indexOf(chosen), 1);
        }
        return selected;
    },

    // Preencher/reduzir para exatamente targetCount
    _fillToTarget(result, numScores, target) {
        const existing = new Set(result);
        while (result.length < target) {
            const missing = Array.from({length:25},(_,i)=>i+1).filter(n => !existing.has(n));
            if (!missing.length) break;
            const best = missing.sort((a,b) => numScores[b].totalScore - numScores[a].totalScore)[0];
            result.push(best); existing.add(best);
        }
        while (result.length > target) {
            // Remover o de menor score que não esteja em todos os grupos
            const sorted = result.slice().sort((a,b) => numScores[a].totalScore - numScores[b].totalScore);
            const rm = sorted[0];
            result.splice(result.indexOf(rm), 1);
        }
    },

    // Ajustar equilíbrio de colunas (minimizar maxDeviation)
    _optimizeColumnBalance(result, numScores, colScores) {
        const MAX_PASSES = 5;
        for (let pass = 0; pass < MAX_PASSES; pass++) {
            const colCounts = this.COLS.map(col => result.filter(n => col.nums.includes(n)).length);
            const maxC  = Math.max(...colCounts);
            const minC  = Math.min(...colCounts);
            if (maxC - minC <= 1) break; // já equilibrado

            const heavyCol = colCounts.indexOf(maxC);
            const lightCol = colCounts.indexOf(minC);

            // Tentar trocar um número do heavy pelo melhor do light
            const fromHeavy = result.filter(n => this.COLS[heavyCol].nums.includes(n));
            const fromLight  = this.COLS[lightCol].nums.filter(n => !result.includes(n));
            if (!fromHeavy.length || !fromLight.length) break;

            // Trocar o de menor score do heavy pelo de maior score do light
            const remove = fromHeavy.sort((a,b) => numScores[a].totalScore - numScores[b].totalScore)[0];
            const add    = fromLight.sort((a,b) => numScores[b].totalScore - numScores[a].totalScore)[0];

            result.splice(result.indexOf(remove), 1);
            result.push(add);
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // RENDERIZAÇÃO DO PAINEL DE ANÁLISE
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    renderPanel(analysis, container, generated) {
        if (!analysis || !container) return;
        const { groupScores, colScores, heatMatrix, heatMatrixPos, heatMax, heatMin,
                topCanon, topExact, recentPattern, streaks, prediction, corrNorm, numScores, N } = analysis;

        container.innerHTML = `<div style="font-family:'Outfit','Inter',sans-serif; padding:4px;">

        <!-- ══ HEADER ══ -->
        <div style="background:linear-gradient(135deg,rgba(147,0,137,0.2),rgba(94,0,88,0.15));border:1px solid #930089A0;border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#c084fc;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;">🎯 MOTOR DE GRUPOS LGE-V1 — LOTOFÁCIL</div>
            <div style="font-size:0.9rem;font-weight:800;color:#f1f5f9;">5 Grupos × 5 Colunas · ${N} sorteios analisados</div>
            ${generated ? `<div style="margin-top:6px;font-size:0.72rem;color:#a21caf;">Perfil gerado: <span style="color:#f0abfc;font-weight:800;">${generated.profile}</span> → ${generated.numbers.join(' · ')}</div>` : ''}
        </div>

        <!-- ══ MATRIZ DE CALOR 5×5 ══ -->
        <div style="background:rgba(15,15,35,0.96);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">🌡️ MATRIZ DE CALOR 5×5 — Frequência de cada posição em ${N} sorteios</div>
            <!-- Cabeçalho de colunas -->
            <div style="display:grid;grid-template-columns:40px repeat(5,1fr);gap:3px;margin-bottom:3px;">
                <div></div>
                ${this.COLS.map(c => `<div style="text-align:center;font-size:0.58rem;color:#94a3b8;font-weight:700;">${c.id}</div>`).join('')}
            </div>
            ${this.GROUPS.map((g, gi) => `
            <div style="display:grid;grid-template-columns:40px repeat(5,1fr);gap:3px;margin-bottom:3px;">
                <div style="display:flex;align-items:center;justify-content:center;font-size:0.65rem;color:${g.color};font-weight:800;">${g.label}</div>
                ${[0,1,2,3,4].map(ci => {
                    const n  = heatMatrixPos[gi][ci];
                    const v  = heatMatrix[gi][ci];
                    const intensity = heatMax > heatMin ? (v - heatMin) / (heatMax - heatMin) : 0.5;
                    const isSelected = generated && generated.numbers.includes(n);
                    const bgColor = `hsl(${280 - Math.round(intensity*180)}, ${40+Math.round(intensity*60)}%, ${10+Math.round(intensity*35)}%)`;
                    const textColor = intensity > 0.5 ? '#f1f5f9' : '#94a3b8';
                    return `<div style="background:${bgColor};border:1px solid ${isSelected ? '#f0abfc' : 'rgba(255,255,255,0.05)'};border-radius:6px;padding:5px 2px;text-align:center;${isSelected ? 'box-shadow:0 0 6px #f0abfc80;' : ''}">
                        <div style="font-size:0.72rem;font-weight:800;color:${isSelected ? '#f0abfc' : textColor};">${String(n).padStart(2,'0')}</div>
                        <div style="font-size:0.5rem;color:${textColor};opacity:0.7;">${v}×</div>
                    </div>`;
                }).join('')}
            </div>`).join('')}
            <!-- Legenda de calor -->
            <div style="display:flex;align-items:center;gap:4px;margin-top:6px;">
                <span style="font-size:0.58rem;color:#64748b;">Frio</span>
                <div style="flex:1;height:4px;border-radius:2px;background:linear-gradient(to right,hsl(280,40%,10%),hsl(180,70%,25%),hsl(100,100%,45%));"></div>
                <span style="font-size:0.58rem;color:#64748b;">Quente</span>
            </div>
        </div>

        <!-- ══ STATUS DOS GRUPOS ══ -->
        <div style="background:rgba(15,15,35,0.96);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">📊 STATUS DOS GRUPOS — Contribuição por sorteio (esperado: 3.00)</div>
            <div style="display:flex;flex-direction:column;gap:5px;">
                ${groupScores.map(gs => {
                    const predVal = prediction[gs.gi]?.predicted || 3;
                    const barPct = Math.round(parseFloat(gs.avg5) / 5 * 100);
                    return `<div style="display:flex;align-items:center;gap:6px;padding:7px 10px;background:${gs.color}10;border-radius:8px;border-left:3px solid ${gs.color};">
                        <span style="font-size:0.9rem;">${gs.statusEmoji}</span>
                        <div style="min-width:30px;font-size:0.72rem;font-weight:800;color:${gs.color};">${gs.label}</div>
                        <div style="flex:1;">
                            <div style="display:flex;justify-content:space-between;margin-bottom:3px;">
                                <span style="font-size:0.68rem;color:#f1f5f9;font-weight:600;">${gs.status}</span>
                                <span style="font-size:0.62rem;color:#94a3b8;">avg3: <b style="color:${gs.color};">${gs.avg3}</b> · avg10: ${gs.avg10} · geral: ${gs.avgAll}</span>
                            </div>
                            <div style="height:4px;background:rgba(255,255,255,0.08);border-radius:2px;">
                                <div style="height:100%;width:${barPct}%;background:${gs.color};border-radius:2px;transition:width 0.3s;"></div>
                            </div>
                        </div>
                        <div style="text-align:right;min-width:48px;">
                            <div style="font-size:0.58rem;color:#94a3b8;">Previsão</div>
                            <div style="font-size:0.78rem;font-weight:800;color:${gs.color};">${predVal.toFixed(1)}</div>
                        </div>
                    </div>`;
                }).join('')}
            </div>
        </div>

        <!-- ══ PREVISÃO DO PRÓXIMO PERFIL ══ -->
        <div style="background:linear-gradient(135deg,rgba(99,102,241,0.12),rgba(139,92,246,0.08));border:1px solid #6366f130;border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#a5b4fc;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">🔮 PREVISÃO DO PRÓXIMO PERFIL</div>
            <div style="display:flex;justify-content:center;gap:8px;margin-bottom:8px;">
                ${prediction.map(p => `
                <div style="text-align:center;background:${p.color}20;border:1px solid ${p.color}50;border-radius:8px;padding:6px 10px;min-width:42px;">
                    <div style="font-size:0.6rem;color:#94a3b8;">G${p.gi+1}</div>
                    <div style="font-size:1.1rem;font-weight:900;color:${p.color};">${p.predicted.toFixed(1)}</div>
                    <div style="font-size:0.6rem;color:${parseFloat(p.predicted)>3?'#22C55E':parseFloat(p.predicted)<3?'#EF4444':'#94a3b8'};">${parseFloat(p.predicted)>3?'↑':parseFloat(p.predicted)<3?'↓':'='}</div>
                </div>`).join('')}
            </div>
            <div style="text-align:center;font-size:0.68rem;color:#64748b;">Perfil previsto: <span style="color:#a5b4fc;font-weight:700;">${prediction.map(p=>p.rounded).join('-')}</span></div>
        </div>

        <!-- ══ PADRÕES MAIS FREQUENTES ══ -->
        <div style="background:rgba(15,15,35,0.96);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">📐 PERFIS MAIS FREQUENTES (assinatura canônica)</div>
            <div style="display:flex;flex-wrap:wrap;gap:5px;">
                ${topCanon.slice(0,10).map((p, ri) => `
                <div style="background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.1);border-radius:8px;padding:5px 8px;min-width:70px;text-align:center;">
                    <div style="font-size:0.72rem;font-weight:800;color:${ri===0?'#f0abfc':'#a5b4fc'};">${p.sig}</div>
                    <div style="font-size:0.6rem;color:#64748b;">${p.cnt}× · ${p.pct}%</div>
                    <div style="height:3px;background:rgba(255,255,255,0.08);border-radius:2px;margin-top:3px;">
                        <div style="height:100%;width:${Math.round(p.pct/topCanon[0].pct*100)}%;background:${ri===0?'#c026d3':'#6366f1'};border-radius:2px;"></div>
                    </div>
                </div>`).join('')}
            </div>
        </div>

        <!-- ══ CORRELAÇÕES ENTRE GRUPOS ══ -->
        <div style="background:rgba(15,15,35,0.96);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">🔗 CORRELAÇÕES ENTRE GRUPOS — quando Gi é alto, Gj tende a ser...</div>
            <div style="display:grid;grid-template-columns:30px repeat(5,1fr);gap:2px;">
                <div></div>
                ${this.GROUPS.map(g => `<div style="text-align:center;font-size:0.6rem;color:${g.color};font-weight:700;">${g.label}</div>`).join('')}
                ${this.GROUPS.map((g, gi) => `
                <div style="display:contents;">
                    <div style="font-size:0.6rem;color:${g.color};font-weight:700;display:flex;align-items:center;">${g.label}</div>
                    ${corrNorm[gi].map((v, gj) => {
                        const intensity = Math.min(1, Math.abs(v) / 1.5);
                        const bg = gi===gj ? 'rgba(255,255,255,0.04)' : v > 0.1 ? `rgba(34,197,94,${0.1+intensity*0.4})` : v < -0.1 ? `rgba(239,68,68,${0.1+intensity*0.4})` : 'rgba(255,255,255,0.03)';
                        const tc = gi===gj ? '#94a3b8' : v > 0.1 ? '#22C55E' : v < -0.1 ? '#EF4444' : '#64748b';
                        return `<div style="background:${bg};border-radius:4px;padding:4px;text-align:center;font-size:0.6rem;color:${tc};font-weight:${Math.abs(v)>0.1?'700':'400'};">${gi===gj?'—':(v>0?'+':'')+v.toFixed(2)}</div>`;
                    }).join('')}
                </div>`).join('')}
            </div>
            <div style="font-size:0.6rem;color:#64748b;margin-top:4px;">🟢 Positivo: tendem a sair juntos · 🔴 Negativo: quando um é alto, o outro é baixo</div>
        </div>

        <!-- ══ STATUS DAS COLUNAS ══ -->
        <div style="background:rgba(15,15,35,0.96);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">📏 STATUS DAS COLUNAS (esperado: 3.00/sorteio)</div>
            <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:6px;">
                ${colScores.map(cs => {
                    const pct = Math.round(parseFloat(cs.avg10)/5*100);
                    const gc = parseFloat(cs.avg10) > 3.2 ? '#22C55E' : parseFloat(cs.avg10) < 2.8 ? '#EF4444' : '#94a3b8';
                    return `<div style="background:rgba(255,255,255,0.04);border:1px solid ${gc}30;border-radius:8px;padding:8px;text-align:center;">
                        <div style="font-size:0.65rem;font-weight:800;color:${gc};">${cs.id}</div>
                        <div style="font-size:0.55rem;color:#64748b;">${cs.nums.join(',')}</div>
                        <div style="font-size:0.88rem;font-weight:900;color:${gc};margin-top:3px;">${cs.avg10}</div>
                        <div style="font-size:0.55rem;color:#94a3b8;">${cs.status}</div>
                    </div>`;
                }).join('')}
            </div>
        </div>

        <!-- ══ ÚLTIMOS 10 SORTEIOS ══ -->
        <div style="background:rgba(15,15,35,0.96);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;">
            <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">📋 ÚLTIMOS ${recentPattern.length} SORTEIOS — Perfil por grupo</div>
            <div style="display:flex;flex-direction:column;gap:3px;">
                ${recentPattern.map((rp, ri) => {
                    const colors = ['#EF4444','#F97316','#EAB308','#22C55E','#6366f1'];
                    return `<div style="display:flex;align-items:center;gap:4px;">
                        <span style="font-size:0.6rem;color:#64748b;min-width:42px;">#${rp.draw||'?'}</span>
                        ${rp.profile.map((v, gi) => `<div style="
                            min-width:20px;text-align:center;padding:2px 4px;border-radius:4px;
                            background:${colors[gi]}${v>=4?'40':v<=2?'15':'28'};
                            font-size:0.65rem;font-weight:800;
                            color:${colors[gi]};
                            border:1px solid ${colors[gi]}${v>=4?'80':v<=2?'20':'40'};
                        ">${v}</div>`).join('')}
                        <span style="font-size:0.58rem;color:#475569;margin-left:2px;">${rp.profile.join('-')}</span>
                    </div>`;
                }).join('')}
                <div style="display:flex;gap:4px;margin-top:4px;opacity:0.5;">
                    ${this.GROUPS.map(g => `<div style="min-width:20px;text-align:center;font-size:0.55rem;color:${g.color};">${g.label}</div>`).join('')}
                </div>
            </div>
        </div>

        </div>`;
    }
};
