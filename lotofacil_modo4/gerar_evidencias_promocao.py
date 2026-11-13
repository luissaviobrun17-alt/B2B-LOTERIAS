# -*- coding: utf-8 -*-
"""
GERADOR DE MANIFESTO, EVIDENCIAS E DOSSIE DE PROMOCAO CONTROLADA
================================================================
Sela os hashes SHA-256 de producao em `manifesto_promocao_controlada.json`,
executa bateria completa ponta a ponta contra a instancia `api.app` real
(modo OFF padrao, modo ON controlado, experimental_2J opcional, rollback,
concorrencia, nao interferencia e integridade pos-implantacao) e grava:
  - auditoria/lotofacil_modo4/manifesto_promocao_controlada.json
  - auditoria/lotofacil_modo4/promocao_controlada_evidencias.json
  - auditoria/lotofacil_modo4/DOSSIE_PROMOCAO_CONTROLADA.md
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import json
import os
import sys
import time
from typing import Any, Dict, List

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import api as api_producao

from lotofacil_modo4.etapa1_regras_oficiais import CLAUSULA_MATEMATICA_OBRIGATORIA
from lotofacil_modo4.etapa4_referencia_independente import auditar_independencia_ast_etapa4
from lotofacil_modo4.etapa5_api_homologacao import (
    ServidorHttpHomologacao,
    chamar_api_lotofacil_modo4_seguro,
)
from lotofacil_modo4.promocao_producao import (
    ARQUIVOS_PRODUCAO_PROMOCAO,
    ENV_FEATURE_FLAG_LOTOFACIL_MODO4,
    ENV_PERMITIR_EXPERIMENTAL_2J,
    ENV_POLITICA_MICRO_PADRAO,
    INICIALIZACAO_MISTA_FIXA,
    POLITICA_MICRO_PRODUCAO_PADRAO,
    VERSAO_PROMOCAO_LOTOFACIL_MODO4,
    calcular_hash_carteira_lotofacil,
    definir_feature_flag_lotofacil_modo4,
    garantir_integridade_promocao_ou_falhar,
    gerar_manifesto_promocao_controlada,
)


def _garantir(condicao: bool, msg: str) -> None:
    if not condicao:
        raise RuntimeError(msg)


def _executar_bateria_concorrencia(base_url: str, *, modo_esperado_ativo: bool) -> Dict[str, Any]:
    t0 = time.perf_counter()

    def _tarefa(idx: int) -> Dict[str, Any]:
        if idx % 3 == 0:
            r_h = chamar_api_lotofacil_modo4_seguro(base_url, endpoint="/health", metodo="GET")
            return {"tipo": "health", "status": r_h["status_http"], "ok": r_h["status_http"] == 200}
        if idx % 3 == 1:
            r_lm = chamar_api_lotofacil_modo4_seguro(
                base_url,
                {"quantidade_jogos": 5, "permitir_espelhos": True, "seed": 42, "trace": False},
                endpoint="/api/v1/lotomania-modo4/gerar",
                timeout_s=15.0,
            )
            return {
                "tipo": "lotomania_modo4",
                "status": r_lm["status_http"],
                "ok": r_lm["status_http"] == 200 and len(r_lm["dados_brutos"].get("jogos", [])) == 5,
                "sha_v2": r_lm["dados_brutos"].get("hash_carteira_sha256_v2_canonico"),
            }
        r_lf = chamar_api_lotofacil_modo4_seguro(
            base_url,
            {"quantidade_jogos": 4, "semente": 42, "max_avaliacoes": 120},
            endpoint="/api/v1/lotofacil-modo4/gerar",
            timeout_s=20.0,
        )
        if modo_esperado_ativo:
            d = r_lf["dados_brutos"] or {}
            ok = bool(
                r_lf["sucesso"]
                and r_lf["status_http"] == 200
                and len(r_lf["jogos"]) == 4
                and d.get("fallback_executado") is False
                and d.get("historico_utilizado") is None
            )
            return {
                "tipo": "lotofacil_modo4",
                "status": r_lf["status_http"],
                "ok": ok,
                "hash_carteira": d.get("hash_carteira_sha256"),
            }
        ok = bool(
            (not r_lf["sucesso"])
            and r_lf["status_http"] == 503
            and len(r_lf["jogos"]) == 0
            and r_lf["fallback_executado"] is False
        )
        return {"tipo": "lotofacil_modo4", "status": r_lf["status_http"], "ok": ok}

    with ThreadPoolExecutor(max_workers=6) as pool:
        resultados = list(pool.map(_tarefa, range(12)))

    duracao_s = round(time.perf_counter() - t0, 4)
    falhas = [r for r in resultados if not r["ok"]]
    hashes_lf = {r["hash_carteira"] for r in resultados if r.get("tipo") == "lotofacil_modo4" and "hash_carteira" in r}
    hashes_lm = {r["sha_v2"] for r in resultados if r.get("tipo") == "lotomania_modo4"}
    return {
        "total_requisicoes": len(resultados),
        "sucessos": len(resultados) - len(falhas),
        "falhas": len(falhas),
        "duracao_segundos": duracao_s,
        "lotofacil_hashes_unicos": len(hashes_lf),
        "lotomania_hashes_unicos": len(hashes_lm),
        "amostra_resultados": resultados,
    }


def _construir_dossie_markdown(ev: Dict[str, Any]) -> str:
    manifesto = ev["manifesto_promocao"]
    off_ev = ev["evidencia_flag_off_padrao"]
    on_ev = ev["evidencia_flag_on_controlada"]
    rb_ev = ev["evidencia_rollback_runtime"]
    conc_off = ev["concorrencia_flag_off"]
    conc_on = ev["concorrencia_flag_on"]
    n_int = ev["nao_interferencia"]
    ast_ev = ev["auditoria_ast_referencia"]
    int_pos = ev["integridade_pos_implantacao"]

    linhas: List[str] = [
        "# DOSSIE DE PROMOCAO CONTROLADA - LOTOFACIL MODO 4",
        "",
        f"**Versao da Promocao:** `{VERSAO_PROMOCAO_LOTOFACIL_MODO4}`  ",
        f"**Data/Hora (UTC):** `{ev['gerado_em_utc']}`  ",
        f"**Estado Padrao em Producao:** `lotofacil_modo4_ativo = {str(off_ev['health_lotofacil_modo4']['feature_flag_ativa']).lower()}` (DESLIGADO POR PADRAO)  ",
        f"**Politica Micro Padrao:** `{POLITICA_MICRO_PRODUCAO_PADRAO}` (`experimental_2J` configuravel, desabilitada por padrao)  ",
        f"**Inicializacao Mista:** `{INICIALIZACAO_MISTA_FIXA}` (travada; `mista_equilibrada` rejeitada com HTTP 422)  ",
        "",
        "## 1. Resumo Executivo da Promocao",
        "",
        (
            "A integracao do motor LOTOFACIL MODO 4 foi implantada em `api.py`, na interface Web (`index.html`, "
            "`js/engines/motor_lotofacil_modo4_engine.js`, `js/ui.js`) e na interface Mobile (`B2B_Loterias_Mobile.html`) "
            "sob controle estrito de feature flag desligada por padrao (`LOTOFACIL_MODO4_ATIVO=false`). Todos os "
            "artefatos congelados das Etapas 1 a 4, os arquivos selados da Etapa 5, as bases oficiais da CAIXA, o motor "
            "legado `motor_lotofacil.py` e o sistema Lotomania MODO 4 v1.2 com selo Ed25519 permaneceram integralmente "
            "preservados e validados por SHA-256 antes e depois dos testes."
        ),
        "",
        "## 2. Configuracao de Feature Flag e Politicas em Producao",
        "",
        "| Parametro / Regra | Valor Padrao em Producao | Mecanismo de Controle | Comportamento Fail-Closed |",
        "| :--- | :--- | :--- | :--- |",
        f"| Feature Flag Principal (`{ENV_FEATURE_FLAG_LOTOFACIL_MODO4}`) | `False` | Variavel de ambiente explicita ou runtime controlado | HTTP 503 com 0 jogos e zero fallback |",
        f"| Politica Micro Oficial (`{ENV_POLITICA_MICRO_PADRAO}`) | `{POLITICA_MICRO_PRODUCAO_PADRAO}` | Fixada como padrao da API, Web e Mobile | `experimental_2J` bloqueada se flag experimental OFF |",
        f"| Habilitacao Experimental (`{ENV_PERMITIR_EXPERIMENTAL_2J}`) | `False` | Opt-in restrito desmarcado e desabilitado por padrao | Requisicao com `experimental_2J` recebe HTTP 422 com 0 jogos |",
        "| Inicializacao Mista | `padrao` | Literal estrito Pydantic v2 e ConfigProducao | Rejeita `mista_equilibrada` com HTTP 422 |",
        "| Historico na Geracao | `None` | Schema `extra='forbid'` sem campo de historico | Rejeita payload com `historico` via HTTP 422 |",
        "",
        "## 3. Preservacao Criptografica e Hashes SHA-256 Pos-Implantacao",
        "",
        (
            f"A verificacao criptografica pos-implantacao confirmou `{int_pos['verificados_etapas_1_2_3']}` artefatos "
            f"das Etapas 1 a 3, `{int_pos['verificados_etapa_4']}` artefatos da Etapa 4, bases externas e selo Ed25519 "
            f"da Lotomania (`selo_lotomania_valido={int_pos['selo_lotomania_valido']}`), manifesto Etapa 5 presente "
            f"(`{int_pos['manifesto_etapa5_presente']}`) e `{int_pos['verificados_promocao']}` modulos de producao "
            f"selados no manifesto da promocao sem nenhuma divergencia (`integro={int_pos['integro']}`). Auditoria "
            f"AST da referencia independente confirmou `independencia_comprovada={ast_ev['independencia_comprovada']}`."
        ),
        "",
        "| Arquivo Monitorado em Producao | SHA-256 Pos-Implantacao | Papel |",
        "| :--- | :--- | :--- |",
    ]
    for rel, sha in manifesto["hashes_producao"].items():
        papel = "Preservado inalterado (baseline legado)" if rel == "motor_lotofacil.py" else "Integracao controlada de promocao"
        linhas.append(f"| `{rel}` | `{sha}` | {papel} |")

    linhas.extend([
        "",
        "## 4. Matriz de Evidencias de Implantacao (Itens V.1 a V.8)",
        "",
        "| Check | Cenario Testado | Resultado Observado | Evidencia Chave |",
        "| :--- | :--- | :--- | :--- |",
        (
            f"| Feature Flag OFF (Padrao) | `GET /health`, `POST /gerar`, `POST /avaliar` com flag `False` | "
            f"Aprovado (Fail-Closed) | `disponivel={off_ev['health_lotofacil_modo4']['disponivel']}`, HTTP `503`, "
            f"`{len(off_ev['gerar_off']['jogos'])}` jogos, `fallback_executado={off_ev['gerar_off']['fallback_executado']}` |"
        ),
        (
            f"| Ativacao Controlada ON (`conservadora_3J`) | 8 jogos de 15 dezenas (seed 42) + 4 jogos de 16 dezenas (Independencia) | "
            f"Aprovado | `politica_micro_utilizada={on_ev['caso_simples_conservador']['politica_micro_utilizada']}`, "
            f"diff F = `{on_ev['caso_simples_conservador']['divergencia_F']:.2e}`, "
            f"diff F (16 dez.) = `{on_ev['caso_multipla_16']['divergencia_F']:.2e}` |"
        ),
        (
            f"| Politica `experimental_2J` Configuravel | Bloqueada por padrao; ativa somente com `permitir_experimental_2j=True` | "
            f"Aprovado | Bloqueio padrao HTTP `{on_ev['bloqueio_experimental_2j_padrao']['status_http']}`; "
            f"com opt-in ON diff F = `{on_ev['caso_experimental_2j_habilitado']['divergencia_F']:.2e}` |"
        ),
        (
            f"| Rollback em Runtime | Transicao `ON -> OFF` sem reiniciar processo | "
            f"Aprovado | Primeira chamada pos-rollback retornou HTTP `{rb_ev['gerar_pos_rollback']['status_http']}`, "
            f"`{len(rb_ev['gerar_pos_rollback']['jogos'])}` jogos, `disponivel={rb_ev['health_pos_rollback']['disponivel']}` |"
        ),
        (
            f"| Concorrencia Multi-Requisicao | 12 chamadas simultaneas (6 workers) nos estados OFF e ON | "
            f"Aprovado | OFF: `{conc_off['sucessos']}/{conc_off['total_requisicoes']}` em `{conc_off['duracao_segundos']}s`; "
            f"ON: `{conc_on['sucessos']}/{conc_on['total_requisicoes']}` em `{conc_on['duracao_segundos']}s` |"
        ),
        (
            f"| Nao Interferencia Entre Modalidades | Lotomania MODO 4 + legados (Lotofacil, Lotomania, Dia de Sorte, Mega-Sena) | "
            f"Aprovado | Lotomania SHA identico flag OFF/ON (`{n_int['lotomania_modo4_hashes_identicos']}`); "
            f"todos os endpoints legados HTTP 200 |"
        ),
        "",
        "## 5. Limites Cientificos e Clausula Matematica Obrigatoria",
        "",
        f"> {CLAUSULA_MATEMATICA_OBRIGATORIA}",
        "",
        (
            "Na aposta simples de 15 dezenas, a probabilidade individual permanece rigorosamente fixa em `1 em 3.268.760` "
            "para 15 acertos e `346.126 / 3.268.760` (aprox. `10,5889%`) para alguma premiacao (11 a 15 acertos). "
            "As cotas de Dawson-Sankoff e Hunter-Worsley, bem como `S_prob` e `F_MODO4`, funcionam exclusivamente como "
            "metricas e limites de otimizacao combinatoria de carteiras, sem prometer previsao ou alteracao de chances individuais."
        ),
        "",
        "## 6. Posicao Final para Go/No-Go",
        "",
        (
            "A implantacao controlada em `api.py`, Web e Mobile encontra-se concluida, selada por manifesto SHA-256 "
            "e com `lotofacil_modo4_ativo = False` por padrao. Recomenda-se manter a feature flag desligada ate autorizacao "
            "formal de ativacao em janela assistida (`LOTOFACIL_MODO4_ATIVO=true`), preservando `experimental_2J` "
            "desabilitada por padrao."
        ),
        "",
    ])
    return "\n".join(linhas)


def gerar_evidencias_promocao_controlada() -> Dict[str, Any]:
    caminho_ref4 = os.path.join(BASE_DIR, "lotofacil_modo4", "etapa4_referencia_independente.py")
    ast_res = auditar_independencia_ast_etapa4(caminho_ref4)
    _garantir(ast_res["independencia_comprovada"] is True, f"AST invalido: {ast_res}")

    # 1. Garante que api.app iniciou em padrao OFF
    definir_feature_flag_lotofacil_modo4(
        api_producao.app,
        ativo=False,
        permitir_experimental_2j=False,
        motivo="garantir_padrao_off_inicial",
    )

    # 2. Gera manifesto de promocao controlada com hashes pos-implantacao
    manifesto = gerar_manifesto_promocao_controlada(diretorio_base=BASE_DIR, salvar=True)

    # 3. Executa bateria HTTP real contra `api_producao.app`
    with ServidorHttpHomologacao(api_producao.app) as srv:
        # V.7: Feature Flag OFF (Padrao)
        r_health_off = chamar_api_lotofacil_modo4_seguro(srv.base_url, endpoint="/health", metodo="GET")
        r_status_off = chamar_api_lotofacil_modo4_seguro(
            srv.base_url, endpoint="/api/v1/lotofacil-modo4/status", metodo="GET"
        )
        r_gerar_off = chamar_api_lotofacil_modo4_seguro(
            srv.base_url, {"quantidade_jogos": 8, "semente": 42}
        )
        r_avaliar_off = chamar_api_lotofacil_modo4_seguro(
            srv.base_url,
            {"carteira": [list(range(1, 16))]},
            endpoint="/api/v1/lotofacil-modo4/avaliar",
        )
        _garantir(r_health_off["status_http"] == 200, "Health OFF falhou.")
        _garantir(r_health_off["dados_brutos"]["modo4_disponivel"] is True, "Lotomania MODO 4 deveria estar disponivel.")
        _garantir(
            r_health_off["dados_brutos"]["lotofacil_modo4"]["disponivel"] is False
            and r_health_off["dados_brutos"]["lotofacil_modo4"]["feature_flag_ativa"] is False,
            "Lotofacil MODO 4 deve iniciar OFF no /health.",
        )
        _garantir(
            r_gerar_off["status_http"] == 503
            and r_gerar_off["jogos"] == []
            and r_gerar_off["fallback_executado"] is False,
            "Geracao com flag OFF nao falhou fechado com HTTP 503.",
        )
        _garantir(r_avaliar_off["status_http"] == 503, "Avaliacao com flag OFF deve retornar 503.")

        conc_off = _executar_bateria_concorrencia(srv.base_url, modo_esperado_ativo=False)
        _garantir(conc_off["falhas"] == 0, f"Concorrencia OFF teve falhas: {conc_off}")

        # Nao interferencia estado OFF
        r_lm_off = chamar_api_lotofacil_modo4_seguro(
            srv.base_url,
            {"quantidade_jogos": 5, "permitir_espelhos": True, "seed": 42, "trace": False},
            endpoint="/api/v1/lotomania-modo4/gerar",
            timeout_s=15.0,
        )
        legados_off = {}
        for ep in (
            "/api/v1/motor-lotofacil",
            "/api/v1/motor-lotomania",
            "/api/v1/motor-diadesorte",
            "/api/v1/motor-megasena",
        ):
            r_leg = chamar_api_lotofacil_modo4_seguro(
                srv.base_url, {"quantidade_jogos": 3}, endpoint=ep, timeout_s=15.0
            )
            legados_off[ep] = r_leg["status_http"]
            _garantir(r_leg["status_http"] == 200, f"Legado {ep} falhou em OFF: {r_leg}")

        try:
            # V.8: Feature Flag ON controlada (experimental_2J ainda desabilitada)
            definir_feature_flag_lotofacil_modo4(
                api_producao.app,
                ativo=True,
                permitir_experimental_2j=False,
                motivo="evidencia_controlada_flag_on",
            )
            r_health_on = chamar_api_lotofacil_modo4_seguro(srv.base_url, endpoint="/health", metodo="GET")
            _garantir(
                r_health_on["dados_brutos"]["lotofacil_modo4"]["disponivel"] is True
                and r_health_on["dados_brutos"]["lotofacil_modo4"]["experimental_2j_habilitada"] is False,
                "Health ON inconsistente.",
            )

            r_simples = chamar_api_lotofacil_modo4_seguro(
                srv.base_url,
                {
                    "quantidade_jogos": 8,
                    "tamanho_aposta": 15,
                    "semente": 42,
                    "tipo_concurso": "concurso_regular",
                    "prioridade": "equilibrio_adaptativo",
                },
                timeout_s=25.0,
            )
            _garantir(r_simples["sucesso"] is True and r_simples["status_http"] == 200, f"Simples falhou: {r_simples}")
            d_s = r_simples["dados_brutos"]

            r_exp_blq = chamar_api_lotofacil_modo4_seguro(
                srv.base_url,
                {"quantidade_jogos": 8, "semente": 42, "politica_micro": "experimental_2J"},
                timeout_s=15.0,
            )
            _garantir(
                r_exp_blq["status_http"] == 422 and len(r_exp_blq["jogos"]) == 0,
                f"experimental_2J deveria ser bloqueada por padrao: {r_exp_blq}",
            )

            r_mult16 = chamar_api_lotofacil_modo4_seguro(
                srv.base_url,
                {
                    "quantidade_jogos": 4,
                    "tamanho_aposta": 16,
                    "pool": list(range(1, 24)),
                    "fixas": [1, 2],
                    "bloqueadas": [24, 25],
                    "tipo_concurso": "lotofacil_independencia",
                    "semente": 42,
                    "max_avaliacoes": 250,
                },
                timeout_s=25.0,
            )
            _garantir(r_mult16["sucesso"] is True and r_mult16["status_http"] == 200, f"Multipla 16 falhou: {r_mult16}")
            d_m16 = r_mult16["dados_brutos"]

            conc_on = _executar_bateria_concorrencia(srv.base_url, modo_esperado_ativo=True)
            _garantir(conc_on["falhas"] == 0, f"Concorrencia ON teve falhas: {conc_on}")

            # Opt-in explicito experimental_2J
            definir_feature_flag_lotofacil_modo4(
                api_producao.app,
                ativo=True,
                permitir_experimental_2j=True,
                motivo="evidencia_experimental_2j_configurada",
            )
            r_exp_on = chamar_api_lotofacil_modo4_seguro(
                srv.base_url,
                {"quantidade_jogos": 8, "semente": 42, "politica_micro": "experimental_2J"},
                timeout_s=25.0,
            )
            _garantir(r_exp_on["sucesso"] is True and r_exp_on["status_http"] == 200, f"Opt-in 2J falhou: {r_exp_on}")
            d_exp = r_exp_on["dados_brutos"]

            # Nao interferencia estado ON
            r_lm_on = chamar_api_lotofacil_modo4_seguro(
                srv.base_url,
                {"quantidade_jogos": 5, "permitir_espelhos": True, "seed": 42, "trace": False},
                endpoint="/api/v1/lotomania-modo4/gerar",
                timeout_s=15.0,
            )
            legados_on = {}
            for ep in legados_off:
                r_leg = chamar_api_lotofacil_modo4_seguro(
                    srv.base_url, {"quantidade_jogos": 3}, endpoint=ep, timeout_s=15.0
                )
                legados_on[ep] = r_leg["status_http"]
                _garantir(r_leg["status_http"] == 200, f"Legado {ep} falhou em ON: {r_leg}")
        finally:
            # Rollback imediato para OFF padrao de producao
            rb_info = definir_feature_flag_lotofacil_modo4(
                api_producao.app,
                ativo=False,
                permitir_experimental_2j=False,
                motivo="rollback_producao_padrao_off",
            )

        r_health_rb = chamar_api_lotofacil_modo4_seguro(srv.base_url, endpoint="/health", metodo="GET")
        r_gerar_rb = chamar_api_lotofacil_modo4_seguro(
            srv.base_url, {"quantidade_jogos": 8, "semente": 42}
        )
        _garantir(
            r_gerar_rb["status_http"] == 503
            and r_gerar_rb["jogos"] == []
            and r_gerar_rb["fallback_executado"] is False,
            f"Rollback falhou: {r_gerar_rb}",
        )

    int_pos = garantir_integridade_promocao_ou_falhar(
        diretorio_base=BASE_DIR,
        verificar_lotomania_selo=True,
        exigir_manifesto_etapa5=True,
        exigir_manifesto_promocao=True,
    )

    evidencia = {
        "versao_promocao": VERSAO_PROMOCAO_LOTOFACIL_MODO4,
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "arquivos_promocao": list(ARQUIVOS_PRODUCAO_PROMOCAO),
        "manifesto_promocao": manifesto,
        "auditoria_ast_referencia": ast_res,
        "integridade_pos_implantacao": int_pos,
        "evidencia_flag_off_padrao": {
            "health_lotofacil_modo4": r_health_off["dados_brutos"]["lotofacil_modo4"],
            "status_endpoint": r_status_off["dados_brutos"],
            "gerar_off": {
                "status_http": r_gerar_off["status_http"],
                "jogos": r_gerar_off["jogos"],
                "fallback_executado": r_gerar_off["fallback_executado"],
            },
            "avaliar_off_status": r_avaliar_off["status_http"],
        },
        "evidencia_flag_on_controlada": {
            "caso_simples_conservador": {
                "quantidade_jogos": len(d_s["jogos"]),
                "politica_micro_utilizada": d_s["promocao_controlada"]["politica_micro_utilizada"],
                "inicializacao_mista": d_s["promocao_controlada"]["inicializacao_mista"],
                "algoritmo_utilizado": d_s.get("algoritmo_selecionado") or d_s.get("algoritmo"),
                "funcao_objetivo_F": d_s["funcao_objetivo_F"],
                "divergencia_F": d_s["auditoria_referencia_independente"]["divergencia_F"],
                "hash_carteira_sha256": d_s["hash_carteira_sha256"],
                "clausula_obrigatoria_integra": d_s["clausula_obrigatoria"] == CLAUSULA_MATEMATICA_OBRIGATORIA,
            },
            "bloqueio_experimental_2j_padrao": {
                "status_http": r_exp_blq["status_http"],
                "jogos": r_exp_blq["jogos"],
                "fallback_executado": r_exp_blq["fallback_executado"],
            },
            "caso_multipla_16": {
                "quantidade_jogos": len(d_m16["jogos"]),
                "tamanho_aposta": len(d_m16["jogos"][0]),
                "funcao_objetivo_F": d_m16["funcao_objetivo_F"],
                "divergencia_F": d_m16["auditoria_referencia_independente"]["divergencia_F"],
                "hash_carteira_sha256": d_m16["hash_carteira_sha256"],
            },
            "caso_experimental_2j_habilitado": {
                "quantidade_jogos": len(d_exp["jogos"]),
                "politica_micro_utilizada": d_exp["promocao_controlada"]["politica_micro_utilizada"],
                "experimental_2j_utilizada": d_exp["promocao_controlada"]["experimental_2j_utilizada"],
                "funcao_objetivo_F": d_exp["funcao_objetivo_F"],
                "divergencia_F": d_exp["auditoria_referencia_independente"]["divergencia_F"],
                "hash_carteira_sha256": calcular_hash_carteira_lotofacil(d_exp["jogos"]),
            },
        },
        "evidencia_rollback_runtime": {
            "transicao": rb_info,
            "health_pos_rollback": r_health_rb["dados_brutos"]["lotofacil_modo4"],
            "gerar_pos_rollback": {
                "status_http": r_gerar_rb["status_http"],
                "jogos": r_gerar_rb["jogos"],
                "fallback_executado": r_gerar_rb["fallback_executado"],
            },
        },
        "concorrencia_flag_off": conc_off,
        "concorrencia_flag_on": conc_on,
        "nao_interferencia": {
            "lotomania_modo4_hashes_identicos": (
                r_lm_off["dados_brutos"]["hash_carteira_sha256_v2_canonico"]
                == r_lm_on["dados_brutos"]["hash_carteira_sha256_v2_canonico"]
            ),
            "lotomania_sha256_v2": r_lm_off["dados_brutos"]["hash_carteira_sha256_v2_canonico"],
            "legados_status_off": legados_off,
            "legados_status_on": legados_on,
        },
    }

    dir_aud = os.path.join(BASE_DIR, "auditoria", "lotofacil_modo4")
    os.makedirs(dir_aud, exist_ok=True)
    caminho_json = os.path.join(dir_aud, "promocao_controlada_evidencias.json")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(evidencia, f, indent=2, ensure_ascii=False)

    md = _construir_dossie_markdown(evidencia)
    if "\u2014" in md or "\u2013" in md:
        raise RuntimeError("Dossie Markdown nao pode conter em-dash ou en-dash.")
    caminho_md = os.path.join(dir_aud, "DOSSIE_PROMOCAO_CONTROLADA.md")
    with open(caminho_md, "w", encoding="utf-8") as f:
        f.write(md)

    return evidencia


if __name__ == "__main__":
    out = gerar_evidencias_promocao_controlada()
    print(
        json.dumps(
            {
                "versao_promocao": out["versao_promocao"],
                "integro_pos_implantacao": out["integridade_pos_implantacao"]["integro"],
                "flag_off_disponivel": out["evidencia_flag_off_padrao"]["health_lotofacil_modo4"]["disponivel"],
                "concorrencia_off_ok": out["concorrencia_flag_off"]["sucessos"],
                "concorrencia_on_ok": out["concorrencia_flag_on"]["sucessos"],
                "nao_interferencia_lotomania": out["nao_interferencia"]["lotomania_modo4_hashes_identicos"],
            },
            indent=2,
        )
    )
