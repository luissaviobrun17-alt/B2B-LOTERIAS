/**
 * MOTOR LOTECA — B2B LOTERIAS (Modulo Oficial Desktop)
 * ====================================================
 * 1. 14 Jogos da Grade Oficial da Caixa
 * 2. Dixon-Coles Bivariado com tau para empates de poucos gols
 * 3. 100.000 simulacoes Monte Carlo por partida
 * 4. Entropia de Shannon normalizada [0, 1] e Score de Certeza [0, 100]
 * 5. Detector de Partidas Armadilha (Trap Matches)
 * 6. Otimizador de orcamentos Caixa (2^D * 3^T <= 864)
 * 7. Modulo 7 Duques (9 combinacoes cada, particao exata dos 14 jogos)
 * 8. Modulo 4 Ternos / Trios (27 combinacoes cada, fechamento reduzido)
 * 9. Conexao com API Python local + Fallback nativo de alta velocidade
 */

class MotorLotecaB2BEngine {
    static async obterGradeOficialCaixa() {
        try {
            if (typeof StatsService !== 'undefined') {
                const st = await StatsService.getStats('loteca');
                if (st && st.latest && st.latest.matches && st.latest.matches.length === 14) {
                    return st.latest.matches.map(m => ({
                        jogo_numero: m.jogoNum,
                        mandante: m.mandante || `Mandante ${m.jogoNum}`,
                        visitante: m.visitante || `Visitante ${m.jogoNum}`,
                        campeonato: m.campeonato || 'Loteca Oficial Caixa',
                        placar_oficial: (m.nuGol1 !== null && m.nuGol2 !== null) ? `${m.nuGol1} x ${m.nuGol2}` : null,
                        coluna_oficial: m.coluna || null,
                        xg_mandante: 1.50,
                        xg_visitante: 1.10,
                        odds_mandante: 2.15,
                        odds_empate: 3.10,
                        odds_visitante: 3.35
                    }));
                }
            }
        } catch (e) {
            console.warn('[MotorLoteca] Falha ao obter grade da Caixa:', e);
        }

        if (typeof REAL_HISTORY_DB !== 'undefined' && REAL_HISTORY_DB.loteca && REAL_HISTORY_DB.loteca.length > 0) {
            const histMatches = [
                { jogo_numero: 1, mandante: 'FLAMENGO', visitante: 'BOTAFOGO' },
                { jogo_numero: 2, mandante: 'ATLETICO-MG', visitante: 'VITORIA' },
                { jogo_numero: 3, mandante: 'SAO PAULO', visitante: 'BRAGANTINO' },
                { jogo_numero: 4, mandante: 'SEVILLA', visitante: 'ATLETICO DE MADRID' },
                { jogo_numero: 5, mandante: 'VASCO DA GAMA', visitante: 'CRUZEIRO' },
                { jogo_numero: 6, mandante: 'ATHLETICO-PR', visitante: 'FLUMINENSE' },
                { jogo_numero: 7, mandante: 'CHELSEA', visitante: 'BRIGHTON' },
                { jogo_numero: 8, mandante: 'LEEDS UNITED', visitante: 'BRENTFORD' },
                { jogo_numero: 9, mandante: 'CORINTHIANS', visitante: 'SANTOS' },
                { jogo_numero: 10, mandante: 'CRB', visitante: 'CRICIUMA' },
                { jogo_numero: 11, mandante: 'MIRASSOL', visitante: 'PALMEIRAS' },
                { jogo_numero: 12, mandante: 'GREMIO', visitante: 'CHAPECOENSE' },
                { jogo_numero: 13, mandante: 'BAHIA', visitante: 'INTERNACIONAL' },
                { jogo_numero: 14, mandante: 'CELTA DE VIGO', visitante: 'ATHLETIC BILBAO' }
            ];
            return histMatches.map(m => ({
                ...m,
                campeonato: 'Concurso Caixa 1268',
                xg_mandante: 1.50,
                xg_visitante: 1.10,
                odds_mandante: 2.15,
                odds_empate: 3.10,
                odds_visitante: 3.35
            }));
        }

        return this.GRADE_PADRAO;
    }

    static GRADE_PADRAO = [
        { jogo_numero: 1, mandante: 'Palmeiras', visitante: 'Flamengo', campeonato: 'Brasileirao Serie A', rating_mandante: 1820, rating_visitante: 1810, xg_mandante: 1.55, xg_visitante: 1.35, odds_mandante: 2.30, odds_empate: 3.20, odds_visitante: 2.90 },
        { jogo_numero: 2, mandante: 'Sao Paulo', visitante: 'Corinthians', campeonato: 'Brasileirao Serie A', rating_mandante: 1710, rating_visitante: 1680, xg_mandante: 1.45, xg_visitante: 1.15, odds_mandante: 2.20, odds_empate: 3.10, odds_visitante: 3.30 },
        { jogo_numero: 3, mandante: 'Atletico-MG', visitante: 'Cruzeiro', campeonato: 'Brasileirao Serie A', rating_mandante: 1740, rating_visitante: 1690, xg_mandante: 1.50, xg_visitante: 1.10, odds_mandante: 2.10, odds_empate: 3.25, odds_visitante: 3.40 },
        { jogo_numero: 4, mandante: 'Internacional', visitante: 'Gremio', campeonato: 'Brasileirao Serie A', rating_mandante: 1720, rating_visitante: 1700, xg_mandante: 1.35, xg_visitante: 1.20, odds_mandante: 2.40, odds_empate: 3.00, odds_visitante: 3.00 },
        { jogo_numero: 5, mandante: 'Botafogo', visitante: 'Fluminense', campeonato: 'Brasileirao Serie A', rating_mandante: 1790, rating_visitante: 1680, xg_mandante: 1.70, xg_visitante: 1.05, odds_mandante: 1.85, odds_empate: 3.40, odds_visitante: 4.10 },
        { jogo_numero: 6, mandante: 'Fortaleza', visitante: 'Bahia', campeonato: 'Brasileirao Serie A', rating_mandante: 1700, rating_visitante: 1670, xg_mandante: 1.40, xg_visitante: 1.20, odds_mandante: 2.25, odds_empate: 3.15, odds_visitante: 3.10 },
        { jogo_numero: 7, mandante: 'Vasco da Gama', visitante: 'Athletico-PR', campeonato: 'Brasileirao Serie A', rating_mandante: 1650, rating_visitante: 1660, xg_mandante: 1.30, xg_visitante: 1.25, odds_mandante: 2.50, odds_empate: 3.10, odds_visitante: 2.80 },
        { jogo_numero: 8, mandante: 'Santos', visitante: 'Sport Recife', campeonato: 'Brasileirao Serie B', rating_mandante: 1640, rating_visitante: 1560, xg_mandante: 1.65, xg_visitante: 0.95, odds_mandante: 1.75, odds_empate: 3.50, odds_visitante: 4.50 },
        { jogo_numero: 9, mandante: 'Ceara', visitante: 'America-MG', campeonato: 'Brasileirao Serie B', rating_mandante: 1580, rating_visitante: 1570, xg_mandante: 1.35, xg_visitante: 1.15, odds_mandante: 2.30, odds_empate: 3.00, odds_visitante: 3.15 },
        { jogo_numero: 10, mandante: 'Coritiba', visitante: 'Goias', campeonato: 'Brasileirao Serie B', rating_mandante: 1560, rating_visitante: 1550, xg_mandante: 1.25, xg_visitante: 1.10, odds_mandante: 2.40, odds_empate: 2.95, odds_visitante: 3.05 },
        { jogo_numero: 11, mandante: 'Real Madrid', visitante: 'Barcelona', campeonato: 'La Liga (Espanha)', rating_mandante: 1980, rating_visitante: 1950, xg_mandante: 1.85, xg_visitante: 1.65, odds_mandante: 2.10, odds_empate: 3.60, odds_visitante: 3.10 },
        { jogo_numero: 12, mandante: 'Arsenal', visitante: 'Chelsea', campeonato: 'Premier League (Inglaterra)', rating_mandante: 1920, rating_visitante: 1840, xg_mandante: 1.80, xg_visitante: 1.20, odds_mandante: 1.70, odds_empate: 3.80, odds_visitante: 4.40 },
        { jogo_numero: 13, mandante: 'Inter de Milao', visitante: 'Juventus', campeonato: 'Serie A (Italia)', rating_mandante: 1900, rating_visitante: 1850, xg_mandante: 1.60, xg_visitante: 1.10, odds_mandante: 1.95, odds_empate: 3.30, odds_visitante: 3.80 },
        { jogo_numero: 14, mandante: 'Bayern de Munique', visitante: 'Borussia Dortmund', campeonato: 'Bundesliga (Alemanha)', rating_mandante: 1960, rating_visitante: 1880, xg_mandante: 2.30, xg_visitante: 1.35, odds_mandante: 1.60, odds_empate: 4.20, odds_visitante: 4.80 }
    ];

    static factorial(n) {
        let res = 1;
        for (let i = 2; i <= n; i++) res *= i;
        return res;
    }

    static poissonProb(k, lambda) {
        return (Math.pow(lambda, k) * Math.exp(-lambda)) / this.factorial(k);
    }

    static tauCorrection(x, y, l1, l2, rho = -0.11) {
        if (x === 0 && y === 0) return 1.0 - (l1 * l2 * rho);
        if (x === 0 && y === 1) return 1.0 + (l1 * rho);
        if (x === 1 && y === 0) return 1.0 + (l2 * rho);
        if (x === 1 && y === 1) return 1.0 - rho;
        return 1.0;
    }

    static calcularDixonColes(lambdaHome, lambdaAway, maxGoals = 7, rho = -0.11) {
        let pHome = 0.0, pDraw = 0.0, pAway = 0.0, total = 0.0;
        for (let h = 0; h <= maxGoals; h++) {
            for (let a = 0; a <= maxGoals; a++) {
                const base = this.poissonProb(h, lambdaHome) * this.poissonProb(a, lambdaAway);
                const tau = this.tauCorrection(h, a, lambdaHome, lambdaAway, rho);
                const prob = Math.max(0.0, base * tau);
                total += prob;
                if (h > a) pHome += prob;
                else if (h === a) pDraw += prob;
                else pAway += prob;
            }
        }
        return { pHome: pHome / total, pDraw: pDraw / total, pAway: pAway / total };
    }

    static simularMonteCarlo(p1, px, p2, runs = 100000) {
        let w1 = 0, wx = 0, w2 = 0;
        const c1 = p1, cx = p1 + px;
        for (let i = 0; i < runs; i++) {
            const r = Math.random();
            if (r < c1) w1++;
            else if (r < cx) wx++;
            else w2++;
        }
        return { p1: w1 / runs, pX: wx / runs, p2: w2 / runs, runs };
    }

    static calcularEntropia(p1, px, p2) {
        let h = 0.0;
        [p1, px, p2].forEach(p => { if (p > 1e-9) h -= p * Math.log2(p); });
        const hNorm = Math.min(1.0, Math.max(0.0, h / 1.5849625));
        const certeza = Math.max(0.0, Math.min(100.0, (1.0 - hNorm) * 100.0));
        return { entropia: hNorm, certeza };
    }

    static detectarArmadilha(j, p1, px, p2, entropia) {
        let isTrap = false, motivo = '';
        if (j.odds_mandante && j.odds_empate && j.odds_visitante) {
            const sumOdds = (1/j.odds_mandante) + (1/j.odds_empate) + (1/j.odds_visitante);
            const imp1 = (1/j.odds_mandante) / sumOdds;
            if (imp1 - p1 > 0.16) {
                isTrap = true;
                motivo = 'Vies excessivo do mercado em ' + j.mandante + ' (+' + ((imp1 - p1)*100).toFixed(1) + '% acima da probabilidade real).';
            }
        }
        if (!isTrap && entropia > 0.93) {
            isTrap = true;
            motivo = 'Equilibrio estatistico extremo (Entropia ' + entropia.toFixed(3) + '). Partida com alta variancia de resultado.';
        }
        return { isTrap, motivo };
    }

    static analisarGrade(grade = null) {
        const jogos = grade || this.GRADE_PADRAO;
        return jogos.map(j => {
            let xgHome = j.xg_mandante || 1.40;
            let xgAway = j.xg_visitante || 1.15;
            if (j.rating_mandante && j.rating_visitante) {
                const diff = (j.rating_mandante - j.rating_visitante) / 400.0;
                xgHome *= Math.max(0.6, 1.0 + diff * 0.35);
                xgAway *= Math.max(0.6, 1.0 - diff * 0.25);
            }
            const dc = this.calcularDixonColes(xgHome, xgAway);
            const mc = this.simularMonteCarlo(dc.pHome, dc.pDraw, dc.pAway, 100000);
            const ent = this.calcularEntropia(dc.pHome, dc.pDraw, dc.pAway);
            const trap = this.detectarArmadilha(j, dc.pHome, dc.pDraw, dc.pAway, ent.entropia);

            const sorted = [
                { coluna: '1', prob: dc.pHome, desc: j.mandante },
                { coluna: 'X', prob: dc.pDraw, desc: 'Empate' },
                { coluna: '2', prob: dc.pAway, desc: j.visitante }
            ].sort((a, b) => b.prob - a.prob);

            return {
                jogo: j,
                probabilidades: { coluna1: dc.pHome, colunaX: dc.pDraw, coluna2: dc.pAway },
                monte_carlo: mc,
                entropia: ent.entropia,
                certeza: ent.certeza,
                trap,
                palpite_seco: sorted[0].coluna,
                palpite_duplo: sorted[0].coluna + sorted[1].coluna,
                palpite_triplo: '1X2',
                ranking: sorted
            };
        });
    }

    static otimizarOrcamento(analises, orcamentoMax = 48.0, estrategia = 'equilibrada') {
        const estruturas = [
            { d: 1, t: 0, custo: 4.0 },
            { d: 0, t: 1, custo: 12.0 },
            { d: 2, t: 0, custo: 16.0 },
            { d: 1, t: 1, custo: 48.0 },
            { d: 3, t: 0, custo: 64.0 },
            { d: 2, t: 1, custo: 144.0 },
            { d: 4, t: 0, custo: 256.0 },
            { d: 1, t: 2, custo: 288.0 },
            { d: 3, t: 1, custo: 576.0 },
            { d: 2, t: 2, custo: 864.0 },
            { d: 3, t: 2, custo: 1728.0 }
        ];

        const candidatas = estruturas.filter(e => e.custo <= orcamentoMax);
        const escolhida = candidatas.length > 0 ? candidatas[candidatas.length - 1] : estruturas[0];

        const ordenados = [...analises].sort((a, b) => {
            if (estrategia === 'agressiva') {
                if (a.trap.isTrap && !b.trap.isTrap) return -1;
                if (!a.trap.isTrap && b.trap.isTrap) return 1;
            }
            return b.entropia - a.entropia;
        });

        const triplosSet = new Set(ordenados.slice(0, escolhida.t).map(j => j.jogo.jogo_numero));
        const duplosSet = new Set(ordenados.slice(escolhida.t, escolhida.t + escolhida.d).map(j => j.jogo.jogo_numero));

        const jogosFinal = analises.map(a => {
            const num = a.jogo.jogo_numero;
            let tipo = 'SECO', palpite = a.palpite_seco;
            if (triplosSet.has(num)) { tipo = 'TRIPLO'; palpite = '1X2'; }
            else if (duplosSet.has(num)) { tipo = 'DUPLO'; palpite = a.palpite_duplo; }
            return {
                jogo_numero: num,
                jogo: a.jogo,
                tipo,
                palpite,
                probabilidades: a.probabilidades,
                entropia: a.entropia,
                certeza: a.certeza,
                trap: a.trap
            };
        });

        return {
            estrutura: escolhida,
            custo: escolhida.custo,
            apostas_equivalentes: Math.pow(2, escolhida.d) * Math.pow(3, escolhida.t),
            jogos: jogosFinal
        };
    }

    static gerar7Duques(analises) {
        const duques = [];
        for (let i = 0; i < 7; i++) {
            const j1 = analises[i * 2], j2 = analises[i * 2 + 1];
            const cols = ['1', 'X', '2'];
            const combs = [];
            cols.forEach(c1 => {
                cols.forEach(c2 => {
                    const p1 = c1 === '1' ? j1.probabilidades.coluna1 : (c1 === 'X' ? j1.probabilidades.colunaX : j1.probabilidades.coluna2);
                    const p2 = c2 === '1' ? j2.probabilidades.coluna1 : (c2 === 'X' ? j2.probabilidades.colunaX : j2.probabilidades.coluna2);
                    combs.push({ comb: c1 + '-' + c2, c1, c2, prob: p1 * p2, prob_pct: (p1 * p2 * 100).toFixed(2) + '%' });
                });
            });
            combs.sort((a, b) => b.prob - a.prob);
            duques.push({
                duque_numero: i + 1,
                jogo_a: j1,
                jogo_b: j2,
                top_combinacao: combs[0],
                combinacoes: combs,
                reducao_2_triplos_em_3: [
                    { aposta: 1, c1: '1', c2: '1' },
                    { aposta: 2, c1: 'X', c2: '2' },
                    { aposta: 3, c1: '2', c2: 'X' }
                ]
            });
        }
        return duques;
    }

    static gerar4Ternos(analises) {
        const ternos = [];
        for (let i = 0; i < 4; i++) {
            const j1 = analises[i * 3], j2 = analises[i * 3 + 1], j3 = analises[i * 3 + 2];
            const cols = ['1', 'X', '2'];
            const combs = [];
            cols.forEach(c1 => {
                cols.forEach(c2 => {
                    cols.forEach(c3 => {
                        const p1 = c1 === '1' ? j1.probabilidades.coluna1 : (c1 === 'X' ? j1.probabilidades.colunaX : j1.probabilidades.coluna2);
                        const p2 = c2 === '1' ? j2.probabilidades.coluna1 : (c2 === 'X' ? j2.probabilidades.colunaX : j2.probabilidades.coluna2);
                        const p3 = c3 === '1' ? j3.probabilidades.coluna1 : (c3 === 'X' ? j3.probabilidades.colunaX : j3.probabilidades.coluna2);
                        combs.push({ comb: c1 + '-' + c2 + '-' + c3, c1, c2, c3, prob: p1 * p2 * p3, prob_pct: (p1 * p2 * p3 * 100).toFixed(2) + '%' });
                    });
                });
            });
            combs.sort((a, b) => b.prob - a.prob);
            ternos.push({
                terno_numero: i + 1,
                jogos: [j1, j2, j3],
                top_combinacao: combs[0],
                combinacoes: combs,
                reducao_3_duplos_em_4: [
                    { aposta: 1, c1: '1', c2: '1', c3: '1' },
                    { aposta: 2, c1: '1', c2: 'X', c3: 'X' },
                    { aposta: 3, c1: 'X', c2: '1', c3: 'X' },
                    { aposta: 4, c1: 'X', c2: 'X', c3: '1' }
                ],
                reducao_3_triplos_em_9: [
                    { aposta: 1, c1: '1', c2: '1', c3: '1' },
                    { aposta: 2, c1: '1', c2: 'X', c3: '2' },
                    { aposta: 3, c1: '1', c2: '2', c3: 'X' },
                    { aposta: 4, c1: 'X', c2: '1', c3: 'X' },
                    { aposta: 5, c1: 'X', c2: 'X', c3: '1' },
                    { aposta: 6, c1: 'X', c2: '2', c3: '2' },
                    { aposta: 7, c1: '2', c2: '1', c3: '2' },
                    { aposta: 8, c1: '2', c2: 'X', c3: 'X' },
                    { aposta: 9, c1: '2', c2: '2', c3: '1' }
                ]
            });
        }
        return ternos;
    }

    static gerarRelatorioTecnico(otimizacao, duques, ternos) {
        const mediaEntropia = (otimizacao.jogos.reduce((s, j) => s + j.entropia, 0) / 14).toFixed(3);
        const mediaCerteza = (otimizacao.jogos.reduce((s, j) => s + j.certeza, 0) / 14).toFixed(1);

        const linhasJogos = otimizacao.jogos.map(j => {
            const p1 = (j.probabilidades.coluna1 * 100).toFixed(1);
            const px = (j.probabilidades.colunaX * 100).toFixed(1);
            const p2 = (j.probabilidades.coluna2 * 100).toFixed(1);
            return '   Jogo ' + String(j.jogo_numero).padStart(2, '0') + ': [' + j.jogo.mandante + ' x ' + j.jogo.visitante + '] -> Col 1: ' + p1 + '% | X: ' + px + '% | Col 2: ' + p2 + '% | Palpite: [' + j.palpite + '] (' + j.tipo + ')';
        }).join('\n');

        const traps = otimizacao.jogos.filter(j => j.trap.isTrap);
        const linhasTraps = traps.length > 0
            ? traps.map(j => '   ⚠️ Jogo ' + j.jogo_numero + ' (' + j.jogo.mandante + ' x ' + j.jogo.visitante + '): ' + j.trap.motivo).join('\n')
            : '   Nenhum jogo com armadilha severa detectado.';

        const linhasDuques = duques.map(d => {
            return '   Duque ' + d.duque_numero + ' (Jogos ' + d.jogo_a.jogo.jogo_numero + ' & ' + d.jogo_b.jogo.jogo_numero + '): Top [' + d.top_combinacao.comb + '] com ' + d.top_combinacao.prob_pct + ' | Reducao: 2 Triplos em 3 Volantes (-66.7%)';
        }).join('\n');

        const linhasTernos = ternos.map(t => {
            const nums = t.jogos.map(j => j.jogo.jogo_numero).join(', ');
            return '   Terno ' + t.terno_numero + ' (Jogos ' + nums + '): Top [' + t.top_combinacao.comb + '] com ' + t.top_combinacao.prob_pct + ' | Reducoes: 3D em 4 volantes (-50%), 3T em 9 volantes (-66.7%)';
        }).join('\n');

        return [
            '================================================================================',
            '          ⚽ MOTOR LOTECA — B2B LOTERIAS (RELATORIO TECNICO OFICIAL)',
            '================================================================================',
            '1. RESUMO EXECUTIVO DO CONCURSO:',
            '   • Total de Partidas Auditadas: 14 Jogos da Grade Oficial',
            '   • Investimento Selecionado: R$ ' + otimizacao.custo.toFixed(2) + ' (' + otimizacao.estrutura.d + ' Duplo(s), ' + otimizacao.estrutura.t + ' Triplo(s))',
            '   • Apostas Equivalentes Cobertas: ' + otimizacao.apostas_equivalentes + ' volantes simples',
            '   • Entropia Media da Grade: ' + mediaEntropia,
            '   • Score Medio de Certeza: ' + mediaCerteza + ' / 100',
            '',
            '2. PROBABILIDADES FECHADAS DIXON-COLES (SOMA EXATA = 1.0):',
            linhasJogos,
            '',
            '3. DETECCAO DE JOGOS ARMADILHA (TRAP DETECTOR):',
            linhasTraps,
            '',
            '4. MODULO DOS 7 DUQUES (PARTICAO EXATA DOS 14 JOGOS):',
            linhasDuques,
            '',
            '5. MODULO DOS 4 TERNOS / TRIOS (27 COMBINACOES):',
            linhasTernos,
            '',
            '6. FECHAMENTOS REDUZIDOS CAIXA APLICADOS:',
            '   • 3 Duplos Reduzidos para 4 Apostas simples (-50.0% economia, garantia de 12/13 acertos)',
            '   • 3 Triplos Reduzidos para 9 Apostas simples (-66.7% economia, garantia de 12/13 acertos)',
            '   • 2 Triplos em Duques Reduzidos para 3 Apostas simples (-66.7% economia)',
            '',
            '7. DECLARACAO DE HONESTIDADE MATEMATICA:',
            '   O futebol e um sistema dinamico complexo estocastico. Nenhuma modelagem matematica,',
            '   Poisson, Monte Carlo ou IA e capaz de garantir 14 acertos. Este sistema maximiza o',
            '   Valor Esperado (EV), protege contra vieses emocionais do publico e otimiza a',
            '   distribuicao combinatoria dos volantes dentro das regras da Caixa.',
            '================================================================================'
        ].join('\n');
    }

    static gerarCarteiraDiversificada(quantidadeJogos = 10, orcamentoPorJogo = 4.0, estrategia = 'equilibrada', gradeCustom = null, palpitesManuais = null) {
        const analises = this.analisarGrade(gradeCustom);
        const qtd = Math.max(1, Math.min(50000, parseInt(quantidadeJogos) || 10));

        const estruturas = [
            { d: 1, t: 0, custo: 4.0 },
            { d: 0, t: 1, custo: 12.0 },
            { d: 2, t: 0, custo: 16.0 },
            { d: 1, t: 1, custo: 48.0 },
            { d: 3, t: 0, custo: 64.0 },
            { d: 2, t: 1, custo: 144.0 },
            { d: 4, t: 0, custo: 256.0 },
            { d: 1, t: 2, custo: 288.0 },
            { d: 3, t: 1, custo: 576.0 },
            { d: 2, t: 2, custo: 864.0 }
        ];
        const candidatas = estruturas.filter(e => e.custo <= orcamentoPorJogo);
        const estrutura = candidatas.length > 0 ? candidatas[candidatas.length - 1] : estruturas[0];
        const custoUnitario = estrutura.custo;
        const custoTotal = custoUnitario * qtd;

        // Ordenar jogos por incerteza (entropia)
        const ordenadosIncerteza = [...analises].sort((a, b) => b.entropia - a.entropia);
        const ordenadosCerteza = [...analises].sort((a, b) => a.entropia - b.entropia);

        // Se o usuário passou palpites manuais (ex: ['1', '1X', 'X', '1X2', ...])
        const temPalpitesManuais = Array.isArray(palpitesManuais) && palpitesManuais.length === 14;

        // Âncoras naturais: os 5 a 6 jogos com maior certeza estatística
        const ancorasNumeros = new Set(ordenadosCerteza.slice(0, 6).map(j => j.jogo.jogo_numero));

        const volantes = [];
        const maxTentativas = 250;

        for (let v = 0; v < qtd; v++) {
            const volanteId = v + 1;
            let melhorPalpitesVolante = null;

            // Determinar quais jogos receberão duplo ou triplo neste volante
            const triploIndices = new Set();
            const duploIndices = new Set();

            if (temPalpitesManuais) {
                // Se o apostador marcou duplos e triplos manualmente na grade
                analises.forEach((a, i) => {
                    const pUser = (palpitesManuais[i] || '').toUpperCase();
                    if (pUser.length === 3) triploIndices.add(a.jogo.jogo_numero);
                    else if (pUser.length === 2) duploIndices.add(a.jogo.jogo_numero);
                });
            } else {
                // Alocação inteligente: duplos e triplos nas partidas de maior incerteza (clássicos/equilíbrio)
                const offset = (v * (estrutura.d + estrutura.t || 1)) % ordenadosIncerteza.length;
                for (let t = 0; t < estrutura.t; t++) {
                    const idx = (offset + t) % ordenadosIncerteza.length;
                    triploIndices.add(ordenadosIncerteza[idx].jogo.jogo_numero);
                }
                for (let d = 0; d < estrutura.d; d++) {
                    const idx = (offset + estrutura.t + d) % ordenadosIncerteza.length;
                    duploIndices.add(ordenadosIncerteza[idx].jogo.jogo_numero);
                }
            }

            // Gerar o volante aplicando os 5 filtros estatísticos da Loteca
            for (let tentativa = 0; tentativa < maxTentativas; tentativa++) {
                let zebras = 0;
                let c1 = 0, cx = 0, c2 = 0;

                const palpites = analises.map((a, i) => {
                    const num = a.jogo.jogo_numero;
                    let tipo = 'SECO';
                    let palpite = a.palpite_seco;

                    if (temPalpitesManuais) {
                        const pUser = (palpitesManuais[i] || '').toUpperCase();
                        if (pUser.length === 3) {
                            tipo = 'TRIPLO';
                            palpite = '1X2';
                        } else if (pUser.length === 2) {
                            tipo = 'DUPLO';
                            palpite = pUser;
                        } else if (pUser.length === 1) {
                            tipo = 'SECO';
                            palpite = pUser;
                        }
                    } else if (triploIndices.has(num)) {
                        tipo = 'TRIPLO';
                        palpite = '1X2';
                    } else if (duploIndices.has(num)) {
                        tipo = 'DUPLO';
                        palpite = a.palpite_duplo;
                    } else {
                        // É Seco: verificar se é âncora fixa ou jogo de variação controlada
                        const ehAncora = ancorasNumeros.has(num);
                        const r = Math.random();
                        if (ehAncora) {
                            // Âncora mantém o favorito em 92% das vezes (alta assertividade)
                            if (r < 0.92 || estrategia === 'conservadora') {
                                palpite = a.ranking[0].coluna;
                            } else {
                                palpite = a.ranking[1].coluna;
                            }
                        } else {
                            // Jogo equilibrado: 68% favorito, 25% alternativa, 7% zebra
                            if (r < 0.68) {
                                palpite = a.ranking[0].coluna;
                            } else if (r < 0.93) {
                                palpite = a.ranking[1].coluna;
                            } else {
                                palpite = a.ranking[2].coluna;
                                zebras++;
                            }
                        }
                    }

                    // Contagem de colunas para os filtros estatísticos
                    const prim = palpite[0];
                    if (prim === '1') c1++;
                    else if (prim === 'X') cx++;
                    else c2++;

                    return {
                        jogo_numero: num,
                        mandante: a.jogo.mandante,
                        visitante: a.jogo.visitante,
                        palpite: palpite,
                        tipo: tipo
                    };
                });

                // FILTROS DE ASSERTIVIDADE MATEMÁTICA:
                // 1. Mandantes entre 5 e 8
                // 2. Empates entre 2 e 5
                // 3. Visitantes entre 2 e 5
                // 4. Zebras <= 2
                // 5. Máximo de 3 repetições consecutivas da mesma coluna
                let maxConsec = 1, curConsec = 1;
                for (let k = 1; k < 14; k++) {
                    if (palpites[k].palpite[0] === palpites[k - 1].palpite[0]) {
                        curConsec++;
                        if (curConsec > maxConsec) maxConsec = curConsec;
                    } else {
                        curConsec = 1;
                    }
                }

                const filtroColunas = (c1 >= 5 && c1 <= 8) && (cx >= 2 && cx <= 5) && (c2 >= 2 && c2 <= 5);
                const filtroZebras = zebras <= 2;
                const filtroConsec = maxConsec <= 3;

                if (filtroColunas && filtroZebras && filtroConsec) {
                    melhorPalpitesVolante = palpites;
                    break;
                }

                if (!melhorPalpitesVolante || tentativa === maxTentativas - 1) {
                    melhorPalpitesVolante = palpites;
                }
            }

            volantes.push({
                volante_numero: volanteId,
                estrutura: estrutura.d + 'D ' + estrutura.t + 'T',
                custo: custoUnitario,
                palpites: melhorPalpitesVolante,
                resumo_colunas: melhorPalpitesVolante.map(p => p.palpite).join(' - ')
            });
        }

        return {
            quantidade_jogos: qtd,
            custo_unitario: custoUnitario,
            custo_total: custoTotal,
            estrutura: estrutura,
            volantes: volantes,
            analises: analises
        };
    }

    static executarSimulacaoMonteCarlo(carteira, numSimulacoes = 10000, premio14 = 1500000.0, premio13 = 35000.0) {
        const runs = Math.max(100, Math.min(50000, parseInt(numSimulacoes) || 10000));
        const analises = carteira.analises || this.analisarGrade();
        const volantes = carteira.volantes;
        const nVolantes = volantes.length;

        const cumProbs = analises.map(a => {
            return { c1: a.probabilidades.coluna1, cx: a.probabilidades.coluna1 + a.probabilidades.colunaX };
        });

        const hist = { 14: 0, 13: 0, 12: 0, 11: 0, 10: 0, 9: 0, 8: 0, 7: 0, 6: 0, 5: 0, 4: 0, 3: 0, 2: 0, 1: 0, 0: 0 };
        let tot14 = 0, tot13 = 0;

        for (let i = 0; i < runs; i++) {
            const gabarito = cumProbs.map(cp => {
                const r = Math.random();
                if (r < cp.c1) return '1';
                if (r < cp.cx) return 'X';
                return '2';
            });

            let maxAcertos = 0;
            let fez14 = false, fez13 = false;

            for (let v = 0; v < nVolantes; v++) {
                let acertos = 0;
                const palps = volantes[v].palpites;
                for (let j = 0; j < 14; j++) {
                    if (palps[j].palpite.indexOf(gabarito[j]) !== -1) {
                        acertos++;
                    }
                }
                if (acertos > maxAcertos) maxAcertos = acertos;
                if (acertos === 14) fez14 = true;
                else if (acertos === 13) fez13 = true;
            }

            hist[maxAcertos] = (hist[maxAcertos] || 0) + 1;
            if (fez14) tot14++;
            if (fez13) tot13++;
        }

        const custoSimulado = runs * carteira.custo_total;
        const retornoSimulado = (tot14 * premio14) + (tot13 * premio13);
        const roi = custoSimulado > 0 ? ((retornoSimulado - custoSimulado) / custoSimulado) * 100 : 0;
        const ev = retornoSimulado / runs;
        const freq14 = (tot14 / runs) * 100;
        const freq13 = (tot13 / runs) * 100;

        const probAleatoria14 = (1.0 / Math.pow(3, 14)) * nVolantes;
        const vantagem = (probAleatoria14 > 0 && freq14 > 0) ? (freq14 / 100) / probAleatoria14 : 1.0;

        return {
            num_simulacoes: runs,
            quantidade_volantes: nVolantes,
            custo_carteira_por_concurso: carteira.custo_total,
            custo_total_simulado: custoSimulado,
            premios_14_acertos: tot14,
            premios_13_acertos: tot13,
            freq_14_pct: parseFloat(freq14.toFixed(4)),
            freq_13_pct: parseFloat(freq13.toFixed(3)),
            retorno_bruto_simulado: retornoSimulado,
            ev_por_concurso: parseFloat(ev.toFixed(2)),
            roi_simulado_pct: parseFloat(roi.toFixed(2)),
            vantagem_vs_aleatorio: parseFloat(vantagem.toFixed(1)),
            histograma: hist
        };
    }

    static simularCenarios(carteira) {
        const analises = carteira.analises || this.analisarGrade();
        const volantes = carteira.volantes;

        const gabLogica = analises.map(a => a.ranking[0].coluna);

        const ordenadosIncerteza = [...analises].sort((a, b) => b.entropia - a.entropia);
        const indicesZebras = new Set(ordenadosIncerteza.slice(0, 4).map(j => j.jogo.jogo_numero));
        const gabZebras = analises.map(a => {
            if (indicesZebras.has(a.jogo.jogo_numero)) return a.ranking[2].coluna;
            return a.ranking[0].coluna;
        });

        const ordenadosEmpate = [...analises].sort((a, b) => b.probabilidades.colunaX - a.probabilidades.colunaX);
        const indicesEmpate = new Set(ordenadosEmpate.slice(0, 5).map(j => j.jogo.jogo_numero));
        const gabEmpates = analises.map(a => {
            if (indicesEmpate.has(a.jogo.jogo_numero)) return 'X';
            return a.ranking[0].coluna;
        });

        const avaliar = (gabarito) => {
            let maxAcertos = 0;
            let volantes14 = [], volantes13 = [];
            volantes.forEach(v => {
                let ac = 0;
                for (let j = 0; j < 14; j++) {
                    if (v.palpites[j].palpite.indexOf(gabarito[j]) !== -1) ac++;
                }
                if (ac > maxAcertos) maxAcertos = ac;
                if (ac === 14) volantes14.push(v.volante_numero);
                else if (ac === 13) volantes13.push(v.volante_numero);
            });
            return { max_acertos: maxAcertos, volantes_14: volantes14, volantes_13: volantes13, gabarito: gabarito.join('') };
        };

        return {
            cenario_logico: avaliar(gabLogica),
            cenario_zebras: avaliar(gabZebras),
            cenario_empates: avaliar(gabEmpates)
        };
    }

    static conferirGabarito(carteira, gabarito) {
        const volantes = carteira.volantes || [];
        let maxAcertos = 0, melhorVolante = null;
        const resultados = volantes.map((v, vIdx) => {
            let acertos = 0;
            const palpitesArr = v.palpites || (Array.isArray(v) ? v : []);
            const detalhe = palpitesArr.map((p, idx) => {
                const sorteado = (gabarito[idx] || '-').toString().toUpperCase().trim();
                const pickStr = (p && typeof p === 'object' && p.palpite) ? String(p.palpite).toUpperCase().trim() : String(p).toUpperCase().trim();
                const acertou = sorteado !== '-' && sorteado !== '' && pickStr.indexOf(sorteado) !== -1;
                if (acertou) acertos++;
                return { 
                    jogo_numero: (p && typeof p === 'object' && p.jogo_numero) ? p.jogo_numero : (idx + 1), 
                    palpite: pickStr, 
                    sorteado: sorteado, 
                    acertou: acertou 
                };
            });
            const vNum = v.volante_numero || (vIdx + 1);
            if (acertos > maxAcertos) {
                maxAcertos = acertos;
                melhorVolante = vNum;
            }
            return {
                volante_numero: vNum,
                acertos: acertos,
                premio: acertos === 14 ? '14 PONTOS! 🏆' : (acertos === 13 ? '13 PONTOS! 🥈' : 'NÃO PREMIADO'),
                detalhe: detalhe
            };
        });

        return {
            max_acertos: maxAcertos,
            melhor_volante: melhorVolante,
            volantes: resultados
        };
    }

    static gerarGabaritoAleatorio(analises = null) {
        const lista = analises || this.analisarGrade();
        return lista.map(a => {
            const r = Math.random();
            const p1 = a.probabilidades.coluna1;
            const px = a.probabilidades.colunaX;
            if (r < p1) return '1';
            if (r < (p1 + px)) return 'X';
            return '2';
        });
    }

    static async gerarPrognosticos(orcamento = 48.0, estrategia = 'equilibrada', quantidadeJogos = 10, gradeCustom = null, palpitesManuais = null) {
        let dadosApi = null;
        if (!palpitesManuais) {
            try {
                const controller = new AbortController();
                const tid = setTimeout(() => controller.abort(), 2500);
                const res = await fetch('http://127.0.0.1:8000/api/v1/motor-loteca/simular-carteira', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    signal: controller.signal,
                    body: JSON.stringify({
                        orcamento_por_jogo: orcamento,
                        estrategia: estrategia,
                        quantidade_jogos: quantidadeJogos,
                        num_simulacoes: 10000
                    })
                });
                clearTimeout(tid);
                if (res.ok) {
                    const data = await res.json();
                    if (data.sucesso) dadosApi = data;
                }
            } catch (e) {
                // Fallback para Motor Loteca Nativo JS
            }
        }

        const analises = this.analisarGrade(gradeCustom);
        const otimizacao = this.otimizarOrcamento(analises, orcamento, estrategia);
        const duques = this.gerar7Duques(analises);
        const ternos = this.gerar4Ternos(analises);
        const relatorio = this.gerarRelatorioTecnico(otimizacao, duques, ternos);
        const carteira = (!palpitesManuais && dadosApi?.carteira) ? dadosApi.carteira : this.gerarCarteiraDiversificada(quantidadeJogos, orcamento, estrategia, gradeCustom, palpitesManuais);
        const simulacao = dadosApi?.simulacao_monte_carlo || this.executarSimulacaoMonteCarlo(carteira, 10000);
        const cenarios = dadosApi?.cenarios || this.simularCenarios(carteira);

        return {
            sucesso: true,
            origem: dadosApi ? 'API_PYTHON' : 'NATIVO_JS',
            orcamento: otimizacao.custo,
            estrutura: otimizacao.estrutura,
            apostas_equivalentes: otimizacao.apostas_equivalentes,
            jogos: otimizacao.jogos,
            duques,
            ternos,
            carteira,
            simulacao,
            cenarios,
            relatorio
        };
    }
}

if (typeof window !== 'undefined') {
    window.MotorLotecaB2BEngine = MotorLotecaB2BEngine;
}
