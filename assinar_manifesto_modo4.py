# -*- coding: utf-8 -*-
"""
FERRAMENTA OFFLINE DE ASSINATURA DO MANIFESTO — LOTOMANIA MODO 4 (v1.2)
=======================================================================
Utilitario administrativo de linha de comando (uso exclusivo do responsavel
pelo sistema). Nao e importado pela API nem exposto por rotas de rede.

Operacoes realizadas:
1. Carrega (ou gera na primeira execucao) a chave privada Ed25519 em diretorio
   EXTERNO ao repositorio: C:\\Users\\Luis Brun\\B2B_chaves\\modo4_ed25519.key
2. Exporta a chave publica correspondente para chave_publica_modo4.pem no repositorio.
3. Calcula os hashes SHA-256 de 64 caracteres dos artefatos selados:
   - motor_lotomania_modo4.py
   - verificador_selo_modo4.py
   - data/lotomania.json (corte fixo no concurso 2699)
4. Gera manifesto_modo4.json e assina seus bytes canonicos com Ed25519 em manifesto_modo4.sig.
5. Registra o evento de assinatura em logs/assinaturas_modo4.log.
"""

import datetime
import hashlib
import json
import os
import subprocess
import sys
from typing import Optional

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from verificador_selo_modo4 import (
    IDENTIFICACAO_OFICIAL_MODO4,
    CLAUSULA_OBRIGATORIA_MODO4,
    PARAMETROS_HOMOLOGADOS_V1_2,
    calcular_sha256_arquivo,
    serializar_manifesto_canonico,
    verificar_selo_modo4,
)

DIRETORIO_CHAVES_EXTERNO = r"C:\Users\Luis Brun\B2B_chaves"
CAMINHO_CHAVE_PRIVADA = os.path.join(DIRETORIO_CHAVES_EXTERNO, "modo4_ed25519.key")


def _restringir_permissoes_windows(caminho: str) -> None:
    """Restringe permissoes ACL no Windows ao usuario atual para proteger a chave privada."""
    usuario = os.environ.get("USERNAME")
    if not usuario or os.name != "nt":
        return
    try:
        subprocess.run(
            ["icacls", caminho, "/inheritance:r", "/grant:r", f"{usuario}:(F)"],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except Exception:
        pass


def obter_ou_gerar_chave_privada(caminho_privada: str = CAMINHO_CHAVE_PRIVADA) -> Ed25519PrivateKey:
    """Carrega a chave privada Ed25519 externa ou gera uma nova se nao existir."""
    pasta = os.path.dirname(os.path.abspath(caminho_privada))
    os.makedirs(pasta, exist_ok=True)

    if os.path.isfile(caminho_privada):
        with open(caminho_privada, "rb") as f_priv:
            chave = serialization.load_pem_private_key(f_priv.read(), password=None)
        if not isinstance(chave, Ed25519PrivateKey):
            raise RuntimeError("O arquivo de chave privada nao contem uma chave Ed25519 valida.")
        return chave

    chave = Ed25519PrivateKey.generate()
    pem_priv = chave.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    with open(caminho_privada, "wb") as f_priv:
        f_priv.write(pem_priv)
    _restringir_permissoes_windows(caminho_privada)
    return chave


def assinar_manifesto(diretorio_repo: Optional[str] = None) -> dict:
    """Gera e assina o manifesto externo do motor Lotomania MODO 4 v1.2."""
    base_dir = diretorio_repo or os.path.dirname(os.path.abspath(__file__))

    # Garantia de que a chave privada NUNCA reside dentro do repositorio
    repo_real = os.path.realpath(base_dir)
    priv_real = os.path.realpath(CAMINHO_CHAVE_PRIVADA)
    if priv_real.startswith(repo_real + os.sep):
        raise RuntimeError(
            "Violacao de seguranca: a chave privada nao pode residir dentro do repositorio."
        )

    chave_privada = obter_ou_gerar_chave_privada(CAMINHO_CHAVE_PRIVADA)
    chave_publica = chave_privada.public_key()

    pem_pub = chave_publica.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    caminho_pub = os.path.join(base_dir, "chave_publica_modo4.pem")
    with open(caminho_pub, "wb") as f_pub:
        f_pub.write(pem_pub)

    arquivos_protegidos = {
        "motor_lotomania_modo4.py": calcular_sha256_arquivo(
            os.path.join(base_dir, "motor_lotomania_modo4.py")
        ),
        "verificador_selo_modo4.py": calcular_sha256_arquivo(
            os.path.join(base_dir, "verificador_selo_modo4.py")
        ),
        "chave_publica_modo4.pem": calcular_sha256_arquivo(
            os.path.join(base_dir, "chave_publica_modo4.pem")
        ),
        "data/lotomania.json": calcular_sha256_arquivo(
            os.path.join(base_dir, "data", "lotomania.json")
        ),
    }

    manifesto = {
        "identificacao_oficial": IDENTIFICACAO_OFICIAL_MODO4,
        "versao": "1.2",
        "algoritmo_assinatura": "Ed25519",
        "algoritmo_hash": "SHA-256",
        "clausula_obrigatoria": CLAUSULA_OBRIGATORIA_MODO4,
        "politica_base_historica": (
            "Base historica de referencia selada com corte fixo no concurso 2699 "
            "(2.699 concursos). O nucleo gerador MODO 4 v1.2 opera com historico=None "
            "e sem filtro de repeticao do ultimo concurso, preservando 100% de equivalencia "
            "com a auditoria homologada."
        ),
        "parametros_homologados": dict(PARAMETROS_HOMOLOGADOS_V1_2),
        "arquivos_protegidos": arquivos_protegidos,
    }

    caminho_manifesto = os.path.join(base_dir, "manifesto_modo4.json")
    with open(caminho_manifesto, "w", encoding="utf-8") as f_man:
        json.dump(manifesto, f_man, indent=2, ensure_ascii=False, sort_keys=True)

    bytes_canonicos = serializar_manifesto_canonico(manifesto)
    assinatura = chave_privada.sign(bytes_canonicos)
    assinatura_hex = assinatura.hex()

    caminho_sig = os.path.join(base_dir, "manifesto_modo4.sig")
    with open(caminho_sig, "w", encoding="ascii") as f_sig:
        f_sig.write(assinatura_hex + "\n")

    # Verifica imediatamente o selo recem-gerado
    status_verificacao = verificar_selo_modo4(diretorio_base=base_dir)

    # Registra auditoria de assinatura em logs/assinaturas_modo4.log
    pasta_logs = os.path.join(base_dir, "logs")
    os.makedirs(pasta_logs, exist_ok=True)
    caminho_log = os.path.join(pasta_logs, "assinaturas_modo4.log")
    registro_log = {
        "timestamp_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "versao": "1.2",
        "sha256_manifesto": hashlib.sha256(bytes_canonicos).hexdigest(),
        "assinatura_ed25519_prefixo": assinatura_hex[:32],
        "arquivos_protegidos": arquivos_protegidos,
        "chave_privada_externa": CAMINHO_CHAVE_PRIVADA,
    }
    with open(caminho_log, "a", encoding="utf-8") as f_log:
        f_log.write(json.dumps(registro_log, ensure_ascii=False) + "\n")

    return status_verificacao


if __name__ == "__main__":
    resultado = assinar_manifesto()
    print("Manifesto MODO 4 v1.2 assinado e verificado com sucesso:")
    print(json.dumps(resultado, indent=2, ensure_ascii=False))
