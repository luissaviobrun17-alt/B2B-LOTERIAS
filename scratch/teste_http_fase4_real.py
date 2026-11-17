# -*- coding: utf-8 -*-
"""
TESTES PRÁTICOS EM TEMPO DE EXECUÇÃO: CAMADA HTTP (FASE 4)
==========================================================
Bateria de testes reais contra o daemon FastAPI ativo em http://127.0.0.1:8000.
Validação de integridade, paginação, hashes canônicos, latência e governança
para as carteiras canônicas J=1.000 e J=2.000.
"""

from __future__ import annotations

import hashlib
import json
import statistics
import time
from typing import Any, Dict, List, Tuple
import urllib.error
import urllib.request

BASE_URL = "http://127.0.0.1:8000/api/v1/lotofacil-catalogo"

HASH_CANONICO_J1000 = "891c598a23399d0efad1d8f84e44e89559603f1f15a5481206e9be417b86d153"
HASH_CANONICO_J2000 = "baf528336b7d935d91262705560c9d7410c8c76987f8a0eddbde82bf5aa93048"
HASH_FISICO_J2000 = "42946f9e8915e55d22fb7c83e7b78ebac5e8241e84dadb610403292051ebdfb1"
HASH_DOC_J2000 = "25bcad7073ba690c00692317c22f91616f752f2046b2c0825987372cc1716b4b"


def requisitar(url: str, method: str = "GET", data: bytes = None) -> Tuple[int, Dict[str, Any], float]:
    t0 = time.perf_counter()
    req = urllib.request.Request(url, data=data, method=method)
    try:
        with urllib.request.urlopen(req, timeout=10.0) as resp:
            duracao_ms = (time.perf_counter() - t0) * 1000.0
            body = resp.read()
            return int(resp.status), json.loads(body.decode("utf-8")), duracao_ms
    except urllib.error.HTTPError as err:
        duracao_ms = (time.perf_counter() - t0) * 1000.0
        body = err.read()
        try:
            parsed = json.loads(body.decode("utf-8"))
        except Exception:
            parsed = {"raw": body.decode("utf-8", errors="replace")}
        return int(err.code), parsed, duracao_ms


def main():
    print("=" * 80)
    print("INICIANDO TESTES HTTP PRÁTICOS (FASE 4) - SERVIDOR ATIVO NA PORTA 8000")
    print("=" * 80)

    # 1. Teste Status Geral e Governança J=1000
    status, d1000, lat1 = requisitar(f"{BASE_URL}/status")
    assert status == 200, f"Falha status 1000: {status}"
    assert d1000["sucesso"] is True
    assert d1000["quantidade_jogos"] == 1000
    assert d1000["governanca"]["estado_operacional"] == "OFF_STANDBY"
    assert d1000["governanca"]["feature_flag"] == "LOTOFACIL_MODO4_ATIVO"
    assert d1000["governanca"]["em_producao"] is False
    assert d1000["governanca"]["integridade_confirmada"] is True
    assert "1000" in d1000["governanca"]["carteiras_disponiveis"]
    assert "2000" in d1000["governanca"]["carteiras_disponiveis"]
    print(f"[OK] 1. Status Geral e Governança J=1.000: HTTP {status} ({lat1:.2f} ms)")

    # 2. Teste Status Geral J=2000
    status, d2000, lat2 = requisitar(f"{BASE_URL}/status?tamanho=2000")
    assert status == 200, f"Falha status 2000: {status}"
    assert d2000["sucesso"] is True
    assert d2000["catalogo"] == "LOTOFACIL_MODO4_J2000_CANONICA"
    assert d2000["quantidade_jogos"] == 2000
    assert d2000["auditoria_resumida"]["integro"] is True
    assert d2000["auditoria_resumida"]["hash_fisico_valido"] is True
    assert d2000["auditoria_resumida"]["hash_jogos_valido"] is True
    print(f"[OK] 2. Status Canônico J=2.000: HTTP {status} ({lat2:.2f} ms)")

    # 3. Teste Metadados J=2000
    status, meta2000, lat3 = requisitar(f"{BASE_URL}/metadados?tamanho=2000")
    assert status == 200, f"Falha metadados 2000: {status}"
    assert meta2000["identificador"] == "LOTOFACIL_MODO4_J2000_CANONICA"
    assert meta2000["semente_utilizada"] == 2027
    assert meta2000["b_cand_utilizado"] == 32
    assert meta2000["orcamento_max_avaliacoes"] == 64000
    assert meta2000["sha256_jogos_canonicos"] == HASH_CANONICO_J2000
    assert meta2000["sha256_documento_catalogo"] == HASH_DOC_J2000
    mq = meta2000["metricas_qualidade"]
    assert mq["duplicatas"] == 0
    assert mq["unicidade_pct"] == 100.0
    assert mq["quadras_cobertas"] == 12650
    assert mq["cobertura_t4_pct"] == 100.0
    assert mq["ss_minimo"] == 0.0
    assert mq["ss_observado"] == 30.0
    assert mq["maior_sequencia_consecutiva"] == 6
    assert mq["jogos_seq_ge_7"] == 0
    assert abs(mq["funcao_objetivo_F"] - 0.970246481147) < 1e-6
    tv = meta2000["tripla_validacao"]
    assert tv["aprovado_tolerancia_1e12"] is True
    assert tv["divergencia_e4_e2"] <= 1e-12
    assert tv["divergencia_e4_ref"] <= 1e-12
    print(f"[OK] 3. Metadados e Tripla Validação J=2.000: HTTP {status} ({lat3:.2f} ms)")

    # 4. Teste Paginação Inicial (offset 0, limit 50)
    status, pag_ini, lat4 = requisitar(f"{BASE_URL}/jogos?tamanho=2000&offset=0&limit=50")
    assert status == 200, f"Falha pag inicial: {status}"
    assert pag_ini["total_jogos"] == 2000
    assert pag_ini["retornados"] == 50
    assert pag_ini["offset"] == 0
    assert pag_ini["limit"] == 50
    assert len(pag_ini["jogos"]) == 50
    assert pag_ini["jogos"][0] == [1, 2, 3, 4, 5, 6, 8, 9, 10, 11, 12, 14, 15, 16, 18]
    print(f"[OK] 4. Paginação Inicial J=2.000 [0:50]: HTTP {status} ({lat4:.2f} ms)")

    # 5. Teste Paginação Intermediária (offset 950, limit 100)
    status, pag_mid, lat5 = requisitar(f"{BASE_URL}/jogos?tamanho=2000&offset=950&limit=100")
    assert status == 200, f"Falha pag mid: {status}"
    assert pag_mid["retornados"] == 100
    assert pag_mid["offset"] == 950
    print(f"[OK] 5. Paginação Intermediária J=2.000 [950:1050]: HTTP {status} ({lat5:.2f} ms)")

    # 6. Teste Paginação Final (offset 1950, limit 50)
    status, pag_fim, lat6 = requisitar(f"{BASE_URL}/jogos?tamanho=2000&offset=1950&limit=50")
    assert status == 200, f"Falha pag final: {status}"
    assert pag_fim["retornados"] == 50
    assert pag_fim["offset"] == 1950
    assert len(pag_fim["jogos"]) == 50
    print(f"[OK] 6. Paginação Final J=2.000 [1950:2000]: HTTP {status} ({lat6:.2f} ms)")

    # 7. Teste de Imutabilidade Total dos 2.000 Jogos via HTTP (limit=2000)
    status, todos_jogos, lat7 = requisitar(f"{BASE_URL}/jogos?tamanho=2000&offset=0&limit=2000")
    assert status == 200, f"Falha entrega total: {status}"
    assert todos_jogos["total_jogos"] == 2000
    assert todos_jogos["retornados"] == 2000
    jogos_recebidos = todos_jogos["jogos"]
    assert len(jogos_recebidos) == 2000

    # Verificação de regras da Caixa para todos os 2000 jogos
    jogos_set = set()
    for idx, jg in enumerate(jogos_recebidos):
        assert len(jg) == 15, f"Jogo {idx} tem tamanho {len(jg)}"
        assert all(1 <= d <= 25 for d in jg), f"Jogo {idx} dezenas invalidas"
        assert len(set(jg)) == 15, f"Jogo {idx} tem dezenas repetidas"
        jogos_set.add(tuple(jg))
    assert len(jogos_set) == 2000, "Detectada duplicata nos jogos entregues via HTTP!"

    # Cálculo do hash canônico exato dos dados retornados pela API
    serializacao = json.dumps(jogos_recebidos, separators=(",", ":"))
    hash_recebido = hashlib.sha256(serializacao.encode("utf-8")).hexdigest()
    assert hash_recebido == HASH_CANONICO_J2000, f"Divergência hash canônico HTTP: {hash_recebido} != {HASH_CANONICO_J2000}"
    print(f"[OK] 7. Imutabilidade e Hash Canônico dos 2.000 Jogos via HTTP: {hash_recebido} ({lat7:.2f} ms)")

    # 8. Teste Auditoria em Tempo Real J=2000
    status, aud2000, lat8 = requisitar(f"{BASE_URL}/auditoria?tamanho=2000")
    assert status == 200, f"Falha auditoria 2000: {status}"
    assert aud2000["sucesso"] is True
    aud_detalhe = aud2000["auditoria"]
    assert aud_detalhe["arquivo_existe"] is True
    assert aud_detalhe["hash_fisico_valido"] is True
    assert aud_detalhe["hash_jogos_valido"] is True
    assert aud_detalhe["hash_documento_valido"] is True
    assert aud_detalhe["total_jogos"] == 2000
    assert aud_detalhe["jogos_unicos"] == 2000
    assert aud_detalhe["status_geral"] == "INTEGRO"
    print(f"[OK] 8. Auditoria Criptográfica em Tempo Real J=2.000: HTTP {status} ({lat8:.2f} ms)")

    # 9. Testes de Validação de Limites e Erros de Domínio
    # 9a. Offset fora do domínio para J=2000
    st_err1, _, _ = requisitar(f"{BASE_URL}/jogos?tamanho=2000&offset=2000")
    assert st_err1 == 422, f"Esperado 422 para offset 2000, obtido {st_err1}"

    # 9b. Limit zero
    st_err2, _, _ = requisitar(f"{BASE_URL}/jogos?tamanho=2000&limit=0")
    assert st_err2 == 422, f"Esperado 422 para limit 0, obtido {st_err2}"

    # 9c. Tamanho não suportado
    st_err3, _, _ = requisitar(f"{BASE_URL}/jogos?tamanho=3000")
    assert st_err3 == 422, f"Esperado 422 para tamanho 3000, obtido {st_err3}"
    print("[OK] 9. Validação de Fronteiras e Erros de Domínio (422) aprovada com sucesso.")

    # 10. Benchmark de Latência HTTP Real (20 requisições consecutivas para J=1000 e J=2000)
    latencias_1000 = []
    for _ in range(20):
        _, _, lat = requisitar(f"{BASE_URL}/jogos?tamanho=1000&offset=0&limit=100")
        latencias_1000.append(lat)

    latencias_2000 = []
    for _ in range(20):
        _, _, lat = requisitar(f"{BASE_URL}/jogos?tamanho=2000&offset=0&limit=100")
        latencias_2000.append(lat)

    latencias_2000_full = []
    for _ in range(20):
        _, _, lat = requisitar(f"{BASE_URL}/jogos?tamanho=2000&offset=0&limit=2000")
        latencias_2000_full.append(lat)

    med_1000 = statistics.mean(latencias_1000)
    med_2000 = statistics.mean(latencias_2000)
    med_2000_full = statistics.mean(latencias_2000_full)

    print("-" * 80)
    print("BENCHMARK DE LATÊNCIA HTTP REAL (20 REPETIÇÕES):")
    print(f"  - J=1.000 (100 bilhetes): média {med_1000:.2f} ms (min {min(latencias_1000):.2f} ms, max {max(latencias_1000):.2f} ms)")
    print(f"  - J=2.000 (100 bilhetes): média {med_2000:.2f} ms (min {min(latencias_2000):.2f} ms, max {max(latencias_2000):.2f} ms)")
    print(f"  - J=2.000 (2.000 bilhetes): média {med_2000_full:.2f} ms (min {min(latencias_2000_full):.2f} ms, max {max(latencias_2000_full):.2f} ms)")
    print("-" * 80)
    print("TODOS OS TESTES PRÁTICOS HTTP DA FASE 4 FORAM APROVADOS COM SUCESSO!")
    print("=" * 80)


if __name__ == "__main__":
    main()
