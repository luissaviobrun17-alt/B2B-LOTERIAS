# -*- coding: utf-8 -*-
"""
Compilador e publicador offline atomico do catalogo imutavel `CATALOGO_LOTOMANIA_10000`.

Responsabilidades:
1. Carregar exclusivamente chave privada Ed25519 externa ao repositorio
   (recusando qualquer caminho dentro do repo, CATALOGO, staging, auditoria
   ou reutilizacao de `modo4_ed25519.key`).
2. Revalidar integralmente todas as travas R1-R12 e os 4 hashes certificados de
   cada carteira candidata antes de emitir particao binaria `uint8[J][50]`.
3. Construir `indice_catalogo.sqlite` com `PRAGMA journal_mode=DELETE` e fecha-lo
   com zero arquivos auxiliares `-wal`/`-shm`/`-journal`.
4. Emitir `manifesto_catalogo.json` em JCS canonico estrito (RFC 8785, zero floats),
   assina-lo com Ed25519 em `manifesto_catalogo.sig` e registrar recibo terminal
   operacional `CONCLUSAO_PUBLICACAO.json` vinculado para tras.
5. Executar publicacao em `_staging` no mesmo sistema de arquivos, revalidar antes
   da promocao, aplicar permissao somente-leitura, promover por `os.replace`
   para `releases/<versao>` (recusando sobrescrita de versao existente) e atualizar
   `catalogo_ativo.json` via arquivo temporario + fsync + `os.replace`.

Zero instrucoes `assert`.
"""

from datetime import datetime, timezone
import hashlib
import json
import os
import shutil
import sqlite3
import stat
import subprocess
from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple
import uuid

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import (
    Ed25519PrivateKey,
    Ed25519PublicKey,
)

from catalogo_lotomania_10000.canonicalizacao import (
    CONFIGURACAO_PADRAO_S1_1080K,
    ESQUEMA_CATALOGO_VERSAO,
    VERSAO_ALGORITMO_PADRAO,
    calcular_sha256_configuracao,
    exigir,
    montar_id_carteira,
    serializar_jcs_canonico,
)
from catalogo_lotomania_10000.crypto_selo import (
    CHAVE_PUBLICA_CATALOGO_SHA256,
    CatalogoIndisponivelError,
    IntegridadeCatalogoError,
    calcular_sha256_arquivo_streaming,
    resolver_caminho_seguro_em_diretorio,
    validar_sha256_hex,
    validar_versao_catalogo_str,
    verificar_integridade_abertura_versao,
)
from catalogo_lotomania_10000.leitor import (
    CAMINHO_CHAVE_PUBLICA_PADRAO,
    DIR_CATALOGO_PADRAO,
)

_REPOSITORIO_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CAMINHO_CHAVE_PRIVADA_PADRAO = os.path.join(
    os.path.expanduser("~"), "B2B_chaves", "catalogo_lotomania_10000_ed25519.key"
)
CAMINHO_CHAVE_MODO4_PROIBIDA = os.path.join(
    os.path.expanduser("~"), "B2B_chaves", "modo4_ed25519.key"
)

FALHAS_INJETAVEIS_VALIDAS = frozenset(
    {
        "pos_staging",
        "pre_rename_release",
        "pos_rename_release_pre_ponteiro",
        "durante_ponteiro_tmp",
    }
)


class FalhaInjetadaPublicacaoError(RuntimeError):
    """Excecao deterministica usada para simular queda de energia/processo em testes."""


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _fsync_arquivo(caminho: str) -> None:
    try:
        with open(caminho, "rb") as fh:
            os.fsync(fh.fileno())
    except OSError:
        # Alguns descritores somente-leitura no Windows recusam FlushFileBuffers;
        # a gravacao principal ja executou flush + fsync antes de fechar o descritor de escrita.
        return


def _fsync_diretorio_seguro(caminho_dir: str) -> None:
    flags = getattr(os, "O_RDONLY", 0)
    try:
        fd = os.open(caminho_dir, flags)
    except OSError:
        return
    try:
        os.fsync(fd)
    except OSError:
        pass
    finally:
        os.close(fd)


def _atomic_write_bytes(caminho_destino: str, dados: bytes) -> None:
    pasta_pai = os.path.dirname(os.path.abspath(caminho_destino))
    os.makedirs(pasta_pai, exist_ok=True)
    nome_tmp = f".{os.path.basename(caminho_destino)}.tmp.{os.getpid()}.{uuid.uuid4().hex[:8]}"
    caminho_tmp = os.path.join(pasta_pai, nome_tmp)
    with open(caminho_tmp, "wb") as fh:
        fh.write(dados)
        fh.flush()
        os.fsync(fh.fileno())
    os.replace(caminho_tmp, caminho_destino)
    _fsync_diretorio_seguro(pasta_pai)


def _aplicar_somente_leitura_recursivo(dir_alvo: str) -> None:
    for raiz, _, arquivos in os.walk(dir_alvo):
        for arq in arquivos:
            caminho_arq = os.path.join(raiz, arq)
            os.chmod(caminho_arq, stat.S_IREAD | stat.S_IRGRP | stat.S_IROTH)


def _remover_arvore_segura(dir_alvo: str) -> None:
    if not os.path.exists(dir_alvo):
        return
    for raiz, dirs, arquivos in os.walk(dir_alvo):
        for arq in arquivos:
            p = os.path.join(raiz, arq)
            try:
                os.chmod(p, stat.S_IWRITE | stat.S_IREAD)
            except OSError:
                pass
        for d in dirs:
            p = os.path.join(raiz, d)
            try:
                os.chmod(p, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
            except OSError:
                pass
    try:
        os.chmod(dir_alvo, stat.S_IWRITE | stat.S_IREAD | stat.S_IEXEC)
    except OSError:
        pass
    shutil.rmtree(dir_alvo)


def _esta_dentro_de(caminho_filho: str, caminho_pai: str) -> bool:
    filho = os.path.normcase(os.path.realpath(caminho_filho))
    pai = os.path.normcase(os.path.realpath(caminho_pai))
    return filho == pai or filho.startswith(pai + os.sep)


def _validar_caminho_chave_privada_externo(
    caminho_chave_privada: str,
    dir_catalogo: str,
) -> str:
    if type(caminho_chave_privada) is not str or not caminho_chave_privada.strip():
        raise IntegridadeCatalogoError("Caminho da chave privada do catalogo vazio ou invalido.")
    if os.path.islink(caminho_chave_privada):
        raise IntegridadeCatalogoError(
            f"Link simbolico proibido para chave privada: '{caminho_chave_privada}'."
        )
    caminho_abs = os.path.realpath(caminho_chave_privada)

    if os.path.basename(caminho_abs).lower() == "modo4_ed25519.key":
        raise IntegridadeCatalogoError(
            "Proibido reutilizar a chave privada do selo MODO 4 (`modo4_ed25519.key`) no catalogo."
        )
    if os.path.normcase(caminho_abs) == os.path.normcase(
        os.path.realpath(CAMINHO_CHAVE_MODO4_PROIBIDA)
    ):
        raise IntegridadeCatalogoError(
            "Chave privada do catalogo nao pode apontar para a chave do MODO 4."
        )

    locais_proibidos = [
        _REPOSITORIO_RAIZ,
        dir_catalogo,
        os.path.join(dir_catalogo, "_staging"),
        os.path.join(_REPOSITORIO_RAIZ, "auditoria"),
    ]
    for proibido in locais_proibidos:
        if _esta_dentro_de(caminho_abs, proibido):
            raise IntegridadeCatalogoError(
                f"Chave privada Ed25519 deve residir fora do repositorio e do catalogo: '{caminho_abs}'."
            )
    return caminho_abs


def exportar_chave_publica_spki_pem(chave_privada: Ed25519PrivateKey) -> Tuple[bytes, str]:
    pub_bytes = chave_privada.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )
    sha_pub = hashlib.sha256(pub_bytes).hexdigest()
    return pub_bytes, sha_pub


def gerar_par_chaves_catalogo_teste(
    caminho_privada: str,
    caminho_publica: str,
    *,
    dir_catalogo: str = DIR_CATALOGO_PADRAO,
) -> Tuple[str, str]:
    """
    Gera par Ed25519 dedicado (exclusivo para ambientes de teste isolados fora do repo).
    Retorna `(caminho_privada_abs, sha256_chave_publica_pem)`.
    """
    priv_abs = _validar_caminho_chave_privada_externo(caminho_privada, dir_catalogo)
    priv = Ed25519PrivateKey.generate()
    priv_pem = priv.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    pub_pem, sha_pub = exportar_chave_publica_spki_pem(priv)

    os.makedirs(os.path.dirname(priv_abs), exist_ok=True)
    _atomic_write_bytes(priv_abs, priv_pem)
    try:
        os.chmod(priv_abs, stat.S_IREAD | stat.S_IWRITE)
    except OSError:
        pass
    os.makedirs(os.path.dirname(os.path.abspath(caminho_publica)), exist_ok=True)
    _atomic_write_bytes(caminho_publica, pub_pem)
    return priv_abs, sha_pub


def carregar_chave_privada_catalogo(
    caminho_chave_privada: str = CAMINHO_CHAVE_PRIVADA_PADRAO,
    *,
    dir_catalogo: str = DIR_CATALOGO_PADRAO,
    caminho_chave_publica: Optional[str] = None,
    ancora_sha256_esperada: str = CHAVE_PUBLICA_CATALOGO_SHA256,
) -> Tuple[Ed25519PrivateKey, bytes, str]:
    """
    Carrega chave privada Ed25519 externa ao repositorio e valida sua derivacao
    contra a chave publica esperada e ancora SHA-256.
    """
    priv_abs = _validar_caminho_chave_privada_externo(caminho_chave_privada, dir_catalogo)
    if not os.path.isfile(priv_abs):
        raise IntegridadeCatalogoError(
            f"Chave privada externa do catalogo ausente: '{priv_abs}'."
        )

    with open(priv_abs, "rb") as fh:
        priv_bytes = fh.read()
    try:
        priv = serialization.load_pem_private_key(priv_bytes, password=None)
    except Exception as exc:
        raise IntegridadeCatalogoError(
            f"Falha ao carregar chave privada Ed25519 em '{priv_abs}': {exc}"
        ) from exc
    if not isinstance(priv, Ed25519PrivateKey):
        raise IntegridadeCatalogoError("Chave carregada nao e Ed25519PrivateKey valida.")

    pub_bytes, sha_pub_derivada = exportar_chave_publica_spki_pem(priv)
    ancora = validar_sha256_hex(ancora_sha256_esperada, "ancora_sha256_esperada")
    if sha_pub_derivada != ancora:
        raise IntegridadeCatalogoError(
            "Chave privada nao corresponde a ancora SHA-256 confiavel da chave publica do catalogo "
            f"(derivada={sha_pub_derivada}, ancora={ancora})."
        )

    if caminho_chave_publica is not None and os.path.isfile(caminho_chave_publica):
        with open(caminho_chave_publica, "rb") as fh_pub:
            pub_disco = fh_pub.read()
        if pub_disco != pub_bytes or hashlib.sha256(pub_disco).hexdigest() != ancora:
            raise IntegridadeCatalogoError(
                f"Chave publica em '{caminho_chave_publica}' diverge da chave privada externa."
            )
    elif caminho_chave_publica is not None:
        _atomic_write_bytes(caminho_chave_publica, pub_bytes)

    return priv, pub_bytes, sha_pub_derivada


def _carregar_jogos_e_hashes_entrada(
    spec: Mapping[str, Any],
) -> Dict[str, Any]:
    from lotomania_carteira_10000.auditoria import auditar_carteira_completa
    from lotomania_carteira_10000.validacao import (
        BASELINE_ORDEM4_10000_REFERENCIA,
        calcular_hashes_certificados,
    )

    dados_json_carteira: Optional[Dict[str, Any]] = None
    sha_arq_carteira: Optional[str] = None
    if "caminho_json_carteira" in spec and spec["caminho_json_carteira"] is not None:
        caminho_json = os.path.abspath(spec["caminho_json_carteira"])
        sha_arq_carteira, _, _ = calcular_sha256_arquivo_streaming(caminho_json)
        with open(caminho_json, "r", encoding="utf-8") as fh:
            bruto = json.load(fh)
        if isinstance(bruto, dict) and "jogos" in bruto:
            dados_json_carteira = bruto
            jogos = bruto["jogos"]
        elif isinstance(bruto, list):
            jogos = bruto
        else:
            raise IntegridadeCatalogoError(
                f"Formato invalido de JSON de carteira em '{caminho_json}'."
            )
    elif "jogos" in spec and spec["jogos"] is not None:
        jogos = spec["jogos"]
    else:
        raise ValueError("Cada entrada de publicacao exige 'caminho_json_carteira' ou 'jogos'.")

    if not isinstance(jogos, list) or not jogos:
        raise IntegridadeCatalogoError("Lista 'jogos' vazia ou invalida na entrada de publicacao.")

    J = spec.get("J", len(jogos))
    if type(J) is not int or J != len(jogos) or J < 2 or J > 10000 or J % 2 != 0:
        raise IntegridadeCatalogoError(f"J invalido na entrada de publicacao: {J!r} (len={len(jogos)}).")
    if dados_json_carteira is not None and "J" in dados_json_carteira:
        exigir(
            dados_json_carteira["J"] == J,
            "J diverge do metadado interno do JSON da carteira.",
            IntegridadeCatalogoError,
        )

    seed = spec.get("seed")
    if seed is None and dados_json_carteira is not None:
        seed = dados_json_carteira.get("seed")
    if type(seed) is not int:
        raise IntegridadeCatalogoError(f"seed invalida ou ausente na entrada: {seed!r}.")
    if dados_json_carteira is not None and "seed" in dados_json_carteira:
        exigir(
            dados_json_carteira["seed"] == seed,
            "seed diverge do metadado interno do JSON da carteira.",
            IntegridadeCatalogoError,
        )

    versao_alg = spec.get("versao_algoritmo")
    if versao_alg is None and dados_json_carteira is not None:
        versao_alg = dados_json_carteira.get("versao_algoritmo", VERSAO_ALGORITMO_PADRAO)
    if versao_alg is None:
        versao_alg = VERSAO_ALGORITMO_PADRAO
    exigir(
        type(versao_alg) is str and len(versao_alg) > 0,
        f"versao_algoritmo invalida: {versao_alg!r}.",
        IntegridadeCatalogoError,
    )

    cfg_bruta = spec.get("configuracao", CONFIGURACAO_PADRAO_S1_1080K)
    cfg_canonica, _, sha_cfg = calcular_sha256_configuracao(cfg_bruta)

    hashes = calcular_hashes_certificados(
        jogos,
        seed=seed,
        J=J,
        max_tentativas_f3=cfg_canonica["max_tentativas_f3"],
        versao_algoritmo=versao_alg,
    )

    if dados_json_carteira is not None:
        for campo_h in (
            "hash_carteira_sha256_v1",
            "hash_carteira_sha256_v2_canonico",
            "sha256_estado_canonico",
            "sha256_matriz_incidencia_100",
        ):
            if campo_h in dados_json_carteira:
                exigir(
                    dados_json_carteira[campo_h] == hashes[campo_h],
                    f"Hash certificado '{campo_h}' no JSON diverge do calculado.",
                    IntegridadeCatalogoError,
                )

    aud = auditar_carteira_completa(
        jogos,
        teto_kmax=35,
        baseline_ordem4=BASELINE_ORDEM4_10000_REFERENCIA if J == 10000 else None,
    )
    exigir(
        aud["aprovacao_restricoes"]["todas_travas_aprovadas"] is True,
        f"Carteira reprovada na auditoria R1-R12 antes da publicacao: {aud['aprovacao_restricoes']}.",
        IntegridadeCatalogoError,
    )

    # Compactacao binaria canonica uint8[J][50] em ordem de bilhete e dezena crescente.
    estado_bytes = bytes(n for jg in jogos for n in jg)
    exigir(
        len(estado_bytes) == 50 * J,
        f"Buffer binario uint8[{J}][50] com tamanho inesperado ({len(estado_bytes)}).",
        IntegridadeCatalogoError,
    )
    sha_estado_bin = hashlib.sha256(estado_bytes).hexdigest()
    exigir(
        sha_estado_bin == hashes["sha256_estado_canonico"],
        "Buffer binario diverge de sha256_estado_canonico.",
        IntegridadeCatalogoError,
    )

    id_carteira = montar_id_carteira(
        J=J, seed=seed, versao_algoritmo=versao_alg, sha256_configuracao=sha_cfg
    )
    particao_relpath = f"particoes/{id_carteira}.bin"

    # Leitura opcional de benchmark e auditoria externa para proveniencia rica
    bench_info: Optional[Dict[str, Any]] = None
    sha_bench: Optional[str] = None
    if spec.get("caminho_benchmark_json"):
        p_b = os.path.abspath(spec["caminho_benchmark_json"])
        sha_bench, _, _ = calcular_sha256_arquivo_streaming(p_b)
        with open(p_b, "r", encoding="utf-8") as f_b:
            bench_info = json.load(f_b)

    sha_aud_ind: Optional[str] = None
    if spec.get("caminho_auditoria_json"):
        p_a = os.path.abspath(spec["caminho_auditoria_json"])
        sha_aud_ind, _, _ = calcular_sha256_arquivo_streaming(p_a)

    sha_trilha: Optional[str] = spec.get("sha256_trilha_jsonl")
    if not sha_trilha and spec.get("caminho_trilha_jsonl"):
        p_t = os.path.abspath(spec["caminho_trilha_jsonl"])
        if os.path.isfile(p_t):
            sha_trilha, _, _ = calcular_sha256_arquivo_streaming(p_t)
    if not sha_trilha and bench_info is not None:
        sha_trilha = bench_info.get("auditoria_restricoes", {}).get("sha256_trilha_jsonl")

    proveniencia_manifesto: Dict[str, Any] = {
        "commit_git_gerador": str(spec.get("commit_git_gerador") or "455796c7f83b4042ba531438f2bb6ac9324ed426"),
        "swaps_aceitos": int(
            bench_info["swaps_aceitos"]
            if bench_info and "swaps_aceitos" in bench_info
            else spec.get("swaps_aceitos", 0)
        ),
        "recalculos_dmax_queda": int(
            bench_info["recalculos_dmax_queda"]
            if bench_info and "recalculos_dmax_queda" in bench_info
            else spec.get("recalculos_dmax_queda", 0)
        ),
        "k_max": int(aud["fechamento"]["k_max"]),
        "phi2": int(aud["coocorrencia_4950"]["phi2"]),
        "q_global_plus": int(aud["coocorrencia_4950"]["q_global_plus"]),
        "d_max": int(aud["coocorrencia_4950"]["d_max"]),
        "P_gt_25": int(aud["fechamento"]["P_gt_25"]),
        "R_win": str(aud["fechamento"]["R_win"]),
        "u_min": int(aud["fechamento"]["u_min"]),
        "u_max": int(aud["fechamento"]["u_max"]),
        "intersecao_par_inicial": int(aud["fechamento"]["intersecao_par_inicial"]),
        "todas_travas_aprovadas": True,
    }
    if bench_info and "pre_fase3" in bench_info and "sha256_estado_inicial_fase3" in bench_info["pre_fase3"]:
        proveniencia_manifesto["sha256_estado_inicial_fase3"] = str(
            bench_info["pre_fase3"]["sha256_estado_inicial_fase3"]
        )
    if sha_arq_carteira:
        proveniencia_manifesto["sha256_arquivo_carteira"] = sha_arq_carteira
    if sha_aud_ind:
        proveniencia_manifesto["sha256_auditoria_independente"] = sha_aud_ind
    if sha_bench:
        proveniencia_manifesto["sha256_benchmark_resumo"] = sha_bench
    if sha_trilha:
        proveniencia_manifesto["sha256_trilha_jsonl"] = str(sha_trilha)
    if spec.get("proveniencia_extra"):
        for k_ex, v_ex in spec["proveniencia_extra"].items():
            if type(v_ex) is float:
                raise TypeError(f"proveniencia_extra[{k_ex!r}] nao pode ser float no manifesto JCS.")
            proveniencia_manifesto[str(k_ex)] = v_ex

    entrada_manifesto = {
        "id_carteira": id_carteira,
        "versao_algoritmo": versao_alg,
        "J": J,
        "seed": seed,
        "sha256_configuracao": sha_cfg,
        "configuracao_canonica": cfg_canonica,
        "particao_relpath": particao_relpath,
        "tamanho_bytes": len(estado_bytes),
        "sha256_estado_canonico": hashes["sha256_estado_canonico"],
        "hash_carteira_sha256_v1": hashes["hash_carteira_sha256_v1"],
        "hash_carteira_sha256_v2_canonico": hashes["hash_carteira_sha256_v2_canonico"],
        "sha256_matriz_incidencia_100": hashes["sha256_matriz_incidencia_100"],
        "proveniencia": proveniencia_manifesto,
    }

    metadados_sqlite = {
        "homologacao_kmax": aud["homologacao_kmax"],
        "fechamento": aud["fechamento"],
        "coocorrencia_4950": aud["coocorrencia_4950"],
        "cobertura_por_faixa": aud["cobertura_por_faixa"],
        "comparacao_baseline_ordem4": aud.get("comparacao_baseline_ordem4"),
        "proveniencia": proveniencia_manifesto,
        "benchmark_resumo": (
            {
                "tempo_fase12_s": bench_info.get("tempo_fase12_s"),
                "tempo_fase3_s": bench_info.get("tempo_fase3_s"),
                "tempo_total_s": bench_info.get("tempo_total_s"),
                "pre_fase3": bench_info.get("pre_fase3"),
            }
            if bench_info
            else None
        ),
    }

    return {
        "entrada_manifesto": entrada_manifesto,
        "estado_bytes": estado_bytes,
        "coocorrencia_4950": aud["coocorrencia_4950"],
        "fechamento": aud["fechamento"],
        "cobertura_por_faixa": aud["cobertura_por_faixa"],
        "metadados_sqlite": metadados_sqlite,
    }


def _construir_indice_sqlite(
    caminho_sqlite: str,
    versao_catalogo: str,
    entradas_compiladas: Sequence[Mapping[str, Any]],
) -> Tuple[str, int]:
    if os.path.exists(caminho_sqlite):
        os.remove(caminho_sqlite)

    conn = sqlite3.connect(caminho_sqlite)
    try:
        conn.execute("PRAGMA journal_mode=DELETE;")
        conn.execute("PRAGMA synchronous=FULL;")
        conn.execute(
            """
            CREATE TABLE carteiras (
                id_carteira TEXT PRIMARY KEY,
                versao_catalogo TEXT NOT NULL,
                versao_algoritmo TEXT NOT NULL,
                J INTEGER NOT NULL,
                seed INTEGER NOT NULL,
                sha256_configuracao TEXT NOT NULL,
                particao_relpath TEXT NOT NULL UNIQUE,
                tamanho_bytes INTEGER NOT NULL,
                sha256_estado_canonico TEXT NOT NULL,
                hash_carteira_sha256_v1 TEXT NOT NULL,
                hash_carteira_sha256_v2_canonico TEXT NOT NULL,
                sha256_matriz_incidencia_100 TEXT NOT NULL,
                todas_travas_aprovadas INTEGER NOT NULL,
                k_max INTEGER NOT NULL,
                phi2 INTEGER NOT NULL,
                d_max INTEGER NOT NULL,
                P_gt_25 INTEGER NOT NULL,
                R_win TEXT NOT NULL,
                sigma_intra REAL NOT NULL,
                sigma_inter REAL NOT NULL,
                metadados_completos_json TEXT NOT NULL,
                UNIQUE (versao_algoritmo, J, seed, sha256_configuracao)
            );
            """
        )
        conn.execute(
            "CREATE INDEX idx_carteiras_busca ON carteiras (J, seed, versao_algoritmo, sha256_configuracao);"
        )

        ordenadas = sorted(
            entradas_compiladas,
            key=lambda item: (
                item["entrada_manifesto"]["J"],
                item["entrada_manifesto"]["versao_algoritmo"],
                item["entrada_manifesto"]["sha256_configuracao"],
                item["entrada_manifesto"]["seed"],
                item["entrada_manifesto"]["id_carteira"],
            ),
        )
        for item in ordenadas:
            ent = item["entrada_manifesto"]
            cooc = item["coocorrencia_4950"]
            fech = item["fechamento"]
            conn.execute(
                """
                INSERT INTO carteiras (
                    id_carteira, versao_catalogo, versao_algoritmo, J, seed,
                    sha256_configuracao, particao_relpath, tamanho_bytes,
                    sha256_estado_canonico, hash_carteira_sha256_v1,
                    hash_carteira_sha256_v2_canonico, sha256_matriz_incidencia_100,
                    todas_travas_aprovadas, k_max, phi2, d_max, P_gt_25, R_win,
                    sigma_intra, sigma_inter, metadados_completos_json
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """,
                (
                    ent["id_carteira"],
                    versao_catalogo,
                    ent["versao_algoritmo"],
                    ent["J"],
                    ent["seed"],
                    ent["sha256_configuracao"],
                    ent["particao_relpath"],
                    ent["tamanho_bytes"],
                    ent["sha256_estado_canonico"],
                    ent["hash_carteira_sha256_v1"],
                    ent["hash_carteira_sha256_v2_canonico"],
                    ent["sha256_matriz_incidencia_100"],
                    1,
                    int(fech["k_max"]),
                    int(cooc["phi2"]),
                    int(cooc["d_max"]),
                    int(fech["P_gt_25"]),
                    str(fech["R_win"]),
                    float(cooc["sigma_intra"]),
                    float(cooc["sigma_inter"]),
                    json.dumps(item["metadados_sqlite"], sort_keys=True, ensure_ascii=False),
                ),
            )
        conn.commit()
        conn.execute("VACUUM;")
    finally:
        conn.close()

    for sufixo in ("-wal", "-shm", "-journal"):
        aux = caminho_sqlite + sufixo
        if os.path.exists(aux):
            raise IntegridadeCatalogoError(
                f"Arquivo auxiliar SQLite proibido residual apos fechamento: '{aux}'."
            )

    _fsync_arquivo(caminho_sqlite)
    sha_sql, tam_sql, _ = calcular_sha256_arquivo_streaming(caminho_sqlite)
    return sha_sql, tam_sql


def _atualizar_ponteiro_catalogo_ativo(
    dir_catalogo: str,
    *,
    versao_alvo: str,
    sha256_manifesto: str,
    sha256_assinatura_sig: str,
    falha_em: Optional[str] = None,
) -> Dict[str, Any]:
    ponteiro = {
        "versao_ativa": versao_alvo,
        "sha256_manifesto": sha256_manifesto,
        "sha256_assinatura_sig": sha256_assinatura_sig,
        "atualizado_em_utc": _utc_now_iso(),
    }
    dados = json.dumps(ponteiro, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8") + b"\n"
    caminho_ptr = os.path.join(dir_catalogo, "catalogo_ativo.json")
    caminho_tmp = os.path.join(
        dir_catalogo,
        f".catalogo_ativo.json.tmp.{os.getpid()}.{uuid.uuid4().hex[:8]}",
    )
    with open(caminho_tmp, "wb") as fh:
        fh.write(dados)
        fh.flush()
        os.fsync(fh.fileno())
    if falha_em == "durante_ponteiro_tmp":
        raise FalhaInjetadaPublicacaoError("Falha simulada durante escrita de catalogo_ativo.json.tmp.")
    os.replace(caminho_tmp, caminho_ptr)
    _fsync_diretorio_seguro(dir_catalogo)
    return ponteiro


def publicar_versao_catalogo(
    versao_catalogo: str,
    especificacoes_entradas: Sequence[Mapping[str, Any]],
    *,
    dir_catalogo: str = DIR_CATALOGO_PADRAO,
    caminho_chave_privada: str = CAMINHO_CHAVE_PRIVADA_PADRAO,
    caminho_chave_publica: Optional[str] = None,
    ancora_sha256: str = CHAVE_PUBLICA_CATALOGO_SHA256,
    ativar: bool = True,
    falha_em: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Compila, valida, assina e publica atomicamente uma versao imutavel `vX.Y.Z`.
    Recusa estritamente sobrescrever uma versao ja existente em `releases/`.
    """
    versao = validar_versao_catalogo_str(versao_catalogo)
    if falha_em is not None and falha_em not in FALHAS_INJETAVEIS_VALIDAS:
        raise ValueError(f"falha_em invalido: {falha_em!r}.")
    if not especificacoes_entradas:
        raise ValueError("especificacoes_entradas nao pode ser vazia.")

    dir_cat = os.path.abspath(dir_catalogo)
    os.makedirs(dir_cat, exist_ok=True)
    dir_releases = os.path.join(dir_cat, "releases")
    dir_staging_root = os.path.join(dir_cat, "_staging")
    os.makedirs(dir_releases, exist_ok=True)
    os.makedirs(dir_staging_root, exist_ok=True)

    dir_destino_release = resolver_caminho_seguro_em_diretorio(dir_releases, versao)
    if os.path.exists(dir_destino_release):
        raise IntegridadeCatalogoError(
            f"Sobrescrita proibida: a versao imutavel '{versao}' ja existe em '{dir_destino_release}'."
        )

    caminho_pub = (
        os.path.abspath(caminho_chave_publica)
        if caminho_chave_publica is not None
        else os.path.join(dir_cat, "chave_publica_catalogo.pem")
    )
    priv_key, _, sha_pub = carregar_chave_privada_catalogo(
        caminho_chave_privada,
        dir_catalogo=dir_cat,
        caminho_chave_publica=caminho_pub,
        ancora_sha256_esperada=ancora_sha256,
    )

    compiladas: List[Dict[str, Any]] = []
    for spec in especificacoes_entradas:
        compiladas.append(_carregar_jogos_e_hashes_entrada(spec))
    compiladas.sort(
        key=lambda item: (
            item["entrada_manifesto"]["J"],
            item["entrada_manifesto"]["versao_algoritmo"],
            item["entrada_manifesto"]["sha256_configuracao"],
            item["entrada_manifesto"]["seed"],
            item["entrada_manifesto"]["id_carteira"],
        )
    )

    dir_stage = os.path.join(
        dir_staging_root, f"{versao}_{os.getpid()}_{uuid.uuid4().hex[:8]}"
    )
    os.makedirs(os.path.join(dir_stage, "particoes"), exist_ok=False)

    falha_simulada = False
    try:
        for item in compiladas:
            ent = item["entrada_manifesto"]
            caminho_part_stage = resolver_caminho_seguro_em_diretorio(
                dir_stage, ent["particao_relpath"]
            )
            _atomic_write_bytes(caminho_part_stage, item["estado_bytes"])

        caminho_sqlite_stage = os.path.join(dir_stage, "indice_catalogo.sqlite")
        sha_sql, tam_sql = _construir_indice_sqlite(
            caminho_sqlite_stage, versao, compiladas
        )

        entradas_manifesto = [item["entrada_manifesto"] for item in compiladas]
        j_permitidos = sorted({ent["J"] for ent in entradas_manifesto})
        ts_utc = _utc_now_iso()

        manifesto_obj: Dict[str, Any] = {
            "esquema_versao": ESQUEMA_CATALOGO_VERSAO,
            "versao_catalogo": versao,
            "algoritmo_assinatura": "Ed25519",
            "algoritmo_hash": "SHA-256",
            "loteria": "lotomania",
            "politica_leitura": {
                "apenas_grade_exata": True,
                "rejeitar_fora_da_grade": True,
                "j_permitidos": j_permitidos,
            },
            "chave_publica_sha256_informada": sha_pub,
            "indice_sqlite": {
                "arquivo": "indice_catalogo.sqlite",
                "tamanho_bytes": tam_sql,
                "sha256": sha_sql,
            },
            "contagem_entradas": len(entradas_manifesto),
            "timestamp_compilacao_utc": ts_utc,
            "entradas": entradas_manifesto,
        }
        manifesto_bytes = serializar_jcs_canonico(manifesto_obj)
        sha_manifesto = hashlib.sha256(manifesto_bytes).hexdigest()

        assinatura_raw = priv_key.sign(manifesto_bytes)
        sig_bytes = (assinatura_raw.hex() + "\n").encode("ascii")
        sha_sig = hashlib.sha256(sig_bytes).hexdigest()

        recibo_obj = {
            "esquema_recibo": "1.0.0",
            "versao_catalogo": versao,
            "status": "PUBLICADO",
            "sha256_manifesto": sha_manifesto,
            "sha256_assinatura_sig": sha_sig,
            "sha256_indice_sqlite": sha_sql,
            "total_entradas": len(entradas_manifesto),
            "timestamp_publicacao_utc": _utc_now_iso(),
        }
        recibo_bytes = (
            json.dumps(recibo_obj, sort_keys=True, indent=2, ensure_ascii=False).encode("utf-8")
            + b"\n"
        )

        _atomic_write_bytes(os.path.join(dir_stage, "manifesto_catalogo.json"), manifesto_bytes)
        _atomic_write_bytes(os.path.join(dir_stage, "manifesto_catalogo.sig"), sig_bytes)
        _atomic_write_bytes(os.path.join(dir_stage, "CONCLUSAO_PUBLICACAO.json"), recibo_bytes)

        if falha_em == "pos_staging":
            falha_simulada = True
            raise FalhaInjetadaPublicacaoError("Falha simulada pos_staging.")

        # Revalidacao fail-closed completa ainda no diretorio de staging
        verificar_integridade_abertura_versao(
            dir_stage,
            caminho_pub,
            ancora_sha256=ancora_sha256,
            versao_esperada=versao,
        )

        # Permissoes somente-leitura antes da promocao para releases/
        _aplicar_somente_leitura_recursivo(dir_stage)

        if os.path.exists(dir_destino_release):
            raise IntegridadeCatalogoError(
                f"Sobrescrita proibida: versao '{versao}' surgiu concorrentemente em '{dir_destino_release}'."
            )
        if falha_em == "pre_rename_release":
            falha_simulada = True
            raise FalhaInjetadaPublicacaoError("Falha simulada pre_rename_release.")

        os.replace(dir_stage, dir_destino_release)
        _fsync_diretorio_seguro(dir_releases)

        if falha_em == "pos_rename_release_pre_ponteiro":
            falha_simulada = True
            raise FalhaInjetadaPublicacaoError("Falha simulada pos_rename_release_pre_ponteiro.")
    except Exception:
        if not falha_simulada:
            _remover_arvore_segura(dir_stage)
        raise

    ponteiro: Optional[Dict[str, Any]] = None
    if ativar:
        ponteiro = _atualizar_ponteiro_catalogo_ativo(
            dir_cat,
            versao_alvo=versao,
            sha256_manifesto=sha_manifesto,
            sha256_assinatura_sig=sha_sig,
            falha_em=falha_em,
        )

    return {
        "versao_catalogo": versao,
        "dir_versao": dir_destino_release,
        "ativada": bool(ativar),
        "ponteiro_ativo": ponteiro,
        "sha256_chave_publica": sha_pub,
        "sha256_manifesto": sha_manifesto,
        "sha256_assinatura_sig": sha_sig,
        "sha256_indice_sqlite": sha_sql,
        "total_entradas": len(entradas_manifesto),
        "j_permitidos": j_permitidos,
    }


def ativar_versao_publicada(
    versao_alvo: str,
    *,
    dir_catalogo: str = DIR_CATALOGO_PADRAO,
    caminho_chave_publica: Optional[str] = None,
    ancora_sha256: str = CHAVE_PUBLICA_CATALOGO_SHA256,
    falha_em: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Promove/ativa ou executa rollback atomico do ponteiro `catalogo_ativo.json`
    para uma versao ja publicada em `releases/<versao_alvo>`, validando integralmente
    sua cadeia criptografica e seu indice SQLite antes de mover o ponteiro.
    """
    versao = validar_versao_catalogo_str(versao_alvo)
    dir_cat = os.path.abspath(dir_catalogo)
    dir_releases = os.path.join(dir_cat, "releases")
    if not os.path.isdir(dir_releases):
        raise CatalogoIndisponivelError(f"Diretorio de releases ausente: '{dir_releases}'.")
    dir_versao = resolver_caminho_seguro_em_diretorio(dir_releases, versao)
    caminho_pub = (
        os.path.abspath(caminho_chave_publica)
        if caminho_chave_publica is not None
        else os.path.join(dir_cat, "chave_publica_catalogo.pem")
    )

    res = verificar_integridade_abertura_versao(
        dir_versao,
        caminho_pub,
        ancora_sha256=ancora_sha256,
        versao_esperada=versao,
    )

    from catalogo_lotomania_10000.leitor import LeitorCatalogoLotomania

    leitor_ver = LeitorCatalogoLotomania(
        dir_catalogo=dir_cat,
        caminho_chave_publica=caminho_pub,
        ancora_chave_publica_sha256=ancora_sha256,
        versao_fixa=versao,
    )
    leitor_ver.abrir_catalogo()

    return _atualizar_ponteiro_catalogo_ativo(
        dir_cat,
        versao_alvo=versao,
        sha256_manifesto=res["sha256_manifesto"],
        sha256_assinatura_sig=res["sha256_assinatura_sig"],
        falha_em=falha_em,
    )


def rollback_versao_catalogo(
    versao_anterior: str,
    *,
    dir_catalogo: str = DIR_CATALOGO_PADRAO,
    caminho_chave_publica: Optional[str] = None,
    ancora_sha256: str = CHAVE_PUBLICA_CATALOGO_SHA256,
) -> Dict[str, Any]:
    """Rollback atomico do ponteiro ativo para versao anterior integralmente revalidada."""
    return ativar_versao_publicada(
        versao_anterior,
        dir_catalogo=dir_catalogo,
        caminho_chave_publica=caminho_chave_publica,
        ancora_sha256=ancora_sha256,
    )


def _obter_commit_head_repositorio() -> str:
    try:
        proc = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_REPOSITORIO_RAIZ,
            capture_output=True,
            text=True,
            check=True,
        )
        out = proc.stdout.strip()
        if len(out) == 40:
            return out
    except Exception:
        pass
    return "455796c7f83b4042ba531438f2bb6ac9324ed426"


def publicar_v1_padrao_repositorio(
    *,
    dir_catalogo: str = DIR_CATALOGO_PADRAO,
    caminho_chave_privada: str = CAMINHO_CHAVE_PRIVADA_PADRAO,
) -> Dict[str, Any]:
    """Publica a versao oficial `v1.0.0` (J=10.000, seed=330001) do dossie homologado."""
    dir_aud = os.path.join(_REPOSITORIO_RAIZ, "auditoria", "lotomania_carteira_10000")
    especs = [
        {
            "J": 10000,
            "seed": 330001,
            "versao_algoritmo": VERSAO_ALGORITMO_PADRAO,
            "configuracao": CONFIGURACAO_PADRAO_S1_1080K,
            "caminho_json_carteira": os.path.join(dir_aud, "carteira_10000_seed330001.json"),
            "caminho_benchmark_json": os.path.join(dir_aud, "benchmark_10000_seed330001.json"),
            "caminho_auditoria_json": os.path.join(dir_aud, "auditoria_independente_10000_seed330001.json"),
            "caminho_trilha_jsonl": os.path.join(dir_aud, "trilha_swaps_10000_seed330001.jsonl"),
            "sha256_trilha_jsonl": "9efd671caa8255cc57a51b8b2e11789c1d6ad4d4a9e7b42b269ab942ffa212e8",
            "commit_git_gerador": _obter_commit_head_repositorio(),
        }
    ]
    return publicar_versao_catalogo(
        "v1.0.0",
        especs,
        dir_catalogo=dir_catalogo,
        caminho_chave_privada=caminho_chave_privada,
        caminho_chave_publica=os.path.join(dir_catalogo, "chave_publica_catalogo.pem"),
        ancora_sha256=CHAVE_PUBLICA_CATALOGO_SHA256,
        ativar=True,
    )
