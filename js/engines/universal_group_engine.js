/**
 * ╔══════════════════════════════════════════════════════════════════════════╗
 * ║  UNIVERSAL GROUP ENGINE — UGE-V1                                         ║
 * ║  Análise de padrões de grupos para TODAS as loterias                    ║
 * ╠══════════════════════════════════════════════════════════════════════════╣
 * ║  Estrutura de grupos por loteria:                                         ║
 * ║  Mega Sena  [1-60]:  6 grupos de 10 — esperado 1/grupo                  ║
 * ║  Lotofácil  [1-25]:  5 grupos de 5  — esperado 3/grupo                  ║
 * ║  Quina      [1-80]:  4 grupos de 20 — esperado 1.25/grupo               ║
 * ║  Dupla Sena [1-50]:  5 grupos de 10 — esperado 1.2/grupo                ║
 * ║  Lotomania  [0-99]: 10 grupos de 10 — esperado 2/grupo                  ║
 * ║  Timemania  [1-80]:  4 grupos de 20 — esperado 1.75/grupo               ║
 * ║  Dia Sorte  [1-31]:  4 grupos var.  — esperado 1.75/grupo               ║
 * ╚══════════════════════════════════════════════════════════════════════════╝
 */
const UniversalGroupEngine = {

    // ── CONFIGURAÇÃO DE GRUPOS POR LOTERIA ───────────────────────────────────
    CONFIGS: {
        megasena: {
            groups: [
                { id:1, label:'G1', nums:[1,2,3,4,5,6,7,8,9,10],         range:'01–10', color:'#22C55E' },
                { id:2, label:'G2', nums:[11,12,13,14,15,16,17,18,19,20], range:'11–20', color:'#84CC16' },
                { id:3, label:'G3', nums:[21,22,23,24,25,26,27,28,29,30], range:'21–30', color:'#EAB308' },
                { id:4, label:'G4', nums:[31,32,33,34,35,36,37,38,39,40], range:'31–40', color:'#F97316' },
                { id:5, label:'G5', nums:[41,42,43,44,45,46,47,48,49,50], range:'41–50', color:'#EF4444' },
                { id:6, label:'G6', nums:[51,52,53,54,55,56,57,58,59,60], range:'51–60', color:'#A855F7' }
            ],
            expectedPerGroup: 1.0, // 6 drawn / 6 groups of 10 from 60 = 1.0
            gridCols: 5
        },
        lotofacil: {
            // Same as LotofacilGroupEngine but handled universally
            groups: [
                { id:1, label:'G1', nums:[1,2,3,4,5],      range:'01–05', color:'#EF4444' },
                { id:2, label:'G2', nums:[6,7,8,9,10],     range:'06–10', color:'#F97316' },
                { id:3, label:'G3', nums:[11,12,13,14,15], range:'11–15', color:'#EAB308' },
                { id:4, label:'G4', nums:[16,17,18,19,20], range:'16–20', color:'#22C55E' },
                { id:5, label:'G5', nums:[21,22,23,24,25], range:'21–25', color:'#6366f1' }
            ],
            expectedPerGroup: 3.0, // 15 drawn / 5 groups of 5 from 25 = 3.0
            gridCols: 5,
            // Colunas da matriz 5×5
            cols: [
                { id:'C1', nums:[1,6,11,16,21] },
                { id:'C2', nums:[2,7,12,17,22] },
                { id:'C3', nums:[3,8,13,18,23] },
                { id:'C4', nums:[4,9,14,19,24] },
                { id:'C5', nums:[5,10,15,20,25] }
            ]
        },
        quina: {
            groups: [
                { id:1, label:'G1', nums:Array.from({length:20},(_,i)=>i+1),    range:'01–20', color:'#60A5FA' },
                { id:2, label:'G2', nums:Array.from({length:20},(_,i)=>i+21),   range:'21–40', color:'#34D399' },
                { id:3, label:'G3', nums:Array.from({length:20},(_,i)=>i+41),   range:'41–60', color:'#FBBF24' },
                { id:4, label:'G4', nums:Array.from({length:20},(_,i)=>i+61),   range:'61–80', color:'#F87171' }
            ],
            expectedPerGroup: 1.25, // 5 drawn / 4 groups of 20 from 80 = 1.25
            gridCols: 5
        },
        duplasena: {
            groups: [
                { id:1, label:'G1', nums:Array.from({length:10},(_,i)=>i+1),  range:'01–10', color:'#EF4444' },
                { id:2, label:'G2', nums:Array.from({length:10},(_,i)=>i+11), range:'11–20', color:'#F97316' },
                { id:3, label:'G3', nums:Array.from({length:10},(_,i)=>i+21), range:'21–30', color:'#EAB308' },
                { id:4, label:'G4', nums:Array.from({length:10},(_,i)=>i+31), range:'31–40', color:'#22C55E' },
                { id:5, label:'G5', nums:Array.from({length:10},(_,i)=>i+41), range:'41–50', color:'#6366f1' }
            ],
            expectedPerGroup: 1.2, // 6 drawn / 5 groups of 10 from 50 = 1.2
            gridCols: 5
        },
        lotomania: {
            // 0-99: 10 grupos de 10 (incluindo o 0)
            groups: [
                { id:1,  label:'G0',  nums:Array.from({length:10},(_,i)=>i+0),  range:'00–09', color:'#EF4444' },
                { id:2,  label:'G10', nums:Array.from({length:10},(_,i)=>i+10), range:'10–19', color:'#F97316' },
                { id:3,  label:'G20', nums:Array.from({length:10},(_,i)=>i+20), range:'20–29', color:'#EAB308' },
                { id:4,  label:'G30', nums:Array.from({length:10},(_,i)=>i+30), range:'30–39', color:'#84CC16' },
                { id:5,  label:'G40', nums:Array.from({length:10},(_,i)=>i+40), range:'40–49', color:'#22C55E' },
                { id:6,  label:'G50', nums:Array.from({length:10},(_,i)=>i+50), range:'50–59', color:'#06B6D4' },
                { id:7,  label:'G60', nums:Array.from({length:10},(_,i)=>i+60), range:'60–69', color:'#6366f1' },
                { id:8,  label:'G70', nums:Array.from({length:10},(_,i)=>i+70), range:'70–79', color:'#8B5CF6' },
                { id:9,  label:'G80', nums:Array.from({length:10},(_,i)=>i+80), range:'80–89', color:'#EC4899' },
                { id:10, label:'G90', nums:Array.from({length:10},(_,i)=>i+90), range:'90–99', color:'#94A3B8' }
            ],
            expectedPerGroup: 2.0, // 20 drawn / 10 groups of 10 from 100 = 2.0
            gridCols: 5
        },
        timemania: {
            groups: [
                { id:1, label:'G1', nums:Array.from({length:20},(_,i)=>i+1),  range:'01–20', color:'#22C55E' },
                { id:2, label:'G2', nums:Array.from({length:20},(_,i)=>i+21), range:'21–40', color:'#84CC16' },
                { id:3, label:'G3', nums:Array.from({length:20},(_,i)=>i+41), range:'41–60', color:'#EAB308' },
                { id:4, label:'G4', nums:Array.from({length:20},(_,i)=>i+61), range:'61–80', color:'#F97316' }
            ],
            expectedPerGroup: 1.75, // 7 drawn / 4 groups of 20 from 80 = 1.75
            gridCols: 5
        },
        diadesorte: {
            groups: [
                { id:1, label:'G1', nums:[1,2,3,4,5,6,7,8],     range:'01–08', color:'#F97316' },
                { id:2, label:'G2', nums:[9,10,11,12,13,14,15,16], range:'09–16', color:'#EAB308' },
                { id:3, label:'G3', nums:[17,18,19,20,21,22,23,24], range:'17–24', color:'#22C55E' },
                { id:4, label:'G4', nums:[25,26,27,28,29,30,31],  range:'25–31', color:'#6366f1' }
            ],
            expectedPerGroup: 1.75, // 7 drawn / ~4 groups from 31 ≈ 1.75
            gridCols: 4
        }
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // ANÁLISE UNIVERSAL DE GRUPOS
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    analyze(gameKey, history) {
        const config = this.CONFIGS[gameKey];
        if (!config) return null;

        const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        const drawSize = game ? (game.draw || game.minBet) : 6;
        const N = Math.min(200, (history || []).length);
        if (N < 5) return null;

        const groups = config.groups;
        const expected = config.expectedPerGroup;

        const getN = d => (d.numbers || []).concat(d.numbers2 || []);

        // ── 1. Parse perfis de sorteio ────────────────────────────────────
        const drawProfiles = [];
        for (let i = 0; i < N; i++) {
            const nums = getN(history[i]);
            const numSet = new Set(nums);
            const profile = groups.map(g => g.nums.filter(n => numSet.has(n)).length);
            const canonSig = [...profile].sort((a,b)=>b-a).join('-');
            const exactSig = profile.join('-');
            drawProfiles.push({ profile, nums, numSet, canonSig, exactSig, draw: history[i].drawNumber });
        }

        // ── 2. Frequência de perfis ────────────────────────────────────────
        const canonFreq = {};
        drawProfiles.forEach(dp => { canonFreq[dp.canonSig] = (canonFreq[dp.canonSig]||0)+1; });
        const topProfiles = Object.entries(canonFreq)
            .map(([sig,cnt]) => ({ sig, cnt, pct: Math.round(cnt/N*100) }))
            .sort((a,b) => b.cnt-a.cnt).slice(0,8);

        // ── 3. Score de grupos (multi-janela) ─────────────────────────────
        const groupScores = groups.map((g, gi) => {
            const w3  = drawProfiles.slice(0, Math.min(3,N)).reduce((s,dp)=>s+dp.profile[gi],0);
            const w5  = drawProfiles.slice(0, Math.min(5,N)).reduce((s,dp)=>s+dp.profile[gi],0);
            const w10 = drawProfiles.slice(0,Math.min(10,N)).reduce((s,dp)=>s+dp.profile[gi],0);
            const wAll = drawProfiles.reduce((s,dp)=>s+dp.profile[gi],0);

            const avg3 = w3 / Math.min(3,N);
            const avg5 = w5 / Math.min(5,N);
            const avg10 = w10 / Math.min(10,N);
            const avgAll = wAll / N;

            const momentum = avgAll > 0 ? avg5/avgAll : 1;
            const deviation = (avgAll - expected) / expected * 100;

            let status, statusEmoji;
            const ratio5 = avg5 / expected;
            if (ratio5 >= 1.5)      { status='Super-Quente'; statusEmoji='🔥🔥'; }
            else if (ratio5 >= 1.2) { status='Quente';      statusEmoji='🔥'; }
            else if (ratio5 <= 0.4) { status='Gelado';      statusEmoji='🧊'; }
            else if (ratio5 <= 0.7) { status='Frio';        statusEmoji='❄️'; }
            else if (momentum>1.2)  { status='Subindo';     statusEmoji='📈'; }
            else if (momentum<0.8)  { status='Caindo';      statusEmoji='📉'; }
            else                    { status='Estável';     statusEmoji='➡️'; }

            return { ...g, gi, w3, w5, w10, wAll,
                avg3:avg3.toFixed(2), avg5:avg5.toFixed(2), avg10:avg10.toFixed(2), avgAll:avgAll.toFixed(2),
                momentum:momentum.toFixed(2), deviation:deviation.toFixed(1),
                status, statusEmoji, expected };
        });

        // ── 4. Correlações entre grupos ────────────────────────────────────
        const corrMatrix = Array.from({length:groups.length},()=>Array(groups.length).fill(0));
        drawProfiles.forEach(dp => {
            for (let i = 0; i < groups.length; i++) {
                for (let j = 0; j < groups.length; j++) {
                    corrMatrix[i][j] += (dp.profile[i]-expected)*(dp.profile[j]-expected);
                }
            }
        });
        const corrNorm = corrMatrix.map(row=>row.map(v=>Number((v/N).toFixed(3))));

        // ── 5. Score individual por número ────────────────────────────────
        const numScores = {};
        const allNums = groups.flatMap(g => g.nums);
        for (const n of allNums) {
            const cnt5  = drawProfiles.slice(0,Math.min(5,N)).filter(dp=>dp.numSet.has(n)).length;
            const cnt10 = drawProfiles.slice(0,Math.min(10,N)).filter(dp=>dp.numSet.has(n)).length;
            const cnt20 = drawProfiles.slice(0,Math.min(20,N)).filter(dp=>dp.numSet.has(n)).length;
            const cntAll = drawProfiles.filter(dp=>dp.numSet.has(n)).length;
            let delay = 0;
            for (let i=0;i<N;i++) { if(drawProfiles[i].numSet.has(n)) break; delay++; }
            const expReturn = allNums.length / drawSize;
            const delayPress = Math.min(1, delay/(expReturn*4));
            const freqScore = (cnt5/Math.min(5,N))*0.3 + (cnt10/Math.min(10,N))*0.3 + (cnt20/Math.min(20,N))*0.2 + (cntAll/N)*0.2;
            numScores[n] = { num:n, cnt5, cnt10, cntAll, delay, freqScore, delayPress, totalScore: Math.max(0, freqScore*0.7+delayPress*0.3) };
        }

        // ── 6. Previsão do próximo perfil ─────────────────────────────────
        const prediction = this._predictProfile(drawProfiles, groupScores, corrNorm, expected);

        // ── 7. Últimos N sorteios (padrão visual) ─────────────────────────
        const recentPattern = drawProfiles.slice(0, Math.min(10,N));

        // ── 8. Detecção de anomalias (grupos super/sub-representados historicamente) ─
        const anomalies = groupScores.filter(gs => Math.abs(parseFloat(gs.deviation)) > 8);

        console.log(`[UGE-V1] ✅ ${gameKey} | ${N} sorteios | ${groups.length} grupos | Top: "${topProfiles[0]?.sig}" (${topProfiles[0]?.pct}%) | Pred: ${prediction.map(p=>p.rounded).join('-')}`);

        return { gameKey, N, groups, expected, drawSize,
            drawProfiles, topProfiles, groupScores, corrNorm,
            numScores, prediction, recentPattern, anomalies,
            config };
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // PREVISÃO DO PRÓXIMO PERFIL — genérica
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    _predictProfile(drawProfiles, groupScores, corrNorm, expected) {
        const recent5 = drawProfiles.slice(0, Math.min(5, drawProfiles.length));
        const G = groupScores.length;

        const rawPred = groupScores.map((gs, gi) => {
            const avg5 = recent5.reduce((s,dp)=>s+dp.profile[gi],0) / recent5.length;
            const mom  = parseFloat(gs.momentum);
            const avgAll = parseFloat(gs.avgAll);

            // Regressão à média esperada
            const regress = (expected - avg5) * 0.6;
            // Inércia suavizada
            const inertia = (mom - 1) * 0.15;
            // Viés histórico
            const bias = (avgAll - expected) * 0.1;
            // Correlação com último sorteio
            const last = drawProfiles[0]?.profile || groupScores.map(()=>expected);
            let corrEffect = 0;
            for (let j=0;j<G;j++) {
                if (j!==gi) corrEffect += corrNorm[j][gi]*(last[j]-expected)*0.08;
            }
            const raw = expected + regress + inertia + bias + corrEffect;
            return { group: gs.label, color: gs.color, gi, raw: Math.max(0.1, raw) };
        });

        // Normalizar para soma = drawSize total esperado
        const drawTotal = groupScores.reduce((s,gs)=>s+parseFloat(gs.expected||expected), 0);
        const factor = drawTotal / rawPred.reduce((s,p)=>s+p.raw,0);
        return rawPred.map(p => {
            const predicted = Math.max(0, p.raw * factor);
            return { ...p, predicted: Math.round(predicted*10)/10, rounded: Math.round(predicted) };
        });
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // GERAÇÃO DE NÚMEROS USANDO ANÁLISE DE GRUPOS
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    generate(gameKey, history) {
        const analysis = this.analyze(gameKey, history);
        if (!analysis) return { numbers: [], analysis: null };

        const { prediction, numScores, groups, drawSize } = analysis;
        const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        const betSize = game ? game.minBet : drawSize;
        const result = [];

        // Distribuir betSize pelos grupos seguindo a previsão (arredondamento pelo maior resto)
        const floats = prediction.map(p => p.predicted * betSize / drawSize);
        const floors = floats.map(f => Math.floor(f));
        const rem = betSize - floors.reduce((s,f)=>s+f,0);
        [...floats.map((f,i)=>({i,frac:f-floors[i]})).sort((a,b)=>b.frac-a.frac)]
            .slice(0,rem).forEach(x=>floors[x.i]++);

        for (let gi=0; gi<groups.length; gi++) {
            const want = floors[gi];
            if (want <= 0) continue;
            const pool = groups[gi].nums.map(n=>numScores[n]).filter(Boolean)
                .sort((a,b)=>b.totalScore-a.totalScore);
            const take = Math.min(want, pool.length);
            const avail = pool.slice(0, Math.min(take+2, pool.length));
            for (let k=0; k<take && avail.length>0; k++) {
                const tw = avail.reduce((s,x)=>s+Math.max(0.001,x.totalScore),0);
                let r = Math.random()*tw, chosen = avail[0];
                for (const item of avail) { r-=Math.max(0.001,item.totalScore); if(r<=0){chosen=item;break;} }
                result.push(chosen.num);
                avail.splice(avail.indexOf(chosen),1);
            }
        }

        // Ajustar para exatamente betSize
        const existing = new Set(result);
        const allNums = groups.flatMap(g=>g.nums);
        while (result.length < betSize) {
            const miss = allNums.filter(n=>!existing.has(n)).sort((a,b)=>(numScores[b]?.totalScore||0)-(numScores[a]?.totalScore||0));
            if (!miss.length) break;
            result.push(miss[0]); existing.add(miss[0]);
        }
        while (result.length > betSize) {
            const sorted = result.slice().sort((a,b)=>(numScores[a]?.totalScore||0)-(numScores[b]?.totalScore||0));
            result.splice(result.indexOf(sorted[0]),1);
        }

        return { numbers:[...new Set(result)].sort((a,b)=>a-b), analysis, groupAllocation: floors, profile: floors.join('-') };
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // PAINEL DE ANÁLISE UNIVERSAL
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    renderPanel(analysis, container, generatedResult) {
        if (!analysis || !container) return;
        const { groups, groupScores, topProfiles, corrNorm, recentPattern, prediction, numScores, N, expected, gameKey, anomalies } = analysis;
        const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        const gameColor = game ? game.color : '#6366f1';
        const G = groups.length;

        container.innerHTML = `<div style="font-family:'Outfit','Inter',sans-serif;padding:2px;">

        <!-- ══ HEADER ══ -->
        <div style="background:linear-gradient(135deg,${gameColor}25,${gameColor}10);border:1px solid ${gameColor}50;border-radius:12px;padding:12px;margin-bottom:8px;">
            <div style="font-size:0.6rem;color:${gameColor};letter-spacing:2px;text-transform:uppercase;margin-bottom:3px;">🎯 UGE-V1 — ANÁLISE DE GRUPOS · ${game?game.name:gameKey.toUpperCase()}</div>
            <div style="font-size:0.85rem;font-weight:800;color:#f1f5f9;">${G} grupos · ${N} sorteios · esperado ${expected.toFixed(1)}/grupo</div>
            ${generatedResult ? `<div style="margin-top:5px;font-size:0.7rem;color:${gameColor};">Perfil gerado: <b>${generatedResult.profile}</b> → ${generatedResult.numbers.join(' · ')}</div>` : ''}
        </div>

        <!-- ══ STATUS DOS GRUPOS ══ -->
        <div style="background:rgba(15,15,35,0.96);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:10px;margin-bottom:8px;">
            <div style="font-size:0.58rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">📊 STATUS — contribuição real vs esperado (${expected.toFixed(1)})</div>
            ${groupScores.map(gs => {
                const r = parseFloat(gs.avg5)/expected;
                const barW = Math.min(100, Math.round(r*50));
                const c = r>=1.3?'#22C55E':r>=1.0?'#84CC16':r>=0.7?'#F59E0B':'#EF4444';
                return `<div style="display:flex;align-items:center;gap:6px;padding:5px 0;border-bottom:1px solid rgba(255,255,255,0.04);">
                    <span style="font-size:0.75rem;">${gs.statusEmoji}</span>
                    <div style="min-width:32px;font-size:0.68rem;font-weight:800;color:${gs.color};">${gs.label}</div>
                    <div style="font-size:0.6rem;color:#64748b;min-width:52px;">${gs.range}</div>
                    <div style="flex:1;height:5px;background:rgba(255,255,255,0.06);border-radius:3px;">
                        <div style="height:100%;width:${barW}%;background:${c};border-radius:3px;position:relative;">
                            <div style="position:absolute;right:-1px;top:-3px;width:2px;height:11px;background:rgba(255,255,255,0.3);border-radius:1px;"></div>
                        </div>
                    </div>
                    <div style="text-align:right;min-width:90px;font-size:0.62rem;">
                        <span style="color:${c};font-weight:700;">avg5:${gs.avg5}</span>
                        <span style="color:#475569;"> | geral:${gs.avgAll}</span>
                    </div>
                    <div style="min-width:40px;text-align:right;">
                        <div style="font-size:0.58rem;color:#64748b;">prev</div>
                        <div style="font-size:0.7rem;font-weight:800;color:${gs.color};">${prediction[gs.gi]?.predicted.toFixed(1)}</div>
                    </div>
                </div>`;
            }).join('')}
        </div>

        <!-- ══ PERFIS MAIS FREQUENTES ══ -->
        <div style="background:rgba(15,15,35,0.96);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:10px;margin-bottom:8px;">
            <div style="font-size:0.58rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">📐 TOP PERFIS DE DISTRIBUIÇÃO (últimos ${N} sorteios)</div>
            <div style="display:flex;flex-wrap:wrap;gap:4px;">
                ${topProfiles.map((p,ri) => `
                <div style="background:${ri===0?gameColor+'20':'rgba(255,255,255,0.04)'};border:1px solid ${ri===0?gameColor+'60':'rgba(255,255,255,0.08)'};border-radius:7px;padding:5px 8px;text-align:center;">
                    <div style="font-size:0.7rem;font-weight:800;color:${ri===0?gameColor:'#a5b4fc'};">${p.sig}</div>
                    <div style="font-size:0.58rem;color:#64748b;">${p.cnt}× · ${p.pct}%</div>
                    <div style="height:2px;background:${ri===0?gameColor:'#6366f1'};opacity:${p.pct/topProfiles[0].pct};border-radius:1px;margin-top:2px;"></div>
                </div>`).join('')}
            </div>
        </div>

        <!-- ══ PREVISÃO ══ -->
        <div style="background:linear-gradient(135deg,rgba(99,102,241,0.1),rgba(139,92,246,0.06));border:1px solid #6366f120;border-radius:10px;padding:10px;margin-bottom:8px;">
            <div style="font-size:0.58rem;color:#a5b4fc;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">🔮 PREVISÃO DO PRÓXIMO SORTEIO — perfil esperado</div>
            <div style="display:flex;flex-wrap:wrap;gap:5px;justify-content:center;">
                ${prediction.map(p => `
                <div style="text-align:center;background:${p.color}15;border:1px solid ${p.color}40;border-radius:7px;padding:5px 8px;min-width:38px;">
                    <div style="font-size:0.58rem;color:#64748b;">${groups[p.gi]?.label||'G'+p.gi}</div>
                    <div style="font-size:1rem;font-weight:900;color:${p.color};">${p.predicted.toFixed(1)}</div>
                    <div style="font-size:0.55rem;color:${p.predicted>expected?'#22C55E':p.predicted<expected?'#EF4444':'#94a3b8'};">${p.predicted>expected?'↑':p.predicted<expected?'↓':'='}</div>
                </div>`).join('')}
            </div>
            <div style="text-align:center;margin-top:5px;font-size:0.65rem;color:#64748b;">Perfil: <span style="color:#a5b4fc;font-weight:700;">${prediction.map(p=>p.rounded).join('-')}</span></div>
        </div>

        <!-- ══ ANOMALIAS ══ -->
        ${anomalies.length > 0 ? `
        <div style="background:rgba(239,68,68,0.08);border:1px solid #EF444430;border-radius:10px;padding:9px;margin-bottom:8px;">
            <div style="font-size:0.58rem;color:#F87171;text-transform:uppercase;letter-spacing:1px;margin-bottom:5px;">⚠️ ANOMALIAS DETECTADAS — viés estatístico</div>
            ${anomalies.map(a => `
            <div style="font-size:0.68rem;color:#fca5a5;margin-bottom:2px;">
                <span style="color:${a.color};font-weight:700;">${a.label} (${a.range})</span>:
                desvio histórico ${parseFloat(a.deviation)>0?'+':''}${a.deviation}% vs esperado
                — ${parseFloat(a.deviation)>0?'super':'sub'}-representado
            </div>`).join('')}
        </div>` : ''}

        <!-- ══ ÚLTIMOS 10 SORTEIOS ══ -->
        <div style="background:rgba(15,15,35,0.96);border:1px solid rgba(255,255,255,0.07);border-radius:10px;padding:10px;">
            <div style="font-size:0.58rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:5px;">📋 HISTÓRICO RECENTE — perfil por grupo</div>
            ${recentPattern.slice(0,8).map(rp => {
                return `<div style="display:flex;align-items:center;gap:3px;margin-bottom:2px;">
                    <span style="font-size:0.58rem;color:#475569;min-width:40px;">#${rp.draw||'?'}</span>
                    ${rp.profile.map((v,gi) => `<div style="
                        min-width:18px;text-align:center;padding:2px 3px;border-radius:3px;
                        background:${groups[gi].color}${v>=Math.ceil(expected*1.4)?'50':v>=expected?'28':'15'};
                        font-size:0.62rem;font-weight:800;color:${groups[gi].color};
                    ">${v}</div>`).join('')}
                    <span style="font-size:0.55rem;color:#334155;margin-left:3px;">${rp.exactSig}</span>
                </div>`;
            }).join('')}
        </div>

        </div>`;
    }
};
