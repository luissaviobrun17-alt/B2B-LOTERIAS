// ═══════════════════════════════════════════════════════════════
// CAIXA AUTOMATOR v8.9 STEALTH: Preenche apostas na Caixa
// Silencioso até ter jogos pendentes — Anti-WAF Akamai
// ═══════════════════════════════════════════════════════════════

(function() {
    'use strict';

    var VERSION = '8.9 STEALTH';

    // ═══ CONFIGURAÇÕES ═══
    var BATCH_SIZE = 10;
    var DELAY_CLICK = 130;
    var DELAY_CART = 900;
    var DELAY_BETWEEN = 700;
    var DELAY_MODAL = 250;
    var MAX_CART_RETRY = 12;

    // ═══ HELPER ANGULAR APP & SCOPE ═══
    function getCaixaApp() {
        var selectors = [
            '.escolhe-numero.lotofacil',
            '.escolhe-numero',
            '.volante',
            '#container-volante',
            '#colocarnocarrinho',
            'div.conteudo-volante',
            '[ng-controller]',
            'div[ui-view]',
            '#app',
            'body'
        ];
        for (var i = 0; i < selectors.length; i++) {
            var el = document.querySelector(selectors[i]);
            if (el && typeof angular !== 'undefined') {
                try {
                    var sc = angular.element(el).scope();
                    if (sc) {
                        var vm = sc.vm || (sc.conteudoVolante && sc.conteudoVolante.vm) || sc;
                        if (vm && (vm.numerosCartela || vm.selecionar || vm.limparVolante || vm.incluirAposta)) {
                            return { scope: sc, vm: vm };
                        }
                    }
                } catch(e) {}
            }
        }
        return null;
    }

    function getCaixaScope() {
        var app = getCaixaApp();
        if (app && app.scope) return app.scope;
        var selectors = ['.escolhe-numero', '.volante', '#container-volante', '#colocarnocarrinho', '[ng-controller]', 'body'];
        for (var i = 0; i < selectors.length; i++) {
            var el = document.querySelector(selectors[i]);
            if (el && typeof angular !== 'undefined') {
                try {
                    var sc = angular.element(el).scope();
                    if (sc) return sc;
                } catch(e) {}
            }
        }
        return null;
    }

    function triggerCaixaDigest() {
        var sc = getCaixaScope();
        if (sc) {
            try {
                if (!sc.$$phase && sc.$apply) sc.$apply();
                else if (!sc.$$phase && sc.$digest) sc.$digest();
            } catch(e) {}
        }
    }

    // ═══ 1. FECHAR MODAL DE IDADE E COOKIES (chamado apenas após confirmar jogos) ═══
    function fecharModalIdade() {
        var btnSim = document.getElementById('botaosim');
        if (btnSim && btnSim.offsetParent !== null) {
            btnSim.click();
            return true;
        }
        var bts = document.querySelectorAll('button, a, span[role=button]');
        for (var i = 0; i < bts.length; i++) {
            var t = bts[i].textContent.trim().toLowerCase();
            if ((t === 'sim' || t.indexOf('maior de 18') >= 0 || t.indexOf('mais de 18') >= 0 || t === 'aceitar') &&
                bts[i].offsetParent !== null && bts[i].offsetWidth > 10) {
                bts[i].click();
                return true;
            }
        }
        return false;
    }

    // ═══ 2. DISPATCH REAL CLICK (Anti-WAF Akamai — sem MouseEvent sintético) ═══
    function dispatchRealClick(el) {
        if (!el) return false;
        try {
            el.scrollIntoView({ block: 'center', behavior: 'instant' });
            el.click();
            triggerCaixaDigest();
            return true;
        } catch(e) {
            try { el.click(); return true; } catch(e2) { return false; }
        }
    }

    // ═══ 3. VERIFICAR JOGOS PENDENTES — tudo começa aqui, somente se houver jogos ═══
    chrome.storage.local.get(['b2b_games', 'b2b_config', 'b2b_timestamp'], function(data) {
        if (!data.b2b_games || !data.b2b_config) {
            // NENHUM JOGO: script permanece completamente silencioso
            return;
        }

        var age = Date.now() - (data.b2b_timestamp || 0);
        if (age > 120 * 60 * 1000) {
            chrome.storage.local.remove(['b2b_games', 'b2b_config', 'b2b_timestamp']);
            return;
        }

        // SÓ AGORA: inicializar tudo (localStorage, modais, painel)
        console.log('[B2B v' + VERSION + '] 🔌 Automator ativado');
        try { localStorage.setItem("ngStorage-continuarApostando", "true"); } catch(e) {}

        var games = data.b2b_games;
        var config = data.b2b_config;
        var IS_TIMEMANIA = (config.url === 'timemania');
        var IS_DIADESORTE = (config.url === 'dia-de-sorte' || config.url === 'diadesorte');

        console.log('[B2B v' + VERSION + '] 🎯 ' + games.length + ' jogos de ' + config.name);

        // Fechar modal de idade somente quando houver jogos
        var idadeInterval = setInterval(function() {
            if (fecharModalIdade()) clearInterval(idadeInterval);
        }, 800);
        setTimeout(function() { clearInterval(idadeInterval); }, 20000);

        showStatusPanel(games.length, config.name);

        // NAVEGAÇÃO ROBUSTA PARA CONCURSOS ESPECIAIS (Quina de São João, etc)
        // NOTA: Lotofácil da Independência foi removida do fallback automático para evitar concurso encerrado
        var ALTS = { 'quina': ['quina-de-sao-joao'], 'mega-sena': ['mega-sena-da-virada'], 'dupla-sena': ['dupla-sena-de-pascoa'], 'diadesorte': ['dia-de-sorte'] }[config.url] || [];
        
        function tryUrl(url, cb) {
            try {
                var inj = angular.element(document.querySelector('#app') || document.body).injector();
                if (inj) {
                    var st = inj.get("$state");
                    if (st && st.go) { st.go(url); }
                }
            } catch(e) {}
            var menuLinks = document.querySelectorAll("a[ui-sref],a[href]");
            for (var i = 0; i < menuLinks.length; i++) {
                var href = (menuLinks[i].getAttribute("ui-sref") || menuLinks[i].getAttribute("href") || "").toLowerCase();
                if (href === url || href.indexOf("#/"+url) >= 0) {
                    menuLinks[i].click(); return cb(true);
                }
            }
            // FIX CRÍTICO: Rota oficial da Caixa usa #/ e NÃO #!/
            window.location.hash = "#/" + url;
            return cb(true);
        }

        function navLoteria(idx) {
            var urls = [config.url].concat(ALTS);
            if (idx >= urls.length) return iniciarBuscaVolante(); // fallback
            
            var targetUrl = urls[idx];
            updateStatus('Navegando para ' + targetUrl + '...', 'running');
            tryUrl(targetUrl, function() {
                setTimeout(function() {
                    // Tenta achar o volante.
                    var grid = document.getElementById('n01') || document.querySelector('[id="n01"]');
                    if (grid) {
                        console.log('[B2B v' + VERSION + '] Navegação bem-sucedida para ' + targetUrl);
                        iniciarBuscaVolante();
                    } else {
                        setTimeout(function() {
                            grid = document.getElementById('n01') || document.querySelector('[id="n01"]');
                            if (grid) {
                                iniciarBuscaVolante();
                            } else {
                                console.log('[B2B v' + VERSION + '] Tentando próxima rota...');
                                navLoteria(idx + 1);
                            }
                        }, 2000);
                    }
                }, 2500);
            });
        }

        function iniciarBuscaVolante() {
            waitForGrid(function() {
                console.log('[B2B v' + VERSION + '] ✅ Grid detectado!');
                updateStatus('Grid encontrado! Iniciando em 2s...', 'running');
                setTimeout(function() {
                    fillGamesInBatches(games, config, IS_TIMEMANIA, IS_DIADESORTE);
                }, 2000);
            });
        }

        // Se já estiver na página certa (por hash), vai direto, senão navega
        var hash = window.location.hash || "";
        var currentRouteOk = hash.indexOf(config.url) >= 0;
        for (var a=0; a<ALTS.length; a++) if (hash.indexOf(ALTS[a]) >= 0) currentRouteOk = true;
        
        if (currentRouteOk) {
            iniciarBuscaVolante();
        } else {
            navLoteria(0);
        }
    });

    // ═══ 4. ESPERAR GRID DO VOLANTE ═══
    function waitForGrid(callback, attempts) {
        attempts = attempts || 0;
        if (attempts > 90) { // 3 minutos
            updateStatus('❌ Grid não encontrado. Recarregue a página.', 'error');
            return;
        }

        fecharModalIdade();

        // Procurar números do volante - múltiplos seletores
        // FIX: n00 adicionado para Lotomania (range 0-99)
        var grid = document.getElementById('n00') ||
                   document.getElementById('n01') ||
                   document.getElementById('n02') ||
                   document.getElementById('n05') ||
                   document.getElementById('n10') ||
                   document.querySelector('a[id^="n0"]') ||
                   document.querySelector('[id="n01"]');

        if (grid) {
            console.log('[B2B v' + VERSION + '] 📍 Grid encontrado (tentativa ' + (attempts + 1) + ')');
            setTimeout(callback, 2000);
        } else {
            if (attempts % 15 === 0) {
                console.log('[B2B v' + VERSION + '] ⏳ Aguardando grid... (' + (attempts + 1) + ')');
            }
            setTimeout(function() { waitForGrid(callback, attempts + 1); }, 2000);
        }
    }

    // ═══ 5. PAINEL DE STATUS FLUTUANTE ═══
    function showStatusPanel(count, name) {
        var old = document.getElementById('b2b-status-panel');
        if (old) old.remove();

        var panel = document.createElement('div');
        panel.id = 'b2b-status-panel';
        panel.style.cssText = 'position:fixed;top:10px;right:10px;z-index:999999;' +
            'background:linear-gradient(135deg,#0F172A 0%,#1E293B 100%);color:white;' +
            'padding:18px 22px;border-radius:14px;font-family:Arial,sans-serif;font-size:14px;' +
            'box-shadow:0 8px 40px rgba(0,0,0,0.6),0 0 20px rgba(34,197,94,0.15);' +
            'border:2px solid rgba(34,197,94,0.4);min-width:340px;max-width:420px;' +
            'backdrop-filter:blur(10px);';
        panel.innerHTML = 
            '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;">' +
                '<span style="font-size:22px;">🎰</span>' +
                '<span style="font-weight:800;color:#22C55E;font-size:15px;">B2B Loterias v' + VERSION + '</span>' +
                '<span style="margin-left:auto;cursor:pointer;font-size:18px;color:#94A3B8;' +
                    'transition:color 0.2s;" onmouseover="this.style.color=\'#EF4444\'" ' +
                    'onmouseout="this.style.color=\'#94A3B8\'" ' +
                    'onclick="this.parentElement.parentElement.remove()" title="Fechar">✕</span>' +
            '</div>' +
            '<div id="b2b-status-text" style="color:#E2E8F0;font-size:13px;line-height:1.4;">' +
                'Preparando ' + count + ' jogos de ' + name + '...</div>' +
            '<div id="b2b-progress" style="margin-top:10px;height:6px;background:#1E293B;' +
                'border-radius:6px;overflow:hidden;border:1px solid #334155;">' +
                '<div id="b2b-progress-bar" style="width:0%;height:100%;' +
                    'background:linear-gradient(90deg,#22C55E,#16A34A,#10B981);' +
                    'transition:width 0.4s ease;border-radius:6px;' +
                    'box-shadow:0 0 8px rgba(34,197,94,0.5);"></div>' +
            '</div>' +
            '<div style="display:flex;justify-content:space-between;margin-top:5px;">' +
                '<span id="b2b-progress-text" style="color:#94A3B8;font-size:11px;">0/' + count + '</span>' +
                '<span id="b2b-time-text" style="color:#94A3B8;font-size:11px;"></span>' +
            '</div>' +
            '<div id="b2b-log" style="margin-top:10px;max-height:150px;overflow-y:auto;' +
                'font-size:11px;font-family:\'Courier New\',monospace;color:#94A3B8;' +
                'background:rgba(0,0,0,0.4);padding:8px;border-radius:8px;display:none;' +
                'border:1px solid #334155;"></div>' +
            '<div id="b2b-final-actions" style="display:none;margin-top:12px;"></div>';
        document.body.appendChild(panel);
    }

    function updateStatus(text, type) {
        var el = document.getElementById('b2b-status-text');
        if (!el) return;
        el.textContent = text;
        if (type === 'done') el.style.color = '#22C55E';
        if (type === 'error') el.style.color = '#EF4444';
        if (type === 'running') el.style.color = '#E2E8F0';
        if (type === 'warning') el.style.color = '#F59E0B';
    }

    function updateProgress(current, total) {
        var bar = document.getElementById('b2b-progress-bar');
        var text = document.getElementById('b2b-progress-text');
        if (bar) bar.style.width = (current / total * 100) + '%';
        if (text) text.textContent = current + '/' + total;
    }

    function addLog(msg) {
        var log = document.getElementById('b2b-log');
        if (log) {
            log.style.display = 'block';
            var ts = new Date().toLocaleTimeString('pt-BR');
            log.innerHTML += '<span style="color:#64748B;">[' + ts + ']</span> ' + msg + '<br>';
            log.scrollTop = log.scrollHeight;
        }
        console.log('[B2B v' + VERSION + '] ' + msg);
    }

    // ═══ 6. FECHAR MODAIS DA CAIXA ═══
    function fecharModais() {
        var fechados = 0;
        
        // IDs específicos dos botões de fechar/confirmar da Caixa
        var ids = [
            'fecharModalAlerta', 'fecharModalErro', 'fecharModalInfo',
            'confirmarModalConfirmacao', 'botaosim', 'botaoSim',
            'btnFecharModal', 'btnOk', 'btnConfirmar', 'cookie-consent',
            'adopt-accept-all-btn', 'btnProsseguir'
        ];
        for (var k = 0; k < ids.length; k++) {
            var el = document.getElementById(ids[k]);
            if (el && el.offsetParent !== null && el.offsetWidth > 0) {
                try { dispatchRealClick(el); fechados++; } catch(e) {}
            }
        }

        // Botões e links genéricos de confirmação/fechamento
        var bts = document.querySelectorAll('button, a.btn, a[role=button], .modal button, .dialog button, div[role="dialog"] button');
        for (var j = 0; j < bts.length; j++) {
            var t = bts[j].textContent.trim().toLowerCase();
            if ((t === 'ok' || t === 'entendi' || t === 'fechar' || t === 'confirmar' || 
                 t === 'continuar' || t === 'sim' || t === 'prosseguir' || t === 'aceitar' || 
                 t === 'concordar' || t === 'entendido') &&
                bts[j].offsetParent !== null && bts[j].offsetWidth > 0 && bts[j].offsetHeight > 0) {
                var btnId = (bts[j].id || '').toLowerCase();
                var isBtnCarrinho = btnId.indexOf('carrinho') >= 0 || btnId.indexOf('pagamento') >= 0 ||
                                    t.indexOf('carrinho') >= 0 || t.indexOf('pagamento') >= 0;
                if (!isBtnCarrinho) {
                    try { dispatchRealClick(bts[j]); fechados++; } catch(e) {}
                }
            }
        }

        // Fechar overlays
        var overlays = document.querySelectorAll('.modal-backdrop, .cdk-overlay-backdrop');
        for (var m = 0; m < overlays.length; m++) {
            try { overlays[m].click(); } catch(e) {}
        }

        return fechados;
    }

    // ═══ 7. PREENCHER JOGOS EM LOTES ═══
    async function fillGamesInBatches(games, config, IS_TIMEMANIA, IS_DIADESORTE) {
        var delay = function(ms) { return new Promise(function(r) { setTimeout(r, ms); }); };
        var total = games.length;
        var ok = 0;
        var erros = 0;
        var startTime = Date.now();

        addLog('🎬 Iniciando ' + total + ' jogos de ' + config.name);
        addLog('⚡ Modo TURBO: lotes de ' + BATCH_SIZE);
        if (IS_TIMEMANIA) addLog('⚽ Time do Coração será selecionado automaticamente');
        if (IS_DIADESORTE) addLog('📅 Mês da Sorte será selecionado automaticamente');

        for (var i = 0; i < total; i++) {
            var jogo = games[i];
            var elapsed = ((Date.now() - startTime) / 1000).toFixed(0);
            updateStatus('Jogo ' + (i + 1) + '/' + total + ' — preenchendo...', 'running');
            updateProgress(i, total);

            var timeEl = document.getElementById('b2b-time-text');
            if (timeEl) timeEl.textContent = elapsed + 's';

            // Fechar modais antes
            fecharModais();
            await delay(DELAY_MODAL);

            // TENTATIVA 1: PREENCHIMENTO NATIVO VIA ANGULARJS VIEWMODEL
            var app = getCaixaApp();
            var preenchidoNativo = false;

            if (app && app.vm && app.vm.numerosCartela && typeof app.vm.selecionar === 'function') {
                try {
                    // Limpar volante nativamente
                    if (typeof app.vm.limparVolante === 'function') {
                        app.vm.limparVolante();
                    }
                    var numsTarget = nums.map(function(n) { return parseInt(n, 10); });
                    if (app.vm.qtdNumerosAposta && app.vm.qtdNumerosAposta !== numsTarget.length) {
                        app.vm.qtdNumerosAposta = numsTarget.length;
                    }
                    for (var c = 0; c < app.vm.numerosCartela.length; c++) {
                        var item = app.vm.numerosCartela[c];
                        var want = (numsTarget.indexOf(item.valor) >= 0);
                        if (want !== !!item.selecionado) {
                            app.vm.selecionar(item);
                        }
                    }
                    if (app.scope && !app.scope.$$phase) app.scope.$apply();
                    preenchidoNativo = true;
                    addLog('⚡ Jogo ' + (i+1) + ': ' + nums.length + ' dezenas selecionadas via Angular VM');
                } catch(errVm) {
                    console.warn('[B2B] Fallback VM:', errVm);
                    preenchidoNativo = false;
                }
            }

            // TENTATIVA 2: FALLBACK VIA CLIQUE DOM
            if (!preenchidoNativo) {
                // Limpar volante antes de preencher
                if (i === 0) {
                    fecharModais();
                    await limparVolanteComRetry();
                    await delay(300);
                } else {
                    await limparVolanteComRetry();
                    await delay(300);
                    fecharModais();
                }

                // Clicar em cada número
                var isLargeGame = nums.length >= 20;
                var clickDelay = isLargeGame ? Math.max(DELAY_CLICK, 80) : DELAY_CLICK;
                for (var j = 0; j < nums.length; j++) {
                    clicarNumero(nums[j]);
                    await delay(clickDelay);
                }

                // Verificação leve com range correto por loteria
                var maxRange = (config.url === 'lotofacil') ? 25 : ((config.url === 'lotomania') ? 100 : (config.url === 'timemania' || config.url === 'quina' ? 80 : 60));
                for (var vf = 0; vf < nums.length; vf++) {
                    var elF = getElementoNumero(nums[vf]);
                    if (elF && !isNumeroMarcado(elF)) {
                        dispatchRealClick(elF);
                        await delay(50);
                    }
                }
                triggerCaixaDigest();
                await delay(300);
            }

            addLog('🔢 Jogo ' + (i+1) + ': ' + nums.length + ' dezenas verificadas [' + nums.join(',') + ']');
            fecharModais();
            await delay(DELAY_MODAL);

            // Selecionar Time/Mês antes de colocar no carrinho
            if (IS_TIMEMANIA) {
                var timeOk = await selecionarTimeDoCoracao();
                addLog('⚽ Time: ' + (timeOk ? 'OK' : 'FALHOU'));
                await delay(300);
            }
            if (IS_DIADESORTE) {
                var mesOk = await selecionarMesDaSorte();
                addLog('📅 Mês: ' + (mesOk ? 'OK' : 'FALHOU'));
                await delay(300);
            }

            var cartOk = await colocarNoCarrinhoComRetry(IS_TIMEMANIA, IS_DIADESORTE);

            if (cartOk) {
                ok++;
                addLog('✅ Jogo ' + (i+1) + ' → carrinho (' + ok + '/' + total + ')');
            } else {
                erros++;
                addLog('❌ Jogo ' + (i+1) + ' FALHOU');
            }

            // Delay entre jogos (menor dentro do lote)
            if (i < total - 1) {
                var isEndOfBatch = (i + 1) % BATCH_SIZE === 0;
                if (isEndOfBatch) {
                    addLog('⏸️ Pausa após lote ' + Math.ceil((i+1)/BATCH_SIZE) + '...');
                    await delay(1500); // Pausa maior entre lotes
                } else {
                    await delay(DELAY_BETWEEN);
                }
                fecharModais();
                await delay(DELAY_MODAL);
            }
        }

        // ═══ FINALIZAÇÃO ═══
        updateProgress(total, total);
        var totalTime = ((Date.now() - startTime) / 1000).toFixed(1);
        var msg = '✅ ' + ok + '/' + total + ' jogos no carrinho! (' + totalTime + 's)';
        if (erros > 0) msg += ' ⚠️ ' + erros + ' erro(s)';
        updateStatus(msg, 'done');
        addLog('🏆 ' + msg);

        // Limpar dados usados
        chrome.storage.local.remove(['b2b_games', 'b2b_config', 'b2b_timestamp']);

        // Mostrar botões de ação final
        showFinalActions(ok, total, config.name);
    }

    // ═══ 8. SELEÇÃO ROBUSTA DE DEZENAS (ANTI-DESMARCAÇÃO) ═══
    function isNumeroMarcado(el) {
        if (!el) return false;
        var cls = (el.className || '').toString().toLowerCase();
        if (cls.indexOf('selecionad') >= 0 || cls.indexOf('ativo') >= 0 || cls.indexOf('active') >= 0 || cls.indexOf('selected') >= 0) return true;
        var parentCls = (el.parentElement ? (el.parentElement.className || '').toString().toLowerCase() : '');
        if (parentCls.indexOf('selecionad') >= 0 || parentCls.indexOf('ativo') >= 0 || parentCls.indexOf('active') >= 0 || parentCls.indexOf('selected') >= 0) return true;
        if (el.getAttribute('aria-pressed') === 'true' || el.getAttribute('aria-selected') === 'true') return true;
        return false;
    }

    function getElementoNumero(num) {
        var n = parseInt(num, 10);
        if (isNaN(n)) return null;
        var padded = String(n).padStart(2, '0');
        var raw = String(n);

        // Tentativa 1: ID direto
        var el = document.getElementById('n' + padded) ||
                 document.getElementById('n' + raw) ||
                 document.getElementById('d' + padded) ||
                 document.querySelector('#n' + padded) ||
                 document.querySelector('a#n' + padded) ||
                 document.querySelector('#n' + raw);
        if (el) return el;

        // Tentativa 2: querySelector em botões/links de dezenas
        var todos = document.querySelectorAll('a[role=button], a.dezena, a.numero, a[id^="n"], li[id^="n"]');
        for (var k = 0; k < todos.length; k++) {
            var txt = todos[k].textContent.trim();
            if (txt === padded || txt === raw) {
                return todos[k];
            }
        }

        // Tentativa 3: qualquer elemento com classe número
        var allNums = document.querySelectorAll('.number, .dezena, .num, [class*=number], [class*=dezena]');
        for (var k2 = 0; k2 < allNums.length; k2++) {
            var t = allNums[k2];
            if (t.closest && t.closest('[class*="carrinho"], [id*="carrinho"], [class*="resumo"]')) continue;
            var txt2 = t.textContent.trim();
            if (txt2 === padded || txt2 === raw) {
                return t;
            }
        }
        return null;
    }

    function clicarNumero(num) {
        var el = getElementoNumero(num);
        if (el) {
            // Se já estiver marcado, NÃO clica novamente para não desmarcar!
            if (!isNumeroMarcado(el)) {
                dispatchRealClick(el);
            }
            return true;
        }
        return false;
    }

    function desmarcarNumero(num) {
        var el = getElementoNumero(num);
        if (el && isNumeroMarcado(el)) {
            dispatchRealClick(el);
            return true;
        }
        return false;
    }

    // ═══ 9. COLOCAR NO CARRINHO COM RETRY ROBUSTO ═══
    async function colocarNoCarrinhoComRetry(IS_TIMEMANIA, IS_DIADESORTE) {
        var delay = function(ms) { return new Promise(function(r) { setTimeout(r, ms); }); };

        fecharModais();
        await delay(DELAY_MODAL);

        // Tentativa 0: Inclusão direta via AngularJS ViewModel
        var app = getCaixaApp();
        if (app && app.vm && typeof app.vm.incluirAposta === 'function') {
            var canInclude = true;
            if (typeof app.vm.habilitarInclusaoAposta === 'function') {
                canInclude = app.vm.habilitarInclusaoAposta();
            }
            if (canInclude) {
                try {
                    app.vm.incluirAposta();
                    if (app.scope && !app.scope.$$phase) app.scope.$apply();
                    addLog('🛒 Carrinho OK (Angular VM nativo)');
                    await delay(DELAY_CART);
                    fecharModais();
                    return true;
                } catch(e) {
                    console.warn('[B2B] Fallback nativo para DOM:', e);
                }
            }
        }

        for (var t = 0; t < MAX_CART_RETRY; t++) {
            // Tentativa 1: ID exato "colocarnocarrinho" ou classe Lotofácil
            var btn = document.getElementById('colocarnocarrinho') ||
                      document.querySelector('.data-incluir-aposta-lotofacil');
            if (btn && btn.offsetParent !== null) {
                // FIX CRÍTICO: Verificar se o botão está HABILITADO antes de clicar
                if (btn.disabled || btn.classList.contains('disabled')) {
                    addLog('⏳ Carrinho desabilitado, tentativa ' + (t+1) + '/' + MAX_CART_RETRY);
                    // Forçar Angular digest na hierarquia correta da Caixa
                    triggerCaixaDigest();
                    await delay(800);
                    // Re-selecionar Time/Mês se necessário
                    if (IS_TIMEMANIA) { await selecionarTimeDoCoracao(); await delay(400); }
                    if (IS_DIADESORTE) { await selecionarMesDaSorte(); await delay(400); }
                    continue;
                }
                dispatchRealClick(btn);
                addLog('🛒 Carrinho OK (ID, tent ' + (t+1) + ')');
                await delay(DELAY_CART);
                fecharModais();
                await delay(300);
                fecharModais();
                return true;
            }

            // Tentativa 2: querySelector variantes
            btn = document.querySelector('#colocarnocarrinho') ||
                  document.querySelector('.data-incluir-aposta-lotofacil') ||
                  document.querySelector('button#colocarnocarrinho') ||
                  document.querySelector('[id="colocarnocarrinho"]') ||
                  document.querySelector('button[id*="colocar"]');
            if (btn) {
                if (btn.disabled || btn.classList.contains('disabled')) {
                    triggerCaixaDigest();
                    await delay(800);
                    if (IS_TIMEMANIA) { await selecionarTimeDoCoracao(); await delay(400); }
                    if (IS_DIADESORTE) { await selecionarMesDaSorte(); await delay(400); }
                    continue;
                }
                dispatchRealClick(btn);
                addLog('🛒 Carrinho OK (query, tent ' + (t+1) + ')');
                await delay(DELAY_CART);
                fecharModais();
                await delay(300);
                fecharModais();
                return true;
            }

            // Tentativa 3: botões com texto que contém "carrinho"
            var allBtns = document.querySelectorAll('button, a');
            var foundCart = false;
            for (var k = 0; k < allBtns.length; k++) {
                var txt = allBtns[k].textContent.toLowerCase().trim();
                if ((txt.indexOf('colocar no carrinho') >= 0 || txt.indexOf('colocar no carr') >= 0) &&
                    allBtns[k].offsetParent !== null && allBtns[k].offsetWidth > 0) {
                    if (allBtns[k].disabled || allBtns[k].classList.contains('disabled')) {
                        triggerCaixaDigest();
                        await delay(800);
                        foundCart = true;
                        break;
                    }
                    dispatchRealClick(allBtns[k]);
                    addLog('🛒 Carrinho OK (texto, tent ' + (t+1) + ')');
                    await delay(DELAY_CART);
                    fecharModais();
                    await delay(300);
                    fecharModais();
                    return true;
                }
            }

            if (t % 3 === 0) {
                addLog('⏳ Carrinho: tentativa ' + (t+1) + '/' + MAX_CART_RETRY);
            }
            fecharModais();
            await delay(500);
        }

        addLog('❌ Carrinho não encontrado/habilitado após ' + MAX_CART_RETRY + ' tentativas');
        return false;
    }

    // ═══ 9B. SELECIONAR TIME DO CORAÇÃO (TIMEMANIA) ═══
    async function selecionarTimeDoCoracao() {
        var delay = function(ms) { return new Promise(function(r) { setTimeout(r, ms); }); };
        await delay(300);

        // Seletores REAIS do site da Caixa (AngularJS)
        var times = document.querySelectorAll('img[name=btnTime],.data-selecionar-time-do-coracao,li[ng-repeat*=listaEquipe] img,li[ng-click*=Time] img,li[ng-click*=time] img');

        // Fallback: procurar LIs com ng-repeat de equipes
        if (times.length === 0) {
            var tLis = document.querySelectorAll('li[ng-repeat*=listaEquipe],li[ng-repeat*=equipe]');
            if (tLis.length > 0) {
                var tImgs = [];
                for (var q = 0; q < tLis.length; q++) {
                    var tImg = tLis[q].querySelector('img');
                    if (tImg) tImgs.push(tImg);
                }
                if (tImgs.length > 0) times = tImgs;
            }
        }

        // Fallback 2: UL com muitas imagens (>20 = lista de times)
        if (times.length === 0) {
            var allUls = document.querySelectorAll('ul');
            for (var u = 0; u < allUls.length; u++) {
                var uImgs = allUls[u].querySelectorAll('img');
                if (uImgs.length > 20) { times = uImgs; break; }
            }
        }

        if (times.length > 0) {
            var idx = Math.floor(Math.random() * times.length);
            var chosen = times[idx];
            chosen.scrollIntoView({ block: 'center', behavior: 'instant' });
            await delay(150);
            dispatchRealClick(chosen);
            await delay(250);
            // Clicar no LI pai para garantir trigger Angular
            if (chosen.parentElement && chosen.parentElement.tagName === 'LI') {
                dispatchRealClick(chosen.parentElement);
                await delay(200);
            }
            try { var scope = angular.element(chosen).scope(); if (scope && scope.$apply) scope.$apply(); } catch(e) {}
            var nome = chosen.alt || chosen.title || (chosen.parentElement ? chosen.parentElement.textContent.trim().substring(0, 30) : 'Time #' + (idx+1));
            addLog('⚽ Time selecionado: ' + nome);
            return true;
        }
        addLog('⚠️ Nenhum time encontrado na página');
        return false;
    }

    // ═══ 9C. SELECIONAR MÊS DA SORTE (DIA DE SORTE) ═══
    async function selecionarMesDaSorte() {
        var delay = function(ms) { return new Promise(function(r) { setTimeout(r, ms); }); };
        await delay(300);

        // Seletores REAIS do site da Caixa (AngularJS)
        var meses = document.querySelectorAll('li[ng-repeat*=listaMeses],li[ng-click*=configurarMes],[id=mes] li,ul.meses li,.meses-list li, .lista-meses li, label.mes, .mes-sorte li');

        // Fallback: procurar meses por nome em português
        if (meses.length === 0) {
            var nomesMeses = ['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro','marco'];
            var allLi = document.querySelectorAll('li, a, span, div, label, button');
            var found = [];
            for (var q = 0; q < allLi.length; q++) {
                var tx = allLi[q].textContent.trim().toLowerCase();
                for (var m = 0; m < nomesMeses.length; m++) {
                    if (tx.indexOf(nomesMeses[m]) !== -1 && tx.length < 25 && allLi[q].children.length <= 1) {
                        found.push(allLi[q]);
                        break;
                    }
                }
            }
            if (found.length > 0) meses = found;
        }

        // Fallback 2: select/option
        if (meses.length === 0) {
            var sel = document.querySelector('select');
            if (sel && sel.options.length > 1) {
                sel.selectedIndex = Math.floor(Math.random() * (sel.options.length - 1)) + 1;
                sel.dispatchEvent(new Event('change', { bubbles: true }));
                addLog('📅 Mês (select): ' + sel.options[sel.selectedIndex].text);
                return true;
            }
        }

        if (meses.length > 0) {
            var idx = Math.floor(Math.random() * meses.length);
            var mesEl = meses[idx];
            dispatchRealClick(mesEl);
            await delay(400);
            if (mesEl.tagName !== 'LI' && mesEl.parentElement && mesEl.parentElement.tagName === 'LI') {
                dispatchRealClick(mesEl.parentElement);
                await delay(200);
            }
            try { var scope = angular.element(mesEl).scope(); if (scope && scope.$apply) scope.$apply(); } catch(e) {}
            var mesNome = mesEl.textContent.trim() || 'Mês #' + (idx+1);
            addLog('📅 Mês selecionado: ' + mesNome);
            return true;
        }
        addLog('⚠️ Nenhum mês encontrado na página');
        return false;
    }

    // ═══ 10. LIMPAR VOLANTE COM RETRY E DESMARCAÇÃO ATÔMICA ═══
    async function limparVolanteComRetry() {
        var delay = function(ms) { return new Promise(function(r) { setTimeout(r, ms); }); };
        fecharModais();

        // Tentativa nativa direta
        var app = getCaixaApp();
        if (app && app.vm && typeof app.vm.limparVolante === 'function') {
            try {
                app.vm.limparVolante();
                if (app.scope && !app.scope.$$phase) app.scope.$apply();
                await delay(200);
                return true;
            } catch(e) {}
        }
        
        for (var t = 0; t < 5; t++) {
            fecharModais();

            // ID exato e classe da Lotofácil
            var btn = document.getElementById('limparvolante') ||
                      document.querySelector('.data-limpar-volante-lotofacil') ||
                      document.querySelector('#limparvolante') ||
                      document.querySelector('button#limparvolante') ||
                      document.querySelector('[id*="limparvolante"]') ||
                      document.querySelector('[id*="limpar"]');
            if (btn && btn.offsetParent !== null) {
                dispatchRealClick(btn);
                await delay(350);
                fecharModais();
                await delay(150);
            } else {
                // Buscar por texto
                var allBtns = document.querySelectorAll('button, a');
                for (var k = 0; k < allBtns.length; k++) {
                    var txt = allBtns[k].textContent.toLowerCase().trim();
                    if ((txt.indexOf('limpar volante') >= 0 || txt === 'limpar') &&
                        allBtns[k].offsetParent !== null) {
                        dispatchRealClick(allBtns[k]);
                        await delay(350);
                        fecharModais();
                        await delay(150);
                        break;
                    }
                }
            }

            triggerCaixaDigest();
            await delay(250);

            // VERIFICAÇÃO ATÔMICA: se ainda houver dezenas marcadas no volante, desmarcar explicitamente!
            var dezenasAindaMarcadas = 0;
            var marcados = document.querySelectorAll('.selecionado, .ativo, [class*="selecionad"], a[aria-pressed="true"]');
            for (var m = 0; m < marcados.length; m++) {
                var elM = marcados[m];
                if (elM.closest && elM.closest('[class*="carrinho"], [id*="carrinho"], [class*="resumo"], [class*="sidebar"]')) continue;
                if (isNumeroMarcado(elM)) {
                    dispatchRealClick(elM);
                    dezenasAindaMarcadas++;
                }
            }

            if (dezenasAindaMarcadas > 0) {
                triggerCaixaDigest();
                await delay(200);
            }

            // Checagem final de dezenas 1 a 60/80
            var checkMarcados = 0;
            for (var numCheck = 1; numCheck <= 80; numCheck++) {
                var elCheck = getElementoNumero(numCheck);
                if (elCheck && isNumeroMarcado(elCheck)) {
                    checkMarcados++;
                }
            }

            if (checkMarcados === 0) {
                return true;
            }

            await delay(400);
        }
        return false;
    }

    // ═══ 11. AÇÕES FINAIS — IR PARA PAGAMENTO ═══
    function showFinalActions(ok, total, name) {
        var container = document.getElementById('b2b-final-actions');
        if (!container) return;

        container.style.display = 'block';
        container.innerHTML = 
            '<div style="border-top:1px solid #334155;padding-top:12px;">' +
                '<div style="color:#F59E0B;font-weight:700;font-size:12px;margin-bottom:8px;">' +
                    '⚠️ PRÓXIMO PASSO: Finalizar pagamento</div>' +
                '<div style="display:flex;gap:8px;">' +
                    '<button id="b2b-btn-pay" style="flex:1;padding:10px;background:linear-gradient(135deg,#22C55E,#16A34A);' +
                        'color:white;border:none;border-radius:8px;font-weight:800;font-size:13px;cursor:pointer;' +
                        'transition:all 0.2s;box-shadow:0 4px 12px rgba(34,197,94,0.3);" ' +
                        'onmouseover="this.style.transform=\'scale(1.02)\'" ' +
                        'onmouseout="this.style.transform=\'scale(1)\'">' +
                        '💳 Ir para Pagamento</button>' +
                    '<button id="b2b-btn-cart" style="flex:1;padding:10px;background:linear-gradient(135deg,#3B82F6,#1D4ED8);' +
                        'color:white;border:none;border-radius:8px;font-weight:800;font-size:13px;cursor:pointer;' +
                        'transition:all 0.2s;box-shadow:0 4px 12px rgba(59,130,246,0.3);" ' +
                        'onmouseover="this.style.transform=\'scale(1.02)\'" ' +
                        'onmouseout="this.style.transform=\'scale(1)\'">' +
                        '🛒 Ver Carrinho</button>' +
                '</div>' +
                '<div style="margin-top:8px;padding:8px;background:rgba(245,158,11,0.1);' +
                    'border:1px solid rgba(245,158,11,0.3);border-radius:6px;">' +
                    '<p style="margin:0;color:#FCD34D;font-size:11px;line-height:1.5;">' +
                        '📝 <strong>' + ok + ' jogos</strong> de ' + name + ' estão no carrinho.<br>' +
                        'Clique em <strong>"Ir para Pagamento"</strong> e faça login na Caixa para concluir sua aposta.' +
                    '</p>' +
                '</div>' +
            '</div>';

        // Botão IR PARA PAGAMENTO
        var btnPay = document.getElementById('b2b-btn-pay');
        if (btnPay) {
            btnPay.addEventListener('click', function() {
                irParaPagamento();
            });
        }

        // Botão VER CARRINHO
        var btnCart = document.getElementById('b2b-btn-cart');
        if (btnCart) {
            btnCart.addEventListener('click', function() {
                acessarCarrinho();
            });
        }

        // Auto-tentar ir para pagamento após 2s
        setTimeout(function() {
            addLog('🔔 Clique "Ir para Pagamento" para finalizar!');
        }, 2000);
    }

    // ═══ 12. IR PARA PAGAMENTO ═══
    function irParaPagamento() {
        addLog('💳 Tentando ir para pagamento...');

        // Tentativa 1: botão pelo ID direto
        var btn = document.getElementById('irparapagamento');
        if (btn) {
            dispatchRealClick(btn);
            addLog('✅ Clicou em #irparapagamento');
            return;
        }

        // Tentativa 2: buscar botão de pagamento
        var allBtns = document.querySelectorAll('button, a');
        for (var k = 0; k < allBtns.length; k++) {
            var txt = allBtns[k].textContent.toLowerCase().trim();
            if ((txt.indexOf('pagamento') >= 0 || txt.indexOf('pagar') >= 0 || 
                 txt.indexOf('finalizar') >= 0 || txt.indexOf('ir para pagamento') >= 0) &&
                allBtns[k].offsetParent !== null) {
                dispatchRealClick(allBtns[k]);
                addLog('✅ Clicou em botão de pagamento (' + txt.substring(0, 30) + ')');
                return;
            }
        }

        // Tentativa 3: navegar direto
        addLog('⚠️ Botão de pagamento não encontrado, tentando via carrinho...');
        acessarCarrinho();
    }

    // ═══ 13. ACESSAR CARRINHO ═══
    function acessarCarrinho() {
        // Tentativa 1: ID do carrinho
        var btn = document.getElementById('acessarcarrrinhoapostas') || 
                  document.getElementById('acessarcarrinhoapostas');
        if (btn) {
            dispatchRealClick(btn);
            addLog('✅ Clicou em carrinho de apostas');
            return;
        }

        // Tentativa 2: buscar por ícone de carrinho
        var allLinks = document.querySelectorAll('a, button, div');
        for (var k = 0; k < allLinks.length; k++) {
            var txt = allLinks[k].textContent.toLowerCase().trim();
            if ((txt.indexOf('acessar') >= 0 && allLinks[k].closest('[class*="carrinho"]')) ||
                (txt.indexOf('carrinho') >= 0 && txt.indexOf('colocar') < 0)) {
                if (allLinks[k].offsetParent !== null && allLinks[k].offsetWidth > 0) {
                    dispatchRealClick(allLinks[k]);
                    addLog('✅ Clicou no carrinho (' + txt.substring(0, 30) + ')');
                    return;
                }
            }
        }

        // Tentativa 3: o número do carrinho no header
        var cartCount = document.querySelector('[class*="carrinho"] span, [class*="cart"] span');
        if (cartCount && cartCount.parentElement) {
            dispatchRealClick(cartCount.parentElement);
            addLog('✅ Clicou no contador do carrinho');
            return;
        }

        addLog('⚠️ Carrinho não encontrado — clique manualmente no ícone 🛒 no topo da página');
    }

})();
