# -*- coding: utf-8 -*-
"""CLI operacional para publicacao, auditoria e benchmark do catalogo Lotomania 10.000."""

import argparse
import json
import statistics
import time
from typing import Any, Dict, List

from catalogo_lotomania_10000.canonicalizacao import CLAUSULA_OBRIGATORIA
from catalogo_lotomania_10000.leitor import (
    DIR_CATALOGO_PADRAO,
    LeitorCatalogoLotomania,
    abrir_catalogo,
)


def _executar_benchmark(dir_catalogo: str, repeticoes_paginadas: int = 20) -> Dict[str, Any]:
    t0 = time.perf_counter()
    leitor, info_abertura = abrir_catalogo(dir_catalogo=dir_catalogo)
    abertura_ms = (time.perf_counter() - t0) * 1000.0

    t1 = time.perf_counter()
    primeira_leitura = leitor.obter_carteira(10000, 330001)
    primeira_leitura_ms = (time.perf_counter() - t1) * 1000.0

    tempos_paginados_ms: List[float] = []
    for idx in range(repeticoes_paginadas):
        offset = (idx * 200) % 10000
        tp0 = time.perf_counter()
        pag = leitor.obter_carteira(10000, 330001, offset=offset, limit=200)
        tp1 = (time.perf_counter() - tp0) * 1000.0
        if not pag["cache_hit"] or pag["retornados"] != 200:
            raise RuntimeError("Leitura paginada esperada em cache_hit=True com 200 bilhetes.")
        tempos_paginados_ms.append(tp1)

    t_full_cached0 = time.perf_counter()
    leitura_cached_10000 = leitor.obter_carteira(10000, 330001)
    leitura_cached_10000_ms = (time.perf_counter() - t_full_cached0) * 1000.0

    stats_cache = leitor.estatisticas_cache()
    slos = {
        "abertura_ms": round(abertura_ms, 3),
        "abertura_slo_ms": 50.0,
        "abertura_ok": abertura_ms <= 50.0,
        "primeira_leitura_10000_sha256_ms": round(primeira_leitura_ms, 3),
        "primeira_leitura_slo_ms": 25.0,
        "primeira_leitura_ok": primeira_leitura_ms <= 25.0,
        "paginada_200_mediana_ms": round(statistics.median(tempos_paginados_ms), 4),
        "paginada_200_max_ms": round(max(tempos_paginados_ms), 4),
        "paginada_200_slo_ms": 5.0,
        "paginada_200_ok": max(tempos_paginados_ms) <= 5.0,
        "leitura_10000_em_cache_ms": round(leitura_cached_10000_ms, 3),
        "cache_bytes_em_uso": stats_cache["bytes_em_uso"],
        "cache_teto_bytes": stats_cache["max_cache_bytes"],
        "cache_teto_ok": stats_cache["bytes_em_uso"] <= 32 * 1024 * 1024,
        "primeira_leitura_cache_hit": primeira_leitura["cache_hit"],
        "leitura_cached_cache_hit": leitura_cached_10000["cache_hit"],
    }
    return {
        "clausula_obrigatoria": CLAUSULA_OBRIGATORIA,
        "abertura": info_abertura,
        "slos": slos,
        "cache_stats": stats_cache,
    }


def main(argv: Any = None) -> int:
    parser = argparse.ArgumentParser(
        description="CLI do catalogo imutavel Lotomania J=10.000."
    )
    parser.add_argument(
        "--dir-catalogo",
        default=DIR_CATALOGO_PADRAO,
        help="Diretorio raiz do catalogo.",
    )
    parser.add_argument(
        "--publicar-v1",
        action="store_true",
        help="Compila e publica atomicamente a versao oficial v1.0.0.",
    )
    parser.add_argument(
        "--chave-privada",
        default=None,
        help="Caminho externo opcional da chave privada Ed25519 para publicacao.",
    )
    parser.add_argument(
        "--auditar",
        action="store_true",
        help="Executa auditoria integral em disco (Ed25519 + SHA-256 + R1-R12).",
    )
    parser.add_argument(
        "--benchmark",
        action="store_true",
        help="Executa benchmark de SLOs (abertura, primeira leitura e paginada em cache).",
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Exibe status e inventario autenticado da versao ativa.",
    )

    args = parser.parse_args(argv)
    if not any([args.publicar_v1, args.auditar, args.benchmark, args.status]):
        parser.print_help()
        return 1

    saida: Dict[str, Any] = {}
    if args.publicar_v1:
        from catalogo_lotomania_10000.publicador import (
            CAMINHO_CHAVE_PRIVADA_PADRAO,
            publicar_v1_padrao_repositorio,
        )

        chave = args.chave_privada or CAMINHO_CHAVE_PRIVADA_PADRAO
        saida["publicacao_v1"] = publicar_v1_padrao_repositorio(
            dir_catalogo=args.dir_catalogo,
            caminho_chave_privada=chave,
        )

    if args.status:
        leitor, info = abrir_catalogo(dir_catalogo=args.dir_catalogo)
        saida["status"] = {
            "abertura": info,
            "carteiras": leitor.listar_carteiras(),
            "cache": leitor.estatisticas_cache(),
        }

    if args.auditar:
        leitor = LeitorCatalogoLotomania(dir_catalogo=args.dir_catalogo)
        saida["auditoria_completa"] = leitor.auditar_catalogo_completo()

    if args.benchmark:
        saida["benchmark"] = _executar_benchmark(args.dir_catalogo)

    print(json.dumps(saida, indent=2, sort_keys=True, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
