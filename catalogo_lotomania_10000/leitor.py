# -*- coding: utf-8 -*-
"""
Leitor somente-leitura, fail-closed e desacoplado do otimizador combinatorio
para o catalogo imutavel `CATALOGO_LOTOMANIA_10000`.

Propriedades garantidas:
- Verificacao criptografica aciclica na abertura (`abrir_catalogo`) e a cada
  troca ou alteracao detectada em disco (`catalogo_ativo.json` / `stat`).
- Zero dependencia de runtime dos modulos `construtiva` ou `otimizador_swap`
  e zero acesso a chaves privadas.
- Politica de rejeicao estrita: qualquer `J`, `seed`, `versao_algoritmo` ou
  configuracao ausente da grade autenticada lanca `SolicitacaoForaDaGradeError`.
- Leitura binaria integral controlada pelo mesmo `fd`, com verificacao de
  SHA-256 completa antes de qualquer retencao no cache limitado a 32 MB.
- Zero instrucoes `assert` (execucao identica em `python` e `python -O`).
"""

from collections import OrderedDict
import hashlib
import json
import os
import sqlite3
import threading
import time
from typing import Any, Dict, List, Mapping, Optional, Tuple
import urllib.request

from catalogo_lotomania_10000.canonicalizacao import (
    CONFIGURACAO_PADRAO_S1_1080K,
    SHA256_CONFIGURACAO_PADRAO_S1_1080K,
    VERSAO_ALGORITMO_PADRAO,
    calcular_sha256_configuracao,
    exigir,
)
from catalogo_lotomania_10000.crypto_selo import (
    CHAVE_PUBLICA_CATALOGO_SHA256,
    CatalogoIndisponivelError,
    IntegridadeCatalogoError,
    SolicitacaoForaDaGradeError,
    extrair_assinatura_stat,
    ler_arquivo_controlado_fd,
    resolver_caminho_seguro_em_diretorio,
    validar_versao_catalogo_str,
    verificar_integridade_abertura_versao,
)

LIMITE_MAXIMO_CACHE_BYTES = 32 * 1024 * 1024  # 32 MB estritos

_REPOSITORIO_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIR_CATALOGO_PADRAO = os.path.join(_REPOSITORIO_RAIZ, "dados", "CATALOGO_LOTOMANIA_10000")
CAMINHO_CHAVE_PUBLICA_PADRAO = os.path.join(DIR_CATALOGO_PADRAO, "chave_publica_catalogo.pem")
CHAVES_PONTEIRO_ATIVO = frozenset(
    {
        "versao_ativa",
        "sha256_manifesto",
        "sha256_assinatura_sig",
        "atualizado_em_utc",
    }
)


class _CacheParticoesLRU:
    """Cache em RAM limitado em bytes, mantendo apenas payloads autenticados."""

    def __init__(self, max_bytes: int = LIMITE_MAXIMO_CACHE_BYTES) -> None:
        if type(max_bytes) is not int or max_bytes < 0 or max_bytes > LIMITE_MAXIMO_CACHE_BYTES:
            raise ValueError(
                f"max_cache_bytes deve estar no intervalo [0, {LIMITE_MAXIMO_CACHE_BYTES}] "
                f"(recebido {max_bytes!r})."
            )
        self.max_bytes = max_bytes
        self.bytes_em_uso = 0
        self._itens: "OrderedDict[Tuple[str, str], Dict[str, Any]]" = OrderedDict()
        self.hits = 0
        self.misses = 0
        self.invalidacoes = 0

    def limpar(self, *, contar_invalidacao: bool = False) -> None:
        if contar_invalidacao and self._itens:
            self.invalidacoes += len(self._itens)
        self._itens.clear()
        self.bytes_em_uso = 0

    def remover(self, chave: Tuple[str, str]) -> None:
        item = self._itens.pop(chave, None)
        if item is not None:
            self.bytes_em_uso -= item["tamanho_bytes"]
            self.invalidacoes += 1

    def obter(self, chave: Tuple[str, str]) -> Optional[Dict[str, Any]]:
        item = self._itens.get(chave)
        if item is None:
            return None
        self._itens.move_to_end(chave)
        return item

    def inserir(self, chave: Tuple[str, str], item: Dict[str, Any]) -> bool:
        tam = item["tamanho_bytes"]
        if tam > self.max_bytes:
            return False
        antigo = self._itens.pop(chave, None)
        if antigo is not None:
            self.bytes_em_uso -= antigo["tamanho_bytes"]
        while self._itens and (self.bytes_em_uso + tam) > self.max_bytes:
            _, removido = self._itens.popitem(last=False)
            self.bytes_em_uso -= removido["tamanho_bytes"]
        self._itens[chave] = item
        self._itens.move_to_end(chave)
        self.bytes_em_uso += tam
        return True

    def estatisticas(self) -> Dict[str, int]:
        return {
            "entradas": len(self._itens),
            "bytes_em_uso": self.bytes_em_uso,
            "max_cache_bytes": self.max_bytes,
            "hits": self.hits,
            "misses": self.misses,
            "invalidacoes": self.invalidacoes,
        }


def _ler_ponteiro_catalogo_ativo(
    dir_catalogo: str,
) -> Tuple[Dict[str, Any], Tuple[int, int, int, int]]:
    caminho_ptr = os.path.join(dir_catalogo, "catalogo_ativo.json")
    if not os.path.isfile(caminho_ptr) or os.path.islink(caminho_ptr):
        raise CatalogoIndisponivelError(
            f"Ponteiro de catalogo ativo ausente ou invalido: '{caminho_ptr}'."
        )
    raw, sig_stat = ler_arquivo_controlado_fd(caminho_ptr, tamanho_maximo=65536)
    try:
        ptr = json.loads(raw.decode("utf-8"))
    except Exception as exc:
        raise IntegridadeCatalogoError(
            f"catalogo_ativo.json corrompido: {exc}"
        ) from exc
    if not isinstance(ptr, dict) or set(ptr.keys()) != CHAVES_PONTEIRO_ATIVO:
        raise IntegridadeCatalogoError(
            f"Esquema invalido em catalogo_ativo.json em '{caminho_ptr}'."
        )
    validar_versao_catalogo_str(ptr["versao_ativa"])
    for campo_str in ("sha256_manifesto", "sha256_assinatura_sig", "atualizado_em_utc"):
        if type(ptr[campo_str]) is not str or not ptr[campo_str]:
            raise IntegridadeCatalogoError(
                f"Campo '{campo_str}' invalido em catalogo_ativo.json."
            )
    return ptr, sig_stat


def _conectar_sqlite_imutavel(caminho_sqlite: str) -> sqlite3.Connection:
    abs_path = os.path.abspath(caminho_sqlite)
    url_path = urllib.request.pathname2url(abs_path)
    uri = f"file:{url_path}?mode=ro&immutable=1"
    try:
        conn = sqlite3.connect(uri, uri=True, check_same_thread=True)
    except sqlite3.Error as exc:
        raise IntegridadeCatalogoError(
            f"Falha ao abrir indice_catalogo.sqlite em modo somente-leitura imutavel: {exc}"
        ) from exc
    return conn


def _decodificar_bloco_binario(dados_bin: bytes, inicio_bilhete: int, fim_bilhete: int) -> List[List[int]]:
    mv = memoryview(dados_bin)
    inicio_byte = inicio_bilhete * 50
    fim_byte = fim_bilhete * 50
    return [list(mv[pos : pos + 50]) for pos in range(inicio_byte, fim_byte, 50)]


class LeitorCatalogoLotomania:
    """
    Cliente somente-leitura do catalogo imutavel de carteiras Lotomania J=10.000.

    Observacao: este leitor nunca aciona algoritmos construtivos ou de swap em
    consultas online. Qualquer solicitacao fora da grade catalogada e rejeitada.
    """

    def __init__(
        self,
        dir_catalogo: str = DIR_CATALOGO_PADRAO,
        *,
        caminho_chave_publica: Optional[str] = None,
        ancora_chave_publica_sha256: str = CHAVE_PUBLICA_CATALOGO_SHA256,
        versao_fixa: Optional[str] = None,
        max_cache_bytes: int = LIMITE_MAXIMO_CACHE_BYTES,
    ) -> None:
        self._dir_catalogo = os.path.abspath(dir_catalogo)
        self._caminho_chave_pub = (
            os.path.abspath(caminho_chave_publica)
            if caminho_chave_publica is not None
            else os.path.join(self._dir_catalogo, "chave_publica_catalogo.pem")
        )
        self._ancora_sha256 = ancora_chave_publica_sha256
        self._versao_fixa = (
            validar_versao_catalogo_str(versao_fixa) if versao_fixa is not None else None
        )
        self._lock = threading.RLock()
        self._cache = _CacheParticoesLRU(max_bytes=max_cache_bytes)

        self._versao_carregada: Optional[str] = None
        self._dir_versao_carregada: Optional[str] = None
        self._sig_stat_ponteiro: Optional[Tuple[int, int, int, int]] = None
        self._sig_stat_manifesto: Optional[Tuple[int, int, int, int]] = None
        self._estado_abertura: Optional[Dict[str, Any]] = None
        self._entradas_ordenadas: Tuple[Dict[str, Any], ...] = ()
        self._indice_chave: Dict[Tuple[str, int, int, str], Dict[str, Any]] = {}
        self._indice_por_versao_j_cfg: Dict[Tuple[str, int, str], List[Dict[str, Any]]] = {}
        self._j_permitidos: Tuple[int, ...] = ()
        self._registros_sqlite_por_id: Dict[str, Dict[str, Any]] = {}

    def abrir_catalogo(self) -> Dict[str, Any]:
        """Executa abertura fail-closed com verificacao aciclica completa da versao."""
        with self._lock:
            self._carregar_e_validar_versao()
            exigir(
                self._estado_abertura is not None,
                "Estado interno ausente apos abertura do catalogo.",
                IntegridadeCatalogoError,
            )
            return {
                "versao_catalogo": self._versao_carregada,
                "dir_catalogo": self._dir_catalogo,
                "dir_versao": self._dir_versao_carregada,
                "sha256_chave_publica": self._estado_abertura["sha256_chave_publica"],
                "sha256_manifesto": self._estado_abertura["sha256_manifesto"],
                "sha256_assinatura_sig": self._estado_abertura["sha256_assinatura_sig"],
                "sha256_indice_sqlite": self._estado_abertura["sha256_indice_sqlite"],
                "j_permitidos": list(self._j_permitidos),
                "total_carteiras": len(self._entradas_ordenadas),
            }

    def _carregar_e_validar_versao(self) -> None:
        if not os.path.isdir(self._dir_catalogo) or os.path.islink(self._dir_catalogo):
            raise CatalogoIndisponivelError(
                f"Diretorio raiz do catalogo inexistente ou invalido: '{self._dir_catalogo}'."
            )

        sig_stat_ptr: Optional[Tuple[int, int, int, int]] = None
        ptr_info: Optional[Dict[str, Any]] = None
        if self._versao_fixa is not None:
            versao_alvo = self._versao_fixa
        else:
            ptr_info, sig_stat_ptr = _ler_ponteiro_catalogo_ativo(self._dir_catalogo)
            versao_alvo = ptr_info["versao_ativa"]

        dir_releases = os.path.join(self._dir_catalogo, "releases")
        if not os.path.isdir(dir_releases) or os.path.islink(dir_releases):
            raise CatalogoIndisponivelError(
                f"Diretorio de releases ausente ou invalido: '{dir_releases}'."
            )
        dir_versao = resolver_caminho_seguro_em_diretorio(dir_releases, versao_alvo)
        resultado = verificar_integridade_abertura_versao(
            dir_versao,
            self._caminho_chave_pub,
            ancora_sha256=self._ancora_sha256,
            versao_esperada=versao_alvo,
        )

        if ptr_info is not None:
            if ptr_info["sha256_manifesto"] != resultado["sha256_manifesto"]:
                raise IntegridadeCatalogoError(
                    "sha256_manifesto em catalogo_ativo.json diverge da versao apontada."
                )
            if ptr_info["sha256_assinatura_sig"] != resultado["sha256_assinatura_sig"]:
                raise IntegridadeCatalogoError(
                    "sha256_assinatura_sig em catalogo_ativo.json diverge da versao apontada."
                )

        caminho_manifesto = os.path.join(dir_versao, "manifesto_catalogo.json")
        sig_stat_man = extrair_assinatura_stat(os.lstat(caminho_manifesto))

        caminho_sqlite = os.path.join(dir_versao, "indice_catalogo.sqlite")
        registros_sql = self._ler_e_cruzar_sqlite(
            caminho_sqlite, resultado["manifesto"]
        )

        entradas = list(resultado["manifesto"]["entradas"])
        entradas.sort(
            key=lambda e: (
                e["J"],
                e["versao_algoritmo"],
                e["sha256_configuracao"],
                e["seed"],
                e["id_carteira"],
            )
        )

        indice_chave: Dict[Tuple[str, int, int, str], Dict[str, Any]] = {}
        indice_v_j_c: Dict[Tuple[str, int, str], List[Dict[str, Any]]] = {}
        for ent in entradas:
            chave = (
                ent["versao_algoritmo"],
                ent["J"],
                ent["seed"],
                ent["sha256_configuracao"],
            )
            indice_chave[chave] = ent
            grupo = (ent["versao_algoritmo"], ent["J"], ent["sha256_configuracao"])
            indice_v_j_c.setdefault(grupo, []).append(ent)

        if self._versao_carregada is not None and (
            self._versao_carregada != versao_alvo
            or self._sig_stat_manifesto != sig_stat_man
        ):
            self._cache.limpar(contar_invalidacao=True)

        self._versao_carregada = versao_alvo
        self._dir_versao_carregada = dir_versao
        self._sig_stat_ponteiro = sig_stat_ptr
        self._sig_stat_manifesto = sig_stat_man
        self._estado_abertura = resultado
        self._entradas_ordenadas = tuple(entradas)
        self._indice_chave = indice_chave
        self._indice_por_versao_j_cfg = indice_v_j_c
        self._j_permitidos = tuple(
            sorted(resultado["manifesto"]["politica_leitura"]["j_permitidos"])
        )
        self._registros_sqlite_por_id = registros_sql

    def _ler_e_cruzar_sqlite(
        self, caminho_sqlite: str, manifesto: Mapping[str, Any]
    ) -> Dict[str, Dict[str, Any]]:
        conn = _conectar_sqlite_imutavel(caminho_sqlite)
        try:
            cur = conn.cursor()
            cols = [
                "id_carteira",
                "versao_catalogo",
                "versao_algoritmo",
                "J",
                "seed",
                "sha256_configuracao",
                "particao_relpath",
                "tamanho_bytes",
                "sha256_estado_canonico",
                "hash_carteira_sha256_v1",
                "hash_carteira_sha256_v2_canonico",
                "sha256_matriz_incidencia_100",
                "todas_travas_aprovadas",
                "k_max",
                "phi2",
                "d_max",
                "P_gt_25",
                "R_win",
                "sigma_intra",
                "sigma_inter",
                "metadados_completos_json",
            ]
            sql = (
                f"SELECT {', '.join(cols)} FROM carteiras "
                "ORDER BY J ASC, versao_algoritmo ASC, sha256_configuracao ASC, seed ASC, id_carteira ASC"
            )
            try:
                linhas = cur.execute(sql).fetchall()
            except sqlite3.Error as exc:
                raise IntegridadeCatalogoError(
                    f"Falha ao consultar tabela carteiras em indice_catalogo.sqlite: {exc}"
                ) from exc
        finally:
            conn.close()

        entradas_man = {e["id_carteira"]: e for e in manifesto["entradas"]}
        if len(linhas) != len(entradas_man):
            raise IntegridadeCatalogoError(
                f"Contagem divergente entre SQLite ({len(linhas)}) e manifesto ({len(entradas_man)})."
            )

        registros: Dict[str, Dict[str, Any]] = {}
        for linha in linhas:
            reg = dict(zip(cols, linha))
            cid = reg["id_carteira"]
            ent = entradas_man.get(cid)
            if ent is None:
                raise IntegridadeCatalogoError(
                    f"id_carteira '{cid}' presente no SQLite mas ausente no manifesto assinado."
                )
            exigir(
                reg["versao_catalogo"] == manifesto["versao_catalogo"]
                and reg["versao_algoritmo"] == ent["versao_algoritmo"]
                and reg["J"] == ent["J"]
                and reg["seed"] == ent["seed"]
                and reg["sha256_configuracao"] == ent["sha256_configuracao"]
                and reg["particao_relpath"] == ent["particao_relpath"]
                and reg["tamanho_bytes"] == ent["tamanho_bytes"]
                and reg["sha256_estado_canonico"] == ent["sha256_estado_canonico"]
                and reg["hash_carteira_sha256_v1"] == ent["hash_carteira_sha256_v1"]
                and reg["hash_carteira_sha256_v2_canonico"] == ent["hash_carteira_sha256_v2_canonico"]
                and reg["sha256_matriz_incidencia_100"] == ent["sha256_matriz_incidencia_100"]
                and bool(reg["todas_travas_aprovadas"]) is True,
                f"Divergencia entre SQLite e manifesto assinado para '{cid}'.",
                IntegridadeCatalogoError,
            )
            try:
                reg["metadados_completos"] = json.loads(reg.pop("metadados_completos_json"))
            except Exception as exc:
                raise IntegridadeCatalogoError(
                    f"metadados_completos_json corrompido no SQLite para '{cid}': {exc}"
                ) from exc
            registros[cid] = reg

        if set(registros.keys()) != set(entradas_man.keys()):
            raise IntegridadeCatalogoError(
                "Conjunto de IDs no SQLite diverge do manifesto assinado."
            )
        return registros

    def _garantir_versao_atualizada(self) -> None:
        if self._estado_abertura is None or self._dir_versao_carregada is None:
            self._carregar_e_validar_versao()
            return

        precisa_reabrir = False
        if self._versao_fixa is None:
            caminho_ptr = os.path.join(self._dir_catalogo, "catalogo_ativo.json")
            try:
                sig_ptr_atual = extrair_assinatura_stat(os.lstat(caminho_ptr))
            except OSError as exc:
                raise CatalogoIndisponivelError(
                    f"Ponteiro catalogo_ativo.json inacessivel: {exc}"
                ) from exc
            if sig_ptr_atual != self._sig_stat_ponteiro:
                precisa_reabrir = True

        if not precisa_reabrir:
            caminho_man = os.path.join(self._dir_versao_carregada, "manifesto_catalogo.json")
            try:
                sig_man_atual = extrair_assinatura_stat(os.lstat(caminho_man))
            except OSError:
                precisa_reabrir = True
            else:
                if sig_man_atual != self._sig_stat_manifesto:
                    precisa_reabrir = True

        if precisa_reabrir:
            self._cache.limpar(contar_invalidacao=True)
            self._carregar_e_validar_versao()

    def _resolver_entrada(
        self,
        J: Any,
        seed: Optional[Any] = None,
        *,
        versao_algoritmo: Optional[str] = None,
        configuracao: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        if type(J) is not int or J < 2 or J > 10000 or J % 2 != 0:
            raise SolicitacaoForaDaGradeError(
                f"Porte J={J!r} rejeitado pela politica estrita: fora da grade catalogada {list(self._j_permitidos)}."
            )
        if J not in self._j_permitidos:
            raise SolicitacaoForaDaGradeError(
                f"Porte J={J} nao existe na grade catalogada {list(self._j_permitidos)}. "
                "Nenhuma composicao ou extrapolacao online e permitida."
            )

        versao_alg = versao_algoritmo if versao_algoritmo is not None else VERSAO_ALGORITMO_PADRAO
        if type(versao_alg) is not str or not versao_alg:
            raise SolicitacaoForaDaGradeError(
                f"versao_algoritmo invalida na consulta: {versao_alg!r}."
            )

        if configuracao is None:
            sha_cfg = SHA256_CONFIGURACAO_PADRAO_S1_1080K
        else:
            _, _, sha_cfg = calcular_sha256_configuracao(configuracao)

        if seed is None:
            candidatos = self._indice_por_versao_j_cfg.get((versao_alg, J, sha_cfg), [])
            if len(candidatos) == 1:
                return candidatos[0]
            if not candidatos:
                raise SolicitacaoForaDaGradeError(
                    f"Nenhuma carteira catalogada para (J={J}, versao_algoritmo={versao_alg!r}, sha256_configuracao={sha_cfg})."
                )
            seeds_disp = [c["seed"] for c in candidatos]
            raise SolicitacaoForaDaGradeError(
                f"Multiplas seeds disponiveis para J={J} ({seeds_disp}); informe `seed` explicitamente."
            )

        if type(seed) is not int:
            raise SolicitacaoForaDaGradeError(
                f"seed deve ser int exato na consulta (recebido {type(seed).__name__})."
            )

        entrada = self._indice_chave.get((versao_alg, J, seed, sha_cfg))
        if entrada is None:
            raise SolicitacaoForaDaGradeError(
                f"Carteira ausente da grade catalogada: J={J}, seed={seed}, "
                f"versao_algoritmo={versao_alg!r}, sha256_configuracao={sha_cfg}."
            )
        return entrada

    def listar_carteiras(self) -> List[Dict[str, Any]]:
        """Lista deterministica das entradas catalogadas na versao autenticada."""
        with self._lock:
            self._garantir_versao_atualizada()
            saida: List[Dict[str, Any]] = []
            for ent in self._entradas_ordenadas:
                cid = ent["id_carteira"]
                sql_reg = self._registros_sqlite_por_id[cid]
                saida.append(
                    {
                        "id_carteira": cid,
                        "versao_catalogo": self._versao_carregada,
                        "versao_algoritmo": ent["versao_algoritmo"],
                        "J": ent["J"],
                        "seed": ent["seed"],
                        "sha256_configuracao": ent["sha256_configuracao"],
                        "particao_relpath": ent["particao_relpath"],
                        "tamanho_bytes": ent["tamanho_bytes"],
                        "sha256_estado_canonico": ent["sha256_estado_canonico"],
                        "hash_carteira_sha256_v1": ent["hash_carteira_sha256_v1"],
                        "hash_carteira_sha256_v2_canonico": ent["hash_carteira_sha256_v2_canonico"],
                        "sha256_matriz_incidencia_100": ent["sha256_matriz_incidencia_100"],
                        "k_max": sql_reg["k_max"],
                        "phi2": sql_reg["phi2"],
                        "d_max": sql_reg["d_max"],
                        "P_gt_25": sql_reg["P_gt_25"],
                        "R_win": sql_reg["R_win"],
                        "todas_travas_aprovadas": bool(sql_reg["todas_travas_aprovadas"]),
                    }
                )
            return saida

    def obter_metadados_carteira(
        self,
        J: int,
        seed: Optional[int] = None,
        *,
        versao_algoritmo: Optional[str] = None,
        configuracao: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Retorna metadados e metricas autenticadas da carteira sem decodificar o binario."""
        with self._lock:
            self._garantir_versao_atualizada()
            ent = self._resolver_entrada(
                J, seed, versao_algoritmo=versao_algoritmo, configuracao=configuracao
            )
            cid = ent["id_carteira"]
            return {
                "versao_catalogo": self._versao_carregada,
                "entrada_manifesto": dict(ent),
                "indice_sqlite": dict(self._registros_sqlite_por_id[cid]),
            }

    def estatisticas_cache(self) -> Dict[str, Any]:
        with self._lock:
            stats = self._cache.estatisticas()
            stats["versao_catalogo"] = self._versao_carregada
            return stats

    def _carregar_bytes_particao_autenticados(
        self,
        entrada: Mapping[str, Any],
        *,
        ignorar_cache: bool = False,
    ) -> Tuple[bytes, bool]:
        exigir(
            self._dir_versao_carregada is not None and self._versao_carregada is not None,
            "Versao do catalogo nao inicializada.",
            CatalogoIndisponivelError,
        )
        caminho_particao = resolver_caminho_seguro_em_diretorio(
            self._dir_versao_carregada, entrada["particao_relpath"]
        )
        chave_cache = (self._versao_carregada, entrada["id_carteira"])

        if not ignorar_cache:
            item_cache = self._cache.obter(chave_cache)
            if item_cache is not None:
                try:
                    st_atual = os.lstat(caminho_particao)
                except OSError as exc:
                    self._cache.remover(chave_cache)
                    raise IntegridadeCatalogoError(
                        f"Particao em cache tornou-se inacessivel em disco: '{caminho_particao}': {exc}"
                    ) from exc
                sig_atual = extrair_assinatura_stat(st_atual)
                if sig_atual == item_cache["stat_sig"] and caminho_particao == item_cache["caminho_real"]:
                    self._cache.hits += 1
                    return item_cache["dados_bin"], True
                self._cache.remover(chave_cache)

        self._cache.misses += 1
        dados_bin, stat_sig = ler_arquivo_controlado_fd(
            caminho_particao, tamanho_esperado=entrada["tamanho_bytes"]
        )
        sha_real = hashlib.sha256(dados_bin).hexdigest()
        if sha_real != entrada["sha256_estado_canonico"]:
            self._cache.remover(chave_cache)
            raise IntegridadeCatalogoError(
                f"Adulteracao de particao binaria detectada em '{entrada['particao_relpath']}': "
                f"SHA-256 calculado ({sha_real}) diverge do manifesto autenticado ({entrada['sha256_estado_canonico']})."
            )

        if not ignorar_cache:
            self._cache.inserir(
                chave_cache,
                {
                    "dados_bin": dados_bin,
                    "tamanho_bytes": len(dados_bin),
                    "caminho_real": caminho_particao,
                    "stat_sig": stat_sig,
                    "sha256_estado_canonico": sha_real,
                },
            )
        return dados_bin, False

    def obter_carteira(
        self,
        J: int,
        seed: Optional[int] = None,
        *,
        versao_algoritmo: Optional[str] = None,
        configuracao: Optional[Mapping[str, Any]] = None,
        offset: int = 0,
        limit: Optional[int] = None,
        verificar_disco_sem_cache: bool = False,
    ) -> Dict[str, Any]:
        """
        Retorna os bilhetes autenticados (`List[List[int]]`) da carteira exata ou
        fatia paginada `[offset : offset + limit]` a partir de bytes autenticados.
        """
        if type(offset) is not int or offset < 0:
            raise ValueError(f"offset deve ser int >= 0 (recebido {offset!r}).")
        if limit is not None and (type(limit) is not int or limit < 1):
            raise ValueError(f"limit deve ser int >= 1 ou None (recebido {limit!r}).")

        with self._lock:
            self._garantir_versao_atualizada()
            entrada = self._resolver_entrada(
                J, seed, versao_algoritmo=versao_algoritmo, configuracao=configuracao
            )
            total_jogos = entrada["J"]
            if offset >= total_jogos:
                raise ValueError(
                    f"offset ({offset}) fora do intervalo [0, {total_jogos - 1}]."
                )
            fim = total_jogos if limit is None else min(total_jogos, offset + limit)

            dados_bin, cache_hit = self._carregar_bytes_particao_autenticados(
                entrada, ignorar_cache=verificar_disco_sem_cache
            )
            jogos = _decodificar_bloco_binario(dados_bin, offset, fim)

            return {
                "id_carteira": entrada["id_carteira"],
                "versao_catalogo": self._versao_carregada,
                "versao_algoritmo": entrada["versao_algoritmo"],
                "J": total_jogos,
                "seed": entrada["seed"],
                "sha256_configuracao": entrada["sha256_configuracao"],
                "sha256_estado_canonico": entrada["sha256_estado_canonico"],
                "hash_carteira_sha256_v1": entrada["hash_carteira_sha256_v1"],
                "hash_carteira_sha256_v2_canonico": entrada["hash_carteira_sha256_v2_canonico"],
                "sha256_matriz_incidencia_100": entrada["sha256_matriz_incidencia_100"],
                "offset": offset,
                "limit": limit,
                "total_jogos_carteira": total_jogos,
                "retornados": len(jogos),
                "cache_hit": cache_hit,
                "jogos": jogos,
            }

    def auditar_catalogo_completo(self) -> Dict[str, Any]:
        """
        Auditoria integral diretamente do disco (ignora RAM cache):
        1. Reexecuta verificacao aciclica Ed25519 + ancora + recibo + inventario.
        2. Recalcula SHA-256 integral de todas as particoes em disco.
        3. Reconstrui todos os bilhetes e reexecuta R1-R12 via `auditar_carteira_completa`
           plus paridade integral dos 4 hashes certificados.
        """
        from lotomania_carteira_10000.auditoria import auditar_carteira_completa
        from lotomania_carteira_10000.validacao import (
            BASELINE_ORDEM4_10000_REFERENCIA,
            calcular_hashes_certificados,
        )

        with self._lock:
            t0 = time.perf_counter()
            self._cache.limpar(contar_invalidacao=False)
            self._carregar_e_validar_versao()

            resultados_carteiras: List[Dict[str, Any]] = []
            for ent in self._entradas_ordenadas:
                dados_bin, cache_hit = self._carregar_bytes_particao_autenticados(
                    ent, ignorar_cache=True
                )
                exigir(
                    cache_hit is False,
                    "Auditoria integral exige leitura direta do disco sem RAM cache.",
                    IntegridadeCatalogoError,
                )
                jogos = _decodificar_bloco_binario(dados_bin, 0, ent["J"])
                hashes = calcular_hashes_certificados(
                    jogos,
                    seed=ent["seed"],
                    J=ent["J"],
                    max_tentativas_f3=ent["configuracao_canonica"]["max_tentativas_f3"],
                    versao_algoritmo=ent["versao_algoritmo"],
                )
                exigir(
                    hashes["sha256_estado_canonico"] == ent["sha256_estado_canonico"],
                    f"Divergencia em sha256_estado_canonico na auditoria de {ent['id_carteira']}.",
                    IntegridadeCatalogoError,
                )
                exigir(
                    hashes["hash_carteira_sha256_v1"] == ent["hash_carteira_sha256_v1"],
                    f"Divergencia em hash_carteira_sha256_v1 na auditoria de {ent['id_carteira']}.",
                    IntegridadeCatalogoError,
                )
                exigir(
                    hashes["hash_carteira_sha256_v2_canonico"] == ent["hash_carteira_sha256_v2_canonico"],
                    f"Divergencia em hash_carteira_sha256_v2_canonico na auditoria de {ent['id_carteira']}.",
                    IntegridadeCatalogoError,
                )
                exigir(
                    hashes["sha256_matriz_incidencia_100"] == ent["sha256_matriz_incidencia_100"],
                    f"Divergencia em sha256_matriz_incidencia_100 na auditoria de {ent['id_carteira']}.",
                    IntegridadeCatalogoError,
                )

                aud = auditar_carteira_completa(
                    jogos,
                    teto_kmax=35,
                    baseline_ordem4=(
                        BASELINE_ORDEM4_10000_REFERENCIA if ent["J"] == 10000 else None
                    ),
                )
                exigir(
                    aud["aprovacao_restricoes"]["todas_travas_aprovadas"] is True,
                    f"Falha em travas R1-R12 na auditoria de {ent['id_carteira']}: "
                    f"{aud['aprovacao_restricoes']}.",
                    IntegridadeCatalogoError,
                )

                resultados_carteiras.append(
                    {
                        "id_carteira": ent["id_carteira"],
                        "J": ent["J"],
                        "seed": ent["seed"],
                        "todas_travas_aprovadas": True,
                        "k_max": aud["fechamento"]["k_max"],
                        "phi2": aud["coocorrencia_4950"]["phi2"],
                        "d_max": aud["coocorrencia_4950"]["d_max"],
                        "P_gt_25": aud["fechamento"]["P_gt_25"],
                        "R_win": aud["fechamento"]["R_win"],
                        "hashes": hashes,
                    }
                )

            dt_ms = (time.perf_counter() - t0) * 1000.0
            return {
                "versao_catalogo": self._versao_carregada,
                "sha256_chave_publica": self._estado_abertura["sha256_chave_publica"],
                "sha256_manifesto": self._estado_abertura["sha256_manifesto"],
                "sha256_assinatura_sig": self._estado_abertura["sha256_assinatura_sig"],
                "sha256_indice_sqlite": self._estado_abertura["sha256_indice_sqlite"],
                "total_carteiras_auditadas": len(resultados_carteiras),
                "todas_aprovadas": True,
                "tempo_ms": dt_ms,
                "carteiras": resultados_carteiras,
            }


def abrir_catalogo(
    dir_catalogo: str = DIR_CATALOGO_PADRAO,
    *,
    caminho_chave_publica: Optional[str] = None,
    ancora_chave_publica_sha256: str = CHAVE_PUBLICA_CATALOGO_SHA256,
    versao_fixa: Optional[str] = None,
    max_cache_bytes: int = LIMITE_MAXIMO_CACHE_BYTES,
) -> Tuple[LeitorCatalogoLotomania, Dict[str, Any]]:
    """Cria e valida imediatamente um `LeitorCatalogoLotomania` fail-closed."""
    leitor = LeitorCatalogoLotomania(
        dir_catalogo=dir_catalogo,
        caminho_chave_publica=caminho_chave_publica,
        ancora_chave_publica_sha256=ancora_chave_publica_sha256,
        versao_fixa=versao_fixa,
        max_cache_bytes=max_cache_bytes,
    )
    info = leitor.abrir_catalogo()
    return leitor, info
