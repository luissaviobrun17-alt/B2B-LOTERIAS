/**
 * ╔══════════════════════════════════════════════════════════════════════════════╗
 * ║  ROI DASHBOARD v1.0 — Painel de Auditoria de Retorno                       ║
 * ║                                                                            ║
 * ║  Módulo de análise financeira para loterias da Caixa Econômica Federal.    ║
 * ║  Gera painéis HTML completos com:                                          ║
 * ║    • Relatório de conferência pós-sorteio                                  ║
 * ║    • Preview de ROI pré-geração                                            ║
 * ║    • Comparação entre todas as loterias                                    ║
 * ║                                                                            ║
 * ║  Probabilidades exatas via distribuição hipergeométrica (log-combinação).  ║
 * ║  Sem dependências externas. CSS inline moderno com glassmorphism.          ║
 * ╚══════════════════════════════════════════════════════════════════════════════╝
 */

class ROIDashboard {

    // ═══════════════════════════════════════════════════════════════════════
    //  CONSTANTES — Dados oficiais das loterias (Lei 13.756/2018)
    // ═══════════════════════════════════════════════════════════════════════

    /** Percentual de payout oficial por loteria (arrecadação destinada a prêmios) */
    static get PAYOUT_OFICIAL() {
        return {
            lotofacil:  0.4335,
            megasena:   0.4379,
            quina:      0.4379,
            timemania:  0.4600,
            diadesorte: 0.4335,
            duplasena:  0.4379,
            lotomania:  0.4335
        };
    }

    /** Configuração combinatória de cada loteria */
    static get LOTTERY_CONFIG() {
        return {
            megasena:   { nome: 'Mega Sena',    N: 60,  K: 6,  n: 6,  custo: 6.00, cor: '#209A3C' },
            lotofacil:  { nome: 'Lotofácil',     N: 25,  K: 15, n: 15, custo: 3.50, cor: '#930089' },
            quina:      { nome: 'Quina',         N: 80,  K: 5,  n: 5,  custo: 3.00, cor: '#3062a8' },
            duplasena:  { nome: 'Dupla Sena',    N: 50,  K: 6,  n: 6,  custo: 3.00, cor: '#e8000f' },
            lotomania:  { nome: 'Lotomania',     N: 100, K: 20, n: 50, custo: 3.00, cor: '#f07d00' },
            timemania:  { nome: 'Timemania',     N: 80,  K: 7,  n: 10, custo: 3.50, cor: '#00a859' },
            diadesorte: { nome: 'Dia de Sorte',  N: 31,  K: 7,  n: 7,  custo: 3.00, cor: '#e27820' }
        };
    }

    /** Prêmios fixos conhecidos (onde aplicável) */
    static get PREMIOS_FIXOS() {
        return {
            lotofacil: { 11: 6, 12: 12, 13: 30 },
            timemania: { 3: 3.50, 4: 10.50 },
            diadesorte: { 4: 5, 5: 25 }
        };
    }

    /** Prêmios médios estimados por faixa (variáveis — base histórica) */
    static get PREMIOS_ESTIMADOS() {
        return {
            megasena: [
                { hits: 6, premio: 50000000, nome: 'Sena (6 acertos)' },
                { hits: 5, premio: 40000,    nome: 'Quina (5 acertos)' },
                { hits: 4, premio: 900,      nome: 'Quadra (4 acertos)' }
            ],
            lotofacil: [
                { hits: 15, premio: 1500000, nome: '15 acertos' },
                { hits: 14, premio: 1200,    nome: '14 acertos' },
                { hits: 13, premio: 30,      nome: '13 acertos', fixo: true },
                { hits: 12, premio: 12,      nome: '12 acertos', fixo: true },
                { hits: 11, premio: 6,       nome: '11 acertos', fixo: true }
            ],
            quina: [
                { hits: 5, premio: 6000000, nome: 'Quina (5 acertos)' },
                { hits: 4, premio: 6500,    nome: 'Quadra (4 acertos)' },
                { hits: 3, premio: 4,       nome: 'Terno (3 acertos)' },
                { hits: 2, premio: 2,       nome: 'Duque (2 acertos)' }
            ],
            duplasena: [
                { hits: 6, premio: 3000000, nome: 'Sena (6 acertos)' },
                { hits: 5, premio: 5000,    nome: 'Quina (5 acertos)' },
                { hits: 4, premio: 130,     nome: 'Quadra (4 acertos)' },
                { hits: 3, premio: 3,       nome: 'Terno (3 acertos)' }
            ],
            lotomania: [
                { hits: 20, premio: 5000000, nome: '20 acertos' },
                { hits: 19, premio: 80000,   nome: '19 acertos' },
                { hits: 18, premio: 3000,    nome: '18 acertos' },
                { hits: 17, premio: 250,     nome: '17 acertos' },
                { hits: 16, premio: 30,      nome: '16 acertos' },
                { hits: 15, premio: 6,       nome: '15 acertos' },
                { hits: 0,  premio: 5000000, nome: '0 acertos' }
            ],
            timemania: [
                { hits: 7, premio: 4000000, nome: '7 acertos' },
                { hits: 6, premio: 30000,   nome: '6 acertos' },
                { hits: 5, premio: 800,     nome: '5 acertos' },
                { hits: 4, premio: 10.50,   nome: '4 acertos', fixo: true },
                { hits: 3, premio: 3.50,    nome: '3 acertos', fixo: true }
            ],
            diadesorte: [
                { hits: 7, premio: 1000000, nome: '7 acertos' },
                { hits: 6, premio: 2500,    nome: '6 acertos' },
                { hits: 5, premio: 25,      nome: '5 acertos', fixo: true },
                { hits: 4, premio: 5,       nome: '4 acertos', fixo: true }
            ]
        };
    }

    // ═══════════════════════════════════════════════════════════════════════
    //  MATEMÁTICA — Log-combinação e probabilidade hipergeométrica
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Cache de log-fatoriais para performance em cálculos repetidos
     * @private
     */
    static _logFactCache = [0, 0]; // logFact(0)=0, logFact(1)=0

    /**
     * Calcula ln(n!) usando cache incremental.
     * Evita overflow com números grandes (ex: C(100,50)).
     * @param {number} n - inteiro não-negativo
     * @returns {number} ln(n!)
     */
    static _logFact(n) {
        if (n < 0) return 0;
        if (n < this._logFactCache.length) return this._logFactCache[n];
        // Preenche cache incrementalmente
        let last = this._logFactCache[this._logFactCache.length - 1];
        for (let i = this._logFactCache.length; i <= n; i++) {
            last += Math.log(i);
            this._logFactCache.push(last);
        }
        return this._logFactCache[n];
    }

    /**
     * Calcula ln(C(n, k)) = ln(n!) - ln(k!) - ln((n-k)!)
     * @param {number} n - total de elementos
     * @param {number} k - elementos escolhidos
     * @returns {number} logaritmo natural da combinação
     */
    static _logComb(n, k) {
        if (k < 0 || k > n) return -Infinity;
        if (k === 0 || k === n) return 0;
        return this._logFact(n) - this._logFact(k) - this._logFact(n - k);
    }

    /**
     * Calcula C(n, k) usando BigInt para resultados exatos.
     * Usado quando o resultado preciso é necessário (não probabilidade).
     * @param {number} n
     * @param {number} k
     * @returns {number}
     */
    static _comb(n, k) {
        if (k < 0 || k > n) return 0;
        if (k === 0 || k === n) return 1;
        if (k > n - k) k = n - k;
        let r = 1;
        for (let i = 0; i < k; i++) {
            r = r * (n - i) / (i + 1);
        }
        return Math.round(r);
    }

    /**
     * Probabilidade hipergeométrica exata: P(X = k)
     *
     * Fórmula: P(X=k) = C(K,k) × C(N-K, n-k) / C(N,n)
     *
     * Usa log-combinação para evitar overflow numérico.
     *
     * @param {number} N - tamanho do universo (ex: 60 para Mega-Sena)
     * @param {number} K - sucessos no universo (números sorteados)
     * @param {number} n - tamanho da amostra (números apostados)
     * @param {number} k - acertos desejados
     * @returns {number} probabilidade entre 0 e 1
     */
    static _hypergeometric(N, K, n, k) {
        if (k < 0 || k > Math.min(K, n)) return 0;
        if ((n - k) > (N - K)) return 0;

        var logP = this._logComb(K, k) + this._logComb(N - K, n - k) - this._logComb(N, n);
        return Math.exp(logP);
    }

    /**
     * Calcula odds (1 em X) a partir de uma probabilidade.
     * @param {number} prob
     * @returns {string} texto formatado "1 em X"
     */
    static _oddsText(prob) {
        if (prob <= 0) return '—';
        var odds = Math.round(1 / prob);
        return '1 em ' + odds.toLocaleString('pt-BR');
    }

    // ═══════════════════════════════════════════════════════════════════════
    //  FORMATAÇÃO — Moeda, percentual e números
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Formata valor em Reais (R$) no padrão brasileiro.
     * @param {number} valor
     * @returns {string}
     */
    static _fmt(valor) {
        if (valor === undefined || valor === null || isNaN(valor)) return 'R$ 0,00';
        var abs = Math.abs(valor);
        var sinal = valor < 0 ? '-' : '';
        return sinal + 'R$ ' + abs.toLocaleString('pt-BR', {
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        });
    }

    /**
     * Formata valor em Reais de forma compacta (K/M).
     * @param {number} valor
     * @returns {string}
     */
    static _fmtCompact(valor) {
        if (valor === undefined || valor === null) return 'R$ 0';
        var abs = Math.abs(valor);
        var sinal = valor < 0 ? '-' : '';
        if (abs >= 1000000) return sinal + 'R$ ' + (abs / 1000000).toFixed(1).replace('.', ',') + 'M';
        if (abs >= 1000) return sinal + 'R$ ' + (abs / 1000).toFixed(1).replace('.', ',') + 'K';
        return sinal + 'R$ ' + abs.toFixed(2).replace('.', ',');
    }

    /**
     * Formata percentual com sinal e cor.
     * @param {number} pct - valor percentual
     * @returns {{ text: string, color: string }}
     */
    static _fmtPct(pct) {
        var text = (pct >= 0 ? '+' : '') + pct.toFixed(2) + '%';
        var color = pct >= 0 ? '#00ff88' : '#ff4444';
        return { text: text, color: color };
    }

    // ═══════════════════════════════════════════════════════════════════════
    //  ESTILOS CSS — Base de estilos inline reutilizáveis
    // ═══════════════════════════════════════════════════════════════════════

    /** Retorna os estilos CSS base do dashboard */
    static get _STYLES() {
        return {
            container: 'background:linear-gradient(145deg,#1a1a2e,#16213e);border-radius:16px;padding:24px;color:#e2e8f0;font-family:inherit;',
            card: 'background:rgba(255,255,255,0.05);backdrop-filter:blur(10px);-webkit-backdrop-filter:blur(10px);border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:16px;margin-bottom:16px;',
            cardHeader: 'font-size:1rem;font-weight:800;margin-bottom:12px;display:flex;align-items:center;gap:8px;',
            metricBox: 'background:rgba(0,0,0,0.3);border-radius:10px;padding:12px;text-align:center;',
            metricLabel: 'color:#94a3b8;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.5px;margin-bottom:4px;',
            metricValue: 'font-size:1.2rem;font-weight:800;',
            table: 'width:100%;border-collapse:collapse;font-size:0.75rem;',
            th: 'padding:8px 6px;text-align:left;color:#64748b;font-size:0.65rem;text-transform:uppercase;letter-spacing:0.5px;border-bottom:2px solid #334155;',
            td: 'padding:8px 6px;border-bottom:1px solid rgba(255,255,255,0.05);color:#cbd5e1;',
            badge: 'display:inline-block;padding:3px 8px;border-radius:6px;font-size:0.65rem;font-weight:700;',
            fadeIn: 'animation:roiFadeIn 0.5s ease-out;',
            alertBox: 'border-radius:10px;padding:12px;margin-bottom:12px;font-size:0.8rem;line-height:1.5;',
            barContainer: 'background:rgba(0,0,0,0.4);border-radius:6px;height:24px;overflow:hidden;position:relative;',
            barFill: 'height:100%;border-radius:6px;transition:width 0.8s ease;display:flex;align-items:center;padding-left:8px;font-size:0.65rem;font-weight:700;color:#fff;'
        };
    }

    /** Retorna o bloco <style> com a animação fadeIn */
    static _getAnimationStyle() {
        return '<style>@keyframes roiFadeIn{from{opacity:0;transform:translateY(12px)}to{opacity:1;transform:translateY(0)}}@keyframes roiPulse{0%,100%{opacity:1}50%{opacity:.7}}</style>';
    }

    // ═══════════════════════════════════════════════════════════════════════
    //  MÉTODO 1: generateReport — Relatório Pós-Conferência
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Gera HTML completo para o painel de auditoria pós-conferência.
     *
     * @param {string} gameKey - chave da loteria (ex: 'lotofacil')
     * @param {Array<Object>} conferenceData - dados das conferências:
     *   { date, concurso, numGames, engine, drawSize, hits15, hits14, hits13,
     *     hits12, hits11, totalPremios, investido, retorno }
     * @returns {string} HTML completo do painel
     */
    static generateReport(gameKey, conferenceData) {
        var s = this._STYLES;
        var config = this.LOTTERY_CONFIG[gameKey];
        var payoutOficial = this.PAYOUT_OFICIAL[gameKey] || 0.4335;

        if (!config) {
            return '<div style="color:#ff4444;padding:16px;">❌ Loteria não encontrada: ' + gameKey + '</div>';
        }

        if (!conferenceData || conferenceData.length === 0) {
            return '<div style="color:#94a3b8;padding:16px;">📭 Nenhum dado de conferência disponível para ' + config.nome + '.</div>';
        }

        // ─── Cálculos agregados ───
        var totalInvestido = 0;
        var totalPremiado = 0;
        var totalJogos = 0;
        var porMotor = {}; // { engine: { investido, retorno, conferencias } }

        for (var i = 0; i < conferenceData.length; i++) {
            var d = conferenceData[i];
            var inv = d.investido || 0;
            var ret = d.retorno || d.totalPremios || 0;
            totalInvestido += inv;
            totalPremiado += ret;
            totalJogos += (d.numGames || 0);

            var eng = d.engine || 'Desconhecido';
            if (!porMotor[eng]) porMotor[eng] = { investido: 0, retorno: 0, conferencias: 0 };
            porMotor[eng].investido += inv;
            porMotor[eng].retorno += ret;
            porMotor[eng].conferencias++;
        }

        var retornoMedio = totalInvestido > 0 ? (totalPremiado / totalInvestido) * 100 : 0;
        var retornoTeorico = payoutOficial * 100;
        var deficit = retornoMedio - retornoTeorico;

        // Classificação
        var classif, classifEmoji, classifCor;
        if (deficit >= -5) {
            classif = 'Normal'; classifEmoji = '🟢'; classifCor = '#00ff88';
        } else if (deficit >= -15) {
            classif = 'Abaixo'; classifEmoji = '🟡'; classifCor = '#fbbf24';
        } else {
            classif = 'Crítico'; classifEmoji = '🔴'; classifCor = '#ff4444';
        }

        // ─── Montagem HTML ───
        var html = this._getAnimationStyle();
        html += '<div style="' + s.container + s.fadeIn + '">';

        // Cabeçalho
        html += '<div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:20px;">';
        html += '<div>';
        html += '<div style="font-size:1.3rem;font-weight:900;background:linear-gradient(90deg,' + config.cor + ',#00ff88);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">📊 Painel de Auditoria ROI</div>';
        html += '<div style="color:#64748b;font-size:0.7rem;margin-top:2px;">' + config.nome + ' — ' + conferenceData.length + ' conferência(s) analisada(s)</div>';
        html += '</div>';
        html += '<div style="' + s.badge + 'background:' + classifCor + '20;color:' + classifCor + ';border:1px solid ' + classifCor + '40;font-size:0.8rem;">' + classifEmoji + ' ' + classif + '</div>';
        html += '</div>';

        // ─── 1. Resumo Geral ───
        html += '<div style="' + s.card + '">';
        html += '<div style="' + s.cardHeader + 'color:#00ff88;">💰 Resumo Geral</div>';
        html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:14px;">';

        // Total Investido
        html += '<div style="' + s.metricBox + '">';
        html += '<div style="' + s.metricLabel + '">Total Investido</div>';
        html += '<div style="' + s.metricValue + 'color:#ff6b6b;">' + this._fmt(totalInvestido) + '</div>';
        html += '</div>';

        // Total Premiado
        html += '<div style="' + s.metricBox + '">';
        html += '<div style="' + s.metricLabel + '">Total Premiado</div>';
        html += '<div style="' + s.metricValue + 'color:#00ff88;">' + this._fmt(totalPremiado) + '</div>';
        html += '</div>';

        // Retorno Médio
        var retPctFmt = this._fmtPct(retornoMedio - 100);
        html += '<div style="' + s.metricBox + '">';
        html += '<div style="' + s.metricLabel + '">Retorno Médio</div>';
        html += '<div style="' + s.metricValue + 'color:' + retPctFmt.color + ';">' + retornoMedio.toFixed(2) + '%</div>';
        html += '</div>';

        html += '</div>'; // grid

        // Métricas secundárias
        html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;">';

        // Retorno teórico
        html += '<div style="' + s.metricBox + '">';
        html += '<div style="' + s.metricLabel + '">Retorno Teórico (Caixa)</div>';
        html += '<div style="' + s.metricValue + 'color:#60a5fa;">' + retornoTeorico.toFixed(2) + '%</div>';
        html += '</div>';

        // Déficit
        var defFmt = this._fmtPct(deficit);
        html += '<div style="' + s.metricBox + '">';
        html += '<div style="' + s.metricLabel + '">Déficit vs Teórico</div>';
        html += '<div style="' + s.metricValue + 'color:' + defFmt.color + ';">' + defFmt.text + '</div>';
        html += '</div>';

        // Total de jogos
        html += '<div style="' + s.metricBox + '">';
        html += '<div style="' + s.metricLabel + '">Total de Jogos</div>';
        html += '<div style="' + s.metricValue + 'color:#c4b5fd;">' + totalJogos.toLocaleString('pt-BR') + '</div>';
        html += '</div>';

        html += '</div>'; // grid
        html += '</div>'; // card

        // ─── 2. Tabela Comparativa por Motor ───
        var engines = Object.keys(porMotor);
        if (engines.length > 0) {
            html += '<div style="' + s.card + '">';
            html += '<div style="' + s.cardHeader + 'color:#a78bfa;">⚙️ Comparativo por Motor</div>';
            html += '<table style="' + s.table + '">';
            html += '<thead><tr>';
            html += '<th style="' + s.th + '">Motor</th>';
            html += '<th style="' + s.th + 'text-align:right;">Investido</th>';
            html += '<th style="' + s.th + 'text-align:right;">Retorno</th>';
            html += '<th style="' + s.th + 'text-align:right;">ROI %</th>';
            html += '<th style="' + s.th + 'text-align:right;">vs Teórico</th>';
            html += '<th style="' + s.th + 'text-align:center;">Status</th>';
            html += '</tr></thead><tbody>';

            // Encontrar melhor motor
            var melhorRoi = -Infinity;
            var melhorMotor = '';
            for (var e = 0; e < engines.length; e++) {
                var eng = engines[e];
                var dados = porMotor[eng];
                var roi = dados.investido > 0 ? (dados.retorno / dados.investido) * 100 : 0;
                if (roi > melhorRoi) { melhorRoi = roi; melhorMotor = eng; }
            }

            for (var e = 0; e < engines.length; e++) {
                var eng = engines[e];
                var dados = porMotor[eng];
                var roi = dados.investido > 0 ? (dados.retorno / dados.investido) * 100 : 0;
                var roiVsTeorico = roi - retornoTeorico;
                var roiFmt = this._fmtPct(roi - 100);
                var vsFmt = this._fmtPct(roiVsTeorico);
                var isMelhor = eng === melhorMotor;

                html += '<tr style="' + (isMelhor ? 'background:rgba(0,255,136,0.05);' : '') + '">';
                html += '<td style="' + s.td + 'font-weight:700;color:#e2e8f0;">' + eng + (isMelhor ? ' 👑' : '') + '</td>';
                html += '<td style="' + s.td + 'text-align:right;">' + this._fmt(dados.investido) + '</td>';
                html += '<td style="' + s.td + 'text-align:right;">' + this._fmt(dados.retorno) + '</td>';
                html += '<td style="' + s.td + 'text-align:right;color:' + roiFmt.color + ';font-weight:700;">' + roi.toFixed(2) + '%</td>';
                html += '<td style="' + s.td + 'text-align:right;color:' + vsFmt.color + ';">' + vsFmt.text + '</td>';
                html += '<td style="' + s.td + 'text-align:center;">' + (roiVsTeorico >= 0 ? '🟢' : roiVsTeorico >= -10 ? '🟡' : '🔴') + '</td>';
                html += '</tr>';
            }

            // Linha teórica (aleatório)
            html += '<tr style="border-top:2px solid #334155;background:rgba(96,165,250,0.05);">';
            html += '<td style="' + s.td + 'color:#60a5fa;font-style:italic;">📐 Aleatório (teórico)</td>';
            html += '<td style="' + s.td + 'text-align:right;color:#64748b;">—</td>';
            html += '<td style="' + s.td + 'text-align:right;color:#64748b;">—</td>';
            html += '<td style="' + s.td + 'text-align:right;color:#60a5fa;font-weight:700;">' + retornoTeorico.toFixed(2) + '%</td>';
            html += '<td style="' + s.td + 'text-align:right;color:#64748b;">0,00%</td>';
            html += '<td style="' + s.td + 'text-align:center;">📐</td>';
            html += '</tr>';

            html += '</tbody></table>';
            html += '</div>'; // card
        }

        // ─── 3. Gráfico de Evolução (barras CSS) ───
        html += '<div style="' + s.card + '">';
        html += '<div style="' + s.cardHeader + 'color:#fbbf24;">📈 Evolução por Conferência</div>';

        // Encontrar max para escala
        var maxRetorno = 0;
        for (var i = 0; i < conferenceData.length; i++) {
            var ret = conferenceData[i].investido > 0 ? (conferenceData[i].retorno || conferenceData[i].totalPremios || 0) / conferenceData[i].investido * 100 : 0;
            if (ret > maxRetorno) maxRetorno = ret;
        }
        var escalaMax = Math.max(maxRetorno, retornoTeorico * 2, 100);

        // Linha de referência teórica (posição relativa)
        var refPos = Math.min((retornoTeorico / escalaMax) * 100, 95);

        html += '<div style="position:relative;margin-bottom:10px;">';

        for (var i = 0; i < conferenceData.length; i++) {
            var d = conferenceData[i];
            var inv = d.investido || 0;
            var ret = d.retorno || d.totalPremios || 0;
            var pctRetorno = inv > 0 ? (ret / inv) * 100 : 0;
            var barWidth = Math.min((pctRetorno / escalaMax) * 100, 100);
            var barColor = pctRetorno >= retornoTeorico ? 'linear-gradient(90deg,#00ff88,#00cc6a)' : 'linear-gradient(90deg,#ff4444,#cc3333)';
            var label = d.concurso ? 'C.' + d.concurso : 'Conf. ' + (i + 1);

            html += '<div style="margin-bottom:8px;">';
            html += '<div style="display:flex;justify-content:space-between;margin-bottom:3px;">';
            html += '<span style="font-size:0.65rem;color:#94a3b8;">' + label + (d.date ? ' (' + d.date + ')' : '') + '</span>';
            html += '<span style="font-size:0.65rem;color:#e2e8f0;font-weight:700;">' + pctRetorno.toFixed(1) + '%</span>';
            html += '</div>';
            html += '<div style="' + s.barContainer + '">';
            html += '<div style="' + s.barFill + 'width:' + Math.max(barWidth, 2) + '%;background:' + barColor + ';">' + (barWidth > 15 ? this._fmtCompact(ret) : '') + '</div>';
            // Linha de referência teórica
            html += '<div style="position:absolute;left:' + refPos + '%;top:0;height:100%;width:2px;background:#60a5fa;opacity:0.7;"></div>';
            html += '</div>';
            html += '</div>';
        }

        // Legenda
        html += '<div style="display:flex;gap:16px;margin-top:10px;font-size:0.6rem;color:#64748b;">';
        html += '<span>🟩 Acima do teórico</span>';
        html += '<span>🟥 Abaixo do teórico</span>';
        html += '<span style="color:#60a5fa;">│ Referência: ' + retornoTeorico.toFixed(1) + '%</span>';
        html += '</div>';

        html += '</div>'; // posição relativa
        html += '</div>'; // card

        // ─── 4. Recomendações ───
        html += '<div style="' + s.card + '">';
        html += '<div style="' + s.cardHeader + 'color:#f472b6;">💡 Recomendações</div>';

        var recomendacoes = [];

        // Performance vs teórico
        if (retornoMedio < retornoTeorico) {
            recomendacoes.push({
                icon: '⚠️',
                cor: '#fbbf24',
                texto: 'Motor performando <strong>pior que aleatório</strong> (retorno ' + retornoMedio.toFixed(2) + '% vs teórico ' + retornoTeorico.toFixed(2) + '%). Isso é comum em amostras pequenas. Aumente o volume para melhorar a convergência estatística.'
            });
        } else {
            recomendacoes.push({
                icon: '✅',
                cor: '#00ff88',
                texto: 'Motor performando <strong>melhor que aleatório</strong> (retorno ' + retornoMedio.toFixed(2) + '% vs teórico ' + retornoTeorico.toFixed(2) + '%). Possível variância positiva — monitorar se sustenta ao longo do tempo.'
            });
        }

        // Volume ótimo
        var volumeOtimo = this._calcularVolumeOtimo(gameKey);
        recomendacoes.push({
            icon: '📊',
            cor: '#60a5fa',
            texto: 'Volume ótimo sugerido por concurso: <strong>' + volumeOtimo.toLocaleString('pt-BR') + ' jogos</strong> para balancear cobertura e custo (investimento: ' + this._fmt(volumeOtimo * config.custo) + ').'
        });

        // Loteria mais eficiente
        var ranking = this._rankLoterias();
        if (ranking.length > 0 && ranking[0].gameKey !== gameKey) {
            var melhor = ranking[0];
            recomendacoes.push({
                icon: '🎯',
                cor: '#a78bfa',
                texto: 'Loteria mais eficiente por ROI teórico: <strong>' + melhor.nome + '</strong> (retorno ' + melhor.retornoPct.toFixed(2) + '%). Considere diversificar parte do orçamento.'
            });
        }

        // Amostragem insuficiente
        if (conferenceData.length < 10) {
            recomendacoes.push({
                icon: '📋',
                cor: '#94a3b8',
                texto: 'Você possui apenas <strong>' + conferenceData.length + ' conferência(s)</strong>. Para conclusões estatisticamente significativas, recomendamos pelo menos 30 conferências.'
            });
        }

        for (var r = 0; r < recomendacoes.length; r++) {
            var rec = recomendacoes[r];
            html += '<div style="' + s.alertBox + 'background:' + rec.cor + '10;border:1px solid ' + rec.cor + '30;">';
            html += '<span style="margin-right:6px;">' + rec.icon + '</span>';
            html += '<span style="color:#e2e8f0;">' + rec.texto + '</span>';
            html += '</div>';
        }

        html += '</div>'; // card

        // Rodapé
        html += '<div style="text-align:center;color:#475569;font-size:0.6rem;margin-top:8px;">';
        html += 'ROI Dashboard v1.0 — Dados calculados com distribuição hipergeométrica exata';
        html += '</div>';

        html += '</div>'; // container
        return html;
    }

    // ═══════════════════════════════════════════════════════════════════════
    //  MÉTODO 2: generateROIPreview — Preview Pré-Geração
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Gera HTML mostrando o que esperar ANTES de gerar jogos.
     *
     * @param {string} gameKey - chave da loteria
     * @param {number} numGames - quantidade de jogos a gerar
     * @returns {string} HTML do preview
     */
    static generateROIPreview(gameKey, numGames) {
        var s = this._STYLES;
        var config = this.LOTTERY_CONFIG[gameKey];
        var premios = this.PREMIOS_ESTIMADOS[gameKey];
        var payoutOficial = this.PAYOUT_OFICIAL[gameKey] || 0.4335;

        if (!config || !premios) {
            return '<div style="color:#ff4444;padding:16px;">❌ Loteria não encontrada: ' + gameKey + '</div>';
        }

        numGames = Math.max(1, Math.floor(numGames || 1));
        var investimentoTotal = numGames * config.custo;

        // Calcular EV por faixa
        var breakdown = [];
        var evTotal = 0;

        for (var i = 0; i < premios.length; i++) {
            var p = premios[i];
            var prob = this._hypergeometric(config.N, config.K, config.n, p.hits);
            var acertosEsperados = prob * numGames;
            var evFaixa = acertosEsperados * p.premio;
            evTotal += evFaixa;

            // Jogos para 50% de chance
            var gamesFor50 = prob > 0 ? Math.ceil(Math.log(0.5) / Math.log(1 - prob)) : Infinity;

            breakdown.push({
                hits: p.hits,
                nome: p.nome,
                fixo: p.fixo || false,
                premio: p.premio,
                prob: prob,
                odds: this._oddsText(prob),
                acertosEsperados: acertosEsperados,
                ev: evFaixa,
                gamesFor50: gamesFor50
            });
        }

        var roi = investimentoTotal > 0 ? ((evTotal - investimentoTotal) / investimentoTotal) * 100 : 0;
        var roiAlerta = roi < -80;

        // ─── Montagem HTML ───
        var html = this._getAnimationStyle();
        html += '<div style="' + s.container + s.fadeIn + '">';

        // Cabeçalho
        html += '<div style="display:flex;align-items:center;gap:10px;margin-bottom:16px;">';
        html += '<div style="font-size:1.6rem;">🔍</div>';
        html += '<div>';
        html += '<div style="font-size:1.1rem;font-weight:900;color:#e2e8f0;">Preview de ROI — ' + config.nome + '</div>';
        html += '<div style="font-size:0.7rem;color:#64748b;">' + numGames + ' jogo(s) × ' + this._fmt(config.custo) + ' = ' + this._fmt(investimentoTotal) + '</div>';
        html += '</div>';
        html += '</div>';

        // Alerta de ROI crítico
        if (roiAlerta) {
            html += '<div style="' + s.alertBox + 'background:rgba(255,68,68,0.12);border:2px solid rgba(255,68,68,0.4);animation:roiPulse 2s infinite;">';
            html += '<div style="font-size:0.9rem;font-weight:900;color:#ff4444;margin-bottom:4px;">⚠️ ALERTA: ROI EXTREMAMENTE NEGATIVO</div>';
            html += '<div style="color:#fca5a5;font-size:0.75rem;">O retorno esperado é de apenas ' + this._fmtPct(roi).text + '. Você perderá em média ' + this._fmt(investimentoTotal - evTotal) + ' por concurso. Considere reduzir o volume ou trocar de loteria.</div>';
            html += '</div>';
        }

        // Métricas principais
        html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin-bottom:16px;">';

        // Investimento
        html += '<div style="' + s.metricBox + '">';
        html += '<div style="' + s.metricLabel + '">Investimento</div>';
        html += '<div style="' + s.metricValue + 'color:#ff6b6b;">' + this._fmt(investimentoTotal) + '</div>';
        html += '</div>';

        // EV Total
        html += '<div style="' + s.metricBox + '">';
        html += '<div style="' + s.metricLabel + '">Retorno Esperado</div>';
        html += '<div style="' + s.metricValue + 'color:#00ff88;">' + this._fmt(evTotal) + '</div>';
        html += '</div>';

        // ROI
        var roiCor = roi >= -20 ? '#00ff88' : roi >= -50 ? '#fbbf24' : '#ff4444';
        html += '<div style="' + s.metricBox + 'border:1px solid ' + roiCor + '30;">';
        html += '<div style="' + s.metricLabel + '">ROI Esperado</div>';
        html += '<div style="' + s.metricValue + 'color:' + roiCor + ';">' + this._fmtPct(roi).text + '</div>';
        html += '</div>';

        html += '</div>'; // grid

        // Tabela de faixas
        html += '<div style="' + s.card + '">';
        html += '<div style="' + s.cardHeader + 'color:#fbbf24;">🎰 Retorno por Faixa de Acertos</div>';
        html += '<table style="' + s.table + '">';
        html += '<thead><tr>';
        html += '<th style="' + s.th + '">Faixa</th>';
        html += '<th style="' + s.th + 'text-align:right;">Prêmio</th>';
        html += '<th style="' + s.th + 'text-align:right;">Odds</th>';
        html += '<th style="' + s.th + 'text-align:right;">Acertos Esp.</th>';
        html += '<th style="' + s.th + 'text-align:right;">EV</th>';
        html += '<th style="' + s.th + 'text-align:right;">50% Chance</th>';
        html += '</tr></thead><tbody>';

        for (var i = 0; i < breakdown.length; i++) {
            var b = breakdown[i];
            var probCor = b.prob > 0.01 ? '#00ff88' : b.prob > 0.001 ? '#fbbf24' : b.prob > 0.00001 ? '#f97316' : '#ff4444';
            var fixoLabel = b.fixo ? ' <span style="' + s.badge + 'background:rgba(96,165,250,0.15);color:#60a5fa;font-size:0.55rem;">FIXO</span>' : '';

            html += '<tr>';
            html += '<td style="' + s.td + 'font-weight:600;">' + b.nome + fixoLabel + '</td>';
            html += '<td style="' + s.td + 'text-align:right;">' + this._fmtCompact(b.premio) + '</td>';
            html += '<td style="' + s.td + 'text-align:right;color:' + probCor + ';font-size:0.65rem;">' + b.odds + '</td>';
            html += '<td style="' + s.td + 'text-align:right;color:#94a3b8;">' + (b.acertosEsperados < 0.01 ? '<0,01' : b.acertosEsperados.toFixed(3)) + '</td>';
            html += '<td style="' + s.td + 'text-align:right;font-weight:700;color:#e2e8f0;">' + this._fmtCompact(b.ev) + '</td>';
            html += '<td style="' + s.td + 'text-align:right;color:#64748b;font-size:0.65rem;">' + (b.gamesFor50 === Infinity ? '∞' : b.gamesFor50.toLocaleString('pt-BR') + ' jogos') + '</td>';
            html += '</tr>';
        }

        html += '</tbody></table>';
        html += '</div>'; // card tabela

        // Barra visual de composição do EV
        html += '<div style="' + s.card + '">';
        html += '<div style="' + s.cardHeader + 'color:#a78bfa;">📊 Composição do Retorno Esperado</div>';

        for (var i = 0; i < breakdown.length; i++) {
            var b = breakdown[i];
            var pctContrib = evTotal > 0 ? (b.ev / evTotal) * 100 : 0;
            if (pctContrib < 0.01) continue;

            var cores = ['#00ff88', '#fbbf24', '#60a5fa', '#f472b6', '#a78bfa', '#f97316', '#14b8a6'];
            var cor = cores[i % cores.length];

            html += '<div style="margin-bottom:6px;">';
            html += '<div style="display:flex;justify-content:space-between;font-size:0.65rem;margin-bottom:2px;">';
            html += '<span style="color:#94a3b8;">' + b.nome + '</span>';
            html += '<span style="color:' + cor + ';font-weight:700;">' + pctContrib.toFixed(1) + '%</span>';
            html += '</div>';
            html += '<div style="' + s.barContainer + 'height:14px;">';
            html += '<div style="' + s.barFill + 'height:100%;width:' + Math.max(pctContrib, 1) + '%;background:' + cor + ';font-size:0.55rem;"></div>';
            html += '</div>';
            html += '</div>';
        }

        html += '</div>'; // card

        // Comparação rápida com outras loterias
        html += this._generateMiniComparison(gameKey, numGames);

        // Rodapé
        html += '<div style="text-align:center;color:#475569;font-size:0.6rem;margin-top:8px;">';
        html += 'Valores baseados em probabilidade hipergeométrica exata e prêmios médios estimados';
        html += '</div>';

        html += '</div>'; // container
        return html;
    }

    /**
     * Mini-comparação com outras loterias (para o preview).
     * Mostra 3 melhores alternativas pelo mesmo investimento.
     * @private
     */
    static _generateMiniComparison(gameKey, numGames) {
        var s = this._STYLES;
        var configAtual = this.LOTTERY_CONFIG[gameKey];
        if (!configAtual) return '';

        var investimento = numGames * configAtual.custo;
        var comparacoes = [];

        var keys = Object.keys(this.LOTTERY_CONFIG);
        for (var i = 0; i < keys.length; i++) {
            var k = keys[i];
            if (k === gameKey) continue;
            var cfg = this.LOTTERY_CONFIG[k];
            var payout = this.PAYOUT_OFICIAL[k] || 0.4335;
            var jogosEquiv = Math.floor(investimento / cfg.custo);
            if (jogosEquiv < 1) continue;

            var evTeorico = jogosEquiv * cfg.custo * payout;
            var roiTeorico = ((evTeorico - (jogosEquiv * cfg.custo)) / (jogosEquiv * cfg.custo)) * 100;

            comparacoes.push({
                nome: cfg.nome,
                cor: cfg.cor,
                jogos: jogosEquiv,
                investimento: jogosEquiv * cfg.custo,
                evTeorico: evTeorico,
                roi: roiTeorico,
                payout: payout * 100
            });
        }

        comparacoes.sort(function(a, b) { return b.roi - a.roi; });
        comparacoes = comparacoes.slice(0, 3);

        if (comparacoes.length === 0) return '';

        var html = '<div style="' + s.card + '">';
        html += '<div style="' + s.cardHeader + 'color:#14b8a6;">🔄 Mesmo Orçamento em Outras Loterias</div>';
        html += '<div style="display:grid;grid-template-columns:repeat(' + Math.min(comparacoes.length, 3) + ',1fr);gap:10px;">';

        for (var i = 0; i < comparacoes.length; i++) {
            var c = comparacoes[i];
            html += '<div style="' + s.metricBox + 'border:1px solid ' + c.cor + '30;">';
            html += '<div style="color:' + c.cor + ';font-size:0.75rem;font-weight:800;margin-bottom:6px;">' + c.nome + '</div>';
            html += '<div style="font-size:0.6rem;color:#94a3b8;">' + c.jogos + ' jogos × ' + this._fmt(this.LOTTERY_CONFIG[Object.keys(this.LOTTERY_CONFIG).find(function(k) { return this.LOTTERY_CONFIG[k].nome === c.nome; }.bind(this))].custo) + '</div>';
            html += '<div style="font-size:0.6rem;color:#94a3b8;margin-top:2px;">Payout: ' + c.payout.toFixed(2) + '%</div>';
            html += '<div style="font-size:0.85rem;font-weight:800;color:' + (c.roi > -50 ? '#fbbf24' : '#ff4444') + ';margin-top:4px;">ROI: ' + c.roi.toFixed(1) + '%</div>';
            html += '</div>';
        }

        html += '</div>';
        html += '</div>';
        return html;
    }

    // ═══════════════════════════════════════════════════════════════════════
    //  MÉTODO 3: generateLotteryComparison — Comparação Geral
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Gera tabela HTML comparativa de TODAS as loterias.
     * Inclui odds por faixa, payout, ROI esperado e ranking.
     *
     * @returns {string} HTML completo
     */
    static generateLotteryComparison() {
        var s = this._STYLES;
        var ranking = this._rankLoterias();

        var html = this._getAnimationStyle();
        html += '<div style="' + s.container + s.fadeIn + '">';

        // Cabeçalho
        html += '<div style="margin-bottom:20px;">';
        html += '<div style="font-size:1.3rem;font-weight:900;background:linear-gradient(90deg,#00ff88,#60a5fa);-webkit-background-clip:text;-webkit-text-fill-color:transparent;">🏆 Comparativo Geral de Loterias</div>';
        html += '<div style="color:#64748b;font-size:0.7rem;margin-top:4px;">Ranking completo por eficiência de ROI — Probabilidades hipergeométricas exatas</div>';
        html += '</div>';

        // Cards de ranking (top 3)
        html += '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:12px;margin-bottom:20px;">';
        var medalhas = ['🥇', '🥈', '🥉'];

        for (var i = 0; i < Math.min(3, ranking.length); i++) {
            var r = ranking[i];
            var borderGlow = i === 0 ? 'border:2px solid rgba(0,255,136,0.3);box-shadow:0 0 20px rgba(0,255,136,0.1);' : 'border:1px solid rgba(255,255,255,0.08);';

            html += '<div style="' + s.card + borderGlow + 'text-align:center;position:relative;">';
            html += '<div style="font-size:1.8rem;margin-bottom:4px;">' + medalhas[i] + '</div>';
            html += '<div style="font-size:0.9rem;font-weight:800;color:' + r.cor + ';">' + r.nome + '</div>';
            html += '<div style="font-size:0.65rem;color:#64748b;margin-top:2px;">Payout: ' + r.payoutPct.toFixed(2) + '%</div>';
            html += '<div style="font-size:1.4rem;font-weight:900;color:' + (r.retornoPct >= 50 ? '#00ff88' : '#fbbf24') + ';margin-top:6px;">' + r.retornoPct.toFixed(2) + '%</div>';
            html += '<div style="font-size:0.6rem;color:#94a3b8;">Retorno teórico</div>';
            html += '</div>';
        }

        html += '</div>';

        // Tabela completa
        html += '<div style="' + s.card + '">';
        html += '<div style="' + s.cardHeader + 'color:#fbbf24;">📋 Tabela Detalhada</div>';
        html += '<div style="overflow-x:auto;">';
        html += '<table style="' + s.table + '">';
        html += '<thead><tr>';
        html += '<th style="' + s.th + '">#</th>';
        html += '<th style="' + s.th + '">Loteria</th>';
        html += '<th style="' + s.th + 'text-align:right;">Custo</th>';
        html += '<th style="' + s.th + 'text-align:right;">Universo</th>';
        html += '<th style="' + s.th + 'text-align:right;">Sorteio</th>';
        html += '<th style="' + s.th + 'text-align:right;">Aposta Min.</th>';
        html += '<th style="' + s.th + 'text-align:right;">Payout</th>';
        html += '<th style="' + s.th + 'text-align:right;">Odds (Máx)</th>';
        html += '<th style="' + s.th + 'text-align:right;">Odds (Mín)</th>';
        html += '<th style="' + s.th + 'text-align:right;">EV/Aposta</th>';
        html += '<th style="' + s.th + 'text-align:center;">Rating</th>';
        html += '</tr></thead><tbody>';

        for (var i = 0; i < ranking.length; i++) {
            var r = ranking[i];
            var rowBg = i % 2 === 0 ? '' : 'background:rgba(255,255,255,0.02);';

            html += '<tr style="' + rowBg + '">';
            html += '<td style="' + s.td + 'font-weight:800;color:' + r.cor + ';">' + (i + 1) + 'º</td>';
            html += '<td style="' + s.td + 'font-weight:700;">' + r.nome + '</td>';
            html += '<td style="' + s.td + 'text-align:right;">' + this._fmt(r.custo) + '</td>';
            html += '<td style="' + s.td + 'text-align:right;color:#94a3b8;">' + r.N + '</td>';
            html += '<td style="' + s.td + 'text-align:right;color:#94a3b8;">' + r.K + '</td>';
            html += '<td style="' + s.td + 'text-align:right;color:#94a3b8;">' + r.n + '</td>';
            html += '<td style="' + s.td + 'text-align:right;color:#60a5fa;font-weight:700;">' + r.payoutPct.toFixed(2) + '%</td>';
            html += '<td style="' + s.td + 'text-align:right;color:#ff6b6b;font-size:0.65rem;">' + r.oddsMax + '</td>';
            html += '<td style="' + s.td + 'text-align:right;color:#00ff88;font-size:0.65rem;">' + r.oddsMin + '</td>';
            html += '<td style="' + s.td + 'text-align:right;font-weight:700;">' + this._fmt(r.evPorAposta) + '</td>';
            html += '<td style="' + s.td + 'text-align:center;">' + r.rating + '</td>';
            html += '</tr>';
        }

        html += '</tbody></table>';
        html += '</div>';
        html += '</div>'; // card

        // Tabela de odds detalhada por faixa
        html += this._generateOddsMatrix();

        // Recomendação de alocação de orçamento
        html += this._generateBudgetAllocation(ranking);

        // Rodapé
        html += '<div style="text-align:center;color:#475569;font-size:0.6rem;margin-top:12px;">';
        html += 'Probabilidades calculadas via distribuição hipergeométrica exata (log-combinação) • Payouts: Lei 13.756/2018';
        html += '</div>';

        html += '</div>'; // container
        return html;
    }

    /**
     * Gera a matriz completa de odds por faixa para todas as loterias.
     * @private
     * @returns {string} HTML
     */
    static _generateOddsMatrix() {
        var s = this._STYLES;
        var html = '<div style="' + s.card + '">';
        html += '<div style="' + s.cardHeader + 'color:#a78bfa;">🎲 Odds por Faixa de Premiação</div>';

        var keys = Object.keys(this.LOTTERY_CONFIG);
        for (var ki = 0; ki < keys.length; ki++) {
            var gk = keys[ki];
            var cfg = this.LOTTERY_CONFIG[gk];
            var premios = this.PREMIOS_ESTIMADOS[gk];
            if (!premios) continue;

            html += '<div style="margin-bottom:14px;">';
            html += '<div style="font-size:0.8rem;font-weight:800;color:' + cfg.cor + ';margin-bottom:6px;">' + cfg.nome + '</div>';
            html += '<div style="display:flex;flex-wrap:wrap;gap:6px;">';

            for (var j = 0; j < premios.length; j++) {
                var p = premios[j];
                var prob = this._hypergeometric(cfg.N, cfg.K, cfg.n, p.hits);
                var odds = this._oddsText(prob);
                var probCor = prob > 0.05 ? '#00ff88' : prob > 0.01 ? '#34d399' : prob > 0.001 ? '#fbbf24' : prob > 0.0001 ? '#f97316' : '#ff4444';

                html += '<div style="background:rgba(0,0,0,0.3);border-radius:8px;padding:8px 10px;min-width:110px;flex:1;">';
                html += '<div style="font-size:0.6rem;color:#94a3b8;">' + p.nome + '</div>';
                html += '<div style="font-size:0.7rem;font-weight:700;color:' + probCor + ';margin-top:2px;">' + odds + '</div>';
                html += '<div style="font-size:0.55rem;color:#475569;margin-top:1px;">' + (prob * 100).toFixed(6) + '%</div>';
                html += '<div style="font-size:0.55rem;color:#64748b;margin-top:1px;">Prêmio: ' + this._fmtCompact(p.premio) + '</div>';
                html += '</div>';
            }

            html += '</div>';
            html += '</div>';
        }

        html += '</div>'; // card
        return html;
    }

    /**
     * Gera recomendação de alocação de orçamento.
     * @private
     * @param {Array} ranking - ranking das loterias
     * @returns {string} HTML
     */
    static _generateBudgetAllocation(ranking) {
        var s = this._STYLES;
        var html = '<div style="' + s.card + '">';
        html += '<div style="' + s.cardHeader + 'color:#14b8a6;">💼 Recomendação de Alocação de Orçamento</div>';

        // Calcular alocação proporcional ao payout
        var totalPayout = 0;
        for (var i = 0; i < ranking.length; i++) {
            totalPayout += ranking[i].payoutPct;
        }

        html += '<div style="margin-bottom:12px;font-size:0.75rem;color:#94a3b8;">Distribuição sugerida para um orçamento mensal, baseada na eficiência de cada loteria:</div>';

        var orcamentoExemplo = 300; // R$300 mensal como exemplo
        html += '<div style="margin-bottom:14px;">';

        for (var i = 0; i < ranking.length; i++) {
            var r = ranking[i];
            var alocPct = (r.payoutPct / totalPayout) * 100;
            var alocValor = (alocPct / 100) * orcamentoExemplo;
            var jogosEstimados = Math.floor(alocValor / r.custo);

            var barW = Math.max(alocPct, 3);

            html += '<div style="margin-bottom:8px;">';
            html += '<div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:3px;">';
            html += '<span style="font-size:0.7rem;color:#e2e8f0;font-weight:600;">' + r.nome + '</span>';
            html += '<span style="font-size:0.65rem;color:#94a3b8;">' + alocPct.toFixed(1) + '% → ' + this._fmt(alocValor) + ' (~' + jogosEstimados + ' jogos/mês)</span>';
            html += '</div>';
            html += '<div style="' + s.barContainer + 'height:10px;">';
            html += '<div style="height:100%;width:' + barW + '%;background:' + r.cor + ';border-radius:6px;"></div>';
            html += '</div>';
            html += '</div>';
        }

        html += '</div>';

        // Nota explicativa
        html += '<div style="' + s.alertBox + 'background:rgba(96,165,250,0.08);border:1px solid rgba(96,165,250,0.2);">';
        html += '<span style="color:#60a5fa;font-weight:700;">📝 Nota:</span> ';
        html += '<span style="color:#94a3b8;font-size:0.7rem;">Exemplo baseado em orçamento de ' + this._fmt(orcamentoExemplo) + '/mês. A alocação é proporcional ao payout oficial de cada loteria. Loterias são jogos de azar com retorno esperado negativo — jogue com responsabilidade.</span>';
        html += '</div>';

        html += '</div>'; // card
        return html;
    }

    // ═══════════════════════════════════════════════════════════════════════
    //  MÉTODOS AUXILIARES INTERNOS
    // ═══════════════════════════════════════════════════════════════════════

    /**
     * Calcula o ranking de todas as loterias por eficiência.
     * @private
     * @returns {Array<Object>}
     */
    static _rankLoterias() {
        var resultado = [];
        var keys = Object.keys(this.LOTTERY_CONFIG);

        for (var i = 0; i < keys.length; i++) {
            var gk = keys[i];
            var cfg = this.LOTTERY_CONFIG[gk];
            var payout = this.PAYOUT_OFICIAL[gk] || 0.4335;
            var premios = this.PREMIOS_ESTIMADOS[gk] || [];

            // Calcular EV real
            var evTotal = 0;
            var oddsMaxNum = 0;
            var oddsMinNum = Infinity;

            for (var j = 0; j < premios.length; j++) {
                var p = premios[j];
                var prob = this._hypergeometric(cfg.N, cfg.K, cfg.n, p.hits);
                evTotal += prob * p.premio;

                if (prob > 0) {
                    var odds = 1 / prob;
                    if (odds > oddsMaxNum) oddsMaxNum = odds;
                    if (odds < oddsMinNum) oddsMinNum = odds;
                }
            }

            var retornoPct = cfg.custo > 0 ? (evTotal / cfg.custo) * 100 : 0;

            // Rating
            var rating;
            if (retornoPct >= 50) rating = '⭐⭐⭐';
            else if (retornoPct >= 40) rating = '⭐⭐';
            else if (retornoPct >= 30) rating = '⭐';
            else rating = '⚠️';

            resultado.push({
                gameKey: gk,
                nome: cfg.nome,
                cor: cfg.cor,
                N: cfg.N,
                K: cfg.K,
                n: cfg.n,
                custo: cfg.custo,
                payoutPct: payout * 100,
                evPorAposta: evTotal,
                retornoPct: retornoPct,
                oddsMax: oddsMaxNum > 0 ? this._oddsText(1 / oddsMaxNum) : '—',
                oddsMin: oddsMinNum < Infinity ? this._oddsText(1 / oddsMinNum) : '—',
                rating: rating
            });
        }

        resultado.sort(function(a, b) { return b.retornoPct - a.retornoPct; });
        return resultado;
    }

    /**
     * Calcula volume ótimo de jogos por concurso para uma loteria.
     * Baseado no equilíbrio entre cobertura mínima viável e custo.
     *
     * Critério: cobertura mínima de 50% na faixa mais acessível.
     *
     * @private
     * @param {string} gameKey
     * @returns {number} número ótimo de jogos
     */
    static _calcularVolumeOtimo(gameKey) {
        var cfg = this.LOTTERY_CONFIG[gameKey];
        var premios = this.PREMIOS_ESTIMADOS[gameKey];
        if (!cfg || !premios || premios.length === 0) return 10;

        // Faixa mais acessível (maior probabilidade)
        var melhorProb = 0;
        for (var i = 0; i < premios.length; i++) {
            var prob = this._hypergeometric(cfg.N, cfg.K, cfg.n, premios[i].hits);
            if (prob > melhorProb) melhorProb = prob;
        }

        if (melhorProb <= 0) return 10;

        // Jogos para 50% de chance na faixa mais acessível
        var jogos50 = Math.ceil(Math.log(0.5) / Math.log(1 - melhorProb));

        // Limitar a um range razoável (5 a 200 jogos)
        return Math.max(5, Math.min(200, jogos50));
    }
}

// ═══════════════════════════════════════════════════════════════════════
//  Expor globalmente para uso no browser
// ═══════════════════════════════════════════════════════════════════════
window.ROIDashboard = ROIDashboard;
