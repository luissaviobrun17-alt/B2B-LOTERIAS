# ETAPA 5: INTEGRACAO EM HOMOLOGACAO ISOLADA E VALIDACAO PONTA A PONTA

**Gerado em (UTC):** 2026-11-13T15:42:47.509617+00:00  
**Versao do motor Etapa 4:** `4.0.0-etapa4-arquitetura-adaptativa`  
**Versao do modulo Etapa 5:** `5.0.0-etapa5-homologacao`  
**Flag `HISTORICO_GERACAO_ETAPA4`:** `None`  
**Feature flag padrao em homologacao (`lotofacil_modo4_ativo`):** `False`

> **Clausula cientifica obrigatoria:**  
> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.

---

## 1. Resumo Executivo da Homologacao Isolada

- **Arquivos de producao preservados intactos:** `True` (`api.py`, `motor_lotofacil.py`, `index.html`, `js/ui.js`, `B2B_Loterias_Mobile.html` com hashes SHA-256 identicos antes e depois da Etapa 5).
- **Artefatos congelados das Etapas 1, 2, 3 e 4:** `20/20` (Etapas 1 a 3) e `4/4` (Etapa 4) integros.
- **Selo criptografico Lotomania MODO 4 v1.2:** `True` e base oficial CAIXA integra (`7/7`).
- **Comparativo 3 vias ao vivo (`api.py` pura vs Flag OFF vs Flag ON):** `concluido_sem_regressao=True`.
- **Equivalencia matematica E2E vs referencia AST-isolada:** divergencia maxima `1.110e-16` (`<= 1e-12`).
- **Seguranca fail-closed (selo adulterado, API offline, timeout, HTTP 500/503, JSON corrompido, `historico`):** 0 jogos retornados e `fallback_executado=False` em 100% dos cenarios.

---

## 2. Comparativo 3 Vias ao Vivo (HTTP Real em Loopback)

| Verificacao | Via A (`api.py` atual) | Via B (Integrada Flag OFF) | Via C (Integrada Flag ON) | Resultado |
| :--- | :--- | :--- | :--- | :--- |
| `GET /health` preservacao integral de chaves | Baseline | Identico (`True`) | Identico (`True`) | Aprovado |
| `/health -> lotofacil_modo4.disponivel` | Ausente | `False` | `True` | Isolado por flag |
| `POST /api/v1/lotomania-modo4/gerar` (`seed=42`) | Baseline (6 jogos) | Identico (`True`) | Identico (`True`) | Zero interferencia |
| `POST /api/v1/lotofacil-modo4/gerar` | HTTP `404` | HTTP `503` (0 jogos) | HTTP `200` (6 jogos) | Rollback em runtime OK |

| Motor legado avaliado | Status A | Status B | Status C | Paridade de contrato |
| :--- | :--- | :--- | :--- | :--- |
| `/api/v1/motor-lotofacil` | 200 | 200 | 200 | `True` |
| `/api/v1/motor-lotomania` | 200 | 200 | 200 | `True` |
| `/api/v1/motor-timemania` | 200 | 200 | 200 | `True` |

---

## 3. Diagnostico Etapa 3 vs Etapa 4 e Independencias da Referencia (Condicionantes I, II e IV)

- **Auditoria AST da referencia independente (`etapa4_referencia_independente.py`):** `independencia_comprovada=True` (`0` importacoes internas). Em atendimento a Condicionante I, registra-se que a auditoria AST comprova **independencia de implementacao** (zero compartilhamento de codigo ou caches com o motor principal), enquanto a **independencia metodologica** decorre da implementacao autonoma a partir das formulas matematicas oficiais da CAIXA (hipergeometrica bivariada 4-regioes, MST de Kruskal para Hunter-Worsley, Dawson-Sankoff e os 4 componentes combinatorio-estruturais), validada previamente contra enumeracao integral dos 3.268.760 sorteios na Etapa 2.
- **Invariancia do avaliador Etapa 3 vs Etapa 4:** divergencia maxima entre `avaliar_carteira_etapa2`, `MotorIncrementalOtimizadoEtapa4` e `avaliar_carteira_ref_etapa4` sobre todas as carteiras (inclusive as geradas pela Etapa 3) = `1.110e-16` (`<= 1e-12`).

| Cenario | Algoritmo | F(Etapa 3) | F(Etapa 4) | Delta F (E4 - E3) | Jaccard | Vit/Emp/Der (5 sementes) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `bench_guloso_p25_J16_b320` | `algoritmo_guloso` | 0.98814321 | 0.98710404 | -0.00103917 | 0.0000 | 3/0/2 |
| `bench_local_p20_J10_b300` | `busca_local_trocas` | 0.99587872 | 0.98963391 | -0.00624481 | 0.0000 | 0/0/5 |
| `bench_multistart_p25_J16_b320` | `multiplos_reinicios` | 0.99233583 | 0.99149012 | -0.00084571 | 0.0000 | 0/0/5 |
| `bench_exata_p16_J4` | `busca_exata_pequena` | 0.99560027 | 0.99560027 | +0.00000000 | 1.0000 | 0/5/0 |

Conclusao da Condicionante II: Os avaliadores da Etapa 2, Etapa 4 incremental e referencia independente convergem com divergencia maxima 1.110e-16 (<= 1e-12), inclusive sobre as proprias carteiras produzidas pela Etapa 3. As diferencas em heuristicas decorrem do desenho distinto de busca: no guloso ha alternancia por semente (PRNG), na busca local e multiplos reinicios a Etapa 3 atinge F superior as custas de maior CPU/RAM (selecao de vitima por p2_mat vs matriz de intersecao/first-improvement), enquanto na busca exata ha empate integral (delta_F = 0.0).

---

## 4. Experimento Controlado de Despacho (Condicionante III e Exigencia 4)

### Bloco A: Limiar micro `max(36, 3J)` (controle) vs `max(20, 2J)` (tratamento experimental)

| Cenario | Grupo | Alg. Controle (3J) | Alg. Tratamento (2J) | F Controle | F Tratamento | Delta F | Tempo (3J vs 2J) |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `micro_p20_J8_B22_s42` | `janela_2J_3J` | `algoritmo_guloso` | `busca_local_trocas` | 0.98733061 | 0.98662690 | -0.00070371 | 0.0133s vs 0.0099s |
| `micro_p25_J10_B24_s42` | `janela_2J_3J` | `algoritmo_guloso` | `busca_local_trocas` | 0.95152119 | 0.97296116 | +0.02143997 | 0.0186s vs 0.0132s |
| `micro_p25_J12_B30_s42` | `janela_2J_3J` | `algoritmo_guloso` | `busca_local_trocas` | 0.96415768 | 0.97657188 | +0.01241420 | 0.0221s vs 0.0170s |
| `micro_p25_J12_B30_s101` | `janela_2J_3J` | `algoritmo_guloso` | `busca_local_trocas` | 0.96719965 | 0.98095334 | +0.01375369 | 0.0218s vs 0.0188s |
| `micro_p22_J14_B32_f2_s42` | `janela_2J_3J` | `algoritmo_guloso` | `busca_local_trocas` | 0.97348956 | 0.98544718 | +0.01195762 | 0.0248s vs 0.0186s |
| `micro_p25_J16_B40_s42` | `janela_2J_3J` | `algoritmo_guloso` | `busca_local_trocas` | 0.97572834 | 0.98588500 | +0.01015666 | 0.0323s vs 0.0238s |
| `controle_fora_janela_p20_J10_B300` | `fora_janela_amplo` | `multiplos_reinicios` | `multiplos_reinicios` | 0.99193181 | 0.99193181 | +0.00000000 | 0.0988s vs 0.0967s |
| `controle_fora_janela_p25_J16_B320` | `fora_janela_amplo` | `multiplos_reinicios` | `multiplos_reinicios` | 0.99149012 | 0.99149012 | +0.00000000 | 0.1635s vs 0.1686s |

- **Na janela `[2J, 3J)`:** `5` vitorias de `2J`, `0` empates, `1` derrotas; `delta_F_medio = +0.01150307`.
- **Invariancia fora da janela (`B >= 3J`):** `True`.
- **Decisao objetiva do Bloco A:** `adotar_experimental_2J`.

### Bloco B: Inicializacao `padrao` (controle) vs `mista_equilibrada` (tratamento) em carteiras heterogeneas

| Cenario | Grupo | F Padrao | F Mista Equilibrada | Delta F | Tempo (Padrao vs Mista) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `mista_p21_2x16_8x15_B200_s42` | `heterogenea_media` | 0.98138600 | 0.97989138 | -0.00149462 | 0.0886s vs 0.0876s |
| `mista_p21_2x16_8x15_B200_s101` | `heterogenea_media` | 0.97814346 | 0.97772076 | -0.00042270 | 0.1024s vs 0.0518s |
| `mista_p25_1x18_2x17_6x15_B300_s42` | `heterogenea_ampla` | 0.94461125 | 0.94248474 | -0.00212651 | 0.6490s vs 0.3362s |
| `mista_p25_1x18_2x17_6x15_B300_s101` | `heterogenea_ampla` | 0.94836027 | 0.94643653 | -0.00192374 | 0.5855s vs 0.3509s |
| `mista_p23_pool_fixas_B240_s42` | `heterogenea_composicao_pool` | 0.96199337 | 0.95525198 | -0.00674139 | 0.1709s vs 0.1102s |
| `mista_p19_estreita_B150_s42` | `heterogenea_restrita` | 0.99289066 | 0.99080765 | -0.00208301 | 0.0691s vs 0.0538s |

- **Resumo Bloco B:** `0` vitorias de `mista_equilibrada`, `0` empates, `6` derrotas; `delta_F_medio = -0.00246533`.
- **Decisao objetiva do Bloco B:** `manter_inicializacao_padrao`.
- **Politica recomendada:** `{'politica_micro_recomendada': 'adotar_experimental_2J', 'inicializacao_mista_recomendada': 'manter_inicializacao_padrao', 'etapa4_inalterada': True}`.

---

## 5. Validacao Ponta a Ponta, Fail-Closed e Limitacoes

| Cenario E2E (`/api/v1/lotofacil-modo4/gerar`) | Algoritmo | Qtd Jogos | F(API) | Div vs Ref | 6 Grandezas | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `e2e_exata_pequena_p16_J4` | `busca_exata_pequena` | 4 | 0.99560027 | 1.11e-16 | `True` | `OK` |
| `e2e_regular_orc56_p25` | `multiplos_reinicios` | 16 | 0.99149012 | 1.11e-16 | `True` | `OK` |
| `e2e_final_zero_fixas_todos_p20_J8` | `busca_local_trocas` | 8 | 0.98966524 | 1.11e-16 | `True` | `OK` |
| `e2e_independencia_fixas_pool_p22_J10` | `multiplos_reinicios` | 10 | 0.99329577 | 0.00e+00 | `True` | `OK` |
| `e2e_mista_heterogenea_p21_2x16_6x15` | `multiplos_reinicios` | 8 | 0.97703557 | 0.00e+00 | `True` | `OK` |
| `e2e_micro_orcamento_p25_J12_B30` | `algoritmo_guloso` | 12 | 0.96415768 | 0.00e+00 | `True` | `OK` |

- **Testes negativos HTTP 422 (`historico`, conflitos, orcamento baixo, ambiguidade):** `True` (todos com `0` jogos).
- **Testes fail-closed cliente (offline, timeout, 500, 503, JSON corrompido):** `True` (todos com `sucesso=False`, `jogos=[]`, `fallback_executado=False`).
- **Adulteracao isolada de artefato Lotofacil e selo Lotomania (diretorio temporario):** `True` (HTTP `503`, `0` jogos).

**Limitacoes explicitas desta etapa:**
1. A integracao desta etapa opera exclusivamente em instancia de homologacao isolada; `api.py` de producao e a interface Web/Mobile permanecem intocados ate autorizacao expressa.
2. A otimizacao heuristica (gulosa, busca local, multiplos reinicios e estrategia combinada) nao fornece prova de otimalidade global fora de `busca_exata_pequena`.
3. Os ganhos ou empates observados no experimento de despacho limitam-se as dimensoes, orcamentos e sementes avaliados, nao autorizando generalizacoes irrestritas nem alegacoes de aumento da probabilidade individual por aposta.
