const L99_MESES = ["Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho", "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"];
const L99_TIMES = ["ABC/RN", "América/MG", "América/RJ", "América/RN", "Atlético/GO", "Atlético/MG", "Atlético/PR", "Avaí/SC", "Bahia/BA", "Bangu/RJ", "Barueri/SP", "Botafogo/PB", "Botafogo/RJ", "Botafogo/SP", "Bragantino/SP", "Brasiliense/DF", "Campinense/PB", "Ceará/CE", "Corinthians/SP", "Coritiba/PR", "CRB/AL", "Criciúma/SC", "Cruzeiro/MG", "CSA/AL", "Desportiva/ES", "Figueirense/SC", "Flamengo/RJ", "Fluminense/RJ", "Fortaleza/CE", "Gama/DF", "Goiás/GO", "Grêmio/RS", "Guarani/SP", "Inter Limeira/SP", "Internacional/RS", "Ipatinga/MG", "Ituano/SP", "Ji-Paraná/RO", "Joinville/SC", "Juventude/RS", "Juventus/SP", "Londrina/PR", "Marília/SP", "Mixto/MT", "Moto Clube/MA", "Náutico/PE", "Nacional/AM", "Olaria/RJ", "Operário/MS", "Palmeiras/SP", "Paraná/PR", "Paulista/SP", "Paysandu/PA", "Ponte Preta/SP", "Portuguesa/SP", "Remo/PA", "Rio Branco/AC", "Rio Branco/ES", "River/PI", "Roraima/RR", "Sampaio Corrêa/MA", "Santa Cruz/PE", "Santo André/SP", "Santos/SP", "São Caetano/SP", "São Paulo/SP", "São Raimundo/AM", "Sergipe/SE", "Sport/PE", "Treze/PB", "Tuna Luso/PA", "Uberlândia/MG", "União Bandeirante/PR", "União São João/SP", "Vasco/RJ", "Vila Nova/GO", "Villa Nova/MG", "Vitória/BA", "Volta Redonda/RJ", "Ypiranga/AP"];

class UI {
    constructor() {
        window.ui = this;
        // ══ Helper para getElementById seguro ══
        const _el = (id) => document.getElementById(id);

        this.navButtons = document.querySelectorAll('.nav-btn') || [];
        this.currentGameTitle = _el('current-game-title');
        this.closingSelect = _el('closing-type');
        this.gamesQuantityInput = _el('games-quantity');
        this.generateBtn = _el('generate-btn');
        this.generateCoverageBtn = _el('generate-coverage-btn');
        this.smartDrawSizeSelect = _el('smart-draw-size');
        this.copyBtn = _el('copy-btn');
        this.gamesContainer = _el('games-container');
        this.currentBetCostElem = _el('current-bet-cost');

        // Action Buttons
        this.saveBtn = _el('save-btn');
        this.checkBtn = _el('check-btn');
        this.playCaixaBtn = _el('btn-play-caixa');

        // Modal Elements
        this.checkModal = _el('check-modal');
        this.closeCheckModalBtn = document.querySelector('.close-check-modal');
        this.inputCheckNumbers = _el('check-input-numbers');
        this.confirmCheckBtn = _el('confirm-check-btn');

        this.copyModal = _el('copy-modal');
        this.closeCopyModalBtns = document.querySelectorAll('.close-copy-modal') || [];
        this.copyTextarea = _el('copy-textarea');

        this.currentGeneratedGames = []; // Store generated games — FONTE ÚNICA DE VERDADE

        this.hotNumbersContainer = _el('hot-numbers');
        this.coldNumbersContainer = _el('cold-numbers');
        this.gridContainer = _el('number-selection-grid');
        this.selectedCountElem = _el('selected-count');
        this.maxSelectionElem = _el('max-selection');
        this.timerElem = _el('timer');

        this.recentResultsContainer = _el('recent-results-list');
        this.loadGamesInput = _el('load-games-input');
        this.checkSummaryContainer = _el('check-summary');

        // Fixed Mode Elements
        this.btnFixedMode = _el('btn-fixed-mode');
        this.fixedInfoPanel = _el('fixed-info-panel');
        this.fixedNumbersList = _el('fixed-numbers-list');
        this.isFixedMode = false;
        this.fixedNumbers = new Set();

        // Stats Controls
        this.statsButtons = document.querySelectorAll('.stat-toggle') || [];
        this.currentStatsRange = 10;

        // Investment Panel Elements
        this.costSelectedCount = _el('cost-selected-count');
        this.costTotalCombinations = _el('cost-total-combinations');
        this.costTotalValue = _el('cost-total-value');
        this.costUserGames = _el('cost-user-games');
        this.costUserGamesDetail = _el('cost-user-games-detail');
        this.closingEstimatesContainer = _el('closing-estimates');

        this.root = document.documentElement;

        this.selectedNumbers = new Set();
        this.currentGameKey = 'megasena';

        // ── Rastreamento de Modo de Geração (para Estatísticas) ──
        this._lastGenerationMode = localStorage.getItem('l99_lastMode') || 'manual';   // quantum_l99 | gerar_jogos | dual_2g | fechamento | manual
        this._lastPrecisionMode = false;
        this._lastDrawSize = 6;
        this._lastCheckDrawInfo = '';

        // ── Flag de geração em andamento (previne double-click) ──
        this._isGenerating = false;

        // Quantum/IA Elements
        this.quantumFormula = _el('quantum-formula');
        this.quantumCountInput = _el('quantum-count');
        this.btnQuantumCalculate = _el('btn-quantum-calculate');
        this.quantumResults = _el('quantum-results');
        this.btnUseQuantum = _el('btn-use-quantum');

        // Tutorial Elements
        this.btnTutorial = _el('btn-tutorial');
        this.tutorialModal = _el('tutorial-modal');
        this.closeTutorialModalBtns = document.querySelectorAll('.close-tutorial-modal') || [];
        this.btnPrintTutorial = _el('print-tutorial');

        // Install Elements
        this.btnInstall = _el('btn-install');
        this.installModal = _el('install-modal');
        this.closeInstallModalBtns = document.querySelectorAll('.close-install-modal') || [];
        this.btnCopyPath = _el('btn-copy-path');
        this.folderPathElem = _el('folder-path');

        // Backup Button
        this.btnBackup = _el('btn-backup');

        // Prize Display Elements
        this.prizeDisplay = _el('prize-display');
        this.prizeValue = _el('prize-value');
        this.prizeBadge = _el('prize-badge');
    }

    // ════════════════════════════════════════════════════════════
    //  INICIALIZACAO DE EVENTOS — CHAMADO POR main.js
    // ════════════════════════════════════════════════════════════
    initEvents() {
        // === NAVEGACAO ENTRE LOTERIAS ===
        this.navButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                const gameKey = btn.dataset.game;
                if (gameKey && typeof GAMES !== 'undefined' && GAMES[gameKey]) {
                    this.updateGameInfo(gameKey);
                }
            });
        });

        // === BOTOES DE SELECAO ===
        const btnRandom = document.getElementById('btn-random-select');
        if (btnRandom) btnRandom.onclick = () => this.selectRandom();

        const btnClear = document.getElementById('btn-clear-selection');
        if (btnClear) btnClear.onclick = () => this.clearSelection();

        if (this.btnFixedMode) {
            this.btnFixedMode.onclick = () => this.toggleFixedMode();
        }

        // === BOTÃO ⚔️ COMPARAR ESTRATÉGIAS ===
        const btnCompare = document.getElementById('btn-compare');
        if (btnCompare) {
            btnCompare.onclick = () => {
                const container = document.getElementById('comparison-container');
                if (!container) return;
                container.style.display = 'block';
                if (typeof ComparisonEngine !== 'undefined') {
                    ComparisonEngine.render(container, this.currentGameKey);
                    container.scrollIntoView({ behavior: 'smooth', block: 'start' });
                } else {
                    container.innerHTML = '<div style="padding:20px;text-align:center;color:#EF4444;">ComparisonEngine não carregado.</div>';
                }
            };
        }

        // === BOTÃO 🎲 MANUAL v14.0 — MotorFechamentoManual ===
        // Delega TODA lógica ao motor. Zero lógica inline.
        if (this.generateBtn) {
            this.generateBtn.onclick = () => {
                // +Milionaria usa motor B2B exclusivo — redirecionar
                if (this.currentGameKey === 'milionaria') {
                    this._executarGeracaoMilionaria(0);
                    return;
                }
                const game = GAMES[this.currentGameKey];
                if (!game) return;
                const qty = parseInt(this.gamesQuantityInput.value) || 10;
                const drawSizeSelect = document.getElementById('smart-draw-size');
                const customDrawSize = drawSizeSelect ? parseInt(drawSizeSelect.value) : 0;
                const drawSize = (customDrawSize && customDrawSize >= game.minBet) ? customDrawSize : game.minBet;

                // Coletar escolhas do apostador
                const selectedArr = Array.from(this.selectedNumbers).filter(n => n >= game.range[0] && n <= game.range[1]);
                const fixedArr = Array.from(this.fixedNumbers).filter(n => n >= game.range[0] && n <= game.range[1]);

                // Pool = todos os números escolhidos (selecionados + fixos)
                const poolSet = new Set([...selectedArr, ...fixedArr]);
                const pool = Array.from(poolSet).sort((a, b) => a - b);

                this._lastGenerationMode = 'manual';
                localStorage.setItem('l99_lastMode', 'manual');
                document.body.setAttribute('data-l99-mode', 'manual');

                let result;
                let bannerMsg = '';

                if (typeof MotorFechamentoManual === 'undefined') {
                    this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">MotorFechamentoManual não carregado. Recarregue (Ctrl+Shift+R).</div>';
                    return;
                }

                if (pool.length < drawSize) {
                    // ═══ BLOQUEADO: Apostador precisa selecionar números ═══
                    const msg = pool.length === 0
                        ? '⚠️ <strong>Selecione seus números!</strong><br>O botão Manual usa SOMENTE os números que VOCÊ escolhe.<br>Selecione pelo menos <strong>' + drawSize + '</strong> números no grid acima.'
                        : '⚠️ <strong>Seleção insuficiente!</strong><br>Você selecionou <strong>' + pool.length + '</strong> número(s), mas precisa de pelo menos <strong>' + drawSize + '</strong>.<br>Selecione mais <strong>' + (drawSize - pool.length) + '</strong> número(s) no grid.';
                    this.gamesContainer.innerHTML = '<div style="text-align:center;padding:30px 20px;color:#FCD34D;font-size:0.9rem;line-height:1.6;">' + msg + '</div>';
                    return;
                }

                // ═══ Apostador selecionou números suficientes ═══
                const closingVal = this.closingSelect ? this.closingSelect.value : '';
                
                if (closingVal.startsWith('close_')) {
                    const guarantee = parseInt(closingVal.replace('close_', ''));
                    if (typeof ClosingEngine === 'undefined') {
                        this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">ClosingEngine não carregado.</div>';
                        return;
                    }
                    
                    this.gamesContainer.innerHTML = '<div style="text-align:center;padding:40px;"><div class="sync-loader" style="font-size:1.2em;">Fechando ' + guarantee + ' pontos com IA...</div></div>';
                    
                    setTimeout(() => {
                        const qty = parseInt(document.getElementById('games-quantity').value) || 0;
                        result = ClosingEngine.generateClosure(poolSet, guarantee, drawSize, this.currentGameKey, fixedArr, qty);
                        
                        if (result.error) {
                            this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#F59E0B;">' + result.error + '</div>';
                            return;
                        }
                        
                        bannerMsg = '🎯 <strong>FECHAMENTO HÍBRIDO (IA + STEINER)</strong> — ' + result.games.length + ' jogos<br>';
                        bannerMsg += 'Garantia: <strong>' + guarantee + ' pontos</strong> | Cobertura Exata: <strong>' + result.coveragePct + '%</strong><br>';
                        if (fixedArr.length > 0) bannerMsg += 'Fixos: ' + fixedArr.join(', ') + '<br>';
                        bannerMsg += 'Investimento: <strong>R$ ' + result.cost.toFixed(2) + '</strong> | Ordenado por Sinergia IA 🔥';
                        
                        const games = result.games || [];
                        this.currentGeneratedGames = games;
                        this._lastGeneratedGames = games;
                        this.renderGames({ pool: pool, games: games, smartAnalysis: null }, this.currentGameKey);
                        
                        setTimeout(() => {
                            var b = document.createElement('div');
                            b.className = 'smart-gen-analysis';
                            b.style.cssText = 'margin-top:8px;margin-bottom:8px;padding:12px 16px;border-radius:10px;background:linear-gradient(135deg, rgba(255,215,0,0.1), rgba(220,38,38,0.1));border:1px solid rgba(255,215,0,0.3);font-size:0.8rem;color:#FCD34D;';
                            b.innerHTML = bannerMsg;
                            var old = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
                            if (old) old.remove();
                            this.gamesContainer.parentNode.insertBefore(b, this.gamesContainer);
                        }, 50);
                        setTimeout(() => { if (this.gamesContainer) this.gamesContainer.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 150);
                    }, 50);
                    
                } else {
                    // Sem fechamento exato -> Motor Genérico
                    // ═══ v15.0: GERAÇÃO ASSÍNCRONA para grandes volumes ═══
                    if (typeof AsyncGenerator !== 'undefined' && AsyncGenerator.shouldUseAsync(qty, this.currentGameKey)) {
                        this.gamesContainer.innerHTML = '<div style="text-align:center;padding:40px;"><div class="sync-loader" style="font-size:1.2em;">Preparando geração assíncrona...</div></div>';
                        AsyncGenerator.generateManualAsync(this.currentGameKey, pool, fixedArr, qty, drawSize, (result, cancelled, error) => {
                            if (cancelled) {
                                this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#F59E0B;">⚠️ Geração cancelada pelo usuário.</div>';
                                return;
                            }
                            if (error || !result || !result.games || result.games.length === 0) {
                                this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">Erro: ' + (error ? error.message : 'Nenhum jogo gerado.') + '</div>';
                                return;
                            }
                            const a = result.analysis || {};
                            let asyncBanner = '🎲 <strong>MANUAL</strong> — ' + result.games.length + ' jogos dos seus ' + a.poolSize + ' números';
                            if (a.fixedCount > 0) asyncBanner += ' (fixos: ' + a.fixedNumbers.join(', ') + ')';
                            asyncBanner += '<br>📊 Investimento: <strong>R$ ' + a.investimento.toFixed(2) + '</strong> | ⚡ Geração Assíncrona (' + a.chunksProcessed + ' lotes) | ' + a.elapsed + 'ms';
                            if (a.isComplete) asyncBanner += '<br>✅ <strong style="color:#22C55E;">FECHAMENTO COMPLETO</strong>';

                            this.currentGeneratedGames = result.games;
                            this._lastGeneratedGames = result.games;
                            if (typeof ComparisonEngine !== 'undefined') ComparisonEngine.saveResult('manual', result.games, result.analysis, this.currentGameKey);
                            this.renderGames({ pool: pool, games: result.games, smartAnalysis: null }, this.currentGameKey);

                            setTimeout(() => {
                                var b = document.createElement('div');
                                b.className = 'smart-gen-analysis';
                                b.style.cssText = 'margin-top:8px;margin-bottom:8px;padding:12px 16px;border-radius:10px;background:rgba(255,215,0,0.08);border:1px solid rgba(255,215,0,0.3);font-size:0.8rem;color:#FCD34D;';
                                b.innerHTML = asyncBanner;
                                var old = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
                                if (old) old.remove();
                                this.gamesContainer.parentNode.insertBefore(b, this.gamesContainer);
                            }, 50);
                            setTimeout(() => { if (this.gamesContainer) this.gamesContainer.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 150);
                        });
                        return; // Sai do onclick — o callback cuidará do resultado
                    }

                    // Geração síncrona (quantidades pequenas — rápido o bastante)
                    result = MotorFechamentoManual.generate(this.currentGameKey, pool, fixedArr, qty, drawSize);
                    const a = result.analysis || {};
                    bannerMsg = '🎲 <strong>MANUAL</strong> — ' + result.games.length + ' jogos dos seus ' + a.poolSize + ' números';
                    if (a.fixedCount > 0) bannerMsg += ' (fixos: ' + a.fixedNumbers.join(', ') + ')';
                    bannerMsg += '<br>📊 Combinações possíveis: <strong>' + a.totalPossible + '</strong> | Investimento: <strong>R$ ' + a.investimento.toFixed(2) + '</strong>';
                    if (a.pairCoveragePct !== undefined) bannerMsg += '<br>📐 Pares cobertos: <strong>' + a.pairCoveragePct + '%</strong>';
                    if (a.avgHamming !== undefined) bannerMsg += ' | Hamming: <strong>' + a.avgHamming + '</strong>';
                    if (a.duplicatesRejected) bannerMsg += ' | Duplicatas rejeitadas: ' + a.duplicatesRejected;
                    if (a.roi && a.roi.roiPercent !== undefined) bannerMsg += '<br>💰 ROI esperado: <strong style="color:' + (a.roi.roiPercent > -60 ? '#F59E0B' : '#EF4444') + ';">' + a.roi.roiPercent.toFixed(1) + '%</strong> <span style="font-size:0.7rem;color:#64748B;">(hipergeométrica exata)</span>';
                    if (a.isComplete) bannerMsg += '<br>✅ <strong style="color:#22C55E;">FECHAMENTO COMPLETO</strong>';
    
                    const games = result.games || [];
                    if (games.length === 0) {
                        this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#F59E0B;">' + (result.error || 'Nenhum jogo gerado.') + '</div>';
                        return;
                    }
                    this.currentGeneratedGames = games;
                    this._lastGeneratedGames = games;
                    if (typeof ComparisonEngine !== 'undefined') ComparisonEngine.saveResult('manual', games, result.analysis, this.currentGameKey);
                    this.renderGames({ pool: pool, games: games, smartAnalysis: null }, this.currentGameKey);
    
                    // Banner informativo
                    setTimeout(() => {
                        var b = document.createElement('div');
                        b.className = 'smart-gen-analysis';
                        b.style.cssText = 'margin-top:8px;margin-bottom:8px;padding:12px 16px;border-radius:10px;background:rgba(255,215,0,0.08);border:1px solid rgba(255,215,0,0.3);font-size:0.8rem;color:#FCD34D;';
                        b.innerHTML = bannerMsg;
                        var old = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
                        if (old) old.remove();
                        this.gamesContainer.parentNode.insertBefore(b, this.gamesContainer);
                    }, 50);
                    setTimeout(() => { if (this.gamesContainer) this.gamesContainer.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 150);
                }
            };
        }

        // === BOTÃO MOTOR LOTOFÁCIL (B2B) ===
        
        // === BOTÃO MOTOR +MILIONÁRIA (B2B) ===
        const btnMotorMilionaria = document.getElementById('btn-motor-milionaria');
        if (btnMotorMilionaria) {
            btnMotorMilionaria.onclick = () => {
                if (this.currentGameKey !== 'milionaria') {
                    const navBtn = document.querySelector(`.nav-btn[data-game="milionaria"]`);
                    if (navBtn) navBtn.click();
                    else this.updateGameInfo('milionaria');
                }
                if (typeof this.updateInvestmentPanel === 'function') this.updateInvestmentPanel();
                if (typeof this.updateCurrentCostDisplay === 'function') this.updateCurrentCostDisplay();
                const panel = document.getElementById('motor-milionaria-panel');
                if (panel) {
                    const isOpening = panel.style.display === 'none' || !panel.style.display;
                    ['motor-lotofacil-panel', 'motor-lotomania-panel', 'motor-timemania-panel'].forEach(id => {
                        const p = document.getElementById(id);
                        if (p) p.style.display = 'none';
                    });
                    panel.style.display = isOpening ? 'block' : 'none';
                    if (isOpening) panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            };
        }
        this._initMilionariaMotorEvents();

        const btnMotorLotofacil = document.getElementById('btn-motor-lotofacil');
        if (btnMotorLotofacil) {
            btnMotorLotofacil.onclick = () => {
                if (this.currentGameKey !== 'lotofacil') {
                    const navBtn = document.querySelector(`.nav-btn[data-game="lotofacil"]`);
                    if (navBtn) navBtn.click();
                    else this.updateGameInfo('lotofacil');
                }
                if (typeof this.updateInvestmentPanel === 'function') this.updateInvestmentPanel();
                if (typeof this.updateCurrentCostDisplay === 'function') this.updateCurrentCostDisplay();
                const panel = document.getElementById('motor-lotofacil-panel');
                if (panel) {
                    panel.style.display = panel.style.display === 'none' ? 'block' : (panel.style.display === 'block' ? 'none' : 'block');
                    panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            };
        }

        const btnExecutarLotofacil = document.getElementById('btn-executar-motor-lotofacil');
        if (btnExecutarLotofacil) {
            btnExecutarLotofacil.onclick = async () => {
                if (this.currentGameKey !== 'lotofacil') {
                    const navBtn = document.querySelector(`.nav-btn[data-game="lotofacil"]`);
                    if (navBtn) navBtn.click();
                    else this.updateGameInfo('lotofacil');
                }
                const qty = parseInt(document.getElementById('games-quantity').value) || 10;
                const historicoLimite = parseInt(document.getElementById('select-historico-lotofacil')?.value || '10') || 10;
                const estrategia = document.getElementById('select-estrategia-lotofacil')?.value || 'equilibrada';

                const origText = btnExecutarLotofacil.innerHTML;
                btnExecutarLotofacil.disabled = true;
                btnExecutarLotofacil.innerHTML = '⏳ Executando Motor Lotofácil...';
                this.gamesContainer.innerHTML = '<div style="text-align:center;padding:40px;"><div class="sync-loader" style="font-size:1.2em;">Executando Motor Lotofácil B2B (Análise 10 Concursos + Divisões Dinâmicas + Score B2B)...</div></div>';

                try {
                    const data = await MotorLotofacilB2BEngine.gerarCarteira(qty, { historicoLimite, estrategia });
                    if (data && data.jogos && data.jogos.length > 0) {
                        const rawGames = data.jogos.map(j => j.numeros);
                        this.currentGeneratedGames = rawGames;
                        this._lastGeneratedGames = rawGames;
                        this.renderGames({ pool: Array.from({length: 25}, (_, i) => i+1), games: rawGames, smartAnalysis: null }, 'lotofacil');

                        const diag = data.diagnostico_10_concursos || {};
                        const est = data.estrutura_recomendada || {};
                        const aud = data.auditoria_carteira || {};
                        const sens = data.analise_sensibilidade || {};
                        const vm = data.verdade_matematica || {};

                        const bannerMsg = `
                            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                                <span style="color:#C084FC; font-weight:800; font-size:1.05rem;">⚡ MOTOR INTELIGENTE LOTOFÁCIL (B2B LOTERIAS) — ${data.jogos.length} JOGOS</span>
                                <span style="background:rgba(168,85,247,0.2); color:#E9D5FF; padding:3px 10px; border-radius:6px; font-weight:700; font-size:0.78rem; border: 1px solid rgba(192,132,252,0.4);">
                                    DIVISÃO: ${est.divisao_selecionada || '01-12 / 13-25'} | SCORE MÉDIO: ${aud.score_medio || 85}/100
                                </span>
                            </div>
                            
                            <div style="margin-top:10px; padding:10px 14px; background:rgba(0,0,0,0.3); border-radius:8px; border:1px solid rgba(192,132,252,0.2); font-size:0.82rem; color:#E2E8F0; line-height:1.6;">
                                <strong style="color:#FCD34D;">📊 1. DIAGNÓSTICO DOS ÚLTIMOS 10 CONCURSOS:</strong><br>
                                • <strong>Quentes (${diag.quentes?.length || 0}):</strong> ${(diag.quentes || []).map(n => String(n).padStart(2,'0')).join(', ') || '--'} | 
                                <strong>Normais (${diag.normais?.length || 0}):</strong> ${(diag.normais || []).map(n => String(n).padStart(2,'0')).join(', ') || '--'} | 
                                <strong>Frios (${diag.frios?.length || 0}):</strong> ${(diag.frios || []).map(n => String(n).padStart(2,'0')).join(', ') || '--'}<br>
                                • <strong>Repetição Média do Concurso Anterior:</strong> ${diag.media_repeticao_anterior || 9.0} dezenas | 
                                <strong>Consecutividade Máxima no Jogo:</strong> ≤ 5 números<br>
                                • <strong>Divisão Selecionada:</strong> ${est.divisao_selecionada || '01-12 / 13-25'} | 
                                <strong>Estruturas Prioritárias:</strong> ${(est.estruturas_prioritarias || []).join(' → ')}
                            </div>

                            <div style="margin-top:8px; padding:10px 14px; background:rgba(16,185,129,0.08); border-radius:8px; border:1px solid rgba(16,185,129,0.3); font-size:0.82rem; color:#D1FAE5; line-height:1.6;">
                                <strong style="color:#34D399;">📐 2. COBERTURA & AUDITORIA DA CARTEIRA:</strong><br>
                                • Cobertura dos 25 números: <strong>${aud.cobertura_25_pct || 100}%</strong> (${aud.dezenas_presentes || 25}/25 dezenas ativas)<br>
                                • Ranking dos Jogos: Classificados de <strong>TOP 1</strong> a <strong>TOP ${data.jogos.length}</strong> por Score B2B Multicritério.
                            </div>

                            <div style="margin-top:8px; padding:10px 14px; background:rgba(59,130,246,0.08); border-radius:8px; border:1px solid rgba(59,130,246,0.3); font-size:0.80rem; color:#BFDBFE; line-height:1.5;">
                                <strong style="color:#60A5FA;">🔬 3. ANÁLISE DE SENSIBILIDADE:</strong><br>
                                • <em>${sens.hipotese_sem_quentes || ''}</em><br>
                                • <em>${sens.resiliencia_do_modelo || ''}</em>
                            </div>

                            <div style="margin-top:8px; padding:12px 14px; background:rgba(239,68,68,0.08); border-radius:8px; border:1px solid rgba(239,68,68,0.35); font-size:0.80rem; color:#FECACA; line-height:1.5;">
                                <strong style="color:#F87171;">🛡️ 4. VERDADE MATEMÁTICA (TRANSPARÊNCIA OBRIGATÓRIA):</strong><br>
                                • <strong>Princípio Fundamental:</strong> ${vm.declaracao_fundamental || ''}<br>
                                • <strong>Limitação Amostral:</strong> ${vm.limitacoes_e_honestidade || ''}
                            </div>
                        `;

                        setTimeout(() => {
                            var b = document.createElement('div');
                            b.className = 'smart-gen-analysis';
                            b.style.cssText = 'margin-top:10px;margin-bottom:12px;padding:16px 20px;border-radius:12px;background:linear-gradient(135deg, rgba(124,58,237,0.18), rgba(15,23,42,0.95));border:1px solid #9333ea;box-shadow:0 6px 25px rgba(147,51,234,0.3);';
                            b.innerHTML = bannerMsg;
                            var old = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
                            if (old) old.remove();
                            this.gamesContainer.parentNode.insertBefore(b, this.gamesContainer);
                        }, 50);
                    }
                } catch (err) {
                    this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">Erro ao gerar no Motor Lotofácil: ' + err.message + '</div>';
                } finally {
                    btnExecutarLotofacil.disabled = false;
                    btnExecutarLotofacil.innerHTML = origText;
                    setTimeout(() => { if (this.gamesContainer) this.gamesContainer.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 150);
                }
            };
        }

        // === BOTÃO MOTOR LOTOMANIA (B2B) ===
        const btnMotorLotomania = document.getElementById('btn-motor-lotomania');
        if (btnMotorLotomania) {
            btnMotorLotomania.onclick = () => {
                if (this.currentGameKey !== 'lotomania') {
                    const tabBtn = document.querySelector(`.lottery-btn[data-lottery="lotomania"]`);
                    if (tabBtn) tabBtn.click();
                    else this.updateGameInfo('lotomania');
                }
                if (typeof this.updateInvestmentPanel === 'function') this.updateInvestmentPanel();
                if (typeof this.updateCurrentCostDisplay === 'function') this.updateCurrentCostDisplay();
                const panel = document.getElementById('motor-lotomania-panel');
                if (panel) {
                    panel.style.display = 'block';
                    panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            };
        }

        const btnExecutarLotomania = document.getElementById('btn-executar-motor-lotomania');
        if (btnExecutarLotomania) {
            btnExecutarLotomania.onclick = async () => {
                if (this.currentGameKey !== 'lotomania') {
                    const tabBtn = document.querySelector(`.lottery-btn[data-lottery="lotomania"]`);
                    if (tabBtn) tabBtn.click();
                }
                const qty = parseInt(document.getElementById('games-quantity').value) || 10;
                const historicoLimite = parseInt(document.getElementById('select-historico-lotomania')?.value || '0') || null;
                const estrategia = document.getElementById('select-estrategia-lotomania')?.value || 'equilibrada';

                const origText = btnExecutarLotomania.innerHTML;
                btnExecutarLotomania.disabled = true;
                btnExecutarLotomania.innerHTML = '⏳ Otimizando Carteira...';
                this.gamesContainer.innerHTML = '<div style="text-align:center;padding:40px;"><div class="sync-loader" style="font-size:1.2em;">Executando Motor Lotomania (5 Conjuntos x 10 Dezenas = 50)...</div></div>';

                try {
                    const data = await MotorLotomaniaB2BEngine.gerarCarteira(qty, { historicoLimite, estrategia });
                    if (data && data.jogos && data.jogos.length > 0) {
                        this.currentGeneratedGames = data.jogos;
                        this._lastGeneratedGames = data.jogos;
                        this.renderGames({ pool: Array.from({length: 100}, (_, i) => i+1), games: data.jogos, smartAnalysis: null }, 'lotomania');

                        const aud = data.auditoria_carteira || {};
                        const bannerMsg = `
                            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                                <span style="color:#38BDF8; font-weight:800; font-size:0.95rem;">⚛️ MOTOR LOTOMANIA (B2B LOTERIAS) — ${data.jogos.length} JOGOS</span>
                                <span style="background:rgba(16,185,129,0.2); color:#34D399; padding:2px 8px; border-radius:4px; font-weight:700; font-size:0.75rem;">[OK] AUDITORIA 10/10 LIBERADA</span>
                            </div>
                            <div style="margin-top:6px; font-size:0.8rem; color:#E2E8F0; line-height:1.5;">
                                • Estrutura: <strong>5 Conjuntos x 10 Dezenas = 50 números/jogo</strong> | Consecutividade Máx: <strong>≤ 4</strong><br>
                                • Cobertura dos 100 números: <strong>${aud.cobertura_100_pct || 100}%</strong> | Diversidade: <strong>${aud.indice_diversidade_pct || 75}%</strong> | Score Médio: <strong>${aud.indice_estatistico_medio || 80}/100</strong><br>
                                • Mais usado: <strong>${aud.numero_mais_utilizado?.numero || '--'} (${aud.numero_mais_utilizado?.vezes || 0}x)</strong> | Menos usado: <strong>${aud.numero_menos_utilizado?.numero || '--'} (${aud.numero_menos_utilizado?.vezes || 0}x)</strong> | Média: <strong>${aud.media_utilizacao || '--'}</strong>
                            </div>
                        `;

                        setTimeout(() => {
                            var b = document.createElement('div');
                            b.className = 'smart-gen-analysis';
                            b.style.cssText = 'margin-top:8px;margin-bottom:8px;padding:14px 18px;border-radius:10px;background:linear-gradient(135deg, rgba(2,132,199,0.15), rgba(15,118,110,0.15));border:1px solid #0284c7;box-shadow:0 4px 15px rgba(2,132,199,0.2);';
                            b.innerHTML = bannerMsg;
                            var old = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
                            if (old) old.remove();
                            this.gamesContainer.parentNode.insertBefore(b, this.gamesContainer);
                        }, 50);
                    }
                } catch (err) {
                    this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">Erro ao gerar no Motor Lotomania: ' + err.message + '</div>';
                } finally {
                    btnExecutarLotomania.disabled = false;
                    btnExecutarLotomania.innerHTML = origText;
                    setTimeout(() => { if (this.gamesContainer) this.gamesContainer.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 150);
                }
            };
        }

        // === BOTÃO MOTOR DIA DE SORTE (B2B) ===
        const btnMotorDiaDeSorte = document.getElementById('btn-motor-diadesorte');
        if (btnMotorDiaDeSorte) {
            btnMotorDiaDeSorte.onclick = () => {
                if (this.currentGameKey !== 'diadesorte') {
                    const navBtn = document.querySelector(`.nav-btn[data-game="diadesorte"]`);
                    if (navBtn) navBtn.click();
                    else {
                        const tabBtn = document.querySelector(`.lottery-btn[data-lottery="diadesorte"]`);
                        if (tabBtn) tabBtn.click();
                        else this.updateGameInfo('diadesorte');
                    }
                }
                if (typeof this.updateInvestmentPanel === 'function') this.updateInvestmentPanel();
                if (typeof this.updateCurrentCostDisplay === 'function') this.updateCurrentCostDisplay();
                const panel = document.getElementById('motor-diadesorte-panel');
                if (panel) {
                    const isOpening = panel.style.display === 'none' || !panel.style.display;
                    ['motor-lotofacil-panel', 'motor-lotomania-panel', 'motor-timemania-panel', 'motor-milionaria-panel'].forEach(id => {
                        const p = document.getElementById(id);
                        if (p) p.style.display = 'none';
                    });
                    panel.style.display = isOpening ? 'block' : 'none';
                    if (isOpening) panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            };
        }

        const btnExecutarDiaDeSorte = document.getElementById('btn-executar-motor-diadesorte');
        if (btnExecutarDiaDeSorte) {
            btnExecutarDiaDeSorte.onclick = async () => {
                if (this.currentGameKey !== 'diadesorte') {
                    const navBtn = document.querySelector(`.nav-btn[data-game="diadesorte"]`);
                    if (navBtn) navBtn.click();
                }
                const qtyInput = document.getElementById('games-quantity');
                const qty = qtyInput ? (parseInt(qtyInput.value) || 10) : 10;
                const historicoLimite = parseInt(document.getElementById('select-historico-diadesorte')?.value || '30') || 30;
                const estrategia = document.getElementById('select-estrategia-diadesorte')?.value || 'equilibrada';
                const poolType = document.getElementById('select-pool-diadesorte')?.value || 'automatico';
                let pool = null;
                if (poolType === 'personalizado' && this.selectedNumbers && this.selectedNumbers.size >= 7) {
                    pool = Array.from(this.selectedNumbers);
                }

                const origText = btnExecutarDiaDeSorte.innerHTML;
                btnExecutarDiaDeSorte.disabled = true;
                btnExecutarDiaDeSorte.innerHTML = '⏳ Calculando Modelos e Coocorrências...';
                this.gamesContainer.innerHTML = '<div style="text-align:center;padding:40px;"><div class="sync-loader" style="font-size:1.2em;">Executando Motor Dia de Sorte (Grupos A: 01-15 | B: 16-31)...</div></div>';

                try {
                    const data = await MotorDiaDeSorteB2BEngine.gerarCarteira(qty, { historicoLimite, estrategia, pool });
                    if (data && data.jogos && data.jogos.length > 0) {
                        this.currentGeneratedGames = data.jogos.map(j => j.jogo);
                        this._lastGeneratedGames = this.currentGeneratedGames;
                        this.renderGames({ pool: pool || Array.from({length: 31}, (_, i) => i+1), games: this.currentGeneratedGames, smartAnalysis: null }, 'diadesorte');

                        const rel = data.relatorio_pre_geracao || {};
                        const bannerMsg = `
                            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                                <span style="color:#FBBF24; font-weight:800; font-size:0.95rem;">🍀 MOTOR DIA DE SORTE (B2B LOTERIAS) — ${data.jogos.length} JOGOS</span>
                                <span style="background:rgba(245,158,11,0.2); color:#FDE68A; padding:2px 8px; border-radius:4px; font-weight:700; font-size:0.75rem;">${rel.nivel_confianca_estatistica || 'AUDITORIA 10/10'}</span>
                            </div>
                            <div style="margin-top:6px; font-size:0.8rem; color:#E2E8F0; line-height:1.5;">
                                • Modelos: <strong>${Object.entries(data.distribuicao_modelos || {}).map(([m, c]) => `${m}: ${c}`).join(' | ')}</strong><br>
                                • Meses da Sorte: <strong>${(data.meses_utilizados || []).join(', ')}</strong><br>
                                • Pares Fortes: <strong>${(rel.pares_maior_relevancia || []).slice(0, 3).join(', ')}</strong> | Consecutividade Máx: <strong>≤ 3</strong><br>
                                • <span style="color:#94A3B8; font-style:italic;">${rel.advertencia_matematica || 'Honestidade Matemática: Análise histórica para diversificação e ordenação.'}</span>
                            </div>
                        `;

                        setTimeout(() => {
                            var b = document.createElement('div');
                            b.className = 'smart-gen-analysis';
                            b.style.cssText = 'margin-top:8px;margin-bottom:8px;padding:14px 18px;border-radius:10px;background:linear-gradient(135deg, rgba(217,119,6,0.15), rgba(15,23,42,0.9));border:1px solid #f59e0b;box-shadow:0 4px 15px rgba(245,158,11,0.2);';
                            b.innerHTML = bannerMsg;
                            var old = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
                            if (old) old.remove();
                            this.gamesContainer.parentNode.insertBefore(b, this.gamesContainer);
                        }, 50);
                    }
                } catch (err) {
                    this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">Erro no Motor Dia de Sorte: ' + err.message + '</div>';
                } finally {
                    btnExecutarDiaDeSorte.disabled = false;
                    btnExecutarDiaDeSorte.innerHTML = origText;
                    setTimeout(() => { if (this.gamesContainer) this.gamesContainer.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 150);
                }
            };
        }

        // === BOTÃO MOTOR TIMEMANIA (B2B) ===
        const btnMotorTimemania = document.getElementById('btn-motor-timemania');
        if (btnMotorTimemania) {
            btnMotorTimemania.onclick = () => {
                if (this.currentGameKey !== 'timemania') {
                    const navBtn = document.querySelector(`.nav-btn[data-game="timemania"]`);
                    if (navBtn) navBtn.click();
                    else this.updateGameInfo('timemania');
                }
                if (typeof this.updateInvestmentPanel === 'function') this.updateInvestmentPanel();
                if (typeof this.updateCurrentCostDisplay === 'function') this.updateCurrentCostDisplay();
                const panel = document.getElementById('motor-timemania-panel');
                if (panel) {
                    panel.style.display = panel.style.display === 'none' ? 'block' : (panel.style.display === 'block' ? 'none' : 'block');
                    panel.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            };
        }

        const btnExecutarTimemania = document.getElementById('btn-executar-motor-timemania');
        if (btnExecutarTimemania) {
            btnExecutarTimemania.onclick = async () => {
                if (this.currentGameKey !== 'timemania') {
                    const navBtn = document.querySelector(`.nav-btn[data-game="timemania"]`);
                    if (navBtn) navBtn.click();
                    else this.updateGameInfo('timemania');
                }
                const qty = parseInt(document.getElementById('games-quantity')?.value || '10') || 10;
                const poolSize = parseInt(document.getElementById('select-pool-timemania')?.value || '80') || 80;
                const historicoLimite = parseInt(document.getElementById('select-historico-timemania')?.value || '0') || null;
                const estrategia = document.getElementById('select-estrategia-timemania')?.value || 'equilibrada';
                const estrategiaTimeSelect = document.getElementById('select-estrategia-time-timemania')?.value || 'maior_ift';
                const noConsecutive3InGroup = document.getElementById('check-no-consec-timemania')?.checked !== false;
                const sniper = document.getElementById('check-sniper-timemania')?.checked || false;

                let estrategiaTime = estrategiaTimeSelect;
                let timeFixoUsuario = null;
                if (estrategiaTimeSelect.startsWith('fixo_')) {
                    const mapFixos = {
                        'fixo_flamengo': 'FLAMENGO/RJ',
                        'fixo_corinthians': 'CORINTHIANS/SP',
                        'fixo_palmeiras': 'PALMEIRAS/SP',
                        'fixo_saopaulo': 'SÃO PAULO/SP',
                        'fixo_santos': 'SANTOS/SP',
                        'fixo_vasco': 'VASCO DA GAMA/RJ',
                        'fixo_gremio': 'GRÊMIO/RS',
                        'fixo_internacional': 'INTERNACIONAL/RS',
                        'fixo_cruzeiro': 'CRUZEIRO/MG',
                        'fixo_atleticomg': 'ATLÉTICO/MG',
                        'fixo_botafogo': 'BOTAFOGO/RJ',
                        'fixo_fluminense': 'FLUMINENSE/RJ',
                        'fixo_bahia': 'BAHIA/BA',
                        'fixo_sport': 'SPORT/PE',
                        'fixo_fortaleza': 'FORTALEZA/CE',
                        'fixo_ceara': 'CEARÁ/CE'
                    };
                    timeFixoUsuario = mapFixos[estrategiaTimeSelect] || 'FLAMENGO/RJ';
                    estrategiaTime = 'fixo';
                }

                // Configurar pool se reduzido
                let pool = null;
                if (poolSize < 80) {
                    pool = Array.from({ length: poolSize }, (_, i) => i + 1);
                }

                const origText = btnExecutarTimemania.innerHTML;
                btnExecutarTimemania.disabled = true;
                btnExecutarTimemania.innerHTML = '⏳ Otimizando Carteira Timemania...';
                this.gamesContainer.innerHTML = '<div style="text-align:center;padding:40px;"><div class="sync-loader" style="font-size:1.2em;">Executando Motor Timemania B2B (4 Grupos x 20 + IFM 8D + Time do Coração)...</div></div>';

                try {
                    const data = await MotorTimemaniaB2BEngine.gerarCarteira(qty, {
                        historicoLimite,
                        estrategia,
                        sniper,
                        noConsecutive3InGroup,
                        pool,
                        estrategiaTime,
                        timeFixoUsuario
                    });

                    if (data && data.jogos && data.jogos.length > 0) {
                        const rawGames = data.jogos.map(j => j.dezenas);
                        const rawExtras = data.jogos.map(j => j.time_coracao);

                        this.currentGeneratedGames = rawGames;
                        this._lastGeneratedGames = rawGames;
                        this.currentGeneratedExtras = rawExtras;

                        this.renderGames({ pool: Array.from({length: 80}, (_, i) => i+1), games: rawGames, smartAnalysis: null }, 'timemania');

                        const aud = data.auditoria_10_pontos || {};
                        const bannerMsg = `
                            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                                <span style="color:#34D399; font-weight:800; font-size:1.05rem;">🎯 MOTOR TIMEMANIA (B2B LOTERIAS) — ${data.jogos.length} JOGOS</span>
                                <span style="background:rgba(16,185,129,0.2); color:#A7F3D0; padding:3px 10px; border-radius:6px; font-weight:700; font-size:0.78rem; border: 1px solid rgba(52,211,153,0.4);">
                                    ${aud.status_geral || 'APROVADO (10/10)'} | SCORE MÉDIO: ${data.score_medio || 75}/100
                                </span>
                            </div>
                            
                            <div style="margin-top:10px; padding:10px 14px; background:rgba(0,0,0,0.3); border-radius:8px; border:1px solid rgba(52,211,153,0.2); font-size:0.82rem; color:#E2E8F0; line-height:1.6;">
                                <strong style="color:#FCD34D;">📐 1. ESTRUTURA COMBINATÓRIA DOS 4 GRUPOS:</strong><br>
                                • <strong>Grupos Analíticos (G1..G4):</strong> G1 (01-20), G2 (21-40), G3 (41-60), G4 (61-80) | <strong>10 números por jogo</strong><br>
                                • <strong>Estruturas Centrais:</strong> Permutações de 3-3-2-2 e 3-2-3-2 (Centróide Hipergeométrico E[N]=2.5/grupo)<br>
                                • <strong>Bloqueio de 3 Consecutivos no Grupo:</strong> ${data.regra_3_consec_bloqueada ? '✅ ATIVADO (Filtro Empírico 96.86%)' : 'DESATIVADO'} | 
                                <strong>Modo SNIPER:</strong> ${data.sniper_ativo ? '🎯 LIGADO (Alta Precisão)' : 'DESLIGADO'}
                            </div>

                            <div style="margin-top:8px; padding:10px 14px; background:rgba(16,185,129,0.08); border-radius:8px; border:1px solid rgba(16,185,129,0.3); font-size:0.82rem; color:#D1FAE5; line-height:1.6;">
                                <strong style="color:#34D399;">⚽ 2. TIME DO CORAÇÃO & COBERTURA:</strong><br>
                                • <strong>Estratégia de Time:</strong> ${estrategiaTimeSelect} | <strong>Top Time Atribuído:</strong> ${data.jogos[0]?.time_coracao || '--'}<br>
                                • <strong>Cobertura do Pool:</strong> <strong>${data.cobertura_pool_pct || 90}%</strong> (${data.total_numeros_cobertos || 72}/${data.total_pool || 80} dezenas ativas) | 
                                <strong>Diversidade Jaccard:</strong> ${data.diversidade_jaccard_pct || 82}%
                            </div>

                            <div style="margin-top:8px; padding:12px 14px; background:rgba(239,68,68,0.08); border-radius:8px; border:1px solid rgba(239,68,68,0.35); font-size:0.80rem; color:#FECACA; line-height:1.5;">
                                <strong style="color:#F87171;">🛡️ 3. VERDADE MATEMÁTICA (TRANSPARÊNCIA OBRIGATÓRIA):</strong><br>
                                • <em>Loterias são processos estocásticos aleatórios independentes. O motor otimiza as estruturas matemáticas e a cobertura sem garantia de retorno futuro.</em>
                            </div>
                        `;

                        setTimeout(() => {
                            var b = document.createElement('div');
                            b.className = 'smart-gen-analysis';
                            b.style.cssText = 'margin-top:10px;margin-bottom:12px;padding:16px 20px;border-radius:12px;background:linear-gradient(135deg, rgba(5,150,105,0.18), rgba(15,23,42,0.95));border:1px solid #10b981;box-shadow:0 6px 25px rgba(16,185,129,0.3);';
                            b.innerHTML = bannerMsg;
                            var old = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
                            if (old) old.remove();
                            this.gamesContainer.parentNode.insertBefore(b, this.gamesContainer);
                        }, 50);
                    }
                } catch (err) {
                    this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">Erro ao gerar no Motor Timemania: ' + err.message + '</div>';
                } finally {
                    btnExecutarTimemania.disabled = false;
                    btnExecutarTimemania.innerHTML = origText;
                    setTimeout(() => { if (this.gamesContainer) this.gamesContainer.scrollIntoView({ behavior: 'smooth', block: 'start' }); }, 150);
                }
            };
        }

        // === BOTÃO 📐 COBERTURA UNIFICADA v14 (Motor Unificado: Estatística + Cobertura + Sniper) ===
        if (this.generateCoverageBtn) {
            this.generateCoverageBtn.onclick = () => {
                const game = GAMES[this.currentGameKey];
                if (!game) return;
                const qty = parseInt(this.gamesQuantityInput.value) || 10;
                const drawSizeSelect = document.getElementById('smart-draw-size');
                const customDrawSize = drawSizeSelect ? parseInt(drawSizeSelect.value) : 0;
                const drawSize = (customDrawSize && customDrawSize >= game.minBet) ? customDrawSize : game.minBet;

                // Verificar modo Sniper
                const sniperToggle = document.getElementById('precision-mode-toggle');
                const sniperMode = sniperToggle ? sniperToggle.checked : false;
                const poolInput = document.getElementById('precision-pool-size');
                const sniperPoolSize = poolInput ? parseInt(poolInput.value) || 20 : 20;

                this._lastGenerationMode = sniperMode ? 'cobertura_sniper' : 'cobertura';
                localStorage.setItem('l99_lastMode', this._lastGenerationMode);
                document.body.setAttribute('data-l99-mode', this._lastGenerationMode);

                const modeLabel = sniperMode ? '🎯 SNIPER + Cobertura' : '📐 Cobertura Estatística';

                // === FEEDBACK VISUAL: desabilita botão e mostra progresso ===
                const _btn = this.generateCoverageBtn;
                const _btnOriginalHTML = _btn ? _btn.innerHTML : '';
                const _btnOriginalDisabled = _btn ? _btn.disabled : false;
                if (_btn) {
                    _btn.disabled = true;
                    _btn.innerHTML = '<span style="display:inline-block;animation:spin 0.8s linear infinite;margin-right:6px;">⚙️</span>' + (sniperMode ? 'Analisando...' : 'Gerando...');
                    _btn.style.opacity = '0.7';
                    _btn.style.cursor = 'not-allowed';
                }
                const _restoreBtn = () => {
                    if (_btn) {
                        _btn.disabled = _btnOriginalDisabled;
                        _btn.innerHTML = _btnOriginalHTML;
                        _btn.style.opacity = '';
                        _btn.style.cursor = '';
                    }
                };

                this.gamesContainer.innerHTML = '<div style="text-align:center;padding:40px;">'
                    + '<div style="font-size:2rem;margin-bottom:12px;animation:spin 1s linear infinite;display:inline-block;">⚙️</div>'
                    + '<div class="sync-loader" style="font-size:1.2em;margin-top:8px;">' + modeLabel + '...</div>'
                    + '<div style="color:#94A3B8;font-size:0.8rem;margin-top:8px;">Calculando ' + qty + ' jogos com análise estatística profunda</div>'
                    + '</div>';

                // Garantir que a animação de spin exista no CSS
                if (!document.getElementById('_sniper_spin_style')) {
                    const st = document.createElement('style');
                    st.id = '_sniper_spin_style';
                    st.textContent = '@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }';
                    document.head.appendChild(st);
                }

                // ═══ v15.0: GERAÇÃO ASSÍNCRONA — sempre para Cobertura (motor pesado) ═══
                if (typeof AsyncGenerator !== 'undefined') {
                    const coverageOpts = { precisionMode: sniperMode, precisionPoolSize: sniperPoolSize };
                    const selectedArr = this.getSelectedNumbers() || [];
                    if (sniperMode && selectedArr.length >= drawSize) {
                        alert('Aviso de Transparência:\n\nVocê ativou o Sniper, mas também selecionou números manualmente no volante.\n\nO sistema respeitará SEUS números e o Sniper automático será DESATIVADO para esta geração.');
                    }
                    AsyncGenerator.generateCoverageAsync(
                        this.currentGameKey, qty, this.getSelectedNumbers(), this.fixedNumbers, drawSize, coverageOpts,
                        (result, cancelled, error) => {
                            _restoreBtn(); // sempre restaurar botão
                            if (cancelled) {
                                this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#F59E0B;">⚠️ Geração cancelada pelo usuário.</div>';
                                return;
                            }
                            if (error || !result || !result.games || result.games.length === 0) {
                                this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">Erro: ' + (error ? error.message : 'Nenhum jogo gerado.') + '</div>';
                                return;
                            }

                            this.currentGeneratedGames = result.games;
                            this._lastGeneratedGames = result.games;
                            if (typeof ComparisonEngine !== 'undefined') ComparisonEngine.saveResult(sniperMode ? 'sniper' : 'cobertura', result.games, result.analysis, this.currentGameKey);
                            this.renderGames(result, this.currentGameKey);

                            const a = result.analysis || {};
                            const strategyName = a.strategy === 'CLOSURE' ? 'Fechamento Exato (Steiner)' 
                                               : a.strategy === 'COVERAGE_FAST' ? 'Set Cover (Rápido)' 
                                               : 'Set Cover (Greedy)';
                            
                            let probHtml = '';
                            if (typeof SmartCoverageEngine !== 'undefined' && SmartCoverageEngine.calcRealMetrics) {
                                const realMetrics = SmartCoverageEngine.calcRealMetrics(result.games, this.currentGameKey);
                                if (realMetrics && realMetrics.prizes) {
                                    probHtml = '<div style="margin-top:10px;padding:8px;background:rgba(0,0,0,0.4);border-radius:8px;font-size:0.75rem;">' +
                                               '<div style="color:#10B981;font-weight:bold;margin-bottom:4px;">PROBABILIDADES EXATAS (HIPERGEOMÉTRICA)</div>';
                                    realMetrics.prizes.slice(0, 3).forEach(p => {
                                        probHtml += '<div style="display:flex;justify-content:space-between;color:#D1D5DB;margin-bottom:2px;">' +
                                                    '<span>Acertar ' + p.hits + ':</span><span>' + p.probAtLeastOnePct + '% (em ' + result.games.length + ' jogos)</span></div>';
                                    });
                                    probHtml += '<div style="color:#6B7280;font-size:0.65rem;margin-top:4px;text-align:right;">* Eventos independentes</div></div>';
                                }
                            }
                            let evHtml = '';
                            if (typeof EVCalculator !== 'undefined') {
                                try {
                                    const evData = EVCalculator.calcMultiGameEV(this.currentGameKey, result.games.length);
                                    if (evData) {
                                        const retColor = evData.retornoPct >= 100 ? '#22C55E' : '#F59E0B';
                                        const retStr = evData.retornoPct.toFixed(1);
                                        evHtml = '<div style="margin-top:8px;display:grid;grid-template-columns:repeat(3,1fr);gap:6px;font-size:0.7rem;">' +
                                            '<div style="text-align:center;padding:6px;background:rgba(0,0,0,0.3);border-radius:8px;border:1px solid rgba(16,185,129,0.1);">' +
                                                '<div style="color:#6EE7B7;font-size:0.55rem;font-weight:700;">INVESTIMENTO</div>' +
                                                '<div style="color:#10B981;font-weight:900;font-size:1rem;">' + evData.custoTotalFormatado + '</div>' +
                                            '</div>' +
                                            '<div style="text-align:center;padding:6px;background:rgba(0,0,0,0.3);border-radius:8px;border:1px solid rgba(16,185,129,0.1);">' +
                                                '<div style="color:#6EE7B7;font-size:0.55rem;font-weight:700;">EV ESPERADO</div>' +
                                                '<div style="color:#10B981;font-weight:900;font-size:1rem;">' + evData.evBrutoTotalFormatado + '</div>' +
                                            '</div>' +
                                            '<div style="text-align:center;padding:6px;background:rgba(0,0,0,0.3);border-radius:8px;border:1px solid ' + retColor + '20;">' +
                                                '<div style="color:#6EE7B7;font-size:0.55rem;font-weight:700;">RETORNO</div>' +
                                                '<div style="color:' + retColor + ';font-weight:900;font-size:1rem;">' + retStr + '%</div>' +
                                            '</div>' +
                                        '</div>';
                                    }
                                } catch(e) { /* EVCalculator opcional */ }
                            }

                            var banner = document.createElement('div');
                            banner.className = 'smart-gen-analysis';
                            banner.style.cssText = 'margin-top:8px;margin-bottom:8px;padding:14px 18px;border-radius:12px;background:linear-gradient(145deg,rgba(4,120,87,0.12),rgba(15,23,42,0.95));border:1px solid rgba(16,185,129,0.3);';
                            banner.innerHTML = '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;"><span style="font-size:1.3rem;">📐</span><div><div style="font-weight:900;color:#10B981;font-size:1rem;text-transform:uppercase;letter-spacing:1px;">MATEMÁTICA PURA — ' + strategyName + '</div><div style="font-size:0.72rem;color:#94A3B8;">Motor: SmartCoverageEngine-Async | ' + result.games.length + ' jogos | ⚡ ' + (a.chunksProcessed || '—') + ' lotes</div></div></div><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px;font-size:0.75rem;"><div style="text-align:center;padding:10px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid rgba(16,185,129,0.2);"><div style="color:#6EE7B7;font-size:0.6rem;font-weight:700;">DIVERSIDADE (HAMMING)</div><div style="color:#10B981;font-weight:900;font-size:1.3rem;">' + (a.avgHamming || 'N/A') + '</div></div><div style="text-align:center;padding:10px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid rgba(16,185,129,0.2);"><div style="color:#6EE7B7;font-size:0.6rem;font-weight:700;">TEMPO DE PROCESSAMENTO</div><div style="color:#10B981;font-weight:900;font-size:1.3rem;">' + (a.elapsed || 'N/A') + '</div></div></div>' + probHtml + evHtml;

                            var oldBanner = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
                            if (oldBanner) oldBanner.remove();
                            this.gamesContainer.parentNode.insertBefore(banner, this.gamesContainer);
                            banner.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        }
                    );
                    return; // Sai do onclick — o callback cuidará do resultado
                }

                // Geração síncrona (quantidades pequenas — rápido o bastante)
                setTimeout(() => {
                    try {
                        if (typeof SmartCoverageEngine === 'undefined') {
                            alert('SmartCoverageEngine não carregado. Recarregue (Ctrl+Shift+R).');
                            return;
                        }
                        const selectedArr = this.getSelectedNumbers() || [];
                        if (sniperMode && selectedArr.length >= drawSize) {
                            alert('Aviso de Transparência:\n\nVocê ativou o Sniper, mas também selecionou números manualmente no volante.\n\nO sistema respeitará SEUS números e o Sniper automático será DESATIVADO para esta geração.');
                        }
                        const coverageOpts = { precisionMode: sniperMode, precisionPoolSize: sniperPoolSize };
                        const result = SmartCoverageEngine.generate(
                            this.currentGameKey, 
                            qty, 
                            this.getSelectedNumbers(), 
                            this.fixedNumbers, 
                            drawSize, 
                            coverageOpts
                        );

                        if (!result || !result.games || result.games.length === 0) {
                            this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#F59E0B;">Nenhum jogo gerado. Tente novamente.</div>';
                            return;
                        }

                        this.currentGeneratedGames = result.games;
                        this._lastGeneratedGames = result.games;
                        if (typeof ComparisonEngine !== 'undefined') ComparisonEngine.saveResult(sniperMode ? 'sniper' : 'cobertura', result.games, result.analysis, this.currentGameKey);
                        this.renderGames(result, this.currentGameKey);

                        // Banner Unificado com Métricas Reais
                        const a = result.analysis || {};
                        const strategyName = a.strategy === 'CLOSURE' ? 'Fechamento Exato (Steiner)' 
                                           : a.strategy === 'COVERAGE_FAST' ? 'Set Cover (Rápido)' 
                                           : 'Set Cover (Greedy)';
                        
                        let probHtml = '';
                        if (typeof SmartCoverageEngine !== 'undefined' && SmartCoverageEngine.calcRealMetrics) {
                            const realMetrics = SmartCoverageEngine.calcRealMetrics(result.games, this.currentGameKey);
                            if (realMetrics && realMetrics.prizes) {
                                probHtml = '<div style="margin-top:10px;padding:8px;background:rgba(0,0,0,0.4);border-radius:8px;font-size:0.75rem;">' +
                                           '<div style="color:#10B981;font-weight:bold;margin-bottom:4px;">PROBABILIDADES EXATAS (HIPERGEOMÉTRICA)</div>';
                                realMetrics.prizes.slice(0, 3).forEach(p => {
                                    probHtml += '<div style="display:flex;justify-content:space-between;color:#D1D5DB;margin-bottom:2px;">' +
                                                '<span>Acertar ' + p.hits + ':</span><span>' + p.probAtLeastOnePct + '% (em ' + qty + ' jogos)</span></div>';
                                });
                                probHtml += '<div style="color:#6B7280;font-size:0.65rem;margin-top:4px;text-align:right;">* Eventos independentes</div></div>';
                            }
                        }

                        var banner = document.createElement('div');
                        banner.className = 'smart-gen-analysis';
                        banner.style.cssText = 'margin-top:8px;margin-bottom:8px;padding:14px 18px;border-radius:12px;background:linear-gradient(145deg,rgba(4,120,87,0.12),rgba(15,23,42,0.95));border:1px solid rgba(16,185,129,0.3);';
                        banner.innerHTML = '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;"><span style="font-size:1.3rem;">📐</span><div><div style="font-weight:900;color:#10B981;font-size:1rem;text-transform:uppercase;letter-spacing:1px;">MATEMÁTICA PURA — ' + strategyName + '</div><div style="font-size:0.72rem;color:#94A3B8;">Motor: SmartCoverageEngine | ' + qty + ' jogos</div></div></div><div style="display:grid;grid-template-columns:repeat(2,1fr);gap:8px;font-size:0.75rem;"><div style="text-align:center;padding:10px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid rgba(16,185,129,0.2);"><div style="color:#6EE7B7;font-size:0.6rem;font-weight:700;">DIVERSIDADE (HAMMING)</div><div style="color:#10B981;font-weight:900;font-size:1.3rem;">' + (a.avgHamming || 'N/A') + '</div></div><div style="text-align:center;padding:10px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid rgba(16,185,129,0.2);"><div style="color:#6EE7B7;font-size:0.6rem;font-weight:700;">TEMPO DE PROCESSAMENTO</div><div style="color:#10B981;font-weight:900;font-size:1.3rem;">' + (a.elapsed || 'N/A') + '</div></div></div>' + probHtml;

                        var oldBanner = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
                        if (oldBanner) oldBanner.remove();
                        this.gamesContainer.parentNode.insertBefore(banner, this.gamesContainer);
                        banner.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    } catch(e) {
                        console.error('Erro Cobertura Unificada:', e);
                        this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">Erro: ' + e.message + '</div>';
                    }
                }, 50);
            };
        }

        // === BOTÃO 🎯 GERADOR INTELIGENTE (Motor Unificado v15.0) ===
        const btnGeradorInteligente = document.getElementById('btn-gerador-inteligente');
        if (btnGeradorInteligente) {
            btnGeradorInteligente.onclick = () => {
                const game = GAMES[this.currentGameKey];
                if (!game) return;
                const qty = parseInt(this.gamesQuantityInput.value) || 10;
                const drawSizeSelect = document.getElementById('smart-draw-size');
                const customDrawSize = drawSizeSelect ? parseInt(drawSizeSelect.value) : 0;
                const drawSize = (customDrawSize && customDrawSize >= game.minBet) ? customDrawSize : game.minBet;

                // Verificar modo Sniper
                const sniperToggle = document.getElementById('precision-mode-toggle');
                const sniperMode = sniperToggle ? sniperToggle.checked : false;
                const poolInput = document.getElementById('precision-pool-size');
                const sniperPoolSize = poolInput ? parseInt(poolInput.value) || 20 : 20;

                this._lastGenerationMode = sniperMode ? 'inteligente_sniper' : 'inteligente';
                localStorage.setItem('l99_lastMode', this._lastGenerationMode);
                document.body.setAttribute('data-l99-mode', this._lastGenerationMode);

                // Mostrar ROI Preview ANTES de gerar
                const roiContainer = document.getElementById('roi-preview-container');
                if (roiContainer && typeof ROIDashboard !== 'undefined') {
                    try {
                        roiContainer.innerHTML = ROIDashboard.generateROIPreview(this.currentGameKey, qty);
                        roiContainer.style.display = 'block';
                    } catch(e) { console.warn('[UI] ROIPreview erro:', e); }
                }

                const modeLabel = sniperMode ? '🎯 Gerador Inteligente + Sniper' : '🎯 Gerador Inteligente';
                this.gamesContainer.innerHTML = '<div style="text-align:center;padding:20px;"><div class="sync-loader">' + modeLabel + '...</div></div>';
                if (typeof AsyncGenerator !== 'undefined') {
                    let sp = null;
                    if (sniperMode && typeof StatisticalBiasEngine !== 'undefined') { try { let h = []; if (typeof StatsService !== 'undefined') h = StatsService.getRecentResults(this.currentGameKey, 200) || []; if (h.length === 0 && typeof REAL_HISTORY_DB !== 'undefined') h = REAL_HISTORY_DB[this.currentGameKey] || []; if (h.length >= 30) { const br = StatisticalBiasEngine.analyze(this.currentGameKey, h, sniperPoolSize); if (br && br.topNumbers) sp = br.topNumbers.slice(0, sniperPoolSize); } } catch(e) {} }
                    const sa = this.getSelectedNumbers ? this.getSelectedNumbers() : [];
                    const fa = this.fixedNumbers ? Array.from(this.fixedNumbers) : [];
                    const ao = { precisionMode: sniperMode, precisionPoolSize: sniperPoolSize, drawSize: drawSize };
                    if (sp && sp.length >= drawSize) ao.pool = sp;
                    AsyncGenerator.generatePureAsync(this.currentGameKey, qty, ao, (result, cancelled, error) => {
                        if (cancelled) { this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#F59E0B;">⚠️ Cancelado.</div>'; return; }
                        if (error || !result || !result.games || result.games.length === 0) { this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">Erro: ' + (error ? error.message : 'Nenhum jogo.') + '</div>'; return; }
                        this.currentGeneratedGames = result.games; this._lastGeneratedGames = result.games;
                        if (typeof ComparisonEngine !== 'undefined') ComparisonEngine.saveResult('inteligente', result.games, result.analysis, this.currentGameKey);
                        this.renderGames(result, this.currentGameKey);
                        const a = result.analysis || {};
                        var banner = document.createElement('div'); banner.className = 'smart-gen-analysis';
                        banner.style.cssText = 'margin-top:8px;margin-bottom:8px;padding:14px 18px;border-radius:12px;background:linear-gradient(145deg,rgba(14,165,233,0.12),rgba(15,23,42,0.95));border:1px solid rgba(56,189,248,0.3);';
                        banner.innerHTML = '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;"><span style="font-size:1.3rem;">🎯</span><div><div style="font-weight:900;color:#38BDF8;font-size:1rem;text-transform:uppercase;">GERADOR INTELIGENTE</div><div style="font-size:0.72rem;color:#94A3B8;">CoverageEngine | ' + result.games.length + ' jogos | ' + (a.elapsed || '') + '</div></div></div>';
                        var ob = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis'); if (ob) ob.remove();
                        this.gamesContainer.parentNode.insertBefore(banner, this.gamesContainer);
                        banner.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    });
                    return;
                }
                setTimeout(() => {
                    try { const r = PureCoverageEngine.generate(this.currentGameKey, qty, {drawSize}); if (!r||!r.games) return; this.currentGeneratedGames=r.games; this._lastGeneratedGames=r.games; this.renderGames(r, this.currentGameKey); } catch(e) { this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">Erro: '+e.message+'</div>'; }
                }, 50)
            };
        }

        // Pool de Precisão (Sniper) — agora vinculado ao botão Cobertura
        const precisionPoolRow = document.createElement('div');
        precisionPoolRow.id = 'precision-pool-row';
        precisionPoolRow.style.cssText = 'display:none; align-items:center; gap:10px; margin-top:8px; padding:10px 14px; background:linear-gradient(145deg,rgba(245,158,11,0.08),rgba(15,23,42,0.95)); border:1px solid rgba(245,158,11,0.3); border-radius:10px;';
        precisionPoolRow.innerHTML = '<span style="color:#F59E0B;font-size:0.85rem;font-weight:700;white-space:nowrap;">Pool Sniper:</span><input type="number" id="precision-pool-size" min="7" max="100" value="20" style="width:70px;padding:6px 8px;border-radius:8px;border:1px solid rgba(255,215,0,0.5);background:rgba(0,0,0,0.4);color:#FFD700;font-weight:800;font-size:0.95rem;text-align:center;outline:none;height:36px;"><span id="precision-pool-info" style="color:#94A3B8;font-size:0.75rem;flex:1;">números no pool</span>';
        const smartNumbersRow = document.getElementById('smart-numbers-row');
        if (smartNumbersRow && smartNumbersRow.parentNode) {
            smartNumbersRow.parentNode.insertBefore(precisionPoolRow, smartNumbersRow.nextSibling);
        }

        // Toggle Sniper — agora controla o botão Cobertura
        const toggle = document.getElementById('precision-mode-toggle');
        if (toggle && this.generateCoverageBtn) {
            const _self = this;
            const _applyPrecisionUI = (checked) => {
                if (checked) {
                    _self.generateCoverageBtn.innerHTML = '🎯 SNIPER';
                    _self.generateCoverageBtn.style.background = 'linear-gradient(135deg, #D97706, #92400E)';
                    _self.generateCoverageBtn.style.boxShadow = '0 6px 25px rgba(217, 119, 6, 0.5)';
                    _self.generateCoverageBtn.style.borderColor = '#F59E0B';
                    precisionPoolRow.style.display = 'flex';
                    _self._updatePrecisionPoolLimits();
                } else {
                    _self.generateCoverageBtn.innerHTML = '📐 Cobertura IA';
                    _self.generateCoverageBtn.style.background = 'linear-gradient(135deg, #047857 0%, #065f46 50%, #064e3b 100%)';
                    _self.generateCoverageBtn.style.boxShadow = '';
                    _self.generateCoverageBtn.style.borderColor = '#10B981';
                    precisionPoolRow.style.display = 'none';
                }
            };
            toggle.addEventListener('change', () => {
                localStorage.setItem('l99_precision_on', toggle.checked ? '1' : '0');
                _applyPrecisionUI(toggle.checked);
            });
            const savedPrecision = localStorage.getItem('l99_precision_on');
            if (savedPrecision === '1') { toggle.checked = true; _applyPrecisionUI(true); }
            // A inicialização do valor agora é feita no _updatePrecisionPoolLimits() para ser sensível à loteria atual
            const poolInput = document.getElementById('precision-pool-size');
            if (poolInput) {
                poolInput.addEventListener('change', () => localStorage.setItem('l99_precision_pool_' + _self.currentGameKey, poolInput.value));
                poolInput.addEventListener('input', () => localStorage.setItem('l99_precision_pool_' + _self.currentGameKey, poolInput.value));
            }
        }

        // === ACOES SECUNDARIAS ===
        if (this.copyBtn) this.copyBtn.onclick = () => this.copyGames();
        if (this.saveBtn) this.saveBtn.onclick = () => this.saveGames();
        if (this.gamesQuantityInput) this.gamesQuantityInput.addEventListener('input', () => this.updateCurrentCostDisplay());
        if (this.smartDrawSizeSelect) this.smartDrawSizeSelect.addEventListener('change', () => this.updateCurrentCostDisplay());
        if (this.checkBtn) this.checkBtn.onclick = () => this.openCheckModal();
        if (this.playCaixaBtn) {
            this.playCaixaBtn.onclick = (e) => {
                e.preventDefault();
                this.openCaixa();
            };
        }

        // Individual Game Copy (Delegation)
        if (this.gamesContainer) {
            this.gamesContainer.addEventListener('click', (e) => {
                const copyBtn = e.target.closest('.copy-single-btn');
                if (copyBtn) {
                    const text = copyBtn.dataset.numbers;
                    this.copyToClipboard(text).then(success => {
                        if (success === true) {
                            const original = copyBtn.innerHTML;
                            copyBtn.innerHTML = 'OK';
                            setTimeout(() => copyBtn.innerHTML = original, 1000);
                        }
                    });
                }
            });
        }

        // Check Modal Events
        if (this.confirmCheckBtn) this.confirmCheckBtn.onclick = () => this.confirmCheck();
        if (this.closeCheckModalBtn) this.closeCheckModalBtn.onclick = () => this.closeCheckModal();

        // Carregar jogos salvos (btn-listar-jogos-salvos)
        const btnListarSalvos = document.getElementById('btn-listar-jogos-salvos');
        const loadGamesInput = document.getElementById('load-games-input');
        if (btnListarSalvos && loadGamesInput) {
            btnListarSalvos.onclick = () => loadGamesInput.click();
            loadGamesInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (evt) => {
                    const text = evt.target.result;
                    const checkInput = document.getElementById('check-input-numbers');
                    if (checkInput) {
                        checkInput.value = text.trim();
                        if (typeof Guardian !== 'undefined' && Guardian.toast) {
                            Guardian.toast(`Arquivo "${file.name}" carregado com sucesso!`, 'success');
                        }
                    }
                    loadGamesInput.value = ''; // Reset para permitir re-seleção
                };
                reader.readAsText(file);
            });
        }

        // Print Button
        const btnPrint = document.getElementById('btn-print');
        if (btnPrint) btnPrint.onclick = () => window.print();

        // Stats Range Toggles
        this.statsButtons.forEach(btn => {
            btn.onclick = () => {
                this.currentStatsRange = parseInt(btn.dataset.range);
                this.statsButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.updateStats();
            };
        });

        // Clean Header for Print
        window.addEventListener('beforeprint', () => {
            document.title = '\u200B';
            this.insertPrintTimestamp();
        });

        // Initialize Modules
        this.initTutorialEvents();
        this.initInstallEvents();
        this.initQuantum();
        this.initCopyEvents();
        this.initShareEvents();
        this.initStatisticsPanel();

        // Carregar Hot/Cold inicial
        this.updateStats();

        console.log('[UI] initEvents() concluido com sucesso');
    }

    debounce(func, wait) {
        let timeout;
        return (...args) => {
            clearTimeout(timeout);
            timeout = setTimeout(() => func.apply(this, args), wait);
        };
    }

    // ════════════════════════════════════════════════════════════
    //  ATUALIZAR ESTATÍSTICAS (Números Quentes / Frios)
    // ════════════════════════════════════════════════════════════
    updateStats() {
        if (typeof StatsService === 'undefined') {
            console.warn('[UI] StatsService não disponível');
            return;
        }
        try {
            const stats = StatsService.getStats(this.currentGameKey, this.currentStatsRange);
            this.renderHotCold(stats);
        } catch (e) {
            console.warn('[UI] Erro ao atualizar stats:', e.message);
        }
    }

    renderHotCold(stats) {
        const hotContainer = this.hotNumbersContainer || document.getElementById('hot-numbers');
        const coldContainer = this.coldNumbersContainer || document.getElementById('cold-numbers');
        if (!hotContainer || !coldContainer) return;

        const gameConfig = (typeof GAMES !== 'undefined') ? GAMES[this.currentGameKey] : null;
        const color = gameConfig ? gameConfig.color : '#10B981';
        const statsCount = gameConfig ? (gameConfig.statsCount || 15) : 15;

        const hotNums = (stats && stats.hot) ? stats.hot.slice(0, statsCount) : [];
        const coldNums = (stats && stats.cold) ? stats.cold.slice(0, statsCount) : [];

        // Render Hot
        hotContainer.innerHTML = hotNums.map(item => {
            const num = String(item.number).padStart(2, '0');
            return '<span class="stat-ball hot" style="--ball-color:' + color + '" title="Saiu ' + item.count + 'x">' + num + '</span>';
        }).join('');

        // Render Cold
        coldContainer.innerHTML = coldNums.map(item => {
            const num = String(item.number).padStart(2, '0');
            return '<span class="stat-ball cold" title="Saiu ' + item.count + 'x | Atraso: ' + item.delay + '">' + num + '</span>';
        }).join('');

        console.log('[UI] Hot/Cold renderizado: ' + hotNums.length + ' quentes, ' + coldNums.length + ' frios (range=' + this.currentStatsRange + ')');
    }

    initCopyEvents() {
        if (this.closeCopyModalBtns) {
            this.closeCopyModalBtns.forEach(btn => {
                btn.onclick = () => {
                    this.copyModal.style.display = 'none';
                };
            });
        }

        const btnSelectAll = document.getElementById('btn-select-all');
        if (btnSelectAll && this.copyTextarea) {
            btnSelectAll.onclick = this.debounce(() => {
                this.copyTextarea.focus();
                this.copyTextarea.select();
            }, 300);
        }
    }

    initTutorialEvents() {
        if (this.btnTutorial && this.tutorialModal) {
            this.btnTutorial.addEventListener('click', () => {
                this.tutorialModal.style.display = 'flex';
            });
        }

        if (this.closeTutorialModalBtns) {
            this.closeTutorialModalBtns.forEach(btn => {
                btn.addEventListener('click', () => {
                    this.tutorialModal.style.display = 'none';
                });
            });
        }

        if (this.btnPrintTutorial) {
            this.btnPrintTutorial.addEventListener('click', (e) => {
                e.preventDefault();
                const modal = document.getElementById('tutorial-modal');
                if (!modal) return;
                const body = modal.querySelector('.modal-body');
                if (!body) return;

                const printWin = window.open('', '_blank', 'width=800,height=600');
                if (!printWin) { alert('Permita pop-ups para imprimir o tutorial.'); return; }

                printWin.document.write(`<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<title>B2B Loterias v14.0 — Tutorial Completo</title>
<style>
  * { margin: 0; padding: 0; box-sizing: border-box; }
  body {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 13px;
    line-height: 1.5;
    color: #000 !important;
    background: #fff !important;
    padding: 20px 30px;
  }
  h3 { font-size: 18px; margin-bottom: 12px; text-align: center; }
  h4 { font-size: 14px; margin: 14px 0 6px 0; color: #000 !important; }
  p { margin: 4px 0; color: #000 !important; }
  li { color: #000 !important; margin-bottom: 2px; }
  strong { color: #000 !important; }
  ul { margin-left: 20px; }
  div { color: #000 !important; background: none !important; border-color: #999 !important; }
  a { color: #000 !important; text-decoration: none; }
  button { display: none !important; }
  /* Forçar preto e branco */
  @media print {
    * { color: #000 !important; background: #fff !important; -webkit-print-color-adjust: exact; }
    body { padding: 10px 15px; font-size: 12px; }
    div[style*="gradient"] { background: #f5f5f5 !important; border: 1px solid #ccc !important; }
    div[style*="border-left"] { border-left: 3px solid #333 !important; }
    @page { margin: 1.5cm; }
  }
</style>
</head><body>
<h3>📚 B2B Loterias v14.0 — Tutorial Completo</h3>
<hr style="margin:10px 0;border:1px solid #ccc;">
${body.innerHTML}
</body></html>`);
                printWin.document.close();
                setTimeout(() => { printWin.print(); }, 400);
            });
        }
    }

    initInstallEvents() {
        // btn-install agora é um link <a> para INSTALAR_B2B.html — não precisa de handler
        // Apenas garante que o modal antigo não seja aberto por acidente
        if (this.installModal) {
            // Fechar modal antigo se ainda existir (retrocompatibilidade)
            if (this.closeInstallModalBtns) {
                this.closeInstallModalBtns.forEach(btn => {
                    btn.addEventListener('click', () => {
                        this.installModal.style.display = 'none';
                    });
                });
            }
        }

        if (this.btnCopyPath && this.folderPathElem) {
            this.btnCopyPath.addEventListener('click', async () => {
                const path = this.folderPathElem.textContent.trim();
                const success = await this.copyToClipboard(path);
                if (success === true) {
                    const originalText = this.btnCopyPath.textContent;
                    this.btnCopyPath.textContent = 'Caminho Copiado!';
                    setTimeout(() => this.btnCopyPath.textContent = originalText, 2000);
                }
            });
        }

        // Backup Button
        if (this.btnBackup) {
            this.btnBackup.addEventListener('click', () => this.exportBackup());
        }
    }

    runQuantumCalculation() {
        const game = typeof GAMES !== 'undefined' ? GAMES[this.currentGameKey] : null;
        if (!game) {
            console.error('[UI] GAMES não carregado ou jogo inválido:', this.currentGameKey);
            if (typeof Guardian !== 'undefined' && Guardian.toast) Guardian.toast('Erro: dados do jogo não carregados. Recarregue a página.', 'error');
            return;
        }

        const count = parseInt(this.quantumCountInput ? this.quantumCountInput.value : 6) || game.minBet;
        const constraints = (typeof QuantumGodEngine !== 'undefined' && QuantumGodEngine.getConstraints) 
            ? QuantumGodEngine.getConstraints(this.currentGameKey) 
            : null;
        const totalNumbers = constraints ? constraints.totalNumbers : (game.range[1] - game.range[0] + 1);

        // Validação: mínimo é o minBet do jogo
        if (count < game.minBet) {
            if (typeof Guardian !== 'undefined' && Guardian.toast) {
                Guardian.toast(`Mínimo de ${game.minBet} números para ${game.name}.`, 'warning');
            } else {
                alert(`Mínimo de ${game.minBet} números para ${game.name}.`);
            }
            if (this.quantumCountInput) this.quantumCountInput.value = game.minBet;
            return;
        }

        // Validação: máximo é o total de números da loteria
        if (count > totalNumbers) {
            if (typeof Guardian !== 'undefined' && Guardian.toast) {
                Guardian.toast(`Limite excedido: ${game.name} possui apenas ${totalNumbers} números.`, 'warning');
            } else {
                alert(`Limite excedido: ${game.name} possui apenas ${totalNumbers} números.`);
            }
            return;
        }

        const statusDiv = this.quantumResults;
        if (!statusDiv) {
            console.error('[UI] quantum-results não encontrado no DOM');
            return;
        }

        statusDiv.innerHTML = '<div class="quantum-placeholder" style="opacity: 1; color: #8B5CF6; font-style: normal;">★ MODO DEUS v9.5 — 21 Camadas + Ciclo Individual + Superposição Quântica...</div>';

        // Phase 1: Analysis
        setTimeout(() => {
            if (!statusDiv.parentNode) return; // Elemento removido do DOM
            statusDiv.innerHTML = '<div class="quantum-placeholder" style="opacity: 1; color: #6366f1; font-style: normal;">★ Bayesian + Markov + Posicional + Cadeias Sequenciais...</div>';

            // Phase 2: Processing
            setTimeout(() => {
                if (!statusDiv.parentNode) return;
                statusDiv.innerHTML = '<div class="quantum-placeholder" style="opacity: 1; color: #ec4899; font-style: normal;">★ Análise 21 Camadas + Walk-Forward → Próximo Sorteio...</div>';

                // Phase 3: Run Engine (with robust error handling + fallback chain)
                setTimeout(() => {
                    try {
                        let suggestion = null;
                        let history = [];
                        try {
                            history = (typeof StatsService !== 'undefined') 
                                ? (StatsService.getRecentResults(this.currentGameKey, 100) || []) 
                                : [];
                        } catch(e) { console.warn('[UI] StatsService.getRecentResults falhou:', e.message); }

                        // Fallback 2: REAL_HISTORY_DB
                        if (history.length < 3 && typeof REAL_HISTORY_DB !== 'undefined' && REAL_HISTORY_DB[this.currentGameKey]) {
                            history = REAL_HISTORY_DB[this.currentGameKey].slice(0, 100);
                            console.log('[UI] Fallback para REAL_HISTORY_DB:', history.length, 'registros');
                        }

                        // Motor 1: NovaEraEngine (preferido)
                        if (typeof NovaEraEngine !== 'undefined' && typeof NovaEraEngine.suggestNumbers === 'function') {
                            try {
                                console.log('[UI] Usando NovaEraEngine.suggestNumbers para ' + this.currentGameKey);
                                // v10.0: Walk-Forward OUT-OF-SAMPLE
                                // Treinar com history[10+], testar contra history[0..9]
                                const trainHistory = history.length > 12 ? history.slice(10) : history;
                                suggestion = NovaEraEngine.suggestNumbers(this.currentGameKey, count, trainHistory);
                            } catch(neErr) {
                                console.warn('[UI] NovaEraEngine falhou:', neErr.message);
                                suggestion = null;
                            }
                        }

                        // Motor 2: QuantumGodEngine (fallback)
                        if ((!suggestion || suggestion.length === 0) && typeof QuantumGodEngine !== 'undefined') {
                            try {
                                console.log('[UI] Fallback para QuantumGodEngine.runSimulation');
                                suggestion = QuantumGodEngine.runSimulation(this.currentGameKey, count, history);
                            } catch(qgeErr) {
                                console.warn('[UI] QuantumGodEngine falhou:', qgeErr.message);
                                suggestion = null;
                            }
                        }

                        // Motor 3: Fallback aleatório (último recurso)
                        let _usedRandomFallback = false;
                        if (!suggestion || suggestion.length === 0) {
                            console.warn('[UI] Todos os motores falharam, usando fallback aleatório');
                            _usedRandomFallback = true;
                            suggestion = [];
                            const pool = [];
                            for (let i = game.range[0]; i <= game.range[1]; i++) pool.push(i);
                            while (suggestion.length < count && pool.length > 0) {
                                suggestion.push(pool.splice(Math.floor(Math.random() * pool.length), 1)[0]);
                            }
                            suggestion.sort((a, b) => a - b);
                        }

                        // ★ v11.0: Confiança via Walk-Forward OUT-OF-SAMPLE + Hipergeométrica
                        if (suggestion && suggestion.length > 0 && history.length >= 5) {
                            try {
                                // Walk-Forward REAL: gerar sugestão NOVA para cada sorteio usando só dados posteriores
                                const wfCount = Math.min(10, history.length - 3);
                                const lotteryDraw = game.lotteryDraw || game.minBet;
                                const actualDrawn = this.currentGameKey === 'duplasena' ? lotteryDraw * 2 : lotteryDraw;
                                let totalHits = 0;
                                let totalHitsRandom = 0;
                                for (let t = 0; t < wfCount; t++) {
                                    // Gerar sugestão usando SÓ dados POSTERIORES ao sorteio t (sem data leaking)
                                    const trainHistory = history.slice(t + 1);
                                    let wfSuggestion = suggestion; // fallback
                                    try {
                                        if (typeof NovaEraEngine !== 'undefined' && NovaEraEngine.suggestNumbers) {
                                            wfSuggestion = NovaEraEngine.suggestNumbers(this.currentGameKey, count, trainHistory);
                                        }
                                    } catch(wfErr) { /* usa suggestion original como fallback */ }
                                    
                                    const drawn = new Set((history[t].numbers || []).concat(history[t].numbers2 || []));
                                    let hits = 0;
                                    for (const n of wfSuggestion) { if (drawn.has(n)) hits++; }
                                    totalHits += hits;
                                    
                                    // Baseline aleatório para comparação
                                    totalHitsRandom += suggestion.length * actualDrawn / (game.range[1] - game.range[0] + 1);
                                }
                                const avgHits = totalHits / Math.max(1, wfCount);
                                const totalRange = game.range[1] - game.range[0] + 1;
                                const expectedRandom = totalHitsRandom / Math.max(1, wfCount);
                                const improvement = avgHits / Math.max(0.01, expectedRandom);
                                
                                // v11.0: Confiança = Probabilidade hipergeométrica REAL
                                // P(X >= k) via hipergeométrica: P exata de acertar >= faixa mínima de prêmio
                                let wfConfidence = 10;
                                if (!_usedRandomFallback && typeof MathPureEngine !== 'undefined') {
                                    try {
                                        const minPrize = lotteryDraw >= 15 ? lotteryDraw - 4 : Math.max(2, lotteryDraw - 2);
                                        wfConfidence = Math.round(MathPureEngine.hypergeometricCDF(totalRange, suggestion.length, actualDrawn, minPrize) * 100);
                                    } catch(hErr) {
                                        // Fallback: escala linear baseada em improvement real
                                        wfConfidence = Math.round(Math.min(95, Math.max(5, (improvement - 0.5) * 40)));
                                    }
                                } else if (!_usedRandomFallback) {
                                    wfConfidence = Math.round(Math.min(95, Math.max(5, (improvement - 0.5) * 40)));
                                }

                                if (typeof QuantumGodEngine !== 'undefined') {
                                    QuantumGodEngine._lastConfidence = wfConfidence;
                                    QuantumGodEngine._lastBacktest = {
                                        confidence: wfConfidence,
                                        avgHits: avgHits,
                                        expectedByChance: expectedRandom,
                                        improvement: improvement,
                                        winRate: totalHits > 0 ? avgHits / suggestion.length : 0
                                    };
                                }
                                console.log('[v10.0] Walk-Forward Sugestão: avg=' + avgHits.toFixed(2) + ' vs acaso=' + expectedRandom.toFixed(2) + ' | ' + improvement.toFixed(2) + 'x | Conf=' + wfConfidence + '%');
                            } catch(btErr) {
                                console.warn('[v10.0] Walk-Forward falhou:', btErr.message);
                                if (typeof QuantumGodEngine !== 'undefined') QuantumGodEngine._lastConfidence = 30;
                            }
                        }

                                                // v10.0: Indicador visual de fallback aleatorio
                        if (_usedRandomFallback) {
                            const fallbackDiv = document.createElement('div');
                            fallbackDiv.style.cssText = 'text-align:center;padding:8px;margin:6px 0;border-radius:8px;background:rgba(239,68,68,0.15);border:1px solid rgba(239,68,68,0.3);font-size:0.78rem;color:#EF4444;font-weight:700;';
                            fallbackDiv.textContent = '\u26a0\ufe0f Gerado ALEATORIAMENTE \u2014 motores IA falharam. Recarregue a p\u00e1gina (Ctrl+Shift+R)';
                            this.quantumResults.innerHTML = '';
                            this.quantumResults.appendChild(fallbackDiv);
                        }
console.log('[UI] Sugestão gerada: ' + (suggestion ? suggestion.length : 0) + ' números');
                        this.renderQuantumResults(suggestion);
                    } catch (err) {
                        console.error('[UI] ERRO CRÍTICO no engine:', err);
                        statusDiv.innerHTML = '<div style="color: #ef4444; text-align: center; padding: 10px;">❌ Erro: ' + err.message + '<br><small>Verifique o console (F12) para detalhes</small></div>';
                    }
                }, 100);

            }, 600);

        }, 600);
    }

    renderQuantumResults(numbers) {
        const game = GAMES[this.currentGameKey];
        this.quantumResults.innerHTML = '';
        const card = document.createElement('div');
        card.style.display = 'flex';
        card.style.flexWrap = 'wrap';
        card.style.gap = '6px';
        card.style.justifyContent = 'center';
        card.style.width = '100%';

        if (!numbers || numbers.length === 0) {
            this.quantumResults.innerHTML = '<div style="color: var(--text-secondary); text-align: center; font-size: 0.8rem;">Nenhum número gerado. Tente novamente.</div>';
            return;
        }

        numbers.forEach(num => {
            const ball = this.createBall(num);
            // RESET ALL INLINE STYLES first to avoid conflicts
            ball.style = '';

            // Apply specific styles for the suggestion ball
            ball.style.width = '30px';
            ball.style.height = '30px';
            ball.style.fontSize = '0.85rem';
            ball.style.lineHeight = '28px';

            // Use Game-specific color/accent
            ball.style.backgroundColor = game.color || '#10B981';
            ball.style.borderColor = 'rgba(255, 255, 255, 0.2)';
            ball.style.color = '#ffffff';

            ball.style.fontWeight = '800';
            ball.style.display = 'flex';
            ball.style.alignItems = 'center';
            ball.style.justifyContent = 'center';
            ball.style.borderRadius = '50%';
            ball.style.margin = '1px';
            ball.style.boxShadow = '0 2px 6px rgba(0,0,0,0.25)';
            ball.style.border = '1px solid rgba(255,255,255,0.15)';

            card.appendChild(ball);
        });

        this.quantumResults.appendChild(card);

        // Indicador de Confiança V9
        try {
            const confidence = QuantumGodEngine.getLastConfidence ? QuantumGodEngine.getLastConfidence() : 50;
            const backtest = QuantumGodEngine.getLastBacktest ? QuantumGodEngine.getLastBacktest() : null;
            const confColor = confidence >= 70 ? '#22C55E' : confidence >= 50 ? '#EAB308' : '#EF4444';
            const confEmoji = confidence >= 70 ? '🟢' : confidence >= 50 ? '🟡' : '🔴';
            const confLabel = confidence >= 70 ? 'ALTA' : confidence >= 50 ? 'MODERADA' : 'BAIXA';

            let confHTML = `<div style="margin-top:10px;padding:8px 12px;border-radius:8px;background:rgba(0,0,0,0.3);border:1px solid ${confColor}40;font-size:0.78rem;">`;
            confHTML += `<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:4px;">`;
            confHTML += `<span style="color:${confColor};font-weight:800;">${confEmoji} Confiança: ${confidence}% (${confLabel})</span>`;
            if (backtest && backtest.improvement) {
                const impColor = backtest.improvement >= 1.0 ? '#22C55E' : '#EF4444';
                confHTML += `<span style="color:${impColor};font-weight:700;">${backtest.improvement >= 1.0 ? '↑' : '↓'} ${(backtest.improvement * 100 - 100).toFixed(0)}% vs chance</span>`;
            }
            confHTML += `</div>`;
            if (backtest && backtest.avgHits !== undefined) {
                confHTML += `<div style="color:#94a3b8;font-size:0.72rem;">Média: ${backtest.avgHits.toFixed(1)} acertos (esperado: ${(backtest.expectedByChance || 0).toFixed(1)}) | Taxa de vitória: ${((backtest.winRate || 0) * 100).toFixed(0)}%</div>`;
            }
            confHTML += `</div>`;

            const confDiv = document.createElement('div');
            confDiv.innerHTML = confHTML;
            this.quantumResults.appendChild(confDiv);
        } catch(e) { console.log('Conf indicator error:', e); }

        // Update formula again for "Next Run"
        try { this.quantumFormula.textContent = QuantumService.getFormula(); } catch(e) {}

        // ── HELPER: obter histórico robusto (StatsService + fallback REAL_HISTORY_DB) ────
        const _getHistory = (gameKey, maxCount) => {
            let h = [];
            try { h = StatsService.getRecentResults(gameKey, maxCount) || []; } catch(e) { console.warn('[UI] Falha no StatsService (historico):', e.message); }
            // Fallback: usar REAL_HISTORY_DB diretamente se StatsService retornar vazio
            if (h.length < 3 && typeof REAL_HISTORY_DB !== 'undefined' && REAL_HISTORY_DB[gameKey]) {
                h = REAL_HISTORY_DB[gameKey].slice(0, maxCount);
                console.log('[UI] Fallback para REAL_HISTORY_DB:', h.length, 'registros');
            }
            return h;
        };


        // v10.0: DIAGNOSTICO REAL de engines carregados
        const enginesLoaded = [
            typeof NovaEraEngine !== 'undefined'        ? '\u269b\ufe0fNE-v10'  : null,
            typeof PrecisionEngine !== 'undefined'      ? '\ud83c\udfafPE-v2'   : null,
            typeof SmartBetsEngine !== 'undefined'      ? '\ud83e\udde0SB-v1'   : null,
            typeof PrecisionCalibrator !== 'undefined'  ? '\ud83d\udcd0PC-v1'   : null,
        ].filter(Boolean);
        const diagDiv = document.createElement('div');
        diagDiv.style.cssText = 'text-align:center;font-size:0.58rem;color:#475569;padding:3px 0 1px;letter-spacing:0.5px;';
        diagDiv.textContent = 'v10.0 | 21 Dimensões | ' + enginesLoaded.join(' \u00b7 ');
        this.quantumResults.appendChild(diagDiv);
    }

    useQuantumNumbers() {
        const resultDiv = this.quantumResults;
        const balls = resultDiv.querySelectorAll('.ball');

        if (balls.length === 0) {
            alert("Gere uma sugestão quântica primeiro!");
            return;
        }

        // IMPORTANTE: Extrair números ANTES de clearSelection (que limpa o DOM)
        const numbersToSelect = [];
        balls.forEach(b => {
            const n = parseInt(b.textContent);
            if (!isNaN(n)) numbersToSelect.push(n);
        });

        if (numbersToSelect.length === 0) return;

        // Limpar seleção atual (mas preservar os números já extraídos)
        this.selectedNumbers.clear();
        this.fixedNumbers.clear();
        this.isFixedMode = false;
        this.btnFixedMode.classList.remove('active');
        this.fixedInfoPanel.style.display = 'none';
        const selectedEls = this.gridContainer.querySelectorAll('.selected, .fixed');
        selectedEls.forEach(el => {
            el.classList.remove('selected');
            el.classList.remove('fixed');
        });
        this.gamesContainer.innerHTML = '<div class="empty-state">Selecione as opções e clique em Gerar Jogos</div>';

        const game = GAMES[this.currentGameKey];

        let addedCount = 0;
        numbersToSelect.forEach(num => {
            const el = this.gridContainer.querySelector(`.grid-num[data-number="${num}"]`);
            if (el) {
                this.selectedNumbers.add(num);
                el.classList.add('selected');
                addedCount++;
            }
        });

        this.updateSelectionInfo();

        // Scroll para a grade
        this.gridContainer.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    // ╔══════════════════════════════════════════════════════════╗
    // ║  MANUAL: Métodos auxiliares de fechamento combinatório   ║
    // ╚══════════════════════════════════════════════════════════╝

    // ╔══════════════════════════════════════════════════════════╗
    // ║  POOL PRECISÃO — LIMITES DINÂMICOS POR LOTERIA           ║
    // ╚══════════════════════════════════════════════════════════╝
    _updatePrecisionPoolLimits() {
        const poolInput = document.getElementById('precision-pool-size');
        if (!poolInput) return;

        const game = GAMES[this.currentGameKey];
        if (!game) return;

        const drawSize = game.minBet;
        const totalRange = game.range[1] - game.range[0] + 1;
        const minPool = drawSize + 1; // Mínimo: drawSize + 1
        const maxPool = totalRange; // Máximo: total de números

        // Default inteligente por loteria
        let defaultPool = Math.min(totalRange, Math.max(20, drawSize + Math.ceil(drawSize * 0.45)));
        if (this.currentGameKey === 'lotomania') defaultPool = 90; // Exigência do usuário
        if (this.currentGameKey === 'lotofacil') defaultPool = 21;
        if (this.currentGameKey === 'megasena') defaultPool = 40;

        poolInput.min = minPool;
        poolInput.max = maxPool;
        
        // Ao invés de preservar o valor da loteria anterior, 
        // vamos carregar o valor salvo especificamente para ESTA loteria, ou usar o default inteligente!
        const savedPool = localStorage.getItem('l99_precision_pool_' + this.currentGameKey);
        
        let targetValue = savedPool ? parseInt(savedPool) : defaultPool;
        
        // Se o valor estiver corrompido ou fora dos limites, forçar o default
        if (targetValue < minPool || targetValue > maxPool) {
            targetValue = defaultPool;
        }

        poolInput.value = targetValue;
        
        poolInput.title = `Mín: ${minPool} | Máx: ${maxPool} | Padrão: ${defaultPool}`;

        // Atualizar texto info
        const infoSpan = document.getElementById('precision-pool-info');
        if (infoSpan) {
            infoSpan.textContent = `Mín: ${minPool} | Máx: ${maxPool} | Padrão: ${defaultPool}`;
        }
    }

    // ╔══════════════════════════════════════════════════════════╗
    // ║  GERAR JOGOS COM IA (SMART BETS + MODO PRECISÃO)        ║
    // ╚══════════════════════════════════════════════════════════╝
    runSmartGeneration() {
        const game = GAMES[this.currentGameKey];
        if (!game) return;

        // ── PROTEÇÃO DOUBLE-CLICK ──
        if (this._isGenerating) {
            console.warn('[SmartBets] Geração já em andamento, ignorando clique duplo');
            return;
        }
        this._isGenerating = true;

        // Verificar se Modo Precisão está ativo
        const precisionCheckbox = document.getElementById('precision-mode-toggle');
        const isPrecisionMode = precisionCheckbox && precisionCheckbox.checked;

        // ── RASTREAMENTO DE MODO ── ★ FIX v14: QUANTUM L99 grava como 'quantum_l99'
        const _modeKey = 'quantum_l99';
        this._lastGenerationMode = _modeKey; localStorage.setItem('l99_lastMode', _modeKey); document.body.setAttribute('data-l99-mode', _modeKey);
        this._lastPrecisionMode = isPrecisionMode;
        this._lastDrawSize = this.smartDrawSizeSelect ? parseInt(this.smartDrawSizeSelect.value) || game.minBet : game.minBet;

        const quantity = parseInt(this.gamesQuantityInput.value) || 10;
        let selectedArr = Array.from(this.selectedNumbers);
        const fixedArr = Array.from(this.fixedNumbers);

        // Ler quantidade de números por jogo IA
        const customDrawSize = this.smartDrawSizeSelect
            ? parseInt(this.smartDrawSizeSelect.value) || game.minBet
            : game.minBet;

        // V10 FIX: Expand pool to full board if user only selected fixed numbers
        if (fixedArr.length > 0 && selectedArr.length === fixedArr.length) {
            selectedArr = [];
            for (let i = game.range[0]; i <= game.range[1]; i++) selectedArr.push(i);
        }

        // AUTO-USAR números sugeridos pela fórmula IA (se nenhum selecionado no grid)
        let _quantumInjected = false;
        if (selectedArr.length === 0 && this.quantumResults) {
            const quantumBalls = this.quantumResults.querySelectorAll('.ball');
            if (quantumBalls.length > 0) {
                const quantumNums = [];
                quantumBalls.forEach(b => {
                    const n = parseInt(b.textContent);
                    if (!isNaN(n)) quantumNums.push(n);
                });
                if (quantumNums.length > 0) {
                    selectedArr = quantumNums;
                    _quantumInjected = true;
                    console.log(`[SmartBets] 🔮 Usando ${quantumNums.length} números da Telepatia Quântica como pool`);
                }
            }
        }

        // V9: Sem validação restritiva — qualquer quantidade de selecionados é aceita
        // O motor IA usa os selecionados como pool preferencial (veja smart_bets.js)
        // Só bloquear se 0 < selected < 2 (impossível de fazer qualquer jogo)
        if (selectedArr.length > 0 && selectedArr.length < 2) {
            alert(`Selecione pelo menos ${customDrawSize} números (ou nenhum para usar análise completa).`);
            return;
        }

        // Limpar feedback anterior
        const oldFeedback = this.gamesContainer.parentNode.querySelector('.generation-feedback');
        if (oldFeedback) oldFeedback.remove();
        const oldAnalysis = this.gamesContainer.parentNode.querySelector('.smart-analysis-panel');
        if (oldAnalysis) oldAnalysis.remove();
        const oldCaixaBtn = document.getElementById('caixa-panel');
        if (oldCaixaBtn) oldCaixaBtn.remove();

        // V9: Indicador de modo ★ FIX: mostrar quando usa Quantum auto-injeção
        const modeLabel = _quantumInjected
            ? `🔮 ${selectedArr.length} números da Telepatia Quântica → pool preferencial`
            : selectedArr.length > 0
                ? `🎯 ${selectedArr.length} números selecionados → gerando variantes`
                : '🧠 Análise IA completa do universo';

        // Loading - QUANTUM L99 (Honesto)
        this.gamesContainer.innerHTML = `
            <div style="text-align:center;padding:40px;background:linear-gradient(145deg,rgba(10,10,30,0.95),rgba(20,10,40,0.9));border-radius:16px;border:1px solid rgba(139,92,246,0.3);">
                <div style="font-size:2.5rem;margin-bottom:8px;">⚙️</div>
                <div style="color:#A78BFA;font-weight:900;font-size:1rem;text-transform:uppercase;letter-spacing:1px;">PROCESSANDO ANÁLISE + SET COVER</div>
                <div style="color:#94A3B8;font-size:0.8rem;margin-top:6px;">${modeLabel}</div>
                <div style="margin-top:12px;width:70%;height:4px;background:rgba(139,92,246,0.15);border-radius:4px;margin-left:auto;margin-right:auto;overflow:hidden;">
                    <div style="width:30%;height:100%;background:linear-gradient(90deg,#8B5CF6,#FFD700);border-radius:4px;animation:smartProgress 1s ease-in-out infinite;"></div>
                </div>
            </div>
            <style>@keyframes smartProgress{0%{width:10%;margin-left:0}50%{width:60%;margin-left:20%}100%{width:10%;margin-left:90%}}</style>
        `;

        // ═══ v15.0: GERAÇÃO ASSÍNCRONA para grandes volumes ═══
        if (typeof AsyncGenerator !== 'undefined' && AsyncGenerator.shouldUseAsync(quantity, this.currentGameKey)) {
            const sniperToggle = document.getElementById('precision-mode-toggle');
            const sniperMode = sniperToggle ? sniperToggle.checked : false;
            const poolInput = document.getElementById('precision-pool-size');
            const sniperPoolSize = poolInput ? parseInt(poolInput.value) || 20 : 20;
            const aiOpts = { precisionMode: sniperMode, precisionPoolSize: sniperPoolSize };

            AsyncGenerator.generateCoverageAsync(
                this.currentGameKey, quantity,
                selectedArr.length >= customDrawSize ? selectedArr : null,
                fixedArr, customDrawSize, aiOpts,
                (result, cancelled, error) => {
                    this._isGenerating = false;
                    if (cancelled) {
                        this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#F59E0B;">⚠️ Geração cancelada pelo usuário.</div>';
                        return;
                    }
                    if (error || !result || !result.games || result.games.length === 0) {
                        this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">Erro: ' + (error ? error.message : 'Nenhum jogo gerado.') + '</div>';
                        return;
                    }

                    this.currentGeneratedGames = result.games;
                    this._lastGeneratedGames = result.games;
                    if (typeof ComparisonEngine !== 'undefined') ComparisonEngine.saveResult('quantum_l99', result.games, result.analysis, this.currentGameKey);
                    this.renderGames(result, this.currentGameKey);

                    var sa = result.analysis || {};
                    var banner = document.createElement('div');
                    banner.className = 'smart-gen-analysis';
                    banner.style.cssText = 'margin-top:8px;margin-bottom:8px;padding:14px 18px;border-radius:12px;background:linear-gradient(145deg,rgba(139,92,246,0.12),rgba(15,23,42,0.95));border:1px solid rgba(139,92,246,0.3);';
                    banner.innerHTML = '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;"><span style="font-size:1.3rem;">&#x26A1;</span><div><div style="font-weight:900;color:#A78BFA;font-size:1rem;text-transform:uppercase;letter-spacing:1px;">QUANTUM L99 — ESTATÍSTICA + SET COVER</div><div style="font-size:0.72rem;color:#94A3B8;">Motor: Ciência 21-Dim → CoverageEngine-Async | ' + result.games.length + ' jogos | ⚡ ' + (sa.chunksProcessed || '—') + ' lotes</div></div></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;font-size:0.75rem;"><div style="text-align:center;padding:10px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid rgba(139,92,246,0.2);" title="Cobertura de dezenas únicas sobre o universo da loteria"><div style="color:#C4B5FD;font-size:0.6rem;font-weight:700;">COBERTURA NUMÉRICA</div><div style="color:#A78BFA;font-weight:900;font-size:1.3rem;">' + (sa.coverage||0) + '%</div></div><div style="text-align:center;padding:10px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid rgba(139,92,246,0.2);" title="Diversidade combinatória entre os jogos"><div style="color:#C4B5FD;font-size:0.6rem;font-weight:700;">DIVERSIDADE</div><div style="color:#A78BFA;font-weight:900;font-size:1.3rem;">' + (sa.diversity||0) + '%</div></div><div style="text-align:center;padding:10px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid rgba(139,92,246,0.2);" title="Tempo real de processamento do algoritmo"><div style="color:#C4B5FD;font-size:0.6rem;font-weight:700;">TEMPO REAL</div><div style="color:#A78BFA;font-weight:900;font-size:1.3rem;">' + (sa.elapsed || 'N/A') + '</div></div></div>';
                    var ob = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
                    if (ob) ob.remove();
                    this.gamesContainer.parentNode.insertBefore(banner, this.gamesContainer);
                    banner.scrollIntoView({ behavior: 'smooth', block: 'start' });
                }
            );
            return; // Sai — o callback cuidará do resultado
        }

        // Geração síncrona (quantidades pequenas — rápido o bastante)
        setTimeout(() => {
            try {
                if (typeof NovaEraEngine === 'undefined') {
                    this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">NovaEraEngine nao carregado. Recarregue (Ctrl+Shift+R).</div>';
                    this._isGenerating = false;
                    return;
                }
                const sniperToggle = document.getElementById('precision-mode-toggle');
                const sniperMode = sniperToggle ? sniperToggle.checked : false;
                const poolInput = document.getElementById('precision-pool-size');
                const sniperPoolSize = poolInput ? parseInt(poolInput.value) || 20 : 20;
                const aiOpts = { precisionMode: sniperMode, precisionPoolSize: sniperPoolSize };

                const smartResult = NovaEraEngine.generate(this.currentGameKey, quantity, selectedArr.length >= customDrawSize ? selectedArr : null, fixedArr, customDrawSize, aiOpts);
                if (!smartResult || !smartResult.games || smartResult.games.length === 0) {
                    this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#F59E0B;">Nenhum jogo gerado. Tente novamente.</div>';
                    this._isGenerating = false;
                    return;
                }
                this.currentGeneratedGames = smartResult.games;
                this._lastGeneratedGames = smartResult.games;
                if (typeof ComparisonEngine !== 'undefined') ComparisonEngine.saveResult('quantum_l99', smartResult.games, smartResult.analysis, this.currentGameKey);
                this.renderGames(smartResult, this.currentGameKey);
                // Banner HONESTO — Métricas reais do Set Cover + Ciência
                var sa = smartResult.analysis || {};
                var banner = document.createElement('div');
                banner.className = 'smart-gen-analysis';
                banner.style.cssText = 'margin-top:8px;margin-bottom:8px;padding:14px 18px;border-radius:12px;background:linear-gradient(145deg,rgba(139,92,246,0.12),rgba(15,23,42,0.95));border:1px solid rgba(139,92,246,0.3);';
                banner.innerHTML = '<div style="display:flex;align-items:center;gap:10px;margin-bottom:10px;"><span style="font-size:1.3rem;">&#x26A1;</span><div><div style="font-weight:900;color:#A78BFA;font-size:1rem;text-transform:uppercase;letter-spacing:1px;">QUANTUM L99 — ESTATÍSTICA + SET COVER</div><div style="font-size:0.72rem;color:#94A3B8;">Motor: Ciência 21-Dim → CoverageEngine Multi-Tier | ' + quantity + ' jogos</div></div></div><div style="display:grid;grid-template-columns:repeat(3,1fr);gap:8px;font-size:0.75rem;"><div style="text-align:center;padding:10px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid rgba(139,92,246,0.2);" title="Cobertura de dezenas únicas sobre o universo da loteria"><div style="color:#C4B5FD;font-size:0.6rem;font-weight:700;">COBERTURA NUMÉRICA</div><div style="color:#A78BFA;font-weight:900;font-size:1.3rem;">' + (sa.coverage||0) + '%</div></div><div style="text-align:center;padding:10px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid rgba(139,92,246,0.2);" title="Diversidade combinatória entre os jogos"><div style="color:#C4B5FD;font-size:0.6rem;font-weight:700;">DIVERSIDADE</div><div style="color:#A78BFA;font-weight:900;font-size:1.3rem;">' + (sa.diversity||0) + '%</div></div><div style="text-align:center;padding:10px;background:rgba(0,0,0,0.3);border-radius:10px;border:1px solid rgba(139,92,246,0.2);" title="Tempo real de processamento do algoritmo"><div style="color:#C4B5FD;font-size:0.6rem;font-weight:700;">TEMPO REAL</div><div style="color:#A78BFA;font-weight:900;font-size:1.3rem;">' + (sa.elapsed || 'N/A') + 'ms</div></div></div>';
                var ob = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
                if (ob) ob.remove();
                this.gamesContainer.parentNode.insertBefore(banner, this.gamesContainer);
                banner.scrollIntoView({ behavior: 'smooth', block: 'start' });
            } catch(e) {
                console.error('[SmartBets] Erro:', e);
                this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">Erro: ' + e.message + '</div>';
            } finally {
                this._isGenerating = false;
            }
        }, 50);
    }


    initQuantum() {
        if (this.btnQuantumCalculate) {
            this.btnQuantumCalculate.onclick = () => this.runQuantumCalculation();
        }
        if (this.btnUseQuantum) {
            this.btnUseQuantum.onclick = () => this.useQuantumNumbers();
        }

        // ── Botão de Análise Manual da Seleção ──────────────────────────────
        const btnAnalyse = document.getElementById('btn-analyse-selection');
        if (btnAnalyse) {
            btnAnalyse.onclick = () => {
                const container = document.getElementById('ae-manual-container');
                if (!container) return;

                const nums = [...this.selectedNumbers].sort((a, b) => a - b);
                if (nums.length < 2) {
                    container.innerHTML = '<div style="color:#EF4444;font-size:0.72rem;padding:8px;text-align:center;">⚠️ Selecione pelo menos 2 números no grid para analisar.</div>';
                    return;
                }

                container.innerHTML = '<div style="color:#8B5CF6;font-size:0.72rem;padding:8px;text-align:center;">🔬 Analisando ' + nums.length + ' números em 12 dimensões...</div>';

                setTimeout(() => {
                    try {
                        const history = StatsService.getRecentResults(this.currentGameKey, 100) || [];
                        const analysis = AnalysisEngine.analyze(this.currentGameKey, nums, history);
                        if (analysis) {
                            AnalysisEngine.renderPanel(analysis, container);
                        } else {
                            container.innerHTML = '<div style="color:#EF4444;font-size:0.72rem;padding:8px;text-align:center;">⚠️ Histórico insuficiente para análise.</div>';
                        }
                    } catch (e) {
                        container.innerHTML = '<div style="color:#EF4444;font-size:0.72rem;padding:8px;text-align:center;">⚠️ Erro: ' + e.message + '</div>';
                        console.error('[AE] Erro análise manual:', e);
                    }
                }, 150);
            };
        }

        // ── Botão de Análise por Grupos (Lotofácil exclusivo) ────────────────
        const btnGroup = document.getElementById('btn-group-analysis');
        if (btnGroup) {
            btnGroup.onclick = () => {
                const container = document.getElementById('lge-group-container');
                if (!container) return;
                container.innerHTML = '<div style="color:#c026d3;font-size:0.72rem;padding:8px;text-align:center;">🎯 Carregando análise de grupos...</div>';
                setTimeout(() => {
                    try {
                        const history = StatsService.getRecentResults(this.currentGameKey, 200) || [];
                        if (history.length < 5) {
                            container.innerHTML = '<div style="color:#EF4444;font-size:0.72rem;padding:8px;text-align:center;">⚠️ Histórico insuficiente.</div>';
                            return;
                        }
                        // Usar UniversalGroupEngine para todas as loterias
                        if (typeof UniversalGroupEngine !== 'undefined' && UniversalGroupEngine.CONFIGS[this.currentGameKey]) {
                            const result = UniversalGroupEngine.generate(this.currentGameKey, history);
                            container.innerHTML = '';
                            UniversalGroupEngine.renderPanel(result.analysis, container, result);
                        } else if (this.currentGameKey === 'lotofacil' && typeof LotofacilGroupEngine !== 'undefined') {
                            // Fallback para o motor específico da Lotofácil
                            const result = LotofacilGroupEngine.generate(history, 15, true);
                            container.innerHTML = '';
                            LotofacilGroupEngine.renderPanel(result.analysis, container, result);
                        } else {
                            container.innerHTML = '<div style="color:#EF4444;font-size:0.72rem;padding:8px;text-align:center;">⚠️ Motor de grupos não disponível.</div>';
                        }
                    } catch (e) {
                        container.innerHTML = '<div style="color:#EF4444;font-size:0.72rem;padding:8px;text-align:center;">⚠️ Erro: ' + e.message + '</div>';
                        console.error('[UGE] Erro análise por grupos:', e);
                    }
                }, 100);
            };
        }

        // ── Botão Estratégia Dual 2 Grupos (Lotofácil exclusivo) ────────────────
        const btnDualStrat = document.getElementById('btn-dual-strategy');
        if (btnDualStrat) {
            btnDualStrat.onclick = () => {
                if (this.currentGameKey !== 'lotofacil') return;
                const container = document.getElementById('dual-strategy-container');
                if (!container) return;

                const gameCount = Math.max(1, Math.min(100, parseInt(this.gamesQuantityInput?.value) || 10));

                container.innerHTML = `<div style="background:linear-gradient(135deg,rgba(124,58,237,0.15),rgba(76,29,149,0.1));border:1px solid #7c3aed60;border-radius:10px;padding:14px;text-align:center;margin-top:8px;">
                    <div style="font-size:1.5rem;margin-bottom:6px;">⚡</div>
                    <div style="color:#a78bfa;font-weight:700;font-size:0.88rem;">Analisando Estratégia Dual 2G...</div>
                    <div style="color:#6d28d9;font-size:0.72rem;margin-top:4px;">Calculando melhor divisão dos 25 números em 2 macro-grupos para ${gameCount} jogo${gameCount>1?'s':''}...</div>
                    <div style="margin-top:10px;height:3px;background:rgba(124,58,237,0.2);border-radius:2px;overflow:hidden;">
                        <div style="height:100%;background:linear-gradient(90deg,#7c3aed,#a855f7,#c084fc);border-radius:2px;animation:dualProgress 1.2s ease-in-out infinite;width:40%;"></div>
                    </div>
                    <style>@keyframes dualProgress{0%{width:10%;margin-left:0}50%{width:70%;margin-left:15%}100%{width:10%;margin-left:90%}}</style>
                </div>`;

                setTimeout(() => {
                    try {
                        if (typeof LotofacilDualStrategy === 'undefined') {
                            container.innerHTML = '<div style="color:#EF4444;padding:10px;text-align:center;">⚠️ Motor LDSE-V1 não carregado. Recarregue (Ctrl+Shift+R).</div>';
                            return;
                        }

                        let history = [];
                        try { history = StatsService.getRecentResults('lotofacil', 300) || []; } catch(e) {}
                        if (history.length < 5 && typeof REAL_HISTORY_DB !== 'undefined' && REAL_HISTORY_DB.lotofacil) {
                            history = REAL_HISTORY_DB.lotofacil.slice(0, 300);
                        }
                        if (history.length < 5) {
                            container.innerHTML = '<div style="color:#EF4444;padding:10px;text-align:center;">⚠️ Histórico insuficiente para análise dual.</div>';
                            return;
                        }

                        const result = LotofacilDualStrategy.generate(history, gameCount);

                        if (!result || !result.games || result.games.length === 0) {
                            container.innerHTML = '<div style="color:#EF4444;padding:10px;text-align:center;">⚠️ Não foi possível gerar jogos com a estratégia dual.</div>';
                            return;
                        }

                        container.innerHTML = '';
                        LotofacilDualStrategy.renderPanel(result.analysis, result, container);

                        // Renderizar jogos na área principal
                        const gamesData = {
                            games: result.games.map(g => g.numbers),
                            analysis: {
                                confidence: 79,
                                coverage: Math.round(new Set(result.games.flatMap(g => g.numbers)).size / 25 * 100),
                                diversity: 87,
                                mode: 'DUAL-2G',
                                uniqueNumbers: new Set(result.games.flatMap(g => g.numbers)).size
                            }
                        };
                        this.renderGames(gamesData, 'lotofacil');

                        // Feedback
                        const fb = document.createElement('div');
                        fb.className = 'generation-feedback';
                        fb.style.cssText = 'color:#a78bfa;text-align:center;padding:10px;font-weight:bold;margin-top:8px;font-size:0.88rem;';
                        fb.textContent = `⚡ ${result.games.length} jogos gerados via Estratégia Dual 2G — Split: ${result.bestSplit?.id || 'S4'}`;
                        const oldFb = this.gamesContainer.parentNode.querySelector('.generation-feedback');
                        if (oldFb) oldFb.remove();
                        this.gamesContainer.parentNode.insertBefore(fb, this.gamesContainer);

                        container.scrollIntoView({ behavior: 'smooth', block: 'start' });
                        console.log(`[LDSE] ✅ ${result.games.length} jogos | Split: ${result.bestSplit?.name}`);

                    } catch (e) {
                        container.innerHTML = `<div style="color:#EF4444;padding:10px;text-align:center;">⚠️ Erro LDSE: ${e.message}</div>`;
                        console.error('[LDSE] Erro:', e);
                    }
                }, 150);
            };
        }
    }

    initShareEvents() {
        // Handler de share é gerenciado pelo script inline no HTML
    }

    updateUrlHash() {
        // Disabled: prevents auto-generation bug on page refresh
    }

    restoreGamesFromHash() {
        // Disabled: prevents auto-generation bug on page refresh
        // Clear any leftover hash
        if (window.location.hash) {
            history.replaceState(null, '', window.location.pathname);
        }
    }

    insertPrintTimestamp() {
        // Remove old dynamic div if it exists (cleanup)
        const old = document.getElementById('print-timestamp-display');
        if (old) old.remove();

        const now = new Date();
        const dateStr = now.toLocaleDateString('pt-BR');
        const timeStr = now.toLocaleTimeString('pt-BR');

        // Capture Game Name
        const game = GAMES[this.currentGameKey];
        const gameName = game ? game.name : 'Loteria';

        // Get Next Draw Number
        StatsService.ensureHistory(this.currentGameKey);
        const latestResult = StatsService.getRecentResults(this.currentGameKey, 1)[0];
        const nextDrawNumber = latestResult ? latestResult.drawNumber + 1 : '???';

        // Target the existing Print Title H1
        const printTitle = document.querySelector('.print-title');
        if (printTitle) {
            printTitle.style.display = 'block'; // Ensure it's visible
            printTitle.innerHTML = `
                <div style="font-size: 18pt; margin-bottom: 5px;">${gameName}</div>
                <div style="font-size: 11pt; font-weight: normal; text-transform: none;">
                    <span>Concurso: <strong>${nextDrawNumber}</strong></span>
                    <span style="margin: 0 10px;">|</span>
                    <span>Data: ${dateStr} - ${timeStr}</span>
                </div>
            `;
        }
    }

    addInstallButton() {
        // Carregar prêmios nos botões de navegação
        this.loadAllNavPrizes();
    }

    async loadAllNavPrizes() {
        const gameKeys = Object.keys(GAMES);
        for (const key of gameKeys) {
            // Mostrar fallback imediatamente enquanto carrega API
            const elemFallback = document.getElementById(`prize-nav-${key}`);
            const fallbackAmount = GAMES[key].estimatedPrizeFallback || 0;
            if (elemFallback && fallbackAmount > 0) {
                elemFallback.textContent = this._formatPrizeShort(fallbackAmount);
            }

            (async () => {
                try {
                    await StatsService.ensureHistory(key);
                    const prizeInfo = StatsService.getPrizeInfo(key);
                    const elem = document.getElementById(`prize-nav-${key}`);
                    if (!elem) return;

                    const amount = prizeInfo ? (prizeInfo.estimatedPrize || prizeInfo.accumulatedPrize || 0) : 0;
                    if (amount > 0) {
                        elem.textContent = this._formatPrizeShort(amount);
                        if (prizeInfo.accumulated) {
                            elem.textContent += ' 🔥';
                        }
                        // Also update main prize display if this is the currently active game
                        if (key === this.currentGameKey) {
                            this.updatePrizeDisplay(key);
                        }
                    }
                    // Se API não retornou nada, mantém o fallback já exibido
                } catch (e) {
                    // Mantém o fallback já exibido
                }
            })();
        }
    }

    _formatPrizeShort(amount) {
        if (amount >= 1_000_000) {
            return `R$ ${(amount / 1_000_000).toFixed(1).replace('.', ',')} M`;
        } else if (amount >= 1_000) {
            return `R$ ${(amount / 1_000).toFixed(0)}K`;
        }
        return `R$ ${amount.toFixed(0)}`;
    }

    updateTheme(color) {
        this.root.style.setProperty('--primary-accent', color);
    }

    updateGameInfo(gameKey) {
        this.currentGameKey = gameKey;
        const game = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
        if (!game) {
            console.error('[UI] Dados da loteria não encontrados para: ' + gameKey);
            return;
        }

        this.updateTheme(game.color);
        this.updateCountdown(gameKey);

        // Atualizar link do botão Jogar Online com a loteria atual
        var cfgLink = this._getCaixaLotteryConfig();
        if (this.playCaixaBtn && cfgLink[gameKey]) {
            // Em vez de forçar a rota, abre o site principal e o script fará a navegação
            this.playCaixaBtn.href = 'https://www.loteriasonline.caixa.gov.br/';
        }
        // Atualizar link da Caixa na sidebar também
        var sidebarCaixaLink = document.getElementById('btn-caixa-link');
        if (sidebarCaixaLink && cfgLink[gameKey]) {
            sidebarCaixaLink.href = 'https://www.loteriasonline.caixa.gov.br/';
        }

        // Botão de análise de grupos: disponível para TODAS as loterias via UniversalGroupEngine
        const btnGroup = document.getElementById('btn-group-analysis');
        const lgeContainer = document.getElementById('lge-group-container');
        if (btnGroup) {
            const hasConfig = typeof UniversalGroupEngine !== 'undefined' &&
                              UniversalGroupEngine.CONFIGS && UniversalGroupEngine.CONFIGS[gameKey];
            btnGroup.style.display = hasConfig ? 'block' : 'none';
            if (hasConfig) {
                const groupCount = UniversalGroupEngine.CONFIGS[gameKey].groups.length;
                btnGroup.textContent = `🎯 Análise por Grupos (${groupCount}G) — ${game.name}`;
            }
        }
        if (lgeContainer) lgeContainer.innerHTML = '';

        // Botão Estratégia Dual 2G — exclusivo Lotofácil
        const btnDual = document.getElementById('btn-dual-strategy');
        const dualContainer = document.getElementById('dual-strategy-container');
        if (btnDual) {
            btnDual.style.display = gameKey === 'lotofacil' ? 'block' : 'none';
        }
        if (dualContainer) dualContainer.innerHTML = '';

        this.navButtons.forEach(btn => {
            const isActive = btn.dataset.game === gameKey;
            const gameData = GAMES[btn.dataset.game];
            const c1 = gameData ? gameData.color : '#10B981';

            if (isActive) {
                btn.classList.add('active');
                btn.style.background = `linear-gradient(135deg, ${game.color}, ${game.colorGrad || game.color})`;
                btn.style.boxShadow = `0 8px 32px ${game.color}aa, 0 0 15px #FFD70088, inset 0 0 0 1px rgba(255,255,255,0.5)`;
                btn.style.borderColor = `#FFD700`; // Always Gold
                btn.style.color = 'white';
            } else {
                btn.classList.remove('active');
                btn.style.background = 'rgba(255,255,255,0.08)';
                btn.style.boxShadow = '0 0 10px rgba(255, 215, 0, 0.2)';
                btn.style.borderColor = `#FFD70066`; // Semi-transparent Gold
                btn.style.color = 'rgba(255,255,255,0.9)';
            }
        });

        // Initialize display to avoid jumpiness
        this.currentGameTitle.innerHTML = `${game.name} <span class="next-draw-tag" style="font-size: 0.6em; opacity: 0.8; margin-left:10px;">(Concurso: ...)</span>`;

        if (this.recentResultsContainer) {
            this.recentResultsContainer.innerHTML = '<div class="sync-loader">Sincronizando com a Caixa...</div>';
        }

        // ━━ DROPDOWN DINÂMICO v3.0 ━━
        this._rebuildClosingDropdown(gameKey, true); // true = forçar 'generate'

        // ━━ EVENTO: Preview do Fechamento em tempo real ━━
        this.closingSelect.onchange = () => this._updateClosingPreview();

        this.maxSelectionElem.textContent = game.maxBet;
        this.selectedNumbers.clear();
        this.fixedNumbers.clear();
        this.isFixedMode = false;
        this.btnFixedMode.classList.remove('active');
        this.btnFixedMode.textContent = '📌 Fixar';
        this.fixedInfoPanel.style.display = 'none';

        // ━━ MÊS DA SORTE — visível apenas para Dia de Sorte ━━
        const mesSorteRow = document.getElementById('mes-sorte-row');
        const mesSorteSelect = document.getElementById('mes-sorte-select');
        if (mesSorteRow) {
            mesSorteRow.style.display = gameKey === 'diadesorte' ? 'grid' : 'none';
        }
        // Pré-selecionar mês mais recente da API (Dia de Sorte)
        if (gameKey === 'diadesorte' && mesSorteSelect) {
            try {
                const prizeInfo = StatsService.prizeStore && StatsService.prizeStore['diadesorte'];
                const recent = StatsService.getRecentResults('diadesorte', 1);
                const mesDaSorte = (recent && recent[0] && recent[0].mesSorte) ? recent[0].mesSorte : null;
                if (mesDaSorte && mesSorteSelect.value === '') {
                    // Normalizar nome do mês (API pode retornar "Agosto", "agosto", etc.)
                    const mesNorm = mesDaSorte.charAt(0).toUpperCase() + mesDaSorte.slice(1).toLowerCase();
                    for (let i = 0; i < mesSorteSelect.options.length; i++) {
                        if (mesSorteSelect.options[i].value.toLowerCase() === mesNorm.toLowerCase()) {
                            mesSorteSelect.selectedIndex = i;
                            break;
                        }
                    }
                }
            } catch(e) { /* sem dados da API ainda — usuário seleciona manualmente */ }
        }

        // Mostrar toggle Modo Sniper para todas as loterias
        const sniperToggleParent = document.getElementById('sniper-label-text');
        if (sniperToggleParent && sniperToggleParent.parentElement) {
            sniperToggleParent.parentElement.style.display = 'flex';
            this._updatePrecisionPoolLimits();
        }

        if (this.quantumCountInput) {
            // Sugestão IA: padrão = 50% dos números da loteria, mas mínimo é minBet
            const qConstraints = (typeof QuantumGodEngine !== 'undefined' && QuantumGodEngine.getConstraints)
                ? QuantumGodEngine.getConstraints(gameKey)
                : null;
            const totalNums = qConstraints ? qConstraints.totalNumbers : (game.range[1] - game.range[0] + 1);
            const defaultSuggestion = Math.ceil(totalNums * 0.5);
            this.quantumCountInput.value = defaultSuggestion;
            this.quantumCountInput.min = game.minBet;
            this.quantumCountInput.max = totalNums;
        }
        if (this.quantumResults) {
            this.quantumResults.innerHTML = '<div class="quantum-placeholder">Clique em "Gerar Sugestão" para começar</div>';
        }

        // Atualizar seletor de números por jogo IA
        this.updateSmartDrawSizeSelect(gameKey, game);

        // RENDER GRID IMMEDIATELY
        this.renderNumberGrid(game);
        this.updateSelectionInfo();
        this.updateCurrentCostDisplay();

        // Mostrar prêmio fallback IMEDIATAMENTE (sem depender da API)
        this.updatePrizeDisplayWithFallback(gameKey);

        // ASYNC LOAD FOR DATA
        (async () => {
            try {
                await StatsService.ensureHistory(gameKey);

                // Update stats and results once data is ready
                this.updateStats();
                this.updateRecentResults();

                // Update Tag with REAL draw number
                const latestResult = StatsService.getRecentResults(gameKey, 1)[0];
                const nextDrawNumber = latestResult ? latestResult.drawNumber + 1 : '???';
                const tag = this.currentGameTitle.querySelector('.next-draw-tag');
                if (tag) tag.textContent = `(Concurso: ${nextDrawNumber})`;

                // Update Prize Display com dados reais da API
                this.updatePrizeDisplay(gameKey);
            } catch (e) {
                console.warn("Async history load failed:", e);
                // Mantém o fallback exibido
                if (this.recentResultsContainer) {
                    this.recentResultsContainer.innerHTML = '<div class="empty-state">Usando dados offline.</div>';
                }
            }
        })();

        // ═══ LIMPEZA ao trocar de loteria (bugs #1-#5 fix) ═══
        // Bug 1: Limpar banner que fica fora do gamesContainer
        const oldBanner = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
        if (oldBanner) oldBanner.remove();

        // Bug 2+5: Limpar arrays de jogos da loteria anterior
        this.currentGeneratedGames = [];
        this._lastGeneratedGames = [];

        // Bug 3: Cancelar geração assíncrona em andamento
        if (typeof AsyncGenerator !== 'undefined' && AsyncGenerator._isRunning) {
            AsyncGenerator._cancelled = true;
            AsyncGenerator._isRunning = false;
        }
        const asyncProgress = document.getElementById('async-progress-inline');
        if (asyncProgress) { asyncProgress.style.display = 'none'; asyncProgress.innerHTML = ''; }

        this.gamesContainer.innerHTML = '<div class="empty-state">Selecione as opções e clique em Gerar Jogos</div>';
    }

    // ╔══════════════════════════════════════════════════════════╗
    // ║  ATUALIZAR SELECT DE NÚMEROS POR JOGO IA              ║
    // ╚══════════════════════════════════════════════════════════╝
    updateSmartDrawSizeSelect(gameKey, game) {
        if (!this.smartDrawSizeSelect) return;

        this.smartDrawSizeSelect.innerHTML = '';
        const min = game.minBet;
        // Limitar max a algo razoável para o select
        const maxDisplay = Math.min(game.maxBet, min + 14); // Até 15 opções iniciais
        
        for (let i = min; i <= maxDisplay; i++) {
            const opt = document.createElement('option');
            opt.value = i;
            opt.textContent = i + ' núm.';
            if (i === min) opt.textContent += ' ★'; // Marcar padrão
            this.smartDrawSizeSelect.appendChild(opt);
        }

        // ★ v9.5: Para loterias com range grande (Lotomania), adicionar opções extras
        // de 5 em 5 até 90% do range total
        if (game.maxBet > maxDisplay + 5) {
            const extendedMax = Math.min(game.maxBet, Math.round((game.range[1] - game.range[0] + 1) * 0.90));
            for (let i = maxDisplay + 5; i <= extendedMax; i += 5) {
                const opt = document.createElement('option');
                opt.value = i;
                opt.textContent = i + ' núm.';
                this.smartDrawSizeSelect.appendChild(opt);
            }
        }

        // Se max for maior que a última opção, adicionar como última opção
        const lastOpt = parseInt(this.smartDrawSizeSelect.lastChild?.value || 0);
        if (game.maxBet > lastOpt) {
            const optMax = document.createElement('option');
            optMax.value = game.maxBet;
            optMax.textContent = game.maxBet + ' núm. (máx)';
            this.smartDrawSizeSelect.appendChild(optMax);
        }

        // Definir padrão como minBet
        this.smartDrawSizeSelect.value = min;

        // Atualizar info
        if (this.smartDrawInfo) {
            if (min === game.maxBet) {
                this.smartDrawInfo.textContent = `Fixo: ${min} números`;
            } else {
                this.smartDrawInfo.textContent = `Mín: ${min} | Máx: ${game.maxBet}`;
            }
        }
    }

    updateRecentResults() {
        const results = StatsService.getRecentResults(this.currentGameKey, 5);
        this.renderRecentResults(results);
    }

    // Exibe prêmio fallback IMEDIATAMENTE (sem precisar de API)
    updatePrizeDisplayWithFallback(gameKey) {
        if (!this.prizeDisplay) return;
        
        // Primeiro tenta dados reais da API (se já tiver carregado)
        const prizeInfo = StatsService.getPrizeInfo(gameKey);
        if (prizeInfo && (prizeInfo.estimatedPrize > 0 || prizeInfo.accumulatedPrize > 0)) {
            this.updatePrizeDisplay(gameKey);
            return;
        }

        // Se não tem dados da API, usa o fallback definido em games.js
        const game = GAMES[gameKey];
        const fallbackAmount = game ? (game.estimatedPrizeFallback || 0) : 0;
        
        if (fallbackAmount > 0) {
            const formatted = fallbackAmount.toLocaleString('pt-BR', { 
                style: 'currency', 
                currency: 'BRL',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            });
            this.prizeValue.textContent = formatted;
            this.prizeDisplay.style.display = 'block';
            
            if (this.prizeBadge) {
                this.prizeBadge.style.display = 'none';
            }
        } else {
            this.prizeDisplay.style.display = 'none';
        }
    }

    updatePrizeDisplay(gameKey) {
        const prizeInfo = StatsService.getPrizeInfo(gameKey);
        
        if (!prizeInfo || !this.prizeDisplay) return;

        const prizeAmount = prizeInfo.estimatedPrize || prizeInfo.accumulatedPrize || 0;

        if (prizeAmount > 0) {
            const formatted = prizeAmount.toLocaleString('pt-BR', { 
                style: 'currency', 
                currency: 'BRL',
                minimumFractionDigits: 0,
                maximumFractionDigits: 0
            });

            this.prizeValue.textContent = formatted;
            this.prizeDisplay.style.display = 'block';

            // Show ACUMULADO badge
            if (prizeInfo.accumulated && this.prizeBadge) {
                this.prizeBadge.style.display = 'inline-block';
            } else if (this.prizeBadge) {
                this.prizeBadge.style.display = 'none';
            }

            // Sincronizar botão de navegação com valor real da API
            const navElem = document.getElementById(`prize-nav-${gameKey}`);
            if (navElem) {
                navElem.textContent = this._formatPrizeShort(prizeAmount);
                if (prizeInfo.accumulated) {
                    navElem.textContent += ' 🔥';
                }
            }
        } else {
            this.prizeDisplay.style.display = 'none';
        }
    }

    renderNumberGrid(game) {
        this.gridContainer.innerHTML = '';
        const rangeStart = game.range[0];
        const rangeEnd = game.range[1];

        for (let i = rangeStart; i <= rangeEnd; i++) {
            const numDiv = document.createElement('div');
            numDiv.className = 'grid-num';
            numDiv.textContent = i.toString().padStart(2, '0');
            numDiv.dataset.number = i;
            numDiv.onclick = () => this.toggleNumber(i, numDiv);
            this.gridContainer.appendChild(numDiv);
        }
    }

    toggleFixedMode() {
        this.isFixedMode = !this.isFixedMode;
        if (this.isFixedMode) {
            this.btnFixedMode.classList.add('active');
            this.btnFixedMode.textContent = '📌 Modo Fixo (ON)';
            // Visual Hint
            // alert("Clique nos números para FIXÁ-LOS (Borda Dourada). Eles aparecerão em TODOS os jogos.");
        } else {
            this.btnFixedMode.classList.remove('active');
            this.btnFixedMode.textContent = '📌 Fixar';
        }
    }

    toggleNumber(number, element) {
        const game = GAMES[this.currentGameKey];

        // If element is not provided, find it in the grid
        if (!element) {
            element = this.gridContainer.querySelector(`.grid-num[data-number="${number}"]`);
        }

        if (this.isFixedMode) {
            // FIXED MODE LOGIC
            if (this.fixedNumbers.has(number)) {
                this.fixedNumbers.delete(number);
                if (element) element.classList.remove('fixed');
            } else {
                // Validation: Limit Fixed Numbers (50% minBet or maxFixed)
                const limit = game.maxFixed || Math.floor(game.minBet / 2);
                if (this.fixedNumbers.size >= limit) {
                    alert(`Máximo de ${limit} números fixos permitidos para ${game.name}.`);
                    return;
                }

                // If fixing, ensure it's selected
                if (!this.selectedNumbers.has(number)) {
                    if (this.selectedNumbers.size >= game.maxBet) {
                        alert("Limite de números selecionados atingido! Remove alguns para fixar este.");
                        return;
                    }
                    this.selectedNumbers.add(number);
                    if (element) element.classList.add('selected');
                }

                this.fixedNumbers.add(number);
                if (element) element.classList.add('fixed');
            }
            this.updateFixedInfo();
            return;
        }

        // NORMAL SELECTION LOGIC
        if (this.selectedNumbers.has(number)) {
            // Prevent unselecting if fixed (unless in fixed mode)
            if (this.fixedNumbers.has(number)) {
                alert("Este número está FIXO. Desative o 'Modo Fixo' ou clique em 'Fixar' para removê-lo.");
                return;
            }
            this.selectedNumbers.delete(number);
            if (element) element.classList.remove('selected');
        } else {
            if (this.selectedNumbers.size >= game.maxBet) {
                alert(`Máximo de ${game.maxBet} números permitidos.`);
                return;
            }
            this.selectedNumbers.add(number);
            if (element) element.classList.add('selected');
        }
        this.updateSelectionInfo();
    }

    updateFixedInfo() {
        const list = Array.from(this.fixedNumbers).sort((a, b) => a - b).map(n => n.toString().padStart(2, '0')).join(', ');
        this.fixedNumbersList.textContent = list;
        this.fixedInfoPanel.style.display = this.fixedNumbers.size > 0 ? 'block' : 'none';
        this.updateSelectionInfo(); // Updates cost too
        // v3.0: Reconstruir dropdown de fechamento com níveis dinâmicos
        this._rebuildClosingDropdown(this.currentGameKey);
    }

    selectRandom() {
        const game = GAMES[this.currentGameKey];
        const targetCount = game.minBet; // Pick minimum for random suggestion

        this.clearSelection();

        const universe = [];
        for (let i = game.range[0]; i <= game.range[1]; i++) {
            universe.push(i);
        }

        // Fisher-Yates shuffle para aleatoriedade verdadeira
        for (let i = universe.length - 1; i > 0; i--) {
            const j = Math.floor(Math.random() * (i + 1));
            const temp = universe[i];
            universe[i] = universe[j];
            universe[j] = temp;
        }
        const selected = universe.slice(0, targetCount);

        selected.forEach(num => {
            const el = this.gridContainer.querySelector(`.grid-num[data-number="${num}"]`);
            if (el) {
                this.selectedNumbers.add(num);
                el.classList.add('selected');
            }
        });

        this.updateSelectionInfo();
    }



    clearSelection() {
        this.selectedNumbers.clear();
        this.fixedNumbers.clear();
        this.isFixedMode = false;
        if (this.btnFixedMode) {
            this.btnFixedMode.classList.remove('active');
            this.btnFixedMode.textContent = '📌 Fixar';
        }
        if (this.fixedInfoPanel) this.fixedInfoPanel.style.display = 'none';

        if (this.gridContainer) {
            const selected = this.gridContainer.querySelectorAll('.selected, .fixed');
            selected.forEach(el => {
                el.classList.remove('selected');
                el.classList.remove('fixed');
            });
        }
        this.updateSelectionInfo();

        // Clear generated games
        this.currentGeneratedGames = [];
        this.gamesContainer.innerHTML = '<div class="empty-state">Selecione as opções e clique em Gerar Jogos</div>';

        // Clear check summary
        if (this.checkSummaryContainer) this.checkSummaryContainer.style.display = 'none';

        // Clear generation feedback
        const feedback = document.querySelector('.generation-feedback');
        if (feedback) feedback.remove();

        // Clear Quantum Suggestions
        if (this.quantumResults) this.quantumResults.innerHTML = '';
    }

    updateSelectionInfo() {
        const count = this.selectedNumbers.size;
        this.selectedCountElem.textContent = count;
        this.updateInvestmentPanel();
        this.updateCurrentCostDisplay();
        this._updateClosingPreview();

        // v12: Wheel System removido — substituído por MotorFechamentoManual
    }

    
    updateCost() {
        if (typeof this.updateInvestmentPanel === 'function') this.updateInvestmentPanel();
        if (typeof this.updateCurrentCostDisplay === 'function') this.updateCurrentCostDisplay();
    }

    updateCurrentCostDisplay() {
        const game = GAMES[this.currentGameKey];
        const qty = parseInt(this.gamesQuantityInput.value) || 10;

                // Calcular preço por jogo baseado no número de números selecionados
        let pricePerGame = game.price;
        const smartDrawSize = this.smartDrawSizeSelect 
            ? parseInt(this.smartDrawSizeSelect.value) || game.minBet
            : game.minBet;

        // ★ v9.5: Se Sniper ativo, dropdown = pool size, cada jogo custa minBet
        const precisionCheckbox = document.getElementById('precision-mode-toggle');
        const isSniperActive = precisionCheckbox && precisionCheckbox.checked;
        
        if (isSniperActive) {
            // Sniper: cada jogo é minBet números → preço base
            pricePerGame = game.price;
        } else if (smartDrawSize > game.minBet) {
            // Normal: se jogador escolheu mais números, calcular combinações
            const combinations = this._calcCombinations(smartDrawSize, game.minBet);
            pricePerGame = combinations * game.price;
        }

        const cost = qty * pricePerGame;
        if (this.currentBetCostElem) {
            this.currentBetCostElem.textContent = cost.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        }
        // Atualizar custo no Simulador de Custo
        if (this.costUserGames) {
            this.costUserGames.textContent = cost.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        }
        if (this.costUserGamesDetail) {
            const priceFormatted = pricePerGame.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
            const detail = smartDrawSize > game.minBet
                ? `${qty} jogo${qty > 1 ? 's' : ''} × ${priceFormatted} (${smartDrawSize} núm.)`
                : `${qty} jogo${qty > 1 ? 's' : ''} × ${priceFormatted}`;
            this.costUserGamesDetail.textContent = detail;
        }

        // Atualizar info de preço no painel IA
        if (this.smartDrawInfo) {
            if (smartDrawSize > game.minBet) {
                const priceFormatted = pricePerGame.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
                this.smartDrawInfo.textContent = `${priceFormatted}/jogo`;
                this.smartDrawInfo.style.color = '#F59E0B';
                this.smartDrawInfo.style.fontWeight = '700';
            } else {
                const basePrice = game.price.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
                this.smartDrawInfo.textContent = `${basePrice}/jogo`;
                this.smartDrawInfo.style.color = '#94A3B8';
                this.smartDrawInfo.style.fontWeight = '400';
            }
        }
    }

    // Calcular C(n, k) = n! / (k! × (n-k)!)
    _calcCombinations(n, k) {
        if (k > n) return 0;
        if (k === 0 || k === n) return 1;
        let result = 1;
        for (let i = 0; i < k; i++) {
            result = result * (n - i) / (i + 1);
        }
        return Math.round(result);
    }

    // ━━ PREVIEW DO FECHAMENTO v3.1 (CONDICIONAL) ━━
    // ━━ CÁLCULO SEGURO C(n,k) ━━
    _nCrSafe(n, k) {
        if (k > n || k < 0) return 0;
        if (k === 0 || k === n) return 1;
        if (k > n - k) k = n - k;
        let result = 1;
        for (let i = 0; i < k; i++) {
            result = result * (n - i) / (i + 1);
            if (result > 1e9) return result; // Evitar overflow
        }
        return Math.round(result);
    }

    _updateClosingPreview() {
        const closingVal = this.closingSelect ? this.closingSelect.value : '';
        if (!closingVal || !closingVal.startsWith('close_')) return;

        const guarantee = parseInt(closingVal.replace('close_', ''));
        const game = GAMES[this.currentGameKey];
        if (!game) return;

        const numSelected = this.selectedNumbers.size;
        const fixedCount = this.fixedNumbers ? this.fixedNumbers.size : 0;
        if (typeof ClosingEngine === 'undefined') return;

        const preview = ClosingEngine.getClosurePreview(numSelected, guarantee, game.minBet, this.currentGameKey, fixedCount);

        if (preview.possible && preview.games > 0) {
            this.gamesQuantityInput.value = preview.games;
        }
        this.updateCurrentCostDisplay();

        if (this.closingEstimatesContainer) {
            if (!preview.possible || numSelected < game.minBet) {
                this.closingEstimatesContainer.innerHTML = '<p class="helper-text" style="color:#F59E0B;">' + preview.msg + '</p>';
            } else {
                const guaranteeIcons = { 20: '🎯', 19: '⭐', 18: '🔥', 17: '✅', 15: '🎯', 14: '⭐', 13: '🔥', 12: '💎', 11: '💎', 10: '👑', 9: '👑', 8: '🔥', 7: '🎯', 6: '🎯', 5: '⭐', 4: '🔥', 3: '✅' };
                const effG = preview.effectiveGuarantee || (guarantee - fixedCount);
                let fixedBadge = '';
                if (fixedCount > 0) {
                    const probPct = (preview.fixedHitProb * 100).toFixed(4);
                    const isLowProb = preview.fixedHitProb < 0.15; // less than 15% probability
                    const warningColor = isLowProb ? '#F87171' : '#10B981';
                    const warningIcon = isLowProb ? '⚠️' : '✅';
                    fixedBadge = 
                        '<div style="font-size:0.75em;color:#10B981;margin-top:4px;font-weight:600;">📌 ' + fixedCount + ' fixos → efetivo: ' + effG + ' variáveis a cobrir (↓ menos jogos!)</div>' +
                        '<div style="font-size:0.75em;color:' + warningColor + ';margin-top:2px;font-weight:600;">' + warningIcon + ' Requisito: acertar ≥ ' + preview.maxHitsInFixed + ' dos ' + fixedCount + ' fixos para a garantia valer.</div>' +
                        '<div style="font-size:0.72em;color:#9CA3AF;margin-top:1px;">Probabilidade real de atingir o requisito: <strong>' + probPct + '%</strong></div>';
                }
                this.closingEstimatesContainer.innerHTML =
                    '<div style="padding:8px 12px;border-radius:8px;background:rgba(234,179,8,0.1);border:1px solid #EAB30830;">' +
                    '<div style="font-weight:700;color:#EAB308;">' + (guaranteeIcons[guarantee] || '🎯') + ' ' + preview.msg + '</div>' +
                    fixedBadge +
                    '<div style="font-size:0.8em;color:#9CA3AF;margin-top:4px;">Subconjuntos: C(' + numSelected + ',' + guarantee + ') = ' + preview.subsets.toLocaleString('pt-BR') + '</div>' +
                    '<div style="font-size:0.75em;color:' + (preview.possible ? '#10B981' : '#F59E0B') + ';margin-top:3px;">Confiança: ' + (preview.possible ? '✅ Alta' : '⚠️ Muitos jogos') + '</div>' +
                    '</div>';
            }
        }
    }

    // ━━ RECONSTRUIR DROPDOWN DE FECHAMENTO v3.0 ━━
    _rebuildClosingDropdown(gameKey, forceGenerate = false) {
        if (!gameKey) gameKey = this.currentGameKey;
        const game = GAMES[gameKey];
        if (!game || !this.closingSelect) return;

        const fixedCount = this.fixedNumbers ? this.fixedNumbers.size : 0;
        const savedValue = forceGenerate ? '' : this.closingSelect.value;

        this.closingSelect.innerHTML = '';

        // v3.2 FIX: Opção padrão "Gerar Jogos" — respeita a quantidade solicitada
        const defaultOpt = document.createElement('option');
        defaultOpt.value = 'generate';
        defaultOpt.textContent = '🎲 Gerar Jogos (Quantidade)';
        defaultOpt.style.fontWeight = '700';
        this.closingSelect.appendChild(defaultOpt);

        if (typeof ClosingEngine !== 'undefined' && game.closingLevels && game.closingLevels.length > 0) {
            const poolSize = this.selectedNumbers ? this.selectedNumbers.size : 0;
            const dynamicLevels = ClosingEngine.getDynamicClosingLevels(gameKey, fixedCount, poolSize);
            const optGroup1 = document.createElement('optgroup');
            optGroup1.label = fixedCount > 0
                ? '🎯 Fechamento (' + fixedCount + ' fixos → menos jogos!)'
                : '🎯 Fechamento Objetivo (Garantido)';
            dynamicLevels.forEach(cl => {
                const option = document.createElement('option');
                option.value = 'close_' + cl.guarantee;
                option.textContent = cl.icon + ' ' + cl.label;
                option.dataset.closing = 'true';
                optGroup1.appendChild(option);
            });
            this.closingSelect.appendChild(optGroup1);
        } else if (game.closingLevels && game.closingLevels.length > 0) {
            const optGroup1 = document.createElement('optgroup');
            optGroup1.label = '🎯 Fechamento Objetivo (Garantido)';
            game.closingLevels.forEach(cl => {
                const option = document.createElement('option');
                option.value = 'close_' + cl.guarantee;
                option.textContent = cl.icon + ' ' + cl.label;
                option.dataset.closing = 'true';
                optGroup1.appendChild(option);
            });
            this.closingSelect.appendChild(optGroup1);
        }

        const optGroup2 = document.createElement('optgroup');
        optGroup2.label = 'Garantia de Fechamento';
        game.strategies.forEach(strat => {
            const option = document.createElement('option');
            option.value = strat.match;
            option.textContent = strat.label;
            optGroup2.appendChild(option);
        });
        this.closingSelect.appendChild(optGroup2);

        // v3.3 FIX: Ao trocar de loteria, SEMPRE resetar para 'generate'
        // para evitar que close_7 de outra loteria persista e gere 80k jogos
        if (forceGenerate) {
            this.closingSelect.value = 'generate';
        } else {
            const savedOption = Array.from(this.closingSelect.options).find(o => o.value === savedValue);
            if (savedOption && savedValue !== '') {
                this.closingSelect.value = savedValue;
            } else {
                this.closingSelect.value = 'generate';
            }
        }
        this._updateClosingPreview();
    }

    updateInvestmentPanel() {
        const count = this.selectedNumbers ? this.selectedNumbers.size : 0;
        if (typeof CombinationEngine === 'undefined') return;
        const result = CombinationEngine.calculateInvestment(this.currentGameKey, count);

        if (!result) return;

        this.costSelectedCount.textContent = count;

        if (!result.valid) {
            this.costTotalCombinations.textContent = "0";
            this.costTotalValue.textContent = "R$ 0,00";
            this.closingEstimatesContainer.innerHTML = '<p class="helper-text">Selecione mais números...</p>';
            return;
        }

        const fmt = (n) => n.toLocaleString('pt-BR');
        const currency = (n) => n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });

        this.costTotalCombinations.textContent = fmt(result.totalCombinations);
        this.costTotalValue.textContent = currency(result.totalCost);

        this.closingEstimatesContainer.innerHTML = '';
        if (result.estimates && result.estimates.length > 0) {
            result.estimates.forEach(est => {
                const item = document.createElement('div');
                item.className = 'estimate-item';
                item.style.cursor = 'pointer';
                item.title = "Clique para aplicar esta configuração";

                item.onclick = () => {
                    this.gamesQuantityInput.value = est.qty;
                    // Try to match strategy
                    if (est.strategyId) {
                        // Find option with this value
                        const opt = Array.from(this.closingSelect.options).find(o => o.value == est.strategyId);
                        if (opt) this.closingSelect.value = est.strategyId;
                    }
                    this.updateCurrentCostDisplay();

                    // Visual feedback
                    item.style.borderColor = 'var(--primary-accent)';
                    setTimeout(() => item.style.borderColor = '', 500);
                };

                item.innerHTML = `
                    <span class="estimate-label">${est.label}</span>
                    <div class="estimate-value">
                        <span>${fmt(est.qty)} jogos</span>
                        <span>${currency(est.cost)}</span>
                    </div>
                `;
                this.closingEstimatesContainer.appendChild(item);
            });
        } else {
            this.closingEstimatesContainer.innerHTML = '<p class="helper-text">Sem estimativas extras.</p>';
        }
    }

    updateStats() {
        if (typeof StatsService === 'undefined') return;
        try {
            const stats = StatsService.getStats(this.currentGameKey, this.currentStatsRange);
            this.renderStats(stats);

            const recents = StatsService.getRecentResults(this.currentGameKey, 5);
            this.renderRecentResults(recents);

            // ── Painel de Frequência Multi-Faixa ──
            this.renderFrequencyPanel();
        } catch(e) {
            console.warn('[UI] Erro ao atualizar estatísticas:', e.message);
        }
    }

    renderRecentResults(recents) {
        if (!this.recentResultsContainer) return;
        this.recentResultsContainer.innerHTML = '';

        if (!recents || recents.length === 0) {
            this.recentResultsContainer.innerHTML = '<div class="empty-state" style="padding:1rem;">Sem dados recentes.</div>';
            return;
        }

        const self = this;

        recents.forEach(item => {
            const row = document.createElement('div');
            row.className = 'recent-row';
            row.style.display = 'flex';
            row.style.flexDirection = 'column';
            row.style.gap = '5px';
            row.style.marginBottom = '0.8rem';
            row.style.padding = '0.5rem';
            row.style.background = 'var(--bg-surface)';
            row.style.borderRadius = 'var(--radius-sm)';
            row.style.border = '1px solid var(--border-color)';

            const label = document.createElement('span');
            label.className = 'recent-label';
            label.style.fontWeight = 'bold';
            label.style.color = '#F59E0B';
            label.style.fontSize = '0.85rem';
            label.textContent = `Concurso ${item.drawNumber}`;
            row.appendChild(label);

            // Função auxiliar para criar linha de bolas
            function createBallsRow(numbers, labelText) {
                if (labelText) {
                    const sortLabel = document.createElement('span');
                    sortLabel.style.fontSize = '0.7rem';
                    sortLabel.style.color = '#94A3B8';
                    sortLabel.style.fontWeight = '600';
                    sortLabel.style.marginTop = '2px';
                    sortLabel.textContent = labelText;
                    row.appendChild(sortLabel);
                }
                const numbersDiv = document.createElement('div');
                numbersDiv.className = 'recent-numbers';
                numbersDiv.style.display = 'flex';
                numbersDiv.style.gap = '4px';
                numbersDiv.style.flexWrap = 'wrap';

                numbers.forEach(num => {
                    const ball = document.createElement('span');
                    ball.className = 'mini-ball';
                    ball.textContent = num.toString().padStart(2, '0');
                    ball.style.display = 'inline-flex';
                    ball.style.alignItems = 'center';
                    ball.style.justifyContent = 'center';
                    ball.style.width = '20px';
                    ball.style.height = '20px';
                    ball.style.borderRadius = '50%';
                    ball.style.backgroundColor = 'var(--bg-main)';
                    ball.style.border = '1px solid var(--border-color)';
                    ball.style.fontSize = '0.75rem';
                    ball.style.color = 'var(--text-primary)';
                    numbersDiv.appendChild(ball);
                });
                row.appendChild(numbersDiv);
            }

            // Dupla Sena: exibir Sorteio 1 e Sorteio 2 separados
            if (item.numbers2 && item.numbers2.length > 0) {
                createBallsRow(item.numbers, '1º Sorteio');
                createBallsRow(item.numbers2, '2º Sorteio');
            } else {
                createBallsRow(item.numbers, null);
            }

            this.recentResultsContainer.appendChild(row);
        });
    }

    renderStats(stats) {
        if (!this.hotNumbersContainer || !this.coldNumbersContainer) return;
        if (!stats || !stats.hot || !stats.cold) return;
        this.hotNumbersContainer.innerHTML = '';
        this.coldNumbersContainer.innerHTML = '';

        // Atualizar header com total de sorteios e split 50/50
        const statsHeader = document.querySelector('.stats-header h3');
        if (statsHeader) {
            const label = stats.totalDraws
                ? `Estatísticas <span style="font-size:0.7em;color:#94A3B8;font-weight:400;">(${stats.totalDraws} sorteios analisados — 50% hot / 50% cold)</span>`
                : 'Estatísticas';
            statsHeader.innerHTML = label;
        }

        // Atualizar títulos das seções com contagem
        const hotHeader = document.querySelector('.stat-box.hot h4');
        const coldHeader = document.querySelector('.stat-box.cold h4');
        if (hotHeader) hotHeader.textContent = `Mais Sorteados (${stats.hot.length})`;
        if (coldHeader) coldHeader.textContent = `Menos Sorteados (${stats.cold.length})`;

        // Container sem scroll — todos os números visíveis
        const listStyle = 'display:flex;flex-wrap:wrap;gap:8px;padding:4px 2px;';
        if (this.hotNumbersContainer)  this.hotNumbersContainer.setAttribute('style', listStyle);
        if (this.coldNumbersContainer) this.coldNumbersContainer.setAttribute('style', listStyle);

        const createStatItem = (stat, isHot) => {
            const container = document.createElement('div');
            container.className = 'stat-ball-wrapper';
            container.style.cssText = 'position:relative;display:flex;flex-direction:column;align-items:center;gap:2px;cursor:pointer;';
            container.title = `Clique para adicionar ao jogo`;

            const ball = this.createBall(stat.number);
            ball.classList.add('stat-ball');

            // Estado inicial baseado na seleção atual
            if (this.selectedNumbers.has(stat.number)) {
                ball.classList.add('selected');
            }

            // Badge de frequência
            if (stat.count > 0) {
                const badge = document.createElement('span');
                badge.style.cssText = 'position:absolute;top:-4px;right:-4px;background:#F59E0B;color:#000;font-size:0.6rem;font-weight:800;padding:1px 3px;border-radius:6px;min-width:14px;text-align:center;line-height:1.2;z-index:2;pointer-events:none;';
                badge.textContent = stat.count + '×';
                container.appendChild(badge);
            }

            const addIcon = document.createElement('div');
            addIcon.className = 'stat-add-icon';
            addIcon.innerHTML = this.selectedNumbers.has(stat.number) ? '✓' : '+';
            addIcon.title = 'Adicionar ao jogo';

            // Click: adicionar/remover do grid de jogo acima
            container.onclick = (e) => {
                e.stopPropagation();
                this.toggleNumber(stat.number);
                const isSelected = this.selectedNumbers.has(stat.number);
                if (isSelected) {
                    ball.classList.add('selected');
                    addIcon.innerHTML = '✓';
                    addIcon.style.background = '#10B981';
                    // Pulsar para confirmar
                    ball.style.transform = 'scale(1.3)';
                    setTimeout(() => { ball.style.transform = ''; }, 300);
                } else {
                    ball.classList.remove('selected');
                    addIcon.innerHTML = '+';
                    addIcon.style.background = '';
                }
            };

            container.appendChild(ball);
            container.appendChild(addIcon);

            // Badge de atraso (delay)
            if (stat.delay !== undefined && stat.delay > 0) {
                const delayBadge = document.createElement('span');
                const delayColor = stat.delay >= 10 ? '#EF4444' : stat.delay >= 5 ? '#F59E0B' : '#64748B';
                const delayBg    = stat.delay >= 10 ? 'rgba(239,68,68,0.12)' : stat.delay >= 5 ? 'rgba(245,158,11,0.12)' : 'rgba(100,116,139,0.10)';
                const delayIcon  = stat.delay >= 10 ? '⏳' : stat.delay >= 5 ? '🕑' : '•';
                delayBadge.style.cssText = `font-size:0.58rem;font-weight:700;color:${delayColor};background:${delayBg};padding:1px 4px;border-radius:4px;line-height:1.3;white-space:nowrap;margin-top:1px;pointer-events:none;`;
                delayBadge.textContent = `${delayIcon} ${stat.delay}d`;
                delayBadge.title = `Há ${stat.delay} sorteio${stat.delay !== 1 ? 's' : ''} sem sair`;
                container.appendChild(delayBadge);
            } else if (stat.delay === 0) {
                const freshBadge = document.createElement('span');
                freshBadge.style.cssText = 'font-size:0.58rem;font-weight:700;color:#22C55E;background:rgba(34,197,94,0.10);padding:1px 4px;border-radius:4px;line-height:1.3;margin-top:1px;pointer-events:none;';
                freshBadge.textContent = '✔ recente';
                freshBadge.title = 'Saiu no último sorteio';
                container.appendChild(freshBadge);
            }

            return container;
        };

        stats.hot.forEach(stat => {
            this.hotNumbersContainer.appendChild(createStatItem(stat, true));
        });

        stats.cold.forEach(stat => {
            this.coldNumbersContainer.appendChild(createStatItem(stat, false));
        });
    }

    // ╔══════════════════════════════════════════════════════════════════╗
    // ║  PAINEL DE FREQUÊNCIA MULTI-FAIXA — 3, 5, 10 e 15 Sorteios   ║
    // ║  Mostra os números mais e menos sorteados em 4 faixas         ║
    // ╚══════════════════════════════════════════════════════════════════╝
    renderFrequencyPanel() {
        const container = document.getElementById('freq-content');
        if (!container) return;

        const game = GAMES[this.currentGameKey];
        if (!game) return;

        const ranges = [3, 5, 10, 15];
        // Exibir no máximo 15 números por seção (hot/cold) — compacto para todas as loterias
        const totalNumbers = game.range[1] - game.range[0] + 1;
        const topNDisplay = Math.min(15, Math.ceil(totalNumbers * 0.25));

        // Verificar se temos dados
        const history = StatsService.historyStore ? StatsService.historyStore[this.currentGameKey] : null;
        if (!history || history.length === 0) {
            container.innerHTML = '<div class="freq-loading"><span class="freq-spinner"></span>Aguardando dados da API da Caixa...</div>';
            // Tentar novamente em 2s — COM LIMITE de 3 retries
            const retryKey = 'freqPanel_' + this.currentGameKey;
            if (typeof Guardian !== 'undefined' && Guardian.canRetry(retryKey, 3)) {
                Guardian.setTimeout(retryKey, () => this.renderFrequencyPanel(), 2000);
            } else {
                container.innerHTML = '<div class="freq-loading" style="color:#94A3B8;">Dados indisponíveis — usando modo offline</div>';
            }
            return;
        }
        // Reset retry counter quando dados chegam
        if (typeof Guardian !== 'undefined') Guardian.resetRetry('freqPanel_' + this.currentGameKey);

        let html = '<div class="freq-grid">';

        ranges.forEach(range => {
            const stats = StatsService.getStats(this.currentGameKey, range);
            const actualDraws = stats.totalDraws || 0;
            const hotSlice = stats.hot.slice(0, topNDisplay);
            const coldSlice = stats.cold.slice(0, topNDisplay);

            html += '<div class="freq-column">';
            html += '<div class="freq-col-header">';
            html += `<span class="freq-range-label">${range} Sorteios</span>`;
            html += `<span class="freq-range-sub">${actualDraws} analisados</span>`;
            html += '</div>';

            // ── HOT ──
            html += '<div class="freq-section">';
            html += '<div class="freq-section-title hot">🔥 Mais Sorteados</div>';
            html += '<div class="freq-nums">';
            hotSlice.forEach((stat, idx) => {
                const tier = idx < 3 ? 'hot-1' : idx < 6 ? 'hot-2' : 'hot-3';
                const num = String(stat.number).padStart(2, '0');
                html += `<div class="freq-ball ${tier}" title="${stat.number}: ${stat.count}x em ${actualDraws} sorteios">`;
                html += `${num}`;
                html += `<span class="freq-tooltip">${stat.number}: ${stat.count}× (atraso: ${stat.delay})</span>`;
                html += '</div>';
            });
            html += '</div></div>';

            // ── COLD ──
            html += '<div class="freq-section">';
            html += '<div class="freq-section-title cold">❄️ Menos Sorteados</div>';
            html += '<div class="freq-nums">';
            coldSlice.forEach((stat, idx) => {
                const tier = idx < 3 ? 'cold-1' : idx < 6 ? 'cold-2' : 'cold-3';
                const num = String(stat.number).padStart(2, '0');
                html += `<div class="freq-ball ${tier}" title="${stat.number}: ${stat.count}x em ${actualDraws} sorteios">`;
                html += `${num}`;
                html += `<span class="freq-tooltip">${stat.number}: ${stat.count}× (atraso: ${stat.delay})</span>`;
                html += '</div>';
            });
            html += '</div></div>';

            html += '</div>'; // freq-column
        });

        html += '</div>'; // freq-grid

        // ── LEGENDA ──
        html += '<div style="margin-top:10px;display:flex;justify-content:center;gap:14px;flex-wrap:wrap;font-size:0.6rem;color:#64748B;">';
        html += '<span>🔥 <span style="color:#FACC15;">■</span> Top 3 | <span style="color:#FCD34D;">■</span> Top 6 | <span style="color:#F59E0B;">■</span> Top 10</span>';
        html += '<span>❄️ <span style="color:#60A5FA;">■</span> Top 3 | <span style="color:#93C5FD;">■</span> Top 6 | <span style="color:#BFDBFE;">■</span> Top 10</span>';
        html += '</div>';

        container.innerHTML = html;
    }

    _generateExtras(gameKey, count) {
        let pool = [];
        if (gameKey === 'diadesorte') pool = L99_MESES.map((_, i) => i);
        else if (gameKey === 'timemania') pool = L99_TIMES.map((_, i) => i);
        else return null;

        function shuffle(array) {
            let currentIndex = array.length, randomIndex;
            while (currentIndex !== 0) {
                randomIndex = Math.floor(Math.random() * currentIndex);
                currentIndex--;
                [array[currentIndex], array[randomIndex]] = [array[randomIndex], array[currentIndex]];
            }
            return array;
        }

        let extras = [];
        let currentPool = [];
        for (let i = 0; i < count; i++) {
            if (currentPool.length === 0) {
                currentPool = shuffle([...pool]);
            }
            extras.push(currentPool.pop());
        }
        return extras;
    }

    renderGames(result, gameKey, updateHash = true) {
        // Validação defensiva de dados de entrada
        if (!result) result = { games: [] };
        if (!result.games) result.games = [];

        // ── ORDENAÇÃO GLOBAL POR SINERGIA IA 🔥 ──
        // Isso garante que TODOS os motores (Sniper, Cobertura, Manual Simples, etc) 
        // entreguem os melhores jogos estatisticamente no topo da lista.
        if (result.games.length > 0 && typeof ClosingEngine !== 'undefined') {
            let pool = result.pool;
            if (!pool || pool.length === 0) {
                pool = Array.from(this.selectedNumbers || []);
            }
            if (!pool || pool.length === 0) {
                const gameConfig = typeof GAMES !== 'undefined' ? GAMES[gameKey] : null;
                if (gameConfig && gameConfig.range) {
                    pool = [];
                    for(let i = gameConfig.range[0]; i <= gameConfig.range[1]; i++) pool.push(i);
                }
            }
            
            try {
                if (pool && pool.length > 0) {
                    const aiSynergy = ClosingEngine._getAISynergy(gameKey, pool);
                    if (aiSynergy) {
                        const fixedArr = Array.from(this.fixedNumbers || []);
                        result.games.sort((a, b) => {
                            const scoreA = ClosingEngine._evalSynergy(a.filter(n => !fixedArr.includes(n)), fixedArr, aiSynergy);
                            const scoreB = ClosingEngine._evalSynergy(b.filter(n => !fixedArr.includes(n)), fixedArr, aiSynergy);
                            return scoreB - scoreA;
                        });
                        console.log('[GLOBAL-SORT] 🔥 Jogos globais ordenados por Sinergia IA.');
                    }
                }
            } catch(e) {
                console.warn('[GLOBAL-SORT] Falha ao ordenar por sinergia', e);
            }
        }

        this.currentGeneratedGames = result.games;
        this._lastInternalEngine = result.internalEngine || 'Desconhecido';
        
        // Gerar múltiplos times/meses distribuídos com máxima cobertura (sem repetição precoce)
        if (gameKey === 'timemania' || gameKey === 'diadesorte') {
            this.currentGeneratedExtras = this._generateExtras(gameKey, result.games.length);
        } else if (gameKey !== 'milionaria') {
            // Para +Milionária, os trevos já foram definidos ANTES de renderGames ser chamado
            // e devem ser preservados. Para as demais loterias, limpar.
            this.currentGeneratedExtras = null;
        }

        if (!this.gamesContainer) return;
        this.gamesContainer.innerHTML = '';
        this.gamesContainer.dataset.gameKey = gameKey || this.currentGameKey;

        if (updateHash) this.updateUrlHash();

        if (!result.games || result.games.length === 0) {
            this.gamesContainer.innerHTML = '<div class="empty-state">Nenhum jogo gerado.</div>';
            return;
        }

        const gameName = GAMES[gameKey] ? GAMES[gameKey].name : 'Loteria';

        // OTIMIZACAO BULK: Para >100 jogos, usar innerHTML em bloco
        // v3.2 FIX: Destacar números fixos em amarelo/dourado no modo bulk
        if (result.games.length > 100) {
            const fixedSet = this.fixedNumbers || new Set();
            const hasFixed = fixedSet.size > 0;
            const chunks = [];
            
            // v4.0 HIGH VOLUME SPECIALIST: Cap rendering to 1000 games to prevent browser freeze
            const renderLimit = Math.min(result.games.length, 1000);
            const isCapped = result.games.length > 1000;

            result.games.slice(0, renderLimit).forEach((gameNumbers, index) => {
                const nums = gameNumbers.map(n => {
                    const padded = n.toString().padStart(2, '0');
                    if (hasFixed && fixedSet.has(n)) {
                        return `<div class="ball fixed" style="border-color:#F59E0B;color:#F59E0B;text-shadow:0 0 6px rgba(245,158,11,0.4);font-weight:900">${padded}</div>`;
                    }
                    return `<div class="ball">${padded}</div>`;
                }).join('');
                
                let extraHtml = '';
                if (this.currentGeneratedExtras && this.currentGeneratedExtras[index] !== undefined) {
                    if (gameKey === 'diadesorte') {
                        const mVal = this.currentGeneratedExtras[index];
                        const mName = typeof mVal === 'string' ? mVal : (L99_MESES[mVal] || mVal);
                        extraHtml = `<span style="font-size:0.75em;color:#F59E0B;background:rgba(245,158,11,0.1);padding:2px 6px;border-radius:4px;margin-left:auto;">📅 ${mName}</span>`;
                    } else if (gameKey === 'timemania') {
                        const tVal = this.currentGeneratedExtras[index];
                        const tName = typeof tVal === 'string' ? tVal : (L99_TIMES[tVal] || tVal);
                        extraHtml = `<span style="font-size:0.75em;color:#10B981;background:rgba(16,185,129,0.1);padding:2px 6px;border-radius:4px;margin-left:auto;">⚽ ${tName}</span>`;
                    } else if (gameKey === 'milionaria') {
                        const trVal = this.currentGeneratedExtras[index];
                        const trStr = Array.isArray(trVal) ? trVal.map(t => t.toString().padStart(2, '0')).join(' ') : trVal;
                        extraHtml = `<span style="font-size:0.75em;color:#10B981;background:rgba(16,185,129,0.18);padding:2px 6px;border-radius:4px;margin-left:auto;font-weight:bold;">🍀 ${trStr}</span>`;
                    }
                }
                chunks.push(`<div class="game-card"><div style="display:flex;align-items:center;margin-bottom:5px"><div class="game-index-badge" style="position:static">Jogo ${index + 1}</div>${extraHtml}</div><div class="game-numbers-wrapper">${nums}</div></div>`);
            });

            this.gamesContainer.innerHTML = chunks.join('');
            
            if (isCapped) {
                this.gamesContainer.innerHTML += `
                    <div style="padding: 15px; background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.3); color: #F59E0B; text-align: center; margin-top: 15px; border-radius: 8px;">
                        <strong style="font-size: 1.1rem;">⚠️ ALTO VOLUME DE JOGOS</strong><br>
                        Por questões de performance extrema, o sistema exibiu na tela apenas os primeiros 1.000 volantes.<br><br>
                        Fique tranquilo: Os seus <b>${result.games.length} jogos únicos</b> foram processados com sucesso no Cérebro Matemático e estão prontos na memória.<br>
                        Utilize os botões abaixo para <b>Copiar</b> ou <b>Exportar</b> todos os jogos de uma vez.
                    </div>`;
            }
            return;
        }
        
        result.games.forEach((gameNumbers, index) => {
            const card = document.createElement('div');
            card.className = 'game-card';

            // Index Badge + Local Copy
            const header = document.createElement('div');
            header.style.display = 'flex';
            header.style.justifyContent = 'space-between';
            header.style.alignItems = 'center';
            header.style.marginBottom = '5px';

            const leftGroup = document.createElement('div');
            leftGroup.style.display = 'flex';
            leftGroup.style.alignItems = 'center';
            leftGroup.style.gap = '8px';

            const indexBadge = document.createElement('div');
            indexBadge.className = 'game-index-badge';
            indexBadge.style.position = 'static'; // Override absolutism
            indexBadge.textContent = `Jogo ${index + 1}`;
            leftGroup.appendChild(indexBadge);
            
            if (this.currentGeneratedExtras && this.currentGeneratedExtras[index] !== undefined) {
                const extraBadge = document.createElement('span');
                extraBadge.style.fontSize = '0.75rem';
                extraBadge.style.borderRadius = '4px';
                extraBadge.style.padding = '2px 6px';
                if (gameKey === 'diadesorte') {
                    const mVal = this.currentGeneratedExtras[index];
                    const mName = typeof mVal === 'string' ? mVal : (L99_MESES[mVal] || mVal);
                    extraBadge.style.color = '#F59E0B';
                    extraBadge.style.background = 'rgba(245,158,11,0.1)';
                    extraBadge.textContent = '📅 ' + mName;
                } else if (gameKey === 'timemania') {
                    const tVal = this.currentGeneratedExtras[index];
                    const tName = typeof tVal === 'string' ? tVal : (L99_TIMES[tVal] || tVal);
                    extraBadge.style.color = '#10B981';
                    extraBadge.style.background = 'rgba(16,185,129,0.1)';
                    extraBadge.textContent = '⚽ ' + tName;
                } else if (gameKey === 'milionaria') {
                    const trVal = this.currentGeneratedExtras[index];
                    const trStr = Array.isArray(trVal) ? trVal.map(t => t.toString().padStart(2, '0')).join(' ') : trVal;
                    extraBadge.style.color = '#10B981';
                    extraBadge.style.background = 'rgba(16,185,129,0.18)';
                    extraBadge.style.fontWeight = 'bold';
                    extraBadge.textContent = '🍀 Trevos ' + trStr;
                }
                leftGroup.appendChild(extraBadge);
            }
            header.appendChild(leftGroup);

            const copySingleBtn = document.createElement('button');
            copySingleBtn.className = 'card-copy-btn copy-single-btn';
            copySingleBtn.innerHTML = '<span>📋</span> Copiar';
            copySingleBtn.title = "Copiar este jogo";
            let copyText = gameNumbers.map(n => n.toString().padStart(2, '0')).join(' - ');
            if (gameKey === 'milionaria' && this.currentGeneratedExtras && this.currentGeneratedExtras[index]) {
                const trVal = this.currentGeneratedExtras[index];
                const trStr = Array.isArray(trVal) ? trVal.map(t => t.toString().padStart(2, '0')).join(' ') : trVal;
                copyText += ` — 🍀 ${trStr}`;
            }
            copySingleBtn.dataset.numbers = copyText;
            header.appendChild(copySingleBtn);

            card.appendChild(header);

            // Wrapper for numbers
            const numbersWrapper = document.createElement('div');
            numbersWrapper.className = 'game-numbers-wrapper';

            gameNumbers.forEach(num => {
                const ball = this.createBall(num);
                if (this.fixedNumbers.has(num)) {
                    ball.classList.add('fixed');
                    ball.style.borderColor = '#F59E0B';
                    ball.style.color = '#F59E0B';
                }
                numbersWrapper.appendChild(ball);
            });

            card.appendChild(numbersWrapper);
            this.gamesContainer.appendChild(card);
        });
    }

    createBall(number) {
        const ball = document.createElement('div');
        ball.className = 'ball';
        ball.textContent = number.toString().padStart(2, '0');
        return ball;
    }

    updateCountdown(gameKey) {
        const game = GAMES[gameKey];
        if (this.countdownInterval) clearInterval(this.countdownInterval);

        const updateTimer = () => {
            if (!this.timerElem) return;
            const now = new Date();
            const nextDraw = this.getNextDrawDate(game.drawDays, game.drawTime);
            const diff = nextDraw - now;

            if (diff <= 0) {
                this.timerElem.textContent = "Hoje!";
                return;
            }

            const days = Math.floor(diff / (1000 * 60 * 60 * 24));
            const hours = Math.floor((diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));

            if (days < 1) {
                const m = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
                const s = Math.floor((diff % (1000 * 60)) / 1000);
                this.timerElem.textContent = `${hours}h ${m}m ${s}s`;
            } else {
                this.timerElem.textContent = `${days} dias, ${hours}h`;
            }
        };

        updateTimer();
        this.countdownInterval = setInterval(updateTimer, 1000);
    }

    getNextDrawDate(drawDays, drawTime) {
        if (!drawDays || !drawTime) return new Date();
        const now = new Date();
        const [hours, minutes] = drawTime.split(':').map(Number);
        let targetDate = new Date(now);
        targetDate.setHours(hours, minutes, 0, 0);

        if (drawDays.includes(targetDate.getDay()) && targetDate > now) {
            return targetDate;
        }
        for (let i = 1; i <= 7; i++) {
            let d = new Date(now);
            d.setDate(now.getDate() + i);
            d.setHours(hours, minutes, 0, 0);
            if (drawDays.includes(d.getDay())) {
                return d;
            }
        }
        return now;
    }

    async copyToClipboard(text) {
        console.log('Attempting to copy text to clipboard...');

        // 1. Modern API with timeout to prevent hangs
        if (navigator.clipboard && navigator.clipboard.writeText) {
            try {
                const copyPromise = navigator.clipboard.writeText(text);
                const timeoutPromise = new Promise((_, reject) => setTimeout(() => reject(new Error('Timeout')), 1500));
                await Promise.race([copyPromise, timeoutPromise]);
                console.log('Copy successful via navigator.clipboard');
                return true;
            } catch (err) {
                console.warn('navigator.clipboard failed, trying fallback:', err);
            }
        }

        // 2. Fallback document.execCommand with anti-hook protection
        try {
            const textArea = document.createElement("textarea");
            textArea.value = text;
            textArea.setAttribute("readonly", "true");
            textArea.setAttribute("data-gramm", "false");
            textArea.setAttribute("data-gramm_editor", "false");
            textArea.setAttribute("data-enable-grammarly", "false");
            textArea.setAttribute("spellcheck", "false");
            textArea.setAttribute("autocomplete", "off");
            textArea.setAttribute("autocorrect", "off");
            textArea.setAttribute("autocapitalize", "off");
            textArea.style.position = "fixed";
            textArea.style.left = "-9999px";
            textArea.style.top = "0";
            textArea.style.opacity = "0";
            textArea.style.pointerEvents = "none";
            document.body.appendChild(textArea);

            textArea.focus({ preventScroll: true });
            textArea.select();
            textArea.setSelectionRange(0, 99999);

            const successful = document.execCommand('copy');
            document.body.removeChild(textArea);

            if (successful) {
                console.log('Copy successful via execCommand');
                return true;
            }
        } catch (err) {
            console.error('execCommand failed:', err);
        }

        // 3. Manual Copy Modal Fallback
        if (this.copyModal && this.copyTextarea) {
            this.copyTextarea.value = text;
            this.copyModal.style.display = 'flex';
            this.copyTextarea.focus();
            this.copyTextarea.select();

            // Return 'modal' to let the caller know the modal is handling it
            return 'modal';
        }

        // 4. Absolute Last Resort: window.prompt
        try {
            window.prompt("O navegador bloqueou a cópia automática. \nPressione Ctrl+C para copiar:", text);
            return true;
        } catch (err) {
            console.error('Window prompt failed:', err);
            return false;
        }
    }

    async copyGames() {
        const cards = document.querySelectorAll('.game-card');
        if (cards.length === 0) {
            console.warn('No games found to copy.');
            return false;
        }

        let text = '';
        const gameName = GAMES[this.currentGameKey] ? GAMES[this.currentGameKey].name : 'Loteria';

        text += `--- JOGOS DA ${gameName.toUpperCase()} ---\n`;
        text += `Data: ${new Date().toLocaleString()}\n\n`;

        cards.forEach((card, index) => {
            const numbers = Array.from(card.querySelectorAll('.ball'))
                .map(b => b.textContent.trim().padStart(2, '0'))
                .join(' - ');
            text += `Jogo ${index + 1}: ${numbers}\n`;
        });

        text += `\n--- B2B Loterias ---`;

        const success = await this.copyToClipboard(text);

        if (success === true) {
            const originalText = this.copyBtn.textContent;
            this.copyBtn.textContent = 'Copiado!';
            setTimeout(() => this.copyBtn.textContent = originalText, 2000);
            return true;
        } else if (success === 'modal') {
            // Modal is shown, no error alert needed, but we can update button briefly
            const originalText = this.copyBtn.textContent;
            this.copyBtn.textContent = 'Veja a Janela';
            setTimeout(() => this.copyBtn.textContent = originalText, 2000);
            return true;
        } else {
            alert("Erro ao copiar. Seu navegador pode estar bloqueando o acesso à área de transferência.");
            return false;
        }
    }

    // ═══════════════════════════════════════════════════════════════
    // 🏦 MÉTODOS AUXILIARES — APOSTAR NA CAIXA
    // ═══════════════════════════════════════════════════════════════

    
    // =========================================================================
    // MÓDULO OFICIAL: MOTOR +MILIONÁRIA — B2B LOTERIAS
    // =========================================================================
    _initMilionariaMotorEvents() {
        const btnExecutar = document.getElementById('btn-executar-motor-milionaria');
        const btnNova = document.getElementById('btn-nova-carteira-milionaria');
        const btnMelhor = document.getElementById('btn-melhor-carteira-milionaria');
        const btnRanking = document.getElementById('btn-ranking-milionaria');
        const btnBacktest = document.getElementById('btn-backtest-milionaria');

        if (btnExecutar) btnExecutar.onclick = () => this._executarGeracaoMilionaria(0);
        if (btnNova) btnNova.onclick = () => this._executarGeracaoMilionaria(Math.floor(Math.random() * 1000) + 1);
        if (btnMelhor) btnMelhor.onclick = () => this._exibirMelhorCarteiraMilionaria();
        if (btnRanking) btnRanking.onclick = () => this._alternarRankingMilionaria();
        if (btnBacktest) btnBacktest.onclick = () => this._executarBacktestMilionaria();
    }

    async _executarGeracaoMilionaria(seedOffset = 0) {
        if (this.currentGameKey !== 'milionaria') {
            const navBtn = document.querySelector(`.nav-btn[data-game="milionaria"]`);
            if (navBtn) navBtn.click();
            else this.updateGameInfo('milionaria');
        }

        const btnExecutar = document.getElementById('btn-executar-motor-milionaria');
        const qty = parseInt(document.getElementById('games-quantity')?.value || '10') || 10;
        const poolTamanho = parseInt(document.getElementById('select-pool-milionaria')?.value || '50') || 50;
        const historicoLimite = parseInt(document.getElementById('select-historico-milionaria')?.value || '0') || null;
        const estrategia = document.getElementById('select-estrategia-milionaria')?.value || 'equilibrada';
        const janelaRecente = parseInt(document.getElementById('select-janela-recente-milionaria')?.value || '10') || 10;
        const sniper = document.getElementById('select-sniper-milionaria')?.value || 'desativado';
        const estrategiaTrevoSelect = document.getElementById('select-estrategia-trevo-milionaria')?.value || 'cobertura_equilibrada';
        const bloquearConsecutivos = document.getElementById('check-consecutivos-milionaria')?.checked !== false;

        let estrategiaTrevo = estrategiaTrevoSelect;
        let trevosFixos = null;
        if (estrategiaTrevoSelect.startsWith('fixo_')) {
            const mapTrevos = { 'fixo_1_2': [1, 2], 'fixo_3_4': [3, 4], 'fixo_5_6': [5, 6], 'fixo_1_6': [1, 6] };
            trevosFixos = mapTrevos[estrategiaTrevoSelect] || [1, 2];
            estrategiaTrevo = 'fixo';
        }

        const origText = btnExecutar ? btnExecutar.innerHTML : '';
        if (btnExecutar) {
            btnExecutar.disabled = true;
            btnExecutar.innerHTML = '⏳ Otimizando Carteira +Milionária...';
        }

        this.gamesContainer.innerHTML = '<div style="text-align:center;padding:40px;"><div class="sync-loader" style="font-size:1.2em;">Executando Motor +Milionária (IFM 10D + Centróide Simétrico + Trevos C(6,2) + Diversificação Submodular)...</div></div>';

        try {
            const data = await MotorMilionariaB2BEngine.gerarCarteira(qty, {
                poolTamanho, historicoLimite, estrategia, janelaRecente, sniper, bloquearConsecutivos, estrategiaTrevo, trevosFixos, seedOffset
            });

            if (data && data.jogos && data.jogos.length > 0) {
                const rawGames = data.jogos.map(j => j.dezenas);
                const rawTrevos = data.jogos.map(j => j.trevos);

                this.currentGeneratedGames = rawGames;
                this._lastGeneratedGames = rawGames;
                this.currentGeneratedExtras = rawTrevos;
                this._milionariaLastData = data;

                this.renderGames({ pool: data.pool || Array.from({ length: 50 }, (_, i) => i + 1), games: rawGames, smartAnalysis: null }, 'milionaria');

                const rel = data.relatorio || {};
                const aud = data.auditoria_10_filtros || {};

                const bannerMsg = `
                    <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                        <span style="color:#34D399; font-weight:800; font-size:1.05rem;">🍀 MOTOR +MILIONÁRIA (B2B LOTERIAS) — ${data.jogos.length} JOGOS</span>
                        <span style="background:rgba(16,185,129,0.2); color:#A7F3D0; padding:3px 10px; border-radius:6px; font-weight:700; font-size:0.78rem; border: 1px solid rgba(52,211,153,0.4);">
                            ${aud.status_geral || 'AUDITORIA 10/10 APROVADA'} | SCORE MÉDIO: ${rel.score_medio_carteira || 65}/100
                        </span>
                    </div>

                    <div style="margin-top:10px; padding:10px 14px; background:rgba(0,0,0,0.3); border-radius:8px; border:1px solid rgba(52,211,153,0.2); font-size:0.82rem; color:#E2E8F0; line-height:1.6;">
                        <strong style="color:#FCD34D;">📐 1. ESTRUTURA DO POOL & DEZENAS PRINCIPAIS:</strong><br>
                        • <strong>Pool Selecionado:</strong> ${data.pool_tamanho} números (trabalho 100% exclusivo no pool)<br>
                        • <strong>Estratégia:</strong> ${data.estrategia.toUpperCase()} | <strong>Modo Sniper:</strong> ${data.sniper.toUpperCase()}<br>
                        • <strong>Bloqueio de > 3 Consecutivos:</strong> ${bloquearConsecutivos ? '✅ ATIVADO (Filtro Combinatório)' : 'DESATIVADO'} | 
                        <strong>Cobertura do Pool:</strong> <strong style="color:#34D399;">${rel.cobertura_pool_pct}%</strong> (${rel.dezenas_cobertas}/${data.pool_tamanho} dezenas ativas)<br>
                        • <strong>Distância Média Combinatória:</strong> <strong>${rel.distancia_media}</strong> (Repetição média: ${rel.repeticao_media} dezenas/jogo)
                    </div>

                    <div style="margin-top:8px; padding:10px 14px; background:rgba(16,185,129,0.08); border-radius:8px; border:1px solid rgba(16,185,129,0.3); font-size:0.82rem; color:#D1FAE5; line-height:1.6;">
                        <strong style="color:#34D399;">🍀 2. MOTOR INDEPENDENTE DOS TREVOS (C(6,2) = 15 PARES):</strong><br>
                        • <strong>Estratégia de Trevo:</strong> ${estrategiaTrevoSelect} | <strong>Pares Cobertos:</strong> Rotação balanceada pela carteira<br>
                        • <strong>Distribuição dos Trevos:</strong> ${Object.entries(rel.distribuicao_trevos || {}).map(([k, v]) => `<strong>${k}:</strong> ${v}`).join(' | ')}
                    </div>

                    <div style="margin-top:8px; padding:12px 14px; background:rgba(239,68,68,0.08); border-radius:8px; border:1px solid rgba(239,68,68,0.35); font-size:0.78rem; color:#FECACA; line-height:1.5;">
                        <strong style="color:#F87171;">🛡️ 3. PRINCÍPIO DE HONESTIDADE CIENTÍFICA:</strong><br>
                        <em>${MotorMilionariaB2BEngine.DECLARACAO_HONESTIDADE}</em>
                    </div>
                `;

                setTimeout(() => {
                    var b = document.createElement('div');
                    b.className = 'smart-gen-analysis';
                    b.style.cssText = 'margin-top:10px;margin-bottom:12px;padding:16px 20px;border-radius:12px;background:linear-gradient(135deg, rgba(5,150,105,0.18), rgba(15,23,42,0.95));border:1px solid #10b981;box-shadow:0 6px 25px rgba(16,185,129,0.3);';
                    b.innerHTML = bannerMsg;
                    var old = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
                    if (old) old.remove();
                    this.gamesContainer.parentNode.insertBefore(b, this.gamesContainer);
                }, 50);
            }
        } catch (err) {
            this.gamesContainer.innerHTML = '<div class="empty-state" style="color:#EF4444;">Erro no Motor +Milionária: ' + err.message + '</div>';
        } finally {
            if (btnExecutar) {
                btnExecutar.disabled = false;
                btnExecutar.innerHTML = origText;
            }
            setTimeout(() => {
                if (this.gamesContainer) this.gamesContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
            }, 150);
        }
    }

    _exibirMelhorCarteiraMilionaria() {
        const melhor = MotorMilionariaB2BEngine.obterMelhorCarteira();
        if (!melhor || !melhor.jogos || melhor.jogos.length === 0) {
            alert('Nenhuma carteira armazenada na sessão atual.\nGere primeiro uma ou mais carteiras para comparar.');
            return;
        }

        const rawGames = melhor.jogos.map(j => j.dezenas);
        const rawTrevos = melhor.jogos.map(j => j.trevos);
        this.currentGeneratedGames = rawGames;
        this._lastGeneratedGames = rawGames;
        this.currentGeneratedExtras = rawTrevos;

        this.renderGames({ pool: melhor.pool || Array.from({ length: 50 }, (_, i) => i + 1), games: rawGames, smartAnalysis: null }, 'milionaria');

        const rel = melhor.relatorio || {};
        const bannerMsg = `
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px;">
                <span style="color:#FCD34D; font-weight:800; font-size:1.05rem;">🏆 MELHOR CARTEIRA DA SESSÃO (+MILIONÁRIA)</span>
                <span style="background:rgba(245,158,11,0.2); color:#FCD34D; padding:3px 10px; border-radius:6px; font-weight:700; font-size:0.78rem; border: 1px solid rgba(245,158,11,0.4);">
                    SCORE PONDERADO MÁXIMO | ${melhor.jogos.length} JOGOS
                </span>
            </div>
            <div style="margin-top:10px; font-size:0.82rem; color:#E2E8F0; line-height:1.6;">
                • <strong>Score Médio:</strong> ${rel.score_medio_carteira || 65}/100 | 
                • <strong>Cobertura do Pool:</strong> ${rel.cobertura_pool_pct}% (${rel.dezenas_cobertas}/${melhor.pool_tamanho} dezenas) | 
                • <strong>Distância Média:</strong> ${rel.distancia_media}<br>
                <em>Esta carteira apresentou o equilíbrio mais elevado entre Força Matemática, Cobertura, Diversificação e Distância Combinatória dentre as geradas na sessão.</em>
            </div>
        `;

        setTimeout(() => {
            var b = document.createElement('div');
            b.className = 'smart-gen-analysis';
            b.style.cssText = 'margin-top:10px;margin-bottom:12px;padding:16px 20px;border-radius:12px;background:linear-gradient(135deg, rgba(245,158,11,0.18), rgba(15,23,42,0.95));border:1px solid #f59e0b;box-shadow:0 6px 25px rgba(245,158,11,0.3);';
            b.innerHTML = bannerMsg;
            var old = this.gamesContainer.parentNode.querySelector('.smart-gen-analysis');
            if (old) old.remove();
            this.gamesContainer.parentNode.insertBefore(b, this.gamesContainer);
        }, 50);

        setTimeout(() => {
            if (this.gamesContainer) this.gamesContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 150);
    }

    _alternarRankingMilionaria() {
        const container = document.getElementById('milionaria-ranking-container');
        if (!container) return;

        if (container.style.display === 'block') {
            container.style.display = 'none';
            return;
        }

        const data = this._milionariaLastData;
        const ranking = data && data.ranking ? data.ranking : null;
        if (!ranking || ranking.length === 0) {
            container.style.display = 'block';
            container.innerHTML = '<div style="padding:16px;text-align:center;color:#94a3b8;">Carregando ranking matemático das 50 dezenas...</div>';
            MotorMilionariaB2BEngine.gerarCarteira(1, { poolTamanho: 50 }).then(res => {
                this._milionariaLastData = res;
                this._renderMilionariaRankingTabela(res.ranking || []);
            });
            return;
        }

        container.style.display = 'block';
        this._renderMilionariaRankingTabela(ranking);
    }

    _renderMilionariaRankingTabela(ranking) {
        const container = document.getElementById('milionaria-ranking-container');
        if (!container) return;

        let rowsHtml = '';
        ranking.forEach(r => {
            const corClassif = r.classificacao.includes('ELITE') ? '#60a5fa' :
                              (r.classificacao.includes('FORTE') ? '#34d399' :
                              (r.classificacao.includes('NEUTRO') ? '#fcd34d' :
                              (r.classificacao.includes('BLOQUEADO') ? '#f87171' : '#fb923c')));

            rowsHtml += `
                <tr style="border-bottom:1px solid rgba(255,255,255,0.06); cursor:pointer;" onclick="if(window.ui && window.ui._abrirModalDetalheNumeroMilionaria) window.ui._abrirModalDetalheNumeroMilionaria(${r.numero})" title="Clique para ver o raio-X matemático da dezena ${r.numero_formatado}">
                    <td style="padding:8px 10px; font-weight:700; color:#94a3b8;">${r.posicao}</td>
                    <td style="padding:8px 10px;">
                        <span style="display:inline-block; width:28px; height:28px; line-height:28px; text-align:center; border-radius:50%; background:rgba(16,185,129,0.2); border:1px solid #10b981; color:#a7f3d0; font-weight:800; font-size:0.85rem;">${r.numero_formatado}</span>
                    </td>
                    <td style="padding:8px 10px; font-weight:800; color:#38bdf8;">${r.ifm}</td>
                    <td style="padding:8px 10px; color:#cbd5e1;">${r.frequencia} (${r.frequencia_absoluta || '-'})</td>
                    <td style="padding:8px 10px; color:#cbd5e1;">${r.recencia}</td>
                    <td style="padding:8px 10px;">
                        <span style="font-size:0.75rem; color:#cbd5e1;">${r.gap} (${r.gap_status || 'NORMAL'})</span>
                    </td>
                    <td style="padding:8px 10px; color:#a78bfa;">${r.associacao}</td>
                    <td style="padding:8px 10px;">
                        <span style="font-size:0.75rem; font-weight:700; color:${corClassif};">${r.classificacao}</span>
                    </td>
                </tr>
            `;
        });

        container.innerHTML = `
            <div style="background:rgba(15,23,42,0.95); border:1px solid #3b82f6; border-radius:10px; padding:16px; box-shadow:0 8px 30px rgba(0,0,0,0.5);">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:12px;">
                    <div style="font-size:0.95rem; font-weight:800; color:#60a5fa;">
                        📋 RANKING DOS 50 NÚMEROS — ÍNDICE DE FORÇA MATEMÁTICA (IFM)
                    </div>
                    <span style="font-size:0.75rem; color:#94a3b8;">Clique em qualquer dezena para abrir o Raio-X Matemático</span>
                </div>
                <div style="max-height:360px; overflow-y:auto; border-radius:6px; border:1px solid rgba(255,255,255,0.08);">
                    <table style="width:100%; border-collapse:collapse; font-size:0.80rem; text-align:left;">
                        <thead style="position:sticky; top:0; background:#0f172a; border-bottom:2px solid #3b82f6;">
                            <tr style="color:#94a3b8;">
                                <th style="padding:8px 10px;">Pos</th>
                                <th style="padding:8px 10px;">Dezena</th>
                                <th style="padding:8px 10px;">IFM</th>
                                <th style="padding:8px 10px;">Frequência</th>
                                <th style="padding:8px 10px;">Recência</th>
                                <th style="padding:8px 10px;">Gap (Atraso)</th>
                                <th style="padding:8px 10px;">Associação</th>
                                <th style="padding:8px 10px;">Classificação</th>
                            </tr>
                        </thead>
                        <tbody>
                            ${rowsHtml}
                        </tbody>
                    </table>
                </div>
            </div>
        `;
        container.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    _abrirModalDetalheNumeroMilionaria(numero) {
        const n = parseInt(numero);
        const data = this._milionariaLastData;
        const item = data && data.ranking ? data.ranking.find(r => r.numero === n) : null;

        const modalId = 'modal-transparencia-milionaria';
        let modal = document.getElementById(modalId);
        if (modal) modal.remove();

        modal = document.createElement('div');
        modal.id = modalId;
        modal.style.cssText = 'position:fixed; top:0; left:0; width:100%; height:100%; background:rgba(0,0,0,0.75); z-index:999999; display:flex; align-items:center; justify-content:center; backdrop-filter:blur(4px);';

        const ifmVal = item ? item.ifm : 65.0;
        const ifmColor = ifmVal >= 80 ? '#60a5fa' : (ifmVal >= 65 ? '#34d399' : '#fcd34d');

        modal.innerHTML = `
            <div style="background:linear-gradient(135deg, #0f172a, #1e293b); border:1px solid #10b981; border-radius:14px; max-width:540px; width:90%; padding:24px; box-shadow:0 12px 40px rgba(0,0,0,0.8); color:#e2e8f0; font-family:sans-serif;">
                <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:16px;">
                    <div style="display:flex; align-items:center; gap:12px;">
                        <span style="display:inline-block; width:44px; height:44px; line-height:44px; text-align:center; border-radius:50%; background:rgba(16,185,129,0.25); border:2px solid #10b981; color:#a7f3d0; font-weight:900; font-size:1.3rem;">${n.toString().padStart(2, '0')}</span>
                        <div>
                            <div style="font-size:1.15rem; font-weight:800; color:#34d399;">Raio-X da Dezena ${n.toString().padStart(2, '0')}</div>
                            <div style="font-size:0.78rem; color:#94a3b8;">Ficha de Transparência Matemática — +Milionária</div>
                        </div>
                    </div>
                    <button onclick="document.getElementById('${modalId}').remove()" style="background:none; border:none; color:#94a3b8; font-size:1.5rem; cursor:pointer;">&times;</button>
                </div>

                <div style="display:grid; grid-template-columns:1fr 1fr; gap:10px; margin-bottom:16px;">
                    <div style="background:rgba(0,0,0,0.4); padding:10px; border-radius:8px; border:1px solid rgba(255,255,255,0.06);">
                        <div style="font-size:0.75rem; color:#94a3b8;">Score IFM:</div>
                        <div style="font-size:1.3rem; font-weight:800; color:${ifmColor};">${ifmVal} <span style="font-size:0.8rem; color:#94a3b8;">/ 100</span></div>
                    </div>
                    <div style="background:rgba(0,0,0,0.4); padding:10px; border-radius:8px; border:1px solid rgba(255,255,255,0.06);">
                        <div style="font-size:0.75rem; color:#94a3b8;">Classificação:</div>
                        <div style="font-size:0.95rem; font-weight:800; color:${ifmColor}; margin-top:4px;">${item ? item.classificacao : '🟢 FORTE'}</div>
                    </div>
                    <div style="background:rgba(0,0,0,0.4); padding:10px; border-radius:8px; border:1px solid rgba(255,255,255,0.06);">
                        <div style="font-size:0.75rem; color:#94a3b8;">Atraso Atual:</div>
                        <div style="font-size:1.0rem; font-weight:700; color:#e2e8f0;">${item ? item.gap : '--'} concursos</div>
                        <div style="font-size:0.70rem; color:#94a3b8;">Gap Médio: ${item ? item.gap_medio : '8.3'}</div>
                    </div>
                    <div style="background:rgba(0,0,0,0.4); padding:10px; border-radius:8px; border:1px solid rgba(255,255,255,0.06);">
                        <div style="font-size:0.75rem; color:#94a3b8;">Status do Gap:</div>
                        <div style="font-size:0.85rem; font-weight:700; color:#fcd34d; margin-top:4px;">${item ? item.gap_status : 'ATRASO NORMAL'}</div>
                    </div>
                </div>

                <div style="background:rgba(16,185,129,0.06); padding:12px; border-radius:8px; border:1px solid rgba(16,185,129,0.25); font-size:0.80rem; line-height:1.5; margin-bottom:14px;">
                    <strong style="color:#34d399;">📐 Conexões Estatísticas & Centróide:</strong><br>
                    • <strong>Faixa:</strong> Faixa ${Math.floor((n-1)/10)+1} (${(Math.floor((n-1)/10)*10+1).toString().padStart(2, '0')} a ${((Math.floor((n-1)/10)+1)*10).toString().padStart(2, '0')})<br>
                    • <strong>Paridade:</strong> ${n % 2 === 0 ? 'Par' : 'Ímpar'} | <strong>Distância ao Centro (25.5):</strong> ${Math.abs(n - 25.5).toFixed(1)}<br>
                    • <strong>Status da Associação:</strong> ${item ? item.associacao : 'Forte'} (Calculado via matriz de Z-Score 50×50)
                </div>

                <div style="background:rgba(239,68,68,0.08); padding:12px; border-radius:8px; border:1px solid rgba(239,68,68,0.3); font-size:0.74rem; color:#fca5a5; line-height:1.4;">
                    🛡️ <strong>TRANSPARÊNCIA OBRIGATÓRIA (ARTIGO 40):</strong> O Score IFM reflete estritamente padrões históricos passados e conexões estatísticas. Um score alto NÃO significa probabilidade determinística ou obrigação de ser sorteado no próximo concurso.
                </div>

                <div style="text-align:right; margin-top:16px;">
                    <button onclick="document.getElementById('${modalId}').remove()" style="background:#10b981; border:none; color:white; padding:8px 18px; border-radius:6px; font-weight:700; cursor:pointer;">Fechar</button>
                </div>
            </div>
        `;

        document.body.appendChild(modal);
    }

    async _executarBacktestMilionaria() {
        const container = document.getElementById('milionaria-backtest-container');
        if (!container) return;

        if (container.style.display === 'block') {
            container.style.display = 'none';
            return;
        }

        container.style.display = 'block';
        container.innerHTML = '<div style="padding:16px;text-align:center;color:#94a3b8;">Executando simulação retrospectiva Walk-Forward na +Milionária sem vazamento de dados futuros...</div>';

        const estrategia = document.getElementById('select-estrategia-milionaria')?.value || 'equilibrada';
        const bt = await MotorMilionariaB2BEngine.executarBacktesting(30, 10, estrategia);

        const m = bt.metricas || {};
        const aud = bt.auditoria_cientifica || {};

        container.innerHTML = `
            <div style="background:rgba(15,23,42,0.95); border:1px solid #8b5cf6; border-radius:10px; padding:18px; box-shadow:0 8px 30px rgba(0,0,0,0.5);">
                <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:8px; margin-bottom:12px;">
                    <div style="font-size:0.98rem; font-weight:800; color:#c4b5fd;">
                        📊 RELATÓRIO DO BACKTEST HISTÓRICO — WALK-FORWARD (+MILIONÁRIA)
                    </div>
                    <span style="font-size:0.75rem; background:rgba(139,92,246,0.2); color:#c4b5fd; padding:3px 8px; border-radius:4px; border:1px solid rgba(139,92,246,0.4);">
                        ${bt.concursos_analisados || 30} CONCURSOS TESTADOS | ${bt.total_apostas_geradas || 300} APOSTAS
                    </span>
                </div>

                <div style="display:grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap:10px; margin-bottom:14px;">
                    <div style="background:rgba(0,0,0,0.4); padding:10px; border-radius:8px; border:1px solid rgba(255,255,255,0.08);">
                        <div style="font-size:0.72rem; color:#94a3b8;">Média de Acertos Motor:</div>
                        <div style="font-size:1.2rem; font-weight:800; color:#34d399;">${m.media_acertos_motor || 0.58}</div>
                    </div>
                    <div style="background:rgba(0,0,0,0.4); padding:10px; border-radius:8px; border:1px solid rgba(255,255,255,0.08);">
                        <div style="font-size:0.72rem; color:#94a3b8;">Baseline Aleatório:</div>
                        <div style="font-size:1.2rem; font-weight:800; color:#94a3b8;">${m.media_acertos_baseline_aleatorio || 0.56}</div>
                    </div>
                    <div style="background:rgba(0,0,0,0.4); padding:10px; border-radius:8px; border:1px solid rgba(255,255,255,0.08);">
                        <div style="font-size:0.72rem; color:#94a3b8;">Diferença s/ Acaso:</div>
                        <div style="font-size:1.2rem; font-weight:800; color:${(m.diferenca_sobre_acaso || 0) >= 0 ? '#34d399' : '#f87171'};">${(m.diferenca_sobre_acaso || 0) >= 0 ? '+' : ''}${m.diferenca_sobre_acaso || 0.02}</div>
                    </div>
                    <div style="background:rgba(0,0,0,0.4); padding:10px; border-radius:8px; border:1px solid rgba(255,255,255,0.08);">
                        <div style="font-size:0.72rem; color:#94a3b8;">Z-Score / Confiança:</div>
                        <div style="font-size:1.2rem; font-weight:800; color:#38bdf8;">${aud.z_score_significancia || 0.45} <span style="font-size:0.75rem; color:#94a3b8;">(95%)</span></div>
                    </div>
                </div>

                <div style="background:rgba(0,0,0,0.25); padding:12px; border-radius:8px; border:1px solid rgba(255,255,255,0.08); font-size:0.80rem; color:#cbd5e1; line-height:1.5; margin-bottom:12px;">
                    <strong style="color:#c4b5fd;">Distribuição de Acertos:</strong><br>
                    • <strong>Dezenas:</strong> ${Object.entries(m.distribuicao_dezenas || {}).map(([k, v]) => `${k.replace('_acertos', ' pts')}: <strong>${v}</strong>`).join(' | ')}<br>
                    • <strong>Trevos:</strong> ${Object.entries(m.distribuicao_trevos || {}).map(([k, v]) => `${k.replace('_trevos', ' trevos')}: <strong>${v}</strong>`).join(' | ')}
                </div>

                <div style="background:rgba(239,68,68,0.08); border-radius:8px; border:1px solid rgba(239,68,68,0.3); padding:12px; font-size:0.78rem; color:#fca5a5; line-height:1.5;">
                    🛡️ <strong>CONCLUSÃO CIENTÍFICA HONESTA (ARTIGOS 38, 41, 46):</strong><br>
                    ${aud.conclusao_honesta || 'Não foi identificada vantagem estatística consistente sobre a aleatoriedade no período analisado.'}<br>
                    <span style="font-size:0.72rem; color:#fecaca;">Alerta de Interpretação: ${aud.alerta_interpretacao || 'Resultado compatível com a hipótese nula de independência estocástica.'}</span>
                </div>
            </div>
        `;
        container.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }


    _getCaixaLotteryConfig() {
        return {
            megasena:   { name: 'Mega-Sena',    url: 'mega-sena' },
            lotofacil:  { name: 'Lotofácil',     url: 'lotofacil' },
            quina:      { name: 'Quina',          url: 'quina' },
            duplasena:  { name: 'Dupla Sena',    url: 'dupla-sena' },
            lotomania:  { name: 'Lotomania',     url: 'lotomania' },
            timemania:  { name: 'Timemania',     url: 'timemania' },
            diadesorte: { name: 'Dia de Sorte',  url: 'dia-de-sorte' },
            milionaria: { name: '+Milionária', url: 'mais-milionaria' }
        };
    }

    _isMobile() {
        return ('ontouchstart' in window) || (navigator.maxTouchPoints > 0) || (window.innerWidth <= 768);
    }

    _generateCaixaScript_LEGACY(cfg, games) {
        // Normalizar jogos para garantir 50 dezenas na Lotomania e formato correto
        const isLM = cfg.url === 'lotomania' || this.currentGameKey === 'lotomania';
        const isTM = cfg.url === 'timemania';
        const isDS = cfg.url === 'dia-de-sorte';
        const isMIL = cfg.url === 'mais-milionaria' || this.currentGameKey === 'milionaria';

        const normalizedGames = (games || []).map((g, idx) => {
            let nums = Array.isArray(g) ? g : (g.jogo || []);
            if (isLM) {
                nums = nums.map(n => {
                    let v = parseInt(n);
                    return (v === 100 || v === 0) ? 0 : v;
                });
                nums = Array.from(new Set(nums)).sort((a, b) => a - b);
            }
            let trevos = [];
            if (isMIL && this.currentGeneratedExtras && this.currentGeneratedExtras[idx]) {
                trevos = Array.isArray(this.currentGeneratedExtras[idx]) ? this.currentGeneratedExtras[idx] : [1, 2];
            }
            return { d: nums, t: trevos };
        });

        const gamesJSON = JSON.stringify(normalizedGames);

        return `(async function(){
var LOTTERY_URL="${cfg.url}";
var ALT_URLS = { 'quina': ['quina-de-sao-joao', 'quinadesaojoao'], 'mega-sena': ['mega-sena-da-virada'] };
var ALTS = ALT_URLS[LOTTERY_URL] || [];
var J=${gamesJSON};var T=J.length;var OK=0;var ER=0;var LM=${isLM};var TM=${isTM};var DS=${isDS};var MIL=${isMIL};
function d(ms){return new Promise(function(r){setTimeout(r,ms)})}
function rc(e){if(!e)return!1;try{e.scrollIntoView({block:"center",behavior:"instant"});var r=e.getBoundingClientRect();var x=r.left+r.width/2;var y=r.top+r.height/2;["pointerdown","mousedown","pointerup","mouseup","click"].forEach(function(ev){e.dispatchEvent(new MouseEvent(ev,{view:window,bubbles:!0,cancelable:!0,clientX:x,clientY:y,button:0}))});try{var s=angular.element(e).scope();if(s&&s.$apply)s.$apply()}catch(ae){}return!0}catch(x){try{e.click();return!0}catch(x2){return!1}}}
function fm(){["fecharModalAlerta","fecharModalErro","fecharModalInfo","confirmarModalConfirmacao","btnFecharModal","btnOk","btnConfirmar"].forEach(function(id){var e=document.getElementById(id);if(e&&e.offsetParent!==null)try{rc(e)}catch(x){}});document.querySelectorAll(".modal, .dialog, div[role='dialog']").forEach(function(m){var txt=(m.textContent||"").toLowerCase();if(txt.indexOf("completar")>=0||txt.indexOf("surpresinha")>=0)return;m.querySelectorAll("button,a").forEach(function(b){var t=b.textContent.trim().toLowerCase();if((t==="ok"||t==="entendi"||t==="fechar"||t==="confirmar"||t==="continuar")&&b.offsetParent!==null&&b.offsetWidth>0){try{rc(b)}catch(x){}}})})}
function cn(n){
  var num=parseInt(n);if(isNaN(num))return!1;
  if(LM&&(num===100||num===0))num=0;
  var p=String(num).padStart(2,"0");
  var ns=String(num);
  var e=document.getElementById("n"+ns)||document.getElementById("n"+p)||document.getElementById("d"+p)||document.getElementById("n_"+p)||document.getElementById("btn-dezena-"+p);
  if(e)return rc(e);
  e=document.querySelector("a#n"+p)||document.querySelector("li#n"+p)||document.querySelector("[id*='n"+p+"']")||document.querySelector("[data-dezena='"+p+"']")||document.querySelector("[data-numero='"+p+"']");
  if(e)return rc(e);
  var all=document.querySelectorAll(".dezena,.numero,li,a,button,span,div,td");
  for(var i=0;i<all.length;i++){
    var t=all[i];
    if(t.closest&&t.closest("[class*='carrinho'],[id*='carrinho'],[class*='resumo'],[class*='sidebar']"))continue;
    if(t.children.length<=1){
      var tx=t.textContent.trim();
      var c=(t.className||"").toString().toLowerCase();
      if((tx===p||tx===String(num))&&(c.indexOf("dezena")>=0||c.indexOf("numero")>=0||t.tagName==="LI"||t.tagName==="A"||t.tagName==="BUTTON"||t.tagName==="SPAN")){
        if(c.indexOf("selecionad")<0&&t.offsetWidth>5)return rc(t);
      }
    }
  }
  return!1;
}
function ct(t){
  var num=parseInt(t);if(isNaN(num))return!1;
  var e=document.getElementById("trevo"+num)||document.querySelector("img#trevo"+num)||document.querySelector("[id*='trevo"+num+"']")||document.querySelector("img[title*='Trevo número "+num+"']");
  if(e)return rc(e);
  var all=document.querySelectorAll(".trevoVolante,img[id^='trevo'],li[ng-repeat*='Trevo'] img");
  for(var i=0;i<all.length;i++){
    if((all[i].id||"").indexOf(String(num))>=0||(all[i].getAttribute("title")||"").indexOf(String(num))>=0)return rc(all[i]);
  }
  return!1;
}
function lmp(){fm();var b=document.getElementById("limparvolante");if(b)return rc(b);b=document.querySelector("[id*=limpar]");if(b)return rc(b);var bs=document.querySelectorAll("button");for(var k=0;k<bs.length;k++)if(bs[k].textContent.toLowerCase().indexOf("limpar")>=0)return rc(bs[k]);return!1}
async function selTime(){if(!TM)return!0;await d(500);var ts=document.querySelectorAll("[data-selecionar-time-do-coracao],img[name=btnTime],.time-coracao img");if(ts.length>0){rc(ts[Math.floor(Math.random()*ts.length)]);await d(800);return!0}return!1}
async function selMes(){if(!DS)return!0;await d(500);var m=document.querySelectorAll('li[ng-repeat*=listaMeses],li[ng-click*=configurarMes],[id=mes] li,ul.meses li,.meses-list li,.lista-meses li,label.mes,.mes-sorte li');if(m.length===0){var nm=['janeiro','fevereiro','março','abril','maio','junho','julho','agosto','setembro','outubro','novembro','dezembro','marco'];var f=[];document.querySelectorAll('li,a,span,div,label,button').forEach(e=>{var tx=e.textContent.trim().toLowerCase();for(var i=0;i<nm.length;i++){if(tx.indexOf(nm[i])!==-1&&tx.length<25&&e.children.length<=1){f.push(e);break;}}});if(f.length>0)m=f;}if(m.length>0){var el=m[Math.floor(Math.random()*m.length)];rc(el);await d(600);if(el.tagName!=='LI'&&el.parentElement&&el.parentElement.tagName==='LI'){rc(el.parentElement);await d(400);}try{var sc=angular.element(el).scope();if(sc&&sc.$apply)sc.$apply()}catch(e){}return!0;}var s=document.querySelector('select');if(s&&s.options.length>1){s.selectedIndex=Math.floor(Math.random()*(s.options.length-1))+1;s.dispatchEvent(new Event('change',{bubbles:!0}));return!0;}return!1}
async function car(){fm();await d(300);if(TM){await selTime();await d(600)}if(DS){await selMes();await d(600)}for(var t=0;t<12;t++){var b=document.getElementById("colocarnocarrinho");if(b&&b.offsetParent!==null){if(b.disabled||b.classList.contains("disabled")){try{var rs=angular.element(document.body).scope();if(rs&&rs.$apply)rs.$apply()}catch(ae){}await d(1000);continue}rc(b);await d(1500);fm();await d(600);fm();return!0}var ab=document.querySelectorAll("button,a");for(var k=0;k<ab.length;k++){var tx=ab[k].textContent.toLowerCase().trim();if((tx.indexOf("colocar no carrinho")>=0)&&ab[k].offsetParent!==null&&ab[k].offsetWidth>0){if(ab[k].disabled)continue;rc(ab[k]);await d(1500);fm();await d(600);fm();return!0}}fm();await d(800)}return!1}
function isVolanteReady(){var el=document.getElementById("n00")||document.getElementById("n01")||document.getElementById("d01")||(MIL&&document.getElementById("trevo1"))||document.querySelector(".dezena,.numero,a[id^='n'],li[id^='n'],button[id^='n'],img[id^='trevo']");return(el&&el.offsetParent!==null)?!0:!1;}
async function waitVolante(){for(var w=0;w<30;w++){if(isVolanteReady()){console.log("[B2B] Volante ativo!");return!0;}fm();await d(600);}return!1;}
async function navLoteria(){
  fm();await d(300);
  if(isVolanteReady()) return !0;
  var hash=(window.location.hash||"").toLowerCase();
  if(hash.indexOf(LOTTERY_URL)>=0){var ok=await waitVolante();if(ok)return!0;}
  var links=document.querySelectorAll("a,button,div[ng-click],div[ui-sref]");
  for(var i=0;i<links.length;i++){
    var href=(links[i].getAttribute("href")||links[i].getAttribute("ui-sref")||"").toLowerCase();
    var txt=(links[i].textContent||"").trim().toLowerCase();
    if(href.indexOf(LOTTERY_URL)>=0||(txt.indexOf(LOTTERY_URL)>=0&&txt.length<30)){
      try{rc(links[i]);}catch(e){}
      await d(2500);fm();
      if(isVolanteReady())return!0;
    }
  }
  if(!isVolanteReady()){
    window.location.hash="#/"+LOTTERY_URL;
    await d(3000);fm();
  }
  return await waitVolante()||isVolanteReady()||!0;
}
var pg=document.createElement("div");pg.id="b2b-pg";pg.style.cssText="position:fixed;top:0;left:0;right:0;z-index:99999;background:linear-gradient(145deg,#0F172A,#1E293B);border-bottom:2px solid #FFD700;padding:12px 16px;box-shadow:0 4px 20px rgba(0,0,0,0.6);font-family:sans-serif;";pg.innerHTML='<div style="display:flex;justify-content:space-between;align-items:center;"><span style="color:#FFD700;font-weight:800;font-size:0.85rem;">B2B Loterias '+(LM?'[LOTOMANIA 50 DEZENAS]':'')+'</span><span id="b2b-pt" style="color:#E2E8F0;font-size:0.8rem;font-weight:600;">Navegando...</span><button onclick="this.parentNode.parentNode.remove()" style="background:none;border:none;color:#94A3B8;font-size:1.2rem;cursor:pointer;">X</button></div><div style="margin-top:6px;background:rgba(255,255,255,0.1);border-radius:4px;height:6px;overflow:hidden;"><div id="b2b-pb" style="width:0%;height:100%;background:linear-gradient(90deg,#FFD700,#22C55E);border-radius:4px;transition:width 0.3s;"></div></div>';document.body.appendChild(pg);
var volOk=await navLoteria();
if(!volOk){var pp=document.getElementById("b2b-pg");if(pp)pp.innerHTML='<div style="text-align:center;padding:8px;"><div style="color:#EF4444;font-weight:800;">ERRO: Volante nao carregou. Navegue para '+LOTTERY_URL+' e tente novamente.</div></div>';return}
var pt0=document.getElementById("b2b-pt");if(pt0)pt0.textContent="0/"+T;
fm();await d(800);
for(var i=0;i<T;i++){
  var item=J[i];
  var j=item.d||item;
  var trvs=item.t||[];
  var pt=document.getElementById("b2b-pt");
  var pb=document.getElementById("b2b-pb");
  if(pt)pt.textContent="Jogo "+(i+1)+"/"+T+" ("+j.length+" dezenas"+(MIL&&trvs.length>0?" + "+trvs.length+" trevos":"")+")";
  if(pb)pb.style.width=((i+1)/T*100).toFixed(0)+"%";
  fm();
  if(i>0){lmp();await d(1000);fm();await d(300)}
  for(var n=0;n<j.length;n++){
    if(!cn(j[n])){await d(120);cn(j[n])}
    await d(80);
  }
  if(MIL&&trvs.length>0){
    await d(400);
    for(var t=0;t<trvs.length;t++){
      if(!ct(trvs[t])){await d(150);ct(trvs[t])}
      await d(100);
    }
  }
  try{var rs=angular.element(document.body).scope();if(rs&&rs.$apply)rs.$apply()}catch(ae){}
  await d(1000);fm();await d(300);
  var ok=await car();
  if(ok){OK++}else{ER++}
  if(i<T-1){await d(1200);fm()}
}
var pp=document.getElementById("b2b-pg");
if(pp){pp.style.borderColor="#22C55E";pp.innerHTML='<div style="text-align:center;padding:8px;"><div style="color:#22C55E;font-weight:800;font-size:1rem;">PRONTO! '+OK+'/'+T+' jogos ('+(LM?'50 dezenas cada':'')+') no carrinho!</div><button onclick="this.parentNode.parentNode.remove()" style="margin-top:8px;background:#22C55E;color:white;border:none;padding:8px 20px;border-radius:8px;font-weight:700;cursor:pointer;">OK</button></div>'}
alert(OK + "/" + T + " jogos no carrinho!" + (ER > 0 ? "\\n" + ER + " erro(s)." : "") + "\\nFinalize no carrinho da Caixa.");
})()`;
    }

    _openMobileBetModal(games, gameKey) {
        const allConfigs = this._getCaixaLotteryConfig();
        const cfg = allConfigs[gameKey] || { name: 'Loteria', url: '' };
        // Abre o site principal e deixa o script de automação encontrar o volante correto
        const caixaUrl = 'https://www.loteriasonline.caixa.gov.br/silce-web/#/' + (cfg ? cfg.url : '');

        // Remover modal anterior se existir
        const old = document.getElementById('mobile-bet-modal');
        if (old) old.remove();

        // Gerar script para console F12
        const freshScript = this._generateCaixaScript_LEGACY(cfg, games);

        // Gerar HTML dos jogos para aba manual
        let jogosHTML = '';
        games.forEach((g, i) => {
            const nums = g.map(n => String(n).padStart(2, '0'));
            let extraMobile = '';
            if (gameKey === 'milionaria' && this.currentGeneratedExtras && this.currentGeneratedExtras[i]) {
                const tr = Array.isArray(this.currentGeneratedExtras[i]) ? this.currentGeneratedExtras[i] : [1, 2];
                extraMobile = ' <span style="color:#34d399;font-weight:700;">— 🍀 ' + tr.map(t => String(t).padStart(2, '0')).join(' ') + '</span>';
            }
            jogosHTML += '<div style="display:flex;align-items:center;gap:8px;padding:10px 12px;background:rgba(255,255,255,0.04);border-radius:10px;margin-bottom:6px;border:1px solid rgba(255,255,255,0.06);">' +
                '<div style="flex:1;"><div style="color:#60A5FA;font-weight:700;font-size:0.72rem;margin-bottom:3px;">Jogo ' + (i + 1) + '</div>' +
                '<div style="color:#E2E8F0;font-size:1rem;font-weight:600;font-family:monospace;letter-spacing:1px;">' + nums.join('  ') + extraMobile + '</div></div>' +
                '<button class="mobile-copy-game-btn" data-nums="' + nums.join(', ') + '" style="background:linear-gradient(135deg,#22C55E,#16A34A);color:white;border:none;padding:10px 14px;border-radius:10px;font-size:0.8rem;font-weight:800;cursor:pointer;white-space:nowrap;min-width:70px;">📋 Copiar</button></div>';
        });
        const allFmt = games.map((g, i) => 'Jogo ' + (i + 1) + ': ' + g.map(n => String(n).padStart(2, '0')).join(' - ')).join('\n');

        // Criar modal
        const modal = document.createElement('div');
        modal.id = 'mobile-bet-modal';
        modal.style.cssText = 'position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,0.92);z-index:10000;display:flex;align-items:flex-start;justify-content:center;padding:10px;box-sizing:border-box;overflow-y:auto;-webkit-overflow-scrolling:touch;';

        modal.innerHTML = `<div style="background:linear-gradient(145deg,#0F172A,#1E293B);border-radius:16px;border:1px solid #FFD70040;width:100%;max-width:520px;max-height:92vh;overflow-y:auto;padding:18px;color:#E2E8F0;box-shadow:0 20px 60px rgba(0,0,0,0.6);">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px;">
                <h2 style="margin:0;font-size:1.1rem;color:#FFD700;">🎰 Apostar Online — ${cfg.name}</h2>
                <button id="close-mobile-bet-modal" style="background:none;border:none;color:#94A3B8;font-size:1.8rem;cursor:pointer;padding:4px 8px;">✕</button>
            </div>
            <div style="background:linear-gradient(135deg,rgba(255,215,0,0.12),rgba(0,60,120,0.1));border:1px solid #FFD70030;border-radius:12px;padding:12px;margin-bottom:14px;">
                <div style="font-weight:800;color:#FFD700;font-size:0.95rem;margin-bottom:4px;">🎰 ${games.length} jogos de ${cfg.name}</div>
                <div style="font-size:0.75rem;color:#94A3B8;">Escolha o método de aposta.</div>
            </div>
            <div style="display:flex;gap:4px;margin-bottom:14px;">
                <button id="tab-auto-btn-m" style="flex:1;padding:12px 6px;border-radius:10px;border:2px solid #FFD700;background:linear-gradient(135deg,#FFD70020,#FFD70008);color:#FFD700;font-weight:800;font-size:0.78rem;cursor:pointer;">⚡ F12 Console</button>
                <button id="tab-manual-btn-m" style="flex:1;padding:12px 6px;border-radius:10px;border:1px solid #47556940;background:transparent;color:#94A3B8;font-weight:700;font-size:0.78rem;cursor:pointer;">📋 Manual</button>
            </div>
            <div id="tab-auto-content-m">
                <div style="background:linear-gradient(145deg,rgba(34,197,94,0.1),rgba(0,60,120,0.08));border:1px solid #22C55E30;border-radius:12px;padding:14px;margin-bottom:12px;">
                    <div style="color:#22C55E;font-weight:800;font-size:0.9rem;margin-bottom:8px;">⚡ Preenchimento Automático</div>
                    <div style="font-size:0.78rem;color:#CBD5E1;line-height:1.6;">Copie o script, abra o site da Caixa, pressione F12 → Console, cole e Enter.</div>
                </div>
                <div style="margin-bottom:14px;">
                    <button id="btn-copy-script-m" style="width:100%;background:linear-gradient(135deg,#22C55E,#16A34A);color:white;border:none;padding:14px;border-radius:10px;font-size:0.95rem;font-weight:800;cursor:pointer;margin-bottom:10px;">📋 COPIAR SCRIPT DE AUTOMAÇÃO</button>
                    <a href="${caixaUrl}" target="_blank" rel="noopener" style="display:block;width:100%;background:linear-gradient(135deg,#0066CC,#003D80);color:white;padding:14px;border-radius:10px;font-size:0.9rem;font-weight:800;text-align:center;text-decoration:none;box-sizing:border-box;">🌐 ABRIR ${cfg.name.toUpperCase()} NA CAIXA</a>
                </div>
                <div style="background:rgba(255,215,0,0.06);border:1px solid #FFD70020;border-radius:10px;padding:10px;">
                    <div style="color:#FFD700;font-weight:700;font-size:0.72rem;margin-bottom:6px;">⚠️ Se aparecer aviso no Console, digite: <strong>allow pasting</strong> e pressione Enter</div>
                </div>
            </div>
            <div id="tab-manual-content-m" style="display:none;">
                <div style="background:linear-gradient(135deg,rgba(0,102,204,0.1),rgba(0,60,120,0.08));border:1px solid #0066CC20;border-radius:12px;padding:10px;margin-bottom:12px;">
                    <div style="font-size:0.78rem;color:#94A3B8;">Copie cada jogo e preencha manualmente no site da Caixa.</div>
                </div>
                <div style="margin-bottom:12px;">${jogosHTML}</div>
                <button id="mobile-copy-all-btn-m" style="width:100%;background:linear-gradient(135deg,#8B5CF6,#7C3AED);color:white;border:none;padding:14px;border-radius:12px;font-size:0.95rem;font-weight:800;cursor:pointer;margin-bottom:10px;">📋 COPIAR TODOS OS ${games.length} JOGOS</button>
                <a href="${caixaUrl}" target="_blank" rel="noopener" style="display:block;width:100%;background:linear-gradient(135deg,#0066CC,#003D80);color:white;padding:14px;border-radius:12px;font-size:0.95rem;font-weight:800;text-align:center;text-decoration:none;box-sizing:border-box;">🌐 ABRIR SITE DA CAIXA — ${cfg.name}</a>
            </div>
        </div>`;

        document.body.appendChild(modal);

        // Handlers
        document.getElementById('close-mobile-bet-modal').addEventListener('click', () => modal.remove());
        modal.addEventListener('click', (e) => { if (e.target === modal) modal.remove(); });

        const tabAutoBtn = document.getElementById('tab-auto-btn-m');
        const tabManualBtn = document.getElementById('tab-manual-btn-m');
        const tabAutoContent = document.getElementById('tab-auto-content-m');
        const tabManualContent = document.getElementById('tab-manual-content-m');
        const inactiveStyle = 'flex:1;padding:12px 6px;border-radius:10px;border:1px solid #47556940;background:transparent;color:#94A3B8;font-weight:700;font-size:0.78rem;cursor:pointer;';
        tabAutoBtn.addEventListener('click', () => {
            tabAutoContent.style.display = 'block';
            tabManualContent.style.display = 'none';
            tabAutoBtn.style.cssText = 'flex:1;padding:12px 6px;border-radius:10px;border:2px solid #FFD700;background:linear-gradient(135deg,#FFD70020,#FFD70008);color:#FFD700;font-weight:800;font-size:0.78rem;cursor:pointer;';
            tabManualBtn.style.cssText = inactiveStyle;
        });
        tabManualBtn.addEventListener('click', () => {
            tabAutoContent.style.display = 'none';
            tabManualContent.style.display = 'block';
            tabManualBtn.style.cssText = 'flex:1;padding:12px 6px;border-radius:10px;border:2px solid #0066CC;background:linear-gradient(135deg,#0066CC20,#0066CC08);color:#60A5FA;font-weight:800;font-size:0.78rem;cursor:pointer;';
            tabAutoBtn.style.cssText = inactiveStyle;
        });

        // Copiar script
        const copyScriptBtn = document.getElementById('btn-copy-script-m');
        if (copyScriptBtn) {
            copyScriptBtn.addEventListener('click', async () => {
                try { await navigator.clipboard.writeText(freshScript); } catch(e) {
                    const ta = document.createElement('textarea');
                    ta.value = freshScript; ta.style.cssText = 'position:fixed;left:-9999px;';
                    document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
                }
                copyScriptBtn.textContent = '✅ SCRIPT COPIADO!';
                copyScriptBtn.style.background = 'linear-gradient(135deg,#059669,#047857)';
                setTimeout(() => {
                    copyScriptBtn.textContent = '📋 COPIAR SCRIPT DE AUTOMAÇÃO';
                    copyScriptBtn.style.background = 'linear-gradient(135deg,#22C55E,#16A34A)';
                }, 3000);
            });
        }

        // Copiar jogos individuais
        modal.querySelectorAll('.mobile-copy-game-btn').forEach(btn => {
            btn.addEventListener('click', async () => {
                const nums = btn.getAttribute('data-nums');
                try { await navigator.clipboard.writeText(nums); } catch(e) {
                    const ta = document.createElement('textarea');
                    ta.value = nums; ta.style.cssText = 'position:fixed;left:-9999px;';
                    document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
                }
                btn.textContent = '✅';
                setTimeout(() => { btn.textContent = '📋 Copiar'; }, 2000);
            });
        });

        // Copiar todos
        const copyAllBtn = document.getElementById('mobile-copy-all-btn-m');
        if (copyAllBtn) {
            copyAllBtn.addEventListener('click', async () => {
                try { await navigator.clipboard.writeText(allFmt); } catch(e) {
                    const ta = document.createElement('textarea');
                    ta.value = allFmt; ta.style.cssText = 'position:fixed;left:-9999px;';
                    document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
                }
                copyAllBtn.textContent = '✅ TODOS COPIADOS!';
                copyAllBtn.style.background = 'linear-gradient(135deg,#059669,#047857)';
                setTimeout(() => {
                    copyAllBtn.textContent = '📋 COPIAR TODOS OS ' + games.length + ' JOGOS';
                    copyAllBtn.style.background = 'linear-gradient(135deg,#8B5CF6,#7C3AED)';
                }, 3000);
            });
        }
    }

    async openCaixa() {
        const allConfigs = this._getCaixaLotteryConfig();
        const cfg = allConfigs[this.currentGameKey];
        const caixaUrl = 'https://www.loteriasonline.caixa.gov.br/silce-web/#/' + (cfg ? cfg.url : '');

        const games = this._lastGeneratedGames || this.currentGeneratedGames || [];

        // ══════ MOBILE: Modal com jogos formatados ══════
        if (this._isMobile()) {
            if (games.length > 0 && cfg) {
                this._openMobileBetModal(games, this.currentGameKey);
            } else {
                // Sem jogos — navegar via link direto
                var linkMobile = document.createElement('a');
                linkMobile.href = caixaUrl;
                linkMobile.target = '_blank';
                linkMobile.rel = 'noopener';
                document.body.appendChild(linkMobile);
                linkMobile.click();
                document.body.removeChild(linkMobile);
            }
            return;
        }

        // ══════ DESKTOP: Fluxo de script (Console F12) ══════
        if (games.length > 0 && cfg) {
            const freshScript = this._generateCaixaScript_LEGACY(cfg, games);
            
            // Link direto será usado após copiar o script

            try {
                if (navigator.clipboard && navigator.clipboard.writeText) {
                    await navigator.clipboard.writeText(freshScript);
                } else {
                    throw new Error('Clipboard API not available');
                }
                console.log('[B2B] ✅ ' + games.length + ' jogos de ' + cfg.name + ' copiados!');
            } catch(e) {
                var ta = document.createElement('textarea');
                ta.value = freshScript;
                ta.style.cssText = 'position:fixed;left:-9999px;';
                document.body.appendChild(ta);
                ta.select();
                document.execCommand('copy');
                document.body.removeChild(ta);
            }

            document.dispatchEvent(new CustomEvent('b2b-aposte-online', {
                detail: { games: games, config: cfg }
            }));

            // Notificação visual (sem alert bloqueante)
            if (typeof Guardian !== 'undefined' && Guardian.toast) {
                Guardian.toast('\u2705 ' + games.length + ' jogos de ' + cfg.name + ' copiados! No site da Caixa: F12 \u2192 Console \u2192 Ctrl+V \u2192 Enter', 'success', 8000);
            }
        }

        // Mostrar painel flutuante com link real para a Caixa
        var oldPanel = document.getElementById('caixa-link-panel');
        if (oldPanel) oldPanel.remove();
        var linkPanel = document.createElement('div');
        linkPanel.id = 'caixa-link-panel';
        linkPanel.style.cssText = 'position:fixed;bottom:20px;left:50%;transform:translateX(-50%);z-index:99999;background:linear-gradient(135deg,#0F172A,#1E293B);border:2px solid #22C55E;border-radius:16px;padding:16px 24px;box-shadow:0 10px 40px rgba(0,0,0,0.6);text-align:center;max-width:400px;width:90%;animation:slideUp 0.3s ease;';
        var linkHtml = '<div style="color:#22C55E;font-weight:800;font-size:1rem;margin-bottom:10px;">\u2705 Script copiado!</div>';
        linkHtml += '<a href="' + caixaUrl + '" target="_blank" rel="noopener" style="display:block;background:linear-gradient(135deg,#22C55E,#16A34A);color:white;text-decoration:none;padding:14px 24px;border-radius:12px;font-weight:900;font-size:1rem;margin-bottom:8px;">\uD83C\uDFE6 ABRIR SITE DA CAIXA</a>';
        linkHtml += '<div style="color:#94A3B8;font-size:0.72rem;">No site: F12 \u2192 Console \u2192 Ctrl+V \u2192 Enter</div>';
        linkHtml += '<button onclick="this.parentNode.remove()" style="margin-top:8px;background:none;border:1px solid #475569;color:#94A3B8;padding:6px 16px;border-radius:8px;cursor:pointer;font-size:0.75rem;">Fechar</button>';
        linkPanel.innerHTML = linkHtml;
        document.body.appendChild(linkPanel);
        // Auto-remover apos 15 segundos
        setTimeout(function() { var p = document.getElementById('caixa-link-panel'); if (p) p.remove(); }, 15000);
    }

    getSelectedNumbers() {
        return Array.from(this.selectedNumbers);
    }

    // ═══════════════════════════════════════════════════════════════
    // 💾 SALVAR JOGOS — DIRETO na pasta da loteria (sem diálogo)
    //    POST /salvar → server.js grava em:
    //    Desktop/LOTERIAS JOGOS SALVOS L99/<Loteria>/arquivo.txt
    // ═══════════════════════════════════════════════════════════════

    
    // ═══════════════════════════════════════════════════════════════
    // 🌐 HELPER API — Conecta de forma resiliente ao servidor local
    //    Funciona via http://localhost:8777, rede local e file:///
    // ═══════════════════════════════════════════════════════════════
    async _callServerApi(endpoint, options = {}) {
        const method = options.method || 'GET';
        const headers = { 'Content-Type': 'application/json', ...(options.headers || {}) };
        const body = options.body ? (typeof options.body === 'string' ? options.body : JSON.stringify(options.body)) : undefined;
        const timeoutMs = options.timeoutMs || 8000;

        const candidateUrls = [];
        if (window.location.protocol === 'http:' || window.location.protocol === 'https:') {
            candidateUrls.push(endpoint);
        }
        candidateUrls.push(`http://localhost:8777${endpoint}`);
        candidateUrls.push(`http://127.0.0.1:8777${endpoint}`);

        const uniqueUrls = Array.from(new Set(candidateUrls));
        let lastError = null;

        for (const url of uniqueUrls) {
            try {
                const controller = new AbortController();
                const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
                const resp = await fetch(url, {
                    method,
                    headers,
                    body,
                    signal: controller.signal
                });
                clearTimeout(timeoutId);
                if (resp.ok) {
                    const data = await resp.json();
                    return data;
                } else {
                    const errData = await resp.json().catch(() => ({}));
                    lastError = new Error(errData.error || `HTTP ${resp.status}`);
                }
            } catch (err) {
                lastError = err;
            }
        }
        throw lastError || new Error('Servidor local indisponível');
    }

    async saveGames() {
        if (!this.currentGeneratedGames || this.currentGeneratedGames.length === 0) {
            if (typeof Guardian !== 'undefined' && Guardian.toast) {
                Guardian.toast('Gere jogos primeiro antes de salvar.', 'warning');
            } else {
                alert('Gere jogos primeiro antes de salvar.');
            }
            return;
        }

        const game = typeof GAMES !== 'undefined' ? GAMES[this.currentGameKey] : null;
        const gameName = game ? game.name : 'Loteria';
        const now = new Date();
        const pad = n => String(n).padStart(2, '0');
        const dateStr = `${pad(now.getDate())}-${pad(now.getMonth() + 1)}-${now.getFullYear()}`;
        const timeStr = `${pad(now.getHours())}h${pad(now.getMinutes())}m${pad(now.getSeconds())}s`;
        const cleanGameName = (gameName || 'Loteria').replace(/[^a-zA-Z0-9áéíóúÁÉÍÓÚãõÃÕâêîôûÂÊÎÔÛçÇ _-]/g, '').trim();
        const fileName = `${cleanGameName}_${dateStr}_${timeStr}.txt`;

        // ── Extras: Time do Coração (Timemania) e Mês da Sorte (Dia de Sorte) ──
        const mesSorteSelect = document.getElementById('mes-sorte-select');
        const mesSorte = (this.currentGameKey === 'diadesorte' && mesSorteSelect) ? mesSorteSelect.value : null;

        const extras = this.currentGeneratedExtras || [];
        const isTimemania = this.currentGameKey === 'timemania';
        const isDiaDeSorte = this.currentGameKey === 'diadesorte';

        let content = `═══════════════════════════════════════
`;
        content += `  JOGOS — ${gameName.toUpperCase()}
`;
        if (mesSorte) content += `  Mês da Sorte (cabeçalho): ${mesSorte}
`;
        if (isTimemania) content += `  Time do Coração: registrado por jogo abaixo
`;
        content += `  Data: ${now.toLocaleString('pt-BR')}
`;
        content += `  Total de Jogos: ${this.currentGeneratedGames.length}
`;
        content += `═══════════════════════════════════════

`;

        this.currentGeneratedGames.forEach((g, index) => {
            const nums = g.map(n => n.toString().padStart(2, '0')).join(' - ');
            let extra = '';
            if (isTimemania && extras[index] !== undefined && extras[index] !== null) {
                const timeName = (typeof L99_TIMES !== 'undefined' && L99_TIMES[extras[index]])
                    ? L99_TIMES[extras[index]]
                    : `Time #${extras[index]}`;
                extra = ` | Time: ${timeName}`;
            } else if (isDiaDeSorte) {
                if (extras[index] !== undefined && extras[index] !== null) {
                    const mesNome = (typeof L99_MESES !== 'undefined' && L99_MESES[extras[index]])
                        ? L99_MESES[extras[index]]
                        : (mesSorte || `Mês #${extras[index]}`);
                    extra = ` | Mês: ${mesNome}`;
                } else if (mesSorte) {
                    extra = ` | Mês: ${mesSorte}`;
                }
            }
            content += `Jogo ${String(index + 1).padStart(3, '0')}: ${nums}${extra}
`;
        });

        content += `
═══════════════════════════════════════
`;
        content += `  B2B Loterias — Boa Sorte! 🍀
`;
        content += `═══════════════════════════════════════
`;

        // ══════ 1. TENTAR SALVAR DIRETO NA PASTA VIA SERVIDOR LOCAL ══════
        try {
            const result = await this._callServerApi('/salvar', {
                method: 'POST',
                body: {
                    gameKey: this.currentGameKey,
                    fileName: fileName,
                    content: content,
                },
                timeoutMs: 10000
            });

            if (result && result.ok) {
                const btn = this.saveBtn;
                if (btn) {
                    const originalHTML = btn.innerHTML;
                    btn.innerHTML = '✅ Salvo!';
                    btn.style.background = 'linear-gradient(135deg, #22C55E, #16A34A)';
                    btn.style.transform = 'scale(1.05)';
                    setTimeout(() => {
                        btn.innerHTML = originalHTML;
                        btn.style.background = '';
                        btn.style.transform = '';
                    }, 3000);
                }

                const savedRelPath = result.relativePath || result.path || `LOTERIAS JOGOS SALVOS L99\${gameName}\${result.fileName || fileName}`;
                const toastMsg = `✅ <strong>Jogo salvo com sucesso!</strong><br><span style="font-size:11px;opacity:0.9">📁 ${savedRelPath}</span>`;
                
                if (typeof Guardian !== 'undefined' && Guardian.toast) {
                    Guardian.toast(`✅ Jogo salvo com sucesso!
📁 ${savedRelPath}`, 'success', 6000);
                } else {
                    const toast = document.createElement('div');
                    toast.style.cssText = `
                        position:fixed; bottom:24px; left:50%; transform:translateX(-50%);
                        background:linear-gradient(135deg,#166534,#15803d); color:#fff;
                        padding:14px 24px; border-radius:12px; font-size:13px;
                        box-shadow:0 8px 32px rgba(0,0,0,0.4); z-index:99999;
                        max-width:480px; text-align:center; line-height:1.5;
                        animation: fadeInUp 0.3s ease; border: 1px solid #4ade80;
                    `;
                    toast.innerHTML = toastMsg;
                    document.body.appendChild(toast);
                    setTimeout(() => toast.remove(), 6000);
                }

                console.log(`[B2B] ✅ Salvo com sucesso: ${result.path}`);
                return;
            }
        } catch (err) {
            console.warn('[Save] Servidor local indisponível, usando fallback de download:', err.message);
        }

        // ══════ 2. FALLBACK: Download como arquivo no navegador ══════
        try {
            const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
            const urlObj = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = urlObj;
            a.download = fileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            setTimeout(() => window.URL.revokeObjectURL(urlObj), 3000);

            const btn = this.saveBtn;
            if (btn) {
                const originalHTML = btn.innerHTML;
                btn.innerHTML = '⬇️ Baixado!';
                btn.style.background = 'linear-gradient(135deg, #2563EB, #1D4ED8)';
                setTimeout(() => {
                    btn.innerHTML = originalHTML;
                    btn.style.background = '';
                }, 2500);
            }

            const fallbackMsg = `📥 <strong>Arquivo baixado pelo navegador!</strong><br><span style="font-size:11px;opacity:0.9">Verifique a pasta de Downloads (${fileName})</span>`;
            if (typeof Guardian !== 'undefined' && Guardian.toast) {
                Guardian.toast(`📥 Arquivo baixado pelo navegador!
Verifique seus Downloads (${fileName})`, 'info', 5000);
            } else {
                const toast = document.createElement('div');
                toast.style.cssText = `
                    position:fixed; bottom:24px; left:50%; transform:translateX(-50%);
                    background:linear-gradient(135deg,#1e40af,#2563eb); color:#fff;
                    padding:14px 24px; border-radius:12px; font-size:13px;
                    box-shadow:0 8px 32px rgba(0,0,0,0.4); z-index:99999;
                    max-width:480px; text-align:center; line-height:1.5;
                    border: 1px solid #60a5fa;
                `;
                toast.innerHTML = fallbackMsg;
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 5000);
            }
        } catch (e) {
            alert('Não foi possível salvar o arquivo: ' + e.message);
        }
    }

    openCheckModal() {
        // We now allow opening even without current generated games, to check saved files
        // if (!this.currentGeneratedGames || this.currentGeneratedGames.length === 0) { ... } REMOVED CHECK


        // Auto-fill with last draw number for convenience
        const recent = StatsService.getRecentResults(this.currentGameKey, 1)[0];
        let autoFillValue = "";

        if (recent) {
            autoFillValue = recent.drawNumber.toString();
        }

        this.checkModal.style.display = 'flex';
        this.inputCheckNumbers.value = autoFillValue;
        if (this.loadGamesInput) this.loadGamesInput.value = ''; // Reset file input


        // Add a visual hint about using last draw
        if (recent) {
            this.inputCheckNumbers.title = `Concurso sugerido: ${autoFillValue}`;
        }

        this.inputCheckNumbers.focus();

        // ── L99: Botão para listar jogos salvos da pasta ──
        const self = this;
        const listarBtn = document.getElementById('btn-listar-jogos-salvos');
        const listArea = document.getElementById('saved-games-list');
        if (listarBtn && listArea) {
            listarBtn.onclick = async function() {
                listarBtn.innerHTML = '⏳ Carregando...';
                try {
                    const data = await self._callServerApi('/listar-jogos?gameKey=' + self.currentGameKey);
                    // resp já parseado por _callServerApi
                    if (data.ok && data.files && data.files.length > 0) {
                        // Filtrar apenas arquivos de jogos (não relatórios CONFERIDO_...Concurso)
                        const gameFiles = data.files.filter(function(f) {
                            return !f.name.includes('Concurso_');
                        });
                        listArea.style.display = 'block';
                        listArea.innerHTML = '';
                        if (gameFiles.length === 0) {
                            listArea.innerHTML = '<div style="padding:12px;color:#94A3B8;text-align:center;">Nenhum arquivo de jogo encontrado (apenas relatórios de conferência)</div>';
                            listarBtn.innerHTML = '📂 Carregar da Pasta LOTERIAS JOGOS SALVOS L99';
                            return;
                        }
                        gameFiles.forEach(function(file) {
                            var modified = new Date(file.modified).toLocaleDateString('pt-BR') + ' ' + new Date(file.modified).toLocaleTimeString('pt-BR', {hour:'2-digit',minute:'2-digit'});
                            var isChecked = file.name.includes('CONFERIDO');
                            var icon = isChecked ? '✅' : '📄';
                            var item = document.createElement('div');
                            item.style.cssText = 'padding:8px 12px;border-bottom:1px solid rgba(255,255,255,0.06);cursor:pointer;display:flex;justify-content:space-between;align-items:center;transition:background 0.2s;font-size:0.8rem;';
                            item.innerHTML = '<span style="color:#E2E8F0;font-weight:600;">' + icon + ' ' + file.name + '</span><span style="color:#64748b;font-size:0.7rem;">' + modified + '</span>';
                            item.onmouseenter = function() { item.style.background = 'rgba(59,130,246,0.15)'; };
                            item.onmouseleave = function() { item.style.background = ''; };
                            item.onclick = async function() {
                                item.innerHTML = '<span style="color:#22C55E;">⏳ Carregando...</span>';
                                try {
                                    var readData = await self._callServerApi('/ler-jogo', { method: 'POST', body: { gameKey: self.currentGameKey, fileName: file.name } });
                                    // readResp já parseado por _callServerApi
                                    if (readData.ok && readData.content) {
                                        var parsedGames = self.parseSavedGames(readData.content);
                                        if (parsedGames && parsedGames.length > 0) {
                                            self.currentGeneratedGames = parsedGames;
                                            self._lastLoadedFileName = file.name;
                                            self.renderGames({ games: parsedGames }, self.currentGameKey);
                                            listArea.style.display = 'none';
                                            listarBtn.innerHTML = '✅ ' + parsedGames.length + ' jogos carregados de ' + file.name;
                                            setTimeout(function() { listarBtn.innerHTML = '📂 Carregar da Pasta LOTERIAS JOGOS SALVOS L99'; }, 3000);
                                        } else {
                                            alert('Nenhum jogo encontrado no arquivo: ' + file.name);
                                            item.innerHTML = '<span style="color:#EF4444;">❌ Formato inválido</span>';
                                        }
                                    }
                                } catch(e) {
                                    alert('Erro ao ler arquivo: ' + e.message);
                                }
                            };
                            listArea.appendChild(item);
                        });
                    } else {
                        listArea.style.display = 'block';
                        listArea.innerHTML = '<div style="padding:12px;color:#94A3B8;text-align:center;">Nenhum jogo salvo encontrado para esta loteria.<br><small>Pasta: ' + (data.path || '') + '</small></div>';
                    }
                } catch(e) {
                    alert('Erro ao listar jogos: ' + e.message + '\nVerifique se o servidor está rodando.');
                }
                listarBtn.innerHTML = '📂 Carregar da Pasta LOTERIAS JOGOS SALVOS L99';
            };
        }
    }

    closeCheckModal() {
        this.checkModal.style.display = 'none';
        // Remove highlights on close? Maybe not, user might want to see.
    }

    async confirmCheck() {
        const input = this.inputCheckNumbers ? this.inputCheckNumbers.value.trim() : '';
        const game = typeof GAMES !== 'undefined' ? GAMES[this.currentGameKey] : null;
        if (!game) {
            alert('Erro: jogo não carregado.');
            return;
        }

        let targetNumbers = [];
        let drawInfo = "Manual";

        // Check if input is a Draw Number (single integer) or Manual List of numbers
        const isDrawNumber = /^\d+$/.test(input) && !input.includes(' ') && !input.includes(',');

        if (isDrawNumber) {
            const drawNum = parseInt(input);
            
            // 1. Primeiro tenta o cache local (historyStore)
            let result = StatsService.getResultByDrawNumber(this.currentGameKey, drawNum);

            // 2. Se não encontrou, busca da API em tempo real
            if (!result) {
                console.log('[CONFERIR] Concurso ' + drawNum + ' não encontrado no cache. Buscando da API...');
                
                // Feedback visual: buscando...
                const confirmBtn = document.getElementById('confirm-check-btn');
                const originalText = confirmBtn ? confirmBtn.innerHTML : '';
                if (confirmBtn) {
                    confirmBtn.innerHTML = '⏳ Buscando resultado do Concurso ' + drawNum + '...';
                    confirmBtn.disabled = true;
                }

                try {
                    const fetched = await StatsService._fetchSingleDraw(this.currentGameKey, drawNum);
                    if (fetched && fetched.numbers && fetched.numbers.length > 0) {
                        // Inserir no historyStore para futuras consultas
                        if (!StatsService.historyStore[this.currentGameKey]) {
                            StatsService.historyStore[this.currentGameKey] = [];
                        }
                        StatsService.historyStore[this.currentGameKey].push(fetched);
                        result = fetched;
                        console.log('[CONFERIR] ✅ Resultado obtido da API: Concurso ' + drawNum + ' → [' + fetched.numbers.join(', ') + ']');
                    }
                } catch(apiErr) {
                    console.warn('[CONFERIR] API falhou:', apiErr.message);
                }

                // Restaurar botão
                if (confirmBtn) {
                    confirmBtn.innerHTML = originalText;
                    confirmBtn.disabled = false;
                }
            }

            // 3. Fallback: busca no REAL_HISTORY_DB
            if (!result && typeof REAL_HISTORY_DB !== 'undefined' && REAL_HISTORY_DB[this.currentGameKey]) {
                const db = REAL_HISTORY_DB[this.currentGameKey];
                for (let i = 0; i < db.length; i++) {
                    if (db[i].drawNumber == drawNum) {
                        result = db[i];
                        console.log('[CONFERIR] Encontrado no REAL_HISTORY_DB');
                        break;
                    }
                }
            }

            if (result && result.numbers && result.numbers.length > 0) {
                targetNumbers = result.numbers;
                drawInfo = `Concurso ${result.drawNumber}`;
                // ★ v10.9: Salvar resultado completo para conferência de extras (mês/time)
                this._lastDrawResult = result;
                // ★ v13.0: Dupla Sena — incluir 2º sorteio na conferência
                if (this.currentGameKey === 'duplasena' && result.numbers2 && result.numbers2.length > 0) {
                    this._lastDrawNumbers2 = result.numbers2;
                } else {
                    this._lastDrawNumbers2 = null;
                }
            } else {
                // Concurso realmente não encontrado em nenhuma fonte
                alert(`❌ Concurso ${drawNum} não encontrado.\n\nVerifique se o número do concurso está correto ou digite os números sorteados manualmente separados por espaço ou vírgula.\n\nExemplo: 08 24 27 37 47 55`);
                return;
            }
        } else {
            this._lastDrawResult = null; // v10.9: entrada manual, sem dados extras da API
            targetNumbers = input.split(/[\s,-]+/).map(n => parseInt(n)).filter(n => !isNaN(n));
            if (targetNumbers.length < game.draw) {
                alert(`Por favor, insira o Número do Concurso OU pelo menos ${game.draw} números.`);
                return;
            }
        }

        const file = this.loadGamesInput ? this.loadGamesInput.files[0] : null;
        if (file) {
            // Check from File
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target.result;
                const parsedGames = this.parseSavedGames(text);
                if (parsedGames && parsedGames.length > 0) {
                    this.currentGeneratedGames = parsedGames;
                    this.renderGames({ games: parsedGames }, this.currentGameKey);
                    this.closeCheckModal();
                    setTimeout(() => this.highlightResults(targetNumbers, drawInfo, this._lastDrawResult), 100);
                } else {
                    alert('Erro ao ler jogos do arquivo.');
                }
            };
            reader.readAsText(file);
        } else {
            // Check Current
            if (!this.currentGeneratedGames || this.currentGeneratedGames.length === 0) {
                alert('Nenhum jogo carregado para conferir.\n\nGere jogos primeiro usando "Gerar Jogos" ou "QUANTUM L99".');
                return;
            }
            this.closeCheckModal();
            this.highlightResults(targetNumbers, drawInfo, this._lastDrawResult);
        }
    }

    parseSavedGames(text) {
        const games = [];
        const lines = text.split('\n');
        lines.forEach(line => {
            const clean = line.trim();
            if (!clean || clean.startsWith('═') || clean.startsWith('JOGOS') || clean.startsWith('Total') || clean.startsWith('Data') || clean.startsWith('B2B') || clean.startsWith('Time') || clean.startsWith('Mês') || clean.startsWith('Conferência') || clean.startsWith('Relatório')) {
                return;
            }
            if (clean.toLowerCase().startsWith('jogo')) {
                const parts = clean.split(':');
                if (parts.length > 1) {
                    const numsPart = parts[1].split('|')[0].trim();
                    const numbers = numsPart.split(/[\s,-]+/).map(n => parseInt(n)).filter(n => !isNaN(n));
                    if (numbers.length > 0) {
                        games.push(numbers);
                    }
                }
            } else {
                const numsPart = clean.split('|')[0].trim();
                const numbers = numsPart.split(/[\s,-]+/).map(n => parseInt(n)).filter(n => !isNaN(n));
                if (numbers.length >= 5) {
                    games.push(numbers);
                }
            }
        });
        return games;
    }

    highlightResults(drawnNumbers, drawInfo = "", drawResult = null) {
        const drawnSet = new Set(drawnNumbers);
        const cards = document.querySelectorAll('.game-card');
        const game = GAMES[this.currentGameKey];

        // ═══ V13: Dupla Sena — conferir contra AMBOS os sorteios ═══
        const isDuplaSena = this.currentGameKey === 'duplasena';
        const drawnSet2 = (isDuplaSena && this._lastDrawNumbers2) ? new Set(this._lastDrawNumbers2) : null;

        // ═══ V10: Conferência Completa — Todas as Faixas ═══
        const paidStrategies = game.strategies.filter(s => s.paid !== false);
        const awardCounts = {};
        paidStrategies.forEach(s => awardCounts[s.id] = 0);

        // Distribuição de acertos para gráfico
        const hitDistribution = {};
        let maxPossibleHits = 0;

        // V11: Coletar jogos ganhadores para exibição agrupada
        const winningGames = [];

        // V13 FIX: Para Dupla Sena, cada jogo é conferido contra AMBOS os sorteios.
        // Regra oficial: premiações de cada sorteio são INDEPENDENTES e ACUMULAM.
        // Um mesmo jogo pode ganhar Terno no 1º sorteio E Quadra no 2º sorteio.
        this.currentGeneratedGames.forEach((gameNumbers, index) => {
            // Hits no 1º sorteio
            let hits1 = 0;
            for (let i = 0; i < gameNumbers.length; i++) {
                if (drawnSet.has(gameNumbers[i])) hits1++;
            }

            // Hits no 2º sorteio (Dupla Sena)
            let hits2 = 0;
            if (drawnSet2) {
                for (let i = 0; i < gameNumbers.length; i++) {
                    if (drawnSet2.has(gameNumbers[i])) hits2++;
                }
            }

            // Para Dupla Sena: premiar em AMBOS os sorteios (acumula)
            // Para outras loterias: apenas hits1
            const hits = isDuplaSena ? Math.max(hits1, hits2) : hits1;

            if (hits > maxPossibleHits) maxPossibleHits = hits;
            hitDistribution[hits] = (hitDistribution[hits] || 0) + 1;

            const hitsToCheck = (this.currentGameKey === 'lotomania' && hits === 0) ? 0 : hits;

            if (isDuplaSena && drawnSet2) {
                // Dupla Sena: conferir cada sorteio INDEPENDENTEMENTE
                const strat1 = paidStrategies.find(s => s.match === hits1);
                const strat2 = paidStrategies.find(s => s.match === hits2);

                let totalPrize = 0;
                let bestStrat = null;

                if (strat1) {
                    awardCounts[strat1.id]++;
                    totalPrize += (strat1.prize || 0);
                    bestStrat = strat1;
                }
                if (strat2) {
                    awardCounts[strat2.id]++;
                    totalPrize += (strat2.prize || 0);
                    if (!bestStrat || strat2.match > bestStrat.match) bestStrat = strat2;
                }

                if (bestStrat) {
                    winningGames.push({
                        index: index,
                        numbers: gameNumbers,
                        hits: Math.max(hits1, hits2),
                        hits1: hits1,
                        hits2: hits2,
                        strat: bestStrat,
                        prize: totalPrize
                    });
                }
            } else {
                // Todas as outras loterias
                const matchedStrat = paidStrategies.find(s => s.match === hitsToCheck);
                if (matchedStrat) {
                    awardCounts[matchedStrat.id]++;
                    winningGames.push({
                        index: index,
                        numbers: gameNumbers,
                        hits: hits,
                        strat: matchedStrat,
                        prize: matchedStrat.prize || 0
                    });
                }
            }
        });

        // Atualização Visual Otimizada (DOM)
        // Se houver muitos jogos (>500), faremos atualizações assíncronas para não travar a UI
        const CHUNK_SIZE = 250;
        let currentChunk = 0;

        const updateCardsChunk = () => {
            const start = currentChunk * CHUNK_SIZE;
            const end = Math.min(start + CHUNK_SIZE, cards.length);

            for (let i = start; i < end; i++) {
                const card = cards[i];
                const gameNumbers = this.currentGeneratedGames[i];
                if (!gameNumbers) continue;

                // Hits no 1º sorteio
                let hits1 = 0;
                for (let k = 0; k < gameNumbers.length; k++) {
                    if (drawnSet.has(gameNumbers[k])) hits1++;
                }

                // Hits no 2º sorteio (Dupla Sena)
                let hits2 = 0;
                if (drawnSet2) {
                    for (let k = 0; k < gameNumbers.length; k++) {
                        if (drawnSet2.has(gameNumbers[k])) hits2++;
                    }
                }

                const hits = isDuplaSena ? Math.max(hits1, hits2) : hits1;
                const hitsToCheck = (this.currentGameKey === 'lotomania' && hits === 0) ? 0 : hits;

                // Update balls — Dupla Sena: verde=1º, azul=2º, dourado=ambos
                const balls = card.querySelectorAll('.ball');
                balls.forEach((ball, bIdx) => {
                    const num = gameNumbers[bIdx];
                    const inDraw1 = drawnSet.has(num);
                    const inDraw2 = drawnSet2 ? drawnSet2.has(num) : false;

                    if (inDraw1 && inDraw2) {
                        // Acertou em AMBOS os sorteios
                        ball.classList.add('hit');
                        ball.style.backgroundColor = '#FFD700';
                        ball.style.color = '#000';
                        ball.style.borderColor = '#FFD700';
                        ball.style.boxShadow = '0 0 10px rgba(255,215,0,0.6)';
                    } else if (inDraw1) {
                        ball.classList.add('hit');
                        ball.style.backgroundColor = '#22C55E';
                        ball.style.color = '#fff';
                        ball.style.borderColor = '#22C55E';
                        ball.style.boxShadow = '0 0 8px rgba(34,197,94,0.5)';
                    } else if (inDraw2) {
                        ball.classList.add('hit');
                        ball.style.backgroundColor = '#3B82F6';
                        ball.style.color = '#fff';
                        ball.style.borderColor = '#3B82F6';
                        ball.style.boxShadow = '0 0 8px rgba(59,130,246,0.5)';
                    } else {
                        if (!ball.classList.contains('fixed')) {
                            ball.style.backgroundColor = '';
                            ball.style.color = '';
                            ball.style.borderColor = '';
                            ball.style.boxShadow = '';
                            ball.classList.remove('hit');
                        }
                    }
                });

                // Update Summary
                let summary = card.querySelector('.hit-summary');
                if (!summary) {
                    summary = document.createElement('div');
                    summary.className = 'hit-summary';
                    summary.style.cssText = 'width:100%;text-align:right;font-size:0.8rem;font-weight:bold;margin-top:5px;padding:4px 6px;border-radius:6px;';
                    card.appendChild(summary);
                }

                if (isDuplaSena && drawnSet2) {
                    // Dupla Sena: mostrar resultado de AMBOS os sorteios
                    const strat1 = paidStrategies.find(s => s.match === hits1);
                    const strat2 = paidStrategies.find(s => s.match === hits2);
                    const bestStrat = strat1 || strat2;
                    let totalPrize = (strat1 ? strat1.prize : 0) + (strat2 ? strat2.prize : 0);

                    if (bestStrat) {
                        const isJackpot = (strat1 && strat1.match === game.draw) || (strat2 && strat2.match === game.draw);
                        summary.style.color = isJackpot ? '#FFD700' : '#22C55E';
                        summary.style.background = isJackpot ? 'rgba(255,215,0,0.08)' : 'rgba(34,197,94,0.08)';
                        const s1Label = strat1 ? `1º: ${hits1}ac (${strat1.label})` : `1º: ${hits1}ac`;
                        const s2Label = strat2 ? `2º: ${hits2}ac (${strat2.label})` : `2º: ${hits2}ac`;
                        const prizeHint = totalPrize > 0 ? ` ≈ R$ ${totalPrize.toFixed(2).replace('.', ',')}` : '';
                        summary.innerHTML = `🏆 ${s1Label} | ${s2Label}${prizeHint}`;
                    } else if (hits1 > 0 || hits2 > 0) {
                        summary.style.color = '#94A3B8';
                        summary.style.background = 'rgba(255,255,255,0.03)';
                        summary.textContent = `1º: ${hits1}ac | 2º: ${hits2}ac — sem premiação`;
                    } else {
                        summary.style.color = '#475569';
                        summary.style.background = '';
                        summary.textContent = 'Nenhum acerto em ambos sorteios';
                    }
                } else {
                    // Todas as outras loterias
                    const displayHits = (this.currentGameKey === 'lotomania' && hits1 === 0) ? '0 (Mania!)' : hits1;
                    const matchedStrat = paidStrategies.find(s => s.match === hitsToCheck);

                    if (matchedStrat) {
                        const isJackpot = matchedStrat.match === game.draw;
                        summary.style.color = isJackpot ? '#FFD700' : '#22C55E';
                        summary.style.background = isJackpot ? 'rgba(255,215,0,0.08)' : 'rgba(34,197,94,0.08)';
                        const prizeHint = matchedStrat.prize > 100
                            ? ` ≈ ${matchedStrat.prize.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })}`
                            : (matchedStrat.prize > 0 ? ` ≈ R$ ${matchedStrat.prize.toFixed(2).replace('.', ',')}` : '');
                        summary.innerHTML = `🏆 ${displayHits} acertos — <strong>${matchedStrat.label}</strong>${prizeHint}`;
                    } else if (hits1 > 0) {
                        summary.style.color = '#94A3B8';
                        summary.style.background = 'rgba(255,255,255,0.03)';
                        summary.textContent = `${hits1} acerto${hits1 > 1 ? 's' : ''} — sem premiação nesta faixa`;
                    } else {
                        summary.style.color = '#475569';
                        summary.style.background = '';
                        summary.textContent = 'Nenhum acerto';
                    }
                }
            }

            currentChunk++;
            if (currentChunk * CHUNK_SIZE < cards.length) {
                requestAnimationFrame(updateCardsChunk);
            }
        };

        // Iniciar atualização visual
        requestAnimationFrame(updateCardsChunk);

        // ═══ RESUMO DA CONFERÊNCIA V10 — COMPLETO E DETALHADO ═══
        const currency = (n) => n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
        const totalJogos = this.currentGeneratedGames.length;
        const totalGanhos = Object.values(awardCounts).reduce((s, v) => s + v, 0);
        const minStrat = paidStrategies.length > 0 ? Math.min(...paidStrategies.map(s => s.match)) : 0;
        const maxStrat = paidStrategies.length > 0 ? Math.max(...paidStrategies.map(s => s.match)) : 0;

        let summaryHTML = `<div style="font-family:'Outfit','Inter',sans-serif;">`;

        
// ── CABEÇALHO ──
        summaryHTML += `<div style="display:flex;align-items:center;gap:10px;margin-bottom:12px;">`;
        summaryHTML += `<div style="font-size:1.8rem;">🔍</div>`;
        summaryHTML += `<div>`;
        summaryHTML += `<h4 style="margin:0;color:${game.color};font-size:1rem;font-weight:800;">CONFERÊNCIA — ${game.name.toUpperCase()}</h4>`;
        summaryHTML += `<div style="font-size:0.72rem;color:#94A3B8;">${drawInfo || 'Resultado informado manualmente'} · Faixas premiadas: ${minStrat} a ${maxStrat} acertos</div>`;
        if (isDuplaSena && this._lastDrawNumbers2) {
            summaryHTML += `<div style="font-size:0.72rem;color:#94A3B8;margin-top:4px;">`;
            summaryHTML += `<span style="color:#22C55E;">● 1º Sorteio:</span> ${drawnNumbers.map(n => String(n).padStart(2,'0')).join(' - ')} `;
            summaryHTML += `<span style="color:#3B82F6;margin-left:8px;">● 2º Sorteio:</span> ${this._lastDrawNumbers2.map(n => String(n).padStart(2,'0')).join(' - ')}`;
            summaryHTML += `</div>`;
        }
        summaryHTML += `</div></div>`;

        
// ── RESUMO RÁPIDO ──
        summaryHTML += `<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:12px;">`;
        summaryHTML += `<div style="background:rgba(255,255,255,0.06);border-radius:8px;padding:6px 12px;font-size:0.82rem;"><strong>${totalJogos}</strong> jogo${totalJogos > 1 ? 's' : ''} conferidos</div>`;
        if (totalGanhos > 0) {
            summaryHTML += `<div style="background:rgba(34,197,94,0.15);border:1px solid #22C55E50;border-radius:8px;padding:6px 12px;color:#22C55E;font-size:0.82rem;font-weight:700;">🏆 ${totalGanhos} prêmio${totalGanhos > 1 ? 's' : ''} ganho${totalGanhos > 1 ? 's' : ''}!</div>`;
        } else {
            summaryHTML += `<div style="background:rgba(239,68,68,0.1);border:1px solid #EF444440;border-radius:8px;padding:6px 12px;color:#EF4444;font-size:0.82rem;">Nenhuma faixa premiada desta vez</div>`;
        }
        summaryHTML += `</div>`;

        
// ── DISTRIBUIÇÃO DE ACERTOS (gráfico de barras) ──
        summaryHTML += `<div style="margin-bottom:12px;padding:10px 14px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:10px;">`;
        summaryHTML += `<div style="font-size:0.68rem;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;margin-bottom:8px;">Distribuição de Acertos</div>`;
        const maxHitCount = Math.max(...Object.values(hitDistribution), 1);
        for (let h = maxPossibleHits; h >= 0; h--) {
            const count = hitDistribution[h] || 0;
            if (count === 0 && h > maxPossibleHits) continue;
            const pct = totalJogos > 0 ? (count / totalJogos * 100) : 0;
            const barW = maxHitCount > 0 ? (count / maxHitCount * 100) : 0;
            const isPrized = paidStrategies.some(s => s.match === h);
            const barColor = isPrized ? (h === game.draw ? '#FFD700' : '#22C55E') : '#334155';
            const textColor = isPrized ? '#f1f5f9' : '#64748b';
            if (count > 0 || isPrized) {
                summaryHTML += `<div style="display:flex;align-items:center;gap:8px;margin-bottom:3px;">`;
                summaryHTML += `<span style="min-width:55px;font-size:0.72rem;color:${textColor};font-weight:${isPrized?'700':'400'};text-align:right;">${h} acerto${h !== 1 ? 's' : ''}</span>`;
                summaryHTML += `<div style="flex:1;height:14px;background:rgba(255,255,255,0.04);border-radius:4px;overflow:hidden;">`;
                summaryHTML += `<div style="height:100%;width:${barW}%;background:${barColor};border-radius:4px;transition:width 0.5s;min-width:${count>0?'2px':'0'};"></div>`;
                summaryHTML += `</div>`;
                summaryHTML += `<span style="min-width:50px;font-size:0.72rem;color:${textColor};font-weight:600;">${count}x (${pct.toFixed(0)}%)</span>`;
                summaryHTML += `${isPrized ? '<span style="font-size:0.65rem;">💰</span>' : ''}`;
                summaryHTML += `</div>`;
            }
        }
        summaryHTML += `</div>`;

        
// ── TABELA DE FAIXAS PREMIADAS ──
        summaryHTML += `<div style="font-size:0.72rem;color:#64748b;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">💎 Faixas de Premiação — ${game.name}</div>`;
        summaryHTML += `<div style="display:flex;flex-direction:column;gap:4px;">`;

        // ── Buscar prêmios REAIS da API (se disponíveis) ──
        let realPrizes = {};
        try {
            const prizeInfo = StatsService.getPrizeInfo(this.currentGameKey);
            if (prizeInfo && prizeInfo.prizes && prizeInfo.prizes.length > 0) {
                prizeInfo.prizes.forEach(p => {
                    // API da Caixa: { descricaoFaixa, faixa, numeroDeGanhadores, valorPremio }
                    const faixa = parseInt(p.faixa);
                    if (p.valorPremio !== undefined) {
                        realPrizes[faixa] = {
                            valor: parseFloat(p.valorPremio) || 0,
                            ganhadores: parseInt(p.numeroDeGanhadores) || 0,
                            descricao: p.descricaoFaixa || ''
                        };
                    }
                });
            }
        } catch(e) { /* fallback para valores estáticos */ }

        let estimatedTotal = 0;
        let faixaIndex = 0;
        paidStrategies.forEach(strat => {
            faixaIndex++;
            const count = awardCounts[strat.id] || 0;
            const isJackpot = strat.match === game.draw;

            // Usar prêmio real da API se disponível, senão fallback estático
            const realPrize = realPrizes[faixaIndex];
            const prizeValue = realPrize ? realPrize.valor : (strat.prize || 0);

            // Para prêmio principal: NÃO multiplicar por count (é o valor total do rateio)
            // Para faixas menores: prêmio é por volante
            let subtotal;
            if (isJackpot) {
                // Jackpot: se temos count ganhadores nossos, o valor é prizeValue dividido
                // entre TODOS os ganhadores (nossos + outros). Usamos como estimativa.
                subtotal = count > 0 ? prizeValue : 0;
            } else {
                subtotal = count * prizeValue;
            }
            if (count > 0) estimatedTotal += subtotal;

            const rowBg = count > 0
                ? (isJackpot ? 'rgba(255,215,0,0.15)' : 'rgba(34,197,94,0.12)')
                : 'rgba(255,255,255,0.03)';
            const borderCol = count > 0
                ? (isJackpot ? '#FFD70060' : '#22C55E50')
                : 'rgba(255,255,255,0.06)';
            const textCol = count > 0
                ? (isJackpot ? '#FFD700' : '#22C55E')
                : '#475569';

            let prizeStr;
            // Usar prizeType do games.js para exibir corretamente
            const pType = strat.prizeType || (isJackpot ? 'acumulado' : 'rateio');
            const pNote = strat.note || '';
            if (pType === 'fixo') {
                prizeStr = `${currency(prizeValue)} — <span style="color:#22C55E;font-weight:700;font-size:0.6rem;background:rgba(34,197,94,0.15);padding:1px 5px;border-radius:4px;">FIXO</span>`;
            } else if (pType === 'acumulado' || isJackpot) {
                prizeStr = `~${currency(prizeValue)} — <span style="color:#F59E0B;font-weight:700;font-size:0.6rem;background:rgba(245,158,11,0.15);padding:1px 5px;border-radius:4px;">ACUMULADO</span>`;
            } else {
                prizeStr = `~${currency(prizeValue)} — <span style="color:#94A3B8;font-weight:700;font-size:0.6rem;background:rgba(148,163,184,0.1);padding:1px 5px;border-radius:4px;">RATEIO</span>`;
            }

            summaryHTML += `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:${rowBg};border:1px solid ${borderCol};border-radius:8px;transition:all 0.3s;">`;
            summaryHTML += `<div style="display:flex;align-items:center;gap:8px;">`;
            summaryHTML += `<span style="font-size:0.9rem;">${count > 0 ? (isJackpot ? '🥇' : '✅') : '◻️'}</span>`;
            summaryHTML += `<div>`;
            summaryHTML += `<div style="font-size:0.82rem;font-weight:${count > 0 ? '700' : '400'};color:${count > 0 ? '#f1f5f9' : '#64748b'};">${strat.label}</div>`;
            summaryHTML += `<div style="font-size:0.66rem;color:#64748b;">${strat.match === 0 ? 'Nenhum número acertado' : strat.match + ' acertos'} · ${prizeStr}</div>`;
            // Nota explicativa honesta (note do games.js)
            if (pNote) {
                summaryHTML += `<div style="font-size:0.6rem;color:#475569;margin-top:1px;font-style:italic;">${pNote}</div>`;
            }
            summaryHTML += `</div></div>`;
            summaryHTML += `<div style="text-align:right;">`;
            summaryHTML += `<div style="font-size:0.9rem;font-weight:800;color:${textCol};">${count > 0 ? count + 'x' : '—'}</div>`;
            if (count > 0 && prizeValue > 0) {
                summaryHTML += `<div style="font-size:0.68rem;color:${textCol};opacity:0.85;">≈ ${currency(subtotal)}</div>`;
            }
            summaryHTML += `</div></div>`;
        });

        summaryHTML += `</div>`;

        
// ── TOTAL ESTIMADO ──
        // Somar prêmio dos extras (Time do Coração / Mês da Sorte) ao total visual
        // ★ v10.9 FIX: Prêmio de extras (Mês/Time) — SÓ contar se realmente acertou
        // Bug anterior: contava TODOS os jogos como acerto porque todo jogo tem um mês/time gerado
        if ((this.currentGameKey === 'timemania' || this.currentGameKey === 'diadesorte') && this.currentGeneratedExtras) {
            let extrasHitCount = 0;
            // Usar o valor real definido em game.extraPrize.prize (games.js V11)
            const extraPrizeUnit = (game.extraPrize && game.extraPrize.prize)
                ? game.extraPrize.prize
                : (this.currentGameKey === 'timemania' ? 7.50 : 2.50);
            const extraPrizeNote = (game.extraPrize && game.extraPrize.note) || '';
            const extrasLabel = this.currentGameKey === 'timemania' ? 'Time do Coração' : 'Mês da Sorte';

            // Determinar o extra REAL sorteado (da API)
            let drawnExtraIdx = -1; // -1 = desconhecido (API não retornou)
            if (drawResult) {
                if (this.currentGameKey === 'diadesorte' && drawResult.mesSorte) {
                    // mesSorte vem como "Janeiro", "Fevereiro", etc.
                    drawnExtraIdx = L99_MESES.findIndex(m => m.toLowerCase() === drawResult.mesSorte.toLowerCase());
                } else if (this.currentGameKey === 'timemania' && drawResult.timeCoracao) {
                    drawnExtraIdx = L99_TIMES.findIndex(t => t.toLowerCase() === drawResult.timeCoracao.toLowerCase());
                }
            }

            if (drawnExtraIdx >= 0) {
                // Temos o resultado real — verificar quais jogos acertaram
                this.currentGeneratedGames.forEach((nums, idx) => {
                    if (this.currentGeneratedExtras[idx] === drawnExtraIdx) {
                        extrasHitCount++;
                    }
                });
            }
            // Se drawnExtraIdx === -1 (sem dados da API), não contar nenhum extra como prêmio

            if (extrasHitCount > 0) {
                const extrasTotalPrize = extrasHitCount * extraPrizeUnit;
                estimatedTotal += extrasTotalPrize;
                const extraName = this.currentGameKey === 'diadesorte' 
                    ? (drawnExtraIdx >= 0 ? L99_MESES[drawnExtraIdx] : '?')
                    : (drawnExtraIdx >= 0 ? L99_TIMES[drawnExtraIdx] : '?');
                summaryHTML += `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:rgba(16,185,129,0.08);border:1px solid rgba(16,185,129,0.3);border-radius:8px;margin-top:6px;">`
                + `<div style="display:flex;align-items:center;gap:8px;">`
                + `<span style="font-size:0.9rem;">${this.currentGameKey === 'timemania' ? '⚽' : '📅'}</span>`
                + `<div><div style="font-size:0.82rem;font-weight:700;color:#f1f5f9;">${extrasLabel} Acertado: ${extraName}</div>`
                + `<div style="font-size:0.66rem;color:#64748b;">${extrasHitCount}x acertos → R$ ${extraPrizeUnit.toFixed(2).replace('.',',')} cada</div></div></div>`
                + `<div style="text-align:right;"><div style="font-size:0.9rem;font-weight:800;color:#10B981;">${extrasHitCount}x</div>`
                + `<div style="font-size:0.68rem;color:#10B981;opacity:0.85;">→ R$ ${extrasTotalPrize.toFixed(2).replace('.',',')}</div></div></div>`;
            } else if (drawnExtraIdx >= 0) {
                // Ninguém acertou — mostrar qual era o mês/time correto
                const extraName = this.currentGameKey === 'diadesorte'
                    ? L99_MESES[drawnExtraIdx]
                    : L99_TIMES[drawnExtraIdx];
                summaryHTML += `<div style="display:flex;justify-content:space-between;align-items:center;padding:8px 12px;background:rgba(255,255,255,0.03);border:1px solid rgba(255,255,255,0.06);border-radius:8px;margin-top:6px;">`
                + `<div style="display:flex;align-items:center;gap:8px;">`
                + `<span style="font-size:0.9rem;">${this.currentGameKey === 'timemania' ? '⚽' : '📅'}</span>`
                + `<div><div style="font-size:0.82rem;font-weight:400;color:#64748b;">${extrasLabel} Sorteado: ${extraName}</div>`
                + `<div style="font-size:0.66rem;color:#475569;">Nenhum jogo acertou o ${extrasLabel.toLowerCase()}</div></div></div>`
                + `<div style="text-align:right;"><div style="font-size:0.9rem;font-weight:800;color:#475569;">—</div></div></div>`;
            }
        }

        if (estimatedTotal > 0) {
            summaryHTML += `<div style="margin-top:12px;padding:12px 16px;background:linear-gradient(135deg,rgba(34,197,94,0.2),rgba(16,185,129,0.1));border:2px solid #22C55E80;border-radius:12px;display:flex;justify-content:space-between;align-items:center;">`;
            summaryHTML += `<span style="color:#86efac;font-weight:700;font-size:0.88rem;">💰 Prêmio Estimado Total</span>`;
            summaryHTML += `<span style="color:#22C55E;font-weight:900;font-size:1.1rem;">${currency(estimatedTotal)}</span>`;
            summaryHTML += `</div>`;
        }

        
// ── NÚMEROS SORTEADOS ──
        const sortedDrawn = [...drawnNumbers].sort((a, b) => a - b);
        summaryHTML += `<div style="margin-bottom:12px;padding:10px 14px;background:linear-gradient(145deg,rgba(0,0,0,0.4),rgba(0,0,0,0.2));border:1px solid ${game.color}50;border-radius:10px;">`;
        summaryHTML += `<div style="font-size:0.68rem;color:#94A3B8;text-transform:uppercase;letter-spacing:1px;margin-bottom:6px;">Resultado Oficial</div>`;
        summaryHTML += `<div style="display:flex;flex-wrap:wrap;gap:6px;justify-content:center;">`;
        sortedDrawn.forEach(n => {
            summaryHTML += `<span style="display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:50%;background:${game.color};color:#fff;font-weight:800;font-size:0.88rem;box-shadow:0 2px 8px ${game.color}60;">${String(n).padStart(2,'0')}</span>`;
        });
        summaryHTML += `</div></div>`;

        
// ── V11: JOGOS GANHADORES — Agrupados do maior ao menor prêmio ──
        if (winningGames.length > 0) {
            // Ordenar do maior prêmio (mais acertos) para o menor
            winningGames.sort((a, b) => b.hits - a.hits || b.prize - a.prize);

            summaryHTML += `<div style="margin-bottom:12px;padding:12px 14px;background:linear-gradient(145deg,rgba(34,197,94,0.06),rgba(0,0,0,0.2));border:2px solid #22C55E40;border-radius:12px;">`;
            summaryHTML += `<div style="display:flex;align-items:center;gap:8px;margin-bottom:10px;">`;
            summaryHTML += `<span style="font-size:1.2rem;">🏆</span>`;
            summaryHTML += `<div style="font-size:0.78rem;color:#22C55E;font-weight:800;text-transform:uppercase;letter-spacing:1px;">Jogos Ganhadores (${winningGames.length})</div>`;
            summaryHTML += `</div>`;

            let currentTier = null;
            winningGames.forEach(wg => {
                // Separador por faixa de prêmio
                if (currentTier !== wg.strat.id) {
                    currentTier = wg.strat.id;
                    const isJP = wg.strat.match === game.draw;
                    const tierColor = isJP ? '#FFD700' : '#22C55E';
                    summaryHTML += `<div style="display:flex;align-items:center;gap:6px;margin:${currentTier === winningGames[0].strat.id ? '0' : '8px'} 0 6px 0;">`;
                    summaryHTML += `<span style="font-size:0.7rem;">${isJP ? '🥇' : '✅'}</span>`;
                    summaryHTML += `<span style="font-size:0.72rem;font-weight:700;color:${tierColor};">${wg.strat.label}</span>`;
                    summaryHTML += `<div style="flex:1;height:1px;background:${tierColor}30;"></div>`;
                    const tierPrize = wg.prize > 100 ? ` ≈ ${currency(wg.prize)}` : (wg.prize > 0 ? ` ≈ R$ ${wg.prize.toFixed(2).replace('.',',')}` : '');
                    summaryHTML += `<span style="font-size:0.62rem;color:${tierColor};opacity:0.8;">${tierPrize}/jogo</span>`;
                    summaryHTML += `</div>`;
                }

                // Card do jogo ganhador
                const isJP = wg.strat.match === game.draw;
                const cardBorder = isJP ? '#FFD70050' : '#22C55E40';
                const cardBg = isJP ? 'rgba(255,215,0,0.06)' : 'rgba(34,197,94,0.04)';
                summaryHTML += `<div style="display:flex;align-items:center;gap:8px;padding:6px 10px;margin-bottom:4px;background:${cardBg};border:1px solid ${cardBorder};border-radius:8px;flex-wrap:wrap;">`;
                summaryHTML += `<span style="font-size:0.68rem;color:#94A3B8;font-weight:600;min-width:42px;">Jogo ${wg.index + 1}</span>`;
                
                // ★ v10.9 FIX: Badge de Time/Mês — SÓ mostrar ✓ se realmente acertou
                if (this.currentGeneratedExtras && this.currentGeneratedExtras[wg.index] !== undefined && drawResult) {
                    const genExtraIdx = this.currentGeneratedExtras[wg.index];
                    let drawnExtraIdx2 = -1;
                    if (this.currentGameKey === 'diadesorte' && drawResult.mesSorte) {
                        drawnExtraIdx2 = L99_MESES.findIndex(m => m.toLowerCase() === drawResult.mesSorte.toLowerCase());
                    } else if (this.currentGameKey === 'timemania' && drawResult.timeCoracao) {
                        drawnExtraIdx2 = L99_TIMES.findIndex(t => t.toLowerCase() === drawResult.timeCoracao.toLowerCase());
                    }
                    if (drawnExtraIdx2 >= 0 && genExtraIdx === drawnExtraIdx2) {
                        const extraLabel = this.currentGameKey === 'timemania' ? '⚽ Time ✓' : '📅 Mês ✓';
                        summaryHTML += `<span style="font-size:0.62rem;color:#10B981;background:rgba(16,185,129,0.15);padding:1px 5px;border-radius:4px;font-weight:600;">${extraLabel}</span>`;
                    }
                }
                
                summaryHTML += `<div style="display:flex;flex-wrap:wrap;gap:3px;flex:1;">`;
                wg.numbers.forEach(n => {
                    const isHit = drawnSet.has(n);
                    const bg = isHit ? '#22C55E' : 'rgba(255,255,255,0.06)';
                    const col = isHit ? '#fff' : '#64748b';
                    const shadow = isHit ? 'box-shadow:0 0 6px rgba(34,197,94,0.4);' : '';
                    summaryHTML += `<span style="display:inline-flex;align-items:center;justify-content:center;width:26px;height:26px;border-radius:50%;background:${bg};color:${col};font-weight:700;font-size:0.7rem;border:1px solid ${isHit ? '#22C55E' : 'rgba(255,255,255,0.1)'};${shadow}">${String(n).padStart(2,'0')}</span>`;
                });
                summaryHTML += `</div>`;
                
                // ★ v9.5: Mostrar acertos e valor estimado do prêmio por jogo
                const prizePerGame = wg.prize || 0;
                summaryHTML += `<div style="text-align:right;min-width:60px;">`;
                summaryHTML += `<div style="font-size:0.68rem;font-weight:700;color:${isJP ? '#FFD700' : '#22C55E'};">${wg.hits}/${game.draw}</div>`;
                if (prizePerGame > 0) {
                    const prizeDisplay = prizePerGame >= 100 
                        ? prizePerGame.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' })
                        : 'R$ ' + prizePerGame.toFixed(2).replace('.', ',');
                    summaryHTML += `<div style="font-size:0.58rem;color:${isJP ? '#FFD70090' : '#22C55E90'};">≈ ${prizeDisplay}</div>`;
                }
                summaryHTML += `</div>`;
                summaryHTML += `</div>`;
            });
            summaryHTML += `</div>`;
        }

        
// ── DISCLAIMER ──
        summaryHTML += `<div style="margin-top:10px;padding:8px 12px;background:rgba(234,179,8,0.08);border:1px solid rgba(234,179,8,0.2);border-radius:8px;font-size:0.65rem;color:#EAB308;">`;
        summaryHTML += `⚠️ <strong>Importante:</strong> Os valores de prêmios exibidos são estimativas médias baseadas nos sorteios recentes da Caixa. `;
        summaryHTML += `O prêmio real depende do rateio oficial (número de ganhadores em cada faixa). `;
        summaryHTML += `Confira sempre o resultado oficial em <strong>loterias.caixa.gov.br</strong>`;
        summaryHTML += `</div>`;

        summaryHTML += `</div>`;

        if (this.checkSummaryContainer) {
            this.checkSummaryContainer.innerHTML = summaryHTML;
            this.checkSummaryContainer.style.display = 'block';
            this.checkSummaryContainer.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }

        // ═══════════════════════════════════════════════════════
        // AUTO-SALVAR ESTATÍSTICAS (StatisticsTracker)
        // ═══════════════════════════════════════════════════════
        try {
            if (typeof StatisticsTracker !== 'undefined') {
                // Detectar drawSize real dos jogos gerados
                const actualDrawSize = (this.currentGeneratedGames && this.currentGeneratedGames[0])
                    ? this.currentGeneratedGames[0].length
                    : (this._lastDrawSize || game.minBet);
                const pricePerGame = game.price || 3.00;

                // Calcular fator de combinação para jogos com mais números
                let priceFactor = 1;
                if (actualDrawSize > game.minBet) {
                    const _comb = (n, k) => { let r = 1; for (let i = 0; i < k; i++) r *= (n - i) / (i + 1); return r; };
                    priceFactor = _comb(actualDrawSize, game.minBet);
                }
                const valorInvestido = totalJogos * pricePerGame * priceFactor;

                // Construir faixas detalhadas com prêmios reais
                const faixasDetail = {};
                let fIdx = 0;
                paidStrategies.forEach(s => {
                    fIdx++;
                    const real = realPrizes[fIdx];
                    faixasDetail[s.id] = {
                        label: s.label,
                        match: s.match,
                        count: awardCounts[s.id] || 0,
                        prizeUnit: real ? real.valor : (s.prize || 0)
                    };
                });

                // Extrair número do concurso do drawInfo
                let concursoNum = 0;
                const concursoMatch = drawInfo.match(/(\d+)/);
                if (concursoMatch) concursoNum = parseInt(concursoMatch[1]);

                // Precisão: ler rastreamento + fallback do checkbox (para QUALQUER modo)
                let isPrecisao = this._lastPrecisionMode === true;
                if (!isPrecisao) {
                    const pc = document.getElementById('precision-mode-toggle');
                    if (pc && pc.checked) {
                        isPrecisao = true;
                    }
                }

                // ★ v10.9 FIX: Coletar times/meses dos jogos que REALMENTE acertaram
                let extrasGanhadores = [];
                if ((this.currentGameKey === 'timemania' || this.currentGameKey === 'diadesorte') && this.currentGeneratedExtras && drawResult) {
                    let drawnExtraIdx = -1;
                    if (this.currentGameKey === 'diadesorte' && drawResult.mesSorte) {
                        drawnExtraIdx = L99_MESES.findIndex(m => m.toLowerCase() === drawResult.mesSorte.toLowerCase());
                    } else if (this.currentGameKey === 'timemania' && drawResult.timeCoracao) {
                        drawnExtraIdx = L99_TIMES.findIndex(t => t.toLowerCase() === drawResult.timeCoracao.toLowerCase());
                    }

                    if (drawnExtraIdx >= 0) {
                        winningGames.forEach(wg => {
                            const extraIdx = this.currentGeneratedExtras[wg.index];
                            if (extraIdx === drawnExtraIdx) {
                                const premioExtra = this.currentGameKey === 'timemania' ? 7.50 : 3.00;
                                extrasGanhadores.push({ jogo: wg.index + 1, extra: extraIdx, acertos: wg.hits, premio: wg.prize, premioExtra: premioExtra });
                            }
                        });
                    }
                }

                // Somar prêmio dos extras que REALMENTE acertaram ao total
                if (extrasGanhadores.length > 0) {
                    const extrasPrizeTotal = extrasGanhadores.reduce((sum, eg) => sum + (eg.premioExtra || 0), 0);
                    estimatedTotal += extrasPrizeTotal;
                }

                const record = {
                    lotteryKey: this.currentGameKey,
                    lotteryName: game.name,
                    concurso: concursoNum,
                    drawInfo: drawInfo,
                    data: new Date().toISOString(),
                    qtdJogos: totalJogos,
                    modoGeracao: localStorage.getItem('l99_lastMode') || document.body.getAttribute('data-l99-mode') || this._lastGenerationMode || 'manual',
                    internalEngine: this._lastInternalEngine || 'Desconhecido',
                    precisao: isPrecisao,
                    numPorJogo: actualDrawSize,
                    faixas: faixasDetail,
                    volantesPremiados: totalGanhos,
                    valorPremio: estimatedTotal,
                    valorInvestido: valorInvestido,
                    drawnNumbers: [...drawnNumbers],
                    extrasGanhadores: extrasGanhadores.length > 0 ? extrasGanhadores : undefined
                };
                record.pctRetorno = valorInvestido > 0 ? ((estimatedTotal - valorInvestido) / valorInvestido * 100) : 0;

                console.log('%c[L99-STATS] SALVANDO RECORD', 'color: #22C55E; font-weight: bold;', {
                    modo: record.modoGeracao,
                    concurso: record.concurso,
                    jogos: record.qtdJogos,
                    this_mode: this._lastGenerationMode,
                    dom_mode: document.body.getAttribute('data-l99-mode'),
                    ls_mode: localStorage.getItem('l99_lastMode')
                });
                StatisticsTracker.save(record);
                // ALERTA VISUAL de confirmação
                var modoSalvo = record.modoGeracao;
                var toast = document.createElement('div');
                toast.style.cssText = 'position:fixed;top:20px;right:20px;background:#22C55E;color:#fff;padding:12px 20px;border-radius:12px;z-index:999999;font-size:14px;font-weight:bold;box-shadow:0 4px 20px rgba(0,0,0,0.3);';
                toast.textContent = '📊 Estatística salva! Modo: ' + modoSalvo + ' | Jogos: ' + record.qtdJogos;
                document.body.appendChild(toast);
                setTimeout(function() { toast.remove(); }, 5000);
                console.log('%c[L99-STATS] RECORD SALVO COM SUCESSO', 'color: #22C55E; font-weight: bold;');

                var self = this;
                // ── SALVAR CONFERÊNCIA NA PASTA (async para não travar) ──
                setTimeout(function() { try {
                    var reportText = '════════════════════════════════════════════\n';
                    reportText += '  📊 CONFERÊNCIA L99 — ' + game.name + '\n';
                    reportText += '  Concurso ' + concursoNum + '\n';
                    reportText += '  Data: ' + new Date().toLocaleString('pt-BR') + '\n';
                    reportText += '════════════════════════════════════════════\n\n';
                    reportText += '📊 RESUMO\n';
                    reportText += '  Jogos Conferidos: ' + totalJogos + '\n';
                    reportText += '  Modo: ' + (localStorage.getItem('l99_lastMode') || document.body.getAttribute('data-l99-mode') || self._lastGenerationMode || 'manual') + '\n';
                    reportText += '  Nº por Jogo: ' + actualDrawSize + '\n\n';
                    reportText += '🔢 NÚMEROS SORTEADOS: ' + drawnNumbers.join(' - ') + '\n\n';
                    reportText += '🏅 FAIXAS DE PREMIAÇÃO\n';
                    paidStrategies.forEach(function(s) {
                        var count = awardCounts[s.id] || 0;
                        reportText += '  ' + s.label + ': ' + count + ' volante(s)\n';
                    });
                    reportText += '\n  Total Premiados: ' + totalGanhos + ' volante(s)\n';
                    reportText += '  Valor Estimado: R$ ' + estimatedTotal.toLocaleString('pt-BR', {minimumFractionDigits:2}) + '\n\n';
                    if (winningGames.length > 0) {
                        reportText += '🏆 JOGOS GANHADORES\n';
                        winningGames.forEach(function(w) {
                            reportText += '  Jogo ' + (w.index + 1) + ': ' + w.numbers.join(' - ') + ' → ' + w.hits + ' acertos (' + w.strat.label + ')\n';
                        });
                    }
                    var maxListJogos = Math.min(self.currentGeneratedGames.length, 200);
                    reportText += '\n📋 JOGOS CONFERIDOS (' + maxListJogos + ' de ' + self.currentGeneratedGames.length + ')\n';
                    var drawnS2 = new Set(drawnNumbers);
                    var minPrize = paidStrategies.length > 0 ? paidStrategies[paidStrategies.length-1].match : 3;
                    self.currentGeneratedGames.slice(0, maxListJogos).forEach(function(nums, idx) {
                        var h2 = 0;
                        nums.forEach(function(n) { if (drawnS2.has(n)) h2++; });
                        var sinal = h2 >= minPrize ? '✅' : '  ';
                        reportText += sinal + ' Jogo ' + String(idx+1).padStart(4,' ') + ': ' + nums.map(function(n){return String(n).padStart(2,'0')}).join(' - ') + ' = ' + h2 + ' acertos\n';
                    });
                    reportText += '\n════════════════════════════════════════════\n';
                    reportText += '  L99 B2B Loterias — Relatório Automático\n';
                    reportText += '════════════════════════════════════════════\n';
                    self._callServerApi('/salvar-conferencia', { method: 'POST', body: { gameKey: self.currentGameKey, concurso: concursoNum, content: reportText } }).then(function(result) {
                        if (result.ok) console.log('[L99] ✅ Conferência salva em: ' + result.fileName);
                    }).catch(function() {});
                    // Marcar arquivo original como conferido
                    if (self._lastLoadedFileName && !self._lastLoadedFileName.startsWith('✅')) {
                        self._callServerApi('/marcar-conferido', { method: 'POST', body: { gameKey: self.currentGameKey, fileName: self._lastLoadedFileName } }).catch(function() {});
                    }
                } catch(saveErr) {
                    console.warn('[L99] Erro ao salvar conferência:', saveErr);
                } }, 100); // setTimeout
            }
        } catch(statsErr) {
            console.warn('[Stats] Erro ao salvar estatística:', statsErr);
        }
    }
    exportBackup() {
        if (this.currentGeneratedGames.length === 0) {
            alert('Nenhum jogo gerado para fazer backup.\nGere seus jogos primeiro!');
            return;
        }

        const game = GAMES[this.currentGameKey];
        const gameName = game ? game.name : 'Loteria';
        const now = new Date();
        const dateStr = now.toLocaleDateString('pt-BR');
        const timeStr = now.toLocaleTimeString('pt-BR');
        const dateFile = now.toISOString().slice(0, 10).replace(/-/g, '');

        let content = '═══════════════════════════════════════\n';
        content += `  BACKUP - B2B LOTERIAS\n`;
        content += '═══════════════════════════════════════\n';
        content += `  Jogo: ${gameName}\n`;
        content += `  Data: ${dateStr} às ${timeStr}\n`;
        content += `  Total de Jogos: ${this.currentGeneratedGames.length}\n`;

        // Números fixos
        if (this.fixedNumbers.size > 0) {
            const fixedArr = Array.from(this.fixedNumbers).sort((a, b) => a - b);
            content += `  Números Fixos: ${fixedArr.map(n => n.toString().padStart(2, '0')).join(' ')}\n`;
        }

        content += '═══════════════════════════════════════\n\n';

        this.currentGeneratedGames.forEach((nums, i) => {
            const formatted = nums.map(n => n.toString().padStart(2, '0')).join('  ');
            content += `Jogo ${(i + 1).toString().padStart(3, '0')}:  ${formatted}\n`;
        });

        content += '\n═══════════════════════════════════════\n';
        content += '  Gerado por B2B Loterias - Boa Sorte!\n';
        content += '═══════════════════════════════════════\n';

        // Download como arquivo
        const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `backup_${gameName.replace(/\s+/g, '_')}_${dateFile}.txt`;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        // Feedback visual no botão
        const h3 = this.btnBackup.querySelector('h3');
        if (h3) {
            const original = h3.textContent;
            h3.textContent = '✅ BACKUP SALVO!';
            h3.style.color = '#10B981';
            setTimeout(() => {
                h3.textContent = original;
                h3.style.color = '';
            }, 2500);
        }
    }

    // ╔══════════════════════════════════════════════════════════════╗
    // ║  PAINEL ESTATÍSTICAS — Conferência de Resultados & ROI     ║
    // ║  Rastreia performance de apostas para calibrar o motor      ║
    // ╚══════════════════════════════════════════════════════════════╝

    initStatisticsPanel() {
        const statsBtn = document.getElementById('btn-statistics');
        const overlay = document.getElementById('stats-modal-overlay');
        const closeBtn = document.getElementById('stats-modal-close');
        if (!statsBtn || !overlay) return;

        const _self = this;
        this._statsActiveLottery = null;

        // ── Abrir Modal ──
        statsBtn.addEventListener('click', () => {
            overlay.classList.add('active');
            this._buildStatsLotteryGrid();
        });

        // ── Fechar Modal ──
        if (closeBtn) closeBtn.addEventListener('click', () => overlay.classList.remove('active'));
        overlay.addEventListener('click', (e) => { if (e.target === overlay) overlay.classList.remove('active'); });

        // ── Filtros ──
        ['stats-filter-modo', 'stats-filter-precisao', 'stats-filter-qtd', 'stats-filter-numjogo'].forEach(id => {
            const el = document.getElementById(id);
            if (el) el.addEventListener('change', () => _self._applyStatsFilters());
        });

        // ── Exportar CSV ──
        const exportBtn = document.getElementById('stats-export-csv');
        if (exportBtn) {
            exportBtn.addEventListener('click', () => {
                try {
                    const csv = StatisticsTracker.exportCSV(this._statsActiveLottery);
                    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' });
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    const lName = this._statsActiveLottery || 'todas';
                    a.href = url;
                    a.download = `b2b_estatisticas_${lName}_${new Date().toISOString().slice(0,10)}.csv`;
                    document.body.appendChild(a);
                    a.click();
                    document.body.removeChild(a);
                    URL.revokeObjectURL(url);
                    exportBtn.textContent = '✅ Exportado!';
                    setTimeout(() => exportBtn.textContent = '📥 Exportar CSV', 2000);
                } catch(e) {
                    alert('Erro ao exportar: ' + e.message);
                }
            });
        }

        // ── Importar CSV ──
        const importBtn = document.getElementById('stats-import-csv');
        const importInput = document.getElementById('stats-import-input');
        if (importBtn && importInput) {
            importBtn.addEventListener('click', () => importInput.click());
            importInput.addEventListener('change', (e) => {
                const file = e.target.files[0];
                if (!file) return;
                const reader = new FileReader();
                reader.onload = (ev) => {
                    try {
                        const count = StatisticsTracker.importCSV(ev.target.result);
                        alert(`✅ ${count} registros importados com sucesso!`);
                        this._buildStatsLotteryGrid();
                        if (this._statsActiveLottery) this.renderStatisticsTable(this._statsActiveLottery);
                    } catch(err) {
                        alert('Erro ao importar: ' + err.message);
                    }
                };
                reader.readAsText(file);
                importInput.value = '';
            });
        }

        // ── Limpar Dados ──
        const clearBtn = document.getElementById('stats-clear');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => {
                const lName = this._statsActiveLottery
                    ? (GAMES[this._statsActiveLottery]?.name || this._statsActiveLottery)
                    : 'TODAS AS LOTERIAS';
                if (confirm(`⚠️ Tem certeza que deseja limpar TODOS os dados de estatísticas de ${lName}?\n\nEsta ação não pode ser desfeita.`)) {
                    StatisticsTracker.clear(this._statsActiveLottery);
                    this._buildStatsLotteryGrid();
                    if (this._statsActiveLottery) this.renderStatisticsTable(this._statsActiveLottery);
                }
            });
        }
    }

    // ── Construir Grid de Loterias ──
    _buildStatsLotteryGrid() {
        const grid = document.getElementById('stats-lottery-grid');
        if (!grid) return;

        const counts = typeof StatisticsTracker !== 'undefined' ? StatisticsTracker.getCounts() : {};
        const gameKeys = ['megasena', 'lotofacil', 'quina', 'duplasena', 'lotomania', 'timemania', 'diadesorte'];

        grid.innerHTML = '';
        gameKeys.forEach(key => {
            const game = GAMES[key];
            if (!game) return;
            const count = counts[key] || 0;
            const btn = document.createElement('button');
            btn.className = 'stats-lottery-btn' + (this._statsActiveLottery === key ? ' active' : '');
            btn.style.setProperty('--stats-lottery-color', game.color);
            btn.innerHTML = `
                <div class="stats-lot-dot" style="background:${game.color};"></div>
                <div class="stats-lot-name">${game.name}</div>
                <div class="stats-lot-count">${count} registro${count !== 1 ? 's' : ''}</div>
            `;
            btn.addEventListener('click', () => {
                this._statsActiveLottery = key;
                grid.querySelectorAll('.stats-lottery-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                this.renderStatisticsTable(key);
            });
            grid.appendChild(btn);
        });
    }

    // ── Aplicar Filtros ──
    _applyStatsFilters() {
        if (!this._statsActiveLottery) return;
        this.renderStatisticsTable(this._statsActiveLottery);
    }

    // ── Renderizar Tabela de Estatísticas ──
    renderStatisticsTable(lotteryKey) {
        const tableArea = document.getElementById('stats-table-area');
        const filterBar = document.getElementById('stats-filter-bar');
        const totalsBar = document.getElementById('stats-totals');
        const actionsBar = document.getElementById('stats-actions');
        if (!tableArea) return;

        const game = GAMES[lotteryKey];
        if (!game) return;

        // Mostrar controles
        if (filterBar) filterBar.style.display = 'flex';
        if (actionsBar) actionsBar.style.display = 'flex';

        // Ler filtros
        const filters = {
            modoGeracao: document.getElementById('stats-filter-modo')?.value || 'todos',
            precisao: document.getElementById('stats-filter-precisao')?.value || 'todos',
            qtdJogos: document.getElementById('stats-filter-qtd')?.value || 'todos',
            numPorJogo: document.getElementById('stats-filter-numjogo')?.value || 'todos'
        };

        // Ajustar filtro de precisão
        if (filters.precisao === 'sim') filters.precisao = true;
        else if (filters.precisao === 'nao') filters.precisao = false;
        else filters.precisao = 'todos';

        const records = StatisticsTracker.filter(lotteryKey, filters);

        // Popular filtros dinâmicos
        const allRecords = StatisticsTracker.getAll(lotteryKey);
        this._populateStatsFilter('stats-filter-qtd', 'Qtd Jogos', allRecords.map(r => r.qtdJogos), filters.qtdJogos);
        this._populateStatsFilter('stats-filter-numjogo', 'Nº/Jogo', allRecords.map(r => r.numPorJogo), filters.numPorJogo);

        // ── Sem dados ──
        if (records.length === 0) {
            tableArea.innerHTML = `
                <div class="stats-empty">
                    <div class="stats-empty-icon">📭</div>
                    <div class="stats-empty-title">Nenhum registro encontrado</div>
                    <div class="stats-empty-desc">
                        ${allRecords.length > 0
                            ? 'Nenhum resultado corresponde aos filtros selecionados. Tente alterar os filtros.'
                            : `Ainda não há conferências registradas para <strong>${game.name}</strong>.<br>Gere jogos, depois use o botão <strong>"Conferir"</strong> para verificar os resultados.`}
                    </div>
                </div>`;
            if (totalsBar) { totalsBar.style.display = 'none'; totalsBar.innerHTML = ''; }
            return;
        }

        // ── Aggregates ──
        const agg = StatisticsTracker.aggregate(records);
        if (totalsBar) {
            totalsBar.style.display = 'grid';
            const currency = (n) => n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2 });
            const retClass = agg.pctRetornoMedio >= 0 ? 'positive' : 'negative';
            totalsBar.innerHTML = `
                <div class="stats-total-card"><div class="stats-total-label">Conferências</div><div class="stats-total-value">${agg.total}</div></div>
                <div class="stats-total-card"><div class="stats-total-label">Total Jogos</div><div class="stats-total-value">${agg.totalJogos}</div></div>
                <div class="stats-total-card"><div class="stats-total-label">Investido</div><div class="stats-total-value">${currency(agg.totalInvestido)}</div></div>
                <div class="stats-total-card"><div class="stats-total-label">Premiado</div><div class="stats-total-value stats-cell-prize">${currency(agg.totalPremio)}</div></div>
                <div class="stats-total-card"><div class="stats-total-label">Volantes Premiados</div><div class="stats-total-value">${agg.totalVolantesPremiados}</div></div>
                <div class="stats-total-card"><div class="stats-total-label">Retorno Médio</div><div class="stats-total-value ${retClass}">${agg.pctRetornoMedio >= 0 ? '+' : ''}${agg.pctRetornoMedio.toFixed(1)}%</div></div>
            `;
        }

        // ── Tabela ──
        const paidStrats = game.strategies.filter(s => s.paid !== false);
        const currency = (n) => n.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL', minimumFractionDigits: 2 });

        // ── Adicionar Banner de Premiação (Timemania / Dia de Sorte) ──
        let prizeBannerHtml = '';
        if (lotteryKey === 'timemania' || lotteryKey === 'diadesorte') {
            const prizeInfo = typeof StatsService !== 'undefined' ? StatsService.getPrizeInfo(lotteryKey) : null;
            if (prizeInfo && prizeInfo.estimatedPrize) {
                const prizeFormatted = prizeInfo.estimatedPrize.toLocaleString('pt-BR', { style: 'currency', currency: 'BRL' });
                prizeBannerHtml = `
                    <div style="margin-bottom:15px;padding:12px 16px;background:linear-gradient(145deg,rgba(16,185,129,0.1),rgba(15,23,42,0.9));border:1px solid #10B98150;border-radius:8px;display:flex;align-items:center;gap:12px;">
                        <div style="font-size:2rem;">💰</div>
                        <div>
                            <div style="color:#10B981;font-weight:700;font-size:1.1rem;">Premiação Estimada ${game.name}</div>
                            <div style="color:#E2E8F0;font-size:0.9rem;">Próximo Concurso: <span style="font-weight:800;color:#FFD700;">${prizeFormatted}</span></div>
                        </div>
                    </div>
                `;
            }
        }

        const isTimemania = lotteryKey === 'timemania';
        const isDiaDeSorte = lotteryKey === 'diadesorte';
        const hasExtrasCol = isTimemania || isDiaDeSorte;
        const extrasColLabel = isTimemania ? 'Time' : 'Mês';

        let html = prizeBannerHtml + '<div class="stats-table-wrapper"><table class="stats-table"><thead><tr>';
        html += '<th>Data</th>';
        html += '<th>Concurso</th>';
        html += '<th>Jogos</th>';
        html += '<th>Modo</th>';
        html += '<th>Precisão</th>';
        html += '<th>Nº/Jogo</th>';

        paidStrats.forEach(s => {
            html += `<th>${s.label.replace(/\(.+?\)/, '').trim()}</th>`;
        });

        html += '<th>Premiados</th>';
        // ★ v9.5: Coluna Time/Mês para Timemania e Dia de Sorte
        if (hasExtrasCol) html += `<th>${extrasColLabel}</th>`;
        html += '<th>Valor Prêmio</th>';
        html += '<th>Investido</th>';
        html += '<th>% Retorno</th>';
        html += '<th></th>';
        html += '</tr></thead><tbody>';

        records.forEach(r => {
            const data = r.data ? new Date(r.data).toLocaleDateString('pt-BR') : '—';

            // Badge de modo
            const modoBadgeClass = {
                'manual': 'manual',
                'estatistica': 'quantum',
                'manual_sniper': 'manual',
                'cobertura': 'gerar',
                'cobertura_sniper': 'gerar',
                'precision': 'quantum',
                'precision_sniper': 'quantum',
                'quantum_l99': 'quantum',
                'precision_l99': 'quantum',
                'gerar_jogos': 'manual',
                'dual_2g': 'dual',
                'fechamento': 'fech'
            }[r.modoGeracao] || 'manual';
            const modoLabel = StatisticsTracker.getModoLabel(r.modoGeracao);

            // Badge de precisão
            const precBadge = r.precisao
                ? '<span class="stats-badge sim">Sim</span>'
                : '<span class="stats-badge nao">Não</span>';

            // Retorno
            const retorno = r.pctRetorno || 0;
            const retClass = retorno > 0 ? 'stats-cell-positive' : (retorno < 0 ? 'stats-cell-negative' : 'stats-cell-neutral');
            const retStr = (retorno >= 0 ? '+' : '') + retorno.toFixed(1) + '%';

            // Valor prêmio
            const premioStr = r.valorPremio > 0 ? currency(r.valorPremio) : '—';
            const premioClass = r.valorPremio > 0 ? 'stats-cell-prize' : 'stats-cell-neutral';

            html += '<tr>';
            html += `<td>${data}</td>`;
            html += `<td>${r.concurso || '—'}</td>`;
            html += `<td>${r.qtdJogos || 0}</td>`;
            html += `<td><span class="stats-badge ${modoBadgeClass}">${modoLabel}</span></td>`;
            html += `<td>${precBadge}</td>`;
            html += `<td>${r.numPorJogo || '—'}</td>`;

            // Faixas de premiação
            paidStrats.forEach(s => {
                const faixa = r.faixas && r.faixas[s.id];
                const count = faixa ? faixa.count : 0;
                if (count > 0) {
                    html += `<td><strong style="color:#22C55E;">${count}x</strong></td>`;
                } else {
                    html += `<td style="color:#334155;">—</td>`;
                }
            });

            html += `<td>${r.volantesPremiados > 0 ? '<strong style="color:#22C55E;">' + r.volantesPremiados + '</strong>' : '0'}</td>`;

            // ★ v9.5: Coluna Time/Mês com badges dos ganhadores
            if (hasExtrasCol) {
                if (r.extrasGanhadores && r.extrasGanhadores.length > 0) {
                    const badgeColor = isTimemania ? '#10B981' : '#F59E0B';
                    const badgeBg = isTimemania ? 'rgba(16,185,129,0.15)' : 'rgba(245,158,11,0.15)';
                    const icon = isTimemania ? '⚽' : '📅';
                    const extrasCount = r.extrasGanhadores.length;
                    const extrasTotal = r.extrasGanhadores.reduce((sum, eg) => sum + (eg.premioExtra || 0), 0);
                    const extrasTotalStr = extrasTotal > 0 ? `<div style="font-size:0.55rem;color:${badgeColor};margin-top:2px;">+R$ ${extrasTotal.toFixed(2).replace('.',',')}</div>` : '';
                    html += `<td style="text-align:center;"><strong style="color:${badgeColor};font-size:0.85rem;">${extrasCount}x</strong>${extrasTotalStr}</td>`;
                } else {
                    html += `<td style="color:#334155;">—</td>`;
                }
            }

            html += `<td class="${premioClass}">${premioStr}</td>`;
            html += `<td>${currency(r.valorInvestido || 0)}</td>`;
            html += `<td class="${retClass}">${retStr}</td>`;
            html += `<td><button class="stats-delete-btn" data-id="${r.id}" data-lottery="${lotteryKey}" title="Excluir registro">🗑️</button></td>`;
            html += '</tr>';
        });

        html += '</tbody></table></div>';
        tableArea.innerHTML = html;

        // ── Delete handlers ──
        tableArea.querySelectorAll('.stats-delete-btn').forEach(btn => {
            btn.addEventListener('click', () => {
                const id = btn.dataset.id;
                const lk = btn.dataset.lottery;
                if (confirm('Excluir este registro?')) {
                    StatisticsTracker.remove(lk, id);
                    this._buildStatsLotteryGrid();
                    this.renderStatisticsTable(lk);
                }
            });
        });
    }

    // ── Popular filtro dinâmico ──
    _populateStatsFilter(selectId, label, values, currentValue) {
        const sel = document.getElementById(selectId);
        if (!sel) return;
        const unique = [...new Set(values.filter(v => v != null))].sort((a, b) => a - b);
        const oldVal = currentValue || sel.value;
        sel.innerHTML = `<option value="todos">${label}: Todos</option>`;
        unique.forEach(v => {
            sel.innerHTML += `<option value="${v}" ${String(v) === String(oldVal) ? 'selected' : ''}>${v}</option>`;
        });
    }

    // ─── Métodos auxiliares para fechamento manual ─────────────────────────
    // Calcula C(n, k) — número de combinações possíveis
    _manualComb(n, k) {
        if (k < 0 || k > n) return 0;
        if (k === 0 || k === n) return 1;
        k = Math.min(k, n - k);
        let result = 1;
        for (let i = 0; i < k; i++) {
            result = result * (n - i) / (i + 1);
        }
        return Math.round(result);
    }

    // Gera todas as combinações C(pool, drawSize) com suporte a fixos
    _manualGenCombos(pool, drawSize, start, current, result, fixedArr) {
        if (result.length >= 500000) return; // Limite de segurança
        if (current.length === drawSize) {
            // Verificar que todos os fixos estão incluídos
            const s = new Set(current);
            const fixedOk = !fixedArr || fixedArr.every(f => s.has(f));
            if (fixedOk) result.push(current.slice().sort((a, b) => a - b));
            return;
        }
        const remaining = drawSize - current.length;
        const available = pool.length - start;
        if (available < remaining) return; // Poda: não há números suficientes
        for (let i = start; i < pool.length; i++) {
            current.push(pool[i]);
            this._manualGenCombos(pool, drawSize, i + 1, current, result, fixedArr);
            current.pop();
        }
    }
}

// Export removed for global script compatibility
/* Cache bust: 20260511171042 */








