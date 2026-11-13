# -*- coding: utf-8 -*-
"""
GERADOR DE EVIDENCIAS VERIFICAVEIS: ETAPA 1 (LOTOFACIL MODO 4)
=================================================================
Consolida as definicoes matematicas exatas de etapa1_regras_oficiais e o
relatorio de auditoria da base CAIXA sincronizada em:
  - auditoria/lotofacil_modo4/etapa_01_evidencias.json
  - auditoria/lotofacil_modo4/ETAPA_01_REGRAS_E_FORMALIZACAO_MATEMATICA.md
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict

from .etapa1_regras_oficiais import (
    API_OFICIAL_CAIXA_URL,
    CLAUSULA_MATEMATICA_OBRIGATORIA,
    ESCALA_APOSTAS_OFICIAIS,
    RATEIO_SALDO_VARIAVEL,
    gerar_resumo_formal_etapa1,
)
from .sincronizador_caixa import calcular_sha256_arquivo


def gerar_pacote_etapa1(diretorio_repo: str | None = None) -> Dict[str, Any]:
    base_dir = diretorio_repo or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta_aud = os.path.join(base_dir, "auditoria", "lotofacil_modo4")
    os.makedirs(pasta_aud, exist_ok=True)

    caminho_base_aud = os.path.join(pasta_aud, "auditoria_base_caixa_etapa1.json")
    if not os.path.isfile(caminho_base_aud):
        raise FileNotFoundError(
            f"Relatorio de sincronizacao da base CAIXA nao encontrado: {caminho_base_aud}"
        )

    with open(caminho_base_aud, "r", encoding="utf-8") as f:
        auditoria_base = json.load(f)

    resumo_formal = gerar_resumo_formal_etapa1()

    artefatos_codigo = {
        "lotofacil_modo4/__init__.py": calcular_sha256_arquivo(
            os.path.join(base_dir, "lotofacil_modo4", "__init__.py")
        ),
        "lotofacil_modo4/etapa1_regras_oficiais.py": calcular_sha256_arquivo(
            os.path.join(base_dir, "lotofacil_modo4", "etapa1_regras_oficiais.py")
        ),
        "lotofacil_modo4/sincronizador_caixa.py": calcular_sha256_arquivo(
            os.path.join(base_dir, "lotofacil_modo4", "sincronizador_caixa.py")
        ),
        "lotofacil_modo4/gerar_evidencias_etapa1.py": calcular_sha256_arquivo(
            os.path.join(base_dir, "lotofacil_modo4", "gerar_evidencias_etapa1.py")
        ),
        "testes/test_lotofacil_modo4_etapa1.py": calcular_sha256_arquivo(
            os.path.join(base_dir, "testes", "test_lotofacil_modo4_etapa1.py")
        ),
    }

    evidencias = {
        **resumo_formal,
        "auditoria_base_caixa": auditoria_base,
        "hashes_artefatos_etapa1": artefatos_codigo,
    }

    caminho_json = os.path.join(pasta_aud, "etapa_01_evidencias.json")
    with open(caminho_json, "w", encoding="utf-8") as f_json:
        json.dump(evidencias, f_json, ensure_ascii=False, indent=2)
        f_json.write("\n")

    espaco_str = f"{resumo_formal['regras_oficiais']['espaco_amostral_simples']:,}".replace(",", ".")
    linhas_md = [
        "# LOTOFACIL MODO 4 : ETAPA 1 (Regras Oficiais e Formalizacao Matematica)",
        "",
        "## 1. Fonte Oficial Conferida e Parametros da Modalidade",
        f"- **Pagina oficial CAIXA:** `{resumo_formal['fonte_oficial_url']}`",
        f"- **API oficial CAIXA:** `{API_OFICIAL_CAIXA_URL}`",
        f"- **Data da conferencia:** `{resumo_formal['data_conferencia_caixa']}`",
        f"- **Universo / Sorteio / Aposta:** 25 dezenas (`01` a `25`), `15` sorteadas, apostas de `15` a `20` dezenas, faixas premiadas `11, 12, 13, 14 e 15` acertos.",
        f"- **Espaco amostral simples:** $C(25, 15) = {espaco_str}$",
        f"- **Aposta simples / Premios fixos / Premio bruto:** `R$ {resumo_formal['regras_oficiais']['preco_aposta_simples_brl']}` | `11 acertos: R$ 7,00`, `12 acertos: R$ 14,00`, `13 acertos: R$ 35,00` | `43,79%` da arrecadacao.",
        "",
        "### Tabela Oficial de Desdobramento e Custos (15 a 20 dezenas)",
        "| Dezenas (m) | Combinacoes C(m, 15) | Valor Oficial (R$) |",
        "| :---: | :---: | :---: |",
    ]
    for m in range(15, 21):
        row = ESCALA_APOSTAS_OFICIAIS[m]
        linhas_md.append(f"| {m} | {row['combinacoes_simples']} | R$ {row['valor_aposta_brl']} |")

    linhas_md.extend(
        [
            "",
            "### 1.1 Regras de Premiacao Versionadas (Regular, Final Zero e Independência)",
            "",
        ]
    )
    for chave, reg in resumo_formal["regras_premiacao_versionadas"].items():
        rateio_fmt = ", ".join(f"{k}: {v}" for k, v in reg["rateio_saldo_variavel"].items())
        linhas_md.append(
            f"- **`{chave}`** (versao `{reg['versao_regra']}`, vigencia desde concurso `{reg['vigencia_desde_concurso']}` em `{reg['vigencia_desde_data']}`, fonte `{reg['fonte_oficial_url']}`): "
            f"saldo variavel [{rateio_fmt}]."
        )

    linhas_md.extend(
        [
            "",
            "## 2. Distribuicao Hipergeometrica Exata H(25, 15, m)",
            "Para cada tamanho de aposta $m \\in \\{15, \\dots, 20\\}$ e cada $k$ acertos:",
            "$$P(X = k \\mid m) = \\frac{C(m, k) \\cdot C(25 - m, 15 - k)}{C(25, 15)}$$",
            "",
            "| m | k = 15 (1 em X) | k = 14 (1 em X) | k = 13 (1 em X) | k = 12 (1 em X) | k = 11 (1 em X) | P(X >= 11) | E[X] |",
            "| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |",
        ]
    )

    dists = resumo_formal["distribuicoes_hipergeometricas_15_a_20"]
    for m_str in ("15", "16", "17", "18", "19", "20"):
        d = dists[m_str]
        dm = d["distribuicao"]
        linhas_md.append(
            f"| {m_str} | {dm['15']['chance_1_em']:.2f} ({dm['15']['probabilidade_fracao']}) "
            f"| {dm['14']['chance_1_em']:.2f} | {dm['13']['chance_1_em']:.2f} "
            f"| {dm['12']['chance_1_em']:.2f} | {dm['11']['chance_1_em']:.2f} "
            f"| {d['probabilidade_alguma_premiacao_percentual']:.4f}% | {d['valor_esperado_acertos']} |"
        )

    linhas_md.extend(
        [
            "",
            "## 3. Distincao Formal das Grandezas Combinatorias e Probabilisticas (Secao 3)",
            (
                "1. **Probabilidade individual de um bilhete:** "
                f"{dists['15']['probabilidade_alguma_premiacao_exata']} "
                f"({dists['15']['probabilidade_alguma_premiacao_percentual']:.4f}% em aposta simples de 15 dezenas)."
            ),
            "2. **Probabilidade de pelo menos um bilhete premiado:** $P(\\bigcup_{i=1}^J A_i)$, dependente da estrutura de intersecao conjunta via inclusao-exclusao.",
            "3. **Distribuicao do numero de premiacoes $N_{\\text{prem}}(C)$:** dispersao redistribui massa entre eventos multiplos simultaneos e eventos unitarios sem alterar a esperanca.",
            "4. **Quantidade esperada de bilhetes premiados:** $E[N_{\\text{prem}}(C)] = J \\cdot P(H_1 \\ge 11)$, invariante sob qualquer selecao de $J$ bilhetes simples.",
            "5. **Cobertura combinatoria $Cov_t(C)$:** fracao deterministica dos subconjuntos de tamanho $t$ cobertos; nao equivale a garantia automatica de premio sem prova condicional.",
            "",
            "## 4. Auditoria da Base Historica Oficial Sincronizada (CAIXA)",
            f"- **Versao do sincronizador:** `{auditoria_base.get('versao_sincronizador')}`",
            f"- **Origem verificada:** `{auditoria_base['origem_oficial']}`",
            f"- **Planilha oficial CAIXA:** `{auditoria_base.get('arquivo_planilha_oficial')}` (SHA-256: `{auditoria_base.get('sha256_planilha_oficial_caixa')}`)",
            f"- **Arquivo canonico:** `{auditoria_base['arquivo_canonico']}`",
            f"- **Periodo completo:** concurso `{auditoria_base['primeiro_concurso']}` ({auditoria_base['primeiro_data_apuracao']}) ate `{auditoria_base['ultimo_concurso']}` ({auditoria_base['ultimo_data_apuracao']})",
            f"- **Total de concursos / Ausentes / Duplicados:** `{auditoria_base['total_concursos']}` / `{auditoria_base.get('relatorio_integridade_concursos', {}).get('qtd_ausentes', auditoria_base['concursos_faltantes'])}` / `{auditoria_base.get('relatorio_integridade_concursos', {}).get('qtd_duplicados', 0)}`",
            f"- **SHA-256 arquivo:** `{auditoria_base['sha256_arquivo']}`",
            f"- **SHA-256 lista canonica:** `{auditoria_base['sha256_lista_concursos_canonica']}`",
            f"- **Confronto contra base legada (`data/lotofacil.json`):** `{auditoria_base['confronto_base_legada'].get('concursos_confrontados')}` confrontados, `{auditoria_base['confronto_base_legada'].get('qtd_divergencias_conjunto')}` divergencias de dezenas, `{auditoria_base['confronto_base_legada'].get('novos_concursos_apos_legado')}` concursos novos recuperados.",
            f"- **Confronto cruzado contra amostra da API JSON CAIXA:** `{auditoria_base.get('confronto_amostra_api_caixa', {}).get('concursos_api_confrontados', 0)}` confrontados, `{auditoria_base.get('confronto_amostra_api_caixa', {}).get('qtd_divergencias_api_vs_planilha', 0)}` divergencias.",
            "- **Ordem de sorteio fisica:** planilha CAIXA possui dezenas em ordem crescente; campo `ordem_sorteio` mantido vazio `[]` sem preenchimento artificial.",
            "",
            "### 4.1 Registro Auditavel de Transformacoes Aplicadas",
            *[f"- {passo}" for passo in auditoria_base.get("registro_transformacoes", [])],
            "",
            "## 5. Clausula Matematica Obrigatoria e Independencia dos Sorteios",
            f"> {CLAUSULA_MATEMATICA_OBRIGATORIA}",
            "",
            "- **Regra de independencia em codigo:** `validar_natureza_componente` proibe atribuir ganho preditivo ou alteracao da probabilidade futura a historico, frequencia, atraso ou coocorrencia.",
            "",
            "## 6. Estado de Homologacao da Etapa 1",
            "Etapa 1 homologada com ressalvas tecnicas incorporadas (versionamento das regras de premiacao regular/final zero/independencia, linhagem completa da base e garantia de independencia em codigo).",
            "",
        ]
    )

    caminho_md = os.path.join(pasta_aud, "ETAPA_01_REGRAS_E_FORMALIZACAO_MATEMATICA.md")
    with open(caminho_md, "w", encoding="utf-8") as f_md:
        f_md.write("\n".join(linhas_md))

    return {
        "evidencias_json": caminho_json,
        "relatorio_md": caminho_md,
        "hashes_artefatos_etapa1": artefatos_codigo,
    }


if __name__ == "__main__":
    out = gerar_pacote_etapa1()
    print(json.dumps(out, ensure_ascii=False, indent=2))
