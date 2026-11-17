# -*- coding: utf-8 -*-
import os
import pprint
import sys

sys.path.insert(0, os.path.abspath("."))

from lotofacil_modo4.etapa4_referencia_independente import verificar_preservacao_etapas_1_2_3_ref

res = verificar_preservacao_etapas_1_2_3_ref(os.path.abspath("."))
print("Resultado de verificar_preservacao_etapas_1_2_3_ref:")
pprint.pprint(res)
