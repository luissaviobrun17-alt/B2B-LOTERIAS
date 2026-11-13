# -*- coding: utf-8 -*-
"""
GERADOR DE EVIDENCIAS E RELATORIO DA ETAPA 5 - LOTOFACIL MODO 4
===============================================================
Executa validacao ponta a ponta em homologacao isolada (comparativo 3 vias,
alternancia de feature flag, testes fail-closed, auditoria AST e matematica
<= 1e-12, diagnostico Etapa 3 vs Etapa 4 e experimento controlado de despacho)
e grava os artefatos auditaveis:
  - auditoria/lotofacil_modo4/manifesto_etapa5.json
  - auditoria/lotofacil_modo4/etapa_05_evidencias.json
  - auditoria/lotofacil_modo4/ETAPA_05_INTEGRACAO_API.md
"""

from __future__ import annotations

from datetime import datetime, timezone
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import shutil
import socket
import tempfile
import threading
import time
from typing import Any, Dict, List, Mapping, Tuple

import api as api_producao

from lotofacil_modo4.etapa1_regras_oficiais import CLAUSULA_MATEMATICA_OBRIGATORIA
from lotofacil_modo4.etapa2_funcao_objetivo import NOMES_COMPONENTES
from lotofacil_modo4.etapa4_arquitetura_adaptativa import (
    HISTORICO_GERACAO_ETAPA4,
    VERSAO_ARQUITETURA_ETAPA4,
)
from lotofacil_modo4.etapa4_referencia_independente import (
    auditar_conformidade_etapa4_ref,
    auditar_independencia_ast_etapa4,
    avaliar_carteira_ref_etapa4,
)
from lotofacil_modo4.etapa5_api_homologacao import (
    ConfigHomologacaoLotofacilModo4,
    ServidorHttpHomologacao,
    alternar_feature_flag_homologacao,
    chamar_api_lotofacil_modo4_seguro,
    criar_app_homologacao,
)
from lotofacil_modo4.etapa5_experimento_despacho import (
    ARQUIVOS_PRODUCAO_INALTERAVEIS_HOMOLOGACAO,
    BASE_DIR_PADRAO,
    VERSAO_MODULO_ETAPA5,
    calcular_sha256_arquivo,
    diagnosticar_trajetorias_etapa3_vs_etapa4,
    executar_experimento_controlado_despacho,
    garantir_integridade_etapa5_ou_falhar,
    gerar_manifesto_etapa5,
)


def _hashes_producao(base_dir: str) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for rel in ARQUIVOS_PRODUCAO_INALTERAVEIS_HOMOLOGACAO:
        p = os.path.join(base_dir, rel.replace("/", os.sep))
        out[rel] = calcular_sha256_arquivo(p) if os.path.isfile(p) else None
    return out


def _comparar_3_vias_ao_vivo() -> Dict[str, Any]:
    """
    Executa requisicoes HTTP reais contra 3 servidores simultaneos:
      - Via A: `api.app` original (sem modificacao em api.py)
      - Via B: aplicacao integrada isolada com feature flag OFF (`False`)
      - Via C: aplicacao integrada isolada com feature flag ON (`True`)
    """
    app_b = criar_app_homologacao(ConfigHomologacaoLotofacilModo4(lotofacil_modo4_ativo=False))
    app_c = criar_app_homologacao(ConfigHomologacaoLotofacilModo4(lotofacil_modo4_ativo=True))

    with (
        ServidorHttpHomologacao(api_producao.app) as srv_a,
        ServidorHttpHomologacao(app_b) as srv_b,
        ServidorHttpHomologacao(app_c) as srv_c,
    ):
        # 1. /health nas 3 vias
        h_a = chamar_api_lotofacil_modo4_seguro(srv_a.base_url, endpoint="/health", metodo="GET")
        h_b = chamar_api_lotofacil_modo4_seguro(srv_b.base_url, endpoint="/health", metodo="GET")
        h_c = chamar_api_lotofacil_modo4_seguro(srv_c.base_url, endpoint="/health", metodo="GET")

        da = dict(h_a["dados_brutos"] or {})
        db = dict(h_b["dados_brutos"] or {})
        dc = dict(h_c["dados_brutos"] or {})

        chaves_a = set(da.keys())
        paridade_health_b = all(db.get(k) == da.get(k) for k in chaves_a)
        paridade_health_c = all(dc.get(k) == da.get(k) for k in chaves_a)
        flag_off_health_ok = (
            isinstance(db.get("lotofacil_modo4"), dict)
            and db["lotofacil_modo4"].get("disponivel") is False
            and db["lotofacil_modo4"].get("feature_flag_ativa") is False
        )
        flag_on_health_ok = (
            isinstance(dc.get("lotofacil_modo4"), dict)
            and dc["lotofacil_modo4"].get("disponivel") is True
            and dc["lotofacil_modo4"].get("feature_flag_ativa") is True
        )

        # 2. Lotomania MODO 4 deterministica (seed=42) nas 3 vias
        payload_lm4 = {"quantidade_jogos": 6, "permitir_espelhos": True, "seed": 42, "trace": False}
        lm4_a = chamar_api_lotofacil_modo4_seguro(
            srv_a.base_url, payload_lm4, endpoint="/api/v1/lotomania-modo4/gerar"
        )
        lm4_b = chamar_api_lotofacil_modo4_seguro(
            srv_b.base_url, payload_lm4, endpoint="/api/v1/lotomania-modo4/gerar"
        )
        lm4_c = chamar_api_lotofacil_modo4_seguro(
            srv_c.base_url, payload_lm4, endpoint="/api/v1/lotomania-modo4/gerar"
        )
        da_lm4 = lm4_a["dados_brutos"] or {}
        db_lm4 = lm4_b["dados_brutos"] or {}
        dc_lm4 = lm4_c["dados_brutos"] or {}
        lm4_jogos_identicos = (
            da_lm4.get("jogos") == db_lm4.get("jogos") == dc_lm4.get("jogos")
            and isinstance(da_lm4.get("jogos"), list)
            and len(da_lm4.get("jogos", [])) == 6
        )

        # 3. Motores legados (Lotofacil v2.5, Lotomania legada, Timemania)
        legados: List[Dict[str, Any]] = []
        rotas_legadas = [
            (
                "/api/v1/motor-lotofacil",
                {"quantidade_jogos": 4, "estrategia": "equilibrada", "sniper": True},
            ),
            (
                "/api/v1/motor-lotomania",
                {"quantidade_jogos": 4, "estrategia": "equilibrada"},
            ),
            (
                "/api/v1/motor-timemania",
                {"quantidade_jogos": 4, "estrategia": "equilibrada"},
            ),
        ]
        for ep, pl in rotas_legadas:
            ra = chamar_api_lotofacil_modo4_seguro(srv_a.base_url, pl, endpoint=ep)
            rb = chamar_api_lotofacil_modo4_seguro(srv_b.base_url, pl, endpoint=ep)
            rc = chamar_api_lotofacil_modo4_seguro(srv_c.base_url, pl, endpoint=ep)
            ok_rota = (
                ra["status_http"] == 200
                and rb["status_http"] == 200
                and rc["status_http"] == 200
                and set((ra["dados_brutos"] or {}).keys()) == set((rb["dados_brutos"] or {}).keys())
                and set((ra["dados_brutos"] or {}).keys()) == set((rc["dados_brutos"] or {}).keys())
            )
            legados.append(
                {
                    "endpoint": ep,
                    "status_a": ra["status_http"],
                    "status_b": rb["status_http"],
                    "status_c": rc["status_http"],
                    "paridade_esquema_e_operacao": ok_rota,
                }
            )

        # 4. Lotofacil MODO 4 nas 3 vias e rollback em runtime OFF -> ON -> OFF
        pl_lf4 = {"quantidade_jogos": 6, "semente": 42, "max_avaliacoes": 180}
        lf_a = chamar_api_lotofacil_modo4_seguro(srv_a.base_url, pl_lf4)
        lf_b = chamar_api_lotofacil_modo4_seguro(srv_b.base_url, pl_lf4)
        lf_c = chamar_api_lotofacil_modo4_seguro(srv_c.base_url, pl_lf4)

        alternar_feature_flag_homologacao(app_c, False)
        lf_c_rollback = chamar_api_lotofacil_modo4_seguro(srv_c.base_url, pl_lf4)
        alternar_feature_flag_homologacao(app_c, True)
        lf_c_reativado = chamar_api_lotofacil_modo4_seguro(srv_c.base_url, pl_lf4)

        rollback_ok = (
            lf_a["status_http"] == 404
            and lf_b["status_http"] == 503
            and len(lf_b["jogos"]) == 0
            and lf_c["status_http"] == 200
            and len(lf_c["jogos"]) == 6
            and lf_c_rollback["status_http"] == 503
            and len(lf_c_rollback["jogos"]) == 0
            and lf_c_reativado["status_http"] == 200
            and lf_c_reativado["jogos"] == lf_c["jogos"]
        )

    return {
        "concluido_sem_regressao": bool(
            paridade_health_b
            and paridade_health_c
            and flag_off_health_ok
            and flag_on_health_ok
            and lm4_jogos_identicos
            and all(x["paridade_esquema_e_operacao"] for x in legados)
            and rollback_ok
        ),
        "health_paridade_chaves_producao": paridade_health_b and paridade_health_c,
        "health_flag_off_correta": flag_off_health_ok,
        "health_flag_on_correta": flag_on_health_ok,
        "lotomania_modo4_jogos_identicos_3_vias": lm4_jogos_identicos,
        "motores_legados_3_vias": legados,
        "lotofacil_modo4_ciclo_flag_e_rollback": {
            "status_via_a_producao": lf_a["status_http"],
            "status_via_b_flag_off": lf_b["status_http"],
            "jogos_via_b_flag_off": len(lf_b["jogos"]),
            "status_via_c_flag_on": lf_c["status_http"],
            "jogos_via_c_flag_on": len(lf_c["jogos"]),
            "status_rollback_runtime_off": lf_c_rollback["status_http"],
            "jogos_rollback_runtime_off": len(lf_c_rollback["jogos"]),
            "status_reativacao_runtime_on": lf_c_reativado["status_http"],
            "determinismo_pos_reativacao": lf_c_reativado["jogos"] == lf_c["jogos"],
            "aprovado": rollback_ok,
        },
    }


def _validar_e2e_e_fail_closed() -> Dict[str, Any]:
    """
    Executa matriz ponta a ponta na API de homologacao (ON) conferindo cada
    resposta contra a referencia independente (<= 1e-12) e testa todos os
    cenarios negativos fail-closed (adulteracao de selo/hash, rede offline,
    timeout, HTTP 500/503, JSON corrompido, parametro historico e entradas invalidas).
    """
    app_on = criar_app_homologacao(ConfigHomologacaoLotofacilModo4(lotofacil_modo4_ativo=True))
    casos_e2e = [
        {
            "id": "e2e_exata_pequena_p16_J4",
            "payload": {
                "pool": list(range(1, 17)),
                "bloqueadas": [21, 22, 23, 24, 25],
                "quantidade_jogos": 4,
                "max_avaliacoes": 2000,
                "max_iteracoes": 2000,
                "semente": 42,
            },
        },
        {
            "id": "e2e_regular_orc56_p25",
            "payload": {
                "pool": list(range(1, 26)),
                "orcamento_brl": "56.00",
                "tipo_concurso": "concurso_regular",
                "semente": 42,
                "max_avaliacoes": 260,
            },
        },
        {
            "id": "e2e_final_zero_fixas_todos_p20_J8",
            "payload": {
                "pool": list(range(1, 21)),
                "fixas": [1, 2, 3],
                "bloqueadas": [21, 22, 23, 24, 25],
                "modo_fixas": "todos_os_jogos",
                "quantidade_jogos": 8,
                "tipo_concurso": "concurso_final_zero",
                "semente": 42,
                "max_avaliacoes": 200,
            },
        },
        {
            "id": "e2e_independencia_fixas_pool_p22_J10",
            "payload": {
                "pool": list(range(1, 23)),
                "fixas": list(range(1, 17)),
                "bloqueadas": [23, 24, 25],
                "modo_fixas": "composicao_pool",
                "quantidade_jogos": 10,
                "tipo_concurso": "lotofacil_independencia",
                "semente": 42,
                "max_avaliacoes": 220,
            },
        },
        {
            "id": "e2e_mista_heterogenea_p21_2x16_6x15",
            "payload": {
                "pool": list(range(1, 22)),
                "fixas": [1, 2],
                "bloqueadas": [22, 23, 24, 25],
                "tamanhos_jogos": [16, 16, 15, 15, 15, 15, 15, 15],
                "semente": 42,
                "max_avaliacoes": 240,
            },
        },
        {
            "id": "e2e_micro_orcamento_p25_J12_B30",
            "payload": {
                "pool": list(range(1, 26)),
                "quantidade_jogos": 12,
                "semente": 42,
                "max_avaliacoes": 30,
            },
        },
    ]

    resultados_e2e: List[Dict[str, Any]] = []
    maior_div_e2e = 0.0
    todos_e2e_ok = True

    with ServidorHttpHomologacao(app_on) as srv:
        for c in casos_e2e:
            resp = chamar_api_lotofacil_modo4_seguro(srv.base_url, c["payload"])
            dados = resp["dados_brutos"] or {}
            ok_req = resp["sucesso"] and resp["status_http"] == 200
            if not ok_req:
                todos_e2e_ok = False
                resultados_e2e.append({"id": c["id"], "ok": False, "erro": resp["erro"]})
                continue

            esp = dados["especificacao"]
            av_ref = avaliar_carteira_ref_etapa4(
                dados["jogos"],
                pool=esp["pool"],
                fixas=esp["fixas"],
                bloqueadas=esp["bloqueadas"],
                modo_fixas=esp["modo_fixas"],
                pesos=esp["pesos"],
            )
            conf = auditar_conformidade_etapa4_ref(
                dados["jogos"],
                pool=esp["pool"],
                fixas=esp["fixas"],
                bloqueadas=esp["bloqueadas"],
                modo_fixas=esp["modo_fixas"],
                tamanhos_esperados=esp["tamanhos_jogos"],
            )
            div_f = abs(float(dados["funcao_objetivo_F"]) - float(av_ref["funcao_objetivo_F"]))
            div_comp = max(
                abs(
                    float(dados["componentes"][k])
                    - float(av_ref["componentes"][k])
                )
                for k in NOMES_COMPONENTES
            )
            maior_div_e2e = max(maior_div_e2e, div_f, div_comp)

            dist6 = dados.get("distincao_seis_grandezas_probabilisticas", {})
            chaves_dist_esperadas = {
                "1_probabilidade_individual",
                "2_probabilidade_pareada_detalhes",
                "3_esperanca_N_prem",
                "3_variancia_N_prem",
                "4_cota_inferior_dawson_sankoff",
                "4_cota_superior_hunter_worsley",
                "5_probabilidade_exata_uniao",
                "6_nota_escopo_S_prob",
            }
            seis_grandezas_ok = chaves_dist_esperadas.issubset(dist6.keys())
            ok_dist = (
                seis_grandezas_ok
                and dados.get("historico_utilizado") is None
                and dados.get("fallback_executado") is False
                and conf["conforme"] is True
                and div_f <= 1e-12
                and div_comp <= 1e-12
            )
            if not ok_dist:
                todos_e2e_ok = False

            resultados_e2e.append(
                {
                    "id": c["id"],
                    "ok": ok_dist,
                    "algoritmo": dados.get("algoritmo_selecionado"),
                    "quantidade_jogos": len(dados["jogos"]),
                    "custo_total_brl": esp["custo_total_brl"],
                    "F_api": dados["funcao_objetivo_F"],
                    "F_ref_independente": av_ref["funcao_objetivo_F"],
                    "divergencia_F": div_f,
                    "divergencia_max_componente": div_comp,
                    "conforme_ref": conf["conforme"],
                    "seis_grandezas_distintas_presentes": seis_grandezas_ok,
                }
            )

        # Teste /avaliar cruzado
        amostra = resultados_e2e[0]
        resp_av = chamar_api_lotofacil_modo4_seguro(
            srv.base_url,
            {
                "carteira": [
                    list(range(1, 16)),
                    [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16],
                ],
                "pool": list(range(1, 17)),
                "bloqueadas": [21, 22, 23, 24, 25],
            },
            endpoint="/api/v1/lotofacil-modo4/avaliar",
        )
        av_ok = (
            resp_av["status_http"] == 200
            and resp_av["dados_brutos"]["auditoria_referencia_independente"]["divergencia_F"] <= 1e-12
        )

        # Cenarios negativos HTTP 422
        neg_422_specs = [
            ("historico_proibido", {"quantidade_jogos": 4, "historico": [[1, 2, 3]]}),
            ("usar_historico_proibido", {"quantidade_jogos": 4, "usar_historico": True}),
            (
                "conflito_fixas_bloqueadas",
                {"quantidade_jogos": 2, "fixas": [1, 2], "bloqueadas": [2, 24, 25]},
            ),
            ("orcamento_insuficiente", {"orcamento_brl": "3.00"}),
            (
                "ambiguidade_tamanhos_quantidade",
                {"quantidade_jogos": 2, "tamanhos_jogos": [15, 15]},
            ),
        ]
        neg_422_resultados: List[Dict[str, Any]] = []
        for nome_neg, pl_neg in neg_422_specs:
            rn = chamar_api_lotofacil_modo4_seguro(srv.base_url, pl_neg)
            ok_neg = (
                rn["sucesso"] is False
                and rn["status_http"] == 422
                and len(rn["jogos"]) == 0
                and rn["fallback_executado"] is False
            )
            neg_422_resultados.append(
                {"caso": nome_neg, "status_http": rn["status_http"], "jogos": len(rn["jogos"]), "aprovado": ok_neg}
            )

    # Cenarios fail-closed de rede / timeout / 500 / 503 / JSON corrompido
    class _SimuladorFalhasHandler(BaseHTTPRequestHandler):
        def log_message(self, format: str, *args: Any) -> None:
            return

        def do_POST(self) -> None:
            tam = int(self.headers.get("Content-Length", "0") or 0)
            if self.path == "/timeout":
                time.sleep(0.6)
                try:
                    self.send_response(200)
                    self.end_headers()
                    self.wfile.write(b"{}")
                except OSError:
                    pass
                return
            if tam > 0:
                _ = self.rfile.read(tam)
            if self.path == "/erro500":
                self.send_response(500)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"erro": "INTERNAL_SIMULATED"}')
                return
            if self.path == "/corrompido":
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"jogos": [[1,2')
                return
            self.send_response(503)
            self.end_headers()

    srv_sim = ThreadingHTTPServer(("127.0.0.1", 0), _SimuladorFalhasHandler)
    port_sim = srv_sim.server_port
    t_sim = threading.Thread(target=srv_sim.serve_forever, daemon=True)
    t_sim.start()
    try:
        # Descobre porta fechada efemera
        s_dead = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_dead.bind(("127.0.0.1", 0))
        dead_port = s_dead.getsockname()[1]
        s_dead.close()

        falhas_cliente = []
        for nome_f, url_f, ep_f, tout in (
            ("porta_desconectada", f"http://127.0.0.1:{dead_port}", "/api/v1/lotofacil-modo4/gerar", 1.5),
            ("timeout_rede", f"http://127.0.0.1:{port_sim}", "/timeout", 0.15),
            ("http_500_simulado", f"http://127.0.0.1:{port_sim}", "/erro500", 2.0),
            ("http_503_simulado", f"http://127.0.0.1:{port_sim}", "/indisponivel", 2.0),
            ("json_corrompido", f"http://127.0.0.1:{port_sim}", "/corrompido", 2.0),
        ):
            rf = chamar_api_lotofacil_modo4_seguro(
                url_f, {"quantidade_jogos": 2}, endpoint=ep_f, timeout_s=tout
            )
            ok_f = rf["sucesso"] is False and len(rf["jogos"]) == 0 and rf["fallback_executado"] is False
            falhas_cliente.append(
                {
                    "caso": nome_f,
                    "erro": rf["erro"],
                    "status_http": rf["status_http"],
                    "jogos": len(rf["jogos"]),
                    "fallback_executado": rf["fallback_executado"],
                    "aprovado": ok_f,
                }
            )
    finally:
        srv_sim.shutdown()
        srv_sim.server_close()

    # Teste de adulteracao em diretorio temporario isolado (Exigencia 5/6 fail-closed)
    tamper_resultados: List[Dict[str, Any]] = []
    with tempfile.TemporaryDirectory() as tmpdir:
        for rel in (
            "lotofacil_modo4/__init__.py",
            "lotofacil_modo4/etapa1_regras_oficiais.py",
            "lotofacil_modo4/sincronizador_caixa.py",
            "lotofacil_modo4/gerar_evidencias_etapa1.py",
            "lotofacil_modo4/etapa2_funcao_objetivo.py",
            "lotofacil_modo4/etapa2_referencia_independente.py",
            "lotofacil_modo4/gerar_evidencias_etapa2.py",
            "lotofacil_modo4/etapa3_otimizadores.py",
            "lotofacil_modo4/etapa3_referencia_independente.py",
            "lotofacil_modo4/gerar_evidencias_etapa3.py",
            "lotofacil_modo4/etapa4_referencia_independente.py",
            "lotofacil_modo4/etapa4_arquitetura_adaptativa.py",
            "lotofacil_modo4/gerar_evidencias_etapa4.py",
            "lotofacil_modo4/dados/lotofacil_oficial_caixa.json",
            "lotofacil_modo4/dados/caixa_lotofacil_oficial.xlsx",
            "auditoria/lotofacil_modo4/auditoria_base_caixa_etapa1.json",
            "auditoria/lotofacil_modo4/etapa_01_evidencias.json",
            "auditoria/lotofacil_modo4/ETAPA_01_REGRAS_E_FORMALIZACAO_MATEMATICA.md",
            "auditoria/lotofacil_modo4/etapa_02_evidencias.json",
            "auditoria/lotofacil_modo4/ETAPA_02_FUNCAO_OBJETIVO_E_OTIMIZACAO.md",
            "auditoria/lotofacil_modo4/etapa_03_evidencias.json",
            "auditoria/lotofacil_modo4/ETAPA_03_ALGORITMOS_DE_OTIMIZACAO.md",
            "testes/test_lotofacil_modo4_etapa1.py",
            "testes/test_lotofacil_modo4_etapa2.py",
            "testes/test_lotofacil_modo4_etapa3.py",
            "testes/test_lotofacil_modo4_etapa4.py",
            "data/lotofacil.json",
            "data/lotomania.json",
            "motor_lotomania_modo4.py",
            "verificador_selo_modo4.py",
            "chave_publica_modo4.pem",
            "manifesto_modo4.json",
            "manifesto_modo4.sig",
        ):
            src = os.path.join(BASE_DIR_PADRAO, rel.replace("/", os.sep))
            dst = os.path.join(tmpdir, rel.replace("/", os.sep))
            os.makedirs(os.path.dirname(dst), exist_ok=True)
            shutil.copy2(src, dst)

        for caso_t, alvo_rel in (
            ("adulteracao_artefato_lotofacil_etapa2", "lotofacil_modo4/etapa2_funcao_objetivo.py"),
            ("adulteracao_motor_lotomania_selo", "motor_lotomania_modo4.py"),
        ):
            alvo_abs = os.path.join(tmpdir, alvo_rel.replace("/", os.sep))
            original_bytes = open(alvo_abs, "rb").read()
            try:
                with open(alvo_abs, "wb") as f:
                    f.write(original_bytes + b"\n# adulterado\n")
                app_tmp = criar_app_homologacao(
                    ConfigHomologacaoLotofacilModo4(
                        lotofacil_modo4_ativo=True,
                        diretorio_base=tmpdir,
                    )
                )
                with ServidorHttpHomologacao(app_tmp) as srv_t:
                    rt = chamar_api_lotofacil_modo4_seguro(
                        srv_t.base_url, {"quantidade_jogos": 2}
                    )
                    rh = chamar_api_lotofacil_modo4_seguro(
                        srv_t.base_url, endpoint="/health", metodo="GET"
                    )
                ok_t = (
                    rt["sucesso"] is False
                    and rt["status_http"] == 503
                    and len(rt["jogos"]) == 0
                    and rt["fallback_executado"] is False
                    and rh["dados_brutos"]["lotofacil_modo4"]["disponivel"] is False
                )
                tamper_resultados.append(
                    {
                        "caso": caso_t,
                        "status_http_gerar": rt["status_http"],
                        "jogos_gerados": len(rt["jogos"]),
                        "health_disponivel": rh["dados_brutos"]["lotofacil_modo4"]["disponivel"],
                        "aprovado": ok_t,
                    }
                )
            finally:
                with open(alvo_abs, "wb") as f:
                    f.write(original_bytes)

    return {
        "todos_e2e_ok": bool(todos_e2e_ok and av_ok),
        "maior_divergencia_e2e_vs_ref": maior_div_e2e,
        "casos_e2e": resultados_e2e,
        "avaliar_endpoint_ok": av_ok,
        "negativos_422_ok": all(x["aprovado"] for x in neg_422_resultados),
        "negativos_422": neg_422_resultados,
        "fail_closed_cliente_ok": all(x["aprovado"] for x in falhas_cliente),
        "fail_closed_cliente": falhas_cliente,
        "adulteracao_fail_closed_ok": all(x["aprovado"] for x in tamper_resultados),
        "adulteracao_fail_closed": tamper_resultados,
        "amostra_primeiro_caso": amostra["id"],
    }


def _sanitizar_sem_travessao(texto: str) -> str:
    return texto.replace("\u2014", ",").replace("\u2013", "-")


def _renderizar_markdown_etapa5(ev: Mapping[str, Any]) -> str:
    tr = ev["diagnostico_etapa3_vs_etapa4"]
    exp = ev["experimento_controlado_despacho"]
    bl_a = exp["bloco_a_limiar_micro"]
    bl_b = exp["bloco_b_inicializacao_mista"]
    comp3 = ev["comparativo_3_vias"]
    e2e = ev["validacao_e2e_e_fail_closed"]
    pres_pos = ev["preservacao_pos_execucao"]
    ast4 = ev["auditoria_ast_referencia_etapa4"]

    linhas: List[str] = [
        "# ETAPA 5: INTEGRACAO EM HOMOLOGACAO ISOLADA E VALIDACAO PONTA A PONTA",
        "",
        f"**Gerado em (UTC):** {ev['gerado_em_utc']}  ",
        f"**Versao do motor Etapa 4:** `{ev['versao_arquitetura_etapa4']}`  ",
        f"**Versao do modulo Etapa 5:** `{ev['versao_modulo_etapa5']}`  ",
        f"**Flag `HISTORICO_GERACAO_ETAPA4`:** `{ev['historico_geracao_etapa4']}`  ",
        f"**Feature flag padrao em homologacao (`lotofacil_modo4_ativo`):** `{ev['feature_flag_padrao']}`",
        "",
        "> **Clausula cientifica obrigatoria:**  ",
        f"> {CLAUSULA_MATEMATICA_OBRIGATORIA}",
        "",
        "---",
        "",
        "## 1. Resumo Executivo da Homologacao Isolada",
        "",
        f"- **Arquivos de producao preservados intactos:** `{ev['producao_inalterada']}` (`api.py`, `motor_lotofacil.py`, `index.html`, `js/ui.js`, `B2B_Loterias_Mobile.html` com hashes SHA-256 identicos antes e depois da Etapa 5).",
        f"- **Artefatos congelados das Etapas 1, 2, 3 e 4:** `{pres_pos['verificados_etapas_1_2_3']}/{pres_pos['esperados_etapas_1_2_3']}` (Etapas 1 a 3) e `{pres_pos['verificados_etapa_4']}/{pres_pos['esperados_etapa_4']}` (Etapa 4) integros.",
        f"- **Selo criptografico Lotomania MODO 4 v1.2:** `{pres_pos['selo_lotomania_valido']}` e base oficial CAIXA integra (`{pres_pos['verificados_dados_e_lotomania']}/{pres_pos['esperados_dados_e_lotomania']}`).",
        f"- **Comparativo 3 vias ao vivo (`api.py` pura vs Flag OFF vs Flag ON):** `concluido_sem_regressao={comp3['concluido_sem_regressao']}`.",
        f"- **Equivalencia matematica E2E vs referencia AST-isolada:** divergencia maxima `{e2e['maior_divergencia_e2e_vs_ref']:.3e}` (`<= 1e-12`).",
        f"- **Seguranca fail-closed (selo adulterado, API offline, timeout, HTTP 500/503, JSON corrompido, `historico`):** 0 jogos retornados e `fallback_executado=False` em 100% dos cenarios.",
        "",
        "---",
        "",
        "## 2. Comparativo 3 Vias ao Vivo (HTTP Real em Loopback)",
        "",
        "| Verificacao | Via A (`api.py` atual) | Via B (Integrada Flag OFF) | Via C (Integrada Flag ON) | Resultado |",
        "| :--- | :--- | :--- | :--- | :--- |",
        f"| `GET /health` preservacao integral de chaves | Baseline | Identico (`{comp3['health_paridade_chaves_producao']}`) | Identico (`{comp3['health_paridade_chaves_producao']}`) | Aprovado |",
        f"| `/health -> lotofacil_modo4.disponivel` | Ausente | `False` | `True` | Isolado por flag |",
        f"| `POST /api/v1/lotomania-modo4/gerar` (`seed=42`) | Baseline (6 jogos) | Identico (`{comp3['lotomania_modo4_jogos_identicos_3_vias']}`) | Identico (`{comp3['lotomania_modo4_jogos_identicos_3_vias']}`) | Zero interferencia |",
        f"| `POST /api/v1/lotofacil-modo4/gerar` | HTTP `{comp3['lotofacil_modo4_ciclo_flag_e_rollback']['status_via_a_producao']}` | HTTP `{comp3['lotofacil_modo4_ciclo_flag_e_rollback']['status_via_b_flag_off']}` (0 jogos) | HTTP `{comp3['lotofacil_modo4_ciclo_flag_e_rollback']['status_via_c_flag_on']}` (6 jogos) | Rollback em runtime OK |",
        "",
        "| Motor legado avaliado | Status A | Status B | Status C | Paridade de contrato |",
        "| :--- | :--- | :--- | :--- | :--- |",
    ]
    for ml in comp3["motores_legados_3_vias"]:
        linhas.append(
            f"| `{ml['endpoint']}` | {ml['status_a']} | {ml['status_b']} | {ml['status_c']} | `{ml['paridade_esquema_e_operacao']}` |"
        )

    linhas.extend(
        [
            "",
            "---",
            "",
            "## 3. Diagnostico Etapa 3 vs Etapa 4 e Independencias da Referencia (Condicionantes I, II e IV)",
            "",
            f"- **Auditoria AST da referencia independente (`etapa4_referencia_independente.py`):** `independencia_comprovada={ast4['independencia_comprovada']}` (`0` importacoes internas). Em atendimento a Condicionante I, registra-se que a auditoria AST comprova **independencia de implementacao** (zero compartilhamento de codigo ou caches com o motor principal), enquanto a **independencia metodologica** decorre da implementacao autonoma a partir das formulas matematicas oficiais da CAIXA (hipergeometrica bivariada 4-regioes, MST de Kruskal para Hunter-Worsley, Dawson-Sankoff e os 4 componentes combinatorio-estruturais), validada previamente contra enumeracao integral dos 3.268.760 sorteios na Etapa 2.",
            f"- **Invariancia do avaliador Etapa 3 vs Etapa 4:** divergencia maxima entre `avaliar_carteira_etapa2`, `MotorIncrementalOtimizadoEtapa4` e `avaliar_carteira_ref_etapa4` sobre todas as carteiras (inclusive as geradas pela Etapa 3) = `{max(tr['divergencia_max_etapa2_vs_motor_etapa4'], tr['divergencia_max_etapa2_vs_ref_independente']):.3e}` (`<= 1e-12`).",
            "",
            "| Cenario | Algoritmo | F(Etapa 3) | F(Etapa 4) | Delta F (E4 - E3) | Jaccard | Vit/Emp/Der (5 sementes) |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
    )
    for c in tr["casos"]:
        ms = c["sensibilidade_multi_semente"]
        linhas.append(
            f"| `{c['caso']}` | `{c['algoritmo']}` | {c['F_etapa3']:.8f} | {c['F_etapa4']:.8f} | "
            f"{c['delta_F_etapa4_menos_etapa3']:+.8f} | {c['similaridade_jaccard_carteiras']:.4f} | "
            f"{ms['vitorias_etapa4']}/{ms['empates']}/{ms['vitorias_etapa3']} |"
        )

    linhas.extend(
        [
            "",
            f"Conclusao da Condicionante II: {tr['conclusao_tecnica']}",
            "",
            "---",
            "",
            "## 4. Experimento Controlado de Despacho (Condicionante III e Exigencia 4)",
            "",
            "### Bloco A: Limiar micro `max(36, 3J)` (controle) vs `max(20, 2J)` (tratamento experimental)",
            "",
            "| Cenario | Grupo | Alg. Controle (3J) | Alg. Tratamento (2J) | F Controle | F Tratamento | Delta F | Tempo (3J vs 2J) |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
    )
    for r in bl_a["execucoes"]:
        linhas.append(
            f"| `{r['cenario']}` | `{r['grupo']}` | `{r['algoritmo_controle']}` | `{r['algoritmo_tratamento']}` | "
            f"{r['F_controle']:.8f} | {r['F_tratamento']:.8f} | {r['delta_F']:+.8f} | "
            f"{r['tempo_controle_s']:.4f}s vs {r['tempo_tratamento_s']:.4f}s |"
        )

    linhas.extend(
        [
            "",
            f"- **Na janela `[2J, 3J)`:** `{bl_a['na_janela_2J_3J']['vitorias_2J']}` vitorias de `2J`, `{bl_a['na_janela_2J_3J']['empates']}` empates, `{bl_a['na_janela_2J_3J']['derrotas_2J']}` derrotas; `delta_F_medio = {bl_a['na_janela_2J_3J']['delta_F_medio']:+.8f}`.",
            f"- **Invariancia fora da janela (`B >= 3J`):** `{bl_a['invariancia_fora_da_janela_3J']}`.",
            f"- **Decisao objetiva do Bloco A:** `{bl_a['decisao_empirica_micro']}`.",
            "",
            "### Bloco B: Inicializacao `padrao` (controle) vs `mista_equilibrada` (tratamento) em carteiras heterogeneas",
            "",
            "| Cenario | Grupo | F Padrao | F Mista Equilibrada | Delta F | Tempo (Padrao vs Mista) |",
            "| :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
    )
    for r in bl_b["execucoes"]:
        linhas.append(
            f"| `{r['cenario']}` | `{r['grupo']}` | {r['F_controle']:.8f} | {r['F_tratamento']:.8f} | "
            f"{r['delta_F']:+.8f} | {r['tempo_controle_s']:.4f}s vs {r['tempo_tratamento_s']:.4f}s |"
        )

    linhas.extend(
        [
            "",
            f"- **Resumo Bloco B:** `{bl_b['vitorias_tratamento']}` vitorias de `mista_equilibrada`, `{bl_b['empates']}` empates, `{bl_b['derrotas_tratamento']}` derrotas; `delta_F_medio = {bl_b['delta_F_medio']:+.8f}`.",
            f"- **Decisao objetiva do Bloco B:** `{bl_b['decisao_empirica_mista']}`.",
            f"- **Politica recomendada:** `{exp['recomendacao_padrao_producao']}`.",
            "",
            "---",
            "",
            "## 5. Validacao Ponta a Ponta, Fail-Closed e Limitacoes",
            "",
            "| Cenario E2E (`/api/v1/lotofacil-modo4/gerar`) | Algoritmo | Qtd Jogos | F(API) | Div vs Ref | 6 Grandezas | Status |",
            "| :--- | :--- | :--- | :--- | :--- | :--- | :--- |",
        ]
    )
    for e in e2e["casos_e2e"]:
        linhas.append(
            f"| `{e['id']}` | `{e.get('algoritmo')}` | {e.get('quantidade_jogos')} | "
            f"{e.get('F_api', 0.0):.8f} | {e.get('divergencia_F', 0.0):.2e} | "
            f"`{e.get('seis_grandezas_distintas_presentes')}` | `{'OK' if e.get('ok') else 'FALHA'}` |"
        )

    linhas.extend(
        [
            "",
            f"- **Testes negativos HTTP 422 (`historico`, conflitos, orcamento baixo, ambiguidade):** `{e2e['negativos_422_ok']}` (todos com `0` jogos).",
            f"- **Testes fail-closed cliente (offline, timeout, 500, 503, JSON corrompido):** `{e2e['fail_closed_cliente_ok']}` (todos com `sucesso=False`, `jogos=[]`, `fallback_executado=False`).",
            f"- **Adulteracao isolada de artefato Lotofacil e selo Lotomania (diretorio temporario):** `{e2e['adulteracao_fail_closed_ok']}` (HTTP `503`, `0` jogos).",
            "",
            "**Limitacoes explicitas desta etapa:**",
            "1. A integracao desta etapa opera exclusivamente em instancia de homologacao isolada; `api.py` de producao e a interface Web/Mobile permanecem intocados ate autorizacao expressa.",
            "2. A otimizacao heuristica (gulosa, busca local, multiplos reinicios e estrategia combinada) nao fornece prova de otimalidade global fora de `busca_exata_pequena`.",
            "3. Os ganhos ou empates observados no experimento de despacho limitam-se as dimensoes, orcamentos e sementes avaliados, nao autorizando generalizacoes irrestritas nem alegacoes de aumento da probabilidade individual por aposta.",
            "",
        ]
    )
    return _sanitizar_sem_travessao("\n".join(linhas))


def gerar_pacote_etapa5() -> Dict[str, Any]:
    out_dir = os.path.join(BASE_DIR_PADRAO, "auditoria", "lotofacil_modo4")
    os.makedirs(out_dir, exist_ok=True)

    # 1. Preservacao pre-execucao e baseline de producao
    pres_pre = garantir_integridade_etapa5_ou_falhar(
        diretorio_base=BASE_DIR_PADRAO,
        verificar_lotomania_selo=True,
        exigir_manifesto_etapa5=False,
        verificar_manifesto_se_presente=False,
    )
    prod_pre = _hashes_producao(BASE_DIR_PADRAO)

    # 2. Auditoria AST da referencia independente
    caminho_ref4 = os.path.join(BASE_DIR_PADRAO, "lotofacil_modo4", "etapa4_referencia_independente.py")
    ast4 = auditar_independencia_ast_etapa4(caminho_ref4)
    if not ast4["independencia_comprovada"]:
        raise RuntimeError(f"Referencia Etapa 4 falhou na auditoria AST: {ast4['violacoes']}")

    # 3. Manifesto criptografico SHA-256 Etapa 5
    manifesto = gerar_manifesto_etapa5(
        BASE_DIR_PADRAO,
        modulos_etapa5_extras=("testes/test_lotofacil_modo4_etapa5.py",),
    )

    # 4. Comparativo 3 vias ao vivo
    comp3 = _comparar_3_vias_ao_vivo()
    if not comp3["concluido_sem_regressao"]:
        raise RuntimeError(f"Falha no comparativo 3 vias ao vivo: {comp3}")

    # 5. Validacao E2E + Fail-Closed
    e2e = _validar_e2e_e_fail_closed()
    if not (
        e2e["todos_e2e_ok"]
        and e2e["negativos_422_ok"]
        and e2e["fail_closed_cliente_ok"]
        and e2e["adulteracao_fail_closed_ok"]
    ):
        raise RuntimeError(f"Falha na validacao E2E/fail-closed: {e2e}")

    # 6. Diagnostico Etapa 3 vs Etapa 4 (Condicionante II)
    diag34 = diagnosticar_trajetorias_etapa3_vs_etapa4()
    if not diag34["avaliador_exato_invariante"]:
        raise RuntimeError(f"Falha na invariancia do avaliador Etapa 3 vs 4: {diag34}")

    # 7. Experimento controlado de despacho (Condicionante III e Exigencia 4)
    exp_despacho = executar_experimento_controlado_despacho()

    # 8. Preservacao pos-execucao (congelados + producao intactos)
    pres_pos = garantir_integridade_etapa5_ou_falhar(
        diretorio_base=BASE_DIR_PADRAO,
        verificar_lotomania_selo=True,
        exigir_manifesto_etapa5=True,
    )
    prod_pos = _hashes_producao(BASE_DIR_PADRAO)
    producao_inalterada = prod_pre == prod_pos
    if not producao_inalterada:
        raise RuntimeError(f"Alteracao inesperada em arquivos de producao: {prod_pre} vs {prod_pos}")

    evidencias: Dict[str, Any] = {
        "sistema": "LOTOFACIL_MODO4",
        "etapa": "ETAPA_05_INTEGRACAO_E_VALIDACAO_E2E",
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "versao_arquitetura_etapa4": VERSAO_ARQUITETURA_ETAPA4,
        "versao_modulo_etapa5": VERSAO_MODULO_ETAPA5,
        "historico_geracao_etapa4": HISTORICO_GERACAO_ETAPA4,
        "feature_flag_padrao": False,
        "producao_inalterada": producao_inalterada,
        "hashes_producao_preservados": prod_pos,
        "preservacao_pre_execucao": pres_pre,
        "preservacao_pos_execucao": pres_pos,
        "manifesto_etapa5_resumo": {
            "arquivo": "auditoria/lotofacil_modo4/manifesto_etapa5.json",
            "modulos_etapa5_protegidos": list(manifesto["hashes_modulos_etapa5"].keys()),
        },
        "auditoria_ast_referencia_etapa4": {
            **ast4,
            "distincao_epistemologica": {
                "independencia_implementacao_demonstrada": True,
                "independencia_metodologica_origem": (
                    "Derivacao autonoma das formulas oficiais CAIXA (hipergeometrica 4-regioes, "
                    "MST Kruskal Hunter-Worsley, Dawson-Sankoff) validada contra enumeracao exata "
                    "dos 3.268.760 sorteios na Etapa 2."
                ),
            },
        },
        "comparativo_3_vias": comp3,
        "validacao_e2e_e_fail_closed": e2e,
        "diagnostico_etapa3_vs_etapa4": diag34,
        "experimento_controlado_despacho": exp_despacho,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
    }

    caminho_json = os.path.join(out_dir, "etapa_05_evidencias.json")
    caminho_md = os.path.join(out_dir, "ETAPA_05_INTEGRACAO_API.md")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(evidencias, f, indent=2, ensure_ascii=False)
    with open(caminho_md, "w", encoding="utf-8") as f:
        f.write(_renderizar_markdown_etapa5(evidencias))

    return evidencias


if __name__ == "__main__":
    resultado = gerar_pacote_etapa5()
    print(
        json.dumps(
            {
                "status": "ETAPA_5_OK",
                "producao_inalterada": resultado["producao_inalterada"],
                "comparativo_3_vias_ok": resultado["comparativo_3_vias"]["concluido_sem_regressao"],
                "maior_divergencia_e2e": resultado["validacao_e2e_e_fail_closed"]["maior_divergencia_e2e_vs_ref"],
                "recomendacao_despacho": resultado["experimento_controlado_despacho"]["recomendacao_padrao_producao"],
            },
            indent=2,
            ensure_ascii=False,
        )
    )
