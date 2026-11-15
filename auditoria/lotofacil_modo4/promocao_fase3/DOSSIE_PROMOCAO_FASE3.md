# DOSSIE E ATA DA FASE 3 - PROMOCAO CONTROLADA EM PRODUCAO (LOTOFACIL MODO 4)

**Versao do Runbook:** `1.0.0-fase3-preparacao`  
**Versao Avaliada:** `5.1.0-promocao-controlada`  
**Data/Hora (UTC):** `2026-11-15T01:52:43.509646+00:00`  
**Veredito:** `GO` | **Abortada:** `False`  
**Modo Pos-Rollback:** `encerrar_em_off_standby` | **Estado Final Ativo:** `False`  

## 1. Resumo Executivo das 6 Etapas da Fase 3

| Etapa | Resultado | Evidencia Chave |
| :--- | :--- | :--- |
| 1. Snapshot Passivo Anterior | `GO` | PID=`10304`, SHA-256 estado=`42d50331a3cfec6e659ca224e36f996fba5e58611ec9d6b498b1506d337cd2a2`, Selados=`7/7`, Legados+Lotomania=`True` |
| 2. Reinicio ON e Integridade Pos-Reinicio | `GO` | Processo ON=`True` (PID=`5324`), Selados pos-reinicio=`True`, Divergencias=`0` |
| 3. Teste Controlado e Cenarios 422 | `GO` | HTTP pequeno=`200`, Latencia=`0.0651 s`, Diff F=`0.0`, `/avaliar` ok=`True`, Negativos 422 ok=`True` |
| 4. Monitoramento de Recursos e Legados | `GO` | RSS pico=`61.07 MB`, Latencia ok=`True`, Telemetria ok=`True`, Legados+Lotomania=`True` |
| 5. Rollback Comprovado para OFF | `GO` | Disponivel=`False`, `/gerar` HTTP=`503` (`0` jogos), `/avaliar` HTTP=`503` (`0` jogos), Fallback=`False` |
| 6. Estado Final Pos-Rollback | `GO` | Modo aplicado=`encerrar_em_off_standby`, Estado final ativo=`False`, Verificacao ok=`True` |

## 2. Detalhamento da Etapa 1 (Snapshot Anterior) e Etapa 2 (Reinicio ON + Integridade)

* **Processo inicial na porta 8000 (OFF_STANDBY):** PID `10304`, `rss_atual_mb = 68.3 MB`, `rss_pico_mb = 69.51 MB`, `privado_mb = 54.28 MB`.
* **Governanca pre-janela:** `feature_flag_ativa = False`, `experimental_2j_habilitada = False`, `politica_micro_padrao = conservadora_3J`, `inicializacao_mista = padrao`.
* **Isolamento de ambiente (allowlist):** `3` chaves permitidas, `57` variaveis externas omitidas por seguranca, `proibir_dump_ambiente_completo = True`.
* **Mapa de arquivos legados em disco:** `23` arquivos monitorados (`sha256_mapa_legados_disco = a3cffc581bb1d38900a6e6c7ce88558c13a96054f88f24ef3443584fb22c28bd`).
* **Reinicio controlado ON (Etapa 2):** PID `5324`, `integridade_7_selados_pos.integro = True`, `selo_lotomania_valido = True`, `divergencias_totais = []`.

## 3. Detalhamento da Etapa 3 (Teste Controlado) e Etapa 4 (Monitoramento)

* **Carteira pequena controlada (3 jogos, semente 42, `conservadora_3J`):** `HTTP 200`, latencia `0.0651 s`, `diff_F_pequeno = 0.0`, `hash_carteira_pequena = de5e70b1163ae7dee7e0841d5326b265344ba26c21a54532adb6d9ca35faae29`.
* **Auditoria `/avaliar`:** `avaliar_ok = True`, `diff_F_avaliar = 0.0`.
* **Bloqueios fail-closed (`HTTP 422`, `0` jogos, `fallback_executado = False`):** `negativos_422_ok = True`, cenarios validados: `{"experimental_2J": {"jogos": 0, "status_http": 422}, "historico_proibido": {"jogos": 0, "status_http": 422}, "inicializacao_mista": {"jogos": 0, "status_http": 422}}`.
* **Memoria e telemetria sob ativacao (Etapa 4):** `rss_atual_mb = 61.07 MB`, `rss_pico_mb = 61.07 MB`, `privado_mb = 48.05 MB`, `total_requisicoes_gerar = 2`, `total_sucesso_gerar = 1`, `total_bloqueios_politica_experimental = 1`, `total_erros_validacao = 2`, `total_erros_internos = 0`, `total_requisicoes_avaliar = 1`.

## 4. Detalhamento da Etapa 5 (Rollback Comprovado) e Etapa 6 (Encerramento OFF_STANDBY)

* **Comprovacao de rollback ON para OFF:** `status_disponivel = False`, `status_feature_flag = False`, `POST /gerar = HTTP 503` (`0` jogos entregues, `fallback_executado = False`), `POST /avaliar = HTTP 503` (`0` jogos entregues), `legados_e_lotomania_ok = True`.
* **Estado final pos-rollback (Etapa 6):** `modo_aplicado = encerrar_em_off_standby`, `estado_final_ativo = False`, `verificacao_ok = True`.

## 5. Hashes SHA-256 dos 7 Arquivos Selados (Pre e Pos-Janela)

| Arquivo Monitorado | SHA-256 Verificado |
| :--- | :--- |
| `lotofacil_modo4/promocao_producao.py` | `5bc19c7e8313f0042afd7414373de334ddb6832350789c1c026aca3996a66996` |
| `api.py` | `d60cad46afbf563530a77e4950b142c1ebd54bcd2fef2e17bc23d84fc9de7c0b` |
| `motor_lotofacil.py` | `7dcaf017f8a4845fe42f5a58cb978c81e95e8f55b96ef558b9a0ec551ba077c3` |
| `js/engines/motor_lotofacil_modo4_engine.js` | `943b4bba0a6928dfc9402c6f5f57598a7820302b4faaa3a10c48528a11231413` |
| `index.html` | `639bf551a59a3eeef9b1ee322ba16e9eeb6bc3477616338fef996fc155a12de0` |
| `js/ui.js` | `e11df28bae9c9671b5ea4a69dfd389c8c66663ecf4caf139be56f0b2f14ca427` |
| `B2B_Loterias_Mobile.html` | `22d7439d279073dae543eb1a8c89649dd38abe18c5dd76727edfff29b2ac02e3` |

## 6. Clausula Matematica Obrigatoria

> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.

**Decisao Formal da Ata da Fase 3:** `GO` | **Modo Final:** `encerrar_em_off_standby` | **Lotofacil MODO 4 Ativo:** `False`
