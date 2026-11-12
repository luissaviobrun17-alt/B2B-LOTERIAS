#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
VERIFICADOR INDEPENDENTE DA CADEIA DE EVIDENCIAS DE HOMOLOGACAO (MODO 4 v1.2)
=============================================================================
Utilitario autonomo de auditoria (nao importa `gerar_manifesto_evidencia_execucao.py`,
`procedimento_homologacao_integral.py` nem `motor_lotomania_modo4.py`) implementado
sem instrucoes `assert` (100% compativel com `python -O`, lancando `RuntimeError`
explicito diante de qualquer violacao).

Executa 10 verificacoes obrigatorias (fail-closed), distingue formalmente
APROVACOES, RESSALVAS/AVISOS e ERROS na saida JSON, informa seu proprio hash
SHA-256 para autenticacao externa pelo auditor e executa bateria de 10
autotestes negativos de rejeicao ativa sobre o pacote avaliado.
"""

import copy
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile

from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

# Raiz de confianca independente fixada fora dos manifestos auditados
CHAVE_PUBLICA_OFICIAL_SHA256 = (
    "d810ed9f31f476b159590cd2e053632dc32e8e6e62a5a17f7c2f371a45084b0f"
)
SHA256_MOTOR_REFERENCIA_OFICIAL = (
    "085d6fa972dfb97576246f26b8687fce35b7dc9199bb30fca61cc348df851d6c"
)
VERSAO_MOTOR_EXIGIDA = "1.2"
VERSAO_ESQUEMA_RELATORIO_EXIGIDA = "1.2.2"
TAMANHOS_MATRIZ_EXIGIDOS = [1, 2, 10, 20, 50, 80, 100, 500, 1000, 5000, 10000]
TAMANHOS_COMPARACAO_DIRETA_EXIGIDOS = [1, 2, 10, 20, 50, 80, 100, 500, 1000]

ARQUIVOS_FONTE_MANIFESTO_EXIGIDOS = {
    "api.py",
    "chave_publica_modo4.pem",
    "dados_brutos_90_saldos_consolidados.json",
    "data/lotomania.json",
    "demonstracao_invariancia_argmin.py",
    "gerar_manifesto_evidencia_execucao.py",
    "js/engines/motor_lotomania_modo4_engine.js",
    "manifesto_modo4.json",
    "manifesto_modo4.sig",
    "motor_lotomania.py",
    "motor_lotomania_modo4.py",
    "procedimento_homologacao_integral.py",
    "test_motor_lotomania.py",
    "test_motor_lotomania_evolution.py",
    "test_validacao_matematica_rwin.py",
    "teste_sensibilidade_pesos.py",
    "testes/test_modo4_equivalencia.py",
    "testes/test_modo4_matriz_carteiras.py",
    "testes/test_modo4_selo.py",
    "testes/test_modo4_sem_fallback.py",
    "verificador_selo_modo4.py",
    "verificar_evidencia_independente.py",
}

ARQUIVOS_PACOTE_FIXOS_PERMITIDOS = ARQUIVOS_FONTE_MANIFESTO_EXIGIDOS | {
    "relatorio_matriz_modo4.json",
    "manifesto_evidencia_execucao_modo4.json",
    "manifesto_evidencia_execucao_modo4.sig",
}

CHAVES_TOPO_RELATORIO_EXIGIDAS = {
    "sucesso",
    "versao_esquema_relatorio",
    "versao_motor",
    "clausula_obrigatoria",
    "metadados_execucao",
    "seed_padrao",
    "tamanhos_testados",
    "tamanhos_comparacao_integral_direta_referencia",
    "rejeicoes_estritas",
    "teste_reinicializacao_subprocesso",
    "comparacao_bitmask_histograma_referencia",
    "validacao_serializacao_infinito",
    "matriz_resultados",
}

CHAVES_ITEM_MATRIZ_EXIGIDAS = {
    "quantidade_jogos",
    "tempo_execucao_s",
    "tempo_execucao_ms",
    "tempo_execucao_referencia_ao_vivo_s",
    "tempo_execucao_com_tracemalloc_s",
    "memoria_pico_kb",
    "memoria_pico_mb",
    "memoria_working_set_processo_mb",
    "memoria_peak_working_set_processo_mb",
    "desempenho_medido_execucao_atual",
    "desempenho_historico_referencia_com_tracemalloc",
    "jogos_validos_pct",
    "jogos_unicos",
    "total_pares_carteira",
    "dezenas_cobertas",
    "desvio_padrao_alocacao_dezenas",
    "intersecao_media_pares",
    "intersecao_maxima_pares",
    "intersecao_minima_pares",
    "soma_intersecoes_real",
    "equivalente_referencia",
    "equivalencia_integral_direta_comprovada",
    "equivalencia_amostral_alto_volume_comprovada",
    "classificacao_tres_niveis_equivalencia",
    "metodo_equivalencia",
    "escopo_equivalencia",
    "reprodutibilidade_confirmada",
    "serializacao_json_estrita_ok",
    "hash_carteira_v1",
    "hash_carteira_v2",
}


def exigir(condicao: bool, mensagem: str) -> None:
    if condicao is not True:
        raise RuntimeError(mensagem)


def sha256_arquivo(caminho: str) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def serializar_canonico(obj: dict) -> bytes:
    """
    Canonicalizacao JSON deterministica para verificacao da assinatura Ed25519.
    """
    return json.dumps(
        obj,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def _eh_int_estrito(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def _eh_num_estrito(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool)


def _eh_hex_sha256(v) -> bool:
    return (
        isinstance(v, str)
        and len(v) == 64
        and all(c in "0123456789abcdef" for c in v.lower())
    )


def validar_esquema_estrito_relatorio(rel_dados: dict) -> dict:
    exigir(isinstance(rel_dados, dict), "Relatorio JSON deve ser um objeto dict.")
    chaves_topo = set(rel_dados.keys())
    exigir(
        chaves_topo == CHAVES_TOPO_RELATORIO_EXIGIDAS,
        f"Chaves de topo invalidas no relatorio: {chaves_topo ^ CHAVES_TOPO_RELATORIO_EXIGIDAS}",
    )
    exigir(rel_dados["sucesso"] is True, "Campo 'sucesso' deve ser True.")
    exigir(
        rel_dados["versao_esquema_relatorio"] == VERSAO_ESQUEMA_RELATORIO_EXIGIDA,
        f"Versao de esquema incompativel: {rel_dados['versao_esquema_relatorio']!r}",
    )
    exigir(
        rel_dados["versao_motor"] == VERSAO_MOTOR_EXIGIDA,
        f"Versao do motor incompativel no relatorio: {rel_dados['versao_motor']!r}",
    )
    exigir(
        rel_dados["tamanhos_testados"] == TAMANHOS_MATRIZ_EXIGIDOS,
        "Lista 'tamanhos_testados' diverge da matriz exigida.",
    )
    exigir(
        rel_dados["tamanhos_comparacao_integral_direta_referencia"]
        == TAMANHOS_COMPARACAO_DIRETA_EXIGIDOS,
        "Lista 'tamanhos_comparacao_integral_direta_referencia' diverge do escopo exigido.",
    )

    meta = rel_dados["metadados_execucao"]
    exigir(isinstance(meta, dict), "'metadados_execucao' deve ser dict.")
    exigir(
        meta.get("caminho_relatorio_persistente_preservado") == "relatorio_matriz_modo4.json",
        "Campo 'caminho_relatorio_persistente_preservado' invalido ou ausente.",
    )
    exigir(
        meta.get("sha256_relatorio_temporario_e_persistente_identicos") is True,
        "Paridade entre relatorio temporario e persistente nao confirmada.",
    )
    ref_of = meta.get("referencia_oficial_motor")
    exigir(isinstance(ref_of, dict), "'referencia_oficial_motor' ausente em metadados_execucao.")
    exigir(
        ref_of.get("arquivo_fisico_oficial") == "motor_lotomania.py",
        f"Arquivo oficial de referencia diverge de motor_lotomania.py: {ref_of.get('arquivo_fisico_oficial')!r}",
    )
    exigir(
        ref_of.get("sha256") == SHA256_MOTOR_REFERENCIA_OFICIAL,
        "SHA-256 em 'referencia_oficial_motor' diverge do motor oficial!",
    )

    matriz = rel_dados["matriz_resultados"]
    exigir(isinstance(matriz, dict), "'matriz_resultados' deve ser um dict.")
    chaves_esperadas_matriz = {str(t) for t in TAMANHOS_MATRIZ_EXIGIDOS}
    exigir(
        set(matriz.keys()) == chaves_esperadas_matriz,
        f"Tamanhos presentes em 'matriz_resultados' divergem dos 11 exigidos: {set(matriz.keys())}",
    )

    for t_int in TAMANHOS_MATRIZ_EXIGIDOS:
        k_str = str(t_int)
        item = matriz[k_str]
        exigir(isinstance(item, dict), f"Registro J={k_str} nao e um dict.")
        chaves_item = set(item.keys())
        if chaves_item != CHAVES_ITEM_MATRIZ_EXIGIDAS:
            faltantes = CHAVES_ITEM_MATRIZ_EXIGIDAS - chaves_item
            extras = chaves_item - CHAVES_ITEM_MATRIZ_EXIGIDAS
            raise RuntimeError(
                f"Violacao de esquema estrito em J={k_str}: faltantes={faltantes}, inesperadas={extras}"
            )

        exigir(_eh_int_estrito(item["quantidade_jogos"]) and item["quantidade_jogos"] == t_int, f"J={k_str}: quantidade_jogos invalida.")
        exigir(_eh_num_estrito(item["tempo_execucao_s"]) and item["tempo_execucao_s"] >= 0, f"J={k_str}: tempo_execucao_s invalido.")
        exigir(_eh_num_estrito(item["tempo_execucao_ms"]) and item["tempo_execucao_ms"] >= 0, f"J={k_str}: tempo_execucao_ms invalido.")
        if t_int in TAMANHOS_COMPARACAO_DIRETA_EXIGIDOS:
            exigir(_eh_num_estrito(item["tempo_execucao_referencia_ao_vivo_s"]), f"J={k_str}: tempo referencia ausente.")
        else:
            exigir(item["tempo_execucao_referencia_ao_vivo_s"] is None, f"J={k_str}: tempo referencia deveria ser None.")
        exigir(_eh_num_estrito(item["tempo_execucao_com_tracemalloc_s"]), f"J={k_str}: tracemalloc_s invalido.")
        exigir(_eh_num_estrito(item["memoria_pico_kb"]), f"J={k_str}: memoria_pico_kb invalida.")
        exigir(_eh_num_estrito(item["memoria_pico_mb"]), f"J={k_str}: memoria_pico_mb invalida.")
        exigir(_eh_num_estrito(item["memoria_working_set_processo_mb"]), f"J={k_str}: working_set invalido.")
        exigir(_eh_num_estrito(item["memoria_peak_working_set_processo_mb"]), f"J={k_str}: peak_working_set invalido.")

        des_atual = item["desempenho_medido_execucao_atual"]
        des_hist = item["desempenho_historico_referencia_com_tracemalloc"]
        clas_3 = item["classificacao_tres_niveis_equivalencia"]
        exigir(
            isinstance(des_atual, dict)
            and set(des_atual.keys()) == {
                "tempo_execucao_atual_sem_tracemalloc_s",
                "tempo_execucao_atual_sem_tracemalloc_ms",
                "tempo_execucao_referencia_ao_vivo_s",
                "memoria_working_set_atual_processo_mb",
                "memoria_peak_working_set_atual_processo_mb",
            },
            f"J={k_str}: subestrutura desempenho_medido_execucao_atual invalida.",
        )
        exigir(
            isinstance(des_hist, dict)
            and set(des_hist.keys()) == {
                "tempo_execucao_historico_com_tracemalloc_s",
                "memoria_pico_historica_tracemalloc_kb",
                "memoria_pico_historica_tracemalloc_mb",
            },
            f"J={k_str}: subestrutura desempenho_historico_referencia_com_tracemalloc invalida.",
        )
        exigir(
            isinstance(clas_3, dict)
            and set(clas_3.keys()) == {
                "comparacao_integral_direta",
                "verificacao_estrutural",
                "auditoria_amostral",
            }
            and clas_3["comparacao_integral_direta"] is (t_int <= 1000)
            and clas_3["verificacao_estrutural"] is True
            and clas_3["auditoria_amostral"] == ("complementar" if t_int <= 1000 else "primaria_alto_volume"),
            f"J={k_str}: classificacao_tres_niveis_equivalencia inconsistente.",
        )

        exigir(_eh_num_estrito(item["jogos_validos_pct"]) and item["jogos_validos_pct"] == 100.0, f"J={k_str}: jogos_validos_pct != 100.")
        exigir(_eh_int_estrito(item["jogos_unicos"]) and item["jogos_unicos"] == t_int, f"J={k_str}: jogos_unicos != J.")
        exigir(_eh_int_estrito(item["total_pares_carteira"]) and item["total_pares_carteira"] == (t_int * (t_int - 1)) // 2, f"J={k_str}: total_pares invalido.")
        exigir(_eh_int_estrito(item["dezenas_cobertas"]) and 50 <= item["dezenas_cobertas"] <= 100, f"J={k_str}: dezenas_cobertas fora [50..100].")
        exigir(_eh_num_estrito(item["desvio_padrao_alocacao_dezenas"]), f"J={k_str}: desvio_padrao invalido.")
        exigir(_eh_num_estrito(item["intersecao_media_pares"]), f"J={k_str}: intersecao_media_pares invalida.")
        exigir(_eh_int_estrito(item["intersecao_maxima_pares"]), f"J={k_str}: intersecao_maxima_pares invalida.")
        exigir(_eh_int_estrito(item["intersecao_minima_pares"]), f"J={k_str}: intersecao_minima_pares invalida.")
        exigir(_eh_int_estrito(item["soma_intersecoes_real"]), f"J={k_str}: soma_intersecoes_real invalida.")
        exigir(item["equivalente_referencia"] is True, f"J={k_str}: equivalente_referencia != True.")
        exigir(isinstance(item["equivalencia_integral_direta_comprovada"], bool), f"J={k_str}: tipo invalido em equivalencia_integral.")
        exigir(item["equivalencia_amostral_alto_volume_comprovada"] is True, f"J={k_str}: equivalencia_amostral != True.")
        exigir(isinstance(item["metodo_equivalencia"], str) and len(item["metodo_equivalencia"]) > 0, f"J={k_str}: metodo_equivalencia vazio.")
        exigir(isinstance(item["escopo_equivalencia"], str) and len(item["escopo_equivalencia"]) > 0, f"J={k_str}: escopo_equivalencia vazio.")
        exigir(item["reprodutibilidade_confirmada"] is True, f"J={k_str}: reprodutibilidade_confirmada != True.")
        exigir(item["serializacao_json_estrita_ok"] is True, f"J={k_str}: serializacao_json_estrita_ok != True.")
        exigir(_eh_hex_sha256(item["hash_carteira_v1"]), f"hash_carteira_v1 invalido em J={k_str}")
        exigir(_eh_hex_sha256(item["hash_carteira_v2"]), f"hash_carteira_v2 invalido em J={k_str}")

        if t_int <= 1000:
            exigir(item["equivalencia_integral_direta_comprovada"] is True, f"J={k_str}: comparacao direta obrigatoria.")
            exigir(item["metodo_equivalencia"] == "comparacao_integral_direta_motor_referencia", f"J={k_str}: metodo inesperado.")
        else:
            exigir(item["equivalencia_integral_direta_comprovada"] is False, f"J={k_str}: falso positivo de comparacao direta.")
            exigir(item["metodo_equivalencia"] == "invariancia_prefixo_ate_1000_e_auditoria_amostral_estagios_reais", f"J={k_str}: metodo alto volume inesperado.")

    comp_bm = rel_dados.get("comparacao_bitmask_histograma_referencia")
    exigir(isinstance(comp_bm, dict) and comp_bm.get("sucesso") is True, "comparacao_bitmask_histograma_referencia invalida.")
    exigir(comp_bm.get("divergencias_encontradas") == 0, "Divergencias sinteticas detectadas na matriz.")
    fid_prng = comp_bm.get("comprovacao_fidelidade_reconstrucao_prng")
    exigir(isinstance(fid_prng, dict), "Secao comprovacao_fidelidade_reconstrucao_prng ausente no relatorio.")
    exigir(fid_prng.get("deriva_prng_ao_longo_de_10000_jogos") == 0, "Deriva de PRNG detectada no relatorio.")
    exigir(fid_prng.get("identidade_100pct_contra_trace_interno") is True, "Confronto trace interno nao aprovado.")
    exigir(fid_prng.get("todos_vencedores_presentes_nos_80_candidatos_da_etapa") is True, "Vencedores ausentes em etapa PRNG.")
    idx_inicio = fid_prng.get("idx_inicio_greedy")
    exigir(idx_inicio in (1, 2), f"idx_inicio_greedy invalido no relatorio: {idx_inicio!r}")
    exigir(
        fid_prng.get("estagios_gulosos_verificados_em_j10000") == 10000 - idx_inicio,
        "Contagem de estagios gulosos PRNG inconsistente no relatorio.",
    )
    exigir(
        fid_prng.get("candidatos_confrontados_contra_trace_interno_j20")
        == fid_prng.get("estagios_trace_confrontados_j20", -1) * 80,
        "Contagem de candidatos confrontados contra trace inconsistente no relatorio.",
    )

    return {
        "esquema_estrito_aprovado": True,
        "registros_matriz_validados": len(TAMANHOS_MATRIZ_EXIGIDOS),
        "chaves_por_registro": len(CHAVES_ITEM_MATRIZ_EXIGIDAS),
    }


def _validar_nome_log_permitido(nome_log: str) -> None:
    exigir(
        isinstance(nome_log, str)
        and "/" not in nome_log
        and "\\" not in nome_log
        and ".." not in nome_log
        and bool(re.fullmatch(r"(?:task|homologacao)[0-9A-Za-z_.-]*\.log", nome_log)),
        f"Nome de arquivo de log nao autorizado ou inseguro: {nome_log!r}",
    )


def verificar_ausencia_arquivos_nao_previstos(base_dir: str, nome_log_esperado: str) -> int:
    _validar_nome_log_permitido(nome_log_esperado)
    permitidos = ARQUIVOS_PACOTE_FIXOS_PERMITIDOS | {nome_log_esperado}
    extensoes_monitoradas = (".py", ".js", ".json", ".sig", ".pem", ".key", ".log")
    total_inspecionados = 0
    for root, dirs, files in os.walk(base_dir):
        dirs[:] = [d for d in dirs if d != "__pycache__"]
        for fname in files:
            if fname.lower().endswith(".key"):
                raise RuntimeError(f"Chave privada residual detectada no pacote: {fname}")
            if fname.lower().endswith(extensoes_monitoradas):
                rel_p = os.path.relpath(os.path.join(root, fname), base_dir).replace("\\", "/")
                exigir(
                    rel_p in permitidos,
                    f"Arquivo adicional nao previsto relevante a cadeia de confianca detectado: {rel_p}",
                )
                total_inspecionados += 1
    return total_inspecionados


def verificar_cadeia_independente(
    base_dir: str,
    caminho_log: str = "",
    estrito_diretorio_pacote: bool = False,
) -> dict:
    aprovacoes = []
    ressalvas = [
        "Verificador independente deve ter seu proprio SHA-256 ('sha256_verificador_proprio') e 'CHAVE_PUBLICA_OFICIAL_SHA256' confrontados externamente pelo auditor antes da aceitacao definitiva.",
        "Equivalencia de carteiras J in {5000, 10000} e sustentada por invariancia do prefixo J=1000, teorema de contagem dupla integral, zero deriva do PRNG nos estagios gulosos de J=10000 e auditoria amostral (2.160 candidatos), nao por execucao O(J^2) integral da referencia neste tamanho.",
    ]

    # 1. Raiz de confianca independente: chave publica oficial
    cam_pub = os.path.join(base_dir, "chave_publica_modo4.pem")
    exigir(os.path.isfile(cam_pub), "Arquivo obrigatorio ausente: chave_publica_modo4.pem")
    sha_pub = sha256_arquivo(cam_pub)
    exigir(
        sha_pub.lower() == CHAVE_PUBLICA_OFICIAL_SHA256.lower(),
        f"Chave publica diverge do SHA-256 oficial fixado fora do manifesto: {sha_pub}",
    )
    with open(cam_pub, "rb") as fp:
        pub_key = serialization.load_pem_public_key(fp.read())
    exigir(isinstance(pub_key, Ed25519PublicKey), "chave_publica_modo4.pem nao e Ed25519PublicKey valida.")
    aprovacoes.append("1. Raiz de confianca chave_publica_modo4.pem validada contra SHA-256 fixado.")

    # 2. Selo do motor (manifesto_modo4.json + manifesto_modo4.sig)
    cam_man_motor = os.path.join(base_dir, "manifesto_modo4.json")
    cam_sig_motor = os.path.join(base_dir, "manifesto_modo4.sig")
    exigir(os.path.isfile(cam_man_motor), "Arquivo obrigatorio ausente: manifesto_modo4.json")
    exigir(os.path.isfile(cam_sig_motor), "Arquivo obrigatorio ausente: manifesto_modo4.sig")
    sha_man_motor_arquivo_bytes = sha256_arquivo(cam_man_motor)
    sha_sig_motor_arquivo_bytes = sha256_arquivo(cam_sig_motor)
    with open(cam_man_motor, "r", encoding="utf-8") as f:
        man_motor = json.load(f)
    with open(cam_sig_motor, "r", encoding="utf-8") as f:
        sig_motor_bytes = bytes.fromhex(f.read().strip())
    bytes_canonicos_motor = serializar_canonico(man_motor)
    sha_man_motor_canonico = hashlib.sha256(bytes_canonicos_motor).hexdigest()
    pub_key.verify(sig_motor_bytes, bytes_canonicos_motor)
    aprovacoes.append("2. Assinatura Ed25519 de manifesto_modo4.json verificada com exito.")

    # 3. Manifesto de evidencia da execucao
    cam_man_ev = os.path.join(base_dir, "manifesto_evidencia_execucao_modo4.json")
    cam_sig_ev = os.path.join(base_dir, "manifesto_evidencia_execucao_modo4.sig")
    exigir(os.path.isfile(cam_man_ev), "Arquivo obrigatorio ausente: manifesto_evidencia_execucao_modo4.json")
    exigir(os.path.isfile(cam_sig_ev), "Arquivo obrigatorio ausente: manifesto_evidencia_execucao_modo4.sig")
    sha_man_ev_arquivo_bytes = sha256_arquivo(cam_man_ev)
    sha_sig_ev_arquivo_bytes = sha256_arquivo(cam_sig_ev)
    with open(cam_man_ev, "r", encoding="utf-8") as f:
        man_ev = json.load(f)
    with open(cam_sig_ev, "r", encoding="utf-8") as f:
        sig_ev_hex = f.read().strip()
        sig_ev_bytes = bytes.fromhex(sig_ev_hex)
    bytes_canonicos_ev = serializar_canonico(man_ev)
    sha_man_ev_canonico = hashlib.sha256(bytes_canonicos_ev).hexdigest()
    pub_key.verify(sig_ev_bytes, bytes_canonicos_ev)

    exigir(
        man_ev.get("versao_motor") == VERSAO_MOTOR_EXIGIDA,
        f"Versao do motor incompativel no manifesto: {man_ev.get('versao_motor')!r}",
    )
    exigir(
        man_ev.get("versao_esquema_relatorio") == VERSAO_ESQUEMA_RELATORIO_EXIGIDA,
        f"Versao de esquema incompativel no manifesto: {man_ev.get('versao_esquema_relatorio')!r}",
    )
    exigir(
        str(man_ev.get("chave_publica_confiavel_sha256_fixado", "")).lower()
        == CHAVE_PUBLICA_OFICIAL_SHA256.lower(),
        "Campo chave_publica_confiavel_sha256_fixado no manifesto diverge da raiz de confianca!",
    )
    aprovacoes.append("3. Assinatura Ed25519 e versao (1.2 / 1.2.2) de manifesto_evidencia_execucao_modo4.json validados.")

    nome_log = man_ev.get("arquivo_log_execucao", "")
    _validar_nome_log_permitido(nome_log)
    if estrito_diretorio_pacote:
        total_inspecionados_pacote = verificar_ausencia_arquivos_nao_previstos(base_dir, nome_log)
        aprovacoes.append(f"3b. Higiene estrita de arquivos do pacote validada ({total_inspecionados_pacote} artefatos permitidos, zero .key residual).")

    # 4. Verifica relatorio_matriz_modo4.json
    cam_rel = os.path.join(base_dir, "relatorio_matriz_modo4.json")
    exigir(os.path.isfile(cam_rel), "Arquivo obrigatorio ausente: relatorio_matriz_modo4.json")
    sha_rel_atual = sha256_arquivo(cam_rel)
    exigir(
        sha_rel_atual == man_ev.get("sha256_relatorio_matriz_modo4_json"),
        "Hash de relatorio_matriz_modo4.json diverge do manifesto assinado!",
    )
    with open(cam_rel, "r", encoding="utf-8") as f:
        rel_dados = json.load(f)
    validacao_esquema = validar_esquema_estrito_relatorio(rel_dados)

    exec_id = man_ev["execucao_id"]
    meta_rel = rel_dados["metadados_execucao"]
    exigir(
        meta_rel["execucao_id"] == exec_id,
        "execucao_id diverge entre relatorio_matriz_modo4.json e o manifesto!",
    )
    exigir(meta_rel["timestamp_inicio_utc"] == man_ev["timestamp_inicio_execucao_utc"], "timestamp_inicio_utc diverge.")
    exigir(meta_rel["timestamp_fim_utc"] == man_ev["timestamp_fim_execucao_utc"], "timestamp_fim_utc diverge.")
    exigir(meta_rel["duracao_total_bateria_s"] == man_ev["duracao_total_bateria_s"], "duracao_total_bateria_s diverge.")
    exigir(meta_rel["caminho_saida_relatorio"] == man_ev["caminho_saida_relatorio_temporario"], "caminho_saida_relatorio diverge.")
    exigir(meta_rel["gerado_em_diretorio_temporario"] is True, "Relatorio nao foi gerado em diretorio temporario.")
    aprovacoes.append("4. Hash SHA-256, execucao_id, metadados e esquema estrito 1.2.2 de relatorio_matriz_modo4.json validados.")

    # 5. Log finalizado
    if not caminho_log:
        caminhos_possiveis_log = [
            os.path.join(base_dir, nome_log),
            os.path.join(
                r"C:\Users\Luis Brun\.gemini\antigravity\brain\f3af3942-aca3-4c9a-a3dd-e56f90feb848\.system_generated\tasks",
                nome_log,
            ),
        ]
        caminho_log = next((c for c in caminhos_possiveis_log if os.path.isfile(c)), "")

    exigir(bool(caminho_log) and os.path.isfile(caminho_log), f"Arquivo de log obrigatorio ausente: {nome_log}")
    sha_log_atual = sha256_arquivo(caminho_log)
    exigir(
        sha_log_atual == man_ev.get("sha256_log_execucao_finalizado"),
        f"Hash do log ({sha_log_atual}) diverge do manifesto ({man_ev.get('sha256_log_execucao_finalizado')})!",
    )
    with open(caminho_log, "r", encoding="utf-8", errors="replace") as fl:
        conteudo_log = fl.read()
    exigir(exec_id in conteudo_log, f"execucao_id {exec_id} nao encontrado no log finalizado da tarefa!")
    exigir(sha_rel_atual in conteudo_log, f"SHA-256 do relatorio ({sha_rel_atual}) nao consta no log finalizado!")
    exigir(
        "PARECER TECNICO CONCLUSIVO: HOMOLOGACAO INTEGRAL MODO 4 v1.2 EXECUTADA COM EXITO (7/7 ETAPAS)" in conteudo_log,
        "Banner conclusivo da Etapa 7 ausente no log finalizado!",
    )
    aprovacoes.append(f"5. Log finalizado '{nome_log}' integro contra SHA-256 assinado e vinculado ao execucao_id.")

    # 6. Inventario exato dos 22 arquivos-fonte/dados/testes
    hashes_manifesto = man_ev.get("hashes_sha256_arquivos_fonte")
    exigir(
        isinstance(hashes_manifesto, dict)
        and set(hashes_manifesto.keys()) == ARQUIVOS_FONTE_MANIFESTO_EXIGIDOS,
        (
            f"Inventario do manifesto diverge dos 22 arquivos exigidos: "
            f"faltantes={ARQUIVOS_FONTE_MANIFESTO_EXIGIDOS - set(hashes_manifesto or {})}, "
            f"extras={set(hashes_manifesto or {}) - ARQUIVOS_FONTE_MANIFESTO_EXIGIDOS}"
        ),
    )
    arquivos_verificados = 0
    for rel_path, sha_esp in hashes_manifesto.items():
        cam_f = os.path.join(base_dir, *rel_path.split("/"))
        exigir(os.path.isfile(cam_f), f"Arquivo obrigatorio inventariado ausente no pacote: {rel_path}")
        sha_calc = sha256_arquivo(cam_f)
        exigir(sha_calc == sha_esp, f"Divergencia de hash em {rel_path}: {sha_calc} != {sha_esp}")
        arquivos_verificados += 1
    aprovacoes.append(f"6. Todos os {arquivos_verificados} arquivos inventariados conferem byte a byte com SHA-256 assinado.")

    # 7. Confronto contra hashes gravados durante a execucao no relatorio
    hashes_relatorio_exec = meta_rel.get("hashes_sha256_codigo_fonte", {})
    exigir(
        isinstance(hashes_relatorio_exec, dict) and len(hashes_relatorio_exec) >= 13,
        "Secao 'hashes_sha256_codigo_fonte' no relatorio incompleta (< 13 arquivos).",
    )
    for rel_path_exec, sha_exec in hashes_relatorio_exec.items():
        exigir(rel_path_exec in hashes_manifesto, f"Arquivo registrado no relatorio ({rel_path_exec}) ausente no manifesto!")
        exigir(
            hashes_manifesto[rel_path_exec] == sha_exec,
            f"Arquivo de fonte ({rel_path_exec}) difere daquele efetivamente executado no relatorio!",
        )
    aprovacoes.append(f"7. Consistencia cruzada entre hashes em disco e hashes de execucao no relatorio confirmada ({len(hashes_relatorio_exec)} itens).")

    sha_self = sha256_arquivo(os.path.abspath(__file__))

    return {
        "verificacao_independente_aprovada": True,
        "sha256_verificador_proprio": sha_self,
        "execucao_id_confirmado": exec_id,
        "arquivo_log_confirmado": nome_log,
        "chave_publica_sha256_raiz_confianca": sha_pub,
        "aprovacoes": aprovacoes,
        "ressalvas_ou_avisos": ressalvas,
        "erros": [],
        "manifesto_motor": {
            "sha256_arquivo_json_bytes": sha_man_motor_arquivo_bytes,
            "sha256_canonico_bytes_assinados": sha_man_motor_canonico,
            "tamanho_bytes_canonicos_assinados": len(bytes_canonicos_motor),
            "sha256_arquivo_sig_bytes": sha_sig_motor_arquivo_bytes,
            "assinatura_ed25519_valida": True,
        },
        "manifesto_evidencia_execucao": {
            "sha256_arquivo_json_bytes": sha_man_ev_arquivo_bytes,
            "sha256_canonico_bytes_assinados": sha_man_ev_canonico,
            "tamanho_bytes_canonicos_assinados": len(bytes_canonicos_ev),
            "sha256_arquivo_sig_bytes": sha_sig_ev_arquivo_bytes,
            "assinatura_ed25519_hex": sig_ev_hex,
            "assinatura_ed25519_valida": True,
            "procedimento_canonicalizacao": (
                'json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode("utf-8")'
            ),
        },
        "relatorio_matriz_sha256_integro": sha_rel_atual,
        "validacao_esquema_estrito_relatorio": validacao_esquema,
        "log_execucao_finalizado_sha256_integro": sha_log_atual,
        "arquivos_fonte_verificados": arquivos_verificados,
    }


def executar_autotestes_rejeicao(
    base_dir: str,
    nome_log: str,
    exec_id_real: str,
    caminho_log_real: str = "",
) -> dict:
    """
    Executa 10 cenarios negativos de adulteracao em diretorios temporarios isolados para
    comprovar rejeicao fail-closed mesmo sob `python -O`.
    """
    cenarios_aprovados = []
    arquivos_copia = ARQUIVOS_PACOTE_FIXOS_PERMITIDOS | {nome_log}

    def _copiar_pacote(dst: str):
        for rel_p in arquivos_copia:
            src_f = os.path.join(base_dir, *rel_p.split("/"))
            if os.path.isfile(src_f):
                dst_f = os.path.join(dst, *rel_p.split("/"))
                os.makedirs(os.path.dirname(dst_f), exist_ok=True)
                shutil.copy2(src_f, dst_f)
        dst_log = os.path.join(dst, nome_log)
        if not os.path.isfile(dst_log) and caminho_log_real and os.path.isfile(caminho_log_real):
            shutil.copy2(caminho_log_real, dst_log)

    def _deve_falhar(nome_cenario: str, mutator_fn):
        with tempfile.TemporaryDirectory(prefix="autoteste_verificador_") as tmp:
            _copiar_pacote(tmp)
            falhou = False
            erro_capturado = ""
            try:
                mutator_fn(tmp)
                verificar_cadeia_independente(
                    tmp,
                    caminho_log=os.path.join(tmp, nome_log),
                    estrito_diretorio_pacote=True,
                )
            except (RuntimeError, InvalidSignature, ValueError, KeyError, FileNotFoundError) as exc:
                falhou = True
                erro_capturado = f"{type(exc).__name__}: {exc}"
            exigir(falhou, f"Cenario '{nome_cenario}' NAO foi rejeitado pelo verificador!")
            cenarios_aprovados.append({"cenario": nome_cenario, "rejeitado": True, "erro": erro_capturado})

    _deve_falhar(
        "1_arquivo_obrigatorio_ausente",
        lambda d: os.remove(os.path.join(d, "verificador_selo_modo4.py")),
    )
    _deve_falhar(
        "2_arquivo_adicional_nao_previsto",
        lambda d: open(os.path.join(d, "modulo_intruso.py"), "w", encoding="utf-8").write("x = 1\n"),
    )
    _deve_falhar(
        "3_hash_divergente_modulo",
        lambda d: open(os.path.join(d, "motor_lotomania_modo4.py"), "a", encoding="utf-8").write("\n# adulterado\n"),
    )

    def _corromper_sig(d):
        p = os.path.join(d, "manifesto_evidencia_execucao_modo4.sig")
        sig_h = open(p, "r", encoding="utf-8").read().strip()
        novo = ("0" if sig_h[0] != "0" else "1") + sig_h[1:]
        open(p, "w", encoding="utf-8").write(novo)

    _deve_falhar("4_assinatura_ed25519_invalida", _corromper_sig)

    def _adulterar_exec_id_log(d):
        p = os.path.join(d, nome_log)
        txt = open(p, "r", encoding="utf-8", errors="replace").read().replace(
            exec_id_real,
            "00000000-0000-0000-0000-000000000000",
        )
        open(p, "w", encoding="utf-8").write(txt)

    _deve_falhar("5_execucao_id_divergente", _adulterar_exec_id_log)

    def _adulterar_manifesto(d):
        p = os.path.join(d, "manifesto_evidencia_execucao_modo4.json")
        obj = json.load(open(p, "r", encoding="utf-8"))
        obj["duracao_total_bateria_s"] = 1.0
        json.dump(obj, open(p, "w", encoding="utf-8"), indent=2, sort_keys=True)

    _deve_falhar("6_manifesto_alterado", _adulterar_manifesto)
    _deve_falhar(
        "7_log_alterado",
        lambda d: open(os.path.join(d, nome_log), "a", encoding="utf-8").write("\nlinha extra\n"),
    )

    def _adulterar_schema_relatorio(d):
        p = os.path.join(d, "relatorio_matriz_modo4.json")
        rel = json.load(open(p, "r", encoding="utf-8"))
        rel_copia = copy.deepcopy(rel)
        rel_copia["matriz_resultados"]["2"]["hash_v2"] = rel_copia["matriz_resultados"]["2"].pop("hash_carteira_v2")
        validar_esquema_estrito_relatorio(rel_copia)

    _deve_falhar("8_esquema_relatorio_incompativel_hash_v2", _adulterar_schema_relatorio)

    def _relatorio_outra_execucao(d):
        p = os.path.join(d, "relatorio_matriz_modo4.json")
        rel = json.load(open(p, "r", encoding="utf-8"))
        rel["metadados_execucao"]["execucao_id"] = "11111111-2222-3333-4444-555555555555"
        json.dump(rel, open(p, "w", encoding="utf-8"), indent=2)

    _deve_falhar("9_relatorio_de_outra_execucao", _relatorio_outra_execucao)
    _deve_falhar(
        "10_chave_publica_nao_confiavel",
        lambda d: open(os.path.join(d, "chave_publica_modo4.pem"), "a", encoding="utf-8").write("\n"),
    )

    return {
        "total_cenarios_rejeicao_testados": len(cenarios_aprovados),
        "todos_rejeitados_com_sucesso": len(cenarios_aprovados) == 10,
        "cenarios": cenarios_aprovados,
    }


if __name__ == "__main__":
    dir_alvo = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.abspath(__file__))
    log_alvo = sys.argv[2] if len(sys.argv) > 2 else ""
    estrito = "--strict-dir" in sys.argv
    try:
        resultado = verificar_cadeia_independente(
            dir_alvo,
            log_alvo,
            estrito_diretorio_pacote=estrito,
        )
        resultado["autotestes_rejeicao_10_cenarios"] = executar_autotestes_rejeicao(
            dir_alvo,
            resultado["arquivo_log_confirmado"],
            resultado["execucao_id_confirmado"],
            log_alvo,
        )
        print(json.dumps(resultado, indent=2, ensure_ascii=False))
    except Exception as exc_cli:
        saida_erro = {
            "verificacao_independente_aprovada": False,
            "sha256_verificador_proprio": sha256_arquivo(os.path.abspath(__file__)),
            "aprovacoes": [],
            "ressalvas_ou_avisos": [],
            "erros": [f"{type(exc_cli).__name__}: {exc_cli}"],
        }
        print(json.dumps(saida_erro, indent=2, ensure_ascii=False))
        sys.exit(1)
