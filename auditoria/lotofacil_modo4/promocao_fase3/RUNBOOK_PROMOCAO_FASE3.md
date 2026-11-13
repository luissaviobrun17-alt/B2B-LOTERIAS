# RUNBOOK DE PREPARACAO AUDITAVEL DA FASE 3 - LOTOFACIL MODO 4

**Versao Alvo de Promocao:** `5.1.0-promocao-controlada`  
**Versao da Preparacao Fase 3:** `1.0.0-fase3-preparacao`  
**Diretorio de Controle:** `auditoria/lotofacil_modo4/promocao_fase3`  
**Branch Autorizada:** `feat/lotomania-modo4-jobs-mobile` (proibido merge em `main` sem autorizacao especifica)  
**Estado de Governanca:** `FASE_3_PREPARADA_AGUARDANDO_AUTORIZACAO_PRODUCAO` | **Porta `8000`:** `LOTOFACIL_MODO4_ATIVO=False`

## 1. Escopo Desta Preparacao e Travas de Seguranca

Esta entrega cria exclusivamente a preparacao auditavel, o checklist executavel, os controles de contingencia, a configuracao e os testes unitarios da Fase 3. A execucao da Fase 3 permanece **estritamente bloqueada** (`exit code 2` por padrao), preservando a porta `8000` inalterada em estado `OFF`, todos os motores matematicos e os sete arquivos selados intactos e sem merge em `main`.

## 2. Incorporacao das Regras, Cinco Exigencias e Tres Definicoes Operacionais

| Controle | Implementacao Obrigatoria no Executor da Fase 3 |
| :--- | :--- |
| Regras Base (1 a 9) | Ativar somente `LOTOFACIL_MODO4_ATIVO=true`; preservar motores e 7 arquivos selados; manter `experimental_2J=False`, `conservadora_3J` e `padrao`; monitorar, comprovar rollback, publicar no GitHub e nao fazer merge em `main`. |
| Exigencia 1: Snapshot Anterior | Capturar PID ouvinte da porta `8000`, memoria Win32, versao, variaveis da allowlist, `/health`, `/api/v1/lotofacil-modo4/status`, hashes SHA-256 dos 7 arquivos selados e respostas de referencia dos endpoints legados e da Lotomania MODO 4 antes do reinicio. |
| Exigencia 2: Integridade Posterior | Recalcular os SHA-256 dos 7 arquivos selados e verificar a cadeia criptografica completa imediatamente apos o processo subir; qualquer divergencia interrompe a Fase 3 na hora. |
| Exigencia 3: Teste Controlado | Executar primeiro uma geracao pequena controlada (`3` jogos simples, `conservadora_3J`, semente `42`), conferir contrato, `diff <= 1e-12`, `historico_utilizado=null` e clausula obrigatoria; somente apos validacao integral rodar `/avaliar` e cenarios negativos `HTTP 422`. |
| Exigencia 4: Monitoramento | Verificar zero erros HTTP inesperados, latencia dentro do teto (`<= 3.0 s` no teste controlado), `PeakWorkingSetSize <= 1024.0 MB`, contadores de `telemetria` coerentes em `/status` e operacao normal (`HTTP 200`) dos 4 motores legados e da Lotomania MODO 4. |
| Exigencia 5: Rollback Comprovado | Alternar a porta `8000` para `LOTOFACIL_MODO4_ATIVO=False` e comprovar `HTTP 503` com `0` jogos e `fallback_executado=false` em `/gerar` e `/avaliar`, mantendo legados e Lotomania operacionais. |
| Definicao 1: Allowlist de Ambiente | Registrar apenas as chaves explicitas `LOTOFACIL_MODO4_ATIVO`, `LOTOFACIL_MODO4_PERMITIR_EXPERIMENTAL_2J` e `LOTOFACIL_MODO4_POLITICA_MICRO`, omitindo quaisquer segredos ou variaveis do sistema operacional (gravando somente a contagem numerica omitida). |
| Definicao 2: Ordem Pos-Rollback Explicita | A execucao futura exige parametro explicito `--pos-rollback-modo` (`encerrar_em_off_standby` ou `reativar_on_com_revalidacao`). Sem essa escolha explicita e token de confirmacao humana, a execucao falha fechada (`codigo 2`). |
| Definicao 3: Contingencia no Reinicio | Se houver falha de subida ou erro funcional com selo integro, abortar a Fase 3 e restaurar imediatamente a porta `8000` em `LOTOFACIL_MODO4_ATIVO=False` validando legados e Lotomania; se houver divergencia em qualquer dos 7 arquivos selados, abortar fail-closed sem mascaramento e preservar evidencias forenses. |

## 3. Sequencia Ordenada Quando a Fase 3 For Expressamente Autorizada

1. **Etapa 1 (Pre-requisitos e Snapshot Anterior):** confirmar Ata `GO` da Fase 2, 7 arquivos selados integros e capturar snapshot completo antes do reinicio na porta `8000`.
2. **Etapa 2 (Reinicio Controlado ON e Integridade Posterior):** subir processo `uvicorn` (`workers=1`) na porta `8000` com `LOTOFACIL_MODO4_ATIVO=true`, `LOTOFACIL_MODO4_PERMITIR_EXPERIMENTAL_2J=false` e `LOTOFACIL_MODO4_POLITICA_MICRO=conservadora_3J`, recalculando os 7 SHA-256 imediatamente.
3. **Etapa 3 (Teste Controlado Escalonado):** validar primeiro carteira de `3` jogos; apenas se aprovada, executar `/avaliar` e cenarios negativos `HTTP 422`.
4. **Etapa 4 (Monitoramento):** auditar memoria (`PeakWorkingSetSize`), latencias, telemetria em `/status`, 4 rotas legadas e Lotomania MODO 4.
5. **Etapa 5 (Rollback Comprovado):** reiniciar em `LOTOFACIL_MODO4_ATIVO=false` e comprovar `HTTP 503` e zero jogos.
6. **Etapa 6 (Estado Final Explicito):** executar exatamente o `--pos-rollback-modo` autorizado (`encerrar_em_off_standby` ou `reativar_on_com_revalidacao`), emitir `ata_promocao_fase3.json`, `evidencias_promocao_fase3.json` e `DOSSIE_PROMOCAO_FASE3.md`.

## 4. Criterios Obrigatorios de Interrupcao Imediata

* Falha ao encerrar ou subir o processo `uvicorn` na porta `8000` dentro do tempo limite configurado.
* Qualquer divergencia SHA-256 nos sete arquivos selados (`promocao_producao.py`, `api.py`, `motor_lotofacil.py`, `motor_lotofacil_modo4_engine.js`, `index.html`, `js/ui.js`, `B2B_Loterias_Mobile.html`) ou falha do selo Ed25519 da Lotomania.
* Qualquer desvio em `experimental_2J=False`, `politica_micro="conservadora_3J"` ou `inicializacao_mista="padrao"`.
* Falha no teste controlado de `3` jogos, divergencia numerica acima de `1e-12` contra referencia AST independente ou aceitacao de payload proibido.
* Qualquer erro HTTP inesperado, regressao nos quatro motores legados ou na Lotomania MODO 4, ou estouro de `PeakWorkingSetSize > 1024.0 MB`.
* Resposta diferente de `HTTP 503` ou retorno de jogos apos rollback para `LOTOFACIL_MODO4_ATIVO=False`.

## 5. Comandos Disponiveis

```powershell
Set-Location 'C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS'

# 1. Conferencia passiva da Preparacao da Fase 3 (nao altera nem reinicia a porta 8000)
& 'C:\Users\Luis Brun\AppData\Local\Programs\Python\Python312\python.exe' -m lotofacil_modo4.promocao_fase3_runbook --preparacao-check

# 2. Captura de snapshot somente-leitura da porta 8000 com allowlist (nao altera nem reinicia)
& 'C:\Users\Luis Brun\AppData\Local\Programs\Python\Python312\python.exe' -m lotofacil_modo4.promocao_fase3_runbook --snapshot-somente-leitura

# 3. Execucao da Fase 3 (BLOQUEADA nesta etapa; exige autorizacao formal expressa)
# & 'C:\Users\Luis Brun\AppData\Local\Programs\Python\Python312\python.exe' -m lotofacil_modo4.promocao_fase3_runbook --autorizar-execucao-fase3 --confirmacao-humana-fase3 AUTORIZADO_PRODUCAO_PORTA_8000 --pos-rollback-modo <encerrar_em_off_standby|reativar_on_com_revalidacao>
```

## 6. Limites Cientificos e Clausula Obrigatoria

> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.
