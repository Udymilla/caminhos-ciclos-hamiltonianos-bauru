"""Verificações do ponto de partida obrigatório no modo de escolas reais."""
import pandas as pd
import pytest

from src.base_fixa import (
    NOME_BASE, LATITUDE_BASE, LONGITUDE_BASE, ID_BASE, adicionar_base_fixa,
)


def _escolas(n=2):
    return pd.DataFrame([
        {"id": str(i), "nome": f"Escola {i}", "latitude": -22.3-i*.001,
         "longitude": -49.05-i*.001, "municipio": "Bauru"}
        for i in range(n)
    ])


def test_base_fixa_e_vertice_zero():
    origem = _escolas()
    rotas = adicionar_base_fixa(origem)
    assert rotas.iloc[0]["nome"] == NOME_BASE
    assert rotas.iloc[0]["id"] == ID_BASE
    assert rotas.iloc[0]["latitude"] == pytest.approx(-22.325573)
    assert rotas.iloc[0]["longitude"] == pytest.approx(-49.091570)
    assert len(rotas) == 3
    assert rotas["id"].is_unique
    assert origem.shape[0] == 2
    assert rotas.iloc[1]["id"] == origem.iloc[0]["id"]


def test_base_adicionada_uma_vez_apenas():
    with pytest.raises(ValueError, match="já presente"):
        adicionar_base_fixa(adicionar_base_fixa(_escolas()))


def test_limite_de_24_escolas():
    assert len(adicionar_base_fixa(_escolas(24))) == 25
    with pytest.raises(ValueError, match="até 24"):
        adicionar_base_fixa(_escolas(25))


def test_lista_vazia_nao_cria_rota_somente_com_base():
    assert adicionar_base_fixa(_escolas(0)).empty
