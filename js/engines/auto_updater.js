// ══════════════════════════════════════════════════════════════════
// AUTO UPDATER — B2B Loterias QUANTUM L99
// Atualização automática de TODOS os indicadores ao iniciar
// Versão: 1.0 — 22/04/2026
// ══════════════════════════════════════════════════════════════════

var AutoUpdater = (function () {
    'use strict';

    // ── Mapeamento de nomes internos → nomes da API ──
    var API_NAMES = {
        megasena: 'mega-sena',
        lotofacil: 'lotofacil',
        quina: 'quina',
        duplasena: 'dupla-sena',
        lotomania: 'lotomania',
        timemania: 'timemania',
        diadesorte: 'dia-de-sorte',
        milionaria: 'maismilionaria',
        loteca: 'loteca'
    };

    var HEROKU_NAMES = {
        megasena: 'megasena',
        lotofacil: 'lotofacil',
        quina: 'quina',
        duplasena: 'duplasena',
        lotomania: 'lotomania',
        timemania: 'timemania',
        diadesorte: 'diadesorte',
        milionaria: 'maismilionaria',
        loteca: 'loteca'
    };

    var ALL_GAMES = ['megasena', 'lotofacil', 'quina', 'duplasena', 'lotomania', 'timemania', 'diadesorte', 'milionaria', 'loteca'];
    var CACHE_TTL = 2 * 60 * 60 * 1000; // 2 horas
    var REFRESH_INTERVAL = 30 * 60 * 1000; // 30 minutos
    var API_TIMEOUT = 6000; // 6 segundos
    var _lastFullUpdate = 0;
    var _updateTimer = null;
    var _isUpdating = false;
    var _isFirstUpdate = true;

    // ── Buscar dados de uma loteria com fallback multi-API ──
    function _fetchGame(gameKey) {
        var caixaName = API_NAMES[gameKey] || gameKey;
        var herokuName = HEROKU_NAMES[gameKey] || gameKey;

        var apis = [
            { url: 'https://servicebus2.caixa.gov.br/portaldeloterias/api/' + caixaName, name: 'Caixa' },
            { url: 'https://loteriascaixa-api.herokuapp.com/api/' + herokuName + '/latest', name: 'Heroku' }
        ];

        return _tryAPIs(apis, 0);
    }

    function _tryAPIs(apis, index) {
        if (index >= apis.length) {
            return Promise.resolve(null);
        }
        var api = apis[index];
        return _fetchWithTimeout(api.url, API_TIMEOUT)
            .then(function (data) {
                if (data) {
                    console.log('[AutoUpdater] ✅ ' + api.name + ' OK');
                    return data;
                }
                return _tryAPIs(apis, index + 1);
            })
            .catch(function () {
                return _tryAPIs(apis, index + 1);
            });
    }

    function _fetchWithTimeout(url, ms) {
        return new Promise(function (resolve, reject) {
            var controller = new AbortController();
            var tid = setTimeout(function () { controller.abort(); }, ms);
            fetch(url, {
                signal: controller.signal,
                cache: 'no-store',
                headers: { 'Accept': 'application/json' }
            })
                .then(function (r) { clearTimeout(tid); return r.ok ? r.json() : null; })
                .then(resolve)
                .catch(function (e) { clearTimeout(tid); reject(e); });
        });
    }

    // ── Normalizar resposta da API ──
    function _normalize(data, gameKey) {
        if (!data) return null;

        // Compatibilidade entre APIs
        var drawNum = parseInt(data.numero || data.concurso || 0);
        if (!drawNum) return null;

        var dezenas = data.listaDezenas || data.dezenas || [];
        if (dezenas.length === 0 && gameKey !== 'loteca') return null;

        var numbers = dezenas.map(function (n) { return parseInt(n); }).sort(function (a, b) { return a - b; });

        var result = {
            drawNumber: drawNum,
            numbers: numbers
        };

        // +Milionária: trevos sorteados
        if (gameKey === 'milionaria') {
            var tr = data.trevosSorteados || data.trevos || [];
            if (tr && tr.length > 0) {
                result.trevos = tr.map(function (n) { return parseInt(n); }).sort(function (a, b) { return a - b; });
            }
        }

        // Dupla Sena: segundo sorteio
        if (gameKey === 'duplasena') {
            var dez2 = data.listaDezenasSegundoSorteio || data.dezenas2 || [];
            if (dez2 && dez2.length > 0) {
                result.numbers2 = dez2.map(function (n) { return parseInt(n); }).sort(function (a, b) { return a - b; });
            } else if (numbers.length >= 12) {
                result.numbers = numbers.slice(0, 6);
                result.numbers2 = numbers.slice(6, 12);
            }
        }

        // Dados de prêmio
        result.prize = {
            estimatedPrize: data.valorEstimadoProximoConcurso || 0,
            accumulatedPrize: data.valorAcumuladoProximoConcurso || 0,
            accumulated: !!(data.acumulado || data.acumulou),
            nextDraw: data.numeroConcursoProximo || data.proximoConcurso || (drawNum + 1),
            nextDrawDate: data.dataProximoConcurso || null,
            currentDraw: drawNum,
            drawDate: data.dataApuracao || data.data || null,
            lastUpdated: Date.now()
        };

        return result;
    }

    // ── Buscar concursos anteriores para preencher gaps ──
    function _fetchPreviousDraws(gameKey, latestDraw, count) {
        var promises = [];
        var existing = {};

        // Marcar concursos que já temos
        if (typeof StatsService !== 'undefined' && StatsService.historyStore[gameKey]) {
            StatsService.historyStore[gameKey].forEach(function (item) {
                existing[item.drawNumber] = true;
            });
        }
        if (typeof REAL_HISTORY_DB !== 'undefined' && REAL_HISTORY_DB[gameKey]) {
            REAL_HISTORY_DB[gameKey].forEach(function (item) {
                existing[item.drawNumber] = true;
            });
        }

        for (var i = 1; i <= count; i++) {
            var num = latestDraw - i;
            if (existing[num]) continue;

            (function (drawNum) {
                var caixaName = API_NAMES[gameKey] || gameKey;
                var herokuName = HEROKU_NAMES[gameKey] || gameKey;
                var apis = [
                    { url: 'https://servicebus2.caixa.gov.br/portaldeloterias/api/' + caixaName + '/' + drawNum, name: 'Caixa' },
                    { url: 'https://loteriascaixa-api.herokuapp.com/api/' + herokuName + '/' + drawNum, name: 'Heroku' }
                ];
                promises.push(
                    _tryAPIs(apis, 0).then(function (data) {
                        return _normalize(data, gameKey);
                    }).catch(function () { return null; })
                );
            })(num);
        }

        return Promise.all(promises).then(function (results) {
            return results.filter(function (r) { return r !== null; });
        });
    }

    // ── Mesclar dados no StatsService ──
    function _mergeIntoHistory(gameKey, latestResult, previousResults) {
        if (typeof StatsService === 'undefined') return;

        if (!StatsService.historyStore[gameKey]) {
            // Carregar da base estática primeiro
            if (typeof REAL_HISTORY_DB !== 'undefined' && REAL_HISTORY_DB[gameKey]) {
                StatsService.historyStore[gameKey] = REAL_HISTORY_DB[gameKey].slice();
            } else {
                StatsService.historyStore[gameKey] = [];
            }
        }

        var store = StatsService.historyStore[gameKey];
        var seen = {};
        store.forEach(function (item) { seen[item.drawNumber] = true; });

        // Adicionar resultado mais recente
        if (latestResult && !seen[latestResult.drawNumber]) {
            store.unshift({ drawNumber: latestResult.drawNumber, numbers: latestResult.numbers, numbers2: latestResult.numbers2 });
            seen[latestResult.drawNumber] = true;
        } else if (latestResult && seen[latestResult.drawNumber]) {
            // Atualizar existente
            for (var i = 0; i < store.length; i++) {
                if (store[i].drawNumber === latestResult.drawNumber) {
                    store[i].numbers = latestResult.numbers;
                    if (latestResult.numbers2) store[i].numbers2 = latestResult.numbers2;
                    break;
                }
            }
        }

        // Adicionar concursos anteriores
        if (previousResults) {
            previousResults.forEach(function (r) {
                if (!seen[r.drawNumber]) {
                    store.push({ drawNumber: r.drawNumber, numbers: r.numbers, numbers2: r.numbers2 });
                    seen[r.drawNumber] = true;
                }
            });
        }

        // Ordenar e limitar
        store.sort(function (a, b) { return b.drawNumber - a.drawNumber; });
        if (store.length > 60) store.length = 60;
    }

    // ── Atualizar prêmio no StatsService ──
    function _updatePrizeStore(gameKey, prizeData) {
        if (typeof StatsService === 'undefined' || !prizeData) return;
        StatsService.prizeStore[gameKey] = prizeData;

        try {
            localStorage.setItem('b2b_prize_' + gameKey, JSON.stringify(prizeData));
        } catch (e) { /* ok */ }
    }

    // ── Atualizar UI: prêmio na navbar ──
    function _updateNavPrize(gameKey, prize) {
        var navEl = document.getElementById('prize-nav-' + gameKey);
        if (!navEl || !prize || !prize.estimatedPrize) return;

        var amount = prize.estimatedPrize;
        var text;
        if (amount >= 1000000) {
            text = 'R$ ' + (amount / 1000000).toFixed(1).replace('.', ',') + ' M';
        } else if (amount >= 1000) {
            text = 'R$ ' + (amount / 1000).toFixed(0) + 'K';
        } else {
            text = 'R$ ' + amount.toFixed(0);
        }

        navEl.textContent = text;

        // Indicador de acumulado
        if (prize.accumulated) {
            navEl.style.color = '#FFD700';
            if (!navEl.querySelector('.acc-dot')) {
                var dot = document.createElement('span');
                dot.className = 'acc-dot';
                dot.style.cssText = 'display:inline-block;width:6px;height:6px;background:#EF4444;border-radius:50%;margin-left:4px;animation:pulse 1.5s infinite;vertical-align:middle;';
                navEl.appendChild(dot);
            }
        }
    }

    // ── Atualizar painel principal (se jogo ativo) ──
    function _updateMainPanel(gameKey, result) {
        // Só atualizar se este jogo é o ativo na UI
        var titleEl = document.getElementById('current-game-title');
        if (!titleEl) return;

        var game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        if (!game) return;

        var currentTitle = titleEl.textContent.trim().toLowerCase();
        var gameName = game.name.toLowerCase();
        if (currentTitle.indexOf(gameName) === -1 && !currentTitle.match(new RegExp(gameKey, 'i'))) return;

        // Atualizar número do concurso no título
        var prize = result.prize;
        if (prize && prize.nextDraw) {
            var concText = '(Concurso: ' + prize.nextDraw + ')';
            if (titleEl.textContent.indexOf('Concurso') >= 0) {
                titleEl.textContent = game.name + '  ' + concText;
            } else {
                titleEl.textContent = game.name + '  ' + concText;
            }
        }

        // Atualizar prêmio principal
        var prizeValue = document.getElementById('prize-value');
        var prizeBadge = document.getElementById('prize-badge');
        if (prizeValue && prize && prize.estimatedPrize) {
            prizeValue.textContent = prize.estimatedPrize.toLocaleString('pt-BR', {
                style: 'currency', currency: 'BRL',
                minimumFractionDigits: 0, maximumFractionDigits: 0
            });
        }
        if (prizeBadge && prize) {
            if (prize.accumulated) {
                prizeBadge.textContent = 'ACUMULADO!';
                prizeBadge.style.display = 'inline-block';
            } else {
                prizeBadge.style.display = 'none';
            }
        }

        // Atualizar countdown com data real
        if (prize && prize.nextDrawDate) {
            _updateCountdownReal(prize.nextDrawDate);
        }
    }

    // ── Countdown real baseado na data da API ──
    function _updateCountdownReal(dateStr) {
        if (!dateStr) return;
        var timerEl = document.getElementById('timer');
        if (!timerEl) return;

        // Formato: DD/MM/AAAA
        var parts = dateStr.split('/');
        if (parts.length !== 3) return;

        var targetDate = new Date(
            parseInt(parts[2]), parseInt(parts[1]) - 1, parseInt(parts[0]),
            20, 0, 0 // Sorteio às 20h
        );

        // Armazenar para o timer global
        window._b2bNextDrawDate = targetDate;

        _tickCountdown();
    }

    function _tickCountdown() {
        if (!window._b2bNextDrawDate) return;
        var timerEl = document.getElementById('timer');
        if (!timerEl) return;

        var now = new Date();
        var diff = window._b2bNextDrawDate - now;

        if (diff <= 0) {
            timerEl.textContent = 'SORTEIO HOJE!';
            timerEl.style.color = '#FFD700';
            timerEl.style.animation = 'pulse 1s infinite';
            return;
        }

        var days = Math.floor(diff / 86400000);
        var hours = Math.floor((diff % 86400000) / 3600000);
        var mins = Math.floor((diff % 3600000) / 60000);
        var secs = Math.floor((diff % 60000) / 1000);

        var text = '';
        if (days > 0) text += days + ' dias, ';
        text += String(hours).padStart(2, '0') + 'h' + String(mins).padStart(2, '0') + 'm' + String(secs).padStart(2, '0') + 's';

        timerEl.textContent = text;
    }

    // ── Banner de status visual ──
    function _showBanner(msg, type) {
        var banner = document.getElementById('auto-update-banner');
        if (!banner) {
            banner = document.createElement('div');
            banner.id = 'auto-update-banner';
            banner.style.cssText = 'position:fixed;top:0;left:0;width:100%;z-index:99999;text-align:center;padding:6px 16px;font-family:Inter,sans-serif;font-size:0.78rem;font-weight:600;transition:all 0.5s ease;pointer-events:none;';
            document.body.appendChild(banner);
        }

        if (type === 'loading') {
            banner.style.background = 'linear-gradient(90deg, #0F172A, #1E293B, #0F172A)';
            banner.style.color = '#60A5FA';
            banner.style.borderBottom = '1px solid #3B82F640';
            banner.innerHTML = '<span style="animation:pulse 1.5s infinite;display:inline-block;">🔄</span> ' + msg;
        } else if (type === 'success') {
            banner.style.background = 'linear-gradient(90deg, #052e16, #14532d, #052e16)';
            banner.style.color = '#22C55E';
            banner.style.borderBottom = '1px solid #22C55E40';
            banner.innerHTML = '✅ ' + msg;
            setTimeout(function () {
                banner.style.opacity = '0';
                setTimeout(function () { banner.remove(); }, 500);
            }, 3000);
        } else if (type === 'error') {
            banner.style.background = 'linear-gradient(90deg, #450a0a, #7f1d1d, #450a0a)';
            banner.style.color = '#FCA5A5';
            banner.style.borderBottom = '1px solid #EF444440';
            banner.innerHTML = '⚠️ ' + msg;
            setTimeout(function () {
                banner.style.opacity = '0';
                setTimeout(function () { banner.remove(); }, 500);
            }, 5000);
        }

        banner.style.opacity = '1';
    }

    // ── Verificar cache local ──
    function _isCacheValid(gameKey) {
        try {
            var cached = localStorage.getItem('b2b_autoupdate_' + gameKey);
            if (!cached) return false;
            var data = JSON.parse(cached);
            return data && data.ts && (Date.now() - data.ts) < CACHE_TTL;
        } catch (e) { return false; }
    }

    function _saveCache(gameKey, result) {
        try {
            localStorage.setItem('b2b_autoupdate_' + gameKey, JSON.stringify({
                ts: Date.now(),
                drawNumber: result.drawNumber
            }));
        } catch (e) { /* ok */ }
    }

    // ══════════════════════════════════════════════
    // MÉTODO PRINCIPAL: Atualizar uma loteria
    // ══════════════════════════════════════════════
    function updateSingleGame(gameKey) {
        // Verificar cache
        if (_isCacheValid(gameKey)) {
            console.log('[AutoUpdater] 💾 Cache válido para ' + gameKey);
            return Promise.resolve(true);
        }

        return _fetchGame(gameKey).then(function (rawData) {
            if (!rawData) {
                console.warn('[AutoUpdater] ❌ Sem dados para ' + gameKey);
                return false;
            }

            var result = _normalize(rawData, gameKey);
            if (!result) return false;

            // 1. Atualizar prêmio
            _updatePrizeStore(gameKey, result.prize);
            _updateNavPrize(gameKey, result.prize);

            // 2. Mesclar histórico
            _mergeIntoHistory(gameKey, result, null);

            // 3. Buscar concursos anteriores (gaps)
            return _fetchPreviousDraws(gameKey, result.drawNumber, 10).then(function (prev) {
                _mergeIntoHistory(gameKey, null, prev);

                // 4. Atualizar painel principal
                _updateMainPanel(gameKey, result);

                // 5. Salvar cache
                _saveCache(gameKey, result);

                console.log('[AutoUpdater] ✅ ' + gameKey + ' → Concurso ' + result.drawNumber +
                    ' | Prêmio: R$ ' + ((result.prize.estimatedPrize || 0) / 1e6).toFixed(1) + 'M' +
                    (result.prize.accumulated ? ' [ACUMULADO]' : ''));

                return true;
            });
        }).catch(function (err) {
            console.warn('[AutoUpdater] ⚠️ Erro em ' + gameKey + ':', err.message || err);
            return false;
        });
    }

    // ══════════════════════════════════════════════
    // ATUALIZAR TODAS AS LOTERIAS
    // ══════════════════════════════════════════════
    function updateAll(silent) {
        if (_isUpdating) return Promise.resolve();
        _isUpdating = true;

        if (!silent) _showBanner('Atualizando dados de todas as loterias...', 'loading');

        var promises = ALL_GAMES.map(function (key) {
            return updateSingleGame(key).catch(function () { return false; });
        });

        return Promise.all(promises).then(function (results) {
            _isUpdating = false;
            _lastFullUpdate = Date.now();

            var ok = results.filter(function (r) { return r === true; }).length;
            var fail = results.length - ok;

            if (!silent) {
                if (ok > 0) {
                    var now = new Date();
                    var timeStr = String(now.getHours()).padStart(2, '0') + ':' + String(now.getMinutes()).padStart(2, '0');
                    _showBanner('Dados atualizados — ' + ok + '/7 loterias (' + timeStr + ')', 'success');
                } else {
                    _showBanner('Modo offline — usando dados locais', 'error');
                }
            }

            // Disparar evento para a UI reagir
            try {
                window.dispatchEvent(new CustomEvent('b2b-data-updated', { detail: { ok: ok, fail: fail } }));
            } catch (e) { /* ok */ }

            return { ok: ok, fail: fail };
        });
    }

    // ══════════════════════════════════════════════
    // INICIALIZAÇÃO
    // ══════════════════════════════════════════════
    function init() {
        console.log('[AutoUpdater] 🚀 Iniciando atualização automática...');

        // Primeira atualização: imediata (com banner)
        updateAll(false).then(function () {
            _isFirstUpdate = false;
            // Agendar atualizações periódicas (silenciosas — sem banner)
            if (_updateTimer) clearInterval(_updateTimer);
            _updateTimer = setInterval(function () {
                updateAll(true); // silencioso
            }, REFRESH_INTERVAL);
        });

        // Countdown ticker a cada segundo
        setInterval(_tickCountdown, 1000);
    }

    // ══════════════════════════════════════════════
    // API PÚBLICA
    // ══════════════════════════════════════════════
    return {
        init: init,
        updateAll: updateAll,
        updateSingleGame: updateSingleGame,
        getLastUpdate: function () { return _lastFullUpdate; },
        isUpdating: function () { return _isUpdating; }
    };

})();
