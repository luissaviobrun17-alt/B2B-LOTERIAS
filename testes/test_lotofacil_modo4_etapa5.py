# -*- coding: utf-8 -*-
"""
SUITE DE TESTES E2E DA ETAPA 5 - LOTOFACIL MODO 4
=================================================
Cobre integracao isolada em homologacao, comparativo 3 vias, alternancia de
feature flag OFF/ON/OFF, seguranca fail-closed (sem fallback silencioso),
adulteracao criptografica em diretorio isolado, auditoria AST e equivalencia
matematica (<= 1e-12) contra a referencia independente, diagnostico Etapa 3 vs
Etapa 4 e experimento controlado de despacho.
100% compativel com execucao sob `python` e `python -O` (sem `assert`).
"""

from __future__ import annotations

from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import time
import unittest
from typing import Any, Dict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import api as api_producao

from lotofacil_modo4.etapa1_regras_oficiais import CLAUSULA_MATEMATICA_OBRIGATORIA
from lotofacil_modo4.etapa2_funcao_objetivo import NOMES_COMPONENTES
from lotofacil_modo4.etapa4_arquitetura_adaptativa import (
    HISTORICO_GERACAO_ETAPA4,
    _resolver_especificacao_etapa4,
)
from lotofacil_modo4.etapa4_referencia_independente import (
    auditar_conformidade_etapa4_ref,
    auditar_independencia_ast_etapa4,
    avaliar_carteira_ref_etapa4,
)
from lotofacil_modo4.etapa5_api_homologacao import (
    ENV_FEATURE_FLAG_LOTOFACIL_MODO4,
    ConfigHomologacaoLotofacilModo4,
    ServidorHttpHomologacao,
    alternar_feature_flag_homologacao,
    carregar_config_homologacao_de_env,
    chamar_api_lotofacil_modo4_seguro,
    criar_app_homologacao,
)
from lotofacil_modo4.etapa5_experimento_despacho import (
    despachar_com_politica_experimental,
    executar_com_politica_etapa5,
    verificar_integridade_etapa5,
)


def _exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise AssertionError(mensagem)


_CHAVES_DIST_6 = {
    "1_probabilidade_individual",
    "2_probabilidade_pareada_detalhes",
    "3_esperanca_N_prem",
    "3_variancia_N_prem",
    "4_cota_inferior_dawson_sankoff",
    "4_cota_superior_hunter_worsley",
    "5_probabilidade_exata_uniao",
    "6_nota_escopo_S_prob",
}


class TestLotofacilModo4Etapa5(unittest.TestCase):
    def test_01_preservacao_congelados_ast_e_producao_intocada(self) -> None:
        integridade = verificar_integridade_etapa5(
            diretorio_base=BASE_DIR,
            verificar_lotomania_selo=True,
            exigir_manifesto_etapa5=False,
            verificar_manifesto_se_presente=False,
        )
        _exigir(integridade["integro"] is True, f"Falha de integridade base: {integridade}")
        _exigir(
            integridade["verificados_etapas_1_2_3"] == 20,
            f"Esperados 20 artefatos Etapas 1-3, obtidos {integridade['verificados_etapas_1_2_3']}",
        )
        _exigir(
            integridade["verificados_etapa_4"] == 4,
            f"Esperados 4 artefatos Etapa 4, obtidos {integridade['verificados_etapa_4']}",
        )
        _exigir(
            integridade["selo_lotomania_valido"] is True,
            f"Selo Lotomania MODO 4 invalido: {integridade['erro_selo_lotomania']}",
        )

        caminho_ref4 = os.path.join(BASE_DIR, "lotofacil_modo4", "etapa4_referencia_independente.py")
        ast4 = auditar_independencia_ast_etapa4(caminho_ref4)
        _exigir(ast4["independencia_comprovada"] is True, f"Falha AST: {ast4['violacoes']}")

        _exigir(HISTORICO_GERACAO_ETAPA4 is None, "HISTORICO_GERACAO_ETAPA4 deve permanecer None.")

        rotas_prod = [getattr(r, "path", "") for r in api_producao.app.routes]
        _exigir(
            not any(p.startswith("/api/v1/lotofacil-modo4") for p in rotas_prod),
            f"api.py de producao nao pode receber rotas Lotofacil MODO 4 na Etapa 5: {rotas_prod}",
        )

    def test_02_feature_flag_padrao_desligada_e_rollback_runtime(self) -> None:
        cfg_padrao = ConfigHomologacaoLotofacilModo4()
        _exigir(cfg_padrao.lotofacil_modo4_ativo is False, "Flag padrao precisa iniciar False.")

        antigo = os.environ.pop(ENV_FEATURE_FLAG_LOTOFACIL_MODO4, None)
        try:
            _exigir(
                carregar_config_homologacao_de_env().lotofacil_modo4_ativo is False,
                "Sem variavel de ambiente, flag precisa permanecer False.",
            )
            os.environ[ENV_FEATURE_FLAG_LOTOFACIL_MODO4] = "true"
            _exigir(
                carregar_config_homologacao_de_env().lotofacil_modo4_ativo is True,
                "Env 'true' deve ativar explicitamente a flag.",
            )
            os.environ[ENV_FEATURE_FLAG_LOTOFACIL_MODO4] = "invalido"
            levantou = False
            try:
                carregar_config_homologacao_de_env()
            except ValueError:
                levantou = True
            _exigir(levantou, "Valor invalido na env da feature flag deve falhar fechado.")
        finally:
            if antigo is None:
                os.environ.pop(ENV_FEATURE_FLAG_LOTOFACIL_MODO4, None)
            else:
                os.environ[ENV_FEATURE_FLAG_LOTOFACIL_MODO4] = antigo

        app_h = criar_app_homologacao(ConfigHomologacaoLotofacilModo4(lotofacil_modo4_ativo=False))
        with ServidorHttpHomologacao(app_h) as srv:
            r_off = chamar_api_lotofacil_modo4_seguro(
                srv.base_url, {"quantidade_jogos": 4, "semente": 42, "max_avaliacoes": 120}
            )
            _exigir(r_off["status_http"] == 503 and len(r_off["jogos"]) == 0, f"Flag OFF falhou: {r_off}")
            _exigir(r_off["fallback_executado"] is False, "Rollback nao pode executar fallback.")

            alternar_feature_flag_homologacao(app_h, True)
            r_on = chamar_api_lotofacil_modo4_seguro(
                srv.base_url, {"quantidade_jogos": 4, "semente": 42, "max_avaliacoes": 120}
            )
            _exigir(r_on["sucesso"] is True and len(r_on["jogos"]) == 4, f"Flag ON falhou: {r_on}")

            alternar_feature_flag_homologacao(app_h, False)
            r_back = chamar_api_lotofacil_modo4_seguro(
                srv.base_url, {"quantidade_jogos": 4, "semente": 42, "max_avaliacoes": 120}
            )
            _exigir(
                r_back["status_http"] == 503 and len(r_back["jogos"]) == 0,
                f"Rollback imediato falhou: {r_back}",
            )

    def test_03_comparativo_3_vias_nao_interferencia_real_http(self) -> None:
        app_off = criar_app_homologacao(ConfigHomologacaoLotofacilModo4(lotofacil_modo4_ativo=False))
        app_on = criar_app_homologacao(ConfigHomologacaoLotofacilModo4(lotofacil_modo4_ativo=True))

        with (
            ServidorHttpHomologacao(api_producao.app) as srv_a,
            ServidorHttpHomologacao(app_off) as srv_b,
            ServidorHttpHomologacao(app_on) as srv_c,
        ):
            ha = chamar_api_lotofacil_modo4_seguro(srv_a.base_url, endpoint="/health", metodo="GET")
            hb = chamar_api_lotofacil_modo4_seguro(srv_b.base_url, endpoint="/health", metodo="GET")
            hc = chamar_api_lotofacil_modo4_seguro(srv_c.base_url, endpoint="/health", metodo="GET")

            da = ha["dados_brutos"]
            db = hb["dados_brutos"]
            dc = hc["dados_brutos"]
            for chave, val in da.items():
                _exigir(db.get(chave) == val, f"Divergencia em /health flag OFF chave={chave}")
                _exigir(dc.get(chave) == val, f"Divergencia em /health flag ON chave={chave}")

            _exigir("lotofacil_modo4" not in da, "Producao /health nao deve ser alterada.")
            _exigir(db["lotofacil_modo4"]["disponivel"] is False, "Flag OFF deve informar disponivel=False.")
            _exigir(dc["lotofacil_modo4"]["disponivel"] is True, "Flag ON deve informar disponivel=True.")

            pl_lm4 = {"quantidade_jogos": 5, "permitir_espelhos": True, "seed": 42, "trace": False}
            la = chamar_api_lotofacil_modo4_seguro(srv_a.base_url, pl_lm4, endpoint="/api/v1/lotomania-modo4/gerar")
            lb = chamar_api_lotofacil_modo4_seguro(srv_b.base_url, pl_lm4, endpoint="/api/v1/lotomania-modo4/gerar")
            lc = chamar_api_lotofacil_modo4_seguro(srv_c.base_url, pl_lm4, endpoint="/api/v1/lotomania-modo4/gerar")
            _exigir(
                la["dados_brutos"]["jogos"] == lb["dados_brutos"]["jogos"] == lc["dados_brutos"]["jogos"],
                "Lotomania MODO 4 precisa permanecer identica nas 3 vias.",
            )

            for ep, pl in (
                ("/api/v1/motor-lotofacil", {"quantidade_jogos": 3, "estrategia": "equilibrada", "sniper": True}),
                ("/api/v1/motor-lotomania", {"quantidade_jogos": 3, "estrategia": "equilibrada"}),
            ):
                ra = chamar_api_lotofacil_modo4_seguro(srv_a.base_url, pl, endpoint=ep)
                rb = chamar_api_lotofacil_modo4_seguro(srv_b.base_url, pl, endpoint=ep)
                rc = chamar_api_lotofacil_modo4_seguro(srv_c.base_url, pl, endpoint=ep)
                _exigir(
                    ra["status_http"] == rb["status_http"] == rc["status_http"] == 200,
                    f"Rota legada {ep} falhou em uma das 3 vias.",
                )

    def test_04_e2e_equivalencia_matematica_e_endpoints_avaliacao(self) -> None:
        app_on = criar_app_homologacao(ConfigHomologacaoLotofacilModo4(lotofacil_modo4_ativo=True))
        casos = [
            {
                "pool": list(range(1, 17)),
                "bloqueadas": [21, 22, 23, 24, 25],
                "quantidade_jogos": 4,
                "max_avaliacoes": 2000,
                "max_iteracoes": 2000,
            },
            {
                "pool": list(range(1, 26)),
                "orcamento_brl": "56.00",
                "tipo_concurso": "lotofacil_independencia",
                "max_avaliacoes": 220,
            },
            {
                "pool": list(range(1, 22)),
                "fixas": [1, 2],
                "bloqueadas": [22, 23, 24, 25],
                "tamanhos_jogos": [16, 16, 15, 15, 15, 15],
                "tipo_concurso": "concurso_final_zero",
                "max_avaliacoes": 200,
            },
        ]

        with ServidorHttpHomologacao(app_on) as srv:
            st = chamar_api_lotofacil_modo4_seguro(
                srv.base_url, endpoint="/api/v1/lotofacil-modo4/status", metodo="GET"
            )
            _exigir(st["status_http"] == 200 and st["dados_brutos"]["disponivel"] is True, f"Status erro: {st}")

            for pl in casos:
                resp = chamar_api_lotofacil_modo4_seguro(srv.base_url, pl)
                _exigir(resp["sucesso"] is True and resp["status_http"] == 200, f"E2E falhou: {resp}")
                d = resp["dados_brutos"]
                _exigir(d["historico_utilizado"] is None, "Historico deve ser None.")
                _exigir(d["fallback_executado"] is False, "Fallback deve ser False.")
                _exigir(
                    d["clausula_obrigatoria"] == CLAUSULA_MATEMATICA_OBRIGATORIA,
                    "Clausula obrigatoria divergente.",
                )
                _exigir(
                    _CHAVES_DIST_6.issubset(d["distincao_seis_grandezas_probabilisticas"].keys()),
                    "Chaves das 6 grandezas probabilisticas incompletas.",
                )

                esp = d["especificacao"]
                av_ref = avaliar_carteira_ref_etapa4(
                    d["jogos"],
                    pool=esp["pool"],
                    fixas=esp["fixas"],
                    bloqueadas=esp["bloqueadas"],
                    modo_fixas=esp["modo_fixas"],
                    pesos=esp["pesos"],
                )
                conf = auditar_conformidade_etapa4_ref(
                    d["jogos"],
                    pool=esp["pool"],
                    fixas=esp["fixas"],
                    bloqueadas=esp["bloqueadas"],
                    modo_fixas=esp["modo_fixas"],
                    tamanhos_esperados=esp["tamanhos_jogos"],
                )
                _exigir(conf["conforme"] is True, f"Violacoes na carteira: {conf['violacoes']}")
                _exigir(
                    abs(float(d["funcao_objetivo_F"]) - float(av_ref["funcao_objetivo_F"])) <= 1e-12,
                    "Divergencia > 1e-12 em F.",
                )
                for k in NOMES_COMPONENTES:
                    _exigir(
                        abs(float(d["componentes"][k]) - float(av_ref["componentes"][k])) <= 1e-12,
                        f"Divergencia > 1e-12 no componente {k}.",
                    )

            av_resp = chamar_api_lotofacil_modo4_seguro(
                srv.base_url,
                {
                    "carteira": [list(range(1, 16)), [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 16]],
                    "pool": list(range(1, 17)),
                    "bloqueadas": [21, 22, 23, 24, 25],
                },
                endpoint="/api/v1/lotofacil-modo4/avaliar",
            )
            _exigir(
                av_resp["status_http"] == 200
                and av_resp["dados_brutos"]["auditoria_referencia_independente"]["divergencia_F"] <= 1e-12,
                f"Endpoint /avaliar falhou: {av_resp}",
            )

    def test_05_fail_closed_entradas_invalidas_rede_e_adulteracao(self) -> None:
        app_on = criar_app_homologacao(ConfigHomologacaoLotofacilModo4(lotofacil_modo4_ativo=True))
        with ServidorHttpHomologacao(app_on) as srv:
            for bad_payload in (
                {"quantidade_jogos": 3, "historico": [[1, 2, 3]]},
                {"quantidade_jogos": 3, "usar_historico": True},
                {"quantidade_jogos": True},
                {"orcamento_brl": True},
                {"quantidade_jogos": 2, "fixas": [1, 2], "bloqueadas": [2, 25]},
                {"orcamento_brl": "2.00"},
                {"quantidade_jogos": 2, "tamanhos_jogos": [15, 15]},
            ):
                rb = chamar_api_lotofacil_modo4_seguro(srv.base_url, bad_payload)
                _exigir(
                    rb["sucesso"] is False and rb["status_http"] == 422 and len(rb["jogos"]) == 0,
                    f"Entrada invalida nao retornou 422 com 0 jogos: {bad_payload} -> {rb}",
                )
                _exigir(rb["fallback_executado"] is False, "Entrada invalida nao pode usar fallback.")

        # Adulteracao em diretorio temporario isolado (Lotofacil + Lotomania + manifesto Etapa 5)
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
                "lotofacil_modo4/etapa5_experimento_despacho.py",
                "lotofacil_modo4/etapa5_api_homologacao.py",
                "lotofacil_modo4/gerar_evidencias_etapa5.py",
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
                src = os.path.join(BASE_DIR, rel.replace("/", os.sep))
                dst = os.path.join(tmpdir, rel.replace("/", os.sep))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

            alvo = os.path.join(tmpdir, "lotofacil_modo4", "etapa1_regras_oficiais.py")
            with open(alvo, "ab") as f:
                f.write(b"\n# byte adulterado\n")

            app_tampered = criar_app_homologacao(
                ConfigHomologacaoLotofacilModo4(lotofacil_modo4_ativo=True, diretorio_base=tmpdir)
            )
            with ServidorHttpHomologacao(app_tampered) as srv_t:
                rt = chamar_api_lotofacil_modo4_seguro(srv_t.base_url, {"quantidade_jogos": 2})
                _exigir(
                    rt["sucesso"] is False and rt["status_http"] == 503 and len(rt["jogos"]) == 0,
                    f"Adulteracao nao bloqueou fail-closed: {rt}",
                )

            # Manifesto Etapa 5 ausente quando exigido tambem deve bloquear com 503
            app_sem_man = criar_app_homologacao(
                ConfigHomologacaoLotofacilModo4(
                    lotofacil_modo4_ativo=True,
                    diretorio_base=tmpdir,
                    verificar_lotomania_selo=True,
                    exigir_manifesto_etapa5=True,
                )
            )
            with ServidorHttpHomologacao(app_sem_man) as srv_m:
                rm = chamar_api_lotofacil_modo4_seguro(srv_m.base_url, {"quantidade_jogos": 2})
                _exigir(
                    rm["status_http"] == 503 and len(rm["jogos"]) == 0,
                    f"Manifesto ausente nao bloqueou fail-closed: {rm}",
                )

        # Cliente contra porta fechada, timeout e HTTP 500
        s_dead = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s_dead.bind(("127.0.0.1", 0))
        dead_port = s_dead.getsockname()[1]
        s_dead.close()
        r_dead = chamar_api_lotofacil_modo4_seguro(f"http://127.0.0.1:{dead_port}", {"quantidade_jogos": 2}, timeout_s=1.0)
        _exigir(r_dead["sucesso"] is False and len(r_dead["jogos"]) == 0 and r_dead["fallback_executado"] is False, "Porta offline deve retornar 0 jogos.")

        class _ErrHandler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                return

            def do_POST(self) -> None:
                tam = int(self.headers.get("Content-Length", "0") or 0)
                if tam > 0:
                    _ = self.rfile.read(tam)
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"erro")

        srv_err = ThreadingHTTPServer(("127.0.0.1", 0), _ErrHandler)
        threading.Thread(target=srv_err.serve_forever, daemon=True).start()
        try:
            r500 = chamar_api_lotofacil_modo4_seguro(
                f"http://127.0.0.1:{srv_err.server_port}", {"quantidade_jogos": 2}
            )
            _exigir(r500["sucesso"] is False and r500["status_http"] == 500 and len(r500["jogos"]) == 0, "HTTP 500 deve falhar fechado.")
        finally:
            srv_err.shutdown()
            srv_err.server_close()

    def test_06_experimento_controlado_despacho_e_artefatos_etapa5(self) -> None:
        spec_micro = _resolver_especificacao_etapa4(
            pool=list(range(1, 26)),
            fixas=(),
            bloqueadas=(),
            modo_fixas="todos_os_jogos",
            quantidade_jogos=12,
            tamanho_aposta=15,
            tamanhos_jogos=None,
            orcamento_brl=None,
            pesos=None,
            perfil_pesos=None,
        )
        d3 = despachar_com_politica_experimental(spec_micro, politica_micro="conservadora_3J", max_avaliacoes=30)
        d2 = despachar_com_politica_experimental(spec_micro, politica_micro="experimental_2J", max_avaliacoes=30)
        _exigir(d3["algoritmo_escolhido"] == "algoritmo_guloso", f"Esperado guloso em 3J B=30, obtido {d3['algoritmo_escolhido']}")
        _exigir(d2["algoritmo_escolhido"] == "busca_local_trocas", f"Esperado busca_local_trocas em 2J B=30, obtido {d2['algoritmo_escolhido']}")

        res_mista = executar_com_politica_etapa5(
            pool=list(range(1, 22)),
            fixas=[1, 2],
            bloqueadas=[22, 23, 24, 25],
            tamanhos_jogos=[16, 16, 15, 15, 15, 15],
            max_avaliacoes=160,
            semente=42,
            politica_micro="conservadora_3J",
            inicializacao_mista="mista_equilibrada",
            validar_referencia_independente=True,
        )
        _exigir(
            res_mista["telemetria"]["avaliacoes_efetivas"] <= 160
            and res_mista["auditoria_referencia_independente"]["divergencia_F"] <= 1e-12,
            "Inicializacao mista experimental deve respeitar orcamento e referencia <= 1e-12.",
        )

        # Verifica artefatos gerados da Etapa 5
        arq_ev = os.path.join(BASE_DIR, "auditoria", "lotofacil_modo4", "etapa_05_evidencias.json")
        arq_md = os.path.join(BASE_DIR, "auditoria", "lotofacil_modo4", "ETAPA_05_INTEGRACAO_API.md")
        arq_man = os.path.join(BASE_DIR, "auditoria", "lotofacil_modo4", "manifesto_etapa5.json")
        _exigir(os.path.isfile(arq_ev) and os.path.isfile(arq_md) and os.path.isfile(arq_man), "Artefatos Etapa 5 ausentes.")

        with open(arq_ev, "r", encoding="utf-8") as f:
            ev = json.load(f)
        _exigir(ev["producao_inalterada"] is True, "Producao precisa estar marcada inalterada nas evidencias.")
        _exigir(ev["comparativo_3_vias"]["concluido_sem_regressao"] is True, "Comparativo 3 vias nao aprovado.")
        _exigir(ev["validacao_e2e_e_fail_closed"]["maior_divergencia_e2e_vs_ref"] <= 1e-12, "Divergencia E2E excede 1e-12.")
        _exigir(ev["diagnostico_etapa3_vs_etapa4"]["avaliador_exato_invariante"] is True, "Invariancia E3 vs E4 falhou.")
        for caso_diag in ev["diagnostico_etapa3_vs_etapa4"]["casos"]:
            ms = caso_diag["sensibilidade_multi_semente"]
            _exigir(
                ms["vitorias_etapa4"] >= 0
                and ms["empates"] >= 0
                and ms["vitorias_etapa3"] >= 0
                and ms["vitorias_etapa4"] + ms["empates"] + ms["vitorias_etapa3"] == len(ms["sementes"]),
                f"Contagem multi-semente inconsistente em {caso_diag['caso']}: {ms}",
            )

        int_man = verificar_integridade_etapa5(
            diretorio_base=BASE_DIR,
            verificar_lotomania_selo=True,
            exigir_manifesto_etapa5=True,
            verificar_manifesto_se_presente=True,
        )
        _exigir(int_man["integro"] is True, f"Manifesto Etapa 5 divergente: {int_man}")

        with open(arq_md, "r", encoding="utf-8") as f:
            md_txt = f.read()
        _exigir("\u2014" not in md_txt and "\u2013" not in md_txt, "Relatorio Markdown nao pode conter travessoes.")
        _exigir(CLAUSULA_MATEMATICA_OBRIGATORIA in md_txt, "Relatorio precisa incluir a clausula cientifica obrigatoria.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
