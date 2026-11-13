# -*- coding: utf-8 -*-
"""
SUITE DE TESTES DE PROMOCAO CONTROLADA - LOTOFACIL MODO 4
==========================================================
Valida integralmente a matriz obrigatoria do Parecer Final (itens V.1 a V.8):
  1. Integracao em `api.py` com feature flag desligada por padrao (`False`);
  2. Paridade estrutural e fail-closed das interfaces Web e Mobile (zero fallback);
  3. Teste de concorrencia multi-requisicao (estados OFF e ON);
  4. Falhas negativas, schema estrito, rejeicao de `mista_equilibrada`, rollback e
     adulteracao SHA-256 em diretorio isolado;
  5. Verificacao criptografica SHA-256 pos-implantacao + `manifesto_promocao_controlada.json`;
  6. Nao interferencia com Lotomania MODO 4 v1.2 (selo Ed25519) e motores legados;
  7. Evidencia funcional com feature flag OFF (padrao de producao);
  8. Evidencia funcional com feature flag ON controlada e `experimental_2J` opcional.
Compativel com `python` e `python -O` (sem instrucoes `assert`).
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import os
import shutil
import socket
import sys
import tempfile
import threading
import unittest
from typing import Any, Dict

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import api as api_producao

from lotofacil_modo4.etapa1_regras_oficiais import CLAUSULA_MATEMATICA_OBRIGATORIA
from lotofacil_modo4.etapa2_funcao_objetivo import NOMES_COMPONENTES
from lotofacil_modo4.etapa4_arquitetura_adaptativa import HISTORICO_GERACAO_ETAPA4
from lotofacil_modo4.etapa4_referencia_independente import (
    auditar_conformidade_etapa4_ref,
    auditar_independencia_ast_etapa4,
    avaliar_carteira_ref_etapa4,
)
from lotofacil_modo4.etapa5_api_homologacao import (
    ServidorHttpHomologacao,
    chamar_api_lotofacil_modo4_seguro,
)
from lotofacil_modo4.promocao_producao import (
    ENV_FEATURE_FLAG_LOTOFACIL_MODO4,
    ENV_PERMITIR_EXPERIMENTAL_2J,
    ENV_POLITICA_MICRO_PADRAO,
    INICIALIZACAO_MISTA_FIXA,
    POLITICA_MICRO_PRODUCAO_PADRAO,
    ConfigProducaoLotofacilModo4,
    carregar_config_producao_de_env,
    definir_feature_flag_lotofacil_modo4,
    garantir_integridade_promocao_ou_falhar,
    obter_status_health_lotofacil_modo4,
    verificar_integridade_promocao,
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

_HASH_MOTOR_LOTOFACIL_LEGADO = "7dcaf017f8a4845fe42f5a58cb978c81e95e8f55b96ef558b9a0ec551ba077c3"


class TestLotofacilModo4PromocaoControlada(unittest.TestCase):
    def tearDown(self) -> None:
        # Garante retorno ao estado seguro padrao de producao apos cada teste
        definir_feature_flag_lotofacil_modo4(
            api_producao.app,
            ativo=False,
            permitir_experimental_2j=False,
            motivo="teardown_padrao_seguro",
        )

    def test_01_configuracao_padrao_desligada_e_env(self) -> None:
        cfg_padrao = ConfigProducaoLotofacilModo4()
        _exigir(cfg_padrao.lotofacil_modo4_ativo is False, "Flag padrao deve ser False.")
        _exigir(
            cfg_padrao.politica_micro_padrao == POLITICA_MICRO_PRODUCAO_PADRAO,
            "Politica padrao deve ser conservadora_3J.",
        )
        _exigir(
            cfg_padrao.permitir_experimental_2j is False,
            "experimental_2J deve vir desabilitada por padrao.",
        )
        _exigir(
            cfg_padrao.inicializacao_mista == INICIALIZACAO_MISTA_FIXA,
            "Inicializacao mista deve ser 'padrao'.",
        )

        levantou_mista = False
        try:
            ConfigProducaoLotofacilModo4(inicializacao_mista="mista_equilibrada")
        except ValueError:
            levantou_mista = True
        _exigir(levantou_mista, "mista_equilibrada deve ser bloqueada na configuracao.")

        levantou_2j = False
        try:
            ConfigProducaoLotofacilModo4(politica_micro_padrao="experimental_2J", permitir_experimental_2j=False)
        except ValueError:
            levantou_2j = True
        _exigir(levantou_2j, "experimental_2J como padrao sem permissao deve falhar.")

        bkp = {
            k: os.environ.pop(k, None)
            for k in (
                ENV_FEATURE_FLAG_LOTOFACIL_MODO4,
                ENV_PERMITIR_EXPERIMENTAL_2J,
                ENV_POLITICA_MICRO_PADRAO,
            )
        }
        try:
            cfg_env_vazia = carregar_config_producao_de_env()
            _exigir(cfg_env_vazia.lotofacil_modo4_ativo is False, "Sem env, flag deve permanecer False.")
            _exigir(cfg_env_vazia.permitir_experimental_2j is False, "Sem env, experimental_2J permanece False.")

            os.environ[ENV_FEATURE_FLAG_LOTOFACIL_MODO4] = "true"
            cfg_env_on = carregar_config_producao_de_env()
            _exigir(cfg_env_on.lotofacil_modo4_ativo is True, "Env 'true' deve habilitar flag.")
            _exigir(cfg_env_on.politica_micro_padrao == "conservadora_3J", "Politica continua conservadora_3J.")

            os.environ[ENV_FEATURE_FLAG_LOTOFACIL_MODO4] = "talvez"
            falhou_bool = False
            try:
                carregar_config_producao_de_env()
            except ValueError:
                falhou_bool = True
            _exigir(falhou_bool, "Valor booleano invalido em env deve falhar fechado.")
        finally:
            for k, v in bkp.items():
                if v is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = v

        _exigir(HISTORICO_GERACAO_ETAPA4 is None, "HISTORICO_GERACAO_ETAPA4 deve ser None.")

    def test_02_integridade_pos_implantacao_e_adulteracao_fail_closed(self) -> None:
        ast_res = auditar_independencia_ast_etapa4(
            os.path.join(BASE_DIR, "lotofacil_modo4", "etapa4_referencia_independente.py")
        )
        _exigir(ast_res["independencia_comprovada"] is True, f"AST falhou: {ast_res['violacoes']}")

        int_res = garantir_integridade_promocao_ou_falhar(
            diretorio_base=BASE_DIR,
            verificar_lotomania_selo=True,
            exigir_manifesto_etapa5=True,
            exigir_manifesto_promocao=True,
        )
        _exigir(int_res["integro"] is True, f"Integridade pos-implantacao falhou: {int_res['divergencias']}")
        _exigir(int_res["verificados_etapas_1_2_3"] == 20, "Esperados 20 artefatos congelados Etapas 1-3.")
        _exigir(int_res["verificados_etapa_4"] == 4, "Esperados 4 artefatos congelados Etapa 4.")
        _exigir(int_res["selo_lotomania_valido"] is True, "Selo Ed25519 Lotomania deve permanecer valido.")
        _exigir(int_res["manifesto_promocao_presente"] is True, "manifesto_promocao_controlada.json ausente.")
        _exigir(
            int_res["hashes_atuais_producao"].get("motor_lotofacil.py") == _HASH_MOTOR_LOTOFACIL_LEGADO,
            "motor_lotofacil.py legado nao pode ter sido alterado.",
        )

        # Adulteracao em diretorio isolado deve falhar fechado
        with tempfile.TemporaryDirectory() as tmpdir:
            caminho_man = os.path.join(BASE_DIR, "auditoria", "lotofacil_modo4", "manifesto_promocao_controlada.json")
            with open(caminho_man, "r", encoding="utf-8") as f:
                man = json.load(f)

            for rel in (
                list(int_res["hashes_atuais_producao"].keys())
                + [
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
                    "auditoria/lotofacil_modo4/manifesto_etapa5.json",
                    "auditoria/lotofacil_modo4/manifesto_promocao_controlada.json",
                    "testes/test_lotofacil_modo4_etapa1.py",
                    "testes/test_lotofacil_modo4_etapa2.py",
                    "testes/test_lotofacil_modo4_etapa3.py",
                    "testes/test_lotofacil_modo4_etapa4.py",
                    "testes/test_lotofacil_modo4_etapa5.py",
                    "data/lotofacil.json",
                    "motor_lotomania_modo4.py",
                    "verificador_selo_modo4.py",
                    "chave_publica_modo4.pem",
                    "data/lotomania.json",
                    "manifesto_modo4.json",
                    "manifesto_modo4.sig",
                ]
            ):
                src = os.path.join(BASE_DIR, rel.replace("/", os.sep))
                dst = os.path.join(tmpdir, rel.replace("/", os.sep))
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)

            ok_tmp = verificar_integridade_promocao(
                diretorio_base=tmpdir,
                verificar_lotomania_selo=False,
                exigir_manifesto_etapa5=True,
                exigir_manifesto_promocao=True,
            )
            _exigir(ok_tmp["integro"] is True, f"Copia limpa no tmpdir falhou: {ok_tmp['divergencias']}")

            # Adultera promocao_producao.py no tmpdir
            alvo = os.path.join(tmpdir, "lotofacil_modo4", "promocao_producao.py")
            with open(alvo, "a", encoding="utf-8") as f:
                f.write("\n# adulteracao_teste\n")
            ad_tmp = verificar_integridade_promocao(
                diretorio_base=tmpdir,
                verificar_lotomania_selo=False,
                exigir_manifesto_etapa5=True,
                exigir_manifesto_promocao=True,
            )
            _exigir(ad_tmp["integro"] is False, "Adulteracao em modulo de promocao nao bloqueou.")
            _exigir(len(ad_tmp["divergencias"]) >= 1, "Esperada divergencia apos adulteracao.")

    def test_03_api_producao_flag_off_on_experimental_e_rollback(self) -> None:
        definir_feature_flag_lotofacil_modo4(
            api_producao.app,
            ativo=False,
            permitir_experimental_2j=False,
            motivo="teste_03_off",
        )
        with ServidorHttpHomologacao(api_producao.app) as srv:
            # 1) Padrao OFF
            rh = chamar_api_lotofacil_modo4_seguro(srv.base_url, endpoint="/health", metodo="GET")
            _exigir(rh["status_http"] == 200, "/health falhou.")
            l4 = rh["dados_brutos"]["lotofacil_modo4"]
            _exigir(l4["disponivel"] is False and l4["feature_flag_ativa"] is False, f"/health OFF inesperado: {l4}")
            _exigir(l4["politica_micro_padrao"] == "conservadora_3J", "Politica padrao errada.")
            _exigir(l4["experimental_2j_habilitada"] is False, "experimental_2J nao pode estar habilitada.")

            r_off = chamar_api_lotofacil_modo4_seguro(srv.base_url, {"quantidade_jogos": 8, "semente": 42})
            _exigir(
                r_off["status_http"] == 503 and r_off["jogos"] == [] and r_off["fallback_executado"] is False,
                f"Flag OFF deveria retornar 503 sem jogos: {r_off}",
            )

            # 2) Ativacao controlada ON (experimental_2J ainda desabilitada por padrao)
            definir_feature_flag_lotofacil_modo4(
                api_producao.app,
                ativo=True,
                permitir_experimental_2j=False,
                motivo="teste_03_on",
            )
            r_on = chamar_api_lotofacil_modo4_seguro(
                srv.base_url,
                {
                    "quantidade_jogos": 6,
                    "tamanho_aposta": 15,
                    "semente": 42,
                    "max_avaliacoes": 200,
                },
                timeout_s=20.0,
            )
            _exigir(r_on["sucesso"] is True and r_on["status_http"] == 200, f"Flag ON falhou: {r_on}")
            d = r_on["dados_brutos"]
            _exigir(d["historico_utilizado"] is None, "Historico deve ser None.")
            _exigir(d["fallback_executado"] is False, "Fallback deve ser False.")
            _exigir(d["clausula_obrigatoria"] == CLAUSULA_MATEMATICA_OBRIGATORIA, "Clausula diverge.")
            _exigir(
                d["promocao_controlada"]["politica_micro_utilizada"] == "conservadora_3J"
                and d["promocao_controlada"]["inicializacao_mista"] == "padrao",
                "Configuracao de geracao ON inesperada.",
            )
            _exigir(
                _CHAVES_DIST_6.issubset(d["distincao_seis_grandezas_probabilisticas"].keys()),
                "Chaves probabilisticas incompletas.",
            )

            # Validacao cruzada AST independente <= 1e-12
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
            _exigir(conf["conforme"] is True, f"Carteira nao conforme: {conf['violacoes']}")
            _exigir(abs(float(d["funcao_objetivo_F"]) - float(av_ref["funcao_objetivo_F"])) <= 1e-12, "Diff F > 1e-12.")
            for comp in NOMES_COMPONENTES:
                _exigir(
                    abs(float(d["componentes"][comp]) - float(av_ref["componentes"][comp])) <= 1e-12,
                    f"Diff componente {comp} > 1e-12.",
                )

            # Bloqueio padrao de experimental_2J + rejeicao de campos proibidos
            for payload_invalido in (
                {"quantidade_jogos": 8, "politica_micro": "experimental_2J"},
                {"quantidade_jogos": 4, "inicializacao_mista": "mista_equilibrada"},
                {"quantidade_jogos": 4, "historico": [[1, 2, 3]]},
                {"quantidade_jogos": True},
            ):
                rinv = chamar_api_lotofacil_modo4_seguro(srv.base_url, payload_invalido)
                _exigir(
                    rinv["status_http"] == 422 and len(rinv["jogos"]) == 0 and rinv["fallback_executado"] is False,
                    f"Entrada invalida deveria retornar 422 com 0 jogos: {payload_invalido} -> {rinv}",
                )

            # Habilitacao configuravel explicita experimental_2J
            definir_feature_flag_lotofacil_modo4(
                api_producao.app,
                ativo=True,
                permitir_experimental_2j=True,
                motivo="teste_03_exp2j",
            )
            r_def = chamar_api_lotofacil_modo4_seguro(
                srv.base_url, {"quantidade_jogos": 8, "semente": 42}, timeout_s=20.0
            )
            _exigir(
                r_def["sucesso"] is True
                and r_def["dados_brutos"]["promocao_controlada"]["politica_micro_utilizada"] == "conservadora_3J",
                "Sem parametro explicito, politica padrao continua conservadora_3J.",
            )
            r_exp = chamar_api_lotofacil_modo4_seguro(
                srv.base_url,
                {"quantidade_jogos": 8, "semente": 42, "politica_micro": "experimental_2J"},
                timeout_s=20.0,
            )
            _exigir(
                r_exp["sucesso"] is True
                and r_exp["dados_brutos"]["promocao_controlada"]["politica_micro_utilizada"] == "experimental_2J",
                f"Opt-in experimental_2J falhou: {r_exp}",
            )

            # Endpoint /avaliar
            r_av = chamar_api_lotofacil_modo4_seguro(
                srv.base_url,
                {"carteira": d["jogos"]},
                endpoint="/api/v1/lotofacil-modo4/avaliar",
            )
            _exigir(
                r_av["status_http"] == 200
                and r_av["dados_brutos"]["auditoria_referencia_independente"]["divergencia_F"] <= 1e-12,
                f"/avaliar falhou: {r_av}",
            )

            # 3) Rollback runtime imediato para OFF
            definir_feature_flag_lotofacil_modo4(
                api_producao.app,
                ativo=False,
                permitir_experimental_2j=False,
                motivo="teste_03_rollback",
            )
            r_rb = chamar_api_lotofacil_modo4_seguro(srv.base_url, {"quantidade_jogos": 4, "semente": 42})
            _exigir(
                r_rb["status_http"] == 503 and len(r_rb["jogos"]) == 0 and r_rb["fallback_executado"] is False,
                f"Rollback imediato falhou: {r_rb}",
            )

    def test_04_concorrencia_e_nao_interferencia_demais_modalidades(self) -> None:
        definir_feature_flag_lotofacil_modo4(api_producao.app, ativo=False, motivo="teste_04_off")
        with ServidorHttpHomologacao(api_producao.app) as srv:
            # Referencia nao interferencia OFF
            lm_off = chamar_api_lotofacil_modo4_seguro(
                srv.base_url,
                {"quantidade_jogos": 5, "permitir_espelhos": True, "seed": 42, "trace": False},
                endpoint="/api/v1/lotomania-modo4/gerar",
                timeout_s=15.0,
            )
            _exigir(lm_off["status_http"] == 200, "Lotomania MODO 4 falhou em OFF.")

            def _worker(i: int) -> bool:
                if i % 2 == 0:
                    r = chamar_api_lotofacil_modo4_seguro(
                        srv.base_url, {"quantidade_jogos": 4, "semente": 42}, timeout_s=20.0
                    )
                    return bool(r["status_http"] == 200 and len(r["jogos"]) == 4)
                r_lm = chamar_api_lotofacil_modo4_seguro(
                    srv.base_url,
                    {"quantidade_jogos": 5, "permitir_espelhos": True, "seed": 42, "trace": False},
                    endpoint="/api/v1/lotomania-modo4/gerar",
                    timeout_s=15.0,
                )
                return bool(
                    r_lm["status_http"] == 200
                    and r_lm["dados_brutos"]["jogos"] == lm_off["dados_brutos"]["jogos"]
                )

            definir_feature_flag_lotofacil_modo4(api_producao.app, ativo=True, motivo="teste_04_concorrencia")
            with ThreadPoolExecutor(max_workers=6) as pool:
                res_list = list(pool.map(_worker, range(10)))
            _exigir(all(res_list), f"Falha sob concorrencia: {res_list}")

            for ep in (
                "/api/v1/motor-lotofacil",
                "/api/v1/motor-lotomania",
                "/api/v1/motor-diadesorte",
                "/api/v1/motor-megasena",
            ):
                rl = chamar_api_lotofacil_modo4_seguro(srv.base_url, {"quantidade_jogos": 3}, endpoint=ep, timeout_s=15.0)
                _exigir(rl["status_http"] == 200, f"Nao interferencia falhou em {ep}: {rl}")

    def test_05_falha_rede_http500_fail_closed(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind(("127.0.0.1", 0))
        porta_morta = sock.getsockname()[1]
        sock.close()

        r_dead = chamar_api_lotofacil_modo4_seguro(
            f"http://127.0.0.1:{porta_morta}", {"quantidade_jogos": 2}, timeout_s=1.0
        )
        _exigir(
            r_dead["sucesso"] is False and r_dead["jogos"] == [] and r_dead["fallback_executado"] is False,
            "Porta fechada deve retornar 0 jogos.",
        )

        class _Err500Handler(BaseHTTPRequestHandler):
            def log_message(self, format: str, *args: Any) -> None:
                return

            def do_POST(self) -> None:
                tam = int(self.headers.get("Content-Length", "0") or 0)
                if tam > 0:
                    _ = self.rfile.read(tam)
                self.send_response(500)
                self.end_headers()
                self.wfile.write(b"erro_simulado")

        srv_err = ThreadingHTTPServer(("127.0.0.1", 0), _Err500Handler)
        threading.Thread(target=srv_err.serve_forever, daemon=True).start()
        try:
            r500 = chamar_api_lotofacil_modo4_seguro(
                f"http://127.0.0.1:{srv_err.server_port}", {"quantidade_jogos": 2}
            )
            _exigir(
                r500["sucesso"] is False
                and r500["status_http"] == 500
                and r500["jogos"] == []
                and r500["fallback_executado"] is False,
                "HTTP 500 deve falhar fechado.",
            )
        finally:
            srv_err.shutdown()
            srv_err.server_close()

    def test_06_ui_web_e_mobile_paridade_e_zero_fallback(self) -> None:
        with open(
            os.path.join(BASE_DIR, "js", "engines", "motor_lotofacil_modo4_engine.js"),
            encoding="utf-8",
        ) as f:
            eng_js = f.read()
        with open(os.path.join(BASE_DIR, "index.html"), encoding="utf-8") as f:
            idx_html = f.read()
        with open(os.path.join(BASE_DIR, "js", "ui.js"), encoding="utf-8") as f:
            ui_js = f.read()
        with open(os.path.join(BASE_DIR, "B2B_Loterias_Mobile.html"), encoding="utf-8") as f:
            mob_html = f.read()

        # Cliente JS nunca referencia motores legados ou aleatoriedade
        for proibido in ("MotorLotofacilB2BEngine", "LotofacilDualStrategy", "LotofacilGroupEngine", "Math.random"):
            _exigir(proibido not in eng_js, f"Proibido encontrar {proibido} em motor_lotofacil_modo4_engine.js.")

        # Verifica isolamento estrito dentro do bloco MODO 4 em ui.js e Mobile
        ui_ini = ui_js.index("    _initLotofacilModo4Controls() {")
        ui_fim = ui_js.index("// Export removed for global script compatibility", ui_ini)
        trecho_ui = ui_js[ui_ini:ui_fim]
        for proibido in ("MotorLotofacilB2BEngine", "LotofacilDualStrategy", "Math.random"):
            _exigir(proibido not in trecho_ui, f"Fallback proibido {proibido} encontrado no handler MODO 4 de ui.js.")

        mob_ini = mob_html.index("    _initLotofacilModo4Controls() {")
        mob_fim = mob_html.index("// Export removed for global script compatibility", mob_ini)
        trecho_mob = mob_html[mob_ini:mob_fim]
        for proibido in ("MotorLotofacilB2BEngine", "LotofacilDualStrategy", "Math.random"):
            _exigir(proibido not in trecho_mob, f"Fallback proibido {proibido} encontrado no handler MODO 4 Mobile.")

        ids_obrigatorios = (
            "tab-btn-lotofacil-modo4",
            "subpanel-lotofacil-modo4",
            "badge-status-lotofacil-modo4",
            "btn-verificar-lotofacil-modo4",
            "clausula-obrigatoria-lotofacil-modo4",
            "alerta-indisponivel-lotofacil-modo4",
            "input-qtd-jogos-lotofacil-modo4",
            "select-tamanho-lotofacil-modo4",
            "check-exp2j-lotofacil-modo4",
            "btn-executar-lotofacil-modo4",
            "btn-avaliar-lotofacil-modo4",
            "container-resultado-lotofacil-modo4",
        )
        for doc_nome, conteudo in (("index.html", idx_html), ("B2B_Loterias_Mobile.html", mob_html)):
            for elem_id in ids_obrigatorios:
                _exigir(elem_id in conteudo, f"ID {elem_id} ausente em {doc_nome}.")
            _exigir(CLAUSULA_MATEMATICA_OBRIGATORIA in conteudo, f"Clausula ausente em {doc_nome}.")
            _exigir(
                'id="subpanel-lotofacil-modo4" style="display:none;"' in conteudo,
                f"Subpainel MODO 4 precisa iniciar oculto por padrao em {doc_nome}.",
            )
            _exigir(
                'id="check-exp2j-lotofacil-modo4" disabled' in conteudo,
                f"Checkbox experimental_2J deve iniciar desabilitada e desmarcada em {doc_nome}.",
            )

        _exigir(CLAUSULA_MATEMATICA_OBRIGATORIA in eng_js, "Clausula ausente em motor_lotofacil_modo4_engine.js.")
        _exigir("MotorLotofacilModo4Engine" in mob_html, "Engine Lotofacil MODO 4 nao embutida no Mobile.")

    def test_07_artefatos_e_dossie_promocao(self) -> None:
        dir_aud = os.path.join(BASE_DIR, "auditoria", "lotofacil_modo4")
        arq_ev = os.path.join(dir_aud, "promocao_controlada_evidencias.json")
        arq_md = os.path.join(dir_aud, "DOSSIE_PROMOCAO_CONTROLADA.md")
        _exigir(os.path.isfile(arq_ev), "promocao_controlada_evidencias.json nao encontrado.")
        _exigir(os.path.isfile(arq_md), "DOSSIE_PROMOCAO_CONTROLADA.md nao encontrado.")

        with open(arq_ev, "r", encoding="utf-8") as f:
            ev = json.load(f)
        _exigir(
            ev["evidencia_flag_off_padrao"]["health_lotofacil_modo4"]["disponivel"] is False,
            "Evidencia OFF deve registrar disponivel=False.",
        )
        _exigir(ev["concorrencia_flag_off"]["falhas"] == 0, "Concorrencia OFF registrou falhas.")
        _exigir(ev["concorrencia_flag_on"]["falhas"] == 0, "Concorrencia ON registrou falhas.")
        _exigir(
            ev["nao_interferencia"]["lotomania_modo4_hashes_identicos"] is True,
            "Evidencia Lotomania hashes nao identicos.",
        )

        with open(arq_md, "r", encoding="utf-8") as f:
            md_txt = f.read()
        _exigir("\u2014" not in md_txt and "\u2013" not in md_txt, "Dossie contem travessao proibido.")
        _exigir(CLAUSULA_MATEMATICA_OBRIGATORIA in md_txt, "Clausula ausente no Dossie.")


if __name__ == "__main__":
    unittest.main()
