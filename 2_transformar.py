"""
Fase 2 - Transformação da camada Raw para Silver.

Aqui os dados brutos armazenados como texto são limpos e
convertidos para os tipos corretos e inseridos nas tabelas Silver.
"""

from datetime import datetime
from decimal import Decimal, InvalidOperation

from banco import conectar, executar, inserir_em_lote