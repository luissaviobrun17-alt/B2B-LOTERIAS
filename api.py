from fastapi import FastAPI, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
import uvicorn
import urllib.request
import json
import os
import sys
import logging
import uuid

logger = logging.getLogger('api.loteria_b2b')


def _garantir_fluxos_padrao_seguros() -> None:
    """Garante stdout/stderr validos quando iniciado via pythonw.exe (sem console)."""
    if sys.stdout is not None and sys.stderr is not None:
        return
    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.join(base_dir, "logs", "api_server.log")
    stream = None
    try:
        os.makedirs(os.path.dirname(log_path), exist_ok=True)
        if os.path.exists(log_path) and os.path.getsize(log_path) > 2 * 1024 * 1024:
            backup_path = log_path + ".1"
            try:
                if os.path.exists(backup_path):
                    os.remove(backup_path)
                os.replace(log_path, backup_path)
            except OSError:
                pass
        stream = open(log_path, "a", encoding="utf-8", buffering=1)
    except OSError:
        try:
            stream = open(os.devnull, "a", encoding="utf-8")
        except OSError:
            stream = None
    if stream is not None:
        if sys.stdout is None:
            sys.stdout = stream
        if sys.stderr is None:
            sys.stderr = stream


_garantir_fluxos_padrao_seguros()
try:
    from motor_sugestao import MotorSugestaoLoteria
except ImportError:
    MotorSugestaoLoteria = None
from motor_lotomania import MotorLotomaniaB2B
try:
    from motor_lotofacil import MotorLotofacilB2B
except ImportError:
    MotorLotofacilB2B = None
try:
    from motor_timemania import MotorTimemaniaB2B
except ImportError:
    MotorTimemaniaB2B = None
try:
    from motor_diadesorte import MotorDiaDeSorteB2B
except ImportError:
    MotorDiaDeSorteB2B = None
try:
    from motor_megasena import MotorMegaSenaB2B
except ImportError:
    MotorMegaSenaB2B = None
try:
    from motor_supersete import MotorSuperSeteB2B
except ImportError:
    MotorSuperSeteB2B = None
try:
    from motor_quina import MotorQuinaB2B
except ImportError:
    MotorQuinaB2B = None

app = FastAPI(
    title="Loteria B2B AI Engine API",
    description="API REST de Alta Performance para Motores Matematicos de Loterias B2B.",
    version="2.0.0"
)

# Configuracao de CORS para permitir acesso do front-end
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Modelos de Dados
class SugestaoRequest(BaseModel):
    nome_loteria: str
    historico: Optional[List[List[int]]] = None
    quantidade_sugestao: Optional[int] = None

class CoberturaIARequest(BaseModel):
    nome_loteria: str
    pool_selecionado: List[int]
    quantidade_jogos: int
    fixas: Optional[List[int]] = None
    historico: Optional[List[List[int]]] = None
    is_sniper: Optional[bool] = False

class OtimizarCoberturaRequest(BaseModel):
    quantidade_jogos: int = Field(default=20, ge=1, le=10000, strict=True, description="Quantidade de jogos (entre 1 e 10000, tipo estrito)")
    permitir_espelhos: bool = Field(default=True, strict=True, description="Permitir geracao de pares espelho complementares")
    seed: Optional[int] = Field(default=None, strict=True, description="Semente opcional para reprodutibilidade estocastica (tipo estrito)")
    trace: Optional[bool] = Field(default=False, strict=True, description="Incluir rastreamento intermediario das etapas de selecao")

class ConferirModo4Request(BaseModel):
    jogos: List[List[int]] = Field(..., min_length=1, description="Lista nao vazia de bilhetes de 50 dezenas para conferencia")
    concurso: Optional[int] = Field(default=None, strict=True, description="Numero do concurso na base de referencia (1 a 2699)")

class BacktestCientificoRequest(BaseModel):
    concursos_teste: Optional[int] = 30
    quantidade_jogos_por_concurso: Optional[int] = 10
    modo: Optional[str] = "matematico_puro"
    seed: Optional[int] = 42

class AnaliseParesTriosRequest(BaseModel):
    limite_top: Optional[int] = 50
    janela: Optional[int] = None

class MotorLotomaniaRequest(BaseModel):
    quantidade_jogos: int
    historico_limite: Optional[int] = None
    estrategia: Optional[str] = "equilibrada"
    historico: Optional[List[List[int]]] = None

class BacktestLotomaniaRequest(BaseModel):
    concurso_alvo_idx: Optional[int] = None
    quantidade_jogos: Optional[int] = 10
    estrategia: Optional[str] = "equilibrada"

class MotorLotomaniaGruposRequest(BaseModel):
    grupos: Dict[str, List[int]]
    combinacoes: Optional[List[List[int]]] = None
    modo: Optional[str] = "planilha_126"
    qtd_grupos_por_jogo: Optional[int] = 5
    eliminar_duplicados: Optional[bool] = False
    ordenar_dezenas: Optional[bool] = True
    fixas: Optional[List[int]] = None
    excluidas: Optional[List[int]] = None

class MotorLotofacilRequest(BaseModel):
    quantidade_jogos: int
    historico_limite: Optional[int] = None
    estrategia: Optional[str] = "equilibrada"
    sniper: Optional[bool] = True
    fixas: Optional[List[int]] = None
    excluidas: Optional[List[int]] = None
    historico: Optional[List[List[int]]] = None

class BacktestLotofacilRequest(BaseModel):
    concurso_alvo_idx: Optional[int] = None
    quantidade_jogos: Optional[int] = 20
    estrategia: Optional[str] = "equilibrada"
    sniper: Optional[bool] = True

class MotorLotofacilGruposRequest(BaseModel):
    grupos: Dict[str, List[int]]
    combinacoes: Optional[List[List[int]]] = None
    qtd_grupos_por_jogo: Optional[int] = 5
    eliminar_duplicados: Optional[bool] = False
    ordenar_dezenas: Optional[bool] = True
    fixas: Optional[List[int]] = None
    excluidas: Optional[List[int]] = None


class MotorTimemaniaRequest(BaseModel):
    quantidade_jogos: int
    modo: Optional[str] = "original"
    base_games: Optional[List[List[int]]] = None
    blocos_selecionados: Optional[List[int]] = None
    usar_base_invertida: Optional[bool] = False
    ambas_bases: Optional[bool] = False
    historico_limite: Optional[int] = None
    estrategia: Optional[str] = "equilibrada"
    sniper: Optional[bool] = False
    no_consecutive_3_in_group: Optional[bool] = True
    max_consecutive_total: Optional[int] = 3
    pool: Optional[List[int]] = None
    estrategia_time: Optional[str] = "maior_ift"
    time_fixo_usuario: Optional[str] = None
    historico: Optional[List[List[int]]] = None
    historico_times: Optional[List[str]] = None

class ComparadorTimemaniaRequest(BaseModel):
    quantidade_jogos: Optional[int] = 64
    base_games: Optional[List[List[int]]] = None
    concursos_backtest: Optional[int] = 50

class CoberturaTimemaniaRequest(BaseModel):
    jogos: List[List[int]]

class BaseInvertidaRequest(BaseModel):
    base_games: Optional[List[List[int]]] = None

class BacktestTimemaniaRequest(BaseModel):
    concursos_teste: Optional[int] = 50
    quantidade_jogos: Optional[int] = 10
    estrategia: Optional[str] = "equilibrada"
    sniper: Optional[bool] = False
    no_consecutive_3_in_group: Optional[bool] = True
    pool: Optional[List[int]] = None

class AnaliseTimemaniaRequest(BaseModel):
    historico_limite: Optional[int] = None
    pool: Optional[List[int]] = None


def obter_historico_caixa(nome_loteria: str) -> List[List[int]]:
    mapping = {
        "megasena": "megasena",
        "lotofacil": "lotofacil",
        "quina": "quina",
        "lotomania": "lotomania",
        "duplasena": "duplasena",
        "diadesorte": "diadesorte",
        "supersete": "supersete",
        "super-sete": "supersete",
        "super_sete": "supersete",
        "timemania": "timemania"
    }
    
    loteria_normalizada = nome_loteria.lower().strip().replace(" ", "").replace("-", "").replace("á", "a").replace("ó", "o")
    loteria_key = "megasena"
    for k, v in mapping.items():
        if k in loteria_normalizada:
            loteria_key = v
            break

    base_dir = os.path.dirname(os.path.abspath(__file__))
    possible_paths = [
        os.path.join(base_dir, "data", f"{loteria_key}.json"),
        os.path.join("data", f"{loteria_key}.json"),
        os.path.join(base_dir, "..", "data", f"{loteria_key}.json")
    ]
    cache_path = os.path.join(base_dir, "data", f"{loteria_key}.json")
    for p_cand in possible_paths:
        if os.path.exists(p_cand):
            cache_path = p_cand
            break

    data = None
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception as e:
            print(f"Erro ao ler cache local de {loteria_key}: {e}")

    if not data:
        url = f"https://raw.githubusercontent.com/guilhermeasn/loteria.json/master/data/{loteria_key}.json"
        print(f"Baixando historico de {loteria_key} de: {url}")
        try:
            req = urllib.request.Request(
                url, 
                headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            )
            with urllib.request.urlopen(req, timeout=15) as response:
                content = response.read().decode('utf-8')
                data = json.loads(content)
                
                with open(cache_path, "w", encoding="utf-8") as f:
                    f.write(content)
        except Exception as e:
            print(f"Erro ao baixar dados da web para {loteria_key}: {e}")
            raise HTTPException(
                status_code=500, 
                detail=f"Nao foi possivel baixar o historico da loteria {nome_loteria}."
            )

    try:
        sorted_keys = sorted(data.keys(), key=lambda x: int(x))
        historico = []
        for key in sorted_keys:
            draw = [int(x) for x in data[key] if str(x).isdigit()]
            if draw:
                historico.append(draw)
        return historico
    except Exception as e:
        print(f"Erro ao processar dados de {loteria_key}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Erro de processamento nos dados historicos da loteria {nome_loteria}."
        )


@app.post("/api/v1/gerar-cobertura-ia")
def endpoint_gerar_cobertura_ia(request: CoberturaIARequest):
    """Endpoint do Motor Cascata."""
    try:
        from motor_cascata import MotorCascata

        historico = request.historico
        if not historico:
            historico = obter_historico_caixa(request.nome_loteria)

        motor = MotorCascata(
            pool=request.pool_selecionado,
            historico=historico,
            fixas=request.fixas or [],
            is_sniper=request.is_sniper
        )

        resultado = motor.gerar_jogos(request.quantidade_jogos)
        if "erro" in resultado:
            raise HTTPException(status_code=400, detail=resultado["erro"])

        jogos = resultado["jogos"]
        probabilidade = motor.calcular_probabilidade(jogos)

        return {
            "sucesso": True,
            "jogos": jogos,
            "grupos": resultado["grupos"],
            "tamanho_grupo": resultado["tamanho_grupo"],
            "nivel_cascata": resultado["nivel"],
            "total_candidatos": resultado["total_candidatos"],
            "total_descartados": resultado["total_descartados"],
            "cobertura": probabilidade,
            "s_alta": resultado.get("s_alta", []),
            "s_baixa": resultado.get("s_baixa", [])
        }
    except HTTPException as he:
        raise he
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# NOVO MÓDULO EXCLUSIVO: MOTOR LOTOMANIA DO B2B LOTERIAS
# =============================================================================

@app.post("/api/v1/motor-lotomania")
def endpoint_motor_lotomania(request: MotorLotomaniaRequest):
    """
    Endpoint exclusivo do MOTOR LOTOMANIA — B2B LOTERIAS.
    Aplica divisão estrita em 5 conjuntos C(20,10)^5, filtro <= 4 consecutivos,
    scoring multicritério, diversificação de carteira e auditoria 10 pontos.
    """
    try:
        historico = request.historico
        if not historico:
            historico = obter_historico_caixa("lotomania")

        estrategia_norm = request.estrategia or "equilibrada"
        if estrategia_norm in ("cobertura_maxima", "modo4", "otimizador_cobertura"):
            estrategia_norm = "modo_4"

        motor = MotorLotomaniaB2B(
            historico=historico,
            limite_historico=request.historico_limite,
            estrategia=estrategia_norm
        )

        resultado = motor.gerar_carteira(request.quantidade_jogos)
        return resultado
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Motor Lotomania: {str(e)}")


@app.post("/api/v1/motor-lotomania/backtest")
def endpoint_motor_lotomania_backtest(request: BacktestLotomaniaRequest):
    """Executa simulação histórica (backtesting) sem vazamento de dados futuros."""
    try:
        historico = obter_historico_caixa("lotomania")
        alvo = request.concurso_alvo_idx
        if alvo is None or alvo <= 0:
            alvo = len(historico) - 1

        motor = MotorLotomaniaB2B(historico=historico, estrategia=request.estrategia or "equilibrada")
        resultado = motor.executar_backtesting(
            concurso_alvo_idx=alvo,
            quantidade_jogos=request.quantidade_jogos or 10,
            estrategia=request.estrategia
        )
        return {"sucesso": True, "backtest": resultado}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Backtest Lotomania: {str(e)}")


@app.post("/api/v1/motor-lotomania/grupos")
def endpoint_motor_lotomania_grupos(request: MotorLotomaniaGruposRequest):
    """
    Endpoint do MOTOR DE FECHAMENTO POR GRUPOS DA LOTOMANIA - B2B LOTERIAS.
    O jogador define os 10 grupos de 10 dezenas e o motor une as combinacoes de 5 grupos (50 dezenas).
    """
    try:
        resultado = MotorLotomaniaB2B.gerar_jogos_por_grupos(
            grupos=request.grupos,
            combinacoes=request.combinacoes,
            modo=request.modo or "fechamento_total",
            qtd_grupos_por_jogo=request.qtd_grupos_por_jogo or 5,
            eliminar_duplicados=request.eliminar_duplicados or False,
            ordenar_dezenas=request.ordenar_dezenas if request.ordenar_dezenas is not None else True,
            fixas=request.fixas,
            excluidas=request.excluidas
        )
        return resultado
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Motor Lotomania por Grupos: {str(e)}")


@app.post("/api/v1/motor-lotomania/analise-janelas")
def endpoint_motor_lotomania_analise_janelas():
    """Retorna analise detalhada das 4 janelas temporais (3, 5, 10, 15 concursos) e comparativo integrado."""
    try:
        historico = obter_historico_caixa("lotomania")
        motor = MotorLotomaniaB2B(historico=historico)
        return motor.analisar_quatro_janelas()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na analise de janelas Lotomania: {str(e)}")


@app.post("/api/v1/motor-lotomania/pares-trios")
def endpoint_motor_lotomania_pares_trios(request: Optional[AnaliseParesTriosRequest] = None):
    """Retorna investigacao estatistica dos 4.950 pares e 161.700 trios com correcao de Bonferroni."""
    try:
        historico = obter_historico_caixa("lotomania")
        motor = MotorLotomaniaB2B(historico=historico)
        limite = request.limite_top if request else 50
        janela = request.janela if request else None
        res_pares = motor.analisar_pares(limite_top=limite, janela=janela)
        res_trios = motor.analisar_trios(limite_top=limite, janela=janela)
        return {
            "sucesso": True,
            "pares": res_pares,
            "trios": res_trios
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na analise de pares/trios Lotomania: {str(e)}")


@app.post("/api/v1/motor-lotomania/ifm")
def endpoint_motor_lotomania_ifm():
    """Retorna o Indice de Forca Matematica (IFM) e ranking completo das 100 dezenas."""
    try:
        historico = obter_historico_caixa("lotomania")
        motor = MotorLotomaniaB2B(historico=historico)
        return motor.calcular_ifm()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no calculo IFM Lotomania: {str(e)}")


@app.post("/api/v1/motor-lotomania/backtest-cientifico")
def endpoint_motor_lotomania_backtest_cientifico(request: BacktestCientificoRequest):
    """Executa backtesting retrospectivo walk-forward com comparacao Monte Carlo, teste t e intervalos de confianca."""
    try:
        historico = obter_historico_caixa("lotomania")
        motor = MotorLotomaniaB2B(historico=historico)
        return motor.executar_backtesting_multiplo(
            concursos_teste=request.concursos_teste or 30,
            quantidade_jogos_por_concurso=request.quantidade_jogos_por_concurso or 10,
            modo=request.modo or "matematico_puro",
            seed=request.seed or 42
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Backtest Cientifico Lotomania: {str(e)}")


@app.post("/api/v1/motor-lotomania/auditoria")
def endpoint_motor_lotomania_auditoria():
    """Retorna relatorio integrado de integridade e honestidade cientifica."""
    try:
        historico = obter_historico_caixa("lotomania")
        motor = MotorLotomaniaB2B(historico=historico)
        return motor.gerar_relatorio_auditoria_completo()
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na auditoria Lotomania: {str(e)}")


# =============================================================================
# COMPONENTE DE VERIFICACAO DE INICIALIZACAO E NUCLEO ISOLADO MODO 4 (v1.2)
# =============================================================================
from verificador_selo_modo4 import (
    CLAUSULA_OBRIGATORIA_MODO4,
    IDENTIFICACAO_OFICIAL_MODO4,
    IntegridadeModo4Error,
    verificar_selo_modo4,
)
from lotomania_modo4_jobs import (
    encerrar_gerenciador_jobs_lotomania_modo4,
    obter_gerenciador_jobs_lotomania_modo4,
    validar_e_serializar_resultado_lotomania_modo4,
)

try:
    from lotofacil_modo4.promocao_producao import (
        obter_status_health_lotofacil_modo4,
        registrar_lotofacil_modo4_na_api,
    )
    _LOTOFACIL_MODO4_ERRO_IMPORT = None
except Exception as _exc_lf4:
    obter_status_health_lotofacil_modo4 = None
    registrar_lotofacil_modo4_na_api = None
    _LOTOFACIL_MODO4_ERRO_IMPORT = str(_exc_lf4)


def _status_lotofacil_modo4_health():
    if obter_status_health_lotofacil_modo4 is not None:
        return obter_status_health_lotofacil_modo4(app)
    return {
        "disponivel": False,
        "feature_flag_ativa": False,
        "status": "bloqueado_erro_import",
        "motivo_indisponibilidade": _LOTOFACIL_MODO4_ERRO_IMPORT or "modulo_indisponivel",
        "fallback_permitido": False,
    }

_MODO4_SELO_INICIAL = None
_MODO4_ERRO_INICIAL = None
MotorLotomaniaModo4 = None

try:
    # Verificacao criptografica realizada ANTES de carregar o nucleo MODO 4
    _MODO4_SELO_INICIAL = verificar_selo_modo4()
    from motor_lotomania_modo4 import MotorLotomaniaModo4 as _MotorModo4Cls
    MotorLotomaniaModo4 = _MotorModo4Cls
except Exception as _exc_m4:
    _MODO4_ERRO_INICIAL = str(_exc_m4)
    logger.error("Bloqueio de inicializacao do MODO 4 v1.2: %s", _exc_m4)


@app.get("/health")
def endpoint_health():
    """
    Rota oficial de saude do servidor matematico e verificacao em tempo real
    do selamento criptografico Ed25519 do motor Lotomania MODO 4 v1.2.
    """
    try:
        parametros_rt = (
            MotorLotomaniaModo4.obter_parametros_runtime()
            if MotorLotomaniaModo4 is not None
            else None
        )
        status_selo = verificar_selo_modo4(parametros_runtime=parametros_rt)
        if MotorLotomaniaModo4 is None:
            from motor_lotomania_modo4 import MotorLotomaniaModo4 as _M4
            globals()["MotorLotomaniaModo4"] = _M4
            status_selo = verificar_selo_modo4(parametros_runtime=_M4.obter_parametros_runtime())

        return {
            "status": "ok",
            "api_operacional": True,
            "modo4_disponivel": True,
            "modo4": {
                "disponivel": True,
                "identificacao_oficial": IDENTIFICACAO_OFICIAL_MODO4,
                "versao_motor": "1.2",
                "selo_valido": True,
                "algoritmo_assinatura": status_selo["algoritmo_assinatura"],
                "integridade_base_historica": True,
                "corte_historico_concurso": status_selo["corte_historico_concurso"],
                "historico_geracao": None,
                "limite_min_jogos": 1,
                "limite_max_jogos": 10000,
                "sha256_manifesto": status_selo["sha256_manifesto"],
                "arquivos_verificados": status_selo["arquivos_verificados"],
                "clausula_obrigatoria": CLAUSULA_OBRIGATORIA_MODO4,
            },
            "lotofacil_modo4": _status_lotofacil_modo4_health(),
        }
    except Exception as exc:
        logger.error("Falha na verificacao de saude do MODO 4: %s", exc)
        return {
            "status": "degraded",
            "api_operacional": True,
            "modo4_disponivel": False,
            "modo4": {
                "disponivel": False,
                "identificacao_oficial": IDENTIFICACAO_OFICIAL_MODO4,
                "versao_motor": "1.2",
                "selo_valido": False,
                "integridade_base_historica": False,
                "motivo_bloqueio": "Selo criptografico invalido ou arquivos de referencia adulterados.",
                "clausula_obrigatoria": CLAUSULA_OBRIGATORIA_MODO4,
            },
            "lotofacil_modo4": _status_lotofacil_modo4_health(),
        }


def _validar_requisicao_e_selo_lotomania_modo4(request: OtimizarCoberturaRequest) -> None:
    """Valida estritamente tipos de entrada e integridade Ed25519/SHA-256 do MODO 4."""
    if type(request.quantidade_jogos) is not int or not (1 <= request.quantidade_jogos <= 10000):
        raise HTTPException(
            status_code=422,
            detail="quantidade_jogos deve ser um inteiro estrito entre 1 e 10.000.",
        )
    if request.seed is not None and type(request.seed) is not int:
        raise HTTPException(
            status_code=422,
            detail="seed deve ser um inteiro estrito ou null.",
        )
    if type(request.permitir_espelhos) is not bool:
        raise HTTPException(
            status_code=422,
            detail="permitir_espelhos deve ser booleano estrito.",
        )

    verificar_selo_modo4(
        parametros_runtime=(
            MotorLotomaniaModo4.obter_parametros_runtime()
            if MotorLotomaniaModo4 is not None
            else None
        )
    )


@app.post("/api/v1/lotomania-modo4/gerar")
def endpoint_lotomania_modo4_gerar(request: OtimizarCoberturaRequest):
    """
    Endpoint exclusivo do OTIMIZADOR COMBINATÓRIO DE DISPERSÃO E COBERTURA CONJUNTA
    — LOTOMANIA | MODO 4 — v1.2.
    Opera com verificacao previa de selo Ed25519, historico=None e limite estrito 1..10.000.
    """
    try:
        _validar_requisicao_e_selo_lotomania_modo4(request)
        if MotorLotomaniaModo4 is None:
            from motor_lotomania_modo4 import MotorLotomaniaModo4 as _M4
            globals()["MotorLotomaniaModo4"] = _M4

        motor = MotorLotomaniaModo4(verificar_selo=True)
        resultado = motor.gerar_carteira_otimizada_cobertura(
            quantidade_jogos=request.quantidade_jogos,
            seed=request.seed,
            permitir_espelhos=request.permitir_espelhos,
            trace=bool(request.trace),
        )

        # Camada de representacao da API: pos-validacao + float('inf') -> None (null no JSON)
        return validar_e_serializar_resultado_lotomania_modo4(
            resultado,
            request.quantidade_jogos,
            MotorLotomaniaModo4,
        )
    except HTTPException:
        raise
    except IntegridadeModo4Error as exc_selo:
        erro_id = str(uuid.uuid4())[:8]
        logger.critical("BLOQUEIO CRIPTOGRAFICO MODO 4 (ID: %s): %s", erro_id, exc_selo)
        raise HTTPException(
            status_code=503,
            detail=(
                f"MODO 4 bloqueado por falha de integridade criptografica (ID: {erro_id}). "
                "Nenhum jogo foi gerado."
            ),
        )
    except Exception as e:
        erro_id = str(uuid.uuid4())[:8]
        logger.exception("Erro no Motor Lotomania MODO 4. ID: %s | Detalhe: %s", erro_id, e)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno no processamento do MODO 4 (ID: {erro_id}). Consulte o log do servidor.",
        )


@app.post("/api/v1/lotomania-modo4/jobs", status_code=202)
def endpoint_lotomania_modo4_criar_job(request: OtimizarCoberturaRequest):
    """Enfileira geracao MODO 4 em subprocesso isolado, evitando timeout HTTP e disputa de GIL."""
    try:
        _validar_requisicao_e_selo_lotomania_modo4(request)
        return obter_gerenciador_jobs_lotomania_modo4().criar_job(
            quantidade_jogos=request.quantidade_jogos,
            permitir_espelhos=request.permitir_espelhos,
            seed=request.seed,
            trace=bool(request.trace),
        )
    except HTTPException:
        raise
    except IntegridadeModo4Error as exc_selo:
        erro_id = str(uuid.uuid4())[:8]
        logger.critical("BLOQUEIO CRIPTOGRAFICO MODO 4 JOB (ID: %s): %s", erro_id, exc_selo)
        raise HTTPException(
            status_code=503,
            detail=(
                f"MODO 4 bloqueado por falha de integridade criptografica (ID: {erro_id}). "
                "Nenhum jogo foi gerado."
            ),
        )
    except OverflowError as exc_lim:
        raise HTTPException(status_code=429, detail=str(exc_lim))
    except Exception as e:
        erro_id = str(uuid.uuid4())[:8]
        logger.exception("Erro ao enfileirar job MODO 4. ID: %s | Detalhe: %s", erro_id, e)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno ao criar tarefa do MODO 4 (ID: {erro_id}).",
        )


@app.get("/api/v1/lotomania-modo4/jobs/{job_id}")
def endpoint_lotomania_modo4_status_job(job_id: str):
    """Consulta estado, tempo decorrido e disponibilidade de resultado de um job MODO 4."""
    snap = obter_gerenciador_jobs_lotomania_modo4().obter_status(job_id)
    if snap is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' nao encontrado ou expirado.")
    return snap


@app.get("/api/v1/lotomania-modo4/jobs/{job_id}/resultado")
def endpoint_lotomania_modo4_resultado_job(job_id: str):
    """Entrega o JSON oficial validado de um job MODO 4 concluido (fail-closed em erros)."""
    estado, payload_bytes, meta = obter_gerenciador_jobs_lotomania_modo4().obter_resultado(job_id)
    if estado == "not_found":
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' nao encontrado ou expirado.")
    if estado == "running":
        raise HTTPException(status_code=409, detail="Job ainda em processamento. Aguarde a conclusao.")
    if estado == "cancelled":
        raise HTTPException(
            status_code=409,
            detail=(meta or {}).get("erro") or "Job cancelado pelo usuario. Nenhum jogo foi gerado.",
        )
    if estado == "failed" or payload_bytes is None:
        status_err = int((meta or {}).get("status_http") or 500)
        raise HTTPException(
            status_code=status_err,
            detail=(meta or {}).get("erro") or "Falha no processamento do MODO 4. Nenhum jogo foi gerado.",
        )
    return Response(content=payload_bytes, media_type="application/json")


@app.delete("/api/v1/lotomania-modo4/jobs/{job_id}")
def endpoint_lotomania_modo4_cancelar_job(job_id: str):
    """Cancela um job MODO 4 e encerra seu subprocesso trabalhador imediatamente."""
    snap = obter_gerenciador_jobs_lotomania_modo4().cancelar_job(job_id)
    if snap is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' nao encontrado ou expirado.")
    return snap


@app.post("/api/v1/lotomania-modo4/jobs/{job_id}/cancel")
def endpoint_lotomania_modo4_cancelar_job_post(job_id: str):
    """Alias POST para cancelamento via navigator.sendBeacon ao fechar a aba."""
    return endpoint_lotomania_modo4_cancelar_job(job_id)


@app.post("/api/v1/lotomania-modo4/conferir")
def endpoint_lotomania_modo4_conferir(request: ConferirModo4Request):
    """Confere uma carteira de bilhetes contra a base de referencia selada (concurso 1 a 2699)."""
    try:
        if not request.jogos:
            raise HTTPException(
                status_code=422,
                detail="Lista de jogos obrigatoria para conferencia nao pode ser vazia.",
            )
        verificar_selo_modo4()
        if MotorLotomaniaModo4 is None:
            from motor_lotomania_modo4 import MotorLotomaniaModo4 as _M4
            globals()["MotorLotomaniaModo4"] = _M4
        motor = MotorLotomaniaModo4(verificar_selo=True)
        return motor.conferir_carteira(jogos=request.jogos, concurso=request.concurso)
    except ValueError as ve:
        raise HTTPException(status_code=422, detail=str(ve))
    except IntegridadeModo4Error as exc_selo:
        erro_id = str(uuid.uuid4())[:8]
        logger.critical("BLOQUEIO CRIPTOGRAFICO MODO 4 CONFERENCIA (ID: %s): %s", erro_id, exc_selo)
        raise HTTPException(
            status_code=503,
            detail=f"MODO 4 bloqueado por violacao de integridade (ID: {erro_id}).",
        )
    except Exception as e:
        erro_id = str(uuid.uuid4())[:8]
        logger.exception("Erro na conferencia MODO 4. ID: %s | Detalhe: %s", erro_id, e)
        raise HTTPException(
            status_code=500,
            detail=f"Erro interno na conferencia do MODO 4 (ID: {erro_id}).",
        )


@app.post("/api/v1/motor-lotomania/otimizar-cobertura")
def endpoint_motor_lotomania_otimizar_cobertura(request: OtimizarCoberturaRequest):
    """
    Rota legada que delega integralmente ao modulo independente e selado
    MotorLotomaniaModo4 (v1.2), eliminando qualquer duplicidade de motor.
    """
    return endpoint_lotomania_modo4_gerar(request)


# =============================================================================
# MÓDULO EXCLUSIVO: MOTOR LOTOFÁCIL B2B (VERSÃO 2.5 - AJUSTE FINO)
# =============================================================================

@app.post("/api/v1/motor-lotofacil")
def endpoint_motor_lotofacil(request: MotorLotofacilRequest):
    """
    Endpoint exclusivo do MOTOR LOTOFACIL — B2B LOTERIAS (v2.5).
    Aplica paridade calibrada (7I/8P e 8I/7P), ressonancia de sorteio anterior,
    primos, moldura, fibonacci, multiplos de 3, corredor de soma 180-210,
    teto max 4 consecutivos e anti-saturacao de matriz 5x5.
    """
    try:
        historico = request.historico
        if not historico:
            historico = obter_historico_caixa("lotofacil")

        motor = MotorLotofacilB2B(
            historico=historico,
            limite_historico=request.historico_limite,
            estrategia=request.estrategia or "equilibrada",
            sniper=request.sniper if request.sniper is not None else True
        )

        resultado = motor.gerar_carteira(
            quantidade_jogos=request.quantidade_jogos,
            fixas=request.fixas,
            excluidas=request.excluidas
        )
        return resultado
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Motor Lotofacil: {str(e)}")


@app.post("/api/v1/motor-lotofacil/backtest")
def endpoint_motor_lotofacil_backtest(request: BacktestLotofacilRequest):
    """Executa simulação retrospectiva na Lotofácil sem vazamento de dados futuros."""
    try:
        historico = obter_historico_caixa("lotofacil")
        alvo = request.concurso_alvo_idx
        if alvo is None or alvo <= 0:
            alvo = len(historico) - 1

        motor = MotorLotofacilB2B(
            historico=historico,
            estrategia=request.estrategia or "equilibrada",
            sniper=request.sniper if request.sniper is not None else True
        )
        resultado = motor.executar_backtesting(
            concurso_alvo_idx=alvo,
            quantidade_jogos=request.quantidade_jogos or 20,
            estrategia=request.estrategia
        )
        return {"sucesso": True, "backtest": resultado}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Backtest Lotofacil: {str(e)}")



@app.post("/api/v1/motor-lotofacil/grupos")
def endpoint_motor_lotofacil_grupos(request: MotorLotofacilGruposRequest):
    """
    Endpoint do MOTOR DE FECHAMENTO POR GRUPOS DA LOTOFACIL - B2B LOTERIAS.
    O jogador define os grupos de dezenas e o motor une as combinacoes de grupos.
    """
    try:
        resultado = MotorLotofacilB2B.gerar_jogos_por_grupos(
            grupos=request.grupos,
            combinacoes=request.combinacoes,
            qtd_grupos_por_jogo=request.qtd_grupos_por_jogo or 5,
            eliminar_duplicados=request.eliminar_duplicados or False,
            ordenar_dezenas=request.ordenar_dezenas if request.ordenar_dezenas is not None else True,
            fixas=request.fixas,
            excluidas=request.excluidas
        )
        return resultado
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Motor Lotofacil por Grupos: {str(e)}")


# =============================================================================
# MÓDULO EXCLUSIVO: MOTOR TIMEMANIA B2B (ALTA ASSERTIVIDADE E CIÊNCIA EXATA)
# =============================================================================

@app.post("/api/v1/motor-timemania")
def endpoint_motor_timemania(request: MotorTimemaniaRequest):
    """
    Endpoint do MOTOR TIMEMANIA MATRIX PRO — B2B LOTERIAS.
    Suporta os 7 Modos de Operacao, os 6 Blocos de Desdobramentos da Planilha Original,
    Transposicao Serpentina (Base Invertida) com 100% de cobertura de pares,
    Score IFM 8D, Time do Coracao e Auditoria 10 pontos.
    """
    try:
        motor = MotorTimemaniaB2B(
            historico=request.historico,
            historico_times=request.historico_times,
            limite_historico=request.historico_limite,
            estrategia=request.estrategia or "equilibrada",
            sniper=request.sniper or False,
            no_consecutive_3_in_group=request.no_consecutive_3_in_group if request.no_consecutive_3_in_group is not None else True,
            max_consecutive_total=request.max_consecutive_total or 3,
            pool=request.pool,
            base_games=request.base_games
        )

        resultado = motor.gerar_carteira(
            quantidade_jogos=request.quantidade_jogos,
            modo=request.modo or "original",
            base_games=request.base_games,
            blocos_selecionados=request.blocos_selecionados,
            usar_base_invertida=request.usar_base_invertida or False,
            ambas_bases=request.ambas_bases or False,
            estrategia_time=request.estrategia_time or "maior_ift",
            time_fixo_usuario=request.time_fixo_usuario
        )
        return resultado
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Motor Timemania: {str(e)}")


@app.post("/api/v1/motor-timemania/matriz-pro")
def endpoint_motor_timemania_matriz_pro(request: MotorTimemaniaRequest):
    """Gera jogos da Timemania utilizando a matriz combinatoria e os 6 blocos de desdobramentos."""
    return endpoint_motor_timemania(request)


@app.post("/api/v1/motor-timemania/comparador")
def endpoint_motor_timemania_comparador(request: ComparadorTimemaniaRequest):
    """Executa confronto comparativo rigoroso entre Modo Original, Aprimorado e Hibrido."""
    try:
        motor = MotorTimemaniaB2B(base_games=request.base_games)
        resultado = motor.comparar_desdobramentos(
            quantidade_jogos=request.quantidade_jogos or 64,
            base_games=request.base_games,
            concursos_backtest=request.concursos_backtest or 50
        )
        return resultado
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Comparador Timemania: {str(e)}")


@app.post("/api/v1/motor-timemania/matriz-cobertura")
def endpoint_motor_timemania_cobertura(request: CoberturaTimemaniaRequest):
    """Calcula a matriz analitica de cobertura das 80 dezenas, pares, trincas e redundancia."""
    try:
        motor = MotorTimemaniaB2B()
        return {
            "sucesso": True,
            "analise": motor.calcular_matriz_cobertura_80(request.jogos)
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na Analise de Cobertura: {str(e)}")


@app.post("/api/v1/motor-timemania/base-invertida")
def endpoint_motor_timemania_base_invertida(request: BaseInvertidaRequest):
    """Calcula a transposicao serpentina (boustrophedon) dos 8 jogos-base."""
    try:
        base_inv = MotorTimemaniaB2B.calcular_base_invertida(request.base_games)
        return {
            "sucesso": True,
            "base_invertida": base_inv
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro ao calcular Base Invertida: {str(e)}")


@app.post("/api/v1/motor-timemania/backtest")
def endpoint_motor_timemania_backtest(request: BacktestTimemaniaRequest):
    """Executa simulação retrospectiva Walk-Forward na Timemania sem vazamento de dados futuros."""
    try:
        motor = MotorTimemaniaB2B(
            estrategia=request.estrategia or "equilibrada",
            sniper=request.sniper or False,
            no_consecutive_3_in_group=request.no_consecutive_3_in_group if request.no_consecutive_3_in_group is not None else True,
            pool=request.pool
        )
        resultado = motor.executar_backtesting(
            concursos_teste=request.concursos_teste or 50,
            quantidade_jogos=request.quantidade_jogos or 10,
            estrategia=request.estrategia
        )
        return {"sucesso": True, "backtest": resultado}
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Backtest Timemania: {str(e)}")


@app.post("/api/v1/motor-timemania/analise-estatistica")
def endpoint_motor_timemania_analise(request: AnaliseTimemaniaRequest):
    """Retorna o diagnóstico estatístico completo do universo e dos 80 clubes da Timemania."""
    try:
        motor = MotorTimemaniaB2B(
            limite_historico=request.historico_limite,
            pool=request.pool
        )
        return {
            "sucesso": True,
            "total_sorteios": len(motor.historico),
            "ifm_ranking": motor._gerar_relatorio_analitico([], 0, 0)["top_10_dezenas_ifm"],
            "times_ranking": motor._obter_ranking_times()[:15],
            "scores_grupos": motor._gerar_relatorio_analitico([], 0, 0)["scores_grupos"]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na Análise Timemania: {str(e)}")


# =============================================================================
# MÓDULO EXCLUSIVO: MOTOR DIA DE SORTE B2B (MÁXIMO RIGOR E HONESTIDADE)
# =============================================================================

class MotorDiaDeSorteRequest(BaseModel):
    quantidade_jogos: int
    historico_limite: Optional[int] = 30
    estrategia: Optional[str] = "equilibrada"
    pool: Optional[List[int]] = None
    historico: Optional[List[List[int]]] = None
    historico_meses: Optional[List[str]] = None


class AnaliseDiaDeSorteRequest(BaseModel):
    historico_limite: Optional[int] = 30
    estrategia: Optional[str] = "equilibrada"
    pool: Optional[List[int]] = None


@app.post("/api/v1/motor-diadesorte")
def endpoint_motor_diadesorte(request: MotorDiaDeSorteRequest):
    """
    Endpoint oficial do NOVO MOTOR DIA DE SORTE — B2B LOTERIAS.
    Aplica rigor matemático, grupos A (01-15) e B (16-31), modelos 3+4, 4+3, 5+2, 2+5,
    filtro <= 3 consecutivos, Lift/Z-score, auto-pesos, meses da sorte e transparência.
    """
    try:
        motor = MotorDiaDeSorteB2B(
            historico=request.historico,
            historico_meses=request.historico_meses,
            limite_historico=request.historico_limite or 30,
            estrategia=request.estrategia or "equilibrada",
            pool=request.pool
        )
        return motor.gerar_carteira(request.quantidade_jogos)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Motor Dia de Sorte: {str(e)}")


@app.post("/api/v1/motor-diadesorte/analise-estatistica")
def endpoint_motor_diadesorte_analise(request: AnaliseDiaDeSorteRequest):
    """Retorna o relatório pré-geração de evidência estatística do Dia de Sorte."""
    try:
        motor = MotorDiaDeSorteB2B(
            limite_historico=request.historico_limite or 30,
            estrategia=request.estrategia or "equilibrada",
            pool=request.pool
        )
        return {
            "sucesso": True,
            "relatorio": motor.gerar_relatorio_pre_geracao(),
            "distribuicoes": motor.stats["modelos_ordenados"],
            "top_meses": motor.stats["meses"][:5]
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na Análise Dia de Sorte: {str(e)}")


# =============================================================================
# MÓDULO EXCLUSIVO: MOTOR MEGA-SENA B2B (RIGOR MATEMÁTICO E COMBINATÓRIO)
# =============================================================================

class MotorMegaSenaRequest(BaseModel):
    quantidade_jogos: int
    historico_limite: Optional[int] = 30
    estrategia: Optional[str] = "equilibrada"
    pool: Optional[List[int]] = None
    modelo_preferencial: Optional[str] = None
    numeros_fixos: Optional[List[int]] = None
    numeros_proibidos: Optional[List[int]] = None
    historico: Optional[List[List[int]]] = None


class BacktestMegaSenaRequest(BaseModel):
    concursos_teste: Optional[int] = 10
    quantidade_jogos: Optional[int] = 10
    historico_limite: Optional[int] = 30
    estrategia: Optional[str] = "equilibrada"
    pool: Optional[List[int]] = None


class AnaliseMegaSenaRequest(BaseModel):
    historico_limite: Optional[int] = 30
    estrategia: Optional[str] = "equilibrada"
    pool: Optional[List[int]] = None


@app.post("/api/v1/motor-megasena")
def endpoint_motor_megasena(request: MotorMegaSenaRequest):
    """
    Endpoint oficial do NOVO MOTOR MEGA-SENA — B2B LOTERIAS.
    Aplica rigor matemático e estatístico, grupos A (01-30) e B (31-60), modelos hipergeométricos
    (3/3, 2/4, 4/2, 1/5, 5/1), filtro estrito de no máximo 3 números consecutivos, centróide simétrico,
    coocorrência/Lift/Z-Score, auto-pesos e diversificação de Jaccard.
    """
    try:
        motor = MotorMegaSenaB2B(
            historico=request.historico,
            limite_historico=request.historico_limite or 30,
            estrategia=request.estrategia or "equilibrada",
            pool=request.pool,
            modelo_preferencial=request.modelo_preferencial,
            numeros_fixos=request.numeros_fixos,
            numeros_proibidos=request.numeros_proibidos
        )
        return motor.gerar_carteira(request.quantidade_jogos)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Motor Mega-Sena: {str(e)}")


@app.post("/api/v1/motor-megasena/backtest")
def endpoint_motor_megasena_backtest(request: BacktestMegaSenaRequest):
    """Executa simulação retrospectiva Walk-Forward na Mega-Sena sem vazamento de dados futuros."""
    try:
        motor = MotorMegaSenaB2B(
            limite_historico=request.historico_limite or 30,
            estrategia=request.estrategia or "equilibrada",
            pool=request.pool
        )
        return motor.executar_backtesting(
            concursos_teste=request.concursos_teste or 10,
            quantidade_jogos=request.quantidade_jogos or 10
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Backtest Mega-Sena: {str(e)}")


@app.post("/api/v1/motor-megasena/analise-estatistica")
def endpoint_motor_megasena_analise(request: AnaliseMegaSenaRequest):
    """Retorna o relatório pré-geração de evidência estatística da Mega-Sena."""
    try:
        motor = MotorMegaSenaB2B(
            limite_historico=request.historico_limite or 30,
            estrategia=request.estrategia or "equilibrada",
            pool=request.pool
        )
        return {
            "sucesso": True,
            "relatorio": motor.gerar_relatorio_pre_geracao(),
            "distribuicoes": motor.stats["modelos_ordenados"],
            "top_pares": motor.stats["pares_top"][:10],
            "robustez": motor.testar_robustez_indicadores()
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na Análise Mega-Sena: {str(e)}")


# =============================================================================
# MÓDULO EXCLUSIVO: MOTOR QUINA B2B (MÁXIMA ASSERTIVIDADE ESTATÍSTICA)
# =============================================================================

class MotorQuinaRequest(BaseModel):
    quantidade_jogos: int
    historico_limite: Optional[int] = 30
    estrategia: Optional[str] = "equilibrada"
    pool: Optional[List[int]] = None
    modelo_preferencial: Optional[str] = None
    numeros_fixos: Optional[List[int]] = None
    numeros_proibidos: Optional[List[int]] = None
    historico: Optional[List[List[int]]] = None


class BacktestQuinaRequest(BaseModel):
    concursos_teste: Optional[int] = 10
    quantidade_jogos: Optional[int] = 10
    historico_limite: Optional[int] = 30
    estrategia: Optional[str] = "equilibrada"
    pool: Optional[List[int]] = None


class AnaliseQuinaRequest(BaseModel):
    historico_limite: Optional[int] = 30
    estrategia: Optional[str] = "equilibrada"
    pool: Optional[List[int]] = None


@app.post("/api/v1/motor-quina")
def endpoint_motor_quina(request: MotorQuinaRequest):
    """
    Endpoint oficial do NOVO MOTOR QUINA — B2B LOTERIAS.
    Aplica rigor matemático e estatístico, grupos A (01-40) e B (41-80), modelos hipergeométricos
    (3/2, 2/3, 4/1, 1/4, 5/0, 0/5), filtro estrito de no máximo 2 números consecutivos, centróide simétrico (202.5),
    coocorrência/Lift/Z-Score, auto-pesos, IGA (0-100), modo Sniper e diversificação combinatória.
    """
    try:
        motor = MotorQuinaB2B(
            historico=request.historico,
            limite_historico=request.historico_limite or 30,
            estrategia=request.estrategia or "equilibrada",
            pool=request.pool,
            modelo_preferencial=request.modelo_preferencial,
            numeros_fixos=request.numeros_fixos,
            numeros_proibidos=request.numeros_proibidos
        )
        return motor.gerar_carteira(request.quantidade_jogos)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Motor Quina: {str(e)}")


@app.post("/api/v1/motor-quina/backtest")
def endpoint_motor_quina_backtest(request: BacktestQuinaRequest):
    """Executa simulação retrospectiva Walk-Forward na Quina sem vazamento de dados futuros."""
    try:
        motor = MotorQuinaB2B(
            limite_historico=request.historico_limite or 30,
            estrategia=request.estrategia or "equilibrada",
            pool=request.pool
        )
        return motor.executar_backtesting(
            concursos_teste=request.concursos_teste or 10,
            quantidade_jogos=request.quantidade_jogos or 10
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Backtest Quina: {str(e)}")


@app.post("/api/v1/motor-quina/analise-estatistica")
def endpoint_motor_quina_analise(request: AnaliseQuinaRequest):
    """Retorna o relatório pré-geração de evidência estatística da Quina."""
    try:
        motor = MotorQuinaB2B(
            limite_historico=request.historico_limite or 30,
            estrategia=request.estrategia or "equilibrada",
            pool=request.pool
        )
        return {
            "sucesso": True,
            "relatorio": motor.gerar_relatorio_pre_geracao(),
            "distribuicoes": motor.stats["modelos_ordenados"],
            "top_pares": motor.stats["pares_top"][:10],
            "robustez": motor.testar_robustez_indicadores()
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na Análise Quina: {str(e)}")




# =============================================================================
# MÓDULO EXCLUSIVO: MOTOR SUPER SETE B2B (RIGOR MATEMÁTICO E COMBINATÓRIO)
# =============================================================================

class MotorSuperSeteRequest(BaseModel):
    quantidade_jogos: int
    historico_limite: Optional[int] = None
    estrategia: Optional[str] = "equilibrada"
    pool_colunas: Optional[Dict[int, List[int]]] = None
    digitos_fixos: Optional[Dict[int, int]] = None
    digitos_proibidos: Optional[Dict[int, List[int]]] = None
    max_consecutivos: Optional[int] = 3
    hamming_minimo: Optional[int] = 4
    historico: Optional[List[List[int]]] = None


class BacktestSuperSeteRequest(BaseModel):
    concursos_teste: Optional[int] = 15
    quantidade_jogos: Optional[int] = 10
    estrategia: Optional[str] = "equilibrada"


class AnaliseSuperSeteRequest(BaseModel):
    historico_limite: Optional[int] = None
    estrategia: Optional[str] = "equilibrada"


@app.post("/api/v1/motor-supersete")
def endpoint_motor_supersete(request: MotorSuperSeteRequest):
    """
    Endpoint oficial do NOVO MOTOR SUPER SETE — B2B LOTERIAS.
    Aplica rigor matemático, estatístico e computacional com 7 modelos independentes
    de coluna (M1..M7), matriz de Lift regularizada por Laplace, centróide simétrico,
    diversificação de Hamming, modo Sniper e Honestidade Científica.
    """
    try:
        from motor_supersete import MotorSuperSeteB2B
        historico = request.historico
        if not historico:
            historico = obter_historico_caixa("supersete")

        motor = MotorSuperSeteB2B(
            historico=historico,
            limite_historico=request.historico_limite,
            estrategia=request.estrategia or "equilibrada",
            pool_colunas=request.pool_colunas,
            digitos_fixos=request.digitos_fixos,
            digitos_proibidos=request.digitos_proibidos,
            max_consecutivos=request.max_consecutivos or 3,
            hamming_minimo=request.hamming_minimo or 4
        )
        return motor.gerar_carteira(request.quantidade_jogos)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Motor Super Sete: {str(e)}")


@app.post("/api/v1/motor-supersete/backtest")
def endpoint_motor_supersete_backtest(request: BacktestSuperSeteRequest):
    """Executa simulação retrospectiva Walk-Forward no Super Sete sem vazamento de dados futuros."""
    try:
        from motor_supersete import MotorSuperSeteB2B
        historico = obter_historico_caixa("supersete")
        motor = MotorSuperSeteB2B(
            historico=historico,
            estrategia=request.estrategia or "equilibrada"
        )
        return motor.executar_backtesting(
            concursos_teste=request.concursos_teste or 15,
            quantidade_jogos=request.quantidade_jogos or 10,
            estrategia=request.estrategia
        )
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Backtest Super Sete: {str(e)}")


@app.post("/api/v1/motor-supersete/analise-estatistica")
def endpoint_motor_supersete_analise(request: AnaliseSuperSeteRequest):
    """Retorna o relatório pré-geração de evidência estatística das 7 colunas do Super Sete."""
    try:
        from motor_supersete import MotorSuperSeteB2B
        historico = obter_historico_caixa("supersete")
        motor = MotorSuperSeteB2B(
            historico=historico,
            limite_historico=request.historico_limite,
            estrategia=request.estrategia or "equilibrada"
        )
        return {
            "sucesso": True,
            "relatorio": motor.gerar_relatorio_pre_geracao(),
            "frase_obrigatoria": motor.FRASE_OBRIGATORIA
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro na Análise Super Sete: {str(e)}")


# =============================================================================
# LOTOFACIL MODO 4 — PROMOCAO CONTROLADA (FEATURE FLAG DESLIGADA POR PADRAO)
# =============================================================================
if registrar_lotofacil_modo4_na_api is not None:
    registrar_lotofacil_modo4_na_api(app)


app.add_event_handler("shutdown", encerrar_gerenciador_jobs_lotomania_modo4)


if __name__ == "__main__":
    _garantir_fluxos_padrao_seguros()
    _app_dir = os.path.dirname(os.path.abspath(__file__))
    if _app_dir not in sys.path:
        sys.path.insert(0, _app_dir)
    os.chdir(_app_dir)
    _use_colors = bool(sys.stdout is not None and getattr(sys.stdout, "isatty", lambda: False)())
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=False, use_colors=_use_colors)
