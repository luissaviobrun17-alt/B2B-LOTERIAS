#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTE 4: AUSÊNCIA DE FALLBACK JAVASCRIPT, RESILIÊNCIA FAIL-CLOSED DA API E VALIDAÇÃO DE CONTRATOS
==================================================================================================
Verifica sem utilizar instruções `assert` (100% compatível com `python -O`, lançando
`RuntimeError` explícito diante de qualquer violação):
1. Análise estática de `js/engines/motor_lotomania_modo4_engine.js`, `index.html` e `js/ui.js`.
2. Teste de indisponibilidade total da API (conexão recusada em porta fechada -> 0 jogos).
3. Testes com servidor HTTP loopback efêmero simulando: timeout, erro HTTP 500/503, JSON
   corrompido e resposta incompleta (fiel ao contrato estrito do cliente JS) -> 0 jogos.
4. Validação estrita Pydantic v2 em `/gerar` e `/conferir` (dados ausentes/inválidos -> erro).
5. Testes negativos controlados nos handlers FastAPI (`api.py`) para:
   - Violação de selo / manifesto inválido -> HTTP 503 (0 jogos);
   - Erro interno no processo de otimização -> HTTP 500 (0 jogos);
   - Falha na validação final da carteira (`sucesso=False`, qtd divergente, 49 dezenas, dezena > 100) -> HTTP 500 (0 jogos).
"""

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import re
import socket
import sys
import threading
import time
import unittest
import urllib.error
import urllib.request

DIR_TESTES = os.path.dirname(os.path.abspath(__file__))
DIR_RAIZ = os.path.dirname(DIR_TESTES)
if DIR_RAIZ not in sys.path:
    sys.path.insert(0, DIR_RAIZ)

from fastapi import HTTPException
from pydantic import ValidationError

import api
from motor_lotomania_modo4 import CLAUSULA_OBRIGATORIA_MODO4

MENSAGEM_OBRIGATORIA_OFFLINE = (
    "MODO 4 temporariamente indisponível. O servidor matemático oficial não está conectado. Nenhum jogo foi gerado."
)


def exigir(condicao: bool, mensagem: str) -> None:
    if condicao is not True:
        raise RuntimeError(f"Falha no teste de proibição de fallback: {mensagem}")


def localizar_arquivo_projeto(rel_path: str) -> str:
    caminhos = [
        os.path.join(DIR_RAIZ, rel_path),
        os.path.join(r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS", rel_path),
        os.path.join(
            r"C:\Users\Luis Brun\.gemini\antigravity\brain\f3af3942-aca3-4c9a-a3dd-e56f90feb848\scratch\ref",
            rel_path,
        ),
    ]
    for cam in caminhos:
        if os.path.isfile(cam):
            return cam
    raise FileNotFoundError(f"Arquivo {rel_path} não encontrado.")


def simular_cliente_modo4_offline(
    quantidade_jogos,
    url_base: str = "http://127.0.0.1:18099",
    timeout_s: float = 0.5,
) -> dict:
    """
    Espelha estritamente o comportamento de `MotorLotomaniaModo4Engine.gerarCarteira` em JS:
    qualquer entrada inválida, timeout, falha HTTP, JSON inválido ou carteira incompleta
    resulta em `sucesso=False` e `jogos=[]` (zero jogos entregues).
    """
    if type(quantidade_jogos) is not int or quantidade_jogos < 1 or quantidade_jogos > 10000:
        return {
            "sucesso": False,
            "erro": "Quantidade inválida. Informe um número inteiro estrito entre 1 e 10.000 jogos.",
            "jogos": [],
        }

    req = urllib.request.Request(
        f"{url_base}/api/v1/lotomania-modo4/gerar",
        data=json.dumps({"quantidade_jogos": quantidade_jogos, "permitir_espelhos": True}).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout_s) as resp:
            status_code = getattr(resp, "status", 200)
            if status_code != 200:
                return {"sucesso": False, "erro": MENSAGEM_OBRIGATORIA_OFFLINE, "jogos": []}
            dados = json.loads(resp.read().decode("utf-8"))
            jogos = dados.get("jogos") if isinstance(dados, dict) else None
            completa = (
                isinstance(dados, dict)
                and dados.get("sucesso") is True
                and isinstance(jogos, list)
                and len(jogos) == quantidade_jogos
                and all(
                    isinstance(j, list)
                    and len(j) == 50
                    and len(set(j)) == 50
                    and all(type(n) is int and 1 <= n <= 100 for n in j)
                    for j in jogos
                )
            )
            if not completa:
                return {"sucesso": False, "erro": MENSAGEM_OBRIGATORIA_OFFLINE, "jogos": []}
            return dados
    except (
        urllib.error.URLError,
        urllib.error.HTTPError,
        TimeoutError,
        socket.timeout,
        json.JSONDecodeError,
        ValueError,
        ConnectionError,
        OSError,
    ):
        return {
            "sucesso": False,
            "erro": MENSAGEM_OBRIGATORIA_OFFLINE,
            "jogos": [],
        }


def _iniciar_servidor_simulado(handler_cls):
    servidor = ThreadingHTTPServer(("127.0.0.1", 0), handler_cls)
    port = servidor.server_address[1]
    thread = threading.Thread(target=servidor.serve_forever, daemon=True)
    thread.start()
    return servidor, f"http://127.0.0.1:{port}"


def _testar_cenarios_http_cliente() -> dict:
    cenarios = {}

    # Cenario 1: Timeout real de socket
    class _TimeoutHandler(BaseHTTPRequestHandler):
        def do_POST(self):
            time.sleep(0.35)
            try:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(b"{}")
            except OSError:
                pass

        def log_message(self, format, *args):
            return

    srv, url = _iniciar_servidor_simulado(_TimeoutHandler)
    try:
        r_to = simular_cliente_modo4_offline(20, url_base=url, timeout_s=0.08)
        exigir(r_to["sucesso"] is False and r_to["jogos"] == [], "Timeout não retornou zero jogos.")
        cenarios["timeout_http_zero_jogos"] = True
    finally:
        srv.shutdown()
        srv.server_close()

    # Cenario 2: Erro HTTP 500, JSON truncado e resposta incompleta (19 de 20 jogos)
    modos_resposta = {
        "erro_http_500": (500, b'{"detail":"Erro interno simulado"}'),
        "json_truncado": (200, b'{"sucesso": true, "jogos": [['),
        "sem_campo_jogos": (200, b'{"sucesso": true}'),
        "carteira_incompleta_19_de_20": (
            200,
            json.dumps({"sucesso": True, "jogos": [list(range(1, 51))] * 19}).encode("utf-8"),
        ),
        "bilhete_invalido_49_dezenas": (
            200,
            json.dumps({"sucesso": True, "jogos": [list(range(1, 50))] * 20}).encode("utf-8"),
        ),
    }

    for nome_modo, (st_code, body_bytes) in modos_resposta.items():
        class _RespHandler(BaseHTTPRequestHandler):
            def do_POST(self):
                length = int(self.headers.get("Content-Length", "0"))
                if length:
                    _ = self.rfile.read(length)
                self.send_response(st_code)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(body_bytes)

            def log_message(self, format, *args):
                return

        srv_m, url_m = _iniciar_servidor_simulado(_RespHandler)
        try:
            r_resp = simular_cliente_modo4_offline(20, url_base=url_m, timeout_s=1.0)
            exigir(
                r_resp["sucesso"] is False and r_resp["jogos"] == [],
                f"Cenário HTTP '{nome_modo}' não bloqueou entrega de jogos!",
            )
            cenarios[nome_modo] = True
        finally:
            srv_m.shutdown()
            srv_m.server_close()

    return cenarios


def _testar_falhas_controladas_api() -> dict:
    resultados = {}
    req_gerar_20 = api.OtimizarCoberturaRequest(quantidade_jogos=20, seed=330001, permitir_espelhos=True)

    # A) Violação de selo / manifesto inválido na API -> HTTP 503 em /gerar, /conferir e False em /health
    print(
        "  [TESTE NEGATIVO CONTROLADO - REJEICAO ESPERADA]: Simulando violacao de selo/manifesto na API (HTTP 503)...",
        flush=True,
    )
    fn_verificar_original = api.verificar_selo_modo4
    try:
        def _falha_selo(*args, **kwargs):
            raise api.IntegridadeModo4Error("Manifesto ou selo criptográfico inválido (simulação controlada).")

        api.verificar_selo_modo4 = _falha_selo

        bloqueado_503_gerar = False
        try:
            api.endpoint_lotomania_modo4_gerar(req_gerar_20)
        except HTTPException as exc:
            exigir(exc.status_code == 503, f"Status esperado 503 em /gerar, obtido {exc.status_code}")
            bloqueado_503_gerar = True
        exigir(bloqueado_503_gerar, "Violação de selo em /gerar não retornou HTTP 503.")

        bloqueado_503_conferir = False
        try:
            api.endpoint_lotomania_modo4_conferir(api.ConferirModo4Request(jogos=[list(range(1, 51))], concurso=1))
        except HTTPException as exc:
            exigir(exc.status_code == 503, f"Status esperado 503 em /conferir, obtido {exc.status_code}")
            bloqueado_503_conferir = True
        exigir(bloqueado_503_conferir, "Violação de selo em /conferir não retornou HTTP 503.")

        health_degradado = api.endpoint_health()
        exigir(health_degradado["modo4_disponivel"] is False, "/health não acusou indisponibilidade com selo violado.")
        resultados["manifesto_ou_selo_invalido_http_503"] = True
    finally:
        api.verificar_selo_modo4 = fn_verificar_original

    # B) Erro interno no processo de otimização -> HTTP 500 (zero jogos entregues)
    if api.MotorLotomaniaModo4 is None:
        from motor_lotomania_modo4 import MotorLotomaniaModo4 as _M4
        api.MotorLotomaniaModo4 = _M4

    metodo_orig = api.MotorLotomaniaModo4.gerar_carteira_otimizada_cobertura
    try:
        def _erro_interno(self, *args, **kwargs):
            raise RuntimeError("Erro interno simulado no processo de otimização.")

        api.MotorLotomaniaModo4.gerar_carteira_otimizada_cobertura = _erro_interno
        bloqueado_500 = False
        try:
            api.endpoint_lotomania_modo4_gerar(req_gerar_20)
        except HTTPException as exc:
            exigir(exc.status_code == 500, f"Erro interno deveria retornar HTTP 500, obtido {exc.status_code}")
            bloqueado_500 = True
        exigir(bloqueado_500, "Erro interno no otimizador não lançou HTTP 500.")
        resultados["erro_interno_otimizacao_http_500"] = True
    finally:
        api.MotorLotomaniaModo4.gerar_carteira_otimizada_cobertura = metodo_orig

    # C) Falhas na validação final da carteira gerada pela API -> HTTP 500 (zero jogos entregues)
    saidas_corrompidas = {
        "validacao_sucesso_false": {"sucesso": False, "jogos": [list(range(1, 51))] * 20},
        "validacao_quantidade_divergente": {"sucesso": True, "jogos": [list(range(1, 51))] * 19},
        "validacao_bilhete_49_dezenas": {"sucesso": True, "jogos": [list(range(1, 50))] * 20},
        "validacao_dezena_fora_dominio_101": {"sucesso": True, "jogos": [list(range(2, 51)) + [101]] * 20},
    }
    for nome_v, payload_corrompido in saidas_corrompidas.items():
        try:
            def _retorno_corrompido(self, *args, _p=payload_corrompido, **kwargs):
                return _p

            api.MotorLotomaniaModo4.gerar_carteira_otimizada_cobertura = _retorno_corrompido
            rejeitado_val = False
            try:
                api.endpoint_lotomania_modo4_gerar(req_gerar_20)
            except HTTPException as exc:
                exigir(exc.status_code == 500, f"Cenário '{nome_v}' deveria lançar HTTP 500, obtido {exc.status_code}")
                rejeitado_val = True
            exigir(rejeitado_val, f"Falha de validação final '{nome_v}' não foi bloqueada!")
            resultados[nome_v] = True
        finally:
            api.MotorLotomaniaModo4.gerar_carteira_otimizada_cobertura = metodo_orig

    # D) Ausência de dados obrigatórios em /conferir -> ValidationError / HTTP 422
    rejeitou_vazio = False
    try:
        api.ConferirModo4Request()
    except ValidationError:
        rejeitou_vazio = True
    exigir(rejeitou_vazio, "ConferirModo4Request aceitou ausência de campo obrigatório 'jogos'.")

    rejeitou_lista_vazia_pydantic = False
    try:
        api.ConferirModo4Request(jogos=[], concurso=1)
    except ValidationError:
        rejeitou_lista_vazia_pydantic = True
    exigir(rejeitou_lista_vazia_pydantic, "ConferirModo4Request aceitou jogos=[] vazio.")

    rejeitou_concurso_inexistente = False
    try:
        api.endpoint_lotomania_modo4_conferir(api.ConferirModo4Request(jogos=[list(range(1, 51))], concurso=99999))
    except HTTPException as exc:
        exigir(exc.status_code == 422, f"Esperado HTTP 422 para concurso inexistente, obtido {exc.status_code}")
        rejeitou_concurso_inexistente = True
    exigir(rejeitou_concurso_inexistente, "/conferir não rejeitou concurso inexistente com HTTP 422.")
    resultados["ausencia_dados_conferir_422"] = True

    return resultados


def executar_testes_sem_fallback() -> dict:
    cam_js = localizar_arquivo_projeto(os.path.join("js", "engines", "motor_lotomania_modo4_engine.js"))
    with open(cam_js, "r", encoding="utf-8") as f:
        codigo_js = f.read()

    # 1. Análise estática de ausência de fallback local em JavaScript
    linhas_codigo = [
        ln
        for ln in codigo_js.splitlines()
        if not ln.strip().startswith("//")
        and not ln.strip().startswith("*")
        and not ln.strip().startswith("/*")
    ]
    codigo_executavel = "\n".join(linhas_codigo)

    padroes_proibidos = [
        "Math.random",
        "gerarCarteiraLocal",
        "sample10(",
        "CoverageEngine",
        "PureCoverageEngine",
        "SmartCoverageEngine",
        "MotorLotomaniaB2BEngine",
    ]
    violacoes = [p for p in padroes_proibidos if p in codigo_executavel]
    exigir(len(violacoes) == 0, f"Padrões proibidos de fallback detectados no JS: {violacoes}")
    exigir(MENSAGEM_OBRIGATORIA_OFFLINE in codigo_js, "Mensagem offline ausente no JS.")
    exigir(CLAUSULA_OBRIGATORIA_MODO4 in codigo_js, "Cláusula obrigatória ausente no JS.")
    exigir("http://127.0.0.1:8000/api/v1/lotomania-modo4/gerar" in codigo_js, "URL /gerar ausente no JS.")
    exigir("http://127.0.0.1:8000/api/v1/lotomania-modo4/conferir" in codigo_js, "URL /conferir ausente no JS.")
    exigir("http://127.0.0.1:8000/health" in codigo_js, "URL /health ausente no JS.")
    exigir("Number.isInteger(quantidadeJogos)" in codigo_executavel, "Validação Number.isInteger ausente.")
    exigir("quantidadeJogos < 1 || quantidadeJogos > 10000" in codigo_executavel, "Limites 1..10000 ausentes no JS.")
    exigir("respostaCompleta" in codigo_executavel, "Validação estrita de resposta completa ausente no JS.")
    exigir("jogos: []" in codigo_executavel, "Retorno vazio 'jogos: []' ausente no JS.")

    # Verifica isolamento de interface no index.html e js/ui.js
    cam_html = localizar_arquivo_projeto("index.html")
    with open(cam_html, "r", encoding="utf-8") as f:
        html_content = f.read()

    match_select = re.search(
        r'<select[^>]*id="select-estrategia-lotomania"[^>]*>(.*?)</select>',
        html_content,
        re.DOTALL,
    )
    exigir(match_select is not None, "Seletor #select-estrategia-lotomania não encontrado no index.html")
    opcoes_select_legado = match_select.group(1)
    exigir('value="modo_4"' not in opcoes_select_legado, "modo_4 ainda presente no seletor legado!")
    exigir('id="tab-btn-lotomania-modo4"' in html_content, "Botão de aba dedicada MODO 4 ausente.")
    exigir('id="subpanel-lotomania-modo4"' in html_content, "Subpainel dedicado MODO 4 ausente.")
    exigir('max="10000"' in html_content, "Atributo max='10000' ausente no index.html.")

    cam_ui = localizar_arquivo_projeto(os.path.join("js", "ui.js"))
    with open(cam_ui, "r", encoding="utf-8") as f:
        ui_content = f.read()
    exigir("MotorLotomaniaModo4Engine.gerarCarteira" in ui_content, "Chamada ao MotorLotomaniaModo4Engine ausente em ui.js.")
    exigir(MENSAGEM_OBRIGATORIA_OFFLINE in ui_content, "Mensagem offline ausente em ui.js.")

    # 2. Teste de indisponibilidade (API desligada -> zero jogos e mensagem obrigatória)
    res_offline = simular_cliente_modo4_offline(20)
    exigir(res_offline["sucesso"] is False, "Cliente offline deveria retornar sucesso=False.")
    exigir(res_offline["jogos"] == [], "Cliente offline deveria retornar jogos=[].")
    exigir(len(res_offline["jogos"]) == 0, "Cliente offline deveria retornar 0 jogos.")
    exigir(res_offline["erro"] == MENSAGEM_OBRIGATORIA_OFFLINE, "Mensagem de erro offline incorreta.")

    entradas_invalidas_cliente = [0, -1, 10001, "10", 10.5, True, False, None]
    for val in entradas_invalidas_cliente:
        r_inv = simular_cliente_modo4_offline(val)
        exigir(r_inv["sucesso"] is False, f"Entrada inválida {val!r} não rejeitada no cliente.")
        exigir(r_inv["jogos"] == [], f"Entrada inválida {val!r} gerou jogos no cliente.")

    # 3. Cenários HTTP simulados (timeout, HTTP 500, JSON truncado, resposta incompleta)
    cenarios_http = _testar_cenarios_http_cliente()

    # 4. Validação estrita do contrato Pydantic v2
    entradas_invalidas_api = [
        {"quantidade_jogos": 0},
        {"quantidade_jogos": -1},
        {"quantidade_jogos": 10001},
        {"quantidade_jogos": "10"},
        {"quantidade_jogos": 10.5},
        {"quantidade_jogos": True},
        {"quantidade_jogos": False},
        {"quantidade_jogos": None},
        {"quantidade_jogos": 20, "seed": "330001"},
        {"quantidade_jogos": 20, "seed": 330001.5},
        {"quantidade_jogos": 20, "seed": True},
        {"quantidade_jogos": 20, "permitir_espelhos": "true"},
    ]
    rejeicoes_pydantic = 0
    for payload in entradas_invalidas_api:
        rejeitado = False
        try:
            api.OtimizarCoberturaRequest(**payload)
        except ValidationError:
            rejeitado = True
        exigir(rejeitado, f"Payload inválido aceito indevidamente: {payload}")
        rejeicoes_pydantic += 1

    for qtd_valida in [1, 100, 500, 1000, 5000, 10000]:
        req_ok = api.OtimizarCoberturaRequest(
            quantidade_jogos=qtd_valida, seed=330001, permitir_espelhos=True
        )
        exigir(req_ok.quantidade_jogos == qtd_valida, f"Quantidade válida {qtd_valida} alterada.")

    # 5. Teste positivo dos handlers da API (`/health`, `/api/v1/lotomania-modo4/gerar`)
    health_resp = api.endpoint_health()
    exigir(health_resp["status"] == "ok", "Status /health diverge de 'ok'.")
    exigir(health_resp["modo4_disponivel"] is True, "modo4_disponivel deveria ser True.")
    exigir(health_resp["modo4"]["selo_valido"] is True, "selo_valido deveria ser True.")
    exigir(health_resp["modo4"]["limite_min_jogos"] == 1, "limite_min_jogos != 1.")
    exigir(health_resp["modo4"]["limite_max_jogos"] == 10000, "limite_max_jogos != 10000.")

    req_gerar_20 = api.OtimizarCoberturaRequest(quantidade_jogos=20, seed=330001, permitir_espelhos=True)
    resp_gerar_20 = api.endpoint_lotomania_modo4_gerar(req_gerar_20)
    exigir(resp_gerar_20["sucesso"] is True, "Falha em endpoint_lotomania_modo4_gerar(20).")
    exigir(len(resp_gerar_20["jogos"]) == 20, "Quantidade gerada na API diverge de 20.")
    exigir(
        resp_gerar_20["hash_carteira_sha256_v1"]
        == "a98c0b0267b1c2d91c630b363bb9be6744dd1d2a6d6943d447f869d705844f0f",
        "Hash v1 da carteira de 20 jogos via API diverge do oficial.",
    )

    # 6. Cenários negativos controlados nos handlers FastAPI
    cenarios_api_negativos = _testar_falhas_controladas_api()
    print(
        "  [TESTE NEGATIVO CONTROLADO - REJEICAO ESPERADA]: Bloqueios 503/500/422 confirmados com zero jogos entregues.",
        flush=True,
    )

    return {
        "sucesso": True,
        "arquivo_js_auditado": cam_js,
        "padroes_proibidos_verificados": padroes_proibidos,
        "violacoes_fallback_encontradas": 0,
        "isolamento_interface_verificado": True,
        "teste_api_desligada_zero_jogos": {
            "sucesso_retorno": res_offline["sucesso"],
            "jogos_gerados": len(res_offline["jogos"]),
            "mensagem_exata": res_offline["erro"],
        },
        "cenarios_resiliencia_http": cenarios_http,
        "cenarios_negativos_api": cenarios_api_negativos,
        "rejeicoes_cliente_js": len(entradas_invalidas_cliente),
        "rejeicoes_pydantic_api": rejeicoes_pydantic,
        "bloqueio_http_503_selo_invalido": True,
        "teste_negativo_controlado_rejeicao_esperada": True,
    }


def test_resiliencia_http_timeout_e_incompleta():
    c = _testar_cenarios_http_cliente()
    exigir(all(c.values()) and len(c) == 6, "Nem todos os cenários HTTP passaram.")


def test_falhas_controladas_handlers_api():
    r = _testar_falhas_controladas_api()
    exigir(all(r.values()) and len(r) == 7, "Nem todos os cenários negativos da API passaram.")


def test_sem_fallback_completo():
    r = executar_testes_sem_fallback()
    exigir(r["sucesso"] is True and r["violacoes_fallback_encontradas"] == 0, "Falha na auditoria sem fallback.")


class TestModo4SemFallback(unittest.TestCase):
    def test_cenarios_http_timeout_erro_incompleta(self):
        test_resiliencia_http_timeout_e_incompleta()

    def test_handlers_api_negativos_fail_closed(self):
        test_falhas_controladas_handlers_api()

    def test_auditoria_estatica_e_dinamica_sem_fallback(self):
        test_sem_fallback_completo()


if __name__ == "__main__":
    resultado = executar_testes_sem_fallback()
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
