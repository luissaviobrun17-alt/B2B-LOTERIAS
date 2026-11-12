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

    /**
     * Consulta o endpoint /health do servidor Python para verificar disponibilidade e selo Ed25519.
     */
    static async verificarStatusServidor() {
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 2500);
            const resp = await fetch(this.ENDPOINT_HEALTH, {
                method: 'GET',
                headers: { 'Accept': 'application/json' },
                signal: controller.signal
            });
            clearTimeout(timeoutId);
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
     * Solicita a geração de carteira ao servidor Python oficial do MODO 4 v1.2.
     * Não existe fallback local: qualquer falha de conexão retorna zero jogos.
     */
    static async gerarCarteira(quantidadeJogos, options = {}) {
        const validacaoQtd = this.validarQuantidadeJogos(quantidadeJogos);
        if (!validacaoQtd.valido) {
            return {
                sucesso: false,
                jogos: [],
                jogos_formatados: [],
                quantidade_entregue: 0,
                erro: validacaoQtd.erro
            };
        }

        const permitirEspelhos = (options.permitirEspelhos !== undefined)
            ? Boolean(options.permitirEspelhos)
            : (options.incluirEspelho !== undefined ? Boolean(options.incluirEspelho) : true);

        let seedVal = null;
        if (options.seed !== undefined && options.seed !== null && String(options.seed).trim() !== '') {
            if (typeof options.seed === 'boolean') {
                return {
                    sucesso: false,
                    jogos: [],
                    jogos_formatados: [],
                    quantidade_entregue: 0,
                    erro: 'Parâmetro seed inválido: deve ser um número inteiro ou vazio.'
                };
            }
            const parsedSeed = Number(options.seed);
            if (!Number.isInteger(parsedSeed)) {
                return {
                    sucesso: false,
                    jogos: [],
                    jogos_formatados: [],
                    quantidade_entregue: 0,
                    erro: 'Parâmetro seed inválido: deve ser um número inteiro ou vazio.'
                };
            }
            seedVal = parsedSeed;
        }

        const payload = {
            quantidade_jogos: validacaoQtd.valor,
            permitir_espelhos: permitirEspelhos,
            seed: seedVal,
            trace: Boolean(options.trace === true)
        };

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 180000);

            const resp = await fetch(this.ENDPOINT_GERAR, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            if (resp.status === 503) {
                return {
                    sucesso: false,
                    jogos: [],
                    jogos_formatados: [],
                    quantidade_entregue: 0,
                    erro: this.MENSAGEM_INDISPONIVEL
                };
            }

            const data = await resp.json();
            if (!resp.ok || !data || data.sucesso !== true || !Array.isArray(data.jogos)) {
                const detailMsg = (data && (data.erro || data.detail))
                    ? (typeof data.detail === 'string' ? data.detail : JSON.stringify(data.detail))
                    : this.MENSAGEM_INDISPONIVEL;
                return {
                    sucesso: false,
                    jogos: [],
                    jogos_formatados: [],
                    quantidade_entregue: 0,
                    erro: detailMsg
                };
            }

            const respostaCompleta = data.jogos.length === validacaoQtd.valor && data.jogos.every(
                (j) => Array.isArray(j) && j.length === 50 && new Set(j).size === 50
            );
            if (!respostaCompleta) {
                return {
                    sucesso: false,
                    jogos: [],
                    jogos_formatados: [],
                    quantidade_entregue: 0,
                    erro: this.MENSAGEM_INDISPONIVEL
                };
            }

            return data;
        } catch (_err) {
            return {
                sucesso: false,
                jogos: [],
                jogos_formatados: [],
                quantidade_entregue: 0,
                erro: this.MENSAGEM_INDISPONIVEL
            };
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
