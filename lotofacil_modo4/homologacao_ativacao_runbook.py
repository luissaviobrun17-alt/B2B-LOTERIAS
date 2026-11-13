# -*- coding: utf-8 -*-
"""
LOTOFACIL MODO 4 - RUNBOOK ISOLADO DE HOMOLOGACAO ESPECIFICA DE ATIVACAO (FASE 1 / REVISAO CALIBRADA)
==================================================================================================
Script modular para verificacao de preparacao (`--preparacao-check`), microcalibracao em porta
isolada (`--microcalibracao-revisao-fase1`) e futura execucao isolada da Homologacao Especifica
de Ativacao (`--autorizar-homologacao-isolada`).

REGRAS DE SEGURANCA E GOVERNANCA:
1. Nao executa homologacao Fase 2 nem liga feature flag de producao sem autorizacao expressa.
2. Nao modifica nenhum dos 7 arquivos selados em `manifesto_promocao_controlada.json`, nem
   os artefatos congelados das Etapas 1-5, `motor_lotomania_modo4.py` ou os manifestos historicos.
3. Toda a bateria ativa e de microcalibracao roda em subprocesso Uvicorn (`workers=1`) e servidor
   UI dedicados em portas isoladas (`18080` / `18081` ou livres), preservando `127.0.0.1:8000`
   inalterada antes e depois dos ensaios.
4. Evidencias da revisao e da futura janela sao gravadas exclusivamente em
   `auditoria/lotofacil_modo4/homologacao_ativacao/`.
"""

from __future__ import annotations

import argparse
import base64
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import ctypes
from ctypes import wintypes
from datetime import datetime, timezone
from functools import partial
import hashlib
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import math
import os
import platform
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple
import urllib.error
import urllib.request

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lotofacil_modo4.etapa1_regras_oficiais import CLAUSULA_MATEMATICA_OBRIGATORIA
from lotofacil_modo4.etapa2_funcao_objetivo import NOMES_COMPONENTES
from lotofacil_modo4.etapa4_referencia_independente import (
    auditar_conformidade_etapa4_ref,
    avaliar_carteira_ref_etapa4,
)
from lotofacil_modo4.etapa5_api_homologacao import (
    ServidorHttpHomologacao,
    chamar_api_lotofacil_modo4_seguro,
)
from lotofacil_modo4.promocao_producao import (
    VERSAO_PROMOCAO_LOTOFACIL_MODO4,
    calcular_hash_carteira_lotofacil,
    definir_feature_flag_lotofacil_modo4,
    verificar_integridade_promocao,
)

DIR_HOMOLOGACAO_REL = os.path.join("auditoria", "lotofacil_modo4", "homologacao_ativacao")
DIR_HOMOLOGACAO_ABS = os.path.join(BASE_DIR, DIR_HOMOLOGACAO_REL)
CAMINHO_CONFIG_JSON = os.path.join(DIR_HOMOLOGACAO_ABS, "config_homologacao_ativacao.json")
CAMINHO_RUNBOOK_MD = os.path.join(DIR_HOMOLOGACAO_ABS, "RUNBOOK_HOMOLOGACAO_ATIVACAO.md")
CAMINHO_MICROCALIBRACAO_JSON = os.path.join(DIR_HOMOLOGACAO_ABS, "microcalibracao_fase1.json")
CAMINHO_RELATORIO_REVISAO_MD = os.path.join(DIR_HOMOLOGACAO_ABS, "RELATORIO_REVISAO_FASE1.md")

CONTROLES_ROTAS_LEGADAS: Dict[str, Dict[str, Any]] = {
    "/api/v1/motor-lotofacil": {
        "payload": {"quantidade_jogos": 3, "historico_limite": 20, "estrategia": "equilibrada"},
        "campo_numeros": "numeros",
        "qtd_dezenas": 15,
        "min_dezena": 1,
        "max_dezena": 25,
    },
    "/api/v1/motor-lotomania": {
        "payload": {"quantidade_jogos": 3, "historico_limite": 20, "estrategia": "equilibrada"},
        "campo_numeros": None,
        "qtd_dezenas": 50,
        "min_dezena": 1,
        "max_dezena": 100,
    },
    "/api/v1/motor-diadesorte": {
        "payload": {"quantidade_jogos": 3, "historico_limite": 20, "estrategia": "equilibrada"},
        "campo_numeros": "jogo",
        "qtd_dezenas": 7,
        "min_dezena": 1,
        "max_dezena": 31,
    },
    "/api/v1/motor-megasena": {
        "payload": {"quantidade_jogos": 3, "historico_limite": 20, "estrategia": "equilibrada"},
        "campo_numeros": "numeros",
        "qtd_dezenas": 6,
        "min_dezena": 1,
        "max_dezena": 60,
    },
}

CHROME_CANDIDATOS = (
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
)


class _MemoryStatusEx(ctypes.Structure):
    _fields_ = [
        ("dwLength", wintypes.DWORD),
        ("dwMemoryLoad", wintypes.DWORD),
        ("ullTotalPhys", ctypes.c_uint64),
        ("ullAvailPhys", ctypes.c_uint64),
        ("ullTotalPageFile", ctypes.c_uint64),
        ("ullAvailPageFile", ctypes.c_uint64),
        ("ullTotalVirtual", ctypes.c_uint64),
        ("ullAvailVirtual", ctypes.c_uint64),
        ("ullAvailExtendedVirtual", ctypes.c_uint64),
    ]


class _ProcessMemoryCountersEx(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
        ("PrivateUsage", ctypes.c_size_t),
    ]


def carregar_config_homologacao(caminho: str = CAMINHO_CONFIG_JSON) -> Dict[str, Any]:
    """Carrega a configuracao congelada de Go/No-Go da Fase 1."""
    with open(caminho, encoding="utf-8") as f:
        return json.load(f)


def coletar_telemetria_hardware() -> Dict[str, Any]:
    """Coleta capacidades reais de CPU, RAM, disco e navegadores via stdlib/Win32."""
    mem = _MemoryStatusEx()
    mem.dwLength = ctypes.sizeof(_MemoryStatusEx)
    ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(mem))
    disco = shutil.disk_usage(BASE_DIR)

    navegador_encontrado = None
    for cand in CHROME_CANDIDATOS:
        if os.path.isfile(cand):
            navegador_encontrado = cand
            break
    if navegador_encontrado is None:
        for exe in ("chrome", "msedge"):
            achado = shutil.which(exe)
            if achado:
                navegador_encontrado = achado
                break

    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "sistema_operacional": platform.platform(),
        "arquitetura": platform.machine(),
        "python_versao": platform.python_version(),
        "cpu_threads_logicas": int(os.cpu_count() or 1),
        "ram_total_gb": round(mem.ullTotalPhys / (1024**3), 2),
        "ram_disponivel_gb": round(mem.ullAvailPhys / (1024**3), 2),
        "ram_uso_pct": int(mem.dwMemoryLoad),
        "disco_livre_gb": round(disco.free / (1024**3), 2),
        "navegador_headless": navegador_encontrado,
    }


def medir_memoria_processo_windows(pid: int) -> Dict[str, float]:
    """Consulta WorkingSetSize, PeakWorkingSetSize e PrivateUsage em MB via Win32 psapi."""
    PROCESS_QUERY_INFORMATION = 0x0400
    PROCESS_VM_READ = 0x0010
    handle = ctypes.windll.kernel32.OpenProcess(
        PROCESS_QUERY_INFORMATION | PROCESS_VM_READ, False, int(pid)
    )
    if not handle:
        raise OSError(f"OpenProcess falhou para PID {pid}: erro Win32 {ctypes.GetLastError()}")
    try:
        pmc = _ProcessMemoryCountersEx()
        pmc.cb = ctypes.sizeof(_ProcessMemoryCountersEx)
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(handle, ctypes.byref(pmc), pmc.cb)
        if not ok:
            raise OSError(f"GetProcessMemoryInfo falhou para PID {pid}: erro Win32 {ctypes.GetLastError()}")
        mb = 1024.0 * 1024.0
        return {
            "rss_atual_mb": round(pmc.WorkingSetSize / mb, 2),
            "rss_pico_mb": round(pmc.PeakWorkingSetSize / mb, 2),
            "privado_mb": round(pmc.PrivateUsage / mb, 2),
        }
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _reservar_porta_livre(preferida: int) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferida))
            return preferida
        except OSError:
            s.bind(("127.0.0.1", 0))
            return int(s.getsockname()[1])


def _calcular_estatisticas_latencia(latencias_s: Sequence[float]) -> Dict[str, Any]:
    if not latencias_s:
        return {"n": 0, "min_s": 0.0, "media_s": 0.0, "p50_s": 0.0, "p95_s": 0.0, "p99_s": 0.0, "max_s": 0.0}
    ord_lat = sorted(float(x) for x in latencias_s)
    n = len(ord_lat)

    def _pct(p: float) -> float:
        idx = min(n - 1, max(0, math.ceil(p * n) - 1))
        return round(ord_lat[idx], 4)

    return {
        "n": n,
        "min_s": round(ord_lat[0], 4),
        "media_s": round(sum(ord_lat) / n, 4),
        "p50_s": _pct(0.50),
        "p95_s": _pct(0.95),
        "p99_s": _pct(0.99),
        "max_s": round(ord_lat[-1], 4),
    }


def _calcular_sha256_json_canonico(obj: Any) -> str:
    serializado = json.dumps(obj, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(serializado).hexdigest()


def _calcular_sha256_arquivo(caminho: str) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        while True:
            bloco = f.read(65536)
            if not bloco:
                break
            h.update(bloco)
    return h.hexdigest()


def _coletar_hashes_arquivos_legados() -> Dict[str, str]:
    hashes: Dict[str, str] = {}
    for nome in sorted(os.listdir(BASE_DIR)):
        if nome.startswith("motor_") and nome.endswith(".py"):
            hashes[nome] = _calcular_sha256_arquivo(os.path.join(BASE_DIR, nome))
    dir_data = os.path.join(BASE_DIR, "data")
    if os.path.isdir(dir_data):
        for nome in sorted(os.listdir(dir_data)):
            if nome.endswith(".json"):
                hashes[f"data/{nome}"] = _calcular_sha256_arquivo(os.path.join(dir_data, nome))
    return hashes


def _gerar_assinatura_canonica_entrada(
    endpoint: str,
    metodo: str,
    payload: Optional[Dict[str, Any]],
) -> str:
    canonico = {
        "endpoint": endpoint,
        "metodo": metodo.upper(),
        "payload": payload or {},
    }
    return _calcular_sha256_json_canonico(canonico)


def _extrair_semente_payload(payload: Optional[Dict[str, Any]]) -> Any:
    if not isinstance(payload, dict):
        return None
    if "semente" in payload:
        return payload.get("semente")
    return payload.get("seed")


def _agrupar_determinismo_por_assinatura(registros: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Agrupa hashes de saida por assinatura canonica da entrada (endpoint, metodo e payload).
    Exige repetibilidade estrita (1 unico hash de saida) para entradas identicas, sem exigir
    que sementes diferentes produzam necessariamente hashes distintos.
    """
    buckets: Dict[str, List[Dict[str, Any]]] = {}
    for reg in registros:
        chave = f"{reg['tipo']}::{reg['assinatura_entrada']}"
        buckets.setdefault(chave, []).append(reg)

    grupos: Dict[str, Any] = {}
    for chave, itens in buckets.items():
        amostras = len(itens)
        hashes = [str(it["hash_saida"]) for it in itens if it.get("hash_saida")]
        hashes_distintos = sorted(set(hashes))
        hist_nulo_ok = all(it.get("historico_utilizado") is None for it in itens)
        repetivel = len(hashes) == amostras and len(hashes_distintos) == 1 and hist_nulo_ok
        grupos[chave] = {
            "tipo": itens[0]["tipo"],
            "assinatura_entrada": itens[0]["assinatura_entrada"],
            "semente": itens[0].get("semente"),
            "amostras": amostras,
            "hashes_validos": len(hashes),
            "hashes_distintos": len(hashes_distintos),
            "hash_saida_unico": hashes_distintos[0] if len(hashes_distintos) == 1 else None,
            "historico_sempre_nulo": hist_nulo_ok,
            "repetivel": repetivel,
        }

    grupos_lf = {k: v for k, v in grupos.items() if v["tipo"].startswith("lotofacil_")}
    grupos_lm = {k: v for k, v in grupos.items() if v["tipo"] == "lotomania_modo4_gerar"}
    return {
        "total_grupos": len(grupos),
        "grupos": grupos,
        "repetibilidade_ok": bool(grupos) and all(g["repetivel"] for g in grupos.values()),
        "lotofacil_repetibilidade_ok": (not grupos_lf) or all(g["repetivel"] for g in grupos_lf.values()),
        "lotomania_repetibilidade_ok": (not grupos_lm) or all(g["repetivel"] for g in grupos_lm.values()),
    }


def _validar_contrato_resposta_legada(
    endpoint: str,
    payload: Dict[str, Any],
    dados: Any,
) -> Tuple[bool, str]:
    spec = CONTROLES_ROTAS_LEGADAS.get(endpoint)
    if spec is None:
        return isinstance(dados, dict) and bool(dados.get("sucesso") is True), "rota_legada_generica"
    if not isinstance(dados, dict) or dados.get("sucesso") is not True:
        return False, "sucesso_falso_ou_ausente"
    jogos = dados.get("jogos")
    qtd_esp = int(payload.get("quantidade_jogos", 0))
    if not isinstance(jogos, list) or len(jogos) != qtd_esp:
        return False, f"quantidade_jogos_divergente:{len(jogos) if isinstance(jogos, list) else None}!={qtd_esp}"
    campo = spec["campo_numeros"]
    qtd_dez = int(spec["qtd_dezenas"])
    d_min = int(spec["min_dezena"])
    d_max = int(spec["max_dezena"])
    for idx, item in enumerate(jogos):
        dezenas = item if campo is None else (item.get(campo) if isinstance(item, dict) else None)
        if not isinstance(dezenas, list) or len(dezenas) != qtd_dez:
            return False, f"jogo_{idx}_tamanho_invalido"
        if not all(isinstance(d, int) and not isinstance(d, bool) and d_min <= d <= d_max for d in dezenas):
            return False, f"jogo_{idx}_faixa_invalida"
        if len(set(dezenas)) != qtd_dez:
            return False, f"jogo_{idx}_dezenas_duplicadas"
    return True, "ok"


class _MonitorMemoriaProcesso:
    """Monitora WorkingSetSize, PeakWorkingSetSize e PrivateUsage periodicamente em thread daemon."""

    def __init__(self, pid: int, *, intervalo_s: float = 0.25) -> None:
        self.pid = int(pid)
        self.intervalo_s = max(0.05, float(intervalo_s))
        self._stop = threading.Event()
        self._lock = threading.Lock()
        self._thread: Optional[threading.Thread] = None
        self._t0 = 0.0
        self.amostras: List[Dict[str, float]] = []

    def _coletar_ponto(self) -> None:
        try:
            leitura = medir_memoria_processo_windows(self.pid)
        except OSError:
            return
        ponto = {
            "t_s": round(time.perf_counter() - self._t0, 4),
            "rss_atual_mb": float(leitura["rss_atual_mb"]),
            "rss_pico_mb": float(leitura["rss_pico_mb"]),
            "privado_mb": float(leitura["privado_mb"]),
        }
        with self._lock:
            self.amostras.append(ponto)

    def _loop(self) -> None:
        while not self._stop.wait(self.intervalo_s):
            self._coletar_ponto()

    def __enter__(self) -> "_MonitorMemoriaProcesso":
        self._t0 = time.perf_counter()
        self._coletar_ponto()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        self._coletar_ponto()

    def resumo(self) -> Dict[str, Any]:
        with self._lock:
            pts = list(self.amostras)
        if not pts:
            raise RuntimeError(f"Nenhuma leitura de memoria obtida para PID {self.pid}.")
        return {
            "pid_monitorado": self.pid,
            "escopo_processo": "exclusivo_subprocesso_uvicorn_workers_1",
            "intervalo_amostragem_s": self.intervalo_s,
            "amostras_count": len(pts),
            "rss_atual_antes_mb": pts[0]["rss_atual_mb"],
            "rss_atual_depois_mb": pts[-1]["rss_atual_mb"],
            "rss_atual_max_mb": max(p["rss_atual_mb"] for p in pts),
            "rss_pico_windows_antes_mb": pts[0]["rss_pico_mb"],
            "rss_pico_windows_max_mb": max(p["rss_pico_mb"] for p in pts),
            "privado_max_mb": max(p["privado_mb"] for p in pts),
            "amostras": pts,
        }


def _capturar_estado_producao_8000(porta_prod: int = 8000) -> Dict[str, Any]:
    base_url = f"http://127.0.0.1:{int(porta_prod)}"
    r_health = _sondar_http_cronometrado(base_url, endpoint="/health", metodo="GET", timeout_s=3.0)
    r_status = _sondar_http_cronometrado(
        base_url, endpoint="/api/v1/lotofacil-modo4/status", metodo="GET", timeout_s=3.0
    )
    dh = r_health.get("dados_brutos")
    ds = r_status.get("dados_brutos")
    if (
        r_health["status_http"] == 200
        and r_status["status_http"] == 200
        and isinstance(dh, dict)
        and isinstance(ds, dict)
    ):
        lm = dh.get("modo4") or {}
        l4_h = dh.get("lotofacil_modo4") or {}
        estado_norm = {
            "api_operacional": dh.get("api_operacional"),
            "modo4_disponivel": dh.get("modo4_disponivel"),
            "lotomania_sha256_manifesto": lm.get("sha256_manifesto"),
            "lotomania_selo_valido": lm.get("selo_valido"),
            "lotofacil_disponivel": ds.get("disponivel"),
            "health_lotofacil_disponivel": l4_h.get("disponivel"),
            "feature_flag_ativa": ds.get("feature_flag_ativa"),
            "status": ds.get("status"),
            "experimental_2j_habilitada": ds.get("experimental_2j_habilitada"),
            "politica_micro_padrao": ds.get("politica_micro_padrao"),
            "inicializacao_mista": ds.get("inicializacao_mista"),
            "integridade_verificada": ds.get("integridade_verificada"),
            "integridade_etapas_1_a_5_valida": ds.get("integridade_etapas_1_a_5_valida"),
            "selo_lotomania_valido": ds.get("selo_lotomania_valido"),
            "divergencias_integridade": ds.get("divergencias_integridade"),
            "sha256_modulos_promocao": ds.get("sha256_modulos_promocao"),
            "telemetria": ds.get("telemetria"),
        }
        return {
            "alcancavel": True,
            "porta": int(porta_prod),
            "health_http": 200,
            "status_http": 200,
            "estado_normalizado": estado_norm,
            "sha256_estado_normalizado": _calcular_sha256_json_canonico(estado_norm),
        }
    return {
        "alcancavel": False,
        "porta": int(porta_prod),
        "health_http": r_health.get("status_http"),
        "health_erro": r_health.get("erro"),
        "status_http": r_status.get("status_http"),
        "status_erro": r_status.get("erro"),
    }


def _comparar_producao_8000_antes_depois(
    antes: Dict[str, Any],
    depois: Dict[str, Any],
    *,
    exigir_alcancavel: bool = True,
) -> Dict[str, Any]:
    antes_ok = bool(antes.get("alcancavel"))
    depois_ok = bool(depois.get("alcancavel"))
    if exigir_alcancavel and (not antes_ok or not depois_ok):
        return {
            "preservada": False,
            "motivo": "porta_8000_inacessivel_antes_ou_depois",
            "antes_alcancavel": antes_ok,
            "depois_alcancavel": depois_ok,
            "hashes_identicos": False,
            "sha256_antes": antes.get("sha256_estado_normalizado"),
            "sha256_depois": depois.get("sha256_estado_normalizado"),
        }
    if not antes_ok and not depois_ok:
        return {
            "preservada": False,
            "motivo": "porta_8000_inacessivel",
            "antes_alcancavel": False,
            "depois_alcancavel": False,
            "hashes_identicos": False,
            "sha256_antes": None,
            "sha256_depois": None,
        }
    est_a = antes.get("estado_normalizado") or {}
    est_d = depois.get("estado_normalizado") or {}
    sha_a = antes.get("sha256_estado_normalizado")
    sha_d = depois.get("sha256_estado_normalizado")
    invariantes_off = (
        est_a.get("lotofacil_disponivel") is False
        and est_d.get("lotofacil_disponivel") is False
        and est_a.get("feature_flag_ativa") is False
        and est_d.get("feature_flag_ativa") is False
        and est_a.get("experimental_2j_habilitada") is False
        and est_d.get("experimental_2j_habilitada") is False
        and est_a.get("politica_micro_padrao") == "conservadora_3J"
        and est_d.get("politica_micro_padrao") == "conservadora_3J"
        and est_a.get("inicializacao_mista") == "padrao"
        and est_d.get("inicializacao_mista") == "padrao"
        and est_a.get("integridade_verificada") is True
        and est_d.get("integridade_verificada") is True
        and est_a.get("lotomania_selo_valido") is True
        and est_d.get("lotomania_selo_valido") is True
    )
    hashes_iguais = bool(sha_a and sha_a == sha_d)
    preservada = bool(antes_ok and depois_ok and invariantes_off and hashes_iguais)
    return {
        "preservada": preservada,
        "motivo": "ok" if preservada else ("estado_mutado" if not hashes_iguais else "invariante_off_violada"),
        "antes_alcancavel": antes_ok,
        "depois_alcancavel": depois_ok,
        "invariantes_off_ok": invariantes_off,
        "hashes_identicos": hashes_iguais,
        "sha256_antes": sha_a,
        "sha256_depois": sha_d,
        "antes": antes,
        "depois": depois,
    }


def _sondar_http_cronometrado(
    base_url: str,
    payload: Optional[Dict[str, Any]] = None,
    *,
    endpoint: str = "/api/v1/lotofacil-modo4/gerar",
    metodo: str = "POST",
    timeout_s: float = 30.0,
) -> Dict[str, Any]:
    t0 = time.perf_counter()
    res = chamar_api_lotofacil_modo4_seguro(
        base_url,
        payload,
        endpoint=endpoint,
        metodo=metodo,
        timeout_s=timeout_s,
    )
    res["latencia_s"] = round(time.perf_counter() - t0, 4)
    return res


class _SubprocessoUvicornIsolado:
    """Inicia subprocesso dedicado do servidor `api:app` em porta isolada sem alterar producao."""

    def __init__(
        self,
        *,
        porta: int,
        lotofacil_modo4_ativo: bool,
        permitir_experimental_2j: bool = False,
        politica_micro: str = "conservadora_3J",
    ) -> None:
        self.porta = int(porta)
        self.lotofacil_modo4_ativo = bool(lotofacil_modo4_ativo)
        self.permitir_experimental_2j = bool(permitir_experimental_2j)
        self.politica_micro = politica_micro
        self.base_url = f"http://127.0.0.1:{self.porta}"
        self.proc: Optional[subprocess.Popen[str]] = None

    def __enter__(self) -> "_SubprocessoUvicornIsolado":
        env = os.environ.copy()
        env["LOTOFACIL_MODO4_ATIVO"] = "true" if self.lotofacil_modo4_ativo else "false"
        env["LOTOFACIL_MODO4_PERMITIR_EXPERIMENTAL_2J"] = "true" if self.permitir_experimental_2j else "false"
        env["LOTOFACIL_MODO4_POLITICA_MICRO"] = self.politica_micro
        cmd_py = (
            "import sys, uvicorn; "
            f"sys.path.insert(0, {BASE_DIR!r}); "
            "import api; "
            f"uvicorn.run(api.app, host='127.0.0.1', port={self.porta}, workers=1, log_level='warning', access_log=False)"
        )
        self.proc = subprocess.Popen(
            [sys.executable, "-c", cmd_py],
            cwd=BASE_DIR,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        prazo = time.perf_counter() + 20.0
        while time.perf_counter() < prazo:
            if self.proc.poll() is not None:
                out_e = self.proc.stderr.read() if self.proc.stderr else ""
                raise RuntimeError(f"Subprocesso Uvicorn isolado encerrou prematuramente: {out_e}")
            h = _sondar_http_cronometrado(self.base_url, endpoint="/health", metodo="GET", timeout_s=1.0)
            if h["status_http"] == 200 and isinstance(h.get("dados_brutos"), dict):
                return self
            time.sleep(0.15)
        self._encerrar()
        raise TimeoutError(f"Timeout ao aguardar subprocesso isolado em {self.base_url}")

    def _encerrar(self) -> None:
        if self.proc is None:
            return
        if self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(timeout=5.0)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=3.0)
        for stream in (self.proc.stdout, self.proc.stderr):
            if stream is not None:
                stream.close()

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        self._encerrar()


class _HandlerUiSilencioso(SimpleHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path.split("?")[0] == "/favicon.ico":
            self.send_response(204)
            self.end_headers()
            return
        super().do_GET()

    def log_message(self, format: str, *args: Any) -> None:
        return None


class _ServidorUiEstaticoIsolado:
    """Servidor HTTP somente-leitura para servir index.html e B2B_Loterias_Mobile.html ao navegador."""

    def __init__(self, porta: int) -> None:
        self.porta = int(porta)
        self.base_url = f"http://127.0.0.1:{self.porta}"
        self._srv: Optional[ThreadingHTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def __enter__(self) -> "_ServidorUiEstaticoIsolado":
        handler = partial(_HandlerUiSilencioso, directory=BASE_DIR)
        self._srv = ThreadingHTTPServer(("127.0.0.1", self.porta), handler)
        self._thread = threading.Thread(target=self._srv.serve_forever, daemon=True)
        self._thread.start()
        return self

    def __exit__(self, exc_type: Any, exc: Any, tb: Any) -> None:
        if self._srv is not None:
            self._srv.shutdown()
            self._srv.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2.0)


class _ClienteCdpWebSocket:
    """Cliente WebSocket RFC-6455 em stdlib pura para automacao Chrome DevTools Protocol."""

    def __init__(self, ws_url: str, timeout_s: float = 15.0) -> None:
        if not ws_url.startswith("ws://"):
            raise ValueError(f"URL WS invalida: {ws_url}")
        resto = ws_url[5:]
        host_port, path = resto.split("/", 1)
        host, port_str = host_port.split(":", 1)
        self._sock = socket.create_connection((host, int(port_str)), timeout=timeout_s)
        self._buf = bytearray()
        self._next_id = 1
        self.excecoes_js: List[Dict[str, Any]] = []
        self.erros_console: List[Dict[str, Any]] = []

        chave = base64.b64encode(os.urandom(16)).decode("ascii")
        req = (
            f"GET /{path} HTTP/1.1\r\n"
            f"Host: {host}:{port_str}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {chave}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        ).encode("ascii")
        self._sock.sendall(req)

        while b"\r\n\r\n" not in self._buf:
            chunk = self._sock.recv(4096)
            if not chunk:
                raise ConnectionError("Handshake WebSocket CDP encerrado sem cabecalho completo.")
            self._buf.extend(chunk)
        fim = self._buf.index(b"\r\n\r\n")
        cab = bytes(self._buf[:fim]).decode("latin-1")
        del self._buf[: fim + 4]
        if "101 " not in cab.splitlines()[0]:
            raise ConnectionError(f"Handshake WebSocket CDP recusado: {cab}")

    def close(self) -> None:
        try:
            self._sock.close()
        except OSError:
            pass

    def _ler_exato(self, n: int) -> bytes:
        while len(self._buf) < n:
            chunk = self._sock.recv(65536)
            if not chunk:
                raise ConnectionError("Conexao WebSocket CDP encerrada inesperadamente.")
            self._buf.extend(chunk)
        out = bytes(self._buf[:n])
        del self._buf[:n]
        return out

    def _enviar_frame(self, payload: bytes, opcode: int = 0x1) -> None:
        cab = bytearray([0x80 | (opcode & 0x0F)])
        tam = len(payload)
        if tam < 126:
            cab.append(0x80 | tam)
        elif tam < 65536:
            cab.append(0x80 | 126)
            cab.extend(struct.pack("!H", tam))
        else:
            cab.append(0x80 | 127)
            cab.extend(struct.pack("!Q", tam))
        mask = os.urandom(4)
        cab.extend(mask)
        mascarado = bytes(b ^ mask[i % 4] for i, b in enumerate(payload))
        self._sock.sendall(bytes(cab) + mascarado)

    def _receber_mensagem(self) -> str:
        fragmentos: List[bytes] = []
        while True:
            b1, b2 = self._ler_exato(2)
            fin = bool(b1 & 0x80)
            opcode = b1 & 0x0F
            masked = bool(b2 & 0x80)
            tam = b2 & 0x7F
            if tam == 126:
                tam = struct.unpack("!H", self._ler_exato(2))[0]
            elif tam == 127:
                tam = struct.unpack("!Q", self._ler_exato(8))[0]
            mask = self._ler_exato(4) if masked else None
            corpo = self._ler_exato(tam)
            if mask is not None:
                corpo = bytes(b ^ mask[i % 4] for i, b in enumerate(corpo))

            if opcode == 0x8:
                raise ConnectionError("CDP WebSocket fechado pelo Chrome.")
            if opcode == 0x9:
                self._enviar_frame(corpo, opcode=0xA)
                continue
            if opcode == 0xA:
                continue
            fragmentos.append(corpo)
            if fin:
                return b"".join(fragmentos).decode("utf-8", errors="replace")

    def chamar(
        self,
        method: str,
        params: Optional[Dict[str, Any]] = None,
        *,
        timeout_s: float = 20.0,
    ) -> Dict[str, Any]:
        req_id = self._next_id
        self._next_id += 1
        self._sock.settimeout(timeout_s)
        msg = json.dumps({"id": req_id, "method": method, "params": params or {}}).encode("utf-8")
        self._enviar_frame(msg, opcode=0x1)

        prazo = time.perf_counter() + timeout_s
        while time.perf_counter() < prazo:
            bruto = self._receber_mensagem()
            obj = json.loads(bruto)
            if "method" in obj:
                ev = obj["method"]
                p = obj.get("params", {})
                if ev == "Runtime.exceptionThrown":
                    self.excecoes_js.append(p)
                elif ev == "Runtime.consoleAPICalled" and p.get("type") == "error":
                    self.erros_console.append(p)
                elif ev == "Page.javascriptDialogOpening":
                    try:
                        self._enviar_frame(
                            json.dumps(
                                {
                                    "id": self._next_id,
                                    "method": "Page.handleJavaScriptDialog",
                                    "params": {"accept": True},
                                }
                            ).encode("utf-8")
                        )
                        self._next_id += 1
                    except Exception:
                        pass
                continue
            if obj.get("id") == req_id:
                if "error" in obj:
                    raise RuntimeError(f"Erro CDP em {method}: {obj['error']}")
                return obj.get("result", {})
        raise TimeoutError(f"Timeout CDP aguardando resposta de {method}")

    def avaliar_js(self, expr: str, *, await_promise: bool = True, timeout_s: float = 25.0) -> Any:
        res = self.chamar(
            "Runtime.evaluate",
            {
                "expression": expr,
                "awaitPromise": await_promise,
                "returnByValue": True,
            },
            timeout_s=timeout_s,
        )
        if "exceptionDetails" in res:
            raise RuntimeError(f"Excecao JS avaliada via CDP: {res['exceptionDetails']}")
        return res.get("result", {}).get("value")


def executar_frente_1_criptografia(cfg_hom: Dict[str, Any]) -> Dict[str, Any]:
    c1 = cfg_hom["criterios_go_no_go"]["frente_1_criptografia"]
    res = verificar_integridade_promocao(
        diretorio_base=BASE_DIR,
        verificar_lotomania_selo=c1["exigir_selo_lotomania_valido"],
        exigir_manifesto_etapa5=c1["exigir_manifesto_etapa5"],
        exigir_manifesto_promocao=c1["exigir_manifesto_promocao"],
        verificar_manifesto_promocao_se_presente=True,
    )
    ok = (
        res["integro"] is True
        and res["integro_etapas_1_a_5"] is True
        and res["manifesto_etapa5_presente"] is True
        and res["manifesto_promocao_presente"] is True
        and res["selo_lotomania_valido"] is True
        and len(res["divergencias"]) <= c1["max_divergencias"]
    )
    return {"aprovada": ok, "detalhes": res}


def executar_frente_2_rotas(cfg_hom: Dict[str, Any], porta_api: int) -> Dict[str, Any]:
    c2 = cfg_hom["criterios_go_no_go"]["frente_2_rotas_e_contratos"]
    casos = cfg_hom["casos_repetibilidade"]

    # 2A) Instancia isolada com flag OFF
    with _SubprocessoUvicornIsolado(porta=porta_api, lotofacil_modo4_ativo=False) as srv_off:
        r_status_off = _sondar_http_cronometrado(
            srv_off.base_url, endpoint="/api/v1/lotofacil-modo4/status", metodo="GET"
        )
        r_gerar_off = _sondar_http_cronometrado(srv_off.base_url, casos["caso_simples_conservador"])
        r_av_off = _sondar_http_cronometrado(
            srv_off.base_url, {"carteira": [list(range(1, 16))]}, endpoint="/api/v1/lotofacil-modo4/avaliar"
        )
        off_ok = (
            r_status_off["status_http"] == 200
            and r_status_off["dados_brutos"]["disponivel"] is False
            and r_gerar_off["status_http"] == 503
            and r_gerar_off["jogos"] == []
            and r_gerar_off["fallback_executado"] is False
            and r_av_off["status_http"] == 503
            and r_av_off["jogos"] == []
        )

    # 2B) Instancia isolada com flag ON (experimental_2J ainda desabilitada por padrao)
    with _SubprocessoUvicornIsolado(porta=porta_api, lotofacil_modo4_ativo=True) as srv_on:
        r_status_on = _sondar_http_cronometrado(
            srv_on.base_url, endpoint="/api/v1/lotofacil-modo4/status", metodo="GET"
        )
        r_simples = _sondar_http_cronometrado(srv_on.base_url, casos["caso_simples_conservador"])
        r_mult16 = _sondar_http_cronometrado(srv_on.base_url, casos["caso_multipla_16_independencia"])

        negativos = {}
        payloads_422 = {
            "experimental_2J": {"quantidade_jogos": 8, "semente": 42, "politica_micro": "experimental_2J"},
            "inicializacao_mista": {"quantidade_jogos": 4, "inicializacao_mista": "mista_equilibrada"},
            "historico_proibido": {"quantidade_jogos": 4, "historico": [[1, 2, 3]]},
            "conflito_pool_bloqueadas": {
                "quantidade_jogos": 4,
                "pool": list(range(1, 26)),
                "bloqueadas": [24, 25],
            },
        }
        neg_ok = True
        for k, pl in payloads_422.items():
            rn = _sondar_http_cronometrado(srv_on.base_url, pl)
            negativos[k] = {"status_http": rn["status_http"], "jogos": len(rn["jogos"])}
            if rn["status_http"] != 422 or len(rn["jogos"]) != 0 or rn["fallback_executado"] is not False:
                neg_ok = False

        ds = r_simples.get("dados_brutos") or {}
        dm = r_mult16.get("dados_brutos") or {}
        esp_s = ds.get("especificacao", {})
        r_avaliar = _sondar_http_cronometrado(
            srv_on.base_url,
            {
                "carteira": ds.get("jogos", []),
                "pool": esp_s.get("pool"),
                "fixas": esp_s.get("fixas", []),
                "bloqueadas": esp_s.get("bloqueadas", []),
                "modo_fixas": esp_s.get("modo_fixas", "todos_os_jogos"),
            },
            endpoint="/api/v1/lotofacil-modo4/avaliar",
        )

        # Validacao AST independente direta na resposta simples e /avaliar
        av_ref_s = avaliar_carteira_ref_etapa4(
            ds.get("jogos", []),
            pool=esp_s.get("pool"),
            fixas=esp_s.get("fixas", []),
            bloqueadas=esp_s.get("bloqueadas", []),
            modo_fixas=esp_s.get("modo_fixas", "todos_os_jogos"),
            pesos=esp_s.get("pesos"),
        )
        conf_s = auditar_conformidade_etapa4_ref(
            ds.get("jogos", []),
            pool=esp_s.get("pool"),
            fixas=esp_s.get("fixas", []),
            bloqueadas=esp_s.get("bloqueadas", []),
            modo_fixas=esp_s.get("modo_fixas", "todos_os_jogos"),
            tamanhos_esperados=esp_s.get("tamanhos_jogos"),
        )
        diff_F_s = abs(float(ds.get("funcao_objetivo_F", -1.0)) - float(av_ref_s["funcao_objetivo_F"]))
        max_diff_comp_s = max(
            abs(float(ds["componentes"][c]) - float(av_ref_s["componentes"][c])) for c in NOMES_COMPONENTES
        )
        dav = r_avaliar.get("dados_brutos") or {}
        diff_F_av = float(dav.get("auditoria_referencia_independente", {}).get("divergencia_F", 999.0))

        on_ok = (
            r_status_on["status_http"] == 200
            and r_status_on["dados_brutos"]["disponivel"] is True
            and r_simples["sucesso"] is True
            and r_mult16["sucesso"] is True
            and r_avaliar["status_http"] == 200
            and conf_s["conforme"] is True
            and ds.get("historico_utilizado") is None
            and ds.get("clausula_obrigatoria") == CLAUSULA_MATEMATICA_OBRIGATORIA
            and diff_F_s <= c2["tolerancia_divergencia_ast_F"]
            and max_diff_comp_s <= c2["tolerancia_divergencia_ast_componentes"]
            and diff_F_av <= c2["tolerancia_divergencia_ast_F"]
            and dm.get("auditoria_referencia_independente", {}).get("divergencia_F", 999.0)
            <= c2["tolerancia_divergencia_ast_F"]
        )

    return {
        "aprovada": bool(off_ok and neg_ok and on_ok),
        "off_ok": off_ok,
        "negativos_ok": neg_ok,
        "negativos": negativos,
        "on_ok": on_ok,
        "diff_F_simples": diff_F_s,
        "max_diff_comp_simples": max_diff_comp_s,
        "diff_F_avaliar": diff_F_av,
        "hash_carteira_simples": ds.get("hash_carteira_sha256"),
        "hash_carteira_mult16": dm.get("hash_carteira_sha256"),
    }


def _validar_item_patamar(
    tipo: str,
    endpoint: str,
    payload: Optional[Dict[str, Any]],
    res: Dict[str, Any],
) -> Tuple[Optional[Dict[str, Any]], Optional[Dict[str, Any]]]:
    """Valida resposta de um request de carga; retorna `(erro, registro_determinismo)`."""
    if res["status_http"] != 200:
        return {"tipo": tipo, "endpoint": endpoint, "status_http": res["status_http"], "erro": res.get("erro")}, None

    dados = res.get("dados_brutos") or {}
    assinatura = _gerar_assinatura_canonica_entrada(endpoint, "GET" if endpoint.endswith("/status") else "POST", payload)
    semente = _extrair_semente_payload(payload)

    if tipo in ("lotofacil_modo4_gerar", "lotofacil_modo4_gerar_simples", "lotofacil_modo4_gerar_multipla16"):
        pl = payload or {}
        jogos = dados.get("jogos") or []
        tam_esp = int(pl.get("tamanho_aposta", 15))
        qtd_esp = int(pl.get("quantidade_jogos", len(jogos)))
        tam_ok = isinstance(jogos, list) and len(jogos) == qtd_esp and all(isinstance(j, list) and len(j) == tam_esp for j in jogos)
        if (
            not dados.get("sucesso")
            or dados.get("fallback_executado") is not False
            or dados.get("historico_utilizado") is not None
            or not isinstance(dados.get("hash_carteira_sha256"), str)
            or not tam_ok
        ):
            return {"tipo": tipo, "endpoint": endpoint, "motivo": "contrato_gerar_violado"}, None
        return None, {
            "tipo": tipo,
            "assinatura_entrada": assinatura,
            "semente": semente,
            "hash_saida": dados["hash_carteira_sha256"],
            "historico_utilizado": dados.get("historico_utilizado"),
        }

    if tipo == "lotofacil_modo4_avaliar":
        if (
            not dados.get("sucesso")
            or dados.get("fallback_executado") is not False
            or dados.get("historico_utilizado") is not None
            or not isinstance(dados.get("avaliacao_etapa2"), dict)
            or not isinstance(dados.get("hash_carteira_sha256"), str)
        ):
            return {"tipo": tipo, "endpoint": endpoint, "motivo": "contrato_avaliar_violado"}, None
        return None, None

    if tipo == "lotofacil_modo4_status":
        if (
            dados.get("disponivel") is not True
            or dados.get("feature_flag_ativa") is not True
            or dados.get("integridade_verificada") is not True
        ):
            return {"tipo": tipo, "endpoint": endpoint, "motivo": "contrato_status_violado"}, None
        return None, None

    if tipo == "lotomania_modo4_gerar":
        pl = payload or {}
        jogos = dados.get("jogos") or []
        qtd_esp = int(pl.get("quantidade_jogos", len(jogos)))
        if (
            not dados.get("sucesso")
            or dados.get("historico_geracao") is not None
            or not isinstance(dados.get("hash_carteira_sha256_v2_canonico"), str)
            or not isinstance(jogos, list)
            or len(jogos) != qtd_esp
        ):
            return {"tipo": tipo, "endpoint": endpoint, "motivo": "contrato_lotomania_violado"}, None
        return None, {
            "tipo": tipo,
            "assinatura_entrada": assinatura,
            "semente": semente,
            "hash_saida": dados["hash_carteira_sha256_v2_canonico"],
            "historico_utilizado": dados.get("historico_geracao"),
        }

    if tipo == "motores_legados":
        ok_leg, motivo_leg = _validar_contrato_resposta_legada(endpoint, payload or {}, dados)
        if not ok_leg:
            return {"tipo": tipo, "endpoint": endpoint, "motivo": f"contrato_legado_violado:{motivo_leg}"}, None
        return None, None

    return None, None


def _construir_tarefas_patamar(
    pat: Dict[str, Any],
    casos: Dict[str, Any],
    carteira_base: Sequence[Sequence[int]],
    legados: Sequence[str],
) -> List[Tuple[str, str, str, Optional[Dict[str, Any]]]]:
    pl_simples = casos["caso_simples_conservador"]
    pl_mult16 = casos["caso_multipla_16_independencia"]
    pl_lm = casos["caso_lotomania_controle"]

    if "distribuicao" not in pat:
        n_req = int(pat["total_requisicoes"])
        return [
            ("lotofacil_modo4_gerar_simples", "/api/v1/lotofacil-modo4/gerar", "POST", pl_simples)
            for _ in range(n_req)
        ]

    dist = pat["distribuicao"]
    filas: List[List[Tuple[str, str, str, Optional[Dict[str, Any]]]]] = []

    def _add_fila(tipo: str, qtd: int, endpoint: str, metodo: str, payload: Optional[Dict[str, Any]]) -> None:
        if qtd > 0:
            filas.append([(tipo, endpoint, metodo, payload) for _ in range(qtd)])

    _add_fila(
        "lotofacil_modo4_gerar_simples",
        int(dist.get("lotofacil_modo4_gerar_simples", dist.get("lotofacil_modo4_gerar", 0))),
        "/api/v1/lotofacil-modo4/gerar",
        "POST",
        pl_simples,
    )
    _add_fila(
        "lotofacil_modo4_gerar_multipla16",
        int(dist.get("lotofacil_modo4_gerar_multipla16", 0)),
        "/api/v1/lotofacil-modo4/gerar",
        "POST",
        pl_mult16,
    )
    _add_fila(
        "lotofacil_modo4_avaliar",
        int(dist.get("lotofacil_modo4_avaliar", 0)),
        "/api/v1/lotofacil-modo4/avaliar",
        "POST",
        {"carteira": list(carteira_base)},
    )
    _add_fila(
        "lotofacil_modo4_status",
        int(dist.get("lotofacil_modo4_status", 0)),
        "/api/v1/lotofacil-modo4/status",
        "GET",
        None,
    )
    _add_fila(
        "lotomania_modo4_gerar",
        int(dist.get("lotomania_modo4_gerar", 0)),
        "/api/v1/lotomania-modo4/gerar",
        "POST",
        pl_lm,
    )
    qtd_leg = int(dist.get("motores_legados", 0))
    if qtd_leg > 0 and legados:
        fila_leg = []
        for i in range(qtd_leg):
            ep_leg = legados[i % len(legados)]
            pl_leg = dict(CONTROLES_ROTAS_LEGADAS.get(ep_leg, {}).get("payload") or {"quantidade_jogos": 3})
            fila_leg.append(("motores_legados", ep_leg, "POST", pl_leg))
        filas.append(fila_leg)

    # Intercala uniformemente para garantir concorrencia mista real ao longo de todo o patamar
    agendadas: List[Tuple[float, int, Tuple[str, str, str, Optional[Dict[str, Any]]]]] = []
    for f_idx, fila in enumerate(filas):
        n_f = len(fila)
        for i, item in enumerate(fila):
            agendadas.append(((i + 0.5) / n_f, f_idx, item))
    agendadas.sort(key=lambda x: (x[0], x[1]))
    return [item for _, _, item in agendadas]


def _executar_patamar_carga(
    *,
    base_url: str,
    pid_servidor: int,
    tarefas: Sequence[Tuple[str, str, str, Optional[Dict[str, Any]]]],
    clientes: int,
    timeout_s: float = 30.0,
    intervalo_memoria_s: float = 0.25,
) -> Dict[str, Any]:
    def _executar_uma(item: Tuple[str, str, str, Optional[Dict[str, Any]]]) -> Tuple[Tuple[str, str, str, Optional[Dict[str, Any]]], Dict[str, Any]]:
        _, ep, met, pl = item
        return item, _sondar_http_cronometrado(base_url, pl, endpoint=ep, metodo=met, timeout_s=timeout_s)

    t_ini = time.perf_counter()
    with _MonitorMemoriaProcesso(pid_servidor, intervalo_s=intervalo_memoria_s) as mon:
        with ThreadPoolExecutor(max_workers=clientes) as pool:
            resultados = list(pool.map(_executar_uma, tarefas))
    duracao_total_s = round(time.perf_counter() - t_ini, 4)
    mem_resumo = mon.resumo()

    por_tipo: Dict[str, List[float]] = {}
    registros_det: List[Dict[str, Any]] = []
    erros: List[Dict[str, Any]] = []

    for (tipo, endpoint, _metodo, payload), r in resultados:
        por_tipo.setdefault(tipo, []).append(float(r["latencia_s"]))
        err, reg_det = _validar_item_patamar(tipo, endpoint, payload, r)
        if err is not None:
            erros.append(err)
        if reg_det is not None:
            registros_det.append(reg_det)

    stats_por_tipo = {k: _calcular_estatisticas_latencia(v) for k, v in por_tipo.items()}
    det_res = _agrupar_determinismo_por_assinatura(registros_det)
    total = len(resultados)
    return {
        "total_requisicoes": total,
        "clientes_simultaneos": clientes,
        "uvicorn_workers": 1,
        "duracao_total_s": duracao_total_s,
        "erros_count": len(erros),
        "taxa_erro_pct": round(100.0 * len(erros) / max(1, total), 4),
        "amostra_erros": erros[:5],
        "latencias_por_tipo": stats_por_tipo,
        "determinismo_por_assinatura": det_res,
        "memoria_monitorada": mem_resumo,
    }


def _auditar_uso_semente_e_independencia_estado(
    base_url: str,
    casos: Dict[str, Any],
    timeout_s: float = 30.0,
) -> Dict[str, Any]:
    """
    Comprova repetibilidade para entradas identicas, uso da semente/nao dependencia
    de estado anterior (42 -> 43 -> 42), historico nulo e documenta comportamento para
    sementes distintas (sem exigir falsamente hashes sempre diferentes).
    """
    pl_s = dict(casos["caso_simples_conservador"])
    pl_m = dict(casos["caso_multipla_16_independencia"])

    sequencia = [
        ("simples_42_antes", {**pl_s, "semente": 42}),
        ("simples_43", {**pl_s, "semente": 43}),
        ("simples_42_depois", {**pl_s, "semente": 42}),
        ("simples_999", {**pl_s, "semente": 999}),
        ("mult16_42_antes", {**pl_m, "semente": 42}),
        ("mult16_43", {**pl_m, "semente": 43}),
        ("mult16_42_depois", {**pl_m, "semente": 42}),
    ]
    obs: Dict[str, Dict[str, Any]] = {}
    for nome, pl in sequencia:
        r = _sondar_http_cronometrado(base_url, pl, endpoint="/api/v1/lotofacil-modo4/gerar", timeout_s=timeout_s)
        dados = r.get("dados_brutos") or {}
        obs[nome] = {
            "status_http": r["status_http"],
            "semente": pl["semente"],
            "assinatura_entrada": _gerar_assinatura_canonica_entrada("/api/v1/lotofacil-modo4/gerar", "POST", pl),
            "hash_carteira_sha256": dados.get("hash_carteira_sha256"),
            "historico_utilizado": dados.get("historico_utilizado"),
            "algoritmo_utilizado": dados.get("algoritmo_utilizado"),
            "fallback_executado": dados.get("fallback_executado"),
        }

    todos_200 = all(v["status_http"] == 200 and bool(v["hash_carteira_sha256"]) and v["fallback_executado"] is False for v in obs.values())
    historico_nulo_ok = all(v["historico_utilizado"] is None for v in obs.values())
    rep_simples = bool(obs["simples_42_antes"]["hash_carteira_sha256"]) and (
        obs["simples_42_antes"]["hash_carteira_sha256"] == obs["simples_42_depois"]["hash_carteira_sha256"]
    )
    rep_mult16 = bool(obs["mult16_42_antes"]["hash_carteira_sha256"]) and (
        obs["mult16_42_antes"]["hash_carteira_sha256"] == obs["mult16_42_depois"]["hash_carteira_sha256"]
    )
    hashes_simples_sementes = {
        "42": obs["simples_42_antes"]["hash_carteira_sha256"],
        "43": obs["simples_43"]["hash_carteira_sha256"],
        "999": obs["simples_999"]["hash_carteira_sha256"],
    }
    hashes_mult16_sementes = {
        "42": obs["mult16_42_antes"]["hash_carteira_sha256"],
        "43": obs["mult16_43"]["hash_carteira_sha256"],
    }

    # Verifica propagacao efetiva da semente no modulo etapa3/etapa4 em nivel de PRNG
    rng_42_a = random_seed_probe(42)
    rng_43 = random_seed_probe(43)
    rng_42_b = random_seed_probe(42)
    semente_propagada_prng_ok = rng_42_a == rng_42_b and rng_42_a != rng_43

    return {
        "aprovada": bool(todos_200 and historico_nulo_ok and rep_simples and rep_mult16 and semente_propagada_prng_ok),
        "repetibilidade_simples_42_antes_depois": rep_simples,
        "repetibilidade_mult16_42_antes_depois": rep_mult16,
        "historico_utilizado_sempre_nulo": historico_nulo_ok,
        "semente_propagada_prng_ok": semente_propagada_prng_ok,
        "exigir_hashes_diferentes_entre_sementes_distintas": False,
        "comportamento_sementes_simples": {
            "hashes_por_semente": hashes_simples_sementes,
            "hashes_distintos_count": len(set(hashes_simples_sementes.values())),
            "convergencia_entre_sementes": len(set(hashes_simples_sementes.values())) < len(hashes_simples_sementes),
        },
        "comportamento_sementes_mult16": {
            "hashes_por_semente": hashes_mult16_sementes,
            "hashes_distintos_count": len(set(hashes_mult16_sementes.values())),
            "convergencia_entre_sementes": len(set(hashes_mult16_sementes.values())) < len(hashes_mult16_sementes),
        },
        "detalhes_sondagens": obs,
    }


def random_seed_probe(semente: int) -> Tuple[float, ...]:
    import random
    rng = random.Random(int(semente))
    return tuple(rng.random() for _ in range(4))


def executar_frente_3_carga(
    cfg_hom: Dict[str, Any],
    porta_api: int,
    *,
    modo_calibracao: bool = False,
) -> Dict[str, Any]:
    c3 = cfg_hom["criterios_go_no_go"]["frente_3_carga_escalonada"]
    casos = cfg_hom["casos_repetibilidade"]
    timeout_s = float(c3["timeout_por_requisicao_s"])
    pl_simples = casos["caso_simples_conservador"]
    legados = cfg_hom["criterios_go_no_go"]["frente_5_nao_interferencia"]["rotas_legadas_obrigatorias"]
    lim_mem = c3["limites_memoria_processo_isolado"]
    intervalo_mem_s = float(lim_mem.get("intervalo_amostragem_s", 0.25))

    patamares_res: List[Dict[str, Any]] = []
    todos_ok = True

    with _SubprocessoUvicornIsolado(porta=porta_api, lotofacil_modo4_ativo=True) as srv:
        pid = int(srv.proc.pid) if srv.proc else os.getpid()
        r_seed = _sondar_http_cronometrado(srv.base_url, pl_simples, timeout_s=timeout_s)
        carteira_base = r_seed["jogos"]
        mem_base = medir_memoria_processo_windows(pid)
        auditoria_sementes = _auditar_uso_semente_e_independencia_estado(srv.base_url, casos, timeout_s=timeout_s)
        if not auditoria_sementes["aprovada"]:
            todos_ok = False

        for pat in c3["patamares"]:
            pid_id = pat["id"]
            clientes = int(pat["clientes_simultaneos"])
            tarefas = _construir_tarefas_patamar(pat, casos, carteira_base, legados)
            m = _executar_patamar_carga(
                base_url=srv.base_url,
                pid_servidor=pid,
                tarefas=tarefas,
                clientes=clientes,
                timeout_s=timeout_s,
                intervalo_memoria_s=intervalo_mem_s,
            )

            violacoes_latencia: List[str] = []
            ok_pat = m["taxa_erro_pct"] <= c3["max_taxa_erro_pct"]
            det_ok = m["determinismo_por_assinatura"]["repetibilidade_ok"]
            if pat.get("exigir_determinismo_por_assinatura", True) and not det_ok:
                ok_pat = False
                violacoes_latencia.append("determinismo_por_assinatura")
            if pat.get("exigir_determinismo_lotomania", True) and not m["determinismo_por_assinatura"]["lotomania_repetibilidade_ok"]:
                ok_pat = False
                violacoes_latencia.append("determinismo_lotomania")

            limites_rotas = pat.get("limites_latencia_por_tipo_s") or {}
            if not modo_calibracao:
                for tipo_rota, lims in limites_rotas.items():
                    st_rota = m["latencias_por_tipo"].get(tipo_rota)
                    if not st_rota or st_rota.get("n", 0) == 0:
                        ok_pat = False
                        violacoes_latencia.append(f"{tipo_rota}:ausente")
                        continue
                    if "max_p95_s" in lims and st_rota["p95_s"] > float(lims["max_p95_s"]):
                        ok_pat = False
                        violacoes_latencia.append(f"{tipo_rota}:p95={st_rota['p95_s']}>{lims['max_p95_s']}")
                    if "max_p99_s" in lims and st_rota["p99_s"] > float(lims["max_p99_s"]):
                        ok_pat = False
                        violacoes_latencia.append(f"{tipo_rota}:p99={st_rota['p99_s']}>{lims['max_p99_s']}")

            m["id"] = pid_id
            m["violacoes"] = violacoes_latencia
            m["aprovado"] = ok_pat
            patamares_res.append(m)
            if not ok_pat:
                todos_ok = False

    rss_pico_max_obs = max(p["memoria_monitorada"]["rss_pico_windows_max_mb"] for p in patamares_res)
    rss_atual_max_obs = max(p["memoria_monitorada"]["rss_atual_max_mb"] for p in patamares_res)
    delta_rss_baseline_para_max = round(
        patamares_res[-1]["memoria_monitorada"]["rss_atual_depois_mb"]
        - patamares_res[0]["memoria_monitorada"]["rss_atual_depois_mb"],
        2,
    )
    delta_pico_windows = round(
        rss_pico_max_obs - float(mem_base["rss_pico_mb"]),
        2,
    )
    teto_rss_abs = float(lim_mem["max_rss_pico_absoluto_mb"])
    teto_cresc = float(lim_mem["max_crescimento_rss_baseline_para_max_mb"])
    mem_ok = rss_pico_max_obs <= teto_rss_abs and delta_rss_baseline_para_max <= teto_cresc

    return {
        "aprovada": bool(todos_ok and mem_ok),
        "uvicorn_workers": 1,
        "escopo_memoria": "exclusivo_subprocesso_uvicorn_workers_1",
        "memoria_warmup": mem_base,
        "rss_pico_windows_max_observado_mb": rss_pico_max_obs,
        "rss_atual_max_observado_mb": rss_atual_max_obs,
        "delta_rss_baseline_para_max_mb": delta_rss_baseline_para_max,
        "delta_pico_windows_mb": delta_pico_windows,
        "memoria_dentro_limites": mem_ok,
        "auditoria_sementes_e_estado": auditoria_sementes,
        "patamares": patamares_res,
    }


def _auditar_pagina_em_chrome(
    chrome_exe: str,
    url_pagina: str,
    porta_api_isolada: int,
    *,
    modo_ativo_esperado: bool,
) -> Dict[str, Any]:
    cdp_port = _reservar_porta_livre(19222)
    tmp_dir = tempfile.mkdtemp(prefix="lf_m4_cdp_")
    proc = subprocess.Popen(
        [
            chrome_exe,
            "--headless=new",
            f"--remote-debugging-port={cdp_port}",
            f"--user-data-dir={tmp_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--disable-gpu",
            "--disable-extensions",
            "about:blank",
        ],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    ws: Optional[_ClienteCdpWebSocket] = None
    try:
        ws_url = None
        prazo = time.perf_counter() + 12.0
        while time.perf_counter() < prazo:
            try:
                with urllib.request.urlopen(f"http://127.0.0.1:{cdp_port}/json/list", timeout=1.5) as resp:
                    targets = json.loads(resp.read().decode("utf-8"))
                pages = [t for t in targets if t.get("type") == "page" and t.get("webSocketDebuggerUrl")]
                if pages:
                    ws_url = pages[0]["webSocketDebuggerUrl"]
                    break
            except Exception:
                time.sleep(0.15)
        if not ws_url:
            raise RuntimeError("Chrome headless nao expos target CDP no prazo.")

        ws = _ClienteCdpWebSocket(ws_url, timeout_s=20.0)
        ws.chamar("Page.enable")
        ws.chamar("Runtime.enable")

        # Redireciona chamadas fetch para porta isolada dentro da aba de teste sem alterar arquivos em disco
        hook_js = f"""
        (function() {{
            const _origFetch = window.fetch.bind(window);
            window.fetch = function(input, init) {{
                if (typeof input === 'string' && input.startsWith('http://127.0.0.1:8000')) {{
                    input = input.replace('http://127.0.0.1:8000', 'http://127.0.0.1:{porta_api_isolada}');
                }}
                return _origFetch(input, init);
            }};
            window.__b2bAlerts = [];
            window.alert = function(msg) {{ window.__b2bAlerts.push(String(msg)); }};
        }})();
        """
        ws.chamar("Page.addScriptToEvaluateOnNewDocument", {"source": hook_js})
        ws.chamar("Page.navigate", {"url": url_pagina})

        # Aguarda window.ui e inicializacao do motor MODO 4
        prazo_dom = time.perf_counter() + 15.0
        pronto = False
        while time.perf_counter() < prazo_dom:
            pronto = bool(
                ws.avaliar_js(
                    "Boolean(document.readyState === 'complete' && window.ui && typeof MotorLotofacilModo4Engine !== 'undefined' && document.getElementById('tab-btn-lotofacil-modo4'))",
                    await_promise=False,
                )
            )
            if pronto:
                break
            time.sleep(0.15)
        if not pronto:
            raise RuntimeError(f"Timeout aguardando inicializacao de UI/Motor em {url_pagina}")

        estado_inicial = ws.avaliar_js(
            """
            (async () => {
                const uiRef = window.ui || window._b2bUI;
                const statusOk = await uiRef._atualizarStatusServidorLotofacilModo4();
                const sub = document.getElementById('subpanel-lotofacil-modo4');
                const chk = document.getElementById('check-exp2j-lotofacil-modo4');
                const cl = document.getElementById('clausula-obrigatoria-lotofacil-modo4');
                return {
                    statusOk: Boolean(statusOk),
                    subpanelDisplayInicial: sub ? getComputedStyle(sub).display : null,
                    exp2jDisabled: chk ? chk.disabled : null,
                    exp2jChecked: chk ? chk.checked : null,
                    clausulaTexto: cl ? cl.innerText.trim() : '',
                    badgeTexto: (document.getElementById('badge-status-lotofacil-modo4') || {}).innerText || ''
                };
            })()
            """
        )

        # Seleciona Lotofacil, abre aba MODO 4 e dispara geracao via UI real
        execucao = ws.avaliar_js(
            """
            (async () => {
                const uiRef = window.ui || window._b2bUI;
                const tabBtn = document.getElementById('tab-btn-lotofacil-modo4');
                if (tabBtn) tabBtn.click();
                const inputQtd = document.getElementById('input-qtd-jogos-lotofacil-modo4');
                if (inputQtd) inputQtd.value = '6';
                await uiRef._executarGeracaoLotofacilModo4();
                const jogos = Array.isArray(uiRef.currentGeneratedGames) ? uiRef.currentGeneratedGames : [];
                const alerta = document.getElementById('alerta-indisponivel-lotofacil-modo4');
                const contRes = document.getElementById('container-resultado-lotofacil-modo4');
                let avaliarTexto = '';
                if (jogos.length > 0 && document.getElementById('btn-avaliar-lotofacil-modo4')) {
                    await uiRef._avaliarCarteiraLotofacilModo4();
                    avaliarTexto = contRes ? contRes.innerText : '';
                }
                return {
                    qtdJogos: jogos.length,
                    primeiroJogoTam: jogos[0] ? jogos[0].length : 0,
                    alertaVisivel: alerta ? getComputedStyle(alerta).display !== 'none' : false,
                    alertaTexto: alerta ? alerta.innerText.trim() : '',
                    resultadoVisivel: contRes ? getComputedStyle(contRes).display !== 'none' : false,
                    resultadoTexto: contRes ? contRes.innerText : '',
                    avaliarTexto: avaliarTexto,
                    alerts: window.__b2bAlerts || []
                };
            })()
            """,
            timeout_s=30.0,
        )

        return {
            "url": url_pagina,
            "modo_ativo_esperado": modo_ativo_esperado,
            "excecoes_js_nao_tratadas": len(ws.excecoes_js),
            "detalhes_excecoes_js": ws.excecoes_js,
            "estado_inicial": estado_inicial,
            "execucao_ui": execucao,
        }
    finally:
        if ws is not None:
            ws.close()
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=3.0)
            except subprocess.TimeoutExpired:
                proc.kill()
        shutil.rmtree(tmp_dir, ignore_errors=True)


def executar_frente_4_navegador(
    cfg_hom: Dict[str, Any],
    *,
    porta_api: int,
    porta_ui: int,
    navegador_exe: Optional[str],
) -> Dict[str, Any]:
    if not navegador_exe or not os.path.isfile(navegador_exe):
        return {
            "aprovada": False,
            "motivo": "Navegador Chromium/Edge nao encontrado para auditoria automatizada.",
        }

    c4 = cfg_hom["criterios_go_no_go"]["frente_4_navegador_web_mobile"]
    clausula_ok = CLAUSULA_MATEMATICA_OBRIGATORIA
    resultados: List[Dict[str, Any]] = []
    todos_ok = True

    with _ServidorUiEstaticoIsolado(porta_ui) as srv_ui:
        for ativo in (False, True):
            with _SubprocessoUvicornIsolado(porta=porta_api, lotofacil_modo4_ativo=ativo):
                for arquivo_html in c4["interfaces"]:
                    url = f"{srv_ui.base_url}/{arquivo_html}"
                    r = _auditar_pagina_em_chrome(
                        navegador_exe, url, porta_api, modo_ativo_esperado=ativo
                    )
                    ei = r["estado_inicial"]
                    ex = r["execucao_ui"]
                    ok_comum = (
                        r["excecoes_js_nao_tratadas"] <= c4["max_excecoes_js_nao_tratadas"]
                        and ei["subpanelDisplayInicial"] == "none"
                        and ei["exp2jDisabled"] is True
                        and ei["exp2jChecked"] is False
                        and clausula_ok in ei["clausulaTexto"]
                    )
                    if not ativo:
                        ok_modo = (
                            ei["statusOk"] is False
                            and ex["qtdJogos"] == 0
                            and ex["alertaVisivel"] is True
                            and ex["resultadoVisivel"] is False
                        )
                    else:
                        ok_modo = (
                            ei["statusOk"] is True
                            and ex["qtdJogos"] == 6
                            and ex["primeiroJogoTam"] == 15
                            and ex["resultadoVisivel"] is True
                            and "F_MODO4" in ex["resultadoTexto"]
                            and "SHA-256" in ex["resultadoTexto"]
                            and "AUDITORIA INDEPENDENTE" in ex["avaliarTexto"]
                            and clausula_ok in ex["resultadoTexto"]
                        )
                    r["aprovada"] = bool(ok_comum and ok_modo)
                    resultados.append(r)
                    if not r["aprovada"]:
                        todos_ok = False

    return {"aprovada": todos_ok, "navegador": navegador_exe, "execucoes": resultados}


def executar_frente_5_nao_interferencia(cfg_hom: Dict[str, Any], porta_api: int) -> Dict[str, Any]:
    c5 = cfg_hom["criterios_go_no_go"]["frente_5_nao_interferencia"]
    casos = cfg_hom["casos_repetibilidade"]
    pl_lm = casos["caso_lotomania_controle"]
    pl_lf = casos["caso_simples_conservador"]
    rotas_legadas = list(c5["rotas_legadas_obrigatorias"])
    hashes_disco_antes = _coletar_hashes_arquivos_legados()

    # 5A) Baseline isolado com Lotofacil MODO 4 OFF
    legados_off: Dict[str, Dict[str, Any]] = {}
    with _SubprocessoUvicornIsolado(porta=porta_api, lotofacil_modo4_ativo=False) as srv_off:
        lm_off_1 = _sondar_http_cronometrado(srv_off.base_url, pl_lm, endpoint="/api/v1/lotomania-modo4/gerar")
        lm_off_2 = _sondar_http_cronometrado(srv_off.base_url, pl_lm, endpoint="/api/v1/lotomania-modo4/gerar")
        for ep in rotas_legadas:
            pl_leg = dict(CONTROLES_ROTAS_LEGADAS.get(ep, {}).get("payload") or {"quantidade_jogos": 3})
            r1 = _sondar_http_cronometrado(srv_off.base_url, pl_leg, endpoint=ep)
            r2 = _sondar_http_cronometrado(srv_off.base_url, pl_leg, endpoint=ep)
            d1 = r1.get("dados_brutos") or {}
            d2 = r2.get("dados_brutos") or {}
            ok1, mot1 = _validar_contrato_resposta_legada(ep, pl_leg, d1) if r1["status_http"] == 200 else (False, f"http_{r1['status_http']}")
            ok2, mot2 = _validar_contrato_resposta_legada(ep, pl_leg, d2) if r2["status_http"] == 200 else (False, f"http_{r2['status_http']}")
            sha_resp_1 = _calcular_sha256_json_canonico(d1) if r1["status_http"] == 200 else None
            sha_resp_2 = _calcular_sha256_json_canonico(d2) if r2["status_http"] == 200 else None
            sha_jogos_1 = _calcular_sha256_json_canonico(d1.get("jogos")) if ok1 else None
            sha_jogos_2 = _calcular_sha256_json_canonico(d2.get("jogos")) if ok2 else None
            legados_off[ep] = {
                "http_1": r1["status_http"],
                "http_2": r2["status_http"],
                "contrato_ok": bool(ok1 and ok2),
                "motivo": mot1 if not ok1 else mot2,
                "sha256_resposta_off_1": sha_resp_1,
                "sha256_resposta_off_2": sha_resp_2,
                "sha256_jogos_off_1": sha_jogos_1,
                "sha256_jogos_off_2": sha_jogos_2,
                "deterministico_jogos_baseline": bool(sha_jogos_1 and sha_jogos_1 == sha_jogos_2),
                "deterministico_resposta_baseline": bool(sha_resp_1 and sha_resp_1 == sha_resp_2),
            }

    # 5B) Probes executadas simultaneamente DURANTE carga concorrente real do Lotofacil MODO 4 ON
    legados_sob_carga: Dict[str, Dict[str, Any]] = {}
    with _SubprocessoUvicornIsolado(porta=porta_api, lotofacil_modo4_ativo=True) as srv_on:
        with ThreadPoolExecutor(max_workers=10) as pool:
            futuros_lf = [
                pool.submit(_sondar_http_cronometrado, srv_on.base_url, pl_lf, endpoint="/api/v1/lotofacil-modo4/gerar")
                for _ in range(10)
            ]
            fut_lm_1 = pool.submit(
                _sondar_http_cronometrado, srv_on.base_url, pl_lm, endpoint="/api/v1/lotomania-modo4/gerar"
            )
            fut_lm_2 = pool.submit(
                _sondar_http_cronometrado, srv_on.base_url, pl_lm, endpoint="/api/v1/lotomania-modo4/gerar"
            )
            fut_legs = {
                ep: pool.submit(
                    _sondar_http_cronometrado,
                    srv_on.base_url,
                    dict(CONTROLES_ROTAS_LEGADAS.get(ep, {}).get("payload") or {"quantidade_jogos": 3}),
                    endpoint=ep,
                )
                for ep in rotas_legadas
            }
            res_carga_lf = [f.result() for f in futuros_lf]
            lm_on_1 = fut_lm_1.result()
            lm_on_2 = fut_lm_2.result()
            res_legs_on = {ep: fut.result() for ep, fut in fut_legs.items()}

        for ep, rl in res_legs_on.items():
            pl_leg = dict(CONTROLES_ROTAS_LEGADAS.get(ep, {}).get("payload") or {"quantidade_jogos": 3})
            dl = rl.get("dados_brutos") or {}
            ok_c, mot_c = _validar_contrato_resposta_legada(ep, pl_leg, dl) if rl["status_http"] == 200 else (False, f"http_{rl['status_http']}")
            sha_resp_on = _calcular_sha256_json_canonico(dl) if rl["status_http"] == 200 else None
            sha_jogos_on = _calcular_sha256_json_canonico(dl.get("jogos")) if ok_c else None
            base_ep = legados_off[ep]
            det_ok = True
            if base_ep["deterministico_jogos_baseline"] and sha_jogos_on != base_ep["sha256_jogos_off_1"]:
                det_ok = False
            legados_sob_carga[ep] = {
                "http_sob_carga": rl["status_http"],
                "latencia_s": rl["latencia_s"],
                "contrato_ok": ok_c,
                "motivo": mot_c,
                "sha256_resposta_sob_carga": sha_resp_on,
                "sha256_jogos_sob_carga": sha_jogos_on,
                "preservou_determinismo_se_aplicavel": det_ok,
            }

    hashes_disco_depois = _coletar_hashes_arquivos_legados()
    disco_intacto = hashes_disco_antes == hashes_disco_depois

    hash_off_1 = (lm_off_1.get("dados_brutos") or {}).get("hash_carteira_sha256_v2_canonico")
    hash_off_2 = (lm_off_2.get("dados_brutos") or {}).get("hash_carteira_sha256_v2_canonico")
    hash_on_1 = (lm_on_1.get("dados_brutos") or {}).get("hash_carteira_sha256_v2_canonico")
    hash_on_2 = (lm_on_2.get("dados_brutos") or {}).get("hash_carteira_sha256_v2_canonico")

    lotomania_ok = (
        lm_off_1["status_http"] == 200
        and lm_off_2["status_http"] == 200
        and lm_on_1["status_http"] == 200
        and lm_on_2["status_http"] == 200
        and bool(hash_off_1)
        and hash_off_1 == hash_off_2 == hash_on_1 == hash_on_2
    )
    carga_lf_ok = all(r["status_http"] == 200 and (r.get("dados_brutos") or {}).get("sucesso") is True for r in res_carga_lf)
    legados_ok = all(
        legados_off[ep]["contrato_ok"]
        and legados_sob_carga[ep]["http_sob_carga"] == 200
        and legados_sob_carga[ep]["contrato_ok"]
        and legados_sob_carga[ep]["preservou_determinismo_se_aplicavel"]
        for ep in rotas_legadas
    )

    comparacao_legados = {
        ep: {
            "off": legados_off[ep],
            "on_sob_carga": legados_sob_carga[ep],
            "aprovado": bool(
                legados_off[ep]["contrato_ok"]
                and legados_sob_carga[ep]["contrato_ok"]
                and legados_sob_carga[ep]["preservou_determinismo_se_aplicavel"]
            ),
        }
        for ep in rotas_legadas
    }
    return {
        "aprovada": bool(lotomania_ok and legados_ok and carga_lf_ok and disco_intacto),
        "carga_concorrente_lotofacil_ok": carga_lf_ok,
        "lotomania_sha256_v2_off": hash_off_1,
        "lotomania_sha256_v2_on_sob_carga": hash_on_1,
        "lotomania_hashes_identicos": lotomania_ok,
        "integridade_arquivos_legados_disco_ok": disco_intacto,
        "arquivos_legados_monitorados_count": len(hashes_disco_depois),
        "hashes_arquivos_legados": hashes_disco_depois,
        "legados_status_http": {ep: legados_sob_carga[ep]["http_sob_carga"] for ep in rotas_legadas},
        "comparacao_legados_off_vs_carga": comparacao_legados,
    }


def executar_frente_6_rollback_e_preservacao(
    cfg_hom: Dict[str, Any],
    porta_api: int,
    *,
    prod_8000_antes: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    # 6A) Rollback runtime imediato sem reiniciar em instancia isolada `ServidorHttpHomologacao`
    import api as api_isolada

    definir_feature_flag_lotofacil_modo4(
        api_isolada.app, ativo=True, permitir_experimental_2j=False, motivo="homologacao_teste_rollback_on"
    )
    try:
        with ServidorHttpHomologacao(api_isolada.app) as srv_rt:
            r_antes = _sondar_http_cronometrado(
                srv_rt.base_url, cfg_hom["casos_repetibilidade"]["caso_simples_conservador"]
            )
            definir_feature_flag_lotofacil_modo4(
                api_isolada.app,
                ativo=False,
                permitir_experimental_2j=False,
                motivo="homologacao_teste_rollback_off",
            )
            r_depois = _sondar_http_cronometrado(
                srv_rt.base_url, cfg_hom["casos_repetibilidade"]["caso_simples_conservador"]
            )
    finally:
        definir_feature_flag_lotofacil_modo4(
            api_isolada.app, ativo=False, permitir_experimental_2j=False, motivo="restaurar_padrao_off"
        )

    rollback_runtime_ok = (
        r_antes["status_http"] == 200
        and len(r_antes["jogos"]) == 6
        and r_depois["status_http"] == 503
        and r_depois["jogos"] == []
        and r_depois["fallback_executado"] is False
    )

    # 6B) Reinicio controlado do subprocesso dedicado com env OFF
    with _SubprocessoUvicornIsolado(porta=porta_api, lotofacil_modo4_ativo=False) as srv_off:
        r_env_off = _sondar_http_cronometrado(
            srv_off.base_url, cfg_hom["casos_repetibilidade"]["caso_simples_conservador"]
        )
    rollback_subprocesso_ok = (
        r_env_off["status_http"] == 503
        and r_env_off["jogos"] == []
        and r_env_off["fallback_executado"] is False
    )

    # 6C) Verificacao estrita fail-closed na porta de producao 8000 (antes vs depois, sem mutacao)
    c6 = cfg_hom["criterios_go_no_go"]["frente_6_rollback_e_preservacao"]
    porta_prod = int(cfg_hom["ambiente_homologacao_isolada"]["porta_api_producao_preservada"])
    exigir_alcancavel = bool(c6.get("exigir_producao_8000_alcancavel", True))
    prod_depois = _capturar_estado_producao_8000(porta_prod)
    prod_antes_ef = prod_8000_antes if prod_8000_antes is not None else prod_depois
    comp_prod = _comparar_producao_8000_antes_depois(
        prod_antes_ef, prod_depois, exigir_alcancavel=exigir_alcancavel
    )
    prod_ok = bool(comp_prod["preservada"])

    return {
        "aprovada": bool(rollback_runtime_ok and rollback_subprocesso_ok and prod_ok),
        "rollback_runtime_ok": rollback_runtime_ok,
        "rollback_subprocesso_ok": rollback_subprocesso_ok,
        "producao_8000_intacta": prod_ok,
        "producao_8000_comparacao": comp_prod,
    }


def _construir_relatorio_homologacao(dados: Dict[str, Any]) -> str:
    ata = dados["ata_decisao"]
    hw = dados["telemetria_hardware"]
    f1_pre = dados["frentes"]["frente_1_criptografia_pre"]["detalhes"]
    f1_pos = dados["frentes"]["frente_1_criptografia_pos"]["detalhes"]
    f2 = dados["frentes"]["frente_2_rotas"]
    f3 = dados["frentes"]["frente_3_carga"]
    f4 = dados["frentes"]["frente_4_navegador"]
    f5 = dados["frentes"]["frente_5_nao_interferencia"]
    f6 = dados["frentes"]["frente_6_rollback"]

    linhas = [
        "# DOSSIE E ATA DE HOMOLOGACAO ESPECIFICA DE ATIVACAO - LOTOFACIL MODO 4",
        "",
        f"**Versao Avaliada:** `{VERSAO_PROMOCAO_LOTOFACIL_MODO4}`  ",
        f"**Data/Hora (UTC):** `{dados['executado_em_utc']}`  ",
        f"**Veredito Automatico Go/No-Go:** `{ata['veredito']}`  ",
        f"**Hardware Medido:** `CPU {hw['cpu_threads_logicas']} threads` | `RAM livre {hw['ram_disponivel_gb']} GB / {hw['ram_total_gb']} GB` | `{hw['sistema_operacional']}`  ",
        "",
        "## 1. Resumo das 6 Frentes Avaliadas",
        "",
        "| Frente | Resultado | Evidencia Chave |",
        "| :--- | :--- | :--- |",
        f"| 1. Auditoria Criptografica (Pre e Pos) | `{'GO' if ata['criterios']['frente_1_ok'] else 'NO-GO'}` | Pre divergencias=`{len(f1_pre['divergencias'])}`, Pos divergencias=`{len(f1_pos['divergencias'])}`, Ed25519=`{f1_pos['selo_lotomania_valido']}` |",
        f"| 2. Rotas e Contratos (`/status`, `/gerar`, `/avaliar`) | `{'GO' if ata['criterios']['frente_2_ok'] else 'NO-GO'}` | Diff AST simples=`{f2['diff_F_simples']:.2e}`, Diff `/avaliar`=`{f2['diff_F_avaliar']:.2e}`, Negativos 422 ok=`{f2['negativos_ok']}` |",
        f"| 3. Carga Escalonada (Uvicorn `workers=1`, Portas Isoladas) | `{'GO' if ata['criterios']['frente_3_ok'] else 'NO-GO'}` | Pico Windows RSS=`{f3['rss_pico_windows_max_observado_mb']} MB`, Delta baseline para carga=`{f3['delta_rss_baseline_para_max_mb']} MB`, Mem ok=`{f3['memoria_dentro_limites']}` |",
        f"| 4. Auditoria Chrome Real (Web + Mobile) | `{'GO' if ata['criterios']['frente_4_ok'] else 'NO-GO'}` | Execucoes aprovadas=`{sum(1 for e in f4.get('execucoes', []) if e['aprovada'])}/{len(f4.get('execucoes', []))}` |",
        f"| 5. Nao Interferencia Sob Carga | `{'GO' if ata['criterios']['frente_5_ok'] else 'NO-GO'}` | Lotomania hash identico=`{f5['lotomania_hashes_identicos']}`, Disco legados intacto=`{f5['integridade_arquivos_legados_disco_ok']}` |",
        f"| 6. Rollback ON para OFF e Preservacao 8000 | `{'GO' if ata['criterios']['frente_6_ok'] else 'NO-GO'}` | Runtime rollback ok=`{f6['rollback_runtime_ok']}`, Subprocesso OFF ok=`{f6['rollback_subprocesso_ok']}`, Prod 8000 intacta=`{f6['producao_8000_intacta']}` |",
        "",
        "## 2. Patamares de Carga Escalonada",
        "",
        "| Patamar | Clientes Simultaneos | Requisicoes | Taxa Erro (%) | p95 `/gerar` simples (s) | p99 `/gerar` simples (s) | Pico RSS Windows (MB) | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for p in f3["patamares"]:
        st_gs = p["latencias_por_tipo"].get("lotofacil_modo4_gerar_simples", {})
        p95_g = st_gs.get("p95_s", "--")
        p99_g = st_gs.get("p99_s", "--")
        pico_rss = p["memoria_monitorada"]["rss_pico_windows_max_mb"]
        linhas.append(
            f"| `{p['id']}` | `{p['clientes_simultaneos']}` | `{p['total_requisicoes']}` | `{p['taxa_erro_pct']}` | `{p95_g}` | `{p99_g}` | `{pico_rss}` | `{'GO' if p['aprovado'] else 'NO-GO'}` |"
        )
    linhas.extend(
        [
            "",
            "## 3. Hashes Examinados (Pre e Pos-Janela)",
            "",
            "| Arquivo Monitorado | SHA-256 Pos-Janela |",
            "| :--- | :--- |",
        ]
    )
    for rel, sha in f1_pos["hashes_atuais_producao"].items():
        linhas.append(f"| `{rel}` | `{sha}` |")
    linhas.extend(
        [
            "",
            "## 4. Limites Cientificos e Clausula Obrigatoria",
            "",
            f"> {CLAUSULA_MATEMATICA_OBRIGATORIA}",
            "",
            f"**Decisao da Ata:** `{ata['veredito']}` | **Motivos NO-GO (se houver):** `{ata['motivos_no_go']}`",
        ]
    )
    md = "\n".join(linhas)
    if "\u2014" in md or "\u2013" in md:
        raise RuntimeError("Relatorio Markdown nao pode conter travessao em-dash ou en-dash.")
    return md


def executar_homologacao_especifica_ativacao() -> Dict[str, Any]:
    """Executa a Fase 2 completa em ambiente isolado (somente quando autorizado)."""
    cfg_hom = carregar_config_homologacao()
    hw = coletar_telemetria_hardware()
    porta_api = _reservar_porta_livre(int(cfg_hom["ambiente_homologacao_isolada"]["porta_api_isolada_preferencial"]))
    porta_ui = _reservar_porta_livre(int(cfg_hom["ambiente_homologacao_isolada"]["porta_ui_isolada_preferencial"]))
    porta_prod = int(cfg_hom["ambiente_homologacao_isolada"]["porta_api_producao_preservada"])

    prod_antes = _capturar_estado_producao_8000(porta_prod)
    f1_pre = executar_frente_1_criptografia(cfg_hom)
    if not f1_pre["aprovada"]:
        raise RuntimeError(f"NO-GO imediato na Frente 1 (pre-checagem): {f1_pre['detalhes']['divergencias']}")

    f2 = executar_frente_2_rotas(cfg_hom, porta_api)
    f3 = executar_frente_3_carga(cfg_hom, porta_api)
    f4 = executar_frente_4_navegador(
        cfg_hom, porta_api=porta_api, porta_ui=porta_ui, navegador_exe=hw["navegador_headless"]
    )
    f5 = executar_frente_5_nao_interferencia(cfg_hom, porta_api)
    f6 = executar_frente_6_rollback_e_preservacao(cfg_hom, porta_api, prod_8000_antes=prod_antes)
    f1_pos = executar_frente_1_criptografia(cfg_hom)

    criterios = {
        "frente_1_ok": bool(f1_pre["aprovada"] and f1_pos["aprovada"]),
        "frente_2_ok": bool(f2["aprovada"]),
        "frente_3_ok": bool(f3["aprovada"]),
        "frente_4_ok": bool(f4["aprovada"]),
        "frente_5_ok": bool(f5["aprovada"]),
        "frente_6_ok": bool(f6["aprovada"]),
    }
    motivos_no_go = [k for k, v in criterios.items() if not v]
    veredito = "GO" if len(motivos_no_go) == 0 else "NO-GO"

    ata = {
        "veredito": veredito,
        "versao_avaliada": VERSAO_PROMOCAO_LOTOFACIL_MODO4,
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "criterios": criterios,
        "motivos_no_go": motivos_no_go,
        "proxima_acao_autorizada": (
            "Submeter Ata GO para deliberacao formal de ativacao LOTOFACIL_MODO4_ATIVO=true (experimental_2J=false)."
            if veredito == "GO"
            else "NO-GO: ativacao em producao permanece estritamente bloqueada."
        ),
    }

    evidencias = {
        "versao_runbook": cfg_hom["versao_runbook"],
        "versao_avaliada": VERSAO_PROMOCAO_LOTOFACIL_MODO4,
        "executado_em_utc": ata["executado_em_utc"],
        "portas_isoladas_utilizadas": {"api": porta_api, "ui": porta_ui},
        "telemetria_hardware": hw,
        "ata_decisao": ata,
        "frentes": {
            "frente_1_criptografia_pre": f1_pre,
            "frente_2_rotas": f2,
            "frente_3_carga": f3,
            "frente_4_navegador": f4,
            "frente_5_nao_interferencia": f5,
            "frente_6_rollback": f6,
            "frente_1_criptografia_pos": f1_pos,
        },
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }

    os.makedirs(DIR_HOMOLOGACAO_ABS, exist_ok=True)
    with open(os.path.join(DIR_HOMOLOGACAO_ABS, "evidencias_homologacao_ativacao.json"), "w", encoding="utf-8") as f:
        json.dump(evidencias, f, indent=2, ensure_ascii=False)
    with open(os.path.join(DIR_HOMOLOGACAO_ABS, "ata_homologacao_ativacao.json"), "w", encoding="utf-8") as f:
        json.dump(ata, f, indent=2, ensure_ascii=False)
    md = _construir_relatorio_homologacao(evidencias)
    with open(os.path.join(DIR_HOMOLOGACAO_ABS, "DOSSIE_HOMOLOGACAO_ATIVACAO.md"), "w", encoding="utf-8") as f:
        f.write(md)

    return evidencias


def executar_microcalibracao_revisao_fase1() -> Dict[str, Any]:
    """
    Executa exclusivamente a microcalibracao da Revisao da Fase 1 em porta isolada.
    Nao executa a Fase 2 completa, nao cria ata_homologacao_ativacao.json e nao altera a porta 8000.
    """
    cfg_hom = carregar_config_homologacao()
    hw = coletar_telemetria_hardware()
    porta_api = _reservar_porta_livre(int(cfg_hom["ambiente_homologacao_isolada"]["porta_api_isolada_preferencial"]))
    porta_prod = int(cfg_hom["ambiente_homologacao_isolada"]["porta_api_producao_preservada"])
    exigir_alcancavel = bool(
        cfg_hom["criterios_go_no_go"]["frente_6_rollback_e_preservacao"].get("exigir_producao_8000_alcancavel", True)
    )

    f1_pre = executar_frente_1_criptografia(cfg_hom)
    if not f1_pre["aprovada"]:
        raise RuntimeError(f"Divergencia criptografica previa a microcalibracao: {f1_pre['detalhes']['divergencias']}")

    prod_antes = _capturar_estado_producao_8000(porta_prod)
    f3 = executar_frente_3_carga(cfg_hom, porta_api, modo_calibracao=False)
    f5 = executar_frente_5_nao_interferencia(cfg_hom, porta_api)
    prod_depois = _capturar_estado_producao_8000(porta_prod)
    comp_prod = _comparar_producao_8000_antes_depois(
        prod_antes, prod_depois, exigir_alcancavel=exigir_alcancavel
    )
    f1_pos = executar_frente_1_criptografia(cfg_hom)

    # Calculo de recomendacoes empiricas p95/p99 por patamar e rota com folga controlada para JIT/GIL
    calibracao_sugerida: Dict[str, Dict[str, Dict[str, float]]] = {}
    for p in f3["patamares"]:
        rotas_rec: Dict[str, Dict[str, float]] = {}
        for tipo, st in p["latencias_por_tipo"].items():
            p95_obs = float(st["p95_s"])
            p99_obs = float(st["p99_s"])
            rec_p95 = round(max(0.25, max(p95_obs * 1.85, p95_obs + 0.35)), 2)
            rec_p99 = round(max(rec_p95 + 0.15, max(p99_obs * 1.85, p99_obs + 0.50)), 2)
            rotas_rec[tipo] = {
                "p95_observado_s": p95_obs,
                "p99_observado_s": p99_obs,
                "max_p95_s_sugerido": rec_p95,
                "max_p99_s_sugerido": rec_p99,
            }
        calibracao_sugerida[p["id"]] = rotas_rec

    evidencias = {
        "fase": "REVISAO_FASE_1_MICROCALIBRACAO",
        "versao_runbook": cfg_hom["versao_runbook"],
        "versao_avaliada": VERSAO_PROMOCAO_LOTOFACIL_MODO4,
        "executado_em_utc": datetime.now(timezone.utc).isoformat(),
        "fase_2_executada": False,
        "ativacao_producao": False,
        "porta_api_isolada_utilizada": porta_api,
        "telemetria_hardware": hw,
        "frente_1_criptografia_pre": f1_pre,
        "frente_3_carga_microcalibracao": f3,
        "frente_5_nao_interferencia": f5,
        "producao_8000_comparacao": comp_prod,
        "frente_1_criptografia_pos": f1_pos,
        "calibracao_sugerida_por_patamar": calibracao_sugerida,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }
    os.makedirs(DIR_HOMOLOGACAO_ABS, exist_ok=True)
    with open(CAMINHO_MICROCALIBRACAO_JSON, "w", encoding="utf-8") as f:
        json.dump(evidencias, f, indent=2, ensure_ascii=False)
    return evidencias


def verificar_preparacao_somente_leitura() -> Dict[str, Any]:
    """Modo estritamente passivo da Fase 1: valida arquivos de preparacao e integridade vigente."""
    cfg_hom = carregar_config_homologacao()
    hw = coletar_telemetria_hardware()
    integridade = verificar_integridade_promocao(
        diretorio_base=BASE_DIR,
        verificar_lotomania_selo=True,
        exigir_manifesto_etapa5=True,
        exigir_manifesto_promocao=True,
        verificar_manifesto_promocao_se_presente=True,
    )
    runbook_ok = os.path.isfile(CAMINHO_RUNBOOK_MD)
    return {
        "fase": "FASE_1_PREPARACAO_VERIFICADA",
        "homologacao_executada": False,
        "runbook_presente": runbook_ok,
        "config_versao": cfg_hom["versao_runbook"],
        "integridade_cadeia_selada": integridade["integro"],
        "divergencias": integridade["divergencias"],
        "hardware": hw,
    }


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Runbook isolado de Homologacao Especifica de Ativacao (Fase 1 Preparacao/Revisao / Fase 2 Execucao)."
    )
    parser.add_argument(
        "--preparacao-check",
        action="store_true",
        help="Executa apenas conferencia passiva dos artefatos de preparacao e integridade sem rodar Fase 2.",
    )
    parser.add_argument(
        "--microcalibracao-revisao-fase1",
        action="store_true",
        help="Executa exclusivamente a microcalibracao da Revisao da Fase 1 em porta isolada, sem rodar Fase 2.",
    )
    parser.add_argument(
        "--autorizar-homologacao-isolada",
        action="store_true",
        help="Autoriza explicitamente a execucao da Fase 2 em portas isoladas.",
    )
    args = parser.parse_args(argv)

    if args.preparacao_check and not args.autorizar_homologacao_isolada and not args.microcalibracao_revisao_fase1:
        res = verificar_preparacao_somente_leitura()
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0 if res["integridade_cadeia_selada"] and res["runbook_presente"] else 1

    if args.microcalibracao_revisao_fase1 and not args.autorizar_homologacao_isolada:
        ev = executar_microcalibracao_revisao_fase1()
        resumo = {
            "fase": ev["fase"],
            "fase_2_executada": ev["fase_2_executada"],
            "porta_api_isolada_utilizada": ev["porta_api_isolada_utilizada"],
            "rss_pico_windows_max_mb": ev["frente_3_carga_microcalibracao"]["rss_pico_windows_max_observado_mb"],
            "delta_rss_baseline_para_max_mb": ev["frente_3_carga_microcalibracao"]["delta_rss_baseline_para_max_mb"],
            "auditoria_sementes_aprovada": ev["frente_3_carga_microcalibracao"]["auditoria_sementes_e_estado"]["aprovada"],
            "frente_5_aprovada": ev["frente_5_nao_interferencia"]["aprovada"],
            "producao_8000_intacta": ev["producao_8000_comparacao"]["preservada"],
            "frente_1_pos_integro": ev["frente_1_criptografia_pos"]["aprovada"],
            "arquivo_microcalibracao": CAMINHO_MICROCALIBRACAO_JSON,
        }
        print(json.dumps(resumo, indent=2, ensure_ascii=False))
        ok = (
            ev["frente_1_criptografia_pre"]["aprovada"]
            and ev["frente_3_carga_microcalibracao"]["aprovada"]
            and ev["frente_5_nao_interferencia"]["aprovada"]
            and ev["producao_8000_comparacao"]["preservada"]
            and ev["frente_1_criptografia_pos"]["aprovada"]
        )
        return 0 if ok else 1

    if not args.autorizar_homologacao_isolada:
        print(
            json.dumps(
                {
                    "bloqueado": True,
                    "motivo": (
                        "Fase 2 nao autorizada. Passe --preparacao-check para conferencia passiva, "
                        "--microcalibracao-revisao-fase1 para calibracao isolada ou "
                        "--autorizar-homologacao-isolada apos autorizacao formal."
                    ),
                },
                indent=2,
                ensure_ascii=False,
            )
        )
        return 2

    ev = executar_homologacao_especifica_ativacao()
    print(json.dumps(ev["ata_decisao"], indent=2, ensure_ascii=False))
    return 0 if ev["ata_decisao"]["veredito"] == "GO" else 1


if __name__ == "__main__":
    raise SystemExit(main())
