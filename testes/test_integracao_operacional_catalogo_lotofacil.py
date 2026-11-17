# -*- coding: utf-8 -*-
"""
SUÍTE DE TESTES OPERACIONAIS: PILOTO CATÁLOGO LOTOFÁCIL J=1.000
=============================================================
Validação operacional de ponta a ponta do catálogo canônico de 1.000 jogos
integrado à API do B2B Loterias via servidor ASGI uvicorn real e urllib.

Testes executados:
1. Carregamento inicial e tempo de resposta (latência ultrarrápida < 50 ms).
2. Status geral de governança e identificação oficial (OFF_STANDBY).
3. Consulta paginada, navegação e validação de limites.
4. Imutabilidade e integridade criptográfica dos jogos entregues (SHA-256).
5. Auditoria em tempo real via endpoint HTTP (/auditoria).
6. Apresentação e integridade dos metadados de homologação e qualidade.
7. Resiliência do catálogo e rotina de auto-recuperação via backup independente.
"""

from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import os
import socket
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import unittest
import urllib.error
import urllib.request

import uvicorn
from api import app

from catalogo_lotofacil_10000.leitor import (
    HASH_DOCUMENTO_OFICIAL_J1000,
    HASH_FISICO_OFICIAL_J1000,
    HASH_JOGOS_OFICIAL_J1000,
    IDENTIFICADOR_CANONICO_J1000,
    HASH_DOCUMENTO_OFICIAL_J2000,
    HASH_FISICO_OFICIAL_J2000,
    HASH_JOGOS_OFICIAL_J2000,
    IDENTIFICADOR_CANONICO_J2000,
    obter_carteira_oficial_1000,
    obter_carteira_oficial_2000,
    verificar_integridade_catalogo_1000,
    verificar_integridade_catalogo_2000,
)


@dataclass
class _ServidorUvicornTemporario:
    port: int
    server: uvicorn.Server
    thread: threading.Thread

    def url(self, caminho: str) -> str:
        return f"http://127.0.0.1:{self.port}{caminho}"


def _iniciar_uvicorn_temporario() -> _ServidorUvicornTemporario:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("127.0.0.1", 0))
    port = int(sock.getsockname()[1])
    sock.close()

    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    prazo = time.monotonic() + 10.0
    while time.monotonic() < prazo:
        if server.started:
            return _ServidorUvicornTemporario(port=port, server=server, thread=thread)
        time.sleep(0.02)
    server.should_exit = True
    thread.join(timeout=2.0)
    raise RuntimeError("Servidor uvicorn temporario nao iniciou a tempo.")


def _parar_uvicorn_temporario(srv: _ServidorUvicornTemporario) -> None:
    srv.server.should_exit = True
    srv.thread.join(timeout=5.0)


def _requisitar_http(
    url: str,
    *,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    data: Optional[bytes] = None,
) -> Tuple[int, Dict[str, str], bytes]:
    req = urllib.request.Request(url, data=data, method=method, headers=headers or {})
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            hdrs = {k.lower(): v for k, v in resp.headers.items()}
            return int(resp.status), hdrs, resp.read()
    except urllib.error.HTTPError as err:
        hdrs = {k.lower(): v for k, v in (err.headers.items() if err.headers else [])}
        return int(err.code), hdrs, err.read()


class TestIntegracaoOperacionalCatalogoLotofacil(unittest.TestCase):
    """Bateria de testes operacionais da carteira canônica J=1.000 no B2B Loterias."""

    srv: _ServidorUvicornTemporario = None
    carteira_esperada: List[List[int]] = []
    carteira_esperada_2000: List[List[int]] = []

    @classmethod
    def setUpClass(cls):
        cls.srv = _iniciar_uvicorn_temporario()
        cls.carteira_esperada = obter_carteira_oficial_1000(auto_recuperar=True)
        cls.carteira_esperada_2000 = obter_carteira_oficial_2000(auto_recuperar=True)

    @classmethod
    def tearDownClass(cls):
        if cls.srv is not None:
            _parar_uvicorn_temporario(cls.srv)

    def test_01_carregamento_inicial_e_tempo_resposta(self):
        """Valida que o carregamento direto dos 1.000 jogos ocorre em tempo ultrarrápido (< 50 ms)."""
        t0 = time.perf_counter()
        carteira = obter_carteira_oficial_1000(auto_recuperar=False)
        duracao_ms = (time.perf_counter() - t0) * 1000.0

        self.assertEqual(len(carteira), 1000, "Devem ser carregados exatamente 1.000 jogos.")
        self.assertLess(duracao_ms, 50.0, f"Tempo de carregamento excessivo: {duracao_ms:.2f} ms.")

        # Validação de integridade e regras da Caixa
        jogos_unicos = set(tuple(jg) for jg in carteira)
        self.assertEqual(len(jogos_unicos), 1000, "Não podem existir bilhetes duplicados.")
        for jg in carteira:
            self.assertEqual(len(jg), 15, "Cada aposta deve conter 15 dezenas.")
            self.assertTrue(all(1 <= d <= 25 for d in jg), "Dezenas devem estar entre 1 e 25.")

    def test_02_status_governanca_e_identificacao(self):
        """Valida endpoint /status, confirmando metadados e estado OFF_STANDBY."""
        code, _, body = _requisitar_http(self.srv.url("/api/v1/lotofacil-catalogo/status"))
        self.assertEqual(code, 200)
        data = json.loads(body.decode("utf-8"))

        self.assertTrue(data["sucesso"])
        self.assertEqual(data["catalogo"], IDENTIFICADOR_CANONICO_J1000)
        self.assertEqual(data["quantidade_jogos"], 1000)
        self.assertEqual(data["tamanho_aposta"], 15)
        self.assertEqual(data["pool"], 25)

        gov = data["governanca"]
        self.assertEqual(gov["estado_operacional"], "OFF_STANDBY")
        self.assertFalse(gov["em_producao"])
        self.assertTrue(gov["integridade_confirmada"])
        self.assertEqual(gov["hashes"]["arquivo_fisico"], HASH_FISICO_OFICIAL_J1000)
        self.assertEqual(gov["hashes"]["jogos_canonicos"], HASH_JOGOS_OFICIAL_J1000)

    def test_03_consulta_paginada_e_limites(self):
        """Valida acesso paginado via API em diferentes offsets e validação de limites."""
        # Página 1 (jogos 0 a 99)
        code1, _, body1 = _requisitar_http(self.srv.url("/api/v1/lotofacil-catalogo/jogos?offset=0&limit=100"))
        self.assertEqual(code1, 200)
        d1 = json.loads(body1.decode("utf-8"))
        self.assertEqual(d1["total_jogos"], 1000)
        self.assertEqual(d1["retornados"], 100)
        self.assertEqual(d1["jogos"], self.carteira_esperada[:100])

        # Página intermediária (jogos 450 a 649)
        code2, _, body2 = _requisitar_http(self.srv.url("/api/v1/lotofacil-catalogo/jogos?offset=450&limit=200"))
        self.assertEqual(code2, 200)
        d2 = json.loads(body2.decode("utf-8"))
        self.assertEqual(d2["retornados"], 200)
        self.assertEqual(d2["jogos"], self.carteira_esperada[450:650])

        # Página final (jogos 900 a 999)
        code3, _, body3 = _requisitar_http(self.srv.url("/api/v1/lotofacil-catalogo/jogos?offset=900&limit=100"))
        self.assertEqual(code3, 200)
        d3 = json.loads(body3.decode("utf-8"))
        self.assertEqual(d3["retornados"], 100)
        self.assertEqual(d3["jogos"], self.carteira_esperada[900:1000])

        # Validação de erro em limites fora do domínio
        code_inv_offset, _, _ = _requisitar_http(self.srv.url("/api/v1/lotofacil-catalogo/jogos?offset=1000"))
        self.assertEqual(code_inv_offset, 422)

        code_inv_limit, _, _ = _requisitar_http(self.srv.url("/api/v1/lotofacil-catalogo/jogos?limit=0"))
        self.assertEqual(code_inv_limit, 422)

    def test_04_imutabilidade_entre_carregamento_e_uso(self):
        """Valida que a carteira retornada pela API preserva integralmente o hash SHA-256 canônico."""
        code, _, body = _requisitar_http(self.srv.url("/api/v1/lotofacil-catalogo/jogos?offset=0&limit=1000"))
        self.assertEqual(code, 200)
        data = json.loads(body.decode("utf-8"))
        jogos_api = data["jogos"]

        serializacao = json.dumps(jogos_api, separators=(",", ":"))
        hash_jogos_api = hashlib.sha256(serializacao.encode("utf-8")).hexdigest()
        self.assertEqual(hash_jogos_api, HASH_JOGOS_OFICIAL_J1000)

    def test_05_auditoria_em_tempo_real(self):
        """Valida endpoint /auditoria com verificação dos três níveis de hash."""
        code, _, body = _requisitar_http(self.srv.url("/api/v1/lotofacil-catalogo/auditoria"))
        self.assertEqual(code, 200)
        data = json.loads(body.decode("utf-8"))

        self.assertTrue(data["sucesso"])
        aud = data["auditoria"]
        self.assertTrue(aud["arquivo_existe"])
        self.assertTrue(aud["hash_fisico_valido"])
        self.assertTrue(aud["hash_jogos_valido"])
        self.assertTrue(aud["hash_documento_valido"])
        self.assertEqual(aud["total_jogos"], 1000)
        self.assertEqual(aud["jogos_unicos"], 1000)
        self.assertEqual(aud["status_geral"], "INTEGRO")

    def test_06_metadados_e_metricas_combinatorias(self):
        """Valida endpoint /metadados, confirmando métricas de qualidade registradas."""
        code, _, body = _requisitar_http(self.srv.url("/api/v1/lotofacil-catalogo/metadados"))
        self.assertEqual(code, 200)
        data = json.loads(body.decode("utf-8"))

        self.assertTrue(data["sucesso"])
        self.assertEqual(data["semente_utilizada"], 2027)
        self.assertEqual(data["b_cand_utilizado"], 32)
        self.assertEqual(data["orcamento_max_avaliacoes"], 32000)

        mq = data["metricas_qualidade"]
        self.assertEqual(mq["duplicatas"], 0)
        self.assertEqual(mq["unicidade_pct"], 100.0)
        self.assertEqual(mq["cobertura_t4_pct"], 100.0)
        self.assertEqual(mq["quadras_cobertas"], 12650)
        self.assertEqual(mq["ss_minimo"], 0.0)
        self.assertEqual(mq["ss_observado"], 14.0)
        self.assertAlmostEqual(mq["funcao_objetivo_F"], 0.975914280806, places=6)

        tv = data["tripla_validacao"]
        self.assertTrue(tv["aprovado_tolerancia_1e12"])
        self.assertLessEqual(tv["divergencia_e4_e2"], 1e-12)
        self.assertLessEqual(tv["divergencia_e4_ref"], 1e-12)

    def test_07_resiliencia_e_restauracao_do_backup(self):
        """Valida que o endpoint de restauração opera com sucesso mantendo a integridade."""
        code, _, body = _requisitar_http(
            self.srv.url("/api/v1/lotofacil-catalogo/restaurar"),
            method="POST",
            data=b"{}",
        )
        self.assertEqual(code, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertTrue(data["sucesso"])

        valido, rel = verificar_integridade_catalogo_1000()
        self.assertTrue(valido)
        self.assertEqual(rel["status_geral"], "INTEGRO")

    def test_08_carregamento_e_tempo_resposta_2000(self):
        """Valida carregamento direto dos 2.000 jogos e latência ultrarrápida (< 50 ms)."""
        t0 = time.perf_counter()
        carteira = obter_carteira_oficial_2000(auto_recuperar=False)
        duracao_ms = (time.perf_counter() - t0) * 1000.0

        self.assertEqual(len(carteira), 2000, "Devem ser carregados exatamente 2.000 jogos.")
        self.assertLess(duracao_ms, 50.0, f"Tempo de carregamento excessivo: {duracao_ms:.2f} ms.")

        jogos_unicos = set(tuple(jg) for jg in carteira)
        self.assertEqual(len(jogos_unicos), 2000, "Não podem existir bilhetes duplicados.")
        for jg in carteira:
            self.assertEqual(len(jg), 15, "Cada aposta deve conter 15 dezenas.")
            self.assertTrue(all(1 <= d <= 25 for d in jg), "Dezenas devem estar entre 1 e 25.")

    def test_09_status_governanca_2000(self):
        """Valida endpoint /status?tamanho=2000, confirmando identificação oficial e integridade."""
        code, _, body = _requisitar_http(self.srv.url("/api/v1/lotofacil-catalogo/status?tamanho=2000"))
        self.assertEqual(code, 200)
        data = json.loads(body.decode("utf-8"))

        self.assertTrue(data["sucesso"])
        self.assertEqual(data["catalogo"], IDENTIFICADOR_CANONICO_J2000)
        self.assertEqual(data["quantidade_jogos"], 2000)
        self.assertEqual(data["tamanho_aposta"], 15)
        self.assertEqual(data["pool"], 25)

        gov = data["governanca"]
        self.assertEqual(gov["estado_operacional"], "OFF_STANDBY")
        self.assertFalse(gov["em_producao"])
        self.assertTrue(gov["integridade_confirmada"])
        self.assertEqual(gov["carteiras_disponiveis"]["2000"]["hashes"]["arquivo_fisico"], HASH_FISICO_OFICIAL_J2000)
        self.assertEqual(gov["carteiras_disponiveis"]["2000"]["hashes"]["jogos_canonicos"], HASH_JOGOS_OFICIAL_J2000)

    def test_10_consulta_paginada_e_limites_2000(self):
        """Valida acesso paginado via API para carteira J=2.000 em múltiplos offsets."""
        # Página 1 (jogos 0 a 99)
        code1, _, body1 = _requisitar_http(
            self.srv.url("/api/v1/lotofacil-catalogo/jogos?tamanho=2000&offset=0&limit=100")
        )
        self.assertEqual(code1, 200)
        d1 = json.loads(body1.decode("utf-8"))
        self.assertEqual(d1["total_jogos"], 2000)
        self.assertEqual(d1["retornados"], 100)
        self.assertEqual(d1["jogos"], self.carteira_esperada_2000[:100])

        # Página intermediária (jogos 950 a 1049)
        code2, _, body2 = _requisitar_http(
            self.srv.url("/api/v1/lotofacil-catalogo/jogos?tamanho=2000&offset=950&limit=100")
        )
        self.assertEqual(code2, 200)
        d2 = json.loads(body2.decode("utf-8"))
        self.assertEqual(d2["retornados"], 100)
        self.assertEqual(d2["jogos"], self.carteira_esperada_2000[950:1050])

        # Página final (jogos 1900 a 1999)
        code3, _, body3 = _requisitar_http(
            self.srv.url("/api/v1/lotofacil-catalogo/jogos?tamanho=2000&offset=1900&limit=100")
        )
        self.assertEqual(code3, 200)
        d3 = json.loads(body3.decode("utf-8"))
        self.assertEqual(d3["retornados"], 100)
        self.assertEqual(d3["jogos"], self.carteira_esperada_2000[1900:2000])

        # Limite fora de domínio
        code_inv_offset, _, _ = _requisitar_http(
            self.srv.url("/api/v1/lotofacil-catalogo/jogos?tamanho=2000&offset=2000")
        )
        self.assertEqual(code_inv_offset, 422)

    def test_11_imutabilidade_entre_carregamento_e_uso_2000(self):
        """Valida que todos os 2.000 jogos entregues pela API reproduzem o hash canônico exato."""
        code, _, body = _requisitar_http(
            self.srv.url("/api/v1/lotofacil-catalogo/jogos?tamanho=2000&offset=0&limit=2000")
        )
        self.assertEqual(code, 200)
        data = json.loads(body.decode("utf-8"))
        jogos_api = data["jogos"]

        serializacao = json.dumps(jogos_api, separators=(",", ":"))
        hash_jogos_api = hashlib.sha256(serializacao.encode("utf-8")).hexdigest()
        self.assertEqual(hash_jogos_api, HASH_JOGOS_OFICIAL_J2000)

    def test_12_auditoria_em_tempo_real_2000(self):
        """Valida endpoint /auditoria?tamanho=2000 com verificação dos três níveis de hash."""
        code, _, body = _requisitar_http(self.srv.url("/api/v1/lotofacil-catalogo/auditoria?tamanho=2000"))
        self.assertEqual(code, 200)
        data = json.loads(body.decode("utf-8"))

        self.assertTrue(data["sucesso"])
        aud = data["auditoria"]
        self.assertTrue(aud["arquivo_existe"])
        self.assertTrue(aud["hash_fisico_valido"])
        self.assertTrue(aud["hash_jogos_valido"])
        self.assertTrue(aud["hash_documento_valido"])
        self.assertEqual(aud["total_jogos"], 2000)
        self.assertEqual(aud["jogos_unicos"], 2000)
        self.assertEqual(aud["status_geral"], "INTEGRO")

    def test_13_metadados_e_metricas_combinatorias_2000(self):
        """Valida endpoint /metadados?tamanho=2000, confirmando qualidade e tripla validação."""
        code, _, body = _requisitar_http(self.srv.url("/api/v1/lotofacil-catalogo/metadados?tamanho=2000"))
        self.assertEqual(code, 200)
        data = json.loads(body.decode("utf-8"))

        self.assertTrue(data["sucesso"])
        self.assertEqual(data["semente_utilizada"], 2027)
        self.assertEqual(data["b_cand_utilizado"], 32)
        self.assertEqual(data["orcamento_max_avaliacoes"], 64000)

        mq = data["metricas_qualidade"]
        self.assertEqual(mq["duplicatas"], 0)
        self.assertEqual(mq["unicidade_pct"], 100.0)
        self.assertEqual(mq["cobertura_t4_pct"], 100.0)
        self.assertEqual(mq["quadras_cobertas"], 12650)
        self.assertEqual(mq["ss_minimo"], 0.0)
        self.assertEqual(mq["ss_observado"], 30.0)
        self.assertEqual(mq["maior_sequencia_consecutiva"], 6)
        self.assertEqual(mq["jogos_seq_ge_7"], 0)
        self.assertAlmostEqual(mq["funcao_objetivo_F"], 0.970246481147, places=6)

        tv = data["tripla_validacao"]
        self.assertTrue(tv["aprovado_tolerancia_1e12"])
        self.assertLessEqual(tv["divergencia_e4_e2"], 1e-12)
        self.assertLessEqual(tv["divergencia_e4_ref"], 1e-12)

    def test_14_resiliencia_e_restauracao_backup_2000(self):
        """Valida restauração do catálogo J=2.000 a partir da custódia independente."""
        code, _, body = _requisitar_http(
            self.srv.url("/api/v1/lotofacil-catalogo/restaurar?tamanho=2000"),
            method="POST",
            data=b"{}",
        )
        self.assertEqual(code, 200)
        data = json.loads(body.decode("utf-8"))
        self.assertTrue(data["sucesso"])

        valido, rel = verificar_integridade_catalogo_2000()
        self.assertTrue(valido)
        self.assertEqual(rel["status_geral"], "INTEGRO")


if __name__ == "__main__":
    unittest.main()
