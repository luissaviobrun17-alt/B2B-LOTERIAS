/**
 * LOTOFACIL DUAL STRATEGY ENGINE - LDSE-V1
 * Estrategia de 2 Macro-Grupos para geracao otimizada de jogos na Lotofacil
 *
 * CONCEITO:
 *  1. Divide os 25 numeros em 2 macro-grupos (A e B)
 *     - baseado no momentum/status dos 5 grupos (LGE-V1)
 *     - possiveis splits: G1+G2 vs G3+G4+G5, G1+G2+G3 vs G4+G5, etc.
 *  2. Analisa qual distribuicao A/B foi mais frequente historicamente
 *     Ex: para split 12/13 -> jogar 7/8, 8/7, 6/9, 9/6...
 *  3. Gera N jogos respeitando a melhor distribuicao identificada
 *  4. Unifica com LGE-V1 para selecao dos numeros dentro de cada grupo
 */
var LotofacilDualStrategy = {

    DRAW: 15,
    RANGE: 25,

    GROUPS: [
        { id: 1, label: 'G1', nums: [1,2,3,4,5],      range: '01-05', color: '#EF4444' },
        { id: 2, label: 'G2', nums: [6,7,8,9,10],     range: '06-10', color: '#F97316' },
        { id: 3, label: 'G3', nums: [11,12,13,14,15], range: '11-15', color: '#EAB308' },
        { id: 4, label: 'G4', nums: [16,17,18,19,20], range: '16-20', color: '#22C55E' },
        { id: 5, label: 'G5', nums: [21,22,23,24,25], range: '21-25', color: '#6366f1' }
    ],

    CANDIDATE_SPLITS: [
        { id: 'S1', name: 'Baixo (G1+G2) x Alto (G3+G4+G5)', groupsA: [0,1],   numsSplit: '10x15' },
        { id: 'S2', name: 'Baixo (G1+G2+G3) x Alto (G4+G5)', groupsA: [0,1,2], numsSplit: '15x10' },
        { id: 'S3', name: 'Impares (G1+G3+G5) x Pares (G2+G4)', groupsA: [0,2,4], numsSplit: '15x10' },
        { id: 'S4', name: 'Quentes x Frios (dinamico)',         groupsA: null,   numsSplit: 'dinamico' }
    ],

    // -------------------------------------------------------------------------
    // ANALISE COMPLETA
    // -------------------------------------------------------------------------
    analyze: function(history) {
        var N = Math.min(300, (history || []).length);
        if (N < 5) return null;
        var self = this;

        // 1. Obter analise LGE-V1
        var lgeData = null;
        try {
            if (typeof LotofacilGroupEngine !== 'undefined') {
                lgeData = LotofacilGroupEngine.analyze(history);
            }
        } catch(e) { console.warn('[LDSE] LGE erro:', e.message); }

        var groupMomentum = this.GROUPS.map(function(g, gi) {
            if (lgeData && lgeData.groupScores && lgeData.groupScores[gi]) {
                return parseFloat(lgeData.groupScores[gi].avg5) || 3;
            }
            var cnt5 = history.slice(0, Math.min(5, N))
                .reduce(function(s, d){ return s + g.nums.filter(function(n){ return (d.numbers||[]).indexOf(n)>=0; }).length; }, 0);
            return cnt5 / Math.min(5, N);
        });

        // 2. Split dinamico
        var hotColdSplit = this._buildHotColdSplit(groupMomentum);
        var splits = this.CANDIDATE_SPLITS.map(function(s) {
            if (s.id === 'S4') {
                return { id: s.id, name: s.name, groupsA: hotColdSplit.groupsA, numsSplit: hotColdSplit.numsA + 'x' + (25 - hotColdSplit.numsA) };
            }
            return { id: s.id, name: s.name, groupsA: s.groupsA, numsSplit: s.numsSplit };
        });

        // 3. Analisar cada split
        var splitAnalysis = splits.map(function(split){ return self._analyzeSplit(split, history, N); });

        // 4. Eleger melhor split
        var bestSplit = this._electBestSplit(splitAnalysis);

        // 5. Score dos numeros
        var numScores = this._calcNumScores(history, N);

        var chosenAnalysis = null;
        for (var i = 0; i < splitAnalysis.length; i++) {
            if (splitAnalysis[i].id === bestSplit.id) { chosenAnalysis = splitAnalysis[i]; break; }
        }
        if (!chosenAnalysis) chosenAnalysis = splitAnalysis[0];

        console.log('[LDSE-V1] Melhor split: ' + bestSplit.name + ' | N=' + N);

        return {
            N: N, splits: splits, splitAnalysis: splitAnalysis,
            bestSplit: chosenAnalysis,
            lgeData: lgeData, numScores: numScores, groupMomentum: groupMomentum
        };
    },

    // -------------------------------------------------------------------------
    // GERAR N JOGOS
    // -------------------------------------------------------------------------
    generate: function(history, gameCount) {
        if (!gameCount) gameCount = 10;
        var analysis = this.analyze(history);
        if (!analysis) return { games: [], analysis: null };

        var bestSplit = analysis.bestSplit;
        var numScores = analysis.numScores;
        var games = [];
        var distPlan = this._planDistributions(bestSplit, gameCount);

        for (var i = 0; i < gameCount; i++) {
            var d = distPlan[i] || distPlan[0];
            var game = this._generateOneGame(bestSplit, d, numScores, games);
            games.push({ numbers: game, dist: d.fromA + '/' + d.fromB, split: bestSplit.name });
        }

        return { games: games, analysis: analysis, bestSplit: bestSplit, distPlan: distPlan };
    },

    // -------------------------------------------------------------------------
    // HELPERS
    // -------------------------------------------------------------------------
    _buildHotColdSplit: function(groupMomentum) {
        var self = this;
        var avg = groupMomentum.reduce(function(s,v){ return s+v; }, 0) / 5;
        var groupsA = [];
        for (var i = 0; i < 5; i++) { if (groupMomentum[i] >= avg) groupsA.push(i); }
        if (groupsA.length === 0) groupsA = [0, 1];
        if (groupsA.length === 5) groupsA = [0, 1, 2];
        var numsA = groupsA.reduce(function(s, gi){ return s + self.GROUPS[gi].nums.length; }, 0);
        var hotLabels = groupsA.map(function(gi){ return self.GROUPS[gi].label; });
        var coldLabels = [];
        for (var j = 0; j < 5; j++) { if (groupsA.indexOf(j) < 0) coldLabels.push(self.GROUPS[j].label); }
        return { groupsA: groupsA, numsA: numsA, hotLabels: hotLabels, coldLabels: coldLabels };
    },

    _analyzeSplit: function(split, history, N) {
        var self = this;
        var groupsA = split.groupsA || [0, 1];
        var groupsB = [];
        for (var k = 0; k < 5; k++) { if (groupsA.indexOf(k) < 0) groupsB.push(k); }

        var numsA = [];
        groupsA.forEach(function(gi){ numsA = numsA.concat(self.GROUPS[gi].nums); });
        var numsB = [];
        groupsB.forEach(function(gi){ numsB = numsB.concat(self.GROUPS[gi].nums); });

        var distFreq = {};
        for (var i = 0; i < N; i++) {
            var drawn = history[i].numbers || [];
            var cntA = drawn.filter(function(n){ return numsA.indexOf(n) >= 0; }).length;
            var cntB = drawn.filter(function(n){ return numsB.indexOf(n) >= 0; }).length;
            var key = cntA + '/' + cntB;
            distFreq[key] = (distFreq[key] || 0) + 1;
        }

        var distRanked = Object.keys(distFreq).map(function(dist) {
            var parts = dist.split('/');
            var a = parseInt(parts[0], 10);
            var b = parseInt(parts[1], 10);
            return { dist: dist, fromA: a, fromB: b, cnt: distFreq[dist], pct: Math.round(distFreq[dist] / N * 100) };
        }).sort(function(a, b){ return b.cnt - a.cnt; });

        var bestDist = distRanked[0] || { dist: '8/7', fromA: 8, fromB: 7, cnt: 1, pct: 100 };

        var recentDistFreq = {};
        for (var j = 0; j < Math.min(10, N); j++) {
            var dr = history[j].numbers || [];
            var cA = dr.filter(function(n){ return numsA.indexOf(n) >= 0; }).length;
            var cB = dr.filter(function(n){ return numsB.indexOf(n) >= 0; }).length;
            var rk = cA + '/' + cB;
            recentDistFreq[rk] = (recentDistFreq[rk] || 0) + 1;
        }
        var trendArr = Object.keys(recentDistFreq).sort(function(a, b){ return recentDistFreq[b] - recentDistFreq[a]; });
        var trendKey = trendArr[0] || bestDist.dist;
        var tParts = trendKey.split('/');
        var tA = parseInt(tParts[0], 10);
        var tB = parseInt(tParts[1], 10);

        var predictScore = bestDist.pct * 0.6 + (recentDistFreq[bestDist.dist] || 0) / 10 * 40;

        return {
            id: split.id, name: split.name,
            groupsA: groupsA, groupsB: groupsB, numsA: numsA, numsB: numsB,
            distRanked: distRanked.slice(0, 10),
            bestDist: bestDist,
            trendDist: { dist: trendKey, fromA: tA, fromB: tB, cnt: recentDistFreq[trendKey] || 0 },
            predictScore: predictScore,
            splitSize: numsA.length + 'x' + numsB.length
        };
    },

    _electBestSplit: function(splitAnalysis) {
        return splitAnalysis.slice().sort(function(a, b){ return b.predictScore - a.predictScore; })[0];
    },

    _calcNumScores: function(history, N) {
        var scores = {};
        for (var n = 1; n <= 25; n++) {
            var cnt3  = history.slice(0, Math.min(3, N)).filter(function(d){ return (d.numbers||[]).indexOf(n)>=0; }).length;
            var cnt5  = history.slice(0, Math.min(5, N)).filter(function(d){ return (d.numbers||[]).indexOf(n)>=0; }).length;
            var cnt10 = history.slice(0, Math.min(10, N)).filter(function(d){ return (d.numbers||[]).indexOf(n)>=0; }).length;
            var cntAll = history.slice(0, N).filter(function(d){ return (d.numbers||[]).indexOf(n)>=0; }).length;
            var delay = 0;
            for (var i = 0; i < N; i++) {
                if ((history[i].numbers || []).indexOf(n) >= 0) break;
                delay++;
            }
            var delayPress = Math.min(1, delay / (25/15 * 4));
            var freqScore = (cnt3/3)*0.35 + (cnt5/5)*0.30 + (cnt10/10)*0.20 + (cntAll/N)*0.15;
            scores[n] = {
                num: n, cnt3: cnt3, cnt5: cnt5, cnt10: cnt10, cntAll: cntAll,
                delay: delay, delayPress: delayPress,
                totalScore: Math.max(0, freqScore * 0.7 + delayPress * 0.3)
            };
        }
        return scores;
    },

    _planDistributions: function(bestSplit, gameCount) {
        var distRanked = bestSplit.distRanked || [];
        var trendDist = bestSplit.trendDist || null;
        var numsA = bestSplit.numsA || [];
        var numsB = bestSplit.numsB || [];
        var plan = [];

        var maxA = Math.min(numsA.length, 15);
        var minA = Math.max(0, 15 - numsB.length);
        var validDists = distRanked.filter(function(d){ return d.fromA >= minA && d.fromA <= maxA && d.fromA + d.fromB === 15; });

        if (validDists.length === 0) {
            var a = Math.min(maxA, Math.round(15 * numsA.length / 25));
            var b = 15 - a;
            for (var i = 0; i < gameCount; i++) plan.push({ fromA: a, fromB: b, dist: a + '/' + b });
            return plan;
        }

        if (gameCount === 1) {
            var td = null;
            if (trendDist) {
                for (var x = 0; x < validDists.length; x++) {
                    if (validDists[x].dist === trendDist.dist) { td = validDists[x]; break; }
                }
            }
            plan.push(td || validDists[0]);
            return plan;
        }

        var totalPct = validDists.reduce(function(s, d){ return s + d.pct; }, 0);
        var remaining = gameCount;
        for (var vi = 0; vi < validDists.length; vi++) {
            var d = validDists[vi];
            var count;
            if (vi === validDists.length - 1) {
                count = remaining;
            } else {
                count = Math.max(1, Math.round(gameCount * d.pct / Math.max(1, totalPct)));
                count = Math.min(count, remaining - (validDists.length - vi - 1));
            }
            count = Math.max(0, count);
            remaining -= count;
            for (var k = 0; k < count; k++) plan.push(d);
        }

        while (plan.length < gameCount) plan.push(validDists[0]);
        while (plan.length > gameCount) plan.pop();

        // Embaralhar
        for (var s = plan.length - 1; s > 0; s--) {
            var j = Math.floor(Math.random() * (s + 1));
            var tmp = plan[s]; plan[s] = plan[j]; plan[j] = tmp;
        }
        return plan;
    },

    _generateOneGame: function(bestSplit, dist, numScores, alreadyGenerated) {
        var numsA = bestSplit.numsA || [];
        var numsB = bestSplit.numsB || [];
        var fromA = dist.fromA;
        var fromB = dist.fromB;

        var usageCount = {};
        alreadyGenerated.forEach(function(g){ g.numbers.forEach(function(n){ usageCount[n] = (usageCount[n]||0)+1; }); });
        var penalty = function(n){ return (usageCount[n] || 0) * 0.08; };

        var pick = function(pool, count) {
            var avail = pool.map(function(n) {
                return { num: n, score: Math.max(0.001, ((numScores[n] && numScores[n].totalScore) || 0.1) - penalty(n)) };
            }).sort(function(a, b){ return b.score - a.score; });

            var selected = [];
            var remaining = avail.slice();
            for (var k = 0; k < count && remaining.length > 0; k++) {
                var totalW = remaining.reduce(function(s, x){ return s + x.score; }, 0);
                var rand = Math.random() * totalW;
                var chosen = remaining[0];
                for (var m = 0; m < remaining.length; m++) {
                    rand -= remaining[m].score;
                    if (rand <= 0) { chosen = remaining[m]; break; }
                }
                selected.push(chosen.num);
                remaining.splice(remaining.indexOf(chosen), 1);
            }
            return selected;
        };

        var fa = pick(numsA, fromA);
        var fb = pick(numsB, fromB);
        var combined = fa.concat(fb).sort(function(a, b){ return a - b; });

        var existing = {};
        combined.forEach(function(n){ existing[n] = true; });
        var allNums = numsA.concat(numsB);
        while (combined.length < 15) {
            var miss = allNums.filter(function(n){ return !existing[n]; })
                .sort(function(a, b){ return ((numScores[b] && numScores[b].totalScore)||0) - ((numScores[a] && numScores[a].totalScore)||0); });
            if (!miss.length) break;
            combined.push(miss[0]);
            existing[miss[0]] = true;
        }

        return combined.slice(0, 15).sort(function(a, b){ return a - b; });
    },

    // =========================================================================
    // RENDERIZACAO DO PAINEL (DOM direto - sem template literals aninhados)
    // =========================================================================
    renderPanel: function(analysis, generatedResult, container) {
        if (!analysis || !container) return;
        var bestSplit = analysis.bestSplit;
        var splitAnalysis = analysis.splitAnalysis;
        var N = analysis.N;
        var games = generatedResult ? generatedResult.games : [];
        var self = this;

        container.innerHTML = '';

        var wrap = document.createElement('div');
        wrap.style.fontFamily = "'Outfit','Inter',sans-serif";
        wrap.style.padding = '2px';

        // -- HEADER --
        var hdr = document.createElement('div');
        hdr.style.cssText = 'background:linear-gradient(135deg,rgba(147,0,137,0.25),rgba(94,0,88,0.15));border:1px solid rgba(147,0,137,0.63);border-radius:12px;padding:14px;margin-bottom:8px;';
        var hLine1 = document.createElement('div');
        hLine1.style.cssText = 'font-size:0.62rem;color:#e879f9;letter-spacing:2px;text-transform:uppercase;margin-bottom:4px;';
        hLine1.textContent = '\u26a1 LDSE-V1 \u2014 ESTRAT\u00c9GIA DUAL 2 MACRO-GRUPOS \u00b7 LOTOF\u00c1CIL';
        var hLine2 = document.createElement('div');
        hLine2.style.cssText = 'font-size:0.88rem;font-weight:800;color:#f1f5f9;';
        hLine2.textContent = 'Divis\u00e3o dos 25 n\u00fameros em 2 grupos para maximizar acertividade';
        var hLine3 = document.createElement('div');
        hLine3.style.cssText = 'font-size:0.72rem;color:#c084fc;margin-top:4px;';
        hLine3.innerHTML = N + ' sorteios analisados \u00b7 Split eleito: <strong style="color:#f0abfc;">' + bestSplit.name + '</strong>';
        hdr.appendChild(hLine1); hdr.appendChild(hLine2); hdr.appendChild(hLine3);
        wrap.appendChild(hdr);

        // -- COMPOSICAO DOS MACRO-GRUPOS --
        var mapDiv = document.createElement('div');
        mapDiv.style.cssText = 'background:rgba(15,15,35,0.96);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:8px;';
        var mapTitle = document.createElement('div');
        mapTitle.style.cssText = 'font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;';
        mapTitle.textContent = '\ud83d\uddc2 COMPOSI\u00c7\u00c3O DOS MACRO-GRUPOS';
        mapDiv.appendChild(mapTitle);

        var grid2 = document.createElement('div');
        grid2.style.cssText = 'display:grid;grid-template-columns:1fr 1fr;gap:8px;';

        function buildMacroBox(groupsArr, labelText, bgColor, borderColor, numBg, numColor) {
            var box = document.createElement('div');
            box.style.cssText = 'background:' + bgColor + ';border:2px solid ' + borderColor + ';border-radius:10px;padding:10px;';
            var boxTitle = document.createElement('div');
            boxTitle.style.cssText = 'font-size:0.65rem;color:' + numColor + ';font-weight:800;margin-bottom:6px;text-transform:uppercase;';
            boxTitle.textContent = labelText;
            box.appendChild(boxTitle);

            var tagRow = document.createElement('div');
            tagRow.style.cssText = 'display:flex;flex-wrap:wrap;gap:3px;margin-bottom:6px;';
            groupsArr.forEach(function(gi) {
                var g = self.GROUPS[gi];
                var tag = document.createElement('div');
                tag.style.cssText = 'background:' + g.color + '25;border:1px solid ' + g.color + '60;border-radius:5px;padding:3px 6px;text-align:center;';
                tag.innerHTML = '<div style="font-size:0.7rem;color:' + g.color + ';font-weight:800;">' + g.label + '</div><div style="font-size:0.55rem;color:#64748b;">' + g.range + '</div>';
                tagRow.appendChild(tag);
            });
            box.appendChild(tagRow);

            var numsArr = [];
            groupsArr.forEach(function(gi){ numsArr = numsArr.concat(self.GROUPS[gi].nums); });
            var labelsStr = groupsArr.map(function(gi){ return self.GROUPS[gi].label; }).join('+');
            var info = document.createElement('div');
            info.style.cssText = 'font-size:0.62rem;color:#94a3b8;';
            info.textContent = numsArr.length + ' n\u00fameros \u00b7 ' + labelsStr;
            box.appendChild(info);

            var numRow = document.createElement('div');
            numRow.style.cssText = 'display:flex;flex-wrap:wrap;gap:2px;margin-top:4px;';
            numsArr.forEach(function(n) {
                var sp = document.createElement('span');
                sp.style.cssText = 'background:' + numBg + ';color:' + numColor + ';border-radius:3px;padding:1px 4px;font-size:0.6rem;font-weight:700;';
                sp.textContent = String(n).padStart(2, '0');
                numRow.appendChild(sp);
            });
            box.appendChild(numRow);
            return box;
        }

        grid2.appendChild(buildMacroBox(bestSplit.groupsA, '\ud83d\udd34 Macro-Grupo A', 'rgba(147,0,137,0.12)', 'rgba(147,0,137,0.63)', 'rgba(147,0,137,0.2)', '#f0abfc'));
        grid2.appendChild(buildMacroBox(bestSplit.groupsB, '\ud83d\udd35 Macro-Grupo B', 'rgba(99,102,241,0.12)', 'rgba(99,102,241,0.63)', 'rgba(99,102,241,0.2)', '#a5b4fc'));
        mapDiv.appendChild(grid2);
        wrap.appendChild(mapDiv);

        // -- DISTRIBUICOES HISTORICAS --
        var distDiv = document.createElement('div');
        distDiv.style.cssText = 'background:rgba(15,15,35,0.96);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:8px;';
        var distTitle = document.createElement('div');
        distTitle.style.cssText = 'font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;';
        distTitle.textContent = '\ud83d\udcca DISTRIBUI\u00c7\u00d5ES HIST\u00d3RICAS - Quantos de A x Quantos de B em ' + N + ' sorteios';
        distDiv.appendChild(distTitle);

        var distGrid = document.createElement('div');
        distGrid.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px;';
        var maxPctVal = (bestSplit.distRanked && bestSplit.distRanked[0]) ? bestSplit.distRanked[0].pct : 1;
        var trendDistKey = bestSplit.trendDist ? bestSplit.trendDist.dist : '';
        (bestSplit.distRanked || []).slice(0, 12).forEach(function(d, ri) {
            var isTop = ri === 0;
            var isTrend = d.dist === trendDistKey;
            var bgC = isTop ? 'rgba(147,0,137,0.2)' : (isTrend ? 'rgba(34,197,94,0.1)' : 'rgba(255,255,255,0.04)');
            var borC = isTop ? 'rgba(147,0,137,0.56)' : (isTrend ? 'rgba(34,197,94,0.38)' : 'rgba(255,255,255,0.06)');
            var txtC = isTop ? '#f0abfc' : (isTrend ? '#86efac' : '#a5b4fc');
            var barC = isTop ? '#930089' : (isTrend ? '#22C55E' : '#6366f1');
            var card = document.createElement('div');
            card.style.cssText = 'background:' + bgC + ';border:1px solid ' + borC + ';border-radius:8px;padding:6px 10px;text-align:center;min-width:58px;';
            var distLabel = document.createElement('div');
            distLabel.style.cssText = 'font-size:0.75rem;font-weight:800;color:' + txtC + ';';
            distLabel.textContent = d.dist;
            var distCount = document.createElement('div');
            distCount.style.cssText = 'font-size:0.6rem;color:#64748b;';
            distCount.textContent = d.cnt + 'x \u00b7 ' + d.pct + '%';
            var bar = document.createElement('div');
            bar.style.cssText = 'height:3px;background:' + barC + ';opacity:' + (d.pct / Math.max(1, maxPctVal)).toFixed(2) + ';border-radius:2px;margin-top:2px;';
            card.appendChild(distLabel);
            card.appendChild(distCount);
            card.appendChild(bar);
            if (isTop) {
                var topLabel = document.createElement('div');
                topLabel.style.cssText = 'font-size:0.5rem;color:#e879f9;margin-top:1px;';
                topLabel.textContent = 'TOP';
                card.appendChild(topLabel);
            }
            if (isTrend && !isTop) {
                var trendLabel = document.createElement('div');
                trendLabel.style.cssText = 'font-size:0.5rem;color:#86efac;margin-top:1px;';
                trendLabel.textContent = 'TEND\u00caNCIA';
                card.appendChild(trendLabel);
            }
            distGrid.appendChild(card);
        });
        distDiv.appendChild(distGrid);
        var distLegend = document.createElement('div');
        distLegend.style.cssText = 'margin-top:8px;font-size:0.62rem;color:#64748b;';
        distLegend.textContent = 'Roxo = distribuicao mais frequente historica | Verde = tendencia nos ultimos 10 sorteios';
        distDiv.appendChild(distLegend);
        wrap.appendChild(distDiv);

        // -- SPLITS COMPARADOS --
        var splitsDiv = document.createElement('div');
        splitsDiv.style.cssText = 'background:rgba(15,15,35,0.96);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:12px;margin-bottom:8px;';
        var splitsTitle = document.createElement('div');
        splitsTitle.style.cssText = 'font-size:0.62rem;color:#94a3b8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;';
        splitsTitle.textContent = '\ud83c\udfc6 COMPARA\u00c7\u00c3O DOS SPLITS TESTADOS';
        splitsDiv.appendChild(splitsTitle);
        (splitAnalysis || []).forEach(function(s) {
            var isElected = s.id === bestSplit.id;
            var row = document.createElement('div');
            row.style.cssText = 'display:flex;align-items:center;gap:8px;padding:7px 10px;margin-bottom:4px;background:'
                + (isElected ? 'rgba(147,0,137,0.15)' : 'rgba(255,255,255,0.03)') + ';border:1px solid '
                + (isElected ? 'rgba(147,0,137,0.63)' : 'rgba(255,255,255,0.05)') + ';border-radius:8px;';
            var icon = document.createElement('span');
            icon.style.fontSize = '0.8rem';
            icon.textContent = isElected ? '\ud83d\udc51' : '\u27a1';
            var info2 = document.createElement('div');
            info2.style.flex = '1';
            var infoName = document.createElement('div');
            infoName.style.cssText = 'font-size:0.68rem;color:' + (isElected ? '#f0abfc' : '#f1f5f9') + ';font-weight:' + (isElected ? '800' : '500') + ';';
            infoName.textContent = s.name;
            var infoDetail = document.createElement('div');
            infoDetail.style.cssText = 'font-size:0.58rem;color:#64748b;';
            infoDetail.textContent = s.splitSize + ' - Top dist: ' + (s.bestDist ? s.bestDist.dist : '?') + ' (' + (s.bestDist ? s.bestDist.pct : '?') + '%)';
            info2.appendChild(infoName);
            info2.appendChild(infoDetail);
            var scoreDiv = document.createElement('div');
            scoreDiv.style.textAlign = 'right';
            var scoreLabel2 = document.createElement('div');
            scoreLabel2.style.cssText = 'font-size:0.6rem;color:#64748b;';
            scoreLabel2.textContent = 'Score Preditivo';
            var scoreVal = document.createElement('div');
            scoreVal.style.cssText = 'font-size:0.78rem;font-weight:800;color:' + (isElected ? '#e879f9' : '#94a3b8') + ';';
            scoreVal.textContent = s.predictScore.toFixed(1);
            scoreDiv.appendChild(scoreLabel2);
            scoreDiv.appendChild(scoreVal);
            row.appendChild(icon); row.appendChild(info2); row.appendChild(scoreDiv);
            splitsDiv.appendChild(row);
        });
        wrap.appendChild(splitsDiv);

        // -- JOGOS GERADOS --
        if (games.length > 0) {
            var gamesDiv = document.createElement('div');
            gamesDiv.style.cssText = 'background:linear-gradient(135deg,rgba(34,197,94,0.1),rgba(16,185,129,0.05));border:2px solid rgba(34,197,94,0.5);border-radius:12px;padding:14px;margin-bottom:8px;';
            var gamesTitle = document.createElement('div');
            gamesTitle.style.cssText = 'font-size:0.65rem;color:#86efac;text-transform:uppercase;letter-spacing:1px;margin-bottom:10px;';
            gamesTitle.textContent = '\ud83c\udfae ' + games.length + ' JOGO' + (games.length > 1 ? 'S' : '') + ' GERADO' + (games.length > 1 ? 'S' : '') + ' - Estrategia Dual 2G';
            gamesDiv.appendChild(gamesTitle);
            var gList = document.createElement('div');
            gList.style.cssText = 'display:flex;flex-direction:column;gap:8px;';
            games.forEach(function(g, gi) {
                var fromA = g.numbers.filter(function(n){ return (bestSplit.numsA||[]).indexOf(n)>=0; }).length;
                var fromB = g.numbers.filter(function(n){ return (bestSplit.numsB||[]).indexOf(n)>=0; }).length;
                var gRow = document.createElement('div');
                gRow.style.cssText = 'background:rgba(0,0,0,0.3);border-radius:8px;padding:8px 10px;';
                var header = document.createElement('div');
                header.style.cssText = 'display:flex;justify-content:space-between;align-items:center;margin-bottom:5px;';
                var numLabel = document.createElement('span');
                numLabel.style.cssText = 'font-size:0.62rem;color:#86efac;font-weight:700;';
                numLabel.textContent = 'Jogo ' + (gi + 1);
                var distLabel = document.createElement('span');
                distLabel.style.cssText = 'font-size:0.6rem;color:#64748b;background:rgba(255,255,255,0.06);padding:1px 6px;border-radius:4px;';
                distLabel.textContent = '\ud83d\udd34 A:' + fromA + ' \u00b7 \ud83d\udd35 B:' + fromB;
                header.appendChild(numLabel); header.appendChild(distLabel);
                gRow.appendChild(header);
                var ballRow = document.createElement('div');
                ballRow.style.cssText = 'display:flex;flex-wrap:wrap;gap:4px;';
                g.numbers.forEach(function(n) {
                    var inA = (bestSplit.numsA||[]).indexOf(n) >= 0;
                    var ball = document.createElement('div');
                    ball.style.cssText = 'width:28px;height:28px;border-radius:50%;background:' + (inA ? 'rgba(147,0,137,0.6)' : 'rgba(99,102,241,0.6)') + ';border:2px solid ' + (inA ? '#930089' : '#6366f1') + ';display:flex;align-items:center;justify-content:center;font-size:0.72rem;font-weight:800;color:#fff;';
                    ball.textContent = String(n).padStart(2, '0');
                    ballRow.appendChild(ball);
                });
                gRow.appendChild(ballRow);
                gList.appendChild(gRow);
            });
            gamesDiv.appendChild(gList);
            wrap.appendChild(gamesDiv);
        }

        // -- LEGENDA --
        var leg = document.createElement('div');
        leg.style.cssText = 'background:rgba(99,102,241,0.06);border:1px solid rgba(99,102,241,0.13);border-radius:10px;padding:10px;';
        var legTitle = document.createElement('div');
        legTitle.style.cssText = 'font-size:0.6rem;color:#a5b4fc;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;';
        legTitle.textContent = '\ud83d\udccb COMO LER ESTA AN\u00c1LISE';
        var legBody = document.createElement('div');
        legBody.style.cssText = 'font-size:0.65rem;color:#94a3b8;line-height:1.7;';
        legBody.innerHTML = '\ud83d\udd34 <strong style="color:#e879f9;">Macro-A</strong> = grupos considerados prioritarios no momento<br>'
            + '\ud83d\udd35 <strong style="color:#a5b4fc;">Macro-B</strong> = grupos de suporte / complementares<br>'
            + '\ud83d\udcca <strong style="color:#f1f5f9;">Distribuicao</strong> = quantos numeros de A/B aparecem em cada sorteio<br>'
            + '\ud83c\udfc6 O sistema testa 4 splits e escolhe o com maior poder preditivo historico';
        leg.appendChild(legTitle); leg.appendChild(legBody);
        wrap.appendChild(leg);

        container.appendChild(wrap);
    }
};
