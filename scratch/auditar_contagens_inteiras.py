import sys
import math
import random
from collections import Counter
from pathlib import Path

CAMINHO_REPO = r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS"
if CAMINHO_REPO not in sys.path:
    sys.path.insert(0, CAMINHO_REPO)

from lotofacil_modo4.etapa2_funcao_objetivo import PERFIS_PESOS_ETAPA2
from lotofacil_modo4.etapa4_arquitetura_adaptativa import AvaliadorConstrutivoIncrementalEtapa4, _gerar_jogo_aleatorio_valido

def calcular_maior_sequencia(jogo):
    max_seq = 1
    atual = 1
    for i in range(len(jogo) - 1):
        if jogo[i + 1] == jogo[i] + 1:
            atual += 1
            if atual > max_seq:
                max_seq = atual
        else:
            atual = 1
    return max_seq

spec = {
    "quantidade_jogos": 1000,
    "tamanhos_jogos": (15,) * 1000,
    "pool": tuple(range(1, 26)),
    "fixas": (),
    "fixas_por_jogo": (),
    "bloqueadas": (),
    "livres_para_jogos": tuple(range(1, 26)),
    "pesos": PERFIS_PESOS_ETAPA2["padrao_modo4"],
    "tamanho_pool": 25,
    "espaco_admissivel": math.comb(25, 15),
    "modo_fixas": "fixas_todas_apostas",
}

def gerar_jogos_rapido(semente, teto_consecutivos):
    rng = random.Random(semente)
    av = AvaliadorConstrutivoIncrementalEtapa4(spec)
    tams = spec["tamanhos_jogos"]
    j = spec["quantidade_jogos"]
    livres = spec["livres_para_jogos"]
    fixas_j = spec["fixas_por_jogo"]
    cand_por_passo = max(2, 32000 // j)

    avaliacoes_efetivas = 0
    usados = set()
    total_tentativas = 0
    rejeitados_filtro = 0
    rejeitados_unicidade = 0
    admitidos = 0

    for idx_j, m_i in enumerate(tams):
        faltam = m_i - len(fixas_j)
        restantes_av = max(1, 32000 - avaliacoes_efetivas)
        limite_cands = min(cand_por_passo, restantes_av) if idx_j < j - 1 else restantes_av
        if idx_j == 0 and teto_consecutivos is None:
            limite_cands = min(limite_cands, 16)

        cands = []
        vistos = set()

        if faltam == 0:
            cands.append(fixas_j)
            admitidos += 1
        else:
            ord_menos = sorted(livres, key=lambda d: (av.u_counts[d], d))
            cg0 = tuple(sorted((*fixas_j, *ord_menos[:faltam])))
            total_tentativas += 1
            if teto_consecutivos is None or calcular_maior_sequencia(cg0) <= teto_consecutivos:
                if cg0 not in usados:
                    vistos.add(cg0)
                    cands.append(cg0)
                    admitidos += 1
                else:
                    rejeitados_unicidade += 1
            else:
                rejeitados_filtro += 1

            if len(ord_menos) > faltam and len(cands) < limite_cands:
                desloc = max(1, len(ord_menos) // 4)
                rot = ord_menos[desloc:] + ord_menos[:desloc]
                cg1 = tuple(sorted((*fixas_j, *rot[:faltam])))
                total_tentativas += 1
                if teto_consecutivos is None or calcular_maior_sequencia(cg1) <= teto_consecutivos:
                    if cg1 not in usados and cg1 not in vistos:
                        vistos.add(cg1)
                        cands.append(cg1)
                        admitidos += 1
                    else:
                        rejeitados_unicidade += 1
                else:
                    rejeitados_filtro += 1

            pesos_amostra = [1.0 / (1.0 + av.u_counts[d]) for d in livres]
            tent = 0
            max_tent = max(limite_cands * (15 if teto_consecutivos is not None else 6), 30)

            while len(cands) < limite_cands and tent < max_tent:
                tent += 1
                total_tentativas += 1
                escolhidos = []
                p_disp = list(livres)
                w_disp = list(pesos_amostra)
                for _ in range(faltam):
                    tot = sum(w_disp)
                    alvo = rng.random() * tot
                    acum = 0.0
                    pick = len(p_disp) - 1
                    for k, wk in enumerate(w_disp):
                        acum += wk
                        if acum >= alvo:
                            pick = k
                            break
                    escolhidos.append(p_disp.pop(pick))
                    w_disp.pop(pick)
                cg = tuple(sorted((*fixas_j, *escolhidos)))
                if cg not in usados and cg not in vistos:
                    if teto_consecutivos is None or calcular_maior_sequencia(cg) <= teto_consecutivos:
                        vistos.add(cg)
                        cands.append(cg)
                        admitidos += 1
                    else:
                        rejeitados_filtro += 1
                else:
                    rejeitados_unicidade += 1

        if not cands:
            for _ in range(200):
                total_tentativas += 1
                cg = _gerar_jogo_aleatorio_valido(rng, livres, fixas_j, m_i)
                if cg not in usados:
                    if teto_consecutivos is None or calcular_maior_sequencia(cg) <= teto_consecutivos:
                        cands.append(cg)
                        admitidos += 1
                        break
                    else:
                        rejeitados_filtro += 1
                else:
                    rejeitados_unicidade += 1

        escolhido = cands[0]
        melhor_f = -1.0
        if len(cands) > 1:
            for cg in cands:
                f_p = av.simular_adicao_jogo(cg)
                avaliacoes_efetivas += 1
                if f_p > melhor_f + 1e-12 or (abs(f_p - melhor_f) <= 1e-12 and cg < escolhido):
                    melhor_f = f_p
                    escolhido = cg
        else:
            avaliacoes_efetivas += 1

        av.adicionar_jogo(escolhido)
        usados.add(escolhido)

    # Contagem exata de pares
    total_pares = j * (j - 1) // 2
    hist = Counter()
    for i in range(j):
        si = set(av.jogos[i])
        for k in range(i + 1, j):
            hist[len(si & set(av.jogos[k]))] += 1

    return {
        "tentativas": total_tentativas,
        "rejeitados_filtro": rejeitados_filtro,
        "rejeitados_unicidade": rejeitados_unicidade,
        "admitidos": admitidos,
        "avaliacoes": avaliacoes_efetivas,
        "hist": dict(sorted(hist.items())),
        "soma_pares": sum(hist.values()),
        "soma_produtos": sum(k * v for k, v in hist.items()),
    }

print("Executando contagem inteira exata para os três cenários...")
for nome, teto in [("Baseline", None), ("Limite 5", 5), ("Limite 6", 6)]:
    r = gerar_jogos_rapido(2027, teto)
    print(f"\n--- {nome} ---")
    print(f"Tentativas: {r['tentativas']} = Admitidos({r['admitidos']}) + Rejeitados_Filtro({r['rejeitados_filtro']}) + Rejeitados_Unicidade({r['rejeitados_unicidade']})")
    print(f"Soma bate? {r['tentativas'] == r['admitidos'] + r['rejeitados_filtro'] + r['rejeitados_unicidade']}")
    print(f"Total de pares: {r['soma_pares']}")
    print(f"Soma dos produtos (k * count): {r['soma_produtos']}")
    media_exata = r['soma_produtos'] / r['soma_pares']
    print(f"Média exata: {media_exata:.12f}")
    for k, v in r['hist'].items():
        pct = (v / r['soma_pares']) * 100.0
        print(f"  k={k:2d}: {v:6d} pares ({pct:.6f}%)")
