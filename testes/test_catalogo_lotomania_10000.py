# -*- coding: utf-8 -*-
"""
Suite completa de testes e verificacao empirica de SLOs do Passo 2
(`CATALOGO_LOTOMANIA_10000` - catalogo imutavel, assinado e somente-leitura).

Regras estruturais:
- Zero instrucoes `assert` (usa exclusivamente `unittest.TestCase`), garantindo
  execucao identica sob `python` e `python -O`.
- Nenhum teste altera `dados/CATALOGO_LOTOMANIA_10000`, Passo 1, `api.py` ou arquivos selados.
"""

import ast
from decimal import Decimal
import hashlib
import json
import os
import random
import shutil
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from unittest import mock

_REPOSITORIO_RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _REPOSITORIO_RAIZ not in sys.path:
    sys.path.insert(0, _REPOSITORIO_RAIZ)

from catalogo_lotomania_10000 import (  # noqa: E402
    CAMINHO_CHAVE_PUBLICA_PADRAO,
    CHAVE_PUBLICA_CATALOGO_SHA256,
    CLAUSULA_OBRIGATORIA,
    CONFIGURACAO_PADRAO_S1_1080K,
    DIR_CATALOGO_PADRAO,
    LIMITE_MAXIMO_CACHE_BYTES,
    SHA256_CONFIGURACAO_PADRAO_S1_1080K,
    VERSAO_ALGORITMO_PADRAO,
    CatalogoIndisponivelError,
    IntegridadeCatalogoError,
    LeitorCatalogoLotomania,
    SolicitacaoForaDaGradeError,
    abrir_catalogo,
    calcular_sha256_configuracao,
    canonicalizar_configuracao,
    formatar_decimal_canonico,
    montar_id_carteira,
    serializar_jcs_canonico,
)
from catalogo_lotomania_10000.crypto_selo import ler_arquivo_controlado_fd  # noqa: E402
from catalogo_lotomania_10000.publicador import (  # noqa: E402
    CAMINHO_CHAVE_PRIVADA_PADRAO,
    FalhaInjetadaPublicacaoError,
    _remover_arvore_segura,
    ativar_versao_publicada,
    gerar_par_chaves_catalogo_teste,
    publicar_versao_catalogo,
    rollback_versao_catalogo,
)
from lotomania_carteira_10000.validacao import (  # noqa: E402
    calcular_hashes_certificados,
    validar_r1_r9_rapido,
)
from testes.test_lotomania_carteira_10000 import HASHES_ARQUIVOS_PROTEGIDOS  # noqa: E402


def _gerar_carteira_espelhada_valida(J: int, seed: int) -> list:
    """Constroi carteira valida (R1-R12, k_max<=35, marginais=J//2) para testes isolados."""
    if J < 2 or J % 2 != 0:
        raise ValueError("J deve ser par >= 2.")
    rng = random.Random(seed)
    blocos = [list(range(20 * r + 1, 20 * (r + 1) + 1)) for r in range(5)]
    jogos = []
    masks = []
    vistos = set()

    for _ in range(J // 2):
        tent = 0
        while True:
            tent += 1
            if tent > 50000:
                raise RuntimeError("Nao foi possivel gerar par valido dentro do teto de tentativas.")
            j_a = []
            j_b = []
            for bloco in blocos:
                metade = sorted(rng.sample(bloco, 10))
                metade_set = set(metade)
                comp = [n for n in bloco if n not in metade_set]
                j_a.extend(metade)
                j_b.extend(comp)
            if not validar_r1_r9_rapido(j_a) or not validar_r1_r9_rapido(j_b):
                continue
            tupla_a = tuple(j_a)
            tupla_b = tuple(j_b)
            if tupla_a in vistos or tupla_b in vistos:
                continue
            m_a = 0
            for n in j_a:
                m_a |= 1 << (n - 1)
            m_b = 0
            for n in j_b:
                m_b |= 1 << (n - 1)
            ok = True
            for m_prev in masks:
                if (m_a & m_prev).bit_count() > 35 or (m_b & m_prev).bit_count() > 35:
                    ok = False
                    break
            if ok:
                jogos.append(j_a)
                jogos.append(j_b)
                masks.append(m_a)
                masks.append(m_b)
                vistos.add(tupla_a)
                vistos.add(tupla_b)
                break
    return jogos


def _assinar_manifesto_e_atualizar_recibo(dir_versao: str, caminho_chave_privada: str, caminho_ponteiro: str = None) -> None:
    """Reassina manifesto em testes de manipulacao controlada mantendo recibo consistente."""
    from cryptography.hazmat.primitives import serialization

    p_man = os.path.join(dir_versao, "manifesto_catalogo.json")
    p_sig = os.path.join(dir_versao, "manifesto_catalogo.sig")
    p_rec = os.path.join(dir_versao, "CONCLUSAO_PUBLICACAO.json")
    for p in (p_man, p_sig, p_rec):
        os.chmod(p, stat.S_IWRITE | stat.S_IREAD)

    with open(p_man, "rb") as fh:
        man_bytes = fh.read()
    with open(caminho_chave_privada, "rb") as fk:
        priv = serialization.load_pem_private_key(fk.read(), password=None)
    sig_bytes = (priv.sign(man_bytes).hex() + "\n").encode("ascii")
    with open(p_sig, "wb") as fs:
        fs.write(sig_bytes)

    sha_man = hashlib.sha256(man_bytes).hexdigest()
    sha_sig = hashlib.sha256(sig_bytes).hexdigest()
    with open(p_rec, "r", encoding="utf-8") as fr:
        rec = json.load(fr)
    rec["sha256_manifesto"] = sha_man
    rec["sha256_assinatura_sig"] = sha_sig
    with open(p_rec, "w", encoding="utf-8") as fr:
        json.dump(rec, fr, sort_keys=True, indent=2)

    if caminho_ponteiro and os.path.isfile(caminho_ponteiro):
        with open(caminho_ponteiro, "r", encoding="utf-8") as fp:
            ptr = json.load(fp)
        ptr["sha256_manifesto"] = sha_man
        ptr["sha256_assinatura_sig"] = sha_sig
        with open(caminho_ponteiro, "w", encoding="utf-8") as fp:
            json.dump(ptr, fp, sort_keys=True, indent=2)


class Test01CanonicalizacaoEGoldenVectors(unittest.TestCase):
    def test_01_golden_vectors_decimais_e_rejeicoes(self) -> None:
        casos_validos = [
            ("0.08", "0.08"),
            ("0.0800", "0.08"),
            (".08", "0.08"),
            ("+0.080", "0.08"),
            (Decimal("0.08000"), "0.08"),
            ("30", "30"),
            ("30.00", "30"),
            (30, "30"),
            (Decimal("3E+1"), "30"),
            ("0", "0"),
            ("0.000", "0"),
            ("+0.0", "0"),
            (Decimal("0E-5"), "0"),
            ("-1.5000", "-1.5"),
            ("1.000", "1"),
        ]
        for entrada, esperado in casos_validos:
            self.assertEqual(formatar_decimal_canonico(entrada), esperado)

        rejeicoes_valor = [
            "NaN",
            "nan",
            "Infinity",
            "-Infinity",
            "inf",
            "-0",
            "-0.0",
            "-0.000",
            " 0.08",
            "0.08 ",
            "1_000",
            "1e-2",
            "",
            Decimal("NaN"),
            Decimal("Infinity"),
            Decimal("-Infinity"),
            Decimal("-0"),
            Decimal("-0.0"),
        ]
        for ruim in rejeicoes_valor:
            with self.assertRaises(ValueError):
                formatar_decimal_canonico(ruim)

        for tipo_proibido in (0.08, 30.0, -0.0, True, False, None, [1]):
            with self.assertRaises(TypeError):
                formatar_decimal_canonico(tipo_proibido)  # type: ignore[arg-type]

    def test_02_golden_vector_configuracao_padrao_e_equivalencia(self) -> None:
        self.assertEqual(
            SHA256_CONFIGURACAO_PADRAO_S1_1080K,
            "d302cf3a1f9ceedc14c8eb1bb6b6fafff6f5be24b0d5419ec3a66d400f9fb25e",
        )

        cfg_equivalente = {
            "batch0": 80,
            "gamma_plus": Decimal("0.0200"),
            "alpha_2": ".2500",
            "alpha_1": "+0.080",
            "alpha_win": 1,
            "alpha_25": "30.00",
            "tau_primario": 35,
            "max_tentativas_f3": 1080000,
            "estrategia_fase3": "S1_atual_top8",
        }
        canonica, bytes_jcs, digest = calcular_sha256_configuracao(cfg_equivalente)
        self.assertEqual(digest, SHA256_CONFIGURACAO_PADRAO_S1_1080K)
        self.assertEqual(canonica, CONFIGURACAO_PADRAO_S1_1080K)
        self.assertEqual(
            bytes_jcs,
            b'{"alpha_1":"0.08","alpha_2":"0.25","alpha_25":"30","alpha_win":"1",'
            b'"batch0":80,"estrategia_fase3":"S1_atual_top8","gamma_plus":"0.02",'
            b'"max_tentativas_f3":1080000,"tau_primario":35}',
        )

        with self.assertRaises(TypeError):
            serializar_jcs_canonico({"a": {"b": 0.25}})
        with self.assertRaises(ValueError):
            canonicalizar_configuracao({"alpha_1": "0.08"})

        self.assertEqual(
            montar_id_carteira(
                J=10000,
                seed=330001,
                versao_algoritmo=VERSAO_ALGORITMO_PADRAO,
                sha256_configuracao=SHA256_CONFIGURACAO_PADRAO_S1_1080K,
            ),
            "ltm_ordem5r3_s1_1080k_J10000_seed330001",
        )


class Test02CatalogoOficialV1EParidade(unittest.TestCase):
    def test_01_abertura_paridade_integral_e_paginacao_catalogo_oficial(self) -> None:
        self.assertTrue(os.path.isdir(DIR_CATALOGO_PADRAO))
        self.assertTrue(os.path.isfile(CAMINHO_CHAVE_PUBLICA_PADRAO))
        with open(CAMINHO_CHAVE_PUBLICA_PADRAO, "rb") as fk_cat:
            sha_pub_cat = hashlib.sha256(fk_cat.read()).hexdigest()
        self.assertEqual(sha_pub_cat, CHAVE_PUBLICA_CATALOGO_SHA256)

        caminho_pub_modo4 = os.path.join(_REPOSITORIO_RAIZ, "chave_publica_modo4.pem")
        if os.path.isfile(caminho_pub_modo4):
            with open(caminho_pub_modo4, "rb") as fk_m4:
                self.assertNotEqual(sha_pub_cat, hashlib.sha256(fk_m4.read()).hexdigest())

        leitor, info = abrir_catalogo(DIR_CATALOGO_PADRAO)
        self.assertEqual(info["versao_catalogo"], "v1.0.0")
        self.assertEqual(info["j_permitidos"], [10000])
        self.assertEqual(info["total_carteiras"], 1)

        dir_v1 = info["dir_versao"]
        for raiz, _, arqs in os.walk(dir_v1):
            for arq in arqs:
                self.assertFalse(arq.endswith(("-wal", "-shm", "-journal")))
                modo = os.stat(os.path.join(raiz, arq)).st_mode
                self.assertEqual(modo & stat.S_IWRITE, 0)

        res = leitor.obter_carteira(10000, 330001)
        self.assertFalse(res["cache_hit"])
        self.assertEqual(res["retornados"], 10000)

        caminho_json_orig = os.path.join(
            _REPOSITORIO_RAIZ, "auditoria", "lotomania_carteira_10000", "carteira_10000_seed330001.json"
        )
        with open(caminho_json_orig, "r", encoding="utf-8") as fj:
            orig = json.load(fj)
        self.assertEqual(res["jogos"], orig["jogos"])
        self.assertEqual(
            res["sha256_estado_canonico"],
            "747e25a84986e676a11c3706bf6d178c1c5a78e99dce76d9bfc0c08e74c3950e",
        )
        self.assertEqual(
            res["hash_carteira_sha256_v1"],
            "589947b2385147f6acce8a36b78c5d3ed295cfbf1a588a710f9559b597fccb6d",
        )
        self.assertEqual(
            res["hash_carteira_sha256_v2_canonico"],
            "f33e0f72869905a7b9f211ae89f9167ed7916103731a5369bb8b9500fb4fb247",
        )
        self.assertEqual(
            res["sha256_matriz_incidencia_100"],
            "75ff1e068d8c81c90b26e2f8e1a8fa151d57a967815fc0fb43f13e911ee4b127",
        )

        # Leitura paginada em cache e verificacao de limites de pagina
        pag1 = leitor.obter_carteira(10000, 330001, offset=0, limit=200)
        self.assertTrue(pag1["cache_hit"])
        self.assertEqual(pag1["retornados"], 200)
        self.assertEqual(pag1["jogos"], orig["jogos"][:200])

        pag2 = leitor.obter_carteira(10000, 330001, offset=9900, limit=200)
        self.assertTrue(pag2["cache_hit"])
        self.assertEqual(pag2["retornados"], 100)
        self.assertEqual(pag2["jogos"], orig["jogos"][9900:])

        with self.assertRaises(ValueError):
            leitor.obter_carteira(10000, 330001, offset=10000, limit=1)
        with self.assertRaises(ValueError):
            leitor.obter_carteira(10000, 330001, offset=-1, limit=10)
        with self.assertRaises(ValueError):
            leitor.obter_carteira(10000, 330001, offset=0, limit=0)

    def test_02_rejeicao_estrita_solicitacoes_fora_da_grade(self) -> None:
        leitor, _ = abrir_catalogo(DIR_CATALOGO_PADRAO)
        for J_invalido in (20, 200, 500, 9998, 9999, 0, -2, True, 10000.0, "10000"):
            with self.assertRaises(SolicitacaoForaDaGradeError):
                leitor.obter_carteira(J_invalido)  # type: ignore[arg-type]

        with self.assertRaises(SolicitacaoForaDaGradeError):
            leitor.obter_carteira(10000, 999999)
        with self.assertRaises(SolicitacaoForaDaGradeError):
            leitor.obter_carteira(10000, True)  # type: ignore[arg-type]
        with self.assertRaises(SolicitacaoForaDaGradeError):
            leitor.obter_carteira(10000, 330001, versao_algoritmo="ordem4-inexistente")

        cfg_diferente = dict(CONFIGURACAO_PADRAO_S1_1080K)
        cfg_diferente["alpha_1"] = "0.09"
        with self.assertRaises(SolicitacaoForaDaGradeError):
            leitor.obter_carteira(10000, 330001, configuracao=cfg_diferente)

    def test_03_auditoria_integral_r1_r12_e_slos_empiricos(self) -> None:
        t0 = time.perf_counter()
        leitor, _ = abrir_catalogo(DIR_CATALOGO_PADRAO)
        abertura_ms = (time.perf_counter() - t0) * 1000.0

        t1 = time.perf_counter()
        r1 = leitor.obter_carteira(10000, 330001)
        primeira_ms = (time.perf_counter() - t1) * 1000.0
        self.assertFalse(r1["cache_hit"])

        t2 = time.perf_counter()
        r2 = leitor.obter_carteira(10000, 330001, offset=0, limit=200)
        paginada_ms = (time.perf_counter() - t2) * 1000.0
        self.assertTrue(r2["cache_hit"])

        self.assertLessEqual(abertura_ms, 50.0)
        self.assertLessEqual(primeira_ms, 25.0)
        self.assertLessEqual(paginada_ms, 5.0)

        aud = leitor.auditar_catalogo_completo()
        self.assertTrue(aud["todas_aprovadas"])
        self.assertEqual(aud["total_carteiras_auditadas"], 1)
        c0 = aud["carteiras"][0]
        self.assertEqual(c0["k_max"], 35)
        self.assertEqual(c0["phi2"], 232285184)
        self.assertEqual(c0["d_max"], 1140)
        self.assertEqual(c0["P_gt_25"], 161144723)
        self.assertEqual(c0["R_win"], "3509128436603630355147408")
        # Auditoria limpa o cache para garantir leitura pura do disco
        self.assertEqual(leitor.estatisticas_cache()["bytes_em_uso"], 0)


class Test03VerificacaoCriptograficaAdulteracoesETOCTOU(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp(prefix="cat_tamper_")
        self.dir_cat = os.path.join(self.tmp_dir, "CATALOGO")
        shutil.copytree(DIR_CATALOGO_PADRAO, self.dir_cat)
        self.dir_v1 = os.path.join(self.dir_cat, "releases", "v1.0.0")
        self.addCleanup(_remover_arvore_segura, self.tmp_dir)

    def test_01_adulteracao_chave_publica_assinatura_e_manifesto(self) -> None:
        p_pem = os.path.join(self.dir_cat, "chave_publica_catalogo.pem")
        os.chmod(p_pem, stat.S_IWRITE | stat.S_IREAD)
        with open(p_pem, "ab") as fh:
            fh.write(b"\n")
        with self.assertRaises(IntegridadeCatalogoError):
            abrir_catalogo(self.dir_cat)

    def test_02_adulteracao_sig_e_recibo_e_jcs(self) -> None:
        # 1. Corromper assinatura .sig
        dir_c1 = os.path.join(self.tmp_dir, "c_sig")
        shutil.copytree(self.dir_cat, dir_c1)
        p_sig = os.path.join(dir_c1, "releases", "v1.0.0", "manifesto_catalogo.sig")
        os.chmod(p_sig, stat.S_IWRITE | stat.S_IREAD)
        with open(p_sig, "r", encoding="ascii") as fs:
            hex_orig = fs.read().strip()
        byte_trocado = ("0" if hex_orig[0] != "0" else "1") + hex_orig[1:]
        with open(p_sig, "w", encoding="ascii") as fs:
            fs.write(byte_trocado + "\n")
        with self.assertRaises(IntegridadeCatalogoError):
            abrir_catalogo(dir_c1)

        # 2. Ausencia e corrupcao de CONCLUSAO_PUBLICACAO.json
        dir_c2 = os.path.join(self.tmp_dir, "c_rec")
        shutil.copytree(self.dir_cat, dir_c2)
        p_rec = os.path.join(dir_c2, "releases", "v1.0.0", "CONCLUSAO_PUBLICACAO.json")
        os.chmod(p_rec, stat.S_IWRITE | stat.S_IREAD)
        with open(p_rec, "r", encoding="utf-8") as fr:
            rec = json.load(fr)
        rec["sha256_manifesto"] = "0" * 64
        with open(p_rec, "w", encoding="utf-8") as fr:
            json.dump(rec, fr)
        with self.assertRaises(IntegridadeCatalogoError):
            abrir_catalogo(dir_c2)
        os.remove(p_rec)
        with self.assertRaises(IntegridadeCatalogoError):
            abrir_catalogo(dir_c2)

        # 3. Manifesto valido semanticamente, mas formatado fora do padrao JCS canonico (mesmo com assinatura valida)
        dir_jcs = os.path.join(self.tmp_dir, "c_jcs")
        dir_jcs_ch = os.path.join(self.tmp_dir, "ch_jcs")
        os.makedirs(dir_jcs_ch, exist_ok=True)
        p_priv_t = os.path.join(dir_jcs_ch, "priv.key")
        p_pub_t = os.path.join(dir_jcs, "chave_publica_catalogo.pem")
        _, sha_t = gerar_par_chaves_catalogo_teste(p_priv_t, p_pub_t, dir_catalogo=dir_jcs)
        publicar_versao_catalogo(
            "v1.0.0",
            [{"J": 20, "seed": 4001, "jogos": _gerar_carteira_espelhada_valida(20, 4001)}],
            dir_catalogo=dir_jcs,
            caminho_chave_privada=p_priv_t,
            caminho_chave_publica=p_pub_t,
            ancora_sha256=sha_t,
        )
        dir_v_jcs = os.path.join(dir_jcs, "releases", "v1.0.0")
        p_man_jcs = os.path.join(dir_v_jcs, "manifesto_catalogo.json")
        os.chmod(p_man_jcs, stat.S_IWRITE | stat.S_IREAD)
        with open(p_man_jcs, "r", encoding="utf-8") as fm:
            man_obj = json.load(fm)
        with open(p_man_jcs, "w", encoding="utf-8") as fm:
            json.dump(man_obj, fm, indent=2, sort_keys=True, ensure_ascii=False)
        _assinar_manifesto_e_atualizar_recibo(
            dir_v_jcs, p_priv_t, os.path.join(dir_jcs, "catalogo_ativo.json")
        )
        with self.assertRaises(IntegridadeCatalogoError):
            abrir_catalogo(dir_jcs, caminho_chave_publica=p_pub_t, ancora_chave_publica_sha256=sha_t)

    def test_03_adulteracao_sqlite_inventario_e_particao_binaria_toctou(self) -> None:
        # 1. Arquivo extra nao declarado no inventario da release
        p_extra = os.path.join(self.dir_v1, "indice_catalogo.sqlite-wal")
        with open(p_extra, "wb") as fw:
            fw.write(b"fake-wal")
        with self.assertRaises(IntegridadeCatalogoError):
            abrir_catalogo(self.dir_cat)
        os.remove(p_extra)

        # 2. SQLite adulterado (sem remover arquivo)
        dir_sql = os.path.join(self.tmp_dir, "c_sql")
        shutil.copytree(self.dir_cat, dir_sql)
        p_sql = os.path.join(dir_sql, "releases", "v1.0.0", "indice_catalogo.sqlite")
        os.chmod(p_sql, stat.S_IWRITE | stat.S_IREAD)
        with open(p_sql, "r+b") as fsql:
            fsql.seek(-10, os.SEEK_END)
            b0 = fsql.read(1)
            fsql.seek(-10, os.SEEK_END)
            fsql.write(bytes([b0[0] ^ 0xFF]))
        with self.assertRaises(IntegridadeCatalogoError):
            abrir_catalogo(dir_sql)

        # 3. Particao binaria adulterada em 1 byte: nao deve entrar no cache
        leitor_ok, _ = abrir_catalogo(self.dir_cat)
        p_bin = os.path.join(
            self.dir_v1, "particoes", "ltm_ordem5r3_s1_1080k_J10000_seed330001.bin"
        )
        os.chmod(p_bin, stat.S_IWRITE | stat.S_IREAD)
        with open(p_bin, "r+b") as fb:
            fb.seek(123456)
            orig_b = fb.read(1)
            fb.seek(123456)
            fb.write(bytes([orig_b[0] ^ 0x01]))
        with self.assertRaises(IntegridadeCatalogoError):
            leitor_ok.obter_carteira(10000, 330001)
        self.assertEqual(leitor_ok.estatisticas_cache()["entradas"], 0)
        self.assertEqual(leitor_ok.estatisticas_cache()["bytes_em_uso"], 0)

        # Restaura byte e testa leitura controlada + invalidacao por mutacao pos-cache
        with open(p_bin, "r+b") as fb:
            fb.seek(123456)
            fb.write(orig_b)
        res_ok = leitor_ok.obter_carteira(10000, 330001)
        self.assertFalse(res_ok["cache_hit"])
        self.assertEqual(leitor_ok.estatisticas_cache()["bytes_em_uso"], 500000)

        time.sleep(0.02)
        with open(p_bin, "r+b") as fb:
            fb.seek(999)
            b_k = fb.read(1)
            fb.seek(999)
            fb.write(bytes([b_k[0] ^ 0x01]))
        with self.assertRaises(IntegridadeCatalogoError):
            leitor_ok.obter_carteira(10000, 330001, offset=0, limit=50)
        self.assertEqual(leitor_ok.estatisticas_cache()["bytes_em_uso"], 0)

    def test_04_fd_toctou_leitura_truncada_e_tamanho_divergente(self) -> None:
        p_bin = os.path.join(
            self.dir_v1, "particoes", "ltm_ordem5r3_s1_1080k_J10000_seed330001.bin"
        )
        dados, sig = ler_arquivo_controlado_fd(p_bin, tamanho_esperado=500000)
        self.assertEqual(len(dados), 500000)
        self.assertEqual(len(sig), 4)

        with self.assertRaises(IntegridadeCatalogoError):
            ler_arquivo_controlado_fd(p_bin, tamanho_esperado=500001)

        # Simula divergencia concorrente entre lstat e fstat no mesmo fd
        st_falso = mock.Mock(
            st_mode=stat.S_IFREG | 0o444,
            st_dev=sig[0],
            st_ino=sig[1],
            st_size=sig[2],
            st_mtime_ns=sig[3] + 100,
        )
        with mock.patch("catalogo_lotomania_10000.crypto_selo.os.fstat", return_value=st_falso):
            with self.assertRaises(IntegridadeCatalogoError):
                ler_arquivo_controlado_fd(p_bin, tamanho_esperado=500000)


class Test04CacheLimitesEInvalidacao(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp(prefix="cat_cache_")
        self.dir_cat = os.path.join(self.tmp_dir, "CATALOGO")
        self.dir_chaves = os.path.join(self.tmp_dir, "CHAVES")
        os.makedirs(self.dir_chaves, exist_ok=True)
        self.p_priv = os.path.join(self.dir_chaves, "catalogo_teste_ed25519.key")
        self.p_pub = os.path.join(self.dir_cat, "chave_publica_catalogo.pem")
        _, self.sha_pub = gerar_par_chaves_catalogo_teste(
            self.p_priv, self.p_pub, dir_catalogo=self.dir_cat
        )
        self.addCleanup(_remover_arvore_segura, self.tmp_dir)

    def test_01_lru_eviction_teto_bytes_e_rejeicao_teto_acima_32mb(self) -> None:
        with self.assertRaises(ValueError):
            LeitorCatalogoLotomania(
                self.dir_cat,
                caminho_chave_publica=self.p_pub,
                ancora_chave_publica_sha256=self.sha_pub,
                max_cache_bytes=LIMITE_MAXIMO_CACHE_BYTES + 1,
            )

        jogos_200_a = _gerar_carteira_espelhada_valida(200, 1001)
        jogos_200_b = _gerar_carteira_espelhada_valida(200, 1002)
        publicar_versao_catalogo(
            "v1.0.0",
            [
                {"J": 200, "seed": 1001, "jogos": jogos_200_a},
                {"J": 200, "seed": 1002, "jogos": jogos_200_b},
            ],
            dir_catalogo=self.dir_cat,
            caminho_chave_privada=self.p_priv,
            caminho_chave_publica=self.p_pub,
            ancora_sha256=self.sha_pub,
            ativar=True,
        )

        # Cada particao J=200 ocupa 10.000 bytes; teto=12.000 bytes so comporta 1 entrada por vez
        leitor, _ = abrir_catalogo(
            self.dir_cat,
            caminho_chave_publica=self.p_pub,
            ancora_chave_publica_sha256=self.sha_pub,
            max_cache_bytes=12000,
        )
        r_a1 = leitor.obter_carteira(200, 1001)
        self.assertFalse(r_a1["cache_hit"])
        self.assertEqual(leitor.estatisticas_cache()["bytes_em_uso"], 10000)

        r_a2 = leitor.obter_carteira(200, 1001, offset=0, limit=10)
        self.assertTrue(r_a2["cache_hit"])

        r_b1 = leitor.obter_carteira(200, 1002)
        self.assertFalse(r_b1["cache_hit"])
        stats = leitor.estatisticas_cache()
        self.assertLessEqual(stats["bytes_em_uso"], 12000)
        self.assertEqual(stats["entradas"], 1)

        # seed=1001 foi removida por LRU ao inserir seed=1002
        r_a3 = leitor.obter_carteira(200, 1001)
        self.assertFalse(r_a3["cache_hit"])

    def test_02_invalidacao_automatica_em_troca_versao_e_rollback(self) -> None:
        jogos_20 = _gerar_carteira_espelhada_valida(20, 2001)
        jogos_40 = _gerar_carteira_espelhada_valida(40, 2002)
        publicar_versao_catalogo(
            "v1.0.0",
            [{"J": 20, "seed": 2001, "jogos": jogos_20}],
            dir_catalogo=self.dir_cat,
            caminho_chave_privada=self.p_priv,
            caminho_chave_publica=self.p_pub,
            ancora_sha256=self.sha_pub,
            ativar=True,
        )
        leitor, info1 = abrir_catalogo(
            self.dir_cat,
            caminho_chave_publica=self.p_pub,
            ancora_chave_publica_sha256=self.sha_pub,
        )
        self.assertEqual(info1["versao_catalogo"], "v1.0.0")
        leitor.obter_carteira(20, 2001)
        self.assertEqual(leitor.estatisticas_cache()["entradas"], 1)

        publicar_versao_catalogo(
            "v1.0.1",
            [
                {"J": 20, "seed": 2001, "jogos": jogos_20},
                {"J": 40, "seed": 2002, "jogos": jogos_40},
            ],
            dir_catalogo=self.dir_cat,
            caminho_chave_privada=self.p_priv,
            caminho_chave_publica=self.p_pub,
            ancora_sha256=self.sha_pub,
            ativar=True,
        )
        # Proxima leitura no leitor ja aberto detecta nova versao ativa e limpa cache antigo
        r_40 = leitor.obter_carteira(40, 2002)
        self.assertEqual(r_40["versao_catalogo"], "v1.0.1")
        self.assertEqual(r_40["jogos"], jogos_40)

        rollback_versao_catalogo(
            "v1.0.0",
            dir_catalogo=self.dir_cat,
            caminho_chave_publica=self.p_pub,
            ancora_sha256=self.sha_pub,
        )
        with self.assertRaises(SolicitacaoForaDaGradeError):
            leitor.obter_carteira(40, 2002)
        r_20 = leitor.obter_carteira(20, 2001)
        self.assertEqual(r_20["versao_catalogo"], "v1.0.0")


class Test05PublicadorSegurancaFalhasEImutabilidade(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp_dir = tempfile.mkdtemp(prefix="cat_pub_")
        self.dir_cat = os.path.join(self.tmp_dir, "CATALOGO")
        self.dir_chaves = os.path.join(self.tmp_dir, "CHAVES")
        os.makedirs(self.dir_chaves, exist_ok=True)
        self.p_priv = os.path.join(self.dir_chaves, "catalogo_teste_ed25519.key")
        self.p_pub = os.path.join(self.dir_cat, "chave_publica_catalogo.pem")
        _, self.sha_pub = gerar_par_chaves_catalogo_teste(
            self.p_priv, self.p_pub, dir_catalogo=self.dir_cat
        )
        self.jogos_v1 = _gerar_carteira_espelhada_valida(20, 3001)
        self.jogos_v2 = _gerar_carteira_espelhada_valida(40, 3002)
        self.addCleanup(_remover_arvore_segura, self.tmp_dir)

    def test_01_recusa_chave_privada_no_repo_catalogo_ou_modo4(self) -> None:
        caminhos_proibidos = [
            os.path.join(_REPOSITORIO_RAIZ, "chave_indevida.key"),
            os.path.join(self.dir_cat, "chave.key"),
            os.path.join(self.dir_cat, "_staging", "chave.key"),
            os.path.join(_REPOSITORIO_RAIZ, "auditoria", "chave.key"),
            os.path.join(self.dir_chaves, "modo4_ed25519.key"),
            os.path.join(os.path.expanduser("~"), "B2B_chaves", "modo4_ed25519.key"),
        ]
        for p_proibido in caminhos_proibidos:
            with self.assertRaises(IntegridadeCatalogoError):
                publicar_versao_catalogo(
                    "v1.0.0",
                    [{"J": 20, "seed": 3001, "jogos": self.jogos_v1}],
                    dir_catalogo=self.dir_cat,
                    caminho_chave_privada=p_proibido,
                    caminho_chave_publica=self.p_pub,
                    ancora_sha256=self.sha_pub,
                )

    def test_02_recusa_carteira_invalida_e_sobrescrita_versao_imutavel(self) -> None:
        jogos_invalidos = [list(j) for j in self.jogos_v1]
        jogos_invalidos[1] = list(jogos_invalidos[0])
        with self.assertRaises(IntegridadeCatalogoError):
            publicar_versao_catalogo(
                "v1.0.0",
                [{"J": 20, "seed": 3001, "jogos": jogos_invalidos}],
                dir_catalogo=self.dir_cat,
                caminho_chave_privada=self.p_priv,
                caminho_chave_publica=self.p_pub,
                ancora_sha256=self.sha_pub,
            )

        publicar_versao_catalogo(
            "v1.0.0",
            [{"J": 20, "seed": 3001, "jogos": self.jogos_v1}],
            dir_catalogo=self.dir_cat,
            caminho_chave_privada=self.p_priv,
            caminho_chave_publica=self.p_pub,
            ancora_sha256=self.sha_pub,
        )
        with self.assertRaises(IntegridadeCatalogoError):
            publicar_versao_catalogo(
                "v1.0.0",
                [{"J": 20, "seed": 3001, "jogos": self.jogos_v1}],
                dir_catalogo=self.dir_cat,
                caminho_chave_privada=self.p_priv,
                caminho_chave_publica=self.p_pub,
                ancora_sha256=self.sha_pub,
            )

    def test_03_injecao_de_falhas_atomicas_e_recuperacao_limpa(self) -> None:
        publicar_versao_catalogo(
            "v1.0.0",
            [{"J": 20, "seed": 3001, "jogos": self.jogos_v1}],
            dir_catalogo=self.dir_cat,
            caminho_chave_privada=self.p_priv,
            caminho_chave_publica=self.p_pub,
            ancora_sha256=self.sha_pub,
        )
        leitor, _ = abrir_catalogo(
            self.dir_cat, caminho_chave_publica=self.p_pub, ancora_chave_publica_sha256=self.sha_pub
        )

        # Falha pos_staging e pre_rename_release: v1.0.1 nao aparece em releases/, v1.0.0 continua intacta
        for ponto in ("pos_staging", "pre_rename_release"):
            with self.assertRaises(FalhaInjetadaPublicacaoError):
                publicar_versao_catalogo(
                    "v1.0.1",
                    [{"J": 40, "seed": 3002, "jogos": self.jogos_v2}],
                    dir_catalogo=self.dir_cat,
                    caminho_chave_privada=self.p_priv,
                    caminho_chave_publica=self.p_pub,
                    ancora_sha256=self.sha_pub,
                    falha_em=ponto,
                )
            self.assertFalse(os.path.exists(os.path.join(self.dir_cat, "releases", "v1.0.1")))
            res_atual = leitor.obter_carteira(20, 3001)
            self.assertEqual(res_atual["versao_catalogo"], "v1.0.0")
            self.assertEqual(res_atual["jogos"], self.jogos_v1)

        # Falha pos_rename_release_pre_ponteiro: v1.0.1 existe completa, mas ponteiro ainda aponta v1.0.0
        with self.assertRaises(FalhaInjetadaPublicacaoError):
            publicar_versao_catalogo(
                "v1.0.1",
                [{"J": 40, "seed": 3002, "jogos": self.jogos_v2}],
                dir_catalogo=self.dir_cat,
                caminho_chave_privada=self.p_priv,
                caminho_chave_publica=self.p_pub,
                ancora_sha256=self.sha_pub,
                falha_em="pos_rename_release_pre_ponteiro",
            )
        self.assertTrue(os.path.isdir(os.path.join(self.dir_cat, "releases", "v1.0.1")))
        self.assertEqual(leitor.obter_carteira(20, 3001)["versao_catalogo"], "v1.0.0")

        # Falha durante escrita de .catalogo_ativo.json.tmp.* preserva v1.0.0 integra
        with self.assertRaises(FalhaInjetadaPublicacaoError):
            ativar_versao_publicada(
                "v1.0.1",
                dir_catalogo=self.dir_cat,
                caminho_chave_publica=self.p_pub,
                ancora_sha256=self.sha_pub,
                falha_em="durante_ponteiro_tmp",
            )
        self.assertEqual(leitor.obter_carteira(20, 3001)["versao_catalogo"], "v1.0.0")

        # Ativacao normal subsequente conclui transicao atomica para v1.0.1 e permite rollback
        ativar_versao_publicada(
            "v1.0.1",
            dir_catalogo=self.dir_cat,
            caminho_chave_publica=self.p_pub,
            ancora_sha256=self.sha_pub,
        )
        self.assertEqual(leitor.obter_carteira(40, 3002)["versao_catalogo"], "v1.0.1")

        # Rollback recusa versao corrompida antes de mover o ponteiro
        p_bin_v1 = os.path.join(
            self.dir_cat,
            "releases",
            "v1.0.0",
            "particoes",
            f"{montar_id_carteira(J=20, seed=3001, versao_algoritmo=VERSAO_ALGORITMO_PADRAO, sha256_configuracao=SHA256_CONFIGURACAO_PADRAO_S1_1080K)}.bin",
        )
        os.chmod(p_bin_v1, stat.S_IWRITE | stat.S_IREAD)
        with open(p_bin_v1, "r+b") as fb:
            fb.seek(0)
            fb.write(b"\xff")
        p_rec_v1 = os.path.join(self.dir_cat, "releases", "v1.0.0", "CONCLUSAO_PUBLICACAO.json")
        os.chmod(p_rec_v1, stat.S_IWRITE | stat.S_IREAD)
        os.remove(p_rec_v1)
        with self.assertRaises(IntegridadeCatalogoError):
            rollback_versao_catalogo(
                "v1.0.0",
                dir_catalogo=self.dir_cat,
                caminho_chave_publica=self.p_pub,
                ancora_sha256=self.sha_pub,
            )
        # v1.0.1 segue ativa mesmo apos rollback rejeitado
        self.assertEqual(leitor.obter_carteira(40, 3002)["versao_catalogo"], "v1.0.1")


class Test06DesacoplamentoASTESelados(unittest.TestCase):
    def test_01_ausencia_absoluta_de_assert_no_catalogo_e_nos_testes(self) -> None:
        arquivos = [
            os.path.join(_REPOSITORIO_RAIZ, "catalogo_lotomania_10000", nome)
            for nome in sorted(os.listdir(os.path.join(_REPOSITORIO_RAIZ, "catalogo_lotomania_10000")))
            if nome.endswith(".py")
        ]
        arquivos.append(os.path.abspath(__file__))

        for caminho in arquivos:
            with open(caminho, "r", encoding="utf-8") as fh:
                arvore = ast.parse(fh.read(), filename=caminho)
            nos_assert = [n for n in ast.walk(arvore) if isinstance(n, ast.Assert)]
            self.assertEqual(
                nos_assert,
                [],
                msg=f"Instrucao assert proibida encontrada em '{caminho}'.",
            )

    def test_02_desacoplamento_runtime_leitor_nao_importa_otimizador_nem_publicador(self) -> None:
        script = (
            "import json, sys; "
            "from catalogo_lotomania_10000 import abrir_catalogo; "
            "leitor, _ = abrir_catalogo(); "
            "res = leitor.obter_carteira(10000, 330001, offset=0, limit=10); "
            "proibidos = ['lotomania_carteira_10000', 'lotomania_carteira_10000.construtiva', "
            "'lotomania_carteira_10000.otimizador_swap', 'catalogo_lotomania_10000.publicador']; "
            "carregados = [m for m in proibidos if m in sys.modules]; "
            "print(json.dumps({'retornados': res['retornados'], 'carregados': carregados}))"
        )
        for flags in ([], ["-O"]):
            proc = subprocess.run(
                [sys.executable, *flags, "-c", script],
                cwd=_REPOSITORIO_RAIZ,
                capture_output=True,
                text=True,
                check=True,
            )
            dados = json.loads(proc.stdout.strip())
            self.assertEqual(dados["retornados"], 10)
            self.assertEqual(dados["carregados"], [])

    def test_03_integridade_integral_arquivos_selados_e_passo1(self) -> None:
        for rel_path, sha_esperado in HASHES_ARQUIVOS_PROTEGIDOS.items():
            caminho_abs = os.path.join(_REPOSITORIO_RAIZ, rel_path.replace("/", os.sep))
            self.assertTrue(os.path.isfile(caminho_abs), msg=f"Arquivo protegido ausente: {rel_path}")
            h = hashlib.sha256()
            with open(caminho_abs, "rb") as fh:
                while True:
                    bloco = fh.read(65536)
                    if not bloco:
                        break
                    h.update(bloco)
            self.assertEqual(h.hexdigest(), sha_esperado, msg=f"Violacao de selo em {rel_path}")

        self.assertTrue(os.path.isfile(CAMINHO_CHAVE_PRIVADA_PADRAO))
        self.assertIn("probabilidade", CLAUSULA_OBRIGATORIA)


if __name__ == "__main__":
    unittest.main(verbosity=2)
