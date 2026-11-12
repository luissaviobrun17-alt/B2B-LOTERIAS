# PARECER EXTERNO DEFINITIVO
## LOTOMANIA MODO 4 v1.2: Auditoria Técnica da Execução TASK-3438

* **Versão avaliada:** 1.2 (congelada)
* **Execução auditada:** `task-3438` (`execucao_id`: `7b9b2102-82b3-469d-86c1-768c89dab2ea`)
* **Data da execução (UTC):** `2026-11-12T20:45:40.059059+00:00` a `2026-11-12T20:59:14.909156+00:00` (assinatura do manifesto em `2026-11-12T21:00:23.367684+00:00`)
* **Status:** **APROVAÇÃO TÉCNICA COM RESSALVAS METODOLÓGICAS**

Este documento constitui registro complementar e independente aos artefatos originalmente assinados da execução `task-3438`. Adota cinco princípios de encerramento: preservação integral sem alterações dos dois pacotes ZIP originais, registro objetivo das verificações físicas e criptográficas executadas, incorporação expressa das quatro ressalvas sem tentativa de correção retroativa, separação entre aprovação operacional interna e alcance metodológico, e vinculação da autenticação de origem da chave pública à declaração verificável do custodiante.

---

## 1. OBJETO DA AUDITORIA

Este parecer consolida os resultados da auditoria técnica independente do sistema Lotomania MODO 4 v1.2 e de seu pacote de evidências da execução `task-3438`.

O pacote externo examinado foi `ENTREGA_AUDITORIA_EXTERNA_TASK_3438.zip` (`224.602` bytes), cujo hash SHA-256 calculado é:

```text
cb2a100819b5221629a6596924e0b909609e08fd6c871b5cf81b456a830eb608
```

A auditoria abrangeu integridade física, consistência criptográfica, verificações matemáticas, reprodução computacional, auditoria estatística, rastreabilidade e controles negativos de segurança.

| Componente do Pacote Externo | Tamanho (bytes) | SHA-256 Verificado |
| :--- | ---: | :--- |
| `ENTREGA_AUDITORIA_EXTERNA_TASK_3438.zip` (envelope externo) | 224.602 | `cb2a100819b5221629a6596924e0b909609e08fd6c871b5cf81b456a830eb608` |
| `pacote_homologacao_task_3438_modo4_v1_2.zip` (pacote interno, 26 arquivos) | 212.483 | `04b72ed761903d4a7601a41b9eaae5749223e70cbb0cf632866928e01b9930bd` |
| `RELATORIO_AUDITORIA_FINAL_MODO4_V1_2.md` | 14.648 | `06919c492dbf4ac17cc9f0f137ab17c8b17beec0d8c9366598230d4be71d9335` |
| `task-3438.log` | 9.935 | `a4800ca2351418e775c350893c103c5c3b518c9e4a5a3374e049c6c566141f21` |
| `manifesto_evidencia_execucao_modo4.json` (bytes em disco) | 5.639 | `8ca5eea07c2b5ad20511119aed504ed2426d9f24e81cbc02a7d4229595526a48` |
| `manifesto_evidencia_execucao_modo4.sig` | 130 | `f6cfb00feffdc1a1caaf2aae9b8e31960b4d2b66051edacdf1ed18bf7356a52b` |
| `chave_publica_modo4.pem` | 113 | `d810ed9f31f476b159590cd2e053632dc32e8e6e62a5a17f7c2f371a45084b0f` |

---

## 2. INTEGRIDADE FÍSICA E CRIPTOGRÁFICA

Foi confirmada a correspondência exata do SHA-256 do pacote externo com o fingerprint declarado, com teste estrutural ZIP sem erros (`testzip() == None`). O pacote interno `pacote_homologacao_task_3438_modo4_v1_2.zip` apresentou `26` artefatos, igualmente íntegros do ponto de vista estrutural.

Foram verificados diretamente sobre os arquivos:

* Assinatura Ed25519 do manifesto (`manifesto_evidencia_execucao_modo4.sig`) sobre a serialização canônica de `manifesto_evidencia_execucao_modo4.json` (`5.026` bytes UTF-8 sem espaços redundantes, SHA-256 canônico `46241c038ce08cf9aa311ca9db415ebc68380722ed60421000205c10df44d64e`).
* Esquema de relatório `1.2.2` em `relatorio_matriz_modo4.json` (`67fa82b7c905a4bda18d6802950188d79b47680d7fac8fa88393019d010b7a81`).
* Correspondência integral dos hashes dos `22` arquivos-fonte, dados, verificadores e testes inventariados no manifesto.
* Ausência de arquivos adicionais não autorizados (`--strict-dir` aprovado).
* Ausência de qualquer chave privada (`.key`) nos dois pacotes ZIP distribuídos.

A assinatura Ed25519 foi validada matematicamente em relação à chave pública fornecida (`chave_publica_modo4.pem`, payload Base64 `MCowBQYDK2VwAyEAPPFCkzbtBh3n01JK9JwxMmA9aHwZpozdK++EudJ1WLA=`), cujo fingerprint SHA-256 é:

```text
d810ed9f31f476b159590cd2e053632dc32e8e6e62a5a17f7c2f371a45084b0f
```

Permanece necessária a autenticação externa formal da origem da chave pública, por confronto com registro independente e assinatura do termo de custódia histórica pelo responsável detentor da chave privada, tratado em documento separado (`DECLARACAO_CUSTODIA_CHAVE_PUBLICA_MODO4_V1_2.md`).

---

## 3. VALIDAÇÃO COMPUTACIONAL E PRNG

A execução independente do verificador (`verificar_evidencia_independente.py`, SHA-256 `2dfc9a3ed1ff45b5661323ed16dc69275d97769fc39d92f75f80c5045a080999`) sob `python -O` e opção `--strict-dir` foi aprovada com código de saída `0` (`verificacao_independente_aprovada: true`, `erros: []`). Os `10` cenários negativos de adulteração foram integralmente rejeitados de forma fail-closed.

A reconstrução registrada para `J=10.000` (com `seed=330001`, onde o bilhete espelho `j2` é estruturalmente inválido por conter `8` dezenas na coluna `0` e o processo guloso inicia em `idx_inicio_greedy=1`) documentou:

* `9.999` estágios gulosos verificados (`19` estágios e `1.520` candidatos no confronto contra o trace interno de `J=20`).
* `799.920` candidatos avaliados em `J=10.000`.
* `0` desvios (`deriva_prng_ao_longo_de_10000_jogos: 0`), com presença de todos os vencedores nos `80` candidatos por etapa.

A classificação técnica adotada para essa etapa é **REPRODUÇÃO CRUZADA COM INDEPENDÊNCIA PARCIAL**. Essa classificação decorre do compartilhamento da primitiva `random.Random` do Python, dos filtros estruturais de amostragem e de parte da lógica de inicialização do motor de referência. Não se declara independência computacional integral dessa reconstrução.

---

## 4. EQUIVALÊNCIA E ESCOPO DE COMPROVAÇÃO

A equivalência integral direta bit a bit contra o motor de referência `MotorLotomaniaB2B` foi documentada para os nove tamanhos `J=1, 2, 10, 20, 50, 80, 100, 500` e `1.000`.

Para `J=5.000` e `J=10.000`, conforme registrado no próprio relatório `relatorio_matriz_modo4.json` (`classificacao_tres_niveis_equivalencia.comparacao_integral_direta: false`, `auditoria_amostral: "primaria_alto_volume"`), a evidência combina:

* Invariância exata do prefixo `J=1.000` contra o motor de referência.
* Verificação algébrica integral pelo teorema de contagem dupla nas `12.497.500` (`J=5.000`) e `49.995.000` (`J=10.000`) interseções par a par.
* Ausência de deriva do PRNG ao longo dos `9.999` estágios gulosos.
* Auditoria amostral de `2.160` candidatos (`560` candidatos comparados na camada base e `1.600` candidatos reais na auditoria de trajetória sob `seed=330001`, distribuídos em `20` estágios reais incluindo `M_sel=4.999` e `M_sel=9.999`).

Consequentemente, não se declara equivalência integral direta de execução completa do motor de referência para `J=5.000` e `J=10.000`. Essa delimitação deve acompanhar qualquer divulgação técnica dos resultados.

---

## 5. AUDITORIA ESTATÍSTICA

Foram examinados diretamente os dados brutos de `90` rodadas em `dados_brutos_90_saldos_consolidados.json`, divididos em `30` rodadas exploratórias (Bateria 1, `Goo100`, saldo `10.150`) e `60` rodadas distribuídas nas Baterias 2, 3 e 4 (`20` rodadas cada, declaradas como executadas sob parâmetros congelados).

O recálculo independente sobre as `60` rodadas confirmou exatamente os valores apresentados no relatório:

* Saldo acumulado (`sum`): `18.507`
* Saldo médio (`mean`): `308,45`
* Desvio-padrão amostral (`sd`, n-1): `157,182117`
* Estatística `t` (`gl = 59`): `15,200479`
* Valor-p bilateral: `4,562890 × 10⁻²²`

Os resultados são integralmente reproduzíveis a partir dos registros fornecidos. Entretanto, não foi apresentada prova temporal criptográfica anterior à execução das baterias (como protocolo pré-registrado assinado e ancorado em carimbo do tempo verificável por terceiros) que comprove de forma autônoma a pré-especificação dos parâmetros. Essa limitação histórica é permanente para a build `v1.2` e não pode ser sanada retroativamente; eventual validação confirmatória futura deverá adotar pré-registro assinado e temporalmente verificável antes da coleta de novas rodadas.

---

## 6. RESSALVAS FORMAIS

Ficam formalmente estabelecidas quatro ressalvas vinculantes:

### 6.1. Autenticação da chave pública

A assinatura Ed25519 foi validada matematicamente em relação a `chave_publica_modo4.pem` (`d810ed9f31f476b159590cd2e053632dc32e8e6e62a5a17f7c2f371a45084b0f`). A autenticação institucional e de origem dessa chave pública permanece condicionada à formalização assinada pelo custodiante no documento complementar `DECLARACAO_CUSTODIA_CHAVE_PUBLICA_MODO4_V1_2.md`, sem exposição de bytes da chave privada.

### 6.2. Pré-especificação estatística

A ausência de prova temporal criptográfica anterior à execução das `60` rodadas confirmatórias constitui limitação histórica permanente da versão `1.2`.

### 6.3. Independência parcial do PRNG

A reconstrução dos `9.999` estágios gulosos e `799.920` candidatos constitui reprodução cruzada com independência parcial, não validação computacional totalmente independente de implementação e gerador.

### 6.4. Equivalência em grandes carteiras

A equivalência integral direta comprovada contra o motor de referência limita-se a `J=1.000`. Para `J=5.000` e `J=10.000`, aplica-se exclusivamente a classificação de evidência combinada descrita na Seção 4.

---

## 7. DECISÃO E CONCLUSÃO

Com base nas verificações físicas, criptográficas, computacionais e estatísticas realizadas, conclui-se que o pacote de evidências da execução `task-3438` apresenta integridade física, consistência criptográfica interna, rastreabilidade completa e reprodutibilidade numérica dos resultados documentados.

A execução operacional interna da versão `1.2` encontra-se **aprovada**, sendo concedida a **aprovação técnica com as quatro ressalvas metodológicas** expressamente registradas neste parecer. Esta decisão não equivale a certificação universal de desempenho estatístico nem elimina as limitações históricas e computacionais identificadas.

Encaminhamento recomendado para encerramento documental da versão `1.2`:

1. Preservar integralmente e sem alterações os pacotes ZIP originais (`ENTREGA_AUDITORIA_EXTERNA_TASK_3438.zip`, `pacote_homologacao_task_3438_modo4_v1_2.zip` e a referência histórica `pacote_homologacao_task_3057_modo4_v1_2.zip`).
2. Encerrar tecnicamente modificações de código ou reemissões de evidência na build `v1.2`.
3. Manter este parecer em arquivo separado, anexado apenas como documento complementar de auditoria.
4. Formalizar a autenticação de origem da chave pública mediante preenchimento e assinatura do custodiante em `DECLARACAO_CUSTODIA_CHAVE_PUBLICA_MODO4_V1_2.md`.
5. Exigir pré-registro criptograficamente assinado com âncora temporal anterior ao início de qualquer bateria confirmatória futura.

---

## CLÁUSULA MATEMÁTICA OBRIGATÓRIA

> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.

Documento complementar aos artefatos congelados da execução `task-3438`. Este parecer não modifica, substitui ou reemite qualquer arquivo originalmente assinado.
