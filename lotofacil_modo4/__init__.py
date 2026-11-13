# -*- coding: utf-8 -*-
"""
Pacote LOTOFACIL MODO 4
=======================
Arquitetura modular auditavel para formalizacao matematica, estatistica,
otimizacao combinatoria, simulacao e homologacao criptografica da Lotofacil.
"""

from .etapa1_regras_oficiais import (
    CLAUSULA_MATEMATICA_OBRIGATORIA,
    ESCALA_APOSTAS_OFICIAIS,
    ESPACO_AMOSTRAL_SIMPLES,
    FAIXAS_PREMIADAS,
    MAX_DEZENAS_APOSTA,
    MIN_DEZENAS_APOSTA,
    PERCENTUAL_PREMIO_BRUTO,
    PRECO_APOSTA_SIMPLES,
    PREMIOS_FIXOS,
    REGRAS_OFICIAIS_LOTOFACIL,
    TAMANHO_SORTEIO,
    UNIVERSO_TOTAL,
    ErroValidacaoLotofacilError,
    combinacao_exata,
    custo_aposta_oficial,
    definicao_formal_conceitos_secao3,
    distribuicao_hipergeometrica_aposta,
    gerar_resumo_formal_etapa1,
    matriz_5x5_coordenadas,
    multiplicidade_premios_aposta,
    probabilidade_hipergeometrica_exata,
    probabilidade_pelo_menos_k_exata,
    probabilidade_split_bivariada_exata,
    validar_aposta_lotofacil,
    validar_inteiro_estrito,
)

__all__ = [
    "CLAUSULA_MATEMATICA_OBRIGATORIA",
    "ESCALA_APOSTAS_OFICIAIS",
    "ESPACO_AMOSTRAL_SIMPLES",
    "FAIXAS_PREMIADAS",
    "MAX_DEZENAS_APOSTA",
    "MIN_DEZENAS_APOSTA",
    "PERCENTUAL_PREMIO_BRUTO",
    "PRECO_APOSTA_SIMPLES",
    "PREMIOS_FIXOS",
    "REGRAS_OFICIAIS_LOTOFACIL",
    "TAMANHO_SORTEIO",
    "UNIVERSO_TOTAL",
    "ErroValidacaoLotofacilError",
    "combinacao_exata",
    "custo_aposta_oficial",
    "definicao_formal_conceitos_secao3",
    "distribuicao_hipergeometrica_aposta",
    "gerar_resumo_formal_etapa1",
    "matriz_5x5_coordenadas",
    "multiplicidade_premios_aposta",
    "probabilidade_hipergeometrica_exata",
    "probabilidade_pelo_menos_k_exata",
    "probabilidade_split_bivariada_exata",
    "validar_aposta_lotofacil",
    "validar_inteiro_estrito",
]
