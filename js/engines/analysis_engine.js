/**
 * ╔══════════════════════════════════════════════════════════════════════════╗
 * ║  ANALYSIS ENGINE — AE-V2 (Deep Pattern Intelligence)                    ║
 * ║  12 Dimensões + DeepPatternEngine (8 módulos avançados)                 ║
 * ╠══════════════════════════════════════════════════════════════════════════╣
 * ║  "Os acertos começam na ESCOLHA CORRETA dos números"                    ║
 * ║                                                                          ║
 * ║  MÓDULOS:                                                                ║
 * ║  1. Score por número (12 dimensões estatísticas)                         ║
 * ║  2. Perfil comportamental: Hot/Cooling/Dormant/Awakening/Cyclic          ║
 * ║  3. Projeção de saída: probabilidade p/ próximo concurso                 ║
 * ║  4. Autocorrelação: periodicidade e padrão de retorno                    ║
 * ║  5. Análise de pares: quem sai junto com quem                            ║
 * ║  6. Detecção de viés estatístico no sistema                              ║
 * ║  7. Padrões aritméticos nos sorteios (somas, progressões)                ║
 * ║  8. Mapa de calor temporal do volante                                    ║
 * ╚══════════════════════════════════════════════════════════════════════════╝
 */

const AnalysisEngine = {

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // PONTO DE ENTRADA PRINCIPAL
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    analyze(gameKey, selectedNumbers, history) {
        if (!selectedNumbers || selectedNumbers.length === 0 || !history || history.length < 3) return null;

        const game  = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        const min   = game ? game.range[0] : 1;
        const max   = game ? game.range[1] : 60;
        // CRITICO: usar game.draw (bolas sorteadas), NAO game.minBet (aposta do jogador)
        // Lotomania: minBet=50 (jogador aposta 50) mas draw=20 (20 bolas saem)
        const drawSize   = game ? (game.draw || game.minBet) : 6;
        const betSize    = game ? game.minBet : drawSize; // aposta do jogador
        const totalRange = max - min + 1;
        const N = history.length;

        console.log(`[AE-V2] 🔬 Análise Profunda: ${selectedNumbers.length} nums | ${gameKey} | ${N} sorteios | draw=${drawSize} bet=${betSize}`);

        // ── 1. Score de todos os números do range ─────────────────────────
        const allScores = {};
        for (let n = min; n <= max; n++) {
            allScores[n] = this._scoreNumber(n, history, min, max, drawSize, totalRange);
        }
        const allRanked = Object.entries(allScores)
            .map(([n, s]) => ({ num: parseInt(n), score: s.total, dims: s.dims }))
            .sort((a, b) => b.score - a.score);

        const selectedScores = selectedNumbers.map(n => ({
            num: n, score: allScores[n] ? allScores[n].total : 0,
            dims: allScores[n] ? allScores[n].dims : {},
            rank: allRanked.findIndex(r => r.num === n) + 1
        })).sort((a, b) => b.score - a.score);

        const topN    = allRanked.slice(0, selectedNumbers.length);
        const topNSet = new Set(topN.map(r => r.num));
        const selSet  = new Set(selectedNumbers);

        const selectionHits      = selectedNumbers.filter(n => topNSet.has(n));
        const missedOpportunities = topN.filter(r => !selSet.has(r.num));
        const weakPicks          = selectedScores.filter(s => !topNSet.has(s.num)).sort((a, b) => a.score - b.score);

        const topNTotal   = topN.reduce((s, r) => s + r.score, 0);
        const selTotal    = selectedScores.reduce((s, r) => s + r.score, 0);
        const coverageScore    = topNTotal > 0 ? Math.min(100, selTotal / topNTotal * 100) : 0;
        const positioningScore = selectionHits.length / selectedNumbers.length * 100;
        const overallEfficiency = Math.round(coverageScore * 0.50 + positioningScore * 0.50);

        // ── 2. DEEP PATTERN ENGINE ────────────────────────────────────────
        const behaviorProfiles = this._buildBehaviorProfiles(allScores, history, min, max, drawSize, totalRange);
        const projection       = this._projectNextDraw(allRanked, behaviorProfiles, history, min, max, drawSize, totalRange);
        const pairAnalysis     = this._analyzePairs(history, min, max);
        const systemBias       = this._detectSystemBias(history, min, max, drawSize, totalRange);
        const arithmeticPats   = this._detectArithmeticPatterns(history, min, max, drawSize);
        const distribution     = this._analyzeDistribution(selectedNumbers, history, min, max, drawSize, totalRange);
        const backtestResult   = this._backtestSelection(selectedNumbers, history, drawSize, totalRange);


        console.log(`[AE-V2] ✅ Ef=${overallEfficiency}% | Pos=${Math.round(positioningScore)}% | Cov=${Math.round(coverageScore)}%`);

        return {
            gameKey, selectedNumbers, selectedScores, allRanked, topN,
            selectionHits, missedOpportunities, weakPicks,
            overallEfficiency, coverageScore: Math.round(coverageScore),
            positioningScore: Math.round(positioningScore),
            behaviorProfiles, projection, pairAnalysis, systemBias, arithmeticPats,
            distribution, backtestResult, historySize: N, drawSize, min, max
        };
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 1. SCORE INDIVIDUAL — 12 dimensões
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _scoreNumber(n, history, min, max, drawSize, totalRange) {
        const N = history.length;
        const getDrawNums = d => (d.numbers || []).concat(d.numbers2 || []);
        const dims = {};

        // D1 — Frequência multi-janela ponderada
        const wins3 = history.slice(0,Math.min(3,N)).filter(d => getDrawNums(d).includes(n)).length;
        const wins5 = history.slice(0,Math.min(5,N)).filter(d => getDrawNums(d).includes(n)).length;
        const wins10= history.slice(0,Math.min(10,N)).filter(d => getDrawNums(d).includes(n)).length;
        const wins15= history.slice(0,Math.min(15,N)).filter(d => getDrawNums(d).includes(n)).length;
        const winsAll = history.filter(d => getDrawNums(d).includes(n)).length;
        const freqScore = (wins3/3)*0.35 + (wins5/Math.min(5,N))*0.25 + (wins10/Math.min(10,N))*0.20 + (wins15/Math.min(15,N))*0.12 + (winsAll/N)*0.08;
        dims.frequencia = { score: freqScore, val: `${wins5}/${Math.min(5,N)} | ${wins10}/${Math.min(10,N)} | ${wins15}/${Math.min(15,N)} | total:${winsAll}` };

        // D2 — Atraso vs retorno esperado
        let lastSeen = -1;
        const appearances = [];
        for (let i = 0; i < N; i++) {
            if (getDrawNums(history[i]).includes(n)) { if (lastSeen < 0) lastSeen = i; appearances.push(i); }
        }
        const delay = lastSeen < 0 ? N : lastSeen;
        const expectedReturn = totalRange / drawSize; // usa draw (bolas sorteadas), coreto para Lotomania
        const delayScore = delay >= expectedReturn*2.5 ? 1.0 : delay >= expectedReturn*1.8 ? 0.85 : delay >= expectedReturn*1.2 ? 0.60 : delay >= expectedReturn*0.7 ? 0.35 : delay <= 1 ? 0.05 : 0.20;
        dims.atraso = { score: delayScore, val: `${delay} sorteios sem sair (esp: ${expectedReturn.toFixed(1)})`, delay };

        // D3 — Pressão de vácuo
        const probPerDraw = drawSize / totalRange;
        const vacuumPressure = 1 - Math.pow(1 - probPerDraw, delay + 1);
        dims.vacuo = { score: vacuumPressure, val: `${(vacuumPressure*100).toFixed(1)}% prob. acumulada` };

        // D4 — Tendência / Momentum
        const freq5  = wins5  / Math.min(5, N);
        const freq15 = wins15 / Math.max(1, Math.min(15, N));
        const momentum = freq5 > 0 && freq15 > 0 ? freq5/freq15 : (freq5 > 0 ? 2.0 : 0.5);
        const momentumScore = momentum >= 2.0 ? 1.0 : momentum >= 1.5 ? 0.80 : momentum >= 1.0 ? 0.55 : momentum >= 0.5 ? 0.30 : 0.10;
        dims.tendencia = { score: momentumScore, val: momentum >= 1.5 ? '📈 Acelerando' : momentum >= 0.8 ? '➡️ Estável' : '📉 Desacelerando', momentum };

        // D5 — Autocorrelação (periodicidade real)
        let cycleScore = 0.30, avgPeriod = 0, periodStd = 0;
        if (appearances.length >= 3) {
            const periods = [];
            for (let k = 1; k < appearances.length; k++) periods.push(appearances[k] - appearances[k-1]);
            avgPeriod = periods.reduce((s,p) => s+p, 0) / periods.length;
            periodStd = Math.sqrt(periods.reduce((s,p) => s+(p-avgPeriod)**2, 0) / periods.length);
            const stability = avgPeriod > 0 ? Math.max(0, 1 - periodStd/avgPeriod) : 0;
            const drawsFromLastAppearance = lastSeen < 0 ? N : lastSeen;
            const onCycle = Math.abs(drawsFromLastAppearance - avgPeriod) <= avgPeriod * 0.35;
            cycleScore = stability * 0.65 + (onCycle ? 0.35 : 0.05);
        }
        dims.ciclos = { score: cycleScore, val: appearances.length >= 2 ? `período médio: ${avgPeriod.toFixed(1)} ±${periodStd.toFixed(1)} sorteios` : 'dados insuficientes', avgPeriod, periodStd, appearances: appearances.length };

        // D6 — Markov (transição do último sorteio)
        const lastDraw = getDrawNums(history[0] || {});
        let markovScore = 0;
        for (let i = 1; i < Math.min(25,N); i++) {
            const older = getDrawNums(history[i]);
            const newer = getDrawNums(history[i-1]);
            const decay = Math.exp(-i * 0.12);
            if (older.some(m => lastDraw.includes(m)) && newer.includes(n)) markovScore += decay * 0.08;
        }
        dims.markov = { score: Math.min(1, markovScore), val: `${(Math.min(1,markovScore)*100).toFixed(0)}% correlação trajetória` };

        // D7 — Emaranhamento temporal (vizinhança)
        const prevDraw = getDrawNums(history[1] || {});
        let entScore = 0;
        [n-3,n-2,n-1,n+1,n+2,n+3].filter(x=>x>=min&&x<=max).forEach(nb => {
            if (lastDraw.includes(nb)) entScore += 0.12;
            if (prevDraw.includes(nb)) entScore += 0.06;
        });
        dims.emaranhamento = { score: Math.min(1,entScore), val: `${(Math.min(1,entScore)*100).toFixed(0)}% energia de vizinhança` };

        // D8 — Propriedades matemáticas
        const isFib = this._isFibonacci(n), isPrime = this._isPrime(n);
        dims.matematica = { score: (isPrime&&isFib)?1:(isFib?0.75:isPrime?0.55:0.30), val: isFib?'✦ Fibonacci':isPrime?'◈ Primo':'○ Regular' };

        // D9 — Equilíbrio de zonas
        const numZones = Math.ceil(totalRange/10);
        const zone = Math.min(numZones-1, Math.floor((n-min)/10));
        const zoneHist = history.slice(0,Math.min(10,N)).reduce((cnt,d) => {
            return cnt + getDrawNums(d).filter(x=>Math.min(numZones-1,Math.floor((x-min)/10))===zone).length;
        }, 0);
        const idealZone = 10*drawSize/numZones;
        const zoneDeviation = Math.abs(zoneHist-idealZone)/Math.max(1,idealZone);
        dims.zona = { score: zoneHist < idealZone ? Math.min(1, 0.4+(1-zoneDeviation)*0.6) : Math.max(0.1, 0.6-zoneDeviation*0.5), val: `Zona ${zone+1}: ${zoneHist} apars. (esperado: ${idealZone.toFixed(1)})` };

        // D10 — Equilíbrio Par/Ímpar histórico
        let tEven=0, tNums=0;
        history.slice(0,Math.min(20,N)).forEach(d => {
            const ns = (d.numbers||[]).filter(x=>x>=min&&x<=max);
            tEven+=ns.filter(x=>x%2===0).length; tNums+=ns.length;
        });
        const histEvenRatio = tNums>0?tEven/tNums:0.5;
        const isEven = n%2===0;
        dims.parImpar = { score: Math.min(1, isEven?histEvenRatio+0.10:(1-histEvenRatio)+0.10), val: isEven?`Par (hist:${(histEvenRatio*100).toFixed(0)}% pares)`:`Ímpar (hist:${((1-histEvenRatio)*100).toFixed(0)}% ímpares)` };

        // D11 — Posição soma ideal
        const histSums = history.slice(0,Math.min(30,N))
            .filter(d=>(d.numbers||[]).filter(x=>x>=min&&x<=max).length===drawSize)
            .map(d=>d.numbers.reduce((s,x)=>s+x,0));
        let sumScore = 0.45;
        if (histSums.length>3) {
            histSums.sort((a,b)=>a-b);
            const med = histSums[Math.floor(histSums.length/2)];
            sumScore = Math.max(0.10, 1-Math.abs(n-med/drawSize)/((max-min)/2));
        }
        dims.somaIdeal = { score: sumScore, val: 'contribuição para soma mediana' };

        // D12 — Padrão de streak (sequência recente)
        let streak=0;
        for (let i=0;i<Math.min(8,N);i++) { if(getDrawNums(history[i]).includes(n))streak++; else break; }
        dims.sequencia = { score: streak===0?0.70:streak===1?0.85:streak===2?0.60:streak===3?0.35:0.15, val: streak===0?'Ausente (pressão alta)':`${streak} sorteios consecutivos`, streak };

        const weights = { frequencia:0.18, atraso:0.16, vacuo:0.14, tendencia:0.12, ciclos:0.08, markov:0.10, emaranhamento:0.06, matematica:0.04, zona:0.05, parImpar:0.03, somaIdeal:0.02, sequencia:0.02 };
        let total = 0;
        for (const [k,w] of Object.entries(weights)) total += (dims[k]?.score||0)*w;
        return { total: Math.round(total*1000)/1000, dims };
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 2. PERFIS COMPORTAMENTAIS POR NÚMERO
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _buildBehaviorProfiles(allScores, history, min, max, drawSize, totalRange) {
        const N = history.length;
        const getDrawNums = d => (d.numbers||[]).concat(d.numbers2||[]);
        const expectedReturn = totalRange / drawSize;
        const profiles = {};

        for (let n = min; n <= max; n++) {
            const sc  = allScores[n]?.dims || {};
            const delay = sc.atraso?.delay ?? 0;
            const streak = sc.sequencia?.streak ?? 0;
            const momentum = sc.tendencia?.momentum ?? 1;
            const cycleAvg = sc.ciclos?.avgPeriod ?? 0;
            const appearances = sc.ciclos?.appearances ?? 0;

            // Lógica de classificação por perfil
            let profile, emoji, color, description, prediction;

            if (streak >= 4) {
                profile = 'Super-Quente'; emoji = '🔥🔥'; color = '#EF4444';
                description = 'Saiu em 4+ sorteios seguidos — saturação iminente';
                prediction = 'Risco de resfriamento — próximos 2-3 sorteios';
            } else if (streak >= 2 && momentum >= 1.5) {
                profile = 'Quente'; emoji = '🔥'; color = '#F97316';
                description = 'Forte presença recente com momentum crescente';
                prediction = `Pode manter ou ceder em ${Math.ceil(expectedReturn * 0.5)} sorteios`;
            } else if (delay === 0 || delay === 1) {
                profile = 'Resfriando'; emoji = '🌡️'; color = '#F59E0B';
                description = 'Saiu no último sorteio — probabilidade reduzida temporariamente';
                prediction = `Pressão retorna em ~${Math.ceil(expectedReturn * 0.7)} sorteios`;
            } else if (delay >= expectedReturn * 2.5) {
                profile = 'Crítico'; emoji = '⚡'; color = '#8B5CF6';
                description = 'Ausente por período MUITO além do esperado — forte pressão de vácuo';
                prediction = 'Alta probabilidade de aparecer nos próximos 2-4 sorteios';
            } else if (delay >= expectedReturn * 1.5 && momentum >= 0.8) {
                profile = 'Despertando'; emoji = '🌅'; color = '#22C55E';
                description = 'Atrasado além do esperado e tendência estável — ponto de entrada ideal';
                prediction = 'Janela de entrada favorável — próximos 3-5 sorteios';
            } else if (cycleAvg > 0 && appearances >= 5 && sc.ciclos?.score > 0.6) {
                profile = 'Cíclico'; emoji = '🔄'; color = '#06B6D4';
                description = `Período regular de ~${cycleAvg.toFixed(0)} sorteios — padrão detectado`;
                prediction = `Próximo ciclo esperado em ~${Math.round(cycleAvg - delay)} sorteios`;
            } else if (delay >= expectedReturn * 0.8 && delay <= expectedReturn * 1.4) {
                profile = 'Neutro'; emoji = '⚪'; color = '#94a3b8';
                description = 'Dentro do intervalo esperado — sem pressão especial';
                prediction = 'Comportamento estatisticamente normal';
            } else if (streak === 0 && momentum < 0.5) {
                profile = 'Dormindo'; emoji = '💤'; color = '#475569';
                description = 'Ausente com tendência de queda — padrão de hibernação';
                prediction = 'Baixa probabilidade — aguardar confirmação de ciclo';
            } else {
                profile = 'Normal'; emoji = '○'; color = '#64748b';
                description = 'Comportamento típico para este estágio do ciclo';
                prediction = 'Sem padrão especial identificado';
            }

            profiles[n] = { profile, emoji, color, description, prediction, delay, streak, momentum, expectedReturn };
        }
        return profiles;
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 3. PROJEÇÃO DO PRÓXIMO CONCURSO
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _projectNextDraw(allRanked, behaviorProfiles, history, min, max, drawSize, totalRange) {
        // Combina score analítico com perfil comportamental
        const combined = allRanked.map(r => {
            const prof = behaviorProfiles[r.num];
            let profileMultiplier = 1.0;
            if (prof) {
                if (prof.profile === 'Crítico')      profileMultiplier = 1.45;
                if (prof.profile === 'Despertando')  profileMultiplier = 1.30;
                if (prof.profile === 'Cíclico')      profileMultiplier = 1.20;
                if (prof.profile === 'Neutro')       profileMultiplier = 1.00;
                if (prof.profile === 'Quente')       profileMultiplier = 0.90;
                if (prof.profile === 'Resfriando')   profileMultiplier = 0.70;
                if (prof.profile === 'Super-Quente') profileMultiplier = 0.55;
                if (prof.profile === 'Dormindo')     profileMultiplier = 0.65;
                if (prof.profile === 'Normal')       profileMultiplier = 0.95;
            }
            return { num: r.num, projScore: r.score * profileMultiplier, profile: prof?.profile || 'Normal', emoji: prof?.emoji || '○', color: prof?.color || '#94a3b8' };
        }).sort((a, b) => b.projScore - a.projScore);

        // Top candidatos para o próximo sorteio
        const topCandidates = combined.slice(0, Math.min(drawSize * 3, 20));

        // Score de confiança da projeção
        const N = history.length;
        const confScore = Math.min(95, Math.round(40 + (N / 50) * 30 + (topCandidates.filter(c => ['Crítico','Despertando','Cíclico'].includes(c.profile)).length / Math.max(1, topCandidates.length)) * 25));

        return { topCandidates, confidence: confScore };
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 4. ANÁLISE DE PARES (quem sai junto)
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _analyzePairs(history, min, max) {
        const N = Math.min(50, history.length);
        const getDrawNums = d => (d.numbers||[]).concat(d.numbers2||[]).filter(x=>x>=min&&x<=max);
        const pairCount = {};
        const numFreq = {};

        for (let i = 0; i < N; i++) {
            const nums = getDrawNums(history[i]);
            nums.forEach(n => { numFreq[n] = (numFreq[n]||0)+1; });
            for (let j = 0; j < nums.length; j++) {
                for (let k = j+1; k < nums.length; k++) {
                    const key = `${Math.min(nums[j],nums[k])}-${Math.max(nums[j],nums[k])}`;
                    pairCount[key] = (pairCount[key]||0)+1;
                }
            }
        }

        // Top pares por frequência ajustada (lift: frequência do par vs esperado)
        const allPairs = Object.entries(pairCount).map(([key, cnt]) => {
            const [a, b] = key.split('-').map(Number);
            const fa = (numFreq[a]||0)/N, fb = (numFreq[b]||0)/N;
            const expected = fa * fb * N;
            const lift = expected > 0 ? cnt/expected : 1;
            return { a, b, cnt, lift };
        }).sort((x, y) => y.lift - x.lift);

        return {
            topPairs: allPairs.slice(0, 10),
            hotPairs:  allPairs.filter(p => p.cnt >= 3 && p.lift >= 1.8).slice(0, 8)
        };
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 5. DETECÇÃO DE VIÉS ESTATÍSTICO DO SISTEMA
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _detectSystemBias(history, min, max, drawSize, totalRange) {
        const N = Math.min(100, history.length);
        const getDrawNums = d => (d.numbers||[]).concat(d.numbers2||[]).filter(x=>x>=min&&x<=max);
        const freq = {};
        for (let n = min; n <= max; n++) freq[n] = 0;
        for (let i = 0; i < N; i++) getDrawNums(history[i]).forEach(n => freq[n]++);

        const expected = N * drawSize / totalRange;
        const chiItems = Object.entries(freq).map(([n, f]) => ({
            n: parseInt(n), f, expected, chi: Math.pow(f-expected,2)/expected, deviation: (f-expected)/expected
        }));
        const chiSquare = chiItems.reduce((s,x) => s+x.chi, 0);

        // Quais números saem mais/menos do que o esperado
        const overperformers = chiItems.filter(x => x.deviation >= 0.3).sort((a,b) => b.deviation-a.deviation).slice(0,10);
        const underperformers = chiItems.filter(x => x.deviation <= -0.3).sort((a,b) => a.deviation-b.deviation).slice(0,10);

        // Análise de zonas: há zona favorecida?
        const numZones = Math.ceil(totalRange/10);
        const zoneFreq = new Array(numZones).fill(0);
        for (let i = 0; i < N; i++) {
            getDrawNums(history[i]).forEach(n => {
                const z = Math.min(numZones-1, Math.floor((n-min)/10));
                zoneFreq[z]++;
            });
        }
        const zoneExpected = N * drawSize / numZones;
        const zoneBias = zoneFreq.map((f, z) => ({ zone: z+1, f, expected: zoneExpected, deviation: (f-zoneExpected)/zoneExpected }));
        const biasedZones = zoneBias.filter(z => Math.abs(z.deviation) >= 0.15);

        // Viés par/ímpar
        let totalEven = 0, totalNums = 0;
        for (let i = 0; i < N; i++) {
            const ns = getDrawNums(history[i]);
            totalEven += ns.filter(x=>x%2===0).length;
            totalNums += ns.length;
        }
        const actualEvenRatio = totalNums > 0 ? totalEven/totalNums : 0.5;
        const rangeEvenRatio  = Math.floor(totalRange/2) / totalRange;
        const parImparBias    = actualEvenRatio - rangeEvenRatio;

        // Índice de aleatoriedade: Chi² / graus de liberdade
        const degreesOfFreedom = totalRange - 1;
        const randomnessIndex = Math.max(0, Math.min(100, Math.round(100 - (chiSquare / degreesOfFreedom - 1) * 50)));

        return {
            chiSquare: chiSquare.toFixed(1),
            randomnessIndex,
            overperformers: overperformers.slice(0, 6),
            underperformers: underperformers.slice(0, 6),
            zoneBias, biasedZones,
            parImparBias: parImparBias.toFixed(3),
            actualEvenRatio: (actualEvenRatio*100).toFixed(1)
        };
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 6. PADRÕES ARITMÉTICOS NOS SORTEIOS
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _detectArithmeticPatterns(history, min, max, drawSize) {
        const N = Math.min(50, history.length);
        const sums = [], avgs = [], ranges = [];
        let sumBins = {};

        for (let i = 0; i < N; i++) {
            const nums = (history[i].numbers||[]).filter(x=>x>=min&&x<=max);
            if (nums.length < drawSize * 0.7) continue;
            const sorted = [...nums].sort((a,b)=>a-b);
            const sum = sorted.reduce((s,x)=>s+x,0);
            const range = sorted[sorted.length-1] - sorted[0];
            sums.push(sum);
            avgs.push(sum/nums.length);
            ranges.push(range);
            // Binning de somas
            const bin = Math.floor(sum/20)*20;
            sumBins[bin] = (sumBins[bin]||0)+1;
        }

        if (sums.length < 3) return { available: false };

        const sumMean = sums.reduce((s,x)=>s+x,0)/sums.length;
        const sumStd  = Math.sqrt(sums.reduce((s,x)=>s+(x-sumMean)**2,0)/sums.length);
        const sumMin  = Math.min(...sums);
        const sumMax  = Math.max(...sums);
        const rangeAvg = ranges.reduce((s,x)=>s+x,0)/ranges.length;

        // Faixas de soma mais frequentes
        const topBins = Object.entries(sumBins).sort((a,b)=>b[1]-a[1]).slice(0,3).map(([k,v])=>({ range:`${k}-${parseInt(k)+19}`, count:v }));

        // Detectar últimas 5 somas — tendência
        const last5sums = sums.slice(0,5);
        const sumTrend = last5sums[0] > sumMean + sumStd*0.5 ? 'Alta' : last5sums[0] < sumMean - sumStd*0.5 ? 'Baixa' : 'Média';

        return {
            available: true,
            sumMean: sumMean.toFixed(1),
            sumStd:  sumStd.toFixed(1),
            sumMin, sumMax,
            rangeAvg: rangeAvg.toFixed(1),
            topBins,
            sumTrend,
            last5sums
        };
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // 7. DISTRIBUIÇÃO E BACKTESTING
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _analyzeDistribution(numbers, history, min, max, drawSize, totalRange) {
        const n = numbers.length;
        if (n === 0) return {};
        const evenCnt = numbers.filter(x=>x%2===0).length;
        const numZones = Math.ceil(totalRange/10);
        const zoneCounts = new Array(numZones).fill(0);
        numbers.forEach(x => { const z=Math.min(numZones-1,Math.floor((x-min)/10)); zoneCounts[z]++; });
        const sorted = [...numbers].sort((a,b)=>a-b);
        let maxConsec=1, curConsec=1;
        for (let i=1;i<sorted.length;i++) { if(sorted[i]===sorted[i-1]+1){curConsec++;maxConsec=Math.max(maxConsec,curConsec);}else curConsec=1; }
        const poolSet = new Set(numbers);
        const N = history.length;
        const recentHits = history.slice(0,Math.min(15,N)).map(d => (d.numbers||[]).concat(d.numbers2||[]).filter(x=>poolSet.has(x)).length);
        const avgPoolHit = recentHits.reduce((s,h)=>s+h,0)/Math.max(1,recentHits.length);
        const expectedPoolHit = drawSize*n/totalRange;
        return {
            evenCnt, oddCnt:n-evenCnt, evenPct:Math.round(evenCnt/n*100),
            zoneCounts, coveredZones:zoneCounts.filter(c=>c>0).length, numZones,
            sum:numbers.reduce((s,x)=>s+x,0), avg:(numbers.reduce((s,x)=>s+x,0)/n).toFixed(1),
            maxConsec, fibCount:numbers.filter(x=>this._isFibonacci(x)).length, primeCount:numbers.filter(x=>this._isPrime(x)).length,
            avgPoolHit:avgPoolHit.toFixed(2), expectedPoolHit:expectedPoolHit.toFixed(2),
            poolEfficiency:(avgPoolHit/Math.max(0.01,expectedPoolHit)).toFixed(2)
        };
    },

    _backtestSelection(numbers, history, drawSize, totalRange) {
        const poolSet = new Set(numbers);
        const N = Math.min(30, history.length);
        const results = [];
        let totalHits=0, wins=0, best=0;
        for (let i=0;i<N;i++) {
            const drawn = (history[i].numbers||[]).concat(history[i].numbers2||[]);
            const hits = drawn.filter(x=>poolSet.has(x)).length;
            totalHits+=hits; if(hits>best)best=hits; if(hits>=drawSize*0.4)wins++;
            results.push({ concurso:history[i].drawNumber||(N-i), hits, total:drawn.length });
        }
        const avgHits=totalHits/N, expectedHits=drawSize*numbers.length/totalRange;
        return { results:results.slice(0,10), avgHits:avgHits.toFixed(2), expectedHits:expectedHits.toFixed(2), improvement:(avgHits/Math.max(0.01,expectedHits)).toFixed(2), bestHit:best, wins, winRate:Math.round(wins/N*100) };
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // RENDERIZAÇÃO — painel visual completo
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    renderPanel(analysis, container) {
        if (!analysis || !container) return;
        const eff = analysis.overallEfficiency;
        const effColor = eff>=75?'#22C55E':eff>=55?'#F59E0B':'#EF4444';
        const game = typeof GAMES!=='undefined'?GAMES[analysis.gameKey]:null;
        const gc = game?game.color:'#6366f1';

        container.innerHTML = `<div style="font-family:'Outfit','Inter',sans-serif; margin-top:12px;">

        <!-- ══ HEADER ══ -->
        <div style="background:linear-gradient(135deg,rgba(15,15,35,0.98),rgba(20,10,45,0.98));border:1px solid ${gc}40;border-radius:14px;padding:16px;margin-bottom:10px;box-shadow:0 4px 30px rgba(0,0,0,0.5);">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:12px;">
                <div>
                    <div style="font-size:0.62rem;color:#94a3b8;letter-spacing:2px;text-transform:uppercase;">🔬 ANÁLISE PROFUNDA AE-V2</div>
                    <div style="font-size:0.95rem;font-weight:800;color:#f1f5f9;margin-top:2px;">${analysis.selectedNumbers.length} números · ${analysis.historySize} sorteios · 12 dimensões</div>
                </div>
                <div style="text-align:center;">
                    <div style="width:60px;height:60px;border-radius:50%;background:conic-gradient(${effColor} ${eff}%,rgba(255,255,255,0.08) 0%);display:flex;align-items:center;justify-content:center;box-shadow:0 0 18px ${effColor}40;">
                        <div style="width:44px;height:44px;border-radius:50%;background:#0f0f23;display:flex;align-items:center;justify-content:center;">
                            <span style="font-size:0.9rem;font-weight:900;color:${effColor};">${eff}%</span>
                        </div>
                    </div>
                    <div style="font-size:0.6rem;color:${effColor};font-weight:700;margin-top:3px;">EFICIÊNCIA</div>
                </div>
            </div>
            <div style="display:grid;grid-template-columns:repeat(3,1fr);gap:7px;">
                ${this._card('🎯','Posicionamento',analysis.positioningScore+'%',`${analysis.selectionHits.length}/${analysis.selectedNumbers.length} no top`,analysis.positioningScore>=60?'#22C55E':analysis.positioningScore>=40?'#F59E0B':'#EF4444')}
                ${this._card('📊','Cobertura',analysis.coverageScore+'%','vs seleção ideal',analysis.coverageScore>=70?'#22C55E':analysis.coverageScore>=50?'#F59E0B':'#EF4444')}
                ${this._card('🔄','BT Pool',analysis.backtestResult.improvement+'x',`avg ${analysis.backtestResult.avgHits} hits`,parseFloat(analysis.backtestResult.improvement)>=1.3?'#22C55E':parseFloat(analysis.backtestResult.improvement)>=1?'#F59E0B':'#EF4444')}
            </div>
        </div>

        <!-- ══ SEUS NÚMEROS COM SCORE ══ -->
        <div style="background:rgba(15,15,35,0.95);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">📌 SEUS NÚMEROS — Score + Perfil Comportamental</div>
            <div style="display:flex;flex-wrap:wrap;gap:5px;">
                ${analysis.selectedScores.map(s => {
                    const prof = analysis.behaviorProfiles[s.num];
                    const sc = s.score;
                    const inTop = analysis.selectionHits.includes(s.num);
                    const bc = sc>=0.55?'#22C55E':sc>=0.38?'#F59E0B':'#EF4444';
                    return `<div title="${prof?.description||''} | Score:${(sc*100).toFixed(0)}% | Rank:#${s.rank}" style="display:flex;flex-direction:column;align-items:center;gap:2px;background:rgba(255,255,255,0.04);border-radius:8px;padding:5px 7px;border:1px solid ${inTop?'#22C55E60':'#ffffff18'};min-width:34px;">
                        <span style="font-size:0.65rem">${prof?.emoji||'○'}</span>
                        <span style="font-size:0.82rem;font-weight:800;color:${inTop?'#22C55E':'#f1f5f9'};">${s.num}</span>
                        <div style="width:100%;height:3px;background:rgba(255,255,255,0.1);border-radius:2px;"><div style="width:${Math.round(sc*100)}%;height:100%;background:${bc};border-radius:2px;"></div></div>
                        <span style="font-size:0.55rem;color:${bc};">${(sc*100).toFixed(0)}%</span>
                    </div>`;
                }).join('')}
            </div>
        </div>

        <!-- ══ PROJEÇÃO PRÓXIMO CONCURSO ══ -->
        <div style="background:linear-gradient(135deg,rgba(99,102,241,0.12),rgba(139,92,246,0.08));border:1px solid #6366f130;border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#a5b4fc;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                🔮 PROJEÇÃO — Top candidatos para próximo sorteio
                <span style="color:#6366f1;margin-left:6px;">Confiança: ${analysis.projection.confidence}%</span>
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:4px;">
                ${analysis.projection.topCandidates.slice(0, 15).map(c => `
                <div title="${c.profile}" style="display:flex;flex-direction:column;align-items:center;gap:1px;background:${c.color}15;border:1px solid ${c.color}40;border-radius:7px;padding:4px 6px;min-width:30px;">
                    <span style="font-size:0.65rem;">${c.emoji}</span>
                    <span style="font-size:0.78rem;font-weight:800;color:${c.color};">${c.num}</span>
                </div>`).join('')}
            </div>
        </div>

        <!-- ══ PERFIS COMPORTAMENTAIS (selecionados) ══ -->
        <div style="background:rgba(15,15,35,0.95);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">🧠 PERFIS COMPORTAMENTAIS — Seus números</div>
            <div style="display:flex;flex-direction:column;gap:5px;">
                ${analysis.selectedScores.slice(0,8).map(s => {
                    const prof = analysis.behaviorProfiles[s.num];
                    if (!prof) return '';
                    return `<div style="display:flex;align-items:center;gap:8px;padding:6px 8px;background:${prof.color}10;border-radius:8px;border-left:3px solid ${prof.color};">
                        <span style="font-size:0.8rem;min-width:20px;text-align:center;">${prof.emoji}</span>
                        <span style="color:${prof.color};font-weight:700;font-size:0.72rem;min-width:28px;">${s.num}</span>
                        <div style="flex:1;">
                            <div style="font-size:0.7rem;color:#f1f5f9;font-weight:600;">${prof.profile} — ${prof.description}</div>
                            <div style="font-size:0.62rem;color:#94a3b8;margin-top:1px;">📅 ${prof.prediction}</div>
                        </div>
                        <span style="font-size:0.65rem;color:#64748b;white-space:nowrap;">atraso:${prof.delay}</span>
                    </div>`;
                }).join('')}
            </div>
        </div>

        <!-- ══ VIÉS DO SISTEMA ══ -->
        <div style="background:rgba(15,15,35,0.95);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                📡 VIÉS ESTATÍSTICO DO SISTEMA
                <span style="color:${analysis.systemBias.randomnessIndex>=70?'#22C55E':'#F59E0B'};margin-left:6px;">Aleatoriedade: ${analysis.systemBias.randomnessIndex}%</span>
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;margin-bottom:8px;">
                <div style="background:rgba(34,197,94,0.08);border:1px solid #22C55E20;border-radius:8px;padding:8px;">
                    <div style="font-size:0.6rem;color:#22C55E;margin-bottom:4px;">⬆️ SUPER-REPRESENTADOS</div>
                    <div style="display:flex;flex-wrap:wrap;gap:3px;">
                        ${analysis.systemBias.overperformers.map(p=>`<span style="background:#22C55E20;color:#22C55E;border-radius:4px;padding:2px 5px;font-size:0.68rem;font-weight:700;" title="${(p.deviation*100).toFixed(0)}% acima do esperado">${p.n} <small>+${(p.deviation*100).toFixed(0)}%</small></span>`).join('')}
                    </div>
                </div>
                <div style="background:rgba(239,68,68,0.08);border:1px solid #EF444420;border-radius:8px;padding:8px;">
                    <div style="font-size:0.6rem;color:#EF4444;margin-bottom:4px;">⬇️ SUB-REPRESENTADOS</div>
                    <div style="display:flex;flex-wrap:wrap;gap:3px;">
                        ${analysis.systemBias.underperformers.map(p=>`<span style="background:#EF444420;color:#F87171;border-radius:4px;padding:2px 5px;font-size:0.68rem;font-weight:700;" title="${(p.deviation*100).toFixed(0)}% abaixo do esperado">${p.n} <small>${(p.deviation*100).toFixed(0)}%</small></span>`).join('')}
                    </div>
                </div>
            </div>
            <div style="font-size:0.65rem;color:#64748b;">
                Par/Ímpar real: <span style="color:#f1f5f9;">${analysis.systemBias.actualEvenRatio}% pares</span>
                (viés: <span style="color:${Math.abs(parseFloat(analysis.systemBias.parImparBias))>0.05?'#F59E0B':'#22C55E'};">${parseFloat(analysis.systemBias.parImparBias)>0?'+':''}${(parseFloat(analysis.systemBias.parImparBias)*100).toFixed(1)}%</span>) •
                Chi²: <span style="color:#94a3b8;">${analysis.systemBias.chiSquare}</span>
            </div>
        </div>

        <!-- ══ ANÁLISE DE PARES ══ -->
        ${analysis.pairAnalysis.hotPairs.length > 0 ? `
        <div style="background:rgba(15,15,35,0.95);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">🔗 PARES QUENTES — Co-ocorrência acima do esperado</div>
            <div style="display:flex;flex-wrap:wrap;gap:5px;">
                ${analysis.pairAnalysis.hotPairs.map(p=>`
                <div style="background:rgba(99,102,241,0.12);border:1px solid #6366f130;border-radius:8px;padding:5px 8px;text-align:center;">
                    <div style="font-size:0.78rem;font-weight:800;color:#a5b4fc;">${p.a}–${p.b}</div>
                    <div style="font-size:0.58rem;color:#64748b;">${p.cnt}x · lift ${p.lift.toFixed(1)}x</div>
                </div>`).join('')}
            </div>
        </div>` : ''}

        <!-- ══ PADRÕES ARITMÉTICOS ══ -->
        ${analysis.arithmeticPats.available ? `
        <div style="background:rgba(15,15,35,0.95);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">📐 PADRÕES ARITMÉTICOS NOS SORTEIOS</div>
            <div style="display:grid;grid-template-columns:repeat(2,1fr);gap:6px;font-size:0.7rem;">
                <div style="background:rgba(255,255,255,0.04);border-radius:8px;padding:8px;">
                    <div style="color:#94a3b8;font-size:0.6rem;">Soma dos Sorteios</div>
                    <div style="color:#f1f5f9;font-weight:700;margin-top:2px;">${analysis.arithmeticPats.sumMean} <span style="color:#64748b;font-size:0.62rem">±${analysis.arithmeticPats.sumStd}</span></div>
                    <div style="color:#94a3b8;font-size:0.6rem;">min:${analysis.arithmeticPats.sumMin} · max:${analysis.arithmeticPats.sumMax}</div>
                    <div style="margin-top:3px;font-size:0.62rem;">Tendência recente: <span style="color:${analysis.arithmeticPats.sumTrend==='Alta'?'#22C55E':analysis.arithmeticPats.sumTrend==='Baixa'?'#EF4444':'#F59E0B'}">${analysis.arithmeticPats.sumTrend}</span></div>
                </div>
                <div style="background:rgba(255,255,255,0.04);border-radius:8px;padding:8px;">
                    <div style="color:#94a3b8;font-size:0.6rem;">Faixas de Soma Mais Frequentes</div>
                    ${analysis.arithmeticPats.topBins.map(b=>`<div style="margin-top:3px;font-size:0.65rem;color:#f1f5f9;">${b.range}: <span style="color:#6366f1;font-weight:700;">${b.count}x</span></div>`).join('')}
                    <div style="color:#94a3b8;font-size:0.6rem;margin-top:3px;">Amplitude média: ${analysis.arithmeticPats.rangeAvg}</div>
                </div>
            </div>
        </div>` : ''}

        <!-- ══ OPORTUNIDADES PERDIDAS ══ -->
        ${analysis.missedOpportunities.length > 0 ? `
        <div style="background:rgba(239,68,68,0.07);border:1px solid #EF444428;border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#EF4444;text-transform:uppercase;letter-spacing:1px;margin-bottom:7px;">⚠️ OPORTUNIDADES PERDIDAS — Não estão na sua seleção</div>
            <div style="display:flex;flex-wrap:wrap;gap:5px;">
                ${analysis.missedOpportunities.slice(0,12).map(m=>{
                    const prof = analysis.behaviorProfiles[m.num];
                    return `<div title="Score:${(m.score*100).toFixed(0)}% | ${prof?.profile||''}" style="display:flex;flex-direction:column;align-items:center;gap:1px;background:rgba(239,68,68,0.15);border:1px solid #EF444440;border-radius:8px;padding:5px 7px;min-width:34px;">
                        <span style="font-size:0.65rem;">${prof?.emoji||'⊕'}</span>
                        <span style="font-size:0.82rem;font-weight:800;color:#EF4444;">${m.num}</span>
                        <span style="font-size:0.55rem;color:#F87171;">${(m.score*100).toFixed(0)}%</span>
                    </div>`;
                }).join('')}
            </div>
        </div>` : ''}

        <!-- ══ BACKTESTING ══ -->
        <div style="background:rgba(15,15,35,0.95);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;">
            <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:7px;">📈 BACKTESTING — Últimos ${analysis.backtestResult.results.length} sorteios</div>
            <div style="display:flex;flex-wrap:wrap;gap:4px;margin-bottom:6px;">
                ${analysis.backtestResult.results.map(r=>{
                    const hc=r.hits>=5?'#22C55E':r.hits>=3?'#F59E0B':r.hits>=1?'#6366f1':'#475569';
                    return `<div style="display:flex;flex-direction:column;align-items:center;background:rgba(255,255,255,0.04);border:1px solid ${hc}40;border-radius:6px;padding:3px 5px;min-width:32px;">
                        <span style="font-size:0.58rem;color:#64748b;">#${r.concurso}</span>
                        <span style="font-size:0.78rem;font-weight:800;color:${hc};">${r.hits}</span>
                    </div>`;
                }).join('')}
            </div>
            <div style="font-size:0.65rem;color:#64748b;">
                Melhor: <span style="color:#22C55E;font-weight:700;">${analysis.backtestResult.bestHit} hits</span> •
                Win rate: <span style="color:#6366f1;font-weight:700;">${analysis.backtestResult.winRate}%</span> •
                Melhoria vs acaso: <span style="color:${parseFloat(analysis.backtestResult.improvement)>=1?'#22C55E':'#EF4444'};font-weight:700;">${analysis.backtestResult.improvement}x</span>
            </div>
        </div>

        </div>`;
    },

    _card(icon, label, value, sub, color) {
        return `<div style="background:rgba(255,255,255,0.04);border:1px solid ${color}30;border-radius:8px;padding:8px;text-align:center;">
            <div style="font-size:0.6rem;color:#94a3b8;margin-bottom:2px;">${icon} ${label}</div>
            <div style="font-size:1.05rem;font-weight:900;color:${color};">${value}</div>
            <div style="font-size:0.58rem;color:#64748b;">${sub}</div>
        </div>`;
    },

    _isFibonacci(n) { return new Set([1,2,3,5,8,13,21,34,55,89]).has(n); },
    _isPrime(n) {
        if (n<2) return false; if(n===2) return true; if(n%2===0) return false;
        for (let i=3;i<=Math.sqrt(n);i+=2) if(n%i===0) return false;
        return true;
    }
};
