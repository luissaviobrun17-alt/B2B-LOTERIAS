// ═══════════════════════════════════════════════════════════════════
// ║  STATISTICS TRACKER v1.0 — Módulo de Estatísticas B2B Loterias ║
// ║  Persiste resultados de conferência no localStorage             ║
// ║  Suporta filtros, ROI, exportação CSV                           ║
// ═══════════════════════════════════════════════════════════════════

const StatisticsTracker = (function() {
    'use strict';

    const STORAGE_KEY = 'b2b_stats_history';
    const VERSION = '1.0';

    // ── Helpers ──────────────────────────────────────────────────
    function _loadAll() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return {};
            const data = JSON.parse(raw);
            return data || {};
        } catch(e) {
            console.warn('[Stats] Erro ao carregar dados:', e);
            return {};
        }
    }

    function _saveAll(data) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
        } catch(e) {
            console.error('[Stats] Erro ao salvar dados:', e);
        }
    }

    // ── Gerar ID único para cada registro ──
    function _generateId() {
        return Date.now().toString(36) + Math.random().toString(36).substr(2, 5);
    }

    // ── API Pública ─────────────────────────────────────────────

    /**
     * Salvar um registro de conferência
     * @param {Object} record
     * @param {string} record.lotteryKey     - ex: 'megasena', 'lotofacil'
     * @param {string} record.lotteryName    - ex: 'Mega Sena'
     * @param {number} record.concurso       - Número do concurso
     * @param {string} record.drawInfo       - Info do sorteio (ex: "Concurso 2800")
     * @param {string} record.data           - Data da conferência (ISO string)
     * @param {number} record.qtdJogos       - Quantidade de jogos conferidos
     * @param {string} record.modoGeracao    - 'quantum_l99' | 'gerar_jogos' | 'dual_2g' | 'fechamento' | 'manual'
     * @param {boolean} record.precisao      - Se Modo Precisão estava ativo
     * @param {number} record.numPorJogo     - Números por jogo (drawSize)
     * @param {Object} record.faixas         - { stratId: { label, match, count, prizeUnit } }
     * @param {number} record.volantesPremiados - Total de volantes que ganharam
     * @param {number} record.valorPremio    - Valor total estimado ganho
     * @param {number} record.valorInvestido - Custo total investido
     * @param {number} record.pctRetorno     - Percentual de retorno (%)
     * @param {string} record.internalEngine - Motor que gerou os jogos (CoverageEngine, etc)
     * @param {number[]} record.drawnNumbers - Números sorteados
     */
    function save(record) {
        if (!record || !record.lotteryKey) {
            console.warn('[Stats] Registro inválido, ignorando.');
            return;
        }

        const all = _loadAll();
        const key = record.lotteryKey;

        if (!all[key]) {
            all[key] = [];
        }

        // Adicionar metadados
        record.id = _generateId();
        record.timestamp = Date.now();
        record.version = VERSION;

        // Calcular ROI se não fornecido
        if (record.valorInvestido > 0 && record.pctRetorno == null) {
            record.pctRetorno = ((record.valorPremio - record.valorInvestido) / record.valorInvestido * 100);
        }

        all[key].push(record);
        _saveAll(all);

        console.log(`[Stats] ✅ Registro salvo: ${record.lotteryName} | Concurso ${record.concurso} | ${record.qtdJogos} jogos | Modo: ${record.modoGeracao}`);
        return record.id;
    }

    /**
     * Obter todos os registros de uma loteria
     * @param {string} lotteryKey
     * @returns {Array}
     */
    function getAll(lotteryKey) {
        const all = _loadAll();
        return (all[lotteryKey] || []).sort((a, b) => (b.timestamp || 0) - (a.timestamp || 0));
    }

    /**
     * Obter contagem total de registros
     * @returns {Object} { lotteryKey: count }
     */
    function getCounts() {
        const all = _loadAll();
        const counts = {};
        Object.keys(all).forEach(key => {
            counts[key] = (all[key] || []).length;
        });
        return counts;
    }

    /**
     * Filtrar registros por critérios
     * @param {string} lotteryKey
     * @param {Object} filters
     * @param {string} [filters.modoGeracao]  - 'quantum_l99' | 'gerar_jogos' etc
     * @param {boolean} [filters.precisao]
     * @param {number} [filters.numPorJogo]
     * @param {number} [filters.qtdJogos]
     * @param {number} [filters.concurso]
     * @param {string} [filters.dateFrom]     - ISO date string
     * @param {string} [filters.dateTo]       - ISO date string
     * @returns {Array}
     */
    function filter(lotteryKey, filters) {
        let records = getAll(lotteryKey);

        if (!filters) return records;

        if (filters.modoGeracao && filters.modoGeracao !== 'todos') {
            records = records.filter(r => r.modoGeracao === filters.modoGeracao);
        }
        if (filters.precisao !== undefined && filters.precisao !== null && filters.precisao !== 'todos') {
            const val = filters.precisao === true || filters.precisao === 'true' || filters.precisao === 'sim';
            records = records.filter(r => r.precisao === val);
        }
        if (filters.numPorJogo && filters.numPorJogo !== 'todos') {
            records = records.filter(r => r.numPorJogo === parseInt(filters.numPorJogo));
        }
        if (filters.qtdJogos && filters.qtdJogos !== 'todos') {
            records = records.filter(r => r.qtdJogos === parseInt(filters.qtdJogos));
        }
        if (filters.concurso) {
            records = records.filter(r => r.concurso === parseInt(filters.concurso));
        }
        if (filters.dateFrom) {
            const from = new Date(filters.dateFrom).getTime();
            records = records.filter(r => (r.timestamp || 0) >= from);
        }
        if (filters.dateTo) {
            const to = new Date(filters.dateTo).getTime() + 86400000;
            records = records.filter(r => (r.timestamp || 0) <= to);
        }

        return records;
    }

    /**
     * Calcular estatísticas agregadas
     * @param {Array} records
     * @returns {Object}
     */
    function aggregate(records) {
        if (!records || records.length === 0) {
            return {
                total: 0,
                totalJogos: 0,
                totalInvestido: 0,
                totalPremio: 0,
                pctRetornoMedio: 0,
                totalVolantesPremiados: 0,
                melhorRetorno: 0,
                piorRetorno: 0
            };
        }

        const totalJogos = records.reduce((s, r) => s + (r.qtdJogos || 0), 0);
        const totalInvestido = records.reduce((s, r) => s + (r.valorInvestido || 0), 0);
        const totalPremio = records.reduce((s, r) => s + (r.valorPremio || 0), 0);
        const totalVolantesPremiados = records.reduce((s, r) => s + (r.volantesPremiados || 0), 0);
        const retornos = records.map(r => r.pctRetorno || 0);

        return {
            total: records.length,
            totalJogos,
            totalInvestido,
            totalPremio,
            pctRetornoMedio: totalInvestido > 0 ? ((totalPremio - totalInvestido) / totalInvestido * 100) : 0,
            totalVolantesPremiados,
            melhorRetorno: Math.max(...retornos),
            piorRetorno: Math.min(...retornos)
        };
    }

    /**
     * Obter valores únicos de uma coluna para filtros
     * @param {string} lotteryKey
     * @param {string} field
     * @returns {Array}
     */
    function getUniqueValues(lotteryKey, field) {
        const records = getAll(lotteryKey);
        const unique = new Set();
        records.forEach(r => {
            if (r[field] !== undefined && r[field] !== null) {
                unique.add(r[field]);
            }
        });
        return [...unique].sort();
    }

    /**
     * Exportar dados como CSV
     * @param {string} [lotteryKey] - Se não informado, exporta todas
     * @returns {string} CSV content
     */
    function exportCSV(lotteryKey) {
        const all = _loadAll();
        const keys = lotteryKey ? [lotteryKey] : Object.keys(all);
        
        let csv = 'Loteria;Concurso;Data;Qtd Jogos;Modo Geração;Motor Real;Precisão;Nº/Jogo;Volantes Premiados;Valor Prêmio;Valor Investido;% Retorno;Faixas Detalhadas\n';

        keys.forEach(key => {
            const records = all[key] || [];
            records.forEach(r => {
                const data = r.data ? new Date(r.data).toLocaleDateString('pt-BR') : '';
                const faixasStr = r.faixas ? Object.values(r.faixas).map(f => `${f.label}:${f.count}`).join('|') : '';
                csv += [
                    r.lotteryName || key,
                    r.concurso || '',
                    data,
                    r.qtdJogos || 0,
                    _modoLabel(r.modoGeracao),
                    r.internalEngine || 'Desconhecido',
                    r.precisao ? 'Sim' : 'Não',
                    r.numPorJogo || '',
                    r.volantesPremiados || 0,
                    (r.valorPremio || 0).toFixed(2),
                    (r.valorInvestido || 0).toFixed(2),
                    (r.pctRetorno || 0).toFixed(1),
                    faixasStr
                ].join(';') + '\n';
            });
        });

        return csv;
    }

    /**
     * Importar dados de CSV
     * @param {string} csvContent
     * @returns {number} Quantidade de registros importados
     */
    function importCSV(csvContent) {
        const lines = csvContent.split('\n').filter(l => l.trim());
        if (lines.length < 2) return 0;

        const all = _loadAll();
        let imported = 0;

        for (let i = 1; i < lines.length; i++) {
            const cols = lines[i].split(';');
            if (cols.length < 10) continue;

            // Encontrar a chave da loteria pelo nome
            const lotteryName = cols[0].trim();
            let lotteryKey = _findKeyByName(lotteryName);
            if (!lotteryKey) continue;

            if (!all[lotteryKey]) all[lotteryKey] = [];

            const record = {
                id: _generateId(),
                lotteryKey: lotteryKey,
                lotteryName: lotteryName,
                concurso: parseInt(cols[1]) || 0,
                data: cols[2] || new Date().toISOString(),
                qtdJogos: parseInt(cols[3]) || 0,
                modoGeracao: _modoFromLabel(cols[4].trim()),
                internalEngine: cols[5] ? cols[5].trim() : 'Desconhecido',
                precisao: cols[6] ? cols[6].trim().toLowerCase() === 'sim' : false,
                numPorJogo: parseInt(cols[7]) || 0,
                volantesPremiados: parseInt(cols[8]) || 0,
                valorPremio: parseFloat(cols[9]) || 0,
                valorInvestido: parseFloat(cols[10]) || 0,
                pctRetorno: parseFloat(cols[11]) || 0,
                timestamp: Date.now(),
                version: VERSION,
                imported: true
            };

            all[lotteryKey].push(record);
            imported++;
        }

        _saveAll(all);
        console.log(`[Stats] ✅ ${imported} registros importados.`);
        return imported;
    }

    /**
     * Limpar registros de uma loteria
     * @param {string} lotteryKey
     */
    function clear(lotteryKey) {
        const all = _loadAll();
        if (lotteryKey) {
            delete all[lotteryKey];
        } else {
            Object.keys(all).forEach(k => delete all[k]);
        }
        _saveAll(all);
        console.log(`[Stats] 🗑️ Dados limpos: ${lotteryKey || 'TODOS'}`);
    }

    /**
     * Excluir um registro específico
     * @param {string} lotteryKey
     * @param {string} recordId
     */
    function remove(lotteryKey, recordId) {
        const all = _loadAll();
        if (all[lotteryKey]) {
            all[lotteryKey] = all[lotteryKey].filter(r => r.id !== recordId);
            _saveAll(all);
        }
    }

    // ── Helpers internos ────────────────────────────────────────
    function _modoLabel(modo) {
        const labels = {
            'manual': '🎲 Manual',
            'cobertura': '📐 Cobertura IA',
            'cobertura_sniper': '📐🎯 Cobertura+Sniper',
            'quantum_l99': '⚡ QUANTUM L99',
            'precision': '🎯 Precisão',
            // Retrocompatibilidade
            'estatistica': '⚡ QUANTUM L99',
            'manual_sniper': '✋🎯 Manual+Sniper',
            'precision_sniper': '🎯🔫 Precisão+Sniper',
            'precision_l99': '⚡ QUANTUM L99',
            'gerar_jogos': '🎲 Manual',
            'dual_2g': '⚡ Dual 2G',
            'fechamento': '🔒 Fechamento'
        };
        return labels[modo] || modo || '🎲 Manual';
    }

    function _modoFromLabel(label) {
        const map = {
            'manual': 'manual',
            'estatistica': 'estatistica',
            'estatística': 'estatistica',
            'cobertura': 'cobertura',
            'cobertura+sniper': 'cobertura_sniper',
            'cobertura sniper': 'cobertura_sniper',
            'precisão': 'precision',
            'precisao': 'precision',
            'precisão+sniper': 'precision_sniper',
            'precisao+sniper': 'precision_sniper',
            // Retrocompatibilidade
            'manual+sniper': 'manual_sniper',
            'manual sniper': 'manual_sniper',
            'precisão sniper': 'precision_sniper',
            'precisao sniper': 'precision_sniper',
            'quantum l99': 'quantum_l99',
            'quantum_l99': 'quantum_l99',
            'jogar l99': 'precision',
            'precision l99': 'precision',
            'gerar jogos': 'manual',
            'dual 2g': 'dual_2g',
            'fechamento': 'fechamento'
        };
        // Strip emoji prefixes for matching
        const clean = (label || '').toLowerCase().replace(/[⚡🎯🎲🔒✋📐🔫📊]/g, '').trim();
        return map[clean] || 'manual';
    }

    function _findKeyByName(name) {
        const nameMap = {
            'mega sena': 'megasena',
            'mega-sena': 'megasena',
            'megasena': 'megasena',
            'lotofácil': 'lotofacil',
            'lotofacil': 'lotofacil',
            'quina': 'quina',
            'dupla sena': 'duplasena',
            'dupla-sena': 'duplasena',
            'duplasena': 'duplasena',
            'lotomania': 'lotomania',
            'timemania': 'timemania',
            'dia de sorte': 'diadesorte',
            'dia-de-sorte': 'diadesorte',
            'diadesorte': 'diadesorte'
        };
        return nameMap[(name || '').toLowerCase()] || null;
    }

    // ── Expor API ───────────────────────────────────────────────
    return {
        save,
        getAll,
        getCounts,
        filter,
        aggregate,
        getUniqueValues,
        exportCSV,
        importCSV,
        clear,
        remove,
        getModoLabel: _modoLabel,
        VERSION
    };

})();
