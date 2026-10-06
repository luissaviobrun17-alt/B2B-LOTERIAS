// ╔══════════════════════════════════════════════════════════════════════╗
// ║  GUARDIAN LAYER v1.0 — Camada de Proteção Global B2B Loterias     ║
// ║  Carregado ANTES de todos os outros scripts.                       ║
// ║  Previne crashes por null references, NaN, engines não carregados  ║
// ╚══════════════════════════════════════════════════════════════════════╝

(function(global) {
    'use strict';

    const Guardian = {
        version: '1.0',
        _errorCount: 0,
        _maxErrors: 50,      // Limite de erros antes de parar de reportar
        _toastQueue: [],
        _toastActive: false,
        _toastContainer: null,
        _timeouts: new Map(), // Gerenciamento central de timeouts
        _retryCounters: {},   // Contadores de retry por chave

        // ══════════════════════════════════════════════════════════════
        // SAFE DOM — Nunca retorna null, retorna proxy seguro
        // ══════════════════════════════════════════════════════════════
        _nullProxy: null,

        /**
         * $$(id) — getElementById seguro. Retorna o elemento ou um objeto inerte.
         * Uso: const el = Guardian.$('my-id'); el.style.display = 'none'; // nunca crash
         */
        $(id) {
            const el = document.getElementById(id);
            if (el) return el;
            // Retornar proxy que absorve qualquer operação sem crash
            if (!Guardian._nullProxy) {
                Guardian._nullProxy = new Proxy({}, {
                    get(target, prop) {
                        if (prop === 'style') return new Proxy({}, { set() { return true; }, get() { return ''; } });
                        if (prop === 'classList') return { add(){}, remove(){}, toggle(){}, contains(){ return false; } };
                        if (prop === 'innerHTML' || prop === 'textContent' || prop === 'value') return '';
                        if (prop === 'dataset') return {};
                        if (prop === 'parentNode' || prop === 'parentElement') return Guardian._nullProxy;
                        if (prop === 'querySelector' || prop === 'querySelectorAll') return () => prop === 'querySelectorAll' ? [] : null;
                        if (prop === 'appendChild' || prop === 'insertBefore' || prop === 'removeChild') return () => null;
                        if (prop === 'addEventListener' || prop === 'removeEventListener') return () => {};
                        if (prop === 'scrollIntoView' || prop === 'focus' || prop === 'select' || prop === 'click' || prop === 'remove') return () => {};
                        if (prop === 'offsetWidth' || prop === 'offsetHeight') return 0;
                        if (prop === 'children' || prop === 'childNodes') return [];
                        if (typeof prop === 'symbol') return undefined;
                        return '';
                    },
                    set() { return true; }
                });
            }
            // Log apenas na primeira vez (não poluir console)
            if (Guardian._errorCount < 5) {
                console.warn(`[Guardian] ⚠️ Elemento #${id} não encontrado no DOM`);
            }
            return Guardian._nullProxy;
        },

        // ══════════════════════════════════════════════════════════════
        // SAFE parseInt — Nunca retorna NaN
        // ══════════════════════════════════════════════════════════════
        safeInt(value, fallback) {
            if (fallback === undefined) fallback = 0;
            const n = parseInt(value, 10);
            return isNaN(n) ? fallback : n;
        },

        safeFloat(value, fallback) {
            if (fallback === undefined) fallback = 0;
            const n = parseFloat(value);
            return isNaN(n) ? fallback : n;
        },

        // ══════════════════════════════════════════════════════════════
        // SAFE ARRAY/SET — Garante que nunca é undefined/null
        // ══════════════════════════════════════════════════════════════
        safeArray(val) {
            if (Array.isArray(val)) return val;
            if (val instanceof Set) return Array.from(val);
            if (val == null) return [];
            return [val];
        },

        safeSet(val) {
            if (val instanceof Set) return val;
            if (Array.isArray(val)) return new Set(val);
            if (val == null) return new Set();
            return new Set([val]);
        },

        // ══════════════════════════════════════════════════════════════
        // SAFE ENGINE — Chama engine com try/catch + fallback
        // ══════════════════════════════════════════════════════════════
        callEngine(engineName, methodName, args, fallbackResult) {
            try {
                const engine = global[engineName];
                if (!engine) {
                    console.warn(`[Guardian] ⚠️ Engine "${engineName}" não carregado`);
                    return fallbackResult !== undefined ? fallbackResult : null;
                }
                if (typeof engine[methodName] !== 'function') {
                    console.warn(`[Guardian] ⚠️ Método "${engineName}.${methodName}" não existe`);
                    return fallbackResult !== undefined ? fallbackResult : null;
                }
                return engine[methodName].apply(engine, args || []);
            } catch (err) {
                console.error(`[Guardian] ❌ Erro em ${engineName}.${methodName}():`, err);
                Guardian.toast(`Erro em ${engineName}: ${err.message}`, 'error');
                return fallbackResult !== undefined ? fallbackResult : null;
            }
        },

        // ══════════════════════════════════════════════════════════════
        // SAFE GAME — Valida que GAMES[key] existe e tem dados mínimos
        // ══════════════════════════════════════════════════════════════
        safeGame(gameKey) {
            if (typeof GAMES === 'undefined') return null;
            const game = GAMES[gameKey];
            if (!game) {
                console.warn(`[Guardian] ⚠️ Loteria "${gameKey}" não encontrada em GAMES`);
                return null;
            }
            // Garantir propriedades mínimas
            return {
                ...game,
                name: game.name || gameKey,
                minBet: game.minBet || 6,
                maxBet: game.maxBet || 20,
                range: game.range || [1, 60],
                price: game.price || 5,
                draw: game.draw || 6,
                color: game.color || '#10B981',
                strategies: game.strategies || [],
                closingLevels: game.closingLevels || [],
            };
        },

        // ══════════════════════════════════════════════════════════════
        // TOAST — Notificações não-bloqueantes (substitui alert())
        // ══════════════════════════════════════════════════════════════
        toast(message, type, duration) {
            if (!type) type = 'info';
            if (!duration) duration = 4000;

            // Criar container se não existir
            if (!Guardian._toastContainer) {
                Guardian._toastContainer = document.createElement('div');
                Guardian._toastContainer.id = 'guardian-toast-container';
                Guardian._toastContainer.style.cssText = 'position:fixed;top:20px;right:20px;z-index:99999;display:flex;flex-direction:column;gap:8px;max-width:380px;pointer-events:none;';
                document.body.appendChild(Guardian._toastContainer);
            }

            const colors = {
                info: { bg: 'rgba(59,130,246,0.95)', border: '#3B82F6', icon: 'ℹ️' },
                success: { bg: 'rgba(34,197,94,0.95)', border: '#22C55E', icon: '✅' },
                warning: { bg: 'rgba(245,158,11,0.95)', border: '#F59E0B', icon: '⚠️' },
                error: { bg: 'rgba(239,68,68,0.95)', border: '#EF4444', icon: '❌' }
            };
            const c = colors[type] || colors.info;

            const toast = document.createElement('div');
            toast.style.cssText = `
                padding:12px 16px;border-radius:12px;background:${c.bg};
                border:1px solid ${c.border};color:#fff;font-size:0.85rem;
                font-weight:600;box-shadow:0 8px 32px rgba(0,0,0,0.4);
                backdrop-filter:blur(10px);pointer-events:auto;cursor:pointer;
                transform:translateX(120%);transition:transform 0.3s ease-out,opacity 0.3s;
                font-family:'Inter','Outfit',sans-serif;display:flex;align-items:center;gap:8px;
            `;
            toast.innerHTML = `<span style="font-size:1.1rem;">${c.icon}</span><span>${message}</span>`;
            toast.onclick = function() { Guardian._removeToast(toast); };

            Guardian._toastContainer.appendChild(toast);

            // Animar entrada
            requestAnimationFrame(function() {
                toast.style.transform = 'translateX(0)';
            });

            // Auto-remover
            setTimeout(function() { Guardian._removeToast(toast); }, duration);
        },

        _removeToast(toast) {
            if (!toast || !toast.parentNode) return;
            toast.style.transform = 'translateX(120%)';
            toast.style.opacity = '0';
            setTimeout(function() {
                if (toast.parentNode) toast.parentNode.removeChild(toast);
            }, 300);
        },

        // ══════════════════════════════════════════════════════════════
        // TIMEOUT MANAGER — Gerencia timeouts com cleanup automático
        // ══════════════════════════════════════════════════════════════
        setTimeout(key, fn, delay) {
            Guardian.clearTimeout(key);
            var id = setTimeout(function() {
                Guardian._timeouts.delete(key);
                try { fn(); } catch(e) {
                    console.error('[Guardian] Timeout error (' + key + '):', e);
                }
            }, delay);
            Guardian._timeouts.set(key, id);
            return id;
        },

        clearTimeout(key) {
            if (Guardian._timeouts.has(key)) {
                clearTimeout(Guardian._timeouts.get(key));
                Guardian._timeouts.delete(key);
            }
        },

        clearAllTimeouts() {
            Guardian._timeouts.forEach(function(id) { clearTimeout(id); });
            Guardian._timeouts.clear();
        },

        // ══════════════════════════════════════════════════════════════
        // RETRY LIMITER — Previne loops infinitos de retry
        // ══════════════════════════════════════════════════════════════
        canRetry(key, maxRetries) {
            if (!maxRetries) maxRetries = 3;
            if (!Guardian._retryCounters[key]) Guardian._retryCounters[key] = 0;
            Guardian._retryCounters[key]++;
            if (Guardian._retryCounters[key] > maxRetries) {
                console.warn('[Guardian] ⛔ Limite de retries atingido para: ' + key);
                return false;
            }
            return true;
        },

        resetRetry(key) {
            delete Guardian._retryCounters[key];
        },

        // ══════════════════════════════════════════════════════════════
        // SAFE LOCALSTORAGE — Operações com try/catch (modo privado!)
        // ══════════════════════════════════════════════════════════════
        storageGet(key, fallback) {
            try {
                var val = localStorage.getItem(key);
                return val !== null ? val : (fallback !== undefined ? fallback : null);
            } catch(e) {
                console.warn('[Guardian] localStorage.getItem falhou:', e.message);
                return fallback !== undefined ? fallback : null;
            }
        },

        storageSet(key, value) {
            try {
                localStorage.setItem(key, value);
                return true;
            } catch(e) {
                console.warn('[Guardian] localStorage.setItem falhou:', e.message);
                return false;
            }
        },

        storageGetJSON(key, fallback) {
            try {
                var val = localStorage.getItem(key);
                return val !== null ? JSON.parse(val) : (fallback !== undefined ? fallback : null);
            } catch(e) {
                console.warn('[Guardian] JSON parse falhou para ' + key + ':', e.message);
                return fallback !== undefined ? fallback : null;
            }
        },

        storageSetJSON(key, value) {
            try {
                localStorage.setItem(key, JSON.stringify(value));
                return true;
            } catch(e) {
                console.warn('[Guardian] JSON stringify falhou para ' + key + ':', e.message);
                return false;
            }
        },

        // ══════════════════════════════════════════════════════════════
        // SAFE SCROLL — scrollIntoView que não crasha
        // ══════════════════════════════════════════════════════════════
        scrollTo(element, options) {
            try {
                if (element && typeof element.scrollIntoView === 'function') {
                    element.scrollIntoView(options || { behavior: 'smooth', block: 'center' });
                }
            } catch(e) {
                // Fallback silencioso
            }
        },

        // ══════════════════════════════════════════════════════════════
        // SAFE CLAMP — Garante valor dentro de limites
        // ══════════════════════════════════════════════════════════════
        clamp(value, min, max) {
            var v = Guardian.safeInt(value, min);
            return Math.max(min, Math.min(max, v));
        }
    };

    // ══════════════════════════════════════════════════════════════
    // ERROR BOUNDARY GLOBAL — Captura erros não tratados
    // ══════════════════════════════════════════════════════════════
    global.addEventListener('error', function(event) {
        Guardian._errorCount++;
        if (Guardian._errorCount > Guardian._maxErrors) return;

        var msg = event.message || 'Erro desconhecido';
        var file = event.filename ? event.filename.split('/').pop() : '?';
        var line = event.lineno || '?';

        console.error('[Guardian] 🛡️ Erro capturado: ' + msg + ' (' + file + ':' + line + ')');

        // Não mostrar toast para erros menores (CSS, rede, etc.)
        if (msg.indexOf('ResizeObserver') !== -1) return;
        if (msg.indexOf('Script error') !== -1) return;
        if (msg.indexOf('Loading chunk') !== -1) return;

        // Mostrar toast apenas para erros em nossos arquivos
        if (file.indexOf('ui.js') !== -1 || file.indexOf('main.js') !== -1 ||
            file.indexOf('stats.js') !== -1 || file.indexOf('engine') !== -1) {
            Guardian.toast('Erro: ' + msg.substring(0, 80), 'error', 5000);
        }
    });

    global.addEventListener('unhandledrejection', function(event) {
        Guardian._errorCount++;
        if (Guardian._errorCount > Guardian._maxErrors) return;

        var reason = event.reason;
        var msg = reason ? (reason.message || String(reason)) : 'Promise rejeitada';

        console.error('[Guardian] 🛡️ Promise não tratada:', msg);

        // Não alertar para erros de rede (API fora do ar)
        if (msg.indexOf('fetch') !== -1 || msg.indexOf('NetworkError') !== -1 ||
            msg.indexOf('AbortError') !== -1 || msg.indexOf('Failed to fetch') !== -1) {
            return;
        }

        Guardian.toast('Erro async: ' + msg.substring(0, 80), 'warning', 4000);
    });

    // ══════════════════════════════════════════════════════════════
    // EXPOR GLOBALMENTE
    // ══════════════════════════════════════════════════════════════
    global.Guardian = Guardian;
    global.$$ = Guardian.$.bind(Guardian);

    console.log('%c[Guardian] 🛡️ Camada de proteção v1.0 ativada', 'color:#22C55E;font-weight:bold;');

})(typeof window !== 'undefined' ? window : this);
