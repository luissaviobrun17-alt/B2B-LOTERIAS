import os
import random
import sys
import time

BASE_DIR = r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lotofacil_modo4.etapa1_regras_oficiais import DEZENAS_DISPONIVEIS
from lotofacil_modo4.etapa2_funcao_objetivo import (
    avaliar_cobertura_subconjuntos_exata,
    avaliar_probabilidade_conjunta_carteira,
    avaliar_diversificacao_sobreposicao,
    avaliar_distribuicao_dezenas,
    avaliar_custo_beneficio,
    avaliar_estrutura_e_descritivo,
    validar_pool_e_restricoes,
    validar_pesos_objetivo,
    extrair_perfil_estrutural_jogo,
    validar_aposta_lotofacil,
)

random.seed(42)
J = 2000
universo = list(range(1, 26))
jogos = [tuple(sorted(random.sample(universo, 15))) for _ in range(J)]

print(f"--- DECOMPOSICAO TEMPORAL DA ETAPA 2 PARA J = {J} ---")

t0 = time.perf_counter()
jogos_validos = [validar_aposta_lotofacil(jg) for jg in jogos]
t_val = time.perf_counter() - t0
print(f"Validar apostas: {t_val:.4f} s")

t0 = time.perf_counter()
perfis_jogos = [extrair_perfil_estrutural_jogo(jg) for jg in jogos_validos]
t_perfis = time.perf_counter() - t0
print(f"Extrair perfis estruturais ({J} jogos): {t_perfis:.4f} s")

t0 = time.perf_counter()
meta_pool = validar_pool_e_restricoes(
    pool=DEZENAS_DISPONIVEIS,
    fixas=(),
    bloqueadas=(),
    modo_fixas="todos_os_jogos",
    tamanho_jogo=15,
)
pool_ord = meta_pool["pool"]
fixas_jogo_ord = meta_pool["fixas_por_jogo"]
t_pool = time.perf_counter() - t0
print(f"Validar pool e restricoes: {t_pool:.4f} s")

t0 = time.perf_counter()
aval_cov = avaliar_cobertura_subconjuntos_exata(jogos_validos, pool_ord, fixas_jogo_ord)
t_cov = time.perf_counter() - t0
print(f"Avaliar cobertura subconjuntos (t=1..4): {t_cov:.4f} s")

t0 = time.perf_counter()
aval_prob = avaliar_probabilidade_conjunta_carteira(jogos_validos, pool_ord, fixas_jogo_ord, perfis_jogos)
t_prob = time.perf_counter() - t0
print(f"Avaliar probabilidade conjunta: {t_prob:.4f} s")

t0 = time.perf_counter()
aval_div = avaliar_diversificacao_sobreposicao(jogos_validos, pool_ord, fixas_jogo_ord, perfis_jogos)
t_div = time.perf_counter() - t0
print(f"Avaliar diversificacao sobreposicao: {t_div:.4f} s")

t0 = time.perf_counter()
aval_dist = avaliar_distribuicao_dezenas(jogos_validos, pool_ord, fixas_jogo_ord)
t_dist = time.perf_counter() - t0
print(f"Avaliar distribuicao dezenas: {t_dist:.4f} s")

t0 = time.perf_counter()
aval_cb = avaliar_custo_beneficio(jogos_validos, pool_ord, fixas_jogo_ord, aval_cov)
t_cb = time.perf_counter() - t0
print(f"Avaliar custo beneficio: {t_cb:.4f} s")

t0 = time.perf_counter()
aval_est = avaliar_estrutura_e_descritivo(perfis_jogos)
t_est = time.perf_counter() - t0
print(f"Avaliar estrutura e descritivo: {t_est:.4f} s")
