# RUNBOOK DE HOMOLOGACAO ESPECIFICA DE ATIVACAO - LOTOFACIL MODO 4

**Versao Alvo:** `5.1.0-promocao-controlada`  
**Versao do Runbook:** `1.1.0-fase1-revisada`  
**Diretorio de Saida Isolado:** `auditoria/lotofacil_modo4/homologacao_ativacao`  
**Estado Vigente na Revisao:** `LOTOFACIL_MODO4_ATIVO=False`, `LOTOFACIL_MODO4_PERMITIR_EXPERIMENTAL_2J=False`, `politica_micro="conservadora_3J"`, `inicializacao_mista="padrao"`  
**Situacao de Governanca:** `REVISAO_FASE_1_CONCLUIDA` | `FASE_2_BLOQUEADA_AGUARDANDO_AUTORIZACAO` | `FASE_3_BLOQUEADA`

## 1. Modelo de Governanca em Etapas Independentes

1. **Fase 1 (Preparacao Inicial) e Revisao da Fase 1 (Calibracao e Endurecimento):** endurecimento dos sete pontos de controle no executor isolado (`lotofacil_modo4/homologacao_ativacao_runbook.py`), na configuracao (`config_homologacao_ativacao.json`), neste Runbook e na suite de preparacao (`testes/test_lotofacil_modo4_homologacao_preparacao.py`), acompanhado de microcalibracao empirica em porta dedicada (`18080`). Nenhum dos 7 arquivos selados em `manifesto_promocao_controlada.json` nem `motor_lotomania_modo4.py` foram alterados.
2. **Fase 2 (Homologacao Especifica Completa em Portas Isoladas):** continua **estritamente bloqueada** e somente podera ser executada apos avaliacao dos resultados desta revisao e nova autorizacao expressa, utilizando `--autorizar-homologacao-isolada` nas portas dedicadas `18080` e `18081`.
3. **Fase 3 (Eventual Ativacao em Producao):** somente apos emissao de Ata `GO` da Fase 2 e deliberacao expressa separada para ajustar `LOTOFACIL_MODO4_ATIVO=true`, preservando `experimental_2J` desabilitada por padrao.

## 2. Capacidade Real de Hardware e Arquitetura Uvicorn

| Recurso Medido | Valor Observado no Host | Impacto na Calibracao Endurecida |
| :--- | :--- | :--- |
| CPU | AMD Ryzen 7 255 (8 nucleos fisicos, 16 threads logicas, clock max. `3801 MHz`) | Calibra patamares em `1`, `8`, `16` e `24` `clientes_simultaneos` |
| Modelo Uvicorn | Subprocesso unico com `workers=1` explicito e pool AnyIO sob GIL Python `3.12.10` | Toda concorrencia externa traduz fila de clientes simultaneos sobre processo Python unico |
| Memoria RAM do Host | `29.79 GB` total; `16.07 GB` livre | Monitoramento exclusivo do PID do subprocesso Uvicorn `workers=1` (exclui Chrome e runner) |
| Amostragem de Memoria | Polling Win32 a cada `0.25s` durante cada patamar (`WorkingSetSize`, `PeakWorkingSetSize`, `PrivateUsage`) | Avalia `PeakWorkingSetSize <= 1024.0 MB` e crescimento de `WorkingSetSize <= 150.0 MB` |
| Armazenamento e Browser | `803.21 GB` livre; Chrome headless + CDP WebSocket stdlib (`playwright=false`, `psutil=false`) | Auditoria Web/Mobile real isolada sem dependencias externas |

## 3. Sete Pontos Corrigidos e Ressalva Matematica das Sementes

1. **Latencia (`p95` e `p99` por rota e cliente base):** todos os patamares agora incluem baseline de `1` cliente e escalonamento para `8`, `16` e `24` `clientes_simultaneos`, cobrindo `/api/v1/lotofacil-modo4/gerar` simples (`15` dezenas), `/api/v1/lotofacil-modo4/gerar` multipla (`16` dezenas, caso `caso_multipla_16_independencia`), `/api/v1/lotofacil-modo4/avaliar`, `/api/v1/lotofacil-modo4/status`, `/api/v1/lotomania-modo4/gerar` e os 4 motores legados em agendamento intercalado.
2. **Determinismo por assinatura canonica de entrada:** saidas sao agrupadas pelo SHA-256 canonico de `(endpoint, metodo, payload completo incluindo semente)`. Nao se exige que sementes diferentes produzam hashes sempre diferentes (convergencia combinatoria legitima); comprova-se repetibilidade estrita para entradas identicas, propagacao de semente, `historico_utilizado=None` e independencia de estado anterior via sequencia `42 -> 43 -> 42 -> 999`.
3. **Lotomania sob carga:** `/api/v1/lotomania-modo4/gerar` passa por agrupamento canonico em todos os patamares, exigindo 100% de repetibilidade de `hash_carteira_sha256_v2_canonico` sob concorrencia.
4. **Memoria via `PeakWorkingSetSize` e amostragem periodica:** thread daemon amostra `WorkingSetSize`, `PeakWorkingSetSize` e `PrivateUsage` a cada `250 ms` durante os patamares, restringindo o escopo ao PID do subprocesso Uvicorn isolado.
5. **Nomenclatura de concorrencia:** `workers_simultaneos` substituido por `clientes_simultaneos`, com `workers=1` explicito na chamada `uvicorn.run(...)`.
6. **Nao interferencia completa dos motores legados:** compara os 4 endpoints legados (`/api/v1/motor-lotofacil`, `/api/v1/motor-lotomania` faixa `1..100`, `/api/v1/motor-diadesorte` faixa `1..31`, `/api/v1/motor-megasena` faixa `1..60`) com flag OFF versus chamadas disparadas simultaneamente durante carga concorrente de Lotofacil MODO 4 ON, validando contratos/faixas, registrando hashes SHA-256 das respostas e dos jogos (exigindo igualdade exata nos deterministicos em baseline como Dia de Sorte) e conferindo hashes SHA-256 em disco dos 23 arquivos `motor_*.py` e `data/*.json` antes e depois.
7. **Preservacao fail-closed da producao (`127.0.0.1:8000`):** captura `/health` e `/api/v1/lotofacil-modo4/status` antes e depois dos ensaios, calculando e comparando o SHA-256 normalizado completo e reprovando automaticamente se a porta `8000` estiver inacessivel ou sofrer qualquer alteracao.

## 4. Calibracao Empirica Registrada (Microcalibracao na Porta Isolada `18080`)

Ensaio executado em `2026-11-13T22:04:24+00:00` (`microcalibracao_fase1.json`), com `0.0%` de erros nas 172 requisicoes totais, pico `PeakWorkingSetSize = 76.91 MB` e delta de `WorkingSetSize = +4.17 MB` entre o baseline (`1` cliente) e a sobrecarga (`24` clientes):

| Patamar (`clientes_simultaneos`) | Rota / Tipo | p95 Medido (s) | p99 Medido (s) | Teto p95 Calibrado (s) | Teto p99 Calibrado (s) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| `patamar_0` (`1` cliente, `20` req) | `/gerar` simples (`15` dez) | `0.1340` | `0.1340` | `0.50` | `0.65` |
| `patamar_0` (`1` cliente) | `/gerar` multipla (`16` dez) | `0.1206` | `0.1206` | `0.50` | `0.65` |
| `patamar_0` (`1` cliente) | `/avaliar` / `/status` | `0.0385` / `0.0366` | `0.0385` / `0.0366` | `0.40` / `0.40` | `0.55` / `0.55` |
| `patamar_0` (`1` cliente) | Lotomania MODO 4 / Legados | `0.0558` / `0.0624` | `0.0558` / `0.0624` | `0.45` / `0.45` | `0.60` / `0.60` |
| `patamar_1` (`8` clientes, `32` req) | `/gerar` simples / multipla16 | `0.6804` / `0.6338` | `0.6804` / `0.6338` | `1.50` / `1.35` | `1.75` / `1.60` |
| `patamar_1` (`8` clientes) | `/avaliar` / `/status` | `0.6080` / `0.5400` | `0.6080` / `0.5400` | `1.35` / `1.15` | `1.60` / `1.40` |
| `patamar_1` (`8` clientes) | Lotomania MODO 4 / Legados | `0.4638` / `0.0692` | `0.4638` / `0.0692` | `1.00` / `0.75` | `1.25` / `0.95` |
| `patamar_2` (`16` clientes, `48` req) | `/gerar` simples / multipla16 | `1.2087` / `1.2543` | `1.2087` / `1.2543` | `2.35` / `2.35` | `2.65` / `2.65` |
| `patamar_2` (`16` clientes) | `/avaliar` / `/status` | `1.1281` / `1.1131` | `1.1281` / `1.1131` | `2.20` / `2.20` | `2.50` / `2.50` |
| `patamar_2` (`16` clientes) | Lotomania MODO 4 / Legados | `0.8251` / `0.3260` | `0.8251` / `0.3260` | `1.60` / `0.75` | `1.85` / `0.95` |
| `patamar_3` (`24` clientes, `72` req) | `/gerar` simples / multipla16 | `1.7405` / `1.7827` | `1.7723` / `1.7827` | `3.25` / `3.25` | `3.60` / `3.60` |
| `patamar_3` (`24` clientes) | `/avaliar` / `/status` | `1.7994` / `1.6339` | `1.7994` / `1.6339` | `3.25` / `3.20` | `3.60` / `3.55` |
| `patamar_3` (`24` clientes) | Lotomania MODO 4 / Legados | `1.0050` / `0.3069` | `1.0050` / `0.3069` | `2.00` / `1.10` | `2.30` / `1.35` |

Justificativa dos ajustes em relacao a v1.0.0: sob Uvicorn `workers=1`, a fila GIL elevava `/status` para `1.6339 s` em `24` clientes (o antigo limite de `0.75 s` reprovaria artificialmente), enquanto `/gerar` operava em `1.7405 s` contra um teto antigo frouxo de `8.0 s` que ocultaria degradacoes de ate 4x. Os novos limiares refletem o comportamento real medido com margem calibrada para jitter de agendamento no Windows.

## 5. Criterios Automaticos de Reprovacao (`NO-GO`)

* Qualquer divergencia criptografica SHA-256 ou falha do selo Ed25519 antes ou depois dos testes.
* Qualquer fallback para algoritmo JavaScript ou motor legado em estado OFF, falha de rede ou erro HTTP.
* Qualquer resposta diferente de `HTTP 503` ou entrega de mais de `0` jogos com flag OFF ou pos-rollback.
* Aceitacao de `experimental_2J` sem habilitacao, `inicializacao_mista="mista_equilibrada"` ou parametro de historico.
* Divergencia numerica superior a `1e-12` contra a referencia AST independente em geracao ou avaliacao.
* Taxa de erro acima de `0.0%`, violacao de `p95` ou `p99` por rota em `1`, `8`, `16` ou `24` clientes simultaneos.
* Estouro de `PeakWorkingSetSize` acima de `1024.0 MB` ou crescimento de `WorkingSetSize` acima de `150.0 MB` no subprocesso Uvicorn `workers=1`.
* Perda de repetibilidade por assinatura canonica de entrada (Lotofacil simples, multipla 16 ou Lotomania) ou dependencia de estado anterior entre sementes.
* Qualquer excecao JavaScript nao capturada ou omissao da clausula matematica obrigatoria no DOM Web/Mobile.
* Violacao de contrato/faixa dos motores legados, alteracao de hash da Lotomania sob carga ou mudanca em `motor_*.py` e `data/*.json` em disco.
* Indisponibilidade da porta `127.0.0.1:8000` ou alteracao entre o estado capturado antes e depois dos ensaios.

## 6. Comandos de Operacao Isolada

```powershell
# Conferencia passiva da Fase 1 Revisada (nao altera porta 8000 nem roda Fase 2)
Set-Location 'C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS'
& 'C:\Users\Luis Brun\AppData\Local\Programs\Python\Python312\python.exe' -m lotofacil_modo4.homologacao_ativacao_runbook --preparacao-check

# Microcalibracao isolada da Revisao da Fase 1 em porta dedicada (nao roda Fase 2)
& 'C:\Users\Luis Brun\AppData\Local\Programs\Python\Python312\python.exe' -m lotofacil_modo4.homologacao_ativacao_runbook --microcalibracao-revisao-fase1

# Execucao da Fase 2 (BLOQUEADA: usar somente apos nova autorizacao expressa)
& 'C:\Users\Luis Brun\AppData\Local\Programs\Python\Python312\python.exe' -m lotofacil_modo4.homologacao_ativacao_runbook --autorizar-homologacao-isolada
```

## 7. Limites Cientificos e Clausula Obrigatoria

> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.
