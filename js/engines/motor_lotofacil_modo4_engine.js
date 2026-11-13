/**
 * MOTOR COMBINATÓRIO DE OTIMIZAÇÃO DE CARTEIRAS - LOTOFÁCIL | MODO 4 (Promoção Controlada)
 * =========================================================================================
 * Cliente HTTP estrito para o núcleo matemático Python oficial (127.0.0.1:8000).
 * REGIME FAIL-CLOSED E FEATURE FLAG CONTROLADA:
 * 1. Feature flag de produção iniciada como FALSE por padrão (`lotofacil_modo4_ativo = False`).
 * 2. PROIBIÇÃO ABSOLUTA DE FALLBACK JAVASCRIPT: este módulo não possui gerador local.
 *    Se a flag estiver desativada (HTTP 503), o servidor offline ou a integridade
 *    SHA-256/Ed25519 falhar, ZERO jogos são gerados.
 * 3. Política micro padrão conservadora (`conservadora_3J`); opção `experimental_2J`
 *    desabilitada por padrão e utilizada somente mediante habilitação configurada
 *    e seleção explícita. Inicialização mista travada em `padrao`.
 */

class MotorLotofacilModo4Engine {
    static API_BASE = 'http://127.0.0.1:8000';
    static ENDPOINT_HEALTH = 'http://127.0.0.1:8000/health';
    static ENDPOINT_STATUS = 'http://127.0.0.1:8000/api/v1/lotofacil-modo4/status';
    static ENDPOINT_GERAR = 'http://127.0.0.1:8000/api/v1/lotofacil-modo4/gerar';
    static ENDPOINT_AVALIAR = 'http://127.0.0.1:8000/api/v1/lotofacil-modo4/avaliar';

    static VERSAO = '5.1.0-promocao-controlada';
    static NOME_OFICIAL = 'LOTOFÁCIL MODO 4 | Otimizador Combinatório de Carteiras';

    static MENSAGEM_INDISPONIVEL = 'LOTOFÁCIL MODO 4 temporariamente indisponível. O servidor matemático oficial não está conectado. Nenhum jogo foi gerado.';
    static MENSAGEM_DESATIVADO_FLAG = 'LOTOFÁCIL MODO 4 desativado em produção por feature flag controlada (padrão OFF). Nenhum jogo foi gerado.';

    static CLAUSULA_MATEMATICA_OBRIGATORIA = 'O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.';

    static CUSTOS_CAIXA_REGULAR = {
        15: 3.50,
        16: 56.00,
        17: 476.00,
        18: 2856.00,
        19: 13566.00,
        20: 54264.00
    };

    static fmt(n) {
        return String(Number(n)).padStart(2, '0');
    }

    /**
     * Consulta `/health` para verificar disponibilidade, feature flag, política ativa e integridade.
     */
    static async verificarStatusServidor() {
        const estadoOffline = {
            conectado: false,
            disponivel: false,
            feature_flag_ativa: false,
            integridade_verificada: false,
            experimental_2j_habilitada: false,
            politica_micro_padrao: 'conservadora_3J',
            inicializacao_mista: 'padrao',
            status: 'desconectado',
            motivo_indisponibilidade: 'servidor_desconectado',
            versao_promocao: this.VERSAO,
            mensagem: this.MENSAGEM_INDISPONIVEL
        };

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
                return estadoOffline;
            }
            const data = await resp.json();
            const info = (data && data.lotofacil_modo4 && typeof data.lotofacil_modo4 === 'object')
                ? data.lotofacil_modo4
                : null;
            if (!info) {
                return estadoOffline;
            }
            const flagAtiva = info.feature_flag_ativa === true;
            const integridadeOk = info.integridade_verificada === true;
            const disponivel = info.disponivel === true && flagAtiva && integridadeOk;
            let mensagem = this.MENSAGEM_INDISPONIVEL;
            if (disponivel) {
                mensagem = 'LOTOFÁCIL MODO 4 ativo com integridade SHA-256/Ed25519 verificada.';
            } else if (!flagAtiva && integridadeOk) {
                mensagem = this.MENSAGEM_DESATIVADO_FLAG;
            }

            return {
                conectado: true,
                disponivel: disponivel,
                feature_flag_ativa: flagAtiva,
                integridade_verificada: integridadeOk,
                experimental_2j_habilitada: info.experimental_2j_habilitada === true,
                politica_micro_padrao: info.politica_micro_padrao || 'conservadora_3J',
                inicializacao_mista: info.inicializacao_mista || 'padrao',
                status: info.status || (disponivel ? 'ativo' : 'desativado_por_feature_flag'),
                motivo_indisponibilidade: info.motivo_indisponibilidade || null,
                versao_promocao: info.versao_promocao || this.VERSAO,
                versao_motor: info.versao_motor || null,
                mensagem: mensagem
            };
        } catch (_err) {
            return estadoOffline;
        }
    }

    static validarQuantidadeJogos(quantidadeJogos) {
        if (typeof quantidadeJogos !== 'number' || !Number.isInteger(quantidadeJogos) || Number.isNaN(quantidadeJogos)) {
            return {
                valido: false,
                erro: 'Quantidade inválida: informe um número inteiro estrito entre 1 e 5.000 jogos.'
            };
        }
        if (quantidadeJogos < 1 || quantidadeJogos > 5000) {
            return {
                valido: false,
                erro: 'Fora do intervalo permitido pelo LOTOFÁCIL MODO 4: selecione entre 1 e 5.000 jogos.'
            };
        }
        return { valido: true, valor: quantidadeJogos };
    }

    static validarTamanhoAposta(tamanhoAposta) {
        if (typeof tamanhoAposta !== 'number' || !Number.isInteger(tamanhoAposta) || Number.isNaN(tamanhoAposta)) {
            return {
                valido: false,
                erro: 'Tamanho da aposta inválido: selecione um inteiro entre 15 e 20 dezenas.'
            };
        }
        if (tamanhoAposta < 15 || tamanhoAposta > 20) {
            return {
                valido: false,
                erro: 'Tamanho da aposta fora das regras oficiais da CAIXA (15 a 20 dezenas).'
            };
        }
        return { valido: true, valor: tamanhoAposta };
    }

    static _aplicarRestricoesPool(payload, options = {}) {
        if (Array.isArray(options.fixas) && options.fixas.length > 0) {
            payload.fixas = options.fixas.map(Number);
        }
        if (Array.isArray(options.bloqueadas) && options.bloqueadas.length > 0) {
            payload.bloqueadas = options.bloqueadas.map(Number);
        }
        if (Array.isArray(options.pool) && options.pool.length > 0) {
            payload.pool = options.pool.map(Number);
        } else if (Array.isArray(payload.bloqueadas) && payload.bloqueadas.length > 0) {
            const blqSet = new Set(payload.bloqueadas);
            payload.pool = Array.from({ length: 25 }, (_, i) => i + 1).filter((n) => !blqSet.has(n));
        }
    }

    /**
     * Solicita geração fail-closed ao endpoint oficial Python `/api/v1/lotofacil-modo4/gerar`.
     * Nenhum fallback local é executado em caso de erro, flag desligada ou offline.
     */
    static async gerarCarteira(options = {}) {
        const qtd = options.quantidadeJogos !== undefined ? Number(options.quantidadeJogos) : 8;
        const valQtd = this.validarQuantidadeJogos(qtd);
        if (!valQtd.valido) {
            return {
                sucesso: false,
                jogos: [],
                quantidade_entregue: 0,
                fallback_executado: false,
                erro: valQtd.erro
            };
        }

        const tamanhoAposta = options.tamanhoAposta !== undefined ? Number(options.tamanhoAposta) : 15;
        const valTam = this.validarTamanhoAposta(tamanhoAposta);
        if (!valTam.valido) {
            return {
                sucesso: false,
                jogos: [],
                quantidade_entregue: 0,
                fallback_executado: false,
                erro: valTam.erro
            };
        }

        let sementeVal = 42;
        if (options.semente !== undefined && options.semente !== null && String(options.semente).trim() !== '') {
            if (typeof options.semente === 'boolean') {
                return {
                    sucesso: false,
                    jogos: [],
                    quantidade_entregue: 0,
                    fallback_executado: false,
                    erro: 'Parâmetro semente inválido: informe um número inteiro não negativo.'
                };
            }
            const parsedSeed = Number(options.semente);
            if (!Number.isInteger(parsedSeed) || parsedSeed < 0) {
                return {
                    sucesso: false,
                    jogos: [],
                    quantidade_entregue: 0,
                    fallback_executado: false,
                    erro: 'Parâmetro semente inválido: informe um número inteiro não negativo.'
                };
            }
            sementeVal = parsedSeed;
        }

        const usarExperimental2J = options.usarExperimental2J === true;
        const politicaMicro = usarExperimental2J ? 'experimental_2J' : 'conservadora_3J';

        const payload = {
            quantidade_jogos: valQtd.valor,
            tamanho_aposta: valTam.valor,
            tipo_concurso: options.tipoConcurso || 'concurso_regular',
            prioridade: options.prioridade || 'equilibrio_adaptativo',
            semente: sementeVal,
            politica_micro: politicaMicro,
            inicializacao_mista: 'padrao'
        };

        this._aplicarRestricoesPool(payload, options);

        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 120000);
            const resp = await fetch(this.ENDPOINT_GERAR, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                signal: controller.signal
            });
            clearTimeout(timeoutId);

            let data = null;
            try {
                data = await resp.json();
            } catch (_parseErr) {
                return {
                    sucesso: false,
                    jogos: [],
                    quantidade_entregue: 0,
                    fallback_executado: false,
                    erro: this.MENSAGEM_INDISPONIVEL
                };
            }

            if (resp.status === 503) {
                const detailObj = (data && data.detail && typeof data.detail === 'object') ? data.detail : data;
                const motivo = detailObj && detailObj.motivo ? detailObj.motivo : '';
                const msg = (detailObj && detailObj.mensagem)
                    ? detailObj.mensagem
                    : (motivo === 'feature_flag_desativada' ? this.MENSAGEM_DESATIVADO_FLAG : this.MENSAGEM_INDISPONIVEL);
                return {
                    sucesso: false,
                    jogos: [],
                    quantidade_entregue: 0,
                    fallback_executado: false,
                    motivo: motivo || 'indisponivel_503',
                    erro: msg
                };
            }

            if (
                !resp.ok ||
                !data ||
                data.sucesso !== true ||
                data.fallback_executado !== false ||
                data.historico_utilizado !== null ||
                !Array.isArray(data.jogos) ||
                data.jogos.length !== valQtd.valor
            ) {
                const detailObj = (data && data.detail && typeof data.detail === 'object') ? data.detail : data;
                const msgErro = (detailObj && (detailObj.mensagem || detailObj.erro))
                    ? (detailObj.mensagem || detailObj.erro)
                    : this.MENSAGEM_INDISPONIVEL;
                return {
                    sucesso: false,
                    jogos: [],
                    quantidade_entregue: 0,
                    fallback_executado: false,
                    erro: typeof msgErro === 'string' ? msgErro : JSON.stringify(msgErro)
                };
            }

            const bilhetesValidos = data.jogos.every(
                (j) => Array.isArray(j) && j.length === valTam.valor && new Set(j).size === valTam.valor &&
                    j.every((d) => Number.isInteger(d) && d >= 1 && d <= 25)
            );
            if (!bilhetesValidos) {
                return {
                    sucesso: false,
                    jogos: [],
                    quantidade_entregue: 0,
                    fallback_executado: false,
                    erro: 'Contrato da carteira retornada violou invariantes da Lotofácil. Nenhum jogo foi aceito.'
                };
            }

            return data;
        } catch (_err) {
            return {
                sucesso: false,
                jogos: [],
                quantidade_entregue: 0,
                fallback_executado: false,
                erro: this.MENSAGEM_INDISPONIVEL
            };
        }
    }

    /**
     * Solicita auditoria matemática fail-closed de uma carteira ao endpoint `/api/v1/lotofacil-modo4/avaliar`.
     */
    static async avaliarCarteira(jogos, options = {}) {
        if (!Array.isArray(jogos) || jogos.length === 0) {
            return {
                sucesso: false,
                fallback_executado: false,
                erro: 'Nenhuma carteira disponível para auditoria no LOTOFÁCIL MODO 4.'
            };
        }
        try {
            const controller = new AbortController();
            const timeoutId = setTimeout(() => controller.abort(), 30000);
            const payload = { carteira: jogos };
            this._aplicarRestricoesPool(payload, options);

            const resp = await fetch(this.ENDPOINT_AVALIAR, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload),
                signal: controller.signal
            });
            clearTimeout(timeoutId);
            let data = null;
            try { data = await resp.json(); } catch (_e) {}
            if (!resp.ok || !data || data.sucesso !== true) {
                const detailObj = (data && data.detail && typeof data.detail === 'object') ? data.detail : data;
                const msg = (detailObj && (detailObj.mensagem || detailObj.erro))
                    ? (detailObj.mensagem || detailObj.erro)
                    : this.MENSAGEM_INDISPONIVEL;
                return {
                    sucesso: false,
                    fallback_executado: false,
                    erro: typeof msg === 'string' ? msg : JSON.stringify(msg)
                };
            }
            return data;
        } catch (_err) {
            return {
                sucesso: false,
                fallback_executado: false,
                erro: this.MENSAGEM_INDISPONIVEL
            };
        }
    }
}

if (typeof window !== 'undefined') {
    window.MotorLotofacilModo4Engine = MotorLotofacilModo4Engine;
}
