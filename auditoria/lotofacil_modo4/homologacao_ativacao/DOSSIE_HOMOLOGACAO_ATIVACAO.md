# DOSSIE E ATA DE HOMOLOGACAO ESPECIFICA DE ATIVACAO - LOTOFACIL MODO 4

**Versao Avaliada:** `5.1.0-promocao-controlada`  
**Data/Hora (UTC):** `2026-11-13T22:21:54.576286+00:00`  
**Veredito Automatico Go/No-Go:** `GO`  
**Hardware Medido:** `CPU 16 threads` | `RAM livre 15.16 GB / 29.79 GB` | `Windows-11-10.0.26200-SP0`  

## 1. Resumo das 6 Frentes Avaliadas

| Frente | Resultado | Evidencia Chave |
| :--- | :--- | :--- |
| 1. Auditoria Criptografica (Pre e Pos) | `GO` | Pre divergencias=`0`, Pos divergencias=`0`, Ed25519=`True` |
| 2. Rotas e Contratos (`/status`, `/gerar`, `/avaliar`) | `GO` | Diff AST simples=`1.11e-16`, Diff `/avaliar`=`1.11e-16`, Negativos 422 ok=`True` |
| 3. Carga Escalonada (Uvicorn `workers=1`, Portas Isoladas) | `GO` | Pico Windows RSS=`76.05 MB`, Delta baseline para carga=`6.9 MB`, Mem ok=`True` |
| 4. Auditoria Chrome Real (Web + Mobile) | `GO` | Execucoes aprovadas=`4/4` |
| 5. Nao Interferencia Sob Carga | `GO` | Lotomania hash identico=`True`, Disco legados intacto=`True` |
| 6. Rollback ON para OFF e Preservacao 8000 | `GO` | Runtime rollback ok=`True`, Subprocesso OFF ok=`True`, Prod 8000 intacta=`True` |

## 2. Patamares de Carga Escalonada

| Patamar | Clientes Simultaneos | Requisicoes | Taxa Erro (%) | p95 `/gerar` simples (s) | p99 `/gerar` simples (s) | Pico RSS Windows (MB) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `patamar_0_baseline_1_cliente` | `1` | `20` | `0.0` | `0.1318` | `0.1318` | `67.25` | `GO` |
| `patamar_1_1x_cores_fisicos_8_clientes` | `8` | `32` | `0.0` | `0.8071` | `0.8071` | `69.51` | `GO` |
| `patamar_2_1x_threads_logicas_16_clientes` | `16` | `48` | `0.0` | `1.366` | `1.366` | `72.93` | `GO` |
| `patamar_3_sobrecarga_24_clientes` | `24` | `72` | `0.0` | `1.9628` | `2.0894` | `76.05` | `GO` |

## 3. Hashes Examinados (Pre e Pos-Janela)

| Arquivo Monitorado | SHA-256 Pos-Janela |
| :--- | :--- |
| `lotofacil_modo4/promocao_producao.py` | `5bc19c7e8313f0042afd7414373de334ddb6832350789c1c026aca3996a66996` |
| `api.py` | `d60cad46afbf563530a77e4950b142c1ebd54bcd2fef2e17bc23d84fc9de7c0b` |
| `motor_lotofacil.py` | `7dcaf017f8a4845fe42f5a58cb978c81e95e8f55b96ef558b9a0ec551ba077c3` |
| `js/engines/motor_lotofacil_modo4_engine.js` | `943b4bba0a6928dfc9402c6f5f57598a7820302b4faaa3a10c48528a11231413` |
| `index.html` | `639bf551a59a3eeef9b1ee322ba16e9eeb6bc3477616338fef996fc155a12de0` |
| `js/ui.js` | `e11df28bae9c9671b5ea4a69dfd389c8c66663ecf4caf139be56f0b2f14ca427` |
| `B2B_Loterias_Mobile.html` | `22d7439d279073dae543eb1a8c89649dd38abe18c5dd76727edfff29b2ac02e3` |

## 4. Limites Cientificos e Clausula Obrigatoria

> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.

**Decisao da Ata:** `GO` | **Motivos NO-GO (se houver):** `[]`