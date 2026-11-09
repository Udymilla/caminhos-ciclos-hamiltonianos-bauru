"""Ponto base fixo usado nas rotas com escolas reais do município de Bauru.

O endereco foi conferido no site institucional da Unidade Regional de Ensino
e as coordenadas constam em cadastro publico de localizacao. Para operacao
rodoviaria recomenda-se verificar o encaixe OSRM e a entrada veicular.
Nos cenarios didaticos permanecem validos os pontos simulados.
"""
from __future__ import annotations

import pandas as pd

NOME_BASE = "Unidade Regional de Ensino de Bauru"
LATITUDE_BASE = -22.325573
LONGITUDE_BASE = -49.091570
ID_BASE = "__base__"


def adicionar_base_fixa(escolas: pd.DataFrame) -> pd.DataFrame:
    """Insere a base como vértice 0, sem editar os registros originais de escolas."""
    if escolas.empty:
        return escolas.copy()
    if "id" in escolas.columns and escolas["id"].astype(str).eq(ID_BASE).any():
        raise ValueError("Ponto base já presente; não se deve adicioná-lo duas vezes.")
    if len(escolas) > 24:
        raise ValueError("Selecione até 24 escolas, além do ponto base fixo (25 vértices).")
    base = {
        "id": ID_BASE,
        "nome": NOME_BASE,
        "etiqueta": "BASE FIXA · Unidade Regional de Ensino de Bauru",
        "latitude": LATITUDE_BASE,
        "longitude": LONGITUDE_BASE,
        "municipio": "Bauru",
        "endereco": "Rua Campos Salles, 9-43, Vila Falcão, Bauru - SP, 17050-000",
        "codigo_inep": "",
        "rede": "PONTO BASE (NÃO É ESCOLA)",
        "origem": "PONTO BASE FIXO DEFINIDO PELO GRUPO",
    }
    return pd.concat([pd.DataFrame([base]), escolas], ignore_index=True)
