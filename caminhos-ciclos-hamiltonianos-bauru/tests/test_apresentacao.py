"""Valida textos da interface sem precisar instalar Streamlit."""
import pandas as pd
from src.algoritmos import exato, heuristico, rota_valida
from src.apresentacao import (
    status_resultado, explicar_resultado, comparar_interpretacao, melhor_resultado,
    tabela_etapas, tabela_resultados,
)
from src.instancias import pontos_simulados, matriz_cenario


def _matriz_completa():
    return [[0, 3, 5, 9], [3, 0, 2, 4], [5, 2, 0, 2], [9, 4, 2, 0]]


def test_otimo_comprovado_explicado_sem_inventar():
    r = exato(_matriz_completa(), "minimo", 2)
    assert r["otimo_comprovado"]
    assert status_resultado(r) == "Ótimo comprovado"
    texto = explicar_resultado(r, 4)
    assert "comprovou" in texto
    assert "retorna à base" in texto
    assert f"{r['km']:.2f} km" in texto


def test_caminho_comprovado_nao_e_chamado_minimo():
    r = exato(_matriz_completa(), "caminho", 2)
    assert r["rota"]
    assert "menor" not in status_resultado(r).lower()
    assert "não foi pesquisado o menor custo" in explicar_resultado(r, 4)


def test_impossibilidade_comprovada_corredor():
    m = [[0, 2, float('inf')], [2, 0, 2], [float('inf'), 2, 0]]
    r = exato(m, "ciclo", 2)
    assert r["ausencia_comprovada"]
    assert "não existe" in explicar_resultado(r, 3)
    assert status_resultado(r) == "Inexistência comprovada"


def test_heuristica_sem_rota_nao_comprova_inexistencia():
    m = [[0, 2, float('inf')], [2, 0, 2], [float('inf'), 2, 0]]
    r = heuristico(m, "ciclo")
    assert "não comprova" in explicar_resultado(r, 3)
    assert "comprovada" not in status_resultado(r).lower()


def test_exato_temporizado_sem_rota_inconclusivo():
    r = {"modo": "minimo", "metodo": "Exato", "rota": [], "km": None,
         "tempo_ms": 1000.0, "timeout": True, "otimo_comprovado": False,
         "ausencia_comprovada": False, "aviso": "Limite"}
    assert "inconclusivo" in explicar_resultado(r, 6)


def test_comparacao_desvio_so_quando_otimo_comprovado():
    m = _matriz_completa()
    e, h = exato(m, "minimo", 2), heuristico(m, "minimo")
    assert "desvio da heurística em relação ao ótimo" in comparar_interpretacao({"Exato": e, "Heuristica": h}, "minimo")
    n = dict(e, otimo_comprovado=False)
    assert "sem uma prova de otimalidade" in comparar_interpretacao({"Exato": n, "Heuristica": h}, "minimo")


def test_comparacao_um_so_resultado_sem_contradicao():
    m = _matriz_completa()
    e, h = exato(m, "minimo", 2), heuristico(m, "minimo")
    eh = dict(h, rota=[], km=None)
    assert "heurística não" in comparar_interpretacao({"Exato": e, "Heuristica": eh}, "minimo")
    en = dict(e, rota=[], km=None)
    texto = comparar_interpretacao({"Exato": en, "Heuristica": h}, "minimo")
    assert "heurística encontrou" in texto
    assert "enquanto a busca exata não apresentou rota" in texto


def test_tabela_passos_indica_retorno_na_base():
    df = pd.DataFrame({"nome": ["Base", "Escola A", "Escola B"]})
    m = [[0, 1, 2], [1, 0, 3], [2, 3, 0]]
    r = [0, 1, 2, 0]
    tabela = tabela_etapas(df, r, m)
    assert list(tabela["Local"]) == ["Base", "Escola A", "Escola B", "Base"]
    assert tabela.iloc[-1]["Próximo trecho (km)"] != tabela.iloc[-1]["Próximo trecho (km)"]  # NaN
    assert tabela.iloc[1]["Próximo trecho (km)"] == 3.0


def test_melhor_resultado_funciona_sem_nenhuma_rota():
    r = {"Exato": {"rota": [], "km": None}, "Heuristica": {"rota": [], "km": None}}
    assert melhor_resultado(r) == (None, None)


def test_tabela_comparacao_duas_entradas():
    m = _matriz_completa()
    tabela = tabela_resultados({"Exato": exato(m, "ciclo", 2), "Heuristica": heuristico(m, "ciclo")})
    assert len(tabela) == 2
    assert "Situação" in tabela.columns
