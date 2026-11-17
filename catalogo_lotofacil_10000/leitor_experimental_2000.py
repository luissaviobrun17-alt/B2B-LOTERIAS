# -*- coding: utf-8 -*-
"""
MÓDULO EXPERIMENTAL ISOLADO: LEITOR DO CATÁLOGO CANÔNICO J=2.000 (FASE 3)
========================================================================
Módulo de homologação operacional isolado para carregamento, auditoria e
benchmarking da carteira canônica de 2.000 jogos da Lotofácil MODO 4.

Diretrizes de Governança da Fase 3:
1. Módulo experimental desacoplado de leitor.py oficial (que permanece intacto).
2. Sem integração na API oficial e sem ativação em produção (OFF_STANDBY).
3. Triplo hash SHA-256 verificado por leitura binária direta em disco.
4. Auto-recuperação suportada a partir da custódia isolada.
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
import time
import tracemalloc
from typing import Any, Dict, List, Optional, Tuple

DIR_CATALOGO = Path(__file__).resolve().parent

# Arquivos canônicos locais
CAMINHO_CATALOGO_1000 = DIR_CATALOGO / "lotofacil_carteira_1000.json"
CAMINHO_MANIFESTO_1000 = DIR_CATALOGO / "lotofacil_carteira_1000.json.sha256"

CAMINHO_CATALOGO_2000 = DIR_CATALOGO / "lotofacil_carteira_2000.json"
CAMINHO_MANIFESTO_2000 = DIR_CATALOGO / "lotofacil_carteira_2000.json.sha256"

# Custódias externas isoladas
CAMINHO_BACKUP_1000 = Path(
    r"C:\Users\Luis Brun\.gemini\antigravity\scratch\backup_oficial_lotofacil_1000"
) / "lotofacil_carteira_1000.json"

CAMINHO_BACKUP_2000 = Path(
    r"C:\Users\Luis Brun\.gemini\antigravity\scratch\backup_oficial_lotofacil_2000"
) / "lotofacil_carteira_2000.json"

# Hashes certificados de J=1.000 (Etapa 2.1)
HASH_FISICO_OFICIAL_J1000 = "9a835a98a2f5a56d806b07683b12dd1ed393d54d6d0ba291ed2084443b2ee595"
HASH_JOGOS_OFICIAL_J1000 = "891c598a23399d0efad1d8f84e44e89559603f1f15a5481206e9be417b86d153"
HASH_DOCUMENTO_OFICIAL_J1000 = "7acb12e1fe5d7767bff798f629e23d1dc61e3c877999b0d764391cfef3bbfd99"
IDENTIFICADOR_CANONICO_J1000 = "LOTOFACIL_MODO4_J1000_CANONICA"

# Hashes certificados de J=2.000 (Etapa 2.2)
HASH_FISICO_OFICIAL_J2000 = "42946f9e8915e55d22fb7c83e7b78ebac5e8241e84dadb610403292051ebdfb1"
HASH_JOGOS_OFICIAL_J2000 = "baf528336b7d935d91262705560c9d7410c8c76987f8a0eddbde82bf5aa93048"
HASH_DOCUMENTO_OFICIAL_J2000 = "25bcad7073ba690c00692317c22f91616f752f2046b2c0825987372cc1716b4b"
IDENTIFICADOR_CANONICO_J2000 = "LOTOFACIL_MODO4_J2000_CANONICA"


class ErroIntegridadeCatalogo2000(Exception):
    """Exceção para discrepâncias na integridade criptográfica da carteira J=2.000."""
    pass


def _calcular_hash_arquivo(caminho: Path) -> str:
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def verificar_integridade_catalogo_2000() -> Tuple[bool, Dict[str, Any]]:
    """
    Audita integralmente os hashes físico, dos jogos e estrutural da carteira J=2.000.
    """
    relatorio: Dict[str, Any] = {
        "arquivo_existe": False,
        "hash_fisico_valido": False,
        "hash_jogos_valido": False,
        "hash_documento_valido": False,
        "jogos_unicos": 0,
        "status_geral": "FALHA",
    }

    if not CAMINHO_CATALOGO_2000.is_file():
        relatorio["motivo"] = "Arquivo lotofacil_carteira_2000.json ausente no catálogo."
        return False, relatorio

    relatorio["arquivo_existe"] = True
    hash_fisico = _calcular_hash_arquivo(CAMINHO_CATALOGO_2000)
    relatorio["hash_fisico_observado"] = hash_fisico
    relatorio["hash_fisico_esperado"] = HASH_FISICO_OFICIAL_J2000
    relatorio["hash_fisico_valido"] = (hash_fisico == HASH_FISICO_OFICIAL_J2000)

    try:
        with open(CAMINHO_CATALOGO_2000, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as e:
        relatorio["motivo"] = f"JSON corrompido: {e}"
        return False, relatorio

    # Checagem dos jogos canônicos
    jogos = doc.get("jogos", [])
    relatorio["total_jogos"] = len(jogos)
    relatorio["jogos_unicos"] = len(set(tuple(sorted(jg)) for jg in jogos))

    serializacao = json.dumps(jogos, separators=(",", ":"))
    hash_jogos = hashlib.sha256(serializacao.encode("utf-8")).hexdigest()
    relatorio["hash_jogos_observado"] = hash_jogos
    relatorio["hash_jogos_esperado"] = HASH_JOGOS_OFICIAL_J2000
    relatorio["hash_jogos_valido"] = (hash_jogos == HASH_JOGOS_OFICIAL_J2000)

    # Checagem do documento estrutural
    doc_sem_hash = {k: v for k, v in doc.items() if k != "sha256_documento_catalogo"}
    hash_doc = hashlib.sha256(
        json.dumps(doc_sem_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    relatorio["hash_documento_observado"] = hash_doc
    relatorio["hash_documento_esperado"] = HASH_DOCUMENTO_OFICIAL_J2000
    relatorio["hash_documento_valido"] = (hash_doc == HASH_DOCUMENTO_OFICIAL_J2000)

    valido = (
        relatorio["hash_fisico_valido"]
        and relatorio["hash_jogos_valido"]
        and relatorio["hash_documento_valido"]
        and relatorio["total_jogos"] == 2000
        and relatorio["jogos_unicos"] == 2000
    )
    relatorio["status_geral"] = "INTEGRO" if valido else "DIVERGENTE"
    return valido, relatorio


def restaurar_catalogo_2000_do_backup() -> bool:
    """
    Restaura o arquivo do catálogo de 2.000 jogos a partir da salvaguarda isolada.
    """
    if not CAMINHO_BACKUP_2000.is_file():
        raise FileNotFoundError(f"Backup isolado de J=2.000 não encontrado em: {CAMINHO_BACKUP_2000}")

    hash_bkp = _calcular_hash_arquivo(CAMINHO_BACKUP_2000)
    if hash_bkp != HASH_FISICO_OFICIAL_J2000:
        raise ErroIntegridadeCatalogo2000(
            f"Backup isolado comprometido: hash {hash_bkp} diverge do oficial!"
        )

    DIR_CATALOGO.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CAMINHO_BACKUP_2000, CAMINHO_CATALOGO_2000)

    man_origem = CAMINHO_BACKUP_2000.parent / "lotofacil_carteira_2000.json.sha256"
    if man_origem.is_file():
        shutil.copy2(man_origem, CAMINHO_MANIFESTO_2000)

    valido, _ = verificar_integridade_catalogo_2000()
    if not valido:
        raise ErroIntegridadeCatalogo2000("Falha de integridade após restauração do catálogo J=2.000!")
    return True


def carregar_documento_catalogo_2000(auto_recuperar: bool = True) -> Dict[str, Any]:
    """
    Carrega o payload JSON completo da carteira homologada de 2.000 jogos.
    """
    valido, rel = verificar_integridade_catalogo_2000()
    if not valido:
        if auto_recuperar:
            restaurar_catalogo_2000_do_backup()
        else:
            raise ErroIntegridadeCatalogo2000(f"Catálogo J=2.000 inválido: {rel.get('motivo')}")

    with open(CAMINHO_CATALOGO_2000, "r", encoding="utf-8") as f:
        return json.load(f)


def obter_carteira_oficial_2000(auto_recuperar: bool = True) -> List[List[int]]:
    """
    Retorna a matriz de 2.000 bilhetes canônicos homologados.
    """
    doc = carregar_documento_catalogo_2000(auto_recuperar=auto_recuperar)
    return [list(sorted(jg)) for jg in doc["jogos"]]


def obter_carteira_por_tamanho(quantidade: int) -> List[List[int]]:
    """
    Função seletora de carteiras canônicas homologadas (suporta 1000 e 2000).
    """
    if quantidade == 1000:
        if not CAMINHO_CATALOGO_1000.is_file():
            raise FileNotFoundError(f"Catálogo J=1000 não encontrado: {CAMINHO_CATALOGO_1000}")
        with open(CAMINHO_CATALOGO_1000, "r", encoding="utf-8") as f:
            doc = json.load(f)
        return [list(sorted(jg)) for jg in doc["jogos"]]
    elif quantidade == 2000:
        return obter_carteira_oficial_2000(auto_recuperar=True)
    else:
        raise ValueError(f"Quantidade de jogos {quantidade} não homologada no catálogo.")


def obter_status_governanca_fase3() -> Dict[str, Any]:
    """
    Retorna o status unificado de governança em ambiente isolado da Fase 3.
    """
    from .leitor import verificar_integridade_catalogo_1000

    val_1000, rel_1000 = verificar_integridade_catalogo_1000()
    val_2000, rel_2000 = verificar_integridade_catalogo_2000()

    return {
        "fase": "FASE_3_INCORPORACAO_ISOLADA",
        "ambiente": "EXPERIMENTAL_ISOLADO",
        "motor_dinamico": {
            "feature_flag": "LOTOFACIL_MODO4_ATIVO",
            "valor": False,
            "estado_producao": "OFF_STANDBY",
        },
        "carteiras": {
            "J1000": {
                "identificador": IDENTIFICADOR_CANONICO_J1000,
                "integro": val_1000,
                "total_jogos": rel_1000.get("total_jogos", 1000),
                "sha256_jogos": HASH_JOGOS_OFICIAL_J1000,
                "sha256_fisico": HASH_FISICO_OFICIAL_J1000,
            },
            "J2000": {
                "identificador": IDENTIFICADOR_CANONICO_J2000,
                "integro": val_2000,
                "total_jogos": rel_2000.get("total_jogos", 2000),
                "sha256_jogos": HASH_JOGOS_OFICIAL_J2000,
                "sha256_fisico": HASH_FISICO_OFICIAL_J2000,
            },
        },
    }
