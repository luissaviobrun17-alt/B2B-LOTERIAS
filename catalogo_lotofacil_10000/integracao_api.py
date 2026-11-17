# -*- coding: utf-8 -*-
"""
INTEGRAÇÃO API: CATÁLOGO OFICIAL LOTOFÁCIL MODO 4 (J=1.000 E J=2.000)
===================================================================
Camada HTTP somente leitura e de auditoria para disponibilização das
carteiras canônicas homologadas de 1.000 e 2.000 jogos no B2B Loterias.

Endpoints providos sob o prefixo `/api/v1/lotofacil-catalogo`:
- GET  /status     -> Status das carteiras, integridade, hashes e governança.
- GET  /metadados  -> Métricas de qualidade combinatória, telemetria e validação.
- GET  /jogos      -> Acesso paginado aos bilhetes homologados (J=1.000 ou J=2.000).
- GET  /auditoria  -> Auditoria em tempo real dos hashes SHA-256 (físico, jogos e doc).
- POST /restaurar  -> Restauração automática a partir da custódia independente (ambiente de teste).
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, FastAPI, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

from .leitor import (
    HASH_DOCUMENTO_OFICIAL_J1000,
    HASH_FISICO_OFICIAL_J1000,
    HASH_JOGOS_OFICIAL_J1000,
    IDENTIFICADOR_CANONICO_J1000,
    HASH_DOCUMENTO_OFICIAL_J2000,
    HASH_FISICO_OFICIAL_J2000,
    HASH_JOGOS_OFICIAL_J2000,
    IDENTIFICADOR_CANONICO_J2000,
    carregar_documento_catalogo,
    carregar_documento_catalogo_1000,
    carregar_documento_catalogo_2000,
    obter_carteira_oficial,
    obter_carteira_oficial_1000,
    obter_carteira_oficial_2000,
    obter_status_governanca,
    restaurar_catalogo_1000_do_backup,
    restaurar_catalogo_2000_do_backup,
    restaurar_catalogo_do_backup,
    verificar_integridade_catalogo,
    verificar_integridade_catalogo_1000,
    verificar_integridade_catalogo_2000,
)

logger = logging.getLogger("b2b_loterias.catalogo_lotofacil")

router_catalogo_lotofacil = APIRouter(
    prefix="/api/v1/lotofacil-catalogo",
    tags=["Catálogo Lotofácil MODO 4 (Multicarteira Canônica)"],
)


@router_catalogo_lotofacil.get("/status")
def endpoint_catalogo_status(
    tamanho: int = Query(default=1000, description="Tamanho da carteira canônica (1000 ou 2000)"),
) -> Dict[str, Any]:
    """Retorna o status geral de governança, integridade dos hashes e identificação oficial."""
    if tamanho not in (1000, 2000):
        raise HTTPException(
            status_code=422,
            detail=f"Tamanho {tamanho} não suportado. Carteiras disponíveis: 1000 e 2000.",
        )

    gov = obter_status_governanca()
    valido, relatorio = verificar_integridade_catalogo(tamanho=tamanho)
    identificador = IDENTIFICADOR_CANONICO_J1000 if tamanho == 1000 else IDENTIFICADOR_CANONICO_J2000

    return {
        "sucesso": True,
        "catalogo": identificador,
        "quantidade_jogos": tamanho,
        "tamanho_aposta": 15,
        "pool": 25,
        "governanca": gov,
        "auditoria_resumida": {
            "integro": valido,
            "status": relatorio.get("status_geral", "DESCONHECIDO"),
            "hash_fisico_valido": relatorio.get("hash_fisico_valido", False),
            "hash_jogos_valido": relatorio.get("hash_jogos_valido", False),
            "hash_documento_valido": relatorio.get("hash_documento_valido", False),
        },
    }


@router_catalogo_lotofacil.get("/metadados")
def endpoint_catalogo_metadados(
    tamanho: int = Query(default=1000, description="Tamanho da carteira canônica (1000 ou 2000)"),
) -> Dict[str, Any]:
    """Retorna o memorial técnico, métricas de qualidade combinatória e tripla validação."""
    if tamanho not in (1000, 2000):
        raise HTTPException(
            status_code=422,
            detail=f"Tamanho {tamanho} não suportado. Carteiras disponíveis: 1000 e 2000.",
        )

    try:
        doc = carregar_documento_catalogo(tamanho=tamanho, auto_recuperar=True)
    except Exception as exc:
        logger.error("Falha ao carregar metadados do catálogo J=%d: %s", tamanho, exc)
        raise HTTPException(status_code=500, detail=f"Erro ao carregar catálogo: {exc}")

    return {
        "sucesso": True,
        "identificador": doc.get("identificador"),
        "versao_formato": doc.get("versao_formato"),
        "semente_utilizada": doc.get("semente"),
        "b_cand_utilizado": doc.get("b_cand_utilizado"),
        "orcamento_max_avaliacoes": doc.get("orcamento_max_avaliacoes"),
        "sha256_jogos_canonicos": doc.get("sha256_jogos_canonicos"),
        "sha256_documento_catalogo": doc.get("sha256_documento_catalogo"),
        "metricas_qualidade": doc.get("metricas_qualidade"),
        "tripla_validacao": doc.get("tripla_validacao"),
        "telemetria": doc.get("telemetria"),
    }


@router_catalogo_lotofacil.get("/jogos")
def endpoint_catalogo_jogos(
    tamanho: int = Query(default=1000, description="Tamanho da carteira canônica (1000 ou 2000)"),
    offset: int = Query(default=0, ge=0, le=10000, description="Índice inicial do bilhete"),
    limit: int = Query(default=100, ge=1, le=2000, description="Quantidade de bilhetes retornados (1 a 2000)"),
) -> Dict[str, Any]:
    """Retorna os bilhetes da carteira homologada com paginação segura e verificada."""
    if tamanho not in (1000, 2000):
        raise HTTPException(
            status_code=422,
            detail=f"Tamanho {tamanho} não suportado. Carteiras disponíveis: 1000 e 2000.",
        )

    try:
        carteira = obter_carteira_oficial(tamanho=tamanho, auto_recuperar=True)
    except Exception as exc:
        logger.error("Falha ao obter carteira de %d jogos: %s", tamanho, exc)
        raise HTTPException(status_code=500, detail=f"Erro no carregamento dos jogos: {exc}")

    total = len(carteira)
    if offset >= total:
        raise HTTPException(
            status_code=422,
            detail=f"Offset {offset} fora dos limites para carteira de tamanho {total}.",
        )

    fatia = carteira[offset : offset + limit]
    identificador = IDENTIFICADOR_CANONICO_J1000 if tamanho == 1000 else IDENTIFICADOR_CANONICO_J2000
    hash_jogos = HASH_JOGOS_OFICIAL_J1000 if tamanho == 1000 else HASH_JOGOS_OFICIAL_J2000

    return {
        "sucesso": True,
        "catalogo": identificador,
        "total_jogos": total,
        "offset": offset,
        "limit": limit,
        "retornados": len(fatia),
        "sha256_jogos_canonicos": hash_jogos,
        "jogos": fatia,
    }


@router_catalogo_lotofacil.get("/auditoria")
def endpoint_catalogo_auditoria(
    tamanho: int = Query(default=1000, description="Tamanho da carteira canônica (1000 ou 2000)"),
) -> JSONResponse:
    """Executa auditoria em tempo real da integridade criptográfica binária do catálogo."""
    if tamanho not in (1000, 2000):
        raise HTTPException(
            status_code=422,
            detail=f"Tamanho {tamanho} não suportado. Carteiras disponíveis: 1000 e 2000.",
        )

    valido, relatorio = verificar_integridade_catalogo(tamanho=tamanho)
    identificador = IDENTIFICADOR_CANONICO_J1000 if tamanho == 1000 else IDENTIFICADOR_CANONICO_J2000
    status_code = 200 if valido else 503
    return JSONResponse(
        status_code=status_code,
        content={
            "sucesso": valido,
            "catalogo": identificador,
            "auditoria": relatorio,
        },
    )


@router_catalogo_lotofacil.post("/restaurar")
def endpoint_catalogo_restaurar(
    tamanho: int = Query(default=1000, description="Tamanho da carteira canônica (1000 ou 2000)"),
) -> Dict[str, Any]:
    """Restaura o catálogo a partir da custódia independente em caso de inconsistência (ambiente de testes)."""
    if tamanho not in (1000, 2000):
        raise HTTPException(
            status_code=422,
            detail=f"Tamanho {tamanho} não suportado. Carteiras disponíveis: 1000 e 2000.",
        )

    try:
        if tamanho == 1000:
            sucesso = restaurar_catalogo_1000_do_backup()
            valido, rel = verificar_integridade_catalogo_1000()
        else:
            sucesso = restaurar_catalogo_2000_do_backup()
            valido, rel = verificar_integridade_catalogo_2000()

        return {
            "sucesso": sucesso,
            "mensagem": f"Catálogo de {tamanho} jogos restaurado com sucesso a partir do backup independente.",
            "auditoria_pos_restauracao": rel,
        }
    except Exception as exc:
        logger.error("Falha na restauração do catálogo J=%d: %s", tamanho, exc)
        raise HTTPException(status_code=500, detail=f"Erro na restauração: {exc}")


def registrar_catalogo_lotofacil_na_api(app: FastAPI) -> None:
    """Registra o router do catálogo na instância FastAPI principal."""
    rotas_existentes = {getattr(r, "path", "") for r in app.routes}
    if "/api/v1/lotofacil-catalogo/status" not in rotas_existentes:
        app.include_router(router_catalogo_lotofacil)
        logger.info("Router do Catálogo Lotofácil MODO 4 (multicarteira) registrado na API com sucesso.")
