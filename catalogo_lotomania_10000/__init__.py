# -*- coding: utf-8 -*-
"""
Interface somente-leitura do catalogo versionado e imutavel de carteiras
otimizadas da Lotomania (`CATALOGO_LOTOMANIA_10000`).

Este pacote nao aciona otimizadores combinatorios em runtime nem carrega chaves
privadas no caminho de leitura.
"""

from catalogo_lotomania_10000.canonicalizacao import (
    CLAUSULA_OBRIGATORIA,
    CONFIGURACAO_PADRAO_S1_1080K,
    ESQUEMA_CATALOGO_VERSAO,
    ESTRATEGIA_FASE3_PADRAO,
    SHA256_CONFIGURACAO_PADRAO_S1_1080K,
    VERSAO_ALGORITMO_PADRAO,
    calcular_sha256_configuracao,
    canonicalizar_configuracao,
    formatar_decimal_canonico,
    montar_id_carteira,
    serializar_jcs_canonico,
)
from catalogo_lotomania_10000.crypto_selo import (
    CHAVE_PUBLICA_CATALOGO_SHA256,
    CatalogoIndisponivelError,
    CatalogoLotomaniaError,
    IntegridadeCatalogoError,
    SolicitacaoForaDaGradeError,
)
from catalogo_lotomania_10000.leitor import (
    CAMINHO_CHAVE_PUBLICA_PADRAO,
    DIR_CATALOGO_PADRAO,
    LIMITE_MAXIMO_CACHE_BYTES,
    LeitorCatalogoLotomania,
    abrir_catalogo,
)

__all__ = [
    "CAMINHO_CHAVE_PUBLICA_PADRAO",
    "CHAVE_PUBLICA_CATALOGO_SHA256",
    "CLAUSULA_OBRIGATORIA",
    "CONFIGURACAO_PADRAO_S1_1080K",
    "CatalogoIndisponivelError",
    "CatalogoLotomaniaError",
    "DIR_CATALOGO_PADRAO",
    "ESQUEMA_CATALOGO_VERSAO",
    "ESTRATEGIA_FASE3_PADRAO",
    "IntegridadeCatalogoError",
    "LIMITE_MAXIMO_CACHE_BYTES",
    "LeitorCatalogoLotomania",
    "SHA256_CONFIGURACAO_PADRAO_S1_1080K",
    "SolicitacaoForaDaGradeError",
    "VERSAO_ALGORITMO_PADRAO",
    "abrir_catalogo",
    "calcular_sha256_configuracao",
    "canonicalizar_configuracao",
    "formatar_decimal_canonico",
    "montar_id_carteira",
    "serializar_jcs_canonico",
]
