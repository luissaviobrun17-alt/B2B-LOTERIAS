# -*- coding: utf-8 -*-
"""
SUITE DE TESTES — ETAPA 1 (LOTOFACIL MODO 4)
=============================================
Valida regras oficiais da CAIXA, combinatoria exata, distribuicao
hipergeometrica H(25, 15, m), multiplicidade de premios em apostas multiplas,
splits bivariados, geometria da matriz 5x5 e integridade da base oficial.

Importante: nao utiliza 'assert' como barreira critica; todas as verificacoes
usam excecoes explicitas e mantem efetividade integral sob python -O.
"""

from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import math
import os
import sys
import unittest

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lotofacil_modo4.etapa1_regras_oficiais import (  # noqa: E402
    CENTRO_5X5,
    CLAUSULA_MATEMATICA_OBRIGATORIA,
    COLUNAS_5X5,
    DEZENAS_DISPONIVEIS,
    DIAGONAL_PRINCIPAL_5X5,
    DIAGONAL_SECUNDARIA_5X5,
    ESPACO_AMOSTRAL_SIMPLES,
    FIBONACCI_25,
    LINHAS_5X5,
    MASCARA_CENTRO_5X5,
    MASCARA_MOLDURA_5X5,
    MASCARA_PARES,
    MASCARA_IMPARES,
    MASCARAS_COLUNAS_5X5,
    MASCARAS_LINHAS_5X5,
    MOLDURA_5X5,
    MULTIPLOS_3_25,
    MULTIPLOS_5_25,
    PERCENTUAL_PREMIO_BRUTO,
    PRECO_APOSTA_SIMPLES,
    PREMIOS_FIXOS,
    PRIMOS_25,
    RATEIO_SALDO_VARIAVEL,
    REGRAS_OFICIAIS_LOTOFACIL,
    REGRAS_PREMIACAO_FINAL_ZERO,
    REGRAS_PREMIACAO_INDEPENDENCIA,
    REGRAS_PREMIACAO_REGULAR,
    UNIVERSO_TOTAL,
    ErroValidacaoLotofacilError,
    combinacao_exata,
    custo_aposta_oficial,
    definicao_formal_conceitos_secao3,
    distribuicao_hipergeometrica_aposta,
    gerar_resumo_formal_etapa1,
    matriz_5x5_coordenadas,
    multiplicidade_premios_aposta,
    probabilidade_hipergeometrica_exata,
    probabilidade_pelo_menos_k_exata,
    probabilidade_split_bivariada_exata,
    validar_aposta_lotofacil,
    validar_inteiro_estrito,
    validar_natureza_componente,
)


def _exigir(condicao: bool, mensagem: str) -> None:
    if not condicao:
        raise AssertionError(mensagem)


class TestLotofacilModo4Etapa1(unittest.TestCase):
    def test_regras_oficiais_caixa_e_custos_exatos(self) -> None:
        _exigir(ESPACO_AMOSTRAL_SIMPLES == 3_268_760, "C(25,15) diverge de 3.268.760.")
        _exigir(len(DEZENAS_DISPONIVEIS) == 25, "Universo deve conter 25 dezenas.")
        _exigir(PRECO_APOSTA_SIMPLES == Decimal("3.50"), "Aposta simples deve ser R$ 3,50.")
        _exigir(PERCENTUAL_PREMIO_BRUTO == Decimal("0.4379"), "Premio bruto deve ser 43,79%.")
        _exigir(PREMIOS_FIXOS[11] == Decimal("7.00"), "Premio 11 acertos diverge de R$ 7,00.")
        _exigir(PREMIOS_FIXOS[12] == Decimal("14.00"), "Premio 12 acertos diverge de R$ 14,00.")
        _exigir(PREMIOS_FIXOS[13] == Decimal("35.00"), "Premio 13 acertos diverge de R$ 35,00.")

        # Conferencia integral dos rateios (soma = 100% do saldo restante em cada regime)
        for regime, mapa in RATEIO_SALDO_VARIAVEL.items():
            soma_rateio = sum(mapa.values())
            _exigir(
                soma_rateio == Decimal("1.00"),
                f"Rateio do regime '{regime}' nao soma 1.00 ({soma_rateio}).",
            )

        # Conferencia do versionamento das 3 regras de premiacao (Ressalva 1.A)
        for regra in (
            REGRAS_PREMIACAO_REGULAR,
            REGRAS_PREMIACAO_FINAL_ZERO,
            REGRAS_PREMIACAO_INDEPENDENCIA,
        ):
            _exigir(bool(regra.get("versao_regra")), "Regra sem versao_regra.")
            _exigir(bool(regra.get("vigencia_desde_data")), "Regra sem data de vigencia.")
            _exigir(bool(regra.get("fonte_oficial_url")), "Regra sem fonte oficial.")
            _exigir(
                sum(regra["rateio_saldo_variavel"].values()) == Decimal("1.00"),
                f"Saldo variavel da regra {regra['codigo_regime']} nao soma 1.00.",
            )

        tabela_esperada = {
            15: (1, Decimal("3.50")),
            16: (16, Decimal("56.00")),
            17: (136, Decimal("476.00")),
            18: (816, Decimal("2856.00")),
            19: (3876, Decimal("13566.00")),
            20: (15504, Decimal("54264.00")),
        }
        for m, (comb_esp, custo_esp) in tabela_esperada.items():
            _exigir(combinacao_exata(m, 15) == comb_esp, f"C({m}, 15) incorreta.")
            _exigir(custo_aposta_oficial(m) == custo_esp, f"Custo para m={m} incorreto.")

        _exigir(
            CLAUSULA_MATEMATICA_OBRIGATORIA in REGRAS_OFICIAIS_LOTOFACIL["clausula_obrigatoria"],
            "Clausula matematica obrigatoria ausente nas regras oficiais.",
        )

    def test_distribuicao_hipergeometrica_exata_15_a_20(self) -> None:
        # Conferencia direta dos valores '1 em X' da tabela oficial da CAIXA
        for m in range(15, 21):
            res = distribuicao_hipergeometrica_aposta(m)
            _exigir(res["soma_probabilidades"] == "1/1", f"Soma != 1 para m={m}.")
            _exigir(res["combinacoes_simples"] == math.comb(m, 15), f"Combinacoes != C({m},15).")

            # Recalculo independente em fracoes irredutiveis para todo k do suporte
            soma_indep = Fraction(0, 1)
            esp_indep = Fraction(0, 1)
            for k, item in res["distribuicao"].items():
                p = item["probabilidade_exata"]
                _exigir(isinstance(p, Fraction), "Probabilidade deve ser Fraction exata.")
                p_esp = Fraction(math.comb(m, k) * math.comb(25 - m, 15 - k), 3_268_760)
                _exigir(p == p_esp, f"Divergencia em P(X={k} | m={m}).")
                soma_indep += p
                esp_indep += k * p

            _exigir(soma_indep == Fraction(1, 1), f"Recalculo soma != 1 para m={m}.")
            _exigir(esp_indep == Fraction(15 * m, 25), f"E[X] incorreta para m={m}.")

        # Pontos especificos da tabela oficial da CAIXA ("1 em X")
        _exigir(probabilidade_hipergeometrica_exata(15, 15) == Fraction(1, 3_268_760), "P(15|15) incorreta.")
        _exigir(probabilidade_hipergeometrica_exata(15, 14) == Fraction(150, 3_268_760), "P(14|15) incorreta.")
        _exigir(probabilidade_hipergeometrica_exata(15, 13) == Fraction(4725, 3_268_760), "P(13|15) incorreta.")
        _exigir(probabilidade_hipergeometrica_exata(15, 12) == Fraction(54600, 3_268_760), "P(12|15) incorreta.")
        _exigir(probabilidade_hipergeometrica_exata(15, 11) == Fraction(286650, 3_268_760), "P(11|15) incorreta.")

        p_prem_15 = probabilidade_pelo_menos_k_exata(15, 11)
        _exigir(p_prem_15 == Fraction(346_126, 3_268_760), f"P(X>=11 | m=15) inesperada: {p_prem_15}.")
        _exigir(
            probabilidade_hipergeometrica_exata(20, 15) == Fraction(15504, 3_268_760),
            "P(15 | m=20) deve ser 15504/3268760 (~1 em 210.83).",
        )
        # Caso impossivel no suporte (m=20, k=9 => 15-9=6 > 5 dezenas fora do bilhete)
        _exigir(
            probabilidade_hipergeometrica_exata(20, 9) == Fraction(0, 1),
            "P(X=9 | m=20) deveria ser exatamente 0.",
        )

    def test_multiplicidade_premios_tabela_oficial_caixa(self) -> None:
        casos_caixa = [
            (15, 15, {15: 1, 14: 0, 13: 0, 12: 0, 11: 0}),
            (16, 15, {15: 1, 14: 15, 13: 0, 12: 0, 11: 0}),
            (16, 14, {15: 0, 14: 2, 13: 14, 12: 0, 11: 0}),
            (17, 15, {15: 1, 14: 30, 13: 105, 12: 0, 11: 0}),
            (17, 13, {15: 0, 14: 0, 13: 6, 12: 52, 11: 78}),
            (18, 14, {15: 0, 14: 4, 13: 84, 12: 364, 11: 364}),
            (19, 15, {15: 1, 14: 60, 13: 630, 12: 1820, 11: 1365}),
            (20, 15, {15: 1, 14: 75, 13: 1050, 12: 4550, 11: 6825}),
            (20, 12, {15: 0, 14: 0, 13: 0, 12: 56, 11: 840}),
            (20, 11, {15: 0, 14: 0, 13: 0, 12: 0, 11: 126}),
        ]
        for m, h, esperado in casos_caixa:
            res = multiplicidade_premios_aposta(m, h)
            _exigir(
                res["premios_por_faixa"] == esperado,
                f"Multiplicidade divergiu da tabela oficial CAIXA para m={m}, h={h}: {res['premios_por_faixa']}.",
            )

    def test_splits_e_geometria_matriz_5x5(self) -> None:
        # Soma exata = 1 para qualquer divisao (A, 25-A)
        for tam_a in (10, 11, 12, 13, 14):
            soma = sum(probabilidade_split_bivariada_exata(tam_a, a) for a in range(16))
            _exigir(soma == Fraction(1, 1), f"Split A={tam_a} nao soma 1 ({soma}).")

        # Particoes ortogonais da matriz 5x5
        _exigir(len(MOLDURA_5X5) == 16 and len(CENTRO_5X5) == 9, "Moldura/centro incorretos.")
        _exigir(MOLDURA_5X5.isdisjoint(CENTRO_5X5), "Moldura e centro devem ser disjuntos.")
        _exigir(MOLDURA_5X5 | CENTRO_5X5 == set(range(1, 26)), "Moldura + centro deve cobrir [1..25].")
        _exigir((MASCARA_MOLDURA_5X5 & MASCARA_CENTRO_5X5) == 0, "Bitmasks moldura/centro sobrepostas.")
        _exigir((MASCARA_MOLDURA_5X5 | MASCARA_CENTRO_5X5) == (1 << 25) - 1, "Bitmask total invalida.")
        _exigir((MASCARA_PARES ^ MASCARA_IMPARES) == (1 << 25) - 1, "Paridade deve particionar [1..25].")
        _exigir(len(LINHAS_5X5) == 5 and len(COLUNAS_5X5) == 5, "Matriz deve ter 5 linhas e 5 colunas.")
        _exigir(len(MASCARAS_LINHAS_5X5) == 5 and len(MASCARAS_COLUNAS_5X5) == 5, "Mascaras 5x5 invalidas.")
        _exigir(DIAGONAL_PRINCIPAL_5X5 & DIAGONAL_SECUNDARIA_5X5 == {13}, "Centro da matriz deve ser 13.")
        _exigir(PRIMOS_25 == {2, 3, 5, 7, 11, 13, 17, 19, 23}, "Conjunto de primos invalido.")
        _exigir(FIBONACCI_25 == {1, 2, 3, 5, 8, 13, 21}, "Conjunto Fibonacci invalido.")
        _exigir(MULTIPLOS_3_25 == {3, 6, 9, 12, 15, 18, 21, 24}, "Multiplos de 3 invalidos.")
        _exigir(MULTIPLOS_5_25 == {5, 10, 15, 20, 25}, "Multiplos de 5 invalidos.")
        _exigir(matriz_5x5_coordenadas(1) == (0, 0) and matriz_5x5_coordenadas(25) == (4, 4), "Coordenadas 5x5 invalidas.")

    def test_validacao_negativa_sem_assert_efetiva_em_modo_O(self) -> None:
        entradas_invalidas = [
            (True, "flag"),
            (15.0, "m_float"),
            ("15", "m_str"),
            (None, "m_none"),
        ]
        for val, nome in entradas_invalidas:
            falhou = False
            try:
                validar_inteiro_estrito(val, nome, 1, 25)
            except ErroValidacaoLotofacilError:
                falhou = True
            _exigir(falhou, f"Tipo invalido {val!r} nao foi rejeitado.")

        apostas_invalidas = [
            list(range(1, 15)),            # 14 dezenas
            list(range(1, 22)),            # 21 dezenas
            list(range(1, 15)) + [14],     # duplicata
            list(range(1, 15)) + [26],     # fora do limite >25
            list(range(0, 15)),            # 0 fora de [1..25]
            [True] + list(range(2, 16)),   # bool
            "01 02 03",                    # string
        ]
        for ap in apostas_invalidas:
            falhou = False
            try:
                validar_aposta_lotofacil(ap)
            except ErroValidacaoLotofacilError:
                falhou = True
            _exigir(falhou, f"Aposta invalida {ap!r} nao foi rejeitada.")

        resumo = gerar_resumo_formal_etapa1()
        conceitos = definicao_formal_conceitos_secao3()
        _exigir(len(conceitos["distincoes_conceituais_obrigatorias"]) == 5, "Devem existir 5 distincoes na Secao 3.")
        _exigir(
            "346.126 / 3.268.760"
            in conceitos["distincoes_conceituais_obrigatorias"]["1_probabilidade_individual_bilhete"]["definicao"],
            "Definicao 1 da Secao 3 deve conter exatamente 346.126 / 3.268.760.",
        )
        _exigir(len(resumo["regras_premiacao_versionadas"]) == 3, "Devem existir 3 regras versionadas no resumo.")
        _exigir(resumo["splits_teoricos"]["divisao_principal_13_12_soma"] == "1", "Resumo Etapa 1 invalido.")

        # Ressalva 1.D: tentativa de uso preditivo deve falhar explicitamente no codigo
        _exigir(validar_natureza_componente("DESCRITIVO", False) == "DESCRITIVO", "Natureza descritiva falhou.")
        falhou_pred = False
        try:
            validar_natureza_componente("DESCRITIVO", True)
        except ErroValidacaoLotofacilError:
            falhou_pred = True
        _exigir(falhou_pred, "Uso preditivo indevido de indicador descritivo nao foi bloqueado.")

    def test_integridade_base_oficial_caixa_sincronizada(self) -> None:
        caminho_base = os.path.join(BASE_DIR, "lotofacil_modo4", "dados", "lotofacil_oficial_caixa.json")
        _exigir(
            os.path.isfile(caminho_base),
            f"Base oficial sincronizada ausente em {caminho_base}.",
        )
        with open(caminho_base, "r", encoding="utf-8") as f:
            doc = json.load(f)

        concursos = doc["concursos"]
        _exigir(len(concursos) == doc["total_concursos"], "Contagem total_concursos diverge.")
        _exigir(doc["total_concursos"] >= 3828, "Base sincronizada deve conter ao menos 3828 concursos.")
        _exigir(doc["concursos_faltantes"] == 0, "Existem concursos faltantes registrados.")

        for idx, rec in enumerate(concursos, start=1):
            _exigir(rec["numero"] == idx, f"Sequencia de concursos quebrada no indice {idx}.")
            _exigir(bool(rec.get("data_apuracao")), f"Concurso {idx} sem data_apuracao.")
            dezs = rec["dezenas"]
            _exigir(len(dezs) == 15 and dezs == sorted(set(dezs)), f"Concurso {idx} com dezenas invalidas.")
            _exigir(min(dezs) >= 1 and max(dezs) <= 25, f"Concurso {idx} fora do dominio [1..25].")

        payload_canonico = json.dumps(
            concursos, ensure_ascii=False, separators=(",", ":"), sort_keys=True
        ).encode("utf-8")
        sha_rec = hashlib.sha256(payload_canonico).hexdigest()
        _exigir(
            sha_rec == doc["sha256_lista_concursos_canonica"],
            "SHA-256 canonico da base oficial nao confere.",
        )

        confronto = doc.get("confronto_base_legada", {})
        if confronto.get("presente"):
            _exigir(
                confronto["qtd_divergencias_conjunto"] == 0,
                f"Divergencias encontradas contra data/lotofacil.json: {confronto['divergencias_dezenas_conjunto']}",
            )

        # Ressalva 1.B: linhagem completa e ausencia de duplicados / preenchimento artificial
        _exigir(bool(doc.get("versao_sincronizador")), "Campo versao_sincronizador ausente.")
        _exigir(bool(doc.get("sha256_planilha_oficial_caixa")), "Hash da planilha oficial ausente.")
        _exigir(len(doc.get("registro_transformacoes", [])) >= 4, "Registro de transformacoes incompleto.")
        integridade = doc.get("relatorio_integridade_concursos", {})
        _exigir(integridade.get("qtd_ausentes") == 0, "Relatorio deve indicar 0 ausentes.")
        _exigir(integridade.get("qtd_duplicados") == 0, "Relatorio deve indicar 0 duplicados.")
        _exigir(all(rec["ordem_sorteio"] == [] for rec in concursos), "ordem_sorteio nao deve ser preenchida artificialmente na origem XLSX.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
