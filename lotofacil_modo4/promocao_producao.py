# -*- coding: utf-8 -*-
"""
LOTOFACIL MODO 4 - INTEGRACAO DE PROMOCAO CONTROLADA EM PRODUCAO
=================================================================
Modulo de integracao controlada para `api.py` com feature flag explicita
desligada por padrao (`lotofacil_modo4_ativo = False`), politica micro
conservadora por padrao (`"conservadora_3J"`), `"experimental_2J"` exposta
apenas como opcao configuravel desabilitada por padrao, `inicializacao_mista`
travada em `"padrao"`, regime estritamente fail-closed (HTTP 503/422/500 com
zero jogos e zero fallback), verificacao criptografica SHA-256 de ponta a
ponta (Etapas 1-5, base CAIXA, Lotomania Ed25519 e manifesto de promocao)
e auditoria cruzada contra a referencia independente AST-isolada.
"""

from __future__ import annotations

from collections import deque
from dataclasses import asdict, dataclass, replace
from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import json
import math
import os
import threading
from typing import Any, Deque, Dict, List, Literal, Optional, Sequence, Tuple, Union

from fastapi import APIRouter, FastAPI, Request
from fastapi.exception_handlers import request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, StrictFloat, StrictInt, StrictStr, field_validator

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
    IntegridadeLotofacilEtapa5Error,
    calcular_sha256_arquivo,
    executar_com_politica_etapa5,
    verificar_integridade_etapa5,
)

VERSAO_PROMOCAO_LOTOFACIL_MODO4 = "5.1.0-promocao-controlada"
IDENTIFICACAO_OFICIAL_LOTOFACIL_MODO4 = (
    "MOTOR COMBINATORIO DE OTIMIZACAO DE CARTEIRAS - LOTOFACIL | MODO 4"
)
ENV_FEATURE_FLAG_LOTOFACIL_MODO4 = "LOTOFACIL_MODO4_ATIVO"
ENV_POLITICA_MICRO_PADRAO = "LOTOFACIL_MODO4_POLITICA_MICRO"
ENV_PERMITIR_EXPERIMENTAL_2J = "LOTOFACIL_MODO4_PERMITIR_EXPERIMENTAL_2J"
INICIALIZACAO_MISTA_FIXA = "padrao"
POLITICA_MICRO_PRODUCAO_PADRAO = "conservadora_3J"
CAMINHO_MANIFESTO_PROMOCAO_REL = "auditoria/lotofacil_modo4/manifesto_promocao_controlada.json"

BASE_DIR_PADRAO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

ARQUIVOS_PRODUCAO_PROMOCAO: Tuple[str, ...] = (
    "lotofacil_modo4/promocao_producao.py",
    "api.py",
    "motor_lotofacil.py",
    "js/engines/motor_lotofacil_modo4_engine.js",
    "index.html",
    "js/ui.js",
    "B2B_Loterias_Mobile.html",
)

_LOCK_PROMOCAO = threading.RLock()


class IntegridadePromocaoLotofacilError(RuntimeError):
    """Excecao levantada quando a verificacao fail-closed de integridade falha."""


class _FailClosedLotofacilModo4Exception(Exception):
    """Excecao interna para retornar resposta JSON fail-closed com detalhe e chaves topo."""

    def __init__(self, status_code: int, payload: Dict[str, Any]) -> None:
        super().__init__(payload.get("erro", "ERRO_LOTOFACIL_MODO4"))
        self.status_code = int(status_code)
        self.payload = payload


@dataclass(frozen=True)
class ConfigProducaoLotofacilModo4:
    """Configuracao imutavel da promocao controlada em producao."""

    lotofacil_modo4_ativo: bool = False
    politica_micro_padrao: str = POLITICA_MICRO_PRODUCAO_PADRAO
    permitir_experimental_2j: bool = False
    inicializacao_mista: str = INICIALIZACAO_MISTA_FIXA
    verificar_integridade_na_requisicao: bool = True
    verificar_lotomania_selo: bool = True
    exigir_manifesto_etapa5: bool = True
    exigir_manifesto_promocao: bool = False
    validar_referencia_independente: bool = True
    max_avaliacoes_teto: int = 2000
    max_iteracoes_teto: int = 2000
    diretorio_base: Optional[str] = None

    def __post_init__(self) -> None:
        if not isinstance(self.lotofacil_modo4_ativo, bool):
            raise ValueError("lotofacil_modo4_ativo deve ser bool estrito.")
        if not isinstance(self.permitir_experimental_2j, bool):
            raise ValueError("permitir_experimental_2j deve ser bool estrito.")
        if self.politica_micro_padrao not in POLITICAS_MICRO_PERMITIDAS:
            raise ValueError(f"politica_micro_padrao invalida: {self.politica_micro_padrao}")
        if self.politica_micro_padrao == "experimental_2J" and not self.permitir_experimental_2j:
            raise ValueError(
                "politica_micro_padrao='experimental_2J' exige permitir_experimental_2j=True."
            )
        if self.inicializacao_mista != INICIALIZACAO_MISTA_FIXA:
            raise ValueError(
                f"inicializacao_mista deve permanecer '{INICIALIZACAO_MISTA_FIXA}' "
                f"(recebido: {self.inicializacao_mista!r})."
            )
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


def carregar_config_producao_de_env(
    *,
    padrao_ativo: bool = False,
    diretorio_base: Optional[str] = None,
) -> ConfigProducaoLotofacilModo4:
    """
    Carrega configuracao de producao lendo variaveis de ambiente explicitas.
    Por seguranca operacional, `lotofacil_modo4_ativo` e
    `permitir_experimental_2j` iniciam `False` por padrao.
    """
    ativo = _parse_bool_env(os.environ.get(ENV_FEATURE_FLAG_LOTOFACIL_MODO4), padrao=padrao_ativo)
    permitir_2j = _parse_bool_env(
        os.environ.get(ENV_PERMITIR_EXPERIMENTAL_2J),
        padrao=False,
    )
    pol_raw = os.environ.get(ENV_POLITICA_MICRO_PADRAO)
    pol = pol_raw.strip() if pol_raw and pol_raw.strip() else POLITICA_MICRO_PRODUCAO_PADRAO
    return ConfigProducaoLotofacilModo4(
        lotofacil_modo4_ativo=ativo,
        politica_micro_padrao=pol,
        permitir_experimental_2j=permitir_2j,
        inicializacao_mista=INICIALIZACAO_MISTA_FIXA,
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


class LotofacilModo4ProducaoGerarRequest(BaseModel):
    """Schema estrito sem historico/previsao e com politica controlada em producao."""

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
    politica_micro: Optional[Literal["conservadora_3J", "experimental_2J"]] = None
    inicializacao_mista: Literal["padrao"] = "padrao"

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


class LotofacilModo4ProducaoAvaliarRequest(BaseModel):
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


def calcular_hash_carteira_lotofacil(jogos: Sequence[Sequence[int]]) -> str:
    """Calcula SHA-256 canonico sobre os bilhetes ordenados da carteira."""
    canonico = [sorted(int(d) for d in j) for j in jogos]
    serializado = json.dumps(canonico, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(serializado).hexdigest()


def _construir_erro_fail_closed(
    *,
    erro: str,
    mensagem: str,
    motivo: str,
    feature_flag_ativa: bool,
    detalhes: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "sucesso": False,
        "erro": erro,
        "mensagem": mensagem,
        "motivo": motivo,
        "jogos": [],
        "quantidade_entregue": 0,
        "fallback_executado": False,
        "feature_flag_ativa": feature_flag_ativa,
        "historico_utilizado": None,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
        "detalhes": detalhes or {},
    }


def _sanitizar_json(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {str(k): _sanitizar_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_sanitizar_json(x) for x in obj]
    if isinstance(obj, Decimal):
        return str(obj)
    return obj


def _garantir_telemetria(app: FastAPI) -> Dict[str, Any]:
    with _LOCK_PROMOCAO:
        tel = getattr(app.state, "lotofacil_modo4_telemetria", None)
        if tel is None:
            tel = {
                "total_requisicoes_gerar": 0,
                "total_sucesso_gerar": 0,
                "total_bloqueios_feature_flag": 0,
                "total_bloqueios_integridade": 0,
                "total_bloqueios_politica_experimental": 0,
                "total_erros_validacao": 0,
                "total_erros_internos": 0,
                "total_requisicoes_avaliar": 0,
                "eventos": deque(maxlen=100),
            }
            app.state.lotofacil_modo4_telemetria = tel
        return tel


def _registrar_evento_telemetria(
    app: FastAPI,
    *,
    contador: Optional[str],
    evento: str,
    detalhes: Optional[Dict[str, Any]] = None,
) -> None:
    tel = _garantir_telemetria(app)
    with _LOCK_PROMOCAO:
        if contador is not None and contador in tel:
            tel[contador] = int(tel[contador]) + 1
        eventos: Deque[Dict[str, Any]] = tel["eventos"]
        eventos.append(
            {
                "timestamp_utc": datetime.now(timezone.utc).isoformat(),
                "evento": evento,
                "detalhes": detalhes or {},
            }
        )


def _obter_config_app(app: Optional[FastAPI]) -> ConfigProducaoLotofacilModo4:
    if app is None:
        return ConfigProducaoLotofacilModo4()
    with _LOCK_PROMOCAO:
        cfg = getattr(app.state, "config_lotofacil_modo4", None)
        if isinstance(cfg, ConfigProducaoLotofacilModo4):
            return cfg
        if cfg is not None:
            return ConfigProducaoLotofacilModo4(
                lotofacil_modo4_ativo=bool(getattr(cfg, "lotofacil_modo4_ativo", False)),
                politica_micro_padrao=str(getattr(cfg, "politica_micro", POLITICA_MICRO_PRODUCAO_PADRAO)),
                permitir_experimental_2j=bool(getattr(cfg, "permitir_experimental_2j", False)),
                inicializacao_mista=INICIALIZACAO_MISTA_FIXA,
                verificar_integridade_na_requisicao=bool(
                    getattr(cfg, "verificar_integridade_na_requisicao", True)
                ),
                verificar_lotomania_selo=bool(getattr(cfg, "verificar_lotomania_selo", True)),
                exigir_manifesto_etapa5=bool(getattr(cfg, "exigir_manifesto_etapa5", True)),
                exigir_manifesto_promocao=bool(getattr(cfg, "exigir_manifesto_promocao", False)),
                validar_referencia_independente=bool(
                    getattr(cfg, "validar_referencia_independente", True)
                ),
                max_avaliacoes_teto=int(getattr(cfg, "max_avaliacoes_teto", 2000)),
                max_iteracoes_teto=int(getattr(cfg, "max_iteracoes_teto", 2000)),
                diretorio_base=getattr(cfg, "diretorio_base", None),
            )
        return ConfigProducaoLotofacilModo4()


def verificar_integridade_promocao(
    *,
    diretorio_base: Optional[str] = None,
    verificar_lotomania_selo: bool = True,
    exigir_manifesto_etapa5: bool = True,
    exigir_manifesto_promocao: bool = False,
    verificar_manifesto_promocao_se_presente: bool = True,
) -> Dict[str, Any]:
    """
    Verifica fail-closed toda a cadeia criptografica SHA-256 e Ed25519:
    - Etapas 1-3 (20 artefatos), Etapa 4 (4 artefatos), Etapa 5 (4 artefatos),
      bases CAIXA e selo Ed25519 da Lotomania MODO 4;
    - Manifesto de Promocao Controlada (`manifesto_promocao_controlada.json`),
      quando presente ou exigido.
    """
    base = os.path.abspath(diretorio_base or BASE_DIR_PADRAO)
    int_etapa5 = verificar_integridade_etapa5(
        diretorio_base=base,
        verificar_lotomania_selo=verificar_lotomania_selo,
        exigir_manifesto_etapa5=exigir_manifesto_etapa5,
        verificar_manifesto_se_presente=True,
    )

    divergencias_promocao: List[Dict[str, Any]] = []
    verificados_promocao = 0
    hashes_atuais: Dict[str, str] = {}
    for rel in ARQUIVOS_PRODUCAO_PROMOCAO:
        abs_p = os.path.join(base, rel.replace("/", os.sep))
        if os.path.isfile(abs_p):
            hashes_atuais[rel] = calcular_sha256_arquivo(abs_p)

    caminho_man = os.path.join(base, CAMINHO_MANIFESTO_PROMOCAO_REL.replace("/", os.sep))
    man_presente = os.path.isfile(caminho_man)

    if exigir_manifesto_promocao and not man_presente:
        divergencias_promocao.append(
            {
                "arquivo": CAMINHO_MANIFESTO_PROMOCAO_REL,
                "motivo": "manifesto_promocao_ausente",
                "esperado": "presente",
                "obtido": None,
            }
        )
    elif man_presente and (exigir_manifesto_promocao or verificar_manifesto_promocao_se_presente):
        try:
            with open(caminho_man, "r", encoding="utf-8") as f:
                dados_man = json.load(f)
            mapa_esp = dados_man.get("hashes_producao", {})
            if not isinstance(mapa_esp, dict) or not mapa_esp:
                divergencias_promocao.append(
                    {
                        "arquivo": CAMINHO_MANIFESTO_PROMOCAO_REL,
                        "motivo": "manifesto_promocao_sem_hashes",
                        "esperado": "hashes_producao nao vazio",
                        "obtido": type(mapa_esp).__name__,
                    }
                )
            else:
                for rel, sha_esp in mapa_esp.items():
                    abs_p = os.path.join(base, str(rel).replace("/", os.sep))
                    if not os.path.isfile(abs_p):
                        divergencias_promocao.append(
                            {
                                "arquivo": str(rel),
                                "motivo": "arquivo_ausente",
                                "esperado": sha_esp,
                                "obtido": None,
                            }
                        )
                        continue
                    sha_obt = calcular_sha256_arquivo(abs_p)
                    verificados_promocao += 1
                    if sha_obt != sha_esp:
                        divergencias_promocao.append(
                            {
                                "arquivo": str(rel),
                                "motivo": "sha256_divergente",
                                "esperado": sha_esp,
                                "obtido": sha_obt,
                            }
                        )
        except Exception as exc:
            divergencias_promocao.append(
                {
                    "arquivo": CAMINHO_MANIFESTO_PROMOCAO_REL,
                    "motivo": "manifesto_promocao_corrompido",
                    "esperado": "json_valido",
                    "obtido": f"{type(exc).__name__}: {exc}",
                }
            )

    historico_isolado = HISTORICO_GERACAO_ETAPA4 is None
    todas_divergencias = list(int_etapa5.get("divergencias", [])) + divergencias_promocao
    integro = bool(int_etapa5.get("integro", False) and len(divergencias_promocao) == 0 and historico_isolado)

    return {
        "integro": integro,
        "integro_etapas_1_a_5": bool(int_etapa5.get("integro", False)),
        "historico_geracao_none": historico_isolado,
        "verificados_etapas_1_2_3": int(int_etapa5.get("verificados_etapas_1_2_3", 0)),
        "verificados_etapa_4": int(int_etapa5.get("verificados_etapa_4", 0)),
        "verificados_bases_externas": int(int_etapa5.get("verificados_bases_externas", 0)),
        "selo_lotomania_valido": bool(int_etapa5.get("selo_lotomania_valido", False)),
        "erro_selo_lotomania": int_etapa5.get("erro_selo_lotomania"),
        "manifesto_etapa5_presente": bool(int_etapa5.get("manifesto_etapa5_presente", False)),
        "manifesto_promocao_presente": man_presente,
        "verificados_promocao": verificados_promocao,
        "hashes_atuais_producao": hashes_atuais,
        "divergencias": todas_divergencias,
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
    }


def garantir_integridade_promocao_ou_falhar(
    *,
    diretorio_base: Optional[str] = None,
    verificar_lotomania_selo: bool = True,
    exigir_manifesto_etapa5: bool = True,
    exigir_manifesto_promocao: bool = False,
    verificar_manifesto_promocao_se_presente: bool = True,
) -> Dict[str, Any]:
    """Valida toda a cadeia criptografica ou levanta excecao fail-closed."""
    res = verificar_integridade_promocao(
        diretorio_base=diretorio_base,
        verificar_lotomania_selo=verificar_lotomania_selo,
        exigir_manifesto_etapa5=exigir_manifesto_etapa5,
        exigir_manifesto_promocao=exigir_manifesto_promocao,
        verificar_manifesto_promocao_se_presente=verificar_manifesto_promocao_se_presente,
    )
    if not res["integro"]:
        raise IntegridadePromocaoLotofacilError(
            f"Falha de integridade LOTOFACIL MODO 4: {res['divergencias'][:3]}"
        )
    return res


def gerar_manifesto_promocao_controlada(
    *,
    diretorio_base: Optional[str] = None,
    salvar: bool = True,
) -> Dict[str, Any]:
    """
    Calcula e grava `auditoria/lotofacil_modo4/manifesto_promocao_controlada.json`
    selando os artefatos de producao apos integracao controlada.
    """
    base = os.path.abspath(diretorio_base or BASE_DIR_PADRAO)
    int_etapa5 = verificar_integridade_etapa5(
        diretorio_base=base,
        verificar_lotomania_selo=True,
        exigir_manifesto_etapa5=True,
        verificar_manifesto_se_presente=True,
    )
    if not int_etapa5["integro"]:
        raise IntegridadeLotofacilEtapa5Error(
            f"Impossivel selar promocao com divergencias nas Etapas 1-5: {int_etapa5['divergencias']}"
        )

    hashes_prod: Dict[str, str] = {}
    ausentes: List[str] = []
    for rel in ARQUIVOS_PRODUCAO_PROMOCAO:
        abs_p = os.path.join(base, rel.replace("/", os.sep))
        if not os.path.isfile(abs_p):
            ausentes.append(rel)
            continue
        hashes_prod[rel] = calcular_sha256_arquivo(abs_p)

    if ausentes:
        raise FileNotFoundError(
            f"Arquivos obrigatorios ausentes para selagem de promocao: {ausentes}"
        )

    manifesto = {
        "versao_promocao": VERSAO_PROMOCAO_LOTOFACIL_MODO4,
        "versao_motor": VERSAO_ARQUITETURA_ETAPA4,
        "identificacao_oficial": IDENTIFICACAO_OFICIAL_LOTOFACIL_MODO4,
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "feature_flag_padrao_producao": False,
        "politica_micro_padrao_producao": POLITICA_MICRO_PRODUCAO_PADRAO,
        "experimental_2j_habilitada_por_padrao": False,
        "inicializacao_mista_fixa": INICIALIZACAO_MISTA_FIXA,
        "etapas_1_a_5_verificadas": True,
        "verificados_etapas_1_2_3": int_etapa5["verificados_etapas_1_2_3"],
        "verificados_etapa_4": int_etapa5["verificados_etapa_4"],
        "selo_lotomania_valido": int_etapa5["selo_lotomania_valido"],
        "hashes_producao": hashes_prod,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }

    if salvar:
        caminho = os.path.join(base, CAMINHO_MANIFESTO_PROMOCAO_REL.replace("/", os.sep))
        os.makedirs(os.path.dirname(caminho), exist_ok=True)
        with open(caminho, "w", encoding="utf-8") as f:
            json.dump(manifesto, f, indent=2, ensure_ascii=False)

    return manifesto


def definir_feature_flag_lotofacil_modo4(
    app: FastAPI,
    *,
    ativo: bool,
    permitir_experimental_2j: Optional[bool] = None,
    motivo: str = "ajuste_runtime_controlado",
) -> Dict[str, Any]:
    """
    Alterna a feature flag em runtime de forma atomica e auditavel.
    Permite rollback imediato para `ativo=False` retornando HTTP 503 sem reiniciar.
    """
    if not isinstance(ativo, bool):
        raise ValueError("Parametro 'ativo' deve ser bool estrito.")
    if permitir_experimental_2j is not None and not isinstance(permitir_experimental_2j, bool):
        raise ValueError("Parametro 'permitir_experimental_2j' deve ser bool estrito.")

    with _LOCK_PROMOCAO:
        cfg_atual = _obter_config_app(app)
        novo_exp_2j = (
            cfg_atual.permitir_experimental_2j
            if permitir_experimental_2j is None
            else permitir_experimental_2j
        )
        cfg_nova = replace(
            cfg_atual,
            lotofacil_modo4_ativo=ativo,
            permitir_experimental_2j=novo_exp_2j,
        )
        app.state.config_lotofacil_modo4 = cfg_nova

    tipo_ev = "ATIVACAO_FEATURE_FLAG" if ativo else "ROLLBACK_FEATURE_FLAG"
    _registrar_evento_telemetria(
        app,
        contador=None,
        evento=tipo_ev,
        detalhes={
            "feature_flag_anterior": cfg_atual.lotofacil_modo4_ativo,
            "feature_flag_atual": cfg_nova.lotofacil_modo4_ativo,
            "permitir_experimental_2j": cfg_nova.permitir_experimental_2j,
            "motivo": motivo,
        },
    )
    return {
        "feature_flag_anterior": cfg_atual.lotofacil_modo4_ativo,
        "feature_flag_atual": cfg_nova.lotofacil_modo4_ativo,
        "politica_micro_padrao": cfg_nova.politica_micro_padrao,
        "permitir_experimental_2j": cfg_nova.permitir_experimental_2j,
        "inicializacao_mista": cfg_nova.inicializacao_mista,
        "motivo": motivo,
    }


def _avaliar_disponibilidade_producao(cfg: ConfigProducaoLotofacilModo4) -> Dict[str, Any]:
    integridade = verificar_integridade_promocao(
        diretorio_base=cfg.diretorio_base,
        verificar_lotomania_selo=cfg.verificar_lotomania_selo,
        exigir_manifesto_etapa5=cfg.exigir_manifesto_etapa5,
        exigir_manifesto_promocao=cfg.exigir_manifesto_promocao,
        verificar_manifesto_promocao_se_presente=True,
    )
    motivo: Optional[str] = None
    if cfg.verificar_integridade_na_requisicao and not integridade["integro"]:
        motivo = "falha_integridade_criptografica"
        status_str = "bloqueado_integridade"
    elif not cfg.lotofacil_modo4_ativo:
        motivo = "feature_flag_desativada"
        status_str = "desativado_por_feature_flag"
    else:
        status_str = "ativo"

    disponivel = bool(
        cfg.lotofacil_modo4_ativo
        and (not cfg.verificar_integridade_na_requisicao or integridade["integro"])
    )
    return {
        "versao_promocao": VERSAO_PROMOCAO_LOTOFACIL_MODO4,
        "versao_motor": VERSAO_ARQUITETURA_ETAPA4,
        "identificacao_oficial": IDENTIFICACAO_OFICIAL_LOTOFACIL_MODO4,
        "disponivel": disponivel,
        "feature_flag_ativa": cfg.lotofacil_modo4_ativo,
        "status": status_str,
        "motivo_indisponibilidade": motivo,
        "integridade_verificada": integridade["integro"],
        "integridade_etapas_1_a_5_valida": integridade["integro_etapas_1_a_5"],
        "verificados_etapas_1_2_3": integridade["verificados_etapas_1_2_3"],
        "verificados_etapa_4": integridade["verificados_etapa_4"],
        "selo_lotomania_valido": integridade["selo_lotomania_valido"],
        "manifesto_etapa5_presente": integridade["manifesto_etapa5_presente"],
        "manifesto_promocao_presente": integridade["manifesto_promocao_presente"],
        "politica_micro_padrao": cfg.politica_micro_padrao,
        "experimental_2j_habilitada": cfg.permitir_experimental_2j,
        "inicializacao_mista": cfg.inicializacao_mista,
        "historico_geracao": HISTORICO_GERACAO_ETAPA4,
        "fallback_permitido": False,
        "sha256_modulos_promocao": integridade["hashes_atuais_producao"],
        "divergencias_integridade": integridade["divergencias"],
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }


def obter_status_health_lotofacil_modo4(app: Optional[FastAPI] = None) -> Dict[str, Any]:
    """
    Snapshot seguro do estado da promocao controlada LOTOFACIL MODO 4 para `/health`.
    Nunca levanta excecao que possa interromper o endpoint `/health` principal.
    """
    try:
        cfg = _obter_config_app(app)
        return _avaliar_disponibilidade_producao(cfg)
    except Exception as exc:
        return {
            "versao_promocao": VERSAO_PROMOCAO_LOTOFACIL_MODO4,
            "versao_motor": VERSAO_ARQUITETURA_ETAPA4,
            "identificacao_oficial": IDENTIFICACAO_OFICIAL_LOTOFACIL_MODO4,
            "disponivel": False,
            "feature_flag_ativa": False,
            "status": "bloqueado_erro_interno",
            "motivo_indisponibilidade": f"erro_verificacao_saude: {type(exc).__name__}",
            "integridade_verificada": False,
            "politica_micro_padrao": POLITICA_MICRO_PRODUCAO_PADRAO,
            "experimental_2j_habilitada": False,
            "inicializacao_mista": INICIALIZACAO_MISTA_FIXA,
            "historico_geracao": None,
            "fallback_permitido": False,
            "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
        }


def _verificar_acesso_e_integridade_requisicao(
    request: Request,
    *,
    acao: str,
) -> Tuple[ConfigProducaoLotofacilModo4, Dict[str, Any]]:
    app = request.app
    cfg = _obter_config_app(app)
    if not cfg.lotofacil_modo4_ativo:
        _registrar_evento_telemetria(
            app,
            contador="total_bloqueios_feature_flag",
            evento=f"BLOQUEIO_FEATURE_FLAG_{acao.upper()}",
            detalhes={"feature_flag_ativa": False},
        )
        raise _FailClosedLotofacilModo4Exception(
            status_code=503,
            payload=_construir_erro_fail_closed(
                erro="LOTOFACIL_MODO4_DESATIVADO",
                mensagem=(
                    "LOTOFACIL MODO 4 temporariamente desativado por feature flag controlada "
                    "em producao (padrao OFF). Nenhum jogo foi gerado."
                ),
                motivo="feature_flag_desativada",
                feature_flag_ativa=False,
            ),
        )

    if cfg.verificar_integridade_na_requisicao:
        try:
            integridade = garantir_integridade_promocao_ou_falhar(
                diretorio_base=cfg.diretorio_base,
                verificar_lotomania_selo=cfg.verificar_lotomania_selo,
                exigir_manifesto_etapa5=cfg.exigir_manifesto_etapa5,
                exigir_manifesto_promocao=cfg.exigir_manifesto_promocao,
                verificar_manifesto_promocao_se_presente=True,
            )
        except IntegridadePromocaoLotofacilError as exc:
            _registrar_evento_telemetria(
                app,
                contador="total_bloqueios_integridade",
                evento=f"BLOQUEIO_INTEGRIDADE_{acao.upper()}",
                detalhes={"erro": str(exc)},
            )
            raise _FailClosedLotofacilModo4Exception(
                status_code=503,
                payload=_construir_erro_fail_closed(
                    erro="FALHA_INTEGRIDADE_LOTOFACIL_MODO4",
                    mensagem=(
                        "Verificacao criptografica SHA-256/Ed25519 falhou (regime fail-closed). "
                        "Nenhum jogo foi gerado."
                    ),
                    motivo="integridade_violada",
                    feature_flag_ativa=cfg.lotofacil_modo4_ativo,
                    detalhes={"erro_integridade": str(exc)},
                ),
            ) from exc
    else:
        integridade = {"integro": None, "verificacao_desabilitada": True}
    return cfg, integridade


router_lotofacil_modo4 = APIRouter(
    prefix="/api/v1/lotofacil-modo4",
    tags=["Lotofacil MODO 4"],
)


@router_lotofacil_modo4.get("/status")
def endpoint_lotofacil_modo4_status(request: Request) -> Dict[str, Any]:
    """Retorna telemetria, feature flag, politicas configuradas e integridade."""
    app = request.app
    status_disp = obter_status_health_lotofacil_modo4(app)
    tel = _garantir_telemetria(app)
    with _LOCK_PROMOCAO:
        snapshot_tel = {
            "total_requisicoes_gerar": tel["total_requisicoes_gerar"],
            "total_sucesso_gerar": tel["total_sucesso_gerar"],
            "total_bloqueios_feature_flag": tel["total_bloqueios_feature_flag"],
            "total_bloqueios_integridade": tel["total_bloqueios_integridade"],
            "total_bloqueios_politica_experimental": tel["total_bloqueios_politica_experimental"],
            "total_erros_validacao": tel["total_erros_validacao"],
            "total_erros_internos": tel["total_erros_internos"],
            "total_requisicoes_avaliar": tel["total_requisicoes_avaliar"],
            "ultimos_eventos": list(tel["eventos"])[-10:],
        }
    return {
        **status_disp,
        "telemetria": snapshot_tel,
        "regimes_caixa": [
            integrar_configuracao_caixa_etapa1("concurso_regular"),
            integrar_configuracao_caixa_etapa1("concurso_final_zero"),
            integrar_configuracao_caixa_etapa1("lotofacil_independencia"),
        ],
    }


@router_lotofacil_modo4.post("/gerar")
def endpoint_lotofacil_modo4_gerar(
    request: Request,
    req: LotofacilModo4ProducaoGerarRequest,
) -> Dict[str, Any]:
    """
    Gera carteira otimizada LOTOFACIL MODO 4 exclusivamente quando a feature flag
    estiver explicitamente ativa e toda a cadeia SHA-256/Ed25519 estiver integra.
    """
    app = request.app
    _registrar_evento_telemetria(
        app,
        contador="total_requisicoes_gerar",
        evento="REQUISICAO_GERAR",
        detalhes={
            "quantidade_jogos": req.quantidade_jogos,
            "politica_solicitada": req.politica_micro,
            "tamanho_aposta": req.tamanho_aposta,
        },
    )

    cfg, integridade = _verificar_acesso_e_integridade_requisicao(request, acao="gerar")

    politica_efetiva = req.politica_micro if req.politica_micro is not None else cfg.politica_micro_padrao
    if politica_efetiva == "experimental_2J" and not cfg.permitir_experimental_2j:
        _registrar_evento_telemetria(
            app,
            contador="total_bloqueios_politica_experimental",
            evento="BLOQUEIO_EXPERIMENTAL_2J",
            detalhes={"politica_solicitada": politica_efetiva},
        )
        raise _FailClosedLotofacilModo4Exception(
            status_code=422,
            payload=_construir_erro_fail_closed(
                erro="POLITICA_EXPERIMENTAL_DESABILITADA",
                mensagem=(
                    "A politica micro 'experimental_2J' esta desabilitada por padrao em producao "
                    "(padrao oficial: 'conservadora_3J'). Nenhum jogo foi gerado."
                ),
                motivo="politica_experimental_desabilitada",
                feature_flag_ativa=cfg.lotofacil_modo4_ativo,
            ),
        )

    if req.max_avaliacoes > cfg.max_avaliacoes_teto:
        _registrar_evento_telemetria(
            app,
            contador="total_erros_validacao",
            evento="ERRO_TETO_AVALIACOES",
            detalhes={"max_avaliacoes": req.max_avaliacoes, "teto": cfg.max_avaliacoes_teto},
        )
        raise _FailClosedLotofacilModo4Exception(
            status_code=422,
            payload=_construir_erro_fail_closed(
                erro="ORCAMENTO_EXCEDE_TETO_PRODUCAO",
                mensagem=f"max_avaliacoes={req.max_avaliacoes} excede teto {cfg.max_avaliacoes_teto}.",
                motivo="teto_computacional",
                feature_flag_ativa=cfg.lotofacil_modo4_ativo,
            ),
        )
    if req.max_iteracoes > cfg.max_iteracoes_teto:
        _registrar_evento_telemetria(
            app,
            contador="total_erros_validacao",
            evento="ERRO_TETO_ITERACOES",
            detalhes={"max_iteracoes": req.max_iteracoes, "teto": cfg.max_iteracoes_teto},
        )
        raise _FailClosedLotofacilModo4Exception(
            status_code=422,
            payload=_construir_erro_fail_closed(
                erro="ITERACOES_EXCEDEM_TETO_PRODUCAO",
                mensagem=f"max_iteracoes={req.max_iteracoes} excede teto {cfg.max_iteracoes_teto}.",
                motivo="teto_computacional",
                feature_flag_ativa=cfg.lotofacil_modo4_ativo,
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
            politica_micro=politica_efetiva,
            inicializacao_mista=INICIALIZACAO_MISTA_FIXA,
            validar_referencia_independente=cfg.validar_referencia_independente,
        )
    except ErroValidacaoLotofacilError as exc:
        _registrar_evento_telemetria(
            app,
            contador="total_erros_validacao",
            evento="ERRO_VALIDACAO_COMBINATORIA",
            detalhes={"erro": str(exc)},
        )
        raise _FailClosedLotofacilModo4Exception(
            status_code=422,
            payload=_construir_erro_fail_closed(
                erro="PARAMETRO_INVALIDO_LOTOFACIL",
                mensagem=f"Restricao combinatoria ou orcamentaria invalida: {exc}",
                motivo="validacao_combinatoria",
                feature_flag_ativa=cfg.lotofacil_modo4_ativo,
            ),
        ) from exc
    except Exception as exc:
        _registrar_evento_telemetria(
            app,
            contador="total_erros_internos",
            evento="ERRO_INTERNO_GERACAO",
            detalhes={"tipo": type(exc).__name__},
        )
        raise _FailClosedLotofacilModo4Exception(
            status_code=500,
            payload=_construir_erro_fail_closed(
                erro="ERRO_INTERNO_LOTOFACIL_MODO4",
                mensagem=(
                    "Falha interna na geracao LOTOFACIL MODO 4 (sem fallback). "
                    f"Detalhe: {type(exc).__name__}"
                ),
                motivo="erro_interno_fail_closed",
                feature_flag_ativa=cfg.lotofacil_modo4_ativo,
            ),
        ) from exc

    esp = res["especificacao"]
    jogos = res.get("jogos", [])
    tamanhos_esp = list(esp["tamanhos_jogos"])
    if len(jogos) != len(tamanhos_esp) or len({tuple(j) for j in jogos}) != len(jogos):
        _registrar_evento_telemetria(
            app,
            contador="total_erros_internos",
            evento="ERRO_POS_CONDICAO",
            detalhes={"qtd_esperada": len(tamanhos_esp), "qtd_obtida": len(jogos)},
        )
        raise _FailClosedLotofacilModo4Exception(
            status_code=500,
            payload=_construir_erro_fail_closed(
                erro="POS_CONDICAO_INCONSISTENTE",
                mensagem="Carteira retornada falhou na verificacao estrita de pos-condicao.",
                motivo="falha_pos_condicao",
                feature_flag_ativa=cfg.lotofacil_modo4_ativo,
            ),
        )

    hash_carteira = calcular_hash_carteira_lotofacil(jogos)
    _registrar_evento_telemetria(
        app,
        contador="total_sucesso_gerar",
        evento="SUCESSO_GERAR",
        detalhes={
            "quantidade_jogos": len(jogos),
            "politica_micro": politica_efetiva,
            "algoritmo_utilizado": res.get("algoritmo_utilizado"),
            "hash_carteira_sha256": hash_carteira[:16],
        },
    )

    resposta = {
        **res,
        "sucesso": True,
        "fallback_executado": False,
        "historico_utilizado": HISTORICO_GERACAO_ETAPA4,
        "quantidade_entregue": len(jogos),
        "hash_carteira_sha256": hash_carteira,
        "promocao_controlada": {
            "versao_promocao": VERSAO_PROMOCAO_LOTOFACIL_MODO4,
            "feature_flag_ativa": cfg.lotofacil_modo4_ativo,
            "politica_micro_padrao_producao": POLITICA_MICRO_PRODUCAO_PADRAO,
            "politica_micro_utilizada": politica_efetiva,
            "experimental_2j_habilitada": cfg.permitir_experimental_2j,
            "experimental_2j_utilizada": politica_efetiva == "experimental_2J",
            "inicializacao_mista": INICIALIZACAO_MISTA_FIXA,
            "integridade": integridade,
        },
    }
    return _sanitizar_json(resposta)


@router_lotofacil_modo4.post("/avaliar")
def endpoint_lotofacil_modo4_avaliar(
    request: Request,
    req: LotofacilModo4ProducaoAvaliarRequest,
) -> Dict[str, Any]:
    """Audita matematicamente uma carteira fornecida contra a referencia AST."""
    app = request.app
    _registrar_evento_telemetria(
        app,
        contador="total_requisicoes_avaliar",
        evento="REQUISICAO_AVALIAR",
        detalhes={"quantidade_jogos": len(req.carteira)},
    )
    cfg, integridade = _verificar_acesso_e_integridade_requisicao(request, acao="avaliar")

    pool_efetivo = list(range(1, 26)) if req.pool is None else list(req.pool)
    try:
        conf = auditar_conformidade_etapa4_ref(
            req.carteira,
            pool=pool_efetivo,
            fixas=req.fixas,
            bloqueadas=req.bloqueadas,
            modo_fixas=req.modo_fixas,
            tamanhos_esperados=[len(j) for j in req.carteira],
        )
        if not conf["conforme"]:
            raise _FailClosedLotofacilModo4Exception(
                status_code=422,
                payload=_construir_erro_fail_closed(
                    erro="CARTEIRA_NAO_CONFORME",
                    mensagem=f"Carteira fornecida viola regras da Lotofacil: {conf['violacoes']}",
                    motivo="violacao_conformidade",
                    feature_flag_ativa=cfg.lotofacil_modo4_ativo,
                ),
            )
        av_e2 = avaliar_carteira_etapa2(
            req.carteira,
            pool=pool_efetivo,
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
    except _FailClosedLotofacilModo4Exception:
        raise
    except Exception as exc:
        raise _FailClosedLotofacilModo4Exception(
            status_code=422,
            payload=_construir_erro_fail_closed(
                erro="ERRO_AVALIACAO_LOTOFACIL_MODO4",
                mensagem=f"Nao foi possivel avaliar a carteira fornecida: {exc}",
                motivo="erro_avaliacao",
                feature_flag_ativa=cfg.lotofacil_modo4_ativo,
            ),
        ) from exc

    diff_F = abs(float(av_e2["funcao_objetivo_F"]) - float(av_ref["funcao_objetivo_F"]))
    max_diff_comp = max(
        abs(float(av_e2["componentes"][k]) - float(av_ref["componentes"][k]))
        for k in NOMES_COMPONENTES
    )
    if diff_F > 1e-12 or max_diff_comp > 1e-12:
        raise _FailClosedLotofacilModo4Exception(
            status_code=500,
            payload=_construir_erro_fail_closed(
                erro="DIVERGENCIA_REFERENCIA_INDEPENDENTE",
                mensagem="Divergencia numerica > 1e-12 entre motor principal e referencia.",
                motivo="divergencia_numerica",
                feature_flag_ativa=cfg.lotofacil_modo4_ativo,
                detalhes={"diff_F": diff_F, "max_diff_comp": max_diff_comp},
            ),
        )

    return _sanitizar_json(
        {
            "sucesso": True,
            "fallback_executado": False,
            "historico_utilizado": None,
            "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
            "hash_carteira_sha256": calcular_hash_carteira_lotofacil(req.carteira),
            "avaliacao_etapa2": av_e2,
            "distincao_seis_grandezas_probabilisticas": av_ref[
                "distincao_seis_grandezas_probabilisticas"
            ],
            "auditoria_referencia_independente": {
                "divergencia_F": diff_F,
                "max_divergencia_componentes": max_diff_comp,
                "tolerancia": 1e-12,
                "conformidade": conf,
            },
            "promocao_controlada": {
                "versao_promocao": VERSAO_PROMOCAO_LOTOFACIL_MODO4,
                "feature_flag_ativa": cfg.lotofacil_modo4_ativo,
                "integridade": integridade,
            },
        }
    )


def registrar_lotofacil_modo4_na_api(
    app: FastAPI,
    *,
    config: Optional[ConfigProducaoLotofacilModo4] = None,
) -> ConfigProducaoLotofacilModo4:
    """
    Registra o router LOTOFACIL MODO 4 e o tratamento fail-closed de validacao
    na instancia FastAPI principal com `lotofacil_modo4_ativo = False` por padrao.
    """
    cfg = config if config is not None else carregar_config_producao_de_env(padrao_ativo=False)
    with _LOCK_PROMOCAO:
        app.state.config_lotofacil_modo4 = cfg
        _garantir_telemetria(app)

    rotas_existentes = {getattr(r, "path", "") for r in app.routes}
    if "/api/v1/lotofacil-modo4/gerar" not in rotas_existentes:
        app.include_router(router_lotofacil_modo4)

    if not getattr(app.state, "_lotofacil_modo4_handler_registrado", False):

        @app.exception_handler(_FailClosedLotofacilModo4Exception)
        async def _tratar_fail_closed_lotofacil_modo4(
            request: Request,
            exc: _FailClosedLotofacilModo4Exception,
        ) -> JSONResponse:
            payload = _sanitizar_json(exc.payload)
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": payload, **payload},
            )

        @app.exception_handler(RequestValidationError)
        async def _tratar_validacao_lotofacil_modo4(
            request: Request,
            exc: RequestValidationError,
        ) -> JSONResponse:
            if request.url.path.startswith("/api/v1/lotofacil-modo4"):
                cfg_atual = _obter_config_app(app)
                _registrar_evento_telemetria(
                    app,
                    contador="total_erros_validacao",
                    evento="ERRO_VALIDACAO_SCHEMA_HTTP_422",
                    detalhes={"path": request.url.path},
                )
                return JSONResponse(
                    status_code=422,
                    content={
                        "detail": _sanitizar_json(exc.errors()),
                        **_construir_erro_fail_closed(
                            erro="REQUISICAO_INVALIDA_LOTOFACIL_MODO4",
                            mensagem=(
                                "Parametros invalidos ou campo proibido informado. "
                                "Nenhum jogo foi gerado."
                            ),
                            motivo="validacao_schema_estrito",
                            feature_flag_ativa=cfg_atual.lotofacil_modo4_ativo,
                        ),
                    },
                )
            return await request_validation_exception_handler(request, exc)

        app.state._lotofacil_modo4_handler_registrado = True

    return cfg
