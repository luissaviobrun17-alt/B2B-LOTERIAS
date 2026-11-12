# DECLARAÇÃO DE CUSTÓDIA E ORIGEM DA CHAVE PÚBLICA
## LOTOMANIA MODO 4 v1.2: Autenticação do Root of Trust Ed25519

* **Finalidade:** Responder à Ressalva 6.1 do `PARECER_EXTERNO_DEFINITIVO_MODO4_V1_2.md` mediante registro formal e verificável da origem, continuidade histórica e titularidade da chave pública Ed25519 vinculada aos manifestos da build `v1.2`.
* **Natureza:** Documento complementar de governança. Não altera, substitui ou reemite nenhum artefato ou arquivo ZIP congelado de `task-3057` ou `task-3438`.
* **Situação atual:** Confronto criptográfico local e continuidade histórica tecnicamente confirmados; **pendente apenas de identificação nominal, vínculo institucional e assinatura formal do custodiante** na Seção 5 para validade jurídica e perante terceiros.

---

## 1. IDENTIFICAÇÃO DA CHAVE PÚBLICA FIXADA

| Atributo | Valor Verificado |
| :--- | :--- |
| Arquivo público distribuído | `chave_publica_modo4.pem` (`113` bytes) |
| Formato / Algoritmo | SubjectPublicKeyInfo (SPKI) PEM, algoritmo `Ed25519` |
| Conteúdo Base64 público SPKI | `MCowBQYDK2VwAyEAPPFCkzbtBh3n01JK9JwxMmA9aHwZpozdK++EudJ1WLA=` |
| Fingerprint SHA-256 oficial | `d810ed9f31f476b159590cd2e053632dc32e8e6e62a5a17f7c2f371a45084b0f` |
| Repositório local da chave privada (restrito ao ambiente do custodiante) | `C:\Users\Luis Brun\B2B_chaves\modo4_ed25519.key` |
| Inclusão de chave privada em pacotes externos/internos | Nenhuma (`0` arquivos `.key` em `ENTREGA_AUDITORIA_EXTERNA_TASK_3438.zip` e em `pacote_homologacao_task_3438_modo4_v1_2.zip`) |

---

## 2. CONFRONTO CRIPTOGRÁFICO LOCAL E CADEIA HISTÓRICA VERIFICADA

Em verificação controlada executada em ambiente local em `2026-11-12` (leitura estrita apenas para derivação em memória da componente pública de `modo4_ed25519.key`, sem leitura externa, transmissão ou exibição dos bytes privados), foram confirmados os seguintes fatos objetivos:

| Elo da Cadeia de Custódia | Evidência Técnica Observada | Fingerprint / Hash SHA-256 | Resultado |
| :--- | :--- | :--- | :--- |
| Chave privada local (`C:\Users\Luis Brun\B2B_chaves\modo4_ed25519.key`) | Derivação SPKI PEM em memória (`113` bytes) | `d810ed9f31f476b159590cd2e053632dc32e8e6e62a5a17f7c2f371a45084b0f` | Idêntico à chave distribuída |
| Referência histórica `task-3057` (`execucao_id`: `36447bf9-5007-4cca-bac0-ceb5da35ce46`, assinatura `2026-11-12T18:52:13.961297+00:00`) | Chave pública interna do ZIP (`pacote_homologacao_task_3057_modo4_v1_2.zip`), manifesto JSON (`5.430` B, canônico `4.831` B) e `.sig` (`130` B) | Chave: `d810ed9f...084b0f`; ZIP: `866aafbd1968356577cc76bda78e9dbf94e01a31e281ba4e43d72ff9820092da`; Canônico: `0ff653a2732a89eca2a133ccd03862541faf55128bcd0107120defc609d067a5` | Assinatura Ed25519 válida e chave idêntica |
| Execução congelada `task-3438` (`execucao_id`: `7b9b2102-82b3-469d-86c1-768c89dab2ea`, assinatura `2026-11-12T21:00:23.367684+00:00`) | Pacotes ZIP externo e interno, manifesto JSON (`5.639` B, canônico `5.026` B) e `.sig` (`130` B) | Canônico: `46241c038ce08cf9aa311ca9db415ebc68380722ed60421000205c10df44d64e`; `.sig`: `f6cfb00feffdc1a1caaf2aae9b8e31960b4d2b66051edacdf1ed18bf7356a52b` | Assinatura Ed25519 válida e chave idêntica |

Essa matriz estabelece continuidade criptográfica entre a chave privada sob guarda local, a homologação histórica preservada (`task-3057`) e o pacote final auditado (`task-3438`).

---

## 3. LIMITES DE VALIDAÇÃO PERANTE TERCEIROS

A validação matemática confirma que o mesmo par de chaves assinou os pacotes `task-3057` e `task-3438`, porém não substitui a vinculação jurídica e institucional da chave a uma pessoa física ou entidade responsável. Sem uma declaração formal assinada pelo custodiante e, preferencialmente, uma publicação prévia da chave em canal institucional independente (como repositório com histórico auditável, registro ICP-Brasil ou serviço de transparência criptográfica), um auditor externo apenas verifica a consistência interna entre a chave fornecida e as assinaturas entregues.

Para ciclos subsequentes à build `v1.2`, recomenda-se publicar o fingerprint da chave pública oficial em registro institucional imutável antes do início das execuções auditadas, acompanhado de carimbo do tempo RFC 3161 ou âncora externa equivalente para pré-especificação estatística.

---

## 4. PROCEDIMENTO REPRODUTÍVEL DE CONFERÊNCIA LOCAL PELO CUSTODIANTE

O próprio custodiante pode reconfirmar a correspondência pública a qualquer momento em terminal local, sem imprimir ou copiar o segredo privado:

```powershell
python -c "import hashlib; from pathlib import Path; from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat, load_pem_private_key; pub=load_pem_private_key(Path(r'C:\Users\Luis Brun\B2B_chaves\modo4_ed25519.key').read_bytes(), password=None).public_key().public_bytes(Encoding.PEM, PublicFormat.SubjectPublicKeyInfo); print(hashlib.sha256(pub).hexdigest())"
```

Saída esperada para confirmação integral:

```text
d810ed9f31f476b159590cd2e053632dc32e8e6e62a5a17f7c2f371a45084b0f
```

---

## 5. TERMO DE DECLARAÇÃO E ASSINATURA DO CUSTODIANTE

Eu, abaixo assinado(a), na qualidade de custodiante responsável pela guarda do par de chaves criptográficas vinculado ao projeto Lotomania MODO 4 `v1.2`, declaro para os devidos fins técnicos e de auditoria que:

1. A chave pública Ed25519 contida em `chave_publica_modo4.pem` (`MCowBQYDK2VwAyEAPPFCkzbtBh3n01JK9JwxMmA9aHwZpozdK++EudJ1WLA=`, SHA-256 `d810ed9f31f476b159590cd2e053632dc32e8e6e62a5a17f7c2f371a45084b0f`) corresponde exatamente à chave privada mantida sob minha custódia exclusiva e isolada em `C:\Users\Luis Brun\B2B_chaves\modo4_ed25519.key`.
2. A referida chave privada permaneceu restrita ao ambiente de custódia durante os ciclos `task-3057` e `task-3438`, não tendo sido copiada, compartilhada nem incluída nos pacotes de entrega externa ou de homologação.
3. Reconheço como legítimas as assinaturas digitais Ed25519 emitidas sobre os manifestos das execuções `task-3057` (`36447bf9-5007-4cca-bac0-ceb5da35ce46`) e `task-3438` (`7b9b2102-82b3-469d-86c1-768c89dab2ea`).

* **Nome completo do custodiante:** `[PREENCHER]`
* **Cargo / Organização:** `[PREENCHER]`
* **Documento ou Identificador Institucional:** `[PREENCHER]`
* **Canal ou Registro Público Adicional da Chave (se aplicável):** `[OPCIONAL / PREENCHER]`
* **Local e Data:** `[PREENCHER]`
* **Assinatura do Custodiante (física ou ICP-Brasil / assinatura eletrônica qualificada):** `[ASSINAR]`

---

## CLÁUSULA MATEMÁTICA OBRIGATÓRIA

> O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.
