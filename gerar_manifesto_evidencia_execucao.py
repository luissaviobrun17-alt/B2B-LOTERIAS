#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GERADOR E VERIFICADOR DO MANIFESTO DE EVIDENCIA DA EXECUCAO DE HOMOLOGACAO (Ed25519 + SHA-256)
==============================================================================================
Gera e assina digitalmente (Ed25519) o manifesto de cadeia de custodia da execucao
(`manifesto_evidencia_execucao_modo4.json` + `manifesto_evidencia_execucao_modo4.sig`),
vinculando criptograficamente:
1. Hashes SHA-256 de TODOS os 22 arquivos-fonte, dados brutos, modulos auxiliares,
   testes unitarios, testes da Etapa 6, verificador do selo e verificador independente.
2. Hash SHA-256 do relatorio `relatorio_matriz_modo4.json` finalizado na execucao (esquema 1.2.2).
3. Hash SHA-256 do log integral finalizado da tarefa, calculado SOMENTE apos o encerramento
   definitivo do processo de homologacao (e nunca dentro de diretorios de pacote para a chave .key).
4. Verificacao matematica de correspondencia entre chave privada e chave publica oficial fixada
   (`CHAVE_PUBLICA_OFICIAL_SHA256`) antes de emitir a assinatura, sem expor bytes da chave em log.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
import stat
import sys

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey, Ed25519PublicKey

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from verificador_selo_modo4 import (
    CHAVE_PUBLICA_OFICIAL_SHA256,
    CLAUSULA_OBRIGATORIA_MODO4,
    IDENTIFICACAO_OFICIAL_MODO4,
    PARAMETROS_HOMOLOGADOS_V1_2,
    calcular_sha256_arquivo,
    serializar_manifesto_canonico,
)


def exigir(condicao: bool, mensagem: str) -> None:
    if condicao is not True:
        raise RuntimeError(f"Falha fail-closed na geracao/assinatura do manifesto de evidencia: {mensagem}")


def gerar_e_assinar_manifesto_evidencia(
    caminho_log_task: str = "",
    assinar: bool = True,
    exigir_assinatura: bool = True,
) -> dict:
    caminho_rel = os.path.join(BASE_DIR, "relatorio_matriz_modo4.json")
    exigir(os.path.isfile(caminho_rel), f"Relatorio obrigatorio ausente: {caminho_rel}")
    with open(caminho_rel, "r", encoding="utf-8") as f:
        rel = json.load(f)

    exigir(
        rel.get("versao_esquema_relatorio") == "1.2.2",
        f"Versao de esquema inesperada em relatorio_matriz_modo4.json: {rel.get('versao_esquema_relatorio')!r}",
    )

    meta = rel["metadados_execucao"]
    sha_relatorio = calcular_sha256_arquivo(caminho_rel)

    if assinar and exigir_assinatura:
        exigir(
            bool(caminho_log_task) and os.path.isfile(caminho_log_task),
            f"Log finalizado obrigatorio para assinatura definitiva nao encontrado: {caminho_log_task!r}",
        )

    sha_log = (
        calcular_sha256_arquivo(caminho_log_task)
        if caminho_log_task and os.path.isfile(caminho_log_task)
        else None
    )

    arquivos_evidencia = {}
    modulos_completos = {
        "api.py": os.path.join(BASE_DIR, "api.py"),
        "chave_publica_modo4.pem": os.path.join(BASE_DIR, "chave_publica_modo4.pem"),
        "dados_brutos_90_saldos_consolidados.json": os.path.join(
            BASE_DIR, "dados_brutos_90_saldos_consolidados.json"
        ),
        "data/lotomania.json": os.path.join(BASE_DIR, "data", "lotomania.json"),
        "demonstracao_invariancia_argmin.py": os.path.join(
            BASE_DIR, "demonstracao_invariancia_argmin.py"
        ),
        "gerar_manifesto_evidencia_execucao.py": os.path.abspath(__file__),
        "js/engines/motor_lotomania_modo4_engine.js": os.path.join(
            BASE_DIR, "js", "engines", "motor_lotomania_modo4_engine.js"
        ),
        "manifesto_modo4.json": os.path.join(BASE_DIR, "manifesto_modo4.json"),
        "manifesto_modo4.sig": os.path.join(BASE_DIR, "manifesto_modo4.sig"),
        "motor_lotomania.py": os.path.join(BASE_DIR, "motor_lotomania.py"),
        "motor_lotomania_modo4.py": os.path.join(BASE_DIR, "motor_lotomania_modo4.py"),
        "procedimento_homologacao_integral.py": os.path.join(
            BASE_DIR, "procedimento_homologacao_integral.py"
        ),
        "test_motor_lotomania.py": os.path.join(BASE_DIR, "test_motor_lotomania.py"),
        "test_motor_lotomania_evolution.py": os.path.join(
            BASE_DIR, "test_motor_lotomania_evolution.py"
        ),
        "test_validacao_matematica_rwin.py": os.path.join(
            BASE_DIR, "test_validacao_matematica_rwin.py"
        ),
        "teste_sensibilidade_pesos.py": os.path.join(
            BASE_DIR, "teste_sensibilidade_pesos.py"
        ),
        "testes/test_modo4_equivalencia.py": os.path.join(
            BASE_DIR, "testes", "test_modo4_equivalencia.py"
        ),
        "testes/test_modo4_matriz_carteiras.py": os.path.join(
            BASE_DIR, "testes", "test_modo4_matriz_carteiras.py"
        ),
        "testes/test_modo4_selo.py": os.path.join(
            BASE_DIR, "testes", "test_modo4_selo.py"
        ),
        "testes/test_modo4_sem_fallback.py": os.path.join(
            BASE_DIR, "testes", "test_modo4_sem_fallback.py"
        ),
        "verificador_selo_modo4.py": os.path.join(BASE_DIR, "verificador_selo_modo4.py"),
        "verificar_evidencia_independente.py": os.path.join(
            BASE_DIR, "verificar_evidencia_independente.py"
        ),
    }
    for chave_m, cam_m in modulos_completos.items():
        exigir(os.path.isfile(cam_m), f"Modulo obrigatorio do inventario ausente em disco: {chave_m}")
        arquivos_evidencia[chave_m] = calcular_sha256_arquivo(cam_m)

    # Garante consistencia absoluta contra hashes gravados dentro do relatorio de execucao
    for chave_rel, sha_rel_item in meta.get("hashes_sha256_codigo_fonte", {}).items():
        exigir(
            chave_rel in arquivos_evidencia and arquivos_evidencia[chave_rel] == sha_rel_item,
            f"Hash registrado no relatorio diverge do disco para '{chave_rel}'!",
        )

    cam_pub = os.path.join(BASE_DIR, "chave_publica_modo4.pem")
    sha_pub = calcular_sha256_arquivo(cam_pub)
    exigir(
        sha_pub.lower() == CHAVE_PUBLICA_OFICIAL_SHA256.lower(),
        "Chave publica nao corresponde ao SHA-256 confiavel fixado!",
    )

    manifesto_evidencia = {
        "identificacao_oficial": IDENTIFICACAO_OFICIAL_MODO4,
        "clausula_obrigatoria": CLAUSULA_OBRIGATORIA_MODO4,
        "versao_motor": "1.2",
        "versao_esquema_relatorio": rel["versao_esquema_relatorio"],
        "execucao_id": meta["execucao_id"],
        "timestamp_inicio_execucao_utc": meta["timestamp_inicio_utc"],
        "timestamp_fim_execucao_utc": meta["timestamp_fim_utc"],
        "timestamp_assinatura_manifesto_utc": datetime.now(timezone.utc).isoformat() if assinar else None,
        "duracao_total_bateria_s": meta["duracao_total_bateria_s"],
        "python_version": meta["python_version"],
        "plataforma": meta["plataforma"],
        "gerado_em_diretorio_temporario": meta["gerado_em_diretorio_temporario"],
        "caminho_saida_relatorio_temporario": meta["caminho_saida_relatorio"],
        "seed_utilizada": rel["seed_padrao"],
        "tamanhos_testados": rel["tamanhos_testados"],
        "tamanhos_comparacao_integral_direta_referencia": rel[
            "tamanhos_comparacao_integral_direta_referencia"
        ],
        "total_avaliacoes_swar_vs_set_intersection": rel[
            "comparacao_bitmask_histograma_referencia"
        ]["total_combinado_avaliacoes_swar_vs_set_intersection"],
        "parametros_homologados": PARAMETROS_HOMOLOGADOS_V1_2,
        "chave_publica_confiavel_sha256_fixado": CHAVE_PUBLICA_OFICIAL_SHA256,
        "sha256_relatorio_matriz_modo4_json": sha_relatorio,
        "sha256_log_execucao_finalizado": sha_log,
        "arquivo_log_execucao": os.path.basename(caminho_log_task) if caminho_log_task else None,
        "hashes_sha256_arquivos_fonte": arquivos_evidencia,
        "algoritmo_assinatura": "Ed25519",
        "algoritmo_hash": "SHA-256",
    }

    cam_man_ev = os.path.join(BASE_DIR, "manifesto_evidencia_execucao_modo4.json")
    with open(cam_man_ev, "w", encoding="utf-8") as f:
        json.dump(manifesto_evidencia, f, indent=2, sort_keys=True, ensure_ascii=False)

    bytes_canonicos = serializar_manifesto_canonico(manifesto_evidencia)
    sha_manifesto_ev = hashlib.sha256(bytes_canonicos).hexdigest()

    assinatura_hex = None
    assinatura_verificada = False
    chave_origem_segura = None

    if assinar:
        caminhos_priv = [
            r"C:\Users\Luis Brun\B2B_chaves\modo4_ed25519.key",
            r"C:\Users\Luis Brun\.gemini\antigravity\brain\f3af3942-aca3-4c9a-a3dd-e56f90feb848\scratch\keys\modo4_ed25519.key",
        ]
        cam_priv = None
        for p in caminhos_priv:
            try:
                if os.path.isfile(p):
                    cam_priv = p
                    break
            except OSError:
                continue

        if exigir_assinatura:
            exigir(
                cam_priv is not None,
                "Chave privada oficial Ed25519 inacessivel para assinatura definitiva (nenhum fallback permitido).",
            )

        if cam_priv and os.path.isfile(cam_pub):
            # Garante que nenhuma chave privada reside dentro de BASE_DIR do pacote
            exigir(
                not os.path.abspath(cam_priv).lower().startswith(os.path.abspath(BASE_DIR).lower()),
                "Violacao de seguranca: chave privada localizada dentro do diretorio distribuivel!",
            )
            _st_priv = os.stat(cam_priv)
            chave_origem_segura = os.path.basename(cam_priv) if stat.S_ISREG(_st_priv.st_mode) else None
            exigir(chave_origem_segura is not None, "Caminho da chave privada nao e arquivo regular.")

            with open(cam_priv, "rb") as fp:
                priv_bytes = fp.read()
            priv_key = serialization.load_pem_private_key(priv_bytes, password=None)
            del priv_bytes
            exigir(isinstance(priv_key, Ed25519PrivateKey), "Chave carregada nao e Ed25519PrivateKey valida.")

            # Verifica paridade criptografica estrita contra a chave publica oficial fixada
            pub_derivada_pem = priv_key.public_key().public_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PublicFormat.SubjectPublicKeyInfo,
            )
            sha_pub_derivada = hashlib.sha256(pub_derivada_pem).hexdigest()
            exigir(
                sha_pub_derivada.lower() == CHAVE_PUBLICA_OFICIAL_SHA256.lower(),
                "Chave privada localizada NAO corresponde matematicamente a chave publica oficial fixada!",
            )

            sig_bytes = priv_key.sign(bytes_canonicos)
            assinatura_hex = sig_bytes.hex()

            cam_sig_ev = os.path.join(BASE_DIR, "manifesto_evidencia_execucao_modo4.sig")
            with open(cam_sig_ev, "w", encoding="utf-8") as fs:
                fs.write(assinatura_hex + "\n")

            with open(cam_pub, "rb") as fpub:
                pub_key = serialization.load_pem_public_key(fpub.read())
            exigir(isinstance(pub_key, Ed25519PublicKey), "Chave publica carregada nao e Ed25519PublicKey.")
            pub_key.verify(bytes.fromhex(assinatura_hex), bytes_canonicos)
            assinatura_verificada = True

    return {
        "sucesso": True,
        "status_assinatura": "ASSINADO_POS_LOG" if assinatura_verificada else "PRELIMINAR_SEM_ASSINATURA",
        "execucao_id": meta["execucao_id"],
        "versao_esquema_relatorio": rel["versao_esquema_relatorio"],
        "chave_publica_confiavel_sha256_fixado": CHAVE_PUBLICA_OFICIAL_SHA256,
        "total_arquivos_fonte_inventariados": len(arquivos_evidencia),
        "sha256_relatorio_matriz_modo4_json": sha_relatorio,
        "sha256_log_execucao_finalizado": sha_log,
        "sha256_manifesto_evidencia_canonico": sha_manifesto_ev,
        "assinatura_ed25519_hex": assinatura_hex,
        "assinatura_ed25519_verificada_contra_chave_publica": assinatura_verificada,
    }


if __name__ == "__main__":
    if len(sys.argv) < 2:
        raise RuntimeError(
            "Uso obrigatorio: python gerar_manifesto_evidencia_execucao.py <caminho_log_finalizado>"
        )
    res = gerar_e_assinar_manifesto_evidencia(sys.argv[1], assinar=True, exigir_assinatura=True)
    print(json.dumps(res, indent=2, ensure_ascii=False))
