/**
 * ============================================================
 *  StrategyValidator — Validação de Estratégias de Jogos
 * ============================================================
 *  Valida estratégias de geração de jogos e bloqueia
 *  configurações com retorno negativo extremo.
 *  Sem dependências externas — funciona direto no browser.
 * ============================================================
 */

class StrategyValidator {

  // ── Regras por loteria ───────────────────────────────────
  static RULES = {
    megasena: {
      allowManual:   false,
      allowSniper:   false,
      minPool:       6,
      recPool:       10,
      maxGames:      500000,
      label:         'Mega-Sena',
      numbersPerGame: 6,
      totalNumbers:  60
    },
    lotofacil: {
      allowManual:   true,
      allowSniper:   false,
      minPool:       15,
      recPool:       18,
      maxGames:      500000,
      label:         'Lotofácil',
      numbersPerGame: 15,
      totalNumbers:  25
    },
    quina: {
      allowManual:   false,
      allowSniper:   false,
      minPool:       5,
      recPool:       8,
      maxGames:      500000,
      label:         'Quina',
      numbersPerGame: 5,
      totalNumbers:  80
    },
    duplasena: {
      allowManual:   false,
      allowSniper:   false,
      minPool:       6,
      recPool:       8,
      maxGames:      500000,
      label:         'Dupla Sena',
      numbersPerGame: 6,
      totalNumbers:  50
    },
    lotomania: {
      allowManual:   false,
      allowSniper:   false,
      minPool:       50,
      recPool:       50,
      maxGames:      500000,
      label:         'Lotomania',
      numbersPerGame: 50,
      totalNumbers:  100
    },
    timemania: {
      allowManual:   true,
      allowSniper:   true,
      minPool:       10,
      recPool:       12,
      maxGames:      500000,
      sniperMinPool: 12,
      label:         'Timemania',
      numbersPerGame: 10,
      totalNumbers:  80
    },
    diadesorte: {
      allowManual:   true,
      allowSniper:   false,
      minPool:       7,
      recPool:       10,
      maxGames:      500000,
      label:         'Dia de Sorte',
      numbersPerGame: 7,
      totalNumbers:  31
    }
  };

  // ── Estratégias conhecidas ───────────────────────────────
  static STRATEGIES = ['frequencia', 'equilibrado', 'aleatorio', 'manual', 'sniper'];

  // ─────────────────────────────────────────────────────────
  //  validate — Validação completa de uma configuração
  // ─────────────────────────────────────────────────────────
  /**
   * Valida uma configuração de geração de jogos.
   *
   * @param {string}  gameKey   — Chave da loteria (ex.: 'megasena')
   * @param {number}  poolSize  — Quantidade de números no pool selecionado
   * @param {string}  strategy  — Estratégia escolhida
   * @param {number}  gameCount — Quantidade de jogos a gerar
   * @returns {{ valid: boolean, errors: string[], warnings: string[], useBatch: boolean }}
   */
  static validate(gameKey, poolSize, strategy, gameCount) {
    const resultado = {
      valid:    true,
      errors:   [],
      warnings: [],
      useBatch: false
    };

    // ── Loteria existe? ──
    const regra = StrategyValidator.RULES[gameKey];
    if (!regra) {
      resultado.valid = false;
      resultado.errors.push(`Loteria "${gameKey}" não reconhecida.`);
      return resultado;
    }

    // ── Estratégia válida? ──
    const strategyNorm = (strategy || '').toLowerCase().trim();
    if (!StrategyValidator.STRATEGIES.includes(strategyNorm)) {
      resultado.valid = false;
      resultado.errors.push(
        `Estratégia "${strategy}" inválida. Use: ${StrategyValidator.STRATEGIES.join(', ')}.`
      );
    }

    // ── Estratégia manual permitida? ──
    if (strategyNorm === 'manual' && !regra.allowManual) {
      resultado.valid = false;
      resultado.errors.push(
        `A estratégia manual não é permitida para ${regra.label}.`
      );
    }

    // ── Estratégia sniper permitida? ──
    if (strategyNorm === 'sniper') {
      if (!regra.allowSniper) {
        resultado.valid = false;
        resultado.errors.push(
          `A estratégia sniper não é permitida para ${regra.label}.`
        );
      } else if (regra.sniperMinPool && poolSize < regra.sniperMinPool) {
        resultado.valid = false;
        resultado.errors.push(
          `Para usar sniper na ${regra.label}, o pool mínimo é ${regra.sniperMinPool} números. Você selecionou ${poolSize}.`
        );
      }
    }

    // ── Pool de números válido? ──
    const poolNum = Number(poolSize);
    if (!Number.isFinite(poolNum) || poolNum < 1) {
      resultado.valid = false;
      resultado.errors.push('O tamanho do pool deve ser um número positivo.');
    } else {
      if (poolNum < regra.minPool) {
        resultado.valid = false;
        resultado.errors.push(
          `O pool mínimo para ${regra.label} é ${regra.minPool} números. Você selecionou ${poolNum}.`
        );
      }
      if (regra.totalNumbers && poolNum > regra.totalNumbers) {
        resultado.valid = false;
        resultado.errors.push(
          `O pool máximo para ${regra.label} é ${regra.totalNumbers} números. Você selecionou ${poolNum}.`
        );
      }
      if (poolNum < regra.recPool) {
        resultado.warnings.push(
          `Recomenda-se usar pelo menos ${regra.recPool} números no pool para ${regra.label}. Você selecionou ${poolNum}.`
        );
      }
    }

    // ── Quantidade de jogos válida? ──
    const countNum = Number(gameCount);
    if (!Number.isFinite(countNum) || countNum < 1) {
      resultado.valid = false;
      resultado.errors.push('A quantidade de jogos deve ser um número positivo.');
    } else {
      if (countNum > regra.maxGames) {
        resultado.valid = false;
        resultado.errors.push(
          `O máximo de jogos para ${regra.label} é ${regra.maxGames.toLocaleString('pt-BR')}. Você solicitou ${countNum.toLocaleString('pt-BR')}.`
        );
      }

      // ── Retorno negativo extremo ──
      // Se o custo estimado ultrapassar R$ 500.000, avisa; > R$ 5.000.000 bloqueia
      const custoPorJogo = StrategyValidator._estimarCusto(gameKey);
      const custoTotal   = custoPorJogo * countNum;

      if (custoTotal > 5000000) {
        resultado.valid = false;
        resultado.errors.push(
          `Custo estimado de R$ ${custoTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })} ` +
          `excede o limite seguro de R$ 5.000,000,00. Reduza a quantidade de jogos.`
        );
      } else if (custoTotal > 500000) {
        resultado.warnings.push(
          `Custo estimado de R$ ${custoTotal.toLocaleString('pt-BR', { minimumFractionDigits: 2 })}. ` +
          `Verifique se essa quantidade de jogos é realmente desejada.`
        );
      }
    }

    // ── Verificação de combinações possíveis ──
    if (Number.isFinite(poolNum) && poolNum >= regra.minPool) {
      const combPossiveis = StrategyValidator._combinacoes(poolNum, regra.numbersPerGame);
      if (Number.isFinite(countNum) && countNum > combPossiveis) {
        resultado.valid = false;
        resultado.errors.push(
          `Com um pool de ${poolNum} números, existem apenas ${combPossiveis.toLocaleString('pt-BR')} ` +
          `combinações possíveis para ${regra.label}. Você solicitou ${countNum.toLocaleString('pt-BR')} jogos.`
        );
      }
    }

    // ── Definir se deve usar processamento em lote ──
    if (Number.isFinite(countNum) && countNum > 200) {
      resultado.useBatch = true;
      resultado.warnings.push(
        `Serão gerados ${countNum.toLocaleString('pt-BR')} jogos — processamento em lote será ativado para melhor desempenho.`
      );
    }

    return resultado;
  }

  // ─────────────────────────────────────────────────────────
  //  isManualAllowed — Verifica se a estratégia manual é permitida
  // ─────────────────────────────────────────────────────────
  /**
   * @param {string} gameKey — Chave da loteria
   * @returns {boolean}
   */
  static isManualAllowed(gameKey) {
    const regra = StrategyValidator.RULES[gameKey];
    return regra ? regra.allowManual === true : false;
  }

  // ─────────────────────────────────────────────────────────
  //  isSniperAllowed — Verifica se a estratégia sniper é permitida
  // ─────────────────────────────────────────────────────────
  /**
   * @param {string} gameKey  — Chave da loteria
   * @param {number} poolSize — Tamanho do pool selecionado
   * @returns {boolean}
   */
  static isSniperAllowed(gameKey, poolSize) {
    const regra = StrategyValidator.RULES[gameKey];
    if (!regra || !regra.allowSniper) return false;
    if (regra.sniperMinPool && poolSize < regra.sniperMinPool) return false;
    return true;
  }

  // ─────────────────────────────────────────────────────────
  //  getMaxGames — Retorna o máximo de jogos permitidos
  // ─────────────────────────────────────────────────────────
  /**
   * @param {string} gameKey — Chave da loteria
   * @returns {number}
   */
  static getMaxGames(gameKey) {
    const regra = StrategyValidator.RULES[gameKey];
    return regra ? regra.maxGames : 0;
  }

  // ─────────────────────────────────────────────────────────
  //  getRecommendation — Recomendação textual em português
  // ─────────────────────────────────────────────────────────
  /**
   * Retorna uma recomendação em português sobre a melhor
   * estratégia para a loteria informada.
   *
   * @param {string} gameKey — Chave da loteria
   * @returns {string}
   */
  static getRecommendation(gameKey) {
    const regra = StrategyValidator.RULES[gameKey];
    if (!regra) return `Loteria "${gameKey}" não reconhecida.`;

    const partes = [];

    partes.push(`📊 Recomendação para ${regra.label}:`);
    partes.push('');

    // Pool recomendado
    partes.push(
      `• Use um pool de pelo menos ${regra.recPool} números para equilibrar custo e cobertura.`
    );

    // Estratégia sugerida
    if (regra.allowSniper) {
      partes.push(
        `• A estratégia "sniper" é indicada — foca nos números com maior frequência recente` +
        (regra.sniperMinPool ? ` (pool mínimo: ${regra.sniperMinPool} números).` : '.')
      );
    } else if (regra.allowManual) {
      partes.push(
        `• A estratégia "manual" está disponível — permite escolher seus números da sorte.`
      );
    }

    partes.push(
      `• A estratégia "equilibrado" é recomendada para a maioria dos jogadores — combina números quentes e frios.`
    );

    // Quantidade de jogos
    const jogosIdeal = StrategyValidator._jogosRecomendados(gameKey);
    partes.push(
      `• Quantidade sugerida: entre ${jogosIdeal.min} e ${jogosIdeal.max} jogos ` +
      `(máximo permitido: ${regra.maxGames.toLocaleString('pt-BR')}).`
    );

    // Custo estimado
    const custo = StrategyValidator._estimarCusto(gameKey);
    if (custo > 0) {
      partes.push(
        `• Custo por jogo: R$ ${custo.toFixed(2).replace('.', ',')} ` +
        `(${jogosIdeal.min} jogos ≈ R$ ${(custo * jogosIdeal.min).toFixed(2).replace('.', ',')}).`
      );
    }

    partes.push('');
    partes.push('💡 Dica: analise os números mais e menos frequentes dos últimos sorteios antes de gerar seus jogos.');

    return partes.join('\n');
  }

  // ─────────────────────────────────────────────────────────
  //  getRules — Retorna as regras de uma loteria específica
  // ─────────────────────────────────────────────────────────
  /**
   * @param {string} gameKey — Chave da loteria
   * @returns {object|null}
   */
  static getRules(gameKey) {
    return StrategyValidator.RULES[gameKey] || null;
  }

  // ─────────────────────────────────────────────────────────
  //  getAllGameKeys — Retorna todas as chaves de loterias
  // ─────────────────────────────────────────────────────────
  /**
   * @returns {string[]}
   */
  static getAllGameKeys() {
    return Object.keys(StrategyValidator.RULES);
  }

  // ─────────────────────────────────────────────────────────
  //  getSummary — Resumo rápido das regras de uma loteria
  // ─────────────────────────────────────────────────────────
  /**
   * @param {string} gameKey — Chave da loteria
   * @returns {string}
   */
  static getSummary(gameKey) {
    const regra = StrategyValidator.RULES[gameKey];
    if (!regra) return `Loteria "${gameKey}" não encontrada.`;

    const estrategias = ['frequencia', 'equilibrado', 'aleatorio'];
    if (regra.allowManual)  estrategias.push('manual');
    if (regra.allowSniper)  estrategias.push('sniper');

    return (
      `${regra.label}: ${regra.numbersPerGame} de ${regra.totalNumbers} | ` +
      `Pool mín: ${regra.minPool}, rec: ${regra.recPool} | ` +
      `Máx jogos: ${regra.maxGames.toLocaleString('pt-BR')} | ` +
      `Estratégias: ${estrategias.join(', ')}`
    );
  }

  // ═════════════════════════════════════════════════════════
  //  Métodos privados auxiliares
  // ═════════════════════════════════════════════════════════

  /**
   * Calcula o número de combinações C(n, k).
   * @private
   */
  static _combinacoes(n, k) {
    if (k > n) return 0;
    if (k === 0 || k === n) return 1;
    if (k > n - k) k = n - k;

    let resultado = 1;
    for (let i = 0; i < k; i++) {
      resultado = resultado * (n - i) / (i + 1);
    }
    return Math.round(resultado);
  }

  /**
   * Estima o custo unitário de uma aposta simples (em R$).
   * Valores baseados nas tabelas oficiais da Caixa (2024/2025).
   * @private
   */
  static _estimarCusto(gameKey) {
    const custos = {
      megasena:    6.00,
      lotofacil:   3.50,
      quina:       2.50,
      duplasena:   2.50,
      lotomania:   3.00,
      timemania:   3.50,
      diadesorte:  2.50
    };
    return custos[gameKey] || 0;
  }

  /**
   * Retorna faixa de jogos recomendados para cada loteria.
   * @private
   */
  static _jogosRecomendados(gameKey) {
    const faixas = {
      megasena:    { min: 6,  max: 50  },
      lotofacil:   { min: 3,  max: 20  },
      quina:       { min: 5,  max: 40  },
      duplasena:   { min: 6,  max: 50  },
      lotomania:   { min: 3,  max: 20  },
      timemania:   { min: 5,  max: 30  },
      diadesorte:  { min: 5,  max: 40  }
    };
    return faixas[gameKey] || { min: 1, max: 10 };
  }
}

// ── Exportação global ──────────────────────────────────────
window.StrategyValidator = StrategyValidator;
