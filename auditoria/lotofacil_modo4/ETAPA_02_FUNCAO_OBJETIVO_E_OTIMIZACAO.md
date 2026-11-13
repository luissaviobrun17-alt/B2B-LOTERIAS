# LOTOFACIL MODO 4 : ETAPA 2 (Funcao Objetivo e Criterios de Otimizacao)

## 1. Definicao Matematica da Funcao Objetivo Principal
Para uma carteira admissivel $C = \{B_1, \dots, B_J\}$ dentro de um pool candidato $P \subseteq \{1, \dots, 25\}$ ($|P| = p \in [15, 25]$), respeitando dezenas fixas $F \subseteq P$ ($|F| = f$) segundo `modo_fixas` (`todos_os_jogos` ou `composicao_pool`) e dezenas bloqueadas $E$ ($E \cap P = \emptyset$, $F \cap E = \emptyset$), a funcao objetivo principal de maximizacao $F_{\text{MODO4}}(C \mid P, \theta) \in [0, 1]$ (equivalente a perda $L(C) = 1 - F(C)$) e definida por:

$$F_{\text{MODO4}}(C \mid P, \theta) = w_{\text{cov}} S_{\text{cov}}(C) + w_{\text{prob}} S_{\text{prob}}(C) + w_{\text{div}} S_{\text{div}}(C) + w_{\text{dist}} S_{\text{dist}}(C) + w_{\text{cb}} S_{\text{cb}}(C) + w_{\text{est}} S_{\text{div\_est}}(C)$$

### 1.1 Classificacao Epistemologica e Pesos Justificados (`padrao_modo4`)
| Componente | Simbolo | Fundamento Cientifico | Peso | Papel Matematico |
| :--- | :---: | :---: | :---: | :--- |
| `cobertura_combinatoria` | `S_cov` | **EXATO** | `0.30` | Media ponderada da eficiencia combinatoria exata de cobertura de subconjuntos t in {1,2,3,4} em P normalizada pela cota intransponivel U_t(J, p, f). |
| `probabilidade_conjunta` | `S_prob` | **EXATO** | `0.25` | Metrica de otimizacao baseada em probabilidades pareadas exatas p_2(m_i, m_k, I_ik) e limites matematicos (Cauchy-Schwarz, Dawson-Sankoff e Hunter-Worsley), reduzindo a soma de covariancias e a variancia Var(N_prem(C)); nao deve ser confundida com o valor exato de P(U_i A_i) em carteiras com 3 ou mais bilhetes. |
| `diversificacao_sobreposicao` | `S_div` | **HEURISTICO** | `0.20` | Penalizacao quadratica de picos de sobreposicao I_ij acima da cota minima teorica combinada ao excesso medio normalizado entre pares de bilhetes. |
| `distribuicao_dezenas` | `S_dist` | **HEURISTICO** | `0.10` | Aproximacao ao equilibrio uniforme inteiro u_d das dezenas livres do pool, evitando concentracao artificial ou abandono de candidatas. |
| `custo_beneficio` | `S_cb` | **EXATO** | `0.10` | Unicidade exata de combinacoes simples pagas combinada a densidade de pares cobertos por investimento em comparacao ao limite combinatorio do orcamento. |
| `diversidade_estrutural` | `S_div_est` | **HEURISTICO** | `0.05` | Dispersao dos perfis estruturais (paridade, moldura/centro, faixas de soma) e equilibrio de ocupacao de linhas e colunas da matriz 5x5 sem carater preditivo. |
| Indicadores historicos (frequencia, atraso, lift, aderencia modal) | N/A | **DESCRITIVO** | `0.00` | Painel estatistico isolado; proibido de atuar como ganho preditivo |

### 1.2 Distincao Obrigatoria das Cinco Grandezas Probabilisticas (Ressalva 2.1)
1. **Probabilidade individual de cada bilhete:** $P(A_i) = P(|B_i \cap S| \ge 11)$ para $m_i \in [15, 20]$.
2. **Probabilidade pareada simultanea:** $p_2(m_i, m_k, c) = P(A_i \cap A_k)$ pela particao hipergeometrica de 4 regioes.
3. **Esperanca e variancia de bilhetes premiados:** $E[N_{\text{prem}}(C)] = \sum_i P(A_i)$ e $\operatorname{Var}(N_{\text{prem}}(C))$ exata via covariancias pareadas.
4. **Limites matematicos da uniao ($P(\bigcup A_i)$):** cota inferior de Dawson-Sankoff e cota superior de Hunter-Worsley (`S_prob` usa probabilidades pareadas e cotas como metrica de otimizacao, nao sendo igual a $P(\bigcup A_i)$ quando $J \ge 3$).
5. **Probabilidade exata da uniao:** calculada por inclusao-exclusao fechada para $J \le 2$, ou explicitamente marcada como `nao_calculada_diretamente` para $J \ge 3$ salvo enumeracao direta do espaco amostral.

### 1.3 Definicao Formal de Dezenas Fixas e Compatibilidade (Ressalva 2.4)
- **`todos_os_jogos`:** exige $F \subseteq B_i \subseteq P$ para todo bilhete $B_i \in C$, $|F| \le m_{\min}$, $F \cap E = P \cap E = \emptyset$ e $J \le C(|P \setminus F|, m - |F|)$.
- **`composicao_pool`:** exige $F \subseteq P$ apenas na formacao e manutencao do pool (permitindo $|F| > m$ ate $|P|$, ex.: `17` fixas em `p = 20`), variando cada bilhete livremente em $P$ com teto $J \le C(|P|, m)$.

## 2. Probabilidade Conjunta Pareada $p_2(m_1, m_2, c)$ em Quatro Regioes (15 a 20 Dezenas)
Para quaisquer dois bilhetes $B_1$ ($m_1$) e $B_2$ ($m_2$) com intersecao $c = |B_1 \cap B_2|$, o universo de 25 dezenas particiona-se em $(n_0, n_1, n_2, n_3) = (c, m_1 - c, m_2 - c, 25 - m_1 - m_2 + c)$:

$$p_2(m_1, m_2, c) = \frac{1}{\binom{25}{15}} \sum_{x_0, x_1, x_2 : x_0+x_1 \ge 11,\; x_0+x_2 \ge 11} \binom{n_0}{x_0}\binom{n_1}{x_1}\binom{n_2}{x_2}\binom{n_3}{15 - x_0 - x_1 - x_2}$$

| c = |B_i inter B_k| (15x15) | p_2(c) Fracao Exata | p_2(c) Decimal | Covariancia p_2(c) - p_1^2 | Correlacao Pearson | P(A_i U A_k) Exata |
| :---: | :---: | :---: | :---: | :---: | :---: |
| 5 | `0/1` | 0.000000 | -0.011212 | -0.1184 | 21.1778% |
| 6 | `0/1` | 0.000000 | -0.011212 | -0.1184 | 21.1778% |
| 7 | `245/163438` | 0.001499 | -0.009713 | -0.1026 | 21.0279% |
| 8 | `3185/653752` | 0.004872 | -0.006341 | -0.0670 | 20.6906% |
| 9 | `1625/163438` | 0.009943 | -0.001270 | -0.0134 | 20.1836% |
| 10 | `2725/163438` | 0.016673 | +0.005460 | +0.0577 | 19.5105% |
| 11 | `1493/59432` | 0.025121 | +0.013909 | +0.1469 | 18.6657% |
| 12 | `2117/59432` | 0.035621 | +0.024408 | +0.2578 | 17.6158% |
| 13 | `727/14858` | 0.048930 | +0.037717 | +0.3984 | 16.2848% |
| 14 | `500/7429` | 0.067304 | +0.056091 | +0.5925 | 14.4474% |
| 15 | `15733/148580` | 0.105889 | +0.094677 | +1.0000 | 10.5889% |

Observa-se matematicamente que $p_2(5) = p_2(6) = 0.000000$ (impossibilidade exata de premiacao simultanea quando $c \le 6$, pois $11 + 11 - 15 = 7 > c$) e, para $c \in [7, 15]$, ocorre crescimento estrito $p_2(6) = 0 < p_2(7) < \dots < p_2(15) = 0.105889 = p_1$: reduzir sobreposicao (ate $c \le 6$, onde os eventos de premiacao se tornam disjuntos) diminui a covariancia pareada e a variancia exata $\operatorname{Var}(N_{\text{prem}}(C)) = \sum_i p_i(1-p_i) + 2\sum_{i<k}(p_2(I_{ik}) - p_i p_k)$.

### 2.1 Extremos da Formula 4-Regioes para Apostas Multiplas (15x15 ate 20x20)
| Par (m1 x m2) | c_min | c_max | p_2(c_min) Exata | p_2(c_max) Exata | Regioes (n0, n1, n2, n3) em c_min |
| :---: | :---: | :---: | :---: | :---: | :---: |
| `15x15` | 5 | 15 | `0/1` (0.000000) | `15733/148580` (0.105889) | (5, 10, 10, 0) |
| `15x16` | 6 | 15 | `0/1` (0.000000) | `15733/148580` (0.105889) | (6, 9, 10, 0) |
| `15x17` | 7 | 15 | `735/163438` (0.004497) | `15733/148580` (0.105889) | (7, 8, 10, 0) |
| `15x18` | 8 | 15 | `7035/326876` (0.021522) | `15733/148580` (0.105889) | (8, 7, 10, 0) |
| `15x19` | 9 | 15 | `34725/653752` (0.053116) | `15733/148580` (0.105889) | (9, 6, 10, 0) |
| `15x20` | 10 | 15 | `14275/163438` (0.087342) | `15733/148580` (0.105889) | (10, 5, 10, 0) |
| `16x16` | 7 | 16 | `3969/817190` (0.004857) | `8233/37145` (0.221645) | (7, 9, 9, 0) |
| `16x17` | 8 | 16 | `10437/408595` (0.025544) | `8233/37145` (0.221645) | (8, 8, 9, 0) |
| `16x18` | 9 | 16 | `57939/817190` (0.070900) | `8233/37145` (0.221645) | (9, 7, 9, 0) |
| `16x19` | 10 | 16 | `440871/3268760` (0.134874) | `8233/37145` (0.221645) | (10, 6, 9, 0) |
| `16x20` | 11 | 16 | `28733/148580` (0.193384) | `8233/37145` (0.221645) | (11, 5, 9, 0) |
| `17x17` | 9 | 17 | `31752/408595` (0.077710) | `859/2185` (0.393135) | (9, 8, 8, 0) |
| `17x18` | 10 | 17 | `134869/817190` (0.165040) | `859/2185` (0.393135) | (10, 7, 8, 0) |
| `17x19` | 11 | 17 | `80081/297160` (0.269488) | `859/2185` (0.393135) | (11, 6, 8, 0) |
| `17x20` | 12 | 17 | `52743/148580` (0.354980) | `859/2185` (0.393135) | (12, 5, 8, 0) |
| `18x18` | 11 | 18 | `44513/148580` (0.299589) | `1314/2185` (0.601373) | (11, 7, 7, 0) |
| `18x19` | 12 | 18 | `132091/297160` (0.444511) | `1314/2185` (0.601373) | (12, 6, 7, 0) |
| `18x20` | 13 | 18 | `82423/148580` (0.554738) | `1314/2185` (0.601373) | (13, 5, 7, 0) |
| `19x19` | 13 | 19 | `92303/148580` (0.621234) | `369/460` (0.802174) | (13, 6, 6, 0) |
| `19x20` | 14 | 19 | `222761/297160` (0.749633) | `369/460` (0.802174) | (14, 5, 6, 0) |
| `20x20` | 15 | 20 | `263841/297160` (0.887875) | `217/230` (0.943478) | (15, 5, 5, 0) |

## 3. Prova em Forca Bruta no Universo Completo (3.268.760 Sorteios : Casos Nominais)
Escopo (`VALIDACAO_EXAUSTIVA_UNIVERSO_SORTEIOS`): enumera todos os 3.268.760 sorteios para validar as formulas exatas nos 5 casos abaixo (incluindo pares heterogeneos de apostas multiplas); nao enumera todas as carteiras possiveis do espaco de busca.

| Caso | Dimensoes | P(N_prem >= 1) Exata | Cota [DS, HW] | E[N_prem] Exata | Var(N_prem) Universo vs Formula |
| :--- | :---: | :---: | :---: | :---: | :---: |
| `ex_j2_p16_I14` | `[15,15]` | 14.4474% (`10733/74290`) | [14.4474%, 14.4474%] | `15733/74290` | 0.301536 vs 0.301536 |
| `ex_j3_p18_dispersa` | `[15,15,15]` | 22.9519% (`750243/3268760`) | [21.0806%, 24.6426%] | `47199/148580` | 0.430478 vs 0.430478 |
| `ex_j3_p18_concentrada` | `[15,15,15]` | 16.5911% (`24651/148580`) | [14.4474%, 18.3060%] | `47199/148580` | 0.620578 vs 0.620578 |
| `ex_multipla_m16_m15_I7` | `[16,15]` | 32.4836% (`106181/326876`) | [32.4836%, 32.4836%] | `9733/29716` | 0.225652 vs 0.225652 |
| `ex_multipla_m18_m17_I12` | `[18,17]` | 76.4948% (`28414/37145`) | [76.4948%, 76.4948%] | `2173/2185` | 0.464581 vs 0.464581 |

## 4. Comparativo Custo x Combinacoes Simples x Cobertura (Orcamento R$ 56,00)
| Estrategia (R$ 56,00) | Jogos | Comb. Simples (Pagas/Unicas) | Pares Cobertos | Trincas Cobertas | Var(N_prem) | Intervalo [DS, HW] P(U A_i) | Score F(C) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `1_aposta_multipla_16_dezenas_fechada` | 1 | 16 / 16 | 120 | 560 | 0.1725 | [22.16%, 22.16%] | 0.9952 |
| `16_apostas_simples_em_pool_16` | 16 | 16 / 16 | 120 | 560 | 14.9767 | [16.12%, 68.47%] | 0.9745 |
| `16_apostas_simples_em_pool_18` | 16 | 16 / 16 | 153 | 816 | 8.6959 | [24.90%, 68.47%] | 0.9826 |
| `16_apostas_simples_em_pool_20` | 16 | 16 / 16 | 190 | 1140 | 5.5858 | [33.96%, 73.98%] | 0.9708 |
| `16_apostas_simples_em_pool_25` | 16 | 16 / 16 | 300 | 2039 | 2.7970 | [51.60%, 80.82%] | 0.9348 |

## 5. Analise de Sensibilidade dos Pesos (Escopo Controlado) e Desempate
- **Escopo (`COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`):** `34` cenarios avaliados sobre o conjunto fixo de 5 carteiras em `p=20, J=4`; indica estabilidade local nesse conjunto de teste e nao prova invariancia universal para qualquer pool, orcamento ou quantidade $J$.
- **Estabilidade da solucao vencedora (`C1_dispersa_equilibrada`):** `34/34` cenarios (`100.0%`).
- **Preservacao integral do ranking completo (`C1 > C2 > C3 > C4 > C5`):** `34/34` cenarios.
- **Criterio deterministico de desempate (`chave_desempate_deterministica`):** tupla lexicografica `(F(C), S_cov, S_prob, -I_max, -SS_obs, -carteira_canonica)` garantindo ordem total unica e reprodutivel.

## 6. Clausula Matematica Obrigatoria
> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.

## 7. Estado de Homologacao Condicionada da Etapa 2
Ressalvas 2.1 a 2.4 integralmente incorporadas em codigo, referencia independente, evidencias JSON/MD e testes de aceitacao.
