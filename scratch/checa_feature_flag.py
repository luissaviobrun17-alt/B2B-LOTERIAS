import sys
import os

BASE_DIR = r"C:\Users\Luis Brun\Desktop\GitHub\B2B LOTERIAS"
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from lotofacil_modo4.etapa5_api_homologacao import carregar_config_homologacao_de_env, ConfigHomologacaoLotofacilModo4
from lotofacil_modo4.promocao_producao import carregar_config_producao_de_env, ConfigProducaoLotofacilModo4

cfg_h = carregar_config_homologacao_de_env()
cfg_p = carregar_config_producao_de_env()

print("EVIDENCIA_FEATURE_FLAG_HOMOLOGACAO:", cfg_h.lotofacil_modo4_ativo)
print("EVIDENCIA_FEATURE_FLAG_PRODUCAO:", cfg_p.lotofacil_modo4_ativo)
print("DEFAULT_CLASS_HOMOLOGACAO:", ConfigHomologacaoLotofacilModo4().lotofacil_modo4_ativo)
print("DEFAULT_CLASS_PRODUCAO:", ConfigProducaoLotofacilModo4().lotofacil_modo4_ativo)
