// ======================================================
// StatsService - Busca e gerencia dados das loterias
// Versão: 20260318 - Correção de cache e compatibilidade
// ======================================================

class StatsService {

    static async ensureHistory(gameType) {
        // Se já carregou histórico E já tem prêmio, retorna
        if (this.historyStore[gameType] && this.historyStore[gameType].length > 0) {
            // Mesmo com cache, tenta atualizar prêmios em background
            this._refreshPrizesInBackground(gameType);
            return;
        }

        // Evita chamadas duplicadas
        if (this.loadingPromises[gameType]) {
            return this.loadingPromises[gameType];
        }

        this.loadingPromises[gameType] = this._loadHistory(gameType);
        await this.loadingPromises[gameType];
        delete this.loadingPromises[gameType];
    }

    static async _refreshPrizesInBackground(gameType) {
        var now = Date.now();
        // Máximo 1x a cada 2 minutos por jogo
        if (this._lastPrizeRefresh[gameType] && (now - this._lastPrizeRefresh[gameType]) < 120000) {
            return;
        }
        this._lastPrizeRefresh[gameType] = now;

        try {
            await this._fetchLatestFromAPIs(gameType);
        } catch(e) {
            // Silencioso em background
        }
    }

    static async _loadHistory(gameType) {
        // 1. RESTAURAR PRÊMIOS DO CACHE LOCAL (localStorage)
        try {
            var savedPrize = localStorage.getItem('b2b_prize_' + gameType);
            if (savedPrize) {
                var parsed = JSON.parse(savedPrize);
                // Usar se tiver menos de 24h
                if (parsed && parsed.lastUpdated && (Date.now() - parsed.lastUpdated) < 86400000) {
                    this.prizeStore[gameType] = parsed;
                    console.log('[StatsService] 💾 Prêmio restaurado do cache local: ' + gameType + ' = R$ ' + (parsed.estimatedPrize || 0).toLocaleString('pt-BR'));
                }
            }
        } catch(e) {
            console.warn('[StatsService] localStorage indisponível para ' + gameType + ':', e.message);
        }

        // 2. CARREGAR HISTÓRICO DA BASE ESTÁTICA
        if (typeof REAL_HISTORY_DB !== 'undefined' && REAL_HISTORY_DB[gameType]) {
            this.historyStore[gameType] = REAL_HISTORY_DB[gameType].slice();
        } else {
            this.historyStore[gameType] = [];
        }

        // 2. BUSCAR DA API (com fallback para múltiplas APIs)
        try {
            var latest = await this._fetchLatestFromAPIs(gameType);
            if (latest && latest.drawNumber) {
                var existingIndex = -1;
                for (var i = 0; i < this.historyStore[gameType].length; i++) {
                    if (this.historyStore[gameType][i].drawNumber === latest.drawNumber) {
                        existingIndex = i;
                        break;
                    }
                }
                if (existingIndex === -1) {
                    this.historyStore[gameType].unshift(latest);
                } else {
                    this.historyStore[gameType][existingIndex] = latest;
                }

                // v12.9 (Auto-Cura da Base de Dados)
                // O sistema vai rastrear e cobrir um buraco de até 60 sorteios ausentes
                // entre a base estática local e a API da Caixa sempre que for aberto,
                // garantindo inteligência de escolhas sempre 100% atualizada.
                await this._fetchPreviousDraws(gameType, latest.drawNumber, 60);

                // Ordenar: mais recente primeiro
                this.historyStore[gameType].sort(function(a, b) { return b.drawNumber - a.drawNumber; });

                // Remover duplicatas
                var seen = {};
                this.historyStore[gameType] = this.historyStore[gameType].filter(function(item) {
                    if (seen[item.drawNumber]) return false;
                    seen[item.drawNumber] = true;
                    return true;
                });
            }
        } catch (e) {
            console.warn('[StatsService] API falhou para ' + gameType + '. Usando dados offline.');
        }

        // 3. Fallback se vazio
        if (this.historyStore[gameType].length === 0) {
            this._generateFallbackHistory(gameType);
        }
    }

    // Tenta buscar de MÚLTIPLAS APIs em sequência
    static async _fetchLatestFromAPIs(gameType) {
        // Mapear gameKey interno para o nome de rota da API Caixa
        var caixaRoute = { milionaria: 'maismilionaria' }[gameType] || gameType;
        var apis;
        if (gameType === 'loteca') {
            apis = [
                'https://servicebus2.caixa.gov.br/portaldeloterias/api/loteca',
                'https://loteriascaixa-api.herokuapp.com/api/loteca/latest'
            ];
        } else {
            apis = [
                'https://loteriascaixa-api.herokuapp.com/api/' + gameType + '/latest',
                'https://servicebus2.caixa.gov.br/portaldeloterias/api/' + caixaRoute
            ];
        }

        for (var a = 0; a < apis.length; a++) {
            var controller = null;
            var timeoutId = null;
            try {
                controller = new AbortController();
                timeoutId = setTimeout(function() { try { controller.abort(); } catch(ae) {} }, 8000);

                var response = await fetch(apis[a], {
                    signal: controller.signal,
                    cache: 'no-store',  // FORÇAR busca fresca, sem cache!
                    headers: { 'Accept': 'application/json' }
                });
                clearTimeout(timeoutId);
                timeoutId = null;

                if (!response.ok) continue;

                var data = await response.json();

                // Compatibilidade com formato da API da Caixa
                if (data && !data.concurso && data.numero) data.concurso = data.numero;
                if (data && !data.dezenas && data.listaDezenas) data.dezenas = data.listaDezenas;

                var result = this._parseAPIResponse(data, gameType);
                if (result) {
                    console.log('[StatsService] ✅ ' + gameType + ' carregado. Prêmio: R$ ' + 
                        ((this.prizeStore[gameType] && this.prizeStore[gameType].estimatedPrize) || 0).toLocaleString('pt-BR'));
                    return result;
                }
            } catch (e) {
                console.warn('[StatsService] API #' + (a+1) + ' falhou para ' + gameType + ': ' + (e.name === 'AbortError' ? 'timeout' : e.message));
                continue;
            } finally {
                if (timeoutId) clearTimeout(timeoutId);
            }
        }
        return null;
    }

    static async _fetchPreviousDraws(gameType, latestDraw, count) {
        var missingDraws = [];
        for (var i = 1; i <= count; i++) {
            var drawNum = latestDraw - i;
            var exists = false;
            for (var j = 0; j < this.historyStore[gameType].length; j++) {
                if (this.historyStore[gameType][j].drawNumber === drawNum) {
                    exists = true;
                    break;
                }
            }
            if (!exists) {
                missingDraws.push(drawNum);
            }
        }

        // Buscar em pequenos lotes de 5 para estabilidade e evitar timeouts da API
        var self = this;
        for (var b = 0; b < missingDraws.length; b += 5) {
            var batch = missingDraws.slice(b, b + 5);
            var batchPromises = batch.map(function(num) {
                return self._fetchSingleDraw(gameType, num).catch(function() { return null; });
            });
            var batchResults = await Promise.all(batchPromises);
            for (var r = 0; r < batchResults.length; r++) {
                if (batchResults[r]) {
                    self.historyStore[gameType].push(batchResults[r]);
                }
            }
        }
    }

    static async _fetchSingleDraw(gameType, drawNumber) {
        var caixaRoute2 = { milionaria: 'maismilionaria' }[gameType] || gameType;
        var apis;
        if (gameType === 'loteca') {
            apis = [
                'https://servicebus2.caixa.gov.br/portaldeloterias/api/loteca/' + drawNumber,
                'https://loteriascaixa-api.herokuapp.com/api/loteca/' + drawNumber
            ];
        } else {
            apis = [
                'https://loteriascaixa-api.herokuapp.com/api/' + gameType + '/' + drawNumber,
                'https://servicebus2.caixa.gov.br/portaldeloterias/api/' + caixaRoute2 + '/' + drawNumber
            ];
        }

        for (var a = 0; a < apis.length; a++) {
            try {
                var controller = new AbortController();
                var timeoutId = setTimeout(function() { controller.abort(); }, 5000);

                var response = await fetch(apis[a], {
                    signal: controller.signal,
                    cache: 'no-store',
                    headers: { 'Accept': 'application/json' }
                });
                clearTimeout(timeoutId);
                if (!response.ok) continue;

                var data = await response.json();
                if (data && !data.concurso && data.numero) data.concurso = data.numero;
                if (data && !data.dezenas && data.listaDezenas) data.dezenas = data.listaDezenas;

                return this._parseAPIResponse(data, gameType);
            } catch (e) {
                continue;
            }
        }
        return null;
    }

    static _parseAPIResponse(data, gameType) {
        // Normalizar campos - API Caixa usa 'numero' e 'listaDezenas' e 'dezenasSorteadasOrdemSorteio'
        if (data && !data.concurso && data.numero) data.concurso = data.numero;
        if (data && !data.dezenas && data.listaDezenas) data.dezenas = data.listaDezenas;
        if (data && !data.dezenas && data.dezenasSorteadasOrdemSorteio) data.dezenas = data.dezenasSorteadasOrdemSorteio;

        // ★ Suporte especializado para LOTECA (14 Jogos de Futebol da Caixa)
        var isLoteca = (gameType === 'loteca') || (data.tipoJogo && String(data.tipoJogo).toLowerCase().includes('loteca'));
        var sortedMatches = null;
        if (isLoteca) {
            if (data.listaResultadoEquipeEsportiva && Array.isArray(data.listaResultadoEquipeEsportiva)) {
                sortedMatches = data.listaResultadoEquipeEsportiva.slice().sort(function(a, b) {
                    return (a.nuSequencial || 0) - (b.nuSequencial || 0);
                });
                var cols = sortedMatches.map(function(m) {
                    if (m.resultado) return String(m.resultado).toUpperCase().trim();
                    var g1 = (m.nuGolEquipeUm !== undefined && m.nuGolEquipeUm !== null) ? parseInt(m.nuGolEquipeUm) : null;
                    var g2 = (m.nuGolEquipeDois !== undefined && m.nuGolEquipeDois !== null) ? parseInt(m.nuGolEquipeDois) : null;
                    if (g1 !== null && g2 !== null) {
                        return g1 > g2 ? '1' : (g2 > g1 ? '2' : 'X');
                    }
                    return '1';
                });
                data.dezenas = cols;
                if (!data.premiacoes && data.listaRateioPremio) {
                    data.premiacoes = data.listaRateioPremio;
                }
            }
        }

        if (!data || !data.concurso || !data.dezenas) return null;

        var drawNum = parseInt(data.concurso);
        var storageKey = gameType || data.loteria;

        // SÓ atualizar prêmio se este concurso for MAIS RECENTE que o já armazenado
        var currentStored = this.prizeStore[storageKey];
        if (!currentStored || drawNum >= currentStored.currentDraw) {
            var estimated = data.valorEstimadoProximoConcurso || data.valorAcumuladoProximoConcurso || data.valorAcumulado || 0;

            this.prizeStore[storageKey] = {
                estimatedPrize: estimated,
                accumulatedPrize: data.valorAcumuladoProximoConcurso || 0,
                accumulated: data.acumulou || false,
                nextDraw: data.proximoConcurso || (drawNum + 1),
                nextDrawDate: data.dataProximoConcurso || null,
                currentDraw: drawNum,
                prizes: data.premiacoes || [],
                lastUpdated: Date.now()
            };

            // SALVAR NO CACHE LOCAL (localStorage) para próximas sessões
            try {
                localStorage.setItem('b2b_prize_' + storageKey, JSON.stringify(this.prizeStore[storageKey]));
            } catch(e) { /* localStorage cheio ou indisponível */ }

            console.log('[StatsService] ✅ Prêmio atualizado: ' + storageKey + ' (concurso ' + drawNum + ') = R$ ' + (estimated || 0).toLocaleString('pt-BR'));
        }

        var rawNumbers = isLoteca
            ? data.dezenas.map(function(c) { return String(c).toUpperCase(); })
            : data.dezenas.map(function(n) { return parseInt(n); });
        var result = { drawNumber: parseInt(data.concurso) };

        if (isLoteca) {
            result.numbers = rawNumbers;
            if (sortedMatches || data.listaResultadoEquipeEsportiva) {
                result.matches = sortedMatches || data.listaResultadoEquipeEsportiva;
            }
            if (data.dataApuracao) result.date = data.dataApuracao;
            if (data.premiacoes) result.prizes = data.premiacoes;
            return result;
        }

        // Data do sorteio para todas as loterias
        if (data.dataApuracao) {
            result.date = data.dataApuracao;
        } else if (data.data) {
            result.date = data.data;
        }

        // ★ Preservar dados extras da API (Mês da Sorte / Time do Coração)
        if (data.nomeTimeCoracaoMesSorte || data.mesSorte) {
            result.mesSorte = data.nomeTimeCoracaoMesSorte || data.mesSorte;
        }
        if (data.nomeTimeCoracaoMesSorte || data.timeCoracao) {
            result.timeCoracao = (data.nomeTimeCoracaoMesSorte || data.timeCoracao || '').trim();
        }

        if (gameType === 'supersete' || (data.tipoJogo && String(data.tipoJogo).toUpperCase().includes('SUPER_SETE'))) {
            // Super Sete: exatamente 7 colunas (C1 a C7) na ordem oficial, dígitos de 0 a 9 com repetições permitidas!
            result.numbers = rawNumbers.slice(0, 7);
        } else if (gameType === 'duplasena') {
            // Dupla Sena: pode vir como 12 números juntos, ou em dezenas + dezenas2 separados
            if (data.dezenas2 && data.dezenas2.length > 0) {
                // Formato com dezenas2 separado (algumas APIs)
                var sort1 = rawNumbers.slice().sort(function(a, b) { return a - b; });
                var sort2 = data.dezenas2.map(function(n) { return parseInt(n); }).sort(function(a, b) { return a - b; });
                result.numbers  = sort1;
                result.numbers2 = sort2;
            } else if (rawNumbers.length >= 12) {
                // 12 números juntos (api hercules)
                result.numbers  = rawNumbers.slice(0, 6).sort(function(a, b) { return a - b; });
                result.numbers2 = rawNumbers.slice(6, 12).sort(function(a, b) { return a - b; });
            } else if (rawNumbers.length === 6) {
                // Apenas 1 sorteio retornado pela API (incompleto)
                result.numbers  = rawNumbers.slice().sort(function(a, b) { return a - b; });
                result.numbers2 = [];
            } else {
                // Qualquer outro caso: dividir ao meio
                var half = Math.floor(rawNumbers.length / 2);
                result.numbers  = rawNumbers.slice(0, half).sort(function(a, b) { return a - b; });
                result.numbers2 = rawNumbers.slice(half).sort(function(a, b) { return a - b; });
            }
        } else {
            // Outros jogos: deduplicar e ordenar
            var uniqueNumbers = [];
            var seen = {};
            for (var u = 0; u < rawNumbers.length; u++) {
                if (!seen[rawNumbers[u]]) {
                    seen[rawNumbers[u]] = true;
                    uniqueNumbers.push(rawNumbers[u]);
                }
            }
            uniqueNumbers.sort(function(a, b) { return a - b; });
            result.numbers = uniqueNumbers;
        }

        // Salvar trevos para +Milionaria
        if (gameType === 'milionaria') {
            var rawTrevos = data.trevosSorteados || data.listaDezenasSegundoSorteio || data.trevos || [];
            if (rawTrevos && rawTrevos.length > 0) {
                result.trevos = rawTrevos.map(function(t) { return parseInt(t); }).sort(function(a,b){return a-b;});
            }
        }

        return result;
    }

    static getPrizeInfo(gameType) {
        return this.prizeStore[gameType] || null;
    }

    // Compatibilidade: método antigo
    static async fetchLatestFromAPI(gameType) {
        return this._fetchLatestFromAPIs(gameType);
    }

    // Compatibilidade: método antigo
    static async fetchPreviousDraws(gameType, latestDraw, count) {
        return this._fetchPreviousDraws(gameType, latestDraw, count || 5);
    }

    static _generateFallbackHistory(gameType) {
        var game = typeof GAMES !== 'undefined' ? GAMES[gameType] : null;
        if (!game) return;
        var startDraw = 3000;
        for (var i = 0; i < 16; i++) {
            this.historyStore[gameType].push({
                drawNumber: startDraw - i,
                numbers: this.simulateDraw(game)
            });
        }
    }

    static getRecentResults(gameType, count) {
        if (!count) count = 5;
        if (!this.historyStore[gameType] || this.historyStore[gameType].length === 0) {
            // Tenta carregar sem bloquear (async fire-and-forget)
            try { this.ensureHistory(gameType); } catch(e) {}
        }
        return (this.historyStore[gameType] || []).slice(0, count);
    }

    static getResultByDrawNumber(gameType, drawNumber) {
        if (!this.historyStore[gameType]) {
            this.ensureHistory(gameType);
        }
        var history = this.historyStore[gameType] || [];
        for (var i = 0; i < history.length; i++) {
            if (history[i].drawNumber == drawNumber) return history[i];
        }
        return null;
    }

    static getStats(gameType, rangeAnalysis) {
        var game = typeof GAMES !== 'undefined' ? GAMES[gameType] : null;
        if (!game) return { hot: [], cold: [] };
        if (gameType === 'loteca') return { hot: [], cold: [], totalDraws: 0 };

        if (!this.historyStore[gameType]) this.ensureHistory(gameType);
        var history = this.historyStore[gameType] || [];

        var analyzesCount = (!rangeAnalysis || rangeAnalysis === 0)
            ? history.length
            : Math.min(rangeAnalysis, history.length);

        var recentDraws = history.slice(0, analyzesCount);
        if (recentDraws.length === 0) return { hot: [], cold: [], totalDraws: 0 };

        // Contar quantas vezes cada número saiu
        var countMap = {};
        for (var i = game.range[0]; i <= game.range[1]; i++) countMap[i] = 0;

        recentDraws.forEach(function(item) {
            (item.numbers  || []).forEach(function(n) { if (countMap[n] !== undefined) countMap[n]++; });
            (item.numbers2 || []).forEach(function(n) { if (countMap[n] !== undefined) countMap[n]++; });
        });

        // Delay: há quantos sorteios o número não sai
        var delayMap = {};
        var fullHist = history;
        for (var n = game.range[0]; n <= game.range[1]; n++) delayMap[n] = fullHist.length;
        for (var h = 0; h < fullHist.length; h++) {
            var nums = (fullHist[h].numbers || []).concat(fullHist[h].numbers2 || []);
            nums.forEach(function(n) {
                if (n >= game.range[0] && n <= game.range[1] && delayMap[n] === fullHist.length)
                    delayMap[n] = h;
            });
        }

        // Criar lista ordenada pela quantidade de sorteios (desc)
        var sorted = Object.keys(countMap).map(function(num) {
            var n = parseInt(num);
            return { number: n, count: countMap[n], delay: delayMap[n] !== undefined ? delayMap[n] : 0 };
        }).sort(function(a, b) {
            if (b.count !== a.count) return b.count - a.count; // mais sorteados primeiro
            return a.delay - b.delay;                           // desempate: menos atrasado primeiro
        });

        var half = Math.ceil(sorted.length / 2);

        // HOT: top 50% — do mais sorteado ao menos sorteado
        var hot = sorted.slice(0, half);

        // COLD: bottom 50% — do menos sorteado ao mais sorteado
        var cold = sorted.slice(half).reverse();

        return { hot: hot, cold: cold, totalDraws: analyzesCount };
    }

    static simulateDraw(game) {
        if (!game) return [];
        var set = new Set();
        while (set.size < game.draw) {
            set.add(Math.floor(Math.random() * (game.range[1] - game.range[0] + 1)) + game.range[0]);
        }
        return Array.from(set).sort(function(a, b) { return a - b; });
    }

    static mockRealWeights(game) {
        return this.simulateDraw(game);
    }
}

// Inicializar propriedades estáticas (compatível com todos os navegadores)
StatsService.historyStore = {};
StatsService.loadingPromises = {};
StatsService.prizeStore = {};
StatsService._lastPrizeRefresh = {};
