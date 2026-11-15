# -*- coding: utf-8 -*-
"""
Verificacao criptografica aciclica e controle de integridade de arquivos em disco
para o catalogo imutavel `CATALOGO_LOTOMANIA_10000`.

Cadeia de autenticacao:
  Ancora independente (`CHAVE_PUBLICA_CATALOGO_SHA256`)
    -> `chave_publica_catalogo.pem`
    -> `manifesto_catalogo.sig` (Ed25519 sobre bytes canonicos de `manifesto_catalogo.json`)
    -> `manifesto_catalogo.json` (digests SHA-256 de `indice_catalogo.sqlite` e `particoes/*.bin`)
  Registro terminal operacional:
    `CONCLUSAO_PUBLICACAO.json` vinculado para tras aos hashes ja autenticados
    (registro estrutural de encerramento, nao prova criptografica independente).

Zero instrucoes `assert` para compatibilidade integral com `python` e `python -O`.
"""

import hashlib
import json
import os
import re
import stat
from typing import Any, Dict, Iterable, List, Mapping, Optional, Set, Tuple

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from catalogo_lotomania_10000.canonicalizacao import (
    ESQUEMA_CATALOGO_VERSAO,
    calcular_sha256_configuracao,
    exigir,
    montar_id_carteira,
    serializar_jcs_canonico,
)

# Ancora independente oficial da chave publica SPKI PEM exclusiva do catalogo
# (`C:\Users\Luis Brun\B2B_chaves\catalogo_lotomania_10000_ed25519.key`).
CHAVE_PUBLICA_CATALOGO_SHA256 = (
    "524727ffad5613487d1a27ffa04c02276db50069bb71231027b283c176fdb41c"
)

ARQUIVOS_RAIZ_VERSAO = frozenset(
    {
        "manifesto_catalogo.json",
        "manifesto_catalogo.sig",
        "indice_catalogo.sqlite",
        "CONCLUSAO_PUBLICACAO.json",
    }
)

CHAVES_RECIBO_OBRIGATORIAS = frozenset(
    {
        "esquema_recibo",
        "versao_catalogo",
        "status",
        "sha256_manifesto",
        "sha256_assinatura_sig",
        "sha256_indice_sqlite",
        "total_entradas",
        "timestamp_publicacao_utc",
    }
)

CHAVES_MANIFESTO_OBRIGATORIAS = frozenset(
    {
        "esquema_versao",
        "versao_catalogo",
        "algoritmo_assinatura",
        "algoritmo_hash",
        "loteria",
        "politica_leitura",
        "chave_publica_sha256_informada",
        "indice_sqlite",
        "contagem_entradas",
        "timestamp_compilacao_utc",
        "entradas",
    }
)

_RE_SHA256_HEX = re.compile(r"^[0-9a-f]{64}$")
_RE_VERSAO_CATALOGO = re.compile(r"^v\d+\.\d+\.\d+$")
_TAMANHO_BLOCO_LEITURA = 65536


class CatalogoLotomaniaError(RuntimeError):
    """Excecao base do subsistema de catalogo imutavel da Lotomania."""


class IntegridadeCatalogoError(CatalogoLotomaniaError):
    """Falha criptografica, estrutural, de permissao ou de completude do catalogo."""


class CatalogoIndisponivelError(CatalogoLotomaniaError):
    """Catalogo ou versao solicitada ausente ou sem ponteiro ativo valido."""


class SolicitacaoForaDaGradeError(CatalogoLotomaniaError):
    """Solicitacao de J, seed ou configuracao nao catalogada (rejeicao estrita)."""


def validar_sha256_hex(valor: Any, nome: str) -> str:
    """Valida formato hexadecimal minusculo estrito de 64 caracteres."""
    if type(valor) is not str or not _RE_SHA256_HEX.match(valor):
        raise IntegridadeCatalogoError(
            f"{nome} invalido: esperado SHA-256 hex minusculo de 64 caracteres (recebido {valor!r})."
        )
    return valor


def validar_versao_catalogo_str(valor: Any) -> str:
    """Valida identificador semver de versao do catalogo (`vX.Y.Z`)."""
    if type(valor) is not str or not _RE_VERSAO_CATALOGO.match(valor):
        raise IntegridadeCatalogoError(
            f"versao_catalogo invalida: esperado formato vX.Y.Z (recebido {valor!r})."
        )
    return valor


def extrair_assinatura_stat(st: os.stat_result) -> Tuple[int, int, int, int]:
    """Extrai tupla comparavel `(st_dev, st_ino, st_size, st_mtime_ns)` de `stat_result`."""
    return (int(st.st_dev), int(st.st_ino), int(st.st_size), int(st.st_mtime_ns))


def resolver_caminho_seguro_em_diretorio(dir_base: str, rel_path: str) -> str:
    """Garante que caminho relativo (`a/b.ext`) permaneca estritamente dentro de `dir_base`."""
    if type(rel_path) is not str or not rel_path or "\\" in rel_path:
        raise IntegridadeCatalogoError(f"Caminho relativo invalido no manifesto: {rel_path!r}.")
    if rel_path.startswith("/") or ":" in rel_path:
        raise IntegridadeCatalogoError(f"Caminho absoluto proibido no manifesto: {rel_path!r}.")
    partes = rel_path.split("/")
    if any(p in ("", ".", "..") for p in partes):
        raise IntegridadeCatalogoError(f"Segmento de caminho proibido no manifesto: {rel_path!r}.")
    base_real = os.path.realpath(dir_base)
    alvo = os.path.realpath(os.path.join(base_real, *partes))
    if not alvo.startswith(base_real + os.sep):
        raise IntegridadeCatalogoError(
            f"Caminho fora do diretorio de versao detectado: {rel_path!r}."
        )
    return alvo


def _garantir_nao_symlink(caminho: str) -> os.stat_result:
    try:
        lst = os.lstat(caminho)
    except OSError as exc:
        raise IntegridadeCatalogoError(
            f"Falha ao inspecionar arquivo obrigatorio '{caminho}': {exc}"
        ) from exc
    if stat.S_ISLNK(lst.st_mode):
        raise IntegridadeCatalogoError(
            f"Link simbolico proibido na arvore do catalogo: '{caminho}'."
        )
    if not stat.S_ISREG(lst.st_mode):
        raise IntegridadeCatalogoError(
            f"Artefato do catalogo nao e arquivo regular: '{caminho}'."
        )
    return lst


def ler_arquivo_controlado_fd(
    caminho: str,
    *,
    tamanho_esperado: Optional[int] = None,
    tamanho_maximo: int = 64 * 1024 * 1024,
) -> Tuple[bytes, Tuple[int, int, int, int]]:
    """
    Executa leitura completa controlada ate EOF pelo mesmo descritor aberto (`fd`),
    conferindo `fstat(fd)` antes e depois da leitura para mitigar TOCTOU e truncamento.
    """
    st_lstat = _garantir_nao_symlink(caminho)
    limite = tamanho_esperado if tamanho_esperado is not None else tamanho_maximo

    try:
        with open(caminho, "rb") as fh:
            fd = fh.fileno()
            st_antes = os.fstat(fd)
            if not stat.S_ISREG(st_antes.st_mode):
                raise IntegridadeCatalogoError(
                    f"Descritor aberto nao corresponde a arquivo regular: '{caminho}'."
                )
            sig_antes = extrair_assinatura_stat(st_antes)
            if sig_antes != extrair_assinatura_stat(st_lstat):
                raise IntegridadeCatalogoError(
                    f"Alteracao concorrente detectada entre lstat e abertura de '{caminho}'."
                )
            if tamanho_esperado is not None and st_antes.st_size != tamanho_esperado:
                raise IntegridadeCatalogoError(
                    f"Tamanho divergente em '{caminho}': esperado {tamanho_esperado} bytes, "
                    f"encontrado {st_antes.st_size}."
                )
            if st_antes.st_size > limite:
                raise IntegridadeCatalogoError(
                    f"Arquivo '{caminho}' excede limite maximo permitido ({st_antes.st_size} > {limite})."
                )

            blocos: List[bytes] = []
            total_lido = 0
            teto_leitura = limite + 1
            while True:
                restante_teto = teto_leitura - total_lido
                if restante_teto <= 0:
                    raise IntegridadeCatalogoError(
                        f"Arquivo '{caminho}' excedeu limite esperado durante leitura controlada."
                    )
                pedaco = fh.read(min(_TAMANHO_BLOCO_LEITURA, restante_teto))
                if not pedaco:
                    break
                blocos.append(pedaco)
                total_lido += len(pedaco)

            st_depois = os.fstat(fd)
            sig_depois = extrair_assinatura_stat(st_depois)
    except IntegridadeCatalogoError:
        raise
    except OSError as exc:
        raise IntegridadeCatalogoError(f"Erro de I/O ao ler '{caminho}': {exc}") from exc

    st_caminho_final = _garantir_nao_symlink(caminho)
    sig_final = extrair_assinatura_stat(st_caminho_final)
    if sig_antes != sig_depois or sig_antes != sig_final:
        raise IntegridadeCatalogoError(
            f"Alteracao de metadados/descritor detectada durante leitura de '{caminho}'."
        )

    dados = b"".join(blocos)
    if tamanho_esperado is not None and len(dados) != tamanho_esperado:
        raise IntegridadeCatalogoError(
            f"Leitura truncada em '{caminho}': esperados {tamanho_esperado} bytes, lidos {len(dados)}."
        )
    if len(dados) != st_depois.st_size:
        raise IntegridadeCatalogoError(
            f"Tamanho lido ate EOF ({len(dados)}) diverge de fstat ({st_depois.st_size}) em '{caminho}'."
        )
    return dados, sig_depois


def calcular_sha256_arquivo_streaming(
    caminho: str, *, tamanho_esperado: Optional[int] = None
) -> Tuple[str, int, Tuple[int, int, int, int]]:
    """Calcula SHA-256 e tamanho em streaming de 64 KiB sobre um unico descritor verificado."""
    st_lstat = _garantir_nao_symlink(caminho)
    hasher = hashlib.sha256()
    total_lido = 0
    try:
        with open(caminho, "rb") as fh:
            fd = fh.fileno()
            st_antes = os.fstat(fd)
            if not stat.S_ISREG(st_antes.st_mode):
                raise IntegridadeCatalogoError(
                    f"Descritor aberto nao e arquivo regular: '{caminho}'."
                )
            sig_antes = extrair_assinatura_stat(st_antes)
            if sig_antes != extrair_assinatura_stat(st_lstat):
                raise IntegridadeCatalogoError(
                    f"Alteracao concorrente entre lstat e open em '{caminho}'."
                )
            if tamanho_esperado is not None and st_antes.st_size != tamanho_esperado:
                raise IntegridadeCatalogoError(
                    f"Tamanho divergente em '{caminho}': esperado {tamanho_esperado}, atual {st_antes.st_size}."
                )
            while True:
                pedaco = fh.read(_TAMANHO_BLOCO_LEITURA)
                if not pedaco:
                    break
                hasher.update(pedaco)
                total_lido += len(pedaco)
            st_depois = os.fstat(fd)
            sig_depois = extrair_assinatura_stat(st_depois)
    except IntegridadeCatalogoError:
        raise
    except OSError as exc:
        raise IntegridadeCatalogoError(
            f"Erro de streaming SHA-256 em '{caminho}': {exc}"
        ) from exc

    sig_final = extrair_assinatura_stat(_garantir_nao_symlink(caminho))
    if sig_antes != sig_depois or sig_antes != sig_final:
        raise IntegridadeCatalogoError(
            f"Alteracao detectada durante hashing em streaming de '{caminho}'."
        )
    if total_lido != st_depois.st_size:
        raise IntegridadeCatalogoError(
            f"Total lido ({total_lido}) diverge do descritor ({st_depois.st_size}) em '{caminho}'."
        )
    if tamanho_esperado is not None and total_lido != tamanho_esperado:
        raise IntegridadeCatalogoError(
            f"Tamanho final de '{caminho}' ({total_lido}) diverge do esperado ({tamanho_esperado})."
        )
    return hasher.hexdigest(), total_lido, sig_depois


def validar_ancora_chave_publica(
    caminho_pem: str,
    ancora_sha256_esperada: str = CHAVE_PUBLICA_CATALOGO_SHA256,
) -> Tuple[Ed25519PublicKey, str]:
    """
    Valida `chave_publica_catalogo.pem` contra a ancora independente de confianca
    e retorna `(Ed25519PublicKey, sha256_pem_verificado)`.
    """
    ancora = validar_sha256_hex(ancora_sha256_esperada, "ancora_sha256_esperada")
    if not os.path.isfile(caminho_pem):
        raise IntegridadeCatalogoError(
            f"Chave publica obrigatoria do catalogo ausente: '{caminho_pem}'."
        )
    pem_bytes, _ = ler_arquivo_controlado_fd(caminho_pem, tamanho_maximo=65536)
    sha_pem = hashlib.sha256(pem_bytes).hexdigest()
    if sha_pem != ancora:
        raise IntegridadeCatalogoError(
            "Chave publica do catalogo diverge da ancora independente confiavel "
            f"(encontrado={sha_pem}, ancora={ancora})."
        )
    try:
        chave_pub = serialization.load_pem_public_key(pem_bytes)
    except Exception as exc:
        raise IntegridadeCatalogoError(
            f"Falha ao decodificar chave publica PEM do catalogo: {exc}"
        ) from exc
    if not isinstance(chave_pub, Ed25519PublicKey):
        raise IntegridadeCatalogoError("Chave publica do catalogo nao e Ed25519 valida.")
    return chave_pub, sha_pem


def verificar_assinatura_manifesto_ed25519(
    manifesto_bytes: bytes,
    caminho_sig: str,
    chave_publica: Ed25519PublicKey,
) -> str:
    """
    Valida assinatura destacada Ed25519 em `manifesto_catalogo.sig` sobre os bytes
    exatos de `manifesto_catalogo.json`, retornando `sha256` do arquivo `.sig`.
    """
    if not os.path.isfile(caminho_sig):
        raise IntegridadeCatalogoError(
            f"Assinatura obrigatoria ausente: '{caminho_sig}'."
        )
    sig_arquivo_bytes, _ = ler_arquivo_controlado_fd(caminho_sig, tamanho_maximo=4096)
    try:
        sig_hex = sig_arquivo_bytes.strip().decode("ascii")
        sig_raw = bytes.fromhex(sig_hex)
    except Exception as exc:
        raise IntegridadeCatalogoError(
            f"Formato corrompido em manifesto_catalogo.sig: {exc}"
        ) from exc
    if len(sig_raw) != 64:
        raise IntegridadeCatalogoError(
            f"Assinatura Ed25519 deve ter 64 bytes (recebido {len(sig_raw)})."
        )
    try:
        chave_publica.verify(sig_raw, manifesto_bytes)
    except InvalidSignature as exc:
        raise IntegridadeCatalogoError(
            "Assinatura digital Ed25519 INVALIDA para manifesto_catalogo.json."
        ) from exc
    return hashlib.sha256(sig_arquivo_bytes).hexdigest()


def _validar_entrada_manifesto(
    entrada: Any,
    idx: int,
    dir_versao: str,
) -> Tuple[Tuple[str, int, int, str], str]:
    if not isinstance(entrada, dict):
        raise IntegridadeCatalogoError(f"Entrada {idx} do manifesto nao e objeto JSON.")
    campos_req = {
        "id_carteira",
        "versao_algoritmo",
        "J",
        "seed",
        "sha256_configuracao",
        "configuracao_canonica",
        "particao_relpath",
        "tamanho_bytes",
        "sha256_estado_canonico",
        "hash_carteira_sha256_v1",
        "hash_carteira_sha256_v2_canonico",
        "sha256_matriz_incidencia_100",
        "proveniencia",
    }
    falt = sorted(campos_req - set(entrada.keys()))
    if falt:
        raise IntegridadeCatalogoError(
            f"Entrada {idx} do manifesto sem campos obrigatorios: {falt}."
        )

    J = entrada["J"]
    seed = entrada["seed"]
    versao_alg = entrada["versao_algoritmo"]
    if type(J) is not int or J < 2 or J > 10000 or J % 2 != 0:
        raise IntegridadeCatalogoError(f"J invalido na entrada {idx} do manifesto: {J!r}.")
    if type(seed) is not int:
        raise IntegridadeCatalogoError(f"seed invalida na entrada {idx}: {seed!r}.")
    if type(versao_alg) is not str or not versao_alg:
        raise IntegridadeCatalogoError(f"versao_algoritmo invalida na entrada {idx}.")

    try:
        _, _, sha_cfg_recalc = calcular_sha256_configuracao(entrada["configuracao_canonica"])
    except Exception as exc:
        raise IntegridadeCatalogoError(
            f"Configuracao canonica invalida na entrada {idx}: {exc}"
        ) from exc
    sha_cfg = validar_sha256_hex(entrada["sha256_configuracao"], "sha256_configuracao")
    if sha_cfg != sha_cfg_recalc:
        raise IntegridadeCatalogoError(
            f"sha256_configuracao divergente da configuracao canonica na entrada {idx}."
        )

    id_esperado = montar_id_carteira(
        J=J, seed=seed, versao_algoritmo=versao_alg, sha256_configuracao=sha_cfg
    )
    if entrada["id_carteira"] != id_esperado:
        raise IntegridadeCatalogoError(
            f"id_carteira divergente na entrada {idx}: {entrada['id_carteira']!r} vs {id_esperado!r}."
        )

    tamanho_esp = 50 * J
    if type(entrada["tamanho_bytes"]) is not int or entrada["tamanho_bytes"] != tamanho_esp:
        raise IntegridadeCatalogoError(
            f"tamanho_bytes invalido na entrada {idx}: esperado {tamanho_esp}, recebido {entrada['tamanho_bytes']!r}."
        )

    for campo_h in (
        "sha256_estado_canonico",
        "hash_carteira_sha256_v1",
        "hash_carteira_sha256_v2_canonico",
        "sha256_matriz_incidencia_100",
    ):
        validar_sha256_hex(entrada[campo_h], campo_h)

    prov = entrada["proveniencia"]
    if not isinstance(prov, dict) or prov.get("todas_travas_aprovadas") is not True:
        raise IntegridadeCatalogoError(
            f"Entrada {idx} sem declaracao aprovada R1-R12 em proveniencia."
        )

    rel_part = entrada["particao_relpath"]
    if type(rel_part) is not str or not rel_part.startswith("particoes/"):
        raise IntegridadeCatalogoError(
            f"particao_relpath deve residir em particoes/: {rel_part!r}."
        )
    resolver_caminho_seguro_em_diretorio(dir_versao, rel_part)
    return (versao_alg, J, seed, sha_cfg), rel_part


def validar_recibo_conclusao(
    caminho_recibo: str,
    *,
    versao_esperada: str,
    sha256_manifesto_real: str,
    sha256_sig_real: str,
    sha256_indice_real: str,
    total_entradas_esperado: int,
) -> Dict[str, Any]:
    """
    Valida `CONCLUSAO_PUBLICACAO.json` como registro terminal operacional de fechamento.

    Nota normativa: este recibo nao e prova criptografica independente de execucao do
    pipeline; comprova consistencia estrutural vinculada para tras ao manifesto autenticado.
    """
    if not os.path.isfile(caminho_recibo):
        raise IntegridadeCatalogoError(
            f"Registro terminal CONCLUSAO_PUBLICACAO.json ausente: '{caminho_recibo}'."
        )
    recibo_bytes, _ = ler_arquivo_controlado_fd(caminho_recibo, tamanho_maximo=65536)
    try:
        recibo = json.loads(recibo_bytes.decode("utf-8"))
    except Exception as exc:
        raise IntegridadeCatalogoError(
            f"CONCLUSAO_PUBLICACAO.json corrompido: {exc}"
        ) from exc

    if not isinstance(recibo, dict):
        raise IntegridadeCatalogoError("CONCLUSAO_PUBLICACAO.json deve ser objeto JSON.")
    chaves = set(recibo.keys())
    if chaves != CHAVES_RECIBO_OBRIGATORIAS:
        raise IntegridadeCatalogoError(
            f"Esquema invalido em CONCLUSAO_PUBLICACAO.json: chaves={sorted(chaves)}."
        )
    exigir(
        recibo["status"] == "PUBLICADO",
        f"Status invalido no recibo de publicacao: {recibo['status']!r}.",
        IntegridadeCatalogoError,
    )
    exigir(
        recibo["versao_catalogo"] == versao_esperada,
        "versao_catalogo do recibo diverge do manifesto autenticado.",
        IntegridadeCatalogoError,
    )
    exigir(
        recibo["sha256_manifesto"] == sha256_manifesto_real,
        "sha256_manifesto no recibo diverge dos bytes assinados do manifesto.",
        IntegridadeCatalogoError,
    )
    exigir(
        recibo["sha256_assinatura_sig"] == sha256_sig_real,
        "sha256_assinatura_sig no recibo diverge de manifesto_catalogo.sig.",
        IntegridadeCatalogoError,
    )
    exigir(
        recibo["sha256_indice_sqlite"] == sha256_indice_real,
        "sha256_indice_sqlite no recibo diverge do manifesto autenticado.",
        IntegridadeCatalogoError,
    )
    exigir(
        type(recibo["total_entradas"]) is int and recibo["total_entradas"] == total_entradas_esperado,
        "total_entradas no recibo diverge do manifesto autenticado.",
        IntegridadeCatalogoError,
    )
    exigir(
        type(recibo["esquema_recibo"]) is str and len(recibo["esquema_recibo"]) > 0,
        "esquema_recibo invalido no recibo.",
        IntegridadeCatalogoError,
    )
    exigir(
        type(recibo["timestamp_publicacao_utc"]) is str and len(recibo["timestamp_publicacao_utc"]) > 0,
        "timestamp_publicacao_utc invalido no recibo.",
        IntegridadeCatalogoError,
    )
    return recibo


def _listar_arquivos_relativos_versao(dir_versao: str) -> Set[str]:
    base_real = os.path.realpath(dir_versao)
    encontrados: Set[str] = set()
    for raiz, dirs, arqs in os.walk(base_real, followlinks=False):
        for d in dirs:
            p_dir = os.path.join(raiz, d)
            if os.path.islink(p_dir):
                raise IntegridadeCatalogoError(
                    f"Subdiretorio symlink proibido dentro de release: '{p_dir}'."
                )
        for arq in arqs:
            p_arq = os.path.join(raiz, arq)
            _garantir_nao_symlink(p_arq)
            rel = os.path.relpath(p_arq, base_real).replace(os.sep, "/")
            encontrados.add(rel)
    return encontrados


def verificar_integridade_abertura_versao(
    dir_versao: str,
    caminho_chave_pub: str,
    *,
    ancora_sha256: str = CHAVE_PUBLICA_CATALOGO_SHA256,
    versao_esperada: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Executa a verificacao fail-closed de abertura de uma versao do catalogo:
    ancora -> chave publica -> Ed25519 sobre manifesto -> schema e unicidade ->
    recibo terminal vinculado -> SHA-256 de indice_catalogo.sqlite -> inventario exato
    e `st_size` de todas as particoes declaradas (sem ler os bytes `.bin`).
    """
    if not os.path.isdir(dir_versao) or os.path.islink(dir_versao):
        raise CatalogoIndisponivelError(
            f"Diretorio de versao do catalogo inexistente ou invalido: '{dir_versao}'."
        )

    chave_pub, sha_pub = validar_ancora_chave_publica(
        caminho_chave_pub, ancora_sha256_esperada=ancora_sha256
    )

    caminho_manifesto = os.path.join(dir_versao, "manifesto_catalogo.json")
    caminho_sig = os.path.join(dir_versao, "manifesto_catalogo.sig")
    caminho_recibo = os.path.join(dir_versao, "CONCLUSAO_PUBLICACAO.json")
    caminho_indice = os.path.join(dir_versao, "indice_catalogo.sqlite")

    if not os.path.isfile(caminho_manifesto):
        raise IntegridadeCatalogoError(f"Manifesto ausente em '{dir_versao}'.")

    manifesto_bytes, _ = ler_arquivo_controlado_fd(
        caminho_manifesto, tamanho_maximo=16 * 1024 * 1024
    )
    sha_sig = verificar_assinatura_manifesto_ed25519(
        manifesto_bytes, caminho_sig, chave_pub
    )
    sha_manifesto = hashlib.sha256(manifesto_bytes).hexdigest()

    try:
        manifesto = json.loads(manifesto_bytes.decode("utf-8"))
    except Exception as exc:
        raise IntegridadeCatalogoError(
            f"Falha ao interpretar manifesto_catalogo.json: {exc}"
        ) from exc

    if not isinstance(manifesto, dict):
        raise IntegridadeCatalogoError("manifesto_catalogo.json deve ser um objeto JSON.")
    chaves_man = set(manifesto.keys())
    if chaves_man != CHAVES_MANIFESTO_OBRIGATORIAS:
        raise IntegridadeCatalogoError(
            f"Chaves divergentes em manifesto_catalogo.json: {sorted(chaves_man)}."
        )
    if serializar_jcs_canonico(manifesto) != manifesto_bytes:
        raise IntegridadeCatalogoError(
            "manifesto_catalogo.json em disco nao esta em formato JCS canonico exato."
        )

    versao_cat = validar_versao_catalogo_str(manifesto["versao_catalogo"])
    if versao_esperada is not None and versao_cat != versao_esperada:
        raise IntegridadeCatalogoError(
            f"Versao declarada no manifesto ({versao_cat}) diverge da esperada ({versao_esperada})."
        )
    exigir(
        manifesto["esquema_versao"] == ESQUEMA_CATALOGO_VERSAO,
        "esquema_versao incompativel no manifesto.",
        IntegridadeCatalogoError,
    )
    exigir(
        manifesto["algoritmo_assinatura"] == "Ed25519"
        and manifesto["algoritmo_hash"] == "SHA-256",
        "Algoritmos declarados no manifesto incompativeis.",
        IntegridadeCatalogoError,
    )
    exigir(
        manifesto["loteria"] == "lotomania",
        "Loteria invalida no manifesto.",
        IntegridadeCatalogoError,
    )
    exigir(
        manifesto["chave_publica_sha256_informada"] == sha_pub,
        "Metadado chave_publica_sha256_informada no manifesto diverge da ancora autenticada.",
        IntegridadeCatalogoError,
    )

    pol = manifesto["politica_leitura"]
    if not isinstance(pol, dict) or pol.get("apenas_grade_exata") is not True:
        raise IntegridadeCatalogoError("politica_leitura deve impor apenas_grade_exata=true.")
    if pol.get("rejeitar_fora_da_grade") is not True:
        raise IntegridadeCatalogoError("politica_leitura deve impor rejeitar_fora_da_grade=true.")
    j_perm = pol.get("j_permitidos")
    if not isinstance(j_perm, list) or not j_perm or not all(type(x) is int for x in j_perm):
        raise IntegridadeCatalogoError("j_permitidos invalido na politica_leitura do manifesto.")

    idx_info = manifesto["indice_sqlite"]
    if not isinstance(idx_info, dict) or idx_info.get("arquivo") != "indice_catalogo.sqlite":
        raise IntegridadeCatalogoError("Metadado indice_sqlite invalido no manifesto.")
    sha_idx_esp = validar_sha256_hex(idx_info.get("sha256"), "indice_sqlite.sha256")
    tam_idx_esp = idx_info.get("tamanho_bytes")
    if type(tam_idx_esp) is not int or tam_idx_esp <= 0:
        raise IntegridadeCatalogoError("indice_sqlite.tamanho_bytes invalido.")

    entradas = manifesto["entradas"]
    if not isinstance(entradas, list) or len(entradas) == 0:
        raise IntegridadeCatalogoError("Lista de entradas do manifesto vazia ou invalida.")
    if type(manifesto["contagem_entradas"]) is not int or manifesto["contagem_entradas"] != len(entradas):
        raise IntegridadeCatalogoError("contagem_entradas diverge do total de entradas.")

    chaves_unicas: Set[Tuple[str, int, int, str]] = set()
    ids_vistos: Set[str] = set()
    particoes_esperadas: Set[str] = set()
    j_encontrados: Set[int] = set()
    for idx_e, ent in enumerate(entradas):
        chave_nat, rel_part = _validar_entrada_manifesto(ent, idx_e, dir_versao)
        if chave_nat in chaves_unicas:
            raise IntegridadeCatalogoError(
                f"Colisao de identidade natural no manifesto: {chave_nat}."
            )
        if ent["id_carteira"] in ids_vistos:
            raise IntegridadeCatalogoError(
                f"id_carteira duplicado no manifesto: {ent['id_carteira']}."
            )
        if rel_part in particoes_esperadas:
            raise IntegridadeCatalogoError(
                f"particao_relpath duplicada no manifesto: {rel_part}."
            )
        chaves_unicas.add(chave_nat)
        ids_vistos.add(ent["id_carteira"])
        particoes_esperadas.add(rel_part)
        j_encontrados.add(ent["J"])

    if sorted(j_encontrados) != sorted(j_perm):
        raise IntegridadeCatalogoError(
            f"Grade j_permitidos {j_perm} diverge dos portes nas entradas {sorted(j_encontrados)}."
        )

    recibo = validar_recibo_conclusao(
        caminho_recibo,
        versao_esperada=versao_cat,
        sha256_manifesto_real=sha_manifesto,
        sha256_sig_real=sha_sig,
        sha256_indice_real=sha_idx_esp,
        total_entradas_esperado=len(entradas),
    )

    sha_idx_real, tam_idx_real, _ = calcular_sha256_arquivo_streaming(
        caminho_indice, tamanho_esperado=tam_idx_esp
    )
    if sha_idx_real != sha_idx_esp:
        raise IntegridadeCatalogoError(
            f"indice_catalogo.sqlite adulterado: calculado={sha_idx_real}, manifesto={sha_idx_esp}."
        )

    arquivos_esperados = set(ARQUIVOS_RAIZ_VERSAO) | particoes_esperadas
    arquivos_reais = _listar_arquivos_relativos_versao(dir_versao)
    faltantes = sorted(arquivos_esperados - arquivos_reais)
    extras = sorted(arquivos_reais - arquivos_esperados)
    if faltantes or extras:
        raise IntegridadeCatalogoError(
            f"Inventario da versao '{versao_cat}' inconsistente (faltantes={faltantes}, extras={extras})."
        )

    for ent in entradas:
        caminho_part = resolver_caminho_seguro_em_diretorio(dir_versao, ent["particao_relpath"])
        st_p = _garantir_nao_symlink(caminho_part)
        if st_p.st_size != ent["tamanho_bytes"]:
            raise IntegridadeCatalogoError(
                f"Tamanho da particao '{ent['particao_relpath']}' diverge do manifesto "
                f"({st_p.st_size} != {ent['tamanho_bytes']})."
            )

    return {
        "versao_catalogo": versao_cat,
        "sha256_chave_publica": sha_pub,
        "sha256_manifesto": sha_manifesto,
        "sha256_assinatura_sig": sha_sig,
        "sha256_indice_sqlite": sha_idx_real,
        "tamanho_indice_sqlite": tam_idx_real,
        "manifesto": manifesto,
        "recibo": recibo,
    }
