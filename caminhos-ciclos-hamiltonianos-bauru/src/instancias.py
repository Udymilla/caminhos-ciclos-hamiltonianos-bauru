"""Instancias didaticas offline DECLARADAMENTE SIMULADAS.

Coordenadas sao pontos ficticios, nao escolas nem distancias por rua.
"""
import math
import pandas as pd

PONTOS = [
    ("Base simulada - Bauru", -22.3240, -49.0710),
    ("Ponto ficticio 01", -22.3150, -49.0550),
    ("Ponto ficticio 02", -22.3330, -49.0510),
    ("Ponto ficticio 03", -22.3440, -49.0800),
    ("Ponto ficticio 04", -22.3120, -49.0900),
    ("Ponto ficticio 05", -22.2990, -49.0670),
    ("Ponto ficticio 06", -22.3330, -49.1010),
    ("Ponto ficticio 07", -22.3530, -49.0650),
    ("Ponto ficticio 08", -22.2910, -49.0920),
    ("Ponto ficticio 09", -22.3550, -49.0950),
    ("Ponto ficticio 10", -22.3080, -49.0310),
    ("Ponto ficticio 11", -22.3410, -49.0340),
    ("Ponto ficticio 12", -22.2830, -49.0470),
    ("Ponto ficticio 13", -22.3670, -49.0520),
    ("Ponto ficticio 14", -22.2830, -49.1150),
    ("Ponto ficticio 15", -22.3700, -49.1110),
    ("Ponto ficticio 16", -22.3050, -49.1200),
    ("Ponto ficticio 17", -22.3710, -49.0300),
    ("Ponto ficticio 18", -22.2800, -49.0800),
    ("Ponto ficticio 19", -22.3240, -49.1220),
]


def pontos_simulados(n: int) -> pd.DataFrame:
    return pd.DataFrame(PONTOS[:n], columns=["nome", "latitude", "longitude"]).assign(
        municipio="Bauru", origem="SIMULADO (NAO E ESCOLA REAL)")


def haversine(lat1, lon1, lat2, lon2):
    r = 6371.0088
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp/2)**2 + math.cos(p1)*math.cos(p2)*math.sin(dl/2)**2
    return 2*r*math.asin(min(1, math.sqrt(a)))


def distancia_aproximada(df: pd.DataFrame) -> list[list[float]]:
    """Haversine vezes fator 1.3, somente ilustrativo; NAO e distancia de ruas."""
    pontos = df.to_dict("records")
    n = len(pontos)
    return [[0.0 if i == j else round(haversine(a["latitude"], a["longitude"], b["latitude"], b["longitude"]) * 1.3, 4)
             for j, b in enumerate(pontos)] for i, a in enumerate(pontos)]


def instancias_offline() -> dict:
    return {
        "Pequena - 5 pontos (completo)": {"n": 5, "cenario": "completo"},
        "Media - 9 pontos (completo)": {"n": 9, "cenario": "completo"},
        "Grande - 16 pontos (completo)": {"n": 16, "cenario": "completo"},
        "Corredor - caminho sem ciclo": {"n": 7, "cenario": "corredor"},
        "Desconexo - sem caminho": {"n": 6, "cenario": "desconexo"},
    }


def matriz_cenario(df: pd.DataFrame, cenario: str = "completo") -> list[list[float]]:
    matriz = distancia_aproximada(df)
    n = len(matriz)
    if cenario == "corredor":
        for i in range(n):
            for j in range(n):
                if abs(i-j) > 1:
                    matriz[i][j] = math.inf
    elif cenario == "desconexo":
        for i in range(n):
            for j in range(n):
                if i != j and (i == n - 1 or j == n - 1):
                    matriz[i][j] = math.inf
    elif cenario != "completo":
        raise ValueError("Cenario desconhecido")
    return matriz
