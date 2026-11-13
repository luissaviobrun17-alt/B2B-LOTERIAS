# LOTOFACIL MODO 4 : ETAPA 3 (Especificacao dos Algoritmos de Otimizacao)

## 1. Arquitetura, Especificacao e Complexidade dos Algoritmos
| Algoritmo | Categoria | Complexidade Tempo | Complexidade Espaco | Garante Otimo Global? |
| :--- | :--- | :--- | :--- | :---: |
| `referencia_aleatoria` | `BASELINE_ALEATORIO` | `O(B * J * m)` | `O(J * m)` | Nao (heuristica / baseline) |
| `busca_exata_pequena` | `EXATO_GLOBAL_PEQUENA_ESCALA` | `O(C(K, J) * Delta_eval)` | `O(K * m + C(p, 4))` | Sim (quando C(K,J) <= limite) |
| `algoritmo_guloso` | `CONSTRUTIVO_GULOSO` | `O(J * M_cand * Delta_eval)` | `O(J * m + T_cov)` | Nao (heuristica / baseline) |
| `busca_local_trocas` | `BUSCA_LOCAL_TROCAS` | `O(B * (C(m-1, 3) + J))` | `O(J^2 + T_cov)` | Nao (heuristica / baseline) |
| `multiplos_reinicios` | `MULTI_START_BUSCA_LOCAL` | `O(R * (B / R) * (C(m-1, 3) + J))` | `O(J^2 + T_cov)` | Nao (heuristica / baseline) |
| `estrategia_combinada` | `HIBRIDO_CONSTRUTIVO_ILS` | `O(B * (C(m-1, 3) + J))` | `O(J^2 + T_cov + |visitados|)` | Nao (heuristica / baseline) |

## 2. Comparacao Empirica Controlada Sob Condicoes Identicas
Todas as comparacoes abaixo utilizam identico pool, mesmas restricoes (`todos_os_jogos` ou `composicao_pool`), mesma quantidade de jogos e dimensoes, mesmo orcamento, mesma funcao objetivo $F_{\text{MODO4}}$, mesma semente SHA-256 e mesmo teto de avaliacoes (`max_avaliacoes`).

### 2.1 Instancia `inst_peq_p16_J4_exata` (`escopo: PROVA_OTIMO_GLOBAL_INSTANCIA_PEQUENA`)
- **Configuracao:** pool=`16`, fixas=`0`, bloqueadas=`5`, modo=`todos_os_jogos`, jogos=`4` (`[15]`), custo=`R$ 14.00`, semente=`42`, teto_eval=`250`.

| Pos | Algoritmo | Score F(C) | Ganho vs Aleatorio | Gap p/ Exato | Pares | Trincas | I_max | Var(N_prem) | Avaliacoes | Tempo (s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `busca_exata_pequena` | 0.995600 | +0.000208 | 0.000000 | 120 | 560 | 14 | 1.0518 | 1820 | 1.3630 |
| 2 | `algoritmo_guloso` | 0.995600 | +0.000208 | 0.000000 | 120 | 560 | 14 | 1.0518 | 58 | 0.0261 |
| 3 | `estrategia_combinada` | 0.995600 | +0.000208 | 0.000000 | 120 | 560 | 14 | 1.0518 | 250 | 0.0721 |
| 4 | `multiplos_reinicios` | 0.995600 | +0.000208 | 0.000000 | 120 | 560 | 14 | 1.0518 | 250 | 0.0653 |
| 5 | `referencia_aleatoria` | 0.995392 | +0.000000 | 0.000208 | 120 | 560 | 14 | 1.0518 | 150 | 0.1044 |
| 6 | `busca_local_trocas` | 0.995392 | +0.000000 | 0.000208 | 120 | 560 | 14 | 1.0518 | 81 | 0.0190 |

### 2.1 Instancia `inst_peq_p18_f11_J3_exata` (`escopo: PROVA_OTIMO_GLOBAL_INSTANCIA_PEQUENA`)
- **Configuracao:** pool=`18`, fixas=`11`, bloqueadas=`7`, modo=`todos_os_jogos`, jogos=`3` (`[15]`), custo=`R$ 10.50`, semente=`42`, teto_eval=`250`.

| Pos | Algoritmo | Score F(C) | Ganho vs Aleatorio | Gap p/ Exato | Pares | Trincas | I_max | Var(N_prem) | Avaliacoes | Tempo (s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `busca_exata_pequena` | 0.971903 | +0.000278 | 0.000000 | 148 | 738 | 13 | 0.4837 | 6545 | 4.4131 |
| 2 | `busca_local_trocas` | 0.971903 | +0.000278 | 0.000000 | 148 | 738 | 13 | 0.4837 | 88 | 0.0189 |
| 3 | `multiplos_reinicios` | 0.971903 | +0.000278 | 0.000000 | 148 | 738 | 13 | 0.4837 | 250 | 0.0456 |
| 4 | `algoritmo_guloso` | 0.971903 | +0.000278 | 0.000000 | 148 | 738 | 13 | 0.4837 | 83 | 0.0372 |
| 5 | `estrategia_combinada` | 0.971903 | +0.000278 | 0.000000 | 148 | 738 | 13 | 0.4837 | 250 | 0.0878 |
| 6 | `referencia_aleatoria` | 0.971626 | +0.000000 | 0.000278 | 148 | 738 | 13 | 0.4837 | 150 | 0.0829 |

### 2.1 Instancia `inst_med_p20_J10_fix3_todos_jogos_s42` (`escopo: COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`)
- **Configuracao:** pool=`20`, fixas=`3`, bloqueadas=`5`, modo=`todos_os_jogos`, jogos=`10` (`[15]`), custo=`R$ 35.00`, semente=`42`, teto_eval=`300`.

| Pos | Algoritmo | Score F(C) | Ganho vs Aleatorio | Gap p/ Exato | Pares | Trincas | I_max | Var(N_prem) | Avaliacoes | Tempo (s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `busca_local_trocas` | 0.995879 | +0.016461 | N/A | 190 | 1140 | 12 | 2.2907 | 300 | 0.0662 |
| 2 | `estrategia_combinada` | 0.995550 | +0.016133 | N/A | 190 | 1140 | 12 | 2.2948 | 300 | 0.1953 |
| 3 | `multiplos_reinicios` | 0.994968 | +0.015550 | N/A | 190 | 1140 | 12 | 2.3031 | 300 | 0.1321 |
| 4 | `algoritmo_guloso` | 0.992135 | +0.012717 | N/A | 190 | 1140 | 13 | 2.3415 | 300 | 0.3863 |
| 5 | `referencia_aleatoria` | 0.979417 | +0.000000 | N/A | 190 | 1139 | 13 | 2.4613 | 150 | 0.3214 |

### 2.1 Instancia `inst_med_p20_J10_fix3_todos_jogos_s101` (`escopo: COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`)
- **Configuracao:** pool=`20`, fixas=`3`, bloqueadas=`5`, modo=`todos_os_jogos`, jogos=`10` (`[15]`), custo=`R$ 35.00`, semente=`101`, teto_eval=`300`.

| Pos | Algoritmo | Score F(C) | Ganho vs Aleatorio | Gap p/ Exato | Pares | Trincas | I_max | Var(N_prem) | Avaliacoes | Tempo (s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `busca_local_trocas` | 0.995879 | +0.016452 | N/A | 190 | 1140 | 12 | 2.2907 | 300 | 0.0656 |
| 2 | `estrategia_combinada` | 0.995588 | +0.016161 | N/A | 190 | 1140 | 12 | 2.2948 | 300 | 0.2022 |
| 3 | `multiplos_reinicios` | 0.995476 | +0.016050 | N/A | 190 | 1140 | 12 | 2.2948 | 300 | 0.1281 |
| 4 | `algoritmo_guloso` | 0.988428 | +0.009001 | N/A | 190 | 1140 | 14 | 2.3813 | 300 | 0.3614 |
| 5 | `referencia_aleatoria` | 0.979426 | +0.000000 | N/A | 190 | 1138 | 13 | 2.4597 | 150 | 0.2979 |

### 2.1 Instancia `inst_med_p22_J12_f16_composicao_pool` (`escopo: COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`)
- **Configuracao:** pool=`22`, fixas=`16`, bloqueadas=`3`, modo=`composicao_pool`, jogos=`12` (`[15]`), custo=`R$ 42.00`, semente=`42`, teto_eval=`300`.

| Pos | Algoritmo | Score F(C) | Ganho vs Aleatorio | Gap p/ Exato | Pares | Trincas | I_max | Var(N_prem) | Avaliacoes | Tempo (s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `busca_local_trocas` | 0.996619 | +0.012365 | N/A | 231 | 1540 | 11 | 1.7124 | 300 | 0.0773 |
| 2 | `estrategia_combinada` | 0.995981 | +0.011727 | N/A | 231 | 1540 | 11 | 1.7226 | 300 | 0.2861 |
| 3 | `multiplos_reinicios` | 0.994990 | +0.010736 | N/A | 231 | 1540 | 11 | 1.7466 | 300 | 0.1688 |
| 4 | `algoritmo_guloso` | 0.991719 | +0.007465 | N/A | 231 | 1540 | 12 | 1.8122 | 300 | 0.5325 |
| 5 | `referencia_aleatoria` | 0.984254 | +0.000000 | N/A | 231 | 1536 | 12 | 1.9075 | 150 | 0.4724 |

### 2.1 Instancia `inst_grd_p25_orc56_J16_simples` (`escopo: COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`)
- **Configuracao:** pool=`25`, fixas=`0`, bloqueadas=`0`, modo=`todos_os_jogos`, jogos=`16` (`[15]`), custo=`R$ 56.00`, semente=`42`, teto_eval=`320`.

| Pos | Algoritmo | Score F(C) | Ganho vs Aleatorio | Gap p/ Exato | Pares | Trincas | I_max | Var(N_prem) | Avaliacoes | Tempo (s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `multiplos_reinicios` | 0.992336 | +0.012931 | N/A | 300 | 2292 | 11 | 0.9152 | 320 | 0.2524 |
| 2 | `estrategia_combinada` | 0.990191 | +0.010786 | N/A | 300 | 2290 | 11 | 1.0247 | 320 | 0.4351 |
| 3 | `algoritmo_guloso` | 0.988143 | +0.008738 | N/A | 300 | 2285 | 12 | 1.0914 | 320 | 0.7604 |
| 4 | `busca_local_trocas` | 0.984014 | +0.004609 | N/A | 300 | 2286 | 12 | 1.3115 | 320 | 0.1104 |
| 5 | `referencia_aleatoria` | 0.979405 | +0.000000 | N/A | 300 | 2253 | 12 | 1.1961 | 160 | 0.6852 |

### 2.1 Instancia `inst_mult_p20_J4_m17` (`escopo: COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`)
- **Configuracao:** pool=`20`, fixas=`0`, bloqueadas=`5`, modo=`todos_os_jogos`, jogos=`4` (`[17]`), custo=`R$ 1904.00`, semente=`42`, teto_eval=`200`.

| Pos | Algoritmo | Score F(C) | Ganho vs Aleatorio | Gap p/ Exato | Pares | Trincas | I_max | Var(N_prem) | Avaliacoes | Tempo (s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `busca_local_trocas` | 0.996527 | +0.000000 | N/A | 190 | 1140 | 14 | 1.8329 | 123 | 0.0719 |
| 2 | `estrategia_combinada` | 0.996527 | +0.000000 | N/A | 190 | 1140 | 14 | 1.8329 | 200 | 0.1598 |
| 3 | `algoritmo_guloso` | 0.996527 | +0.000000 | N/A | 190 | 1140 | 14 | 1.8329 | 200 | 0.2477 |
| 4 | `multiplos_reinicios` | 0.996527 | +0.000000 | N/A | 190 | 1140 | 14 | 1.8329 | 200 | 0.1366 |
| 5 | `referencia_aleatoria` | 0.996527 | +0.000000 | N/A | 190 | 1140 | 14 | 1.8329 | 100 | 0.1542 |

### 2.1 Instancia `inst_mult_mista_p20_m16_mais_3x15` (`escopo: COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`)
- **Configuracao:** pool=`20`, fixas=`2`, bloqueadas=`5`, modo=`todos_os_jogos`, jogos=`4` (`[15, 16]`), custo=`R$ 66.50`, semente=`42`, teto_eval=`200`.

| Pos | Algoritmo | Score F(C) | Ganho vs Aleatorio | Gap p/ Exato | Pares | Trincas | I_max | Var(N_prem) | Avaliacoes | Tempo (s) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| 1 | `busca_local_trocas` | 0.989620 | +0.048778 | N/A | 190 | 1120 | 11 | 0.5919 | 190 | 0.0338 |
| 2 | `multiplos_reinicios` | 0.989620 | +0.048778 | N/A | 190 | 1120 | 11 | 0.5919 | 200 | 0.0585 |
| 3 | `estrategia_combinada` | 0.989456 | +0.048614 | N/A | 190 | 1120 | 11 | 0.5919 | 200 | 0.0823 |
| 4 | `algoritmo_guloso` | 0.989456 | +0.048614 | N/A | 190 | 1120 | 11 | 0.5919 | 200 | 0.1506 |
| 5 | `referencia_aleatoria` | 0.940841 | +0.000000 | N/A | 189 | 1070 | 12 | 0.6613 | 100 | 0.0999 |

## 3. Conferencia Contra Referencia Independente e Reprodutibilidade
- **Execucoes conferidas vs referencia independente:** `42/42` conformes e equivalentes.
- **Maior divergencia numerica observada em F(C):** `0.00e+00` (limite `1.00e-12`).
- **Reprodutibilidade sob mesma semente (`777`):** `SHA-256` identico (`True`), carteira identica (`True`), `historico_utilizado=None`.

## 4. Limitacao de Escopo das Comparacoes (Ressalva 2.3)
- As instancias `inst_peq_p16_J4_exata` e `inst_peq_p18_f11_J3_exata` pertencem a categoria `PROVA_OTIMO_GLOBAL_INSTANCIA_PEQUENA`, onde a busca exata enumerou todas as carteiras viaveis do espaco.
- As demais instancias pertencem a categoria `COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`, medindo desempenho empirico dentro dos parametros e orcamentos avaliados sem declarar superioridade universal absoluta.

## 5. Clausula Obrigatoria de Veracidade Cientifica
> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.
