// Global UI usage — Hardened v2.0

document.addEventListener('DOMContentLoaded', function() {
    try {
        var gameKeys = ['megasena', 'lotofacil', 'quina', 'duplasena', 'lotomania', 'timemania', 'diadesorte', 'milionaria', 'loteca'];
        gameKeys.forEach(function(key) {
            try {
                var game = typeof GAMES !== 'undefined' ? GAMES[key] : null;
                if (game && game.estimatedPrizeFallback) {
                    var navElem = document.getElementById('prize-nav-' + key);
                    if (navElem && (navElem.textContent === '--' || navElem.textContent.trim() === '')) {
                        var amount = game.estimatedPrizeFallback;
                        if (amount >= 1000000) {
                            navElem.textContent = 'R$ ' + (amount / 1000000).toFixed(1).replace('.', ',') + ' M';
                        } else if (amount >= 1000) {
                            navElem.textContent = 'R$ ' + (amount / 1000).toFixed(0) + 'K';
                        }
                    }
                }
            } catch(prizeErr) {
                console.warn('[Main] Erro ao carregar prêmio para ' + key + ':', prizeErr.message);
            }
        });

        // Mostrar prêmio principal (Mega Sena = jogo padrão)
        var prizeDisplay = document.getElementById('prize-display');
        var prizeValue = document.getElementById('prize-value');
        if (prizeDisplay && prizeValue) {
            var megaFallback = typeof GAMES !== 'undefined' && GAMES.megasena ? GAMES.megasena.estimatedPrizeFallback : 30000000;
            prizeValue.textContent = megaFallback.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 0, maximumFractionDigits: 0 });
            prizeDisplay.style.display = 'block';
        }

        // ══════ VERIFICAÇÃO PRÉ-INICIALIZAÇÃO ══════
        if (typeof GAMES === 'undefined') {
            console.error('[Main] ❌ GAMES não carregado! Verifique games.js');
            if (typeof Guardian !== 'undefined') {
                Guardian.toast('Erro crítico: dados das loterias não carregados. Recarregue com Ctrl+Shift+R', 'error', 10000);
            }
            return;
        }
        if (typeof UI === 'undefined') {
            console.error('[Main] ❌ UI não carregado! Verifique ui.js');
            if (typeof Guardian !== 'undefined') {
                Guardian.toast('Erro crítico: interface não carregada. Recarregue com Ctrl+Shift+R', 'error', 10000);
            }
            return;
        }

        var ui = new UI();
        window._b2bUI = ui; // Expor globalmente para CoverageEngine e outros handlers
        ui.initEvents();
        ui.updateGameInfo('megasena');
        ui.addInstallButton();

        // ══════════════════════════════════════════════
        // AUTO UPDATER — Atualizar dados automaticamente
        // ══════════════════════════════════════════════
        if (typeof AutoUpdater !== 'undefined') {
            // Delay de 500ms para garantir que UI está pronta
            setTimeout(function() {
                try {
                    AutoUpdater.init();
                    // Nota: O AutoUpdater já atualiza prêmios e countdown diretamente.
                    // NÃO chamar updateGameInfo() no evento pois ele reseta seleções e jogos.
                } catch(autoErr) {
                    console.warn('[Main] AutoUpdater falhou:', autoErr.message);
                }
            }, 500);
        }

        console.log('%c[B2B] ✅ Sistema inicializado com sucesso', 'color:#22C55E;font-weight:bold;');

    } catch(e) {
        console.error('[Main] ERRO FATAL na inicialização:', e);
        // Usar Guardian toast se disponível, senão alert como último recurso
        if (typeof Guardian !== 'undefined') {
            Guardian.toast('Erro na inicialização: ' + e.message + ' — Tente Ctrl+Shift+R', 'error', 10000);
        } else {
            alert('ERRO B2B: ' + e.message + '\n\nLinha: ' + (e.stack || ''));
        }
    }
});
