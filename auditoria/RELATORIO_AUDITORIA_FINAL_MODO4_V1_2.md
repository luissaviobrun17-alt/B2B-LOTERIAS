# Relatório Consolidado de Auditoria e Evidências Finais: Lotomania MODO 4 v1.2 (`task-3438`)

**Cláusula Matemática Obrigatória:**
O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.

---

## 1. Resumo da Execução `task-3438` (`python -O`) e Encerramento da Cadeia

- **Identificador da execução (`execucao_id`):** `7b9b2102-82b3-469d-86c1-768c89dab2ea`
- **Modo de execução:** `python -O` (Python `3.12.10` no Windows 11, com `assert` e `__debug__` desativados pela flag `-O` e substituídos por validações explícitas `exigir()` / `RuntimeError`)
- **Início global UTC:** `2026-11-12T20:45:01.004892+00:00`
- **Fim global UTC:** `2026-11-12T20:59:15.631600+00:00`
- **Código de saída do processo:** `0` (`7/7` etapas concluídas em [task-3438.log](file:///C:/Users/Luis%20Brun/.gemini/antigravity/brain/f3af3942-aca3-4c9a-a3dd-e56f90feb848/task-3438.log))
- **Validação adicional em modo padrão pós-edição (`task-3473`):** `Ran 28 tests in 18.300s -> OK` (20 testes centrais + `test_modo4_selo` + `test_modo4_sem_fallback` + `test_modo4_equivalencia`) e saída `0` do verificador independente `--strict-dir` sobre o ZIP descompactado
- **Auditoria estática AST (pré-execução sobre os 22 arquivos Python de trabalho e testes):** `0` instruções `assert`, `0` referências a `__debug__`
- **Ocorrência intermediária relevante (`task-3345`):** a tentativa imediatamente anterior em `python -O` terminou com código de saída `1` em `test_modo4_matriz_carteiras.py` (`Esperado 9998 estágios gulosos, obtido 9999`), demonstrando funcionamento ativo do bloqueio fail-closed sob `-O`. A causa raiz verificada decorreu de o bilhete espelho `j2` na `seed=330001` falhar na regra de equilíbrio de colunas (`8 > 7`), levando a busca gulosa a iniciar no índice `1` (`9.999` estágios em `J=10.000` e `19` em `J=20`).

### 1.1. Detalhamento dos Artefatos Criptográficos Pós-Fechamento

A assinatura Ed25519 do manifesto de evidência foi realizada **após** o encerramento do processo `task-3438` e fechamento definitivo do arquivo [task-3438.log](file:///C:/Users/Luis%20Brun/.gemini/antigravity/brain/f3af3942-aca3-4c9a-a3dd-e56f90feb848/task-3438.log) (`timestamp_assinatura_manifesto_utc = 2026-11-12T21:00:23.367684+00:00`), mantendo a chave privada estritamente local fora dos diretórios distribuíveis.

| Artefato | Tamanho em Disco (Bytes) | SHA-256 dos Bytes em Disco | Bytes Canônicos Assinados | SHA-256 Canônico Assinado (UTF-8) | SHA-256 do `.sig` |
| :--- | :---: | :--- | :---: | :--- | :--- |
| [manifesto_modo4.json](file:///C:/Users/Luis%20Brun/.gemini/antigravity/brain/f3af3942-aca3-4c9a-a3dd-e56f90feb848/manifesto_modo4.json) (Selo do Motor) | `2.554` | `66e255cd526e2c72ec1fda3d3112cb918b4e678b1f264117593ca7cdf127e57c` | `2.280` | `ae7a38f2b80bb07a7b145c570a26d1bc5cd104216b11a785d30f3e28f169fcc2` | `21e43c7fd670fed1d384bad98344c7daf7f3f1c6fd5405f0dceb64f55fbd453f` |
| [manifesto_evidencia_execucao_modo4.json](file:///C:/Users/Luis%20Brun/.gemini/antigravity/brain/f3af3942-aca3-4c9a-a3dd-e56f90feb848/manifesto_evidencia_execucao_modo4.json) (Final pós-log) | `5.639` | `8ca5eea07c2b5ad20511119aed504ed2426d9f24e81cbc02a7d4229595526a48` | `5.026` | `46241c038ce08cf9aa311ca9db415ebc68380722ed60421000205c10df44d64e` | `f6cfb00feffdc1a1caaf2aae9b8e31960b4d2b66051edacdf1ed18bf7356a52b` |
| [task-3438.log](file:///C:/Users/Luis%20Brun/.gemini/antigravity/brain/f3af3942-aca3-4c9a-a3dd-e56f90feb848/task-3438.log) | `9.935` | `a4800ca2351418e775c350893c103c5c3b518c9e4a5a3374e049c6c566141f21` | N/A | N/A | N/A |
| [relatorio_matriz_modo4.json](file:///C:/Users/Luis%20Brun/.gemini/antigravity/brain/f3af3942-aca3-4c9a-a3dd-e56f90feb848/relatorio_matriz_modo4.json) | `39.450` | `67fa82b7c905a4bda18d6802950188d79b47680d7fac8fa88393019d010b7a81` | N/A | N/A | N/A |
| [chave_publica_modo4.pem](file:///C:/Users/Luis%20Brun/.gemini/antigravity/brain/f3af3942-aca3-4c9a-a3dd-e56f90feb848/chave_publica_modo4.pem) | `113` | `d810ed9f31f476b159590cd2e053632dc32e8e6e62a5a17f7c2f371a45084b0f` | N/A | N/A | N/A |

Assinatura Ed25519 registrada em [manifesto_evidencia_execucao_modo4.sig](file:///C:/Users/Luis%20Brun/.gemini/antigravity/brain/f3af3942-aca3-4c9a-a3dd-e56f90feb848/manifesto_evidencia_execucao_modo4.sig):
`782b4b5c5bcebeb3b9b92401a4611543f29a5c1c2fda6173be070f1ab444d93c3486b919af6428938fad7826f596e234c14c369b5fe3797c5555b32bfc972a0f`

---

## 2. Demonstração Independente do Par Inicial (`seed = 330001`) e Regra Estrutural

A validação estrutural pura (sem invocar métodos de validação do motor) confirma exatamente o comportamento observado em `J=20` e `J=10.000`, reproduzido de forma idêntica por `MotorLotomaniaB2B` (referência original) e `MotorLotomaniaModo4`:

- **Bilhete inicial `j1` (`50` dezenas):**
  `[1, 5, 7, 9, 12, 15, 16, 17, 18, 20, 22, 23, 25, 27, 29, 32, 35, 37, 38, 39, 43, 45, 46, 49, 50, 52, 55, 56, 58, 59, 62, 63, 64, 67, 69, 71, 73, 76, 78, 80, 82, 83, 84, 86, 89, 92, 94, 95, 96, 97]`
  - Contagem por coluna (`(n - 1) % 10`, índices `0..9`): `{0: 2, 1: 7, 2: 5, 3: 3, 4: 7, 5: 6, 6: 6, 7: 4, 8: 7, 9: 3}` (`min_col = 2`, `max_col = 7`, `max_consec = 4`, 10 dezenas por quintil `C1..C5`). Resultado: **válido** (`True`) na validação independente pura, em `MotorLotomaniaB2B.validar_jogo` e em `MotorLotomaniaModo4.validar_jogo`.
- **Complemento espelho `j2 = {1..100} \ j1` (`50` dezenas):**
  `[2, 3, 4, 6, 8, 10, 11, 13, 14, 19, 21, 24, 26, 28, 30, 31, 33, 34, 36, 40, 41, 42, 44, 47, 48, 51, 53, 54, 57, 60, 61, 65, 66, 68, 70, 72, 74, 75, 77, 79, 81, 85, 87, 88, 90, 91, 93, 98, 99, 100]`
  - Contagem por coluna (`(n - 1) % 10`, índices `0..9`): `{0: 8, 1: 3, 2: 5, 3: 7, 4: 3, 5: 4, 6: 4, 7: 6, 8: 3, 9: 7}` (`min_col = 3`, `max_col = 8 > 7`, `max_consec = 3`).
  - Na coluna `0` (terminação `1`: `[11, 21, 31, 41, 51, 61, 81, 91]`), `j2` acumula `8` dezenas porque `j1` possuía apenas `2` dezenas nessa coluna (`[1, 71]`). Isso viola `colunas_max = 7` e torna `j2` inválido (`False`) na validação independente pura, em `MotorLotomaniaB2B.validar_jogo` e em `MotorLotomaniaModo4.validar_jogo`.
- **Efeito exato na trajetória gulosa (`seed=330001`):**
  - Apenas `j1` entra na inicialização (`idx_inicio_greedy = 1`).
  - `J=20` executa `19` estágios gulosos (`19 * 80 = 1.520` candidatos confrontados no trace interno com identidade exata de sequência e igualdade total contra `MotorLotomaniaB2B`).
  - `J=10.000` executa `9.999` estágios gulosos (`9.999 * 80 = 799.920` candidatos reconstruídos independentemente pela sequência PRNG em `comparar_bitmask_histograma_contra_referencia`, com zero deriva ao longo dos `10.000` jogos).
  - Nenhuma alteração foi feita no motor congelado [motor_lotomania_modo4.py](file:///C:/Users/Luis%20Brun/.gemini/antigravity/brain/f3af3942-aca3-4c9a-a3dd-e56f90feb848/motor_lotomania_modo4.py), nos pesos (`peso_inter = 30.0`, `peso_uso = 0.05`) ou nos critérios de seleção.

---

## 3. Verificação Independente sob `python -O --strict-dir` e Autotestes de Adulteração

Executado [verificar_evidencia_independente.py](file:///C:/Users/Luis%20Brun/.gemini/antigravity/brain/f3af3942-aca3-4c9a-a3dd-e56f90feb848/verificar_evidencia_independente.py) (`sha256_verificador_proprio = 2dfc9a3ed1ff45b5661323ed16dc69275d97769fc39d92f75f80c5045a080999`) com `python -O` diretamente sobre cópia recém-extraída do ZIP final em diretório temporário com a opção `--strict-dir`:

- **Resultado global:** `verificacao_independente_aprovada: true`, código de saída `0`, `erros: []`, `26` artefatos válidos no pacote (zero `.key` ou arquivo não previsto), `22` arquivos-fonte conferidos byte a byte contra o manifesto assinado e `13` hashes cruzados com os registrados durante a execução em `relatorio_matriz_modo4.json`.
- **Validação estrita de esquema JSON (`1.2.2`):** `11` registros (`J=1..10.000`) x `30` chaves exatas por registro, além de verificação dos campos de `comprovacao_fidelidade_reconstrucao_prng`.
- **Autotestes negativos sob `python -O` (`10/10` rejeitados):**
  1. `1_arquivo_obrigatorio_ausente` -> `RuntimeError`
  2. `2_arquivo_adicional_nao_previsto` -> `RuntimeError`
  3. `3_hash_divergente_modulo` -> `RuntimeError`
  4. `4_assinatura_ed25519_invalida` -> `InvalidSignature`
  5. `5_execucao_id_divergente` -> `RuntimeError`
  6. `6_manifesto_alterado` -> `InvalidSignature`
  7. `7_log_alterado` -> `RuntimeError`
  8. `8_esquema_relatorio_incompativel_hash_v2` -> `RuntimeError`
  9. `9_relatorio_de_outra_execucao` -> `RuntimeError`
  10. `10_chave_publica_nao_confiavel` -> `RuntimeError`

---

## 4. Comparação Histórica: `task-3057` (Preservada) vs. `task-3438` (Atual)

Os cinco artefatos da `task-3057` permanecem preservados em `scratch/historico_task_3057/` sem modificações.

| Critério | `task-3057` (Histórico Preservado) | `task-3438` (Execução Atual) | Diferença / Impacto |
| :--- | :--- | :--- | :--- |
| `execucao_id` | `36447bf9-5007-4cca-bac0-ceb5da35ce46` | `7b9b2102-82b3-469d-86c1-768c89dab2ea` | Nova execução pós-correções em diretório temporário isolado |
| Modo de execução Python | Padrão (`assert` ativo) | `-O` (`assert` ignorado, `0` ocorrências em AST nos 22 arquivos `.py`) | Comprova resistência integral a `python -O` |
| Versão de esquema do relatório | `1.2.1` (`27` chaves/tamanho) | `1.2.2` (`30` chaves/tamanho) | Separação explícita de métricas sem vs. com `tracemalloc`, classificação em 3 níveis e rastreio PRNG |
| Arquivos inventariados no manifesto | `20` | `22` | Adicionados `dados_brutos_90_saldos_consolidados.json` e `verificar_evidencia_independente.py`; padronizado `motor_lotomania.py` |
| Motor selado e referências congeladas | Selo Ed25519 original | Mesmos SHA-256 exatos em 11 arquivos inalterados (incluindo `motor_lotomania_modo4.py`, `verificador_selo_modo4.py`, `manifesto_modo4.*`, `chave_publica_modo4.pem`, `data/lotomania.json`) | Nenhuma alteração na matemática, pesos ou selo do motor |
| Hashes `hash_carteira_v1` e `v2` (`J=1..10.000`) | Referência gravada | `0` divergências em todos os `11` tamanhos | Reprodutibilidade bit a bit preservada |
| Suite rápida (`selo`, `sem_fallback`, `equivalencia`) | Cobertura inicial menor | `test_modo4_selo.py` expandido para `10` cenários; `test_modo4_sem_fallback.py` com bloqueios TCP/HTTP e `/conferir` `422`; `test_modo4_equivalencia.py` com prova em inteiros/Q | Cobertura fail-closed integral na API, cliente JS e núcleo |
| Verificador independente | `25` arquivos no ZIP anterior | `26` arquivos no pacote `pacote_homologacao_task_3438_modo4_v1_2.zip` (com `--strict-dir` ativo e log dinâmico) | Nomes/hashes antigos desacoplados e `10/10` autotestes em `-O` |

---

## 5. Inventário Completo dos 26 Arquivos em `pacote_homologacao_task_3438_modo4_v1_2.zip`

- **Arquivo ZIP final:** [pacote_homologacao_task_3438_modo4_v1_2.zip](file:///C:/Users/Luis%20Brun/.gemini/antigravity/brain/f3af3942-aca3-4c9a-a3dd-e56f90feb848/pacote_homologacao_task_3438_modo4_v1_2.zip) (`212.483` bytes)
- **SHA-256 do arquivo ZIP:** `04b72ed761903d4a7601a41b9eaae5749223e70cbb0cf632866928e01b9930bd`

| # | Caminho no Pacote ZIP | Bytes | SHA-256 |
| :---: | :--- | :---: | :--- |
| `1` | `api.py` | `25.821` | `66feca799af114c387c577574e9cd0cef7b21fffa093d6169177d06139557c0c` |
| `2` | `chave_publica_modo4.pem` | `113` | `d810ed9f31f476b159590cd2e053632dc32e8e6e62a5a17f7c2f371a45084b0f` |
| `3` | `dados_brutos_90_saldos_consolidados.json` | `39.040` | `07cbe14c5dc52e4f5b9cc0971f93062e2675bb386cb6e34cd3c490872378fc70` |
| `4` | `data/lotomania.json` | `293.085` | `3f11b71e15b936940c8cef40cf39c0a67f5c47f7a15b12a8c2608763ec39f873` |
| `5` | `demonstracao_invariancia_argmin.py` | `7.897` | `42493a44e24259e801624291498b50ce55d31c53ca4348c3d3ba42fe7dee78dc` |
| `6` | `gerar_manifesto_evidencia_execucao.py` | `12.459` | `ecb1a9b8b6d778c6b9b518b55a2f65373e3e939398bc2dc09ebcd1bbb39bc9f7` |
| `7` | `js/engines/motor_lotomania_modo4_engine.js` | `11.157` | `847729336f9db03afdb007ddb1d06c3570ec198328785bf6db05f5dd25a0f0fd` |
| `8` | `manifesto_evidencia_execucao_modo4.json` | `5.639` | `8ca5eea07c2b5ad20511119aed504ed2426d9f24e81cbc02a7d4229595526a48` |
| `9` | `manifesto_evidencia_execucao_modo4.sig` | `130` | `f6cfb00feffdc1a1caaf2aae9b8e31960b4d2b66051edacdf1ed18bf7356a52b` |
| `10` | `manifesto_modo4.json` | `2.554` | `66e255cd526e2c72ec1fda3d3112cb918b4e678b1f264117593ca7cdf127e57c` |
| `11` | `manifesto_modo4.sig` | `130` | `21e43c7fd670fed1d384bad98344c7daf7f3f1c6fd5405f0dceb64f55fbd453f` |
| `12` | `motor_lotomania.py` | `108.318` | `085d6fa972dfb97576246f26b8687fce35b7dc9199bb30fca61cc348df851d6c` |
| `13` | `motor_lotomania_modo4.py` | `40.462` | `94a2d1001d235e0e9bd543aeee697bac0ac6c60b1d24654838e452d6f42c68f9` |
| `14` | `procedimento_homologacao_integral.py` | `34.171` | `57446e28eb69917b30b0ebec5854b8580ec816862a15a9e87e7b636d3a2e201c` |
| `15` | `relatorio_matriz_modo4.json` | `39.450` | `67fa82b7c905a4bda18d6802950188d79b47680d7fac8fa88393019d010b7a81` |
| `16` | `task-3438.log` | `9.935` | `a4800ca2351418e775c350893c103c5c3b518c9e4a5a3374e049c6c566141f21` |
| `17` | `test_motor_lotomania.py` | `4.562` | `515930726ca0ffc6e2617ff506ff590e390e78841fae1e8fe85a48c71d2ca663` |
| `18` | `test_motor_lotomania_evolution.py` | `6.395` | `a1a924db12c269169177632d0b71f61c1641bda121ddbcc19dc1baa86ca6458e` |
| `19` | `test_validacao_matematica_rwin.py` | `12.257` | `e59809c8b930bb0b823fc1dbf789293dfb3e25b01ae670a16997c45d38e646c5` |
| `20` | `teste_sensibilidade_pesos.py` | `9.548` | `5aebdce7926c3ee19ac02539db6d45d2d01a5d8cf04155458bf3a60c4d870dbf` |
| `21` | `testes/test_modo4_equivalencia.py` | `18.560` | `32793702ecf7a0b306739e64fbddea9c81596c32a3b26207ba2b396196debdfd` |
| `22` | `testes/test_modo4_matriz_carteiras.py` | `48.034` | `d4644226a5665c514ec286d22a83f117a5ec1ef4f524fffac06a8a986ea21e88` |
| `23` | `testes/test_modo4_selo.py` | `10.604` | `e4996ca8858cd739fba5b1f1d34e34ee039e2ea20e0e8b9b5592bde3d260a50e` |
| `24` | `testes/test_modo4_sem_fallback.py` | `21.780` | `c5f487125ee6b6b3fd796f54af550856366752ad477a3fabc233ab4f422c5ab0` |
| `25` | `verificador_selo_modo4.py` | `10.671` | `632388d3c58aee37ae41cd33e44ddd8fad78ea22ebdb339f2aff4fae59b89e46` |
| `26` | `verificar_evidencia_independente.py` | `33.771` | `2dfc9a3ed1ff45b5661323ed16dc69275d97769fc39d92f75f80c5045a080999` |
