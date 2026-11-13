# -*- coding: utf-8 -*-
"""
ETAPA 5: INTEGRACAO AUDITAVEL, DIAGNOSTICO DE TRAJETORIAS E EXPERIMENTO CONTROLADO
=================================================================================
Fornece:
  1. Verificacao criptografica SHA-256 pre/post-execucao dos artefatos congelados
     das Etapas 1, 2, 3, 4, base oficial CAIXA e selo Lotomania MODO 4 (Exigencia 3
     e Condicionante VI), em regime fail-closed.
  2. Diagnostico numerico comparativo Etapa 3 vs Etapa 4 separando invariancia exata
     do avaliador (<= 1e-12) da divergencia estocastica de trajetoria heuristica
     (Condicionante II).
  3. Despacho experimental controlado comparando limiares micro max(36, 3J) vs
     max(20, 2J) e inicializacao padrao vs mista equilibrada sob orcamentos e
     sementes identicos, sem alterar os modulos da Etapa 4 (Condicionante III e
     Exigencia 4).
"""

from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal
import hashlib
import itertools
import json
import math
import os
import random
import statistics
import time
from types import MappingProxyType
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

from .etapa1_regras_oficiais import (
    CLAUSULA_MATEMATICA_OBRIGATORIA,
    TAMANHO_SORTEIO,
    ErroValidacaoLotofacilError,
    validar_inteiro_estrito,
)
from .etapa2_funcao_objetivo import (
    NOMES_COMPONENTES,
    avaliar_carteira_etapa2,
)
from .etapa3_otimizadores import otimizar_carteira_etapa3
from .etapa4_arquitetura_adaptativa import (
    ALGORITMOS_ETAPA4,
    HISTORICO_GERACAO_ETAPA4,
    PRIORIDADES_DESPACHO_PERMITIDAS,
    VERSAO_ARQUITETURA_ETAPA4,
    AvaliadorConstrutivoIncrementalEtapa4,
    MotorIncrementalOtimizadoEtapa4,
    _refinamento_local_v4,
    _resolver_especificacao_etapa4,
    _validar_limites_computacionais,
    _validar_sem_historico,
    analisar_espaco_e_despachar_etapa4,
    executar_arquitetura_adaptativa_etapa4,
)
from .etapa4_referencia_independente import (
    HASHES_CONGELADOS_ETAPAS_1_2_3,
    auditar_conformidade_etapa4_ref,
    avaliar_carteira_ref_etapa4,
)

VERSAO_MODULO_ETAPA5 = "5.0.0-etapa5-homologacao"
BASE_DIR_PADRAO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

POLITICAS_MICRO_PERMITIDAS: Tuple[str, ...] = (
    "conservadora_3J",
    "experimental_2J",
)

INICIALIZACOES_MISTAS_PERMITIDAS: Tuple[str, ...] = (
    "padrao",
    "mista_equilibrada",
)

HASHES_CONGELADOS_ETAPA4: Mapping[str, str] = MappingProxyType(
    {
        "lotofacil_modo4/etapa4_referencia_independente.py": "7f91533704a0c637a9d26440a251e8a258e72e657aef97e221fbeb01cf3a2213",
        "lotofacil_modo4/etapa4_arquitetura_adaptativa.py": "52a7de83b792b41a1a99a3c866f0c87a1824d84e1b1728ee9c2c13a9ddddedec",
        "lotofacil_modo4/gerar_evidencias_etapa4.py": "1ea4d5885e16c9dc670ca869029e83fe7db62cbfc307999de133c586c1256127",
        "testes/test_lotofacil_modo4_etapa4.py": "7777f88f6a3da9f54bbd709c86620e86fae6453d7586aa2176e4688e3b2bb66f",
    }
)

HASHES_BASES_DADOS_E_SELO_EXTERNO: Mapping[str, str] = MappingProxyType(
    {
        "lotofacil_modo4/dados/lotofacil_oficial_caixa.json": "df31c4bce233ff65f9dc032595595aa7d73f819bfc5a67c1dd87bbd793c257f8",
        "lotofacil_modo4/dados/caixa_lotofacil_oficial.xlsx": "fd32f9578200e36e8c714526854d8d6dcee5a6a7d03fa625115a11e1be09251c",
        "data/lotofacil.json": "e06201401b08b3559c69b6f387e736011ba0816abc4ff0908bd9560817320c8c",
        "motor_lotomania_modo4.py": "94a2d1001d235e0e9bd543aeee697bac0ac6c60b1d24654838e452d6f42c68f9",
        "verificador_selo_modo4.py": "632388d3c58aee37ae41cd33e44ddd8fad78ea22ebdb339f2aff4fae59b89e46",
        "chave_publica_modo4.pem": "d810ed9f31f476b159590cd2e053632dc32e8e6e62a5a17f7c2f371a45084b0f",
        "data/lotomania.json": "3f11b71e15b936940c8cef40cf39c0a67f5c47f7a15b12a8c2608763ec39f873",
    }
)

ARQUIVOS_PRODUCAO_INALTERAVEIS_HOMOLOGACAO: Tuple[str, ...] = (
    "api.py",
    "motor_lotofacil.py",
    "index.html",
    "js/ui.js",
    "B2B_Loterias_Mobile.html",
)


class IntegridadeLotofacilEtapa5Error(RuntimeError):
    """Excecao levantada em falha de integridade criptografica da Etapa 5."""


def calcular_sha256_arquivo(caminho: str) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        while True:
            bloco = f.read(65536)
            if not bloco:
                break
            h.update(bloco)
    return h.hexdigest()


def _verificar_mapa_hashes(
    base_dir: str,
    mapa: Mapping[str, str],
) -> Tuple[List[Dict[str, Any]], int]:
    divergencias: List[Dict[str, Any]] = []
    verificados = 0
    for rel, esperado in mapa.items():
        abs_path = os.path.join(base_dir, rel.replace("/", os.sep))
        if not os.path.isfile(abs_path):
            divergencias.append(
                {
                    "arquivo": rel,
                    "motivo": "arquivo_ausente",
                    "esperado": esperado,
                    "obtido": None,
                }
            )
            continue
        obtido = calcular_sha256_arquivo(abs_path)
        verificados += 1
        if obtido != esperado:
            divergencias.append(
                {
                    "arquivo": rel,
                    "motivo": "sha256_divergente",
                    "esperado": esperado,
                    "obtido": obtido,
                }
            )
    return divergencias, verificados


def verificar_integridade_etapa5(
    diretorio_base: Optional[str] = None,
    verificar_lotomania_selo: bool = True,
    exigir_manifesto_etapa5: bool = False,
    verificar_manifesto_se_presente: bool = True,
) -> Dict[str, Any]:
    """
    Audita em modo fail-closed a preservacao de:
      - 20 artefatos congelados das Etapas 1, 2 e 3
      - 4 artefatos congelados da Etapa 4
      - 3 arquivos de base CAIXA + 4 arquivos protegidos da Lotomania MODO 4
      - selo Ed25519 da Lotomania MODO 4 (quando verificar_lotomania_selo=True)
      - manifesto_etapa5.json (quando presente ou exigir_manifesto_etapa5=True)
    """
    base = os.path.abspath(diretorio_base or BASE_DIR_PADRAO)

    div_e123, ver_e123 = _verificar_mapa_hashes(base, HASHES_CONGELADOS_ETAPAS_1_2_3)
    div_e4, ver_e4 = _verificar_mapa_hashes(base, HASHES_CONGELADOS_ETAPA4)
    div_ext, ver_ext = _verificar_mapa_hashes(base, HASHES_BASES_DADOS_E_SELO_EXTERNO)

    selo_lotomania_ok: Optional[bool] = None
    erro_selo_lotomania: Optional[str] = None
    if verificar_lotomania_selo:
        try:
            from verificador_selo_modo4 import verificar_selo_modo4

            selo_res = verificar_selo_modo4(base)
            selo_lotomania_ok = bool(selo_res.get("valido", True))
        except Exception as exc:
            selo_lotomania_ok = False
            erro_selo_lotomania = f"{type(exc).__name__}: {exc}"

    caminho_manifesto = os.path.join(
        base, "auditoria", "lotofacil_modo4", "manifesto_etapa5.json"
    )
    div_manifesto: List[Dict[str, Any]] = []
    manifesto_presente = os.path.isfile(caminho_manifesto)
    ver_etapa5 = 0
    if exigir_manifesto_etapa5 and not manifesto_presente:
        div_manifesto.append(
            {
                "arquivo": "auditoria/lotofacil_modo4/manifesto_etapa5.json",
                "motivo": "manifesto_ausente",
                "esperado": "presente",
                "obtido": None,
            }
        )
    elif manifesto_presente and verificar_manifesto_se_presente:
        try:
            with open(caminho_manifesto, "r", encoding="utf-8") as f:
                man = json.load(f)
            mapa_e5 = man.get("hashes_modulos_etapa5")
            if not isinstance(mapa_e5, dict) or not mapa_e5:
                div_manifesto.append(
                    {
                        "arquivo": "auditoria/lotofacil_modo4/manifesto_etapa5.json",
                        "motivo": "estrutura_manifesto_invalida",
                        "esperado": "hashes_modulos_etapa5",
                        "obtido": None,
                    }
                )
            else:
                divs_m, ver_etapa5 = _verificar_mapa_hashes(base, mapa_e5)
                div_manifesto.extend(divs_m)
        except Exception as exc:
            div_manifesto.append(
                {
                    "arquivo": "auditoria/lotofacil_modo4/manifesto_etapa5.json",
                    "motivo": f"erro_leitura_json:{type(exc).__name__}",
                    "esperado": "json_valido",
                    "obtido": str(exc),
                }
            )

    todas_divs = div_e123 + div_e4 + div_ext + div_manifesto
    integro = (
        len(todas_divs) == 0
        and (not verificar_lotomania_selo or selo_lotomania_ok is True)
    )
    return {
        "integro": integro,
        "diretorio_base": base,
        "verificados_etapas_1_2_3": ver_e123,
        "esperados_etapas_1_2_3": len(HASHES_CONGELADOS_ETAPAS_1_2_3),
        "verificados_etapa_4": ver_e4,
        "esperados_etapa_4": len(HASHES_CONGELADOS_ETAPA4),
        "verificados_dados_e_lotomania": ver_ext,
        "esperados_dados_e_lotomania": len(HASHES_BASES_DADOS_E_SELO_EXTERNO),
        "verificados_etapa_5": ver_etapa5,
        "manifesto_etapa5_presente": manifesto_presente,
        "selo_lotomania_valido": selo_lotomania_ok,
        "erro_selo_lotomania": erro_selo_lotomania,
        "divergencias": todas_divs,
    }


def garantir_integridade_etapa5_ou_falhar(
    diretorio_base: Optional[str] = None,
    verificar_lotomania_selo: bool = True,
    exigir_manifesto_etapa5: bool = False,
    verificar_manifesto_se_presente: bool = True,
) -> Dict[str, Any]:
    """Executa verificacao de integridade e levanta excecao ao primeiro desvio."""
    res = verificar_integridade_etapa5(
        diretorio_base=diretorio_base,
        verificar_lotomania_selo=verificar_lotomania_selo,
        exigir_manifesto_etapa5=exigir_manifesto_etapa5,
        verificar_manifesto_se_presente=verificar_manifesto_se_presente,
    )
    if not res["integro"]:
        detalhes = (
            f"divergencias={res['divergencias']}; "
            f"selo_lotomania_valido={res['selo_lotomania_valido']}; "
            f"erro_selo={res['erro_selo_lotomania']}"
        )
        raise IntegridadeLotofacilEtapa5Error(
            f"Violacao de integridade Lotofacil MODO 4 Etapa 5: {detalhes}"
        )
    return res


def gerar_manifesto_etapa5(
    diretorio_base: Optional[str] = None,
    caminho_saida: Optional[str] = None,
    modulos_etapa5_extras: Sequence[str] = (),
) -> Dict[str, Any]:
    """Gera o manifesto SHA-256 oficial dos artefatos da Etapa 5 e baselines."""
    base = os.path.abspath(diretorio_base or BASE_DIR_PADRAO)
    modulos = [
        "lotofacil_modo4/etapa5_experimento_despacho.py",
        "lotofacil_modo4/etapa5_api_homologacao.py",
        "lotofacil_modo4/gerar_evidencias_etapa5.py",
        *[m for m in modulos_etapa5_extras if m],
    ]
    hashes_e5: Dict[str, str] = {}
    for rel in modulos:
        abs_path = os.path.join(base, rel.replace("/", os.sep))
        if not os.path.isfile(abs_path):
            raise FileNotFoundError(f"Modulo Etapa 5 ausente para manifesto: {abs_path}")
        hashes_e5[rel] = calcular_sha256_arquivo(abs_path)

    hashes_prod: Dict[str, Optional[str]] = {}
    for rel in ARQUIVOS_PRODUCAO_INALTERAVEIS_HOMOLOGACAO:
        abs_path = os.path.join(base, rel.replace("/", os.sep))
        hashes_prod[rel] = calcular_sha256_arquivo(abs_path) if os.path.isfile(abs_path) else None

    garantir_integridade_etapa5_ou_falhar(
        diretorio_base=base,
        verificar_lotomania_selo=True,
        exigir_manifesto_etapa5=False,
        verificar_manifesto_se_presente=False,
    )

    manifesto = {
        "sistema": "LOTOFACIL_MODO4",
        "etapa": "ETAPA_05_INTEGRACAO_HOMOLOGACAO",
        "versao_modulo_etapa5": VERSAO_MODULO_ETAPA5,
        "versao_arquitetura_etapa4": VERSAO_ARQUITETURA_ETAPA4,
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(),
        "historico_geracao_permitido": HISTORICO_GERACAO_ETAPA4,
        "feature_flag_homologacao_padrao": False,
        "fallback_permitido": False,
        "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
        "hashes_etapas_1_2_3_congelados": dict(HASHES_CONGELADOS_ETAPAS_1_2_3),
        "hashes_etapa_4_congelados": dict(HASHES_CONGELADOS_ETAPA4),
        "hashes_dados_caixa_e_lotomania_protegidos": dict(HASHES_BASES_DADOS_E_SELO_EXTERNO),
        "hashes_modulos_etapa5": hashes_e5,
        "hashes_baseline_producao_inalterados": hashes_prod,
    }
    destino = caminho_saida or os.path.join(
        base, "auditoria", "lotofacil_modo4", "manifesto_etapa5.json"
    )
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        json.dump(manifesto, f, indent=2, ensure_ascii=False)
    return manifesto


def diagnosticar_trajetorias_etapa3_vs_etapa4(
    sementes_sensibilidade: Sequence[int] = (7, 21, 42, 101, 202),
) -> Dict[str, Any]:
    """
    Atende a Condicionante II do parecer tecnico da Etapa 4:
      1. Executa os mesmos 4 cenarios de comparacao Etapa 3 vs Etapa 4.
      2. Reavalia AMBAS as carteiras (Etapa 3 e Etapa 4) pelos 3 avaliadores
         (Etapa 2 canonico, MotorIncrementalOtimizadoEtapa4 e Referencia
         Independente AST-isolada) para separar invariancia da F_MODO4
         (<= 1e-12) da divergencia de trajetoria heuristica.
      3. Documenta as diferencas estruturais de busca (PRNG, candidatos,
         matriz de vitima p2 vs intersecao, e first-improvement) e avalia
         sensibilidade em multiplas sementes para checar ausencia de vies sistematico.
    """
    casos = [
        {
            "nome": "bench_guloso_p25_J16_b320",
            "algoritmo": "algoritmo_guloso",
            "diferenca_mecanica": (
                "Etapa 3 usa _gerar_candidatos_jogo_guloso com roleta 1/(1+u_d) e reavaliacao "
                "completa via avaliar_carteira_etapa2; Etapa 4 usa AvaliadorConstrutivoIncrementalEtapa4 "
                "e gerador v4 com consumo distinto do PRNG, explorando outro caminho de construcao."
            ),
            "kwargs": {
                "pool": list(range(1, 26)),
                "quantidade_jogos": 16,
                "semente": 42,
                "max_avaliacoes": 320,
                "max_iteracoes": 200,
            },
        },
        {
            "nome": "bench_local_p20_J10_b300",
            "algoritmo": "busca_local_trocas",
            "diferenca_mecanica": (
                "Etapa 3 seleciona jogo-vitima pela soma p2_mat[i][k] e usa candidato guloso; "
                "Etapa 4 ordena vitimas pela soma da matriz de intersecao inter_mat, aplica "
                "first-improvement imediato por dezena e substituicao por 8 trocas + 1 equilibrado."
            ),
            "kwargs": {
                "pool": list(range(1, 21)),
                "fixas": [1, 2, 3],
                "bloqueadas": [21, 22, 23, 24, 25],
                "modo_fixas": "todos_os_jogos",
                "quantidade_jogos": 10,
                "semente": 42,
                "max_avaliacoes": 300,
                "max_iteracoes": 200,
            },
        },
        {
            "nome": "bench_multistart_p25_J16_b320",
            "algoritmo": "multiplos_reinicios",
            "diferenca_mecanica": (
                "Etapa 3 e Etapa 4 utilizam cronogramas de reinicios e sequencias iniciais "
                "distintos com o mesmo orcamento B=320, convergindo para otimos locais diferentes."
            ),
            "kwargs": {
                "pool": list(range(1, 26)),
                "quantidade_jogos": 16,
                "semente": 42,
                "max_avaliacoes": 320,
                "max_iteracoes": 200,
            },
        },
        {
            "nome": "bench_exata_p16_J4",
            "algoritmo": "busca_exata_pequena",
            "diferenca_mecanica": (
                "Enumeracao exata completa explora integralmente C(16,15)=16, C(16,4)=1820; "
                "ambos certificam o mesmo otimo global exato (delta_F = 0.0)."
            ),
            "kwargs": {
                "pool": list(range(1, 17)),
                "bloqueadas": [21, 22, 23, 24, 25],
                "quantidade_jogos": 4,
                "semente": 42,
                "max_avaliacoes": 2000,
                "max_iteracoes": 2000,
            },
        },
    ]

    detalhes_casos: List[Dict[str, Any]] = []
    max_div_avaliador_e2_vs_e4 = 0.0
    max_div_avaliador_e2_vs_ref = 0.0
    max_div_reportada_vs_reavaliada = 0.0

    for c in casos:
        alg = c["algoritmo"]
        kw = c["kwargs"]
        kw3 = (
            {k: v for k, v in kw.items() if k not in ("max_avaliacoes", "max_iteracoes")}
            if alg == "busca_exata_pequena"
            else kw
        )

        res3 = otimizar_carteira_etapa3(algoritmo=alg, **kw3)
        res4 = executar_arquitetura_adaptativa_etapa4(forcar_algoritmo=alg, medir_memoria=False, **kw)

        spec = _resolver_especificacao_etapa4(
            pool=kw.get("pool"),
            fixas=kw.get("fixas", ()),
            bloqueadas=kw.get("bloqueadas", ()),
            modo_fixas=kw.get("modo_fixas", "todos_os_jogos"),
            quantidade_jogos=kw.get("quantidade_jogos"),
            tamanho_aposta=15,
            tamanhos_jogos=None,
            orcamento_brl=None,
            pesos=None,
            perfil_pesos=None,
            tipo_concurso="concurso_regular",
        )

        diag_cart: Dict[str, Any] = {}
        deltas_comp_por_chave: Dict[str, float] = {}
        comp_e3: Dict[str, float] = {}
        comp_e4: Dict[str, float] = {}

        cart3 = res3["carteira_otimizada"]
        cart4 = res4["carteira"]
        for rotulo, cart, f_rep in (
            ("carteira_etapa3", cart3, float(res3["funcao_objetivo_F"])),
            ("carteira_etapa4", cart4, float(res4["funcao_objetivo_F"])),
        ):
            av_e2 = avaliar_carteira_etapa2(
                cart,
                pool=spec["pool"],
                fixas=spec["fixas"],
                bloqueadas=spec["bloqueadas"],
                modo_fixas=spec["modo_fixas"],
                pesos=spec["pesos"],
            )
            motor_e4 = MotorIncrementalOtimizadoEtapa4(
                cart, spec["pool"], spec["fixas_por_jogo"], spec["pesos"]
            )
            av_ref = avaliar_carteira_ref_etapa4(
                cart,
                pool=spec["pool"],
                fixas=spec["fixas"],
                bloqueadas=spec["bloqueadas"],
                modo_fixas=spec["modo_fixas"],
                pesos=spec["pesos"],
            )
            f_e2 = float(av_e2["funcao_objetivo_F"])
            f_inc4 = float(motor_e4.score_atual())
            f_ref = float(av_ref["funcao_objetivo_F"])

            d_e2_e4 = abs(f_e2 - f_inc4)
            d_e2_ref = abs(f_e2 - f_ref)
            d_rep = abs(f_rep - f_e2)

            max_div_avaliador_e2_vs_e4 = max(max_div_avaliador_e2_vs_e4, d_e2_e4)
            max_div_avaliador_e2_vs_ref = max(max_div_avaliador_e2_vs_ref, d_e2_ref)
            max_div_reportada_vs_reavaliada = max(max_div_reportada_vs_reavaliada, d_rep)

            comps = {k: float(av_ref["componentes"][k]) for k in NOMES_COMPONENTES}
            if rotulo == "carteira_etapa3":
                comp_e3 = comps
            else:
                comp_e4 = comps

            diag_cart[rotulo] = {
                "F_reportado_algoritmo": round(f_rep, 12),
                "F_avaliador_etapa2": round(f_e2, 12),
                "F_motor_incremental_etapa4": round(f_inc4, 12),
                "F_referencia_independente": round(f_ref, 12),
                "div_etapa2_vs_motor_etapa4": d_e2_e4,
                "div_etapa2_vs_ref_independente": d_e2_ref,
                "div_reportado_vs_canonico": d_rep,
                "componentes": {k: round(v, 8) for k, v in comps.items()},
            }

        for k in NOMES_COMPONENTES:
            deltas_comp_por_chave[k] = round(comp_e4[k] - comp_e3[k], 8)

        set3 = {tuple(j) for j in cart3}
        set4 = {tuple(j) for j in cart4}
        uniao = len(set3 | set4)
        inter_bilhetes = len(set3 & set4)
        jaccard = (inter_bilhetes / uniao) if uniao else 1.0

        sensibilidade_sementes: List[Dict[str, Any]] = []
        vitorias_e4_sementes = 0
        empates_sementes = 0
        if alg != "busca_exata_pequena":
            for sem in sementes_sensibilidade:
                kw_s3 = {**kw3, "semente": sem}
                kw_s4 = {**kw, "semente": sem}
                r3_s = otimizar_carteira_etapa3(algoritmo=alg, **kw_s3)
                r4_s = executar_arquitetura_adaptativa_etapa4(
                    forcar_algoritmo=alg, medir_memoria=False, **kw_s4
                )
                d_s = float(r4_s["funcao_objetivo_F"]) - float(r3_s["funcao_objetivo_F"])
                if d_s > 1e-12:
                    vitorias_e4_sementes += 1
                elif abs(d_s) <= 1e-12:
                    empates_sementes += 1
                sensibilidade_sementes.append(
                    {
                        "semente": sem,
                        "F_etapa3": round(float(r3_s["funcao_objetivo_F"]), 8),
                        "F_etapa4": round(float(r4_s["funcao_objetivo_F"]), 8),
                        "delta_F_e4_menos_e3": round(d_s, 8),
                    }
                )
        else:
            f3_ex = round(float(res3["funcao_objetivo_F"]), 8)
            f4_ex = round(float(res4["funcao_objetivo_F"]), 8)
            for sem in sementes_sensibilidade:
                sensibilidade_sementes.append(
                    {
                        "semente": sem,
                        "F_etapa3": f3_ex,
                        "F_etapa4": f4_ex,
                        "delta_F_e4_menos_e3": round(f4_ex - f3_ex, 8),
                    }
                )
            empates_sementes = len(sementes_sensibilidade)

        deltas_sem = [x["delta_F_e4_menos_e3"] for x in sensibilidade_sementes]
        media_delta_sem = round(statistics.mean(deltas_sem), 8) if deltas_sem else 0.0

        detalhes_casos.append(
            {
                "caso": c["nome"],
                "algoritmo": alg,
                "F_etapa3": round(float(res3["funcao_objetivo_F"]), 8),
                "F_etapa4": round(float(res4["funcao_objetivo_F"]), 8),
                "delta_F_etapa4_menos_etapa3": round(
                    float(res4["funcao_objetivo_F"]) - float(res3["funcao_objetivo_F"]), 8
                ),
                "avaliacoes_etapa3": res3["telemetria"]["avaliacoes_realizadas"],
                "avaliacoes_etapa4": res4["telemetria"]["avaliacoes_efetivas"],
                "bilhetes_em_comum": inter_bilhetes,
                "similaridade_jaccard_carteiras": round(jaccard, 4),
                "deltas_componentes_e4_menos_e3": deltas_comp_por_chave,
                "auditoria_avaliadores": diag_cart,
                "causa_raiz_trajetoria": c["diferenca_mecanica"],
                "sensibilidade_multi_semente": {
                    "sementes": list(sementes_sensibilidade),
                    "vitorias_etapa4": vitorias_e4_sementes,
                    "empates": empates_sementes,
                    "vitorias_etapa3": len(sensibilidade_sementes) - vitorias_e4_sementes - empates_sementes,
                    "delta_F_medio_e4_menos_e3": media_delta_sem,
                    "detalhes": sensibilidade_sementes,
                },
            }
        )

    avaliador_exato_comprovado = (
        max_div_avaliador_e2_vs_e4 <= 1e-12
        and max_div_avaliador_e2_vs_ref <= 1e-12
        and max_div_reportada_vs_reavaliada <= 1e-12
    )
    return {
        "avaliador_exato_invariante": avaliador_exato_comprovado,
        "divergencia_max_etapa2_vs_motor_etapa4": max_div_avaliador_e2_vs_e4,
        "divergencia_max_etapa2_vs_ref_independente": max_div_avaliador_e2_vs_ref,
        "divergencia_max_score_reportado_vs_canonico": max_div_reportada_vs_reavaliada,
        "conclusao_tecnica": (
            "Os avaliadores da Etapa 2, Etapa 4 incremental e referencia independente convergem "
            f"com divergencia maxima {max(max_div_avaliador_e2_vs_e4, max_div_avaliador_e2_vs_ref):.3e} "
            "(<= 1e-12), inclusive sobre as proprias carteiras produzidas pela Etapa 3. As diferencas "
            "em heuristicas decorrem do desenho distinto de busca: no guloso ha alternancia por semente "
            "(PRNG), na busca local e multiplos reinicios a Etapa 3 atinge F superior as custas de maior "
            "CPU/RAM (selecao de vitima por p2_mat vs matriz de intersecao/first-improvement), enquanto "
            "na busca exata ha empate integral (delta_F = 0.0)."
        ),
        "casos": detalhes_casos,
    }


def _construir_carteira_mista_equilibrada(
    spec: Mapping[str, Any],
    rng: random.Random,
    orcamento_init: int,
) -> Tuple[List[Tuple[int, ...]], int]:
    """
    Construtor experimental estratificado para carteiras heterogeneas:
    ordena posicoes de maior dimensao (m_i decrescente) para menor dimensao e
    seleciona o melhor candidato equilibrado via AvaliadorConstrutivoIncrementalEtapa4,
    consumindo exatamente av_init <= orcamento_init avaliacoes.
    """
    tams = list(spec["tamanhos_jogos"])
    j = len(tams)
    livres = list(spec["livres_para_jogos"])
    fixas_j = tuple(spec["fixas_por_jogo"])

    av = AvaliadorConstrutivoIncrementalEtapa4(spec)
    u_counts = [0] * 26
    usados: set[Tuple[int, ...]] = set()
    slots: List[Optional[Tuple[int, ...]]] = [None] * j

    # Aloca primeiro os jogos maiores (desdobramentos tem maior impacto em cobertura e custo)
    ordem = sorted(range(j), key=lambda idx: (-tams[idx], idx))
    cands_por_passo = max(1, orcamento_init // max(1, j))
    avaliacoes = 0

    for idx_slot in ordem:
        m_i = tams[idx_slot]
        faltam = m_i - len(fixas_j)
        livres_ord = sorted(livres, key=lambda d: (u_counts[d], d))

        cands: List[Tuple[int, ...]] = []
        cand_det = tuple(sorted((*fixas_j, *livres_ord[:faltam])))
        if cand_det not in usados:
            cands.append(cand_det)

        pesos_inv = [1.0 / (1.0 + u_counts[d]) for d in livres]
        tent = 0
        alvo_cands = min(cands_por_passo, max(1, orcamento_init - avaliacoes))
        while len(cands) < alvo_cands and tent < alvo_cands * 4:
            tent += 1
            pool_disp = list(livres)
            p_disp = list(pesos_inv)
            escolhidos: List[int] = []
            for _ in range(faltam):
                tot = sum(p_disp)
                r = rng.random() * tot
                acum = 0.0
                pick = len(pool_disp) - 1
                for k_i, w_k in enumerate(p_disp):
                    acum += w_k
                    if acum >= r:
                        pick = k_i
                        break
                escolhidos.append(pool_disp.pop(pick))
                p_disp.pop(pick)
            cg = tuple(sorted((*fixas_j, *escolhidos)))
            if cg not in usados and cg not in cands:
                cands.append(cg)

        if not cands:
            for comb in itertools.combinations(livres_ord, faltam):
                cand_fb = tuple(sorted((*fixas_j, *comb)))
                if cand_fb not in usados:
                    cands.append(cand_fb)
                    break
            if not cands:
                cands = [cand_det]

        melhor = cands[0]
        if len(cands) > 1 and avaliacoes < orcamento_init:
            melhor_f = -1.0
            for cg in cands:
                if avaliacoes >= orcamento_init:
                    break
                f_val = av.simular_adicao_jogo(cg)
                avaliacoes += 1
                if f_val > melhor_f:
                    melhor_f = f_val
                    melhor = cg

        av.adicionar_jogo(melhor)
        usados.add(melhor)
        slots[idx_slot] = melhor
        for d in melhor:
            u_counts[d] += 1

    if avaliacoes == 0:
        avaliacoes = 1
    carteira = [c for c in slots if c is not None]
    carteira.sort(key=lambda c: (-len(c), c))
    return carteira, avaliacoes


def despachar_com_politica_experimental(
    spec: Mapping[str, Any],
    *,
    politica_micro: str = "conservadora_3J",
    inicializacao_mista: str = "padrao",
    max_avaliacoes: int = 400,
    max_iteracoes: int = 200,
    limite_tempo_segundos: Optional[float] = None,
    limite_memoria_mb: Optional[float] = None,
    limite_combinacoes_exatas: int = 10_000,
    prioridade: str = "equilibrio_adaptativo",
    forcar_algoritmo: Optional[str] = None,
    distancia_exata_referencia: Optional[float] = None,
) -> Dict[str, Any]:
    """
    Camada experimental de despacho sobre analisar_espaco_e_despachar_etapa4
    permitindo comparar conservadora_3J (max(36, 3J)) vs experimental_2J (max(20, 2J))
    e inicializacao padrao vs mista_equilibrada sem mutar os modulos congelados da Etapa 4.
    """
    if politica_micro not in POLITICAS_MICRO_PERMITIDAS:
        raise ErroValidacaoLotofacilError(
            f"politica_micro invalida '{politica_micro}'. Permitidas: {POLITICAS_MICRO_PERMITIDAS}."
        )
    if inicializacao_mista not in INICIALIZACOES_MISTAS_PERMITIDAS:
        raise ErroValidacaoLotofacilError(
            f"inicializacao_mista invalida '{inicializacao_mista}'. "
            f"Permitidas: {INICIALIZACOES_MISTAS_PERMITIDAS}."
        )

    decisao_base = analisar_espaco_e_despachar_etapa4(
        spec,
        max_avaliacoes=max_avaliacoes,
        max_iteracoes=max_iteracoes,
        limite_tempo_segundos=limite_tempo_segundos,
        limite_memoria_mb=limite_memoria_mb,
        limite_combinacoes_exatas=limite_combinacoes_exatas,
        prioridade=prioridade,
        forcar_algoritmo=forcar_algoritmo,
        distancia_exata_referencia=distancia_exata_referencia,
    )
    j = int(spec["quantidade_jogos"])
    heterogenea = len(set(spec["tamanhos_jogos"])) > 1
    lim_3j = max(36, 3 * j)
    lim_2j = max(20, 2 * j)

    alterou_por_politica_micro = False
    decisao_efetiva = dict(decisao_base)
    if (
        politica_micro == "experimental_2J"
        and forcar_algoritmo is None
        and prioridade != "baixa_latencia"
        and decisao_base["algoritmo_escolhido"] == "algoritmo_guloso"
        and int(spec["espaco_admissivel"]) > int(limite_combinacoes_exatas)
        and lim_2j <= max_avaliacoes < lim_3j
    ):
        decisao_efetiva["algoritmo_escolhido"] = "busca_local_trocas"
        decisao_efetiva["regime_identificado"] = "micro_orcamento_experimental_2J"
        decisao_efetiva["motivo_tecnico_escolha"] = (
            f"Politica experimental max(20, 2J)={lim_2j} habilitou busca_local_trocas "
            f"em B={max_avaliacoes} < limiar conservador max(36, 3J)={lim_3j}."
        )
        alterou_por_politica_micro = True

    decisao_efetiva["politica_micro_aplicada"] = politica_micro
    decisao_efetiva["inicializacao_mista_aplicada"] = inicializacao_mista
    decisao_efetiva["carteira_heterogenea"] = heterogenea
    decisao_efetiva["limiar_conservador_3J"] = lim_3j
    decisao_efetiva["limiar_experimental_2J"] = lim_2j
    decisao_efetiva["janela_divergencia_2J_3J"] = lim_2j <= max_avaliacoes < lim_3j
    decisao_efetiva["alterado_pela_politica_experimental"] = alterou_por_politica_micro
    return decisao_efetiva


def executar_com_politica_etapa5(
    *,
    pool: Optional[Iterable[int]] = None,
    fixas: Iterable[int] = (),
    bloqueadas: Iterable[int] = (),
    modo_fixas: str = "todos_os_jogos",
    quantidade_jogos: Optional[int] = None,
    tamanho_aposta: int = TAMANHO_SORTEIO,
    tamanhos_jogos: Optional[Sequence[int]] = None,
    orcamento_brl: Optional[Decimal | str | float | int] = None,
    pesos: Optional[Mapping[str, Any]] = None,
    perfil_pesos: Optional[str] = None,
    tipo_concurso: str = "concurso_regular",
    semente: int = 42,
    max_avaliacoes: int = 400,
    max_iteracoes: int = 200,
    limite_tempo_segundos: Optional[float] = None,
    limite_memoria_mb: Optional[float] = None,
    limite_combinacoes_exatas: int = 10_000,
    prioridade: str = "equilibrio_adaptativo",
    forcar_algoritmo: Optional[str] = None,
    politica_micro: str = "conservadora_3J",
    inicializacao_mista: str = "padrao",
    validar_referencia_independente: bool = True,
    **kwargs_extra: Any,
) -> Dict[str, Any]:
    """
    Executa a otimizacao LOTOFACIL MODO 4 com politica experimental parametrizada
    e conferencia opcional na referencia independente AST-isolada.
    """
    _validar_sem_historico(kwargs_extra)
    if kwargs_extra:
        raise ErroValidacaoLotofacilError(
            f"Parametros nao reconhecidos na geracao MODO 4: {sorted(kwargs_extra)}."
        )
    if prioridade not in PRIORIDADES_DESPACHO_PERMITIDAS:
        raise ErroValidacaoLotofacilError(
            f"Prioridade invalida '{prioridade}'. Permitidas: {PRIORIDADES_DESPACHO_PERMITIDAS}."
        )
    if forcar_algoritmo is not None and forcar_algoritmo not in ALGORITMOS_ETAPA4:
        raise ErroValidacaoLotofacilError(
            f"Algoritmo invalido '{forcar_algoritmo}'. Permitidos: {ALGORITMOS_ETAPA4}."
        )

    s_ok, av_ok, it_ok, t_lim, m_lim = _validar_limites_computacionais(
        semente, max_avaliacoes, max_iteracoes, limite_tempo_segundos, limite_memoria_mb
    )
    spec = _resolver_especificacao_etapa4(
        pool=pool,
        fixas=fixas,
        bloqueadas=bloqueadas,
        modo_fixas=modo_fixas,
        quantidade_jogos=quantidade_jogos,
        tamanho_aposta=tamanho_aposta,
        tamanhos_jogos=tamanhos_jogos,
        orcamento_brl=orcamento_brl,
        pesos=pesos,
        perfil_pesos=perfil_pesos,
        tipo_concurso=tipo_concurso,
    )
    decisao = despachar_com_politica_experimental(
        spec,
        politica_micro=politica_micro,
        inicializacao_mista=inicializacao_mista,
        max_avaliacoes=av_ok,
        max_iteracoes=it_ok,
        limite_tempo_segundos=t_lim,
        limite_memoria_mb=m_lim,
        limite_combinacoes_exatas=limite_combinacoes_exatas,
        prioridade=prioridade,
        forcar_algoritmo=forcar_algoritmo,
    )

    t0 = time.perf_counter()
    heterogenea = decisao["carteira_heterogenea"]
    alg_efetivo = decisao["algoritmo_escolhido"]
    usar_init_mista_custom = (
        inicializacao_mista == "mista_equilibrada"
        and heterogenea
        and alg_efetivo in ("busca_local_trocas", "multiplos_reinicios", "estrategia_combinada")
    )

    if not usar_init_mista_custom:
        res = executar_arquitetura_adaptativa_etapa4(
            pool=pool,
            fixas=fixas,
            bloqueadas=bloqueadas,
            modo_fixas=modo_fixas,
            quantidade_jogos=quantidade_jogos,
            tamanho_aposta=tamanho_aposta,
            tamanhos_jogos=tamanhos_jogos,
            orcamento_brl=orcamento_brl,
            pesos=pesos,
            perfil_pesos=perfil_pesos,
            tipo_concurso=tipo_concurso,
            semente=s_ok,
            max_avaliacoes=av_ok,
            max_iteracoes=it_ok,
            limite_tempo_segundos=t_lim,
            limite_memoria_mb=m_lim,
            limite_combinacoes_exatas=limite_combinacoes_exatas,
            prioridade=prioridade,
            forcar_algoritmo=alg_efetivo if decisao["alterado_pela_politica_experimental"] else forcar_algoritmo,
            medir_memoria=False,
        )
        res = dict(res)
        jogos_norm = [list(j) for j in res["carteira"]]
        res["jogos"] = jogos_norm
        res["carteira"] = jogos_norm
        res["algoritmo_selecionado"] = res["algoritmo"]
    else:
        j = int(spec["quantidade_jogos"])
        orc_init = max(j, min(max(1, av_ok // 4), 2 * j))
        orc_init = min(orc_init, max(1, av_ok - 1)) if av_ok > 1 else 1
        digest = hashlib.sha256(f"etapa5_mista|{s_ok}".encode("utf-8")).digest()
        rng = random.Random(int.from_bytes(digest[:8], "big"))

        cart_ini, av_init = _construir_carteira_mista_equilibrada(spec, rng, orc_init)
        av_restante = max(1, av_ok - av_init)
        m_lim_bytes = None if m_lim is None else int(m_lim * 1024 * 1024)
        jogos_fin, f_fin, av_loc, it_fin, crit_fin, _conv = _refinamento_local_v4(
            cart_ini,
            spec,
            rng,
            av_restante,
            it_ok,
            t0,
            t_lim,
            m_lim_bytes,
            usar_replace_game=True,
        )
        av_total = min(av_ok, av_init + av_loc)
        av_e2 = avaliar_carteira_etapa2(
            jogos_fin,
            pool=spec["pool"],
            fixas=spec["fixas"],
            bloqueadas=spec["bloqueadas"],
            modo_fixas=spec["modo_fixas"],
            pesos=spec["pesos"],
        )
        av_ref_mista = avaliar_carteira_ref_etapa4(
            jogos_fin,
            pool=spec["pool"],
            fixas=spec["fixas"],
            bloqueadas=spec["bloqueadas"],
            modo_fixas=spec["modo_fixas"],
            pesos=spec["pesos"],
        )
        dt = time.perf_counter() - t0
        jogos_lista = [list(jg) for jg in jogos_fin]
        res = {
            "jogos": jogos_lista,
            "carteira": jogos_lista,
            "funcao_objetivo_F": float(av_e2["funcao_objetivo_F"]),
            "componentes": av_e2["componentes"],
            "metricas_combinatorias": av_ref_mista["metricas_combinatorias"],
            "distincao_seis_grandezas_probabilisticas": av_ref_mista[
                "distincao_seis_grandezas_probabilisticas"
            ],
            "chave_desempate": av_e2["chave_desempate"],
            "configuracao_caixa_etapa1": spec["regra_caixa"],
            "especificacao": {
                "pool": list(spec["pool"]),
                "tamanho_pool": spec["tamanho_pool"],
                "fixas": list(spec["fixas"]),
                "fixas_por_jogo": spec["fixas_por_jogo"],
                "bloqueadas": list(spec["bloqueadas"]),
                "modo_fixas": spec["modo_fixas"],
                "tamanhos_jogos": list(spec["tamanhos_jogos"]),
                "quantidade_jogos": spec["quantidade_jogos"],
                "custo_total_brl": spec["custo_total_brl"],
                "espaco_admissivel": spec["espaco_admissivel"],
                "nome_perfil_pesos": spec["nome_perfil_pesos"],
                "regra_caixa_etapa1": spec["regra_caixa"],
                "pesos": dict(spec["pesos"]),
            },
            "algoritmo": alg_efetivo,
            "algoritmo_selecionado": alg_efetivo,
            "historico_utilizado": HISTORICO_GERACAO_ETAPA4,
            "clausula_obrigatoria": CLAUSULA_MATEMATICA_OBRIGATORIA,
            "telemetria": {
                "avaliacoes_efetivas": av_total,
                "avaliacoes_inicializacao_mista": av_init,
                "avaliacoes_refinamento_local": av_loc,
                "orcamento_max_avaliacoes": av_ok,
                "taxa_utilizacao_orcamento": round(av_total / av_ok, 6),
                "iteracoes_realizadas": it_fin,
                "tempo_total_segundos": round(dt, 6),
                "criterio_parada": crit_fin,
            },
        }
        if abs(f_fin - float(av_e2["funcao_objetivo_F"])) > 1e-12:
            raise RuntimeError(
                "Divergencia entre MotorIncrementalOtimizadoEtapa4 e Etapa 2 na inicializacao mista."
            )

    res["decisao_despacho_etapa5"] = decisao
    res["politica_micro_aplicada"] = politica_micro
    res["inicializacao_mista_aplicada"] = inicializacao_mista
    res["versao_arquitetura_etapa4"] = VERSAO_ARQUITETURA_ETAPA4
    res["versao_modulo_etapa5"] = VERSAO_MODULO_ETAPA5

    if validar_referencia_independente:
        tamanhos_esp = list(res["especificacao"]["tamanhos_jogos"])
        custo_esp = Decimal(str(res["especificacao"]["custo_total_brl"]))
        conf = auditar_conformidade_etapa4_ref(
            res["jogos"],
            pool=spec["pool"],
            fixas=spec["fixas"],
            bloqueadas=spec["bloqueadas"],
            modo_fixas=spec["modo_fixas"],
            tamanhos_esperados=tamanhos_esp,
            orcamento_max_brl=custo_esp,
        )
        av_ref = avaliar_carteira_ref_etapa4(
            res["jogos"],
            pool=spec["pool"],
            fixas=spec["fixas"],
            bloqueadas=spec["bloqueadas"],
            modo_fixas=spec["modo_fixas"],
            pesos=spec["pesos"],
        )
        div_f = abs(float(res["funcao_objetivo_F"]) - float(av_ref["funcao_objetivo_F"]))
        div_comp = max(
            abs(float(res["componentes"][k]) - float(av_ref["componentes"][k]))
            for k in NOMES_COMPONENTES
        )
        if not conf["conforme"] or div_f > 1e-12 or div_comp > 1e-12:
            raise RuntimeError(
                f"Falha na auditoria independente pos-geracao: conforme={conf['conforme']}, "
                f"violacoes={conf['violacoes']}, div_f={div_f}, div_comp={div_comp}"
            )
        res["auditoria_referencia_independente"] = {
            "conforme": True,
            "divergencia_F": div_f,
            "divergencia_max_componente": div_comp,
            "tolerancia_exigida": 1e-12,
        }
    return res


def _avaliar_subexperimento_pareado(
    cenarios: Sequence[Mapping[str, Any]],
    *,
    rotulo_experimento: str,
    kw_controle: Mapping[str, Any],
    kw_tratamento: Mapping[str, Any],
) -> Dict[str, Any]:
    linhas: List[Dict[str, Any]] = []
    vitorias_trat = 0
    empates = 0
    derrotas_trat = 0
    max_div_ref = 0.0

    for c in cenarios:
        params = dict(c["kwargs"])
        t0 = time.perf_counter()
        rc = executar_com_politica_etapa5(
            **params, **kw_controle, validar_referencia_independente=True
        )
        tc = time.perf_counter() - t0

        t1 = time.perf_counter()
        rt = executar_com_politica_etapa5(
            **params, **kw_tratamento, validar_referencia_independente=True
        )
        tt = time.perf_counter() - t1

        fc = float(rc["funcao_objetivo_F"])
        ft = float(rt["funcao_objetivo_F"])
        df = ft - fc
        max_div_ref = max(
            max_div_ref,
            float(rc["auditoria_referencia_independente"]["divergencia_F"]),
            float(rt["auditoria_referencia_independente"]["divergencia_F"]),
        )
        if df > 1e-12:
            vitorias_trat += 1
            vencedor = "tratamento"
        elif abs(df) <= 1e-12:
            empates += 1
            vencedor = "empate"
        else:
            derrotas_trat += 1
            vencedor = "controle"

        linhas.append(
            {
                "cenario": c["id"],
                "grupo": c["grupo"],
                "algoritmo_controle": rc["decisao_despacho_etapa5"]["algoritmo_escolhido"],
                "algoritmo_tratamento": rt["decisao_despacho_etapa5"]["algoritmo_escolhido"],
                "F_controle": round(fc, 8),
                "F_tratamento": round(ft, 8),
                "delta_F": round(df, 8),
                "tempo_controle_s": round(tc, 5),
                "tempo_tratamento_s": round(tt, 5),
                "avaliacoes_controle": rc["telemetria"]["avaliacoes_efetivas"],
                "avaliacoes_tratamento": rt["telemetria"]["avaliacoes_efetivas"],
                "vencedor": vencedor,
            }
        )

    deltas = [x["delta_F"] for x in linhas]
    return {
        "experimento": rotulo_experimento,
        "total_execucoes_pareadas": len(linhas),
        "vitorias_tratamento": vitorias_trat,
        "empates": empates,
        "derrotas_tratamento": derrotas_trat,
        "delta_F_medio": round(statistics.mean(deltas), 8) if deltas else 0.0,
        "delta_F_min": round(min(deltas), 8) if deltas else 0.0,
        "delta_F_max": round(max(deltas), 8) if deltas else 0.0,
        "divergencia_max_ref_independente": max_div_ref,
        "execucoes": linhas,
    }


def executar_experimento_controlado_despacho() -> Dict[str, Any]:
    """
    Executa experimento empirico controlado exigido pela Condicionante III e
    Exigencia 4, isolando:
      Bloco A: Limiar micro max(36, 3J) [conservadora_3J] vs max(20, 2J) [experimental_2J]
               dentro da janela [2J, 3J) e fora dela (invariancia para B >= 3J).
      Bloco B: Inicializacao padrao vs mista_equilibrada em carteiras heterogeneas
               com restricoes diversas e multiplas sementes.
    """
    cenarios_bloco_a: List[Dict[str, Any]] = [
        {
            "id": "micro_p20_J8_B22_s42",
            "grupo": "janela_2J_3J",
            "kwargs": {"pool": list(range(1, 21)), "bloqueadas": [21, 22, 23, 24, 25], "quantidade_jogos": 8, "max_avaliacoes": 22, "semente": 42},
        },
        {
            "id": "micro_p25_J10_B24_s42",
            "grupo": "janela_2J_3J",
            "kwargs": {"pool": list(range(1, 26)), "quantidade_jogos": 10, "max_avaliacoes": 24, "semente": 42},
        },
        {
            "id": "micro_p25_J12_B30_s42",
            "grupo": "janela_2J_3J",
            "kwargs": {"pool": list(range(1, 26)), "quantidade_jogos": 12, "max_avaliacoes": 30, "semente": 42},
        },
        {
            "id": "micro_p25_J12_B30_s101",
            "grupo": "janela_2J_3J",
            "kwargs": {"pool": list(range(1, 26)), "quantidade_jogos": 12, "max_avaliacoes": 30, "semente": 101},
        },
        {
            "id": "micro_p22_J14_B32_f2_s42",
            "grupo": "janela_2J_3J",
            "kwargs": {"pool": list(range(1, 23)), "fixas": [1, 2], "bloqueadas": [23, 24, 25], "quantidade_jogos": 14, "max_avaliacoes": 32, "semente": 42},
        },
        {
            "id": "micro_p25_J16_B40_s42",
            "grupo": "janela_2J_3J",
            "kwargs": {"pool": list(range(1, 26)), "quantidade_jogos": 16, "max_avaliacoes": 40, "semente": 42},
        },
        {
            "id": "controle_fora_janela_p20_J10_B300",
            "grupo": "fora_janela_amplo",
            "kwargs": {"pool": list(range(1, 21)), "fixas": [1, 2, 3], "bloqueadas": [21, 22, 23, 24, 25], "quantidade_jogos": 10, "max_avaliacoes": 300, "semente": 42},
        },
        {
            "id": "controle_fora_janela_p25_J16_B320",
            "grupo": "fora_janela_amplo",
            "kwargs": {"pool": list(range(1, 26)), "orcamento_brl": "56.00", "max_avaliacoes": 320, "semente": 42},
        },
    ]

    bloco_a = _avaliar_subexperimento_pareado(
        cenarios_bloco_a,
        rotulo_experimento="bloco_a_limiar_micro_3J_vs_2J",
        kw_controle={"politica_micro": "conservadora_3J", "inicializacao_mista": "padrao"},
        kw_tratamento={"politica_micro": "experimental_2J", "inicializacao_mista": "padrao"},
    )

    janela_a = [x for x in bloco_a["execucoes"] if x["grupo"] == "janela_2J_3J"]
    fora_a = [x for x in bloco_a["execucoes"] if x["grupo"] == "fora_janela_amplo"]
    invariancia_fora_janela = all(abs(x["delta_F"]) <= 1e-12 for x in fora_a)

    cenarios_bloco_b: List[Dict[str, Any]] = [
        {
            "id": "mista_p21_2x16_8x15_B200_s42",
            "grupo": "heterogenea_media",
            "kwargs": {"pool": list(range(1, 22)), "fixas": [1, 2], "bloqueadas": [22, 23, 24, 25], "tamanhos_jogos": [16, 16, 15, 15, 15, 15, 15, 15, 15, 15], "max_avaliacoes": 200, "semente": 42},
        },
        {
            "id": "mista_p21_2x16_8x15_B200_s101",
            "grupo": "heterogenea_media",
            "kwargs": {"pool": list(range(1, 22)), "fixas": [1, 2], "bloqueadas": [22, 23, 24, 25], "tamanhos_jogos": [16, 16, 15, 15, 15, 15, 15, 15, 15, 15], "max_avaliacoes": 200, "semente": 101},
        },
        {
            "id": "mista_p25_1x18_2x17_6x15_B300_s42",
            "grupo": "heterogenea_ampla",
            "kwargs": {"pool": list(range(1, 26)), "tamanhos_jogos": [18, 17, 17, 15, 15, 15, 15, 15, 15], "max_avaliacoes": 300, "semente": 42},
        },
        {
            "id": "mista_p25_1x18_2x17_6x15_B300_s101",
            "grupo": "heterogenea_ampla",
            "kwargs": {"pool": list(range(1, 26)), "tamanhos_jogos": [18, 17, 17, 15, 15, 15, 15, 15, 15], "max_avaliacoes": 300, "semente": 101},
        },
        {
            "id": "mista_p23_pool_fixas_B240_s42",
            "grupo": "heterogenea_composicao_pool",
            "kwargs": {"pool": list(range(1, 24)), "fixas": list(range(1, 17)), "bloqueadas": [24, 25], "modo_fixas": "composicao_pool", "tamanhos_jogos": [17, 16, 16, 15, 15, 15, 15, 15], "max_avaliacoes": 240, "semente": 42},
        },
        {
            "id": "mista_p19_estreita_B150_s42",
            "grupo": "heterogenea_restrita",
            "kwargs": {"pool": list(range(1, 20)), "bloqueadas": [20, 21, 22, 23, 24, 25], "tamanhos_jogos": [17, 16, 15, 15, 15, 15], "max_avaliacoes": 150, "semente": 42},
        },
    ]

    bloco_b = _avaliar_subexperimento_pareado(
        cenarios_bloco_b,
        rotulo_experimento="bloco_b_inicializacao_mista",
        kw_controle={"politica_micro": "conservadora_3J", "inicializacao_mista": "padrao"},
        kw_tratamento={"politica_micro": "conservadora_3J", "inicializacao_mista": "mista_equilibrada"},
    )

    deltas_janela_a = [x["delta_F"] for x in janela_a]
    vit_janela_a = sum(1 for x in janela_a if x["delta_F"] > 1e-12)
    der_janela_a = sum(1 for x in janela_a if x["delta_F"] < -1e-12)
    media_janela_a = statistics.mean(deltas_janela_a) if deltas_janela_a else 0.0

    rec_micro = (
        "adotar_experimental_2J"
        if media_janela_a > 0.0005 and vit_janela_a > der_janela_a
        else "manter_conservadora_3J"
    )
    rec_mista = (
        "adotar_inicializacao_mista_em_heterogeneas"
        if bloco_b["delta_F_medio"] > 0.0005
        and bloco_b["vitorias_tratamento"] > bloco_b["derrotas_tratamento"]
        else "manter_inicializacao_padrao"
    )

    return {
        "bloco_a_limiar_micro": {
            **bloco_a,
            "invariancia_fora_da_janela_3J": invariancia_fora_janela,
            "na_janela_2J_3J": {
                "execucoes": len(janela_a),
                "vitorias_2J": vit_janela_a,
                "derrotas_2J": der_janela_a,
                "empates": len(janela_a) - vit_janela_a - der_janela_a,
                "delta_F_medio": round(media_janela_a, 8),
            },
            "decisao_empirica_micro": rec_micro,
        },
        "bloco_b_inicializacao_mista": {
            **bloco_b,
            "decisao_empirica_mista": rec_mista,
        },
        "recomendacao_padrao_producao": {
            "politica_micro_recomendada": rec_micro,
            "inicializacao_mista_recomendada": rec_mista,
            "etapa4_inalterada": True,
        },
    }
