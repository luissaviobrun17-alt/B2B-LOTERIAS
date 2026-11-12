#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TESTE 3: INTEGRIDADE E SELO CRIPTOGRÁFICO (Ed25519 + SHA-256) DO MODO 4 v1.2
=============================================================================
Executa os testes formais de integridade, ausência de artefatos e adulteração sem
depender de instruções `assert` (100% compatível com `python -O`, lançando
`RuntimeError` explícito diante de qualquer falha):
1. Selo válido: `verificar_selo_modo4` e `MotorLotomaniaModo4` autorizam execução.
2. Ausência de chave privada (`.key`) dentro do repositório oficial.
3. Selo ausente (`manifesto_modo4.sig`, `manifesto_modo4.json`, `chave_publica_modo4.pem`) -> bloqueado, 0 jogos.
4. Adulteração de módulos protegidos (`motor_lotomania_modo4.py`, `verificador_selo_modo4.py`, `data/lotomania.json`) -> bloqueado, 0 jogos.
5. Adulteração de `manifesto_modo4.json` (parâmetro e hash esperado divergente) -> bloqueado, 0 jogos.
6. Assinatura Ed25519 inválida em `manifesto_modo4.sig` -> bloqueado, 0 jogos.
7. Chave pública Ed25519 incompatível em `chave_publica_modo4.pem` -> bloqueado, 0 jogos.
"""

import json
import os
import shutil
import sys
import tempfile
import unittest

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

DIR_TESTES = os.path.dirname(os.path.abspath(__file__))
DIR_RAIZ = os.path.dirname(DIR_TESTES)
if DIR_RAIZ not in sys.path:
    sys.path.insert(0, DIR_RAIZ)

from motor_lotomania_modo4 import MotorLotomaniaModo4
from verificador_selo_modo4 import IntegridadeModo4Error, verificar_selo_modo4


def exigir(condicao: bool, mensagem: str) -> None:
    if condicao is not True:
        raise RuntimeError(f"Falha de integridade no teste de selo: {mensagem}")


def preparar_ambiente_temporario(tmpdir: str) -> None:
    os.makedirs(os.path.join(tmpdir, "data"), exist_ok=True)
    os.makedirs(os.path.join(tmpdir, "logs"), exist_ok=True)
    for arq in [
        "motor_lotomania_modo4.py",
        "manifesto_modo4.json",
        "manifesto_modo4.sig",
        "chave_publica_modo4.pem",
        "verificador_selo_modo4.py",
    ]:
        shutil.copy2(os.path.join(DIR_RAIZ, arq), os.path.join(tmpdir, arq))
    shutil.copy2(
        os.path.join(DIR_RAIZ, "data", "lotomania.json"),
        os.path.join(tmpdir, "data", "lotomania.json"),
    )


def _executar_cenario_falha(nome: str, mutator_fn) -> dict:
    """
    Executa um cenário de violação em diretório temporário isolado e comprova que:
    1) `verificar_selo_modo4(tmpdir)` bloqueia com `IntegridadeModo4Error`;
    2) `MotorLotomaniaModo4(verificar_selo=True, diretorio_base=tmpdir)` também bloqueia antes
       de gerar qualquer jogo, mantendo `jogos_gerados == 0` e sem fallback alternativo.
    """
    with tempfile.TemporaryDirectory(prefix=f"selo_{nome}_") as tmpdir:
        preparar_ambiente_temporario(tmpdir)
        mutator_fn(tmpdir)

        bloqueado_verif = False
        motivo_verif = ""
        try:
            verificar_selo_modo4(
                tmpdir,
                parametros_runtime=MotorLotomaniaModo4.obter_parametros_runtime(),
            )
        except IntegridadeModo4Error as exc:
            bloqueado_verif = True
            motivo_verif = str(exc)
        exigir(bloqueado_verif, f"Cenário '{nome}': verificar_selo_modo4 não bloqueou!")

        bloqueado_motor = False
        jogos_gerados = []
        motivo_motor = ""
        try:
            motor_tmp = MotorLotomaniaModo4(verificar_selo=True, diretorio_base=tmpdir)
            res = motor_tmp.gerar_carteira_otimizada_cobertura(5, seed=330001, permitir_espelhos=True)
            jogos_gerados = res.get("jogos", [])
        except IntegridadeModo4Error as exc:
            bloqueado_motor = True
            motivo_motor = str(exc)
        exigir(bloqueado_motor, f"Cenário '{nome}': MotorLotomaniaModo4 não bloqueou!")
        exigir(len(jogos_gerados) == 0, f"Cenário '{nome}': produziu {len(jogos_gerados)} jogos em falha!")

        return {
            "bloqueado": True,
            "bloqueado_no_verificador": True,
            "bloqueado_no_motor": True,
            "jogos_gerados": 0,
            "excecao": "IntegridadeModo4Error",
            "mensagem": motivo_verif or motivo_motor,
        }


def testar_selo_valido_e_chave_ausente_repo() -> dict:
    selo_oficial = verificar_selo_modo4(
        DIR_RAIZ,
        parametros_runtime=MotorLotomaniaModo4.obter_parametros_runtime(),
    )
    exigir(selo_oficial.get("selo_valido") is True, "Selo oficial não validado.")
    exigir(selo_oficial.get("versao_motor") == "1.2", "Versão do motor diverge de '1.2'.")

    motor_ok = MotorLotomaniaModo4(verificar_selo=True, diretorio_base=DIR_RAIZ)
    res_ok = motor_ok.gerar_carteira_otimizada_cobertura(2, seed=330001, permitir_espelhos=True)
    exigir(res_ok.get("sucesso") is True and len(res_ok.get("jogos", [])) == 2, "Execução autorizada falhou.")

    repo_oficial = r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS"
    dir_inspecao = repo_oficial if os.path.isdir(repo_oficial) else DIR_RAIZ
    arquivos_key_repo = []
    for root, _dirs, files in os.walk(dir_inspecao):
        if "scratch" in root or ".git" in root:
            continue
        for f in files:
            cam_f = os.path.join(root, f)
            if f.endswith(".key") or "ed25519.key" in f or f.endswith(".pem"):
                with open(cam_f, "r", encoding="utf-8", errors="ignore") as fk:
                    conteudo_k = fk.read()
                if "PRIVATE KEY" in conteudo_k:
                    arquivos_key_repo.append(cam_f)
                elif (f.endswith(".key") or "ed25519.key" in f) and not (
                    os.path.abspath(cam_f) == os.path.abspath(os.path.join(dir_inspecao, "licenca.key"))
                    and "ChaveLicenca=" in conteudo_k
                ):
                    arquivos_key_repo.append(cam_f)
    exigir(
        len(arquivos_key_repo) == 0,
        f"Chave privada encontrada no repositório: {arquivos_key_repo}",
    )
    return selo_oficial


def executar_testes_selo() -> dict:
    selo_oficial = testar_selo_valido_e_chave_ausente_repo()

    cenarios_adulteracao = {}

    def _adulterar_nucleo(d: str) -> None:
        with open(os.path.join(d, "motor_lotomania_modo4.py"), "ab") as f:
            f.write(b"\n# adulteracao_teste\n")

    def _adulterar_verificador(d: str) -> None:
        with open(os.path.join(d, "verificador_selo_modo4.py"), "ab") as f:
            f.write(b"\n# adulteracao_verificador\n")

    def _adulterar_base(d: str) -> None:
        with open(os.path.join(d, "data", "lotomania.json"), "ab") as f:
            f.write(b" ")

    def _adulterar_parametro_manifesto(d: str) -> None:
        p = os.path.join(d, "manifesto_modo4.json")
        with open(p, "r", encoding="utf-8") as f:
            man = json.load(f)
        man["parametros_homologados"]["peso_inter"] = 30.1
        with open(p, "w", encoding="utf-8") as f:
            json.dump(man, f, indent=2, ensure_ascii=False)

    def _adulterar_hash_manifesto(d: str) -> None:
        p = os.path.join(d, "manifesto_modo4.json")
        with open(p, "r", encoding="utf-8") as f:
            man = json.load(f)
        man["arquivos_protegidos"]["motor_lotomania_modo4.py"] = "0" * 64
        with open(p, "w", encoding="utf-8") as f:
            json.dump(man, f, indent=2, ensure_ascii=False)

    def _adulterar_assinatura(d: str) -> None:
        p = os.path.join(d, "manifesto_modo4.sig")
        with open(p, "r", encoding="utf-8") as f:
            sig_hex = f.read().strip()
        primeiro_char = "0" if sig_hex[0] != "0" else "1"
        with open(p, "w", encoding="utf-8") as f:
            f.write(primeiro_char + sig_hex[1:] + "\n")

    def _chave_publica_incompativel(d: str) -> None:
        chave_estranha = Ed25519PrivateKey.generate().public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        with open(os.path.join(d, "chave_publica_modo4.pem"), "wb") as f:
            f.write(chave_estranha)

    especificacoes = [
        ("cenario_A_adulteracao_nucleo", _adulterar_nucleo),
        ("cenario_B_adulteracao_base_historica", _adulterar_base),
        ("cenario_C_adulteracao_parametro", _adulterar_parametro_manifesto),
        ("cenario_D_adulteracao_assinatura", _adulterar_assinatura),
        ("cenario_E_chave_publica_incompativel", _chave_publica_incompativel),
        ("cenario_F_selo_ausente_sig", lambda d: os.remove(os.path.join(d, "manifesto_modo4.sig"))),
        ("cenario_G_manifesto_ausente", lambda d: os.remove(os.path.join(d, "manifesto_modo4.json"))),
        ("cenario_H_chave_publica_ausente", lambda d: os.remove(os.path.join(d, "chave_publica_modo4.pem"))),
        ("cenario_I_manifesto_hash_modificado", _adulterar_hash_manifesto),
        ("cenario_J_adulteracao_verificador", _adulterar_verificador),
    ]

    for nome, fn in especificacoes:
        cenarios_adulteracao[nome] = _executar_cenario_falha(nome, fn)

    exigir(len(cenarios_adulteracao) == 10, f"Esperados 10 cenários, executados {len(cenarios_adulteracao)}.")

    return {
        "sucesso": True,
        "selo_oficial": selo_oficial,
        "chave_privada_fora_repositorio": True,
        "cenarios_adulteracao_testados": len(cenarios_adulteracao),
        "todos_cenarios_zero_jogos_confirmados": True,
        "detalhes_cenarios": cenarios_adulteracao,
    }


def test_selo_oficial_autoriza_execucao():
    selo = testar_selo_valido_e_chave_ausente_repo()
    exigir(selo["selo_valido"] is True, "Selo oficial inválido.")


def test_selo_ausente_sig_bloqueia_e_nao_gera_jogos():
    res = _executar_cenario_falha("sig_ausente", lambda d: os.remove(os.path.join(d, "manifesto_modo4.sig")))
    exigir(res["bloqueado"] and res["jogos_gerados"] == 0, "Falha no bloqueio de .sig ausente.")


def test_selo_ausente_manifesto_e_chave_bloqueiam_sem_jogos():
    r1 = _executar_cenario_falha("manifesto_ausente", lambda d: os.remove(os.path.join(d, "manifesto_modo4.json")))
    r2 = _executar_cenario_falha("chave_ausente", lambda d: os.remove(os.path.join(d, "chave_publica_modo4.pem")))
    exigir(r1["jogos_gerados"] == 0 and r2["jogos_gerados"] == 0, "Falha em bloqueio por ausência.")


def test_todos_cenarios_adulteracao_e_chave_incompativel():
    res = executar_testes_selo()
    exigir(res["sucesso"] is True and res["cenarios_adulteracao_testados"] == 10, "Falha na bateria completa.")


class TestModo4Selo(unittest.TestCase):
    def test_selo_oficial_valido(self):
        test_selo_oficial_autoriza_execucao()

    def test_selo_ausente_bloqueado(self):
        test_selo_ausente_sig_bloqueia_e_nao_gera_jogos()
        test_selo_ausente_manifesto_e_chave_bloqueiam_sem_jogos()

    def test_bateria_completa_10_cenarios_fail_closed(self):
        test_todos_cenarios_adulteracao_e_chave_incompativel()


if __name__ == "__main__":
    resultado = executar_testes_selo()
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
