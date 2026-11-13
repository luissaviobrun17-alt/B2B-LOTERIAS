# -*- coding: utf-8 -*-
"""
PREPARACAO E RUNBOOK CONTROLADO DA FASE 3 - PROMOCAO EM PRODUCAO (LOTOFACIL MODO 4)
====================================================================================
Implementa a Preparacao Auditavel da Fase 3 (checklist executavel, snapshot
sanitizado por allowlist, conferencia dos 7 arquivos selados pre e pos reinicio,
teste controlado em etapas, monitoramento, rollback comprovado HTTP 503 com zero
jogos e maquina de contingencia).

REGRA DE GOVERNANCA:
  - A preparacao e estritamente somente-leitura e NAO altera nem reinicia a porta 8000.
  - A execucao da Fase 3 permanece bloqueada por padrao (codigo de saida 2) ate
    autorizacao humana expressa com parametro explicito de estado pos-rollback.
  - Nenhum dado fora da allowlist de ambiente pode ser gravado em evidencias.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import os
import re
import socket
import subprocess
import sys
import time
from typing import Any, Callable, Dict, List, Mapping, Optional, Protocol, Sequence, Tuple

from .etapa1_regras_oficiais import CLAUSULA_MATEMATICA_OBRIGATORIA
from .etapa2_funcao_objetivo import NOMES_COMPONENTES
from .etapa4_referencia_independente import (
    auditar_conformidade_etapa4_ref,
    avaliar_carteira_ref_etapa4,
)
from .homologacao_ativacao_runbook import (
    BASE_DIR,
    CONTROLES_ROTAS_LEGADAS,
    _calcular_sha256_arquivo,
    _calcular_sha256_json_canonico,
    _capturar_estado_producao_8000,
    _coletar_hashes_arquivos_legados,
    _sondar_http_cronometrado,
    _validar_contrato_resposta_legada,
    coletar_telemetria_hardware,
    medir_memoria_processo_windows,
)
from .promocao_producao import (
    ARQUIVOS_PRODUCAO_PROMOCAO,
    ENV_FEATURE_FLAG_LOTOFACIL_MODO4,
    ENV_PERMITIR_EXPERIMENTAL_2J,
    ENV_POLITICA_MICRO_PADRAO,
    INICIALIZACAO_MISTA_FIXA,
    POLITICA_MICRO_PRODUCAO_PADRAO,
    VERSAO_PROMOCAO_LOTOFACIL_MODO4,
    verificar_integridade_promocao,
)

DIR_FASE3_REL = os.path.join("auditoria", "lotofacil_modo4", "promocao_fase3")
DIR_FASE3_ABS = os.path.join(BASE_DIR, DIR_FASE3_REL)
CAMINHO_CONFIG_FASE3_JSON = os.path.join(DIR_FASE3_ABS, "config_promocao_fase3.json")
CAMINHO_RUNBOOK_FASE3_MD = os.path.join(DIR_FASE3_ABS, "RUNBOOK_PROMOCAO_FASE3.md")
CAMINHO_ATA_FASE2_JSON = os.path.join(
    BASE_DIR,
    "auditoria",
    "lotofacil_modo4",
    "homologacao_ativacao",
    "ata_homologacao_ativacao.json",
)
CAMINHO_ATA_FASE3_JSON = os.path.join(DIR_FASE3_ABS, "ata_promocao_fase3.json")
CAMINHO_EVIDENCIAS_FASE3_JSON = os.path.join(DIR_FASE3_ABS, "evidencias_promocao_fase3.json")
CAMINHO_DOSSIE_FASE3_MD = os.path.join(DIR_FASE3_ABS, "DOSSIE_PROMOCAO_FASE3.md")

ALLOWLIST_ENV_FASE3: Tuple[str, ...] = (
    ENV_FEATURE_FLAG_LOTOFACIL_MODO4,
    ENV_PERMITIR_EXPERIMENTAL_2J,
    ENV_POLITICA_MICRO_PADRAO,
)
MODOS_POS_ROLLBACK_VALIDOS: Tuple[str, ...] = (
    "encerrar_em_off_standby",
    "reativar_on_com_revalidacao",
)
MODO_POS_ROLLBACK_DESIGNADO = "encerrar_em_off_standby"
TOKEN_CONFIRMACAO_HUMANA_FASE3 = "AUTORIZADO_PRODUCAO_PORTA_8000"
_ESTADOS_ESCUTA_NETSTAT = {"LISTENING", "ESCUTANDO", "LISTEN"}


class ControladorProcessoProducao(Protocol):
    """Protocolo de ciclo de vida do processo HTTP alvo da Fase 3."""

    @property
    def base_url(self) -> str: ...

    def pid_atual(self) -> Optional[int]: ...

    def reiniciar_para(
        self,
        *,
        lotofacil_modo4_ativo: bool,
        permitir_experimental_2j: bool = False,
        politica_micro: str = POLITICA_MICRO_PRODUCAO_PADRAO,
    ) -> Dict[str, Any]: ...


def carregar_config_fase3(caminho: str = CAMINHO_CONFIG_FASE3_JSON) -> Dict[str, Any]:
    """Carrega a configuracao JSON da Preparacao da Fase 3."""
    with open(caminho, "r", encoding="utf-8") as f:
        return json.load(f)


def sanitizar_variaveis_ambiente_snapshot(
    environ_map: Optional[Mapping[str, str]] = None,
    allowlist: Sequence[str] = ALLOWLIST_ENV_FASE3,
) -> Dict[str, Any]:
    """
    Extrai exclusivamente as 3 variaveis existentes em os.environ declaradas na allowlist.
    Nunca inclui nomes ou valores de variaveis externas ou segredos do SO.
    Registra separadamente o quarto parametro de governanca (inicializacao_mista),
    que nao possui variavel de ambiente e decorre de constante interna imutavel.
    """
    fonte = os.environ if environ_map is None else environ_map
    chaves_permitidas = tuple(allowlist)
    permitidas_set = set(chaves_permitidas)
    variaveis: Dict[str, str] = {}
    for chave in chaves_permitidas:
        if chave in fonte:
            variaveis[chave] = str(fonte[chave])
        else:
            variaveis[chave] = "NAO_DEFINIDA_USAR_PADRAO_SEGURO"

    omitidas = sum(1 for k in fonte.keys() if k not in permitidas_set)
    return {
        "variaveis_permitidas": variaveis,
        "allowlist_aplicada": list(chaves_permitidas),
        "configuracao_interna_imutavel": {
            "inicializacao_mista": {
                "valor": INICIALIZACAO_MISTA_FIXA,
                "origem": "constante_interna_imutavel_codigo_selado",
                "referencia_codigo": "lotofacil_modo4/promocao_producao.py:INICIALIZACAO_MISTA_FIXA",
                "suporta_override_env": False,
                "observacao": "Nao ha quarta variavel de ambiente no servidor; apenas 3 chaves existem em os.environ.",
            }
        },
        "proibir_dump_ambiente_completo": True,
        "total_variaveis_omitidas_por_seguranca": int(omitidas),
    }


def _mapear_quatro_parametros_governanca(
    *,
    env_snap: Dict[str, Any],
    dados_status: Dict[str, Any],
    endpoint_alcancavel: bool,
) -> Dict[str, Any]:
    """
    Consolida os 4 parametros de governanca no snapshot, separando as 3 chaves
    de ambiente da constante interna imutavel inicializacao_mista e conferindo /status.
    """
    vars_env = env_snap["variaveis_permitidas"]
    const_int = env_snap["configuracao_interna_imutavel"]["inicializacao_mista"]
    valor_api_inic = dados_status.get("inicializacao_mista")
    return {
        "1_feature_flag_ativa": {
            "chave_env": ENV_FEATURE_FLAG_LOTOFACIL_MODO4,
            "origem": "variavel_de_ambiente_allowlist_e_endpoint_status",
            "valor_env": vars_env.get(ENV_FEATURE_FLAG_LOTOFACIL_MODO4),
            "valor_status_api": dados_status.get("feature_flag_ativa"),
        },
        "2_experimental_2j_habilitada": {
            "chave_env": ENV_PERMITIR_EXPERIMENTAL_2J,
            "origem": "variavel_de_ambiente_allowlist_e_endpoint_status",
            "valor_env": vars_env.get(ENV_PERMITIR_EXPERIMENTAL_2J),
            "valor_status_api": dados_status.get("experimental_2j_habilitada"),
        },
        "3_politica_micro_padrao": {
            "chave_env": ENV_POLITICA_MICRO_PADRAO,
            "origem": "variavel_de_ambiente_allowlist_e_endpoint_status",
            "valor_env": vars_env.get(ENV_POLITICA_MICRO_PADRAO),
            "valor_status_api": dados_status.get("politica_micro_padrao"),
        },
        "4_inicializacao_mista": {
            "chave_env": None,
            "origem": const_int["origem"],
            "referencia_codigo": const_int["referencia_codigo"],
            "suporta_override_env": False,
            "valor_codigo_selado": INICIALIZACAO_MISTA_FIXA,
            "valor_status_api": valor_api_inic,
            "conforme": (not endpoint_alcancavel) or (valor_api_inic == INICIALIZACAO_MISTA_FIXA),
        },
    }


def parsear_pid_netstat_tcp(saida_netstat: str, porta: int = 8000) -> Optional[int]:
    """Extrai o PID ouvinte TCP da porta alvo a partir da saida do `netstat -ano -p TCP`."""
    alvo_porta = str(int(porta))
    for linha in saida_netstat.splitlines():
        partes = linha.strip().split()
        if len(partes) < 5:
            continue
        if partes[0].upper() != "TCP":
            continue
        estado = partes[3].upper()
        if estado not in _ESTADOS_ESCUTA_NETSTAT:
            continue
        endereco_local = partes[1]
        if ":" not in endereco_local:
            continue
        porta_local = endereco_local.rsplit(":", 1)[1]
        if porta_local == alvo_porta and partes[4].isdigit():
            return int(partes[4])
    return None


def descobrir_pid_ouvinte_porta_windows(porta: int = 8000) -> Optional[int]:
    """Identifica de forma somente-leitura o PID que escuta a porta TCP local."""
    try:
        proc = subprocess.run(
            ["netstat", "-ano", "-p", "TCP"],
            capture_output=True,
            timeout=5,
        )
        if proc.returncode != 0 or not proc.stdout:
            return None
        texto = proc.stdout.decode("cp850", errors="replace")
        return parsear_pid_netstat_tcp(texto, porta=porta)
    except Exception:
        return None


def recalcular_hashes_7_arquivos_selados(
    diretorio_base: str = BASE_DIR,
    hashes_referencia: Optional[Mapping[str, str]] = None,
) -> Dict[str, Any]:
    """
    Recalcula os SHA-256 dos 7 arquivos selados da promocao controlada e valida
    a cadeia criptografica completa contra manifestos e snapshot anterior.
    """
    res_prom = verificar_integridade_promocao(
        diretorio_base=diretorio_base,
        verificar_lotomania_selo=True,
        exigir_manifesto_etapa5=True,
        exigir_manifesto_promocao=True,
        verificar_manifesto_promocao_se_presente=True,
    )
    hashes_atuais: Dict[str, Optional[str]] = {}
    divergencias_snapshot: List[Dict[str, Any]] = []

    for rel in ARQUIVOS_PRODUCAO_PROMOCAO:
        abs_p = os.path.join(os.path.abspath(diretorio_base), rel.replace("/", os.sep))
        sha_atual = _calcular_sha256_arquivo(abs_p) if os.path.isfile(abs_p) else None
        hashes_atuais[rel] = sha_atual
        if hashes_referencia is not None:
            sha_esp = hashes_referencia.get(rel)
            if sha_atual != sha_esp:
                divergencias_snapshot.append(
                    {
                        "arquivo": rel,
                        "motivo": "divergencia_contra_snapshot_anterior",
                        "esperado": sha_esp,
                        "obtido": sha_atual,
                    }
                )

    divergencias_manifesto = list(res_prom.get("divergencias", []))
    divergencias_totais = divergencias_manifesto + divergencias_snapshot
    integro = bool(
        res_prom.get("integro") is True
        and res_prom.get("selo_lotomania_valido") is True
        and len(divergencias_totais) == 0
        and all(isinstance(v, str) and len(v) == 64 for v in hashes_atuais.values())
    )
    return {
        "integro": integro,
        "verificados_promocao": len(ARQUIVOS_PRODUCAO_PROMOCAO),
        "selo_lotomania_valido": bool(res_prom.get("selo_lotomania_valido")),
        "manifesto_promocao_presente": bool(res_prom.get("manifesto_promocao_presente")),
        "hashes_atuais": hashes_atuais,
        "divergencias_manifesto": divergencias_manifesto,
        "divergencias_snapshot": divergencias_snapshot,
        "divergencias_totais": divergencias_totais,
    }


def validar_ordem_pos_rollback(pos_rollback_modo: Optional[str]) -> str:
    """Garante fail-closed que o estado apos o ensaio de rollback foi explicitamente escolhido."""
    if pos_rollback_modo not in MODOS_POS_ROLLBACK_VALIDOS:
        raise ValueError(
            "Parametro pos_rollback_modo obrigatorio e invalido; escolha explicitamente entre "
            f"{MODOS_POS_ROLLBACK_VALIDOS} (recebido: {pos_rollback_modo!r})."
        )
    return pos_rollback_modo


def planejar_acao_contingencia_fase3(
    *,
    processo_iniciou: bool,
    integridade_ok: bool,
    teste_controlado_ok: bool,
    monitoramento_ok: bool,
    rollback_ok: bool = True,
    detalhe_erro: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Decide deterministicamente a acao de contingencia da Fase 3:
    1. Divergencia nos 7 arquivos selados ou criptografia -> aborto fail-closed sem mascaramento.
    2. Falha operacional/funcional com selo integro -> aborto com restauracao imediata da porta 8000 em OFF.
    3. Todos os criterios aprovados -> prosseguir.
    """
    if not integridade_ok:
        return {
            "acao": "abortar_fail_closed_divergencia_selada",
            "abortar": True,
            "restaurar_8000_off": False,
            "mascaramento_permitido": False,
            "motivo": detalhe_erro or "divergencia_arquivo_selado_ou_criptografia",
        }
    if not processo_iniciou:
        return {
            "acao": "abortar_e_restaurar_porta_8000_off",
            "abortar": True,
            "restaurar_8000_off": True,
            "mascaramento_permitido": False,
            "motivo": detalhe_erro or "falha_subida_processo_porta_8000",
        }
    if not teste_controlado_ok:
        return {
            "acao": "abortar_e_restaurar_porta_8000_off",
            "abortar": True,
            "restaurar_8000_off": True,
            "mascaramento_permitido": False,
            "motivo": detalhe_erro or "falha_teste_controlado_lotofacil_modo4",
        }
    if not monitoramento_ok or not rollback_ok:
        return {
            "acao": "abortar_e_restaurar_porta_8000_off",
            "abortar": True,
            "restaurar_8000_off": True,
            "mascaramento_permitido": False,
            "motivo": detalhe_erro or "falha_monitoramento_ou_comprovacao_rollback",
        }
    return {
        "acao": "prosseguir",
        "abortar": False,
        "restaurar_8000_off": False,
        "mascaramento_permitido": False,
        "motivo": "ok",
    }


def _sondar_contratos_legados_e_lotomania(
    base_url: str,
    cfg_f3: Dict[str, Any],
) -> Dict[str, Any]:
    """Executa sondagem de contrato da Lotomania MODO 4 e dos 4 endpoints legados."""
    rotas_legadas = list(cfg_f3["endpoints_legados_controle"])
    pl_lm = {"quantidade_jogos": 5, "permitir_espelhos": True, "seed": 42, "trace": False}
    r_lm = _sondar_http_cronometrado(
        base_url, pl_lm, endpoint="/api/v1/lotomania-modo4/gerar", timeout_s=15.0
    )
    d_lm = r_lm.get("dados_brutos") or {}
    lm_ok = (
        r_lm["status_http"] == 200
        and d_lm.get("sucesso") is True
        and d_lm.get("historico_geracao") is None
        and isinstance(d_lm.get("hash_carteira_sha256_v2_canonico"), str)
        and isinstance(d_lm.get("jogos"), list)
        and len(d_lm.get("jogos", [])) == 5
    )

    resultados_legados: Dict[str, Dict[str, Any]] = {}
    legados_ok = True
    for ep in rotas_legadas:
        pl_leg = dict(CONTROLES_ROTAS_LEGADAS.get(ep, {}).get("payload") or {"quantidade_jogos": 3})
        resp = _sondar_http_cronometrado(base_url, pl_leg, endpoint=ep, timeout_s=15.0)
        dados = resp.get("dados_brutos") or {}
        ok_ep, motivo = (
            _validar_contrato_resposta_legada(ep, pl_leg, dados)
            if resp["status_http"] == 200
            else (False, f"http_{resp['status_http']}")
        )
        if not ok_ep:
            legados_ok = False
        resultados_legados[ep] = {
            "status_http": resp["status_http"],
            "latencia_s": resp["latencia_s"],
            "contrato_ok": bool(ok_ep),
            "motivo": motivo,
            "sha256_resposta": _calcular_sha256_json_canonico(dados) if resp["status_http"] == 200 else None,
        }

    return {
        "aprovado": bool(lm_ok and legados_ok),
        "lotomania_modo4": {
            "status_http": r_lm["status_http"],
            "latencia_s": r_lm["latencia_s"],
            "sucesso": bool(lm_ok),
            "hash_carteira_sha256_v2_canonico": d_lm.get("hash_carteira_sha256_v2_canonico"),
        },
        "legados": resultados_legados,
    }


def capturar_snapshot_producao_somente_leitura(
    porta: int = 8000,
    *,
    incluir_sondagem_endpoints: bool = False,
    environ_map: Optional[Mapping[str, str]] = None,
    diretorio_base: str = BASE_DIR,
    pid_forcado: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Captura snapshot completo antes do reinicio de forma estritamente passiva:
    PID, memoria Win32, versao, variaveis via allowlist, /health, /status e os
    7 SHA-256 selados, sem reiniciar ou mutar flags.
    """
    cfg_f3 = carregar_config_fase3()
    base_url = f"http://127.0.0.1:{int(porta)}"
    pid = pid_forcado if pid_forcado is not None else descobrir_pid_ouvinte_porta_windows(porta)
    mem_pid = None
    if pid is not None and pid > 0:
        try:
            mem_pid = medir_memoria_processo_windows(pid)
        except Exception as exc:
            mem_pid = {"erro": str(exc)}

    r_health = _sondar_http_cronometrado(base_url, endpoint="/health", metodo="GET", timeout_s=3.0)
    r_status = _sondar_http_cronometrado(
        base_url, endpoint="/api/v1/lotofacil-modo4/status", metodo="GET", timeout_s=3.0
    )
    estado_8000 = _capturar_estado_producao_8000(porta_prod=porta)
    ds = r_status.get("dados_brutos") if isinstance(r_status.get("dados_brutos"), dict) else {}
    dh = r_health.get("dados_brutos") if isinstance(r_health.get("dados_brutos"), dict) else {}
    integridade_7 = recalcular_hashes_7_arquivos_selados(diretorio_base=diretorio_base)
    hashes_legados_disco = _coletar_hashes_arquivos_legados()

    sondagem_ref = (
        _sondar_contratos_legados_e_lotomania(base_url, cfg_f3)
        if incluir_sondagem_endpoints and estado_8000.get("alcancavel")
        else None
    )
    env_snap = sanitizar_variaveis_ambiente_snapshot(environ_map=environ_map)
    quatro_parametros = _mapear_quatro_parametros_governanca(
        env_snap=env_snap,
        dados_status=ds,
        endpoint_alcancavel=bool(estado_8000.get("alcancavel")),
    )

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "modo_captura": "somente_leitura_sem_reinicio",
        "porta": int(porta),
        "pid_ouvinte": pid,
        "memoria_processo_mb": mem_pid,
        "alcancavel": bool(estado_8000.get("alcancavel")),
        "versao_promocao": ds.get("versao_promocao"),
        "versao_motor": ds.get("versao_motor"),
        "health_api_operacional": dh.get("api_operacional"),
        "estado_normalizado_sha256": estado_8000.get("sha256_estado_normalizado"),
        "feature_flag_ativa": ds.get("feature_flag_ativa"),
        "experimental_2j_habilitada": ds.get("experimental_2j_habilitada"),
        "politica_micro_padrao": ds.get("politica_micro_padrao"),
        "inicializacao_mista": ds.get("inicializacao_mista"),
        "telemetria_anterior": ds.get("telemetria"),
        "variaveis_ambiente": env_snap,
        "configuracao_interna_imutavel": env_snap["configuracao_interna_imutavel"],
        "quatro_parametros_governanca": quatro_parametros,
        "integridade_7_selados": integridade_7,
        "hashes_arquivos_legados_disco_count": len(hashes_legados_disco),
        "sha256_mapa_legados_disco": _calcular_sha256_json_canonico(hashes_legados_disco),
        "sondagem_referencia_endpoints": sondagem_ref,
    }


def _validar_contem_sem_travessao_e_clausula(caminho_md: str) -> None:
    with open(caminho_md, "r", encoding="utf-8") as f:
        conteudo = f.read()
    if "\u2014" in conteudo or "\u2013" in conteudo:
        raise ValueError(f"Arquivo {os.path.basename(caminho_md)} contem travessao proibido.")
    if CLAUSULA_MATEMATICA_OBRIGATORIA not in conteudo:
        raise ValueError(f"Clausula matematica obrigatoria ausente em {os.path.basename(caminho_md)}.")


def verificar_preparacao_fase3_somente_leitura(
    diretorio_base: str = BASE_DIR,
    *,
    caminho_config: str = CAMINHO_CONFIG_FASE3_JSON,
    caminho_runbook: str = CAMINHO_RUNBOOK_FASE3_MD,
    caminho_ata_fase2: str = CAMINHO_ATA_FASE2_JSON,
    dir_fase3: str = DIR_FASE3_ABS,
) -> Dict[str, Any]:
    """
    Confere passivamente todos os artefatos de Preparacao da Fase 3, pre-requisito
    GO da Fase 2 e integridade dos 7 arquivos selados, sem executar a Fase 3.
    """
    cfg_f3 = carregar_config_fase3(caminho_config)
    _validar_contem_sem_travessao_e_clausula(caminho_runbook)

    if not os.path.isfile(caminho_ata_fase2):
        raise FileNotFoundError(f"Ata da Fase 2 obrigatoria nao encontrada: {caminho_ata_fase2}")
    with open(caminho_ata_fase2, "r", encoding="utf-8") as fa:
        ata_f2 = json.load(fa)

    criterios_f2 = ata_f2.get("criterios", {})
    f2_go = bool(
        ata_f2.get("veredito") == "GO"
        and ata_f2.get("motivos_no_go") == []
        and all(bool(criterios_f2.get(f"frente_{i}_ok")) for i in range(1, 7))
    )
    param = cfg_f3["parametros_producao"]
    allow_cfg = cfg_f3["allowlist_variaveis_snapshot"]
    inic_cfg = allow_cfg.get("configuracao_interna_imutavel", {}).get("inicializacao_mista", {})
    defs_cfg = cfg_f3.get("tres_definicoes_operacionais", {})
    def2_cfg = defs_cfg.get("2_ordem_rollback_e_estado_final", {})
    quatro_esclarecidos = bool(
        tuple(allow_cfg["chaves_permitidas"]) == ALLOWLIST_ENV_FASE3
        and inic_cfg.get("valor") == INICIALIZACAO_MISTA_FIXA
        and inic_cfg.get("suporta_override_env") is False
        and bool(inic_cfg.get("origem"))
        and bool(inic_cfg.get("referencia_codigo"))
    )
    regras_f3_ok = bool(
        param["permitir_experimental_2j"] is False
        and param["politica_micro_homologada"] == POLITICA_MICRO_PRODUCAO_PADRAO
        and param["inicializacao_mista"] == INICIALIZACAO_MISTA_FIXA
        and allow_cfg["proibir_dump_ambiente_completo"] is True
        and quatro_esclarecidos
        and def2_cfg.get("modo_pos_rollback_designado") == MODO_POS_ROLLBACK_DESIGNADO
        and cfg_f3["clausula_matematica_obrigatoria"] == CLAUSULA_MATEMATICA_OBRIGATORIA
    )

    artefatos_execucao = (
        os.path.join(dir_fase3, "ata_promocao_fase3.json"),
        os.path.join(dir_fase3, "evidencias_promocao_fase3.json"),
        os.path.join(dir_fase3, "DOSSIE_PROMOCAO_FASE3.md"),
    )
    fase3_executada = any(os.path.exists(p) for p in artefatos_execucao)
    integridade_7 = recalcular_hashes_7_arquivos_selados(diretorio_base=diretorio_base)
    hw = coletar_telemetria_hardware()

    pronto = bool(f2_go and regras_f3_ok and integridade_7["integro"] and not fase3_executada)
    return {
        "fase": "FASE_3_PREPARACAO_AUDITAVEL_VERIFICADA",
        "fase3_executada": fase3_executada,
        "pronto_para_deliberacao": pronto,
        "ata_fase2_veredito": ata_f2.get("veredito"),
        "regras_governanca_fase3_ok": regras_f3_ok,
        "quatro_parametros_governanca_esclarecidos": quatro_esclarecidos,
        "modo_pos_rollback_designado": def2_cfg.get("modo_pos_rollback_designado"),
        "integridade_cadeia_selada": integridade_7["integro"],
        "hashes_7_selados": integridade_7["hashes_atuais"],
        "divergencias": integridade_7["divergencias_totais"],
        "hardware": hw,
    }


def _validar_autorizacao_fase3(
    *,
    autorizacao_explicita: bool,
    confirmacao_humana: Optional[str],
    pos_rollback_modo: Optional[str],
    permitir_experimental_2j: bool,
) -> str:
    if autorizacao_explicita is not True or confirmacao_humana != TOKEN_CONFIRMACAO_HUMANA_FASE3:
        raise PermissionError(
            "Execucao da Fase 3 bloqueada fail-closed: exige autorizacao_explicita=True e token de confirmacao humana."
        )
    if permitir_experimental_2j is not False:
        raise PermissionError("Politica experimental_2J permanece bloqueada na Fase 3 (deve ser False).")
    return validar_ordem_pos_rollback(pos_rollback_modo)


def _executar_teste_controlado_e_adicionais(
    base_url: str,
    cfg_f3: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Executa primeiro geracao pequena controlada (3 jogos) e somente apos validacao
    integral executa /avaliar e cenarios negativos HTTP 422.
    """
    ex3 = cfg_f3["cinco_exigencias_adicionais"]["3_teste_controlado"]
    tol = float(ex3["tolerancia_divergencia_ast_F"])
    pl_pequeno = dict(ex3["payload_inicial_pequeno"])

    r_peq = _sondar_http_cronometrado(base_url, pl_pequeno, endpoint="/api/v1/lotofacil-modo4/gerar", timeout_s=15.0)
    dp = r_peq.get("dados_brutos") if isinstance(r_peq.get("dados_brutos"), dict) else {}
    esp = dp.get("especificacao", {})
    jogos_p = dp.get("jogos", [])
    inicial_ok = False
    diff_F_peq = 999.0

    if r_peq["status_http"] == 200 and dp.get("sucesso") is True and len(jogos_p) == int(pl_pequeno["quantidade_jogos"]):
        av_ref = avaliar_carteira_ref_etapa4(
            jogos_p,
            pool=esp.get("pool"),
            fixas=esp.get("fixas", []),
            bloqueadas=esp.get("bloqueadas", []),
            modo_fixas=esp.get("modo_fixas", "todos_os_jogos"),
            pesos=esp.get("pesos"),
        )
        conf_ref = auditar_conformidade_etapa4_ref(
            jogos_p,
            pool=esp.get("pool"),
            fixas=esp.get("fixas", []),
            bloqueadas=esp.get("bloqueadas", []),
            modo_fixas=esp.get("modo_fixas", "todos_os_jogos"),
            tamanhos_esperados=esp.get("tamanhos_jogos"),
        )
        diff_F_peq = abs(float(dp.get("funcao_objetivo_F", -1.0)) - float(av_ref["funcao_objetivo_F"]))
        comp_ok = all(c in dp.get("componentes", {}) for c in NOMES_COMPONENTES)
        inicial_ok = bool(
            conf_ref["conforme"] is True
            and comp_ok
            and dp.get("historico_utilizado") is None
            and dp.get("fallback_executado") is False
            and dp.get("clausula_obrigatoria") == CLAUSULA_MATEMATICA_OBRIGATORIA
            and diff_F_peq <= tol
        )

    if not inicial_ok:
        return {
            "aprovado": False,
            "teste_pequeno_ok": False,
            "testes_adicionais_executados": False,
            "status_http_pequeno": r_peq["status_http"],
            "latencia_pequeno_s": r_peq["latencia_s"],
            "diff_F_pequeno": diff_F_peq,
        }

    r_av = _sondar_http_cronometrado(
        base_url,
        {
            "carteira": jogos_p,
            "pool": esp.get("pool"),
            "fixas": esp.get("fixas", []),
            "bloqueadas": esp.get("bloqueadas", []),
            "modo_fixas": esp.get("modo_fixas", "todos_os_jogos"),
        },
        endpoint="/api/v1/lotofacil-modo4/avaliar",
        timeout_s=15.0,
    )
    dav = r_av.get("dados_brutos") if isinstance(r_av.get("dados_brutos"), dict) else {}
    diff_av = float(dav.get("auditoria_referencia_independente", {}).get("divergencia_F", 999.0))
    avaliar_ok = bool(r_av["status_http"] == 200 and dav.get("sucesso") is True and diff_av <= tol)

    payloads_422 = {
        "experimental_2J": {"quantidade_jogos": 3, "semente": 42, "politica_micro": "experimental_2J"},
        "inicializacao_mista": {"quantidade_jogos": 3, "inicializacao_mista": "mista_equilibrada"},
        "historico_proibido": {"quantidade_jogos": 3, "historico": [[1, 2, 3]]},
    }
    negativos: Dict[str, Any] = {}
    neg_ok = True
    for nome, pl in payloads_422.items():
        rn = _sondar_http_cronometrado(base_url, pl, endpoint="/api/v1/lotofacil-modo4/gerar", timeout_s=10.0)
        negativos[nome] = {"status_http": rn["status_http"], "jogos": len(rn["jogos"])}
        if rn["status_http"] != 422 or len(rn["jogos"]) != 0 or rn["fallback_executado"] is not False:
            neg_ok = False

    return {
        "aprovado": bool(inicial_ok and avaliar_ok and neg_ok),
        "teste_pequeno_ok": True,
        "testes_adicionais_executados": True,
        "status_http_pequeno": r_peq["status_http"],
        "latencia_pequeno_s": r_peq["latencia_s"],
        "diff_F_pequeno": diff_F_peq,
        "hash_carteira_pequena": dp.get("hash_carteira_sha256"),
        "avaliar_ok": avaliar_ok,
        "diff_F_avaliar": diff_av,
        "negativos_422_ok": neg_ok,
        "negativos": negativos,
    }


def _validar_rollback_503_zero_jogos(base_url: str, cfg_f3: Dict[str, Any]) -> Dict[str, Any]:
    r_status = _sondar_http_cronometrado(base_url, endpoint="/api/v1/lotofacil-modo4/status", metodo="GET", timeout_s=5.0)
    ds = r_status.get("dados_brutos") if isinstance(r_status.get("dados_brutos"), dict) else {}
    r_gerar = _sondar_http_cronometrado(
        base_url, {"quantidade_jogos": 3, "semente": 42}, endpoint="/api/v1/lotofacil-modo4/gerar", timeout_s=5.0
    )
    r_av = _sondar_http_cronometrado(
        base_url, {"carteira": [list(range(1, 16))]}, endpoint="/api/v1/lotofacil-modo4/avaliar", timeout_s=5.0
    )
    legados_pos = _sondar_contratos_legados_e_lotomania(base_url, cfg_f3)
    aprovado = bool(
        r_status["status_http"] == 200
        and ds.get("disponivel") is False
        and ds.get("feature_flag_ativa") is False
        and r_gerar["status_http"] == 503
        and r_gerar["jogos"] == []
        and r_gerar["fallback_executado"] is False
        and r_av["status_http"] == 503
        and r_av["jogos"] == []
        and legados_pos["aprovado"] is True
    )
    return {
        "aprovado": aprovado,
        "status_disponivel": ds.get("disponivel"),
        "status_feature_flag": ds.get("feature_flag_ativa"),
        "gerar_http": r_gerar["status_http"],
        "gerar_jogos": len(r_gerar["jogos"]),
        "gerar_fallback": r_gerar["fallback_executado"],
        "avaliar_http": r_av["status_http"],
        "avaliar_jogos": len(r_av["jogos"]),
        "legados_e_lotomania_ok": legados_pos["aprovado"],
    }


def _monitorar_pos_ativacao(
    base_url: str,
    pid: Optional[int],
    cfg_f3: Dict[str, Any],
    teste_ctrl: Dict[str, Any],
) -> Dict[str, Any]:
    ex4 = cfg_f3["cinco_exigencias_adicionais"]["4_monitoramento"]
    r_status = _sondar_http_cronometrado(base_url, endpoint="/api/v1/lotofacil-modo4/status", metodo="GET", timeout_s=5.0)
    ds = r_status.get("dados_brutos") if isinstance(r_status.get("dados_brutos"), dict) else {}
    tel = ds.get("telemetria") or {}

    mem = None
    mem_ok = True
    if pid is not None and pid > 0:
        mem = medir_memoria_processo_windows(pid)
        mem_ok = float(mem["rss_pico_mb"]) <= float(ex4["max_rss_pico_mb"])

    telemetria_ok = bool(
        r_status["status_http"] == 200
        and ds.get("disponivel") is True
        and ds.get("feature_flag_ativa") is True
        and ds.get("experimental_2j_habilitada") is False
        and ds.get("politica_micro_padrao") == POLITICA_MICRO_PRODUCAO_PADRAO
        and ds.get("inicializacao_mista") == INICIALIZACAO_MISTA_FIXA
        and int(tel.get("total_requisicoes_gerar", 0)) >= 1
        and int(tel.get("total_sucesso_gerar", 0)) >= 1
        and int(tel.get("total_erros_internos", 0)) == 0
        and int(tel.get("total_requisicoes_avaliar", 0)) >= 1
    )
    lat_ok = float(teste_ctrl.get("latencia_pequeno_s", 999.0)) <= float(ex4["max_latencia_teste_controlado_s"])
    legados = _sondar_contratos_legados_e_lotomania(base_url, cfg_f3)
    aprovado = bool(mem_ok and telemetria_ok and lat_ok and legados["aprovado"])
    return {
        "aprovado": aprovado,
        "memoria_pid_mb": mem,
        "memoria_dentro_limite": mem_ok,
        "latencia_controlada_ok": lat_ok,
        "telemetria_coerente_ok": telemetria_ok,
        "telemetria": tel,
        "legados_e_lotomania": legados,
    }


def _construir_dossie_fase3_md(dados: Dict[str, Any]) -> str:
    ata = dados["ata_decisao"]
    linhas = [
        "# DOSSIE E ATA DA FASE 3 - PROMOCAO CONTROLADA EM PRODUCAO (LOTOFACIL MODO 4)",
        "",
        f"**Versao Avaliada:** `{dados['versao_avaliada']}`  ",
        f"**Data/Hora (UTC):** `{dados['executado_em_utc']}`  ",
        f"**Veredito:** `{ata['veredito']}` | **Abortada:** `{ata['abortada']}`  ",
        "",
        "## Clausula Matematica Obrigatoria",
        "",
        f"> {CLAUSULA_MATEMATICA_OBRIGATORIA}",
    ]
    return "\n".join(linhas) + "\n"


def _registrar_e_emitir_dossie_opcional(
    *,
    dados: Dict[str, Any],
    dir_saida: Optional[str],
) -> None:
    if dir_saida is None:
        return
    os.makedirs(dir_saida, exist_ok=True)
    with open(os.path.join(dir_saida, "evidencias_promocao_fase3.json"), "w", encoding="utf-8") as fe:
        json.dump(dados, fe, indent=2, ensure_ascii=False)
    with open(os.path.join(dir_saida, "ata_promocao_fase3.json"), "w", encoding="utf-8") as fa:
        json.dump(dados["ata_decisao"], fa, indent=2, ensure_ascii=False)
    with open(os.path.join(dir_saida, "DOSSIE_PROMOCAO_FASE3.md"), "w", encoding="utf-8") as fd:
        fd.write(_construir_dossie_fase3_md(dados))


def _finalizar_aborto_fase3(
    *,
    contingencia: Dict[str, Any],
    controlador: ControladorProcessoProducao,
    etapas: Dict[str, Any],
    cfg_f3: Dict[str, Any],
    dir_saida: Optional[str],
) -> Dict[str, Any]:
    restauracao_off = None
    if contingencia.get("restaurar_8000_off") is True:
        try:
            controlador.reiniciar_para(
                lotofacil_modo4_ativo=False,
                permitir_experimental_2j=False,
                politica_micro=POLITICA_MICRO_PRODUCAO_PADRAO,
            )
            restauracao_off = _validar_rollback_503_zero_jogos(controlador.base_url, cfg_f3)
        except Exception as exc:
            restauracao_off = {"aprovado": False, "erro": str(exc)}

    resultado = {
        "versao_runbook": cfg_f3["versao_runbook"],
        "versao_avaliada": VERSAO_PROMOCAO_LOTOFACIL_MODO4,
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "ata_decisao": {
            "veredito": "NO-GO",
            "abortada": True,
            "contingencia": contingencia,
            "restauracao_off": restauracao_off,
        },
        "etapas": etapas,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }
    _registrar_e_emitir_dossie_opcional(dados=resultado, dir_saida=dir_saida)
    return resultado


def executar_protocolo_fase3_controlado(
    *,
    controlador_processo: ControladorProcessoProducao,
    autorizacao_explicita: bool = False,
    confirmacao_humana: Optional[str] = None,
    pos_rollback_modo: Optional[str] = None,
    permitir_experimental_2j: bool = False,
    diretorio_base: str = BASE_DIR,
    dir_saida: Optional[str] = DIR_FASE3_ABS,
    recalculo_integridade_fn: Optional[Callable[..., Dict[str, Any]]] = None,
    porta_alvo: int = 8000,
) -> Dict[str, Any]:
    """
    Executa as 6 etapas ordenadas da Fase 3 com trava dupla de autorizacao,
    comparacao de hashes antes/depois e contingencia fail-closed.
    """
    modo_final = _validar_autorizacao_fase3(
        autorizacao_explicita=autorizacao_explicita,
        confirmacao_humana=confirmacao_humana,
        pos_rollback_modo=pos_rollback_modo,
        permitir_experimental_2j=permitir_experimental_2j,
    )
    cfg_f3 = carregar_config_fase3()
    calc_hashes = recalculo_integridade_fn or recalcular_hashes_7_arquivos_selados
    etapas: Dict[str, Any] = {}

    # Etapa 1: Snapshot anterior
    snap_antes = capturar_snapshot_producao_somente_leitura(
        porta=porta_alvo,
        incluir_sondagem_endpoints=True,
        diretorio_base=diretorio_base,
        pid_forcado=controlador_processo.pid_atual(),
    )
    etapas["etapa_1_snapshot_anterior"] = snap_antes
    hashes_ref = snap_antes["integridade_7_selados"]["hashes_atuais"]

    # Etapa 2: Reinicio controlado ON + Integridade posterior dos 7 selados
    try:
        info_on = controlador_processo.reiniciar_para(
            lotofacil_modo4_ativo=True,
            permitir_experimental_2j=False,
            politica_micro=POLITICA_MICRO_PRODUCAO_PADRAO,
        )
        processo_on_ok = True
        erro_on = None
    except Exception as exc:
        info_on = {}
        processo_on_ok = False
        erro_on = str(exc)

    int_pos = calc_hashes(diretorio_base=diretorio_base, hashes_referencia=hashes_ref)
    etapas["etapa_2_reinicio_on_e_integridade"] = {
        "processo_iniciou": processo_on_ok,
        "info_processo": info_on,
        "erro": erro_on,
        "integridade_7_selados_pos": int_pos,
    }
    cont_2 = planejar_acao_contingencia_fase3(
        processo_iniciou=processo_on_ok,
        integridade_ok=bool(int_pos.get("integro")),
        teste_controlado_ok=True,
        monitoramento_ok=True,
        detalhe_erro=erro_on,
    )
    if cont_2["abortar"]:
        return _finalizar_aborto_fase3(
            contingencia=cont_2, controlador=controlador_processo, etapas=etapas, cfg_f3=cfg_f3, dir_saida=dir_saida
        )

    # Etapa 3: Teste pequeno controlado antes de testes adicionais
    teste_ctrl = _executar_teste_controlado_e_adicionais(controlador_processo.base_url, cfg_f3)
    etapas["etapa_3_teste_controlado"] = teste_ctrl
    cont_3 = planejar_acao_contingencia_fase3(
        processo_iniciou=True,
        integridade_ok=True,
        teste_controlado_ok=bool(teste_ctrl["aprovado"]),
        monitoramento_ok=True,
    )
    if cont_3["abortar"]:
        return _finalizar_aborto_fase3(
            contingencia=cont_3, controlador=controlador_processo, etapas=etapas, cfg_f3=cfg_f3, dir_saida=dir_saida
        )

    # Etapa 4: Monitoramento de erros, latencia, memoria, telemetria e legados
    monit = _monitorar_pos_ativacao(
        controlador_processo.base_url,
        controlador_processo.pid_atual(),
        cfg_f3,
        teste_ctrl,
    )
    etapas["etapa_4_monitoramento"] = monit
    cont_4 = planejar_acao_contingencia_fase3(
        processo_iniciou=True,
        integridade_ok=True,
        teste_controlado_ok=True,
        monitoramento_ok=bool(monit["aprovado"]),
    )
    if cont_4["abortar"]:
        return _finalizar_aborto_fase3(
            contingencia=cont_4, controlador=controlador_processo, etapas=etapas, cfg_f3=cfg_f3, dir_saida=dir_saida
        )

    # Etapa 5: Rollback comprovado para OFF (HTTP 503 + zero jogos)
    controlador_processo.reiniciar_para(
        lotofacil_modo4_ativo=False,
        permitir_experimental_2j=False,
        politica_micro=POLITICA_MICRO_PRODUCAO_PADRAO,
    )
    rb_res = _validar_rollback_503_zero_jogos(controlador_processo.base_url, cfg_f3)
    etapas["etapa_5_rollback_comprovado"] = rb_res
    cont_5 = planejar_acao_contingencia_fase3(
        processo_iniciou=True,
        integridade_ok=True,
        teste_controlado_ok=True,
        monitoramento_ok=True,
        rollback_ok=bool(rb_res["aprovado"]),
    )
    if cont_5["abortar"]:
        return _finalizar_aborto_fase3(
            contingencia=cont_5, controlador=controlador_processo, etapas=etapas, cfg_f3=cfg_f3, dir_saida=dir_saida
        )

    # Etapa 6: Estado pos-rollback explicito
    if modo_final == "encerrar_em_off_standby":
        pos_final = {
            "modo_aplicado": modo_final,
            "estado_final_ativo": False,
            "verificacao_ok": bool(rb_res["aprovado"]),
        }
    else:
        controlador_processo.reiniciar_para(
            lotofacil_modo4_ativo=True,
            permitir_experimental_2j=False,
            politica_micro=POLITICA_MICRO_PRODUCAO_PADRAO,
        )
        int_final = calc_hashes(diretorio_base=diretorio_base, hashes_referencia=hashes_ref)
        teste_pos = _executar_teste_controlado_e_adicionais(controlador_processo.base_url, cfg_f3)
        monit_final = _monitorar_pos_ativacao(
            controlador_processo.base_url,
            controlador_processo.pid_atual(),
            cfg_f3,
            teste_pos,
        )
        ok_reat = bool(int_final["integro"] and teste_pos["aprovado"] and monit_final["aprovado"])
        if not ok_reat:
            cont_6 = planejar_acao_contingencia_fase3(
                processo_iniciou=True,
                integridade_ok=bool(int_final["integro"]),
                teste_controlado_ok=bool(teste_pos["aprovado"]),
                monitoramento_ok=bool(monit_final["aprovado"]),
            )
            return _finalizar_aborto_fase3(
                contingencia=cont_6,
                controlador=controlador_processo,
                etapas=etapas,
                cfg_f3=cfg_f3,
                dir_saida=dir_saida,
            )
        pos_final = {
            "modo_aplicado": modo_final,
            "estado_final_ativo": True,
            "integridade_final_ok": int_final["integro"],
            "verificacao_ok": ok_reat,
        }

    etapas["etapa_6_pos_rollback_final"] = pos_final
    resultado = {
        "versao_runbook": cfg_f3["versao_runbook"],
        "versao_avaliada": VERSAO_PROMOCAO_LOTOFACIL_MODO4,
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "ata_decisao": {
            "veredito": "GO",
            "abortada": False,
            "pos_rollback_modo": modo_final,
            "estado_final_ativo": pos_final["estado_final_ativo"],
        },
        "etapas": etapas,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }
    _registrar_e_emitir_dossie_opcional(dados=resultado, dir_saida=dir_saida)
    return resultado


class _ControladorProcessoPortaProducao:
    """Controlador concreto do processo Uvicorn em 127.0.0.1:8000 (usado somente na Fase 3 autorizada)."""

    def __init__(self, porta: int = 8000) -> None:
        self.porta = int(porta)
        self.base_url = f"http://127.0.0.1:{self.porta}"
        self._proc: Optional[subprocess.Popen[Any]] = None

    def pid_atual(self) -> Optional[int]:
        if self._proc is not None and self._proc.poll() is None:
            return self._proc.pid
        return descobrir_pid_ouvinte_porta_windows(self.porta)

    def _aguardar_porta_livre(self, timeout_s: float = 12.0) -> None:
        prazo = time.perf_counter() + timeout_s
        while time.perf_counter() < prazo:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                if s.connect_ex(("127.0.0.1", self.porta)) != 0:
                    return
            time.sleep(0.2)
        raise TimeoutError(f"Porta {self.porta} nao liberada apos encerramento do processo anterior.")

    def reiniciar_para(
        self,
        *,
        lotofacil_modo4_ativo: bool,
        permitir_experimental_2j: bool = False,
        politica_micro: str = POLITICA_MICRO_PRODUCAO_PADRAO,
    ) -> Dict[str, Any]:
        if permitir_experimental_2j is not False:
            raise ValueError("experimental_2J deve permanecer False na promocao controlada.")
        pid_antigo = self.pid_atual()
        if pid_antigo is not None:
            subprocess.run(["taskkill", "/PID", str(pid_antigo), "/T", "/F"], capture_output=True, timeout=10)
            self._aguardar_porta_livre()

        env = os.environ.copy()
        env[ENV_FEATURE_FLAG_LOTOFACIL_MODO4] = "true" if lotofacil_modo4_ativo else "false"
        env[ENV_PERMITIR_EXPERIMENTAL_2J] = "false"
        env[ENV_POLITICA_MICRO_PADRAO] = politica_micro
        cmd_py = (
            "import sys, uvicorn; "
            f"sys.path.insert(0, {BASE_DIR!r}); "
            "import api; "
            f"uvicorn.run(api.app, host='127.0.0.1', port={self.porta}, workers=1)"
        )
        self._proc = subprocess.Popen(
            [sys.executable, "-c", cmd_py],
            cwd=BASE_DIR,
            env=env,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        prazo = time.perf_counter() + 20.0
        while time.perf_counter() < prazo:
            if self._proc.poll() is not None:
                raise RuntimeError(f"Processo na porta {self.porta} encerrou prematuramente (rc={self._proc.returncode}).")
            h = _sondar_http_cronometrado(self.base_url, endpoint="/health", metodo="GET", timeout_s=1.0)
            if h["status_http"] == 200 and isinstance(h.get("dados_brutos"), dict):
                return {"pid": self._proc.pid, "ativo": lotofacil_modo4_ativo}
            time.sleep(0.2)
        raise TimeoutError(f"Timeout aguardando subida de 127.0.0.1:{self.porta}.")


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Preparacao Auditavel e Executor Protegido da Fase 3 (Promocao Controlada na Porta 8000)."
    )
    parser.add_argument(
        "--preparacao-check",
        action="store_true",
        help="Confere passivamente artefatos da Fase 3, Ata GO da Fase 2 e 7 hashes selados.",
    )
    parser.add_argument(
        "--snapshot-somente-leitura",
        action="store_true",
        help="Captura snapshot passivo da porta 8000 com allowlist estrita de ambiente, sem reiniciar o servico.",
    )
    parser.add_argument(
        "--autorizar-execucao-fase3",
        action="store_true",
        help="Exige --confirmacao-humana-fase3 e --pos-rollback-modo explicitos; bloqueado sem ambos.",
    )
    parser.add_argument(
        "--confirmacao-humana-fase3",
        default=None,
        help="Token humano explicito obrigatorio para execucao futura da Fase 3.",
    )
    parser.add_argument(
        "--pos-rollback-modo",
        default=None,
        choices=MODOS_POS_ROLLBACK_VALIDOS,
        help="Estado final explicito da porta 8000 apos comprovacao do rollback.",
    )
    args = parser.parse_args(argv)

    if args.preparacao_check and not args.autorizar_execucao_fase3 and not args.snapshot_somente_leitura:
        res = verificar_preparacao_fase3_somente_leitura()
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0 if res["pronto_para_deliberacao"] else 1

    if args.snapshot_somente_leitura and not args.autorizar_execucao_fase3:
        snap = capturar_snapshot_producao_somente_leitura(porta=8000, incluir_sondagem_endpoints=False)
        print(json.dumps(snap, indent=2, ensure_ascii=False))
        return 0 if snap["alcancavel"] and snap["integridade_7_selados"]["integro"] else 1

    if (
        not args.autorizar_execucao_fase3
        or args.confirmacao_humana_fase3 != TOKEN_CONFIRMACAO_HUMANA_FASE3
        or args.pos_rollback_modo not in MODOS_POS_ROLLBACK_VALIDOS
    ):
        print(
            json.dumps(
                {
                    "bloqueado": True,
                    "fase": "FASE_3_PREPARACAO_SOMENTE",
                    "motivo": (
                        "Execucao da Fase 3 em producao nao autorizada. Use --preparacao-check ou "
                        "--snapshot-somente-leitura para verificacao passiva sem alterar a porta 8000."
                    ),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 2

    res_f3 = executar_protocolo_fase3_controlado(
        controlador_processo=_ControladorProcessoPortaProducao(porta=8000),
        autorizacao_explicita=True,
        confirmacao_humana=args.confirmacao_humana_fase3,
        pos_rollback_modo=args.pos_rollback_modo,
        permitir_experimental_2j=False,
    )
    print(json.dumps(res_f3["ata_decisao"], indent=2, ensure_ascii=False))
    return 0 if res_f3["ata_decisao"]["veredito"] == "GO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
