# RELATORIO TECNICO - PREPARACAO AUDITAVEL DA FASE 3 (LOTOFACIL MODO 4)

**Versao Alvo:** `5.1.0-promocao-controlada`  
**Versao da Preparacao Fase 3:** `1.0.0-fase3-preparacao`  
**Branch de Trabalho:** `feat/lotomania-modo4-jobs-mobile` (`main` preservada sem merge)  
**Estado Operacional:** `FASE_3_PREPARADA_AGUARDANDO_AUTORIZACAO_PRODUCAO` | **Porta `8000`:** `LOTOFACIL_MODO4_ATIVO=False`

## 1. Escopo Executado

Esta entrega formaliza exclusivamente a **Preparacao Auditavel da Fase 3**, criando configuracao dedicada, runbook operacional, executor com trava dupla fail-closed e suite de testes em porta efemera isolada. Nenhum arquivo selado, motor matematico, manifesto historico ou processo em execucao na porta `8000` foi modificado ou reiniciado.

## 2. Incorporacao das Cinco Exigencias Adicionais e Tres Definicoes Operacionais

| Controle Implementado | Mecanismo no Codigo e Configuracao |
| :--- | :--- |
| Exigencia 1: Snapshot Anterior | `capturar_snapshot_producao_somente_leitura` registra PID ouvinte TCP via `parsear_pid_netstat_tcp`, memoria Win32 (`WorkingSetSize`, `PeakWorkingSetSize`, `PrivateUsage`), versao, allowlist de ambiente, `/health`, `/status`, hashes dos 7 arquivos selados e contratos de legados/Lotomania. |
| Exigencia 2: Integridade Posterior | `recalcular_hashes_7_arquivos_selados` recalcula os 7 SHA-256 em disco imediatamente apos reinicio ON e confronta com manifestos selados e snapshot anterior. |
| Exigencia 3: Teste Controlado Escalonado | `_executar_teste_controlado_e_adicionais` executa primeiro carteira pequena (`3` jogos simples, `conservadora_3J`, semente `42`), valida `diff_F <= 1e-12`, `historico_utilizado=None` e clausula obrigatoria; somente se aprovada executa `/avaliar` e cenarios negativos `HTTP 422`. |
| Exigencia 4: Monitoramento Pos-Ativacao | `_monitorar_pos_ativacao` confere `0` erros HTTP inesperados, latencia controlada, `PeakWorkingSetSize <= 1024.0 MB`, coerencia de contadores em `/status` e funcionamento `HTTP 200` dos 4 motores legados e da Lotomania MODO 4. |
| Exigencia 5: Rollback Comprovado | `_validar_rollback_503_zero_jogos` alterna para `LOTOFACIL_MODO4_ATIVO=False` e comprova `HTTP 503`, `0` jogos, `fallback_executado=False` e continuidade dos legados e da Lotomania. |
| Definicao 1: Allowlist de Ambiente | `sanitizar_variaveis_ambiente_snapshot` captura exclusivamente `LOTOFACIL_MODO4_ATIVO`, `LOTOFACIL_MODO4_PERMITIR_EXPERIMENTAL_2J` e `LOTOFACIL_MODO4_POLITICA_MICRO`, omitindo qualquer outra chave do sistema operacional (`57` variaveis omitidas no host atual). |
| Definicao 2: Ordem Pos-Rollback Explicita | `validar_ordem_pos_rollback` bloqueia execucao sem escolha explicita em `--pos-rollback-modo` (`encerrar_em_off_standby` ou `reativar_on_com_revalidacao`). |
| Definicao 3: Contingencia Fail-Closed | `planejar_acao_contingencia_fase3` separa divergencia em arquivo selado (`abortar_fail_closed_divergencia_selada`, sem mascaramento) de falha de subida/funcional com selo integro (`abortar_e_restaurar_porta_8000_off`). |

## 3. Evidencia de Snapshot Passivo na Porta `8000` (Sem Reinicio)

Sonda passiva executada via `--snapshot-somente-leitura` sobre a instancia vigente em `127.0.0.1:8000`:

* **PID ouvinte detectado:** `15312` (`WorkingSetSize = 62.77 MB`, `PeakWorkingSetSize = 87.78 MB`, `PrivateUsage = 51.39 MB`).
* **Estado normalizado SHA-256:** `42d50331a3cfec6e659ca224e36f996fba5e58611ec9d6b498b1506d337cd2a2`.
* **Flags de governanca em producao:** `feature_flag_ativa = False`, `experimental_2j_habilitada = False`, `politica_micro_padrao = "conservadora_3J"`, `inicializacao_mista = "padrao"`, todos os contadores de telemetria em `0`.
* **Isolamento de ambiente:** `allowlist` aplicada em `3` chaves de governanca; `57` variaveis externas do host omitidas por seguranca.

## 4. Hashes SHA-256 dos Artefatos de Preparacao e Arquivos Selados Preservados

| Arquivo | SHA-256 | Situacao |
| :--- | :--- | :--- |
| `auditoria/lotofacil_modo4/promocao_fase3/config_promocao_fase3.json` | `c55242fc6191d492978611ec25e0ec16b50aceae1b602e521bacbb8c0cbe2d9c` | Novo (Preparacao Fase 3) |
| `auditoria/lotofacil_modo4/promocao_fase3/RUNBOOK_PROMOCAO_FASE3.md` | `010dc68525ca07410851d38f5ac0d9f7598e888df5a266596ebc7fd8e661c219` | Novo (Preparacao Fase 3) |
| `lotofacil_modo4/promocao_fase3_runbook.py` | `ef9be124c60491d1fbbcb2f1bf806f6faffc4945cceb103a844a9d483d0a35fa` | Novo (Preparacao Fase 3) |
| `testes/test_lotofacil_modo4_promocao_fase3_preparacao.py` | `82ce91c0cce05e79401198805393e607e0126e25b24971acbbad0a775c209a80` | Novo (Preparacao Fase 3) |
| `lotofacil_modo4/promocao_producao.py` | `5bc19c7e8313f0042afd7414373de334ddb6832350789c1c026aca3996a66996` | Selado e preservado |
| `api.py` | `d60cad46afbf563530a77e4950b142c1ebd54bcd2fef2e17bc23d84fc9de7c0b` | Selado e preservado |
| `motor_lotofacil.py` | `7dcaf017f8a4845fe42f5a58cb978c81e95e8f55b96ef558b9a0ec551ba077c3` | Selado e preservado |
| `js/engines/motor_lotofacil_modo4_engine.js` | `943b4bba0a6928dfc9402c6f5f57598a7820302b4faaa3a10c48528a11231413` | Selado e preservado |
| `index.html` | `639bf551a59a3eeef9b1ee322ba16e9eeb6bc3477616338fef996fc155a12de0` | Selado e preservado |
| `js/ui.js` | `e11df28bae9c9671b5ea4a69dfd389c8c66663ecf4caf139be56f0b2f14ca427` | Selado e preservado |
| `B2B_Loterias_Mobile.html` | `22d7439d279073dae543eb1a8c89649dd38abe18c5dd76727edfff29b2ac02e3` | Selado e preservado |
| `motor_lotomania_modo4.py` | `94a2d1001d235e0e9bd543aeee697bac0ac6c60b1d24654838e452d6f42c68f9` | Selado e preservado |

## 5. Clausula Matematica Obrigatoria

> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.

**Situacao:** Preparacao concluida para auditoria e deliberacao. Nenhuma intervencao em producao (porta `8000`) ou merge em `main` sera realizada sem autorizacao humana expressa.
