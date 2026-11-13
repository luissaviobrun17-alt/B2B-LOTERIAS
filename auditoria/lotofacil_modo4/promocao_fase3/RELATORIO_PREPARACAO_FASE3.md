# RELATORIO TECNICO: PREPARACAO AUDITAVEL DA FASE 3 (LOTOFACIL MODO 4)

**Versao Alvo:** `5.1.0-promocao-controlada`  
**Versao da Preparacao Fase 3:** `1.0.1-fase3-preparacao-revisada`  
**Branch de Trabalho:** `feat/lotomania-modo4-jobs-mobile` (`main` preservada sem merge)  
**Estado Operacional:** `FASE_3_PREPARADA_AGUARDANDO_AUTORIZACAO_PRODUCAO` | **Porta `8000`:** `LOTOFACIL_MODO4_ATIVO=False`

## 1. Escopo Executado e Fechamento das Divergencias de Governanca

Esta revisao da **Preparacao Auditavel da Fase 3** fecha integralmente as duas pendencias apontadas no parecer tecnico da preparacao anterior, mantendo a porta `8000` intocada em `OFF`, os sete arquivos selados preservados e a execucao da Fase 3 estritamente bloqueada (`exit code 2` por padrao).

### 1.1 Esclarecimento do Quarto Parametro de Governanca (`inicializacao_mista`)

Por inspecao direta do codigo selado (`lotofacil_modo4/promocao_producao.py` e `api.py`), o servico em producao le **exclusivamente tres variaveis de ambiente** em `os.environ`: `LOTOFACIL_MODO4_ATIVO`, `LOTOFACIL_MODO4_PERMITIR_EXPERIMENTAL_2J` e `LOTOFACIL_MODO4_POLITICA_MICRO`. Nao existe quarta variavel de ambiente para inicializacao mista. O quarto parametro (`inicializacao_mista = "padrao"`) origina-se de uma constante interna imutavel (`lotofacil_modo4/promocao_producao.py:INICIALIZACAO_MISTA_FIXA`, com `suporta_override_env = False`), exposta pelo endpoint `/api/v1/lotofacil-modo4/status`.

Para eliminar qualquer ambiguidade entre allowlist de ambiente e parametros efetivos em producao, o snapshot passou a registrar separadamente:

| Bloco do Snapshot / Configuracao | Parametro | Fonte Real | Chave em `os.environ` | Suporta Override via Env |
| :--- | :--- | :--- | :--- | :--- |
| `variaveis_ambiente.allowlist_aplicada` + `quatro_parametros_governanca.1_*` | `feature_flag_ativa` | Variavel de ambiente + `/status` | `LOTOFACIL_MODO4_ATIVO` | Sim |
| `variaveis_ambiente.allowlist_aplicada` + `quatro_parametros_governanca.2_*` | `experimental_2j_habilitada` | Variavel de ambiente + `/status` | `LOTOFACIL_MODO4_PERMITIR_EXPERIMENTAL_2J` | Sim (travada em `False` na Fase 3) |
| `variaveis_ambiente.allowlist_aplicada` + `quatro_parametros_governanca.3_*` | `politica_micro_padrao` | Variavel de ambiente + `/status` | `LOTOFACIL_MODO4_POLITICA_MICRO` | Sim (homologada em `conservadora_3J`) |
| `configuracao_interna_imutavel` + `quatro_parametros_governanca.4_*` | `inicializacao_mista` | Constante interna imutavel (`INICIALIZACAO_MISTA_FIXA = "padrao"`) + conferencia `/status` | Nenhuma (`None`) | Nao (`False`) |

### 1.2 Designacao Formal do Estado Final Pos-Rollback (`encerrar_em_off_standby`)

A configuracao, o runbook, o executor (`MODO_POS_ROLLBACK_DESIGNADO`) e as verificacoes automatizadas passam a registrar formalmente **`encerrar_em_off_standby`** como o estado final designado ao termino da Fase 3, apos a comprovacao obrigatoria de rollback em `LOTOFACIL_MODO4_ATIVO=False` (`HTTP 503`, `0` jogos e continuidade dos motores legados e Lotomania). A eventual opcao `reativar_on_com_revalidacao` fica restrita a uma deliberacao posterior especifica, mantendo-se a exigencia fail-closed de passar `--pos-rollback-modo` explicitamente na CLI.

## 2. Incorporacao das Cinco Exigencias Adicionais e Tres Definicoes Operacionais

| Controle Implementado | Mecanismo no Codigo e Configuracao |
| :--- | :--- |
| Exigencia 1: Snapshot Anterior | `capturar_snapshot_producao_somente_leitura` registra PID ouvinte TCP via `parsear_pid_netstat_tcp`, memoria Win32 (`WorkingSetSize`, `PeakWorkingSetSize`, `PrivateUsage`), versao, allowlist de 3 chaves de ambiente, `configuracao_interna_imutavel`, `quatro_parametros_governanca`, `/health`, `/status`, hashes dos 7 arquivos selados e contratos de legados/Lotomania. |
| Exigencia 2: Integridade Posterior | `recalcular_hashes_7_arquivos_selados` recalcula os 7 SHA-256 em disco imediatamente apos reinicio ON e confronta com manifestos selados e snapshot anterior. |
| Exigencia 3: Teste Controlado Escalonado | `_executar_teste_controlado_e_adicionais` executa primeiro carteira pequena (`3` jogos simples, `conservadora_3J`, semente `42`), valida `diff_F <= 1e-12`, `historico_utilizado=None` e clausula obrigatoria; somente se aprovada executa `/avaliar` e cenarios negativos `HTTP 422`. |
| Exigencia 4: Monitoramento Pos-Ativacao | `_monitorar_pos_ativacao` confere `0` erros HTTP inesperados, latencia controlada, `PeakWorkingSetSize <= 1024.0 MB`, coerencia de contadores em `/status` e funcionamento `HTTP 200` dos 4 motores legados e da Lotomania MODO 4. |
| Exigencia 5: Rollback Comprovado | `_validar_rollback_503_zero_jogos` alterna para `LOTOFACIL_MODO4_ATIVO=False` e comprova `HTTP 503`, `0` jogos, `fallback_executado=False` e continuidade dos legados e da Lotomania. |
| Definicao 1: Allowlist + Origem do 4o Parametro | `sanitizar_variaveis_ambiente_snapshot` captura exclusivamente as 3 chaves existentes em `os.environ` (`57` variaveis externas omitidas no host atual) e explicita `configuracao_interna_imutavel.inicializacao_mista` (`suporta_override_env=False`), consolidado em `quatro_parametros_governanca`. |
| Definicao 2: Ordem Pos-Rollback e Estado Designado | `validar_ordem_pos_rollback` exige escolha explicita em `--pos-rollback-modo`; `MODO_POS_ROLLBACK_DESIGNADO` e `config_promocao_fase3.json` designam formalmente `encerrar_em_off_standby` como estado final alvo da Fase 3. |
| Definicao 3: Contingencia Fail-Closed | `planejar_acao_contingencia_fase3` separa divergencia em arquivo selado (`abortar_fail_closed_divergencia_selada`, sem mascaramento) de falha de subida/funcional com selo integro (`abortar_e_restaurar_porta_8000_off`). |

## 3. Evidencia de Snapshot Passivo na Porta `8000` (Sem Reinicio)

Sonda passiva executada via `--snapshot-somente-leitura` sobre a instancia vigente em `127.0.0.1:8000`:

* **PID ouvinte detectado:** `15312` (`rss_atual_mb = 62.99 MB`, `rss_pico_mb = 87.78 MB`, `privado_mb = 51.39 MB`).
* **Estado normalizado SHA-256:** `42d50331a3cfec6e659ca224e36f996fba5e58611ec9d6b498b1506d337cd2a2`.
* **Quatro parametros de governanca conferidos:** `feature_flag_ativa = False` (`LOTOFACIL_MODO4_ATIVO`), `experimental_2j_habilitada = False` (`LOTOFACIL_MODO4_PERMITIR_EXPERIMENTAL_2J`), `politica_micro_padrao = "conservadora_3J"` (`LOTOFACIL_MODO4_POLITICA_MICRO`) e `inicializacao_mista = "padrao"` (`INICIALIZACAO_MISTA_FIXA`, `chave_env = None`, `conforme = True`); todos os contadores de telemetria em `0`.
* **Isolamento de ambiente:** `allowlist` aplicada exclusivamente sobre `3` variaveis (`NAO_DEFINIDA_USAR_PADRAO_SEGURO` para as tres); `57` variaveis externas do host omitidas por seguranca.
* **Arquivos legados em disco verificados:** `23` arquivos (`sha256_mapa_legados_disco = a3cffc581bb1d38900a6e6c7ce88558c13a96054f88f24ef3443584fb22c28bd`).

## 4. Hashes SHA-256 dos Artefatos de Preparacao e Arquivos Selados Preservados

| Arquivo | SHA-256 | Situacao |
| :--- | :--- | :--- |
| `auditoria/lotofacil_modo4/promocao_fase3/config_promocao_fase3.json` | `f9706e3f6e2b66ba2632c90ea83cc7c7db609265f20fb1c22ec78efa72bbf14f` | Atualizado (Revisao Preparacao Fase 3) |
| `auditoria/lotofacil_modo4/promocao_fase3/RUNBOOK_PROMOCAO_FASE3.md` | `1e7e8cce8ca07046b0f9c232552f96334d8aa4449eb2277e70ae9fe14c9fe6f1` | Atualizado (Revisao Preparacao Fase 3) |
| `lotofacil_modo4/promocao_fase3_runbook.py` | `533dc8388bcd6bc57b2d560f7d1e717b25d82d0a97b64a6d4e2d825c9f9c4b5d` | Atualizado (Revisao Preparacao Fase 3) |
| `testes/test_lotofacil_modo4_promocao_fase3_preparacao.py` | `21659ab333c0919543748ec5050bc6c694cc1c7661ef24e14954ada6618920b9` | Atualizado (Revisao Preparacao Fase 3) |
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

**Situacao:** Divergencias de governanca da Preparacao da Fase 3 sanadas. Nenhuma intervencao em producao (porta `8000`) ou merge em `main` sera realizada sem autorizacao humana expressa.
