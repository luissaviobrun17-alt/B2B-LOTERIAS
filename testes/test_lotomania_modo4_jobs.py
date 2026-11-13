"""
Suite automatizada do fluxo assincrono (/api/v1/lotomania-modo4/jobs) do MODO 4.
Compativel com `python` e `python -O` (nao depende de `assert` nem de `httpx`).
"""

from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import contextmanager
from unittest.mock import patch
from urllib import error as urlerror
from urllib import request as urlrequest

from fastapi import HTTPException

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

import api  # noqa: E402
from lotomania_modo4_jobs import (  # noqa: E402
    LotomaniaModo4JobManager,
    encerrar_gerenciador_jobs_lotomania_modo4,
)


def _porta_livre() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _http_json(
    url: str,
    *,
    method: str = "GET",
    payload: dict | None = None,
    timeout: float = 10.0,
) -> tuple[int, dict]:
    data = None
    headers = {"Accept": "application/json"}
    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
    req = urlrequest.Request(url, data=data, headers=headers, method=method)
    try:
        with urlrequest.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
            return int(resp.status), json.loads(raw)
    except urlerror.HTTPError as exc:
        raw = exc.read().decode("utf-8", errors="replace")
        try:
            body = json.loads(raw)
        except Exception:
            body = {"detail": raw}
        return int(exc.code), body


@contextmanager
def _servidor_uvicorn_isolado():
    porta = _porta_livre()
    cmd = [sys.executable]
    if not __debug__:
        cmd.append("-O")
    cmd.extend(["-m", "uvicorn", "api:app", "--host", "127.0.0.1", "--port", str(porta), "--log-level", "warning"])
    proc = subprocess.Popen(
        cmd,
        cwd=ROOT_DIR,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    base = f"http://127.0.0.1:{porta}"
    try:
        pronto = False
        deadline_up = time.monotonic() + 20.0
        while time.monotonic() < deadline_up:
            try:
                code, body = _http_json(f"{base}/health", timeout=2.0)
                if code == 200 and body.get("modo4_disponivel") is True:
                    pronto = True
                    break
            except Exception:
                time.sleep(0.25)
        if not pronto:
            stderr_txt = ""
            if proc.poll() is not None and proc.stderr is not None:
                stderr_txt = proc.stderr.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"Uvicorn isolado nao subiu em {base}: {stderr_txt}")
        yield base
    finally:
        if proc.poll() is None:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=5)
        if proc.stderr is not None:
            proc.stderr.close()


class TestLotomaniaModo4Jobs(unittest.TestCase):
    """Valida geracao assincrona isolada, fail-closed, cancelamento e paridade web/mobile."""

    def tearDown(self) -> None:
        encerrar_gerenciador_jobs_lotomania_modo4()

    def _aguardar_job_http(self, base: str, job_id: str, *, timeout_s: float = 45.0) -> dict:
        limite = time.monotonic() + timeout_s
        ultimo = {}
        while time.monotonic() < limite:
            code, ultimo = _http_json(f"{base}/api/v1/lotomania-modo4/jobs/{job_id}", timeout=5.0)
            self.assertEqual(code, 200, msg=f"Status inesperado: {ultimo}")
            if ultimo.get("status") in ("completed", "failed", "cancelled"):
                return ultimo
            time.sleep(0.15)
        self.fail(f"Timeout aguardando job {job_id}: ultimo snapshot={ultimo}")

    def test_equivalencia_limites_cancelamento_e_nao_interferencia_http_real(self) -> None:
        """Executa ciclo completo em Uvicorn HTTP real cobrindo 202/200/404/409/422, cancelamento e /health."""
        with _servidor_uvicorn_isolado() as base:
            # 1) Equivalencia matematica exata entre POST /gerar e POST /jobs -> /resultado
            payload = {"quantidade_jogos": 10, "permitir_espelhos": True, "seed": 330001}
            c_sync, dados_sync = _http_json(f"{base}/api/v1/lotomania-modo4/gerar", method="POST", payload=payload, timeout=30.0)
            self.assertEqual(c_sync, 200, msg=str(dados_sync))

            c_criar, job = _http_json(f"{base}/api/v1/lotomania-modo4/jobs", method="POST", payload=payload, timeout=10.0)
            self.assertEqual(c_criar, 202, msg=str(job))
            self.assertIn("job_id", job)

            snap_final = self._aguardar_job_http(base, job["job_id"])
            self.assertEqual(snap_final.get("status"), "completed", msg=str(snap_final))
            self.assertTrue(snap_final.get("resultado_disponivel"))

            c_res, dados_async = _http_json(
                f"{base}/api/v1/lotomania-modo4/jobs/{job['job_id']}/resultado",
                timeout=15.0,
            )
            self.assertEqual(c_res, 200, msg=str(dados_async))
            self.assertTrue(dados_async["sucesso"])
            self.assertEqual(dados_async["quantidade_entregue"], 10)
            self.assertEqual(dados_async["jogos"], dados_sync["jogos"])
            self.assertEqual(dados_async["hash_carteira_sha256_v1"], dados_sync["hash_carteira_sha256_v1"])
            self.assertEqual(
                dados_async["hash_carteira_sha256_v2_canonico"],
                dados_sync["hash_carteira_sha256_v2_canonico"],
            )
            self.assertEqual(
                dados_async["selo_criptografico"]["sha256_manifesto"],
                dados_sync["selo_criptografico"]["sha256_manifesto"],
            )

            # 2) Validacao de limites e 404 fail-closed
            for qtd_invalida in (0, -5, 10001):
                c_inv, body_inv = _http_json(
                    f"{base}/api/v1/lotomania-modo4/jobs",
                    method="POST",
                    payload={"quantidade_jogos": qtd_invalida, "permitir_espelhos": True},
                )
                self.assertEqual(c_inv, 422, msg=f"Qtd={qtd_invalida} -> {body_inv}")

            self.assertEqual(_http_json(f"{base}/api/v1/lotomania-modo4/jobs/inexistente123")[0], 404)
            self.assertEqual(_http_json(f"{base}/api/v1/lotomania-modo4/jobs/inexistente123/resultado")[0], 404)
            self.assertEqual(_http_json(f"{base}/api/v1/lotomania-modo4/jobs/inexistente123", method="DELETE")[0], 404)

            # 3) Cancelamento via DELETE e POST /cancel, 409 antes do termino e /health < 1s + motor legado
            for idx, metodo_cancel in enumerate(("DELETE", "POST")):
                c_j, b_j = _http_json(
                    f"{base}/api/v1/lotomania-modo4/jobs",
                    method="POST",
                    payload={"quantidade_jogos": 800, "permitir_espelhos": True, "seed": 42 + idx},
                    timeout=5.0,
                )
                self.assertEqual(c_j, 202, msg=str(b_j))
                jid = b_j["job_id"]

                # Aguarda entrar em running e checa /health + /resultado 409 + legado durante o primeiro ciclo
                limite = time.monotonic() + 10.0
                while time.monotonic() < limite:
                    _, st = _http_json(f"{base}/api/v1/lotomania-modo4/jobs/{jid}", timeout=3.0)
                    if st.get("status") == "running" and st.get("worker_alive"):
                        break
                    time.sleep(0.1)

                c_409, _ = _http_json(f"{base}/api/v1/lotomania-modo4/jobs/{jid}/resultado", timeout=5.0)
                self.assertIn(c_409, (409, 200))  # 409 enquanto ativo; 200 apenas se ambiente concluiu sub-segundo

                if idx == 0:
                    latencias = []
                    for _ in range(4):
                        t0 = time.monotonic()
                        c_h, b_h = _http_json(f"{base}/health", timeout=2.0)
                        latencias.append(time.monotonic() - t0)
                        self.assertEqual(c_h, 200)
                        self.assertTrue(b_h.get("modo4_disponivel"))
                        self.assertFalse(b_h["lotofacil_modo4"]["disponivel"])
                        time.sleep(0.15)
                    self.assertLess(max(latencias), 1.0, msg=f"Latencias /health={latencias}")

                    c_leg, b_leg = _http_json(
                        f"{base}/api/v1/motor-lotomania/otimizar-cobertura",
                        method="POST",
                        payload={"quantidade_jogos": 5, "permitir_espelhos": True},
                        timeout=10.0,
                    )
                    self.assertEqual(c_leg, 200, msg=str(b_leg))
                    self.assertEqual(len(b_leg.get("jogos", [])), 5)

                t_c0 = time.monotonic()
                if metodo_cancel == "DELETE":
                    c_can, b_can = _http_json(f"{base}/api/v1/lotomania-modo4/jobs/{jid}", method="DELETE", timeout=5.0)
                else:
                    c_can, b_can = _http_json(
                        f"{base}/api/v1/lotomania-modo4/jobs/{jid}/cancel",
                        method="POST",
                        payload={},
                        timeout=5.0,
                    )
                self.assertEqual(c_can, 200, msg=str(b_can))
                self.assertLess(time.monotonic() - t_c0, 5.0)
                self.assertEqual(b_can.get("status"), "cancelled", msg=str(b_can))
                self.assertFalse(b_can.get("worker_alive"))

                c_pos, b_pos = _http_json(f"{base}/api/v1/lotomania-modo4/jobs/{jid}/resultado", timeout=5.0)
                self.assertEqual(c_pos, 409, msg=str(b_pos))

    def test_selo_invalido_na_criacao_bloqueia_503_sem_criar_job(self) -> None:
        req = api.OtimizarCoberturaRequest(quantidade_jogos=5, permitir_espelhos=True, seed=77)
        with patch("api.verificar_selo_modo4", side_effect=api.IntegridadeModo4Error("manifesto adulterado teste")):
            with self.assertRaises(HTTPException) as ctx:
                api.endpoint_lotomania_modo4_criar_job(req)
        self.assertEqual(ctx.exception.status_code, 503)
        self.assertIn("Nenhum jogo foi gerado", str(ctx.exception.detail))

    def test_limite_fila_retorna_429(self) -> None:
        mgr_restrito = LotomaniaModo4JobManager(
            diretorio_base=ROOT_DIR,
            max_concurrent_workers=1,
            max_active_jobs=1,
        )
        try:
            with patch("api.obter_gerenciador_jobs_lotomania_modo4", return_value=mgr_restrito):
                criado = api.endpoint_lotomania_modo4_criar_job(
                    api.OtimizarCoberturaRequest(quantidade_jogos=500, permitir_espelhos=True, seed=123)
                )
                self.assertIn("job_id", criado)
                with self.assertRaises(HTTPException) as ctx:
                    api.endpoint_lotomania_modo4_criar_job(
                        api.OtimizarCoberturaRequest(quantidade_jogos=10, permitir_espelhos=True, seed=124)
                    )
                self.assertEqual(ctx.exception.status_code, 429)
                mgr_restrito.cancelar_job(criado["job_id"])
        finally:
            mgr_restrito.encerrar_todos()

    def test_selo_invalido_dentro_do_worker_falha_503_zero_jogos(self) -> None:
        """Verifica em subprocesso real com copia temporaria adulterada que o worker falha fechado."""
        with tempfile.TemporaryDirectory(prefix="test_m4_adulterado_") as tmp_dir:
            for nome in (
                "motor_lotomania_modo4.py",
                "verificador_selo_modo4.py",
                "manifesto_modo4.json",
                "manifesto_modo4.sig",
                "chave_publica_modo4.pem",
                "lotomania_modo4_jobs.py",
            ):
                src = os.path.join(ROOT_DIR, nome)
                if os.path.exists(src):
                    shutil.copy2(src, os.path.join(tmp_dir, nome))
            os.makedirs(os.path.join(tmp_dir, "data"), exist_ok=True)
            data_src = os.path.join(ROOT_DIR, "data", "lotomania.json")
            if os.path.exists(data_src):
                shutil.copy2(data_src, os.path.join(tmp_dir, "data", "lotomania.json"))
            manifest_tmp = os.path.join(tmp_dir, "manifesto_modo4.json")
            with open(manifest_tmp, "r", encoding="utf-8") as fh:
                txt = fh.read()
            with open(manifest_tmp, "w", encoding="utf-8") as fh:
                fh.write(txt.replace("1.2", "9.9", 1))

            mgr = LotomaniaModo4JobManager(
                diretorio_base=tmp_dir,
                max_concurrent_workers=1,
                max_active_jobs=2,
            )
            try:
                criado = mgr.criar_job(quantidade_jogos=5, permitir_espelhos=True, seed=11, trace=False)
                job_id = criado["job_id"]
                limite = time.monotonic() + 20.0
                snap = None
                while time.monotonic() < limite:
                    snap = mgr.obter_status(job_id)
                    if snap and snap["status"] in ("completed", "failed", "cancelled"):
                        break
                    time.sleep(0.1)
                self.assertIsNotNone(snap)
                self.assertEqual(snap["status"], "failed", msg=str(snap))
                self.assertEqual(snap["codigo_erro"], "SELO_INVALIDO", msg=str(snap))
                self.assertEqual(snap["status_http"], 503, msg=str(snap))
                estado, payload_bytes, meta = mgr.obter_resultado(job_id)
                self.assertEqual(estado, "failed")
                self.assertIsNone(payload_bytes)
                self.assertEqual((meta or {}).get("status_http"), 503)
            finally:
                mgr.encerrar_todos()

    def test_paridade_estatica_web_e_mobile_preservando_botoes_e_flag_lotofacil(self) -> None:
        arquivos = {
            "engine": os.path.join(ROOT_DIR, "js", "engines", "motor_lotomania_modo4_engine.js"),
            "ui": os.path.join(ROOT_DIR, "js", "ui.js"),
            "index": os.path.join(ROOT_DIR, "index.html"),
            "mobile": os.path.join(ROOT_DIR, "B2B_Loterias_Mobile.html"),
        }
        conteudos = {}
        for chave, caminho in arquivos.items():
            self.assertTrue(os.path.isfile(caminho), msg=f"Arquivo ausente: {caminho}")
            with open(caminho, "r", encoding="utf-8") as fh:
                conteudos[chave] = fh.read()

        for marcador in (
            "/api/v1/lotomania-modo4/jobs",
            "cancelarJob",
            "onProgress",
            "onJobCreated",
            "MENSAGEM_INDISPONIVEL",
        ):
            self.assertIn(marcador, conteudos["engine"])
            self.assertIn(marcador, conteudos["mobile"])

        for marcador_ui in ("_activeModo4JobId", "_modo4AbortController", "sendBeacon", "beforeunload"):
            self.assertIn(marcador_ui, conteudos["ui"])
            self.assertIn(marcador_ui, conteudos["mobile"])

        for marcador_dom in (
            "btn-executar-modo4-lotomania",
            "btn-conferir-modo4-lotomania",
            "subpanel-lotomania-modo4",
            'id="subpanel-lotofacil-modo4" style="display:none;"',
            "btn-central-jogos",
            "save-btn",
            "btn-print",
            "btn-play-caixa",
            "Central de Jogos",
        ):
            self.assertIn(marcador_dom, conteudos["index"])
            self.assertIn(marcador_dom, conteudos["mobile"])

        self.assertEqual(
            conteudos["mobile"].count("Touch fix + FastClick loaded"),
            1,
            msg="Injecao Touch fix do Mobile deve ocorrer uma unica vez no body principal.",
        )
        idx_print = conteudos["mobile"].index("printWin.document.write")
        self.assertNotIn(
            "Touch fix + FastClick loaded",
            conteudos["mobile"][idx_print : idx_print + 1500],
            msg="String de impressao HTML nao pode ser corrompida pelo GERAR_MOBILE.ps1.",
        )


if __name__ == "__main__":
    unittest.main()
