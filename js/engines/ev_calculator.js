/**
 * ============================================================
 *  EVCalculator — Valor Esperado para Loterias da Caixa
 * ============================================================
 *  Calcula probabilidade hipergeométrica e Valor Esperado (EV)
 *  para cada faixa de premiação das loterias brasileiras.
 *
 *  Sem dependências externas. Funciona direto no browser.
 *  Usa BigInt internamente para evitar overflow em C(n,k).
 * ============================================================
 */

class EVCalculator {

  // ──────────────────────────────────────────────
  //  Dados de premiação embutidos por loteria
  // ──────────────────────────────────────────────

  /** @returns {Object} Configuração de cada jogo */
  static get GAMES() {
    return {

      megasena: {
        nome: 'Mega-Sena',
        N: 60,   // universo de números
        K: 6,    // números sorteados
        n: 6,    // números apostados (aposta mínima)
        custo: 6.00,
        premios: { 6: 50_000_000, 5: 40_000, 4: 800 },
        multiplicador: 1,   // sorteio único
        descricao: '6 dezenas de 01 a 60'
      },

      lotofacil: {
        nome: 'Lotofácil',
        N: 25,
        K: 15,
        n: 15,
        custo: 3.50,
        premios: { 15: 1_500_000, 14: 1_200, 13: 30, 12: 12, 11: 6 },
        multiplicador: 1,
        descricao: '15 dezenas de 01 a 25'
      },

      quina: {
        nome: 'Quina',
        N: 80,
        K: 5,
        n: 5,
        custo: 3.00,
        premios: { 5: 8_000_000, 4: 6_000, 3: 100, 2: 3 },
        multiplicador: 1,
        descricao: '5 dezenas de 01 a 80'
      },

      duplasena: {
        nome: 'Dupla Sena',
        N: 50,
        K: 6,
        n: 6,
        custo: 3.00,
        premios: { 6: 3_000_000, 5: 1_500, 4: 10 },
        multiplicador: 2,   // dois sorteios independentes
        descricao: '6 dezenas de 01 a 50 (2 sorteios)'
      },

      lotomania: {
        nome: 'Lotomania',
        N: 100,
        K: 20,
        n: 50,
        custo: 3.00,
        premios: { 20: 3_000_000, 19: 30_000, 18: 1_500, 17: 100, 16: 30, 15: 6, 0: 3_000_000 },
        multiplicador: 1,
        descricao: '50 dezenas de 00 a 99'
      },

      timemania: {
        nome: 'Timemania',
        N: 80,
        K: 7,
        n: 10,
        custo: 3.50,
        premios: { 7: 5_000_000, 6: 50_000, 5: 500, 4: 10, 3: 3 },
        multiplicador: 1,
        descricao: '10 dezenas de 01 a 80'
      },

      diadesorte: {
        nome: 'Dia de Sorte',
        N: 31,
        K: 7,
        n: 7,
        custo: 3.00,
        premios: { 7: 1_500_000, 6: 5_000, 5: 50, 4: 5 },
        multiplicador: 1,
        descricao: '7 dezenas de 01 a 31'
      }
    };
  }

  // ──────────────────────────────────────────────
  //  Combinação C(n, k) usando BigInt
  // ──────────────────────────────────────────────

  /**
   * Calcula C(n, k) = n! / (k! * (n-k)!)
   * Usa BigInt para evitar overflow com números grandes.
   * @param {number} n - total de elementos
   * @param {number} k - elementos escolhidos
   * @returns {BigInt} valor da combinação
   */
  static comb(n, k) {
    // Casos triviais
    if (k < 0 || k > n) return 0n;
    if (k === 0 || k === n) return 1n;

    // Otimização: C(n,k) == C(n, n-k), usa o menor
    if (k > n - k) k = n - k;

    let resultado = 1n;
    const bn = BigInt(n);

    for (let i = 0; i < k; i++) {
      resultado = resultado * (bn - BigInt(i)) / (BigInt(i) + 1n);
    }

    return resultado;
  }

  // ──────────────────────────────────────────────
  //  Probabilidade Hipergeométrica
  // ──────────────────────────────────────────────

  /**
   * Calcula P(X = k) pela distribuição hipergeométrica.
   *
   * Fórmula:  P(X=k) = C(K,k) * C(N-K, n-k) / C(N,n)
   *
   * @param {number} N - tamanho do universo (ex: 60 para Mega-Sena)
   * @param {number} K - número de "sucessos" no universo (números sorteados)
   * @param {number} n - tamanho da amostra (números apostados)
   * @param {number} k - acertos desejados
   * @returns {number} probabilidade entre 0 e 1
   */
  static hypergeometric(N, K, n, k) {
    // Validações rápidas
    if (k < 0 || k > Math.min(K, n)) return 0;
    if (k > K || (n - k) > (N - K)) return 0;

    const numerador = this.comb(K, k) * this.comb(N - K, n - k);
    const denominador = this.comb(N, n);

    if (denominador === 0n) return 0;

    // Converte BigInt para Number com precisão adequada
    return Number(numerador * 1_000_000_000_000_000n / denominador) / 1e15;
  }

  // ──────────────────────────────────────────────
  //  Cálculo do Valor Esperado (EV)
  // ──────────────────────────────────────────────

  /**
   * Calcula o Valor Esperado completo para uma loteria.
   *
   * @param {string} gameKey - chave do jogo (ex: 'megasena')
   * @returns {Object} { breakdown, totalEV, betCost, netEV, returnPct }
   *   - breakdown: array com detalhes de cada faixa
   *   - totalEV: valor esperado bruto (R$)
   *   - betCost: custo da aposta (R$)
   *   - netEV: valor esperado líquido (totalEV - betCost)
   *   - returnPct: percentual de retorno (totalEV / betCost * 100)
   */
  static calculateEV(gameKey) {
    const jogo = this.GAMES[gameKey];

    if (!jogo) {
      throw new Error(`Loteria "${gameKey}" não encontrada. Opções: ${Object.keys(this.GAMES).join(', ')}`);
    }

    const { N, K, n, custo, premios, multiplicador } = jogo;
    const breakdown = [];
    let totalEV = 0;

    // Percorre cada faixa de premiação
    for (const [acertosStr, premio] of Object.entries(premios)) {
      const acertos = parseInt(acertosStr, 10);
      const prob = this.hypergeometric(N, K, n, acertos);

      // Probabilidade efetiva considera o multiplicador (ex: Dupla Sena = x2)
      // Para múltiplos sorteios independentes:
      // P(acertar em pelo menos 1) ≈ 1 - (1 - p)^m
      // Mas para EV simples, basta multiplicar: EV = m * p * premio
      const probEfetiva = prob * multiplicador;
      const evFaixa = probEfetiva * premio;

      // Calcula odds (1 em X)
      const odds = prob > 0 ? Math.round(1 / prob) : Infinity;

      breakdown.push({
        acertos,
        premio,
        probabilidade: prob,
        probEfetiva,
        odds,
        oddsTexto: prob > 0 ? `1 em ${odds.toLocaleString('pt-BR')}` : 'impossível',
        ev: evFaixa,
        evFormatado: this._formatarMoeda(evFaixa)
      });

      totalEV += evFaixa;
    }

    // Ordena do maior para o menor número de acertos
    breakdown.sort((a, b) => b.acertos - a.acertos);

    const netEV = totalEV - custo;
    const returnPct = (totalEV / custo) * 100;

    return {
      gameKey,
      nome: jogo.nome,
      descricao: jogo.descricao,
      breakdown,
      totalEV,
      totalEVFormatado: this._formatarMoeda(totalEV),
      betCost: custo,
      betCostFormatado: this._formatarMoeda(custo),
      netEV,
      netEVFormatado: this._formatarMoeda(netEV),
      returnPct,
      returnPctFormatado: returnPct.toFixed(2) + '%',
      multiplicador
    };
  }

  // ──────────────────────────────────────────────
  //  Resumo formatado em português
  // ──────────────────────────────────────────────

  /**
   * Retorna um texto formatado com o resumo do EV.
   * Ideal para exibição em console ou UI.
   *
   * @param {string} gameKey - chave do jogo
   * @returns {string} texto formatado em português
   */
  static getEVSummary(gameKey) {
    const ev = this.calculateEV(gameKey);
    const linhas = [];

    linhas.push('╔══════════════════════════════════════════════╗');
    linhas.push(`║  📊 VALOR ESPERADO — ${ev.nome.toUpperCase().padEnd(23)}║`);
    linhas.push('╠══════════════════════════════════════════════╣');
    linhas.push(`║  ${ev.descricao.padEnd(43)}║`);

    if (ev.multiplicador > 1) {
      linhas.push(`║  ⚡ ${ev.multiplicador} sorteios por aposta${' '.repeat(23)}║`);
    }

    linhas.push('╠══════════════════════════════════════════════╣');
    linhas.push('║  Acertos │  Prêmio     │ Probabilidade │ EV  ║');
    linhas.push('╠══════════════════════════════════════════════╣');

    for (const faixa of ev.breakdown) {
      const ac = String(faixa.acertos).padStart(2);
      const pr = this._formatarMoedaCurta(faixa.premio).padStart(10);
      const od = faixa.oddsTexto.padStart(14);
      const evf = faixa.evFormatado.padStart(8);
      linhas.push(`║    ${ac}   │ ${pr} │ ${od} │${evf}║`);
    }

    linhas.push('╠══════════════════════════════════════════════╣');
    linhas.push(`║  Custo da aposta:  ${ev.betCostFormatado.padStart(10)}${' '.repeat(16)}║`);
    linhas.push(`║  EV bruto:         ${ev.totalEVFormatado.padStart(10)}${' '.repeat(16)}║`);
    linhas.push(`║  EV líquido:       ${ev.netEVFormatado.padStart(10)}${' '.repeat(16)}║`);
    linhas.push(`║  Retorno:          ${ev.returnPctFormatado.padStart(10)}${' '.repeat(16)}║`);
    linhas.push('╚══════════════════════════════════════════════╝');

    // Análise qualitativa
    if (ev.returnPct < 30) {
      linhas.push('⚠️  Retorno muito baixo — aposta altamente desfavorável.');
    } else if (ev.returnPct < 50) {
      linhas.push('⚠️  Retorno baixo — a casa tem grande vantagem.');
    } else if (ev.returnPct < 80) {
      linhas.push('📉 Retorno moderado — ainda desfavorável ao apostador.');
    } else {
      linhas.push('📈 Retorno relativamente alto para uma loteria.');
    }

    return linhas.join('\n');
  }

  // ──────────────────────────────────────────────
  //  EV para múltiplos jogos
  // ──────────────────────────────────────────────

  /**
   * Calcula o EV ao apostar N jogos da mesma loteria.
   *
   * @param {string} gameKey - chave do jogo
   * @param {number} numGames - quantidade de apostas
   * @returns {Object} resultado com EV total, custo total, etc.
   */
  static calcMultiGameEV(gameKey, numGames) {
    if (!Number.isInteger(numGames) || numGames < 1) {
      throw new Error('numGames deve ser um inteiro positivo.');
    }

    const evUnico = this.calculateEV(gameKey);
    const custoTotal = evUnico.betCost * numGames;
    const evBrutoTotal = evUnico.totalEV * numGames;
    const evLiquidoTotal = evBrutoTotal - custoTotal;
    const retornoPct = (evBrutoTotal / custoTotal) * 100;

    // Probabilidade de ganhar pelo menos um prêmio em qualquer faixa
    // P(pelo menos 1 prêmio) = 1 - P(nenhum prêmio)^numGames
    const probAlgumPremioUnico = evUnico.breakdown.reduce(
      (soma, f) => soma + f.probEfetiva, 0
    );
    const probNenhumPremio = Math.pow(1 - probAlgumPremioUnico, numGames);
    const probAlgumPremio = 1 - probNenhumPremio;

    // Detalhamento por faixa com múltiplos jogos
    const breakdownMulti = evUnico.breakdown.map(faixa => {
      const probAcertar = 1 - Math.pow(1 - faixa.probEfetiva, numGames);
      return {
        ...faixa,
        probMultiJogos: probAcertar,
        probMultiTexto: (probAcertar * 100).toFixed(6) + '%',
        evMulti: faixa.ev * numGames,
        evMultiFormatado: this._formatarMoeda(faixa.ev * numGames)
      };
    });

    return {
      gameKey,
      nome: evUnico.nome,
      numGames,
      custoTotal,
      custoTotalFormatado: this._formatarMoeda(custoTotal),
      evBrutoTotal,
      evBrutoTotalFormatado: this._formatarMoeda(evBrutoTotal),
      evLiquidoTotal,
      evLiquidoTotalFormatado: this._formatarMoeda(evLiquidoTotal),
      retornoPct,
      retornoPctFormatado: retornoPct.toFixed(2) + '%',
      probAlgumPremio,
      probAlgumPremioTexto: (probAlgumPremio * 100).toFixed(4) + '%',
      breakdownMulti
    };
  }

  // ──────────────────────────────────────────────
  //  Utilitários de comparação
  // ──────────────────────────────────────────────

  /**
   * Compara todas as loterias por retorno percentual (EV / custo).
   * @returns {Array} loterias ordenadas do melhor para o pior retorno
   */
  static compararLoterias() {
    const resultados = [];

    for (const gameKey of Object.keys(this.GAMES)) {
      const ev = this.calculateEV(gameKey);
      resultados.push({
        gameKey,
        nome: ev.nome,
        custo: ev.betCost,
        custoFormatado: ev.betCostFormatado,
        totalEV: ev.totalEV,
        totalEVFormatado: ev.totalEVFormatado,
        netEV: ev.netEV,
        netEVFormatado: ev.netEVFormatado,
        returnPct: ev.returnPct,
        returnPctFormatado: ev.returnPctFormatado
      });
    }

    // Ordena do melhor retorno para o pior
    resultados.sort((a, b) => b.returnPct - a.returnPct);
    return resultados;
  }

  /**
   * Retorna tabela comparativa formatada em texto.
   * @returns {string} tabela formatada
   */
  static getComparativoTexto() {
    const dados = this.compararLoterias();
    const linhas = [];

    linhas.push('┌────────────────┬──────────┬──────────────┬──────────────┬──────────┐');
    linhas.push('│    Loteria     │  Custo   │  EV Bruto    │  EV Líquido  │ Retorno  │');
    linhas.push('├────────────────┼──────────┼──────────────┼──────────────┼──────────┤');

    for (const d of dados) {
      const nome = d.nome.padEnd(14);
      const custo = d.custoFormatado.padStart(8);
      const evb = d.totalEVFormatado.padStart(12);
      const evl = d.netEVFormatado.padStart(12);
      const ret = d.returnPctFormatado.padStart(8);
      linhas.push(`│ ${nome} │ ${custo} │ ${evb} │ ${evl} │ ${ret} │`);
    }

    linhas.push('└────────────────┴──────────┴──────────────┴──────────────┴──────────┘');
    return linhas.join('\n');
  }

  // ──────────────────────────────────────────────
  //  Métodos auxiliares privados
  // ──────────────────────────────────────────────

  /**
   * Formata valor em Reais (R$).
   * @param {number} valor
   * @returns {string} ex: "R$ 1.234,56"
   */
  static _formatarMoeda(valor) {
    const abs = Math.abs(valor);
    const sinal = valor < 0 ? '-' : '';

    if (abs >= 1_000_000) {
      return sinal + 'R$ ' + (abs / 1_000_000).toFixed(2).replace('.', ',') + 'M';
    }

    return sinal + 'R$ ' + abs.toLocaleString('pt-BR', {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    });
  }

  /**
   * Formata valor em Reais de forma curta para tabelas.
   * @param {number} valor
   * @returns {string} ex: "50M", "40K", "800"
   */
  static _formatarMoedaCurta(valor) {
    if (valor >= 1_000_000) {
      return 'R$' + (valor / 1_000_000).toFixed(0) + 'M';
    }
    if (valor >= 1_000) {
      return 'R$' + (valor / 1_000).toFixed(0) + 'K';
    }
    return 'R$' + valor.toFixed(0);
  }

  /**
   * Retorna lista de chaves de jogos disponíveis.
   * @returns {string[]}
   */
  static getJogosDisponiveis() {
    return Object.keys(this.GAMES);
  }

  /**
   * Retorna informações básicas de um jogo.
   * @param {string} gameKey
   * @returns {Object|null}
   */
  static getInfoJogo(gameKey) {
    const jogo = this.GAMES[gameKey];
    if (!jogo) return null;

    return {
      gameKey,
      nome: jogo.nome,
      descricao: jogo.descricao,
      universo: jogo.N,
      sorteados: jogo.K,
      apostados: jogo.n,
      custo: jogo.custo,
      custoFormatado: this._formatarMoeda(jogo.custo),
      faixas: Object.keys(jogo.premios).map(Number).sort((a, b) => b - a),
      multiplicador: jogo.multiplicador
    };
  }
}

// Expõe globalmente para uso no browser
window.EVCalculator = EVCalculator;
