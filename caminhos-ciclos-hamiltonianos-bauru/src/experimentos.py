"""Bateria reproduzivel de experimentos para diferentes dimensoes."""
import pandas as pd
from src.algoritmos import exato, heuristico, rota_valida
from src.instancias import pontos_simulados, matriz_cenario


def realizar_experimentos(limite_segundos: float = 2.0) -> pd.DataFrame:
    entradas = [(5, "completo"), (9, "completo"), (12, "completo"),
                (16, "completo"), (7, "corredor"), (6, "desconexo")]
    saida = []
    for n, cenario in entradas:
        d = matriz_cenario(pontos_simulados(n), cenario)
        for modo in ("caminho", "ciclo", "minimo"):
            for nome, f in (("Exato", lambda: exato(d, modo, limite_segundos)),
                            ("Heuristica", lambda: heuristico(d, modo))):
                r = f()
                saida.append({"pontos": n, "cenario": cenario, "problema": modo,
                              "algoritmo": nome, "rota_valida": rota_valida(r["rota"], d, modo) if r["rota"] else False,
                              "distancia_km": r["km"], "tempo_ms": r["tempo_ms"],
                              "concluido": r["concluido"], "timeout": r["timeout"],
                              "otimo_comprovado": r["otimo_comprovado"],
                              "ausencia_comprovada": r["ausencia_comprovada"],
                              "nos_explorados": r["nos"]})
    return pd.DataFrame(saida)
