# -*- coding: utf-8 -*-
"""
SINCRONIZADOR E AUDITOR DA BASE OFICIAL LOTOFACIL: API DA CAIXA
==================================================================
Sincroniza todos os concursos oficiais diretamente de:
    https://servicebus2.caixa.gov.br/portaldeloterias/api/lotofacil/{n}

Garantias de auditoria:
- Retomada idempotente via cache incremental JSONL (.cache_caixa_parcial.jsonl).
- Controle adaptativo de vazao (token pacing + pausa coordenada em HTTP 429).
- Validacao estrita por concurso (numero, data DD/MM/YYYY, 15 dezenas unicas
  em [1..25], consistencia entre listaDezenas e dezenasSorteadasOrdemSorteio).
- Confronto integral contra o arquivo legado local data/lotofacil.json sem
  alterar artefatos da Lotomania MODO 4 v1.2 nem o cache legado.
- Geracao deterministica do dataset canonico e relatorio de integridade com SHA-256.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import hashlib
import http.client
import json
import os
import random
import re
import ssl
import threading
import time
from typing import Any, Dict, List, Optional, Tuple
import unicodedata
import urllib.parse
import xml.etree.ElementTree as ET
import zipfile

from .etapa1_regras_oficiais import (
    API_OFICIAL_CAIXA_URL,
    TAMANHO_SORTEIO,
    UNIVERSO_TOTAL,
    validar_aposta_lotofacil,
    validar_inteiro_estrito,
)


class ErroIntegridadeBaseCaixaError(RuntimeError):
    """Excecao explicita levantada quando a base oficial apresenta inconformidade."""


VERSAO_SINCRONIZADOR = "1.1.0-etapa1-homologada"
HOST_CAIXA = "servicebus2.caixa.gov.br"
CAMINHO_API_BASE = "/portaldeloterias/api/lotofacil"
CABECALHOS_CAIXA = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) B2BLoterias-Auditoria/1.0",
    "Accept": "application/json",
    "Connection": "keep-alive",
}

_thread_local = threading.local()


class _ControladorVazaoCaixa:
    """Coordena cadencia global entre threads e pausa compartilhada em HTTP 429."""

    def __init__(self, intervalo_inicial: float = 0.08) -> None:
        self._lock = threading.Lock()
        self.intervalo = intervalo_inicial
        self._proximo_slot = 0.0
        self._cooldown_ate = 0.0
        self._sucessos_seguidos = 0

    def aguardar_slot(self) -> None:
        while True:
            with self._lock:
                agora = time.monotonic()
                alvo = max(self._proximo_slot, self._cooldown_ate)
                if agora >= alvo:
                    self._proximo_slot = agora + self.intervalo
                    return
                espera = alvo - agora
            time.sleep(min(espera, 1.0))

    def registrar_sucesso(self) -> None:
        with self._lock:
            self._sucessos_seguidos += 1
            if self._sucessos_seguidos >= 45:
                self._sucessos_seguidos = 0
                self.intervalo = max(0.055, self.intervalo * 0.94)

    def registrar_throttling(self, pausa_sugerida: Optional[float] = None) -> float:
        with self._lock:
            self._sucessos_seguidos = 0
            pausa = pausa_sugerida if pausa_sugerida is not None else 3.5
            pausa = max(1.5, min(30.0, pausa))
            self.intervalo = min(0.50, max(self.intervalo * 1.35, 0.14))
            agora = time.monotonic()
            self._cooldown_ate = max(self._cooldown_ate, agora + pausa)
            self._proximo_slot = max(self._proximo_slot, self._cooldown_ate)
            return pausa


def _obter_conexao_caixa() -> http.client.HTTPSConnection:
    conn = getattr(_thread_local, "conn", None)
    if conn is None:
        ctx = ssl.create_default_context()
        conn = http.client.HTTPSConnection(HOST_CAIXA, timeout=20, context=ctx)
        _thread_local.conn = conn
    return conn


def _resetar_conexao_caixa() -> None:
    conn = getattr(_thread_local, "conn", None)
    if conn is not None:
        try:
            conn.close()
        except Exception:
            pass
        _thread_local.conn = None


def _interpretar_retry_after(valor: Optional[str]) -> Optional[float]:
    if not valor:
        return None
    try:
        return float(valor.strip())
    except ValueError:
        return None


def _buscar_json_caixa(
    subcaminho: str,
    tentativas: int = 10,
    controlador: Optional[_ControladorVazaoCaixa] = None,
) -> Dict[str, Any]:
    """Busca payload JSON diretamente na API oficial da CAIXA com controle de vazao."""
    ultimo_erro: Optional[Exception] = None
    for tentativa in range(tentativas):
        if controlador is not None:
            controlador.aguardar_slot()
        try:
            conn = _obter_conexao_caixa()
            conn.request("GET", subcaminho, headers=CABECALHOS_CAIXA)
            resp = conn.getresponse()
            raw = resp.read()
            if resp.status == 200:
                if controlador is not None:
                    controlador.registrar_sucesso()
                return json.loads(raw.decode("utf-8"))
            if resp.status in (301, 302, 303, 307, 308):
                loc = resp.getheader("Location")
                if loc:
                    parsed = urllib.parse.urlparse(loc)
                    subcaminho = parsed.path or subcaminho
                _resetar_conexao_caixa()
                continue
            if resp.status in (429, 503):
                retry_s = _interpretar_retry_after(resp.getheader("Retry-After"))
                pausa_base = retry_s if retry_s is not None else min(15.0, 2.0 * (1.4 ** tentativa))
                _resetar_conexao_caixa()
                ultimo_erro = ErroIntegridadeBaseCaixaError(
                    f"HTTP {resp.status} ao consultar {subcaminho}"
                )
                if controlador is not None:
                    controlador.registrar_throttling(pausa_base)
                else:
                    time.sleep(pausa_base + random.uniform(0.1, 0.6))
                continue
            ultimo_erro = ErroIntegridadeBaseCaixaError(
                f"HTTP {resp.status} ao consultar {subcaminho}"
            )
            _resetar_conexao_caixa()
        except Exception as exc:
            ultimo_erro = exc
            _resetar_conexao_caixa()
        time.sleep(min(4.0, 0.35 * (2 ** min(tentativa, 4))) + random.uniform(0.05, 0.25))

    raise ErroIntegridadeBaseCaixaError(
        f"Falha ao obter {subcaminho} apos {tentativas} tentativas: {ultimo_erro}"
    )


def _normalizar_data_br_para_iso(data_br: str, numero: int) -> str:
    if not isinstance(data_br, str) or not data_br.strip():
        raise ErroIntegridadeBaseCaixaError(f"Concurso {numero}: dataApuracao ausente.")
    texto = data_br.strip()
    try:
        dt = datetime.datetime.strptime(texto, "%d/%m/%Y")
    except ValueError as exc:
        raise ErroIntegridadeBaseCaixaError(
            f"Concurso {numero}: formato invalido de dataApuracao '{texto}'."
        ) from exc
    return dt.strftime("%Y-%m-%d")


def _extrair_inteiros_dezenas(lista: Any, nome: str, numero: int) -> Tuple[int, ...]:
    if not isinstance(lista, list) or len(lista) != TAMANHO_SORTEIO:
        raise ErroIntegridadeBaseCaixaError(
            f"Concurso {numero}: campo '{nome}' invalido ({lista!r})."
        )
    valores: List[int] = []
    for item in lista:
        if isinstance(item, bool):
            raise ErroIntegridadeBaseCaixaError(f"Concurso {numero}: booleano em '{nome}'.")
        try:
            n = int(str(item).strip())
        except ValueError as exc:
            raise ErroIntegridadeBaseCaixaError(
                f"Concurso {numero}: valor nao numerico em '{nome}': {item!r}."
            ) from exc
        if not (1 <= n <= UNIVERSO_TOTAL):
            raise ErroIntegridadeBaseCaixaError(
                f"Concurso {numero}: dezena fora de [1..25] em '{nome}': {n}."
            )
        valores.append(n)
    if len(set(valores)) != TAMANHO_SORTEIO:
        raise ErroIntegridadeBaseCaixaError(
            f"Concurso {numero}: dezenas duplicadas em '{nome}': {valores}."
        )
    return tuple(valores)


def normalizar_registro_caixa(payload: Dict[str, Any], numero_esperado: Optional[int] = None) -> Dict[str, Any]:
    """Valida e normaliza um registro oficial de concurso retornado pela CAIXA."""
    numero = validar_inteiro_estrito(payload.get("numero"), "numero", 1)
    if numero_esperado is not None and numero != numero_esperado:
        raise ErroIntegridadeBaseCaixaError(
            f"Divergencia de concurso: esperado {numero_esperado}, recebido {numero}."
        )

    data_br = str(payload.get("dataApuracao", "")).strip()
    data_iso = _normalizar_data_br_para_iso(data_br, numero)

    dezenas_ord_raw = _extrair_inteiros_dezenas(payload.get("listaDezenas"), "listaDezenas", numero)
    dezenas_ordenadas = list(validar_aposta_lotofacil(dezenas_ord_raw, TAMANHO_SORTEIO))

    ordem_sorteio_raw = payload.get("dezenasSorteadasOrdemSorteio")
    if ordem_sorteio_raw:
        ordem_sorteio = list(_extrair_inteiros_dezenas(ordem_sorteio_raw, "dezenasSorteadasOrdemSorteio", numero))
        if sorted(ordem_sorteio) != dezenas_ordenadas:
            raise ErroIntegridadeBaseCaixaError(
                f"Concurso {numero}: divergencia entre listaDezenas e dezenasSorteadasOrdemSorteio."
            )
    else:
        ordem_sorteio = []

    rateio_limpo: List[Dict[str, Any]] = []
    for faixa in payload.get("listaRateioPremio") or []:
        if not isinstance(faixa, dict):
            continue
        rateio_limpo.append(
            {
                "faixa": int(faixa.get("faixa", 0)),
                "descricao": str(faixa.get("descricaoFaixa", "")).strip(),
                "ganhadores": int(faixa.get("numeroDeGanhadores", 0)),
                "valor_premio": float(faixa.get("valorPremio", 0.0)),
            }
        )
    rateio_limpo.sort(key=lambda x: x["faixa"])

    return {
        "numero": numero,
        "data_apuracao": data_br,
        "data_iso": data_iso,
        "dezenas": dezenas_ordenadas,
        "ordem_sorteio": ordem_sorteio,
        "acumulado": bool(payload.get("acumulado", False)),
        "valor_arrecadado": float(payload.get("valorArrecadado") or 0.0),
        "rateio": rateio_limpo,
    }


def _carregar_cache_parcial(caminho_cache: str) -> Dict[int, Dict[str, Any]]:
    registros: Dict[int, Dict[str, Any]] = {}
    if not os.path.isfile(caminho_cache):
        return registros
    with open(caminho_cache, "r", encoding="utf-8") as f:
        for linha in f:
            linha_s = linha.strip()
            if not linha_s:
                continue
            try:
                rec = json.loads(linha_s)
                num = int(rec["numero"])
                registros[num] = rec
            except Exception:
                continue
    return registros


def calcular_sha256_bytes(dados: bytes) -> str:
    return hashlib.sha256(dados).hexdigest()


def calcular_sha256_arquivo(caminho: str) -> str:
    h = hashlib.sha256()
    with open(caminho, "rb") as f:
        for bloco in iter(lambda: f.read(65536), b""):
            h.update(bloco)
    return h.hexdigest()


def _normalizar_rotulo_coluna(texto: Any) -> str:
    s = unicodedata.normalize("NFKD", str(texto or ""))
    s = s.encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().strip().split())


def _parsear_moeda_brl(valor: Any) -> float:
    if valor is None:
        return 0.0
    texto = str(valor).strip()
    if not texto:
        return 0.0
    limpo = texto.replace("R$", "").replace("r$", "").replace(" ", "")
    if "," in limpo:
        limpo = limpo.replace(".", "").replace(",", ".")
    try:
        return float(limpo)
    except ValueError as exc:
        raise ErroIntegridadeBaseCaixaError(f"Valor monetario invalido na planilha CAIXA: {valor!r}") from exc


def _parsear_inteiro_xlsx(valor: Any, nome: str, numero: int) -> int:
    if valor is None or str(valor).strip() == "":
        return 0
    try:
        return int(float(str(valor).strip()))
    except ValueError as exc:
        raise ErroIntegridadeBaseCaixaError(
            f"Concurso {numero}: valor inteiro invalido em '{nome}': {valor!r}."
        ) from exc


def _indice_coluna_excel(referencia: str) -> int:
    m = re.match(r"([A-Za-z]+)", referencia or "")
    if not m:
        raise ErroIntegridadeBaseCaixaError(f"Referencia de celula XLSX invalida: {referencia!r}.")
    total = 0
    for ch in m.group(1).upper():
        total = total * 26 + (ord(ch) - 64)
    return total - 1


def carregar_concursos_planilha_caixa(caminho_xlsx: str) -> Tuple[List[Dict[str, Any]], str]:
    """
    Carrega e valida integralmente a planilha oficial XLSX baixada de
    https://loterias.caixa.gov.br/Paginas/Lotofacil.aspx utilizando apenas stdlib.
    """
    if not os.path.isfile(caminho_xlsx):
        raise FileNotFoundError(f"Planilha oficial CAIXA nao encontrada: {caminho_xlsx}")

    sha_xlsx = calcular_sha256_arquivo(caminho_xlsx)
    ns = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"

    with zipfile.ZipFile(caminho_xlsx, "r") as zf:
        shared_strings: List[str] = []
        if "xl/sharedStrings.xml" in zf.namelist():
            root_ss = ET.fromstring(zf.read("xl/sharedStrings.xml"))
            shared_strings = ["".join(si.itertext()) for si in root_ss.findall(f"{ns}si")]

        if "xl/worksheets/sheet1.xml" not in zf.namelist():
            raise ErroIntegridadeBaseCaixaError("Planilha oficial CAIXA sem xl/worksheets/sheet1.xml.")
        root_ws = ET.fromstring(zf.read("xl/worksheets/sheet1.xml"))

    rows = root_ws.findall(f".//{ns}sheetData/{ns}row")
    if len(rows) < 2:
        raise ErroIntegridadeBaseCaixaError("Planilha oficial CAIXA sem linhas de dados.")

    def _ler_linha(el_row: ET.Element) -> Dict[int, str]:
        celulas: Dict[int, str] = {}
        col_atual = 0
        for c in el_row.findall(f"{ns}c"):
            ref = c.get("r")
            if ref:
                col_atual = _indice_coluna_excel(ref)
            tipo = c.get("t")
            v_el = c.find(f"{ns}v")
            is_el = c.find(f"{ns}is")
            if tipo == "s" and v_el is not None and v_el.text is not None:
                valor = shared_strings[int(v_el.text)]
            elif tipo == "inlineStr" and is_el is not None:
                valor = "".join(is_el.itertext())
            elif v_el is not None and v_el.text is not None:
                valor = v_el.text
            else:
                valor = ""
            celulas[col_atual] = valor
            col_atual += 1
        return celulas

    cabecalho_raw = _ler_linha(rows[0])
    mapa_cols = {_normalizar_rotulo_coluna(v): k for k, v in cabecalho_raw.items() if str(v).strip()}

    obrigatorias = [
        "concurso",
        "data sorteio",
        *(f"bola{i}" for i in range(1, TAMANHO_SORTEIO + 1)),
        "ganhadores 15 acertos",
        "rateio 15 acertos",
        "ganhadores 14 acertos",
        "rateio 14 acertos",
        "ganhadores 13 acertos",
        "rateio 13 acertos",
        "ganhadores 12 acertos",
        "rateio 12 acertos",
        "ganhadores 11 acertos",
        "rateio 11 acertos",
        "arrecadacao total",
    ]
    ausentes = [col for col in obrigatorias if col not in mapa_cols]
    if ausentes:
        raise ErroIntegridadeBaseCaixaError(
            f"Colunas obrigatorias ausentes na planilha oficial CAIXA: {ausentes}"
        )

    registros: List[Dict[str, Any]] = []
    for row_el in rows[1:]:
        vals = _ler_linha(row_el)
        conc_str = str(vals.get(mapa_cols["concurso"], "")).strip()
        if not conc_str:
            continue
        numero = validar_inteiro_estrito(int(float(conc_str)), "concurso", 1)
        data_br = str(vals.get(mapa_cols["data sorteio"], "")).strip()
        data_iso = _normalizar_data_br_para_iso(data_br, numero)

        dezs_brutas = [vals.get(mapa_cols[f"bola{i}"], "") for i in range(1, TAMANHO_SORTEIO + 1)]
        dezenas = list(validar_aposta_lotofacil(_extrair_inteiros_dezenas(dezs_brutas, "Bola1..Bola15", numero), TAMANHO_SORTEIO))

        faixas_espec = (
            (1, 15, "15 acertos"),
            (2, 14, "14 acertos"),
            (3, 13, "13 acertos"),
            (4, 12, "12 acertos"),
            (5, 11, "11 acertos"),
        )
        rateio_limpo: List[Dict[str, Any]] = []
        ganhadores_15 = 0
        for codigo_faixa, acertos, desc in faixas_espec:
            g = _parsear_inteiro_xlsx(vals.get(mapa_cols[f"ganhadores {acertos} acertos"]), desc, numero)
            p = _parsear_moeda_brl(vals.get(mapa_cols[f"rateio {acertos} acertos"]))
            if acertos == 15:
                ganhadores_15 = g
            rateio_limpo.append(
                {
                    "faixa": codigo_faixa,
                    "descricao": desc,
                    "ganhadores": g,
                    "valor_premio": p,
                }
            )

        acum_val = _parsear_moeda_brl(vals.get(mapa_cols.get("acumulado 15 acertos", -1)))
        arrecadacao = _parsear_moeda_brl(vals.get(mapa_cols["arrecadacao total"]))

        registros.append(
            {
                "numero": numero,
                "data_apuracao": data_br,
                "data_iso": data_iso,
                "dezenas": dezenas,
                "ordem_sorteio": [],
                "acumulado": bool(ganhadores_15 == 0 and acum_val > 0.0) if "acumulado 15 acertos" in mapa_cols else bool(ganhadores_15 == 0),
                "valor_arrecadado": arrecadacao,
                "rateio": rateio_limpo,
            }
        )

    registros.sort(key=lambda r: r["numero"])
    numeros_vistos: set[int] = set()
    duplicados: List[int] = []
    for rec in registros:
        num = rec["numero"]
        if num in numeros_vistos:
            duplicados.append(num)
        numeros_vistos.add(num)
    if duplicados:
        raise ErroIntegridadeBaseCaixaError(
            f"Concursos duplicados detectados na planilha CAIXA: {duplicados}"
        )

    for idx, rec in enumerate(registros, start=1):
        if rec["numero"] != idx:
            raise ErroIntegridadeBaseCaixaError(
                f"Sequencia quebrada na planilha CAIXA: esperado {idx}, encontrado {rec['numero']}."
            )

    return registros, sha_xlsx


def sincronizar_base_oficial_caixa(
    diretorio_repo: Optional[str] = None,
    max_workers: int = 3,
    concurso_limite: Optional[int] = None,
    caminho_planilha: Optional[str] = None,
    preferir_planilha: bool = True,
) -> Dict[str, Any]:
    """
    Sincroniza integralmente todos os concursos 1..ultimo diretamente da fonte
    oficial da CAIXA (planilha oficial XLSX da CAIXA e/ou API oficial CAIXA),
    valida consistencia, confronta com data/lotofacil.json e amostra da API,
    e grava a base canonica datada + relatorio de auditoria com SHA-256.
    """
    base_dir = diretorio_repo or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    pasta_dados = os.path.join(base_dir, "lotofacil_modo4", "dados")
    pasta_auditoria = os.path.join(base_dir, "auditoria", "lotofacil_modo4")
    os.makedirs(pasta_dados, exist_ok=True)
    os.makedirs(pasta_auditoria, exist_ok=True)

    caminho_cache = os.path.join(pasta_dados, ".cache_caixa_parcial.jsonl")
    caminho_xlsx_padrao = os.path.join(pasta_dados, "caixa_lotofacil_oficial.xlsx")
    caminho_xlsx = caminho_planilha or caminho_xlsx_padrao
    caminho_destino = os.path.join(pasta_dados, "lotofacil_oficial_caixa.json")
    caminho_relatorio = os.path.join(pasta_auditoria, "auditoria_base_caixa_etapa1.json")
    caminho_legado = os.path.join(base_dir, "data", "lotofacil.json")

    cache_api = _carregar_cache_parcial(caminho_cache)
    confronto_api: Dict[str, Any] = {"presente": bool(cache_api)}
    sha_planilha_oficial: Optional[str] = None
    origem_utilizada = API_OFICIAL_CAIXA_URL
    arquivo_planilha_relativo: Optional[str] = None

    if preferir_planilha and os.path.isfile(caminho_xlsx):
        registros_xlsx, sha_planilha_oficial = carregar_concursos_planilha_caixa(caminho_xlsx)
        if concurso_limite is not None:
            registros_xlsx = [r for r in registros_xlsx if r["numero"] <= concurso_limite]
        cache = {r["numero"]: r for r in registros_xlsx}
        alvo_final = len(cache)
        origem_utilizada = "https://loterias.caixa.gov.br/Paginas/Lotofacil.aspx (Planilha Oficial CAIXA .xlsx)"
        arquivo_planilha_relativo = "lotofacil_modo4/dados/caixa_lotofacil_oficial.xlsx"

        if cache_api:
            divergencias_api: List[int] = []
            confrontados_api = 0
            for num_api, rec_api in sorted(cache_api.items()):
                if num_api not in cache:
                    continue
                confrontados_api += 1
                rec_xlsx = cache[num_api]
                if (
                    rec_xlsx["dezenas"] != rec_api["dezenas"]
                    or rec_xlsx["data_apuracao"] != rec_api["data_apuracao"]
                ):
                    divergencias_api.append(num_api)
            confronto_api.update(
                {
                    "concursos_api_confrontados": confrontados_api,
                    "qtd_divergencias_api_vs_planilha": len(divergencias_api),
                    "divergencias_api_vs_planilha": divergencias_api,
                }
            )
            if divergencias_api:
                raise ErroIntegridadeBaseCaixaError(
                    f"Divergencia entre planilha CAIXA e API CAIXA nos concursos: {divergencias_api}"
                )
    else:
        controlador = _ControladorVazaoCaixa(intervalo_inicial=0.065)
        ultimo_payload = _buscar_json_caixa(CAMINHO_API_BASE, controlador=controlador)
        ultimo_reg = normalizar_registro_caixa(ultimo_payload)
        ultimo_disponivel = ultimo_reg["numero"]
        alvo_final = ultimo_disponivel if concurso_limite is None else min(concurso_limite, ultimo_disponivel)

        cache = dict(cache_api)
        cache[ultimo_reg["numero"]] = ultimo_reg
        faltantes = [n for n in range(1, alvo_final + 1) if n not in cache]

        if faltantes:
            lock_arquivo = threading.Lock()
            total_faltantes = len(faltantes)
            concluidos = 0
            with open(caminho_cache, "a", encoding="utf-8", buffering=1) as f_cache:
                def _baixar_um(n: int) -> Dict[str, Any]:
                    payload = _buscar_json_caixa(f"{CAMINHO_API_BASE}/{n}", controlador=controlador)
                    return normalizar_registro_caixa(payload, numero_esperado=n)

                with ThreadPoolExecutor(max_workers=max_workers) as pool:
                    futuros = {pool.submit(_baixar_um, n): n for n in faltantes}
                    for fut in as_completed(futuros):
                        rec = fut.result()
                        with lock_arquivo:
                            cache[rec["numero"]] = rec
                            f_cache.write(json.dumps(rec, ensure_ascii=False) + "\n")
                            concluidos += 1
                            if concluidos % 250 == 0 or concluidos == total_faltantes:
                                print(
                                    f"[CAIXA] Progresso: {len(cache)}/{alvo_final} concursos "
                                    f"(lote {concluidos}/{total_faltantes}, intervalo={controlador.intervalo:.3f}s)",
                                    flush=True,
                                )

    concursos_ordenados: List[Dict[str, Any]] = []
    for n in range(1, alvo_final + 1):
        if n not in cache:
            raise ErroIntegridadeBaseCaixaError(f"Concurso faltante apos sincronizacao: {n}.")
        rec = cache[n]
        # Revalidacao rigorosa em memoria antes de selar o arquivo canonico
        validar_aposta_lotofacil(rec["dezenas"], TAMANHO_SORTEIO)
        if sorted(rec["dezenas"]) != rec["dezenas"]:
            raise ErroIntegridadeBaseCaixaError(f"Concurso {n}: dezenas fora de ordem crescente.")
        concursos_ordenados.append(rec)

    # Confronto integral com o dataset legado data/lotofacil.json (se existir)
    confronto_legado: Dict[str, Any] = {"presente": os.path.isfile(caminho_legado)}
    if confronto_legado["presente"]:
        sha_legado = calcular_sha256_arquivo(caminho_legado)
        with open(caminho_legado, "r", encoding="utf-8") as f_leg:
            legado_raw = json.load(f_leg)
        chaves_legado = sorted(int(k) for k in legado_raw.keys())
        divergencias_conjunto: List[int] = []
        divergencias_ordem_sorteio: List[int] = []
        comparados = 0
        for k in chaves_legado:
            if k not in cache:
                continue
            comparados += 1
            dezs_leg = [int(x) for x in legado_raw[str(k)]]
            rec_caixa = cache[k]
            if sorted(dezs_leg) != rec_caixa["dezenas"]:
                divergencias_conjunto.append(k)
            if rec_caixa["ordem_sorteio"] and dezs_leg != rec_caixa["ordem_sorteio"]:
                divergencias_ordem_sorteio.append(k)

        confronto_legado.update(
            {
                "caminho": "data/lotofacil.json",
                "sha256": sha_legado,
                "concursos_legado_total": len(chaves_legado),
                "primeiro_concurso_legado": chaves_legado[0] if chaves_legado else None,
                "ultimo_concurso_legado": chaves_legado[-1] if chaves_legado else None,
                "concursos_confrontados": comparados,
                "divergencias_dezenas_conjunto": divergencias_conjunto,
                "qtd_divergencias_conjunto": len(divergencias_conjunto),
                "divergencias_ordem_sorteio": divergencias_ordem_sorteio,
                "qtd_divergencias_ordem_sorteio": len(divergencias_ordem_sorteio),
                "novos_concursos_apos_legado": max(0, alvo_final - (chaves_legado[-1] if chaves_legado else 0)),
            }
        )

    payload_concursos_bytes = json.dumps(
        concursos_ordenados, ensure_ascii=False, separators=(",", ":"), sort_keys=True
    ).encode("utf-8")
    sha_concursos_canonico = calcular_sha256_bytes(payload_concursos_bytes)

    if not cache_api and os.path.isfile(caminho_relatorio):
        try:
            with open(caminho_relatorio, "r", encoding="utf-8") as f_prev:
                aud_prev = json.load(f_prev)
            if (
                aud_prev.get("sha256_lista_concursos_canonica") == sha_concursos_canonico
                and aud_prev.get("confronto_amostra_api_caixa", {}).get("presente")
            ):
                confronto_api = dict(aud_prev["confronto_amostra_api_caixa"])
                confronto_api["validado_no_mesmo_sha256_canonico"] = True
        except Exception:
            pass

    ausentes = [n for n in range(1, alvo_final + 1) if n not in cache]
    numeros_lista = [r["numero"] for r in concursos_ordenados]
    vistos_final: set[int] = set()
    duplicados_final: List[int] = []
    for n_chk in numeros_lista:
        if n_chk in vistos_final:
            duplicados_final.append(n_chk)
        vistos_final.add(n_chk)

    relatorio_integridade_concursos = {
        "total_concursos": len(concursos_ordenados),
        "primeiro_concurso": concursos_ordenados[0]["numero"],
        "ultimo_concurso": concursos_ordenados[-1]["numero"],
        "ausentes": ausentes,
        "qtd_ausentes": len(ausentes),
        "duplicados": duplicados_final,
        "qtd_duplicados": len(duplicados_final),
    }

    origens_separadas = {
        "planilha_historica_oficial": {
            "utilizada": bool(arquivo_planilha_relativo),
            "caminho": arquivo_planilha_relativo,
            "sha256": sha_planilha_oficial,
            "pagina_oficial": "https://loterias.caixa.gov.br/Paginas/Lotofacil.aspx",
            "preserva_ordem_sorteio_fisica": False,
            "observacao": "Planilha CAIXA fornece Bola1..Bola15 ordenadas crescentemente; campo ordem_sorteio mantido vazio [] sem preenchimento artificial.",
        },
        "amostras_api_json_caixa": {
            "endpoint": API_OFICIAL_CAIXA_URL,
            **confronto_api,
        },
    }

    registro_transformacoes = [
        "1. Leitura direta de xl/sharedStrings.xml e xl/worksheets/sheet1.xml via stdlib zipfile + xml.etree.ElementTree (sem macros ou inferencias).",
        "2. Mapeamento explicito de cabecalhos e referencias de coluna Excel (suportando celulas esparsas e sequenciais).",
        "3. Conversao deterministica de valores monetarios 'R$...' para float e inteiros de ganhadores.",
        "4. Validacao estrita de data DD/MM/YYYY -> YYYY-MM-DD e de 15 dezenas unicas no intervalo [1..25].",
        "5. Ordenacao crescente por numero de concurso (1..3828), verificando ausencia de lacunas e duplicatas, preservando ordem_sorteio=[] na ausencia de ordem fisica.",
        "6. Serializacao UTF-8 deterministica da lista de concursos e calculo de SHA-256 do arquivo XLSX, do JSON completo e da lista canonica.",
    ]

    documento_base = {
        "modalidade": "lotofacil",
        "versao_sincronizador": VERSAO_SINCRONIZADOR,
        "origem_oficial": origem_utilizada,
        "arquivo_planilha_oficial": arquivo_planilha_relativo,
        "sha256_planilha_oficial_caixa": sha_planilha_oficial,
        "sincronizado_em_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "total_concursos": len(concursos_ordenados),
        "primeiro_concurso": concursos_ordenados[0]["numero"],
        "primeiro_data_apuracao": concursos_ordenados[0]["data_apuracao"],
        "ultimo_concurso": concursos_ordenados[-1]["numero"],
        "ultimo_data_apuracao": concursos_ordenados[-1]["data_apuracao"],
        "concursos_faltantes": len(ausentes),
        "sha256_lista_concursos_canonica": sha_concursos_canonico,
        "origens_separadas": origens_separadas,
        "registro_transformacoes": registro_transformacoes,
        "relatorio_integridade_concursos": relatorio_integridade_concursos,
        "confronto_base_legada": confronto_legado,
        "confronto_amostra_api_caixa": confronto_api,
        "concursos": concursos_ordenados,
    }

    conteudo_bytes = (json.dumps(documento_base, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    with open(caminho_destino, "wb") as f_dest:
        f_dest.write(conteudo_bytes)
    sha_arquivo_destino = calcular_sha256_bytes(conteudo_bytes)

    resumo_auditoria = {
        "versao_sincronizador": VERSAO_SINCRONIZADOR,
        "origem_oficial": origem_utilizada,
        "arquivo_planilha_oficial": arquivo_planilha_relativo,
        "sha256_planilha_oficial_caixa": sha_planilha_oficial,
        "sincronizado_em_utc": documento_base["sincronizado_em_utc"],
        "arquivo_canonico": "lotofacil_modo4/dados/lotofacil_oficial_caixa.json",
        "tamanho_bytes": len(conteudo_bytes),
        "sha256_arquivo": sha_arquivo_destino,
        "sha256_lista_concursos_canonica": sha_concursos_canonico,
        "total_concursos": documento_base["total_concursos"],
        "primeiro_concurso": documento_base["primeiro_concurso"],
        "primeiro_data_apuracao": documento_base["primeiro_data_apuracao"],
        "ultimo_concurso": documento_base["ultimo_concurso"],
        "ultimo_data_apuracao": documento_base["ultimo_data_apuracao"],
        "concursos_faltantes": len(ausentes),
        "origens_separadas": origens_separadas,
        "registro_transformacoes": registro_transformacoes,
        "relatorio_integridade_concursos": relatorio_integridade_concursos,
        "confronto_base_legada": confronto_legado,
        "confronto_amostra_api_caixa": confronto_api,
    }
    with open(caminho_relatorio, "w", encoding="utf-8") as f_aud:
        json.dump(resumo_auditoria, f_aud, ensure_ascii=False, indent=2)
        f_aud.write("\n")

    if concurso_limite is None and os.path.isfile(caminho_cache):
        os.remove(caminho_cache)

    return resumo_auditoria


if __name__ == "__main__":
    rel = sincronizar_base_oficial_caixa()
    print(json.dumps(rel, ensure_ascii=False, indent=2))
