# -*- coding: utf-8 -*-
"""
Pacote oficial do Catálogo Canônico Lotofácil MODO 4 (Escala 10.000).
"""

from .leitor import (
    HASH_DOCUMENTO_OFICIAL_J1000,
    HASH_FISICO_OFICIAL_J1000,
    HASH_JOGOS_OFICIAL_J1000,
    IDENTIFICADOR_CANONICO_J1000,
    carregar_documento_catalogo_1000,
    obter_carteira_oficial_1000,
    obter_status_governanca,
    restaurar_catalogo_do_backup,
    verificar_integridade_catalogo_1000,
)

__all__ = [
    "HASH_DOCUMENTO_OFICIAL_J1000",
    "HASH_FISICO_OFICIAL_J1000",
    "HASH_JOGOS_OFICIAL_J1000",
    "IDENTIFICADOR_CANONICO_J1000",
    "carregar_documento_catalogo_1000",
    "obter_carteira_oficial_1000",
    "obter_status_governanca",
    "restaurar_catalogo_do_backup",
    "verificar_integridade_catalogo_1000",
]
