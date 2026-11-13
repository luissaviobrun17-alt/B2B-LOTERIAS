/**
 * OTIMIZADOR COMBINATÓRIO DE DISPERSÃO E COBERTURA CONJUNTA — LOTOMANIA | MODO 4 — v1.2
 * =====================================================================================
 * Cliente HTTP estrito para o núcleo matemático Python isolado e selado (Ed25519 + SHA-256).
 * PROIBIÇÃO ABSOLUTA DE FALLBACK JAVASCRIPT:
 * Este módulo não possui gerador local. Se a API Python oficial (127.0.0.1:8000) estiver
 * indisponível ou se o selo criptográfico falhar, zero jogos são gerados.
 */

class MotorLotomaniaModo4Engine {
    static API_BASE = 'http://127.0.0.1:8000';
    static ENDPOINT_GERAR = 'http://127.0.0.1:8000/api/v1/lotomania-modo4/gerar';
    static ENDPOINT_JOBS = 'http://127.0.0.1:8000/api/v1/lotomania-modo4/jobs';
    static ENDPOINT_CONFERIR = 'http://127.0.0.1:8000/api/v1/lotomania-modo4/conferir';
    static ENDPOINT_HEALTH = 'http://127.0.0.1:8000/health';

    static NOME_OFICIAL = 'OTIMIZADOR COMBINATÓRIO DE DISPERSÃO E COBERTURA CONJUNTA — LOTOMANIA | MODO 4 — v1.2';
    static VERSAO = '1.2';

    static MENSAGEM_INDISPONIVEL = 'MODO 4 temporariamente indisponível. O servidor matemático oficial não está conectado. Nenhum jogo foi gerado.';

    static CLAUSULA_INSTITUCIONAL = 'O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.';
    static CLAUSULA_INSTITUCIONAL_RESUMO = 'O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é estruturar carteiras de apostas com menor redundância interna, melhor distribuição de dezenas e maior cobertura combinatória conjunta.';

    static fmt(n) {
        const num = Number(n);
        if (num === 100 || num === 0) return '00';
        return String(num).padStart(2, '0');
    }

    static _respostaVaziaErro(erro, extras = {}) {
        return {
            sucesso: false,
            jogos: [],
            jogos_formatados: [],
            quantidade_entregue: 0,
            erro: erro,
            ...extras
        };
    }

    static _aguardar(ms, signal = null) {
        return new Promise((resolve) => {
            if (signal && signal.aborted) {
                resolve();
                return;
            }
            const timer = setTimeout(() => {
                if (signal && onAbort) signal.removeEventListener('abort', onAbort);
                resolve();
            }, ms);
            const onAbort = signal ? () => {
                clearTimeout(timer);
                signal.removeEventListener('abort', onAbort);
                resolve();
            } : null;
            if (signal && onAbort) {
                signal.addEventListener('abort', onAbort, { once: true });
            }
        });
    }

    static async _fetchComTimeout(url, fetchOptions, timeoutMs, externalSignal = null) {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), timeoutMs);
        const onExternalAbort = () => controller.abort();
        if (externalSignal) {
            if (externalSignal.aborted) {
                clearTimeout(timeoutId);
                throw new DOMException('Aborted', 'AbortError');
            }
            externalSignal.addEventListener('abort', onExternalAbort, { once: true });
        }
        try {
            return await fetch(url, { ...fetchOptions, signal: controller.signal });
        } finally {
            clearTimeout(timeoutId);
            if (externalSignal) externalSignal.removeEventListener('abort', onExternalAbort);
        }
    }

    /**
     * Solicita cancelamento imediato de um job assíncrono em execução no servidor.
     */
    static async cancelarJob(jobId) {
        if (!jobId) return false;
        try {
            const resp = await this._fetchComTimeout(
                `${this.ENDPOINT_JOBS}/${encodeURIComponent(jobId)}`,
                { method: 'DELETE', headers: { 'Accept': 'application/json' } },
                5000
            );
            return Boolean(resp && resp.ok);
        } catch (_err) {
            return false;
        }
    }

    /**
     * Consulta o endpoint /health do servidor Python para verificar disponibilidade e selo Ed25519.
     */
    static async verificarStatusServidor() {
        try {
            const resp = await this._fetchComTimeout(
                this.ENDPOINT_HEALTH,
                { method: 'GET', headers: { 'Accept': 'application/json' } },
                5000
            );
            if (!resp.ok) {
                return {
                    conectado: false,
                    modo4_disponivel: false,
                    selo_valido: false,
                    versao: this.VERSAO,
                    mensagem: this.MENSAGEM_INDISPONIVEL
                };
            }
            const data = await resp.json();
            const infoM4 = (data && data.modo4) ? data.modo4 : {};
            const seloOk = Boolean(data && (data.selo_valido === true || infoM4.selo_valido === true));
            const ativo = Boolean(data && data.modo4_disponivel === true && seloOk);
            const arqs = infoM4.arquivos_verificados || {};
            return {
                conectado: true,
                modo4_disponivel: ativo,
                selo_valido: seloOk,
                versao: infoM4.versao_motor || data.versao || this.VERSAO,
                hash_nucleo: arqs['motor_lotomania_modo4.py'] || data.hash_nucleo || null,
                hash_manifesto_canonico: infoM4.sha256_manifesto || data.hash_manifesto_canonico || null,
                concurso_corte: infoM4.corte_historico_concurso || 2699,
                limite_jogos: {
                    min: infoM4.limite_min_jogos || 1,
                    max: infoM4.limite_max_jogos || 10000
                },
                mensagem: ativo ? 'Servidor matemático oficial conectado e selo Ed25519 íntegro.' : this.MENSAGEM_INDISPONIVEL
            };
        } catch (_err) {
            return {
                conectado: false,
                modo4_disponivel: false,
                selo_valido: false,
                versao: this.VERSAO,
                mensagem: this.MENSAGEM_INDISPONIVEL
            };
        }
    }

    /**
     * Valida rigorosamente a quantidade de jogos solicitada (inteiro estrito entre 1 e 10.000).
     */
    static validarQuantidadeJogos(quantidadeJogos) {
        if (typeof quantidadeJogos !== 'number' || !Number.isInteger(quantidadeJogos) || Number.isNaN(quantidadeJogos)) {
            return {
                valido: false,
                erro: 'Quantidade inválida: informe um número inteiro estrito entre 1 e 10.000 jogos.'
            };
        }
        if (quantidadeJogos < 1 || quantidadeJogos > 10000) {
            return {
                valido: false,
                erro: 'Fora do intervalo permitido pelo MODO 4 v1.2: selecione entre 1 e 10.000 jogos.'
            };
        }
        return { valido: true, valor: quantidadeJogos };
    }

    /**
     * Solicita a geração de carteira ao servidor Python oficial do MODO 4 v1.2 via job assíncrono.
     * Não existe fallback local: qualquer falha de conexão retorna zero jogos.
     */
    static async gerarCarteira(quantidadeJogos, options = {}) {
        const validacaoQtd = this.validarQuantidadeJogos(quantidadeJogos);
        if (!validacaoQtd.valido) {
            return this._respostaVaziaErro(validacaoQtd.erro);
        }

        const permitirEspelhos = (options.permitirEspelhos !== undefined)
            ? Boolean(options.permitirEspelhos)
            : (options.incluirEspelho !== undefined ? Boolean(options.incluirEspelho) : true);

        let seedVal = null;
        if (options.seed !== undefined && options.seed !== null && String(options.seed).trim() !== '') {
            if (typeof options.seed === 'boolean') {
                return this._respostaVaziaErro('Parâmetro seed inválido: deve ser um número inteiro ou vazio.');
            }
            const parsedSeed = Number(options.seed);
            if (!Number.isInteger(parsedSeed)) {
                return this._respostaVaziaErro('Parâmetro seed inválido: deve ser um número inteiro ou vazio.');
            }
            seedVal = parsedSeed;
        }

        const payload = {
            quantidade_jogos: validacaoQtd.valor,
            permitir_espelhos: permitirEspelhos,
            seed: seedVal,
            trace: Boolean(options.trace === true)
        };

        const signal = options.signal || null;
        const onProgress = typeof options.onProgress === 'function' ? options.onProgress : null;
        const onJobCreated = typeof options.onJobCreated === 'function' ? options.onJobCreated : null;
        const maxWaitMs = Number.isFinite(options.maxWaitMs) && options.maxWaitMs > 0 ? options.maxWaitMs : 1800000;
        let activeJobId = null;

        try {
            // 1) Cria o job no servidor (resposta HTTP 202 imediata, imune a timeout HTTP de longa execucao)
            const respCriar = await this._fetchComTimeout(
                this.ENDPOINT_JOBS,
                {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                },
                15000,
                signal
            );

            if (respCriar.status === 503) {
                return this._respostaVaziaErro(this.MENSAGEM_INDISPONIVEL);
            }

            let jobInit = null;
            try {
                jobInit = await respCriar.json();
            } catch (_jsonErr) {
                jobInit = null;
            }

            if (!respCriar.ok || !jobInit || !jobInit.job_id) {
                const detailMsg = (jobInit && (jobInit.erro || jobInit.detail))
                    ? (typeof jobInit.detail === 'string' ? jobInit.detail : JSON.stringify(jobInit.detail))
                    : this.MENSAGEM_INDISPONIVEL;
                return this._respostaVaziaErro(detailMsg);
            }

            activeJobId = jobInit.job_id;
            if (onJobCreated) onJobCreated(activeJobId);
            if (onProgress) onProgress(jobInit);

            const pollIntervalBase = Number.isFinite(jobInit.poll_interval_ms) && jobInit.poll_interval_ms >= 250
                ? jobInit.poll_interval_ms
                : 1500;
            const deadline = Date.now() + maxWaitMs;
            let falhasTransitoriasSeguidas = 0;
            const maxFalhasTransitorias = 3;

            // 2) Polling curto com tolerancia controlada a falhas transitorias de rede/aba em segundo plano
            while (Date.now() < deadline) {
                if (signal && signal.aborted) {
                    await this.cancelarJob(activeJobId);
                    return this._respostaVaziaErro('Operação cancelada pelo usuário. Nenhum jogo foi gerado.', { cancelado: true });
                }

                await this._aguardar(pollIntervalBase, signal);

                if (signal && signal.aborted) {
                    await this.cancelarJob(activeJobId);
                    return this._respostaVaziaErro('Operação cancelada pelo usuário. Nenhum jogo foi gerado.', { cancelado: true });
                }

                let respStatus = null;
                let statusData = null;
                try {
                    respStatus = await this._fetchComTimeout(
                        `${this.ENDPOINT_JOBS}/${encodeURIComponent(activeJobId)}`,
                        { method: 'GET', headers: { 'Accept': 'application/json' } },
                        12000,
                        signal
                    );
                } catch (pollErr) {
                    if (signal && signal.aborted) {
                        await this.cancelarJob(activeJobId);
                        return this._respostaVaziaErro('Operação cancelada pelo usuário. Nenhum jogo foi gerado.', { cancelado: true });
                    }
                    falhasTransitoriasSeguidas += 1;
                    if (falhasTransitoriasSeguidas > maxFalhasTransitorias) {
                        return this._respostaVaziaErro(this.MENSAGEM_INDISPONIVEL);
                    }
                    continue;
                }

                if (respStatus.status === 503) {
                    return this._respostaVaziaErro(this.MENSAGEM_INDISPONIVEL);
                }
                if (respStatus.status === 404) {
                    return this._respostaVaziaErro('Tarefa interrompida no servidor (sessão reiniciada ou expirada). Nenhum jogo foi gerado.');
                }

                try {
                    statusData = await respStatus.json();
                } catch (_parseErr) {
                    statusData = null;
                }

                if (!respStatus.ok || !statusData) {
                    falhasTransitoriasSeguidas += 1;
                    if (falhasTransitoriasSeguidas > maxFalhasTransitorias) {
                        const errDetail = (statusData && (statusData.erro || statusData.detail)) || this.MENSAGEM_INDISPONIVEL;
                        return this._respostaVaziaErro(typeof errDetail === 'string' ? errDetail : JSON.stringify(errDetail));
                    }
                    continue;
                }

                falhasTransitoriasSeguidas = 0;
                if (onProgress) onProgress(statusData);

                if (statusData.status === 'completed') {
                    break;
                }
                if (statusData.status === 'failed') {
                    const isSeloOuOffline = statusData.status_http === 503 || statusData.codigo_erro === 'SELO_INVALIDO';
                    const msgFalha = isSeloOuOffline
                        ? this.MENSAGEM_INDISPONIVEL
                        : (statusData.erro || 'Erro interno ao otimizar carteira no servidor oficial. Nenhum jogo foi gerado.');
                    return this._respostaVaziaErro(msgFalha);
                }
                if (statusData.status === 'cancelled') {
                    return this._respostaVaziaErro(
                        statusData.erro || 'Operação cancelada pelo usuário. Nenhum jogo foi gerado.',
                        { cancelado: true }
                    );
                }
            }

            if (Date.now() >= deadline) {
                await this.cancelarJob(activeJobId);
                return this._respostaVaziaErro('Tempo limite global de execução excedido no servidor matemático. Nenhum jogo foi gerado.');
            }

            // 3) Coleta do JSON completo validado (suporte folgado para carteiras ate 10.000 jogos)
            const respRes = await this._fetchComTimeout(
                `${this.ENDPOINT_JOBS}/${encodeURIComponent(activeJobId)}/resultado`,
                { method: 'GET', headers: { 'Accept': 'application/json' } },
                60000,
                signal
            );

            if (respRes.status === 503) {
                return this._respostaVaziaErro(this.MENSAGEM_INDISPONIVEL);
            }

            const data = await respRes.json();
            if (!respRes.ok || !data || data.sucesso !== true || !Array.isArray(data.jogos)) {
                const detailMsg = (data && (data.erro || data.detail))
                    ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))
                    : this.MENSAGEM_INDISPONIVEL;
                return this._respostaVaziaErro(detailMsg);
            }

            const respostaCompleta = data.jogos.length === validacaoQtd.valor && data.jogos.every(
                (j) => Array.isArray(j) && j.length === 50 && new Set(j).size === 50
            );
            if (!respostaCompleta) {
                return this._respostaVaziaErro(this.MENSAGEM_INDISPONIVEL);
            }

            return data;
        } catch (_err) {
            if (signal && signal.aborted && activeJobId) {
                await this.cancelarJob(activeJobId);
                return this._respostaVaziaErro('Operação cancelada pelo usuário. Nenhum jogo foi gerado.', { cancelado: true });
            }
            return this._respostaVaziaErro(this.MENSAGEM_INDISPONIVEL);
        }
    }

    /**
     * Solicita a conferência da carteira gerada contra um concurso oficial (1 a 2699) na API Python.
     */
    static async conferirCarteira(jogos, concurso = null) {
        if (!Array.isArray(jogos) || jogos.length === 0) {
            return {
                sucesso: false,
                erro: 'Nenhum jogo disponível na carteira para conferência.'
            };
        }

        let concVal = null;
        if (concurso !== undefined && concurso !== null && String(concurso).trim() !== '') {
            const parsedConc = Number(concurso);
            if (!Number.isInteger(parsedConc) || parsedConc < 1) {
                return {
                    sucesso: false,
                    erro: 'Número de concurso inválido para conferência.'
                };
            }
            concVal = parsedConc;
        }

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000);
            const resp = await fetch(this.ENDPOINT_CONFERIR, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    jogos: jogos,
                    concurso: concVal
                }),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (!resp.ok) {
                let errData = null;
                try { errData = await resp.json(); } catch (_e) {}
                return {
                    sucesso: false,
                    erro: (errData && (errData.erro || errData.detail)) ? (errData.erro || errData.detail) : this.MENSAGEM_INDISPONIVEL
                };
            }
            return await resp.json();
        } catch (_err) {
            return {
                sucesso: false,
                erro: this.MENSAGEM_INDISPONIVEL
            };
        }
    }
}

if (typeof window !== 'undefined') {
    window.MotorLotomaniaModo4Engine = MotorLotomaniaModo4Engine;
}
