# Dossiê de Auditoria Independente: Otimizador Combinatório de Dispersão e Cobertura Conjunta (MODO 4: Lotomania)

Este documento consolida a totalidade dos códigos-fonte, bases brutas em formato JSON, suítes de testes unitários automatizados, demonstração algébrica e empírica da invariância do minimizador, análises de sensibilidade dos pesos, quatro baterias de reprodução empírica com pareamento por Common Random Numbers (CRN) e manifesto criptográfico do **OTIMIZADOR COMBINATÓRIO DE DISPERSÃO E COBERTURA CONJUNTA: LOTOMANIA | MODO 4**.

---

## 1. Pacote Consolidado para Inspeção Física

O pacote oficial compactado contendo todos os 23 arquivos executáveis, suítes de testes e bases de dados brutas está disponível nos seguintes caminhos:

- **Área de Trabalho (Host Windows):** [`auditoria_lotomania_b2b_completa.zip`](file:///C:/Users/Luis%20Brun/Desktop/auditoria_lotomania_b2b_completa.zip)
- **Script Extrator Autônomo na Área de Trabalho:** [`extrair_auditoria_completa.py`](file:///C:/Users/Luis%20Brun/Desktop/extrair_auditoria_completa.py)
- **Diretório de Artefatos:** [`auditoria_lotomania_b2b_completa.zip`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/brain/f3af3942-aca3-4c9a-a3dd-e56f90feb848/auditoria_lotomania_b2b_completa.zip)
- **Diretório do Workspace:** [`auditoria_lotomania_b2b_completa.zip`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/auditoria_lotomania_b2b_completa.zip)
- **Tamanho Físico Exato:** 169.366 bytes (169.366 B)
- **Hash Criptográfico SHA-256:** `9387de3b5c512cd77380371bf88422386b0ad7b0bb215cecd8a9023771158f28`
- **Total de Itens Integrados:** 23 arquivos (incluindo diretório `data/lotomania.json`)

---

## 2. Conteúdo dos 23 Arquivos do Pacote

| Item | Arquivo | Descrição Técnica e Função no Sistema |
| :---: | :--- | :--- |
| 1 | [`motor_lotomania.py`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/motor_lotomania.py) | Núcleo matemático com tabela pré-computada $R_{\text{win}}(k)$, amostragem controlada de 80 candidatos com frozenset, separação formal entre Camada A (regras oficiais Caixa) e Camada B (filtros heurísticos B2B), cálculo exato de $\Delta V$ e proteção fail-closed. |
| 2 | [`api.py`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/api.py) | Servidor FastAPI com validação Pydantic estrita, mascaramento de erros internos e tipagem profunda de inteiros. |
| 3 | [`auditoria_independente_unificada.py`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/auditoria_independente_unificada.py) | Script autocontido de auditoria que valida fórmulas bivariadas, toy models, casos-limite e realiza a carga dinâmica dos 90 saldos das 4 baterias. |
| 4 | [`test_validacao_matematica_rwin.py`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/test_validacao_matematica_rwin.py) | 8 testes unitários automatizados confrontando todos os 51 valores de $R_{\text{win}}(k)$ por programação dinâmica, toy models e conservação do espaço amostral. |
| 5 | [`test_motor_lotomania.py`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/test_motor_lotomania.py) | 5 testes unitários de conformidade regulatória, divisão de quintis e consecutividade de dezenas. |
| 6 | [`test_motor_lotomania_evolution.py`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/test_motor_lotomania_evolution.py) | 7 testes unitários evolutivos cobrindo análise temporal, 6 modos, cálculo do IFM em 10 dimensões e backtesting com histórico determinístico de fallback. |
| 7 | [`demonstracao_invariancia_argmin.py`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/demonstracao_invariancia_argmin.py) | Script de auditoria analítica que processa as 189 etapas sequenciais e confronta os 79 concorrentes por etapa sob $\alpha \in [0,5; 2,0]$. |
| 8 | [`invariancia_argmin_189_etapas.json`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/invariancia_argmin_189_etapas.json) | Matriz completa com as 14.931 comparações pareadas individuais, discriminando 182 mínimos estritos e 7 empates exatos em $\mathbb{Q}$. |
| 9 | [`teste_sensibilidade_pesos.py`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/teste_sensibilidade_pesos.py) | Teste de sensibilidade com 2.000.000 de sorteios avaliando as configurações sob pesos 0x, 0,5x, 1x e 2x, com verificação de hashes SHA-256. |
| 10 | [`analise_sensibilidade_resultados.json`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/analise_sensibilidade_resultados.json) | Base bruta da análise de sensibilidade e registro dos hashes SHA-256 das 10 rodadas sob sementes 330001 a 330010. |
| 11 | [`bateria_30_carteiras_lotomania.py`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/bateria_30_carteiras_lotomania.py) | Script executor da Bateria 1 (30 rodadas pareadas de 50.000 sorteios, totalizando 1.500.000 sorteios). |
| 12 | [`bateria_30_carteiras_resultados.json`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/bateria_30_carteiras_resultados.json) | Dados brutos das 30 rodadas da Bateria 1 (+10.150 premiações, 30/30 vitórias, $t = 11,5496$). |
| 13 | [`teste_robustez_novas_sementes.py`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/teste_robustez_novas_sementes.py) | Script executor da Bateria 2 (20 rodadas sob sementes inéditas, totalizando 1.000.000 de sorteios). |
| 14 | [`teste_robustez_novas_sementes_resultados.json`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/teste_robustez_novas_sementes_resultados.json) | Dados brutos das 20 rodadas da Bateria 2 (+6.003 premiações, 20/20 vitórias, $t = 8,1732$). |
| 15 | [`teste_generalizacao_bateria3.py`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/teste_generalizacao_bateria3.py) | Script executor da Bateria 3 (20 rodadas pareadas adicionais, 1.000.000 de sorteios). |
| 16 | [`teste_generalizacao_bateria3_resultados.json`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/teste_generalizacao_bateria3_resultados.json) | Dados brutos das 20 rodadas da Bateria 3 (+7.171 premiações, 20/20 vitórias, $t = 10,8321$). |
| 17 | [`teste_generalizacao_bateria4.py`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/teste_generalizacao_bateria4.py) | Script executor da Bateria 4 com metodologia estrita Common Random Numbers (CRN) e parâmetros congelados. |
| 18 | [`teste_generalizacao_bateria4_resultados.json`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/teste_generalizacao_bateria4_resultados.json) | Dados brutos das 20 rodadas da Bateria 4 (+5.333 premiações, 20/20 vitórias, $t = 7,8157$). |
| 19 | [`dados_brutos_90_saldos_consolidados.json`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/dados_brutos_90_saldos_consolidados.json) | Tabela completa unificada das 90 unidades amostrais independentes com sementes de carteira, sementes de sorteios, contagens individuais de acertos e saldos $D_r$. |
| 20 | [`auditoria_reprodutivel_lotomania.py`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/auditoria_reprodutivel_lotomania.py) | Simulação inicial de controle com 100.000 sorteios para confronto das carteiras de 20 apostas. |
| 21 | [`auditoria_reprodutivel_resultados.json`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/auditoria_reprodutivel_resultados.json) | As 60 apostas completas de 50 dezenas e respectivas matrizes de interseção para auditoria estática. |
| 22 | [`data/lotomania.json`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/data/lotomania.json) | Histórico oficial completo de concursos da Caixa para calibracao de janelas temporais e backtesting. |
| 23 | [`README_AUDITORIA.txt`](file:///C:/Users/Luis%20Brun/.gemini/antigravity/scratch/loteria_b2b/README_AUDITORIA.txt) | Manifesto oficial e guia de execução no terminal para reprodução independente em comando único. |

---

## 3. Instruções de Reprodução Rápida no Terminal

Após descompactar o arquivo `auditoria_lotomania_b2b_completa.zip` em um diretório limpo, as verificações formais podem ser reproduzidas diretamente:

1. **Execução integral da suíte de 20 testes unitários automatizados (0 falhas e 0 erros):**
   ```powershell
   python -c "import unittest, sys; import test_validacao_matematica_rwin, test_motor_lotomania, test_motor_lotomania_evolution; loader = unittest.TestLoader(); suite = unittest.TestSuite(); suite.addTests(loader.loadTestsFromModule(test_validacao_matematica_rwin)); suite.addTests(loader.loadTestsFromModule(test_motor_lotomania)); suite.addTests(loader.loadTestsFromModule(test_motor_lotomania_evolution)); runner = unittest.TextTestRunner(verbosity=2); res = runner.run(suite); sys.exit(0 if (res.wasSuccessful() and res.testsRun == 20) else 1)"
   ```

2. **Execução do relatório unificado de auditoria com carga dinâmica dos 90 saldos:**
   ```powershell
   python auditoria_independente_unificada.py
   ```

3. **Reprodução da matriz de 189 etapas de invariância do minimizador:**
   ```powershell
   python demonstracao_invariancia_argmin.py
   ```

4. **Verificação dos hashes SHA-256 e sensibilidade de pesos sob 2.000.000 de sorteios:**
   ```powershell
   python teste_sensibilidade_pesos.py
   ```

---

## 4. Cláusula Regulatória Mandatória

O sistema não prevê resultados futuros nem altera a probabilidade matemática individual de premiação de qualquer bilhete. Seu objetivo é otimizar a distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a redundância entre eventos premiados e melhorar a cobertura conjunta observada.
