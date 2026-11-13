# LOTOFACIL MODO 4 : ETAPA 4 (Arquitetura Adaptativa, Integracao e Otimizacao)

## 1. Independencia da Validacao (AST) e Preservacao das Etapas 1 a 3
- **Referencia Etapa 4 (`4.0.0-referencia-zero-dependencia`):** `independencia_comprovada=True`, dependencias internas detectadas=`0` (somente biblioteca padrao: `__future__, ast, decimal, fractions, hashlib, itertools, math, os, typing`).
- **Diagnostico da Etapa 3 anterior (`etapa3_referencia_independente.py`):** detectadas `2` importacoes internas (`.etapa1_regras_oficiais, .etapa2_referencia_independente`); lacuna eliminada integralmente na Etapa 4.
- **Preservacao de artefatos congelados (Etapas 1, 2 e 3):** `20/20` arquivos preservados sem alteracao (`preservado_integralmente=True`).

## 2. Benchmark de Desempenho e Memoria: Etapa 3 vs Etapa 4
| Caso | Algoritmo | Tempo E3 (s) | Tempo E4 (s) | Aceleracao | Pico Mem E3 (KB) | Pico Mem E4 (KB) | Reducao Mem (%) | Delta F(C) |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :---: |
| `bench_guloso_p25_J16_b320` | `algoritmo_guloso` | 0.76930 | 0.07566 | 10.17x | 1809.17 | 1262.20 | 30.23% | -0.00103917 |
| `bench_local_p20_J10_b300` | `busca_local_trocas` | 0.07343 | 0.04304 | 1.71x | 725.74 | 344.40 | 52.54% | -0.00624481 |
| `bench_multistart_p25_J16_b320` | `multiplos_reinicios` | 0.23674 | 0.16076 | 1.47x | 1650.72 | 1636.44 | 0.86% | -0.00084571 |
| `bench_exata_p16_J4` | `busca_exata_pequena` | 1.49435 | 1.18460 | 1.26x | 523.78 | 345.23 | 34.09% | +0.00000000 |

## 3. Despacho Adaptativo Deterministico e Escalabilidade Sob Orcamento Equivalente
| Instancia | Despachado | Regime | Pos | F(C) Adaptativo | F(C) Lider | Gap p/ Lider | Evals Efetivas / Teto (% Uso) | Reinicios | Parada | Tempo (s) | Mem Pico (MB) |
| :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| `e4_unit_p15_J1` | `busca_exata_pequena` | `ESPACO_UNITARIO` | 2 | 0.995000 | 0.995000 | 0.000000 | 1/100 (1.0%) | 1 | `espaco_unitario` | 0.0038 | 0.0359 |
| `e4_peq_p16_J4_b2000_exata` | `busca_exata_pequena` | `EXATO_GLOBAL_TRATAVEL` | 2 | 0.995600 | 0.995600 | 0.000000 | 1820/2000 (91.0%) | 1 | `enumeracao_completa` | 12.9167 | 0.1897 |
| `e4_peq_mista_p17_m16_e_2x15_exata` | `busca_exata_pequena` | `EXATO_GLOBAL_TRATAVEL` | 2 | 0.935190 | 0.935190 | 0.000000 | 9/200 (4.5%) | 1 | `enumeracao_completa` | 0.0874 | 0.2679 |
| `e4_micro_orc_p25_J12_b30` | `algoritmo_guloso` | `MICRO_ORCAMENTO_OU_BAIXA_LATENCIA` | 4 | 0.964158 | 0.977880 | 0.013723 | 30/30 (100.0%) | 1 | `construcao_completa` | 0.1939 | 0.1059 |
| `e4_med_p20_J10_f3_todos_s42` | `multiplos_reinicios` | `ESPACO_AMPLO_MULTIPLOS_REINICIOS_HIPOTESE` | 3 | 0.991932 | 0.993573 | 0.001641 | 300/300 (100.0%) | 6 | `teto_avaliacoes` | 1.0848 | 0.7526 |
| `e4_med_p22_J12_f16_pool_s42` | `multiplos_reinicios` | `ESPACO_AMPLO_MULTIPLOS_REINICIOS_HIPOTESE` | 1 | 0.993917 | 0.993917 | 0.000000 | 300/300 (100.0%) | 6 | `teto_avaliacoes` | 1.4434 | 1.1634 |
| `e4_amp_p25_J16_orc56_s42` | `multiplos_reinicios` | `ESPACO_AMPLO_MULTIPLOS_REINICIOS_HIPOTESE` | 1 | 0.991490 | 0.991490 | 0.000000 | 320/320 (100.0%) | 6 | `teto_avaliacoes` | 1.9577 | 1.5643 |
| `e4_amp_p25_J16_orc56_s101` | `multiplos_reinicios` | `ESPACO_AMPLO_MULTIPLOS_REINICIOS_HIPOTESE` | 1 | 0.992008 | 0.992008 | 0.000000 | 320/320 (100.0%) | 6 | `teto_avaliacoes` | 1.9029 | 1.5017 |
| `e4_esc_p25_J30_orc105_b450` | `multiplos_reinicios` | `ESPACO_AMPLO_MULTIPLOS_REINICIOS_HIPOTESE` | 1 | 0.995031 | 0.995031 | 0.000000 | 450/450 (100.0%) | 6 | `teto_avaliacoes` | 2.6399 | 1.7205 |
| `e4_mult_mista_p21_2x16_8x15_b350` | `multiplos_reinicios` | `ESPACO_AMPLO_MULTIPLOS_REINICIOS_HIPOTESE` | 2 | 0.981386 | 0.983209 | 0.001823 | 350/350 (100.0%) | 6 | `teto_avaliacoes` | 1.4405 | 1.2066 |

## 4. Comparacao Justa Detalhada nas Instancias Chave (Telemetria Completa)

### 4.1 `e4_peq_p16_J4_b2000_exata` (`PROVA_OTIMO_GLOBAL_INSTANCIA_PEQUENA`)
- **Parametros:** pool=`16`, fixas=`0` (`todos_os_jogos`), bloqueadas=`5`, jogos=`4` (`[15]`), espaco=`1820`, semente=`42`, teto=`2000`.
- **Motivo despacho:** Espaco admissivel=1820 cabe integralmente no teto combinatorio (10000), no orcamento de avaliacoes (B=2000), no tempo estimado (0.3800s) e na memoria estimada (1.61 MB), permitindo prova deterministica de otimo global.

| Pos | Algoritmo | Score F(C) | Dist. Otimo Exato | Efetivas / Teto | % Uso | Reinicios | Crit. Parada | Tempo (s) | Mem (MB) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| 1 | `busca_exata_pequena` | 0.995600 | 0.000000 | 1820/2000 | 91.0% | 1 | `enumeracao_completa` | 12.8825 | 0.1892 |
| 2 | `despacho_adaptativo` | 0.995600 | 0.000000 | 1820/2000 | 91.0% | 1 | `enumeracao_completa` | 12.9167 | 0.1897 |
| 3 | `algoritmo_guloso` | 0.995600 | 0.000000 | 58/2000 | 2.9% | 1 | `construcao_completa` | 2.3218 | 0.0841 |
| 4 | `estrategia_combinada` | 0.995600 | 0.000000 | 323/2000 | 16.2% | 6 | `otimo_local_sem_melhora` | 1.2287 | 0.3624 |
| 5 | `referencia_aleatoria` | 0.995600 | 0.000000 | 2000/2000 | 100.0% | 1 | `teto_avaliacoes` | 20.8566 | 0.4101 |
| 6 | `multiplos_reinicios` | 0.995600 | 0.000000 | 299/2000 | 14.9% | 6 | `otimo_local_sem_melhora` | 0.7042 | 0.2602 |
| 7 | `busca_local_trocas` | 0.995392 | 0.000208 | 38/2000 | 1.9% | 1 | `otimo_local_sem_melhora` | 0.1036 | 0.0457 |

### 4.1 `e4_peq_mista_p17_m16_e_2x15_exata` (`PROVA_OTIMO_GLOBAL_INSTANCIA_PEQUENA`)
- **Parametros:** pool=`17`, fixas=`14` (`todos_os_jogos`), bloqueadas=`8`, jogos=`3` (`[15, 16]`), espaco=`9`, semente=`42`, teto=`200`.
- **Motivo despacho:** Espaco admissivel=9 cabe integralmente no teto combinatorio (10000), no orcamento de avaliacoes (B=200), no tempo estimado (0.0020s) e na memoria estimada (1.61 MB), permitindo prova deterministica de otimo global.

| Pos | Algoritmo | Score F(C) | Dist. Otimo Exato | Efetivas / Teto | % Uso | Reinicios | Crit. Parada | Tempo (s) | Mem (MB) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| 1 | `busca_exata_pequena` | 0.935190 | 0.000000 | 9/200 | 4.5% | 1 | `enumeracao_completa` | 0.0862 | 0.2694 |
| 2 | `despacho_adaptativo` | 0.935190 | 0.000000 | 9/200 | 4.5% | 1 | `enumeracao_completa` | 0.0874 | 0.2679 |
| 3 | `referencia_aleatoria` | 0.935190 | 0.000000 | 200/200 | 100.0% | 1 | `teto_avaliacoes` | 1.7338 | 0.0882 |
| 4 | `multiplos_reinicios` | 0.935190 | 0.000000 | 70/200 | 35.0% | 5 | `otimo_local_sem_melhora` | 0.3153 | 0.2809 |
| 5 | `busca_local_trocas` | 0.935190 | 0.000000 | 12/200 | 6.0% | 1 | `otimo_local_sem_melhora` | 0.0508 | 0.0448 |
| 6 | `estrategia_combinada` | 0.935190 | 0.000000 | 48/200 | 24.0% | 4 | `otimo_local_sem_melhora` | 0.2221 | 0.3829 |
| 7 | `algoritmo_guloso` | 0.935190 | 0.000000 | 8/200 | 4.0% | 1 | `construcao_completa` | 0.0698 | 0.0799 |

### 4.1 `e4_med_p20_J10_f3_todos_s42` (`COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`)
- **Parametros:** pool=`20`, fixas=`3` (`todos_os_jogos`), bloqueadas=`5`, jogos=`10` (`[15]`), espaco=`22520610003381472748033656414026`, semente=`42`, teto=`300`.
- **Motivo despacho:** Espaco combinatorio amplo (p=20, f_jogo=3, J=10, vizinhanca_1swap=600) com B=300 comporta 6 reinicios bem financiados (>= 40 evals/reinicio), adotando multi-start como hipotese de engenharia para mitigar minimos locais sob validacao empirica continua.

| Pos | Algoritmo | Score F(C) | Dist. Otimo Exato | Efetivas / Teto | % Uso | Reinicios | Crit. Parada | Tempo (s) | Mem (MB) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| 1 | `estrategia_combinada` | 0.993573 | N/A (Heur.) | 300/300 | 100.0% | 3 | `teto_avaliacoes` | 0.9093 | 0.7646 |
| 2 | `algoritmo_guloso` | 0.992177 | N/A (Heur.) | 300/300 | 100.0% | 1 | `construcao_completa` | 0.9639 | 0.1102 |
| 3 | `despacho_adaptativo` | 0.991932 | N/A (Heur.) | 300/300 | 100.0% | 6 | `teto_avaliacoes` | 1.0848 | 0.7526 |
| 4 | `multiplos_reinicios` | 0.991932 | N/A (Heur.) | 300/300 | 100.0% | 6 | `teto_avaliacoes` | 1.0790 | 0.6864 |
| 5 | `busca_local_trocas` | 0.989634 | N/A (Heur.) | 300/300 | 100.0% | 1 | `teto_avaliacoes` | 0.5817 | 0.0574 |
| 6 | `referencia_aleatoria` | 0.981147 | N/A (Heur.) | 200/300 | 66.7% | 1 | `teto_avaliacoes` | 5.9032 | 0.4334 |

### 4.1 `e4_amp_p25_J16_orc56_s42` (`COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`)
- **Parametros:** pool=`25`, fixas=`0` (`todos_os_jogos`), bloqueadas=`0`, jogos=`16` (`[15]`), espaco=`8118822004031084633299686223863297610546391751744174092808945387797872569646347530355384375`, semente=`42`, teto=`320`.
- **Motivo despacho:** Espaco combinatorio amplo (p=25, f_jogo=0, J=16, vizinhanca_1swap=2400) com B=320 comporta 6 reinicios bem financiados (>= 40 evals/reinicio), adotando multi-start como hipotese de engenharia para mitigar minimos locais sob validacao empirica continua.

| Pos | Algoritmo | Score F(C) | Dist. Otimo Exato | Efetivas / Teto | % Uso | Reinicios | Crit. Parada | Tempo (s) | Mem (MB) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| 1 | `despacho_adaptativo` | 0.991490 | N/A (Heur.) | 320/320 | 100.0% | 6 | `teto_avaliacoes` | 1.9577 | 1.5643 |
| 2 | `multiplos_reinicios` | 0.991490 | N/A (Heur.) | 320/320 | 100.0% | 6 | `teto_avaliacoes` | 1.9181 | 1.5435 |
| 3 | `estrategia_combinada` | 0.989400 | N/A (Heur.) | 320/320 | 100.0% | 3 | `teto_avaliacoes` | 1.5251 | 1.6228 |
| 4 | `algoritmo_guloso` | 0.987104 | N/A (Heur.) | 320/320 | 100.0% | 1 | `construcao_completa` | 1.2929 | 0.1269 |
| 5 | `busca_local_trocas` | 0.986706 | N/A (Heur.) | 320/320 | 100.0% | 1 | `teto_avaliacoes` | 0.7637 | 0.0700 |
| 6 | `referencia_aleatoria` | 0.979086 | N/A (Heur.) | 200/320 | 62.5% | 1 | `teto_avaliacoes` | 10.9884 | 0.3565 |

### 4.1 `e4_amp_p25_J16_orc56_s101` (`COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`)
- **Parametros:** pool=`25`, fixas=`0` (`todos_os_jogos`), bloqueadas=`0`, jogos=`16` (`[15]`), espaco=`8118822004031084633299686223863297610546391751744174092808945387797872569646347530355384375`, semente=`101`, teto=`320`.
- **Motivo despacho:** Espaco combinatorio amplo (p=25, f_jogo=0, J=16, vizinhanca_1swap=2400) com B=320 comporta 6 reinicios bem financiados (>= 40 evals/reinicio), adotando multi-start como hipotese de engenharia para mitigar minimos locais sob validacao empirica continua.

| Pos | Algoritmo | Score F(C) | Dist. Otimo Exato | Efetivas / Teto | % Uso | Reinicios | Crit. Parada | Tempo (s) | Mem (MB) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| 1 | `despacho_adaptativo` | 0.992008 | N/A (Heur.) | 320/320 | 100.0% | 6 | `teto_avaliacoes` | 1.9029 | 1.5017 |
| 2 | `multiplos_reinicios` | 0.992008 | N/A (Heur.) | 320/320 | 100.0% | 6 | `teto_avaliacoes` | 1.8873 | 1.5455 |
| 3 | `algoritmo_guloso` | 0.989902 | N/A (Heur.) | 320/320 | 100.0% | 1 | `construcao_completa` | 1.2811 | 0.1272 |
| 4 | `estrategia_combinada` | 0.989780 | N/A (Heur.) | 320/320 | 100.0% | 3 | `teto_avaliacoes` | 1.4823 | 1.6262 |
| 5 | `busca_local_trocas` | 0.988379 | N/A (Heur.) | 320/320 | 100.0% | 1 | `teto_avaliacoes` | 0.8271 | 0.0716 |
| 6 | `referencia_aleatoria` | 0.980258 | N/A (Heur.) | 200/320 | 62.5% | 1 | `teto_avaliacoes` | 11.0486 | 0.4562 |

### 4.1 `e4_esc_p25_J30_orc105_b450` (`COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`)
- **Parametros:** pool=`25`, fixas=`0` (`todos_os_jogos`), bloqueadas=`0`, jogos=`30` (`[15]`), espaco=`10180595329029060634336253896999417592346150607277895677363627064616408299789763280418626843578354282588419540840342396728175465439213921535171708331497589410424000`, semente=`42`, teto=`450`.
- **Motivo despacho:** Espaco combinatorio amplo (p=25, f_jogo=0, J=30, vizinhanca_1swap=4500) com B=450 comporta 6 reinicios bem financiados (>= 60 evals/reinicio), adotando multi-start como hipotese de engenharia para mitigar minimos locais sob validacao empirica continua.

| Pos | Algoritmo | Score F(C) | Dist. Otimo Exato | Efetivas / Teto | % Uso | Reinicios | Crit. Parada | Tempo (s) | Mem (MB) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| 1 | `despacho_adaptativo` | 0.995031 | N/A (Heur.) | 450/450 | 100.0% | 6 | `teto_avaliacoes` | 2.6399 | 1.7205 |
| 2 | `multiplos_reinicios` | 0.995031 | N/A (Heur.) | 450/450 | 100.0% | 6 | `teto_avaliacoes` | 2.6672 | 1.7935 |
| 3 | `estrategia_combinada` | 0.993676 | N/A (Heur.) | 450/450 | 100.0% | 3 | `teto_avaliacoes` | 2.4279 | 1.9040 |
| 4 | `algoritmo_guloso` | 0.993615 | N/A (Heur.) | 450/450 | 100.0% | 1 | `construcao_completa` | 2.1336 | 0.1972 |
| 5 | `busca_local_trocas` | 0.989983 | N/A (Heur.) | 450/450 | 100.0% | 1 | `teto_avaliacoes` | 1.0277 | 0.1111 |
| 6 | `referencia_aleatoria` | 0.987475 | N/A (Heur.) | 200/450 | 44.4% | 1 | `teto_avaliacoes` | 22.0004 | 0.2751 |

### 4.1 `e4_mult_mista_p21_2x16_8x15_b350` (`COMPARACAO_AMOSTRAL_CONTROLADA_ALGORITMOS`)
- **Parametros:** pool=`21`, fixas=`2` (`todos_os_jogos`), bloqueadas=`4`, jogos=`10` (`[15, 16]`), espaco=`491845173489041469123983679888455540250`, semente=`42`, teto=`350`.
- **Motivo despacho:** Espaco combinatorio amplo (p=21, f_jogo=2, J=10, vizinhanca_1swap=764) com B=350 comporta 6 reinicios bem financiados (>= 40 evals/reinicio), adotando multi-start como hipotese de engenharia para mitigar minimos locais sob validacao empirica continua.

| Pos | Algoritmo | Score F(C) | Dist. Otimo Exato | Efetivas / Teto | % Uso | Reinicios | Crit. Parada | Tempo (s) | Mem (MB) |
| :---: | :--- | :---: | :---: | :---: | :---: | :---: | :--- | :---: | :---: |
| 1 | `busca_local_trocas` | 0.983209 | N/A (Heur.) | 350/350 | 100.0% | 1 | `teto_avaliacoes` | 0.7987 | 0.0606 |
| 2 | `despacho_adaptativo` | 0.981386 | N/A (Heur.) | 350/350 | 100.0% | 6 | `teto_avaliacoes` | 1.4405 | 1.2066 |
| 3 | `multiplos_reinicios` | 0.981386 | N/A (Heur.) | 350/350 | 100.0% | 6 | `teto_avaliacoes` | 1.4569 | 1.2019 |
| 4 | `estrategia_combinada` | 0.978899 | N/A (Heur.) | 350/350 | 100.0% | 3 | `teto_avaliacoes` | 1.2310 | 1.3141 |
| 5 | `algoritmo_guloso` | 0.978414 | N/A (Heur.) | 350/350 | 100.0% | 1 | `construcao_completa` | 1.1908 | 0.1246 |
| 6 | `referencia_aleatoria` | 0.968703 | N/A (Heur.) | 200/350 | 57.1% | 1 | `teto_avaliacoes` | 6.2789 | 0.3767 |

## 5. Verificacao Cruzada Independente, Reprodutibilidade e Principio Cientifico
- **Execucoes auditadas pela referencia zero-dependencia:** `63/63` equivalentes em <= 1e-12 e conformes (`maior_diferenca_F_observada=2.22e-16`).
- **Prova exata mista independente (`e4_peq_mista_p17_m16_e_2x15_exata`):** coincide integralmente (`True`) em `9` carteiras enumeradas.
- **Reprodutibilidade e integracao CAIXA (semente `909`, `lotofacil_independencia`):** SHA-256 identico=`True` (`81b1351b25bb3e663bac11c990473f76c9131681946dfb2c13d9470d67ed6e8e`), `historico_utilizado=None`.

> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.