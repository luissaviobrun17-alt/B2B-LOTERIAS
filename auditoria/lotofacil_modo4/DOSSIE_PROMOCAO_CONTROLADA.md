# DOSSIE DE PROMOCAO CONTROLADA - LOTOFACIL MODO 4

**Versao da Promocao:** `5.1.0-promocao-controlada`  
**Data/Hora (UTC):** `2026-11-13T18:04:31.405080+00:00`  
**Estado Padrao em Producao:** `lotofacil_modo4_ativo = false` (DESLIGADO POR PADRAO)  
**Politica Micro Padrao:** `conservadora_3J` (`experimental_2J` configuravel, desabilitada por padrao)  
**Inicializacao Mista:** `padrao` (travada; `mista_equilibrada` rejeitada com HTTP 422)  

## 1. Resumo Executivo da Promocao

A integracao do motor LOTOFACIL MODO 4 foi implantada em `api.py`, na interface Web (`index.html`, `js/engines/motor_lotofacil_modo4_engine.js`, `js/ui.js`) e na interface Mobile (`B2B_Loterias_Mobile.html`) sob controle estrito de feature flag desligada por padrao (`LOTOFACIL_MODO4_ATIVO=false`). Todos os artefatos congelados das Etapas 1 a 4, os arquivos selados da Etapa 5, as bases oficiais da CAIXA, o motor legado `motor_lotofacil.py` e o sistema Lotomania MODO 4 v1.2 com selo Ed25519 permaneceram integralmente preservados e validados por SHA-256 antes e depois dos testes.

## 2. Configuracao de Feature Flag e Politicas em Producao

| Parametro / Regra | Valor Padrao em Producao | Mecanismo de Controle | Comportamento Fail-Closed |
| :--- | :--- | :--- | :--- |
| Feature Flag Principal (`LOTOFACIL_MODO4_ATIVO`) | `False` | Variavel de ambiente explicita ou runtime controlado | HTTP 503 com 0 jogos e zero fallback |
| Politica Micro Oficial (`LOTOFACIL_MODO4_POLITICA_MICRO`) | `conservadora_3J` | Fixada como padrao da API, Web e Mobile | `experimental_2J` bloqueada se flag experimental OFF |
| Habilitacao Experimental (`LOTOFACIL_MODO4_PERMITIR_EXPERIMENTAL_2J`) | `False` | Opt-in restrito desmarcado e desabilitado por padrao | Requisicao com `experimental_2J` recebe HTTP 422 com 0 jogos |
| Inicializacao Mista | `padrao` | Literal estrito Pydantic v2 e ConfigProducao | Rejeita `mista_equilibrada` com HTTP 422 |
| Historico na Geracao | `None` | Schema `extra='forbid'` sem campo de historico | Rejeita payload com `historico` via HTTP 422 |

## 3. Preservacao Criptografica e Hashes SHA-256 Pos-Implantacao

A verificacao criptografica pos-implantacao confirmou `20` artefatos das Etapas 1 a 3, `4` artefatos da Etapa 4, bases externas e selo Ed25519 da Lotomania (`selo_lotomania_valido=True`), manifesto Etapa 5 presente (`True`) e `7` modulos de producao selados no manifesto da promocao sem nenhuma divergencia (`integro=True`). Auditoria AST da referencia independente confirmou `independencia_comprovada=True`.

| Arquivo Monitorado em Producao | SHA-256 Pos-Implantacao | Papel |
| :--- | :--- | :--- |
| `lotofacil_modo4/promocao_producao.py` | `5bc19c7e8313f0042afd7414373de334ddb6832350789c1c026aca3996a66996` | Integracao controlada de promocao |
| `api.py` | `fce9c08bdb6344612d6e35a799f51e9371fff09d0ce7917f503fc8a1e0003387` | Integracao controlada de promocao |
| `motor_lotofacil.py` | `7dcaf017f8a4845fe42f5a58cb978c81e95e8f55b96ef558b9a0ec551ba077c3` | Preservado inalterado (baseline legado) |
| `js/engines/motor_lotofacil_modo4_engine.js` | `943b4bba0a6928dfc9402c6f5f57598a7820302b4faaa3a10c48528a11231413` | Integracao controlada de promocao |
| `index.html` | `53065882b7adf6aca8807faad0b76e80bc4e3dc7f003c368dc6bb2d0bfb1e91d` | Integracao controlada de promocao |
| `js/ui.js` | `814e795daa55249ce302308bd2277f373ea8f263b80862b247570a5fad85d4c8` | Integracao controlada de promocao |
| `B2B_Loterias_Mobile.html` | `c57b6f73b26098af3bb82201f46b75a8008a78a63dd2d3fbf9d4e11b8abb2c8c` | Integracao controlada de promocao |

## 4. Matriz de Evidencias de Implantacao (Itens V.1 a V.8)

| Check | Cenario Testado | Resultado Observado | Evidencia Chave |
| :--- | :--- | :--- | :--- |
| Feature Flag OFF (Padrao) | `GET /health`, `POST /gerar`, `POST /avaliar` com flag `False` | Aprovado (Fail-Closed) | `disponivel=False`, HTTP `503`, `0` jogos, `fallback_executado=False` |
| Ativacao Controlada ON (`conservadora_3J`) | 8 jogos de 15 dezenas (seed 42) + 4 jogos de 16 dezenas (Independencia) | Aprovado | `politica_micro_utilizada=conservadora_3J`, diff F = `1.11e-16`, diff F (16 dez.) = `0.00e+00` |
| Politica `experimental_2J` Configuravel | Bloqueada por padrao; ativa somente com `permitir_experimental_2j=True` | Aprovado | Bloqueio padrao HTTP `422`; com opt-in ON diff F = `1.11e-16` |
| Rollback em Runtime | Transicao `ON -> OFF` sem reiniciar processo | Aprovado | Primeira chamada pos-rollback retornou HTTP `503`, `0` jogos, `disponivel=False` |
| Concorrencia Multi-Requisicao | 12 chamadas simultaneas (6 workers) nos estados OFF e ON | Aprovado | OFF: `12/12` em `0.2231s`; ON: `12/12` em `0.4166s` |
| Nao Interferencia Entre Modalidades | Lotomania MODO 4 + legados (Lotofacil, Lotomania, Dia de Sorte, Mega-Sena) | Aprovado | Lotomania SHA identico flag OFF/ON (`True`); todos os endpoints legados HTTP 200 |

## 5. Limites Cientificos e Clausula Matematica Obrigatoria

> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.

Na aposta simples de 15 dezenas, a probabilidade individual permanece rigorosamente fixa em `1 em 3.268.760` para 15 acertos e `346.126 / 3.268.760` (aprox. `10,5889%`) para alguma premiacao (11 a 15 acertos). As cotas de Dawson-Sankoff e Hunter-Worsley, bem como `S_prob` e `F_MODO4`, funcionam exclusivamente como metricas e limites de otimizacao combinatoria de carteiras, sem prometer previsao ou alteracao de chances individuais.

## 6. Posicao Final para Go/No-Go

A implantacao controlada em `api.py`, Web e Mobile encontra-se concluida, selada por manifesto SHA-256 e com `lotofacil_modo4_ativo = False` por padrao. Recomenda-se manter a feature flag desligada ate autorizacao formal de ativacao em janela assistida (`LOTOFACIL_MODO4_ATIVO=true`), preservando `experimental_2J` desabilitada por padrao.
