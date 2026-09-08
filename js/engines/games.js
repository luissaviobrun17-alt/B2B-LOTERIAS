
// js/engines/games.js
// Premiações baseadas nas faixas oficiais da Caixa Econômica Federal
// ⚠️  ATENÇÃO HONESTA:
//    'prize' = valor ESTIMADO/REFERÊNCIA. A maioria das faixas funciona por RATIÃO.
//    A Caixa divide o arrecadado entre os ganhadores de cada faixa.
//    O valor real pago pode ser MUITO diferente da estimativa.
//    Somente faixas marcadas com prizeType:'fixo' têm valor garantido.
// ═══ ATUALIZADO V11: Valores corrigidos + tipo de prêmio + notas de transparência ═══

const GAMES = {
    megasena: {
        name: "Mega Sena",
        range: [1, 60],
        draw: 6,
        color: "#209A3C",
        colorGrad: "#0d6b28",
        cols: 10,
        price: 5.00,
        // Faixas oficiais Mega Sena (aposta simples R$ 5,00): Sena (6), Quina (5), Quadra (4)
        // TODAS por ratião. A Sena acumula se não houver ganhador.
        strategies: [
            { id: "sena",   label: "Sena (6 acertos)",   match: 6, prize: 50000000, prizeType: "acumulado",  note: "Rateio — acumula se vazio. Média histórica: R$ 40-80 milhões",  paid: true  },
            { id: "quina",  label: "Quina (5 acertos)",  match: 5, prize: 58000,    prizeType: "rateio",     note: "Rateio — ~22% da arrecadação. Média: R$ 40k-80k por vencedor",   paid: true  },
            { id: "quadra", label: "Quadra (4 acertos)", match: 4, prize: 1200,     prizeType: "rateio",     note: "Rateio — ~19% da arrecadação. Média: R$ 800-1.500 por vencedor", paid: true  }
        ],
        closingLevels: [
            { id: "close6", label: "Fechamento Sena (6)",   guarantee: 6, icon: "🎯" },
            { id: "close5", label: "Fechamento Quina (5)",  guarantee: 5, icon: "⭐" },
            { id: "close4", label: "Fechamento Quadra (4)", guarantee: 4, icon: "🔥" }
        ],
        minBet: 6,
        maxBet: 60,
        statsCount: 20
    },
    lotofacil: {
        name: "Lotofácil",
        range: [1, 25],
        draw: 15,
        color: "#930089",
        colorGrad: "#5e0058",
        cols: 5,
        price: 3.00,
        // Faixas oficiais: 15, 14, 13 por rateio (aposta simples R$ 3,00) | 12, 11 FIXO
        strategies: [
            { id: "15pts", label: "15 Pontos",  match: 15, prize: 2000000, prizeType: "acumulado", note: "Rateio — acumula se vazio. Média: R$ 1,5-4 milhões",         paid: true  },
            { id: "14pts", label: "14 Pontos",  match: 14, prize: 2000,    prizeType: "rateio",    note: "Rateio — ~20% do prêmio total. Média: R$ 1.500-3.000",       paid: true  },
            { id: "13pts", label: "13 Pontos",  match: 13, prize: 25,      prizeType: "rateio",    note: "Rateio — média histórica R$ 20-35 por vencedor",            paid: true  },
            { id: "12pts", label: "12 Pontos",  match: 12, prize: 12,      prizeType: "fixo",      note: "FIXO: R$ 12,00 garantido por aposta ganhadora",            paid: true  },
            { id: "11pts", label: "11 Pontos",  match: 11, prize: 6,       prizeType: "fixo",      note: "FIXO: R$ 6,00 garantido por aposta ganhadora",             paid: true  }
        ],
        closingLevels: [
            { id: "close15", label: "Fechamento 15 Pontos",  guarantee: 15, icon: "🎯" },
            { id: "close14", label: "Fechamento 14 Pontos",  guarantee: 14, icon: "⭐" },
            { id: "close13", label: "Fechamento 13 Pontos",  guarantee: 13, icon: "🔥" },
            { id: "close12", label: "Fechamento 12 Pontos",  guarantee: 12, icon: "💎" },
            { id: "close11", label: "Fechamento 11 Pontos",  guarantee: 11, icon: "👑" }
        ],
        minBet: 15,
        maxBet: 25,
        maxFixed: 10,
        statsCount: 15
    },
    quina: {
        name: "Quina",
        range: [1, 80],
        draw: 5,
        color: "#3062a8",
        colorGrad: "#1a3d6b",
        cols: 10,
        price: 2.50,
        // Faixas oficiais: Quina (5), Quadra (4) (aposta simples R$ 2,50), Terno (3) por ratião | Duque (2) FIXO R$ 2
        strategies: [
            { id: "quina",  label: "Quina (5 acertos)",  match: 5, prize: 6000000, prizeType: "acumulado", note: "Rateio — acumula se vazio. Média: R$ 3-10 milhões",          paid: true  },
            { id: "quadra", label: "Quadra (4 acertos)", match: 4, prize: 7500,    prizeType: "rateio",    note: "Rateio — ~19% da arrecadação. Média: R$ 5k-10k por vencedor", paid: true  },
            { id: "terno",  label: "Terno (3 acertos)",  match: 3, prize: 4,       prizeType: "fixo",      note: "FIXO: R$ 4,00 garantido por aposta ganhadora",             paid: true  },
            { id: "duque",  label: "Duque (2 acertos)",  match: 2, prize: 2,       prizeType: "fixo",      note: "FIXO: R$ 2,00 garantido (devolve parte da aposta)",       paid: true  }
        ],
        closingLevels: [
            { id: "close5", label: "Fechamento Quina (5)",  guarantee: 5, icon: "🎯" },
            { id: "close4", label: "Fechamento Quadra (4)", guarantee: 4, icon: "⭐" },
            { id: "close3", label: "Fechamento Terno (3)",  guarantee: 3, icon: "🔥" }
        ],
        minBet: 5,
        maxBet: 80,
        statsCount: 30
    },
    duplasena: {
        name: "Dupla Sena",
        range: [1, 50],
        draw: 6,
        color: "#e8000f",
        colorGrad: "#8f0009",
        cols: 10,
        price: 2.50,
        // Faixas oficiais (aposta simples R$ 2,50) — todos por ratião
        // 2 sorteios por concurso — você concorre aos dois simultaneamente
        strategies: [
            { id: "sena",   label: "Sena (6 acertos)",   match: 6, prize: 2500000, prizeType: "acumulado", note: "Rateio em cada sorteio. Média: R$ 1-5 milhões",         paid: true  },
            { id: "quina",  label: "Quina (5 acertos)",  match: 5, prize: 6000,    prizeType: "rateio",    note: "Rateio — média R$ 4k-10k por vencedor por sorteio",    paid: true  },
            { id: "quadra", label: "Quadra (4 acertos)", match: 4, prize: 150,     prizeType: "rateio",    note: "Rateio — média R$ 80-250 por vencedor por sorteio",   paid: true  },
            { id: "terno",  label: "Terno (3 acertos)",  match: 3, prize: 3,       prizeType: "fixo",      note: "FIXO: R$ 3,00 por sorteio (se ganhar nos 2 = R$ 6)", paid: true  }
        ],
        closingLevels: [
            { id: "close6", label: "Fechamento Sena (6)",   guarantee: 6, icon: "🎯" },
            { id: "close5", label: "Fechamento Quina (5)",  guarantee: 5, icon: "⭐" },
            { id: "close4", label: "Fechamento Quadra (4)", guarantee: 4, icon: "🔥" },
            { id: "close3", label: "Fechamento Terno (3)",  guarantee: 3, icon: "✅" }
        ],
        minBet: 6,
        maxBet: 50,
        statsCount: 15
    },
    lotomania: {
        name: "Lotomania",
        range: [0, 99],
        draw: 20,
        color: "#f07d00",
        colorGrad: "#9b5000",
        cols: 10,
        price: 3.00,
        // Jogador marca 50 números de 0-99. Caixa sorteia 20.
        // Faixas: 20, 19, 18, 17, 16, 15 acertos + 0 acertos (Mania de Milionário)
        strategies: [
            { id: "20pts",  label: "20 Pontos (Lotomania)",         match: 20, prize: 5000000, prizeType: "acumulado", note: "Rateio — acumula se vazio. Média: R$ 3-8 milhões",    paid: true  },
            { id: "19pts",  label: "19 Pontos",                      match: 19, prize: 90000,   prizeType: "rateio",    note: "Rateio — média R$ 60k-120k por vencedor",           paid: true  },
            { id: "18pts",  label: "18 Pontos",                      match: 18, prize: 3500,    prizeType: "rateio",    note: "Rateio — média R$ 2k-5k por vencedor",             paid: true  },
            { id: "17pts",  label: "17 Pontos",                      match: 17, prize: 280,     prizeType: "rateio",    note: "Rateio — média R$ 200-400 por vencedor",           paid: true  },
            { id: "16pts",  label: "16 Pontos",                      match: 16, prize: 35,      prizeType: "rateio",    note: "Rateio — média R$ 25-50 por vencedor",             paid: true  },
            { id: "15pts",  label: "15 Pontos",                      match: 15, prize: 6,       prizeType: "fixo",      note: "FIXO: R$ 6,00 garantido",                          paid: true  },
            { id: "0pts",   label: "0 Pontos (Mania de Milionário)", match: 0,  prize: 250,     prizeType: "rateio",    note: "Rateio — zerar os 20 acertos. Média: R$ 100-400",  paid: true  }
        ],
        closingLevels: [
            { id: "close20", label: "Fechamento 20 Pontos",  guarantee: 20, icon: "🎯" },
            { id: "close19", label: "Fechamento 19 Pontos",  guarantee: 19, icon: "⭐" },
            { id: "close18", label: "Fechamento 18 Pontos",  guarantee: 18, icon: "🔥" },
            { id: "close17", label: "Fechamento 17 Pontos",  guarantee: 17, icon: "✅" }
        ],
        minBet: 50,
        maxBet: 100,
        maxFixed: 30,
        statsCount: 30,
        statsSortNumeric: true
    },
    timemania: {
        name: "Timemania",
        range: [1, 80],
        draw: 7,
        color: "#00a859",
        colorGrad: "#006638",
        cols: 10,
        price: 3.50,
        // Jogador escolhe 10 números + 1 Time do Coração. Sorteados: 7 + 1 time.
        // Faixas: 7, 6, 5 por ratião | 4, 3 FIXO | Time do Coração FIXO
        strategies: [
            { id: "7pts",  label: "7 Pontos (Timemania)",  match: 7, prize: 4000000, prizeType: "acumulado", note: "Rateio — acumula se vazio. Média: R$ 2-8 milhões",          paid: true  },
            { id: "6pts",  label: "6 Pontos",               match: 6, prize: 35000,   prizeType: "rateio",    note: "Rateio — média R$ 20k-60k por vencedor",                   paid: true  },
            { id: "5pts",  label: "5 Pontos",               match: 5, prize: 900,     prizeType: "rateio",    note: "Rateio — média R$ 600-1.400 por vencedor",                paid: true  },
            { id: "4pts",  label: "4 Pontos",               match: 4, prize: 7,       prizeType: "fixo",      note: "FIXO: R$ 7,00 garantido por aposta",                       paid: true  },
            { id: "3pts",  label: "3 Pontos",               match: 3, prize: 3,       prizeType: "fixo",      note: "FIXO: R$ 3,00 garantido por aposta",                       paid: true  }
        ],
        closingLevels: [
            { id: "close7", label: "Fechamento 7 Pontos",  guarantee: 7, icon: "🎯" },
            { id: "close6", label: "Fechamento 6 Pontos",  guarantee: 6, icon: "⭐" },
            { id: "close5", label: "Fechamento 5 Pontos",  guarantee: 5, icon: "🔥" }
        ],
        // Bônus do Time do Coração: R$ 7,50 fixo se o time sorteado for igual ao escolhido
        extraPrize: { label: "Time do Coração", prize: 7.50, prizeType: "fixo", note: "FIXO: R$ 7,50 se o time sorteado for o mesmo que o escolhido" },
        minBet: 10,
        maxBet: 80,
        statsCount: 20
    },
        milionaria: {
        name: "+Milionária",
        range: [1, 50],
        draw: 6,
        color: "#059669",
        colorGrad: "#047857",
        cols: 10,
        price: 6.00,
        trevos: [1, 6],
        qtdTrevos: 2,
        strategies: [
            { id: "faixa1",  label: "Faixa 1 (6 acertos + 2 trevos)", match: 6, prize: 10000000, prizeType: "acumulado", note: "Prêmio Principal — Mínimo R$ 10 milhões", paid: true },
            { id: "faixa2",  label: "Faixa 2 (6 acertos + 1/0 trevo)", match: 6, prize: 250000,   prizeType: "rateio",    note: "Rateio oficial Caixa", paid: true },
            { id: "faixa3",  label: "Faixa 3 (5 acertos + 2 trevos)", match: 5, prize: 50000,    prizeType: "rateio",    note: "Rateio oficial Caixa", paid: true },
            { id: "faixa4",  label: "Faixa 4 (5 acertos + 1/0 trevo)", match: 5, prize: 12000,    prizeType: "rateio",    note: "Rateio oficial Caixa", paid: true },
            { id: "faixa5",  label: "Faixa 5 (4 acertos + 2 trevos)", match: 4, prize: 1500,     prizeType: "rateio",    note: "Rateio oficial Caixa", paid: true },
            { id: "faixa6",  label: "Faixa 6 (4 acertos + 1/0 trevo)", match: 4, prize: 250,      prizeType: "rateio",    note: "Rateio oficial Caixa", paid: true },
            { id: "faixa7",  label: "Faixa 7 (3 acertos + 2 trevos)", match: 3, prize: 50,       prizeType: "rateio",    note: "Rateio oficial Caixa", paid: true },
            { id: "faixa8",  label: "Faixa 8 (3 acertos + 1 trevo)",  match: 3, prize: 24,       prizeType: "fixo",      note: "FIXO: R$ 24,00 garantido", paid: true },
            { id: "faixa9",  label: "Faixa 9 (2 acertos + 2 trevos)", match: 2, prize: 12,       prizeType: "fixo",      note: "FIXO: R$ 12,00 garantido", paid: true },
            { id: "faixa10", label: "Faixa 10 (2 acertos + 1 trevo)", match: 2, prize: 6,        prizeType: "fixo",      note: "FIXO: R$ 6,00 garantido", paid: true }
        ],
        closingLevels: [
            { id: "close6", label: "Fechamento 6 Números", guarantee: 6, icon: "🎯" },
            { id: "close5", label: "Fechamento 5 Números", guarantee: 5, icon: "⭐" },
            { id: "close4", label: "Fechamento 4 Números", guarantee: 4, icon: "🔥" }
        ],
        minBet: 6,
        maxBet: 50,
        statsCount: 20,
        drawDays: [3, 6],
        drawTime: "20:00",
        estimatedPrizeFallback: 10000000
    },
    diadesorte: {
        name: "Dia de Sorte",
        range: [1, 31],
        draw: 7,
        color: "#e27820",
        colorGrad: "#8f4c0f",
        cols: 7,
        price: 2.50,
        // Aposta simples R$ 2,50. Sorteados: 7 + 1 mês.
        // Faixas: 7, 6 por ratião | 5, 4 FIXO | Mês da Sorte FIXO R$ 2,50
        strategies: [
            { id: "7pts",  label: "7 Pontos (Dia de Sorte)",  match: 7, prize: 1000000, prizeType: "acumulado", note: "Rateio — acumula se vazio. Média: R$ 500k-2 milhões",   paid: true  },
            { id: "6pts",  label: "6 Pontos",                  match: 6, prize: 3000,    prizeType: "rateio",    note: "Rateio — média R$ 2k-5k por vencedor",                paid: true  },
            { id: "5pts",  label: "5 Pontos",                  match: 5, prize: 25,      prizeType: "fixo",      note: "FIXO: R$ 25,00 garantido por aposta ganhadora",       paid: true  },
            { id: "4pts",  label: "4 Pontos",                  match: 4, prize: 5,       prizeType: "fixo",      note: "FIXO: R$ 5,00 garantido por aposta ganhadora",        paid: true  }
        ],
        closingLevels: [
            { id: "close7", label: "Fechamento 7 Pontos",  guarantee: 7, icon: "🎯" },
            { id: "close6", label: "Fechamento 6 Pontos",  guarantee: 6, icon: "⭐" },
            { id: "close5", label: "Fechamento 5 Pontos",  guarantee: 5, icon: "🔥" }
        ],
        // Bônus do Mês da Sorte: R$ 2,50 fixo se o mês sorteado for igual ao escolhido
        extraPrize: { label: "Mês da Sorte", prize: 2.50, prizeType: "fixo", note: "FIXO: R$ 2,50 se o mês sorteado for o mesmo que o escolhido" },
        minBet: 7,
        maxBet: 31,
        statsCount: 15,
        drawDays: [2, 4, 6],
        drawTime: "20:00"
    },
        supersete: {
        name: "Super Sete",
        range: [0, 9],
        draw: 7,
        color: "#0284c7",
        colorGrad: "#0369a1",
        cols: 7,
        price: 2.50,
        isColumnGame: true,
        // Faixas oficiais Caixa Econômica Federal:
        strategies: [
            { id: "7pts", label: "7 Colunas (Faixa 1 — Rateio)", match: 7, prize: 2000000, prizeType: "acumulado", note: "Rateio — acumula se vazio. Média: R$ 1-5 milhões", paid: true },
            { id: "6pts", label: "6 Colunas (Faixa 2)", match: 6, prize: 15000, prizeType: "rateio", note: "Rateio — média R$ 10k-30k por vencedor", paid: true },
            { id: "5pts", label: "5 Colunas (Faixa 3)", match: 5, prize: 800, prizeType: "rateio", note: "Rateio — média R$ 500-1.200 por vencedor", paid: true },
            { id: "4pts", label: "4 Colunas (Faixa 4)", match: 4, prize: 50, prizeType: "rateio", note: "Rateio — média R$ 35-70 por vencedor", paid: true },
            { id: "3pts", label: "3 Colunas (Faixa 5 — FIXO)", match: 3, prize: 5.00, prizeType: "fixo", note: "FIXO: R$ 5,00 garantido por aposta ganhadora", paid: true }
        ],
        closingLevels: [
            { id: "close7", label: "Fechamento 7 Colunas", guarantee: 7, icon: "🎯" },
            { id: "close6", label: "Fechamento 6 Colunas", guarantee: 6, icon: "⭐" },
            { id: "close5", label: "Fechamento 5 Colunas", guarantee: 5, icon: "🔥" }
        ],
        minBet: 7,
        maxBet: 21,
        statsCount: 15,
        drawDays: [1, 3, 5],
        drawTime: "20:00",
        estimatedPrizeFallback: 2000000
    },
    loteca: {
        name: "Loteca",
        range: [1, 14],
        draw: 14,
        color: "#15803d",
        colorGrad: "#166534",
        cols: 14,
        price: 4.00,
        strategies: [
            { id: "14pts", label: "14 Pontos (Faixa Principal)", match: 14, prize: 1500000, prizeType: "acumulado", note: "Rateio — acumula se vazio. Média histórica: R$ 1-3 milhões", paid: true },
            { id: "13pts", label: "13 Pontos", match: 13, prize: 35000, prizeType: "rateio", note: "Rateio — ~15% da arrecadação.", paid: true }
        ],
        closingLevels: [
            { id: "close14", label: "Fechamento 14 Acertos", guarantee: 14, icon: "🎯" },
            { id: "close13", label: "Fechamento 13 Acertos", guarantee: 13, icon: "⭐" }
        ],
        minBet: 14,
        maxBet: 14,
        statsCount: 14,
        drawDays: [1, 2],
        drawTime: "18:00",
        estimatedPrizeFallback: 1500000
    }
};

// Add missing draw days to others
GAMES.megasena.drawDays = [2, 4, 6];
GAMES.megasena.drawTime = "20:00";
GAMES.megasena.estimatedPrizeFallback = 30000000;

GAMES.lotofacil.drawDays = [1, 2, 3, 4, 5, 6];
GAMES.lotofacil.drawTime = "20:00";
GAMES.lotofacil.estimatedPrizeFallback = 1700000;

GAMES.quina.drawDays = [1, 2, 3, 4, 5, 6];
GAMES.quina.drawTime = "20:00";
GAMES.quina.estimatedPrizeFallback = 6000000;

GAMES.duplasena.drawDays = [1, 3, 5];
GAMES.duplasena.drawTime = "20:00";
GAMES.duplasena.estimatedPrizeFallback = 2500000;

GAMES.lotomania.drawDays = [1, 3, 5];
GAMES.lotomania.drawTime = "20:00";
GAMES.lotomania.estimatedPrizeFallback = 4000000;

GAMES.timemania.drawDays = [2, 4, 6];
GAMES.timemania.drawTime = "20:00";
GAMES.timemania.estimatedPrizeFallback = 3500000;

GAMES.diadesorte.estimatedPrizeFallback = 1000000;
GAMES.diadesorte.drawDays = [2, 4, 6];
GAMES.diadesorte.drawTime = "20:00";
GAMES.milionaria.drawDays = [3, 6];
GAMES.milionaria.drawTime = "20:00";
GAMES.milionaria.estimatedPrizeFallback = 90000000; // Acumulado - estimativa 02/09/2026

GAMES.loteca.drawDays = [1, 2];
GAMES.loteca.drawTime = "18:00";
GAMES.loteca.estimatedPrizeFallback = 1500000;
GAMES.supersete.drawDays = [1, 3, 5];
GAMES.supersete.drawTime = "20:00";
GAMES.supersete.estimatedPrizeFallback = 2000000;

// ═══ FIM games.js V11 ═══
