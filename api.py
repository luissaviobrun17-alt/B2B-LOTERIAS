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


def obter_historico_caixa(nome_loteria: str) -> List[List[int]]:
    mapping = {
        "megasena": "megasena",
        "lotofacil": "lotofacil",
        "quina": "quina",
        "lotomania": "lotomania",
        "duplasena": "duplasena",
        "diadesorte": "diadesorte"
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
            draw = [int(x) for x in data[key]]
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


class MotorLotofacilRequest(BaseModel):
    quantidade_jogos: int
    historico_limite: Optional[int] = 10
    estrategia: Optional[str] = "equilibrada"
    historico: Optional[List[List[int]]] = None


@app.post("/api/v1/motor-lotofacil")
def endpoint_motor_lotofacil(request: MotorLotofacilRequest):
    """
    Endpoint exclusivo do MOTOR INTELIGENTE LOTOFÁCIL — B2B LOTERIAS.
    Explora divisões dinâmicas, subconjuntos 7/8, 8/7, 6/9, 9/6, consecutividade <= 5,
    scoring multicritério (Score B2B), diversificação e transparência ("Verdade Matemática").
    """
    try:
        historico = request.historico
        if not historico:
            historico = obter_historico_caixa("lotofacil")

        motor = MotorLotofacilB2B(
            historico=historico,
            limite_historico=request.historico_limite or 10,
            estrategia=request.estrategia or "equilibrada"
        )

        resultado = motor.gerar_carteira(request.quantidade_jogos)
        return resultado
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Erro no Motor Lotofácil: {str(e)}")


if __name__ == "__main__":
    uvicorn.run("api:app", host="0.0.0.0", port=8000, reload=True)
