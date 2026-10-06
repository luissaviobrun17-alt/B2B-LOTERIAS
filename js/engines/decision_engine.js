/**
 * ╔══════════════════════════════════════════════════════════════════════════╗
 * ║  DECISION ENGINE — Motor de Decisão Integrado                           ║
 * ║  Une AE-V2 (12 dimensões) + LGE-V1 (grupos) em uma decisão concreta    ║
 * ╠══════════════════════════════════════════════════════════════════════════╣
 * ║  FLUXO:                                                                  ║
 * ║  1. Recebe sugestão da IA (pool de números)                             ║
 * ║  2. Avalia cada número via AE-V2 (score individual)                     ║
 * ║  3. Calcula perfil de grupos atual vs perfil previsto (LGE-V1)          ║
 * ║  4. Identifica trocas necessárias (remover fraco, adicionar forte)      ║
 * ║  5. Entrega decisão final: pool refinado + justificativa                 ║
 * ╚══════════════════════════════════════════════════════════════════════════╝
 */
const DecisionEngine = {

    /**
     * Ponto de entrada: dado um pool de números sugeridos pela IA,
     * retorna o pool refinado com justificativa completa.
     *
     * @param {string}   gameKey      - ex: 'lotofacil'
     * @param {number[]} aiPool       - números sugeridos pela IA
     * @param {Object[]} history      - histórico de sorteios
     * @returns {Object}              - decisão final com ações e pool refinado
     */
    decide(gameKey, aiPool, history) {
        if (!aiPool || aiPool.length < 2 || !history || history.length < 3) return null;

        const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        const drawSize = game ? (game.draw || game.minBet) : 15;
        const betSize  = game ? game.minBet : drawSize;
        const min      = game ? game.range[0] : 1;
        const max      = game ? game.range[1] : 25;
        const totalRange = max - min + 1;

        console.log(`[DE-V1] 🎯 Decisão integrada: ${aiPool.length} nums | ${gameKey}`);

        // ── 1. ANÁLISE AE-V2 (score individual de todos os números) ──────────
        let aeAnalysis = null;
        try {
            if (typeof AnalysisEngine !== 'undefined') {
                aeAnalysis = AnalysisEngine.analyze(gameKey, aiPool, history);
            }
        } catch(e) { console.warn('[DE] AE erro:', e.message); }

        // ── 2. ANÁLISE LGE-V1 (grupos — só Lotofácil) ───────────────────────
        let lgeResult = null;
        try {
            if (gameKey === 'lotofacil' && typeof LotofacilGroupEngine !== 'undefined') {
                lgeResult = LotofacilGroupEngine.analyze(history);
            }
        } catch(e) { console.warn('[DE] LGE erro:', e.message); }

        // ── 3. Scores de todos os números do range ───────────────────────────
        const allScores = {};
        if (aeAnalysis && aeAnalysis.allRanked) {
            aeAnalysis.allRanked.forEach(r => { allScores[r.num] = r.score; });
        } else {
            // Fallback: frequência simples
            for (let n = min; n <= max; n++) {
                const cnt = history.slice(0, Math.min(20, history.length))
                    .filter(d => (d.numbers||[]).concat(d.numbers2||[]).includes(n)).length;
                allScores[n] = cnt / Math.min(20, history.length);
            }
        }

        // ── 4. Classificar o pool atual ──────────────────────────────────────
        const poolSet    = new Set(aiPool);
        const poolScored = aiPool.map(n => ({ num: n, score: allScores[n] || 0 }))
                                  .sort((a, b) => b.score - a.score);

        // Números FORA do pool com score alto = oportunidades perdidas
        const outsidePool = [];
        for (let n = min; n <= max; n++) {
            if (!poolSet.has(n)) outsidePool.push({ num: n, score: allScores[n] || 0 });
        }
        outsidePool.sort((a, b) => b.score - a.score);

        // Threshold: fraco = score abaixo do percentil 30 do pool
        const poolScoresSorted = poolScored.map(p => p.score).sort((a,b) => a-b);
        const weakThreshold = poolScoresSorted[Math.floor(poolScoresSorted.length * 0.30)] || 0;

        const weakInPool    = poolScored.filter(p => p.score < weakThreshold).slice(0, 5);
        const strongOutside = outsidePool.slice(0, 8); // top candidatos para entrar

        // ── 5. ANÁLISE DE GRUPOS (Lotofácil) ─────────────────────────────────
        let groupActions = [];
        let currentProfile = null, targetProfile = null;
        if (lgeResult) {
            // Perfil atual do pool
            currentProfile = LotofacilGroupEngine.GROUPS.map(g =>
                g.nums.filter(n => poolSet.has(n)).length
            );

            // Perfil previsto pelo LGE
            targetProfile = lgeResult.prediction.map(p => p.rounded);

            // Determinar ajustes de grupo necessários
            const groupDeltas = currentProfile.map((cur, gi) => ({
                gi, label: LotofacilGroupEngine.GROUPS[gi].label,
                color: LotofacilGroupEngine.GROUPS[gi].color,
                current: cur, target: targetProfile[gi],
                delta: targetProfile[gi] - cur
            }));

            // Grupos que precisam adicionar (+) ou remover (-)
            groupActions = groupDeltas.filter(g => g.delta !== 0).sort((a,b) => Math.abs(b.delta) - Math.abs(a.delta));
        }

        // ── 6. CONSTRUIR PLANO DE AÇÃO ───────────────────────────────────────
        const actions = [];
        const finalPool = [...aiPool];
        const finalSet  = new Set(finalPool);

        // Prioridade 1: ajustes de grupo (Lotofácil)
        if (groupActions.length > 0) {
            for (const ga of groupActions) {
                const group = LotofacilGroupEngine.GROUPS[ga.gi];
                if (ga.delta > 0) {
                    // Precisa ADICIONAR números deste grupo
                    const candidates = group.nums
                        .filter(n => !finalSet.has(n))
                        .map(n => ({ num: n, score: allScores[n] || 0 }))
                        .sort((a,b) => b.score - a.score);
                    for (let k = 0; k < ga.delta && candidates.length > 0; k++) {
                        const add = candidates.shift();
                        // Remover o mais fraco do pool que esteja num grupo com delta negativo
                        const toRemoveGroup = groupActions.find(g2 => g2.delta < 0 && g2.gi !== ga.gi);
                        let removed = null;
                        if (toRemoveGroup) {
                            const removeGroup = LotofacilGroupEngine.GROUPS[toRemoveGroup.gi];
                            const weakInGroup = removeGroup.nums
                                .filter(n => finalSet.has(n))
                                .map(n => ({ num: n, score: allScores[n] || 0 }))
                                .sort((a,b) => a.score - b.score);
                            if (weakInGroup.length > 0) {
                                removed = weakInGroup[0];
                                finalPool.splice(finalPool.indexOf(removed.num), 1);
                                finalSet.delete(removed.num);
                                toRemoveGroup.delta++;
                            }
                        } else if (finalPool.length >= betSize) {
                            // Remover o de menor score geral
                            const weakest = [...finalPool].sort((a,b) => (allScores[a]||0) - (allScores[b]||0))[0];
                            removed = { num: weakest, score: allScores[weakest] || 0 };
                            finalPool.splice(finalPool.indexOf(weakest), 1);
                            finalSet.delete(weakest);
                        }
                        finalPool.push(add.num);
                        finalSet.add(add.num);
                        ga.delta--;
                        actions.push({
                            type: 'GROUP_REBALANCE',
                            priority: 'alta',
                            emoji: '🔄',
                            remove: removed,
                            add,
                            reason: `${ga.label} previsto com ${ga.target} números (atual: ${ga.current})`
                        });
                    }
                }
            }
        }

        // Prioridade 2: substituir números fracos por fortes (score-based)
        const MAX_SWAPS = Math.min(3, Math.floor(aiPool.length * 0.20));
        let swapsDone = 0;
        for (const weak of weakInPool) {
            if (swapsDone >= MAX_SWAPS) break;
            if (!finalSet.has(weak.num)) continue; // já foi removido
            const candidate = strongOutside.find(o => !finalSet.has(o.num) && o.score > weak.score * 1.25);
            if (!candidate) continue;
            finalPool.splice(finalPool.indexOf(weak.num), 1);
            finalSet.delete(weak.num);
            finalPool.push(candidate.num);
            finalSet.add(candidate.num);
            actions.push({
                type: 'SCORE_SWAP',
                priority: 'média',
                emoji: '📈',
                remove: weak,
                add: candidate,
                reason: `Score ${(weak.score*100).toFixed(0)}% → ${(candidate.score*100).toFixed(0)}% (+${((candidate.score-weak.score)/Math.max(0.001,weak.score)*100).toFixed(0)}%)`
            });
            swapsDone++;
        }

        // ── 7. POOL FINAL ────────────────────────────────────────────────────
        const finalSorted = [...new Set(finalPool)].sort((a,b) => a-b);

        // Calcular delta final (diferença entre pool original e refinado)
        const originalSet = new Set(aiPool);
        const added   = finalSorted.filter(n => !originalSet.has(n));
        const removed = aiPool.filter(n => !new Set(finalSorted).has(n));

        // Score médio: antes vs depois
        const scoreOriginal = aiPool.reduce((s,n) => s + (allScores[n]||0), 0) / aiPool.length;
        const scoreFinal    = finalSorted.reduce((s,n) => s + (allScores[n]||0), 0) / finalSorted.length;
        const improvement   = scoreOriginal > 0 ? (scoreFinal - scoreOriginal) / scoreOriginal * 100 : 0;

        // Perfil de grupos final (Lotofácil)
        let finalGroupProfile = null;
        if (lgeResult) {
            finalGroupProfile = LotofacilGroupEngine.GROUPS.map((g, gi) => ({
                label: g.label, color: g.color,
                count: g.nums.filter(n => new Set(finalSorted).has(n)).length,
                target: targetProfile ? targetProfile[gi] : 3
            }));
        }

        // ── 8. CONFIANÇA DA DECISÃO ──────────────────────────────────────────
        const actionsWithClarity = actions.filter(a => a.add && a.remove).length;
        const decisionConfidence = Math.min(95, Math.round(
            60 +
            (actionsWithClarity > 0 ? 10 : 0) +
            Math.min(15, improvement) +
            (history.length > 30 ? 10 : history.length > 15 ? 5 : 0) +
            (lgeResult ? 5 : 0)
        ));

        console.log(`[DE-V1] ✅ ${actions.length} ações | Melhoria: +${improvement.toFixed(1)}% | Pool: ${finalSorted.join(',')}`);

        return {
            gameKey, original: aiPool, final: finalSorted,
            added, removed, actions,
            scoreOriginal: (scoreOriginal*100).toFixed(1),
            scoreFinal: (scoreFinal*100).toFixed(1),
            improvement: improvement.toFixed(1),
            decisionConfidence, currentProfile, targetProfile, finalGroupProfile,
            aeAnalysis, lgeResult
        };
    },

    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    // RENDERIZAÇÃO DO PAINEL DE DECISÃO
    // ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    renderDecisionPanel(decision, container) {
        if (!decision || !container) return;

        const gc = typeof GAMES !== 'undefined' && GAMES[decision.gameKey] ? GAMES[decision.gameKey].color : '#930089';
        const confColor = decision.decisionConfidence >= 75 ? '#22C55E' : decision.decisionConfidence >= 55 ? '#F59E0B' : '#EF4444';

        container.innerHTML = `<div style="font-family:'Outfit','Inter',sans-serif;">

        <!-- ══ HEADER ══ -->
        <div style="background:linear-gradient(135deg,rgba(0,80,0,0.2),rgba(0,40,0,0.1));border:1px solid #22C55E50;border-radius:14px;padding:14px;margin-bottom:10px;box-shadow:0 4px 20px rgba(0,0,0,0.4);">
            <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:10px;">
                <div>
                    <div style="font-size:0.62rem;color:#86efac;letter-spacing:2px;text-transform:uppercase;">✅ DECISÃO INTEGRADA — Como Jogar</div>
                    <div style="font-size:0.88rem;font-weight:800;color:#f1f5f9;margin-top:3px;">Pool refinado com ${decision.final.length} números</div>
                </div>
                <div style="text-align:center;background:${confColor}20;border:1px solid ${confColor}40;border-radius:10px;padding:6px 12px;">
                    <div style="font-size:0.6rem;color:${confColor};letter-spacing:1px;">CONFIANÇA</div>
                    <div style="font-size:1.2rem;font-weight:900;color:${confColor};">${decision.decisionConfidence}%</div>
                </div>
            </div>

            <!-- Score improvement -->
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:6px;">
                <div style="background:rgba(255,255,255,0.04);border-radius:8px;padding:8px;text-align:center;">
                    <div style="font-size:0.58rem;color:#94a3b8;">Score Orig.</div>
                    <div style="font-size:0.9rem;font-weight:800;color:#94a3b8;">${decision.scoreOriginal}%</div>
                </div>
                <div style="background:rgba(34,197,94,0.1);border-radius:8px;padding:8px;text-align:center;border:1px solid #22C55E30;">
                    <div style="font-size:0.58rem;color:#86efac;">Score Refinado</div>
                    <div style="font-size:0.9rem;font-weight:800;color:#22C55E;">${decision.scoreFinal}%</div>
                </div>
                <div style="background:rgba(99,102,241,0.1);border-radius:8px;padding:8px;text-align:center;border:1px solid #6366f130;">
                    <div style="font-size:0.58rem;color:#a5b4fc;">Melhoria</div>
                    <div style="font-size:0.9rem;font-weight:800;color:#6366f1;">${parseFloat(decision.improvement) >= 0 ? '+' : ''}${decision.improvement}%</div>
                </div>
            </div>
        </div>

        <!-- ══ POOL FINAL (JOGAR ESTES NÚMEROS) ══ -->
        <div style="background:linear-gradient(135deg,rgba(34,197,94,0.12),rgba(16,185,129,0.06));border:2px solid #22C55E80;border-radius:14px;padding:14px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#86efac;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                🎯 JOGUE ESTES NÚMEROS — Pool Refinado Final
            </div>
            <div style="display:flex;flex-wrap:wrap;gap:5px;">
                ${decision.final.map(n => {
                    const isNew     = decision.added.includes(n);
                    const isKept    = !isNew;
                    const score     = decision.aeAnalysis?.allRanked?.find(r => r.num === n)?.score || 0;
                    const scoreClr  = score >= 0.55 ? '#22C55E' : score >= 0.38 ? '#F59E0B' : '#94a3b8';
                    return `<div style="
                        display:flex;flex-direction:column;align-items:center;gap:2px;
                        background:${isNew ? 'rgba(34,197,94,0.25)' : 'rgba(255,255,255,0.06)'};
                        border:1px solid ${isNew ? '#22C55E' : '#ffffff25'};
                        border-radius:8px;padding:5px 7px;min-width:36px;
                        ${isNew ? 'box-shadow:0 0 8px #22C55E40;' : ''}
                    ">
                        <span style="font-size:0.58rem;color:${isNew ? '#86efac' : '#64748b'};">${isNew ? 'NOVO' : '✓'}</span>
                        <span style="font-size:0.88rem;font-weight:900;color:${isNew ? '#22C55E' : '#f1f5f9'};">${String(n).padStart(2,'0')}</span>
                    </div>`;
                }).join('')}
            </div>
            ${decision.finalGroupProfile ? `
            <div style="display:flex;gap:4px;margin-top:8px;">
                ${decision.finalGroupProfile.map(fg => {
                    const ok = fg.count === fg.target;
                    return `<div style="flex:1;text-align:center;background:${fg.color}15;border:1px solid ${fg.color}30;border-radius:6px;padding:4px;">
                        <div style="font-size:0.58rem;color:${fg.color};">${fg.label}</div>
                        <div style="font-size:0.82rem;font-weight:800;color:${ok?'#22C55E':fg.color};">${fg.count}${ok?'✓':''}</div>
                        <div style="font-size:0.52rem;color:#64748b;">alvo:${fg.target}</div>
                    </div>`;
                }).join('')}
            </div>` : ''}
        </div>

        <!-- ══ PLANO DE AÇÃO ══ -->
        ${decision.actions.length > 0 ? `
        <div style="background:rgba(15,15,35,0.96);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:10px;">
            <div style="font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">
                ⚙️ AÇÕES REALIZADAS (${decision.actions.length}) — Por que trocamos estes números
            </div>
            <div style="display:flex;flex-direction:column;gap:6px;">
                ${decision.actions.map(a => `
                <div style="display:flex;align-items:center;gap:6px;padding:7px 9px;background:rgba(255,255,255,0.03);border-radius:8px;border-left:3px solid ${a.priority==='alta'?'#EF4444':a.priority==='média'?'#F59E0B':'#6366f1'};">
                    <span style="font-size:1rem;">${a.emoji}</span>
                    <div style="flex:1;">
                        <div style="font-size:0.68rem;color:#f1f5f9;font-weight:600;">${a.reason}</div>
                        <div style="display:flex;align-items:center;gap:4px;margin-top:2px;">
                            ${a.remove ? `<span style="background:#EF444430;border:1px solid #EF444450;border-radius:5px;padding:1px 6px;font-size:0.65rem;color:#F87171;font-weight:700;">−${String(a.remove.num).padStart(2,'0')}</span>` : ''}
                            ${a.remove && a.add ? `<span style="color:#64748b;font-size:0.65rem;">→</span>` : ''}
                            ${a.add ? `<span style="background:#22C55E30;border:1px solid #22C55E50;border-radius:5px;padding:1px 6px;font-size:0.65rem;color:#86efac;font-weight:700;">+${String(a.add.num).padStart(2,'0')}</span>` : ''}
                        </div>
                    </div>
                    <span style="font-size:0.6rem;color:#64748b;padding:2px 6px;background:rgba(255,255,255,0.05);border-radius:4px;">${a.priority}</span>
                </div>`).join('')}
            </div>
        </div>` : `
        <div style="background:rgba(34,197,94,0.08);border:1px solid #22C55E30;border-radius:12px;padding:10px;margin-bottom:10px;text-align:center;">
            <div style="font-size:0.72rem;color:#86efac;">✅ Pool já está otimizado — nenhuma troca necessária</div>
        </div>`}

        <!-- ══ O QUE FOI REMOVIDO ══ -->
        ${decision.removed.length > 0 ? `
        <div style="display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:10px;">
            <div style="background:rgba(239,68,68,0.08);border:1px solid #EF444430;border-radius:10px;padding:10px;">
                <div style="font-size:0.6rem;color:#EF4444;text-transform:uppercase;margin-bottom:5px;">❌ Removidos (fracos)</div>
                <div style="display:flex;flex-wrap:wrap;gap:4px;">
                    ${decision.removed.map(n => `<span style="background:#EF444420;border:1px solid #EF444440;border-radius:5px;padding:2px 7px;font-size:0.7rem;color:#F87171;font-weight:700;">${String(n).padStart(2,'0')}</span>`).join('')}
                </div>
            </div>
            <div style="background:rgba(34,197,94,0.08);border:1px solid #22C55E30;border-radius:10px;padding:10px;">
                <div style="font-size:0.6rem;color:#22C55E;text-transform:uppercase;margin-bottom:5px;">✅ Adicionados (fortes)</div>
                <div style="display:flex;flex-wrap:wrap;gap:4px;">
                    ${decision.added.map(n => `<span style="background:#22C55E20;border:1px solid #22C55E40;border-radius:5px;padding:2px 7px;font-size:0.7rem;color:#86efac;font-weight:700;">${String(n).padStart(2,'0')}</span>`).join('')}
                </div>
            </div>
        </div>` : ''}

        <!-- ══ GUIA PRÁTICO ══ -->
        <div style="background:rgba(99,102,241,0.08);border:1px solid #6366f130;border-radius:12px;padding:12px;">
            <div style="font-size:0.62rem;color:#a5b4fc;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">📋 COMO USAR NA PRÁTICA</div>
            <div style="display:flex;flex-direction:column;gap:5px;font-size:0.68rem;color:#94a3b8;line-height:1.5;">
                <div>1️⃣ <span style="color:#f1f5f9;">Use os ${decision.final.length} números do pool refinado</span> como base fixa</div>
                <div>2️⃣ <span style="color:#f1f5f9;">Gere múltiplos jogos</span> combinando esses números em grupos de ${typeof GAMES !== 'undefined' && GAMES[decision.gameKey] ? GAMES[decision.gameKey].minBet : 15}</div>
                <div>3️⃣ <span style="color:#f1f5f9;">Mantenha a distribuição por grupos</span>${decision.finalGroupProfile ? ': ' + decision.finalGroupProfile.map(fg=>`${fg.label}×${fg.count}`).join(' · ') : ''}</div>
                <div>4️⃣ <span style="color:#f1f5f9;">Priorize os números com borda verde</span> — foram adicionados pelo motor com score maior</div>
                <div>5️⃣ <span style="color:#f1f5f9;">Revise novamente</span> após próximo sorteio para re-calibrar</div>
            </div>
        </div>

        </div>`;
    }
};
