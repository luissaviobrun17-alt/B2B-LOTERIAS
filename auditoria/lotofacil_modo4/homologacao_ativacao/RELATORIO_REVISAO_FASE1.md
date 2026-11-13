# RELATORIO DA REVISAO DA FASE 1 - CALIBRACAO E ENDURECIMENTO DOS CRITERIOS (LOTOFACIL MODO 4)

**Versao Alvo da Promocao:** `5.1.0-promocao-controlada`  
**Versao Revisada do Runbook:** `1.1.0-fase1-revisada`  
**Timestamp da Microcalibracao (UTC):** `2026-11-13T22:04:24.894448+00:00`  
**Porta Isolada Utilizada:** `127.0.0.1:18080` (`uvicorn workers=1`)  
**Situacao de Governanca:** `REVISAO_FASE_1_CONCLUIDA` | `FASE_2_BLOQUEADA` | `FASE_3_BLOQUEADA` | `PORTA_8000_OFF_PRESERVADA`

## 1. Resumo das Correcoes Executadas nos Sete Pontos de Controle

| Ponto de Controle | Problema Corrigido | Implementacao Validada |
| :--- | :--- | :--- |
| 1. Latencia (`p95`, `p99` e baseline) | Ausencia de `1` cliente, ausencia de multipla `16` dezenas nos patamares e limiares desconectados do runtime | Cobertura de `[1, 8, 16, 24]` `clientes_simultaneos`, todas as 6 categorias de rotas intercaladas incluindo `caso_multipla_16_independencia`, com limites `max_p95_s` e `max_p99_s` por rota |
| 2. Determinismo e ressalva das sementes | Agrupamento por conjunto plano e exigencia potencialmente falsa entre sementes distintas | Agrupamento por SHA-256 canonico de `(endpoint, metodo, payload completo)`, auditoria sequencial `42 -> 43 -> 42 -> 999` comprovando ausencia de dependencia de estado e `historico_utilizado=None` |
| 3. Lotomania sob concorrencia | Apenas contagem de hashes sem checagem por assinatura canonica em todos os niveis | Repetibilidade estrita de `hash_carteira_sha256_v2_canonico` verificada em todos os patamares (`1`, `8`, `16` e `24` clientes) |
| 4. Memoria (`PeakWorkingSetSize`) | Medicao apenas pos-patamar via `WorkingSetSize` sem explicitar processo alvo | Thread daemon amostrou `WorkingSetSize`, `PeakWorkingSetSize` e `PrivateUsage` a cada `0.25 s` exclusivamente no PID do subprocesso `uvicorn workers=1` (`10872`) |
| 5. Nomenclatura de concorrencia | Uso ambiguo de `workers_simultaneos` | Substituido por `clientes_simultaneos` com `workers=1` explicito na chamada `uvicorn.run(...)` |
| 6. Nao interferencia completa dos legados | Verificacao rasa de status `200` sem carga concorrente nem hashes | Baseline OFF vs probes disparados simultaneamente durante carga de Lotofacil MODO 4 ON, checagem estrutural e de faixas (`1..100` na Lotomania legada, `1..25`, `1..31`, `1..60`), hashes SHA-256 de respostas/jogos e `23` arquivos em disco (`motor_*.py` + `data/*.json`) |
| 7. Preservacao fail-closed da porta `8000` | Falha silenciosa quando `8000` estava inacessivel | Captura completa de `/health` e `/api/v1/lotofacil-modo4/status` antes e depois, com comparacao de SHA-256 normalizado e reprovacao imediata se inacessivel ou mutada |

## 2. Evidencias Empiricas da Microcalibracao (`microcalibracao_fase1.json`)

| Patamar (`clientes_simultaneos`) | Total Req | Erro (%) | p95 `/gerar` simples / multipla16 (s) | p99 `/gerar` simples / multipla16 (s) | p95 `/status` / `/avaliar` (s) | p95 Lotomania / Legados (s) | Pico `PeakWorkingSetSize` (MB) | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `patamar_0` (`1` cliente) | `20` | `0.0` | `0.1340` / `0.1206` | `0.1340` / `0.1206` | `0.0366` / `0.0385` | `0.0558` / `0.0624` | `67.11` | `APROVADO` |
| `patamar_1` (`8` clientes) | `32` | `0.0` | `0.6804` / `0.6338` | `0.6804` / `0.6338` | `0.5400` / `0.6080` | `0.4638` / `0.0692` | `68.99` | `APROVADO` |
| `patamar_2` (`16` clientes) | `48` | `0.0` | `1.2087` / `1.2543` | `1.2087` / `1.2543` | `1.1131` / `1.1281` | `0.8251` / `0.3260` | `73.71` | `APROVADO` |
| `patamar_3` (`24` clientes) | `72` | `0.0` | `1.7405` / `1.7827` | `1.7723` / `1.7827` | `1.6339` / `1.7994` | `1.0050` / `0.3069` | `76.91` | `APROVADO` |

1. **Memoria:** warmup em `61.62 MB`, pico maximo real (`PeakWorkingSetSize`) de `76.91 MB` frente ao limite de `1024.0 MB`, e delta de `WorkingSetSize` entre baseline e sobrecarga de `+4.17 MB` frente ao teto de `150.0 MB`.
2. **Sementes e determinismo:** repetibilidade `42 -> 43 -> 42` identica no caso simples (`a21f44e82dac44afdc6eafd251c00d8f121c3d5b6da1f1b947be0e361ff78d6f`) e no caso multipla 16 dezenas (`7ca7e5e84228f2b70bef53faacb9f79b187419693a30dcadd106584e1a7fc089`), com `historico_utilizado=null` e `3` hashes distintos para `{42, 43, 999}` no caso simples e `2` para `{42, 43}` no caso multipla 16. Lotomania MODO 4 manteve `c3e0e60d4582103bd0d8661fb53c3334219499c966258701cadacaa16966ee27` em OFF e em todos os patamares sob carga.
3. **Nao interferencia dos legados:** os 4 motores responderam `HTTP 200` sob carga concorrente e mantiveram contratos integros; `/api/v1/motor-diadesorte` preservou exatamente o hash canonico de jogos `98e437c412aca2360238e9192689cc476eb3fc769ecb7c442b5b100c753405b9` e resposta `b71f36b9822d11b36959fb9fc79efb16c02378da8d382f598e73fed49f74647e` entre OFF e carga; `23` arquivos (`motor_*.py` + `data/*.json`) em disco permaneceram bit a bit identicos.
4. **Producao (`127.0.0.1:8000`):** acessivel antes e depois da microcalibracao, preservando `lotofacil_disponivel=false`, `feature_flag_ativa=false`, `experimental_2j_habilitada=false`, `politica_micro_padrao="conservadora_3J"`, `inicializacao_mista="padrao"` e SHA-256 normalizado identico `42d50331a3cfec6e659ca224e36f996fba5e58611ec9d6b498b1506d337cd2a2`.

## 3. Hashes SHA-256 Verificados (Artefatos da Revisao e Arquivos Selados Preservados)

| Arquivo | Categoria | SHA-256 |
| :--- | :--- | :--- |
| `lotofacil_modo4/homologacao_ativacao_runbook.py` | Executor isolado revisado | `17ff71ac649159a361f44e5671c949dabfbc087e9198a6baafcda0ede96aa416` |
| `auditoria/lotofacil_modo4/homologacao_ativacao/config_homologacao_ativacao.json` | Config calibrado `1.1.0-fase1-revisada` | `9496af2791e0b27dd8ce803853f6285499f99a208b0211b59c8aa51fddffc785` |
| `auditoria/lotofacil_modo4/homologacao_ativacao/RUNBOOK_HOMOLOGACAO_ATIVACAO.md` | Runbook revisado `1.1.0-fase1-revisada` | `08116f92a7592ad83726818f55e790399731d430e159b2bbb0976ac027ce79dd` |
| `auditoria/lotofacil_modo4/homologacao_ativacao/microcalibracao_fase1.json` | Evidencia empirica da microcalibracao | `7359ad9b6c5dd94674a81e57f7e448c54b40453d1c3d50d776a37d4493158b77` |
| `testes/test_lotofacil_modo4_homologacao_preparacao.py` | Suite Fase 1 endurecida | `43711a5345bbcc0d00a52a48f79bf1d4601371167cab959fe4bb21ca539d0488` |
| `api.py` | Selado (preservado intacto) | `d60cad46afbf563530a77e4950b142c1ebd54bcd2fef2e17bc23d84fc9de7c0b` |
| `index.html` | Selado (preservado intacto) | `639bf551a59a3eeef9b1ee322ba16e9eeb6bc3477616338fef996fc155a12de0` |
| `js/ui.js` | Selado (preservado intacto) | `e11df28bae9c9671b5ea4a69dfd389c8c66663ecf4caf139be56f0b2f14ca427` |
| `B2B_Loterias_Mobile.html` | Selado (preservado intacto) | `22d7439d279073dae543eb1a8c89649dd38abe18c5dd76727edfff29b2ac02e3` |
| `motor_lotofacil.py` | Selado (preservado intacto) | `7dcaf017f8a4845fe42f5a58cb978c81e95e8f55b96ef558b9a0ec551ba077c3` |
| `lotofacil_modo4/promocao_producao.py` | Selado (preservado intacto) | `5bc19c7e8313f0042afd7414373de334ddb6832350789c1c026aca3996a66996` |
| `js/engines/motor_lotofacil_modo4_engine.js` | Selado (preservado intacto) | `943b4bba0a6928dfc9402c6f5f57598a7820302b4faaa3a10c48528a11231413` |
| `motor_lotomania_modo4.py` | Selado Ed25519 (preservado intacto) | `94a2d1001d235e0e9bd543aeee697bac0ac6c60b1d24654838e452d6f42c68f9` |
| `manifesto_modo4.json` | Manifesto historico (preservado intacto) | `66e255cd526e2c72ec1fda3d3112cb918b4e678b1f264117593ca7cdf127e57c` |
| `auditoria/lotofacil_modo4/manifesto_etapa5.json` | Manifesto historico (preservado intacto) | `2f40c1a466b30ec75492777ab7d4886df573e87114a931b89b3b03befce5cf48` |
| `auditoria/lotofacil_modo4/manifesto_promocao_controlada.json` | Manifesto versionado (preservado intacto) | `df5624f03ee008c36d702e1ae8d0efc51411031e5729a2219d4418949d686021` |

## 4. Limite Matematico Obrigatorio

> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.
