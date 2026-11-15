# -*- coding: utf-8 -*-
"""
Canonicalizacao decimal exata, serializacao JCS (RFC 8785) e identidade
deterministica de configuracao para o catalogo imutavel `CATALOGO_LOTOMANIA_10000`.

Zero instrucoes `assert` para execucao identica em `python` e `python -O`.
"""

from decimal import Decimal, InvalidOperation
import hashlib
import json
import re
from typing import Any, Dict, Mapping, Tuple, Union

VERSAO_ALGORITMO_PADRAO = "ordem5-r3-s1-1080k-v1.0"
ESTRATEGIA_FASE3_PADRAO = "S1_atual_top8"
ESQUEMA_CATALOGO_VERSAO = "1.0.0"

CLAUSULA_OBRIGATORIA = (
    "O sistema não prevê resultados futuros nem altera a probabilidade matemática "
    "individual de premiação de qualquer bilhete. Seu objetivo é otimizar a "
    "distribuição combinatória dos bilhetes de uma carteira, buscando reduzir a "
    "redundância entre eventos premiados e melhorar a cobertura conjunta observada."
)

# Parametros reais declarados exclusivamente por strings decimais exatas (sem float binario).
CONFIGURACAO_PADRAO_S1_1080K: Dict[str, Any] = {
    "estrategia_fase3": ESTRATEGIA_FASE3_PADRAO,
    "max_tentativas_f3": 1080000,
    "tau_primario": 35,
    "alpha_25": "30",
    "alpha_win": "1",
    "alpha_1": "0.08",
    "alpha_2": "0.25",
    "gamma_plus": "0.02",
    "batch0": 80,
}

CHAVES_CONFIGURACAO_OBRIGATORIAS = frozenset(CONFIGURACAO_PADRAO_S1_1080K.keys())
CHAVES_REAIS_CONFIGURACAO = ("alpha_25", "alpha_win", "alpha_1", "alpha_2", "gamma_plus")

_RE_TEXTO_DECIMAL_ESTRITO = re.compile(r"^[+-]?(?:\d+(?:\.\d*)?|\.\d+)$")


def exigir(condicao: bool, mensagem: str, exc_cls: type = RuntimeError) -> None:
    """Garante invariante em tempo de execucao sem depender de `assert`."""
    if condicao is not True:
        raise exc_cls(mensagem)


def _validar_inteiro_estrito(valor: Any, nome: str, *, minimo: int, maximo: int) -> int:
    if type(valor) is not int:
        raise TypeError(f"{nome} deve ser int exato (recebido {type(valor).__name__}).")
    if valor < minimo or valor > maximo:
        raise ValueError(f"{nome} fora do intervalo [{minimo}, {maximo}]: {valor}.")
    return valor


def formatar_decimal_canonico(valor: Union[int, str, Decimal]) -> str:
    """
    Converte inteiro estrito, string decimal sintaticamente estrita ou `Decimal` em
    representacao decimal canonica unica sem notacao cientifica.

    Rejeita explicitamente `bool`, `float`, `NaN`, infinitos e qualquer forma de `-0`.
    """
    if type(valor) is bool or type(valor) is float:
        raise TypeError(
            f"Valor real canonico nao pode ser {type(valor).__name__}; utilize Decimal, int ou str decimal."
        )
    if type(valor) is int:
        return str(valor)

    if isinstance(valor, Decimal):
        dec = valor
    elif isinstance(valor, str):
        if not valor or valor != valor.strip() or "_" in valor:
            raise ValueError(f"String decimal invalida ou com espacos/sublinhados: {valor!r}.")
        if not _RE_TEXTO_DECIMAL_ESTRITO.match(valor):
            raise ValueError(f"Representacao decimal fora da sintaxe estrita: {valor!r}.")
        try:
            dec = Decimal(valor)
        except InvalidOperation as exc:
            raise ValueError(f"Valor decimal invalido: {valor!r}.") from exc
    else:
        raise TypeError(
            f"Tipo nao suportado para canonicalizacao decimal: {type(valor).__name__}."
        )

    if not dec.is_finite():
        raise ValueError(f"Valor decimal nao finito rejeitado: {valor!r}.")
    if dec.is_zero():
        if dec.is_signed():
            raise ValueError(f"Zero negativo (-0) rejeitado na canonicalizacao: {valor!r}.")
        return "0"

    norm = dec.normalize()
    sign, digits, exp = norm.as_tuple()
    if type(exp) is not int:
        raise ValueError(f"Expoente decimal invalido: {exp!r}.")
    if abs(exp) > 100 or len(digits) + max(0, exp) > 120:
        raise ValueError(f"Magnitude decimal excede limite canonico seguro: {valor!r}.")

    dig_str = "".join(str(d) for d in digits)
    if exp >= 0:
        corpo = dig_str + ("0" * exp)
    else:
        pos_ponto = len(dig_str) + exp
        if pos_ponto <= 0:
            corpo = "0." + ("0" * (-pos_ponto)) + dig_str
        else:
            corpo = dig_str[:pos_ponto] + "." + dig_str[pos_ponto:]
    return ("-" + corpo) if sign == 1 else corpo


def _validar_estrutura_sem_float(obj: Any, caminho: str = "$") -> None:
    if obj is None or type(obj) is bool or type(obj) is int or type(obj) is str:
        return
    if type(obj) is float:
        raise TypeError(f"Float binario proibido em objeto JCS canonico no caminho {caminho}.")
    if isinstance(obj, list):
        for idx, item in enumerate(obj):
            _validar_estrutura_sem_float(item, f"{caminho}[{idx}]")
        return
    if isinstance(obj, dict):
        for chave, val in obj.items():
            if type(chave) is not str:
                raise TypeError(
                    f"Chave JSON deve ser str exata em {caminho} (recebido {type(chave).__name__})."
                )
            _validar_estrutura_sem_float(val, f"{caminho}.{chave}")
        return
    raise TypeError(
        f"Tipo nao suportado em serializacao JCS canonica em {caminho}: {type(obj).__name__}."
    )


def serializar_jcs_canonico(obj: Mapping[str, Any]) -> bytes:
    """
    Serializa objeto JSON canonico segundo esquema JCS (RFC 8785) sobre tipos exatos
    (`dict`, `list`, `str`, `int`, `bool`, `None`), rejeitando qualquer `float`.
    """
    if not isinstance(obj, dict):
        raise TypeError(f"Objeto raiz JCS deve ser dict (recebido {type(obj).__name__}).")
    _validar_estrutura_sem_float(obj)
    texto = json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return texto.encode("utf-8")


def canonicalizar_configuracao(config: Mapping[str, Any]) -> Dict[str, Any]:
    """Valida e normaliza exatamente os nove parametros de configuracao geradora."""
    if not isinstance(config, Mapping):
        raise TypeError("configuracao deve ser um Mapping.")
    chaves = set(config.keys())
    if chaves != CHAVES_CONFIGURACAO_OBRIGATORIAS:
        faltantes = sorted(CHAVES_CONFIGURACAO_OBRIGATORIAS - chaves)
        extras = sorted(chaves - CHAVES_CONFIGURACAO_OBRIGATORIAS)
        raise ValueError(
            f"Configuracao deve conter exatamente as chaves canonicas (faltantes={faltantes}, extras={extras})."
        )

    estrategia = config["estrategia_fase3"]
    if type(estrategia) is not str or not estrategia.strip() or estrategia != estrategia.strip():
        raise ValueError("estrategia_fase3 deve ser str nao vazia e sem espacos laterais.")

    canonica: Dict[str, Any] = {
        "estrategia_fase3": estrategia,
        "max_tentativas_f3": _validar_inteiro_estrito(
            config["max_tentativas_f3"], "max_tentativas_f3", minimo=0, maximo=100_000_000
        ),
        "tau_primario": _validar_inteiro_estrito(
            config["tau_primario"], "tau_primario", minimo=25, maximo=50
        ),
        "batch0": _validar_inteiro_estrito(
            config["batch0"], "batch0", minimo=1, maximo=10_000
        ),
    }
    for chave_real in CHAVES_REAIS_CONFIGURACAO:
        canonica[chave_real] = formatar_decimal_canonico(config[chave_real])
    return canonica


def calcular_sha256_configuracao(
    config: Mapping[str, Any],
) -> Tuple[Dict[str, Any], bytes, str]:
    """Retorna `(config_normalizada, bytes_jcs, sha256_configuracao)` deterministicamente."""
    canonica = canonicalizar_configuracao(config)
    bytes_jcs = serializar_jcs_canonico(canonica)
    digest = hashlib.sha256(bytes_jcs).hexdigest()
    return canonica, bytes_jcs, digest


_, _BYTES_JCS_PADRAO, SHA256_CONFIGURACAO_PADRAO_S1_1080K = calcular_sha256_configuracao(
    CONFIGURACAO_PADRAO_S1_1080K
)


def montar_id_carteira(
    *,
    J: int,
    seed: int,
    versao_algoritmo: str,
    sha256_configuracao: str,
) -> str:
    """Constroi identificador canonico e livre de colisoes para entrada de catalogo."""
    _validar_inteiro_estrito(J, "J", minimo=2, maximo=10000)
    exigir(J % 2 == 0, f"J deve ser par (recebido {J}).", ValueError)
    exigir(type(seed) is int, "seed deve ser int estrito.", TypeError)
    exigir(
        type(versao_algoritmo) is str and len(versao_algoritmo) > 0,
        "versao_algoritmo deve ser str nao vazia.",
        ValueError,
    )
    exigir(
        type(sha256_configuracao) is str and len(sha256_configuracao) == 64,
        "sha256_configuracao deve ter 64 hex.",
        ValueError,
    )
    if (
        versao_algoritmo == VERSAO_ALGORITMO_PADRAO
        and sha256_configuracao == SHA256_CONFIGURACAO_PADRAO_S1_1080K
    ):
        return f"ltm_ordem5r3_s1_1080k_J{J}_seed{seed}"
    return f"ltm_J{J}_seed{seed}_{sha256_configuracao[:12]}"
