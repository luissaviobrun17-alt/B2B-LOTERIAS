# -*- coding: utf-8 -*-
"""
ETAPA 5: INTEGRACAO ISOLADA EM HOMOLOGACAO (FASTAPI) E CLIENTE FAIL-CLOSED
=========================================================================
Constroi uma instancia FastAPI isolada que espelha 100% das rotas existentes de
`api.app` sem alterar `api.py`, acrescentando os endpoints do LOTOFACIL MODO 4
protegidos por feature flag explicita (`lotofacil_modo4_ativo=False` por padrao),
verificacao fail-closed de integridade SHA-256 (Etapa 5 + Etapas 1..4 + Lotomania)
e auditoria cruzada contra a referencia independente AST-isolada.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, replace
from decimal import Decimal
import json
import math
import os
import socket
import threading
import time
from typing import Any, Dict, List, Literal, Optional, Sequence, Tuple, Union
import urllib.error
import urllib.request

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr, field_validator
import uvicorn

import api as api_producao

from .etapa1_regras_oficiais import (
    CLAUSULA_MATEMATICA_OBRIGATORIA,
    ErroValidacaoLotofacilError,
)
from .etapa2_funcao_objetivo import (
    NOMES_COMPONENTES,
    avaliar_carteira_etapa2,
)
from .etapa4_arquitetura_adaptativa import (
    HISTORICO_GERACAO_ETAPA4,
    VERSAO_ARQUITETURA_ETAPA4,
    integrar_configuracao_caixa_etapa1,
)
from .etapa4_referencia_independente import (
    auditar_conformidade_etapa4_ref,
    avaliar_carteira_ref_etapa4,
)
from .etapa5_experimento_despacho import (
    INICIALIZACOES_MISTAS_PERMITIDAS,
    POLITICAS_MICRO_PERMITIDAS,
    VERSAO_MODULO_ETAPA5,
    IntegridadeLotofacilEtapa5Error,
    executar_com_politica_etapa5,
    garantir_integridade_etapa5_ou_falhar,
    verificar_integridade_etapa5,
)

VERSAO_HOMOLOGACAO_ETAPA5 = "5.0.0-api-homologacao"
ENV_FEATURE_FLAG_LOTOFACIL_MODO4 = "LOTOFACIL_MODO4_ATIVO"
_ROTAS_INTERNAS_FASTAPI = {
    "/openapi.json",
    "/docs",
    "/docs/oauth2-redirect",
    "/redoc",
    "/health",
}


@dataclass(frozen=True)
class ConfigHomologacaoLotofacilModo4:
    """Configuracao imutavel da instancia isolada de homologacao."""

    lotofacil_modo4_ativo: bool = False
    verificar_integridade_na_requisicao: bool = True
    verificar_lotomania_selo: bool = True
    exigir_manifesto_etapa5: bool = False
    validar_referencia_independente: bool = True
    politica_micro: str = "conservadora_3J"
    inicializacao_mista: str = "padrao"
    max_avaliacoes_teto: int = 2000
    max_iteracoes_teto: int = 2000
    diretorio_base: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.lotofacil_modo4_ativo, bool):
            raise ValueError("lotofacil_modo4_ativo deve ser bool estrito.")
        if self.politica_micro not in POLITICAS_MICRO_PERMITIDAS:
            raise ValueError(f"politica_micro invalida: {self.politica_micro}")
        if self.inicializacao_mista not in INICIALIZACOES_MISTAS_PERMITIDAS:
            raise ValueError(f"inicializacao_mista invalida: {self.inicializacao_mista}")


def _parse_bool_env(valor: Optional[str], padrao: bool = False) -> bool:
    if valor is None:
        return padrao
    norm = valor.strip().lower()
    if norm in ("1", "true", "sim", "yes", "on"):
        return True
    if norm in ("0", "false", "nao", "no", "off", ""):
        return False
    raise ValueError(f"Valor booleano invalido em variavel de ambiente: {valor!r}")


def carregar_config_homologacao_de_env(
    *,
    padrao_ativo: bool = False,
    diretorio_base: Optional[str] = None,
) -> ConfigHomologacaoLotofacilModo4:
    """Carrega configuracao lendo feature flag explicita (padrao False)."""
    ativo = _parse_bool_env(os.environ.get(ENV_FEATURE_FLAG_LOTOFACIL_MODO4), padrao=padrao_ativo)
    return ConfigHomologacaoLotofacilModo4(
        lotofacil_modo4_ativo=ativo,
        diretorio_base=diretorio_base,
    )


def _validar_numero_finito(val: Any, nome: str) -> Any:
    if val is None:
        return None
    if isinstance(val, bool):
        raise ValueError(f"Campo '{nome}' nao aceita booleano.")
    if isinstance(val, float) and not math.isfinite(val):
        raise ValueError(f"Campo '{nome}' deve ser finito.")
    return val


class LotofacilModo4GerarRequest(BaseModel):
    """Schema estrito sem historico/previsao para geracao de carteiras."""

    model_config = ConfigDict(extra="forbid")

    pool: Optional[List[StrictInt]] = None
    fixas: List[StrictInt] = Field(default_factory=list)
    bloqueadas: List[StrictInt] = Field(default_factory=list)
    modo_fixas: Literal["todos_os_jogos", "composicao_pool"] = "todos_os_jogos"
    quantidade_jogos: Optional[StrictInt] = Field(default=None, ge=1, le=5000)
    tamanho_aposta: StrictInt = Field(default=15, ge=15, le=20)
    tamanhos_jogos: Optional[List[StrictInt]] = None
    orcamento_brl: Optional[Union[StrictStr, StrictFloat, StrictInt]] = None
    pesos: Optional[Dict[StrictStr, Union[StrictFloat, StrictInt]]] = None
    perfil_pesos: Optional[StrictStr] = None
    tipo_concurso: Literal[
        "concurso_regular",
        "concurso_final_zero",
        "lotofacil_independencia",
    ] = "concurso_regular"
    semente: StrictInt = Field(default=42, ge=0)
    max_avaliacoes: StrictInt = Field(default=400, ge=1, le=2000)
    max_iteracoes: StrictInt = Field(default=200, ge=1, le=2000)
    limite_tempo_segundos: Optional[Union[StrictFloat, StrictInt]] = None
    limite_memoria_mb: Optional[Union[StrictFloat, StrictInt]] = None
    limite_combinacoes_exatas: StrictInt = Field(default=10_000, ge=1, le=250_000)
    prioridade: Literal[
        "equilibrio_adaptativo",
        "qualidade_maxima",
        "baixa_latencia",
    ] = "equilibrio_adaptativo"
    forcar_algoritmo: Optional[
        Literal[
            "referencia_aleatoria",
            "busca_exata_pequena",
            "algoritmo_guloso",
            "busca_local_trocas",
            "multiplos_reinicios",
            "estrategia_combinada",
        ]
    ] = None

    @field_validator("orcamento_brl", "limite_tempo_segundos", "limite_memoria_mb")
    @classmethod
    def _checar_escalar_finito(cls, v: Any, info: Any) -> Any:
        return _validar_numero_finito(v, info.field_name)

    @field_validator("pesos")
    @classmethod
    def _checar_pesos_finitos(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return None
        for k, val in v.items():
            _validar_numero_finito(val, f"pesos[{k}]")
        return v


class LotofacilModo4AvaliarRequest(BaseModel):
    """Schema estrito para auditoria matematica de carteiras fornecidas."""

    model_config = ConfigDict(extra="forbid")

    carteira: List[List[StrictInt]] = Field(..., min_length=1)
    pool: Optional[List[StrictInt]] = None
    fixas: List[StrictInt] = Field(default_factory=list)
    bloqueadas: List[StrictInt] = Field(default_factory=list)
    modo_fixas: Literal["todos_os_jogos", "composicao_pool"] = "todos_os_jogos"
    pesos: Optional[Dict[StrictStr, Union[StrictFloat, StrictInt]]] = None
    perfil_pesos: Optional[StrictStr] = None

    @field_validator("pesos")
    @classmethod
    def _checar_pesos_avaliar(cls, v: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        if v is None:
            return None
        for k, val in v.items():
            _validar_numero_finito(val, f"pesos[{k}]")
        return v


def _construir_erro_fail_closed(
    *,
    erro: str,
    mensagem: str,
    motivo: str,
    detalhes: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "erro": erro,
        "mensagem": mensagem,
        "motivo": motivo,
        "jogos": [],
        "fallback_executado": False,
        "historico_utilizado": None,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
        "detalhes": detalhes or {},
    }


def alternar_feature_flag_homologacao(
    app_homologacao: FastAPI,
    ativo: bool,
) -> Dict[str, Any]:
    """Alterna a feature flag em runtime sem alterar `api.py` nem reiniciar processo."""
    if not isinstance(ativo, bool):
        raise ValueError("Parametro 'ativo' deve ser bool estrito.")
    cfg_atual: ConfigHomologacaoLotofacilModo4 = app_homologacao.state.config_lotofacil_modo4
    cfg_nova = replace(cfg_atual, lotofacil_modo4_ativo=ativo)
    app_homologacao.state.config_lotofacil_modo4 = cfg_nova
    return {
        "feature_flag_anterior": cfg_atual.lotofacil_modo4_ativo,
        "feature_flag_atual": cfg_nova.lotofacil_modo4_ativo,
        "politica_micro": cfg_nova.politica_micro,
        "inicializacao_mista": cfg_nova.inicializacao_mista,
    }


def _avaliar_disponibilidade_lotofacil(cfg: ConfigHomologacaoLotofacilModo4) -> Dict[str, Any]:
    integridade = verificar_integridade_etapa5(
        diretorio_base=cfg.diretorio_base,
        verificar_lotomania_selo=cfg.verificar_lotomania_selo,
        exigir_manifesto_etapa5=cfg.exigir_manifesto_etapa5,
    )
    motivo: Optional[str] = None
    if not cfg.lotofacil_modo4_ativo:
        motivo = "feature_flag_desativada"
    elif cfg.verificar_integridade_na_requisicao and not integridade["integro"]:
        motivo = "falha_integridade_criptografica"

    disponivel = bool(
        cfg.lotofacil_modo4_ativo
        and (not cfg.verificar_integridade_na_requisicao or integridade["integro"])
    )
    return {
        "disponivel": disponivel,
        "feature_flag_ativa": cfg.lotofacil_modo4_ativo,
        "integridade_etapa5_valida": integridade["integro"],
        "selo_lotomania_valido": integridade["selo_lotomania_valido"],
        "motivo_indisponibilidade": motivo,
        "versao_motor": VERSAO_ARQUITETURA_ETAPA4,
        "versao_homologacao": VERSAO_HOMOLOGACAO_ETAPA5,
        "politica_micro": cfg.politica_micro,
        "inicializacao_mista": cfg.inicializacao_mista,
        "historico_geracao": HISTORICO_GERACAO_ETAPA4,
        "fallback_permitido": False,
        "detalhes_integridade": integridade,
    }


def _sanitizar_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _sanitizar_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitizar_json(x) for x in obj]
    if isinstance(obj, Decimal):
        return str(obj)
    return obj


def criar_app_homologacao(
    config: Optional[ConfigHomologacaoLotofacilModo4] = None,
) -> FastAPI:
    """
    Cria aplicacao FastAPI isolada copiando todas as rotas existentes de `api.app`
    (exceto `/health`, estendida preservando integralmente as chaves originais) e
    expondo os novos endpoints `/api/v1/lotofacil-modo4/*`.
    """
    cfg_inicial = config if config is not None else ConfigHomologacaoLotofacilModo4()
    app_h = FastAPI(
        title=f"{api_producao.app.title} [Homologacao Lotofacil MODO 4 Etapa 5]",
        version=api_producao.app.version,
    )
    app_h.state.config_lotofacil_modo4 = cfg_inicial

    app_h.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app_h.exception_handler(RequestValidationError)
    async def _tratar_validacao_pydantic(
        request: Request, exc: RequestValidationError
    ) -> JSONResponse:
        if request.url.path.startswith("/api/v1/lotofacil-modo4"):
            return JSONResponse(
                status_code=422,
                content={
                    "detail": exc.errors(),
                    **_construir_erro_fail_closed(
                        erro="REQUISICAO_INVALIDA_LOTOFACIL_MODO4",
                        mensagem="Parametros invalidos ou campo proibido informado. Nenhum jogo foi gerado.",
                        motivo="validacao_schema_estrito",
                    ),
                },
            )
        return JSONResponse(status_code=422, content={"detail": exc.errors()})

    # Copia todas as rotas da API de producao sem modificar `api.app`
    for rota in api_producao.app.routes:
        if isinstance(rota, APIRoute) and rota.path not in _ROTAS_INTERNAS_FASTAPI:
            app_h.router.routes.append(rota)

    @app_h.get("/health")
    def endpoint_health_homologacao() -> Dict[str, Any]:
        payload = dict(api_producao.endpoint_health())
        cfg_atual: ConfigHomologacaoLotofacilModo4 = app_h.state.config_lotofacil_modo4
        disp = _avaliar_disponibilidade_lotofacil(cfg_atual)
        payload["lotofacil_modo4"] = {
            "disponivel": disp["disponivel"],
            "feature_flag_ativa": disp["feature_flag_ativa"],
            "integridade_etapa5_valida": disp["integridade_etapa5_valida"],
            "motivo_indisponibilidade": disp["motivo_indisponibilidade"],
            "versao_motor": disp["versao_motor"],
            "versao_homologacao": disp["versao_homologacao"],
            "politica_micro": disp["politica_micro"],
            "inicializacao_mista": disp["inicializacao_mista"],
            "fallback_permitido": False,
        }
        return payload

    @app_h.get("/api/v1/lotofacil-modo4/status")
    def endpoint_lotofacil_modo4_status() -> Dict[str, Any]:
        cfg_atual: ConfigHomologacaoLotofacilModo4 = app_h.state.config_lotofacil_modo4
        status_disp = _avaliar_disponibilidade_lotofacil(cfg_atual)
        return {
            **status_disp,
            "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
            "regimes_caixa": [
                integrar_configuracao_caixa_etapa1("concurso_regular"),
                integrar_configuracao_caixa_etapa1("concurso_final_zero"),
                integrar_configuracao_caixa_etapa1("lotofacil_independencia"),
            ],
        }

    @app_h.post("/api/v1/lotofacil-modo4/gerar")
    def endpoint_lotofacil_modo4_gerar(req: LotofacilModo4GerarRequest) -> Dict[str, Any]:
        cfg_atual: ConfigHomologacaoLotofacilModo4 = app_h.state.config_lotofacil_modo4
        if not cfg_atual.lotofacil_modo4_ativo:
            raise HTTPException(
                status_code=503,
                detail=_construir_erro_fail_closed(
                    erro="LOTOFACIL_MODO4_DESATIVADO",
                    mensagem=(
                        "LOTOFACIL MODO 4 temporariamente desativado por feature flag "
                        "de homologacao. Nenhum jogo foi gerado."
                    ),
                    motivo="feature_flag_desativada",
                ),
            )

        if cfg_atual.verificar_integridade_na_requisicao:
            try:
                integridade = garantir_integridade_etapa5_ou_falhar(
                    diretorio_base=cfg_atual.diretorio_base,
                    verificar_lotomania_selo=cfg_atual.verificar_lotomania_selo,
                    exigir_manifesto_etapa5=cfg_atual.exigir_manifesto_etapa5,
                )
            except IntegridadeLotofacilEtapa5Error as exc:
                raise HTTPException(
                    status_code=503,
                    detail=_construir_erro_fail_closed(
                        erro="FALHA_INTEGRIDADE_ETAPA5",
                        mensagem=(
                            "Verificacao criptografica SHA-256 falhou (regime fail-closed). "
                            "Nenhum jogo foi gerado."
                        ),
                        motivo="integridade_violada",
                        detalhes={"erro_integridade": str(exc)},
                    ),
                ) from exc
        else:
            integridade = {"integro": None, "verificacao_desabilitada": True}

        if req.max_avaliacoes > cfg_atual.max_avaliacoes_teto:
            raise HTTPException(
                status_code=422,
                detail=_construir_erro_fail_closed(
                    erro="ORCAMENTO_EXCEDE_TETO_HOMOLOGACAO",
                    mensagem=f"max_avaliacoes={req.max_avaliacoes} excede teto {cfg_atual.max_avaliacoes_teto}.",
                    motivo="teto_computacional",
                ),
            )
        if req.max_iteracoes > cfg_atual.max_iteracoes_teto:
            raise HTTPException(
                status_code=422,
                detail=_construir_erro_fail_closed(
                    erro="ITERACOES_EXCEDEM_TETO_HOMOLOGACAO",
                    mensagem=f"max_iteracoes={req.max_iteracoes} excede teto {cfg_atual.max_iteracoes_teto}.",
                    motivo="teto_computacional",
                ),
            )

        try:
            res = executar_com_politica_etapa5(
                pool=req.pool,
                fixas=req.fixas,
                bloqueadas=req.bloqueadas,
                modo_fixas=req.modo_fixas,
                quantidade_jogos=req.quantidade_jogos,
                tamanho_aposta=req.tamanho_aposta,
                tamanhos_jogos=req.tamanhos_jogos,
                orcamento_brl=req.orcamento_brl,
                pesos=req.pesos,
                perfil_pesos=req.perfil_pesos,
                tipo_concurso=req.tipo_concurso,
                semente=req.semente,
                max_avaliacoes=req.max_avaliacoes,
                max_iteracoes=req.max_iteracoes,
                limite_tempo_segundos=req.limite_tempo_segundos,
                limite_memoria_mb=req.limite_memoria_mb,
                limite_combinacoes_exatas=req.limite_combinacoes_exatas,
                prioridade=req.prioridade,
                forcar_algoritmo=req.forcar_algoritmo,
                politica_micro=cfg_atual.politica_micro,
                inicializacao_mista=cfg_atual.inicializacao_mista,
                validar_referencia_independente=cfg_atual.validar_referencia_independente,
            )
        except ErroValidacaoLotofacilError as exc:
            raise HTTPException(
                status_code=422,
                detail=_construir_erro_fail_closed(
                    erro="PARAMETRO_INVALIDO_LOTOFACIL",
                    mensagem=f"Restricao combinatoria ou orcamentaria invalida: {exc}",
                    motivo="validacao_combinatoria",
                ),
            ) from exc
        except Exception as exc:
            raise HTTPException(
                status_code=500,
                detail=_construir_erro_fail_closed(
                    erro="ERRO_INTERNO_LOTOFACIL_MODO4",
                    mensagem=(
                        "Falha interna na geracao LOTOFACIL MODO 4 (sem fallback). "
                        f"Detalhe: {type(exc).__name__}"
                    ),
                    motivo="erro_interno_fail_closed",
                ),
            ) from exc

        esp = res["especificacao"]
        jogos = res.get("jogos", [])
        tamanhos_esp = list(esp["tamanhos_jogos"])
        if len(jogos) != len(tamanhos_esp) or len({tuple(j) for j in jogos}) != len(jogos):
            raise HTTPException(
                status_code=500,
                detail=_construir_erro_fail_closed(
                    erro="POS_CONDICAO_INCONSISTENTE",
                    mensagem="Carteira retornada falhou na verificacao estrita de pos-condicao.",
                    motivo="falha_pos_condicao",
                ),
            )

        resposta = {
            **res,
            "sucesso": True,
            "fallback_executado": False,
            "historico_utilizado": HISTORICO_GERACAO_ETAPA4,
            "homologacao_etapa5": {
                "versao_homologacao": VERSAO_HOMOLOGACAO_ETAPA5,
                "feature_flag_ativa": cfg_atual.lotofacil_modo4_ativo,
                "config": asdict(cfg_atual),
                "integridade": integridade,
            },
        }
        return _sanitizar_json(resposta)

    @app_h.post("/api/v1/lotofacil-modo4/avaliar")
    def endpoint_lotofacil_modo4_avaliar(req: LotofacilModo4AvaliarRequest) -> Dict[str, Any]:
        cfg_atual: ConfigHomologacaoLotofacilModo4 = app_h.state.config_lotofacil_modo4
        if not cfg_atual.lotofacil_modo4_ativo:
            raise HTTPException(
                status_code=503,
                detail=_construir_erro_fail_closed(
                    erro="LOTOFACIL_MODO4_DESATIVADO",
                    mensagem="LOTOFACIL MODO 4 desativado por feature flag.",
                    motivo="feature_flag_desativada",
                ),
            )

        if cfg_atual.verificar_integridade_na_requisicao:
            try:
                garantir_integridade_etapa5_ou_falhar(
                    diretorio_base=cfg_atual.diretorio_base,
                    verificar_lotomania_selo=cfg_atual.verificar_lotomania_selo,
                    exigir_manifesto_etapa5=cfg_atual.exigir_manifesto_etapa5,
                )
            except IntegridadeLotofacilEtapa5Error as exc:
                raise HTTPException(
                    status_code=503,
                    detail=_construir_erro_fail_closed(
                        erro="FALHA_INTEGRIDADE_ETAPA5",
                        mensagem="Verificacao criptografica falhou. Avaliacao bloqueada.",
                        motivo="integridade_violada",
                        detalhes={"erro_integridade": str(exc)},
                    ),
                ) from exc

        try:
            pool_efetivo = list(range(1, 26)) if req.pool is None else req.pool
            av_e2 = avaliar_carteira_etapa2(
                req.carteira,
                pool=pool_efetivo,
                fixas=req.fixas,
                bloqueadas=req.bloqueadas,
                modo_fixas=req.modo_fixas,
                pesos=req.pesos,
                perfil_pesos=req.perfil_pesos,
            )
            av_ref = avaliar_carteira_ref_etapa4(
                req.carteira,
                pool=pool_efetivo,
                fixas=req.fixas,
                bloqueadas=req.bloqueadas,
                modo_fixas=req.modo_fixas,
                pesos=av_e2["pesos"],
            )
            conf = auditar_conformidade_etapa4_ref(
                req.carteira,
                pool=pool_efetivo,
                fixas=req.fixas,
                bloqueadas=req.bloqueadas,
                modo_fixas=req.modo_fixas,
            )
        except ErroValidacaoLotofacilError as exc:
            raise HTTPException(
                status_code=422,
                detail=_construir_erro_fail_closed(
                    erro="CARTEIRA_INVALIDA_LOTOFACIL",
                    mensagem=f"Carteira ou restricoes invalidas: {exc}",
                    motivo="validacao_carteira",
                ),
            ) from exc

        div_f = abs(float(av_e2["funcao_objetivo_F"]) - float(av_ref["funcao_objetivo_F"]))
        div_comp = max(
            abs(float(av_e2["componentes"][k]) - float(av_ref["componentes"][k]))
            for k in NOMES_COMPONENTES
        )
        if div_f > 1e-12 or div_comp > 1e-12:
            raise HTTPException(
                status_code=500,
                detail=_construir_erro_fail_closed(
                    erro="DIVERGENCIA_REFERENCIA_INDEPENDENTE",
                    mensagem="Divergencia numerica detectada entre motor e referencia independente.",
                    motivo="auditoria_matematica_fail_closed",
                    detalhes={"divergencia_F": div_f, "divergencia_max_componente": div_comp},
                ),
            )
        return _sanitizar_json(
            {
                "sucesso": True,
                "conforme_restricoes": conf["conforme"],
                "violacoes": conf["violacoes"],
                "funcao_objetivo_F": av_e2["funcao_objetivo_F"],
                "componentes": av_e2["componentes"],
                "metricas_combinatorias": av_ref["metricas_combinatorias"],
                "distincao_seis_grandezas_probabilisticas": av_ref[
                    "distincao_seis_grandezas_probabilisticas"
                ],
                "auditoria_referencia_independente": {
                    "F_referencia": av_ref["funcao_objetivo_F"],
                    "divergencia_F": div_f,
                    "divergencia_max_componente": div_comp,
                    "tolerancia_exigida": 1e-12,
                },
                "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
                "fallback_executado": False,
            }
        )

    return app_h


class ServidorHttpHomologacao:
    """
    Context manager para subir um servidor Uvicorn HTTP real em loopback 127.0.0.1
    sobre porta efemera para testes ponta a ponta e comparativo 3 vias.
    """

    def __init__(self, app_asgi: FastAPI, host: str = "127.0.0.1") -> None:
        self.app_asgi = app_asgi
        self.host = host
        self._sock: Optional[socket.socket] = None
        self._server: Optional[uvicorn.Server] = None
        self._thread: Optional[threading.Thread] = None
        self.port: int = 0
        self.base_url: str = ""

    def __enter__(self) -> "ServidorHttpHomologacao":
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.host, 0))
        sock.listen(128)
        self._sock = sock
        self.port = int(sock.getsockname()[1])
        self.base_url = f"http://{self.host}:{self.port}"

        uv_cfg = uvicorn.Config(
            self.app_asgi,
            host=self.host,
            port=self.port,
            log_level="critical",
            access_log=False,
        )
        server = uvicorn.Server(uv_cfg)
        server.install_signal_handlers = lambda: None
        self._server = server
        self._thread = threading.Thread(
            target=server.run,
            kwargs={"sockets": [sock]},
            daemon=True,
        )
        self._thread.start()

        deadline = time.perf_counter() + 10.0
        while not server.started and time.perf_counter() < deadline:
            if not self._thread.is_alive():
                raise RuntimeError("Servidor HTTP de homologacao encerrou prematuramente.")
            time.sleep(0.02)
        if not server.started:
            raise TimeoutError("Timeout ao aguardar inicializacao do servidor HTTP de homologacao.")
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._server is not None:
            self._server.should_exit = True
        if self._thread is not None:
            self._thread.join(timeout=5.0)
        if self._sock is not None:
            try:
                self._sock.close()
            except OSError:
                pass


def chamar_api_lotofacil_modo4_seguro(
    base_url: str,
    payload: Optional[Mapping[str, Any]] = None,
    *,
    endpoint: str = "/api/v1/lotofacil-modo4/gerar",
    metodo: str = "POST",
    timeout_s: float = 5.0,
) -> Dict[str, Any]:
    """
    Cliente fail-closed estrito para consumo do LOTOFACIL MODO 4.
    Qualquer erro de rede, timeout, HTTP != 200, JSON malformado ou resposta sem
    carteira valida resulta obrigatoriamente em sucesso=False, jogos=[] e
    fallback_executado=False.
    """
    url = f"{base_url.rstrip('/')}{endpoint}"
    dados = None if payload is None else json.dumps(payload).encode("utf-8")
    cabecalhos = {"Accept": "application/json"}
    if dados is not None:
        cabecalhos["Content-Type"] = "application/json"

    req = urllib.request.Request(url, data=dados, headers=cabecalhos, method=metodo)
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            status = int(resp.status)
            bruto = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        try:
            corpo_err = json.loads(exc.read().decode("utf-8", errors="replace"))
        except Exception:
            corpo_err = None
        return {
            "sucesso": False,
            "status_http": int(exc.code),
            "jogos": [],
            "fallback_executado": False,
            "erro": f"HTTP_{exc.code}",
            "dados_brutos": corpo_err,
        }
    except (urllib.error.URLError, TimeoutError, socket.timeout, OSError) as exc:
        return {
            "sucesso": False,
            "status_http": None,
            "jogos": [],
            "fallback_executado": False,
            "erro": f"REDE_OU_TIMEOUT:{type(exc).__name__}",
            "dados_brutos": None,
        }

    try:
        parsed = json.loads(bruto)
    except json.JSONDecodeError as exc:
        return {
            "sucesso": False,
            "status_http": status,
            "jogos": [],
            "fallback_executado": False,
            "erro": f"JSON_CORROMPIDO:{exc.msg}",
            "dados_brutos": None,
        }

    if not isinstance(parsed, dict):
        return {
            "sucesso": False,
            "status_http": status,
            "jogos": [],
            "fallback_executado": False,
            "erro": "RESPOSTA_NAO_OBJETO",
            "dados_brutos": None,
        }

    if endpoint.endswith("/gerar"):
        jogos = parsed.get("jogos")
        if (
            status != 200
            or parsed.get("sucesso") is not True
            or not isinstance(jogos, list)
            or len(jogos) == 0
            or parsed.get("historico_utilizado") is not None
            or parsed.get("fallback_executado") is not False
        ):
            return {
                "sucesso": False,
                "status_http": status,
                "jogos": [],
                "fallback_executado": False,
                "erro": "CONTRATO_GERACAO_INVALIDO",
                "dados_brutos": parsed,
            }
        return {
            "sucesso": True,
            "status_http": status,
            "jogos": jogos,
            "fallback_executado": False,
            "erro": None,
            "dados_brutos": parsed,
        }

    return {
        "sucesso": status == 200,
        "status_http": status,
        "jogos": [],
        "fallback_executado": False,
        "erro": None if status == 200 else f"HTTP_{status}",
        "dados_brutos": parsed,
    }
