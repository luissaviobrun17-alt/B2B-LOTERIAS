# -*- coding: utf-8 -*-
"""
Testes unitarios e de contrato da Preparacao Auditavel da FASE 3 (Promocao em Producao).

Executa somente validacoes estaticas e ensaios em porta efemera isolada
(nunca na porta 8000 e sem gerar arquivos de execucao na pasta oficial da Fase 3).
Compativel com `python` e `python -O` (sem instrucoes `assert`).
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import unittest
from typing import Any, Dict, Optional

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lotofacil_modo4.etapa1_regras_oficiais import CLAUSULA_MATEMATICA_OBRIGATORIA
from lotofacil_modo4.homologacao_ativacao_runbook import (
    _SubprocessoUvicornIsolado,
    _reservar_porta_livre,
)
from lotofacil_modo4.promocao_fase3_runbook import (
    ALLOWLIST_ENV_FASE3,
    CAMINHO_CONFIG_FASE3_JSON,
    CAMINHO_RUNBOOK_FASE3_MD,
    DIR_FASE3_ABS,
    TOKEN_CONFIRMACAO_HUMANA_FASE3,
    carregar_config_fase3,
    executar_protocolo_fase3_controlado,
    parsear_pid_netstat_tcp,
    planejar_acao_contingencia_fase3,
    recalcular_hashes_7_arquivos_selados,
    sanitizar_variaveis_ambiente_snapshot,
    validar_ordem_pos_rollback,
    verificar_preparacao_fase3_somente_leitura,
)
from lotofacil_modo4.promocao_producao import ARQUIVOS_PRODUCAO_PROMOCAO


def _exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise AssertionError(mensagem)


class _ControladorUvicornEfemeroTestes:
    """Wrapper de ciclo de vida exclusivamente em porta efemera isolada (!= 8000)."""

    def __init__(self, porta: int) -> None:
        _exigir(int(porta) != 8000, "Testes nunca podem operar sobre a porta 8000.")
        self.porta = int(porta)
        self.base_url = f"http://127.0.0.1:{self.porta}"
        self._srv: Optional[_SubprocessoUvicornIsolado] = None
        self.historico_modos: list[bool] = []

    def pid_atual(self) -> Optional[int]:
        if self._srv is not None and self._srv.proc is not None:
            return self._srv.proc.pid
        return None

    def reiniciar_para(
        self,
        *,
        lotofacil_modo4_ativo: bool,
        permitir_experimental_2j: bool = False,
        politica_micro: str = "conservadora_3J",
    ) -> Dict[str, Any]:
        self.encerrar()
        self._srv = _SubprocessoUvicornIsolado(
            porta=self.porta,
            lotofacil_modo4_ativo=lotofacil_modo4_ativo,
            permitir_experimental_2j=permitir_experimental_2j,
            politica_micro=politica_micro,
        )
        self._srv.__enter__()
        self.historico_modos.append(bool(lotofacil_modo4_ativo))
        return {"pid": self.pid_atual(), "ativo": lotofacil_modo4_ativo}

    def encerrar(self) -> None:
        if self._srv is not None:
            self._srv.__exit__(None, None, None)
            self._srv = None


class TestLotofacilModo4PromocaoFase3Preparacao(unittest.TestCase):
    def test_01_artefatos_preparacao_fase3_completos_e_sem_travessao(self) -> None:
        _exigir(os.path.isdir(DIR_FASE3_ABS), "Diretorio promocao_fase3 ausente.")
        _exigir(os.path.isfile(CAMINHO_CONFIG_FASE3_JSON), "config_promocao_fase3.json ausente.")
        _exigir(os.path.isfile(CAMINHO_RUNBOOK_FASE3_MD), "RUNBOOK_PROMOCAO_FASE3.md ausente.")

        # Nenhum artefato de execucao em producao pode existir antes de autorizacao expressa
        for nome_exec in ("ata_promocao_fase3.json", "evidencias_promocao_fase3.json", "DOSSIE_PROMOCAO_FASE3.md"):
            _exigir(
                not os.path.exists(os.path.join(DIR_FASE3_ABS, nome_exec)),
                f"Artefato de execucao {nome_exec} nao pode existir durante a preparacao.",
            )

        caminho_relatorio_md = os.path.join(DIR_FASE3_ABS, "RELATORIO_PREPARACAO_FASE3.md")
        _exigir(os.path.isfile(caminho_relatorio_md), "RELATORIO_PREPARACAO_FASE3.md ausente.")
        with open(CAMINHO_CONFIG_FASE3_JSON, "r", encoding="utf-8") as fc:
            cfg_bruto = fc.read()
        with open(CAMINHO_RUNBOOK_FASE3_MD, "r", encoding="utf-8") as fm:
            md_bruto = fm.read()
        with open(caminho_relatorio_md, "r", encoding="utf-8") as fr:
            rel_bruto = fr.read()
        for nome, txt in (
            ("config_promocao_fase3.json", cfg_bruto),
            ("RUNBOOK_PROMOCAO_FASE3.md", md_bruto),
            ("RELATORIO_PREPARACAO_FASE3.md", rel_bruto),
        ):
            _exigir("\u2014" not in txt and "\u2013" not in txt, f"{nome} contem travessao proibido.")
            _exigir(CLAUSULA_MATEMATICA_OBRIGATORIA in txt, f"Clausula matematica ausente em {nome}.")

        cfg = carregar_config_fase3()
        _exigir(cfg["prerequisitos_fase2"]["merge_main_proibido"] is True, "Merge em main deve estar proibido.")
        _exigir(cfg["parametros_producao"]["permitir_experimental_2j"] is False, "experimental_2J deve permanecer False.")
        _exigir(cfg["parametros_producao"]["politica_micro_homologada"] == "conservadora_3J", "Politica conservadora_3J obrigatoria.")
        _exigir(cfg["parametros_producao"]["inicializacao_mista"] == "padrao", "Inicializacao padrao obrigatoria.")

        ex = cfg["cinco_exigencias_adicionais"]
        for chave in (
            "1_snapshot_anterior",
            "2_integridade_posterior",
            "3_teste_controlado",
            "4_monitoramento",
            "5_rollback_comprovado",
        ):
            _exigir(chave in ex, f"Exigencia adicional ausente: {chave}")
        _exigir(
            int(ex["3_teste_controlado"]["payload_inicial_pequeno"]["quantidade_jogos"]) <= 5,
            "Teste controlado inicial deve comecar pequeno.",
        )

        defs = cfg["tres_definicoes_operacionais"]
        _exigir("1_escopo_snapshot_ambiente" in defs, "Definicao 1 ausente.")
        _exigir("2_ordem_rollback_e_estado_final" in defs, "Definicao 2 ausente.")
        _exigir("3_contingencia_reinicio_8000" in defs, "Definicao 3 ausente.")

    def test_02_travas_fail_closed_cli_e_executor(self) -> None:
        sem_flag = subprocess.run(
            [sys.executable, "-m", "lotofacil_modo4.promocao_fase3_runbook"],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=15,
        )
        _exigir(sem_flag.returncode == 2, f"CLI sem flag deve retornar 2; obtido {sem_flag.returncode}")
        _exigir(json.loads(sem_flag.stdout)["bloqueado"] is True, "CLI sem flag deve retornar bloqueado=True.")

        parcial = subprocess.run(
            [
                sys.executable,
                "-m",
                "lotofacil_modo4.promocao_fase3_runbook",
                "--autorizar-execucao-fase3",
                "--pos-rollback-modo",
                "encerrar_em_off_standby",
            ],
            cwd=BASE_DIR,
            capture_output=True,
            text=True,
            timeout=15,
        )
        _exigir(parcial.returncode == 2, "CLI sem confirmacao humana deve retornar 2.")

        ctrl_dummy = _ControladorUvicornEfemeroTestes(_reservar_porta_livre(18280))
        bloqueou_auth = False
        try:
            executar_protocolo_fase3_controlado(
                controlador_processo=ctrl_dummy,
                autorizacao_explicita=False,
                confirmacao_humana=TOKEN_CONFIRMACAO_HUMANA_FASE3,
                pos_rollback_modo="encerrar_em_off_standby",
                dir_saida=None,
            )
        except PermissionError:
            bloqueou_auth = True
        _exigir(bloqueou_auth, "Executor direto sem autorizacao_explicita=True deve falhar com PermissionError.")

        bloqueou_2j = False
        try:
            executar_protocolo_fase3_controlado(
                controlador_processo=ctrl_dummy,
                autorizacao_explicita=True,
                confirmacao_humana=TOKEN_CONFIRMACAO_HUMANA_FASE3,
                pos_rollback_modo="encerrar_em_off_standby",
                permitir_experimental_2j=True,
                dir_saida=None,
            )
        except PermissionError:
            bloqueou_2j = True
        _exigir(bloqueou_2j, "Executor deve recusar permitir_experimental_2j=True.")

        bloqueou_modo = False
        try:
            validar_ordem_pos_rollback(None)
        except ValueError:
            bloqueou_modo = True
        _exigir(bloqueou_modo, "Ausencia de pos_rollback_modo deve levantar ValueError.")

    def test_03_snapshot_allowlist_nunca_expoe_segredos_ou_variaveis_extras(self) -> None:
        env_simulado = {
            "LOTOFACIL_MODO4_ATIVO": "false",
            "GITHUB_TOKEN": "ghp_SEGREDO_CRITICO_NAO_VAZAR",
            "AWS_SECRET_ACCESS_KEY": "aws_segredo_nao_vazar",
            "DATABASE_URL": "postgresql://user:senha@host/db",
            "API_SECRET_KEY": "chave_privada_simulada",
        }
        snap_env = sanitizar_variaveis_ambiente_snapshot(environ_map=env_simulado)
        bruto = json.dumps(snap_env)
        _exigir(snap_env["proibir_dump_ambiente_completo"] is True, "Flag de proibicao de dump completo obrigatoria.")
        _exigir(set(snap_env["variaveis_permitidas"].keys()) == set(ALLOWLIST_ENV_FASE3), "Snapshot deve conter somente allowlist.")
        _exigir(snap_env["total_variaveis_omitidas_por_seguranca"] == 4, "Contagem de variaveis omitidas divergente.")
        for segredo in ("GITHUB_TOKEN", "AWS_SECRET_ACCESS_KEY", "DATABASE_URL", "API_SECRET_KEY", "ghp_SEGREDO", "senha@host"):
            _exigir(segredo not in bruto, f"Segredo/chave nao permitida vazou no snapshot: {segredo}")

    def test_04_maquina_contingencia_e_parser_netstat(self) -> None:
        saida_netstat = "\n".join(
            [
                "  Proto  Endereco local         Endereco externo       Estado           PID",
                "  TCP    0.0.0.0:80000          0.0.0.0:0              LISTENING       9999",
                "  TCP    127.0.0.1:8000         127.0.0.1:51234        ESTABLISHED     4321",
                "  TCP    127.0.0.1:8000         0.0.0.0:0              ESCUTANDO       24680",
            ]
        )
        _exigir(parsear_pid_netstat_tcp(saida_netstat, porta=8000) == 24680, "Parser deve identificar exatamente porta 8000 em escuta.")
        _exigir(parsear_pid_netstat_tcp(saida_netstat, porta=18080) is None, "Porta ausente deve retornar None.")

        c_selo = planejar_acao_contingencia_fase3(
            processo_iniciou=True,
            integridade_ok=False,
            teste_controlado_ok=True,
            monitoramento_ok=True,
        )
        _exigir(c_selo["acao"] == "abortar_fail_closed_divergencia_selada", "Divergencia selada deve abortar fail-closed.")
        _exigir(c_selo["restaurar_8000_off"] is False and c_selo["mascaramento_permitido"] is False, "Divergencia selada proibe mascaramento.")

        c_subida = planejar_acao_contingencia_fase3(
            processo_iniciou=False,
            integridade_ok=True,
            teste_controlado_ok=True,
            monitoramento_ok=True,
        )
        _exigir(c_subida["acao"] == "abortar_e_restaurar_porta_8000_off" and c_subida["restaurar_8000_off"] is True, "Falha de subida sem divergencia deve restaurar 8000 OFF.")

        c_ok = planejar_acao_contingencia_fase3(
            processo_iniciou=True,
            integridade_ok=True,
            teste_controlado_ok=True,
            monitoramento_ok=True,
            rollback_ok=True,
        )
        _exigir(c_ok["acao"] == "prosseguir" and c_ok["abortar"] is False, "Cenario nominal deve prosseguir.")

    def test_05_preparacao_somente_leitura_e_7_hashes_selados(self) -> None:
        prep = verificar_preparacao_fase3_somente_leitura()
        _exigir(prep["fase3_executada"] is False, "Preparacao nao pode indicar Fase 3 executada.")
        _exigir(prep["pronto_para_deliberacao"] is True, f"Preparacao deve estar pronta: {prep}")
        _exigir(prep["ata_fase2_veredito"] == "GO", "Pre-requisito Fase 2 GO deve estar verificado.")
        _exigir(prep["integridade_cadeia_selada"] is True and prep["divergencias"] == [], "Cadeia selada deve estar integra.")
        _exigir(set(prep["hashes_7_selados"].keys()) == set(ARQUIVOS_PRODUCAO_PROMOCAO), "Devem constar exatamente os 7 arquivos selados.")

    def test_06_protocolo_6_etapas_e_abortos_em_porta_efemera_isolada(self) -> None:
        porta_a = _reservar_porta_livre(18290)
        ctrl_a = _ControladorUvicornEfemeroTestes(porta_a)
        try:
            ctrl_a.reiniciar_para(lotofacil_modo4_ativo=False)
            with tempfile.TemporaryDirectory() as tmp_ok:
                res_ok = executar_protocolo_fase3_controlado(
                    controlador_processo=ctrl_a,
                    autorizacao_explicita=True,
                    confirmacao_humana=TOKEN_CONFIRMACAO_HUMANA_FASE3,
                    pos_rollback_modo="encerrar_em_off_standby",
                    permitir_experimental_2j=False,
                    dir_saida=tmp_ok,
                    porta_alvo=porta_a,
                )
                _exigir(res_ok["ata_decisao"]["veredito"] == "GO", f"Protocolo isolado deveria aprovar GO: {res_ok['ata_decisao']}")
                _exigir(res_ok["ata_decisao"]["estado_final_ativo"] is False, "Modo encerrar_em_off_standby deve manter OFF ao final.")
                _exigir(res_ok["etapas"]["etapa_3_teste_controlado"]["aprovado"] is True, "Teste controlado pequeno+adicional falhou.")
                _exigir(res_ok["etapas"]["etapa_4_monitoramento"]["aprovado"] is True, "Monitoramento falhou.")
                _exigir(res_ok["etapas"]["etapa_5_rollback_comprovado"]["aprovado"] is True, "Rollback comprovado 503 falhou.")
                _exigir(os.path.isfile(os.path.join(tmp_ok, "DOSSIE_PROMOCAO_FASE3.md")), "Dossie temporario deveria existir.")

            res_reat = executar_protocolo_fase3_controlado(
                controlador_processo=ctrl_a,
                autorizacao_explicita=True,
                confirmacao_humana=TOKEN_CONFIRMACAO_HUMANA_FASE3,
                pos_rollback_modo="reativar_on_com_revalidacao",
                permitir_experimental_2j=False,
                dir_saida=None,
                porta_alvo=porta_a,
            )
            _exigir(res_reat["ata_decisao"]["veredito"] == "GO", "Modo reativar_on_com_revalidacao deve aprovar GO.")
            _exigir(res_reat["ata_decisao"]["estado_final_ativo"] is True, "Modo reativar_on_com_revalidacao deve concluir ON.")
            _exigir(res_reat["etapas"]["etapa_6_pos_rollback_final"]["integridade_final_ok"] is True, "Revalidacao final dos 7 selados falhou.")

            # Simulacao controlada de divergencia nos 7 selados apos reinicio ON -> aborto fail-closed imediato
            def _recalculo_adulterado(**kwargs: Any) -> Dict[str, Any]:
                base = recalcular_hashes_7_arquivos_selados(diretorio_base=BASE_DIR)
                base["integro"] = False
                base["divergencias_totais"] = [{"arquivo": "api.py", "motivo": "simulacao_adulteracao_teste"}]
                return base

            res_selo = executar_protocolo_fase3_controlado(
                controlador_processo=ctrl_a,
                autorizacao_explicita=True,
                confirmacao_humana=TOKEN_CONFIRMACAO_HUMANA_FASE3,
                pos_rollback_modo="encerrar_em_off_standby",
                dir_saida=None,
                recalculo_integridade_fn=_recalculo_adulterado,
                porta_alvo=porta_a,
            )
            _exigir(res_selo["ata_decisao"]["veredito"] == "NO-GO", "Divergencia selada deve gerar NO-GO.")
            _exigir(res_selo["ata_decisao"]["contingencia"]["acao"] == "abortar_fail_closed_divergencia_selada", "Acao divergente.")
            _exigir("etapa_3_teste_controlado" not in res_selo["etapas"], "Teste controlado nao pode rodar apos divergencia de selo.")

            # Simulacao de falha de subida sem divergencia selada -> restauracao imediata OFF validada
            class _CtrlFalhaSubidaOn(_ControladorUvicornEfemeroTestes):
                def reiniciar_para(self, **kwargs: Any) -> Dict[str, Any]:
                    if kwargs.get("lotofacil_modo4_ativo") is True:
                        raise RuntimeError("Falha simulada na subida ON")
                    return super().reiniciar_para(**kwargs)

            ctrl_b = _CtrlFalhaSubidaOn(_reservar_porta_livre(18295))
            try:
                ctrl_b.reiniciar_para(lotofacil_modo4_ativo=False)
                res_sub = executar_protocolo_fase3_controlado(
                    controlador_processo=ctrl_b,
                    autorizacao_explicita=True,
                    confirmacao_humana=TOKEN_CONFIRMACAO_HUMANA_FASE3,
                    pos_rollback_modo="encerrar_em_off_standby",
                    dir_saida=None,
                    porta_alvo=ctrl_b.porta,
                )
                _exigir(res_sub["ata_decisao"]["contingencia"]["acao"] == "abortar_e_restaurar_porta_8000_off", "Falha sem divergencia deve restaurar OFF.")
                _exigir(res_sub["ata_decisao"]["restauracao_off"]["aprovado"] is True, "Restauracao OFF deveria validar HTTP 503 e legados.")
            finally:
                ctrl_b.encerrar()
        finally:
            ctrl_a.encerrar()


if __name__ == "__main__":
    unittest.main()
