# RUNBOOK DE HOMOLOGACAO ESPECIFICA DE ATIVACAO - LOTOFACIL MODO 4

**Versao Alvo:** `5.1.0-promocao-controlada`  
**Versao do Runbook:** `1.0.0-fase1-preparacao`  
**Diretorio de Saida Isolado:** `auditoria/lotofacil_modo4/homologacao_ativacao`  
**Estado Vigente na Preparacao:** `LOTOFACIL_MODO4_ATIVO=False`, `LOTOFACIL_MODO4_PERMITIR_EXPERIMENTAL_2J=False`, `politica_micro="conservadora_3J"`, `inicializacao_mista="padrao"`  

## 1. Modelo de Governanca em Tres Fases

1. **Fase 1 (Preparacao):** elaboracao deste Runbook, da configuracao declarativa (`config_homologacao_ativacao.json`), do executor isolado (`lotofacil_modo4/homologacao_ativacao_runbook.py`) e do levantamento somente-leitura de hardware, sem alteracao dos 7 arquivos selados e sem execucao da homologacao.
2. **Fase 2 (Homologacao Isolada):** mediante autorizacao expressa apos revisao destes criterios, execucao automatizada e reproduzivel das 6 frentes em portas dedicadas (`18080` API isolada e `18081` UI estatica isolada), preservando integralmente o servico de producao (`127.0.0.1:8000`) e os manifestos originais.
3. **Fase 3 (Ativacao em Producao):** somente apos emissao da Ata `GO` da Fase 2 e mediante nova deliberacao expressa para configurar `LOTOFACIL_MODO4_ATIVO=true`, mantendo `experimental_2J` desabilitada por padrao.

## 2. Capacidade Real de Hardware Levantada (Somente-Leitura)

| Recurso Medido | Valor Observado no Host | Impacto na Calibracao de Carga |
| :--- | :--- | :--- |
| CPU | AMD Ryzen 7 255 (8 nucleos fisicos, 16 threads logicas, clock max. `3801 MHz`) | Calibra patamares em `8`, `16` e `24` workers simultaneos |
| Memoria RAM | `29.79 GB` total; `16.07 GB` livre (`46%` uso base) | Fixa teto absoluto de processo Uvicorn em `1024.0 MB` e delta de crescimento em `150.0 MB` |
| Armazenamento | `803.21 GB` livre | Folga ampla para evidencias JSON/Markdown isoladas |
| Runtime API | Windows 11 (`AMD64`), Python `3.12.10`, FastAPI + Uvicorn (`workers=1`, AnyIO/GIL) | Latencias p95 dimensionadas para fila de threads em processo Python unico |
| Automacao Browser | `chrome.exe` + `msedge.exe` instalados; sem `playwright`/`selenium`/`psutil` | Auditoria em navegador real via Chrome headless + CDP WebSocket em stdlib pura |

## 3. Frentes de Verificacao e Criterios Objetivos de Go/No-Go

| Frente | Escopo Isolado | Limiar Objetivo de Aprovacao (`GO`) |
| :--- | :--- | :--- |
| 1. Auditoria Criptografica | Etapas 1 a 5 (`20` + `4` modulos), selo Ed25519 Lotomania e 7 arquivos de `manifesto_promocao_controlada.json` | `0` divergencias antes da janela e `0` divergencias apos rollback; manifestos originais intactos |
| 2. Rotas e Contratos | `/status`, `/gerar` e `/avaliar` em OFF, ON (`15` e `16` dezenas) e entradas proibidas | OFF: `HTTP 503` com `0` jogos; ON: `HTTP 200`, diff AST `<= 1e-12`; proibidos: `HTTP 422` (`experimental_2J`, `mista_equilibrada`, `historico`, conflito `pool`/`bloqueadas`) |
| 3. Carga Escalonada (Subprocesso Dedicado) | Patamar 1 (`8` workers, `16` req `/gerar`), Patamar 2 (`16` workers, `32` req `/gerar`), Patamar 3 (`24` workers, `60` req mistas) | Erro inesperado `0.0%`; timeout `30.0s`; p95 `<= 2.5s` (P1), `<= 5.0s` (P2), `<= 8.0s` `/gerar` e `<= 0.75s` `/status` (P3); `1` unico hash por seed; RSS `<= 1024 MB` e delta P1 para P3 `<= 150 MB` |
| 4. Navegador Real Web e Mobile | `index.html` e `B2B_Loterias_Mobile.html` em Chrome headless (redirecionamento em memoria de `8000` para porta isolada) | `0` excecoes JS nao tratadas; subpainel oculto ao carregar; `check-exp2j` desabilitada; OFF exibe alerta e `0` jogos (sem fallback); ON renderiza jogos, auditoria e clausula |
| 5. Nao Interferencia | Lotomania MODO 4 + 4 motores legados sob carga paralela com flag ON | Todos legados `HTTP 200`; `hash_carteira_sha256_v2_canonico` da Lotomania identico entre OFF e ON |
| 6. Rollback e Preservacao | Transicao `ON -> OFF` em runtime + reinicio de subprocesso em OFF + conferencia da porta `8000` | Primeira chamada pos-rollback em `HTTP 503` com `0` jogos; producao `127.0.0.1:8000` mantida intacta com `disponivel=false` |

## 4. Criterios Automaticos de Reprovacao (`NO-GO`)

Qualquer ocorrencia abaixo reprova a homologacao imediatamente e bloqueia a Fase 3:

* Qualquer divergencia criptografica SHA-256 ou falha do selo Ed25519 antes ou depois dos testes.
* Qualquer fallback para algoritmo JavaScript ou motor legado em estado OFF, falha de rede ou erro HTTP.
* Qualquer resposta diferente de `HTTP 503` ou quantidade de jogos maior que `0` com a flag desativada ou apos rollback.
* Aceitacao de `experimental_2J` por padrao, `inicializacao_mista="mista_equilibrada"` ou parametro de historico.
* Divergencia numerica superior a `1e-12` contra a referencia AST independente em geracao ou avaliacao.
* Taxa de erro acima de `0.0%`, violacao dos tetos de latencia p95/p99, estouro de RSS acima de `1024 MB`, crescimento acima de `150 MB` ou perda de determinismo sob concorrencia.
* Qualquer excecao JavaScript nao capturada ou omissao da clausula matematica obrigatoria no DOM Web/Mobile.
* Alteracao do estado ou hash de saida da Lotomania MODO 4 ou indisponibilidade dos motores legados.
* Modificacao detectada no servico de producao (`127.0.0.1:8000`) durante ou apos a janela isolada.

## 5. Procedimento de Execucao (Somente apos Autorizacao da Fase 2)

O executor `lotofacil_modo4/homologacao_ativacao_runbook.py` possui trava de seguranca fail-closed e exige o argumento `--autorizar-homologacao-isolada` para iniciar a Fase 2. Na Fase 1, permite apenas verificacao estatica via `--preparacao-check`.

```powershell
# Conferencia passiva de preparacao (permitida antes da Fase 2)
Set-Location 'C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS'
& 'C:\Users\Luis Brun\AppData\Local\Programs\Python\Python312\python.exe' -m lotofacil_modo4.homologacao_ativacao_runbook --preparacao-check

# Execucao da Fase 2 (SOMENTE apos autorizacao expressa da Homologacao Isolada)
& 'C:\Users\Luis Brun\AppData\Local\Programs\Python\Python312\python.exe' -m lotofacil_modo4.homologacao_ativacao_runbook --autorizar-homologacao-isolada

# Sondagem do servico de producao antes e depois da janela (URLs em texto simples)
Invoke-RestMethod -Uri 'http://127.0.0.1:8000/health' |
    ConvertTo-Json -Depth 6

Invoke-RestMethod -Uri 'http://127.0.0.1:8000/api/v1/lotofacil-modo4/status' |
    ConvertTo-Json -Depth 6
```

## 6. Limites Cientificos e Clausula Obrigatoria

> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.
