# -*- coding: utf-8 -*-
"""
PROCEDIMENTO UNIFICADO DE HOMOLOGACAO INTEGRAL: LOTOMANIA MODO 4 (v1.2)
=======================================================================
Script mestre automatizado de verificacao estrita (fail-closed) em 7 etapas.
Implementado com zero instrucoes `assert` (100% compativel com `python -O`,
lancando `RuntimeError` explicito e encerrando com codigo de saida != 0 diante
de qualquer divergencia numerica, logica ou criptografica):

1. Validacao formal do nucleo matematico (toy model 6x5x5=150 configuracoes
   contadas dinamicamente com documentacao de escopo, casos-limite k=0, 25, 50
   e identidade analitica exata Delta V).
2. Recalculo estatistico rigoroso a partir dos 90 dados brutos pareados em
   `dados_brutos_90_saldos_consolidados.json` (com verificacao integral
   premios_C - premios_A == saldo_D em todas as 90 rodadas), discriminando
   proveniencia exploratoria (Bateria 1, N=30) vs confirmatoria sob pesos
   congelados (Baterias 2, 3, 4, N=60), teste t de Student para uma amostra
   sobre diferencas pareadas sob CRN com verificacao independente exata via
   Decimal de 100 digitos, e Teste Exato dos Sinais (unilateral e bilateral).
3. Reproducao integral das 189 etapas de selecao, 33 minimizadores conjuntos e
   7 empates algebricos exatos em Q.
4. Reproducao estrutural das carteiras sob alpha in {0.5, 1.0, 2.0} e recalculo
   dos hashes SHA-256 sob Protocolo v1 e Protocolo v2.
5. Execucao da suite completa de 20 testes unitarios automatizados.
6. Execucao dos 4 modulos de homologacao MODO 4 (selo em 10 cenarios, equivalencia
   com 15.120 Delta V + 33 minimizadores, zero fallback / resiliencia HTTP/API e
   matriz 1..10.000 em diretorio temporario sob esquema JSON 1.2.2) e inventario
   criptografico preliminar pre-assinatura pos-fechamento do log.
7. Emissao do parecer executavel final (7/7 etapas) com ressalva matematica
   obrigatoria e orientacao de assinatura final apos fechamento do log.
"""

from datetime import datetime, timezone
from decimal import Decimal, getcontext
import hashlib
import itertools
import json
import math
import os
import random
import shutil
import sys
import tempfile
import time
import unittest

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
TESTES_DIR = os.path.join(BASE_DIR, "testes")
if os.path.isdir(TESTES_DIR) and TESTES_DIR not in sys.path:
    sys.path.insert(0, TESTES_DIR)


def exigir(condicao: bool, mensagem: str) -> None:
    if condicao is not True:
        raise RuntimeError(f"FALHA FAIL-CLOSED DE HOMOLOGACAO: {mensagem}")


def _ts_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


def nCr(n: int, r: int) -> int:
    if r < 0 or r > n:
        return 0
    return math.comb(n, r)


def convolucao_hipergeometrica_bivariada(k: int, t1: int, t2: int) -> int:
    c_min = max(0, t1 - (50 - k), t2 - (50 - k), t1 + t2 - 20)
    c_max = min(k, t1, t2, 20, k - 20 + t1 + t2)
    if c_min > c_max:
        return 0
    total = 0
    for x11 in range(c_min, c_max + 1):
        total += (
            math.comb(k, x11)
            * math.comb(50 - k, t1 - x11)
            * math.comb(50 - k, t2 - x11)
            * math.comb(k, 20 - t1 - t2 + x11)
        )
    return total


def calcular_valor_p_student(t_stat: float, df: int) -> float:
    t_val = abs(t_stat)
    x = df / (df + t_val**2)
    a = df / 2.0
    b = 0.5
    log_B = math.lgamma(a) + math.lgamma(b) - math.lgamma(a + b)
    series_sum = 0.0
    term = 1.0
    for k in range(160):
        val = (a / (a + k)) * term * (x**k)
        series_sum += val
        term *= (0.5 + k) / (k + 1)
        if val < 1e-25 * series_sum:
            break
    p_two_tailed = (x**a) * series_sum / (a * math.exp(log_B))
    return min(1.0, max(0.0, p_two_tailed))


def calcular_student_decimal_exato(valores: list) -> dict:
    """
    Calculo independente de alta precisao (100 digitos decimais via Gauss-Legendre pi
    e expansao exata da Beta Incompleta Regularizada I_x(df/2, 1/2)) para teste t
    de Student de uma amostra sobre diferencas pareadas sob CRN.
    """
    getcontext().prec = 100
    n = len(valores)
    df = n - 1
    exigir(df % 2 == 1 and df >= 1, f"Esperado df impar >= 1 para formula Beta fechada, obtido {df}")

    a_agm = Decimal(1)
    b_agm = Decimal(1) / Decimal(2).sqrt()
    t_agm = Decimal(1) / Decimal(4)
    p_agm = Decimal(1)
    for _ in range(10):
        an = (a_agm + b_agm) / Decimal(2)
        b_agm = (a_agm * b_agm).sqrt()
        t_agm -= p_agm * (a_agm - an) * (a_agm - an)
        a_agm = an
        p_agm *= Decimal(2)
    pi_dec = (a_agm + b_agm) * (a_agm + b_agm) / (Decimal(4) * t_agm)

    n_dec = Decimal(n)
    decs = [Decimal(v) for v in valores]
    media = sum(decs) / n_dec
    var_amostral = sum((x - media) ** 2 for x in decs) / Decimal(df)
    s_d = var_amostral.sqrt()
    se = s_d / n_dec.sqrt()
    t_stat = media / se

    m = (df - 1) // 2
    x = Decimal(df) / (Decimal(df) + t_stat * t_stat)
    a_beta = Decimal(df) / Decimal(2)
    beta_val = (Decimal(math.comb(2 * m, m)) * pi_dec) / Decimal(4**m)

    soma_serie = Decimal(0)
    termo = Decimal(1)
    for k in range(300):
        parc = (termo * (x**k)) / (a_beta + Decimal(k))
        soma_serie += parc
        termo = termo * (Decimal("0.5") + Decimal(k)) / Decimal(k + 1)
        if abs(parc) < Decimal("1e-95"):
            break
    p_bilateral = (x**a_beta) * soma_serie / beta_val
    p_unilateral = p_bilateral / Decimal(2)
    return {
        "media": media,
        "s_d": s_d,
        "se": se,
        "t_stat": t_stat,
        "p_bilateral": p_bilateral,
        "p_unilateral": p_unilateral,
    }


print("=" * 95)
print("PROCEDIMENTO DE HOMOLOGACAO INTEGRAL EM 7 ETAPAS: LOTOMANIA MODO 4 v1.2 (FAIL-CLOSED)")
print(f"Inicio Global UTC: {_ts_utc()} | Modo Otimizado (-O ignora assert): Python {sys.version.split()[0]}")
print("=" * 95)

# -------------------------------------------------------------------------------------------------
# ETAPA 1: NUCLEO MATEMATICO (TOY MODEL, CASOS-LIMITE E DELTA V) COM BLOQUEIO FAIL-CLOSED
# -------------------------------------------------------------------------------------------------
t_e1 = time.perf_counter()
print(f"\n[ETAPA 1/7] Validacao Formal do Nucleo Matematico (Inicio UTC: {_ts_utc()}):")

N_toy, M_toy, D_toy = 10, 5, 4
univ_toy = set(range(N_toy))
sorteios_toy = list(itertools.combinations(univ_toy, D_toy))
divergencias_toy = 0
total_configuracoes_toy = 0
for k_toy in range(M_toy + 1):  # 6 valores: k in {0, 1, 2, 3, 4, 5}
    g1_toy = set(range(M_toy))
    g2_toy = set(range(M_toy - k_toy, 2 * M_toy - k_toy))
    for t1_toy in range(D_toy + 1):  # 5 valores: t1 in {0, 1, 2, 3, 4}
        for t2_toy in range(D_toy + 1):  # 5 valores: t2 in {0, 1, 2, 3, 4}
            total_configuracoes_toy += 1
            ex_count = sum(
                1
                for d in sorteios_toy
                if len(g1_toy.intersection(d)) == t1_toy
                and len(g2_toy.intersection(d)) == t2_toy
            )
            r11, r10, r01, r00 = (
                k_toy,
                M_toy - k_toy,
                M_toy - k_toy,
                N_toy - 2 * M_toy + k_toy,
            )
            c_min = max(0, t1_toy - r10, t2_toy - r01, t1_toy + t2_toy - D_toy)
            c_max = min(k_toy, t1_toy, t2_toy, D_toy, r00 - D_toy + t1_toy + t2_toy)
            form_count = 0
            if c_min <= c_max:
                for x in range(c_min, c_max + 1):
                    form_count += (
                        math.comb(r11, x)
                        * math.comb(r10, t1_toy - x)
                        * math.comb(r01, t2_toy - x)
                        * math.comb(r00, D_toy - t1_toy - t2_toy + x)
                    )
            if ex_count != form_count:
                divergencias_toy += 1

exigir(total_configuracoes_toy == 150, f"Esperadas 150 configuracoes no Toy Model (6x5x5), obtido {total_configuracoes_toy}")
exigir(divergencias_toy == 0, f"Auditoria falhou na Etapa 1: {divergencias_toy} divergencias no toy model.")
print(
    f"  Toy Model ({total_configuracoes_toy} configuracoes = 6 valores de k [0..5] x 5 valores de t1 x 5 valores de t2): "
    f"{divergencias_toy} divergencias encontradas -> CONFORME"
)

faixas_win = [0, 15, 16, 17, 18, 19, 20]
r_win_0 = sum(
    convolucao_hipergeometrica_bivariada(0, t1, t2)
    for t1 in faixas_win
    for t2 in faixas_win
)
r_win_50 = sum(
    convolucao_hipergeometrica_bivariada(50, t1, t2)
    for t1 in faixas_win
    for t2 in faixas_win
)
c50_20 = nCr(50, 20)
suporte_bilhete = sum(nCr(50, t) * nCr(50, 20 - t) for t in faixas_win)
exigir(r_win_0 == 2 * c50_20, f"Falha no caso-limite k=0: {r_win_0} != {2*c50_20}")
exigir(r_win_50 == suporte_bilhete, f"Falha no caso-limite k=50: {r_win_50} != {suporte_bilhete}")

total_espaco_k25 = sum(
    convolucao_hipergeometrica_bivariada(25, t1, t2)
    for t1 in range(21)
    for t2 in range(21)
)
exigir(total_espaco_k25 == math.comb(100, 20), f"Conservacao do espaco amostral em k=25 falhou: {total_espaco_k25}")
print("  Casos-Limite Lotomania (k=0, k=25 conservacao integral, k=50): CONFORME (100% identico)")

rnd_v = random.Random(42)
c19 = [set(rnd_v.sample(range(1, 101), 50)) for _ in range(19)]
u_v = {n: sum(1 for jg in c19 if n in jg) for n in range(1, 101)}
m_ant = sum(u_v.values()) / 100.0
v1 = sum((u_v[n] - m_ant) ** 2 for n in range(1, 101))
cand_v = set(rnd_v.sample(range(1, 101), 50))
u_nov = u_v.copy()
for n in cand_v:
    u_nov[n] += 1
m_nov = sum(u_nov.values()) / 100.0
v2 = sum((u_nov[n] - m_nov) ** 2 for n in range(1, 101))
exigir(abs((v2 - v1) - (2.0 * sum(u_v[n] - m_ant for n in cand_v) + 25.0)) < 1e-9, "Falha na identidade Delta V.")
print(f"  Identidade Delta V = 2*sum(u - m_ant) + 25: CONFORME | Duracao Etapa 1: {round(time.perf_counter()-t_e1, 3)}s")

# -------------------------------------------------------------------------------------------------
# ETAPA 2: RECALCULO ESTATISTICO RIGOROSO DOS 90 PARES BRUTOS INDIVIDUAIS
# -------------------------------------------------------------------------------------------------
t_e2 = time.perf_counter()
print(f"\n[ETAPA 2/7] Recalculo Estatistico dos 90 Pares Brutos Individuais (Inicio UTC: {_ts_utc()}):")
cam_brutos_90 = os.path.join(BASE_DIR, "dados_brutos_90_saldos_consolidados.json")
exigir(os.path.isfile(cam_brutos_90), f"Arquivo obrigatorio ausente: {cam_brutos_90}")
with open(cam_brutos_90, "r", encoding="utf-8") as f_br:
    dados_90 = json.load(f_br)

rodadas_90 = dados_90.get("rodadas", [])
exigir(len(rodadas_90) == 90, f"Esperadas 90 rodadas em dados_brutos_90_saldos_consolidados.json, obtido {len(rodadas_90)}")
for idx_r, row_r in enumerate(rodadas_90, start=1):
    exigir(row_r.get("rodada_global") == idx_r, f"Indice de rodada divergente: {row_r.get('rodada_global')}")
    exigir(isinstance(row_r.get("premios_C"), int) and isinstance(row_r.get("premios_A"), int), (
        f"Rodada {idx_r} sem contagem bruta inteira (premios_C, premios_A)."
    ))
    exigir(row_r["premios_C"] - row_r["premios_A"] == row_r["saldo_D"], (
        f"Divergencia premios_C - premios_A != saldo_D na rodada {idx_r}."
    ))

b1 = [r["saldo_D"] for r in rodadas_90 if r["bateria"] == 1]
b2 = [r["saldo_D"] for r in rodadas_90 if r["bateria"] == 2]
b3 = [r["saldo_D"] for r in rodadas_90 if r["bateria"] == 3]
b4 = [r["saldo_D"] for r in rodadas_90 if r["bateria"] == 4]
exigir(len(b1) == 30 and len(b2) == 20 and len(b3) == 20 and len(b4) == 20, "Tamanhos das baterias 1..4 invalidos.")

conf_60 = b2 + b3 + b4
exigir(len(conf_60) == 60 and all(x > 0 for x in conf_60), "Conjunto confirmatorio (60) invalido.")
soma_conf = sum(conf_60)
exigir(soma_conf == 18507, f"Soma confirmatoria incorreta: {soma_conf}")
m_conf = soma_conf / 60.0
exigir(abs(m_conf - 308.45) < 1e-9, "Media confirmatoria incorreta.")
var_conf = sum((x - m_conf) ** 2 for x in conf_60) / 59.0
s_conf = math.sqrt(var_conf)
se_conf = s_conf / math.sqrt(60.0)
t_conf = m_conf / se_conf
p_conf_bi = calcular_valor_p_student(t_conf, 59)
p_conf_uni = 0.5 * p_conf_bi
dec_conf = calcular_student_decimal_exato(conf_60)
exigir(
    abs(Decimal(str(p_conf_bi)) - dec_conf["p_bilateral"]) / dec_conf["p_bilateral"] < Decimal("1e-10"),
    f"Divergencia entre float e Decimal 100-digitos em conf_60: {p_conf_bi} vs {dec_conf['p_bilateral']}",
)
p_sinais_60_unilateral = 0.5**60
p_sinais_60_bilateral = 2.0 * (0.5**60)

print("  Delineamento: Teste t de Student de uma amostra sobre diferencas pareadas D_r = premios_C - premios_A sob CRN (50.000 sorteios/rodada)")
print("  Proveniencia: Bateria 1 (30 rodadas, seeds 1001..1030/3001..3030/50001..50030) = exploratoria/calibracao;")
print("                Baterias 2, 3 e 4 (60 rodadas, 3.000.000 sorteios) = parametros congelados (w_inter=30.0, w_uso=0.05).")
print("  Analise Confirmatoria (60 rodadas congeladas, 90/90 pares brutos integros verificados em JSON):")
print(f"    Saldo = +{soma_conf} | Media = +{m_conf:.4f} | s_D = {s_conf:.6f} | t(59) = {float(dec_conf['t_stat']):.6f}")
print(f"    Valor-p t de Student unilateral (H1: mu_D > 0):  {dec_conf['p_unilateral']:.6e}")
print(f"    Valor-p t de Student bilateral  (H1: mu_D != 0): {dec_conf['p_bilateral']:.6e}")
print(f"    Teste dos Sinais (60/60) unilateral (0.5^60):    {p_sinais_60_unilateral:.6e}")
print(f"    Teste dos Sinais (60/60) bilateral (2*0.5^60):   {p_sinais_60_bilateral:.6e}")
exigir(abs(t_conf - float(dec_conf["t_stat"])) < 1e-9, "Divergencia em t_conf.")
exigir(abs(p_sinais_60_bilateral - 2.0 * p_sinais_60_unilateral) < 1e-30, "Divergencia no teste dos sinais 60.")

glob_90 = b1 + conf_60
exigir(len(glob_90) == 90 and all(x > 0 for x in glob_90), "Conjunto global (90) invalido.")
soma_glob = sum(glob_90)
exigir(soma_glob == 28657, f"Soma global incorreta: {soma_glob}")
m_glob = soma_glob / 90.0
var_glob = sum((x - m_glob) ** 2 for x in glob_90) / 89.0
s_glob = math.sqrt(var_glob)
se_glob = s_glob / math.sqrt(90.0)
t_glob = m_glob / se_glob
p_glob_bi = calcular_valor_p_student(t_glob, 89)
dec_glob = calcular_student_decimal_exato(glob_90)
exigir(
    abs(Decimal(str(p_glob_bi)) - dec_glob["p_bilateral"]) / dec_glob["p_bilateral"] < Decimal("1e-10"),
    f"Divergencia entre float e Decimal 100-digitos em glob_90: {p_glob_bi} vs {dec_glob['p_bilateral']}",
)
p_sinais_90_unilateral = 0.5**90
p_sinais_90_bilateral = 2.0 * (0.5**90)

print("  Analise Historica Global (90 rodadas = exploratoria + congeladas):")
print(f"    Saldo = +{soma_glob} | Media = +{m_glob:.4f} | s_D = {s_glob:.6f} | t(89) = {float(dec_glob['t_stat']):.6f}")
print(f"    Valor-p t de Student unilateral (H1: mu_D > 0):  {dec_glob['p_unilateral']:.6e}")
print(f"    Valor-p t de Student bilateral  (H1: mu_D != 0): {dec_glob['p_bilateral']:.6e}")
print(f"    Teste dos Sinais (90/90) unilateral (0.5^90):    {p_sinais_90_unilateral:.6e}")
print(f"    Teste dos Sinais (90/90) bilateral (2*0.5^90):   {p_sinais_90_bilateral:.6e}")
print("  Nota Metodologica e Ressalva Matematica:")
print("    Os valores-p acima medem vantagem combinatoria conjunta observada em unidades Monte Carlo")
print("    independentes sob CRN contra carteiras uniformes aleatorias (nao se referem a concursos reais")
print("    nem garantem ganho financeiro futuro). O sistema nao preve resultados futuros nem altera a")
print("    probabilidade matematica individual de premiacao de qualquer bilhete.")
exigir(abs(p_sinais_90_bilateral - 2.0 * p_sinais_90_unilateral) < 1e-39, "Divergencia no teste dos sinais 90.")
print(f"  Status Estatistico: CONFORME (Decimal 100-digitos validado) | Duracao Etapa 2: {round(time.perf_counter()-t_e2, 3)}s")

# -------------------------------------------------------------------------------------------------
# ETAPA 3: REPRODUCAO INTEGRAL DAS 189 ETAPAS DE INVARIANCIA E 7 EMPATES EXATOS
# -------------------------------------------------------------------------------------------------
t_e3 = time.perf_counter()
print(f"\n[ETAPA 3/7] Reproducao da Invariancia do Minimizador (189 Etapas x 79 Concorrentes) (Inicio UTC: {_ts_utc()}):")
from demonstracao_invariancia_argmin import analisar_fielmente

relatorio_invariancia = analisar_fielmente()

tot_etapas = 0
minimos_estritos = 0
empates_exatos_Q = 0
empates_registrados = []

for rodada_idx, etapas in relatorio_invariancia:
    for e in etapas:
        tot_etapas += 1
        m05 = e["min_margem_05"]
        m20 = e["min_margem_20"]
        if m05 > 1e-9 and m20 > 1e-9:
            minimos_estritos += 1
        elif abs(m05) <= 1e-9 and abs(m20) <= 1e-9:
            empates_exatos_Q += 1
            empates_registrados.append(
                (tot_etapas, rodada_idx, e["etapa"], e["best_A"], e["best_B"], e["second_A"], e["second_B"])
            )
        else:
            raise RuntimeError(f"Falha de invariancia na etapa {tot_etapas}: margem negativa!")

print(f"  Total de Etapas Analisadas:                {tot_etapas} (exigido: exatamente 189)")
print(f"  Minimos Estritos (margem > 0):             {minimos_estritos} ({minimos_estritos/tot_etapas*100:.2f}%)")
print(f"  Empates Algebricos Exatos em Q:            {empates_exatos_Q} ({empates_exatos_Q/tot_etapas*100:.2f}%)")
exigir(tot_etapas == 189, f"Quantidade de etapas incorreta: {tot_etapas}")
exigir(minimos_estritos == 182, f"Quantidade de minimos estritos incorreta: {minimos_estritos}")
exigir(empates_exatos_Q == 7, f"Quantidade de empates incorreta: {empates_exatos_Q}")

for step_g, r_idx, b_idx, a1, b1_val, a2, b2_val in empates_registrados:
    delta_A = abs(a2 - a1)
    delta_B = abs(b2_val - b1_val)
    print(
        f"    Etapa {step_g:3d} (Rodada {r_idx}, Bilhete {b_idx}): Delta A = {delta_A:.6f}, Delta B = {delta_B:.6f} -> Delta C(alpha) = 0 identico"
    )
    exigir(delta_A < 1e-9 and delta_B < 1e-9, f"Divergencia no empate da etapa {step_g}!")

print(f"  Status Invariancia: CONFORME (182 minimos estritos e 7 empates exatos) | Duracao Etapa 3: {round(time.perf_counter()-t_e3, 3)}s")

# -------------------------------------------------------------------------------------------------
# ETAPA 4: RECALCULO DOS HASHES SHA-256 E COMPARACAO ESTRUTURAL DAS CARTEIRAS
# -------------------------------------------------------------------------------------------------
t_e4 = time.perf_counter()
print(f"\n[ETAPA 4/7] Recalculo dos Hashes SHA-256 sob Protocolos v1 e v2 (Inicio UTC: {_ts_utc()}):")
from teste_sensibilidade_pesos import gerar_carteira_custom

hashes_auditados_v1 = [
    "a98c0b0267b1c2d91c630b363bb9be6744dd1d2a6d6943d447f869d705844f0f",
    "c5c3f21ca9bee8ad107d169619763f6a6e527b33e08d343423feabc4be5fbb71",
    "8a50e329b767a1a0f7394646265d408d47a16e2dedd1194e749fb286c77b035e",
    "5d6579b2f452eb826fe702017875c24624552b187563223b874d4c4a884ff07b",
    "560233f78dbdc071c4cf41005d7aa98ce507b30e073683b022492a73382b9f5c",
    "56ca8dd40c00e11b907a740179fd4fbc851b5a0b4fd0c9be4cd96c1523583455",
    "a9abe41b8d391690c34c4c25f6cdb44455c1d1b175eb3e0730c369b078c797bf",
    "ccb4390a4a9383bf7b20e662817b4360b51782e503d163ebd8b806903910c13c",
    "dbf05f13b93f5d9b849f67ef927ee640101657b0f22eebc1583ffe2a6086c3f0",
    "d5faaad0be1cb03cc471d4e94f39491a5106e565f8198889cf865d2059ce8480",
]

hashes_auditados_v2 = [
    "31a34473b0fe1e09f00dca01cebccc2a96abc59331bb472df926d2735a3b211f",
    "a9764997aafb36c8357b9dde03880e0371873899a55b1c8953924c06aded9064",
    "8e0470f2c55fbee21074a1932557fffa0a71a3116856965d2397d180dc019d10",
    "2131a62d501d235e039693aef18cfae839adebe083e8423cdc81a871f15cd55f",
    "0a22ae4b8e28f9bebfec4af98fff26775f29403e55e5ee71bfae718628705d2c",
    "e527bf00e3f295476561be3892f69b4c076561b0192fad389cb70666c699caba",
    "fbb9081b8ec614f97c146842a1a81c64909fa84e1dfe732d927972b426362198",
    "ba553f4a1f3be3b8f981bca7db9fb25f0249f056eb0f9451ce0c292ed7b984cf",
    "5320296decd82a10bd4613625407c578bb32b62edce319b936019a6d2ef7f1c8",
    "8fcf590b3767542663588bda426c35221f8debdfd09bb512c298c083106d21b1",
]

for r in range(1, 11):
    seed_c = 330000 + r
    c_padrao = gerar_carteira_custom(30.0, 0.05, seed=seed_c)
    c_meios = gerar_carteira_custom(15.0, 0.025, seed=seed_c)
    c_dobro = gerar_carteira_custom(60.0, 0.10, seed=seed_c)

    exigir(c_padrao == c_meios == c_dobro, f"Falha na identidade estrutural da rodada {r}!")

    hv1_p = hashlib.sha256(json.dumps(c_padrao).encode("utf-8")).hexdigest()
    hv1_m = hashlib.sha256(json.dumps(c_meios).encode("utf-8")).hexdigest()
    hv1_d = hashlib.sha256(json.dumps(c_dobro).encode("utf-8")).hexdigest()
    exigir(hv1_p == hv1_m == hv1_d == hashes_auditados_v1[r - 1], f"Divergencia no hash v1 da rodada {r}!")

    hv2_p = hashlib.sha256(json.dumps(c_padrao, separators=(",", ":")).encode("utf-8")).hexdigest()
    hv2_m = hashlib.sha256(json.dumps(c_meios, separators=(",", ":")).encode("utf-8")).hexdigest()
    hv2_d = hashlib.sha256(json.dumps(c_dobro, separators=(",", ":")).encode("utf-8")).hexdigest()
    exigir(hv2_p == hv2_m == hv2_d == hashes_auditados_v2[r - 1], f"Divergencia no hash v2 da rodada {r}!")

print("  Identidade Estrutural das 10 Carteiras sob alpha in {0.5, 1.0, 2.0}: 10/10 CONFORME")
print(f"  Status Hashes (v1 e v2): CONFORME | Duracao Etapa 4: {round(time.perf_counter()-t_e4, 3)}s")

# -------------------------------------------------------------------------------------------------
# ETAPA 5: EXECUCAO DA SUITE COMPLETA DE 20 TESTES UNITARIOS AUTOMATIZADOS
# -------------------------------------------------------------------------------------------------
t_e5 = time.perf_counter()
print(f"\n[ETAPA 5/7] Execucao da Suite Completa de 20 Testes Unitarios (Inicio UTC: {_ts_utc()}):")
import test_validacao_matematica_rwin
import test_motor_lotomania
import test_motor_lotomania_evolution

loader = unittest.TestLoader()
suite = unittest.TestSuite()
suite.addTests(loader.loadTestsFromModule(test_validacao_matematica_rwin))
suite.addTests(loader.loadTestsFromModule(test_motor_lotomania))
suite.addTests(loader.loadTestsFromModule(test_motor_lotomania_evolution))

runner = unittest.TextTestRunner(verbosity=1)
resultado_testes = runner.run(suite)

print(
    f"  Testes Executados: {resultado_testes.testsRun} | Falhas: {len(resultado_testes.failures)} | Erros: {len(resultado_testes.errors)}"
)
exigir(resultado_testes.wasSuccessful() and resultado_testes.testsRun == 20, "Falha na execucao da suite de 20 testes unitarios.")
print(f"  Status Testes Unitarios: CONFORME (20/20 aprovados) | Duracao Etapa 5: {round(time.perf_counter()-t_e5, 3)}s")

# -------------------------------------------------------------------------------------------------
# ETAPA 6: VERIFICACAO CRIPTOGRAFICA ED25519, RASTREAMENTO, SEM FALLBACK E MATRIZ 1..10.000
# -------------------------------------------------------------------------------------------------
t_e6 = time.perf_counter()
print(f"\n[ETAPA 6/7] Verificacao do Selo Ed25519 (10 cenarios), Equivalencia (15.120 Delta V + 33 minimizadores), Zero Fallback e Matriz 1..10.000 (Inicio UTC: {_ts_utc()}):")
from test_modo4_selo import executar_testes_selo
from test_modo4_equivalencia import executar_testes_equivalencia
from test_modo4_sem_fallback import executar_testes_sem_fallback
from test_modo4_matriz_carteiras import executar_matriz_carteiras
from verificador_selo_modo4 import calcular_sha256_arquivo

res_selo = executar_testes_selo()
exigir(
    res_selo["sucesso"] is True
    and res_selo["cenarios_adulteracao_testados"] == 10
    and res_selo["todos_cenarios_zero_jogos_confirmados"] is True,
    "Falha nos 10 cenarios do teste de selo Ed25519.",
)
sha_man = res_selo["selo_oficial"]["sha256_manifesto"]
print(f"  Selo Ed25519 (10 cenarios incluindo ausencia/chave incompativel/0 jogos): CONFORME (Manifesto: {sha_man})")

res_equiv = executar_testes_equivalencia()
exigir(res_equiv["sucesso"] is True, "Falha em executar_testes_equivalencia.")
exigir(res_equiv["total_etapas_verificadas"] == 189, "Divergencia em 189 etapas.")
exigir(res_equiv["empates_exatos_q_reproduzidos"] == 7, "Divergencia em 7 empates em Q.")
exigir(res_equiv["total_minimizadores_conjuntos_empates"] == 33, "Divergencia nos 33 minimizadores conjuntos.")
exigir(res_equiv["total_verificacoes_exatas_delta_v"] == 15120, "Divergencia nas 15.120 verificacoes Delta V.")
exigir(res_equiv["historico_geracao"] is None, "historico_geracao deve ser None.")
exigir(res_equiv["filtro_repeticao_ultimo_concurso_ativo"] is False, "Filtro ultimo concurso deve ser False.")
print(
    f"  Equivalencia Registro a Registro (MotorLotomaniaModo4): CONFORME "
    f"({res_equiv['total_etapas_verificadas']} etapas, {res_equiv['total_candidatos_intermediarios_verificados']} candidatos, "
    f"33 minimizadores conjuntos em Q, 15.120 verificacoes exatas Delta V, historico=None)"
)

res_nofallback = executar_testes_sem_fallback()
exigir(res_nofallback["sucesso"] is True, "Falha em executar_testes_sem_fallback.")
exigir(res_nofallback["violacoes_fallback_encontradas"] == 0, "Violacoes fallback > 0.")
exigir(res_nofallback["teste_api_desligada_zero_jogos"]["jogos_gerados"] == 0, "API desligada gerou jogos.")
exigir(all(res_nofallback["cenarios_resiliencia_http"].values()), "Falha na resiliencia HTTP.")
exigir(all(res_nofallback["cenarios_negativos_api"].values()), "Falha nos cenarios negativos API.")
print("  Proibicao de Fallback JS e Resiliencia API (offline/timeout/500/503/422/incompleta = 0 jogos): CONFORME")

caminho_rel_raiz = os.path.join(BASE_DIR, "relatorio_matriz_modo4.json")
caminho_rel_historico = os.path.join(BASE_DIR, "relatorio_matriz_modo4_historico_anterior.json")
if os.path.isfile(caminho_rel_raiz):
    shutil.copy2(caminho_rel_raiz, caminho_rel_historico)

with tempfile.TemporaryDirectory(prefix="homologacao_modo4_v1_2_") as tmpdir_homolog:
    caminho_rel_temp = os.path.join(tmpdir_homolog, "relatorio_matriz_modo4.json")
    exigir(not os.path.exists(caminho_rel_temp), "Relatorio temporario nao deveria existir antes da execucao!")

    executar_matriz_carteiras(caminho_saida=caminho_rel_temp, atualizar_raiz=True)

    exigir(os.path.isfile(caminho_rel_temp), "Relatorio temporario nao foi gerado pela execucao corrente!")
    with open(caminho_rel_temp, "r", encoding="utf-8") as f_rel:
        rel_matriz = json.load(f_rel)

exigir(rel_matriz["sucesso"] is True, "Falha no status sucesso do relatorio matriz.")
exigir(rel_matriz["versao_esquema_relatorio"] == "1.2.2", f"Esquema esperado '1.2.2', obtido {rel_matriz['versao_esquema_relatorio']!r}")
meta_exec = rel_matriz["metadados_execucao"]
exigir(meta_exec["gerado_em_diretorio_temporario"] is True, "Relatorio deve ser gerado em diretorio temporario.")
exigir(meta_exec["caminho_saida_relatorio"] == caminho_rel_temp, "Caminho temporario diverge no relatorio.")
exigir(meta_exec["sha256_relatorio_temporario_e_persistente_identicos"] is True, "Sinalizador de paridade do relatorio persistente invalido.")
exigir(
    meta_exec["referencia_oficial_motor"]["arquivo_fisico_oficial"] == "motor_lotomania.py",
    "Nome do arquivo oficial de referencia diverge de motor_lotomania.py.",
)

hashes_fonte_rel = meta_exec["hashes_sha256_codigo_fonte"]
arquivos_fonte_obrigatorios = [
    ("motor_lotomania_modo4.py", os.path.join(BASE_DIR, "motor_lotomania_modo4.py")),
    ("verificador_selo_modo4.py", os.path.join(BASE_DIR, "verificador_selo_modo4.py")),
    ("manifesto_modo4.json", os.path.join(BASE_DIR, "manifesto_modo4.json")),
    ("manifesto_modo4.sig", os.path.join(BASE_DIR, "manifesto_modo4.sig")),
    ("chave_publica_modo4.pem", os.path.join(BASE_DIR, "chave_publica_modo4.pem")),
    ("data/lotomania.json", os.path.join(BASE_DIR, "data", "lotomania.json")),
    ("dados_brutos_90_saldos_consolidados.json", os.path.join(BASE_DIR, "dados_brutos_90_saldos_consolidados.json")),
    ("motor_lotomania.py", os.path.join(BASE_DIR, "motor_lotomania.py")),
    ("procedimento_homologacao_integral.py", os.path.abspath(__file__)),
    ("testes/test_modo4_matriz_carteiras.py", os.path.join(BASE_DIR, "testes", "test_modo4_matriz_carteiras.py")),
    ("testes/test_modo4_selo.py", os.path.join(BASE_DIR, "testes", "test_modo4_selo.py")),
    ("testes/test_modo4_equivalencia.py", os.path.join(BASE_DIR, "testes", "test_modo4_equivalencia.py")),
    ("testes/test_modo4_sem_fallback.py", os.path.join(BASE_DIR, "testes", "test_modo4_sem_fallback.py")),
]
for arq_rel, camino_disco in arquivos_fonte_obrigatorios:
    exigir(arq_rel in hashes_fonte_rel, f"Arquivo obrigatorio '{arq_rel}' ausente em hashes_sha256_codigo_fonte.")
    sha_disco = calcular_sha256_arquivo(camino_disco)
    exigir(
        hashes_fonte_rel.get(arq_rel) == sha_disco,
        f"Hash de codigo-fonte no relatorio ({arq_rel}) diverge do arquivo em disco!",
    )

tamanhos_validados = [int(k) for k in rel_matriz["matriz_resultados"].keys()]
chaves_esquema_ref = set(rel_matriz["matriz_resultados"]["1"].keys())
exigir("hash_carteira_v1" in chaves_esquema_ref and "hash_carteira_v2" in chaves_esquema_ref, "Hashes de carteira ausentes.")

for t_obrig in [1, 2, 10, 20, 50, 80, 100, 500, 1000, 5000, 10000]:
    exigir(t_obrig in tamanhos_validados, f"Tamanho obrigatorio {t_obrig} ausente na matriz!")
    item_t = rel_matriz["matriz_resultados"][str(t_obrig)]
    exigir(set(item_t.keys()) == chaves_esquema_ref, f"Esquema JSON inconsistente em J={t_obrig}!")
    exigir(item_t["equivalente_referencia"] is True, f"Equivalencia nao comprovada para J={t_obrig}!")
    exigir(item_t["reprodutibilidade_confirmada"] is True, f"Reprodutibilidade nao confirmada para J={t_obrig}!")
    exigir(item_t["serializacao_json_estrita_ok"] is True, f"Serializacao JSON falhou para J={t_obrig}!")
    if t_obrig <= 1000:
        exigir(item_t["equivalencia_integral_direta_comprovada"] is True, f"Comparacao direta ausente em J={t_obrig}!")
        exigir(item_t["metodo_equivalencia"] == "comparacao_integral_direta_motor_referencia", "Metodo inesperado.")
    else:
        exigir(item_t["equivalencia_integral_direta_comprovada"] is False, f"Falso positivo direto em J={t_obrig}!")
        exigir(item_t["equivalencia_amostral_alto_volume_comprovada"] is True, "Amostragem ausente em alto volume!")
        exigir(
            item_t["metodo_equivalencia"] == "invariancia_prefixo_ate_1000_e_auditoria_amostral_estagios_reais",
            "Metodo de alto volume inesperado.",
        )

exigir(rel_matriz["teste_reinicializacao_subprocesso"]["sucesso"] is True, "Falha na reinicializacao em subprocesso.")
comp_bm = rel_matriz["comparacao_bitmask_histograma_referencia"]
exigir(comp_bm["sucesso"] is True, "Falha na comparacao bitmask vs referencia.")
exigir(comp_bm["total_candidatos_comparados_contra_set_intersection"] == 560, "Esperados 560 sinteticos.")
exigir(comp_bm["auditoria_trajetoria_real_seed_330001"]["total_candidatos_reais_comparados"] == 1600, "Esperados 1600 reais.")
exigir(comp_bm["total_combinado_avaliacoes_swar_vs_set_intersection"] == 2160, "Esperados 2160 combinados.")
fidelidade_prng = comp_bm["comprovacao_fidelidade_reconstrucao_prng"]
exigir(
    fidelidade_prng["deriva_prng_ao_longo_de_10000_jogos"] == 0,
    "Deriva de PRNG detectada na trajetoria de 10.000 jogos!",
)
exigir(
    fidelidade_prng["identidade_100pct_contra_trace_interno"] is True
    and fidelidade_prng["candidatos_confrontados_contra_trace_interno_j20"]
    == fidelidade_prng["estagios_trace_confrontados_j20"] * 80,
    "Falha na confrontacao de candidatos reconstruidos contra trace interno!",
)
exigir(
    fidelidade_prng["estagios_gulosos_verificados_em_j10000"]
    == 10000 - fidelidade_prng["idx_inicio_greedy"],
    "Quantidade de estagios gulosos verificados em J=10.000 inconsistente!",
)

print(
    f"  Relatorio Novo Gerado ao Vivo em TempDir (Esquema: 1.2.2, ID: {meta_exec['execucao_id']}, "
    f"Duracao: {meta_exec['duracao_total_bateria_s']}s): CONFORME"
)
print(
    f"  Comparacao Integral Direta contra Referencia ate 1.000 Jogos "
    f"({rel_matriz['tamanhos_comparacao_integral_direta_referencia']}): CONFORME"
)
print(
    f"  Auditoria Amostral de Alto Volume (560 sinteticos + 1.600 reais = 2.160 candidatos, "
    f"0 divergencias, {fidelidade_prng['candidatos_confrontados_contra_trace_interno_j20']} candidatos trace, "
    f"0 deriva PRNG em {fidelidade_prng['estagios_gulosos_verificados_em_j10000']} estagios) "
    f"e Reinicializacao a Frio: CONFORME"
)

from gerar_manifesto_evidencia_execucao import gerar_e_assinar_manifesto_evidencia
res_man_pre = gerar_e_assinar_manifesto_evidencia("", assinar=False, exigir_assinatura=False)
exigir(res_man_pre["sucesso"] is True, "Falha ao inventariar artefatos da execucao.")
print(
    f"  [PRELIMINAR - LOG AINDA ABERTO] Inventario pre-fechamento preparado "
    f"(Relatorio SHA-256: {res_man_pre['sha256_relatorio_matriz_modo4_json']}, "
    f"Total Modulos Inventariados: {res_man_pre['total_arquivos_fonte_inventariados']}). "
    f"A assinatura Ed25519 definitiva sera executada apos o fechamento do log na Etapa 7."
)
print(f"  Duracao Etapa 6: {round(time.perf_counter()-t_e6, 3)}s")

# -------------------------------------------------------------------------------------------------
# ETAPA 7: EMISSAO DO PARECER CONCLUSIVO DE HOMOLOGACAO INTEGRAL (7 ETAPAS)
# -------------------------------------------------------------------------------------------------
t_e7 = time.perf_counter()
print(f"\n[ETAPA 7/7] Emissao do Parecer Conclusivo da Arquitetura Isolada e Selada (UTC: {_ts_utc()}):")
print("=" * 95)
print("PARECER TECNICO CONCLUSIVO: HOMOLOGACAO INTEGRAL MODO 4 v1.2 EXECUTADA COM EXITO (7/7 ETAPAS)")
print(f"Execucao ID: {meta_exec['execucao_id']} | Relatorio SHA-256: {res_man_pre['sha256_relatorio_matriz_modo4_json']}")
print("Ressalva Matematica Obrigatoria: O sistema nao preve resultados futuros nem altera a")
print("probabilidade matematica individual de premiacao de qualquer bilhete. Seu objetivo e")
print("otimizar a distribuicao combinatoria dos bilhetes de uma carteira, buscando reduzir a")
print("redundancia entre eventos premiados e melhorar a cobertura conjunta observada.")
print(f"Fim Global UTC: {_ts_utc()} | Duracao Etapa 7: {round(time.perf_counter()-t_e7, 4)}s")
print("=" * 95)
