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
    CAMINHO_RUNBOOK_MD,
    DIR_HOMOLOGACAO_ABS,
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

        cfg = carregar_config_homologacao()
        _exigir(
            cfg["versao_alvo_promocao"] == "5.1.0-promocao-controlada",
            f"Versao alvo divergente: {cfg['versao_alvo_promocao']}",
        )
        _exigir(
            cfg["ambiente_homologacao_isolada"]["permitir_experimental_2j"] is False,
            "experimental_2J deve permanecer False no config de homologacao.",
        )
        _exigir(
            len(cfg["criterios_go_no_go"]["frente_3_carga_escalonada"]["patamares"]) >= 3,
            "Esperados ao menos 3 patamares escalonados calibrados ao hardware.",
        )
        _exigir(
            len(cfg["regras_automaticas_no_go"]) >= 5,
            "Regras automaticas de NO-GO devem estar registradas.",
        )

        with open(CAMINHO_RUNBOOK_MD, encoding="utf-8") as f:
            md = f.read()
        _exigir("\u2014" not in md and "\u2013" not in md, "Runbook nao pode conter em-dash ou en-dash.")
        _exigir(CLAUSULA_MATEMATICA_OBRIGATORIA in md, "Clausula matematica obrigatoria ausente no Runbook.")

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


if __name__ == "__main__":
    unittest.main()
