# -*- coding: utf-8 -*-
"""
Testes unitarios exclusivamente da FASE 1 (PREPARACAO) do Runbook de Homologacao
Especifica de Ativacao do LOTOFACIL MODO 4.

Nao executa a Fase 2 (carga, browser ou ativacao) nem altera manifestos selados.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lotofacil_modo4.etapa1_regras_oficiais import CLAUSULA_MATEMATICA_OBRIGATORIA
from lotofacil_modo4.homologacao_ativacao_runbook import (
    CAMINHO_CONFIG_JSON,
    CAMINHO_MICROCALIBRACAO_JSON,
    CAMINHO_RELATORIO_REVISAO_MD,
    CAMINHO_RUNBOOK_MD,
    DIR_HOMOLOGACAO_ABS,
    _agrupar_determinismo_por_assinatura,
    _comparar_producao_8000_antes_depois,
    _gerar_assinatura_canonica_entrada,
    _validar_contrato_resposta_legada,
    carregar_config_homologacao,
    coletar_telemetria_hardware,
    medir_memoria_processo_windows,
    verificar_preparacao_somente_leitura,
)


def _exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise AssertionError(mensagem)


class TestLotofacilModo4HomologacaoPreparacao(unittest.TestCase):
    def test_01_arquivos_preparacao_isolados_e_sem_travessao(self) -> None:
        _exigir(os.path.isdir(DIR_HOMOLOGACAO_ABS), "Diretorio isolado de homologacao ausente.")
        _exigir(os.path.isfile(CAMINHO_CONFIG_JSON), "config_homologacao_ativacao.json ausente.")
        _exigir(os.path.isfile(CAMINHO_RUNBOOK_MD), "RUNBOOK_HOMOLOGACAO_ATIVACAO.md ausente.")
        _exigir(os.path.isfile(CAMINHO_MICROCALIBRACAO_JSON), "microcalibracao_fase1.json ausente.")
        _exigir(os.path.isfile(CAMINHO_RELATORIO_REVISAO_MD), "RELATORIO_REVISAO_FASE1.md ausente.")

        # Fase 2 isolada autorizada: valida integridade da Ata GO, Dossie e Evidencias sem reexecutar carga/browser
        caminho_ata = os.path.join(DIR_HOMOLOGACAO_ABS, "ata_homologacao_ativacao.json")
        caminho_dossie = os.path.join(DIR_HOMOLOGACAO_ABS, "DOSSIE_HOMOLOGACAO_ATIVACAO.md")
        caminho_evidencias = os.path.join(DIR_HOMOLOGACAO_ABS, "evidencias_homologacao_ativacao.json")
        _exigir(os.path.isfile(caminho_ata), "ata_homologacao_ativacao.json da Fase 2 isolada ausente.")
        _exigir(os.path.isfile(caminho_dossie), "DOSSIE_HOMOLOGACAO_ATIVACAO.md da Fase 2 isolada ausente.")
        _exigir(os.path.isfile(caminho_evidencias), "evidencias_homologacao_ativacao.json da Fase 2 isolada ausente.")

        with open(caminho_ata, encoding="utf-8") as fa:
            ata = json.load(fa)
        with open(caminho_evidencias, encoding="utf-8") as fe:
            evid = json.load(fe)

        _exigir(ata.get("veredito") == "GO", f"Veredito esperado GO na Fase 2 isolada; obtido {ata.get('veredito')}")
        _exigir(ata.get("versao_avaliada") == "5.1.0-promocao-controlada", "Versao avaliada divergente na Ata.")
        _exigir(ata.get("motivos_no_go") == [], f"Ata GO nao pode ter motivos NO-GO: {ata.get('motivos_no_go')}")
        criterios_esperados = {f"frente_{i}_ok" for i in range(1, 7)}
        _exigir(set(ata.get("criterios", {}).keys()) == criterios_esperados, "Criterios da Ata incompletos.")
        _exigir(all(bool(ata["criterios"][k]) for k in criterios_esperados), "Todas as 6 frentes devem estar aprovadas na Ata GO.")

        _exigir(evid.get("versao_runbook") == "1.1.0-fase1-revisada", "Versao do runbook divergente nas evidencias.")
        _exigir(evid.get("portas_isoladas_utilizadas") == {"api": 18080, "ui": 18081}, "Fase 2 deve registrar exclusivamente portas isoladas 18080/18081.")
        _exigir(evid.get("ata_decisao") == ata, "ata_decisao nas evidencias deve coincidir com ata_homologacao_ativacao.json.")
        _exigir(evid.get("clausula_obrigatoria") == CLAUSULA_MATEMATICA_OBRIGATORIA, "Clausula obrigatoria divergente nas evidencias.")
        comp_8000 = evid["frentes"]["frente_6_rollback"]["producao_8000_comparacao"]
        _exigir(
            comp_8000["preservada"] is True and comp_8000["hashes_identicos"] is True and comp_8000["invariantes_off_ok"] is True,
            "Porta 8000 deve permanecer preservada e com invariantes OFF apos a Fase 2.",
        )

        with open(CAMINHO_CONFIG_JSON, encoding="utf-8") as fc:
            cfg_bruto = fc.read()
        _exigir("workers_simultaneos" not in cfg_bruto, "Nomenclatura workers_simultaneos deve ser substituida por clientes_simultaneos.")
        _exigir("\u2014" not in cfg_bruto and "\u2013" not in cfg_bruto, "Config JSON nao pode conter travessao.")

        cfg = carregar_config_homologacao()
        _exigir(
            cfg["versao_runbook"] == "1.1.0-fase1-revisada",
            f"Versao do runbook esperada 1.1.0-fase1-revisada; obtida {cfg['versao_runbook']}",
        )
        _exigir(
            cfg["versao_alvo_promocao"] == "5.1.0-promocao-controlada",
            f"Versao alvo divergente: {cfg['versao_alvo_promocao']}",
        )
        _exigir(
            cfg["ambiente_homologacao_isolada"]["permitir_experimental_2j"] is False,
            "experimental_2J deve permanecer False no config de homologacao.",
        )
        _exigir(
            cfg["ambiente_homologacao_isolada"]["uvicorn_workers"] == 1,
            "Uvicorn deve declarar explicitamente workers=1.",
        )
        f3 = cfg["criterios_go_no_go"]["frente_3_carga_escalonada"]
        pats = f3["patamares"]
        _exigir(
            [int(p["clientes_simultaneos"]) for p in pats] == [1, 8, 16, 24],
            f"Patamares devem cobrir [1, 8, 16, 24] clientes_simultaneos; obtido {[p.get('clientes_simultaneos') for p in pats]}",
        )
        rotas_esperadas = {
            "lotofacil_modo4_gerar_simples",
            "lotofacil_modo4_gerar_multipla16",
            "lotofacil_modo4_avaliar",
            "lotofacil_modo4_status",
            "lotomania_modo4_gerar",
            "motores_legados",
        }
        for p in pats:
            lim = p.get("limites_latencia_por_tipo_s", {})
            _exigir(
                rotas_esperadas.issubset(set(lim.keys())),
                f"Patamar {p['id']} deve definir p95/p99 para todas as rotas relevantes.",
            )
            for rk, rlims in lim.items():
                _exigir(
                    "max_p95_s" in rlims and "max_p99_s" in rlims and 0.0 < rlims["max_p95_s"] <= rlims["max_p99_s"],
                    f"Limites p95/p99 invalidos em {p['id']}.{rk}",
                )

        pdet = f3["politica_determinismo"]
        _exigir(pdet["modo_agrupamento"] == "por_assinatura_canonica_entrada", "Agrupamento canonico obrigatorio.")
        _exigir(pdet["exigir_hashes_lotomania_repetiveis_sob_carga"] is True, "Lotomania deve exigir repetibilidade sob carga.")
        _exigir(
            pdet["exigir_hashes_diferentes_entre_sementes_distintas"] is False,
            "Ressalva matematica: sementes diferentes nao podem ser forcadas a produzir hashes distintos.",
        )
        lmem = f3["limites_memoria_processo_isolado"]
        _exigir(lmem["metrica_pico"] == "PeakWorkingSetSize", "Metrica obrigatoria de pico de memoria deve ser PeakWorkingSetSize.")
        _exigir(lmem["escopo_processo"] == "exclusivo_subprocesso_uvicorn_workers_1", "Escopo de memoria deve ser exclusivo do subprocesso Uvicorn.")
        _exigir(0.05 <= float(lmem["intervalo_amostragem_s"]) <= 0.5, "Intervalo de amostragem de memoria deve ser periodico (<=0.5s).")

        f6 = cfg["criterios_go_no_go"]["frente_6_rollback_e_preservacao"]
        _exigir(f6["exigir_producao_8000_alcancavel"] is True, "Porta 8000 deve ser exigida de forma fail-closed.")
        _exigir(f6["comparar_estado_8000_antes_e_depois_via_sha256"] is True, "Comparacao antes/depois da porta 8000 deve usar SHA-256.")

        _exigir(len(cfg["regras_automaticas_no_go"]) >= 8, "Regras automaticas endurecidas de NO-GO devem estar registradas.")

        for caminho_md in (
            CAMINHO_RUNBOOK_MD,
            CAMINHO_RELATORIO_REVISAO_MD,
            os.path.join(DIR_HOMOLOGACAO_ABS, "DOSSIE_HOMOLOGACAO_ATIVACAO.md"),
        ):
            with open(caminho_md, encoding="utf-8") as f:
                md = f.read()
            _exigir("\u2014" not in md and "\u2013" not in md, f"Arquivo {os.path.basename(caminho_md)} nao pode conter em-dash ou en-dash.")
            _exigir(CLAUSULA_MATEMATICA_OBRIGATORIA in md, f"Clausula matematica obrigatoria ausente em {os.path.basename(caminho_md)}.")

    def test_02_trava_fail_closed_sem_autorizacao_fase2(self) -> None:
        proc = subprocess.run(
            [sys.executable, "-m", "lotofacil_modo4.homologacao_ativacao_runbook"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=15,
        )
        _exigir(proc.returncode == 2, f"CLI sem flag de autorizacao deve retornar 2; obtido {proc.returncode}")
        dados = json.loads(proc.stdout)
        _exigir(dados["bloqueado"] is True, "Execucao sem autorizacao deve ser bloqueada.")

    def test_03_telemetria_hardware_e_cadeia_selada_intacta(self) -> None:
        hw = coletar_telemetria_hardware()
        _exigir(hw["cpu_threads_logicas"] >= 1, "Contagem de CPU invalida.")
        _exigir(hw["ram_total_gb"] > 0.0, "RAM total invalida.")
        mem = medir_memoria_processo_windows(os.getpid())
        _exigir(mem["rss_atual_mb"] > 0.0 and mem["rss_pico_mb"] >= mem["rss_atual_mb"], "Leitura Win32 RSS invalida.")

        prep = verificar_preparacao_somente_leitura()
        _exigir(prep["homologacao_executada"] is False, "Check de preparacao nao pode executar Fase 2.")
        _exigir(prep["integridade_cadeia_selada"] is True, f"Cadeia selada divergiu: {prep['divergencias']}")
        _exigir(prep["divergencias"] == [], "Nao pode haver divergencias criptograficas na Fase 1.")

    def test_04_criterios_endurecidos_determinismo_8000_legados_e_evidencia_microcalibracao(self) -> None:
        # 1) Determinismo por assinatura canonica: entradas distintas nao causam falso erro,
        # mas entradas identicas com hashes diferentes reprovam
        sig_a = _gerar_assinatura_canonica_entrada("/api/v1/lotofacil-modo4/gerar", "POST", {"semente": 42})
        sig_b = _gerar_assinatura_canonica_entrada("/api/v1/lotofacil-modo4/gerar", "POST", {"semente": 43})
        _exigir(sig_a != sig_b, "Assinatura canonica deve distinguir sementes diferentes.")
        ok_grupos = _agrupar_determinismo_por_assinatura(
            [
                {"tipo": "lotofacil_modo4_gerar_simples", "assinatura_entrada": sig_a, "semente": 42, "hash_saida": "h1", "historico_utilizado": None},
                {"tipo": "lotofacil_modo4_gerar_simples", "assinatura_entrada": sig_a, "semente": 42, "hash_saida": "h1", "historico_utilizado": None},
                {"tipo": "lotofacil_modo4_gerar_simples", "assinatura_entrada": sig_b, "semente": 43, "hash_saida": "h1", "historico_utilizado": None},
                {"tipo": "lotomania_modo4_gerar", "assinatura_entrada": sig_a, "semente": 42, "hash_saida": "hm", "historico_utilizado": None},
            ]
        )
        _exigir(ok_grupos["repetibilidade_ok"] is True, "Convergencia legitima entre sementes distintas deve ser aceita.")
        falha_rep = _agrupar_determinismo_por_assinatura(
            [
                {"tipo": "lotomania_modo4_gerar", "assinatura_entrada": sig_a, "semente": 42, "hash_saida": "hm1", "historico_utilizado": None},
                {"tipo": "lotomania_modo4_gerar", "assinatura_entrada": sig_a, "semente": 42, "hash_saida": "hm2", "historico_utilizado": None},
            ]
        )
        _exigir(falha_rep["repetibilidade_ok"] is False and falha_rep["lotomania_repetibilidade_ok"] is False, "Mesma entrada com hashes distintos deve reprovar.")

        # 2) Producao porta 8000 fail-closed: inacessivel ou mutada reprova
        off_mock = {
            "alcancavel": True,
            "sha256_estado_normalizado": "abc",
            "estado_normalizado": {
                "lotofacil_disponivel": False,
                "feature_flag_ativa": False,
                "experimental_2j_habilitada": False,
                "politica_micro_padrao": "conservadora_3J",
                "inicializacao_mista": "padrao",
                "integridade_verificada": True,
                "lotomania_selo_valido": True,
            },
        }
        _exigir(_comparar_producao_8000_antes_depois({"alcancavel": False}, off_mock, exigir_alcancavel=True)["preservada"] is False, "8000 inacessivel deve reprovar.")
        _exigir(_comparar_producao_8000_antes_depois(off_mock, {**off_mock, "sha256_estado_normalizado": "def"}, exigir_alcancavel=True)["preservada"] is False, "Mudanca de SHA-256 na 8000 deve reprovar.")
        _exigir(_comparar_producao_8000_antes_depois(off_mock, off_mock, exigir_alcancavel=True)["preservada"] is True, "Estado identico OFF na 8000 deve aprovar.")

        # 3) Contrato legado Lotomania aceita faixa 1..100 e rejeita 101
        jogo_valido = list(range(51, 101))
        ok_l, _ = _validar_contrato_resposta_legada("/api/v1/motor-lotomania", {"quantidade_jogos": 1}, {"sucesso": True, "jogos": [jogo_valido]})
        bad_l, _ = _validar_contrato_resposta_legada("/api/v1/motor-lotomania", {"quantidade_jogos": 1}, {"sucesso": True, "jogos": [list(range(52, 102))]})
        _exigir(ok_l is True and bad_l is False, "Validador legado Lotomania deve aceitar 1..100 e rejeitar >100.")

        # 4) Evidencia da microcalibracao gravada preserva Fase 2 bloqueada e porta 8000 intacta
        with open(CAMINHO_MICROCALIBRACAO_JSON, encoding="utf-8") as fm:
            mc = json.load(fm)
        _exigir(mc["fase"] == "REVISAO_FASE_1_MICROCALIBRACAO", "Tipo de evidencia inesperado.")
        _exigir(mc["fase_2_executada"] is False and mc["ativacao_producao"] is False, "Microcalibracao nao pode executar Fase 2 nem ativar producao.")
        _exigir(mc["frente_3_carga_microcalibracao"]["aprovada"] is True, "Carga de microcalibracao deve estar integralmente aprovada.")
        _exigir(mc["frente_5_nao_interferencia"]["aprovada"] is True, "Nao interferencia de microcalibracao deve estar aprovada.")
        _exigir(mc["producao_8000_comparacao"]["preservada"] is True, "Porta 8000 deve constar preservada na microcalibracao.")


if __name__ == "__main__":
    unittest.main()
