# -*- coding: utf-8 -*-
"""
LOTOFACIL MODO 4 - RUNBOOK ISOLADO DE HOMOLOGACAO ESPECIFICA DE ATIVACAO (FASE 1 / PREPARACAO)
==================================================================================================
Script modular para verificacao de preparacao (`--preparacao-check`) e futura execucao isolada
da Homologacao Especifica de Ativacao (`--autorizar-homologacao-isolada`).

REGRAS DE SEGURANCA E GOVERNANCA:
1. Nao executa homologacao nem liga feature flag sem `--autorizar-homologacao-isolada`.
2. Nao modifica nenhum dos 7 arquivos selados em `manifesto_promocao_controlada.json`, nem
   os artefatos congelados das Etapas 1-5 ou o manifesto da Lotomania MODO 4.
3. Toda a bateria ativa (Fase 2) roda em subprocesso Uvicorn e servidor UI dedicados em portas
   isoladas (`18080` / `18081` ou livres), mantendo intacta a instancia `127.0.0.1:8000`.
4. Evidencias da janela sao gravadas exclusivamente em `auditoria/lotofacil_modo4/homologacao_ativacao/`.
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


def _calcular_estatisticas_latencia(latencias_s: Sequence[float]) -> Dict[str, float]:
    if not latencias_s:
        return {"min_s": 0.0, "media_s": 0.0, "p50_s": 0.0, "p95_s": 0.0, "p99_s": 0.0, "max_s": 0.0}
    ord_lat = sorted(float(x) for x in latencias_s)
    n = len(ord_lat)

    def _pct(p: float) -> float:
        idx = min(n - 1, max(0, math.ceil(p * n) - 1))
        return round(ord_lat[idx], 4)

    return {
        "min_s": round(ord_lat[0], 4),
        "media_s": round(sum(ord_lat) / n, 4),
        "p50_s": _pct(0.50),
        "p95_s": _pct(0.95),
        "p99_s": _pct(0.99),
        "max_s": round(ord_lat[-1], 4),
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
            f"uvicorn.run(api.app, host='127.0.0.1', port={self.porta}, log_level='warning', access_log=False)"
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


def _executar_patamar_carga(
    *,
    base_url: str,
    pid_servidor: int,
    tarefas: Sequence[Tuple[str, Callable[[], Dict[str, Any]]]],
    workers: int,
) -> Dict[str, Any]:
    mem_antes = medir_memoria_processo_windows(pid_servidor)
    t_ini = time.perf_counter()
    with ThreadPoolExecutor(max_workers=workers) as pool:
        resultados = list(pool.map(lambda item: (item[0], item[1]()), tarefas))
    duracao_total_s = round(time.perf_counter() - t_ini, 4)
    mem_depois = medir_memoria_processo_windows(pid_servidor)

    por_tipo: Dict[str, List[float]] = {}
    hashes_lf: set[str] = set()
    hashes_lm: set[str] = set()
    erros: List[Dict[str, Any]] = []

    for tipo, r in resultados:
        por_tipo.setdefault(tipo, []).append(float(r["latencia_s"]))
        if r["status_http"] != 200:
            erros.append({"tipo": tipo, "status_http": r["status_http"], "erro": r.get("erro")})
            continue
        dados = r.get("dados_brutos") or {}
        if tipo == "lotofacil_modo4_gerar":
            if not dados.get("sucesso") or dados.get("fallback_executado") is not False:
                erros.append({"tipo": tipo, "motivo": "contrato_gerar_violado"})
            elif dados.get("hash_carteira_sha256"):
                hashes_lf.add(dados["hash_carteira_sha256"])
        elif tipo == "lotomania_modo4_gerar":
            if dados.get("hash_carteira_sha256_v2_canonico"):
                hashes_lm.add(dados["hash_carteira_sha256_v2_canonico"])

    stats_por_tipo = {k: _calcular_estatisticas_latencia(v) for k, v in por_tipo.items()}
    total = len(resultados)
    return {
        "total_requisicoes": total,
        "workers_simultaneos": workers,
        "duracao_total_s": duracao_total_s,
        "erros_count": len(erros),
        "taxa_erro_pct": round(100.0 * len(erros) / max(1, total), 4),
        "amostra_erros": erros[:5],
        "latencias_por_tipo": stats_por_tipo,
        "hashes_unicos_lotofacil": len(hashes_lf),
        "hashes_unicos_lotomania": len(hashes_lm),
        "memoria_antes": mem_antes,
        "memoria_depois": mem_depois,
    }


def executar_frente_3_carga(cfg_hom: Dict[str, Any], porta_api: int) -> Dict[str, Any]:
    c3 = cfg_hom["criterios_go_no_go"]["frente_3_carga_escalonada"]
    casos = cfg_hom["casos_repetibilidade"]
    timeout_s = float(c3["timeout_por_requisicao_s"])
    pl_simples = casos["caso_simples_conservador"]
    pl_lm = casos["caso_lotomania_controle"]
    legados = cfg_hom["criterios_go_no_go"]["frente_5_nao_interferencia"]["rotas_legadas_obrigatorias"]

    patamares_res: List[Dict[str, Any]] = []
    todos_ok = True

    with _SubprocessoUvicornIsolado(porta=porta_api, lotofacil_modo4_ativo=True) as srv:
        pid = int(srv.proc.pid) if srv.proc else os.getpid()
        # Aquecimento unitario controlado para preparar carteira base de /avaliar
        r_seed = _sondar_http_cronometrado(srv.base_url, pl_simples, timeout_s=timeout_s)
        carteira_base = r_seed["jogos"]
        mem_base = medir_memoria_processo_windows(pid)

        for pat in c3["patamares"]:
            pid_id = pat["id"]
            workers = int(pat["workers_simultaneos"])
            tarefas: List[Tuple[str, Callable[[], Dict[str, Any]]]] = []
            if "distribuicao" not in pat:
                n_req = int(pat["total_requisicoes"])
                for _ in range(n_req):
                    tarefas.append(
                        (
                            "lotofacil_modo4_gerar",
                            lambda b=srv.base_url, p=pl_simples: _sondar_http_cronometrado(
                                b, p, timeout_s=timeout_s
                            ),
                        )
                    )
            else:
                dist = pat["distribuicao"]
                for _ in range(int(dist["lotofacil_modo4_gerar"])):
                    tarefas.append(
                        (
                            "lotofacil_modo4_gerar",
                            lambda b=srv.base_url, p=pl_simples: _sondar_http_cronometrado(
                                b, p, timeout_s=timeout_s
                            ),
                        )
                    )
                for _ in range(int(dist["lotofacil_modo4_avaliar"])):
                    tarefas.append(
                        (
                            "lotofacil_modo4_avaliar",
                            lambda b=srv.base_url, c=carteira_base: _sondar_http_cronometrado(
                                b, {"carteira": c}, endpoint="/api/v1/lotofacil-modo4/avaliar", timeout_s=timeout_s
                            ),
                        )
                    )
                for _ in range(int(dist["lotofacil_modo4_status"])):
                    tarefas.append(
                        (
                            "lotofacil_modo4_status",
                            lambda b=srv.base_url: _sondar_http_cronometrado(
                                b, endpoint="/api/v1/lotofacil-modo4/status", metodo="GET", timeout_s=timeout_s
                            ),
                        )
                    )
                for _ in range(int(dist["lotomania_modo4_gerar"])):
                    tarefas.append(
                        (
                            "lotomania_modo4_gerar",
                            lambda b=srv.base_url, p=pl_lm: _sondar_http_cronometrado(
                                b, p, endpoint="/api/v1/lotomania-modo4/gerar", timeout_s=timeout_s
                            ),
                        )
                    )
                for i in range(int(dist["motores_legados"])):
                    ep_leg = legados[i % len(legados)]
                    tarefas.append(
                        (
                            "motores_legados",
                            lambda b=srv.base_url, e=ep_leg: _sondar_http_cronometrado(
                                b, {"quantidade_jogos": 3}, endpoint=e, timeout_s=timeout_s
                            ),
                        )
                    )

            m = _executar_patamar_carga(base_url=srv.base_url, pid_servidor=pid, tarefas=tarefas, workers=workers)
            st_gerar = m["latencias_por_tipo"].get("lotofacil_modo4_gerar", {})
            ok_pat = m["taxa_erro_pct"] <= c3["max_taxa_erro_pct"]
            if pat.get("exigir_determinismo_hash_unico") and m["hashes_unicos_lotofacil"] != 1:
                ok_pat = False
            if "max_p95_s" in pat and st_gerar.get("p95_s", 999.0) > pat["max_p95_s"]:
                ok_pat = False
            if "max_p99_s" in pat and st_gerar.get("p99_s", 999.0) > pat["max_p99_s"]:
                ok_pat = False
            if "max_p95_gerar_s" in pat and st_gerar.get("p95_s", 999.0) > pat["max_p95_gerar_s"]:
                ok_pat = False
            if (
                "max_p95_status_s" in pat
                and m["latencias_por_tipo"].get("lotofacil_modo4_status", {}).get("p95_s", 999.0)
                > pat["max_p95_status_s"]
            ):
                ok_pat = False
            if (
                "max_p95_legados_s" in pat
                and m["latencias_por_tipo"].get("motores_legados", {}).get("p95_s", 999.0)
                > pat["max_p95_legados_s"]
            ):
                ok_pat = False

            m["id"] = pid_id
            m["aprovado"] = ok_pat
            patamares_res.append(m)
            if not ok_pat:
                todos_ok = False

    lim_mem = c3["limites_memoria_processo_isolado"]
    rss_max_obs = max(p["memoria_depois"]["rss_atual_mb"] for p in patamares_res)
    delta_rss_p1_p3 = round(
        patamares_res[-1]["memoria_depois"]["rss_atual_mb"] - patamares_res[0]["memoria_depois"]["rss_atual_mb"],
        2,
    )
    mem_ok = rss_max_obs <= lim_mem["max_rss_absoluto_mb"] and delta_rss_p1_p3 <= lim_mem["max_crescimento_rss_patamar1_para_patamar3_mb"]

    return {
        "aprovada": bool(todos_ok and mem_ok),
        "memoria_warmup": mem_base,
        "rss_max_observado_mb": rss_max_obs,
        "delta_rss_p1_para_p3_mb": delta_rss_p1_p3,
        "memoria_dentro_limites": mem_ok,
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
                const statusOk = await window.ui._atualizarStatusServidorLotofacilModo4();
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
                const tabBtn = document.getElementById('tab-btn-lotofacil-modo4');
                if (tabBtn) tabBtn.click();
                const inputQtd = document.getElementById('input-qtd-jogos-lotofacil-modo4');
                if (inputQtd) inputQtd.value = '6';
                await window.ui._executarGeracaoLotofacilModo4();
                const jogos = Array.isArray(window.ui.currentGeneratedGames) ? window.ui.currentGeneratedGames : [];
                const alerta = document.getElementById('alerta-indisponivel-lotofacil-modo4');
                const contRes = document.getElementById('container-resultado-lotofacil-modo4');
                let avaliarTexto = '';
                if (jogos.length > 0 && document.getElementById('btn-avaliar-lotofacil-modo4')) {
                    await window.ui._avaliarCarteiraLotofacilModo4();
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
    pl_lm = cfg_hom["casos_repetibilidade"]["caso_lotomania_controle"]

    with _SubprocessoUvicornIsolado(porta=porta_api, lotofacil_modo4_ativo=False) as srv_off:
        lm_off = _sondar_http_cronometrado(
            srv_off.base_url, pl_lm, endpoint="/api/v1/lotomania-modo4/gerar"
        )

    legados_status = {}
    with _SubprocessoUvicornIsolado(porta=porta_api, lotofacil_modo4_ativo=True) as srv_on:
        lm_on = _sondar_http_cronometrado(
            srv_on.base_url, pl_lm, endpoint="/api/v1/lotomania-modo4/gerar"
        )
        for ep in c5["rotas_legadas_obrigatorias"]:
            rl = _sondar_http_cronometrado(srv_on.base_url, {"quantidade_jogos": 3}, endpoint=ep)
            legados_status[ep] = rl["status_http"]

    hash_off = (lm_off.get("dados_brutos") or {}).get("hash_carteira_sha256_v2_canonico")
    hash_on = (lm_on.get("dados_brutos") or {}).get("hash_carteira_sha256_v2_canonico")
    ok = (
        lm_off["status_http"] == 200
        and lm_on["status_http"] == 200
        and bool(hash_off)
        and hash_off == hash_on
        and all(st == 200 for st in legados_status.values())
    )
    return {
        "aprovada": ok,
        "lotomania_sha256_v2_off": hash_off,
        "lotomania_sha256_v2_on": hash_on,
        "lotomania_hashes_identicos": bool(hash_off and hash_off == hash_on),
        "legados_status_http": legados_status,
    }


def executar_frente_6_rollback_e_preservacao(cfg_hom: Dict[str, Any], porta_api: int) -> Dict[str, Any]:
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

    # 6C) Verificacao somente-leitura na porta de producao 8000 (nao modifica nada)
    porta_prod = int(cfg_hom["ambiente_homologacao_isolada"]["porta_api_producao_preservada"])
    prod_url = f"http://127.0.0.1:{porta_prod}"
    h_prod = _sondar_http_cronometrado(prod_url, endpoint="/health", metodo="GET", timeout_s=2.0)
    if h_prod["status_http"] == 200 and isinstance(h_prod.get("dados_brutos"), dict):
        l4_prod = h_prod["dados_brutos"].get("lotofacil_modo4", {})
        prod_ok = (
            l4_prod.get("disponivel") is False
            and l4_prod.get("feature_flag_ativa") is False
            and l4_prod.get("integridade_verificada") is True
        )
        prod_estado = {"alcancavel": True, "disponivel": l4_prod.get("disponivel"), "feature_flag_ativa": l4_prod.get("feature_flag_ativa")}
    else:
        prod_ok = True
        prod_estado = {"alcancavel": False, "nota": "Instancia 8000 nao estava em execucao durante sondagem."}

    return {
        "aprovada": bool(rollback_runtime_ok and rollback_subprocesso_ok and prod_ok),
        "rollback_runtime_ok": rollback_runtime_ok,
        "rollback_subprocesso_ok": rollback_subprocesso_ok,
        "producao_8000_intacta": prod_ok,
        "producao_8000_observada": prod_estado,
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
        f"| 3. Carga Escalonada (Portas Isoladas) | `{'GO' if ata['criterios']['frente_3_ok'] else 'NO-GO'}` | RSS max=`{f3['rss_max_observado_mb']} MB`, Delta P1-P3=`{f3['delta_rss_p1_para_p3_mb']} MB`, Mem ok=`{f3['memoria_dentro_limites']}` |",
        f"| 4. Auditoria Chrome Real (Web + Mobile) | `{'GO' if ata['criterios']['frente_4_ok'] else 'NO-GO'}` | Execucoes aprovadas=`{sum(1 for e in f4.get('execucoes', []) if e['aprovada'])}/{len(f4.get('execucoes', []))}` |",
        f"| 5. Nao Interferencia Sob Carga | `{'GO' if ata['criterios']['frente_5_ok'] else 'NO-GO'}` | Lotomania hash identico=`{f5['lotomania_hashes_identicos']}`, Legados HTTP 200=`{all(v == 200 for v in f5['legados_status_http'].values())}` |",
        f"| 6. Rollback ON para OFF e Preservacao 8000 | `{'GO' if ata['criterios']['frente_6_ok'] else 'NO-GO'}` | Runtime rollback ok=`{f6['rollback_runtime_ok']}`, Subprocesso OFF ok=`{f6['rollback_subprocesso_ok']}`, Prod 8000 intacta=`{f6['producao_8000_intacta']}` |",
        "",
        "## 2. Patamares de Carga Escalonada",
        "",
        "| Patamar | Workers | Requisicoes | Taxa Erro (%) | p95 `/gerar` (s) | RSS Final (MB) | Status |",
        "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
    ]
    for p in f3["patamares"]:
        p95_g = p["latencias_por_tipo"].get("lotofacil_modo4_gerar", {}).get("p95_s", "--")
        linhas.append(
            f"| `{p['id']}` | `{p['workers_simultaneos']}` | `{p['total_requisicoes']}` | `{p['taxa_erro_pct']}` | `{p95_g}` | `{p['memoria_depois']['rss_atual_mb']}` | `{'GO' if p['aprovado'] else 'NO-GO'}` |"
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

    f1_pre = executar_frente_1_criptografia(cfg_hom)
    if not f1_pre["aprovada"]:
        raise RuntimeError(f"NO-GO imediato na Frente 1 (pre-checagem): {f1_pre['detalhes']['divergencias']}")

    f2 = executar_frente_2_rotas(cfg_hom, porta_api)
    f3 = executar_frente_3_carga(cfg_hom, porta_api)
    f4 = executar_frente_4_navegador(
        cfg_hom, porta_api=porta_api, porta_ui=porta_ui, navegador_exe=hw["navegador_headless"]
    )
    f5 = executar_frente_5_nao_interferencia(cfg_hom, porta_api)
    f6 = executar_frente_6_rollback_e_preservacao(cfg_hom, porta_api)
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
        description="Runbook isolado de Homologacao Especifica de Ativacao (Fase 1 Preparacao / Fase 2 Execucao)."
    )
    parser.add_argument(
        "--preparacao-check",
        action="store_true",
        help="Executa apenas conferencia passiva dos artefatos de preparacao e integridade sem rodar Fase 2.",
    )
    parser.add_argument(
        "--autorizar-homologacao-isolada",
        action="store_true",
        help="Autoriza explicitamente a execucao da Fase 2 em portas isoladas.",
    )
    args = parser.parse_args(argv)

    if args.preparacao_check and not args.autorizar_homologacao_isolada:
        res = verificar_preparacao_somente_leitura()
        print(json.dumps(res, indent=2, ensure_ascii=False))
        return 0 if res["integridade_cadeia_selada"] and res["runbook_presente"] else 1

    if not args.autorizar_homologacao_isolada:
        print(
            json.dumps(
                {
                    "bloqueado": True,
                    "motivo": (
                        "Fase 2 nao autorizada. Passe --preparacao-check para conferencia passiva "
                        "ou --autorizar-homologacao-isolada apos autorizacao formal."
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
