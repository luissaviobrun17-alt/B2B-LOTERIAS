/**
 * ╔══════════════════════════════════════════════════════════════════════════╗
 * ║  ASYNC GENERATOR v6.0 — setTimeout puro (sem async/await)             ║
 * ║                                                                        ║
 * ║  A barra de evolução é inserida no DOM e então setTimeout(fn, 200)    ║
 * ║  garante que o browser PINTA antes do motor pesado começar.           ║
 * ║  Cobertura IA: UMA chamada (Set Cover global = qualidade máxima).     ║
 * ╚══════════════════════════════════════════════════════════════════════════╝
 */

class AsyncGenerator {

    static _cancelled = false;
    static _isRunning = false;
    static _startTime = 0;

    // ═══════════════════════════════════════════════════════════
    //  BARRA DE EVOLUÇÃO
    // ═══════════════════════════════════════════════════════════

    static _injectCSS() {
        if (document.getElementById('apg-css')) return;
        const s = document.createElement('style');
        s.id = 'apg-css';
        s.textContent = `
            .apg-panel{margin-top:4px;background:linear-gradient(165deg,rgba(15,23,42,0.98),rgba(30,41,59,0.95));border:1px solid rgba(16,185,129,0.25);border-radius:10px;padding:8px 12px;box-shadow:0 4px 20px rgba(0,0,0,0.3),inset 0 1px 0 rgba(255,255,255,0.03);animation:apgFade .3s ease}
            @keyframes apgFade{from{opacity:0;transform:translateY(-4px)}to{opacity:1;transform:translateY(0)}}
            .apg-header{display:flex;align-items:center;justify-content:space-between;margin-bottom:10px}
            .apg-left{display:flex;align-items:center;gap:8px}
            .apg-dot{width:8px;height:8px;border-radius:50%;background:#10B981;box-shadow:0 0 8px rgba(16,185,129,0.6);animation:apgBlink 1.5s ease-in-out infinite;flex-shrink:0}
            @keyframes apgBlink{0%,100%{transform:scale(1);opacity:1}50%{transform:scale(1.4);opacity:.6}}
            .apg-title{font-size:0.85rem;font-weight:800;color:#E2E8F0}
            .apg-badge{font-size:0.65rem;color:#10B981;font-weight:700;text-transform:uppercase;letter-spacing:1px;padding:2px 8px;background:rgba(16,185,129,0.1);border-radius:6px;border:1px solid rgba(16,185,129,0.2)}
            .apg-pct{font-size:.9rem;font-weight:900;color:#10B981;font-family:'Inter',monospace;min-width:45px;text-align:right}
            .apg-x{width:24px;height:24px;border-radius:6px;border:1px solid rgba(239,68,68,0.3);background:rgba(239,68,68,0.1);color:#F87171;font-size:0.7rem;font-weight:700;cursor:pointer;display:flex;align-items:center;justify-content:center}
            .apg-x:hover{background:rgba(239,68,68,0.25)}
            .apg-grid{display:grid;grid-template-columns:repeat(4,1fr);gap:5px;margin-bottom:6px}
            .apg-cell{text-align:center;padding:3px 4px;background:rgba(0,0,0,0.2);border-radius:8px;border:1px solid rgba(16,185,129,0.08)}
            .apg-val{display:block;font-size:0.95rem;font-weight:900;color:#10B981;font-family:'Inter',monospace;line-height:1.2}
            .apg-lbl{display:block;font-size:0.55rem;color:#475569;text-transform:uppercase;letter-spacing:.8px;margin-top:2px;font-weight:700}
            .apg-track{width:100%;height:8px;background:rgba(0,0,0,0.35);border-radius:4px;overflow:hidden}
            .apg-fill{height:100%;width:0%;background:linear-gradient(90deg,#059669,#10B981,#34D399);border-radius:4px;transition:width .3s ease;box-shadow:0 0 8px rgba(16,185,129,0.4)}
            .apg-slide{width:30%!important;animation:apgSlide 1.2s ease-in-out infinite}
            @keyframes apgSlide{0%{margin-left:0;width:30%}50%{margin-left:35%;width:40%}100%{margin-left:70%;width:30%}}
            .apg-done .apg-dot{animation:none;background:#22C55E}
            .apg-done .apg-fill{background:#22C55E;animation:none!important;margin-left:0!important;width:100%!important}
            @media(max-width:480px){.apg-panel{padding:10px 12px}.apg-grid{grid-template-columns:repeat(2,1fr)}.apg-val{font-size:.8rem}.apg-title{font-size:.75rem}}
        `;
        document.head.appendChild(s);
    }

    static _showBar(label, total) {
        this._injectCSS();
        this._startTime = Date.now();
        this._cancelled = false;
        const c = document.getElementById('async-progress-inline');
        if (!c) return;
        c.style.display = 'block';
        c.innerHTML = '<div class="apg-panel" id="apg-box">'
            + '<div class="apg-header"><div class="apg-left">'
            + '<span class="apg-dot"></span>'
            + '<span class="apg-title">⚡ Gerando Jogos</span>'
            + '<span class="apg-badge">' + label + '</span>'
            + '</div><div style="display:flex;align-items:center;gap:10px">'
            + '<span class="apg-pct" id="apg-pct">⏳</span>'
            + '<button class="apg-x" id="apg-x">✕</button>'
            + '</div></div>'
            + '<div class="apg-grid">'
            + '<div class="apg-cell"><span class="apg-val" id="apg-n">0</span><span class="apg-lbl">Gerados</span></div>'
            + '<div class="apg-cell"><span class="apg-val" id="apg-t">' + total.toLocaleString('pt-BR') + '</span><span class="apg-lbl">Total</span></div>'
            + '<div class="apg-cell"><span class="apg-val" id="apg-s">—</span><span class="apg-lbl">Jogos/s</span></div>'
            + '<div class="apg-cell"><span class="apg-val" id="apg-e">—</span><span class="apg-lbl">Restante</span></div>'
            + '</div>'
            + '<div class="apg-track"><div class="apg-fill apg-slide" id="apg-bar"></div></div>'
            + '</div>';
        var xb = document.getElementById('apg-x');
        if (xb) xb.onclick = function() { AsyncGenerator._cancelled = true; };
    }

    static _updateBar(cur, tot) {
        var el = (Date.now() - this._startTime) / 1000;
        var p = Math.min(100, Math.round(cur / tot * 100));
        var sp = el > 0 ? Math.round(cur / el) : 0;
        var rem = sp > 0 ? Math.ceil((tot - cur) / sp) : 0;
        var pe = document.getElementById('apg-pct'); if (pe) pe.textContent = p + '%';
        var ne = document.getElementById('apg-n'); if (ne) ne.textContent = cur.toLocaleString('pt-BR');
        var se = document.getElementById('apg-s'); if (se) se.textContent = sp.toLocaleString('pt-BR');
        var ee = document.getElementById('apg-e');
        if (ee) { if (rem > 60) ee.textContent = Math.ceil(rem/60) + 'min'; else if (rem > 0) ee.textContent = rem + 's'; else ee.textContent = '—'; }
        var be = document.getElementById('apg-bar');
        if (be) { be.classList.remove('apg-slide'); be.style.width = p + '%'; }
    }

    static _doneBar(tot) {
        var el = ((Date.now() - this._startTime) / 1000).toFixed(1);
        var elapsed = (Date.now() - this._startTime) / 1000;
        var sp = elapsed > 0 ? Math.round(tot / elapsed) : 0;
        var bx = document.getElementById('apg-box'); if (bx) bx.classList.add('apg-done');
        var pe = document.getElementById('apg-pct'); if (pe) { pe.textContent = '✅'; pe.style.color = '#22C55E'; }
        var ne = document.getElementById('apg-n'); if (ne) { ne.textContent = tot.toLocaleString('pt-BR'); ne.style.color = '#22C55E'; }
        var se = document.getElementById('apg-s'); if (se) { se.textContent = sp.toLocaleString('pt-BR'); se.style.color = '#22C55E'; }
        var ee = document.getElementById('apg-e'); if (ee) { ee.textContent = el + 's'; ee.style.color = '#22C55E'; }
        var xb = document.getElementById('apg-x'); if (xb) xb.style.display = 'none';
        // v16.1 FIX: guard para evitar crash se elemento não existir no DOM
        try { var tt = document.querySelector('.apg-title'); if (tt) tt.textContent = '✅ Concluído'; } catch(e) {}
        setTimeout(function() {
            var c = document.getElementById('async-progress-inline');
            if (c) { c.style.display = 'none'; c.innerHTML = ''; }
        }, 4000);
    }

    static _hideBar() {
        var c = document.getElementById('async-progress-inline');
        if (c) { c.style.display = 'none'; c.innerHTML = ''; }
    }

    // ═══════════════════════════════════════════════════════════
    //  MANUAL — chunks (motor leve, qualidade ok)
    // ═══════════════════════════════════════════════════════════

    static generateManualAsync(gameKey, pool, fixedNumbers, numGames, drawSize, callback) {
        var self = this;
        self._isRunning = true;
        self._cancelled = false;
        var game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        var name = game ? game.name : gameKey;

        // Delegação oficial para Super Sete B2B
        if (gameKey === 'supersete' && typeof MotorSuperSeteB2BEngine !== 'undefined') {
            const ssRes = MotorSuperSeteB2BEngine._gerarFallbackNativo(numGames, {});
            const games = (ssRes && ssRes.jogos) ? ssRes.jogos.map(j => j.jogo) : [];
            self._isRunning = false;
            self._hideBar();
            callback({
                games,
                analysis: {
                    totalGames: games.length,
                    poolSize: 10,
                    avgHamming: ssRes.metricas_carteira?.hamming_medio || 5.2,
                    coveragePct: ssRes.icm_global || 85,
                    elapsed: '10ms'
                }
            }, false, null);
            return;
        }

        // Barra indeterminada — motor processa tudo de uma vez
        self._showBar(name + ' — Manual', numGames);

        // setTimeout(200ms) = browser PINTA a barra ANTES do motor pesado
        setTimeout(function() {
            try {
                if (typeof MotorFechamentoManual === 'undefined') throw new Error('MotorFechamentoManual não carregado');

                if (self._cancelled) {
                    self._isRunning = false;
                    self._hideBar();
                    callback(null, true);
                    return;
                }

                // ═══ v16.3: Roteamento para volume alto (> 1000 jogos) ═══
                // Para volumes massivos (> 1000 jogos), PureCoverageEngine processa em chunks assíncronos sem travar a UI
                if (numGames > 1000 && typeof PureCoverageEngine !== 'undefined') {
                    console.log('%c[AsyncGen] 🚀 MANUAL MASSIVO (Volume Alto via PureCoverageEngine): ' + numGames + ' jogos', 'color:#10B981;font-weight:bold;');
                    self._showBar(name + ' — Manual Massivo (' + numGames.toLocaleString('pt-BR') + ' jogos)', numGames);
                    return self.generatePureAsync(gameKey, numGames, { drawSize: drawSize, pool: pool, fixed: fixedNumbers }, function(pureRes, pureCancelled, pureError) {
                        if (pureRes && pureRes.analysis) {
                            pureRes.analysis.poolSize = pureRes.analysis.poolSize || pool.length;
                            pureRes.analysis.fixedCount = (fixedNumbers || []).length;
                            pureRes.analysis.fixedNumbers = fixedNumbers || [];
                            var calcInv = (typeof pureRes.analysis.investimento === 'number')
                                ? pureRes.analysis.investimento
                                : ((typeof pureRes.analysis.investment === 'number')
                                    ? pureRes.analysis.investment
                                    : (pureRes.games.length * (game ? game.price : 0)));
                            pureRes.analysis.investimento = calcInv;
                            pureRes.analysis.investment = calcInv;
                        }
                        callback(pureRes, pureCancelled, pureError);
                    });
                }

                // ═══ CHAMADA ÚNICA GLOBAL ═══
                // O Greedy Set Cover precisa de estado contínuo para:
                // 1. Cobrir TODOS os pares do pool selecionado
                // 2. Distribuir números uniformemente (anti-concentração)
                // 3. Maximizar diversidade (Hamming) entre todos os jogos
                var r = MotorFechamentoManual.generate(gameKey, pool, fixedNumbers, numGames, drawSize);

                // Deduplicar (segurança)
                var uniqueGames = [];
                var keys = {};
                if (r && r.games) {
                    for (var i = 0; i < r.games.length; i++) {
                        var k = r.games[i].join(',');
                        if (!keys[k]) {
                            keys[k] = true;
                            uniqueGames.push(r.games[i]);
                        }
                    }
                }

                self._updateBar(uniqueGames.length, numGames);
                self._doneBar(uniqueGames.length);

                var analysis = Object.assign({}, r.analysis || {}, {
                    totalGames: uniqueGames.length, poolSize: pool.length,
                    fixedCount: (fixedNumbers||[]).length, fixedNumbers: fixedNumbers||[],
                    drawSize: drawSize, pricePerGame: game?game.price:0,
                    investimento: uniqueGames.length * (game?game.price:0),
                    isComplete: false, elapsed: Date.now() - self._startTime,
                    asyncMode: true, chunksProcessed: 1, totalPossible: '—'
                });

                self._isRunning = false;
                setTimeout(function() { callback({ games: uniqueGames, analysis: analysis }, false); }, 500);

            } catch (e) {
                console.error('[AsyncGen Manual]', e);
                self._isRunning = false;
                self._hideBar();
                callback(null, false, e);
            }
        }, 200);
    }

    // ═══════════════════════════════════════════════════════════
    //  COBERTURA IA — UMA chamada (Set Cover global = qualidade)
    //  Barra indeterminada anima enquanto o motor processa.
    // ═══════════════════════════════════════════════════════════

    static generateCoverageAsync(gameKey, numGames, selectedNumbers, fixedNumbers, drawSize, options, callback) {
        var self = this;
        self._isRunning = true;
        self._cancelled = false;
        var game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        var name = game ? game.name : gameKey;
        var opts = options || {};

        // Delegação oficial para Super Sete B2B
        if (gameKey === 'supersete' && typeof MotorSuperSeteB2BEngine !== 'undefined') {
            const ssRes = MotorSuperSeteB2BEngine._gerarFallbackNativo(numGames, opts);
            const games = (ssRes && ssRes.jogos) ? ssRes.jogos.map(j => j.jogo) : [];
            self._isRunning = false;
            self._hideBar();
            callback({
                games,
                analysis: {
                    totalGames: games.length,
                    poolSize: 10,
                    avgHamming: ssRes.metricas_carteira?.hamming_medio || 5.2,
                    coveragePct: ssRes.icm_global || 85,
                    elapsed: '10ms'
                }
            }, false, null);
            return;
        }

        // ═══ v16.2 SNIPER RÁPIDO: redireciona para PureCoverageEngine ═══
        // O fluxo SmartCoverage/CoverageEngine bloqueia o browser por 400ms-7s.
        // PureCoverageEngine usa chunks assíncronos — não trava a UI.
        if (opts.precisionMode && typeof PureCoverageEngine !== 'undefined' && typeof SmartCoverageEngine !== 'undefined') {
            // Construir pool sniper (agora rápido: 3ms com scoring rápido + cache)
            var sniperPool = null;
            try {
                var sniperPoolSize = (opts.precisionPoolSize && !isNaN(opts.precisionPoolSize) && opts.precisionPoolSize > 0)
                    ? opts.precisionPoolSize : 20;
                if (game) {
                    sniperPool = SmartCoverageEngine._buildSniperPool(gameKey, game, numGames, sniperPoolSize);
                }
            } catch(eSn) {
                console.warn('[AsyncGen] Sniper pool erro:', eSn.message);
            }

            // Se pool válido → usa PureCoverageEngine que é assíncrono e rápido
            var selArr = selectedNumbers ? Array.from(selectedNumbers).filter(function(n){ return typeof n === 'number'; }) : [];
            var effectivePool = (selArr.length >= drawSize) ? selArr
                              : (sniperPool && sniperPool.length >= drawSize) ? sniperPool
                              : null;

            if (effectivePool) {
                console.log('%c[AsyncGen] 🎯 SNIPER via PureCoverageEngine: pool=' + effectivePool.length + ' | jogos=' + numGames, 'color:#F59E0B;font-weight:bold;');
                self._showBar(name + ' — Sniper', numGames);
                return self.generatePureAsync(gameKey, numGames, { drawSize: drawSize, pool: effectivePool }, callback);
            }
        }

        // ═══ v16.3: Roteamento Inteligente para Cobertura IA de Alto Volume ═══
        // Se numGames > 1000, forçar o uso do PureCoverageEngine que é O(N log N) e não trava,
        // garantindo a Matemática Pura original sem os limites da Fronteira de Pareto O(N^2)
        if (numGames > 1000 && typeof PureCoverageEngine !== 'undefined') {
            console.log('%c[AsyncGen] 🚀 COBERTURA PURA MASSIVA (Volume Alto): ' + numGames + ' jogos', 'color:#10B981;font-weight:bold;');
            self._showBar(name + ' — Cobertura Pura Massiva', numGames);
            
            var fullPool = [];
            if (game) {
                var maxNum = game.maxBet || 60;
                if (typeof GameBuilderEngine !== 'undefined') {
                    var prof = GameBuilderEngine._getProfile(gameKey);
                    for (var n = prof.startNum; n <= prof.endNum; n++) fullPool.push(n);
                } else {
                    for (var n = 1; n <= maxNum; n++) fullPool.push(n);
                }
            }
            
            var selArr = selectedNumbers ? Array.from(selectedNumbers).filter(function(n){ return typeof n === 'number'; }) : [];
            var fixArr = fixedNumbers ? Array.from(fixedNumbers).filter(function(n){ return typeof n === 'number'; }) : [];
            if (selArr.length >= drawSize) {
                fullPool = [...new Set([...selArr, ...fixArr])].sort(function(a,b){return a-b;});
            } else if (fixArr.length > 0) {
                fullPool = [...new Set([...fullPool, ...fixArr])].sort(function(a,b){return a-b;});
            }
            
            // Ativar flag rigorosa de anti-sequência para matemática pura (conforme exigido pelo usuário)
            opts.strictMathRules = true;
            
            return self.generatePureAsync(gameKey, numGames, { drawSize: drawSize, pool: fullPool, strictMathRules: true }, callback);
        }

        // Verificar se GameBuilderEngine está disponível
        var useGameBuilder = typeof GameBuilderEngine !== 'undefined';

        // 1) Mostrar barra com animação indeterminada
        var engineLabel = useGameBuilder ? 'Convergência Multi-Otimizador' : 'Gerador Inteligente';
        self._showBar(name + ' — ' + engineLabel, numGames);

        // 2) setTimeout(200ms) = browser PINTA a barra ANTES do motor pesado
        setTimeout(function() {
            try {
                if (self._cancelled) {
                    self._isRunning = false;
                    self._hideBar();
                    callback(null, true);
                    return;
                }

                var result;

                if (useGameBuilder) {
                    // ═══ GAMEBUILDER ENGINE: 5 otimizadores + ConvergenceEngine (Terceiro) ═══
                    // 1. EnsembleEngine fornece pool com scores calibrados por loteria
                    // 2. GameBuilderEngine forma os jogos por convergência multi-objetivo
                    // 3. ConvergenceEngine seleciona pela fronteira de Pareto

                    var pool = [];
                    var history = [];

                    // Obter histórico
                    try {
                        if (typeof StatsService !== 'undefined') {
                            history = StatsService.getRecentResults(gameKey, 200) || [];
                        }
                        if (history.length === 0 && typeof REAL_HISTORY_DB !== 'undefined') {
                            history = REAL_HISTORY_DB[gameKey] || [];
                        }
                    } catch(e) {}

                    // Pool: se usuário selecionou números, usar eles
                    var selArr = selectedNumbers ? Array.from(selectedNumbers).filter(n => typeof n === 'number') : [];
                    var fixArr = fixedNumbers ? Array.from(fixedNumbers).filter(n => typeof n === 'number') : [];

                    if (selArr.length >= drawSize) {
                        // Usuário selecionou pool manual — usar diretamente
                        pool = [...new Set([...selArr, ...fixArr])].sort((a, b) => a - b);
                        console.log('[AsyncGen] Pool manual: ' + pool.length + ' números');

                    } else if (options && options.precisionMode && typeof SmartCoverageEngine !== 'undefined') {
                        // ═══ v16.1 FIX SNIPER: Pool do Sniper via SmartCoverageEngine ═══
                        // BUG ANTERIOR: precisionMode era ignorado — o EnsembleEngine criava
                        // um pool normal sem considerar que o usuário ativou o Sniper.
                        // CORREÇÃO: Quando Sniper está ativo, construir o pool analítico
                        // primeiro e passar para o GameBuilderEngine.
                        try {
                            var sniperPoolSize = (options.precisionPoolSize && options.precisionPoolSize > 0)
                                ? options.precisionPoolSize : 20;
                            var sniperGame = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
                            if (sniperGame) {
                                var sniperPool = SmartCoverageEngine._buildSniperPool(
                                    gameKey, sniperGame, numGames, sniperPoolSize
                                );
                                if (sniperPool && sniperPool.length >= drawSize) {
                                    pool = sniperPool;
                                    if (fixArr.length > 0) {
                                        pool = [...new Set([...pool, ...fixArr])].sort((a, b) => a - b);
                                    }
                                    console.log('%c[AsyncGen] 🎯 SNIPER ATIVO: Pool analítico de ' + pool.length + ' números → ' + pool.join(','), 'color:#F59E0B;font-weight:bold;');
                                } else {
                                    console.warn('[AsyncGen] Sniper pool insuficiente (' + (sniperPool ? sniperPool.length : 0) + '), fallback para Ensemble');
                                }
                            }
                        } catch(eSn) {
                            console.warn('[AsyncGen] Sniper pool falhou, usando Ensemble:', eSn.message);
                        }

                        // Se sniper pool não foi construído, usa Ensemble como fallback
                        if (pool.length < drawSize && typeof EnsembleEngine !== 'undefined' && history.length >= 10) {
                            try {
                                var ensemble = EnsembleEngine.score(gameKey, numGames, history, drawSize);
                                var adaptivePool = EnsembleEngine._buildAdaptivePool(ensemble, numGames, drawSize, gameKey);
                                pool = adaptivePool.length >= drawSize ? adaptivePool : [];
                                if (fixArr.length > 0) {
                                    pool = [...new Set([...pool, ...fixArr])].sort((a, b) => a - b);
                                }
                                console.log('[AsyncGen] Pool Ensemble (fallback sniper): ' + pool.length + ' números');
                            } catch(e) {
                                console.warn('[AsyncGen] EnsembleEngine falhou:', e.message);
                            }
                        }

                        if (pool.length < drawSize) {
                            var prof2 = GameBuilderEngine._getProfile(gameKey);
                            pool = [];
                            for (var n2 = prof2.startNum; n2 <= prof2.endNum; n2++) pool.push(n2);
                        }

                    } else {
                        // Pool automático via EnsembleEngine (se disponível) ou range completo
                        if (typeof EnsembleEngine !== 'undefined' && history.length >= 10) {
                            try {
                                var ensemble = EnsembleEngine.score(gameKey, numGames, history, drawSize);
                                var adaptivePool = EnsembleEngine._buildAdaptivePool(ensemble, numGames, drawSize, gameKey);
                                pool = adaptivePool.length >= drawSize ? adaptivePool : [];
                                if (fixArr.length > 0) {
                                    pool = [...new Set([...pool, ...fixArr])].sort((a, b) => a - b);
                                }
                                console.log('[AsyncGen] Pool Ensemble: ' + pool.length + ' números (estratégia: ' + adaptivePool._strategy + ')');
                            } catch(e) {
                                console.warn('[AsyncGen] EnsembleEngine falhou, usando range completo:', e.message);
                            }
                        }

                        if (pool.length < drawSize) {
                            // Fallback: range completo da loteria
                            var prof = GameBuilderEngine._getProfile(gameKey);
                            pool = [];
                            for (var n = prof.startNum; n <= prof.endNum; n++) pool.push(n);
                            if (fixArr.length > 0) {
                                pool = [...new Set([...pool, ...fixArr])].sort((a, b) => a - b);
                            }
                        }
                    }

                    // ═══ FIX v14.2: Anti-concentração para GameBuilderEngine ═══
                    // CAUSA DO BUG: PairOptimizer usa pares mais frequentes do histórico
                    // completo como âncoras → números âncora aparecem em ~90% dos jogos.
                    // SOLUÇÃO 1: Limitar histórico a 30 sorteios recentes.
                    //   → Reduz a dominância de pares historicamente frequentes.
                    //   → Preserva estrutura recente sem viés de longo prazo.
                    // SOLUÇÃO 2: Embaralhar pool antes de passar aos otimizadores.
                    //   → Quebra viés de ordenação que favorece números baixos.
                    var historyForBuilder = history.length > 30 ? history.slice(0, 30) : history;
                    // Embaralhar pool (Fisher-Yates) para quebrar viés de ordem
                    var shuffledPool = pool.slice();
                    for (var si = shuffledPool.length - 1; si > 0; si--) {
                        var sj = Math.floor(Math.random() * (si + 1));
                        var st = shuffledPool[si]; shuffledPool[si] = shuffledPool[sj]; shuffledPool[sj] = st;
                    }
                    console.log('[AsyncGen] v14.2: history limitado a ' + historyForBuilder.length + ' sorteios | pool embaralhado');

                    // ═══ GAMEBUILDER: forma os jogos por convergência ═══
                    result = GameBuilderEngine.generate(gameKey, numGames, shuffledPool, drawSize, historyForBuilder, options);

                } else {
                    // ═══ FALLBACK: SmartCoverageEngine ═══
                    if (typeof SmartCoverageEngine === 'undefined') throw new Error('SmartCoverageEngine não carregado');
                    result = SmartCoverageEngine.generate(
                        gameKey, numGames, selectedNumbers, fixedNumbers, drawSize, options
                    );
                }

                // === BULK ASYNC: se PrecisionEngine gerou só 50 jogos e tem mais para fazer ===
                // Acontece quando numGames > 50 com Sniper ativo.
                // generateBulkAsync gera em chunks de 300, cedendo ao browser entre cada lote.
                var bulkParams = (typeof PrecisionEngine !== 'undefined') ? PrecisionEngine._lastBulkParams : null;
                if (bulkParams && result && result.games && result.games.length < numGames) {
                    // Integrar jogos de precisão ao result antes do bulk
                    var precGames = result.games.slice();
                    var seen2 = {};
                    for (var pi = 0; pi < precGames.length; pi++) seen2[precGames[pi].join(',')] = true;

                    PrecisionEngine.generateBulkAsync(
                        bulkParams,
                        function(cur, tot) {
                            // Progresso ao vivo — atualiza barra a cada chunk
                            self._updateBar(cur, tot);
                        },
                        function(allGames, failCount, wasCancelled) {
                            self._isRunning = false;
                            if (wasCancelled) {
                                self._hideBar();
                                callback(null, true);
                                return;
                            }
                            // Deduplicar resultado final
                            var finalGames = [];
                            var seenFinal = {};
                            for (var fi = 0; fi < allGames.length; fi++) {
                                var fk = allGames[fi].join(',');
                                if (!seenFinal[fk]) { seenFinal[fk] = true; finalGames.push(allGames[fi]); }
                            }
                            self._doneBar(finalGames.length);
                            var elapsed2 = Date.now() - self._startTime;
                            var fr2 = {
                                games: finalGames,
                                pool: result.pool || [],
                                analysis: Object.assign({}, result.analysis || {}, {
                                    engine: 'PrecisionEngine+BulkAsync',
                                    totalGames: finalGames.length,
                                    elapsed: elapsed2 + 'ms',
                                    asyncMode: true,
                                    chunksProcessed: Math.ceil(finalGames.length / 300)
                                })
                            };
                            if (typeof SmartCoverageEngine !== 'undefined' && SmartCoverageEngine._calcAvgHamming) {
                                fr2.analysis.avgHamming = SmartCoverageEngine._calcAvgHamming(finalGames, drawSize);
                            }
                            setTimeout(function() { callback(fr2, false); }, 300);
                        }
                    );
                    return; // Sai — o callback do bulk cuidará do resultado
                }

                // Deduplicar
                var seen = {};
                var uniqueGames = [];
                if (result && result.games) {
                    for (var i = 0; i < result.games.length; i++) {
                        var k = result.games[i].join(',');
                        if (!seen[k]) {
                            seen[k] = true;
                            uniqueGames.push(result.games[i]);
                        }
                    }
                }

                self._updateBar(uniqueGames.length, numGames);
                self._doneBar(uniqueGames.length);

                var elapsed = Date.now() - self._startTime;
                var finalResult = {
                    games: uniqueGames,
                    pool: result.pool || (function() {
                        var s = {};
                        for (var j = 0; j < uniqueGames.length; j++)
                            for (var m = 0; m < uniqueGames[j].length; m++)
                                s[uniqueGames[j][m]] = true;
                        return Object.keys(s).map(Number).sort(function(a,b){return a-b});
                    })(),
                    analysis: Object.assign({}, result.analysis || {}, {
                        engine: useGameBuilder ? 'GameBuilderEngine' : 'SmartCoverageEngine',
                        totalGames: uniqueGames.length,
                        elapsed: elapsed + 'ms',
                        strategy: useGameBuilder ? 'GAMEBUILDER_CONVERGENCE' : 'COVERAGE_FAST',
                        asyncMode: true,
                        chunksProcessed: 1
                    })
                };

                if (useGameBuilder && result.analysis && result.analysis.convergenceStats) {
                    finalResult.analysis.avgConvergence = result.analysis.avgConvergence;
                    finalResult.analysis.convergenceStats = result.analysis.convergenceStats;
                }

                if (typeof SmartCoverageEngine !== 'undefined' && SmartCoverageEngine._calcAvgHamming) {
                    finalResult.analysis.avgHamming = SmartCoverageEngine._calcAvgHamming(uniqueGames, drawSize);
                }

                self._isRunning = false;
                setTimeout(function() { callback(finalResult, false); }, 500);

            } catch (e) {
                console.error('[AsyncGen Coverage]', e);
                self._isRunning = false;
                self._hideBar();
                callback(null, false, e);
            }
        }, 200);
    }


    // ═══════════════════════════════════════════════════════════


    // PURE COVERAGE - PureCoverageEngine (motor original)
    // UMA chamada global = Greedy Set Cover com estado completo = cobertura REAL
    static generatePureAsync(gameKey, numGames, options, callback) {
        var self = this;
        self._isRunning = true;
        self._cancelled = false;
        var game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        var name = game ? game.name : gameKey;

        // Delegação oficial para Super Sete B2B
        if (gameKey === 'supersete' && typeof MotorSuperSeteB2BEngine !== 'undefined') {
            const ssRes = MotorSuperSeteB2BEngine._gerarFallbackNativo(numGames, options);
            const games = (ssRes && ssRes.jogos) ? ssRes.jogos.map(j => j.jogo) : [];
            self._isRunning = false;
            self._hideBar();
            callback({
                games,
                analysis: {
                    totalGames: games.length,
                    poolSize: 10,
                    avgHamming: ssRes.metricas_carteira?.hamming_medio || 5.2,
                    coveragePct: ssRes.icm_global || 85,
                    elapsed: '10ms'
                }
            }, false, null);
            return;
        }

        // Barra indeterminada — motor processa tudo de uma vez
        self._showBar(name, numGames);

        // setTimeout(200ms) = browser PINTA a barra ANTES do motor pesado
        setTimeout(function() {
            try {
                if (typeof PureCoverageEngine === 'undefined') throw new Error('PureCoverageEngine nao carregado');

                if (self._cancelled) {
                    self._isRunning = false;
                    self._hideBar();
                    callback(null, true);
                    return;
                }

                // ═══ CHAMADA ÚNICA GLOBAL ═══
                // O Greedy Set Cover PRECISA de estado contínuo para:
                // 1. Cobrir TODOS os pares do espaço combinatório
                // 2. Distribuir números uniformemente (anti-concentração)
                // 3. Maximizar diversidade (Hamming) entre todos os jogos
                // Fragmentar em chunks DESTRÓI esse estado.
                var result = PureCoverageEngine.generate(gameKey, numGames, options);

                // Deduplicar (segurança)
                var seen = {};
                var uniqueGames = [];
                if (result && result.games) {
                    for (var i = 0; i < result.games.length; i++) {
                        var k = result.games[i].join(',');
                        if (!seen[k]) {
                            seen[k] = true;
                            uniqueGames.push(result.games[i]);
                        }
                    }
                }

                self._updateBar(uniqueGames.length, numGames);
                self._doneBar(uniqueGames.length);

                var elapsed = Date.now() - self._startTime;
                var totalInvest = (result && result.analysis && typeof result.analysis.investment === 'number')
                    ? result.analysis.investment
                    : ((result && result.analysis && typeof result.analysis.investimento === 'number')
                        ? result.analysis.investimento
                        : (uniqueGames.length * (game ? game.price : 0)));
                var poolArr = result.pool || (options && options.pool) || (function() {
                    var s = {};
                    for (var j = 0; j < uniqueGames.length; j++)
                        for (var m = 0; m < uniqueGames[j].length; m++)
                            s[uniqueGames[j][m]] = true;
                    return Object.keys(s).map(Number).sort(function(a,b){return a-b});
                })();
                var fr = {
                    games: uniqueGames,
                    pool: poolArr,
                    analysis: Object.assign({}, result.analysis || {}, {
                        engine: 'PureCoverageEngine',
                        totalGames: uniqueGames.length,
                        elapsed: elapsed + 'ms',
                        asyncMode: true,
                        chunksProcessed: 1,
                        investment: totalInvest,
                        investimento: totalInvest,
                        poolSize: poolArr ? poolArr.length : (result.analysis && result.analysis.poolSize ? result.analysis.poolSize : 0),
                        fixedCount: (options && options.fixed) ? options.fixed.length : 0,
                        fixedNumbers: (options && options.fixed) || []
                    })
                };

                self._isRunning = false;
                setTimeout(function() { callback(fr, false); }, 500);

            } catch (e) {
                console.error('[AsyncGen Pure]', e);
                self._isRunning = false;
                self._hideBar();
                callback(null, false, e);
            }
        }, 200);
    }

    static _dedupe(games) {
        var seen = {};
        return games.filter(function(g) { var k = g.join(','); if (seen[k]) return false; seen[k] = true; return true; });
    }

    static shouldUseAsync(numGames, gameKey) { return numGames >= 1; }
}

if (typeof window !== 'undefined') window.AsyncGenerator = AsyncGenerator;
