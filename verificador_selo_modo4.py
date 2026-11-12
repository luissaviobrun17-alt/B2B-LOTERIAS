# -*- coding: utf-8 -*-
"""
VERIFICADOR CRIPTOGRAFICO ISOLADO — LOTOMANIA MODO 4 (v1.2)
===========================================================
Componente confiavel de inicializacao responsavel por verificar:
1. A existencia e integridade do manifesto externo (manifesto_modo4.json).
2. A assinatura digital Ed25519 (manifesto_modo4.sig) contra a chave publica oficial.
3. Os hashes SHA-256 completos (64 caracteres hex) de:
   - motor_lotomania_modo4.py (nucleo matematico v1.2)
   - verificador_selo_modo4.py (este verificador)
   - data/lotomania.json (base historica de referencia com corte fixo no concurso 2699)
4. A imutabilidade de todos os parametros matematicos homologados da versao 1.2.

Este componente e executado ANTES do carregamento do nucleo MODO 4 e jamais
possui acesso a chave privada ou capacidade de auto-assinatura.
"""

import hashlib
import json
import os
from typing import Dict, Any, Optional

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey


IDENTIFICACAO_OFICIAL_MODO4 = (
    "OTIMIZADOR COMBINATÓRIO DE DISPERSÃO E COBERTURA CONJUNTA — LOTOMANIA | MODO 4 — v1.2"
)

CLAUSULA_OBRIGATORIA_MODO4 = (
    "O sistema não prevê resultados futuros nem altera a probabilidade matemática "
    "individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição "
    "combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre "
    "eventos premiados e melhorar a cobertura conjunta observada."
)

CHAVE_PUBLICA_OFICIAL_SHA256 = (
    "d810ed9f31f476b159590cd2e053632dc32e8e6e62a5a17f7c2f371a45084b0f"
)

# Parametros matematicos e operacionais imutaveis da versao v1.2 homologada
PARAMETROS_HOMOLOGADOS_V1_2: Dict[str, Any] = {
    "versao": "1.2",
    "identificacao_oficial": IDENTIFICACAO_OFICIAL_MODO4,
    "universo_total": 100,
    "dezenas_por_bilhete": 50,
    "dezenas_sorteadas": 20,
    "quintis_tamanho": 20,
    "dezenas_por_quintil": 10,
    "max_consecutivos": 4,
    "colunas_min": 2,
    "colunas_max": 7,
    "historico_geracao": None,
    "filtro_repeticao_ultimo_concurso_ativo": False,
    "candidatos_por_etapa": 80,
    "max_tentativas_candidatos_etapa": 500,
    "max_tentativas_amostragem_jogo": 2000,
    "peso_inter": 30.0,
    "peso_uso": 0.05,
    "escala_rwin": 10000000000000000,
    "escala_inteira": 500000000000000,
    "razao_penalidade": 600,
    "limiar_intersecao_penalidade": 25,
    "limite_min_jogos": 1,
    "limite_max_jogos": 10000,
    "corte_historico_concurso": 2699,
    "total_concursos_referencia": 2699,
    "sha256_pacote_auditoria_referencia": (
        "14e108169fe0b22c7326f540289e2573c7d43ed9134d04757748c76d47e3d857"
    ),
    "sha256_motor_referencia_original": (
        "085d6fa972dfb97576246f26b8687fce35b7dc9199bb30fca61cc348df851d6c"
    ),
    "sha256_base_historica_corte_2699": (
        "3f11b71e15b936940c8cef40cf39c0a67f5c47f7a15b12a8c2608763ec39f873"
    ),
}


class IntegridadeModo4Error(RuntimeError):
    """Excecao lancada quando qualquer verificacao criptografica ou de parametro falha."""


def calcular_sha256_arquivo(caminho: str) -> str:
    """Calcula o hash SHA-256 hexadecimal completo (64 caracteres) de um arquivo."""
    if not os.path.isfile(caminho):
        raise IntegridadeModo4Error(f"Arquivo obrigatorio ausente para verificacao de selo: {caminho}")
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def serializar_manifesto_canonico(dados_manifesto: Dict[str, Any]) -> bytes:
    """Serializa o dicionario do manifesto de forma canonica deterministica (UTF-8)."""
    return json.dumps(
        dados_manifesto,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def verificar_selo_modo4(
    diretorio_base: Optional[str] = None,
    parametros_runtime: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Executa a verificacao criptografica completa (fail-closed) antes de autorizar
    o carregamento ou a execucao do motor MODO 4 v1.2.
    """
    base_dir = diretorio_base or os.path.dirname(os.path.abspath(__file__))

    caminho_manifesto = os.path.join(base_dir, "manifesto_modo4.json")
    caminho_assinatura = os.path.join(base_dir, "manifesto_modo4.sig")
    caminho_chave_pub = os.path.join(base_dir, "chave_publica_modo4.pem")

    for caminho, nome in (
        (caminho_manifesto, "manifesto_modo4.json"),
        (caminho_assinatura, "manifesto_modo4.sig"),
        (caminho_chave_pub, "chave_publica_modo4.pem"),
    ):
        if not os.path.isfile(caminho):
            raise IntegridadeModo4Error(
                f"Falha de selamento criptografico: artefato obrigatorio '{nome}' nao encontrado."
            )

    try:
        with open(caminho_manifesto, "r", encoding="utf-8") as f_man:
            manifesto = json.load(f_man)
    except Exception as exc:
        raise IntegridadeModo4Error(f"Falha ao ler manifesto_modo4.json: {exc}") from exc

    if not isinstance(manifesto, dict):
        raise IntegridadeModo4Error("Formato invalido em manifesto_modo4.json.")

    try:
        with open(caminho_assinatura, "rb") as f_sig:
            assinatura_hex = f_sig.read().strip().decode("ascii")
            assinatura_bytes = bytes.fromhex(assinatura_hex)
    except Exception as exc:
        raise IntegridadeModo4Error(f"Assinatura manifesto_modo4.sig corrompida ou invalida: {exc}") from exc

    try:
        with open(caminho_chave_pub, "rb") as f_pub:
            pem_bytes = f_pub.read()
        sha_pub_atual = hashlib.sha256(pem_bytes).hexdigest()
        if sha_pub_atual.lower() != CHAVE_PUBLICA_OFICIAL_SHA256.lower():
            raise IntegridadeModo4Error(
                "Chave publica chave_publica_modo4.pem diverge da chave publica oficial homologada."
            )
        chave_publica = serialization.load_pem_public_key(pem_bytes)
        if not isinstance(chave_publica, Ed25519PublicKey):
            raise IntegridadeModo4Error("A chave publica carregada nao e uma chave Ed25519 valida.")
    except IntegridadeModo4Error:
        raise
    except Exception as exc:
        raise IntegridadeModo4Error(f"Erro ao carregar chave_publica_modo4.pem: {exc}") from exc

    # 1. Verificacao da assinatura digital Ed25519 sobre a serializacao canonica do manifesto
    bytes_canonicos = serializar_manifesto_canonico(manifesto)
    try:
        chave_publica.verify(assinatura_bytes, bytes_canonicos)
    except InvalidSignature as exc:
        raise IntegridadeModo4Error(
            "Assinatura digital Ed25519 INVALIDA para manifesto_modo4.json. Execucao bloqueada."
        ) from exc

    # 2. Verificacao da versao e dos parametros matematicos congelados no manifesto
    if manifesto.get("versao") != "1.2":
        raise IntegridadeModo4Error(
            f"Versao do manifesto ({manifesto.get('versao')}) diverge da versao homologada (1.2)."
        )

    parametros_manifesto = manifesto.get("parametros_homologados")
    if not isinstance(parametros_manifesto, dict):
        raise IntegridadeModo4Error("Secao 'parametros_homologados' ausente no manifesto.")

    for chave_p, valor_esperado in PARAMETROS_HOMOLOGADOS_V1_2.items():
        if chave_p not in parametros_manifesto:
            raise IntegridadeModo4Error(f"Parametro obrigatorio '{chave_p}' ausente no manifesto.")
        valor_man = parametros_manifesto[chave_p]
        if valor_man != valor_esperado or type(valor_man) is not type(valor_esperado):
            raise IntegridadeModo4Error(
                f"Violacao de parametro homologado '{chave_p}': manifesto={valor_man!r}, "
                f"esperado={valor_esperado!r}."
            )

    if parametros_runtime is not None:
        for chave_p, valor_esperado in PARAMETROS_HOMOLOGADOS_V1_2.items():
            if chave_p not in parametros_runtime:
                raise IntegridadeModo4Error(
                    f"Parametro '{chave_p}' ausente nos parametros em tempo de execucao do motor."
                )
            valor_rt = parametros_runtime[chave_p]
            if valor_rt != valor_esperado or type(valor_rt) is not type(valor_esperado):
                raise IntegridadeModo4Error(
                    f"Adulteracao detectada em tempo de execucao no parametro '{chave_p}': "
                    f"runtime={valor_rt!r}, homologado={valor_esperado!r}."
                )

    # 3. Verificacao dos hashes SHA-256 dos arquivos monitorados
    arquivos_manifesto = manifesto.get("arquivos_protegidos")
    if not isinstance(arquivos_manifesto, dict):
        raise IntegridadeModo4Error("Secao 'arquivos_protegidos' ausente no manifesto.")

    arquivos_obrigatorios = (
        "motor_lotomania_modo4.py",
        "verificador_selo_modo4.py",
        "chave_publica_modo4.pem",
        "data/lotomania.json",
    )
    hashes_verificados: Dict[str, str] = {}

    for rel_path in arquivos_obrigatorios:
        if rel_path not in arquivos_manifesto:
            raise IntegridadeModo4Error(
                f"Arquivo obrigatorio '{rel_path}' nao consta em 'arquivos_protegidos' do manifesto."
            )
        hash_esperado = arquivos_manifesto[rel_path]
        caminho_abs = os.path.join(base_dir, *rel_path.split("/"))
        hash_atual = calcular_sha256_arquivo(caminho_abs)
        if hash_atual.lower() != str(hash_esperado).lower():
            raise IntegridadeModo4Error(
                f"Violacao de integridade SHA-256 em '{rel_path}': "
                f"calculado={hash_atual}, manifesto={hash_esperado}."
            )
        hashes_verificados[rel_path] = hash_atual

    # 4. Garantia explicita de que a base historica corresponde ao corte fixo 2699 homologado
    hash_base_esperado = PARAMETROS_HOMOLOGADOS_V1_2["sha256_base_historica_corte_2699"]
    if hashes_verificados["data/lotomania.json"].lower() != hash_base_esperado.lower():
        raise IntegridadeModo4Error(
            "O arquivo data/lotomania.json diverge do hash SHA-256 da base de referencia com corte fixo no concurso 2699."
        )

    hash_manifesto = hashlib.sha256(bytes_canonicos).hexdigest()

    return {
        "selo_valido": True,
        "algoritmo_assinatura": "Ed25519",
        "versao_motor": "1.2",
        "identificacao_oficial": IDENTIFICACAO_OFICIAL_MODO4,
        "corte_historico_concurso": 2699,
        "historico_geracao": None,
        "sha256_manifesto": hash_manifesto,
        "arquivos_verificados": hashes_verificados,
    }
