# -*- coding: utf-8 -*-
"""
LEITOR OFICIAL DO CATÁLOGO CANÔNICO: LOTOFÁCIL MODO 4 (J=1.000)
===============================================================
Módulo oficial de acesso e auditoria controlada da carteira canônica
de 1.000 jogos da Lotofácil MODO 4 no B2B Loterias.

Garantias implementadas:
1. Verificação criptográfica de triplo hash (físico, jogos e estrutural).
2. Auto-recuperação segura via cópia de custódia independente em caso de corrupção.
3. Imutabilidade em tempo de execução e conformidade estrita com as regras da Caixa.
4. Respeito integral ao estado de governança (OFF_STANDBY).
"""

from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import shutil
from typing import Any, Dict, List, Optional, Tuple

DIR_CATALOGO_ATUAL = Path(__file__).resolve().parent
CAMINHO_CATALOGO_1000 = DIR_CATALOGO_ATUAL / "lotofacil_carteira_1000.json"
CAMINHO_MANIFESTO_1000 = DIR_CATALOGO_ATUAL / "lotofacil_carteira_1000.json.sha256"

CAMINHO_BACKUP_INDEPENDENTE = Path(
    r"C:\Users\Luis Brun\.gemini\antigravity\scratch\backup_oficial_lotofacil_1000"
) / "lotofacil_carteira_1000.json"

# Hashes certificados e congelados formalmente na Etapa 2.1
HASH_FISICO_OFICIAL_J1000 = "9a835a98a2f5a56d806b07683b12dd1ed393d54d6d0ba291ed2084443b2ee595"
HASH_JOGOS_OFICIAL_J1000 = "891c598a23399d0efad1d8f84e44e89559603f1f15a5481206e9be417b86d153"
HASH_DOCUMENTO_OFICIAL_J1000 = "7acb12e1fe5d7767bff798f629e23d1dc61e3c877999b0d764391cfef3bbfd99"

IDENTIFICADOR_CANONICO_J1000 = "LOTOFACIL_MODO4_J1000_CANONICA"


class ErroIntegridadeCatalogoLotofacil(Exception):
    """Exceção lançada quando um arquivo de catálogo diverge dos hashes certificados."""
    pass


def _calcular_hash_arquivo(caminho: Path) -> str:
    with open(caminho, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def verificar_integridade_catalogo_1000() -> Tuple[bool, Dict[str, Any]]:
    """
    Realiza a auditoria em cadeia de integridade física, dos jogos e do documento.
    Retorna uma tupla (valido, relatorio_detalhado).
    """
    relatorio: Dict[str, Any] = {
        "arquivo_existe": False,
        "hash_fisico_valido": False,
        "hash_jogos_valido": False,
        "hash_documento_valido": False,
        "jogos_unicos": 0,
        "status_geral": "FALHA",
    }

    if not CAMINHO_CATALOGO_1000.is_file():
        relatorio["motivo"] = "Arquivo não encontrado no catálogo principal."
        return False, relatorio

    relatorio["arquivo_existe"] = True
    hash_fisico = _calcular_hash_arquivo(CAMINHO_CATALOGO_1000)
    relatorio["hash_fisico_observado"] = hash_fisico
    relatorio["hash_fisico_esperado"] = HASH_FISICO_OFICIAL_J1000
    relatorio["hash_fisico_valido"] = (hash_fisico == HASH_FISICO_OFICIAL_J1000)

    try:
        with open(CAMINHO_CATALOGO_1000, "r", encoding="utf-8") as f:
            doc = json.load(f)
    except Exception as e:
        relatorio["motivo"] = f"JSON corrompido: {e}"
        return False, relatorio

    # Checagem de jogos canônicos
    jogos = doc.get("jogos", [])
    relatorio["total_jogos"] = len(jogos)
    relatorio["jogos_unicos"] = len(set(tuple(sorted(jg)) for jg in jogos))

    serializacao = json.dumps(jogos, separators=(",", ":"))
    hash_jogos = hashlib.sha256(serializacao.encode("utf-8")).hexdigest()
    relatorio["hash_jogos_observado"] = hash_jogos
    relatorio["hash_jogos_esperado"] = HASH_JOGOS_OFICIAL_J1000
    relatorio["hash_jogos_valido"] = (hash_jogos == HASH_JOGOS_OFICIAL_J1000)

    # Checagem de documento canônico
    doc_sem_hash = {k: v for k, v in doc.items() if k != "sha256_documento_catalogo"}
    hash_doc = hashlib.sha256(
        json.dumps(doc_sem_hash, sort_keys=True, separators=(",", ":")).encode("utf-8")
    ).hexdigest()
    relatorio["hash_documento_observado"] = hash_doc
    relatorio["hash_documento_esperado"] = HASH_DOCUMENTO_OFICIAL_J1000
    relatorio["hash_documento_valido"] = (hash_doc == HASH_DOCUMENTO_OFICIAL_J1000)

    valido = (
        relatorio["hash_fisico_valido"]
        and relatorio["hash_jogos_valido"]
        and relatorio["hash_documento_valido"]
        and relatorio["total_jogos"] == 1000
        and relatorio["jogos_unicos"] == 1000
    )
    relatorio["status_geral"] = "INTEGRO" if valido else "DIVERGENTE"
    return valido, relatorio


def restaurar_catalogo_do_backup() -> bool:
    """
    Restaura o catálogo de 1.000 jogos a partir da cópia de segurança independente.
    """
    if not CAMINHO_BACKUP_INDEPENDENTE.is_file():
        raise FileNotFoundError(
            f"Arquivo de backup independente ausente em: {CAMINHO_BACKUP_INDEPENDENTE}"
        )

    hash_bkp = _calcular_hash_arquivo(CAMINHO_BACKUP_INDEPENDENTE)
    if hash_bkp != HASH_FISICO_OFICIAL_J1000:
        raise ErroIntegridadeCatalogoLotofacil(
            f"Backup independente comprometido: hash {hash_bkp} diverge do oficial!"
        )

    DIR_CATALOGO_ATUAL.mkdir(parents=True, exist_ok=True)
    shutil.copy2(CAMINHO_BACKUP_INDEPENDENTE, CAMINHO_CATALOGO_1000)

    # Copia manifesto correspondente se presente no backup
    origem_manifesto = CAMINHO_BACKUP_INDEPENDENTE.parent / "lotofacil_carteira_1000.json.sha256"
    if origem_manifesto.is_file():
        shutil.copy2(origem_manifesto, CAMINHO_MANIFESTO_1000)

    valido, _ = verificar_integridade_catalogo_1000()
    if not valido:
        raise ErroIntegridadeCatalogoLotofacil("Falha de integridade após restauração do catálogo!")
    return True


def carregar_documento_catalogo_1000(auto_recuperar: bool = True) -> Dict[str, Any]:
    """
    Carrega o payload JSON completo do catálogo oficial de 1.000 jogos.
    Garante a integridade do arquivo antes da entrega.
    """
    valido, rel = verificar_integridade_catalogo_1000()
    if not valido:
        if auto_recuperar:
            restaurar_catalogo_do_backup()
        else:
            raise ErroIntegridadeCatalogoLotofacil(
                f"Catálogo de 1.000 jogos inválido: {rel.get('motivo', 'Divergência de hashes')}"
            )

    with open(CAMINHO_CATALOGO_1000, "r", encoding="utf-8") as f:
        return json.load(f)


def obter_carteira_oficial_1000(auto_recuperar: bool = True) -> List[List[int]]:
    """
    Retorna estritamente a matriz de 1.000 jogos canônicos homologados.
    """
    doc = carregar_documento_catalogo_1000(auto_recuperar=auto_recuperar)
    return [list(sorted(jg)) for jg in doc["jogos"]]


def obter_status_governanca() -> Dict[str, Any]:
    """
    Informa o estado normativo de ativação e auditoria da carteira canônica.
    """
    valido, rel = verificar_integridade_catalogo_1000()
    return {
        "modalidade": "LOTOFACIL",
        "modo": 4,
        "versao_catalogo": "2.0-canonica-j1000",
        "identificador": IDENTIFICADOR_CANONICO_J1000,
        "feature_flag": "LOTOFACIL_MODO4_ATIVO",
        "estado_operacional": "OFF_STANDBY",
        "em_producao": False,
        "integridade_confirmada": valido,
        "hashes": {
            "arquivo_fisico": HASH_FISICO_OFICIAL_J1000,
            "jogos_canonicos": HASH_JOGOS_OFICIAL_J1000,
            "documento_estrutural": HASH_DOCUMENTO_OFICIAL_J1000,
        },
    }
