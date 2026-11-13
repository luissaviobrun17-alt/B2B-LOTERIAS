# -*- coding: utf-8 -*-
"""
GERENCIADOR DE JOBS ISOLADOS - LOTOMANIA | MODO 4 (v1.2)
========================================================
Executa geracoes assincronas do motor matematico selado MotorLotomaniaModo4 em
subprocesso Python dedicado por job, preservando:
1. Zero alteracao no nucleo selado `motor_lotomania_modo4.py` (Ed25519 + SHA-256).
2. Isolamento do GIL da API FastAPI/Uvicorn (`/health`, polling e demais motores
   permanecem responsivos mesmo durante geracoes de 10.000 jogos).
3. Regime fail-closed estrito: falha de integridade retorna HTTP 503 e 0 jogos;
   zero fallback local/aleatorio e pos-validacao integral das 50 dezenas.
4. Cancelamento real do subprocesso trabalhador e limpeza automatica em memoria/disco.
"""

from __future__ import annotations

import argparse
import atexit
from dataclasses import dataclass, field
from datetime import datetime, timezone
import json
import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from typing import Any, Dict, Optional, Tuple
import uuid

from verificador_selo_modo4 import IntegridadeModo4Error, verificar_selo_modo4


BASE_DIR_PADRAO = os.path.dirname(os.path.abspath(__file__))


def _agora_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _garantir_fluxos_worker() -> None:
    """Evita AttributeError quando o worker herda pythonw.exe com stdout/stderr None."""
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def validar_e_serializar_resultado_lotomania_modo4(
    resultado: Any,
    quantidade_esperada: int,
    engine_cls: Any,
) -> Dict[str, Any]:
    """
    Valida rigorosamente a carteira retornada pelo MotorLotomaniaModo4 e converte
    valores nao finitos via `serializar_resposta_api`.
    """
    if not isinstance(resultado, dict) or not resultado.get("sucesso"):
        raise RuntimeError("Falha estrutural: o motor MODO 4 nao retornou status de sucesso.")
    jogos = resultado.get("jogos", [])
    if len(jogos) != quantidade_esperada:
        raise RuntimeError(
            f"Discrepancia quantitativa: esperados {quantidade_esperada} jogos, entregues {len(jogos)}."
        )
    for idx, jg in enumerate(jogos):
        if not isinstance(jg, list) or len(jg) != 50 or len(set(jg)) != 50:
            raise RuntimeError(f"Jogo {idx + 1} na resposta nao contem 50 dezenas distintas.")
        if not all(type(n) is int and 1 <= n <= 100 for n in jg):
            raise RuntimeError(f"Jogo {idx + 1} na resposta contem dezenas fora do dominio [1..100].")
    return engine_cls.serializar_resposta_api(resultado)


def _escrever_json_atomico(caminho_final: str, objeto: Any) -> None:
    pasta = os.path.dirname(os.path.abspath(caminho_final))
    os.makedirs(pasta, exist_ok=True)
    caminho_tmp = f"{caminho_final}.{uuid.uuid4().hex[:8]}.tmp"
    dados = json.dumps(objeto, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    with open(caminho_tmp, "w", encoding="utf-8") as fh:
        fh.write(dados)
    os.replace(caminho_tmp, caminho_final)


def _executar_worker_cli(spec_path: str, output_path: str, error_path: str) -> int:
    """Ponto de entrada do subprocesso trabalhador isolado para um job unico."""
    _garantir_fluxos_worker()
    with open(spec_path, "r", encoding="utf-8") as fh:
        spec = json.load(fh)

    diretorio_base = spec["diretorio_base"]
    if diretorio_base not in sys.path:
        sys.path.insert(0, diretorio_base)

    try:
        from motor_lotomania_modo4 import MotorLotomaniaModo4

        verificar_selo_modo4(
            diretorio_base=diretorio_base,
            parametros_runtime=MotorLotomaniaModo4.obter_parametros_runtime(),
        )
        motor = MotorLotomaniaModo4(verificar_selo=True, diretorio_base=diretorio_base)
        resultado = motor.gerar_carteira_otimizada_cobertura(
            quantidade_jogos=int(spec["quantidade_jogos"]),
            seed=spec.get("seed"),
            permitir_espelhos=bool(spec["permitir_espelhos"]),
            trace=bool(spec.get("trace", False)),
        )
        payload = validar_e_serializar_resultado_lotomania_modo4(
            resultado,
            int(spec["quantidade_jogos"]),
            MotorLotomaniaModo4,
        )
        _escrever_json_atomico(output_path, payload)
        return 0
    except IntegridadeModo4Error as exc_selo:
        _escrever_json_atomico(
            error_path,
            {
                "codigo_erro": "SELO_INVALIDO",
                "status_http": 503,
                "erro": f"MODO 4 bloqueado por falha de integridade criptografica: {exc_selo}",
            },
        )
        return 3
    except Exception as exc:
        _escrever_json_atomico(
            error_path,
            {
                "codigo_erro": "ERRO_INTERNO",
                "status_http": 500,
                "erro": f"Erro interno no processamento do MODO 4 ({type(exc).__name__}): {exc}",
            },
        )
        return 1


@dataclass
class _RegistroJobModo4:
    job_id: str
    quantidade_jogos: int
    permitir_espelhos: bool
    seed: Optional[int]
    trace: bool
    spec_path: str
    output_path: str
    error_path: str
    status: str = "queued"
    created_at_utc: str = field(default_factory=_agora_utc_iso)
    updated_at_utc: str = field(default_factory=_agora_utc_iso)
    started_at_utc: Optional[str] = None
    finished_at_utc: Optional[str] = None
    created_monotonic: float = field(default_factory=time.monotonic)
    started_monotonic: Optional[float] = None
    finished_monotonic: Optional[float] = None
    elapsed_s: float = 0.0
    codigo_erro: Optional[str] = None
    status_http_erro: Optional[int] = None
    erro: Optional[str] = None
    cancel_requested: bool = False
    processo: Optional[subprocess.Popen[bytes]] = None


class LotomaniaModo4JobManager:
    """Gerencia ciclo de vida completo de jobs assincronos do Lotomania MODO 4."""

    def __init__(
        self,
        *,
        diretorio_base: str = BASE_DIR_PADRAO,
        max_concurrent_workers: int = 2,
        max_active_jobs: int = 8,
        ttl_finalizados_s: float = 1800.0,
        max_retidos_finalizados: int = 12,
        poll_interval_ms: int = 1500,
    ) -> None:
        self.diretorio_base = os.path.abspath(diretorio_base)
        self.max_concurrent_workers = max(1, int(max_concurrent_workers))
        self.max_active_jobs = max(1, int(max_active_jobs))
        self.ttl_finalizados_s = float(ttl_finalizados_s)
        self.max_retidos_finalizados = max(1, int(max_retidos_finalizados))
        self.poll_interval_ms = max(250, int(poll_interval_ms))

        self._spool_dir = tempfile.mkdtemp(prefix="b2b_lm_m4_jobs_")
        self._lock = threading.RLock()
        self._semaforo = threading.Semaphore(self.max_concurrent_workers)
        self._jobs: Dict[str, _RegistroJobModo4] = {}
        self._shutdown = False

    def _remover_arquivos_job(self, reg: _RegistroJobModo4) -> None:
        for caminho in (reg.spec_path, reg.output_path, reg.error_path):
            try:
                if caminho and os.path.exists(caminho):
                    os.remove(caminho)
            except OSError:
                pass

    def _limpar_expirados_locked(self) -> None:
        agora_mono = time.monotonic()
        finalizados = [
            j
            for j in self._jobs.values()
            if j.status in ("completed", "failed", "cancelled") and j.finished_monotonic is not None
        ]
        # Expira por TTL
        for reg in finalizados:
            if (agora_mono - float(reg.finished_monotonic)) > self.ttl_finalizados_s:
                self._remover_arquivos_job(reg)
                self._jobs.pop(reg.job_id, None)

        # Limita quantidade maxima retida (LRU pelo termino)
        restantes = sorted(
            (
                j
                for j in self._jobs.values()
                if j.status in ("completed", "failed", "cancelled") and j.finished_monotonic is not None
            ),
            key=lambda item: float(item.finished_monotonic or 0.0),
        )
        excesso = len(restantes) - self.max_retidos_finalizados
        if excesso > 0:
            for reg in restantes[:excesso]:
                self._remover_arquivos_job(reg)
                self._jobs.pop(reg.job_id, None)

    def _montar_snapshot_locked(self, reg: _RegistroJobModo4) -> Dict[str, Any]:
        if reg.status == "running" and reg.started_monotonic is not None:
            elapsed = round(max(0.0, time.monotonic() - reg.started_monotonic), 3)
        elif reg.finished_monotonic is not None and reg.started_monotonic is not None:
            elapsed = round(max(0.0, reg.finished_monotonic - reg.started_monotonic), 3)
        else:
            elapsed = round(reg.elapsed_s, 3)

        worker_alive = bool(reg.processo is not None and reg.processo.poll() is None)
        resultado_ok = bool(reg.status == "completed" and os.path.isfile(reg.output_path))
        return {
            "sucesso": True,
            "job_id": reg.job_id,
            "status": reg.status,
            "quantidade_jogos": reg.quantidade_jogos,
            "seed": reg.seed,
            "permitir_espelhos": reg.permitir_espelhos,
            "created_at_utc": reg.created_at_utc,
            "started_at_utc": reg.started_at_utc,
            "finished_at_utc": reg.finished_at_utc,
            "updated_at_utc": _agora_utc_iso() if reg.status == "running" else reg.updated_at_utc,
            "elapsed_s": elapsed,
            "poll_interval_ms": self.poll_interval_ms,
            "worker_alive": worker_alive,
            "resultado_disponivel": resultado_ok,
            "codigo_erro": reg.codigo_erro,
            "status_http": reg.status_http_erro,
            "erro": reg.erro,
        }

    def criar_job(
        self,
        *,
        quantidade_jogos: int,
        permitir_espelhos: bool,
        seed: Optional[int],
        trace: bool,
    ) -> Dict[str, Any]:
        with self._lock:
            self._limpar_expirados_locked()
            if self._shutdown:
                raise RuntimeError("Gerenciador de jobs encerrado.")
            ativos = sum(1 for j in self._jobs.values() if j.status in ("queued", "running"))
            if ativos >= self.max_active_jobs:
                raise OverflowError(
                    f"Limite de {self.max_active_jobs} jobs simultaneos/enfileirados atingido. Aguarde ou cancele um job ativo."
                )

            job_id = uuid.uuid4().hex[:16]
            spec_path = os.path.join(self._spool_dir, f"{job_id}.spec.json")
            output_path = os.path.join(self._spool_dir, f"{job_id}.result.json")
            error_path = os.path.join(self._spool_dir, f"{job_id}.error.json")
            _escrever_json_atomico(
                spec_path,
                {
                    "diretorio_base": self.diretorio_base,
                    "quantidade_jogos": int(quantidade_jogos),
                    "permitir_espelhos": bool(permitir_espelhos),
                    "seed": seed,
                    "trace": bool(trace),
                },
            )
            reg = _RegistroJobModo4(
                job_id=job_id,
                quantidade_jogos=int(quantidade_jogos),
                permitir_espelhos=bool(permitir_espelhos),
                seed=seed,
                trace=bool(trace),
                spec_path=spec_path,
                output_path=output_path,
                error_path=error_path,
            )
            self._jobs[job_id] = reg
            snapshot = self._montar_snapshot_locked(reg)

        thread = threading.Thread(
            target=self._supervisionar_worker,
            args=(job_id,),
            daemon=True,
            name=f"lm-modo4-job-{job_id[:8]}",
        )
        thread.start()
        return snapshot

    def _terminar_processo(self, proc: Optional[subprocess.Popen[bytes]]) -> None:
        if proc is None or proc.poll() is not None:
            return
        try:
            proc.terminate()
            proc.wait(timeout=3.0)
        except Exception:
            try:
                proc.kill()
                proc.wait(timeout=2.0)
            except Exception:
                pass

    def _supervisionar_worker(self, job_id: str) -> None:
        adquirido = False
        try:
            while not self._shutdown:
                with self._lock:
                    reg = self._jobs.get(job_id)
                    if reg is None or reg.cancel_requested:
                        if reg is not None:
                            reg.status = "cancelled"
                            reg.codigo_erro = "CANCELADO"
                            reg.erro = "Operacao cancelada antes da execucao."
                            reg.finished_at_utc = _agora_utc_iso()
                            reg.updated_at_utc = reg.finished_at_utc
                            reg.finished_monotonic = time.monotonic()
                        return
                if self._semaforo.acquire(timeout=0.25):
                    adquirido = True
                    break

            if not adquirido:
                return

            with self._lock:
                reg = self._jobs.get(job_id)
                if reg is None or reg.cancel_requested or self._shutdown:
                    if reg is not None:
                        reg.status = "cancelled"
                        reg.codigo_erro = "CANCELADO"
                        reg.erro = "Operacao cancelada pelo usuario."
                        reg.finished_at_utc = _agora_utc_iso()
                        reg.updated_at_utc = reg.finished_at_utc
                        reg.finished_monotonic = time.monotonic()
                    return

                cmd = [sys.executable]
                if not __debug__:
                    cmd.append("-O")
                cmd.extend(
                    [
                        "-m",
                        "lotomania_modo4_jobs",
                        "--spec",
                        reg.spec_path,
                        "--output",
                        reg.output_path,
                        "--error",
                        reg.error_path,
                    ]
                )
                creation_flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
                proc = subprocess.Popen(
                    cmd,
                    cwd=self.diretorio_base,
                    stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.PIPE,
                    creationflags=creation_flags,
                )
                reg.processo = proc
                reg.status = "running"
                reg.started_at_utc = _agora_utc_iso()
                reg.updated_at_utc = reg.started_at_utc
                reg.started_monotonic = time.monotonic()

            stderr_bytes = b""
            try:
                while True:
                    ret = proc.poll()
                    if ret is not None:
                        if proc.stderr is not None:
                            try:
                                stderr_bytes = proc.stderr.read() or b""
                            except Exception:
                                stderr_bytes = b""
                        break
                    with self._lock:
                        reg_check = self._jobs.get(job_id)
                        cancelar = bool(reg_check is None or reg_check.cancel_requested or self._shutdown)
                    if cancelar:
                        self._terminar_processo(proc)
                        ret = proc.returncode
                        break
                    time.sleep(0.25)
            finally:
                if proc.stderr is not None:
                    try:
                        proc.stderr.close()
                    except OSError:
                        pass

            with self._lock:
                reg = self._jobs.get(job_id)
                if reg is None:
                    return
                reg.processo = None
                reg.finished_monotonic = time.monotonic()
                reg.finished_at_utc = _agora_utc_iso()
                reg.updated_at_utc = reg.finished_at_utc
                if reg.started_monotonic is not None:
                    reg.elapsed_s = max(0.0, reg.finished_monotonic - reg.started_monotonic)

                if reg.cancel_requested or self._shutdown:
                    reg.status = "cancelled"
                    reg.codigo_erro = "CANCELADO"
                    reg.erro = "Operacao cancelada pelo usuario. Nenhum jogo foi gerado."
                    self._remover_arquivos_job(reg)
                    return

                if ret == 0 and os.path.isfile(reg.output_path):
                    reg.status = "completed"
                    reg.codigo_erro = None
                    reg.status_http_erro = None
                    reg.erro = None
                    return

                err_payload: Dict[str, Any] = {}
                if os.path.isfile(reg.error_path):
                    try:
                        with open(reg.error_path, "r", encoding="utf-8") as fh:
                            err_payload = json.load(fh)
                    except Exception:
                        err_payload = {}

                reg.status = "failed"
                reg.codigo_erro = err_payload.get("codigo_erro") or "WORKER_CRASH"
                reg.status_http_erro = int(err_payload.get("status_http") or 500)
                stderr_txt = stderr_bytes.decode("utf-8", errors="replace").strip()[-300:]
                reg.erro = err_payload.get("erro") or (
                    f"Subprocesso do motor MODO 4 encerrou inesperadamente (codigo {ret}): {stderr_txt}"
                )
        finally:
            if adquirido:
                self._semaforo.release()

    def obter_status(self, job_id: str) -> Optional[Dict[str, Any]]:
        with self._lock:
            self._limpar_expirados_locked()
            reg = self._jobs.get(job_id)
            if reg is None:
                return None
            return self._montar_snapshot_locked(reg)

    def obter_resultado(self, job_id: str) -> Tuple[str, Optional[bytes], Optional[Dict[str, Any]]]:
        """
        Retorna `(estado, json_bytes_ou_None, metadados_erro_ou_None)`.
        `estado` em {"not_found", "running", "completed", "failed", "cancelled"}.
        """
        with self._lock:
            self._limpar_expirados_locked()
            reg = self._jobs.get(job_id)
            if reg is None:
                return ("not_found", None, None)
            snap = self._montar_snapshot_locked(reg)
            if reg.status in ("queued", "running"):
                return ("running", None, snap)
            if reg.status == "completed" and os.path.isfile(reg.output_path):
                with open(reg.output_path, "rb") as fh:
                    return ("completed", fh.read(), snap)
            return (reg.status, None, snap)

    def cancelar_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        proc_para_matar: Optional[subprocess.Popen[bytes]] = None
        with self._lock:
            reg = self._jobs.get(job_id)
            if reg is None:
                return None
            if reg.status in ("completed", "failed", "cancelled"):
                return self._montar_snapshot_locked(reg)
            reg.cancel_requested = True
            proc_para_matar = reg.processo
            reg.status = "cancelled"
            reg.codigo_erro = "CANCELADO"
            if proc_para_matar is None:
                reg.erro = "Operacao cancelada pelo usuario. Nenhum jogo foi gerado."
                reg.finished_at_utc = _agora_utc_iso()
                reg.updated_at_utc = reg.finished_at_utc
                reg.finished_monotonic = time.monotonic()
            else:
                reg.erro = "Cancelamento solicitado; encerrando subprocesso do motor MODO 4."
                reg.updated_at_utc = _agora_utc_iso()

        if proc_para_matar is not None:
            self._terminar_processo(proc_para_matar)

        with self._lock:
            reg_atual = self._jobs.get(job_id)
            if reg_atual is None:
                return None
            return self._montar_snapshot_locked(reg_atual)

    def encerrar_todos(self) -> None:
        procs: list[subprocess.Popen[bytes]] = []
        with self._lock:
            self._shutdown = True
            for reg in self._jobs.values():
                reg.cancel_requested = True
                if reg.processo is not None:
                    procs.append(reg.processo)
        for proc in procs:
            self._terminar_processo(proc)
        shutil.rmtree(self._spool_dir, ignore_errors=True)


_GERENCIADOR_PADRAO: Optional[LotomaniaModo4JobManager] = None
_LOCK_SINGLETON = threading.Lock()
_ATEXIT_REGISTRADO = False


def obter_gerenciador_jobs_lotomania_modo4() -> LotomaniaModo4JobManager:
    global _GERENCIADOR_PADRAO, _ATEXIT_REGISTRADO
    with _LOCK_SINGLETON:
        if _GERENCIADOR_PADRAO is None or _GERENCIADOR_PADRAO._shutdown:
            _GERENCIADOR_PADRAO = LotomaniaModo4JobManager()
        if not _ATEXIT_REGISTRADO:
            atexit.register(encerrar_gerenciador_jobs_lotomania_modo4)
            _ATEXIT_REGISTRADO = True
        return _GERENCIADOR_PADRAO


def encerrar_gerenciador_jobs_lotomania_modo4() -> None:
    """Encerra workers ativos e reinicia o singleton de forma segura no shutdown da API."""
    global _GERENCIADOR_PADRAO
    with _LOCK_SINGLETON:
        mgr = _GERENCIADOR_PADRAO
        _GERENCIADOR_PADRAO = None
    if mgr is not None:
        mgr.encerrar_todos()


def _main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Worker isolado Lotomania MODO 4.")
    parser.add_argument("--spec", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--error", required=True)
    args = parser.parse_args(argv)
    return _executar_worker_cli(args.spec, args.output, args.error)


if __name__ == "__main__":
    raise SystemExit(_main())
