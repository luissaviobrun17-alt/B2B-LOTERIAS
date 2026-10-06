from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
import urllib.request
import json
import os
from motor_sugestao import MotorSugestaoLoteria
from motor_lotomania import MotorLotomaniaB2B
from motor_lotofacil import MotorLotofacilB2B
from motor_timemania import MotorTimemaniaB2B
from motor_diadesorte import MotorDiaDeSorteB2B
from motor_megasena import MotorMegaSenaB2B
try:
    from motor_supersete import MotorSuperSeteB2B
except ImportError:
    MotorSuperSeteB2B = None
from motor_quina import MotorQuinaB2B

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

class MotorLotomaniaRequest(BaseModel):
    quantidade_jogos: int
    historico_limite: Optional[int] = None
    estrategia: Optional[str] = "equilibrada"
    historico: Optional[List[List[int]]] = None

class BacktestLotomaniaRequest(BaseModel):
    concurso_alvo_idx: Optional[int] = None
    quantidade_jogos: Optional[int] = 10
    estrategia: Optional[str] = "equilibrada"

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

class MotorTimemaniaRequest(BaseModel):
    quantidade_jogos: int
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

    cache_dir = "data"
    os.makedirs(cache_dir, exist_ok=True)
    cache_path = os.path.join(cache_dir, f"{loteria_key}.json")

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

        motor = MotorLotomaniaB2B(
            historico=historico,
            limite_historico=request.historico_limite,
            estrategia=request.estrategia or "equilibrada"
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


# =============================================================================
# MÓDULO EXCLUSIVO: MOTOR TIMEMANIA B2B (ALTA ASSERTIVIDADE E CIÊNCIA EXATA)
# =============================================================================

@app.post("/api/v1/motor-timemania")
def endpoint_motor_timemania(request: MotorTimemaniaRequest):
    """
    Endpoint do MOTOR TIMEMANIA — B2B LOTERIAS.
    Aplica divisão analítica em 4 grupos (01-20, 21-40, 41-60, 61-80),
    bloqueio de 3 consecutivos por grupo, IFM 8 dimensões, IFT do Time do Coração,
    otimização submodular de carteira e auditoria 10 pontos.
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
            pool=request.pool
        )

        resultado = motor.gerar_carteira(
            quantidade_jogos=request.quantidade_jogos,
            estrategia_time=request.estrategia_time or "maior_ift",
            time_fixo_usuario=request.time_fixo_usuario
        )
        return resultado
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Motor Timemania: {str(e)}")


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


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
