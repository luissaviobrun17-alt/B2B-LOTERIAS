# LOTOFACIL MODO 4 : ETAPA 1 (Regras Oficiais e Formalizacao Matematica)

## 1. Fonte Oficial Conferida e Parametros da Modalidade
- **Pagina oficial CAIXA:** `https://loterias.caixa.gov.br/Paginas/Lotofacil.aspx`
- **API oficial CAIXA:** `https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil`
- **Data da conferencia:** `2026-11-13`
- **Universo / Sorteio / Aposta:** 25 dezenas (`01` a `25`), `15` sorteadas, apostas de `15` a `20` dezenas, faixas premiadas `11, 12, 13, 14 e 15` acertos.
- **Espaco amostral simples:** $C(25, 15) = 3.268.760$
- **Aposta simples / Premios fixos / Premio bruto:** `R$ 3.50` | `11 acertos: R$ 7,00`, `12 acertos: R$ 14,00`, `13 acertos: R$ 35,00` | `43,79%` da arrecadacao.

### Tabela Oficial de Desdobramento e Custos (15 a 20 dezenas)
| Dezenas (m) | Combinacoes C(m, 15) | Valor Oficial (R$) |
| :---: | :---: | :---: |
| 15 | 1 | R$ 3.50 |
| 16 | 16 | R$ 56.00 |
| 17 | 136 | R$ 476.00 |
| 18 | 816 | R$ 2856.00 |
| 19 | 3876 | R$ 13566.00 |
| 20 | 15504 | R$ 54264.00 |

### 1.1 Regras de Premiacao Versionadas (Regular, Final Zero e Independência)

- **`regras_premiacao_regular`** (versao `2025.07-v1`, vigencia desde concurso `3439` em `2025-07-10`, fonte `https://loterias.caixa.gov.br/Paginas/Lotofacil.aspx`): saldo variavel [15_acertos: 0.62, 14_acertos: 0.13, acumulado_final_zero: 0.10, acumulado_independencia: 0.15].
- **`regras_premiacao_final_zero`** (versao `2025.07-v1`, vigencia desde concurso `3439` em `2025-07-10`, fonte `https://loterias.caixa.gov.br/Paginas/Lotofacil.aspx`): saldo variavel [15_acertos: 0.72, 14_acertos: 0.13, acumulado_independencia: 0.15].
- **`regras_premiacao_independencia`** (versao `2025.07-v1`, vigencia desde concurso `3439` em `2025-07-10`, fonte `https://loterias.caixa.gov.br/Paginas/Lotofacil.aspx`): saldo variavel [15_acertos: 0.87, 14_acertos: 0.13].

## 2. Distribuicao Hipergeometrica Exata H(25, 15, m)
Para cada tamanho de aposta $m \in \{15, \dots, 20\}$ e cada $k$ acertos:
$$P(X = k \mid m) = \frac{C(m, k) \cdot C(25 - m, 15 - k)}{C(25, 15)}$$

| m | k = 15 (1 em X) | k = 14 (1 em X) | k = 13 (1 em X) | k = 12 (1 em X) | k = 11 (1 em X) | P(X >= 11) | E[X] |
| :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 15 | 3268760.00 (1/3268760) | 21791.73 | 691.80 | 59.87 | 11.40 | 10.5889% | 9 |
| 16 | 204297.50 (2/408595) | 3026.63 | 162.14 | 21.38 | 5.94 | 22.1645% | 48/5 |
| 17 | 24035.00 (1/24035) | 600.88 | 49.05 | 9.43 | 3.77 | 39.3135% | 51/5 |
| 18 | 4005.83 (6/24035) | 152.60 | 18.17 | 5.03 | 2.93 | 60.1373% | 54/5 |
| 19 | 843.33 (3/2530) | 46.85 | 8.03 | 3.24 | 2.88 | 80.2174% | 57/5 |
| 20 | 210.83 (6/1265) | 16.87 | 4.22 | 2.59 | 3.89 | 94.3478% | 12 |

## 3. Distincao Formal das Grandezas Combinatorias e Probabilisticas (Secao 3)
1. **Probabilidade individual de um bilhete:** 15733/148580 (10.5889% em aposta simples de 15 dezenas).
2. **Probabilidade de pelo menos um bilhete premiado:** $P(\bigcup_{i=1}^J A_i)$, dependente da estrutura de intersecao conjunta via inclusao-exclusao.
3. **Distribuicao do numero de premiacoes $N_{\text{prem}}(C)$:** dispersao redistribui massa entre eventos multiplos simultaneos e eventos unitarios sem alterar a esperanca.
4. **Quantidade esperada de bilhetes premiados:** $E[N_{\text{prem}}(C)] = J \cdot P(H_1 \ge 11)$, invariante sob qualquer selecao de $J$ bilhetes simples.
5. **Cobertura combinatoria $Cov_t(C)$:** fracao deterministica dos subconjuntos de tamanho $t$ cobertos; nao equivale a garantia automatica de premio sem prova condicional.

## 4. Auditoria da Base Historica Oficial Sincronizada (CAIXA)
- **Versao do sincronizador:** `1.1.0-etapa1-homologada`
- **Origem verificada:** `https://loterias.caixa.gov.br/Paginas/Lotofacil.aspx (Planilha Oficial CAIXA .xlsx)`
- **Planilha oficial CAIXA:** `lotofacil_modo4/dados/caixa_lotofacil_oficial.xlsx` (SHA-256: `fd32f9578200e36e8c714526854d8d6dcee5a6a7d03fa625115a11e1be09251c`)
- **Arquivo canonico:** `lotofacil_modo4/dados/lotofacil_oficial_caixa.json`
- **Periodo completo:** concurso `1` (29/09/2003) ate `3828` (12/11/2026)
- **Total de concursos / Ausentes / Duplicados:** `3828` / `0` / `0`
- **SHA-256 arquivo:** `df31c4bce233ff65f9dc032595595aa7d73f819bfc5a67c1dd87bbd793c257f8`
- **SHA-256 lista canonica:** `121c645b1f84f9cf868a099bddf4ea06e28e177e45aef4eee467a7a5c6a54a57`
- **Confronto contra base legada (`data/lotofacil.json`):** `3246` confrontados, `0` divergencias de dezenas, `582` concursos novos recuperados.
- **Confronto cruzado contra amostra da API JSON CAIXA:** `161` confrontados, `0` divergencias.
- **Ordem de sorteio fisica:** planilha CAIXA possui dezenas em ordem crescente; campo `ordem_sorteio` mantido vazio `[]` sem preenchimento artificial.

### 4.1 Registro Auditavel de Transformacoes Aplicadas
- 1. Leitura direta de xl/sharedStrings.xml e xl/worksheets/sheet1.xml via stdlib zipfile + xml.etree.ElementTree (sem macros ou inferencias).
- 2. Mapeamento explicito de cabecalhos e referencias de coluna Excel (suportando celulas esparsas e sequenciais).
- 3. Conversao deterministica de valores monetarios 'R$...' para float e inteiros de ganhadores.
- 4. Validacao estrita de data DD/MM/YYYY -> YYYY-MM-DD e de 15 dezenas unicas no intervalo [1..25].
- 5. Ordenacao crescente por numero de concurso (1..3828), verificando ausencia de lacunas e duplicatas, preservando ordem_sorteio=[] na ausencia de ordem fisica.
- 6. Serializacao UTF-8 deterministica da lista de concursos e calculo de SHA-256 do arquivo XLSX, do JSON completo e da lista canonica.

## 5. Clausula Matematica Obrigatoria e Independencia dos Sorteios
> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.

- **Regra de independencia em codigo:** `validar_natureza_componente` proibe atribuir ganho preditivo ou alteracao da probabilidade futura a historico, frequencia, atraso ou coocorrencia.

## 6. Estado de Homologacao da Etapa 1
Etapa 1 homologada com ressalvas tecnicas incorporadas (versionamento das regras de premiacao regular/final zero/independencia, linhagem completa da base e garantia de independencia em codigo).
