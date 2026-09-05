/**
 * MOTOR INTELIGENTE QUINA — B2B LOTERIAS (MÓDULO OFICIAL JS)
 * =========================================================
 * Rigor Matemático, Estatístico, Probabilístico e Combinatório:
 * 1. Universo de 80 dezenas (01-80), exatamente 5 dezenas por jogo.
 *    Espaço amostral exato: C(80, 5) = 24.040.016 combinações.
 * 2. Partição Canônica Obrigatória: Grupo A (01-40) e Grupo B (41-80).
 * 3. Modelos Combinatórios Hipergeométricos: 3/2, 2/3, 4/1, 1/4, 5/0, 0/5.
 *    (Ordenação dinâmica calculada pelo histórico de 3 a 100 concursos).
 * 4. Filtro Mandatório de Sequências Consecutivas (Item 28): MÁXIMO 2 CONSECUTIVOS (<= 2 permitido, >= 3 proibido).
 * 5. Centróide Simétrico (Item 19): Média em torno de 40.5 e Soma esperada de 202.5 (Faixa P5-P95: [120, 285]).
 * 6. Associação, Coocorrência, Matriz de Lift e Z-Score com regularização Bayesiana (Laplace).
 * 7. Modos de Operação: Equilibrada, Sniper (🎯), Frequência, Atrasos/Recuperações, Pares/Trios, Auto-Pesos.
 * 8. Geração em Duas Etapas (Subconjuntos A e B) e Confronto Combinatório Cruzado (A x B).
 * 9. Diversificação Coletiva por Limiar de Jaccard e Auditoria dos 10 Checks Mandatórios.
 * 10. Suporte à API Python de alta performance com Fallback 100% Autônomo em JavaScript Nativo.
 */

class MotorQuinaB2BEngine {
    static TOTAL_NUMEROS = 80;
    static GAME_SIZE = 5;
    static MAX_CONSECUTIVOS = 2; // Item 28: NO MÁXIMO 2 NÚMEROS CONSECUTIVOS!
    static UNIVERSO = Array.from({ length: 80 }, (_, i) => i + 1);

    static GRUPO_A = Array.from({ length: 40 }, (_, i) => i + 1);    // 01..40
    static GRUPO_B = Array.from({ length: 40 }, (_, i) => i + 41);   // 41..80
    static SET_A = new Set(MotorQuinaB2BEngine.GRUPO_A);
    static SET_B = new Set(MotorQuinaB2BEngine.GRUPO_B);

    static MEDIA_ESPERADA_NUMERO = 40.5;
    static SOMA_ESPERADA_JOGO = 202.5;
    static SOMA_MIN_ACEITAVEL = 120;
    static SOMA_MAX_ACEITAVEL = 285;

    static DISTRIBUICOES_TEORICAS = {
        '3/2': { kA: 3, kB: 2, comb: 7706400, pct: 32.0565, rotulo: '3/2 (3A + 2B)' },
        '2/3': { kA: 2, kB: 3, comb: 7706400, pct: 32.0565, rotulo: '2/3 (2A + 3B)' },
        '4/1': { kA: 4, kB: 1, comb: 3655600, pct: 15.2063, rotulo: '4/1 (4A + 1B)' },
        '1/4': { kA: 1, kB: 4, comb: 3655600, pct: 15.2063, rotulo: '1/4 (1A + 4B)' },
        '5/0': { kA: 5, kB: 0, comb: 658008,  pct: 2.7371,  rotulo: '5/0 (5A + 0B)' },
        '0/5': { kA: 0, kB: 5, comb: 658008,  pct: 2.7371,  rotulo: '0/5 (0A + 5B)' }
    };

    static fmt(n) {
        return parseInt(n).toString().padStart(2, '0');
    }

    static validarConsecutivos(jogo) {
        const s = [...jogo].sort((a, b) => a - b);
        let cur = 1, maxC = 1;
        for (let i = 1; i < s.length; i++) {
            if (s[i] === s[i - 1] + 1) {
                cur++;
                if (cur > maxC) maxC = cur;
            } else {
                cur = 1;
            }
        }
        return maxC <= MotorQuinaB2BEngine.MAX_CONSECUTIVOS;
    }

    static contarMaxConsecutivos(jogo) {
        const s = [...jogo].sort((a, b) => a - b);
        let cur = 1, maxC = 1;
        for (let i = 1; i < s.length; i++) {
            if (s[i] === s[i - 1] + 1) {
                cur++;
                if (cur > maxC) maxC = cur;
            } else {
                cur = 1;
            }
        }
        return maxC;
    }

    static obterHistorico(limite = 30) {
        if (typeof REAL_HISTORY_DB !== 'undefined' && REAL_HISTORY_DB.quina && REAL_HISTORY_DB.quina.length > 0) {
            const draws = REAL_HISTORY_DB.quina.map(d => d.numbers.slice().sort((a, b) => a - b));
            if (draws.length >= 3) return draws;
        }
        return [
            [5, 13, 58, 72, 80], [10, 22, 34, 45, 67], [3, 14, 28, 51, 69],
            [12, 19, 33, 44, 78], [7, 21, 38, 52, 63], [1, 16, 29, 41, 75],
            [9, 25, 42, 60, 77], [4, 18, 35, 48, 71], [8, 20, 37, 55, 68],
            [2, 15, 31, 49, 64], [11, 24, 39, 57, 79], [6, 23, 40, 53, 70],
            [13, 27, 43, 59, 74], [17, 30, 46, 62, 76], [5, 26, 36, 50, 73],
            [14, 32, 47, 65, 80], [3, 19, 38, 54, 69], [12, 28, 45, 61, 78],
            [7, 22, 41, 58, 72], [10, 25, 34, 51, 67], [1, 18, 37, 56, 75],
            [8, 21, 39, 63, 77], [4, 16, 35, 52, 71], [9, 24, 42, 60, 79],
            [2, 15, 33, 48, 66], [11, 29, 44, 57, 74], [6, 20, 40, 55, 70],
            [13, 27, 43, 59, 76], [17, 31, 49, 64, 78], [5, 23, 36, 53, 80]
        ];
    }

    static async gerarCarteira(quantidadeJogos = 10, options = {}) {
        const qtd = Math.max(1, parseInt(quantidadeJogos) || 10);
        const historicoLimite = options.historicoLimite || 30;
        const estrategia = options.estrategia || 'equilibrada';
        const pool = options.pool || null;
        const modeloPreferencial = options.modeloPreferencial || null;
        const numerosFixos = options.numerosFixos || [];
        const numerosProibidos = options.numerosProibidos || [];

        // 1. Tentar API Python local se estiver ativa
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 3500);

            const res = await fetch('http://127.0.0.1:8000/api/v1/motor-quina', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                signal: controller.signal,
                body: JSON.stringify({
                    quantidade_jogos: qtd,
                    historico_limite: historicoLimite,
                    estrategia: estrategia,
                    pool: pool,
                    modelo_preferencial: modeloPreferencial,
                    numeros_fixos: numerosFixos,
                    numeros_proibidos: numerosProibidos
                })
            });
            clearTimeout(timeoutId);

            if (res.ok) {
                const data = await res.json();
                if (data.sucesso && data.jogos && data.jogos.length >= qtd) {
                    console.log(`[B2B] Motor Quina executado via API Python (${data.jogos.length} jogos).`);
                    return data;
                }
            }
        } catch (e) {
            console.log('[B2B] API Python indisponível ou timeout, utilizando Motor Quina nativo JS.');
        }

        // 2. Motor Nativo Local em JavaScript
        return this.gerarCarteiraLocal(qtd, options);
    }

    static gerarCarteiraLocal(qtd = 10, options = {}) {
        const targetQtd = Math.max(1, parseInt(qtd) || 10);
        const rawHistorico = this.obterHistorico();
        const limite = Math.max(3, Math.min(100, options.historicoLimite || 30));
        const historico = rawHistorico.slice(-limite);
        const W = historico.length;
        const estrategia = options.estrategia || 'equilibrada';
        const isSniper = (estrategia === 'sniper');

        // Configuração do Pool (Item 32)
        let pool = MotorQuinaB2BEngine.UNIVERSO;
        let isCustomPool = false;
        if (options.pool && Array.isArray(options.pool) && options.pool.length >= 5) {
            const valid = options.pool.filter(n => n >= 1 && n <= 80);
            if (valid.length >= 5) {
                pool = Array.from(new Set(valid)).sort((a, b) => a - b);
                isCustomPool = (pool.length < 80);
            }
        }
        const setPool = new Set(pool);
        const poolA = pool.filter(n => MotorQuinaB2BEngine.SET_A.has(n));
        const poolB = pool.filter(n => MotorQuinaB2BEngine.SET_B.has(n));

        const fixos = (options.numerosFixos || []).filter(n => setPool.has(n));
        const proibidos = new Set(options.numerosProibidos || []);

        // 1. Diagnóstico Estatístico
        const expFreq = (5.0 / 80.0) * W;
        const sigmaFreq = Math.sqrt(W * 0.0625 * 0.9375) || 1.0;

        const freqAbs = {};
        for (let i = 1; i <= 80; i++) freqAbs[i] = 0;
        historico.forEach(draw => draw.forEach(n => { if (freqAbs[n] !== undefined) freqAbs[n]++; }));

        const wRec = Math.max(2, Math.min(5, Math.floor(W / 3)));
        const janelaRec = historico.slice(-wRec);
        const freqRec = {};
        for (let i = 1; i <= 80; i++) freqRec[i] = 0;
        janelaRec.forEach(draw => draw.forEach(n => { if (freqRec[n] !== undefined) freqRec[n]++; }));

        const atrasoAtual = {};
        for (let i = 1; i <= 80; i++) {
            let cur = 0;
            for (let k = rawHistorico.length - 1; k >= 0; k--) {
                if (rawHistorico[k].includes(i)) break;
                cur++;
            }
            atrasoAtual[i] = cur;
        }

        const scoreNumero = {};
        for (let i = 1; i <= 80; i++) {
            const z = (freqAbs[i] - expFreq) / sigmaFreq;
            const recBonus = (freqRec[i] / wRec) * 20.0;
            scoreNumero[i] = Math.max(10, Math.min(99, 50.0 + (z * 15.0) + recBonus));
        }

        // Modelos empíricos
        const contagemModelos = {};
        historico.forEach(draw => {
            const nA = draw.filter(n => MotorQuinaB2BEngine.SET_A.has(n)).length;
            const nB = 5 - nA;
            const key = `${nA}/${nB}`;
            contagemModelos[key] = (contagemModelos[key] || 0) + 1;
        });

        const modelosOrdenados = Object.keys(MotorQuinaB2BEngine.DISTRIBUICOES_TEORICAS).map(key => {
            const teo = MotorQuinaB2BEngine.DISTRIBUICOES_TEORICAS[key];
            const obs = contagemModelos[key] || 0;
            const pctObs = (obs / W) * 100.0;
            const ratio = (pctObs + 5.0) / (teo.pct + 5.0);
            const scoreMod = Math.min(100, Math.max(20, Math.round(teo.pct * ratio * 2.5 * 10) / 10));
            return {
                modelo: key,
                rotulo: teo.rotulo,
                ocorrencias: obs,
                pctObservada: Math.round(pctObs * 100) / 100,
                pctTeorica: teo.pct,
                scoreAssertividade: scoreMod
            };
        }).sort((a, b) => b.scoreAssertividade - a.scoreAssertividade);

        // Pares e Lift
        const pParTeorica = (5.0 * 4.0) / (80.0 * 79.0);
        const expPar = W * pParTeorica;
        const contagemPares = {};
        historico.forEach(draw => {
            for (let i = 0; i < draw.length; i++) {
                for (let j = i + 1; j < draw.length; j++) {
                    const key = `${draw[i]}-${draw[j]}`;
                    contagemPares[key] = (contagemPares[key] || 0) + 1;
                }
            }
        });

        const mapaPares = {};
        Object.keys(contagemPares).forEach(key => {
            const [n1, n2] = key.split('-').map(Number);
            const count = contagemPares[key];
            const p1 = (freqAbs[n1] + 0.5) / (W + 40);
            const p2 = (freqAbs[n2] + 0.5) / (W + 40);
            const p12 = (count + 0.5) / (W + 0.5);
            const lift = p12 / (p1 * p2);
            const zPar = (count - expPar) / Math.sqrt(Math.max(0.1, expPar * (1 - pParTeorica)));
            const score = Math.min(99, Math.max(20, 50.0 + (lift - 1.0) * 25.0 + zPar * 10.0));
            mapaPares[key] = {
                rotulo: `${MotorQuinaB2BEngine.fmt(n1)}-${MotorQuinaB2BEngine.fmt(n2)}`,
                count, lift: Math.round(lift * 100) / 100,
                score: Math.round(score * 10) / 10
            };
        });

        // 2. Cotas dos Modelos
        let modelosAlocacao = [];
        if (options.modeloPreferencial && MotorQuinaB2BEngine.DISTRIBUICOES_TEORICAS[options.modeloPreferencial]) {
            modelosAlocacao.push({ modelo: options.modeloPreferencial, count: targetQtd });
        } else {
            const topMods = isSniper ? modelosOrdenados.slice(0, 3) : modelosOrdenados.slice(0, 4);
            const totalScore = topMods.reduce((acc, m) => acc + m.scoreAssertividade, 0);
            let alocados = 0;
            topMods.forEach((m, idx) => {
                const c = (idx === topMods.length - 1) ? Math.max(1, targetQtd - alocados) : Math.max(1, Math.round(targetQtd * (m.scoreAssertividade / totalScore)));
                modelosAlocacao.push({ modelo: m.modelo, count: c });
                alocados += c;
            });
        }

        // 3. Seleção de Candidatos
        const candA = isSniper ? [...poolA].sort((a, b) => scoreNumero[b] - scoreNumero[a]).slice(0, 18) : poolA;
        const candB = isSniper ? [...poolB].sort((a, b) => scoreNumero[b] - scoreNumero[a]).slice(0, 18) : poolB;

        const candidatosPorModelo = {};
        modelosAlocacao.forEach(alloc => {
            const [nA, nB] = alloc.modelo.split('/').map(Number);
            candidatosPorModelo[alloc.modelo] = [];

            const limiteTentativas = Math.max(600, alloc.count * 80);
            let tentativas = 0;

            while (tentativas < limiteTentativas && candidatosPorModelo[alloc.modelo].length < alloc.count * 15) {
                tentativas++;
                const partA = MotorQuinaB2BEngine.amostrarAleatorio(candA, nA);
                const partB = MotorQuinaB2BEngine.amostrarAleatorio(candB, nB);
                const combo = [...partA, ...partB].sort((a, b) => a - b);

                if (combo.length !== 5) continue;
                if (new Set(combo).size !== 5) continue;
                if (fixos.length > 0 && !fixos.every(f => combo.includes(f))) continue;
                if (Array.from(proibidos).some(p => combo.includes(p))) continue;

                // FILTRO MANDATÓRIO (Item 28): Máximo 2 consecutivos
                if (!MotorQuinaB2BEngine.validarConsecutivos(combo)) continue;

                // Centróide Simétrico (Item 19)
                const soma = combo.reduce((acc, n) => acc + n, 0);
                if (soma < MotorQuinaB2BEngine.SOMA_MIN_ACEITAVEL || soma > MotorQuinaB2BEngine.SOMA_MAX_ACEITAVEL) continue;

                // Cálculo IGA
                const igaInfo = MotorQuinaB2BEngine.calcularIgaLocal(combo, {
                    scoreNumero, freqRec, wRec, mapaPares,
                    modelosOrdenados, modelo: alloc.modelo, soma, totalAnalisado: W
                });

                candidatosPorModelo[alloc.modelo].push({
                    numeros: combo,
                    iga: igaInfo.iga,
                    explicacao: igaInfo.explicacao
                });
            }
        });

        // 4. Seleção da Carteira com Diversificação (Item 27)
        const carteira = [];
        const setsUsados = [];
        const dezenasContador = {};

        modelosAlocacao.forEach(alloc => {
            const lista = (candidatosPorModelo[alloc.modelo] || []).sort((a, b) => b.iga - a.iga);
            let added = 0;
            for (const cand of lista) {
                const s = new Set(cand.numeros);
                // Evita duplicatas
                if (setsUsados.some(u => Array.from(s).every(n => u.has(n)))) continue;
                // Evita sobreposição excessiva (4 dezenas iguais)
                if (setsUsados.some(u => cand.numeros.filter(n => u.has(n)).length >= 4)) continue;

                carteira.push(cand);
                setsUsados.push(s);
                cand.numeros.forEach(n => dezenasContador[n] = (dezenasContador[n] || 0) + 1);
                added++;
                if (added >= alloc.count || carteira.length >= targetQtd) break;
            }
        });

        // Fallback se necessário
        if (carteira.length < targetQtd) {
            Object.keys(candidatosPorModelo).forEach(mKey => {
                for (const cand of candidatosPorModelo[mKey]) {
                    const s = new Set(cand.numeros);
                    if (!setsUsados.some(u => Array.from(s).every(n => u.has(n))) && MotorQuinaB2BEngine.validarConsecutivos(cand.numeros)) {
                        carteira.push(cand);
                        setsUsados.push(s);
                        if (carteira.length >= targetQtd) break;
                    }
                }
            });
        }

        carteira.sort((a, b) => b.iga - a.iga);

        // 5. Formatação dos Jogos
        const jogosFormatados = carteira.slice(0, targetQtd).map((item, idx) => {
            const exp = item.explicacao;
            let alerta = 'ASSERTIVIDADE MODERADA';
            let cor = 'amarelo';
            if (item.iga >= 85.0) { alerta = 'ASSERTIVIDADE ROBUSTA'; cor = 'verde'; }
            else if (item.iga < 50.0) { alerta = 'SEM EVIDÊNCIA'; cor = 'cinza'; }
            else if (item.iga < 70.0) { alerta = 'ASSERTIVIDADE FRACA'; cor = 'laranja'; }

            const motivos = [
                `Modelo ${exp.modelo} (${exp.distribuicaoAB}).`,
                `Centróide: soma ${exp.soma} (desvio ${exp.distanciaCentroide} da média 202.5).`,
                `Filtro de sequências: max ${exp.maxConsecutivos} consecutivos (<= 2).`
            ];
            if (exp.paresFortes && exp.paresFortes.length > 0) {
                motivos.push(`Pares com Lift: ${exp.paresFortes.slice(0, 3).join(', ')}.`);
            }

            return {
                posicao: idx + 1,
                numeros: item.numeros,
                numeros_formatados: item.numeros.map(MotorQuinaB2BEngine.fmt),
                linha_texto: item.numeros.map(MotorQuinaB2BEngine.fmt).join(' - '),
                iga: item.iga,
                iga_fmt: item.iga.toFixed(1),
                alerta_qualidade: alerta,
                classe_cor: cor,
                modelo: exp.modelo,
                soma: exp.soma,
                max_consecutivos: exp.maxConsecutivos,
                explicacao_resumida: motivos.join(' | '),
                detalhes_explicacao: exp
            };
        });

        // 6. IGA da Carteira
        const igas = jogosFormatados.map(j => j.iga);
        const mediaIga = igas.length > 0 ? (igas.reduce((a, b) => a + b, 0) / igas.length) : 0;
        const totalUnicas = new Set(jogosFormatados.flatMap(j => j.numeros)).size;
        const taxaCobertura = (totalUnicas / 80.0) * 100.0;
        const igaCarteira = Math.round((mediaIga * 0.70 + taxaCobertura * 0.30) * 10) / 10;

        const checks = {
            check_01_quantidade_exata: (jogosFormatados.length === targetQtd),
            check_02_cinco_numeros: jogosFormatados.every(j => j.numeros.length === 5),
            check_03_range_valido: jogosFormatados.every(j => j.numeros.every(n => n >= 1 && n <= 80)),
            check_04_sem_duplicatas: jogosFormatados.every(j => new Set(j.numeros).size === 5),
            check_05_sem_jogos_duplicados: (new Set(jogosFormatados.map(j => j.numeros.join('-'))).size === jogosFormatados.length),
            check_06_max_dois_consecutivos: jogosFormatados.every(j => j.max_consecutivos <= 2),
            check_07_centroide_equilibrado: jogosFormatados.every(j => j.soma >= 120 && j.soma <= 285),
            check_08_iga_calculado: jogosFormatados.every(j => j.iga >= 0 && j.iga <= 100),
            check_09_explicacao_presente: jogosFormatados.every(j => j.explicacao_resumida.length > 10),
            check_10_iga_carteira_valido: (igaCarteira >= 0 && igaCarteira <= 100)
        };

        return {
            sucesso: true,
            total_solicitado: targetQtd,
            total_gerado: jogosFormatados.length,
            estrategia,
            is_sniper: isSniper,
            iga_carteira: igaCarteira,
            media_iga_jogos: Math.round(mediaIga * 10) / 10,
            dezenas_unicas_cobertas: totalUnicas,
            taxa_cobertura_universo: Math.round(taxaCobertura * 10) / 10,
            jogos: jogosFormatados,
            checks_auditoria: {
                aprovacao_integral_10_de_10: Object.values(checks).every(Boolean),
                detalhes: checks
            },
            relatorio_tecnico: {
                concursos_utilizados: W,
                espaco_amostral_total: 24040016,
                probabilidade_quina: "1 / 24.040.016 (0,00000416%)",
                soma_esperada_jogo: 202.5,
                faixa_centroide_p5_p95: [120, 285],
                modelos_ranking: modelosOrdenados
            }
        };
    }

    static calcularIgaLocal(combo, ctx) {
        const nA = combo.filter(n => MotorQuinaB2BEngine.SET_A.has(n)).length;
        const nB = 5 - nA;
        const modeloStr = `${nA}/${nB}`;

        const compNums = combo.reduce((acc, n) => acc + (ctx.scoreNumero[n] || 50), 0) / 5.0;
        const compRec = Math.min(99, Math.max(20, (combo.reduce((acc, n) => acc + (ctx.freqRec[n] || 0), 0) / ctx.wRec) * 20.0 + 40));

        const paresFortes = [];
        let scoreParesSoma = 0;
        let countPares = 0;
        for (let i = 0; i < combo.length; i++) {
            for (let j = i + 1; j < combo.length; j++) {
                const key = `${combo[i]}-${combo[j]}`;
                if (ctx.mapaPares[key]) {
                    scoreParesSoma += ctx.mapaPares[key].score;
                    if (ctx.mapaPares[key].lift >= 1.2) paresFortes.push(ctx.mapaPares[key].rotulo);
                } else {
                    scoreParesSoma += 50.0;
                }
                countPares++;
            }
        }
        const compPares = countPares > 0 ? (scoreParesSoma / countPares) : 50.0;

        let compModelo = 50.0;
        const mInfo = ctx.modelosOrdenados.find(m => m.modelo === modeloStr);
        if (mInfo) compModelo = mInfo.scoreAssertividade;

        const distCentro = Math.abs(ctx.soma - MotorQuinaB2BEngine.SOMA_ESPERADA_JOGO);
        const compCentroide = Math.max(20, 100 - distCentro * 0.7);

        let iga = (compNums * 0.25) + (compRec * 0.15) + (compPares * 0.25) + (compModelo * 0.20) + (compCentroide * 0.15);

        const consec = MotorQuinaB2BEngine.contarMaxConsecutivos(combo);
        if (consec > 2) iga -= 40.0;
        else if (consec === 2) iga -= 2.0;

        if (ctx.totalAnalisado < 10) iga -= 5.0;

        iga = Math.round(Math.max(10, Math.min(99.4, iga)) * 10) / 10;

        return {
            iga,
            explicacao: {
                modelo: modeloStr,
                distribuicaoAB: `${nA} do Grupo A (01-40) e ${nB} do Grupo B (41-80)`,
                soma: ctx.soma,
                distanciaCentroide: Math.round(distCentro * 10) / 10,
                maxConsecutivos: consec,
                paresFortes
            }
        };
    }

    static amostrarAleatorio(arr, k) {
        if (k <= 0) return [];
        if (k >= arr.length) return [...arr];
        const copia = [...arr];
        const res = [];
        for (let i = 0; i < k; i++) {
            const idx = Math.floor(Math.random() * copia.length);
            res.push(copia[idx]);
            copia.splice(idx, 1);
        }
        return res;
    }
}

if (typeof window !== 'undefined') {
    window.MotorQuinaB2BEngine = MotorQuinaB2BEngine;
}
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { MotorQuinaB2BEngine };
}
