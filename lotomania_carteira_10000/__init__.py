# -*- coding: utf-8 -*-
"""
Modulo isolado de otimizacao combinatoria de carteiras da Lotomania ate 10.000 jogos
(Ordem 5-R3 + S1_atual_top8 + orcamento experimental de 1.080.000 tentativas).

Sem integracao em producao na API ou nos motores existentes nesta etapa.
"""

from lotomania_carteira_10000.auditoria import (
    auditar_carteira_completa,
    calcular_coocorrencia_global_bruta,
    calcular_delta_phi2_exato_candidato,
    calcular_metricas_intersecao_bruta,
    verificar_consistencia_lam_e_presenca,
)
from lotomania_carteira_10000.construtiva import (
    calcular_q_plus,
    inicializar_carteira_fase12,
    somar_comb_vetor,
)
from lotomania_carteira_10000.otimizador_swap import (
    FalhaInjetadaAtomica,
    avaliar_delta_q_dmax_local,
    avaliar_e_aplicar_swap_fase3,
    capturar_snapshot_estado,
    comparar_estado_snapshot,
    gerar_carteira_10000_otimizada,
)
from lotomania_carteira_10000.validacao import (
    BASELINE_ORDEM4_10000_REFERENCIA,
    BLOCOS,
    BLOCK_OF,
    CLAUSULA_OBRIGATORIA,
    ESTRATEGIA_FASE3_PADRAO,
    FAIXAS_PREMIACAO,
    FAIXAS_PREMIACAO_RELATORIO,
    MASK_80,
    PARAMETROS_PADRAO,
    TABELA_COMBINADA,
    TABELA_OVERLAP_BIVARIADA,
    TABELA_OVERLAP_FAIXAS,
    TABELA_OVERLAP_PREMIADOS,
    VERSAO_ALGORITMO,
    calcular_hashes_certificados,
    calcular_n2_celula,
    classificar_homologacao_kmax,
    exigir,
    gerar_tabelas_hipergeometricas,
    sha256_matriz_incidencia_canonica,
    validar_bilhete_individual,
    validar_entrada_carteira,
    validar_r1_r9_rapido,
    validar_trilha_jsonl_em_disco,
)

__all__ = [
    "BASELINE_ORDEM4_10000_REFERENCIA",
    "BLOCOS",
    "BLOCK_OF",
    "CLAUSULA_OBRIGATORIA",
    "ESTRATEGIA_FASE3_PADRAO",
    "FAIXAS_PREMIACAO",
    "FAIXAS_PREMIACAO_RELATORIO",
    "FalhaInjetadaAtomica",
    "MASK_80",
    "PARAMETROS_PADRAO",
    "TABELA_COMBINADA",
    "TABELA_OVERLAP_BIVARIADA",
    "TABELA_OVERLAP_FAIXAS",
    "TABELA_OVERLAP_PREMIADOS",
    "VERSAO_ALGORITMO",
    "auditar_carteira_completa",
    "avaliar_delta_q_dmax_local",
    "avaliar_e_aplicar_swap_fase3",
    "calcular_coocorrencia_global_bruta",
    "calcular_delta_phi2_exato_candidato",
    "calcular_hashes_certificados",
    "calcular_metricas_intersecao_bruta",
    "calcular_n2_celula",
    "calcular_q_plus",
    "capturar_snapshot_estado",
    "classificar_homologacao_kmax",
    "comparar_estado_snapshot",
    "exigir",
    "gerar_carteira_10000_otimizada",
    "gerar_tabelas_hipergeometricas",
    "inicializar_carteira_fase12",
    "sha256_matriz_incidencia_canonica",
    "somar_comb_vetor",
    "validar_bilhete_individual",
    "validar_entrada_carteira",
    "validar_r1_r9_rapido",
    "validar_trilha_jsonl_em_disco",
    "verificar_consistencia_lam_e_presenca",
]
