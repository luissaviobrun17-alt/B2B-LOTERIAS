"""Configurações e parâmetros matemáticos oficiais do Super Sete."""

TOTAL_COLUNAS = 7
DIGITOS_POR_COLUNA = 10
TOTAL_COMBINACOES_TEORICAS = 10_000_000
PRECO_APOSTA_SIMPLES = 2.50

PROBABILIDADES = {
    7: {"acertos": 7, "odds": 10_000_000, "prob": 1e-7, "nome": "Faixa 1 (7 acertos)"},
    6: {"acertos": 6, "odds": 158_730.16, "prob": 6.3e-6, "nome": "Faixa 2 (6 acertos)"},
    5: {"acertos": 5, "odds": 5_878.89, "prob": 1.701e-4, "nome": "Faixa 3 (5 acertos)"},
    4: {"acertos": 4, "odds": 391.93, "prob": 2.5515e-3, "nome": "Faixa 4 (4 acertos)"},
    3: {"acertos": 3, "odds": 43.55, "prob": 2.29635e-2, "nome": "Faixa 5 (3 acertos - R$ 5,00 fixo)"}
}

SOMA_ESPERADA_TEORICA = 31.5
DESVIO_ESPERADO_TEORICO = 7.60
CORTE_CENTROIDE_MIN = 16
CORTE_CENTROIDE_MAX = 47
MAX_CONSECUTIVOS_PADRAO = 3
HAMMING_MINIMO_PADRAO = 4

FRASE_OBRIGATORIA = (
    "Este motor não prevê o sorteio. Ele utiliza matemática, estatística, simulação "
    "e otimização para selecionar as combinações mais bem classificadas dentro dos critérios definidos. "
    "Nenhum método possui garantia de acerto em um sorteio aleatório."
)
